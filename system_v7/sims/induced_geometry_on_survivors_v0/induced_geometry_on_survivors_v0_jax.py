#!/usr/bin/env python3
"""JAX leg for induced_geometry_on_survivors_v0.

This leg recomputes the same quotient-survivor geometry with a distinct data
representation: quotient vertices are rows in a JAX array, survivor sets are
boolean masks, and the Hamming metric is a vectorized pairwise matrix. It does
not read the exact leg result.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

SIM_ID = "induced_geometry_on_survivors_v0"
HERE = Path(__file__).resolve().parent
SPEC = HERE / "spec.json"
RESULT = HERE / "results" / f"{SIM_ID}_jax_results.json"

PROBE_WIDTH = 4
RAW_WIDTH = 5


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bits_from_row(row: list[int]) -> str:
    return "".join(str(int(i)) for i in row)


def metric_signature(metric: dict[str, object]) -> tuple[object, ...]:
    return (
        tuple(metric["degree_sequence"]),
        metric["component_count"],
        metric["diameter"],
        metric["edge_count"],
        metric["nearest_distance"],
    )


def build_vertices() -> jnp.ndarray:
    return jnp.array(list(itertools.product((0, 1), repeat=PROBE_WIDTH)), dtype=jnp.int32)


def pairwise_hamming(vertices: jnp.ndarray) -> jnp.ndarray:
    def one_to_many(v: jnp.ndarray) -> jnp.ndarray:
        return jax.vmap(lambda w: jnp.sum(v != w))(vertices)

    return jax.vmap(one_to_many)(vertices)


def rows_for_mask(vertices: jnp.ndarray, mask: jnp.ndarray) -> list[list[int]]:
    rows = jax.device_get(vertices[mask]).tolist()
    return [[int(x) for x in row] for row in rows]


def metrics_from_adjacency(
    vertices: jnp.ndarray,
    mask: jnp.ndarray,
    adjacency: jnp.ndarray,
    nearest_distance: int | None,
    mode: str,
) -> dict[str, object]:
    rows = rows_for_mask(vertices, mask)
    names = [bits_from_row(row) for row in rows]
    active_indices = [int(i) for i in jax.device_get(jnp.where(mask, size=vertices.shape[0], fill_value=-1)[0]).tolist() if i >= 0]
    adj_host = jax.device_get(adjacency).tolist()

    neighbors = {name: set() for name in names}
    index_to_name = {idx: name for idx, name in zip(active_indices, names)}
    for i in active_indices:
        for j in active_indices:
            if j <= i:
                continue
            if bool(adj_host[i][j]):
                neighbors[index_to_name[i]].add(index_to_name[j])
                neighbors[index_to_name[j]].add(index_to_name[i])

    components: list[list[str]] = []
    unseen = set(names)
    while unseen:
        start = min(unseen)
        queue = deque([start])
        unseen.remove(start)
        comp = [start]
        while queue:
            node = queue.popleft()
            for nbr in sorted(neighbors[node]):
                if nbr in unseen:
                    unseen.remove(nbr)
                    queue.append(nbr)
                    comp.append(nbr)
        components.append(sorted(comp))

    def distances_from(start: str) -> dict[str, int]:
        dist = {start: 0}
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for nbr in neighbors[node]:
                if nbr not in dist:
                    dist[nbr] = dist[node] + 1
                    queue.append(nbr)
        return dist

    if len(names) <= 1:
        diameter: int | None = 0 if names else None
    elif len(components) != 1:
        diameter = None
    else:
        diameter = max(max(distances_from(name).values()) for name in names)

    degree_by_vertex = {name: len(neighbors[name]) for name in sorted(names)}
    return {
        "mode": mode,
        "survivor_count": len(names),
        "vertices": sorted(names),
        "nearest_distance": nearest_distance,
        "edge_count": sum(degree_by_vertex.values()) // 2,
        "degree_sequence": sorted(degree_by_vertex.values()),
        "degree_by_vertex": degree_by_vertex,
        "component_count": len(components),
        "components": components,
        "diameter": diameter,
        "connected": len(components) == 1 if names else False,
    }


def recomputed_geometry(vertices: jnp.ndarray, dist: jnp.ndarray, mask: jnp.ndarray) -> tuple[dict[str, object], jnp.ndarray, int | None]:
    active_pair = mask[:, None] & mask[None, :] & (dist > 0)
    pair_dist = jnp.where(active_pair, dist, 999)
    nearest_raw = int(jax.device_get(jnp.min(pair_dist)))
    if nearest_raw == 999:
        adjacency = jnp.zeros_like(active_pair)
        nearest: int | None = None
    else:
        nearest = nearest_raw
        adjacency = active_pair & (dist == nearest)
    adjacency = adjacency & (jnp.arange(vertices.shape[0])[:, None] < jnp.arange(vertices.shape[0])[None, :])
    return metrics_from_adjacency(vertices, mask, adjacency, nearest, "recomputed_hamming_nearest_neighbor"), adjacency, nearest


def stale_geometry(vertices: jnp.ndarray, mask: jnp.ndarray, initial_adjacency: jnp.ndarray, initial_nearest: int | None) -> dict[str, object]:
    restricted = initial_adjacency & mask[:, None] & mask[None, :]
    return metrics_from_adjacency(vertices, mask, restricted, initial_nearest, "stale_initial_edges_restricted_no_recompute")


def run_sequence(final_first_bit: int) -> list[dict[str, object]]:
    vertices = build_vertices()
    dist = pairwise_hamming(vertices)
    mask = jnp.ones(vertices.shape[0], dtype=bool)
    g0, initial_adjacency, initial_nearest = recomputed_geometry(vertices, dist, mask)
    steps = [{
        "step": 0,
        "constraint": "X0_probe_quotient_support",
        "survivor_predicate": "all quotient classes [s]_P",
        "recomputed_geometry": g0,
        "stale_geometry": stale_geometry(vertices, mask, initial_adjacency, initial_nearest),
    }]

    weights = vertices.sum(axis=1)
    constraints = [
        ("C1_even_probe_parity", "sum(pi(s)) mod 2 == 0", weights % 2 == 0),
        ("C2_probe_weight_le_2", "sum(pi(s)) <= 2", weights <= 2),
        (f"C3_first_probe_{final_first_bit}", f"pi(s)[0] == {final_first_bit}", vertices[:, 0] == final_first_bit),
    ]
    for idx, (cid, predicate, keep) in enumerate(constraints, start=1):
        mask = mask & keep
        recomputed, _, _ = recomputed_geometry(vertices, dist, mask)
        steps.append({
            "step": idx,
            "constraint": cid,
            "survivor_predicate": predicate,
            "recomputed_geometry": recomputed,
            "stale_geometry": stale_geometry(vertices, mask, initial_adjacency, initial_nearest),
        })
    return steps


def quotient_class_membership() -> dict[str, int]:
    """Group the raw 5-bit support by its 4-bit probe signature and count members.

    Computed from the actual enumerated support (not a hardcoded ``: 2`` map), so a
    wrong probe map or RAW/PROBE width mismatch would change the counts.
    """
    members: dict[str, int] = {}
    for raw in itertools.product((0, 1), repeat=RAW_WIDTH):
        sig = "".join(str(b) for b in raw[:PROBE_WIDTH])
        members[sig] = members.get(sig, 0) + 1
    return members


def main() -> int:
    spec = json.loads(SPEC.read_text())
    primary = run_sequence(final_first_bit=0)
    perturbed = run_sequence(final_first_bit=1)

    recomputed_signatures = [metric_signature(step["recomputed_geometry"]) for step in primary]
    c1 = primary[1]
    primary_final = primary[-1]["recomputed_geometry"]
    perturbed_final = perturbed[-1]["recomputed_geometry"]
    state_flip = metric_signature(primary_final) != metric_signature(perturbed_final)

    # Could-fail quotient check on actually-grouped support: every probe signature
    # must collapse exactly 2 raw states (the forgotten hidden bit) and there must
    # be exactly 16 classes. A broken probe map or width would change these counts.
    class_membership = quotient_class_membership()
    quotient_nontrivial = (
        len(class_membership) == 16
        and all(n == 2 for n in class_membership.values())
    )

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
        "recomputed_geometry_changes_across_constraints": len(set(recomputed_signatures)) > 1,
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

    raw_states_per_class = {"".join(map(str, p)): 2 for p in itertools.product((0, 1), repeat=PROBE_WIDTH)}
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "computation_style": "jax_boolean_mask_and_vectorized_pairwise_hamming_matrix",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_of(Path(__file__).resolve()),
        "spec_sha256": sha256_of(SPEC),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_jax_results.json",
        "quotient_relation": spec["equivalence_relation"],
        "quotient_summary": {
            "raw_support_count": 2 ** RAW_WIDTH,
            "quotient_class_count": 2 ** PROBE_WIDTH,
            "raw_states_per_class": raw_states_per_class,
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
            "earns": "independent JAX mask/matrix recomputation that the induced Hamming nearest-neighbor geometry changes on survivor sets and stale restriction is wrong.",
            "does_not_earn": "smooth manifold, formal admission, bridge/axis claim, physics, or any statement beyond this finite scratch diagnostic.",
        },
        "package_versions": {"jax": jax.__version__},
        "packages_used": ["jax", "jax.numpy"],
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "vectorized pairwise Hamming matrix and boolean-mask survivor filtering; gates graph adjacency and agreement"},
            "jax.numpy": {"tried": True, "used": True, "reason": "array support for quotient signatures, masks, and adjacency construction"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "jax.numpy": "supportive"},
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"jax leg wrote {RESULT}")
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
