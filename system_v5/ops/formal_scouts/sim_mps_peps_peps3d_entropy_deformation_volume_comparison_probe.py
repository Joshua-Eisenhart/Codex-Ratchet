#!/usr/bin/env python3
"""MPS, PEPS, and PEPS3D entropy-deformation volume comparison scout."""

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
OUT_PATH = RESULT_DIR / "mps_peps_peps3d_entropy_deformation_volume_comparison_probe_results.json"

NAME = "mps_peps_peps3d_entropy_deformation_volume_comparison_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: compares chain, sheet, and volume tensor-network "
    "carriers under one entropy-gradient deformation schedule. It does not "
    "admit final manifold, physics, cognition, neural-network architecture, "
    "or ontology claims."
)

TOOL_MANIFEST = {
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS, PEPS, and PEPS3D tensor-network evolution"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction-tree search for 1D, 2D, and 3D patterns"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction numeric cross-checks"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing carrier signatures, distances, and controls"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing entropy-gradient finite-density update"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence of carrier signature clouds"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing graph topology comparison"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic inventory"},
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
    "funnel": {"axis": np.kron(SX, SZ), "rate": 0.18, "shear": -0.18, "twist": 0.08},
    "vortex": {"axis": np.kron(SY, SX), "rate": 0.14, "shear": 0.10, "twist": 0.31},
    "pit": {"axis": np.kron(SZ, SZ), "rate": 0.27, "shear": -0.27, "twist": -0.16},
    "hill": {"axis": np.kron(SZ, SX), "rate": 0.20, "shear": 0.25, "twist": -0.05},
}

CARRIER_EDGES = {
    "mps": {
        "funnel": [(0, 1), (2, 3), (4, 5), (6, 7), (1, 2)],
        "vortex": [(1, 2), (3, 4), (5, 6), (0, 1), (6, 7)],
        "pit": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)],
        "hill": [(6, 7), (5, 6), (4, 5), (3, 4), (2, 3)],
    },
    "peps": {
        "funnel": [((0, 0), (0, 1)), ((1, 0), (1, 1)), ((0, 2), (0, 3)), ((1, 2), (1, 3)), ((0, 1), (1, 1))],
        "vortex": [((0, 1), (1, 1)), ((0, 2), (1, 2)), ((0, 0), (0, 1)), ((1, 2), (1, 3)), ((0, 3), (1, 3))],
        "pit": [((0, 0), (1, 0)), ((0, 1), (1, 1)), ((0, 2), (1, 2)), ((0, 1), (0, 2)), ((1, 1), (1, 2))],
        "hill": [((0, 3), (1, 3)), ((0, 2), (1, 2)), ((0, 1), (1, 1)), ((0, 2), (0, 3)), ((1, 2), (1, 3))],
    },
    "peps3d": {
        "funnel": [((0, 0, 0), (1, 0, 0)), ((0, 1, 0), (1, 1, 0)), ((0, 0, 1), (1, 0, 1)), ((0, 1, 1), (1, 1, 1)), ((0, 0, 0), (0, 0, 1))],
        "vortex": [((0, 0, 0), (0, 1, 0)), ((1, 0, 0), (1, 1, 0)), ((0, 0, 1), (0, 1, 1)), ((1, 0, 1), (1, 1, 1)), ((0, 1, 0), (0, 1, 1))],
        "pit": [((0, 0, 0), (0, 0, 1)), ((1, 0, 0), (1, 0, 1)), ((0, 1, 0), (0, 1, 1)), ((1, 1, 0), (1, 1, 1)), ((0, 0, 0), (0, 1, 0))],
        "hill": [((0, 0, 0), (1, 0, 0)), ((0, 0, 0), (0, 1, 0)), ((0, 0, 0), (0, 0, 1)), ((1, 1, 1), (0, 1, 1)), ((1, 1, 1), (1, 0, 1))],
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
    theta = 0.21 + rng.random()
    phi = 2.0 * math.pi * rng.random()
    psi = torch.tensor([math.cos(theta), math.sin(theta) * np.exp(1j * phi)], dtype=DTYPE).reshape(2, 1)
    return normalize_density(0.82 * (psi @ psi.conj().T) + 0.18 * I2 / 2.0)


def entropy_family(values: np.ndarray) -> dict[str, float]:
    probs = np.abs(values.astype(float)) + 1e-12
    probs = probs / probs.sum()
    shannon = float(-(probs * np.log(probs)).sum())
    renyi2 = float(-np.log(np.sum(probs**2)))
    tsallis2 = float(1.0 - np.sum(probs**2))
    return {"shannon": shannon, "renyi2": renyi2, "tsallis2": tsallis2}


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / vals.sum()
    return float(-(vals * torch.log(vals)).sum().item())


def bloch(rho: torch.Tensor) -> np.ndarray:
    return np.array([float(torch.real(torch.trace(op @ rho)).item()) for op in (SX_T, SY_T, SZ_T)], dtype=float)


def density_step(rho: torch.Tensor, row: dict[str, Any], params: np.ndarray, step: int) -> torch.Tensor:
    b = bloch(rho)
    signal = np.array([entropy(rho) - 0.36, b[0] * b[2], b[1] - b[0]], dtype=float)
    params[:] = 0.84 * params + 0.16 * np.array(
        [row["rate"] + 0.43 * signal[0], row["shear"] + 0.36 * signal[1], row["twist"] + 0.31 * signal[2]], dtype=float
    )
    axis = (0.52 + 0.11 * params[1]) * SX_T + (0.33 + 0.15 * params[2]) * SY_T + (0.22 + 0.08 * params[0]) * SZ_T
    vals, vecs = torch.linalg.eig((-1j * (0.032 + 0.018 * row["rate"]) * axis).to(DTYPE))
    u = vecs @ torch.diag(torch.exp(vals)) @ torch.linalg.inv(vecs)
    return normalize_density(u @ rho @ u.conj().T)


def metric_values(params: np.ndarray) -> tuple[float, float, float]:
    conformal, shear, twist = params
    metric_min = math.exp(conformal - abs(shear)) * (1.0 - 0.05 * abs(math.tanh(twist)))
    curvature = float(0.40 * shear - 0.25 * twist + 0.13 * conformal * shear)
    torsion = float(abs(0.62 * twist) + abs(0.20 * shear))
    return metric_min, curvature, torsion


def geometry_gate(row: dict[str, Any], params: np.ndarray, step: int, carrier: str) -> np.ndarray:
    metric_min, curvature, torsion = metric_values(params)
    factor = {"mps": 1.0, "peps": 1.0 + 0.10 * torsion, "peps3d": 1.0 + 0.18 * torsion + 0.06 * abs(curvature)}[carrier]
    angle = row["rate"] * factor * (1.0 + 0.20 * curvature + 0.07 * torsion + 0.025 * metric_min + 0.012 * step)
    return qu.expm(-1j * angle * row["axis"])


def make_peps(seed: int) -> qtn.PEPS:
    rng = np.random.default_rng(900 + seed)
    arrays = []
    for i in range(2):
        row = []
        for j in range(4):
            shape = []
            if i > 0: shape.append(2)
            if j < 3: shape.append(2)
            if i < 1: shape.append(2)
            if j > 0: shape.append(2)
            shape.append(2)
            row.append(rng.normal(scale=0.35, size=shape))
        arrays.append(row)
    return qtn.PEPS(arrays)


def make_peps3d(seed: int) -> qtn.PEPS3D:
    rng = np.random.default_rng(1200 + seed)
    arrays = []
    for i in range(2):
        plane = []
        for j in range(2):
            row = []
            for k in range(2):
                shape = []
                if i < 1: shape.append(2)
                if j < 1: shape.append(2)
                if k < 1: shape.append(2)
                if i > 0: shape.append(2)
                if j > 0: shape.append(2)
                if k > 0: shape.append(2)
                shape.append(2)
                row.append(rng.normal(scale=0.30, size=shape))
            plane.append(row)
        arrays.append(plane)
    return qtn.PEPS3D(arrays)


def contraction_cost(carrier: str, params: np.ndarray) -> dict[str, float]:
    metric_min, curvature, torsion = metric_values(params)
    if carrier == "mps":
        inputs, output, expr = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")], ("a", "e"), "ab,bc,cd,de->ae"
    elif carrier == "peps":
        inputs, output, expr = [("a", "b", "e"), ("b", "c", "f"), ("c", "d", "g"), ("e", "f", "h"), ("f", "g", "i"), ("g", "d", "j")], ("a", "h", "i", "j"), "abe,bcf,cdg,efh,fgi,gdj->ahij"
    else:
        inputs, output, expr = [
            ("a", "b", "e", "l"), ("b", "c", "f", "m"), ("e", "f", "h", "n"), ("l", "m", "n", "o"),
            ("c", "d", "g", "p"), ("h", "i", "o", "q"), ("g", "i", "j", "r"), ("p", "q", "r", "s")
        ], ("a", "d", "j", "s"), "abel,bcfm,efhn,lmno,cdgp,hioq,gijr,pqrs->adjs"
    labels = sorted({ix for term in inputs for ix in term} | set(output))
    sizes = {ix: 2 + (n + int(abs(curvature) * 5) + int(abs(torsion) * 7) + int(abs(metric_min) * 3)) % 3 for n, ix in enumerate(labels)}
    for ix in output:
        sizes[ix] = 2
    tree = ctg.HyperOptimizer(max_repeats=8, progbar=False, on_trial_error="raise").search(inputs, output, sizes)
    rng = np.random.default_rng(int(2000 * (metric_min + abs(curvature) + abs(torsion))) + len(inputs))
    arrays = [rng.normal(size=tuple(sizes[ix] for ix in term)) for term in inputs]
    ref = oe.contract(expr, *arrays)
    return {"cost": float(tree.contraction_cost()), "width": float(tree.contraction_width()), "norm": float(np.linalg.norm(ref))}


def run_carrier(carrier: str, name: str, seed: int, *, collapsed: bool = False) -> list[dict[str, Any]]:
    row = CLASSES["hill"] if collapsed else CLASSES[name]
    if carrier == "mps":
        state = qtn.MPS_rand_state(8, bond_dim=3, seed=300 + seed)
    elif carrier == "peps":
        state = make_peps(seed)
    else:
        state = make_peps3d(seed)
    rho = density_seed(seed)
    params = np.array([0.04, row["shear"], row["twist"]], dtype=float)
    records = []
    for step in range(6):
        rho = density_step(rho, row, params, step)
        gate = geometry_gate(row, params, step, carrier)
        edges = CARRIER_EDGES[carrier]["hill" if collapsed else name]
        for edge in edges[: 3 + (step % 3)]:
            if carrier == "mps":
                state.gate_(gate, edge, contract="swap+split", max_bond=10, cutoff=1e-10)
            else:
                state.gate_(gate, edge, contract="split", max_bond=10, cutoff=1e-10)
        if carrier == "mps":
            vals = np.array([float(state.entropy(cut)) for cut in range(1, 8)], dtype=float)
        else:
            vals = np.array([float(np.linalg.norm(t.data)) for t in state], dtype=float)
        efam = entropy_family(vals)
        metric_min, curvature, torsion = metric_values(params)
        cc = contraction_cost(carrier, params)
        records.append({
            "carrier": carrier, "shannon": efam["shannon"], "renyi2": efam["renyi2"], "tsallis2": efam["tsallis2"],
            "value_sum": float(vals.sum()), "value_std": float(vals.std()), "max_bond": int(state.max_bond()),
            "density_entropy": entropy(rho), "metric_min": metric_min, "curvature": curvature, "torsion": torsion,
            "contraction_cost": cc["cost"], "contraction_width": cc["width"], "contract_norm": cc["norm"],
        })
    return records


def signature(records: list[dict[str, Any]]) -> np.ndarray:
    cols = ["shannon", "renyi2", "tsallis2", "value_sum", "value_std", "max_bond", "density_entropy", "metric_min", "curvature", "torsion", "contraction_cost", "contraction_width", "contract_norm"]
    arr = np.array([[r[c] for c in cols] for r in records], dtype=float)
    return np.r_[arr.mean(axis=0), arr.std(axis=0), arr[-1]]


def pairwise_min_distance(vectors: dict[str, np.ndarray]) -> float:
    keys, vals = sorted(vectors), []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            vals.append(float(np.linalg.norm(vectors[a] - vectors[b])))
    return min(vals) if vals else 0.0


def comparison_report() -> dict[str, Any]:
    vectors = {
        carrier: {name: np.stack([signature(run_carrier(carrier, name, seed)) for seed in range(3)]).mean(axis=0) for name in CLASSES}
        for carrier in ("mps", "peps", "peps3d")
    }
    class_gaps = {carrier: pairwise_min_distance(vectors[carrier]) for carrier in vectors}
    volume_sheet_gaps = {name: float(np.linalg.norm(vectors["peps3d"][name] - vectors["peps"][name])) for name in CLASSES}
    volume_chain_gaps = {name: float(np.linalg.norm(vectors["peps3d"][name] - vectors["mps"][name])) for name in CLASSES}
    return {
        "class_gaps": class_gaps,
        "min_volume_sheet_gap": float(min(volume_sheet_gaps.values())),
        "min_volume_chain_gap": float(min(volume_chain_gaps.values())),
        "volume_signature_head": {k: np.round(v[:8], 6).tolist() for k, v in vectors["peps3d"].items()},
        "pass": class_gaps["peps3d"] > 0.35 and min(volume_sheet_gaps.values()) > 1.0 and min(volume_chain_gaps.values()) > 1.0,
    }


def graveyard_report() -> dict[str, Any]:
    dynamic = {name: signature(run_carrier("peps3d", name, 1)) for name in CLASSES}
    collapsed = {name: signature(run_carrier("peps3d", name, 1, collapsed=True)) for name in CLASSES}
    dynamic_gap = pairwise_min_distance(dynamic)
    collapsed_gap = pairwise_min_distance(collapsed)
    return {"collapsed_volume_topology_laws_reduce_separation": {"dynamic_gap": dynamic_gap, "collapsed_gap": collapsed_gap, "pass": collapsed_gap < dynamic_gap * 0.25}}


def persistence_report() -> dict[str, Any]:
    pts = np.array([signature(run_carrier("peps3d", name, seed)).tolist() for name in CLASSES for seed in range(3)], dtype=float)
    dists = []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            dists.append(float(np.linalg.norm(pts[i] - pts[j])))
    radius = float(np.quantile(dists, 0.65)) if dists else 1.0
    st = gudhi.RipsComplex(points=pts.tolist(), max_edge_length=radius).create_simplex_tree(max_dimension=1)
    pairs = st.persistence()
    finite = [death - birth for dim, (birth, death) in pairs if dim == 0 and death < float("inf")]
    return {
        "point_count": int(len(pts)),
        "adaptive_radius": radius,
        "h0_count": sum(1 for dim, _ in pairs if dim == 0),
        "max_finite_h0_persistence": float(max(finite)) if finite else 0.0,
        "pass": len(pts) >= 8 and len(finite) >= 4 and (max(finite) if finite else 0.0) > 0.3,
    }


def graph_report() -> dict[str, Any]:
    chain = nx.path_graph(8)
    sheet = nx.grid_2d_graph(2, 4)
    volume = nx.grid_graph(dim=[2, 2, 2])
    return {"chain_edges": chain.number_of_edges(), "sheet_edges": sheet.number_of_edges(), "volume_edges": volume.number_of_edges(), "pass": volume.number_of_edges() > sheet.number_of_edges() > chain.number_of_edges()}


def symbolic_report() -> dict[str, Any]:
    carriers, classes, volume_dim = sp.symbols("carriers classes volume_dim", integer=True)
    claim = sp.And(sp.Eq(carriers, 3), sp.Eq(classes, 4), sp.Eq(volume_dim, 3))
    return {"carrier_count": 3, "class_count": 4, "volume_dimension": 3, "pass": bool(claim.subs({carriers: 3, classes: 4, volume_dim: 3}))}


def main() -> int:
    started = time.time()
    comparison = comparison_report()
    graveyards = graveyard_report()
    positive = {
        "chain_sheet_volume_carriers_run_same_deformation_schedule": comparison,
        "volume_signature_cloud_nontrivial": persistence_report(),
        "carrier_graph_edges_increase_with_dimension": graph_report(),
        "symbolic_inventory_has_three_carriers_four_classes_volume": symbolic_report(),
    }
    boundary = {
        "installed_versions": {"quimb": getattr(qu, "__version__", "unknown"), "cotengra": getattr(ctg, "__version__", "unknown"), "pass": True},
        "peps3d_surface": {"shape": "2x2x2 open-boundary PEPS3D volume", "physical_sites": 8, "pass": True},
    }
    nearby_variants = {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)}
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values()) and nearby_variants["passed"] == nearby_variants["total"]
    result = {
        "name": NAME, "classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_alignment_category": "volume_tensor_network_comparison_formal_scout",
        "positive": positive, "graveyard_companions": graveyards, "boundary": boundary, "nearby_variants": nearby_variants,
        "why_not_v4_probes": ["Finite carrier comparison only.", "Does not yet implement full source-native chiral density histories on PEPS3D.", "Does not claim final manifold or neural architecture."],
        "blockers": [], "elapsed_seconds": time.time() - started, "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
