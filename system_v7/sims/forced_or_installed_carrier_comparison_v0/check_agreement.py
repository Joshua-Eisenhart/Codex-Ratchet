#!/usr/bin/env python3
"""Agreement envelope for forced_or_installed_carrier_comparison_v0."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive readback of independent engine receipts and envelope write",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive path binding for result files inside this sim directory",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "pathlib": "supportive",
}

SIM_ID = "forced_or_installed_carrier_comparison_v0"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def py_fixture(result: dict[str, Any], fixture: str, solver: str) -> dict[str, Any]:
    return result["fixture_results"][fixture][solver]


def julia_fixture(result: dict[str, Any], fixture: str) -> dict[str, Any]:
    return result["fixture_results"][fixture]["julia_z3"]


def py_control(result: dict[str, Any], control: str, solver: str) -> dict[str, Any]:
    return result["fixture_results"]["load_bearing_controls"][control][solver]


def julia_control(result: dict[str, Any], control: str) -> dict[str, Any]:
    return result["fixture_results"]["load_bearing_controls"][control]["julia_z3"]


def main() -> int:
    spec = load_json(HERE / "spec.json")
    jax_path = RESULTS / f"{SIM_ID}_jax_results.json"
    julia_path = RESULTS / f"{SIM_ID}_julia_results.json"
    pytorch_path = RESULTS / f"{SIM_ID}_pytorch_results.json"
    jax_result = load_json(jax_path)
    julia_result = load_json(julia_path)
    pytorch_result = load_json(pytorch_path)
    failures: list[str] = []

    for name, result in (("jax", jax_result), ("julia", julia_result), ("pytorch", pytorch_result)):
        if result.get("reads_peer_result") is not False:
            failures.append(f"{name}: reads_peer_result is not false")
        if result.get("classification") != "scratch_diagnostic":
            failures.append(f"{name}: classification is not scratch_diagnostic")
        if result.get("promotion_allowed") is not False:
            failures.append(f"{name}: promotion_allowed is not false")
        if result.get("formal_admission_allowed") is not False:
            failures.append(f"{name}: formal_admission_allowed is not false")
        if result.get("all_pass") is not True:
            failures.append(f"{name}: all_pass is not true")

    installed_statuses = {
        "jax_z3": py_fixture(jax_result, "installed_incomplete", "z3")["solver_status"],
        "jax_cvc5": py_fixture(jax_result, "installed_incomplete", "cvc5")["solver_status"],
        "pytorch_z3": py_fixture(pytorch_result, "installed_incomplete", "z3")["solver_status"],
        "pytorch_cvc5": py_fixture(pytorch_result, "installed_incomplete", "cvc5")["solver_status"],
        "julia_z3": julia_fixture(julia_result, "installed_incomplete")["solver_status"],
    }
    forced_statuses = {
        "jax_z3": py_fixture(jax_result, "forced_complete", "z3")["solver_status"],
        "jax_cvc5": py_fixture(jax_result, "forced_complete", "cvc5")["solver_status"],
        "pytorch_z3": py_fixture(pytorch_result, "forced_complete", "z3")["solver_status"],
        "pytorch_cvc5": py_fixture(pytorch_result, "forced_complete", "cvc5")["solver_status"],
        "julia_z3": julia_fixture(julia_result, "forced_complete")["solver_status"],
    }
    installed_verdicts = {
        "jax_z3": py_fixture(jax_result, "installed_incomplete", "z3")["verdict"],
        "jax_cvc5": py_fixture(jax_result, "installed_incomplete", "cvc5")["verdict"],
        "pytorch_z3": py_fixture(pytorch_result, "installed_incomplete", "z3")["verdict"],
        "pytorch_cvc5": py_fixture(pytorch_result, "installed_incomplete", "cvc5")["verdict"],
        "julia_z3": julia_fixture(julia_result, "installed_incomplete")["verdict"],
    }
    forced_verdicts = {
        "jax_z3": py_fixture(jax_result, "forced_complete", "z3")["verdict"],
        "jax_cvc5": py_fixture(jax_result, "forced_complete", "cvc5")["verdict"],
        "pytorch_z3": py_fixture(pytorch_result, "forced_complete", "z3")["verdict"],
        "pytorch_cvc5": py_fixture(pytorch_result, "forced_complete", "cvc5")["verdict"],
        "julia_z3": julia_fixture(julia_result, "forced_complete")["verdict"],
    }

    if any(status == "unknown" for status in list(installed_statuses.values()) + list(forced_statuses.values())):
        failures.append("headline solver returned unknown")
    if any(status != "sat" for status in installed_statuses.values()):
        failures.append("installed fixture did not return SAT across all solver legs")
    if any(verdict != "installed" for verdict in installed_verdicts.values()):
        failures.append("installed fixture did not return installed across all solver legs")
    if any(status != "unsat" for status in forced_statuses.values()):
        failures.append("forced fixture did not return UNSAT across all solver legs")
    if any(verdict != "forced" for verdict in forced_verdicts.values()):
        failures.append("forced fixture did not return forced across all solver legs")

    controls = {
        "jax": jax_result["fixture_results"]["load_bearing_controls"],
        "pytorch": pytorch_result["fixture_results"]["load_bearing_controls"],
        "julia": julia_result["fixture_results"]["load_bearing_controls"],
    }

    for result_name, result in (("jax", jax_result), ("pytorch", pytorch_result)):
        for solver in ("z3", "cvc5"):
            if py_control(result, "forced_reproduce_off_mismatch", solver)["solver_status"] != "sat":
                failures.append(f"{result_name}:{solver}: forced reproduce OFF mismatch control is not SAT")
            if py_control(result, "invalid_measured_z_reproduce_on", solver)["solver_status"] != "unsat":
                failures.append(f"{result_name}:{solver}: invalid measured Z reproduce ON is not UNSAT")
            if py_control(result, "invalid_measured_z_reproduce_off_mismatch", solver)["solver_status"] != "sat":
                failures.append(f"{result_name}:{solver}: invalid measured Z reproduce OFF mismatch is not SAT")
            if py_control(result, "forced_scrambled_values", solver)["solver_status"] != "sat":
                failures.append(f"{result_name}:{solver}: forced scrambled value control is not SAT")
            if py_control(result, "installed_scrambled_values", solver)["solver_status"] != "sat":
                failures.append(f"{result_name}:{solver}: installed scrambled value control is not SAT")
            if py_control(result, "installed_without_non_isomorphism", solver)["solver_status"] != "sat":
                failures.append(f"{result_name}:{solver}: installed noniso OFF control is not SAT")
            if py_control(result, "forced_without_non_isomorphism", solver)["solver_status"] != "sat":
                failures.append(f"{result_name}:{solver}: forced noniso OFF control is not SAT")

    if julia_control(julia_result, "forced_reproduce_off_mismatch")["solver_status"] != "sat":
        failures.append("julia_z3: forced reproduce OFF mismatch control is not SAT")
    if julia_control(julia_result, "invalid_measured_z_reproduce_on")["solver_status"] != "unsat":
        failures.append("julia_z3: invalid measured Z reproduce ON is not UNSAT")
    if julia_control(julia_result, "invalid_measured_z_reproduce_off_mismatch")["solver_status"] != "sat":
        failures.append("julia_z3: invalid measured Z reproduce OFF mismatch is not SAT")
    if julia_control(julia_result, "forced_scrambled_values")["solver_status"] != "sat":
        failures.append("julia_z3: forced scrambled value control is not SAT")
    if julia_control(julia_result, "installed_scrambled_values")["solver_status"] != "sat":
        failures.append("julia_z3: installed scrambled value control is not SAT")
    if julia_control(julia_result, "installed_without_non_isomorphism")["solver_status"] != "sat":
        failures.append("julia_z3: installed noniso OFF control is not SAT")
    if julia_control(julia_result, "forced_without_non_isomorphism")["solver_status"] != "sat":
        failures.append("julia_z3: forced noniso OFF control is not SAT")

    torch_depth = pytorch_result["TOOL_INTEGRATION_DEPTH"]
    if torch_depth.get("torch.func") != "supportive":
        failures.append("torch.func is not demoted to supportive")

    build_status = "PASS" if not failures else "BUILD FAILED"
    installed_witness = py_fixture(jax_result, "installed_incomplete", "z3")["witness"]
    installed_cvc5_witness = py_fixture(jax_result, "installed_incomplete", "cvc5")["witness"]
    envelope = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engine": "envelope_controller",
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": not failures,
        "build_status": build_status,
        "claim": "For these finite fixtures, the incomplete Z/X table is installed by a second density-carrier witness, while the complete Z/X/Y table is forced only in the coordinate sense: no second carrier with different (a,b,c) coordinates reproduces the table against C1.",
        "claim_ceiling": spec["claim_ceiling"],
        "decision_rule": spec["decision_rule"],
        "carrier_type": spec["carrier_type"],
        "readout_definition": spec["readout_definition"],
        "same_decide_code": {
            "python": str(HERE / "carrier_decision_core.py"),
            "julia": str(HERE / "forced_or_installed_carrier_comparison_v0_julia.jl"),
        },
        "claim_path_tools": ["Z3", "z3", "cvc5"],
        "control_only_tools": [],
        "TOOL_MANIFEST": {
            "Z3": julia_result["TOOL_MANIFEST"]["Z3"],
            "z3": jax_result["TOOL_MANIFEST"]["z3"],
            "cvc5": jax_result["TOOL_MANIFEST"]["cvc5"],
            "torch.func": pytorch_result["TOOL_MANIFEST"]["torch.func"],
            "json": TOOL_MANIFEST["json"],
            "pathlib": TOOL_MANIFEST["pathlib"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "Z3": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "torch.func": "supportive",
            "json": "supportive",
            "pathlib": "supportive",
        },
        "engines": {
            "julia": {
                "ran": True,
                "source_path": julia_result["source_path"],
                "source_sha256": julia_result["source_sha256"],
                "result_path": str(julia_path),
                "packages_used": julia_result["packages_used"],
                "aligned_packages_load_bearing": julia_result["aligned_packages_load_bearing"],
                "package_observables": julia_result["package_observables"],
                "reads_peer_result": False,
                "classification": "scratch_diagnostic",
                "promotion_allowed": False,
                "formal_admission_allowed": False,
                "julia_project": julia_result["julia_project"],
            },
            "jax": {
                "ran": True,
                "source_path": jax_result["source_path"],
                "source_sha256": jax_result["source_sha256"],
                "result_path": str(jax_path),
                "packages_used": jax_result["packages_used"],
                "aligned_packages_load_bearing": jax_result["aligned_packages_load_bearing"],
                "package_observables": jax_result["package_observables"],
                "reads_peer_result": False,
                "classification": "scratch_diagnostic",
                "promotion_allowed": False,
                "formal_admission_allowed": False,
            },
            "pytorch": {
                "ran": True,
                "source_path": pytorch_result["source_path"],
                "source_sha256": pytorch_result["source_sha256"],
                "result_path": str(pytorch_path),
                "packages_used": pytorch_result["packages_used"],
                "aligned_packages_load_bearing": pytorch_result["aligned_packages_load_bearing"],
                "package_observables": pytorch_result["package_observables"],
                "reads_peer_result": False,
                "classification": "scratch_diagnostic",
                "promotion_allowed": False,
                "formal_admission_allowed": False,
            },
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": forced_statuses["jax_z3"],
                "forced_fixture_verdict": forced_statuses["jax_z3"],
                "installed_fixture_verdict": installed_statuses["jax_z3"],
                "claim": "Python z3 returns UNSAT for complete-table coordinate-distinct C2 and SAT for incomplete-table C2.",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": forced_statuses["jax_cvc5"],
                "forced_fixture_verdict": forced_statuses["jax_cvc5"],
                "installed_fixture_verdict": installed_statuses["jax_cvc5"],
                "claim": "Python cvc5 agrees with z3 on both fixture polarities.",
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": forced_statuses["julia_z3"],
                "forced_fixture_verdict": forced_statuses["julia_z3"],
                "installed_fixture_verdict": installed_statuses["julia_z3"],
                "claim": "Z3.jl agrees on both fixture polarities.",
            },
        },
        "fixture_verdicts": {
            "installed_incomplete": {
                "statuses": installed_statuses,
                "verdicts": installed_verdicts,
            },
            "forced_complete": {
                "statuses": forced_statuses,
                "verdicts": forced_verdicts,
            },
        },
        "free_variable_declarations": {
            "installed_z3": py_fixture(jax_result, "installed_incomplete", "z3")["second_carrier_variables"],
            "installed_cvc5": py_fixture(jax_result, "installed_incomplete", "cvc5")["second_carrier_variables"],
            "forced_z3": py_fixture(jax_result, "forced_complete", "z3")["second_carrier_variables"],
            "forced_cvc5": py_fixture(jax_result, "forced_complete", "cvc5")["second_carrier_variables"],
            "installed_julia_z3": julia_fixture(julia_result, "installed_incomplete")["second_carrier_variables"],
            "forced_julia_z3": julia_fixture(julia_result, "forced_complete")["second_carrier_variables"],
        },
        "non_isomorphism_predicate": spec["non_isomorphism_predicate"],
        "installed_multiplicity_witness": {
            "z3": installed_witness,
            "cvc5": installed_cvc5_witness,
            "julia_z3": julia_fixture(julia_result, "installed_incomplete")["witness_model_string"],
        },
        "load_bearing_controls": controls,
        "reproduce_on_off_comparison": {
            "jax": jax_result["headline_checks"]["reproduce_on_off"],
            "pytorch": pytorch_result["headline_checks"]["reproduce_on_off"],
            "julia": julia_result["headline_checks"]["reproduce_on_off"],
        },
        "scramble_controls": {
            "installed_scrambled_values": {
                "jax_z3": py_control(jax_result, "installed_scrambled_values", "z3")["solver_status"],
                "jax_cvc5": py_control(jax_result, "installed_scrambled_values", "cvc5")["solver_status"],
                "julia_z3": julia_control(julia_result, "installed_scrambled_values")["solver_status"],
            },
            "forced_scrambled_values": {
                "jax_z3": py_control(jax_result, "forced_scrambled_values", "z3")["solver_status"],
                "jax_cvc5": py_control(jax_result, "forced_scrambled_values", "cvc5")["solver_status"],
                "julia_z3": julia_control(julia_result, "forced_scrambled_values")["solver_status"],
            },
        },
        "positive_tests": {
            "installed_incomplete": "SAT under z3, cvc5, and Z3.jl",
            "forced_complete": "UNSAT under z3, cvc5, and Z3.jl for coordinate-distinct C2 vs C1",
        },
        "negative_tests": {
            "non_isomorphism_constraint_removed": "both headline fixtures SAT under all solver legs",
            "reproduce_table_constraint_removed_with_mismatch": "forced and invalid controls differ from reproduce-ON status",
            "scrambled_complete_values": "SAT, so forced is not independent of measured values",
        },
        "surviving_alternatives": spec["surviving_alternatives"],
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": "not_scoped",
            "consumer_policy": "density-carrier coordinate variables and Z3.jl SMT only; no algebra artifact consumed",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia_result["julia_project"], "packages": julia_result["packages_used"], "role": "semantic_owner"},
            "jax": {"packages": jax_result["packages_used"], "role": "proof_side_worker"},
            "pytorch": {"packages": pytorch_result["packages_used"], "role": "supportive_readback_worker"},
            "tensor_exchange": "not_scoped",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": {"forced": forced_verdicts["julia_z3"], "installed": installed_verdicts["julia_z3"]},
                "jax": {"forced": forced_verdicts["jax_z3"], "installed": installed_verdicts["jax_z3"]},
                "pytorch": {"forced": forced_verdicts["pytorch_z3"], "installed": installed_verdicts["pytorch_z3"]},
            },
            "max_divergence": 0.0 if not failures else 1.0,
            "notes": [
                "Agreement is envelope plumbing after independent local lane runs.",
                "The claim path is the second-carrier SMT existence search, not cross-engine parity by itself.",
            ],
        },
        "tool_calls": jax_result["tool_calls"] + julia_result["tool_calls"] + pytorch_result["tool_calls"],
        "engine_result_paths": {"jax": str(jax_path), "julia": str(julia_path), "pytorch": str(pytorch_path)},
        "failures": failures,
    }

    out_path = RESULTS / f"{SIM_ID}_three_engine_results.json"
    out_path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": envelope["all_pass"],
                "result_path": str(out_path),
                "build_status": envelope["build_status"],
                "installed": installed_verdicts,
                "forced": forced_verdicts,
                "reproduce_on_off": envelope["reproduce_on_off_comparison"],
                "solver_found_C2": envelope["installed_multiplicity_witness"],
                "failures": failures,
            },
            indent=2,
        )
    )
    return 0 if envelope["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
