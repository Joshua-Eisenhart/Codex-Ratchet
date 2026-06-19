#!/usr/bin/env python3
"""Envelope for ring_checkerboard_support_graph_probe."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "ring_checkerboard_support_graph_probe"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
PRIMARY_N = 8
COMMON_VALUE_KEYS = [
    "support_vertex_count",
    "support_edge_count",
    "parity_transition_rate",
    "cross_partition_rate",
    "mean_abs_gradient",
    "phi0_variance",
    "mean_orientation_score_delta",
    "z3_coloring_unsat",
    "cvc5_coloring_unsat",
]
REQUIRED_CONTROLS = [
    "shuffled_adjacency",
    "erased_coloring",
    "erased_nesting",
    "reversed_orientation",
    "label_shuffle",
    "scrambled_same_parity_adjacency_for_smt",
]
MUST_NOT_CLAIM_FENCES = [
    "Axis-0 closure",
    "manifold admission",
    "canonical ring-checkerboard support",
    "settled Xi",
    "physics/cosmology/consciousness/world-engine",
    "collapse of the live readings preserved in the pre-AI provenance page",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_leg(engine: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{SIM_ID}_{engine}_results.json"
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": payload["result_path"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "reads_peer_result": payload["reads_peer_result"],
        "core_semantics_path": payload["core_semantics_path"],
        "engine_native_roles": payload["engine_native_roles"],
        "phi0_status": payload["phi0_status"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "pin_block_sha256": payload["pin_block_sha256"],
        "support_table_hash": payload["support_table_hash"],
        "primary_summary": payload["primary_summary"],
        "gate_pass": payload["gate_pass"],
        "controls_fired": {name: payload["controls"][name]["fired"] for name in REQUIRED_CONTROLS},
        "kill_condition_met": payload["kill_conditions"]["kill_condition_met"],
        "values": payload["values"],
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    max_div = 0.0
    max_key = None
    engine_values = {engine: {key: float(payload["values"][key]) for key in COMMON_VALUE_KEYS} for engine, payload in legs.items()}
    for key in COMMON_VALUE_KEYS:
        values = {engine: engine_values[engine][key] for engine in legs}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_div:
            max_div = diff
            max_key = key
    return {
        "julia_authoritative": True,
        "engine_values": engine_values,
        "max_divergence": max_div,
        "max_divergence_key": max_key,
        "comparison": {
            "common_observable_count": len(COMMON_VALUE_KEYS),
            "rows": rows,
            "within_tolerance": max_div <= 1.0e-8,
            "same_named_observable_sets": True,
        },
    }


def build_result() -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ("julia", "jax", "pytorch")}
    gate_names = {f"G{i}" for i in range(1, 9)}
    pin_strings = {payload["pin_block_canonical_json"] for payload in legs.values()}
    pin_hashes = {payload["pin_block_sha256"] for payload in legs.values()}
    support_hashes = {payload["support_table_hash"] for payload in legs.values()}
    fences_ok = all(payload["must_not_claim_fences"] == MUST_NOT_CLAIM_FENCES for payload in legs.values())
    ceiling_ok = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["candidate_only"]["axis0_rough_draft_formalization"] == "CANDIDATE only"
        and payload["candidate_only"]["source_doc_title"] == "Axis 0 rough and drifty. NOT CANON.md"
        for payload in legs.values()
    )
    pin_ok = len(pin_strings) == 1 and len(pin_hashes) == 1
    support_ok = len(support_hashes) == 1
    all_gates_present = all(gate_names <= set(payload["gate_pass"].keys()) and gate_names <= set(payload["gates"].keys()) for payload in legs.values())
    all_gate_pass = all(all(payload["gate_pass"][gate] for gate in gate_names) for payload in legs.values())
    independence_labeling_ok = (
        legs["jax"]["core_semantics_path"] == "mirrored_pure_python_helpers"
        and legs["pytorch"]["core_semantics_path"] == "mirrored_pure_python_helpers"
        and legs["julia"]["core_semantics_path"] == "julia_independent_formula_implementation"
        and all(payload["engine_native_roles"] for payload in legs.values())
    )
    phi0_status_ok = all(payload["phi0_status"] == "candidate_support_graph_scalar_not_axis0" for payload in legs.values())
    controls_fired = all(
        bool(payload["controls"][name]["fired"])
        for payload in legs.values()
        for name in REQUIRED_CONTROLS
    )
    kill_conditions_ok = all(payload["kill_conditions"]["kill_condition_met"] is False for payload in legs.values())
    presentation_ok = all(
        payload["presentation_receipts"]["presentation_keys"] == ["flat", "spherical-shell", "nested-ring"]
        and all(
            len(payload["presentation_receipts"]["row_location_receipts"][key]) == payload["primary_summary"]["vertex_count"]
            for key in payload["presentation_receipts"]["presentation_keys"]
        )
        and all(row["fired"] for row in payload["presentation_receipts"]["disagreement_controls"].values())
        for payload in legs.values()
    )
    smt_ok = (
        legs["jax"]["crossover_proofs"]["z3"]["verdict"] == "unsat"
        and legs["jax"]["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
        and legs["jax"]["crossover_proofs"]["z3"]["scrambled_same_parity_control"] == "sat"
        and legs["jax"]["crossover_proofs"]["cvc5"]["scrambled_same_parity_control"] == "sat"
        and legs["pytorch"]["crossover_proofs"]["z3"]["verdict"] == "unsat"
        and legs["pytorch"]["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
        and legs["julia"]["crossover_proofs"]["julia_z3"]["verdict"] == "unsat"
        and legs["julia"]["crossover_proofs"]["julia_z3"]["scrambled_same_parity_control"] == "sat"
    )
    comparability_ok = all(
        payload["comparability_row"]["mct_support_size"] == 384
        and payload["comparability_row"]["n8_support_vertex_count"] == PRIMARY_N * PRIMARY_N
        and payload["comparability_row"]["supersedes_or_closes_mct"] is False
        for payload in legs.values()
    )
    div = divergence(legs)
    all_pass = all(
        [
            all(payload["all_pass"] for payload in legs.values()),
            ceiling_ok,
            fences_ok,
            pin_ok,
            support_ok,
            all_gates_present,
            all_gate_pass,
            independence_labeling_ok,
            phi0_status_ok,
            controls_fired,
            kill_conditions_ok,
            presentation_ok,
            smt_ok,
            comparability_ok,
            div["comparison"]["within_tolerance"],
        ]
    )
    jax_proofs = legs["jax"]["crossover_proofs"]
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
            "reads_peer_result": False,
        },
        "claim": "owner-source ring/checkerboard support graph G=(V,E,kappa,V_inner,V_outer,phi0) computed as measured finite graph behaviors on n=8 with ladder rows",
        "allowed_claims": [
            "scratch diagnostic support-graph behavior on the declared finite construction",
            "comparison row against MCT support counts without supersession or closure",
        ],
        "must_not_claim_fences": MUST_NOT_CLAIM_FENCES,
        "candidate_only": {
            "axis0_rough_draft_formalization": "CANDIDATE only",
            "source_doc_title": "Axis 0 rough and drifty. NOT CANON.md",
        },
        "pin_block_sha256": next(iter(pin_hashes)),
        "pin_block_canonical_json": next(iter(pin_strings)),
        "pin_identical_across_legs": pin_ok,
        "claim_path_tools": ["Graphs", "Z3", "jax", "cvc5", "torch", "torch_geometric"],
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml",
            "role": "canon finite graph construction plus Graphs.jl and Z3.jl checks",
            "classification": CLASSIFICATION,
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier", "packages": legs["julia"]["packages_used"], "role": "semantic_owner"},
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": legs["jax"]["packages_used"], "role": "ladder_sweep_and_smt_worker"},
            "pytorch": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": legs["pytorch"]["packages_used"], "role": "independent_graph_lane"},
            "tensor_exchange": "none; no cross-engine tensor exchange on claim path",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "engines": {engine: engine_record(payload) for engine, payload in legs.items()},
        "controls": {engine: {name: legs[engine]["controls"][name] for name in REQUIRED_CONTROLS} for engine in legs},
        "kill_conditions": {engine: legs[engine]["kill_conditions"] for engine in legs},
        "presentation_receipts": {engine: legs[engine]["presentation_receipts"] for engine in legs},
        "comparability_rows": {engine: legs[engine]["comparability_row"] for engine in legs},
        "gate_pass": {
            "ceiling_ok": ceiling_ok,
            "fences_ok": fences_ok,
            "pin_ok": pin_ok,
            "support_hash_ok": support_ok,
            "all_gates_present": all_gates_present,
            "all_gate_pass": all_gate_pass,
            "independence_labeling_ok": independence_labeling_ok,
            "phi0_status_ok": phi0_status_ok,
            "controls_fired": controls_fired,
            "kill_conditions_ok": kill_conditions_ok,
            "presentation_ok": presentation_ok,
            "smt_ok": smt_ok,
            "comparability_ok": comparability_ok,
            "divergence_ok": div["comparison"]["within_tolerance"],
        },
        "crossover_proofs": {
            "z3": jax_proofs["z3"],
            "cvc5": jax_proofs["cvc5"],
            "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"],
            "pytorch_z3": legs["pytorch"]["crossover_proofs"]["z3"],
            "pytorch_cvc5": legs["pytorch"]["crossover_proofs"]["cvc5"],
        },
        "phi0_status_by_engine": {engine: legs[engine]["phi0_status"] for engine in legs},
        "independence_labeling": {
            engine: {
                "core_semantics_path": legs[engine]["core_semantics_path"],
                "engine_native_roles": legs[engine]["engine_native_roles"],
            }
            for engine in legs
        },
        "divergence": div,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": result["all_pass"],
                "result_path": str(RESULT_PATH),
                "pin_identical": result["pin_identical_across_legs"],
                "max_divergence": result["divergence"]["max_divergence"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
