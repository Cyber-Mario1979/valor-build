# A16 — Runtime Target Spec

**Status:** SKELETON (B2 — not yet written) · **Gap:** G-01 (biggest buildability gap) · **Baseline:** frozen pack v1.0.1 / `0ec3060`.

> This is a placeholder so B2 has a home. Sections below are the agreed scope from `co-design/PHASE_B_BUILD_WORKFLOW_PLAN.md` (B2); fill them in during the B2 session. **Do not invent content here** — each section is a decision or a spec to be written, not a guess.

## 1. Scope & relationship to the pack
- A16 specifies *what the system is built on*; the pack specifies *what it is*. A16 is additive and external.

## 2. Stack (D-04)
- Python + JSON Schema **draft-07**; explicit contract-validation layer at **every boundary**; fail-closed.

## 3. WP store (G-06 / D-03)
- **file/git**, satisfying the mandated **append-only ID ledger + tombstoning** (A04.2 §4).
- **Lock-aware write path from day one** — single commit chokepoint + advisory lock.
- Multi-user concurrency **deferred** as an extension, not a rewrite (O3).

## 4. LLM interface (D-08 — LOCKED)
- Prompt = versioned/hashed asset; temp 0; schema-constrained JSON; refuse/accept loop (1 silent retry → 2nd failure escalates to human); audit-logged prompt-version + input-hash + output-hash.
- Model selection = a later spike (O1).
- **Validation lesson to carry (from A3):** the engine's validation layer must use a real `$ref` registry / absolute `$id`s, not naive ref-following — the pack's `valor://` scheme defeats `urljoin`.

## 5. Contract enforcement map
- Each engine boundary → its contract action + `result_schema_ref`. (39 actions across 7 contracts.)

## 6. Seams
- Engine (Layer 1, the pack) ↔ AI (Layer 2) ↔ UI (Layer 3). Define each interface concretely.

## 7. Open items
- O1 LLM model selection · O2 UI design · O3 multi-user concurrency. (See Phase-B plan.)
