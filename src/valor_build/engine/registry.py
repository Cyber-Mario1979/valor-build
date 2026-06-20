"""Contract registry loader (A16 §5).

The pack's ``CONTRACT_REGISTRY_v1.0.1.yaml`` is the **single authoritative**
action -> (side-effect class, confirm rule, result schema) map. A16 deliberately
does not transcribe it; the runtime loads it dynamically so a future pack v1.1.0
action is in-scope *by pattern* with zero edit here.

This module exposes a thin typed view: resolve an ``action_type`` or public alias
to its ``ActionSpec``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .. import pack_access

SIDE_EFFECT_CLASSES = {
    "READ_ONLY",
    "VALIDATE_ONLY",
    "STAGE_ONLY",
    "MUTATES_TRUTH",
    "GENERATES_ARTIFACT",
}


@dataclass(frozen=True)
class ActionSpec:
    action_type: str
    contract_id: str
    contract_version: str
    side_effect: str
    confirm: bool
    result_schema_ref: str | None
    aliases: tuple[str, ...] = field(default_factory=tuple)
    status: str = ""


class UnknownActionError(KeyError):
    """Raised when an action type/alias is not in the frozen registry."""


class ContractRegistry:
    def __init__(self, pack_root: Path | None = None):
        self.pack_root = pack_root or pack_access.find_pack_root()
        self._raw = pack_access.read_registry(self.pack_root)
        self.registry_version: str = self._raw.get("registry_version", "")
        self._by_type: dict[str, ActionSpec] = {}
        self._alias_to_type: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        for contract in self._raw.get("contracts", []):
            cid = contract["contract_id"]
            # Contract bodies carry their own version; the registry pins v1.0.1.
            cversion = self.registry_version
            for action in contract.get("actions", []):
                aliases = tuple(action.get("aliases", []) or ())
                spec = ActionSpec(
                    action_type=action["type"],
                    contract_id=cid,
                    contract_version=cversion,
                    side_effect=action["side_effect"],
                    confirm=bool(action.get("confirm", False)),
                    result_schema_ref=action.get("schema"),
                    aliases=aliases,
                    status=action.get("status", ""),
                )
                self._by_type[spec.action_type] = spec
                for alias in aliases:
                    self._alias_to_type[alias] = spec.action_type

    # -- public API ---------------------------------------------------------

    def resolve(self, action: str) -> ActionSpec:
        """Resolve a canonical type or a public alias to its ActionSpec."""
        if action in self._by_type:
            return self._by_type[action]
        if action in self._alias_to_type:
            return self._by_type[self._alias_to_type[action]]
        raise UnknownActionError(action)

    def all_actions(self) -> list[ActionSpec]:
        return list(self._by_type.values())

    def count_by_side_effect(self) -> dict[str, int]:
        counts = {cls: 0 for cls in SIDE_EFFECT_CLASSES}
        for spec in self._by_type.values():
            counts[spec.side_effect] = counts.get(spec.side_effect, 0) + 1
        return counts
