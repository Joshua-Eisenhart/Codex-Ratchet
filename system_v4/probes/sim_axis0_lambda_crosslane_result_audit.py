#!/usr/bin/env python3
"""
sim_axis0_lambda_crosslane_result_audit.py

Persisted-result Axis 0 semantic consistency witness.

This does not rebuild the live semantic lanes. It loads the lane-owned semantic
rows already written by the lambda cosmology, seam, through-shells, and PyG
probes, then reruns the shared cross-lane contract over those persisted rows.
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

from axis0_lambda_crosslane_semantic_core import run_positive_tests_from_results
from sim_integration_quantum_open_entangle_correlator_mega_stack import _json_default


classification = "classical_baseline"
divergence_log = (
    "Persisted-result Axis 0 cross-lane semantic audit. This does not claim a "
    "finished cosmology law. It checks whether the lane-owned semantic rows "
    "already written by the lambda cosmology, seam, through-shells, and PyG "
    "witnesses still satisfy the shared semantic bridge when read back from "
    "result artifacts."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "persisted semantic vectors and cross-lane aggregation arithmetic",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "semantic propagator witness over persisted lane rows",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "open-system source witness reused by the persisted semantic bridge",
    },
    "cirq": {
        "tried": True,
        "used": True,
        "reason": "entangling source witness reused by the persisted semantic bridge",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "QNode source witness reused by the persisted semantic bridge",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "consensus frontier fit witness over persisted lane rows",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "message-passing witness over the persisted semantic graph",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "QF_LRA contradiction witness over persisted semantic rows",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "geometric carrier witness for the persisted consensus vector",
    },
    "torch_ga": {
        "tried": True,
        "used": True,
        "reason": "geometric algebra roundtrip witness for the persisted consensus vector",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "spherical-harmonic parity witness for persisted semantic rows",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "ordered DAG witness over the persisted semantic frontier",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "higher-order coupling witness across persisted lane triplets",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "cell-complex boundary witness for persisted cross-lane closure",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "persistent topology witness for persisted semantic parity",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "symbolic interpolation and derivative witness for persisted semantic rows",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "constraint witness over the persisted semantic frontier",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "Frechet-mean manifold witness for the persisted semantic carrier",
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
    "sim_axis0_lambda_crosslane_result_audit_results.json",
)


def main() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    positive = run_positive_tests_from_results()
    summary = {
        "persisted_positive_all_pass": bool(positive["pass"]),
        "all_pass": bool(positive["pass"]),
    }

    results = {
        "name": "sim_axis0_lambda_crosslane_result_audit",
        "timestamp": datetime.now(UTC).isoformat(),
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "audit_mode": "persisted_results",
        "positive": positive,
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
