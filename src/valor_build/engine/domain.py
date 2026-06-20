"""PE-HIGH domain access + CAL-WORKWEEK calendar (R4: the single live domain).

PE-HIGH is the only domain with a shipped pool/profile/preset
(``TP/PROF/PS-PE-HIGH``) and therefore the only end-to-end-exercisable surface
today (Phase-B plan R4). This module reads that governed trio **directly from the
pinned pack** — no invented task data — and resolves profile durations for the
deterministic scheduler.

The calendar is a thin CAL-WORKWEEK forward calculator (Mon-Fri working days); it is
deliberately minimal — the walking skeleton proves the *path*, not a full calendar
engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import yaml

from .. import pack_access

PRESET_RELPATH = "libraries/preset_library/PS-PE-HIGH_v1.0.1.yaml"
POOL_RELPATH = "libraries/task_pool/TP-PE-HIGH_v1.0.1.yaml"
PROFILE_RELPATH = "libraries/profile_library/PROF-PE-HIGH_v1.0.1.yaml"


@dataclass
class PEHighDomain:
    preset: dict
    pool: dict
    profile: dict

    @classmethod
    def load(cls, pack_root: Path | None = None) -> "PEHighDomain":
        root = pack_root or pack_access.find_pack_root()
        load = lambda rel: yaml.safe_load((root / rel).read_text(encoding="utf-8"))
        return cls(load(PRESET_RELPATH), load(POOL_RELPATH), load(PROFILE_RELPATH))

    # -- bindings -----------------------------------------------------------

    @property
    def bindings(self) -> dict:
        return self.preset["bindings"]

    @property
    def calendar_logic_ref(self) -> dict:
        return dict(self.bindings["calendar_logic_ref"])

    @property
    def standards_bundle_ref(self) -> dict:
        return dict(self.bindings["standards_bundle_ref"])

    # -- tasks --------------------------------------------------------------

    def pool_tasks(self) -> list[dict]:
        return self.pool["tasks"]

    def task(self, atomic_task_id: str) -> dict:
        for t in self.pool_tasks():
            if t["atomic_task_id"] == atomic_task_id:
                return t
        raise KeyError(atomic_task_id)

    def resolve_duration(self, profile_key: str) -> tuple[float, str]:
        """Return (value, unit) for a profile duration key, read from PROF-PE-HIGH."""
        entry = self.profile["entries"][profile_key]
        cell = entry["value_table"][0]
        return float(cell["value"]), cell["unit"]


# -- CAL-WORKWEEK working-day calendar -------------------------------------

def _is_working_day(d: date) -> bool:
    return d.weekday() < 5  # Mon-Fri


def next_working_day(d: date) -> date:
    while not _is_working_day(d):
        d += timedelta(days=1)
    return d


def add_working_days(start: date, n_working_days: int) -> date:
    """Inclusive forward span: a 1-day task starts and finishes the same working day."""
    d = next_working_day(start)
    remaining = max(int(n_working_days), 1) - 1
    while remaining > 0:
        d += timedelta(days=1)
        if _is_working_day(d):
            remaining -= 1
    return d
