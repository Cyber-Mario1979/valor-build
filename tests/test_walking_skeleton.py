"""B6 walking-skeleton invariants (replaces the trivial scaffold test).

These tests prove the Phase-B B6 exit criterion and the cross-cutting guarantees the
specs require: full vertical slice runs against PE-HIGH; gates are log-only in BUILD
and halt in LIVE; the human-confirmation gate is always live; truth-store integrity
(never-reused IDs, fail-closed validation) holds; the D-08 AI call is audited.
"""
from __future__ import annotations

import pytest

from valor_build.engine.dispatch import Dispatcher, StepRequest
from valor_build.engine.gates import GATE_PLAN, GateBlocked, Lifecycle
from valor_build.engine.registry import ContractRegistry
from valor_build.engine.schemas import SchemaRegistry
from valor_build.engine.store import IdReuseError, WPStore
from valor_build.modes.runtime import ModeReachError, RuntimeMode
from valor_build.skeleton import run_walking_skeleton


# -- the full slice ---------------------------------------------------------

def test_full_slice_runs_end_to_end(tmp_path):
    result = run_walking_skeleton(tmp_path)
    assert result.all_ok
    actions = [s["action"] for s in result.steps]
    assert actions == [
        "WP_CREATE", "WP_STAGE_TASKS", "WP_COMMIT_STAGED_TASKS",
        "PLAN_GENERATE_PROPOSAL", "WP_APPLY_PLAN_PROPOSAL",
        "DOC_GENERATE_DRAFT", "DOC_FINALIZE_ARTIFACT", "RPT_GENERATE_WORKBOOK_EXPORT",
    ]


def test_all_five_canonical_gates_logged(tmp_path):
    result = run_walking_skeleton(tmp_path)
    gates = {r["gate"] for r in result.audit.of_kind("gate_outcome")}
    assert gates == {"GATE-Stage", "GATE-Commit", "GATE-Plan", "GATE-Apply", "GATE-Export"}


def test_committed_truth_is_persisted(tmp_path):
    result = run_walking_skeleton(tmp_path)
    wp = result.store.load_wp(result.wp_id)
    assert wp["lifecycle_state"] == "WP_COMMITTED"
    assert len(wp["tasks"]) == 1
    task = wp["tasks"][0]
    # Plan was applied: committed dates are populated.
    assert task["committed_start_date"] and task["committed_finish_date"]


# -- gates: log-only in BUILD, halt in LIVE ---------------------------------

def _dispatcher(tmp_path):
    registry = ContractRegistry()
    schemas = SchemaRegistry()
    from valor_build.engine.audit import AuditLog
    audit = AuditLog()
    disp = Dispatcher(registry, schemas, audit, lambda _m: True)
    return disp, audit


def test_unmet_gate_proceeds_in_build(tmp_path):
    disp, audit = _dispatcher(tmp_path)
    # PLAN_GENERATE_PROPOSAL with an UNMET entry condition, BUILD -> log-only, proceeds.
    req = StepRequest(
        action="PLAN_GENERATE_PROPOSAL", payload={}, target={"wp_id": "WP-X"},
        runtime_mode=RuntimeMode.M3, lifecycle=Lifecycle.BUILD, engine_mode="EXECUTION",
        actor_role="CQV", state="PROPOSED", gate=GATE_PLAN, entry_condition_met=False,
        gate_reason="WP not committed",
    )
    minimal_plan = _minimal_plan_proposal("WP-X")
    res = disp.dispatch(req, lambda: minimal_plan)
    assert res.ok
    assert res.verdict.verdict == "WOULD_BLOCK"
    assert res.verdict.proceeded is True


def test_unmet_gate_halts_in_live(tmp_path):
    disp, audit = _dispatcher(tmp_path)
    req = StepRequest(
        action="PLAN_GENERATE_PROPOSAL", payload={}, target={"wp_id": "WP-X"},
        runtime_mode=RuntimeMode.M3, lifecycle=Lifecycle.LIVE, engine_mode="EXECUTION",
        actor_role="CQV", state="PROPOSED", gate=GATE_PLAN, entry_condition_met=False,
        gate_reason="WP not committed",
    )
    with pytest.raises(GateBlocked):
        disp.dispatch(req, lambda: _minimal_plan_proposal("WP-X"))


# -- human-confirmation gate stays live in BUILD ----------------------------

def test_confirmation_no_leaves_truth_unmutated(tmp_path):
    # A "No" provider: every confirm:true step is refused -> slice stops at WP_CREATE,
    # and no WP truth is written.
    result = run_walking_skeleton(tmp_path, confirm_provider=lambda _m: False)
    assert not result.all_ok
    assert result.steps[0]["action"] == "WP_CREATE"
    assert result.steps[0]["ok"] is False
    assert result.store.load_wp(result.wp_id) is None
    refusals = result.audit.of_kind("refusal")
    assert any(r["code"] == "CONFIRMATION_REFUSED" for r in refusals)


# -- BUILD stamps + R5 guard ------------------------------------------------

def test_build_outputs_carry_testing_only_stamp(tmp_path):
    result = run_walking_skeleton(tmp_path)
    stamps = result.audit.of_kind("output_stamp")
    assert stamps and all(s.get("testing_only") is True for s in stamps)
    assert all("NOT APPROVED FOR REAL-LIFE" in s.get("testing_only_stamp", "") for s in stamps)


# -- truth-store integrity --------------------------------------------------

def test_ids_are_never_reused(tmp_path):
    store = WPStore(tmp_path)
    store.allocate_id("WP-1")
    with pytest.raises(IdReuseError):
        store.allocate_id("WP-1")


# -- runtime mode reachability (A18) ---------------------------------------

def test_m1_cannot_reach_mutating_action(tmp_path):
    disp, _ = _dispatcher(tmp_path)
    req = StepRequest(
        action="WP_COMMIT_STAGED_TASKS", payload={}, target={"wp_id": "WP-X"},
        runtime_mode=RuntimeMode.M1, lifecycle=Lifecycle.BUILD, engine_mode="EXECUTION",
        actor_role="CQV", state="WP_COMMITTED", gate=None,
    )
    with pytest.raises(ModeReachError):
        disp.dispatch(req, lambda: {})


# -- D-08 AI call is audited with provenance --------------------------------

def test_ai_call_audited_with_hashes(tmp_path):
    result = run_walking_skeleton(tmp_path)
    ai_calls = result.audit.of_kind("ai_call")
    assert len(ai_calls) == 1
    call = ai_calls[0]
    assert call["outcome"] == "ACCEPT"
    assert call["prompt_version"] and call["input_hash"].startswith("sha256:")
    assert call["output_hash"].startswith("sha256:")


# -- helpers ----------------------------------------------------------------

def _minimal_plan_proposal(wp_id: str) -> dict:
    return {
        "action_type": "PLAN_GENERATE_PROPOSAL",
        "plan_proposal_id": f"{wp_id}-PLAN-001",
        "wp_id": wp_id,
        "state": "PROPOSED",
        "apply_required": True,
        "planning_basis": "PROFILE_BASED",
        "calendar_logic_ref": {"calendar_id": "CAL-WORKWEEK", "calendar_version": "v1.0.1", "canonical_calendar_version": "v1"},
        "schedule": [{
            "task_id": f"{wp_id}-T001", "proposed_start_date": "2026-07-01",
            "proposed_finish_date": "2026-07-28", "duration_value": 20, "duration_unit": "WORKING_DAYS",
        }],
        "provenance_stamps": {"profile": "PROF-PE-HIGH"},
        "validation_result": {"ok": True, "errors": [], "warnings": []},
    }
