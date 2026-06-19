#!/usr/bin/env python3
"""Self-tests for the GCM nested schema checker."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from gcm_nested_schema_check import gcm_nested_schema_check  # noqa: E402


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def test_conformant_nested_payload_passes() -> None:
    result = gcm_nested_schema_check(load("conformant_nested_payload.json"))
    assert result["ok"] is True
    assert result["error_codes"] == []
    assert result["geometry_delta_claimed"] is True


def test_missing_field_payload_fails_with_named_code() -> None:
    result = gcm_nested_schema_check(load("missing_field_payload.json"))
    assert result["ok"] is False
    assert "cross_pin_stability" in result["missing_fields"]
    assert "GCM_NESTED_MISSING_CROSS_PIN_STABILITY" in result["error_codes"]


def test_geometry_delta_without_stability_fails_with_named_code() -> None:
    result = gcm_nested_schema_check(load("geometry_delta_without_stability_payload.json"))
    assert result["ok"] is False
    assert "geometry_delta_stability_class" in result["missing_fields"]
    assert "GCM_NESTED_MISSING_GEOMETRY_DELTA_STABILITY_CLASS" in result["error_codes"]
    assert "GCM_NESTED_GEOMETRY_DELTA_WITHOUT_STABILITY" in result["error_codes"]


def test_geometry_delta_requires_flip_control_or_explicit_untested() -> None:
    payload = load("conformant_nested_payload.json")
    payload["what_would_flip"] = "alternate_registry=pin_prime only"
    result = gcm_nested_schema_check(payload)
    assert result["ok"] is False
    assert "GCM_NESTED_GEOMETRY_DELTA_FLIP_CONTROL_MISSING" in result["error_codes"]
