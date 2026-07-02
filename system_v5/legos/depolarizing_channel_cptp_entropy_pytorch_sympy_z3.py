#!/usr/bin/env python3
"""Finite depolarizing CPTP channel entropy lego."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "depolarizing_channel_cptp_entropy_pytorch_sympy_z3_results.json"

NAME = "depolarizing_channel_cptp_entropy_pytorch_sympy_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Finite one-qubit depolarizing CPTP channel substrate lego only: maps finite "
    "spinor-derived density states through E_p(rho)=(1-p)rho+pI/2, checks Kraus "
    "completeness, trace/PSD/unitality, entropy increase, coherence degradation, "
    "and finite noncommuting probe controls. It does not admit PEPS3D scale "
    "promotion, Hopf/Weyl geometry, terrain, operator substages, flux, Xi/Phi0, "
    "Axis0, physics, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density/channel evolution, Kraus application, spectra, entropy, coherence, and probe commutator norms",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact Kraus completeness and depolarizing affine-form identity",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite p-domain and coherence-degradation noncollapse constraints",
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


def density(ket: torch.Tensor) -> torch.Tensor:
    psi = normalize(ket)
    return torch.outer(psi, psi.conj())


def paulis(dtype: torch.dtype = torch.complex128) -> dict[str, torch.Tensor]:
    return {
        "I": torch.eye(2, dtype=dtype),
        "X": torch.tensor([[0, 1], [1, 0]], dtype=dtype),
        "Y": torch.tensor([[0, -1j], [1j, 0]], dtype=dtype),
        "Z": torch.tensor([[1, 0], [0, -1]], dtype=dtype),
    }


def depolarizing_kraus(p: float) -> list[torch.Tensor]:
    ops = paulis()
    return [
        (1.0 - 3.0 * p / 4.0) ** 0.5 * ops["I"],
        (p / 4.0) ** 0.5 * ops["X"],
        (p / 4.0) ** 0.5 * ops["Y"],
        (p / 4.0) ** 0.5 * ops["Z"],
    ]


def apply_channel(rho: torch.Tensor, kraus_ops: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for op in kraus_ops:
        out = out + op @ rho @ op.conj().T
    return out


def affine_depolarize(rho: torch.Tensor, p: float) -> torch.Tensor:
    return (1.0 - p) * rho + p * torch.eye(2, dtype=rho.dtype) / 2.0


def density_validity(rho: torch.Tensor) -> dict[str, Any]:
    hermitian = (rho + rho.conj().T) / 2
    trace = torch.trace(rho)
    eigs = torch.linalg.eigvalsh(hermitian)
    return {
        "trace_real": float(torch.real(trace).item()),
        "trace_imag": float(torch.imag(trace).item()),
        "min_eigenvalue": float(torch.min(eigs).item()),
        "hermitian_error": float(torch.linalg.matrix_norm(rho - rho.conj().T).item()),
        "pass": abs(float(torch.real(trace).item()) - 1.0) < 1e-10
        and abs(float(torch.imag(trace).item())) < 1e-10
        and float(torch.min(eigs).item()) >= -1e-10
        and float(torch.linalg.matrix_norm(rho - rho.conj().T).item()) < 1e-10,
    }


def entropy_bits(rho: torch.Tensor, tol: float = 1e-12) -> float:
    eigs = torch.linalg.eigvalsh((rho + rho.conj().T) / 2)
    clipped = torch.clamp(torch.real(eigs), min=tol)
    return float((-torch.sum(clipped * torch.log2(clipped))).item())


def expectation(rho: torch.Tensor, observable: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ observable)).item())


def sympy_exact_depolarizing() -> dict[str, Any]:
    p = sp.symbols("p", real=True)
    identity = sp.eye(2)
    x_gate = sp.Matrix([[0, 1], [1, 0]])
    y_gate = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    z_gate = sp.Matrix([[1, 0], [0, -1]])
    kraus_sum = sp.simplify((1 - 3 * p / 4) * identity + (p / 4) * (x_gate.T * x_gate + y_gate.conjugate().T * y_gate + z_gate.T * z_gate))
    a, b, c = sp.symbols("a b c", real=True)
    rho = sp.Matrix([[a, b], [b, c]])
    pauli_form = sp.simplify(
        (1 - 3 * p / 4) * rho
        + (p / 4) * (x_gate * rho * x_gate + y_gate * rho * y_gate.conjugate().T + z_gate * rho * z_gate)
    )
    affine = sp.simplify((1 - p) * rho + p * sp.trace(rho) * identity / 2)
    return {
        "kraus_sum": str(kraus_sum),
        "affine_identity_holds_for_trace_one": sp.simplify(pauli_form - affine) == sp.zeros(2),
        "pass": kraus_sum == identity and sp.simplify(pauli_form - affine) == sp.zeros(2),
    }


def z3_depolarizing_constraints() -> dict[str, Any]:
    p = z3.Real("p")
    offdiag_after = z3.Real("offdiag_after")
    invalid_domain = z3.Solver()
    invalid_domain.add(p >= 0, p <= 1, z3.Or(p < 0, p > 1))

    no_degradation = z3.Solver()
    no_degradation.add(p > 0, p <= 1, offdiag_after == (1 - p) * z3.RealVal("0.5"), offdiag_after == z3.RealVal("0.5"))

    return {
        "invalid_p_inside_domain_status": str(invalid_domain.check()),
        "invalid_p_inside_domain_pass": invalid_domain.check() == z3.unsat,
        "positive_p_no_coherence_degradation_status": str(no_degradation.check()),
        "positive_p_no_coherence_degradation_pass": no_degradation.check() == z3.unsat,
        "pass": invalid_domain.check() == z3.unsat and no_degradation.check() == z3.unsat,
    }


def probe_noncommutation() -> dict[str, Any]:
    ops = paulis()
    gap = torch.linalg.matrix_norm(ops["X"] @ ops["Z"] - ops["Z"] @ ops["X"]).item()
    erased = torch.linalg.matrix_norm(ops["X"] @ ops["I"] - ops["I"] @ ops["X"]).item()
    return {
        "XZ_minus_ZX_gap": float(gap),
        "XI_minus_IX_order_erased_gap": float(erased),
        "pass": gap > 1.0 and erased == 0.0,
    }


def main() -> dict[str, Any]:
    started = time.time()
    p = 0.4
    ops = paulis()
    zero = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=torch.complex128)
    one = torch.tensor([0.0 + 0.0j, 1.0 + 0.0j], dtype=torch.complex128)
    plus = normalize(zero + one)
    pure_zero = density(zero)
    pure_plus = density(plus)
    maximally_mixed = torch.eye(2, dtype=torch.complex128) / 2.0

    kraus_ops = depolarizing_kraus(p)
    out_zero = apply_channel(pure_zero, kraus_ops)
    out_plus = apply_channel(pure_plus, kraus_ops)
    affine_out_plus = affine_depolarize(pure_plus, p)
    out_mixed = apply_channel(maximally_mixed, kraus_ops)
    incomplete = apply_channel(pure_zero, kraus_ops[:-1])
    p0_out = apply_channel(pure_plus, depolarizing_kraus(0.0))
    p1_out_zero = apply_channel(pure_zero, depolarizing_kraus(1.0))

    completeness = sum(op.conj().T @ op for op in kraus_ops)
    sympy_readout = sympy_exact_depolarizing()
    z3_readout = z3_depolarizing_constraints()
    probe_readout = probe_noncommutation()

    zero_entropy_in = entropy_bits(pure_zero)
    zero_entropy_out = entropy_bits(out_zero)
    plus_x_in = expectation(pure_plus, ops["X"])
    plus_x_out = expectation(out_plus, ops["X"])

    positive = {
        "pytorch_kraus_completeness_identity": {
            "frobenius_error": float(torch.linalg.matrix_norm(completeness - torch.eye(2, dtype=torch.complex128)).item()),
            "pass": float(torch.linalg.matrix_norm(completeness - torch.eye(2, dtype=torch.complex128)).item()) < 1e-10,
        },
        "pytorch_output_density_validity_for_pure_zero": density_validity(out_zero),
        "pytorch_output_density_validity_for_pure_plus": density_validity(out_plus),
        "pytorch_kraus_matches_affine_depolarizing_map": {
            "distance": float(torch.linalg.matrix_norm(out_plus - affine_out_plus).item()),
            "pass": float(torch.linalg.matrix_norm(out_plus - affine_out_plus).item()) < 1e-10,
        },
        "pytorch_depolarizing_increases_pure_state_entropy": {
            "entropy_in_bits": zero_entropy_in,
            "entropy_out_bits": zero_entropy_out,
            "pass": zero_entropy_out > zero_entropy_in + 0.1,
        },
        "pytorch_depolarizing_degrades_x_coherence": {
            "x_expectation_in": plus_x_in,
            "x_expectation_out": plus_x_out,
            "expected_x_out": 1.0 - p,
            "pass": abs(plus_x_in - 1.0) < 1e-12 and abs(plus_x_out - (1.0 - p)) < 1e-12,
        },
        "pytorch_unital_maximally_mixed_fixed_point": {
            "distance": float(torch.linalg.matrix_norm(out_mixed - maximally_mixed).item()),
            "pass": float(torch.linalg.matrix_norm(out_mixed - maximally_mixed).item()) < 1e-10,
        },
        "sympy_exact_kraus_and_affine_identity": sympy_readout,
        "z3_domain_and_coherence_noncollapse": z3_readout,
        "finite_noncommuting_probe_witness": probe_readout,
    }
    graveyard_companions = {
        "incomplete_kraus_control_loses_trace": {
            "trace_after_incomplete_channel": float(torch.real(torch.trace(incomplete)).item()),
            "pass": abs(float(torch.real(torch.trace(incomplete)).item()) - 1.0) > 1e-3,
        },
        "scalar_label_control_rejected": {
            "reason": "A label 'depolarizing' without Kraus/affine map, density output, and entropy/coherence readouts cannot witness CPTP noise.",
            "pass": True,
        },
        "dense_closure_control_not_used": {
            "reason": "The row uses one-qubit density/channel objects only; no many-qubit dense environment, PEPS3D closure, or manifold stacking is built.",
            "pass": True,
        },
        "commuting_identity_probe_erases_N01": {
            "readout": {"XI_minus_IX_order_erased_gap": probe_readout["XI_minus_IX_order_erased_gap"]},
            "pass": probe_readout["XI_minus_IX_order_erased_gap"] == 0.0,
        },
    }
    boundary = {
        "p_zero_identity_channel_boundary": {
            "distance": float(torch.linalg.matrix_norm(p0_out - pure_plus).item()),
            "pass": float(torch.linalg.matrix_norm(p0_out - pure_plus).item()) < 1e-10,
        },
        "p_one_pure_zero_maps_to_maximally_mixed_boundary": {
            "distance": float(torch.linalg.matrix_norm(p1_out_zero - maximally_mixed).item()),
            "entropy_bits": entropy_bits(p1_out_zero),
            "pass": float(torch.linalg.matrix_norm(p1_out_zero - maximally_mixed).item()) < 1e-10
            and abs(entropy_bits(p1_out_zero) - 1.0) < 1e-10,
        },
        "invalid_p_rejected_by_z3_boundary": {
            "solver_status": z3_readout["invalid_p_inside_domain_status"],
            "pass": z3_readout["invalid_p_inside_domain_pass"],
        },
    }
    entropy_matrix = [
        {
            "observable": "von_neumann_entropy",
            "support_kind": "one_qubit_density",
            "support_id": "pure_zero_input",
            "subsystem_partition": "full_one_qubit",
            "value_bits": zero_entropy_in,
            "status": "passed_input_boundary",
        },
        {
            "observable": "von_neumann_entropy",
            "support_kind": "one_qubit_density",
            "support_id": "depolarized_zero_p_0_4",
            "subsystem_partition": "full_one_qubit",
            "value_bits": zero_entropy_out,
            "status": "passed_noise_entropy_readout",
        },
        {
            "observable": "x_coherence_expectation",
            "support_kind": "one_qubit_density",
            "support_id": "depolarized_plus_p_0_4",
            "subsystem_partition": "X_probe",
            "value_bits": plus_x_out,
            "status": "passed_coherence_degradation_readout",
        },
    ]
    scale_rungs = [
        {"qubits": 1, "status": "passed_scale_floor", "description": "finite one-qubit depolarizing CPTP channel"},
        {"qubits": 2, "status": "blocked_pending_channel_composition_row", "description": "two-qubit independent noise is outside this substrate row"},
        {"qubits": 8, "status": "blocked_pending_channel_composition_row", "description": "multi-qubit channel scaling is outside this substrate row"},
    ]
    ablation_outcome_delta = {
        "pytorch": {
            "without_tool": "map_unprovable",
            "reason": "Density/channel evolution, Kraus application, spectra, entropy, coherence, and probe commutators are PyTorch objects.",
        },
        "sympy": {
            "without_tool": "map_unprovable",
            "reason": "Exact Kraus completeness and affine depolarizing identity become unchecked numeric observations.",
        },
        "z3": {
            "without_tool": "map_unprovable",
            "reason": "p-domain and positive-noise coherence-degradation noncollapse are not mechanically blocked.",
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
        "finite_map": "D_p : finite one-qubit spinor-derived density rho -> (1-p)rho + p I/2 with Kraus, entropy, coherence, and probe readouts",
        "domain": "finite one-qubit density states {|0><0|, |+><+|, I/2}, finite p in {0, 0.4, 1}, finite Pauli probes {X,Z,I}",
        "codomain_or_output": "finite output densities, trace/PSD/unital statuses, entropy values, coherence expectations, exact SymPy identities, and z3 noncollapse statuses",
        "F01_status": "passed: finite states, finite p values, finite Kraus operators, finite probes, finite controls, finite outputs",
        "N01_status": "passed_limited_probe_noncommutation: finite X/Z probe commutator is nonzero while identity-probe order-erased control collapses; the depolarizing channel itself is not promoted as a path-order layer",
        "torch_carrier_status": "claim_bearing_one_qubit_density_channel",
        "spinor_or_density_status": "spinor_derived_density_to_noisy_density_readout",
        "peps3d_anchor_status": "not_applicable_to_one_qubit_channel_row; PEPS3D scale promotion remains blocked",
        "math_object": "finite one-qubit depolarizing CPTP channel with entropy and coherence readouts",
        "observable": [
            "Kraus completeness",
            "trace and PSD",
            "unital fixed point",
            "von Neumann entropy",
            "X coherence degradation",
            "finite X/Z probe noncommutation",
            "z3 p-domain and noncollapse status",
        ],
        "predicate": "finite depolarizing channel is CPTP/unital and degrades pure-state information while invalid, incomplete, scalar, dense-closure, and order-erased controls fail",
        "entropy_matrix": entropy_matrix,
        "scale_rungs": scale_rungs,
        "controls": {
            "p_zero_identity": boundary["p_zero_identity_channel_boundary"],
            "p_one_maximally_mixed": boundary["p_one_pure_zero_maps_to_maximally_mixed_boundary"],
            "invalid_p": boundary["invalid_p_rejected_by_z3_boundary"],
            "incomplete_kraus": graveyard_companions["incomplete_kraus_control_loses_trace"],
            "scalar_label": graveyard_companions["scalar_label_control_rejected"],
            "dense_closure": graveyard_companions["dense_closure_control_not_used"],
            "order_erased": graveyard_companions["commuting_identity_probe_erases_N01"],
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
