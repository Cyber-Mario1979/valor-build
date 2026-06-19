# VALOR Freeze-Status Register

**Type:** Co-design artifact — **lives OUTSIDE the hashed pack** (migrates to the build repo `co-design/` in Phase B; D-01).
**Purpose:** One map of the v1.0.1 freeze: which status value, on what discipline/domain, is frozen vs. deliberately not — and *why*. This is the authoritative record of the A5 status sweep.
**Baseline:** sweep applied to pack HEAD `78c40d7`; verified on two independent clones (verify 173 / smoke / harness PASS; 0 residual; 0 CR).
**Scheme decided (owner, 2026-06-18):** lifecycle suffix `_PRE_FREEZE → _FROZEN`; capability prefix preserved; header phase `pre_freeze_controlled / PRE_FREEZE_CONTROLLED → frozen_controlled` (lowercase normalized). KS content-approval lifecycle is **out of scope** (see §2).

---

## §1 — Swept to FROZEN (pack-freeze governance lifecycle)

| Frozen value | Was | Discipline / domain | Where it lives | State | Why frozen |
|---|---|---|---|---|---|
| `frozen_controlled` | `pre_freeze_controlled` / `PRE_FREEZE_CONTROLLED` | Pack & document governance phase | Registry header; arch docs A04.1/.2/.4/.5/.6, A05–A08, A12, A13, A15; 4 addendums; libraries CAL/PS/PROF/TP headers; registry vector | **FROZEN** | The whole pack reaches its frozen baseline; the header phase moves from controlled-pre-freeze to controlled-frozen. "Controlled" retained — changes still batch into a deliberate v1.1 (D-02). |
| `ACTIVE_FROZEN` | `ACTIVE_PRE_FREEZE` | Public-callable execution engine | WP, WP-user-driven, PLAN, DOC, RPT contracts + their actions (registry, 7 contract bodies, action_blocks) | **FROZEN** | Core deterministic engine contracts/actions are design-complete and audit-confirmed (G-05); they freeze as the v1.0.1 callable surface. |
| `ACTIVE_INTERNAL_FROZEN` | `ACTIVE_INTERNAL_PRE_FREEZE` | Internal service resolver | PS (preset resolver) | **FROZEN** | Internal-only resolver; frozen alongside the engine. Capability ("internal") preserved in the prefix. |
| `ACTIVE_NON_CALLABLE_FROZEN` | `ACTIVE_NON_CALLABLE_PRE_FREEZE` | Non-callable support authorities | TP (task pool), PROF (profile), CAL (calendar) | **FROZEN** | Governed support authorities consumed by the engine; frozen. "Non-callable" capability preserved. |
| `ACTIVE_POLICY_FIRST_FROZEN` | `ACTIVE_POLICY_FIRST_PRE_FREEZE` | Policy-first cross-cutting control | SEC | **FROZEN** | Cross-cutting security control; frozen. "Policy-first" capability preserved. |
| `TESTING_ONLY_FROZEN` | `TESTING_ONLY_PRE_FREEZE` | Knowledge-standards contract actions | orch-ks actions | **FROZEN (testing-only)** | The KS *contract surface* freezes, but its scope stays testing-only — capability ("testing only") preserved in the prefix; this is the contract, not the content (see §2). |
| `TESTING_ONLY_FROZEN_WITH_REGULATED_USE_BLOCK` | `TESTING_ONLY_PRE_FREEZE_WITH_REGULATED_USE_BLOCK` | KS contract (contract-level) | orch-ks contract head | **FROZEN (testing-only, regulated-use blocked)** | The contract freezes; the regulated-use block is a standing scope constraint that persists past freeze (ties to blocker A, §4). |

## §2 — Deliberately NOT swept (different lifecycle — left as-is)

| Value | Discipline / domain | Where it lives | State | Why untouched |
|---|---|---|---|---|
| `PRE_FREEZE_USER_REVIEW_REQUIRED` | Knowledge-standards **content approval** | `approval_status` on STD-CQV-BASE, all TPL-* templates, all BND-* bundles, source mapping, external references; **plus** the `status` **enum** in 9 KS schemas (`[TESTING_ONLY, PRE_FREEZE_USER_REVIEW_REQUIRED, ACTIVE, DUE_FOR_REVIEW, EXPIRED, SUPERSEDED, BLOCKED]`) | **NOT frozen — pending user review** | This is the *regulatory approval* lifecycle of the knowledge content, **orthogonal to the pack-freeze lifecycle**. Freezing the pack does not approve the content — editions/dates/locators are still gated for regulated use (blocker A). Sweeping it would (a) rewrite 9 schema enums, (b) conflate two lifecycles, and (c) make testing-only content read as *approved*, violating the registry's `validation_requirement` #3 ("TESTING_ONLY assets cannot be represented as approved regulated basis"). Its sibling state `ACTIVE` in this enum already means *approved* — so the separation is load-bearing. |

## §3 — Removed in this pass

| Item | What | Why | Recoverable |
|---|---|---|---|
| `_review_control/` (28 files) | Stale review scaffolding (Blockers, DECISION_LOG, `FINAL_FREEZE_READINESS_*`, `PHASE13_*`, `.bak_phase11` cruft) from a prior freeze attempt that did not succeed | Contradicts the real freeze; same stale-status-drift class cleaned in build-prep-0.7. Authoritative record is SESSION_LOG/CHANGELOG/gap-assessment/audit. | Yes — git history retains every byte. |
| `EXCLUDE_DEGOVERNED_DIRS` (in `pack_excludes.py`) | The de-govern exclude that pointed at `_review_control/` | Dead once the folder is gone; removing it cuts machinery and a future "why is this here?" | Yes — git history. |

## §4 — freeze_blockers_retained (resolved, owner 2026-06-18)

- **Blocker B** ("Manifest regeneration and final freeze-readiness check remain blocked until all pre-freeze content edits are complete") — **REMOVED.** Pure process gate; its condition is satisfied (edits done, manifest regenerated clean at 173). Leaving it would make a `frozen_controlled` registry self-contradictory.
- **Blocker A** ("K&S content testing-only; regulated use gated") — **RETAINED verbatim.** Not a process gate: it is the standing statement that the knowledge-standards content is *not approved for regulated use*. It is the same boundary that kept `PRE_FREEZE_USER_REVIEW_REQUIRED` (§2). Removing it would misrepresent unapproved testing-only content as unrestricted. (`freeze_blockers_retained` now holds A only.)

---

*Sweep verified by co-design on Linux/LF across two independent clones. Owner commits, freezes, tags v1.0.1.*
