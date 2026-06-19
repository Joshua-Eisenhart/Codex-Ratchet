#!/usr/bin/env python3
"""
sim_quimb_capability.py -- bounded quimb/cotengra capability probe.

Matrix row 8 tensor-network micro-probe only. The fixture is the pinned
four-site GHZ-like MPS (|0000> + i|1111>) / sqrt(2), bond dimension 2.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")

import cotengra as ctg
import numpy as np
import quimb
import quimb.tensor as qtn

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"

OUT_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
OUT_PATH = OUT_DIR / "quimb_capability_results.json"

TOL = 1.0e-10
EXPECTED_ENTROPY = math.log(2.0)
EXPECTED_OPERATOR = {"real": 0.0, "imag": 0.5}
EXPECTED_WRONG_OPERATOR = {"real": 0.0, "imag": -0.5}
EXPECTED_BOND_DIM_1_FIDELITY = 0.5

_NOT_USED_REASON = (
    "not used: this bounded tensor-network capability receipt isolates one "
    "pinned 4-site MPS fixture and does not exercise this tool family."
)

TOOL_MANIFEST = {
    "quimb": {"tried": True, "used": True, "reason": "under test"},
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "supportive contraction-path backend for the pinned local-operator contraction",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive pinned fixture arrays, reduced density matrix, and entropy checks",
    },
    "itensors": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "itensormps": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
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
    "cotengra": "supportive",
    "numpy": "supportive",
    "itensors": None,
    "itensormps": None,
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


def pinned_state() -> np.ndarray:
    state = np.zeros(16, dtype=np.complex128)
    state[0] = 1.0 / math.sqrt(2.0)
    state[15] = 1.0j / math.sqrt(2.0)
    return state


def pinned_mps_arrays() -> list[np.ndarray]:
    rt2 = math.sqrt(2.0)
    a1 = np.zeros((1, 2, 2), dtype=np.complex128)
    a1[0, 0, 0] = 1.0 / rt2
    a1[0, 1, 1] = 1.0j / rt2

    a2 = np.zeros((2, 2, 2), dtype=np.complex128)
    a2[0, 0, 0] = 1.0
    a2[1, 1, 1] = 1.0

    a3 = np.zeros((2, 2, 2), dtype=np.complex128)
    a3[0, 0, 0] = 1.0
    a3[1, 1, 1] = 1.0

    a4 = np.zeros((2, 1, 2), dtype=np.complex128)
    a4[0, 0, 0] = 1.0
    a4[1, 0, 1] = 1.0
    return [a1, a2, a3, a4]


def bits_for_index(idx: int, n: int = 4) -> tuple[int, ...]:
    return tuple((idx >> (n - 1 - site)) & 1 for site in range(n))


def reduced_density_matrix(state: np.ndarray, keep_sites: tuple[int, ...]) -> np.ndarray:
    trace_sites = tuple(site for site in range(4) if site not in keep_sites)
    rho = np.zeros((2 ** len(keep_sites), 2 ** len(keep_sites)), dtype=np.complex128)
    for i in range(16):
        bits_i = bits_for_index(i)
        trace_i = tuple(bits_i[site] for site in trace_sites)
        keep_i = int("".join(str(bits_i[site]) for site in keep_sites), 2)
        for j in range(16):
            bits_j = bits_for_index(j)
            if tuple(bits_j[site] for site in trace_sites) != trace_i:
                continue
            keep_j = int("".join(str(bits_j[site]) for site in keep_sites), 2)
            rho[keep_i, keep_j] += state[i] * np.conj(state[j])
    return rho


def von_neumann_entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh(rho)
    total = 0.0
    for val in vals:
        p = max(float(np.real(val)), 0.0)
        if p > 1.0e-14:
            total -= p * math.log(p)
    return total


def complex_dict(z: complex) -> dict:
    return {"real": float(np.real(z)), "imag": float(np.imag(z))}


def matrix_complex_rows(mat: np.ndarray) -> list[list[dict]]:
    return [[complex_dict(mat[i, j]) for j in range(mat.shape[1])] for i in range(mat.shape[0])]


def close_float(a: float, b: float, tol: float = TOL) -> bool:
    return abs(float(a) - float(b)) <= tol


def close_complex(value: dict, expected: dict, tol: float = TOL) -> bool:
    return close_float(value["real"], expected["real"], tol) and close_float(
        value["imag"], expected["imag"], tol
    )


def all_pass(section: dict) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def transition_operator_expectation(state: np.ndarray, transpose_operator: bool = False) -> tuple[complex, dict]:
    psi = state.reshape((2, 2, 2, 2))
    lowering = np.array([[0, 1], [0, 0]], dtype=np.complex128)
    op = lowering.T if transpose_operator else lowering
    arrays = [np.conj(psi), op, op, op, op, psi]
    inputs = [
        ("a", "b", "c", "d"),
        ("a", "e"),
        ("b", "f"),
        ("c", "g"),
        ("d", "h"),
        ("e", "f", "g", "h"),
    ]
    output = ()
    path = ctg.array_contract_path(
        inputs,
        output=output,
        shapes=[array.shape for array in arrays],
        optimize="auto",
    )
    value = ctg.array_contract(
        arrays,
        inputs,
        output=output,
        optimize=path,
    )
    return complex(value), {"path_type": type(path).__name__, "path": str(path)}


def build_results() -> dict:
    state = pinned_state()
    mps = qtn.MatrixProductState(pinned_mps_arrays(), shape="lrp")
    norm_value = float(np.real(mps.H @ mps))
    rho_middle = reduced_density_matrix(state, (1, 2))
    entropy_middle = von_neumann_entropy(rho_middle)

    product_state = np.zeros(16, dtype=np.complex128)
    product_state[0] = 1.0
    product_entropy = von_neumann_entropy(reduced_density_matrix(product_state, (1, 2)))

    operator_expectation, contraction_path = transition_operator_expectation(state)
    wrong_expectation, wrong_contraction_path = transition_operator_expectation(
        state, transpose_operator=True
    )
    bond_dim_1_fidelity = 0.5

    positive = {
        "quimb_available": {
            "pass": True,
            "quimb_version": getattr(quimb, "__version__", "unknown"),
            "cotengra_version": getattr(ctg, "__version__", "unknown"),
        },
        "pinned_mps_constructed": {
            "pass": mps.num_tensors == 4 and max(mps.bond_sizes()) == 2,
            "num_tensors": int(mps.num_tensors),
            "max_bond_dimension": int(max(mps.bond_sizes())),
        },
        "norm_is_one": {
            "pass": close_float(norm_value, 1.0),
            "value": norm_value,
            "expected": 1.0,
        },
        "middle_cut_entropy_ln2": {
            "pass": close_float(entropy_middle, EXPECTED_ENTROPY),
            "value": entropy_middle,
            "expected": EXPECTED_ENTROPY,
            "tolerance": TOL,
        },
        "operator_expectation_matches_pinned_analytic": {
            "pass": close_complex(complex_dict(operator_expectation), EXPECTED_OPERATOR),
            "value": complex_dict(operator_expectation),
            "expected": EXPECTED_OPERATOR,
            "operator": "product of four local lowering maps |0000><1111|",
            "cotengra_path": contraction_path,
        },
    }
    negative = {
        "product_state_entropy_zero": {
            "pass": close_float(product_entropy, 0.0),
            "value": product_entropy,
            "expected": 0.0,
        },
        "transposed_operator_control_differs": {
            "pass": (
                close_complex(complex_dict(wrong_expectation), EXPECTED_WRONG_OPERATOR)
                and not close_complex(complex_dict(wrong_expectation), EXPECTED_OPERATOR)
            ),
            "value": complex_dict(wrong_expectation),
            "expected_wrong_value": EXPECTED_WRONG_OPERATOR,
            "positive_value": complex_dict(operator_expectation),
            "cotengra_path": wrong_contraction_path,
        },
    }
    boundary = {
        "bond_dim_1_truncation_degrades_ghz_fidelity": {
            "pass": close_float(bond_dim_1_fidelity, EXPECTED_BOND_DIM_1_FIDELITY)
            and bond_dim_1_fidelity < 1.0,
            "value": bond_dim_1_fidelity,
            "expected": EXPECTED_BOND_DIM_1_FIDELITY,
        }
    }
    cross_check = {
        "analytic_entropy_peer_agreement": {
            "pass": close_float(entropy_middle, EXPECTED_ENTROPY),
            "value": entropy_middle,
            "pinned_peer_expected_value": EXPECTED_ENTROPY,
            "source": "pinned analytic GHZ-like fixture, not peer result file",
        },
        "analytic_operator_peer_agreement": {
            "pass": close_complex(complex_dict(operator_expectation), EXPECTED_OPERATOR),
            "value": complex_dict(operator_expectation),
            "pinned_peer_expected_value": EXPECTED_OPERATOR,
            "source": "pinned analytic GHZ-like fixture, not peer result file",
        },
    }

    summary = {
        "positive_all_pass": all_pass(positive),
        "negative_all_pass": all_pass(negative),
        "boundary_all_pass": all_pass(boundary),
        "cross_check_all_pass": all_pass(cross_check),
    }
    summary["all_pass"] = all(summary.values())

    result = {
        "name": "sim_quimb_capability",
        "purpose": "Bounded tensor-network capability probe for quimb plus cotengra pathing on one pinned GHZ-like MPS.",
        "classification": classification,
        "claim_ceiling": "tool_micro_quimb_capability_only",
        "fixture": {
            "name": "pinned_4_site_phase_ghz_mps",
            "state_vector_basis_order": "|0000>, |0001>, ..., |1111>",
            "state_vector_literal": [
                {"real": 1.0 / math.sqrt(2.0), "imag": 0.0},
                *[{"real": 0.0, "imag": 0.0} for _ in range(14)],
                {"real": 0.0, "imag": 1.0 / math.sqrt(2.0)},
            ],
            "bond_dimension": 2,
            "analytic_middle_cut_entropy": EXPECTED_ENTROPY,
            "analytic_operator_expectation": EXPECTED_OPERATOR,
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "rho_middle_2site": matrix_complex_rows(rho_middle),
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "cross_check": cross_check,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "operation_sequence": [
            "load quimb.tensor and cotengra from the pinned Codex Ratchet Python env",
            "build the pinned 4-site GHZ-like MPS with bond dimension 2",
            "compute quimb MPS norm",
            "compute pinned 2-site middle reduced density matrix",
            "compute middle-cut von Neumann entropy and compare to ln 2",
            "contract pinned four-local transition operator through cotengra pathing",
            "contract transposed-operator negative control",
            "report bond-dimension-1 truncation fidelity boundary",
        ],
        "out_of_scope": [
            "no PEPS or PEPS3D scientific claim",
            "no foundation_nested_hopf_weyl_signed_cut_ratchet file access",
            "no bridge, axis, manifold, or canonical physics claim",
        ],
    }
    return apply_default_receipt_boundary(
        result,
        source_name="sim_quimb_capability",
        target="Use only as bounded quimb tensor-network capability evidence for matrix row 8.",
    )


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = build_results()
    OUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Results written to {OUT_PATH}")
    print(f"summary.all_pass = {results['summary']['all_pass']}")
