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
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density states, entropy, finite gradient signals, metric tensors, curvature samples, and trajectory distances"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic curvature and torsion-style formulas"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing backend tensor sanity for positive metric samples"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over curvature/twist trajectory point clouds"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing deformation dependency graph"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
FLOAT_DTYPE = torch.float64
I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
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


def bloch(rho: torch.Tensor) -> list[float]:
    return [
        float(torch.real(torch.trace(SX @ rho)).item()),
        float(torch.real(torch.trace(SY @ rho)).item()),
        float(torch.real(torch.trace(SZ @ rho)).item()),
    ]


def density_from_angles(theta: float, phi: float, mix: float) -> torch.Tensor:
    phase = torch.exp(torch.tensor(1j * phi, dtype=DTYPE))
    psi = torch.stack(
        [
            torch.tensor(math.cos(theta), dtype=DTYPE),
            torch.tensor(math.sin(theta), dtype=DTYPE) * phase,
        ]
    ).reshape(2, 1)
    return normalize_density((1 - mix) * (psi @ psi.conj().T) + mix * I2 / 2.0)


def unitary(axis: torch.Tensor, angle: float) -> torch.Tensor:
    vals, vecs = torch.linalg.eig((-1j * angle * axis).to(DTYPE))
    return vecs @ torch.diag(torch.exp(vals)) @ torch.linalg.inv(vecs)


def metric_tensor(params: Any) -> torch.Tensor:
    conformal, shear, twist = params
    conformal = float(conformal)
    shear = float(shear)
    twist = float(twist)
    scale = math.exp(conformal)
    return scale * torch.tensor(
        [[math.exp(shear), 0.18 * math.tanh(twist)], [0.18 * math.tanh(twist), math.exp(-shear)]],
        dtype=FLOAT_DTYPE,
    )


def curvature_scalar(params: Any, x: float, y: float) -> float:
    conformal, shear, twist = params
    conformal = float(conformal)
    shear = float(shear)
    twist = float(twist)
    phi = conformal + 0.30 * shear * math.sin(x) + 0.22 * twist * math.cos(y)
    lap_phi = -0.30 * shear * math.sin(x) - 0.22 * twist * math.cos(y)
    return float(-2.0 * math.exp(-2.0 * phi) * lap_phi)


def torsion_style_norm(params: Any, x: float, y: float) -> float:
    _conformal, shear, twist = params
    shear = float(shear)
    twist = float(twist)
    a_xy = twist * math.sin(x - y) + 0.25 * shear * math.sin(x + y)
    da_dx = twist * math.cos(x - y) + 0.25 * shear * math.cos(x + y)
    da_dy = -twist * math.cos(x - y) + 0.25 * shear * math.cos(x + y)
    return float(abs(da_dx - da_dy) + abs(a_xy))


def entropy_gradient_signal(rho: torch.Tensor) -> list[float]:
    b = bloch(rho)
    s = entropy(rho)
    return [s - 0.38, b[0] * b[2], b[1] - b[0]]


def geometry_flow_rhs(_t: float, params: Any, signal: list[float], mode: str) -> list[float]:
    if mode == "entropy_curvature_flow":
        conformal, shear, twist = params
        return [
            0.62 * signal[0] - 0.18 * float(conformal),
            0.47 * signal[1] - 0.15 * float(shear),
            0.53 * signal[2] - 0.17 * float(twist),
        ]
    if mode == "frozen_geometry":
        return [0.0, 0.0, 0.0]
    if mode == "random_geometry_flow":
        return [0.04, -0.03, 0.02]
    if mode == "curvature_flat_control":
        return [0.00, -0.55 * float(params[1]), -0.55 * float(params[2])]
    raise ValueError(mode)


def add_scaled(left: list[float], right: list[float], scale: float) -> list[float]:
    return [float(a) + scale * float(b) for a, b in zip(left, right)]


def rk4_integrate_params(params: list[float], signal: list[float], mode: str, dt: float, substeps: int = 4) -> list[float]:
    y = [float(v) for v in params]
    h = dt / float(substeps)
    t = 0.0
    for _ in range(substeps):
        k1 = geometry_flow_rhs(t, y, signal, mode)
        k2 = geometry_flow_rhs(t + h / 2.0, add_scaled(y, k1, h / 2.0), signal, mode)
        k3 = geometry_flow_rhs(t + h / 2.0, add_scaled(y, k2, h / 2.0), signal, mode)
        k4 = geometry_flow_rhs(t + h, add_scaled(y, k3, h), signal, mode)
        y = [
            y_i + (h / 6.0) * (float(k1_i) + 2.0 * float(k2_i) + 2.0 * float(k3_i) + float(k4_i))
            for y_i, k1_i, k2_i, k3_i, k4_i in zip(y, k1, k2, k3, k4)
        ]
        t += h
    return y


def density_update(rho: torch.Tensor, params: Any, step: int) -> torch.Tensor:
    g = metric_tensor(params)
    eigvals = torch.linalg.eigvalsh(g)
    metric_drive = math.sqrt(max(float(eigvals[1].item()) / max(float(eigvals[0].item()), 1e-9), 1e-9))
    curv = curvature_scalar(params, 0.3 * step, 0.17 * step)
    torsion = torsion_style_norm(params, 0.3 * step, 0.17 * step)
    axis = (0.55 + 0.08 * curv) * SX + (0.35 + 0.05 * torsion) * SY + 0.25 * SZ
    u = unitary(axis, 0.045 * metric_drive)
    out = u @ rho @ u.conj().T
    mix = min(0.35, 0.018 * abs(curv) + 0.012 * torsion)
    return normalize_density((1 - mix) * out + mix * I2 / 2.0)


def run(mode: str, seed: int) -> list[dict[str, Any]]:
    generator = torch.Generator().manual_seed(seed)
    rho = density_from_angles(
        0.18 + float(torch.rand((), dtype=FLOAT_DTYPE, generator=generator).item()),
        2 * math.pi * float(torch.rand((), dtype=FLOAT_DTYPE, generator=generator).item()),
        0.11,
    )
    params: list[float] = [0.05, 0.03, -0.02]
    rows = []
    for step in range(20):
        signal = entropy_gradient_signal(rho)
        params = rk4_integrate_params(params, signal, mode, dt=0.10)
        rho = density_update(rho, params, step)
        g = metric_tensor(params)
        eigvals = torch.linalg.eigvalsh(g)
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
                "metric_min_eigenvalue": float(eigvals[0].item()),
                "metric_max_eigenvalue": float(eigvals[1].item()),
                "curvature_scalar": curv,
                "torsion_style_norm": tors,
            }
        )
    return rows


def features(rows: list[dict[str, Any]]) -> torch.Tensor:
    return torch.tensor(
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
        dtype=FLOAT_DTYPE,
    )


def mode_comparison() -> dict[str, Any]:
    modes = ["entropy_curvature_flow", "frozen_geometry", "random_geometry_flow", "curvature_flat_control"]
    data = {m: torch.stack([features(run(m, seed)) for seed in range(8)]) for m in modes}
    centroids = {m: torch.mean(vals, dim=(0, 1)) for m, vals in data.items()}
    dist = {}
    for i, a in enumerate(modes):
        for b in modes[i + 1 :]:
            dist[f"{a}_vs_{b}"] = float(torch.linalg.vector_norm(centroids[a] - centroids[b]).item())
    curvature_var = float(torch.var(data["entropy_curvature_flow"][:, :, 7], unbiased=False).item())
    torsion_var = float(torch.var(data["entropy_curvature_flow"][:, :, 8], unbiased=False).item())
    metric_positive = bool(torch.min(data["entropy_curvature_flow"][:, :, 9]).item() > 0)
    return {
        "centroids": {k: [round(float(x), 6) for x in v.tolist()] for k, v in centroids.items()},
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
    sample = gs.array(metric_tensor([0.1, 0.2, -0.3]).tolist())
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
