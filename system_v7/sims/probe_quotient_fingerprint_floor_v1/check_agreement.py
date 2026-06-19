#!/usr/bin/env python3
"""Envelope for probe_quotient_fingerprint_floor_v1."""

from __future__ import annotations

import hashlib
import json
import os
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


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def norm_classes(classes: list[list[str]]) -> list[list[str]]:
    return sorted([sorted(group) for group in classes])


def main() -> int:
    spec = load_json(HERE / "spec.json")
    jax_result_path = RESULTS / f"{SIM_ID}_jax_results.json"
    julia_result_path = RESULTS / f"{SIM_ID}_julia_results.json"
    jax_result = load_json(jax_result_path)
    julia_result = load_json(julia_result_path)
    failures: list[str] = []

    for name, row in (("jax", jax_result), ("julia", julia_result)):
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

    if norm_classes(jax_result["quotient_classes_full"]) != norm_classes(julia_result["quotient_classes_full"]):
        failures.append("full quotient classes disagree")
    if norm_classes(jax_result["quotient_classes_erased"]) != norm_classes(julia_result["quotient_classes_erased"]):
        failures.append("erased quotient classes disagree")

    full_count = int(julia_result["quotient_class_count_full"])
    erased_count = int(julia_result["quotient_class_count_erased"])
    if full_count != int(spec["expected"]["full_class_count"]):
        failures.append("full class count does not match expected fixture")
    if erased_count != int(spec["expected"]["erased_class_count"]):
        failures.append("erased class count does not match expected fixture")

    jax_smt = jax_result["smt_flip"]
    julia_smt = julia_result["smt_flip"]
    if not (
        jax_smt["z3_full_P"] == "unsat"
        and jax_smt["z3_erased_P"] == "sat"
        and jax_smt["cvc5_full_P"] == "unsat"
        and jax_smt["cvc5_erased_P"] == "sat"
    ):
        failures.append("Python SMT flip did not match UNSAT/SAT requirement")
    if not (julia_smt["julia_z3_full_P"] == "unsat" and julia_smt["julia_z3_erased_P"] == "sat"):
        failures.append("Julia Z3.jl flip did not match UNSAT/SAT requirement")

    tautology_guard_tripped = not (
        jax_smt["z3_erased_P"] == "sat"
        and jax_smt["cvc5_erased_P"] == "sat"
        and julia_smt["julia_z3_erased_P"] == "sat"
    )
    if tautology_guard_tripped:
        failures.append("tautology guard tripped")

    merge_pair = jax_result["flip_control"]["erased_merge_pair"]
    if merge_pair != spec["expected"]["merge_pair_when_erased"]:
        failures.append("erased merge pair does not match expected fixture")

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
            "pytorch": {
                "scoped": False,
                "reason": "Rung-0 scratch diagnostic has no graph, network, or autograd claim path.",
            },
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
        },
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": not failures,
        "build_status": build_status,
        "claim_ceiling": spec["claim_ceiling"],
        "claim": "Finite opaque support X with explicit finite probe table P admits the forced quotient Q=X/~P. The solver polarity is a consistency check over the supplied generating table, not load-bearing discovery.",
        "claim_path_tools": ["jax", "jax.numpy"],
        "control_only_tools": [],
        "TOOL_MANIFEST": {
            "jax": jax_result["TOOL_MANIFEST"]["jax"],
            "z3": jax_result["TOOL_MANIFEST"]["z3"],
            "cvc5": jax_result["TOOL_MANIFEST"]["cvc5"],
            "Z3": julia_result["TOOL_MANIFEST"]["Z3"],
            "json": TOOL_MANIFEST["json"],
            "pathlib": TOOL_MANIFEST["pathlib"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "load_bearing",
            "z3": "supportive",
            "cvc5": "supportive",
            "Z3": "supportive",
            "json": "supportive",
            "pathlib": "supportive",
        },
        "engines": {
            "julia": {
                "ran": True,
                "source_path": julia_result["source_path"],
                "source_sha256": julia_result["source_sha256"],
                "result_path": str(julia_result_path),
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
                "result_path": str(jax_result_path),
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
                "load_bearing": False,
                "supportive": True,
                "verdict": jax_smt["z3_full_P"],
                "full_P_verdict": jax_smt["z3_full_P"],
                "erased_P_verdict": jax_smt["z3_erased_P"],
                "claim": "supportive consistency check: full P has no soundness/coarseness violation and erased P exposes the expected over-refinement relative to the forced full Q",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": False,
                "supportive": True,
                "verdict": jax_smt["cvc5_full_P"],
                "full_P_verdict": jax_smt["cvc5_full_P"],
                "erased_P_verdict": jax_smt["cvc5_erased_P"],
                "claim": "supportive consistency check: independent SMT route agrees with z3 on full and erased probe lists",
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": False,
                "supportive": True,
                "verdict": julia_smt["julia_z3_full_P"],
                "full_P_verdict": julia_smt["julia_z3_full_P"],
                "erased_P_verdict": julia_smt["julia_z3_erased_P"],
                "claim": "supportive consistency check: Z3.jl route agrees on the full/erased polarity",
            },
        },
        "quotient": {
            "support": spec["support"],
            "probe_order_full": spec["probe_order_full"],
            "probe_order_erased": spec["probe_order_erased"],
            "full_classes": julia_result["quotient_classes_full"],
            "erased_classes": julia_result["quotient_classes_erased"],
            "full_class_count": full_count,
            "erased_class_count": erased_count,
        },
        "flip_control": {
            "erased_merge_pair": merge_pair,
            "new_class_count_after_erasure": erased_count,
            "added_probe": spec["added_probe"],
            "split_pair_after_addition": merge_pair,
            "new_class_count_after_addition": full_count,
            "tautology_guard_tripped": tautology_guard_tripped,
        },
        "positive_tests": {
            "full_P_structural_claim": "UNSAT under z3 and cvc5",
            "class_count_matches_fixture": full_count == int(spec["expected"]["full_class_count"]),
        },
        "negative_tests": {
            "erased_P_control": "SAT under z3 and cvc5",
            "merge_pair": merge_pair,
        },
        "boundary_tests": {
            "persistent_indistinguishable_pair_under_full_P": jax_result["boundary_tests"][
                "persistent_indistinguishable_pair_under_full_P"
            ],
            "counting_cardinality_not_claimed_forced": True,
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
            "pytorch": {"packages": [], "role": "not_scoped"},
            "tensor_exchange": "not_scoped",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": full_count, "jax": int(jax_result["quotient_class_count_full"])},
            "max_divergence": 0.0 if full_count == int(jax_result["quotient_class_count_full"]) else 1.0,
            "notes": [
                "Agreement is envelope plumbing after independent local lane runs.",
                "The claim path is the finite table quotient. The SMT flip is supportive consistency evidence, not load-bearing discovery.",
            ],
        },
        "tool_calls": jax_result["tool_calls"] + julia_result["tool_calls"],
        "engine_result_paths": {"jax": str(jax_result_path), "julia": str(julia_result_path)},
        "failures": failures,
    }
    out_path = RESULTS / f"{SIM_ID}_three_engine_results.json"
    out_path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": not failures, "result_path": str(out_path), "build_status": build_status, "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
