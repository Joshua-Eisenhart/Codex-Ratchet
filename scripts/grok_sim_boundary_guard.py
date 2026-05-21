#!/usr/bin/env python3
"""Fail if grok_sim result receipts use formal-scout admission vocabulary."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GROK_RESULTS = ROOT / "system_v5" / "grok_sim" / "results"
GROK_DOCS = ROOT / "system_v5" / "grok_sim"

DANGEROUS_JSON_KEYS = {
    "suggested_basin_verdict",
    "single_file_complete_sim",
    "classification_formal_scout",
    "side_quest_deep_basin_admitted",
}

DANGEROUS_STRING_PATTERNS = {
    "v5 formal scout",
    "v5 formal-scout",
    "v5 formal_scouts",
    "formal_scout basin classifier admission",
    "deep_basin_candidate (side-quest)",
    "deep_basin_cross_solver",
    "peps/peps3d dynamics",
}

DANGEROUS_TEXT_PATTERNS = {
    "KEY MULTI-QUBIT VERIFICATION",
    "PEPS/PEPS3D dynamics",
    "FULL MANIFOLD with COHERENT BRIDGE",
    "captures A-B correlation",
    "deep_basin_cross_solver",
    "deep_basin_candidate_for_formal_review",
    "admit at `deep_basin`",
    "admit at deep_basin",
    "admission stands",
    "basin verified",
    "formal evidence",
}

NEGATED_TEXT_CONTEXT = {
    "blocked",
    "invalidated",
    "not admission",
    "not admitted",
    "not admit",
    "not formal evidence",
    "prohibits",
    "doctrine prohibits",
}

JSON_STRING_PATTERNS = {
    pattern.lower() for pattern in (DANGEROUS_STRING_PATTERNS | DANGEROUS_TEXT_PATTERNS)
}

TEXT_PATTERNS = {
    pattern.lower() for pattern in DANGEROUS_TEXT_PATTERNS
}


def main() -> int:
    violations: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    def add_violation(path: Path, rule: str, detail: str) -> None:
        violations.append(
            {
                "path": str(path.relative_to(ROOT)),
                "rule": rule,
                "detail": detail,
            }
        )

    def scan_json_leaf(path: Path, value: object, json_path: str = "$") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in DANGEROUS_JSON_KEYS:
                    add_violation(
                        path,
                        "grok_result_nested_admission_key",
                        f"{json_path}.{key}",
                    )
                scan_json_leaf(path, item, f"{json_path}.{key}")
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                scan_json_leaf(path, item, f"{json_path}[{idx}]")
        elif isinstance(value, str):
            lowered = value.lower()
            for pattern in JSON_STRING_PATTERNS:
                if pattern in lowered:
                    add_violation(
                        path,
                        "grok_result_nested_admission_text",
                        f"{json_path}: {pattern}",
                    )

    for path in sorted(GROK_DOCS.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            violations.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "rule": "json_parse_error",
                    "detail": str(exc),
                }
            )
            continue
        is_result_json = path.is_relative_to(GROK_RESULTS)
        if is_result_json and "claim_ceiling" not in data:
            warnings.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "rule": "grok_result_missing_claim_ceiling_legacy_warning",
                    "detail": "legacy grok_sim result lacks explicit claim_ceiling",
                }
            )
        scan_json_leaf(path, data)
        if not is_result_json:
            continue
        if data.get("classification") == "formal_scout":
            violations.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "rule": "grok_result_uses_formal_scout_classification",
                    "detail": "grok_sim results must stay side_quest_only or omit classification",
                }
            )
        if data.get("promotion_allowed") is True:
            violations.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "rule": "grok_result_allows_promotion",
                    "detail": "grok_sim results must not allow promotion",
                }
            )
        if data.get("evidence_allowed") is True:
            violations.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "rule": "grok_result_allows_evidence",
                    "detail": "grok_sim results must not present as admitted evidence",
                }
            )
        claim_ceiling = str(data.get("claim_ceiling", "")).lower()
        if "formal scout only" in claim_ceiling:
            violations.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "rule": "grok_result_uses_formal_claim_ceiling",
                    "detail": "grok_sim claim ceilings must not present as formal scout receipts",
                }
            )
        for key in ("TOOL_INTEGRATION_DEPTH", "tool_integration_depth"):
            depth = data.get(key)
            if not isinstance(depth, dict):
                continue
            for tool, role in depth.items():
                if str(tool).lower() == "numpy" and str(role).lower() in {"load_bearing", "required", "primary"}:
                    violations.append(
                        {
                            "path": str(path.relative_to(ROOT)),
                            "rule": "grok_result_uses_numpy_load_bearing_depth",
                            "detail": f"{key}.{tool}={role}",
                        }
                    )
    text_paths = {
        *GROK_DOCS.rglob("*.py"),
        *GROK_DOCS.rglob("*.md"),
        *GROK_DOCS.rglob("*.txt"),
        *GROK_DOCS.rglob("*.log"),
    }
    for path in sorted(text_paths):
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            lowered_line = line.lower()
            for pattern in TEXT_PATTERNS:
                if pattern in lowered_line and not any(context in lowered_line for context in NEGATED_TEXT_CONTEXT):
                    add_violation(
                        path,
                        "grok_text_overclaim_phrase",
                        f"line {lineno}: {pattern}",
                    )
    print(
        json.dumps(
            {
                "checked_roots": [
                    str(GROK_RESULTS.relative_to(ROOT)),
                    str(GROK_DOCS.relative_to(ROOT)),
                ],
                "violations": violations,
                "warnings": warnings,
            },
            indent=2,
        )
    )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
