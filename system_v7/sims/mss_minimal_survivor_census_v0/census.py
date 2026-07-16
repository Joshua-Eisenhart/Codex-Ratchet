#!/usr/bin/env python3
"""Exhaustive quotient-only MSS census for all binary operations on {0,1,2}."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Iterable


CARRIER_SIZE = 3
SMALL_QUOTIENT_SIZES = (2, 1)
PERMUTATIONS = tuple(itertools.permutations(range(CARRIER_SIZE)))


def decode_table(code: int, size: int) -> tuple[int, ...]:
    """Decode a row-major size-by-size table from a base-size integer."""
    cells = []
    for _ in range(size * size):
        cells.append(code % size)
        code //= size
    return tuple(cells)


def encode_table(table: tuple[int, ...], size: int) -> int:
    """Encode a row-major table as a base-size integer."""
    code = 0
    multiplier = 1
    for value in table:
        code += value * multiplier
        multiplier *= size
    return code


def product(table: tuple[int, ...], size: int, left: int, right: int) -> int:
    return table[left * size + right]


def has_n01(table: tuple[int, ...], size: int) -> bool:
    return any(
        product(table, size, left, right) != product(table, size, right, left)
        for left in range(size)
        for right in range(size)
    )


def translation_signature(table: tuple[int, ...], size: int, element: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return (
        tuple(product(table, size, element, x) for x in range(size)),
        tuple(product(table, size, x, element) for x in range(size)),
    )


def has_probe_distinguishability(table: tuple[int, ...], size: int) -> bool:
    return any(
        translation_signature(table, size, left) != translation_signature(table, size, right)
        for left in range(size)
        for right in range(left + 1, size)
    )


def is_survivor(table: tuple[int, ...], size: int) -> bool:
    return has_n01(table, size) and has_probe_distinguishability(table, size)


def associative_witness(table: tuple[int, ...], size: int) -> tuple[int, int, int] | None:
    for left, middle, right in itertools.product(range(size), repeat=3):
        lhs = product(table, size, product(table, size, left, middle), right)
        rhs = product(table, size, left, product(table, size, middle, right))
        if lhs != rhs:
            return (left, middle, right)
    return None


def canonical_code(table: tuple[int, ...]) -> int:
    """Return the least code over the six relabellings of the 3-carrier."""
    relabelled_codes = []
    for permutation in PERMUTATIONS:
        relabelled = [0] * (CARRIER_SIZE * CARRIER_SIZE)
        for left, right in itertools.product(range(CARRIER_SIZE), repeat=2):
            relabelled[permutation[left] * CARRIER_SIZE + permutation[right]] = permutation[
                product(table, CARRIER_SIZE, left, right)
            ]
        relabelled_codes.append(encode_table(tuple(relabelled), CARRIER_SIZE))
    return min(relabelled_codes)


def row_major(table: tuple[int, ...], size: int) -> list[list[int]]:
    return [list(table[row * size : (row + 1) * size]) for row in range(size)]


def surjections(source_size: int, target_size: int) -> Iterable[tuple[int, ...]]:
    for mapping in itertools.product(range(target_size), repeat=source_size):
        if len(set(mapping)) == target_size:
            yield mapping


def quotient_witnesses(source: tuple[int, ...]) -> list[dict[str, object]]:
    """Return every proper surviving quotient witness, ordered deterministically."""
    witnesses: list[dict[str, object]] = []
    for target_size in SMALL_QUOTIENT_SIZES:
        for mapping in surjections(CARRIER_SIZE, target_size):
            target: list[int | None] = [None] * (target_size * target_size)
            homomorphic = True
            for left, right in itertools.product(range(CARRIER_SIZE), repeat=2):
                target_index = mapping[left] * target_size + mapping[right]
                image_product = mapping[product(source, CARRIER_SIZE, left, right)]
                previous = target[target_index]
                if previous is not None and previous != image_product:
                    homomorphic = False
                    break
                target[target_index] = image_product
            if not homomorphic or any(value is None for value in target):
                continue
            completed_target = tuple(int(value) for value in target)
            if is_survivor(completed_target, target_size):
                witnesses.append(
                    {
                        "source_to_target_map": list(mapping),
                        "target_size": target_size,
                        "target_table_code": encode_table(completed_target, target_size),
                        "target_table": row_major(completed_target, target_size),
                    }
                )
    return witnesses


def iso_representatives(codes: Iterable[int]) -> list[int]:
    representatives: set[int] = set()
    for code in codes:
        representatives.add(canonical_code(decode_table(code, CARRIER_SIZE)))
    return sorted(representatives)


def build_result() -> dict[str, object]:
    total_tables = CARRIER_SIZE ** (CARRIER_SIZE * CARRIER_SIZE)
    n01_candidates: list[int] = []
    survivors: list[int] = []
    quotient_kill_witnesses: list[dict[str, object]] = []
    minima: list[int] = []

    for code in range(total_tables):
        table = decode_table(code, CARRIER_SIZE)
        if not has_n01(table, CARRIER_SIZE):
            if (code + 1) % 2000 == 0:
                print(f"progress: {code + 1}/{total_tables} tables")
            continue
        n01_candidates.append(code)
        if not has_probe_distinguishability(table, CARRIER_SIZE):
            if (code + 1) % 2000 == 0:
                print(f"progress: {code + 1}/{total_tables} tables")
            continue
        survivors.append(code)
        witnesses = quotient_witnesses(table)
        if witnesses:
            quotient_kill_witnesses.append(
                {
                    "source_table_code": code,
                    "source_table": row_major(table, CARRIER_SIZE),
                    "witnesses": witnesses,
                }
            )
        else:
            minima.append(code)
        if (code + 1) % 2000 == 0:
            print(f"progress: {code + 1}/{total_tables} tables")

    associative_minima: list[int] = []
    nonassociative_minima: list[dict[str, object]] = []
    for code in minima:
        table = decode_table(code, CARRIER_SIZE)
        witness = associative_witness(table, CARRIER_SIZE)
        if witness is None:
            associative_minima.append(code)
        else:
            left, middle, right = witness
            nonassociative_minima.append(
                {
                    "table_code": code,
                    "associator_witness": [left, middle, right],
                    "lhs": product(table, CARRIER_SIZE, product(table, CARRIER_SIZE, left, middle), right),
                    "rhs": product(table, CARRIER_SIZE, left, product(table, CARRIER_SIZE, middle, right)),
                }
            )

    minimum_representatives = iso_representatives(minima)
    associative_minimum_representatives = iso_representatives(associative_minima)
    nonassociative_minimum_representatives = iso_representatives(
        item["table_code"] for item in nonassociative_minima
    )
    minimum_records = []
    for code in minimum_representatives:
        table = decode_table(code, CARRIER_SIZE)
        witness = associative_witness(table, CARRIER_SIZE)
        record: dict[str, object] = {
            "table_code": code,
            "table": row_major(table, CARRIER_SIZE),
            "association_status": "associative" if witness is None else "witnessed_nonassociative",
        }
        if witness is not None:
            left, middle, right = witness
            record["associator_witness"] = {
                "triple": [left, middle, right],
                "lhs": product(table, CARRIER_SIZE, product(table, CARRIER_SIZE, left, middle), right),
                "rhs": product(table, CARRIER_SIZE, left, product(table, CARRIER_SIZE, middle, right)),
            }
        minimum_records.append(record)

    return {
        "schema": "mss_minimal_survivor_census_result_v1",
        "sim_id": "mss_minimal_survivor_census_v0",
        "classification": "classical_baseline",
        "promotion_allowed": False,
        "claim_ceiling": "finite_3_carrier_quotient_only_diagnostic",
        "carrier": [0, 1, 2],
        "enumeration": {
            "operation_tables": total_tables,
            "formula": "3^(3*3)",
            "table_encoding": "row-major base-3 integer, least-significant digit first",
            "isomorphism_action": "all 6 permutations of the 3-carrier",
        },
        "criteria": {
            "n01": "exists x,y with x*y != y*x",
            "probe_distinguishability": "exists a!=b with L_a!=L_b or R_a!=R_b",
            "minimality": "no witnessed proper surjective homomorphism to a surviving 2- or 1-carrier quotient",
            "refinement_open": "subquotient minimality",
            "association_boundary": "association-unspecified floor; nonassociativity requires a nonzero associator witness",
        },
        "counts": {
            "candidate_count_n01": len(n01_candidates),
            "survivor_count_n01_and_probe": len(survivors),
            "minimal_count_quotient_only": len(minima),
        },
        "kill_attribution": {
            "n01_rejected": total_tables - len(n01_candidates),
            "probe_rejected_after_n01": len(n01_candidates) - len(survivors),
            "quotient_killed_after_n01_and_probe": len(quotient_kill_witnesses),
            "minimal_retained": len(minima),
            "partition_check": {
                "lhs": total_tables,
                "rhs": (total_tables - len(n01_candidates))
                + (len(n01_candidates) - len(survivors))
                + len(quotient_kill_witnesses)
                + len(minima),
            },
        },
        "isomorphism_classes": {
            "candidate_n01": len(iso_representatives(n01_candidates)),
            "survivor_n01_and_probe": len(iso_representatives(survivors)),
            "minimal_quotient_only": len(minimum_representatives),
        },
        "incomparable_minima": {
            "all_pairwise_incomparable_under_proper_surviving_quotient": True,
            "proper_surviving_quotient_relations_among_minima": 0,
            "reason": "a minimum is retained exactly when it has no proper surviving 2- or 1-carrier quotient",
        },
        "associativity_split_among_minima": {
            "floor_label": "association_unspecified",
            "associative_raw_tables": len(associative_minima),
            "witnessed_nonassociative_raw_tables": len(nonassociative_minima),
            "associative_iso_classes": len(associative_minimum_representatives),
            "witnessed_nonassociative_iso_classes": len(nonassociative_minimum_representatives),
            "nonzero_associator_witnesses_by_raw_table": nonassociative_minima,
        },
        "minimum_iso_class_representatives": minimum_records,
        "quotient_kill_witnesses": quotient_kill_witnesses,
        "tool_manifest": {
            "python_standard_library": {
                "used": True,
                "reason": "bounded exact enumeration, isomorphism action, and witnessed quotient search",
            }
        },
        "tool_integration_depth": None,
        "blocked_consumers": [
            "subquotient_minimality",
            "unbounded_magma_claims",
            "general_MSS_theorem",
            "ratchet_promotion",
        ],
    }


def print_census_table(result: dict[str, object]) -> None:
    counts = result["counts"]
    kills = result["kill_attribution"]
    iso_classes = result["isomorphism_classes"]
    association = result["associativity_split_among_minima"]
    print("MSS MINIMAL-SURVIVOR CENSUS")
    print("metric                                  raw tables   iso classes")
    print(f"N01 candidates                           {counts['candidate_count_n01']:10d}   {iso_classes['candidate_n01']:11d}")
    print(f"N01 + probe survivors                    {counts['survivor_count_n01_and_probe']:10d}   {iso_classes['survivor_n01_and_probe']:11d}")
    print(f"quotient-only minima                     {counts['minimal_count_quotient_only']:10d}   {iso_classes['minimal_quotient_only']:11d}")
    print("kill attribution")
    print(f"  N01 rejected:                           {kills['n01_rejected']:10d}")
    print(f"  probe rejected after N01:               {kills['probe_rejected_after_n01']:10d}")
    print(f"  quotient killed after N01 + probe:      {kills['quotient_killed_after_n01_and_probe']:10d}")
    print("association split among quotient-only minima")
    print(f"  associative:                            {association['associative_raw_tables']:10d}   {association['associative_iso_classes']:11d}")
    print(f"  witnessed nonassociative:               {association['witnessed_nonassociative_raw_tables']:10d}   {association['witnessed_nonassociative_iso_classes']:11d}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("results_v1.json"),
        help="result JSON path (default: results_v1.json beside this script)",
    )
    args = parser.parse_args()
    result = build_result()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_census_table(result)


if __name__ == "__main__":
    main()
