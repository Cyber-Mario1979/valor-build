"""B5 project-container invariants (M4 projection over SELECTED_WP_SET).

Proves the Phase-B B5 exit criterion and the D-13 guarantees: an M4 projection
composes ≥2 committed PE-HIGH WPs **read-only**; it imposes **no truth gates** and
**mutates no WP truth**; its **sole control is the scope-bound** (R3 — ALL_WPS, empty
sets, and uncommitted members refused); M4 reaches the projection-only RPT artifact
but **not** the truth path; the projection validates against ``report_result``.
"""
from __future__ import annotations

import pytest

from valor_build.engine.gates import Lifecycle
from valor_build.engine.project import ALL_WPS, ProjectContainer, ScopeBoundError
from valor_build.engine.store import WPStore
from valor_build.modes.runtime import (
    PROJECTION_CONTRACT_ID,
    ModeReachError,
    RuntimeMode,
    is_reachable,
)
from valor_build.project_skeleton import run_project_container
from valor_build.skeleton import run_walking_skeleton

TWO_WPS = ("WP-PEH-A1", "WP-PEH-B2")


# -- the B5 exit slice ------------------------------------------------------

def test_project_composes_two_pe_high_wps(tmp_path):
    result = run_project_container(tmp_path, TWO_WPS)
    assert result.all_ok
    assert result.members_ok
    meta = result.projection.result["artifact_metadata"]
    assert meta["target_scope"] == "SELECTED_WP_SET"
    assert meta["wp_ids"] == list(TWO_WPS)
    assert result.projection.result["report_type"] == "WORK_PACKAGE_STATUS_REPORT"


def test_projection_is_read_only(tmp_path):
    result = run_project_container(tmp_path, TWO_WPS)
    meta = result.projection.result["artifact_metadata"]
    assert meta["projection_only"] is True
    assert meta["mutates_wp_truth"] is False


def test_m4_mutates_no_wp_truth(tmp_path):
    # Run the two M3 slices, snapshot the truth-transition count, then run ONLY the
    # M4 projection and assert the ledger's truth transitions are unchanged.
    from valor_build.engine.audit import AuditLog
    from valor_build.engine.dispatch import Dispatcher, StepRequest
    from valor_build.engine.registry import ContractRegistry
    from valor_build.engine.schemas import SchemaRegistry

    audit = AuditLog()
    for wp_id in TWO_WPS:
        run_walking_skeleton(tmp_path, wp_id=wp_id, audit=audit)
    store = WPStore(tmp_path)
    truth_before = [r for r in store.ledger() if r["event"] == "TRUTH_TRANSITION"]

    container = ProjectContainer.compose("PRJ-X", TWO_WPS, store)
    disp = Dispatcher(ContractRegistry(), SchemaRegistry(), audit, lambda _m: True)
    req = StepRequest(
        action="RPT_GENERATE_STATUS_REPORT", payload={}, target={"project_id": "PRJ-X"},
        runtime_mode=RuntimeMode.M4, lifecycle=Lifecycle.BUILD, engine_mode="EXECUTION",
        actor_role="CQV", state="ARTIFACT", gate=None,
    )
    res = disp.dispatch(req, container.build_status_report)
    assert res.ok

    truth_after = [r for r in WPStore(tmp_path).ledger() if r["event"] == "TRUTH_TRANSITION"]
    # 3 truth transitions per M3 slice (create / commit / apply) × 2 WPs = 6; M4 adds 0.
    assert len(truth_before) == 6
    assert len(truth_after) == len(truth_before)


def test_no_truth_gates_in_m4_projection(tmp_path):
    result = run_project_container(tmp_path, TWO_WPS)
    gate_records = result.audit.of_kind("gate_outcome")
    # Exactly the five canonical gates per M3 member (5 × 2 = 10); the M4 step adds none.
    assert len(gate_records) == 10
    assert {r["gate"] for r in gate_records} == {
        "GATE-Stage", "GATE-Commit", "GATE-Plan", "GATE-Apply", "GATE-Export"
    }
    # Every gate record belongs to a member WP — none to the project-level M4 step.
    assert all(r["wp_id"] in TWO_WPS for r in gate_records)


# -- scope-bound is the sole control (R3, D-13) -----------------------------

def _store_with_two_committed(tmp_path):
    for wp_id in TWO_WPS:
        run_walking_skeleton(tmp_path, wp_id=wp_id)
    return WPStore(tmp_path)


def test_scope_bound_refuses_all_wps_sentinel(tmp_path):
    store = _store_with_two_committed(tmp_path)
    with pytest.raises(ScopeBoundError):
        ProjectContainer.compose("PRJ-X", ALL_WPS, store)          # bare sentinel string
    with pytest.raises(ScopeBoundError):
        ProjectContainer.compose("PRJ-X", [*TWO_WPS, ALL_WPS], store)  # sentinel in the set


def test_scope_bound_refuses_empty_set(tmp_path):
    store = _store_with_two_committed(tmp_path)
    with pytest.raises(ScopeBoundError):
        ProjectContainer.compose("PRJ-X", [], store)


def test_scope_bound_refuses_uncommitted_member(tmp_path):
    store = _store_with_two_committed(tmp_path)
    with pytest.raises(ScopeBoundError):
        ProjectContainer.compose("PRJ-X", ["WP-PEH-A1", "WP-DOES-NOT-EXIST"], store)


def test_scope_bound_refuses_duplicates(tmp_path):
    store = _store_with_two_committed(tmp_path)
    with pytest.raises(ScopeBoundError):
        ProjectContainer.compose("PRJ-X", ["WP-PEH-A1", "WP-PEH-A1"], store)


# -- M4 reachability: projection yes, truth path no -------------------------

def test_m4_reaches_projection_rpt_only(tmp_path):
    # The projection-only RPT artifact is reachable...
    assert is_reachable(RuntimeMode.M4, "GENERATES_ARTIFACT", PROJECTION_CONTRACT_ID)
    assert is_reachable(RuntimeMode.M4, "READ_ONLY")
    # ...but a non-projection GENERATES_ARTIFACT (e.g. a DOC/PLAN contract) is not...
    assert not is_reachable(RuntimeMode.M4, "GENERATES_ARTIFACT", "VALOR-contract-orch-doc")
    # ...and the truth path is never reachable in M4.
    assert not is_reachable(RuntimeMode.M4, "MUTATES_TRUTH", PROJECTION_CONTRACT_ID)
    assert not is_reachable(RuntimeMode.M4, "STAGE_ONLY", PROJECTION_CONTRACT_ID)


def test_m4_cannot_reach_mutating_action(tmp_path):
    from valor_build.engine.audit import AuditLog
    from valor_build.engine.dispatch import Dispatcher, StepRequest
    from valor_build.engine.registry import ContractRegistry
    from valor_build.engine.schemas import SchemaRegistry

    disp = Dispatcher(ContractRegistry(), SchemaRegistry(), AuditLog(), lambda _m: True)
    req = StepRequest(
        action="WP_COMMIT_STAGED_TASKS", payload={}, target={"wp_id": "WP-X"},
        runtime_mode=RuntimeMode.M4, lifecycle=Lifecycle.BUILD, engine_mode="EXECUTION",
        actor_role="CQV", state="WP_COMMITTED", gate=None,
    )
    with pytest.raises(ModeReachError):
        disp.dispatch(req, lambda: {})


# -- projection validity + BUILD stamp --------------------------------------

def test_projection_validates_and_has_nine_sections(tmp_path):
    # ok==True means the result passed report_result.schema.json validation in dispatch.
    result = run_project_container(tmp_path, TWO_WPS)
    assert result.projection.ok
    sections = result.projection.result["report_sections"]
    assert len(sections) >= 9


def test_m4_projection_carries_testing_only_stamp(tmp_path):
    result = run_project_container(tmp_path, TWO_WPS)
    stamps = result.audit.of_kind("output_stamp")
    m4_stamps = [s for s in stamps if s.get("runtime_mode") == "M4"]
    assert len(m4_stamps) == 1
    assert m4_stamps[0].get("testing_only") is True
    assert "NOT APPROVED FOR REAL-LIFE" in m4_stamps[0].get("testing_only_stamp", "")


def test_members_keep_their_own_committed_truth(tmp_path):
    result = run_project_container(tmp_path, TWO_WPS)
    for wp_id in TWO_WPS:
        wp = result.store.load_wp(wp_id)
        assert wp["lifecycle_state"] == "WP_COMMITTED"
        assert wp["tasks"] and wp["tasks"][0]["committed_start_date"]
