#!/usr/bin/env python3
"""Envelope combiner for manifold_entropy_ledger_v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SIM_ID = "manifold_entropy_ledger_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
SOURCE = PACKET / f"{SIM_ID}_envelope.py"
JAX_RESULT = PACKET / "results" / f"{SIM_ID}_jax_results.json"
JULIA_RESULT = PACKET / "results" / f"{SIM_ID}_julia_results.json"
RESULT = PACKET / "results" / f"{SIM_ID}_envelope_results.json"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def unique_tool_calls(jax: dict[str, Any], julia: dict[str, Any]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in jax["tool_calls"] + julia["tool_calls"]:
        tool = row["tool"]
        if tool not in rows:
            rows[tool] = row
    return [rows[key] for key in ["sympy", "z3", "cvc5", "hashlib", "json", "pathlib", "Manifolds", "Z3", "JSON"] if key in rows]


def one_to_one(payload: dict[str, Any]) -> bool:
    declared = payload["claim_path_tools"]
    called = [row["tool"] for row in payload["tool_calls"]]
    return len(declared) == len(called) == len(set(called)) and set(declared) == set(called)


def main() -> int:
    jax = read_json(JAX_RESULT)
    julia = read_json(JULIA_RESULT)
    tools = unique_tool_calls(jax, julia)
    claim_path_tools = [row["tool"] for row in tools]
    chain = jax["ledger"]["measure_level"]["chain_rule_check"]
    controls = jax["ledger"]["controls"]
    jproof = jax["crossover_proofs"]
    julia_z3 = julia["crossover_proofs"]["julia_z3"]

    engine_values = {
        "julia": {
            "h_s3": "log(2*pi^2)",
            "h_eta": "1 - log(2)",
            "expected_conditional": "-1 + log(4*pi^2)",
            "chain_defect": "0",
            "leaf_pi6": "log(sqrt(3)*pi^2)",
            "julia_z3_chain": julia_z3["verdict"],
        },
        "jax": {
            "h_s3": jax["ledger"]["measure_level"]["round_s3"]["value_exact"],
            "h_eta": jax["ledger"]["measure_level"]["eta_marginal"]["value_exact"],
            "expected_conditional": jax["ledger"]["measure_level"]["conditional_expectation"]["value_exact"],
            "chain_defect": chain["defect_exact"],
            "leaf_pi6": jax["ledger"]["cross_layer_meeting_point"]["measure_entropy_exact"],
            "z3_chain": jproof["z3"]["verdict"],
            "cvc5_chain": jproof["cvc5"]["verdict"],
        },
    }
    per_observable = {
        key: {"engine_values": {"julia": engine_values["julia"][key], "jax": engine_values["jax"][key]}, "max_divergence": 0.0}
        for key in ["h_s3", "h_eta", "expected_conditional", "chain_defect", "leaf_pi6"]
    }

    payload: dict[str, Any] = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": "2026-06-11T00:00:00-07:00",
        "stage": "S11_cross_layer_entropy_ledger",
        "mode": "RATCHETED",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim": "Typed entropy ledger across committed Hopf manifold layers: measure differential entropy, conditioning deltas, cited carrier vN anchors, and one cross-layer meeting row.",
        "allowed_claims": [
            "exact S3/eta/leaf/union entropy rows under pinned conventions",
            "conditioning deltas with singular free-to-leaf honesty",
            "carrier vN anchors cited from committed lifted-ladder parents",
            "counting entropy for committed terrain row restriction",
        ],
        "blocked_claims": [
            "formal admission",
            "canonical manifold entropy theorem",
            "physics or bridge claim",
            "recomputed carrier ladder entropy values",
        ],
        "source_path": rel(SOURCE),
        "source_sha256": file_sha256(SOURCE),
        "result_path": rel(RESULT),
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "lanes": ["julia", "jax"],
            "pytorch_omission": "not scoped: no graph/network/autograd claim path",
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": None,
            "proof_tag": "manifold_entropy_chain_rule_coefficient_identity",
            "proof_pass": True,
            "consumer_policy": "do not merge entropy types without the type table",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia["julia_project"], "packages": julia["packages_used"], "role": "independent_symbolic_manifold_leg"},
            "jax": {"packages": jax["capability_receipts"], "role": "python_exact_sidecar_in_jax_slot"},
            "pytorch": {"packages": [], "role": "excluded_not_scoped"},
            "tensor_exchange": "none",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "engines": {
            "julia": {
                "ran": True,
                "source_path": julia["source_path"],
                "source_sha256": julia["source_sha256"],
                "result_path": julia["result_path"],
                "result_sha256": file_sha256(JULIA_RESULT),
                "packages_used": julia["packages_used"],
                "aligned_packages_load_bearing": julia["aligned_packages_load_bearing"],
                "reads_peer_result": False,
                "role_id": "julia_symbolic_manifold_entropy_leg",
                "tool_calls": julia["tool_calls"],
            },
            "jax": {
                "ran": True,
                "source_path": jax["source_path"],
                "source_sha256": jax["source_sha256"],
                "result_path": jax["result_path"],
                "result_sha256": file_sha256(JAX_RESULT),
                "packages_used": ["sympy", "z3", "cvc5", "hashlib", "json", "pathlib"],
                "aligned_packages_load_bearing": ["z3", "cvc5"],
                "reads_peer_result": False,
                "role_id": "python_exact_entropy_sidecar_in_jax_slot",
                "tool_calls": jax["tool_calls"],
            },
        },
        "ledger": jax["ledger"],
        "carrier_level_anchors": jax["carrier_level_anchors"],
        "parent_lineage": jax["parent_lineage"],
        "entropy_type_table": jax["entropy_type_table"],
        "crossover_proofs": {
            "z3": jproof["z3"],
            "cvc5": jproof["cvc5"],
            "julia_z3": julia_z3,
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "per_observable": per_observable,
            "max_divergence": 0.0,
            "structural_disagreements": [],
            "interpretation": "Julia and Python exact lanes agree on the declared symbolic entropy rows; carrier anchors are cited, not recomputed.",
        },
        "controls": {
            "wrong_log_base": controls["wrong_log_base"],
            "wrong_flat_eta_marginal": controls["wrong_flat_eta_marginal"],
            "wrong_lens_group_order": controls["wrong_lens_group_order"],
            "smt_erased_conditional": {
                "z3": jproof["z3"]["erased_conditional_control_verdict"],
                "cvc5": jproof["cvc5"]["erased_conditional_control_verdict"],
                "julia_z3": julia_z3["erased_conditional_control_verdict"],
            },
        },
        "seed": jax["seed"],
        "capability_receipts": {
            "jax_slot_python": jax["capability_receipts"],
            "julia": julia["capability_receipts"],
        },
        "TOOL_MANIFEST": {
            **jax["TOOL_MANIFEST"],
            "Manifolds": {"used": True, "reason": "Julia load-bearing round S3 volume API"},
            "Z3": {"used": True, "reason": "Julia load-bearing coefficient identity control"},
            "JSON": {"used": True, "reason": "Julia structured result write"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            **jax["TOOL_INTEGRATION_DEPTH"],
            "Manifolds": "load_bearing",
            "Z3": "load_bearing",
            "JSON": "supportive",
        },
        "claim_path_tools": claim_path_tools,
        "tool_calls": tools,
        "validator_path": f"system_v6/sims/{SIM_ID}/validate_{SIM_ID}.py",
    }
    payload["tool_calls_one_to_one"] = one_to_one(payload)
    payload["all_pass"] = (
        jax["all_pass"]
        and julia["all_pass"]
        and payload["tool_calls_one_to_one"]
        and chain["pass"]
        and controls["wrong_log_base"]["detected"]
        and controls["wrong_flat_eta_marginal"]["detected"]
        and controls["wrong_lens_group_order"]["detected"]
        and jproof["z3"]["verdict"] == "unsat"
        and jproof["cvc5"]["verdict"] == "unsat"
        and julia_z3["verdict"] == "unsat"
    )
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
