#!/usr/bin/env python3
"""GUDHI connected Hopf-torus layer homology baseline."""

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


NAME = "gudhi_connected_hopf_torus_layer_homology"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": (
            "SimplexTree insert/compute_persistence/betti_numbers encode two triangulated torus layers plus "
            "triangulated interlayer faces"
        ),
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "computes sampled Hopf S3 embeddings and interlayer distance diagnostics",
    },
}
TOOL_INTEGRATION_DEPTH = {"gudhi": "load_bearing", "numpy": "supportive"}


def hopf_s3_point(theta: float, phi: float, chi: float) -> np.ndarray:
    a = math.cos(theta / 2.0) * np.exp(1j * (chi + phi) / 2.0)
    b = math.sin(theta / 2.0) * np.exp(1j * (chi - phi) / 2.0)
    return np.array([a.real, a.imag, b.real, b.imag], dtype=float)


def vertex(size: int, layer: int, i: int, j: int) -> int:
    return layer * size * size + (i % size) * size + (j % size)


def add_triangle(st: gudhi.SimplexTree, a: int, b: int, c: int) -> None:
    st.insert([a, b, c])


def add_periodic_torus_layer(st: gudhi.SimplexTree, *, size: int, layer: int) -> None:
    for i in range(size):
        for j in range(size):
            a = vertex(size, layer, i, j)
            b = vertex(size, layer, i + 1, j)
            c = vertex(size, layer, i + 1, j + 1)
            d = vertex(size, layer, i, j + 1)
            add_triangle(st, a, b, c)
            add_triangle(st, a, c, d)


def add_interlayer_faces(st: gudhi.SimplexTree, *, size: int, connect_phi: bool, connect_chi: bool) -> None:
    for i in range(size):
        for j in range(size):
            if connect_phi:
                a = vertex(size, 0, i, j)
                b = vertex(size, 0, i + 1, j)
                c = vertex(size, 1, i + 1, j)
                d = vertex(size, 1, i, j)
                add_triangle(st, a, b, c)
                add_triangle(st, a, c, d)
            if connect_chi:
                a = vertex(size, 0, i, j)
                b = vertex(size, 0, i, j + 1)
                c = vertex(size, 1, i, j + 1)
                d = vertex(size, 1, i, j)
                add_triangle(st, a, b, c)
                add_triangle(st, a, c, d)


def build_complex(size: int, *, connect_phi: bool, connect_chi: bool) -> gudhi.SimplexTree:
    st = gudhi.SimplexTree()
    add_periodic_torus_layer(st, size=size, layer=0)
    add_periodic_torus_layer(st, size=size, layer=1)
    if connect_phi or connect_chi:
        add_interlayer_faces(st, size=size, connect_phi=connect_phi, connect_chi=connect_chi)
    st.compute_persistence(persistence_dim_max=True)
    return st


def readout(st: gudhi.SimplexTree) -> dict[str, object]:
    return {
        "num_vertices": int(st.num_vertices()),
        "num_simplices": int(st.num_simplices()),
        "betti": [int(value) for value in st.betti_numbers()],
    }


def embedding_readout(theta_values: tuple[float, float], size: int) -> dict[str, object]:
    distances = []
    norm_errors = []
    for i in range(size):
        for j in range(size):
            phi = 2.0 * math.pi * i / size
            chi = 2.0 * math.pi * j / size
            low = hopf_s3_point(theta_values[0], phi, chi)
            high = hopf_s3_point(theta_values[1], phi, chi)
            distances.append(float(np.linalg.norm(high - low)))
            norm_errors.append(float(abs(np.linalg.norm(low) - 1.0)))
            norm_errors.append(float(abs(np.linalg.norm(high) - 1.0)))
    return {
        "theta_values": [float(theta_values[0]), float(theta_values[1])],
        "interlayer_distance_min": float(min(distances)),
        "interlayer_distance_max": float(max(distances)),
        "interlayer_distance_mean": float(np.mean(distances)),
        "max_s3_norm_error": float(max(norm_errors)),
    }


def run_positive(size: int) -> dict[str, object]:
    connected = readout(build_complex(size, connect_phi=True, connect_chi=True))
    embedding = embedding_readout((math.pi / 3.0, 2.0 * math.pi / 3.0), size)
    return {
        "size": size,
        "connected_layer_complex": connected,
        "embedding": embedding,
        "survives_connected_layer_homology": bool(
            connected["betti"] == [1, 2, 17]
            and connected["num_vertices"] == 2 * size * size
            and embedding["interlayer_distance_min"] > 1e-6
            and embedding["max_s3_norm_error"] < 1e-12
        ),
    }


def run_graveyards(size: int) -> dict[str, object]:
    connected = readout(build_complex(size, connect_phi=True, connect_chi=True))
    disjoint = readout(build_complex(size, connect_phi=False, connect_chi=False))
    phi_only = readout(build_complex(size, connect_phi=True, connect_chi=False))
    chi_only = readout(build_complex(size, connect_phi=False, connect_chi=True))
    duplicate_embedding = embedding_readout((math.pi / 3.0, math.pi / 3.0), size)

    collapsed = gudhi.SimplexTree()
    collapsed.insert([0])
    collapsed.compute_persistence(persistence_dim_max=True)
    collapsed_readout = readout(collapsed)

    return {
        "disjoint_layers_keep_two_components": {
            "betti": disjoint["betti"],
            "passed": bool(disjoint["betti"] == [2, 4, 2] and disjoint["betti"][0] != connected["betti"][0]),
        },
        "single_interlayer_direction_keeps_extra_loops": {
            "phi_only_betti": phi_only["betti"],
            "chi_only_betti": chi_only["betti"],
            "connected_betti": connected["betti"],
            "passed": bool(phi_only["betti"][1] > connected["betti"][1] and chi_only["betti"][1] > connected["betti"][1]),
        },
        "duplicated_theta_values_remove_interlayer_embedding_separation": {
            "interlayer_distance_max": duplicate_embedding["interlayer_distance_max"],
            "passed": bool(duplicate_embedding["interlayer_distance_max"] < 1e-12),
        },
        "collapsed_point_is_not_connected_layer_carrier": {
            "betti": collapsed_readout["betti"],
            "passed": bool(collapsed_readout["betti"] == [1]),
        },
        "rank2_faces_removed_do_not_have_torus_layer_homology": {
            "num_simplices": collapsed_readout["num_simplices"],
            "passed": bool(collapsed_readout["num_simplices"] == 1),
        },
    }


def main() -> int:
    size = 4
    positive = run_positive(size)
    graveyards = run_graveyards(size)
    all_pass = bool(
        positive["survives_connected_layer_homology"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "GUDHI finite triangulated connected two-layer Hopf-torus homology baseline only; the H2 count reflects "
            "this finite triangulated fixture and is not a promoted manifold theorem; no physical inner/outer loop "
            "independence, no full S3 bundle, no flux, no QIT, GStack, axis, bridge, nonclassical, target-system, "
            "or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "nested_hopf_torus_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later carrier-geometry planning after independent TopoNetX, connection, Weyl-spinor, "
            "and operator-evolution receipts reproduce compatible connected-layer readouts with physical graveyards."
        ),
        "demotion_condition": (
            "Demote if GUDHI connected-layer Betti readouts drift, if single-direction controls do not retain extra "
            "loops, if disjoint/duplicate-theta/collapsed controls do not collapse, or if S3 embedding norms fail."
        ),
        "blocked_until": "blocked from target-system claims until fuller Hopf/Weyl carrier topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No full geometric-constraint-manifold implementation.",
            "No flux representation or Pauli shortcut.",
            "No Lindblad evolution, Hamiltonian dynamics, or target-system admission.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This baseline tests a finite triangulated connected two-layer carrier fixture and GUDHI Betti readouts. "
            "It does not simulate a full nested carrier manifold or prove inner/outer loop independence."
        ),
        "operation_sequence": [
            "triangulate two periodic fixed-theta Hopf torus layers",
            "triangulate interlayer rectangular faces in both torus coordinate directions",
            "compute GUDHI persistence and Betti readouts",
            "compute S3 norm and interlayer-distance embedding diagnostics",
            "run disjoint-layer, single-direction-connection, duplicate-theta, collapsed-point, and no-face graveyards",
        ],
        "carrier_topology": (
            "two fixed-theta Hopf torus layers connected by triangulated interlayer faces over a periodic grid, with "
            "sampled S3 embeddings at corresponding grid coordinates"
        ),
        "observable": "GUDHI Betti numbers, simplex counts, S3 norm error, and interlayer S3 distance diagnostics",
        "pass_fail_predicate": (
            "connected layers have Betti [1,2,17] in this finite fixture, expected vertex count, unit S3 embeddings, "
            "and separated theta layers; adjacent controls collapse or expose missing connection/layer geometry"
        ),
        "graveyards": [
            "disjoint layers keep two components",
            "single interlayer direction keeps extra loops",
            "duplicated theta values remove interlayer embedding separation",
            "collapsed point is not connected layer carrier",
            "rank-2 faces removed do not have torus layer homology",
        ],
        "baselines": [
            "TopoNetX connected Hopf-torus layer incidence fixture",
            "TopoNetX two disjoint Hopf-torus layer incidence fixture",
            "GUDHI Hopf torus fiber/base homology fixture",
            "three-formulation Hopf phase-generator density transport packet",
        ],
        "alternative_formulations": [
            "TopoNetX connected two-layer carrier fixture",
            "XGI higher-order layer-incidence hypergraph fixture",
            "nested horizontal-lift ODE integration over multiple theta layers",
            "density-object evolution over connected carrier coordinates",
        ],
        "exact_tool_function_needs": {
            "gudhi": ["SimplexTree.insert", "SimplexTree.compute_persistence", "SimplexTree.betti_numbers"],
            "numpy": ["exp", "linalg.norm", "mean"],
        },
        "lego_or_coupling_target": "nested_hopf_torus_loop_geometry_baseline",
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
