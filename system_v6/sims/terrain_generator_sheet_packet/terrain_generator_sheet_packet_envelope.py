#!/usr/bin/env python3
"""Envelope for the source-locked terrain generator sheet packet."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "terrain_generator_sheet_packet"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOL = 1.0e-6

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from independent engine receipts",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for the v6 packet files",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source hashing",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive", "hashlib": "supportive"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "values": payload["shared_scalars"],
        "controls": payload["controls"],
    }


def compare_shared_scalars(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    key_sets = {engine: set(payload["shared_scalars"].keys()) for engine, payload in payloads.items()}
    common = sorted(set.intersection(*key_sets.values()))
    same_sets = all(keys == key_sets["julia"] for keys in key_sets.values())
    rows = []
    max_divergence = 0.0
    max_key = None
    for key in common:
        values = {engine: float(payload["shared_scalars"][key]) for engine, payload in payloads.items()}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_divergence:
            max_divergence = diff
            max_key = key
    union = set.union(*key_sets.values())
    return {
        "same_named_observable_sets": same_sets,
        "common_observable_count": len(common),
        "missing_by_engine": {engine: sorted(union - keys) for engine, keys in key_sets.items()},
        "rows": rows,
        "max_divergence": max_divergence,
        "max_divergence_key": max_key,
        "within_tolerance": same_sets and max_divergence <= TOL,
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def ne_variant_divergence(payload: dict[str, Any]) -> dict[str, Any]:
    pair = payload["pair_separation_table"]["Vortex_vs_Spiral"]
    vortex_cert = payload["terrain_certificates"]
    # Keep this table numeric and simple: it answers whether the live source
    # alternatives are the same executable object. They are not.
    return {
        "pure_pair_trace_distance_rho_0": pair["pure_trace_distance_rho_0"],
        "weak_pair_trace_distance_rho_0": pair["weak_trace_distance_rho_0"],
        "pair_distance_delta_weak_minus_pure": pair["weak_trace_distance_rho_0"] - pair["pure_trace_distance_rho_0"],
        "vortex_rho_0_delta_pure": vortex_cert["Vortex:pure_hamiltonian"]["state_deltas"]["rho_0"]["trace_distance_from_input"],
        "vortex_rho_0_delta_weak": vortex_cert["Vortex:weak_dissipator"]["state_deltas"]["rho_0"]["trace_distance_from_input"],
        "spiral_rho_0_delta_pure": vortex_cert["Spiral:pure_hamiltonian"]["state_deltas"]["rho_0"]["trace_distance_from_input"],
        "spiral_rho_0_delta_weak": vortex_cert["Spiral:weak_dissipator"]["state_deltas"]["rho_0"]["trace_distance_from_input"],
        "live_alternatives_distinct": abs(pair["weak_trace_distance_rho_0"] - pair["pure_trace_distance_rho_0"]) > 1.0e-4,
    }


def build_result() -> dict[str, Any]:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    comparison = compare_shared_scalars(payloads)
    jax_z3 = payloads["jax"]["crossover_proofs"]["z3"]
    jax_cvc5 = payloads["jax"]["crossover_proofs"]["cvc5"]
    julia_z3 = payloads["julia"]["crossover_proofs"]["julia_z3"]
    controls = {
        "legs_all_pass": all(payload["all_pass"] is True for payload in payloads.values()),
        "classification_ceiling_held": CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False,
        "shared_scalars_within_tolerance": comparison["within_tolerance"],
        "source_line_refs_match": payloads["julia"]["source_line_refs"] == payloads["jax"]["source_line_refs"] == payloads["pytorch"]["source_line_refs"],
        "z3_cvc5_pit_source_forced_equal_unsat": jax_z3["verdict"] == jax_cvc5["verdict"] == "unsat",
        "z3_cvc5_sigma_swapped_valid": jax_z3["sigma_swapped_pit_source_convention_inequality"]
        == jax_cvc5["sigma_swapped_pit_source_convention_inequality"]
        == "unsat",
        "julia_z3_pit_source_forced_equal_unsat": julia_z3["verdict"] == "unsat",
        "julia_z3_sigma_swapped_valid": julia_z3["sigma_swapped_pit_source_convention_inequality"] == "unsat",
        "ne_live_alternatives_distinct": ne_variant_divergence(payloads["julia"])["live_alternatives_distinct"],
        "placements_16_instantiated": len(payloads["julia"]["placements_16"]) == 16,
        "fiber_base_loop_coordinate_check": payloads["julia"]["shared_scalars"]["fiber_stationary_count"] == 8.0
        and payloads["julia"]["shared_scalars"]["base_visible_count"] == 8.0,
        "source_lock_fresh": all(payload["source_lock_freshness"]["all_fresh"] is True for payload in payloads.values()),
        "unitality_columns_pass": all(payload["unitality_column"]["pass"] is True for payload in payloads.values()),
        "axis0_response_computed": all(payload["axis0_response"]["pass"] is True for payload in payloads.values()),
        "entropy_columns_present": all("entropy_columns" in payload and len(payload["entropy_columns"]["rows"]) == 10 for payload in payloads.values()),
    }
    all_pass = bool(all(controls.values()))
    return {
        "schema_version": "three_engine_sim_result_v1",
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "reads_peer_result": False,
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "object_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "all_pass": all_pass,
        "claim_ceiling": "scratch diagnostic only; no formal admission, canonical terrain claim, or source doctrine promotion",
        "source_line_refs": payloads["julia"]["source_line_refs"],
        "source_lock_freshness": {engine: payload["source_lock_freshness"] for engine, payload in payloads.items()},
        "pin_spec": payloads["julia"]["pin_spec"],
        "pauli_expansion_family_pin_metadata": payloads["julia"]["pauli_expansion_family_pin_metadata"],
        "states": payloads["julia"]["states"],
        "engines": {
            "julia": engine_record(payloads["julia"], JULIA_RESULT),
            "jax": engine_record(payloads["jax"], JAX_RESULT),
            "pytorch": engine_record(payloads["pytorch"], PYTORCH_RESULT),
        },
        "pair_separation_table": payloads["julia"]["pair_separation_table"],
        "placements_16": payloads["julia"]["placements_16"],
        "ne_variants_divergence": ne_variant_divergence(payloads["julia"]),
        "unitality_column": {engine: payload["unitality_column"] for engine, payload in payloads.items()},
        "axis0_response": {engine: payload["axis0_response"] for engine, payload in payloads.items()},
        "entropy_columns": {engine: payload["entropy_columns"] for engine, payload in payloads.items()},
        "negative_controls": payloads["julia"]["negative_controls"],
        "sigma_swap_control_detail": payloads["julia"]["sigma_swap_control_detail"],
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax_z3["verdict"],
                "sigma_swapped_pit_source_convention_equality": jax_z3["sigma_swapped_pit_source_convention_equality"],
                "sigma_swapped_pit_source_convention_inequality": jax_z3["sigma_swapped_pit_source_convention_inequality"],
                "binds_generator_entries": jax_z3["binds_generator_entries"],
                "asserted_precomputed_boolean": jax_z3["asserted_precomputed_boolean"],
                "proof_kind": jax_z3["proof_kind"],
                "symbolic_derivation_in_solver": jax_z3["symbolic_derivation_in_solver"],
                "entry_binding_honesty_label": jax_z3["entry_binding_honesty_label"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax_cvc5["verdict"],
                "sigma_swapped_pit_source_convention_equality": jax_cvc5["sigma_swapped_pit_source_convention_equality"],
                "sigma_swapped_pit_source_convention_inequality": jax_cvc5["sigma_swapped_pit_source_convention_inequality"],
                "binds_generator_entries": jax_cvc5["binds_generator_entries"],
                "asserted_precomputed_boolean": jax_cvc5["asserted_precomputed_boolean"],
                "proof_kind": jax_cvc5["proof_kind"],
                "symbolic_derivation_in_solver": jax_cvc5["symbolic_derivation_in_solver"],
                "entry_binding_honesty_label": jax_cvc5["entry_binding_honesty_label"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3["verdict"],
                "sigma_swapped_pit_source_convention_equality": julia_z3["sigma_swapped_pit_source_convention_equality"],
                "sigma_swapped_pit_source_convention_inequality": julia_z3["sigma_swapped_pit_source_convention_inequality"],
                "proof_kind": julia_z3["proof_kind"],
                "symbolic_derivation_in_solver": julia_z3["symbolic_derivation_in_solver"],
                "entry_binding_honesty_label": julia_z3["entry_binding_honesty_label"],
            },
        },
        "claim_path_tools": collect_claim_tools(payloads),
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {engine: payload["shared_scalars"] for engine, payload in payloads.items()},
            "comparison": comparison,
            "max_divergence": comparison["max_divergence"],
            "max_divergence_key": comparison["max_divergence_key"],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "controls": controls,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "envelope": str(RESULT_PATH),
                "all_pass": result["all_pass"],
                "max_divergence": result["divergence"]["max_divergence"],
                "max_divergence_key": result["divergence"]["max_divergence_key"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
