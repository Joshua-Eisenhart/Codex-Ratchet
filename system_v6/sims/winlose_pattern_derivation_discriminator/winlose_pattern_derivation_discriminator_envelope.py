#!/usr/bin/env python3
"""Composite envelope for the Win/Lose pattern derivation discriminator."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "winlose_pattern_derivation_discriminator"
OBJECT_ID = f"{SIM_ID}_envelope"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULTS_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULTS_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULTS_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULTS_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULTS_DIR / f"{SIM_ID}_pytorch_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from independently run Julia, JAX, and PyTorch receipts",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic result-path binding",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source identity pinning",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
}


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload.get("source_sha256"),
        "result_path": str(result_path),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": payload.get("packages_used", []),
        "aligned_packages_load_bearing": payload.get("aligned_packages_load_bearing", []),
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "solution_counts": payload.get("solution_counts", {}),
        "documented_table_sat": payload.get("documented_table_sat", {}),
        "verdict": payload.get("verdict"),
    }


def shared_scalar_spreads(engine_scalars: dict[str, dict[str, float]]) -> dict[str, dict[str, Any]]:
    common = set.intersection(*(set(values) for values in engine_scalars.values()))
    rows: dict[str, dict[str, Any]] = {}
    for key in sorted(common):
        values = {engine: float(scalars[key]) for engine, scalars in engine_scalars.items()}
        spread = max(values.values()) - min(values.values())
        rows[key] = {"values": values, "spread": spread, "within_tolerance": spread == 0.0}
    return rows


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    payloads = {"julia": julia, "jax": jax, "pytorch": pytorch}
    engine_scalars = {name: payload["shared_scalars"] for name, payload in payloads.items()}
    spreads = shared_scalar_spreads(engine_scalars)
    max_divergence = max((row["spread"] for row in spreads.values()), default=0.0)
    counts = {name: payload["solution_counts"] for name, payload in payloads.items()}
    full_counts = {name: int(row["full_constraints"]) for name, row in counts.items()}
    drop_scaffold_counts = {name: int(row["drop_chart_scaffold_consistency"]) for name, row in counts.items()}
    drop_balance_counts = {name: int(row["drop_balance"]) for name, row in counts.items()}
    selected_coupling_counts = {
        name: int(payload["shared_scalars"]["selected_outcome_coupling_solution_count"])
        for name, payload in payloads.items()
    }
    documented_sat = {
        "julia_z3": julia["smt"]["julia_z3"]["documented_table_sat"],
        "z3_jax": jax["smt"]["z3"]["documented_table_sat"],
        "cvc5_jax": jax["smt"]["cvc5"]["documented_table_sat"],
        "z3_pytorch": pytorch["smt"]["z3"]["documented_table_sat"],
        "cvc5_pytorch": pytorch["smt"]["cvc5"]["documented_table_sat"],
    }
    scrambled_sat = {
        "julia_z3": julia["smt"]["julia_z3"]["scrambled_table_sat"],
        "z3_jax": jax["smt"]["z3"]["scrambled_table_sat"],
        "cvc5_jax": jax["smt"]["cvc5"]["scrambled_table_sat"],
        "z3_pytorch": pytorch["smt"]["z3"]["scrambled_table_sat"],
        "cvc5_pytorch": pytorch["smt"]["cvc5"]["scrambled_table_sat"],
    }
    all_pass = bool(
        all(payload.get("all_pass") is True for payload in payloads.values())
        and set(full_counts.values()) == {36}
        and set(drop_scaffold_counts.values()) == {36}
        and set(selected_coupling_counts.values()) == {1}
        and set(drop_balance_counts.values()) == {256}
        and set(documented_sat.values()) == {"sat"}
        and set(scrambled_sat.values()) == {"unsat"}
        and all(payload.get("reads_peer_result") is False for payload in payloads.values())
        and max_divergence == 0.0
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
    )

    verdict = "underdetermined-36" if all_pass else "failed_or_inconclusive"

    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "classification": classification,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_sha256(),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "scratch diagnostic finite combinatorics discriminator only; no canonical promotion, no bridge claim, no scientific admission",
        "all_pass": all_pass,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "identity_pin": jax["identity_pin"],
        "documented_table": jax["documented_table"],
        "sign_outcome_analysis": jax["sign_outcome_analysis"],
        "primary_question": {
            "question": "Are the documented two-bit outcomes determined by sign triple (b0,b3,b6), or is an additional row datum required; and what happens to the 36 balanced-dual models when the resulting coupling is encoded over assignment bits?",
            "solution_count": full_counts["julia"],
            "verdict": verdict,
            "documented_table_sat": set(documented_sat.values()) == {"sat"},
            "scrambled_cell_sat_to_unsat": set(scrambled_sat.values()) == {"unsat"},
            "sign_determined": bool(jax["sign_outcome_analysis"]["signs_only_functional"]),
            "selected_minimal_extra_input": jax["sign_outcome_analysis"]["selected_minimal_extra_input"],
            "selected_coupling_solution_count": selected_coupling_counts["julia"],
        },
        "solution_counts": {
            "full_constraints": full_counts,
            "drop_chart_scaffold_consistency": drop_scaffold_counts,
            "selected_outcome_coupling": selected_coupling_counts,
            "drop_balance": drop_balance_counts,
        },
        "controls": {
            "chart_scaffold_consistency": {
                "counts_when_dropped": drop_scaffold_counts,
                "increases_over_full": all(value > full_counts[name] for name, value in drop_scaffold_counts.items()),
                "interpretation": "no increase: b6=-b0*b3 is retained as documented row-scaffold metadata consistency, not as an assignment-bit predicate",
            },
            "outcome_coupling": {
                "counts": {
                    "julia": julia["controls"]["outcome_coupling_counts"],
                    "jax": jax["controls"]["outcome_coupling_counts"],
                    "pytorch": pytorch["controls"]["outcome_coupling_counts"],
                },
                "selected_counts": selected_coupling_counts,
                "interpretation": "signs alone split; signs plus operator id make outcome functional and reduce the 36 balanced-dual models to the documented table",
            },
            "drop_balance": {
                "counts": drop_balance_counts,
                "changes_over_full": any(value != full_counts[name] for name, value in drop_balance_counts.items()),
                "interpretation": "balance is load-bearing: removing it raises the count from 36 to 256",
            },
            "scramble_one_documented_cell": {
                "cell": "Type-1 Se outer LOSE -> WIN",
                "smt_status": scrambled_sat,
                "violations": jax["controls"]["scramble_one_documented_cell"]["violations"],
            },
        },
        "orbit_diagnostic": {
            "status": "primary_undertermination_orbits_under_conservative_stage_relabeling",
            "julia": julia["relaxed_orbit_diagnostic"],
            "jax": jax["relaxed_orbit_diagnostic"],
            "pytorch": pytorch["relaxed_orbit_diagnostic"],
        },
        "smt_verdicts": {
            "documented_table_sat": documented_sat,
            "scrambled_table_sat": scrambled_sat,
            "z3_jax_full_model_count": jax["smt"]["z3"]["full_constraints"]["model_count"],
            "cvc5_jax_full_model_count": jax["smt"]["cvc5"]["full_constraints"]["model_count"],
            "z3_pytorch_full_model_count": pytorch["smt"]["z3"]["full_constraints"]["model_count"],
            "cvc5_pytorch_full_model_count": pytorch["smt"]["cvc5"]["full_constraints"]["model_count"],
            "julia_z3_full_model_count": julia["smt"]["julia_z3"]["full_constraints_model_count"],
            "julia_z3_target_blocking_status": julia["smt"]["julia_z3"]["target_blocking_status"],
            "sign_class_functionality": {
                "julia_z3": julia["smt"]["julia_z3"]["sign_class_functionality"],
                "z3_jax": jax["smt"]["z3"]["sign_class_functionality"],
                "cvc5_jax": jax["smt"]["cvc5"]["sign_class_functionality"],
                "z3_pytorch": pytorch["smt"]["z3"]["sign_class_functionality"],
                "cvc5_pytorch": pytorch["smt"]["cvc5"]["sign_class_functionality"],
            },
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
                "verdict": jax["smt"]["z3"]["documented_table_sat"],
                "model_count_full_constraints": jax["smt"]["z3"]["full_constraints"]["model_count"],
                "drop_chart_scaffold_consistency_model_count": jax["smt"]["z3"]["drop_chart_scaffold_consistency"]["model_count"],
                "selected_outcome_coupling_model_count": selected_coupling_counts["jax"],
                "drop_balance_model_count": jax["smt"]["z3"]["drop_balance"]["model_count"],
                "scrambled_table_sat": jax["smt"]["z3"]["scrambled_table_sat"],
                "blocking_clause_status_after_full_count": jax["smt"]["z3"]["full_constraints"]["status_after_blocking"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax["smt"]["cvc5"]["documented_table_sat"],
                "model_count_full_constraints": jax["smt"]["cvc5"]["full_constraints"]["model_count"],
                "drop_chart_scaffold_consistency_model_count": jax["smt"]["cvc5"]["drop_chart_scaffold_consistency"]["model_count"],
                "selected_outcome_coupling_model_count": selected_coupling_counts["jax"],
                "drop_balance_model_count": jax["smt"]["cvc5"]["drop_balance"]["model_count"],
                "scrambled_table_sat": jax["smt"]["cvc5"]["scrambled_table_sat"],
                "blocking_clause_status_after_full_count": jax["smt"]["cvc5"]["full_constraints"]["status_after_blocking"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["smt"]["julia_z3"]["documented_table_sat"],
                "model_count_full_constraints": julia["smt"]["julia_z3"]["full_constraints_model_count"],
                "drop_chart_scaffold_consistency_model_count": julia["smt"]["julia_z3"]["drop_chart_scaffold_consistency_model_count"],
                "selected_outcome_coupling_model_count": selected_coupling_counts["julia"],
                "drop_balance_model_count": julia["smt"]["julia_z3"]["drop_balance_model_count"],
                "scrambled_table_sat": julia["smt"]["julia_z3"]["scrambled_table_sat"],
                "target_blocking_status": julia["smt"]["julia_z3"]["target_blocking_status"],
            },
        },
        "claim_path_tools": ["Z3", "z3", "cvc5", "jax", "jax.numpy", "torch"],
        "control_only_tools": [],
        "shared_scalar_spreads": spreads,
        "out_of_tolerance_shared_scalars": {key: row for key, row in spreads.items() if not row["within_tolerance"]},
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": float(julia["shared_scalars"]["full_solution_count"]),
                "jax": float(jax["shared_scalars"]["full_solution_count"]),
                "pytorch": float(pytorch["shared_scalars"]["full_solution_count"]),
            },
            "max_divergence": max_divergence,
            "comparison_rule": "same finite model-count/control scalars across independent engine receipts",
        },
        "ledger_result_paths": {
            "julia": str(JULIA_RESULT),
            "jax": str(JAX_RESULT),
            "pytorch": str(PYTORCH_RESULT),
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
        "WINLOSE_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"full={result['primary_question']['solution_count']} "
        f"drop_scaffold={result['solution_counts']['drop_chart_scaffold_consistency']['julia']} "
        f"selected_coupling={result['solution_counts']['selected_outcome_coupling']['julia']} "
        f"drop_balance={result['solution_counts']['drop_balance']['julia']} "
        f"verdict={result['primary_question']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
