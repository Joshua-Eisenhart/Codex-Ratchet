#!/usr/bin/env python3
"""Report the current sim-stage gate and answer narrow admission questions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ORDER = ["tools", "tool_integration", "lego", "coupling"]

CLAIM_RULES = {
    "tool_micro": {"min_stage": "tools"},
    "tool_integration_micro": {"min_stage": "tool_integration"},
    "tool_lego_fit": {"min_stage": "tool_integration"},
    "lego": {"min_stage": "lego"},
    "scientific_coupling": {"requires_stage": "coupling", "requires_receipts": True},
    "bridge": {"requires_stage": "coupling", "requires_receipts": True},
    "coexistence": {"requires_stage": "coupling", "requires_receipts": True},
    "axis": {"requires_stage": "coupling", "requires_receipts": True},
    "engine": {"requires_stage": "coupling", "requires_receipts": True},
    "tier_d": {"requires_flag": "allow_tier_d_launch"},
    "default_late_stage": {"requires_flag": "allow_default_queue_late_stage"},
    "off_program": {"requires_flag": "allow_off_program"},
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage-gate",
        default=str(root / "system_v5" / "ops" / "stage_gate.json"),
        help="Machine-readable stage gate JSON.",
    )
    parser.add_argument(
        "--claim",
        choices=sorted(CLAIM_RULES),
        help="Return nonzero when this claim is blocked by the current gate.",
    )
    return parser.parse_args()


def load_gate(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "active_stage": payload.get("active_stage"),
        "allow_default_queue_late_stage": payload.get("allow_default_queue_late_stage") is True,
        "allow_off_program": payload.get("allow_off_program") is True,
        "allow_tier_d_launch": payload.get("allow_tier_d_launch") is True,
        "notes": payload.get("notes", []),
    }


def stage_index(stage: str | None) -> int:
    try:
        return ORDER.index(str(stage))
    except ValueError:
        return -1


def decide_claim(gate: dict[str, Any], claim: str) -> dict[str, Any]:
    rule = CLAIM_RULES[claim]
    active = str(gate.get("active_stage"))
    allowed = False
    reason = ""

    if "min_stage" in rule:
        minimum = str(rule["min_stage"])
        allowed = stage_index(active) >= stage_index(minimum)
        reason = (
            f"{claim} is not stage-blocked during active_stage={active}"
            if allowed
            else f"{claim} is blocked until active_stage reaches {minimum}"
        )
    elif "requires_stage" in rule:
        required = str(rule["requires_stage"])
        stage_open = stage_index(active) >= stage_index(required)
        if stage_open and rule.get("requires_receipts"):
            allowed = False
            reason = (
                f"{claim} is stage-open only after {required}, but generic "
                "stage_gate.py does not admit it without exact reconciled parent receipts"
            )
        else:
            allowed = stage_open
            reason = (
                f"{claim} is not stage-blocked because active_stage={active} has reached {required}"
                if allowed
                else f"{claim} is blocked until active_stage reaches {required}"
            )
    elif "requires_flag" in rule:
        flag = str(rule["requires_flag"])
        allowed = gate.get(flag) is True
        reason = (
            f"{claim} is allowed because {flag}=true"
            if allowed
            else f"{claim} is blocked because {flag}=false"
        )

    return {"claim": claim, "allowed": allowed, "reason": reason}


def main() -> int:
    args = parse_args()
    gate_path = Path(args.stage_gate)
    gate = load_gate(gate_path)
    decisions = {
        claim: decide_claim(gate, claim)
        for claim in sorted(CLAIM_RULES)
    }
    report = {
        "stage_gate": str(gate_path),
        "active_stage": gate.get("active_stage"),
        "allow_default_queue_late_stage": gate.get("allow_default_queue_late_stage"),
        "allow_off_program": gate.get("allow_off_program"),
        "allow_tier_d_launch": gate.get("allow_tier_d_launch"),
        "all_pass": True,
        "decisions": decisions,
    }
    if args.claim:
        report["requested_claim"] = decisions[args.claim]
        report["all_pass"] = decisions[args.claim]["allowed"]

    print(json.dumps(report, indent=2, sort_keys=True))
    if args.claim and not decisions[args.claim]["allowed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
