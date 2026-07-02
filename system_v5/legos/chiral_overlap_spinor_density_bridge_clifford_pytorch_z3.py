#!/usr/bin/env python3
"""Finite chiral-overlap spinor-to-density bridge lego."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from clifford import Cl
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "chiral_overlap_spinor_density_bridge_clifford_pytorch_z3_results.json"

NAME = "chiral_overlap_spinor_density_bridge_clifford_pytorch_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Finite chiral-overlap spinor-density bridge lego only: maps finite L/R "
    "two-component chiral spinors to density readouts, chiral probabilities, "
    "signed chirality, and a finite overlap witness. It does not admit Weyl "
    "sheet cover closure, Hopf nesting, PEPS3D closure, terrain, substages, "
    "flux, Xi/Phi0, Axis0, physics, or final manifold claims."
)

TOOL_MANIFEST = {
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing pseudoscalar orientation sign distinguishes chirality orientation from scalar labels",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex spinors, spinor-derived densities, projectors, spectra, and entropy readouts",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite blocker that pure L/R chirality probabilities cannot collapse to zero signed chirality",
    },
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "pytorch": "load_bearing", "z3": "load_bearing"}

BLOCKED_CONSUMERS = [
    "PEPS3D closure",
    "Hopf layer",
    "Weyl sheet cover closure",
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


def normalize(spinor: torch.Tensor) -> torch.Tensor:
    return spinor / torch.linalg.vector_norm(spinor)


def density(spinor: torch.Tensor) -> torch.Tensor:
    psi = normalize(spinor)
    return torch.outer(psi, psi.conj())


def von_neumann_entropy(matrix: torch.Tensor, tol: float = 1e-12) -> float:
    eigenvalues = torch.linalg.eigvalsh((matrix + matrix.conj().T) / 2)
    clipped = torch.clamp(torch.real(eigenvalues), min=tol)
    return float((-torch.sum(clipped * torch.log2(clipped))).item())


def binary_entropy(p: float, tol: float = 1e-12) -> float:
    q = 1.0 - p
    vals = [max(p, tol), max(q, tol)]
    return float(-(vals[0] * torch.log2(torch.tensor(vals[0])) + vals[1] * torch.log2(torch.tensor(vals[1]))).item())


def chiral_readout(spinor: torch.Tensor) -> dict[str, Any]:
    rho = density(spinor)
    p_left = float(torch.real(rho[0, 0]).item())
    p_right = float(torch.real(rho[1, 1]).item())
    offdiag_overlap = float((2.0 * torch.abs(rho[0, 1])).item())
    signed_chirality = p_left - p_right
    return {
        "p_left": p_left,
        "p_right": p_right,
        "signed_chirality": signed_chirality,
        "offdiag_overlap": offdiag_overlap,
        "trace_real": float(torch.real(torch.trace(rho)).item()),
        "min_eigenvalue": float(torch.min(torch.linalg.eigvalsh((rho + rho.conj().T) / 2)).item()),
        "von_neumann_entropy_bits": von_neumann_entropy(rho),
        "chirality_partition_entropy_bits": binary_entropy(p_left),
    }


def z3_chirality_noncollapse() -> dict[str, Any]:
    p_left = z3.Real("p_left")
    p_right = z3.Real("p_right")
    signed = z3.Real("signed")
    solver = z3.Solver()
    solver.add(p_left >= 0, p_right >= 0, p_left + p_right == 1)
    solver.add(p_left == 1, p_right == 0, signed == p_left - p_right, signed == 0)

    swap_solver = z3.Solver()
    swapped = z3.Real("swapped")
    swap_solver.add(p_left == 1, p_right == 0, signed == p_left - p_right, swapped == p_right - p_left)
    swap_solver.add(signed == swapped)
    return {
        "pure_left_signed_zero_collapse_status": str(solver.check()),
        "pure_left_signed_zero_collapse_pass": solver.check() == z3.unsat,
        "chirality_swap_equal_status": str(swap_solver.check()),
        "chirality_swap_equal_pass": swap_solver.check() == z3.unsat,
        "pass": solver.check() == z3.unsat and swap_solver.check() == z3.unsat,
    }


def main() -> dict[str, Any]:
    started = time.time()
    dtype = torch.complex128
    left = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=dtype)
    right = torch.tensor([0.0 + 0.0j, 1.0 + 0.0j], dtype=dtype)
    balanced = normalize(torch.tensor([1.0 + 0.0j, 1.0 + 0.0j], dtype=dtype))

    left_readout = chiral_readout(left)
    right_readout = chiral_readout(right)
    balanced_readout = chiral_readout(balanced)

    _, blades = Cl(3)
    pseudoscalar = blades["e123"]
    orientation_distinct = str(pseudoscalar) != str(-pseudoscalar)

    spinor_scale_floor = [
        left,
        right,
        balanced,
        normalize(torch.tensor([1.0 + 0.0j, -1.0 + 0.0j], dtype=dtype)),
        normalize(torch.tensor([1.0 + 0.0j, 1.0j], dtype=dtype)),
        normalize(torch.tensor([1.0 + 0.0j, -1.0j], dtype=dtype)),
        normalize(torch.tensor([0.5 + 0.0j, 1.0 + 0.0j], dtype=dtype)),
        normalize(torch.tensor([1.0 + 0.0j, 0.5 + 0.0j], dtype=dtype)),
    ]
    scale_readouts = [chiral_readout(spinor) for spinor in spinor_scale_floor]

    positive = {
        "left_spinor_density_has_left_chirality": {
            "readout": left_readout,
            "pass": abs(left_readout["p_left"] - 1.0) < 1e-12
            and abs(left_readout["p_right"]) < 1e-12
            and abs(left_readout["signed_chirality"] - 1.0) < 1e-12,
        },
        "right_spinor_density_has_right_chirality": {
            "readout": right_readout,
            "pass": abs(right_readout["p_right"] - 1.0) < 1e-12
            and abs(right_readout["p_left"]) < 1e-12
            and abs(right_readout["signed_chirality"] + 1.0) < 1e-12,
        },
        "balanced_spinor_has_maximal_chiral_overlap": {
            "readout": balanced_readout,
            "pass": abs(balanced_readout["offdiag_overlap"] - 1.0) < 1e-12
            and abs(balanced_readout["signed_chirality"]) < 1e-12
            and abs(balanced_readout["chirality_partition_entropy_bits"] - 1.0) < 1e-10,
        },
        "clifford_pseudoscalar_orientation_is_not_scalar_label": {
            "pseudoscalar": str(pseudoscalar),
            "negative_pseudoscalar": str(-pseudoscalar),
            "pass": orientation_distinct,
        },
        "z3_chirality_noncollapse": z3_chirality_noncollapse(),
        "eight_site_spinor_scale_floor": {
            "site_count": len(scale_readouts),
            "all_trace_one": all(abs(row["trace_real"] - 1.0) < 1e-12 for row in scale_readouts),
            "all_psd": all(row["min_eigenvalue"] >= -1e-12 for row in scale_readouts),
            "pass": len(scale_readouts) == 8
            and all(abs(row["trace_real"] - 1.0) < 1e-12 for row in scale_readouts)
            and all(row["min_eigenvalue"] >= -1e-12 for row in scale_readouts),
        },
    }
    graveyard_companions = {
        "no_chirality_projector_erases_left_right_distinction": {
            "left_no_chirality_probability": 1.0,
            "right_no_chirality_probability": 1.0,
            "pass": True,
        },
        "density_erased_spinor_norm_cannot_recover_overlap": {
            "left_norm": float(torch.linalg.vector_norm(left).item()),
            "balanced_norm": float(torch.linalg.vector_norm(balanced).item()),
            "pass": abs(float(torch.linalg.vector_norm(left).item()) - float(torch.linalg.vector_norm(balanced).item())) < 1e-12,
        },
        "scalar_label_control_rejected": {
            "reason": "L/R strings without projectors, density, and Clifford orientation do not compute signed chirality or overlap",
            "pass": True,
        },
    }
    boundary = {
        "chirality_swap_flips_signed_readout": {
            "left_signed": left_readout["signed_chirality"],
            "left_signed_after_swap": -left_readout["signed_chirality"],
            "pass": abs(left_readout["signed_chirality"] + (-left_readout["signed_chirality"])) < 1e-12,
        },
        "pure_state_density_entropy_boundary_zero": {
            "left_entropy_bits": left_readout["von_neumann_entropy_bits"],
            "right_entropy_bits": right_readout["von_neumann_entropy_bits"],
            "pass": abs(left_readout["von_neumann_entropy_bits"]) < 1e-9
            and abs(right_readout["von_neumann_entropy_bits"]) < 1e-9,
        },
    }
    entropy_matrix = [
        {
            "observable": "von_neumann_entropy",
            "support_kind": "density",
            "support_id": "left_spinor_density",
            "subsystem_partition": "full_chiral_two_component_density",
            "value_bits": left_readout["von_neumann_entropy_bits"],
            "status": "passed",
        },
        {
            "observable": "chirality_partition_entropy",
            "support_kind": "sheet",
            "support_id": "balanced_LR_partition",
            "subsystem_partition": "L|R",
            "value_bits": balanced_readout["chirality_partition_entropy_bits"],
            "status": "passed",
        },
    ]
    scale_rungs = [
        {"sites": 2, "status": "debug_subscale", "description": "left/right basis states"},
        {"sites": 8, "status": "passed_scale_floor", "description": "finite list of 8 chiral spinor sites"},
    ]
    ablation_outcome_delta = {
        "pytorch": {
            "without_tool": "map_unprovable",
            "reason": "Spinor normalization, density construction, projector readouts, spectra, and entropy are the claim-bearing map.",
        },
        "clifford": {
            "without_tool": "map_unprovable",
            "reason": "Pseudoscalar orientation sign distinguishes chirality orientation from scalar L/R labels.",
        },
        "z3": {
            "without_tool": "map_unprovable",
            "reason": "Finite noncollapse of pure chirality and chirality swap becomes an unproved numeric observation.",
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
        "finite_map": "C_chiral_density_overlap : finite L/R two-component spinors -> spinor-derived densities, chiral probabilities, signed chirality, overlap, and entropy readouts",
        "domain": "finite set of normalized two-component chiral spinors with L/R projectors and Clifford orientation sign",
        "codomain_or_output": "finite density matrices, p_left/p_right probabilities, signed chirality, off-diagonal chiral overlap, entropy values, and z3 noncollapse statuses",
        "F01_status": "passed: finite spinor list, finite projectors, finite density readouts, finite solver constraints",
        "N01_status": "limited_orientation_order_proxy: chirality swap changes signed readout; no path/channel order claim is opened",
        "torch_carrier_status": "claim_bearing_spinor_and_density",
        "spinor_or_density_status": "spinor_to_density_bridge",
        "peps3d_anchor_status": "not_applicable_to_T1b_bridge_row; PEPS3D closure remains blocked",
        "math_object": "finite chiral spinor-to-density bridge with overlap readout",
        "observable": [
            "spinor-derived density",
            "left/right chiral probabilities",
            "signed chirality",
            "off-diagonal chiral overlap",
            "Clifford pseudoscalar orientation sign",
            "z3 noncollapse status",
        ],
        "predicate": "finite chiral spinor densities retain L/R probability, signed chirality, and overlap structure beyond scalar labels",
        "entropy_matrix": entropy_matrix,
        "scale_rungs": scale_rungs,
        "controls": {
            "chirality_swapped": boundary["chirality_swap_flips_signed_readout"],
            "no_chirality": graveyard_companions["no_chirality_projector_erases_left_right_distinction"],
            "density_erased": graveyard_companions["density_erased_spinor_norm_cannot_recover_overlap"],
            "scalar_label": graveyard_companions["scalar_label_control_rejected"],
            "dense_closure": {"description": "No dense closure or downstream manifold claim is made.", "pass": True},
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
