#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

VERBS = (
    "kill",
    "demote",
    "reroute",
    "shrink",
    "override",
    "block_full",
    "accept_with_reason",
    "no_intervention_needed",
)


def watch(metrics: dict) -> dict:
    findings = []
    verb = "no_intervention_needed"
    if metrics.get("same_state_rounds", 0) >= 3:
        findings.append("stuck")
        verb = "kill"
    if metrics.get("loop_count", 0) > metrics.get("max_rounds", 1):
        findings.append("spinning")
        verb = "kill"
    if metrics.get("children_waiting") and not metrics.get("children_running"):
        findings.append("starved")
        verb = "reroute"
    if metrics.get("parallel_children", 0) > metrics.get("max_parallel", 8):
        findings.append("stampede")
        verb = "shrink"
    if metrics.get("context_bytes", 0) > metrics.get("context_budget", 10**9):
        findings.append("context_growth")
        verb = "shrink"
    if metrics.get("budget_exhausted"):
        findings.append("budget_exhaustion")
        verb = "block_full"
    if metrics.get("route_truth") == "FULL" and metrics.get("model_free"):
        findings.append("drift")
        verb = "block_full"
    return {
        "schema": "constraintbox.watchdog.v1",
        "status": "WATCHED",
        "findings": findings,
        "verb": verb,
        "content_vote": False,
        "promotion_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=str, required=True)
    args = parser.parse_args()
    receipt = watch(json.loads(args.metrics))
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
