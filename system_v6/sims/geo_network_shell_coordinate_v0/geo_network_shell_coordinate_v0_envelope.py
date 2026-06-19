#!/usr/bin/env python3
"""Envelope and validator for geo_network_shell_coordinate_v0."""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_network_shell_coordinate_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ENGINE_MODE = "all_three_full_sims"
ENGINES = ["julia", "jax", "pytorch"]
TOL = 1.0e-9
SMT_SCALE = 10**12
SOURCE_WHITELIST = {
    "system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_jax_results.json",
    "system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_jax_results.json",
    "system_v6/sims/stage_lifted_spinor_shell_n5_v0/results/stage_lifted_spinor_shell_n5_v0_jax_results.json",
    "system_v6/sims/stage_lifted_spinor_shell_n6_v0/results/stage_lifted_spinor_shell_n6_v0_jax_results.json",
    "system_v6/sims/stage_lifted_spinor_shell_n7_v0/results/stage_lifted_spinor_shell_n7_v0_jax_results.json",
    "system_v6/sims/stage_lifted_spinor_shell_n8_v0/results/stage_lifted_spinor_shell_n8_v0_jax_results.json",
}
SOURCE_LABELS = ("n3", "n4", "n5", "n6", "n7", "n8")
DEGENERATE_DISCRIMINATOR_LABELS = ("n4", "n5")
EQUAL_DEGREE_BOUNDARY_LABELS = ("n3", "n6", "n7", "n8")
COORDINATE_NAMES = {
    "degree_weighted_shell_centroid_spread_v0",
    "degree_squared_shell_centroid_v0",
    "edge_gradient_shell_energy_v0",
    "unweighted_shell_mean_spread_alt_v0",
}
CONTROL_NAMES = {
    "collapsed_shell",
    "permuted_site_labels",
    "moved_single_site",
    "degenerate_unweighted_conflation",
}
JULIA_ALIGNED_LOAD_BEARING = {
    "CliffordAlgebras",
    "DifferentialEquations",
    "Grassmann",
    "ITensorMPS",
    "ITensorNetworks",
    "ITensors",
    "Manifolds",
    "QuantumClifford",
    "QuantumOptics",
    "TensorKit",
    "Z3",
}
JULIA_LOAD_BEARING_ROW_NAMES = {"frechet_karcher_shell_mean_degree_weighted_v0"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_leg(engine: str) -> dict[str, Any]:
    return load_json(RESULT_DIR / f"{SIM_ID}_{engine}_results.json")


def engine_record(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": payload["result_path"],
        "role_id": payload["role_id"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload["tool_calls"],
        "capability_receipts": payload["capability_receipts"],
        "claim_path_tools": payload["claim_path_tools"],
    }


def source_hash_fresh(payload: dict[str, Any]) -> bool:
    source_path = ROOT / payload["source_path"]
    return source_path.exists() and sha256_file(source_path) == payload["source_sha256"]


def input_sources_ok(legs: dict[str, dict[str, Any]]) -> bool:
    for payload in legs.values():
        paths = {entry["path"] for entry in payload["input_source_results"].values()}
        if paths != SOURCE_WHITELIST:
            return False
        for entry in payload["input_source_results"].values():
            source_path = ROOT / entry["path"]
            if not source_path.exists() or sha256_file(source_path) != entry["sha256"]:
                return False
    return True


def controls_ok(payload: dict[str, Any]) -> bool:
    for row in payload["rows"].values():
        if set(row["network_shell_coordinates"]) != COORDINATE_NAMES:
            return False
        if set(row["controls"]) != CONTROL_NAMES:
            return False
        if not all(control.get("fired") is True for control in row["controls"].values()):
            return False
    return True


def julia_aligned_load_bearing_ok(payload: dict[str, Any]) -> bool:
    if payload.get("engine") != "julia":
        return True
    aligned = set(payload.get("aligned_packages_load_bearing", []))
    return bool(aligned & JULIA_ALIGNED_LOAD_BEARING) and {"Manifolds", "Z3"}.issubset(aligned)


def julia_manifolds_rows_ok(payload: dict[str, Any]) -> bool:
    if payload.get("engine") != "julia":
        return True
    for source_label, row in payload["rows"].items():
        load_rows = row.get("julia_load_bearing_rows", {})
        if set(load_rows) != JULIA_LOAD_BEARING_ROW_NAMES:
            return False
        frechet = load_rows["frechet_karcher_shell_mean_degree_weighted_v0"]
        if frechet.get("fired") is not True:
            return False
        if frechet.get("api") != "Manifolds.mean(Manifolds.Sphere(2), pts, support_graph_degree_weights)":
            return False
        if frechet.get("torus_api") != "Manifolds.mean(Manifolds.Torus(2), pts, support_graph_degree_weights)":
            return False
        if source_label in DEGENERATE_DISCRIMINATOR_LABELS:
            if abs(float(frechet["abs_divergence"])) <= 1.0e-6:
                return False
    return True


def julia_z3_smt_ok(payload: dict[str, Any], source_label: str = "n4") -> bool:
    if payload.get("engine") != "julia":
        return True
    row = payload["rows"][source_label]["controls"]["degenerate_unweighted_conflation"]
    smt = row.get("z3_smt_row", {})
    return (
        smt.get("fired") is True
        and smt.get("api") == "Z3.Solver / Z3.IntVar / Z3.IntVal / Z3.check"
        and smt.get("raw_values_bound") is True
        and smt.get("raw_weights_bound") is True
        and smt.get("unweighted_equality_status") == "sat"
        and smt.get("weighted_equality_status") == "unsat"
        and smt.get("erased_weights_equality_status") == "sat"
        and smt.get("permuted_control_weighted_equality_status") == "unsat"
        and abs(float(smt.get("weighted_delta_abs", 0.0))) > 1.0e-6
    )


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def scaled_int(value: float) -> int:
    return round(float(value) * SMT_SCALE)


def cvc5_equality_status(kind: str, z_values: list[float], swapped: list[float], weights: list[int]) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()

    def intval(value: int) -> Any:
        return solver.mkInteger(str(value))

    def sum_terms(terms: list[Any]) -> Any:
        if len(terms) == 1:
            return terms[0]
        return solver.mkTerm(Kind.ADD, *terms)

    def weighted_sum(prefix: str, values: list[float], use_weights: bool) -> Any:
        terms = []
        for idx, value in enumerate(values):
            z_var = solver.mkConst(int_sort, f"{prefix}_z_{idx}")
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, z_var, intval(scaled_int(value))))
            if use_weights:
                w_var = solver.mkConst(int_sort, f"{prefix}_w_{idx}")
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, w_var, intval(int(weights[idx]))))
                terms.append(solver.mkTerm(Kind.MULT, w_var, z_var))
            else:
                terms.append(z_var)
        return sum_terms(terms)

    left = weighted_sum("orig", z_values, kind == "weighted")
    right = weighted_sum("swap", swapped, kind == "weighted")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, left, right))
    return cvc5_status(solver.checkSat())


def crossover_proofs_for_source(julia_payload: dict[str, Any], source_label: str) -> dict[str, Any]:
    row = julia_payload["rows"][source_label]
    smt = row["controls"]["degenerate_unweighted_conflation"]["z3_smt_row"]
    z_values = [float(value) for value in row["z_values"]]
    swapped = list(z_values)
    swapped[1], swapped[2] = swapped[2], swapped[1]
    weights = [int(round(value)) for value in row["degrees"]]
    erased_weights = [1 for _ in weights]
    perm = list(reversed(range(len(z_values))))
    permuted_z = [z_values[idx] for idx in perm]
    permuted_swapped = [swapped[idx] for idx in perm]
    permuted_weights = [weights[idx] for idx in perm]
    cvc5_proof = {
        "ran": True,
        "load_bearing": True,
        "verdict": cvc5_equality_status("weighted", z_values, swapped, weights),
        "claim": f"weighted equality between original and swapped {source_label} shell coordinates is UNSAT from bound scaled z values and degree weights",
        "source_label": source_label,
        "unweighted_equality_status": cvc5_equality_status("unweighted", z_values, swapped, weights),
        "weighted_equality_status": cvc5_equality_status("weighted", z_values, swapped, weights),
        "erased_weights_equality_status": cvc5_equality_status("weighted", z_values, swapped, erased_weights),
        "permuted_control_weighted_equality_status": cvc5_equality_status("weighted", permuted_z, permuted_swapped, permuted_weights),
        "raw_values_bound": True,
        "raw_weights_bound": True,
        "scaled_integer_precision": SMT_SCALE,
    }
    z3_proof = {
        "ran": True,
        "load_bearing": True,
        "verdict": smt["weighted_equality_status"],
        "claim": f"Julia Z3 weighted equality between original and swapped {source_label} shell coordinates is UNSAT from bound scaled z values and degree weights",
        "source_label": source_label,
        **smt,
    }
    return {"z3": z3_proof, "cvc5": cvc5_proof, "julia_z3": z3_proof}


def crossover_proofs_from_julia(julia_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {source_label: crossover_proofs_for_source(julia_payload, source_label) for source_label in DEGENERATE_DISCRIMINATOR_LABELS}


def compare_rows(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    max_diff = 0.0
    for source_label in SOURCE_LABELS:
        for coord in sorted(COORDINATE_NAMES):
            for key in ("z_bar", "sigma_z", "edge_mean_delta_z_squared"):
                values = {}
                for engine, payload in legs.items():
                    value = payload["rows"][source_label]["network_shell_coordinates"][coord].get(key)
                    if value is not None:
                        values[engine] = float(value)
                if values:
                    diff = max(values.values()) - min(values.values())
                    max_diff = max(max_diff, abs(diff))
                    rows.append({"source": source_label, "coordinate": coord, "key": key, "values": values, "max_abs_diff": abs(diff)})
    return {"rows": rows, "max_abs_diff": max_diff, "within_tolerance": max_diff <= TOL}


def build_result() -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ENGINES}
    comparison = compare_rows(legs)
    crossover_by_source = crossover_proofs_from_julia(legs["julia"])
    primary_crossover = crossover_by_source["n4"]
    gate_pass = {
        "legs_all_pass": all(payload["all_pass"] is True for payload in legs.values()),
        "engine_mode_requires_pytorch": ENGINE_MODE == "all_three_full_sims" and "pytorch" in legs,
        "source_hashes_fresh": all(source_hash_fresh(payload) for payload in legs.values()),
        "input_sources_whitelisted_and_hash_fresh": input_sources_ok(legs),
        "ceiling_exact": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in legs.values()
        ),
        "no_peer_result_reads": all(payload["reads_peer_result"] is False for payload in legs.values()),
        "controls_fire": all(controls_ok(payload) for payload in legs.values()),
        "cross_engine_coordinate_agreement": comparison["within_tolerance"],
        "tool_calls_one_to_one": all(len(payload["tool_calls"]) == len(payload["claim_path_tools"]) for payload in legs.values()),
        "capability_receipts_present": all(payload["capability_receipts"] for payload in legs.values()),
        "julia_aligned_load_bearing_package": julia_aligned_load_bearing_ok(legs["julia"]),
        "julia_manifolds_rows_gate": julia_manifolds_rows_ok(legs["julia"]),
        "julia_z3_smt_gate": all(julia_z3_smt_ok(legs["julia"], source_label) for source_label in DEGENERATE_DISCRIMINATOR_LABELS),
        "crossover_proofs_agree": all(
            proof["z3"]["verdict"] == proof["cvc5"]["verdict"] == "unsat"
            for proof in crossover_by_source.values()
        ),
        "audit_verdict_present_for_builder_extension": (SIM_DIR / "audit_verdict.md").exists(),
    }
    all_pass = all(gate_pass.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "claim": "G4 scratch diagnostic: committed n3/n4/n5/n6/n7/n8 lifted-shell per-site z=cos(2 eta) rows induce separately named static network-level shell coordinates with fail-capable controls.",
        "allowed_claims": [
            "degree-weighted centroid/spread, degree-squared centroid, edge-gradient energy, and unweighted alternative were computed from committed n3/n4/n5/n6/n7/n8 per-site z rows",
            "collapsed shell, site-label permutation, moved-site, and degenerate-unweighted controls fired in full reruns",
            "the n4/n5 unequal-degree rows discriminate the degree-weighted coordinate from the unweighted alternative; n3/n6/n7/n8 are equal-degree boundary rows",
        ],
        "disallowed_claims": ["canonical network coordinate", "formal admission", "promotion beyond scratch", "trend claim", "scaling claim", "geo bracketing result"],
        "engine_contract": {
            "mode": ENGINE_MODE,
            "lanes": ENGINES,
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
            "reads_peer_result": False,
            "torch_role": "real graph-network role: torch_geometric.utils.degree independently computes support graph degree weights",
        },
        "build_flags": {
            "require_pytorch": True,
            "allow_two_engine_mode": False,
            "require_read_only_sources": sorted(SOURCE_WHITELIST),
            "write_audit_verdict": False,
        },
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "engines": {engine: engine_record(payload) for engine, payload in legs.items()},
        "input_source_results": legs["jax"]["input_source_results"],
        "network_coordinate_rows": {label: legs["jax"]["rows"][label] for label in SOURCE_LABELS},
        "julia_load_bearing_rows": {
            label: legs["julia"]["rows"][label]["julia_load_bearing_rows"]
            for label in SOURCE_LABELS
        },
        "julia_z3_smt_row": legs["julia"]["rows"]["n4"]["controls"]["degenerate_unweighted_conflation"]["z3_smt_row"],
        "julia_z3_smt_rows": {
            label: legs["julia"]["rows"][label]["controls"]["degenerate_unweighted_conflation"]["z3_smt_row"]
            for label in DEGENERATE_DISCRIMINATOR_LABELS
        },
        "claim_path_tools": ["Manifolds", "Z3", "jraph", "torch_geometric", "cvc5"],
        "crossover_proofs": primary_crossover,
        "crossover_proofs_by_source": crossover_by_source,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                engine: legs[engine]["rows"]["n4"]["network_shell_coordinates"]["degree_weighted_shell_centroid_spread_v0"]["z_bar"]
                for engine in ENGINES
            },
            "coordinate": "n4.degree_weighted_shell_centroid_spread_v0.z_bar",
            "max_divergence": comparison["max_abs_diff"],
            "within_tolerance": comparison["within_tolerance"],
        },
        "controller_comparison": comparison,
        "gate_pass": gate_pass,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(payload["schema_version"] == "three_engine_sim_result_v1", "bad schema")
    require(payload["all_pass"] is True, "envelope all_pass is not true")
    require(payload["classification"] == CLASSIFICATION, "classification drift")
    require(payload["promotion_allowed"] is False, "promotion_allowed drift")
    require(payload["formal_admission_allowed"] is False, "formal_admission_allowed drift")
    require(payload["engine_contract"]["mode"] == ENGINE_MODE, "engine mode drift")
    require(payload["build_flags"]["require_pytorch"] is True, "validator flag require_pytorch drift")
    require(set(payload["engines"]) == set(ENGINES), "engine set drift")
    require(set(payload["network_coordinate_rows"]) == set(SOURCE_LABELS), "source label set drift")
    require(set(payload["input_source_results"]) == set(SOURCE_LABELS), "input source label set drift")
    require(all(gate is True for gate in payload["gate_pass"].values()), "failed gate present")
    require(payload["controller_comparison"]["within_tolerance"] is True, "cross-engine comparison failed")
    for engine, record in payload["engines"].items():
        source = ROOT / record["source_path"]
        require(source.exists(), f"{engine} source missing")
        require(sha256_file(source) == record["source_sha256"], f"{engine} source hash mismatch")
        require(record["reads_peer_result"] is False, f"{engine} reads peer result")
        require(record["capability_receipts"], f"{engine} capability receipts missing")
        require(len(record["tool_calls"]) == len(record["claim_path_tools"]), f"{engine} tool call count mismatch")
    require(
        bool(set(payload["engines"]["julia"]["aligned_packages_load_bearing"]) & JULIA_ALIGNED_LOAD_BEARING),
        "julia must have at least one aligned load-bearing package",
    )
    require({"Manifolds", "Z3"}.issubset(set(payload["engines"]["julia"]["aligned_packages_load_bearing"])), "julia Manifolds/Z3 load-bearing packages missing")
    require(payload["gate_pass"].get("julia_manifolds_rows_gate") is True, "julia Manifolds row gate failed")
    require(payload["gate_pass"].get("julia_z3_smt_gate") is True, "julia Z3 SMT gate failed")
    for source_label, row in payload["network_coordinate_rows"].items():
        require(set(row["network_shell_coordinates"]) == COORDINATE_NAMES, f"{source_label} coordinate names drift")
        require(set(row["controls"]) == CONTROL_NAMES, f"{source_label} control names drift")
        require(row["controls"]["collapsed_shell"]["fired"] is True, f"{source_label} collapsed shell control did not fire")
        require(row["controls"]["permuted_site_labels"]["fired"] is True, f"{source_label} label permutation control did not fire")
        require(row["controls"]["moved_single_site"]["fired"] is True, f"{source_label} moved-site control did not fire")
        require(row["controls"]["degenerate_unweighted_conflation"]["fired"] is True, f"{source_label} degenerate alternative control did not fire")
    for source_label in DEGENERATE_DISCRIMINATOR_LABELS:
        require(
            payload["network_coordinate_rows"][source_label]["controls"]["degenerate_unweighted_conflation"].get("degenerate_witness_applicable") is True,
            f"{source_label} unequal-degree degenerate alternative discriminator not applicable",
        )
        smt = payload["julia_z3_smt_rows"][source_label]
        require(smt["unweighted_equality_status"] == "sat", f"{source_label} Julia Z3 unweighted equality did not SAT")
        require(smt["weighted_equality_status"] == "unsat", f"{source_label} Julia Z3 weighted equality did not UNSAT")
        require(smt["erased_weights_equality_status"] == "sat", f"{source_label} Julia Z3 erased-weight control did not flip to SAT")
        require(smt["permuted_control_weighted_equality_status"] == "unsat", f"{source_label} Julia Z3 permuted weighted control did not UNSAT")
        require(float(smt["weighted_delta_abs"]) > 1.0e-6, f"{source_label} weighted separation delta missing")
    for source_label in EQUAL_DEGREE_BOUNDARY_LABELS:
        control = payload["network_coordinate_rows"][source_label]["controls"]["degenerate_unweighted_conflation"]
        require(control.get("degenerate_witness_applicable") is False, f"{source_label} equal-degree boundary row drift")
        require("all support-graph degrees are equal" in control.get("reason", ""), f"{source_label} equal-degree boundary reason missing")
    require(abs(float(payload["julia_load_bearing_rows"]["n4"]["frechet_karcher_shell_mean_degree_weighted_v0"]["chart_space_weighted_z_bar"]) - 0.05) <= TOL, "n4 chart weighted z_bar drift")
    require(float(payload["julia_load_bearing_rows"]["n4"]["frechet_karcher_shell_mean_degree_weighted_v0"]["abs_divergence"]) > 1.0e-6, "n4 Manifolds Frechet/chart divergence missing")
    require(float(payload["julia_load_bearing_rows"]["n5"]["frechet_karcher_shell_mean_degree_weighted_v0"]["abs_divergence"]) > 1.0e-6, "n5 Manifolds Frechet/chart divergence missing")
    for source_label in DEGENERATE_DISCRIMINATOR_LABELS:
        proof = payload["crossover_proofs_by_source"][source_label]
        require(proof["z3"]["verdict"] == proof["cvc5"]["verdict"] == "unsat", f"{source_label} crossover proofs do not agree on UNSAT")
    require(payload["divergence"]["julia_authoritative"] is True, "divergence julia_authoritative drift")
    require(payload["divergence"]["within_tolerance"] is True, "divergence outside tolerance")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        payload = load_json(RESULT_PATH)
    else:
        RESULT_DIR.mkdir(parents=True, exist_ok=True)
        payload = build_result()
        RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    errors = validate_payload(payload)
    print(
        json.dumps(
            {
                "ok": not errors,
                "errors": errors,
                "result_json": str(RESULT_PATH.relative_to(ROOT)),
                "declared_mode": ENGINE_MODE,
                "flags": payload.get("build_flags", {}),
            },
            indent=2,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
