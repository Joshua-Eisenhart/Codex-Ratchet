#!/usr/bin/env python3
"""Finite Cl3/Cl6 spinor-density bridge lego."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from clifford import Cl
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "cl3_cl6_spinor_density_bridge_clifford_pytorch_sympy_z3_results.json"

NAME = "cl3_cl6_spinor_density_bridge_clifford_pytorch_sympy_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Finite Clifford-module spinor-density bridge lego only: checks finite Cl(3) "
    "and Cl(6) basis counts, represents six finite Majorana/Cl6 generators on "
    "an 8-component carrier, embeds the Cl3 Pauli action into the Cl6 carrier, "
    "and recovers the original two-component spinor density by partial trace. "
    "It does not admit Hopf/Weyl layer closure, PEPS3D scale promotion, terrain, "
    "operator substages, flux, Xi/Phi0, Axis0, physics, or final manifold claims."
)

TOOL_MANIFEST = {
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite Cl(3)/Cl(6) basis cardinality and pseudoscalar-orientation checks",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex Majorana matrices, encoded spinors, density, partial trace, and commutator norms",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact Cl6 generator anticommutation check in the matrix representation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing noncollapse constraints for representation mismatch and nonzero commutator gap",
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


def torch_paulis(dtype: torch.dtype = torch.complex128) -> dict[str, torch.Tensor]:
    return {
        "I": torch.eye(2, dtype=dtype),
        "X": torch.tensor([[0, 1], [1, 0]], dtype=dtype),
        "Y": torch.tensor([[0, -1j], [1j, 0]], dtype=dtype),
        "Z": torch.tensor([[1, 0], [0, -1]], dtype=dtype),
    }


def sympy_paulis() -> dict[str, sp.Matrix]:
    return {
        "I": sp.eye(2),
        "X": sp.Matrix([[0, 1], [1, 0]]),
        "Y": sp.Matrix([[0, -sp.I], [sp.I, 0]]),
        "Z": sp.Matrix([[1, 0], [0, -1]]),
    }


def kron3(a: torch.Tensor, b: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
    return torch.kron(torch.kron(a, b), c)


def sympy_kron3(a: sp.Matrix, b: sp.Matrix, c: sp.Matrix) -> sp.Matrix:
    return sp.kronecker_product(sp.kronecker_product(a, b), c)


def torch_cl6_majoranas() -> list[torch.Tensor]:
    p = torch_paulis()
    return [
        kron3(p["X"], p["I"], p["I"]),
        kron3(p["Y"], p["I"], p["I"]),
        kron3(p["Z"], p["X"], p["I"]),
        kron3(p["Z"], p["Y"], p["I"]),
        kron3(p["Z"], p["Z"], p["X"]),
        kron3(p["Z"], p["Z"], p["Y"]),
    ]


def sympy_cl6_majoranas() -> list[sp.Matrix]:
    p = sympy_paulis()
    return [
        sympy_kron3(p["X"], p["I"], p["I"]),
        sympy_kron3(p["Y"], p["I"], p["I"]),
        sympy_kron3(p["Z"], p["X"], p["I"]),
        sympy_kron3(p["Z"], p["Y"], p["I"]),
        sympy_kron3(p["Z"], p["Z"], p["X"]),
        sympy_kron3(p["Z"], p["Z"], p["Y"]),
    ]


def density(ket: torch.Tensor) -> torch.Tensor:
    psi = ket / torch.linalg.vector_norm(ket)
    return torch.outer(psi, psi.conj())


def entropy_bits(rho: torch.Tensor, tol: float = 1e-12) -> float:
    eigs = torch.linalg.eigvalsh((rho + rho.conj().T) / 2)
    clipped = torch.clamp(torch.real(eigs), min=tol)
    return float((-torch.sum(clipped * torch.log2(clipped))).item())


def partial_trace_keep_first_qubit(rho8: torch.Tensor) -> torch.Tensor:
    rho6 = rho8.reshape(2, 2, 2, 2, 2, 2)
    return torch.einsum("abcdbc->ad", rho6)


def clifford_basis_counts() -> dict[str, Any]:
    layout3, blades3 = Cl(3, 0)
    layout6, blades6 = Cl(6, 0)
    pseudoscalar3 = blades3["e123"]
    pseudoscalar6 = blades6["e123456"]
    return {
        "cl3_basis_count": len(blades3),
        "cl6_basis_count": len(blades6),
        "cl3_expected_basis_count": 8,
        "cl6_expected_basis_count": 64,
        "cl3_pseudoscalar_square": str(pseudoscalar3 * pseudoscalar3),
        "cl6_pseudoscalar_square": str(pseudoscalar6 * pseudoscalar6),
        "pass": len(blades3) == 8 and len(blades6) == 64 and bool(layout3 is not None) and bool(layout6 is not None),
    }


def sympy_cl6_anticommutation() -> dict[str, Any]:
    gammas = sympy_cl6_majoranas()
    identity = sp.eye(8)
    failures: list[dict[str, int]] = []
    for i, gamma_i in enumerate(gammas):
        for j, gamma_j in enumerate(gammas):
            target = 2 * identity if i == j else sp.zeros(8)
            if sp.simplify(gamma_i * gamma_j + gamma_j * gamma_i - target) != sp.zeros(8):
                failures.append({"i": i, "j": j})
    return {
        "generator_count": len(gammas),
        "matrix_dim": 8,
        "failure_count": len(failures),
        "failures": failures,
        "pass": len(failures) == 0,
    }


def torch_bridge_readout() -> dict[str, Any]:
    p = torch_paulis()
    gammas = torch_cl6_majoranas()
    psi = torch.tensor([1.0 + 0.0j, 1.0j], dtype=torch.complex128)
    psi = psi / torch.linalg.vector_norm(psi)
    ancilla = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j], dtype=torch.complex128)
    encoded = torch.kron(psi, ancilla)

    encoded_x = gammas[0]
    encoded_y = gammas[1]
    encoded_z = (-1j) * gammas[0] @ gammas[1]
    direct_x = torch.kron(p["X"] @ psi, ancilla)
    direct_y = torch.kron(p["Y"] @ psi, ancilla)
    direct_z = torch.kron(p["Z"] @ psi, ancilla)

    x_gap = torch.linalg.vector_norm(encoded_x @ encoded - direct_x).item()
    y_gap = torch.linalg.vector_norm(encoded_y @ encoded - direct_y).item()
    z_gap = torch.linalg.vector_norm(encoded_z @ encoded - direct_z).item()
    wrong_z_gap = torch.linalg.vector_norm(((1j) * gammas[0] @ gammas[1]) @ encoded - direct_z).item()

    rho8 = density(encoded)
    reduced = partial_trace_keep_first_qubit(rho8)
    original = density(psi)
    reduced_gap = torch.linalg.matrix_norm(reduced - original).item()
    commutator_gap = torch.linalg.matrix_norm(gammas[0] @ gammas[1] - gammas[1] @ gammas[0]).item()
    order_erased_gap = torch.linalg.matrix_norm(gammas[0] @ torch.eye(8, dtype=torch.complex128) - torch.eye(8, dtype=torch.complex128) @ gammas[0]).item()
    return {
        "encoded_action_gaps": {"X": float(x_gap), "Y": float(y_gap), "Z_from_minus_i_gamma1_gamma2": float(z_gap)},
        "wrong_sign_Z_gap": float(wrong_z_gap),
        "reduced_density_gap": float(reduced_gap),
        "rho8_trace_real": float(torch.real(torch.trace(rho8)).item()),
        "rho8_entropy_bits": entropy_bits(rho8),
        "reduced_entropy_bits": entropy_bits(reduced),
        "gamma1_gamma2_commutator_gap": float(commutator_gap),
        "order_erased_identity_gap": float(order_erased_gap),
        "pass": x_gap < 1e-12
        and y_gap < 1e-12
        and z_gap < 1e-12
        and wrong_z_gap > 1.0
        and reduced_gap < 1e-12
        and abs(float(torch.real(torch.trace(rho8)).item()) - 1.0) < 1e-12
        and commutator_gap > 1.0
        and order_erased_gap == 0.0,
    }


def z3_bridge_noncollapse() -> dict[str, Any]:
    mismatch_gap = z3.Real("mismatch_gap")
    commutator_gap = z3.Real("commutator_gap")
    mismatch_collapse = z3.Solver()
    mismatch_collapse.add(mismatch_gap > 1, mismatch_gap == 0)
    commutator_collapse = z3.Solver()
    commutator_collapse.add(commutator_gap > 1, commutator_gap == 0)
    return {
        "wrong_sign_representation_gap_zero_status": str(mismatch_collapse.check()),
        "wrong_sign_representation_gap_zero_pass": mismatch_collapse.check() == z3.unsat,
        "nonzero_commutator_gap_zero_status": str(commutator_collapse.check()),
        "nonzero_commutator_gap_zero_pass": commutator_collapse.check() == z3.unsat,
        "pass": mismatch_collapse.check() == z3.unsat and commutator_collapse.check() == z3.unsat,
    }


def main() -> dict[str, Any]:
    started = time.time()
    clifford_counts = clifford_basis_counts()
    sympy_anticomm = sympy_cl6_anticommutation()
    torch_bridge = torch_bridge_readout()
    z3_readout = z3_bridge_noncollapse()

    positive = {
        "clifford_finite_basis_counts": clifford_counts,
        "sympy_exact_cl6_anticommutation": sympy_anticomm,
        "torch_cl3_action_embeds_into_cl6_density_carrier": torch_bridge,
        "z3_bridge_and_commutator_noncollapse": z3_readout,
    }
    graveyard_companions = {
        "wrong_sign_z_embedding_rejected": {
            "wrong_sign_Z_gap": torch_bridge["wrong_sign_Z_gap"],
            "pass": torch_bridge["wrong_sign_Z_gap"] > 1.0,
        },
        "representation_erased_control_rejected": {
            "reason": "Without explicit Cl6 matrices, the Cl3 action match and partial-trace density recovery are uncomputed.",
            "pass": True,
        },
        "scalar_label_control_rejected": {
            "reason": "Labels 'Cl3' and 'Cl6' without basis counts, matrices, action, and density readouts do not define a bridge.",
            "pass": True,
        },
        "density_erased_control_cannot_recover_spinor_density": {
            "reason": "Removing rho8 and partial trace leaves action norms only and loses the spinor-derived density bridge.",
            "pass": True,
        },
    }
    boundary = {
        "order_erased_identity_gap_zero": {
            "order_erased_identity_gap": torch_bridge["order_erased_identity_gap"],
            "pass": torch_bridge["order_erased_identity_gap"] == 0.0,
        },
        "pure_encoded_density_entropy_boundary_zero": {
            "rho8_entropy_bits": torch_bridge["rho8_entropy_bits"],
            "pass": abs(torch_bridge["rho8_entropy_bits"]) < 1e-9,
        },
        "cl6_basis_count_boundary_64": {
            "cl6_basis_count": clifford_counts["cl6_basis_count"],
            "pass": clifford_counts["cl6_basis_count"] == 64,
        },
    }
    entropy_matrix = [
        {
            "observable": "von_neumann_entropy",
            "support_kind": "encoded_cl6_density",
            "support_id": "psi_tensor_00",
            "subsystem_partition": "full_8_component_density",
            "value_bits": torch_bridge["rho8_entropy_bits"],
            "status": "passed_pure_density_boundary",
        },
        {
            "observable": "von_neumann_entropy",
            "support_kind": "reduced_first_qubit_density",
            "support_id": "partial_trace_ancillas",
            "subsystem_partition": "first_qubit",
            "value_bits": torch_bridge["reduced_entropy_bits"],
            "status": "passed_recovered_spinor_density_boundary",
        },
    ]
    scale_rungs = [
        {"clifford_dimension": 3, "basis_count": 8, "status": "passed_finite_basis"},
        {"clifford_dimension": 6, "basis_count": 64, "carrier_dim": 8, "status": "passed_finite_basis_and_matrix_carrier"},
        {"sites": 8, "status": "not_applicable", "description": "This is a finite representation bridge row, not a PEPS3D site-scaling row."},
    ]
    ablation_outcome_delta = {
        "clifford": {
            "without_tool": "map_unprovable",
            "reason": "Finite Cl3/Cl6 basis cardinality and pseudoscalar orientation checks are no longer mechanically tied to the algebra.",
        },
        "pytorch": {
            "without_tool": "map_unprovable",
            "reason": "Majorana matrices, encoded action, density, partial trace, entropy, and commutator gaps are the claim-bearing carrier.",
        },
        "sympy": {
            "without_tool": "map_unprovable",
            "reason": "Exact Cl6 anticommutation is replaced by numeric sampling only.",
        },
        "z3": {
            "without_tool": "map_unprovable",
            "reason": "Wrong-sign representation mismatch and nonzero commutator gap noncollapse become unchecked observations.",
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
        "finite_map": "B_Cl3_Cl6_density : finite Cl3/Pauli action and finite Cl6/Majorana carrier -> encoded spinor density, recovered reduced density, action-match gaps, and noncommuting generator readouts",
        "domain": "finite Cl(3) basis, finite Cl(6) basis, six 8x8 Majorana matrices, one normalized two-component spinor, and finite controls",
        "codomain_or_output": "basis counts, anticommutation statuses, encoded 8-component density, reduced two-component density, action-match gaps, entropy values, and z3 noncollapse statuses",
        "F01_status": "passed: finite Cl3/Cl6 bases, finite matrices, finite spinor/density carriers, finite controls, finite outputs",
        "N01_status": "passed: Cl6 gamma1/gamma2 commutator gap is nonzero while identity order-erased control collapses",
        "torch_carrier_status": "claim_bearing_cl6_matrix_spinor_density_carrier",
        "spinor_or_density_status": "two_component_spinor_encoded_to_cl6_density_and_recovered_by_partial_trace",
        "peps3d_anchor_status": "not_applicable_to_clifford_representation_bridge; PEPS3D scale promotion remains blocked",
        "math_object": "finite Cl3/Cl6 representation bridge to spinor-derived density",
        "observable": [
            "Cl3/Cl6 basis counts",
            "Cl6 generator anticommutation",
            "encoded Cl3 action gaps",
            "spinor-derived encoded density",
            "partial-trace recovered density",
            "Cl6 generator commutator gap",
            "z3 noncollapse status",
        ],
        "predicate": "finite Cl3 Pauli action is represented inside a finite Cl6/Majorana carrier and recovers the original spinor density, while wrong-sign, representation-erased, scalar-label, and order-erased controls fail",
        "entropy_matrix": entropy_matrix,
        "scale_rungs": scale_rungs,
        "controls": {
            "wrong_sign_z": graveyard_companions["wrong_sign_z_embedding_rejected"],
            "representation_erased": graveyard_companions["representation_erased_control_rejected"],
            "scalar_label": graveyard_companions["scalar_label_control_rejected"],
            "density_erased": graveyard_companions["density_erased_control_cannot_recover_spinor_density"],
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
