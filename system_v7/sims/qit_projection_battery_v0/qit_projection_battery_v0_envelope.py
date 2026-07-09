#!/usr/bin/env python3
"""Three-engine envelope for qit_projection_battery_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qit_projection_battery_v0_common import (
    CLAIM_CEILING,
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULTS,
    SIM_DIR,
    SIM_ID,
    V1_ENVELOPE,
    now_z,
    read_json,
    rel,
    sha256_file,
    write_json,
)

SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULTS / f"{SIM_ID}_envelope_results.json"
COMMON_PATH = SIM_DIR / f"{SIM_ID}_common.py"

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


def engine_record(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    return {
        "ran": payload.get("ran", True),
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": rel(path),
        "result_sha256": sha256_file(path),
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
    view_values = {
        "julia": float(julia["view_count"]),
        "jax": float(jax["view_count"]),
        "pytorch": float(pytorch["view_count"]),
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
    if max_divergence(view_values) != 0.0:
        failures.append("engine view_count divergence")
    if not main["projection_policy"]["direct_identity_leakage_excluded"]:
        failures.append("nominal projection policy still uses direct identity leakage")
    if main["crossover_proofs"]["z3"]["verdict"] != "unsat":
        failures.append("main z3 projection gate not unsat")
    if main["crossover_proofs"]["cvc5"]["verdict"] != "unsat":
        failures.append("main cvc5 projection gate not unsat")
    if jax["solver_proofs"]["z3"]["verdict"] != "unsat":
        failures.append("jax z3 projection gate not unsat")
    if jax["solver_proofs"]["cvc5"]["verdict"] != "unsat":
        failures.append("jax cvc5 projection gate not unsat")
    if julia["julia_z3"]["verdict"] != "unsat":
        failures.append("julia z3 projection gate not unsat")
    if pytorch["learned_projection_readouts"]["nominal"]["mean_heldout_accuracy"] < 0.85:
        failures.append("pytorch learned nominal projection readout below gate")
    if V1_ENVELOPE.exists() is False:
        failures.append("parent v1 envelope missing")

    envelope = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "written_at": now_z(),
        "engine": "three_engine_envelope_controller",
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
            "The v1 finite object-card carrier supports partial MMM-style projection convergence across "
            "JAX/JAX-SMT, Julia graph/Z3, and PyTorch prototype-learning lanes, while erased controls stay at chance."
        ),
        "engine_contract": {
            "mode": "julia_graph_z3_jax_smt_pytorch_learned_projection_battery",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["controller_result", "julia_local", "jax_local", "pytorch_local", "envelope_comparison"],
            "lane_evidence": {
                "julia": "independent finite carrier recompute, object-view projection graph, and Julia Z3 gate",
                "jax": "independent projection records, vectorized heldout centroid readout, z3/cvc5 gate",
                "pytorch": "learned finite prototype readout plus torch.func jacrev/vmap sensitivity",
            },
        },
        "out_of_scope": [
            "Axis0 admission",
            "FEP admission",
            "production perception",
            "Lev mesh runtime integration",
            "remote peer graph mutation",
            "ontology writer admission",
            "MMM driver admission",
            "physics/manifold admission",
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
            "claim_classes": ["finite_projection_convergence", "erasure_control", "source_backed_three_engine_scout"],
            "engine_tool_intent": {
                "julia": {
                    "Graphs": "object-view projection graph must have five projection leaves per object and four components",
                    "Z3": "scaled projection-convergence gate negation must be UNSAT while erased controls are SAT",
                },
                "jax": {
                    "z3": "projection-convergence gate negation must be UNSAT with SAT erased controls",
                    "cvc5": "independent cvc5 gate must agree with z3 on the same measured values",
                },
                "pytorch": {
                    "torch.func": "jacrev/vmap gradient norms must be nonzero for the learned nominal projection readout",
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
                "claim": "nominal projection convergence gate is UNSAT under negation; erased controls are SAT/chance",
            },
            "cvc5": {
                "ran": True,
                "verdict": jax["solver_proofs"]["cvc5"]["verdict"],
                "load_bearing": True,
                "erased_control_verdict": jax["solver_proofs"]["cvc5"]["erased_control_verdict"],
                "claim": "independent cvc5 encoding agrees with z3 on projection battery polarity",
            },
            "julia_z3": julia["julia_z3"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "metric": "survivor_object_count",
            "max_divergence": max_divergence(engine_values),
            "view_values": view_values,
            "view_max_divergence": max_divergence(view_values),
        },
        "stability_pairs": {
            "nominal_vs_bag": {
                "nominal_mean": main["core_measurement"]["nominal"]["mean_heldout_accuracy"],
                "bag_mean": main["core_measurement"]["controls"]["bag_erased"]["mean_heldout_accuracy"],
            },
            "nominal_vs_view_erased": {
                "nominal_mean": main["core_measurement"]["nominal"]["mean_heldout_accuracy"],
                "view_erased_mean": main["core_measurement"]["controls"]["view_erased"]["mean_heldout_accuracy"],
            },
            "pytorch_nominal_vs_bag": {
                "nominal_mean": pytorch["learned_projection_readouts"]["nominal"]["mean_heldout_accuracy"],
                "bag_mean": pytorch["learned_projection_readouts"]["bag_erased_control"]["mean_heldout_accuracy"],
            },
        },
        "source_result_paths": {
            "main": rel(main_path),
            "julia": rel(julia_path),
            "jax": rel(jax_path),
            "pytorch": rel(pytorch_path),
        },
        "source_file_hashes": {
            "envelope_source": sha256_file(SOURCE_PATH),
            "common_source": sha256_file(COMMON_PATH),
            "main_source": main["source_sha256"],
            "julia_source": julia["source_sha256"],
            "jax_source": jax["source_sha256"],
            "pytorch_source": pytorch["source_sha256"],
        },
        "parent_lineage": {
            "parent_sim_id": "qit_full_type1_type2_64_live_v1",
            "parent_envelope": rel(V1_ENVELOPE),
            "parent_envelope_sha256": sha256_file(V1_ENVELOPE) if V1_ENVELOPE.exists() else None,
            "common_source_path": rel(COMMON_PATH),
            "common_source_sha256": sha256_file(COMMON_PATH),
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
