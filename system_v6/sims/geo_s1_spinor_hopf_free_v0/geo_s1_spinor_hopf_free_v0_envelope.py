#!/usr/bin/env python3
"""Three-engine envelope for geo_s1_spinor_hopf_free_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_spinor_hopf_free_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
PROGRAM_RECEIPT = "system_v6/receipts/geometry_sim_program_canonical_20260610.md"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
PIN_SPEC = (
    "geo_s1_spinor_hopf_free_v0|S1-free|chart:z1=cos(eta)exp(i(phi+chi)),"
    "z2=sin(eta)exp(i(phi-chi))|hopf=(2Re z1conj(z2),2Im z1conj(z2),"
    "|z1|^2-|z2|^2)|metric=deta^2+dphi^2+dchi^2+2cos(2eta)dphi dchi|"
    "bloch_basis=(sigma_x,-sigma_y,sigma_z)|"
    "seed_ledger=jax.random.PRNGKey[11000:n1000,20000:n10000,110000:n100000,"
    "55/56/57:clustered_control_n10000];"
    "torch.Generator.manual_seed[91000:n1000,100000:n10000,190000:n100000]|"
    "rerun=SIM_PY geo_s1_spinor_hopf_free_v0_{jax,julia,pytorch,envelope}|"
    "classification=scratch_diagnostic"
)

SEED_LEDGER = {
    "status": "declared_recompute_metadata_only",
    "rng_api": ["jax.random.PRNGKey", "torch.Generator.manual_seed"],
    "seeds": [
        {"engine": "jax", "seed": 11000, "use": "dense_sample_N1000", "sample_count": 1000},
        {"engine": "jax", "seed": 20000, "use": "dense_sample_N10000", "sample_count": 10000},
        {"engine": "jax", "seed": 110000, "use": "dense_sample_N100000", "sample_count": 100000},
        {"engine": "jax", "seed": 55, "use": "non_haar_clustered_eta_control", "sample_count": 10000},
        {"engine": "jax", "seed": 56, "use": "non_haar_clustered_phi_control", "sample_count": 10000},
        {"engine": "jax", "seed": 57, "use": "non_haar_clustered_chi_control", "sample_count": 10000},
        {"engine": "pytorch", "seed": 91000, "use": "independent_sample_N1000", "sample_count": 1000},
        {"engine": "pytorch", "seed": 100000, "use": "independent_sample_N10000", "sample_count": 10000},
        {"engine": "pytorch", "seed": 190000, "use": "independent_sample_N100000", "sample_count": 100000},
    ],
    "deterministic_legs": ["julia_grid_and_symbolic_rows"],
    "rerun_command": "SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3; $SIM_PY system_v6/sims/geo_s1_spinor_hopf_free_v0/geo_s1_spinor_hopf_free_v0_jax.py && JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/geo_s1_spinor_hopf_free_v0/geo_s1_spinor_hopf_free_v0_julia.jl && $SIM_PY system_v6/sims/geo_s1_spinor_hopf_free_v0/geo_s1_spinor_hopf_free_v0_pytorch.py && $SIM_PY system_v6/sims/geo_s1_spinor_hopf_free_v0/geo_s1_spinor_hopf_free_v0_envelope.py",
}

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from independently regenerated leg receipts",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source hashing and pin equality checks",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic result path binding",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload.get("all_pass") is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path.relative_to(ROOT)),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "pin_sha256": payload["pin_sha256"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "shared_scalars": payload.get("shared_scalars", {}),
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def require_gate(condition: bool, name: str, details: Any) -> dict[str, Any]:
    return {"pass": bool(condition), "details": details, "gate": name}


def build_result() -> dict[str, Any]:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    julia = payloads["julia"]
    jax = payloads["jax"]
    pytorch = payloads["pytorch"]
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    ceilings_exact = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is PROMOTION_ALLOWED
        and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
        for payload in payloads.values()
    )
    g_names = [f"G{i}" for i in range(1, 8)]
    jax_receipts = jax["G_receipts"]
    receipt_keys = {
        "G1": "G1_spinors",
        "G2": "G2_s3_metric_volume_geodesics",
        "G3": "G3_su2_structure",
        "G4": "G4_hopf_map",
        "G5": "G5_fibers",
        "G6": "G6_density_quotient",
        "G7": "G7_s2_base",
    }
    g_coverage = {
        name: {
            "jax_receipt": receipt_keys[name],
            "jax_pass": jax_receipts[receipt_keys[name]]["pass"] is True,
            "julia_receipt_present": any(key.startswith(name) for key in julia["G_receipts"]),
            "pytorch_receipt_present": (
                name == "G5" and "G5_fibers_and_linking" in pytorch["G_receipts"]
            )
            or (name == "G7" and "G7_commuting_square_torch_native" in pytorch["G_receipts"]),
        }
        for name in g_names
    }
    p1 = jax["proofs"]["P1_hopf_unit_sphere"]
    p2 = jax["proofs"]["P2_commuting_square"]
    linking = pytorch["G_receipts"]["G5_fibers_and_linking"]
    keystone = jax["G_receipts"]["G6_density_quotient"]
    gates = {
        "legs_exit_0_by_receipt": require_gate(
            all(payload["all_pass"] is True for payload in payloads.values()),
            "legs_exit_0_by_receipt",
            {engine: payload["all_pass"] for engine, payload in payloads.items()},
        ),
        "pin_identical": require_gate(len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC), "pin_identical", sorted(pin_hashes)),
        "ceiling_exact": require_gate(ceilings_exact, "ceiling_exact", {engine: payload["classification"] for engine, payload in payloads.items()}),
        "all_g_items_have_receipts": require_gate(
            all(row["jax_pass"] for row in g_coverage.values()),
            "all_g_items_have_receipts",
            g_coverage,
        ),
        "linking_number_gauss_integral": require_gate(
            linking["pass"] is True and abs(linking["final_linking_number"] - 1.0) < 1.0e-3,
            "linking_number_gauss_integral",
            linking["linking_convergence"],
        ),
        "keystone_identity_pointwise": require_gate(
            keystone["pass"] is True and keystone["bloch_vector_equals_hopf_max_deviation_N100000"] <= 1.0e-8,
            "keystone_identity_pointwise",
            keystone,
        ),
        "proofs_flip": require_gate(
            p1["pass"] is True
            and p2["pass"] is True
            and p1["z3_verdict"] == "unsat"
            and p1["cvc5_verdict"] == "unsat"
            and p1["scrambled_control_z3_verdict"] == "sat"
            and p1["scrambled_control_cvc5_verdict"] == "sat"
            and p2["z3_verdict"] == "unsat"
            and p2["cvc5_verdict"] == "unsat"
            and p2["wrong_rotation_control_z3_verdict"] == "sat"
            and p2["wrong_rotation_control_cvc5_verdict"] == "sat",
            "proofs_flip",
            {"P1": p1, "P2": p2},
        ),
    }
    all_pass = all(gate["pass"] for gate in gates.values())
    engine_values = {
        "julia": float(julia["shared_scalars"]["hopf_unit_sphere_max_deviation"]),
        "jax": float(jax["shared_scalars"]["hopf_unit_sphere_max_deviation"]),
        "pytorch": float(pytorch["shared_scalars"]["hopf_unit_sphere_max_deviation"]),
    }
    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Stage-1 free-mode geometry: normalized spinors, S3 metric/volume, Hopf map, fibers/linking, density quotient, and S2 base",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "program_receipt": PROGRAM_RECEIPT,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "seed_ledger": SEED_LEDGER,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": julia.get("julia_project"),
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "S1_free_geometry_Z3jl_raw_value_check",
            "proof_pass": julia["proofs"]["julia_z3_hopf_unit_sphere"]["pass"],
            "table_version": None,
            "bracket_convention": "not_applicable_pure_S1_geometry",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "canon_geometry_and_Z3jl_raw_value_check"},
            "jax": {"packages": jax["packages_used"], "role": "dense batched Haar/convergence sweeps plus z3/cvc5 proofs"},
            "pytorch": {"packages": pytorch["packages_used"], "role": "independent Gauss linking integral and torch.func commuting-square check"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": collect_claim_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "P1_hopf_unit_sphere": p1["z3_verdict"],
                    "P2_commuting_square": p2["z3_verdict"],
                    "P1_scrambled_control": p1["scrambled_control_z3_verdict"],
                    "P2_wrong_rotation_control": p2["wrong_rotation_control_z3_verdict"],
                },
                "raw_value_binding": {
                    "P1_raw_scaled_min_max": p1["raw_scaled_min_max"],
                    "P2_raw_scaled_values": p2["raw_scaled_values"],
                },
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "P1_hopf_unit_sphere": p1["cvc5_verdict"],
                    "P2_commuting_square": p2["cvc5_verdict"],
                    "P1_scrambled_control": p1["scrambled_control_cvc5_verdict"],
                    "P2_wrong_rotation_control": p2["wrong_rotation_control_cvc5_verdict"],
                },
                "raw_value_binding": {
                    "P1_raw_scaled_min_max": p1["raw_scaled_min_max"],
                    "P2_raw_scaled_values": p2["raw_scaled_values"],
                },
            },
            "julia_z3": {
                "ran": True,
                "verdict": julia["proofs"]["julia_z3_hopf_unit_sphere"]["verdict"],
                "load_bearing": True,
                "proof": julia["proofs"]["julia_z3_hopf_unit_sphere"],
            },
        },
        "G_receipts": {
            "julia": julia["G_receipts"],
            "jax": jax["G_receipts"],
            "pytorch": pytorch["G_receipts"],
        },
        "convergence_rows": {
            "julia": julia["convergence_rows"],
            "jax": jax["convergence_rows"],
            "pytorch": pytorch["convergence_rows"],
        },
        "convergence_ladder_rows": {
            "julia": julia.get("convergence_ladder_rows", julia["convergence_rows"]),
            "jax": jax.get("convergence_ladder_rows", jax["convergence_rows"]),
            "pytorch": pytorch.get("convergence_ladder_rows", pytorch["convergence_rows"]),
        },
        "exact_by_algebra_rows": {
            "julia": julia.get("exact_by_algebra_rows", {}),
            "jax": jax.get("exact_by_algebra_rows", {}),
            "pytorch": pytorch.get("exact_by_algebra_rows", {}),
        },
        "controls": {
            "julia": julia["controls"],
            "jax": jax["controls"],
            "pytorch": pytorch["controls"],
        },
        "build_gates": gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": max(engine_values.values()),
            "meaning": "max exact-invariant residual by engine, not a promotion metric",
        },
        "tripwires": {
            "s3_vs_fubini_study_distance_separated": jax["tripwires"]["s3_vs_fubini_study_distance_separated"],
            "no_bloch_ball_content": True,
            "no_torus_content": True,
            "no_manifold_axis_physics_claims": True,
        },
    }
    return payload


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT_PATH), "engine": "envelope"}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
