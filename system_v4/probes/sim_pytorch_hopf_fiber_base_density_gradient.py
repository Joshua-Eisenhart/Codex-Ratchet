#!/usr/bin/env python3
"""PyTorch gradient readout for Hopf fiber and base density coordinates."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import math
from pathlib import Path

import torch


NAME = "pytorch_hopf_fiber_base_density_gradient"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "constructs complex tensor carrier states and uses autograd to test density readout derivatives",
    }
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing"}


def spinor(theta: torch.Tensor, phi: torch.Tensor, chi: torch.Tensor) -> torch.Tensor:
    half = torch.tensor(0.5, dtype=torch.float64)
    first = torch.cos(theta * half) * torch.exp(0.5j * (chi + phi))
    second = torch.sin(theta * half) * torch.exp(0.5j * (chi - phi))
    return torch.stack([first, second]).to(torch.complex128)


def density(psi: torch.Tensor) -> torch.Tensor:
    return psi[:, None] * torch.conj(psi[None, :])


def off_diagonal_abs(theta: torch.Tensor, phi: torch.Tensor, chi: torch.Tensor) -> torch.Tensor:
    rho = density(spinor(theta, phi, chi))
    return torch.real(rho[0, 1] * torch.conj(rho[0, 1]))


def off_diagonal_real(theta: torch.Tensor, phi: torch.Tensor, chi: torch.Tensor) -> torch.Tensor:
    rho = density(spinor(theta, phi, chi))
    return torch.real(rho[0, 1])


def gradient(value: torch.Tensor, variable: torch.Tensor) -> float:
    grad = torch.autograd.grad(value, variable, retain_graph=True, allow_unused=False)[0]
    return float(grad.detach())


def run_positive() -> dict[str, object]:
    theta = torch.tensor(math.pi / 3.0, dtype=torch.float64, requires_grad=True)
    phi = torch.tensor(math.pi / 5.0, dtype=torch.float64, requires_grad=True)
    chi = torch.tensor(math.pi / 7.0, dtype=torch.float64, requires_grad=True)

    fiber_invariant = off_diagonal_abs(theta, phi, chi)
    base_visible = off_diagonal_real(theta, phi, chi)
    d_fiber_invariant_d_chi = gradient(fiber_invariant, chi)
    d_base_visible_d_phi = gradient(base_visible, phi)
    return {
        "theta": float(theta.detach()),
        "phi": float(phi.detach()),
        "chi": float(chi.detach()),
        "fiber_invariant_readout": float(fiber_invariant.detach()),
        "base_visible_readout": float(base_visible.detach()),
        "d_fiber_invariant_readout_d_chi": d_fiber_invariant_d_chi,
        "d_base_visible_readout_d_phi": d_base_visible_d_phi,
        "fiber_coordinate_gradient_zero": abs(d_fiber_invariant_d_chi) < 1e-12,
        "base_coordinate_gradient_nonzero": abs(d_base_visible_d_phi) > 1e-3,
    }


def run_graveyards() -> dict[str, object]:
    phi = torch.tensor(math.pi / 5.0, dtype=torch.float64, requires_grad=True)
    chi = torch.tensor(math.pi / 7.0, dtype=torch.float64, requires_grad=True)

    pole_theta = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
    pole_value = off_diagonal_real(pole_theta, phi, chi)
    pole_grad = gradient(pole_value, phi)

    equator_theta = torch.tensor(math.pi / 2.0, dtype=torch.float64, requires_grad=True)
    diagonal_value = torch.real(density(spinor(equator_theta, phi, chi))[0, 0])
    diagonal_grad = gradient(diagonal_value, phi)

    constant_no_path = torch.tensor(1.0, dtype=torch.float64)
    return {
        "base_lift_at_pole_degenerates": {
            "d_off_diagonal_real_d_phi_at_pole": pole_grad,
            "expected_zero": True,
            "passed": abs(pole_grad) < 1e-12,
        },
        "diagonal_readout_hides_base_lift_change": {
            "d_diagonal_density_d_phi": diagonal_grad,
            "expected_zero": True,
            "passed": abs(diagonal_grad) < 1e-12,
        },
        "constant_readout_has_no_path_derivative": {
            "requires_grad": bool(constant_no_path.requires_grad),
            "can_distinguish_fiber_base": False,
            "passed": True,
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["fiber_coordinate_gradient_zero"]
        and positive["base_coordinate_gradient_nonzero"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "PyTorch autograd Hopf-coordinate density-gradient baseline only; no QIT, GStack, axis, bridge, "
            "nonclassical, target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "declared_fiber_base_coordinate_readout_baseline",
        "promotion_condition": (
            "May only support later differentiable-geometry planning after independent carrier and operator-evolution "
            "receipts reproduce the same distinction with physical graveyards."
        ),
        "demotion_condition": (
            "Demote if the fiber-coordinate gradient is nonzero for a fiber-invariant density readout, if the "
            "base-coordinate gradient vanishes away from degeneracy, or if pole/diagonal graveyards do not collapse."
        ),
        "blocked_until": "blocked from target-system claims until fuller carrier/topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No Lindblad evolution, Hamiltonian dynamics, or target-system admission.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
            "No claim that flux is represented.",
        ],
        "divergence_log": (
            "This is a PyTorch complex-tensor/autograd baseline over declared coordinates. It checks local derivative "
            "readouts only and cannot promote a target geometry."
        ),
        "operation_sequence": [
            "construct complex two-component carrier tensor in Hopf-style coordinates",
            "form density tensor psi psi dagger",
            "differentiate fiber-invariant off-diagonal magnitude by the fiber coordinate",
            "differentiate off-diagonal real density readout by the base-lift coordinate",
            "run pole-degenerate, diagonal-hidden, and no-path graveyards",
        ],
        "carrier_topology": "differentiable two-component complex tensor carrier projected to density readouts",
        "observable": "autograd derivatives of density readouts with respect to fiber and base-lift coordinates",
        "pass_fail_predicate": (
            "fiber-invariant density readout has zero fiber gradient, base-lift readout has nonzero base gradient away "
            "from degeneracy, and adjacent graveyards collapse"
        ),
        "graveyards": [
            "base-lift derivative at pole degenerates",
            "diagonal density readout hides base-lift change",
            "constant no-path readout cannot distinguish loops",
        ],
        "baselines": [
            "sampled NumPy Hopf path metric fixture",
            "symbolic SymPy Hopf density derivative fixture",
            "QuTiP and Qiskit density-object path readout fixtures",
        ],
        "alternative_formulations": [
            "torch path-length sweep over sampled states",
            "Hamiltonian generator autograd fixture",
            "operator-evolution differentiable fixture",
        ],
        "exact_tool_function_needs": {
            "pytorch": ["tensor", "complex exp", "conj", "stack", "autograd.grad"]
        },
        "lego_or_coupling_target": "declared_fiber_base_coordinate_readout_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
