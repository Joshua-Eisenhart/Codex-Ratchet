#!/usr/bin/env python3
"""Post-run diagnosis of the frozen campaign red; never opens a campaign gate."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SPEC = HERE / "campaign_spec.json"
PREREG = HERE / "preregistration.json"
EXECUTION = HERE / "results" / "campaign_execution.json"
FROZEN_VALIDATION = HERE / "results" / "campaign_validation.json"
OUT = HERE / "results" / "postrun_diagnostics.json"
DEEP_ROOT = Path("/Users/joshuaeisenhart/.config/superpowers/worktrees/Codex-Ratchet/deep-stack-stress-20260714")
DEEP_ESTATE = DEEP_ROOT / "system_v5/ops/tooling/deep_stack_stress_20260714/results/deep_stack_estate_v8_nonofficial_regression_20260715.json"
DEEP_VALIDATION = DEEP_ROOT / "system_v5/ops/tooling/deep_stack_stress_20260714/results/deep_stack_validation_v8_nonofficial_regression_20260715.json"
FIRST_RUNG_ROOT = Path("/Users/joshuaeisenhart/.config/superpowers/worktrees/Codex-Ratchet/v8-first-rungs-20260715")
FIRST_G0_G9 = FIRST_RUNG_ROOT / "system_v7/sims/tolerance_to_equivalence_ratchet_rung_v0/results/g0_g9_report.json"
FIRST_FINAL = FIRST_RUNG_ROOT / "system_v7/sims/tolerance_to_equivalence_ratchet_rung_v0/results/final_report.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str]) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False, timeout=300)
    return {"command": command, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def case(payload: dict[str, Any], case_id: str) -> dict[str, Any]:
    return next(row for row in payload["cases"] if row["case_id"] == case_id)


def step(payload: dict[str, Any], case_id: str, step_id: str) -> dict[str, Any]:
    return next(row for row in case(payload, case_id)["steps"] if row["step_id"] == step_id)


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    execution = json.loads(EXECUTION.read_text(encoding="utf-8"))
    frozen_validation = json.loads(FROZEN_VALIDATION.read_text(encoding="utf-8"))
    py = spec["runtime_contract"]["python"]
    lint = run([
        py,
        "-B",
        "scripts/lint_sim_contract.py",
        "system_v7/sims/qit_projection_battery_v0/qit_projection_battery_v0.py",
        "system_v7/sims/qit_projection_battery_v0/qit_projection_battery_v0_envelope.py",
    ])
    tests = run([
        py,
        "-B",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "system_v7/sims/qit_projection_battery_v0/tests",
    ])
    strict = run([
        py,
        "-B",
        "scripts/validate_three_engine_sim_result.py",
        "system_v7/sims/qit_projection_battery_v0/results/qit_projection_battery_v0_envelope_results.json",
        "--require-pytorch",
        "--strict-source-backed",
        "--require-tool-intent",
    ])
    strict_text = f"{strict['stdout']}\n{strict['stderr']}"
    deep_estate = json.loads(DEEP_ESTATE.read_text(encoding="utf-8"))
    deep_validation = json.loads(DEEP_VALIDATION.read_text(encoding="utf-8"))
    historical_first_final = json.loads(FIRST_FINAL.read_text(encoding="utf-8"))
    deep_snapshot = case(execution, "DS_ALL_FINITE_ROSTER")["artifacts_after"]
    edge_kinds: dict[str, int] = {}
    for edge in deep_estate.get("integration_edge_receipts", []):
        kind = str(edge.get("evidence_kind", "unknown"))
        edge_kinds[kind] = edge_kinds.get(kind, 0) + 1
    qit_case = case(execution, "OLD_QIT_PROJECTION_BATTERY")
    qit_strict = step(execution, "OLD_QIT_PROJECTION_BATTERY", "generic_validator")
    qit_lint = step(execution, "OLD_QIT_PROJECTION_BATTERY", "lint")
    qit_tests = step(execution, "OLD_QIT_PROJECTION_BATTERY", "tests")
    checks = {
        "frozen_spec_hash_still_matches_preregistration": sha256(SPEC) == prereg["source_state"]["spec_sha256"],
        "frozen_campaign_is_red": execution.get("execution_integrity_pass") is False,
        "only_qit_case_unexpected": [row["case_id"] for row in execution["cases"] if not row.get("case_execution_pass")] == ["OLD_QIT_PROJECTION_BATTERY"],
        "qit_packet_validator_green": step(execution, "OLD_QIT_PROJECTION_BATTERY", "packet_validator").get("returncode") == 0,
        "qit_shared_strict_gate_red": qit_strict.get("returncode") == 1 and "source-token-thin: jaxlib" in f"{qit_strict.get('stdout_tail', '')}{qit_strict.get('stderr_tail', '')}",
        "qit_downstream_steps_were_blocked_not_timed_out": qit_lint.get("executed") is False and qit_tests.get("executed") is False and qit_lint.get("blocked_by") == "generic_validator" and qit_tests.get("blocked_by") == "generic_validator",
        "qit_followup_lint_green": lint["returncode"] == 0 and '"violation_total": 0' in lint["stdout"],
        "qit_followup_tests_green": tests["returncode"] == 0 and "3 passed" in tests["stdout"],
        "qit_followup_strict_red_same_reason": strict["returncode"] == 1 and "source-token-thin: jaxlib" in strict_text,
        "deep_estate_95_tool_rows_green": deep_estate.get("producer_summary", {}).get("deep_stress_tool_count") == 95 and deep_estate.get("producer_summary", {}).get("operational_pass_count") == 95,
        "deep_validator_86_operational_receipts_green": deep_validation.get("receipt_valid") is True and deep_validation.get("operational_pass") is True and deep_validation.get("summary", {}).get("required_operational_count") == 86 and deep_validation.get("summary", {}).get("operational_pass_count") == 86,
        "deep_estate_hash_matches_frozen_campaign_snapshot": len(deep_snapshot) == 2 and deep_snapshot[0].get("path") == str(DEEP_ESTATE) and deep_snapshot[0].get("sha256") == sha256(DEEP_ESTATE),
        "deep_validation_hash_matches_frozen_campaign_snapshot": len(deep_snapshot) == 2 and deep_snapshot[1].get("path") == str(DEEP_VALIDATION) and deep_snapshot[1].get("sha256") == sha256(DEEP_VALIDATION),
        "deep_edge_evidence_kinds_are_bounded": edge_kinds == {"direct_value_handoff": 1, "independent_shared_crosscheck": 3, "member_cohealth_compatibility_witness": 25},
        "historical_first_tooth_final_is_stale_after_fresh_g0_g9": historical_first_final.get("artifacts", {}).get("g0_g9_report", {}).get("sha256") != sha256(FIRST_G0_G9),
        "frozen_meta_validator_selftest_green": frozen_validation.get("validator_mutation_selftest", {}).get("all_rejected") is True,
        "official_launch_remains_closed": all(payload.get("official_launch_allowed") is False for payload in (spec, prereg, execution, frozen_validation)),
    }
    result = {
        "schema": "codex_ratchet.v8_nonofficial_stress_campaign.postrun_diagnostics.v1",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "classification": "postrun_diagnostic_not_preregistered_not_a_gate_rewrite",
        "source_path": str(Path(__file__).resolve()),
        "source_sha256": sha256(Path(__file__)),
        "bound_inputs": {str(path): sha256(path) for path in (SPEC, PREREG, EXECUTION, FROZEN_VALIDATION, DEEP_ESTATE, DEEP_VALIDATION, FIRST_G0_G9, FIRST_FINAL)},
        "checks": checks,
        "diagnostic_integrity_pass": all(checks.values()),
        "campaign_integrity_pass": False,
        "all_systems_green": False,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "release_eligible": False,
        "official_launch_allowed": False,
        "scientific_claim_proven": False,
        "llm_gate_used": False,
        "install_attempted": False,
        "unexpected_red": {
            "case_id": qit_case["case_id"],
            "step_id": qit_strict["step_id"],
            "returncode": qit_strict["returncode"],
            "reason": "shared strict validator rejects declared JAX jaxlib evidence as source-token-thin and tool-intent-inexact",
            "downstream_in_frozen_run": "blocked fail-closed",
            "followup_lint_returncode": lint["returncode"],
            "followup_tests_returncode": tests["returncode"],
            "followup_strict_returncode": strict["returncode"],
        },
        "stale_historical_artifact": {
            "path": str(FIRST_FINAL),
            "reason": "fresh G0-G9 replay changed the bound report while no fresh G10 was run; the historical final report fails its own hash validator",
            "fresh_authority": str(FIRST_G0_G9),
        },
        "frozen_meta_validator_findings": {
            "finding_count": len(frozen_validation.get("failures", [])),
            "diagnosed_false_secondary_findings": [
                "skipped QIT lint/tests were reported as timeouts because skipped rows omit timed_out",
                "deep-stack producer counts 95 stress-required tool rows while the strict validator counts 86 operational receipt obligations; both layers are green",
                "frozen rung summary must not mark R3 reproduced while its QIT strict gate is unexpected red",
            ],
        },
        "deep_edge_evidence_kinds": edge_kinds,
        "rung_states": [
            {"rung_id": "R0_FROZEN_BOUNDARY", "state": "GREEN_NONOFFICIAL"},
            {"rung_id": "R1_RUNTIME_CARRIER", "state": "CANONICAL_GREEN_PORTABILITY_RED"},
            {"rung_id": "R2_FINITE_STACK", "state": "GREEN_95_OF_95_TOOL_ROWS_29_OF_29_EDGES"},
            {"rung_id": "R3_OLD_SIM_REGRESSION", "state": "HOLD_QIT_SHARED_STRICT_GATE_RED"},
            {"rung_id": "R4_FIRST_TOOTH_CANDIDATE", "state": "GREEN_G0_G9_HOLD_PENDING_LEV"},
            {"rung_id": "R5_LATER_RUNG_SCRATCH", "state": "MECHANICAL_GREENS_STRICT_REDS_PRESERVED"},
            {"rung_id": "R6_PROCESS_ADMISSION", "state": "HOLD_LEV_MONITOR_TO_PROOF_RED"},
        ],
        "followup_commands": {"lint": lint, "tests": tests, "strict": strict},
        "claim_ceiling": "post-run diagnosis of a frozen nonofficial campaign; cannot promote, admit, release, or authorize launch",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT), "diagnostic_integrity_pass": result["diagnostic_integrity_pass"], "campaign_integrity_pass": False}, sort_keys=True))
    return 0 if result["diagnostic_integrity_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
