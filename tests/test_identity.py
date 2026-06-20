"""B7 identity soft-control invariants (G-07, D-14 / Option A).

Proves the Phase-B B7 exit criterion's *now* half: declared role-context is captured
and audited; the role is stamped on every output; the frozen envelope already carries
``actor.id`` (the M-IDENTITY seam); and the warn-with-ack soft control fires for a
sensitive action with no declared role — staying *soft* (warn + acknowledge), never a
hard authorization gate. D-14 keeps a role->action authority map and real authority
validation out of scope here; both are the named cryptographic-identity milestone.
"""
from __future__ import annotations

import pytest

from valor_build.engine.audit import AuditLog
from valor_build.engine.dispatch import Dispatcher, StepRequest
from valor_build.engine.identity import RoleContext, actor_block, requires_role_ack
from valor_build.engine.registry import ContractRegistry
from valor_build.engine.schemas import SchemaRegistry
from valor_build.engine.gates import Lifecycle
from valor_build.modes.runtime import RuntimeMode
from valor_build.skeleton import run_walking_skeleton


def _dispatcher(confirm=lambda _m: True):
    return Dispatcher(ContractRegistry(), SchemaRegistry(), AuditLog(), confirm)


# -- capture + audit --------------------------------------------------------

def test_role_context_captured_and_audited(tmp_path):
    result = run_walking_skeleton(tmp_path)
    ctx_events = result.audit.of_kind("identity_context")
    # One capture per dispatched action in the 8-step slice.
    assert len(ctx_events) == 8
    assert all(e["declared_role"] == "CQV" for e in ctx_events)
    # Soft control: identity is never cryptographically verified in v0.x.
    assert all(e["identity_verified"] is False for e in ctx_events)


def test_declared_role_stamped_on_every_output(tmp_path):
    result = run_walking_skeleton(tmp_path)
    stamps = result.audit.of_kind("output_stamp")
    assert stamps and all(s.get("actor_role") == "CQV" for s in stamps)


def test_capture_helper_emits_one_event():
    audit = AuditLog()
    ctx = RoleContext.capture(audit, "QA reviewer", name="A. Tester", action_type="WP_CREATE")
    assert ctx.role == "QA reviewer"
    assert ctx.id is None                       # crypto seam: reserved, unset in v0.x
    events = audit.of_kind("identity_context")
    assert len(events) == 1
    assert events[0]["actor_name"] == "A. Tester"


# -- the actor block + the M-IDENTITY (actor.id) seam -----------------------

def test_actor_block_is_backward_compatible():
    # No name/id -> identical to the prior {"role": ...} envelope shape.
    assert actor_block("CQV") == {"role": "CQV"}
    assert actor_block("CQV", "Jane") == {"role": "CQV", "name": "Jane"}
    assert actor_block("CQV", "Jane", "did:example:abc") == {
        "role": "CQV", "name": "Jane", "id": "did:example:abc"
    }


def test_actor_id_validates_through_frozen_envelope():
    # The crypto seam: an actor.id rides the frozen contract_request envelope today,
    # so M-IDENTITY needs no pack/schema change. Validate the block directly.
    schemas = SchemaRegistry()
    env = {
        "contract": "VALOR-contract-orch-wp",
        "contract_version": "v1.0.1",
        "action_id": "WP_CREATE:deadbeef0001",
        "action_type": "WP_CREATE",
        "mode": "EXECUTION",
        "actor": actor_block("CQV", "Jane", "did:example:abc"),
        "target": {"wp_id": "WP-X"},
        "payload": {},
        "context": {"timestamp_utc": "2026-06-20T00:00:00+00:00"},
    }
    # Should not raise — additionalProperties:true on actor permits id.
    schemas.validate(env, "schemas/contracts/contract_request.schema.json")


# -- warn-with-ack soft control (A10 §7, D-14 / Option A) -------------------

def test_requires_role_ack_predicate():
    # Sensitive (confirm) action, blank role -> ack required.
    assert requires_role_ack(True, "") is True
    assert requires_role_ack(True, "   ") is True
    # Declared role -> no ack.
    assert requires_role_ack(True, "CQV") is False
    # Non-sensitive action -> never (no confirm, no map).
    assert requires_role_ack(False, "") is False


def test_blank_role_on_sensitive_action_requires_acknowledgement():
    # WP_CREATE is confirm:true. Blank role + a declining provider -> refusal.
    disp = _dispatcher(confirm=lambda _m: False)
    req = StepRequest(
        action="WP_CREATE", payload={}, target={"wp_id": "WP-X"},
        runtime_mode=RuntimeMode.M3, lifecycle=Lifecycle.BUILD, engine_mode="EXECUTION",
        actor_role="", state="WP_DRAFT", gate=None,
    )
    res = disp.dispatch(req, lambda: {})
    assert not res.ok
    assert res.error["code"] == "ROLE_CONTEXT_UNACKNOWLEDGED"
    warnings = disp.audit.of_kind("role_consistency_warning")
    assert len(warnings) == 1 and warnings[0]["acknowledged"] is False


def test_blank_role_proceeds_past_identity_gate_when_acknowledged():
    # Same blank-role sensitive action, but the actor acknowledges -> the identity
    # soft control lets it through (it is *soft*). The handler returns an invalid
    # object so the call refuses downstream at result-schema validation — which proves
    # control passed the ack gate into execution, not stopped at ROLE_CONTEXT_UNACKNOWLEDGED.
    disp = _dispatcher(confirm=lambda _m: True)
    req = StepRequest(
        action="WP_CREATE", payload={}, target={"wp_id": "WP-X"},
        runtime_mode=RuntimeMode.M3, lifecycle=Lifecycle.BUILD, engine_mode="EXECUTION",
        actor_role="", state="WP_DRAFT", gate=None,
    )
    res = disp.dispatch(req, lambda: {})        # deliberately schema-invalid result
    warnings = disp.audit.of_kind("role_consistency_warning")
    assert len(warnings) == 1 and warnings[0]["acknowledged"] is True
    # Got past identity: any refusal is a *downstream* one, never the role code.
    assert res.error is None or res.error["code"] != "ROLE_CONTEXT_UNACKNOWLEDGED"
    assert res.error is not None and res.error["code"] == "RESULT_SCHEMA_INVALID"


def test_declared_role_does_not_trigger_warning(tmp_path):
    # The normal slice (role=CQV) never raises a role-consistency warning.
    result = run_walking_skeleton(tmp_path)
    assert result.all_ok
    assert result.audit.of_kind("role_consistency_warning") == []
