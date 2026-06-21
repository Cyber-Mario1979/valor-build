"""Dispatch spine — the A16 §5 contract-enforcement pattern, made executable.

Every boundary crossing runs this exact sequence, fail-closed:

    caller -> [validate request envelope: contract_request.schema.json]
           -> resolve action in registry -> side_effect + confirm + result_schema_ref
           -> [runtime-mode reachability: A18 §2]
           -> [gate evaluation: A17 — BUILD log-only / LIVE halts]
           -> (if confirm:true) human confirmation gate  [ALWAYS on, BUILD included]
           -> execute handler against L1 path
           -> [validate result against result_schema_ref]
           -> [validate response envelope: contract_response.schema.json]
           -> stamp output (A18 §3) + audit
           -> return | refuse

The pack (L1) is never told to skip anything; this layer decides what to *do* with a
verdict (R2). Truth-store integrity and the human gate stay live in every mode (A17 §4).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Callable

from .audit import AuditLog, canonical_hash, now_utc
from .identity import Principal, RoleContext, actor_block, requires_role_ack
from .authority import Approval, authorize, evaluate_approval
from .gates import GateBlocked, GateVerdict, Lifecycle, evaluate_gate
from .registry import ActionSpec, ContractRegistry
from .schemas import SchemaRegistry, SchemaValidationError
from ..modes.runtime import RuntimeMode, require_reachable

# Pack marker carried on every BUILD output (A17 §6 / R5 guard).
PRODUCT_TESTING_ONLY = "PRODUCT TESTING ONLY — NOT APPROVED FOR REAL-LIFE REGULATED CQV/GMP USE."


@dataclass
class StepRequest:
    action: str                       # canonical type or public alias
    payload: dict
    target: dict                      # e.g. {"wp_id": "WP001"}
    runtime_mode: RuntimeMode
    lifecycle: Lifecycle
    engine_mode: str                  # "EXECUTION" | "DESIGN" (envelope mode field)
    actor_role: str
    actor_name: str | None = None     # optional declared name (A09 §7.1 actor.name)
    state: str = ""                   # resulting state for the output stamp
    gate: str | None = None           # canonical gate this step maps to, or None
    entry_condition_met: bool = True
    gate_reason: str = ""
    provenance: dict = field(default_factory=dict)  # e.g. AI prompt/output hashes
    # M-IDENTITY (C1 Step 3): a verified identity engages the verified path. When
    # None, the soft B7 path runs unchanged (declared role, identity_verified=False).
    principal: Principal | None = None
    author_id: str = ""               # DOC_FINALIZE: who authored the draft (approver != author)
    approvals: tuple[Approval, ...] = field(default_factory=tuple)  # full signed approver set


@dataclass
class DispatchResult:
    ok: bool
    response: dict                    # validated contract_response envelope
    result: dict | None
    verdict: GateVerdict | None
    stamp: dict
    spec: ActionSpec
    error: dict | None = None


class ConfirmationRefused(RuntimeError):
    """The human said No at the confirmation gate. Truth is not mutated."""


class Dispatcher:
    def __init__(
        self,
        registry: ContractRegistry,
        schemas: SchemaRegistry,
        audit: AuditLog,
        confirm_provider: Callable[[str], bool],
    ):
        self.registry = registry
        self.schemas = schemas
        self.audit = audit
        self.confirm = confirm_provider

    def dispatch(self, req: StepRequest, handler: Callable[[], dict]) -> DispatchResult:
        spec = self.registry.resolve(req.action)
        action_id = f"{spec.action_type}:{uuid.uuid4().hex[:12]}"
        wp_id = req.target.get("wp_id", "")

        # Effective actor: a verified Principal supersedes the declared role/name.
        # With no principal, these collapse to the soft B7 values byte-for-byte.
        principal = req.principal
        actor_role = principal.role if principal else req.actor_role
        actor_name = principal.name if principal else req.actor_name
        actor = principal.actor_block() if principal else actor_block(actor_role, actor_name)

        # 0. Capture identity context — one audited record per action (A09 §7.1).
        #    Verified path: identity_verified=True + the real actor.id (M-IDENTITY).
        #    Soft path: the unchanged B7 capture (identity_verified=False).
        if principal:
            self.audit.emit(
                "identity_context",
                declared_role=principal.role,
                actor_name=principal.name or "",
                actor_id=principal.id,
                profile=principal.profile,
                identity_verified=True,
                action_type=spec.action_type,
                wp_id=wp_id,
            )
        else:
            RoleContext.capture(
                self.audit, req.actor_role, name=req.actor_name,
                action_type=spec.action_type, wp_id=wp_id,
            )

        # 1. Build + validate the request envelope (fail-closed). A verified actor.id
        #    rides the frozen envelope unchanged (actor.additionalProperties:true).
        request_env = {
            "contract": spec.contract_id,
            "contract_version": spec.contract_version,
            "action_id": action_id,
            "action_type": spec.action_type,
            "mode": req.engine_mode,
            "actor": actor,
            "target": req.target,
            "payload": req.payload,
            "context": {"timestamp_utc": now_utc()},
        }
        self.schemas.validate(request_env, "schemas/contracts/contract_request.schema.json")

        # 2. Runtime-mode reachability (A18 §2). M3 reaches all; M1/M2/M4 bounded.
        #    M4 takes a contract-aware exception for projection-only RPT artifacts.
        require_reachable(req.runtime_mode, spec.side_effect, spec.contract_id)

        # 3. Gate evaluation (A17). BUILD: log-only; LIVE: GateBlocked halts.
        verdict = None
        if req.gate is not None:
            try:
                verdict = evaluate_gate(req.gate, req.entry_condition_met, req.lifecycle, req.gate_reason)
            except GateBlocked as blocked:
                self.audit.emit(
                    "gate_outcome", gate=blocked.gate, mode=req.lifecycle.value,
                    entry_condition="not_met", verdict="WOULD_BLOCK", reason=blocked.reason,
                    proceeded=False, wp_id=wp_id, actor_role=actor_role,
                )
                raise
            self.audit.emit(
                "gate_outcome", gate=verdict.gate, mode=req.lifecycle.value,
                entry_condition="met" if verdict.entry_condition_met else "not_met",
                verdict=verdict.verdict, reason=verdict.reason, proceeded=verdict.proceeded,
                wp_id=wp_id, actor_role=actor_role, **req.provenance,
            )

        # 4. Human-confirmation gate — ALWAYS on, BUILD included (A17 §4).
        if spec.confirm:
            # 4a. Soft control (A10 §7 / D-14): on the *unverified* path, a sensitive
            #     action with no declared role context warns and requires explicit
            #     acknowledgement. A verified principal always carries a role, so it
            #     skips this and gets real authority validation (4b) instead.
            if principal is None and requires_role_ack(spec.confirm, actor_role):
                ack_message = (
                    f"No role context declared for {spec.action_type} on "
                    f"{wp_id or '<no wp>'} — acknowledge proceeding as an undeclared role? (Yes/No)"
                )
                acknowledged = self.confirm(ack_message)
                self.audit.emit(
                    "role_consistency_warning", action_type=spec.action_type, wp_id=wp_id,
                    declared_role=actor_role or "", acknowledged=acknowledged,
                    message=ack_message,
                )
                if not acknowledged:
                    return self._refuse(
                        spec, action_id, "ROLE_CONTEXT_UNACKNOWLEDGED",
                        "sensitive action without declared role context; acknowledgement declined",
                        verdict,
                    )

            # 4b. Verified authority validation (M-IDENTITY / D-16 soft role map).
            #     Lifts the A09 §6.2 deferral: now that identity is verified, validate
            #     real-world authority for this sensitive action. SOFT — a lacking
            #     authority is a warn-with-ack, never a hard refusal (R6; hard -> C4).
            if principal is not None:
                refusal = self._validate_authority(spec, action_id, wp_id, principal, req, verdict)
                if refusal is not None:
                    return refusal

            message = f"Confirm {spec.action_type} on {wp_id or '<no wp>'} (Yes/No)"
            accepted = self.confirm(message)
            self.audit.emit(
                "confirmation", action_type=spec.action_type, wp_id=wp_id,
                actor_role=actor_role, accepted=accepted, message=message,
            )
            if not accepted:
                # A No leaves the WP in its prior state; truth is not mutated.
                return self._refuse(spec, action_id, "CONFIRMATION_REFUSED",
                                    "human declined at confirmation gate", verdict)

        # 5. Execute the handler against the L1 path.
        try:
            result = handler()
        except SchemaValidationError as exc:
            return self._refuse(spec, action_id, "RESULT_SCHEMA_INVALID", str(exc), verdict)

        # 6. Validate the result against its declared result schema (fail-closed).
        if spec.result_schema_ref:
            try:
                self.schemas.validate(result, spec.result_schema_ref)
            except SchemaValidationError as exc:
                return self._refuse(spec, action_id, "RESULT_SCHEMA_INVALID",
                                    "; ".join(exc.errors), verdict)

        # 7. Build + validate the response envelope (fail-closed).
        response_env = {
            "contract": spec.contract_id,
            "contract_version": spec.contract_version,
            "action_id": action_id,
            "ok": True,
            "result": result,
            "error": None,
        }
        self.schemas.validate(response_env, "schemas/contracts/contract_response.schema.json")

        # 8. Output stamp (A18 §3) on the single audit channel.
        stamp = self._stamp(req, spec, result)
        self.audit.emit("output_stamp", action_type=spec.action_type, **stamp)

        return DispatchResult(True, response_env, result, verdict, stamp, spec)

    # -- helpers ------------------------------------------------------------

    def _stamp(self, req: StepRequest, spec: ActionSpec, result: dict) -> dict:
        principal = req.principal
        actor_role = principal.role if principal else req.actor_role
        actor_name = principal.name if principal else req.actor_name
        stamp = {
            "runtime_mode": req.runtime_mode.value,
            "lifecycle": req.lifecycle.value,
            "engine_authority": req.engine_mode,
            "state": req.state,
            "wp_id": req.target.get("wp_id", ""),
            "actor_role": actor_role,                # A10 §7: log the role on outputs
            "identity_verified": bool(principal),    # M-IDENTITY: true once verified
            "result_hash": canonical_hash(result),
            **req.provenance,
        }
        if actor_name:
            stamp["actor_name"] = actor_name
        if principal:                                # the populated A09 §6.2 seam
            stamp["actor_id"] = principal.id
            stamp["profile"] = principal.profile
        if req.lifecycle is Lifecycle.BUILD:
            stamp["testing_only"] = True
            stamp["testing_only_stamp"] = PRODUCT_TESTING_ONLY
        return stamp

    def _validate_authority(
        self, spec, action_id, wp_id, principal, req, verdict,
    ) -> "DispatchResult | None":
        """D-16 soft authority validation for a verified principal on a confirm action.

        Returns a refusal DispatchResult only when a soft warn-with-ack is *declined*;
        otherwise (authorized, or warned+acknowledged) returns None and dispatch
        proceeds. admin is always authorized and always logged (A10 §8).
        """
        av = authorize(principal.profile, spec)

        # admin: authorized for everything, always logged (D-16 / A10 §8).
        if principal.profile == "admin":
            self.audit.emit(
                "security_event", event_type="EVT_ADMIN_ACTION", phase="authorization",
                actor_id=principal.id, profile=principal.profile,
                action_type=spec.action_type, wp_id=wp_id,
                rationale="admin authority — authorized for all actions (always logged)",
                affected_artifacts=[wp_id] if wp_id else [],
            )
        elif not av.authorized:
            # Soft: warn-with-ack. Not a hard RBAC refusal (R6) — hard enforcement -> C4.
            ack_message = (
                f"Authority warning: profile '{principal.profile}' is not authorized for "
                f"{spec.action_type} on {wp_id or '<no wp>'} — acknowledge proceeding "
                f"(testing only)? (Yes/No)"
            )
            acknowledged = self.confirm(ack_message)
            self.audit.emit(
                "authority_warning", action_type=spec.action_type, wp_id=wp_id,
                actor_id=principal.id, profile=principal.profile, category=av.category,
                reason=av.reason, acknowledged=acknowledged, message=ack_message,
            )
            if not acknowledged:
                self.audit.emit(
                    "security_event", event_type="EVT_SECURITY_POLICY_BLOCK",
                    phase="authorization", actor_id=principal.id, profile=principal.profile,
                    action_type=spec.action_type, wp_id=wp_id,
                    rationale=f"authority not acknowledged: {av.reason}",
                    affected_artifacts=[wp_id] if wp_id else [],
                )
                return self._refuse(
                    spec, action_id, "AUTHORITY_UNACKNOWLEDGED", av.reason, verdict,
                )

        # Controlled-document finalize: approver(s) != author, over the full signed
        # approver set. Recorded at the engine/audit layer (zero pack change); soft.
        if spec.action_type == "DOC_FINALIZE_ARTIFACT":
            approvers = req.approvals or (
                Approval(approver_id=principal.id, role=principal.role, name=principal.name),
            )
            decision = evaluate_approval(req.author_id or principal.id, approvers)
            self.audit.emit(
                "document_approval", action_type=spec.action_type, wp_id=wp_id,
                author_id=req.author_id or principal.id,
                approver_set=[{"id": a.approver_id, "role": a.role, "name": a.name or ""}
                              for a in approvers],
                approver_author_conflict=decision.conflict, reason=decision.reason,
            )
            if decision.conflict:
                # Single-user: author is also the approver -> soft warn-with-ack.
                ack_message = (
                    f"Approver(s) must differ from the author for {spec.action_type} on "
                    f"{wp_id or '<no wp>'} — acknowledge proceeding (testing only)? (Yes/No)"
                )
                acknowledged = self.confirm(ack_message)
                self.audit.emit(
                    "approver_author_warning", action_type=spec.action_type, wp_id=wp_id,
                    author_id=decision.author_id, approver_ids=list(decision.approver_ids),
                    acknowledged=acknowledged, message=ack_message,
                )
                if not acknowledged:
                    self.audit.emit(
                        "security_event", event_type="EVT_SECURITY_POLICY_BLOCK",
                        phase="document_approval", actor_id=principal.id,
                        profile=principal.profile, action_type=spec.action_type, wp_id=wp_id,
                        rationale="approver(s) != author not acknowledged",
                        affected_artifacts=[wp_id] if wp_id else [],
                    )
                    return self._refuse(
                        spec, action_id, "APPROVER_AUTHOR_CONFLICT_UNACKNOWLEDGED",
                        decision.reason, verdict,
                    )
        return None

    def _refuse(self, spec, action_id, code, message, verdict) -> DispatchResult:
        error = {"code": code, "message": message}
        response_env = {
            "contract": spec.contract_id,
            "contract_version": spec.contract_version,
            "action_id": action_id,
            "ok": False,
            "result": None,
            "error": error,
        }
        # The refusal envelope itself must be valid (fail-closed all the way out).
        self.schemas.validate(response_env, "schemas/contracts/contract_response.schema.json")
        self.audit.emit("refusal", action_type=spec.action_type, code=code, message=message)
        return DispatchResult(False, response_env, None, verdict, {}, spec, error=error)
