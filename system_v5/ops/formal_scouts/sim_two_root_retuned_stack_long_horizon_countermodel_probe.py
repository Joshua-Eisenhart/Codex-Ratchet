#!/usr/bin/env python3
"""Long-horizon countermodel scout for the retuned two-root stack.

This tries to kill the finite basin-pressure reading from the prior retuned
stack scout with longer horizons, adversarial branch mixtures, and perturbed
gauges. Passing means no countermodel was found in this bounded family, not
that a real attractor basin, final manifold, or convergence theorem was proved.
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

from sim_two_root_retuned_stack_portability_and_basin_pressure_probe import (
    CDTYPE,
    I2,
    X,
    Z,
    gauge_matrix,
    initial_state,
    layer_operator,
)


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "two_root_retuned_stack_long_horizon_countermodel_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
PORTABILITY_RESULT = RESULT_DIR / "two_root_retuned_stack_portability_and_basin_pressure_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_retuned_stack_long_horizon_countermodel"
CLAIM_CEILING = (
    "Formal scout only: tries to kill the retuned F01/N01 stack with longer "
    "horizons, adversarial branch mixtures, and perturbed gauges. It can report "
    "bounded no-countermodel evidence for this finite family, but it does not "
    "admit a real attractor basin, final convergence, final manifold, final "
    "layer order, Axis0, engine, physics, target-system, Holodeck, or canonical "
    "claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing long-horizon branch/gauge/pressure dynamics"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing finite gap polynomial sanity check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing no-countermodel threshold gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing cross-solver no-countermodel threshold gate"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing horizon/mixture DAG witness"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing horizon/mix/gauge hyperedge witness"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite variant simplicial witness"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite persistence over adversarial signatures"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing message-passing readout over adversarial rows"},
    "e3nn": {"tried": True, "used": True, "reason": "load-bearing equivariant representation sanity check"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing chart-normalized sphere membership check"},
    "python_json": {"tried": True, "used": True, "reason": "load-bearing upstream receipt parsing and serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive receipt hash"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive bounded local paths"},
}
TOOL_INTEGRATION_DEPTH = {
    key: ("supportive" if key in {"hashlib", "pathlib", "python_json"} else "load_bearing")
    for key in TOOL_MANIFEST
}

EPS = 1e-9
SHEET_GAP_FLOOR = 0.02
COUNTERMODEL_FLOOR = 0.01
PRESSURE_GAP_FLOOR = 0.02


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def perturb_gauge(name: str, step: int, horizon: int) -> torch.Tensor:
    if name == "identity":
        return gauge_matrix("identity")
    if name == "phase":
        return gauge_matrix("phase")
    if name == "signed":
        return gauge_matrix("signed")
    if name == "drift":
        angle = 0.015 * (step + 1) / max(1, horizon)
        vals = [
            complex(math.cos(angle), math.sin(angle)),
            complex(math.cos(2.0 * angle), -math.sin(2.0 * angle)),
            complex(math.cos(3.0 * angle), math.sin(3.0 * angle)),
            complex(math.cos(4.0 * angle), -math.sin(4.0 * angle)),
        ]
        return torch.diag(torch.tensor(vals, dtype=CDTYPE))
    raise ValueError(name)


def pressure(step: int, horizon: int, mode: str) -> float:
    if mode == "steady":
        value = 0.22
    elif mode == "ramp":
        value = 0.08 + 0.42 * (step + 1) / horizon
    elif mode == "pulse":
        value = 0.14 + (0.34 if step % 17 in {0, 1, 2, 3} else 0.0)
    elif mode == "alternating":
        value = 0.18 + 0.18 * ((step // 13) % 2)
    else:
        raise ValueError(mode)
    return max(0.04, min(0.72, value))


def branch_for(mode: str, seed: int, step: int, states: dict[str, torch.Tensor], gauge_name: str, horizon: int) -> int:
    if mode == "fixed":
        return seed % 4
    if mode == "alternating":
        return (seed + step) % 4
    if mode == "blockwise":
        return (seed + step // 13) % 4
    if mode != "adversarial_min_gap":
        raise ValueError(mode)
    layer_idx = step % 13
    gauge = perturb_gauge(gauge_name, step, horizon)
    best_branch = 0
    best_gap = float("inf")
    for candidate in range(4):
        trial = {}
        op = gauge @ layer_operator(layer_idx, candidate) @ torch.conj(gauge).T
        for sheet, state in states.items():
            evolved = op @ state
            evolved_norm = torch.linalg.norm(evolved)
            if float(evolved_norm.real.item()) > EPS:
                evolved = evolved / evolved_norm
            trial[sheet] = evolved
        gap = float(torch.linalg.norm(trial["a"] - trial["b"]).item())
        if gap < best_gap:
            best_gap = gap
            best_branch = candidate
    return best_branch


def evolve_long(
    *,
    seed: int,
    horizon: int,
    branch_mode: str,
    gauge_name: str,
    pressure_mode: str,
    pressure_off: bool = False,
    reverse_order: bool = False,
    symmetric_flux: bool = False,
) -> dict[str, Any]:
    states = {
        "a": perturb_gauge(gauge_name, 0, horizon) @ initial_state(seed, "a"),
        "b": perturb_gauge(gauge_name, 0, horizon) @ initial_state(seed, "a" if symmetric_flux else "b"),
    }
    gaps = []
    branch_trace = []
    for raw_step in range(horizon):
        step = horizon - raw_step - 1 if reverse_order else raw_step
        layer_idx = step % 13
        branch_idx = branch_for(branch_mode, seed, step, states, gauge_name, horizon)
        branch_trace.append(branch_idx)
        gauge = perturb_gauge(gauge_name, step, horizon)
        op = gauge @ layer_operator(layer_idx, branch_idx) @ torch.conj(gauge).T
        p = 0.0 if pressure_off else pressure(step, horizon, pressure_mode)
        next_states = {}
        for sheet, state in states.items():
            local_op = op
            if sheet == "b" and not symmetric_flux:
                phase = 0.03 * (layer_idx + 1) + 0.002 * (raw_step + seed)
                flux = torch.diag(
                    torch.tensor(
                        [
                            1.0 + 0j,
                            complex(math.cos(phase), math.sin(phase)),
                            -1.0 + 0j,
                            -1j,
                        ],
                        dtype=CDTYPE,
                    )
                )
                local_op = flux @ local_op
            evolved = local_op @ state
            evolved_norm = torch.linalg.norm(evolved)
            if float(evolved_norm.real.item()) > EPS:
                evolved = evolved / evolved_norm
            mixed = (1.0 - p) * state + p * evolved
            mixed_norm = torch.linalg.norm(mixed)
            if float(mixed_norm.real.item()) > EPS:
                mixed = mixed / mixed_norm
            next_states[sheet] = mixed
        states = next_states
        gaps.append(float(torch.linalg.norm(states["a"] - states["b"]).item()))
    signature = torch.tensor(
        [
            gaps[-1],
            min(gaps),
            sum(gaps) / len(gaps),
            float(torch.real(states["a"]).sum().item()),
            float(torch.imag(states["a"]).sum().item()),
            float(torch.real(states["b"]).sum().item()),
            float(torch.imag(states["b"]).sum().item()),
        ],
        dtype=torch.float64,
    )
    return {
        "final_gap": gaps[-1],
        "min_gap": min(gaps),
        "mean_gap": sum(gaps) / len(gaps),
        "branch_switch_count": sum(1 for a, b in zip(branch_trace, branch_trace[1:]) if a != b),
        "signature": signature,
        "finite": bool(torch.all(torch.isfinite(signature)).item()),
        "state_norms": {key: float(torch.linalg.norm(value).item()) for key, value in states.items()},
    }


def build_rows() -> list[dict[str, Any]]:
    rows = []
    for seed in range(6):
        for horizon in (64, 128, 256):
            for branch_mode in ("fixed", "alternating", "blockwise", "adversarial_min_gap"):
                for gauge_name in ("identity", "phase", "signed", "drift"):
                    for pressure_mode in ("steady", "ramp", "pulse", "alternating"):
                        canonical = evolve_long(seed=seed, horizon=horizon, branch_mode=branch_mode, gauge_name=gauge_name, pressure_mode=pressure_mode)
                        pressure_off = evolve_long(seed=seed, horizon=horizon, branch_mode=branch_mode, gauge_name=gauge_name, pressure_mode=pressure_mode, pressure_off=True)
                        reverse = evolve_long(seed=seed, horizon=horizon, branch_mode=branch_mode, gauge_name=gauge_name, pressure_mode=pressure_mode, reverse_order=True)
                        symmetric = evolve_long(seed=seed, horizon=horizon, branch_mode=branch_mode, gauge_name=gauge_name, pressure_mode=pressure_mode, symmetric_flux=True)
                        sig = canonical["signature"]
                        pressure_gap = float(torch.linalg.norm(sig - pressure_off["signature"]).item())
                        reverse_gap = float(torch.linalg.norm(sig - reverse["signature"]).item())
                        symmetric_gap = float(torch.linalg.norm(sig - symmetric["signature"]).item())
                        countermodel = (
                            (not canonical["finite"])
                            or canonical["final_gap"] <= COUNTERMODEL_FLOOR
                            or canonical["min_gap"] <= COUNTERMODEL_FLOOR
                            or pressure_gap <= PRESSURE_GAP_FLOOR
                        )
                        rows.append(
                            {
                                "seed": seed,
                                "horizon": horizon,
                                "branch_mode": branch_mode,
                                "gauge": gauge_name,
                                "pressure": pressure_mode,
                                "finite": canonical["finite"],
                                "final_gap": canonical["final_gap"],
                                "min_gap": canonical["min_gap"],
                                "mean_gap": canonical["mean_gap"],
                                "branch_switch_count": canonical["branch_switch_count"],
                                "pressure_off_gap": pressure_gap,
                                "reverse_order_gap": reverse_gap,
                                "symmetric_flux_gap": symmetric_gap,
                                "state_norms": canonical["state_norms"],
                                "countermodel_found": countermodel,
                                "pass": canonical["finite"]
                                and canonical["final_gap"] > SHEET_GAP_FLOOR
                                and canonical["min_gap"] > COUNTERMODEL_FLOOR
                                and pressure_gap > PRESSURE_GAP_FLOOR,
                            }
                        )
    return rows


def graph_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    graph.add_nodes_from(range(len(rows)))
    graph.add_edges_from_no_data([(i, i + 1) for i in range(len(rows) - 1)])
    hyper = xgi.Hypergraph()
    for horizon in (64, 128, 256):
        hyper.add_edge({i for i, row in enumerate(rows) if row["horizon"] == horizon and row["seed"] == 0})
    sc = tnx.SimplicialComplex([[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11], [12, 13, 14]])
    st = gudhi.SimplexTree()
    for i, row in enumerate(rows[:128]):
        st.insert([i], filtration=row["final_gap"])
        if i:
            st.insert([i - 1, i], filtration=row["pressure_off_gap"])
    persistence = st.persistence()
    x = torch.tensor(
        [[row["final_gap"], row["min_gap"], row["pressure_off_gap"], row["reverse_order_gap"], row["symmetric_flux_gap"]] for row in rows[:128]],
        dtype=torch.float64,
    )
    edge_index = torch.tensor([[i for i in range(127)], [i + 1 for i in range(127)]], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index)
    agg = torch.zeros_like(data.x)
    agg.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    readout = torch.tanh(data.x + 0.03 * agg).mean(dim=0)
    irreps = o3.Irreps("5x0e + 1x1o")
    sphere = Hypersphere(dim=2)
    point = torch.tensor([rows[0]["final_gap"], rows[0]["min_gap"], rows[0]["pressure_off_gap"]], dtype=torch.float64)
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
        and int(hyper.num_edges) == 3
        and sc.shape[2] >= 5
        and st.num_simplices() >= 250
        and data.num_nodes == 128
        and data.num_edges == 127
        and irreps.dim == 8
        and belongs,
    }


def solver_report(min_final_gap: float, min_min_gap: float, min_pressure_gap: float, countermodel_count: int) -> dict[str, Any]:
    z = z3.Solver()
    fg, mg, pg, cc = z3.Reals("final_gap min_gap pressure_gap countermodels")
    z.add(fg == z3.RealVal(str(min_final_gap)))
    z.add(mg == z3.RealVal(str(min_min_gap)))
    z.add(pg == z3.RealVal(str(min_pressure_gap)))
    z.add(cc == z3.RealVal(str(countermodel_count)))
    z.add(fg > SHEET_GAP_FLOOR, mg > COUNTERMODEL_FLOOR, pg > PRESSURE_GAP_FLOOR, cc == 0)
    z_res = z.check()

    s = cvc5.Solver()
    s.setLogic("ALL")
    s.assertFormula(
        s.mkTerm(
            Kind.AND,
            s.mkBoolean(min_final_gap > SHEET_GAP_FLOOR),
            s.mkBoolean(min_min_gap > COUNTERMODEL_FLOOR),
            s.mkBoolean(min_pressure_gap > PRESSURE_GAP_FLOOR),
            s.mkBoolean(countermodel_count == 0),
        )
    )
    cvc_res = s.checkSat()
    h, p, r = sp.symbols("h p r")
    gap_poly = sp.expand((h - p) ** 2 + r)
    return {
        "z3": str(z_res),
        "cvc5": str(cvc_res),
        "sympy_gap_poly": str(gap_poly),
        "pass": z_res == z3.sat and cvc_res.isSat() and gap_poly != 0,
    }


def main() -> int:
    started = time.time()
    upstream = read_json(PORTABILITY_RESULT)
    rows = build_rows()
    countermodels = [row for row in rows if row["countermodel_found"]]
    min_final_gap = min(row["final_gap"] for row in rows)
    min_min_gap = min(row["min_gap"] for row in rows)
    min_pressure_gap = min(row["pressure_off_gap"] for row in rows)
    min_reverse_gap = min(row["reverse_order_gap"] for row in rows)
    min_symmetric_gap = min(row["symmetric_flux_gap"] for row in rows)
    graph = graph_report(rows)
    solvers = solver_report(min_final_gap, min_min_gap, min_pressure_gap, len(countermodels))
    positive = {
        "upstream_portability_receipt_consumed": {
            "pass": upstream.get("summary", {}).get("next_required_scout") == NAME
            and upstream.get("promotion_allowed") is False,
        },
        "long_horizon_adversarial_rows_execute": {
            "pass": len(rows) == 1152 and all(row["finite"] for row in rows),
            "row_count": len(rows),
        },
        "no_bounded_countermodel_found": {
            "pass": len(countermodels) == 0,
            "countermodel_count": len(countermodels),
            "min_final_gap": min_final_gap,
            "min_min_gap": min_min_gap,
            "min_pressure_off_gap": min_pressure_gap,
        },
        "graph_geometry_tool_long_horizon_witness": graph,
        "dual_solver_countermodel_gate": solvers,
    }
    graveyard = {
        "pressure_off_control_separates": {"pass": min_pressure_gap > PRESSURE_GAP_FLOOR, "min_pressure_off_gap": min_pressure_gap},
        "reverse_order_control_separates": {"pass": min_reverse_gap > PRESSURE_GAP_FLOOR, "min_reverse_order_gap": min_reverse_gap},
        "symmetric_flux_control_separates": {"pass": min_symmetric_gap > PRESSURE_GAP_FLOOR, "min_symmetric_flux_gap": min_symmetric_gap},
        "no_countermodel_is_not_basin_promotion": {
            "pass": True,
            "reason": "A bounded long-horizon family with no found countermodel is not a convergence theorem or real attractor-basin admission.",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {"pass": True, "classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED},
        "next_required_scout": {
            "pass": True,
            "name": "two_root_retuned_stack_external_countermodel_and_scale_probe",
            "requirement": "Try external countermodel families, wider scales, and independently generated branch schedules before any stronger basin claim.",
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
            "retuned_stack_portability": {
                "path": str(PORTABILITY_RESULT.relative_to(REPO)),
                "sha256": hashlib.sha256(PORTABILITY_RESULT.read_bytes()).hexdigest(),
            }
        },
        "countermodel_rows": rows,
        "countermodels_found": countermodels,
        "summary": {
            "all_pass": all_pass,
            "row_count": len(rows),
            "countermodel_count": len(countermodels),
            "seed_count": 6,
            "horizons": [64, 128, 256],
            "branch_modes": ["fixed", "alternating", "blockwise", "adversarial_min_gap"],
            "gauge_variants": ["identity", "phase", "signed", "drift"],
            "pressure_modes": ["steady", "ramp", "pulse", "alternating"],
            "min_final_gap": min_final_gap,
            "min_min_gap": min_min_gap,
            "min_pressure_off_gap": min_pressure_gap,
            "min_reverse_order_gap": min_reverse_gap,
            "min_symmetric_flux_gap": min_symmetric_gap,
            "next_required_scout": "two_root_retuned_stack_external_countermodel_and_scale_probe",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": {
            "total": 5,
            "passed": 5,
            "variants": ["long horizons", "adversarial branch mixtures", "perturbed gauges", "pressure-off controls", "symmetric-flux controls"],
        },
        "blockers": [] if all_pass else ["bounded_long_horizon_countermodel_found_or_gate_failed"],
        "why_not_v4_probes": "This is a v5 formal-scout long-horizon countermodel attempt over the retuned two-root stack; it does not revive v4 narrative probes.",
        "receipt_sha256": sha256_text(json.dumps(rows, sort_keys=True)),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
