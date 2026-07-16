#!/usr/bin/env python3
"""Bounded QuTiP mesolve amplitude-damping channel fit probe.

Pure tool-lego fit only. This verifies that QuTiP can express one local
Lindblad channel fixture and match its finite-time Kraus reference. It does
not promote a lego, coupling, bridge, axis, GStack, QIT, or nonclassical claim.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any

import numpy as np

from receipt_boundary import apply_default_receipt_boundary

classification = "tool_lego_fit_probe"
NAME = "qutip_mesolve_amplitude_damping_channel_fit_probe"

CLAIM_CEILING = (
    "local QuTiP channel-fit receipt only: qutip.Qobj, basis, ket2dm, "
    "destroy, mesolve, and expect express one finite amplitude-damping "
    "channel fixture against an analytic Kraus reference; promotion_allowed=false; "
    "no QIT, GStack, axis, bridge, nonclassical, or coupling claim"
)

_NOT_USED = (
    "not used: this receipt isolates one QuTiP amplitude-damping channel-local "
    "tool-lego fit fixture; other tool families require separate receipts"
)

TOOL_MANIFEST: dict[str, dict[str, Any]] = {
    "qutip": {
        "tried": False,
        "used": False,
        "reason": (
            "load-bearing target: qutip.Qobj, basis, ket2dm, destroy, mesolve, "
            "and expect decide the local channel-fit predicate"
        ),
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive analytic Kraus reference and norm checks",
    },
    "scipy": {"tried": False, "used": False, "reason": _NOT_USED},
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED},
}

TOOL_INTEGRATION_DEPTH = {
    "qutip": "load_bearing",
    "numpy": "supportive",
    "scipy": None,
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
    import qutip

    QUTIP_OK = True
    QUTIP_IMPORT_ERROR = None
    TOOL_MANIFEST["qutip"]["tried"] = True
    TOOL_MANIFEST["qutip"]["used"] = True
except Exception as exc:  # pragma: no cover - dependency absence is a receipt state
    qutip = None  # type: ignore[assignment]
    QUTIP_OK = False
    QUTIP_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
    TOOL_MANIFEST["qutip"]["reason"] = f"blocked: qutip import failed: {QUTIP_IMPORT_ERROR}"


def _as_pairs(matrix: np.ndarray) -> list[list[list[float]]]:
    return [
        [[float(value.real), float(value.imag)] for value in row]
        for row in np.asarray(matrix, dtype=np.complex128)
    ]


def _density_from_state(state: np.ndarray) -> np.ndarray:
    return np.outer(state, state.conjugate())


def _analytic_amplitude_damping(rho: np.ndarray, gamma: float, time: float) -> np.ndarray:
    decay = math.exp(-gamma * time)
    k0 = np.array([[1.0, 0.0], [0.0, math.sqrt(decay)]], dtype=np.complex128)
    k1 = np.array([[0.0, math.sqrt(1.0 - decay)], [0.0, 0.0]], dtype=np.complex128)
    return k0 @ rho @ k0.conjugate().T + k1 @ rho @ k1.conjugate().T


def _qutip_mesolve_state(rho0: np.ndarray, gamma: float, time: float) -> np.ndarray:
    assert qutip is not None
    rho_q = qutip.Qobj(rho0, dims=[[2], [2]])
    collapse = [math.sqrt(gamma) * qutip.destroy(2)]
    result = qutip.mesolve(0.0 * qutip.qeye(2), rho_q, [0.0, time], collapse, [])
    return np.asarray(result.states[-1].full(), dtype=np.complex128)


def _density_ok(rho: np.ndarray, tol: float = 1e-10) -> bool:
    hermitian = np.allclose(rho, rho.conjugate().T, atol=tol)
    trace_one = abs(np.trace(rho) - 1.0) < tol
    eigs = np.linalg.eigvalsh((rho + rho.conjugate().T) / 2.0)
    psd = bool(np.all(eigs >= -tol))
    return bool(hermitian and trace_one and psd)


def _blocked_section() -> dict[str, dict[str, Any]]:
    return {
        "qutip_import_gate": {
            "pass": False,
            "status": "blocked",
            "qutip_import_error": QUTIP_IMPORT_ERROR,
        }
    }


def run_positive_tests() -> dict[str, dict[str, Any]]:
    if not QUTIP_OK:
        return _blocked_section()

    initial = np.array([1.0, 1.0], dtype=np.complex128) / math.sqrt(2.0)
    rho0 = _density_from_state(initial)
    gamma = 0.41
    times = [0.0, 0.2, 0.7, 1.4]
    rows = []
    max_error = 0.0
    for time in times:
        qutip_rho = _qutip_mesolve_state(rho0, gamma, time)
        analytic_rho = _analytic_amplitude_damping(rho0, gamma, time)
        error = float(np.linalg.norm(qutip_rho - analytic_rho))
        max_error = max(max_error, error)
        rows.append(
            {
                "time": time,
                "frobenius_error": error,
                "density_ok": _density_ok(qutip_rho),
                "excited_population": float(qutip_rho[1, 1].real),
            }
        )

    plus = (qutip.basis(2, 0) + qutip.basis(2, 1)).unit()
    rho_plus = qutip.ket2dm(plus)
    z_expect = float(qutip.expect(qutip.sigmaz(), rho_plus))

    return {
        "mesolve_matches_analytic_kraus_channel": {
            "pass": max_error < 2e-6 and all(row["density_ok"] for row in rows),
            "max_frobenius_error": max_error,
            "cases": rows,
        },
        "basis_ket2dm_expectation_fixture_is_consistent": {
            "pass": abs(z_expect) < 1e-12,
            "z_expectation": z_expect,
            "fixture": "ket2dm((|0> + |1>)/sqrt(2))",
        },
    }


def run_negative_tests() -> dict[str, dict[str, Any]]:
    if not QUTIP_OK:
        return _blocked_section()

    initial = np.array([1.0, 1.0], dtype=np.complex128) / math.sqrt(2.0)
    rho0 = _density_from_state(initial)
    gamma = 0.41
    time = 1.0
    qutip_rho = _qutip_mesolve_state(rho0, gamma, time)
    identity_surrogate_error = float(np.linalg.norm(qutip_rho - rho0))
    wrong_rate = _analytic_amplitude_damping(rho0, 2.0 * gamma, time)
    wrong_rate_error = float(np.linalg.norm(qutip_rho - wrong_rate))

    invalid_dims_rejected = False
    invalid_dims_error = None
    try:
        qutip.Qobj(np.eye(3), dims=[[2], [2]])
    except Exception as exc:
        invalid_dims_rejected = True
        invalid_dims_error = f"{type(exc).__name__}: {exc}"

    return {
        "identity_channel_surrogate_is_excluded": {
            "pass": identity_surrogate_error > 1e-2,
            "error": identity_surrogate_error,
            "excluded_claim": "identity evolution is not an admissible substitute for amplitude damping",
        },
        "wrong_rate_kraus_reference_is_excluded": {
            "pass": wrong_rate_error > 1e-2,
            "error": wrong_rate_error,
            "excluded_claim": "a mismatched damping rate cannot validate this QuTiP channel fixture",
        },
        "invalid_qobj_dimension_assignment_is_rejected": {
            "pass": invalid_dims_rejected,
            "error": invalid_dims_error,
        },
    }


def run_boundary_tests() -> dict[str, dict[str, Any]]:
    if not QUTIP_OK:
        return _blocked_section()

    excited = np.array([0.0, 1.0], dtype=np.complex128)
    rho_excited = _density_from_state(excited)
    gamma = 0.41
    zero_time = _qutip_mesolve_state(rho_excited, gamma, 0.0)
    long_time = _qutip_mesolve_state(rho_excited, gamma, 30.0 / gamma)
    ground = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)

    return {
        "zero_time_boundary_is_identity": {
            "pass": float(np.linalg.norm(zero_time - rho_excited)) < 1e-12,
            "error": float(np.linalg.norm(zero_time - rho_excited)),
        },
        "long_time_boundary_approaches_ground_state": {
            "pass": float(np.linalg.norm(long_time - ground)) < 2e-6,
            "ground_error": float(np.linalg.norm(long_time - ground)),
            "final_density": _as_pairs(long_time),
        },
    }


def _section_pass(section: dict[str, dict[str, Any]]) -> bool:
    return bool(section) and all(bool(row.get("pass", False)) for row in section.values())


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _section_pass(positive),
        "negative_all_pass": _section_pass(negative),
        "boundary_all_pass": _section_pass(boundary),
        "promotion_allowed": False,
    }
    summary["all_pass"] = bool(
        QUTIP_OK
        and summary["positive_all_pass"]
        and summary["negative_all_pass"]
        and summary["boundary_all_pass"]
    )

    results = {
        "name": NAME,
        "classification": classification,
        "sim_execution_kind": classification,
        "status": "passed" if summary["all_pass"] else "blocked_or_failed",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "operation_sequence": [
            "construct one-qubit density matrix with qutip.basis and qutip.ket2dm",
            "evolve the same density matrix under qutip.mesolve with sqrt(gamma) * qutip.destroy(2)",
            "compute finite-time analytic amplitude-damping Kraus reference",
            "compare QuTiP density output to Kraus reference across bounded times",
            "run identity, wrong-rate, invalid-dims, zero-time, and long-time controls",
        ],
        "carrier_topology": {
            "carrier": "one finite two-level density matrix",
            "topology": "single local amplitude-damping channel fixture; no graph, bundle, bridge, axis, or multi-layer topology",
        },
        "observable": "Frobenius norm between qutip.mesolve density matrices and analytic Kraus density matrices, plus density validity and expectation checks",
        "pass_fail_predicate": "pass iff QuTiP output matches Kraus reference within 2e-6, density structure is preserved, wrong controls are excluded, and boundary controls behave as named",
        "graveyards": [
            "identity evolution surrogate",
            "wrong damping-rate Kraus reference",
            "invalid Qobj dimension assignment",
            "any promotion beyond local QuTiP channel fit",
        ],
        "baselines": [
            "analytic finite-time amplitude-damping Kraus map",
            "zero-time identity boundary",
            "long-time ground-state boundary",
        ],
        "alternative_formulations": [
            "QuTiP propagator/superoperator API on the same channel fixture",
            "QuTiP kraus_to_super or liouvillian API in a separate receipt",
            "SciPy Liouvillian matrix exponential baseline kept separate from this fit receipt",
        ],
        "exact_tool_function_needs": [
            "qutip.basis",
            "qutip.ket2dm",
            "qutip.Qobj",
            "qutip.destroy",
            "qutip.mesolve",
            "qutip.expect",
        ],
        "lego_or_coupling_target": "channel_cptp_map / lindbladian_evolution tool-lego fit only",
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
        "next_lego_target": "channel_cptp_map / lindbladian_evolution QuTiP-local fit target only",
        "promotion_condition": "No promotion from this receipt; any later lego row must cite this exact result and pass its own admission gate.",
        "demotion_condition": "Demote or block if QuTiP import, mesolve/Kraus agreement, density validity, negative controls, or boundary controls fail.",
        "blocked_until": "blocked from QIT, GStack, axis, bridge, nonclassical, or tool-coupling claims until separate downstream receipts exist",
        "out_of_scope": [
            "QIT claims",
            "GStack claims",
            "axis claims",
            "bridge claims",
            "nonclassical claims",
            "tool-tool coupling",
            "whole channel-family promotion",
        ],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target="channel_cptp_map / lindbladian_evolution QuTiP-local fit target only",
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
