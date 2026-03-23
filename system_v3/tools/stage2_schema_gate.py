#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    return True


def _minimal_validate(value: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: const_mismatch expected={schema['const']!r}")
        return

    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _type_ok(value, expected_type):
        errors.append(f"{path}: type_mismatch expected={expected_type}")
        return

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: enum_mismatch")
        return

    if isinstance(value, str):
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.match(pattern, value) is None:
            errors.append(f"{path}: pattern_mismatch")

    if isinstance(value, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path}: minItems_violation expected>={min_items}")
        items_schema = schema.get("items")
        if isinstance(items_schema, dict):
            for index, item in enumerate(value):
                _minimal_validate(item, items_schema, f"{path}[{index}]", errors)

    if isinstance(value, dict):
        properties = schema.get("properties")
        required = schema.get("required")
        if isinstance(required, list):
            for key in required:
                if isinstance(key, str) and key not in value:
                    errors.append(f"{path}: missing_required_field:{key}")
        if schema.get("additionalProperties") is False and isinstance(properties, dict):
            for key in value.keys():
                if key not in properties:
                    errors.append(f"{path}: unknown_field:{key}")
        if isinstance(properties, dict):
            for key, prop_schema in properties.items():
                if key in value and isinstance(prop_schema, dict):
                    _minimal_validate(value[key], prop_schema, f"{path}.{key}", errors)


def _validate_with_jsonschema_or_fallback(instance: Any, schema: dict[str, Any]) -> list[str]:
    try:
        import jsonschema

        validator = jsonschema.Draft202012Validator(schema)
        return sorted([f"{'/'.join(map(str, e.path)) or '$'}: {e.message}" for e in validator.iter_errors(instance)])
    except Exception:
        errors: list[str] = []
        _minimal_validate(instance, schema, "$", errors)
        return errors


def _resolve_schema_path(repo_root: Path, bundle_root: Path, raw: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate
    from_repo = (repo_root / raw).resolve()
    if from_repo.exists():
        return from_repo
    return (bundle_root / raw).resolve()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed Stage-2 schema gate for ZIP_JOB outputs.")
    parser.add_argument("--bundle-root", required=True, help="Path to bundle root.")
    parser.add_argument(
        "--bindings-relpath",
        default="meta/STAGE_2_SCHEMA_BINDINGS__v1.json",
        help="Relative path to schema binding file from bundle root.",
    )
    args = parser.parse_args(argv)

    bundle_root = Path(args.bundle_root).expanduser().resolve()
    repo_root = Path(__file__).resolve().parents[2]
    bindings_path = (bundle_root / args.bindings_relpath).resolve()

    errors: list[str] = []
    warnings: list[str] = []
    validated: list[dict[str, Any]] = []

    if not bindings_path.exists():
        print(
            json.dumps(
                {
                    "schema": "STAGE_2_SCHEMA_GATE_RESULT_v1",
                    "status": "FAIL",
                    "errors": [f"missing_bindings_file:{bindings_path}"],
                    "warnings": [],
                },
                sort_keys=True,
            )
        )
        return 2

    bindings_doc = _load_json(bindings_path)
    if not isinstance(bindings_doc, dict):
        errors.append("bindings_document_must_be_object")
    if bindings_doc.get("schema") != "STAGE_2_SCHEMA_BINDINGS_v1":
        errors.append("bindings_schema_mismatch")

    bindings = bindings_doc.get("bindings")
    if not isinstance(bindings, list):
        errors.append("bindings_must_be_list")
        bindings = []

    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            errors.append(f"bindings[{index}]_must_be_object")
            continue

        output_rel = binding.get("output_relpath")
        schema_rel = binding.get("schema_relpath")
        required = bool(binding.get("required", True))
        if not isinstance(output_rel, str) or not output_rel:
            errors.append(f"bindings[{index}]_missing_output_relpath")
            continue
        if not isinstance(schema_rel, str) or not schema_rel:
            errors.append(f"bindings[{index}]_missing_schema_relpath")
            continue

        output_path = (bundle_root / output_rel).resolve()
        schema_path = _resolve_schema_path(repo_root=repo_root, bundle_root=bundle_root, raw=schema_rel)

        if not schema_path.exists():
            errors.append(f"schema_missing:{schema_path}")
            continue

        if not output_path.exists():
            message = f"output_missing:{output_path}"
            if required:
                errors.append(message)
            else:
                warnings.append(message)
            continue

        try:
            instance = _load_json(output_path)
        except Exception as exc:
            errors.append(f"output_json_parse_error:{output_path}:{exc}")
            continue

        try:
            schema_obj = _load_json(schema_path)
        except Exception as exc:
            errors.append(f"schema_json_parse_error:{schema_path}:{exc}")
            continue

        validation_errors = _validate_with_jsonschema_or_fallback(instance=instance, schema=schema_obj)
        if validation_errors:
            for issue in validation_errors:
                errors.append(f"schema_validation_error:{output_rel}:{issue}")
        else:
            validated.append(
                {
                    "output_relpath": output_rel,
                    "schema_relpath": schema_rel,
                    "status": "PASS",
                }
            )

    status = "PASS" if not errors else "FAIL"
    result = {
        "schema": "STAGE_2_SCHEMA_GATE_RESULT_v1",
        "status": status,
        "bundle_root": str(bundle_root),
        "bindings_path": str(bindings_path),
        "validated_count": len(validated),
        "validated": validated,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))

