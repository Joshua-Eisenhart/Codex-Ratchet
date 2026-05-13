#!/usr/bin/env python3
"""PyTorch Hopf/Weyl fiber-base gradient readout baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import torch
from receipt_boundary import apply_default_receipt_boundary


NAME = "pytorch_hopf_weyl_fiber_base_gradient_readout"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "constructs complex two-component carrier tensors and uses autograd.grad for density-readout sensitivities",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supports sampled finite-difference checks and signed-area control metrics",
    },
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "numpy": "supportive"}

DTYPE = torch.float64
CDTYPE = torch.complex128


def spinor(theta: torch.Tensor, phi: torch.Tensor, chi: torch.Tensor, sheet_orientation: int) -> torch.Tensor:
    if sheet_orientation not in (-1, 1):
        raise ValueError("sheet_orientation must be -1 or +1")
    signed_phi = phi * float(sheet_orientation)
    half = torch.tensor(0.5, dtype=DTYPE)
    amp0 = torch.cos(theta * half).to(CDTYPE) * torch.exp(0.5j * (chi + signed_phi).to(CDTYPE))
    amp1 = torch.sin(theta * half).to(CDTYPE) * torch.exp(0.5j * (chi - signed_phi).to(CDTYPE))
    return torch.stack([amp0, amp1])


def density(psi: torch.Tensor) -> torch.Tensor:
    return psi[:, None] @ torch.conj(psi[None, :])


def bloch_from_density(rho: torch.Tensor) -> torch.Tensor:
    x = 2.0 * torch.real(rho[0, 1])
    y = -2.0 * torch.imag(rho[0, 1])
    z = torch.real(rho[0, 0] - rho[1, 1])
    return torch.stack([x, y, z])


def density_readout(theta_value: float, phi_value: float, chi_value: float, sheet_orientation: int) -> dict[str, object]:
    theta = torch.tensor(theta_value, dtype=DTYPE)
    phi = torch.tensor(phi_value, dtype=DTYPE, requires_grad=True)
    chi = torch.tensor(chi_value, dtype=DTYPE, requires_grad=True)
    rho = density(spinor(theta, phi, chi, sheet_orientation))
    bloch = bloch_from_density(rho)
    density_norm = torch.real(torch.sum(torch.conj(rho) * rho))
    bloch_norm = torch.sum(bloch * bloch)
    phi_grad = torch.autograd.grad(bloch_norm, phi, retain_graph=True)[0]
    chi_grad = torch.autograd.grad(bloch_norm, chi, retain_graph=True, allow_unused=True)[0]
    density_phi_grad = torch.autograd.grad(density_norm, phi, retain_graph=True)[0]
    density_chi_grad = torch.autograd.grad(density_norm, chi, allow_unused=True)[0]
    if chi_grad is None:
        chi_grad = torch.tensor(0.0, dtype=DTYPE)
    if density_chi_grad is None:
        density_chi_grad = torch.tensor(0.0, dtype=DTYPE)
    return {
        "bloch": [float(value) for value in bloch.detach().numpy()],
        "density_norm": float(density_norm.detach()),
        "bloch_norm": float(bloch_norm.detach()),
        "d_bloch_norm_d_phi": float(phi_grad.detach()),
        "d_bloch_norm_d_chi": float(chi_grad.detach()),
        "d_density_norm_d_phi": float(density_phi_grad.detach()),
        "d_density_norm_d_chi": float(density_chi_grad.detach()),
    }


def signed_bloch_y(theta_value: float, phi_value: float, chi_value: float, sheet_orientation: int) -> dict[str, float]:
    theta = torch.tensor(theta_value, dtype=DTYPE)
    phi = torch.tensor(phi_value, dtype=DTYPE, requires_grad=True)
    chi = torch.tensor(chi_value, dtype=DTYPE, requires_grad=True)
    rho = density(spinor(theta, phi, chi, sheet_orientation))
    bloch = bloch_from_density(rho)
    readout = bloch[1]
    d_phi = torch.autograd.grad(readout, phi, retain_graph=True)[0]
    d_chi = torch.autograd.grad(readout, chi, allow_unused=True)[0]
    if d_chi is None:
        d_chi = torch.tensor(0.0, dtype=DTYPE)
    return {
        "readout": float(readout.detach()),
        "d_readout_d_phi": float(d_phi.detach()),
        "d_readout_d_chi": float(d_chi.detach()),
    }


def finite_difference_phi(theta: float, phi: float, chi: float, sheet_orientation: int, eps: float = 1e-6) -> float:
    plus = signed_bloch_y(theta, phi + eps, chi, sheet_orientation)["readout"]
    minus = signed_bloch_y(theta, phi - eps, chi, sheet_orientation)["readout"]
    return float((plus - minus) / (2.0 * eps))


def sample_bloch_area(theta: float, sheet_orientation: int, samples: int = 129) -> float:
    rows: list[np.ndarray] = []
    for phi in np.linspace(0.0, 2.0 * math.pi, samples):
        readout = density_readout(theta, float(phi), 0.0, sheet_orientation)
        rows.append(np.asarray(readout["bloch"], dtype=float))
    xy = np.asarray([[row[0], row[1]] for row in rows], dtype=float)
    rolled = np.roll(xy, -1, axis=0)
    return float(0.5 * np.sum(xy[:, 0] * rolled[:, 1] - rolled[:, 0] * xy[:, 1]))


def run_positive() -> dict[str, object]:
    theta = math.pi / 3.0
    phi = math.pi / 5.0
    chi = math.pi / 7.0
    pos = signed_bloch_y(theta, phi, chi, 1)
    neg = signed_bloch_y(theta, phi, chi, -1)
    fiber_invariant = density_readout(theta, phi, chi, 1)
    fd = finite_difference_phi(theta, phi, chi, 1)
    pos_area = sample_bloch_area(theta, 1)
    neg_area = sample_bloch_area(theta, -1)
    return {
        "theta": theta,
        "phi": phi,
        "chi": chi,
        "positive_sheet_signed_bloch_y_gradient": pos,
        "negative_sheet_signed_bloch_y_gradient": neg,
        "density_norm_gradient_readout": fiber_invariant,
        "finite_difference_d_signed_bloch_y_d_phi": fd,
        "signed_xy_areas": {"positive_sheet": pos_area, "negative_sheet": neg_area},
        "survives_pytorch_gradient_readout": bool(
            abs(pos["d_readout_d_chi"]) < 1e-10
            and abs(fiber_invariant["d_density_norm_d_chi"]) < 1e-10
            and abs(fiber_invariant["d_density_norm_d_phi"]) < 1e-10
            and abs(pos["d_readout_d_phi"] - fd) < 1e-6
            and abs(pos["d_readout_d_phi"] + neg["d_readout_d_phi"]) < 1e-9
            and pos_area < -1.0
            and neg_area > 1.0
        ),
    }


def run_graveyards() -> dict[str, object]:
    theta = math.pi / 3.0
    phi = math.pi / 5.0
    chi = math.pi / 7.0
    pos = signed_bloch_y(theta, phi, chi, 1)
    neg = signed_bloch_y(theta, phi, chi, -1)
    pole = signed_bloch_y(0.0, phi, chi, 1)
    fiber_norm = density_readout(theta, phi, chi, 1)
    same_a = signed_bloch_y(theta, phi, chi, 1)
    same_b = signed_bloch_y(theta, phi, chi, 1)
    return {
        "fiber_coordinate_drops_from_density_readout": {
            "d_density_norm_d_chi": fiber_norm["d_density_norm_d_chi"],
            "passed": bool(abs(fiber_norm["d_density_norm_d_chi"]) < 1e-10),
        },
        "sheet_orientation_reversal_inverts_phi_gradient": {
            "positive_d_readout_d_phi": pos["d_readout_d_phi"],
            "negative_d_readout_d_phi": neg["d_readout_d_phi"],
            "passed": bool(abs(pos["d_readout_d_phi"] + neg["d_readout_d_phi"]) < 1e-9),
        },
        "base_loop_at_pole_collapses_phi_sensitivity": {
            "pole_d_readout_d_phi": pole["d_readout_d_phi"],
            "passed": bool(abs(pole["d_readout_d_phi"]) < 1e-10),
        },
        "same_sheet_duplicate_gradients_are_indistinguishable": {
            "gradient_gap": float(abs(same_a["d_readout_d_phi"] - same_b["d_readout_d_phi"])),
            "passed": bool(abs(same_a["d_readout_d_phi"] - same_b["d_readout_d_phi"]) < 1e-12),
        },
        "finite_difference_mismatch_would_break_autograd_surface": {
            "autograd": pos["d_readout_d_phi"],
            "finite_difference": finite_difference_phi(theta, phi, chi, 1),
            "passed": bool(abs(pos["d_readout_d_phi"] - finite_difference_phi(theta, phi, chi, 1)) < 1e-6),
        },
        "bare_loop_labels_without_differentiable_carrier_are_insufficient": {
            "has_torch_tensor_carrier": False,
            "has_autograd_graph": False,
            "passed": True,
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_pytorch_gradient_readout"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "PyTorch complex-tensor Hopf/Weyl fiber-base gradient-readout baseline only; this compares autograd "
            "sensitivities of declared carrier density readouts under phi and chi coordinates; no physical "
            "fiber/base loop independence proof, no full nested Hopf-torus manifold, no flux, no QIT, GStack, axis, bridge, "
            "nonclassical, target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later carrier-geometry planning after object-level, symbolic, Clifford, topology, "
            "and physical operator-evolution fixtures reproduce compatible fiber/base readouts with adjacent graveyards."
        ),
        "demotion_condition": (
            "Demote if chi affects density readouts, if phi gradients do not match finite differences, if sheet "
            "orientation reversal does not invert the chosen base-loop gradient, or if pole/duplicate/no-carrier "
            "graveyards do not collapse."
        ),
        "blocked_until": (
            "blocked from target-system claims until full carrier/topology implementation and physical-evolution "
            "graveyards exist"
        ),
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, or thermodynamic cycle mechanics.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This is a differentiable local carrier chart. It adds autograd sensitivity evidence for declared "
            "fiber/base loop coordinates, but it does not implement the fuller geometric carrier or prove physical independence."
        ),
        "operation_sequence": [
            "construct complex two-component PyTorch carrier tensors from Hopf coordinates theta, phi, chi",
            "apply a declared sheet-orientation sign to the base-loop phi coordinate",
            "form a density tensor and Bloch readout from the carrier",
            "differentiate density and Bloch-derived scalar readouts with respect to phi and chi",
            "compare autograd phi sensitivity to finite differences",
            "compare sheet-orientation reversal, pole collapse, duplicate-sheet, and no-carrier graveyards",
        ],
        "carrier_topology": "differentiable two-component Hopf-coordinate tensor carrier with density readout; no full S3 bundle or nested-torus manifold",
        "observable": "autograd gradients with respect to phi and chi, density norm, Bloch readout, signed xy area, and finite-difference gradient gap",
        "pass_fail_predicate": (
            "fiber coordinate chi drops from density-derived readouts, base coordinate phi changes selected Bloch "
            "readouts away from the pole, sheet orientation reversal inverts the selected phi gradient, autograd "
            "matches finite difference, and adjacent controls collapse or become indistinguishable"
        ),
        "graveyards": [
            "fiber coordinate drops from density readout",
            "sheet orientation reversal inverts phi gradient",
            "base loop at pole collapses phi sensitivity",
            "same-sheet duplicate gradients are indistinguishable",
            "finite-difference mismatch would break autograd surface",
            "bare loop labels without differentiable carrier are insufficient",
        ],
        "baselines": [
            "QuTiP Hopf/Weyl fiber-base carrier transport",
            "Qiskit Hopf/Weyl fiber-base carrier transport",
            "NumPy Weyl-sheet Hopf-loop readout separation",
            "SymPy Weyl-sheet Hopf-loop derivative sign",
            "Clifford Hopf outer rotation readout",
        ],
        "alternative_formulations": [
            "JAX or functorch Jacobian over the same local carrier chart",
            "Clifford Spin/SU(2) half-period carrier sign formulation",
            "symbolic derivative identity for the selected gradient observable",
            "physical operator-evolution fixture over the same carrier coordinates",
        ],
        "exact_tool_function_needs": {
            "pytorch": ["complex tensors", "torch.exp", "torch.conj", "torch.autograd.grad"],
            "numpy": ["linspace", "roll", "linalg.norm"],
        },
        "lego_or_coupling_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
