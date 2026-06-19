#!/usr/bin/env python3
"""Composite envelope for the sedenion PG(3,2) Desargues three-engine rung."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_sedenion_pg32_desargues"
OBJECT_ID = "foundation_foundation_r6_sedenion_pg32_desargues_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_sedenion_pg32_desargues_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_sedenion_pg32_desargues_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r6_sedenion_pg32_desargues_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_sedenion_pg32_desargues_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_sedenion_pg32_desargues_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
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
    }


def max_divergence(julia: dict[str, Any], jax: dict[str, Any]) -> float:
    pairs = [
        (julia["pg32"]["point_count"], jax["pg32"]["point_count"]),
        (julia["pg32"]["line_count"], jax["pg32"]["line_count"]),
        (julia["pg32"]["ordinary_line_count"], jax["pg32"]["ordinary_line_count"]),
        (julia["pg32"]["defective_line_count"], jax["pg32"]["defective_line_count"]),
        (julia["desargues_10_3"]["point_count"], jax["desargues_10_3"]["point_count"]),
        (julia["desargues_10_3"]["line_count"], jax["desargues_10_3"]["line_count"]),
        (
            julia["zero_divisor_correlation"]["selected_defective_product"]["product_normsq"],
            jax["zero_divisor_correlation"]["selected_defective_product"]["product_normsq"],
        ),
        (
            julia["zero_divisor_correlation"]["sedenion_zero_product_pair_count_under_two_term_M"],
            jax["zero_divisor_correlation"]["sedenion_zero_product_pair_count_under_two_term_M"],
        ),
        (
            julia["octonion_control"]["zero_product_pair_count_under_two_term_M"],
            jax["octonion_control"]["zero_product_pair_count_under_two_term_M"],
        ),
        (
            julia["zero_divisor_correlation"]["defective_line_support_coverage"]["covered_line_count"],
            jax["zero_divisor_correlation"]["defective_line_support_coverage"]["covered_line_count"],
        ),
    ]
    return max(abs(float(left) - float(right)) for left, right in pairs)


def main() -> int:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    z3_defective = jax["smt"]["z3"]["defective_zero_divisor"]["verdict"]
    cvc5_defective = jax["smt"]["cvc5"]["defective_zero_divisor"]["verdict"]
    z3_ordinary = jax["smt"]["z3"]["ordinary_same_target_search"]["verdict"]
    cvc5_ordinary = jax["smt"]["cvc5"]["ordinary_same_target_search"]["verdict"]
    z3_line = jax["smt"]["z3"]["defective_line_index_anomaly"]["verdict"]
    cvc5_line = jax["smt"]["cvc5"]["defective_line_index_anomaly"]["verdict"]
    divergence_value = max_divergence(julia, jax)

    engine_values = {
        "julia": {
            "points": julia["pg32"]["point_count"],
            "lines": julia["pg32"]["line_count"],
            "ordinary_lines": julia["pg32"]["ordinary_line_count"],
            "defective_lines": julia["pg32"]["defective_line_count"],
            "desargues_points": julia["desargues_10_3"]["point_count"],
            "selected_defective_product_normsq": julia["zero_divisor_correlation"]["selected_defective_product"]["product_normsq"],
            "sedenion_zero_product_pair_count": julia["zero_divisor_correlation"]["sedenion_zero_product_pair_count_under_two_term_M"],
            "octonion_zero_product_pair_count": julia["octonion_control"]["zero_product_pair_count_under_two_term_M"],
            "defective_line_support_coverage": julia["zero_divisor_correlation"]["defective_line_support_coverage"]["covered_line_count"],
        },
        "jax": {
            "points": jax["pg32"]["point_count"],
            "lines": jax["pg32"]["line_count"],
            "ordinary_lines": jax["pg32"]["ordinary_line_count"],
            "defective_lines": jax["pg32"]["defective_line_count"],
            "desargues_points": jax["desargues_10_3"]["point_count"],
            "selected_defective_product_normsq": jax["zero_divisor_correlation"]["selected_defective_product"]["product_normsq"],
            "sedenion_zero_product_pair_count": jax["zero_divisor_correlation"]["sedenion_zero_product_pair_count_under_two_term_M"],
            "octonion_zero_product_pair_count": jax["octonion_control"]["zero_product_pair_count_under_two_term_M"],
            "defective_line_support_coverage": jax["zero_divisor_correlation"]["defective_line_support_coverage"]["covered_line_count"],
        },
        "pytorch": {
            "selected_defective_product_normsq": pytorch["selected_defective_witness"]["product_normsq"],
            "selected_defective_norm_defect": pytorch["selected_defective_witness"]["norm_multiplicativity_defect"],
            "selected_defect_jacrev": pytorch["selected_defective_witness"]["jacrev_norm_defect_gradient"],
            "ordinary_product_normsq": pytorch["ordinary_control"]["product_normsq"],
            "octonion_product_normsq": pytorch["octonion_control"]["product_normsq"],
        },
    }

    all_pass = (
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and z3_defective == cvc5_defective == "sat"
        and z3_ordinary == cvc5_ordinary == "unsat"
        and z3_line == cvc5_line == "sat"
        and julia["negative_control_flip_result"]["drop_line_type_probe"]["flips"] is True
        and jax["negative_control_flip_result"]["drop_line_type_probe"]["flips"] is True
        and jax["negative_control_flip_result"]["ordinary_same_target_control"]["flips_from_defective_witness"] is True
        and pytorch["negative_control_flip_result"]["defective_vs_ordinary_defect"]["flips"] is True
        and divergence_value == 0.0
    )

    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": (
            "Scratch diagnostic foundation rung only: finite sedenion PG(3,2) line-type split, "
            "Desargues (10_3) sub-configuration, and bounded zero-divisor controls. No promotion, "
            "formal admission, bridge, physics, stack, or axis-level claim."
        ),
        "M": julia["M"],
        "C": julia["C"],
        "S_quotient_under_M": julia["S_quotient_under_M"],
        "substantive_values": {
            "point_count": julia["pg32"]["point_count"],
            "line_count": julia["pg32"]["line_count"],
            "ordinary_line_count": julia["pg32"]["ordinary_line_count"],
            "defective_line_count": julia["pg32"]["defective_line_count"],
            "desargues_10_3": julia["desargues_10_3"],
            "defective_lines": julia["S_quotient_under_M"]["line_classes"]["defective_desargues"]["lines"],
            "desargues_points": julia["S_quotient_under_M"]["point_classes_by_defective_degree"]["degree_3_desargues_points"]["points"],
            "selected_defective_zero_divisor": julia["zero_divisor_correlation"]["selected_defective_product"],
            "defective_line_support_coverage": julia["zero_divisor_correlation"]["defective_line_support_coverage"],
            "octonion_control": julia["octonion_control"],
        },
        "negative_control_flip_result": {
            "drop_line_type_probe": julia["negative_control_flip_result"]["drop_line_type_probe"],
            "ordinary_same_target_control": jax["negative_control_flip_result"]["ordinary_same_target_control"],
            "octonion_control": jax["negative_control_flip_result"]["octonion_control"],
            "pytorch_defective_vs_ordinary_defect": pytorch["negative_control_flip_result"]["defective_vs_ordinary_defect"],
        },
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_defective,
                "claim": "Selected defective-line dyads have zero product; product and line index are derived inside z3 from bound S table constants.",
                "product_derived_in_solver": True,
                "ordinary_same_target_control_verdict": z3_ordinary,
                "defective_line_index_anomaly_verdict": z3_line,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_defective,
                "claim": "Selected defective-line dyads have zero product; product and line index are derived inside cvc5 from bound S table constants.",
                "product_derived_in_solver": True,
                "ordinary_same_target_control_verdict": cvc5_ordinary,
                "defective_line_index_anomaly_verdict": cvc5_line,
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["smt"]["Z3"]["defective_zero_divisor_verdict"],
                "ordinary_same_target_zero_product_verdict": julia["smt"]["Z3"]["ordinary_same_target_zero_product_verdict"],
                "product_derived_in_solver": True,
            },
        },
        "claim_path_tools": [
            "CliffordAlgebras",
            "Z3",
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
            "engine_values": engine_values,
            "max_divergence": divergence_value,
        },
        "TOOL_MANIFEST": {
            "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independent engine receipts"},
            "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
        },
        "TOOL_INTEGRATION_DEPTH": {"json": "supportive", "pathlib": "supportive"},
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(all_pass).lower()} "
        f"points={payload['substantive_values']['point_count']} "
        f"lines={payload['substantive_values']['line_count']} "
        f"ordinary={payload['substantive_values']['ordinary_line_count']} "
        f"defective={payload['substantive_values']['defective_line_count']} "
        f"desargues_points={payload['substantive_values']['desargues_10_3']['point_count']} "
        f"z3={z3_defective} cvc5={cvc5_defective} "
        f"ordinary_control={z3_ordinary}/{cvc5_ordinary} "
        f"max_divergence={divergence_value}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
