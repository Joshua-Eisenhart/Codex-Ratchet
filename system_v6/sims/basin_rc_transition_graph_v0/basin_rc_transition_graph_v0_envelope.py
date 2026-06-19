#!/usr/bin/env python3
"""Envelope builder for basin_rc_transition_graph_v0."""

from __future__ import annotations

import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

from basin_rc_transition_graph_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SIM_ID,
    now_z,
    rel,
    sha256_file,
    stable_sha256,
    write_json,
)


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
LEG_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
}

TOOL_MANIFEST = {
    "build_three_engine_envelope.py": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical envelope assembly helper",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive leg-result merge and deterministic payload write",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "build_three_engine_envelope.py": "supportive",
    "json": "supportive",
}

HELPER_PATH = ROOT / "scripts" / "build_three_engine_envelope.py"
spec = importlib.util.spec_from_file_location("build_three_engine_envelope", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(helper)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def package_observables(leg: dict[str, Any]) -> dict[str, str]:
    existing = leg.get("package_observables")
    if isinstance(existing, dict):
        return {str(key): str(value) for key, value in existing.items()}
    calls = leg.get("tool_calls", [])
    observables: dict[str, str] = {}
    for package in leg["aligned_packages_load_bearing"]:
        for call in calls:
            if isinstance(call, dict) and call.get("tool") == package:
                api = call.get("qualified_api/function") or call.get("qualified_api") or package
                output = call.get("output_object") or call.get("gates") or "claim-path observable"
                observables[package] = f"{api}: {output}"
                break
        else:
            observables[package] = leg.get("tool_manifest", {}).get(package, {}).get(
                "reason",
                f"{package} claim-path observable",
            )
    return observables


def engine_lane(leg: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": rel(result_path),
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": package_observables(leg),
        "claim_path_tools": leg.get("claim_path_tools", []),
        "package_versions": leg.get("package_versions", {}),
        "capability_receipts": leg.get("capability_receipts", []),
        "tool_calls": leg.get("tool_calls", []),
        "one_to_one_tool_calls": leg.get("one_to_one_tool_calls", {}),
    }


def merge_tool_manifest(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {engine: leg.get("TOOL_MANIFEST", {}) for engine, leg in legs.items()}


def merge_tool_depth(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {engine: leg.get("TOOL_INTEGRATION_DEPTH", {}) for engine, leg in legs.items()}


def compare_leg_signatures(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    signatures = {
        engine: leg["transition_graph"]["partition_signature"]
        for engine, leg in legs.items()
    }
    hashes = {
        engine: leg["partition_signature_sha256"]
        for engine, leg in legs.items()
    }
    graph_hashes = {
        engine: leg["transition_graph_sha256"]
        for engine, leg in legs.items()
    }
    return {
        "partition_signatures": signatures,
        "partition_signature_sha256": hashes,
        "partition_signature_agreement": len(set(hashes.values())) == 1,
        "transition_graph_sha256": graph_hashes,
        "transition_graph_hash_note": "Engine graph hashes may differ because each leg serializes source rows differently; partition signature is the cross-engine equality gate.",
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {
        engine: float(leg["transition_graph"]["partition_signature"]["scc_count"] - 2)
        for engine, leg in legs.items()
    }
    return {
        "julia_authoritative": True,
        "metric": "scc_count_minus_expected_two",
        "engine_values": values,
        "max_divergence": max(abs(value) for value in values.values()),
        "signature_hashes": {
            engine: leg["partition_signature_sha256"]
            for engine, leg in legs.items()
        },
    }


def build_result() -> dict[str, Any]:
    legs = {engine: load(path) for engine, path in LEG_PATHS.items()}
    jax = legs["jax"]
    julia = legs["julia"]
    pytorch = legs["pytorch"]
    comparison = compare_leg_signatures(legs)
    div = divergence(legs)
    proofs = {
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": jax["crossover_proofs"]["z3"]["verdict"],
            "erased_flip_verdict": jax["crossover_proofs"]["z3"]["erased_flip_verdict"],
            "proof_row": jax["crossover_proofs"]["z3"]["proof_row"],
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": jax["crossover_proofs"]["cvc5"]["verdict"],
            "erased_flip_verdict": jax["crossover_proofs"]["cvc5"]["erased_flip_verdict"],
            "proof_row": jax["crossover_proofs"]["cvc5"]["proof_row"],
        },
        "julia_z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": julia["crossover_proofs"]["julia_z3"]["verdict"],
            "erased_flip_verdict": julia["crossover_proofs"]["julia_z3"]["erased_flip_verdict"],
            "proof_row": julia["crossover_proofs"]["julia_z3"]["proof_row"],
        },
        "pytorch_z3": pytorch["crossover_proofs"]["z3"],
        "pytorch_cvc5": pytorch["crossover_proofs"]["cvc5"],
    }
    all_negative_controls_fire = all(row.get("fired") is True for row in jax["computed"]["negative_controls"].values())
    all_pass = bool(
        all(leg.get("all_pass") is True for leg in legs.values())
        and comparison["partition_signature_agreement"]
        and div["max_divergence"] == 0.0
        and proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == "unsat"
        and proofs["julia_z3"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_verdict"] == proofs["cvc5"]["erased_flip_verdict"] == "sat"
        and proofs["julia_z3"]["erased_flip_verdict"] == "sat"
        and all_negative_controls_fire
        and jax["transition_graph"]["monotone_exclusion_observable"]["monotone_non_decreasing_on_edges"] is True
        and jax["transition_graph"]["monotone_exclusion_observable"]["reachable_size_non_increasing_on_edges"] is True
    )
    extra_fields = {
        "ceiling": CLASSIFICATION,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "standard_schema_mode": "all_three_full_sims",
        "source_backed_validation": {
            "expected_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed {rel(RESULT_PATH)}"
            ),
            "strict_expected_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                f"scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed {rel(RESULT_PATH)}"
            ),
        },
        "TOOL_MANIFEST": merge_tool_manifest(legs),
        "TOOL_INTEGRATION_DEPTH": merge_tool_depth(legs),
        "capability_receipts": {engine: leg.get("capability_receipts", []) for engine, leg in legs.items()},
        "tool_calls": {engine: leg.get("tool_calls", []) for engine, leg in legs.items()},
        "one_to_one_tool_calls": {
            "pass": all(leg.get("one_to_one_tool_calls", {}).get("pass") is True for leg in legs.values()),
            "by_engine": {engine: leg.get("one_to_one_tool_calls", {}) for engine, leg in legs.items()},
        },
        "parent_lineage": jax["parent_lineage"],
        "seed_ledger": jax["seed_ledger"],
        "finite_S": jax["computed"]["finite_S"],
        "R_C_explicit": jax["computed"]["R_C_explicit"],
        "transition_graph": jax["transition_graph"],
        "basin_partition": jax["computed"]["basin_partition"],
        "trapping_and_lyapunov": jax["computed"]["trapping_and_lyapunov"],
        "escape_tests": jax["computed"]["escape_tests"],
        "negative_controls": jax["computed"]["negative_controls"],
        "sub_basin_honesty": jax["computed"]["sub_basin_honesty"],
        "build_contract_9_requirements": jax["computed"]["build_contract_9_requirements"],
        "guard": jax["computed"]["guard"],
        "engine_comparison": comparison,
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "legs": {engine: leg.get("package_versions", {}) for engine, leg in legs.items()},
        },
        "build_gates": {
            "classification_scratch": CLASSIFICATION == "scratch_diagnostic",
            "promotion_blocked": PROMOTION_ALLOWED is False,
            "formal_admission_blocked": FORMAL_ADMISSION_ALLOWED is False,
            "finite_state_count_33": jax["computed"]["finite_S"]["state_count"] == 33,
            "conditioned_shell_cells_marked": jax["computed"]["finite_S"]["conditioned_shell_cell_count"] == 4,
            "six_generators_declared": jax["computed"]["R_C_explicit"]["generator_count"] == 6,
            "one_terminal_closed_class": len(jax["transition_graph"]["terminal_classes"]) == 1,
            "absent_exit_proofs_pass": all(row["absent_exit_proof"]["no_exit"] for row in jax["transition_graph"]["terminal_classes"]),
            "lyapunov_edge_violations_zero": jax["transition_graph"]["monotone_exclusion_observable"]["edge_violation_count"] == 0,
            "reachable_size_edge_violations_zero": jax["transition_graph"]["monotone_exclusion_observable"]["reachable_size_edge_violation_count"] == 0,
            "basin_map_may_must_split": all(
                row.get("can_reach_terminal", {}).get("size") == 33
                and row.get("sure_basin_omega_containment", {}).get("cells") == [16]
                for row in jax["transition_graph"]["basin_map"].values()
            ),
            "coarse_33_caveat_carried": "CAVEAT-COARSE-33" in jax["computed"]["sub_basin_honesty"].get("carried_caveats", []),
            "all_negative_controls_fire": all_negative_controls_fire,
            "source_backed_lanes_present": set(legs) == {"julia", "jax", "pytorch"},
            "one_to_one_tool_calls": all(leg.get("one_to_one_tool_calls", {}).get("pass") is True for leg in legs.values()),
            "z3_cvc5_unsat": proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == "unsat",
            "erased_flip_sat": proofs["z3"]["erased_flip_verdict"] == proofs["cvc5"]["erased_flip_verdict"] == "sat",
            "julia_z3_unsat": proofs["julia_z3"]["verdict"] == "unsat",
            "partition_signature_cross_engine_agreement": comparison["partition_signature_agreement"],
            "audit_verdict_md_read_anchor_present": (SOURCE_PATH.parent / "audit_verdict.md").exists(),
        },
        "builder_hardening_addendum": {
            "round": "basin-map split plus named caveats",
            "closures": [
                "CAVEAT-BASIN-MAP-EXISTENTIAL split into can_reach_terminal may/existential and sure_basin_omega_containment must/universal rows",
                "CAVEAT-LYAPUNOV-DIRECTION made explicit as exclusion non-decreasing and reachable-set size non-increasing, with may/must trajectory samples",
                "CAVEAT-COARSE-33 carried by name; the 33-cell grid earns partition and controls only, not refined sub-basin claims",
            ],
            "audited_rows_byte_stable_expectation": "partition, terminal class, controls, escape rows, and proof verdict rows are expected to remain byte-stable except for basin-map split fields, source hashes, and regeneration timestamps",
        },
        "result_integrity": {
            "leg_result_sha256": {engine: sha256_file(path) for engine, path in LEG_PATHS.items()},
            "build_helper_path": rel(HELPER_PATH),
            "build_helper_sha256": sha256_file(HELPER_PATH),
            "envelope_content_without_result_hash_sha256": stable_sha256(
                {
                    "finite_S": jax["computed"]["finite_S"],
                    "partition": jax["transition_graph"]["partition_signature"],
                    "controls": jax["computed"]["negative_controls"],
                    "proofs": proofs,
                }
            ),
        },
    }
    payload = helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(legs[engine], LEG_PATHS[engine]) for engine in ("julia", "jax", "pytorch")},
        mode="all_three_full_sims",
        claim_path_tools=["Graphs", "Z3", "sympy", "z3", "cvc5", "torch_geometric", "torch.func"],
        crossover_proofs=proofs,
        divergence=div,
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage=jax["parent_lineage"],
        expected_lanes=("julia", "jax", "pytorch"),
        stability_pairs=[
            ("partition_signature", comparison["partition_signature_sha256"]["julia"]),
            ("negative_controls", stable_sha256(jax["computed"]["negative_controls"])),
            ("finite_S", stable_sha256(jax["computed"]["finite_S"])),
        ],
        generated_at=now_z(),
        extra_fields=extra_fields,
    )
    payload["all_pass"] = all_pass and all(value is True for value in payload["build_gates"].values())
    return payload


def main() -> int:
    payload = build_result()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
