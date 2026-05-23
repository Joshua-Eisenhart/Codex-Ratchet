#!/usr/bin/env python3
"""TopoNetX two Hopf-torus layer incidence baseline."""

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


NAME = "toponetx_two_hopf_torus_layer_incidence"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "CellComplex rank-2 cells, incidence matrices, and Hodge Laplacians encode two periodic Hopf-torus layer complexes",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "computes Hopf S3 embeddings, singular-value span diagnostics, and Laplacian zero modes",
    },
}
TOOL_INTEGRATION_DEPTH = {"toponetx": "load_bearing", "numpy": "supportive"}


def hopf_s3_point(theta: float, phi: float, chi: float) -> np.ndarray:
    a = math.cos(theta / 2.0) * np.exp(1j * (chi + phi) / 2.0)
    b = math.sin(theta / 2.0) * np.exp(1j * (chi - phi) / 2.0)
    return np.array([a.real, a.imag, b.real, b.imag], dtype=float)


def sample_layer(theta: float, size: int) -> np.ndarray:
    points = []
    for phi in np.linspace(0.0, 2.0 * math.pi, size, endpoint=False):
        for chi in np.linspace(0.0, 2.0 * math.pi, size, endpoint=False):
            points.append(hopf_s3_point(theta, float(phi), float(chi)))
    return np.asarray(points, dtype=float)


def add_periodic_torus_layer(cc: CellComplex, *, size: int, offset: int) -> None:
    def vertex(i: int, j: int) -> int:
        return offset + (i % size) * size + (j % size)

    for i in range(size):
        for j in range(size):
            cc.add_cell(
                [vertex(i, j), vertex(i + 1, j), vertex(i + 1, j + 1), vertex(i, j + 1)],
                rank=2,
            )


def build_layers(size: int, layer_count: int) -> CellComplex:
    cc = CellComplex()
    for layer in range(layer_count):
        add_periodic_torus_layer(cc, size=size, offset=layer * size * size)
    return cc


def zero_modes(matrix: np.ndarray, tol: float = 1e-8) -> int:
    symmetric = (matrix + matrix.T) / 2.0
    return int(np.sum(np.abs(np.linalg.eigvalsh(symmetric)) < tol))


def complex_readout(cc: CellComplex) -> dict[str, object]:
    incidence_shapes = {}
    laplacian_shapes = {}
    betti_proxy = []
    for rank in (0, 1, 2):
        try:
            incidence_shapes[str(rank)] = list(cc.incidence_matrix(rank).shape)
        except ValueError:
            incidence_shapes[str(rank)] = [0, 0]
        try:
            laplacian = cc.hodge_laplacian_matrix(rank).toarray()
        except ValueError:
            laplacian_shapes[str(rank)] = [0, 0]
            betti_proxy.append(0)
        else:
            laplacian_shapes[str(rank)] = list(laplacian.shape)
            betti_proxy.append(zero_modes(laplacian))
    return {
        "node_count": len(cc.nodes),
        "edge_count": len(cc.edges),
        "rank2_cell_count": len(cc.cells),
        "incidence_shapes": incidence_shapes,
        "laplacian_shapes": laplacian_shapes,
        "betti_proxy": betti_proxy,
    }


def embedding_readout(theta_values: list[float], size: int) -> dict[str, object]:
    layers = [sample_layer(theta, size=size) for theta in theta_values]
    spans = []
    norm_errors = []
    centroids = []
    for points in layers:
        centered = points - points.mean(axis=0, keepdims=True)
        singular_values = np.linalg.svd(centered, compute_uv=False)
        spans.append(int(np.sum(singular_values > 1e-8)))
        norm_errors.append(float(np.max(np.abs(np.linalg.norm(points, axis=1) - 1.0))))
        centroids.append(points.mean(axis=0))
    centroid_distances = []
    for idx in range(len(centroids) - 1):
        centroid_distances.append(float(np.linalg.norm(centroids[idx + 1] - centroids[idx])))
    return {
        "theta_values": theta_values,
        "layer_span_counts": spans,
        "max_s3_norm_error": max(norm_errors),
        "adjacent_centroid_distances": centroid_distances,
    }


def run_positive(size: int) -> dict[str, object]:
    cc = build_layers(size=size, layer_count=2)
    topology = complex_readout(cc)
    embedding = embedding_readout([math.pi / 3.0, 2.0 * math.pi / 3.0], size=size)
    return {
        "size": size,
        "topology": topology,
        "embedding": embedding,
        "survives_two_layer_torus_readout": bool(
            topology["betti_proxy"] == [2, 4, 2]
            and topology["node_count"] == 2 * size * size
            and topology["edge_count"] == 4 * size * size
            and topology["rank2_cell_count"] == 2 * size * size
            and embedding["layer_span_counts"] == [4, 4]
            and embedding["max_s3_norm_error"] < 1e-12
            and min(embedding["adjacent_centroid_distances"]) > 1e-6
        ),
    }


def run_graveyards(size: int) -> dict[str, object]:
    one_layer = complex_readout(build_layers(size=size, layer_count=1))
    two_layers = complex_readout(build_layers(size=size, layer_count=2))
    no_faces = CellComplex()
    for idx in range(2 * size * size):
        no_faces.add_node(idx)
    collapsed = CellComplex()
    collapsed.add_node(0)
    pole_embedding = embedding_readout([0.0, math.pi], size=size)
    return {
        "single_torus_layer_is_not_two_layers": {
            "betti_proxy": one_layer["betti_proxy"],
            "passed": bool(one_layer["betti_proxy"] == [1, 2, 1] and one_layer["betti_proxy"] != two_layers["betti_proxy"]),
        },
        "rank2_faces_removed_do_not_have_torus_loops": {
            "betti_proxy": complex_readout(no_faces)["betti_proxy"],
            "passed": bool(complex_readout(no_faces)["betti_proxy"][1] == 0),
        },
        "collapsed_point_is_not_layered_torus": {
            "betti_proxy": complex_readout(collapsed)["betti_proxy"],
            "passed": bool(complex_readout(collapsed)["betti_proxy"] == [1, 0, 0]),
        },
        "pole_layers_lose_torus_embedding_span": {
            "layer_span_counts": pole_embedding["layer_span_counts"],
            "passed": bool(max(pole_embedding["layer_span_counts"]) < 4),
        },
        "duplicated_theta_values_remove_layer_separation": {
            "adjacent_centroid_distances": embedding_readout([math.pi / 3.0, math.pi / 3.0], size=size)[
                "adjacent_centroid_distances"
            ],
            "passed": bool(
                max(
                    embedding_readout([math.pi / 3.0, math.pi / 3.0], size=size)[
                        "adjacent_centroid_distances"
                    ]
                )
                < 1e-12
            ),
        },
    }


def main() -> int:
    size = 4
    positive = run_positive(size)
    graveyards = run_graveyards(size)
    all_pass = bool(
        positive["survives_two_layer_torus_readout"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "TopoNetX cell-complex incidence and Hodge-Laplacian baseline for two sampled Hopf-torus layers only; "
            "no QIT, GStack, axis, bridge, nonclassical, flux, Pauli shortcut, target-system, or full "
            "geometric-constraint-manifold admission"
        ),
        "next_lego_target": "nested_hopf_torus_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later carrier-geometry planning after independent connection, Weyl-spinor, "
            "operator-evolution, and physical graveyard receipts reproduce compatible nested loop readouts."
        ),
        "demotion_condition": (
            "Demote if two torus layers do not read as doubled torus homology, if layer embeddings leave S3, "
            "if layer centroids are not separated, or if single-layer/no-face/collapsed/pole/duplicate-theta "
            "controls fail."
        ),
        "blocked_until": "blocked from target-system claims until fuller Hopf/Weyl carrier topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No full geometric-constraint-manifold implementation.",
            "No flux representation or Pauli shortcut.",
            "No Lindblad evolution, Hamiltonian dynamics, or target-system admission.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This baseline tests a two-layer Hopf-torus cell complex and sampled S3 embeddings. It does not "
            "simulate a full nested geometric-constraint manifold or prove inner/outer loop independence."
        ),
        "operation_sequence": [
            "sample two fixed-theta Hopf tori in S3",
            "build a periodic rank-2 CellComplex for each torus layer",
            "compute TopoNetX incidence matrices and Hodge Laplacian zero-mode counts",
            "verify doubled torus readout [2,4,2] for two layers",
            "compute S3 norm and centroid separation diagnostics for the sampled layers",
            "run single-layer, no-face, collapsed-point, pole-layer, and duplicate-theta graveyards",
        ],
        "carrier_topology": "two disjoint fixed-theta Hopf torus layers represented as periodic rank-2 cell complexes with sampled S3 embeddings",
        "observable": "cell counts, incidence shapes, Hodge-Laplacian zero-mode counts, S3 norm error, and layer centroid separation",
        "pass_fail_predicate": (
            "two layers have doubled torus zero-mode readout [2,4,2], expected cell counts, unit S3 embeddings, "
            "and separated theta-layer centroids, while adjacent controls collapse or lose the layer/torus readout"
        ),
        "graveyards": [
            "single torus layer is not two layers",
            "rank-2 faces removed do not have torus loops",
            "collapsed point is not a layered torus",
            "pole layers lose torus embedding span",
            "duplicated theta values remove layer separation",
        ],
        "baselines": [
            "GUDHI Hopf torus fiber/base homology fixture",
            "SciPy Hopf horizontal-lift chi-shift fixture",
            "SymPy Hopf loop holonomy area-dependence fixture",
            "sampled Hopf/Weyl inner-outer loop readout fixture",
        ],
        "alternative_formulations": [
            "GUDHI simplicial homology over two torus layers",
            "nested horizontal-lift ODE integration over multiple theta layers",
            "Weyl spinor density-object evolution over inner and outer loops",
            "TopoNetX connected layer complex with explicit interlayer cells",
        ],
        "exact_tool_function_needs": {
            "toponetx": ["CellComplex", "add_cell", "incidence_matrix", "hodge_laplacian_matrix"],
            "numpy": ["linspace", "linalg.eigvalsh", "linalg.norm", "linalg.svd"],
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
