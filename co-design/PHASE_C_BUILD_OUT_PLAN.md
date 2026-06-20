# Phase C — Build-Out & Hardening Plan

**Status:** DRAFT for owner review · **Updated:** 2026-06-20 · **Author:** co-design (Mervat)
**Baseline:** Phase B **at EXIT** — B1–B7 landed (build `0.3.0`); Gap Assessment v0.3 + Audit Report v1.0; decisions D-01…D-14.
**Precondition:** **Phase B complete.** The runnable build layer (`src/valor_build/`) runs the full PE-HIGH vertical in M3·BUILD·EXECUTION with soft-control identity. Pack stays **frozen at v1.0.1 (`0ec3060`)**; Phase C remains **additive and external** to the pack (no pack edits except a future deliberate **v1.1.0**).

> **What Phase C is.** Phase B proved the spine *runs*. Phase C turns the walking skeleton into a **real, hardened, usable product**: it realizes the two stack layers still stubbed (Layer 2's *model*, Layer 3's *UI*), lifts the two **named-but-deferred** extensions (cryptographic identity, multi-user concurrency), and clears the carried hygiene debt so the baseline is clean. *Humans Decide; Valor Assists* still governs throughout.

---

## The stack at Phase-C entry (what's real vs. stubbed)

- **Layer 1 — deterministic engine (frozen pack).** ✅ Done. Untouched in Phase C.
- **Layer 2 — AI layer.** ◐ *Interface* locked + runnable (D-08: versioned/hashed prompt, temp 0, schema-constrained JSON, refuse/accept, audited) with a **deterministic stub model**. The **real model is unselected** → **C3**.
- **Layer 3 — UI.** ✗ Not designed → **C4**.
- **Identity / authorization.** ◐ Soft controls live (B7/D-14). **Verified identity deferred** → **C2 (`M-IDENTITY`)**.
- **Concurrency.** ◐ Write path is lock-aware (single commit chokepoint + advisory lock). **True multi-user concurrency deferred** (D-03) → **C5**.
- **Hygiene.** Carried non-blockers (doc-reconcile, schema-count, trailing newlines, env cure, G-10 fold, M4-reach tighten) → **C1**.

---

## Work items (sequenced)

### C1 — Hygiene & reconciliation batch *(carried non-blockers — clean the baseline first)*
Cheap, high-leverage, no new architecture. Clearing these makes every later Phase-C step verifiable against a clean state.
- **Gate doc-reconcile:** the `6→5` canonical-gate shorthand is inconsistent across `G-02` / the Phase-B plan / older `SESSION_LOG` entries. Pick one statement of the five canonical gates (Stage/Commit/Plan/Apply/Export) and reconcile the wording everywhere. Doc-only.
- **Schema-count 52/51:** resolve the 1-file delta (52 on disk vs. 51 carrying `$id`; `documents/index.json` has none). Confirm the count statement in the docs and close the note.
- **O4 (a) — CRLF env cure:** document/apply `git config core.autocrlf false` in the build repo so the recurring CRLF gremlin can't re-smudge a Windows checkout. (The repo already enforces `eol=lf` via `.gitattributes`; this closes the local-env half.)
- **O4 (b) — 3 KS schemas missing a trailing newline:** cosmetic (`i/none`) — fold into a pack **v1.1.0** batch (never a one-off pack edit). Record, don't touch the frozen pack now.
- **G-10 fold confirmation:** confirm no genuinely-new governed requirement was left unfolded into `STD-CQV-BASE`; close the fold.
- **M4-reachability tighten (carried from S14):** owner decision — keep M4 reachability at `READ_ONLY + projection-only RPT` (current, reconciled to A18 §2) or tighten to pure `READ_ONLY`. One-line flip either way.
- **Depends on:** nothing. **Exit:** all carried non-blockers either closed or explicitly re-homed (KS newlines → v1.1.0 batch); docs internally consistent; baseline clean.

### C2 — `M-IDENTITY`: cryptographic identity & authorization *(G-07 / D-14 — the named, non-droppable milestone)*
Lift the A10 §3.2/§7 deferral at the pack-named seam. Builds directly on B7's soft controls.
- **Verified `actor.id`:** integrate a real identity provider; populate the **already-cut** `actor.id` seam (frozen envelope permits it — zero pack/schema change) and flip `identity_verified` true.
- **Authority validation:** at A09 §6.2's named point (*"…does not validate real-world authority unless integrated with identity systems"*), validate real-world authority for sensitive actions.
- **Role→action authority map (D-14 Option B, now in scope):** decide whether to adopt the deferred role-map; if so, it replaces the soft `requires_role_ack` predicate (the one-function seam B7 left open). **Owner decision.**
- **Security events:** wire the A10 §8 audit events (`EVT_SECURITY_POLICY_BLOCK`, override-acceptance, etc.) for identity-relevant decisions.
- **Depends on:** B7 (landed). **Exit:** verified identity replaces declared-role soft controls for sensitive actions; authority validated at the pack-named seam; `identity_verified` true; map decision recorded.

### C3 — O1: AI model selection & Layer-2 realization *(D-08 — interface locked, model open)*
Make the locked AI interface real without changing its contract.
- **Model selection spike:** candidate models, eval criteria, cost/latency/hosting (self-host vs. API), data-handling constraints (A10 non-disclosure).
- **Determinism under a real model:** validate the temp-0 / schema-constrained-JSON / refuse-accept loop holds with the chosen model; audit prompt-version + input/output hashes against real outputs.
- **Narrative-only boundary:** enforce Layer-2's *constraints-not-text* rule (CQV standards bound the proposal; the model writes narrative only, never invents compliance facts — A10 §2/§4).
- **Prompt-asset discipline in practice:** versioned/hashed prompt assets managed as real artifacts (not inline strings).
- **Depends on:** B6 AI interface (landed); **independent of C2.** **Exit:** a selected model runs the D-08 loop end-to-end on PE-HIGH with determinism + audit intact; interface contract unchanged.

### C4 — O2: UI (Layer 3) *(the undesigned layer — Document Factory + mode surfaces)*
The multi-screen UI, designed against the now-real lower layers.
- **Per-mode surfaces:** M1 Advisory · M2 Delivery Plan · M3 WP Mode · M4 Project Mode — each with its latitude and **label discipline (G-17)** preserved (M2 Delivery Plan ≠ M3 WP-tasks planning ≠ the CQV-plan *document*).
- **Document Factory** + the **M4 projection presentation surface** (carried from S14's O2 note).
- **Confirmation / gate UX:** the always-live human confirmation gate (A17 §4) and BUILD `WOULD_BLOCK` visibility, surfaced honestly.
- **Identity & stamp visibility:** role-context entry, `actor`/`identity_verified` display, output-stamp + `PRODUCT_TESTING_ONLY` surfacing (R5).
- **Depends on:** C2 (identity surfaces) + C3 (model behavior to present). **Exit:** a UI design pass covering the M1–M4 surfaces, the Document Factory, and the confirmation/audit/identity surfaces, consistent with A16–A18.

### C5 — O3: multi-user concurrency *(D-03 deferred extension — SCOPE DECISION, see Open Items)*
The deferred concurrency extension; the B2 lock-aware path keeps it an extension, not a rewrite.
- **True concurrency** on the single commit chokepoint: advisory → real locking, conflict detection/resolution, the append-only ledger under concurrent writers.
- **Branching/merge** alignment with A09 governance (branch create/freeze, conflict resolution events).
- **Depends on:** B2 store (landed). **Independent of C2/C3/C4.** **Exit:** concurrent writers cannot corrupt WP truth; conflicts surfaced and resolved per A09; ID ledger integrity holds under contention.
- **Note:** you named **four** tracks (C1–C4); C5 is the carried D-03 extension, included here so it isn't silently dropped. **Owner decides:** in-scope for Phase C, or held as a named post-C extension.

---

## Dependency order

```
C1 (hygiene — clean baseline)         [do first; unblocks verification]
       │
       ├─> C2 (M-IDENTITY) ──┐
       ├─> C3 (O1 model) ────┼─> C4 (O2 UI — surfaces identity + model)
       └─> C5 (O3 concurrency)         [parallel; scope decision]
```
C2 and C3 are independent and may run in parallel. C4 depends on both (it presents what they produce). C5 is independent of all three and gated by the scope decision.

---

## Phase-C exit criteria

1. **C1:** carried non-blockers closed or re-homed (KS newlines → v1.1.0 batch); docs internally consistent.
2. **C2:** verified identity + authority validation live at the A09 §6.2 seam; `identity_verified` true; D-14 map decision recorded.
3. **C3:** a selected model runs the locked D-08 loop on PE-HIGH with determinism + audit intact.
4. **C4:** UI design pass covering M1–M4 surfaces, Document Factory, and confirmation/audit/identity surfaces.
5. **C5 (if in scope):** concurrent writers cannot corrupt WP truth; conflicts resolved per A09.

---

## Open items / decisions needed (owner)

- **OC-1 — C5 scope:** is multi-user concurrency (O3) in Phase C, or held as a named post-C extension? (You named four tracks; C5 is the fifth, carried.)
- **OC-2 — D-14 Option B in C2:** adopt the role→action authority map now (with verified identity), or stay soft and defer the map further?
- **OC-3 — C2/C3 ordering:** parallel, or sequence one first? (Both build on landed B-items; either order works.)
- **OC-4 — Pack v1.1.0 batch trigger:** C1's KS-newline fix + any C2 schema needs are the first candidates for a deliberate pack v1.1.0. Decide when to open that batch (it re-enters the freeze/manifest discipline of Phase A).

---

## Risks & cautions

- **R1 (carried) — Mode collision.** Keep runtime `M1–M4` and engine `DESIGN`/`EXECUTION` strictly separate, now also in the UI copy (C4).
- **R2 (carried) — AI creeping into the pack.** C3 selects/realizes a model **outside** the pack; the pack stays pure Layer 1. No pack edit for model work.
- **R5 (carried) — Testing-only is permanent scope.** Blocker A + `PRE_FREEZE_USER_REVIEW_REQUIRED` survive the freeze by design. C3 (real model) and C4 (UI) must **not** let polished output imply approved regulated basis — `PRODUCT_TESTING_ONLY` stays stamped and surfaced (R5).
- **R6 (new) — Identity scope creep.** C2 must integrate real authority without quietly turning soft controls into an unreviewed hard-RBAC policy; the role-map (D-14 Option B) is an explicit owner decision (OC-2), not a default.
- **R7 (new) — UI implying authority it doesn't have.** A polished UI can imply verification/approval that isn't real until C2 lands. Sequence C4 after C2, or gate identity-dependent surfaces behind it.
- **R8 (new) — Pack v1.1.0 re-opens governance.** Any pack edit (C1 KS newlines, C2 schema needs) re-enters the Phase-A freeze/manifest discipline. Batch deliberately; never one-off.
