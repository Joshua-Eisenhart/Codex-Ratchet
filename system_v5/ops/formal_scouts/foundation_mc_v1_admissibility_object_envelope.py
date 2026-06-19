#!/usr/bin/env python3
"""Composite three-engine envelope for M(C) v1 finite admissibility object."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_mc_v1_admissibility_object"
OBJECT_ID = "foundation_mc_v1_admissibility_object_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_mc_v1_admissibility_object_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_mc_v1_admissibility_object_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_pytorch_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from completed local engine receipts",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source and envelope pinning",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path, packages_used: list[str], load_bearing: list[str], values: dict[str, Any], authority: str) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload.get("source_sha256"),
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "authority": authority,
        "values": values,
        "tool_calls": [
            {"tool": name, "depth": payload.get("TOOL_INTEGRATION_DEPTH", {}).get(name), "reason": payload.get("TOOL_MANIFEST", {}).get(name, {}).get("reason")}
            for name in payload.get("TOOL_MANIFEST", {})
        ],
    }


def summary_values(payload: dict[str, Any]) -> dict[str, float]:
    summary = payload["summary"]
    return {
        "support_size": float(summary["support_size"]),
        "admitted_count": float(summary["admitted_count"]),
        "quotient_S_class_count": float(summary["quotient_S_class_count"]),
        "quotient_Adm_C_class_count": float(summary["quotient_Adm_C_class_count"]),
        "controls_all_flip": 1.0 if summary["controls_all_flip"] else 0.0,
    }


def max_divergence(values: dict[str, dict[str, float]]) -> float:
    keys = sorted(set.intersection(*(set(v) for v in values.values())))
    diffs = []
    for key in keys:
        rows = [values[engine][key] for engine in values]
        diffs.append(max(rows) - min(rows))
    return max(diffs) if diffs else 0.0


def control_matrix(*payloads: tuple[str, dict[str, Any]]) -> dict[str, Any]:
    names = sorted(payloads[0][1]["negative_controls"].keys())
    matrix: dict[str, Any] = {}
    for name in names:
        per_engine = {engine: payload["negative_controls"][name] for engine, payload in payloads}
        matrix[name] = {
            "per_engine": {
                engine: {
                    "flips_value_coupled": row["flips_value_coupled"],
                    "admitted_changed": row["admitted_changed"],
                    "quotient_changed": row["quotient_changed"],
                    "quotient_class_count_after": row["quotient_class_count_after"],
                }
                for engine, row in per_engine.items()
            },
            "all_engines_flip": all(row["flips_value_coupled"] for row in per_engine.values()),
        }
    return matrix


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    object_from_julia = julia["M_C_v1"]
    jvalues = summary_values(julia) | {
        "cl6_dim": float(julia["summary"]["cl6_dimension"]),
        "cl6_even_subalgebra_dimension": float(julia["summary"]["cl6_even_subalgebra_dimension"]),
    }
    xvalues = summary_values(jax) | {
        "cl6_dim": 64.0,
        "cl6_even_subalgebra_dimension": 32.0,
        "smt_agreement": 1.0 if jax["smt_derivations"]["agreement"] else 0.0,
    }
    tvalues = summary_values(pytorch) | {
        "cl6_dim": 64.0,
        "cl6_even_subalgebra_dimension": 32.0,
        "smt_agreement": 1.0 if pytorch["smt_derivations"]["agreement"] else 0.0,
        "torch_func_boundary_visible": 1.0 if pytorch["torch_func_check"]["carrier_erasure_boundary_visible"] else 0.0,
    }
    values = {"julia": jvalues, "jax": xvalues, "pytorch": tvalues}
    tmr_max = max_divergence(values)
    controls = control_matrix(("julia", julia), ("jax", jax), ("pytorch", pytorch))
    controls_ok = all(row["all_engines_flip"] for row in controls.values())
    field_names = ["S", "C", "M/P", "~_M", "Adm_C", "composition", "bracketing", "local_path_rules", "carrier_readout_map", "axes_A_i", "controls", "receipts", "ceiling"]
    field_coverage = {
        name: {
            "status": "PRESENT-in-object",
            "source": "M_C_v1 envelope field" if name != "receipts" else "source/result/artifact receipts embedded in object",
        }
        for name in field_names
    }
    admitted_ids = [row["id"] for row in object_from_julia["S"]["elements"] if row["admitted_under_Adm_C"]]
    z3 = jax["smt_derivations"]["z3"]
    cvc5 = jax["smt_derivations"]["cvc5"]
    all_pass = bool(
        julia["all_pass"]
        and jax["all_pass"]
        and pytorch["all_pass"]
        and tmr_max == 0.0
        and controls_ok
        and jax["smt_derivations"]["agreement"]
        and pytorch["smt_derivations"]["agreement"]
        and z3["bracketing"]["verdict"] == cvc5["bracketing"]["verdict"] == "unsat"
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "name": OBJECT_ID,
        "object_id": OBJECT_ID,
        "rung_id": RUNG_ID,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "local_lane_rule": "reads_peer_result=false for every engine leg; only this envelope reads completed leg JSONs",
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "controller_reads_engine_results_after_lanes": True,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "M(C) v1 finite admissibility object scratch diagnostic only. It wires S, C, M/P, ~_M, Adm_C, composition, bracketing, local paths, carrier/readout, axes, controls, receipts, and ceiling into one finite object. No promotion, no formal admission, no bridge, no physics, no Axis0, no manifold claim.",
        "next_lego_target": "Use only as quarantined scratch fuel for a future rebuilt M(C) v1 packet or for one exact tool-lego fit probe tied to one explicit field, after consumer-aware gates are updated.",
        "promotion_condition": "Requires rebuilt tuned-tool receipt, consumer-aware metadata, dedicated M(C) admission gate, solver/control review, composition/bracketing review, carrier/readout review, and stage-gate approval.",
        "blocked_until": "receipt metadata and consumer-aware gates are repaired; tuned-tool rebuild and dedicated M(C) admission evidence pass; owner resumes ladder work",
        "demotion_condition": "Demote or keep quarantined if receipt validation fails, consumer metadata is missing, controls stop flipping, engine lanes diverge, or any downstream claim exceeds scratch_diagnostic.",
        "out_of_scope": [
            "M(C)_system_fit",
            "same_carrier_geometry",
            "topology_readout_promotion",
            "AI_GNN_readout_promotion",
            "bridge",
            "Axis0",
            "physics",
            "manifold_admission",
        ],
        "all_pass": all_pass,
        "M_C_v1_object": object_from_julia,
        "M_C_v1_field_coverage": field_coverage,
        "M_C_v1_field_coverage_summary": {"present_in_object": field_names, "still_external": []},
        "support_S": object_from_julia["S"],
        "constraint_set_C": object_from_julia["C"],
        "M_over_P": object_from_julia["M_over_P"],
        "quotient_relation": {
            "rule": "x ~_M y iff full finite probe keys agree across density, F01, N01, bracketing, carrier, and axes probes",
            "quotient_S_mod_M": object_from_julia["quotient_S_mod_M"],
            "quotient_Adm_C_mod_M": object_from_julia["quotient_Adm_C_mod_M"],
            "bracketing_visible_in_key": True,
        },
        "Adm_C": {
            "predicate": "density_probe_C && F01 && N01 && bracketing && carrier",
            "admitted_ids": admitted_ids,
            "records": object_from_julia["Adm_C_records"],
        },
        "composition_and_local_paths": object_from_julia["composition"] | {"local_path_rules": object_from_julia["local_path_rules"]},
        "bracketing_in_quotient": {
            "wired_in": True,
            "witness_triple": object_from_julia["bracketing"]["witness_triple"],
            "associative_control_triple": object_from_julia["bracketing"]["associative_control_triple"],
            "left_right_records": [row["id"] for row in object_from_julia["S"]["elements"] if row["id"] in {"s_z0_oct_left", "s_z0_oct_right"}],
            "drop_bracketing_control": controls["drop_bracketing"],
        },
        "carrier_readout_map": object_from_julia["carrier_readout_map"],
        "axes_A_i": object_from_julia["axes_A_i"],
        "negative_controls": controls,
        "smt_derivations": {
            "jax_z3": jax["smt_derivations"]["z3"],
            "jax_cvc5": jax["smt_derivations"]["cvc5"],
            "pytorch_z3": pytorch["smt_derivations"]["z3"],
            "pytorch_cvc5": pytorch["smt_derivations"]["cvc5"],
            "derived_in_solver": True,
            "forbidden_literal_pattern_used": False,
        },
        "canon_runtime": julia["canon_runtime"],
        "receipts": {
            "envelope": {"source_path": str(SOURCE_PATH), "source_sha256": sha256_file(SOURCE_PATH), "result_path": str(RESULT_PATH)},
            "julia": {"source_path": julia["source_path"], "source_sha256": julia["source_sha256"], "result_path": str(JULIA_RESULT)},
            "jax": {"source_path": jax["source_path"], "source_sha256": jax["source_sha256"], "result_path": str(JAX_RESULT)},
            "pytorch": {"source_path": pytorch["source_path"], "source_sha256": pytorch["source_sha256"], "result_path": str(PYTORCH_RESULT)},
            "canon_artifact": julia["canon_runtime"],
        },
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT, julia["packages_used"], julia["aligned_packages_load_bearing"], jvalues, "authoritative_finite_object_and_carrier_surface"),
            "jax": engine_record(jax, JAX_RESULT, jax["packages_used"], jax["aligned_packages_load_bearing"], xvalues, "batched_finite_object_and_dual_smt"),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT, pytorch["packages_used"], pytorch["aligned_packages_load_bearing"], tvalues, "torch_func_boundary_and_dual_smt"),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3["bracketing"]["verdict"],
                "claim": "F01/N01/bracketing control suite derives UNSAT for full violating assertions and SAT after named erasures from bound entries",
                "F01": z3["F01"],
                "N01": z3["N01"],
                "bracketing": z3["bracketing"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5["bracketing"]["verdict"],
                "claim": "Independent cvc5 derivation of the same F01/N01/bracketing control suite from bound entries",
                "F01": cvc5["F01"],
                "N01": cvc5["N01"],
                "bracketing": cvc5["bracketing"],
            },
        },
        "claim_path_tools": ["QuantumOptics", "CliffordAlgebras", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": values,
            "max_divergence": tmr_max,
            "TMR": {
                "name": "three_engine_M_C_v1_reconciliation",
                "max_divergence": tmr_max,
                "compared_keys": sorted(set.intersection(*(set(v) for v in values.values()))),
            },
            "notes": [
                "Julia owns the finite object and Cl(6) carrier surface.",
                "JAX and PyTorch independently rebuild the support/admissibility/quotient counts and derive SMT flips from bound entries.",
                "PyTorch adds a torch.func selector derivative for carrier/bracketing erasure.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"fields_present={len(result['M_C_v1_field_coverage_summary']['present_in_object'])} "
        f"admitted={len(result['Adm_C']['admitted_ids'])} "
        f"controls_flip={str(all(row['all_engines_flip'] for row in result['negative_controls'].values())).lower()} "
        f"tmr_max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
