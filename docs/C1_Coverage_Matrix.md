# C1 Engine — Action × Class × Mode Coverage Matrix

**Phase C / C1 Engine · Step 2 (Coverage).** Generated from the live frozen registry `CONTRACT_REGISTRY_v1.0.1.yaml` @ `0ec3060` via `engine.registry` (A16 §4) — no action list hard-coded. Over the single `PS-PE-HIGH` preset, BUILD lifecycle, gates log-only (A17), outputs `PRODUCT_TESTING_ONLY` (R5).

- **Coverage entries:** 96  (23 mode-gated actions × 4 modes = 92, + 4 PS engine-internal = 96)
- **Exercised:** 49   **N/A-by-reach:** 47   **Failed:** 0
- **Active actions covered:** 27 / 27

Reach rule (A18 §2 / D-15): **M1 & M2 advisory** = `READ_ONLY`+`VALIDATE_ONLY`; **M3** = all classes (only mode reaching `MUTATES_TRUTH`/`STAGE_ONLY`); **M4** = `READ_ONLY` + projection-only RPT `GENERATES_ARTIFACT` (D-13). PS internal-resolver actions are engine-internal / mode-agnostic (S19).

| Action | Contract | Side-effect | M1 | M2 | M3 | M4 | Engine-internal |
|---|---|---|:--:|:--:|:--:|:--:|:--:|
| `DOC_FINALIZE_ARTIFACT` | doc | GENERATES_ARTIFACT | ▫️ N/A | ▫️ N/A | ✅ | ▫️ N/A | — |
| `DOC_GENERATE_DRAFT` | doc | GENERATES_ARTIFACT | ▫️ N/A | ▫️ N/A | ✅ | ▫️ N/A | — |
| `PLAN_GENERATE_PROPOSAL` | plan | GENERATES_ARTIFACT | ▫️ N/A | ▫️ N/A | ✅ | ▫️ N/A | — |
| `PLAN_VALIDATE_PROPOSAL` | plan | VALIDATE_ONLY | ✅ | ✅ | ✅ | ▫️ N/A | — |
| `PS_LIST_PRESETS` | ps | READ_ONLY | — | — | — | — | ✅ |
| `PS_READ_PRESET` | ps | READ_ONLY | — | — | — | — | ✅ |
| `PS_RESOLVE_PRESET` | ps | READ_ONLY | — | — | — | — | ✅ |
| `PS_VALIDATE_BINDINGS` | ps | VALIDATE_ONLY | — | — | — | — | ✅ |
| `RPT_GENERATE_GANTT_CHART` | rpt | GENERATES_ARTIFACT | ▫️ N/A | ▫️ N/A | ✅ | ✅ | — |
| `RPT_GENERATE_STATUS_REPORT` | rpt | GENERATES_ARTIFACT | ▫️ N/A | ▫️ N/A | ✅ | ✅ | — |
| `RPT_GENERATE_WORKBOOK_EXPORT` | rpt | GENERATES_ARTIFACT | ▫️ N/A | ▫️ N/A | ✅ | ✅ | — |
| `RPT_GET_ARTIFACT` | rpt | READ_ONLY | ✅ | ✅ | ✅ | ✅ | — |
| `RPT_LIST_ARTIFACTS` | rpt | READ_ONLY | ✅ | ✅ | ✅ | ✅ | — |
| `RPT_VALIDATE_GANTT_INPUTS` | rpt | VALIDATE_ONLY | ✅ | ✅ | ✅ | ▫️ N/A | — |
| `RPT_VALIDATE_REPORT_INPUTS` | rpt | VALIDATE_ONLY | ✅ | ✅ | ✅ | ▫️ N/A | — |
| `RPT_VALIDATE_STAMPS` | rpt | VALIDATE_ONLY | ✅ | ✅ | ✅ | ▫️ N/A | — |
| `RPT_VALIDATE_WORKBOOK_EXPORT` | rpt | VALIDATE_ONLY | ✅ | ✅ | ✅ | ▫️ N/A | — |
| `WP_APPLY_PLAN_PROPOSAL` | wp | MUTATES_TRUTH | ▫️ N/A | ▫️ N/A | ✅ | ▫️ N/A | — |
| `WP_BIND_PRESET_CONTEXT` | wp | MUTATES_TRUTH | ▫️ N/A | ▫️ N/A | ✅ | ▫️ N/A | — |
| `WP_COMMIT_STAGED_TASKS` | wp | MUTATES_TRUTH | ▫️ N/A | ▫️ N/A | ✅ | ▫️ N/A | — |
| `WP_CREATE` | wp | MUTATES_TRUTH | ▫️ N/A | ▫️ N/A | ✅ | ▫️ N/A | — |
| `WP_GET` | wp | READ_ONLY | ✅ | ✅ | ✅ | ✅ | — |
| `WP_STAGE_TASKS` | wp | STAGE_ONLY | ▫️ N/A | ▫️ N/A | ✅ | ▫️ N/A | — |
| `WP_UPDATE_TASK_FIELDS` | wp | MUTATES_TRUTH | ▫️ N/A | ▫️ N/A | ✅ | ▫️ N/A | — |
| `WP_RECORD_CONFIRMATION` | wp-user-driven-baseline | MUTATES_TRUTH | ▫️ N/A | ▫️ N/A | ✅ | ▫️ N/A | — |
| `WP_SET_PLANNING_BASIS` | wp-user-driven-baseline | MUTATES_TRUTH | ▫️ N/A | ▫️ N/A | ✅ | ▫️ N/A | — |
| `WP_SET_TASK_DURATION_OVERRIDES` | wp-user-driven-baseline | MUTATES_TRUTH | ▫️ N/A | ▫️ N/A | ✅ | ▫️ N/A | — |

**Legend:** ✅ exercised (dispatched green / B6 seed) · ▫️ N/A (class unreachable in mode, recorded reason) · — not applicable.

Every N/A cell carries the `ModeReachError` reason in the harness output (`engine.coverage.run_coverage_matrix`). The matrix is regenerated, not transcribed: `python -m valor_build.coverage`.
