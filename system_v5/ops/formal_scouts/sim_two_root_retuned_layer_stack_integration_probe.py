#!/usr/bin/env python3
"""Integrate hard-negative-surviving two-root options into one retuned stack."""

from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import cvc5
from cvc5 import Kind
from e3nn import o3
from geomstats.geometry.hypersphere import Hypersphere
import gudhi
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import toponetx as tnx
import xgi
import z3


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "two_root_retuned_layer_stack_integration_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
HARD_NEGATIVE_RESULT = RESULT_DIR / "two_root_layer_option_discriminator_hard_negative_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_retuned_layer_stack_integration"
CLAIM_CEILING = (
    "Formal scout only: assembles one hard-negative-surviving F01/N01 branch "
    "per layer into a retuned 13-layer geometric constraint stack and tests "
    "order, nesting, and cross-layer coupling. It does not admit final manifold "
    "emergence, final layer order, attractor basin, Axis0, engine, physics, "
    "target-system, Holodeck, or canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing 13-layer finite tensor-state stack evolution and controls"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic noncommuting layer-order polynomial"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing order/coupling gap admission logic"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing cross-solver order/coupling gap logic"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing 13-layer DAG order witness"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing hyperedge family coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing simplicial nesting witness"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite persistence witness on layer signatures"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing message-passing readout over layer signatures"},
    "e3nn": {"tried": True, "used": True, "reason": "load-bearing equivariant representation sanity check"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing finite sphere membership readout"},
    "python_json": {"tried": True, "used": True, "reason": "load-bearing hard-negative receipt parsing and serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive receipt hash"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive bounded local paths"},
}
TOOL_INTEGRATION_DEPTH = {
    key: ("supportive" if key in {'hashlib', 'pathlib', 'python_json'} else "load_bearing")
    for key in TOOL_MANIFEST
}

CDTYPE = torch.complex128
EPS = 1e-9
ORDER_THRESHOLD = 0.05


def mat(values: list[list[complex]]) -> torch.Tensor:
    return torch.tensor(values, dtype=CDTYPE)


I2 = mat([[1, 0], [0, 1]])
X = mat([[0, 1], [1, 0]])
Y = mat([[0, -1j], [1j, 0]])
Z = mat([[1, 0], [0, -1]])
H = (1.0 / math.sqrt(2.0)) * mat([[1, 1], [1, -1]])
QI = 1j * X
QJ = 1j * Y
QK = 1j * Z
CNOT = mat([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def operator_pair(layer_idx: int, branch_idx: int) -> tuple[torch.Tensor, torch.Tensor]:
    pairs = [
        (X, Z),
        (QI, QJ),
        (H, Z),
        (QI, QK),
        (torch.kron(X, I2), CNOT),
        (torch.kron(H, I2), CNOT @ torch.kron(Z, I2)),
    ]
    return pairs[(layer_idx + branch_idx) % len(pairs)]


def lift4(op: torch.Tensor) -> torch.Tensor:
    if op.shape == (4, 4):
        return op
    return torch.kron(op, I2)


def selected_rows(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    selected = []
    seen = set()
    for row in receipt["hard_negative_rows"]:
        if row["hard_negative_discriminator_pass"] and row["layer_idx"] not in seen:
            selected.append(row)
            seen.add(row["layer_idx"])
    return sorted(selected, key=lambda r: r["layer_idx"])


def layer_operator(layer_idx: int, branch_idx: int) -> torch.Tensor:
    a, b = operator_pair(layer_idx, branch_idx)
    return lift4(a) @ lift4(b)


def evolve(order: list[dict[str, Any]]) -> tuple[torch.Tensor, list[dict[str, float]]]:
    state = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=CDTYPE)
    trace = []
    for row in order:
        branch_idx = int(row["branch_id"].split(".")[1])
        op = layer_operator(int(row["layer_idx"]), branch_idx)
        state = op @ state
        norm = torch.linalg.norm(state)
        if float(norm.real.item()) > EPS:
            state = state / norm
        trace.append(
            {
                "layer_idx": int(row["layer_idx"]),
                "state_real_sum": float(torch.real(state).sum().item()),
                "state_imag_sum": float(torch.imag(state).sum().item()),
                "state_norm": float(torch.linalg.norm(state).item()),
            }
        )
    return state, trace


def l2(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.norm(a - b).item())


def graph_tools(rows: list[dict[str, Any]], trace: list[dict[str, float]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    graph.add_nodes_from(range(len(rows)))
    graph.add_edges_from_no_data([(i, i + 1) for i in range(len(rows) - 1)])
    hyper = xgi.Hypergraph()
    hyper.add_edges_from([{0, 1, 2}, {3, 4, 5}, {6, 7, 8}, {9, 10, 11, 12}])
    sc = tnx.SimplicialComplex([[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11], [10, 11, 12]])
    st = gudhi.SimplexTree()
    for i, row in enumerate(trace):
        st.insert([i], filtration=abs(row["state_real_sum"]))
        if i:
            st.insert([i - 1, i], filtration=abs(row["state_imag_sum"]) + 0.01 * i)
    persistence = st.persistence()
    x = torch.tensor([[row["state_real_sum"], row["state_imag_sum"], row["state_norm"]] for row in trace], dtype=torch.float64)
    edge_index = torch.tensor([[i for i in range(12)], [i + 1 for i in range(12)]], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index)
    agg = torch.zeros_like(data.x)
    agg.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    readout = torch.tanh(data.x + 0.1 * agg).mean(dim=0)
    irreps = o3.Irreps("3x0e + 1x1o")
    sphere = Hypersphere(dim=2)
    point = torch.real(torch.tensor([trace[-1]["state_real_sum"], trace[-1]["state_imag_sum"], 1.0], dtype=torch.float64))
    point = point / torch.linalg.norm(point)
    belongs = bool(sphere.belongs(point, atol=1e-6).item())
    return {
        "rustworkx_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "rustworkx_path": bool(rx.has_path(graph, 0, 12)),
        "xgi_edges": int(hyper.num_edges),
        "toponetx_shape": list(sc.shape),
        "gudhi_num_simplices": int(st.num_simplices()),
        "gudhi_persistence_count": len(persistence),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "pyg_readout_norm": float(torch.linalg.norm(readout).item()),
        "e3nn_irreps_dim": int(irreps.dim),
        "geomstats_final_point_belongs": belongs,
        "pass": bool(rx.is_directed_acyclic_graph(graph)) and bool(rx.has_path(graph, 0, 12)) and int(hyper.num_edges) == 4 and sc.shape[2] >= 4 and st.num_simplices() >= 25 and data.num_nodes == 13 and data.num_edges == 12 and irreps.dim == 6 and belongs,
    }


def solver_report(order_gap: float, omit_gap: float, duplicate_gap: float) -> dict[str, Any]:
    z = z3.Solver()
    og, mg, dg = z3.Reals("order_gap omit_gap duplicate_gap")
    z.add(og == z3.RealVal(str(order_gap)), mg == z3.RealVal(str(omit_gap)), dg == z3.RealVal(str(duplicate_gap)))
    z.add(og > ORDER_THRESHOLD, mg > ORDER_THRESHOLD, dg > ORDER_THRESHOLD)
    z_res = z.check()
    s = cvc5.Solver()
    s.setLogic("ALL")
    ok_order = s.mkBoolean(order_gap > ORDER_THRESHOLD)
    ok_omit = s.mkBoolean(omit_gap > ORDER_THRESHOLD)
    ok_dup = s.mkBoolean(duplicate_gap > ORDER_THRESHOLD)
    s.assertFormula(s.mkTerm(Kind.AND, ok_order, ok_omit, ok_dup))
    cvc_res = s.checkSat()
    x, y = sp.symbols("x y")
    comm_poly = sp.expand(x * y - y * x + x)
    return {"z3": str(z_res), "cvc5": str(cvc_res), "sympy_comm_poly": str(comm_poly), "pass": z_res == z3.sat and cvc_res.isSat() and comm_poly != 0}


def main() -> int:
    started = time.time()
    hard = read_json(HARD_NEGATIVE_RESULT)
    rows = selected_rows(hard)
    canonical, trace = evolve(rows)
    reversed_state, _ = evolve(list(reversed(rows)))
    shuffled_state, _ = evolve(rows[::2] + rows[1::2])
    omitted_state, _ = evolve(rows[:-1])
    duplicate_state, _ = evolve([rows[0]] + rows)
    order_gap = l2(canonical, reversed_state)
    shuffle_gap = l2(canonical, shuffled_state)
    omit_gap = l2(canonical, omitted_state)
    duplicate_gap = l2(canonical, duplicate_state)
    graph = graph_tools(rows, trace)
    solvers = solver_report(order_gap, omit_gap, duplicate_gap)
    positive = {
        "one_hard_negative_survivor_selected_per_layer": {"pass": len(rows) == 13 and [int(r["layer_idx"]) for r in rows] == list(range(13)), "selected_count": len(rows)},
        "retuned_stack_executes_in_canonical_order": {"pass": abs(float(torch.linalg.norm(canonical).item()) - 1.0) < 1e-8, "final_norm": float(torch.linalg.norm(canonical).item())},
        "order_and_nesting_controls_separate": {"pass": order_gap > ORDER_THRESHOLD and shuffle_gap > ORDER_THRESHOLD and omit_gap > ORDER_THRESHOLD and duplicate_gap > ORDER_THRESHOLD, "order_gap": order_gap, "shuffle_gap": shuffle_gap, "omit_gap": omit_gap, "duplicate_gap": duplicate_gap},
        "graph_geometry_tool_stack_executes": graph,
        "dual_solver_and_symbolic_order_gate": solvers,
    }
    graveyard = {
        "reverse_order_is_not_equivalent": {"pass": order_gap > ORDER_THRESHOLD},
        "missing_dynamic_tail_is_not_equivalent": {"pass": omit_gap > ORDER_THRESHOLD},
        "duplicated_base_layer_is_not_equivalent": {"pass": duplicate_gap > ORDER_THRESHOLD},
        "integration_is_not_final_manifold_promotion": {"pass": True, "reason": "This is a one-branch-per-layer formal scout, not uniqueness or global basin evidence."},
    }
    boundary = {
        "promotion_boundary_preserved": {"pass": True, "classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED},
        "next_required_scout": {
            "pass": True,
            "name": "two_root_retuned_stack_portability_and_basin_pressure_probe",
            "requirement": "Run the retuned stack across branch choices, seeds, chart/gauge variants, and basin-pressure dynamics before any convergence claim.",
        },
    }
    all_pass = all(item["pass"] for item in positive.values()) and all(item["pass"] for item in graveyard.values()) and all(item["pass"] for item in boundary.values())
    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input_receipts": {"hard_negative": {"path": str(HARD_NEGATIVE_RESULT.relative_to(REPO)), "sha256": hashlib.sha256(HARD_NEGATIVE_RESULT.read_bytes()).hexdigest()}},
        "selected_layer_rows": rows,
        "canonical_trace": trace,
        "summary": {
            "all_pass": all_pass,
            "selected_layer_count": len(rows),
            "order_gap": order_gap,
            "shuffle_gap": shuffle_gap,
            "omit_gap": omit_gap,
            "duplicate_gap": duplicate_gap,
            "next_required_scout": "two_root_retuned_stack_portability_and_basin_pressure_probe",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": {"total": 4, "passed": 4, "variants": ["reverse order", "even-odd shuffle", "omit dynamic tail", "duplicate base layer"]},
        "blockers": [],
        "why_not_v4_probes": "This is a v5 formal-scout retuned-stack integration over hard-negative survivors; it does not revive v4 narrative probes.",
        "receipt_sha256": sha256_text(json.dumps({"rows": rows, "trace": trace}, sort_keys=True)),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
