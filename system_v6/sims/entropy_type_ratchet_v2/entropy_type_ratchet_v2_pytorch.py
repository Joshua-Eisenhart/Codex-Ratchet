#!/usr/bin/env python3
"""PyTorch graph/autograd leg for entropy_type_ratchet_v2."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev, vmap
from torch_geometric.data import Data

from entropy_type_ratchet_v2_common import (
    RESULT_DIR,
    SIM_ID,
    TYPE_ORDER,
    base_leg_payload,
    build_discovery_packet,
    discovery_status_matrix,
    final_values,
    rel,
    write_json,
)


SOURCE = Path(__file__).resolve()
RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "version_unavailable"


def graph_receipt(table: dict[str, Any]) -> dict[str, Any]:
    matrix = torch.tensor(discovery_status_matrix(table), dtype=torch.float64)
    edge_sources = []
    edge_targets = []
    edge_labels = []
    previous = torch.zeros(matrix.shape[1], dtype=torch.float64)
    for step in range(matrix.shape[0]):
        current = matrix[step]
        changed = torch.nonzero(current != previous).flatten().tolist()
        for type_index in changed:
            edge_sources.append(step)
            edge_targets.append(matrix.shape[0] + type_index)
            edge_labels.append(f"{table['rows'][step]['step_id']}->{TYPE_ORDER[type_index]}")
        previous = current
    edge_index = torch.tensor([edge_sources, edge_targets], dtype=torch.long)
    x = torch.cat([matrix.sum(dim=1), matrix.sum(dim=0)]).reshape(-1, 1)
    data = Data(x=x, edge_index=edge_index)
    data.validate(raise_on_error=True)
    degree = torch.zeros(data.num_nodes, dtype=torch.float64)
    degree.scatter_add_(0, edge_index[0], torch.ones(edge_index.shape[1], dtype=torch.float64))
    final_count = int((matrix[-1] > 0).sum().item())
    changed_type_count = int((degree[: matrix.shape[0]] > 0).sum().item())
    return {
        "ran": True,
        "tool": "torch_geometric",
        "data_validate": True,
        "num_nodes": int(data.num_nodes),
        "num_edges": int(data.num_edges),
        "edge_labels": edge_labels,
        "step_out_degree": [float(x) for x in degree[: matrix.shape[0]].tolist()],
        "changed_step_count": changed_type_count,
        "final_available_type_count": final_count,
        "pass": data.num_edges >= len(TYPE_ORDER) and final_count == len(TYPE_ORDER),
    }


def torch_func_receipt(table: dict[str, Any]) -> dict[str, Any]:
    matrix = torch.tensor(discovery_status_matrix(table), dtype=torch.float64)

    def scaled_final_count(scale: torch.Tensor) -> torch.Tensor:
        weights = torch.sigmoid(scale * matrix[-1])
        return weights.sum()

    scales = torch.tensor([0.5, 1.0, 2.0], dtype=torch.float64)
    values = vmap(scaled_final_count)(scales)
    jacobian = vmap(jacrev(scaled_final_count))(scales)
    return {
        "ran": True,
        "tool": "torch.func",
        "values": [float(x) for x in values.tolist()],
        "jacobian": [float(x) for x in jacobian.tolist()],
        "positive_derivative": all(float(x) > 0.0 for x in jacobian.tolist()),
        "pass": bool(torch.all(jacobian > 0.0).item()),
        "gates": ["operator_co_ratchet_boundary", "all_pass"],
    }


def density_tensor_receipt(table: dict[str, Any]) -> dict[str, Any]:
    rho_row = next(row for row in table["rows"] if row["entropy_types"]["von_neumann_entropy"]["status"] == "computable")
    rho = torch.tensor(rho_row["entropy_types"]["von_neumann_entropy"]["rho"]["rho_matrix"], dtype=torch.float64)
    evals = torch.linalg.eigvalsh(rho)
    entropy = -torch.sum(torch.where(evals > 0, evals * torch.log(evals), torch.zeros_like(evals)))
    return {
        "ran": True,
        "tool": "torch.linalg",
        "rho_eigenvalues": [float(x) for x in evals.tolist()],
        "rho_entropy_nats": float(entropy.item()),
        "trace": float(torch.trace(rho).item()),
        "psd": bool(torch.all(evals >= -1.0e-12).item()),
        "pass": abs(float(entropy.item()) - float(torch.log(torch.tensor(2.0, dtype=torch.float64)).item())) <= 1.0e-10,
    }


def build_result() -> dict[str, Any]:
    packet = build_discovery_packet()
    table = packet["type_admissibility_table"]
    graph = graph_receipt(table)
    func = torch_func_receipt(table)
    density = density_tensor_receipt(table)
    engine_values = final_values(table)
    all_pass = packet["all_pass"] and graph["pass"] and func["pass"] and density["pass"]
    payload = {
        **base_leg_payload("pytorch", SOURCE, RESULT),
        "packages_used": ["torch", "torch_geometric", "torch.func", "json", "pathlib", "importlib.metadata"],
        "aligned_packages_load_bearing": ["torch_geometric"],
        "package_observables": {
            "torch": "torch.tensor/torch.linalg.eigvalsh recomputes the vN entropy from the constructed density quotient rho matrix",
            "torch_geometric": "Data(edge_index=...) validates the construction-change graph induced by parent-derived table rows and all type-admissibility change edges",
            "torch.func": "torch.func.vmap/jacrev computes smoothed sensitivity of the final status tensor; supportive diagnostic only",
        },
        "claim_path_tools": ["torch_geometric"],
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "supportive density tensor/eigenvalue entropy check from constructed rho"},
            "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph validation of construction-change edges from parent-derived table rows to entropy types"},
            "torch.func": {"tried": True, "used": True, "reason": "supportive smoothed final-status sensitivity diagnostic"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "supportive", "torch_geometric": "load_bearing", "torch.func": "supportive"},
        "tool_versions": {name: package_version(name) for name in ["torch", "torch_geometric"]},
        "type_admissibility_table_hash": table["table_hash"],
        "controls": packet["controls"],
        "graph_receipt": graph,
        "torch_func_receipt": func,
        "density_tensor_receipt": density,
        "engine_values": engine_values,
        "tool_calls": [
            {
                "tool": "torch",
                "qualified_api/function": "torch.tensor/torch.linalg.eigvalsh/torch.log/torch.trace",
                "input_object": "constructed density quotient rho matrix from the parent-derived table",
                "output_object": "rho eigenvalues, trace, PSD check, and vN entropy log(2)",
                "positive_case": "rho eigenvalues [1/2, 1/2] give S=log(2) and trace=1",
                "negative/erased_control": "quotient-map erasure removes rho from the construction table before this receipt can run",
                "boundary_case": "two-class finite quotient density matrix",
                "demotion_condition": "demote if rho is not read from the construction table or eigvalsh entropy mismatches the exact row",
                "gates": ["rho", "entropy", "all_pass"],
            },
            {
                "tool": "torch_geometric",
                "qualified_api/function": "torch_geometric.data.Data/Data.validate",
                "input_object": "construction-change edges from discovered table rows to entropy types",
                "output_object": "validated graph with edge count and step out-degree",
                "positive_case": "final graph mirrors all six type nodes from construction-changing table rows",
                "negative/erased_control": "quotient-map erasure would remove the vN change edge in packet controls",
                "boundary_case": "steps with no new construction objects have zero new type edges",
                "demotion_condition": "demote if graph edges are not generated from construction-attempt table changes",
                "gates": ["all_pass"],
            },
            {
                "tool": "torch.func",
                "qualified_api/function": "torch.func.vmap/torch.func.jacrev",
                "input_object": "final discovered status tensor",
                "output_object": "positive sensitivity of smoothed final availability count",
                "positive_case": "jacrev is positive for live final availability statuses",
                "negative/erased_control": "zero status entries have zero contribution under erased construction",
                "boundary_case": "smooth sigmoid boundary, diagnostic only",
                "demotion_condition": "already supportive: derivative alone is not doctrine proof",
                "gates": ["all_pass"],
            },
        ],
        "all_pass": all_pass,
    }
    return payload


def main() -> int:
    payload = build_result()
    write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT)}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
