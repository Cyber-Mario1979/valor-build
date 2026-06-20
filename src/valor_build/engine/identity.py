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
