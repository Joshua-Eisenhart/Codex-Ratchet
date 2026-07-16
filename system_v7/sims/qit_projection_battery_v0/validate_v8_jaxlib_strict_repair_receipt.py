#!/usr/bin/env python3
"""Independent fail-closed validator for the isolated QIT jaxlib repair."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parents[2]
RECEIPT_PATH = SIM_DIR / "results" / "v8_jaxlib_strict_repair_receipt.json"
ENVELOPE_PATH = SIM_DIR / "results" / "qit_projection_battery_v0_envelope_results.json"
OUT_PATH = SIM_DIR / "results" / "v8_jaxlib_strict_repair_validation.json"
EXPECTED_STEPS = [
    "main",
    "jax",
    "pytorch",
    "julia",
    "envelope",
    "packet_validator",
    "shared_strict_validator",
    "validator_tests",
    "packet_tests",
    "contract_lint",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(receipt: dict[str, Any], envelope: dict[str, Any], *, verify_files: bool) -> list[str]:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    require(receipt.get("schema") == "codex_ratchet.qit_projection_battery_v0.jaxlib_strict_repair_receipt.v1", "bad receipt schema")
    require(receipt.get("classification") == "isolated_repair_candidate", "classification drift")
    require(receipt.get("observed_head") == receipt.get("base_commit") == "fe6487de5136d18e7471952a2aa70595cc0f5cf7", "base commit drift")
    for field in ("promotion_allowed", "formal_admission_allowed", "release_eligible", "official_launch_allowed", "scientific_claim_proven", "llm_gate_used", "install_attempted"):
        require(receipt.get(field) is False, f"{field} must remain false")
    require(receipt.get("all_steps_pass") is True and receipt.get("content_pass") is True and receipt.get("repair_gate_pass") is True, "repair gate is not green")
    steps = receipt.get("steps", [])
    require([row.get("step_id") for row in steps] == EXPECTED_STEPS, "step ledger drift")
    require(all(row.get("pass") is True and row.get("returncode") == 0 for row in steps), "one or more repair steps are red")
    by_id = {row.get("step_id"): row for row in steps}
    require('"ok": true' in by_id.get("shared_strict_validator", {}).get("stdout", ""), "shared strict validator did not return ok")
    require("14 passed" in by_id.get("validator_tests", {}).get("stdout", ""), "validator tests did not report 14 passed")
    require("3 passed" in by_id.get("packet_tests", {}).get("stdout", ""), "packet tests did not report 3 passed")
    require('"violation_total": 0' in by_id.get("contract_lint", {}).get("stdout", ""), "contract lint is not green")
    required_changed = {
        "scripts/audit_three_engine_source_claims.py",
        "scripts/validate_three_engine_sim_result.py",
        "system_v5/tests/test_three_engine_sim_result_validator.py",
        "system_v7/sims/qit_projection_battery_v0/qit_projection_battery_v0_envelope.py",
    }
    require(required_changed <= set(receipt.get("changed_paths", [])), "repair source path missing from diff")
    if verify_files:
        for binding in receipt.get("source_bindings", []) + receipt.get("result_bindings", []):
            path = Path(binding.get("path", ""))
            require(path.is_file(), f"bound file missing: {path}")
            if path.is_file():
                require(sha256(path) == binding.get("sha256"), f"bound file hash drift: {path}")
    require(envelope.get("all_pass") is True and envelope.get("classification") == "scratch_diagnostic", "QIT envelope is not scratch green")
    require(envelope.get("promotion_allowed") is False and envelope.get("formal_admission_allowed") is False, "QIT envelope ceiling opened")
    require("jaxlib" in envelope.get("claim_path_tools", []), "jaxlib missing from claim path tools")
    require(envelope.get("TOOL_MANIFEST", {}).get("jaxlib", {}).get("used") is True, "jaxlib manifest use missing")
    require(envelope.get("TOOL_INTEGRATION_DEPTH", {}).get("jaxlib") == "load_bearing", "jaxlib depth is not load-bearing")
    require(bool(envelope.get("tool_intent", {}).get("engine_tool_intent", {}).get("jax", {}).get("jaxlib")), "jaxlib exact tool intent missing")
    jax = envelope.get("engines", {}).get("jax", {})
    require("jaxlib" in jax.get("aligned_packages_load_bearing", []), "jaxlib missing from JAX load-bearing set")
    require(bool(jax.get("package_observables", {}).get("jaxlib")), "jaxlib package observable missing")
    test_source = ROOT / "system_v5/tests/test_three_engine_sim_result_validator.py"
    if test_source.is_file():
        require("test_source_audit_accepts_jaxlib_client_observable_but_rejects_import_only" in test_source.read_text(encoding="utf-8"), "import-only negative-control test missing")
    return failures


def main() -> int:
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    envelope = json.loads(ENVELOPE_PATH.read_text(encoding="utf-8"))
    failures = validate(receipt, envelope, verify_files=True)
    mutation_records = []
    for name, mutate in (
        ("open_launch", lambda value: value.__setitem__("official_launch_allowed", True)),
        ("flip_step", lambda value: value["steps"][0].__setitem__("returncode", 1)),
        ("erase_source_hash", lambda value: value["source_bindings"][0].__setitem__("sha256", "0" * 64)),
    ):
        candidate = copy.deepcopy(receipt)
        mutate(candidate)
        rejected = bool(validate(candidate, envelope, verify_files=True))
        mutation_records.append({"case": name, "rejected": rejected})
    envelope_mutation = copy.deepcopy(envelope)
    envelope_mutation["tool_intent"]["engine_tool_intent"]["jax"].pop("jaxlib")
    mutation_records.append({"case": "erase_jaxlib_intent", "rejected": bool(validate(receipt, envelope_mutation, verify_files=False))})
    all_mutations_rejected = all(row["rejected"] for row in mutation_records)
    if not all_mutations_rejected:
        failures.append("validator mutation self-test is red")
    result = {
        "schema": "codex_ratchet.qit_projection_battery_v0.jaxlib_strict_repair_validation.v1",
        "ok": not failures,
        "failures": failures,
        "mutation_selftest": {"all_rejected": all_mutations_rejected, "cases": mutation_records},
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "release_eligible": False,
        "official_launch_allowed": False,
        "scientific_claim_proven": False,
        "claim_ceiling": "independent validation of an isolated QIT strict-gate repair candidate only",
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT_PATH), "ok": result["ok"], "mutation_selftest": all_mutations_rejected}, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
