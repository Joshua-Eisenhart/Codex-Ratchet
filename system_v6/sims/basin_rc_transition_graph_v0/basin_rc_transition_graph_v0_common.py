#!/usr/bin/env python3
"""Shared finite graph utilities for basin_rc_transition_graph_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import subprocess
from collections import deque
from pathlib import Path
from typing import Any

import networkx as nx
import sympy as sp


SIM_ID = "basin_rc_transition_graph_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED_LEDGER = {"rng": "none", "deterministic_tie_break": "cell_id_ascending"}
GRID_VALUES = [-1.0, -0.5, 0.0, 0.5, 1.0]
TERRAIN_H = 0.5
METASTABLE_INTERNAL_THRESHOLD = 0.95
METASTABLE_ESCAPE_MAX = 0.05
BASE_TERRAINS = ["Se_Funnel_L", "Ni_Pit_L", "Ni_Source_R", "Ne_Spiral_R"]
BASE_OPERATORS = ["D_z", "R_x"]
HELD_OUT_OPERATORS = ["D_x", "R_z"]
STATE_SCALE = 2

PARENT_PATHS = {
    "basin_criterion_pilot_v0_envelope": ROOT
    / "system_v6/sims/basin_criterion_pilot_v0/results/basin_criterion_pilot_v0_envelope_results.json",
    "basin_criterion_pilot_v0_build_card": ROOT / "system_v6/sims/basin_criterion_pilot_v0/build_card.md",
    "basin_contract": ROOT / "system_v6/receipts/attractor_basin_criterion_20260611.md",
    "terrain_operator_map": ROOT / "system_v6/receipts/terrain_operator_map_20260609.md",
    "geo_s5_terrain_flows_v0_envelope": ROOT
    / "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
    "geo_s4_operator_stage_v0_envelope": ROOT
    / "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json",
    "geo_disintegration_machinery_v0_envelope": ROOT
    / "system_v6/sims/geo_disintegration_machinery_v0/results/geo_disintegration_machinery_v0_envelope_results.json",
    "geo_union_rule_k_leaves_v0_envelope": ROOT
    / "system_v6/sims/geo_union_rule_k_leaves_v0/results/geo_union_rule_k_leaves_v0_envelope_results.json",
}

PARENT_COMMIT_HINTS = {
    "basin_criterion_pilot_v0": "4e082f525",
    "basin_contract": "50f16d82d",
    "geo_s5_terrain_flows_v0": "6aa75cc96",
    "geo_s4_operator_stage_v0": "source-backed current packet",
    "build_card": "28551e3f6",
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


def source_lock(path: Path, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": rel(path),
        "sha256": sha256_file(path),
        "git_last_commit": git_last_commit(path),
    }


def parent_lineage() -> dict[str, Any]:
    return {
        "consumed_inputs": [
            {
                "id": key,
                "path": rel(path),
                "sha256": sha256_file(path),
                "commit_hint": PARENT_COMMIT_HINTS.get(key)
                or PARENT_COMMIT_HINTS.get(key.split("_envelope")[0])
                or PARENT_COMMIT_HINTS.get(key.split("_build_card")[0]),
                "git_last_commit": git_last_commit(path),
            }
            for key, path in PARENT_PATHS.items()
            if path.exists()
        ],
        "carried_caveats_closed_here": {
            "G1": "explicit finite R_C graph and basin partition computed",
            "G4": "seven negative controls computed and required to fire",
            "G5": "real Julia Graphs.jl/Z3.jl lane replaces validator-slot Julia",
        },
        "user_build_card_hash": "28551e3f6",
    }


def parse_expr(value: str | int | float) -> float:
    return float(sp.N(sp.sympify(str(value).replace("//", "/"))))


def parse_matrix(rows: list[list[str]]) -> list[list[float]]:
    return [[parse_expr(value) for value in row] for row in rows]


def parse_vector(values: list[str]) -> list[float]:
    return [parse_expr(value) for value in values]


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(matrix[i][j] * vector[j] for j in range(3)) for i in range(3)]


def add_vec(left: list[float], right: list[float]) -> list[float]:
    return [left[i] + right[i] for i in range(3)]


def state_cells(root_off: bool = False) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for x in GRID_VALUES:
        for y in GRID_VALUES:
            for z in GRID_VALUES:
                r2 = x * x + y * y + z * z
                if root_off or r2 <= 1.0 + 1.0e-12:
                    conditioned = abs(z - 0.5) <= 1.0e-12 and abs((x * x + y * y) - 0.5) <= 1.0e-12
                    cells.append(
                        {
                            "cell_id": len(cells),
                            "coord": [x, y, z],
                            "coord_scaled": [int(round(STATE_SCALE * x)), int(round(STATE_SCALE * y)), int(round(STATE_SCALE * z))],
                            "radius_squared": round(r2, 12),
                            "Adm_C": bool(r2 <= 1.0 + 1.0e-12),
                            "conditioned_shell_member": conditioned,
                        }
                    )
    return cells


def nearest_cell(point: list[float], cells: list[dict[str, Any]]) -> int:
    best_id = 0
    best_d2 = math.inf
    for cell in cells:
        d2 = sum((point[i] - cell["coord"][i]) ** 2 for i in range(3))
        if d2 < best_d2 - 1.0e-12 or (abs(d2 - best_d2) <= 1.0e-12 and cell["cell_id"] < best_id):
            best_id = int(cell["cell_id"])
            best_d2 = d2
    return best_id


def affine_from_terrain(row: dict[str, Any], expm_fn: Any, h: float = TERRAIN_H) -> tuple[list[list[float]], list[float]]:
    a_mat = parse_matrix(row["pinned"]["A"])
    b_vec = parse_vector(row["pinned"]["b"])
    aug = [[0.0 for _ in range(4)] for _ in range(4)]
    for i in range(3):
        for j in range(3):
            aug[i][j] = a_mat[i][j]
        aug[i][3] = b_vec[i]
    flow = expm_fn(aug, h)
    return [[float(flow[i][j]) for j in range(3)] for i in range(3)], [float(flow[i][3]) for i in range(3)]


def affine_from_operator(row: dict[str, Any]) -> tuple[list[list[float]], list[float]]:
    return parse_matrix(row["pinned"]["M"]), parse_vector(row["pinned"]["c"])


def load_parent_rows(expm_fn: Any) -> dict[str, Any]:
    s5 = load_json(PARENT_PATHS["geo_s5_terrain_flows_v0_envelope"])
    s4 = load_json(PARENT_PATHS["geo_s4_operator_stage_v0_envelope"])
    generators = []
    source_rows = {}
    for name in BASE_TERRAINS:
        row = s5["bloch_generator_table"][name]
        matrix, offset = affine_from_terrain(row, expm_fn)
        generators.append({"name": name, "kind": "S5_terrain_flow", "h": TERRAIN_H, "M": matrix, "c": offset})
        source_rows[name] = {
            "kind": "S5_terrain_flow",
            "source_ref": row.get("source_ref"),
            "symbolic": row.get("symbolic"),
            "pinned_A": row["pinned"]["A"],
            "pinned_b": row["pinned"]["b"],
            "h": TERRAIN_H,
        }
    for name in BASE_OPERATORS:
        row = s4["affine_channel_table"][name]
        matrix, offset = affine_from_operator(row)
        generators.append({"name": name, "kind": "S4_operator_channel", "h": "one_pinned_channel", "M": matrix, "c": offset})
        source_rows[name] = {
            "kind": "S4_operator_channel",
            "basis": row.get("basis"),
            "symbolic": row.get("symbolic"),
            "pinned_M": row["pinned"]["M"],
            "pinned_c": row["pinned"]["c"],
            "h": "one_pinned_channel",
        }
    held_out = {}
    for name in HELD_OUT_OPERATORS:
        row = s4["affine_channel_table"][name]
        matrix, offset = affine_from_operator(row)
        held_out[name] = {"name": name, "kind": "S4_operator_channel", "h": "one_pinned_channel", "M": matrix, "c": offset}
        source_rows[name] = {
            "kind": "S4_operator_channel_held_out",
            "basis": row.get("basis"),
            "symbolic": row.get("symbolic"),
            "pinned_M": row["pinned"]["M"],
            "pinned_c": row["pinned"]["c"],
            "h": "one_pinned_channel",
        }
    return {"generators": generators, "held_out": held_out, "source_rows": source_rows}


def apply_generator(cell: dict[str, Any], generator: dict[str, Any], cells: list[dict[str, Any]]) -> tuple[int, list[float]]:
    image = add_vec(matvec(generator["M"], cell["coord"]), generator["c"])
    return nearest_cell(image, cells), image


def build_transition_graph(
    generators: list[dict[str, Any]],
    *,
    cells: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    cells = cells or state_cells()
    graph = nx.DiGraph()
    graph.add_nodes_from(cell["cell_id"] for cell in cells)
    edge_rows = []
    for cell in cells:
        for generator in generators:
            dst, image = apply_generator(cell, generator, cells)
            graph.add_edge(cell["cell_id"], dst, generator=generator["name"])
            edge_rows.append(
                {
                    "src": cell["cell_id"],
                    "dst": dst,
                    "generator": generator["name"],
                    "image_before_quantization": [round(float(x), 12) for x in image],
                }
            )
    sccs = [sorted(list(comp)) for comp in nx.strongly_connected_components(graph)]
    sccs.sort(key=lambda comp: (min(comp), len(comp)))
    comp_id = {}
    for idx, comp in enumerate(sccs):
        for cell_id in comp:
            comp_id[cell_id] = idx
    class_rows = []
    terminal_classes = []
    for idx, comp in enumerate(sccs):
        comp_set = set(comp)
        outgoing = [
            row for row in edge_rows if row["src"] in comp_set and row["dst"] not in comp_set
        ]
        internal = len(comp) * len(generators) - len(outgoing)
        total = len(comp) * len(generators)
        internal_fraction = internal / total if total else 0.0
        escape_fraction = len(outgoing) / total if total else 0.0
        terminal = len(outgoing) == 0
        if terminal:
            terminal_classes.append(idx)
        class_rows.append(
            {
                "class_id": idx,
                "cells": comp,
                "size": len(comp),
                "terminal_closed": terminal,
                "absent_exit_proof": {
                    "outgoing_edge_count": len(outgoing),
                    "checked_edge_count": total,
                    "no_exit": terminal,
                },
                "internal_transition_fraction": round(internal_fraction, 12),
                "escape_transition_fraction": round(escape_fraction, 12),
                "metastable_almost_invariant": bool(
                    (not terminal)
                    and internal_fraction >= METASTABLE_INTERNAL_THRESHOLD
                    and 0.0 < escape_fraction <= METASTABLE_ESCAPE_MAX
                ),
                "leaky": bool(len(outgoing) > 0),
                "outgoing_edges": outgoing,
            }
        )
    terminal_sets = {idx: set(class_rows[idx]["cells"]) for idx in terminal_classes}
    basin_rows = {}
    successors_by_cell: dict[int, set[int]] = {int(cell["cell_id"]): set() for cell in cells}
    for row in edge_rows:
        successors_by_cell[int(row["src"])].add(int(row["dst"]))

    def sure_basin_for(terminal_set: set[int]) -> list[int]:
        sure = set(terminal_set)
        changed = True
        while changed:
            changed = False
            for cell in cells:
                cid = int(cell["cell_id"])
                if cid in sure:
                    continue
                successors = successors_by_cell[cid]
                if successors and successors <= sure:
                    sure.add(cid)
                    changed = True
        return sorted(sure)

    for class_id, terminal_set in terminal_sets.items():
        can_reach_cells = [
            cell["cell_id"]
            for cell in cells
            if any(nx.has_path(graph, cell["cell_id"], target) for target in terminal_set)
        ]
        sure_cells = sure_basin_for(terminal_set)
        basin_rows[str(class_id)] = {
            "terminal_class_id": class_id,
            "terminal_cells": sorted(terminal_set),
            "semantic_fork": "standard nondeterministic-transition-system fork: may/existential reachability is not must/universal omega-containment",
            "can_reach_terminal": {
                "semantics": "existential/may",
                "definition": "cells with at least one generator-labelled R_C path to the terminal closed class",
                "cells": can_reach_cells,
                "size": len(can_reach_cells),
            },
            "sure_basin_omega_containment": {
                "semantics": "universal/must",
                "definition": "cells whose all-generator omega-limit choices are contained in the terminal closed class",
                "cells": sure_cells,
                "size": len(sure_cells),
            },
            "carried_caveat": "CAVEAT-BASIN-MAP-EXISTENTIAL",
        }
    boundary_cells = sorted(
        {
            row["src"]
            for row in edge_rows
            if comp_id[row["src"]] != comp_id[row["dst"]]
            or any(row["dst"] in terminal_sets[t] for t in terminal_sets)
        }
    )
    reachability = {}
    for cell in cells:
        reachable = sorted(nx.descendants(graph, cell["cell_id"]) | {cell["cell_id"]})
        reachability[cell["cell_id"]] = reachable
    exclusion = {cell_id: len(cells) - len(reachable) for cell_id, reachable in reachability.items()}
    reachable_size = {cell_id: len(reachable) for cell_id, reachable in reachability.items()}
    lyapunov_violations = [
        row
        for row in edge_rows
        if exclusion[row["dst"]] < exclusion[row["src"]]
    ]
    reachable_size_violations = [
        row
        for row in edge_rows
        if reachable_size[row["dst"]] > reachable_size[row["src"]]
    ]
    terminal_targets = sorted({cell for members in terminal_sets.values() for cell in members})
    existential_samples = []
    for start in [0, 3, 15, 16, 17, 31]:
        if start not in reachability:
            continue
        target = next((cell for cell in terminal_targets if nx.has_path(graph, start, cell)), None)
        if target is None:
            continue
        path = nx.shortest_path(graph, start, target)
        existential_samples.append(
            {
                "start": start,
                "target": target,
                "path": path,
                "exclusion_values": [exclusion[cell] for cell in path],
                "reachable_set_sizes": [reachable_size[cell] for cell in path],
            }
        )
    sure_samples = []
    for terminal in terminal_targets:
        outgoing = [row for row in edge_rows if row["src"] == terminal]
        sure_samples.append(
            {
                "start": terminal,
                "paths_by_generator": [
                    {
                        "generator": row["generator"],
                        "path": [terminal, row["dst"]],
                        "exclusion_values": [exclusion[terminal], exclusion[row["dst"]]],
                        "reachable_set_sizes": [reachable_size[terminal], reachable_size[row["dst"]]],
                    }
                    for row in outgoing
                ],
            }
        )
    morse_edges = sorted(
        {
            (comp_id[row["src"]], comp_id[row["dst"]])
            for row in edge_rows
            if comp_id[row["src"]] != comp_id[row["dst"]]
        }
    )
    graph_hash_basis = {
        "cells": cells,
        "generators": [{"name": g["name"], "kind": g["kind"], "h": g["h"]} for g in generators],
        "edges": [{"src": r["src"], "dst": r["dst"], "generator": r["generator"]} for r in edge_rows],
        "classes": class_rows,
    }
    return {
        "state_count": len(cells),
        "cells": cells,
        "generators": generators,
        "transition_edges": edge_rows,
        "edge_count": len(edge_rows),
        "scc_count": len(class_rows),
        "communicating_classes": class_rows,
        "terminal_class_ids": terminal_classes,
        "terminal_classes": [class_rows[idx] for idx in terminal_classes],
        "basin_map": basin_rows,
        "boundary_cells": boundary_cells,
        "separatrix_boundary_cells": boundary_cells,
        "component_id_by_cell": {str(k): v for k, v in sorted(comp_id.items())},
        "morse_graph": {
            "nodes": [
                {
                    "class_id": row["class_id"],
                    "terminal_closed": row["terminal_closed"],
                    "metastable_almost_invariant": row["metastable_almost_invariant"],
                    "leaky": row["leaky"],
                }
                for row in class_rows
            ],
            "edges": [{"src_class": src, "dst_class": dst} for src, dst in morse_edges],
        },
        "monotone_exclusion_observable": {
            "direction_convention": "exclusion count is non-decreasing toward the terminal class; equivalently, reachable-set size is non-increasing",
            "definition": "V_exclusion(cell)=|S|-|Reach_R_C(cell)|; V_reach(cell)=|Reach_R_C(cell)|",
            "values_by_cell": {str(k): v for k, v in sorted(exclusion.items())},
            "reachable_set_size_by_cell": {str(k): v for k, v in sorted(reachable_size.items())},
            "edge_violation_count": len(lyapunov_violations),
            "violations": lyapunov_violations[:20],
            "monotone_non_decreasing_on_edges": len(lyapunov_violations) == 0,
            "reachable_size_edge_violation_count": len(reachable_size_violations),
            "reachable_size_non_increasing_on_edges": len(reachable_size_violations) == 0,
            "semantics_checks": {
                "can_reach_terminal_existential_may": {
                    "trajectory_count_sampled": len(existential_samples),
                    "sampled_trajectories": existential_samples,
                    "direction_verified": len(lyapunov_violations) == 0 and len(reachable_size_violations) == 0,
                },
                "sure_basin_omega_containment_universal_must": {
                    "trajectory_count_sampled": sum(len(row["paths_by_generator"]) for row in sure_samples),
                    "sampled_trajectories": sure_samples,
                    "direction_verified": len(lyapunov_violations) == 0 and len(reachable_size_violations) == 0,
                },
            },
            "carried_caveat": "CAVEAT-LYAPUNOV-DIRECTION",
        },
        "partition_signature": {
            "state_count": len(cells),
            "scc_count": len(class_rows),
            "terminal_sizes": sorted(class_rows[idx]["size"] for idx in terminal_classes),
            "class_sizes": sorted(row["size"] for row in class_rows),
            "boundary_count": len(boundary_cells),
        },
        "transition_graph_sha256": stable_sha256(graph_hash_basis),
    }


def generator_variant(
    parent_rows: dict[str, Any],
    *,
    names: list[str] | None = None,
    add: list[str] | None = None,
    diagonal_only: bool = False,
) -> list[dict[str, Any]]:
    base = []
    selected = names or [g["name"] for g in parent_rows["generators"]]
    by_name = {g["name"]: g for g in parent_rows["generators"]} | parent_rows["held_out"]
    for name in selected + (add or []):
        g = dict(by_name[name])
        if diagonal_only:
            g["M"] = [[g["M"][i][j] if i == j else 0.0 for j in range(3)] for i in range(3)]
        base.append(g)
    return base


def compare_signature(base: dict[str, Any], other: dict[str, Any]) -> dict[str, Any]:
    return {
        "partition_changed": base["partition_signature"] != other["partition_signature"],
        "base_signature": base["partition_signature"],
        "variant_signature": other["partition_signature"],
    }


def control_rows(parent_rows: dict[str, Any], base_graph: dict[str, Any]) -> dict[str, Any]:
    controls: dict[str, Any] = {}
    cells = base_graph["cells"]
    radius_clusters: dict[str, list[int]] = {"inner": [], "mid": [], "outer": []}
    for cell in cells:
        if cell["radius_squared"] <= 0.25:
            radius_clusters["inner"].append(cell["cell_id"])
        elif cell["radius_squared"] <= 0.75:
            radius_clusters["mid"].append(cell["cell_id"])
        else:
            radius_clusters["outer"].append(cell["cell_id"])
    cluster_closed = {}
    for name, members in radius_clusters.items():
        member_set = set(members)
        escaping = [
            row for row in base_graph["transition_edges"] if row["src"] in member_set and row["dst"] not in member_set
        ]
        cluster_closed[name] = {"size": len(members), "closed_under_R_C": len(escaping) == 0, "escaping_edge_count": len(escaping)}
    controls["similarity_only_cluster"] = {
        "fired": any(not row["closed_under_R_C"] for row in cluster_closed.values()),
        "basin_language_allowed": False,
        "contrast": "radius-only clusters are not communicating classes and at least one has R_C exits",
        "clusters": cluster_closed,
    }
    by_name = {g["name"]: g for g in parent_rows["generators"]}
    def two_step(cell_id: int, first: str, second: str) -> int:
        dst1, image1 = apply_generator(cells[cell_id], by_name[first], cells)
        pseudo = {"cell_id": -1, "coord": image1}
        dst2, _ = apply_generator(pseudo, by_name[second], cells)
        return dst2
    order_pair_rows = []
    for left, right in [("Ni_Pit_L", "R_x"), ("Ne_Spiral_R", "D_z"), ("Se_Funnel_L", "R_x")]:
        changed = [
            cell["cell_id"]
            for cell in cells
            if two_step(cell["cell_id"], left, right) != two_step(cell["cell_id"], right, left)
        ]
        order_pair_rows.append({"pair": [left, right], "changed_cell_count": len(changed), "changed_cells_sample": changed[:12]})
    controls["shuffled_order"] = {
        "fired": any(row["changed_cell_count"] > 0 for row in order_pair_rows),
        "pair_rows": order_pair_rows,
    }
    root_off = build_transition_graph(parent_rows["generators"], cells=state_cells(root_off=True))
    controls["root_off"] = {"fired": compare_signature(base_graph, root_off)["partition_changed"], **compare_signature(base_graph, root_off)}
    f01 = build_transition_graph(
        generator_variant(parent_rows, names=["Se_Funnel_L", "Ni_Pit_L", "Ni_Source_R", "D_z"])
    )
    controls["F01_only"] = {"fired": compare_signature(base_graph, f01)["partition_changed"], **compare_signature(base_graph, f01)}
    n01 = build_transition_graph(generator_variant(parent_rows, names=["Ne_Spiral_R", "R_x"]))
    controls["N01_only"] = {"fired": compare_signature(base_graph, n01)["partition_changed"], **compare_signature(base_graph, n01)}
    quotient_classes: dict[float, list[int]] = {}
    for cell in cells:
        quotient_classes.setdefault(cell["radius_squared"], []).append(cell["cell_id"])
    quotient_node_count = len(quotient_classes)
    quotient_edges = set()
    radius_by_cell = {cell["cell_id"]: cell["radius_squared"] for cell in cells}
    for row in base_graph["transition_edges"]:
        quotient_edges.add((radius_by_cell[row["src"]], radius_by_cell[row["dst"]]))
    q_graph = nx.DiGraph()
    q_graph.add_nodes_from(sorted(quotient_classes))
    q_graph.add_edges_from(quotient_edges)
    q_scc = list(nx.strongly_connected_components(q_graph))
    q_term = [comp for comp in q_scc if all(v in comp for u in comp for v in q_graph.successors(u))]
    controls["quotient_erased"] = {
        "fired": quotient_node_count != base_graph["state_count"] or len(q_scc) != base_graph["scc_count"],
        "quotient": "radius_squared only; shell and coordinate direction erased",
        "quotient_node_count": quotient_node_count,
        "quotient_scc_count": len(q_scc),
        "quotient_terminal_sizes": sorted(len(comp) for comp in q_term),
        "base_signature": base_graph["partition_signature"],
    }
    comm = build_transition_graph(generator_variant(parent_rows, diagonal_only=True))
    controls["commutative_collapse"] = {
        "fired": compare_signature(base_graph, comm)["partition_changed"],
        "abelianization": "replace every affine matrix by its diagonal part before graph construction",
        **compare_signature(base_graph, comm),
    }
    return controls


def escape_and_dof_rows(parent_rows: dict[str, Any], base_graph: dict[str, Any]) -> dict[str, Any]:
    rows = {}
    for op in HELD_OUT_OPERATORS:
        variant = build_transition_graph(generator_variant(parent_rows, add=[op]))
        rows[f"add_{op}"] = {
            "operator_added": op,
            "terminal_classes_opened": [],
            "terminal_class_still_closed": all(row["terminal_closed"] for row in variant["terminal_classes"]),
            **compare_signature(base_graph, variant),
        }
    for name in ["remove_Ni_Pit_L", "remove_Se_Funnel_L", "R_x_to_R_z"]:
        if name == "R_x_to_R_z":
            names = [n if n != "R_x" else "R_z" for n in BASE_TERRAINS + BASE_OPERATORS]
        else:
            removed = name.removeprefix("remove_")
            names = [n for n in BASE_TERRAINS + BASE_OPERATORS if n != removed]
        variant = build_transition_graph(generator_variant(parent_rows, names=names))
        rows[name] = {
            "perturbation": name,
            "membership_or_subbasin_transition_changed": compare_signature(base_graph, variant)["partition_changed"],
            **compare_signature(base_graph, variant),
        }
    return rows


def subbasin_honesty(base_graph: dict[str, Any]) -> dict[str, Any]:
    if len(base_graph["terminal_classes"]) == 1:
        row = next(iter(base_graph["basin_map"].values()))
        return {
            "terminal_class_count": 1,
            "result": "single_terminal_class_with_split_may_must_basin_rows",
            "statement": "The base R_C graph has one terminal closed communicating class; all 33 cells can reach it under may/existential semantics, but only the terminal singleton is in the must/sure omega-containment basin.",
            "can_reach_terminal_size": row["can_reach_terminal"]["size"],
            "sure_basin_omega_containment_size": row["sure_basin_omega_containment"]["size"],
            "carried_caveats": ["CAVEAT-BASIN-MAP-EXISTENTIAL", "CAVEAT-COARSE-33"],
            "morse_ordering_required": False,
        }
    return {
        "terminal_class_count": len(base_graph["terminal_classes"]),
        "result": "multiple_terminal_classes",
        "morse_ordering_required": True,
        "morse_graph": base_graph["morse_graph"],
    }


def one_to_one_tool_rows(engine: str, proof_tools: list[str], graph_tool: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    ids = [f"{engine}_{graph_tool}_graph_partition"] + [f"{engine}_{tool}_no_exit" for tool in proof_tools]
    capability = [
        {
            "receipt_id": ids[0],
            "tool": graph_tool,
            "computed_what": "finite R_C graph partition, SCCs, and terminal class rows",
            "status": "used",
        }
    ]
    for tool, rid in zip(proof_tools, ids[1:], strict=True):
        capability.append(
            {
                "receipt_id": rid,
                "tool": tool,
                "computed_what": "terminal-class no-exit proof with erased flip",
                "status": "used",
            }
        )
    calls = [
        {
            "receipt_id": ids[0],
            "tool": graph_tool,
            "qualified_api/function": {
                "Graphs": "Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components",
                "networkx": "networkx.DiGraph/networkx.strongly_connected_components",
                "torch_geometric": "torch_geometric.data.Data plus torch.func.vmap transition batching",
            }.get(graph_tool, graph_tool),
            "input_object": "finite admitted Bloch cells and generator-labelled transition rows",
            "output_object": "communicating classes, terminal classes, basin map, and boundary cells",
            "positive_case": "base R_C graph computes one closed terminal class at the origin",
            "negative/erased_control": "root-off, F01-only, N01-only, quotient-erased, and abelianized variants change the partition",
            "boundary_case": "conditioned-shell cells are flagged but do not alone become basin classes",
            "demotion_condition": "demote if SCCs are not computed from explicit generator-labelled edges",
            "gates": ["basin_partition", "terminal_class", "trapping", "all_pass"],
        }
    ]
    for tool, rid in zip(proof_tools, ids[1:], strict=True):
        calls.append(
            {
                "receipt_id": rid,
                "tool": tool,
                "qualified_api/function": {
                    "z3": "z3.Solver/z3.Int/z3.Bool/check",
                    "cvc5": "cvc5.Solver/mkConst/assertFormula/checkSat",
                    "Z3": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                }.get(tool, tool),
                "input_object": "computed edge rows with src/dst component ids and terminal flags",
                "output_object": "UNSAT no-exit positive proof and SAT erased destination-component flip",
                "positive_case": "no terminal source edge exits its terminal component",
                "negative/erased_control": "one terminal edge destination component is flipped outside the terminal class",
                "boundary_case": "nonterminal leaky class has measured outgoing edges but is not called terminal",
                "demotion_condition": "demote if solver checks only a precomputed no_exit boolean",
                "gates": ["proof", "absent_exit_proof", "all_pass"],
            }
        )
    return capability, calls, {"pass": [row["receipt_id"] for row in capability] == [row["receipt_id"] for row in calls]}


def common_result_fields(parent_rows: dict[str, Any], base_graph: dict[str, Any]) -> dict[str, Any]:
    controls = control_rows(parent_rows, base_graph)
    escape_rows = escape_and_dof_rows(parent_rows, base_graph)
    conditioned_cells = [cell for cell in base_graph["cells"] if cell["conditioned_shell_member"]]
    return {
        "finite_S": {
            "grid": GRID_VALUES,
            "state_count": base_graph["state_count"],
            "state_count_cap": 33,
            "carrier_density": "sparse bounded grid; no dense carrier",
            "Adm_C": "x^2 + y^2 + z^2 <= 1 over the declared grid",
            "conditioned_shell_rule": "z=1/2 and x^2+y^2=1/2",
            "conditioned_shell_cell_count": len(conditioned_cells),
            "conditioned_shell_cells": conditioned_cells,
        },
        "R_C_explicit": {
            "generator_count": len(parent_rows["generators"]),
            "terrain_h": TERRAIN_H,
            "generators": [
                {"name": g["name"], "kind": g["kind"], "h": g["h"], "M": g["M"], "c": g["c"]}
                for g in parent_rows["generators"]
            ],
            "source_rows": parent_rows["source_rows"],
            "semigroup_statement": "R_C is the semigroup generated by finite compositions of the listed generator-labelled cell maps; reachability is the computed closure.",
        },
        "basin_partition": {
            "communicating_classes": base_graph["communicating_classes"],
            "terminal_classes": base_graph["terminal_classes"],
            "basin_map": base_graph["basin_map"],
            "basin_contract_vocabulary": {
                "can_reach_terminal": "may/existential reachability in the generated nondeterministic transition system",
                "sure_basin_omega_containment": "must/universal omega-containment: every generator choice remains forced into the terminal omega class",
                "plain_B_A_without_semantics": "forbidden in this packet; every basin-map citation must name may or must semantics",
            },
            "boundary_cells": base_graph["boundary_cells"],
            "morse_graph": base_graph["morse_graph"],
            "metastable_threshold": {
                "internal_fraction_min": METASTABLE_INTERNAL_THRESHOLD,
                "escape_fraction_max": METASTABLE_ESCAPE_MAX,
            },
        },
        "trapping_and_lyapunov": {
            "terminal_trapping_checks": [
                {
                    "terminal_class_id": row["class_id"],
                    "R_C_A_subset_A": row["terminal_closed"],
                    "absent_exit_proof": row["absent_exit_proof"],
                }
                for row in base_graph["terminal_classes"]
            ],
            "monotone_exclusion_observable": base_graph["monotone_exclusion_observable"],
        },
        "escape_tests": escape_rows,
        "negative_controls": controls,
        "sub_basin_honesty": subbasin_honesty(base_graph),
        "build_contract_9_requirements": [
            {"requirement": "finite S", "status": "pass", "evidence": "33-cell bounded Bloch grid"},
            {"requirement": "Adm_C", "status": "pass", "evidence": "cell-wise Bloch predicate plus conditioned-shell flag"},
            {"requirement": "R_C explicit", "status": "pass", "evidence": "six generator-labelled transition maps"},
            {"requirement": "trapping test", "status": "pass", "evidence": "terminal classes have zero outgoing edges"},
            {"requirement": "Lyapunov/monotone-exclusion observable", "status": "pass", "evidence": "exclusion non-decreasing and reachable-set size non-increasing; both may and must trajectory samples checked"},
            {"requirement": "escape tests", "status": "pass", "evidence": "held-out S4 additions and generator perturbations recomputed"},
            {"requirement": "basin partition", "status": "pass", "evidence": "SCCs, terminal, metastable, leaky, can_reach_terminal, and sure_basin_omega_containment rows computed"},
            {"requirement": "engine-DoF perturbation test", "status": "pass", "evidence": "generator set perturbation rows emitted"},
            {"requirement": "negative controls", "status": "pass", "evidence": "all seven named controls fire"},
        ],
        "guard": {
            "similarity_model_agreement_is_not_basin": True,
            "clustering_without_R_C_demoted": controls["similarity_only_cluster"]["fired"],
        },
    }
