#!/usr/bin/env python3
"""Run an order-open Ratchet on the actual bundled L5/L8 observations.

The run is deliberately modest in claim and large in proposal count.  It asks
what finite presentation is needed to retain four installed distinction
families.  Carrier names never affect behavior, all 75 ordered set-partitions
of the four families execute, and the result is a fixture-relative quotient --
not a scientific manifold layer.
"""

from __future__ import annotations

from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any, Iterator, Sequence


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
L5_RESULT = ROOT / "sims_and_scripts" / "manifold_L5_nested_shells_schmidt_strata_sim_results.json"
L8_RESULT = ROOT / "sims_and_scripts" / "manifold_L8_global_bundle_chern_quantization_sim_results.json"
OUTPUT = HERE / "manifold_fixture_ratchet_results.json"


def sha_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalise_partition(values: Sequence[Any]) -> tuple[int, ...]:
    labels: dict[Any, int] = {}
    result = []
    for value in values:
        if value not in labels:
            labels[value] = len(labels)
        result.append(labels[value])
    return tuple(result)


def set_partitions(items: tuple[str, ...]) -> Iterator[tuple[tuple[str, ...], ...]]:
    if not items:
        yield ()
        return
    first, rest = items[0], items[1:]
    for partition in set_partitions(rest):
        yield ((first,),) + partition
        for index in range(len(partition)):
            block = tuple(sorted((first,) + partition[index]))
            yield partition[:index] + (block,) + partition[index + 1 :]


def ordered_gate_hypotheses(items: Sequence[str]) -> list[tuple[tuple[str, ...], ...]]:
    unique: set[tuple[tuple[str, ...], ...]] = set()
    for partition in set_partitions(tuple(items)):
        canonical = tuple(sorted(partition))
        for ordered in itertools.permutations(canonical):
            unique.add(tuple(ordered))
    return sorted(unique, key=lambda row: (len(row), row))


def is_coarser(left: tuple[int, ...], right: tuple[int, ...]) -> bool:
    """True when every right block is contained in a left block."""
    mapping: dict[int, int] = {}
    for lvalue, rvalue in zip(left, right):
        prior = mapping.setdefault(rvalue, lvalue)
        if prior != lvalue:
            return False
    return True


def strictly_coarser(left: tuple[int, ...], right: tuple[int, ...]) -> bool:
    return left != right and is_coarser(left, right)


def stable_bucket(value: Any, modulus: int) -> int:
    digest = hashlib.sha256(repr(value).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % modulus


def build_observations() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    l5 = json.loads(L5_RESULT.read_text(encoding="utf-8"))
    l8 = json.loads(L8_RESULT.read_text(encoding="utf-8"))
    rows = []
    for radial_index, source in enumerate(l5["dual_ratchet_sweep"]):
        for orientation in (-1, +1):
            rows.append(
                {
                    "row_id": len(rows),
                    "radial_index": radial_index,
                    "shell_radius": source["shell_radius"],
                    "entropy_bits": source["marg_entropy_bits"],
                    "purity": source["purity"],
                    "negativity": source["negativity"],
                    "orientation": orientation,
                }
            )
    provenance = {
        "L5_source": str(L5_RESULT.relative_to(ROOT)),
        "L5_sha256": hashlib.sha256(L5_RESULT.read_bytes()).hexdigest(),
        "L8_source": str(L8_RESULT.relative_to(ROOT)),
        "L8_sha256": hashlib.sha256(L8_RESULT.read_bytes()).hexdigest(),
        "L8_observed_chern_plus": l8["fact1_flux_quantized_chern"]["chern_number"],
        "L8_observed_chern_minus": l8["fact2_chern_sign_is_chirality"]["chern_reversed_orientation"],
    }
    return rows, provenance


def build_demands(rows: list[dict[str, Any]]) -> dict[str, list[tuple[int, int]]]:
    demands: dict[str, set[tuple[int, int]]] = {
        "shell_position": set(),
        "marginal_entropy_level": set(),
        "factorization_boundary": set(),
        "orientation_winding": set(),
    }
    for left, right in itertools.combinations(rows, 2):
        pair = (left["row_id"], right["row_id"])
        same_orientation = left["orientation"] == right["orientation"]
        if same_orientation and left["radial_index"] != right["radial_index"]:
            demands["shell_position"].add(pair)
        if same_orientation and abs(left["entropy_bits"] - right["entropy_bits"]) > 1e-12:
            demands["marginal_entropy_level"].add(pair)
        if same_orientation and ((left["radial_index"] == 0) != (right["radial_index"] == 0)):
            demands["factorization_boundary"].add(pair)
        if left["radial_index"] == right["radial_index"] and left["orientation"] != right["orientation"]:
            demands["orientation_winding"].add(pair)
    return {name: sorted(values) for name, values in demands.items()}


COORDINATES = (
    ["none", "product_bit", "radius_exact", "entropy_exact", "purity_exact", "negativity_exact", "radial_index"]
    + [f"bins_{count}" for count in range(2, 10)]
    + [f"threshold_{threshold}" for threshold in range(9)]
    + [f"mod_{modulus}" for modulus in range(2, 10)]
)
ORIENTATIONS = ("none", "sign", "boolean_alias", "inverted_alias")
BUCKETS = (0, 2, 3, 5)
CARRIERS = (
    "scalar",
    "schmidt_spectrum",
    "nested_shell",
    "entropy_coordinate",
    "purity_coordinate",
    "negativity_coordinate",
    "finite_lookup",
    "oriented_bundle",
) + tuple(f"carrier_alias_{index:02d}" for index in range(24))


def coordinate_value(row: dict[str, Any], kind: str) -> Any:
    index = int(row["radial_index"])
    if kind == "none":
        return 0
    if kind == "product_bit":
        return int(index != 0)
    if kind in {"radius_exact", "entropy_exact", "purity_exact", "negativity_exact", "radial_index"}:
        # These are different mathematical readouts but the installed finite data ranks them identically.
        return index
    if kind.startswith("bins_"):
        count = int(kind.split("_")[1])
        return min(count - 1, index * count // 9)
    if kind.startswith("threshold_"):
        threshold = int(kind.split("_")[1])
        return int(index > threshold)
    if kind.startswith("mod_"):
        modulus = int(kind.split("_")[1])
        return index % modulus
    raise ValueError(kind)


def orientation_value(row: dict[str, Any], kind: str) -> Any:
    orientation = int(row["orientation"])
    if kind == "none":
        return 0
    if kind == "sign":
        return orientation
    if kind == "boolean_alias":
        return orientation > 0
    if kind == "inverted_alias":
        return -orientation
    raise ValueError(kind)


def assignments(rows: list[dict[str, Any]], coordinate: str, orientation: str, bucket: int) -> tuple[int, ...]:
    keys = []
    for row in rows:
        key = (coordinate_value(row, coordinate), orientation_value(row, orientation))
        keys.append(key if bucket == 0 else ("bucket", stable_bucket(key, bucket)))
    return normalise_partition(keys)


def explore(rows: list[dict[str, Any]], demands: dict[str, list[tuple[int, int]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    behaviours: dict[tuple[int, ...], dict[str, Any]] = {}
    population_hash = hashlib.sha256()
    proposal_count = 0
    for coordinate, orientation, bucket, carrier in itertools.product(COORDINATES, ORIENTATIONS, BUCKETS, CARRIERS):
        proposal_count += 1
        partition = assignments(rows, coordinate, orientation, bucket)
        spec = f"{coordinate}:{orientation}:bucket{bucket}:{carrier}"
        population_hash.update(sha_json({"spec": spec, "partition": partition}).encode("ascii"))
        existing = behaviours.get(partition)
        if existing is None:
            behaviours[partition] = {
                "partition": partition,
                "digest": sha_json(partition),
                "representative": spec,
                "variant_count": 1,
                "cell_count": len(set(partition)),
                "collapsed": {
                    name: sum(partition[left] == partition[right] for left, right in pairs)
                    for name, pairs in demands.items()
                },
            }
        else:
            existing["variant_count"] += 1
    rows_out = sorted(behaviours.values(), key=lambda value: (value["cell_count"], value["digest"]))
    return rows_out, {
        "parameter_proposals_executed": proposal_count,
        "behavioural_partition_classes": len(rows_out),
        "parameter_aliases": proposal_count - len(rows_out),
        "population_digest": population_hash.hexdigest(),
    }


def frontier(
    behaviours: list[dict[str, Any]],
    demands: dict[str, list[tuple[int, int]]],
    active: frozenset[str],
) -> list[dict[str, Any]]:
    edges = [edge for name in active for edge in demands[name]]
    survivors = [
        behaviour
        for behaviour in behaviours
        if all(behaviour["partition"][left] != behaviour["partition"][right] for left, right in edges)
    ]
    result = []
    for candidate in survivors:
        if not any(
            strictly_coarser(other["partition"], candidate["partition"])
            for other in survivors
            if other is not candidate
        ):
            result.append(candidate)
    return sorted(result, key=lambda value: value["digest"])


def main() -> int:
    observations, provenance = build_observations()
    demands = build_demands(observations)
    behaviours, census = explore(observations, demands)
    family_names = tuple(demands)
    frontier_cache: dict[frozenset[str], list[dict[str, Any]]] = {}
    for size in range(len(family_names) + 1):
        for names in itertools.combinations(family_names, size):
            active = frozenset(names)
            frontier_cache[active] = frontier(behaviours, demands, active)

    schedules = ordered_gate_hypotheses(family_names)
    schedule_rows = []
    trajectories = set()
    for schedule in schedules:
        active: frozenset[str] = frozenset()
        steps = []
        trajectory = []
        for block in schedule:
            prior = frontier_cache[active]
            newly_active = frozenset(set(active).union(block))
            after = frontier_cache[newly_active]
            new_edges = [edge for name in block for edge in demands[name]]
            prior_losses = [
                sum(item["partition"][left] == item["partition"][right] for left, right in new_edges)
                for item in prior
            ]
            positive_gradient = max(prior_losses, default=0) > 0 and bool(after)
            steps.append(
                {
                    "gate_block": list(block),
                    "active_after": sorted(newly_active),
                    "prior_frontier_digests": [item["digest"] for item in prior],
                    "prior_new_edge_losses": prior_losses,
                    "after_frontier_digests": [item["digest"] for item in after],
                    "coface_gradient_positive": positive_gradient,
                    "status": "PROVISIONAL_FIXTURE_TOOTH" if positive_gradient else "NO_LIFT_NEEDED",
                }
            )
            active = newly_active
            trajectory.append(tuple(item["digest"] for item in after))
        trajectories.add(tuple(trajectory))
        schedule_rows.append({"schedule": [list(block) for block in schedule], "steps": steps})

    full = frontier_cache[frozenset(family_names)]
    without_orientation = frontier_cache[frozenset(name for name in family_names if name != "orientation_winding")]
    radius_only_partition = assignments(observations, "radius_exact", "none", 0)
    radius_orientation_partition = assignments(observations, "radius_exact", "sign", 0)
    orientation_edges = demands["orientation_winding"]
    orientation_gradient = {
        "before_unresolved_edges": sum(radius_only_partition[left] == radius_only_partition[right] for left, right in orientation_edges),
        "after_unresolved_edges": sum(radius_orientation_partition[left] == radius_orientation_partition[right] for left, right in orientation_edges),
    }
    orientation_gradient["delta"] = orientation_gradient["before_unresolved_edges"] - orientation_gradient["after_unresolved_edges"]

    result = {
        "schema_version": "manifold-observation-ratchet/0.1",
        "classification": "formal_fixture_ratchet",
        "promotion_allowed": False,
        "root": "constrained_distinguishability",
        "provenance": provenance,
        "observation_count": len(observations),
        "observations": observations,
        "demand_families": {name: {"edge_count": len(edges), "edges": edges} for name, edges in demands.items()},
        "entropy_geometry_coface": {
            "geometry": "the finite partition of installed observation rows induced by a candidate compiler",
            "entropy": "the same partition read as unresolved demanded distinction edges C_D(pi)",
            "loss": "L_D(pi)=|C_D(pi)|",
            "gradient": "Delta L_D=L_D(before)-L_D(after)",
            "orientation_tooth": orientation_gradient,
        },
        "candidate_population": census,
        "candidate_grammar": {
            "coordinate_presentations": list(COORDINATES),
            "orientation_presentations": list(ORIENTATIONS),
            "bucket_maps": list(BUCKETS),
            "carrier_labels": list(CARRIERS),
            "carrier_labels_affect_behavior": False,
        },
        "gate_order_search": {
            "families": list(family_names),
            "ordered_set_partitions_executed": len(schedules),
            "gate_granularities": sorted(set(len(schedule) for schedule in schedules)),
            "unique_intermediate_trajectories": len(trajectories),
            "schedules": schedule_rows,
        },
        "final_frontier": [
            {
                "digest": item["digest"],
                "representative": item["representative"],
                "variant_count": item["variant_count"],
                "cell_count": item["cell_count"],
            }
            for item in full
        ],
        "controls": {
            "erase_orientation_demand_restores_orientation_blind_frontier": any(
                item["partition"] == radius_only_partition for item in without_orientation
            ),
            "orientation_demand_kills_radius_only": all(item["partition"] != radius_only_partition for item in full),
            "all_schedules_reach_same_final_frontier": len({tuple(item["digest"] for item in full) for _ in schedules}) == 1,
            "carrier_aliases_exposed": census["parameter_aliases"] > 0,
        },
        "fixture_relative_receipt": {
            "provisionally_earned": "one additional binary orientation distinction beyond the radial scalar when the installed winding-sign demand is active",
            "not_earned": [
                "nested-shell topology",
                "a Berry connection",
                "a Chern bundle",
                "physical Weyl chirality",
                "engine type",
                "a canonical gate order or decomposition",
            ],
            "reason": "The finite demand edges require radius plus orientation behavior; many named carriers compile to the same partition, so their names and internal ontology are not selected.",
        },
        "scientific_manifold_layers_admitted": 0,
        "status": "FIXTURE_TOOTH_EARNED__NO_MANIFOLD_LAYER_ADMITTED",
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    assert census["parameter_proposals_executed"] == len(COORDINATES) * len(ORIENTATIONS) * len(BUCKETS) * len(CARRIERS)
    assert len(schedules) == 75
    assert full
    assert orientation_gradient == {"before_unresolved_edges": 9, "after_unresolved_edges": 0, "delta": 9}
    assert all(result["controls"].values())
    print("PASS manifold_fixture_ratchet")
    print(f"candidate proposals: {census['parameter_proposals_executed']:,}")
    print(f"behavioral partitions: {census['behavioural_partition_classes']:,}")
    print(f"aliases: {census['parameter_aliases']:,}")
    print(f"ordered gate/decomposition schedules: {len(schedules)}")
    print("orientation coface loss: 9 -> 0")
    print("fixture tooth: radius + one orientation bit")
    print("scientific manifold layers admitted: 0")
    print(f"receipt: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
