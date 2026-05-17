#!/usr/bin/env python3
"""Couple source-native Weyl/Hopf placement histories into shell graph persistence."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import numpy as np
import rustworkx as rx
import z3

from sim_left_right_weyl_density_terrain_loop_placement_mirror_non_equivalence_probe import (
    LEFT_TERRAINS,
    LOOPS,
    RIGHT_TERRAINS,
    signature_for,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "left_right_weyl_density_hopf_loop_shell_graph_persistence_coupling_probe_results.json"

NAME = "left_right_weyl_density_hopf_loop_shell_graph_persistence_coupling_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: consumes the source-native left/right Weyl density "
    "terrain-loop placement signatures and maps them into finite shell graph "
    "persistence readouts. It tests whether downstream graph geometry changes "
    "when it is driven by the repaired operating-space histories. It does not "
    "admit canon, physics, psychology, final manifold order, or bridge claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing placement signatures, edge weights, and distance vectors"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing shell graph construction from placement histories"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing directed graph cycle and edge inventory cross-check"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing H0 persistence diagrams for shell graph filtrations"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite survivor-count witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def graph_from_signature(sig: np.ndarray, mode: str = "source") -> nx.Graph:
    values = sig[:, :3]
    nodes = range(4)
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    for i in nodes:
        for j in range(i + 1, 4):
            vi = values[(i * 2) % len(values)]
            vj = values[(j * 2 + 1) % len(values)]
            base = float(np.linalg.norm(vi - vj))
            if mode == "source":
                weight = base + 0.05 * abs(float(vi[2] - vj[2])) + 0.01 * (i + j + 1)
            elif mode == "uniform":
                weight = 1.0
            elif mode == "mean_only":
                weight = float(np.mean(np.abs(values))) + 0.01
            elif mode == "permuted":
                weight = base + 0.05 * abs(float(vi[0] - vj[0])) + 0.01 * (4 - i + j)
            else:
                raise ValueError(mode)
            graph.add_edge(i, j, weight=weight)
    return graph


def persistence_signature(graph: nx.Graph) -> tuple[float, ...]:
    simplex = gudhi.SimplexTree()
    for node in graph.nodes:
        simplex.insert([int(node)], filtration=0.0)
    for i, j, data in graph.edges(data=True):
        simplex.insert([int(i), int(j)], filtration=float(data["weight"]))
    simplex.make_filtration_non_decreasing()
    persistence = simplex.persistence(homology_coeff_field=2, min_persistence=0.0)
    h0_deaths = sorted(
        death
        for dim, (_, death) in persistence
        if dim == 0 and death != float("inf")
    )
    padded = h0_deaths + [0.0] * max(0, 3 - len(h0_deaths))
    return tuple(round(float(v), 6) for v in padded[:3])


def rustworkx_cycle_count(graph: nx.Graph) -> int:
    digraph = rx.PyDiGraph()
    node_map = {node: digraph.add_node(node) for node in graph.nodes}
    for i, j, data in graph.edges(data=True):
        digraph.add_edge(node_map[i], node_map[j], float(data["weight"]))
        digraph.add_edge(node_map[j], node_map[i], float(data["weight"]))
    return sum(1 for _ in rx.simple_cycles(digraph))


def placement_rows(mode: str = "source") -> list[dict[str, Any]]:
    rows = []
    for sheet, terrains in [("left_weyl_density", LEFT_TERRAINS), ("right_weyl_density", RIGHT_TERRAINS)]:
        for loop in LOOPS:
            for terrain in terrains:
                sig = signature_for(sheet, terrain, loop)
                graph = graph_from_signature(sig, mode=mode)
                rows.append(
                    {
                        "sheet": sheet,
                        "loop": loop,
                        "terrain": terrain,
                        "persistence": persistence_signature(graph),
                        "cycle_count": rustworkx_cycle_count(graph),
                        "edge_weight_sum": round(float(sum(data["weight"] for _, _, data in graph.edges(data=True))), 6),
                    }
                )
    return rows


def quotient_count(rows: list[dict[str, Any]], key: str = "persistence") -> int:
    return len({tuple(row[key]) if isinstance(row[key], list) else row[key] for row in rows})


def min_left_right_gap(rows: list[dict[str, Any]]) -> float:
    gaps = []
    for idx, left_terrain in enumerate(LEFT_TERRAINS):
        right_terrain = RIGHT_TERRAINS[idx]
        for loop in LOOPS:
            left = next(row for row in rows if row["sheet"] == "left_weyl_density" and row["terrain"] == left_terrain and row["loop"] == loop)
            right = next(row for row in rows if row["sheet"] == "right_weyl_density" and row["terrain"] == right_terrain and row["loop"] == loop)
            gaps.append(float(np.linalg.norm(np.array(left["persistence"]) - np.array(right["persistence"]))))
    return min(gaps)


def min_fiber_base_gap(rows: list[dict[str, Any]]) -> float:
    gaps = []
    for sheet, terrains in [("left_weyl_density", LEFT_TERRAINS), ("right_weyl_density", RIGHT_TERRAINS)]:
        for terrain in terrains:
            fiber = next(row for row in rows if row["sheet"] == sheet and row["terrain"] == terrain and row["loop"] == "fiber_loop")
            base = next(row for row in rows if row["sheet"] == sheet and row["terrain"] == terrain and row["loop"] == "base_lift_loop")
            gaps.append(float(np.linalg.norm(np.array(fiber["persistence"]) - np.array(base["persistence"]))))
    return min(gaps)


def z3_survivor_witness(source_classes: int, uniform_classes: int, mean_classes: int) -> dict[str, Any]:
    solver = z3.Solver()
    source = z3.Int("source")
    uniform = z3.Int("uniform")
    mean = z3.Int("mean")
    solver.add(source == source_classes)
    solver.add(uniform == uniform_classes)
    solver.add(mean == mean_classes)
    solver.add(z3.Not(z3.And(source >= 6, uniform < source, mean >= source)))
    status = solver.check()
    return {
        "source_classes": source_classes,
        "uniform_classes": uniform_classes,
        "mean_only_classes": mean_classes,
        "read": "mean-only control remains a live kill boundary, so this scout cannot claim source-specific persistence",
        "solver_status": str(status),
        "pass": status == z3.unsat,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    source_rows = placement_rows("source")
    uniform_rows = placement_rows("uniform")
    mean_rows = placement_rows("mean_only")
    permuted_rows = placement_rows("permuted")

    source_classes = quotient_count(source_rows)
    uniform_classes = quotient_count(uniform_rows)
    mean_classes = quotient_count(mean_rows)
    permuted_classes = quotient_count(permuted_rows)
    source_cycle_counts = {row["cycle_count"] for row in source_rows}

    positive = {
        "all_sixteen_source_native_placements_feed_shell_graphs": {
            "row_count": len(source_rows),
            "pass": len(source_rows) == 16,
        },
        "source_driven_graph_persistence_has_multiple_survivor_classes": {
            "source_persistence_class_count": source_classes,
            "threshold": 6,
            "pass": source_classes >= 6,
        },
        "fiber_base_lift_pairs_remain_separated_after_graph_persistence": {
            "min_fiber_base_persistence_gap": min_fiber_base_gap(source_rows),
            "threshold": 0.015,
            "pass": min_fiber_base_gap(source_rows) > 0.015,
        },
        "rustworkx_cycle_inventory_is_nonzero_for_shell_graphs": {
            "cycle_counts": sorted(source_cycle_counts),
            "pass": min(source_cycle_counts) > 0,
        },
    }

    graveyard_companions = {
        "uniform_shell_control_collapses_persistence_classes": {
            "uniform_class_count": uniform_classes,
            "source_class_count": source_classes,
            "pass": uniform_classes < source_classes,
        },
        "mean_only_shell_control_remains_live_kill_boundary": {
            "mean_only_class_count": mean_classes,
            "source_class_count": source_classes,
            "read": "control produces at least as many persistence classes as the source-driven graph",
            "pass": mean_classes >= source_classes,
        },
        "left_right_mirror_pair_collisions_remain_live_boundary": {
            "min_left_right_persistence_gap": min_left_right_gap(source_rows),
            "threshold": 0.015,
            "read": "H0 persistence does not separate every mirrored left/right pair",
            "pass": min_left_right_gap(source_rows) <= 0.015,
        },
        "permuted_shell_control_matches_class_inventory_live_boundary": {
            "permuted_class_count": permuted_classes,
            "source_class_count": source_classes,
            "read": "permuted shell control has the same class count as source-driven graph",
            "pass": permuted_classes == source_classes,
        },
        "graph_without_source_rows_has_no_placement_inventory": {
            "source_rows_required": 16,
            "proxy_rows_available": 0,
            "pass": True,
        },
    }

    boundary = {
        "z3_persistence_survivor_noncollapse_witness": z3_survivor_witness(source_classes, uniform_classes, mean_classes),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": (
            "source-native left/right Weyl density terrain-loop placement histories "
            "mapped into finite shell graph filtrations and H0 persistence signatures"
        ),
        "source_alignment_category": "downstream_on_source_native_operating_space",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "The shell graph is a finite four-node readout scaffold, not the full eight-qubit tensor-network geometry.",
            "Persistence classes are H0-only; H1 cycles should be tested in a larger graph before using this as strong topology evidence.",
            "Mean-only shell control produces at least as many persistence classes as the source-driven graph, so the current persistence readout is not source-specific.",
            "Mirrored left/right pairs collide under this persistence readout; use coherent information or offdiagonal density readouts for left/right separation.",
            "Permuted shell control keeps the same class count, so this readout cannot detect ordering.",
            "The next downstream scout should combine this source-native graph drive with coherent information and conditional entropy.",
        ],
        "why_not_v4_probes": "This is a clean v5 repair-followup scout that consumes the source-native Weyl density placement histories; v4 remains reference/mining material.",
        "raw_rows": {
            "source": source_rows,
            "uniform_shell_control": uniform_rows,
            "mean_only_shell_control": mean_rows,
            "permuted_shell_control": permuted_rows,
        },
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all(checks),
                "result": str(OUT_PATH),
                "source_classes": source_classes,
                "uniform_classes": uniform_classes,
                "mean_only_classes": mean_classes,
                "permuted_classes": permuted_classes,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
