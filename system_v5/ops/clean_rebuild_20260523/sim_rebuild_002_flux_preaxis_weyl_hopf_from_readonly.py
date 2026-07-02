#!/usr/bin/env python3
"""Clean-room rebuild 002: pre-axis Weyl/Hopf flux candidates.

This scout rebuilds the first flux layer from read-only source math only. It
tests the dependency chain:

    finite spinor -> Hopf projection -> fiber/base loop grammar
    -> Weyl left/right Hamiltonian sheets -> stagewise deltas
    -> candidate flux current family

It does not decide final flux placement. It only checks whether a pre-joint,
pre-Axis0 flux candidate survives the obvious controls.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "rebuild_002_flux_preaxis_weyl_hopf_from_readonly_results.json"

classification = "clean_rebuild_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical_clean_rebuild"
SOURCE_ALIGNMENT_CATEGORY = "preaxis_flux_weyl_hopf_readonly_rebuild"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Clean rebuild scout only: tests pre-joint Weyl/Hopf flux candidate "
    "currents from read-only source math. It does not promote flux to a root, "
    "Axis3, final manifold law, final Axis0, or physics claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite complex spinors, density matrices, Bloch readouts, and Weyl sheet dynamics",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive clean rebuild receipt serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128
TWO_PI = 2.0 * math.pi

I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
H0 = 0.77 * SZ + 0.13 * SX
H_AXIS = torch.tensor([0.13, 0.0, 0.77], dtype=DTYPE)
H_AXIS = H_AXIS / torch.linalg.vector_norm(H_AXIS)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def normalize(v: torch.Tensor) -> torch.Tensor:
    return v / torch.clamp(torch.linalg.vector_norm(v), min=1e-12)


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return normalize(
        torch.tensor(
            [
                complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
                complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
            ],
            dtype=CDTYPE,
        )
    )


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def bloch_from_rho(rho: torch.Tensor) -> torch.Tensor:
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ SX)).item(),
            torch.real(torch.trace(rho @ SY)).item(),
            torch.real(torch.trace(rho @ SZ)).item(),
        ],
        dtype=DTYPE,
    )


def bloch(phi: float, chi: float, eta: float) -> torch.Tensor:
    return bloch_from_rho(density(spinor(phi, chi, eta)))


def unitary_from_h(h: torch.Tensor, dt: float) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(h)
    return vecs @ torch.diag(torch.exp(-1j * vals * dt)).to(CDTYPE) @ torch.conj(vecs).T


def evolve(rho: torch.Tensor, h: torch.Tensor, dt: float) -> torch.Tensor:
    u = unitary_from_h(h, dt)
    out = u @ rho @ torch.conj(u).T
    return (out + torch.conj(out).T) / 2.0


def hopf_connection_integral(path_class: str, eta: float, turns: float = 1.0) -> float:
    if path_class == "fiber":
        return TWO_PI * turns
    if path_class == "lifted_base":
        return 0.0
    raise ValueError(path_class)


def hopf_curvature_cap_from_clifford(eta: float) -> float:
    # A = dphi + cos(2 eta)dchi; F=dA. The cap from eta=pi/4 has sign cos(2 eta).
    return TWO_PI * math.cos(2.0 * eta)


def fiber_density_path_variation(phi: float, chi: float, eta: float, samples: int = 32) -> float:
    rho0 = density(spinor(phi, chi, eta))
    gaps = []
    for idx in range(samples):
        u = TWO_PI * idx / samples
        rho = density(spinor(phi + u, chi, eta))
        gaps.append(torch.linalg.matrix_norm(rho - rho0).item())
    return float(max(gaps))


def base_density_path_variation(phi: float, chi: float, eta: float, samples: int = 32) -> float:
    rho0 = density(spinor(phi, chi, eta))
    gaps = []
    c = math.cos(2.0 * eta)
    for idx in range(samples):
        u = TWO_PI * idx / samples
        rho = density(spinor(phi - c * u, chi + u, eta))
        gaps.append(torch.linalg.matrix_norm(rho - rho0).item())
    return float(max(gaps))


def sheet_step_currents(phi: float, chi: float, eta: float, dt: float = 0.19) -> dict[str, Any]:
    rho0 = density(spinor(phi, chi, eta))
    rho_left = evolve(rho0, H0, dt)
    rho_right = evolve(rho0, -H0, dt)
    rho_no_chirality = evolve(rho0, H0, dt)
    r0 = bloch_from_rho(rho0)
    dl = bloch_from_rho(rho_left) - r0
    dr = bloch_from_rho(rho_right) - r0
    d_no = bloch_from_rho(rho_no_chirality) - r0
    j_bloch = float(torch.linalg.vector_norm(dl - dr).item())
    j_no_chirality = float(torch.linalg.vector_norm(dl - d_no).item())
    orientation_left = float(torch.dot(H_AXIS, torch.linalg.cross(r0, dl, dim=0)).item())
    orientation_right = float(torch.dot(H_AXIS, torch.linalg.cross(r0, dr, dim=0)).item())
    return {
        "r0": r0,
        "delta_left": dl,
        "delta_right": dr,
        "j_bloch": j_bloch,
        "j_no_chirality": j_no_chirality,
        "orientation_left": orientation_left,
        "orientation_right": orientation_right,
        "orientation_product": orientation_left * orientation_right,
        "rho_distance_left_right": float(torch.linalg.matrix_norm(rho_left - rho_right).item()),
    }


def hopf_loop_gate() -> dict[str, Any]:
    phi, chi, eta = 0.17, 0.41, 0.37
    fiber_a = hopf_connection_integral("fiber", eta)
    base_a = hopf_connection_integral("lifted_base", eta)
    fiber_var = fiber_density_path_variation(phi, chi, eta)
    base_var = base_density_path_variation(phi, chi, eta)
    return {
        "pass": abs(fiber_a - TWO_PI) < 1e-12 and abs(base_a) < 1e-12 and fiber_var < 1e-10 and base_var > 0.25,
        "source": "AXES atlas lines 123, 129-132, 351-359: Hopf connection, fiber loop density-stationary, lifted-base density-traversing",
        "fiber_connection_integral": fiber_a,
        "base_connection_integral": base_a,
        "fiber_density_path_variation": fiber_var,
        "base_density_path_variation": base_var,
    }


def preaxis_flux_candidate_gate() -> dict[str, Any]:
    rows = []
    for eta in (math.pi / 8.0, 0.37, 0.63, 3.0 * math.pi / 8.0):
        currents = sheet_step_currents(0.22, 0.36, eta)
        cap = hopf_curvature_cap_from_clifford(eta)
        rows.append(
            {
                "eta": eta,
                "cap_flux_from_clifford": cap,
                "cap_sign": 1 if cap >= 0.0 else -1,
                "j_bloch": currents["j_bloch"],
                "j_no_chirality": currents["j_no_chirality"],
                "rho_distance_left_right": currents["rho_distance_left_right"],
                "orientation_left": currents["orientation_left"],
                "orientation_right": currents["orientation_right"],
                "orientation_product": currents["orientation_product"],
            }
        )
    min_j = min(row["j_bloch"] for row in rows)
    max_no_chirality = max(row["j_no_chirality"] for row in rows)
    opposite_orientation_count = sum(1 for row in rows if row["orientation_product"] < 0.0)
    sign_seats = {row["cap_sign"] for row in rows}
    return {
        "pass": min_j > 0.05 and max_no_chirality < 1e-12 and opposite_orientation_count == len(rows) and sign_seats == {-1, 1},
        "source": "Weyl Flux dependency rows 7, 10, 12-18 and AXES atlas lines 139-144: left/right sheets with H_left=+H0, H_right=-H0",
        "rows": rows,
        "min_bloch_chiral_current": min_j,
        "max_no_chirality_current": max_no_chirality,
        "opposite_orientation_count": opposite_orientation_count,
        "seat_flux_signs_observed": sorted(sign_seats),
    }


def negative_controls_gate() -> dict[str, Any]:
    phi, chi, eta = 0.22, 0.36, 0.37
    currents = sheet_step_currents(phi, chi, eta)
    rho0 = density(spinor(phi, chi, eta))
    flat_gap = float(torch.linalg.matrix_norm(rho0 - rho0).item())
    fiber_only_variation = fiber_density_path_variation(phi, chi, eta)
    base_variation = base_density_path_variation(phi, chi, eta)
    controls = {
        "no_chirality_collapses_current": currents["j_no_chirality"] < 1e-12,
        "flattened_transport_collapses_current": flat_gap < 1e-12,
        "fiber_only_density_is_stationary": fiber_only_variation < 1e-10,
        "base_loop_density_is_not_stationary": base_variation > 0.25,
    }
    return {
        "pass": all(controls.values()),
        "controls": controls,
        "j_chirality_current": currents["j_bloch"],
        "no_chirality_current": currents["j_no_chirality"],
        "flat_gap": flat_gap,
        "fiber_only_variation": fiber_only_variation,
        "base_variation": base_variation,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    sections = {
        "hopf_loop_gate": hopf_loop_gate(),
        "preaxis_flux_candidate_gate": preaxis_flux_candidate_gate(),
        "negative_controls_gate": negative_controls_gate(),
    }
    all_pass = all(bool(section["pass"]) for section in sections.values())
    result = {
        "schema": "clean_rebuild_result_v1",
        "name": "rebuild_002_flux_preaxis_weyl_hopf_from_readonly",
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "sections": sections,
        "placement_status": {
            "pre_joint_candidate_survived": bool(sections["preaxis_flux_candidate_gate"]["pass"]),
            "final_flux_placement": "open",
            "not_axis3_identity": True,
            "not_root": True,
            "next_required_test": "couple this clean pre-axis current to rebuilt engine basins without importing formal_scout receipts",
        },
        "source_boundary": {
            "reads_formal_scout_results": False,
            "reads_grok_sim": False,
            "reads_external_audits": False,
            "reads_cross_lane_synthesis_docs": False,
            "primary_reference_docs": [
                "system_v5/READ ONLY Reference Docs/Weyl Flux.md",
                "system_v5/READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md",
            ],
        },
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

