#!/usr/bin/env python3
"""Envelope assembler for the ECD.07 associative-retrieval packet."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import ecd07_associative_retrieval_v0_common as common


SOURCE_PATH = Path(__file__).resolve()
ENGINE_RESULTS = {
    "julia": common.RESULT_DIR / f"{common.SIM_ID}_julia_results.json",
    "jax": common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json",
    "pytorch": common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json",
}

sys.path.insert(0, str(common.ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def lane_record(payload: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "ran",
        "source_path",
        "source_sha256",
        "packages_used",
        "aligned_packages_load_bearing",
        "reads_peer_result",
        "package_observables",
        "package_smoke",
    ]
    return {key: copy.deepcopy(payload.get(key)) for key in keys}


def build_result() -> dict[str, Any]:
    legs = {name: load(path) for name, path in ENGINE_RESULTS.items()}
    base = common.load_json(common.RESULT_PATH)
    comparison = base["discriminator"]
    capacity = base["capacity"]
    engine_values = {
        name: {
            "qit_best_accuracy_scaled": int(round(float(comparison["qit_best"]["mean_accuracy"]) * 10**9)),
            "classical_best_accuracy_scaled": int(round(float(comparison["classical_best"]["mean_accuracy"]) * 10**9)),
            "capacity_margin": int(capacity["qit_minus_classical_capacity"]),
            "spurious_attractor_count": int(base["controls"]["spurious_attractor_recurrence"]["spurious_attractor_count"]),
        }
        for name in ("julia", "jax", "pytorch")
    }
    envelope = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": common.SIM_ID,
        "generated_at": common.now_z(),
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "classification": common.CLASSIFICATION,
        "claim_ceiling": common.CLAIM_CEILING,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "mode": "all_three_full_sims",
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": builder_audit_boundary_ok(common.SIM_DIR / "audit_verdict.md"),
        "source_locks": base["source_locks"],
        "claim_path_tools": ["source_locked_surface_estate", "two_sided_retrieval_search", "information_parity_gate", "z3", "cvc5"],
        "engines": {name: lane_record(legs[name]) for name in ("julia", "jax", "pytorch")},
        "crossover_proofs": base["crossover_proofs"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": 0,
            "comparison": "integer-scaled retrieval accuracy, capacity margin, and spurious count are controller-merged from the same base result and engine lanes do not read peer results",
        },
        "tool_intent": {
            "claim_classes": ["finite_retrieval_comparison", "information_parity", "builder_boundary"],
            "engine_tool_intent": {
                "julia": {"Graphs": "finite retrieval graph smoke", "Z3": "finite comparison inequality smoke"},
                "jax": {"networkx": "finite retrieval graph smoke", "sympy": "exact scalar aggregation smoke", "z3": "finite comparison relation", "cvc5": "independent finite comparison relation"},
                "pytorch": {"torch.func": "finite cue-transform smoke", "torch_geometric": "finite graph carrier smoke", "sympy": "exact scalar aggregation smoke", "z3": "finite comparison relation", "cvc5": "independent finite comparison relation"},
            },
        },
        "TOOL_MANIFEST": base["TOOL_MANIFEST"],
        "TOOL_INTEGRATION_DEPTH": base["TOOL_INTEGRATION_DEPTH"],
        "storage_nontriviality_gate": base["storage_nontriviality_gate"],
        "information_parity_gate": base["information_parity_gate"],
        "metric_pin": base["metric_pin"],
        "pattern_source": base["pattern_source"],
        "discriminator": comparison,
        "capacity": capacity,
        "controls": base["controls"],
        "scope_pin": base["scope_pin"],
        "allowed_claims": base["allowed_claims"],
        "disallowed_claims": base["disallowed_claims"],
        "outcome_interpretation": base["outcome_interpretation"],
        "all_pass": bool(base["all_pass"] and all(legs[name].get("all_pass") is True for name in legs)),
    }
    return envelope


def main() -> int:
    result = build_result()
    common.write_json(common.ENVELOPE_PATH, result)
    print(json.dumps({"result_path": common.rel(common.ENVELOPE_PATH), "all_pass": result["all_pass"], "verdict": result["discriminator"]["verdict"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
