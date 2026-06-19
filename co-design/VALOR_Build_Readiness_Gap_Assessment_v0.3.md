# Valor Architecture Pack — Build-Readiness Gap Assessment

**Working document v0.3** · Author: co-design sessions · Status: POST-AUDIT (full read complete)
**Purpose:** Identify everything the repo needs before system build begins. Owner fills Decision / Comment columns; co-design fills proposals.

> **Audit scope note (v0.3):** The full first-pass audit is **complete** — all four chunks read directly from a fresh clone (`Cyber-Mario1979/VALOR_Architecture_Pack` @ HEAD): Foundation & Control (A00, A01, manifest tooling, CI), Core Engine (A04.1/.2/.4/.5/.6), Contracts & Schemas (registry, 7 contracts, 51 schemas, 31 vectors, smoke_test — executed live), and Remaining Specs & Standards (A05–A11, A13, A14, STD-CQV-BASE, bundles, external-reference register). Findings and evidence are in **`VALOR_Audit_Report_v1.0.md`**. Every prior **TO VERIFY** row is now **CONFIRMED** or **CLOSED**; two new gaps (G-19, G-20) were found; one correction was recorded (the pack is *pre-freeze*, not frozen).

> **✅ DECISIONS FINALIZED (2026-06-16, owner: Amr):** All gaps/decisions accepted; the owner-decision cells in Table 2 are resolved (see each cell). Seven points locked live:
> 1. **G-16 mode rename APPROVED** — rename pack envelope `M1`/`M2` → `DESIGN`/`EXECUTION` pre-freeze; free `M1–M4` for runtime. Final scheme: lifecycle `ARCH`/`BUILD`; engine authority `DESIGN`/`EXECUTION`; runtime `M1 Advisory · M2 Delivery Plan · M3 WP Mode · M4 Project Mode`.
> 2. **G-04 = full thin vertical** (`stage→commit→plan→doc→export`, one WP/task/doc/export, PE-HIGH, BUILD mode, gates log-only).
> 3. **G-06 store** = file/git, single-user, **lock-aware write path from day one** (commit chokepoint + advisory lock); multi-user deferred as an extension.
> 4. **G-09/D-09** = `co-design/` directory in the build repo, outside any manifest.
> 5. **D-08 interface LOCKED** (versioned/hashed prompt, temp 0, schema-constrained JSON, refuse/accept loop, audit-logged prompt+input+output hashes); model = later spike.
> 6. **G-07** = defer crypto identity; role-context + audit logging now; **identity carried as a named milestone in the end-to-end plan** (owner condition).
> 7. **D-02/G-14 freeze ownership** = **we edit the pack pre-freeze; owner (Amr; Nexus = Amr) commits and freezes** ⇒ freeze-readiness is **Phase A** of the plan. (G-12 + G-20 = one combined CI/harness workstream.)

---

## How to use this document

1. Read each gap row. Add your note in **Owner Comment**.
2. For each decision row, enter your call in **Decision** (leave the recommendation intact for the record).
3. Accepted items become work items for the build-prep project.
4. Status tags: **CONFIRMED** (verified by direct read), **CLOSED** (resolved/answered — no further design needed before build), **DESIGN** (additive capability to design), **NEW** (surfaced by the audit).

---

## System Model (context for the gaps below)

Three-layer stack:
- **Layer 1 — Deterministic Python engine.** *Audit-confirmed: the pack IS this layer.* Inputs, outputs, validation, contracts, WP truth, invariants. Pure code; contains no AI component. Determinism is explicit in Planning/DOC/RPT/WP.
- **Layer 2 — AI layer.** Model the engine calls; output is a *proposal* through a **refuse/accept correction loop** (one silent retry; second failure → human). AI writes **narrative only**, bounded by CQV standards (constraints, not text). Lives entirely *outside* the pack (D-08).
- **Layer 3 — UI.** Multi-screen (Document Factory + others). Not yet designed.

Operating modes — **⚠ naming reconciliation required (see G-16).** The co-design model (M1 Advisory / M2 Execution Planning / M3 Implementation / M4 Project Container) **collides with the pack's existing, enforced modes**: the pack defines **M1 = Architecture/Design** and **M2 = Execution/Implementation** (envelope field `"mode": "M1|M2"`, `MODE_VIOLATION` enforced). The co-design must **rename or re-map** its modes; do not redefine the pack's M1/M2.

Governing principle: **AI freedom shrinks as stakes rise.** Human-in-the-loop in all modes.

---

## Table 1 — Gap Assessment

| ID | Gap | Category | Why it matters for build | Proposal | Priority | Tag | Owner Comment |
|----|-----|----------|--------------------------|----------|----------|-----|---------------|
| G-01 | No runtime / technology target spec | Buildability | Confirmed: A00/A01/A04.x specify *what* the system is, never *what it's built on*. | Write `A16_Runtime_Target_Spec` around the 3-layer stack (engine/AI/UI), WP store, contract enforcement, AI-call interface. | **P0** | CONFIRMED (open) | |
| G-02 | No defined BUILD / DEV operating mode | Governance vs velocity | Confirmed: gates (Stage/Validate/Commit/Apply/Finalize/Close) are mandatory; no dormant build mode. | Define a system BUILD mode where gates are **log-only / dormant** (D-07); document inert-vs-live. | **P0** | CONFIRMED (open) | |
| G-03 | Repo-vs-build seam undefined | Architecture | Manifest hashes the whole pack root recursively → collaboration files committed to root become governed assets. | Decide D-01; add `BUILD_STRATEGY.md`. Separate build repo recommended. | **P0** | CONFIRMED (open) | |
| G-04 | Walking skeleton / reference flow | Buildability | **CLOSED as a design gap:** full stage→commit→plan→apply→generate→stamp→export path is specified and catalogued with real action names. | Build the slice as the first milestone — start with `orch-wp` stage→commit, against the **PE-HIGH** worked example (the only domain with a shipped pool/profile/preset). | **P0** | CONFIRMED (path specified) | |
| G-05 | Contract completeness | Contracts | **CLOSED:** registry ↔ 7 contract bodies ↔ 51 draft-07 schemas ↔ action_blocks all align (39 actions, 0 mismatches); single-instance vectors validate. | Buildable on both sides. No further contract design needed. | **P1** | CONFIRMED (complete) | |
| G-06 | WP truth persistence | State | **CLOSED (design):** logical truth model complete; physical store deliberately unspecified but **constrained** to support an append-only ID ledger + tombstoning. | Choose store under D-03 honoring that constraint (file/git satisfies it; a plain mutable store does not). | **P1** | CONFIRMED | |
| G-07 | Identity / authorization | Security | **CLOSED:** A10 defers cryptographic identity (v0.1.x), uses declared-role **soft controls** as the stub, and names the identity-system integration point. | Implement role-context capture + audit logging; integrate identity later at the named point. | **P2** | CONFIRMED (closed) | |
| G-08 | Human approval / signature event | Boundary | **CLOSED:** A09 models approvals as governance **records** + confirmation capture + append-only audit events; e-signature execution stays external. | Implement confirmation/approval records + audit events; name the e-sign integration. | **P1** | CONFIRMED (closed) | |
| G-09 | Session-continuity method in repo | Collaboration | **CLOSED:** `SESSION_LOG.md` + read-first/update-last instruction stood up. | Keep it outside the hashed pack root (see G-03/D-09). | **P0** | CONFIRMED (done) | |
| G-10 | Seven drafted standards vs existing content | Content | **CONFIRMED overlap:** pack ships ONE base standard (`STD-CQV-BASE`, 16 reqs) + trigger-composed bundles (CQV-BASE/CSV-ADDON/CLEANROOM-ADDON). The seven largely duplicate this; PEQ/CUTIL/BUTIL/CAL belong in task pools/profiles, not standards. | **Do not add the seven as separate standards.** Fold any new requirements into `STD-CQV-BASE` sections; use existing add-on bundles for CSV/cleanroom (D-05). | **P1** | CONFIRMED | |
| G-11 | External-source anchor scheme | Content | **CONFIRMED:** real scheme is `EXT-<SOURCE>` / `EXT-<SOURCE>-<TOPIC>` (10 sources, NO_EXCERPTS, placeholder editions/dates). | Map co-design placeholders (`SRC-ANX15…`) to real `EXT-*` anchors (D-06); never invent a parallel scheme. | **P1** | CONFIRMED | |
| G-12 | CI / workflow purpose | Tooling | **CONFIRMED (precise scope):** CI runs `smoke_test.py` only = manifest verify (tracked-file hash/size) + schema **parse** + **2** report vectors + preset bindings. No extras-detection, no full vector suite, no non-report instance validation. | Wire `verify_manifest.py` (extras, post-G-19 fix) and the G-20 harness into CI. | **P1** | CONFIRMED | |
| G-13 | Determinism mechanism | Buildability | **CLOSED at pack level:** determinism explicit across Planning/DOC/RPT/WP; pack has no AI. Residual = reproducible AI call. | Specify the AI-call reproducibility (versioned prompts, fixed settings, refuse/accept) under **D-08**, outside the pack. | **P1** | CLOSED (pack) → D-08 | |
| G-14 | Versioning policy during build | Process | The pack is **pre-freeze**, not frozen (see D-02 correction). | Finish the freeze, then decide co-evolve policy (D-02); document in BUILD_STRATEGY. | **P1** | CONFIRMED | |
| G-15 | Full audit | Process | **CLOSED:** full read complete; see `VALOR_Audit_Report_v1.0.md`. | — | **P0** | CLOSED | |
| G-16 | Modes not in pack — **now a CONFLICT** | Capability + Governance | **Conflict confirmed:** pack already enforces M1=Design / M2=Execution; co-design's M1–M4 reuse those labels with different meaning and add M3/M4. | **DECIDED:** rename pack envelope `M1`/`M2` → `DESIGN`/`EXECUTION` (pre-freeze). Final scheme: lifecycle `ARCH`/`BUILD`; engine authority `DESIGN`/`EXECUTION`; runtime `M1 Advisory · M2 Delivery Plan · M3 WP Mode · M4 Project Mode` with per-mode AI latitude + output stamping. | **P1** | DESIGN (decided) | **DECIDED — see scheme.** |
| G-17 | M2 "execution planning ≠ CQV plan" labelling | Clarity | Doubly important now: the pack's M2 *is* execution. "Planning" is triple-overloaded (pack-M2 execution, co-design-M2 work-structure planning, M3 CQV plan). | **DECIDED:** distinct labels — `M2 Delivery Plan` (which WPs, how linked) vs `M3 WP Mode` / `WP-Tasks Planning` (within-WP) vs the CQV plan (a document output, not a mode). Resolve with the G-16 rename. | **P2** | DESIGN (decided) | **DECIDED.** |
| G-18 | No Project container above WP (multi-entity) | Capability + Architecture | Reinforced: `SELECTED_WP_SET` (Reporting) is an existing projection-only multi-WP precedent. | Add **Project container (M4)** composing single-entity WPs by context, projection/reference-only (D-11), using SELECTED_WP_SET semantics — **avoid `ALL_WPS`** (out of freeze scope). | **P1** | DESIGN | |
| G-19 | Manifest generator/verifier exclude divergence | Tooling | **NEW:** `generate_manifest.py` and `verify_manifest.py` use different ignore sets/depths/suffixes → a `.pytest_cache/` or stray `.pyc` makes the verifier FAIL with false "extra files" (demonstrated live). | Hoist a single shared exclude constant (dirs + suffixes, any-depth) used by both; fix the verifier loop-scope smell. | **P2** | NEW | |
| G-20 | Test/validation tooling under-enforces the corpus | Tooling | **NEW:** ~29 of 31 vectors are inert (negative/e2e/ks/governance/registry/security never run); 12 `objects/*_schema.json` dodge the smoke-test glob; cross-file `$ref` only stubbed for one case. | Build a vector-driven harness (run all suites, validate cases vs declared `schema_ref`, assert pass/fail); normalise schema filenames or widen the glob; configure a `$ref` registry. | **P1** | NEW | |

---

## Table 2 — Decisions Needed (Owner)

| ID | Decision | Options / considerations | Recommendation | Decision (Owner) |
|----|----------|--------------------------|----------------|------------------|
| D-01 | Build in this repo, or separate build repo with pack as dependency? | **Audit evidence:** manifest hashes the whole root recursively (199 files), so anything committed to root becomes a governed asset — directly contradicting SESSION_LOG's "no manifest hash" claim. | **Separate build repo**, pack as versioned dependency (keeps the frozen pack pristine; collaboration files non-hashed). | **DECIDED: separate build repo; pack as versioned dependency.** |
| D-02 | Freeze pack at v1.0.1 during build, or co-evolve? | **Correction:** the pack is `pre_freeze_controlled` with retained freeze blockers (registry + A04.x/A05–A08), **not frozen**. Mixed status (A00/A01/A09/A10/A11/A14 are `released`). | **Finish the freeze first** (partly the pack's own open task), then freeze at v1.0.1 and batch changes into a deliberate v1.1. Stop calling v1.0.1 "frozen." | **DECIDED: close freeze blockers first (Phase A, we edit pre-freeze; owner commits), then freeze v1.0.1; batch larger changes into v1.1.0.** |
| D-03 | WP truth persistence model | **Constraint surfaced:** the store must support an **append-only ID ledger + tombstoning** (A04.2 §4). | **File/git-based** initially — satisfies the append-only/tombstone constraint with max auditability, low infra. | **DECIDED: file/git store; write path lock-aware from day one (commit chokepoint + advisory lock); multi-user concurrency deferred as an extension.** |
| D-04 | Runtime / language stack | **Confirmed:** `requirements.txt` = pyyaml + jsonschema; **all 51 schemas are draft-07.** | **Python + JSON Schema draft-07**, explicit contract-validation layer at every boundary. **(CONFIRMED by audit.)** | **DECIDED: Python + JSON Schema draft-07; contract validation at every boundary.** |
| D-05 | Seven standards: separate files or folded into `STD-CQV-BASE`? | **Confirmed:** pack = one base standard (sections) + CSV/cleanroom **add-on bundles** (already exist). | **Fold into `STD-CQV-BASE` as `CQV-REQ-###` sections; use existing add-on bundles for CSV/cleanroom. Do not add seven parallel STD files.** **(CONFIRMED.)** | **DECIDED: fold into `STD-CQV-BASE`; no parallel STD files.** |
| D-06 | External-source anchor scheme | **Confirmed:** register scheme is `EXT-<SOURCE>` + `EXT-<SOURCE>-<TOPIC>` TOPIC anchors. | **Adopt the existing `EXT-*` register scheme**; map placeholders; never invent a parallel one. **(CONFIRMED.)** | **DECIDED: adopt existing `EXT-*` scheme; map old placeholders to it.** |
| D-07 | BUILD-mode gate behavior | Off / log-only / on-with-override. | **Log-only in BUILD** — observe and record, never block. | **DECIDED: log-only in BUILD (record gate result, never block development).** |
| D-08 | Agent/LLM layer | **Confirmed:** the pack contains no AI; determinism is engine-native. The AI-call reproducibility lives here. | Defer model choice; **specify the interface now** (prompt = versioned asset, deterministic settings, refuse/accept contract). | **DECIDED (interface): versioned/hashed prompt, temp 0, schema-constrained JSON, refuse/accept loop, audit-logged prompt+input+output hashes. Model selection = later spike (needs discussion).** |
| D-09 | Collaboration setup | Project + `SESSION_LOG.md`. Must live **outside** the hashed pack root (D-01). | **Claude Project + `SESSION_LOG.md`** in the build repo (non-hashed); owner commits, co-design reads/writes through owner. | **DECIDED: Project + `co-design/` directory in the build repo, outside any manifest.** |
| D-10 | Multi-entity: richer WP vs Project container | (A) multi-entity WP blurs the boundary; (B) Project layer composes single-entity WPs. | **(B) Project container as M4 — DECIDED (session 2).** Reinforced: `SELECTED_WP_SET` is an existing projection-only precedent. | **DECIDED: B (Project container, M4 = Project Mode, WPs as sub-entities).** |
| D-11 | Does the Project container own truth? | Owns rollup metadata, or pure reference shell. | **Minimal context metadata + references only; projection-only (like Reporting/INV-09). Compose via SELECTED_WP_SET semantics; avoid `ALL_WPS`.** | **DECIDED: no truth ownership; light metadata + references only (projection-only).** |
| D-12 | Staged-set editability: can a user amend a staged task set, and what changes after commit? | `STAGED` = prepared for review, **not committed**, no IDs allocated (A04_1 §4.1/§4.3); post-commit `task_id` immutable, IDs append-only / never reused, removals tombstoned (A04_2 §4). | Free amend while STAGED; after commit, changes are append-only only. | **DECIDED: free amend in STAGED (no gate beyond GATE-Commit) — insert/reorder/drop candidates; post-commit changes are append-only — add new task (new ID) / `WP_UPDATE_TASK_FIELDS` / tombstone; no in-place insert; IDs immutable & never reused.** |
| D-13 | Does the M4 Project container have gates? | Container owns no truth (D-10/D-11). Truth gates (Stage/Commit/Plan/Apply) exist only to write WP truth; the consolidated plan is a projection over `SELECTED_WP_SET` (Projection Contract §1; INV-09). | No truth gates on the container; per-WP gates run inside each WP (M3); keep the projection scope-bound. | **DECIDED: M4 container has NO truth-mutation gates (extends D-10/D-11, projection-only); consolidated plan = projection over `SELECTED_WP_SET`, per-WP gates run in M3; sole control = scope-bound to an explicit selected set (`ALL_WPS` refused/bounded, R3).** |

---

## Recommendations (priority order, post-audit)

1. **Reconcile the two unblocking decisions: repo placement (D-01) and the mode-name conflict (G-16).** These shape the most downstream work; the mode conflict is now a hard blocker, not a design nicety.
2. **Define BUILD mode (G-02, D-07)** — governance present, dormant, log-only.
3. **Write the runtime target spec A16 (G-01, G-06, G-13→D-08, D-03, D-04)** around the 3-layer stack. Biggest buildability gap.
4. **Fix the integrity tooling (G-19) and stand up the test harness + CI enforcement (G-20).** Cheap, high-leverage; makes every later step verifiable.
5. **Walking skeleton (G-04).** One vertical slice (`orch-wp` stage→commit, PE-HIGH worked example) proving a contract path end to end. First real build milestone.
6. **Design the mode model (G-16/G-17, renamed) and the Project container (G-18, D-10/D-11)** — additive; don't disturb the WP core.
7. **Reconcile the standards last (G-10/G-11, D-05/D-06).** Fold into `STD-CQV-BASE` + existing add-on bundles; remap anchors to `EXT-*`. Don't add parallel STD files.

**Still NOT recommended:** adding more governance documents. The pack's governance is strong and confirmed. The work is the *build layer*, not more rulebook.

---

## Change Log (this document)

| Date | Session | Change |
|------|---------|--------|
| 2026-06-15 | 1 | First draft from partial-read audit; 15 gaps, 9 decisions. |
| 2026-06-16 | 2 | Added system model (3 layers, 4 modes); G-16/G-17/G-18; D-10 (DECIDED), D-11. |
| 2026-06-16 | 3 | **Post-audit v0.3.** Full read complete (see `VALOR_Audit_Report_v1.0.md`). All TO-VERIFY → CONFIRMED/CLOSED (G-04/05/06/08/12/13). G-07/G-08 closed; G-10/G-11 confirmed with concrete scheme; G-16 escalated to a confirmed mode-name **conflict**. Added **G-19** (integrity-tooling bug) and **G-20** (test/CI under-enforcement). Corrected D-02 (pack is *pre-freeze*, not frozen). Confirmed D-04/D-05/D-06; constrained D-03; reinforced D-10/D-11. |

**Next session expected (decisions FINALIZED — build the plan):**
1. **Phase A — pack → freeze-readiness** (we edit pre-freeze; owner commits): mode rename `M1/M2`→`DESIGN/EXECUTION` (G-16) → integrity-tooling fix (G-19) + vector/CI harness (G-12+G-20) → standards reconciliation into `STD-CQV-BASE` + `EXT-*` remap (G-10/G-11) → close freeze blockers → **freeze v1.0.1**.
2. **Phase B — build workflow** (against the frozen pack as dependency): build repo + `co-design/` (D-01/D-09) → `A16_Runtime_Target_Spec` (G-01) → BUILD/ARCH + M1–M4 mode model (G-16/G-17) → full-vertical walking skeleton (G-04, PE-HIGH) → named Identity-integration milestone (G-07).
3. Deliverables: `PHASE_A_FREEZE_READINESS_PLAN.md` + `PHASE_B_BUILD_WORKFLOW_PLAN.md` (or combined `VALOR_BUILD_PLAN.md`).
