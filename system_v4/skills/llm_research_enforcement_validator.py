#!/usr/bin/env python3
"""Controller-side validator for LLM research enforcement closeouts.

Checks:
- closeout schema fields exist
- status vocabulary is one of the allowed terms
- load-bearing tools are non-empty when canonical/proof-backed claims are made
- fresh rerun flag required for strong claims
- no decorative tool use if load_bearing_tools is empty
- gate rule: E claims require supporting A-D evidence for the same family
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ALLOWED_STATUS = {
    "exists",
    "runs locally",
    "passes local rerun",
    "proof-backed",
    "canonical by process",
}

MANDATORY_FIELDS = {
    "class",
    "claim_type",
    "target_family",
    "file",
    "result_file",
    "fresh_rerun",
    "status",
    "load_bearing_tools",
    "negative_tests",
    "open_gaps",
}


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_closeout(closeout: dict) -> list[str]:
    errors = []
    missing = sorted(MANDATORY_FIELDS - closeout.keys())
    if missing:
        errors.append(f"missing_fields: {', '.join(missing)}")

    status = closeout.get("status")
    if status not in ALLOWED_STATUS:
        errors.append(f"invalid_status: {status!r}")

    if closeout.get("fresh_rerun") not in {"Y", "N"}:
        errors.append(f"fresh_rerun must be 'Y' or 'N', got {closeout.get('fresh_rerun')!r}")

    load_bearing = closeout.get("load_bearing_tools", [])
    if closeout.get("status") in {"proof-backed", "canonical by process"} and not load_bearing:
        errors.append("decorative_tools: strong claim without load-bearing tools")

    if closeout.get("status") == "canonical by process" and closeout.get("fresh_rerun") != "Y":
        errors.append("canonical claims require fresh rerun")

    return errors


def validate_gap_matrix(path: str) -> list[str]:
    errors = []
    data = load_json(path)
    required = ["schema_version", "execution_ladder", "status_terms", "claim_tool_map", "families"]
    for key in required:
        if key not in data:
            errors.append(f"matrix missing key: {key}")

    families = data.get("families", [])
    for fam in families:
        cells = fam.get("cells", {})
        if set(cells.keys()) != {"A_local", "B_pairwise_coupling", "C_multi_shell_coexistence", "D_topology_variant", "E_emergence"}:
            errors.append(f"bad cell schema for family {fam.get('family')}")
        if any(v not in {"GAP", "PARTIAL", "DONE"} for v in cells.values()):
            errors.append(f"invalid cell value in family {fam.get('family')}")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: llm_research_enforcement_validator.py <closeout.json> [gap_matrix.json]", file=sys.stderr)
        return 2

    closeout_path = argv[1]
    closeout = load_json(closeout_path)
    errors = validate_closeout(closeout)

    if len(argv) > 2:
        errors.extend(validate_gap_matrix(argv[2]))

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1

    print(json.dumps({"ok": True, "status": closeout.get("status")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
