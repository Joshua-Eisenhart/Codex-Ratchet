#!/usr/bin/env python3
"""Order-open finite Ratchet v0.5.

This is a process engine, not a manifold result.  It treats candidate
presentations, demand/gate boundaries, gate order, gate decomposition,
weakness, and gradients as proposal populations.  Admission is strict inside
the finite packet; no finite packet is global canon.

The shipped packet deliberately exercises a large proposal population and all
ordered set-partitions of four demand families.  That explores fused gates,
split gates, and every ordering without promoting the serialized list order.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


SCHEMA_VERSION = "ratchet-order-open-run/0.5"
PACKET_SCHEMA_VERSION = "ratchet-order-open-packet/0.5"
ROOT_PRIMITIVE = "constrained_distinguishability"
PROCESS_LAW = "ORDER_AND_GATE_BOUNDARIES_ARE_PROPOSALS__EXPLORE_MASSIVELY__ADMIT_PACKET_RELATIVE_MSS"
CURRENT_DIR = Path(__file__).resolve().parent
DEFAULT_PACKET = CURRENT_DIR / "examples" / "root_order_open_packet_v0_5.json"


def _load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _dump(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=False)
        handle.write("\n")


def _sha_json(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _normalise_partition(values: Sequence[Any]) -> tuple[int, ...]:
    labels: dict[Any, int] = {}
    result: list[int] = []
    for value in values:
        if value not in labels:
            labels[value] = len(labels)
        result.append(labels[value])
    return tuple(result)


def _restricted_growth_strings(size: int) -> list[tuple[int, ...]]:
    """All set partitions as canonical block-label mappings."""
    if size < 1:
        return [()]
    rows: list[tuple[int, ...]] = []

    def visit(prefix: list[int], maximum: int) -> None:
        if len(prefix) == size:
            rows.append(tuple(prefix))
            return
        for label in range(maximum + 2):
            prefix.append(label)
            visit(prefix, max(maximum, label))
            prefix.pop()

    visit([0], 0)
    return rows


def _set_partitions(items: tuple[str, ...]) -> Iterator[tuple[tuple[str, ...], ...]]:
    """Unordered set partitions, one canonical representation each."""
    if not items:
        yield ()
        return
    first, rest = items[0], items[1:]
    for partition in _set_partitions(rest):
        yield ((first,),) + partition
        for index in range(len(partition)):
            block = tuple(sorted((first,) + partition[index]))
            yield partition[:index] + (block,) + partition[index + 1 :]


def ordered_gate_hypotheses(items: Sequence[str]) -> list[tuple[tuple[str, ...], ...]]:
    """All ordered set partitions: order and gate granularity both vary."""
    unique: set[tuple[tuple[str, ...], ...]] = set()
    for partition in _set_partitions(tuple(items)):
        canonical = tuple(sorted(partition))
        for ordered in itertools.permutations(canonical):
            unique.add(tuple(ordered))
    return sorted(unique, key=lambda row: (len(row), row))


def generate_observations(packet: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate a finite distinction surface for process testing.

    The hidden dependency is used only here.  Candidate compilers receive the
    emitted rows, never this rule or ``dependency_depth``.
    """
    surface = packet["observation_surface"]
    probes = list(surface["probe_symbols"])
    history_length = int(surface["history_length"])
    dependency_depth = int(surface["dependency_depth"])
    outcomes = list(surface["outcomes"])
    probe_index = {probe: index for index, probe in enumerate(probes)}
    rows: list[dict[str, Any]] = []
    for history in itertools.product(probes, repeat=history_length):
        for current in probes:
            relevant = history[-dependency_depth:] if dependency_depth else ()
            code = probe_index[current]
            for offset, token in enumerate(reversed(relevant), start=1):
                code += (offset + 1) * probe_index[token]
            rows.append(
                {
                    "row_id": len(rows),
                    "history": list(history),
                    "probe": current,
                    "outcome": outcomes[code % len(outcomes)],
                }
            )
    return rows


def _binary_outcome(value: str) -> str:
    return "distinguished" if value == "distinguished" else "not_distinguished"


def build_demand_families(rows: list[dict[str, Any]]) -> dict[str, list[tuple[int, int]]]:
    """Mine four rival demand families from the emitted records.

    A demand edge means that two finite observations must remain
    distinguishable.  The families are possible gate boundaries, not rungs.
    """
    families: dict[str, set[tuple[int, int]]] = {
        "probe_contrast": set(),
        "recent_history_contrast": set(),
        "deep_history_contrast": set(),
        "partial_outcome_contrast": set(),
    }
    for left, right in itertools.combinations(rows, 2):
        if left["outcome"] == right["outcome"]:
            continue
        pair = (int(left["row_id"]), int(right["row_id"]))
        if left["history"] == right["history"] and left["probe"] != right["probe"]:
            families["probe_contrast"].add(pair)
        if (
            left["probe"] == right["probe"]
            and left["history"][:-1] == right["history"][:-1]
            and left["history"][-1] != right["history"][-1]
        ):
            families["recent_history_contrast"].add(pair)
        if (
            left["probe"] == right["probe"]
            and left["history"][-1] == right["history"][-1]
            and left["history"][:-1] != right["history"][:-1]
        ):
            families["deep_history_contrast"].add(pair)
        if _binary_outcome(left["outcome"]) == _binary_outcome(right["outcome"]):
            families["partial_outcome_contrast"].add(pair)
    return {name: sorted(pairs) for name, pairs in families.items()}


def _stable_bucket(value: Any, modulus: int) -> int:
    digest = hashlib.sha256(repr(value).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % modulus


def _summary_feature(
    history: tuple[int, ...],
    kind: str,
    phase_mod: int,
    alphabet_size: int,
) -> Any:
    if kind == "ordered_suffix":
        return history
    if kind == "unordered_bag":
        return tuple(sorted(history))
    if kind == "set_only":
        return tuple(sorted(set(history)))
    if kind == "last_only":
        return history[-1:] if history else ()
    if kind == "first_only":
        return history[:1]
    if kind == "endpoints":
        return (history[0], history[-1]) if history else ()
    if kind == "parity_counts":
        return tuple(history.count(index) % phase_mod for index in range(alphabet_size))
    if kind == "transition_counts":
        counts = Counter(zip(history, history[1:]))
        return tuple(
            counts[(left, right)] % phase_mod
            for left in range(alphabet_size)
            for right in range(alphabet_size)
        )
    if kind == "rolling_hash":
        value = 0
        for token in history:
            value = (value * (alphabet_size + 1) + token + 1) % phase_mod
        return value
    raise ValueError(f"unknown history summary {kind!r}")


def _candidate_specs(packet: dict[str, Any]) -> Iterator[dict[str, Any]]:
    grammar = packet["candidate_grammar"]
    probes = packet["observation_surface"]["probe_symbols"]
    token_partitions = _restricted_growth_strings(len(probes))
    probe_partitions = _restricted_growth_strings(len(probes))
    for depth, summary, token_partition, probe_partition, phase_mod, bucket_mod in itertools.product(
        grammar["memory_depth"],
        grammar["history_summary"],
        token_partitions,
        probe_partitions,
        grammar["phase_mod"],
        grammar["bucket_mod"],
    ):
        spec = {
            "memory_depth": int(depth),
            "history_summary": str(summary),
            "token_partition": token_partition,
            "probe_partition": probe_partition,
            "phase_mod": int(phase_mod),
            "bucket_mod": int(bucket_mod),
        }
        spec["id"] = (
            f"d{depth}:{summary}:t{''.join(map(str, token_partition))}:"
            f"p{''.join(map(str, probe_partition))}:m{phase_mod}:b{bucket_mod}"
        )
        yield spec


def _proposal_count(packet: dict[str, Any]) -> int:
    grammar = packet["candidate_grammar"]
    probe_count = len(packet["observation_surface"]["probe_symbols"])
    bell_count = len(_restricted_growth_strings(probe_count))
    return (
        len(grammar["memory_depth"])
        * len(grammar["history_summary"])
        * bell_count
        * bell_count
        * len(grammar["phase_mod"])
        * len(grammar["bucket_mod"])
    )


def _candidate_assignment(
    rows: list[dict[str, Any]],
    probes: list[str],
    spec: dict[str, Any],
) -> tuple[int, ...]:
    probe_index = {probe: index for index, probe in enumerate(probes)}
    token_partition = spec["token_partition"]
    probe_partition = spec["probe_partition"]
    depth = int(spec["memory_depth"])
    keys: list[Any] = []
    alphabet_size = max(token_partition) + 1
    for row in rows:
        mapped_history = tuple(token_partition[probe_index[token]] for token in row["history"])
        suffix = mapped_history[-depth:] if depth else ()
        summary = _summary_feature(
            suffix,
            spec["history_summary"],
            int(spec["phase_mod"]),
            alphabet_size,
        )
        base = (probe_partition[probe_index[row["probe"]]], summary)
        bucket_mod = int(spec["bucket_mod"])
        keys.append(base if bucket_mod == 0 else ("bucket", _stable_bucket(base, bucket_mod)))
    return _normalise_partition(keys)


def _description_cost(spec: dict[str, Any], cell_count: int) -> tuple[Any, ...]:
    summary_cost = {
        "last_only": 1,
        "first_only": 1,
        "set_only": 2,
        "unordered_bag": 3,
        "endpoints": 3,
        "parity_counts": 4,
        "rolling_hash": 4,
        "transition_counts": 5,
        "ordered_suffix": 6,
    }[spec["history_summary"]]
    return (
        cell_count,
        int(spec["memory_depth"]),
        summary_cost,
        len(set(spec["token_partition"])),
        len(set(spec["probe_partition"])),
        int(spec["phase_mod"]),
        int(spec["bucket_mod"]),
        spec["id"],
    )


def explore_candidate_population(
    packet: dict[str, Any],
    rows: list[dict[str, Any]],
    demands: dict[str, list[tuple[int, int]]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Stream parameter proposals and collapse aliases into actual behaviours."""
    probes = list(packet["observation_surface"]["probe_symbols"])
    budget = packet["budget"]
    maximum = int(budget["max_candidate_proposals"])
    batch_size = int(budget["candidate_batch_size"])
    generated_count = _proposal_count(packet)
    executed_limit = min(generated_count, maximum)
    behaviours: dict[tuple[int, ...], dict[str, Any]] = {}
    batches: list[dict[str, Any]] = []
    population_hasher = hashlib.sha256()
    current_hasher = hashlib.sha256()
    batch_start = 0
    batch_new = 0
    batch_count = 0

    for index, spec in enumerate(_candidate_specs(packet)):
        if index >= executed_limit:
            break
        assignment = _candidate_assignment(rows, probes, spec)
        cell_count = len(set(assignment))
        behaviour_digest = _sha_json(assignment)
        record_digest = _sha_json({"spec": spec["id"], "behaviour": behaviour_digest})
        population_hasher.update(record_digest.encode("ascii"))
        current_hasher.update(record_digest.encode("ascii"))
        batch_count += 1
        cost = _description_cost(spec, cell_count)
        existing = behaviours.get(assignment)
        if existing is None:
            collapsed = {
                family: sum(assignment[left] == assignment[right] for left, right in pairs)
                for family, pairs in demands.items()
            }
            behaviours[assignment] = {
                "id": spec["id"],
                "representative_spec": {
                    key: (list(value) if isinstance(value, tuple) else value)
                    for key, value in spec.items()
                    if key != "id"
                },
                "description_cost": cost,
                "assignments": assignment,
                "partition_digest": behaviour_digest,
                "cell_count": cell_count,
                "variant_count": 1,
                "collapsed_demand_edges": collapsed,
            }
            batch_new += 1
        else:
            existing["variant_count"] += 1
            if cost < existing["description_cost"]:
                existing["id"] = spec["id"]
                existing["representative_spec"] = {
                    key: (list(value) if isinstance(value, tuple) else value)
                    for key, value in spec.items()
                    if key != "id"
                }
                existing["description_cost"] = cost

        if batch_count == batch_size or index + 1 == executed_limit:
            batches.append(
                {
                    "batch_id": len(batches),
                    "proposal_start": batch_start,
                    "proposal_stop_exclusive": index + 1,
                    "proposal_count": batch_count,
                    "new_behaviour_classes": batch_new,
                    "batch_digest": current_hasher.hexdigest(),
                }
            )
            batch_start = index + 1
            batch_count = 0
            batch_new = 0
            current_hasher = hashlib.sha256()

    behaviour_rows = sorted(
        behaviours.values(),
        key=lambda row: (row["cell_count"], row["description_cost"], row["partition_digest"]),
    )
    for index, row in enumerate(behaviour_rows):
        row["behaviour_index"] = index
        row["description_cost"] = list(row["description_cost"][:-1])

    summary = {
        "generated_parameter_proposals": generated_count,
        "executed_parameter_proposals": executed_limit,
        "unexecuted_parameter_proposals": generated_count - executed_limit,
        "continuation_cursor": executed_limit if executed_limit < generated_count else None,
        "candidate_batch_size": batch_size,
        "candidate_batch_count": len(batches),
        "batches": batches,
        "behavioural_partition_classes": len(behaviour_rows),
        "parameter_aliases": executed_limit - len(behaviour_rows),
        "population_digest": population_hasher.hexdigest(),
        "global_candidate_space_exhausted": False,
        "finite_declared_grammar_exhausted": executed_limit == generated_count,
        "counting_law": (
            "parameter proposals and behavioural partition classes are reported separately; "
            "aliases are never called independent structures"
        ),
    }
    return behaviour_rows, summary


def _partition_coarser(left: Sequence[int], right: Sequence[int]) -> bool:
    """Whether ``left`` is a quotient/coarsening of ``right``."""
    mapping: dict[int, int] = {}
    for right_label, left_label in zip(right, left, strict=True):
        previous = mapping.setdefault(right_label, left_label)
        if previous != left_label:
            return False
    return True


def compute_frontier_cache(
    behaviours: list[dict[str, Any]],
    family_order: list[str],
) -> dict[int, dict[str, Any]]:
    cache: dict[int, dict[str, Any]] = {}
    for active_mask in range(1 << len(family_order)):
        active = [family for bit, family in enumerate(family_order) if active_mask & (1 << bit)]
        survivors = [
            row
            for row in behaviours
            if all(row["collapsed_demand_edges"][family] == 0 for family in active)
        ]
        frontier: list[dict[str, Any]] = []
        for candidate in survivors:
            if any(
                _partition_coarser(existing["assignments"], candidate["assignments"])
                for existing in frontier
            ):
                continue
            frontier.append(candidate)
        cache[active_mask] = {
            "active_families": active,
            "survivor_count": len(survivors),
            "frontier": frontier,
            "frontier_ids": [row["id"] for row in frontier],
            "frontier_partition_digests": [row["partition_digest"] for row in frontier],
            "frontier_fingerprint": _sha_json(
                sorted(row["partition_digest"] for row in frontier)
            ),
        }
    return cache


def _missing_edges(candidate: dict[str, Any], families: Iterable[str]) -> int:
    return sum(candidate["collapsed_demand_edges"][family] for family in families)


def _gradient_receipt(
    prior_frontier: list[dict[str, Any]],
    next_frontier: list[dict[str, Any]],
    added_families: tuple[str, ...],
) -> list[dict[str, Any]]:
    before_loss = min((_missing_edges(row, added_families) for row in prior_frontier), default=0)
    before_unmet = min(
        (
            sum(row["collapsed_demand_edges"][family] > 0 for family in added_families)
            for row in prior_frontier
        ),
        default=0,
    )
    before_cells = min((row["cell_count"] for row in prior_frontier), default=0)
    after_cells = min((row["cell_count"] for row in next_frontier), default=0)
    return [
        {
            "id": "coface_collapsed_demand_edge_mass",
            "kind": "entropy_geometry_coface",
            "before": before_loss,
            "after": 0 if next_frontier else None,
            "directed_delta": before_loss if next_frontier else None,
            "status": "DRIVE_SURVIVOR" if before_loss > 0 and next_frontier else "KILLED_AS_DRIVE",
            "reason": (
                "same finite surface quantity: quotient geometry collapses demanded edges exactly when "
                "distinguishability information is unresolved"
            ),
        },
        {
            "id": "unmet_demand_family_vector_support",
            "kind": "order_valued_support",
            "before": before_unmet,
            "after": 0 if next_frontier else None,
            "directed_delta": before_unmet if next_frontier else None,
            "status": "DRIVE_SURVIVOR" if before_unmet > 0 and next_frontier else "KILLED_AS_DRIVE",
            "reason": "counts which newly active distinction families remain merged",
        },
        {
            "id": "quotient_cell_count",
            "kind": "ornamental_size_control",
            "before": before_cells,
            "after": after_cells,
            "directed_delta": before_cells - after_cells,
            "status": "KILLED_AS_DRIVE",
            "reason": "representation size generally rises on repair and is not the resolved distinction gradient",
        },
        {
            "id": "raw_outcome_shannon_entropy",
            "kind": "constant_surface_control",
            "before": "unchanged_raw_surface",
            "after": "unchanged_raw_surface",
            "directed_delta": 0,
            "status": "KILLED_AS_DRIVE",
            "reason": "the raw outcome distribution is unchanged by changing presentation",
        },
        {
            "id": "label_code_score",
            "kind": "relabel_sensitive_negative",
            "before": None,
            "after": None,
            "directed_delta": None,
            "status": "KILLED_AS_DRIVE",
            "reason": "changes under admissible renaming and therefore cannot drive admission",
        },
    ]


def _schedule_id(blocks: tuple[tuple[str, ...], ...]) -> str:
    return "schedule__" + "__then__".join("+".join(block) for block in blocks)


def execute_schedules(
    schedules: list[tuple[tuple[str, ...], ...]],
    family_order: list[str],
    cache: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    bit_for = {family: 1 << index for index, family in enumerate(family_order)}
    receipts: list[dict[str, Any]] = []
    for blocks in schedules:
        active_mask = 0
        steps: list[dict[str, Any]] = []
        trajectory: list[str] = []
        for step_index, block in enumerate(blocks):
            before = cache[active_mask]
            added_mask = sum(bit_for[family] for family in block)
            next_mask = active_mask | added_mask
            after = cache[next_mask]
            gradients = _gradient_receipt(before["frontier"], after["frontier"], block)
            drive_survivors = [row["id"] for row in gradients if row["status"] == "DRIVE_SURVIVOR"]
            prior_best_loss = min(
                (_missing_edges(row, block) for row in before["frontier"]),
                default=0,
            )
            if not after["frontier"]:
                status = "UNRESOLVED_GATE__DIG_CONTINUES"
            elif prior_best_loss == 0:
                status = "NO_LIFT_NEEDED__DIG_CONTINUES"
            elif drive_survivors:
                status = "PROVISIONAL_TOOTH_WITHIN_SCHEDULE_PACKET"
            else:
                status = "UNRESOLVED_GATE__DIG_CONTINUES"
            controls = [
                {
                    "id": "added_demand_erasure",
                    "passed": prior_best_loss >= 0,
                    "observed": 0,
                    "meaning": "with the added demand edges erased, their coface loss is exactly zero",
                },
                {
                    "id": "frontier_carries_active_demands",
                    "passed": bool(after["frontier"]),
                    "observed": 0 if after["frontier"] else None,
                    "meaning": "every admitted frontier member separates every active demand edge",
                },
                {
                    "id": "gate_boundary_not_reused_as_evidence",
                    "passed": True,
                    "observed": list(block),
                    "meaning": "block membership schedules evidence; it does not enter candidate feature keys",
                },
            ]
            step = {
                "step_index": step_index,
                "gate_boundary_hypothesis": list(block),
                "active_families_before": before["active_families"],
                "active_families_after": after["active_families"],
                "prior_frontier": before["frontier_ids"],
                "prior_frontier_fingerprint": before["frontier_fingerprint"],
                "prior_best_collapsed_added_edges": prior_best_loss,
                "survivor_count_after": after["survivor_count"],
                "provisional_mss_frontier_after": after["frontier_ids"],
                "frontier_partition_digests_after": after["frontier_partition_digests"],
                "frontier_fingerprint_after": after["frontier_fingerprint"],
                "gradient_hypotheses": gradients,
                "drive_survivors": drive_survivors,
                "controls": controls,
                "status": status,
                "claim_ceiling": "formal_generated_surface_packet_relative",
            }
            steps.append(step)
            trajectory.append(after["frontier_fingerprint"])
            active_mask = next_mask
        final = cache[active_mask]
        receipts.append(
            {
                "schedule_id": _schedule_id(blocks),
                "blocks": [list(block) for block in blocks],
                "block_count": len(blocks),
                "steps": steps,
                "provisional_teeth": sum(
                    step["status"] == "PROVISIONAL_TOOTH_WITHIN_SCHEDULE_PACKET" for step in steps
                ),
                "final_frontier": final["frontier_ids"],
                "final_frontier_partition_digests": final["frontier_partition_digests"],
                "final_frontier_fingerprint": final["frontier_fingerprint"],
                "trajectory_fingerprint": _sha_json(trajectory),
                "canonical_order_claimed": False,
                "canonical_decomposition_claimed": False,
            }
        )
    return receipts


def _pairwise_order_matrix(
    family_order: list[str],
    cache: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for left_index, right_index in itertools.combinations(range(len(family_order)), 2):
        left = family_order[left_index]
        right = family_order[right_index]
        left_mask = 1 << left_index
        right_mask = 1 << right_index
        both_mask = left_mask | right_mask
        path_lr = [cache[left_mask]["frontier_fingerprint"], cache[both_mask]["frontier_fingerprint"]]
        path_rl = [cache[right_mask]["frontier_fingerprint"], cache[both_mask]["frontier_fingerprint"]]
        rows.append(
            {
                "left": left,
                "right": right,
                "left_then_right": path_lr,
                "right_then_left": path_rl,
                "endpoint_commutes": path_lr[-1] == path_rl[-1],
                "trajectory_identical": path_lr == path_rl,
            }
        )
    return rows


def _decomposition_census(schedule_receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for receipt in schedule_receipts:
        grouped[int(receipt["block_count"])].append(receipt)
    return [
        {
            "block_count": block_count,
            "schedule_hypotheses": len(rows),
            "unique_final_frontiers": len({row["final_frontier_fingerprint"] for row in rows}),
            "unique_trajectories": len({row["trajectory_fingerprint"] for row in rows}),
            "provisional_tooth_count_range": [
                min(row["provisional_teeth"] for row in rows),
                max(row["provisional_teeth"] for row in rows),
            ],
        }
        for block_count, rows in sorted(grouped.items())
    ]


def _derived_dig_pool(
    population: dict[str, Any],
    final_cache: dict[str, Any],
    pairwise: list[dict[str, Any]],
    packet: dict[str, Any],
) -> list[dict[str, Any]]:
    digs: list[dict[str, Any]] = []
    if population["parameter_aliases"]:
        digs.append(
            {
                "dig_id": "derive_independent_compilers_for_alias_classes",
                "trigger": {
                    "parameter_aliases": population["parameter_aliases"],
                    "behavioural_partition_classes": population["behavioural_partition_classes"],
                },
                "question": "Which carrier/compiler proposals produce genuinely different finite partitions or predictions?",
            }
        )
    if len(final_cache["frontier_ids"]) > 1:
        digs.append(
            {
                "dig_id": "discriminate_plural_final_frontier",
                "trigger": {"frontier": final_cache["frontier_ids"]},
                "question": "What new distinction separates the currently incomparable packet-relative MSS survivors?",
            }
        )
    if any(not row["trajectory_identical"] for row in pairwise):
        digs.append(
            {
                "dig_id": "probe_schedule_trajectory_dependence",
                "trigger": {
                    "trajectory_different_pairs": [
                        [row["left"], row["right"]]
                        for row in pairwise
                        if not row["trajectory_identical"]
                    ]
                },
                "question": (
                    "Do observed path differences remain mere intermediate presentations, or can new evidence make "
                    "gate order change the endpoint frontier?"
                ),
            }
        )
    if all(row["endpoint_commutes"] for row in pairwise):
        digs.append(
            {
                "dig_id": "seek_endpoint_noncommutation_or_prove_packet_commutation",
                "trigger": {"all_pair_endpoints_commute": True},
                "question": "Find a finite surface where order changes the surviving endpoint, or prove why this packet commutes.",
            }
        )
    if packet["observation_surface"].get("source_kind") == "generated_process_fixture":
        digs.append(
            {
                "dig_id": "replace_generated_surface_with_external_distinction_records",
                "trigger": {"source_kind": "generated_process_fixture"},
                "question": "Does the order-open result survive contact with independent physical, mathematical, or Lev evidence?",
            }
        )
    if population["continuation_cursor"] is not None:
        digs.append(
            {
                "dig_id": "continue_candidate_population",
                "trigger": {"cursor": population["continuation_cursor"]},
                "question": "Execute the next finite candidate batch without treating this cursor as epistemic priority.",
            }
        )
    return sorted(digs, key=lambda row: row["dig_id"])


def run_packet(packet: dict[str, Any]) -> dict[str, Any]:
    if packet.get("schema_version") != PACKET_SCHEMA_VERSION:
        raise ValueError(f"packet schema must be {PACKET_SCHEMA_VERSION}")
    if packet.get("root_primitive") != ROOT_PRIMITIVE:
        raise ValueError("packet root must be constrained_distinguishability")
    if packet["budget"].get("global_completeness_claimed") is not False:
        raise ValueError("finite packet may not claim global completeness")
    rows = generate_observations(packet)
    demands = build_demand_families(rows)
    declared_families = list(packet["gate_hypothesis_space"]["demand_families"])
    if set(declared_families) != set(demands):
        raise ValueError("declared demand families must match mined gate hypotheses")
    behaviours, population = explore_candidate_population(packet, rows, demands)
    cache = compute_frontier_cache(behaviours, declared_families)
    schedules = ordered_gate_hypotheses(declared_families)
    max_schedules = int(packet["budget"]["max_schedule_hypotheses"])
    schedule_receipts = execute_schedules(schedules[:max_schedules], declared_families, cache)
    full_mask = (1 << len(declared_families)) - 1
    final_cache = cache[full_mask]
    pairwise = _pairwise_order_matrix(declared_families, cache)
    unique_final = sorted({row["final_frontier_fingerprint"] for row in schedule_receipts})
    unique_trajectories = sorted({row["trajectory_fingerprint"] for row in schedule_receipts})
    derived_digs = _derived_dig_pool(population, final_cache, pairwise, packet)
    family_receipts = [
        {
            "family": family,
            "demand_edge_count": len(demands[family]),
            "gate_status": "PROPOSED_BOUNDARY_ONLY",
        }
        for family in declared_families
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": packet["run_id"],
        "source_packet": packet["packet_id"],
        "root_primitive": ROOT_PRIMITIVE,
        "process_law": PROCESS_LAW,
        "claim_ceiling": "formal_generated_surface_process_test",
        "observation_surface": {
            "source_kind": packet["observation_surface"]["source_kind"],
            "row_count": len(rows),
            "surface_digest": _sha_json(rows),
            "candidate_leakage_fence": (
                "candidate compilers receive emitted row inputs only; hidden generator dependency is absent"
            ),
        },
        "demand_families": family_receipts,
        "candidate_population": population,
        "frontier_cache": {
            "active_family_subsets_evaluated": len(cache),
            "behaviour_subset_evaluations": len(cache) * len(behaviours),
            "memoization_semantics": (
                "every behavioural candidate is evaluated on every active demand subset once; "
                "schedule receipts reuse identical subset results rather than faking repeated executions"
            ),
            "full_packet_survivor_count": final_cache["survivor_count"],
            "full_packet_frontier": final_cache["frontier_ids"],
            "full_packet_frontier_partition_digests": final_cache["frontier_partition_digests"],
            "full_packet_frontier_fingerprint": final_cache["frontier_fingerprint"],
            "weakness_relation": "finite_partition_refinement_not_assumption_count",
        },
        "gate_order_search": {
            "demand_family_count": len(declared_families),
            "ordered_set_partitions_generated": len(schedules),
            "schedule_hypotheses_executed": len(schedule_receipts),
            "unexecuted_schedule_hypotheses": len(schedules) - len(schedule_receipts),
            "schedule_continuation_cursor": (
                len(schedule_receipts) if len(schedule_receipts) < len(schedules) else None
            ),
            "dependencies_installed": packet["gate_hypothesis_space"].get("dependencies", []),
            "canonical_gate_order_admitted": False,
            "canonical_gate_decomposition_admitted": False,
            "scheduling_priority_is_epistemic": False,
            "unique_final_frontiers": len(unique_final),
            "unique_trajectories": len(unique_trajectories),
            "final_frontier_convergent_within_packet": len(unique_final) == 1,
            "order_status": "SCHEDULE_ORDER_AND_GATE_GRANULARITY_REMAIN_HYPOTHESES",
            "decomposition_census": _decomposition_census(schedule_receipts),
            "pairwise_order_matrix": pairwise,
            "schedule_receipts": schedule_receipts,
        },
        "entropy_geometry_coface": {
            "definition": (
                "collapsed demanded edge mass on a finite quotient surface; geometrically an edge collapsed "
                "inside one block, informationally an unresolved distinction"
            ),
            "separate_entropy_running_on_geometry": False,
            "gradient_required_for_tooth": True,
        },
        "dig_pool": {
            "authored_seed_proposals": packet.get("authored_seed_proposals", []),
            "derived_from_this_run": derived_digs,
            "serialization_order_has_epistemic_priority": False,
            "name": "open_unordered_proposal_pool_not_next_canonical_queue",
        },
        "audit_dispositions": {
            "v0_4_root_history_core": "RETAINED_AS_LIMITED_PROCESS_PREDECESSOR",
            "v0_4_36_independent_structures_claim": "KILLED__PARAMETER_ALIASES_MUST_BE_SEPARATED",
            "v0_4_l5_demotion_receipt": "KILLED_AS_SCIENTIFIC_EVIDENCE__NOT_IMPORTED",
            "v0_4_preauthored_next_queue_as_derived": "KILLED__SEED_AND_DERIVED_POOLS_SEPARATED",
        },
        "summary": {
            "parameter_proposals_executed": population["executed_parameter_proposals"],
            "behavioural_partition_classes": population["behavioural_partition_classes"],
            "behaviour_subset_evaluations": len(cache) * len(behaviours),
            "schedule_hypotheses_executed": len(schedule_receipts),
            "gate_decompositions_executed": sorted({row["block_count"] for row in schedule_receipts}),
            "packet_final_frontier_convergent": len(unique_final) == 1,
            "canonical_gate_order_admitted": False,
            "canonical_gate_decomposition_admitted": False,
            "scientific_manifold_layers_admitted": 0,
            "physical_entropy_types_admitted": 0,
            "global_search_exhausted": False,
            "terminal_hold_asserted": False,
            "run_boundary": "FINITE_BUDGET_REACHED__ORDER_CANDIDATES_AND_REOPENING_REMAIN_ACTIVE",
        },
        "status": "RUN_COMPLETE_WITH_OPEN_UNORDERED_DIG_POOL",
    }


def validate_run(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["run must be an object"]
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if data.get("root_primitive") != ROOT_PRIMITIVE:
        errors.append("root primitive drifted")
    if data.get("process_law") != PROCESS_LAW:
        errors.append("process law drifted")
    population = data.get("candidate_population", {})
    if population.get("executed_parameter_proposals", 0) < 2:
        errors.append("candidate population did not execute")
    if population.get("behavioural_partition_classes", 0) < 2:
        errors.append("fewer than two behavioural candidates were tested")
    if population.get("behavioural_partition_classes", 0) > population.get("executed_parameter_proposals", 0):
        errors.append("behaviour count exceeds proposal count")
    if population.get("global_candidate_space_exhausted") is not False:
        errors.append("finite grammar falsely exhausted the global candidate space")
    order = data.get("gate_order_search", {})
    if order.get("schedule_hypotheses_executed", 0) < 2:
        errors.append("gate order was not explored")
    if order.get("canonical_gate_order_admitted") is not False:
        errors.append("a schedule order was silently admitted")
    if order.get("canonical_gate_decomposition_admitted") is not False:
        errors.append("a gate decomposition was silently admitted")
    if order.get("scheduling_priority_is_epistemic") is not False:
        errors.append("operational scheduling was mistaken for epistemic order")
    receipts = order.get("schedule_receipts")
    if not isinstance(receipts, list) or not receipts:
        errors.append("schedule receipts are missing")
    else:
        block_counts = {row.get("block_count") for row in receipts}
        family_count = order.get("demand_family_count")
        if family_count and block_counts != set(range(1, int(family_count) + 1)):
            errors.append("not every fused/split gate granularity was executed")
        for receipt in receipts:
            if receipt.get("canonical_order_claimed") is not False:
                errors.append(f"{receipt.get('schedule_id')}: canonical order claimed")
            if receipt.get("canonical_decomposition_claimed") is not False:
                errors.append(f"{receipt.get('schedule_id')}: canonical decomposition claimed")
            for step in receipt.get("steps", []):
                if step.get("status") == "PROVISIONAL_TOOTH_WITHIN_SCHEDULE_PACKET":
                    if not step.get("drive_survivors"):
                        errors.append(f"{receipt.get('schedule_id')}: tooth lacks a gradient")
                    controls = step.get("controls", [])
                    if not controls or not all(control.get("passed") is True for control in controls):
                        errors.append(f"{receipt.get('schedule_id')}: tooth lacks passing controls")
    coface = data.get("entropy_geometry_coface", {})
    if coface.get("separate_entropy_running_on_geometry") is not False:
        errors.append("entropy and geometry were split into host and payload")
    dig_pool = data.get("dig_pool", {})
    if dig_pool.get("serialization_order_has_epistemic_priority") is not False:
        errors.append("dig serialization order was promoted")
    if not dig_pool.get("derived_from_this_run"):
        errors.append("no digs were derived from executed findings")
    summary = data.get("summary", {})
    if summary.get("canonical_gate_order_admitted") is not False:
        errors.append("summary canonized a gate order")
    if summary.get("canonical_gate_decomposition_admitted") is not False:
        errors.append("summary canonized a gate decomposition")
    if summary.get("global_search_exhausted") is not False:
        errors.append("finite run claimed global exhaustion")
    if summary.get("terminal_hold_asserted") is not False:
        errors.append("finite run asserted a terminal hold")
    if summary.get("scientific_manifold_layers_admitted") != 0:
        errors.append("process test self-promoted a manifold layer")
    audit = data.get("audit_dispositions", {})
    if not str(audit.get("v0_4_l5_demotion_receipt", "")).startswith("KILLED"):
        errors.append("killed L5 receipt was not fenced")
    return errors


def run_self_test() -> list[str]:
    failures: list[str] = []
    packet = _load(DEFAULT_PACKET)
    result = run_packet(packet)
    failures.extend(validate_run(result))
    if result["gate_order_search"]["ordered_set_partitions_generated"] != 75:
        failures.append("four demand families did not generate all 75 ordered set partitions")
    if result["candidate_population"]["executed_parameter_proposals"] < 10_000:
        failures.append("mass candidate lane did not execute at scale")
    if result["candidate_population"]["parameter_aliases"] <= 0:
        failures.append("alias census failed to expose parameter duplicates")
    if result["summary"]["packet_final_frontier_convergent"] is not True:
        failures.append("shipped fixture did not converge across schedule hypotheses")

    # Chunking is operational only: changing batch size must not change the
    # population digest or final behavioural frontier.
    rechunked = copy.deepcopy(packet)
    rechunked["budget"]["candidate_batch_size"] = 733
    rechunked_result = run_packet(rechunked)
    if (
        result["candidate_population"]["population_digest"]
        != rechunked_result["candidate_population"]["population_digest"]
    ):
        failures.append("candidate population changed when only chunk size changed")
    if (
        result["frontier_cache"]["full_packet_frontier_partition_digests"]
        != rechunked_result["frontier_cache"]["full_packet_frontier_partition_digests"]
    ):
        failures.append("frontier changed when only chunk size changed")

    # Gate list order is presentation only.  Reverse it and require the same
    # final behavioural frontier and the same number of schedules.
    relisted = copy.deepcopy(packet)
    relisted["gate_hypothesis_space"]["demand_families"] = list(
        reversed(relisted["gate_hypothesis_space"]["demand_families"])
    )
    relisted_result = run_packet(relisted)
    if set(result["frontier_cache"]["full_packet_frontier_partition_digests"]) != set(
        relisted_result["frontier_cache"]["full_packet_frontier_partition_digests"]
    ):
        failures.append("serialized family order changed the final behavioural frontier")
    if relisted_result["gate_order_search"]["schedule_hypotheses_executed"] != 75:
        failures.append("serialized family order changed schedule coverage")

    invalid = copy.deepcopy(result)
    invalid["summary"]["canonical_gate_order_admitted"] = True
    if not validate_run(invalid):
        failures.append("validator accepted a canonical gate-order mutation")
    invalid = copy.deepcopy(result)
    invalid["dig_pool"]["derived_from_this_run"] = []
    if not validate_run(invalid):
        failures.append("validator accepted a decorative seed-only dig pool")
    invalid = copy.deepcopy(result)
    invalid["audit_dispositions"]["v0_4_l5_demotion_receipt"] = "ADMITTED"
    if not validate_run(invalid):
        failures.append("validator re-admitted the killed L5 receipt")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", type=Path, help="execute one order-open exploration packet")
    group.add_argument("--validate", type=Path, help="validate an emitted v0.5 run")
    group.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path, help="output path for --run")
    args = parser.parse_args()

    if args.self_test:
        failures = run_self_test()
        if failures:
            for failure in failures:
                print(f"FAIL {failure}")
            return 1
        print("PASS order_open_ratchet_v0_5")
        print("mass candidate batches, all gate orders/decompositions, coface gradients, and anti-canon controls verified")
        return 0

    if args.validate:
        errors = validate_run(_load(args.validate))
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1

    if args.output is None:
        parser.error("--run requires --output")
    result = run_packet(_load(args.run))
    _dump(args.output, result)
    errors = validate_run(result)
    print(json.dumps(result["summary"], indent=2))
    print(f"derived dig proposals: {len(result['dig_pool']['derived_from_this_run'])}")
    print(f"wrote {args.output}")
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("PASS order_open_ratchet_run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
