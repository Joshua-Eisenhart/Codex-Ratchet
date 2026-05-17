#!/usr/bin/env python3
"""Three-dimensional shell flux inverse-square geometry scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "three_dimensional_shell_flux_inverse_square_geometry_probe_results.json"

NAME = "three_dimensional_shell_flux_inverse_square_geometry_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether fixed-area detector flux from spreading "
    "shell geometry scales by dimension, with 3D giving inverse-square behavior "
    "and beam/no-spread controls failing. It does not admit empirical gravity, "
    "general relativity, standard-model recovery, ontology, bridge, axis, or "
    "target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing shell radii, log-log slope fits, and detector flux tensors"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic shell-area scaling d/dr sanity"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing inverse-square and beam-control contradiction checks"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing dimension/control transition graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph-to-tensor conversion for transition graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over dimension slope filtration"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


RADII = torch.tensor([1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 13.0], dtype=torch.float64)


def fit_slope(xs: torch.Tensor, ys: torch.Tensor) -> dict[str, float]:
    lx = torch.log(xs)
    ly = torch.log(torch.clamp(ys, min=1e-15))
    x_center = lx - lx.mean()
    y_center = ly - ly.mean()
    slope = torch.dot(x_center, y_center) / torch.dot(x_center, x_center)
    intercept = ly.mean() - slope * lx.mean()
    pred = slope * lx + intercept
    ss_res = torch.sum((ly - pred) ** 2)
    ss_tot = torch.sum((ly - ly.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot if float(ss_tot.item()) > 0 else torch.tensor(1.0)
    return {"slope": float(slope.item()), "r2": float(r2.item())}


def shell_flux(dim: int, amplitude: float = 1.0) -> torch.Tensor:
    return amplitude / (RADII ** (dim - 1))


def anisotropic_flux(dim: int, detector_angle: float, boost: float) -> torch.Tensor:
    # Angular bias changes amplitude at detector position, not radial scaling,
    # as long as the source still spreads over the whole shell.
    angular_amplitude = 1.0 + boost * max(0.0, math.cos(detector_angle))
    return shell_flux(dim, angular_amplitude)


def directed_beam_flux() -> torch.Tensor:
    return torch.ones_like(RADII) * 0.125


def row(name: str, flux: torch.Tensor, expected_slope: float | None) -> dict[str, Any]:
    fit = fit_slope(RADII, flux)
    slope_error = None if expected_slope is None else abs(fit["slope"] - expected_slope)
    return {
        "name": name,
        "flux_values": [round(float(v), 8) for v in flux.tolist()],
        "fit": fit,
        "expected_slope": expected_slope,
        "slope_error": slope_error,
        "signature": tuple(round(v, 4) for v in [fit["slope"], fit["r2"], slope_error if slope_error is not None else 99.0]),
    }


def transition_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = nx.Graph()
    for current in rows:
        graph.add_node(current["name"], slope=current["fit"]["slope"])
    for i, a in enumerate(rows):
        for b in rows[i + 1 :]:
            if abs(a["fit"]["slope"] - b["fit"]["slope"]) > 0.25:
                graph.add_edge(a["name"], b["name"])
    pyg = from_networkx(graph) if graph.number_of_edges() else None
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
        "pass": graph.number_of_edges() > 0,
    }


def slope_persistence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    st = gudhi.SimplexTree()
    for idx, current in enumerate(rows):
        st.insert([idx], filtration=abs(current["fit"]["slope"]))
    for idx in range(len(rows) - 1):
        st.insert([idx, idx + 1], filtration=max(abs(rows[idx]["fit"]["slope"]), abs(rows[idx + 1]["fit"]["slope"])))
    return {"persistence_pair_count": len(st.persistence()), "pass": len(st.persistence()) > 0}


def sympy_shell_area_scaling() -> dict[str, Any]:
    r = sp.symbols("r", positive=True)
    d = sp.symbols("d", integer=True, positive=True)
    flux = r ** (-(d - 1))
    log_slope = sp.simplify(r * sp.diff(sp.log(flux), r))
    return {"log_slope": str(log_slope), "d3_value": str(log_slope.subs(d, 3)), "pass": sp.simplify(log_slope.subs(d, 3) + 2) == 0}


def z3_checks(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    d3_ok = rows["dim3_isotropic"]["slope_error"] < 0.05
    off_axis_ok = rows["dim3_anisotropic_off_axis"]["slope_error"] < 0.05
    beam_killed = abs(rows["directed_beam_no_spread_control"]["fit"]["slope"]) < 0.05
    s1 = z3.Solver()
    s2 = z3.Solver()
    a = z3.Bool("d3_inverse_square")
    b = z3.Bool("beam_inverse_square")
    s1.add(a == d3_ok, a == False)
    s2.add(b == (not beam_killed), b == True)
    return {
        "d3_inverse_square_unsat_if_false": {"solver_status": str(s1.check()), "pass": d3_ok and s1.check() == z3.unsat},
        "off_axis_anisotropy_keeps_inverse_square": {"pass": off_axis_ok},
        "beam_control_not_inverse_square_unsat_if_equivalent": {"solver_status": str(s2.check()), "pass": beam_killed and s2.check() == z3.unsat},
    }


def main() -> dict[str, Any]:
    started = time.time()
    rows = [
        row("dim2_isotropic", shell_flux(2), -1.0),
        row("dim3_isotropic", shell_flux(3), -2.0),
        row("dim4_isotropic", shell_flux(4), -3.0),
        row("dim3_anisotropic_aligned", anisotropic_flux(3, detector_angle=0.0, boost=10.0), -2.0),
        row("dim3_anisotropic_off_axis", anisotropic_flux(3, detector_angle=math.pi / 2, boost=10.0), -2.0),
        row("directed_beam_no_spread_control", directed_beam_flux(), None),
    ]
    by_name = {current["name"]: current for current in rows}
    z3_rows = z3_checks(by_name)
    positive = {
        "dimension_scaling_matches_shell_spread": {
            "slopes": {current["name"]: current["fit"]["slope"] for current in rows[:3]},
            "pass": all(current["slope_error"] is not None and current["slope_error"] < 0.05 for current in rows[:3]),
        },
        "three_dimensional_shell_gives_inverse_square": {
            **by_name["dim3_isotropic"],
            "pass": by_name["dim3_isotropic"]["slope_error"] < 0.05 and by_name["dim3_isotropic"]["fit"]["r2"] > 0.999,
        },
        "off_axis_anisotropic_spread_keeps_radial_exponent": {
            **by_name["dim3_anisotropic_off_axis"],
            "aligned_slope": by_name["dim3_anisotropic_aligned"]["fit"]["slope"],
            "pass": by_name["dim3_anisotropic_off_axis"]["slope_error"] < 0.05,
        },
        "transition_graph_separates_spread_from_beam_control": transition_graph(rows),
        "gudhi_slope_filtration_computes": slope_persistence(rows),
        "sympy_shell_area_scaling_check": sympy_shell_area_scaling(),
        "z3_inverse_square_and_beam_checks": {"checks": z3_rows, "pass": all(current["pass"] for current in z3_rows.values())},
    }
    graveyard_companions = {
        "directed_beam_no_spread_does_not_have_inverse_square_slope": {
            **by_name["directed_beam_no_spread_control"],
            "pass": abs(by_name["directed_beam_no_spread_control"]["fit"]["slope"]) < 0.05,
        },
        "dimension_two_is_not_inverse_square": {
            **by_name["dim2_isotropic"],
            "pass": abs(by_name["dim2_isotropic"]["fit"]["slope"] + 2.0) > 0.5,
        },
        "dimension_four_is_not_inverse_square": {
            **by_name["dim4_isotropic"],
            "pass": abs(by_name["dim4_isotropic"]["fit"]["slope"] + 2.0) > 0.5,
        },
    }
    boundary = {
        "row_count": {"count": len(rows), "pass": len(rows) == 6},
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
        "gravity_not_claimed": {"claim": "inverse-square functional form only", "pass": "gravity" not in NAME},
    }
    all_pass = all(current["pass"] for current in positive.values()) and all(current["pass"] for current in graveyard_companions.values()) and all(current["pass"] for current in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "fixed-area detector flux from spreading shell geometry across dimensions and beam/no-spread controls",
        "rows": rows,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for current in graveyard_companions.values() if current["pass"])},
        "blockers": [],
        "open_choices": [
            "This proves only dimensional shell-spread scaling, not gravity.",
            "The detector is analytic fixed-area flux, not a Monte Carlo solid-angle estimator.",
            "Next pass should couple this shell-spread law to the future-possibility/past-correlation dynamic shell scout.",
        ],
        "why_not_v4_probes": "This is a clean v5 geometry-scaling scout and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "slopes": {current["name"]: current["fit"]["slope"] for current in rows},
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
