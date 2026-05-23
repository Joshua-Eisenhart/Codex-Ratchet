#!/usr/bin/env python3
"""GUDHI homology readout for Hopf torus fiber and base loops."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import math
from pathlib import Path

import gudhi
import numpy as np
from receipt_boundary import apply_default_receipt_boundary


NAME = "gudhi_hopf_torus_fiber_base_homology"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "builds explicit simplicial complexes and computes Betti numbers for torus, fiber-loop, base-loop, and collapsed controls",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples Hopf-coordinate S3 embeddings and computes coordinate variation diagnostics",
    },
}
TOOL_INTEGRATION_DEPTH = {"gudhi": "load_bearing", "numpy": "supportive"}


def hopf_s3_point(theta: float, phi: float, xi: float) -> np.ndarray:
    a = math.cos(theta / 2.0) * np.exp(1j * (xi + phi) / 2.0)
    b = math.sin(theta / 2.0) * np.exp(1j * (xi - phi) / 2.0)
    return np.array([a.real, a.imag, b.real, b.imag], dtype=float)


def sample_hopf_torus(theta: float, size: int) -> np.ndarray:
    points = []
    for phi in np.linspace(0.0, 2.0 * math.pi, size, endpoint=False):
        for xi in np.linspace(0.0, 2.0 * math.pi, size, endpoint=False):
            points.append(hopf_s3_point(theta, float(phi), float(xi)))
    return np.asarray(points, dtype=float)


def sample_loop(theta: float, *, vary: str, samples: int) -> np.ndarray:
    points = []
    for value in np.linspace(0.0, 2.0 * math.pi, samples, endpoint=False):
        phi = float(value) if vary == "base" else 0.0
        xi = float(value) if vary == "fiber" else 0.0
        points.append(hopf_s3_point(theta, phi, xi))
    return np.asarray(points, dtype=float)


def add_periodic_grid_torus(st: gudhi.SimplexTree, size: int) -> None:
    def vertex(i: int, j: int) -> int:
        return (i % size) * size + (j % size)

    for i in range(size):
        for j in range(size):
            v00 = vertex(i, j)
            v10 = vertex(i + 1, j)
            v01 = vertex(i, j + 1)
            v11 = vertex(i + 1, j + 1)
            st.insert([v00])
            st.insert([v00, v10, v11])
            st.insert([v00, v11, v01])


def add_cycle_graph(st: gudhi.SimplexTree, samples: int) -> None:
    for idx in range(samples):
        st.insert([idx])
        st.insert([idx, (idx + 1) % samples])


def add_collapsed_point(st: gudhi.SimplexTree) -> None:
    st.insert([0])


def betti_numbers(kind: str, size: int) -> list[int]:
    st = gudhi.SimplexTree()
    if kind == "torus":
        add_periodic_grid_torus(st, size)
    elif kind in {"fiber_loop", "base_loop"}:
        add_cycle_graph(st, size)
    elif kind == "collapsed_point":
        add_collapsed_point(st)
    else:
        raise ValueError(kind)
    st.compute_persistence(persistence_dim_max=True)
    values = st.betti_numbers()
    return [int(value) for value in values]


def embedding_metrics(points: np.ndarray) -> dict[str, float]:
    norms = np.linalg.norm(points, axis=1)
    centered = points - points.mean(axis=0, keepdims=True)
    singular_values = np.linalg.svd(centered, compute_uv=False)
    return {
        "count": int(points.shape[0]),
        "max_s3_norm_error": float(np.max(np.abs(norms - 1.0))),
        "rank_proxy_singular_value_count": int(np.sum(singular_values > 1e-8)),
        "largest_singular_value": float(singular_values[0]),
        "smallest_retained_singular_value": float(singular_values[np.sum(singular_values > 1e-8) - 1]),
    }


def readout(theta: float, size: int) -> dict[str, object]:
    torus_points = sample_hopf_torus(theta, size=size)
    fiber_points = sample_loop(theta, vary="fiber", samples=size)
    base_points = sample_loop(theta, vary="base", samples=size)
    return {
        "theta": theta,
        "grid_size": size,
        "torus": {
            "betti": betti_numbers("torus", size),
            "embedding": embedding_metrics(torus_points),
        },
        "fiber_loop": {
            "betti": betti_numbers("fiber_loop", size),
            "embedding": embedding_metrics(fiber_points),
        },
        "base_loop": {
            "betti": betti_numbers("base_loop", size),
            "embedding": embedding_metrics(base_points),
        },
    }


def candidate_survives(payload: dict[str, object]) -> bool:
    torus = payload["torus"]
    fiber = payload["fiber_loop"]
    base = payload["base_loop"]
    return bool(
        torus["betti"][:3] == [1, 2, 1]
        and fiber["betti"][:2] == [1, 1]
        and base["betti"][:2] == [1, 1]
        and torus["embedding"]["rank_proxy_singular_value_count"] >= 3
        and fiber["embedding"]["rank_proxy_singular_value_count"] == 2
        and base["embedding"]["rank_proxy_singular_value_count"] == 2
        and torus["embedding"]["max_s3_norm_error"] < 1e-12
        and fiber["embedding"]["max_s3_norm_error"] < 1e-12
        and base["embedding"]["max_s3_norm_error"] < 1e-12
    )


def run_graveyards(size: int) -> dict[str, object]:
    collapsed = betti_numbers("collapsed_point", size)
    fiber = betti_numbers("fiber_loop", size)
    base = betti_numbers("base_loop", size)
    torus = betti_numbers("torus", size)
    pole_torus = sample_hopf_torus(theta=0.0, size=size)
    pole_metrics = embedding_metrics(pole_torus)
    return {
        "collapsed_point_not_torus": {
            "betti": collapsed,
            "expected_not_torus": True,
            "passed": collapsed[:1] == [1] and len(collapsed) == 1,
        },
        "fiber_loop_alone_not_torus": {
            "betti": fiber,
            "expected_not_torus": True,
            "passed": fiber[:2] == [1, 1] and fiber[:3] != [1, 2, 1],
        },
        "base_loop_alone_not_torus": {
            "betti": base,
            "expected_not_torus": True,
            "passed": base[:2] == [1, 1] and base[:3] != [1, 2, 1],
        },
        "torus_has_two_loop_generators": {
            "betti": torus,
            "expected": [1, 2, 1],
            "passed": torus[:3] == [1, 2, 1],
        },
        "pole_embedding_loses_two_coordinate_span": {
            "rank_proxy_singular_value_count": pole_metrics["rank_proxy_singular_value_count"],
            "expected_degeneracy": True,
            "passed": pole_metrics["rank_proxy_singular_value_count"] < 3,
        },
    }


def main() -> int:
    size = 12
    positive = readout(theta=math.pi / 3.0, size=size)
    graveyards = run_graveyards(size=size)
    all_pass = bool(candidate_survives(positive) and all(row["passed"] for row in graveyards.values()))
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "GUDHI simplicial homology and sampled S3 embedding diagnostics for Hopf torus fiber/base loops only; "
            "no QIT, GStack, axis, bridge, nonclassical, flux, or target-system admission"
        ),
        "next_lego_target": "inner_outer_hopf_weyl_loop_geometry_fit",
        "promotion_condition": (
            "May only support later carrier-geometry planning after independent full-bundle, connection, and "
            "operator-evolution receipts reproduce compatible fiber/base loop distinctions with physical graveyards."
        ),
        "demotion_condition": (
            "Demote if torus Betti numbers are not [1,2,1], if either single loop is misread as a torus, if S3 "
            "embedding norms fail, or if collapsed/pole graveyards do not collapse."
        ),
        "blocked_until": "blocked from target-system claims until fuller Hopf/Weyl carrier topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No full geometric-constraint-manifold implementation.",
            "No flux representation.",
            "No Lindblad evolution, Hamiltonian dynamics, or target-system admission.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This baseline separates a two-loop Hopf torus topology from either single loop and from collapsed/pole "
            "controls. It does not simulate a full nested Hopf-torus manifold or flux."
        ),
        "operation_sequence": [
            "sample Hopf-coordinate S3 points over a fixed-theta two-parameter torus",
            "sample the fiber loop by varying xi with phi fixed",
            "sample the base loop by varying phi with xi fixed",
            "build explicit periodic-grid and cycle simplicial complexes in GUDHI",
            "compute Betti readouts for torus, fiber loop, base loop, collapsed point, and pole controls",
            "compare sampled S3 embedding rank diagnostics for torus and single-loop paths",
        ],
        "carrier_topology": "fixed-theta Hopf torus in S3 with two circle coordinates, plus one-coordinate fiber and base loop subspaces",
        "observable": "GUDHI Betti numbers and sampled S3 embedding rank/norm diagnostics",
        "pass_fail_predicate": (
            "torus has Betti [1,2,1], each one-coordinate loop has Betti [1,1], S3 norms hold, torus embedding "
            "has higher coordinate span than either loop, and collapsed/pole graveyards collapse"
        ),
        "graveyards": [
            "collapsed point is not torus",
            "fiber loop alone is not torus",
            "base loop alone is not torus",
            "pole embedding loses coordinate span",
        ],
        "baselines": [
            "sampled NumPy Hopf path metric fixture",
            "Geomstats projected S2 distance fixture",
            "Clifford projected outer-loop rotor fixture",
        ],
        "alternative_formulations": [
            "alpha-complex persistence on embedded S3 torus point cloud",
            "cubical complex on periodic parameter grid",
            "full connection/curvature fixture over the Hopf bundle",
            "nested Hopf-torus carrier fixture",
        ],
        "exact_tool_function_needs": {
            "gudhi": ["SimplexTree.insert", "SimplexTree.compute_persistence", "SimplexTree.betti_numbers"],
            "numpy": ["linspace", "exp", "asarray", "linalg.norm", "linalg.svd"],
        },
        "lego_or_coupling_target": "inner_outer_hopf_weyl_loop_geometry_fit",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
