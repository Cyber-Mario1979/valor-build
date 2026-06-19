# A17 — BUILD Mode Spec

**Status:** WRITTEN (B3) · **Gap:** G-02 (no dormant build mode, P0) · **Decision:** D-07 (log-only in BUILD) · **Baseline:** frozen pack v1.0.1 / `0ec3060`.
**Layer scope:** the build/runtime layer (L2 orchestration around the L1 pack). The pack (L1) is consumed read-only; nothing here edits it. Builds directly on **A16** (B2).

> The pack's governance gates are **mandatory and always-enforcing** by design — there is no development mode in which they stand down (G-02). A17 defines a runtime **BUILD mode** in which the pack's gate *verdicts* are **recorded but not enforced**, so build/iteration is never halted by a governance stop — while the human-confirmation gate and truth-store integrity stay fully live. The same code path runs **LIVE (gated)** in production by flipping one switch. Every clause traces to a settled decision (D-##), a confirmed gap (G-##), or pack content read directly from the `0ec3060` submodule. No invention; unknowns tagged **[OPEN]**.
>
> **Doc placement note:** like A16, A17 is a *build-repo* architecture doc extending the A-series externally; it lives in `docs/`, outside any hashed pack root (D-01/D-09), and is never folded into the pack.

---

## 1. Scope & the two-mode model

- **BUILD mode is a runtime enforcement policy, not a phase of the calendar.** Gates are inert whenever the system *runs in BUILD*; live whenever the same path *runs in LIVE (gated)*. "Back to enforcing" is a function of **which mode is selected**, not of what week it is. Testing is not a third state: fast iteration runs in BUILD (nothing halts you); gate-conformance is proven by running the same path in LIVE specifically to confirm the gates still stop what they should.
- **Where the switch lives (R2 — no pack edit).** The pack (L1) always evaluates every gate and returns its verdict; that behaviour never changes and is never patched. BUILD mode lives entirely in the **runtime layer around** the pack: it decides what to *do* with a verdict the pack already produced. The pack is never told to skip a gate — it is told nothing. Dormancy is an L2 enforcement-policy choice, additive and external.
- **Builds on A16.** The seams (§6) and the contract-enforcement pattern (§5) of A16 are the surfaces gate-policy attaches to. A16 §5's pattern line `→ [validate result] → return | refuse` becomes mode-sensitive here: in BUILD a gate refusal becomes log-and-proceed; a *truth-write* validation refusal does not (§4).

---

## 2. The pack's canonical gates (ground truth)

The authoritative gate set is `A04_1_Orchestration` §4.1 — **five** mandatory governance gates, in flow order:

| # | Gate | Purpose (A04_1 §4.1) | Produces |
|---|---|---|---|
| 1 | **GATE-Stage** | assemble candidate tasks/metadata, no IDs allocated | `STAGED` |
| 2 | **GATE-Commit** | allocate task IDs, write WP truth | `COMMITTED` |
| 3 | **GATE-Plan** | compute PROPOSED schedule (Planning) | `PROPOSED` |
| 4 | **GATE-Apply** | apply schedule to WP task dates | `COMMITTED` + provenance |
| 5 | **GATE-Export** | generate report/export artifacts | artifact + stamps |

When a gate's entry condition is not met, the pack yields **`BLOCKED`** — "operation refused/stopped because a hard gate is not satisfied" (A04_1 §4.3).

> **Correction folded in this session (doc-reconcile, carried).** Earlier co-design docs (G-02, the Phase-B plan B3 slice, the SESSION_LOG NEXT block) described the gates as *"Stage / Validate / Commit / Apply / Finalize / Close."* That six-item shorthand is inaccurate against the pack and is superseded here: it dropped the real **Plan** and **Export** gates and folded in three non-gates — **Validate** is the fail-closed validation posture wrapping every gate (the `VALIDATE_ONLY` action class), **Finalize** is the DOC lifecycle `DRAFT → FINAL` step (`DOC_FINALIZE_ARTIFACT`, `A04_5` §6), and **Close** is *architecture closure* (`A13`), a separate axis entirely. The five gates above are canonical.

---

## 3. BUILD-mode gate behaviour (log-only / dormant) — D-07

In **BUILD**, each of the five gates still **evaluates** its entry condition and the runtime **records the verdict** — then *proceeds regardless*:

- A verdict that would be **`BLOCKED`** in LIVE is instead logged as `would_block` with its reason, and the flow **continues**. Development is never halted by a governance stop.
- A **PASS** verdict is logged identically in both modes, so a BUILD log is directly comparable to a LIVE one.

**Gate-outcome record (logged on every gate evaluation, both modes):**

```
gate:            GATE-Stage | GATE-Commit | GATE-Plan | GATE-Apply | GATE-Export
mode:            BUILD | LIVE
entry_condition: met | not_met
verdict:         PASS | WOULD_BLOCK
reason:          <text, required when WOULD_BLOCK>
proceeded:       true (BUILD) | false (LIVE, on WOULD_BLOCK)
wp_id:           WP###
actor_role:      <declared-role soft-control, A10 stub — ties to G-07/B7>
prompt_version / input_hash / output_hash: <when the step involved an L2 AI call (A16 §4)>
timestamp:       <iso8601>
```

The log is the *same audit channel* A16 §4 defines for AI calls — BUILD-mode gate outcomes are first-class audit records, not console noise. This is what makes "the same path can later run gated" auditable: the BUILD log already shows every place LIVE *would* have stopped.

---

## 4. What stays ON in every mode (BUILD included)

Two things are **never** dialled down, by decision:

- **The human-confirmation gate (A04_1 §4.2).** Before `GATE-Commit` and `GATE-Apply`, orchestration still asks the human Yes/No — *"Confirm commit staged tasks to WP### (Yes/No)"* and *"Confirm apply schedule proposal to WP### (Yes/No)."* A **No** still leaves the WP `STAGED`/`PROPOSED` and **does not mutate truth**, in BUILD exactly as in LIVE. This is *Humans Decide; Valor Assists* — it holds in all modes. (Owner decision, this session: human confirmation is always live.)
- **Truth-store integrity.** BUILD waives *gate enforcement*, never *store correctness*. Schema/contract validation (A16 §2, fail-closed) still runs in BUILD; a structurally-invalid write is still **refused** before it reaches the WP store. The store is append-only with tombstoning and never-reused IDs (A16 §3) — a bad commit is permanent and irreversible, so "don't block the developer" must never become "write malformed truth." Validation *notes* on read/advisory paths may log-and-proceed; a write that would corrupt the ledger does not.

In short: **BUILD relaxes governance gates; it does not relax human consent or data integrity.**

---

## 5. Inert vs. live — one path, one switch

| Aspect | BUILD (gates dormant) | LIVE (gated) |
|---|---|---|
| Gate evaluation | runs, verdict logged | runs, verdict logged |
| `WOULD_BLOCK` verdict | logged; **flow proceeds** | becomes `BLOCKED`; **flow halts** |
| Human confirm (Commit/Apply) | **asked & honored** | asked & honored |
| Schema validation on writes | fail-closed (refuse) | fail-closed (refuse) |
| Mode stamp on outputs | `mode: BUILD` | `mode: LIVE` |
| Regulated representation | **forbidden** (§6) | per governing controls |

The switch is a single runtime mode flag read by the enforcement layer *around* the pack. No pack code and no gate code branches on it — only the *post-verdict action* does. That is the whole of "the same path runs gated in production."

---

## 6. What BUILD mode is NOT (R5 / Blocker-A guard)

BUILD-mode output must **never** be represented as a regulated-ready basis. This is load-bearing, not boilerplate:

- Every BUILD output carries the pack's **`PRODUCT_TESTING_ONLY`** marker — "may support product testing only and must not be represented as regulated-ready CQV/GMP output" (A04_1 §4.3).
- Freeze **Blocker A** and **`PRE_FREEZE_USER_REVIEW_REQUIRED`** survive the freeze by design (Freeze-Status Register §2/§4; plan R5). A dormant gate is **not** a satisfied gate — a `would_block` logged-and-passed in BUILD has *not* met its control; it has deferred it. Nothing in BUILD may imply the underlying CQV/standards basis is approved.
- **Finalize / Close are not runtime gates** and are out of scope for mode switching: `Finalize` is the DOC `DRAFT→FINAL` artifact step (checksum + source-chain controls; `A04_5`), and `Close` is architecture closure (`A13`). Neither is made "dormant" by BUILD mode — they are different axes.

---

## 7. Open / carried items (non-blocking for B3)

- **Doc-reconcile (raised this session):** correct the "Stage/Validate/Commit/Apply/Finalize/Close" six-gate shorthand → the five canonical gates in G-02, the Phase-B plan B3 slice, and the SESSION_LOG. Doc-only, opportunistic.
- **O1** LLM model spike · **O2** UI (Seam B) · **O3** multi-user concurrency (the lock-aware path keeps it an extension) — all per A16 §7.
- **Schema-count reconcile** (A16 §5): 52-on-disk vs 51-cited, 1 file.
- **G-07/B7** identity: BUILD logs already carry `actor_role` from the A10 soft-control stub; the named crypto-identity milestone remains carried.

---

### Exit criteria (B3) — met by this doc
- [x] BUILD mode defined as a runtime enforcement policy (not a phase), switchable against LIVE — R2-safe (no pack edit).
- [x] Gate outcomes **logged, not enforced** in BUILD (D-07); gate-outcome record specified on the A16 §4 audit channel.
- [x] Grounded on the pack's **five canonical gates** (A04_1 §4.1); six-item shorthand corrected.
- [x] Human-confirmation gate and truth-store integrity specified as **always-on**, BUILD included.
- [x] Inert-vs-live documented as one path / one switch.
- [x] R5 guard: BUILD ≠ regulated-approved; `PRODUCT_TESTING_ONLY` + Blocker-A preserved.

**Next:** B4 — runtime mode model (ARCH/BUILD × DESIGN/EXECUTION; runtime M1–M4; per-mode latitude; label discipline) — G-16 / G-17.
