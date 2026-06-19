#!/usr/bin/env python3
"""Composite envelope for the QIT operator-composition M(C) three-engine sim."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "foundation_qit_operator_composition_mcp_envelope"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_qit_operator_composition_mcp_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_pytorch_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from fresh three-engine receipts; not a math claim path",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source-pinning hash for the envelope itself",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive"}


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path, packages: list[str], load_bearing: list[str]) -> dict[str, Any]:
    readouts = payload["readouts"].get("qit_entropy_split", payload["readouts"])
    return {
        "ran": bool(payload["all_pass"]),
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": packages,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "tool_calls": payload["tool_calls"],
        "values": {
            "order_gap": payload["composition"]["order_gap_Fi_then_Ti_vs_Ti_then_Fi"],
            "commuting_gap": payload["composition"]["commuting_control_Fe_then_Ti_vs_Ti_then_Fe"],
            "projected_nonassoc_gap": payload["composition"]["bracketing"]["projected_nonassoc_gap"],
            "raw_associative_gap": payload["composition"]["bracketing"]["raw_associative_gap"],
            "unitary_entropy_delta_abs": readouts["unitary_entropy_delta_abs"],
            "ti_entropy_increase": readouts["ti_entropy_increase"],
        },
    }


def abs_float(value: Any) -> float:
    return abs(float(value))


def max_divergence(julia: dict[str, Any], jax: dict[str, Any], pytorch: dict[str, Any]) -> float:
    paths = [
        ("composition", "order_gap_Fi_then_Ti_vs_Ti_then_Fi"),
        ("composition", "commuting_control_Fe_then_Ti_vs_Ti_then_Fe"),
    ]
    values = []
    for section, key in paths:
        jv = float(julia[section][key])
        values.append(abs(jv - float(jax[section][key])))
        values.append(abs(jv - float(pytorch[section][key])))
    return max(values)


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    z3_verdict = jax["smt"]["noncommuting_scaled_pauli_transfer"]["z3_force_commute_verdict"]
    cvc5_verdict = jax["smt"]["noncommuting_scaled_pauli_transfer"]["cvc5_force_commute_verdict"]
    z3_commuting = jax["smt"]["commuting_control"]["z3_force_commute_verdict"]
    cvc5_commuting = jax["smt"]["commuting_control"]["cvc5_force_commute_verdict"]

    controls = {
        "order_gap_flips": {
            "noncommuting": {
                "julia": julia["composition"]["order_gap_Fi_then_Ti_vs_Ti_then_Fi"],
                "jax": jax["composition"]["order_gap_Fi_then_Ti_vs_Ti_then_Fi"],
                "pytorch": pytorch["composition"]["order_gap_Fi_then_Ti_vs_Ti_then_Fi"],
            },
            "commuting_control": {
                "julia": julia["composition"]["commuting_control_Fe_then_Ti_vs_Ti_then_Fe"],
                "jax": jax["composition"]["commuting_control_Fe_then_Ti_vs_Ti_then_Fe"],
                "pytorch": pytorch["composition"]["commuting_control_Fe_then_Ti_vs_Ti_then_Fe"],
            },
            "carrier_erasure_control": {
                "julia": julia["composition"]["carrier_erasure_order_gap"],
                "jax": jax["composition"]["carrier_erasure_order_gap"],
            },
        },
        "bracketing_flips": {
            "raw_associative": {
                "julia": julia["composition"]["bracketing"]["raw_associative_gap"],
                "jax": jax["composition"]["bracketing"]["raw_associative_gap"],
                "pytorch": pytorch["composition"]["bracketing"]["raw_associative_gap"],
            },
            "projected_nonassociative": {
                "julia": julia["composition"]["bracketing"]["projected_nonassoc_gap"],
                "jax": jax["composition"]["bracketing"]["projected_nonassoc_gap"],
                "pytorch": pytorch["composition"]["bracketing"]["projected_nonassoc_gap"],
            },
            "erased_projected": {
                "julia": julia["composition"]["bracketing"]["erased_projected_gap"],
                "jax": jax["composition"]["bracketing"]["erased_projected_gap"],
            },
        },
        "entropy_split": {
            "unitary_entropy_delta_abs": {
                "julia": julia["readouts"]["unitary_entropy_delta_abs"],
                "jax": jax["readouts"]["qit_entropy_split"]["unitary_entropy_delta_abs"],
                "pytorch": pytorch["readouts"]["unitary_entropy_delta_abs"],
            },
            "ti_dissipative_entropy_increase": {
                "julia": julia["readouts"]["ti_entropy_increase"],
                "jax": jax["readouts"]["qit_entropy_split"]["ti_entropy_increase"],
                "pytorch": pytorch["readouts"]["ti_entropy_increase"],
            },
        },
        "smt_flip": {
            "noncommuting_force_commute": {"z3": z3_verdict, "cvc5": cvc5_verdict},
            "commuting_control_force_commute": {"z3": z3_commuting, "cvc5": cvc5_commuting},
            "derive_in_solver": "Matrices are bound entry-wise; solvers derive AB and BA products internally before checking AB == BA.",
        },
        "probe_drop_flip": {
            "julia_probe_drop_coarsens": julia["quotient"]["probe_drop_coarsens"],
            "jax_probe_drop_coarsens": jax["quotient"]["probe_drop_coarsens"],
            "pytorch_probe_drop_coarsens": pytorch["quotient"]["probe_drop_coarsens"],
        },
    }

    all_pass = bool(
        julia["all_pass"]
        and jax["all_pass"]
        and pytorch["all_pass"]
        and z3_verdict == cvc5_verdict == "unsat"
        and z3_commuting == cvc5_commuting == "sat"
        and controls["probe_drop_flip"]["julia_probe_drop_coarsens"]
        and controls["probe_drop_flip"]["jax_probe_drop_coarsens"]
        and controls["probe_drop_flip"]["pytorch_probe_drop_coarsens"]
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "reads_peer_result": False,
        },
        "object_id": OBJECT_ID,
        "rung_id": "qit_operator_composition_mcp",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_sha256(),
        "result_path": str(RESULT_PATH),
        "all_pass": all_pass,
        "M": {
            "probe_family": ["Z0", "X0", "Z0Z1"],
            "source": "Each engine computes S/~_M classes from local density states and local probe expectations.",
        },
        "C": {
            "constraints": ["trace=1", "Hermitian", "PSD", "3-qubit finite carrier", "Ti/Te Lindblad channels", "Fi/Fe unitary channels"],
            "rung_specific_constraint": "composition and bracketing are evaluated through ordered Ti/Te/Fi/Fe operators and the P_M quotient-section product",
        },
        "quotient": {
            "julia": julia["quotient"],
            "jax": jax["quotient"],
            "pytorch": pytorch["quotient"],
        },
        "controls": controls,
        "readouts": {
            "qit": controls["entropy_split"],
            "geometry": {
                "julia_quantumoptics_bures": julia["readouts"]["QuantumOptics_fidelity_Bures_FiTi_vs_TiFi"],
                "jax_geomstats_bures": jax["readouts"]["geomstats_bures_wasserstein_FiTi_vs_TiFi"],
                "pytorch_geomstats_bures": pytorch["readouts"]["geomstats_bures_wasserstein_FiTi_vs_TiFi"],
                "jax_ott_sinkhorn": jax["readouts"]["ott_sinkhorn_FiTi_vs_TiFi"],
            },
            "coherent_information": {
                "julia_initial": julia["readouts"]["initial"]["coherent_information_q0_to_q12"],
                "jax_initial": jax["readouts"]["qit_entropy_split"]["initial"]["coherent_information_q0_to_q12"],
                "pytorch_initial": pytorch["readouts"]["initial"]["coherent_information_q0_to_q12"],
            },
        },
        "engines": {
            "julia": engine_record(
                julia,
                JULIA_RESULT,
                [
                    "QuantumOptics",
                    "DifferentialEquations",
                    "CliffordAlgebras",
                    "Grassmann",
                    "QuantumClifford",
                    "ITensors",
                    "ITensorMPS",
                    "Symbolics",
                    "Graphs",
                    "Z3",
                    "LinearAlgebra",
                    "JSON",
                    "Dates",
                    "SHA",
                ],
                ["QuantumOptics", "DifferentialEquations", "Z3"],
            ),
            "jax": engine_record(
                jax,
                JAX_RESULT,
                [
                    "jax",
                    "jax.numpy",
                    "dynamiqs",
                    "diffrax",
                    "quimb.tensor",
                    "cotengra",
                    "geomstats",
                    "ott",
                    "sympy",
                    "z3",
                    "cvc5",
                    "networkx",
                    "numpy",
                ],
                ["geomstats", "sympy", "z3", "cvc5"],
            ),
            "pytorch": engine_record(
                pytorch,
                PYTORCH_RESULT,
                ["torch", "torch.func", "geomstats", "torch_ga"],
                ["geomstats", "torch_ga"],
            ),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "claim": "For the noncommuting finite operator-entry matrices, forcing AB == BA is UNSAT.",
                "commuting_control_verdict": z3_commuting,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "claim": "Independent cvc5 check of the same derive-in-solver matrix-entry commutation flip.",
                "commuting_control_verdict": cvc5_commuting,
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["smt"]["noncommuting_scaled_pauli_transfer"]["z3_force_commute_verdict"],
                "claim": "Julia Z3 derives the same noncommuting matrix-entry UNSAT control.",
                "commuting_control_verdict": julia["smt"]["commuting_control"]["z3_force_commute_verdict"],
            },
        },
        "claim_path_tools": [
            "QuantumOptics",
            "DifferentialEquations",
            "Graphs",
            "Z3",
            "geomstats",
            "sympy",
            "z3",
            "cvc5",
            "torch",
            "torch_ga",
        ],
        "control_only_tools": ["LinearAlgebra", "JSON", "Dates", "SHA", "numpy"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": {
                    "order_gap": julia["composition"]["order_gap_Fi_then_Ti_vs_Ti_then_Fi"],
                    "commuting_gap": julia["composition"]["commuting_control_Fe_then_Ti_vs_Ti_then_Fe"],
                    "projected_nonassoc_gap": julia["composition"]["bracketing"]["projected_nonassoc_gap"],
                },
                "jax": {
                    "order_gap": jax["composition"]["order_gap_Fi_then_Ti_vs_Ti_then_Fi"],
                    "commuting_gap": jax["composition"]["commuting_control_Fe_then_Ti_vs_Ti_then_Fe"],
                    "projected_nonassoc_gap": jax["composition"]["bracketing"]["projected_nonassoc_gap"],
                },
                "pytorch": {
                    "order_gap": pytorch["composition"]["order_gap_Fi_then_Ti_vs_Ti_then_Fi"],
                    "commuting_gap": pytorch["composition"]["commuting_control_Fe_then_Ti_vs_Ti_then_Fe"],
                    "projected_nonassoc_gap": pytorch["composition"]["bracketing"]["projected_nonassoc_gap"],
                },
            },
            "max_divergence": max_divergence(julia, jax, pytorch),
            "notes": [
                "Julia is authoritative for the QIT channel route because QuantumOptics + DifferentialEquations construct the carrier and integrate Ti/Te.",
                "JAX and PyTorch are independent local computations with reads_peer_result=false.",
            ],
        },
        "GAINED": [
            "M(C) now has an executable composition field for Ti/Te/Fi/Fe on a finite 3-qubit density carrier.",
            "Order-gap, commuting, carrier-erasure, bracketing, entropy, probe-drop, and z3+cvc5 controls all flip in the expected direction.",
            "Claim-path rich packages are restricted to computations that gate all_pass, quotient, divergence, control, or proof; side readouts are marked supportive.",
        ],
        "NOT_GAINED": [
            "No canonical admission.",
            "No formal proof admission.",
            "No bridge, Axis0, physics, IGT-truth, or final manifold claim.",
        ],
        "claim_ceiling": "classification=scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
