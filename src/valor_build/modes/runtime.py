"""Runtime mode model M1-M4 (A18 §2).

The runtime axis is **strictly separate** (R1) from the engine-authority axis
(``DESIGN``/``EXECUTION``, a pack field) and the lifecycle axis (``ARCH``/``BUILD``).
Here, the action's **side-effect class** is what bounds each mode — not prose:

  * **M1 Advisory**      — READ_ONLY + VALIDATE_ONLY (advisory only; see D-15)
  * **M2 Delivery Plan** — READ_ONLY + VALIDATE_ONLY (advisory; see D-15)
  * **M3 WP Mode**       — every class, incl. STAGE_ONLY + MUTATES_TRUTH (the full path)
  * **M4 Project Mode**  — READ_ONLY + projection-only RPT artifacts; NO truth path (D-13)

M3 is the **only** mode that reaches MUTATES_TRUTH/STAGE_ONLY. The classes do the
enforcing: a mode that cannot reach a class refuses the action *before* dispatch.

**D-15 (owner, S19) — M1 & M2 are advisory; contracted generation is M3-only.**
A18 §2/§3a originally parked "non-binding generation" in M1 and listed
``GENERATES_ARTIFACT`` (plan proposals) under M2. The owner's runtime model is
cleaner and safer for regulated work: M1 and M2 are **both advisory** and reach
*only* ``READ_ONLY`` + ``VALIDATE_ONLY`` at the contracted-engine level. M2's
"plan" is an **uncontrolled workflow cheat-sheet** (and any example artifact, e.g.
a URS) — AI advisory narrative produced at the AI layer (C2), **not** a
``PLAN_GENERATE_PROPOSAL`` / ``DOC_GENERATE_DRAFT`` dispatch. The contracted CQV
plan (the scheduled task table that feeds RPT and the M4 projection) is produced
only on the **M3** truth path; consolidated ``RPT_GENERATE_*`` is **M4**. This
deletes A18's "contracted-but-non-binding, stamped PROPOSED" middle category, so a
schema-valid contracted object can never originate outside the truth path. A18
§2/§3a is amended to match.

**M4 projection reachability (reconciled to A18 §2, B5).** A18 §2 names M4's real
actions as *"consolidated ``RPT_GENERATE_*`` over the set"* — and those are the
``GENERATES_ARTIFACT`` class, not ``READ_ONLY``. The B4/B6 placeholder set
``{READ_ONLY}`` was therefore too tight to satisfy A18 §2 once M4 was actually
exercised. The grounded rule: **M4 reaches ``READ_ONLY`` plus the projection-only
subset of ``GENERATES_ARTIFACT`` — i.e. artifacts under the pack's RPT projection
contract** (``VALOR-contract-orch-rpt``, whose ``projection_policy`` fixes
``mutates_wp_truth: false``). It still reaches **none** of the truth path
(``MUTATES_TRUTH``/``STAGE_ONLY``) and **not** the per-WP planning/doc artifacts
(``PLAN_*``/``DOC_*``, which feed M3's truth path). This is a code↔doc reconcile to
A18 §2, not a new policy: D-13 ("no truth gates; sole control = scope-bound") is
preserved exactly. A tighter encoding (pure ``READ_ONLY`` M4, consolidation assembled
outside dispatch) is a one-line flip if the owner prefers it.
"""
from __future__ import annotations

from enum import Enum

# The pack's projection contract: its actions are projection-only by policy
# (``projection_policy.mutates_wp_truth: false``). The only GENERATES_ARTIFACT
# class M4 may reach is this contract's artifacts (A18 §2 / B5).
PROJECTION_CONTRACT_ID = "VALOR-contract-orch-rpt"


class RuntimeMode(str, Enum):
    M1 = "M1"  # Advisory
    M2 = "M2"  # Delivery Plan
    M3 = "M3"  # WP Mode
    M4 = "M4"  # Project Mode


# Reachable side-effect classes per runtime mode (A18 §2). M4's base set is
# READ_ONLY; its projection exception (RPT GENERATES_ARTIFACT) is contract-gated
# below — it cannot be expressed by class alone.
_REACHABLE: dict[RuntimeMode, frozenset[str]] = {
    RuntimeMode.M1: frozenset({"READ_ONLY", "VALIDATE_ONLY"}),
    RuntimeMode.M2: frozenset({"READ_ONLY", "VALIDATE_ONLY"}),  # D-15: advisory only
    RuntimeMode.M3: frozenset(
        {"READ_ONLY", "VALIDATE_ONLY", "STAGE_ONLY", "MUTATES_TRUTH", "GENERATES_ARTIFACT"}
    ),
    RuntimeMode.M4: frozenset({"READ_ONLY"}),
}


class ModeReachError(RuntimeError):
    """Raised when an action's side-effect class is unreachable in the active mode."""

    def __init__(self, mode: RuntimeMode, side_effect: str, contract_id: str | None = None):
        self.mode = mode
        self.side_effect = side_effect
        self.contract_id = contract_id
        detail = f"{side_effect} is unreachable in runtime mode {mode.value}"
        if mode is RuntimeMode.M4 and side_effect == "GENERATES_ARTIFACT":
            detail += (
                f" (only projection-only {PROJECTION_CONTRACT_ID} artifacts are reachable; "
                f"got contract {contract_id!r})"
            )
        else:
            detail += f" (reachable classes: {sorted(_REACHABLE[mode])})"
        super().__init__(detail)


def is_reachable(
    mode: RuntimeMode, side_effect: str, contract_id: str | None = None
) -> bool:
    """True iff ``side_effect`` (from ``contract_id``) is reachable in ``mode``.

    M4 takes a contract-aware exception: a ``GENERATES_ARTIFACT`` action is reachable
    only when it belongs to the projection contract (A18 §2 / B5). All other modes are
    decided purely by side-effect class.
    """
    if side_effect in _REACHABLE[mode]:
        return True
    if (
        mode is RuntimeMode.M4
        and side_effect == "GENERATES_ARTIFACT"
        and contract_id == PROJECTION_CONTRACT_ID
    ):
        return True
    return False


def require_reachable(
    mode: RuntimeMode, side_effect: str, contract_id: str | None = None
) -> None:
    if not is_reachable(mode, side_effect, contract_id):
        raise ModeReachError(mode, side_effect, contract_id)
