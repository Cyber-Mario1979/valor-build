"""B6 walking skeleton — the first runnable milestone (G-04).

Drives the full thin vertical slice end-to-end against PE-HIGH::

    create -> stage -> commit -> plan -> apply -> draft -> finalize -> export

running in **M3** (runtime) · **BUILD** (lifecycle, gates log-only per A17) ·
**EXECUTION** (engine-authority). The human-confirmation gate is live on every
``confirm:true`` step (A17 §4) — here driven by an auto-accept provider so the slice
runs unattended, while still exercising and auditing the gate.

Run it directly::

    python -m valor_build.skeleton

Exit criterion (Phase-B plan B6): a thin vertical slice runs the full contract path
against PE-HIGH, gates logging only.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .ai.interface import LLMInterface
from .engine.audit import AuditLog
from .engine.dispatch import Dispatcher, StepRequest
from .engine.domain import PEHighDomain
from .engine.gates import GATE_APPLY, GATE_COMMIT, GATE_EXPORT, GATE_PLAN, GATE_STAGE, Lifecycle
from .engine.handlers import Handlers
from .engine.registry import ContractRegistry
from .engine.schemas import SchemaRegistry
from .engine.store import WPStore
from .modes.runtime import RuntimeMode


def auto_yes(_message: str) -> bool:
    """Default confirmation provider for unattended runs (still audited)."""
    return True


@dataclass
class SkeletonResult:
    wp_id: str
    steps: list[dict]            # per-step: action, ok, state, gate_verdict
    audit: AuditLog
    store: WPStore

    @property
    def all_ok(self) -> bool:
        return all(s["ok"] for s in self.steps)


def run_walking_skeleton(
    store_root: Path | str,
    *,
    wp_id: str = "WP-PEH-001",
    lifecycle: Lifecycle = Lifecycle.BUILD,
    confirm_provider: Callable[[str], bool] = auto_yes,
    audit_path: Path | None = None,
    pack_root: Path | None = None,
) -> SkeletonResult:
    registry = ContractRegistry(pack_root)
    schemas = SchemaRegistry(pack_root)
    audit = AuditLog(audit_path)
    store = WPStore(Path(store_root))
    domain = PEHighDomain.load(pack_root)
    ai = LLMInterface(schemas, audit)
    handlers = Handlers(wp_id, store, domain, ai)
    dispatcher = Dispatcher(registry, schemas, audit, confirm_provider)

    target = {"wp_id": wp_id}
    common = dict(
        payload={}, target=target, runtime_mode=RuntimeMode.M3,
        lifecycle=lifecycle, engine_mode="EXECUTION", actor_role="CQV",
    )

    # (action, handler, gate, resulting-state-stamp)
    plan = [
        ("WP_CREATE", handlers.create_wp, None, "WP_DRAFT"),
        ("WP_STAGE_TASKS", handlers.stage_tasks, GATE_STAGE, "STAGED"),
        ("WP_COMMIT_STAGED_TASKS", handlers.commit_staged_tasks, GATE_COMMIT, "WP_COMMITTED"),
        ("PLAN_GENERATE_PROPOSAL", handlers.generate_plan_proposal, GATE_PLAN, "PROPOSED"),
        ("WP_APPLY_PLAN_PROPOSAL", handlers.apply_plan_proposal, GATE_APPLY, "WP_COMMITTED"),
        ("DOC_GENERATE_DRAFT", handlers.generate_doc_draft, None, "DRAFT"),
        ("DOC_FINALIZE_ARTIFACT", handlers.finalize_doc_artifact, None, "FINAL"),
        ("RPT_GENERATE_WORKBOOK_EXPORT", handlers.export_workbook, GATE_EXPORT, "ARTIFACT"),
    ]

    steps: list[dict] = []
    for action, handler, gate, state in plan:
        req = StepRequest(action=action, state=state, gate=gate, entry_condition_met=True, **common)
        result = dispatcher.dispatch(req, handler)
        steps.append({
            "action": action,
            "ok": result.ok,
            "state": state,
            "gate": gate,
            "gate_verdict": result.verdict.verdict if result.verdict else None,
        })
        if not result.ok:  # a refusal halts the slice (e.g. confirmation No)
            break

    return SkeletonResult(wp_id, steps, audit, store)


def main() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        result = run_walking_skeleton(tmp)
        print(f"Walking skeleton — WP {result.wp_id} — BUILD / M3 / EXECUTION")
        for step in result.steps:
            gate = step["gate"] or "(no gate)"
            verdict = step["gate_verdict"] or "-"
            mark = "ok" if step["ok"] else "REFUSED"
            print(f"  [{mark:7s}] {step['action']:30s} -> {step['state']:14s} {gate:12s} {verdict}")
        print(f"\nall_ok = {result.all_ok}")
        print(f"audit records: {len(result.audit.records)} "
              f"(gates={len(result.audit.of_kind('gate_outcome'))}, "
              f"confirms={len(result.audit.of_kind('confirmation'))}, "
              f"ai_calls={len(result.audit.of_kind('ai_call'))}, "
              f"stamps={len(result.audit.of_kind('output_stamp'))})")
        return 0 if result.all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
