#!/usr/bin/env python3
"""e3nn x PyG equivariance-under-message-passing integration micro probe.

Tool-stage scope:
  - two primary tools: e3nn and PyG
  - exact prior surfaces:
      * e3nn o3.Irreps/tensor-product dimension micro
      * PyG MessagePassing.propagate/autograd micro
  - one tiny claim: additive PyG message passing commutes with a shared e3nn
    SO(3) vector irrep action on a bounded directed vector-feature graph.

This is below lego stage. It does not promote a graph/operator lego, learned
GNN equivariance, bridge, axis, or broad e3nn-PyG compatibility claim.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import torch
from e3nn import o3
from torch_geometric.nn import MessagePassing


classification = "canonical"
NAME = "sim_integration_e3nn_pyg_equivariance_under_mp_micro"
PROBE_FAMILY = "e3nn_pyg_equivariance_under_mp_micro"
CONSTRAINT_SET = "directed_vector_feature_message_passing_equivariance_fixture"

PRIOR_RECEIPTS = {
    "e3nn": "system_v4/probes/a2_state/sim_results/sim_e3nn_irreps_tensor_product_micro_results.json",
    "pyg": "system_v4/probes/a2_state/sim_results/sim_pyg_message_passing_autograd_micro_results.json",
}

IRREPS_VECTOR = o3.Irreps("1x1o")
TOLERANCE = 1e-5

_NOT_USED_REASON = (
    "not used: this integration micro isolates e3nn vector irreps and PyG "
    "additive message passing on one tiny graph; proof, topology, optimizer, "
    "lego, bridge, and broad coupling claims are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "PyTorch is supportive: tensors carry the e3nn/PyG feature fixtures "
            "and numeric equality checks."
        ),
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": (
            "PyG is load-bearing: MessagePassing.propagate supplies the directed "
            "additive aggregation that must commute with the shared irrep action."
        ),
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": (
            "e3nn is load-bearing: o3.Irreps and D_from_matrix supply the SO(3) "
            "vector representation used in the equivariance pass/fail check."
        ),
    },
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["pyg"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"


class SumVectorMessage(MessagePassing):
    def __init__(self):
        super().__init__(aggr="add")

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        _require_vector_features(x)
        return self.propagate(edge_index, x=x)

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        return x_j


class BiasedVectorMessage(MessagePassing):
    def __init__(self):
        super().__init__(aggr="add")
        self.bias = torch.tensor([[0.25, -0.5, 0.75]], dtype=torch.float64)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        _require_vector_features(x)
        return self.propagate(edge_index, x=x)

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        return x_j + self.bias.to(dtype=x_j.dtype, device=x_j.device)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_prior_receipts() -> dict[str, Any]:
    root = _repo_root()
    receipts = {}
    for tool, rel in PRIOR_RECEIPTS.items():
        path = root / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        source_rel = f"system_v4/probes/{data.get('name')}.py"
        source_path = root / source_rel
        result_mtime = path.stat().st_mtime if path.exists() else 0.0
        source_mtime = source_path.stat().st_mtime if source_path.exists() else 0.0
        receipts[tool] = {
            "path": rel,
            "source_path": source_rel,
            "exists": path.exists(),
            "source_exists": source_path.exists(),
            "all_pass": data.get("all_pass") is True,
            "classification": data.get("classification"),
            "load_bearing": data.get("tool_integration_depth", {}).get(tool) == "load_bearing",
            "result_mtime": result_mtime,
            "source_mtime": source_mtime,
            "result_fresh_for_source": (
                path.exists() and source_path.exists() and result_mtime >= source_mtime
            ),
            "name": data.get("name"),
        }
    return receipts


def _prior_receipts_ok(receipts: dict[str, Any]) -> bool:
    return all(
        item["exists"]
        and item["source_exists"]
        and item["all_pass"]
        and item["classification"] == "canonical"
        and item["load_bearing"]
        and item["result_fresh_for_source"]
        for item in receipts.values()
    )


def _require_vector_features(x: torch.Tensor) -> None:
    if x.ndim != 2 or x.shape[-1] != IRREPS_VECTOR.dim:
        raise ValueError(f"expected node features with last dimension {IRREPS_VECTOR.dim}")


def _edge_index_cycle() -> torch.Tensor:
    return torch.tensor([[0, 1, 2], [1, 2, 0]], dtype=torch.long)


def _features() -> torch.Tensor:
    return torch.tensor(
        [
            [1.0, 0.0, 0.5],
            [-0.5, 2.0, 1.0],
            [0.25, -1.0, 1.5],
        ],
        dtype=torch.float64,
    )


def _rotation_representation() -> torch.Tensor:
    angle = torch.tensor(0.7, dtype=torch.float64)
    rotation = torch.tensor(
        [
            [torch.cos(angle), -torch.sin(angle), 0.0],
            [torch.sin(angle), torch.cos(angle), 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=torch.float64,
    )
    return IRREPS_VECTOR.D_from_matrix(rotation).to(dtype=torch.float64)


def _rotate_features(x: torch.Tensor, representation: torch.Tensor) -> torch.Tensor:
    return x @ representation.T


def _as_nested_list(tensor: torch.Tensor) -> list[list[float]]:
    return [[float(value) for value in row] for row in tensor.detach().cpu()]


def run_positive_tests() -> dict[str, Any]:
    receipts = _load_prior_receipts()
    edge_index = _edge_index_cycle()
    x = _features()
    representation = _rotation_representation()
    layer = SumVectorMessage()

    base = layer(x, edge_index)
    rotate_then_message = layer(_rotate_features(x, representation), edge_index)
    message_then_rotate = _rotate_features(base, representation)
    max_error = float((rotate_then_message - message_then_rotate).abs().max())

    return {
        "prior_function_receipts_are_admissible": {
            "passed": _prior_receipts_ok(receipts),
            "receipts": receipts,
        },
        "pyg_additive_message_commutes_with_e3nn_vector_action": {
            "passed": max_error < TOLERANCE,
            "max_equivariance_error": max_error,
            "tolerance": TOLERANCE,
            "edge_semantics": "edge_index[0] source vectors add into edge_index[1] targets",
            "e3nn_irrep": str(IRREPS_VECTOR),
            "base_message": _as_nested_list(base),
        },
    }


def run_negative_tests() -> dict[str, Any]:
    edge_index = _edge_index_cycle()
    x = _features()
    representation = _rotation_representation()
    biased = BiasedVectorMessage()

    base = biased(x, edge_index)
    rotate_then_message = biased(_rotate_features(x, representation), edge_index)
    message_then_rotate = _rotate_features(base, representation)
    biased_error = float((rotate_then_message - message_then_rotate).abs().max())

    wrong_representation = torch.eye(IRREPS_VECTOR.dim, dtype=torch.float64)
    wrong_path = _rotate_features(SumVectorMessage()(x, edge_index), wrong_representation)
    correct_path = SumVectorMessage()(_rotate_features(x, representation), edge_index)
    wrong_rep_error = float((correct_path - wrong_path).abs().max())

    malformed_rejected = False
    malformed_error = ""
    try:
        SumVectorMessage()(torch.ones(3, IRREPS_VECTOR.dim + 1, dtype=torch.float64), edge_index)
    except ValueError as exc:
        malformed_rejected = True
        malformed_error = str(exc)

    return {
        "fixed_unrotated_bias_breaks_equivariance": {
            "passed": biased_error > 0.05,
            "biased_equivariance_error": biased_error,
            "exclusion_note": "A message that adds a fixed unrotated vector is not equivariant.",
        },
        "wrong_output_representation_is_excluded": {
            "passed": wrong_rep_error > 0.05,
            "wrong_representation_error": wrong_rep_error,
            "exclusion_note": "The same e3nn vector representation must be used on both paths.",
        },
        "malformed_feature_width_is_rejected": {
            "passed": malformed_rejected,
            "error": malformed_error,
        },
    }


def run_boundary_tests() -> dict[str, Any]:
    edge_index = torch.tensor([[0], [1]], dtype=torch.long)
    x = torch.tensor(
        [
            [2.0, 0.0, 1.0],
            [-1.0, 1.0, 0.0],
            [0.5, -0.5, 3.0],
        ],
        dtype=torch.float64,
    )
    representation = _rotation_representation()
    layer = SumVectorMessage()
    out = layer(x, edge_index)
    rotate_then_message = layer(_rotate_features(x, representation), edge_index)
    message_then_rotate = _rotate_features(out, representation)
    max_error = float((rotate_then_message - message_then_rotate).abs().max())

    zero_batch = torch.empty((0, IRREPS_VECTOR.dim), dtype=torch.float64)
    zero_out = layer(zero_batch, torch.empty((2, 0), dtype=torch.long))

    return {
        "isolated_node_zero_message_stays_equivariant": {
            "passed": max_error < TOLERANCE
            and torch.allclose(out[2], torch.zeros(IRREPS_VECTOR.dim, dtype=torch.float64)),
            "max_equivariance_error": max_error,
            "isolated_output": [float(value) for value in out[2]],
            "boundary_note": "Node 2 has no incoming edge and receives the additive zero vector.",
        },
        "zero_batch_preserves_vector_width": {
            "passed": tuple(zero_out.shape) == (0, IRREPS_VECTOR.dim),
            "observed_shape": list(zero_out.shape),
            "expected_shape": [0, IRREPS_VECTOR.dim],
        },
    }


def _flatten_sections(*sections: dict[str, Any]) -> list[dict[str, Any]]:
    flat = []
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "passed" in value:
                flat.append(value)
    return flat


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    flat_tests = _flatten_sections(positive, negative, boundary)
    all_pass = all(test.get("passed") for test in flat_tests)

    results = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "prior_function_receipts": PRIOR_RECEIPTS,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "operation_sequence": [
            "load and check the prior e3nn irrep tensor-product function receipt",
            "load and check the prior PyG MessagePassing autograd function receipt",
            "construct a three-node directed vector-feature graph with e3nn 1o feature width",
            "compute the e3nn SO(3) vector representation matrix from a bounded rotation",
            "run PyG additive MessagePassing before and after applying the shared irrep action",
            "compare rotate-then-message against message-then-rotate equivariance residual",
            "run adjacent negative fixtures for fixed unrotated bias, wrong output representation, and malformed feature width",
            "run boundary fixtures for isolated-node zero vector output and zero-batch vector-width preservation",
        ],
        "carrier_topology": (
            "finite directed PyG graph with three-dimensional e3nn 1o vector "
            "features on each node and a shared SO(3) irrep action; no learned "
            "GNN layer, graph/operator lego, bridge, axis, GStack, QIT, or "
            "nonclassical carrier is claimed"
        ),
        "observable": {
            "prior_receipt_gate": "parent e3nn and PyG function receipts exist, are canonical, all_pass, load-bearing, and fresh for source",
            "equivariance_residual": "max absolute difference between rotate-then-message and message-then-rotate paths",
            "biased_message_control": "fixed unrotated vector bias must break equivariance",
            "wrong_representation_control": "identity output representation must disagree with the shared e3nn vector action path",
            "malformed_width_control": "node features not matching the e3nn vector irrep width must raise",
            "boundary_controls": "isolated node receives zero vector and zero-node batch preserves vector width",
        },
        "pass_fail_predicate": (
            "Prior e3nn and PyG function receipts must be canonical, all_pass, "
            "load-bearing, and fresh. The additive PyG message pass must commute "
            "with the shared e3nn vector irrep action below tolerance, while fixed "
            "unrotated bias, wrong output representation, and malformed-width "
            "controls must fail or raise as expected. Isolated-node and zero-batch "
            "boundaries must preserve the declared vector-feature semantics."
        ),
        "graveyards": [
            "missing, stale, noncanonical, or non-load-bearing parent receipt -- must block the integration claim",
            "fixed unrotated vector bias in the message map -- must produce residual above threshold",
            "wrong output representation on the message-then-rotate path -- must produce residual above threshold",
            "malformed feature width accepted silently -- must raise instead",
            "isolated node receives nonzero vector under additive aggregation -- must fail boundary",
        ],
        "baselines": [
            "manual directed additive message-passing over a three-node cycle",
            "shared e3nn 1o vector representation applied uniformly to every node feature",
            "zero-vector additive identity for nodes with no incoming edges",
            "zero-node graph preserving the declared e3nn vector feature width",
        ],
        "alternative_formulations": [
            "manual PyTorch scatter-add over edge_index compared to e3nn rotation",
            "NetworkX predecessor aggregation on vector features with explicit rotation matrices",
            "learned e3nn/PyG convolutional equivariance tested in a later separate API-surface packet",
        ],
        "tool_function_needs": [
            "e3nn.o3.Irreps",
            "Irreps.D_from_matrix",
            "torch_geometric.nn.MessagePassing",
            "MessagePassing.propagate",
            "MessagePassing.message",
            "torch.tensor",
            "torch.empty",
            "torch.allclose",
        ],
        "lego_coupling_target": [
            "e3nn_pyg_vector_message_fixture",
            "graph_operator_equivariance_handoff_rows",
            "later graph/operator lego-fit packets with named parent receipts",
        ],
        "surviving_alternatives": [
            "Learned GNN layers, e3nn convolutions, batching, heterogeneous "
            "graphs, and graph/operator lego promotion remain separate receipts."
        ],
        "claim_ceiling": "tool_integration_micro_only",
        "next_lego_target": "minimal equivariant message-passing fixture below graph/operator lego promotion",
        "promotion_condition": (
            "requires a later admitted integration or lego row that names the "
            "exact parent receipts and passes strict runner admission; this "
            "INTEGRATION_MICRO row does not promote the lego"
        ),
        "blocked_until": (
            "blocked until a downstream queue row declares the exact graph/operator "
            "integration target, parent receipts, and active stage gate for promotion"
        ),
        "demotion_condition": (
            "Demote this e3nn-PyG surface if either prior receipt is missing, "
            "noncanonical, not all_pass, not load-bearing, or older than its "
            "source probe; if PyG additive aggregation does not commute with "
            "the e3nn vector irrep action; if biased or wrong representation "
            "paths pass; or if malformed feature widths are silently accepted."
        ),
        "out_of_scope": [
            "no learned GNN equivariance claim",
            "no e3nn convolution claim",
            "no graph/operator lego promotion",
            "no bridge, axis, or broader graph dynamics claim",
            "no proof of broad e3nn/PyG compatibility",
        ],
        "criteria_checked": [
            "prior e3nn function receipt is canonical and load-bearing",
            "prior PyG function receipt is canonical and load-bearing",
            "prior function receipts are fresh relative to their source probes",
            "PyG additive directed message passing commutes with e3nn vector irrep rotation",
            "fixed unrotated vector bias fails equivariance",
            "wrong output representation fails equivariance",
            "isolated node and zero-batch boundaries",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} passed")

    if not all_pass:
        raise SystemExit(1)
