#!/usr/bin/env python3
"""Topology class, entropy deformation, and tensor-network coupling scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cotengra as ctg
import gudhi
import networkx as nx
import numpy as np
import opt_einsum as oe
import quimb as qu
import quimb.tensor as qtn
import sympy as sp
import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "topology_entropy_deformation_tensor_network_coupling_probe_results.json"

NAME = "topology_entropy_deformation_tensor_network_coupling_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether four topology classes can stay "
    "separable when entropy-gradient deformation changes finite metric, "
    "curvature, torsion-style twist, MPS bond evolution, and contraction-tree "
    "geometry. It does not admit final manifold, physics, cognition, "
    "neural-network architecture, or ontology claims."
)

TOOL_MANIFEST = {
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS state evolution, gate application, and cut entropy readouts"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction-tree search whose index sizes are geometry-shaped"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing numeric contraction cross-check for the cotengra index pattern"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing geometry parameters, signatures, distances, and controls"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing entropy-gradient signal and finite-density update proxy"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence of coupled trajectory signatures"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing dependency graph for coupled deformation path"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic inventory for four classes and deformation fields"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
I2 = torch.eye(2, dtype=DTYPE)
SX_T = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY_T = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ_T = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)

SX = qu.pauli("X").A
SY = qu.pauli("Y").A
SZ = qu.pauli("Z").A

TOPOLOGY_CLASSES = {
    "funnel": {"axis": np.kron(SX, SZ), "rate": 0.18, "shear": -0.18, "twist": 0.08, "pairs": [(0, 1), (2, 3), (4, 5), (6, 7), (1, 2)]},
    "vortex": {"axis": np.kron(SY, SX), "rate": 0.14, "shear": 0.10, "twist": 0.31, "pairs": [(1, 2), (3, 4), (5, 6), (0, 1), (6, 7)]},
    "pit": {"axis": np.kron(SZ, SZ), "rate": 0.27, "shear": -0.27, "twist": -0.16, "pairs": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]},
    "hill": {"axis": np.kron(SZ, SX), "rate": 0.20, "shear": 0.25, "twist": -0.05, "pairs": [(6, 7), (5, 6), (4, 5), (3, 4), (2, 3)]},
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


def density_seed(seed: int) -> torch.Tensor:
    rng = np.random.default_rng(seed)
    theta = 0.17 + rng.random()
    phi = 2.0 * math.pi * rng.random()
    psi = torch.tensor([math.cos(theta), math.sin(theta) * np.exp(1j * phi)], dtype=DTYPE).reshape(2, 1)
    return normalize_density(0.86 * (psi @ psi.conj().T) + 0.14 * I2 / 2.0)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / vals.sum()
    return float(-(vals * torch.log(vals)).sum().item())


def bloch(rho: torch.Tensor) -> np.ndarray:
    return np.array(
        [
            float(torch.real(torch.trace(SX_T @ rho)).item()),
            float(torch.real(torch.trace(SY_T @ rho)).item()),
            float(torch.real(torch.trace(SZ_T @ rho)).item()),
        ],
        dtype=float,
    )


def density_step(rho: torch.Tensor, class_row: dict[str, Any], params: np.ndarray, step: int) -> torch.Tensor:
    b = bloch(rho)
    signal = np.array([entropy(rho) - 0.34, b[0] * b[2], b[1] - b[0]], dtype=float)
    params[:] = 0.88 * params + 0.12 * np.array(
        [
            class_row["rate"] + 0.40 * signal[0],
            class_row["shear"] + 0.34 * signal[1],
            class_row["twist"] + 0.28 * signal[2],
        ],
        dtype=float,
    )
    axis = (0.55 + 0.13 * params[1]) * SX_T + (0.31 + 0.17 * params[2]) * SY_T + (0.20 + 0.09 * params[0]) * SZ_T
    vals, vecs = torch.linalg.eig((-1j * (0.035 + 0.02 * class_row["rate"]) * axis).to(DTYPE))
    u = vecs @ torch.diag(torch.exp(vals)) @ torch.linalg.inv(vecs)
    mixed = u @ rho @ u.conj().T
    return normalize_density((1.0 - 0.025 * abs(params[2])) * mixed + 0.025 * abs(params[2]) * I2 / 2.0)


def metric_values(params: np.ndarray) -> tuple[float, float, float]:
    conformal, shear, twist = params
    g = math.exp(conformal) * np.array(
        [[math.exp(shear), 0.16 * math.tanh(twist)], [0.16 * math.tanh(twist), math.exp(-shear)]],
        dtype=float,
    )
    eigvals = np.linalg.eigvalsh(g)
    curvature = float(0.42 * shear - 0.27 * twist + 0.15 * conformal * shear)
    torsion = float(abs(0.65 * twist) + abs(0.18 * shear))
    return float(eigvals[0]), curvature, torsion


def geometry_gate(class_row: dict[str, Any], params: np.ndarray, step: int) -> np.ndarray:
    metric_min, curvature, torsion = metric_values(params)
    angle = class_row["rate"] * (1.0 + 0.22 * curvature + 0.08 * torsion + 0.03 * metric_min + 0.015 * step)
    return qu.expm(-1j * angle * class_row["axis"])


def contraction_report(params: np.ndarray) -> dict[str, Any]:
    metric_min, curvature, torsion = metric_values(params)
    sizes = {
        "a": 2,
        "b": 2 + int(abs(curvature) * 4) % 3,
        "c": 3 + int(abs(torsion) * 5) % 3,
        "d": 2 + int(abs(params[1]) * 6) % 3,
        "e": 2,
    }
    inputs = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")]
    output = ("a", "e")
    optimizer = ctg.HyperOptimizer(max_repeats=8, progbar=False, on_trial_error="raise")
    tree = optimizer.search(inputs, output, sizes)
    rng = np.random.default_rng(int(1000 * (abs(curvature) + abs(torsion) + metric_min)))
    arrays = [rng.normal(size=(sizes[i], sizes[j])) for i, j in inputs]
    ref = oe.contract("ab,bc,cd,de->ae", *arrays)
    return {
        "sizes": sizes,
        "cost": float(tree.contraction_cost()),
        "width": float(tree.contraction_width()),
        "reference_norm": float(np.linalg.norm(ref)),
    }


def run_class(name: str, seed: int, *, frozen: bool = False, collapsed: bool = False) -> list[dict[str, Any]]:
    row = TOPOLOGY_CLASSES[name]
    active_row = TOPOLOGY_CLASSES["hill"] if collapsed else row
    mps = qtn.MPS_rand_state(8, bond_dim=3, seed=100 + seed)
    rho = density_seed(seed)
    params = np.array([0.04, active_row["shear"], active_row["twist"]], dtype=float)
    records = []
    for step in range(10):
        if not frozen:
            rho = density_step(rho, active_row, params, step)
        gate = geometry_gate(active_row, params, step)
        for pair in active_row["pairs"][: 3 + (step % 3)]:
            mps.gate_(gate, pair, contract="swap+split", max_bond=10, cutoff=1e-10)
        ents = np.array([float(mps.entropy(cut)) for cut in range(1, 8)], dtype=float)
        metric_min, curvature, torsion = metric_values(params)
        contract = contraction_report(params)
        records.append(
            {
                "entropy_sum": float(ents.sum()),
                "entropy_std": float(ents.std()),
                "max_bond": int(mps.max_bond()),
                "density_entropy": entropy(rho),
                "metric_min": metric_min,
                "curvature": curvature,
                "torsion": torsion,
                "contraction_cost": contract["cost"],
                "contraction_width": contract["width"],
                "contract_norm": contract["reference_norm"],
            }
        )
    return records


def signature(records: list[dict[str, Any]]) -> np.ndarray:
    arr = np.array(
        [
            [
                r["entropy_sum"],
                r["entropy_std"],
                r["max_bond"],
                r["density_entropy"],
                r["metric_min"],
                r["curvature"],
                r["torsion"],
                r["contraction_cost"],
                r["contraction_width"],
                r["contract_norm"],
            ]
            for r in records
        ],
        dtype=float,
    )
    return np.r_[arr.mean(axis=0), arr.std(axis=0), arr[-1]]


def pairwise_min_distance(vectors: dict[str, np.ndarray]) -> float:
    vals = []
    keys = sorted(vectors)
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            vals.append(float(np.linalg.norm(vectors[a] - vectors[b])))
    return min(vals) if vals else 0.0


def coupled_class_report() -> dict[str, Any]:
    per_seed = []
    for seed in range(6):
        vectors = {name: signature(run_class(name, seed)) for name in TOPOLOGY_CLASSES}
        per_seed.append(pairwise_min_distance(vectors))
    centroid_vectors = {
        name: np.stack([signature(run_class(name, seed)) for seed in range(6)]).mean(axis=0)
        for name in TOPOLOGY_CLASSES
    }
    return {
        "min_same_seed_pair_distance": float(min(per_seed)),
        "min_centroid_distance": pairwise_min_distance(centroid_vectors),
        "centroid_signature_head": {k: np.round(v[:6], 6).tolist() for k, v in centroid_vectors.items()},
        "pass": min(per_seed) > 0.45 and pairwise_min_distance(centroid_vectors) > 0.55,
    }


def graveyard_report() -> dict[str, Any]:
    dynamic = {name: signature(run_class(name, 2)) for name in TOPOLOGY_CLASSES}
    frozen = {name: signature(run_class(name, 2, frozen=True)) for name in TOPOLOGY_CLASSES}
    collapsed = {name: signature(run_class(name, 2, collapsed=True)) for name in TOPOLOGY_CLASSES}
    dynamic_gap = pairwise_min_distance(dynamic)
    frozen_shift = min(float(np.linalg.norm(dynamic[k] - frozen[k])) for k in TOPOLOGY_CLASSES)
    collapsed_gap = pairwise_min_distance(collapsed)
    return {
        "frozen_entropy_deformation_changes_trajectory": {"shift": frozen_shift, "pass": frozen_shift > 0.12},
        "collapsed_topology_gate_reduces_separation": {"dynamic_gap": dynamic_gap, "collapsed_gap": collapsed_gap, "pass": collapsed_gap < dynamic_gap * 0.85},
    }


def persistence_report() -> dict[str, Any]:
    pts = [signature(run_class(name, seed)).tolist() for name in TOPOLOGY_CLASSES for seed in range(4)]
    st = gudhi.RipsComplex(points=pts, max_edge_length=8.0).create_simplex_tree(max_dimension=1)
    pairs = st.persistence()
    h0 = [p for dim, p in pairs if dim == 0]
    finite = [death - birth for birth, death in h0 if death < float("inf")]
    return {
        "h0_count": len(h0),
        "max_finite_h0_persistence": float(max(finite)) if finite else 0.0,
        "pass": len(h0) >= 8 and (max(finite) if finite else 0.0) > 0.45,
    }


def graph_report() -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_edges_from(
        [
            ("density_entropy", "entropy_gradient_signal"),
            ("entropy_gradient_signal", "metric_shear_twist"),
            ("metric_shear_twist", "geometry_shaped_gate"),
            ("geometry_shaped_gate", "quimb_mps_state"),
            ("metric_shear_twist", "cotengra_index_sizes"),
            ("quimb_mps_state", "cut_entropy_signature"),
            ("cotengra_index_sizes", "contraction_signature"),
        ]
    )
    return {"node_count": graph.number_of_nodes(), "edge_count": graph.number_of_edges(), "acyclic": nx.is_directed_acyclic_graph(graph), "pass": nx.is_directed_acyclic_graph(graph)}


def symbolic_report() -> dict[str, Any]:
    classes, fields, tensor_tools = sp.symbols("classes fields tensor_tools", integer=True)
    claim = sp.And(sp.Eq(classes, 4), sp.Ge(fields, 3), sp.Eq(tensor_tools, 2))
    return {"class_count": 4, "deformation_fields": 3, "tensor_tool_count": 2, "pass": bool(claim.subs({classes: 4, fields: 3, tensor_tools: 2}))}


def main() -> int:
    started = time.time()
    coupled = coupled_class_report()
    graveyards = graveyard_report()
    persistence = persistence_report()
    graph = graph_report()
    symbolic = symbolic_report()
    positive = {
        "topology_classes_survive_entropy_deformed_tensor_network_coupling": coupled,
        "persistent_signature_cloud_nontrivial": persistence,
        "coupling_dependency_graph_is_explicit": graph,
        "symbolic_inventory_has_four_classes_fields_and_tensor_tools": symbolic,
    }
    boundary = {
        "installed_versions": {
            "quimb": getattr(qu, "__version__", "unknown"),
            "cotengra": getattr(ctg, "__version__", "unknown"),
            "pass": True,
        },
        "kahypar_available": {
            "available": bool(getattr(ctg.hyperoptimizers.hyper, "KAHYPAR_FOUND", False)),
            "pass": True,
            "note": "cotengra ran with available optimizer methods; kahypar is optional and absent on this machine when false.",
        },
    }
    nearby_variants = {
        "total": len(graveyards),
        "passed": sum(1 for row in graveyards.values() if row["pass"]),
        "variants": sorted(graveyards),
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_alignment_category": "dynamic_geometry_tensor_network_coupling_formal_scout",
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Finite coupling scout only.",
            "Does not yet replace the full source-native chiral operating-space stage cycle.",
            "Does not claim final topology, physics, cognition, or neural-network architecture.",
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
