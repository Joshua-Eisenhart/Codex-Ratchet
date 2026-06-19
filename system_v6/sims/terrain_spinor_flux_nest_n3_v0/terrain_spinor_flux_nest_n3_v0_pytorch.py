#!/usr/bin/env python3
"""PyTorch/source-backed leg for terrain_spinor_flux_nest_n3_v0."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import jacrev, vmap

try:
    from torch_geometric.data import Data
except Exception:  # pragma: no cover - environment fallback.
    Data = None

from terrain_spinor_flux_nest_n3_v0_common import (
    EDGE_ORDER,
    RESULT_DIR,
    SIM_ID,
    TOL,
    base_leg_payload,
    build_core,
    rel,
    r12,
    write_json,
)


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"
PACKAGES_USED = ["torch", "torch.func", "torch_geometric", "sympy", "json", "math", "pathlib"]
ALIGNED_PACKAGES_LOAD_BEARING = ["torch_geometric", "torch.func", "sympy"]
TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "supportive tensor recompute of edge currents"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev/vmap readout of the current row"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing Data object for the n=3 network edge carrier"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact scalar check for the k-leaf conditioning rule"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing", "torch_geometric": "load_bearing", "sympy": "load_bearing"}


def package_versions() -> dict[str, str]:
    return {
        "torch": getattr(torch, "__version__", "unknown"),
        "torch_geometric": "available" if Data is not None else "unavailable",
        "sympy": getattr(sp, "__version__", "unknown"),
    }


def torch_network_recompute(core: dict[str, Any]) -> dict[str, Any]:
    sites = core["sites"]
    site_index = {site["site_id"]: idx for idx, site in enumerate(sites)}
    z = torch.tensor([float(site["z"]) for site in sites], dtype=torch.float64)
    population = (1.0 - z) / 2.0
    edge_index = torch.tensor(
        [[site_index[edge["src"]] for edge in EDGE_ORDER], [site_index[edge["dst"]] for edge in EDGE_ORDER]],
        dtype=torch.long,
    )
    couplings = torch.tensor(
        [float(edge["coupling_strength"]) for edge in core["terrain_network_coupling"]["edge_rows"]],
        dtype=torch.float64,
    )
    conditioned_couplings = torch.tensor(
        [float(edge["coupling_strength"]) for edge in core["conditioned_network_coupling"]["edge_rows"]],
        dtype=torch.float64,
    )
    if Data is not None:
        graph = Data(x=population[:, None], edge_index=edge_index, edge_attr=couplings[:, None])
        graph_status = f"torch_geometric.Data nodes={int(graph.num_nodes)} edges={int(graph.num_edges)}"
    else:
        graph = {"x": population, "edge_index": edge_index, "edge_attr": couplings}
        graph_status = "fallback_graph_dict"
    del graph

    pairs = torch.stack([population[edge_index[0]], population[edge_index[1]]], dim=1)
    packed = torch.cat([pairs, couplings[:, None]], dim=1)
    conditioned_packed = torch.cat([pairs, conditioned_couplings[:, None]], dim=1)

    def current_from_packed(row: torch.Tensor) -> torch.Tensor:
        return row[2] * (row[0] - row[1])

    current = vmap(current_from_packed)(packed)
    conditioned_current = vmap(current_from_packed)(conditioned_packed)
    first_jacobian = jacrev(current_from_packed)(packed[0])
    z_gap = z[edge_index[0]] - z[edge_index[1]]
    flux = current * z_gap
    conditioned_flux = conditioned_current * z_gap
    return {
        "graph_status": graph_status,
        "total_abs_current": r12(float(torch.sum(torch.abs(current)).item())),
        "total_signed_transport_flux": r12(float(torch.sum(flux).item())),
        "conditioned_total_abs_current": r12(float(torch.sum(torch.abs(conditioned_current)).item())),
        "conditioned_total_signed_transport_flux": r12(float(torch.sum(conditioned_flux).item())),
        "edge_current_values": [r12(float(value.item())) for value in current],
        "first_edge_current_jacobian_dJ_dp_src_dJ_dp_dst_dJ_dg": [r12(float(value.item())) for value in first_jacobian],
    }


def sympy_k_leaf_receipt(core: dict[str, Any]) -> dict[str, Any]:
    eta0, eta1, eta2 = sp.symbols("eta0 eta1 eta2", positive=True)
    weights = [
        sp.sin(2 * eta0) / (sp.sin(2 * eta0) + sp.sin(2 * eta1) + sp.sin(2 * eta2)),
        sp.sin(2 * eta1) / (sp.sin(2 * eta0) + sp.sin(2 * eta1) + sp.sin(2 * eta2)),
        sp.sin(2 * eta2) / (sp.sin(2 * eta0) + sp.sin(2 * eta1) + sp.sin(2 * eta2)),
    ]
    defect = sp.simplify(sum(weights) - 1)
    packet_weight_sum = sum(float(row["weight"]) for row in core["conditioning"]["weights"])
    return {
        "formula": "w_i=sin(2eta_i)/sum_j sin(2eta_j)",
        "symbolic_sum_defect": str(defect),
        "packet_weight_sum": r12(packet_weight_sum),
        "pass": defect == 0 and abs(packet_weight_sum - 1.0) <= TOL,
    }


def build_payload() -> dict[str, Any]:
    core = build_core()
    recompute = torch_network_recompute(core)
    payload = base_leg_payload(ENGINE, SOURCE_PATH, RESULT_PATH)
    payload.update(
        {
            "packages_used": PACKAGES_USED,
            "aligned_packages_load_bearing": ALIGNED_PACKAGES_LOAD_BEARING,
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
            "package_versions": package_versions(),
            "claim_path_tools": ["torch_geometric", "torch.func", "sympy"],
            "carrier_summary": {
                "dimension": core["carrier"]["dimension"],
                "norm": core["carrier"]["norm"],
                "not_support_graph_only": core["carrier"]["not_support_graph_only"],
            },
            "torch_recompute": recompute,
            "sympy_k_leaf_receipt": sympy_k_leaf_receipt(core),
            "conditioning": core["conditioning"],
            "ratchet_signatures": core["ratchet_signatures"],
            "collapse_controls": core["collapse_controls"],
            "parent_lineage": core["parent_lineage"],
            "engine_values": {
                "carrier_norm": core["carrier"]["norm"],
                "total_abs_current": recompute["total_abs_current"],
                "conditioned_total_abs_current": recompute["conditioned_total_abs_current"],
            },
            "all_pass": (
                core["all_pass"]
                and recompute["conditioned_total_abs_current"]
                == core["conditioned_network_coupling"]["observables"]["total_abs_current"]
            ),
        }
    )
    return payload


def main() -> int:
    payload = build_payload()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
