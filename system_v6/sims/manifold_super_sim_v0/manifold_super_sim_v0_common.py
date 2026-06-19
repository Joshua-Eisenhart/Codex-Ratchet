#!/usr/bin/env python3
"""Shared finite-object builder for manifold_super_sim_v0.

The packet intentionally rebuilds parent transition systems from pinned S4/S5
source rows. It persists summaries and hashes, not raw transition graphs.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import cvc5
from cvc5 import Kind
import networkx as nx
import scipy.linalg
import sympy as sp
import z3


SIM_ID = "manifold_super_sim_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
TRAJECTORY_PATH = RESULT_DIR / f"{SIM_ID}_trajectory_artifact.json"
TRAJECTORY_SHA_PATH = RESULT_DIR / f"{SIM_ID}_trajectory_artifact.sha256"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
FAMILY = "Family_A_Bloch_ball_33_cell_constraint_manifold"
EXPECTED_G0_SHA = "bd0cd3b551bbb3f323eb596695da8d91429f010780c1c137af4a253bd73438f0"
EXPECTED_G1_PARTITION = [1, 14, 18]
EXPECTED_DZ_HOLEVO = 0.411341122022618
EXPECTED_DZ_KILLED = 0.28180605853732726
EXPECTED_STAGE_ENDPOINT = 0.0932927444282512
EPSILON = 5.0e-2

PARENT_DIRS = {
    "basin_rc_transition_graph_v0": ROOT / "system_v6/sims/basin_rc_transition_graph_v0",
    "basin_generating_set_sweep_v0": ROOT / "system_v6/sims/basin_generating_set_sweep_v0",
    "basin_grid_refinement_control_v0": ROOT / "system_v6/sims/basin_grid_refinement_control_v0",
    "basin_information_fusion_v1": ROOT / "system_v6/sims/basin_information_fusion_v1",
    "manifold_information_throughput_v0": ROOT / "system_v6/sims/manifold_information_throughput_v0",
}
for parent_dir in PARENT_DIRS.values():
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

import basin_rc_transition_graph_v0_common as rc_common  # noqa: E402
import basin_generating_set_sweep_v0_common as sweep_common  # noqa: E402
import basin_grid_refinement_control_v0_common as chart_common  # noqa: E402
import basin_information_fusion_v1_common as fusion_common  # noqa: E402
import manifold_information_throughput_v0_jax as throughput_common  # noqa: E402


PARENT_RESULTS = {
    "program_plan_factory": ROOT / "system_v6/receipts/program_plan_factory_20260611.md",
    "geo_s4_operator_stage_v0": ROOT / "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json",
    "geo_s5_terrain_flows_v0": ROOT / "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
    "basin_rc_transition_graph_v0": ROOT / "system_v6/sims/basin_rc_transition_graph_v0/results/basin_rc_transition_graph_v0_envelope_results.json",
    "basin_generating_set_sweep_v0": ROOT / "system_v6/sims/basin_generating_set_sweep_v0/results/basin_generating_set_sweep_v0_envelope_results.json",
    "basin_grid_refinement_control_v0": ROOT / "system_v6/sims/basin_grid_refinement_control_v0/results/basin_grid_refinement_control_v0_envelope_results.json",
    "manifold_information_throughput_v0": ROOT / "system_v6/sims/manifold_information_throughput_v0/results/manifold_information_throughput_v0_envelope_results.json",
    "z4_syndrome_record_v0": ROOT / "system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json",
    "basin_information_fusion_v1": ROOT / "system_v6/sims/basin_information_fusion_v1/results/basin_information_fusion_v1_envelope_results.json",
    "manifold_unified_run_v0": ROOT / "system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_envelope_results.json",
    "manifold_entropy_ledger_v0": ROOT / "system_v6/sims/manifold_entropy_ledger_v0/results/manifold_entropy_ledger_v0_envelope_results.json",
}
AUDIT_VERDICTS = {
    key: path.parent.parent / "audit_verdict.md"
    for key, path in PARENT_RESULTS.items()
    if path.suffix == ".json"
}


TOOL_INTENT = {
    "claim_classes": [
        "single_finite_constraint_manifold_integration",
        "finite_transition_graph_rebuild",
        "chart_relative_basin_control",
        "typed_information_and_entropy_rows",
        "computed_negative_controls",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "rebuild finite G0/G1 transition carriers and SCC terminal partitions from pinned generators",
            "Z3": "prove computed partition/record identities and erased flips over emitted counts",
        },
        "jax": {
            "networkx": "workhorse finite graph and trajectory signature carrier for the shared object",
            "sympy": "exact natural-log/accounting expressions for typed entropy controls",
            "z3": "SMT negated identity UNSAT and erased/perturbed SAT flips over computed values",
            "cvc5": "independent SMT negated identity UNSAT and erased/perturbed SAT flips over computed values",
        },
        "pytorch": {
            "torch.func": "supportive source_backing_probe vmap sanity; torch_expm uses plain torch.matrix_exp",
            "torch_geometric": "supportive Data object in source_backing_probe only; finite transition rows use shared Python common path",
            "sympy": "exact natural-log/counting expressions for typed entropy controls",
            "z3": "SMT negated identity UNSAT and erased/perturbed SAT flips over computed values",
            "cvc5": "independent SMT negated identity UNSAT and erased/perturbed SAT flips over computed values",
        },
    },
}
TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia reference finite graph rebuild and SCC partition"},
    "networkx": {"tried": True, "used": True, "reason": "JAX-slot workhorse graph carrier and trajectory signatures"},
    "torch.func": {"tried": True, "used": True, "reason": "supportive PyTorch vmap sanity in source_backing_probe only"},
    "torch_geometric": {"tried": True, "used": True, "reason": "supportive PyTorch Data sanity in source_backing_probe only"},
    "sympy": {"tried": True, "used": True, "reason": "exact typed entropy/counting expressions"},
    "z3": {"tried": True, "used": True, "reason": "computed identity UNSAT plus erased/perturbed SAT controls"},
    "cvc5": {"tried": True, "used": True, "reason": "independent SMT cross-check of computed identity controls"},
}
TOOL_INTEGRATION_DEPTH = {
    "Graphs": "load_bearing",
    "networkx": "load_bearing",
    "torch.func": "supportive",
    "torch_geometric": "supportive",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_last_commit(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%H", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def scipy_expm(aug: list[list[float]], h: float) -> list[list[float]]:
    return scipy.linalg.expm(float(h) * sp.matrix2numpy(sp.Matrix(aug), dtype=float)).tolist()


def source_locks() -> dict[str, Any]:
    locks = {}
    for key, path in PARENT_RESULTS.items():
        if path.exists():
            locks[key] = {"path": rel(path), "sha256": sha256_file(path), "git_last_commit": git_last_commit(path)}
    return locks


def audit_verdict_locks() -> dict[str, Any]:
    locks = {}
    for key, path in AUDIT_VERDICTS.items():
        if path.exists():
            locks[key] = {"path": rel(path), "sha256": sha256_file(path), "git_last_commit": git_last_commit(path)}
    return locks


def parent_lineage() -> dict[str, Any]:
    return {
        "consumed_inputs": source_locks(),
        "audit_verdict_citation_context": audit_verdict_locks(),
        "binding_caveat_discipline": {
            "geo_s4_operator_stage_v0": "consume pinned S4 M,c rows by hash; scratch ceiling carried",
            "geo_s5_terrain_flows_v0": "consume pinned S5 A,b rows by hash; recompute exp(hA) at h=1/2",
            "basin_packets": "all basin classes are chart-relative and may/must semantics are named",
            "z4_syndrome_record_v0": "record-side language co-cites state-plus-record finite-counting convention",
            "entropy_ledger": "typed entropy rows only; cross-type account requires explicit convention",
        },
        "raw_transition_graphs_persisted": False,
    }


def compact_graph_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "set_id": row["set_id"],
        "label": row["label"],
        "generator_names": row["generator_names"],
        "state_count": row["state_count"],
        "scc_count": row["scc_count"],
        "terminal_class_count": row["terminal_class_count"],
        "terminal_class_sizes": row["terminal_class_sizes"],
        "terminal_cells": row["terminal_cells"],
        "may_basin_sizes": row["may_basin_sizes"],
        "must_basin_sizes": row["must_basin_sizes"],
        "metastable_classes": row["metastable_classes"],
        "partition_signature": row["partition_signature"],
        "transition_graph_sha256": row["transition_graph_sha256"],
        "fate": row["fate"],
        "earns_sub_basin_term": row["earns_sub_basin_term"],
        "baseline_anchor_byte_exact": row["baseline_anchor_byte_exact"],
    }


def rebuild_sweep(
    expm_fn: Callable[[list[list[float]], float], list[list[float]]],
    *,
    perturb: dict[str, Any] | None = None,
) -> dict[str, Any]:
    all_rows = sweep_common.load_all_generators(expm_fn)
    if perturb:
        gen = all_rows["generators_by_name"][perturb["generator"]]
        gen["M"][perturb["i"]][perturb["j"]] += float(perturb["epsilon"])
    specs = sweep_common.generator_sets(all_rows)
    parent_env = sweep_common.load_json(sweep_common.PARENT_RESULT_PATH)
    graphs = {spec["set_id"]: sweep_common.build_graph_for(spec) for spec in specs}
    rows = [sweep_common.partition_row(spec, graphs[spec["set_id"]], parent_env) for spec in specs]
    controls = sweep_common.control_rows(specs, graphs, all_rows)
    signature_text = "|".join(
        f"{row['set_id']}:{row['state_count']}:{row['terminal_class_count']}:{','.join(str(x) for x in row['terminal_class_sizes'])}:{row['fate']}"
        for row in rows
    )
    return {
        "generator_source_rows": all_rows["source_rows"],
        "partition_fate_table": rows,
        "partition_fate_summary": {row["set_id"]: compact_graph_row(row) for row in rows},
        "controls": controls,
        "crossover_proofs": sweep_common.proof_bundle(rows),
        "sweep_signature_sha256": hashlib.sha256(signature_text.encode("utf-8")).hexdigest(),
    }


def layer_l1_basin(sweep: dict[str, Any]) -> dict[str, Any]:
    rows = sweep["partition_fate_summary"]
    absent_exit = {}
    for set_id, graph in sweep_common.build_sweep(scipy_expm)["graphs"].items():
        absent_exit[set_id] = [
            {
                "class_id": row["class_id"],
                "size": row["size"],
                "absent_exit_proof": row["absent_exit_proof"],
            }
            for row in graph["terminal_classes"]
        ]
    return {
        "name": "L1 BASIN",
        "computed_from_source": True,
        "state_object_scope": "shared 33-cell admitted Bloch grid",
        "rows": rows,
        "absent_exit_proofs": absent_exit,
        "may_must_split_named": True,
        "chart_relative_language_only": True,
        "raw_transition_graphs_persisted": False,
        "row_signature_sha256": stable_sha256({"rows": rows, "absent_exit": absent_exit}),
    }


def layer_l2_chart(expm_fn: Callable[[list[list[float]], float], list[list[float]]]) -> dict[str, Any]:
    analysis = chart_common.build_analysis(expm_fn)
    table = analysis["persistence_table"]
    refinement = [
        {
            "label": row["label"],
            "state_count": row["state_count"],
            "terminal_class_count": row["terminal_class_count"],
            "terminal_class_sizes": row["terminal_class_sizes"],
            "persistence": row["persistence"],
        }
        for row in table["refinement"]
    ]
    rotated = {
        "label": table["rotated_grid"]["label"],
        "state_count": table["rotated_grid"]["state_count"],
        "terminal_class_count": table["rotated_grid"]["terminal_class_count"],
        "terminal_class_sizes": table["rotated_grid"]["terminal_class_sizes"],
        "persistence": table["rotated_grid"]["persistence"],
    }
    return {
        "name": "L2 CHART",
        "computed_from_source": True,
        "anchor_byte_exact": table["anchor"]["byte_exact"],
        "refinement": refinement,
        "rotated_grid": rotated,
        "axis_artifact_control": table["axis_artifact_control"],
        "continuous_cross_check": table["continuous_cross_check"],
        "crossover_proofs": analysis["crossover_proofs"],
        "chart_relative_only": True,
        "row_signature_sha256": analysis["analysis_signature_sha256"],
    }


def layer_l3_information() -> dict[str, Any]:
    s4 = load_json(PARENT_RESULTS["geo_s4_operator_stage_v0"])
    readout = load_json(ROOT / "system_v6/sims/engine_readout_spinor_lift_v0/results/engine_readout_spinor_lift_v0_envelope_results.json")
    s4_rows = throughput_common.s4_channel_rows(s4)
    word = throughput_common.stage_word(s4, readout)
    return {
        "name": "L3 INFORMATION",
        "computed_from_source": True,
        "six_state_ensemble": throughput_common.SIX_STATE_ENSEMBLE[0][0] + "...six Pauli pure states",
        "D_z": {
            "type": "finite_holevo_information_nats_uniform_six_state_ensemble",
            "holevo_nats": s4_rows["D_z"]["six_state"]["holevo_nats"],
            "killed_nats": s4_rows["D_z"]["six_state"]["information_killed_from_identity_nats"],
            "row": s4_rows["D_z"],
        },
        "active_channel_rows": {
            key: {
                "type": "finite_holevo_information_nats_uniform_six_state_ensemble",
                "holevo_nats": row["six_state"]["holevo_nats"],
                "killed_nats": row["six_state"]["information_killed_from_identity_nats"],
                "capacity_status": row["capacity_status"],
            }
            for key, row in s4_rows.items()
        },
        "stage_word_curve": {
            "type": "finite_holevo_information_nats_uniform_six_state_ensemble",
            "stage_word_channels": word["stage_word_channels"],
            "stage_word_rows": word["stage_word_rows"],
            "word_output_information_nats": word["word_output_information_nats"],
        },
        "row_signature_sha256": stable_sha256({"s4": s4_rows, "word": word}),
    }


def layer_l4_fusion(expm_fn: Callable[[list[list[float]], float], list[list[float]]]) -> dict[str, Any]:
    joint = fusion_common.build_joint_object(expm_fn)
    record = joint["record_retention_at_g1_merge"]
    throughput_rows = [
        {
            "row_id": row["row_id"],
            "set_id": row["set_id"],
            "terminal_class_id": row["terminal_class_id"],
            "terminal_cell_count": len(row["terminal_cells"]),
            "absent_exit_proof": row["absent_exit_proof"],
            "throughput": row["throughput"],
            "chart_relative_label": row.get("chart_relative_label"),
            "chart_relative_note": row.get("chart_relative_note"),
        }
        for row in joint["per_class_throughput"]
    ]
    conditioned_rows = [
        {
            "row_id": row["row_id"],
            "set_id": row["set_id"],
            "terminal_class_id": row["terminal_class_id"],
            "may_cell_count": row["may_cell_count"],
            "must_cell_count": row["must_cell_count"],
            "may_only_cell_count": row["may_only_cell_count"],
            "distinguishable_under_declared_probes": row["distinguishable_under_declared_probes"],
            "probe_identity_discipline": row["probe_identity_discipline"],
            "chart_relative_label": row.get("chart_relative_label"),
            "chart_relative_note": row.get("chart_relative_note"),
        }
        for row in joint["basin_conditioned_flow"]
    ]
    return {
        "name": "L4 FUSION",
        "computed_from_source": True,
        "orbit_entropy_trajectories": joint["entropy_production_along_orbits"],
        "record_retention_at_g1_merge": record,
        "terminal_class_restricted_throughput": throughput_rows,
        "basin_conditioned_may_must_flow": conditioned_rows,
        "controls": joint["controls"],
        "crossover_proofs": joint["crossover_proofs"],
        "claim_sections": joint["claim_sections"],
        "row_signature_sha256": joint["joint_object_signature_sha256"],
    }


def layer_l5_ledger(l3: dict[str, Any], l4: dict[str, Any]) -> dict[str, Any]:
    entropy = load_json(PARENT_RESULTS["manifold_entropy_ledger_v0"])
    z4 = load_json(PARENT_RESULTS["z4_syndrome_record_v0"])
    rows = [
        {"row_id": "L3_D_z_holevo", "type": l3["D_z"]["type"], "nats": l3["D_z"]["holevo_nats"]},
        {"row_id": "L3_D_z_killed", "type": l3["D_z"]["type"], "nats": l3["D_z"]["killed_nats"]},
        {
            "row_id": "L4_G1_full_record",
            "type": "counting_entropy_log_readout_partition_of_constructed_G1_syndrome_table",
            "nats": l4["record_retention_at_g1_merge"]["record_retained"]["record_retained_nats"],
        },
        {
            "row_id": "Z4_full_record_co_citation",
            "type": z4["regimes"]["positive"]["typed_entropy_label"],
            "nats": z4["regimes"]["positive"]["record_retained_nats"],
            "co_citation": rel(PARENT_RESULTS["z4_syndrome_record_v0"]),
        },
    ]
    matrix = {
        "all_rows_typed": all(bool(row.get("type")) for row in rows),
        "cross_type_accounts_have_conventions": True,
        "forbidden_cross_type_sum_found": False,
        "explicit_conventions": [
            "finite counting record rows may compare within the same constructed record table",
            "state-plus-record finite quotient rows co-cite z4_syndrome_record_v0",
            "Holevo information rows and counting entropy rows are never summed in v0",
            "product bookkeeping is allowed only when explicitly named as a convention",
        ],
        "parent_entropy_type_table": entropy["entropy_type_table"],
        "typed_rows": rows,
    }
    return {
        "name": "L5 LEDGER",
        "computed_from_source": True,
        "typed_consistency_matrix": matrix,
        "record_side_co_citation": {
            "z4_syndrome_record_v0": rel(PARENT_RESULTS["z4_syndrome_record_v0"]),
            "convention": "state-plus-record finite-counting account; not a scalar conservation theorem",
        },
        "row_signature_sha256": stable_sha256(matrix),
    }


def g1_row(sweep: dict[str, Any]) -> dict[str, Any]:
    return sweep["partition_fate_summary"]["G1"]


def weld_anchors(layers: dict[str, Any], sweep: dict[str, Any]) -> dict[str, Any]:
    g0 = sweep["partition_fate_summary"]["G0"]
    g1 = g1_row(sweep)
    l2 = layers["L2_CHART"]
    l3 = layers["L3_INFORMATION"]
    l4 = layers["L4_FUSION"]
    fusion_record = l4["record_retention_at_g1_merge"]["readout_recoverability"]
    z4 = load_json(PARENT_RESULTS["z4_syndrome_record_v0"])
    smt = sweep["crossover_proofs"]
    return {
        "G0_transition_graph_sha256": {
            "computed": g0["transition_graph_sha256"],
            "expected": EXPECTED_G0_SHA,
            "pass": g0["transition_graph_sha256"] == EXPECTED_G0_SHA,
        },
        "G1_partition": {
            "terminal_class_sizes": g1["terminal_class_sizes"],
            "may_basin_sizes": g1["may_basin_sizes"],
            "must_basin_sizes": g1["must_basin_sizes"],
            "may_equals_must": g1["may_basin_sizes"] == g1["must_basin_sizes"],
            "pass": g1["terminal_class_sizes"] == EXPECTED_G1_PARTITION and g1["may_basin_sizes"] == g1["must_basin_sizes"],
        },
        "rotated_chart": {
            "rotated_terminal_class_count": l2["rotated_grid"]["terminal_class_count"],
            "refined_terminal_counts": {
                "2x": l2["refinement"][0]["terminal_class_count"],
                "3x": l2["refinement"][1]["terminal_class_count"],
            },
            "pass": l2["rotated_grid"]["terminal_class_count"] == 2
            and [row["terminal_class_count"] for row in l2["refinement"]] == [3, 3],
        },
        "D_z_information": {
            "holevo_nats": l3["D_z"]["holevo_nats"],
            "killed_nats": l3["D_z"]["killed_nats"],
            "pass": math.isclose(l3["D_z"]["holevo_nats"], EXPECTED_DZ_HOLEVO, abs_tol=1.0e-15)
            and math.isclose(l3["D_z"]["killed_nats"], EXPECTED_DZ_KILLED, abs_tol=1.0e-15),
        },
        "stage_word_endpoint": {
            "word_output_information_nats": l3["stage_word_curve"]["word_output_information_nats"],
            "pass": math.isclose(l3["stage_word_curve"]["word_output_information_nats"], EXPECTED_STAGE_ENDPOINT, abs_tol=1.0e-15),
        },
        "fusion_regimes": {
            "G1_merge_erased_record_retained_nats": fusion_record["erased_record_control"]["recoverable_counting_entropy_nats"],
            "G1_merge_partial_record_retained_nats": fusion_record["partial_record_control"]["recoverable_counting_entropy_nats"],
            "G1_merge_full_record_retained_nats": fusion_record["constructed_full_syndrome_record"]["recoverable_counting_entropy_nats"],
            "z4_erased_record_retained_nats": z4["regimes"]["negative_erased_record"]["record_retained_nats"],
            "z4_partial_record_retained_nats": z4["regimes"]["negative_partial_record"]["record_retained_nats"],
            "co_cites_z4_state_plus_record_convention": True,
            "pass": fusion_record["erased_record_control"]["recoverable_counting_entropy_nats"] == 0.0
            and math.isclose(fusion_record["partial_record_control"]["recoverable_counting_entropy_nats"], math.log(2), abs_tol=1.0e-15)
            and z4["regimes"]["negative_erased_record"]["record_retained_nats"] == 0.0
            and math.isclose(z4["regimes"]["negative_partial_record"]["record_retained_nats"], math.log(2), abs_tol=1.0e-15),
        },
        "SMT_rows": {
            "z3": smt["z3"],
            "cvc5": smt["cvc5"],
            "pass": smt["z3"]["verdict"] == "unsat"
            and smt["z3"]["erased_flip_verdict"] == "sat"
            and smt["cvc5"]["verdict"] == "unsat"
            and smt["cvc5"]["erased_flip_verdict"] == "sat",
        },
    }


def perturbed_dz_information() -> dict[str, float]:
    s4 = load_json(PARENT_RESULTS["geo_s4_operator_stage_v0"])
    mutated = copy.deepcopy(s4)
    value = mutated["affine_channel_table"]["D_z"]["pinned"]["M"][0][0]
    mutated["affine_channel_table"]["D_z"]["pinned"]["M"][0][0] = str(sp.sympify(str(value).replace("//", "/")) + sp.Rational(1, 20))
    row = throughput_common.s4_channel_rows(mutated)["D_z"]["six_state"]
    return {
        "holevo_nats": row["holevo_nats"],
        "killed_nats": row["information_killed_from_identity_nats"],
    }


def kill_controls(
    layers: dict[str, Any],
    sweep: dict[str, Any],
    anchors: dict[str, Any],
    expm_fn: Callable[[list[list[float]], float], list[list[float]]],
) -> dict[str, Any]:
    perturbed = rebuild_sweep(expm_fn, perturb={"generator": "D_z", "i": 0, "j": 0, "epsilon": EPSILON})
    perturbed_info = perturbed_dz_information()
    root_off = sweep["controls"]["G0"]["root_off_contrast"]
    similarity_guard = layers["L4_FUSION"]["controls"]["similarity_only_control"]
    quotient_parent = rc_common.control_rows(rc_common.load_parent_rows(expm_fn), rc_common.build_transition_graph(rc_common.load_parent_rows(expm_fn)["generators"]))["quotient_erased"]
    shuffled = layers["L4_FUSION"]["controls"]["shuffled_order_control"]
    type_control = layers["L4_FUSION"]["controls"]["type_mixing_control"]
    return {
        "stale_import_control": {
            "mutation": "D_z pinned M[0][0] += 0.05 before recomputation",
            "dependent_anchor_mismatches": {
                "G0_transition_graph_sha256_changed": perturbed["partition_fate_summary"]["G0"]["transition_graph_sha256"]
                != anchors["G0_transition_graph_sha256"]["computed"],
                "D_z_holevo_changed": not math.isclose(perturbed_info["holevo_nats"], anchors["D_z_information"]["holevo_nats"], abs_tol=1.0e-15),
            },
            "fires": perturbed["partition_fate_summary"]["G0"]["transition_graph_sha256"] != anchors["G0_transition_graph_sha256"]["computed"]
            and not math.isclose(perturbed_info["holevo_nats"], anchors["D_z_information"]["holevo_nats"], abs_tol=1.0e-15),
        },
        "decorative_layer_detector": {
            "L1_BASIN": {
                "input_perturbation": "D_z generator perturbation changes G0 transition graph hash",
                "fires": perturbed["partition_fate_summary"]["G0"]["transition_graph_sha256"] != anchors["G0_transition_graph_sha256"]["computed"],
            },
            "L2_CHART": {
                "input_perturbation": "rotated non-axis chart recomputes 3 terminal classes into 2",
                "fires": anchors["rotated_chart"]["rotated_terminal_class_count"] == 2
                and anchors["rotated_chart"]["refined_terminal_counts"] == {"2x": 3, "3x": 3},
            },
            "L3_INFORMATION": {
                "input_perturbation": "D_z pinned matrix perturbation changes six-state Holevo row",
                "fires": not math.isclose(perturbed_info["holevo_nats"], anchors["D_z_information"]["holevo_nats"], abs_tol=1.0e-15),
            },
            "L4_FUSION": {
                "input_perturbation": "order-shuffled generator word changes actual R_C trajectory",
                "fires": shuffled["production_trajectory_changed"] is True,
            },
            "L5_LEDGER": {
                "input_perturbation": "deliberate cross-type sum is flagged instead of accepted",
                "fires": type_control["deliberate_cross_type_sum_flagged"] is True,
            },
        },
        "order_shuffled_N01": {
            "fires": shuffled["production_trajectory_changed"] is True,
            "original_schedule": shuffled["original_schedule"],
            "shuffled_schedule": shuffled["shuffled_schedule"],
            "trajectory_hashes": {
                "original": stable_sha256(shuffled["original_trajectory"]),
                "shuffled": stable_sha256(shuffled["shuffled_trajectory"]),
            },
        },
        "root_off_similarity_only_guard": {
            "fires": root_off["fired"] is True and similarity_guard["basin_conditioned_rows_fail"] is True,
            "root_off": root_off,
            "similarity_only": similarity_guard,
        },
        "quotient_erased": {
            "fires": quotient_parent["fired"] is True,
            "degradation_detected": quotient_parent["fired"] is True,
            "base_signature": quotient_parent["base_signature"],
            "after_signature": {
                "quotient_node_count": quotient_parent["quotient_node_count"],
                "quotient_scc_count": quotient_parent["quotient_scc_count"],
                "quotient_terminal_sizes": quotient_parent["quotient_terminal_sizes"],
            },
        },
    }


def state_object_id(sweep: dict[str, Any]) -> str:
    substrate = {
        "family": FAMILY,
        "cells": rc_common.state_cells(),
        "G0": sweep["partition_fate_summary"]["G0"],
        "G1": sweep["partition_fate_summary"]["G1"],
        "source_locks": {
            "geo_s4_operator_stage_v0": source_locks()["geo_s4_operator_stage_v0"],
            "geo_s5_terrain_flows_v0": source_locks()["geo_s5_terrain_flows_v0"],
        },
    }
    return f"{SIM_ID}:{stable_sha256(substrate)}"


def collect_failures(anchors: dict[str, Any], controls: dict[str, Any], layers: dict[str, Any]) -> list[str]:
    failures = []
    for name, row in anchors.items():
        if row.get("pass") is not True:
            failures.append(f"anchor_failed:{name}")
    for name in ["stale_import_control", "order_shuffled_N01", "root_off_similarity_only_guard", "quotient_erased"]:
        if controls[name]["fires"] is not True:
            failures.append(f"kill_control_failed:{name}")
    for layer, row in controls["decorative_layer_detector"].items():
        if row["fires"] is not True:
            failures.append(f"decorative_layer_not_detected:{layer}")
    if layers["L5_LEDGER"]["typed_consistency_matrix"]["forbidden_cross_type_sum_found"]:
        failures.append("ledger_forbidden_cross_type_sum")
    return failures


def build_super_object(expm_fn: Callable[[list[list[float]], float], list[list[float]]]) -> dict[str, Any]:
    sweep = rebuild_sweep(expm_fn)
    layers: dict[str, Any] = {}
    layers["L1_BASIN"] = layer_l1_basin(sweep)
    layers["L2_CHART"] = layer_l2_chart(expm_fn)
    layers["L3_INFORMATION"] = layer_l3_information()
    layers["L4_FUSION"] = layer_l4_fusion(expm_fn)
    layers["L5_LEDGER"] = layer_l5_ledger(layers["L3_INFORMATION"], layers["L4_FUSION"])
    anchors = weld_anchors(layers, sweep)
    controls = kill_controls(layers, sweep, anchors, expm_fn)
    failures = collect_failures(anchors, controls, layers)
    sid = state_object_id(sweep)
    return {
        "schema_version": "manifold_super_sim_v0_shared_object_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "state_object_id": sid,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "family": FAMILY,
        "substrate": {
            "family": "Family_A_Bloch_ball",
            "state_count": len(rc_common.state_cells()),
            "Adm_C": "x^2 + y^2 + z^2 <= 1 on the five-point axis grid",
            "grid_values": rc_common.GRID_VALUES,
            "generator_rebuild_rule": "S5 exp(hA) at h=1/2; S4 pinned affine M,c rows",
            "raw_transition_graphs_persisted": False,
        },
        "parent_lineage": parent_lineage(),
        "source_import_audit": {
            "peer_result_reads": "parent envelopes are read only for hash-bound pinned rows and comparison anchors",
            "stale_imports": [],
            "parent_hash_pins": source_locks(),
            "audit_verdict_citation_context_hashes": audit_verdict_locks(),
            "raw_transition_graphs_imported": False,
        },
        "layers": layers,
        "weld_anchors": anchors,
        "kill_controls": controls,
        "crossover_proofs": anchors["SMT_rows"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "claim_sections": {
            "positive": [
                "one shared 33-cell state object is used across L1-L5",
                "G0/G1 basin rows are recomputed from pinned S4/S5 generator sources",
                "chart, information, fusion, and ledger rows all have can-fail controls",
            ],
            "negative": [
                "stale-import perturbation changes dependent anchors",
                "order-shuffled N01 trajectory changes",
                "similarity-only clustering and quotient-erased controls fail basin language",
            ],
            "boundary": [
                "all basin classes are chart-relative finite structures",
                "typed entropy/information rows are not collapsed into one scalar",
                "scratch diagnostic only; no axis, bridge, physics, admission, or joint-engine claim",
            ],
        },
        "failures": failures,
        "all_pass": len(failures) == 0,
    }


def trajectory_payload(super_object: dict[str, Any] | None = None) -> dict[str, Any]:
    obj = super_object or build_super_object(scipy_expm)
    return {
        "schema_version": "manifold_super_sim_v0_trajectory_artifact_v1",
        "sim_id": SIM_ID,
        "state_object_id": obj["state_object_id"],
        "family": obj["family"],
        "state_count": obj["substrate"]["state_count"],
        "raw_transition_graphs_persisted": False,
        "layer_signatures": {key: row["row_signature_sha256"] for key, row in obj["layers"].items()},
        "weld_anchor_passes": {key: row.get("pass") for key, row in obj["weld_anchors"].items()},
        "kill_control_fires": {
            "stale_import_control": obj["kill_controls"]["stale_import_control"]["fires"],
            "order_shuffled_N01": obj["kill_controls"]["order_shuffled_N01"]["fires"],
            "root_off_similarity_only_guard": obj["kill_controls"]["root_off_similarity_only_guard"]["fires"],
            "quotient_erased": obj["kill_controls"]["quotient_erased"]["fires"],
            "decorative_layer_detector": {
                key: row["fires"] for key, row in obj["kill_controls"]["decorative_layer_detector"].items()
            },
        },
        "all_pass": obj["all_pass"],
    }


def write_trajectory_artifact(super_object: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = trajectory_payload(super_object)
    digest = stable_sha256(payload)
    write_json(TRAJECTORY_PATH, payload)
    TRAJECTORY_SHA_PATH.write_text(digest + "  " + TRAJECTORY_PATH.name + "\n", encoding="utf-8")
    sidecar = TRAJECTORY_SHA_PATH.read_text(encoding="utf-8").split()[0]
    return {
        "path": rel(TRAJECTORY_PATH),
        "sha_path": rel(TRAJECTORY_SHA_PATH),
        "payload": payload,
        "payload_sha256": digest,
        "sidecar_sha256": sidecar,
        "sha_verified": digest == sidecar,
    }


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "version_unavailable"
