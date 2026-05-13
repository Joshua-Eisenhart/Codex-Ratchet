#!/usr/bin/env python3
"""Tool-capability isolation sim for Qiskit.

This proves only a tiny Qiskit API surface: construct a circuit, obtain a
statevector/density matrix, and compare an operator expectation against the
known one-qubit answer. It is not a QIT, bridge, axis, or engine admission.
"""

from __future__ import annotations

import json
import os

import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix, Operator, Statevector

from receipt_boundary import apply_default_receipt_boundary


classification = "canonical"
divergence_log = (
    "Capability isolation witness for qiskit: one-qubit circuit, statevector, "
    "density-matrix, and operator-expectation surfaces are exercised so later "
    "bounded bridge sims can treat qiskit as an available quantum-circuit tool. "
    "No QIT, GStack, axis, bridge, or engine claim is admitted here."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not used: this Qiskit capability fixture does not require tensor autodiff, torch modules, or tensor-kernel execution."},
    "pyg": {"tried": False, "used": False, "reason": "not used: no graph carrier, edge index, message passing, batching, or graph pooling surface is exercised."},
    "z3": {"tried": False, "used": False, "reason": "not used: no SMT satisfiability, model extraction, or symbolic constraint admissibility query is part of this fixture."},
    "cvc5": {"tried": False, "used": False, "reason": "not used: no cvc5 formula assertion, SAT check, value extraction, or SyGuS synthesis surface is needed."},
    "sympy": {"tried": False, "used": False, "reason": "not used: no symbolic simplification, polynomial algebra, or exact matrix identity proof is exercised here."},
    "clifford": {"tried": False, "used": False, "reason": "not used: this probe checks circuit and density APIs rather than Clifford multivector algebra."},
    "geomstats": {"tried": False, "used": False, "reason": "not used: no manifold metric, geodesic, or Lie group geometry API is part of this one-qubit fixture."},
    "e3nn": {"tried": False, "used": False, "reason": "not used: no equivariant neural network, irreducible representation tensor, or learned layer is exercised."},
    "rustworkx": {"tried": False, "used": False, "reason": "not used: no graph traversal, DAG, shortest path, or dependency graph structure is involved."},
    "xgi": {"tried": False, "used": False, "reason": "not used: no hypergraph incidence, hyperedge membership, or higher-order relation is represented."},
    "toponetx": {"tried": False, "used": False, "reason": "not used: no cell complex, simplicial complex, Hasse graph, or incidence-matrix API is exercised."},
    "gudhi": {"tried": False, "used": False, "reason": "not used: no persistent homology, simplex tree, filtration, or Betti-number computation is needed."},
    "numpy": {"tried": True, "used": True, "reason": "supportive numeric tolerances, trace checks, norms, and reference arrays for Qiskit state data"},
    "qiskit": {
        "tried": True,
        "used": True,
        "reason": "capability under test -- circuit, statevector, density matrix, operator expectation",
    },
}

TOOL_INTEGRATION_DEPTH = {
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
    "numpy": "supportive",
    "qiskit": "load_bearing",
}


def _all_pass(section: dict[str, dict[str, object]]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def _json_default(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, complex):
        return {"real": obj.real, "imag": obj.imag}
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def run_positive_tests() -> dict[str, dict[str, object]]:
    qc = QuantumCircuit(1)
    qc.h(0)
    state = Statevector.from_instruction(qc)
    density = DensityMatrix(state)
    z = Operator([[1, 0], [0, -1]])
    x = Operator([[0, 1], [1, 0]])
    return {
        "statevector_plus_state": {
            "pass": np.allclose(state.data, np.array([1.0, 1.0]) / np.sqrt(2.0)),
            "statevector": state.data,
        },
        "density_trace_one": {
            "pass": abs(np.trace(density.data) - 1.0) < 1e-12,
            "trace": np.trace(density.data),
        },
        "plus_has_x_expectation_one": {
            "pass": abs(state.expectation_value(x) - 1.0) < 1e-12,
            "value": state.expectation_value(x),
        },
        "plus_has_z_expectation_zero": {
            "pass": abs(state.expectation_value(z)) < 1e-12,
            "value": state.expectation_value(z),
        },
    }


def run_negative_tests() -> dict[str, dict[str, object]]:
    qc = QuantumCircuit(1)
    qc.x(0)
    state = Statevector.from_instruction(qc)
    plus = np.array([1.0, 1.0]) / np.sqrt(2.0)
    return {
        "bit_flip_is_not_plus_state": {
            "pass": not np.allclose(state.data, plus),
            "statevector": state.data,
        }
    }


def run_boundary_tests() -> dict[str, dict[str, object]]:
    qc = QuantumCircuit(1)
    theta = 1e-8
    qc.ry(theta, 0)
    state = Statevector.from_instruction(qc)
    density = DensityMatrix(state)
    purity = np.trace(density.data @ density.data)
    return {
        "small_rotation_remains_normalized": {
            "pass": abs(np.linalg.norm(state.data) - 1.0) < 1e-12,
            "norm": float(np.linalg.norm(state.data)),
        },
        "pure_density_purity_stable": {
            "pass": abs(purity - 1.0) < 1e-12,
            "purity": purity,
        },
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
        "name": "sim_qiskit_capability",
        "classification": classification,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "qiskit_version": getattr(qiskit, "__version__", None),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "claim_ceiling": "tool_micro_qiskit_capability_only",
        "operation_sequence": [
            "construct a one-qubit QuantumCircuit",
            "apply a Hadamard gate to prepare the plus state",
            "derive a Statevector from the circuit instruction",
            "convert the statevector to a DensityMatrix",
            "evaluate X and Z Operator expectation values on the statevector",
            "run adjacent negative and boundary fixtures for a bit-flip state, a small rotation, normalization, and purity",
        ],
        "carrier_topology": {
            "carrier": "one-qubit complex Hilbert space with 2x2 density matrix representation",
            "positive_fixture": "Hadamard-prepared plus state",
            "graveyard_fixture": "bit-flipped computational basis state compared against plus-state amplitudes",
            "boundary_fixture": "small-angle Ry rotation with statevector norm and density purity checks",
        },
        "observable": {
            "primary": "statevector amplitudes and one-qubit operator expectation values",
            "secondary": [
                "density trace",
                "statevector norm",
                "density-matrix purity",
            ],
        },
        "pass_fail_predicate": {
            "pass": [
                "Hadamard circuit statevector equals the plus state within tolerance",
                "derived density matrix has trace 1",
                "plus state has X expectation 1",
                "plus state has Z expectation 0",
                "bit-flipped basis state is not equal to the plus state",
                "small Ry rotation remains normalized",
                "pure-state density matrix has purity 1",
            ],
            "fail": [
                "Qiskit circuit construction or state conversion fails",
                "statevector, density trace, expectation, normalization, or purity checks miss tolerance",
                "negative bit-flip fixture is indistinguishable from the plus state",
            ],
        },
        "graveyards": [
            {
                "name": "bit_flip_basis_state",
                "change": "replace the Hadamard preparation with an X gate on |0>",
                "expected_death": "amplitude equality with the plus state fails",
            }
        ],
        "baselines": [
            {
                "name": "small_rotation_normalization_boundary",
                "role": "near-identity one-qubit rotation baseline for norm and purity preservation",
            }
        ],
        "alternative_formulations": [
            "manual numpy one-qubit matrix multiplication for the same Hadamard and Pauli expectation checks",
            "qiskit Operator expectation evaluated through density-matrix trace rather than Statevector.expectation_value",
            "two-qubit separable extension with tensor-product density checks",
        ],
        "tool_function_needs": [
            {
                "tool": "qiskit",
                "functions": [
                    "QuantumCircuit",
                    "QuantumCircuit.h",
                    "QuantumCircuit.x",
                    "QuantumCircuit.ry",
                    "Statevector.from_instruction",
                    "DensityMatrix",
                    "Operator",
                    "Statevector.expectation_value",
                ],
                "depth": "load_bearing",
            },
            {
                "tool": "numpy",
                "functions": [
                    "np.allclose",
                    "np.sqrt",
                    "np.trace",
                    "np.linalg.norm",
                ],
                "depth": "supportive",
            },
        ],
        "lego_coupling_target": [
            "unitary_channel_map",
            "density_matrix_object",
        ],
        "next_lego_target": "bounded qiskit statevector-density fixture before any QIT or density-carrier lego promotion",
        "promotion_condition": (
            "requires a later admitted downstream row that names this exact Qiskit "
            "capability receipt; this micro row proves only tool availability"
        ),
        "blocked_until": (
            "blocked from QIT, GStack, axis, bridge, engine, and nonclassical promotion "
            "until a downstream target passes strict admission with this receipt as a named parent"
        ),
        "demotion_condition": (
            "Demote Qiskit for this surface if one-qubit circuit construction, "
            "statevector/density conversion, normalization, or X/Z expectation checks fail."
        ),
        "out_of_scope": [
            "no QIT admission",
            "no GStack admission",
            "no axis admission",
            "no bridge or engine claim",
            "no scientific lego coupling claim",
        ],
    }
    results = apply_default_receipt_boundary(results, source_name="sim_qiskit_capability")
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "qiskit_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
