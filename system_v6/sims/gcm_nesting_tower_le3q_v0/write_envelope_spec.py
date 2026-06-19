#!/usr/bin/env python3
"""Write the three-engine envelope for gcm_nesting_tower_le3q_v0."""

from __future__ import annotations

import json

from gcm_nesting_tower_le3q_v0_common import (
    CLAIM_CEILING,
    CLASSIFICATION,
    ENVELOPE_PATH,
    ENVELOPE_SCHEMA,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    RESULT_PATH,
    SIM_ID,
    TOOL_INTENT,
    load_json,
    rel,
    source_lock,
    stable_sha256,
    write_json,
)


JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"


def engine_record(result: dict[str, object]) -> dict[str, object]:
    return {
        "ran": result["ran"],
        "source_path": result["source_path"],
        "source_sha256": source_lock((RESULT_PATH.parents[1] / str(result["source_path"]).split("/")[-1]), "engine source").get("sha256"),
        "result_path": result["result_path"],
        "reads_peer_result": result["reads_peer_result"],
        "packages_used": result["packages_used"],
        "aligned_packages_load_bearing": result["aligned_packages_load_bearing"],
        "package_observables": result["package_observables"],
    }


def max_count_divergence(values: dict[str, dict[str, int]]) -> int:
    keys = ("exact_all_cut_compatible_family_count", "probe_all_cut_compatible_family_count")
    max_div = 0
    for key in keys:
        observed = [int(row[key]) for row in values.values()]
        max_div = max(max_div, max(observed) - min(observed))
    return max_div


def main() -> int:
    main_result = load_json(RESULT_PATH)
    julia = load_json(JULIA_RESULT_PATH)
    jax = load_json(JAX_RESULT_PATH)
    pytorch = load_json(PYTORCH_RESULT_PATH)
    engine_values = {
        "julia": {
            "exact_all_cut_compatible_family_count": int(
                julia["claim_values"]["exact_all_cut_compatible_family_count"]
            ),
            "probe_all_cut_compatible_family_count": int(
                julia["claim_values"]["probe_all_cut_compatible_family_count"]
            ),
        },
        "jax": {
            "exact_all_cut_compatible_family_count": int(
                jax["claim_values"]["exact_all_cut_compatible_family_count"]
            ),
            "probe_all_cut_compatible_family_count": int(
                jax["claim_values"]["probe_all_cut_compatible_family_count"]
            ),
        },
        "pytorch": {
            "exact_all_cut_compatible_family_count": int(
                pytorch["claim_values"]["exact_all_cut_compatible_family_count"]
            ),
            "probe_all_cut_compatible_family_count": int(
                pytorch["claim_values"]["probe_all_cut_compatible_family_count"]
            ),
        },
    }
    envelope = {
        "schema": ENVELOPE_SCHEMA,
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "result_path": rel(RESULT_PATH),
        "result_sha256": stable_sha256(main_result),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "axis_declaration": main_result["axis_declaration"],
        "claim_path_tools": ["Graphs", "sympy", "z3", "cvc5", "torch.func", "gcm_substrate_check"],
        "engines": {
            "julia": engine_record(julia),
            "jax": engine_record(jax),
            "pytorch": engine_record(pytorch),
        },
        "crossover_proofs": main_result["crossover_proofs"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": max_count_divergence(engine_values),
        },
        "counts": main_result["counts"],
        "root_axiom_question_at_3q": main_result["root_axiom_question_at_3q"],
        "controls": main_result["controls"],
        "substrate_checks": main_result["substrate_checks"],
        "TOOL_MANIFEST": main_result["TOOL_MANIFEST"],
        "TOOL_INTEGRATION_DEPTH": main_result["TOOL_INTEGRATION_DEPTH"],
        "tool_intent": TOOL_INTENT,
        "build_boundary": main_result["build_boundary"],
        "divergence_log": main_result["classical_baseline"]["divergence_log"],
    }
    write_json(ENVELOPE_PATH, envelope)
    print(json.dumps({"ok": True, "envelope_path": rel(ENVELOPE_PATH), "max_divergence": envelope["divergence"]["max_divergence"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
