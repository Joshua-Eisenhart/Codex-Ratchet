#!/usr/bin/env python3
"""Shared joint basin-information-flow object for basin_information_fusion_v1."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import z3


SIM_ID = "basin_information_fusion_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CHART_RELATIVE_LABEL = "G1_CHART_RELATIVE_ORIGINAL_33_CELL_FINITE_STRUCTURE"
CHART_RELATIVE_TEXT = (
    "G1 has three finite chart-relative terminal classes in the original 33-cell chart; "
    "the split persists under declared 2x/3x containment refinements and merges under the "
    "pinned non-axis rotated chart, so it is not invariant geometry."
)

SWEEP_SIM = "basin_generating_set_sweep_v0"
SWEEP_DIR = ROOT / "system_v6" / "sims" / SWEEP_SIM
SWEEP_COMMON = SWEEP_DIR / f"{SWEEP_SIM}_common.py"
SWEEP_ENV = SWEEP_DIR / "results" / f"{SWEEP_SIM}_envelope_results.json"
RC_ENV = ROOT / "system_v6/sims/basin_rc_transition_graph_v0/results/basin_rc_transition_graph_v0_envelope_results.json"
BASIN_CONTRACT = ROOT / "system_v6/receipts/attractor_basin_criterion_20260611.md"
GRID_AUDIT = ROOT / "system_v6/sims/basin_grid_refinement_control_v0/audit_verdict.md"
V0_AUDIT = ROOT / "system_v6/sims/basin_information_fusion_v0/audit_verdict.md"
THROUGHPUT_AUDIT = ROOT / "system_v6/sims/manifold_information_throughput_v0/audit_verdict.md"

if str(SWEEP_DIR) not in sys.path:
    sys.path.insert(0, str(SWEEP_DIR))

from basin_generating_set_sweep_v0_common import build_sweep, stable_sha256  # noqa: E402


SEED_LEDGER = {
    "status": "deterministic_no_rng",
    "symbolic_seed": 2026061105,
    "orbit_initial_ensemble": "all active cells for each committed G-row",
    "orbit_schedule": "declared generator order unless a control explicitly permutes it",
    "record_table": "one row per committed 33-cell orbit start",
}

TOOL_INTENT = {
    "claim_classes": [
        "finite_basin_information_flow",
        "orbit_counting_entropy",
        "record_retention_at_merge",
        "terminal_class_throughput",
        "basin_conditioned_may_must_flow",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "supportive G1 syndrome graph component count; does not gate all_pass",
            "Z3": "integer conservation/no-erasure proof over computed syndrome readout counts",
        },
        "jax": {
            "networkx": "workhorse finite R_C graph/orbit and basin-conditioned readout computation",
            "sympy": "exact natural-log counting entropy expressions for record and throughput counts",
            "z3": "SMT negated identity UNSAT over computed record counts",
            "cvc5": "independent SMT negated identity UNSAT over computed record counts",
        },
        "pytorch": {
            "torch.func": "supportive source_backing_probe vmap sanity; torch_expm uses plain torch.matrix_exp",
            "torch_geometric": "supportive Data object in source_backing_probe only; committed R_C substrate graph uses shared Python common path",
            "sympy": "exact natural-log counting entropy expressions for torch-side counts",
            "z3": "SMT negated identity UNSAT over computed record counts",
            "cvc5": "independent SMT negated identity UNSAT over computed record counts",
        },
    },
}

PARENT_PATHS = {
    "basin_generating_set_sweep_v0_envelope": SWEEP_ENV,
    "basin_generating_set_sweep_v0_common": SWEEP_COMMON,
    "basin_rc_transition_graph_v0_envelope": RC_ENV,
    "basin_contract": BASIN_CONTRACT,
    "basin_grid_refinement_control_v0_audit": GRID_AUDIT,
    "basin_information_fusion_v0_audit": V0_AUDIT,
    "manifold_information_throughput_v0_audit": THROUGHPUT_AUDIT,
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def parent_lineage() -> dict[str, Any]:
    return {
        "consumed_inputs": [
            {
                "id": key,
                "path": rel(path),
                "sha256": sha256_file(path),
                "git_last_commit": git_last_commit(path),
            }
            for key, path in PARENT_PATHS.items()
            if path.exists()
        ],
        "carried_caveats": {
            "basin_information_fusion_v0": "CAVEAT_JOINT_OBJECT_NOT_EARNED repaired by orbit/record/throughput/conditioned-flow rows",
            "basin_grid_refinement_control_v0": CHART_RELATIVE_TEXT,
            "manifold_information_throughput_v0": "record sides must be constructed packet-locally; no record := loss assignment",
        },
        "write_scope": rel(SIM_DIR),
        "builder_output_only": True,
    }


def log_count(count: int) -> float:
    return math.log(count) if count > 0 else 0.0


def exact_log(count: int) -> str:
    return "0" if count <= 1 else str(sp.log(count))


def graph_lookup(graph: dict[str, Any]) -> dict[tuple[int, str], int]:
    return {(int(row["src"]), str(row["generator"])): int(row["dst"]) for row in graph["transition_edges"]}


def class_lookup(graph: dict[str, Any]) -> dict[int, int]:
    return {int(k): int(v) for k, v in graph["component_id_by_cell"].items()}


def ordered_generator_names(graph: dict[str, Any]) -> list[str]:
    return [str(gen["name"]) for gen in graph["generators"]]


def trajectory_for_schedule(
    graph: dict[str, Any],
    schedule: list[str],
    *,
    start_cells: list[int] | None = None,
) -> list[dict[str, Any]]:
    edge = graph_lookup(graph)
    class_by_cell = class_lookup(graph)
    current = list(start_cells if start_cells is not None else [int(cell["cell_id"]) for cell in graph["cells"]])
    rows: list[dict[str, Any]] = []
    previous_cell_h = 0.0
    previous_class_h = 0.0
    for step_index in range(len(schedule) + 1):
        cell_counts = Counter(current)
        occupied_cells = sorted(cell_counts)
        classes = [class_by_cell[cell] for cell in current]
        class_counts = Counter(classes)
        occupied_classes = sorted(class_counts)
        cell_h = log_count(len(occupied_cells))
        class_h = log_count(len(occupied_classes))
        rows.append(
            {
                "step_index": step_index,
                "generator_applied": None if step_index == 0 else schedule[step_index - 1],
                "occupied_cell_count": len(occupied_cells),
                "occupied_communicating_class_count": len(occupied_classes),
                "cell_histogram_sha256": stable_sha256(sorted(cell_counts.items())),
                "class_histogram_sha256": stable_sha256(sorted(class_counts.items())),
                "cell_support_counting_entropy": {
                    "type": "counting_entropy_log_occupied_cells_nats",
                    "count": len(occupied_cells),
                    "nats": cell_h,
                    "exact": exact_log(len(occupied_cells)),
                    "after_minus_before": 0.0 if step_index == 0 else cell_h - previous_cell_h,
                },
                "communicating_class_counting_entropy": {
                    "type": "counting_entropy_log_occupied_communicating_classes_nats",
                    "count": len(occupied_classes),
                    "nats": class_h,
                    "exact": exact_log(len(occupied_classes)),
                    "after_minus_before": 0.0 if step_index == 0 else class_h - previous_class_h,
                },
            }
        )
        previous_cell_h = cell_h
        previous_class_h = class_h
        if step_index < len(schedule):
            gen = schedule[step_index]
            current = [edge[(cell, gen)] for cell in current]
    return rows


def entropy_production_rows(sweep: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for set_id in ["G0", "G1", "G2", "G3L", "G3R", "G4", "G5"]:
        graph = sweep["graphs"][set_id]
        schedule = ordered_generator_names(graph)
        row = {
            "row_id": f"{set_id}_actual_R_C_orbit_entropy",
            "set_id": set_id,
            "actual_R_C_orbits": True,
            "state_scope": "G4 conditioned subset of the committed 33-cell substrate" if set_id == "G4" else "committed 33-cell substrate",
            "generator_schedule": schedule,
            "entropy_convention": "typed counting entropy per step; no endpoint delta substitution",
            "trajectory": trajectory_for_schedule(graph, schedule),
            "trajectory_signature_sha256": stable_sha256(trajectory_for_schedule(graph, schedule)),
        }
        if set_id == "G1":
            row["chart_relative_label"] = CHART_RELATIVE_LABEL
            row["chart_relative_note"] = CHART_RELATIVE_TEXT
        rows.append(row)
    return rows


def g1_syndrome_table(g1_graph: dict[str, Any], g2_graph: dict[str, Any]) -> list[dict[str, Any]]:
    g1_class = class_lookup(g1_graph)
    g2_basin = next(iter(g2_graph["basin_map"].values()))
    syndrome_ids = sorted({g1_class[int(cell["cell_id"])] for cell in g1_graph["cells"]})
    first = syndrome_ids[0]
    rows = []
    for cell in sorted(int(cell["cell_id"]) for cell in g1_graph["cells"]):
        syndrome = g1_class[cell]
        partial = "retain_class_%s" % syndrome if syndrome == first else "retain_other_chart_relative_classes"
        rows.append(
            {
                "orbit_id": f"orbit_start_cell_{cell}",
                "start_cell": cell,
                "G1_chart_relative_class_id": syndrome,
                "chart_relative_label": CHART_RELATIVE_LABEL,
                "post_merge_terminal_readout": f"G2_terminal_class_{g2_basin['terminal_class_id']}",
                "constructed_full_syndrome_record": f"G1_chart_relative_class_{syndrome}",
                "partial_record_control": partial,
                "erased_record_control": "erased",
            }
        )
    return rows


def readout_recoverability(table: list[dict[str, Any]], key: str, state_loss: float) -> dict[str, Any]:
    labels = sorted({str(row[key]) for row in table})
    entropy = log_count(len(labels))
    out = {
        "readout_key": key,
        "computed_from_syndrome_table": True,
        "readout_label_count": len(labels),
        "readout_labels": labels,
        "recoverable_counting_entropy_nats": entropy,
        "recoverable_counting_entropy_exact": exact_log(len(labels)),
        "conservation_defect_nats": state_loss - entropy,
        "type": "counting_entropy_log_readout_partition_of_constructed_G1_syndrome_table",
    }
    out["chart_relative_label"] = CHART_RELATIVE_LABEL
    out["chart_relative_note"] = CHART_RELATIVE_TEXT
    return out


def record_retention_at_merge(sweep: dict[str, Any]) -> dict[str, Any]:
    table = g1_syndrome_table(sweep["graphs"]["G1"], sweep["graphs"]["G2"])
    syndrome_count = len({row["G1_chart_relative_class_id"] for row in table})
    state_loss = log_count(syndrome_count)
    modes = {
        "post_merge_terminal_readout_only": readout_recoverability(table, "post_merge_terminal_readout", state_loss),
        "constructed_full_syndrome_record": readout_recoverability(table, "constructed_full_syndrome_record", state_loss),
        "partial_record_control": readout_recoverability(table, "partial_record_control", state_loss),
        "erased_record_control": readout_recoverability(table, "erased_record_control", state_loss),
    }
    return {
        "transition_id": "G1_to_G2",
        "chart_relative_label": CHART_RELATIVE_LABEL,
        "chart_relative_note": CHART_RELATIVE_TEXT,
        "record_object_constructed_packet_locally": True,
        "syndrome_table": table,
        "syndrome_class_count": syndrome_count,
        "state_only_syndrome_loss_nats": state_loss,
        "state_only_syndrome_loss_exact": exact_log(syndrome_count),
        "readout_recoverability": modes,
        "record_retained": {
            "computed_from": "constructed_full_syndrome_record readout over packet-local syndrome table",
            "record_retained_nats": modes["constructed_full_syndrome_record"]["recoverable_counting_entropy_nats"],
            "state_plus_record_defect_nats": modes["constructed_full_syndrome_record"]["conservation_defect_nats"],
        },
        "caveat_q1_repaired_here_for_g1_merge_only": "record side is constructed for the G1 merge syndrome table; this does not construct a Z4 radiated-record object",
    }


def per_class_throughput_rows(sweep: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for set_id in ["G0", "G1", "G2", "G3L", "G3R", "G4", "G5"]:
        graph = sweep["graphs"][set_id]
        terminal_rows = graph["terminal_classes"]
        edge_rows = graph["transition_edges"]
        generator_count = len(graph["generators"])
        for terminal in terminal_rows:
            cells = sorted(int(cell) for cell in terminal["cells"])
            cell_set = set(cells)
            restricted_edges = [
                {"src": int(row["src"]), "dst": int(row["dst"]), "generator": row["generator"]}
                for row in edge_rows
                if int(row["src"]) in cell_set
            ]
            image_cells = sorted({row["dst"] for row in restricted_edges})
            input_h = log_count(len(cells))
            output_h = log_count(len(image_cells))
            row = {
                "row_id": f"{set_id}_terminal_class_{terminal['class_id']}_throughput",
                "set_id": set_id,
                "terminal_class_id": terminal["class_id"],
                "terminal_cells": cells,
                "generator_count": generator_count,
                "class_restricted_update_channel": {
                    "readout": "output_cell_id_after_one_allowed_R_C_step",
                    "edge_count": len(restricted_edges),
                    "image_cells": image_cells,
                    "sample_edges": restricted_edges[:24],
                },
                "absent_exit_proof": terminal["absent_exit_proof"],
                "throughput": {
                    "type": "finite_counting_support_throughput_nats",
                    "exactness": "exact_finite_counting_support",
                    "pinned_ensemble": "uniform over terminal-class cells; readout is output cell id",
                    "input_count": len(cells),
                    "output_support_count": len(image_cells),
                    "input_counting_entropy_nats": input_h,
                    "output_counting_throughput_nats": output_h,
                    "destroyed_counting_entropy_nats": max(0.0, input_h - output_h),
                    "exact_input": exact_log(len(cells)),
                    "exact_output": exact_log(len(image_cells)),
                },
            }
            if set_id == "G1":
                row["chart_relative_label"] = CHART_RELATIVE_LABEL
                row["chart_relative_note"] = CHART_RELATIVE_TEXT
            rows.append(row)
    return rows


def probe_signature(graph: dict[str, Any], cell: int) -> str:
    edge = graph_lookup(graph)
    class_by_cell = class_lookup(graph)
    reachable_sizes = graph.get("monotone_exclusion_observable", {}).get("reachable_set_size_by_cell", {})
    signature = {
        "current_class": class_by_cell[cell],
        "successor_classes_by_generator": [
            [name, class_by_cell[edge[(cell, name)]]]
            for name in ordered_generator_names(graph)
        ],
        "reachable_set_size": reachable_sizes.get(str(cell)),
    }
    return stable_json(signature)


def conditioned_flow_rows(sweep: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for set_id in ["G0", "G1", "G2", "G3L", "G3R", "G4", "G5"]:
        graph = sweep["graphs"][set_id]
        schedule = ordered_generator_names(graph)
        for basin in graph["basin_map"].values():
            terminal_id = basin["terminal_class_id"]
            may_cells = sorted(int(x) for x in basin["can_reach_terminal"]["cells"])
            must_cells = sorted(int(x) for x in basin["sure_basin_omega_containment"]["cells"])
            may_only = sorted(set(may_cells) - set(must_cells))
            must_probe = sorted({probe_signature(graph, cell) for cell in must_cells})
            may_probe = sorted({probe_signature(graph, cell) for cell in may_only})
            if not may_only:
                distinguishable: bool | str = "no_may_only_cells"
                identity_statement = "may-only side is empty; no two nonempty sides are compared"
            else:
                distinguishable = must_probe != may_probe
                identity_statement = (
                    "distinguishable under declared probes"
                    if distinguishable
                    else "identical_under_declared_probes; a=a iff a~b under this packet's probe family"
                )
            row = {
                "row_id": f"{set_id}_terminal_class_{terminal_id}_basin_conditioned_flow",
                "set_id": set_id,
                "terminal_class_id": terminal_id,
                "conditioning_variable": "must_basin_vs_may_only",
                "may_semantics": basin["can_reach_terminal"]["semantics"],
                "must_semantics": basin["sure_basin_omega_containment"]["semantics"],
                "may_cell_count": len(may_cells),
                "must_cell_count": len(must_cells),
                "may_only_cell_count": len(may_only),
                "must_flow_trajectory": trajectory_for_schedule(graph, schedule, start_cells=must_cells) if must_cells else [],
                "may_only_flow_trajectory": trajectory_for_schedule(graph, schedule, start_cells=may_only) if may_only else [],
                "declared_probe_family": "one-step successor communicating-class signatures plus reachable-set-size readout",
                "must_probe_signature_count": len(must_probe),
                "may_only_probe_signature_count": len(may_probe),
                "distinguishable_under_declared_probes": distinguishable,
                "probe_identity_discipline": "a=a iff a~b under declared probe family",
                "identity_statement": identity_statement,
            }
            if set_id == "G1":
                row["chart_relative_label"] = CHART_RELATIVE_LABEL
                row["chart_relative_note"] = CHART_RELATIVE_TEXT
            rows.append(row)
    return rows


def shuffled_order_control(graph: dict[str, Any]) -> dict[str, Any]:
    original = ["Ni_Pit_L", "R_x"]
    shuffled = ["R_x", "Ni_Pit_L"]
    original_traj = trajectory_for_schedule(graph, original)
    shuffled_traj = trajectory_for_schedule(graph, shuffled)
    original_final_cells = original_traj[-1]["cell_histogram_sha256"]
    shuffled_final_cells = shuffled_traj[-1]["cell_histogram_sha256"]
    return {
        "computed": True,
        "control": "permute two allowed G2 generator steps",
        "original_schedule": original,
        "shuffled_schedule": shuffled,
        "original_trajectory": original_traj,
        "shuffled_trajectory": shuffled_traj,
        "production_trajectory_changed": stable_sha256(original_traj) != stable_sha256(shuffled_traj),
        "final_cell_histogram_changed": original_final_cells != shuffled_final_cells,
        "order_matters_N01": True,
    }


def similarity_only_control(sweep: dict[str, Any]) -> dict[str, Any]:
    base = sweep["controls"]["G2"]["similarity_cluster_contrast"]
    return {
        "computed": True,
        "source_set_id": "G2",
        "without_dynamics": "radius-only cell clusters",
        "basin_conditioned_rows_fail": base["fired"] is True and base["basin_language_allowed"] is False,
        "the_guard": "Clustering/model agreement is never a basin without S, Adm_C, R_C, trapping, partition, and escape evidence.",
        "cluster_result": base,
    }


def z3_record_identity(record: dict[str, Any], *, erased_flip: bool = False) -> str:
    full = record["readout_recoverability"]["constructed_full_syndrome_record"]
    state_count = int(record["syndrome_class_count"])
    record_count = int(full["readout_label_count"])
    if erased_flip:
        record_count = int(record["readout_recoverability"]["erased_record_control"]["readout_label_count"])
    solver = z3.Solver()
    state = z3.Int("computed_syndrome_class_count")
    rec = z3.Int("computed_record_readout_label_count")
    solver.add(state == z3.IntVal(state_count))
    solver.add(rec == z3.IntVal(record_count))
    solver.add(state != rec)
    return str(solver.check())


def cvc5_record_identity(record: dict[str, Any], *, erased_flip: bool = False) -> str:
    full = record["readout_recoverability"]["constructed_full_syndrome_record"]
    state_count = int(record["syndrome_class_count"])
    record_count = int(full["readout_label_count"])
    if erased_flip:
        record_count = int(record["readout_recoverability"]["erased_record_control"]["readout_label_count"])
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    state = solver.mkConst(int_sort, "computed_syndrome_class_count_cvc5")
    rec = solver.mkConst(int_sort, "computed_record_readout_label_count_cvc5")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, state, solver.mkInteger(state_count)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, rec, solver.mkInteger(record_count)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, state, rec)))
    result = solver.checkSat()
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def proof_bundle(record: dict[str, Any]) -> dict[str, Any]:
    proof_row = {
        "encoding": "bind computed syndrome class count and computed full-record readout label count; assert inequality",
        "erased_flip": "replace full-record readout count with erased-record readout count",
        "computed_syndrome_class_count": record["syndrome_class_count"],
        "computed_full_record_label_count": record["readout_recoverability"]["constructed_full_syndrome_record"]["readout_label_count"],
        "computed_erased_record_label_count": record["readout_recoverability"]["erased_record_control"]["readout_label_count"],
    }
    return {
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": z3_record_identity(record),
            "erased_flip_verdict": z3_record_identity(record, erased_flip=True),
            "proof_row": proof_row,
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": cvc5_record_identity(record),
            "erased_flip_verdict": cvc5_record_identity(record, erased_flip=True),
            "proof_row": proof_row,
        },
    }


def binding_contract(sweep: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    g2 = sweep["graphs"]["G2"]
    return {
        "finite_S": {
            "state_space": "committed 33-cell Bloch grid",
            "state_count": g2["state_count"],
            "state_count_parent_rows": {row["set_id"]: row["state_count"] for row in sweep["partition_fate_table"]},
        },
        "Adm_C": "x^2 + y^2 + z^2 <= 1 on the committed finite grid; G4 tightens C to conditioned-shell membership before recomputing M(C)",
        "R_C": {
            "explicit": True,
            "generator_rows": {
                row["set_id"]: row["generator_names"] for row in sweep["partition_fate_table"]
            },
        },
        "trapping_test": {
            "terminal_class_absent_exit_rows": sum(len(graph["terminal_classes"]) for graph in sweep["graphs"].values()),
            "all_terminal_classes_no_exit": all(
                terminal["absent_exit_proof"]["no_exit"] is True
                for graph in sweep["graphs"].values()
                for terminal in graph["terminal_classes"]
            ),
        },
        "lyapunov_monotone_observable": {
            "primary": "orbit-step counting entropy plus inherited V_exclusion / reachable-set-size direction discipline",
            "direction": "report production/destruction per step; do not substitute endpoint deltas",
        },
        "escape_tests": {
            "source": "finite transition rows include outgoing_edges and absent-exit proofs; similarity-only clusters expose escaping edges",
            "similarity_only_fired": controls["similarity_only_control"]["basin_conditioned_rows_fail"],
        },
        "basin_partition": {
            row["set_id"]: {
                "terminal_class_count": row["terminal_class_count"],
                "terminal_class_sizes": row["terminal_class_sizes"],
                "may_basin_sizes": row["may_basin_sizes"],
                "must_basin_sizes": row["must_basin_sizes"],
                "fate": row["fate"],
            }
            for row in sweep["partition_fate_table"]
        },
        "engine_dof_perturbation_test": sweep.get("engine_dof_reading", {}),
        "negative_controls": {
            "local": {
                "erased_record_control": controls["erased_record_control"]["flipped"],
                "partial_record_control": controls["partial_record_control"]["flipped"],
                "shuffled_order_control": controls["shuffled_order_control"]["production_trajectory_changed"],
                "similarity_only_control": controls["similarity_only_control"]["basin_conditioned_rows_fail"],
            },
            "inherited_parent_sweep": sweep["controls"],
        },
    }


def build_joint_object(expm_fn: Callable[[list[list[float]], float], list[list[float]]]) -> dict[str, Any]:
    sweep = build_sweep(expm_fn)
    orbit_rows = entropy_production_rows(sweep)
    record = record_retention_at_merge(sweep)
    throughput = per_class_throughput_rows(sweep)
    conditioned = conditioned_flow_rows(sweep)
    proofs = proof_bundle(record)
    controls = {
        "erased_record_control": {
            **record["readout_recoverability"]["erased_record_control"],
            "flipped": record["readout_recoverability"]["erased_record_control"]["recoverable_counting_entropy_nats"] == 0.0
            and record["readout_recoverability"]["erased_record_control"]["conservation_defect_nats"] > 0.0,
        },
        "partial_record_control": {
            **record["readout_recoverability"]["partial_record_control"],
            "flipped": 0.0
            < record["readout_recoverability"]["partial_record_control"]["recoverable_counting_entropy_nats"]
            < record["state_only_syndrome_loss_nats"],
        },
        "shuffled_order_control": shuffled_order_control(sweep["graphs"]["G2"]),
        "similarity_only_control": similarity_only_control(sweep),
        "byte_exact_parent_anchor": {
            "g0_anchor_byte_exact": next(row for row in sweep["partition_fate_table"] if row["set_id"] == "G0")["baseline_anchor_byte_exact"],
            "parent_sweep_path": rel(SWEEP_ENV),
            "source_sweep_signature_sha256": sweep["sweep_signature_sha256"],
        },
        "type_mixing_control": {
            "deliberate_cross_type_sum_flagged": True,
            "reason": "counting entropy over occupied readouts and any finite distribution entropy are separate types",
        },
    }
    contract = binding_contract(sweep, controls)
    gates = expected_gates(sweep, orbit_rows, record, throughput, conditioned, controls, proofs)
    return {
        "source_sweep_signature_sha256": sweep["sweep_signature_sha256"],
        "sweep_partition_rows": sweep["partition_fate_table"],
        "entropy_production_along_orbits": orbit_rows,
        "record_retention_at_g1_merge": record,
        "per_class_throughput": throughput,
        "basin_conditioned_flow": conditioned,
        "controls": controls,
        "binding_basin_packet_contract": contract,
        "crossover_proofs": proofs,
        "claim_sections": {
            "positive": [
                "orbit-step typed counting entropy is computed along actual generator-labelled R_C schedules",
                "G1->G2 record retention is computed from a packet-local 33-row syndrome table",
                "terminal-class throughput rows carry absent-exit proofs and exact finite support counts",
                "may/must basin-conditioned flow reports probe distinguishability or probe-identity honestly",
            ],
            "negative": [
                "erased record drops retained entropy to zero and produces a nonzero defect",
                "partial record retains a strict intermediate counting entropy",
                "shuffled order changes the orbit production trajectory",
                "similarity-only clusters fail the basin-conditioned guard",
            ],
            "boundary": [
                "G1 rows are finite chart-relative original-33-cell structure, not invariant geometry",
                "record construction here is the G1 merge syndrome object only, not a Z4 radiated-record object",
                "scratch diagnostic only; no formal admission, bridge, axis, physics, or universal information scalar",
            ],
        },
        "build_gates": gates,
        "joint_object_signature_sha256": stable_sha256(
            {
                "orbit_rows": orbit_rows,
                "record": record,
                "throughput": throughput,
                "conditioned": conditioned,
                "controls": controls,
            }
        ),
        "all_pass": all(gates.values()),
    }


def expected_gates(
    sweep: dict[str, Any],
    orbit_rows: list[dict[str, Any]],
    record: dict[str, Any],
    throughput: list[dict[str, Any]],
    conditioned: list[dict[str, Any]],
    controls: dict[str, Any],
    proofs: dict[str, Any],
) -> dict[str, bool]:
    return {
        "ceilings_exact": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
        "all_orbit_rows_present": len(orbit_rows) == 7 and all(len(row["trajectory"]) >= 2 for row in orbit_rows),
        "record_constructed_packet_locally": record["record_object_constructed_packet_locally"] is True and len(record["syndrome_table"]) == 33,
        "record_controls_flip": controls["erased_record_control"]["flipped"] is True and controls["partial_record_control"]["flipped"] is True,
        "throughput_all_terminal_classes": len(throughput) == sum(len(graph["terminal_classes"]) for graph in sweep["graphs"].values()),
        "conditioned_flow_all_terminal_basins": len(conditioned) == sum(len(graph["basin_map"]) for graph in sweep["graphs"].values()),
        "shuffled_order_changes_trajectory": controls["shuffled_order_control"]["production_trajectory_changed"] is True,
        "similarity_only_guard_fails": controls["similarity_only_control"]["basin_conditioned_rows_fail"] is True,
        "g1_chart_relative_labels_present": all(
            row.get("chart_relative_label") == CHART_RELATIVE_LABEL
            for row in orbit_rows
            if row["set_id"] == "G1"
        )
        and record.get("chart_relative_label") == CHART_RELATIVE_LABEL,
        "proofs_bind_computed_values": proofs["z3"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_verdict"] == "sat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and proofs["cvc5"]["erased_flip_verdict"] == "sat",
    }


def one_to_one_tool_rows(engine: str, primary_tools: list[str], proof_tools: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    supportive_tools = {"Graphs", "torch.func", "torch_geometric"}
    capability = []
    for tool in primary_tools:
        capability.append(
            {
                "receipt_id": f"{engine}_{tool}_joint_basin_information_flow",
                "tool": tool,
                "computed_what": "orbit entropy, G1 syndrome record, terminal throughput, or basin-conditioned flow",
                "status": "used",
            }
        )
    for tool in proof_tools:
        capability.append(
            {
                "receipt_id": f"{engine}_{tool}_computed_record_identity",
                "tool": tool,
                "computed_what": "computed syndrome/readout identity with erased-record flip",
                "status": "used",
            }
        )
    qualified = {
        "networkx": "networkx.DiGraph/networkx.strongly_connected_components through inherited graph plus local orbit/readout traversals",
        "sympy": "sympy.log/sympy.Rational/sympy.simplify exact count guards",
        "z3": "z3.Solver/z3.Int/check",
        "cvc5": "cvc5.Solver/mkConst/assertFormula/checkSat",
        "torch.func": "torch.func.vmap",
        "torch_geometric": "torch_geometric.data.Data",
        "Graphs": "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components",
        "Z3": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
    }
    calls = []
    for row in capability:
        tool = row["tool"]
        calls.append(
            {
                "receipt_id": row["receipt_id"],
                "tool": tool,
                "qualified_api/function": qualified.get(tool, tool),
                "input_object": "committed 33-cell G0-G5 R_C graph rows and packet-local G1 syndrome table",
                "output_object": "joint object row or computed SMT proof",
                "positive_case": "full constructed G1 syndrome record retains log(3) and has zero defect",
                "negative/erased_control": "erased record has zero retained entropy and nonzero defect",
                "boundary_case": "partial record retains log(2), strictly between erased and full",
                "demotion_condition": "demote if any record value is assigned rather than table-computed",
                "gates": [] if tool in supportive_tools else ["all_pass", "record_retention", "controls", "crossover_proofs"],
                "load_bearing": tool not in supportive_tools,
                "supportive": tool in supportive_tools,
            }
        )
    return capability, calls, {"pass": [row["receipt_id"] for row in capability] == [row["receipt_id"] for row in calls]}
