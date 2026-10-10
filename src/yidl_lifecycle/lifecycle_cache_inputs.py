"""Explicit generation-input schema; no generated template imports."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import os

from yidl_cache import CacheIdentityError
from yidl_lifecycle.lifecycle_harvester import HarvestedLifecycle
from yidl_lifecycle.transaction_yidl import DEFAULT_TRANSACTION

_CLASS_KEYS = frozenset(
    {
        "class_id",
        "class_name",
        "class_order",
        "module_name",
        "state_class_name",
        "facade_base_class_name",
        "current_facade_class_name",
        "working_facade_class_name",
        "lifecycle_definition_param_name",
        "annotations_param_name",
        "tx_keys_param_name",
        "lifecycle_field_names",
    }
)
_RUNTIME_FIELD_KEYS = frozenset(
    {"default_value", "default_factory", "working_default_factory", "freeze", "thaw"}
)
_FIELD_KEYS = _RUNTIME_FIELD_KEYS | frozenset(
    {
        "field_id",
        "field_owner",
        "field_name",
        "field_order",
        "field_kind",
        "binding_shape",
        "compare",
        "mutable",
        "annotation",
        "init",
        "has_default",
        "default_value_param_name",
        "has_default_factory",
        "allow_self_factory",
        "default_factory_param_names",
        "default_factory_param_name",
        "has_working_default_factory",
        "working_default_factory_param_names",
        "working_default_factory_param_name",
        "tx_key_key",
        "value_slot_name",
        "current_slot_name",
        "working_slot_name",
        "staged_slot_name",
        "has_freeze",
        "freeze_param_name",
        "has_thaw",
        "thaw_param_name",
        "has_optional_none",
    }
)
_METHOD_KEYS = frozenset(
    {
        "method_id",
        "method_owner",
        "method_name",
        "method_kind",
        "tx_key_key",
        "tx_index",
        "declaration_order",
    }
)
_MAX_INPUT_BYTES = 1024 * 1024


def generation_digest(harvested: HarvestedLifecycle) -> str:
    """Hash only audited generation inputs, preserving ordered facts and key topology."""
    if harvested.lifecycle_definition.get("version") != 1:
        raise CacheIdentityError("unsupported lifecycle metadata schema")
    if (
        max(
            len(harvested.field_facts),
            len(harvested.transaction_method_facts),
            len(harvested.tx_keys),
        )
        > 20000
    ):
        raise CacheIdentityError("lifecycle fact count exceeds the cache limit")
    _check_schema(harvested.class_fact, _CLASS_KEYS)
    # Use the same hash/equality grouping as generation, never key repr or identity.
    key_indexes = {key: index for index, key in enumerate(harvested.tx_keys)}
    if (
        len(key_indexes) != len(harvested.tx_keys)
        or DEFAULT_TRANSACTION not in key_indexes
    ):
        raise CacheIdentityError("unsupported transaction topology")

    fields = []
    for fact in harvested.field_facts:
        _check_schema(fact, _FIELD_KEYS)
        if type(fact["annotation"]) is not str:
            raise CacheIdentityError("cache requires exact string field annotations")
        projected = {
            name: value
            for name, value in fact.items()
            if name not in _RUNTIME_FIELD_KEYS
        }
        key = fact["tx_key_key"]
        if fact["field_kind"] in {"managed", "owned", "transient"}:
            projected["tx_key_key"] = _key_index(
                key_indexes, DEFAULT_TRANSACTION if key is None else key
            )
        else:
            if key is not None:
                raise CacheIdentityError("unsupported nontransactional key topology")
            projected["tx_key_key"] = None
        fields.append(_fact_input(projected))

    methods = []
    for fact in harvested.transaction_method_facts:
        _check_schema(fact, _METHOD_KEYS)
        projected = dict(fact)
        projected["tx_key_key"] = _key_index(key_indexes, fact["tx_key_key"])
        methods.append(_fact_input(projected))

    inputs = {
        "class": _fact_input(harvested.class_fact),
        "fields": fields,
        "methods": methods,
        "keys": [len(key_indexes), key_indexes[DEFAULT_TRANSACTION]],
        "builder_parameters": _literal(tuple(sorted(harvested.build_kwargs))),
        "engine_environment": sorted(
            (name, value)
            for name, value in os.environ.items()
            if name.startswith("ASTICHI_")
        ),
    }
    encoded = json.dumps(
        inputs, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    if len(encoded) > _MAX_INPUT_BYTES:
        raise CacheIdentityError("lifecycle generation inputs exceed the cache limit")
    return hashlib.sha256(encoded).hexdigest()


def _check_schema(fact: Mapping[str, object], expected: frozenset[str]) -> None:
    if fact.keys() != expected:
        raise CacheIdentityError("unsupported lifecycle fact schema")


def _key_index(indexes: Mapping[object, int], key: object) -> int:
    try:
        return indexes[key]
    except (KeyError, TypeError) as error:
        raise CacheIdentityError("unsupported transaction topology") from error


def _fact_input(fact: Mapping[str, object]) -> list[object]:
    return [[name, _literal(value)] for name, value in sorted(fact.items())]


def _literal(value: object, depth: int = 0) -> object:
    if depth > 16:
        raise CacheIdentityError("lifecycle input nesting exceeds the cache limit")
    if value is None:
        return ["none"]
    if type(value) is bool:
        return ["bool", value]
    if type(value) is int and value.bit_length() <= 64:
        return ["int", value]
    if type(value) is str and len(value) <= 65536:
        return ["str", value]
    if type(value) is tuple and len(value) <= 20000:
        return ["tuple", [_literal(item, depth + 1) for item in value]]
    raise CacheIdentityError("unsupported lifecycle generation input type")
