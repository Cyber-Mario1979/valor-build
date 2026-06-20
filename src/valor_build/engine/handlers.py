"""Path handlers for the B6 walking skeleton (thin, deterministic, schema-valid).

One handler per action in the slice ``create -> stage -> commit -> plan -> apply ->
draft -> finalize -> export``. Each returns a result object that validates against
the action's declared ``result_schema_ref`` in the frozen pack. Truth mutations go
through the store's single commit chokepoint; the doc draft is produced through the
D-08 AI interface (the one narrative step). Everything else is deterministic.

These are intentionally **thin**: the walking skeleton proves the contract path runs
end-to-end against PE-HIGH, not that every field is production-rich.
"""
from __future__ import annotations

from datetime import date

from .audit import canonical_hash, now_utc
from .domain import PEHighDomain, add_working_days, next_working_day
from .store import WPStore
from ..ai.interface import LLMInterface, PromptAsset

PRODUCT_TESTING_ONLY = "PRODUCT TESTING ONLY — NOT APPROVED FOR REAL-LIFE REGULATED CQV/GMP USE."

# Versioned, hashed prompt asset for the doc-draft narrative step (D-08).
DOC_DRAFT_PROMPT = PromptAsset(
    version="doc_draft.vmp.v1",
    template=(
        "Draft a {doc_type} for work package {wp_id} from the committed task set. "
        "Cite only the bound testing-only standards bundle. Output schema-constrained JSON."
    ),
)

_OK_VALIDATION = {"ok": True, "errors": [], "warnings": []}


class Handlers:
    def __init__(self, wp_id: str, store: WPStore, domain: PEHighDomain, ai: LLMInterface):
        self.wp_id = wp_id
        self.store = store
        self.domain = domain
        self.ai = ai
        self._staged_task_ids: list[str] = []

    # -- 1. WP_CREATE (MUTATES_TRUTH) --------------------------------------

    def create_wp(self) -> dict:
        self.store.allocate_id(self.wp_id)
        wp = {
            "wp_id": self.wp_id,
            "title": "PE-HIGH Process Equipment Program (walking skeleton)",
            "scope": "Single high-complexity process-equipment qualification slice",
            "wp_type": "ProcessEquipment",
            "complexity": "High",
            "lifecycle_state": "WP_DRAFT",
            "owner_function": "CQV",
            "created_at_utc": now_utc(),
            "preset_ref": {"preset_id": self.domain.preset["preset_id"], "version": self.domain.preset["version"]},
            "standards_bundle_ref": self.domain.standards_bundle_ref,
            "tasks": [],
            "provenance_refs": {"preset": self.domain.preset["preset_id"]},
            "testing_only": True,
            "usage_classification": "PRODUCT_TESTING_ONLY",
        }
        self.store.commit_truth(self.wp_id, "WP_CREATE", wp)
        return wp

    # -- 2. WP_STAGE_TASKS (STAGE_ONLY) ------------------------------------

    def stage_tasks(self) -> dict:
        # Thin slice: stage the single root task (no predecessors) from TP-PE-HIGH.
        atomic = self.domain.task("PEH-VMP-CYCLE")
        staged_task_id = f"{self.wp_id}-T001"
        self._staged_task_ids = [staged_task_id]
        staged_task = {
            "task_id": staged_task_id,
            "wp_id": self.wp_id,
            "name": atomic["name"],
            "task_type": atomic["task_type"],
            "phase": atomic["phase"],
            "status": "STAGED",
            "dependencies": [],
            "duration_ref": dict(atomic["duration_ref"]),
        }
        result = {
            "action_type": "WP_STAGE_TASKS",
            "wp_id": self.wp_id,
            "staged_task_set_id": f"{self.wp_id}-STG-001",
            "state": "STAGED",
            "tasks": [staged_task],
            "preset_ref": {"preset_id": self.domain.preset["preset_id"], "version": self.domain.preset["version"]},
            "source_task_pool_ref": {"task_pool_id": self.domain.pool["task_pool_id"], "version": self.domain.pool["version"]},
            "provenance_stamps": {"preset": self.domain.preset["preset_id"], "pool": self.domain.pool["task_pool_id"]},
            "validation_result": dict(_OK_VALIDATION),
        }
        # STAGE_ONLY writes to the staging area, not truth.
        self.store.stage_set(self.wp_id, result)
        return result

    # -- 3. WP_COMMIT_STAGED_TASKS (MUTATES_TRUTH) -------------------------

    def commit_staged_tasks(self) -> dict:
        wp = self.store.load_wp(self.wp_id)
        staged = self.store.load_staged(self.wp_id)
        committed_tasks = []
        for st in staged["tasks"]:
            task_id = st["task_id"]
            self.store.allocate_id(task_id)  # never-reused id ledger
            committed_tasks.append({
                "task_id": task_id,
                "wp_id": self.wp_id,
                "name": st["name"],
                "task_type": st["task_type"],
                "phase": st["phase"],
                "status": "COMMITTED",
                "dependencies": st.get("dependencies", []),
                "owner_role": "CQV",
                "duration_ref": st.get("duration_ref"),
                "proposed_start_date": None,
                "proposed_finish_date": None,
                "committed_start_date": None,
                "committed_finish_date": None,
                "provenance_refs": {"staged_from": staged["staged_task_set_id"]},
            })
        wp["tasks"] = committed_tasks
        wp["lifecycle_state"] = "WP_COMMITTED"
        wp["updated_at_utc"] = now_utc()
        self.store.commit_truth(self.wp_id, "WP_COMMIT_STAGED_TASKS", wp)
        return wp

    # -- 4. PLAN_GENERATE_PROPOSAL (GENERATES_ARTIFACT, deterministic) -----

    def generate_plan_proposal(self) -> dict:
        wp = self.store.load_wp(self.wp_id)
        cursor = next_working_day(date(2026, 7, 1))
        schedule = []
        for task in wp["tasks"]:
            profile_key = task["duration_ref"]["profile_key"]
            value, unit = self.domain.resolve_duration(profile_key)
            start = cursor
            finish = add_working_days(start, int(value)) if unit == "WORKING_DAYS" else start
            schedule.append({
                "task_id": task["task_id"],
                "proposed_start_date": start.isoformat(),
                "proposed_finish_date": finish.isoformat(),
                "duration_value": value,
                "duration_unit": unit,
                "depends_on": task.get("dependencies", []),
            })
        result = {
            "action_type": "PLAN_GENERATE_PROPOSAL",
            "plan_proposal_id": f"{self.wp_id}-PLAN-001",
            "wp_id": self.wp_id,
            "state": "PROPOSED",
            "apply_required": True,
            "planning_basis": "PROFILE_BASED",
            "calendar_logic_ref": self.domain.calendar_logic_ref,
            "profile_ref": {"profile_id": self.domain.profile["profile_id"], "version": self.domain.profile["version"]},
            "schedule": schedule,
            "provenance_stamps": {"profile": self.domain.profile["profile_id"], "calendar": self.domain.calendar_logic_ref["calendar_id"]},
            "validation_result": dict(_OK_VALIDATION),
        }
        self.store.stage_plan(self.wp_id, result)
        return result

    # -- 5. WP_APPLY_PLAN_PROPOSAL (MUTATES_TRUTH) -------------------------

    def apply_plan_proposal(self) -> dict:
        wp = self.store.load_wp(self.wp_id)
        plan = self.store.load_plan(self.wp_id)
        by_task = {row["task_id"]: row for row in plan["schedule"]}
        for task in wp["tasks"]:
            row = by_task.get(task["task_id"])
            if row:
                task["committed_start_date"] = row["proposed_start_date"]
                task["committed_finish_date"] = row["proposed_finish_date"]
                task["provenance_refs"]["plan"] = plan["plan_proposal_id"]
        wp["planning_basis"] = "PROFILE_BASED"
        wp["updated_at_utc"] = now_utc()
        self.store.commit_truth(self.wp_id, "WP_APPLY_PLAN_PROPOSAL", wp)
        return wp

    # -- 6. DOC_GENERATE_DRAFT (GENERATES_ARTIFACT, AI narrative step) -----

    def generate_doc_draft(self) -> dict:
        bundle = self.domain.standards_bundle_ref
        model_input = {"wp_id": self.wp_id, "doc_type": "VMP", "bundle": bundle["bundle_id"]}

        def generator(prompt: PromptAsset, model_input: dict, attempt: int) -> dict:
            # Deterministic stub model (temp 0). A real model plugs in here unchanged.
            return {
                "action_type": "DOC_GENERATE_DRAFT",
                "doc_id": f"{self.wp_id}-DOC-VMP-001",
                "doc_type": "VMP",
                "doc_version": "0.1-draft",
                "wp_id": self.wp_id,
                "state": "DRAFT",
                "generated_at_utc": now_utc(),
                "template_ref": {"template_id": "T1_VMP_Template", "template_version": "v1.0.1"},
                "bundle_ref": {
                    "bundle_id": bundle["bundle_id"],
                    "bundle_version": bundle["bundle_version"],
                    "usage_classification": "PRODUCT_TESTING_ONLY",
                },
                "citation_set": [{"anchor": "EXT-EUGMP-ANNEX15", "status": "NO_EXCERPTS"}],
                "source_chain_provenance": {"preset": self.domain.preset["preset_id"], "prompt_version": prompt.version},
                "source_input_completion_status": "COMPLETE",
                "provenance_stamps": {"prompt_version": prompt.version, "prompt_hash": prompt.content_hash},
                "testing_only": True,
                "testing_only_stamp_required": True,
                "testing_only_stamp": PRODUCT_TESTING_ONLY,
                "usage_classification": "PRODUCT_TESTING_ONLY",
                "regulated_output_allowed": False,
                "validation_result": dict(_OK_VALIDATION),
            }

        # Runs the locked D-08 refuse/accept loop; validates against the result schema.
        draft = self.ai.generate(
            DOC_DRAFT_PROMPT, model_input,
            "schemas/contracts/doc_draft_result.schema.json", generator,
        )
        self.store.stage_doc(self.wp_id, draft)
        return draft

    # -- 7. DOC_FINALIZE_ARTIFACT (GENERATES_ARTIFACT; not a runtime gate) -

    def finalize_doc_artifact(self) -> dict:
        draft = self.store.load_doc(self.wp_id)
        generated_at = now_utc()
        artifact_metadata = {
            "doc_id": draft["doc_id"],
            "doc_type": draft["doc_type"],
            "doc_version": "1.0-final",
            "wp_id": self.wp_id,
            "state": "FINAL",
            "generated_at_utc": generated_at,
            "template_ref": draft["template_ref"],
            "bundle_ref": draft["bundle_ref"],
            "citation_set": draft["citation_set"],
            "source_chain_provenance": draft["source_chain_provenance"],
            "source_input_completion_status": "COMPLETE",
            "provenance_stamps": draft["provenance_stamps"],
            "testing_only": True,
            "testing_only_stamp": PRODUCT_TESTING_ONLY,
            "usage_classification": "PRODUCT_TESTING_ONLY",
            "regulated_output_allowed": False,
        }
        checksum = canonical_hash(artifact_metadata)
        result = {
            "action_type": "DOC_FINALIZE_ARTIFACT",
            "doc_id": draft["doc_id"],
            "doc_type": draft["doc_type"],
            "doc_version": "1.0-final",
            "wp_id": self.wp_id,
            "state": "FINAL",
            "template_ref": draft["template_ref"],
            "bundle_ref": draft["bundle_ref"],
            "citation_set": draft["citation_set"],
            "source_chain_provenance": draft["source_chain_provenance"],
            "source_input_completion_status": "COMPLETE",
            "provenance_stamps": draft["provenance_stamps"],
            "testing_only": True,
            "testing_only_stamp": PRODUCT_TESTING_ONLY,
            "checksum": checksum,
            "artifact_metadata": artifact_metadata,
            "validation_result": dict(_OK_VALIDATION),
        }
        return result

    # -- 8. RPT_GENERATE_WORKBOOK_EXPORT (GENERATES_ARTIFACT; GATE-Export) -

    def export_workbook(self) -> dict:
        wp = self.store.load_wp(self.wp_id)
        snapshot_hash = canonical_hash(wp)
        sheets = ["Metadata", "WorkPackage", "Tasks", "Schedule", "Provenance"]
        sheet_validation = [
            {"sheet_name": name, "required": True, "present": True, "errors": [], "warnings": []}
            for name in sheets
        ]
        artifact_metadata = {
            "artifact_id": f"{self.wp_id}-XLSX-001",
            "artifact_type": "WORK_PACKAGE_WORKBOOK_EXPORT",
            "artifact_label": f"{self.wp_id} workbook export (testing only)",
            "target_scope": "SINGLE_WP",
            "wp_ids": [self.wp_id],
            "source_snapshot_hash": snapshot_hash,
            "template_id": "RPT_WORKBOOK_EXPORT",
            "template_version": "v1.0.1",
            "contract_id": "VALOR-contract-orch-rpt",
            "contract_version": "v1.0.1",
            "action_type": "RPT_GENERATE_WORKBOOK_EXPORT",
            "generated_at_utc": now_utc(),
            "projection_only": True,
            "mutates_wp_truth": False,
            "stamps": {"testing_only": True, "testing_only_stamp": PRODUCT_TESTING_ONLY},
            "validation_result": {"ok": True, "mode": "STRICT", "errors": [], "warnings": []},
            "content_ref": {"ref_type": "FILE", "format": "XLSX", "uri": f"exports/{self.wp_id}-001.xlsx"},
        }
        result = {
            "artifact_metadata": artifact_metadata,
            "workbook_type": "WORK_PACKAGE_WORKBOOK_EXPORT",
            "workbook_format": "XLSX",
            "required_sheets": sheets,
            "sheet_validation": sheet_validation,
            "workbook_schema_ref": "schemas/objects/workbook_export_schema.json",
        }
        return result
