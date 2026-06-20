"""Locate and read the frozen VALOR Architecture Pack (Layer 1).

The pack is consumed **read-only**, pinned as a git submodule at v1.0.1 / ``0ec3060``
(see ``BUILD_STRATEGY.md`` and A16 §1). This module does the bare filesystem access:
find the pack root, read the contract registry and the schema files. Nothing here
edits the pack — that is an R2 invariant.

Resolution order for the pack root:
  1. ``$VALOR_PACK_ROOT`` if set (used by tests / non-standard layouts),
  2. a ``pack/`` directory found by walking up from this file to the repo root.

A valid pack root is any directory containing
``contracts/CONTRACT_REGISTRY_v1.0.1.yaml``.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

REGISTRY_RELPATH = "contracts/CONTRACT_REGISTRY_v1.0.1.yaml"
PINNED_PACK_COMMIT = "0ec3060be738025891b8bed9fc7ba3a804e9402d"
PACK_VERSION = "v1.0.1"


class PackNotFoundError(RuntimeError):
    """Raised when the read-only pack submodule cannot be located."""


def _is_pack_root(candidate: Path) -> bool:
    return (candidate / REGISTRY_RELPATH).is_file()


def find_pack_root() -> Path:
    """Return the absolute path to the read-only pack root.

    Raises PackNotFoundError with actionable remediation if the submodule has
    not been initialised (``git submodule update --init pack``).
    """
    env = os.environ.get("VALOR_PACK_ROOT")
    if env:
        root = Path(env).expanduser().resolve()
        if _is_pack_root(root):
            return root
        raise PackNotFoundError(
            f"VALOR_PACK_ROOT={env!r} does not contain {REGISTRY_RELPATH}"
        )

    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "pack"
        if _is_pack_root(candidate):
            return candidate.resolve()

    raise PackNotFoundError(
        "Frozen pack not found. Initialise the read-only submodule at the pin:\n"
        "  git submodule update --init --depth 1 pack\n"
        f"(expected pack/{REGISTRY_RELPATH}; pinned at {PINNED_PACK_COMMIT})"
    )


def read_registry(pack_root: Path | None = None) -> dict:
    """Load and parse the contract registry YAML (the authoritative action map)."""
    root = pack_root or find_pack_root()
    with (root / REGISTRY_RELPATH).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def iter_schema_files(pack_root: Path | None = None):
    """Yield every ``*.json`` schema path under ``schemas/`` in the pack."""
    root = pack_root or find_pack_root()
    yield from sorted((root / "schemas").rglob("*.json"))
