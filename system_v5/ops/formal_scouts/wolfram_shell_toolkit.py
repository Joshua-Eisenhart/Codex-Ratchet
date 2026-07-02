"""Reusable Wolfram-style branch tools for shell-field formal scouts.

The functions here deliberately do not implement Wolfram's theory. They adapt
Wolfram-useful structures into the repo's primary object discipline:

  Omega_r branch table
  PEPS3D support attachment
  branchial compatibility kernel
  shell shear/stress comparison
  outward past-record emission

Every function is finite and keeps shell orientation/provenance explicit.
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from typing import Any

import rustworkx as rx
import torch
import xgi

RTYPE = torch.float64
EPS = 1.0e-12


def normalize_omega_branch_table(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize branch rows into explicit shell/Omega records."""
    normalized = []
    for fallback_id, row in enumerate(raw_rows):
        branch_id = str(row.get("branch_id", f"omega_{fallback_id}"))
        shell_r = int(row["shell_r"])
        orientation = str(row.get("orientation", "future_inward"))
        history = tuple(str(item) for item in row.get("history", ()))
        support_sites = tuple(int(site) for site in row.get("support_sites", ()))
        normalized.append(
            {
                "branch_id": branch_id,
                "shell_r": shell_r,
                "orientation": orientation,
                "history": history,
                "support_sites": support_sites,
            }
        )
    return normalized


def attach_peps3d_supports(
    branches: list[dict[str, Any]],
    site_floor_by_shell: dict[int, int],
) -> list[dict[str, Any]]:
    """Attach finite site/edge/face/cell support summaries to branch rows."""
    attached = []
    for row in branches:
        floor = int(site_floor_by_shell[int(row["shell_r"])])
        sites = tuple(sorted({int(site) % floor for site in row["support_sites"]}))
        if not sites:
            raise ValueError(f"branch {row['branch_id']} has empty PEPS3D support")
        edges = tuple((sites[i], sites[i + 1]) for i in range(len(sites) - 1))
        faces = tuple(tuple(sites[i : i + 3]) for i in range(max(0, len(sites) - 2)))
        cells = tuple(tuple(sites[i : i + 4]) for i in range(max(0, len(sites) - 3)))
        next_row = dict(row)
        next_row.update({"support_sites": sites, "support_edges": edges, "support_faces": faces, "support_cells": cells})
        attached.append(next_row)
    return attached


def build_incidence_hypergraph(branches: list[dict[str, Any]]) -> xgi.Hypergraph:
    """Build a higher-order incidence surface for branch/support/history rows."""
    graph = xgi.Hypergraph()
    for row in branches:
        graph.add_edge(
            [
                f"branch:{row['branch_id']}",
                f"shell:{row['shell_r']}:{row['orientation']}",
                f"support:{sum(row['support_sites'])}",
                f"history:{len(row['history'])}",
            ]
        )
    return graph


def branchial_distance_kernel(branches: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a branchial graph and return bounded compatibility weights."""
    graph = rx.PyGraph()
    node_by_id: dict[str, int] = {}
    support_by_id = {row["branch_id"]: set(row["support_sites"]) for row in branches}

    def node(branch_id: str) -> int:
        if branch_id not in node_by_id:
            node_by_id[branch_id] = graph.add_node(branch_id)
        return node_by_id[branch_id]

    for row in branches:
        node(row["branch_id"])

    rows = list(branches)
    for i, a in enumerate(rows):
        set_a = support_by_id[a["branch_id"]]
        for b in rows[i + 1 :]:
            set_b = support_by_id[b["branch_id"]]
            same_shell = int(a["shell_r"]) == int(b["shell_r"])
            overlap = len(set_a & set_b)
            if same_shell or overlap:
                graph.add_edge(node(a["branch_id"]), node(b["branch_id"]), {"same_shell": same_shell, "overlap": overlap})

    degrees = {graph[node_index]: graph.degree(node_index) for node_index in range(graph.num_nodes())}
    raw = torch.tensor([1.0 + degrees.get(row["branch_id"], 0) for row in branches], dtype=RTYPE)
    weights = raw / raw.sum().clamp_min(EPS)
    return {
        "graph_nodes": graph.num_nodes(),
        "graph_edges": graph.num_edges(),
        "weights": {row["branch_id"]: float(weights[i].item()) for i, row in enumerate(branches)},
        "degree_by_branch": degrees,
    }


def shell_shear_stress(reference_weights: dict[str, float], variant_weights: dict[str, float]) -> dict[str, float]:
    """Compare two branch-weight fields without losing branch ids."""
    branch_ids = sorted(set(reference_weights) | set(variant_weights))
    ref = torch.tensor([float(reference_weights.get(branch_id, 0.0)) for branch_id in branch_ids], dtype=RTYPE)
    var = torch.tensor([float(variant_weights.get(branch_id, 0.0)) for branch_id in branch_ids], dtype=RTYPE)
    ref = ref / ref.sum().clamp_min(EPS)
    var = var / var.sum().clamp_min(EPS)
    l1 = torch.linalg.vector_norm(ref - var, ord=1).item()
    l2 = torch.linalg.vector_norm(ref - var, ord=2).item()
    return {"l1": float(l1), "l2": float(l2), "max_abs": float((ref - var).abs().max().item())}


def emit_outward_record(branches: list[dict[str, Any]], weights: dict[str, float]) -> dict[str, Any]:
    """Emit past-facing provenance summaries after weighted compression."""
    by_shell: dict[int, float] = defaultdict(float)
    by_history_len: dict[int, float] = defaultdict(float)
    for row in branches:
        weight = float(weights.get(row["branch_id"], 0.0))
        by_shell[int(row["shell_r"])] += weight
        by_history_len[len(row["history"])] += weight
    return {
        "orientation": "past_outward",
        "weight_by_shell": {str(k): round(v, 12) for k, v in sorted(by_shell.items())},
        "weight_by_history_len": {str(k): round(v, 12) for k, v in sorted(by_history_len.items())},
        "record_entropy_bits": _entropy_bits(list(weights.values())),
    }


def _entropy_bits(values: list[float]) -> float:
    weights = torch.tensor(values, dtype=RTYPE)
    weights = weights / weights.sum().clamp_min(EPS)
    return float(-(weights * torch.log2(weights.clamp_min(EPS))).sum().item())


def toolkit_selftest(raw_rows: list[dict[str, Any]], site_floor_by_shell: dict[int, int]) -> dict[str, Any]:
    """Run a finite self-test over the toolkit functions."""
    normalized = normalize_omega_branch_table(raw_rows)
    attached = attach_peps3d_supports(normalized, site_floor_by_shell)
    incidence = build_incidence_hypergraph(attached)
    kernel = branchial_distance_kernel(attached)
    uniform = {row["branch_id"]: 1.0 for row in attached}
    stress = shell_shear_stress(uniform, kernel["weights"])
    record = emit_outward_record(attached, kernel["weights"])
    shell_queue = deque(sorted({int(row["shell_r"]) for row in attached}))
    shell_order = list(shell_queue)
    all_pass = (
        len(attached) == len(raw_rows)
        and incidence.num_edges == len(attached)
        and kernel["graph_nodes"] == len(attached)
        and abs(sum(kernel["weights"].values()) - 1.0) < 1.0e-9
        and record["orientation"] == "past_outward"
        and shell_order == sorted(shell_order)
    )
    return {
        "all_pass": all_pass,
        "normalized_rows": len(normalized),
        "attached_rows": len(attached),
        "incidence_hyperedges": incidence.num_edges,
        "branchial_graph_nodes": kernel["graph_nodes"],
        "branchial_graph_edges": kernel["graph_edges"],
        "kernel_weight_sum": round(sum(kernel["weights"].values()), 12),
        "uniform_vs_branchial_stress": {k: round(v, 12) for k, v in stress.items()},
        "outward_record": record,
        "shell_order": shell_order,
    }
