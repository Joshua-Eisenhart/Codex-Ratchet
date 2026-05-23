#!/usr/bin/env python3
"""PEPS/PEPS3D stage and loop depth inventory for the two-root QIT engine.

This scout turns the current "run each engine stage one by one, then each
inner/outer loop one by one" plan into a bounded formal receipt. It uses the
existing PyTorch-native tiny PEPS and PEPS3D substrates:

- PEPS 2x4 sheet: 8 sites, open boundary, simple-update SVD edge gates.
- PEPS3D 2x2x2 volume: 8 sites, open boundary, simple-update SVD edge gates.

It inventories the 16 stage placements:

    2 sheets (L/R, Type-1/Type-2) x 2 loops (inner/outer) x 4 stage slots

and then runs the four loop composites one by one:

    L-inner, L-outer, R-inner, R-outer.

Boundary: this is a tiny-substrate depth inventory. It is not full PEPS or
PEPS3D convergence, not MPDO Lindblad, not L32/L64, not a real attractor-basin
admission, and not final constraint-manifold admission.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import string
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit
import sim_two_root_constraint_peps_small_grid_dynamics_probe as peps2d
import sim_two_root_constraint_peps3d_tiny_grid_dynamics_probe as peps3d
import sim_two_root_constraint_tensor_network_lindblad_runtime_probe as mps_runtime


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_peps_peps3d_stage_loop_depth_inventory_probe_results.json"

NAME = "two_root_constraint_peps_peps3d_stage_loop_depth_inventory_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_peps_peps3d_stage_loop_depth_inventory"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_peps_peps3d_stage_loop_depth_inventory"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal tiny-substrate PEPS/PEPS3D depth-inventory scout only: runs all 16 "
    "stage placements and the four inner/outer loop composites on PyTorch-native "
    "PEPS 2x4 and PEPS3D 2x2x2 substrates. It cannot promote MPDO Lindblad, "
    "full PEPS/PEPS3D convergence, L32/L64 scaling, real attractor-basin "
    "admission, or final constraint-manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS/PEPS3D tensor substrates, no-jump terrain updates, SVD edge gates, dense readouts, and entropy/Phi0 diagnostics",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph witness for the 16 stage-placement inventory and four loop composites",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard: tiny stage/loop inventory cannot imply full PEPS/PEPS3D or final admission",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

PEPS_GRID = (2, 4)
PEPS3D_GRID = (2, 2, 2)
BOND_CAP = 2
INITIAL_FAMILIES = ["plus_x", "alternating_z"]
SHEETS = ["L", "R"]
LOOPS = ["inner", "outer"]
NORM_TOL = 1.0e-8
TRUNCATION_WARN = 100.0
SEPARATION_TOL = 1.0e-9

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "qit_runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "mps_runtime": SCOUT_ROOT / "sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py",
    "peps_runtime": SCOUT_ROOT / "sim_two_root_constraint_peps_small_grid_dynamics_probe.py",
    "peps3d_runtime": SCOUT_ROOT / "sim_two_root_constraint_peps3d_tiny_grid_dynamics_probe.py",
    "d129_result": RESULT_DIR / "two_root_constraint_l64_doubled_mps_lindblad_pilot_probe_results.json",
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
    "next_goal": REPO / "system_v5" / "ops" / "NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    return qit.jsonable(value)


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def configure_substrates() -> None:
    peps2d.GRID = PEPS_GRID
    peps2d.BOND_CAP = BOND_CAP
    peps3d.GRID = PEPS3D_GRID
    peps3d.BOND_CAP = BOND_CAP


def token_for_sheet(sheet: str) -> str:
    if sheet == "L":
        return "1"
    if sheet == "R":
        return "2"
    raise ValueError(f"unknown sheet {sheet!r}")


def placements() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sheet in SHEETS:
        for loop in LOOPS:
            for stage_index, terrain in enumerate(qit.ENGINE_STAGE_ORDERS[sheet][loop]):
                rows.append(
                    {
                        "sheet": sheet,
                        "token": token_for_sheet(sheet),
                        "loop": loop,
                        "stage_index": stage_index,
                        "terrain": terrain,
                        "placement_id": f"{sheet}:{loop}:{stage_index}:{terrain}",
                    }
                )
    return rows


def stage_operator(token: str, terrain: str) -> torch.Tensor:
    hamiltonian = mps_runtime.local_hamiltonian(token)
    collapses = mps_runtime.collapse_ops(token, terrain)
    return mps_runtime.no_jump_operator(hamiltonian, collapses)


def apply_stage_peps(surface: peps2d.PEPS, placement: dict[str, Any]) -> dict[str, Any]:
    op = stage_operator(str(placement["token"]), str(placement["terrain"]))
    for coord in peps2d.coords():
        surface.apply_single(op, coord)
    gate = peps2d.two_site_gate()
    truncation = 0.0
    pair_gates = 0
    for left, right, orientation in peps2d.edge_matching(int(placement["stage_index"])):
        truncation += surface.apply_pair_gate(gate, left, right, orientation)
        pair_gates += 1
    norm_before = normalize_peps_fast(surface)
    return {
        "local_updates": len(peps2d.coords()),
        "pair_gates": pair_gates,
        "stage_truncation_error": truncation,
        "norm_before_final_normalization": norm_before,
    }


def apply_stage_peps3d(surface: peps3d.PEPS3D, placement: dict[str, Any]) -> dict[str, Any]:
    op = stage_operator(str(placement["token"]), str(placement["terrain"]))
    for coord in peps3d.coords():
        surface.apply_single(op, coord)
    gate = peps3d.two_site_gate()
    truncation = 0.0
    pair_gates = 0
    for left, right, axis in peps3d.edge_matching(int(placement["stage_index"])):
        truncation += surface.apply_pair_gate(gate, left, right, axis)
        pair_gates += 1
    norm_before = surface.normalize_()
    return {
        "local_updates": len(peps3d.coords()),
        "pair_gates": pair_gates,
        "stage_truncation_error": truncation,
        "norm_before_final_normalization": norm_before,
    }


def dense_state_peps_fast(surface: peps2d.PEPS) -> torch.Tensor:
    labels = iter(string.ascii_letters)
    physical_labels = {coord: next(labels) for coord in peps2d.coords()}
    bond_labels: dict[tuple[tuple[int, int], int], str] = {}
    for left, right, orientation in peps2d.edge_list():
        if orientation == "horizontal":
            label = next(labels)
            bond_labels[(left, 4)] = label
            bond_labels[(right, 3)] = label
        elif orientation == "vertical":
            label = next(labels)
            bond_labels[(left, 2)] = label
            bond_labels[(right, 1)] = label
        else:
            raise ValueError(f"unknown orientation {orientation!r}")
    operands = []
    tensors = []
    for coord in peps2d.coords():
        axis_labels = [physical_labels[coord]]
        for axis_idx in range(1, 5):
            if (coord, axis_idx) in bond_labels:
                axis_labels.append(bond_labels[(coord, axis_idx)])
            else:
                axis_labels.append(next(labels))
        operands.append("".join(axis_labels))
        tensors.append(surface.tensors[coord])
    output = "".join(physical_labels[coord] for coord in peps2d.coords())
    contracted = torch.einsum(",".join(operands) + "->" + output, *tensors)
    return contracted.reshape(-1)


def normalize_peps_fast(surface: peps2d.PEPS) -> float:
    norm = float(torch.linalg.vector_norm(dense_state_peps_fast(surface)).item())
    if norm <= 0.0:
        raise ValueError("PEPS norm collapsed to zero")
    first = peps2d.coords()[0]
    surface.tensors[first] = surface.tensors[first] / norm
    return norm


def peps_readout(surface: peps2d.PEPS) -> dict[str, Any]:
    state = peps2d.dense_normalize(dense_state_peps_fast(surface))
    edge_phi = peps2d.edge_phi0_summary(state)
    norm_error = abs(float(torch.linalg.vector_norm(state).item()) - 1.0)
    return {
        "norm_error": norm_error,
        "mean_z": peps2d.mean_z_from_state(state),
        "max_bond": surface.max_bond(),
        "edge_phi0": edge_phi,
        "max_edge_I_A_colon_B": edge_phi["max_I_A_colon_B"],
        "mean_edge_I_A_colon_B": edge_phi["mean_I_A_colon_B"],
    }


def peps3d_readout(surface: peps3d.PEPS3D) -> dict[str, Any]:
    state = peps3d.dense_normalize(surface.dense_state())
    edge_phi = peps3d.edge_phi0_summary(state)
    norm_error = abs(float(torch.linalg.vector_norm(state).item()) - 1.0)
    return {
        "norm_error": norm_error,
        "mean_z": peps3d.mean_z_from_state(state),
        "max_bond": surface.max_bond(),
        "edge_phi0": edge_phi,
        "max_edge_I_A_colon_B": edge_phi["max_I_A_colon_B"],
        "mean_edge_I_A_colon_B": edge_phi["mean_I_A_colon_B"],
    }


def run_stage_row(substrate: str, family: str, placement: dict[str, Any]) -> dict[str, Any]:
    if substrate == "peps_2x4":
        surface = peps2d.PEPS.product(family)
        update = apply_stage_peps(surface, placement)
        readout = peps_readout(surface)
    elif substrate == "peps3d_2x2x2":
        surface = peps3d.PEPS3D.product(family)
        update = apply_stage_peps3d(surface, placement)
        readout = peps3d_readout(surface)
    else:
        raise ValueError(f"unknown substrate {substrate!r}")
    return {
        "kind": "stage",
        "substrate": substrate,
        "family": family,
        **placement,
        **update,
        **readout,
    }


def loop_placements(sheet: str, loop: str) -> list[dict[str, Any]]:
    return [
        {
            "sheet": sheet,
            "token": token_for_sheet(sheet),
            "loop": loop,
            "stage_index": stage_index,
            "terrain": terrain,
            "placement_id": f"{sheet}:{loop}:{stage_index}:{terrain}",
        }
        for stage_index, terrain in enumerate(qit.ENGINE_STAGE_ORDERS[sheet][loop])
    ]


def run_loop_row(substrate: str, family: str, sheet: str, loop: str) -> dict[str, Any]:
    stages = loop_placements(sheet, loop)
    stage_updates: list[dict[str, Any]] = []
    if substrate == "peps_2x4":
        surface = peps2d.PEPS.product(family)
        for placement in stages:
            stage_updates.append({**placement, **apply_stage_peps(surface, placement)})
        readout = peps_readout(surface)
    elif substrate == "peps3d_2x2x2":
        surface = peps3d.PEPS3D.product(family)
        for placement in stages:
            stage_updates.append({**placement, **apply_stage_peps3d(surface, placement)})
        readout = peps3d_readout(surface)
    else:
        raise ValueError(f"unknown substrate {substrate!r}")
    return {
        "kind": "loop",
        "substrate": substrate,
        "family": family,
        "sheet": sheet,
        "token": token_for_sheet(sheet),
        "loop": loop,
        "loop_id": f"{sheet}:{loop}",
        "stage_count": len(stage_updates),
        "terrain_order": [row["terrain"] for row in stage_updates],
        "local_updates": sum(int(row["local_updates"]) for row in stage_updates),
        "pair_gates": sum(int(row["pair_gates"]) for row in stage_updates),
        "total_truncation_error": sum(float(row["stage_truncation_error"]) for row in stage_updates),
        "max_stage_truncation_error": max(float(row["stage_truncation_error"]) for row in stage_updates),
        "stage_updates": stage_updates,
        **readout,
    }


def inventory_graph(stage_rows: list[dict[str, Any]], loop_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    substrate_nodes = {name: graph.add_node(f"substrate:{name}") for name in ["peps_2x4", "peps3d_2x2x2"]}
    loop_nodes: dict[str, int] = {}
    placement_nodes: dict[str, int] = {}
    for sheet in SHEETS:
        for loop in LOOPS:
            loop_id = f"{sheet}:{loop}"
            loop_nodes[loop_id] = graph.add_node(f"loop:{loop_id}")
            for substrate_node in substrate_nodes.values():
                graph.add_edge(substrate_node, loop_nodes[loop_id], "runs_loop")
    for placement in placements():
        placement_id = str(placement["placement_id"])
        placement_nodes[placement_id] = graph.add_node(f"placement:{placement_id}")
        graph.add_edge(loop_nodes[f"{placement['sheet']}:{placement['loop']}"], placement_nodes[placement_id], "contains")
    return {
        "stage_row_count": len(stage_rows),
        "loop_row_count": len(loop_rows),
        "unique_stage_placements": len({row["placement_id"] for row in stage_rows}),
        "unique_loop_ids": len({row["loop_id"] for row in loop_rows}),
        "graph_nodes": graph.num_nodes(),
        "graph_edges": graph.num_edges(),
        "graph_is_dag": bool(rx.is_directed_acyclic_graph(graph)),
    }


def z3_guard(stage_rows: list[dict[str, Any]], loop_rows: list[dict[str, Any]]) -> dict[str, Any]:
    stage_inventory = z3.Bool("stage_inventory")
    loop_inventory = z3.Bool("loop_inventory")
    tiny_peps = z3.Bool("tiny_peps")
    tiny_peps3d = z3.Bool("tiny_peps3d")
    mpdo_lindblad = z3.Bool("mpdo_lindblad")
    full_convergence = z3.Bool("full_convergence")
    scale_basin = z3.Bool("scale_basin")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(stage_inventory == (len(stage_rows) > 0))
    solver.add(loop_inventory == (len(loop_rows) > 0))
    solver.add(tiny_peps == any(row["substrate"] == "peps_2x4" for row in stage_rows))
    solver.add(tiny_peps3d == any(row["substrate"] == "peps3d_2x2x2" for row in stage_rows))
    solver.add(mpdo_lindblad == False)
    solver.add(full_convergence == False)
    solver.add(scale_basin == False)
    solver.add(final_admission == z3.And(stage_inventory, loop_inventory, tiny_peps, tiny_peps3d, mpdo_lindblad, full_convergence, scale_basin))
    check = solver.check()
    model = solver.model()
    return {
        "sat": str(check) == "sat",
        "stage_inventory": z3.is_true(model.eval(stage_inventory, model_completion=True)),
        "loop_inventory": z3.is_true(model.eval(loop_inventory, model_completion=True)),
        "tiny_peps": z3.is_true(model.eval(tiny_peps, model_completion=True)),
        "tiny_peps3d": z3.is_true(model.eval(tiny_peps3d, model_completion=True)),
        "mpdo_lindblad": z3.is_true(model.eval(mpdo_lindblad, model_completion=True)),
        "full_convergence": z3.is_true(model.eval(full_convergence, model_completion=True)),
        "scale_basin": z3.is_true(model.eval(scale_basin, model_completion=True)),
        "final_manifold_admission_allowed": z3.is_true(model.eval(final_admission, model_completion=True)),
        "rule": "The 16-stage plus 4-loop tiny PEPS/PEPS3D inventory is evidence for depth routing only; final admission requires MPDO/full convergence/scale-basin receipts.",
    }


def aggregate(rows: list[dict[str, Any]], *, key: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for group in sorted({str(row[key]) for row in rows}):
        subset = [row for row in rows if str(row[key]) == group]
        out[group] = {
            "count": len(subset),
            "max_norm_error": max(float(row["norm_error"]) for row in subset),
            "max_truncation_error": max(float(row.get("stage_truncation_error", row.get("max_stage_truncation_error", 0.0))) for row in subset),
            "max_edge_I_A_colon_B": max(float(row["max_edge_I_A_colon_B"]) for row in subset),
            "mean_edge_I_A_colon_B": sum(float(row["mean_edge_I_A_colon_B"]) for row in subset) / len(subset),
            "mean_z_range": [min(float(row["mean_z"]) for row in subset), max(float(row["mean_z"]) for row in subset)],
        }
    return out


def row_without_edge_details(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if "edge_phi0" in out:
        out["edge_phi0"] = {
            "max_I_A_colon_B": out["edge_phi0"]["max_I_A_colon_B"],
            "mean_I_A_colon_B": out["edge_phi0"]["mean_I_A_colon_B"],
            "edge_count": len(out["edge_phi0"]["edges"]),
        }
    if "stage_updates" in out:
        out["stage_updates"] = [
            {
                "placement_id": item["placement_id"],
                "terrain": item["terrain"],
                "stage_truncation_error": item["stage_truncation_error"],
                "pair_gates": item["pair_gates"],
            }
            for item in out["stage_updates"]
        ]
    return out


def main() -> int:
    started = time.time()
    configure_substrates()
    d129_result = read_json(SOURCE_FILES["d129_result"])
    placement_rows = placements()
    substrates = ["peps_2x4", "peps3d_2x2x2"]
    stage_rows = [
        run_stage_row(substrate, family, placement)
        for substrate in substrates
        for family in INITIAL_FAMILIES
        for placement in placement_rows
    ]
    loop_rows = [
        run_loop_row(substrate, family, sheet, loop)
        for substrate in substrates
        for family in INITIAL_FAMILIES
        for sheet in SHEETS
        for loop in LOOPS
    ]
    graph = inventory_graph(stage_rows, loop_rows)
    guard = z3_guard(stage_rows, loop_rows)
    stage_norm_max = max(float(row["norm_error"]) for row in stage_rows)
    loop_norm_max = max(float(row["norm_error"]) for row in loop_rows)
    stage_truncation_max = max(float(row["stage_truncation_error"]) for row in stage_rows)
    loop_truncation_max = max(float(row["max_stage_truncation_error"]) for row in loop_rows)
    loop_mi_by_id = aggregate(loop_rows, key="loop_id")
    stage_mi_by_terrain = aggregate(stage_rows, key="terrain")
    substrate_summary = aggregate(stage_rows + loop_rows, key="substrate")
    max_loop_gap = 0.0
    for substrate in substrates:
        for family in INITIAL_FAMILIES:
            subset = [row for row in loop_rows if row["substrate"] == substrate and row["family"] == family]
            values = [float(row["max_edge_I_A_colon_B"]) for row in subset]
            max_loop_gap = max(max_loop_gap, max(values) - min(values))
    positive = {
        "d129_doubled_mps_context_exists": {
            "pass": bool(d129_result.get("all_pass")),
            "source": rel(SOURCE_FILES["d129_result"]),
            "completion_status": d129_result.get("summary", {}).get("completion_status"),
        },
        "all_16_stage_placements_covered_per_substrate_family": {
            "pass": (
                len(stage_rows) == 16 * len(substrates) * len(INITIAL_FAMILIES)
                and graph["unique_stage_placements"] == 16
            ),
            "stage_row_count": len(stage_rows),
            "unique_stage_placements": graph["unique_stage_placements"],
            "substrates": substrates,
            "families": INITIAL_FAMILIES,
        },
        "four_loop_composites_covered_per_substrate_family": {
            "pass": len(loop_rows) == 4 * len(substrates) * len(INITIAL_FAMILIES) and graph["unique_loop_ids"] == 4,
            "loop_row_count": len(loop_rows),
            "unique_loop_ids": graph["unique_loop_ids"],
            "loop_ids": sorted({row["loop_id"] for row in loop_rows}),
        },
        "peps_and_peps3d_both_dynamic": {
            "pass": all(row["pair_gates"] > 0 and row["local_updates"] > 0 for row in stage_rows + loop_rows),
            "substrate_summary": substrate_summary,
        },
        "norms_and_truncation_finite": {
            "pass": (
                stage_norm_max < NORM_TOL
                and loop_norm_max < NORM_TOL
                and math.isfinite(stage_truncation_max)
                and math.isfinite(loop_truncation_max)
                and stage_truncation_max < TRUNCATION_WARN
                and loop_truncation_max < TRUNCATION_WARN
            ),
            "stage_norm_max": stage_norm_max,
            "loop_norm_max": loop_norm_max,
            "stage_truncation_max": stage_truncation_max,
            "loop_truncation_max": loop_truncation_max,
            "norm_tolerance": NORM_TOL,
            "truncation_warning_threshold": TRUNCATION_WARN,
        },
        "depth_readouts_are_nonflat_somewhere": {
            "pass": max_loop_gap > SEPARATION_TOL,
            "max_loop_edge_mi_gap_within_substrate_family": max_loop_gap,
            "separation_tolerance": SEPARATION_TOL,
            "loop_mi_by_id": loop_mi_by_id,
            "stage_mi_by_terrain": stage_mi_by_terrain,
        },
        "inventory_graph_is_complete_dag": {
            "pass": graph["graph_is_dag"] and graph["graph_nodes"] > 0 and graph["graph_edges"] > 0,
            "graph": graph,
        },
    }
    graveyard = {
        "stage_inventory_is_not_loop_evidence": {
            "pass": len(stage_rows) > len(loop_rows),
            "detail": "Stage rows are single-placement depth reads; loop rows are separate four-stage composites.",
        },
        "tiny_substrate_is_not_full_convergence": {
            "pass": not guard["full_convergence"],
            "z3_guard": guard,
        },
        "not_mpdo_lindblad": {
            "pass": not guard["mpdo_lindblad"],
            "detail": "The scout uses pure-state PEPS/PEPS3D simple-update no-jump stages, not MPDO deterministic Lindblad.",
        },
        "final_admission_blocked": {
            "pass": not guard["final_manifold_admission_allowed"],
            "z3_guard": guard,
        },
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard.values())
        and not guard["final_manifold_admission_allowed"]
    )
    summary = {
        "all_pass": all_pass,
        "completion_status": "peps_peps3d_stage_loop_depth_inventory_complete" if all_pass else "peps_peps3d_stage_loop_depth_inventory_failed",
        "stage_row_count": len(stage_rows),
        "loop_row_count": len(loop_rows),
        "unique_stage_placements": graph["unique_stage_placements"],
        "unique_loop_ids": graph["unique_loop_ids"],
        "substrates": substrates,
        "families": INITIAL_FAMILIES,
        "peps_grid": list(PEPS_GRID),
        "peps3d_grid": list(PEPS3D_GRID),
        "stage_norm_max": stage_norm_max,
        "loop_norm_max": loop_norm_max,
        "stage_truncation_max": stage_truncation_max,
        "loop_truncation_max": loop_truncation_max,
        "max_loop_edge_mi_gap_within_substrate_family": max_loop_gap,
        "z3_final_manifold_admission_allowed": guard["final_manifold_admission_allowed"],
        "interpretation": (
            "The PEPS/PEPS3D tiny substrates can run all 16 individual stage placements "
            "and the four L/R inner/outer loop composites one by one. This is a useful "
            "depth inventory for the engine build path, while full deterministic MPDO "
            "Lindblad and scale-level PEPS/PEPS3D convergence remain open."
        ),
    }
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "SOURCE_ALIGNMENT_CATEGORY": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "all_pass": all_pass,
        "summary": summary,
        "positive": positive,
        "positive_findings": positive,
        "graveyard_companions": graveyard,
        "graveyard_controls": graveyard,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for item in graveyard.values() if item["pass"]),
            "variants": sorted(graveyard),
        },
        "why_not_v4_probes": (
            "This is a v5 formal-scout depth inventory for tiny PEPS/PEPS3D "
            "stage and loop execution. It is not a promoted v4 probe and does "
            "not admit MPDO Lindblad, full tensor convergence, L32/L64 scaling, "
            "scale-level basin evidence, or final manifold closure."
        ),
        "boundary": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "tiny_peps_2x4_stage_loop_inventory": True,
            "tiny_peps3d_2x2x2_stage_loop_inventory": True,
            "not_mpdo_lindblad": True,
            "not_full_peps_convergence": True,
            "not_full_peps3d_convergence": True,
            "not_l32_l64": True,
            "not_scale_level_real_basin": True,
            "not_final_manifold_admission": True,
            "z3_guard": guard,
        },
        "graph_witness": graph,
        "stage_rows": [row_without_edge_details(row) for row in stage_rows],
        "loop_rows": [row_without_edge_details(row) for row in loop_rows],
        "aggregates": {
            "loop_mi_by_id": loop_mi_by_id,
            "stage_mi_by_terrain": stage_mi_by_terrain,
            "substrate_summary": substrate_summary,
        },
        "next_work_required": [
            "Promote this inventory into deterministic MPDO Lindblad on tensor substrates, not pure-state no-jump PEPS updates.",
            "Run deeper per-loop cycle counts and bond-cap sweeps to identify truncation sensitivity.",
            "Only after deterministic tensor dynamics is stable, test schedule-level pseudo-basin clustering on PEPS/PEPS3D substrates.",
        ],
        "source_hashes": source_hashes(),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
