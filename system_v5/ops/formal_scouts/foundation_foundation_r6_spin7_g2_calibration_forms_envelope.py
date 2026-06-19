#!/usr/bin/env python3
"""Composite envelope for foundation_r6_spin7_g2_calibration_forms.

The envelope reads completed Julia, JAX, and PyTorch leg receipts after the
legs have run. It does not recompute the engine legs or promote the rung.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_spin7_g2_calibration_forms"
OBJECT_ID = "foundation_r6_spin7_g2_calibration_forms_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_spin7_g2_calibration_forms_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_spin7_g2_calibration_forms_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r6_spin7_g2_calibration_forms_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_spin7_g2_calibration_forms_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_spin7_g2_calibration_forms_pytorch_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from completed engine receipts; not part of the algebra claim path",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for source and result receipts",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], *, result_path: Path, values: dict[str, Any]) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "values": values,
    }


def values(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload["summary"]
    return {
        "dim_Stab_phi_G2": int(summary["dim_Stab_phi_G2"]),
        "dim_Stab_Phi_Spin7": int(summary["dim_Stab_Phi_Spin7"]),
        "spin7_minus_g2_coset_dim": int(summary["spin7_minus_g2_coset_dim"]),
        "phi_fano_line_count": int(summary["phi_fano_line_count"]),
        "generic_3_form_stabilizer_dim": int(summary["generic_3_form_stabilizer_dim"]),
        "forced_commutative_zero_phi_dim": int(summary["forced_commutative_zero_phi_dim"]),
    }


def max_divergence(engine_values: dict[str, dict[str, Any]]) -> float:
    keys = [
        "dim_Stab_phi_G2",
        "dim_Stab_Phi_Spin7",
        "spin7_minus_g2_coset_dim",
        "phi_fano_line_count",
        "generic_3_form_stabilizer_dim",
        "forced_commutative_zero_phi_dim",
    ]
    diffs = []
    for key in keys:
        vals = [float(row[key]) for row in engine_values.values()]
        diffs.append(max(vals) - min(vals))
    return max(diffs)


def fences_ok(*payloads: dict[str, Any]) -> bool:
    return all(
        payload["classification"] == "scratch_diagnostic"
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["reads_peer_result"] is False
        for payload in payloads
    )


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    julia_values = values(julia)
    jax_values = values(jax)
    pytorch_values = values(pytorch)
    engine_values = {"julia": julia_values, "jax": jax_values, "pytorch": pytorch_values}
    div = max_divergence(engine_values)
    z3_verdict = jax["crossover_proofs"]["z3"]["verdict"]
    cvc5_verdict = jax["crossover_proofs"]["cvc5"]["verdict"]
    z3_erase = jax["crossover_proofs"]["z3"]["negative_control_verdict"]
    cvc5_erase = jax["crossover_proofs"]["cvc5"]["negative_control_verdict"]
    negative = {
        "generic_3_form_stabilizer_smaller_than_14": bool(
            julia["negative_control_flip"]["generic_3_form_stabilizer_smaller_than_14"]
            and jax["negative_control_flip"]["generic_3_form_stabilizer_smaller_than_14"]
            and pytorch["negative_control_flip"]["generic_3_form_stabilizer_smaller_than_14"]
        ),
        "drop_form_preservation_probe_so7_dim_21_vs_14": bool(
            julia["negative_control_flip"]["drop_form_preservation_probe_so7_dim_21_vs_14"]
            and jax["negative_control_flip"]["drop_form_preservation_probe_so7_dim_21_vs_14"]
            and pytorch["negative_control_flip"]["drop_form_preservation_probe_so7_dim_21_vs_14"]
        ),
        "forced_commutative_zero_phi_dim_21_vs_14": bool(
            julia["negative_control_flip"]["forced_commutative_zero_phi_dim_21_vs_14"]
            and jax["negative_control_flip"]["forced_commutative_zero_phi_dim_21_vs_14"]
            and pytorch["negative_control_flip"]["forced_commutative_zero_phi_dim_21_vs_14"]
        ),
        "erase_fano_line_e145_z3_unsat_to_sat": bool(jax["negative_control_flip"]["erase_fano_line_e145_z3_unsat_to_sat"]),
        "erase_fano_line_e145_cvc5_unsat_to_sat": bool(jax["negative_control_flip"]["erase_fano_line_e145_cvc5_unsat_to_sat"]),
        "non_g2_so7_element_detected_by_phi_z3": bool(jax["negative_control_flip"]["non_g2_so7_element_detected_by_phi_z3"]),
        "non_g2_so7_element_detected_by_phi_cvc5": bool(jax["negative_control_flip"]["non_g2_so7_element_detected_by_phi_cvc5"]),
        "torch_func_jacrev_independent_sensitivity": bool(
            pytorch["negative_control_flip"]["torch_func_jacrev_independent_sensitivity"]
        ),
        "coset_21_minus_14_is_7": bool(
            julia["negative_control_flip"]["coset_21_minus_14_is_7"]
            and jax["negative_control_flip"]["coset_21_minus_14_is_7"]
            and pytorch["negative_control_flip"]["coset_21_minus_14_is_7"]
        ),
    }
    all_pass = bool(
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and z3_verdict == cvc5_verdict == "unsat"
        and z3_erase == cvc5_erase == "sat"
        and div == 0.0
        and fences_ok(julia, jax, pytorch)
        and all(value for value in negative.values() if isinstance(value, bool))
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "controller_reads_engine_results_after_lanes": True,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": (
            "Scratch foundation R6 calibration-form stabilizer rung only: G2 is "
            "computed as Stab(phi) for the octonion associative 3-form and Spin(7) "
            "as Stab(Phi) for the Cayley 4-form. M-theory/SM remains horizon-only; "
            "no promotion or formal admission."
        ),
        "all_pass": all_pass,
        "M": {
            "name": "form_preservation_probe",
            "explicit_probe_family": jax["M"]["explicit_probe_family"],
            "finite_probe_counts": jax["M"]["finite_probe_counts"],
            "measurement_map": "M(X) is the finite vector of all form-action components X.phi or X.Phi; indistinguishability is equality under that vector",
        },
        "C": {
            "trace_eq_1": bool(julia["C"]["trace_eq_1"] and jax["C"]["trace_eq_1"] and pytorch["C"]["trace_eq_1"]),
            "psd": bool(julia["C"]["psd"] and jax["C"]["psd"] and pytorch["C"]["psd"]),
            "hermitian": bool(julia["C"]["hermitian"] and jax["C"]["hermitian"] and pytorch["C"]["hermitian"]),
            "normalization": "orthonormal octonion basis; auxiliary finite probe density is trace-one/PSD/Hermitian",
            "rung_specific_constraint": "Cayley-Dickson octonion structure constants define phi and Phi; skew generators must preserve the calibration form",
        },
        "S_mod_M": {
            "definition": "S is so(7) for phi and so(8) for Phi; A ~_M B iff M(A-B)=0; the quotient/stabilizer is ker(M)",
            "class_dimensions": {"Stab_phi_G2": julia_values["dim_Stab_phi_G2"], "Stab_Phi_Spin7": julia_values["dim_Stab_Phi_Spin7"]},
            "quotient_summary": "dim ker(M_phi)=14 and dim ker(M_Phi)=21",
            "coset": "Spin(7)/G2 dimension = 21 - 14 = 7 = S^7 horizon; no bridge claim",
        },
        "octonion_structure": julia["octonion_structure"],
        "calibration_forms": julia["calibration_forms"],
        "stabilizer_dimension_summary": {
            "dim_Stab_phi_G2": julia_values["dim_Stab_phi_G2"],
            "dim_Stab_Phi_Spin7": julia_values["dim_Stab_Phi_Spin7"],
            "spin7_minus_g2_coset_dim": julia_values["spin7_minus_g2_coset_dim"],
            "generic_3_form_stabilizer_dim": julia_values["generic_3_form_stabilizer_dim"],
            "so7_without_preservation_dim": 21,
            "forced_commutative_zero_phi_dim": julia_values["forced_commutative_zero_phi_dim"],
            "asserted_precomputed_kernel_relations": 0,
        },
        "negative_control_flip": negative,
        "engines": {
            "julia": engine_record(julia, result_path=JULIA_RESULT, values=julia_values),
            "jax": engine_record(jax, result_path=JAX_RESULT, values=jax_values),
            "pytorch": engine_record(pytorch, result_path=PYTORCH_RESULT, values=pytorch_values),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "negative_control_verdict": z3_erase,
                "claim": jax["crossover_proofs"]["z3"]["claim"],
                "asserted_precomputed_kernel_relations": 0,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "negative_control_verdict": cvc5_erase,
                "claim": jax["crossover_proofs"]["cvc5"]["claim"],
                "asserted_precomputed_kernel_relations": 0,
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["julia_z3"]["full_phi_nonpreservation_status"],
                "negative_control_verdict": julia["julia_z3"]["erased_phi_nonpreservation_status"],
                "claim": julia["julia_z3"]["claim"],
                "asserted_precomputed_kernel_relations": 0,
            },
        },
        "claim_path_tools": [
            "QuantumOptics",
            "CliffordAlgebras",
            "Z3",
            "jax",
            "jax.numpy",
            "z3",
            "cvc5",
            "torch",
            "torch.func",
        ],
        "control_only_tools": ["json", "pathlib"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": div,
            "notes": [
                "Julia is authoritative for stabilizer dimensions: exact finite form-action ranks give 14 and 21.",
                "JAX supplies z3+cvc5 in-solver preservation and erased-Fano-line flip checks over bound octonion structure constants.",
                "PyTorch supplies torch.func.jacrev sensitivity of the form-action residual; it is a genuine independent differentiable check, not exact algebra authority.",
            ],
        },
        "torch_func_sensitivity": pytorch["torch_func_sensitivity"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = result["stabilizer_dimension_summary"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R6_SPIN7_G2_CALIBRATION_FORMS_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dim_g2={summary['dim_Stab_phi_G2']} "
        f"dim_spin7={summary['dim_Stab_Phi_Spin7']} "
        f"coset={summary['spin7_minus_g2_coset_dim']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
