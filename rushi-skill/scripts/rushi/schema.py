"""微型 JSON Schema 校验器（支持本规范使用的子集）。"""

from __future__ import annotations

import re
from typing import Any


def _type_ok(value: Any, type_name: str) -> bool:
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "null":
        return value is None
    return True


def validate(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """返回错误列表；空列表表示通过。"""
    errors: list[str] = []

    if "type" in schema and not _type_ok(instance, schema["type"]):
        errors.append(f"{path}: 期望类型 {schema['type']}，实际 {type(instance).__name__}")
        return errors

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: 期望常量 {schema['const']!r}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: 长度 {len(instance)} < minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: 长度 {len(instance)} > maxLength {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: 不匹配 pattern {schema['pattern']!r}")

    if isinstance(instance, list):
        if "items" in schema:
            for i, item in enumerate(instance):
                errors.extend(validate(item, schema["items"], f"{path}[{i}]"))
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: 数组长度 {len(instance)} < minItems {schema['minItems']}")

    if isinstance(instance, dict):
        for prop in schema.get("required", []):
            if prop not in instance:
                errors.append(f"{path}: 缺少必填字段 {prop!r}")
        for key, value in instance.items():
            prop_schema = schema.get("properties", {}).get(key)
            if prop_schema is not None:
                errors.extend(validate(value, prop_schema, f"{path}.{key}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: 未声明字段 {key!r}")
        for key, value in schema.get("properties", {}).items():
            if key in instance and "enum" in value and instance[key] not in value["enum"]:
                errors.append(
                    f"{path}.{key}: {instance[key]!r} 不在枚举 {value['enum']} 中"
                )

    if "oneOf" in schema:
        passed = sum(1 for sub in schema["oneOf"] if not validate(instance, sub, path))
        if passed != 1:
            errors.append(f"{path}: oneOf 命中 {passed} 个（应为 1）")

    return errors


def validate_file(instance_path, schema_path) -> list[str]:
    import json

    from pathlib import Path

    instance = json.loads(Path(instance_path).read_text(encoding="utf-8"))
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    return validate(instance, schema)
