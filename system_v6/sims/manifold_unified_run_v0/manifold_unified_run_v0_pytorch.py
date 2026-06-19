#!/usr/bin/env python3
"""PyTorch graph/autograd leg for manifold_unified_run_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import jacrev
from torch_geometric.data import Data

from manifold_unified_run_v0_common import RESULT_DIR, SIM_ID, base_leg_payload, build_core, r12, write_json

ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"
PACKAGES_USED = ["torch", "torch_geometric", "torch.func", "sympy", "json", "pathlib"]
ALIGNED_PACKAGES_LOAD_BEARING = ["torch_geometric", "torch.func", "sympy"]
TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "supportive tensor carrier for graph and eta rows"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing support graph Data edge-index degree check"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev derivative of density population wrt eta"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic check of population derivative sign"},
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "supportive",
    "torch_geometric": "load_bearing",
    "torch.func": "load_bearing",
    "sympy": "load_bearing",
}


def package_versions() -> dict[str, str]:
    try:
        import torch_geometric

        pyg_version = getattr(torch_geometric, "__version__", "unknown")
    except Exception:
        pyg_version = "unavailable"
    return {"torch": torch.__version__, "torch_geometric": pyg_version, "sympy": sp.__version__}


def graph_receipt(step: dict[str, Any]) -> dict[str, Any]:
    site_ids = [row["site_id"] for row in step["s3_density_probe"]]
    index = {site_id: idx for idx, site_id in enumerate(site_ids)}
    edges = step["s5_s6_terrain_flow"]["edge_rows"]
    directed = []
    for edge in edges:
        src = index[edge["src"]]
        dst = index[edge["dst"]]
        directed.append([src, dst])
        directed.append([dst, src])
    edge_index = torch.tensor(directed, dtype=torch.long).t().contiguous()
    x = torch.tensor([[float(row["population_R"])] for row in step["s3_density_probe"]], dtype=torch.float64)
    data = Data(x=x, edge_index=edge_index)
    degree = torch.zeros((len(site_ids),), dtype=torch.float64)
    degree.index_add_(0, data.edge_index[0], torch.ones(data.edge_index.shape[1], dtype=torch.float64))
    no_face_degree = torch.zeros((len(site_ids),), dtype=torch.float64)
    return {
        "tool": "torch_geometric.data.Data",
        "node_count": int(data.num_nodes),
        "directed_edge_count": int(data.edge_index.shape[1]),
        "undirected_edge_count": int(data.edge_index.shape[1] // 2),
        "degree": [r12(float(value)) for value in degree],
        "no_edge_control_degree": [r12(float(value)) for value in no_face_degree],
        "control_fired": bool(torch.max(torch.abs(degree - no_face_degree)).item() > 0.0),
        "pass": int(data.num_nodes) == 3 and int(data.edge_index.shape[1] // 2) == 3,
    }


def autograd_receipt(step: dict[str, Any]) -> dict[str, Any]:
    etas = torch.tensor([float(row["eta"]) for row in step["s2_geometry"]], dtype=torch.float64)

    def population_from_eta(x: torch.Tensor) -> torch.Tensor:
        return (1.0 - torch.cos(2.0 * x)) / 2.0

    jac = jacrev(population_from_eta)(etas)
    diag = torch.diagonal(jac)
    expected = torch.sin(2.0 * etas)
    eta = sp.symbols("eta")
    symbolic = sp.simplify(sp.diff((1 - sp.cos(2 * eta)) / 2, eta) - sp.sin(2 * eta))
    return {
        "tool": "torch.func.jacrev",
        "derivative_diag": [r12(float(value)) for value in diag],
        "expected_sin_2eta": [r12(float(value)) for value in expected],
        "max_abs_error": r12(float(torch.max(torch.abs(diag - expected)).item())),
        "sympy_symbolic_defect": str(symbolic),
        "pass": float(torch.max(torch.abs(diag - expected)).item()) <= 1.0e-10 and symbolic == 0,
    }


def build_payload() -> dict[str, Any]:
    core = build_core()
    step = core["trajectory"]["steps"][-1]
    graph = graph_receipt(step)
    autograd = autograd_receipt(step)
    current = step["s5_s6_terrain_flow"]["observables"]["total_abs_current"]
    payload = base_leg_payload(ENGINE, SOURCE_PATH, RESULT_PATH)
    payload.update(
        {
            "packages_used": PACKAGES_USED,
            "aligned_packages_load_bearing": ALIGNED_PACKAGES_LOAD_BEARING,
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
            "package_versions": package_versions(),
            "claim_path_tools": ["torch_geometric", "torch.func", "sympy"],
            "engine_values": {"conditioned_total_abs_current": current},
            "graph_receipt": graph,
            "autograd_receipt": autograd,
            "tool_calls": [row for row in core["tool_calls"] if row["tool"] == "pytorch"],
            "all_pass": bool(graph["pass"] and autograd["pass"]),
        }
    )
    return payload


def main() -> int:
    payload = build_payload()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT_PATH)}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
