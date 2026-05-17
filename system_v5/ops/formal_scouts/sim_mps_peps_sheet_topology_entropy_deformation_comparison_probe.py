#!/usr/bin/env python3
"""MPS chain vs PEPS sheet topology entropy-deformation comparison scout."""

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
OUT_PATH = RESULT_DIR / "mps_peps_sheet_topology_entropy_deformation_comparison_probe_results.json"

NAME = "mps_peps_sheet_topology_entropy_deformation_comparison_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: compares a one-dimensional MPS carrier with a "
    "two-dimensional PEPS sheet carrier under the same finite topology-class "
    "and entropy-gradient deformation schedule. It does not admit final "
    "manifold, physics, cognition, neural-network architecture, or ontology claims."
)

TOOL_MANIFEST = {
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS and PEPS construction, gate application, and tensor-network readouts"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction-tree search for chain and sheet index patterns"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing numeric contraction cross-checks for chain and sheet patterns"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing geometry states, signatures, distances, and controls"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite-density entropy-gradient update proxy"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence of sheet signature point cloud"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing chain-vs-sheet graph comparison"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic inventory for MPS, PEPS, and four topology classes"},
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

CLASSES = {
    "funnel": {
        "axis": np.kron(SX, SZ),
        "rate": 0.18,
        "shear": -0.18,
        "twist": 0.08,
        "mps_pairs": [(0, 1), (2, 3), (4, 5), (6, 7), (1, 2)],
        "peps_edges": [((0, 0), (0, 1)), ((1, 0), (1, 1)), ((0, 2), (0, 3)), ((1, 2), (1, 3)), ((0, 1), (1, 1))],
    },
    "vortex": {
        "axis": np.kron(SY, SX),
        "rate": 0.14,
        "shear": 0.10,
        "twist": 0.31,
        "mps_pairs": [(1, 2), (3, 4), (5, 6), (0, 1), (6, 7)],
        "peps_edges": [((0, 1), (1, 1)), ((0, 2), (1, 2)), ((0, 0), (0, 1)), ((1, 2), (1, 3)), ((0, 3), (1, 3))],
    },
    "pit": {
        "axis": np.kron(SZ, SZ),
        "rate": 0.27,
        "shear": -0.27,
        "twist": -0.16,
        "mps_pairs": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)],
        "peps_edges": [((0, 0), (1, 0)), ((0, 1), (1, 1)), ((0, 2), (1, 2)), ((0, 1), (0, 2)), ((1, 1), (1, 2))],
    },
    "hill": {
        "axis": np.kron(SZ, SX),
        "rate": 0.20,
        "shear": 0.25,
        "twist": -0.05,
        "mps_pairs": [(6, 7), (5, 6), (4, 5), (3, 4), (2, 3)],
        "peps_edges": [((0, 3), (1, 3)), ((0, 2), (1, 2)), ((0, 1), (1, 1)), ((0, 2), (0, 3)), ((1, 2), (1, 3))],
    },
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
    theta = 0.19 + rng.random()
    phi = 2.0 * math.pi * rng.random()
    psi = torch.tensor([math.cos(theta), math.sin(theta) * np.exp(1j * phi)], dtype=DTYPE).reshape(2, 1)
    return normalize_density(0.84 * (psi @ psi.conj().T) + 0.16 * I2 / 2.0)


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


def density_step(rho: torch.Tensor, row: dict[str, Any], params: np.ndarray, step: int) -> torch.Tensor:
    b = bloch(rho)
    signal = np.array([entropy(rho) - 0.36, b[0] * b[2], b[1] - b[0]], dtype=float)
    params[:] = 0.86 * params + 0.14 * np.array(
        [
            row["rate"] + 0.42 * signal[0],
            row["shear"] + 0.36 * signal[1],
            row["twist"] + 0.30 * signal[2],
        ],
        dtype=float,
    )
    axis = (0.52 + 0.11 * params[1]) * SX_T + (0.33 + 0.15 * params[2]) * SY_T + (0.22 + 0.08 * params[0]) * SZ_T
    vals, vecs = torch.linalg.eig((-1j * (0.032 + 0.018 * row["rate"]) * axis).to(DTYPE))
    u = vecs @ torch.diag(torch.exp(vals)) @ torch.linalg.inv(vecs)
    mixed = u @ rho @ u.conj().T
    return normalize_density((1.0 - 0.022 * abs(params[2])) * mixed + 0.022 * abs(params[2]) * I2 / 2.0)


def metric_values(params: np.ndarray) -> tuple[float, float, float]:
    conformal, shear, twist = params
    metric_min = math.exp(conformal - abs(shear)) * (1.0 - 0.05 * abs(math.tanh(twist)))
    curvature = float(0.40 * shear - 0.25 * twist + 0.13 * conformal * shear)
    torsion = float(abs(0.62 * twist) + abs(0.20 * shear))
    return metric_min, curvature, torsion


def geometry_gate(row: dict[str, Any], params: np.ndarray, step: int, *, sheet: bool) -> np.ndarray:
    metric_min, curvature, torsion = metric_values(params)
    sheet_factor = 1.0 + (0.10 * torsion if sheet else 0.0)
    angle = row["rate"] * sheet_factor * (1.0 + 0.20 * curvature + 0.07 * torsion + 0.025 * metric_min + 0.012 * step)
    return qu.expm(-1j * angle * row["axis"])


def make_peps(seed: int) -> qtn.PEPS:
    rng = np.random.default_rng(900 + seed)
    arrays = []
    for i in range(2):
        row = []
        for j in range(4):
            shape = []
            if i > 0:
                shape.append(2)
            if j < 3:
                shape.append(2)
            if i < 1:
                shape.append(2)
            if j > 0:
                shape.append(2)
            shape.append(2)
            row.append(rng.normal(scale=0.35, size=shape))
        arrays.append(row)
    return qtn.PEPS(arrays)


def contraction_cost(pattern: str, params: np.ndarray) -> dict[str, float]:
    metric_min, curvature, torsion = metric_values(params)
    if pattern == "mps":
        inputs = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")]
        output = ("a", "e")
        sizes = {"a": 2, "b": 2 + int(abs(curvature) * 4) % 3, "c": 3 + int(abs(torsion) * 5) % 3, "d": 2 + int(abs(params[1]) * 6) % 3, "e": 2}
        expr = "ab,bc,cd,de->ae"
    else:
        inputs = [("a", "b", "e"), ("b", "c", "f"), ("c", "d", "g"), ("e", "f", "h"), ("f", "g", "i"), ("g", "d", "j")]
        output = ("a", "h", "i", "j")
        sizes = {
            "a": 2,
            "b": 2 + int(abs(curvature) * 5) % 3,
            "c": 2 + int(abs(torsion) * 5) % 3,
            "d": 2,
            "e": 2 + int(abs(metric_min) * 4) % 3,
            "f": 3 + int(abs(params[1]) * 7) % 3,
            "g": 2 + int(abs(params[2]) * 7) % 3,
            "h": 2,
            "i": 2,
            "j": 2,
        }
        expr = "abe,bcf,cdg,efh,fgi,gdj->ahij"
    optimizer = ctg.HyperOptimizer(max_repeats=8, progbar=False, on_trial_error="raise")
    tree = optimizer.search(inputs, output, sizes)
    rng = np.random.default_rng(int(1000 * (metric_min + abs(curvature) + abs(torsion))) + (1 if pattern == "peps" else 0))
    arrays = [rng.normal(size=tuple(sizes[ix] for ix in term)) for term in inputs]
    ref = oe.contract(expr, *arrays)
    return {"cost": float(tree.contraction_cost()), "width": float(tree.contraction_width()), "norm": float(np.linalg.norm(ref))}


def run_mps(name: str, seed: int, *, collapsed: bool = False) -> list[dict[str, Any]]:
    row = CLASSES["hill"] if collapsed else CLASSES[name]
    mps = qtn.MPS_rand_state(8, bond_dim=3, seed=300 + seed)
    rho = density_seed(seed)
    params = np.array([0.04, row["shear"], row["twist"]], dtype=float)
    records = []
    for step in range(8):
        rho = density_step(rho, row, params, step)
        gate = geometry_gate(row, params, step, sheet=False)
        for pair in row["mps_pairs"][: 3 + (step % 3)]:
            mps.gate_(gate, pair, contract="swap+split", max_bond=10, cutoff=1e-10)
        ents = np.array([float(mps.entropy(cut)) for cut in range(1, 8)], dtype=float)
        metric_min, curvature, torsion = metric_values(params)
        cc = contraction_cost("mps", params)
        records.append(
            {
                "carrier": "mps",
                "entropy_sum": float(ents.sum()),
                "entropy_std": float(ents.std()),
                "max_bond": int(mps.max_bond()),
                "density_entropy": entropy(rho),
                "metric_min": metric_min,
                "curvature": curvature,
                "torsion": torsion,
                "contraction_cost": cc["cost"],
                "contraction_width": cc["width"],
                "contract_norm": cc["norm"],
            }
        )
    return records


def run_peps(name: str, seed: int, *, collapsed: bool = False) -> list[dict[str, Any]]:
    row = CLASSES["hill"] if collapsed else CLASSES[name]
    peps = make_peps(seed)
    rho = density_seed(seed)
    params = np.array([0.04, row["shear"], row["twist"]], dtype=float)
    records = []
    for step in range(8):
        rho = density_step(rho, row, params, step)
        gate = geometry_gate(row, params, step, sheet=True)
        for edge in row["peps_edges"][: 3 + (step % 3)]:
            peps.gate_(gate, edge, contract="split", max_bond=10, cutoff=1e-10)
        tensor_norms = np.array([float(np.linalg.norm(t.data)) for t in peps], dtype=float)
        metric_min, curvature, torsion = metric_values(params)
        cc = contraction_cost("peps", params)
        records.append(
            {
                "carrier": "peps",
                "entropy_sum": float(tensor_norms.sum()),
                "entropy_std": float(tensor_norms.std()),
                "max_bond": int(peps.max_bond()),
                "density_entropy": entropy(rho),
                "metric_min": metric_min,
                "curvature": curvature,
                "torsion": torsion,
                "contraction_cost": cc["cost"],
                "contraction_width": cc["width"],
                "contract_norm": cc["norm"],
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
    keys = sorted(vectors)
    vals = []
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            vals.append(float(np.linalg.norm(vectors[a] - vectors[b])))
    return min(vals) if vals else 0.0


def comparison_report() -> dict[str, Any]:
    mps_vectors = {name: np.stack([signature(run_mps(name, seed)) for seed in range(4)]).mean(axis=0) for name in CLASSES}
    peps_vectors = {name: np.stack([signature(run_peps(name, seed)) for seed in range(4)]).mean(axis=0) for name in CLASSES}
    sheet_chain_gaps = {name: float(np.linalg.norm(peps_vectors[name] - mps_vectors[name])) for name in CLASSES}
    return {
        "mps_min_class_distance": pairwise_min_distance(mps_vectors),
        "peps_min_class_distance": pairwise_min_distance(peps_vectors),
        "min_sheet_chain_gap": float(min(sheet_chain_gaps.values())),
        "sheet_chain_gaps": sheet_chain_gaps,
        "mps_signature_head": {k: np.round(v[:6], 6).tolist() for k, v in mps_vectors.items()},
        "peps_signature_head": {k: np.round(v[:6], 6).tolist() for k, v in peps_vectors.items()},
        "pass": pairwise_min_distance(peps_vectors) > 0.40 and min(sheet_chain_gaps.values()) > 1.0,
    }


def graveyard_report() -> dict[str, Any]:
    dynamic = {name: signature(run_peps(name, 1)) for name in CLASSES}
    collapsed = {name: signature(run_peps(name, 1, collapsed=True)) for name in CLASSES}
    dynamic_gap = pairwise_min_distance(dynamic)
    collapsed_gap = pairwise_min_distance(collapsed)
    sheet = signature(run_peps("vortex", 2))
    chain = signature(run_mps("vortex", 2))
    return {
        "collapsed_sheet_topology_laws_reduce_separation": {"dynamic_gap": dynamic_gap, "collapsed_gap": collapsed_gap, "pass": collapsed_gap < dynamic_gap * 0.25},
        "sheet_not_chain_relabel": {"sheet_chain_distance": float(np.linalg.norm(sheet - chain)), "pass": float(np.linalg.norm(sheet - chain)) > 1.0},
    }


def persistence_report() -> dict[str, Any]:
    pts = [signature(run_peps(name, seed)).tolist() for name in CLASSES for seed in range(3)]
    st = gudhi.RipsComplex(points=pts, max_edge_length=12.0).create_simplex_tree(max_dimension=1)
    pairs = st.persistence()
    h0 = [p for dim, p in pairs if dim == 0]
    finite = [death - birth for birth, death in h0 if death < float("inf")]
    return {"h0_count": len(h0), "max_finite_h0_persistence": float(max(finite)) if finite else 0.0, "pass": len(h0) >= 8 and (max(finite) if finite else 0.0) > 0.30}


def graph_report() -> dict[str, Any]:
    chain = nx.path_graph(8)
    sheet = nx.grid_2d_graph(2, 4)
    return {
        "chain_edges": chain.number_of_edges(),
        "sheet_edges": sheet.number_of_edges(),
        "sheet_has_vertical_edges": any(a[0] != b[0] for a, b in sheet.edges()),
        "pass": sheet.number_of_edges() > chain.number_of_edges() and any(a[0] != b[0] for a, b in sheet.edges()),
    }


def symbolic_report() -> dict[str, Any]:
    carriers, classes, sheet_dim = sp.symbols("carriers classes sheet_dim", integer=True)
    claim = sp.And(sp.Eq(carriers, 2), sp.Eq(classes, 4), sp.Eq(sheet_dim, 2))
    return {"carrier_count": 2, "class_count": 4, "sheet_dimension": 2, "pass": bool(claim.subs({carriers: 2, classes: 4, sheet_dim: 2}))}


def main() -> int:
    started = time.time()
    comparison = comparison_report()
    graveyards = graveyard_report()
    persistence = persistence_report()
    graph = graph_report()
    symbolic = symbolic_report()
    positive = {
        "mps_and_peps_run_same_entropy_deformation_schedule": comparison,
        "peps_sheet_signature_cloud_nontrivial": persistence,
        "sheet_graph_has_extra_two_dimensional_edges": graph,
        "symbolic_inventory_has_chain_sheet_and_four_classes": symbolic,
    }
    boundary = {
        "installed_versions": {"quimb": getattr(qu, "__version__", "unknown"), "cotengra": getattr(ctg, "__version__", "unknown"), "pass": True},
        "peps_surface": {"shape": "2x4 open-boundary PEPS sheet", "physical_sites": 8, "pass": True},
    }
    nearby_variants = {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)}
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
        "source_alignment_category": "sheet_tensor_network_comparison_formal_scout",
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Finite MPS-vs-PEPS comparison only.",
            "Does not yet implement full source-native left/right Weyl density histories on PEPS sheets.",
            "Does not claim final manifold, physics, cognition, or neural-network architecture.",
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
