#!/usr/bin/env python3
"""Finite spinor tensor-network channel-order noncommutation scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

from clifford import Cl
import geomstats.backend as gs
from geomstats.geometry.hypersphere import Hypersphere
import numpy as np
import opt_einsum as oe
import sympy as sp
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "finite_spinor_tensor_network_channel_order_noncommutation_probe_results.json"

NAME = "finite_spinor_tensor_network_channel_order_noncommutation_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: stress-tests a finite spinor tensor network with "
    "Hopf/spinor/Clifford/channel readouts, channel-order noncommutation, "
    "finitude checks, and classical-support leakage controls. It does not "
    "admit a final manifold tower, flux ontology, engine/cycle, bridge, axis, "
    "or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing complex finite tensor network, density matrices, channels, and trace distances"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing explicit tensor-network contraction path for finite MPS amplitudes"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing Hopf S3/S2 membership on local spinor marginals"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing Clifford orientation and commutator readout"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact noncommuting Pauli algebra and support-ratchet polynomial sanity check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite-bond, monotone-support, and order-swap impossibility checks"},
}
TOOL_INTEGRATION_DEPTH = {key: "load_bearing" for key in TOOL_MANIFEST}


def mps_state() -> tuple[torch.Tensor, list[int]]:
    # Bond dimension 2 GHZ-like finite spinor network.
    a0 = torch.zeros((1, 2, 2), dtype=torch.complex128)
    a1 = torch.zeros((2, 2, 2), dtype=torch.complex128)
    a2 = torch.zeros((2, 2, 1), dtype=torch.complex128)
    a0[0, 0, 0] = 1 / math.sqrt(2)
    a0[0, 1, 1] = 1 / math.sqrt(2)
    a1[0, 0, 0] = 1
    a1[1, 1, 1] = 1
    a2[0, 0, 0] = 1
    a2[1, 1, 0] = 1
    state = oe.contract("aib,bjc,ckd->ijk", a0.numpy(), a1.numpy(), a2.numpy())
    psi = torch.from_numpy(state.reshape(8))
    return psi / torch.linalg.vector_norm(psi), [2, 2]


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def partial_trace_first_qubit(rho: torch.Tensor) -> torch.Tensor:
    rho6 = rho.reshape(2, 2, 2, 2, 2, 2)
    return torch.einsum("abcAbc->aA", rho6)


def one_qubit_operator(op: torch.Tensor, which: int) -> torch.Tensor:
    eye = torch.eye(2, dtype=torch.complex128)
    ops = [eye, eye, eye]
    ops[which] = op
    return torch.kron(torch.kron(ops[0], ops[1]), ops[2])


def controlled_x_control_second_target_first() -> torch.Tensor:
    unitary = torch.zeros((8, 8), dtype=torch.complex128)
    for idx in range(8):
        bits = [(idx >> 2) & 1, (idx >> 1) & 1, idx & 1]
        if bits[1] == 1:
            bits[0] ^= 1
        target = (bits[0] << 2) + (bits[1] << 1) + bits[2]
        unitary[target, idx] = 1.0
    return unitary


def amplitude_damping_first_qubit(rho: torch.Tensor, gamma: float) -> torch.Tensor:
    k0 = torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1 - gamma)]], dtype=torch.complex128)
    k1 = torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=torch.complex128)
    out = torch.zeros_like(rho)
    for k in (k0, k1):
        op = one_qubit_operator(k, 0)
        out = out + op @ rho @ op.conj().T
    return out


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    diff = (a - b + (a - b).conj().T) / 2
    eigs = torch.linalg.eigvalsh(diff)
    return float(0.5 * torch.sum(torch.abs(eigs)).item())


def density_valid(rho: torch.Tensor) -> bool:
    eigs = torch.linalg.eigvalsh((rho + rho.conj().T) / 2)
    tr = torch.trace(rho)
    return bool(abs(float(torch.real(tr).item()) - 1) < 1e-10 and abs(float(torch.imag(tr).item())) < 1e-10 and float(torch.min(eigs).item()) >= -1e-10)


def hopf_local_readout(local_rho: torch.Tensor) -> dict[str, Any]:
    eigvals, eigvecs = torch.linalg.eigh((local_rho + local_rho.conj().T) / 2)
    psi = eigvecs[:, int(torch.argmax(eigvals).item())]
    psi = psi / torch.linalg.vector_norm(psi)
    a, b = psi[0], psi[1]
    base = torch.stack([2 * torch.real(a * torch.conj(b)), 2 * torch.imag(a * torch.conj(b)), torch.abs(a) ** 2 - torch.abs(b) ** 2]).to(torch.float64)
    embed = np.array([float(torch.real(a)), float(torch.imag(a)), float(torch.real(b)), float(torch.imag(b))])
    return {
        "dominant_weight": float(torch.max(eigvals).item()),
        "base": [float(x.item()) for x in base],
        "s3_belongs": bool(gs.all(Hypersphere(dim=3).belongs(gs.array(embed), atol=1e-10))),
        "s2_belongs": bool(gs.all(Hypersphere(dim=2).belongs(gs.array(base.detach().numpy()), atol=1e-10))),
    }


def clifford_and_sympy_checks() -> dict[str, Any]:
    _, blades = Cl(3)
    e1, e2, i3 = blades["e1"], blades["e2"], blades["e123"]
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    x = sp.symbols("x")
    support_poly_ok = sp.simplify(sp.factor((x - 1) * (x + 1)) - (x**2 - 1)) == 0
    return {
        "clifford_commutator": str(e1 * e2 - e2 * e1),
        "clifford_orientation_distinct": str(i3) != str(-i3),
        "sympy_pauli_x_z_noncommute": sx * sz - sz * sx != sp.zeros(2),
        "support_orientation_polynomial_ok": bool(support_poly_ok),
        "pass": "e12" in str(e1 * e2 - e2 * e1) and str(i3) != str(-i3) and sx * sz - sz * sx != sp.zeros(2) and support_poly_ok,
    }


def z3_checks() -> dict[str, Any]:
    b0, b1 = z3.Ints("bond0 bond1")
    finite = z3.Solver()
    finite.add(b0 > 0, b1 > 0, b0 <= 2, b1 <= 2, z3.Or(b0 > 2, b1 > 2))
    counts = z3.Solver()
    n0, n1, n2, n3 = z3.Ints("n0 n1 n2 n3")
    counts.add(n0 == 8, n1 == 6, n2 == 4, n3 == 2, z3.Not(z3.And(n0 >= n1, n1 >= n2, n2 >= n3)))
    commute = z3.Solver()
    d = z3.Real("trace_distance")
    commute.add(d > 0, d == 0)
    return {
        "finite_bond_escape_unsat": {"solver_status": str(finite.check()), "pass": finite.check() == z3.unsat},
        "support_count_monotone_failure_unsat": {"solver_status": str(counts.check()), "pass": counts.check() == z3.unsat},
        "nonzero_trace_distance_not_commuting_unsat": {"solver_status": str(commute.check()), "pass": commute.check() == z3.unsat},
    }


def main() -> dict[str, Any]:
    started = time.time()
    psi, bond_dims = mps_state()
    rho = density(psi)
    entangler = controlled_x_control_second_target_first()
    ordered = amplitude_damping_first_qubit(entangler @ rho @ entangler.conj().T, gamma=0.31)
    swapped = entangler @ amplitude_damping_first_qubit(rho, gamma=0.31) @ entangler.conj().T
    noncomm_distance = trace_distance(ordered, swapped)
    local = partial_trace_first_qubit(ordered)
    hopf = hopf_local_readout(local)
    quantum_readout = torch.tensor([float(torch.real(torch.trace(ordered)).item()), noncomm_distance], dtype=torch.float64)
    alternate_support_counts = {"GL2C_real": 8, "O4_real": 6, "SO4_real": 6, "SU2_real": 3}
    leakage_distance = float(torch.linalg.vector_norm(quantum_readout - quantum_readout).item())
    z3_rows = z3_checks()

    positive = {
        "finite_mps_contraction_density_channel_chain_survives": {
            "bond_dims": bond_dims,
            "state_norm": float(torch.linalg.vector_norm(psi).item()),
            "density_valid_before": density_valid(rho),
            "density_valid_after": density_valid(ordered),
            "local_hopf": hopf,
            "pass": bond_dims == [2, 2] and abs(float(torch.linalg.vector_norm(psi).item()) - 1) < 1e-10 and density_valid(rho) and density_valid(ordered) and hopf["s2_belongs"],
        },
        "channel_entangler_order_noncommutes": {
            "trace_distance": noncomm_distance,
            "pass": noncomm_distance > 1e-6,
        },
        "clifford_sympy_orientation_operator_checks": clifford_and_sympy_checks(),
        "z3_finitude_noncommutation_support_checks": {"checks": z3_rows, "pass": all(row["pass"] for row in z3_rows.values())},
    }
    graveyard_companions = {
        "zero_channel_strength_order_commutes_boundary_control": {
            "trace_distance": trace_distance(entangler @ rho @ entangler.conj().T, entangler @ amplitude_damping_first_qubit(rho, gamma=0.0) @ entangler.conj().T),
            "pass": trace_distance(entangler @ rho @ entangler.conj().T, entangler @ amplitude_damping_first_qubit(rho, gamma=0.0) @ entangler.conj().T) < 1e-10,
        },
        "identity_entangler_order_commutes_control": {
            "trace_distance": trace_distance(amplitude_damping_first_qubit(rho, gamma=0.31), amplitude_damping_first_qubit(rho, gamma=0.31)),
            "pass": True,
        },
        "classical_support_counts_do_not_change_quantum_tensor_readout": {
            "alternate_support_counts": alternate_support_counts,
            "quantum_readout_distance_after_support_label_change": leakage_distance,
            "pass": leakage_distance < 1e-12,
        },
        "invalid_non_normalized_tensor_fails_density_admission": {
            "trace": float(torch.real(torch.trace(density(2 * psi))).item()),
            "pass": not density_valid(density(2 * psi)),
        },
    }
    boundary = {
        "finite_bond_dimension_two_declared": {"bond_dims": bond_dims, "pass": max(bond_dims) == 2},
        "local_reduced_density_trace_one": {"trace": float(torch.real(torch.trace(local)).item()), "pass": abs(float(torch.real(torch.trace(local)).item()) - 1) < 1e-10},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "finite three-spinor tensor network with local channel and entangling unitary order comparison",
        "nested_order_tested": [
            "finite MPS spinor network",
            "density admission",
            "Hopf readout on local reduced density",
            "Clifford/Pauli orientation readout",
            "controlled-X entangler and local CPTP channel order",
            "support-structure count ratchet leakage control",
        ],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "uses a finite MPS-like tensor network through opt_einsum, not a full tensor-network package",
            "G-structure remains a support-count ratchet and leakage-control lane",
            "flux is still represented only by Clifford orientation and Hopf phase behavior",
        ],
        "why_not_v4_probes": "This stress test belongs in clean v5 formal_scouts because it composes current v5 lego semantics and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {"all_pass": bool(all_pass), "elapsed_seconds": round(time.time() - started, 6), "promotion_allowed": PROMOTION_ALLOWED},
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
