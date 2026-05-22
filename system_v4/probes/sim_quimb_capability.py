#!/usr/bin/env python3
"""
sim_quimb_capability.py -- Tool-capability isolation sim for quimb.

This is a bounded capability receipt for the tensor-network primitives used by
the v5 formal scouts. It does not promote any PEPS, PEPS3D, manifold, bridge,
axis, or attractor-basin claim.
"""

classification = "canonical"

import json
import math
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")

import numpy as np

from receipt_boundary import apply_default_receipt_boundary

_NOT_USED_REASON = (
    "not used: this bounded quimb capability receipt isolates tensor-network "
    "carrier construction, finite overlap, and tiny MPS/PEPS/PEPS3D API checks; "
    "other tool families require separate receipts."
)

TOOL_MANIFEST = {
    "quimb": {"tried": False, "used": False, "reason": "under test"},
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive fixture array construction for quimb tensor-network carriers",
    },
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "quimb": "load_bearing",
    "numpy": "supportive",
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import quimb.tensor as qtn

    QUIMB_OK = True
    QUIMB_VERSION = getattr(qtn, "__version__", "unknown")
    TOOL_MANIFEST["quimb"]["tried"] = True
    TOOL_MANIFEST["quimb"]["used"] = True
    TOOL_MANIFEST["quimb"]["reason"] = (
        "load-bearing capability under test: quimb MPS, PEPS, PEPS3D, "
        "finite overlap, and finite entropy API outputs decide this receipt."
    )
except Exception as exc:
    qtn = None
    QUIMB_OK = False
    QUIMB_VERSION = None
    TOOL_MANIFEST["quimb"]["reason"] = f"not installed or failed import: {exc}"


def finite_float(value) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def peps_arrays() -> np.ndarray:
    arrays = np.empty((2, 2), dtype=object)
    for i in range(2):
        for j in range(2):
            arrays[i, j] = np.ones((2, 2, 2), dtype=float) / (1.0 + i + j)
    return arrays


def peps3d_arrays() -> np.ndarray:
    arrays = np.empty((2, 2, 2), dtype=object)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                arrays[i, j, k] = np.ones((2, 2, 2, 2), dtype=float) / (1.0 + i + j + k)
    return arrays


def all_pass(section: dict) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def run_positive_tests() -> dict:
    results = {}
    if not QUIMB_OK:
        return {"quimb_available": {"pass": False, "detail": "quimb missing"}}

    results["quimb_available"] = {"pass": True, "version": QUIMB_VERSION}

    mps = qtn.MPS_rand_state(4, bond_dim=2, seed=0)
    overlap = float(mps.H @ mps)
    entropy = float(mps.entropy(2))
    results["mps_finite_overlap_entropy"] = {
        "pass": mps.num_tensors == 4 and finite_float(overlap) and finite_float(entropy),
        "num_tensors": int(mps.num_tensors),
        "overlap": overlap,
        "entropy_cut_2": entropy,
    }

    peps = qtn.PEPS(peps_arrays())
    results["peps_2x2_carrier_constructs"] = {
        "pass": peps.num_tensors == 4 and len(peps.tensor_map) == 4,
        "num_tensors": int(peps.num_tensors),
        "tensor_map_size": len(peps.tensor_map),
    }

    peps3d = qtn.PEPS3D(peps3d_arrays())
    results["peps3d_2x2x2_carrier_constructs"] = {
        "pass": peps3d.num_tensors == 8 and len(peps3d.tensor_map) == 8,
        "num_tensors": int(peps3d.num_tensors),
        "tensor_map_size": len(peps3d.tensor_map),
    }

    return results


def run_negative_tests() -> dict:
    results = {}
    if not QUIMB_OK:
        return {"quimb_available": {"pass": False, "detail": "quimb missing"}}

    raised = False
    error_type = None
    bad = peps_arrays()
    bad[0, 0] = np.ones((2, 2, 2, 2), dtype=float)
    try:
        qtn.PEPS(bad)
    except Exception as exc:
        raised = True
        error_type = type(exc).__name__
    results["peps_bad_boundary_rank_raises"] = {
        "pass": raised,
        "error_type": error_type,
    }

    mps = qtn.MPS_rand_state(4, bond_dim=2, seed=0)
    wrong_overlap = 0.0
    actual_overlap = float(mps.H @ mps)
    results["mps_overlap_not_wrong_zero"] = {
        "pass": abs(actual_overlap - wrong_overlap) > 1e-9,
        "actual_overlap": actual_overlap,
        "wrong_overlap": wrong_overlap,
    }

    return results


def run_boundary_tests() -> dict:
    results = {}
    if not QUIMB_OK:
        return {"quimb_available": {"pass": False, "detail": "quimb missing"}}

    one_site = qtn.MPS_rand_state(1, bond_dim=1, seed=1)
    overlap = float(one_site.H @ one_site)
    results["one_site_mps_boundary"] = {
        "pass": one_site.num_tensors == 1 and finite_float(overlap),
        "num_tensors": int(one_site.num_tensors),
        "overlap": overlap,
    }

    minimal_peps = qtn.PEPS(np.array([[np.ones((2,), dtype=float)]], dtype=object))
    results["one_by_one_peps_boundary"] = {
        "pass": minimal_peps.num_tensors == 1 and len(minimal_peps.tensor_map) == 1,
        "num_tensors": int(minimal_peps.num_tensors),
        "tensor_map_size": len(minimal_peps.tensor_map),
    }

    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    summary = {
        "positive_all_pass": all_pass(positive),
        "negative_all_pass": all_pass(negative),
        "boundary_all_pass": all_pass(boundary),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_quimb_capability",
        "purpose": (
            "Bounded isolation probe of quimb tensor-network capabilities. "
            "This receipt unblocks load-bearing quimb declarations only at the "
            "tool API level."
        ),
        "classification": classification,
        "quimb_version": QUIMB_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "operation_sequence": [
            "import quimb.tensor and record import status",
            "construct a four-site MPS and check finite overlap plus entropy",
            "construct a 2x2 PEPS carrier and check tensor count",
            "construct a 2x2x2 PEPS3D carrier and check tensor count",
            "run failure controls for malformed PEPS boundary rank and wrong MPS overlap",
            "run minimal one-site MPS and 1x1 PEPS boundary checks",
        ],
        "carrier_topology": (
            "tiny MPS, PEPS, and PEPS3D tensor-network carriers only; no "
            "geometric manifold, Axis0, physics, bridge, or attractor-basin "
            "claim is made"
        ),
        "pass_fail_predicate": (
            "quimb import, finite MPS overlap/entropy, PEPS/PEPS3D carrier "
            "construction, malformed-carrier rejection, wrong-overlap exclusion, "
            "and minimal boundary carriers must all pass."
        ),
        "graveyards": [
            "quimb import fails",
            "MPS finite overlap or entropy is unavailable",
            "PEPS or PEPS3D carrier construction fails on tiny valid fixtures",
            "malformed PEPS boundary rank is accepted silently",
            "wrong zero-overlap fixture matches the actual MPS overlap",
        ],
        "out_of_scope": [
            "no PEPS or PEPS3D scientific claim",
            "no manifold closure claim",
            "no Axis0 claim",
            "no attractor-basin claim",
            "no PyTorch substrate migration claim",
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_quimb_capability",
        target=(
            "Use as bounded quimb tensor-network API capability evidence before "
            "exact quimb lego-fit or tool-coupling packets."
        ),
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "quimb_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
