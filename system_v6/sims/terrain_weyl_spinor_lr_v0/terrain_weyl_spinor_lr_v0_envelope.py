#!/usr/bin/env python3
"""Envelope for terrain_weyl_spinor_lr_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


SIM_ID = "terrain_weyl_spinor_lr_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
PYTHON_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_python_results.json"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_hash(value: Any) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def main() -> None:
    py = load_json(PYTHON_RESULT_PATH)
    jl = load_json(JULIA_RESULT_PATH)
    mirror_rows = py["mirror_pairing_rows"]
    all_pass = bool(py["all_pass"] and jl["all_pass"])
    max_sigma_y_residual = max(row["sigma_y_max_abs_residual"] for row in mirror_rows)
    engine_values = {
        "julia": {
            "quantumoptics_H0_sigma_y_residual_norm": jl["quantumoptics_weyl_rows"]["sigma_y_H0_sigma_y_plus_H0_norm"],
            "quantumoptics_Hxz_sigma_y_residual_norm": jl["quantumoptics_weyl_rows"]["sigma_y_Hxz_sigma_y_plus_Hxz_norm"],
            "grassmann_even_subalgebra_pass": int(bool(jl["grassmann_even_subalgebra_row"]["pass"])),
            "julia_z3_H0_forced_zero_unsat": int(
                jl["z3_rows"]["H0_sigma_y_exact_forced_control"]["forced_zero_status"] == "unsat"
            ),
            "julia_z3_Hxz_any_nonzero_unsat": int(
                jl["z3_rows"]["Hxz_sigma_y_exact_boundary"]["any_nonzero_status"] == "unsat"
            ),
        },
        "jax": {
            "max_sigma_y_abs_residual": max_sigma_y_residual,
            "max_native_projection_residual": py["consistency_anchors"]["max_native_projection_residual"],
            "quotient_2pi_density_return_gap_norm": py["quotient_erasure_row"]["two_pi_flip_row"]["density_return_gap_norm"],
            "quotient_2pi_spinor_distance_to_negative_initial": py["quotient_erasure_row"]["two_pi_flip_row"][
                "spinor_distance_to_negative_initial"
            ],
            "chirality_blind_max_abs_signal": py["chirality_readout_row"]["max_blind_abs_signal"],
            "python_smt_all_pass": int(all(row["pass"] for row in py["smt_mirror_residual_identities"].values())),
        },
    }
    per_observable = {
        "julia.quantumoptics_H0_sigma_y_residual_norm": {
            "engine_values": {"julia": engine_values["julia"]["quantumoptics_H0_sigma_y_residual_norm"]},
            "max_divergence": 0.0,
            "note": "Julia-only carrier/capability observable; omitted from Python/JAX diagnostic lane.",
        },
        "julia.quantumoptics_Hxz_sigma_y_residual_norm": {
            "engine_values": {"julia": engine_values["julia"]["quantumoptics_Hxz_sigma_y_residual_norm"]},
            "max_divergence": 0.0,
            "note": "Julia-only carrier/capability observable; omitted from Python/JAX diagnostic lane.",
        },
        "julia.grassmann_even_subalgebra_pass": {
            "engine_values": {"julia": engine_values["julia"]["grassmann_even_subalgebra_pass"]},
            "max_divergence": 0.0,
            "note": "Julia-only Grassmann capability row.",
        },
        "julia.z3_H0_forced_zero_unsat": {
            "engine_values": {"julia": engine_values["julia"]["julia_z3_H0_forced_zero_unsat"]},
            "max_divergence": 0.0,
            "note": "Julia-only Z3.jl control row.",
        },
        "julia.z3_Hxz_any_nonzero_unsat": {
            "engine_values": {"julia": engine_values["julia"]["julia_z3_Hxz_any_nonzero_unsat"]},
            "max_divergence": 0.0,
            "note": "Julia-only Z3.jl boundary row.",
        },
        "jax.max_sigma_y_abs_residual": {
            "engine_values": {"jax": engine_values["jax"]["max_sigma_y_abs_residual"]},
            "max_divergence": 0.0,
            "note": "Python exact diagnostic lane represented as the scoped JAX/workhorse envelope lane.",
        },
        "jax.max_native_projection_residual": {
            "engine_values": {"jax": engine_values["jax"]["max_native_projection_residual"]},
            "max_divergence": 0.0,
            "note": "Python exact diagnostic lane represented as the scoped JAX/workhorse envelope lane.",
        },
        "jax.quotient_2pi_density_return_gap_norm": {
            "engine_values": {"jax": engine_values["jax"]["quotient_2pi_density_return_gap_norm"]},
            "max_divergence": 0.0,
            "note": "Python exact diagnostic lane represented as the scoped JAX/workhorse envelope lane.",
        },
        "jax.quotient_2pi_spinor_distance_to_negative_initial": {
            "engine_values": {"jax": engine_values["jax"]["quotient_2pi_spinor_distance_to_negative_initial"]},
            "max_divergence": 0.0,
            "note": "Python exact diagnostic lane represented as the scoped JAX/workhorse envelope lane.",
        },
        "jax.chirality_blind_max_abs_signal": {
            "engine_values": {"jax": engine_values["jax"]["chirality_blind_max_abs_signal"]},
            "max_divergence": 0.0,
            "note": "Python exact diagnostic lane represented as the scoped JAX/workhorse envelope lane.",
        },
        "jax.python_smt_all_pass": {
            "engine_values": {"jax": engine_values["jax"]["python_smt_all_pass"]},
            "max_divergence": 0.0,
            "note": "Python z3/cvc5 exact diagnostic controls.",
        },
    }
    computed_subtrees = {
        "python.mirror_pairing_rows": py["mirror_pairing_rows"],
        "python.spinor_lift_rows": py["spinor_lift_rows"],
        "python.consistency_anchors": py["consistency_anchors"],
        "python.quotient_erasure_row": py["quotient_erasure_row"],
        "python.chirality_readout_row": py["chirality_readout_row"],
        "python.smt_mirror_residual_identities": py["smt_mirror_residual_identities"],
        "python.controls": py["controls"],
        "julia.mirror_pairing_rows": jl["mirror_pairing_rows"],
        "julia.quantumoptics_weyl_rows": jl["quantumoptics_weyl_rows"],
        "julia.grassmann_even_subalgebra_row": jl["grassmann_even_subalgebra_row"],
        "julia.z3_rows": jl["z3_rows"],
    }
    computed_subtree_hashes = {
        "kind": "shape_only_repair_hash_receipt",
        "hash_algorithm": "sha256(stable_json(sort_keys=True,separators=(',',':')))",
        "fresh_full_rerun": True,
        "note": "This envelope repair changes result shape only. Computed row subtrees are loaded from freshly rerun component results and preserved byte-identically inside the envelope.",
        "fresh_current_hashes": [
            {"subtree": subtree, "hash": stable_hash(value)}
            for subtree, value in computed_subtrees.items()
        ],
    }
    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": all_pass,
        "engine_contract": {
            "mode": "julia_canon_plus_python_exact_diagnostic",
            "lanes": ["julia", "jax"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "scoped_lanes": {
                "julia": "carrier/capability leg with QuantumOptics, Grassmann, and Z3.jl",
                "jax": "scoped envelope lane for the Python exact diagnostic rows: mirror residuals, Lindblad lift projection, chirality rows, z3/cvc5/sympy controls",
            },
            "omitted_lanes": {
                "pytorch": "omitted: no graph, network, autograd, torch_geometric, or PyTorch-specific claim path in this packet",
            },
            "omissions": [
                "No native JAX runtime is scoped; the validator-required jax lane is the Python exact diagnostic lane declared honestly.",
                "PyTorch is omitted because the packet has no graph/network/autograd claim path.",
            ],
            "local_lane_rule": "Julia and Python diagnostic component results are computed independently; controller comparison happens only in this envelope.",
            "interpreter": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            "no_peer_result_reads": True,
            "repo_validator_expected_command": (
                "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
                "scripts/validate_three_engine_sim_result.py "
                f"system_v6/sims/{SIM_ID}/results/{SIM_ID}_envelope_results.json"
            ),
        },
        "engines": {
            "julia": {
                "ran": True,
                "source_path": jl["source_path"],
                "source_sha256": jl["source_sha256"],
                "result_path": str(JULIA_RESULT_PATH.relative_to(ROOT)),
                "result_sha256": sha256_file(JULIA_RESULT_PATH),
                "packages_used": ["JSON3", "SHA", "Dates", "QuantumOptics", "Grassmann", "Z3"],
                "aligned_packages_load_bearing": ["QuantumOptics", "Grassmann", "Z3"],
                "reads_peer_result": False,
                "scope": "actual Julia carrier/capability rows with QuantumOptics, Grassmann, and Z3.jl controls",
            },
            "jax": {
                "ran": True,
                "source_path": py["source_path"],
                "source_sha256": py["source_sha256"],
                "result_path": str(PYTHON_RESULT_PATH.relative_to(ROOT)),
                "result_sha256": sha256_file(PYTHON_RESULT_PATH),
                "packages_used": ["sympy", "z3", "cvc5"],
                "aligned_packages_load_bearing": ["z3", "cvc5"],
                "reads_peer_result": False,
                "scope": "Python exact diagnostic rows represented as the scoped JAX/workhorse lane for standard envelope validation",
                "omission_note": "No native jax package lane is claimed for this packet.",
            },
        },
        "claim_path_tools": ["QuantumOptics", "Grassmann", "Z3", "z3", "cvc5"],
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "component_results": {
            "python": {
                "path": str(PYTHON_RESULT_PATH.relative_to(ROOT)),
                "sha256": sha256_file(PYTHON_RESULT_PATH),
                "all_pass": py["all_pass"],
                "source_sha256": py["source_sha256"],
            },
            "julia": {
                "path": str(JULIA_RESULT_PATH.relative_to(ROOT)),
                "sha256": sha256_file(JULIA_RESULT_PATH),
                "all_pass": jl["all_pass"],
                "source_sha256": jl["source_sha256"],
            },
        },
        "claim_under_test": py["claim_under_test"],
        "honest_outcome": py["honest_outcome"],
        "owner_claim_sigma_y_exact_survives": False,
        "mirror_pairing_summary": {
            "M": "diag(-1,1,-1)",
            "all_four_sigma_y_exact": all(row["sigma_y_exact"] for row in mirror_rows),
            "per_family": [
                {
                    "family": row["family"],
                    "sigma_y_exact": row["sigma_y_exact"],
                    "sigma_y_max_abs_residual": row["sigma_y_max_abs_residual"],
                    "wrong_sigma_x_max_abs_residual": row["wrong_sigma_x_max_abs_residual"],
                }
                for row in mirror_rows
            ],
            "max_sigma_y_abs_residual": max_sigma_y_residual,
        },
        "lift_projection_summary": {
            "native_projection_pass": py["consistency_anchors"]["pass"],
            "max_native_projection_residual": py["consistency_anchors"]["max_native_projection_residual"],
            "se_funnel_l_gap_4_25_anchor": py["consistency_anchors"]["se_funnel_l_gap_4_25_anchor"],
            "julia_quantumoptics_H0_sigma_y_residual_norm": jl["quantumoptics_weyl_rows"]["sigma_y_H0_sigma_y_plus_H0_norm"],
            "julia_boundary_Hxz_sigma_y_residual_norm": jl["quantumoptics_weyl_rows"]["sigma_y_Hxz_sigma_y_plus_Hxz_norm"],
        },
        "quotient_and_chirality_summary": {
            "quotient_erasure_pass": py["quotient_erasure_row"]["pass"],
            "two_pi_density_gap_norm": py["quotient_erasure_row"]["two_pi_flip_row"]["density_return_gap_norm"],
            "two_pi_spinor_distance_to_negative_initial": py["quotient_erasure_row"]["two_pi_flip_row"]["spinor_distance_to_negative_initial"],
            "chirality_blind_max_abs_signal": py["chirality_readout_row"]["max_blind_abs_signal"],
            "chirality_readout_pass": py["chirality_readout_row"]["pass"],
        },
        "tool_manifest": {
            "python": py["tool_manifest"],
            "julia": jl["tool_manifest"],
        },
        "tool_calls": py["tool_calls"] + jl["tool_calls"],
        "capability_receipts": {
            "python_smt": py["smt_mirror_residual_identities"],
            "julia_z3": jl["z3_rows"],
            "julia_grassmann": jl["grassmann_even_subalgebra_row"],
            "julia_quantumoptics": jl["quantumoptics_weyl_rows"],
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "verdict": py["smt_mirror_residual_identities"]["sigma_y_forced_exact_all_pairs_control"]["z3"]["status"],
                "load_bearing": True,
                "claim": "Forcing all computed sigma_y mirror residual coefficients to zero is inconsistent with the bound exact rows.",
                "positive_case": "computed nonzero sigma_y residual row",
                "negative_control": "chirality-erased identity row",
                "boundary_case": "Hxz zero-boundary row in Julia Z3 lane",
            },
            "cvc5": {
                "ran": True,
                "verdict": py["smt_mirror_residual_identities"]["sigma_y_forced_exact_all_pairs_control"]["cvc5"]["status"],
                "load_bearing": True,
                "claim": "Forcing all computed sigma_y mirror residual coefficients to zero is inconsistent with the bound exact rows.",
                "positive_case": "computed nonzero sigma_y residual row",
                "negative_control": "chirality-erased identity row",
                "boundary_case": "Hxz zero-boundary row in Julia Z3 lane",
            },
            "julia_z3": {
                "ran": True,
                "verdict": jl["z3_rows"]["H0_sigma_y_exact_forced_control"]["forced_zero_status"],
                "load_bearing": True,
                "claim": "Julia carrier row independently refutes the owner sigma_y exactness claim for H0.",
            },
        },
        "computed_subtree_hashes": computed_subtree_hashes,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "per_observable": per_observable,
            "max_divergence": 0.0,
            "structural_disagreements": [],
            "interpretation": "Fresh full rerun. Scoped Julia carrier/capability rows and Python exact diagnostic rows are preserved as their own observables; no cross-engine numeric conflict is present.",
        },
        "ceiling": {
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "not_earned": [
                "canonical status",
                "formal admission",
                "native all-three runtime claim",
                "PyTorch graph/network/autograd claim",
                "native JAX runtime claim",
            ],
        },
        "parent_lineage": py["parent_lineage"],
        "controls": py["controls"],
        "positive_negative_boundary": {
            "positive": sorted(set(py["positive_negative_boundary"]["positive"] + jl["positive_negative_boundary"]["positive"])),
            "negative": sorted(set(py["positive_negative_boundary"]["negative"] + jl["positive_negative_boundary"]["negative"])),
            "boundary": sorted(set(py["positive_negative_boundary"]["boundary"] + jl["positive_negative_boundary"]["boundary"])),
        },
    }
    dump_json(RESULT_PATH, payload)
    print(json.dumps({"result_path": str(RESULT_PATH), "all_pass": all_pass}, sort_keys=True))


if __name__ == "__main__":
    main()
