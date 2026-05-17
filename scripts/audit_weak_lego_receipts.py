#!/usr/bin/env python3
"""Audit weak lego result receipts before admission writes shared state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "system_v4" / "probes" / "a2_state" / "sim_results"
REQUIRED_CONTRACT_FIELDS = {
    "operation_sequence",
    "carrier_topology",
    "observable",
    "pass_fail_predicate",
    "graveyard_companions",
    "baseline_variants",
    "alternative_formulations",
    "exact_tool_function_needs",
    "lego_coupling_target",
    "claim_ceiling",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def result_path(raw: str) -> Path:
    path = Path(raw)
    if path.suffix == ".json":
        return path if path.is_absolute() else ROOT / path
    basename = path.name.removesuffix(".py")
    return RESULTS / f"{basename}_results.json"


def audit_one(path: Path) -> dict:
    findings: list[str] = []
    if not path.exists():
        return {"path": str(path), "ok": False, "findings": ["missing_result"]}
    try:
        payload = load_json(path)
    except Exception as exc:
        return {"path": str(path), "ok": False, "findings": [f"invalid_json:{exc.__class__.__name__}"]}

    if payload.get("classification") != "tool_lego_fit_probe":
        findings.append("classification_not_tool_lego_fit_probe")
    if payload.get("promotion_allowed") is not False:
        findings.append("promotion_allowed_not_false")
    if not payload.get("all_pass"):
        findings.append("all_pass_not_true")
    for field in ("TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "claim_ceiling", "next_lego_target"):
        if not payload.get(field):
            findings.append(f"missing_{field}")
    depths = payload.get("TOOL_INTEGRATION_DEPTH") or {}
    if not any(depth == "load_bearing" for depth in depths.values()):
        findings.append("no_load_bearing_tool")

    contract = payload.get("rosetta_to_sim_contract")
    if not isinstance(contract, dict):
        findings.append("missing_rosetta_to_sim_contract")
    else:
        missing = sorted(REQUIRED_CONTRACT_FIELDS - set(contract))
        if missing:
            findings.extend(f"contract_missing_{field}" for field in missing)
    for field in ("promotion_condition", "blocked_until", "demotion_condition", "out_of_scope"):
        if field not in payload:
            findings.append(f"missing_{field}")

    return {
        "path": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
        "name": payload.get("name"),
        "ok": not findings,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="+", help="Result paths or sim basenames")
    args = parser.parse_args()
    records = [audit_one(result_path(item)) for item in args.results]
    output = {
        "all_pass": all(record["ok"] for record in records),
        "checked": len(records),
        "finding_count": sum(len(record["findings"]) for record in records),
        "records": records,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
