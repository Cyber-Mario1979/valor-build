"""C1 Engine — coverage matrix (Phase C, Session 19; G-02 / D-07 surface).

Drives every **active** action in the frozen registry across the runtime-mode
grid over the single ``PS-PE-HIGH`` preset, reusing the B6 walking-skeleton seed
+ dispatch/store/audit/stamp spine. The action set is read **live** from
``CONTRACT_REGISTRY_v1.0.1.yaml`` via ``ContractRegistry`` (A16 §4) — no action
list is hard-coded here, so a pack v1.1.0 action enters the matrix by pattern.

Grid shape (owner decisions, S19):
  * 23 mode-gated active actions  x  4 runtime modes (M1-M4)  = 92 cells
  * 4 PS internal-resolver actions, engine-internal / mode-agnostic = 4 entries
  * total = 96 coverage entries.

Each cell is **EXERCISED** (dispatched green in that mode, or covered by the B6
seed in M3) or **N/A** (the action's side-effect class is unreachable in that
mode — A18 §2 / D-15 — with the ModeReachError reason recorded). M3 is the only
mode reaching MUTATES_TRUTH/STAGE_ONLY; M1 & M2 are advisory (D-15); M4 reaches
READ_ONLY + the projection-only RPT GENERATES_ARTIFACT exception (D-13).

No pack edits; BUILD lifecycle, gates log-only (A17); outputs PRODUCT_TESTING_ONLY.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .ai.interface import LLMInterface
from .engine.coverage_handlers import CoverageHandlers
from .engine.dispatch import Dispatcher, StepRequest
from .engine.domain import PEHighDomain
from .engine.gates import Lifecycle
from .engine.registry import ContractRegistry
from .engine.schemas import SchemaRegistry
from .modes.runtime import RuntimeMode, ModeReachError, is_reachable, require_reachable
from .skeleton import auto_yes, run_walking_skeleton

ACTIVE_STATUSES = {"ACTIVE_FROZEN", "ACTIVE_INTERNAL_FROZEN"}
PS_CONTRACT_ID = "VALOR-contract-orch-ps"
GRID_MODES = (RuntimeMode.M1, RuntimeMode.M2, RuntimeMode.M3, RuntimeMode.M4)

# action_type -> CoverageHandlers method. The 8 B6 actions + 19 C1 actions = 27.
HANDLER_METHOD = {
    # B6 vertical (seeded by the walking skeleton)
    "WP_CREATE": "create_wp",
    "WP_STAGE_TASKS": "stage_tasks",
    "WP_COMMIT_STAGED_TASKS": "commit_staged_tasks",
    "PLAN_GENERATE_PROPOSAL": "generate_plan_proposal",
    "WP_APPLY_PLAN_PROPOSAL": "apply_plan_proposal",
    "DOC_GENERATE_DRAFT": "generate_doc_draft",
    "DOC_FINALIZE_ARTIFACT": "finalize_doc_artifact",
    "RPT_GENERATE_WORKBOOK_EXPORT": "export_workbook",
    # C1 remainder
    "WP_GET": "wp_get",
    "WP_UPDATE_TASK_FIELDS": "update_task_fields",
    "WP_BIND_PRESET_CONTEXT": "bind_preset_context",
    "WP_SET_PLANNING_BASIS": "set_planning_basis",
    "WP_SET_TASK_DURATION_OVERRIDES": "set_task_duration_overrides",
    "WP_RECORD_CONFIRMATION": "record_confirmation",
    "PLAN_VALIDATE_PROPOSAL": "validate_plan_proposal",
    "RPT_GENERATE_STATUS_REPORT": "generate_status_report",
    "RPT_VALIDATE_REPORT_INPUTS": "validate_report_inputs",
    "RPT_VALIDATE_WORKBOOK_EXPORT": "validate_workbook_export",
    "RPT_GENERATE_GANTT_CHART": "generate_gantt_chart",
    "RPT_VALIDATE_GANTT_INPUTS": "validate_gantt_inputs",
    "RPT_VALIDATE_STAMPS": "validate_stamps",
    "RPT_LIST_ARTIFACTS": "list_artifacts",
    "RPT_GET_ARTIFACT": "get_artifact",
    "PS_LIST_PRESETS": "ps_list_presets",
    "PS_READ_PRESET": "ps_read_preset",
    "PS_RESOLVE_PRESET": "ps_resolve_preset",
    "PS_VALIDATE_BINDINGS": "ps_validate_bindings",
}

# B6 actions whose handler allocates a never-reused id — re-dispatching against a
# seeded WP would (correctly) raise IdReuseError. Their M3 cell is covered by the
# seed run; we don't re-dispatch them.
SEED_NO_REDISPATCH = {"WP_CREATE", "WP_COMMIT_STAGED_TASKS"}
B6_ACTIONS = {
    "WP_CREATE", "WP_STAGE_TASKS", "WP_COMMIT_STAGED_TASKS", "PLAN_GENERATE_PROPOSAL",
    "WP_APPLY_PLAN_PROPOSAL", "DOC_GENERATE_DRAFT", "DOC_FINALIZE_ARTIFACT",
    "RPT_GENERATE_WORKBOOK_EXPORT",
}


@dataclass
class Cell:
    action_type: str
    contract_id: str
    side_effect: str
    mode: str            # "M1".."M4" or "ENGINE_INTERNAL"
    outcome: str         # "EXERCISED" | "N/A" | "FAILED"
    note: str = ""       # reach reason (N/A) or "seed:B6" / error detail


def active_specs(registry: ContractRegistry) -> list:
    """The 27 active actions, sorted by registry order then type for stability."""
    specs = [s for s in registry.all_actions() if s.status in ACTIVE_STATUSES]
    return sorted(specs, key=lambda s: (s.contract_id, s.action_type))


def run_coverage_matrix(store_root: Path | str, *, pack_root: Path | None = None) -> list[Cell]:
    """Seed the B6 WP, then fill the 96-entry grid. Returns the cell list."""
    # 1. Seed a committed + planned + documented + exported WP (the B6 milestone).
    seed = run_walking_skeleton(store_root, pack_root=pack_root)
    assert seed.all_ok, "coverage seed (walking skeleton) did not run green"

    registry = ContractRegistry(pack_root)
    schemas = SchemaRegistry(pack_root)
    domain = PEHighDomain.load(pack_root)
    ai = LLMInterface(schemas, seed.audit)
    handlers = CoverageHandlers(seed.wp_id, seed.store, domain, ai)
    dispatcher = Dispatcher(registry, schemas, seed.audit, auto_yes)
    target = {"wp_id": seed.wp_id}

    def step(action_type: str, mode: RuntimeMode) -> StepRequest:
        return StepRequest(
            action=action_type, payload={}, target=target, runtime_mode=mode,
            lifecycle=Lifecycle.BUILD, engine_mode="EXECUTION", actor_role="CQV",
            state="", gate=None, entry_condition_met=True,
        )

    cells: list[Cell] = []
    for spec in active_specs(registry):
        at, cid, se = spec.action_type, spec.contract_id, spec.side_effect
        method = getattr(handlers, HANDLER_METHOD[at])

        # PS internal resolver — engine-internal / mode-agnostic (one entry).
        if cid == PS_CONTRACT_ID:
            res = dispatcher.dispatch(step(at, RuntimeMode.M3), method)
            cells.append(Cell(at, cid, se, "ENGINE_INTERNAL",
                              "EXERCISED" if res.ok else "FAILED",
                              "engine-internal resolver (S19)" if res.ok else str(res.error)))
            continue

        # Mode-gated action: one cell per runtime mode.
        for mode in GRID_MODES:
            if not is_reachable(mode, se, cid):
                try:
                    require_reachable(mode, se, cid)
                    reason = ""
                except ModeReachError as exc:
                    reason = str(exc)
                cells.append(Cell(at, cid, se, mode.value, "N/A", reason))
                continue

            # Reachable. B6 M3 cells are covered by the seed run (don't re-dispatch
            # the id-allocating ones). Everything else is dispatched live here.
            if at in B6_ACTIONS and mode is RuntimeMode.M3 and at in SEED_NO_REDISPATCH:
                cells.append(Cell(at, cid, se, mode.value, "EXERCISED", "seed:B6"))
                continue
            if at in B6_ACTIONS and mode is RuntimeMode.M3:
                cells.append(Cell(at, cid, se, mode.value, "EXERCISED", "seed:B6"))
                continue
            res = dispatcher.dispatch(step(at, mode), method)
            cells.append(Cell(at, cid, se, mode.value,
                              "EXERCISED" if res.ok else "FAILED",
                              "" if res.ok else str(res.error)))
    return cells


# -- reporting -------------------------------------------------------------

def summarize(cells: list[Cell]) -> dict:
    total = len(cells)
    exercised = sum(1 for c in cells if c.outcome == "EXERCISED")
    na = sum(1 for c in cells if c.outcome == "N/A")
    failed = [c for c in cells if c.outcome == "FAILED"]
    actions = sorted({c.action_type for c in cells})
    return {
        "total_cells": total,
        "exercised": exercised,
        "na": na,
        "failed": failed,
        "action_count": len(actions),
    }


def render_markdown(cells: list[Cell]) -> str:
    """Deterministic matrix report (no timestamps) for the committed doc."""
    by_action: dict[str, dict] = {}
    order: list[str] = []
    for c in cells:
        if c.action_type not in by_action:
            by_action[c.action_type] = {"contract": c.contract_id, "se": c.side_effect}
            order.append(c.action_type)
        by_action[c.action_type][c.mode] = (c.outcome, c.note)

    def glyph(entry):
        if entry is None:
            return "—"
        outcome, _ = entry
        return {"EXERCISED": "✅", "N/A": "▫️ N/A", "FAILED": "❌"}[outcome]

    s = summarize(cells)
    lines = [
        "# C1 Engine — Action × Class × Mode Coverage Matrix",
        "",
        "**Phase C / C1 Engine · Step 2 (Coverage).** Generated from the live frozen "
        "registry `CONTRACT_REGISTRY_v1.0.1.yaml` @ `0ec3060` via `engine.registry` "
        "(A16 §4) — no action list hard-coded. Over the single `PS-PE-HIGH` preset, "
        "BUILD lifecycle, gates log-only (A17), outputs `PRODUCT_TESTING_ONLY` (R5).",
        "",
        f"- **Coverage entries:** {s['total_cells']}  "
        f"(23 mode-gated actions × 4 modes = 92, + 4 PS engine-internal = 96)",
        f"- **Exercised:** {s['exercised']}   **N/A-by-reach:** {s['na']}   "
        f"**Failed:** {len(s['failed'])}",
        f"- **Active actions covered:** {s['action_count']} / 27",
        "",
        "Reach rule (A18 §2 / D-15): **M1 & M2 advisory** = `READ_ONLY`+`VALIDATE_ONLY`; "
        "**M3** = all classes (only mode reaching `MUTATES_TRUTH`/`STAGE_ONLY`); "
        "**M4** = `READ_ONLY` + projection-only RPT `GENERATES_ARTIFACT` (D-13). "
        "PS internal-resolver actions are engine-internal / mode-agnostic (S19).",
        "",
        "| Action | Contract | Side-effect | M1 | M2 | M3 | M4 | Engine-internal |",
        "|---|---|---|:--:|:--:|:--:|:--:|:--:|",
    ]
    for at in order:
        row = by_action[at]
        contract = row["contract"].replace("VALOR-contract-orch-", "")
        cells_md = [
            glyph(row.get("M1")), glyph(row.get("M2")), glyph(row.get("M3")),
            glyph(row.get("M4")), glyph(row.get("ENGINE_INTERNAL")),
        ]
        lines.append(f"| `{at}` | {contract} | {row['se']} | " + " | ".join(cells_md) + " |")

    lines += [
        "",
        "**Legend:** ✅ exercised (dispatched green / B6 seed) · ▫️ N/A (class "
        "unreachable in mode, recorded reason) · — not applicable.",
        "",
        "Every N/A cell carries the `ModeReachError` reason in the harness output "
        "(`engine.coverage.run_coverage_matrix`). The matrix is regenerated, not "
        "transcribed: `python -m valor_build.coverage`.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        cells = run_coverage_matrix(tmp)
        s = summarize(cells)
        print("C1 Engine coverage matrix — PS-PE-HIGH — BUILD / gates log-only")
        print(f"  cells={s['total_cells']}  exercised={s['exercised']}  "
              f"n/a={s['na']}  failed={len(s['failed'])}  actions={s['action_count']}/27")
        for c in s["failed"]:
            print(f"  FAILED: {c.action_type} @ {c.mode} -> {c.note}")
        return 0 if not s["failed"] and s["total_cells"] == 96 else 1


if __name__ == "__main__":
    raise SystemExit(main())
