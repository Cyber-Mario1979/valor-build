"""Soft-control identity (B7 / G-07) — declared role-context capture + audit.

The pack defers cryptographic identity (A10 §3.2, §7) and instead specifies
**soft controls** while identity stays unverified in v0.1.x:

    A10 §7 — "Without identity verification, SEC applies soft controls:
      - require explicit role context for sensitive operations,
      - require confirmations for commit/finalize/export,
      - log the declared role in audit events.
      If a user requests an action inconsistent with declared role:
      warn and require explicit acknowledgement (policy choice)."

A09 §7.1 fixes the canonical audit ``actor`` shape as ``{role, name?, id?}`` and
A09 §6.2 names the integration seam: the system stores who approved but does not
validate real-world authority *"unless integrated with identity systems."*

This module implements the **soft** half (Option A / D-14):

* capture the declared role (and optional name) as an explicit, audited event;
* shape the envelope/stamp ``actor`` block as ``{role, name?, id?}`` — ``id`` is
  **reserved** (always ``None`` here) so the cryptographic-identity milestone
  (M-IDENTITY) can fill it later with **zero** schema change (the frozen
  ``contract_request`` ``actor`` block already permits ``role``/``name`` and
  ``additionalProperties: true``);
* a **warn-with-ack** hook for sensitive operations attempted without a declared
  role. Per D-14 this stays *soft* — it does not encode a role->action authority
  map (that, and real authority validation, arrive with M-IDENTITY). The hook is
  the single seam a richer predicate (a role map, or verified identity) swaps into.

Nothing here is a hard authorization gate; truth-store integrity and the human
confirmation gate remain the live controls (A17 §4).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid an import cycle at runtime
    from .audit import AuditLog


@dataclass(frozen=True)
class RoleContext:
    """A declared (unverified) actor identity. ``id`` is the crypto seam (M-IDENTITY)."""

    role: str
    name: str | None = None
    id: str | None = None  # reserved for cryptographic identity; always None in v0.x

    @property
    def declared(self) -> bool:
        """True when a non-blank role was actually declared."""
        return bool(self.role and self.role.strip())

    def actor_block(self) -> dict:
        """Build the A09 §7.1 ``actor`` block: role always; name/id only when set."""
        return actor_block(self.role, self.name, self.id)

    @classmethod
    def capture(
        cls,
        audit: "AuditLog",
        role: str,
        *,
        name: str | None = None,
        action_type: str = "",
        wp_id: str = "",
    ) -> "RoleContext":
        """Capture the declared role as an explicit, audited ``identity_context`` event.

        This is the soft control's "require explicit role context" step made visible
        on the single audit channel — one capture record per action (A09 §7.1).
        """
        ctx = cls(role=role, name=name, id=None)
        audit.emit(
            "identity_context",
            declared_role=ctx.role or "",
            actor_name=ctx.name or "",
            identity_verified=False,          # soft control: never cryptographically verified yet
            action_type=action_type,
            wp_id=wp_id,
        )
        return ctx


def actor_block(role: str, name: str | None = None, id: str | None = None) -> dict:
    """Canonical ``actor`` block ``{role, name?, id?}`` (A09 §7.1).

    Backward-compatible with the prior ``{"role": ...}`` envelope shape: name and id
    are emitted only when present, so an undeclared name/id yields identical bytes.
    """
    block: dict = {"role": role}
    if name:
        block["name"] = name
    if id:                                    # M-IDENTITY fills this; None in v0.x
        block["id"] = id
    return block


# Sensitive operations (A10 §7: "commit/finalize/export") are exactly the actions the
# frozen registry marks ``confirm: true`` — we key off the pack's own flag rather than
# enumerate a parallel list that would go stale at pack v1.1.0.
def requires_role_ack(confirm: bool, role: str) -> bool:
    """Warn-with-ack predicate (D-14, Option A — the soft baseline).

    Fire when a **sensitive** (confirm-required) action is attempted with **no
    declared role context**. Returns False otherwise — there is deliberately no
    role->action authority map here (that is Option B / M-IDENTITY). A richer
    predicate is a drop-in replacement for this one function.
    """
    if not confirm:
        return False
    return not (role and role.strip())


# ===========================================================================
# M-IDENTITY — verified local identity (C1 Step 3).
#
# Lifts the A10 §3.2/§7 deferral at the pack-named A09 §6.2 seam ("the system
# stores who approved but does not validate real-world authority *unless
# integrated with identity systems*"). This is that integration: a real
# credential is **presented and checked** against a local store, producing a
# verified ``Principal`` with a real ``actor.id`` and ``identity_verified=True``.
#
# Scope (R6): single-user, local, self-contained — no external IdP dragged into a
# PRODUCT_TESTING_ONLY build. The A09 §6.2 seam is the documented swap point for
# an external provider (OIDC/SAML) later, behind this same ``IdentityProvider``
# surface, with zero rework. "Verified" here means a genuine authentication event
# occurred — never a self-declaration dressed up as verification.
# ===========================================================================

import hashlib
import hmac
import os
from typing import Mapping

# D-16 role profiles (the authority tiers; see ``authority.py`` for the map).
PROFILE_READ_ONLY = "read-only"
PROFILE_EDITOR = "editor"
PROFILE_APPROVER = "approver"
PROFILE_ADMIN = "admin"
PROFILE_CQV = "CQV"            # CQV engineer — full WP truth path, solo
PROFILES = frozenset(
    {PROFILE_READ_ONLY, PROFILE_EDITOR, PROFILE_APPROVER, PROFILE_ADMIN, PROFILE_CQV}
)

_PBKDF2_ROUNDS = 120_000
_ID_PREFIX = "valor:uid:"      # real, stable principal id namespace


class AuthenticationError(RuntimeError):
    """A credential check failed — no verified principal is produced."""


@dataclass(frozen=True)
class Principal:
    """A **verified** actor identity, produced only by a real credential check.

    ``verified`` is always True here — a Principal cannot be constructed without
    passing ``LocalIdentityProvider.authenticate``. ``id`` is the populated
    M-IDENTITY seam (A09 §6.2); ``profile`` is the D-16 authority tier; ``role``
    is the A09 §7.1 display role string carried on the audit ``actor`` block.
    """

    id: str
    profile: str
    role: str
    name: str | None = None
    verified: bool = True

    def actor_block(self) -> dict:
        """A09 §7.1 ``{role, name?, id}`` — id always present for a verified actor."""
        return actor_block(self.role, self.name, self.id)


@dataclass(frozen=True)
class Credential:
    """A stored credential: a salted PBKDF2 hash of the secret + the actor's profile.

    The secret itself is never stored — only ``salt`` + ``hash``. ``profile`` must be
    one of the D-16 ``PROFILES``; ``role`` is the display role string (A09 §7.1).
    """

    username: str
    salt: bytes
    hash: bytes
    profile: str
    role: str
    name: str | None = None


def _derive(secret: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, _PBKDF2_ROUNDS)


def make_credential(
    username: str,
    secret: str,
    profile: str,
    *,
    role: str | None = None,
    name: str | None = None,
    salt: bytes | None = None,
) -> Credential:
    """Hash ``secret`` (never store it) and build a ``Credential``.

    ``role`` defaults to ``profile`` when not given. Raises if ``profile`` is not a
    known D-16 tier — an unknown profile must never silently become a credential.
    """
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}; expected one of {sorted(PROFILES)}")
    salt = salt if salt is not None else os.urandom(16)
    return Credential(
        username=username,
        salt=salt,
        hash=_derive(secret, salt),
        profile=profile,
        role=role or profile,
        name=name,
    )


def principal_id(username: str) -> str:
    """Deterministic, stable principal id for a username (the populated seam)."""
    return _ID_PREFIX + username


class CredentialStore:
    """In-memory local credential store (the swap point for a real directory/IdP).

    Single-user testing scope: a credential set is seeded explicitly. A production
    deployment swaps this for a file/DB/IdP-backed store behind the same surface
    (A09 §6.2) with zero caller change.
    """

    def __init__(self, credentials: Mapping[str, Credential] | None = None):
        self._by_user: dict[str, Credential] = dict(credentials or {})

    def add(self, cred: Credential) -> None:
        self._by_user[cred.username] = cred

    def get(self, username: str) -> Credential | None:
        return self._by_user.get(username)

    def __contains__(self, username: str) -> bool:
        return username in self._by_user


class LocalIdentityProvider:
    """Authenticates a (username, secret) against a ``CredentialStore``.

    A successful check emits an ``auth_event`` (login) on the single audit channel
    and returns a verified ``Principal`` carrying a real ``id``. A failed check
    emits an A10 §8 ``security_event`` (``EVT_SECURITY_POLICY_BLOCK``) and raises
    ``AuthenticationError`` — never returns an unverified principal.
    """

    def __init__(self, store: CredentialStore, audit: "AuditLog"):
        self.store = store
        self.audit = audit

    def authenticate(self, username: str, secret: str) -> Principal:
        cred = self.store.get(username)
        # Constant-time comparison; a missing user still does a derive-and-compare
        # against a throwaway salt so timing doesn't distinguish "no such user".
        if cred is None:
            _derive(secret, b"\x00" * 16)
            self._deny(username, "unknown actor")
            raise AuthenticationError("authentication failed")
        candidate = _derive(secret, cred.salt)
        if not hmac.compare_digest(candidate, cred.hash):
            self._deny(username, "credential mismatch")
            raise AuthenticationError("authentication failed")

        principal = Principal(
            id=principal_id(username),
            profile=cred.profile,
            role=cred.role,
            name=cred.name,
            verified=True,
        )
        self.audit.emit(
            "auth_event",
            event_type="EVT_AUTH_SUCCEEDED",
            actor_id=principal.id,
            profile=principal.profile,
            declared_role=principal.role,
            identity_verified=True,
        )
        return principal

    def _deny(self, username: str, rationale: str) -> None:
        # A10 §8 security-relevant audit event: rationale + affected artifact ids.
        self.audit.emit(
            "security_event",
            event_type="EVT_SECURITY_POLICY_BLOCK",
            phase="authentication",
            actor_id="",                       # no verified id — the point of the failure
            attempted_user=username,
            identity_verified=False,
            rationale=f"authentication denied: {rationale}",
            affected_artifacts=[],
        )
