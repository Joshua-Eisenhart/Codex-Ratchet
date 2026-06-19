#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "foundation_r2_admissibility_mc_three_engine_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r2_admissibility_mc_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r2_admissibility_mc_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r2_admissibility_mc_julia_leg_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r2_admissibility_mc_jax_leg_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r2_admissibility_mc_pytorch_leg_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path, packages_used: list[str], load_bearing: list[str], values: dict[str, Any]) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "values": values,
    }


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    full_classes = julia["quotient_summary"]["full_M_class_count"]
    dropped_classes = julia["quotient_summary"]["drop_P_xplus_class_count"]
    flip = jax["negative_control_flip"]
    julia_values = {
        "admitted_count": len(julia["admitted_names"]),
        "excluded_count": len(julia["excluded"]),
        "full_M_class_count": full_classes,
        "drop_P_xplus_class_count": dropped_classes,
        "convex_mix_min_eigenvalue": julia["convex_closure"]["min_eigenvalue"],
    }
    jax_values = {
        "excluded_unsat_count": sum(1 for name, row in jax["proofs"].items() if name.startswith("excluded_") and row["z3_status_under_C"] == "unsat" and row["cvc5_status_under_C"] == "unsat"),
        "negative_control_before": flip["z3_before"],
        "negative_control_after_drop_psd": flip["z3_after_drop_psd"],
        "z3_cvc5_agree_on_flip": flip["z3_after_drop_psd"] == flip["cvc5_after_drop_psd"],
    }
    pytorch_values = {
        "margin_inside_t_0p49": pytorch["rows"][0]["margin"],
        "margin_boundary_t_0p5": pytorch["rows"][1]["margin"],
        "margin_outside_t_0p51": pytorch["rows"][2]["margin"],
        "jacrev_boundary_normal_t_0p49": pytorch["rows"][0]["jacrev_dmargin_dt"],
        "genuine_independent_check": pytorch["genuine_independent_check"],
    }
    all_pass = (
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and flip["z3_before"] == flip["cvc5_before"] == "unsat"
        and flip["z3_after_drop_psd"] == flip["cvc5_after_drop_psd"] == "sat"
        and julia["quotient_summary"]["drop_probe_coarsens_quotient"] is True
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "classification": classification,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Scratch foundation_r2_admissibility_mc three-engine rung only: finite M/C admissibility manifold, quotient by finite probe indistinguishability, excluded-candidate UNSAT receipts, convex closure, and negative control flips. No promotion or formal admission.",
        "M_probe_family": julia["M_probe_family"],
        "C_constraints": julia["C_constraints"],
        "S_quotient_under_M": julia["quotient_summary"],
        "admitted_manifold_summary": {
            "admitted_names": julia["admitted_names"],
            "excluded": julia["excluded"],
            "convex_closure": julia["convex_closure"],
            "convex_closed_on_tested_witnesses": julia["convex_closure"]["admitted"],
        },
        "negative_control_flip_result": {
            "drop_P_xplus_coarsens_quotient": julia["negative_controls"]["drop_P_xplus_coarsens_quotient"],
            "drop_P_xplus_class_count_change": [full_classes, dropped_classes],
            "drop_PSD_candidate": flip["candidate"],
            "drop_PSD_z3": [flip["z3_before"], flip["z3_after_drop_psd"]],
            "drop_PSD_cvc5": [flip["cvc5_before"], flip["cvc5_after_drop_psd"]],
        },
        "all_pass": all_pass,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT, ["QuantumOptics", "LinearAlgebra", "JSON", "SHA"], ["QuantumOptics"], julia_values),
            "jax": engine_record(jax, JAX_RESULT, ["jax", "jax.numpy", "z3", "cvc5"], ["z3", "cvc5"], jax_values),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT, ["torch", "torch.func"], ["torch.func"], pytorch_values),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax["crossover_summary"]["z3_verdict"],
                "claim": jax["crossover_summary"]["claim"],
                "negative_control_verdict": f"{flip['z3_before']}->{flip['z3_after_drop_psd']} when PSD is dropped",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax["crossover_summary"]["cvc5_verdict"],
                "claim": jax["crossover_summary"]["claim"],
                "negative_control_verdict": f"{flip['cvc5_before']}->{flip['cvc5_after_drop_psd']} when PSD is dropped",
            },
        },
        "claim_path_tools": ["QuantumOptics", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": julia_values,
                "jax": jax_values,
                "pytorch": pytorch_values,
            },
            "max_divergence": abs(float(julia_values["excluded_count"]) - float(jax_values["excluded_unsat_count"])),
            "notes": [
                "Julia is authoritative for M/C construction, admitted/excluded witness classification, convex closure, and quotient class counts.",
                "JAX provides z3+cvc5 exact structural receipts for the excluded witnesses and the PSD erase flip.",
                "PyTorch provides a distinct differentiable boundary normal via torch.func.jacrev, not a mirror of SMT.",
            ],
        },
        "TOOL_MANIFEST": {
            "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from leg receipts only"},
            "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result path binding"},
        },
        "TOOL_INTEGRATION_DEPTH": {"json": "supportive", "pathlib": "supportive"},
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"full_M_classes={result['S_quotient_under_M']['full_M_class_count']} "
        f"drop_P_xplus_classes={result['S_quotient_under_M']['drop_P_xplus_class_count']} "
        f"drop_PSD={result['negative_control_flip_result']['drop_PSD_z3'][0]}->{result['negative_control_flip_result']['drop_PSD_z3'][1]}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
