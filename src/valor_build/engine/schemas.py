"""Schema registry + fail-closed validator (A16 §2, §4).

Builds a `referencing` registry keyed on each schema's **absolute ``$id``** and
provides draft-07 validation against it. Every cross-boundary call is validated
*before* it is allowed to take effect; a validation miss is a **refusal**, never a
warning-and-proceed (A16 §2, fail-closed).

**The A3 lesson (load-bearing).** The pack's ``$id``s use a custom ``valor://``
scheme and its cross-file ``$ref``s are *relative* (e.g. ``task_schema.json``,
``../objects/document_metadata_schema.json``). ``urllib.parse.urljoin`` does **not**
apply a base URI for an unknown scheme, so naive relative-ref following leaves those
refs ``Unresolvable``. We fix it at load time exactly as the A3 harness did: rewrite
every relative file-``$ref`` to the target's absolute registered ``$id`` before the
registry is built. Refs then resolve against the registry, not the filesystem.
"""
from __future__ import annotations

import json
import posixpath
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

from .. import pack_access

VALOR_SCHEME = "valor://"


class SchemaValidationError(Exception):
    """A fail-closed validation refusal. Carries the schema id + error list."""

    def __init__(self, schema_id: str, errors: list[str]):
        self.schema_id = schema_id
        self.errors = errors
        super().__init__(f"validation failed against {schema_id}: {errors}")


def _abs_id_for_ref(base_id: str, ref: str) -> str:
    """Resolve a relative file ``$ref`` to an absolute ``valor://`` ``$id``.

    Manual path-join under the ``valor://`` authority, because urljoin won't.
    Fragment-only refs (``#/...``) and already-absolute refs pass through.
    """
    if ref.startswith(VALOR_SCHEME) or ref.startswith("#") or "://" in ref:
        return ref
    base_path = base_id[len(VALOR_SCHEME):]  # e.g. schemas/objects/work_package_schema.json
    base_dir = posixpath.dirname(base_path)
    joined = posixpath.normpath(posixpath.join(base_dir, ref))
    return VALOR_SCHEME + joined


def _rewrite_refs(node, base_id: str):
    """Recursively rewrite every relative ``$ref`` in a schema to an absolute ``$id``."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                node[key] = _abs_id_for_ref(base_id, value)
            else:
                _rewrite_refs(value, base_id)
    elif isinstance(node, list):
        for item in node:
            _rewrite_refs(item, base_id)


class SchemaRegistry:
    """Absolute-``$id`` schema registry over the pinned pack's schemas."""

    def __init__(self, pack_root: Path | None = None):
        self.pack_root = pack_root or pack_access.find_pack_root()
        self._schemas: dict[str, dict] = {}
        self._registry: Registry = self._build()

    def _build(self) -> Registry:
        resources = []
        # First pass: load + index every schema by its declared $id.
        for path in pack_access.iter_schema_files(self.pack_root):
            with path.open("r", encoding="utf-8") as fh:
                schema = json.load(fh)
            schema_id = schema.get("$id")
            if not schema_id:
                continue  # index.json and non-$id assets are not validation targets
            self._schemas[schema_id] = schema
        # Second pass: rewrite relative refs to absolute ids, then register.
        for schema_id, schema in self._schemas.items():
            _rewrite_refs(schema, schema_id)
            resources.append((schema_id, Resource(contents=schema, specification=DRAFT7)))
        return Registry().with_resources(resources)

    # -- public API ---------------------------------------------------------

    def known_ids(self) -> set[str]:
        return set(self._schemas)

    def id_for_ref(self, result_schema_ref: str) -> str:
        """Map a registry ``schema``/``result_schema_ref`` path to its ``valor://`` id.

        The registry stores refs as relative pack paths (``schemas/objects/...``);
        schema ``$id``s are ``valor://schemas/objects/...``. Normalise to the id.
        """
        if result_schema_ref.startswith(VALOR_SCHEME):
            return result_schema_ref
        return VALOR_SCHEME + result_schema_ref.lstrip("/")

    def validate(self, instance, schema_ref: str) -> None:
        """Fail-closed validation. Raises SchemaValidationError on any violation."""
        schema_id = self.id_for_ref(schema_ref)
        schema = self._schemas.get(schema_id)
        if schema is None:
            raise SchemaValidationError(schema_id, [f"unknown schema id: {schema_id}"])
        validator = Draft7Validator(schema, registry=self._registry)
        errors = [
            f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
        ]
        if errors:
            raise SchemaValidationError(schema_id, errors)

    def is_valid(self, instance, schema_ref: str) -> bool:
        try:
            self.validate(instance, schema_ref)
            return True
        except SchemaValidationError:
            return False
