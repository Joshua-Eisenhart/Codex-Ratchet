#!/usr/bin/env python3
"""
sim_qutip_capability.py -- Tool-capability isolation sim for qutip.
"""

from __future__ import annotations

import json
import os

import numpy as np
import qutip

from receipt_boundary import apply_default_receipt_boundary


classification = "canonical"
divergence_log = (
    "Capability isolation witness for qutip: ket, density-matrix, and expectation "
    "surfaces are exercised here so broader bridge sims can treat qutip as an "
    "admitted nonclassical witness instead of an ad hoc runtime dependency."
)

_NOT_USED_REASON = (
    "not used: this bounded QuTiP capability receipt isolates ket, density-matrix, "
    "expectation-value, and tiny rotation APIs; other tool families require separate receipts."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "supportive numeric finite-value checks for the bounded QuTiP ket, density-matrix, and expectation-value controls"},
    "qutip": {"tried": True, "used": True, "reason": "load-bearing capability under test: qutip.basis, ket2dm, sigmax/sigmaz expectation, and matrix exponential state rotation decide every pass/fail verdict"},
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
    "numpy": "supportive",
    "qutip": "load_bearing",
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

WITNESS_INFO = {
    "witness_use_cases": [
        "system_v4/probes/sim_integration_quantum_open_entangle_correlator_mega_stack.py",
        "system_v4/probes/sim_integration_qutip_open_system_bridge.py",
        "system_v4/probes/sim_integration_thermo_open_system_bridge_stack.py",
    ]
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
        "surviving_alternatives": [
            "This receipt isolates bounded QuTiP ket, density-matrix, expectation, and tiny rotation APIs; it does not prove open-system, channel, or mutual-information lego behavior."
        ],
        "demotion_condition": (
            "Demote this QuTiP capability receipt if basis vectors, density "
            "matrix construction, Pauli expectations, or the small-rotation "
            "boundary control fail on rerun."
        ),
        "out_of_scope": [
            "no mutual-information lego promotion",
            "no channel or Lindblad bridge claim",
            "no QIT engine claim",
            "no axis claim",
            "no GStack claim",
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_qutip_capability",
        target="Use as bounded QuTiP capability evidence before exact QuTiP lego-fit or integration packets.",
    )
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "qutip_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
