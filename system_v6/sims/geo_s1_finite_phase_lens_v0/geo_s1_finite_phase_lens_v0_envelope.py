#!/usr/bin/env python3
"""Three-engine envelope for geo_s1_finite_phase_lens_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_finite_phase_lens_v0"
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
PIN_SPEC = (
    "geo_s1_finite_phase_lens_v0|stage1_quotient|S3/Z_N=L(N,1)|"
    "N=(1,2,3,4,8,16,64)|rho=psi psi^dagger|phase_residue=exp(i N theta)|"
    "seed_ledger=jax.random.PRNGKey[60217:haar_base_n128,60218:f01_base_n7,"
    "70001/70002/70003/70004/70008/70016/70064:mc_volume_n20000_per_N];"
    "torch.Generator.manual_seed[70217:pytorch_base_n96]|"
    "rerun=SIM_PY geo_s1_finite_phase_lens_v0_{jax,julia,pytorch,envelope}|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

SEED_LEDGER = {
    "status": "declared_recompute_metadata_only",
    "rng_api": ["jax.random.PRNGKey", "torch.Generator.manual_seed"],
    "seeds": [
        {"engine": "jax", "seed": 60217, "use": "haar_base_orbit_samples", "sample_count": 128},
        {"engine": "jax", "seed": 60218, "use": "f01_probe_samples", "sample_count": 7},
        {
            "engine": "jax",
            "seeds": [70001, 70002, 70003, 70004, 70008, 70016, 70064],
            "use": "mc_volume_comparison_by_N",
            "sample_count_per_seed": 20000,
        },
        {"engine": "pytorch", "seed": 70217, "use": "independent_phase_orbit_base", "sample_count": 96},
    ],
    "deterministic_legs": ["julia_integer_quotient_rows"],
    "rerun_command": "SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3; $SIM_PY system_v6/sims/geo_s1_finite_phase_lens_v0/geo_s1_finite_phase_lens_v0_jax.py && JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/geo_s1_finite_phase_lens_v0/geo_s1_finite_phase_lens_v0_julia.jl && $SIM_PY system_v6/sims/geo_s1_finite_phase_lens_v0/geo_s1_finite_phase_lens_v0_pytorch.py && $SIM_PY system_v6/sims/geo_s1_finite_phase_lens_v0/geo_s1_finite_phase_lens_v0_envelope.py",
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


def all_receipts_pass(payload: dict[str, Any], names: list[str]) -> bool:
    receipts = payload["L_receipts"]
    return all(receipts[name]["pass"] is True for name in names)


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
    jax_receipts = jax["L_receipts"]
    l_names = [
        "L1_quotient_computed",
        "L2_volume_tower",
        "L3_fundamental_group_order",
        "L4_factoring_chain",
        "L5_F01_probe_reading",
        "L6_convergence_to_density_quotient",
    ]
    p_names = [
        "L1_quotient_computed",
        "L4_factoring_chain",
        "L5_F01_probe_reading",
        "L6_convergence_to_density_quotient",
    ]
    known_values = {
        str(row["N"]): {
            "volume_2pi2_over_N": row["known_value_2pi2_over_N"],
            "fundamental_group_order": next(g["computed_fundamental_group_order"] for g in jax_receipts["L3_fundamental_group_order"]["rows"] if g["N"] == row["N"]),
        }
        for row in jax_receipts["L2_volume_tower"]["rows"]
    }
    proof_orbit = jax["proofs"]["orbit_count_differs_from_sample_count_over_N"]
    proof_nonfree = jax["proofs"]["non_free_control_fixed_point_exists"]
    proof_commute = jax["proofs"]["commuting_chain_nonzero_beyond_tolerance"]
    gates = {
        "legs_exit_0_by_receipt": require_gate(
            all(payload["all_pass"] is True for payload in payloads.values()),
            "legs_exit_0_by_receipt",
            {engine: payload["all_pass"] for engine, payload in payloads.items()},
        ),
        "pin_identical": require_gate(len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC), "pin_identical", sorted(pin_hashes)),
        "ceiling_exact": require_gate(ceilings_exact, "ceiling_exact", {engine: payload["classification"] for engine, payload in payloads.items()}),
        "L1_L6_jax_receipts_pass": require_gate(all_receipts_pass(jax, l_names), "L1_L6_jax_receipts_pass", {name: jax_receipts[name]["pass"] for name in l_names}),
        "julia_core_receipts_pass": require_gate(
            all_receipts_pass(julia, ["L1_quotient_computed", "L2_volume_tower", "L3_fundamental_group_order", "L5_F01_probe_reading", "L6_convergence_to_density_quotient"]),
            "julia_core_receipts_pass",
            julia["L_receipts"],
        ),
        "pytorch_independent_receipts_pass": require_gate(all_receipts_pass(pytorch, p_names), "pytorch_independent_receipts_pass", pytorch["L_receipts"]),
        "known_values_exact": require_gate(
            all(row["abs_error"] == 0.0 for row in jax_receipts["L2_volume_tower"]["rows"])
            and all(row["computed_fundamental_group_order"] == row["known_order"] for row in jax_receipts["L3_fundamental_group_order"]["rows"]),
            "known_values_exact",
            known_values,
        ),
        "controls_fired": require_gate(
            jax["controls_fired"] is True
            and jax["controls"]["non_free_action_control"]["caught_by_freeness_check"] is True
            and all(row["control_fired"] for row in jax["controls"]["probe_resolution_mismatch_control"]),
            "controls_fired",
            jax["controls"],
        ),
        "proofs_flip": require_gate(
            proof_orbit["z3_verdict"] == "unsat"
            and proof_orbit["cvc5_verdict"] == "unsat"
            and proof_nonfree["z3_verdict"] == "sat"
            and proof_nonfree["cvc5_verdict"] == "sat"
            and proof_commute["z3_verdict"] == "unsat"
            and proof_commute["cvc5_verdict"] == "unsat",
            "proofs_flip",
            {"orbit": proof_orbit, "nonfree": proof_nonfree, "commuting": proof_commute},
        ),
    }
    engine_values = {
        "julia": float(julia["shared_scalars"]["max_convergence_distance_N64"]),
        "jax": float(jax["shared_scalars"]["max_convergence_distance_N64"]),
        "pytorch": float(pytorch["shared_scalars"]["max_convergence_distance_N64"]),
    }
    all_pass = all(gate["pass"] for gate in gates.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Stage-1 finite-phase quotient tower: S3/Z_N lens spaces L(N,1) as F01 finite-resolution alternatives to full S1 phase erasure",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
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
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "lens_tower_ZN_orbit_count_Z3_raw_value_check",
            "proof_pass": julia["proofs"]["orbit_count_differs_from_sample_count_over_N"]["z3_verdict"] == "unsat",
            "table_version": None,
            "bracket_convention": "not_applicable_stage1_quotient_geometry",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": julia["packages_used"], "role": "canon quotient count and Julia Z3 raw-value check"},
            "jax": {"packages": jax["packages_used"], "role": "Haar orbit, density-chain, F01 ladder, z3/cvc5 proofs"},
            "pytorch": {"packages": pytorch["packages_used"], "role": "independent torch.func quotient and density-chain check"},
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
                    "orbit_count_differs": proof_orbit["z3_verdict"],
                    "commuting_chain_nonzero": proof_commute["z3_verdict"],
                    "non_free_control": proof_nonfree["z3_verdict"],
                },
                "raw_value_binding": {
                    "orbit_rows": proof_orbit["raw_rows"],
                    "commuting_scaled_deviations": proof_commute["raw_scaled_deviations_1e12"],
                },
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    "orbit_count_differs": proof_orbit["cvc5_verdict"],
                    "commuting_chain_nonzero": proof_commute["cvc5_verdict"],
                    "non_free_control": proof_nonfree["cvc5_verdict"],
                },
                "raw_value_binding": {
                    "orbit_rows": proof_orbit["raw_rows"],
                    "commuting_scaled_deviations": proof_commute["raw_scaled_deviations_1e12"],
                },
            },
            "julia_z3": {
                "ran": True,
                "verdict": julia["proofs"]["orbit_count_differs_from_sample_count_over_N"]["z3_verdict"],
                "load_bearing": True,
                "proof": julia["proofs"]["orbit_count_differs_from_sample_count_over_N"],
            },
        },
        "L_receipts": {
            "julia": julia["L_receipts"],
            "jax": jax["L_receipts"],
            "pytorch": pytorch["L_receipts"],
        },
        "controls": {
            "julia": julia["controls"],
            "jax": jax["controls"],
            "pytorch": pytorch["controls"],
        },
        "known_values": known_values,
        "build_gates": gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": max(abs(value - engine_values["julia"]) for value in engine_values.values()),
            "meaning": "max difference in N=64 normalized quotient-to-density residual across engines, not a promotion metric",
        },
        "claim_boundary": {
            "ceiling": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "not_claimed": "the lens tower does not replace the Hopf quotient; it is a finite-resolution alternative family under test",
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT_PATH), "engine": "envelope"}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
