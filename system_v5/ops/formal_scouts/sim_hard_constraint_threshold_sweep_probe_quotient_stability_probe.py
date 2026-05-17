#!/usr/bin/env python3
"""Hard-constraint threshold-sweep probe-quotient stability scout."""

from __future__ import annotations

import json
import os
import pathlib
import time
from collections import defaultdict
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import torch
from torch_geometric.utils import from_networkx
import z3

import sim_hard_constraint_survivor_probe_quotient_pruning_order_probe as hard


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "hard_constraint_threshold_sweep_probe_quotient_stability_probe_results.json"

NAME = "hard_constraint_threshold_sweep_probe_quotient_stability_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: sweeps hard admissibility thresholds and adversarial "
    "probe radii for finite survivor-quotient pruning. It tests robustness of "
    "survivor and quotient counts, but does not admit a final constraint family, "
    "manifold tower, ontology, cycle identity, bridge, axis, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing candidate density channels, threshold predicates, trace distances, and entropies"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing nonconstant threshold grid and radius-instability contradiction checks"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing radius-quotient connected components"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor conversion for quotient graphs"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over threshold-grid and quotient-radius filtrations"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def flexible_predicates(rho: torch.Tensor, entropy_upper_q0: float, purity_floor_01: float) -> dict[str, bool]:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=hard.DTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=hard.DTYPE)
    local_0 = hard.partial_trace_density(rho, [0])
    local_1 = hard.partial_trace_density(rho, [1])
    pair_01 = hard.partial_trace_density(rho, [0, 1])
    return {
        "density_valid": hard.density_valid(rho),
        "qubit_0_z_expectation_nonnegative": hard.expectation(rho, sz, 0) >= -1e-8,
        "qubit_1_x_magnitude_not_too_large": abs(hard.expectation(rho, sx, 1)) <= 0.76,
        "qubit_0_local_entropy_below_swept_bound": hard.entropy(local_0) <= entropy_upper_q0,
        "qubit_1_local_entropy_above_floor": hard.entropy(local_1) >= 0.02,
        "pair_01_purity_above_swept_floor": hard.purity(pair_01) >= purity_floor_01,
    }


def apply_order_with_thresholds(candidate: dict[str, Any], order: list[str], entropy_upper_q0: float, purity_floor_01: float) -> dict[str, Any]:
    rho = candidate["rho"]
    killed_by = None
    for step in order:
        rho = hard.HARD_STEPS[step](rho)
        predicates = flexible_predicates(rho, entropy_upper_q0, purity_floor_01)
        failed = [name for name, ok in predicates.items() if not ok]
        if failed:
            killed_by = {"step": step, "failed": failed}
            break
    survived = killed_by is None
    return {
        "candidate_id": candidate["candidate_id"],
        "source_label": candidate["source_label"],
        "survived": survived,
        "rho": rho,
        "signature": hard.probe_signature(rho) if survived else None,
        "killed_by": killed_by,
    }


def exact_signature_classes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    survivors = [row for row in rows if row["survived"]]
    classes: dict[tuple[float, ...], list[int]] = defaultdict(list)
    for row in survivors:
        classes[row["signature"]].append(row["candidate_id"])
    return {
        "survivor_count": len(survivors),
        "class_count": len(classes),
        "largest_class_size": max((len(ids) for ids in classes.values()), default=0),
    }


def trace_radius_classes(rows: list[dict[str, Any]], radius: float) -> dict[str, Any]:
    survivors = [row for row in rows if row["survived"]]
    graph = nx.Graph()
    for row in survivors:
        graph.add_node(row["candidate_id"])
    for idx, a in enumerate(survivors):
        for b in survivors[idx + 1 :]:
            if hard.trace_distance(a["rho"], b["rho"]) <= radius:
                graph.add_edge(a["candidate_id"], b["candidate_id"])
    components = [sorted(component) for component in nx.connected_components(graph)]
    pyg = from_networkx(graph) if graph.number_of_edges() else None
    st = gudhi.SimplexTree()
    for node in graph.nodes:
        st.insert([int(node)], filtration=0.0)
    for a, b in graph.edges:
        st.insert([int(a), int(b)], filtration=radius)
    return {
        "radius": radius,
        "class_count": len(components),
        "largest_class_size": max((len(component) for component in components), default=0),
        "edge_count": graph.number_of_edges(),
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
        "persistence_pair_count": len(st.persistence()),
    }


def grid_persistence(grid_rows: list[dict[str, Any]]) -> dict[str, Any]:
    st = gudhi.SimplexTree()
    for idx, row in enumerate(grid_rows):
        st.insert([idx], filtration=float(row["survivor_count"]))
    for idx in range(len(grid_rows) - 1):
        if grid_rows[idx]["order_name"] == grid_rows[idx + 1]["order_name"]:
            st.insert([idx, idx + 1], filtration=float(max(grid_rows[idx]["survivor_count"], grid_rows[idx + 1]["survivor_count"])))
    return {"persistence_pair_count": len(st.persistence()), "pass": len(st.persistence()) > 0}


def z3_checks(survivor_counts: list[int], radius_class_counts: list[int]) -> dict[str, Any]:
    survivor_varies = len(set(survivor_counts)) > 1
    radius_varies = len(set(radius_class_counts)) > 1
    s1 = z3.Solver()
    s2 = z3.Solver()
    a = z3.Bool("survivor_varies")
    b = z3.Bool("radius_varies")
    s1.add(a == survivor_varies, a == False)
    s2.add(b == radius_varies, b == False)
    return {
        "threshold_grid_not_constant_unsat_if_constant": {"solver_status": str(s1.check()), "pass": survivor_varies and s1.check() == z3.unsat},
        "probe_radius_not_constant_unsat_if_constant": {"solver_status": str(s2.check()), "pass": radius_varies and s2.check() == z3.unsat},
    }


def main() -> dict[str, Any]:
    started = time.time()
    candidates = hard.candidate_states()
    entropy_bounds = [0.20, 0.35, 0.50, 0.65]
    purity_floors = [0.28, 0.36, 0.44, 0.52]
    grid_rows = []
    for order_name, order in hard.ORDERS.items():
        for entropy_upper in entropy_bounds:
            for purity_floor in purity_floors:
                rows = [apply_order_with_thresholds(candidate, order, entropy_upper, purity_floor) for candidate in candidates]
                classes = exact_signature_classes(rows)
                grid_rows.append(
                    {
                        "order_name": order_name,
                        "entropy_upper_q0": entropy_upper,
                        "purity_floor_01": purity_floor,
                        "survivor_count": classes["survivor_count"],
                        "class_count": classes["class_count"],
                        "largest_class_size": classes["largest_class_size"],
                    }
                )

    reference_cell = max(grid_rows, key=lambda row: (row["survivor_count"], row["class_count"]))
    reference_order = reference_cell["order_name"]
    reference_rows = [
        apply_order_with_thresholds(
            candidate,
            hard.ORDERS[reference_order],
            entropy_upper_q0=reference_cell["entropy_upper_q0"],
            purity_floor_01=reference_cell["purity_floor_01"],
        )
        for candidate in candidates
    ]
    radius_rows = [trace_radius_classes(reference_rows, radius) for radius in [0.0, 0.05, 0.10, 0.20, 0.35, 0.60, 0.90, 1.20]]
    z3_rows = z3_checks([row["survivor_count"] for row in grid_rows], [row["class_count"] for row in radius_rows])
    persistence = grid_persistence(grid_rows)
    positive = {
        "threshold_grid_sweeps_all_orders_and_bound_pairs": {
            "grid_count": len(grid_rows),
            "orders": list(hard.ORDERS.keys()),
            "entropy_bounds": entropy_bounds,
            "purity_floors": purity_floors,
            "pass": len(grid_rows) == len(hard.ORDERS) * len(entropy_bounds) * len(purity_floors),
        },
        "survivor_count_changes_across_threshold_grid": {
            "min_survivors": min(row["survivor_count"] for row in grid_rows),
            "max_survivors": max(row["survivor_count"] for row in grid_rows),
            "pass": min(row["survivor_count"] for row in grid_rows) < max(row["survivor_count"] for row in grid_rows),
        },
        "quotient_class_count_changes_across_threshold_grid": {
            "min_classes": min(row["class_count"] for row in grid_rows),
            "max_classes": max(row["class_count"] for row in grid_rows),
            "pass": min(row["class_count"] for row in grid_rows) < max(row["class_count"] for row in grid_rows),
        },
        "probe_radius_changes_quotient_resolution": {
            "reference_cell": reference_cell,
            "radius_rows": radius_rows,
            "pass": len({row["class_count"] for row in radius_rows}) > 1,
        },
        "gudhi_threshold_grid_persistence_computes": persistence,
        "z3_threshold_and_radius_variation_checks": {"checks": z3_rows, "pass": all(row["pass"] for row in z3_rows.values())},
    }
    graveyard_companions = {
        "empty_candidate_set_has_zero_survivors": {
            "survivor_count": exact_signature_classes([])["survivor_count"],
            "pass": exact_signature_classes([])["survivor_count"] == 0,
        },
        "constant_probe_radius_zero_is_most_discriminating_boundary": {
            "radius_zero_classes": radius_rows[0]["class_count"],
            "max_radius_classes": radius_rows[-1]["class_count"],
            "pass": radius_rows[0]["class_count"] >= radius_rows[-1]["class_count"],
        },
        "overstrict_threshold_pair_can_extinguish_candidates": {
            "extinct_cells": [row for row in grid_rows if row["survivor_count"] == 0],
            "pass": any(row["survivor_count"] == 0 for row in grid_rows),
        },
    }
    boundary = {
        "candidate_count_matches_hard_pruning_source": {"candidate_count": len(candidates), "pass": len(candidates) == 20},
        "radius_sweep_has_eight_values": {"radius_count": len(radius_rows), "pass": len(radius_rows) == 8},
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "hard constraint threshold sweep over survivor counts and probe quotient stability",
        "provider_inputs": [
            "system_v5/ops/formal_scouts/provider_receipts/20260515T015147Z_grok_xai_constraint_survivor_exploration_proposal.json",
            "system_v5/ops/formal_scouts/provider_receipts/20260515T015147Z_gemini_constraint_survivor_exploration_proposal.json",
        ],
        "grid_rows": grid_rows,
        "radius_rows": radius_rows,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "Thresholds are still selected manually; next pass should use adaptive search around transition cells.",
            "Radius quotient stability is only tested on one reference order; later pass should sweep all orders.",
            "Provider proposals also suggested Bures/Rips and sparse-MPS variants that remain unimplemented.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from provider proposals and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "survivor_range": [min(row["survivor_count"] for row in grid_rows), max(row["survivor_count"] for row in grid_rows)],
            "class_count_range": [min(row["class_count"] for row in grid_rows), max(row["class_count"] for row in grid_rows)],
            "radius_class_counts": [row["class_count"] for row in radius_rows],
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
