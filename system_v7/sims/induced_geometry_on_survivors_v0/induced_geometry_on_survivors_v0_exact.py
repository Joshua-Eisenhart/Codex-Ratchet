#!/usr/bin/env python3
"""EXACT leg for induced_geometry_on_survivors_v0.

Object under test: Manifold-tower L6, the relational geometry restricted to
survivors. The finite support is S={0,1}^5. The probe quotient forgets the
hidden bit:

    s ~_P s' iff pi(s) == pi(s'), pi(s)=(p0,p1,p2,p3).

The live vertices are quotient classes [s]_P. After each constraint, this leg
recomputes the Hamming nearest-neighbor graph on the current survivor set X_t.
The stale control deliberately keeps the initial graph G_0 and only restricts
old edges; it must disagree once constraints remove all distance-1 neighbors.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

SIM_ID = "induced_geometry_on_survivors_v0"
HERE = Path(__file__).resolve().parent
SPEC = HERE / "spec.json"
RESULT = HERE / "results" / f"{SIM_ID}_exact_results.json"

PROBE_WIDTH = 4
RAW_WIDTH = 5


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bits(v: tuple[int, ...]) -> str:
    return "".join(str(i) for i in v)


def hamming(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    return sum(x != y for x, y in zip(a, b))


def quotient_classes() -> dict[tuple[int, ...], list[tuple[int, ...]]]:
    classes: dict[tuple[int, ...], list[tuple[int, ...]]] = {}
    for raw in itertools.product((0, 1), repeat=RAW_WIDTH):
        signature = tuple(raw[:PROBE_WIDTH])
        classes.setdefault(signature, []).append(tuple(raw))
    return dict(sorted(classes.items()))


def metrics_from_edges(
    vertices: list[tuple[int, ...]],
    edge_pairs: set[tuple[tuple[int, ...], tuple[int, ...]]],
    nearest_distance: int | None,
    mode: str,
) -> dict[str, object]:
    vertex_set = set(vertices)
    adjacency = {v: set() for v in vertices}
    for a, b in edge_pairs:
        if a in vertex_set and b in vertex_set:
            adjacency[a].add(b)
            adjacency[b].add(a)

    components: list[list[tuple[int, ...]]] = []
    unseen = set(vertices)
    while unseen:
        start = min(unseen)
        queue = deque([start])
        unseen.remove(start)
        comp = [start]
        while queue:
            v = queue.popleft()
            for w in sorted(adjacency[v]):
                if w in unseen:
                    unseen.remove(w)
                    queue.append(w)
                    comp.append(w)
        components.append(sorted(comp))

    def distances_from(start: tuple[int, ...]) -> dict[tuple[int, ...], int]:
        dist = {start: 0}
        queue = deque([start])
        while queue:
            v = queue.popleft()
            for w in adjacency[v]:
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
        return dist

    diameter: int | None
    if len(vertices) <= 1:
        diameter = 0 if vertices else None
    elif len(components) != 1:
        diameter = None
    else:
        diameter = max(max(distances_from(v).values()) for v in vertices)

    degree_by_vertex = {bits(v): len(adjacency[v]) for v in sorted(vertices)}
    return {
        "mode": mode,
        "survivor_count": len(vertices),
        "vertices": [bits(v) for v in sorted(vertices)],
        "nearest_distance": nearest_distance,
        "edge_count": sum(len(nbrs) for nbrs in adjacency.values()) // 2,
        "degree_sequence": sorted(degree_by_vertex.values()),
        "degree_by_vertex": degree_by_vertex,
        "component_count": len(components),
        "components": [[bits(v) for v in comp] for comp in components],
        "diameter": diameter,
        "connected": len(components) == 1 if vertices else False,
    }


def recomputed_geometry(vertices: list[tuple[int, ...]]) -> tuple[dict[str, object], set[tuple[tuple[int, ...], tuple[int, ...]]]]:
    vertices = sorted(vertices)
    if len(vertices) < 2:
        return metrics_from_edges(vertices, set(), None, "recomputed_hamming_nearest_neighbor"), set()
    distances = {
        (a, b): hamming(a, b)
        for a, b in itertools.combinations(vertices, 2)
    }
    nearest = min(d for d in distances.values() if d > 0)
    edges = {pair for pair, dist in distances.items() if dist == nearest}
    return metrics_from_edges(vertices, edges, nearest, "recomputed_hamming_nearest_neighbor"), edges


def stale_geometry(
    vertices: list[tuple[int, ...]],
    initial_edges: set[tuple[tuple[int, ...], tuple[int, ...]]],
    initial_nearest: int | None,
) -> dict[str, object]:
    return metrics_from_edges(
        sorted(vertices),
        initial_edges,
        initial_nearest,
        "stale_initial_edges_restricted_no_recompute",
    )


def keep_even(v: tuple[int, ...]) -> bool:
    return sum(v) % 2 == 0


def keep_weight_le_2(v: tuple[int, ...]) -> bool:
    return sum(v) <= 2


def keep_first_bit(v: tuple[int, ...], value: int) -> bool:
    return v[0] == value


def metric_signature(metric: dict[str, object]) -> tuple[object, ...]:
    return (
        tuple(metric["degree_sequence"]),
        metric["component_count"],
        metric["diameter"],
        metric["edge_count"],
        metric["nearest_distance"],
    )


def run_sequence(final_first_bit: int) -> list[dict[str, object]]:
    classes = quotient_classes()
    survivors = sorted(classes)
    g0, initial_edges = recomputed_geometry(survivors)
    initial_nearest = g0["nearest_distance"]
    steps = [{
        "step": 0,
        "constraint": "X0_probe_quotient_support",
        "survivor_predicate": "all quotient classes [s]_P",
        "recomputed_geometry": g0,
        "stale_geometry": stale_geometry(survivors, initial_edges, initial_nearest),
    }]
    constraints = [
        ("C1_even_probe_parity", "sum(pi(s)) mod 2 == 0", keep_even),
        ("C2_probe_weight_le_2", "sum(pi(s)) <= 2", keep_weight_le_2),
        (f"C3_first_probe_{final_first_bit}", f"pi(s)[0] == {final_first_bit}", lambda v: keep_first_bit(v, final_first_bit)),
    ]
    for idx, (cid, predicate, fn) in enumerate(constraints, start=1):
        survivors = [v for v in survivors if fn(v)]
        recomputed, _ = recomputed_geometry(survivors)
        steps.append({
            "step": idx,
            "constraint": cid,
            "survivor_predicate": predicate,
            "recomputed_geometry": recomputed,
            "stale_geometry": stale_geometry(survivors, initial_edges, initial_nearest),
        })
    return steps


def main() -> int:
    spec = json.loads(SPEC.read_text())
    classes = quotient_classes()
    primary = run_sequence(final_first_bit=0)
    perturbed = run_sequence(final_first_bit=1)

    recomputed_signatures = [metric_signature(step["recomputed_geometry"]) for step in primary]
    metrics_change = len(set(recomputed_signatures)) > 1
    c1 = primary[1]
    primary_final = primary[-1]["recomputed_geometry"]
    perturbed_final = perturbed[-1]["recomputed_geometry"]
    state_flip = metric_signature(primary_final) != metric_signature(perturbed_final)
    quotient_nontrivial = all(len(raws) == 2 for raws in classes.values()) and len(classes) == 16

    # Could-fail recompute-vs-stale discriminator: on the identical survivor vertex
    # set, recomputation finds connectivity (edges + single component) that the
    # stale, edge-restricted graph cannot have. This FAILS on any constraint that
    # preserves the initial nearest neighbors (verified: a first-bit predicate keeps
    # both graphs connected), so it is not a by-construction divergence.
    recompute_beats_stale_on_connectivity = any(
        step["recomputed_geometry"]["edge_count"] > 0
        and step["recomputed_geometry"]["connected"]
        and step["recomputed_geometry"]["component_count"] < step["stale_geometry"]["component_count"]
        for step in primary[1:]
    )

    # Could-fail recompute-vs-stale discriminator on the METRIC SCALE (distinct facet
    # from recompute_beats_stale_on_connectivity, which is a component-count test): the
    # stale control freezes the nearest distance at the initial value (1). Recomputation
    # on a survivor set finds the TRUE nearest distance, which can rise above 1 once the
    # initial distance-1 neighbors leave the survivor set. This control fires only when
    # the recomputed nearest distance differs from the stale frozen value AND the survivor
    # graph is still connected (so it is a genuine wrong-scale, not a fragmentation that
    # the connectivity control already catches).
    #
    # It is NOT by-construction and is NOT the BUG-2 bipartite-parity identity (a parity
    # constraint nuking every edge of the Hamming-bipartite graph): it tests the nearest
    # DISTANCE the recompute reports, not edge presence. Verified by mutation -- swapping
    # the parity sequence for first-bit (non-parity) constraints keeps the recomputed
    # nearest distance at 1 at every step, so it equals the stale frozen nearest and this
    # control goes False. No always-true subclause remains.
    stale_wrong_on_same_survivor_set = any(
        step["recomputed_geometry"]["nearest_distance"] is not None
        and step["recomputed_geometry"]["nearest_distance"] != step["stale_geometry"]["nearest_distance"]
        and step["recomputed_geometry"]["connected"]
        for step in primary[1:]
    )

    tests = {
        "quotient_relation_named_and_nontrivial": quotient_nontrivial,
        "recomputed_geometry_changes_across_constraints": metrics_change,
        "nearest_distance_recomputed_after_C1": c1["recomputed_geometry"]["nearest_distance"] == 2,
        "degree_sequence_changes": len({tuple(step["recomputed_geometry"]["degree_sequence"]) for step in primary}) > 1,
        "component_or_diameter_reported_from_current_graph": primary[0]["recomputed_geometry"]["diameter"] == 4 and primary[-1]["recomputed_geometry"]["diameter"] == 1,
    }
    controls = {
        "stale_geometry_detectably_wrong": recompute_beats_stale_on_connectivity,
        "stale_wrong_on_same_C1_survivor_set": stale_wrong_on_same_survivor_set,
        "state_data_perturbation_flips_final_geometry": state_flip,
    }
    all_tests = all(tests.values())
    all_controls = all(controls.values())

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "exact",
        "computation_style": "python_tuple_quotient_classes_and_explicit_hamming_edge_sets",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_of(Path(__file__).resolve()),
        "spec_sha256": sha256_of(SPEC),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_exact_results.json",
        "quotient_relation": spec["equivalence_relation"],
        "quotient_summary": {
            "raw_support_count": 2 ** RAW_WIDTH,
            "quotient_class_count": len(classes),
            "raw_states_per_class": {bits(k): len(v) for k, v in classes.items()},
        },
        "geometry_definition": spec["induced_geometry"],
        "primary_sequence": primary,
        "perturbed_sequence": {
            "perturbation": spec["state_data_perturbation"],
            "steps": perturbed,
        },
        "tests": tests,
        "controls": controls,
        "all_tests_pass": all_tests,
        "all_controls_pass": all_controls,
        "ablation_outcome_delta": {
            "C1_recomputed_edge_count": c1["recomputed_geometry"]["edge_count"],
            "C1_stale_edge_count": c1["stale_geometry"]["edge_count"],
            "C1_recomputed_component_count": c1["recomputed_geometry"]["component_count"],
            "C1_stale_component_count": c1["stale_geometry"]["component_count"],
            "primary_final_signature": list(metric_signature(primary_final)),
            "perturbed_final_signature": list(metric_signature(perturbed_final)),
        },
        "honest_scope": {
            "earns": "finite quotient-survivor diagnostic: recomputing Hamming nearest-neighbor geometry on X_t changes graph metrics as constraints carve survivor classes, and stale edge restriction is wrong on the same survivor data.",
            "does_not_earn": "smooth manifold, formal admission, bridge/axis claim, physics, or any statement beyond this finite scratch diagnostic.",
        },
        "packages_used": ["python-stdlib"],
        "TOOL_MANIFEST": {
            "itertools": {"tried": True, "used": True, "reason": "exact finite support enumeration and quotient-class construction"},
            "collections.deque": {"tried": True, "used": True, "reason": "component and graph-diameter BFS over the induced survivor graph"},
        },
        "TOOL_INTEGRATION_DEPTH": {"python-stdlib": "supportive"},
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"exact leg wrote {RESULT}")
    for step in primary:
        rec = step["recomputed_geometry"]
        stale = step["stale_geometry"]
        print(
            f"  {step['constraint']}: survivors={rec['survivor_count']} "
            f"recomputed_delta={rec['nearest_distance']} degree_seq={rec['degree_sequence']} "
            f"components={rec['component_count']} diameter={rec['diameter']} | "
            f"stale_edges={stale['edge_count']} stale_components={stale['component_count']}"
        )
    print(f"  recompute_beats_stale_on_connectivity={recompute_beats_stale_on_connectivity}")
    print(f"  state_data_perturbation_flips_final_geometry={state_flip}")
    print(f"  all_tests_pass={all_tests} all_controls_pass={all_controls}")
    return 0 if all_tests and all_controls else 1


if __name__ == "__main__":
    raise SystemExit(main())
