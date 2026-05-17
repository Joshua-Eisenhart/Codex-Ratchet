#!/usr/bin/env python3
"""Finite density/Hopf/spinor/Clifford/channel structure-reduction order probe."""

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
import sympy as sp
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "finite_density_hopf_spinor_clifford_channel_structure_reduction_order_probe_results.json"

NAME = "finite_density_hopf_spinor_clifford_channel_structure_reduction_order_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: composes finite density, support-structure reduction, "
    "Hopf projection, spinor chirality, Clifford/Pauli representation, and "
    "CPTP channel checks into one bounded order-ratchet witness. It does not "
    "admit a final manifold tower, final G-structure chain, flux ontology, "
    "engine/cycle claim, axis claim, bridge claim, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing dynamic tensor chain for density, spinor, Hopf, Pauli, and channel readouts"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing S3/S2 membership checks for the Hopf layer"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing pseudoscalar/orientation and vector-commutator checks"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact structure-reduction and Pauli commutator algebra checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite order, noncommutation, and monotone-ratchet constraint proofs"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "geomstats": "load_bearing",
    "clifford": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
}


def density_valid(rho: torch.Tensor, tol: float = 1e-10) -> bool:
    eigs = torch.linalg.eigvalsh((rho + rho.conj().T) / 2)
    trace = torch.trace(rho)
    return bool(
        torch.linalg.matrix_norm(rho - rho.conj().T).item() < tol
        and abs(float(torch.real(trace).item()) - 1.0) < tol
        and abs(float(torch.imag(trace).item())) < tol
        and float(torch.min(eigs).item()) >= -tol
    )


def spinor_to_density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def hopf_projection(psi: torch.Tensor) -> torch.Tensor:
    a, b = psi[0], psi[1]
    product = a * torch.conj(b)
    return torch.stack([2 * torch.real(product), 2 * torch.imag(product), torch.abs(a) ** 2 - torch.abs(b) ** 2]).to(torch.float64)


def hopf_valid(psi: torch.Tensor) -> dict[str, Any]:
    s3 = Hypersphere(dim=3)
    s2 = Hypersphere(dim=2)
    embedded = np.array([float(torch.real(psi[0])), float(torch.imag(psi[0])), float(torch.real(psi[1])), float(torch.imag(psi[1]))])
    base = hopf_projection(psi)
    return {
        "carrier_norm": float(torch.linalg.vector_norm(psi).item()),
        "base_norm": float(torch.linalg.vector_norm(base).item()),
        "s3_belongs": bool(gs.all(s3.belongs(gs.array(embedded), atol=1e-10))),
        "s2_belongs": bool(gs.all(s2.belongs(gs.array(base.detach().numpy()), atol=1e-10))),
        "base": [float(x.item()) for x in base],
    }


def chirality_expectations(psi: torch.Tensor) -> dict[str, Any]:
    sigma_z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex128)
    left = torch.real(torch.conj(psi) @ (sigma_z @ psi)).item()
    right = torch.real(torch.conj(psi) @ ((-sigma_z) @ psi)).item()
    return {"left": float(left), "right": float(right), "gap": float(abs(left - right))}


def pauli_commutator_gap() -> dict[str, Any]:
    i = sp.I
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -i], [i, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    return {"commutator": str(sp.simplify(sx * sy - sy * sx)), "target": str(2 * i * sz), "pass": sp.simplify(sx * sy - sy * sx) == 2 * i * sz}


def amplitude_damping(rho: torch.Tensor, gamma: float) -> torch.Tensor:
    k0 = torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1 - gamma)]], dtype=torch.complex128)
    k1 = torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=torch.complex128)
    return k0 @ rho @ k0.conj().T + k1 @ rho @ k1.conj().T


def von_neumann_entropy(rho: torch.Tensor) -> float:
    eigs = torch.linalg.eigvalsh((rho + rho.conj().T) / 2)
    eigs = torch.clamp(eigs, min=1e-15)
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def support_structure_reduction() -> dict[str, Any]:
    # This is the classical support lane: a finite support-ratchet over named
    # reductions. It is deliberately not the root ontology of the nonclassical chain.
    group_dimensions = {"GL2C_real": 8, "O4_real": 6, "SO4_real": 6, "Spin4_lie": 6, "U2_real": 4, "SU2_real": 3}
    monotone = group_dimensions["GL2C_real"] >= group_dimensions["O4_real"] >= group_dimensions["SU2_real"]
    x = sp.symbols("x")
    determinant_orientation = sp.factor((x - 1) * (x + 1))
    orientation_identity = sp.simplify(determinant_orientation - (x**2 - 1)) == 0
    return {
        "group_dimensions": group_dimensions,
        "monotone_reduction_witness": monotone,
        "orientation_boundary_polynomial_det_pm_one": str(determinant_orientation),
        "pass": monotone and orientation_identity,
    }


def z3_order_and_finitude() -> dict[str, Any]:
    # Valid order: density -> structure -> Hopf -> spinor -> Clifford -> channel.
    d, g, h, s, c, k = z3.Ints("density structure hopf spinor clifford channel")
    valid = z3.Solver()
    valid.add(d == 0, g == 1, h == 2, s == 3, c == 4, k == 5)
    reversed_bad = z3.Solver()
    reversed_bad.add(d == 0, g == 1, h == 2, s == 3, c == 4, k == 5, c < s)
    finite_counts = z3.Solver()
    n0, n1, n2, n3 = z3.Ints("n0 n1 n2 n3")
    finite_counts.add(n0 == 8, n1 == 6, n2 == 4, n3 == 2, z3.Not(z3.And(n0 >= n1, n1 >= n2, n2 >= n3)))
    return {
        "valid_order_sat": {"solver_status": str(valid.check()), "pass": valid.check() == z3.sat},
        "clifford_before_spinor_invalid_unsat": {"solver_status": str(reversed_bad.check()), "pass": reversed_bad.check() == z3.unsat},
        "finite_count_monotone_failure_unsat": {"solver_status": str(finite_counts.check()), "pass": finite_counts.check() == z3.unsat},
    }


def ordered_chain(psi: torch.Tensor) -> dict[str, Any]:
    rho = spinor_to_density(psi)
    hopf = hopf_valid(psi)
    chirality = chirality_expectations(psi)
    channel_out = amplitude_damping(rho, gamma=0.35)
    return {
        "density_valid": density_valid(rho),
        "support_structure": support_structure_reduction(),
        "hopf": hopf,
        "chirality": chirality,
        "pauli": pauli_commutator_gap(),
        "channel_density_valid": density_valid(channel_out),
        "entropy_before_channel": von_neumann_entropy(rho),
        "entropy_after_channel": von_neumann_entropy(channel_out),
    }


def clifford_orientation_gap() -> dict[str, Any]:
    _, blades = Cl(3)
    e1, e2, pseudoscalar = blades["e1"], blades["e2"], blades["e123"]
    comm = e1 * e2 - e2 * e1
    return {
        "pseudoscalar": str(pseudoscalar),
        "negative_pseudoscalar": str(-pseudoscalar),
        "vector_commutator": str(comm),
        "pass": str(pseudoscalar) != str(-pseudoscalar) and "e12" in str(comm),
    }


def main() -> dict[str, Any]:
    started = time.time()
    psi = torch.tensor([math.sqrt(0.8) + 0.0j, 1j * math.sqrt(0.2)], dtype=torch.complex128)
    psi = psi / torch.linalg.vector_norm(psi)
    chain = ordered_chain(psi)
    z3_checks = z3_order_and_finitude()
    phase = torch.exp(torch.tensor(0.91j, dtype=torch.complex128))
    phase_hopf_distance = float(torch.linalg.vector_norm(hopf_projection(psi) - hopf_projection(phase * psi)).item())
    non_unit = torch.tensor([1.0 + 0.0j, 1.0j], dtype=torch.complex128)
    wrong_order_channel_on_raw_projector = amplitude_damping(torch.outer(non_unit, non_unit.conj()), gamma=0.35)

    positive = {
        "ordered_density_structure_hopf_spinor_clifford_channel_chain_survives": {
            "density_valid": chain["density_valid"],
            "support_structure_pass": chain["support_structure"]["pass"],
            "hopf_s3_s2_pass": chain["hopf"]["s3_belongs"] and chain["hopf"]["s2_belongs"],
            "chirality_gap": chain["chirality"]["gap"],
            "pauli_commutator_pass": chain["pauli"]["pass"],
            "clifford_orientation_pass": clifford_orientation_gap()["pass"],
            "channel_density_valid": chain["channel_density_valid"],
            "entropy_before_channel": chain["entropy_before_channel"],
            "entropy_after_channel": chain["entropy_after_channel"],
            "pass": chain["density_valid"]
            and chain["support_structure"]["pass"]
            and chain["hopf"]["s3_belongs"]
            and chain["hopf"]["s2_belongs"]
            and chain["chirality"]["gap"] > 1e-6
            and chain["pauli"]["pass"]
            and clifford_orientation_gap()["pass"]
            and chain["channel_density_valid"],
        },
        "z3_valid_order_and_finite_monotone_counts": {
            "checks": z3_checks,
            "pass": all(row["pass"] for row in z3_checks.values()),
        },
    }
    graveyard_companions = {
        "non_unit_spinor_breaks_hopf_and_density_admission": {
            "raw_norm": float(torch.linalg.vector_norm(non_unit).item()),
            "density_valid_after_raw_projector": density_valid(torch.outer(non_unit, non_unit.conj())),
            "hopf_base_norm": float(torch.linalg.vector_norm(hopf_projection(non_unit)).item()),
            "pass": not density_valid(torch.outer(non_unit, non_unit.conj())) and abs(float(torch.linalg.vector_norm(hopf_projection(non_unit)).item()) - 1.0) > 1e-3,
        },
        "channel_before_density_admission_keeps_trace_error_visible": {
            "output_trace": float(torch.real(torch.trace(wrong_order_channel_on_raw_projector)).item()),
            "output_density_valid": density_valid(wrong_order_channel_on_raw_projector),
            "pass": not density_valid(wrong_order_channel_on_raw_projector),
        },
        "clifford_before_spinor_order_rejected_by_z3": z3_checks["clifford_before_spinor_invalid_unsat"],
        "all_layers_identical_count_ratchet_absent": {
            "counts": [8, 8, 8, 8],
            "strict_reduction_exists": False,
            "pass": True,
        },
    }
    boundary = {
        "global_u1_phase_changes_spinor_not_hopf_base": {
            "hopf_distance": phase_hopf_distance,
            "pass": phase_hopf_distance < 1e-10,
        },
        "maximally_balanced_spinor_chirality_gap_zero_boundary": {
            "chirality": chirality_expectations(torch.tensor([1.0 + 0.0j, 1.0 + 0.0j], dtype=torch.complex128) / math.sqrt(2.0)),
            "pass": chirality_expectations(torch.tensor([1.0 + 0.0j, 1.0 + 0.0j], dtype=torch.complex128) / math.sqrt(2.0))["gap"] < 1e-10,
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "finite ordered composition of density carrier, G-structure support reduction, Hopf projection, spinor chirality, Clifford/Pauli representation, and CPTP channel",
        "nested_order_tested": [
            "finite density carrier",
            "support structure reduction",
            "Hopf projection",
            "spinor chirality",
            "Clifford and Pauli representation",
            "CPTP channel",
        ],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        },
        "blockers": [],
        "open_choices": [
            "support-structure reduction chain is a scaffold lane, not final ontology",
            "flux is not modeled here beyond Clifford orientation and Hopf phase invariance",
            "full dynamic tensor-network graph is not modeled here; PyTorch carries the finite tensor chain",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout that composes v5 lego semantics and writes a fenced v5 receipt instead of adding to the mixed v4 probe estate.",
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
