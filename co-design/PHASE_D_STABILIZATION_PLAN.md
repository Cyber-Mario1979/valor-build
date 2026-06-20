# Phase D — Stabilization Plan

*Part of VALOR phasing — see `BUILD_STRATEGY.md` §0.*

**Status:** PLANNED (not started) · **Updated:** 2026-06-21 · **Author:** co-design (Mervat)
**Baseline:** Phase C complete — Engine + AI + UI + Multi-user all landed.
**Precondition:** **Phase C complete.** A built product (single- and multi-user) exists. Pack still **frozen at v1.0.1 (`0ec3060`)**; Phase D is **additive and external** to the pack (testing + fixes, no new scope, no pack edits).

> **What Phase D is.** Phase C builds the product; Phase D **hardens** it. The owner runs heavy testing for a while, comes back with a punch list, we work it together, retest until stable, and reissue. Only on a proven, stable base does scope grow (Phase E). *Humans Decide; Valor Assists* governs throughout. **Pack untouched.**

---

## Milestones (in order)

```
D1 · Heavy testing  ──>  D2 · Punch list  ──>  D3 · Fix together  ──>  D4 · Retest  ──>  D5 · Reissue
   (owner, solo, a while)    (owner-authored)     (co-design + owner)     (confirm stable)   (stabilized release)
```

### D1 — Heavy testing *(owner, solo, for a while)*
The owner drives real, sustained testing of the complete product. Solo — so this round exercises the single-user paths hard before concurrency is stressed.
- **Exit:** the owner has put the product through real use and gathered findings.

### D2 — Punch list *(owner-authored)*
The owner returns with a concrete punch list — defects, rough edges, gaps found in use.
- **Exit:** a written punch list exists, ready to work.

### D3 — Fix together *(co-design + owner)*
We work the punch list together — triage, fix, verify each item.
- **Exit:** punch-list items resolved or explicitly deferred with reason.

### D4 — Retest *(confirm stable)*
Another testing round to confirm the fixes hold and nothing regressed.
- **Exit:** the product is stable under the owner's testing; no open blockers.

### D5 — Reissue *(stabilized release — milestone)*
Cut the stabilized release.
- **Exit:** a stabilized, versioned reissue is published. **Phase D complete.**

---

## Phase-D exit criteria

1. Heavy testing done; punch list authored, worked, and closed (or items deferred with reason).
2. Retest confirms stability; no open blockers.
3. Stabilized reissue published.

**On D5, Phase D is complete → Phase E (Scope expansion), at the owner's discretion.**

---

## Open items / decisions needed (owner)

- **OD-1 — Reissue versioning:** how the stabilized reissue is versioned (build-prep workstream vs. a product version line). Decide when D5 is in view.
- **OD-2 — Punch-list scope boundary:** is any punch-list item allowed to touch CQV *scope* (→ defer to Phase E), or is Phase D strictly fixes within existing scope? Recommended: **fixes only**; new scope is Phase E.

---

## Risks & cautions

- **R-D1 — Scope creep via the punch list.** A punch list is a magnet for "while we're here, also add…". Phase D is **hardening, not widening** — new scope routes to Phase E (OD-2).
- **R5 (carried) — Testing-only is permanent.** Heavier real-world use must not erode the `PRODUCT_TESTING_ONLY` stance; the stamp stays.
