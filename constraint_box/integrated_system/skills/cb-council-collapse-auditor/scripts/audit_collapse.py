#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def audit(lanes: list[dict]) -> dict:
    prompts = [lane.get("prompt_sha256") for lane in lanes]
    roots = [tuple(lane.get("source_roots") or []) for lane in lanes]
    conclusions = [lane.get("conclusion") for lane in lanes]
    findings = []
    if len(set(filter(None, prompts))) < len([item for item in prompts if item]) and prompts:
        findings.append("shared_prompt_hash")
    if len(set(roots)) < len(roots):
        findings.append("shared_source_roots")
    if len(set(filter(None, conclusions))) == 1 and len(conclusions) > 1:
        findings.append("repeated_conclusions")
    decorative = [lane.get("id") for lane in lanes if lane.get("role") and not lane.get("source_roots")]
    if decorative:
        findings.append("decorative_roles")
    ancestries = [lane.get("provider_ancestry") for lane in lanes]
    named_ancestries = [item for item in ancestries if item]
    if len(named_ancestries) > 1 and len(set(named_ancestries)) == 1:
        findings.append("correlated_provider_ancestry")
    if any(lane.get("copied_evidence") for lane in lanes):
        findings.append("copied_evidence")
    if any(lane.get("falsifier_softened") for lane in lanes):
        findings.append("softened_falsifiers")
    independent = len({(lane.get("prompt_sha256"), tuple(lane.get("source_roots") or []), lane.get("provider_ancestry")) for lane in lanes})
    return {
        "schema": "constraintbox.council-collapse.v1",
        "status": "COLLAPSED" if findings else "INDEPENDENT",
        "findings": findings,
        "agent_count": len(lanes),
        "effective_independent_lanes": independent,
        "promotion_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lanes", type=str, required=True)
    args = parser.parse_args()
    lanes = json.loads(args.lanes)
    if isinstance(lanes, dict):
        lanes = lanes.get("lanes") or []
    receipt = audit(lanes)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "INDEPENDENT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
