# Phase C — Build-Out Plan

*Part of VALOR phasing — see `BUILD_STRATEGY.md` §0.*

**Status:** APPROVED (owner: Amr, 2026-06-21) · **Updated:** 2026-06-21 · **Author:** co-design (Mervat)
**Baseline:** Phase B **at EXIT** — B1–B7 landed (build `0.3.0`); Gap Assessment v0.3 + Audit Report v1.0; decisions D-01…D-14.
**Precondition:** **Phase B complete.** The runnable build layer (`src/valor_build/`) runs **one** vertical (PE-HIGH, M3·BUILD·EXECUTION) end-to-end with soft-control identity. Pack stays **frozen at v1.0.1 (`0ec3060`)**; Phase C is **additive and external** to the pack (no pack edits — new scope beyond the pack is **Phase E**, not here).

> **What Phase C is.** Phase B proved the spine *runs* — one dish, cooked start to finish. Phase C fills out the whole menu the frozen pack **already defines**: the full CQV scope (all active actions, all side-effect classes, all four runtime modes), then the two stubbed layers (the real AI model, the UI), then multi-user. The output is a **complete, usable single-then-multi-user product** built on the proven spine. *Humans Decide; Valor Assists* governs throughout. **Pack untouched.**

---

## The four Build-Out milestones (the celebration is C1)

Owner's roadmap, in order. Each is a milestone to be **hit and named**.

```
C1 · Engine complete  🎉   ──>   C2 · AI integration   ──>   C3 · UI complete   ──>   C4 · Multi-user
   (CELEBRATE HERE)                  complete                                            complete
```

Linear by owner decision: the **engine is finished first** (single-user, all CQV scope, identity included), *then* AI, *then* UI, *then* multi-user is added onto the proven single-user base — last, right before Phase D testing.

---

## The stack at Phase-C entry (what's real vs. stubbed)

- **Layer 1 — deterministic engine (frozen pack).** ✅ Done. Untouched in Phase C.
- **Layer 2 — AI layer.** ◐ *Interface* locked + runnable (D-08) with a **deterministic stub model**. The **real model is unselected** → **C2**.
- **Layer 3 — UI.** ✗ Not designed → **C3**.
- **Identity / authorization.** ◐ Soft controls live (B7/D-14). **Verified identity deferred** (`M-IDENTITY`) → folded into **C1**.
- **Action × class × mode coverage.** ◐ One path proven (a handful of actions, mostly `MUTATES_TRUTH`, **M3 only**). The full surface is unbuilt → folded into **C1**.
- **Concurrency.** ◐ Write path is lock-aware (single commit chokepoint + advisory lock). **True multi-user deferred** (D-03) → **C4**.
- **Hygiene.** Carried non-blockers → cleared first inside **C1**.

### The CQV surface C1 must cover (verbatim from the pack at `0ec3060`)
- **39 actions across 7 contracts.** By status: **23 ACTIVE + 4 ACTIVE-INTERNAL + 12 TESTING-ONLY**. C1 drives the **27 active**; the 12 testing-only stay behind `PRODUCT_TESTING_ONLY` (R5).
- **5 side-effect classes:** 14 `READ_ONLY` · 10 `VALIDATE_ONLY` · 8 `MUTATES_TRUTH` · 6 `GENERATES_ARTIFACT` · 1 `STAGE_ONLY`. The B6 slice exercised mostly the `MUTATES_TRUTH` write path; the other four are not yet driven end-to-end.
- **4 runtime modes (A18):** M1 Advisory (read/validate, 24 actions) · M2 Delivery Plan (proposal over a WP set) · M3 WP Mode (the only truth-writer) · M4 Project Mode (projection). The skeleton drives **M3 only**.
- **One preset.** The pack defines exactly **one** preset/profile/task-pool: `PS-PE-HIGH`. There are **no other effort classes** at v1.0.1 — additional presets would be a **pack v1.1.0** matter (Phase E), out of scope here. C1 covers the full surface *over this single preset*.
- A16 §4 already intends the validation layer to **load actions/schemas dynamically from the registry** — so coverage is *additive by pattern*, not a rewrite.

---

## Work items (sequenced)

### C1 — Engine complete 🎉  *(the celebration milestone — single-user Python engine, full CQV scope)*
Finish the Python engine so it performs **all** the CQV scope the frozen pack already defines, for **one user**, with identity wired in — ready for the AI and UI layers to plug into. Three sub-steps, in order:

1. **Hygiene & reconciliation (clean baseline first).** Clear the carried non-blockers so everything later is verifiable against a clean state: gate doc-reconcile (the `6→5` canonical-gate shorthand), schema-count `52/51` (1-file delta; `documents/index.json` carries no `$id`), `git config core.autocrlf false` env cure, G-10 fold confirmation, M4-reachability tighten decision. **Doc/config only.** (KS-newline cosmetics are re-homed to a future pack v1.1.0 batch — Phase E — never a one-off pack edit.)
2. **Full coverage — vertical slice → whole surface.** Generalize the proven B6 path to the full surface above: drive all **27 active actions / 7 contracts** through the dynamic registry-load path (A16 §4) with real enforcement; exercise **all five side-effect classes** end-to-end (each with its distinct handling — staging, confirmation, artifact generation); **drive all four modes M1–M4**, not just M3, with class-based reach enforced per A18 §2 (M1 reaches no truth; M3 is the sole truth-writer; M4 projects). Single preset `PS-PE-HIGH`. No new presets; no contract changes.
3. **Identity / login (the `M-IDENTITY` milestone, backend).** Lift the A10 §3.2/§7 deferral at the pack-named A09 §6.2 seam: integrate a real identity provider, populate the **already-cut** `actor.id` seam (frozen envelope permits it — zero pack/schema change), flip `identity_verified` true, validate real-world authority for sensitive actions, and wire the A10 §8 security audit events. **Single-user.** The D-14 Option-B role→action map stays an **open owner decision** (OC-2) — soft controls hold until decided; do not silently install hard RBAC (R6).

- **Depends on:** B6/B7 (landed). **Exit:** the engine performs **every active action across all five side-effect classes and all four runtime modes** for a single user; identity verified (`identity_verified` true) at the pack-named seam; interface + pack contract unchanged; testing-only set stays stamped (R5). **→ 🎉 CELEBRATE: the engine is complete.**

### C2 — AI integration complete  *(D-08 — realize Layer 2 behind the locked interface)*
Make the locked AI interface real without changing its contract.
- **Model selection spike:** candidate models, eval criteria, cost/latency/hosting (self-host vs API), data-handling constraints (A10 non-disclosure).
- **Determinism under a real model:** validate the temp-0 / schema-constrained-JSON / refuse-accept loop holds; audit prompt-version + input/output hashes against real outputs.
- **Narrative-only boundary (A10 §2/§4):** CQV standards bound the proposal; the model writes narrative only, never invents compliance facts.
- **Prompt-asset discipline:** versioned/hashed prompt assets managed as real artifacts.
- **Depends on:** C1 (a complete engine for the model to drive). **Exit:** a selected model runs the D-08 loop end-to-end across the covered action surface with determinism + audit intact; interface contract unchanged. **→ milestone: AI integration complete.**

### C3 — UI complete  *(Layer 3 — the screens, over the now-real lower layers)*
The multi-screen UI, designed against a complete engine + real model.
- **Per-mode surfaces:** M1 Advisory · M2 Delivery Plan · M3 WP Mode · M4 Project Mode — each with its latitude and **label discipline (G-17)** preserved.
- **Document Factory** + the **M4 projection presentation surface**.
- **Confirmation / gate UX:** the always-live human confirmation gate (A17 §4) and BUILD `WOULD_BLOCK` visibility, surfaced honestly.
- **Identity & stamp visibility:** role-context entry, `actor`/`identity_verified` display, output-stamp + `PRODUCT_TESTING_ONLY` surfacing (R5).
- **Depends on:** C1 (engine drives the modes the UI surfaces) + C2 (model behavior to present). **Exit:** a UI covering the M1–M4 surfaces, the Document Factory, and the confirmation/audit/identity surfaces, consistent with A16–A18; nothing implies authority the engine hasn't earned (R7). **→ milestone: UI complete.**

### C4 — Multi-user complete  *(D-03 — concurrency, added onto the proven single-user product)*
The deferred concurrency extension; the B2 lock-aware path keeps it an extension, not a rewrite. Added **last** in Build-Out — on a proven single-user base — because concurrency bugs only surface under contention and the first testing round (Phase D) is the owner, solo.
- **True concurrency** on the single commit chokepoint: advisory → real locking, conflict detection/resolution, the append-only ledger under concurrent writers.
- **Branching/merge** alignment with A09 governance (branch create/freeze, conflict-resolution events).
- **Depends on:** C1 (complete single-user engine) + C3 (UI surfaces to expose conflict/lock state). **Exit:** concurrent writers cannot corrupt WP truth; conflicts surfaced and resolved per A09; ID-ledger integrity holds under contention. **→ milestone: Multi-user complete. Phase C done; hand to Phase D.**

---

## Dependency order

```
C1 Engine complete 🎉  ──>  C2 AI integration  ──>  C3 UI complete  ──>  C4 Multi-user  ──>  (Phase D — Stabilization)
 hygiene → coverage → identity        (real model)        (M1–M4 + Doc Factory)    (concurrency on the proven base)
```

Linear, owner-decided (resolves OC-3): engine first and complete, then AI, then UI, then multi-user last.

---

## Phase-C exit criteria (= the four milestones)

1. **C1 — Engine complete 🎉:** every active action across all five side-effect classes and all four modes runs for a single user; identity verified at the A09 §6.2 seam; pack/contract unchanged; testing-only stamped. *Celebrate.*
2. **C2 — AI integration complete:** a selected model runs the locked D-08 loop across the covered surface with determinism + audit intact.
3. **C3 — UI complete:** UI covering M1–M4 surfaces, Document Factory, confirmation/audit/identity surfaces.
4. **C4 — Multi-user complete:** concurrent writers cannot corrupt WP truth; conflicts resolved per A09.

**On C4 exit, Phase C is complete → Phase D (Stabilization).**

---

## Open items / decisions needed (owner)

- **OC-1 — C5 concurrency scope:** ✅ **RESOLVED** — multi-user is **in Phase C** as milestone **C4**, last in Build-Out.
- **OC-3 — C1/C2 ordering:** ✅ **RESOLVED** — **linear, engine-first** (identity is inside C1; AI is C2 after a complete engine).
- **OC-2 — D-14 Option-B role→action authority map (inside C1's identity step):** ⏳ **OPEN** — adopt the role-map now with verified identity, or stay soft and defer the map further? Soft controls hold until decided; no default to hard RBAC (R6).
- **OC-4 — Pack v1.1.0 batch:** ⏳ **deferred to Phase E.** New CQV scope + the carried KS-newline cosmetics are the v1.1.0 candidates; that batch opens in **Phase E (Scope expansion)**, re-entering Phase-A freeze/manifest discipline. Not opened in Phase C.

---

## Risks & cautions

- **R1 (carried) — Mode collision.** Keep runtime `M1–M4` and engine `DESIGN`/`EXECUTION` strictly separate, now also in UI copy (C3).
- **R2 (carried) — AI creeping into the pack.** C2 selects/realizes a model **outside** the pack; the pack stays pure Layer 1. No pack edit for model work.
- **R5 (carried) — Testing-only is permanent scope.** Blocker A + `PRE_FREEZE_USER_REVIEW_REQUIRED` survive the freeze by design. C2 (real model) and C3 (UI) must **not** let polished output imply approved regulated basis — `PRODUCT_TESTING_ONLY` stays stamped and surfaced.
- **R6 (carried) — Identity scope creep.** C1's identity step must integrate real authority without quietly turning soft controls into an unreviewed hard-RBAC policy; the role-map (D-14 Option B) is an explicit owner decision (OC-2), not a default.
- **R7 (carried) — UI implying authority it doesn't have.** A polished UI can imply verification/approval that isn't real. C3 follows a complete C1 (identity live) and C2; identity-dependent surfaces gate behind real state.
- **R8 (carried, mostly Phase E) — Pack v1.1.0 re-opens governance.** Any pack edit (new scope, KS newlines) re-enters the Phase-A freeze/manifest discipline. Batch deliberately in Phase E; never one-off, never in Phase C.
