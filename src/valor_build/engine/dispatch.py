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
from .identity import RoleContext, actor_block, requires_role_ack
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

        # 0. Capture the declared role context (soft control, A10 §7 / A09 §7.1).
        #    One audited identity_context record per action; identity stays unverified.
        RoleContext.capture(
            self.audit, req.actor_role, name=req.actor_name,
            action_type=spec.action_type, wp_id=wp_id,
        )

        # 1. Build + validate the request envelope (fail-closed).
        request_env = {
            "contract": spec.contract_id,
            "contract_version": spec.contract_version,
            "action_id": action_id,
            "action_type": spec.action_type,
            "mode": req.engine_mode,
            "actor": actor_block(req.actor_role, req.actor_name),
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
                    proceeded=False, wp_id=wp_id, actor_role=req.actor_role,
                )
                raise
            self.audit.emit(
                "gate_outcome", gate=verdict.gate, mode=req.lifecycle.value,
                entry_condition="met" if verdict.entry_condition_met else "not_met",
                verdict=verdict.verdict, reason=verdict.reason, proceeded=verdict.proceeded,
                wp_id=wp_id, actor_role=req.actor_role, **req.provenance,
            )

        # 4. Human-confirmation gate — ALWAYS on, BUILD included (A17 §4).
        if spec.confirm:
            # 4a. Soft control (A10 §7 / D-14): a sensitive action with no declared
            #     role context warns and requires explicit acknowledgement. Stays soft
            #     — no role->action authority map; that arrives with M-IDENTITY.
            if requires_role_ack(spec.confirm, req.actor_role):
                ack_message = (
                    f"No role context declared for {spec.action_type} on "
                    f"{wp_id or '<no wp>'} — acknowledge proceeding as an undeclared role? (Yes/No)"
                )
                acknowledged = self.confirm(ack_message)
                self.audit.emit(
                    "role_consistency_warning", action_type=spec.action_type, wp_id=wp_id,
                    declared_role=req.actor_role or "", acknowledged=acknowledged,
                    message=ack_message,
                )
                if not acknowledged:
                    return self._refuse(
                        spec, action_id, "ROLE_CONTEXT_UNACKNOWLEDGED",
                        "sensitive action without declared role context; acknowledgement declined",
                        verdict,
                    )

            message = f"Confirm {spec.action_type} on {wp_id or '<no wp>'} (Yes/No)"
            accepted = self.confirm(message)
            self.audit.emit(
                "confirmation", action_type=spec.action_type, wp_id=wp_id,
                actor_role=req.actor_role, accepted=accepted, message=message,
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
        stamp = {
            "runtime_mode": req.runtime_mode.value,
            "lifecycle": req.lifecycle.value,
            "engine_authority": req.engine_mode,
            "state": req.state,
            "wp_id": req.target.get("wp_id", ""),
            "actor_role": req.actor_role,            # A10 §7: log the declared role on outputs
            "result_hash": canonical_hash(result),
            **req.provenance,
        }
        if req.actor_name:
            stamp["actor_name"] = req.actor_name
        if req.lifecycle is Lifecycle.BUILD:
            stamp["testing_only"] = True
            stamp["testing_only_stamp"] = PRODUCT_TESTING_ONLY
        return stamp

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
