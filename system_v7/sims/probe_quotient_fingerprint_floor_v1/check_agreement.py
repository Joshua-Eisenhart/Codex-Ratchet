#!/usr/bin/env python3
"""All-three envelope for probe_quotient_fingerprint_floor_v1."""

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

SIM_ID = "probe_quotient_fingerprint_floor_v1"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
PARITY_TOLERANCE = 1e-10


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def norm_classes(classes: list[list[str]]) -> list[list[str]]:
    return sorted([sorted(group) for group in classes])


def equality_matrix_from_fingerprints(labels: list[str], fingerprints: dict[str, list[int]]) -> list[list[bool]]:
    return [[fingerprints[left] == fingerprints[right] for right in labels] for left in labels]


def matrix_mismatch_count(left: list[list[bool]], right: list[list[bool]]) -> int:
    return sum(1 for row_l, row_r in zip(left, right, strict=True) for a, b in zip(row_l, row_r, strict=True) if a != b)


def engine_record(result: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": result["source_path"],
        "source_sha256": result["source_sha256"],
        "result_path": str(result_path),
        "result_sha256": sha256_of(result_path),
        "packages_used": result["packages_used"],
        "aligned_packages_load_bearing": result["aligned_packages_load_bearing"],
        "package_observables": result["package_observables"],
        "reads_peer_result": False,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }


def main() -> int:
    spec = load_json(HERE / "spec.json")
    result_paths = {
        "jax": RESULTS / f"{SIM_ID}_jax_results.json",
        "julia": RESULTS / f"{SIM_ID}_julia_results.json",
        "pytorch": RESULTS / f"{SIM_ID}_pytorch_results.json",
    }
    results = {name: load_json(path) for name, path in result_paths.items()}
    jax_result = results["jax"]
    julia_result = results["julia"]
    pytorch_result = results["pytorch"]
    failures: list[str] = []

    for name, row in results.items():
        if row.get("reads_peer_result") is not False:
            failures.append(f"{name}: reads_peer_result is not false")
        if row.get("classification") != "scratch_diagnostic":
            failures.append(f"{name}: classification is not scratch_diagnostic")
        if row.get("promotion_allowed") is not False:
            failures.append(f"{name}: promotion_allowed is not false")
        if row.get("formal_admission_allowed") is not False:
            failures.append(f"{name}: formal_admission_allowed is not false")
        if row.get("all_pass") is not True:
            failures.append(f"{name}: all_pass is not true")

    for name, row in (("jax", jax_result), ("pytorch", pytorch_result)):
        if norm_classes(row["quotient_classes_full"]) != norm_classes(julia_result["quotient_classes_full"]):
            failures.append(f"{name}: full quotient classes disagree with Julia")
        if norm_classes(row["quotient_classes_erased"]) != norm_classes(julia_result["quotient_classes_erased"]):
            failures.append(f"{name}: erased quotient classes disagree with Julia")

    full_counts = {name: int(row["quotient_class_count_full"]) for name, row in results.items()}
    erased_counts = {name: int(row["quotient_class_count_erased"]) for name, row in results.items()}
    expected_full = int(spec["expected"]["full_class_count"])
    expected_erased = int(spec["expected"]["erased_class_count"])
    if any(count != expected_full for count in full_counts.values()):
        failures.append("full class count does not match expected fixture for every engine")
    if any(count != expected_erased for count in erased_counts.values()):
        failures.append("erased class count does not match expected fixture for every engine")

    jax_smt = jax_result["smt_flip"]
    julia_smt = julia_result["smt_flip"]
    pytorch_smt = pytorch_result["smt_flip"]
    if not (
        jax_smt["z3_full_P"] == "unsat"
        and jax_smt["z3_erased_P"] == "sat"
        and jax_smt["cvc5_full_P"] == "unsat"
        and jax_smt["cvc5_erased_P"] == "sat"
    ):
        failures.append("JAX SMT flip did not match UNSAT/SAT requirement")
    if not (julia_smt["julia_z3_full_P"] == "unsat" and julia_smt["julia_z3_erased_P"] == "sat"):
        failures.append("Julia Z3.jl flip did not match UNSAT/SAT requirement")
    if not (
        pytorch_smt["z3_full_P"] == "unsat"
        and pytorch_smt["z3_erased_P"] == "sat"
        and pytorch_smt["cvc5_full_P"] == "unsat"
        and pytorch_smt["cvc5_erased_P"] == "sat"
    ):
        failures.append("PyTorch SMT flip did not match UNSAT/SAT requirement")

    tautology_guard_tripped = not (
        jax_smt["z3_erased_P"] == "sat"
        and jax_smt["cvc5_erased_P"] == "sat"
        and julia_smt["julia_z3_erased_P"] == "sat"
        and pytorch_smt["z3_erased_P"] == "sat"
        and pytorch_smt["cvc5_erased_P"] == "sat"
    )
    if tautology_guard_tripped:
        failures.append("tautology guard tripped")

    merge_pair = jax_result["flip_control"]["erased_merge_pair"]
    if merge_pair != spec["expected"]["merge_pair_when_erased"]:
        failures.append("erased merge pair does not match expected fixture")
    if pytorch_result["flip_control"]["erased_merge_pair"] != spec["expected"]["merge_pair_when_erased"]:
        failures.append("pytorch erased merge pair does not match expected fixture")

    labels = list(spec["support"])
    julia_full_matrix = equality_matrix_from_fingerprints(labels, julia_result["fingerprints_full"])
    julia_erased_matrix = equality_matrix_from_fingerprints(labels, julia_result["fingerprints_erased"])
    full_matrix_mismatches = {
        name: matrix_mismatch_count(julia_full_matrix, equality_matrix_from_fingerprints(labels, row["fingerprints_full"]))
        for name, row in results.items()
    }
    erased_matrix_mismatches = {
        name: matrix_mismatch_count(julia_erased_matrix, equality_matrix_from_fingerprints(labels, row["fingerprints_erased"]))
        for name, row in results.items()
    }
    parity_by_engine = {
        name: {
            "full_class_count": full_counts[name],
            "erased_class_count": erased_counts[name],
            "full_delta_vs_julia": float(abs(full_counts[name] - full_counts["julia"])),
            "erased_delta_vs_julia": float(abs(erased_counts[name] - erased_counts["julia"])),
            "full_equality_matrix_mismatches_vs_julia": full_matrix_mismatches[name],
            "erased_equality_matrix_mismatches_vs_julia": erased_matrix_mismatches[name],
        }
        for name in ("julia", "jax", "pytorch")
    }
    parity_max = float(
        max(
            [
                parity_by_engine[name]["full_delta_vs_julia"]
                for name in parity_by_engine
            ]
            + [
                parity_by_engine[name]["erased_delta_vs_julia"]
                for name in parity_by_engine
            ]
            + [float(value) for value in full_matrix_mismatches.values()]
            + [float(value) for value in erased_matrix_mismatches.values()]
        )
    )
    if parity_max > PARITY_TOLERANCE:
        failures.append(f"engine parity max {parity_max} exceeds tolerance {PARITY_TOLERANCE}")

    build_status = "PASS" if not failures else "BUILD FAILED"
    engines = {
        "julia": engine_record(julia_result, result_paths["julia"])
        | {"julia_project": julia_result["julia_project"]},
        "jax": engine_record(jax_result, result_paths["jax"]),
        "pytorch": engine_record(pytorch_result, result_paths["pytorch"]),
    }
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
        "mode": "all_three_full_sims",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": not failures,
        "build_status": build_status,
        "claim_ceiling": spec["claim_ceiling"],
        "claim": "Finite opaque support X with explicit finite probe table P admits the forced quotient Q=X/~P. The solver polarity is load-bearing for the full/erased consistency gate, not structural-discovery evidence.",
        "claim_path_tools": ["jax", "jax.numpy", "torch", "torch.func", "z3", "cvc5", "Z3"],
        "control_only_tools": [],
        "TOOL_MANIFEST": {
            "jax": jax_result["TOOL_MANIFEST"]["jax"],
            "torch": pytorch_result["TOOL_MANIFEST"]["torch"],
            "torch.func": pytorch_result["TOOL_MANIFEST"]["torch.func"],
            "z3": jax_result["TOOL_MANIFEST"]["z3"],
            "cvc5": jax_result["TOOL_MANIFEST"]["cvc5"],
            "Z3": julia_result["TOOL_MANIFEST"]["Z3"],
            "json": TOOL_MANIFEST["json"],
            "pathlib": TOOL_MANIFEST["pathlib"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "load_bearing",
            "torch": "load_bearing",
            "torch.func": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "Z3": "load_bearing",
            "json": "supportive",
            "pathlib": "supportive",
        },
        "engines": engines,
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "supportive": False,
                "verdict": jax_smt["z3_full_P"],
                "full_P_verdict": jax_smt["z3_full_P"],
                "erased_P_verdict": jax_smt["z3_erased_P"],
                "claim": "load-bearing consistency gate: full P has no soundness/coarseness violation and erased P exposes the expected over-refinement relative to the forced full Q",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "supportive": False,
                "verdict": jax_smt["cvc5_full_P"],
                "full_P_verdict": jax_smt["cvc5_full_P"],
                "erased_P_verdict": jax_smt["cvc5_erased_P"],
                "claim": "load-bearing consistency gate: independent SMT route agrees with z3 on full and erased probe lists",
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "supportive": False,
                "verdict": julia_smt["julia_z3_full_P"],
                "full_P_verdict": julia_smt["julia_z3_full_P"],
                "erased_P_verdict": julia_smt["julia_z3_erased_P"],
                "claim": "load-bearing consistency gate: Z3.jl route agrees on the full/erased polarity",
            },
            "pytorch_z3": {
                "ran": True,
                "load_bearing": True,
                "supportive": False,
                "verdict": pytorch_smt["z3_full_P"],
                "full_P_verdict": pytorch_smt["z3_full_P"],
                "erased_P_verdict": pytorch_smt["z3_erased_P"],
                "claim": "load-bearing consistency gate over torch-derived rows",
            },
            "pytorch_cvc5": {
                "ran": True,
                "load_bearing": True,
                "supportive": False,
                "verdict": pytorch_smt["cvc5_full_P"],
                "full_P_verdict": pytorch_smt["cvc5_full_P"],
                "erased_P_verdict": pytorch_smt["cvc5_erased_P"],
                "claim": "load-bearing independent consistency gate over torch-derived rows",
            },
        },
        "quotient": {
            "support": spec["support"],
            "probe_order_full": spec["probe_order_full"],
            "probe_order_erased": spec["probe_order_erased"],
            "full_classes": julia_result["quotient_classes_full"],
            "erased_classes": julia_result["quotient_classes_erased"],
            "full_class_count": full_counts["julia"],
            "erased_class_count": erased_counts["julia"],
        },
        "flip_control": {
            "erased_merge_pair": merge_pair,
            "new_class_count_after_erasure": erased_counts["julia"],
            "added_probe": spec["added_probe"],
            "split_pair_after_addition": merge_pair,
            "new_class_count_after_addition": full_counts["julia"],
            "tautology_guard_tripped": tautology_guard_tripped,
        },
        "positive_tests": {
            "full_P_structural_claim": "UNSAT under z3, cvc5, PyTorch z3/cvc5, and Julia Z3.jl",
            "class_count_matches_fixture": all(count == expected_full for count in full_counts.values()),
        },
        "negative_tests": {
            "erased_P_control": "SAT under z3, cvc5, PyTorch z3/cvc5, and Julia Z3.jl",
            "merge_pair": merge_pair,
        },
        "boundary_tests": {
            "persistent_indistinguishable_pair_under_full_P": jax_result["boundary_tests"][
                "persistent_indistinguishable_pair_under_full_P"
            ],
            "counting_cardinality_not_claimed_forced": True,
        },
        "parity": {
            "tolerance": PARITY_TOLERANCE,
            "per_engine": parity_by_engine,
            "max": parity_max,
        },
        "surviving_alternatives": spec["surviving_alternatives"],
        "banned_verb_scan_scope": "result narrative strings reviewed for prohibited promotion verbs",
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": "not_scoped",
            "consumer_policy": "finite table rows only; no canonical carrier artifact consumed",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia_result["julia_project"], "packages": julia_result["packages_used"], "role": "semantic_owner"},
            "jax": {"packages": jax_result["packages_used"], "role": "batched_finite_table_worker"},
            "pytorch": {"packages": pytorch_result["packages_used"], "role": "complex128_graph_autograd_worker"},
            "tensor_exchange": "not_scoped",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": full_counts,
            "erased_engine_values": erased_counts,
            "per_engine_parity": parity_by_engine,
            "max_divergence": parity_max,
            "notes": [
                "Agreement is envelope plumbing after independent local lane runs.",
                "The claim path is the finite table quotient. The SMT flip is load-bearing for the full/erased consistency gate, not structural-discovery evidence.",
            ],
        },
        "tool_calls": jax_result["tool_calls"] + julia_result["tool_calls"] + pytorch_result["tool_calls"],
        "engine_result_paths": {name: str(path) for name, path in result_paths.items()},
        "failures": failures,
    }
    out_path = RESULTS / f"{SIM_ID}_three_engine_results.json"
    out_path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": not failures, "result_path": str(out_path), "build_status": build_status, "failures": failures, "parity_max": parity_max}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
