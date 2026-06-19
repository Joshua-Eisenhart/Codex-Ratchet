#!/usr/bin/env python3
"""PyTorch torch.func sensitivity leg for foundation_r6_oph_icosahedral_screen."""

from __future__ import annotations

import datetime as _dt
import itertools
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_oph_icosahedral_screen"
OBJECT_ID = "foundation_foundation_r6_oph_icosahedral_screen_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_oph_icosahedral_screen_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_oph_icosahedral_screen_pytorch_results.json"
TOL = 1.0e-10

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "supportive float64 graph-energy tensors for icosahedral and octahedral incidence controls"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity of the finite screen incidence energy under vertex-probe perturbations"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing"}


def parity(p: tuple[int, ...]) -> int:
    return sum(1 for i in range(len(p)) for j in range(i + 1, len(p)) if p[i] > p[j]) % 2


def compose(p: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(p[i] for i in q)


def generated_subgroup(generators: list[tuple[int, ...]], n: int) -> set[tuple[int, ...]]:
    identity = tuple(range(n))
    known = set([identity, *generators])
    changed = True
    while changed:
        changed = False
        snapshot = list(known)
        for a in snapshot:
            for b in snapshot:
                c = compose(a, b)
                if c not in known:
                    known.add(c)
                    changed = True
    return known


def icosahedral_edges() -> list[tuple[int, int]]:
    group = sorted(p for p in itertools.permutations(range(5)) if parity(p) == 0)
    index = {g: i for i, g in enumerate(group)}
    h = sorted(generated_subgroup([(1, 2, 3, 4, 0)], 5))
    cosets: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()
    for g in group:
        key = tuple(sorted(index[compose(g, h0)] for h0 in h))
        if key not in seen:
            seen.add(key)
            cosets.append(key)
    vertex_index = {c: i for i, c in enumerate(cosets)}

    def act(g: tuple[int, ...], vertex: int) -> int:
        key = tuple(sorted(index[compose(g, group[element_idx])] for element_idx in cosets[vertex]))
        return vertex_index[key]

    action = [[act(g, vertex) for vertex in range(len(cosets))] for g in group]
    h_orbits = []
    unseen_vertices = set(range(len(cosets)))
    while unseen_vertices:
        start = min(unseen_vertices)
        orbit = sorted({action[index[h0]][start] for h0 in h})
        h_orbits.append(orbit)
        unseen_vertices -= set(orbit)
    base_neighbors = next(orbit for orbit in h_orbits if 0 not in orbit and len(orbit) == 5)
    edges: set[tuple[int, int]] = set()
    for gi in range(len(group)):
        u = action[gi][0]
        for nb in base_neighbors:
            v = action[gi][nb]
            edges.add(tuple(sorted((u, v))))
    return sorted(edges)


def octahedral_edges() -> list[tuple[int, int]]:
    vertices = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    return [tuple(sorted((i, j))) for i in range(6) for j in range(i + 1, 6) if vertices[i] != tuple(-x for x in vertices[j])]


def adjacency(vertex_count: int, edges: list[tuple[int, int]]) -> torch.Tensor:
    mat = torch.zeros((vertex_count, vertex_count), dtype=torch.float64)
    for i, j in edges:
        mat[i, j] = 1.0
        mat[j, i] = 1.0
    return mat


def laplacian(adj: torch.Tensor) -> torch.Tensor:
    return torch.diag(torch.sum(adj, dim=1)) - adj


def graph_energy(lap: torch.Tensor, signal: torch.Tensor) -> torch.Tensor:
    return signal @ lap @ signal


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    ico_edges = icosahedral_edges()
    oct_edges = octahedral_edges()
    ico_adj = adjacency(12, ico_edges)
    oct_adj = adjacency(6, oct_edges)
    ico_lap = laplacian(ico_adj)
    oct_lap = laplacian(oct_adj)
    signal = torch.linspace(-1.1, 1.3, 12, dtype=torch.float64)
    signal = signal - torch.mean(signal)

    energy_fn = lambda x: graph_energy(ico_lap, x)
    grad = jacrev(energy_fn)(signal)
    expected_grad = 2.0 * ico_lap @ signal
    grad_residual = torch.linalg.vector_norm(grad - expected_grad)

    dropped_adj = ico_adj.clone()
    dropped_i, dropped_j = ico_edges[0]
    dropped_adj[dropped_i, dropped_j] = 0.0
    dropped_adj[dropped_j, dropped_i] = 0.0
    dropped_lap = laplacian(dropped_adj)
    dropped_grad = jacrev(lambda x: graph_energy(dropped_lap, x))(signal)
    drop_grad_delta = torch.linalg.vector_norm(grad - dropped_grad)

    oct_signal = torch.linspace(-0.7, 1.1, 6, dtype=torch.float64)
    oct_signal = oct_signal - torch.mean(oct_signal)
    oct_grad = jacrev(lambda x: graph_energy(oct_lap, x))(oct_signal)
    oct_expected_grad = 2.0 * oct_lap @ oct_signal
    oct_grad_residual = torch.linalg.vector_norm(oct_grad - oct_expected_grad)

    values = {
        "vertex_count": 12,
        "edge_count": len(ico_edges),
        "face_count": 20,
        "euler": 12 - len(ico_edges) + 20,
        "gradient_norm": float(torch.linalg.vector_norm(grad)),
        "gradient_residual": float(grad_residual),
        "drop_edge_gradient_delta": float(drop_grad_delta),
        "octahedral_gradient_norm": float(torch.linalg.vector_norm(oct_grad)),
        "octahedral_gradient_residual": float(oct_grad_residual),
    }
    negative = {
        "drop_edge_probe_changes_sensitivity": bool(drop_grad_delta > TOL),
        "octahedral_control_dimension_differs": tuple(oct_grad.shape) != tuple(grad.shape),
        "octahedral_control_edge_count_differs": len(oct_edges) != len(ico_edges),
        "torch_func_jacrev_independent_sensitivity": bool(values["gradient_norm"] > TOL and values["gradient_residual"] <= TOL),
    }
    all_pass = bool(
        values["edge_count"] == 30
        and values["euler"] == 2
        and values["gradient_residual"] <= TOL
        and values["octahedral_gradient_residual"] <= TOL
        and all(negative.values())
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "python_executable": sys.executable,
        "packages_used": ["torch", "torch.func", "json", "itertools", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch", "torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "M": {
            "name": "icosahedral_incidence_sensitivity_probe",
            "explicit_probe_family": ["Dirichlet energy x^T L_icosahedron x", "jacrev gradient dE/dx", "drop-one-edge and octahedral controls"],
            "finite_probe_domain": {"vertices": 12, "edges": len(ico_edges)},
        },
        "C": {
            "trace_equals_one": "not recomputed in torch; Julia QuantumOptics owns PSD/trace/Hermitian screen-state guard",
            "psd": "not recomputed in torch",
            "hermiticity": "not recomputed in torch",
            "normalization": "mean-zero float64 vertex signal for sensitivity only",
            "rung_specific_constraint": "sensitivity is computed against the 30-edge icosahedral incidence Laplacian",
        },
        "S_mod_M": {
            "definition": "incidence-sensitive signals are probed by the icosahedral graph Laplacian; removing an edge changes the differential response",
            "class_count": 1,
            "sensitivity_gradient_shape": list(grad.shape),
        },
        "summary": {
            **values,
            "jacrev_gradient": [float(x) for x in grad],
            "expected_2Lx_gradient": [float(x) for x in expected_grad],
            "genuine_independent_check": True,
            "independent_check_note": "torch.func.jacrev computes the differential sensitivity of the icosahedral screen incidence energy; it is not a mirror of Julia's group simplicity or JAX's SMT normal-subgroup proof.",
        },
        "negative_control_flip": negative,
        "octahedral_control": {"vertices": 6, "edges": len(oct_edges), "faces": 8, "euler": 6 - len(oct_edges) + 8},
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FOUNDATION_R6_OPH_ICOSAHEDRAL_SCREEN_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"grad_residual={result['summary']['gradient_residual']} "
        f"drop_delta={result['summary']['drop_edge_gradient_delta']} "
        f"oct_edges={result['octahedral_control']['edges']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
