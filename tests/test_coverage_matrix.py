"""C1 Engine coverage-matrix invariants (Phase C, Session 19).

Asserts the action x class x mode grid over PS-PE-HIGH: every active action is
exercised in each reachable mode and recorded N/A (with a reach reason) where its
side-effect class is unreachable. Locks the D-15 advisory-mode model and the
A18 §2 reach rules against regression.
"""
from __future__ import annotations

from valor_build.coverage import (
    ACTIVE_STATUSES,
    PS_CONTRACT_ID,
    run_coverage_matrix,
    summarize,
)
from valor_build.engine.registry import ContractRegistry
from valor_build.modes.runtime import RuntimeMode


def _cells(tmp_path):
    return run_coverage_matrix(tmp_path)


# -- shape -----------------------------------------------------------------

def test_matrix_is_96_entries_all_green(tmp_path):
    cells = _cells(tmp_path)
    s = summarize(cells)
    assert s["total_cells"] == 96, s
    assert s["failed"] == [], [(c.action_type, c.mode, c.note) for c in s["failed"]]
    assert s["action_count"] == 27


def test_grid_partition_92_mode_gated_plus_4_ps(tmp_path):
    cells = _cells(tmp_path)
    mode_gated = [c for c in cells if c.mode in {"M1", "M2", "M3", "M4"}]
    engine_internal = [c for c in cells if c.mode == "ENGINE_INTERNAL"]
    assert len(mode_gated) == 92
    assert len(engine_internal) == 4
    assert all(c.contract_id == PS_CONTRACT_ID for c in engine_internal)
    assert all(c.outcome == "EXERCISED" for c in engine_internal)


def test_registry_active_set_is_27_excludes_testing_only(tmp_path):
    reg = ContractRegistry()
    active = [s for s in reg.all_actions() if s.status in ACTIVE_STATUSES]
    testing_only = [s for s in reg.all_actions() if s.status == "TESTING_ONLY_FROZEN"]
    assert len(active) == 27          # 23 ACTIVE_FROZEN + 4 ACTIVE_INTERNAL_FROZEN
    assert len(testing_only) == 12    # the KS class, out of this matrix
    covered = {c.action_type for c in _cells(tmp_path)}
    assert covered == {s.action_type for s in active}


# -- reach invariants (A18 §2 / D-15) --------------------------------------

def test_m3_reaches_every_mode_gated_action(tmp_path):
    cells = _cells(tmp_path)
    m3 = [c for c in cells if c.mode == "M3"]
    assert len(m3) == 23
    assert all(c.outcome == "EXERCISED" for c in m3)


def test_mutating_and_staging_classes_reach_only_m3(tmp_path):
    cells = _cells(tmp_path)
    for c in cells:
        if c.side_effect in {"MUTATES_TRUTH", "STAGE_ONLY"} and c.mode in {"M1", "M2", "M4"}:
            assert c.outcome == "N/A", (c.action_type, c.mode)
            assert "unreachable" in c.note


def test_m1_and_m2_are_advisory_no_contracted_generation(tmp_path):
    """D-15: M1 & M2 reach READ_ONLY + VALIDATE_ONLY only — no GENERATES_ARTIFACT."""
    cells = _cells(tmp_path)
    for mode in ("M1", "M2"):
        gen = [c for c in cells if c.mode == mode and c.side_effect == "GENERATES_ARTIFACT"]
        assert gen and all(c.outcome == "N/A" for c in gen), mode
        exercised = {c.side_effect for c in cells if c.mode == mode and c.outcome == "EXERCISED"}
        assert exercised <= {"READ_ONLY", "VALIDATE_ONLY"}, (mode, exercised)


def test_m1_and_m2_have_identical_reach(tmp_path):
    cells = _cells(tmp_path)
    m1 = {c.action_type for c in cells if c.mode == "M1" and c.outcome == "EXERCISED"}
    m2 = {c.action_type for c in cells if c.mode == "M2" and c.outcome == "EXERCISED"}
    assert m1 == m2


def test_m4_reaches_read_only_plus_projection_rpt_only(tmp_path):
    """M4: READ_ONLY everywhere + GENERATES_ARTIFACT only on the RPT projection contract."""
    cells = _cells(tmp_path)
    m4_exercised = [c for c in cells if c.mode == "M4" and c.outcome == "EXERCISED"]
    for c in m4_exercised:
        if c.side_effect == "GENERATES_ARTIFACT":
            assert c.contract_id == "VALOR-contract-orch-rpt", c.action_type
        else:
            assert c.side_effect == "READ_ONLY", (c.action_type, c.side_effect)
    # no MUTATES_TRUTH / STAGE_ONLY truth path in M4 (D-13)
    assert not any(
        c.mode == "M4" and c.outcome == "EXERCISED"
        and c.side_effect in {"MUTATES_TRUTH", "STAGE_ONLY"}
        for c in cells
    )


def test_every_na_cell_records_a_reach_reason(tmp_path):
    cells = _cells(tmp_path)
    for c in cells:
        if c.outcome == "N/A":
            assert c.note and "unreachable" in c.note, (c.action_type, c.mode)
