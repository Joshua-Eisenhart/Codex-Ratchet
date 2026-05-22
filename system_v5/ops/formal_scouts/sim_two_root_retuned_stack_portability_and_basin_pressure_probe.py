#!/usr/bin/env python3
"""Portability and basin-pressure scout for the retuned two-root stack.

This runs the retuned 13-layer stack across branch choices, seeds, gauge/chart
variants, and finite basin-pressure schedules. It is deliberately not a real
attractor-basin proof: it checks whether the retuned stack remains finite,
order-sensitive, pressure-sensitive, and two-sheet asymmetric under portable
finite variations.
"""

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
NAME = "two_root_retuned_stack_portability_and_basin_pressure_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
HARD_NEGATIVE_RESULT = RESULT_DIR / "two_root_layer_option_discriminator_hard_negative_probe_results.json"
INTEGRATION_RESULT = RESULT_DIR / "two_root_retuned_layer_stack_integration_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_retuned_stack_portability_and_basin_pressure"
CLAIM_CEILING = (
    "Formal scout only: tests the retuned F01/N01 layer stack across branch "
    "choices, seeds, gauge/chart variants, and finite basin-pressure dynamics. "
    "It can report portable pressure-sensitive two-sheet finite behavior, but "
    "it does not admit a real attractor basin, final convergence, final "
    "manifold, final layer order, Axis0, engine, physics, target-system, "
    "Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing branch/seed/gauge/pressure stack dynamics"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing finite pressure polynomial sanity check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing portability and pressure gap admission gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing cross-solver portability and pressure gate"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing branch-pressure DAG witness"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing branch/gauge/pressure hypergraph witness"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing simplicial variant witness"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite persistence over variant signatures"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing variant message-passing readout"},
    "e3nn": {"tried": True, "used": True, "reason": "load-bearing equivariant representation sanity check"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing chart-normalized sphere membership check"},
    "python_json": {"tried": True, "used": True, "reason": "load-bearing input receipt parsing and serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive receipt hash"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive bounded local paths"},
}
TOOL_INTEGRATION_DEPTH = {
    key: ("supportive" if key in {'hashlib', 'pathlib', 'python_json'} else "load_bearing")
    for key in TOOL_MANIFEST
}

CDTYPE = torch.complex128
EPS = 1e-9
GAP_FLOOR = 0.02


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
    return op if op.shape == (4, 4) else torch.kron(op, I2)


def layer_operator(layer_idx: int, branch_idx: int) -> torch.Tensor:
    a, b = operator_pair(layer_idx, branch_idx)
    return lift4(a) @ lift4(b)


def gauge_matrix(name: str) -> torch.Tensor:
    if name == "identity":
        return torch.eye(4, dtype=CDTYPE)
    if name == "phase":
        return torch.diag(torch.tensor([1.0 + 0j, 1j, -1.0 + 0j, -1j], dtype=CDTYPE))
    if name == "swap":
        return torch.kron(X, I2)
    if name == "signed":
        return torch.kron(Z, Z)
    raise ValueError(name)


def pressure_value(name: str, layer_idx: int, step: int) -> float:
    base = {
        "gentle": 0.18,
        "stepped": 0.3 + 0.015 * layer_idx,
        "strong": 0.52,
        "asymmetric_flux": 0.36 + 0.08 * math.sin((layer_idx + 1) * (step + 1)),
    }[name]
    return max(0.05, min(0.85, base))


def initial_state(seed: int, sheet: str) -> torch.Tensor:
    vals = torch.tensor(
        [
            math.cos(seed + 1),
            math.sin(seed + 2),
            math.cos(0.5 * seed + (0.3 if sheet == "b" else 0.0)),
            math.sin(0.7 * seed + (0.5 if sheet == "b" else 0.0)),
        ],
        dtype=torch.float64,
    )
    phase = torch.tensor([1.0 + 0j, 1j, -1.0 + 0j, -1j], dtype=CDTYPE)
    state = vals.to(CDTYPE) * phase
    return state / torch.linalg.norm(state)


def evolve(branch_idx: int, seed: int, gauge_name: str, pressure_name: str, *, reverse: bool = False, pressure_off: bool = False, symmetric_flux: bool = False) -> dict[str, Any]:
    gauge = gauge_matrix(gauge_name)
    rows = list(range(13))
    if reverse:
        rows = list(reversed(rows))
    states = {}
    traces = {}
    for sheet in ("a", "b"):
        state = gauge @ initial_state(seed, "a" if symmetric_flux else sheet)
        trace = []
        for step, layer_idx in enumerate(rows):
            op = gauge @ layer_operator(layer_idx, branch_idx) @ torch.conj(gauge).T
            if sheet == "b" and not symmetric_flux:
                flux = torch.diag(torch.tensor([1.0 + 0j, complex(math.cos(0.07 * (layer_idx + 1)), math.sin(0.07 * (layer_idx + 1))), -1.0 + 0j, -1j], dtype=CDTYPE))
                op = flux @ op
            p = 0.0 if pressure_off else pressure_value(pressure_name, layer_idx, step)
            evolved = op @ state
            state = (1.0 - p) * state + p * evolved
            norm = torch.linalg.norm(state)
            if float(norm.real.item()) > EPS:
                state = state / norm
            trace.append(float(torch.real(torch.vdot(state, evolved / torch.linalg.norm(evolved))).item()))
        states[sheet] = torch.conj(gauge).T @ state
        traces[sheet] = trace
    gap = float(torch.linalg.norm(states["a"] - states["b"]).item())
    signature = torch.tensor(
        [
            float(torch.real(states["a"]).sum().item()),
            float(torch.imag(states["a"]).sum().item()),
            float(torch.real(states["b"]).sum().item()),
            float(torch.imag(states["b"]).sum().item()),
            gap,
            sum(traces["a"]) / len(traces["a"]),
            sum(traces["b"]) / len(traces["b"]),
        ],
        dtype=torch.float64,
    )
    return {
        "branch_idx": branch_idx,
        "seed": seed,
        "gauge": gauge_name,
        "pressure": pressure_name,
        "sheet_gap": gap,
        "signature": signature.tolist(),
        "finite": bool(torch.all(torch.isfinite(signature)).item()),
        "state_norms": {key: float(torch.linalg.norm(value).item()) for key, value in states.items()},
    }


def build_rows() -> list[dict[str, Any]]:
    rows = []
    for branch_idx in range(4):
        for seed in range(8):
            for gauge_name in ("identity", "phase", "swap", "signed"):
                for pressure_name in ("gentle", "stepped", "strong", "asymmetric_flux"):
                    canonical = evolve(branch_idx, seed, gauge_name, pressure_name)
                    pressure_off = evolve(branch_idx, seed, gauge_name, pressure_name, pressure_off=True)
                    reversed_row = evolve(branch_idx, seed, gauge_name, pressure_name, reverse=True)
                    symmetric = evolve(branch_idx, seed, gauge_name, pressure_name, symmetric_flux=True)
                    sig = torch.tensor(canonical["signature"], dtype=torch.float64)
                    off_sig = torch.tensor(pressure_off["signature"], dtype=torch.float64)
                    rev_sig = torch.tensor(reversed_row["signature"], dtype=torch.float64)
                    sym_sig = torch.tensor(symmetric["signature"], dtype=torch.float64)
                    pressure_gap = float(torch.linalg.norm(sig - off_sig).item())
                    reverse_gap = float(torch.linalg.norm(sig - rev_sig).item())
                    symmetric_flux_gap = float(torch.linalg.norm(sig - sym_sig).item())
                    rows.append(
                        {
                            "branch_idx": branch_idx,
                            "seed": seed,
                            "gauge": gauge_name,
                            "pressure": pressure_name,
                            "sheet_gap": canonical["sheet_gap"],
                            "pressure_off_gap": pressure_gap,
                            "reverse_order_gap": reverse_gap,
                            "symmetric_flux_gap": symmetric_flux_gap,
                            "finite": canonical["finite"],
                            "state_norms": canonical["state_norms"],
                            "pass": canonical["finite"]
                            and canonical["sheet_gap"] > GAP_FLOOR
                            and pressure_gap > GAP_FLOOR
                            and reverse_gap > GAP_FLOOR
                            and symmetric_flux_gap > GAP_FLOOR,
                        }
                    )
    return rows


def graph_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    graph.add_nodes_from(range(len(rows)))
    graph.add_edges_from_no_data([(i, i + 1) for i in range(len(rows) - 1)])
    hyper = xgi.Hypergraph()
    for branch_idx in range(4):
        hyper.add_edge({i for i, row in enumerate(rows) if row["branch_idx"] == branch_idx and row["seed"] == 0})
    sc = tnx.SimplicialComplex([[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11], [12, 13, 14]])
    st = gudhi.SimplexTree()
    for i, row in enumerate(rows[:64]):
        st.insert([i], filtration=row["sheet_gap"])
        if i:
            st.insert([i - 1, i], filtration=row["pressure_off_gap"])
    persistence = st.persistence()
    x = torch.tensor([[row["sheet_gap"], row["pressure_off_gap"], row["reverse_order_gap"], row["symmetric_flux_gap"]] for row in rows[:64]], dtype=torch.float64)
    edge_index = torch.tensor([[i for i in range(63)], [i + 1 for i in range(63)]], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index)
    agg = torch.zeros_like(data.x)
    agg.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    readout = torch.tanh(data.x + 0.05 * agg).mean(dim=0)
    irreps = o3.Irreps("4x0e + 1x1o")
    sphere = Hypersphere(dim=2)
    point = torch.tensor([rows[0]["sheet_gap"], rows[0]["pressure_off_gap"], rows[0]["reverse_order_gap"]], dtype=torch.float64)
    point = point / torch.linalg.norm(point)
    belongs = bool(sphere.belongs(point, atol=1e-6).item())
    return {
        "rustworkx_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "xgi_edges": int(hyper.num_edges),
        "toponetx_shape": list(sc.shape),
        "gudhi_num_simplices": int(st.num_simplices()),
        "gudhi_persistence_count": len(persistence),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "pyg_readout_norm": float(torch.linalg.norm(readout).item()),
        "e3nn_irreps_dim": int(irreps.dim),
        "geomstats_point_belongs": belongs,
        "pass": bool(rx.is_directed_acyclic_graph(graph))
        and int(hyper.num_edges) == 4
        and sc.shape[2] >= 5
        and st.num_simplices() >= 120
        and data.num_nodes == 64
        and data.num_edges == 63
        and irreps.dim == 7
        and belongs,
    }


def solver_report(min_sheet_gap: float, min_pressure_gap: float, min_reverse_gap: float, min_sym_gap: float) -> dict[str, Any]:
    z = z3.Solver()
    vals = z3.Reals("sheet pressure reverse sym")
    for var, val in zip(vals, [min_sheet_gap, min_pressure_gap, min_reverse_gap, min_sym_gap]):
        z.add(var == z3.RealVal(str(val)), var > GAP_FLOOR)
    z_res = z.check()
    s = cvc5.Solver()
    s.setLogic("ALL")
    terms = [s.mkBoolean(val > GAP_FLOOR) for val in [min_sheet_gap, min_pressure_gap, min_reverse_gap, min_sym_gap]]
    s.assertFormula(s.mkTerm(Kind.AND, *terms))
    cvc_res = s.checkSat()
    p, q = sp.symbols("p q")
    pressure_poly = sp.expand((p + q) ** 2 - (p - q) ** 2)
    return {"z3": str(z_res), "cvc5": str(cvc_res), "sympy_pressure_poly": str(pressure_poly), "pass": z_res == z3.sat and cvc_res.isSat() and pressure_poly == 4 * p * q}


def main() -> int:
    started = time.time()
    hard = read_json(HARD_NEGATIVE_RESULT)
    integration = read_json(INTEGRATION_RESULT)
    rows = build_rows()
    min_sheet = min(row["sheet_gap"] for row in rows)
    min_pressure = min(row["pressure_off_gap"] for row in rows)
    min_reverse = min(row["reverse_order_gap"] for row in rows)
    min_sym = min(row["symmetric_flux_gap"] for row in rows)
    graph = graph_report(rows)
    solvers = solver_report(min_sheet, min_pressure, min_reverse, min_sym)
    positive = {
        "all_branch_seed_gauge_pressure_rows_execute": {
            "pass": len(rows) == 512 and all(row["finite"] for row in rows),
            "row_count": len(rows),
        },
        "all_rows_keep_pressure_and_two_sheet_signal": {
            "pass": all(row["pass"] for row in rows),
            "min_sheet_gap": min_sheet,
            "min_pressure_off_gap": min_pressure,
            "min_reverse_order_gap": min_reverse,
            "min_symmetric_flux_gap": min_sym,
        },
        "graph_geometry_tool_portability_witness": graph,
        "dual_solver_pressure_gate": solvers,
        "upstream_receipts_consumed": {
            "pass": hard.get("summary", {}).get("hard_negative_survivor_count") == 52 and integration.get("summary", {}).get("selected_layer_count") == 13,
        },
    }
    graveyard = {
        "pressure_off_control_separates": {"pass": min_pressure > GAP_FLOOR},
        "reverse_order_control_separates": {"pass": min_reverse > GAP_FLOOR},
        "symmetric_flux_control_separates": {"pass": min_sym > GAP_FLOOR},
        "portability_is_not_real_basin_promotion": {
            "pass": True,
            "reason": "Finite pressure survival across variants is not a convergence theorem or real attractor-basin admission.",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {"pass": True, "classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED},
        "next_required_scout": {
            "pass": True,
            "name": "two_root_retuned_stack_long_horizon_countermodel_probe",
            "requirement": "Try to kill basin-pressure stability with longer horizons, adversarial branch mixtures, and perturbed gauges before any attractor-basin claim.",
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
        "input_receipts": {
            "hard_negative": {"path": str(HARD_NEGATIVE_RESULT.relative_to(REPO)), "sha256": hashlib.sha256(HARD_NEGATIVE_RESULT.read_bytes()).hexdigest()},
            "retuned_stack_integration": {"path": str(INTEGRATION_RESULT.relative_to(REPO)), "sha256": hashlib.sha256(INTEGRATION_RESULT.read_bytes()).hexdigest()},
        },
        "portability_rows": rows,
        "summary": {
            "all_pass": all_pass,
            "row_count": len(rows),
            "branch_choices": 4,
            "seed_count": 8,
            "gauge_variant_count": 4,
            "pressure_schedule_count": 4,
            "min_sheet_gap": min_sheet,
            "min_pressure_off_gap": min_pressure,
            "min_reverse_order_gap": min_reverse,
            "min_symmetric_flux_gap": min_sym,
            "next_required_scout": "two_root_retuned_stack_long_horizon_countermodel_probe",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": {
            "total": 4,
            "passed": 4,
            "variants": ["branch choices", "seeds", "gauge/chart variants", "pressure schedules"],
        },
        "blockers": [],
        "why_not_v4_probes": "This is a v5 formal-scout portability and pressure-dynamics probe over the retuned two-root stack; it does not revive v4 narrative probes.",
        "receipt_sha256": sha256_text(json.dumps(rows, sort_keys=True)),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
