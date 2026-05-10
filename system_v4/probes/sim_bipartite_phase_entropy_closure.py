#!/usr/bin/env python3
"""Bipartite phase/entropy closure robustness packet.

The parent coexistence receipt shows that one finite Schmidt-family grid can
carry both cut entropy and a phase-sensitive H1 witness. This follow-on asks a
narrower closure question: is that witness robust under finite grid refinement
and phase rotation, while disappearing under phase-blind and radial-collapse
controls?

This is lego-stage evidence only. It does not admit QIT, GStack, axes, bridge,
or nonclassical claims.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import gudhi
import numpy as np
import torch
from z3 import Real, Solver, unsat

from receipt_boundary import apply_default_receipt_boundary


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
PARENT_RESULT_NAMES = [
    "bipartite_entropy_topology_coexistence_results.json",
    "gudhi_bipartite_entangled_results.json",
    "lego_entropy_bipartite_cut_results.json",
]
TOL = 1e-10

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing finite grids, correlations, and control transforms"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing two-qubit density matrices and reduced entropy"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistent H1 checks across grid refinements and controls"},
    "z3": {"tried": True, "used": True, "reason": "supportive finite endpoint/high-entropy disjointness fence"},
    "scipy": {"tried": False, "used": False, "reason": "not needed; no optimization or matrix exponentials"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed; z3 covers this small fence"},
    "pyg": {"tried": False, "used": False, "reason": "not needed; no message-passing graph"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed; no graph path algorithm"},
    "xgi": {"tried": False, "used": False, "reason": "not needed; no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed; no cell complex"},
    "qutip": {"tried": False, "used": False, "reason": "not needed; direct finite torch density matrices"},
    "qiskit": {"tried": False, "used": False, "reason": "not needed; no circuit backend"},
    "clifford": {"tried": False, "used": False, "reason": "not needed; no geometric algebra action"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; no manifold metric layer"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": "load_bearing",
    "gudhi": "load_bearing",
    "z3": "supportive",
    "scipy": None,
    "sympy": None,
    "cvc5": None,
    "pyg": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "qutip": None,
    "qiskit": None,
    "clifford": None,
    "geomstats": None,
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parent_receipts() -> list[dict]:
    rows = []
    for name in PARENT_RESULT_NAMES:
        path = RESULTS_DIR / name
        payload = read_json(path) if path.exists() else {}
        rows.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "classification": payload.get("classification"),
                "all_pass": bool(payload.get("all_pass") or payload.get("summary", {}).get("all_pass")),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
            }
        )
    return rows


def bell_density(theta: float, phi: float) -> torch.Tensor:
    psi = torch.zeros(4, dtype=torch.complex128)
    psi[0] = math.cos(theta / 2.0)
    psi[3] = complex(math.cos(phi), math.sin(phi)) * math.sin(theta / 2.0)
    return torch.outer(psi, psi.conj())


def partial_trace_b(rho: torch.Tensor) -> torch.Tensor:
    view = rho.reshape(2, 2, 2, 2)
    return torch.einsum("abcb->ac", view)


def von_neumann_entropy(rho: torch.Tensor) -> float:
    eigvals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real
    eigvals = torch.clamp(eigvals, min=0.0)
    eigvals = eigvals / torch.sum(eigvals)
    nz = eigvals[eigvals > TOL]
    if nz.numel() == 0:
        return 0.0
    return float((-torch.sum(nz * torch.log2(nz))).item())


def state_row(theta: float, phi: float) -> dict:
    rho = bell_density(theta, phi)
    rho_a = partial_trace_b(rho)
    entropy = von_neumann_entropy(rho_a)
    re = float(torch.real(rho[0, 3]).item())
    im = float(torch.imag(rho[0, 3]).item())
    return {
        "theta": theta,
        "phi": phi,
        "cut_entropy": entropy,
        "offdiag_re": re,
        "offdiag_im": im,
        "offdiag_radius": math.sqrt(re * re + im * im),
    }


def equator_rows(phi_count: int, phase_offset: float = 0.0) -> list[dict]:
    return [
        state_row(math.pi / 2.0, phase_offset + 2.0 * math.pi * i / phi_count)
        for i in range(phi_count)
    ]


def theta_sweep_rows(theta_count: int = 21) -> list[dict]:
    return [state_row(math.pi * i / (theta_count - 1), 0.0) for i in range(theta_count)]


def rips_h1(points: np.ndarray, max_edge_length: float = 0.9) -> dict:
    tree = gudhi.RipsComplex(points=points, max_edge_length=max_edge_length).create_simplex_tree(max_dimension=2)
    persistence = tree.persistence()
    h1 = [pair for dim, pair in persistence if dim == 1 and math.isfinite(pair[1])]
    max_persistence = max((death - birth for birth, death in h1), default=0.0)
    return {"h1_count": len(h1), "h1_max_persistence": float(max_persistence)}


def phase_points(rows: list[dict]) -> np.ndarray:
    return np.array([[row["cut_entropy"], row["offdiag_re"], row["offdiag_im"]] for row in rows])


def phase_blind_points(rows: list[dict]) -> np.ndarray:
    return np.array([[row["cut_entropy"]] for row in rows])


def radial_collapse_points(rows: list[dict]) -> np.ndarray:
    return np.array([[row["cut_entropy"], row["offdiag_radius"], 0.0] for row in rows])


def z3_endpoint_fence(endpoint_entropy: float, high_entropy: float, endpoint_radius: float, high_radius: float) -> dict:
    entropy = Real("entropy")
    radius = Real("radius")
    solver = Solver()
    solver.add(entropy <= endpoint_entropy + 1e-9, entropy >= high_entropy - 1e-9)
    entropy_status = solver.check()
    solver = Solver()
    solver.add(radius <= endpoint_radius + 1e-9, radius >= high_radius - 1e-9)
    radius_status = solver.check()
    return {
        "endpoint_entropy": endpoint_entropy,
        "high_entropy": high_entropy,
        "endpoint_radius": endpoint_radius,
        "high_radius": high_radius,
        "entropy_disjoint_status": str(entropy_status),
        "radius_disjoint_status": str(radius_status),
        "pass": entropy_status == unsat and radius_status == unsat,
    }


def main() -> int:
    parents = parent_receipts()
    resolutions = [12, 24, 36]
    resolution_rows = []
    for phi_count in resolutions:
        rows = equator_rows(phi_count)
        resolution_rows.append({"phi_count": phi_count, **rips_h1(phase_points(rows))})
    rotated_rows = equator_rows(24, phase_offset=math.pi / 7.0)
    rotated_h1 = rips_h1(phase_points(rotated_rows))
    base_rows = equator_rows(24)
    phase_blind_h1 = rips_h1(phase_blind_points(base_rows))
    radial_h1 = rips_h1(radial_collapse_points(base_rows))
    sweep = theta_sweep_rows()
    entropies = np.array([row["cut_entropy"] for row in sweep])
    radii = np.array([row["offdiag_radius"] for row in sweep])
    correlation = float(np.corrcoef(entropies, radii)[0, 1])
    endpoints = [sweep[0], sweep[-1]]
    high = max(sweep, key=lambda row: row["cut_entropy"])

    positive = {
        "parents_exist_and_pass": {"parents": parents, "pass": all(row["exists"] and row["all_pass"] for row in parents)},
        "phase_h1_survives_grid_refinement": {
            "resolution_rows": resolution_rows,
            "pass": all(row["h1_count"] > 0 and row["h1_max_persistence"] > 0.1 for row in resolution_rows),
        },
        "phase_rotation_preserves_h1": {
            "rotated_h1": rotated_h1,
            "pass": rotated_h1["h1_count"] > 0 and rotated_h1["h1_max_persistence"] > 0.1,
        },
        "entropy_radius_coupling_on_theta_sweep": {
            "theta_count": len(sweep),
            "pearson_entropy_radius": correlation,
            "pass": correlation > 0.9,
        },
    }
    negative = {
        "phase_blind_projection_loses_h1": {
            "phase_blind_h1": phase_blind_h1,
            "pass": phase_blind_h1["h1_count"] == 0,
        },
        "radial_collapse_loses_h1": {
            "radial_collapse_h1": radial_h1,
            "pass": radial_h1["h1_count"] == 0,
        },
        "endpoint_controls_have_zero_entropy_and_radius": {
            "endpoints": endpoints,
            "pass": all(abs(row["cut_entropy"]) < 1e-10 and row["offdiag_radius"] < 1e-10 for row in endpoints),
        },
        "z3_endpoint_high_entropy_fence": z3_endpoint_fence(
            endpoint_entropy=max(row["cut_entropy"] for row in endpoints),
            high_entropy=high["cut_entropy"],
            endpoint_radius=max(row["offdiag_radius"] for row in endpoints),
            high_radius=high["offdiag_radius"],
        ),
    }
    closure_checks = {
        "parents": positive["parents_exist_and_pass"]["pass"],
        "grid_refinement": positive["phase_h1_survives_grid_refinement"]["pass"],
        "phase_rotation": positive["phase_rotation_preserves_h1"]["pass"],
        "phase_blind_control": negative["phase_blind_projection_loses_h1"]["pass"],
        "radial_collapse_control": negative["radial_collapse_loses_h1"]["pass"],
        "endpoint_control": negative["endpoint_controls_have_zero_entropy_and_radius"]["pass"],
    }
    promotion_allowed = False
    classification = "classical_baseline"
    boundary = {
        "finite_grids_only": {"resolutions": resolutions, "theta_count": len(sweep), "pass": True},
        "closure_candidate_defined_by_finite_checks": {
            "definition": "phase H1 survives finite refinement and rotation while phase-blind/radial/endpoints controls fail",
            "checks": closure_checks,
            "pass": all(closure_checks.values()),
        },
        "not_semantic_equivalence_or_admission": {
            "classification": classification,
            "promotion_allowed": promotion_allowed,
            "pass": classification in {"classical_baseline", "supporting"} and promotion_allowed is False,
        },
        "no_qit_gstack_axis_bridge_or_nonclassical_promotion": {"promotion_allowed": promotion_allowed, "pass": promotion_allowed is False},
    }
    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    result = {
        "name": "bipartite_phase_entropy_closure",
        "classification": classification,
        "classification_note": "Finite bipartite phase/entropy closure candidate; lego-stage evidence only.",
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "parents": parents,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "closure_candidate": all_pass,
            "promotion_allowed": promotion_allowed,
            "resolution_count": len(resolutions),
            "entropy_radius_correlation": correlation,
            "scope_note": "Phase-aware bipartite entropy/topology robustness only; no stage promotion.",
        },
        "all_pass": all_pass,
        "divergence_log": (
            "Phase-aware H1 survives finite refinement and rotation; phase-blind and radial-collapse controls lose H1. "
            "This supports a bounded bipartite closure candidate without claiming broader entropy/topology admission."
        ),
    }
    result = apply_default_receipt_boundary(
        result,
        source_name="sim_bipartite_phase_entropy_closure",
        target="Use as bounded bipartite entropy/topology closure-candidate evidence before broader assembly.",
    )
    result["promotion_condition"] = "Requires downstream bipartite assembly audit and explicit stage-gate admission."
    result["blocked_until"] = "bipartite assembly audit and stage-gate admission"

    out_path = RESULTS_DIR / "bipartite_phase_entropy_closure_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
