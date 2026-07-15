#!/usr/bin/env python3
"""Independent fail-closed validator for the V8 integration-repair receipt."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RECEIPT_PATH = HERE / "results/integration_gate_receipt.json"
OUT_PATH = HERE / "results/integration_gate_validation.json"
EXPECTED_STEPS = [
    "env_doctor",
    "stack_shakedown",
    "qit_main",
    "qit_jax",
    "qit_pytorch",
    "qit_julia",
    "qit_envelope",
    "qit_packet_validator",
    "shared_strict_validator",
    "focused_tests",
    "contract_lint",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(receipt: dict[str, Any], *, verify_files: bool) -> list[str]:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    require(
        receipt.get("schema") == "codex_ratchet.v8_integration_repair.gate_receipt.v1",
        "bad receipt schema",
    )
    require(receipt.get("classification") == "isolated_integration_repair", "classification drift")
    for field in (
        "frozen_campaign_rewritten",
        "install_attempted",
        "llm_gate_used",
        "promotion_allowed",
        "formal_admission_allowed",
        "official_launch_allowed",
        "release_eligible",
        "scientific_claim_proven",
    ):
        require(receipt.get(field) is False, f"{field} must remain false")
    steps = receipt.get("steps", [])
    require([row.get("step_id") for row in steps] == EXPECTED_STEPS, "step ledger drift")
    require(
        all(
            row.get("pass") is True
            and row.get("returncode") == 0
            and row.get("timed_out") is False
            for row in steps
        ),
        "one or more integration steps are red",
    )
    require(receipt.get("all_steps_pass") is True, "all_steps_pass is not true")
    require(receipt.get("all_content_checks_pass") is True, "content aggregate is not true")
    require(receipt.get("integration_gate_pass") is True, "integration gate is not green")
    checks = receipt.get("content_checks", {})
    require(bool(checks) and all(value is True for value in checks.values()), "content check is red")
    require(
        checks.get("pre_manifest_reproduced_26_pass_3_fail") is True,
        "pre-repair red was not preserved",
    )
    by_id = {row.get("step_id"): row for row in steps}
    require('"ok": true' in by_id.get("shared_strict_validator", {}).get("stdout", ""), "strict validator not green")
    require("20 passed" in by_id.get("focused_tests", {}).get("stdout", ""), "focused tests not 20/20")
    require('"violation_total": 0' in by_id.get("contract_lint", {}).get("stdout", ""), "contract lint red")
    source_head = receipt.get("source_head", "")
    head_check = subprocess.run(
        ["git", "cat-file", "-e", f"{source_head}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    require(head_check.returncode == 0, "source commit is unavailable")
    if verify_files:
        for binding in receipt.get("source_bindings", []) + receipt.get("artifact_bindings", []):
            path = ROOT / binding.get("path", "")
            require(path.is_file(), f"bound file missing: {path}")
            if path.is_file():
                require(sha256(path) == binding.get("sha256"), f"bound file hash drift: {path}")
    return failures


def main() -> int:
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    failures = validate(receipt, verify_files=True)
    mutations = []
    for name, mutate in (
        ("open_launch", lambda value: value.__setitem__("official_launch_allowed", True)),
        ("flip_step", lambda value: value["steps"][0].__setitem__("returncode", 1)),
        (
            "erase_manifest_tracking",
            lambda value: value["content_checks"].__setitem__("carrier_manifest_tracked", False),
        ),
        (
            "erase_artifact_hash",
            lambda value: value["artifact_bindings"][0].__setitem__("sha256", "0" * 64),
        ),
    ):
        candidate = copy.deepcopy(receipt)
        mutate(candidate)
        mutations.append({"case": name, "rejected": bool(validate(candidate, verify_files=True))})
    all_mutations_rejected = all(row["rejected"] for row in mutations)
    if not all_mutations_rejected:
        failures.append("mutation self-test is red")
    result = {
        "schema": "codex_ratchet.v8_integration_repair.gate_validation.v1",
        "ok": not failures,
        "failures": failures,
        "mutation_selftest": {"all_rejected": all_mutations_rejected, "cases": mutations},
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "official_launch_allowed": False,
        "release_eligible": False,
        "scientific_claim_proven": False,
        "claim_ceiling": "independent validation of isolated integration-repair evidence only",
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT_PATH), "ok": result["ok"]}, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
