# Phase B — Build Workflow Plan

*Part of VALOR phasing — see `BUILD_STRATEGY.md` §0.*

**Status:** DRAFT for owner review · **precondition now MET** · **Updated:** 2026-06-18 · **Author:** co-design (Mervat)
**Baseline:** Gap Assessment v0.3 + Audit Report v1.0 (decisions FINALIZED 2026-06-16, owner: Amr)
**Precondition:** **Phase A complete** — pack **frozen at v1.0.1** (HEAD **`0ec3060`**, registry `frozen_controlled`; fresh-clone verify 173 / smoke / harness PASS). Phase B builds against that frozen pack as a **versioned dependency**; the pack stays pristine.

> **Principle carried throughout:** *Humans Decide; Valor Assists.* The pack is **Layer 1** (the deterministic engine). Everything in Phase B is **additive and external** to the pack — the AI layer and UI live entirely outside it.

---

## The system being built (context)

Three-layer stack:
- **Layer 1 — Deterministic Python engine.** *The frozen pack is this layer.* Contracts, schemas, WP truth, invariants. No AI inside.
- **Layer 2 — AI layer.** Narrative-only proposals through a refuse/accept loop, bounded by CQV standards as *constraints, not text*. Lives outside the pack.
- **Layer 3 — UI.** Multi-screen (Document Factory + others). Not yet designed.

Governing principle: **AI freedom shrinks as stakes rise.** Human-in-the-loop in all modes.

---

## Work items (sequenced)

### B1 — Stand up build repo + `co-design/` *(D-01 / D-09)*
The pack manifest hashes the whole root recursively (**173 governed files at frozen v1.0.1**), so anything in root becomes a governed asset. Collaboration files must live **outside** the hashed pack.
- Create a **separate build repo**; pin the frozen pack **v1.0.1 (`0ec3060`)** as a **versioned dependency** (not vendored into a hashed root).
- Add a **`co-design/` directory** in the build repo, **outside any manifest**. Migrate `SESSION_LOG.md`, `CHANGELOG.md`, the gap assessment, the audit report, **and `VALOR_Freeze_Status_Register.md`** here.
- Add `BUILD_STRATEGY.md` documenting the repo seam, the dependency pin, and the co-evolve policy (batch larger pack changes into a deliberate **v1.1.0**).
- **Exit:** build repo exists; pack consumed as a pinned dependency; collaboration files (incl. the freeze-status register) non-hashed.

### B2 — `A16_Runtime_Target_Spec` *(G-01 — biggest buildability gap)*
The pack specifies *what* the system is, never *what it's built on*. A16 fills that, around the 3-layer stack:
- **Stack (D-04):** Python + JSON Schema **draft-07**; explicit contract-validation layer at **every boundary**.
- **WP store (G-06 / D-03):** **file/git**, satisfying the mandated **append-only ID ledger + tombstoning** (A04.2 §4). **Lock-aware write path from day one** — single commit chokepoint + advisory lock. **Multi-user concurrency deferred as an extension, not a rewrite.**
- **LLM interface (D-08 — LOCKED):** prompt = **versioned/hashed asset**; **temp 0**; **schema-constrained JSON** output; **refuse/accept loop** (1 silent retry → 2nd failure escalates to human); audit-logged **prompt-version + input-hash + output-hash**. **Model selection = a later spike** (open — see Open Items).
- **Contract enforcement:** map each engine boundary to its contract action + `result_schema_ref`; validation is fail-closed.
- **Exit:** A16 specifies engine/AI/UI seams, the store, and the locked AI-call interface concretely enough to build against.

### B3 — BUILD mode (gates log-only) *(G-02 / D-07)*
The pack's gates (Stage/Commit/Plan/Apply/Export) are mandatory; there is no dormant build mode.
- Define a system **BUILD mode** where gates are **log-only / dormant** — record the gate result, **never block** development.
- Document inert-vs-live behavior so the same path can later run gated in production.
- **Exit:** BUILD mode defined; gate outcomes logged, not enforced, during build.

### B4 — Mode model *(G-16 / G-17)*
With the pack's engine axis renamed to `DESIGN`/`EXECUTION` (Phase A), the runtime layer is free to define modes **without collision**. Keep the two axes strictly separate.
- **Lifecycle axis:** `ARCH` (design the system) / `BUILD` (build the product).
- **Engine-authority axis:** `DESIGN` / `EXECUTION` (the renamed pack field — do not redefine).
- **Runtime modes:** `M1 Advisory` · `M2 Delivery Plan` (which WPs, how linked) · `M3 WP Mode` (within-WP task execution) · `M4 Project Mode` (projects with WPs as sub-entities).
- **Per-mode AI latitude + output stamping:** latitude shrinks M1→M3; every output stamped with mode + provenance.
- **Label discipline (G-17):** `M2 Delivery Plan` ≠ `M3 WP-Tasks Planning` ≠ the **CQV plan** (a *document output*, not a mode). Keep the three distinct in all copy.
- **Exit:** mode model documented with both axes, runtime M1–M4, per-mode latitude, and disambiguated labels.

### B5 — Project container (M4) *(G-18 / D-10 / D-11)*
- Add a **Project container** composing **single-entity WPs by context**, using **`SELECTED_WP_SET`** semantics (the existing projection-only multi-WP precedent in Reporting, INV-09).
- **Projection/reference-only:** light context metadata + references, **no truth ownership** (never correct/overwrite/infer/mutate WP truth).
- **Avoid `ALL_WPS`** — it is out of freeze scope; compose explicitly selected WPs only.
- **Exit:** M4 composes selected WPs as a projection shell; WP stays the single-entity, boundary-defended source of truth.

### B6 — Walking skeleton *(G-04 — first real build milestone, PE-HIGH)*
Prove the path runs end-to-end, thin but **full vertical**.
- **Slice:** `stage → commit → plan → doc → export` — **one WP / one task / one doc / one export**.
- **Domain:** **PE-HIGH** — the only domain with a shipped pool/profile/preset (`TP/PROF/PS-PE-HIGH`); it is the only end-to-end-exercisable surface today (confirmed again by the A3 harness, which runs one domain).
- **Start at the root:** `VALOR-contract-orch-wp` stage→commit (the truth-owning root every other path depends on), then extend through plan/doc/export using the catalogued real action names (`PLAN_GENERATE_PROPOSAL`, `WP_APPLY_PLAN_PROPOSAL`, `DOC_GENERATE_DRAFT`/`DOC_FINALIZE_ARTIFACT`, `RPT_GENERATE_*`).
- **Priority:** PE-HIGH = **PE-HIGH effort**; **BUILD mode** with gates **log-only**.
- **Depends on:** B2 (runtime spec), B3 (BUILD mode), B4 (at least minimal mode handling).
- **Exit:** a thin vertical slice runs the full contract path against PE-HIGH, gates logging only.

### B7 — Identity-integration milestone *(G-07 — owner condition: preserve, don't forget)*
- **Now:** implement role-context capture + audit logging (the soft-control stub already specified in A10 §7 / A09 §6.2). Per **D-14** this is *soft only*: capture the declared role (audited), stamp it on every output, and warn-with-ack a sensitive (`confirm:true`) action that carries no declared role. **No** role→action authority map and **no** real-authority validation at this stage.
- **Deferred but NAMED — `M-IDENTITY` (cryptographic identity):** cryptographic identity must appear as an explicit, named milestone in the end-to-end plan and integrate at the point the pack already names. This is an owner condition — it must not silently disappear.
- **Exit:** soft controls live; crypto-identity milestone present and named in the plan timeline.

#### `M-IDENTITY` — Cryptographic identity (NAMED, deferred — do not drop)
The post-Phase-B identity milestone, carried per the owner condition (G-07) and D-14:
- **Integration seam (pack-named):** A09 §6.2 — *"the system stores who approved, but it does not validate real-world authority unless integrated with identity systems."* That clause is the plug-in point; A10 §3.2/§7 is the deferral it lifts.
- **Schema seam (already cut):** the frozen `contract_request` `actor` block permits `{role, name}` with `additionalProperties:true`, so a verified `actor.id` validates **today** — M-IDENTITY fills `actor.id` and flips `identity_verified` true with **zero pack/schema change**.
- **Scope:** verified actor identity replacing/augmenting declared-role soft controls; this is where a role→action authority map (D-14 Option B) and real-authority validation land, if adopted.
- **Status:** named, not scheduled. Sequenced after Phase-B exit; not an exit blocker.

---

## Dependency order

```
B1 (repo + dependency)
  └─> B2 (A16 runtime spec) ──┬─> B3 (BUILD mode) ──┐
                              ├─> B4 (mode model) ──┼─> B6 (walking skeleton, PE-HIGH)
                              └─> B5 (project M4) ──┘        │
B7 (identity: soft-controls now + NAMED crypto milestone) ───┘  (carried across the whole plan)
```
B5 is additive and may run parallel to or after B6. B7 runs as a thread across the phase: soft controls early, the crypto milestone carried as a named, non-droppable item.

---

## Phase-B exit criteria

1. **B1:** build repo live; frozen pack pinned as a versioned dependency; `co-design/` non-hashed (incl. freeze-status register).
2. **B2:** `A16_Runtime_Target_Spec` covers stack, lock-aware file/git store, and the locked LLM interface.
3. **B3:** BUILD mode defined; gates log-only.
4. **B4:** mode model documented — ARCH/BUILD × DESIGN/EXECUTION, runtime M1–M4, per-mode latitude, disambiguated labels.
5. **B5:** M4 Project container = projection-only over SELECTED_WP_SET; no truth ownership.
6. **B6:** full thin vertical PE-HIGH slice runs stage→commit→plan→doc→export, gates log-only.
7. **B7:** soft-control identity live (D-14, Option A — capture + stamp + warn-with-ack, no authority map); cryptographic-identity milestone **`M-IDENTITY`** named in the plan timeline (integrates at A09 §6.2; fills the already-cut `actor.id` seam).

---

## Open items (need owner discussion, not blockers)

- **O1 — LLM model selection (D-08).** Interface is locked; the *model* is a deferred spike. Needs a discussion to scope (candidate models, eval criteria, cost/latency, hosting). Flag for a dedicated session.
- **O2 — UI (Layer 3).** Multi-screen Document Factory + others — **not designed**. Out of the walking-skeleton scope; needs its own design pass when ready.
- **O3 — Multi-user concurrency.** Deferred as an extension; the lock-aware path (B2) keeps it from becoming a rewrite. Revisit after the skeleton.
- **O4 — Carried non-blockers from Phase A.** (a) Owner-env cure for the recurring CRLF gremlin: `git config core.autocrlf false` in the repo. **APPLIED (build-prep-0.18): owner ran it in the working tree; doc half in BUILD_STRATEGY §5; O4(a) CLOSED.** (b) 3 KS schemas with no trailing newline (cosmetic, `i/none`). Neither blocks Phase B; clear opportunistically.

---

## Risks & cautions

- **R1 — Mode collision reintroduced.** The whole reason Phase A renamed the engine axis. Keep runtime `M1–M4` and engine `DESIGN`/`EXECUTION` strictly separate in code and copy (B4).
- **R2 — AI layer creeping into the pack.** Layer 2 lives entirely outside the frozen pack. The pack stays pure Layer 1; the AI call's reproducibility is a B2/D-08 concern, not a pack edit.
- **R3 — Boundary erosion at M4.** The Project container is a projection shell. Any drift toward truth ownership or `ALL_WPS` rollups violates D-11 / INV-09 — guard it.
- **R4 — Single live domain.** The skeleton can only run PE-HIGH today. New domains need their own governed pool/profile/preset before they're exercisable — sequence accordingly.
- **R5 — Blocker A is permanent scope.** The retained freeze-blocker A (K&S content testing-only / regulated-use gated) and `PRE_FREEZE_USER_REVIEW_REQUIRED` survive the freeze by design. Phase B must not let the AI/standards work imply approved regulated basis (Freeze-Status Register §2/§4).
