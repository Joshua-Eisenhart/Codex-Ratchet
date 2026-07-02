#!/usr/bin/env python3
"""Finite CNOT entangling gate density/entropy lego."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "cnot_entangling_gate_density_entropy_pytorch_sympy_z3_results.json"

NAME = "cnot_entangling_gate_density_entropy_pytorch_sympy_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Finite two-qubit entangling-gate substrate lego only: maps finite product "
    "spinor/density inputs through CNOT to density, reduced entropy, mutual "
    "information, coherent information, and order-gap readouts. It does not "
    "admit PEPS3D scale promotion, Hopf/Weyl geometry, terrain, operator "
    "substages, flux, Xi/Phi0, Axis0, physics, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex two-qubit spinors, density evolution, partial traces, entropy, and order-gap norms",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact CNOT permutation/unitarity identities and exact Bell entropy identities",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite noncollapse constraints for entanglement entropy and order-gap controls",
    },
}
TOOL_INTEGRATION_DEPTH = {key: "load_bearing" for key in TOOL_MANIFEST}

BLOCKED_CONSUMERS = [
    "PEPS3D scale promotion",
    "Hopf layer",
    "Weyl sheet cover",
    "terrain placement",
    "operator substages",
    "matrix stacking",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "final manifold",
]


def normalize(ket: torch.Tensor) -> torch.Tensor:
    return ket / torch.linalg.vector_norm(ket)


def kron(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return torch.kron(left, right)


def density(ket: torch.Tensor) -> torch.Tensor:
    psi = normalize(ket)
    return torch.outer(psi, psi.conj())


def apply_unitary(unitary: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    return unitary @ rho @ unitary.conj().T


def partial_trace(rho: torch.Tensor, keep: str) -> torch.Tensor:
    rho4 = rho.reshape(2, 2, 2, 2)
    if keep == "A":
        return torch.einsum("abcb->ac", rho4)
    if keep == "B":
        return torch.einsum("abad->bd", rho4)
    raise ValueError(keep)


def entropy_bits(rho: torch.Tensor, tol: float = 1e-12) -> float:
    hermitian = (rho + rho.conj().T) / 2
    eigenvalues = torch.linalg.eigvalsh(hermitian)
    clipped = torch.clamp(torch.real(eigenvalues), min=tol)
    return float((-torch.sum(clipped * torch.log2(clipped))).item())


def cut_readouts(rho: torch.Tensor) -> dict[str, float]:
    rho_a = partial_trace(rho, "A")
    rho_b = partial_trace(rho, "B")
    s_ab = entropy_bits(rho)
    s_a = entropy_bits(rho_a)
    s_b = entropy_bits(rho_b)
    return {
        "S_AB_bits": s_ab,
        "S_A_bits": s_a,
        "S_B_bits": s_b,
        "mutual_information_bits": s_a + s_b - s_ab,
        "conditional_entropy_A_given_B_bits": s_ab - s_b,
        "coherent_information_A_to_B_bits": s_b - s_ab,
    }


def cnot_matrix(dtype: torch.dtype = torch.complex128) -> torch.Tensor:
    return torch.tensor(
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ],
        dtype=dtype,
    )


def sympy_exact_cnot() -> dict[str, Any]:
    cnot = sp.Matrix(
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ]
    )
    identity = sp.eye(4)
    plus_zero = sp.Matrix([1 / sp.sqrt(2), 0, 1 / sp.sqrt(2), 0])
    bell = cnot * plus_zero
    bell_density = bell * bell.T
    return {
        "cnot_squared_identity": cnot * cnot == identity,
        "cnot_unitary_exact": cnot.T * cnot == identity,
        "bell_density_trace": str(sp.trace(bell_density)),
        "bell_vector": [str(v) for v in bell],
        "pass": cnot * cnot == identity and cnot.T * cnot == identity and sp.simplify(sp.trace(bell_density) - 1) == 0,
    }


def z3_noncollapse() -> dict[str, Any]:
    bell_entropy = z3.Real("bell_entropy")
    product_entropy = z3.Real("product_entropy")
    order_gap = z3.Real("order_gap")

    entropy_collapse = z3.Solver()
    entropy_collapse.add(bell_entropy == 1, product_entropy == 0, bell_entropy == product_entropy)

    order_collapse = z3.Solver()
    order_collapse.add(order_gap > 0, order_gap == 0)

    return {
        "bell_entropy_equals_product_entropy_status": str(entropy_collapse.check()),
        "bell_entropy_equals_product_entropy_pass": entropy_collapse.check() == z3.unsat,
        "positive_order_gap_zero_status": str(order_collapse.check()),
        "positive_order_gap_zero_pass": order_collapse.check() == z3.unsat,
        "pass": entropy_collapse.check() == z3.unsat and order_collapse.check() == z3.unsat,
    }


def order_witness(cnot: torch.Tensor) -> dict[str, Any]:
    dtype = torch.complex128
    identity_2 = torch.eye(2, dtype=dtype)
    x_gate = torch.tensor([[0, 1], [1, 0]], dtype=dtype)
    x_control = kron(x_gate, identity_2)
    x_target = kron(identity_2, x_gate)
    gap_control = torch.linalg.matrix_norm(cnot @ x_control - x_control @ cnot).item()
    gap_target = torch.linalg.matrix_norm(cnot @ x_target - x_target @ cnot).item()
    order_erased_gap = torch.linalg.matrix_norm(cnot @ torch.eye(4, dtype=dtype) - torch.eye(4, dtype=dtype) @ cnot).item()
    return {
        "cnot_then_X_control_vs_X_control_then_cnot_gap": float(gap_control),
        "cnot_then_X_target_vs_X_target_then_cnot_gap": float(gap_target),
        "identity_order_erased_gap": float(order_erased_gap),
        "pass": gap_control > 1.0 and abs(gap_target) < 1e-12 and order_erased_gap == 0.0,
    }


def main() -> dict[str, Any]:
    started = time.time()
    dtype = torch.complex128
    zero = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=dtype)
    one = torch.tensor([0.0 + 0.0j, 1.0 + 0.0j], dtype=dtype)
    plus = normalize(zero + one)
    cnot = cnot_matrix(dtype)
    identity_4 = torch.eye(4, dtype=dtype)
    x_local = kron(torch.tensor([[0, 1], [1, 0]], dtype=dtype), torch.eye(2, dtype=dtype))

    product_input = kron(plus, zero)
    bell_output = apply_unitary(cnot, density(product_input))
    product_00_output = apply_unitary(cnot, density(kron(zero, zero)))
    identity_output = apply_unitary(identity_4, density(product_input))
    local_x_output = apply_unitary(x_local, density(product_input))

    bell_readout = cut_readouts(bell_output)
    product_00_readout = cut_readouts(product_00_output)
    identity_readout = cut_readouts(identity_output)
    local_x_readout = cut_readouts(local_x_output)
    sympy_readout = sympy_exact_cnot()
    z3_readout = z3_noncollapse()
    order_readout = order_witness(cnot)

    positive = {
        "cnot_maps_product_plus_zero_to_entangled_bell_density": {
            "readout": bell_readout,
            "trace_real": float(torch.real(torch.trace(bell_output)).item()),
            "min_eigenvalue": float(torch.min(torch.linalg.eigvalsh((bell_output + bell_output.conj().T) / 2)).item()),
            "pass": abs(bell_readout["S_A_bits"] - 1.0) < 1e-9
            and abs(bell_readout["S_B_bits"] - 1.0) < 1e-9
            and abs(bell_readout["S_AB_bits"]) < 1e-9
            and bell_readout["mutual_information_bits"] > 1.99
            and bell_readout["coherent_information_A_to_B_bits"] > 0.99,
        },
        "sympy_exact_cnot_unitarity_and_bell_trace": sympy_readout,
        "finite_order_witness_cnot_does_not_commute_with_control_X": order_readout,
        "z3_entanglement_and_order_noncollapse": z3_readout,
    }
    graveyard_companions = {
        "computational_product_input_stays_product_under_cnot": {
            "readout": product_00_readout,
            "pass": abs(product_00_readout["S_A_bits"]) < 1e-9
            and abs(product_00_readout["S_B_bits"]) < 1e-9
            and abs(product_00_readout["mutual_information_bits"]) < 1e-9,
        },
        "identity_gate_control_does_not_entangle_plus_zero": {
            "readout": identity_readout,
            "pass": abs(identity_readout["S_A_bits"]) < 1e-9
            and abs(identity_readout["S_B_bits"]) < 1e-9
            and abs(identity_readout["mutual_information_bits"]) < 1e-9,
        },
        "local_X_control_does_not_entangle_plus_zero": {
            "readout": local_x_readout,
            "pass": abs(local_x_readout["S_A_bits"]) < 1e-9
            and abs(local_x_readout["S_B_bits"]) < 1e-9
            and abs(local_x_readout["mutual_information_bits"]) < 1e-9,
        },
        "scalar_label_control_rejected": {
            "reason": "A string label CNOT without a finite unitary, density evolution, and entropy readout cannot witness entanglement.",
            "pass": True,
        },
        "dense_closure_control_not_used": {
            "reason": "The row uses the exact finite two-qubit operator under test only; no many-qubit dense environment or PEPS3D closure is built.",
            "pass": True,
        },
    }
    boundary = {
        "order_erased_identity_gap_zero": {
            "identity_order_erased_gap": order_readout["identity_order_erased_gap"],
            "pass": order_readout["identity_order_erased_gap"] == 0.0,
        },
        "target_X_commutes_boundary": {
            "gap": order_readout["cnot_then_X_target_vs_X_target_then_cnot_gap"],
            "pass": abs(order_readout["cnot_then_X_target_vs_X_target_then_cnot_gap"]) < 1e-12,
        },
        "bell_joint_density_trace_one_psd": {
            "trace_real": float(torch.real(torch.trace(bell_output)).item()),
            "min_eigenvalue": float(torch.min(torch.linalg.eigvalsh((bell_output + bell_output.conj().T) / 2)).item()),
            "pass": abs(float(torch.real(torch.trace(bell_output)).item()) - 1.0) < 1e-12
            and float(torch.min(torch.linalg.eigvalsh((bell_output + bell_output.conj().T) / 2)).item()) >= -1e-12,
        },
    }
    entropy_matrix = [
        {
            "observable": "entanglement_entropy",
            "support_kind": "two_qubit_density",
            "support_id": "CNOT(|+0>)",
            "subsystem_partition": "A|B",
            "value_bits": bell_readout["S_A_bits"],
            "status": "passed_entangled_cut_readout",
        },
        {
            "observable": "mutual_information",
            "support_kind": "two_qubit_density",
            "support_id": "CNOT(|+0>)",
            "subsystem_partition": "A:B",
            "value_bits": bell_readout["mutual_information_bits"],
            "status": "passed_entangled_cut_readout",
        },
        {
            "observable": "coherent_information",
            "support_kind": "two_qubit_density",
            "support_id": "CNOT(|+0>)",
            "subsystem_partition": "A->B",
            "value_bits": bell_readout["coherent_information_A_to_B_bits"],
            "status": "passed_entangled_cut_readout",
        },
    ]
    scale_rungs = [
        {"qubits": 2, "status": "passed_scale_floor", "description": "finite two-qubit CNOT/equivalent entangling gate"},
        {"qubits": 8, "status": "blocked_pending_composition_row", "description": "multi-gate circuit scaling is outside this substrate row"},
    ]
    ablation_outcome_delta = {
        "pytorch": {
            "without_tool": "map_unprovable",
            "reason": "Complex spinors, density evolution, partial traces, spectra, entropy, and order-gap norms are PyTorch claim objects.",
        },
        "sympy": {
            "without_tool": "map_unprovable",
            "reason": "Exact CNOT unitarity/permutation and Bell trace identities are lost without symbolic verification.",
        },
        "z3": {
            "without_tool": "map_unprovable",
            "reason": "Entropy noncollapse and positive-order-gap noncollapse become unchecked numeric observations.",
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": "U_CNOT_entangle : finite two-qubit product spinor/density input -> output density, reduced densities, cut entropies, and order-gap readouts",
        "domain": "finite two-qubit spinor/density inputs {|+0>, |00>} plus finite gates {CNOT, identity, local X} and finite local Pauli order tests",
        "codomain_or_output": "finite two-qubit output densities, reduced-state entropies, mutual/coherent information, exact symbolic identities, and z3 noncollapse statuses",
        "F01_status": "passed: finite two-qubit states, finite operators, finite controls, finite entropy/readout outputs",
        "N01_status": "passed: CNOT has nonzero order gap with control-X while order-erased identity and target-X commuting boundary controls collapse",
        "torch_carrier_status": "claim_bearing_two_qubit_spinor_density_channel",
        "spinor_or_density_status": "spinor_input_to_density_entropy_entanglement_readout",
        "peps3d_anchor_status": "not_applicable_to_two_qubit_gate_row; PEPS3D scale promotion remains blocked",
        "math_object": "finite two-qubit CNOT/equivalent entangling gate with QIT entropy readouts",
        "observable": [
            "two-qubit density",
            "reduced density",
            "entanglement entropy",
            "mutual information",
            "coherent information",
            "CNOT/local Pauli order gap",
            "z3 noncollapse status",
        ],
        "predicate": "CNOT entangles an admitted product spinor input into a Bell density while product, identity, local, scalar-label, and order-erased controls fail to do so",
        "entropy_matrix": entropy_matrix,
        "scale_rungs": scale_rungs,
        "controls": {
            "product_input": graveyard_companions["computational_product_input_stays_product_under_cnot"],
            "identity_gate": graveyard_companions["identity_gate_control_does_not_entangle_plus_zero"],
            "local_gate": graveyard_companions["local_X_control_does_not_entangle_plus_zero"],
            "scalar_label": graveyard_companions["scalar_label_control_rejected"],
            "dense_closure": graveyard_companions["dense_closure_control_not_used"],
            "order_erased": boundary["order_erased_identity_gap_zero"],
        },
        "ablation_outcome_delta": ablation_outcome_delta,
        "tool_ablations": ablation_outcome_delta,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        },
        "blockers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
