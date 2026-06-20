"""B5 project container — the M4 projection milestone (G-18, additive on B6).

Drives the B5 vertical: run the proven B6 slice for **≥2 PE-HIGH work packages**
(each its own M3 truth path), then compose them into an **M4 Project container** and
emit one consolidated, projection-only status report over the ``SELECTED_WP_SET``::

    [M3] WP-A: create→…→export        (own truth)
    [M3] WP-B: create→…→export        (own truth)
    [M4] project: RPT_GENERATE_STATUS_REPORT over {WP-A, WP-B}   (projection only)

The M4 step runs in **M4** (runtime) · **BUILD** (lifecycle) · **EXECUTION**
(engine-authority), with **no gate** (``gate=None``) and **no confirmation**
(``RPT_GENERATE_STATUS_REPORT`` is ``confirm: false``): D-13's sole control is the
**scope-bound**, enforced in ``ProjectContainer.compose`` before dispatch. The whole
run shares one audit channel (A16 §4 / A18 §3).

Run it directly::

    python -m valor_build.project_skeleton

Exit criterion (Phase-B plan B5): an M4 projection composes ≥2 PE-HIGH WPs read-only,
no truth gates, scope-bound enforced.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .engine.audit import AuditLog
from .engine.dispatch import Dispatcher, DispatchResult, StepRequest
from .engine.gates import Lifecycle
from .engine.project import ProjectContainer
from .engine.registry import ContractRegistry
from .engine.schemas import SchemaRegistry
from .engine.store import WPStore
from .modes.runtime import RuntimeMode
from .skeleton import SkeletonResult, auto_yes, run_walking_skeleton

DEFAULT_WP_IDS = ("WP-PEH-A1", "WP-PEH-B2")


@dataclass
class ProjectResult:
    project_id: str
    wp_ids: tuple[str, ...]
    member_runs: list[SkeletonResult]   # each member WP's own M3 slice result
    projection: DispatchResult          # the M4 consolidated status-report dispatch
    audit: AuditLog
    store: WPStore

    @property
    def members_ok(self) -> bool:
        return all(r.all_ok for r in self.member_runs)

    @property
    def all_ok(self) -> bool:
        return self.members_ok and self.projection.ok


def run_project_container(
    store_root: Path | str,
    wp_ids=DEFAULT_WP_IDS,
    *,
    project_id: str = "PRJ-PEH-001",
    lifecycle: Lifecycle = Lifecycle.BUILD,
    confirm_provider: Callable[[str], bool] = auto_yes,
    pack_root: Path | None = None,
) -> ProjectResult:
    wp_ids = tuple(wp_ids)
    audit = AuditLog()  # single channel across both M3 slices + the M4 projection

    # 1. Each member WP runs its own M3 truth path (the B6 slice) into a shared store.
    member_runs: list[SkeletonResult] = []
    for wp_id in wp_ids:
        member_runs.append(
            run_walking_skeleton(
                store_root,
                wp_id=wp_id,
                lifecycle=lifecycle,
                confirm_provider=confirm_provider,
                pack_root=pack_root,
                audit=audit,
            )
        )

    # 2. Compose the M4 container — scope-bound (R3) enforced here, before any dispatch.
    store = WPStore(Path(store_root))
    container = ProjectContainer.compose(project_id, wp_ids, store)

    # 3. Dispatch the consolidated projection in M4. No gate (D-13: sole control is the
    #    scope-bound); no confirm (RPT_GENERATE_STATUS_REPORT is confirm:false).
    registry = ContractRegistry(pack_root)
    schemas = SchemaRegistry(pack_root)
    dispatcher = Dispatcher(registry, schemas, audit, confirm_provider)
    req = StepRequest(
        action="RPT_GENERATE_STATUS_REPORT",
        payload={
            "artifact_type": "WORK_PACKAGE_STATUS_REPORT",
            "target_scope": "SELECTED_WP_SET",
            "wp_ids": list(wp_ids),
            "source_snapshot_refs": [{"wp_id": w} for w in wp_ids],
            "stamps": {"testing_only": True},
            "validation_mode": "STRICT",
        },
        target={"project_id": project_id, "wp_ids": list(wp_ids)},
        runtime_mode=RuntimeMode.M4,
        lifecycle=lifecycle,
        engine_mode="EXECUTION",
        actor_role="CQV",
        state="ARTIFACT",
        gate=None,  # D-13: M4 container has no truth gates; scope-bound is the control.
        provenance={"project_id": project_id, "member_count": container.member_count},
    )
    projection = dispatcher.dispatch(req, container.build_status_report)

    return ProjectResult(project_id, wp_ids, member_runs, projection, audit, store)


def main() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        result = run_project_container(tmp)
        print(f"Project container — {result.project_id} — M4 / BUILD / EXECUTION")
        for run in result.member_runs:
            mark = "ok" if run.all_ok else "REFUSED"
            print(f"  [M3 {mark:7s}] {run.wp_id:12s} — {len(run.steps)} steps, all_ok={run.all_ok}")
        proj = result.projection
        meta = (proj.result or {}).get("artifact_metadata", {})
        mark = "ok" if proj.ok else "REFUSED"
        print(
            f"  [M4 {mark:7s}] consolidated status report over "
            f"{meta.get('wp_ids')} — projection_only={meta.get('projection_only')}, "
            f"mutates_wp_truth={meta.get('mutates_wp_truth')}"
        )
        gate_records = result.audit.of_kind("gate_outcome")
        # Gates only fired inside the per-WP M3 slices; the M4 projection adds none.
        print(
            f"\nall_ok = {result.all_ok}\n"
            f"audit records: {len(result.audit.records)} "
            f"(gates={len(gate_records)} [all from M3 members], "
            f"stamps={len(result.audit.of_kind('output_stamp'))}, "
            f"ai_calls={len(result.audit.of_kind('ai_call'))})"
        )
        return 0 if result.all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
