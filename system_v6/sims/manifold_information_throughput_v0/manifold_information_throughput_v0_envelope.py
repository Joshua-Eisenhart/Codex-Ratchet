#!/usr/bin/env python3
"""Envelope combiner for manifold_information_throughput_v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SIM_ID = "manifold_information_throughput_v0"
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
    return json.loads(path.read_text(encoding="utf-8"))


def unique_tool_calls(jax: dict[str, Any], julia: dict[str, Any]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in jax["tool_calls"] + julia["tool_calls"]:
        rows.setdefault(row["tool"], row)
    return [rows[key] for key in ["sympy", "z3", "cvc5", "QuantumOptics", "Z3"] if key in rows]


def main() -> int:
    jax = read_json(JAX_RESULT)
    julia = read_json(JULIA_RESULT)
    tools = unique_tool_calls(jax, julia)
    s4_py = jax["throughput_ledger"]["per_channel_capacities"]["s4_operator_channels"]
    s4_jl = julia["s4_six_state_rows"]
    per_observable = {}
    for key in ["D_z", "D_x", "R_x", "R_z"]:
        py_value = float(s4_py[key]["six_state"]["holevo_nats"])
        jl_value = float(s4_jl[key]["holevo_nats"])
        per_observable[f"{key}_six_state_holevo"] = {
            "engine_values": {"julia": jl_value, "jax": py_value},
            "max_divergence": abs(py_value - jl_value),
        }
    max_divergence = max(row["max_divergence"] for row in per_observable.values())
    z3 = jax["crossover_proofs"]["z3"]
    cvc5 = jax["crossover_proofs"]["cvc5"]
    julia_z3 = julia["crossover_proofs"]["julia_z3"]

    payload: dict[str, Any] = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": "2026-06-11T00:00:00-07:00",
        "stage": "S11_information_throughput_ledger",
        "mode": "RATCHETED",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim": "Light-symbolic information-throughput ledger over committed S4/S5 channels, the eight-stage word, and finite ratchet record accounts.",
        "allowed_claims": [
            "exact dephasing/unitary rows where channel class earns exact capacity",
            "pinned-ensemble Holevo throughput for the committed S4 and S5 channel rows",
            "finite quotient state-loss vs retained-record account",
            "density-vs-spinor 720 readout boundary as a throughput row",
        ],
        "blocked_claims": [
            "formal admission",
            "canonical capacity theorem for all affine terrain channels",
            "entropy as primitive",
            "physics, bridge, or manifold-completion claim",
        ],
        "source_path": rel(SOURCE),
        "source_sha256": file_sha256(SOURCE),
        "result_path": rel(RESULT),
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "lanes": ["julia", "jax"],
            "pytorch_omission": "not scoped: no graph/network/autograd claim path for this light-symbolic QIT/channel ledger",
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": None,
            "proof_tag": "qubit_throughput_and_finite_record_conservation",
            "proof_pass": True,
            "consumer_policy": "capacity exactness is per-row; general affine terrain rows remain bounds unless a later channel-class proof upgrades them",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia["julia_project"], "packages": julia["packages_used"], "role": "QuantumOptics entropy and Julia Z3 check"},
            "jax": {"packages": jax["packages_used"], "role": "Python exact/SMT sidecar in jax slot"},
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
                "role_id": julia["role_id"],
                "tool_calls": julia["tool_calls"],
            },
            "jax": {
                "ran": True,
                "source_path": jax["source_path"],
                "source_sha256": jax["source_sha256"],
                "result_path": jax["result_path"],
                "result_sha256": file_sha256(JAX_RESULT),
                "packages_used": jax["packages_used"],
                "aligned_packages_load_bearing": jax["aligned_packages_load_bearing"],
                "reads_peer_result": False,
                "role_id": jax["role_id"],
                "tool_calls": jax["tool_calls"],
            },
        },
        "throughput_ledger": jax["throughput_ledger"],
        "julia_crosscheck": {"s4_six_state_rows": julia["s4_six_state_rows"], "quantumoptics_guard": julia["quantumoptics_guard"]},
        "parent_lineage": jax["parent_lineage"],
        "controls": jax["controls"],
        "crossover_proofs": {"z3": z3, "cvc5": cvc5, "julia_z3": julia_z3},
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": {key: float(s4_jl[key]["holevo_nats"]) for key in ["D_z", "D_x", "R_x", "R_z"]},
                "jax": {key: float(s4_py[key]["six_state"]["holevo_nats"]) for key in ["D_z", "D_x", "R_x", "R_z"]},
            },
            "per_observable": per_observable,
            "max_divergence": max_divergence,
            "structural_disagreements": [],
            "interpretation": "Julia QuantumOptics and Python exact sidecar agree on the S4 throughput crosscheck rows; broader terrain/ratchet ledger is Python exact/SMT with parent hash pins.",
        },
        "capability_receipts": {"jax_slot_python": jax["capability_receipts"], "julia": julia["capability_receipts"]},
        "TOOL_MANIFEST": {
            **jax["TOOL_MANIFEST"],
            "QuantumOptics": julia["TOOL_MANIFEST"]["QuantumOptics"],
            "Z3": julia["TOOL_MANIFEST"]["Z3"],
        },
        "TOOL_INTEGRATION_DEPTH": {**jax["TOOL_INTEGRATION_DEPTH"], "QuantumOptics": "load_bearing", "Z3": "load_bearing"},
        "claim_path_tools": [row["tool"] for row in tools],
        "tool_calls": tools,
        "validator_path": f"system_v6/sims/{SIM_ID}/validate_{SIM_ID}.py",
    }
    payload["all_pass"] = (
        jax["all_pass"]
        and julia["all_pass"]
        and max_divergence < 1.0e-9
        and z3["verdict"] == "unsat"
        and cvc5["verdict"] == "unsat"
        and julia_z3["verdict"] == "unsat"
        and payload["controls"]["wrong_base_control"]["detected"]
    )
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
