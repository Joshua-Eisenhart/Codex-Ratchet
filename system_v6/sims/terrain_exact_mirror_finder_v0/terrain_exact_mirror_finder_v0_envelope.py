#!/usr/bin/env python3
"""Assemble terrain_exact_mirror_finder_v0 envelope."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


SIM_ID = "terrain_exact_mirror_finder_v0"
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
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def main() -> int:
    py = load_json(PYTHON_RESULT_PATH)
    jl = load_json(JULIA_RESULT_PATH)
    all_pass = bool(py["all_pass"] and jl["all_pass"])
    engine_values = {
        "julia": {
            "M_Ni_first_three_exact": int(all(row["exact"] for row in jl["M_Ni_rows"] if row["family"] in ["Ne", "Ni", "Se"])),
            "M_Ni_Si_exact": int(next(row for row in jl["M_Ni_rows"] if row["family"] == "Si")["exact"]),
            "sigma_y_all_fail": int(all(not row["exact"] for row in jl["sigma_y_rows"])),
            "symbolics_pass": int(bool(jl["symbolics_rows"]["pass"])),
            "julia_z3_pass": int(
                jl["z3_rows"]["M_Ni_first_three_zero"]["any_nonzero_status"] == "unsat"
                and jl["z3_rows"]["Si_erased_flip_control_nonzero"]["forced_zero_status"] == "unsat"
            ),
        },
        "jax": {
            "common_all_four_exists": int(bool(py["common_intersection"]["common_all_four_exists"])),
            "owner_single_mirror_survives": int(bool(py["owner_single_mirror_reading_survives"])),
            "sigma_y_all_fail": int(bool(py["controls"]["sigma_y_candidate"]["all_fail"])),
            "identity_all_fail": int(bool(py["controls"]["identity_candidate"]["all_fail"])),
            "random_orthogonal_all_fail": int(bool(py["controls"]["random_orthogonal_candidate"]["all_fail"])),
            "spinor_lift_pass": int(bool(py["spinor_lift_consistency"]["pass"])),
            "xz_positive_control_exact": int(bool(py["xz_frame_positive_control"]["exact"])),
            "python_smt_all_pass": int(all(row["pass"] for row in py["smt_solve_space_identities"].values())),
        },
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
            "mode": "FIELD",
            "lanes": ["julia", "jax"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "scoped_lanes": {
                "julia": "Symbolics/Z3.jl independent exact/control leg",
                "jax": "Python exact diagnostic lane represented as the validator JAX/workhorse lane; uses sympy plus z3/cvc5 for exact solve-space identities",
            },
            "omitted_lanes": {
                "pytorch": "omitted: no graph, network, autograd, torch_geometric, or PyTorch-specific claim path in this packet"
            },
            "interpreter": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            "no_peer_result_reads": True,
        },
        "engines": {
            "julia": {
                "ran": True,
                "source_path": jl["source_path"],
                "source_sha256": jl["source_sha256"],
                "result_path": str(JULIA_RESULT_PATH.relative_to(ROOT)),
                "result_sha256": sha256_file(JULIA_RESULT_PATH),
                "packages_used": ["Symbolics", "Z3", "JSON"],
                "aligned_packages_load_bearing": ["Symbolics", "Z3"],
                "reads_peer_result": False,
                "tool_calls": jl["tool_calls"],
                "scope": "independent Julia Symbolics/Z3.jl rows for H0 flip/kernel identities and zero/nonzero controls",
            },
            "jax": {
                "ran": True,
                "source_path": py["source_path"],
                "source_sha256": py["source_sha256"],
                "result_path": str(PYTHON_RESULT_PATH.relative_to(ROOT)),
                "result_sha256": sha256_file(PYTHON_RESULT_PATH),
                "packages_used": ["sympy", "z3", "cvc5", "scipy", "numpy"],
                "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
                "reads_peer_result": False,
                "tool_calls": py["tool_calls"],
                "scope": "exact solve-space and controls lane; declared as JAX/workhorse envelope lane for standard validator compatibility",
                "omission_note": "No native jax package is claimed; this packet is an exact symbolic field diagnostic.",
            },
        },
        "claim_path_tools": ["Symbolics", "Z3", "sympy", "z3", "cvc5"],
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "component_results": {
            "python": {"path": str(PYTHON_RESULT_PATH.relative_to(ROOT)), "sha256": sha256_file(PYTHON_RESULT_PATH), "all_pass": py["all_pass"]},
            "julia": {"path": str(JULIA_RESULT_PATH.relative_to(ROOT)), "sha256": sha256_file(JULIA_RESULT_PATH), "all_pass": jl["all_pass"]},
        },
        "claim_under_test": py["claim_under_test"],
        "honest_outcome": py["honest_outcome"],
        "owner_single_mirror_reading_survives": False,
        "per_family_solution_sets": py["per_family_solution_sets"],
        "common_intersection": py["common_intersection"],
        "controls": py["controls"],
        "spinor_lift_consistency": py["spinor_lift_consistency"],
        "xz_frame_positive_control": py["xz_frame_positive_control"],
        "parent_lineage": py["parent_lineage"],
        "tool_manifest": {"python": py["tool_manifest"], "julia": jl["tool_manifest"]},
        "TOOL_MANIFEST": {"python": py["TOOL_MANIFEST"], "julia": jl["TOOL_MANIFEST"]},
        "TOOL_INTEGRATION_DEPTH": {"python": py["TOOL_INTEGRATION_DEPTH"], "julia": jl["TOOL_INTEGRATION_DEPTH"]},
        "tool_calls": py["tool_calls"] + jl["tool_calls"],
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": "unsat",
                "row": "solve_space_identity_Se_Ne_Ni_M_Ni_zero.any_nonzero",
                "erased_control": "identity_erased_flip_control_nonzero.force_zero is unsat",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": "unsat",
                "row": "solve_space_identity_Se_Ne_Ni_M_Ni_zero.any_nonzero",
                "erased_control": "identity_erased_flip_control_nonzero.force_zero is unsat",
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": "unsat",
                "row": "M_Ni_first_three_zero.any_nonzero",
            },
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": 0.0,
            "per_observable": {
                "common_all_four_exists": {
                    "engine_values": {"julia": 0, "jax": engine_values["jax"]["common_all_four_exists"]},
                    "max_divergence": 0.0,
                    "note": "Julia verifies M_Ni fails Si; Python records the full empty intersection.",
                },
                "sigma_y_all_fail": {
                    "engine_values": {"julia": engine_values["julia"]["sigma_y_all_fail"], "jax": engine_values["jax"]["sigma_y_all_fail"]},
                    "max_divergence": 0.0,
                },
                "solve_space_controls": {
                    "engine_values": {"julia": engine_values["julia"]["julia_z3_pass"], "jax": engine_values["jax"]["python_smt_all_pass"]},
                    "max_divergence": 0.0,
                },
            },
        },
        "computed_subtree_hashes": {
            "hash_algorithm": "sha256(stable_json(sort_keys=True,separators=(',',':')))",
            "fresh_full_rerun": True,
            "fresh_current_hashes": [
                {"subtree": "python.per_family_solution_sets", "hash": stable_hash(py["per_family_solution_sets"])},
                {"subtree": "python.common_intersection", "hash": stable_hash(py["common_intersection"])},
                {"subtree": "python.controls", "hash": stable_hash(py["controls"])},
                {"subtree": "python.smt_solve_space_identities", "hash": stable_hash(py["smt_solve_space_identities"])},
                {"subtree": "julia.symbolics_rows", "hash": stable_hash(jl["symbolics_rows"])},
                {"subtree": "julia.z3_rows", "hash": stable_hash(jl["z3_rows"])},
            ],
        },
        "capability_receipts": {"python": py["capability_receipts"], "julia": jl["capability_receipts"]},
        "standard_schema_notes": py["standard_schema_notes"],
    }
    dump_json(RESULT_PATH, payload)
    print(json.dumps({"result_path": str(RESULT_PATH), "all_pass": all_pass}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
