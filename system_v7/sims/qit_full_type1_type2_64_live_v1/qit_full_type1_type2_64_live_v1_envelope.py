#!/usr/bin/env python3
"""Three-engine envelope for qit_full_type1_type2_64_live_v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qit_full_type1_type2_64_live_v1_common import (
    ATLAS_SOURCE,
    CLAIM_CEILING,
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULTS,
    ROOT,
    SIM_DIR,
    SIM_ID,
    now_z,
    read_json,
    rel,
    sha256_file,
    write_json,
)

SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULTS / f"{SIM_ID}_envelope_results.json"

classification = "scratch_diagnostic"


TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result readback, source-hash binding, and three-engine envelope emission",
    }
}

TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}


def load_result(name: str) -> tuple[dict[str, Any], Path]:
    path = RESULTS / f"{SIM_ID}_{name}_results.json"
    if name == "main":
        path = RESULTS / f"{SIM_ID}_results.json"
    return read_json(path), path


def result_sha(path: Path) -> str:
    return sha256_file(path)


def engine_record(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    return {
        "ran": payload.get("ran", True),
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": rel(path),
        "result_sha256": result_sha(path),
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "package_observables": payload["package_observables"],
        "reads_peer_result": payload["reads_peer_result"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "all_pass": payload["all_pass"],
    }


def max_divergence(values: dict[str, float]) -> float:
    return max(values.values()) - min(values.values())


def build_envelope() -> dict[str, Any]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    main, main_path = load_result("main")
    jax, jax_path = load_result("jax")
    julia, julia_path = load_result("julia")
    pytorch, pytorch_path = load_result("pytorch")
    engine_values = {
        "julia": float(julia["object_count"]),
        "jax": float(jax["object_count"]),
        "pytorch": float(pytorch["object_count"]),
    }
    failures: list[str] = []
    if not main["all_pass"]:
        failures.append("main controller result failed")
    for name, payload in (("julia", julia), ("jax", jax), ("pytorch", pytorch)):
        if not payload["all_pass"]:
            failures.append(f"{name} result failed")
        if payload["classification"] != CLASSIFICATION:
            failures.append(f"{name} classification drift")
        if payload["promotion_allowed"] is not False or payload["formal_admission_allowed"] is not False:
            failures.append(f"{name} promotion boundary drift")
        if payload["reads_peer_result"] is not False:
            failures.append(f"{name} reads_peer_result not false")
    if max_divergence(engine_values) != 0.0:
        failures.append("engine object_count divergence")
    if jax["solver_proofs"]["z3"]["verdict"] != jax["solver_proofs"]["cvc5"]["verdict"]:
        failures.append("jax z3/cvc5 verdict mismatch")
    if jax["solver_proofs"]["z3"]["verdict"] != "unsat":
        failures.append("jax structural proof not unsat")
    if julia["julia_z3"]["verdict"] != "unsat":
        failures.append("julia z3 structural proof not unsat")
    if pytorch["readouts"]["ordered_full"]["test_accuracy"] <= pytorch["readouts"]["bag_topology_control"]["test_accuracy"]:
        failures.append("pytorch ordered readout did not beat bag control")

    envelope = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "written_at": now_z(),
        "engine": "three_engine_envelope_controller",
        "engine_contract": {
            "mode": "julia_graph_z3_jax_smt_pytorch_learned_readout",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["controller_result", "julia_local", "jax_local", "pytorch_local", "envelope_comparison"],
            "lane_evidence": {
                "julia": "independent_recompute_schedule_graph_and_z3_gate",
                "jax": "independent_numeric_feature_recompute_plus_z3_cvc5_gate",
                "pytorch": "learned_readout_with_order_erasure_ablation",
            },
        },
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "host_consumed": False,
        "live_lev_consumed": False,
        "release_admission_allowed": False,
        "graph_mutation_allowed": False,
        "mesh_projection_allowed": False,
        "lifecycle_status": "SCRATCH_DIAGNOSTIC",
        "evidence_grade": "scratch_diagnostic_measurement",
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": not failures,
        "claim": (
            "The atlas-derived finite 64-slot Type-1/Type-2 carrier forms four ordered loop objects "
            "under ordered observations; bag/static controls collapse identity; PyTorch can learn the "
            "ordered readout but loses the bag-erased ablation."
        ),
        "out_of_scope": [
            "Axis0 admission",
            "FEP admission",
            "production perception",
            "Lev mesh runtime integration",
            "physics/manifold admission",
            "hexagram semantics",
        ],
        "claim_path_tools": ["Graphs", "Z3", "jax", "z3", "cvc5", "torch.func"],
        "control_only_tools": [],
        "TOOL_MANIFEST": {
            "Graphs": julia["TOOL_MANIFEST"]["Graphs"],
            "Z3": julia["TOOL_MANIFEST"]["Z3"],
            "jax": jax["TOOL_MANIFEST"]["jax"],
            "z3": jax["TOOL_MANIFEST"]["z3"],
            "cvc5": jax["TOOL_MANIFEST"]["cvc5"],
            "torch.func": pytorch["TOOL_MANIFEST"]["torch.func"],
            "python_stdlib": TOOL_MANIFEST["python_stdlib"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "Graphs": "load_bearing",
            "Z3": "load_bearing",
            "jax": "supportive",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "torch.func": "load_bearing",
            "python_stdlib": "supportive",
        },
        "tool_intent": {
            "claim_classes": ["finite_ordered_object_formation", "erasure_control", "learned_ordered_readout"],
            "engine_tool_intent": {
                "julia": {
                    "Graphs": "loop-object graph must close four ordered edges per loop object",
                    "Z3": "scaled ordered-object gate negation must be UNSAT while bag-erased control is SAT",
                },
                "jax": {
                    "z3": "ordered-object gate negation must be UNSAT with SAT erased control",
                    "cvc5": "independent cvc5 gate must agree with z3 on the same measured values",
                },
                "pytorch": {
                    "torch.func": "jacrev/vmap gradient norms must be nonzero for the learned ordered-stream readout",
                },
            },
        },
        "engines": {
            "julia": engine_record(julia, julia_path),
            "jax": engine_record(jax, jax_path),
            "pytorch": engine_record(pytorch, pytorch_path),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "verdict": jax["solver_proofs"]["z3"]["verdict"],
                "load_bearing": True,
                "erased_control_verdict": jax["solver_proofs"]["z3"]["erased_control_verdict"],
                "claim": "ordered unique object gate is UNSAT under negation; bag-erased control is SAT/collapsed",
            },
            "cvc5": {
                "ran": True,
                "verdict": jax["solver_proofs"]["cvc5"]["verdict"],
                "load_bearing": True,
                "erased_control_verdict": jax["solver_proofs"]["cvc5"]["erased_control_verdict"],
                "claim": "independent cvc5 encoding agrees with z3 on full and erased polarity",
            },
            "julia_z3": julia["julia_z3"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "metric": "survivor_object_count",
            "max_divergence": max_divergence(engine_values),
        },
        "stability_pairs": {
            "ordered_vs_bag": {
                "ordered_accuracy": main["core_measurement"]["ordered_object_formation"]["ordered_accuracy"],
                "bag_expected_accuracy": main["core_measurement"]["negative_controls"]["bag_topology"]["expected_accuracy"],
            },
            "pytorch_ordered_vs_bag": {
                "ordered_accuracy": pytorch["readouts"]["ordered_full"]["test_accuracy"],
                "bag_accuracy": pytorch["readouts"]["bag_topology_control"]["test_accuracy"],
            },
        },
        "parent_lineage": {
            "atlas_source": rel(ATLAS_SOURCE),
            "atlas_source_sha256": sha256_file(ATLAS_SOURCE),
            "controller_result": rel(main_path),
            "controller_result_sha256": sha256_file(main_path),
        },
        "lev_host_consumer_contract": {
            "truth_state": "proposed",
            "evidence_kind": "measurement",
            "decision_ceiling": "accepted_as_evidence_only",
            "graph_mutation_allowed": False,
            "compositor_apply_allowed": False,
            "mesh_projection_allowed": False,
            "source_boundary_mutated": False,
            "cr_object_id_is_lev_entity_id": False,
        },
        "blocked_consumers": main["blocked_consumers"],
        "failures": failures,
        "controller_source_path": rel(SOURCE_PATH),
        "controller_source_sha256": sha256_file(SOURCE_PATH),
    }
    write_json(RESULT_PATH, envelope)
    return envelope


def main() -> int:
    envelope = build_envelope()
    print(
        json.dumps(
            {
                "all_pass": envelope["all_pass"],
                "max_divergence": envelope["divergence"]["max_divergence"],
                "failures": envelope["failures"],
                "out": rel(RESULT_PATH),
            },
            sort_keys=True,
        )
    )
    return 0 if envelope["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
