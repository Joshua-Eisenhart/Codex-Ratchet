from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def normalize_partition(signatures: Iterable[tuple[object, ...]]) -> tuple[int, ...]:
    labels: dict[tuple[object, ...], int] = {}
    result = []
    for signature in signatures:
        labels.setdefault(signature, len(labels))
        result.append(labels[signature])
    return tuple(result)


def refines(fine: tuple[int, ...], coarse: tuple[int, ...]) -> bool:
    if len(fine) != len(coarse):
        return False
    mapping: dict[int, int] = {}
    for fine_label, coarse_label in zip(fine, coarse, strict=True):
        prior = mapping.setdefault(fine_label, coarse_label)
        if prior != coarse_label:
            return False
    return True


def _is_prefix(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    return len(left) <= len(right) and right[: len(left)] == left


@dataclass(frozen=True)
class ObservationBundle:
    presentations: tuple[str, ...]
    probe_ids: tuple[str, ...]
    outcomes: tuple[tuple[int, ...], ...]
    probe_contract_sha256: str
    bundle_sha256: str

    @classmethod
    def build(
        cls,
        presentations: tuple[str, ...],
        probe_ids: tuple[str, ...],
        outcomes: tuple[tuple[int, ...], ...],
    ) -> "ObservationBundle":
        if not presentations or not probe_ids:
            raise ValueError("presentations and probes must be nonempty")
        if len(outcomes) != len(presentations):
            raise ValueError("one outcome row is required per presentation")
        if any(len(row) != len(probe_ids) for row in outcomes):
            raise ValueError("every outcome row must cover the frozen probe contract")
        probe_hash = _digest({"probe_ids": probe_ids})
        bundle_hash = _digest(
            {
                "presentations": presentations,
                "probe_ids": probe_ids,
                "outcomes": outcomes,
                "probe_contract_sha256": probe_hash,
            }
        )
        return cls(presentations, probe_ids, outcomes, probe_hash, bundle_hash)


@dataclass(frozen=True)
class RatchetCandidate:
    candidate_id: str
    bundle_sha256: str
    probe_contract_sha256: str
    chain_id: str | None
    selected_probe_ids: tuple[str, ...]
    partition: tuple[int, ...]
    partition_sha256: str
    nesting_witness_sha256: str | None


def derive_candidate(
    bundle: ObservationBundle,
    candidate_id: str,
    selected_probe_ids: tuple[str, ...],
    *,
    chain_id: str | None,
    nesting_witness_sha256: str | None,
) -> RatchetCandidate:
    if not selected_probe_ids:
        raise ValueError("candidate needs a nonempty probe subfamily")
    index = {probe_id: i for i, probe_id in enumerate(bundle.probe_ids)}
    if any(probe_id not in index for probe_id in selected_probe_ids):
        raise ValueError("candidate requested a probe outside the frozen contract")
    signatures = tuple(
        tuple(row[index[probe_id]] for probe_id in selected_probe_ids)
        for row in bundle.outcomes
    )
    partition = normalize_partition(signatures)
    return RatchetCandidate(
        candidate_id,
        bundle.bundle_sha256,
        bundle.probe_contract_sha256,
        chain_id,
        selected_probe_ids,
        partition,
        _digest(partition),
        nesting_witness_sha256,
    )


@dataclass(frozen=True)
class RatchetResult:
    verdict: str
    hold_reason: str | None
    survivors: tuple[str, ...]
    frontier: tuple[str, ...]
    uncompared_live: tuple[str, ...]
    equivalent_groups: tuple[tuple[str, ...], ...]
    collapsed_demand_edges: dict[str, tuple[tuple[int, int], ...]]
    absolute_mss_claimed: bool = False
    winner: None = None
    promotion_allowed: bool = False


def ratchet_frontier(
    candidates: tuple[RatchetCandidate, ...],
    demand_edges: tuple[tuple[int, int], ...],
) -> RatchetResult:
    if not demand_edges:
        return RatchetResult("HOLD", "EMPTY_DEMAND", (), (), (), (), {})
    if not candidates:
        return RatchetResult("HOLD", "NO_CANDIDATE", (), (), (), (), {})
    contracts = {(c.bundle_sha256, c.probe_contract_sha256) for c in candidates}
    if len(contracts) != 1:
        return RatchetResult("HOLD", "CONTRACT_MISMATCH", (), (), (), (), {})

    size = len(candidates[0].partition)
    for left, right in demand_edges:
        if left == right or not (0 <= left < size and 0 <= right < size):
            return RatchetResult(
                "HOLD", "INVALID_DEMAND_EDGE", (), (), (), (), {}
            )

    collapsed: dict[str, tuple[tuple[int, int], ...]] = {}
    live: list[RatchetCandidate] = []
    for candidate in candidates:
        failed = tuple(
            edge
            for edge in demand_edges
            if candidate.partition[edge[0]] == candidate.partition[edge[1]]
        )
        collapsed[candidate.candidate_id] = failed
        if not failed:
            live.append(candidate)
    if not live:
        return RatchetResult(
            "HOLD", "NO_SURVIVOR", (), (), (), (), collapsed
        )

    by_partition: dict[tuple[int, ...], list[str]] = {}
    for candidate in live:
        by_partition.setdefault(candidate.partition, []).append(candidate.candidate_id)
    equivalent = tuple(
        tuple(ids) for ids in by_partition.values() if len(ids) > 1
    )

    comparable: set[str] = set()
    dominated: set[str] = set()
    for i, left in enumerate(live):
        for right in live[i + 1 :]:
            valid_nest = (
                left.chain_id is not None
                and left.chain_id == right.chain_id
                and left.nesting_witness_sha256 is not None
                and left.nesting_witness_sha256 == right.nesting_witness_sha256
                and (
                    _is_prefix(left.selected_probe_ids, right.selected_probe_ids)
                    or _is_prefix(right.selected_probe_ids, left.selected_probe_ids)
                )
            )
            if not valid_nest:
                continue
            left_finer = refines(left.partition, right.partition)
            right_finer = refines(right.partition, left.partition)
            if not (left_finer or right_finer):
                continue
            comparable.update((left.candidate_id, right.candidate_id))
            if left_finer and not right_finer:
                dominated.add(left.candidate_id)
            elif right_finer and not left_finer:
                dominated.add(right.candidate_id)

    frontier = tuple(
        candidate.candidate_id
        for candidate in live
        if candidate.candidate_id in comparable
        and candidate.candidate_id not in dominated
    )
    uncompared = tuple(
        candidate.candidate_id
        for candidate in live
        if candidate.candidate_id not in comparable
    )
    if not frontier:
        return RatchetResult(
            "HOLD",
            "NO_COMPARABLE_NEST",
            tuple(candidate.candidate_id for candidate in live),
            (),
            uncompared,
            equivalent,
            collapsed,
        )
    return RatchetResult(
        "PACKET_RELATIVE_FRONTIER",
        None,
        tuple(candidate.candidate_id for candidate in live),
        frontier,
        uncompared,
        equivalent,
        collapsed,
    )


def continuation_congruent(
    partition: tuple[int, ...], transition: tuple[int, ...]
) -> tuple[bool, tuple[int, int] | None]:
    if len(partition) != len(transition):
        raise ValueError("transition and partition sizes differ")
    if any(index < 0 or index >= len(partition) for index in transition):
        raise ValueError("transition leaves finite carrier")
    for left in range(len(partition)):
        for right in range(left + 1, len(partition)):
            if partition[left] != partition[right]:
                continue
            if partition[transition[left]] != partition[transition[right]]:
                return False, (left, right)
    return True, None
