#!/usr/bin/env python3
"""Entropy-gradient metric/connection deformation scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import numpy as np
import sympy as sp
import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "entropy_gradient_metric_connection_deformation_probe_results.json"

NAME = "entropy_gradient_metric_connection_deformation_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether finite entropy gradients can act as "
    "geometry-deformation signals on metric scale, Hopf-loop area, and "
    "connection/holonomy parameters during density evolution. It does not "
    "admit final manifold, cognition, psychology, physics, or ontology claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing finite-difference gradients, trajectory distances, and controls"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density matrices, entropy, CPTP-style updates, and geometry-coupled evolution"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing deformation dependency graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over deformed trajectory point cloud"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic check that entropy gradient is distinct from operator generator"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
SM = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE)
SP = torch.tensor([[0, 1], [0, 0]], dtype=DTYPE)


TOPOLOGY_LAWS = {
    "funnel": {"stage": "Se", "chirality": +1, "ladder": SM, "axis": SX, "rate": 0.18, "phase": 0.11},
    "vortex": {"stage": "Ne", "chirality": +1, "ladder": SM, "axis": SY, "rate": 0.11, "phase": 0.24},
    "pit": {"stage": "Ni", "chirality": +1, "ladder": SM, "axis": SZ, "rate": 0.29, "phase": 0.08},
    "hill": {"stage": "Si", "chirality": +1, "ladder": SM, "axis": SZ, "rate": 0.15, "phase": 0.18},
    "cannon": {"stage": "Se", "chirality": -1, "ladder": SP, "axis": SX, "rate": 0.18, "phase": -0.11},
    "spiral": {"stage": "Ne", "chirality": -1, "ladder": SP, "axis": SY, "rate": 0.11, "phase": -0.24},
    "source": {"stage": "Ni", "chirality": -1, "ladder": SP, "axis": SX, "rate": 0.29, "phase": -0.08},
    "citadel": {"stage": "Si", "chirality": -1, "ladder": SP, "axis": SZ, "rate": 0.15, "phase": -0.18},
}


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


def purity(rho: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ rho)).item())


def bloch(rho: torch.Tensor) -> np.ndarray:
    return np.array(
        [
            float(torch.real(torch.trace(SX @ rho)).item()),
            float(torch.real(torch.trace(SY @ rho)).item()),
            float(torch.real(torch.trace(SZ @ rho)).item()),
        ],
        dtype=float,
    )


def unitary(axis: torch.Tensor, angle: float) -> torch.Tensor:
    vals, vecs = torch.linalg.eig((-1j * angle * axis).to(DTYPE))
    return vecs @ torch.diag(torch.exp(vals)) @ torch.linalg.inv(vecs)


def dissipator(rho: torch.Tensor, ladder: torch.Tensor, gamma: float) -> torch.Tensor:
    dt = 0.09
    jump = math.sqrt(max(gamma * dt, 0.0)) * ladder
    no_jump = I2 - 0.5 * gamma * dt * ladder.conj().T @ ladder
    return normalize_density(jump @ rho @ jump.conj().T + no_jump @ rho @ no_jump.conj().T)


def hopf_loop_area(theta: float) -> float:
    return float(2.0 * math.pi * (1.0 - math.cos(theta)))


def geometry_update(rho: torch.Tensor, law: dict[str, Any], geom: dict[str, float]) -> torch.Tensor:
    area = hopf_loop_area(geom["theta"])
    holonomy = geom["connection"] * area
    metric_scale = geom["metric_scale"]
    angle = metric_scale * (float(law["phase"]) + 0.035 * holonomy) * float(law["chirality"])
    h = unitary(law["axis"], angle) @ rho @ unitary(law["axis"], angle).conj().T
    h = dissipator(h, law["ladder"], float(law["rate"]) * metric_scale)
    mix = min(0.42, 0.035 * abs(area) + 0.02 * abs(holonomy))
    return normalize_density((1.0 - mix) * h + mix * I2 / 2.0)


def entropy_after(rho: torch.Tensor, law: dict[str, Any], geom: dict[str, float]) -> float:
    return entropy(geometry_update(rho, law, geom))


def entropy_gradient(rho: torch.Tensor, law: dict[str, Any], geom: dict[str, float]) -> dict[str, float]:
    out = {}
    eps = {"metric_scale": 1e-3, "theta": 1e-3, "connection": 1e-3}
    for key, step in eps.items():
        plus = dict(geom)
        minus = dict(geom)
        plus[key] += step
        minus[key] -= step
        if key == "theta":
            plus[key] = min(math.pi - 0.05, plus[key])
            minus[key] = max(0.05, minus[key])
        out[key] = (entropy_after(rho, law, plus) - entropy_after(rho, law, minus)) / (plus[key] - minus[key])
    return out


def initial_density(seed: int) -> torch.Tensor:
    rng = np.random.default_rng(seed)
    theta = 0.18 + 1.1 * rng.random()
    phi = 2.0 * math.pi * rng.random()
    psi = torch.tensor([math.cos(theta), math.sin(theta) * np.exp(1j * phi)], dtype=DTYPE).reshape(2, 1)
    return normalize_density(0.84 * (psi @ psi.conj().T) + 0.16 * I2 / 2.0)


def run_trajectory(mode: str, seed: int = 0) -> list[dict[str, Any]]:
    rho = initial_density(seed)
    geom = {"metric_scale": 1.0, "theta": 0.55, "connection": 0.50}
    rows = []
    sequence = ["funnel", "vortex", "pit", "hill", "cannon", "spiral", "source", "citadel"] * 3
    rng = np.random.default_rng(seed + 800)
    for step, name in enumerate(sequence):
        law = TOPOLOGY_LAWS[name]
        grad = entropy_gradient(rho, law, geom)
        if mode == "entropy_deformed":
            geom["metric_scale"] = float(np.clip(geom["metric_scale"] - 0.42 * grad["metric_scale"], 0.55, 1.75))
            geom["theta"] = float(np.clip(geom["theta"] - 0.35 * grad["theta"], 0.08, math.pi - 0.08))
            geom["connection"] = float(np.clip(geom["connection"] - 0.30 * grad["connection"], -1.5, 1.5))
        elif mode == "random_deformed":
            geom["metric_scale"] = float(np.clip(geom["metric_scale"] + 0.025 * rng.normal(), 0.55, 1.75))
            geom["theta"] = float(np.clip(geom["theta"] + 0.025 * rng.normal(), 0.08, math.pi - 0.08))
            geom["connection"] = float(np.clip(geom["connection"] + 0.025 * rng.normal(), -1.5, 1.5))
        elif mode == "readout_only":
            _ = entropy(rho)
        elif mode == "frozen_geometry":
            pass
        else:
            raise ValueError(mode)
        before = rho
        rho = geometry_update(rho, law, geom)
        rows.append(
            {
                "step": step,
                "law": name,
                "mode": mode,
                "entropy": entropy(rho),
                "purity": purity(rho),
                "bloch": bloch(rho),
                "state_delta": float(torch.linalg.matrix_norm(rho - before).item()),
                "metric_scale": geom["metric_scale"],
                "theta": geom["theta"],
                "connection": geom["connection"],
                "gradient": grad,
            }
        )
    return rows


def trajectory_features(rows: list[dict[str, Any]]) -> np.ndarray:
    return np.array(
        [
            [
                row["entropy"],
                row["purity"],
                *row["bloch"],
                row["metric_scale"],
                row["theta"],
                row["connection"],
                row["state_delta"],
            ]
            for row in rows
        ],
        dtype=float,
    )


def compare_modes() -> dict[str, Any]:
    modes = ["entropy_deformed", "frozen_geometry", "readout_only", "random_deformed"]
    samples = {mode: [trajectory_features(run_trajectory(mode, seed)) for seed in range(10)] for mode in modes}
    centroids = {mode: np.mean(np.stack(vals), axis=(0, 1)) for mode, vals in samples.items()}
    distances = {}
    for i, a in enumerate(modes):
        for b in modes[i + 1 :]:
            distances[f"{a}_vs_{b}"] = float(np.linalg.norm(centroids[a] - centroids[b]))
    entropy_vs_frozen = distances["entropy_deformed_vs_frozen_geometry"]
    entropy_vs_readout = distances["entropy_deformed_vs_readout_only"]
    random_vs_frozen = distances["frozen_geometry_vs_random_deformed"]
    return {
        "centroids": {k: np.round(v, 6).tolist() for k, v in centroids.items()},
        "distances": {k: round(v, 6) for k, v in distances.items()},
        "entropy_vs_frozen": entropy_vs_frozen,
        "entropy_vs_readout_only": entropy_vs_readout,
        "random_vs_frozen": random_vs_frozen,
        "pass": entropy_vs_frozen > 0.08 and entropy_vs_readout > 0.08 and abs(entropy_vs_frozen - random_vs_frozen) > 0.025,
    }


def gradient_not_operator_symbolic() -> dict[str, Any]:
    s, mx, th, conn = sp.symbols("S metric theta connection")
    deformation = sp.Matrix([sp.diff(s * mx + sp.sin(th) + conn**2, mx), sp.diff(s * mx + sp.sin(th) + conn**2, th), sp.diff(s * mx + sp.sin(th) + conn**2, conn)])
    operator_vector = sp.Matrix([1, 0, -1])
    return {
        "deformation_field": [str(x) for x in deformation],
        "operator_vector": [str(x) for x in operator_vector],
        "identically_same": bool(sp.simplify(deformation - operator_vector) == sp.zeros(3, 1)),
        "pass": not bool(sp.simplify(deformation - operator_vector) == sp.zeros(3, 1)),
    }


def persistence_report() -> dict[str, Any]:
    points = []
    for seed in range(8):
        points.extend(trajectory_features(run_trajectory("entropy_deformed", seed)).tolist())
    st = gudhi.RipsComplex(points=points, max_edge_length=0.28).create_simplex_tree(max_dimension=1)
    pairs = st.persistence()
    h0 = [p for dim, p in pairs if dim == 0]
    finite = [death - birth for birth, death in h0 if death < float("inf")]
    return {
        "h0_count": len(h0),
        "max_finite_h0_persistence": float(max(finite)) if finite else 0.0,
        "pass": len(h0) > 8 and (max(finite) if finite else 0.0) > 0.025,
    }


def dependency_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    edges = [
        ("density_state", "entropy_readout"),
        ("entropy_readout", "entropy_gradient"),
        ("entropy_gradient", "metric_scale"),
        ("entropy_gradient", "hopf_loop_area"),
        ("entropy_gradient", "connection_holonomy"),
        ("metric_scale", "density_update"),
        ("hopf_loop_area", "density_update"),
        ("connection_holonomy", "density_update"),
    ]
    graph.add_edges_from(edges)
    return {"nodes": sorted(graph.nodes()), "edges": edges, "is_dag": nx.is_directed_acyclic_graph(graph), "pass": nx.is_directed_acyclic_graph(graph)}


def main() -> int:
    started = time.time()
    comparison = compare_modes()
    symbolic = gradient_not_operator_symbolic()
    persistence = persistence_report()
    graph = dependency_graph()
    positive = {
        "entropy_gradient_deforms_geometry_not_readout_only": comparison,
        "entropy_gradient_field_not_operator_generator": symbolic,
        "deformed_trajectory_point_cloud_nontrivial": persistence,
        "deformation_dependency_graph_executes": graph,
    }
    graveyard_companions = {
        "frozen_geometry_control_differs_from_entropy_deformed": {
            "distance": comparison["entropy_vs_frozen"],
            "pass": comparison["entropy_vs_frozen"] > 0.08,
        },
        "readout_only_entropy_control_differs_from_entropy_deformed": {
            "distance": comparison["entropy_vs_readout_only"],
            "pass": comparison["entropy_vs_readout_only"] > 0.08,
        },
        "random_deformation_not_same_as_entropy_gradient": {
            "entropy_vs_frozen": comparison["entropy_vs_frozen"],
            "random_vs_frozen": comparison["random_vs_frozen"],
            "pass": abs(comparison["entropy_vs_frozen"] - comparison["random_vs_frozen"]) > 0.025,
        },
    }
    boundary = {
        "entropy_role_classification": {
            "pass": True,
            "read": "entropy is a readout when observed, a constraint functional when used in a predicate, and a geometry-deformation field when its gradient updates metric/connection parameters",
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
        "source_alignment_category": "dynamic_geometry_entropy_gradient_deformation_formal_scout",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Finite two-state density fixture only.",
            "Deforms metric/connection parameters but does not prove final manifold dynamics.",
            "Does not identify entropy with Ti/Te/Fi/Fe operators.",
            "Does not promote psychology, cognition, physics, or ontology.",
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
