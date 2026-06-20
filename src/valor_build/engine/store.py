"""File/git WP truth store (A16 §3, G-06/D-03; pack A04_2 §4).

The pack fixes the *logical* truth model and constrains the *physical* store; A16
picks **file/git** because it natively satisfies the mandated constraint:

  * **append-only ID ledger** — every ID ever allocated is recorded and never reused;
  * **tombstoning** — deletions are tombstone records, never destructive edits;
  * **single commit chokepoint** — all ``MUTATES_TRUTH`` writes funnel through one path;
  * **advisory lock** around that path so concurrent writers serialise (lock-aware
    from day one; multi-user concurrency is the O3 *extension* on this seam, not a
    rewrite).

Physical layout under ``store_root``::

    ledger.jsonl     append-only: every id allocation + every truth transition
    ids.json         the allocated-id set (never-reused guard, mirror of the ledger)
    wp/<wp_id>.json  current materialised WP snapshot (derived; truth is the ledger)
    .lock            advisory lock file (fcntl where available)

The ledger is the source of truth; snapshots are a materialised convenience.
A git commit per chokepoint write is the production hook (``commit_hook``); the
default no-op keeps the skeleton dependency-light while preserving the chokepoint.
"""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

from .audit import now_utc

try:  # POSIX advisory lock; degrade gracefully elsewhere.
    import fcntl  # type: ignore
    _HAVE_FCNTL = True
except ImportError:  # pragma: no cover - Windows path
    _HAVE_FCNTL = False


class IdReuseError(RuntimeError):
    """Raised if an already-allocated ID is allocated again. IDs are never reused."""


class TombstonedError(RuntimeError):
    """Raised on any write against a tombstoned entity."""


class WPStore:
    def __init__(self, store_root: Path, commit_hook: Callable[[str], None] | None = None):
        self.root = Path(store_root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "wp").mkdir(exist_ok=True)
        self.ledger_path = self.root / "ledger.jsonl"
        self.ids_path = self.root / "ids.json"
        self.lock_path = self.root / ".lock"
        # Production hook: a real git commit per chokepoint write. Default no-op.
        self._commit_hook = commit_hook or (lambda msg: None)
        if not self.ids_path.exists():
            self.ids_path.write_text(json.dumps({"allocated": [], "tombstoned": []}), encoding="utf-8")

    # -- advisory lock (the single-writer seam) -----------------------------

    @contextmanager
    def _advisory_lock(self):
        with self.lock_path.open("w") as handle:
            if _HAVE_FCNTL:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if _HAVE_FCNTL:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    # -- id ledger ----------------------------------------------------------

    def _read_ids(self) -> dict:
        return json.loads(self.ids_path.read_text(encoding="utf-8"))

    def allocate_id(self, entity_id: str) -> None:
        """Record a never-before-seen ID. Raises IdReuseError on reuse."""
        ids = self._read_ids()
        if entity_id in ids["allocated"]:
            raise IdReuseError(f"id already allocated, never reuse: {entity_id}")
        ids["allocated"].append(entity_id)
        self.ids_path.write_text(json.dumps(ids), encoding="utf-8")
        self._append_ledger({"event": "ID_ALLOCATED", "entity_id": entity_id})

    def is_tombstoned(self, entity_id: str) -> bool:
        return entity_id in self._read_ids()["tombstoned"]

    def tombstone(self, entity_id: str, reason: str) -> None:
        with self._advisory_lock():
            ids = self._read_ids()
            if entity_id not in ids["tombstoned"]:
                ids["tombstoned"].append(entity_id)
                self.ids_path.write_text(json.dumps(ids), encoding="utf-8")
            self._append_ledger({"event": "TOMBSTONED", "entity_id": entity_id, "reason": reason})
            self._commit_hook(f"tombstone {entity_id}")

    def _append_ledger(self, record: dict) -> None:
        record = {"ts": now_utc(), **record}
        with self.ledger_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")

    # -- the single commit chokepoint --------------------------------------

    def commit_truth(self, wp_id: str, transition: str, wp_snapshot: dict) -> dict:
        """The one write path every ``MUTATES_TRUTH`` action funnels through.

        Lock-aware, append-only: records the transition to the ledger, materialises
        the WP snapshot, and fires the commit hook. Refuses writes to a tombstoned WP.
        """
        with self._advisory_lock():
            if self.is_tombstoned(wp_id):
                raise TombstonedError(f"cannot write tombstoned WP: {wp_id}")
            self._append_ledger({"event": "TRUTH_TRANSITION", "wp_id": wp_id, "transition": transition})
            snap_path = self.root / "wp" / f"{wp_id}.json"
            snap_path.write_text(json.dumps(wp_snapshot, indent=2, sort_keys=True), encoding="utf-8")
            self._commit_hook(f"{transition} {wp_id}")
            return {"wp_id": wp_id, "transition": transition, "snapshot_path": str(snap_path)}

    # -- staging area (non-truth; STAGE_ONLY + artifact intermediates) ------

    def _staging_path(self, wp_id: str, kind: str) -> Path:
        staging = self.root / "staging"
        staging.mkdir(exist_ok=True)
        return staging / f"{wp_id}-{kind}.json"

    def _write_staging(self, wp_id: str, kind: str, obj: dict) -> None:
        self._staging_path(wp_id, kind).write_text(
            json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8"
        )

    def _read_staging(self, wp_id: str, kind: str) -> dict:
        return json.loads(self._staging_path(wp_id, kind).read_text(encoding="utf-8"))

    def stage_set(self, wp_id: str, staged: dict) -> None:
        self._write_staging(wp_id, "staged", staged)

    def load_staged(self, wp_id: str) -> dict:
        return self._read_staging(wp_id, "staged")

    def stage_plan(self, wp_id: str, plan: dict) -> None:
        self._write_staging(wp_id, "plan", plan)

    def load_plan(self, wp_id: str) -> dict:
        return self._read_staging(wp_id, "plan")

    def stage_doc(self, wp_id: str, doc: dict) -> None:
        self._write_staging(wp_id, "doc", doc)

    def load_doc(self, wp_id: str) -> dict:
        return self._read_staging(wp_id, "doc")

    # -- read path ----------------------------------------------------------

    def load_wp(self, wp_id: str) -> dict | None:
        snap_path = self.root / "wp" / f"{wp_id}.json"
        if not snap_path.exists():
            return None
        return json.loads(snap_path.read_text(encoding="utf-8"))

    def ledger(self) -> list[dict]:
        if not self.ledger_path.exists():
            return []
        return [json.loads(line) for line in self.ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
