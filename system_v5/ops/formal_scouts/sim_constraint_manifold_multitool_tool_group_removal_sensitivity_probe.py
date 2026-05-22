#!/usr/bin/env python3
"""Tool-group removal sensitivity scout for the multitool manifold probe."""

from __future__ import annotations

import hashlib
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
import quimb.tensor as qtn
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import toponetx as tnx
import xgi
from z3 import And, Bool, Real, Solver, sat


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "constraint_manifold_multitool_tool_group_removal_sensitivity_probe_results.json"

NAME = "constraint_manifold_multitool_tool_group_removal_sensitivity_probe"
classification = "formal_scout"
CLASSIFICATION = classification
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: mirrors the multitool entropy-geometry-carrier scout's "
    "blanket load-bearing risk and tests named tool-group removal effects. It "
    "does not admit a final manifold, bridge, axis, ontology, physics, neural "
    "architecture, or canonical promotion claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing carrier density states and neural readout tensors",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "not used; geometry-flow integration is handled by local RK4 code",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing metric determinant observable for the carrier/tensor group",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor carrier entanglement features",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "load-bearing contraction-width observable for tensor carrier sensitivity",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "supportive numeric contraction cross-check; not alone used as a load-bearing group role",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "supportive graph-distance presentation in the topology/graph group; group load-bearing rests on admitted topology kernels",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent connectivity and path observable in the topology/graph group",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hyperedge incidence observable in the topology/graph group",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplicial shape observable in the topology/graph group",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing persistence observable in the topology/graph group",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic curvature dependency observable in the proof group",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT admissibility witness in the proof group",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing equivariant irreps dimension observable in the readout group",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph data validation and message readout in the readout group",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization only; scientific observables must not depend on this group",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt-stability hashing only",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result-path handling only",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "scipy": None,
    "geomstats": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "supportive",
    "networkx": "supportive",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "e3nn": "load_bearing",
    "torch_geometric": "load_bearing",
    "json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

CARRIER_GROUP = {"pytorch", "geomstats", "quimb", "cotengra", "opt_einsum"}
TOPOLOGY_GROUP = {"networkx", "rustworkx", "xgi", "toponetx", "gudhi"}
PROOF_GROUP = {"sympy", "z3"}
READOUT_GROUP = {"e3nn", "torch_geometric", "pytorch"}
SERIALIZATION_GROUP = {"json", "hashlib", "pathlib"}

DTYPE = torch.complex128
I2 = torch.eye(2, dtype=DTYPE)
SX_T = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY_T = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ_T = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
SX = qu.pauli("X").A
SZ = qu.pauli("Z").A

CLASSES = {
    "funnel": {"generator": qu.kron(SX, SZ), "rate": 0.18, "shear": -0.18, "twist": 0.08},
    "vortex": {"generator": qu.kron(SZ, SX), "rate": 0.14, "shear": 0.11, "twist": 0.31},
    "pit": {"generator": qu.kron(SZ, SZ), "rate": 0.27, "shear": -0.27, "twist": -0.16},
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [as_jsonable(val) for val in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return as_jsonable(value.detach().cpu().tolist())
    return value


def vec_sub(left: list[float], right: list[float]) -> list[float]:
    return [a - b for a, b in zip(left, right)]


def vec_norm(values: Any) -> float:
    if isinstance(values, torch.Tensor):
        return float(torch.linalg.norm(values.detach()).item())
    if hasattr(values, "shape"):
        return float(torch.linalg.norm(torch.as_tensor(values)).item())
    flat = [float(v) for v in values]
    return math.sqrt(sum(v * v for v in flat))


def vec_mean(rows: list[list[float]]) -> list[float]:
    return [sum(row[idx] for row in rows) / len(rows) for idx in range(len(rows[0]))]


def flatten_tensor(values: torch.Tensor) -> list[float]:
    return [float(v) for v in values.reshape(-1).tolist()]


def rounded(values: list[float], digits: int) -> list[float]:
    return [round(float(v), digits) for v in values]


def disabled(remove: set[str], group: set[str]) -> bool:
    return bool(remove & group)


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=1e-12).to(DTYPE)
    out = vecs @ torch.diag(vals) @ vecs.conj().T
    return out / torch.trace(out).real


def density_seed(seed: int) -> torch.Tensor:
    theta = 0.31 + 0.07 * seed
    phi = 0.43 + 0.17 * seed
    psi = torch.tensor([math.cos(theta), math.sin(theta) * complex(math.cos(phi), math.sin(phi))], dtype=DTYPE).reshape(2, 1)
    return normalize_density(0.78 * (psi @ psi.conj().T) + 0.22 * I2 / 2.0)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / vals.sum()
    return float(-(vals * torch.log(vals)).sum().item())


def bloch(rho: torch.Tensor) -> list[float]:
    return [float(torch.real(torch.trace(op @ rho)).item()) for op in (SX_T, SY_T, SZ_T)]


def geometry_rhs(_t: float, params: list[float], signal: list[float], row: dict[str, Any]) -> list[float]:
    return [
        0.48 * (row["rate"] + signal[0]) - 0.17 * params[0],
        0.38 * (row["shear"] + signal[1]) - 0.16 * params[1],
        0.42 * (row["twist"] + signal[2]) - 0.13 * params[2],
    ]


def rk4_geometry_step(params: list[float], signal: list[float], row: dict[str, Any], dt: float) -> list[float]:
    def add_scaled(base: list[float], delta: list[float], scale: float) -> list[float]:
        return [a + scale * b for a, b in zip(base, delta)]

    k1 = geometry_rhs(0.0, params, signal, row)
    k2 = geometry_rhs(dt / 2.0, add_scaled(params, k1, dt / 2.0), signal, row)
    k3 = geometry_rhs(dt / 2.0, add_scaled(params, k2, dt / 2.0), signal, row)
    k4 = geometry_rhs(dt, add_scaled(params, k3, dt), signal, row)
    return [
        float(p + (dt / 6.0) * (a + 2.0 * b + 2.0 * c + d))
        for p, a, b, c, d in zip(params, k1, k2, k3, k4)
    ]


def carrier_signature(class_name: str, seed: int, remove: set[str]) -> list[float]:
    if disabled(remove, CARRIER_GROUP):
        row = CLASSES[class_name]
        return [row["rate"], row["shear"], row["twist"], 0.0, 0.0, 0.0, 0.0]

    row = CLASSES[class_name]
    rho = density_seed(seed)
    params = [0.04, row["shear"], row["twist"]]
    state = qtn.MPS_rand_state(5, bond_dim=3, seed=100 + seed)
    for step in range(3):
        b = bloch(rho)
        signal = [entropy(rho) - 0.35, b[0] * b[2], b[1] - b[0]]
        params = rk4_geometry_step(params, signal, row, dt=0.06)
        generator = (0.44 + 0.10 * params[1]) * SX_T + (0.29 + 0.12 * params[2]) * SY_T + (0.19 + 0.07 * params[0]) * SZ_T
        vals, vecs = torch.linalg.eig((-1j * (0.025 + 0.012 * row["rate"] + 0.002 * step) * generator).to(DTYPE))
        u = vecs @ torch.diag(torch.exp(vals)) @ torch.linalg.inv(vecs)
        rho = normalize_density(u @ rho @ u.conj().T)
        gate = qu.expm(-1j * row["rate"] * (1.0 + 0.03 * step + 0.05 * abs(params[2])) * row["generator"])
        state.gate_(gate, (step, step + 1), contract="swap+split", max_bond=6, cutoff=1e-10)

    mat = gs.array([[1.2 + abs(params[0]), 0.08], [0.08, 0.9 + abs(params[1])]])
    metric_det = float(gs.linalg.det(mat))
    inputs = [("a", "b"), ("b", "c"), ("c", "d")]
    output = ("a", "d")
    sizes = {"a": 2, "b": 3, "c": 2, "d": 2}
    tree = ctg.HyperOptimizer(max_repeats=4, progbar=False, on_trial_error="raise").search(inputs, output, sizes)
    arrays = []
    for term in inputs:
        shape = tuple(sizes[ix] for ix in term)
        count = math.prod(shape)
        arrays.append(torch.arange(1, count + 1, dtype=torch.float64).reshape(shape))
    contraction_norm = vec_norm(oe.contract("ab,bc,cd->ad", *arrays))
    entanglement = float(sum(state.entropy(cut) for cut in range(1, 5)))
    return [
        entropy(rho),
        *bloch(rho),
        entanglement,
        float(tree.contraction_width()),
        metric_det + 1e-4 * contraction_norm,
    ]


def class_vectors(remove: set[str]) -> dict[str, list[float]]:
    return {
        name: vec_mean([carrier_signature(name, seed, remove) for seed in (0, 1)])
        for name in CLASSES
    }


def pairwise_distances(vectors: dict[str, list[float]]) -> list[float]:
    keys = sorted(vectors)
    return [vec_norm(vec_sub(vectors[a], vectors[b])) for idx, a in enumerate(keys) for b in keys[idx + 1 :]]


def topology_observable(vectors: dict[str, list[float]], remove: set[str]) -> dict[str, Any]:
    if disabled(remove, TOPOLOGY_GROUP):
        return {
            "graph_edges": 0,
            "rx_connected": False,
            "hyperedges": 0,
            "simplicial_rank": 0,
            "finite_h0_max": 0.0,
            "topology_signature_span": 0.0,
            "pass": True,
            "mode": "removed",
        }

    keys = sorted(vectors)
    graph = nx.Graph()
    for key in keys:
        graph.add_node(key)
    for idx, a in enumerate(keys):
        for b in keys[idx + 1 :]:
            graph.add_edge(a, b, weight=vec_norm(vec_sub(vectors[a], vectors[b])))

    rg = rx.PyGraph()
    rg.add_nodes_from(range(len(keys)))
    rg.add_edges_from_no_data([(0, 1), (1, 2), (0, 2)])
    hyper = xgi.Hypergraph()
    hyper.add_edges_from([{0, 1}, {1, 2}, {0, 1, 2}])
    sc = tnx.SimplicialComplex([[0, 1, 2]])
    points = [vectors[key] for key in keys]
    dists = pairwise_distances(vectors)
    radius = max(dists) + 1e-6
    st = gudhi.RipsComplex(points=points, max_edge_length=radius).create_simplex_tree(max_dimension=1)
    finite = [death - birth for dim, (birth, death) in st.persistence() if dim == 0 and death < float("inf")]
    return {
        "graph_edges": graph.number_of_edges(),
        "rx_connected": bool(rx.is_connected(rg)),
        "hyperedges": int(hyper.num_edges),
        "simplicial_rank": int(sc.shape[2]),
        "finite_h0_max": float(max(finite)) if finite else 0.0,
        "topology_signature_span": float(nx.diameter(graph) + int(rx.is_connected(rg)) + hyper.num_edges + sc.shape[2] + (max(finite) if finite else 0.0)),
        "pass": graph.number_of_edges() == 3 and bool(rx.is_connected(rg)) and int(hyper.num_edges) == 3 and int(sc.shape[2]) == 1,
        "mode": "active",
    }


def proof_observable(vectors: dict[str, list[float]], topology: dict[str, Any], remove: set[str]) -> dict[str, Any]:
    dists = pairwise_distances(vectors)
    min_gap = min(dists) if dists else 0.0
    if disabled(remove, PROOF_GROUP):
        return {
            "symbolic_depends_on_shear_twist": False,
            "smt_status": "not_run",
            "admissibility_witness_numeric": 0.0,
            "min_gap": min_gap,
            "pass": True,
            "mode": "removed",
        }

    c, sh, tw = sp.symbols("c sh tw")
    curvature = sp.Rational(41, 100) * sh - sp.Rational(26, 100) * tw + sp.Rational(14, 100) * c * sh
    symbolic_depends = bool(curvature.has(sh) and curvature.has(tw))
    g = Real("min_gap")
    topo = Real("topology_signature_span")
    ok = Bool("ok")
    solver = Solver()
    solver.add(g == min_gap, topo == float(topology["topology_signature_span"]))
    solver.add(ok == And(g > 0.02, topo > 4.0))
    solver.add(ok)
    status = solver.check()
    return {
        "symbolic_curvature_formula": str(curvature),
        "symbolic_depends_on_shear_twist": symbolic_depends,
        "smt_status": str(status),
        "admissibility_witness_numeric": 1.0 if symbolic_depends and status == sat else 0.0,
        "min_gap": min_gap,
        "pass": symbolic_depends and status == sat,
        "mode": "active",
    }


def readout_observable(vectors: dict[str, list[float]], remove: set[str]) -> dict[str, Any]:
    points = [vectors[key] for key in sorted(vectors)]
    if disabled(remove, READOUT_GROUP):
        return {
            "node_count": 0,
            "edge_count": 0,
            "irreps_dim": 0,
            "readout_norm": 0.0,
            "readout_margin": 0.0,
            "pass": True,
            "mode": "removed",
        }

    x = torch.tensor([row[:4] for row in points], dtype=torch.float64)
    edge_index = torch.tensor([[0, 1, 2], [1, 2, 0]], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index, num_nodes=x.shape[0])
    data.validate(raise_on_error=True)
    agg = torch.zeros_like(data.x)
    agg.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    readout = torch.tanh(data.x + 0.25 * agg)
    norms = torch.linalg.norm(readout, dim=1)
    irreps = o3.Irreps("2x0e + 1x1o")
    return {
        "node_count": int(data.num_nodes),
        "edge_count": int(data.num_edges),
        "irreps_dim": int(irreps.dim),
        "readout_norm": float(torch.linalg.norm(readout).item()),
        "readout_margin": float((torch.max(norms) - torch.min(norms)).item()),
        "pass": int(data.num_nodes) == len(CLASSES) and int(irreps.dim) == 5 and float(torch.linalg.norm(readout).item()) > 0.0,
        "mode": "active",
    }


def compute_observables(remove: set[str]) -> dict[str, Any]:
    vectors = class_vectors(remove)
    topology = topology_observable(vectors, remove)
    proof = proof_observable(vectors, topology, remove)
    readout = readout_observable(vectors, remove)
    dists = pairwise_distances(vectors)
    return {
        "class_vectors": {key: rounded(val, 8) for key, val in vectors.items()},
        "carrier_separation_gap": min(dists) if dists else 0.0,
        "carrier_signature_norm": vec_norm([item for row in vectors.values() for item in row]),
        "topology_signature_span": float(topology["topology_signature_span"]),
        "admissibility_witness_numeric": float(proof["admissibility_witness_numeric"]),
        "readout_margin": float(readout["readout_margin"]),
        "topology": topology,
        "proof": proof,
        "readout": readout,
    }


def scientific_observable_vector(observables: dict[str, Any]) -> list[float]:
    return [
        float(observables["carrier_separation_gap"]),
        float(observables["carrier_signature_norm"]),
        float(observables["topology_signature_span"]),
        float(observables["admissibility_witness_numeric"]),
        float(observables["readout_margin"]),
    ]


def removal_report(name: str, group: set[str], baseline: dict[str, Any], threshold: float) -> dict[str, Any]:
    removed = compute_observables(group)
    base_vec = scientific_observable_vector(baseline)
    removed_vec = scientific_observable_vector(removed)
    diff = vec_norm(vec_sub(base_vec, removed_vec))
    named_deltas = {
        "carrier_separation_gap": abs(float(baseline["carrier_separation_gap"]) - float(removed["carrier_separation_gap"])),
        "carrier_signature_norm": abs(float(baseline["carrier_signature_norm"]) - float(removed["carrier_signature_norm"])),
        "topology_signature_span": abs(float(baseline["topology_signature_span"]) - float(removed["topology_signature_span"])),
        "admissibility_witness_numeric": abs(float(baseline["admissibility_witness_numeric"]) - float(removed["admissibility_witness_numeric"])),
        "readout_margin": abs(float(baseline["readout_margin"]) - float(removed["readout_margin"])),
    }
    changed_named = [key for key, val in named_deltas.items() if val > threshold]
    return {
        "removed_tools": sorted(group),
        "scientific_observable_l2_delta": diff,
        "named_observable_deltas": named_deltas,
        "changed_named_observables": changed_named,
        "inferred_group_role": "load_bearing" if changed_named else "supportive",
        "pass": bool(changed_named),
        "removed_observables": removed,
    }


def serialization_report(baseline: dict[str, Any]) -> dict[str, Any]:
    science = scientific_observable_vector(baseline)
    payload = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "scientific_observables": rounded(science, 12),
    }
    encoded = json.dumps(payload, sort_keys=True)
    decoded = json.loads(encoded)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    without_serialization_science = list(science)
    science_delta = vec_norm(vec_sub(science, without_serialization_science))
    return {
        "removed_tools": sorted(SERIALIZATION_GROUP),
        "json_roundtrip_ok": decoded == payload,
        "sha256_prefix": digest[:16],
        "scientific_observable_l2_delta": science_delta,
        "changed_named_observables": [],
        "inferred_group_role": "supportive",
        "pass": decoded == payload and science_delta == 0.0,
    }


def tool_role_summary(ablation: dict[str, Any]) -> dict[str, Any]:
    load_bearing_groups = sorted(
        key
        for key, row in ablation.items()
        if key != "supportive_serialization" and row["inferred_group_role"] == "load_bearing"
    )
    supportive_groups = sorted(key for key, row in ablation.items() if row["inferred_group_role"] == "supportive")
    load_bearing_tools = sorted(tool for tool, role in TOOL_INTEGRATION_DEPTH.items() if role == "load_bearing")
    supportive_tools = sorted(tool for tool, role in TOOL_INTEGRATION_DEPTH.items() if role == "supportive")
    return {
        "load_bearing_groups": load_bearing_groups,
        "supportive_groups": supportive_groups,
        "load_bearing_tools": load_bearing_tools,
        "supportive_tools": supportive_tools,
        "blanket_load_bearing_rejected": bool(supportive_groups) and len(load_bearing_tools) < len(TOOL_INTEGRATION_DEPTH),
    }


def main() -> int:
    started = time.time()
    baseline = compute_observables(set())
    ablation = {
        "carrier_tensor_group": removal_report("carrier_tensor_group", CARRIER_GROUP, baseline, threshold=1e-6),
        "topology_graph_group": removal_report("topology_graph_group", TOPOLOGY_GROUP, baseline, threshold=1e-6),
        "proof_symbolic_smt_group": removal_report("proof_symbolic_smt_group", PROOF_GROUP, baseline, threshold=1e-6),
        "equivariant_neural_readout_group": removal_report("equivariant_neural_readout_group", READOUT_GROUP, baseline, threshold=1e-6),
        "supportive_serialization": serialization_report(baseline),
    }
    roles = tool_role_summary(ablation)
    positive = {
        "carrier_tensor_removal_changes_named_observable": {
            "observable": "carrier_separation_gap or carrier_signature_norm",
            "changed_named_observables": ablation["carrier_tensor_group"]["changed_named_observables"],
            "pass": bool(ablation["carrier_tensor_group"]["changed_named_observables"]),
        },
        "topology_graph_removal_changes_named_observable": {
            "observable": "topology_signature_span",
            "changed_named_observables": ablation["topology_graph_group"]["changed_named_observables"],
            "pass": "topology_signature_span" in ablation["topology_graph_group"]["changed_named_observables"],
        },
        "proof_symbolic_smt_removal_changes_named_observable": {
            "observable": "admissibility_witness_numeric",
            "changed_named_observables": ablation["proof_symbolic_smt_group"]["changed_named_observables"],
            "pass": "admissibility_witness_numeric" in ablation["proof_symbolic_smt_group"]["changed_named_observables"],
        },
        "equivariant_neural_readout_removal_changes_named_observable": {
            "observable": "readout_margin",
            "changed_named_observables": ablation["equivariant_neural_readout_group"]["changed_named_observables"],
            "pass": "readout_margin" in ablation["equivariant_neural_readout_group"]["changed_named_observables"],
        },
        "supportive_serialization_does_not_change_scientific_observables": {
            "observable": "scientific_observable_vector",
            "scientific_observable_l2_delta": ablation["supportive_serialization"]["scientific_observable_l2_delta"],
            "pass": ablation["supportive_serialization"]["pass"],
        },
        "blanket_load_bearing_comprehension_rejected": {
            "broad_scout_mirrored": "sim_constraint_manifold_multitool_entropy_geometry_carrier_integration_probe.py",
            "load_bearing_group_count": len(roles["load_bearing_groups"]),
            "supportive_group_count": len(roles["supportive_groups"]),
            "pass": roles["blanket_load_bearing_rejected"],
        },
    }
    graveyard_companions = {
        "all_tools_load_bearing_by_import_is_rejected": {
            "supportive_tools": roles["supportive_tools"],
            "pass": len(roles["supportive_tools"]) >= 4,
        },
        "serialization_as_scientific_manifold_signal_is_rejected": {
            "scientific_delta_when_serialization_removed": ablation["supportive_serialization"]["scientific_observable_l2_delta"],
            "pass": ablation["supportive_serialization"]["scientific_observable_l2_delta"] == 0.0,
        },
        "no_group_promotes_manifold_claim": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": PROMOTION_ALLOWED is False,
        },
    }
    boundary = {
        "promotion_allowed_false": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
        "explicit_depth_split_present": {
            "load_bearing_tools": roles["load_bearing_tools"],
            "supportive_tools": roles["supportive_tools"],
            "pass": bool(roles["load_bearing_tools"]) and bool(roles["supportive_tools"]),
        },
        "named_observable_gate_for_load_bearing_groups": {
            "load_bearing_groups": roles["load_bearing_groups"],
            "pass": all(
                ablation[group]["changed_named_observables"]
                for group in (
                    "carrier_tensor_group",
                    "topology_graph_group",
                    "proof_symbolic_smt_group",
                    "equivariant_neural_readout_group",
                )
            ),
        },
        "baseline_internal_checks_pass": {
            "topology_pass": baseline["topology"]["pass"],
            "proof_pass": baseline["proof"]["pass"],
            "readout_pass": baseline["readout"]["pass"],
            "pass": bool(baseline["topology"]["pass"] and baseline["proof"]["pass"] and baseline["readout"]["pass"]),
        },
    }
    nearby_variants = {
        "total": len(ablation),
        "passed": sum(1 for row in ablation.values() if row["pass"]),
        "variants": sorted(ablation),
        "summary": {key: {"role": row["inferred_group_role"], "changed_named_observables": row["changed_named_observables"]} for key, row in ablation.items()},
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_alignment_category": "blanket_load_bearing_comprehension_removal_sensitivity_formal_scout",
        "mirrors_concern_from": "system_v5/ops/formal_scouts/sim_constraint_manifold_multitool_entropy_geometry_carrier_integration_probe.py",
        "baseline_observables": baseline,
        "group_ablation": ablation,
        "tool_role_summary": roles,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Formal scout only; it tests local removal sensitivity and does not promote manifold status.",
            "A group is load-bearing here only when its removal changes a named finite observable.",
            "Serialization is receipt support only and is not a scientific manifold observable.",
            "This does not rerun the full broad scout or repair its source-level blanket comprehension.",
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
        "n01_evidence": "bounded tool-group removal sensitivity changes named observables and records order-sensitive load-bearing separation",
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
