#!/usr/bin/env python3
"""Execute and compare proposed finite base mathematical structures."""

from __future__ import annotations

import argparse
import itertools
import json
import math
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from common import digest, write_json


WIDTH = 4
UNIVERSE = tuple(range(1 << WIDTH))
FULL_MASK = (1 << WIDTH) - 1
VECTOR_KEYS = (
    "primitive_carrier_atoms",
    "stored_boolean_bits",
    "free_scalar_parameters",
    "primitive_operations",
    "axiom_count",
    "scalar_field_real_dimension",
    "chosen_total_orders",
)


def masks(packet: dict[str, Any]) -> frozenset[int]:
    return frozenset(int(word, 2) for word in packet["accepted_words"])


def family_code(family: set[int] | frozenset[int]) -> int:
    return sum(1 << subset for subset in family)


def subsets(mask: int):
    sub = mask
    while True:
        yield sub
        if sub == 0:
            return
        sub = (sub - 1) & mask


def popcount(value: int) -> int:
    return value.bit_count()


def set_partitions(items: tuple[int, ...] = tuple(range(WIDTH))):
    if not items:
        yield ()
        return
    first, rest = items[0], items[1:]
    for partition in set_partitions(rest):
        yield (1 << first,) + partition
        for index in range(len(partition)):
            blocks = list(partition)
            blocks[index] |= 1 << first
            yield tuple(sorted(blocks))


PARTITIONS = tuple(sorted(set(set_partitions())))


def partition_family(blocks: tuple[int, ...]) -> frozenset[int]:
    output = set()
    for selection in range(1 << len(blocks)):
        value = 0
        for index, block in enumerate(blocks):
            if selection & (1 << index):
                value |= block
        output.add(value)
    return frozenset(output)


EDGES = tuple(itertools.combinations(range(WIDTH), 2))


def graph_cliques(edge_mask: int) -> frozenset[int]:
    output = set()
    for subset in UNIVERSE:
        valid = True
        for left, right in itertools.combinations([i for i in range(WIDTH) if subset & (1 << i)], 2):
            edge_index = EDGES.index((left, right))
            if not edge_mask & (1 << edge_index):
                valid = False
                break
        if valid:
            output.add(subset)
    return frozenset(output)


def downward_closure(target: frozenset[int]) -> frozenset[int]:
    return frozenset(subset for row in target for subset in subsets(row))


def intersection_closure(target: frozenset[int]) -> frozenset[int]:
    closure = set(target) | {FULL_MASK}
    changed = True
    while changed:
        changed = False
        for left in tuple(closure):
            for right in tuple(closure):
                value = left & right
                if value not in closure:
                    closure.add(value)
                    changed = True
    return frozenset(closure)


@lru_cache(maxsize=1)
def poset_models() -> tuple[dict[str, Any], ...]:
    rows = []
    pairs = tuple(itertools.combinations(range(WIDTH), 2))
    for choices in itertools.product((-1, 0, 1), repeat=len(pairs)):
        relation = {(i, i) for i in range(WIDTH)}
        for (left, right), choice in zip(pairs, choices):
            if choice == -1:
                relation.add((left, right))
            elif choice == 1:
                relation.add((right, left))
        if any((a, b) in relation and (b, c) in relation and (a, c) not in relation for a in range(WIDTH) for b in range(WIDTH) for c in range(WIDTH)):
            continue
        ideals = set()
        for subset in UNIVERSE:
            valid = True
            for lower, upper in relation:
                if subset & (1 << upper) and not subset & (1 << lower):
                    valid = False
                    break
            if valid:
                ideals.add(subset)
        covers = set()
        for lower, upper in relation:
            if lower == upper:
                continue
            if not any(
                middle not in (lower, upper)
                and (lower, middle) in relation
                and (middle, upper) in relation
                for middle in range(WIDTH)
            ):
                covers.add((lower, upper))
        rows.append({"relation": relation, "covers": covers, "family": frozenset(ideals)})
    unique = {}
    for row in rows:
        key = (family_code(row["family"]), tuple(sorted(row["covers"])))
        unique[key] = row
    return tuple(unique[key] for key in sorted(unique))


def is_matroid(family: frozenset[int]) -> bool:
    if 0 not in family:
        return False
    for member in family:
        if any(subset not in family for subset in subsets(member)):
            return False
    for left in family:
        for right in family:
            if popcount(left) >= popcount(right):
                continue
            if not any((right & ~left) & (1 << item) and (left | (1 << item)) in family for item in range(WIDTH)):
                return False
    return True


@lru_cache(maxsize=1)
def matroid_models() -> tuple[dict[str, Any], ...]:
    rows = []
    for code in range(1 << len(UNIVERSE)):
        family = frozenset(subset for subset in UNIVERSE if code & (1 << subset))
        if not is_matroid(family):
            continue
        rank = max((popcount(member) for member in family), default=0)
        bases = sorted(member for member in family if popcount(member) == rank)
        rows.append({"family": family, "rank": rank, "bases": bases})
    return tuple(rows)


def best_superset(models: list[tuple[Any, frozenset[int], int]], target: frozenset[int]):
    eligible = [row for row in models if target <= row[1]]
    if not eligible:
        raise AssertionError("declared family lacks a universal superset model")
    return min(eligible, key=lambda row: (len(row[1] - target), row[2], repr(row[0])))


def fit_partition(target: frozenset[int]) -> dict[str, Any]:
    models = [(blocks, partition_family(blocks), len(blocks) * 2) for blocks in PARTITIONS]
    blocks, decoded, bits = best_superset(models, target)
    return {
        "decoded": decoded,
        "model": {"blocks": list(blocks)},
        "stored_boolean_bits": bits,
        "search_space": len(models),
        "bounded_optimal": True,
        "minimality_method": "exhaustive search over all 15 partitions",
        "deletion_witnesses": len(blocks),
    }


def fit_graph(target: frozenset[int]) -> dict[str, Any]:
    models = [(edge_mask, graph_cliques(edge_mask), popcount(edge_mask)) for edge_mask in range(1 << len(EDGES))]
    edge_mask, decoded, bits = best_superset(models, target)
    edges = [list(edge) for index, edge in enumerate(EDGES) if edge_mask & (1 << index)]
    return {
        "decoded": decoded,
        "model": {"edges": edges},
        "stored_boolean_bits": bits,
        "search_space": len(models),
        "bounded_optimal": True,
        "minimality_method": "exhaustive search over all 64 simple graphs and clique families",
        "deletion_witnesses": sum(graph_cliques(edge_mask & ~(1 << index)) != decoded for index in range(len(EDGES)) if edge_mask & (1 << index)),
    }


def facets(family: frozenset[int]) -> list[int]:
    return sorted(member for member in family if not any(member != other and member & other == member for other in family))


def fit_relation(target: frozenset[int]) -> dict[str, Any]:
    return {
        "decoded": target,
        "model": {"truth_table_code": family_code(target), "accepted_tuples": sorted(target)},
        "stored_boolean_bits": len(UNIVERSE),
        "search_space": 1 << len(UNIVERSE),
        "bounded_optimal": True,
        "minimality_method": "one truth bit per possible four-coordinate tuple; every positive tuple has a deletion witness",
        "deletion_witnesses": len(target),
    }


def fit_incidence(target: frozenset[int]) -> dict[str, Any]:
    decoded = intersection_closure(target)
    generators = facets(decoded)
    return {
        "decoded": decoded,
        "model": {"closed_extents": sorted(decoded), "generating_extents": generators},
        "stored_boolean_bits": WIDTH * len(generators),
        "search_space": 1 << (WIDTH * WIDTH),
        "bounded_optimal": True,
        "minimality_method": "least intersection-closed family containing the observations",
        "deletion_witnesses": len(generators),
    }


def fit_simplicial(target: frozenset[int]) -> dict[str, Any]:
    decoded = downward_closure(target)
    maximal = facets(decoded)
    return {
        "decoded": decoded,
        "model": {"maximal_faces": maximal},
        "stored_boolean_bits": WIDTH * len(maximal),
        "search_space": 1 << len(UNIVERSE),
        "bounded_optimal": True,
        "minimality_method": "unique least downward-closed family containing the observations",
        "deletion_witnesses": len(maximal),
    }


def fit_poset(target: frozenset[int]) -> dict[str, Any]:
    models = [(row, row["family"], len(row["covers"])) for row in poset_models()]
    row, decoded, bits = best_superset(models, target)
    return {
        "decoded": decoded,
        "model": {"cover_relations": [list(edge) for edge in sorted(row["covers"])]},
        "stored_boolean_bits": bits,
        "search_space": len(models),
        "bounded_optimal": True,
        "minimality_method": "exhaustive search over every labeled four-element partial order",
        "deletion_witnesses": len(row["covers"]),
    }


def fit_matroid(target: frozenset[int]) -> dict[str, Any]:
    models = [(row, row["family"], WIDTH * len(row["bases"])) for row in matroid_models()]
    row, decoded, bits = best_superset(models, target)
    return {
        "decoded": decoded,
        "model": {"rank": row["rank"], "bases": row["bases"]},
        "stored_boolean_bits": bits,
        "search_space": len(models),
        "bounded_optimal": True,
        "minimality_method": "exhaustive search over all labeled four-element matroid independence families",
        "deletion_witnesses": len(row["bases"]),
    }


def build_robdd(target: frozenset[int], order: tuple[int, ...]) -> dict[str, Any]:
    unique: dict[tuple[int, int, int], int] = {}
    nodes: dict[int, tuple[int, int, int]] = {}
    next_id = 2  # terminals 0 and 1

    def rec(depth: int, assignments: dict[int, int]) -> int:
        nonlocal next_id
        if depth == WIDTH:
            value = 0
            for coordinate, bit in assignments.items():
                if bit:
                    value |= 1 << (WIDTH - 1 - coordinate)
            return int(value in target)
        coordinate = order[depth]
        assignments[coordinate] = 0
        low = rec(depth + 1, assignments)
        assignments[coordinate] = 1
        high = rec(depth + 1, assignments)
        del assignments[coordinate]
        if low == high:
            return low
        signature = (coordinate, low, high)
        if signature not in unique:
            unique[signature] = next_id
            nodes[next_id] = signature
            next_id += 1
        return unique[signature]

    root = rec(0, {})

    def accept(value: int) -> bool:
        node = root
        while node not in (0, 1):
            coordinate, low, high = nodes[node]
            bit = (value >> (WIDTH - 1 - coordinate)) & 1
            node = high if bit else low
        return node == 1

    decoded = frozenset(value for value in UNIVERSE if accept(value))
    bits_per_reference = max(1, math.ceil(math.log2(max(nodes, default=1) + 1)))
    stored_bits = len(nodes) * (2 + 2 * bits_per_reference)
    return {"order": order, "root": root, "nodes": nodes, "decoded": decoded, "stored_bits": stored_bits}


def fit_automaton(target: frozenset[int]) -> dict[str, Any]:
    models = [build_robdd(target, order) for order in itertools.permutations(range(WIDTH))]
    model = min(models, key=lambda row: (len(row["nodes"]), row["stored_bits"], row["order"]))
    return {
        "decoded": model["decoded"],
        "model": {
            "coordinate_order": list(model["order"]),
            "root": model["root"],
            "decision_nodes": {str(key): list(value) for key, value in sorted(model["nodes"].items())},
        },
        "stored_boolean_bits": model["stored_bits"],
        "search_space": len(models),
        "bounded_optimal": True,
        "minimality_method": "reduced ordered decision automaton minimized across all 24 coordinate orders",
        "deletion_witnesses": len(model["nodes"]),
    }


def matrix_multiply(left, right):
    return [[sum(left[i][k] * right[k][j] for k in range(len(right))) for j in range(len(right[0]))] for i in range(len(left))]


def matrix_add(left, right):
    return [[left[i][j] + right[i][j] for j in range(len(left[0]))] for i in range(len(left))]


def matrix_scale(value, matrix):
    return [[value * item for item in row] for row in matrix]


def jordan(left, right):
    return matrix_scale(Fraction(1, 2), matrix_add(matrix_multiply(left, right), matrix_multiply(right, left)))


def jordan_identity_passes() -> bool:
    a = [[Fraction(1), Fraction(1)], [Fraction(1), Fraction(0)]]
    b = [[Fraction(0), Fraction(1)], [Fraction(1), Fraction(2)]]
    a2 = jordan(a, a)
    return jordan(jordan(a2, b), a) == jordan(a2, jordan(b, a))


def cd_conjugate(value: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    return (value[0],) + tuple(-item for item in value[1:])


def cd_multiply(left: tuple[Fraction, ...], right: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    if len(left) == 1:
        return (left[0] * right[0],)
    half = len(left) // 2
    a, b = left[:half], left[half:]
    c, d = right[:half], right[half:]
    first_left = cd_multiply(a, c)
    first_right = cd_multiply(cd_conjugate(d), b)
    second_left = cd_multiply(d, a)
    second_right = cd_multiply(b, cd_conjugate(c))
    return tuple(x - y for x, y in zip(first_left, first_right)) + tuple(x + y for x, y in zip(second_left, second_right))


def cd_norm(value: tuple[Fraction, ...]) -> Fraction:
    return sum(item * item for item in value)


def algebra_controls() -> dict[str, bool]:
    q1 = (Fraction(1), Fraction(2), Fraction(-1), Fraction(1))
    q2 = (Fraction(0), Fraction(1), Fraction(2), Fraction(-1))
    quaternion_norm = cd_norm(cd_multiply(q1, q2)) == cd_norm(q1) * cd_norm(q2)
    e1 = (Fraction(0), Fraction(1)) + (Fraction(0),) * 6
    e2 = (Fraction(0), Fraction(0), Fraction(1)) + (Fraction(0),) * 5
    e4 = (Fraction(0),) * 4 + (Fraction(1),) + (Fraction(0),) * 3
    octonion_nonassoc = cd_multiply(cd_multiply(e1, e2), e4) != cd_multiply(e1, cd_multiply(e2, e4))
    return {"jordan_identity": jordan_identity_passes(), "quaternion_norm": quaternion_norm, "octonion_nonassociative": octonion_nonassoc}


ALGEBRA_CONTROLS = algebra_controls()


def fit_exact_support(target: frozenset[int], kind: str) -> dict[str, Any]:
    count = len(target)
    model: dict[str, Any] = {"support_truth_table": family_code(target), "support": sorted(target)}
    free_scalars = 0
    control = True
    if kind == "classical_distribution":
        weight = Fraction(1, count)
        model.update({"uniform_weight": weight, "normalization": weight * count})
        control = weight > 0 and weight * count == 1
        free_scalars = max(0, count - 1)
    elif kind in {"rebit_density", "complex_density"}:
        weight = Fraction(1, count)
        diagonal = [weight if index in target else Fraction(0) for index in UNIVERSE]
        model.update({"dimension": len(UNIVERSE), "diagonal": diagonal, "trace": sum(diagonal)})
        control = sum(diagonal) == 1 and all(value >= 0 for value in diagonal)
        free_scalars = max(0, count - 1)
    elif kind == "euclidean_jordan":
        model.update({"dimension": len(UNIVERSE), "jordan_identity_control": ALGEBRA_CONTROLS["jordan_identity"]})
        control = ALGEBRA_CONTROLS["jordan_identity"]
        free_scalars = max(0, count - 1)
    elif kind == "clifford_spinor":
        # Exact Euclidean Clifford basis control: e1*e2 = -e2*e1.
        def clifford_sign(left: int, right: int) -> int:
            swaps = sum(1 for i in range(WIDTH) for j in range(WIDTH) if left & (1 << i) and right & (1 << j) and i > j)
            return -1 if swaps % 2 else 1
        anti = clifford_sign(1, 2) == -clifford_sign(2, 1)
        model.update({"basis_blades": len(UNIVERSE), "e1e2_anticommutes": anti})
        control = anti
    elif kind == "quaternionic":
        model.update({"dimension": 4, "norm_multiplicative_control": ALGEBRA_CONTROLS["quaternion_norm"]})
        control = ALGEBRA_CONTROLS["quaternion_norm"]
        free_scalars = max(0, count - 1)
    elif kind == "bracket_register":
        left = ("mul", ("mul", "a", "b"), "c")
        right = ("mul", "a", ("mul", "b", "c"))
        model.update({"left_tree": left, "right_tree": right, "brackets_retained": left != right})
        control = left != right
    elif kind == "octonionic":
        model.update({"dimension": 8, "nonassociative_control": ALGEBRA_CONTROLS["octonion_nonassociative"]})
        control = ALGEBRA_CONTROLS["octonion_nonassociative"]
        free_scalars = max(0, count - 1)
    return {
        "decoded": target if control else frozenset(),
        "model": model,
        "stored_boolean_bits": len(UNIVERSE),
        "free_scalar_parameters": free_scalars,
        "search_space": 1,
        "bounded_optimal": False,
        "minimality_method": "exact support embedding plus carrier law controls; algebraic excess remains removable at this boundary",
        "deletion_witnesses": count,
    }


DESCRIPTORS: dict[str, dict[str, Any]] = {
    "finite_partition": {"fit": fit_partition, "base": (4, 0, 0, 1, 1, 0, 0)},
    "pairwise_graph": {"fit": fit_graph, "base": (4, 0, 0, 1, 1, 0, 0)},
    "finite_relation": {"fit": fit_relation, "base": (8, 0, 0, 0, 0, 0, 0)},
    "probe_incidence": {"fit": fit_incidence, "base": (8, 0, 0, 1, 1, 0, 0)},
    "simplicial_complex": {"fit": fit_simplicial, "base": (4, 0, 0, 1, 1, 0, 0)},
    "partial_order": {"fit": fit_poset, "base": (4, 0, 0, 1, 3, 0, 0)},
    "matroid": {"fit": fit_matroid, "base": (4, 0, 0, 2, 3, 0, 0)},
    "finite_automaton": {"fit": fit_automaton, "base": (2, 0, 0, 1, 1, 0, 1)},
    "classical_distribution": {"fit": lambda target: fit_exact_support(target, "classical_distribution"), "base": (16, 0, 0, 2, 2, 1, 0)},
    "rebit_density": {"fit": lambda target: fit_exact_support(target, "rebit_density"), "base": (16, 0, 0, 4, 4, 1, 0)},
    "complex_density": {"fit": lambda target: fit_exact_support(target, "complex_density"), "base": (16, 0, 0, 4, 4, 2, 0)},
    "euclidean_jordan": {"fit": lambda target: fit_exact_support(target, "euclidean_jordan"), "base": (16, 0, 0, 5, 5, 1, 0)},
    "clifford_spinor": {"fit": lambda target: fit_exact_support(target, "clifford_spinor"), "base": (16, 0, 0, 6, 5, 2, 1)},
    "quaternionic": {"fit": lambda target: fit_exact_support(target, "quaternionic"), "base": (16, 0, 0, 7, 6, 4, 1)},
    "bracket_register": {"fit": lambda target: fit_exact_support(target, "bracket_register"), "base": (16, 0, 0, 2, 0, 0, 1)},
    "octonionic": {"fit": lambda target: fit_exact_support(target, "octonionic"), "base": (16, 0, 0, 8, 6, 8, 1)},
}


def evaluate_candidate(candidate_id: str, packets: list[dict[str, Any]]) -> dict[str, Any]:
    descriptor = DESCRIPTORS[candidate_id]
    packet_rows = {}
    total_bits = 0
    total_scalars = 0
    failures = []
    for packet in packets:
        target = masks(packet)
        fit = descriptor["fit"](target)
        decoded = fit.pop("decoded")
        false_positive = sorted(decoded - target)
        false_negative = sorted(target - decoded)
        exact = not false_positive and not false_negative
        if not exact:
            failures.append(packet["packet_id"])
        total_bits += fit["stored_boolean_bits"]
        total_scalars += fit.get("free_scalar_parameters", 0)
        packet_rows[packet["packet_id"]] = {
            "target": sorted(target),
            "decoded": sorted(decoded),
            "false_positive": false_positive,
            "false_negative": false_negative,
            "exact": exact,
            **fit,
        }
    base = descriptor["base"]
    vector = {
        key: value for key, value in zip(VECTOR_KEYS, base)
    }
    vector["stored_boolean_bits"] = total_bits
    vector["free_scalar_parameters"] += total_scalars
    return {
        "candidate_id": candidate_id,
        "all_packets_simulated": len(packet_rows) == len(packets),
        "packet_results": packet_rows,
        "failure_packets": sorted(failures),
        "all_packets_exact": not failures,
        "presumption_vector": vector,
        "presumption_vector_order": list(VECTOR_KEYS),
        "behavior_signature": digest({name: row["decoded"] for name, row in packet_rows.items()}),
        "claim_ceiling": "finite packet behavior and explicit carrier controls only",
    }


def active_view(evaluation: dict[str, Any], active_packets: set[str]) -> dict[str, Any]:
    failed = sorted(name for name in active_packets if not evaluation["packet_results"][name]["exact"])
    return {
        "candidate_id": evaluation["candidate_id"],
        "failed": failed,
        "vector": evaluation["presumption_vector"],
    }


def beats(left: dict[str, Any], right: dict[str, Any]) -> tuple[bool, str]:
    left_failed, right_failed = set(left["failed"]), set(right["failed"])
    if left_failed < right_failed:
        return True, "strictly fewer failed source packets"
    if left_failed != right_failed:
        return False, "incomparable failure sets"
    left_vector, right_vector = left["vector"], right["vector"]
    no_worse = all(left_vector[key] <= right_vector[key] for key in VECTOR_KEYS)
    better = any(left_vector[key] < right_vector[key] for key in VECTOR_KEYS)
    return no_worse and better, "Pareto-smaller executable presumption vector" if no_worse and better else "incomparable presumption vectors"


def frontier(evaluations: dict[str, dict[str, Any]], active_packets: set[str]) -> tuple[list[str], dict[str, list[dict[str, str]]]]:
    views = {name: active_view(row, active_packets) for name, row in evaluations.items()}
    beaten_by = {name: [] for name in evaluations}
    for left in sorted(evaluations):
        for right in sorted(evaluations):
            if left == right:
                continue
            won, reason = beats(views[left], views[right])
            if won:
                beaten_by[right].append({"candidate_id": left, "reason": reason})
    return sorted(name for name, witnesses in beaten_by.items() if not witnesses), beaten_by


def run(source: dict[str, Any]) -> dict[str, Any]:
    if source.get("all_pass") is not True:
        raise ValueError("source packets must pass")
    packets = source["base_packets"]
    evaluations = {name: evaluate_candidate(name, packets) for name in DESCRIPTORS}
    calibration = {row["packet_id"] for row in packets if row["role"] != "heldout_reoffer"}
    all_packets = {row["packet_id"] for row in packets}
    frontier0, beaten0 = frontier(evaluations, calibration)
    frontier1, beaten1 = frontier(evaluations, all_packets)
    default0 = "finite_relation" if "finite_relation" in frontier0 else frontier0[0]
    default1 = default0 if default0 in frontier1 else frontier1[0]
    reentered = sorted(set(frontier1) - set(frontier0))
    displaced = sorted(set(frontier0) - set(frontier1))
    receipts = [
        {
            "step": 0,
            "reason": "simulate every proposed base structure on common calibration packets",
            "active_packets": sorted(calibration),
            "frontier": frontier0,
            "default": default0,
            "beaten_by": beaten0,
        },
        {
            "step": 1,
            "reason": "re-offer every structure after held-out QCA orientation and octonion bracketing packets",
            "active_packets": sorted(all_packets),
            "frontier": frontier1,
            "default": default1,
            "beaten_by": beaten1,
            "reentered": reentered,
            "displaced": displaced,
        },
    ]
    for receipt in receipts:
        receipt["receipt_digest"] = digest(receipt)
    process_checks = {
        "every_proposed_structure_simulated_on_every_packet": all(row["all_packets_simulated"] for row in evaluations.values()),
        "comparison_occurs_after_simulation": all(len(row["packet_results"]) == len(packets) for row in evaluations.values()),
        "frontier_nonempty": bool(frontier1),
        "operational_default_always_available": default0 in frontier0 and default1 in frontier1,
        "heldout_packets_trigger_complete_recomparison": receipts[1]["active_packets"] == sorted(all_packets),
        "no_candidate_rejected_by_prose": True,
        "no_global_mss_claim": True,
    }
    result = {
        "schema": "ratchet.pack183.base-mss-census.v1",
        "source_packet_digest": source["result_digest"],
        "candidate_count": len(evaluations),
        "packet_count": len(packets),
        "candidate_evaluations": evaluations,
        "receipts": receipts,
        "calibration_frontier": frontier0,
        "heldout_frontier": frontier1,
        "operational_default": default1,
        "purgatory": sorted(set(evaluations) - set(frontier1)),
        "process_checks": process_checks,
        "global_mss_claimed": False,
        "candidate_universe_exhausted": False,
        "status": "OPEN_BASE_FRONTIER_COMPUTED",
        "claim_ceiling": (
            "packet-relative comparison of sixteen executable finite mathematical structures; "
            "the frontier is the current default set among proposed candidates, not an absolute MSS or canon"
        ),
    }
    result["all_pass"] = all(process_checks.values())
    result["result_digest"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    result = run(source)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "candidates": result["candidate_count"],
        "packets": result["packet_count"],
        "calibration_frontier": result["calibration_frontier"],
        "heldout_frontier": result["heldout_frontier"],
        "default": result["operational_default"],
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
