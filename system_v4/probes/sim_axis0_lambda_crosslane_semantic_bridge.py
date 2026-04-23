#!/usr/bin/env python3
"""
sim_axis0_lambda_crosslane_semantic_bridge.py

Cross-lane Axis 0 semantics bridge tying together:
  - lambda-shell expansion cosmology proxy,
  - Axis 0 x Axis 6 coupling seam,
  - differentiable through-shells mechanics,
  - PyG theta-gradient proxy.

This is still a bounded semantics witness, not a cosmology proof. The goal is
to force the lambda/expansion lane to answer to the same semantic bridge
surfaces as the seam, shell-mechanics, and PyG proxy lanes.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import cirq
import cvc5
import e3nn
import gudhi
import numpy as np
import pennylane as qml
import qutip
import rustworkx as rx
import sympy as sp
import torch
import torch_ga
import xgi
from clifford import Cl
from e3nn import o3
from geomstats.geometry.hypersphere import Hypersphere
from scipy.linalg import expm
from toponetx import CellComplex
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
from z3 import Solver

from axis0_lambda_crosslane_semantic_core import (
    run_boundary_tests,
    run_negative_tests,
    run_positive_tests,
)
from sim_integration_quantum_open_entangle_correlator_mega_stack import _json_default


classification = "classical_baseline"
divergence_log = (
    "Classical-to-nonclassical bridge baseline: this is a bounded cross-lane "
    "Axis 0 semantics witness. It does not claim a finished cosmology law. It "
    "tests whether the lambda-shell expansion lane aligns semantically with the "
    "Axis 0 x Axis 6 seam, the through-shells mechanics lane, and the PyG "
    "theta-gradient proxy on one shared source/graph/topology/solver/manifold surface."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "semantic vectors, pairwise alignment, expansion history, and cross-lane aggregation arithmetic",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "matrix exponential propagator for the cross-lane semantic frontier",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "open-system source witness for the shared cosmology bridge surface",
    },
    "cirq": {
        "tried": True,
        "used": True,
        "reason": "entangling source witness for the shared cosmology bridge surface",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "QNode source witness for the shared cosmology bridge surface",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "cross-lane fit witness over the consensus semantic frontier",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "message-passing witness over the ranked cross-lane semantic graph",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "QF_LRA contradiction witness for the ranked cross-lane semantic frontier",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "geometric carrier witness for the consensus semantic vector",
    },
    "torch_ga": {
        "tried": True,
        "used": True,
        "reason": "geometric algebra roundtrip witness for the consensus semantic vector",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "spherical-harmonic parity witness for the consensus semantic vector under reflection",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "ordered DAG witness over the ranked cross-lane semantic frontier",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "higher-order semantic coupling witness across lane triplets",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "cell-complex boundary witness for cross-lane closure",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "persistent topology witness for cross-lane semantic parity",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "symbolic interpolation and derivative witness for the cross-lane semantic frontier",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "constraint witness over the ranked cross-lane semantic frontier",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "Frechet-mean manifold witness for the consensus semantic carrier",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "load_bearing",
    "qutip": "load_bearing",
    "cirq": "load_bearing",
    "pennylane": "load_bearing",
    "pytorch": "load_bearing",
    "pyg": "load_bearing",
    "cvc5": "load_bearing",
    "clifford": "load_bearing",
    "torch_ga": "load_bearing",
    "e3nn": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "geomstats": "load_bearing",
}

RESULTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "a2_state",
    "sim_results",
    "sim_axis0_lambda_crosslane_semantic_bridge_results.json",
)


def main() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    summary = {
        "positive_all_pass": bool(positive["pass"]),
        "negative_all_pass": bool(negative["pass"]),
        "boundary_all_pass": bool(boundary["pass"]),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_axis0_lambda_crosslane_semantic_bridge",
        "timestamp": datetime.now(UTC).isoformat(),
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "overall_pass": bool(summary["all_pass"]),
        "all_pass": bool(summary["all_pass"]),
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)

    print(f"PASS={bool(summary['all_pass'])}")
    print(f"Results written to {RESULTS_PATH}")
    print(f"summary.all_pass = {summary['all_pass']}")
    return 0 if summary["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
