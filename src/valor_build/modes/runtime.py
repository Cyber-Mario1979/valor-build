"""Runtime mode model M1-M4 (A18 §2).

The runtime axis is **strictly separate** (R1) from the engine-authority axis
(``DESIGN``/``EXECUTION``, a pack field) and the lifecycle axis (``ARCH``/``BUILD``).
Here, the action's **side-effect class** is what bounds each mode — not prose:

  * **M1 Advisory**      — READ_ONLY + VALIDATE_ONLY (+ non-binding generation, §3a)
  * **M2 Delivery Plan** — READ_ONLY + VALIDATE_ONLY + GENERATES_ARTIFACT (proposals)
  * **M3 WP Mode**       — every class, incl. STAGE_ONLY + MUTATES_TRUTH (the full path)
  * **M4 Project Mode**  — READ_ONLY projection only; NO truth gates (D-13)

M3 is the **only** mode that reaches MUTATES_TRUTH/STAGE_ONLY. The classes do the
enforcing: a mode that cannot reach a class refuses the action *before* dispatch.
"""
from __future__ import annotations

from enum import Enum


class RuntimeMode(str, Enum):
    M1 = "M1"  # Advisory
    M2 = "M2"  # Delivery Plan
    M3 = "M3"  # WP Mode
    M4 = "M4"  # Project Mode


# Reachable side-effect classes per runtime mode (A18 §2).
_REACHABLE: dict[RuntimeMode, frozenset[str]] = {
    RuntimeMode.M1: frozenset({"READ_ONLY", "VALIDATE_ONLY"}),
    RuntimeMode.M2: frozenset({"READ_ONLY", "VALIDATE_ONLY", "GENERATES_ARTIFACT"}),
    RuntimeMode.M3: frozenset(
        {"READ_ONLY", "VALIDATE_ONLY", "STAGE_ONLY", "MUTATES_TRUTH", "GENERATES_ARTIFACT"}
    ),
    RuntimeMode.M4: frozenset({"READ_ONLY"}),
}


class ModeReachError(RuntimeError):
    """Raised when an action's side-effect class is unreachable in the active mode."""

    def __init__(self, mode: RuntimeMode, side_effect: str):
        self.mode = mode
        self.side_effect = side_effect
        super().__init__(
            f"{side_effect} is unreachable in runtime mode {mode.value} "
            f"(reachable: {sorted(_REACHABLE[mode])})"
        )


def is_reachable(mode: RuntimeMode, side_effect: str) -> bool:
    return side_effect in _REACHABLE[mode]


def require_reachable(mode: RuntimeMode, side_effect: str) -> None:
    if not is_reachable(mode, side_effect):
        raise ModeReachError(mode, side_effect)
