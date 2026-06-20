"""Governance gates (A17; pack A04_1 §4.1).

The pack's **five** canonical gates, in flow order:

    GATE-Stage -> GATE-Commit -> GATE-Plan -> GATE-Apply -> GATE-Export

Each gate **evaluates** an entry condition and the runtime **records** the verdict.
The mode decides what to *do* with that verdict (A17 §3/§5):

  * **BUILD** — a ``WOULD_BLOCK`` verdict is logged with its reason and the flow
    **proceeds**. Development is never halted by a governance stop.
  * **LIVE**  — a ``WOULD_BLOCK`` becomes ``BLOCKED`` and the flow **halts**.

The pack itself always evaluates and returns its verdict unchanged (R2); only this
runtime layer *around* the pack branches on mode. No gate is ever skipped inside L1.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Canonical five gates (A04_1 §4.1). The shorthand "Stage/Validate/Commit/Apply/
# Finalize/Close" is superseded (A17 §2): Validate is the validation posture,
# Finalize is the DOC DRAFT->FINAL step, Close is architecture closure.
GATE_STAGE = "GATE-Stage"
GATE_COMMIT = "GATE-Commit"
GATE_PLAN = "GATE-Plan"
GATE_APPLY = "GATE-Apply"
GATE_EXPORT = "GATE-Export"
CANONICAL_GATES = (GATE_STAGE, GATE_COMMIT, GATE_PLAN, GATE_APPLY, GATE_EXPORT)


class Lifecycle(str, Enum):
    BUILD = "BUILD"
    LIVE = "LIVE"


class GateBlocked(RuntimeError):
    """Raised only in LIVE when a gate's entry condition is not met."""

    def __init__(self, gate: str, reason: str):
        self.gate = gate
        self.reason = reason
        super().__init__(f"{gate} BLOCKED: {reason}")


@dataclass
class GateVerdict:
    gate: str
    entry_condition_met: bool
    verdict: str          # "PASS" | "WOULD_BLOCK"
    reason: str
    proceeded: bool


def evaluate_gate(
    gate: str,
    entry_condition_met: bool,
    lifecycle: Lifecycle,
    reason: str = "",
) -> GateVerdict:
    """Evaluate one gate under the active lifecycle mode.

    In LIVE, an unmet entry condition raises GateBlocked (flow halts). In BUILD it
    is logged as WOULD_BLOCK and the flow proceeds. The verdict object is the audit
    record (A17 §3) regardless of outcome.
    """
    if entry_condition_met:
        return GateVerdict(gate, True, "PASS", "", proceeded=True)

    if lifecycle is Lifecycle.LIVE:
        # Record the would-block, then halt.
        raise GateBlocked(gate, reason or "entry condition not met")

    # BUILD: log-only, proceed.
    return GateVerdict(gate, False, "WOULD_BLOCK", reason or "entry condition not met", proceeded=True)
