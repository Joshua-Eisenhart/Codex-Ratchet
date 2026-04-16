#!/usr/bin/env python3
"""
sim_qutip_capability.py -- Tool-capability isolation sim for qutip.
"""

from __future__ import annotations

import json
import os

import numpy as np
import qutip


classification = "canonical"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "supportive numeric checks for qutip capability"},
    "qutip": {"tried": True, "used": True, "reason": "capability under test -- ket, density matrix, expectation"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "qutip": "load_bearing",
}


def _all_pass(section: dict[str, dict[str, object]]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def run_positive_tests() -> dict[str, dict[str, object]]:
    ket0 = qutip.basis(2, 0)
    rho0 = qutip.ket2dm(ket0)
    plus = (ket0 + qutip.basis(2, 1)).unit()
    exp_z = qutip.expect(qutip.sigmaz(), ket0)
    exp_x = qutip.expect(qutip.sigmax(), plus)
    return {
        "density_shape": {
            "pass": rho0.shape == (2, 2),
        },
        "z_expectation_zero": {
            "pass": abs(float(exp_z) - 1.0) < 1e-10,
            "value": float(exp_z),
        },
        "x_expectation_plus": {
            "pass": abs(float(exp_x) - 1.0) < 1e-10,
            "value": float(exp_x),
        },
    }


def run_negative_tests() -> dict[str, dict[str, object]]:
    ket1 = qutip.basis(2, 1)
    exp_z = qutip.expect(qutip.sigmaz(), ket1)
    return {
        "z_expectation_one_not_plus_one": {
            "pass": abs(float(exp_z) + 1.0) < 1e-10,
            "value": float(exp_z),
        }
    }


def run_boundary_tests() -> dict[str, dict[str, object]]:
    theta = 1e-8
    rot = (-0.5j * theta * qutip.sigmay()).expm()
    state = rot * qutip.basis(2, 0)
    fidelity = abs(qutip.basis(2, 0).overlap(state)) ** 2
    return {
        "small_rotation_stable": {
            "pass": np.isfinite(fidelity) and fidelity > 0.999999999,
            "fidelity": float(fidelity),
        }
    }


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
    }
    summary["all_pass"] = all(summary.values())
    results = {
        "name": "sim_qutip_capability",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "qutip_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
