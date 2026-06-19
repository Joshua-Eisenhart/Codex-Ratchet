#!/usr/bin/env python3
"""Envelope for foundation_nested_hopf_weyl_signed_cut_ratchet."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


PIN_SPEC = """object_id=foundation_nested_hopf_weyl_signed_cut_ratchet
rung_count=3
eta_shells_rad=[eta_1=1.17,eta_2=0.86,eta_3=0.53] with eta_1 > eta_2 > eta_3 nested Hopf tori in S^3
stacking_order=Stack_r = Phi_r after Phi_{r-1} after ... after Phi_1; adjacent order test compares Phi_r after Phi_{r+1} vs Phi_{r+1} after Phi_r on rho_probe=rho_2
constraint_filters_left_sheet=K_1=[[1,0],[0,-1]], K_2=[[1,1],[1,-1]], K_3=[[1,1],[0,1]], Phi_r(rho)=normalize((K_r kron I_R) rho (K_r kron I_R)^adjoint)
rho_family=rho_r=|psi_r><psi_r|, |psi_r>=cos(theta_r)|L0 R0>+sin(theta_r)|L1 R1>, theta_r=0.70*(r-1)/2 for r=1,2,3
separable_control=rho_sep_r=diag(cos(theta_r)^2,sin(theta_r)^2)_L kron diag(cos(theta_r)^2,sin(theta_r)^2)_R
cut=A|B is Weyl-L sheet vs Weyl-R sheet
entropy_log_base=e
probe_sets=M_1=[Z_L Z_R]; M_2=M_1+[X_L X_R]; M_3=M_2+[Z_L,Z_R,Y_L Y_R]
claim_ceiling=scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false; feeds Xi/Axis-0 bridge problem but does not close bridge, Axis0, manifold, or M(C)
"""

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "foundation_nested_hopf_weyl_signed_cut_ratchet"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_nested_hopf_weyl_signed_cut_ratchet_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_nested_hopf_weyl_signed_cut_ratchet_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_nested_hopf_weyl_signed_cut_ratchet_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_nested_hopf_weyl_signed_cut_ratchet_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOL = 1.0e-8

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from independent leg result JSONs; not a math claim path",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source and pin hashing",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive"}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload.get("all_pass") is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "pin_sha256": payload["pin_sha256"],
        "values": payload["shared_scalars"],
    }


def compare_shared_scalars(julia: dict[str, Any], jax: dict[str, Any], pytorch: dict[str, Any]) -> dict[str, Any]:
    key_sets = {
        "julia": set(julia["shared_scalars"].keys()),
        "jax": set(jax["shared_scalars"].keys()),
        "pytorch": set(pytorch["shared_scalars"].keys()),
    }
    common = sorted(set.intersection(*key_sets.values()))
    equal_sets = key_sets["julia"] == key_sets["jax"] == key_sets["pytorch"]
    rows = []
    max_diff = 0.0
    max_key = None
    for key in common:
        values = {
            "julia": float(julia["shared_scalars"][key]),
            "jax": float(jax["shared_scalars"][key]),
            "pytorch": float(pytorch["shared_scalars"][key]),
        }
        diff = max(abs(values["julia"] - values["jax"]), abs(values["julia"] - values["pytorch"]), abs(values["jax"] - values["pytorch"]))
        if diff > max_diff:
            max_diff = diff
            max_key = key
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
    missing = {engine: sorted(set.union(*key_sets.values()) - keys) for engine, keys in key_sets.items()}
    return {
        "same_named_observable_sets": equal_sets,
        "common_observable_count": len(common),
        "missing_by_engine": missing,
        "rows": rows,
        "max_divergence": max_diff,
        "max_divergence_key": max_key,
        "within_tolerance": equal_sets and max_diff <= TOL,
    }


def require_leg_controls(payload: dict[str, Any]) -> bool:
    controls = payload.get("controls", {})
    return all(value for value in controls.values() if isinstance(value, bool))


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    comparison = compare_shared_scalars(julia, jax, pytorch)
    pin_hash = sha256_text(PIN_SPEC)
    pin_equality = {
        "envelope_pin_sha256": pin_hash,
        "julia_pin_sha256": julia["pin_sha256"],
        "jax_pin_sha256": jax["pin_sha256"],
        "pytorch_pin_sha256": pytorch["pin_sha256"],
        "pin_sha256_equal": pin_hash == julia["pin_sha256"] == jax["pin_sha256"] == pytorch["pin_sha256"],
        "pin_spec_literal_equal": PIN_SPEC == julia["pin_spec"] == jax["pin_spec"] == pytorch["pin_spec"],
        "rho_spec_match": PIN_SPEC == julia["pin_spec"] == jax["pin_spec"] == pytorch["pin_spec"],
    }
    z3_verdict = jax["crossover_proofs"]["z3"]["verdict"]
    cvc5_verdict = jax["crossover_proofs"]["cvc5"]["verdict"]
    z3_commuting = jax["crossover_proofs"]["z3"]["commuting_control_verdict"]
    cvc5_commuting = jax["crossover_proofs"]["cvc5"]["commuting_control_verdict"]
    julia_z3 = julia["crossover_proofs"]["julia_z3"]
    controls = {
        "legs_all_pass": julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"],
        "leg_controls_all_pass": require_leg_controls(julia) and require_leg_controls(jax) and require_leg_controls(pytorch),
        "pin_spec_match": pin_equality["pin_sha256_equal"] and pin_equality["pin_spec_literal_equal"],
        "same_named_observables_only": comparison["same_named_observable_sets"],
        "shared_scalars_within_tolerance": comparison["within_tolerance"],
        "z3_cvc5_channel_level_noncommuting_unsat": z3_verdict == cvc5_verdict == "unsat",
        "z3_cvc5_channel_level_commuting_control_sat": z3_commuting == cvc5_commuting == "sat",
        "z3_cvc5_filter_level_noncommuting_unsat": jax["crossover_proofs"]["z3"]["filter_level"]["verdict"]
        == jax["crossover_proofs"]["cvc5"]["filter_level"]["verdict"]
        == "unsat",
        "z3_cvc5_filter_level_commuting_control_sat": jax["crossover_proofs"]["z3"]["commuting_control_filter_level"]["verdict"]
        == jax["crossover_proofs"]["cvc5"]["commuting_control_filter_level"]["verdict"]
        == "sat",
        "julia_z3_channel_level_noncommuting_unsat": julia_z3["verdict"] == "unsat",
        "julia_z3_channel_level_commuting_control_sat": julia_z3["commuting_control_verdict"] == "sat",
        "julia_z3_filter_level_noncommuting_unsat": julia_z3["filter_level"]["verdict"] == "unsat",
        "julia_z3_filter_level_commuting_control_sat": julia_z3["commuting_control_filter_level"]["verdict"] == "sat",
        "separable_control_nonnegative": all(
            float(julia["shared_scalars"][key]) >= -TOL
            and float(jax["shared_scalars"][key]) >= -TOL
            and float(pytorch["shared_scalars"][key]) >= -TOL
            for key in ("separable_conditional_entropy_r1", "separable_conditional_entropy_r2", "separable_conditional_entropy_r3")
        ),
        "commuting_control_zero_order_gap": all(
            abs(float(julia["shared_scalars"][key])) <= TOL
            and abs(float(jax["shared_scalars"][key])) <= TOL
            and abs(float(pytorch["shared_scalars"][key])) <= TOL
            for key in ("commuting_order_gap_r1_r2", "commuting_order_gap_r2_r3")
        ),
        "boundary_rung1_no_crossing": all(
            float(payload["shared_scalars"]["boundary_rung1_conditional_entropy"]) >= -TOL
            for payload in (julia, jax, pytorch)
        ),
    }
    all_pass = bool(
        all(controls.values())
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "reads_peer_result": False,
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "object_id": OBJECT_ID,
        "rung_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": pin_hash,
        "pin_equality": pin_equality,
        "all_pass": all_pass,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "controls": controls,
        "positive": {
            "carrier_conditional_entropy_by_rung": {
                "julia": [julia["shared_scalars"][f"conditional_entropy_r{r}"] for r in (1, 2, 3)],
                "jax": [jax["shared_scalars"][f"conditional_entropy_r{r}"] for r in (1, 2, 3)],
                "pytorch": [pytorch["shared_scalars"][f"conditional_entropy_r{r}"] for r in (1, 2, 3)],
            },
            "signed_cut_Ic_by_rung": {
                "julia": [julia["shared_scalars"][f"signed_cut_Ic_r{r}"] for r in (1, 2, 3)],
                "jax": [jax["shared_scalars"][f"signed_cut_Ic_r{r}"] for r in (1, 2, 3)],
                "pytorch": [pytorch["shared_scalars"][f"signed_cut_Ic_r{r}"] for r in (1, 2, 3)],
            },
            "carrier_entropy_components_by_rung": {
                "julia": [
                    {"S_AB": julia["shared_scalars"][f"carrier_S_AB_r{r}"], "S_B": julia["shared_scalars"][f"carrier_S_B_r{r}"]}
                    for r in (1, 2, 3)
                ],
                "jax": [
                    {"S_AB": jax["shared_scalars"][f"carrier_S_AB_r{r}"], "S_B": jax["shared_scalars"][f"carrier_S_B_r{r}"]}
                    for r in (1, 2, 3)
                ],
                "pytorch": [
                    {
                        "S_AB": pytorch["shared_scalars"][f"carrier_S_AB_r{r}"],
                        "S_B": pytorch["shared_scalars"][f"carrier_S_B_r{r}"],
                    }
                    for r in (1, 2, 3)
                ],
            },
            "quotient_class_counts": {
                "julia": [julia["shared_scalars"][f"quotient_class_count_M{r}"] for r in (1, 2, 3)],
                "jax": [jax["shared_scalars"][f"quotient_class_count_M{r}"] for r in (1, 2, 3)],
                "pytorch": [pytorch["shared_scalars"][f"quotient_class_count_M{r}"] for r in (1, 2, 3)],
            },
        },
        "negative": {
            "separable_conditional_entropy_by_rung": {
                "julia": [julia["shared_scalars"][f"separable_conditional_entropy_r{r}"] for r in (1, 2, 3)],
                "jax": [jax["shared_scalars"][f"separable_conditional_entropy_r{r}"] for r in (1, 2, 3)],
                "pytorch": [pytorch["shared_scalars"][f"separable_conditional_entropy_r{r}"] for r in (1, 2, 3)],
            },
            "separable_control_entropy_components_by_rung": {
                "julia": [
                    {
                        "S_AB": julia["shared_scalars"][f"separable_control_S_AB_r{r}"],
                        "S_B": julia["shared_scalars"][f"separable_control_S_B_r{r}"],
                    }
                    for r in (1, 2, 3)
                ],
                "jax": [
                    {
                        "S_AB": jax["shared_scalars"][f"separable_control_S_AB_r{r}"],
                        "S_B": jax["shared_scalars"][f"separable_control_S_B_r{r}"],
                    }
                    for r in (1, 2, 3)
                ],
                "pytorch": [
                    {
                        "S_AB": pytorch["shared_scalars"][f"separable_control_S_AB_r{r}"],
                        "S_B": pytorch["shared_scalars"][f"separable_control_S_B_r{r}"],
                    }
                    for r in (1, 2, 3)
                ],
            },
            "commuting_order_gaps": {
                "julia": [julia["shared_scalars"]["commuting_order_gap_r1_r2"], julia["shared_scalars"]["commuting_order_gap_r2_r3"]],
                "jax": [jax["shared_scalars"]["commuting_order_gap_r1_r2"], jax["shared_scalars"]["commuting_order_gap_r2_r3"]],
                "pytorch": [pytorch["shared_scalars"]["commuting_order_gap_r1_r2"], pytorch["shared_scalars"]["commuting_order_gap_r2_r3"]],
            },
        },
        "boundary": {
            "rung_count_1": {
                "julia": julia["shared_scalars"]["boundary_rung1_conditional_entropy"],
                "jax": jax["shared_scalars"]["boundary_rung1_conditional_entropy"],
                "pytorch": pytorch["shared_scalars"]["boundary_rung1_conditional_entropy"],
                "crosses_negative": False,
            }
        },
        "order_gaps": {
            "carrier": {
                "julia": [julia["shared_scalars"]["order_gap_r1_r2"], julia["shared_scalars"]["order_gap_r2_r3"]],
                "jax": [jax["shared_scalars"]["order_gap_r1_r2"], jax["shared_scalars"]["order_gap_r2_r3"]],
                "pytorch": [pytorch["shared_scalars"]["order_gap_r1_r2"], pytorch["shared_scalars"]["order_gap_r2_r3"]],
            },
            "commuting_control": {
                "julia": [julia["shared_scalars"]["commuting_order_gap_r1_r2"], julia["shared_scalars"]["commuting_order_gap_r2_r3"]],
                "jax": [jax["shared_scalars"]["commuting_order_gap_r1_r2"], jax["shared_scalars"]["commuting_order_gap_r2_r3"]],
                "pytorch": [pytorch["shared_scalars"]["commuting_order_gap_r1_r2"], pytorch["shared_scalars"]["commuting_order_gap_r2_r3"]],
            },
        },
        "smt": {
            "jax": jax["smt"],
            "julia": julia["smt"],
            "pytorch": "not_scoped_for_smt",
            "derive_in_solver": "JAX z3/cvc5 and Julia Z3 keep the 2x2 filter_level checks and add unnormalized 4x4 channel_level checks over bound rho_probe entries; no precomputed order-gap scalar is asserted.",
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "commuting_control_verdict": z3_commuting,
                "filter_level": jax["crossover_proofs"]["z3"]["filter_level"],
                "channel_level": jax["crossover_proofs"]["z3"]["channel_level"],
                "commuting_control_filter_level": jax["crossover_proofs"]["z3"]["commuting_control_filter_level"],
                "commuting_control_channel_level": jax["crossover_proofs"]["z3"]["commuting_control_channel_level"],
                "claim": "For bound rung-2 adjacent filters and rho_probe entries, forcing unnormalized channel equality is UNSAT; the commuting-control channel family is SAT.",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "commuting_control_verdict": cvc5_commuting,
                "filter_level": jax["crossover_proofs"]["cvc5"]["filter_level"],
                "channel_level": jax["crossover_proofs"]["cvc5"]["channel_level"],
                "commuting_control_filter_level": jax["crossover_proofs"]["cvc5"]["commuting_control_filter_level"],
                "commuting_control_channel_level": jax["crossover_proofs"]["cvc5"]["commuting_control_channel_level"],
                "claim": "Independent cvc5 check of the same filter-level and unnormalized channel-level UNSAT/SAT flip.",
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3["verdict"],
                "commuting_control_verdict": julia_z3["commuting_control_verdict"],
                "filter_level": julia_z3["filter_level"],
                "channel_level": julia_z3["channel_level"],
                "commuting_control_filter_level": julia_z3["commuting_control_filter_level"],
                "commuting_control_channel_level": julia_z3["commuting_control_channel_level"],
                "claim": julia_z3["claim"],
            },
        },
        "shared_observable_comparison": comparison,
        "claim_path_tools": ["QuantumOptics", "Z3", "z3", "cvc5", "torch.func"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": julia["shared_scalars"],
                "jax": jax["shared_scalars"],
                "pytorch": pytorch["shared_scalars"],
            },
            "max_divergence": comparison["max_divergence"],
            "max_divergence_key": comparison["max_divergence_key"],
            "comparison_policy": "Only same-named shared_scalars are compared; unequal key sets fail the envelope.",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "classification=scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false; feeds the Xi/Axis-0 bridge problem but does not close bridge, Axis0, manifold, or M(C).",
        "NOT_GAINED": [
            "No canonical admission.",
            "No formal proof admission.",
            "No bridge, Axis0, manifold, M(C), gravity, or physics closure claim.",
        ],
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_NESTED_HOPF_WEYL_SIGNED_CUT_RATCHET_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"max_divergence={result['divergence']['max_divergence']} "
        f"max_key={result['divergence']['max_divergence_key']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
