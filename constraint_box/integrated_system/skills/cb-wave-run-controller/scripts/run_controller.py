#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SKILLS = Path(os.environ.get("CB_SKILLS_ROOT", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(SKILLS / "cb-management-plane" / "scripts"))
from plane import digest_obj, now, sha_text, write_json
sys.path.insert(0, str(SKILLS / "cb-route-truth-verifier"))
from scripts.verify_routes import verify


WATCHDOG_VERBS = {
    "kill",
    "demote",
    "reroute",
    "shrink",
    "override",
    "block_full",
    "accept_with_reason",
    "no_intervention_needed",
}


def run(definition: dict, child_results: list[dict], budgets: dict | None = None) -> dict:
    budgets = budgets or {}
    declared = [str(child["id"]) for child in definition.get("children") or []]
    observed = [str(row.get("child_id")) for row in child_results]
    max_rounds = int((definition.get("loop") or {}).get("max_rounds") or 1)
    round_n = int(budgets.get("round") or 0)
    cancelled = bool(budgets.get("cancelled"))
    if cancelled:
        state = "CANCELLED"
    elif round_n > max_rounds:
        state = "MAX_ROUNDS"
    elif set(observed) != set(declared):
        state = "PARTIAL"
    elif all(row.get("terminal_state") == "COMPLETED" for row in child_results):
        state = "COMPLETE"
    else:
        state = "PARTIAL"
    output = {
        "wave_id": definition.get("wave_id"),
        "child_ids": observed,
        "state": state,
    }
    output_sha = sha_text(json.dumps(output, sort_keys=True))
    execution = {
        "schema": "constraintbox.wave-execution.v1",
        "wave_id": definition.get("wave_id"),
        "run_id": budgets.get("run_id") or digest_obj([definition.get("wave_id"), now()]),
        "controller_agent_id": "manager.run_controller",
        "depth": int(budgets.get("depth") or 0),
        "round": round_n,
        "state": state,
        "model_free": True,
        "route_truth": "NOT_FULL",
        "target_sha256": budgets.get("target_sha256") or digest_obj(definition.get("wave_id")),
        "children": child_results,
        "cancellation_state": "CANCELLED" if cancelled else "NOT_REQUESTED",
        "disagreement_state": budgets.get("disagreement_state") or "NOT_APPLICABLE",
        "output_digest": output_sha,
        "output_sha256": output_sha,
        "promotion_allowed": False,
        "content_interpreted": False,
    }
    truth = verify(definition, execution)
    execution["route_truth_receipt"] = truth
    return execution


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", type=Path, required=True)
    parser.add_argument("--children", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    definition = json.loads(args.wave.read_text(encoding="utf-8"))
    children = json.loads(args.children.read_text(encoding="utf-8"))
    if isinstance(children, dict):
        children = children.get("children") or []
    execution = run(definition, children)
    write_json(args.out, execution)
    print(json.dumps({"state": execution["state"], "route_truth": execution["route_truth"], "wave_id": execution["wave_id"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
