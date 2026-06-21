"""Authority policy — the D-16 soft role->action map (the B7 §4 / OC-2 home).

This is the role->action authority map B7 deferred and D-16 (Session 20) adopted:
a **soft, multi-approver** map keyed to the frozen registry's own ``confirm:true``
flag, validated only for a **verified** ``Principal`` (M-IDENTITY). It is the richer
predicate that drops into the single ``requires_role_ack`` seam B7 left open.

D-16 invariants enforced here:

* **Soft, not RBAC (R6).** A profile that lacks authority for a sensitive action is
  **warned-with-ack**, never hard-refused, in single-user testing. The caller turns
  a not-authorized verdict into a warn-with-ack; only a *declined* ack refuses. Hard
  enforcement (refuse on mismatch) is C4's call, not installed here.
* **admin does everything, always logged.** ``admin`` is authorized for every action
  and the caller emits an admin-action security event each time.
* **CQV engineer runs the WP truth path solo.** No task-path segregation — the pack
  imposes none (A09 §6.2 role expectations are "typical," not enforced).
* **Controlled documents are segregated.** ``DOC_FINALIZE_ARTIFACT`` needs an
  ``approver`` (not an ``editor``); approval is separately subject to the
  **approver(s) != author** multi-approver rule (``approver_author_conflict``).

The map keys off ``spec.confirm`` (the pack's own "sensitive" flag) + ``action_type``,
never a parallel enumerated action list — so a pack v1.1.0 action is classified by
pattern with zero edit here (the same enumerate-vs-represent discipline as the
contract map).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .identity import (
    PROFILE_ADMIN,
    PROFILE_APPROVER,
    PROFILE_CQV,
    PROFILE_EDITOR,
    PROFILE_READ_ONLY,
    PROFILES,
)
from .registry import ActionSpec

# The one controlled-document approval action (segregated; approver != author).
DOC_APPROVAL_ACTION = "DOC_FINALIZE_ARTIFACT"

# Who may perform each *sensitive* (confirm:true) action category, by profile.
# admin is handled separately (authorized for everything, always logged).
_DOC_APPROVAL_PROFILES = frozenset({PROFILE_APPROVER, PROFILE_ADMIN})
_TASK_PATH_PROFILES = frozenset({PROFILE_EDITOR, PROFILE_CQV, PROFILE_ADMIN})


@dataclass(frozen=True)
class AuthorityVerdict:
    """Outcome of an authority check. ``authorized`` False is a *soft* signal."""

    authorized: bool
    profile: str
    action_type: str
    category: str          # "non_sensitive" | "doc_approval" | "task_path"
    reason: str

    @property
    def requires_ack(self) -> bool:
        """A not-authorized verdict on a sensitive action -> warn-with-ack (soft)."""
        return not self.authorized


def _category(spec: ActionSpec) -> str:
    if not spec.confirm:
        return "non_sensitive"
    if spec.action_type == DOC_APPROVAL_ACTION:
        return "doc_approval"
    return "task_path"


def authorize(profile: str, spec: ActionSpec) -> AuthorityVerdict:
    """Validate real-world authority for ``profile`` against ``spec`` (D-16, soft).

    Non-sensitive (``confirm:false``) actions are never authority-gated — any
    verified actor, including ``read-only``, may run them. Sensitive actions are
    classified and checked against the D-16 map. ``admin`` is always authorized.
    """
    category = _category(spec)
    if category == "non_sensitive":
        return AuthorityVerdict(
            True, profile, spec.action_type, category,
            "non-sensitive action — no authority gate",
        )

    if profile == PROFILE_ADMIN:
        return AuthorityVerdict(
            True, profile, spec.action_type, category,
            "admin — authorized for all actions (always logged)",
        )

    if category == "doc_approval":
        ok = profile in _DOC_APPROVAL_PROFILES
        reason = (
            "approver authority — may finalize controlled documents" if ok
            else f"profile {profile!r} may not approve/finalize controlled documents "
                 "(approver authority required)"
        )
        return AuthorityVerdict(ok, profile, spec.action_type, category, reason)

    # task_path
    ok = profile in _TASK_PATH_PROFILES
    reason = (
        "authorized for the WP task path" if ok
        else f"profile {profile!r} is not authorized for the WP task path"
    )
    return AuthorityVerdict(ok, profile, spec.action_type, category, reason)


# -- approver != author (multi-approver, controlled documents) --------------

@dataclass(frozen=True)
class Approval:
    """One signed, verified approval event (engine/audit-layer record).

    The frozen ``doc.actors.approver`` is a single string; the engine keeps the full
    signed approver **set** in its own audit record (``additionalProperties:true`` /
    zero pack change). Each entry is a distinct verified, logged approval.
    """

    approver_id: str
    role: str
    name: str | None = None


@dataclass(frozen=True)
class ApprovalDecision:
    """Result of the approver(s) != author check for a controlled-document finalize."""

    conflict: bool                 # True when an approver id == the author id
    author_id: str
    approver_ids: tuple[str, ...]
    reason: str

    @property
    def requires_ack(self) -> bool:
        return self.conflict


def evaluate_approval(
    author_id: str,
    approvers: Iterable[Approval],
) -> ApprovalDecision:
    """Check approver(s) != author over the full signed approver set (D-16).

    Single-user reality: author == approver, so ``conflict`` is True and the caller
    raises a soft warn-with-ack the admin clicks through (logged, non-blocking, R5).
    Hard enforcement (true multi-approver, refuse on conflict) activates at C4.
    """
    ids = tuple(a.approver_id for a in approvers)
    conflict = author_id in ids
    if conflict:
        reason = (
            "approver(s) must differ from the author — single-user: author is also an "
            "approver (soft warn-with-ack; hard multi-approver enforcement at C4)"
        )
    else:
        reason = "approver(s) distinct from author"
    return ApprovalDecision(conflict, author_id, ids, reason)
