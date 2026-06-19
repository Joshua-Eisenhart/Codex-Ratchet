#!/usr/bin/env python3
"""region_discovery_from_observables_v0 -- exact numpy/stdlib leg.

Finite Manifold-tower L12 diagnostic: discover regions from observable readouts
only. There are no terrain labels or hidden classes. The named relation is:

    observable_threshold_component_equivalence_v0

For probes p,q in a finite grid P with 4-neighbor adjacency A4:

    p equiv_{O,tau,A4} q
        iff sigma_tau(O(p)) == sigma_tau(O(q))
        and p,q are connected by an A4 path whose every cell has that same
        threshold signature.

The threshold signature is explicit, not universal:

    sigma_tau(O(p)) = (o0(p) <= 0, o1(p) >= 0, o2(p) >= 0).

The discriminator is value-forced: shuffling display labels leaves the
structural quotient unchanged, but a real perturbation to observable o0 moves
threshold memberships, boundary edges, and quotient components.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, deque
from pathlib import Path

import numpy as np

SIM_ID = "region_discovery_from_observables_v0"
ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results" / f"{SIM_ID}_exact_results.json"

HEIGHT = 10
WIDTH = 12
N_CELLS = HEIGHT * WIDTH
EQUIVALENCE_RELATION_NAME = "observable_threshold_component_equivalence_v0"
THRESHOLD_SIGNATURE_NAME = "sigma_tau_o0_le_0_o1_ge_0_o2_ge_0"
THRESHOLDS = {
    "o0_basin_leq": 0,
    "o1_shear_geq": 0,
    "o2_north_geq": 0,
}

DEFAULT_LABELS = {
    "000": "display_A",
    "001": "display_B",
    "010": "display_C",
    "011": "display_D",
    "100": "display_E",
    "101": "display_F",
    "110": "display_G",
    "111": "display_H",
}

SHUFFLED_LABELS = {
    "000": "display_H",
    "001": "display_E",
    "010": "display_A",
    "011": "display_G",
    "100": "display_C",
    "101": "display_B",
    "110": "display_F",
    "111": "display_D",
}


def cell_id(y: int, x: int) -> int:
    return y * WIDTH + x


def coords_from_cell(cid: int) -> list[int]:
    return [int(cid % WIDTH), int(cid // WIDTH)]


def make_observables() -> np.ndarray:
    y, x = np.mgrid[0:HEIGHT, 0:WIDTH]
    o0 = (x - 5) ** 2 + 2 * (y - 4) ** 2 - 18
    o1 = 3 * x - 4 * y - 2
    o2 = 2 * y + x - 13
    return np.stack([o0, o1, o2], axis=-1).astype(np.int64)


def perturb_observable_values(observables: np.ndarray) -> tuple[np.ndarray, dict]:
    y, x = np.mgrid[0:HEIGHT, 0:WIDTH]
    mask = (x >= 4) & (x <= 7) & (y >= 2) & (y <= 6)
    out = observables.copy()
    out[..., 0] = out[..., 0] + (10 * mask.astype(np.int64))
    perturbation = {
        "kind": "real_observable_value_perturbation",
        "observable": "o0",
        "delta": 10,
        "mask_cell_ids": [cell_id(int(yy), int(xx)) for yy, xx in np.argwhere(mask)],
        "note": "Only o0 values are changed. Thresholds, adjacency, and display labels are unchanged.",
    }
    return out, perturbation


def threshold_signature(observables: np.ndarray) -> np.ndarray:
    return np.stack(
        [
            observables[..., 0] <= THRESHOLDS["o0_basin_leq"],
            observables[..., 1] >= THRESHOLDS["o1_shear_geq"],
            observables[..., 2] >= THRESHOLDS["o2_north_geq"],
        ],
        axis=-1,
    )


def signature_code(bits: np.ndarray | list[bool] | tuple[bool, ...]) -> str:
    return "".join("1" if bool(v) else "0" for v in bits)


def neighbors(y: int, x: int):
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        yy = y + dy
        xx = x + dx
        if 0 <= yy < HEIGHT and 0 <= xx < WIDTH:
            yield yy, xx


def connected_components_bfs(signatures: np.ndarray) -> tuple[list[dict], list[int]]:
    seen = np.zeros((HEIGHT, WIDTH), dtype=bool)
    raw_components: list[dict] = []

    for y in range(HEIGHT):
        for x in range(WIDTH):
            if seen[y, x]:
                continue
            sig = tuple(bool(v) for v in signatures[y, x])
            q: deque[tuple[int, int]] = deque([(y, x)])
            seen[y, x] = True
            cells: list[int] = []
            while q:
                cy, cx = q.popleft()
                cells.append(cell_id(cy, cx))
                for ny, nx in neighbors(cy, cx):
                    if seen[ny, nx]:
                        continue
                    if tuple(bool(v) for v in signatures[ny, nx]) != sig:
                        continue
                    seen[ny, nx] = True
                    q.append((ny, nx))
            raw_components.append({
                "signature_bits": [int(v) for v in sig],
                "signature_code": signature_code(sig),
                "min_cell_id": min(cells),
                "size": len(cells),
                "cells": sorted(cells),
            })

    raw_components.sort(key=lambda c: c["min_cell_id"])
    membership = [-1 for _ in range(N_CELLS)]
    components: list[dict] = []
    for component_id, comp in enumerate(raw_components):
        cells = comp["cells"]
        xs = [cid % WIDTH for cid in cells]
        ys = [cid // WIDTH for cid in cells]
        for cid in cells:
            membership[cid] = component_id
        components.append({
            "component_id": component_id,
            **comp,
            "bbox_xyxy": [min(xs), min(ys), max(xs), max(ys)],
        })
    return components, membership


def boundary_edges(signatures: np.ndarray) -> list[list[int]]:
    edges: list[list[int]] = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            here = signatures[y, x]
            for dy, dx in ((1, 0), (0, 1)):
                yy = y + dy
                xx = x + dx
                if yy >= HEIGHT or xx >= WIDTH:
                    continue
                if not np.array_equal(here, signatures[yy, xx]):
                    edges.append([cell_id(y, x), cell_id(yy, xx)])
    return edges


def structure_hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def labels_by_signature(discovery: dict) -> dict[str, str]:
    return {row["signature_code"]: row["display_label"] for row in discovery["inequality_regions"]}


# Structural keys that define the discovered quotient. The structure hash is a
# PROJECTION of the full (label-carrying) discovery onto these keys. Because the
# projection is taken from the same dict that carries display_label, if a label
# ever leaked into one of these structural fields the projection -- and therefore
# the hash -- would change under a label shuffle. The hash is NOT built from a
# hand-curated label-free payload, so label_shuffle_structure_invariant is a
# genuine could-fail control, not a by-construction tautology.
STRUCTURAL_COMPONENT_KEYS = ("signature_code", "min_cell_id", "size", "cells", "bbox_xyxy")


def structural_projection(discovery: dict) -> dict:
    """Project a full discovery dict onto structural-only keys.

    display_label fields are dropped here. If labels had contaminated any
    structural field (component cells/sizes/codes, membership, edges) the
    projection would differ between a default-labeled and a shuffled-labeled
    discovery of the same observables.
    """
    return {
        "grid_shape": discovery["grid_shape"],
        "threshold_signature_name": discovery["threshold_signature_name"],
        "equivalence_relation_name": discovery["equivalence_relation_name"],
        "thresholds": discovery["thresholds"],
        "component_classes": [
            {k: comp[k] for k in STRUCTURAL_COMPONENT_KEYS}
            for comp in discovery["connected_components"]
        ],
        "boundary_edges": discovery["boundary_edges"],
        "cell_membership_by_id": discovery["cell_membership_by_id"],
    }


def discover(observables: np.ndarray, display_labels: dict[str, str]) -> dict:
    signatures = threshold_signature(observables)
    components, membership = connected_components_bfs(signatures)
    edges = boundary_edges(signatures)
    sig_counts = Counter(signature_code(signatures[y, x]) for y in range(HEIGHT) for x in range(WIDTH))

    named_components = [
        {
            **comp,
            "display_label": display_labels[comp["signature_code"]],
        }
        for comp in components
    ]

    discovery = {
        "grid_shape": [HEIGHT, WIDTH],
        "n_probe_cells": N_CELLS,
        "threshold_signature_name": THRESHOLD_SIGNATURE_NAME,
        "equivalence_relation_name": EQUIVALENCE_RELATION_NAME,
        "thresholds": THRESHOLDS,
        "inequality_regions": [
            {
                "signature_code": code,
                "signature_bits": [int(ch) for ch in code],
                "cell_count": int(sig_counts[code]),
                "display_label": display_labels[code],
            }
            for code in sorted(sig_counts)
        ],
        "connected_components": named_components,
        "cell_membership_by_id": membership,
        "boundary_edges": edges,
    }
    # Hash the structural projection of THIS label-carrying discovery, not a
    # separately curated label-free payload. A label leak into any structural
    # field would change this hash under a shuffle.
    discovery["structure_hash"] = structure_hash(structural_projection(discovery))
    return discovery


def main() -> int:
    base_observables = make_observables()
    perturbed_observables, perturbation = perturb_observable_values(base_observables)

    base = discover(base_observables, DEFAULT_LABELS)
    label_shuffled = discover(base_observables, SHUFFLED_LABELS)
    perturbed = discover(perturbed_observables, DEFAULT_LABELS)

    base_signatures = threshold_signature(base_observables)
    perturbed_signatures = threshold_signature(perturbed_observables)
    changed_cell_ids = [
        cell_id(y, x)
        for y in range(HEIGHT)
        for x in range(WIDTH)
        if not np.array_equal(base_signatures[y, x], perturbed_signatures[y, x])
    ]
    base_edges = {tuple(e) for e in base["boundary_edges"]}
    perturbed_edges = {tuple(e) for e in perturbed["boundary_edges"]}
    boundary_edge_symmetric_difference = sorted([list(e) for e in (base_edges ^ perturbed_edges)])

    base_component_sizes = sorted(comp["size"] for comp in base["connected_components"])
    perturbed_component_sizes = sorted(comp["size"] for comp in perturbed["connected_components"])
    base_signature_count = len(base["inequality_regions"])
    perturbed_signature_count = len(perturbed["inequality_regions"])

    # Runtime evidence that labels are not consumed by the region computation.
    # Discover the SAME observables twice with different display-label maps and
    # compare the structural projection (components/membership/edges, labels
    # dropped). Byte-identical projections => the discovered structure does not
    # depend on the only label-like input. This replaces the old hardcoded
    # no_terrain_labels_used=True self-certification. It is computed from a path
    # that COULD have leaked labels (discover() receives the label map), so it
    # could fail if labels contaminated the structure.
    base_structural = json.dumps(structural_projection(base), sort_keys=True)
    shuffled_structural = json.dumps(structural_projection(label_shuffled), sort_keys=True)
    region_computation_label_independent = bool(base_structural == shuffled_structural)

    tests = {
        "no_terrain_labels_consumed_in_region_computation": region_computation_label_independent,
        "nonuniversal_threshold_relation": bool(base_signature_count > 1 and len(base["connected_components"]) > 1),
        "discovers_inequality_regions": bool(base_signature_count == 8),
        "discovers_connected_components": bool(len(base["connected_components"]) == 8),
        "cell_membership_total": bool(len(base["cell_membership_by_id"]) == N_CELLS and min(base["cell_membership_by_id"]) == 0),
        "equivalence_classes_cover_probe_quotient": bool(sum(comp["size"] for comp in base["connected_components"]) == N_CELLS),
    }
    controls = {
        "label_shuffle_structure_invariant": bool(base["structure_hash"] == label_shuffled["structure_hash"]),
        "label_shuffle_display_names_changed": bool(
            [r["display_label"] for r in base["inequality_regions"]]
            != [r["display_label"] for r in label_shuffled["inequality_regions"]]
        ),
        "observable_perturbation_changes_region_membership": bool(len(changed_cell_ids) > 0),
        "value_change_control_moves_boundaries": bool(len(boundary_edge_symmetric_difference) > 0),
        "value_change_changes_component_count": bool(len(base["connected_components"]) != len(perturbed["connected_components"])),
        "value_change_not_label_change": bool(
            base["thresholds"] == perturbed["thresholds"]
            and labels_by_signature(base) == labels_by_signature(perturbed)
        ),
    }
    all_tests = all(tests.values())
    all_controls = all(controls.values())

    invariants = {
        "grid_shape": [HEIGHT, WIDTH],
        "n_probe_cells": N_CELLS,
        "equivalence_relation_name": EQUIVALENCE_RELATION_NAME,
        "threshold_signature_name": THRESHOLD_SIGNATURE_NAME,
        "base_n_signatures": base_signature_count,
        "base_n_components": len(base["connected_components"]),
        "base_component_sizes": base_component_sizes,
        "base_boundary_edges_count": len(base["boundary_edges"]),
        "base_structure_hash": base["structure_hash"],
        "label_shuffle_structure_hash": label_shuffled["structure_hash"],
        "perturbed_n_signatures": perturbed_signature_count,
        "perturbed_n_components": len(perturbed["connected_components"]),
        "perturbed_component_sizes": perturbed_component_sizes,
        "perturbed_boundary_edges_count": len(perturbed["boundary_edges"]),
        "perturbed_structure_hash": perturbed["structure_hash"],
        "value_changed_cell_ids": changed_cell_ids,
        "value_changed_cell_coords_xy": [coords_from_cell(cid) for cid in changed_cell_ids],
        "boundary_edge_symmetric_difference_count": len(boundary_edge_symmetric_difference),
    }

    result = {
        "schema": "codex_ratchet.sim_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "engine": "exact_numpy_bfs_reference",
        "root_lineage": {
            "F01_finite_support": True,
            "L12_region_discovery_from_observables": "region classes are the quotient P / equiv_{O,tau,A4}; no terrain labels enter the relation",
        },
        "source_target": "Manifold-tower L12: region discovery from observables (NO terrain labels).",
        "claim": "finite probe regions are discovered from observable threshold signatures plus 4-neighbor connectedness; label shuffling leaves structure invariant, while real observable value perturbation moves boundaries and quotient classes.",
        "equivalence_relation": {
            "name": EQUIVALENCE_RELATION_NAME,
            "threshold_signature_name": THRESHOLD_SIGNATURE_NAME,
            "definition": "p equiv_{O,tau,A4} q iff sigma_tau(O(p)) = sigma_tau(O(q)) and there exists a 4-neighbor path from p to q whose every cell has that same threshold signature.",
            "thresholds": THRESHOLDS,
            "adjacency": "A4 grid adjacency",
            "not_universal": tests["nonuniversal_threshold_relation"],
        },
        "base_discovery": base,
        "label_shuffle_control": {
            "shuffled_display_labels": SHUFFLED_LABELS,
            "structure_hash": label_shuffled["structure_hash"],
            "structure_invariant": controls["label_shuffle_structure_invariant"],
        },
        "value_change_control": {
            "perturbation": perturbation,
            "perturbed_discovery": perturbed,
            "changed_cell_ids": changed_cell_ids,
            "boundary_edge_symmetric_difference": boundary_edge_symmetric_difference,
        },
        "invariants": invariants,
        "tests": tests,
        "controls": controls,
        "all_tests_pass": all_tests,
        "all_controls_pass": all_controls,
        "honest_scope": {
            "earns": "one exact finite BFS witness that observable threshold values force discovered inequality regions, connected components, cell membership, and probe-quotient equivalence classes; label names do not affect structure, and an o0 value perturbation moves the discovered boundaries.",
            "does_not_earn": "smooth manifold admission, canonical L12 theorem, terrain-labeled segmentation, formal admission, or promotion beyond scratch_diagnostic.",
        },
        "TOOL_MANIFEST": {
            "numpy": {
                "tried": True,
                "used": True,
                "reason": "integer observable arrays, threshold signatures, and exact finite grid storage for the reference leg",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "reason": "explicit BFS, structural hashing, counters, and JSON receipt writing",
            },
        },
        "TOOL_INTEGRATION_DEPTH": "supportive",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print(f"wrote {RESULT}")
    print(f"all_tests_pass={all_tests} all_controls_pass={all_controls}")
    print(f"base components={len(base['connected_components'])} signatures={base_signature_count} boundary_edges={len(base['boundary_edges'])}")
    print(f"perturbed components={len(perturbed['connected_components'])} changed_cells={len(changed_cell_ids)} boundary_delta={len(boundary_edge_symmetric_difference)}")
    print(f"label_shuffle_structure_invariant={controls['label_shuffle_structure_invariant']}")
    return 0 if all_tests and all_controls else 1


if __name__ == "__main__":
    raise SystemExit(main())
