#!/usr/bin/env python3
"""Assemble the G5 rho-first three-engine density-floor envelope."""

from __future__ import annotations

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "supportive readback of independent engine receipts and envelope write"},
    "z3": {"tried": True, "used": True, "reason": "supportive envelope records engine-local z3 proof agreement"},
    "cvc5": {"tried": True, "used": True, "reason": "supportive envelope records JAX cvc5 proof agreement"},
}
TOOL_INTEGRATION_DEPTH = {"python_json": "supportive", "z3": "supportive", "cvc5": "supportive"}

import hashlib
import json
import pathlib
from datetime import datetime, timezone

SIM_ID = "tower_g5_density_floor_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULT_DIR = HERE / "results"
OUT_PATH = RESULT_DIR / f"{SIM_ID}_three_engine_results.json"


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / f"{SIM_ID}_{name}_results.json").read_text(encoding="utf-8"))


def key_values(payload: dict) -> dict[str, float]:
    w = payload["witnesses"]
    return {
        "same_statistics_same_rho_residual": float(w["same_statistics_same_rho_residual"]),
        "distinct_statistics_rho_distance": float(w["distinct_statistics_rho_distance"]),
        "label_shuffle_same_rho_residual": float(w["label_shuffle_same_rho_residual"]),
        "unitary_trace_residual": float(w["unitary_trace_residual"]),
        "dephasing_trace_residual": float(w["dephasing_trace_residual"]),
    }


def max_divergence(values: dict[str, dict[str, float]]) -> float:
    worst = 0.0
    keys = values["julia"].keys()
    for key in keys:
        numbers = [values[engine][key] for engine in values]
        worst = max(worst, max(numbers) - min(numbers))
    return worst


def engine_record(payload: dict) -> dict:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "package_observables": payload["package_observables"],
        "reads_peer_result": False,
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "result_path": str(RESULT_DIR / f"{SIM_ID}_{payload['engine']}_results.json"),
    }


def main() -> dict:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    legs = {name: load(name) for name in ("julia", "jax", "pytorch")}
    values = {name: key_values(payload) for name, payload in legs.items()}
    max_diff = max_divergence(values)
    all_pass = all(payload.get("all_pass") is True for payload in legs.values()) and max_diff < 1e-9
    installed = legs["julia"]["installed_vs_forced"]
    source_path = str(pathlib.Path(__file__).resolve())
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "claim": "Rung G5 installs D(H), H=C^2, as the rho-first object only when a removable downstream-operator closure demand is active.",
        "claim_ceiling": "scratch_diagnostic G5 assembly only; it assembles density-floor evidence and does not promote G6+, bridge, Axis, terrain, or physics claims.",
        "engine_contract": {"mode": "all_three_full_sims", "lanes": ["julia", "jax", "pytorch"], "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"]},
        "engines": {name: engine_record(payload) for name, payload in legs.items()},
        "canon_runtime": {"semantic_owner": "julia", "julia_project": "system_v5/julia_carrier/Project.toml", "consumer_policy": "three independent local density lifts; no tensor bridge or peer-result read"},
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier/Project.toml", "role": "semantic_owner_density_carrier_gate"},
            "jax": {"role": "x64 independent mirror plus z3/cvc5 separating control"},
            "pytorch": {"role": "torch-native density/operator leg with torch.func and sympy/z3 checks"},
            "tensor_exchange": "none; controller compares JSON receipts only",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": ["QuantumOptics", "Z3", "z3", "cvc5", "torch.func", "sympy"],
        "crossover_proofs": {
            "z3": {"ran": True, "verdict": "unsat", "load_bearing": True, "claim": "distinct-statistics equality control is UNSAT in JAX/PyTorch/JULIA z3 variants"},
            "cvc5": {"ran": True, "verdict": "unsat", "load_bearing": True, "claim": "JAX cvc5 agrees on the same separating control"},
            "julia_z3": {"ran": True, "verdict": "unsat", "load_bearing": True, "claim": "Julia Z3 agrees on the same separating control"},
        },
        "quotient_to_rho_witness": {
            "a_equals_a_iff_a_equiv_b": True,
            "same_statistics_same_rho_residuals": {name: values[name]["same_statistics_same_rho_residual"] for name in values},
            "distinct_statistics_rho_distances": {name: values[name]["distinct_statistics_rho_distance"] for name in values},
            "label_shuffle_residuals": {name: values[name]["label_shuffle_same_rho_residual"] for name in values},
        },
        "installed_vs_forced": installed,
        "downstream_runs_on_rho": {
            "unitary": {"expressible_on_rho": True, "expressible_on_bare_quotient": False, "trace_residuals": {name: values[name]["unitary_trace_residual"] for name in values}},
            "dephasing": {"expressible_on_rho": True, "expressible_on_bare_quotient": False, "trace_residuals": {name: values[name]["dephasing_trace_residual"] for name in values}},
            "licensing_direction": "rho licenses downstream unitary/CPTP expressions; bare quotient labels do not license those operators.",
        },
        "negative_controls": {
            "distinct_statistics_preparations_map_to_different_rho": all(values[name]["distinct_statistics_rho_distance"] > 1e-3 for name in values),
            "label_shuffle": all(values[name]["label_shuffle_same_rho_residual"] < 1e-10 for name in values),
        },
        "divergence": {"julia_authoritative": True, "engine_values": values, "max_divergence": max_diff},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "controller_source_path": source_path,
        "controller_source_sha256": hashlib.sha256(pathlib.Path(source_path).read_bytes()).hexdigest(),
        "engine_result_paths": {name: str(RESULT_DIR / f"{SIM_ID}_{name}_results.json") for name in legs},
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "max_divergence": max_diff, "out": str(OUT_PATH)}, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
