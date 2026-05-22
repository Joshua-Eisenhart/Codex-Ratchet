#!/usr/bin/env python3
"""Bounded bipartite entropy/topology coexistence receipt.

This packet links the repaired GUDHI bipartite topology lego to the canonical
bipartite entropy-cut lego on one finite two-qubit Schmidt-family grid. It checks that the
same finite states carry both a cut-entropy scalar and a phase-sensitive
topological circle witness.  It is not bridge, QIT, GStack, or axis evidence.
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


classification = "supporting"

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
PARENT_RESULT_NAMES = [
    "gudhi_bipartite_entangled_results.json",
    "lego_entropy_bipartite_cut_results.json",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density matrices and cut entropy evaluation"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistent H1 witness for phase-sensitive equator"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite endpoint/high-entropy disjointness fence"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing finite grid and correlation checks"},
    "scipy": {"tried": False, "used": False, "reason": "not needed; no matrix exponentials or optimization"},
    "sympy": {"tried": False, "used": False, "reason": "not needed; no symbolic simplification beyond z3 inequality fence"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed; z3 covers this bounded fence"},
    "pyg": {"tried": False, "used": False, "reason": "not needed in this entropy/topology packet"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed; no graph path computation"},
    "xgi": {"tried": False, "used": False, "reason": "not needed; no hypergraph representation"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed; no cell complex representation"},
    "qutip": {"tried": False, "used": False, "reason": "not installed in this environment"},
    "qiskit": {"tried": False, "used": False, "reason": "not installed in this environment"},
    "clifford": {"tried": False, "used": False, "reason": "not needed; no geometric algebra action"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; no Riemannian metric layer"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "gudhi": "load_bearing",
    "z3": "load_bearing",
    "numpy": "load_bearing",
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

TOL = 1e-10


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parent_summaries() -> list[dict]:
    rows = []
    for name in PARENT_RESULT_NAMES:
        path = RESULTS_DIR / name
        if not path.exists():
            rows.append({"path": str(path), "exists": False, "all_pass": False})
            continue
        payload = read_json(path)
        raw = path.read_bytes()
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        all_pass = payload.get("all_pass")
        if all_pass is None:
            all_pass = summary.get("all_pass")
        rows.append(
            {
                "path": str(path),
                "exists": True,
                "classification": payload.get("classification"),
                "all_pass": bool(all_pass),
                "sha256": hashlib.sha256(raw).hexdigest(),
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


def offdiag_radius(theta: float) -> float:
    return float(math.sin(theta) / 2.0)


def grid_rows() -> list[dict]:
    thetas = [0.0, math.pi / 6.0, math.pi / 3.0, math.pi / 2.0, 2.0 * math.pi / 3.0, 5.0 * math.pi / 6.0, math.pi]
    phis = [2.0 * math.pi * i / 24.0 for i in range(24)]
    rows = []
    for theta in thetas:
        for phi in phis:
            rho = bell_density(theta, phi)
            rho_a = partial_trace_b(rho)
            entropy = von_neumann_entropy(rho_a)
            re = float(torch.real(rho[0, 3]).item())
            im = float(torch.imag(rho[0, 3]).item())
            rows.append(
                {
                    "theta": theta,
                    "phi": phi,
                    "cut_entropy": entropy,
                    "offdiag_re": re,
                    "offdiag_im": im,
                    "offdiag_radius": math.sqrt(re * re + im * im),
                    "analytic_radius": offdiag_radius(theta),
                }
            )
    return rows


def rips_h1(points: np.ndarray, max_edge_length: float) -> dict:
    tree = gudhi.RipsComplex(points=points, max_edge_length=max_edge_length).create_simplex_tree(max_dimension=2)
    persistence = tree.persistence()
    h1 = [pair for dim, pair in persistence if dim == 1 and math.isfinite(pair[1])]
    max_persistence = max((death - birth for birth, death in h1), default=0.0)
    return {"h1_count": len(h1), "h1_max_persistence": float(max_persistence)}


def rips_sensitivity(points: np.ndarray, lengths: list[float]) -> dict:
    rows = []
    for length in lengths:
        rows.append({"max_edge_length": length, **rips_h1(points, length)})
    return {
        "rows": rows,
        "positive_count": sum(1 for row in rows if row["h1_count"] > 0 and row["h1_max_persistence"] > 0.1),
    }


def z3_entropy_endpoint_fence(
    max_endpoint_entropy: float,
    min_high_entropy: float,
    max_endpoint_radius: float,
    min_high_radius: float,
) -> dict:
    entropy = Real("entropy")
    radius = Real("radius")
    checks = {}
    solver = Solver()
    solver.add(entropy <= max_endpoint_entropy + 1e-9, entropy >= min_high_entropy - 1e-9)
    checks["measured_endpoint_entropy_disjoint_from_high_entropy"] = str(solver.check())
    solver = Solver()
    solver.add(radius <= max_endpoint_radius + 1e-9, radius >= min_high_radius - 1e-9)
    checks["measured_endpoint_radius_disjoint_from_high_radius"] = str(solver.check())
    return {
        "computed_bounds": {
            "max_endpoint_entropy": max_endpoint_entropy,
            "min_high_entropy": min_high_entropy,
            "max_endpoint_radius": max_endpoint_radius,
            "min_high_radius": min_high_radius,
        },
        "checks": checks,
        "pass": all(value == str(unsat) for value in checks.values()),
    }


def main() -> int:
    parents = parent_summaries()
    rows = grid_rows()
    entropy = np.array([row["cut_entropy"] for row in rows])
    radius = np.array([row["offdiag_radius"] for row in rows])
    analytic_radius = np.array([row["analytic_radius"] for row in rows])
    equator = [row for row in rows if abs(row["theta"] - math.pi / 2.0) < 1e-12]
    product = [row for row in rows if row["theta"] in (0.0, math.pi)]

    equator_points = np.array([[row["cut_entropy"], row["offdiag_re"], row["offdiag_im"]] for row in equator])
    phase_blind_points = np.array([[row["cut_entropy"]] for row in equator])
    rips_lengths = [0.6, 0.75, 0.9, 1.05]
    equator_h1_sensitivity = rips_sensitivity(equator_points, rips_lengths)
    phase_blind_h1_sensitivity = rips_sensitivity(phase_blind_points, rips_lengths)
    equator_h1 = next(row for row in equator_h1_sensitivity["rows"] if row["max_edge_length"] == 0.9)
    phase_blind_h1 = next(row for row in phase_blind_h1_sensitivity["rows"] if row["max_edge_length"] == 0.9)
    max_endpoint_entropy = float(max(row["cut_entropy"] for row in product))
    max_endpoint_radius = float(max(row["offdiag_radius"] for row in product))
    high_entropy_rows = [row for row in rows if row["cut_entropy"] > 0.9]
    min_high_entropy = float(min(row["cut_entropy"] for row in high_entropy_rows))
    min_high_radius = float(min(row["offdiag_radius"] for row in high_entropy_rows))
    correlation = float(np.corrcoef(entropy, radius)[0, 1])

    positive = {
        "parents_exist_and_pass": {
            "parents": parents,
            "pass": bool(parents and all(parent.get("exists") and parent.get("all_pass") for parent in parents)),
        },
        "same_finite_grid_carries_entropy_and_topology": {
            "state_count": len(rows),
            "entropy_min": float(np.min(entropy)),
            "entropy_max": float(np.max(entropy)),
            "radius_min": float(np.min(radius)),
            "radius_max": float(np.max(radius)),
            "pass": bool(len(rows) == 168 and np.max(entropy) > 0.99 and np.max(radius) > 0.49),
        },
        "analytic_radius_matches_joint_offdiag": {
            "max_abs_error": float(np.max(np.abs(radius - analytic_radius))),
            "pass": bool(np.max(np.abs(radius - analytic_radius)) < 1e-10),
        },
        "high_entropy_equator_has_phase_topology": {
            **equator_h1,
            "sensitivity": equator_h1_sensitivity,
            "pass": bool(equator_h1["h1_count"] > 0 and equator_h1["h1_max_persistence"] > 0.1),
        },
        "entropy_and_topological_radius_are_coupled": {
            "pearson_entropy_radius": correlation,
            "pass": bool(correlation > 0.85),
        },
    }
    negative = {
        "phase_blind_entropy_only_loses_circle": {
            **phase_blind_h1,
            "sensitivity": phase_blind_h1_sensitivity,
            "pass": bool(phase_blind_h1["h1_count"] == 0 and phase_blind_h1_sensitivity["positive_count"] == 0),
        },
        "product_endpoints_have_zero_entropy_and_zero_radius": {
            "endpoint_count": len(product),
            "max_endpoint_entropy": max_endpoint_entropy,
            "max_endpoint_radius": max_endpoint_radius,
            "pass": bool(max_endpoint_entropy < 1e-10 and max_endpoint_radius < 1e-10),
        },
        "z3_entropy_endpoint_fence": z3_entropy_endpoint_fence(
            max_endpoint_entropy=max_endpoint_entropy,
            min_high_entropy=min_high_entropy,
            max_endpoint_radius=max_endpoint_radius,
            min_high_radius=min_high_radius,
        ),
    }
    boundary = {
        "finite_grid_only": {
            "theta_count": 7,
            "phi_count": 24,
            "pass": len(rows) == 168,
        },
        "same_state_not_broader_coupling_claim": {
            "pass": True,
            "note": "This only links cut entropy and topology on one finite two-qubit Schmidt-family grid.",
        },
        "no_promotion_claim": {
            "pass": True,
            "note": "No bridge, GStack, axis, QIT, nonclassical admission, or broad entropy-geometry closure.",
        },
    }
    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    result = {
        "name": "bipartite_entropy_topology_coexistence",
        "classification": "supporting",
        "classification_note": "Finite bipartite entropy/topology coexistence receipt; queue evidence only.",
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "parents": parents,
        "finite_state": {
            "theta_count": 7,
            "phi_count": 24,
            "sample_rows": rows[:8],
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "state_count": len(rows),
            "equator_h1_count": equator_h1["h1_count"],
            "equator_h1_max_persistence": equator_h1["h1_max_persistence"],
            "phase_blind_h1_count": phase_blind_h1["h1_count"],
            "entropy_radius_correlation": correlation,
            "promotion_allowed": False,
            "scope_note": "Same-state entropy/topology coupling candidate; broader assembly still blocked.",
        },
        "all_pass": all_pass,
        "divergence_log": (
            "This sim adds a fresh coupling receipt between the repaired GUDHI bipartite topology "
            "lego and the canonical bipartite cut entropy lego. It does not promote entropy/topology "
            "closure or any bridge/nonclassical claim."
        ),
    }
    result = apply_default_receipt_boundary(
        result,
        source_name="sim_bipartite_entropy_topology_coexistence",
        target="Use as bounded bipartite entropy/topology coexistence evidence before broader assembly.",
    )
    result["promotion_condition"] = "Requires broader bipartite assembly audit and explicit stage-gate admission."
    result["blocked_until"] = "broader bipartite entropy/topology assembly and stage-gate admission"

    out_path = RESULTS_DIR / "bipartite_entropy_topology_coexistence_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
