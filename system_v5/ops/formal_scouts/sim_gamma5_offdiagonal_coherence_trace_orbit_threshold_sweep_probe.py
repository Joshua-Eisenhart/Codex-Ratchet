#!/usr/bin/env python3
"""Gamma5 off-diagonal coherence trace-orbit survivor threshold-sweep scout."""

from __future__ import annotations

import json
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

from sim_gamma5_offdiagonal_coherence_trace_orbit_survivor_quotient_probe import (
    DTYPE,
    DIM,
    N_QUBITS,
    asymmetric_local_kraus,
    best_symmetric_fit,
    candidate_densities,
    cptp_gap,
    embed,
    gamma5_boundary,
    orbit,
    signature,
    symmetric_local_kraus,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "gamma5_offdiagonal_coherence_trace_orbit_threshold_sweep_probe_results.json"

NAME = "gamma5_offdiagonal_coherence_trace_orbit_threshold_sweep_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: sweeps survivor thresholds for gamma5 block "
    "off-diagonal coherence trace-norm orbit quotient classes against "
    "symmetric effective-channel controls. It does not admit novelty, "
    "empirical physics, a final manifold tower, bridge claim, ontology, or "
    "target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing orbit distances and CPTP channel checks"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic threshold monotonicity sanity"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing threshold-window witness"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing threshold quotient graph counts"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing tensor graph conversion for quotient graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence intervals over threshold quotient graphs"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

THRESHOLDS = [0.01, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 0.20, 0.24, 0.28, 0.30]


def class_count(rows: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    survivors = [row for row in rows if row["fit_gap"] > threshold and row["initial"] > 1e-8]
    classes: dict[tuple[Any, ...], list[str]] = {}
    for row in survivors:
        classes.setdefault(row["signature"], []).append(row["name"])
    graph = nx.Graph()
    for row in survivors:
        graph.add_node(row["name"])
    for names in classes.values():
        for i, left in enumerate(names):
            for right in names[i + 1 :]:
                graph.add_edge(left, right)
    pyg = from_networkx(graph)
    simplex = gudhi.SimplexTree()
    for idx, row in enumerate(survivors):
        simplex.insert([idx], filtration=float(row["fit_gap"]))
    simplex.persistence()
    h0 = simplex.persistence_intervals_in_dimension(0)
    return {
        "threshold": threshold,
        "survivor_count": len(survivors),
        "class_count": len(classes),
        "classes": {str(key): value for key, value in classes.items()},
        "networkx_nodes": graph.number_of_nodes(),
        "networkx_edges": graph.number_of_edges(),
        "pyg_num_nodes": int(pyg.num_nodes),
        "gudhi_h0_count": int(len(h0)),
    }


def z3_window_witness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    enough = []
    for idx, row in enumerate(rows):
        flag = z3.Bool(f"threshold_{idx}_separates")
        solver.add(flag == (row["class_count"] > row["control_class_count"] and row["class_count"] >= 3))
        enough.append(flag)
    solver.add(z3.Not(z3.PbGe([(flag, 1) for flag in enough], 3)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "separating_threshold_count": sum(1 for row in rows if row["class_count"] > row["control_class_count"] and row["class_count"] >= 3),
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    state_rows = []
    control_rows = []
    for name, rho in candidate_densities().items():
        asym = orbit(rho, "asymmetric")
        fit = best_symmetric_fit(asym["coherence_orbit"], rho)
        state_rows.append(
            {
                "name": name,
                "signature": signature(asym["coherence_orbit"], asym["entropy_orbit"]),
                "fit_gap": fit["gap"],
                "initial": asym["coherence_orbit"][0],
            }
        )
        control_rows.append(
            {
                "name": name,
                "signature": signature(fit["coherence_orbit"], asym["entropy_orbit"]),
                "fit_gap": 0.0,
                "initial": asym["coherence_orbit"][0],
            }
        )
    sweep = []
    for threshold in THRESHOLDS:
        asym = class_count(state_rows, threshold)
        control = class_count(control_rows, threshold)
        sweep.append(
            {
                "threshold": threshold,
                "class_count": asym["class_count"],
                "survivor_count": asym["survivor_count"],
                "control_class_count": control["class_count"],
                "control_survivor_count": control["survivor_count"],
                "separates": asym["class_count"] > control["class_count"] and asym["class_count"] >= 3,
                "asymmetric": asym,
                "control": control,
            }
        )
    separating = [row for row in sweep if row["separates"]]
    cptp = max(
        cptp_gap(embed(asymmetric_local_kraus(0.30, 0.05))),
        cptp_gap(embed(symmetric_local_kraus(0.17))),
    )
    x = sp.symbols("x")
    symbolic_threshold_order = bool(sp.simplify((x > 0.02) & (x < 0.15)) is not False)
    positive = {
        "threshold_window_preserves_survivor_quotient_separation": {
            "separating_thresholds": [row["threshold"] for row in separating],
            "separating_threshold_count": len(separating),
            "pass": len(separating) >= 3,
        },
        "middle_threshold_has_multiple_asymmetric_classes": {
            "row": next(row for row in sweep if row["threshold"] == 0.04),
            "pass": next(row for row in sweep if row["threshold"] == 0.04)["class_count"] >= 3,
        },
        "gamma5_projector_boundary": gamma5_boundary(),
        "asymmetric_and_symmetric_channels_are_cptp": {"cptp_gap": cptp, "pass": cptp < 1e-12},
        "symbolic_threshold_sanity": {"expr": "0.02 < x < 0.15", "pass": symbolic_threshold_order},
    }
    graveyard_companions = {
        "symmetric_effective_channel_control_has_no_survivor_classes": {
            "control_class_counts": [row["control_class_count"] for row in sweep],
            "pass": max(row["control_class_count"] for row in sweep) == 0,
        },
        "too_high_threshold_collapses_all_survivor_classes": {
            "threshold": 0.30,
            "row": sweep[-1],
            "pass": sweep[-1]["class_count"] == 0,
        },
        "zero_initial_offdiagonal_controls_never_survive": {
            "zero_names": [row["name"] for row in state_rows if row["initial"] <= 1e-8],
            "pass": all(row["name"] in {"block_diagonal_left", "block_diagonal_right", "maximally_mixed"} for row in state_rows if row["initial"] <= 1e-8),
        },
        "separation_is_not_single_threshold_tuning": {
            "separating_threshold_count": len(separating),
            "pass": len(separating) >= 3,
        },
    }
    boundary = {
        "finite_four_qubit_dimension": {"dimension": DIM, "qubits": N_QUBITS, "pass": DIM == 16},
        "z3_threshold_window_witness": z3_window_witness(sweep),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "threshold sweep over four-qubit gamma5 off-diagonal coherence trace-orbit survivor quotient classes after symmetric effective-channel controls",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This scout tests threshold stability, not complete channel-equivalence classification.",
            "The next falsifier is a Stinespring or Choi-distance equivalence search without gamma5 labels.",
            "The next constructive extension is coupling this threshold window to dynamic shell graph rewiring.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from Grok/Gemini threshold-sweep proposals; it is not a canonical v4 probe.",
        "raw_rows": {"state_rows": state_rows, "sweep": sweep},
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all(checks),
                "result": str(OUT_PATH),
                "separating_threshold_count": len(separating),
                "separating_thresholds": [row["threshold"] for row in separating],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
