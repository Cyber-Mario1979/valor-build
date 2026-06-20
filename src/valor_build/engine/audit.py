"""Single audit channel (A16 §4, A17 §3, A18 §3).

Every auditable event — AI-call provenance, gate outcomes, output stamps — rides
**one** channel, not parallel logs. That is what makes a BUILD log directly
comparable to a LIVE one and what lets "the same path runs gated later" be auditable.

Records are append-only JSONL. Hashing is sha256 over canonical JSON.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_hash(obj: Any) -> str:
    """sha256 over canonical (sorted-key, compact) JSON of ``obj``."""
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


class AuditLog:
    """Append-only audit channel. Writes JSONL and keeps an in-memory mirror."""

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else None
        self.records: list[dict] = []

    def emit(self, kind: str, **fields) -> dict:
        record = {"kind": kind, "timestamp": now_utc(), **fields}
        self.records.append(record)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, sort_keys=True, default=str) + "\n")
        return record

    def of_kind(self, kind: str) -> list[dict]:
        return [r for r in self.records if r["kind"] == kind]
