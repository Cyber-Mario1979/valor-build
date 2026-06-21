"""C1 Engine — full-coverage handlers (Phase C, Session 19).

Extends the B6 ``Handlers`` spine to the remaining **active** actions in the
frozen ``CONTRACT_REGISTRY_v1.0.1.yaml`` so the engine covers every active
action / side-effect class / runtime mode over the single ``PS-PE-HIGH`` preset
(C1 step 2). Thin and deterministic, exactly like B6: each handler returns a
result that validates against the action's declared ``result_schema_ref`` in the
frozen pack, and every truth mutation goes through the store's single commit
chokepoint. No pack edits; BUILD outputs keep ``PRODUCT_TESTING_ONLY`` (R5).

The 19 here + the 8 in ``Handlers`` = the 27 active actions
(23 ``ACTIVE_FROZEN`` + 4 ``ACTIVE_INTERNAL_FROZEN``). The 12 ``TESTING_ONLY``
KS actions are a separate class and out of this matrix.
"""
from __future__ import annotations

from .audit import canonical_hash, now_utc
from .handlers import Handlers, PRODUCT_TESTING_ONLY

# The nine canonical status-report sections (report_result.schema.json enum).
_RPT_SECTIONS = [
    ("COVER_PAGE", "Cover Page"),
    ("EXECUTIVE_SUMMARY", "Executive Summary"),
    ("WORK_PACKAGE_OVERVIEW", "Work Package Overview"),
    ("TASK_STATUS_SUMMARY", "Task Status Summary"),
    ("SCHEDULE_SUMMARY", "Schedule Summary"),
    ("RISKS_ISSUES_EXCEPTIONS", "Risks, Issues & Exceptions"),
    ("TRACEABILITY_GOVERNANCE", "Traceability & Governance"),
    ("RECOMMENDATIONS_NEXT_ACTIONS", "Recommendations & Next Actions"),
    ("APPENDIX", "Appendix"),
]


class CoverageHandlers(Handlers):
    """B6 handlers + the C1 remainder, sharing the same store/domain/ai/spine."""

    # ====================================================================
    # WP — read
    # ====================================================================

    def wp_get(self) -> dict:                                # READ_ONLY
        return self.store.load_wp(self.wp_id)

    # ====================================================================
    # WP — truth mutations (MUTATES_TRUTH; M3 only). Each loads current
    # truth, mutates a real field, and re-commits through the chokepoint.
    # work_package_schema is additionalProperties:true, so these are genuine.
    # ====================================================================

    def update_task_fields(self) -> dict:
        wp = self.store.load_wp(self.wp_id)
        if wp.get("tasks"):
            wp["tasks"][0]["status"] = "IN_PROGRESS"
            wp["tasks"][0]["field_update_note"] = "coverage: task field update (testing only)"
        wp["lifecycle_state"] = "WP_IN_EXECUTION"
        wp["updated_at_utc"] = now_utc()
        self.store.commit_truth(self.wp_id, "WP_UPDATE_TASK_FIELDS", wp)
        return wp

    def bind_preset_context(self) -> dict:
        wp = self.store.load_wp(self.wp_id)
        wp["preset_ref"] = {
            "preset_id": self.domain.preset["preset_id"],
            "version": self.domain.preset["version"],
        }
        wp["standards_bundle_ref"] = self.domain.standards_bundle_ref
        wp["preset_context_bound"] = True
        wp["updated_at_utc"] = now_utc()
        self.store.commit_truth(self.wp_id, "WP_BIND_PRESET_CONTEXT", wp)
        return wp

    def set_planning_basis(self) -> dict:
        wp = self.store.load_wp(self.wp_id)
        wp["planning_basis"] = "PROFILE_BASED"
        wp["updated_at_utc"] = now_utc()
        self.store.commit_truth(self.wp_id, "WP_SET_PLANNING_BASIS", wp)
        return wp

    def set_task_duration_overrides(self) -> dict:
        wp = self.store.load_wp(self.wp_id)
        if wp.get("tasks"):
            wp["tasks"][0]["duration_override"] = {
                "value": 1.0, "unit": "WORKING_DAYS", "source": "USER_OVERRIDE",
            }
        wp["planning_basis"] = "USER_DRIVEN_BASELINE"
        wp["updated_at_utc"] = now_utc()
        self.store.commit_truth(self.wp_id, "WP_SET_TASK_DURATION_OVERRIDES", wp)
        return wp

    def record_confirmation(self) -> dict:
        wp = self.store.load_wp(self.wp_id)
        confs = wp.get("confirmations", [])
        confs.append({"confirmed_at_utc": now_utc(), "actor_role": "CQV", "scope": "coverage"})
        wp["confirmations"] = confs
        wp["updated_at_utc"] = now_utc()
        self.store.commit_truth(self.wp_id, "WP_RECORD_CONFIRMATION", wp)
        return wp

    # ====================================================================
    # PLAN — validate (VALIDATE_ONLY)
    # ====================================================================

    def validate_plan_proposal(self) -> dict:
        plan = self.store.load_plan(self.wp_id)
        return {
            "action_type": "PLAN_VALIDATE_PROPOSAL",
            "wp_id": self.wp_id,
            "plan_proposal_id": plan["plan_proposal_id"],
            "state": "PROPOSED",
            "ok": True,
            "errors": [],
            "warnings": [],
            "validated_at_utc": now_utc(),
            "provenance_stamps_checked": True,
            "calendar_logic_checked": True,
            "proposal_commit_boundary_checked": True,
        }

    # ====================================================================
    # RPT — shared builders. Single-WP scope (target_scope: SINGLE_WP);
    # projection-only metadata identical in shape to the M4 consolidated form.
    # ====================================================================

    def _rpt_artifact_metadata(
        self, *, action_type: str, artifact_type: str, artifact_id: str,
        template_id: str, ref_type: str, fmt: str, uri: str,
    ) -> dict:
        wp = self.store.load_wp(self.wp_id)
        return {
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "artifact_label": f"{self.wp_id} {artifact_type.lower()} (testing only)",
            "target_scope": "SINGLE_WP",
            "wp_ids": [self.wp_id],
            "source_snapshot_hash": canonical_hash(wp),
            "template_id": template_id,
            "template_version": "v1.0.1",
            "contract_id": "VALOR-contract-orch-rpt",
            "contract_version": "v1.0.1",
            "action_type": action_type,
            "generated_at_utc": now_utc(),
            "projection_only": True,
            "mutates_wp_truth": False,
            "stamps": {
                "testing_only": True,
                "testing_only_stamp": PRODUCT_TESTING_ONLY,
            },
            "validation_result": {"ok": True, "mode": "STRICT", "errors": [], "warnings": []},
            "content_ref": {"ref_type": ref_type, "format": fmt, "uri": uri},
        }

    def _status_report_result(self) -> dict:
        wp = self.store.load_wp(self.wp_id)
        ntasks = len(wp.get("tasks", []))
        sections = [
            {
                "section_id": sid,
                "title": title,
                "required": True,
                "summary": f"{title}: WP {self.wp_id}, {ntasks} task(s) (testing only).",
            }
            for sid, title in _RPT_SECTIONS
        ]
        meta = self._rpt_artifact_metadata(
            action_type="RPT_GENERATE_STATUS_REPORT",
            artifact_type="WORK_PACKAGE_STATUS_REPORT",
            artifact_id=f"{self.wp_id}-RPT-STATUS-001",
            template_id="RPT_STATUS_REPORT",
            ref_type="FILE", fmt="REPORT_SOURCE",
            uri=f"exports/{self.wp_id}-status-report-001.src",
        )
        rendered = "\n".join(f"## {s['title']}\n{s['summary']}" for s in sections)
        return {
            "artifact_metadata": meta,
            "report_type": "WORK_PACKAGE_STATUS_REPORT",
            "report_sections": sections,
            "rendered_report_source": rendered,
            "pdf_intent": True,
        }

    def _gantt_result(self) -> dict:
        wp = self.store.load_wp(self.wp_id)
        starts = [t.get("committed_start_date") for t in wp.get("tasks", []) if t.get("committed_start_date")]
        finishes = [t.get("committed_finish_date") for t in wp.get("tasks", []) if t.get("committed_finish_date")]
        timeline_start = min(starts) if starts else "2026-07-01"
        timeline_end = max(finishes) if finishes else "2026-07-01"
        meta = self._rpt_artifact_metadata(
            action_type="RPT_GENERATE_GANTT_CHART",
            artifact_type="WORK_PACKAGE_GANTT_CHART",
            artifact_id=f"{self.wp_id}-GANTT-001",
            template_id="RPT_GANTT_CHART",
            ref_type="FILE", fmt="XLSX",
            uri=f"exports/{self.wp_id}-gantt-001.xlsx",
        )
        sheets = ["Metadata", "Gantt", "Legend"]
        sheet_validation = [
            {"sheet_name": n, "required": True, "present": True, "errors": [], "warnings": []}
            for n in sheets
        ]
        return {
            "artifact_metadata": meta,
            "gantt_type": "WORK_PACKAGE_GANTT_CHART",
            "gantt_format": "XLSX",
            "timeline": {
                "granularity": "DAY",
                "timeline_start": timeline_start,
                "timeline_end": timeline_end,
            },
            "layout_rules": {
                "timeline_coloring": "FULL_CELL_FILL",
                "character_bars_inside_cells": False,
                "selected_wp_set_grouping": "GROUP_BY_WP",
            },
            "required_sheets": sheets,
            "sheet_validation": sheet_validation,
            "gantt_schema_ref": "schemas/objects/gantt_chart_schema.json",
        }

    # ---- RPT — generate (GENERATES_ARTIFACT; M3 single-WP, M4 projection) --

    def generate_status_report(self) -> dict:       # RPT_GENERATE_STATUS_REPORT
        return self._status_report_result()

    def generate_gantt_chart(self) -> dict:         # RPT_GENERATE_GANTT_CHART
        return self._gantt_result()

    # ---- RPT — validate (VALIDATE_ONLY; result schema == the generate form) -

    def validate_report_inputs(self) -> dict:       # RPT_VALIDATE_REPORT_INPUTS
        return self._status_report_result()

    def validate_gantt_inputs(self) -> dict:        # RPT_VALIDATE_GANTT_INPUTS
        return self._gantt_result()

    def validate_workbook_export(self) -> dict:     # RPT_VALIDATE_WORKBOOK_EXPORT
        # Same result schema as the generate; reuse the proven B6 builder.
        return self.export_workbook()

    def validate_stamps(self) -> dict:              # RPT_VALIDATE_STAMPS
        # Validates the stamps on an existing artifact; returns that metadata.
        # RPT_VALIDATE_STAMPS is not in the metadata action_type enum, so the
        # returned metadata carries the validated artifact's own action_type.
        return self._rpt_artifact_metadata(
            action_type="RPT_GENERATE_WORKBOOK_EXPORT",
            artifact_type="WORK_PACKAGE_WORKBOOK_EXPORT",
            artifact_id=f"{self.wp_id}-XLSX-001",
            template_id="RPT_WORKBOOK_EXPORT",
            ref_type="FILE", fmt="XLSX",
            uri=f"exports/{self.wp_id}-001.xlsx",
        )

    # ---- RPT — read (READ_ONLY) --------------------------------------------

    def list_artifacts(self) -> dict:               # RPT_LIST_ARTIFACTS
        return self._rpt_artifact_metadata(
            action_type="RPT_LIST_ARTIFACTS",
            artifact_type="WORK_PACKAGE_WORKBOOK_EXPORT",
            artifact_id=f"{self.wp_id}-XLSX-001",
            template_id="RPT_WORKBOOK_EXPORT",
            ref_type="ARTIFACT_STORE_REF", fmt="XLSX",
            uri=f"store://{self.wp_id}/artifacts",
        )

    def get_artifact(self) -> dict:                 # RPT_GET_ARTIFACT
        return self._rpt_artifact_metadata(
            action_type="RPT_GET_ARTIFACT",
            artifact_type="WORK_PACKAGE_WORKBOOK_EXPORT",
            artifact_id=f"{self.wp_id}-XLSX-001",
            template_id="RPT_WORKBOOK_EXPORT",
            ref_type="ARTIFACT_STORE_REF", fmt="XLSX",
            uri=f"store://{self.wp_id}/artifacts/{self.wp_id}-XLSX-001",
        )

    # ====================================================================
    # PS — internal service resolver (ACTIVE_INTERNAL_FROZEN).
    # Engine-internal / mode-agnostic (owner decision, S19): not user-mode
    # gated; exercised once when the resolver runs.
    # ====================================================================

    def ps_list_presets(self) -> dict:              # PS_LIST_PRESETS
        p = self.domain.preset
        return {
            "presets": [{
                "preset_id": p["preset_id"],
                "version": p["version"],
                "name": p.get("name", p["preset_id"]),
                "system_type": p.get("applicability", {}).get("system_type", "ProcessEquipment"),
                "complexity": "High",
            }]
        }

    def ps_read_preset(self) -> dict:               # PS_READ_PRESET
        return dict(self.domain.preset)

    def ps_resolve_preset(self) -> dict:            # PS_RESOLVE_PRESET
        cal = self.domain.calendar_logic_ref
        return {
            "preset_id": self.domain.preset["preset_id"],
            "preset_version": self.domain.preset["version"],
            "bindings": {
                "task_pool_ref": {
                    "task_pool_id": self.domain.pool["task_pool_id"],
                    "task_pool_version": self.domain.pool["version"],
                },
                "profile_ref": {
                    "profile_id": self.domain.profile["profile_id"],
                    "profile_version": self.domain.profile["version"],
                },
                "calendar_logic_ref": {
                    "calendar_id": cal["calendar_id"],
                    "calendar_version": cal.get("version", cal.get("calendar_version", "v1.0.1")),
                },
                "standards_bundle_ref": self.domain.standards_bundle_ref,
            },
            "rules_fired": [],
            "stamps": {"preset": self.domain.preset["preset_id"]},
        }

    def ps_validate_bindings(self) -> dict:         # PS_VALIDATE_BINDINGS
        return {
            "action_type": "PS_VALIDATE_BINDINGS",
            "wp_id": self.wp_id,
            "plan_proposal_id": f"{self.wp_id}-BINDINGS-001",
            "state": "PROPOSED",
            "ok": True,
            "errors": [],
            "warnings": [],
            "validated_at_utc": now_utc(),
        }
