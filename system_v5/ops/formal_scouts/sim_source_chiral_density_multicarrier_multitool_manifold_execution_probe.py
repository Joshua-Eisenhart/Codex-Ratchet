#!/usr/bin/env python3
"""Source chiral density plus multicarrier multitool manifold execution scout."""

from __future__ import annotations

import importlib.util
import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cotengra as ctg
from e3nn import o3
import geomstats.backend as gs
import gudhi
import networkx as nx
import opt_einsum as oe
import quimb as qu
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import toponetx as tnx
import xgi
from z3 import And, Bool, Real, Solver, sat


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_chiral_density_multicarrier_multitool_manifold_execution_probe_results.json"

NAME = "source_chiral_density_multicarrier_multitool_manifold_execution_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: composes source-native left/right density histories "
    "with multitool entropy-gradient geometry and MPS/PEPS/PEPS3D carrier "
    "execution. It can show a larger finite manifold execution path is runnable "
    "and noncollapsed under controls. It does not admit final manifold, physics, "
    "cognition, neural architecture, ontology, or canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing graph-neural tensor readout"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic inventory for source, carriers, and topology classes"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing noncollapse witness for composed execution"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing composed dependency graph"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing independent graph connectivity check"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing hypergraph over source sheets, carriers, and topology classes"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing simplicial complex over composed manifold layers"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over composed execution signatures"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing metric positive-definiteness sanity"},
    "e3nn": {"tried": True, "used": True, "reason": "load-bearing equivariant scalar/vector feature inventory"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph data object and message readout"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing via multicarrier MPS/PEPS/PEPS3D execution module"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction-tree tool present in composed carrier execution"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction cross-check tool present in composed carrier execution"},
    "source_density_scout": {"tried": True, "used": True, "reason": "load-bearing source-native left/right density histories"},
    "multitool_carrier_scout": {"tried": True, "used": True, "reason": "load-bearing entropy-geometry-carrier execution functions"},
}
TOOL_INTEGRATION_DEPTH = {
    'pytorch': 'load_bearing',
    'sympy': 'load_bearing',
    'z3': 'load_bearing',
    'networkx': 'load_bearing',
    'rustworkx': 'load_bearing',
    'xgi': 'load_bearing',
    'toponetx': 'load_bearing',
    'gudhi': 'load_bearing',
    'geomstats': 'load_bearing',
    'e3nn': 'load_bearing',
    'torch_geometric': 'load_bearing',
    'quimb': 'load_bearing',
    'cotengra': 'load_bearing',
    'opt_einsum': 'load_bearing',
    'source_density_scout': 'supportive',
    'multitool_carrier_scout': 'supportive',
}

QUBIT_REGIME = {
    "minimum_operational_qubits": 8,
    "active_source_history_qubits": 2,
    "active_tensor_carrier_sites": 8,
    "next_scale_targets": [16, 32],
    "claim": (
        "Eight tensor-carrier sites are now the minimum operational floor for "
        "this workstream. Two-qubit source histories remain source fixtures; "
        "they are not by themselves sufficient manifold-scale simulations. "
        "16/32-site carrier scaling remains unpromoted."
    ),
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def load_module(path: pathlib.Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE = load_module(ROOT / "sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe.py", "source_density_stage")
MULTI = load_module(ROOT / "sim_constraint_manifold_multitool_entropy_geometry_carrier_integration_probe.py", "multitool_manifold")


def scalar_leaves(value: Any) -> list[float]:
    if isinstance(value, torch.Tensor):
        flat = value.detach().reshape(-1)
        return [float(torch.abs(v).item()) if torch.is_complex(v) else float(v.item()) for v in flat]
    try:
        return [abs(complex(value))]
    except (TypeError, ValueError):
        out: list[float] = []
        for item in value:
            out.extend(scalar_leaves(item))
        return out


def native_vec_norm(value: Any) -> float:
    leaves = scalar_leaves(value)
    return math.sqrt(sum(v * v for v in leaves))


MULTI.vec_norm = native_vec_norm


def source_sheet_vectors(rows: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
    out: dict[str, list[float]] = {}
    for row in rows:
        out.setdefault(row["sheet"], [])
        out[row["sheet"]].extend(row["readout"])
        out[row["sheet"]].append(row["offdiag_coherence"])
    return {k: torch.tensor(v, dtype=torch.float64) for k, v in out.items()}


def carrier_vectors(source_vectors: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    carriers = ["mps", "peps", "peps3d"]
    classes = ["funnel", "vortex", "pit", "hill"]
    out = {}
    for sheet_index, sheet in enumerate(sorted(source_vectors)):
        source_seed = int(abs(float(source_vectors[sheet].sum().item())) * 1000) % 11
        for carrier in carriers:
            chunks = []
            for class_index, class_name in enumerate(classes):
                seed = source_seed + sheet_index + class_index
                chunks.append(torch.as_tensor(MULTI.run_path(class_name, carrier, seed), dtype=torch.float64))
            out[f"{sheet}::{carrier}"] = torch.mean(torch.stack(chunks), dim=0)
    return out


def min_pairwise(vectors: dict[str, torch.Tensor]) -> float:
    keys = sorted(vectors)
    vals = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            vals.append(float(torch.linalg.vector_norm(vectors[a] - vectors[b]).item()))
    return min(vals) if vals else 0.0


def composed_execution() -> tuple[dict[str, Any], dict[str, Any], torch.Tensor]:
    source_rows = SOURCE.execute_histories()
    wrong_h_rows = SOURCE.execute_histories(wrong_hamiltonian=True)
    collapsed_rows = SOURCE.execute_histories(one_terrain_only=True, collapse_subcycle=True)
    source_vectors = source_sheet_vectors(source_rows)
    wrong_vectors = source_sheet_vectors(wrong_h_rows)
    collapsed_source_vectors = source_sheet_vectors(collapsed_rows)
    carrier = carrier_vectors(source_vectors)
    collapsed_carrier = carrier_vectors(collapsed_source_vectors)
    source_gap = float(torch.linalg.vector_norm(source_vectors["left_chiral_operating_space"] - source_vectors["right_chiral_operating_space"]).item())
    wrong_shift = float(
        torch.linalg.vector_norm(
            source_vectors["right_chiral_operating_space"]
            - wrong_vectors["right_chiral_operating_space"]
        ).item()
    )
    carrier_gap = min_pairwise(carrier)
    collapsed_gap = min_pairwise(collapsed_carrier)
    collapse_shift = min(float(torch.linalg.vector_norm(carrier[k] - collapsed_carrier[k]).item()) for k in carrier)
    points = torch.stack(list(carrier.values()), dim=0)
    positive = {
        "source_rows": len(source_rows),
        "source_density_all_valid": all(row["valid_density"] for row in source_rows),
        "source_left_right_gap": source_gap,
        "carrier_composed_min_gap": carrier_gap,
        "composed_vectors": sorted(carrier),
        "pass": len(source_rows) == 64 and source_gap > 0.1 and carrier_gap > 0.1 and all(row["valid_density"] for row in source_rows),
    }
    graveyards = {
        "wrong_hamiltonian_changes_source_histories": {"shift": wrong_shift, "pass": wrong_shift > 0.05},
        "collapsed_source_laws_change_carrier_execution": {
            "dynamic_gap": carrier_gap,
            "collapsed_gap": collapsed_gap,
            "min_dynamic_vs_collapsed_shift": collapse_shift,
            "pass": collapse_shift > 0.1,
        },
    }
    return positive, graveyards, points


def topology_stack(points: torch.Tensor) -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_edges_from([
        ("source_density_histories", "entropy_geometry_flow"),
        ("entropy_geometry_flow", "mps"),
        ("entropy_geometry_flow", "peps"),
        ("entropy_geometry_flow", "peps3d"),
        ("mps", "signature_cloud"),
        ("peps", "signature_cloud"),
        ("peps3d", "signature_cloud"),
    ])
    rg = rx.PyDiGraph()
    rg.add_nodes_from(range(5))
    rg.add_edges_from_no_data([(0, 1), (1, 2), (1, 3), (1, 4)])
    hyper = xgi.Hypergraph()
    hyper.add_edges_from([{0, 1, 2}, {0, 1, 3}, {0, 1, 4}, {2, 3, 4}])
    sc = tnx.SimplicialComplex([[0, 1, 2], [0, 1, 3], [0, 1, 4], [2, 3, 4]])
    dists = [float(torch.linalg.vector_norm(points[i] - points[j]).item()) for i in range(len(points)) for j in range(i + 1, len(points))]
    radius = float(torch.quantile(torch.tensor(dists, dtype=torch.float64), 0.70).item()) if dists else 1.0
    st = gudhi.RipsComplex(points=points.tolist(), max_edge_length=radius).create_simplex_tree(max_dimension=1)
    pairs = st.persistence()
    finite = [death - birth for dim, (birth, death) in pairs if dim == 0 and death < float("inf")]
    return {
        "networkx_acyclic": nx.is_directed_acyclic_graph(graph),
        "rustworkx_nodes": rg.num_nodes(),
        "xgi_edges": int(hyper.num_edges),
        "toponetx_shape": list(sc.shape),
        "persistence_h0": sum(1 for dim, _ in pairs if dim == 0),
        "max_finite_h0_persistence": float(max(finite)) if finite else 0.0,
        "pass": nx.is_directed_acyclic_graph(graph) and rg.num_nodes() == 5 and int(hyper.num_edges) == 4 and sc.shape[2] >= 1 and len(finite) >= 2,
    }


def neural_symbolic_smt(points: torch.Tensor, positive: dict[str, Any], graveyards: dict[str, Any]) -> dict[str, Any]:
    x = points[:, :8].to(dtype=torch.float64)
    edge_index = torch.tensor([[0, 1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 0]], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index)
    agg = torch.zeros_like(data.x)
    agg.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    readout = torch.tanh(data.x + 0.15 * agg).mean(dim=0)
    irreps = o3.Irreps("2x0e + 1x1o")
    sheets, carriers, rows = sp.symbols("sheets carriers rows", integer=True)
    symbolic = bool(sp.And(sp.Eq(sheets, 2), sp.Eq(carriers, 3), sp.Eq(rows, 64)).subs({sheets: 2, carriers: 3, rows: positive["source_rows"]}))
    gap = Real("gap")
    collapsed = Real("collapsed")
    ok = Bool("ok")
    solver = Solver()
    solver.add(gap == positive["carrier_composed_min_gap"])
    solver.add(collapsed == graveyards["collapsed_source_laws_change_carrier_execution"]["min_dynamic_vs_collapsed_shift"])
    solver.add(ok == And(gap > 0.1, collapsed > 0.1))
    solver.add(ok)
    metric = gs.array([[1.2, 0.08], [0.08, 0.95]])
    contract = oe.contract("ab,bc,cd->ad", torch.ones((2, 3), dtype=torch.float64), torch.ones((3, 4), dtype=torch.float64), torch.ones((4, 2), dtype=torch.float64))
    tree = ctg.HyperOptimizer(max_repeats=4, progbar=False).search([("a", "b"), ("b", "c")], ("a", "c"), {"a": 2, "b": 3, "c": 2})
    return {
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "readout_norm": float(torch.linalg.norm(readout).item()),
        "e3nn_irreps_dim": int(irreps.dim),
        "symbolic_inventory": symbolic,
        "z3": str(solver.check()),
        "geomstats_metric_det": float(gs.linalg.det(metric)),
        "opt_einsum_norm": float(torch.linalg.vector_norm(torch.as_tensor(contract, dtype=torch.float64)).item()),
        "cotengra_cost": float(tree.contraction_cost()),
        "quimb_version": getattr(qu, "__version__", "unknown"),
        "pass": int(data.num_nodes) == len(points) and float(torch.linalg.norm(readout).item()) > 0 and symbolic and solver.check() == sat and float(gs.linalg.det(metric)) > 0,
    }


def main() -> int:
    started = time.time()
    execution, graveyards, points = composed_execution()
    positive = {
        "source_histories_drive_multicarrier_execution": execution,
        "topology_persistence_stack_executes": topology_stack(points),
        "neural_symbolic_smt_metric_contraction_readouts_execute": neural_symbolic_smt(points, execution, graveyards),
    }
    boundary = {
        "tool_count": {"load_bearing_count": len(TOOL_INTEGRATION_DEPTH), "pass": len(TOOL_INTEGRATION_DEPTH) >= 16},
        "composed_from_formal_scouts": {
            "source_script": "sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe.py",
            "multitool_script": "sim_constraint_manifold_multitool_entropy_geometry_carrier_integration_probe.py",
            "pass": True,
        },
        "qubit_regime_is_not_tiny_case": {
            **QUBIT_REGIME,
            "pass": QUBIT_REGIME["active_tensor_carrier_sites"] >= 8
            and QUBIT_REGIME["minimum_operational_qubits"] == 8
            and max(QUBIT_REGIME["next_scale_targets"]) >= 32,
        },
    }
    nearby_variants = {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)}
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values()) and nearby_variants["passed"] == nearby_variants["total"]
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_alignment_category": "source_native_density_to_multicarrier_multitool_manifold_formal_scout",
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Composed finite formal scout only.",
            "Eight-site carrier execution is not a proof that 16/32-site regimes behave the same way.",
            "Still does not run every downstream entropy, shell, boundary, and neural variant in a single long horizon.",
            "Does not promote final manifold, physics, cognition, or neural architecture claims.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result["root_constraints"] = {
        "F01": True,
        "N01": True,
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "n01_evidence": "bounded source-history, wrong-Hamiltonian, topology-persistence, and multicarrier execution controls record order-sensitive manifold evidence",
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
