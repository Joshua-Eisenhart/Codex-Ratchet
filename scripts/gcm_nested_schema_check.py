#!/usr/bin/env python3
"""Shared schema gate for GCM nested-manifold controller packets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FIELDS = (
    "exact_relation_status",
    "probe_relation_status",
    "extension_fiber_size",
    "cut_state_available",
    "blocked_consumer_enforced",
    "what_would_flip",
    "negative_control_status",
    "cross_pin_stability",
    "geometry_delta_stability_class",
    "forward_transport_status",
    "backward_admissibility_status",
    "claim_ceiling",
)

GEOMETRY_DELTA_STABILITY_CLASSES = {
    "pin_relative",
    "probe_relative",
    "cross_stable",
    "untested",
}

GEOMETRY_DELTA_KEYS = {
    "geometry_delta",
    "geometry_delta_from_free",
    "nested_geometry_delta",
    "nested_geometry_delta_summary",
    "geometry_delta_summary",
}

ALTERNATE_REGISTRY_KEYS = {
    "alternate_registry",
    "alternate_registry_pin",
    "alternate_registry_tested",
    "alternate_pin_registry",
    "cross_pin_registry",
}

ALTERNATE_PROBE_KEYS = {
    "alternate_probe_family",
    "alternate_probe_family_tested",
    "cross_probe_family",
    "probe_family_alternate",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _missing_code(field: str) -> str:
    return f"GCM_NESTED_MISSING_{field.upper()}"


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, (list, dict, tuple, set)) and not value:
        return False
    return True


def _claimed_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"", "none", "not_applicable", "not-applicable", "no", "false"}
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _geometry_delta_claims(value: Any, path: str = "$") -> list[str]:
    claims: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}"
            if key in GEOMETRY_DELTA_KEYS and _claimed_value(item):
                claims.append(child_path)
            if isinstance(item, (dict, list)):
                claims.extend(_geometry_delta_claims(item, child_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, (dict, list)):
                claims.extend(_geometry_delta_claims(item, f"{path}[{index}]"))
    return claims


def _flip_control_ok(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "untested":
            return True
        return "alternate_registry" in lowered and "alternate_probe_family" in lowered
    if not isinstance(value, dict):
        return False
    status = value.get("status")
    if isinstance(status, str) and status.strip().lower() == "untested":
        return True
    if isinstance(value.get("tested"), str) and value["tested"].strip().lower() == "untested":
        return True
    if value.get("tested") == "untested":
        return True
    has_registry = any(_present(value.get(key)) for key in ALTERNATE_REGISTRY_KEYS)
    has_probe = any(_present(value.get(key)) for key in ALTERNATE_PROBE_KEYS)
    return has_registry and has_probe


def gcm_nested_schema_check(payload: dict[str, Any], payload_path: str | Path | None = None) -> dict[str, Any]:
    """Validate tribunal-adopted nested result controller fields.

    This is an enforcement substrate only. It checks field carriage and the
    geometry-delta flip-control gate; it does not validate or promote any
    manifold, tower, or geometry claim.
    """

    errors: list[str] = []
    error_codes: list[str] = []

    def add_error(code: str, message: str) -> None:
        error_codes.append(code)
        errors.append(message)

    missing_fields = [field for field in REQUIRED_FIELDS if field not in payload]
    for field in missing_fields:
        add_error(_missing_code(field), f"missing required nested schema field: {field}")

    stability = payload.get("geometry_delta_stability_class")
    if "geometry_delta_stability_class" in payload and stability not in GEOMETRY_DELTA_STABILITY_CLASSES:
        add_error(
            "GCM_NESTED_GEOMETRY_DELTA_STABILITY_CLASS_INVALID",
            "geometry_delta_stability_class must be one of "
            f"{sorted(GEOMETRY_DELTA_STABILITY_CLASSES)}; got {stability!r}",
        )

    geometry_delta_paths = _geometry_delta_claims(payload)
    if geometry_delta_paths:
        if "geometry_delta_stability_class" not in payload:
            add_error(
                "GCM_NESTED_GEOMETRY_DELTA_WITHOUT_STABILITY",
                "geometry_delta claim requires geometry_delta_stability_class",
            )
        if not _flip_control_ok(payload.get("what_would_flip")):
            add_error(
                "GCM_NESTED_GEOMETRY_DELTA_FLIP_CONTROL_MISSING",
                "geometry_delta claim requires what_would_flip to name alternate_registry "
                "and alternate_probe_family, or be exactly 'untested'",
            )

    result: dict[str, Any] = {
        "ok": not errors,
        "errors": errors,
        "error_codes": error_codes,
        "required_fields": list(REQUIRED_FIELDS),
        "missing_fields": missing_fields,
        "geometry_delta_claimed": bool(geometry_delta_paths),
        "geometry_delta_claim_paths": geometry_delta_paths,
        "claim_ceiling": payload.get("claim_ceiling"),
    }
    if payload_path is not None:
        path = Path(payload_path)
        result["payload_path"] = _display_path(path if path.is_absolute() else ROOT / path)
    return result


def check_paths(paths: list[str]) -> dict[str, Any]:
    results = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_absolute():
            path = ROOT / path
        if not path.is_file():
            results.append(
                {
                    "ok": False,
                    "payload_path": _display_path(path),
                    "errors": [f"payload missing: {_display_path(path)}"],
                    "error_codes": ["GCM_NESTED_PAYLOAD_MISSING"],
                    "missing_fields": list(REQUIRED_FIELDS),
                }
            )
            continue
        results.append(gcm_nested_schema_check(_load_json(path), path))
    return {"ok": all(item.get("ok") for item in results), "results": results}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check GCM nested-result schema fields.")
    parser.add_argument("payload", nargs="+", help="JSON payload path(s) to validate")
    args = parser.parse_args()
    result = check_paths(args.payload)
    if len(result["results"]) == 1:
        result = result["results"][0]
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result.get("ok") else 1)
