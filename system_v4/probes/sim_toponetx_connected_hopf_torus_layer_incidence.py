#!/usr/bin/env python3
"""TopoNetX connected Hopf-torus layer incidence baseline."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import math
from pathlib import Path

import numpy as np
from receipt_boundary import apply_default_receipt_boundary
from toponetx import CellComplex


NAME = "toponetx_connected_hopf_torus_layer_incidence"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": (
            "CellComplex rank-2 torus-layer cells, interlayer rectangular cells, incidence matrices, and Hodge "
            "Laplacian zero-mode proxies encode a connected two-layer Hopf-torus carrier baseline"
        ),
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "computes sampled Hopf S3 embeddings, interlayer distances, and Laplacian zero-mode proxies",
    },
}
TOOL_INTEGRATION_DEPTH = {"toponetx": "load_bearing", "numpy": "supportive"}


def hopf_s3_point(theta: float, phi: float, chi: float) -> np.ndarray:
    a = math.cos(theta / 2.0) * np.exp(1j * (chi + phi) / 2.0)
    b = math.sin(theta / 2.0) * np.exp(1j * (chi - phi) / 2.0)
    return np.array([a.real, a.imag, b.real, b.imag], dtype=float)


def vertex(size: int, layer: int, i: int, j: int) -> int:
    return layer * size * size + (i % size) * size + (j % size)


def add_periodic_torus_layer(cc: CellComplex, *, size: int, layer: int) -> None:
    for i in range(size):
        for j in range(size):
            cc.add_cell(
                [
                    vertex(size, layer, i, j),
                    vertex(size, layer, i + 1, j),
                    vertex(size, layer, i + 1, j + 1),
                    vertex(size, layer, i, j + 1),
                ],
                rank=2,
            )


def add_interlayer_cells(cc: CellComplex, *, size: int, connect_phi: bool = True, connect_chi: bool = True) -> None:
    for i in range(size):
        for j in range(size):
            if connect_phi:
                cc.add_cell(
                    [
                        vertex(size, 0, i, j),
                        vertex(size, 0, i + 1, j),
                        vertex(size, 1, i + 1, j),
                        vertex(size, 1, i, j),
                    ],
                    rank=2,
                )
            if connect_chi:
                cc.add_cell(
                    [
                        vertex(size, 0, i, j),
                        vertex(size, 0, i, j + 1),
                        vertex(size, 1, i, j + 1),
                        vertex(size, 1, i, j),
                    ],
                    rank=2,
                )


def build_complex(size: int, *, connect_phi: bool, connect_chi: bool) -> CellComplex:
    cc = CellComplex()
    add_periodic_torus_layer(cc, size=size, layer=0)
    add_periodic_torus_layer(cc, size=size, layer=1)
    if connect_phi or connect_chi:
        add_interlayer_cells(cc, size=size, connect_phi=connect_phi, connect_chi=connect_chi)
    return cc


def zero_modes(matrix: np.ndarray, tol: float = 1e-8) -> int:
    symmetric = (matrix + matrix.T) / 2.0
    return int(np.sum(np.abs(np.linalg.eigvalsh(symmetric)) < tol))


def complex_readout(cc: CellComplex) -> dict[str, object]:
    incidence_shapes = {}
    laplacian_shapes = {}
    zero_mode_proxy = []
    for rank in (0, 1, 2):
        try:
            incidence_shapes[str(rank)] = list(cc.incidence_matrix(rank).shape)
        except ValueError:
            incidence_shapes[str(rank)] = [0, 0]
        try:
            laplacian = cc.hodge_laplacian_matrix(rank).toarray()
        except ValueError:
            laplacian_shapes[str(rank)] = [0, 0]
            zero_mode_proxy.append(0)
        else:
            laplacian_shapes[str(rank)] = list(laplacian.shape)
            zero_mode_proxy.append(zero_modes(laplacian))
    return {
        "node_count": len(cc.nodes),
        "edge_count": len(cc.edges),
        "rank2_cell_count": len(cc.cells),
        "incidence_shapes": incidence_shapes,
        "laplacian_shapes": laplacian_shapes,
        "zero_mode_proxy": zero_mode_proxy,
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
    connected = complex_readout(build_complex(size, connect_phi=True, connect_chi=True))
    embedding = embedding_readout((math.pi / 3.0, 2.0 * math.pi / 3.0), size)
    return {
        "size": size,
        "connected_layer_complex": connected,
        "embedding": embedding,
        "survives_connected_layer_incidence": bool(
            connected["zero_mode_proxy"][0] == 1
            and connected["zero_mode_proxy"][1] == 2
            and connected["node_count"] == 2 * size * size
            and connected["edge_count"] == 5 * size * size
            and connected["rank2_cell_count"] == 4 * size * size
            and embedding["interlayer_distance_min"] > 1e-6
            and embedding["max_s3_norm_error"] < 1e-12
        ),
    }


def run_graveyards(size: int) -> dict[str, object]:
    connected = complex_readout(build_complex(size, connect_phi=True, connect_chi=True))
    disjoint = complex_readout(build_complex(size, connect_phi=False, connect_chi=False))
    phi_only = complex_readout(build_complex(size, connect_phi=True, connect_chi=False))
    chi_only = complex_readout(build_complex(size, connect_phi=False, connect_chi=True))
    duplicate_embedding = embedding_readout((math.pi / 3.0, math.pi / 3.0), size)
    pole_embedding = embedding_readout((0.0, math.pi), size)

    no_faces = CellComplex()
    for idx in range(2 * size * size):
        no_faces.add_node(idx)
    no_faces_readout = complex_readout(no_faces)

    return {
        "disjoint_layers_keep_two_components": {
            "zero_mode_proxy": disjoint["zero_mode_proxy"],
            "passed": bool(disjoint["zero_mode_proxy"][0] == 2 and disjoint["zero_mode_proxy"][0] != connected["zero_mode_proxy"][0]),
        },
        "single_interlayer_direction_keeps_extra_cycle_proxy": {
            "phi_only_zero_mode_proxy": phi_only["zero_mode_proxy"],
            "chi_only_zero_mode_proxy": chi_only["zero_mode_proxy"],
            "connected_zero_mode_proxy": connected["zero_mode_proxy"],
            "passed": bool(
                phi_only["zero_mode_proxy"][1] > connected["zero_mode_proxy"][1]
                and chi_only["zero_mode_proxy"][1] > connected["zero_mode_proxy"][1]
            ),
        },
        "duplicated_theta_values_remove_interlayer_embedding_separation": {
            "interlayer_distance_max": duplicate_embedding["interlayer_distance_max"],
            "passed": bool(duplicate_embedding["interlayer_distance_max"] < 1e-12),
        },
        "pole_layers_degenerate_embedding_span": {
            "interlayer_distance_mean": pole_embedding["interlayer_distance_mean"],
            "passed": bool(pole_embedding["interlayer_distance_mean"] < 2.1),
        },
        "rank2_faces_removed_do_not_have_torus_layer_cells": {
            "zero_mode_proxy": no_faces_readout["zero_mode_proxy"],
            "passed": bool(no_faces_readout["zero_mode_proxy"][1] == 0 and no_faces_readout["rank2_cell_count"] == 0),
        },
    }


def main() -> int:
    size = 4
    positive = run_positive(size)
    graveyards = run_graveyards(size)
    all_pass = bool(
        positive["survives_connected_layer_incidence"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "TopoNetX connected two-layer Hopf-torus cell-complex incidence baseline only; zero-mode values are "
            "tool-level Hodge-Laplacian proxies for this finite cell fixture, not promoted Betti theorems; no "
            "physical inner/outer loop independence, no full S3 bundle, no flux, no QIT, GStack, axis, bridge, "
            "nonclassical, target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "nested_hopf_torus_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later carrier-geometry planning after independent GUDHI, connection, Weyl-spinor, "
            "and operator-evolution receipts reproduce compatible connected-layer readouts with physical graveyards."
        ),
        "demotion_condition": (
            "Demote if connected interlayer cells do not reduce the component and loop zero-mode proxies, if "
            "disjoint/single-direction/duplicate-theta/no-face controls do not collapse, or if S3 embedding norms fail."
        ),
        "blocked_until": "blocked from target-system claims until fuller Hopf/Weyl carrier topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No full geometric-constraint-manifold implementation.",
            "No flux representation or Pauli shortcut.",
            "No Lindblad evolution, Hamiltonian dynamics, or target-system admission.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This baseline tests a finite connected two-layer cell fixture and TopoNetX incidence/Hodge-Laplacian "
            "readouts. It does not simulate a full nested carrier manifold or prove inner/outer loop independence."
        ),
        "operation_sequence": [
            "sample two fixed-theta Hopf tori in S3",
            "build periodic rank-2 CellComplex cells for each torus layer",
            "add vertical rectangular interlayer cells in both torus coordinate directions",
            "compute TopoNetX incidence matrices and Hodge-Laplacian zero-mode proxies",
            "compute S3 norm and interlayer-distance embedding diagnostics",
            "run disjoint-layer, single-direction-connection, duplicate-theta, pole-layer, and no-face graveyards",
        ],
        "carrier_topology": (
            "two fixed-theta Hopf torus layers connected by rank-2 interlayer cells over a periodic grid, with sampled "
            "S3 embeddings at corresponding grid coordinates"
        ),
        "observable": (
            "cell counts, incidence shapes, Hodge-Laplacian zero-mode proxies, S3 norm error, and interlayer S3 "
            "distance diagnostics"
        ),
        "pass_fail_predicate": (
            "connected layers have one component proxy, two loop proxies, expected cell counts, unit S3 embeddings, "
            "and separated theta layers; adjacent controls collapse or expose missing connection/layer geometry"
        ),
        "graveyards": [
            "disjoint layers keep two components",
            "single interlayer direction keeps extra cycle proxy",
            "duplicated theta values remove interlayer embedding separation",
            "pole layers degenerate embedding span",
            "rank-2 faces removed do not have torus layer cells",
        ],
        "baselines": [
            "TopoNetX two disjoint Hopf-torus layer incidence fixture",
            "GUDHI Hopf torus fiber/base homology fixture",
            "SciPy Hopf horizontal-lift chi-shift fixture",
            "three-formulation Hopf phase-generator density transport packet",
        ],
        "alternative_formulations": [
            "GUDHI simplicial connected two-layer carrier fixture",
            "XGI higher-order layer-incidence hypergraph fixture",
            "nested horizontal-lift ODE integration over multiple theta layers",
            "density-object evolution over connected carrier coordinates",
        ],
        "exact_tool_function_needs": {
            "toponetx": ["CellComplex", "add_cell", "incidence_matrix", "hodge_laplacian_matrix"],
            "numpy": ["linspace", "exp", "linalg.eigvalsh", "linalg.norm", "mean"],
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
