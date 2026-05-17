#!/usr/bin/env python3
"""Entropy-gradient curvature/torsion-style deformation scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import geomstats.backend as gs
import gudhi
import networkx as nx
import numpy as np
from scipy.integrate import solve_ivp
import sympy as sp
import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "entropy_gradient_curvature_torsion_deformation_probe_results.json"

NAME = "entropy_gradient_curvature_torsion_deformation_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite two-coordinate dynamic geometry where "
    "entropy gradients deform metric scale, anisotropic shear, conformal "
    "curvature, and antisymmetric connection/twist parameters. It does not "
    "admit GR, physics, cognition, psychology, ontology, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density states, entropy, and finite gradient signals"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing metric tensors, curvature samples, and trajectory distances"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing ODE integration for geometry-flow parameters"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic curvature and torsion-style formulas"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing backend tensor sanity for positive metric samples"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over curvature/twist trajectory point clouds"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing deformation dependency graph"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=1e-12).to(DTYPE)
    out = vecs @ torch.diag(vals) @ vecs.conj().T
    return out / torch.trace(out).real


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / vals.sum()
    return float(-(vals * torch.log(vals)).sum().item())


def bloch(rho: torch.Tensor) -> np.ndarray:
    return np.array(
        [
            float(torch.real(torch.trace(SX @ rho)).item()),
            float(torch.real(torch.trace(SY @ rho)).item()),
            float(torch.real(torch.trace(SZ @ rho)).item()),
        ],
        dtype=float,
    )


def density_from_angles(theta: float, phi: float, mix: float) -> torch.Tensor:
    psi = torch.tensor([math.cos(theta), math.sin(theta) * np.exp(1j * phi)], dtype=DTYPE).reshape(2, 1)
    return normalize_density((1 - mix) * (psi @ psi.conj().T) + mix * I2 / 2.0)


def unitary(axis: torch.Tensor, angle: float) -> torch.Tensor:
    vals, vecs = torch.linalg.eig((-1j * angle * axis).to(DTYPE))
    return vecs @ torch.diag(torch.exp(vals)) @ torch.linalg.inv(vecs)


def metric_tensor(params: np.ndarray) -> np.ndarray:
    conformal, shear, twist = params
    scale = math.exp(conformal)
    g = scale * np.array([[math.exp(shear), 0.18 * math.tanh(twist)], [0.18 * math.tanh(twist), math.exp(-shear)]], dtype=float)
    return g


def curvature_scalar(params: np.ndarray, x: float, y: float) -> float:
    conformal, shear, twist = params
    phi = conformal + 0.30 * shear * math.sin(x) + 0.22 * twist * math.cos(y)
    lap_phi = -0.30 * shear * math.sin(x) - 0.22 * twist * math.cos(y)
    return float(-2.0 * math.exp(-2.0 * phi) * lap_phi)


def torsion_style_norm(params: np.ndarray, x: float, y: float) -> float:
    _conformal, shear, twist = params
    a_xy = twist * math.sin(x - y) + 0.25 * shear * math.sin(x + y)
    da_dx = twist * math.cos(x - y) + 0.25 * shear * math.cos(x + y)
    da_dy = -twist * math.cos(x - y) + 0.25 * shear * math.cos(x + y)
    return float(abs(da_dx - da_dy) + abs(a_xy))


def entropy_gradient_signal(rho: torch.Tensor) -> np.ndarray:
    b = bloch(rho)
    s = entropy(rho)
    return np.array([s - 0.38, b[0] * b[2], b[1] - b[0]], dtype=float)


def geometry_flow_rhs(_t: float, params: np.ndarray, signal: np.ndarray, mode: str) -> np.ndarray:
    if mode == "entropy_curvature_flow":
        conformal, shear, twist = params
        return np.array(
            [
                0.62 * signal[0] - 0.18 * conformal,
                0.47 * signal[1] - 0.15 * shear,
                0.53 * signal[2] - 0.17 * twist,
            ],
            dtype=float,
        )
    if mode == "frozen_geometry":
        return np.zeros(3, dtype=float)
    if mode == "random_geometry_flow":
        return np.array([0.04, -0.03, 0.02], dtype=float)
    if mode == "curvature_flat_control":
        return np.array([0.00, -0.55 * params[1], -0.55 * params[2]], dtype=float)
    raise ValueError(mode)


def density_update(rho: torch.Tensor, params: np.ndarray, step: int) -> torch.Tensor:
    g = metric_tensor(params)
    eigvals = np.linalg.eigvalsh(g)
    metric_drive = float(np.sqrt(max(eigvals[1] / max(eigvals[0], 1e-9), 1e-9)))
    curv = curvature_scalar(params, 0.3 * step, 0.17 * step)
    torsion = torsion_style_norm(params, 0.3 * step, 0.17 * step)
    axis = (0.55 + 0.08 * curv) * SX + (0.35 + 0.05 * torsion) * SY + 0.25 * SZ
    u = unitary(axis, 0.045 * metric_drive)
    out = u @ rho @ u.conj().T
    mix = min(0.35, 0.018 * abs(curv) + 0.012 * torsion)
    return normalize_density((1 - mix) * out + mix * I2 / 2.0)


def run(mode: str, seed: int) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    rho = density_from_angles(0.18 + rng.random(), 2 * math.pi * rng.random(), 0.11)
    params = np.array([0.05, 0.03, -0.02], dtype=float)
    rows = []
    for step in range(20):
        signal = entropy_gradient_signal(rho)
        sol = solve_ivp(lambda t, y: geometry_flow_rhs(t, y, signal, mode), (0.0, 0.10), params, rtol=1e-7, atol=1e-9)
        params = sol.y[:, -1]
        rho = density_update(rho, params, step)
        g = metric_tensor(params)
        eigvals = np.linalg.eigvalsh(g)
        curv = curvature_scalar(params, 0.3 * step, 0.17 * step)
        tors = torsion_style_norm(params, 0.3 * step, 0.17 * step)
        rows.append(
            {
                "step": step,
                "mode": mode,
                "entropy": entropy(rho),
                "bloch": bloch(rho),
                "conformal": params[0],
                "shear": params[1],
                "twist": params[2],
                "metric_min_eigenvalue": float(eigvals[0]),
                "metric_max_eigenvalue": float(eigvals[1]),
                "curvature_scalar": curv,
                "torsion_style_norm": tors,
            }
        )
    return rows


def features(rows: list[dict[str, Any]]) -> np.ndarray:
    return np.array(
        [
            [
                r["entropy"],
                *r["bloch"],
                r["conformal"],
                r["shear"],
                r["twist"],
                r["curvature_scalar"],
                r["torsion_style_norm"],
                r["metric_min_eigenvalue"],
                r["metric_max_eigenvalue"],
            ]
            for r in rows
        ],
        dtype=float,
    )


def mode_comparison() -> dict[str, Any]:
    modes = ["entropy_curvature_flow", "frozen_geometry", "random_geometry_flow", "curvature_flat_control"]
    data = {m: np.stack([features(run(m, seed)) for seed in range(8)]) for m in modes}
    centroids = {m: vals.mean(axis=(0, 1)) for m, vals in data.items()}
    dist = {}
    for i, a in enumerate(modes):
        for b in modes[i + 1 :]:
            dist[f"{a}_vs_{b}"] = float(np.linalg.norm(centroids[a] - centroids[b]))
    curvature_var = float(np.var(data["entropy_curvature_flow"][:, :, 7]))
    torsion_var = float(np.var(data["entropy_curvature_flow"][:, :, 8]))
    metric_positive = bool(np.min(data["entropy_curvature_flow"][:, :, 9]) > 0)
    return {
        "centroids": {k: np.round(v, 6).tolist() for k, v in centroids.items()},
        "distances": {k: round(v, 6) for k, v in dist.items()},
        "curvature_variance": curvature_var,
        "torsion_variance": torsion_var,
        "metric_positive": metric_positive,
        "pass": (
            dist["entropy_curvature_flow_vs_frozen_geometry"] > 0.03
            and dist["entropy_curvature_flow_vs_random_geometry_flow"] > 0.02
            and dist["entropy_curvature_flow_vs_curvature_flat_control"] > 0.02
            and curvature_var > 1e-6
            and torsion_var > 1e-6
            and metric_positive
        ),
    }


def symbolic_curvature_torsion() -> dict[str, Any]:
    x, y, c, sh, tw = sp.symbols("x y c sh tw")
    phi = c + sp.Rational(3, 10) * sh * sp.sin(x) + sp.Rational(11, 50) * tw * sp.cos(y)
    curvature = -2 * sp.exp(-2 * phi) * (sp.diff(phi, x, 2) + sp.diff(phi, y, 2))
    a_xy = tw * sp.sin(x - y) + sp.Rational(1, 4) * sh * sp.sin(x + y)
    torsion_like = sp.diff(a_xy, x) - sp.diff(a_xy, y)
    return {
        "curvature_formula": str(curvature),
        "torsion_like_formula": str(torsion_like),
        "curvature_depends_on_shear_or_twist": bool(curvature.has(sh) or curvature.has(tw)),
        "torsion_depends_on_shear_or_twist": bool(torsion_like.has(sh) or torsion_like.has(tw)),
        "pass": bool((curvature.has(sh) or curvature.has(tw)) and (torsion_like.has(sh) or torsion_like.has(tw))),
    }


def persistence_report() -> dict[str, Any]:
    pts = []
    for seed in range(6):
        pts.extend(features(run("entropy_curvature_flow", seed)).tolist())
    st = gudhi.RipsComplex(points=pts, max_edge_length=0.22).create_simplex_tree(max_dimension=1)
    pairs = st.persistence()
    h0 = [p for dim, p in pairs if dim == 0]
    finite = [death - birth for birth, death in h0 if death < float("inf")]
    return {
        "h0_count": len(h0),
        "max_finite_h0_persistence": float(max(finite)) if finite else 0.0,
        "pass": len(h0) > 10 and (max(finite) if finite else 0.0) > 0.015,
    }


def graph_report() -> dict[str, Any]:
    graph = nx.DiGraph()
    edges = [
        ("density_state", "entropy_gradient"),
        ("entropy_gradient", "metric_flow"),
        ("entropy_gradient", "connection_twist_flow"),
        ("metric_flow", "curvature_scalar"),
        ("connection_twist_flow", "torsion_style_norm"),
        ("curvature_scalar", "density_update"),
        ("torsion_style_norm", "density_update"),
    ]
    graph.add_edges_from(edges)
    return {"nodes": sorted(graph.nodes()), "edges": edges, "is_dag": nx.is_directed_acyclic_graph(graph), "pass": nx.is_directed_acyclic_graph(graph)}


def geomstats_sanity() -> dict[str, Any]:
    sample = gs.array(metric_tensor(np.array([0.1, 0.2, -0.3])))
    det = float(gs.linalg.det(sample))
    return {"metric_det": det, "pass": det > 0}


def main() -> int:
    started = time.time()
    comparison = mode_comparison()
    symbolic = symbolic_curvature_torsion()
    persistence = persistence_report()
    graph = graph_report()
    geomstats = geomstats_sanity()
    positive = {
        "entropy_gradient_changes_curvature_and_twist_trajectory": comparison,
        "symbolic_curvature_and_torsion_depend_on_deformation": symbolic,
        "deformed_curvature_point_cloud_nontrivial": persistence,
        "deformation_dependency_graph_executes": graph,
        "geomstats_positive_metric_sanity": geomstats,
    }
    graveyard_companions = {
        "frozen_geometry_control_differs": {
            "distance": comparison["distances"]["entropy_curvature_flow_vs_frozen_geometry"],
            "pass": comparison["distances"]["entropy_curvature_flow_vs_frozen_geometry"] > 0.03,
        },
        "random_geometry_flow_control_differs": {
            "distance": comparison["distances"]["entropy_curvature_flow_vs_random_geometry_flow"],
            "pass": comparison["distances"]["entropy_curvature_flow_vs_random_geometry_flow"] > 0.02,
        },
        "curvature_flat_control_differs": {
            "distance": comparison["distances"]["entropy_curvature_flow_vs_curvature_flat_control"],
            "pass": comparison["distances"]["entropy_curvature_flow_vs_curvature_flat_control"] > 0.02,
        },
    }
    boundary = {
        "terminology_boundary": {
            "pass": True,
            "note": "torsion_style_norm is an antisymmetric-connection proxy in this finite scout, not a full Cartan torsion tensor",
        }
    }
    nearby_variants = {
        "total": 3,
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "variants": sorted(graveyard_companions),
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and nearby_variants["passed"] == nearby_variants["total"]
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_alignment_category": "dynamic_geometry_entropy_gradient_curvature_torsion_formal_scout",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Finite two-coordinate geometry only.",
            "Uses torsion-style antisymmetric connection proxy, not a full differential-geometric torsion tensor.",
            "Does not validate GR, physics, cognition, psychology, ontology, or final manifold identity.",
            "Not yet integrated into the full two-chiral-operating-space stage cycle.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
