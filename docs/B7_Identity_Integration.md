# B7 — Identity-integration milestone (soft controls + named crypto milestone)

**Gap:** G-07 · **Decision:** D-14 (Option A) · **Build:** `0.2.0 → 0.3.0` · **Pack:** frozen v1.0.1 (`0ec3060`), **no pack edits.**

B7 is the **last Phase-B exit item**. It has two halves, per the Phase-B plan and the owner condition on G-07: implement the **soft-control** identity stub *now*, and carry the **cryptographic-identity** milestone as an explicit, **named**, non-droppable item in the plan timeline.

---

## 1. What the pack specifies (grounded)

- **A10 §3.2 / §7 — soft controls.** Identity is not cryptographically verified in v0.1.x. While unverified, SEC applies soft controls: *require explicit role context for sensitive operations; require confirmations for commit/finalize/export; log the declared role in audit events.* On an action inconsistent with the declared role: *"warn and require explicit acknowledgement (**policy choice**)."*
- **A09 §6.2 — the integration seam.** *"The system stores who approved, but it does not validate real-world authority unless integrated with identity systems."* That clause is the pack-named plug-in point for cryptographic identity.
- **A09 §7.1 — actor shape.** The canonical audit event carries `actor: {role, name(optional), id(optional)}`.

## 2. What landed (the *now* half — soft controls)

All additive, in `src/valor_build/`; the human confirmation gate and truth-store integrity remain the live controls (A17 §4).

- **`engine/identity.py` (new).** `RoleContext` (`role`, `name?`, `id?` — `id` reserved for crypto, always `None` here); `RoleContext.capture(...)` emits one audited `identity_context` record per action with `identity_verified: false`; `actor_block(role, name?, id?)` builds the A09 §7.1 `{role, name?, id?}` block; `requires_role_ack(confirm, role)` is the warn-with-ack predicate.
- **`engine/dispatch.py` (edit, 5 surgical changes).** Capture role-context at entry; build the envelope `actor` via `actor_block` (byte-identical to the old `{"role": …}` when no name/id); **stamp `actor_role` on every output** (A10 §7 "log the declared role"); run the warn-with-ack soft control before the confirmation prompt; `StepRequest` gains an optional `actor_name`.
- **Sensitive = the pack's own `confirm:true` flag.** A10 §7 names "commit/finalize/export"; those are exactly the registry's `confirm:true` actions. Keying off the pack's flag avoids a parallel enumerated list that would go stale at pack v1.1.0 (the same enumerate-vs-represent discipline as the contract map).
- **Warn-with-ack.** A `confirm:true` action with **no declared role** emits a `role_consistency_warning` and requires explicit acknowledgement; declining refuses with `ROLE_CONTEXT_UNACKNOWLEDGED`. It stays *soft* — there is no role→action authority map. The declared-role slices (`actor_role="CQV"`) never trip it, so all 23 prior B5/B6 tests are unaffected.
- **Tests:** `tests/test_identity.py` (9) — capture audited · role stamped on every output · capture helper · actor block backward-compatible · **`actor.id` validates through the frozen envelope** · ack predicate · blank-role refuses when unacknowledged · proceeds past the identity gate when acknowledged · declared role never warns.

**Checks (fresh-clone):** `pytest` → **32 passed** (10 B6 + 13 B5 unchanged + 9 B7). `python -m valor_build.skeleton` and `... project_skeleton` green; identity events present; all kind-filtered audit counts (gates/ai_calls/stamps) unchanged.

## 3. Decision rationale — D-14 (Option A), alternatives considered

The A10 §7 inconsistent-role behaviour is explicitly a *"policy choice."* Two options were weighed; **Option A** was chosen.

| | **Option A** — capture + log + warn-with-ack | **Option B** — soft role→action map |
|---|---|---|
| **Pros** | Matches A10 §7 verbatim — zero invented policy. Stays genuinely *soft*; no RBAC creep. Smallest surface — additive, fast to build/test. Crypto milestone slots in cleanly later (`actor.id` fills the same block) with no authorization map to rework. No "who may do what" baked into code. | Gives warn-with-ack a real basis: commit/finalize/export carry *expected* roles (A09 §6.2), so "inconsistent" becomes concrete and the warning is meaningful. Richer audit signal — flags genuine role mismatches. Can still be soft (warn+ack, not refuse). |
| **Cons** | The "warn" half is thin without expected roles — "inconsistent" is shallow (catches only an undeclared/blank role, not a wrong-but-declared one). Relies on the declared role being honest. | A09 §6.2 calls those role expectations *"typical,"* not normative — encoding them risks typical→enforced drift (soft→hard), i.e. policy the pack didn't commit. Bigger, owner-owned role→action table to maintain. Couples B7 to a decision that arguably belongs to the crypto phase. Hardcoded map drifts at pack v1.1.0 (enumerate-vs-represent). |

**Why A:** faithful + additive, and it **does not preclude B**. The `requires_role_ack` predicate is a single-function seam: a role map (Option B) or verified identity is a drop-in replacement for that one function. The role-map decision and real-authority validation are deferred into **M-IDENTITY** below, not lost.

## 4. `M-IDENTITY` — cryptographic identity (NAMED, deferred — do not drop)

Carried per the owner condition (G-07) and D-14. Mirrored in `PHASE_B_BUILD_WORKFLOW_PLAN.md`.

- **Integration seam (pack-named):** A09 §6.2 — real-world authority is validated only "integrated with identity systems." A10 §3.2/§7 is the deferral this milestone lifts.
- **Schema seam (already cut):** the frozen `contract_request` `actor` block permits `{role, name}` with `additionalProperties:true`, so a verified `actor.id` validates **today** (proven by `test_actor_id_validates_through_frozen_envelope`). M-IDENTITY fills `actor.id` and flips `identity_verified` true with **zero pack/schema change**.
- **Scope:** verified actor identity replacing/augmenting declared-role soft controls; the home for a role→action authority map (D-14 Option B) and real-authority validation, if adopted.
- **Status:** named, not scheduled — sequenced after Phase-B exit; **not** an exit blocker.

## 5. Scope statement

B7 is *soft controls only*. It is **not** a hard authorization system: no identity verification, no enforced role→action permissions. Those are M-IDENTITY. The live controls remain the human confirmation gate and truth-store integrity.
