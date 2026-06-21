# Changelog

All notable changes to the build-preparation effort for the Valor Architecture Pack are recorded here.
Format follows the spirit of [Keep a Changelog](https://keepachangelog.com/). Versions here track the **build-prep workstream**, separate from the pack's own architecture version.

> Scope: this changelog covers planning/build-prep artifacts (gap assessment, session log, audit report, build strategy, runtime spec) and any agreed changes staged for the pack. It does **not** replace the pack's own manifest/version records.
>
> **Note (build-prep-0.3):** the pack's own status was `pre_freeze_controlled` (mixed `released` / pre-freeze across blocks), **not frozen** — its registry retained freeze blockers. Earlier entries describing v1.0.1 as "frozen" were superseded by that correction. **As of build-prep-0.8 the freeze is real:** registry `frozen_controlled`, tag `v1.0.1` at `0ec3060`.

---

## [Unreleased]

### Decided (owner-finalized 2026-06-16)
- All 20 gaps + 11 decisions finalized (owner: Amr). Key resolutions: **D-01** separate build repo; **D-02/G-14** we edit pack pre-freeze then owner freezes (freeze-readiness = Phase A); **G-16** rename pack envelope `M1/M2`→`DESIGN/EXECUTION`, runtime modes `M1 Advisory · M2 Delivery Plan · M3 WP Mode · M4 Project Mode`; **G-04** full thin vertical skeleton; **G-06/D-03** file/git store, lock-aware write path, multi-user deferred; **G-09/D-09** `co-design/` dir; **D-08** LLM interface locked (model TBD); **G-07** crypto identity deferred but carried as a named plan milestone. (G-12 + G-20 = one CI/harness workstream.)

### Decided (2026-06-19 — B4/B5 pre-decisions, post-0.11)
- **D-12 (staging editability):** free amend while STAGED (no gate beyond GATE-Commit); post-commit changes append-only only — add new task / `WP_UPDATE_TASK_FIELDS` / tombstone; no in-place insert; IDs immutable, never reused (A04_2 §4).
- **D-13 (M4 container gates):** the Project container has **no truth-mutation gates** (extends D-10/D-11, projection-only); the consolidated plan is a projection over `SELECTED_WP_SET` with per-WP gates running inside each WP (M3); sole control is the scope-bound — explicit selected set, `ALL_WPS` refused/bounded (R3).

### Phase A — COMPLETE (shipped build-prep-0.4 → 0.8)
- A1 mode rename (G-16) · A2 integrity tooling (G-19) · A3 vector/CI harness (G-12+G-20) · A4 standards/anchor reconciliation + `PUBLIC_EXCERPT` cleanup (G-10/G-11) · pre-A5 freeze-state cleanup · A5 freeze. **Pack frozen at v1.0.1 (`0ec3060`).**

### Phase B — in progress
- **B1 COMPLETE (build-prep-0.9):** build repo + `co-design/` published (D-01/D-09); pack pinned as a read-only **submodule** at v1.0.1 (`0ec3060`).
- **B2 COMPLETE (build-prep-0.10):** runtime spec A16 written (G-01).
- **B3 COMPLETE (build-prep-0.11):** BUILD mode spec A17 — gates log-only (G-02/D-07).
- **B4 COMPLETE (build-prep-0.12):** runtime mode model A18 — M1–M4, two axes, latitude ladder, labels (G-16/G-17).
- **B6 COMPLETE (build-prep-0.13):** walking skeleton — full vertical `create→stage→commit→plan→apply→draft→finalize→export` runs end-to-end against PE-HIGH in M3·BUILD·EXECUTION, gates log-only; first runnable build `0.1.0` (G-04).
- **B5 COMPLETE (build-prep-0.14):** M4 Project container — projection over `SELECTED_WP_SET`, no truth gates (D-13), scope-bound as sole control (R3); composes ≥2 committed PE-HIGH WPs read-only into one consolidated status report; build `0.2.0` (G-18). Additive on the B6 spine.
- **B7 COMPLETE (build-prep-0.15):** identity soft controls — declared role-context capture (audited), role stamped on every output, warn-with-ack for sensitive (`confirm:true`) actions with no declared role (D-14, Option A); cryptographic identity **named** as `M-IDENTITY` (integrates at A09 §6.2; fills the already-cut `actor.id` seam); build `0.3.0` (G-07). No pack edits.
- **Phase B at EXIT:** all seven exit criteria met (B1–B7). No further mandated B-item; next track is owner's call (`M-IDENTITY` / O1 model / O2 UI / housekeeping).

### Phase C — APPROVED & restructured (build-prep-0.17)
- **Phase C plan APPROVED + reshaped (build-prep-0.17):** `co-design/PHASE_C_BUILD_OUT_PLAN.md` — five loose tracks → **four named Build-Out milestones** (C1 Engine 🎉 → C2 AI → C3 UI → C4 Multi-user), linear/engine-first. Vertical-slice→full-CQV-coverage gap homed in C1 (action×class×mode over the single `PS-PE-HIGH` preset). OC-1 resolved (multi-user in = C4); OC-3 resolved (engine-first); OC-2 open; OC-4 → Phase E. Phasing map landed in `BUILD_STRATEGY.md` §0; Phases D/E stubbed. No code; no pack edits.

### Phase C — C1 Step 1 hygiene batch (build-prep-0.18)
- **C1 hygiene & reconciliation batch landed (build-prep-0.18):** gate shorthand 6→5; schema-count 52/51 clarified; O4(a) CRLF cure APPLIED; G-10 fold CONFIRMED & closed; M4-reach = (A) keep READ_ONLY + projection-RPT (D-13). Doc/config-only; no code; pack untouched. Next: **C1 Step 2 — coverage (CODE)**.

### Phase C — C1 Step 2: coverage matrix (build-prep-0.19)
- **C1 action×class×mode coverage landed (build-prep-0.19):** the engine now exercises **all 27 active actions** (23 `ACTIVE_FROZEN` + 4 `ACTIVE_INTERNAL_FROZEN`) across the runtime-mode grid over the single `PS-PE-HIGH` preset, on the B6 dispatch/store/audit/stamp spine. New **D-15** (M1 & M2 advisory only — contracted generation is M3-only, consolidation M4; deletes A18's "contracted-but-non-binding" middle category). First Phase C code → build **`0.3.0`→`0.4.0`**; gates log-only (G-02/D-07). No pack edits.

---

## [build-prep-0.19] — 2026-06-21 — Phase C / C1 Step 2: action×class×mode coverage matrix (CODE, build `0.4.0`)

First code of Phase C. The walking skeleton proved **one** vertical path; this closes the vertical-slice→full-coverage gap that C1 owns: every **active** action runs through the dispatch spine in each mode its side-effect class can reach, over the single `PS-PE-HIGH` preset, BUILD lifecycle, gates log-only (A17), outputs `PRODUCT_TESTING_ONLY` (R5). Co-design/build by Mervat; owner (Amr) commits/pushes. No pack edits; pack stays `0ec3060`.

### Decided
- **D-15 — M1 & M2 are advisory; contracted generation is M3-only.** Reach for both M1 and M2 is `READ_ONLY` + `VALIDATE_ONLY`. M2's "plan" is an **uncontrolled workflow cheat-sheet** (+ example artifacts) produced at the AI layer (C2), referencing real WP/task numbers but **not** a `PLAN_GENERATE_PROPOSAL`/`DOC_GENERATE_DRAFT` dispatch. All contracted generation → M3; consolidated `RPT_GENERATE_*` → M4. Deletes A18's "contracted-but-non-binding, stamped `PROPOSED`" middle category — a schema-valid contracted object can only originate on the truth path.

### Added
- **`src/valor_build/engine/coverage_handlers.py`** — `CoverageHandlers(Handlers)`: the 19 remaining active-action handlers (WP read + 6 truth mutations, PLAN validate, the RPT generate/validate/read family, the 4 PS internal-resolver actions). Thin, deterministic, schema-valid per each action's `result_schema_ref`; truth mutations through the store's single commit chokepoint.
- **`src/valor_build/coverage.py`** — registry-driven matrix harness. Reads the active set **live** from `CONTRACT_REGISTRY_v1.0.1.yaml` via `engine.registry` (A16 §4 — no action list hard-coded), seeds a committed WP via the B6 walking skeleton, then fills a **96-entry** grid: 23 mode-gated actions × 4 modes (92) + 4 PS engine-internal. Each cell EXERCISED (dispatched green / B6 seed) or N/A with the recorded `ModeReachError` reason. `python -m valor_build.coverage`.
- **`docs/C1_Coverage_Matrix.md`** — the committed, regenerated coverage report: **96 entries, 49 exercised, 47 N/A, 0 failed, 27/27 active actions.**
- **`tests/test_coverage_matrix.py`** — 9 invariant tests (96-entry shape; 92+4 partition; registry 27-active / 12-testing-only; M3 reaches all 23; MUTATES/STAGE only M3; M1&M2 advisory + identical reach; M4 = READ_ONLY + projection-RPT only; every N/A records a reach reason).

### Changed
- **`src/valor_build/modes/runtime.py`** — `_REACHABLE[M2]` tightened to `{READ_ONLY, VALIDATE_ONLY}` (D-15); docstring updated. M1/M3/M4 unchanged (M4 keeps the projection-only RPT `GENERATES_ARTIFACT` exception, D-13).
- **`docs/A18_Runtime_Mode_Model.md`** — §2 M1/M2 rows, §3 latitude rows, and §3a rewritten for D-15; D-15 amendment block added under §2.
- **`co-design/VALOR_Build_Readiness_Gap_Assessment_v0.3.md`** — D-15 row + decision-log entry.
- **Build version `0.3.0` → `0.4.0`** (`pyproject.toml`, `src/valor_build/__init__.py`).

### Verification
- Full suite **41 passed** (32 existing, regression-free + 9 new). Coverage harness green: 96 cells, 0 failed. Pack submodule untouched (`0ec3060`).

---

## [build-prep-0.18] — 2026-06-21 — Phase C / C1 Step 1: hygiene & reconciliation batch (doc/config-only)
**Doc/config-only; no code; build unchanged at `0.3.0`; pack untouched at `0ec3060`.**

### Changed
- **Gate shorthand 6→5** — the stale `Stage/Validate/Commit/Apply/Finalize/Close` six-form (it dropped the real **Plan** + **Export** gates and folded in three non-gates) corrected to the five canonical gates **Stage/Commit/Plan/Apply/Export** (`A04_1` §4.1) in the **G-02** row (gap assessment) and the **B3** slice (Phase-B plan). The one stale-as-fact mention in a superseded `SESSION_LOG` NEXT block carries a bracketed inline correction (verbatim-log discipline preserved).
- **Schema-count 52/51 clarified** — `A16` §schema-dialect now states: 52 `.json` under `schemas/`, 51 draft-07 schemas with `$id`, and `schemas/documents/index.json` is a non-schema index manifest. No count changed; "51 schemas" / "52 files" are each correct in context.

### Confirmed / closed
- **O4(a) — CRLF cure APPLIED.** Owner ran `git config core.autocrlf false` in the working tree (doc half already in `BUILD_STRATEGY` §5). O4(a) CLOSED. *(O4(b) KS trailing-newlines remain re-homed to the Phase-E pack-v1.1.0 batch — pack-touching.)*
- **G-10 fold — CONFIRMED & CLOSED.** Nothing governed left unfolded: `STD-CQV-BASE` = 16 `CQV-REQ` (1:1 with 16 `MAP-CQV-REQ`); CSV/cleanroom governed via add-on-bundle triggers (CQV-REQ-011 → BND-CSV-ADDON, CQV-REQ-012 → BND-CLEANROOM-ADDON); equipment-domain (MGT/PEQ/CUTIL/BUTIL/CAL) homed in task pools/profiles, not standards. The seven S1-drafted standards were co-design drafts, never committed. No genuinely-new governed requirement surfaced.

### Decided (owner, 2026-06-21)
- **M4-reachability = (A) KEEP** — M4 stays `READ_ONLY` + projection-RPT (current B5 behaviour); not tightened to pure READ_ONLY. Consistent with D-13; one-line reversible. (No new D-series.) Owner's broader M4 scope idea parked as a named item.

### Notes
- Registry figures reconciled for the next agenda (from `CONTRACT_REGISTRY_v1.0.1.yaml` @ `0ec3060`): **39 actions** = 23 `ACTIVE_FROZEN` + 4 `ACTIVE_INTERNAL_FROZEN` + 12 `TESTING_ONLY_FROZEN`; **7 contracts**; **5 side-effect classes** (READ_ONLY 14 · VALIDATE_ONLY 10 · MUTATES_TRUTH 8 · GENERATES_ARTIFACT 6 · STAGE_ONLY 1). The C1-Step-2 coverage target "27 active" = 23 active + 4 internal.
- All repo changes via gitignored `apply_session18.py` (LF-deterministic, idempotent, fail-closed, base64-embedded; pack never touched).

---

## [build-prep-0.17] — 2026-06-21 — Phase C APPROVED & restructured (four Build-Out milestones); phasing map; Phases D & E stubbed (doc-only)
**Doc-only; no code; build unchanged at `0.3.0`; pack untouched at `0ec3060`.**

### Added
- **`BUILD_STRATEGY.md` §0 Phasing** — the single authoritative phase-map (A complete · B complete · **C Build-Out approved** · D Stabilization planned · E Scope-expansion planned), the open-ended-phasing note, and the **two-widening caveat** (Phase C fills out pack scope / Phase E widens beyond it via a governed v1.1.0).
- **`co-design/PHASE_D_STABILIZATION_PLAN.md`** (PLANNED) — D1 heavy testing → D2 punch list → D3 fix → D4 retest → D5 reissue.
- **`co-design/PHASE_E_SCOPE_EXPANSION_PLAN.md`** (PLANNED) — E1 define new scope → E2 open pack v1.1.0 → E3 freeze/verify → E4 build-out; the governed-pack-edit home.
- *Part of VALOR phasing — see `BUILD_STRATEGY.md` §0.* pointer line in every phase-plan header.

### Changed
- **`co-design/PHASE_C_BUILD_OUT_PLAN.md`** — DRAFT → **APPROVED**; retitled **Build-Out**; five loose tracks → **four named milestones** (C1 Engine 🎉 → C2 AI → C3 UI → C4 Multi-user), linear/engine-first. Vertical-slice→full-CQV-coverage gap now explicitly homed in C1 (action × side-effect-class × mode coverage over the single `PS-PE-HIGH` preset; **27 active actions / 7 contracts / 5 classes / 4 modes**, from the registry at `0ec3060`). Identity (`M-IDENTITY`) folded into C1.
- **`BUILD_STRATEGY.md`** — stale header `Status: scaffold (B1)` → current Phase-C status; §7 repointed off the completed Phase-B sequence to §0 + the Phase-C plan.

### Decided (owner, 2026-06-21)
- Phase C **APPROVED**. **OC-1** resolved (multi-user **in** Phase C = C4). **OC-3** resolved (linear, engine-first). Identity folded under C1 Engine (backend). Three-chapter split mapped to **Phases C / D / E**. **OC-2** (D-14 role-map) stays **open**; **OC-4** (pack v1.1.0) deferred to **Phase E**. No new D-series.

### Correction
- "Effort classes other than PE-HIGH" was incorrect — `PS-PE-HIGH` is the **only** preset at v1.0.1. The breadth gap is action×class×mode coverage over that single preset; new presets are a Phase-E/v1.1.0 matter.
## [build-prep-0.16] — 2026-06-20 — Phase C plan drafted (under owner review; doc-only)

Planning shipment — **no code, no pack edits**, build version unchanged at `0.3.0`. With Phase B at EXIT, lands a structured **Phase C — Build-Out & Hardening Plan** so the post-exit work has a real home. The plan is a **DRAFT for owner review — not approved.** Co-design / doc by Mervat; owner (Amr) commits/pushes. Logged in SESSION_LOG Session 16.

### Why
Phase B exited with four candidate tracks and no organizing plan. Owner called that out — a backlog is not a plan. Phase A and B each had a structured plan doc; Phase C now does too.

### Added
- `co-design/PHASE_C_BUILD_OUT_PLAN.md` — five sequenced work items (C1 hygiene/reconciliation · C2 `M-IDENTITY` verified identity · C3 O1 model / Layer-2 · C4 O2 UI / Layer-3 · C5 O3 multi-user concurrency [scope decision]); dependency diagram; exit criteria; open items OC-1…OC-4; risks R1/R2/R5 carried + R6/R7/R8 new.

### Status
- **DRAFT, under owner review.** Four scoping decisions open (OC-1 C5 scope · OC-2 D-14 Option-B map in C2 · OC-3 C2/C3 ordering · OC-4 pack v1.1.0 batch trigger). Next session opens on owner feedback; no build work until approved.

### Delivery
- One gitignored **`apply_session16.py`** (LF-deterministic, idempotent, fail-closed, `--dry-run` supported; pack never touched). No non-repo (knowledge/UI) artifacts.

---

## [build-prep-0.15] — 2026-06-20 — B7: identity soft controls + named `M-IDENTITY` (Phase B EXIT, build `0.3.0`)

Seventh Phase-B shipment, **third code** shipment, and the **last Phase-B exit item**. **No pack edits** — pack stays **frozen at v1.0.1 (`0ec3060`)**. Lands B7: the A10 §7 / A09 §6.2 soft-control identity stub, and the **named** cryptographic-identity milestone (`M-IDENTITY`). Co-design / build by Mervat; owner (Amr) commits/pushes. Logged in SESSION_LOG Session 15.

### Why
Session 14 landed B5 and pointed NEXT at B7 — **G-07**, the owner's "preserve, don't forget" condition. B7 makes the declared-role soft control explicit and tested *now*, and pins the deferred crypto milestone into the plan so it can't silently disappear.

### Decided — D-14 (Option A)
The A10 §7 inconsistent-role behaviour is a stated *"policy choice."* Owner approved **Option A**: capture + log + warn-with-ack, **no** role→action authority map. Faithful to A10 §7 verbatim, stays *soft*, smallest surface, and does not preclude a role map / verified identity later (the `requires_role_ack` predicate is the one-function seam). The map + real-authority validation fold into `M-IDENTITY`. Full A-vs-B rationale in `docs/B7_Identity_Integration.md`; decision row in the gap assessment (D-14).

### Added
- `src/valor_build/engine/identity.py` — `RoleContext{role, name?, id?}` (`id` reserved for crypto), `RoleContext.capture` (audited `identity_context`, `identity_verified:false`), `actor_block` (A09 §7.1 shape, backward-compatible), `requires_role_ack` (warn-with-ack predicate).
- `tests/test_identity.py` — 9 B7 invariants (capture audited · role stamped on every output · `actor.id` validates through the frozen envelope · warn-with-ack refuses unacknowledged / proceeds when acknowledged · declared role never warns).
- `docs/B7_Identity_Integration.md` — implementation note + D-14 rationale + `M-IDENTITY` milestone.

### Changed
- `src/valor_build/engine/dispatch.py` — capture role-context at entry; envelope `actor` via `actor_block`; **`actor_role` stamped on every output** (A10 §7); warn-with-ack soft control before the confirmation prompt; `StepRequest.actor_name` (optional).
- `co-design/PHASE_B_BUILD_WORKFLOW_PLAN.md` — B7 slice expanded; `M-IDENTITY` named (integration + schema seams); exit #7 updated.
- `co-design/VALOR_Build_Readiness_Gap_Assessment_v0.3.md` — Table 2 row **D-14**; change-log line (doc stays v0.3, growing).
- Version **0.2.0 → 0.3.0** (`__init__.py`, `pyproject.toml`).

### Verified (fresh clone)
- `pytest` → **32 passed** (10 B6 + 13 B5 unchanged + 9 B7). Both drivers green; kind-filtered audit counts unchanged; every output stamp carries `actor_role`. `actor.id` validates through the frozen `contract_request` envelope (no pack/schema change needed for `M-IDENTITY`).

### Delivery
- One gitignored **`apply_session15.py`** (LF-deterministic, idempotent, fail-closed, base64-embedded; pack never touched). No non-repo (knowledge/UI) artifacts.

---

## [build-prep-0.14] — 2026-06-20 — B5: M4 Project container (projection over `SELECTED_WP_SET`, build `0.2.0`)

Sixth Phase-B shipment, **second code** shipment. **No pack edits** — pack stays **frozen at v1.0.1 (`0ec3060`)**. Lands the B5 deliverable: the **M4 Project container** — a projection that composes a `SELECTED_WP_SET` of committed PE-HIGH WPs into one consolidated, projection-only status report, with **no truth gates** and the **scope-bound as its sole control**. Additive on the B6 spine. Co-design / build by Mervat; owner (Amr) commits/pushes. Logged in SESSION_LOG Session 14.

### Why
Session 13 landed B6 (walking skeleton) and pointed NEXT at B5 — **G-18 / D-10 / D-11 / D-13**. B6 proved the per-WP M3 truth path runs; B5 adds the M4 layer **above** the WP that composes several of them without owning their truth.

### Added (build repo — via installer)
- **`src/valor_build/engine/project.py`** — `ProjectContainer` (scope-bound `compose`; deterministic consolidated `build_status_report` over the set), `ScopeBoundError`, the `ALL_WPS` sentinel + `SELECTED_WP_SET` vocabulary. Owns no truth; reads committed snapshots read-only.
- **`src/valor_build/project_skeleton.py`** — the B5 driver: runs the B6 slice for ≥2 PE-HIGH WPs (each its own M3 path) into a shared store + single audit channel, then composes the container and dispatches the M4 projection. Runnable via `python -m valor_build.project_skeleton`.
- **`tests/test_project_container.py`** — 13 B5 invariant tests (compose ≥2 WPs · projection read-only · M4 mutates no truth · no truth gates in M4 · scope-bound refuses ALL_WPS / empty / uncommitted / duplicates · M4 reaches projection RPT only / never the truth path · projection validates with 9 sections · BUILD testing-only stamp · members keep their own committed truth).
- **`docs/B5_Project_Container.md`** — implementation note (no-truth-ownership model, scope-bound table, grounded report shape, M4-reachability reconcile).

### Changed (build repo — via installer)
- **`src/valor_build/modes/runtime.py`** — M4 reachability reconciled to A18 §2: `READ_ONLY` + the projection-only subset of `GENERATES_ARTIFACT` (RPT projection contract `VALOR-contract-orch-rpt`); the truth path (`MUTATES_TRUTH`/`STAGE_ONLY`) stays unreachable. `is_reachable`/`require_reachable` gained an optional `contract_id` (backward-compatible). **Code↔doc reconcile, not a new policy — D-13 preserved.**
- **`src/valor_build/engine/dispatch.py`** — passes `spec.contract_id` into the reachability check (1 line).
- **`src/valor_build/skeleton.py`** — optional shared `audit` parameter so a project run is one audit channel (1 line; B6 behaviour unchanged).
- **`src/valor_build/__init__.py`** + **`pyproject.toml`** — version **0.1.0 → 0.2.0**.
- **`co-design/SESSION_LOG.md`** — Session 14 entry + refreshed NEXT block (→ B7).
- **`co-design/CHANGELOG.md`** — this entry; `[Unreleased]` Phase B flipped B5-next → **B5 done, B7 next**.

### Decided
- **None new.** B5 executes fixed architecture (A18 §2 + D-10/D-11/D-13). The M4-reachability change is a reconcile to A18 §2, flagged for owner awareness; owner may tighten to pure `READ_ONLY` (one-line flip).

### Notes / carried
- New (flag): M4-reachability encoding — owner may tighten. Carried: gate doc-reconcile (6→5) · schema-count 52/51 · O1/O2/O3/O4 · G-10 fold.
- **B7 (identity-integration milestone, G-07) is the last Phase-B exit item.**
- Installer (`apply_session14.py`) verified on a fresh clone: 11 files written, idempotent on re-run, fail-closed, 0 CR bytes, pack untouched, gitignored. Not committed.

### Verification
- `python -m valor_build.project_skeleton`: 2 × M3 slices (8/8 steps) + 1 × M4 projection — `projection_only=True`, `mutates_wp_truth=False`; 39 audit records, gates=10 all from M3 members (zero from M4), 17 stamps, 2 AI calls. `pytest` — **23 passed** (10 B6 + 13 B5). B6 skeleton regression green.

---

## [build-prep-0.13] — 2026-06-20 — B6: walking skeleton (PE-HIGH, first runnable `0.1.0`)

First Phase-B **code** shipment. **No pack edits** — pack stays **frozen at v1.0.1 (`0ec3060`)**. Lands the B6 deliverable: the first runnable build layer, proving the full contract path runs end-to-end against PE-HIGH, thin but full vertical, in **M3 · BUILD · EXECUTION** with gates logging only. Co-design / build by Mervat; owner (Amr) committed/pushed. Logged in SESSION_LOG Session 13.

### Why
Session 12 landed B4 (A18) and pointed NEXT at B6 — **G-04**. A16/A17/A18 fixed the architecture (runtime target, BUILD mode, mode model); B6 is the first code that makes those three execute against the frozen pack and the live PE-HIGH domain.

### Added (build repo — via installer)
- **`src/valor_build/`** — the build layer (12 modules):
  - `pack_access` (locate read-only pack) · `engine/schemas` (fail-closed validator; absolute-`$id` `referencing` registry with the A3 `valor://` ref rewrite) · `engine/registry` (typed action map) · `engine/audit` (single channel + sha256) · `engine/store` (append-only ledger, tombstoning, never-reused IDs, single lock-aware `commit_truth` chokepoint) · `engine/gates` (five canonical gates; BUILD log-only / LIVE halt) · `modes/runtime` (M1–M4 reachability) · `ai/interface` (D-08 locked: hashed prompt, schema-constrained JSON, 1-retry-then-escalate) · `engine/domain` (reads PE-HIGH trio + CAL-WORKWEEK) · `engine/dispatch` (the A16 §5 spine) · `engine/handlers` (8 thin schema-valid handlers) · `skeleton` (runnable slice).
- **`tests/test_walking_skeleton.py`** — 10 invariant tests (full slice · five gates logged · committed truth persisted · unmet gate proceeds in BUILD / halts in LIVE · confirmation-No leaves truth unmutated · BUILD testing-only stamps · IDs never reused · M1 can't reach MUTATES_TRUTH · AI call audited with hashes).
- **`docs/B6_Walking_Skeleton.md`** — implementation note (real-vs-stubbed scope, module map, action→gate table).

### Changed
- **`src/valor_build/__init__.py`** + **`pyproject.toml`** — version **0.0.0 → 0.1.0** (first runnable milestone).

### Removed
- **`tests/test_scaffold.py`** — the trivial `__version__ == "0.0.0"` placeholder, superseded by the real suite.

### Verification
- `python -m valor_build.skeleton`: 8/8 steps ok, 5 gates PASS, 5 confirmations, 1 AI call (ACCEPT), 8 output stamps, 19 audit records, `all_ok=True`. Pack resolves by walk-up with no env var. `pytest` — 10 passed. Installer: LF-deterministic, idempotent, fail-closed, pack untouched, gitignored.

---

## [build-prep-0.12] — 2026-06-19 — B4: runtime mode model A18 (M1–M4)

Fourth Phase-B shipment. **No pack edits** — pack stays **frozen at v1.0.1 (`0ec3060`)**. Lands the B4 deliverable: the runtime mode model — M1–M4 mapped to real action classes, the two pack/lifecycle axes kept separate from the runtime axis, the per-mode latitude ladder, and the G-17 label discipline. Co-design / doc-only; written by Mervat, owner (Amr) committed/pushed. Logged in SESSION_LOG Session 12.

### Why
Session 11 landed B3 (A17) and pointed NEXT at B4 — **G-16/G-17**. With the engine axis renamed to `DESIGN`/`EXECUTION` in Phase A, the runtime layer is free to define modes without collision; B4 does so and disambiguates the three things called "plan."

### Added (build repo — via installer)
- **`docs/A18_Runtime_Mode_Model.md`** — new B4 spec:
  - **§1:** three axes (lifecycle / engine-authority / runtime), R1-separate; engine `[DESIGN, EXECUTION]` verified at the pin, no `M1/M2` collision.
  - **§2:** M1–M4 mapped to registry action classes (M3 = sole truth-writing mode; M4 projection-only, no gates per D-13).
  - **§3:** latitude ladder (M1 high → M3 low; M4 compositional) + owner decisions 3a (M1 non-binding generation, stamped) / 3b (M3 gate-level batch confirm; per-item → O2) + output stamp on the A16/A17 audit channel.
  - **§4:** G-17 label discipline — Delivery Plan (mode) ≠ WP-tasks planning (gate step) ≠ CQV plan (document).

### Changed (build repo — via installer)
- **`co-design/SESSION_LOG.md`** — Session 12 entry + refreshed NEXT block (→ B6; B5 parallel).
- **`co-design/CHANGELOG.md`** — this entry; `[Unreleased]` Phase B flipped B4-next → **B4 done, B6 next**.

### Decided
- **3a** M1 may generate non-binding `PROPOSED`/`DRAFT` stamped `mode: M1`; **3b** M3 keeps pack gate-level batch confirm, per-item review deferred to O2 (both owner).
- **NEXT → B6** (walking skeleton), B5 (Project container) available in parallel.

### Notes / carried
- Carried: gate doc-reconcile (6→5) · schema-count 52/51 · O1/O2/O3 · G-10 fold · G-07/B7 crypto-identity.
- Installer (`apply_session12.py`) verified on a fresh clone: 3 files written, idempotent, fail-closed, 0 CR bytes, pack untouched, gitignored. Not committed.

---

## [build-prep-0.11] — 2026-06-19 — B3: BUILD-mode spec A17 written + gate vocabulary corrected

Third Phase-B shipment. **No pack edits** — pack stays **frozen at v1.0.1 (`0ec3060`)**. Lands the B3 deliverable: a runtime **BUILD mode** spec where the pack's governance gates are log-only/dormant, with the human-confirmation gate and truth-store integrity kept always-live. Co-design / doc-only; written by Mervat, owner (Amr) committed/pushed. Logged in SESSION_LOG Session 11.

### Why
Session 10 landed B2 (A16) and pointed NEXT at B3 — **G-02** (no dormant build mode) / **D-07** (log-only in BUILD). BUILD mode lets development move through governance stops without halting, while preserving Humans-Decide and data integrity.

### Added (build repo — via installer)
- **`docs/A17_Build_Mode_Spec.md`** — new B3 spec:
  - **§1–2:** BUILD as a runtime enforcement policy (not a calendar phase), R2-safe (no pack edit); grounded on the pack's **five canonical gates** (`A04_1` §4.1: Stage/Commit/Plan/Apply/Export).
  - **§3:** log-only behaviour + gate-outcome record on the A16 §4 audit channel.
  - **§4:** always-on in every mode — human-confirmation gate (A04_1 §4.2) + truth-store integrity (fail-closed writes).
  - **§5:** inert-vs-live — one path, one switch.
  - **§6:** R5/Blocker-A guard — `PRODUCT_TESTING_ONLY`, dormant ≠ satisfied; Finalize/Close named as non-gates.

### Changed (build repo — via installer)
- **`co-design/SESSION_LOG.md`** — Session 11 entry + refreshed NEXT block (→ B4).
- **`co-design/CHANGELOG.md`** — this entry; `[Unreleased]` Phase B flipped B3-next → **B3 done, B4 next**.

### Decided
- **Gate enforcement in BUILD → log-only** (D-07 confirmed); **human confirmation → always live, all modes** (owner); **integrity boundary** — BUILD waives gate enforcement, not store correctness.
- **Gate set corrected → five canonical gates**, superseding the "Stage/Validate/Commit/Apply/Finalize/Close" six-item shorthand (Validate/Finalize/Close are not orchestration gates).

### Notes / carried
- **Doc-reconcile (new, non-blocking):** fix the six-gate shorthand in G-02, the Phase-B plan, and SESSION_LOG.
- Carried: schema-count 52/51 · O1/O2/O3/O4 · G-10 fold · G-07/B7 crypto-identity milestone.
- Installer (`apply_session11.py`) verified on a fresh clone: 3 files written, idempotent, fail-closed, 0 CR bytes, pack untouched, gitignored. Not committed.

---

## [build-prep-0.10] — 2026-06-19 — B2: A16 Runtime Target Spec written + checkpoint-delivery docs amended

Second Phase-B shipment. **No pack edits** — pack stays **frozen at v1.0.1 (`0ec3060`)**. Two parts, one all-inclusive landing: (1) the B2 deliverable — A16 runtime spec written; (2) a process-doc amendment documenting `apply*.py` as the standard (never-committed) checkpoint delivery format. Co-design / doc-only; written by Mervat, owner (Amr) committed/pushed. Logged in SESSION_LOG Session 10.

### Why
Session 9 landed B1 and pointed NEXT at B2. A16 is **G-01** — the biggest buildability gap (P0): the pack says *what* the system is, never *what it is built on*. Separately, the written docs described only the *"never commit `apply*.py`"* half of the checkpoint discipline, not that `apply.py` **is** the delivery format — that omission caused a workflow misfire and is corrected here.

### Added (build repo — via installer)
- **`docs/A16_Runtime_Target_Spec.md`** — full spec replacing the skeleton:
  - **§2 Stack (D-04):** Python ≥3.11 · draft-07 · fail-closed at every boundary · request/response envelope.
  - **§3 WP store (G-06/D-03):** file/git · append-only ledger + tombstoning (`A04_2` §4) · lock-aware write path day one · O3 deferred as extension.
  - **§4 LLM interface (D-08 LOCKED):** hashed prompt · temp 0 · schema-constrained JSON · 1-retry-then-escalate · audit hashes · `referencing`/absolute-`$id` resolution (A3 lesson).
  - **§5 Enforcement map:** representative mapping + pointer to `CONTRACT_REGISTRY_v1.0.1.yaml` (7 contracts · 39 actions · 24 result schemas).
  - **§6 Seams** A/B/C with the R2 enforcement point; identity via `A10` stub + named integration point (G-07).

### Changed (process docs)
- **`BUILD_STRATEGY.md` §5** (repo, via installer) — `apply*.py` documented as the **standard checkpoint delivery format, never committed**; gitignored; LF-deterministic / idempotent / fail-closed; manual fallback; pack never touched.
- **`SESSION_PROTOCOL.md`** (project knowledge, owner re-upload) — Checkpoint section amended + **artifact-home → landing-mechanism** table added (repo→installer+commit · knowledge→re-upload · UI→paste).
- **Instructions field** (UI, owner paste) — Checkpoint + Repo-discipline lines amended to match.

### Decided
- **§5 representation → representative mapping + pointer** to the registry (not inline enumeration), durable across a future pack v1.1.0 (D-02).
- **Checkpoint delivery → gitignored `apply_sessionN.py` is standard**, manual fallback (owner-directed; landed all-inclusive).

### Notes / carried
- **Schema-count:** 52 on disk vs 51 cited — 1-file reconcile, non-blocking.
- Installer (`apply_session10.py`) verified on a fresh clone: 4 files written, idempotent, fail-closed, 0 CR bytes, pack untouched, gitignored. Not committed.

---

## [build-prep-0.9] — 2026-06-19 — B1: build-repo scaffold published, pack pinned as read-only submodule

First Phase-B shipment. **No pack edits** — pack stays **frozen at v1.0.1 (`0ec3060`)**. This batch stands up the build repo `Cyber-Mario1979/valor-build` around the frozen pack and migrates the co-design docs into it. Co-design / doc + scaffold only; edits by Mervat, owner (Amr) committed/pushed. Logged in SESSION_LOG Session 9.

### Why
Session 8 armed Phase B; B1 is its first concrete step (per `PHASE_B_BUILD_WORKFLOW_PLAN.md`). The scaffold gives every later B-item a home and realizes D-01 (separate build repo) and D-09 (`co-design/` outside any manifest) materially rather than on paper.

### Added (build repo)
- **Repo skeleton:** `README.md`, `.gitignore` (blocks one-shot installers / `apply*.py`), `.gitattributes` (`eol=lf`), `LICENSE`, `pyproject.toml` — `valor-build` v0.0.0, `requires-python >=3.11`, deps `jsonschema` / **`referencing`** (real `$ref` registry, A3 lesson) / `pyyaml`.
- **`BUILD_STRATEGY.md`:** repo seam, frozen-pack pin, co-evolve policy (pack changes batch into a deliberate **v1.1.0**, never a hotfix), LF discipline.
- **`co-design/`** (outside any manifest): migrated `SESSION_LOG.md`, `CHANGELOG.md`, gap assessment v0.3, audit v1.0, **freeze-status register**, both phase plans, `README.md`.
- **`src/valor_build/`** skeleton — `engine/` `ai/` `modes/` packages (placeholders; engine = the pack, consumed as a dependency) + `tests/test_scaffold.py`.
- **`docs/A16_Runtime_Target_Spec.md`** — SKELETON placeholder; 7 agreed sections stubbed as the home for B2.

### Decided
- **Pin mechanism → git submodule** (read-only, pinned at `0ec3060`), resolving the BUILD_STRATEGY §2 choice of submodule vs. vendored-read-only vs. package.

### Reconciled (rider)
- Freeze-status register: scheme-decided (header) and §4 blocker-resolved dates **2026-06-19 → 2026-06-18** (owner-confirmed canonical; S7/0.8 dating). Closes the carried register date nit.

### Verified (fresh clone, container)
- Scaffold sanity test **PASS** (`1 passed`). Submodule pin **`0ec3060`** confirmed. `eol=lf` present; no installers in tree.

### Not touched
- The frozen pack. Read-only throughout; membership and manifest unchanged at **173**.

---

## [build-prep-0.8] — 2026-06-18 — A5: status sweep `*_PRE_FREEZE → *_FROZEN`, retire `_review_control/`, drop satisfied blocker B → **FREEZE v1.0.1**

Pre-freeze edits complete; pack **frozen** and tagged. Co-design entry (lives outside the hashed pack). Owner rule applied: SESSION_LOG + CHANGELOG are the authoritative record. Edits by Mervat; owner (Amr) committed/pushed/tagged. **Pack HEAD now `0ec3060` (tag `v1.0.1`)** (was `78c40d7`).

### Why
A5 is the freeze. With all pre-freeze content edits done (A1–A4 + freeze-state cleanup), the registry's retained blocker B condition was satisfied and the manifest could be regenerated. This batch enacts the freeze: relabel the governance-phase status pack-wide, remove stale scaffolding, clear the now-met blocker, regenerate, and tag.

### Changed (governed)
- **Status sweep — 126 replacements across 32 files** (exact whole-token, case-sensitive value-map; no blind replace):
  - `ACTIVE_PRE_FREEZE→ACTIVE_FROZEN`, `TESTING_ONLY_PRE_FREEZE→TESTING_ONLY_FROZEN`, `ACTIVE_INTERNAL_PRE_FREEZE→ACTIVE_INTERNAL_FROZEN`, `ACTIVE_NON_CALLABLE_PRE_FREEZE→ACTIVE_NON_CALLABLE_FROZEN`, `ACTIVE_POLICY_FIRST_PRE_FREEZE→ACTIVE_POLICY_FIRST_FROZEN`, `TESTING_ONLY_PRE_FREEZE_WITH_REGULATED_USE_BLOCK→TESTING_ONLY_FROZEN_WITH_REGULATED_USE_BLOCK`.
  - Header phase `pre_freeze_controlled` / `PRE_FREEZE_CONTROLLED → frozen_controlled` (lowercase normalized; fixes the 4 uppercase library headers).
  - Capability prefixes preserved (the prefix carries meaning; only the lifecycle marker flips).
- **`_review_control/` retired** — 28 files deleted (Blockers, DECISION_LOG, stale `FINAL_FREEZE_READINESS_*` / `PHASE13_*` verdicts, `.bak_phase11` cruft); `EXCLUDE_DEGOVERNED_DIRS` removed from `scripts/pack_validation/pack_excludes.py` (dead once the dir is gone). Recoverable via git history.
- **`freeze_blockers_retained`**: blocker B removed ("Manifest regeneration and final freeze-readiness check remain blocked until all pre-freeze content edits are complete" — condition met); **blocker A retained** ("K&S … product testing only; … regulated use" — standing scope constraint).
- **Manifest regenerated** (Linux/LF clone): membership unchanged at **173**; hashes updated for the swept files + `pack_excludes.py`.
- **Registry `status: pre_freeze_controlled → frozen_controlled`**; **git tag `v1.0.1`** applied at `0ec3060`.

### Held the line (NOT touched)
- **KS content-approval lifecycle.** `PRE_FREEZE_USER_REVIEW_REQUIRED` (29 occurrences; enum in 9 KS schemas + asset `approval_status`) left untouched — it is the regulated-use approval state, orthogonal to pack-freeze. Sweeping it would rewrite the enums and misrepresent testing-only content as approved (violates `validation_requirement` #3). See the freeze-status register.
- Designed PRODUCT_TESTING/FIELD_TRIAL operating baseline (owner option-3 territory) — unchanged.

### CRLF episode (Windows working tree)
- Owner's local `verify_manifest` first FAILed on **13 untouched text files** (RPT action_blocks, A01, A11, `action_block.schema.json`, `contract_request.schema.json`). Proven CR-only: each "actual" hash == the CRLF version of the committed LF content. The sweep force-wrote LF only on edited files; these were CRLF stragglers from a Windows checkout.
- **Installer fix:** added whole-tree **LF normalization** (Step 5), plus made it idempotent, self-skipping, and default-path so it runs in-repo with no clone. Local `verify` then **PASS 173**.
- Owner-env cure (recommended, not blocking): `git config core.autocrlf false`.

### Status
- Fresh clone of `0ec3060` (independent): registry `frozen_controlled`; `_review_control` 0; `EXCLUDE_DEGOVERNED` 0; blocker B 0 / A 1; residual swept tokens 0; `PRE_FREEZE_USER_REVIEW_REQUIRED` 29; committed `i/crlf` 0; **verify 173, smoke, harness all PASS.**
- Installer (out-of-pack): `apply_freeze_sweep.py`. LF `manifest.yaml` drop-in. Freeze-status register delivered as a co-design doc (outside the pack; migrates to `co-design/` in Phase B).

### Phase A — COMPLETE
A1 ✅ A2 ✅ A3 ✅ A4 ✅ A5 ✅ — pack frozen at **v1.0.1** (`0ec3060`). Next: Phase B (B1 build repo + `co-design/` → B2 `A16_Runtime_Target_Spec` → …), against the frozen pack as a versioned dependency.

---

## [build-prep-0.7] — 2026-06-18 — Pre-A5 freeze-state cleanup: de-govern `_review_control/` + correct README freeze status + manifest LF fix

Pre-freeze. Co-design entry (lives outside the hashed pack). Owner rule applied: **SESSION_LOG + CHANGELOG are the authoritative record; anything not stated there is cleanup.** Edits by Mervat; owner (Amr) committed/pushed. Pack HEAD now `78c40d7` (was `fb2b667` after A4).

### Why
The pack carried an **old, incorrect freeze conclusion** ("FREEZE-READY FOR PRODUCT_TESTING / FIELD_TRIAL BASELINE ONLY", dated 2026-06-13) that predates A1–A4, plus stale review scaffolding — none of it reflected in the authoritative SESSION_LOG/CHANGELOG (which state: pre-freeze, A5 pending, "don't call it frozen"). Per the owner rule, that's cleanup.

### Changed (governed-state cleanup only — no designed product content touched)
- `scripts/pack_validation/pack_excludes.py` — added `EXCLUDE_DEGOVERNED_DIRS = {"_review_control"}` to the shared exclude (honored by both generate + verify, so no false "extras"). **De-governs the entire `_review_control/` review-scaffolding directory (28 files)** — Blockers 1–10, DECISION_LOG, the stale `FINAL_FREEZE_READINESS_*` / `PHASE13_*` verdicts, and 3 `*.bak_phase11` cruft files. Files remain in-repo, ungoverned (no governed file references them — confirmed). Reversible.
- `README.md` — freeze STATUS corrected (reusing the pack's own prior BLOCKER7A wording): "FREEZE-READY…" / "is frozen as a PRODUCT_TESTING / FIELD_TRIAL baseline" → "CONTROLLED PRE-FREEZE — NO-FREEZE YET" / "under controlled pre-freeze review (NO-FREEZE YET); its declared scope is the PRODUCT_TESTING / FIELD_TRIAL architecture baseline." Designed scope description kept.
- Manifest regenerated → **201 → 173 files** (28 `_review_control/` entries dropped; `README.md` + `pack_excludes.py` hashes updated).

### Held the line (NOT touched — owner option-3 / re-architecture, not authorized)
- The **designed PRODUCT_TESTING/FIELD_TRIAL operating baseline** in `contracts/VALOR-contract-orch-doc.yaml` (`product_testing_field_trial_allowed: true` + siblings), `A04_5`, and `A12`. Cleaning a stale freeze *verdict* ≠ deleting designed contract fields. Installer asserts these are intact.

### CRLF episode (corrects/reinforces R1 discipline)
- Owner regenerated the manifest from the **Windows working tree** (CRLF), which baked CRLF hashes for LF-committed blobs → commit `561c2df` **PASSED local verify but FAILED fresh-clone verify** (12+ mismatches: action_blocks, contracts, registry vectors). Proven: e.g. `registry_validation_vectors.json` manifest-expected `3604cf6a` == the CRLF-converted hash; committed blob is LF (`76a2fa97`).
- Fixed by regenerating the manifest from a **clean LF clone** (Mervat, Linux) — reproducible PASS 173 across two independent clones — committed as `78c40d7`. **Lesson re-affirmed: never regenerate from the Windows working tree; generate from a fresh LF clone (or hand off to co-design on Linux).**

### Status
- Fresh clone of `78c40d7`: **verify PASS 173, smoke PASS, harness PASS.** CI green.
- `_review_control/`: 28 files on disk, 0 in manifest. README freeze claim gone. `PUBLIC_EXCERPT` still 0 pack-wide (A4 intact). Registry `status: pre_freeze_controlled` is now *accurate*.
- Installer (out-of-pack): `apply_freeze_cleanup.py`. Corrected manifest delivered as drop-in.

### Open (carried)
- **NEW latent wart — CRLF-blob files (next item, separate chat):** 8 text files are committed as CRLF blobs (consistent across clones, so they don't break the manifest, but violate `.gitattributes eol=lf`): `schemas/objects/work_package_schema.json`; `schemas/contracts/{export_result,report_result,workbook_export_result,doc_artifact_result,gantt_chart_result}.schema.json`; `smoke_test.py`; `scripts/pack_validation/run_vector_harness.py`. (`architecture_blueprint.png` is binary — leave it.) Renormalize to LF before freeze for a clean baseline.
- **A5 freeze mechanism (undefined):** no freeze script exists; freeze is a governance status transition. Decide: flip registry `pre_freeze_controlled` → a frozen status, git-tag `v1.0.1`, or both. Owner call — not to be invented.
- Owner-env fix: set `core.autocrlf false` + work from a fresh LF clone so local verify stops diverging from CI.

---

## [build-prep-0.6] — 2026-06-18 — A4: standards/anchor reconciliation + PUBLIC_EXCERPT cleanup (G-10 / G-11 · D-05 / D-06)

Pre-freeze. Co-design entry (lives outside the hashed pack). Edits by Mervat; owner (Amr) commits/pushes and regenerates the manifest from a fresh clone.

### Confirmed (no pack edit — the placeholders/drafts were never committed)
- **G-10 / D-05 — standards.** `standards/` holds exactly one base standard (`STD-CQV-BASE`, 16 reqs `CQV-REQ-001…016`, each with a `source_to_internal_mapping_ref`). All three bundles already exist (`BND-CQV-BASE`, `BND-CSV-ADDON`, `BND-CLEANROOM-ADDON`). **No parallel `STD-*` files exist; none to remove.** The seven drafted standards were co-design working drafts, never in the pack.
- **G-11 / D-06 — anchors.** The register (`external_references_v1.0.1.yaml`, `EXT-REFS-VALOR-KS-v1.0.1`) and the mapping (`source_to_internal_requirements_v1.0.1.yaml`) use **pure `EXT-<SOURCE>` / `EXT-<SOURCE>-<TOPIC>`** anchors across all 10 sources. **Zero `SRC-ANX…` anywhere in the pack** — nothing to remap. `NO_EXCERPTS` + `TESTING_*_NOT_APPROVED` discipline intact.

### Changed (the only pack edits in A4)
- `schemas/contracts/ks_citation_resolved.schema.json` — removed the unused `PUBLIC_EXCERPT` from the `excerpt_policy_applied` enum → `["METADATA_ONLY","INTERNAL_ONLY","NO_EXCERPTS"]`, matching the canonical DOC CitationSet (A04.5 §3.5). 858 → 841 bytes.
- `docs/architecture/A10_Security_Compliance_Arch_v1_0_1.md` §6.4 — dropped the `PUBLIC_EXCERPT` bullet **and added the missing `NO_EXCERPTS` bullet**, so A10 now lists `METADATA_ONLY / INTERNAL_ONLY / NO_EXCERPTS` (was `METADATA_ONLY / PUBLIC_EXCERPT / INTERNAL_ONLY` — both wrong: had the unused value, lacked the used one). 8593 → 8659 bytes.
- Manifest regenerated → **201 files** (no file added/removed; two hashes updated). Fresh-clone-emulation `verify_manifest.py` = **PASS 201**.

### Finding (corrects the audit)
- Audit C4-F6 / Phase-A plan said `PUBLIC_EXCERPT` "appears only in A10." **Undercount:** it was in **two** files, one a **schema enum** (`ks_citation_resolved`). Confirmed safe to remove — **no test vector or instance uses `PUBLIC_EXCERPT` as a value** (grep, pack-wide). A10 was also *missing* `NO_EXCERPTS`, the value every register source actually carries.

### Status
- **Three gates green** on the working tree **and** on a `git archive` normalized tree (fresh-clone emulation): verify **PASS 201**, smoke **PASS** (4 checks, 51 schemas), harness **PASS** (19 A pass + 1 skip · 7/7 B · 49 C registered). Only cross-regen manifest diff = self-referential `created_at_utc` + the two intended file hashes — **zero CRLF/normalization drift** (A1 trap absent).
- **Pending owner:** run `apply_a4.py` (kept out of the hashed pack), regenerate the manifest from a fresh LF clone (expect **PASS 201**), commit + push, confirm CI green.
- **One open confirm (G-10 fold):** "fold any genuinely-new governed requirement into `STD-CQV-BASE`" cannot be executed without the seven draft texts to diff against the 16 existing reqs. Audit C4-F1 already assessed them as duplicative. Owner to confirm we treat C4-F1 as settled (nothing to fold) **or** supply the drafts for a diff.
- Residual (non-blocking, from A3): `smoke_test.py`'s one hand-inlined report-vector ref — superseded by the harness registry; remove post-freeze.
- Next: **A5** (final regen → registry freeze-readiness check → owner freezes v1.0.1).

---

## [build-prep-0.5] — 2026-06-17 — A3: vector / CI harness (G-12 + G-20)

Pre-freeze. Co-design entry (lives outside the hashed pack). Edits by Mervat; owner (Amr) commits/pushes and regenerates the manifest from a fresh clone.

### Added
- `scripts/pack_validation/run_vector_harness.py` — vector-driven harness (pack tooling, under `scripts/`, LF). Routes all **31 vectors** by structure into three honest classes and runs the strongest assertion each class supports pre-engine:
  - Class A (4 schema-validation suites): validate each `instance` vs its declared `schema_ref`, assert verdict == `expected_result.valid` — **19 pass (positives + negatives), 0 fail, 1 legit skip**; `--strict-negative` also passes.
  - Class B (7 single-instance positives): validate vs conventionally-mapped schema — **7/7 pass**.
  - Class C (20 behavioral suites): load, count **49 cases**, cross-reference **every declared `action_type` vs the 39-action registry — all resolve**. Registered + checked, not faked green.
- Real `referencing`-based `$ref` registry keyed on each schema's `$id`; all **6** cross-file refs resolve.
- CI gates: `verify_manifest.py` (tracked hash/size **+ extras-detection**) and the harness, added to `.github/workflows/ci.yml` alongside the existing smoke test → **three ordered gates**.

### Changed
- `smoke_test.py` — schema glob widened to `*.schema.json` **|** `*_schema.json`, closing the 12-file `objects/` coverage hole (G-20b) in the in-CI script itself. Schema parse now covers **51/51**.
- Decision within scope: **widened the glob rather than renaming** `objects/*_schema.json` — a rename would ripple through every `$ref`, the registry vectors' `result_schema_ref`s, and the manifest right before freeze (higher risk, no value).
- Manifest regenerated → **201 files** (200 + harness). Fresh-clone `verify_manifest.py` = **PASS: 201 files**.

### Fixed
- **`valor://` custom scheme defeated relative-`$ref` resolution.** `urllib.parse.urljoin` (used by `referencing`) does not apply a base URI for unknown schemes, so relative refs (e.g. `task_schema.json`) were `Unresolvable`. Harness now rewrites every relative file-`$ref` to the target's absolute registered `$id` at load time. *Phase-B note:* the engine's validation layer (B2 / D-08) must do the same — real registry / absolute ids, not naive ref-following.

### Status
- All three gates green on the working tree **and** on a `git archive` normalized tree (fresh-clone emulation): verify **PASS 201**, smoke **PASS** (4 checks, 51 schemas), harness **PASS** (51/51 meta-validate · 7/7 B · 19 A +1 skip · 49 C registered). Only cross-regen manifest diff = self-referential `created_at_utc` header — **all file hashes identical, zero CRLF/normalization drift** (A1 trap absent).
- **Pending owner:** drop in the 3 files, regenerate manifest from a fresh LF clone (expect PASS 201), commit + push, confirm CI green.
- Residual (non-blocking): `smoke_test.py` keeps its one hand-inlined report-vector ref — works, **superseded** by the harness registry, left to avoid pre-freeze churn; remove post-freeze.
- Next: **A4** (standards reconciliation + `EXT-*` remap + `PUBLIC_EXCERPT` cleanup), then A5 (final regen → freeze-readiness → freeze v1.0.1).

---

## [build-prep-0.4] — 2026-06-17

### Added
- `apply.py` — one-shot A1 mode-rename tool (word-boundary `M1`/`M2` → `DESIGN`/`EXECUTION`, self-excluding, LF-safe). Build tooling, kept outside the hashed pack.
- `apply_a2.py` — A2 installer: writes `scripts/pack_validation/pack_excludes.py` and surgically patches both manifest scripts; self-verifying, LF-safe. Build tooling, kept outside the pack.
- **Pack:** `scripts/pack_validation/pack_excludes.py` — single shared exclude constant (dirs + suffixes, any-depth) for the manifest generator/verifier (G-19).

### Changed (pack — committed, pushed)
- **A1 / G-16 — mode rename DONE.** Renamed engine-authority mode **values** `M1`→`DESIGN`, `M2`→`EXECUTION` across 26 files (7 contracts, 2 schemas, 12 action_blocks, 4 docs, 1 registry vector). Word-boundary only; `MODE_VIOLATION`/`WRONG_MODE_FOR_COMMIT` and the blueprint PNG untouched. Frees `M1–M4` for the Phase-B runtime layer. Validated: 0 residual `M1`/`M2`; 51 schemas meta-validate draft-07; smoke `schemas.load`/`report.vectors`/`presets.bindings` PASS.
- **A2 / G-19 — integrity tooling DONE.** `generate_manifest.py` and `verify_manifest.py` now import one shared `should_exclude` (any-depth dirs + suffixes); verifier's `manifest_paths` loop-invariant hoisted out of the per-entry loop; verifier extras-detection aligned to the shared rule. Regression confirmed: stray `.pytest_cache/` + `.pyc` no longer false-FAIL.
- Manifest regenerated; fresh-clone `verify_manifest.py` = **PASS: 200 files**. Pack HEAD `c59fdee`.

### Fixed
- **CRLF/LF manifest mismatch (NEW finding).** First A1 push (`9109f4d`) generated the manifest from a Windows CRLF working tree while `.gitattributes` stores LF → all 26 edited files mismatched on a fresh clone (local verify passed, masking it). Repaired by regenerating from a fresh LF clone. Both apply scripts switched to `write_bytes` (LF on every OS). **Standing rules:** pack-editing tools write LF; regenerate the manifest from a fresh clone; trust fresh-clone verify over local.
- **Build-tool leak.** `apply_a2.py` was committed into the pack root (`2e8bbd1`) when a `Move-Item` failed silently; evicted in `c59fdee` (manifest back to 200). Reinforces D-01: build tools never live in the hashed pack.

### Status
- Phase A progress: **A1 ✅ · A2 ✅** · A3 (vector/CI harness, G-12+G-20) next · then A4 (standards/anchors + `PUBLIC_EXCERPT` cleanup) · then A5 (freeze-readiness → owner freezes v1.0.1).

---

## [build-prep-0.3] — 2026-06-16

### Added
- `VALOR_Audit_Report_v1.0.md` — full first-pass audit: four chunk findings notes (Foundation & Control, Core Engine, Contracts & Schemas, Remaining Specs & Standards) + consolidated build-readiness verdict.
- `VALOR_Build_Readiness_Gap_Assessment_v0.3.md` — post-audit reissue (20 gaps, 11 decisions).
- **G-19** — manifest generator/verifier exclude-set divergence (false-FAIL on `.pytest_cache`/`.pyc`; demonstrated live).
- **G-20** — test/validation tooling under-enforces the contract corpus (~29 of 31 vectors inert; `objects/*_schema.json` outside the smoke-test glob; cross-file `$ref` only stubbed; CI lacks extras-detection).

### Changed
- All TO-VERIFY gaps resolved to CONFIRMED/CLOSED: **G-04** (walking-skeleton path specified/catalogued), **G-05** (contracts complete — 39 actions, 0 mismatches; 51 valid draft-07 schemas), **G-06** (truth model complete; store constrained to append-only ledger + tombstoning), **G-08** (approval events modeled), **G-12** (CI scope pinned), **G-13** (determinism closed at pack; residual → D-08).
- **G-07** closed (identity deferral + soft-control stub + named integration point).
- **G-10** confirmed (one base standard `STD-CQV-BASE` + trigger-composed add-on bundles; the seven drafted standards largely duplicate this — do **not** add them as separate standards).
- **G-11** confirmed (real anchor scheme `EXT-<SOURCE>` / `EXT-<SOURCE>-<TOPIC>`; remap placeholders).
- **G-16** escalated DESIGN → confirmed **mode-name conflict** (pack enforces M1=Design / M2=Execution; co-design's M1–M4 must be renamed/re-mapped).
- **G-15** closed (full audit complete).

### Decided / Confirmed
- **D-04** confirmed (Python + JSON Schema **draft-07**, verified across all 51 schemas).
- **D-05** confirmed (fold into `STD-CQV-BASE` sections; CSV/cleanroom already exist as add-on bundles).
- **D-06** confirmed (adopt the existing `EXT-*` register scheme).
- **D-03** constrained (store must support an append-only ID ledger + tombstoning).
- **D-08** confirmed as the home for AI-call reproducibility (pack contains no AI layer).
- **D-10 / D-11** reinforced (`SELECTED_WP_SET` is an existing projection-only precedent for the M4 container; avoid `ALL_WPS`).

### Fixed (corrections to prior build-prep records)
- Corrected an earlier audit note: CI **does** verify the manifest via `smoke_test.py` (hash + size of tracked files) — but without extra-file detection.
- Corrected the "frozen v1.0.1" framing: the pack is `pre_freeze_controlled`, not frozen.

---

## [build-prep-0.2] — 2026-06-16

### Added
- System model recorded in the gap assessment: 3 layers (deterministic engine / AI narrative-only / multi-screen UI) and 4 co-design modes (M1 Advisory · M2 Execution Planning · M3 Implementation · M4 Project Container).
- G-16 (modes), G-17 (M2 vs CQV-plan labelling), G-18 (Project container).

### Decided
- **D-10** — multi-entity work handled by a **Project container (M4)** above the WP; WP stays single-entity / boundary-defended.

---

## [build-prep-0.1] — 2026-06-15

### Added
- `SESSION_LOG.md` — co-design continuity record (read-first / update-last).
- `CHANGELOG.md` — this file.
- `VALOR_Build_Readiness_Gap_Assessment_v0.1.md` — 15 gaps, 9 decisions; first partial-read audit.
- Seven CQV internal standards drafted (STD-CQV-MGT, -PEQ, -CUTIL, -BUTIL, -CAL, STD-CLEANROOM-CQ, STD-CSV-CQ) — staged, **not integrated** (superseded by G-10: do not add as separate standards).

---

## How entries are added

Each session, move closed items out of *Unreleased* into a dated, versioned release block:

```
## [build-prep-0.N] — YYYY-MM-DD
### Added / Changed / Decided / Removed / Fixed
- <entry referencing gap or decision IDs>
```

Keep entries terse and ID-referenced (G-##, D-##) so they cross-link to the gap assessment.
