# M-IDENTITY — Verified identity + the D-16 soft authority map (C1 Step 3)

**Milestone:** `M-IDENTITY` (named & carried in B7 §4) · **Decision:** D-16 / OC-2 (S20) · **Build:** `0.4.0 → 0.5.0` · **Pack:** frozen v1.0.1 (`0ec3060`), **no pack/schema edits.**

C1 Step 3 lifts the identity deferral B7 left as a named, non-droppable milestone. It is the **verified** half of identity: a real credential is presented and checked, producing a verified actor with a populated `actor.id` and `identity_verified=True`, and the D-16 role→action authority map validates real-world authority for sensitive actions — **soft** (warn-with-ack), never hard RBAC (R6). With this, **C1 Engine is complete**: every active action runs single-user across all five side-effect classes and all four runtime modes with identity verified.

---

## 1. What the pack specifies (grounded)

- **A09 §6.2 — the integration seam.** *"The system stores who approved, but it does not validate real-world authority unless integrated with identity systems."* M-IDENTITY is that integration; the clause is the pack-named plug-in point.
- **A10 §3.2 — the deferral being lifted.** Identity/authorization are *not* cryptographically verified in v0.1.x; SEC relied on behaviour constraints, confirmations, audit capture, and refusal. Verified identity is now available, so authority can be validated.
- **A09 §7.1 — actor shape.** `actor: {role, name(optional), id(optional)}`. The frozen `contract_request` `actor` block is `additionalProperties:true`, so a verified `actor.id` validates **today** — proven since B7 by `test_actor_id_validates_through_frozen_envelope`. **Zero pack/schema change.**
- **A10 §8 — security-relevant audit events.** Each carries rationale, affected artifact IDs, and stamps when relevant.

## 2. What landed

All additive, in `src/valor_build/`. The human-confirmation gate and truth-store integrity remain the live controls (A17 §4); the verified path layers authority validation on top.

### 2.1 Authentication — verified local identity (`engine/identity.py`)
- `Principal` — a verified actor (`id`, `profile`, `role`, `name?`, `verified=True`), constructible only by a real credential check.
- `Credential` / `make_credential` — a salted **PBKDF2-HMAC-SHA256** (120k rounds) hash of the secret; the secret is never stored. `profile` must be a known D-16 tier.
- `CredentialStore` — in-memory local store; the swap point for a file/DB/IdP-backed store behind the same surface (A09 §6.2), zero caller change.
- `LocalIdentityProvider.authenticate(username, secret)` — constant-time compare; on success emits an `auth_event` and returns a verified `Principal` with a real `id` (`valor:uid:<user>`); on failure emits an A10 §8 `security_event` (`EVT_SECURITY_POLICY_BLOCK`) and raises `AuthenticationError`. A missing user still does a throwaway derive-and-compare so timing doesn't leak existence.

### 2.2 Authorization — the D-16 soft role→action map (`engine/authority.py`, new)
The role→action map B7 §4 deferred and D-16 adopted — keyed to the registry's own `confirm:true` flag (no parallel action list; pack v1.1.0 classified by pattern):
- **Profiles:** `read-only` (reads only) · `editor` (task path; **cannot** approve documents) · `approver` (may finalize controlled documents) · `admin` (all, always logged) · `CQV` engineer (full WP truth path, **solo** — no task-path segregation).
- `authorize(profile, spec)` → `AuthorityVerdict`. Non-sensitive (`confirm:false`) actions are never gated. `admin` is always authorized. `DOC_FINALIZE_ARTIFACT` (controlled document) needs `approver`/`admin`; all other `confirm:true` (task path) needs `editor`/`CQV`/`admin`.
- **approver(s) ≠ author** (`evaluate_approval`) — the multi-approver rule for controlled documents, carried at the **engine/audit layer**: the frozen `doc.actors.approver` is one string, but the engine records the full signed approver **set** in its own `document_approval` audit event (`additionalProperties:true` → zero pack change). Each entry is a distinct verified, logged approval.

### 2.3 Dispatch wiring (`engine/dispatch.py`)
- `StepRequest` gains `principal`, `author_id`, `approvals`. **When `principal` is None the soft B7 path runs byte-for-byte unchanged** (declared role, `identity_verified=False`); the verified path is pure addition.
- Verified `identity_context` carries `identity_verified=True` + the real `actor.id` + `profile`; the envelope `actor` block carries the verified `id`; the output stamp carries `actor_id`, `profile`, `identity_verified`.
- **Authority validation (step 4b)** runs for `confirm:true` actions when a principal is present. SOFT: a lacking-authority verdict is a **warn-with-ack** (`authority_warning`); only a *declined* ack refuses (`AUTHORITY_UNACKNOWLEDGED`) and emits `EVT_SECURITY_POLICY_BLOCK`. `admin` is always authorized and emits `EVT_ADMIN_ACTION` each time (D-16 "always logged"). `DOC_FINALIZE_ARTIFACT` additionally runs the approver≠author check (soft; declined → `APPROVER_AUTHOR_CONFLICT_UNACKNOWLEDGED`).

### 2.4 Runners
`run_walking_skeleton(..., principal=...)` and `run_coverage_matrix(..., principal=...)` thread a verified principal through the whole grid — the **C1 exit demonstration**.

## 3. Soft, not hard (R6 — the line we hold)
Nothing here is hard RBAC. Single-user can't literally satisfy approver≠author, so the rule is a warn-with-ack the admin clicks through — **logged, never blocking** (everything stays `PRODUCT_TESTING_ONLY`, R5). Hard enforcement (refuse on mismatch, true multi-approver) activates at **multi-user (C4)**, owner's call on strictness then. Verified authority replaces the *declared-role* soft control on the verified path; the declared-role warn-with-ack stays for the unverified path.

## 4. Scope statement (R6)
Verified identity is **local** and **single-user** — a genuine credential check, not enterprise SSO/federation/MFA, and not a self-declaration dressed up as verification. The A09 §6.2 seam is the documented swap point for an external IdP (OIDC/SAML) later, behind the same `IdentityProvider` surface, with zero rework. The propose-vs-commit segregation (D-16) is **not** a GMP requirement and is deferred to production.

## 5. Checks (fresh-clone)
`pytest` → **61 passed** (41 prior + 20 M-IDENTITY). The 96-entry coverage matrix runs green **with identity verified** (admin principal); the soft path (no principal) is byte-identical and the S19 matrix fixture is unchanged. Pack untouched at `0ec3060`. **→ 🎉 C1 Engine complete.**
