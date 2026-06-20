"""M4 Project container — projection over a ``SELECTED_WP_SET`` (B5; G-18, D-10/D-11/D-13).

The Project container is the **M4** surface (A18 §2). It composes single-entity WPs
**by context** into one project view and produces consolidated projection artifacts
over the set. It is the *Delivery-Plan* mode surface (G-17 label discipline) — kept
distinct from M3 *WP-tasks planning* and from a *CQV plan* document.

**It owns no truth (D-10/D-11/D-13).** Each member WP runs its own M3 path (the B6
slice) for *its* truth; the container only references the committed snapshots M3 wrote.
There are **no truth-mutation gates** on the container; its **sole control is the
scope-bound** (R3): the selected set must be explicit and bounded — ``ALL_WPS`` is
refused (out of freeze scope per the RPT contract's ``target_scope_policy``), as are
empty sets and members that have no committed snapshot.

Grounded against the frozen pack at ``0ec3060``:
  * RPT contract ``VALOR-contract-orch-rpt`` — ``projection_policy.mutates_wp_truth: false``;
    ``target_scope_policy.supported: [SINGLE_WP, SELECTED_WP_SET]``,
    ``excluded_from_freeze_scope: [ALL_WPS]``.
  * ``RPT_GENERATE_STATUS_REPORT`` — ``GENERATES_ARTIFACT``, ``confirm: false``,
    result schema ``report_result.schema.json`` (9 canonical sections; artifact
    metadata with ``target_scope`` / ``wp_ids`` / ``projection_only: true`` /
    ``mutates_wp_truth: false``).

The consolidated report is a **deterministic projection** of committed truth — no AI
call is involved (the narrative AI step belongs to per-WP DOC generation in M3).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .audit import canonical_hash, now_utc
from .store import WPStore

PRODUCT_TESTING_ONLY = "PRODUCT TESTING ONLY — NOT APPROVED FOR REAL-LIFE REGULATED CQV/GMP USE."

# Scope vocabulary (pack RPT ``target_scope_policy``).
TARGET_SCOPE = "SELECTED_WP_SET"
ALL_WPS = "ALL_WPS"  # the sentinel that is out of freeze scope and must be refused (R3)

CONTRACT_ID = "VALOR-contract-orch-rpt"
CONTRACT_VERSION = "v1.0.1"
STATUS_REPORT_ACTION = "RPT_GENERATE_STATUS_REPORT"
COMMITTED_STATE = "WP_COMMITTED"

# The nine canonical status-report sections (report_result.schema.json enum, minItems 9).
_CANONICAL_SECTIONS = (
    ("COVER_PAGE", "Cover Page", True),
    ("EXECUTIVE_SUMMARY", "Executive Summary", True),
    ("WORK_PACKAGE_OVERVIEW", "Work Package Overview", True),
    ("TASK_STATUS_SUMMARY", "Task Status Summary", True),
    ("SCHEDULE_SUMMARY", "Schedule Summary", True),
    ("RISKS_ISSUES_EXCEPTIONS", "Risks, Issues & Exceptions", True),
    ("TRACEABILITY_GOVERNANCE", "Traceability & Governance", True),
    ("RECOMMENDATIONS_NEXT_ACTIONS", "Recommendations & Next Actions", True),
    ("APPENDIX", "Appendix", False),
)


class ScopeBoundError(RuntimeError):
    """Raised when the selected WP set violates the M4 scope-bound (R3, D-13).

    The container's sole control: the set must be an explicit, bounded list of
    committed WPs. ``ALL_WPS``, empty sets, and uncommitted/unknown members are refused.
    """


@dataclass(frozen=True)
class ProjectContainer:
    """An M4 projection composing an explicit ``SELECTED_WP_SET``. Owns no truth."""

    project_id: str
    selected_wp_ids: tuple[str, ...]
    members: dict[str, dict] = field(default_factory=dict)  # wp_id -> committed snapshot

    # -- composition (scope-bound enforced here) ----------------------------

    @classmethod
    def compose(cls, project_id: str, selected, store: WPStore) -> "ProjectContainer":
        """Compose a project over ``selected`` WPs, enforcing the scope-bound (R3).

        Refuses ``ALL_WPS``, empty/non-list selections, and any member without a
        committed snapshot. Reads each member's committed snapshot **read-only** — no
        truth is written. The container never corrects, overwrites, infers, or mutates
        WP truth (D-11).
        """
        # R3 — explicit, bounded set only. ALL_WPS is out of freeze scope.
        if isinstance(selected, str):
            # A bare string (e.g. the ALL_WPS sentinel) is never an explicit set.
            raise ScopeBoundError(
                f"target scope must be an explicit selected WP set, not {selected!r} "
                f"({ALL_WPS} is out of freeze scope, R3)"
            )
        if selected is None:
            raise ScopeBoundError("no selected WP set provided (scope-bound required, R3)")
        selected_list = list(selected)
        if ALL_WPS in selected_list:
            raise ScopeBoundError(f"{ALL_WPS} is out of freeze scope and is refused (R3)")
        if not selected_list:
            raise ScopeBoundError("selected WP set is empty (scope-bound requires ≥1 WP, R3)")
        if len(set(selected_list)) != len(selected_list):
            raise ScopeBoundError(f"selected WP set has duplicates: {selected_list}")

        members: dict[str, dict] = {}
        for wp_id in selected_list:
            if not isinstance(wp_id, str) or not wp_id:
                raise ScopeBoundError(f"invalid WP id in selected set: {wp_id!r}")
            if store.is_tombstoned(wp_id):
                raise ScopeBoundError(f"selected WP is tombstoned, cannot project: {wp_id}")
            snapshot = store.load_wp(wp_id)
            if snapshot is None:
                raise ScopeBoundError(
                    f"selected WP has no committed snapshot, cannot project: {wp_id} "
                    "(each member must run its own M3 truth path first)"
                )
            if snapshot.get("lifecycle_state") != COMMITTED_STATE:
                raise ScopeBoundError(
                    f"selected WP is not committed ({snapshot.get('lifecycle_state')!r}): {wp_id}"
                )
            members[wp_id] = snapshot

        return cls(project_id, tuple(selected_list), members)

    # -- projection ---------------------------------------------------------

    @property
    def member_count(self) -> int:
        return len(self.selected_wp_ids)

    def consolidated_snapshot_hash(self) -> str:
        """One hash over the ordered member snapshots — the projection's source hash."""
        ordered = [self.members[wp_id] for wp_id in self.selected_wp_ids]
        return canonical_hash({"project_id": self.project_id, "members": ordered})

    def _section_summaries(self) -> dict[str, str]:
        """Deterministic per-section summaries derived from committed truth (projection)."""
        total_tasks = sum(len(m.get("tasks", [])) for m in self.members.values())
        wp_list = ", ".join(self.selected_wp_ids)
        scheduled = sum(
            1
            for m in self.members.values()
            for t in m.get("tasks", [])
            if t.get("committed_start_date") and t.get("committed_finish_date")
        )
        return {
            "COVER_PAGE": f"Project {self.project_id} — {self.member_count} work packages (testing only).",
            "EXECUTIVE_SUMMARY": (
                f"Consolidated status across {self.member_count} committed PE-HIGH work "
                f"packages ({wp_list}); {total_tasks} task(s) total."
            ),
            "WORK_PACKAGE_OVERVIEW": f"Member work packages: {wp_list}.",
            "TASK_STATUS_SUMMARY": f"{total_tasks} committed task(s) across the selected set.",
            "SCHEDULE_SUMMARY": f"{scheduled}/{total_tasks} task(s) carry committed schedule dates.",
            "RISKS_ISSUES_EXCEPTIONS": "No exceptions raised in this projection (skeleton scope).",
            "TRACEABILITY_GOVERNANCE": (
                "Projection-only: container owns no truth; each WP's gates ran in its own M3 path."
            ),
            "RECOMMENDATIONS_NEXT_ACTIONS": "None — projection composes committed snapshots read-only.",
            "APPENDIX": f"Source snapshot hash: {self.consolidated_snapshot_hash()}.",
        }

    def build_status_report(self) -> dict:
        """Build the consolidated ``RPT_GENERATE_STATUS_REPORT`` result over the set.

        Returns a ``report_result``-shaped object (validated by the dispatch spine
        against ``report_result.schema.json``). Projection-only: ``projection_only:
        true`` / ``mutates_wp_truth: false`` on the artifact metadata.
        """
        summaries = self._section_summaries()
        report_sections = [
            {
                "section_id": sid,
                "title": title,
                "required": required,
                "summary": summaries[sid],
            }
            for (sid, title, required) in _CANONICAL_SECTIONS
        ]
        artifact_metadata = {
            "artifact_id": f"{self.project_id}-RPT-STATUS-001",
            "artifact_type": "WORK_PACKAGE_STATUS_REPORT",
            "artifact_label": f"{self.project_id} consolidated status report (testing only)",
            "target_scope": TARGET_SCOPE,
            "wp_ids": list(self.selected_wp_ids),
            "source_snapshot_hash": self.consolidated_snapshot_hash(),
            "template_id": "RPT_STATUS_REPORT",
            "template_version": CONTRACT_VERSION,
            "contract_id": CONTRACT_ID,
            "contract_version": CONTRACT_VERSION,
            "action_type": STATUS_REPORT_ACTION,
            "generated_at_utc": now_utc(),
            "projection_only": True,
            "mutates_wp_truth": False,
            "stamps": {
                "testing_only": True,
                "testing_only_stamp": PRODUCT_TESTING_ONLY,
                "project_id": self.project_id,
                "member_count": self.member_count,
                "runtime_mode": "M4",
            },
            "validation_result": {"ok": True, "mode": "STRICT", "errors": [], "warnings": []},
            "content_ref": {
                "ref_type": "FILE",
                "format": "REPORT_SOURCE",
                "uri": f"exports/{self.project_id}-status-report-001.src",
            },
        }
        rendered = "\n".join(
            f"## {title}\n{summaries[sid]}" for (sid, title, _required) in _CANONICAL_SECTIONS
        )
        return {
            "artifact_metadata": artifact_metadata,
            "report_type": "WORK_PACKAGE_STATUS_REPORT",
            "report_sections": report_sections,
            "rendered_report_source": rendered,
            "pdf_intent": True,
        }
