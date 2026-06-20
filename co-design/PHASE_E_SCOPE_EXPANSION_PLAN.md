# Phase E — Scope Expansion Plan

*Part of VALOR phasing — see `BUILD_STRATEGY.md` §0.*

**Status:** PLANNED (not started; owner-gated) · **Updated:** 2026-06-21 · **Author:** co-design (Mervat)
**Baseline:** Phase D complete — a stable, reissued product.
**Precondition:** **Phase D stable.** Only widen scope on a proven, stable base.

> **What Phase E is — and how it differs from Phase C.** Phase C filled out the CQV scope the frozen pack **already defines** (additive, external, **pack never touched**). Phase E widens CQV scope the pack does **not yet define** — which **touches the pack** through a deliberate, governed **v1.1.0** that re-enters the Phase-A freeze/manifest discipline. Same words ("widen the scope"), very different governance. This is the heavier, more controlled move — which is why it sits last, after everything is stable.

---

## Milestones (shape; detail set when Phase E opens)

```
E1 · Define new scope  ──>  E2 · Open pack v1.1.0 batch  ──>  E3 · Freeze + verify  ──>  E4 · Build-out the new scope
   (what CQV grows to)        (governed pack edit)              (manifest discipline)      (additive, as in Phase C)
```

### E1 — Define new CQV scope
Decide precisely what scope grows: new contracts/actions, new presets/profiles/task-pools (e.g. effort classes beyond `PS-PE-HIGH`), new standards bindings.
- **Exit:** the delta from v1.0.1 scope is specified and owner-approved.

### E2 — Open the pack v1.1.0 batch *(the governed pack edit)*
Open a deliberate **pack v1.1.0** — the *only* sanctioned way the frozen pack changes. Batches in: the new scope from E1, plus the carried cosmetics deferred from Phase C (the 3 KS-schema trailing newlines).
- **Exit:** v1.1.0 changes staged in the pack repo under the Phase-A discipline (never one-off; never from the build repo).

### E3 — Freeze + verify v1.1.0
Re-run the Phase-A freeze/manifest cycle on v1.1.0: `verify_manifest.py`, smoke, harness; registry status; new pinned commit.
- **Exit:** pack **v1.1.0** frozen and hash-verified; the build repo re-pins to the new commit.

### E4 — Build-out the new scope
Cover the new scope in the build layer exactly as Phase C covered v1.0.1 scope — additive, external, dynamic registry-load (A16 §4) carrying the new actions by pattern.
- **Exit:** the engine/AI/UI cover the widened scope; product complete at the new scope. **Project finished at this scope** (until the next deliberate widening — phasing is open-ended).

---

## Phase-E exit criteria

1. New CQV scope defined and owner-approved (E1).
2. Pack **v1.1.0** built, frozen, hash-verified; build repo re-pinned (E2–E3).
3. New scope covered in the build layer, additive and external (E4).

---

## Open items / decisions needed (owner)

- **OE-1 — What grows:** which CQV scope to add (new presets/effort classes? new contracts/actions? new standards?). The E1 input.
- **OE-2 — v1.1.0 trigger timing:** when to open the batch (it re-enters full governance — do it deliberately, not opportunistically). Carries OC-4 from Phase C.
- **OE-3 — Re-pin mechanics:** the build repo's submodule re-pin from `0ec3060` → the v1.1.0 commit, and the CI verify against the new manifest.

---

## Risks & cautions

- **R8 (carried, central here) — Pack v1.1.0 re-opens governance.** This phase *is* the controlled pack edit. Every change goes through the freeze/manifest discipline; nothing ad-hoc; nothing from the build repo into the pack.
- **R2 / R5 (carried) — Layer purity + testing-only.** New scope keeps the pack pure Layer 1; AI stays external; the `PRODUCT_TESTING_ONLY` stance is re-evaluated only by a deliberate, separate owner decision — not implied by scope growth.
