# B5 — Project Container (implementation note)

**Status:** LANDED (B5) · **Gap:** G-18 (Project container above WP, P1) · **Decisions:** D-10/D-11 (projection-only, no truth ownership) · D-13 (no truth gates; sole control = scope-bound) · **Baseline:** frozen pack v1.0.1 / `0ec3060`.
**Layer scope:** the build/runtime layer (L2) in `src/valor_build/`. The pack (L1) is consumed read-only; nothing here edits it.

> This is an **implementation note**, not an architecture spec — hence the `B5` prefix. The architecture is fixed by A18 §2 (M4 Project Mode); B5 is the code that makes it run. It is **additive on B6**: the dispatch spine, store, audit, stamps, and the per-WP M3 slice are reused unchanged. B5 adds the M4 projection that composes ≥2 committed WPs into one consolidated, projection-only artifact.

---

## 1. What it does

Runs the B5 vertical in one pass: the proven B6 slice for **≥2 PE-HIGH work packages** (each its own M3 truth path), then an **M4 Project container** that composes them and emits one consolidated **status report** over the `SELECTED_WP_SET`:

```
python -m valor_build.project_skeleton
```

```
[M3] WP-PEH-A1: create→…→export      (own truth)
[M3] WP-PEH-B2: create→…→export      (own truth)
[M4] PRJ-PEH-001: RPT_GENERATE_STATUS_REPORT over {A1, B2}   (projection only)
```

The M4 step runs in **M4** (runtime) · **BUILD** (lifecycle) · **EXECUTION** (engine-authority), with **no gate** and **no confirmation** — D-13's sole control is the **scope-bound**, enforced in `ProjectContainer.compose` *before* dispatch. The whole run shares one audit channel (A16 §4 / A18 §3).

---

## 2. The container owns no truth (D-10/D-11/D-13)

The Project container composes single-entity WPs **by context** into one project view. It never corrects, overwrites, infers, or mutates WP truth:

- **Each member WP runs its own M3 path** for *its* truth (the B6 slice). The container only **references** the committed snapshots M3 already wrote.
- **No truth-mutation gates** on the container. Stage/Commit/Plan/Apply gates exist to write WP truth; they ran inside each member's M3 path, not here. The M4 dispatch passes `gate=None`.
- **Sole control = the scope-bound (R3).** `ProjectContainer.compose` refuses anything that isn't an explicit, bounded set of committed WPs:

| Refused input | Why |
|---|---|
| `ALL_WPS` (bare sentinel or in the set) | out of freeze scope — pack RPT `target_scope_policy.excluded_from_freeze_scope` |
| empty set | scope-bound requires ≥1 WP |
| duplicate ids | not a well-formed set |
| a member with no committed snapshot | nothing to project — must run its M3 path first |
| a tombstoned member | cannot project tombstoned truth |

The projection reads committed snapshots **read-only** and writes nothing to the truth store — verified by the ledger's `TRUTH_TRANSITION` count being unchanged across the M4 step.

---

## 3. The consolidated projection (grounded in the frozen pack)

The M4 artifact is `RPT_GENERATE_STATUS_REPORT` — a `GENERATES_ARTIFACT` action under the pack's **projection contract** `VALOR-contract-orch-rpt`, whose `projection_policy` fixes `mutates_wp_truth: false`. It is `confirm: false` (a light projection). The result is built deterministically from committed truth — **no AI call** is involved (the narrative AI step belongs to per-WP `DOC_GENERATE_DRAFT` in M3):

- `artifact_metadata` (per `rpt_artifact_metadata_schema.json`): `target_scope: SELECTED_WP_SET`, `wp_ids: [...]`, a consolidated `source_snapshot_hash` over the ordered members, `projection_only: true`, `mutates_wp_truth: false`, `validation_result` in `STRICT` mode, `content_ref` → `REPORT_SOURCE`.
- `report_type: WORK_PACKAGE_STATUS_REPORT`; the **nine canonical `report_sections`** (cover → executive summary → overview → task status → schedule → risks → traceability → recommendations → appendix), each with a deterministic projection summary derived from the member snapshots.
- `rendered_report_source` + `pdf_intent: true`.

The result is validated against `report_result.schema.json` by the dispatch spine — a validation miss is a refusal, like every other boundary.

---

## 4. M4 reachability — reconciled to A18 §2

A18 §2 names M4's real actions as *"consolidated `RPT_GENERATE_*` over the set"* — and those are the `GENERATES_ARTIFACT` class, **not** `READ_ONLY`. The B4/B6 placeholder reachability set `{READ_ONLY}` was therefore too tight once M4 was actually exercised. B5 reconciles `modes/runtime.py` to A18 §2 with a **contract-aware** rule:

> **M4 reaches `READ_ONLY` plus the projection-only subset of `GENERATES_ARTIFACT`** — i.e. artifacts under the RPT projection contract (`VALOR-contract-orch-rpt`). It reaches **none** of the truth path (`MUTATES_TRUTH`/`STAGE_ONLY`) and **not** the per-WP `PLAN_*`/`DOC_*` artifacts that feed M3's truth path.

This is a **code↔doc reconcile to A18 §2, not a new policy** — D-13 ("no truth gates; sole control = scope-bound") is preserved exactly. If the owner prefers a stricter encoding (pure `READ_ONLY` M4, consolidation assembled outside the dispatch spine), it is a one-line flip in `_REACHABLE`/`is_reachable`. **[OPEN — owner may tighten]**

---

## 5. Module map (added / touched)

- **`engine/project.py`** *(new)* — `ProjectContainer` (compose with scope-bound enforcement; consolidated `build_status_report`); `ScopeBoundError`; the `ALL_WPS` sentinel and `SELECTED_WP_SET` constants.
- **`project_skeleton.py`** *(new)* — the B5 driver: runs the B6 slice per WP into a shared store + audit, composes the container, dispatches the M4 projection. Runnable via `python -m valor_build.project_skeleton`.
- **`modes/runtime.py`** *(touched)* — M4 reachability reconciled to A18 §2 (§4 above); `require_reachable`/`is_reachable` gained an optional `contract_id` for the projection exception (backward-compatible).
- **`engine/dispatch.py`** *(touched, 1 line)* — passes `spec.contract_id` into the reachability check.
- **`skeleton.py`** *(touched, 1 line)* — optional shared `audit` parameter so a project run is one audit channel (backward-compatible; B6 behaviour unchanged).

Everything else from B6 is reused **unchanged**.

---

## 6. Verification

- `python -m valor_build.project_skeleton`: 2 × M3 slices (8/8 steps each) + 1 × M4 projection — `projection_only=True`, `mutates_wp_truth=False`; 39 audit records: **gates=10, all from the M3 members (zero from M4)**, 17 stamps, 2 AI calls.
- `pytest`: **23 passed** — 10 B6 (unchanged) + 13 B5 (compose ≥2 WPs · projection read-only · M4 mutates no truth · no truth gates in M4 · scope-bound refuses ALL_WPS / empty / uncommitted / duplicates · M4 reaches projection RPT only, never the truth path · projection validates with 9 sections · BUILD testing-only stamp · members keep their own committed truth).
- R5 guard: the M4 output carries `PRODUCT_TESTING_ONLY`.

---

## 7. Exit criterion (Phase-B plan B5)

> An M4 projection composes ≥2 PE-HIGH WPs read-only, no truth gates, scope-bound enforced. ✔ — WP stays the single-entity, boundary-defended source of truth; the container is a projection shell.
