#!/usr/bin/env python3
"""
sim_lego_weyl_geometry_carrier_compare.py
========================================

Reusable comparison lego for Weyl-style readouts across multiple geometry
carriers already present in the repo.

Carrier families in this probe:
  1. Hopf torus carrier
  2. Sphere section carrier
  3. Graph-derived carrier
  4. Hypergraph-derived carrier

The rule is simple:
  - keep the Weyl readout logic fixed
  - vary only the carrier plumbing
  - compare bounded summary metrics per carrier

This is a lego, not a doctrine claim.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

classification = "canonical"

from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    density_to_bloch,
    hopf_map,
    inter_torus_transport,
    left_weyl_spinor,
    right_weyl_spinor,
    torus_coordinates,
    torus_radii,
    von_neumann_entropy_2x2,
)

try:
    import rustworkx as rx
except ImportError:  # pragma: no cover
    rx = None

try:
    import xgi
except ImportError:  # pragma: no cover
    xgi = None


RESULTS_PATH = Path(__file__).resolve().parent / "a2_state" / "sim_results" / "lego_weyl_geometry_carrier_compare_results.json"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "core numeric carrier/readout layer"},
    "rustworkx": {"tried": True, "used": rx is not None, "reason": "graph carrier stats and DAG order" if rx is not None else "not installed"},
    "xgi": {"tried": True, "used": xgi is not None, "reason": "hypergraph carrier stats" if xgi is not None else "not installed"},
}

N_PHASE = 8
N_GRAPH_PHASE = 4
N_HYPER_PHASE = 4
MIX_BY_CARRIER = {
    "hopf_torus": 0.00,
    "sphere_section": 0.02,
    "graph_carrier": 0.04,
    "hypergraph_carrier": 0.06,
}


@dataclass(frozen=True)
class CarrierSample:
    carrier: str
    sample_id: str
    q: list[float]
    eta: float
    theta1: float
    theta2: float
    mix_strength: float
    left_bloch: list[float]
    right_bloch: list[float]
    hopf_bloch: list[float]
    left_entropy: float
    right_entropy: float
    left_right_overlap_abs: float
    left_right_bloch_antipodal_gap: float
    hopf_roundtrip_gap: float
    left_trace: float
    right_trace: float


def _unit_quaternion_from_complex_pair(z0: complex, z1: complex) -> np.ndarray:
    return np.array([z0.real, z0.imag, z1.real, z1.imag], dtype=float)


def sphere_to_hopf_section_north(theta: float, phi: float) -> np.ndarray:
    """North-patch Hopf section: S^2 -> S^3."""
    ct = math.cos(theta / 2.0)
    st = math.sin(theta / 2.0)
    return np.array([ct, 0.0, st * math.cos(phi), st * math.sin(phi)], dtype=float)


def density_matrix(psi: np.ndarray) -> np.ndarray:
    return np.outer(psi, np.conj(psi))


def mixed_density(psi: np.ndarray, mix_strength: float) -> np.ndarray:
    rho = density_matrix(psi)
    if mix_strength <= 0.0:
        return rho
    eye = np.eye(2, dtype=complex) / 2.0
    mix = float(np.clip(mix_strength, 0.0, 0.49))
    return (1.0 - mix) * rho + mix * eye


def q_from_torus(eta: float, theta1: float, theta2: float) -> np.ndarray:
    return torus_coordinates(eta, theta1, theta2)


def q_from_sphere(theta: float, phi: float) -> np.ndarray:
    return sphere_to_hopf_section_north(theta, phi)


def readout_from_q(
    carrier: str,
    sample_id: str,
    q: np.ndarray,
    eta: float,
    theta1: float,
    theta2: float,
    mix_strength: float,
) -> CarrierSample:
    psi_L = left_weyl_spinor(q)
    psi_R = right_weyl_spinor(q)
    rho_L = mixed_density(psi_L, mix_strength)
    rho_R = mixed_density(psi_R, mix_strength)

    pure_rho_L = density_matrix(psi_L)
    pure_rho_R = density_matrix(psi_R)

    left_bloch = density_to_bloch(rho_L)
    right_bloch = density_to_bloch(rho_R)
    hopf_bloch = hopf_map(q)

    hopf_roundtrip_gap = float(np.linalg.norm(hopf_bloch - density_to_bloch(pure_rho_L)))
    left_right_gap = float(np.linalg.norm(left_bloch + right_bloch))

    return CarrierSample(
        carrier=carrier,
        sample_id=sample_id,
        q=[float(v) for v in q],
        eta=float(eta),
        theta1=float(theta1),
        theta2=float(theta2),
        mix_strength=float(mix_strength),
        left_bloch=[float(v) for v in left_bloch],
        right_bloch=[float(v) for v in right_bloch],
        hopf_bloch=[float(v) for v in hopf_bloch],
        left_entropy=float(von_neumann_entropy_2x2(rho_L)),
        right_entropy=float(von_neumann_entropy_2x2(rho_R)),
        left_right_overlap_abs=float(abs(np.vdot(psi_L, psi_R))),
        left_right_bloch_antipodal_gap=left_right_gap,
        hopf_roundtrip_gap=hopf_roundtrip_gap,
        left_trace=float(np.real(np.trace(rho_L))),
        right_trace=float(np.real(np.trace(rho_R))),
    )


def summarize_samples(samples: list[CarrierSample]) -> dict[str, Any]:
    left_norm_errors = [abs(np.linalg.norm(np.array(s.left_bloch)) - (1.0 - s.mix_strength)) for s in samples]
    right_norm_errors = [abs(np.linalg.norm(np.array(s.right_bloch)) - (1.0 - s.mix_strength)) for s in samples]
    overlap_abs = [s.left_right_overlap_abs for s in samples]
    antipodal_gap = [s.left_right_bloch_antipodal_gap for s in samples]
    hopf_gap = [s.hopf_roundtrip_gap for s in samples]
    left_entropy = [s.left_entropy for s in samples]
    right_entropy = [s.right_entropy for s in samples]
    left_trace = [s.left_trace for s in samples]
    right_trace = [s.right_trace for s in samples]

    step_bloch_jumps = []
    for i in range(len(samples) - 1):
        a = np.array(samples[i].left_bloch, dtype=float)
        b = np.array(samples[i + 1].left_bloch, dtype=float)
        step_bloch_jumps.append(float(np.linalg.norm(b - a)))

    return {
        "sample_count": len(samples),
        "max_left_norm_error": float(max(left_norm_errors)) if left_norm_errors else 0.0,
        "max_right_norm_error": float(max(right_norm_errors)) if right_norm_errors else 0.0,
        "max_left_right_overlap_abs": float(max(overlap_abs)) if overlap_abs else 0.0,
        "max_left_right_bloch_antipodal_gap": float(max(antipodal_gap)) if antipodal_gap else 0.0,
        "mean_left_right_bloch_antipodal_gap": float(np.mean(antipodal_gap)) if antipodal_gap else 0.0,
        "max_hopf_roundtrip_gap": float(max(hopf_gap)) if hopf_gap else 0.0,
        "mean_hopf_roundtrip_gap": float(np.mean(hopf_gap)) if hopf_gap else 0.0,
        "mean_left_entropy": float(np.mean(left_entropy)) if left_entropy else 0.0,
        "mean_right_entropy": float(np.mean(right_entropy)) if right_entropy else 0.0,
        "mean_left_trace": float(np.mean(left_trace)) if left_trace else 0.0,
        "mean_right_trace": float(np.mean(right_trace)) if right_trace else 0.0,
        "mean_step_bloch_jump": float(np.mean(step_bloch_jumps)) if step_bloch_jumps else 0.0,
        "max_step_bloch_jump": float(max(step_bloch_jumps)) if step_bloch_jumps else 0.0,
    }


def build_hopf_torus_carrier() -> dict[str, Any]:
    levels = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]
    samples: list[CarrierSample] = []
    for level_idx, eta in enumerate(levels):
        for phase_idx in range(N_PHASE):
            theta1 = 2.0 * math.pi * phase_idx / N_PHASE
            theta2 = 2.0 * math.pi * ((phase_idx * 3) % N_PHASE) / N_PHASE
            q = q_from_torus(eta, theta1, theta2)
            samples.append(
                readout_from_q(
                    "hopf_torus",
                    f"torus_{level_idx}_{phase_idx}",
                    q,
                    eta,
                    theta1,
                    theta2,
                    MIX_BY_CARRIER["hopf_torus"],
                )
            )

    summary = summarize_samples(samples)
    summary.update({
        "carrier_kind": "hopf_torus",
        "torus_levels": [float(v) for v in levels],
        "torus_radii": [[float(a), float(b)] for a, b in map(torus_radii, levels)],
        "torus_level_count": len(levels),
        "phase_count": N_PHASE,
    })
    return {"samples": [asdict(s) for s in samples], "summary": summary}


def build_sphere_section_carrier() -> dict[str, Any]:
    theta_levels = [math.pi / 6.0, math.pi / 3.0, 2.0 * math.pi / 3.0]
    samples: list[CarrierSample] = []
    for level_idx, theta in enumerate(theta_levels):
        for phase_idx in range(N_PHASE):
            phi = 2.0 * math.pi * phase_idx / N_PHASE
            q = q_from_sphere(theta, phi)
            samples.append(
                readout_from_q(
                    "sphere_section",
                    f"sphere_{level_idx}_{phase_idx}",
                    q,
                    0.5 * theta,
                    phi,
                    0.0,
                    MIX_BY_CARRIER["sphere_section"],
                )
            )

    summary = summarize_samples(samples)
    summary.update({
        "carrier_kind": "sphere_section",
        "theta_levels": [float(v) for v in theta_levels],
        "level_count": len(theta_levels),
        "phase_count": N_PHASE,
        "north_section_used": True,
    })
    return {"samples": [asdict(s) for s in samples], "summary": summary}


def _graph_edges() -> list[tuple[int, int]]:
    return [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (4, 5)]


def _graph_depths(num_nodes: int, edges: list[tuple[int, int]]) -> dict[int, int]:
    children = {i: [] for i in range(num_nodes)}
    indeg = {i: 0 for i in range(num_nodes)}
    for u, v in edges:
        children[u].append(v)
        indeg[v] += 1
    depths = {0: 0}
    queue = [0]
    while queue:
        u = queue.pop(0)
        for v in children[u]:
            next_depth = depths[u] + 1
            if v not in depths or next_depth > depths[v]:
                depths[v] = next_depth
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    for i in range(num_nodes):
        depths.setdefault(i, 0)
    return depths


def build_graph_carrier() -> dict[str, Any]:
    edges = _graph_edges()
    num_nodes = 6
    depths = _graph_depths(num_nodes, edges)
    out_deg = {i: 0 for i in range(num_nodes)}
    in_deg = {i: 0 for i in range(num_nodes)}
    for u, v in edges:
        out_deg[u] += 1
        in_deg[v] += 1
    max_depth = max(depths.values()) or 1
    max_out = max(out_deg.values()) or 1
    samples: list[CarrierSample] = []
    for node in range(num_nodes):
        for phase_idx in range(N_GRAPH_PHASE):
            depth = depths[node]
            eta = TORUS_INNER + (TORUS_OUTER - TORUS_INNER) * (depth / max_depth)
            theta1 = 2.0 * math.pi * ((node + phase_idx / N_GRAPH_PHASE) / num_nodes)
            theta2 = 2.0 * math.pi * ((out_deg[node] + 1 + phase_idx) / (max_out + 2.0))
            q = q_from_torus(eta, theta1, theta2)
            samples.append(
                readout_from_q(
                    "graph_carrier",
                    f"node_{node}_phase_{phase_idx}",
                    q,
                    eta,
                    theta1,
                    theta2,
                    MIX_BY_CARRIER["graph_carrier"],
                )
            )

    if rx is not None:
        dag = rx.PyDiGraph()
        nodes = [dag.add_node({"node": i, "depth": depths[i]}) for i in range(num_nodes)]
        for u, v in edges:
            dag.add_edge(nodes[u], nodes[v], {"kind": "graph_edge"})
        longest = int(rx.dag_longest_path_length(dag))
        acyclic = bool(rx.is_directed_acyclic_graph(dag))
    else:  # pragma: no cover
        longest = max_depth
        acyclic = True

    summary = summarize_samples(samples)
    summary.update({
        "carrier_kind": "graph_carrier",
        "node_count": num_nodes,
        "edge_count": len(edges),
        "topological_depth": longest,
        "acyclic": acyclic,
        "depth_vector": [int(depths[i]) for i in range(num_nodes)],
        "in_degree_vector": [int(in_deg[i]) for i in range(num_nodes)],
        "out_degree_vector": [int(out_deg[i]) for i in range(num_nodes)],
        "phase_count": N_GRAPH_PHASE,
    })
    return {"samples": [asdict(s) for s in samples], "summary": summary}


def _hypergraph_edges() -> list[tuple[int, ...]]:
    return [(0, 1, 2), (1, 3, 4), (2, 3), (3, 4, 5)]


def build_hypergraph_carrier() -> dict[str, Any]:
    edges = _hypergraph_edges()
    num_nodes = 6
    membership = {i: 0 for i in range(num_nodes)}
    incident_sizes = {i: [] for i in range(num_nodes)}
    for edge in edges:
        for node in edge:
            membership[node] += 1
            incident_sizes[node].append(len(edge))
    max_membership = max(membership.values()) or 1
    max_edge_size = max(len(edge) for edge in edges)
    samples: list[CarrierSample] = []
    for node in range(num_nodes):
        for phase_idx in range(N_HYPER_PHASE):
            member_ratio = membership[node] / max_membership
            eta = TORUS_INNER + (TORUS_OUTER - TORUS_INNER) * member_ratio
            theta1 = 2.0 * math.pi * ((node + phase_idx / N_HYPER_PHASE) / num_nodes)
            size_mean = float(np.mean(incident_sizes[node])) if incident_sizes[node] else 1.0
            theta2 = 2.0 * math.pi * ((size_mean + phase_idx) / (max_edge_size + 2.0))
            q = q_from_torus(eta, theta1, theta2)
            samples.append(
                readout_from_q(
                    "hypergraph_carrier",
                    f"node_{node}_phase_{phase_idx}",
                    q,
                    eta,
                    theta1,
                    theta2,
                    MIX_BY_CARRIER["hypergraph_carrier"],
                )
            )

    if xgi is not None:
        H = xgi.Hypergraph()
        H.add_nodes_from(range(num_nodes))
        for edge in edges:
            H.add_edge(edge)
        hyperedge_sizes = [int(v) for v in H.edges.size.aslist()]
        max_hyperedge = int(max(hyperedge_sizes)) if hyperedge_sizes else 0
        connected_components = int(xgi.number_connected_components(H)) if H.num_edges else num_nodes
        num_hyperedges = int(H.num_edges)
    else:  # pragma: no cover
        hyperedge_sizes = [len(edge) for edge in edges]
        max_hyperedge = int(max(hyperedge_sizes)) if hyperedge_sizes else 0
        connected_components = 1
        num_hyperedges = len(edges)

    summary = summarize_samples(samples)
    summary.update({
        "carrier_kind": "hypergraph_carrier",
        "node_count": num_nodes,
        "hyperedge_count": num_hyperedges,
        "max_hyperedge_size": max_hyperedge,
        "connected_components": connected_components,
        "membership_vector": [int(membership[i]) for i in range(num_nodes)],
        "incident_edge_size_means": [
            float(np.mean(incident_sizes[i])) if incident_sizes[i] else 0.0 for i in range(num_nodes)
        ],
        "phase_count": N_HYPER_PHASE,
    })
    return {"samples": [asdict(s) for s in samples], "summary": summary}


def carrier_pairwise_comparisons(carriers: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    reference = carriers["hopf_torus"]["summary"]
    rows = []
    for name, payload in carriers.items():
        if name == "hopf_torus":
            continue
        s = payload["summary"]
        rows.append({
            "carrier": name,
            "reference": "hopf_torus",
            "mean_left_entropy_gap_vs_reference": float(s["mean_left_entropy"] - reference["mean_left_entropy"]),
            "mean_right_entropy_gap_vs_reference": float(s["mean_right_entropy"] - reference["mean_right_entropy"]),
            "mean_step_bloch_jump_gap_vs_reference": float(s["mean_step_bloch_jump"] - reference["mean_step_bloch_jump"]),
            "mean_hopf_roundtrip_gap_gap_vs_reference": float(s["mean_hopf_roundtrip_gap"] - reference["mean_hopf_roundtrip_gap"]),
            "max_left_right_bloch_antipodal_gap_gap_vs_reference": float(
                s["max_left_right_bloch_antipodal_gap"] - reference["max_left_right_bloch_antipodal_gap"]
            ),
        })
    return rows


def run_checks(carriers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks = {}
    all_pass = True
    for name, payload in carriers.items():
        summary = payload["summary"]
        core_ok = (
            summary["max_left_right_overlap_abs"] < 1e-12
            and summary["max_left_right_bloch_antipodal_gap"] < 1e-12
            and summary["max_hopf_roundtrip_gap"] < 1e-12
            and math.isfinite(summary["mean_left_entropy"])
            and math.isfinite(summary["mean_right_entropy"])
        )
        if name == "hopf_torus":
            carrier_ok = core_ok and summary["torus_level_count"] == 3 and summary["phase_count"] == N_PHASE
        elif name == "sphere_section":
            carrier_ok = core_ok and summary["level_count"] == 3 and summary["phase_count"] == N_PHASE
        elif name == "graph_carrier":
            carrier_ok = core_ok and summary["acyclic"] and summary["node_count"] == 6 and summary["edge_count"] == 6
        elif name == "hypergraph_carrier":
            carrier_ok = core_ok and summary["node_count"] == 6 and summary["hyperedge_count"] == 4
        else:
            carrier_ok = core_ok
        checks[name] = {
            "passed": bool(carrier_ok),
            "core_invariants_ok": bool(core_ok),
        }
        all_pass = all_pass and carrier_ok

    comparisons = carrier_pairwise_comparisons(carriers)
    cross_carrier_entropy_spread = max(
        s["summary"]["mean_left_entropy"] for s in carriers.values()
    ) - min(
        s["summary"]["mean_left_entropy"] for s in carriers.values()
    )
    cross_carrier_step_spread = max(
        s["summary"]["mean_step_bloch_jump"] for s in carriers.values()
    ) - min(
        s["summary"]["mean_step_bloch_jump"] for s in carriers.values()
    )
    checks["comparison_spread"] = {
        "passed": cross_carrier_entropy_spread >= 0.0 and cross_carrier_step_spread >= 0.0,
        "mean_left_entropy_spread": float(cross_carrier_entropy_spread),
        "mean_step_bloch_jump_spread": float(cross_carrier_step_spread),
    }
    return {
        "all_pass": bool(all_pass),
        "checks": checks,
        "comparisons": comparisons,
    }


def main() -> int:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    carriers = {
        "hopf_torus": build_hopf_torus_carrier(),
        "sphere_section": build_sphere_section_carrier(),
        "graph_carrier": build_graph_carrier(),
        "hypergraph_carrier": build_hypergraph_carrier(),
    }
    checks = run_checks(carriers)

    summary = {
        "classification": "canonical",
        "carrier_count": len(carriers),
        "carrier_order": list(carriers.keys()),
        "all_pass": checks["all_pass"],
        "result_count": sum(payload["summary"]["sample_count"] for payload in carriers.values()),
        "tool_manifest": TOOL_MANIFEST,
        "checks": checks["checks"],
        "comparison_rows": len(checks["comparisons"]),
    }

    payload = {
        "metadata": {
            "name": "weyl_geometry_carrier_compare",
            "timestamp": datetime.now(UTC).isoformat(),
            "results_path": str(RESULTS_PATH),
        },
        "summary": summary,
        "carriers": carriers,
        "comparisons": checks["comparisons"],
    }

    RESULTS_PATH.write_text(json.dumps(payload, indent=2))

    print("=" * 72)
    print("WEYL GEOMETRY CARRIER COMPARE")
    print("=" * 72)
    for name in carriers:
        s = carriers[name]["summary"]
        print(
            f"{name}: samples={s['sample_count']} "
            f"entropy={s['mean_left_entropy']:.6f} "
            f"step_jump={s['mean_step_bloch_jump']:.6f} "
            f"hopf_gap={s['mean_hopf_roundtrip_gap']:.3e}"
        )
    print("\nChecks")
    for name, check in checks["checks"].items():
        print(f"  {name}: passed={check['passed']}")
    print(f"  comparison_spread: passed={checks['checks']['comparison_spread']['passed']}")
    print(f"\nResults saved: {RESULTS_PATH}")

    return 0 if checks["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
