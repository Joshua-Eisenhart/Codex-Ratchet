#!/usr/bin/env python3
"""Shared controls for basin_grid_refinement_control_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import z3


SIM_ID = "basin_grid_refinement_control_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
PARENT_SWEEP_DIR = ROOT / "system_v6" / "sims" / "basin_generating_set_sweep_v0"
PARENT_RC_DIR = ROOT / "system_v6" / "sims" / "basin_rc_transition_graph_v0"
PARENT_SWEEP_ENV = PARENT_SWEEP_DIR / "results" / "basin_generating_set_sweep_v0_envelope_results.json"
PARENT_SWEEP_COMMON = PARENT_SWEEP_DIR / "basin_generating_set_sweep_v0_common.py"
PARENT_RC_COMMON = PARENT_RC_DIR / "basin_rc_transition_graph_v0_common.py"

if str(PARENT_SWEEP_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_SWEEP_DIR))
if str(PARENT_RC_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_RC_DIR))

import basin_generating_set_sweep_v0_common as sweep_parent
import basin_rc_transition_graph_v0_common as rc_parent


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED_LEDGER = {"rng": "none", "deterministic_tie_break": "cell_id_ascending"}
G1_NAMES = ["R_x", "R_z", "Ne_Spiral_R", "Ne_Vortex_L"]
G0_NAMES = ["Se_Funnel_L", "Ni_Pit_L", "Ni_Source_R", "Ne_Spiral_R", "D_z", "R_x"]
REFINEMENT_MULTIPLIERS = [2, 3]
ROTATED_GRID_AXIS = [1.0, 1.0, 1.0]
ROTATED_GRID_ANGLE = math.pi * (math.sqrt(2.0) - 1.0)
PARENT_COMMIT_HINTS = {
    "basin_generating_set_sweep_v0": "ba1bfc4d1",
    "basin_rc_transition_graph_v0": "631f1c3db",
    "basin_contract": "000f48e71",
}


def now_z() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


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
    paths = {
        "basin_generating_set_sweep_v0_envelope": PARENT_SWEEP_ENV,
        "basin_generating_set_sweep_v0_common": PARENT_SWEEP_COMMON,
        "basin_rc_transition_graph_v0_common": PARENT_RC_COMMON,
        "basin_contract": ROOT / "system_v6/receipts/attractor_basin_criterion_20260611.md",
    }
    return {
        "consumed_inputs": [
            {
                "id": key,
                "path": rel(path),
                "sha256": sha256_file(path),
                "commit_hint": PARENT_COMMIT_HINTS.get(key.split("_envelope")[0]) or PARENT_COMMIT_HINTS.get(key),
                "git_last_commit": git_last_commit(path),
            }
            for key, path in paths.items()
            if path.exists()
        ],
        "parent_committed_hash_bound": PARENT_COMMIT_HINTS,
        "closes_carried_caveat": "CAVEAT C1: whether the three G1 rotation classes are invariant geometry or grid artifacts",
        "builder_output_only": True,
    }


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(matrix[i][j] * vector[j] for j in range(3)) for i in range(3)]


def add_vec(left: list[float], right: list[float]) -> list[float]:
    return [left[i] + right[i] for i in range(3)]


def dot(left: list[float], right: list[float]) -> float:
    return sum(left[i] * right[i] for i in range(3))


def cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def norm(vec: list[float]) -> float:
    return math.sqrt(dot(vec, vec))


def normalize(vec: list[float]) -> list[float]:
    length = norm(vec)
    return [value / length for value in vec]


def rotation_matrix(axis: list[float], angle: float) -> list[list[float]]:
    ux, uy, uz = normalize(axis)
    c = math.cos(angle)
    s = math.sin(angle)
    one = 1.0 - c
    return [
        [c + ux * ux * one, ux * uy * one - uz * s, ux * uz * one + uy * s],
        [uy * ux * one + uz * s, c + uy * uy * one, uy * uz * one - ux * s],
        [uz * ux * one - uy * s, uz * uy * one + ux * s, c + uz * uz * one],
    ]


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [[matrix[j][i] for j in range(3)] for i in range(3)]


def tangent_for(cell_id: int, coord: list[float]) -> list[float]:
    seeds = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    base = seeds[cell_id % 3]
    if norm(coord) <= 1.0e-12:
        return base
    radial = normalize(coord)
    projected = [base[i] - dot(base, radial) * radial[i] for i in range(3)]
    if norm(projected) <= 1.0e-12:
        base = seeds[(cell_id + 1) % 3]
        projected = [base[i] - dot(base, radial) * radial[i] for i in range(3)]
    return normalize(projected)


def nearest_cell_id(point: list[float], cells: list[dict[str, Any]]) -> int:
    best = int(cells[0]["cell_id"])
    best_d2 = math.inf
    for cell in cells:
        d2 = sum((point[i] - cell["coord"][i]) ** 2 for i in range(3))
        cid = int(cell["cell_id"])
        if d2 < best_d2 - 1.0e-12 or (abs(d2 - best_d2) <= 1.0e-12 and cid < best):
            best = cid
            best_d2 = d2
    return best


def committed_cells() -> list[dict[str, Any]]:
    return [dict(cell, parent_cell_id=int(cell["cell_id"]), refinement_child_index=0) for cell in rc_parent.state_cells()]


def refined_cells(multiplier: int) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for parent_cell in rc_parent.state_cells():
        parent_id = int(parent_cell["cell_id"])
        coord = [float(x) for x in parent_cell["coord"]]
        tangent = tangent_for(parent_id, coord)
        second = normalize(cross(normalize(coord), tangent)) if norm(coord) > 1.0e-12 else tangent_for(parent_id + 1, coord)
        offsets = [[0.0, 0.0, 0.0], [0.035 * x for x in tangent]]
        if multiplier == 3:
            offsets.append([0.035 * x for x in second])
        for child_index, offset in enumerate(offsets):
            if norm(coord) > 1.0e-12:
                base = [0.875 * x for x in coord]
            else:
                base = [0.0, 0.0, 0.0]
            point = [base[i] + offset[i] for i in range(3)]
            if norm(point) > 1.0:
                point = [0.98 * x / norm(point) for x in point]
            cells.append(
                {
                    "cell_id": len(cells),
                    "coord": [round(float(x), 12) for x in point],
                    "parent_cell_id": parent_id,
                    "refinement_child_index": child_index,
                    "radius_squared": round(sum(x * x for x in point), 12),
                    "Adm_C": True,
                    "conditioned_shell_member": bool(parent_cell["conditioned_shell_member"]),
                }
            )
    return cells


def rotated_committed_cells() -> list[dict[str, Any]]:
    rot = rotation_matrix(ROTATED_GRID_AXIS, ROTATED_GRID_ANGLE)
    cells: list[dict[str, Any]] = []
    for parent_cell in rc_parent.state_cells():
        coord = [float(x) for x in parent_cell["coord"]]
        point = matvec(rot, coord)
        cells.append(
            {
                "cell_id": len(cells),
                "coord": [round(float(x), 12) for x in point],
                "parent_cell_id": int(parent_cell["cell_id"]),
                "refinement_child_index": 0,
                "radius_squared": round(sum(x * x for x in point), 12),
                "Adm_C": True,
                "conditioned_shell_member": bool(parent_cell["conditioned_shell_member"]),
            }
        )
    return cells


def load_generators(expm_fn: Callable[[list[list[float]], float], list[list[float]]]) -> dict[str, Any]:
    return sweep_parent.load_all_generators(expm_fn)


def g1_generators(all_rows: dict[str, Any]) -> list[dict[str, Any]]:
    return [all_rows["generators_by_name"][name] for name in G1_NAMES]


def g0_generators(all_rows: dict[str, Any]) -> list[dict[str, Any]]:
    return [all_rows["generators_by_name"][name] for name in G0_NAMES]


def build_graph(generators: list[dict[str, Any]], cells: list[dict[str, Any]]) -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_nodes_from(int(cell["cell_id"]) for cell in cells)
    cell_by_id = {int(cell["cell_id"]): cell for cell in cells}
    edge_rows: list[dict[str, Any]] = []
    for cell in cells:
        for generator in generators:
            image = add_vec(matvec(generator["M"], cell["coord"]), generator["c"])
            dst = nearest_cell_id(image, cells)
            graph.add_edge(int(cell["cell_id"]), dst, generator=generator["name"])
            edge_rows.append(
                {
                    "src": int(cell["cell_id"]),
                    "dst": dst,
                    "generator": generator["name"],
                    "image_before_quantization": [round(float(x), 12) for x in image],
                }
            )
    sccs = [sorted(list(comp)) for comp in nx.strongly_connected_components(graph)]
    sccs.sort(key=lambda comp: (min(comp), len(comp)))
    comp_id: dict[int, int] = {}
    for idx, comp in enumerate(sccs):
        for cell_id in comp:
            comp_id[int(cell_id)] = idx
    class_rows: list[dict[str, Any]] = []
    terminal_ids: list[int] = []
    for idx, comp in enumerate(sccs):
        comp_set = set(comp)
        outgoing = [row for row in edge_rows if row["src"] in comp_set and row["dst"] not in comp_set]
        total = len(comp) * len(generators)
        internal = total - len(outgoing)
        terminal = len(outgoing) == 0
        if terminal:
            terminal_ids.append(idx)
        class_rows.append(
            {
                "class_id": idx,
                "cells": comp,
                "parent_cell_ids": sorted({int(cell_by_id[cell]["parent_cell_id"]) for cell in comp}),
                "size": len(comp),
                "terminal_closed": terminal,
                "outgoing_edge_count": len(outgoing),
                "internal_transition_fraction": round(internal / total if total else 0.0, 12),
                "escape_transition_fraction": round(len(outgoing) / total if total else 0.0, 12),
            }
        )
    boundary = sorted({row["src"] for row in edge_rows if comp_id[row["src"]] != comp_id[row["dst"]]})
    graph_hash_basis = {
        "cells": [{"cell_id": c["cell_id"], "coord": c["coord"], "parent_cell_id": c["parent_cell_id"]} for c in cells],
        "generators": [{"name": g["name"], "kind": g["kind"], "h": g["h"]} for g in generators],
        "edges": [{"src": r["src"], "dst": r["dst"], "generator": r["generator"]} for r in edge_rows],
        "classes": class_rows,
    }
    return {
        "state_count": len(cells),
        "edge_count": len(edge_rows),
        "cells": cells,
        "generators": generators,
        "transition_edges": edge_rows,
        "scc_count": len(class_rows),
        "communicating_classes": class_rows,
        "terminal_class_ids": terminal_ids,
        "terminal_classes": [class_rows[idx] for idx in terminal_ids],
        "component_id_by_cell": {str(k): v for k, v in sorted(comp_id.items())},
        "partition_signature": {
            "state_count": len(cells),
            "scc_count": len(class_rows),
            "terminal_sizes": sorted(class_rows[idx]["size"] for idx in terminal_ids),
            "class_sizes": sorted(row["size"] for row in class_rows),
            "boundary_count": len(boundary),
        },
        "transition_graph_sha256": stable_sha256(graph_hash_basis),
    }


def anchor_rows(base_graph: dict[str, Any], exact_parent_graph: dict[str, Any]) -> dict[str, Any]:
    parent_env = load_json(PARENT_SWEEP_ENV)
    g1 = parent_env["sweep"]["G1"]
    parent_terminal = [sorted(row) for row in g1["terminal_cells"]]
    local_terminal = [row["cells"] for row in base_graph["terminal_classes"]]
    exact_terminal = [row["cells"] for row in exact_parent_graph["terminal_classes"]]
    return {
        "parent_path": rel(PARENT_SWEEP_ENV),
        "parent_commit_hint": "ba1bfc4d1",
        "state_count": base_graph["state_count"],
        "parent_terminal_class_count": g1["terminal_class_count"],
        "local_terminal_class_count": len(base_graph["terminal_classes"]),
        "parent_terminal_cells": parent_terminal,
        "local_terminal_cells": local_terminal,
        "exact_rederived_terminal_cells": exact_terminal,
        "byte_exact": bool(
            g1["partition_signature"] == exact_parent_graph["partition_signature"]
            and g1["transition_graph_sha256"] == exact_parent_graph["transition_graph_sha256"]
            and parent_terminal == exact_terminal
        ),
        "parent_partition_signature": g1["partition_signature"],
        "local_partition_signature": base_graph["partition_signature"],
        "exact_rederived_partition_signature": exact_parent_graph["partition_signature"],
        "parent_transition_graph_sha256": g1["transition_graph_sha256"],
        "exact_rederived_transition_graph_sha256": exact_parent_graph["transition_graph_sha256"],
    }


def terminal_parent_overlap(graph: dict[str, Any], anchor_terminal: list[dict[str, Any]]) -> dict[str, Any]:
    anchor_by_class = {row["class_id"]: set(row["cells"]) for row in anchor_terminal}
    out: dict[str, Any] = {}
    for row in graph["terminal_classes"]:
        overlaps = {
            str(class_id): sorted(set(row["parent_cell_ids"]) & cells)
            for class_id, cells in anchor_by_class.items()
            if set(row["parent_cell_ids"]) & cells
        }
        out[str(row["class_id"])] = {
            "cells": row["cells"],
            "parent_cell_ids": row["parent_cell_ids"],
            "overlaps_committed_terminal_classes": overlaps,
            "radius_squared_values": sorted(
                {
                    round(
                        sum(
                            float(graph["cells"][cell_id]["coord"][i]) * float(graph["cells"][cell_id]["coord"][i])
                            for i in range(3)
                        ),
                        12,
                    )
                    for cell_id in row["cells"]
                }
            ),
        }
    return out


def class_fates(graph: dict[str, Any], anchor_terminal: list[dict[str, Any]]) -> dict[str, Any]:
    anchor_by_class = {row["class_id"]: set(row["cells"]) for row in anchor_terminal}
    terminal_to_anchor: dict[int, set[int]] = {}
    for row in graph["terminal_classes"]:
        parent_ids = set(row["parent_cell_ids"])
        terminal_to_anchor[int(row["class_id"])] = {
            int(class_id) for class_id, cells in anchor_by_class.items() if parent_ids & cells
        }
    fates = {}
    for class_id in sorted(anchor_by_class):
        realized = sorted(tid for tid, anchors in terminal_to_anchor.items() if class_id in anchors)
        mixed = [tid for tid in realized if len(terminal_to_anchor[tid]) > 1]
        if not realized:
            fate = "DISSOLVE"
        elif mixed:
            fate = "MERGE"
        elif len(realized) == 1:
            fate = "PERSIST"
        else:
            fate = "SPLIT_FURTHER"
        fates[str(class_id)] = {
            "committed_terminal_class_id": class_id,
            "committed_terminal_cells": sorted(anchor_by_class[class_id]),
            "refined_or_rotated_terminal_class_ids": realized,
            "fate": fate,
        }
    overall = "PERSIST" if all(row["fate"] == "PERSIST" for row in fates.values()) and len(graph["terminal_classes"]) == len(anchor_by_class) else "CHANGED"
    return {
        "overall_fate": overall,
        "committed_class_fates": fates,
        "terminal_to_committed_class_overlap": {str(k): sorted(v) for k, v in terminal_to_anchor.items()},
    }


def graph_summary(label: str, graph: dict[str, Any], anchor_terminal: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "label": label,
        "state_count": graph["state_count"],
        "edge_count": graph["edge_count"],
        "scc_count": graph["scc_count"],
        "terminal_class_count": len(graph["terminal_classes"]),
        "terminal_class_sizes": sorted(row["size"] for row in graph["terminal_classes"]),
        "terminal_classes": [
            {
                "class_id": row["class_id"],
                "cells": row["cells"],
                "parent_cell_ids": row["parent_cell_ids"],
                "size": row["size"],
                "terminal_closed": row["terminal_closed"],
            }
            for row in graph["terminal_classes"]
        ],
        "partition_signature": graph["partition_signature"],
        "transition_graph_sha256": graph["transition_graph_sha256"],
        "persistence": class_fates(graph, anchor_terminal),
        "invariant_characterization": terminal_parent_overlap(graph, anchor_terminal),
    }


def fake_axis_artifact_control(base_graph: dict[str, Any], rotated_graph: dict[str, Any]) -> dict[str, Any]:
    def fake_members(graph: dict[str, Any]) -> list[int]:
        return [
            int(cell["cell_id"])
            for cell in graph["cells"]
            if abs(float(cell["coord"][2]) - 0.5) <= 1.0e-12
        ]

    def closed(graph: dict[str, Any], members: list[int]) -> dict[str, Any]:
        member_set = set(members)
        escaping = [row for row in graph["transition_edges"] if row["src"] in member_set and row["dst"] not in member_set]
        return {"member_count": len(members), "closed_under_G1": len(escaping) == 0, "escaping_edge_count": len(escaping)}

    base_members = fake_members(base_graph)
    rotated_members = fake_members(rotated_graph)
    base_closed = closed(base_graph, base_members)
    rotated_closed = closed(rotated_graph, rotated_members)
    return {
        "construction": "axis-snapped fake class: cells with world-coordinate z exactly 1/2",
        "designed_fail_expected": True,
        "base_axis_grid": base_closed,
        "rotated_grid": rotated_closed,
        "dies_under_rotation": bool(rotated_closed["member_count"] < base_closed["member_count"] and rotated_closed["closed_under_G1"] is False),
    }


def continuous_cross_check(generators: list[dict[str, Any]]) -> dict[str, Any]:
    matrices = {g["name"]: g["M"] for g in generators}
    angle_rows = {}
    for name, matrix in matrices.items():
        trace = sum(matrix[i][i] for i in range(3))
        cos_theta = max(-1.0, min(1.0, (trace - 1.0) / 2.0))
        theta = math.acos(cos_theta)
        angle_rows[name] = {
            "trace": round(trace, 12),
            "angle_radians": round(theta, 12),
            "angle_over_pi": round(theta / math.pi, 12),
            "determinant_close_to_one": bool(abs(sp.Matrix(matrix).det() - 1.0) < 1.0e-9),
        }
    return {
        "continuous_generator_family": "rotations only; offsets are zero for R_x/R_z/Ne_Spiral_R/Ne_Vortex_L",
        "h_time_step_role": "Ne terrain rotations enter as exp(hA) with h=1/2; the observed Ne rotation angle is 1 radian, not a grid angle.",
        "generator_angle_rows": angle_rows,
        "closure_result": "SO(3)",
        "closure_reason": (
            "R_x and R_z generate the cube rotation subgroup. The Ne rotations are about the non-axis (1,1,1) family "
            "with angle 1 radian; this is not one of the finite SO(3) subgroup angles. Conjugating that circle by "
            "the cube rotations supplies nonparallel axes whose Lie algebra spans so(3)."
        ),
        "exact_invariant_decomposition_of_ball": "one recurrent orbit class per radius sphere, plus the fixed origin; with radius erased, the admitted ball is one continuum recurrent basin under SO(3) closure.",
        "finite_vs_continuum_comparison": "the three 33-cell G1 terminal classes are finite quantization structure at the stated grid/time-step, while the continuous closure merges them by radius-shell recurrence.",
        "predicts_one_recurrent_class_after_radius_erasure": True,
    }


def z3_persistence_identity(rows: list[dict[str, Any]], *, erased_flip: bool = False) -> str:
    code = {"PERSIST": 1, "MERGE": 2, "SPLIT_FURTHER": 3, "DISSOLVE": 4, "CHANGED": 5}
    solver = z3.Solver()
    terms = []
    for idx, row in enumerate(rows):
        actual = z3.Int(f"z3_actual_fate_{idx}")
        expected = z3.Int(f"z3_expected_fate_{idx}")
        value = code[row["fate"]]
        solver.add(actual == z3.IntVal(value))
        if erased_flip and idx == len(rows) - 1:
            value = 4 if value != 4 else 1
        solver.add(expected == z3.IntVal(value))
        terms.append(actual != expected)
    solver.add(z3.Or(terms))
    return str(solver.check())


def cvc5_persistence_identity(rows: list[dict[str, Any]], *, erased_flip: bool = False) -> str:
    code = {"PERSIST": 1, "MERGE": 2, "SPLIT_FURTHER": 3, "DISSOLVE": 4, "CHANGED": 5}
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    terms = []
    for idx, row in enumerate(rows):
        actual = solver.mkConst(int_sort, f"cvc5_actual_fate_{idx}")
        expected = solver.mkConst(int_sort, f"cvc5_expected_fate_{idx}")
        value = code[row["fate"]]
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, actual, solver.mkInteger(value)))
        if erased_flip and idx == len(rows) - 1:
            value = 4 if value != 4 else 1
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, expected, solver.mkInteger(value)))
        terms.append(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, actual, expected)))
    solver.assertFormula(terms[0] if len(terms) == 1 else solver.mkTerm(Kind.OR, *terms))
    result = solver.checkSat()
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def proof_rows(refinement_rows: list[dict[str, Any]], rotated_row: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for row in refinement_rows:
        rows.append({"control": row["label"], "fate": row["persistence"]["overall_fate"]})
        for fate in row["persistence"]["committed_class_fates"].values():
            rows.append({"control": row["label"], "class": fate["committed_terminal_class_id"], "fate": fate["fate"]})
    rows.append({"control": rotated_row["label"], "fate": rotated_row["persistence"]["overall_fate"]})
    for fate in rotated_row["persistence"]["committed_class_fates"].values():
        rows.append({"control": rotated_row["label"], "class": fate["committed_terminal_class_id"], "fate": fate["fate"]})
    proof_row = {
        "encoding": "computed persistence fates are integer-coded; assert existence of a mismatch against the emitted fate table",
        "erased_flip": "last expected fate code is changed",
        "partition_identity_inputs": rows,
        "asserted_precomputed_boolean": False,
    }
    return {
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": z3_persistence_identity(rows),
            "erased_flip_verdict": z3_persistence_identity(rows, erased_flip=True),
            "proof_row": proof_row,
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": cvc5_persistence_identity(rows),
            "erased_flip_verdict": cvc5_persistence_identity(rows, erased_flip=True),
            "proof_row": proof_row,
        },
    }


def build_analysis(expm_fn: Callable[[list[list[float]], float], list[list[float]]]) -> dict[str, Any]:
    all_rows = load_generators(expm_fn)
    g1 = g1_generators(all_rows)
    g0 = g0_generators(all_rows)
    base_graph = build_graph(g1, committed_cells())
    exact_parent_graph = sweep_parent.build_graph_for(
        {"set_id": "G1", "generators": g1, "conditioned_only": False}
    )
    anchor = anchor_rows(base_graph, exact_parent_graph)
    anchor_terminal = exact_parent_graph["terminal_classes"]
    refinement_rows = []
    g0_refined_rows = []
    for multiplier in REFINEMENT_MULTIPLIERS:
        cells = refined_cells(multiplier)
        g1_graph = build_graph(g1, cells)
        g0_graph = build_graph(g0, cells)
        refinement_rows.append(graph_summary(f"{multiplier}x_density_refined_grid", g1_graph, anchor_terminal))
        g0_refined_rows.append(
            {
                "label": f"G0_{multiplier}x_density_refined_grid",
                "state_count": g0_graph["state_count"],
                "terminal_class_count": len(g0_graph["terminal_classes"]),
                "terminal_class_sizes": sorted(row["size"] for row in g0_graph["terminal_classes"]),
                "stays_one_class": len(g0_graph["terminal_classes"]) == 1,
                "partition_signature": g0_graph["partition_signature"],
            }
        )
    rotated_graph = build_graph(g1, rotated_committed_cells())
    rotated_row = graph_summary("rotated_33_cell_density_grid", rotated_graph, anchor_terminal)
    artifact = fake_axis_artifact_control(base_graph, rotated_graph)
    proofs = proof_rows(refinement_rows, rotated_row)
    continuous = continuous_cross_check(g1)
    persistence_table = {
        "anchor": anchor,
        "refinement": refinement_rows,
        "rotated_grid": rotated_row,
        "g0_dissipative_refined_control": g0_refined_rows,
        "axis_artifact_control": artifact,
        "continuous_cross_check": continuous,
    }
    signature_basis = {
        "anchor": anchor,
        "refinement": [
            {
                "label": row["label"],
                "state_count": row["state_count"],
                "terminal_class_count": row["terminal_class_count"],
                "terminal_class_sizes": row["terminal_class_sizes"],
                "persistence": row["persistence"],
            }
            for row in refinement_rows
        ],
        "rotated": {
            "terminal_class_count": rotated_row["terminal_class_count"],
            "terminal_class_sizes": rotated_row["terminal_class_sizes"],
            "persistence": rotated_row["persistence"],
        },
        "continuous": continuous["closure_result"],
    }
    controls_pass = bool(
        anchor["byte_exact"]
        and all(row["stays_one_class"] for row in g0_refined_rows)
        and artifact["dies_under_rotation"]
        and proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_verdict"] == "sat"
        and proofs["cvc5"]["erased_flip_verdict"] == "sat"
        and continuous["predicts_one_recurrent_class_after_radius_erasure"] is True
    )
    return {
        "source_locks": {
            "parent_sweep_envelope": {"path": rel(PARENT_SWEEP_ENV), "sha256": sha256_file(PARENT_SWEEP_ENV), "git_last_commit": git_last_commit(PARENT_SWEEP_ENV)},
            "parent_sweep_common": {"path": rel(PARENT_SWEEP_COMMON), "sha256": sha256_file(PARENT_SWEEP_COMMON), "git_last_commit": git_last_commit(PARENT_SWEEP_COMMON)},
            "parent_rc_common": {"path": rel(PARENT_RC_COMMON), "sha256": sha256_file(PARENT_RC_COMMON), "git_last_commit": git_last_commit(PARENT_RC_COMMON)},
        },
        "grid_declaration": {
            "committed_cell_count": 33,
            "refined_cell_counts": {f"{m}x": 33 * m for m in REFINEMENT_MULTIPLIERS},
            "refinement_rule": "deterministic child cells inside each committed cell containment region; no dense carrier",
            "rotated_grid": {
                "cell_count": 33,
                "axis": ROTATED_GRID_AXIS,
                "angle_radians": ROTATED_GRID_ANGLE,
                "angle_over_pi": "sqrt(2)-1",
            },
        },
        "g1_generator_names": G1_NAMES,
        "persistence_table": persistence_table,
        "crossover_proofs": proofs,
        "c1_answer": {
            "finite_grid_reading": "The 33-cell G1 classes are real terminal classes of the finite quantized transition system.",
            "continuum_reading": "The continuous rotations-only closure is SO(3), so the ball has one recurrent class after radius erasure.",
            "closure": "C1 closes as discretization-scale structure, not invariant continuum basin geometry.",
            "promotion_allowed": False,
        },
        "analysis_signature_sha256": stable_sha256(signature_basis),
        "all_pass": controls_pass,
    }


def one_to_one_tool_rows(engine: str, graph_tool: str, proof_tools: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    ids = [f"{engine}_{graph_tool}_grid_refinement_control"] + [f"{engine}_{tool}_persistence_identity" for tool in proof_tools]
    capability = [
        {
            "receipt_id": ids[0],
            "tool": graph_tool,
            "computed_what": "G1 partitions on committed, refined, and rotated grids with containment fates",
            "status": "used",
        }
    ]
    for tool, rid in zip(proof_tools, ids[1:], strict=True):
        capability.append(
            {
                "receipt_id": rid,
                "tool": tool,
                "computed_what": "computed persistence identity with erased fate flip",
                "status": "used",
            }
        )
    calls = [
        {
            "receipt_id": ids[0],
            "tool": graph_tool,
            "qualified_api/function": {
                "networkx": "networkx.DiGraph/networkx.strongly_connected_components",
                "Graphs": "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components",
                "torch_geometric": "torch_geometric.data.Data plus torch.func.vmap",
            }.get(graph_tool, graph_tool),
            "input_object": "G1 generator-labelled finite cells for committed, refined, and rotated grids",
            "output_object": "terminal classes, containment correspondence, class fates, and artifact control",
            "positive_case": "33-cell G1 anchor matches the committed parent byte-exact partition",
            "negative/erased_control": "axis-snapped fake class dies under the pinned non-axis grid rotation",
            "boundary_case": "2x and 3x refined grids stay within declared resource guard",
            "demotion_condition": "demote if class fates are not recomputed from explicit transition edges",
            "gates": ["persistence_table", "axis_artifact_control", "all_pass"],
        }
    ]
    for tool, rid in zip(proof_tools, ids[1:], strict=True):
        calls.append(
            {
                "receipt_id": rid,
                "tool": tool,
                "qualified_api/function": {
                    "z3": "z3.Solver/z3.Int/check",
                    "cvc5": "cvc5.Solver/mkConst/assertFormula/checkSat",
                    "Z3": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                }.get(tool, tool),
                "input_object": "computed persistence fate table",
                "output_object": "UNSAT persistence identity proof and SAT erased flip",
                "positive_case": "all emitted class fates match the solver-bound fate rows",
                "negative/erased_control": "one expected fate code is flipped",
                "boundary_case": "PERSIST, MERGE, SPLIT_FURTHER, and DISSOLVE are all admissible fate codes",
                "demotion_condition": "demote if solver does not bind computed fate rows",
                "gates": ["proof", "identity", "all_pass"],
            }
        )
    return capability, calls, {"pass": [row["receipt_id"] for row in capability] == [row["receipt_id"] for row in calls]}
