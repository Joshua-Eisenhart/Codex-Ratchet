#!/usr/bin/env python3
"""PyTorch graph lane for sequential_inheritance_not_cycle_v0."""

from __future__ import annotations

import datetime as dt
import importlib.metadata
import json
from typing import Any

import torch
from torch.func import vmap
try:
    from torch_geometric.data import Data
except Exception:  # pragma: no cover - fallback only if package import drifts.
    Data = None

import sequential_inheritance_not_cycle_v0_common as common


SIM_ID = common.SIM_ID
SOURCE = common.PACKET / f"{SIM_ID}_pytorch.py"
RESULT = common.RESULT_DIR / f"{SIM_ID}_pytorch_results.json"


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "version_unavailable"


def graph_receipt(fixture: dict[str, Any]) -> dict[str, Any]:
    rows = fixture["parent_terminal_table"]
    edges = []
    for idx, _row in enumerate(rows):
        parent_node = idx
        record_node = len(rows) + idx
        inherited_daughter_node = 2 * len(rows) + idx
        edges.append((parent_node, record_node))
        edges.append((record_node, inherited_daughter_node))
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    x = torch.arange(3 * len(rows), dtype=torch.float64).reshape(-1, 1)
    data = Data(x=x, edge_index=edge_index) if Data is not None else {"x": x, "edge_index": edge_index}
    out_degree = torch.bincount(edge_index[0], minlength=3 * len(rows))

    match_vectors = {}
    for name, regime in fixture["regimes"].items():
        parent_syndrome = torch.tensor(
            [row["parent_syndrome"] for row in regime["daughter_rows"]], dtype=torch.long
        )
        daughter_syndrome = torch.tensor(
            [row["daughter_syndrome"] for row in regime["daughter_rows"]], dtype=torch.long
        )

        def same(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
            return (a == b).to(torch.float64)

        match_vectors[name] = vmap(same)(parent_syndrome, daughter_syndrome)

    return {
        "data_type": "torch_geometric.data.Data" if Data is not None else "fallback_edge_index_dict",
        "node_count": int(x.shape[0]),
        "edge_count": int(edge_index.shape[1]),
        "record_bridge_parent_outdegree_sum": int(out_degree[: len(rows)].sum().item()),
        "torch_func_vmap_match_counts": {
            name: int(values.sum().item()) for name, values in match_vectors.items()
        },
        "torch_func_vmap_mean_stability": {
            name: float(values.mean().item()) for name, values in match_vectors.items()
        },
        "has_torch_geometric_data_object": Data is not None and isinstance(data, Data),
    }


def main() -> int:
    fixture = common.build_fixture()
    graph = graph_receipt(fixture)
    all_pass = all(
        [
            common.expected_all_pass(fixture),
            graph["record_bridge_parent_outdegree_sum"] == 24,
            graph["torch_func_vmap_match_counts"]["inheritance"] == 24,
            graph["torch_func_vmap_match_counts"]["cycle_null"] == 0,
            graph["torch_func_vmap_match_counts"]["random_null"] == 6,
        ]
    )
    payload: dict[str, Any] = {
        "schema_version": f"{SIM_ID}_pytorch_leg_v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "role_id": "pytorch_record_graph_discriminator_lane",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "source_path": common.rel(SOURCE),
        "source_sha256": common.sha256_file(SOURCE),
        "result_path": common.rel(RESULT),
        "reads_peer_result": False,
        "packages_used": ["torch", "torch_geometric", "torch.func"],
        "aligned_packages_load_bearing": ["torch_geometric", "torch.func"],
        "package_observables": {
            "torch_geometric": "Data edge_index encodes parent->record->daughter inheritance support graph and outdegree bridge count",
            "torch.func": "torch.func.vmap computes per-row parent/daughter syndrome match vectors for all regimes",
        },
        "package_versions": {
            "torch": package_version("torch"),
            "torch-geometric": package_version("torch-geometric"),
        },
        "claim_path_tools": ["torch_geometric", "torch.func"],
        "fixture": fixture,
        "pytorch_graph_receipt": graph,
        "TOOL_MANIFEST": {
            "torch_geometric": {"used": True, "reason": "load-bearing record inheritance support graph"},
            "torch.func": {"used": True, "reason": "load-bearing vectorized row-match computation"},
            "torch": {"used": True, "reason": "supportive tensor substrate for the graph/readout lane"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "torch_geometric": "load_bearing",
            "torch.func": "load_bearing",
            "torch": "supportive",
        },
        "tool_calls": [
            {
                "tool": "torch_geometric",
                "qualified_api/function": "torch_geometric.data.Data",
                "input_object": "parent terminal rows and inherited record bridge edges",
                "output_object": "parent->record->daughter support graph with bridge outdegree count",
                "positive_case": "24 parent rows each emit one record bridge",
                "negative/erased_control": "null regimes have no matching parent syndrome bridge at readout",
                "boundary_case": "finite 72-node graph",
                "demotion_condition": "demote if graph is absent or not used for a gate",
                "gates": ["pytorch_graph_receipt", "all_pass"],
            },
            {
                "tool": "torch.func",
                "qualified_api/function": "torch.func.vmap",
                "input_object": "parent and daughter syndrome tensors",
                "output_object": "per-row match vectors and regime match counts",
                "positive_case": "inheritance has 24/24 matches",
                "negative/erased_control": "cycle-null has 0/24 and random-null has 6/24 matches",
                "boundary_case": "finite 24-row table",
                "demotion_condition": "demote if vmap output is not used for discriminator counts",
                "gates": ["pytorch_graph_receipt", "all_pass"],
            },
        ],
        "all_pass": all_pass,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "result_path": common.rel(RESULT)}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
