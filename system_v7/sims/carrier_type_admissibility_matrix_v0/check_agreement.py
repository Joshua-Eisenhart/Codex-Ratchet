#!/usr/bin/env python3
"""Agreement envelope for carrier_type_admissibility_matrix_v0."""

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

SIM_ID = "carrier_type_admissibility_matrix_v0"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def jax_fixture(jax_result: dict[str, Any], solver: str, fixture: str) -> dict[str, Any]:
    return jax_result["headline_matrix"][solver][fixture]


def jax_control(jax_result: dict[str, Any], solver: str, control: str) -> dict[str, Any]:
    return jax_result["load_bearing_controls"][solver][control]


def julia_fixture(julia_result: dict[str, Any], fixture: str) -> dict[str, Any]:
    return julia_result["headline_matrix"]["julia_z3"][fixture]


def sorted_sets(row: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "allowed_set": list(row["allowed_set"]),
        "excluded_set": list(row["excluded_set"]),
        "unknown_set": list(row["unknown_set"]),
    }


def collect_matrix(spec: dict[str, Any], jax_result: dict[str, Any], julia_result: dict[str, Any]) -> dict[str, Any]:
    matrix: dict[str, Any] = {}
    for fixture in spec["headline_fixtures"]:
        matrix[fixture] = {
            "z3": sorted_sets(jax_fixture(jax_result, "z3", fixture)),
            "cvc5": sorted_sets(jax_fixture(jax_result, "cvc5", fixture)),
            "julia_z3": sorted_sets(julia_fixture(julia_result, fixture)),
        }
    return matrix


def compare_solver_sets(matrix: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for fixture, rows in matrix.items():
        z3_allowed = rows["z3"]["allowed_set"]
        z3_excluded = rows["z3"]["excluded_set"]
        for solver in ("cvc5", "julia_z3"):
            if rows[solver]["allowed_set"] != z3_allowed:
                failures.append(f"{fixture}:{solver}: allowed_set disagrees with z3")
            if rows[solver]["excluded_set"] != z3_excluded:
                failures.append(f"{fixture}:{solver}: excluded_set disagrees with z3")
        for solver, row in rows.items():
            if row["unknown_set"]:
                failures.append(f"{fixture}:{solver}: headline unknown_set is non-empty")
    return failures


def fixture_verdict(row: dict[str, Any]) -> str:
    if len(row["allowed_set"]) >= 2:
        return "installed"
    if len(row["allowed_set"]) == 1:
        return "single_allowed_by_panel"
    return "none_allowed"


def summarize_matrix(matrix: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for fixture, rows in matrix.items():
        z3_row = rows["z3"]
        out[fixture] = {
            "allowed_set": z3_row["allowed_set"],
            "excluded_set": z3_row["excluded_set"],
            "fixture_verdict": fixture_verdict(z3_row),
            "solver_rows": rows,
        }
    return out


def apply_by_construction_tags(spec: dict[str, Any], matrix_summary: dict[str, Any]) -> None:
    y_phase = spec["headline_fixtures"].get("y_phase_exclusion", {})
    if y_phase.get("by_construction") is True and "y_phase_exclusion" in matrix_summary:
        matrix_summary["y_phase_exclusion"]["by_construction_exclusions"] = {
            "real_rebit": {
                "by_construction": True,
                "load_bearing": False,
                "reason": y_phase.get(
                    "boundary_control_for",
                    "real_rebit has no Y degree of freedom; Y is fixed at 1/2 by construction.",
                ),
            }
        }


def reproduce_summary(jax_result: dict[str, Any], julia_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "z3": {
            carrier_type: row["z3"]
            for carrier_type, row in jax_result["headline_checks"]["reproduce_on_off_by_type"].items()
        },
        "cvc5": {
            carrier_type: row["cvc5"]
            for carrier_type, row in jax_result["headline_checks"]["reproduce_on_off_by_type"].items()
        },
        "julia_z3": julia_result["headline_checks"]["reproduce_on_off_by_type"],
    }


def isolation_passed(row: dict[str, Any]) -> bool:
    classical = row["classical_noncontextual"]
    return (
        row.get("passed") is True
        and classical["marginals_Z_X"] == "sat"
        and classical["branch_Z_X_ZX"] == "sat"
        and classical["branch_Z_X_XZ"] == "sat"
        and classical["joint_Z_X_ZX_XZ"] == "unsat"
        and row["complex_rho"]["joint_Z_X_ZX_XZ"] == "sat"
    )


def order_gap_clean_isolation(jax_result: dict[str, Any], julia_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "z3": jax_result["order_gap_clean_isolation"]["z3"],
        "cvc5": jax_result["order_gap_clean_isolation"]["cvc5"],
        "julia_z3": julia_result["order_gap_clean_isolation"],
    }


def main() -> int:
    spec = load_json(HERE / "spec.json")
    jax_path = RESULTS / f"{SIM_ID}_jax_results.json"
    julia_path = RESULTS / f"{SIM_ID}_julia_results.json"
    jax_result = load_json(jax_path)
    julia_result = load_json(julia_path)
    failures: list[str] = []

    for name, result in (("jax", jax_result), ("julia", julia_result)):
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

    matrix = collect_matrix(spec, jax_result, julia_result)
    failures.extend(compare_solver_sets(matrix))
    matrix_summary = summarize_matrix(matrix)
    apply_by_construction_tags(spec, matrix_summary)
    has_multiplicity = any(len(row["allowed_set"]) >= 2 for row in matrix_summary.values())
    has_exclusion = any(row["excluded_set"] and row["allowed_set"] for row in matrix_summary.values())
    if not has_multiplicity:
        failures.append("no fixture admits >=2 carrier types")
    if not has_exclusion:
        failures.append("no fixture has a genuine excluded type while another is admitted")

    expected_clean_allowed = ["quotient", "real_rebit", "complex_rho"]
    expected_clean_excluded = ["classical_noncontextual"]
    for solver, row in matrix["order_gap_clean"].items():
        if row["allowed_set"] != expected_clean_allowed:
            failures.append(f"order_gap_clean:{solver}: allowed_set is not {expected_clean_allowed}")
        if row["excluded_set"] != expected_clean_excluded:
            failures.append(f"order_gap_clean:{solver}: excluded_set is not {expected_clean_excluded}")

    isolation = order_gap_clean_isolation(jax_result, julia_result)
    for solver, row in isolation.items():
        if not isolation_passed(row):
            failures.append(f"order_gap_clean:{solver}: isolation proof did not pass")

    original = spec["scramble_pair"]["original"]
    scrambled = spec["scramble_pair"]["scrambled"]
    scramble_evidence = {
        "original": original,
        "scrambled": scrambled,
        "z3_original_allowed": matrix[original]["z3"]["allowed_set"],
        "z3_scrambled_allowed": matrix[scrambled]["z3"]["allowed_set"],
        "cvc5_original_allowed": matrix[original]["cvc5"]["allowed_set"],
        "cvc5_scrambled_allowed": matrix[scrambled]["cvc5"]["allowed_set"],
        "julia_z3_original_allowed": matrix[original]["julia_z3"]["allowed_set"],
        "julia_z3_scrambled_allowed": matrix[scrambled]["julia_z3"]["allowed_set"],
    }
    if scramble_evidence["z3_original_allowed"] == scramble_evidence["z3_scrambled_allowed"]:
        failures.append("z3 scramble did not change allowed set")
    if scramble_evidence["cvc5_original_allowed"] == scramble_evidence["cvc5_scrambled_allowed"]:
        failures.append("cvc5 scramble did not change allowed set")
    if scramble_evidence["julia_z3_original_allowed"] == scramble_evidence["julia_z3_scrambled_allowed"]:
        failures.append("julia_z3 scramble did not change allowed set")

    reproduce = reproduce_summary(jax_result, julia_result)
    for solver, by_type in reproduce.items():
        for carrier_type, row in by_type.items():
            if row.get("differs") is not True:
                failures.append(f"{solver}:{carrier_type}: reproduce ON/OFF did not differ")

    order_gap = matrix["order_gap_clean"]
    build_status = "PASS" if not failures else "BUILD FAILED"
    envelope = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engine": "envelope_controller",
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "lanes": ["julia", "jax"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "pytorch": "not_scoped; no graph/network/autograd claim path",
        },
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": not failures,
        "build_status": build_status,
        "claim": "For these finite fixtures, solver existence over free per-type carrier variables yields an allowed/excluded matrix. Multiplicity means installed. The load-bearing carrier-type negative is order_gap_clean for classical_noncontextual; y_phase_exclusion for real_rebit is by construction and kept as a boundary/control only.",
        "claim_ceiling": spec["claim_ceiling"],
        "decision_rule": spec["decision_rule"],
        "carrier_type_non_isomorphism": spec["carrier_type_non_isomorphism"],
        "readout_definitions": spec["readout_definitions"],
        "claim_path_tools": ["Z3", "z3", "cvc5"],
        "control_only_tools": [],
        "TOOL_MANIFEST": {
            "Z3": julia_result["TOOL_MANIFEST"]["Z3"],
            "z3": jax_result["TOOL_MANIFEST"]["z3"],
            "cvc5": jax_result["TOOL_MANIFEST"]["cvc5"],
            "json": TOOL_MANIFEST["json"],
            "pathlib": TOOL_MANIFEST["pathlib"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "Z3": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
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
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": order_gap["z3"]["excluded_set"] and "unsat" or "sat",
                "headline_fixture": "order_gap_clean",
                "carrier_type": "classical_noncontextual",
                "claim": "Python z3 excludes classical_noncontextual on order_gap_clean while admitting real_rebit and complex_rho.",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": order_gap["cvc5"]["excluded_set"] and "unsat" or "sat",
                "headline_fixture": "order_gap_clean",
                "carrier_type": "classical_noncontextual",
                "claim": "Python cvc5 agrees with z3 on the clean classical_noncontextual order-gap exclusion.",
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": order_gap["julia_z3"]["excluded_set"] and "unsat" or "sat",
                "headline_fixture": "order_gap_clean",
                "carrier_type": "classical_noncontextual",
                "claim": "Z3.jl agrees on the same clean order-gap exclusion and allowed set.",
            },
        },
        "full_allowed_excluded_matrix": matrix_summary,
        "order_gap_clean_isolation_proof": isolation,
        "reproduce_on_off_evidence": reproduce,
        "scramble_evidence": scramble_evidence,
        "multiplicity_fixture_witness": {
            "fixture": spec["multiplicity_witness_fixture"],
            "python_z3": jax_result["multiplicity_witness"],
            "julia_z3": julia_result["multiplicity_witness"],
            "non_isomorphism_basis": "classical simplex weights and complex density-matrix coordinates are different carrier categories; no hardcoded carrier anchor is used",
        },
        "positive_tests": {
            "multiplicity_fixture": "marginal_multiplicity admits >=2 non-isomorphic carrier types under all solver legs",
            "exclusion_fixture": "order_gap_clean excludes classical_noncontextual while admitting quotient, real_rebit, and complex_rho",
        },
        "negative_tests": {
            "y_phase_exclusion": {
                "excluded_carrier": "real_rebit",
                "by_construction": True,
                "load_bearing": False,
                "role": "boundary_control_only",
                "reason": "real_rebit is real-symmetric and has Y=1/2 identically, so measured Y=3/4 is outside the class by design.",
            },
            "order_gap_clean": {
                "excluded_carrier": "classical_noncontextual",
                "by_construction": False,
                "load_bearing": True,
                "reason": "ZX=1/4 versus XZ=3/8 contradicts the non-disturbing classical joint while single branches remain SAT.",
            },
            "scrambled_order_gap": "allowed set changes to quotient-only",
            "order_gap_exclusion": "Z=1 fixture is retained as over-determined marginal plus order-gap pressure, not the isolated contextuality negative",
            "invalid_probability": "reproduce ON/OFF flips quotient and complex_rho, proving readout binding is load-bearing",
        },
        "by_construction_controls": {
            "y_phase_exclusion": {
                "carrier_type": "real_rebit",
                "by_construction": True,
                "load_bearing": False,
                "fenced_from_load_bearing": True,
                "reason": "A real-symmetric rebit has Tr(rho*Y)=0, represented here as Y=1/2, so Y=3/4 is outside the class by construction.",
            }
        },
        "surviving_alternatives": spec["surviving_alternatives"],
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": "not_scoped",
            "consumer_policy": "Z3.jl SMT carrier-type existence search only; no algebra artifact consumed",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia_result["julia_project"], "packages": julia_result["packages_used"], "role": "semantic_owner"},
            "jax": {"packages": jax_result["packages_used"], "role": "python proof sidecar with z3/cvc5"},
            "pytorch": {"packages": [], "role": "not_scoped"},
            "tensor_exchange": "not_scoped",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": {fixture: matrix[fixture]["julia_z3"]["allowed_set"] for fixture in matrix},
                "jax": {fixture: matrix[fixture]["z3"]["allowed_set"] for fixture in matrix},
            },
            "max_divergence": 0.0 if not failures else 1.0,
            "notes": [
                "Agreement is envelope plumbing after independent local lane runs.",
                "The claim path is per-type SMT existence with readout binding, not cross-engine parity by itself.",
            ],
        },
        "tool_calls": jax_result["tool_calls"] + julia_result["tool_calls"],
        "engine_result_paths": {"jax": str(jax_path), "julia": str(julia_path)},
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
                "full_allowed_excluded_matrix": matrix_summary,
                "order_gap_clean_isolation_proof": isolation,
                "reproduce_on_off_evidence": reproduce,
                "scramble_evidence": scramble_evidence,
                "failures": failures,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if envelope["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
