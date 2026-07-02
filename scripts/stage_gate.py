#!/usr/bin/env python3
"""Report the current sim-stage gate and answer narrow admission questions.

Sensitive completion claims never admit through this generic stage gate. They
can only be blocked here; admission requires a dedicated full-layer evidence
packet plus the layer-completion claim gate.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ORDER = ["tools", "tool_integration", "lego", "coupling"]

CLAIM_RULES = {
    "axis0": {"sensitive_completion_claim": True},
    "tool_micro": {"min_stage": "tools"},
    "tool_integration_micro": {"min_stage": "tool_integration"},
    "tool_lego_fit": {"min_stage": "tool_integration"},
    "lego": {"min_stage": "lego"},
    "scientific_coupling": {"requires_stage": "coupling", "requires_receipts": True},
    "bridge": {"requires_stage": "coupling", "requires_receipts": True},
    "coexistence": {"requires_stage": "coupling", "requires_receipts": True},
    "axis": {"requires_stage": "coupling", "requires_receipts": True},
    "engine": {"requires_stage": "coupling", "requires_receipts": True},
    "fep_holodeck": {"sensitive_completion_claim": True},
    "final_manifold": {"sensitive_completion_claim": True},
    "flux": {"sensitive_completion_claim": True},
    "g_structure_completion": {"sensitive_completion_claim": True},
    "layer_completion": {"sensitive_completion_claim": True},
    "physics_gravity": {"sensitive_completion_claim": True},
    "stacking": {"sensitive_completion_claim": True},
    "xi_phi0": {"sensitive_completion_claim": True},
    "tier_d": {"requires_flag": "allow_tier_d_launch"},
    "default_late_stage": {"requires_flag": "allow_default_queue_late_stage"},
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
    parser.add_argument(
        "--claim-file",
        action="append",
        type=Path,
        default=[],
        help="Optional claim text file to pass through the layer-completion claim gate.",
    )
    return parser.parse_args()


def load_gate(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "active_stage": payload.get("active_stage"),
        "allow_default_queue_late_stage": payload.get("allow_default_queue_late_stage") is True,
        "allow_tier_d_launch": payload.get("allow_tier_d_launch") is True,
        "notes": payload.get("notes", []),
    }


def stage_index(stage: str | None) -> int:
    try:
        return ORDER.index(str(stage))
    except ValueError:
        return -1


def run_layer_completion_claim_gate(claim_files: list[Path]) -> dict[str, Any]:
    if not claim_files:
        return {
            "status": "not_evaluated",
            "reason": "no claim files supplied",
        }
    script = repo_root() / "scripts" / "validate_layer_completion_claims.py"
    cmd = [
        sys.executable,
        str(script),
        "--use-default-status",
        "--require-status",
        "--resolve-status-receipts",
    ]
    for claim_file in claim_files:
        cmd.extend(["--claim-file", str(claim_file)])
    proc = subprocess.run(
        cmd,
        cwd=repo_root(),
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {
            "ok": False,
            "violations": [
                {
                    "code": "stage_gate.layer_completion_claim_gate_unparseable",
                    "detail": (proc.stdout or proc.stderr)[-1200:],
                }
            ],
        }
    payload["returncode"] = proc.returncode
    return payload


def decide_claim(
    gate: dict[str, Any],
    claim: str,
    layer_completion_claim_gate: dict[str, Any] | None = None,
    sensitive_claim_file_missing: bool = False,
) -> dict[str, Any]:
    rule = CLAIM_RULES[claim]
    active = str(gate.get("active_stage"))
    allowed = False
    reason = ""

    if rule.get("sensitive_completion_claim"):
        allowed = False
        claim_gate_status = (
            layer_completion_claim_gate.get("status")
            if isinstance(layer_completion_claim_gate, dict)
            else None
        )
        if sensitive_claim_file_missing:
            reason = (
                f"{claim} is blocked because sensitive completion claims require "
                "--claim-file text to check against current status/result evidence"
            )
        elif (
            layer_completion_claim_gate
            and claim_gate_status != "not_evaluated"
            and not layer_completion_claim_gate.get("ok")
        ):
            reason = (
                f"{claim} is blocked because the layer-completion claim gate failed"
            )
        else:
            reason = (
                f"{claim} cannot admit through generic stage_gate.py; it requires "
                "dedicated full-layer/G-structure/manifold evidence plus the "
                "layer-completion claim gate"
            )
    elif "min_stage" in rule:
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

    row = {"claim": claim, "allowed": allowed, "reason": reason}
    if rule.get("sensitive_completion_claim"):
        row["layer_completion_claim_gate"] = layer_completion_claim_gate or {}
    return row


def main() -> int:
    args = parse_args()
    gate_path = Path(args.stage_gate)
    gate = load_gate(gate_path)
    sensitive_requested = bool(
        args.claim and CLAIM_RULES[args.claim].get("sensitive_completion_claim")
    )
    sensitive_claim_file_missing = sensitive_requested and not args.claim_file
    layer_completion_claim_gate = (
        run_layer_completion_claim_gate(args.claim_file)
        if sensitive_requested or args.claim_file
        else run_layer_completion_claim_gate([])
    )
    decisions = {
        claim: decide_claim(
            gate,
            claim,
            layer_completion_claim_gate
            if CLAIM_RULES[claim].get("sensitive_completion_claim")
            else None,
            sensitive_claim_file_missing
            if claim == args.claim and CLAIM_RULES[claim].get("sensitive_completion_claim")
            else False,
        )
        for claim in sorted(CLAIM_RULES)
    }
    report = {
        "stage_gate": str(gate_path),
        "active_stage": gate.get("active_stage"),
        "allow_default_queue_late_stage": gate.get("allow_default_queue_late_stage"),
        "allow_tier_d_launch": gate.get("allow_tier_d_launch"),
        "all_pass": True,
        "decisions": decisions,
    }
    if layer_completion_claim_gate is not None:
        report["layer_completion_claim_gate"] = layer_completion_claim_gate
    if args.claim:
        report["requested_claim"] = decisions[args.claim]
        report["all_pass"] = decisions[args.claim]["allowed"]

    print(json.dumps(report, indent=2, sort_keys=True))
    if args.claim and not decisions[args.claim]["allowed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
