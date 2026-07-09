#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SRC_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r1_n01_noncommutation_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r1_n01_noncommutation_envelope_result.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r1_n01_noncommutation_julia_result.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r1_n01_noncommutation_jax_result.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r1_n01_noncommutation_pytorch_result.json"
RUNG_ID = "foundation_r1_n01_noncommutation"
TOL = 1.0e-12

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from independent engine receipts; not the math claim path",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic result path binding",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "pathlib": "supportive",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(
    *,
    payload: dict[str, Any],
    result_path: Path,
    packages_used: list[str],
    load_bearing: list[str],
    values: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "values": values,
    }


def max_divergence(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0


def same_contract(*payloads: dict[str, Any]) -> bool:
    first_m = payloads[0].get("M", {})
    first_definition = payloads[0].get("quotient_summary", {}).get("definition")
    return all(
        payload.get("rung_id") == RUNG_ID
        and payload.get("classification") == classification
        and payload.get("promotion_allowed") is False
        and payload.get("formal_admission_allowed") is False
        and payload.get("reads_peer_result") is False
        and payload.get("M", {}).get("noncommuting_probe_family") == first_m.get("noncommuting_probe_family")
        and payload.get("quotient_summary", {}).get("definition") == first_definition
        for payload in payloads
    )


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    julia_values = {
        "order_gap_noncommuting": julia["values"]["order_gap_noncommuting"],
        "order_gap_commuting": julia["values"]["order_gap_commuting"],
        "class_count_noncommuting": julia["values"]["class_count_noncommuting"],
        "class_count_commuting": julia["values"]["class_count_commuting"],
    }
    jax_values = {
        "order_gap_noncommuting": jax["values"]["order_gap_noncommuting"],
        "order_gap_commuting": jax["values"]["order_gap_commuting"],
        "class_count_noncommuting": jax["values"]["class_count_noncommuting"],
        "class_count_commuting": jax["values"]["class_count_commuting"],
        "z3_main_status": jax["smt"]["z3"]["main_status"],
        "cvc5_main_status": jax["smt"]["cvc5"]["main_status"],
        "z3_erase_status": jax["smt"]["z3"]["erase_x_probe_constraint_status"],
        "cvc5_erase_status": jax["smt"]["cvc5"]["erase_x_probe_constraint_status"],
    }
    pytorch_values = {
        "order_gap_noncommuting": pytorch["values"]["order_gap_noncommuting"],
        "order_gap_commuting": pytorch["values"]["order_gap_commuting"],
        "class_count_noncommuting": pytorch["values"]["class_count_noncommuting"],
        "class_count_commuting": pytorch["values"]["class_count_commuting"],
        "order_gap_squared_jacrev_at_theta": pytorch["values"]["order_gap_squared_jacrev_at_theta"],
        "commuting_control_gap_squared_jacrev_at_theta": pytorch["values"]["commuting_control_gap_squared_jacrev_at_theta"],
    }

    noncommuting_gaps = [
        float(julia_values["order_gap_noncommuting"]),
        float(jax_values["order_gap_noncommuting"]),
        float(pytorch_values["order_gap_noncommuting"]),
    ]
    commuting_gaps = [
        float(julia_values["order_gap_commuting"]),
        float(jax_values["order_gap_commuting"]),
        float(pytorch_values["order_gap_commuting"]),
    ]
    class_counts_noncommuting = [
        int(julia_values["class_count_noncommuting"]),
        int(jax_values["class_count_noncommuting"]),
        int(pytorch_values["class_count_noncommuting"]),
    ]
    class_counts_commuting = [
        int(julia_values["class_count_commuting"]),
        int(jax_values["class_count_commuting"]),
        int(pytorch_values["class_count_commuting"]),
    ]

    z3_main = jax["smt"]["z3"]["main_status"]
    cvc5_main = jax["smt"]["cvc5"]["main_status"]
    z3_erase = jax["smt"]["z3"]["erase_x_probe_constraint_status"]
    cvc5_erase = jax["smt"]["cvc5"]["erase_x_probe_constraint_status"]
    all_pass = bool(
        julia.get("all_pass") is True
        and jax.get("all_pass") is True
        and pytorch.get("all_pass") is True
        and same_contract(julia, jax, pytorch)
        and z3_main == cvc5_main == "unsat"
        and z3_erase == cvc5_erase == "sat"
        and all(gap > TOL for gap in noncommuting_gaps)
        and all(gap <= TOL for gap in commuting_gaps)
        and len(set(class_counts_noncommuting)) == 1
        and len(set(class_counts_commuting)) == 1
        and class_counts_commuting[0] < class_counts_noncommuting[0]
        and abs(float(pytorch_values["order_gap_squared_jacrev_at_theta"])) > TOL
        and abs(float(pytorch_values["commuting_control_gap_squared_jacrev_at_theta"])) <= TOL
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": "foundation_foundation_r1_n01_noncommutation_envelope",
        "rung_id": RUNG_ID,
        "classification": classification,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "source_path": str(SRC_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": (
            "Scratch foundation N01 rung only: finite qubit probe family M={Z,X}, "
            "admissible density-state quotient under probe expectations, and a "
            "commutative-collapse negative control. No promotion, no bridge, no "
            "axis-level or manifold-level admission claim."
        ),
        "all_pass": all_pass,
        "M": {
            "noncommuting_probe_family": ["Pauli_Z", "Pauli_X"],
            "commuting_control_family": ["Pauli_Z", "Diag_2_3"],
            "fixture_states": julia["M"]["fixture_states"],
        },
        "C": {
            "admissibility": ["Hermitian rho", "trace(rho)=1", "rho PSD", "normalized finite ket fixtures"],
            "rung_specific_constraint": "N01 noncommutation: [Z, X] != 0; order application Z then X is distinguishable from X then Z",
            "negative_control_constraint": "Commuting collapse replaces X with the informative commuting observable D = diag(2, 3) (not I, not a scalar multiple of I), forcing [Z, D]=0 while keeping the control information-bearing",
        },
        "quotient_summary": {
            "definition": julia["quotient_summary"]["definition"],
            "S_over_M": "Equivalence classes of admissible qubit states under finite probe expectations.",
            "noncommuting_coordinates": ["<Z>", "<X>"],
            "commuting_control_coordinates": ["<Z>", "<D>"],
            "fixture_class_count_noncommuting": class_counts_noncommuting[0],
            "fixture_class_count_commuting": class_counts_commuting[0],
            "noncommuting_classes": julia["quotient_summary"]["noncommuting_classes"],
            "commuting_control_classes": julia["quotient_summary"]["commuting_control_classes"],
            "strictly_finer_than_commuting_control": class_counts_commuting[0] < class_counts_noncommuting[0],
        },
        "negative_control_flip_result": {
            "noncommuting_order_gap": noncommuting_gaps[0],
            "commuting_control_order_gap": commuting_gaps[0],
            "noncommuting_class_count": class_counts_noncommuting[0],
            "commuting_control_class_count": class_counts_commuting[0],
            "z3_zero_gap_countermodel_noncommuting": z3_main,
            "cvc5_zero_gap_countermodel_noncommuting": cvc5_main,
            "z3_erase_x_probe_constraint": z3_erase,
            "cvc5_erase_x_probe_constraint": cvc5_erase,
            "flipped": (
                noncommuting_gaps[0] > TOL
                and commuting_gaps[0] <= TOL
                and class_counts_commuting[0] < class_counts_noncommuting[0]
                and z3_main == cvc5_main == "unsat"
                and z3_erase == cvc5_erase == "sat"
            ),
        },
        "engines": {
            "julia": engine_record(
                payload=julia,
                result_path=JULIA_RESULT,
                packages_used=["QuantumOptics", "JSON", "Dates"],
                load_bearing=["QuantumOptics"],
                values=julia_values,
            ),
            "jax": engine_record(
                payload=jax,
                result_path=JAX_RESULT,
                packages_used=["jax", "jax.numpy", "z3", "cvc5", "Python stdlib"],
                load_bearing=["z3", "cvc5"],
                values=jax_values,
            ),
            "pytorch": engine_record(
                payload=pytorch,
                result_path=PYTORCH_RESULT,
                packages_used=["torch", "torch.func", "Python stdlib"],
                load_bearing=["torch.func"],
                values=pytorch_values,
            ),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_main,
                "claim": "Zero commutator equations for computed Z/X entries are unsatisfiable",
                "erase_flip_verdict": z3_erase,
                "commuting_control_verdict": jax["smt"]["z3"]["commuting_control_status"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_main,
                "claim": "Zero commutator equations for computed Z/X entries are unsatisfiable",
                "erase_flip_verdict": cvc5_erase,
                "commuting_control_verdict": jax["smt"]["cvc5"]["commuting_control_status"],
            },
        },
        "claim_path_tools": [
            "QuantumOptics",
            "jax",
            "jax.numpy",
            "z3",
            "cvc5",
            "torch",
            "torch.func",
        ],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": julia_values,
                "jax": jax_values,
                "pytorch": pytorch_values,
            },
            "max_divergence": max(
                max_divergence(noncommuting_gaps),
                max_divergence(commuting_gaps),
            ),
            "notes": [
                "Julia is authoritative for the static QuantumOptics operator/state quotient.",
                "JAX contributes dual-SMT structural proof and erase-flip over computed operator entries.",
                "PyTorch contributes a distinct torch.func.jacrev order-sensitivity check.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "ENVELOPE_N01_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"order_gap={result['negative_control_flip_result']['noncommuting_order_gap']} "
        f"control_gap={result['negative_control_flip_result']['commuting_control_order_gap']} "
        f"classes={result['negative_control_flip_result']['noncommuting_class_count']}->"
        f"{result['negative_control_flip_result']['commuting_control_class_count']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
