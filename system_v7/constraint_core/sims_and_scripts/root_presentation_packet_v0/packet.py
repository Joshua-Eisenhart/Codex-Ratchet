#!/usr/bin/env python3
"""Root-presentation packet v0.3 — schema migration (2026-07-10).

Migration note: this is the ratchet-run/0.2 -> ratchet-run/0.3 migration plus
the four specification-required gradient controls.  The packet mathematics,
candidate population, weakening structure, and harden-round findings are
unchanged.  The harden budget remains exhausted.  See
``graveyard/AUDIT_FINDINGS_v0_20260710.md`` for the preserved findings lineage.

The sole ground truth remains one seed-0 immutable tuple stream.  G1, G2, G2P,
G3, and G4 independently ingest that stream on the honest path.  This packet is
frozen after verification for final fresh audit; unresolved attacks remain open.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import random
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


HERE = Path(__file__).resolve().parent
BUNDLE_ROOT = HERE.parents[1]
sys.path.insert(0, str(BUNDLE_ROOT))

from ratchet.ratchet_kernel import validate_receipt  # noqa: E402


SEED = 0
VERDICTS = ("distinguished", "not_distinguished", "unresolved", "inadmissible")
P_BASE = 0
P_OPEN = 1
P_LOCK = 2
P_OPEN_LOCK = 3
P_LOCK_OPEN = 4
P_HELD = 5
PREFIXES = (P_BASE, P_OPEN, P_LOCK, P_OPEN_LOCK, P_LOCK_OPEN, P_HELD)
PROBES = (0, 1)
MARKS = (0, 1, 2, 3)
O = (0, 0, 1)
N = (1, 1, 2)
L1 = (0, 2, 3)
L2 = (1, 0, 1)
I0 = (1, 3, 0)
CANDIDATE_IDS = ("G1", "G2", "G2P", "G3", "G4")
A0_RELEVANT_ATTEMPTS = (N, L1, L2)
GRADIENT_EPSILON = 0.0
LOCAL_WEAKENINGS = (
    "forget-transitivity",
    "forget-symmetry",
    "forget-totality",
    "forget-incidence",
    "forget-probe-context",
    "restrict-history",
    "erase-labels",
)
INSTALLED_WEAKENINGS = (
    "erase_primitive",
    "forget_structure",
    "quotient_marks",
    "restrict_operations",
    "reduce_history",
    "coarsen_resolution",
    "reduce_locality",
    "carrier_substitution",
    "algebra_restriction",
    "remove_equivalence_closure",
    "remove_independent_entropy_geometry_fields",
)
Record = tuple[int, int, int, int, str]
Stream = tuple[Record, ...]
CandidateLookup = Callable[[dict[str, Any], int, tuple[int, int, int]], str]


@dataclass(frozen=True)
class DistinctionPotentialSpec:
    """Frozen finite type for V_{t,O}; no continuum or named entropy is used."""

    functional: str
    domain: str
    codomain: str
    orientation: str
    tolerance_epsilon: float
    sign_convention: str
    finite_scope: str
    frozen_before_outcomes: bool
    obligation_relevant_attempts: tuple[tuple[int, int, int], ...]


@dataclass(frozen=True)
class AdmissibleGradientUpdate:
    update_id: str
    source_prefix: int
    target_prefix: int
    role: str


DISTINCTION_POTENTIAL = DistinctionPotentialSpec(
    functional=(
        "V_{t,O}(sigma) is the finite count of verdict='unresolved' over the "
        "frozen A0 obligation-relevant attempts N, L1, and L2 on the candidate's own structure"
    ),
    domain=(
        "candidate-owned finite presentation at one declared history prefix, restricted to "
        "the frozen attempt set {N,L1,L2} while the A0 obligation is active"
    ),
    codomain="integers {0,1,2,3}",
    orientation=(
        "each declared edge follows a recorded prefix update; the licensed drive uses P_BASE -> P_OPEN, "
        "and fewer unresolved obligation-relevant distinctions is movement toward closure"
    ),
    tolerance_epsilon=GRADIENT_EPSILON,
    sign_convention=(
        "g = V(sigma_t) - V(u sigma_t); positive g means the admissible update reduces "
        "the frozen unresolved-obligation count, zero is flat, and negative moves away from closure"
    ),
    finite_scope="3 frozen attempts x 5 candidates x the declared finite history prefixes",
    frozen_before_outcomes=True,
    obligation_relevant_attempts=A0_RELEVANT_ATTEMPTS,
)

ADMISSIBLE_GRADIENT_UPDATES = (
    AdmissibleGradientUpdate("base_to_open", P_BASE, P_OPEN, "opening branch measurement"),
    AdmissibleGradientUpdate("base_to_lock", P_BASE, P_LOCK, "locking branch measurement"),
    AdmissibleGradientUpdate(
        "open_to_open_lock",
        P_OPEN,
        P_OPEN_LOCK,
        "recorded opening-then-locking continuation",
    ),
    AdmissibleGradientUpdate(
        "lock_to_lock_open",
        P_LOCK,
        P_LOCK_OPEN,
        "recorded locking-then-opening continuation",
    ),
)
LICENSED_DRIVE_UPDATE_ID = "base_to_open"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(encoded)


def stream_json(stream: Stream) -> list[list[Any]]:
    return [list(record) for record in stream]


def validate_raw_stream(stream: Stream) -> bool:
    return bool(
        isinstance(stream, tuple)
        and stream
        and all(
            isinstance(record, tuple)
            and len(record) == 5
            and record[0] in PREFIXES
            and record[1] in PROBES
            and record[2] in MARKS
            and record[3] in MARKS
            and record[4] in VERDICTS
            for record in stream
        )
        and len({record[:4] for record in stream}) == len(stream)
        and set(record[4] for record in stream) == set(VERDICTS)
    )


def generate_raw_stream(seed: int = SEED) -> Stream:
    """Generate the one finite ground stream without persistent candidate state."""
    records: list[Record] = []
    rows = {
        P_BASE: {O: "distinguished", N: "unresolved", L1: "unresolved", L2: "unresolved", I0: "inadmissible"},
        P_OPEN: {O: "distinguished", N: "distinguished", L1: "unresolved", L2: "unresolved", I0: "inadmissible"},
        P_LOCK: {O: "distinguished", N: "unresolved", L1: "not_distinguished", L2: "not_distinguished", I0: "inadmissible"},
        P_OPEN_LOCK: {O: "distinguished", N: "distinguished", L1: "not_distinguished", L2: "not_distinguished", I0: "inadmissible"},
        P_LOCK_OPEN: {O: "distinguished", N: "not_distinguished", L1: "not_distinguished", L2: "not_distinguished", I0: "inadmissible"},
        P_HELD: {O: "distinguished", N: "distinguished", L1: "not_distinguished", L2: "not_distinguished", I0: "inadmissible"},
    }
    for prefix in PREFIXES:
        for (probe, mark_a, mark_b), verdict in rows[prefix].items():
            records.append((prefix, probe, mark_a, mark_b, verdict))
    random.Random(seed).shuffle(records)
    stream = tuple(records)
    if not validate_raw_stream(stream):
        raise RuntimeError("seeded raw distinction-attempt stream violates its frozen schema")
    return stream


def replace_verdicts(stream: Stream, replacements: dict[tuple[int, int, int, int], str]) -> Stream:
    replaced = tuple(
        (prefix, probe, mark_a, mark_b, replacements.get((prefix, probe, mark_a, mark_b), verdict))
        for prefix, probe, mark_a, mark_b, verdict in stream
    )
    if not validate_raw_stream(replaced):
        raise RuntimeError("hostile stream variant violates the frozen record schema")
    return replaced


def balanced_a0_stream(stream: Stream) -> Stream:
    # Relative to P_BASE, both one-step branches become (+1 distinguished,
    # +1 not-distinguished), so the opening/locking asymmetry is removed.
    return replace_verdicts(
        stream,
        {
            (P_OPEN, *L1): "not_distinguished",
            (P_LOCK, *N): "distinguished",
            (P_LOCK, *L2): "unresolved",
        },
    )


def obligation_erased_stream(stream: Stream) -> Stream:
    return replace_verdicts(
        stream,
        {(prefix, *O): "unresolved" for prefix in PREFIXES},
    )


def order_collapsed_stream(stream: Stream) -> Stream:
    source = {
        (probe, mark_a, mark_b): verdict
        for prefix, probe, mark_a, mark_b, verdict in stream
        if prefix == P_OPEN_LOCK
    }
    return replace_verdicts(
        stream,
        {
            (P_LOCK_OPEN, probe, mark_a, mark_b): verdict
            for (probe, mark_a, mark_b), verdict in source.items()
        },
    )


def erase_probe_stream(stream: Stream, probe_to_erase: int) -> Stream:
    reduced = tuple(record for record in stream if record[1] != probe_to_erase)
    if not reduced or any(record[4] not in VERDICTS for record in reduced):
        raise RuntimeError("probe erasure produced an invalid finite stream")
    return reduced


def relabel_stream(stream: Stream) -> tuple[Stream, dict[int, int], dict[int, int]]:
    probe_map = {0: 1, 1: 0}
    mark_map = {0: 2, 1: 3, 2: 0, 3: 1}
    relabeled = tuple(
        (prefix, probe_map[probe], mark_map[mark_a], mark_map[mark_b], verdict)
        for prefix, probe, mark_a, mark_b, verdict in stream
    )
    if not validate_raw_stream(relabeled):
        raise RuntimeError("bijective label erasure broke the raw stream schema")
    return relabeled, probe_map, mark_map


def permute_and_erase_history_stream(stream: Stream) -> Stream:
    """Swap the two order-bearing prefixes and erase the held-history segment."""
    prefix_map = {P_OPEN_LOCK: P_LOCK_OPEN, P_LOCK_OPEN: P_OPEN_LOCK}
    transformed = tuple(
        (prefix_map.get(prefix, prefix), probe, mark_a, mark_b, verdict)
        for prefix, probe, mark_a, mark_b, verdict in stream
        if prefix != P_HELD
    )
    if not transformed or len({record[:4] for record in transformed}) != len(transformed):
        raise RuntimeError("history permutation/erasure produced an invalid finite stream")
    return transformed


def coarsen_stream(stream: Stream) -> Stream:
    """Genuinely merge 0~1 and 2~3 into a two-mark resolution."""
    mark_map = {0: 0, 1: 0, 2: 1, 3: 1}
    coarsened = tuple(
        (prefix, probe, mark_map[mark_a], mark_map[mark_b], verdict)
        for prefix, probe, mark_a, mark_b, verdict in stream
    )
    if len({record[:4] for record in coarsened}) != len(coarsened):
        raise RuntimeError("frozen coarsening unexpectedly collided attempt records")
    return coarsened


RAW_STREAM = generate_raw_stream(SEED)
BALANCED_STREAM = balanced_a0_stream(RAW_STREAM)
OBLIGATION_ERASED_STREAM = obligation_erased_stream(RAW_STREAM)
ORDER_COLLAPSED_STREAM = order_collapsed_stream(RAW_STREAM)
HISTORY_PERMUTED_ERASED_STREAM = permute_and_erase_history_stream(RAW_STREAM)
PROBE1_ERASED_STREAM = erase_probe_stream(RAW_STREAM, 1)
RELABELLED_STREAM, PROBE_LABEL_MAP, MARK_LABEL_MAP = relabel_stream(RAW_STREAM)
COARSENED_STREAM = coarsen_stream(RAW_STREAM)


def mapped_attempt(attempt: tuple[int, int, int]) -> tuple[int, int, int]:
    return (
        PROBE_LABEL_MAP[attempt[0]],
        MARK_LABEL_MAP[attempt[1]],
        MARK_LABEL_MAP[attempt[2]],
    )


O_RELABELLED = mapped_attempt(O)
N_RELABELLED = mapped_attempt(N)
COARSEN_MARK_MAP = {0: 0, 1: 0, 2: 1, 3: 1}
O_COARSE = (O[0], COARSEN_MARK_MAP[O[1]], COARSEN_MARK_MAP[O[2]])
N_COARSE = (N[0], COARSEN_MARK_MAP[N[1]], COARSEN_MARK_MAP[N[2]])


def resolution_claim_effect(
    raw: dict[str, bool],
    coarsened: dict[str, bool],
    raw_fed_to_coarsened_readout: dict[str, bool],
) -> dict[str, Any]:
    status = {
        claim: (
            "persists"
            if raw[claim] == coarsened[claim]
            else "breaks"
            if raw[claim] and not coarsened[claim]
            else "appears"
        )
        for claim in raw
    }
    expected_coarsened = bool(
        raw["F01"]
        and coarsened["F01"]
        and raw["N01"]
        and coarsened["N01"]
        and raw["A0_drive"]
        and coarsened["A0_drive"]
        and not coarsened["obligation_retention"]
    )
    raw_feed_matches = raw_fed_to_coarsened_readout == coarsened
    return {
        "executed": True,
        "mark_map": {str(key): value for key, value in COARSEN_MARK_MAP.items()},
        "mapped_obligation": list(O_COARSE),
        "mapped_N01_attempt": list(N_COARSE),
        "raw_claims": raw,
        "coarsened_claims": coarsened,
        "raw_stream_fed_to_coarsened_readout": raw_fed_to_coarsened_readout,
        "per_claim_effect": status,
        "coarsened_side_expected": expected_coarsened,
        "raw_substitution_matches_coarsened": raw_feed_matches,
        "verdict": bool(expected_coarsened and not raw_feed_matches),
    }


def history_control_effect(
    raw_pair: tuple[Any, Any],
    attacked_pair: tuple[Any, Any],
    raw_prefixes: Iterable[int],
    attacked_prefixes: Iterable[int],
) -> dict[str, Any]:
    raw_prefix_set = set(raw_prefixes)
    attacked_prefix_set = set(attacked_prefixes)
    verdict = bool(
        attacked_pair == tuple(reversed(raw_pair))
        and P_HELD in raw_prefix_set
        and P_HELD not in attacked_prefix_set
        and len(attacked_prefix_set) == len(raw_prefix_set) - 1
    )
    return {
        "executed": True,
        "manipulation": "swap P_OPEN_LOCK/P_LOCK_OPEN and erase the full P_HELD segment",
        "raw_order_pair": list(raw_pair),
        "attacked_order_pair": list(attacked_pair),
        "raw_prefixes": sorted(raw_prefix_set),
        "attacked_prefixes": sorted(attacked_prefix_set),
        "predicted_effect": "order pair reverses and held segment disappears",
        "verdict": verdict,
    }


def representation_payload_hash(rep: dict[str, Any]) -> str:
    payload = {
        key: value
        for key, value in rep.items()
        if key not in {"kind", "source_kind", "source_hash"}
    }
    return sha256_json(payload)


def merged_shared_build(stream: Stream) -> dict[str, Any]:
    """Hostile common table: one pre-built structure shared by every reader."""
    table = {
        f"{prefix}:{probe}:{mark_a}:{mark_b}": verdict
        for prefix, probe, mark_a, mark_b, verdict in stream
    }
    return {
        "kind": "hostile_merged_shared_table",
        "source_kind": "one_common_prebuilt_table",
        "source_hash": sha256_json(stream_json(stream)),
        "table": dict(sorted(table.items())),
    }


def merged_shared_lookup(rep: dict[str, Any], prefix: int, attempt: tuple[int, int, int]) -> str:
    key = f"{prefix}:{attempt[0]}:{attempt[1]}:{attempt[2]}"
    return str(rep["table"].get(key, "inadmissible"))


def merged_shared_readout(rep: dict[str, Any]) -> dict[str, bool]:
    return {
        "obligation_retention": bool(
            O[1] != O[2]
            and merged_shared_lookup(rep, P_BASE, O) == "distinguished"
            and merged_shared_lookup(rep, P_LOCK, O) == "distinguished"
        ),
        "N01": merged_shared_lookup(rep, P_OPEN_LOCK, N) != merged_shared_lookup(rep, P_LOCK_OPEN, N),
    }


def root_independence_observation(
    representations: dict[str, dict[str, Any]],
    readouts: dict[str, dict[str, bool]],
    claim_bearing_objects: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    claim_bearing = claim_bearing_objects or representations
    object_count = len({id(rep) for rep in representations.values()})
    claim_bearing_count = len({id(rep) for rep in claim_bearing.values()})
    payload_hashes = {candidate: representation_payload_hash(rep) for candidate, rep in representations.items()}
    payload_count = len(set(payload_hashes.values()))
    candidate_count = len(representations)
    return {
        "executed": True,
        "candidate_count": candidate_count,
        "distinct_runtime_object_count": object_count,
        "distinct_claim_bearing_object_count": claim_bearing_count,
        "distinct_payload_count": payload_count,
        "payload_hashes": payload_hashes,
        "readouts": readouts,
        "passed": bool(
            object_count == candidate_count
            and claim_bearing_count == candidate_count
            and payload_count == candidate_count
        ),
    }


# ---------------------------------------------------------------------------
# G1 owns a contextual partial table.  Its builder's only input is the stream.


def g1_build(stream: Stream) -> dict[str, Any]:
    contexts: dict[str, list[list[Any]]] = {}
    for prefix, probe, mark_a, mark_b, verdict in stream:
        contexts.setdefault(str(prefix), []).append([probe, mark_a, mark_b, verdict])
    for rows in contexts.values():
        rows.sort(key=lambda row: (row[0], row[1], row[2]))
    return {
        "kind": "G1_contextual_partial_table",
        "source_kind": "immutable_raw_stream",
        "source_hash": sha256_json(stream_json(stream)),
        "contexts": dict(sorted(contexts.items(), key=lambda item: int(item[0]))),
    }


def g1_lookup(rep: dict[str, Any], prefix: int, attempt: tuple[int, int, int]) -> str:
    for probe, mark_a, mark_b, verdict in rep["contexts"].get(str(prefix), []):
        if (probe, mark_a, mark_b) == attempt:
            return str(verdict)
    return "inadmissible"


def g1_f01(rep: dict[str, Any]) -> bool:
    rows = [row for values in rep["contexts"].values() for row in values]
    return bool(rows and len(rows) <= 64 and all(row[3] in VERDICTS for row in rows))


def g1_obligation(rep: dict[str, Any], attempt: tuple[int, int, int] = O) -> bool:
    return bool(
        attempt[1] != attempt[2]
        and g1_lookup(rep, P_BASE, attempt) == "distinguished"
        and g1_lookup(rep, P_LOCK, attempt) == "distinguished"
    )


def g1_n01(rep: dict[str, Any], attempt: tuple[int, int, int] = N) -> bool:
    return g1_lookup(rep, P_OPEN_LOCK, attempt) != g1_lookup(rep, P_LOCK_OPEN, attempt)


def g1_counts(rep: dict[str, Any], prefix: int) -> tuple[int, int]:
    verdicts = [row[3] for row in rep["contexts"].get(str(prefix), [])]
    return verdicts.count("distinguished"), verdicts.count("not_distinguished")


def g1_a0(rep: dict[str, Any]) -> dict[str, Any]:
    base = g1_counts(rep, P_BASE)
    opened = g1_counts(rep, P_OPEN)
    locked = g1_counts(rep, P_LOCK)
    open_delta = (opened[0] - base[0], opened[1] - base[1])
    lock_delta = (locked[0] - base[0], locked[1] - base[1])
    return {
        "open_delta": list(open_delta),
        "lock_delta": list(lock_delta),
        "A0_drive": bool(open_delta == (1, 0) and lock_delta == (0, 2) and open_delta != lock_delta),
    }


def g1_evaluate() -> dict[str, Any]:
    main = g1_build(RAW_STREAM)
    balanced = g1_build(BALANCED_STREAM)
    erased = g1_build(OBLIGATION_ERASED_STREAM)
    collapsed = g1_build(ORDER_COLLAPSED_STREAM)
    history_attacked = g1_build(HISTORY_PERMUTED_ERASED_STREAM)
    relabeled = g1_build(RELABELLED_STREAM)
    coarse = g1_build(COARSENED_STREAM)
    a0 = g1_a0(main)
    a0_negative = g1_a0(balanced)
    battery = {
        "F01": g1_f01(main),
        "N01": g1_n01(main),
        "obligation_retention": g1_obligation(main),
        "A0_drive": a0["A0_drive"],
        "A0_balanced_negative": a0_negative["A0_drive"],
    }
    raw_claims = {key: bool(battery[key]) for key in ("F01", "N01", "obligation_retention", "A0_drive")}
    coarsened_claims = {
        "F01": g1_f01(coarse),
        "N01": g1_n01(coarse, N_COARSE),
        "obligation_retention": g1_obligation(coarse, O_COARSE),
        "A0_drive": g1_a0(coarse)["A0_drive"],
    }
    raw_fed_to_coarsened_readout = {
        "F01": g1_f01(main),
        "N01": g1_n01(main, N_COARSE),
        "obligation_retention": g1_obligation(main, O_COARSE),
        "A0_drive": g1_a0(main)["A0_drive"],
    }
    resolution_evidence = resolution_claim_effect(raw_claims, coarsened_claims, raw_fed_to_coarsened_readout)
    history_evidence = history_control_effect(
        (g1_lookup(main, P_OPEN_LOCK, N), g1_lookup(main, P_LOCK_OPEN, N)),
        (g1_lookup(history_attacked, P_OPEN_LOCK, N), g1_lookup(history_attacked, P_LOCK_OPEN, N)),
        (int(prefix) for prefix in main["contexts"]),
        (int(prefix) for prefix in history_attacked["contexts"]),
    )
    controls = {
        "label_metadata_erasure": g1_obligation(relabeled, O_RELABELLED) and g1_n01(relabeled, N_RELABELLED),
        "anti_by_construction": g1_obligation(main) and not g1_obligation(erased) and a0["A0_drive"] and not a0_negative["A0_drive"],
        "order_commutation": g1_n01(main) and not g1_n01(collapsed),
        "history_memory": history_evidence["verdict"],
        "resolution": resolution_evidence["verdict"],
    }
    survived = bool(
        battery["F01"]
        and battery["N01"]
        and battery["obligation_retention"]
        and battery["A0_drive"]
        and not battery["A0_balanced_negative"]
    )
    return {
        "main": main,
        "battery": battery,
        "a0": a0,
        "a0_negative": a0_negative,
        "controls": controls,
        "resolution_evidence": resolution_evidence,
        "history_evidence": history_evidence,
        "survived": survived,
    }


# ---------------------------------------------------------------------------
# G2 is the retained probe-blind support/equivalence/quotient construction.


def g2_build(stream: Stream) -> dict[str, Any]:
    observations: dict[str, list[list[Any]]] = {}
    support_by_prefix: dict[str, list[int]] = {}
    classes_by_prefix: dict[str, list[int]] = {}
    equivalence_by_prefix: dict[str, list[list[int]]] = {}
    signatures_by_prefix: dict[str, list[list[str]]] = {}
    quotient_by_prefix: dict[str, list[list[Any]]] = {}
    prefixes = sorted({record[0] for record in stream})
    for prefix in prefixes:
        rows = sorted(
            [[probe, mark_a, mark_b, verdict] for hp, probe, mark_a, mark_b, verdict in stream if hp == prefix],
            key=lambda row: (row[0], row[1], row[2]),
        )
        observations[str(prefix)] = rows
        support = sorted({int(row[1]) for row in rows} | {int(row[2]) for row in rows})
        support_by_prefix[str(prefix)] = support
        parent = {mark: mark for mark in support}

        def find(mark: int) -> int:
            while parent[mark] != mark:
                parent[mark] = parent[parent[mark]]
                mark = parent[mark]
            return mark

        def union(left: int, right: int) -> None:
            root_left, root_right = find(left), find(right)
            if root_left != root_right:
                parent[max(root_left, root_right)] = min(root_left, root_right)

        for _probe, mark_a, mark_b, verdict in rows:
            if verdict == "not_distinguished":
                union(int(mark_a), int(mark_b))
        roots = [find(mark) for mark in support]
        root_order: list[int] = []
        for root in roots:
            if root not in root_order:
                root_order.append(root)
        classes = [root_order.index(root) for root in roots]
        classes_by_prefix[str(prefix)] = classes
        equivalence_by_prefix[str(prefix)] = [
            [int(classes[i] == classes[j]) for j in range(len(support))]
            for i in range(len(support))
        ]
        row_map = {(int(p), int(a), int(b)): str(v) for p, a, b, v in rows}
        signatures: list[list[str]] = []
        for mark in support:
            signature: list[str] = []
            for probe in PROBES:
                for other in support:
                    signature.append(row_map.get((probe, mark, other), "inadmissible"))
                    signature.append(row_map.get((probe, other, mark), "inadmissible"))
            signatures.append(signature)
        signatures_by_prefix[str(prefix)] = signatures
        class_for_mark = {mark: classes[index] for index, mark in enumerate(support)}
        quotient_by_prefix[str(prefix)] = [
            [probe, class_for_mark[mark_a], class_for_mark[mark_b], verdict]
            for probe, mark_a, mark_b, verdict in rows
        ]
    return {
        "kind": "G2_probe_blind_support_equivalence_quotient",
        "source_kind": "immutable_raw_stream",
        "source_hash": sha256_json(stream_json(stream)),
        "observations": observations,
        "support": support_by_prefix,
        "signatures": signatures_by_prefix,
        "classes": classes_by_prefix,
        "equivalence": equivalence_by_prefix,
        "quotient": quotient_by_prefix,
    }


def g2_observation(rep: dict[str, Any], prefix: int, attempt: tuple[int, int, int]) -> str:
    for probe, mark_a, mark_b, verdict in rep["observations"].get(str(prefix), []):
        if (probe, mark_a, mark_b) == attempt:
            return str(verdict)
    return "inadmissible"


def g2_class(rep: dict[str, Any], prefix: int, mark: int) -> int | None:
    support = rep["support"].get(str(prefix), [])
    if mark not in support:
        return None
    return int(rep["classes"][str(prefix)][support.index(mark)])


def g2_f01(rep: dict[str, Any]) -> bool:
    return bool(
        rep["support"]
        and all(len(support) <= len(MARKS) for support in rep["support"].values())
        and all(verdict in VERDICTS for rows in rep["observations"].values() for *_attempt, verdict in rows)
    )


def g2_obligation(rep: dict[str, Any], attempt: tuple[int, int, int] = O) -> bool:
    mark_a, mark_b = attempt[1], attempt[2]
    return bool(
        mark_a != mark_b
        and g2_observation(rep, P_BASE, attempt) == "distinguished"
        and g2_observation(rep, P_LOCK, attempt) == "distinguished"
        and g2_class(rep, P_LOCK, mark_a) != g2_class(rep, P_LOCK, mark_b)
    )


def g2_n01(rep: dict[str, Any], attempt: tuple[int, int, int] = N) -> bool:
    mark_a, mark_b = attempt[1], attempt[2]
    early_same = g2_class(rep, P_OPEN_LOCK, mark_a) == g2_class(rep, P_OPEN_LOCK, mark_b)
    late_same = g2_class(rep, P_LOCK_OPEN, mark_a) == g2_class(rep, P_LOCK_OPEN, mark_b)
    return early_same != late_same


def g2_order_pair(rep: dict[str, Any], attempt: tuple[int, int, int] = N) -> tuple[bool, bool]:
    mark_a, mark_b = attempt[1], attempt[2]
    return (
        g2_class(rep, P_OPEN_LOCK, mark_a) == g2_class(rep, P_OPEN_LOCK, mark_b),
        g2_class(rep, P_LOCK_OPEN, mark_a) == g2_class(rep, P_LOCK_OPEN, mark_b),
    )


def g2_counts(rep: dict[str, Any], prefix: int) -> tuple[int, int]:
    verdicts = [row[3] for row in rep["observations"].get(str(prefix), [])]
    return verdicts.count("distinguished"), verdicts.count("not_distinguished")


def g2_a0(rep: dict[str, Any]) -> dict[str, Any]:
    base = g2_counts(rep, P_BASE)
    opened = g2_counts(rep, P_OPEN)
    locked = g2_counts(rep, P_LOCK)
    open_delta = (opened[0] - base[0], opened[1] - base[1])
    lock_delta = (locked[0] - base[0], locked[1] - base[1])
    return {
        "readout": "candidate-owned pre-quotient observation counts retained inside G2",
        "open_delta": list(open_delta),
        "lock_delta": list(lock_delta),
        "A0_drive": bool(open_delta == (1, 0) and lock_delta == (0, 2) and open_delta != lock_delta),
    }


def g2_evaluate() -> dict[str, Any]:
    main = g2_build(RAW_STREAM)
    balanced = g2_build(BALANCED_STREAM)
    erased = g2_build(OBLIGATION_ERASED_STREAM)
    collapsed = g2_build(ORDER_COLLAPSED_STREAM)
    history_attacked = g2_build(HISTORY_PERMUTED_ERASED_STREAM)
    probe_erased = g2_build(PROBE1_ERASED_STREAM)
    relabeled = g2_build(RELABELLED_STREAM)
    coarse = g2_build(COARSENED_STREAM)
    a0 = g2_a0(main)
    a0_negative = g2_a0(balanced)
    prequotient_o = g2_observation(main, P_LOCK, O) == "distinguished"
    quotient_o = g2_obligation(main)
    battery = {
        "F01": g2_f01(main),
        "N01": g2_n01(main),
        "obligation_retention": quotient_o,
        "A0_drive": a0["A0_drive"],
        "A0_balanced_negative": a0_negative["A0_drive"],
    }
    raw_claims = {key: bool(battery[key]) for key in ("F01", "N01", "obligation_retention", "A0_drive")}
    coarsened_claims = {
        "F01": g2_f01(coarse),
        "N01": g2_n01(coarse, N_COARSE),
        "obligation_retention": g2_obligation(coarse, O_COARSE),
        "A0_drive": g2_a0(coarse)["A0_drive"],
    }
    raw_fed_to_coarsened_readout = {
        "F01": g2_f01(main),
        "N01": g2_n01(main, N_COARSE),
        "obligation_retention": g2_obligation(main, O_COARSE),
        "A0_drive": g2_a0(main)["A0_drive"],
    }
    resolution_evidence = resolution_claim_effect(raw_claims, coarsened_claims, raw_fed_to_coarsened_readout)
    history_evidence = history_control_effect(
        g2_order_pair(main),
        g2_order_pair(history_attacked),
        (int(prefix) for prefix in main["observations"]),
        (int(prefix) for prefix in history_attacked["observations"]),
    )
    controls = {
        "label_metadata_erasure": not g2_obligation(relabeled, O_RELABELLED) and g2_n01(relabeled, N_RELABELLED),
        "anti_by_construction": (not quotient_o) and g2_obligation(probe_erased) and a0["A0_drive"] and not a0_negative["A0_drive"],
        "probe_quotient": (not quotient_o) and g2_obligation(probe_erased),
        "order_commutation": g2_n01(main) and not g2_n01(collapsed),
        "history_memory": history_evidence["verdict"],
        "resolution": resolution_evidence["verdict"],
    }
    survived = bool(
        battery["F01"]
        and battery["N01"]
        and battery["obligation_retention"]
        and battery["A0_drive"]
        and not battery["A0_balanced_negative"]
    )
    return {
        "main": main,
        "battery": battery,
        "a0": a0,
        "a0_negative": a0_negative,
        "controls": controls,
        "resolution_evidence": resolution_evidence,
        "history_evidence": history_evidence,
        "survived": survived,
        "defeat_reason": (
            "G2 globally closes not-distinguished generators across probes. At prefix 2, probe-1 evidence "
            "merges marks 0 and 1 used by probe-0 obligation O. This defeats only the probe-blind G2 "
            "variant; G2P shows that the equivalence/quotient family remains live."
            if not survived
            else None
        ),
    }


# ---------------------------------------------------------------------------
# G2P owns a probe-respecting support/equivalence/quotient presentation.


def g2p_build(stream: Stream) -> dict[str, Any]:
    observations: dict[str, list[list[Any]]] = {}
    support_by_prefix_probe: dict[str, dict[str, list[int]]] = {}
    classes_by_prefix_probe: dict[str, dict[str, list[int]]] = {}
    equivalence_by_prefix_probe: dict[str, dict[str, list[list[int]]]] = {}
    quotient_by_prefix: dict[str, list[list[Any]]] = {}
    prefixes = sorted({record[0] for record in stream})
    for prefix in prefixes:
        rows = sorted(
            [[probe, mark_a, mark_b, verdict] for hp, probe, mark_a, mark_b, verdict in stream if hp == prefix],
            key=lambda row: (row[0], row[1], row[2]),
        )
        observations[str(prefix)] = rows
        support_by_prefix_probe[str(prefix)] = {}
        classes_by_prefix_probe[str(prefix)] = {}
        equivalence_by_prefix_probe[str(prefix)] = {}
        class_maps: dict[int, dict[int, int]] = {}
        for probe in sorted({int(row[0]) for row in rows}):
            probe_rows = [row for row in rows if int(row[0]) == probe]
            support = sorted({int(row[1]) for row in probe_rows} | {int(row[2]) for row in probe_rows})
            parent = {mark: mark for mark in support}

            def find(mark: int) -> int:
                while parent[mark] != mark:
                    parent[mark] = parent[parent[mark]]
                    mark = parent[mark]
                return mark

            def union(left: int, right: int) -> None:
                root_left, root_right = find(left), find(right)
                if root_left != root_right:
                    parent[max(root_left, root_right)] = min(root_left, root_right)

            for _probe, mark_a, mark_b, verdict in probe_rows:
                if verdict == "not_distinguished":
                    union(int(mark_a), int(mark_b))
            roots = [find(mark) for mark in support]
            root_order: list[int] = []
            for root in roots:
                if root not in root_order:
                    root_order.append(root)
            classes = [root_order.index(root) for root in roots]
            support_by_prefix_probe[str(prefix)][str(probe)] = support
            classes_by_prefix_probe[str(prefix)][str(probe)] = classes
            equivalence_by_prefix_probe[str(prefix)][str(probe)] = [
                [int(classes[i] == classes[j]) for j in range(len(support))]
                for i in range(len(support))
            ]
            class_maps[probe] = {mark: classes[index] for index, mark in enumerate(support)}
        quotient_by_prefix[str(prefix)] = [
            [probe, class_maps[int(probe)][int(mark_a)], class_maps[int(probe)][int(mark_b)], verdict]
            for probe, mark_a, mark_b, verdict in rows
        ]
    return {
        "kind": "G2P_probe_respecting_support_equivalence_quotient",
        "source_kind": "immutable_raw_stream",
        "source_hash": sha256_json(stream_json(stream)),
        "observations": observations,
        "support_by_probe": support_by_prefix_probe,
        "classes_by_probe": classes_by_prefix_probe,
        "equivalence_by_probe": equivalence_by_prefix_probe,
        "quotient": quotient_by_prefix,
    }


def g2p_class(rep: dict[str, Any], prefix: int, probe: int, mark: int) -> int | None:
    support = rep["support_by_probe"].get(str(prefix), {}).get(str(probe), [])
    if mark not in support:
        return None
    return int(rep["classes_by_probe"][str(prefix)][str(probe)][support.index(mark)])


def g2p_f01(rep: dict[str, Any]) -> bool:
    supports = [
        support
        for per_probe in rep["support_by_probe"].values()
        for support in per_probe.values()
    ]
    return bool(
        supports
        and all(len(support) <= len(MARKS) for support in supports)
        and all(verdict in VERDICTS for rows in rep["observations"].values() for *_attempt, verdict in rows)
    )


def g2p_obligation(rep: dict[str, Any], attempt: tuple[int, int, int] = O) -> bool:
    probe, mark_a, mark_b = attempt
    return bool(
        mark_a != mark_b
        and g2_observation(rep, P_BASE, attempt) == "distinguished"
        and g2_observation(rep, P_LOCK, attempt) == "distinguished"
        and g2p_class(rep, P_LOCK, probe, mark_a) != g2p_class(rep, P_LOCK, probe, mark_b)
    )


def g2p_order_pair(rep: dict[str, Any], attempt: tuple[int, int, int] = N) -> tuple[bool, bool]:
    probe, mark_a, mark_b = attempt
    return (
        g2p_class(rep, P_OPEN_LOCK, probe, mark_a) == g2p_class(rep, P_OPEN_LOCK, probe, mark_b),
        g2p_class(rep, P_LOCK_OPEN, probe, mark_a) == g2p_class(rep, P_LOCK_OPEN, probe, mark_b),
    )


def g2p_n01(rep: dict[str, Any], attempt: tuple[int, int, int] = N) -> bool:
    early_same, late_same = g2p_order_pair(rep, attempt)
    return early_same != late_same


def g2p_a0(rep: dict[str, Any]) -> dict[str, Any]:
    result = g2_a0(rep)
    result["readout"] = "candidate-owned pre-quotient observation counts retained inside probe-respecting G2P"
    return result


def g2p_evaluate() -> dict[str, Any]:
    main = g2p_build(RAW_STREAM)
    balanced = g2p_build(BALANCED_STREAM)
    erased = g2p_build(OBLIGATION_ERASED_STREAM)
    collapsed = g2p_build(ORDER_COLLAPSED_STREAM)
    history_attacked = g2p_build(HISTORY_PERMUTED_ERASED_STREAM)
    probe_erased = g2p_build(PROBE1_ERASED_STREAM)
    relabeled = g2p_build(RELABELLED_STREAM)
    coarse = g2p_build(COARSENED_STREAM)
    a0 = g2p_a0(main)
    a0_negative = g2p_a0(balanced)
    battery = {
        "F01": g2p_f01(main),
        "N01": g2p_n01(main),
        "obligation_retention": g2p_obligation(main),
        "A0_drive": a0["A0_drive"],
        "A0_balanced_negative": a0_negative["A0_drive"],
    }
    raw_claims = {key: bool(battery[key]) for key in ("F01", "N01", "obligation_retention", "A0_drive")}
    coarsened_claims = {
        "F01": g2p_f01(coarse),
        "N01": g2p_n01(coarse, N_COARSE),
        "obligation_retention": g2p_obligation(coarse, O_COARSE),
        "A0_drive": g2p_a0(coarse)["A0_drive"],
    }
    raw_fed_to_coarsened_readout = {
        "F01": g2p_f01(main),
        "N01": g2p_n01(main, N_COARSE),
        "obligation_retention": g2p_obligation(main, O_COARSE),
        "A0_drive": g2p_a0(main)["A0_drive"],
    }
    resolution_evidence = resolution_claim_effect(raw_claims, coarsened_claims, raw_fed_to_coarsened_readout)
    history_evidence = history_control_effect(
        g2p_order_pair(main),
        g2p_order_pair(history_attacked),
        (int(prefix) for prefix in main["observations"]),
        (int(prefix) for prefix in history_attacked["observations"]),
    )
    probe_erasure_rebuilt = bool(
        g2p_obligation(main)
        and g2p_obligation(probe_erased)
        and sha256_json(main) != sha256_json(probe_erased)
        and all("1" not in per_probe for per_probe in probe_erased["support_by_probe"].values())
    )
    controls = {
        "label_metadata_erasure": g2p_obligation(relabeled, O_RELABELLED) and g2p_n01(relabeled, N_RELABELLED),
        "anti_by_construction": g2p_obligation(main) and not g2p_obligation(erased) and a0["A0_drive"] and not a0_negative["A0_drive"],
        "probe_quotient": probe_erasure_rebuilt,
        "order_commutation": g2p_n01(main) and not g2p_n01(collapsed),
        "history_memory": history_evidence["verdict"],
        "resolution": resolution_evidence["verdict"],
    }
    survived = bool(
        battery["F01"]
        and battery["N01"]
        and battery["obligation_retention"]
        and battery["A0_drive"]
        and not battery["A0_balanced_negative"]
    )
    return {
        "main": main,
        "battery": battery,
        "a0": a0,
        "a0_negative": a0_negative,
        "controls": controls,
        "resolution_evidence": resolution_evidence,
        "history_evidence": history_evidence,
        "survived": survived,
    }


# ---------------------------------------------------------------------------
# G3 owns record-events and candidate-local incidence links.


def g3_build(stream: Stream) -> dict[str, Any]:
    rows = sorted(stream, key=lambda record: (record[0], record[1], record[2], record[3]))
    base_distinguished: dict[tuple[int, int, int], int] = {}
    events: list[dict[str, Any]] = []
    for prefix, probe, mark_a, mark_b, verdict in rows:
        attempt = (probe, mark_a, mark_b)
        event_id = len(events)
        parent = base_distinguished.get(attempt) if prefix != P_BASE and verdict == "distinguished" else None
        events.append(
            {
                "event_id": event_id,
                "history_prefix_index": prefix,
                "probe": probe,
                "mark_a": mark_a,
                "mark_b": mark_b,
                "verdict": verdict,
                "parent_event_id": parent,
            }
        )
        if prefix == P_BASE and verdict == "distinguished":
            base_distinguished[attempt] = event_id
    incidence = [
        [event["parent_event_id"], event["event_id"]]
        for event in events
        if event["parent_event_id"] is not None
    ]
    return {
        "kind": "G3_event_incidence",
        "source_kind": "immutable_raw_stream",
        "source_hash": sha256_json(stream_json(stream)),
        "events": events,
        "incidence": incidence,
    }


def g3_event(rep: dict[str, Any], prefix: int, attempt: tuple[int, int, int]) -> dict[str, Any] | None:
    for event in rep["events"]:
        if event["history_prefix_index"] == prefix and (event["probe"], event["mark_a"], event["mark_b"]) == attempt:
            return event
    return None


def g3_f01(rep: dict[str, Any]) -> bool:
    ids = [event["event_id"] for event in rep["events"]]
    return bool(ids == list(range(len(ids))) and len(ids) <= 64 and all(event["verdict"] in VERDICTS for event in rep["events"]))


def g3_obligation(rep: dict[str, Any], attempt: tuple[int, int, int] = O) -> bool:
    base = g3_event(rep, P_BASE, attempt)
    locked = g3_event(rep, P_LOCK, attempt)
    return bool(
        attempt[1] != attempt[2]
        and base is not None
        and locked is not None
        and base["verdict"] == "distinguished"
        and locked["verdict"] == "distinguished"
        and locked["parent_event_id"] == base["event_id"]
    )


def g3_n01(rep: dict[str, Any], attempt: tuple[int, int, int] = N) -> bool:
    first = g3_event(rep, P_OPEN_LOCK, attempt)
    second = g3_event(rep, P_LOCK_OPEN, attempt)
    return bool(first is not None and second is not None and first["verdict"] != second["verdict"])


def g3_counts(rep: dict[str, Any], prefix: int) -> tuple[int, int]:
    verdicts = [event["verdict"] for event in rep["events"] if event["history_prefix_index"] == prefix]
    return verdicts.count("distinguished"), verdicts.count("not_distinguished")


def g3_a0(rep: dict[str, Any]) -> dict[str, Any]:
    base = g3_counts(rep, P_BASE)
    opened = g3_counts(rep, P_OPEN)
    locked = g3_counts(rep, P_LOCK)
    open_delta = (opened[0] - base[0], opened[1] - base[1])
    lock_delta = (locked[0] - base[0], locked[1] - base[1])
    return {
        "open_delta": list(open_delta),
        "lock_delta": list(lock_delta),
        "A0_drive": bool(open_delta == (1, 0) and lock_delta == (0, 2) and open_delta != lock_delta),
    }


def g3_evaluate() -> dict[str, Any]:
    main = g3_build(RAW_STREAM)
    balanced = g3_build(BALANCED_STREAM)
    erased = g3_build(OBLIGATION_ERASED_STREAM)
    collapsed = g3_build(ORDER_COLLAPSED_STREAM)
    history_attacked = g3_build(HISTORY_PERMUTED_ERASED_STREAM)
    relabeled = g3_build(RELABELLED_STREAM)
    coarse = g3_build(COARSENED_STREAM)
    a0 = g3_a0(main)
    a0_negative = g3_a0(balanced)
    battery = {
        "F01": g3_f01(main),
        "N01": g3_n01(main),
        "obligation_retention": g3_obligation(main),
        "A0_drive": a0["A0_drive"],
        "A0_balanced_negative": a0_negative["A0_drive"],
    }
    raw_claims = {key: bool(battery[key]) for key in ("F01", "N01", "obligation_retention", "A0_drive")}
    coarsened_claims = {
        "F01": g3_f01(coarse),
        "N01": g3_n01(coarse, N_COARSE),
        "obligation_retention": g3_obligation(coarse, O_COARSE),
        "A0_drive": g3_a0(coarse)["A0_drive"],
    }
    raw_fed_to_coarsened_readout = {
        "F01": g3_f01(main),
        "N01": g3_n01(main, N_COARSE),
        "obligation_retention": g3_obligation(main, O_COARSE),
        "A0_drive": g3_a0(main)["A0_drive"],
    }
    resolution_evidence = resolution_claim_effect(raw_claims, coarsened_claims, raw_fed_to_coarsened_readout)
    raw_first, raw_second = g3_event(main, P_OPEN_LOCK, N), g3_event(main, P_LOCK_OPEN, N)
    attacked_first = g3_event(history_attacked, P_OPEN_LOCK, N)
    attacked_second = g3_event(history_attacked, P_LOCK_OPEN, N)
    history_evidence = history_control_effect(
        (raw_first["verdict"] if raw_first else None, raw_second["verdict"] if raw_second else None),
        (attacked_first["verdict"] if attacked_first else None, attacked_second["verdict"] if attacked_second else None),
        (int(event["history_prefix_index"]) for event in main["events"]),
        (int(event["history_prefix_index"]) for event in history_attacked["events"]),
    )
    controls = {
        "label_metadata_erasure": g3_obligation(relabeled, O_RELABELLED) and g3_n01(relabeled, N_RELABELLED),
        "anti_by_construction": g3_obligation(main) and not g3_obligation(erased) and a0["A0_drive"] and not a0_negative["A0_drive"],
        "order_commutation": g3_n01(main) and not g3_n01(collapsed),
        "history_memory": history_evidence["verdict"],
        "resolution": resolution_evidence["verdict"],
    }
    survived = bool(
        battery["F01"]
        and battery["N01"]
        and battery["obligation_retention"]
        and battery["A0_drive"]
        and not battery["A0_balanced_negative"]
    )
    return {
        "main": main,
        "battery": battery,
        "a0": a0,
        "a0_negative": a0_negative,
        "controls": controls,
        "resolution_evidence": resolution_evidence,
        "history_evidence": history_evidence,
        "survived": survived,
    }


# ---------------------------------------------------------------------------
# G4 owns a total table for every observed history prefix.


def g4_build(stream: Stream) -> dict[str, Any]:
    support = sorted({record[2] for record in stream} | {record[3] for record in stream})
    probes = sorted({record[1] for record in stream})
    prefixes = sorted({record[0] for record in stream})
    tables: dict[str, dict[str, str]] = {}
    observed_keys: dict[str, list[str]] = {}
    for prefix in prefixes:
        table = {
            f"{probe}:{mark_a}:{mark_b}": "inadmissible"
            for probe, mark_a, mark_b in itertools.product(probes, support, support)
        }
        for hp, probe, mark_a, mark_b, verdict in stream:
            if hp == prefix:
                table[f"{probe}:{mark_a}:{mark_b}"] = verdict
        observed_keys[str(prefix)] = sorted(
            f"{probe}:{mark_a}:{mark_b}"
            for hp, probe, mark_a, mark_b, _verdict in stream
            if hp == prefix
        )
        tables[str(prefix)] = dict(sorted(table.items()))
    return {
        "kind": "G4_history_indexed_total_table",
        "source_kind": "immutable_raw_stream",
        "source_hash": sha256_json(stream_json(stream)),
        "support": support,
        "probes": probes,
        "tables": tables,
        "observed_keys": observed_keys,
    }


def g4_lookup(rep: dict[str, Any], prefix: int, attempt: tuple[int, int, int]) -> str:
    key = f"{attempt[0]}:{attempt[1]}:{attempt[2]}"
    return str(rep["tables"].get(str(prefix), {}).get(key, "inadmissible"))


def g4_f01(rep: dict[str, Any]) -> bool:
    expected_size = len(rep["probes"]) * len(rep["support"]) ** 2
    return bool(
        rep["tables"]
        and all(len(table) == expected_size for table in rep["tables"].values())
        and all(verdict in VERDICTS for table in rep["tables"].values() for verdict in table.values())
    )


def g4_obligation(rep: dict[str, Any], attempt: tuple[int, int, int] = O) -> bool:
    return bool(
        attempt[1] != attempt[2]
        and g4_lookup(rep, P_BASE, attempt) == "distinguished"
        and g4_lookup(rep, P_LOCK, attempt) == "distinguished"
    )


def g4_n01(rep: dict[str, Any], attempt: tuple[int, int, int] = N) -> bool:
    return g4_lookup(rep, P_OPEN_LOCK, attempt) != g4_lookup(rep, P_LOCK_OPEN, attempt)


def g4_counts(rep: dict[str, Any], prefix: int) -> tuple[int, int]:
    verdicts = list(rep["tables"].get(str(prefix), {}).values())
    return verdicts.count("distinguished"), verdicts.count("not_distinguished")


def g4_a0(rep: dict[str, Any]) -> dict[str, Any]:
    base = g4_counts(rep, P_BASE)
    opened = g4_counts(rep, P_OPEN)
    locked = g4_counts(rep, P_LOCK)
    open_delta = (opened[0] - base[0], opened[1] - base[1])
    lock_delta = (locked[0] - base[0], locked[1] - base[1])
    return {
        "open_delta": list(open_delta),
        "lock_delta": list(lock_delta),
        "A0_drive": bool(open_delta == (1, 0) and lock_delta == (0, 2) and open_delta != lock_delta),
    }


def g4_evaluate() -> dict[str, Any]:
    main = g4_build(RAW_STREAM)
    balanced = g4_build(BALANCED_STREAM)
    erased = g4_build(OBLIGATION_ERASED_STREAM)
    collapsed = g4_build(ORDER_COLLAPSED_STREAM)
    history_attacked = g4_build(HISTORY_PERMUTED_ERASED_STREAM)
    relabeled = g4_build(RELABELLED_STREAM)
    coarse = g4_build(COARSENED_STREAM)
    a0 = g4_a0(main)
    a0_negative = g4_a0(balanced)
    battery = {
        "F01": g4_f01(main),
        "N01": g4_n01(main),
        "obligation_retention": g4_obligation(main),
        "A0_drive": a0["A0_drive"],
        "A0_balanced_negative": a0_negative["A0_drive"],
    }
    raw_claims = {key: bool(battery[key]) for key in ("F01", "N01", "obligation_retention", "A0_drive")}
    coarsened_claims = {
        "F01": g4_f01(coarse),
        "N01": g4_n01(coarse, N_COARSE),
        "obligation_retention": g4_obligation(coarse, O_COARSE),
        "A0_drive": g4_a0(coarse)["A0_drive"],
    }
    raw_fed_to_coarsened_readout = {
        "F01": g4_f01(main),
        "N01": g4_n01(main, N_COARSE),
        "obligation_retention": g4_obligation(main, O_COARSE),
        "A0_drive": g4_a0(main)["A0_drive"],
    }
    resolution_evidence = resolution_claim_effect(raw_claims, coarsened_claims, raw_fed_to_coarsened_readout)
    history_evidence = history_control_effect(
        (g4_lookup(main, P_OPEN_LOCK, N), g4_lookup(main, P_LOCK_OPEN, N)),
        (g4_lookup(history_attacked, P_OPEN_LOCK, N), g4_lookup(history_attacked, P_LOCK_OPEN, N)),
        (int(prefix) for prefix in main["tables"]),
        (int(prefix) for prefix in history_attacked["tables"]),
    )
    controls = {
        "label_metadata_erasure": g4_obligation(relabeled, O_RELABELLED) and g4_n01(relabeled, N_RELABELLED),
        "anti_by_construction": g4_n01(main) and not g4_n01(collapsed) and a0["A0_drive"] and not a0_negative["A0_drive"],
        "order_commutation": g4_n01(main) and not g4_n01(collapsed),
        "history_memory": history_evidence["verdict"],
        "resolution": resolution_evidence["verdict"],
    }
    survived = bool(
        battery["F01"]
        and battery["N01"]
        and battery["obligation_retention"]
        and battery["A0_drive"]
        and not battery["A0_balanced_negative"]
    )
    return {
        "main": main,
        "battery": battery,
        "a0": a0,
        "a0_negative": a0_negative,
        "controls": controls,
        "resolution_evidence": resolution_evidence,
        "history_evidence": history_evidence,
        "survived": survived,
    }


def candidate_build_for_gradient(candidate: str, stream: Stream) -> dict[str, Any]:
    builders = {
        "G1": g1_build,
        "G2": g2_build,
        "G2P": g2p_build,
        "G3": g3_build,
        "G4": g4_build,
    }
    return builders[candidate](stream)


def candidate_lookup_for_gradient(
    candidate: str,
    rep: dict[str, Any],
    prefix: int,
    attempt: tuple[int, int, int],
) -> str:
    if candidate == "G1":
        return g1_lookup(rep, prefix, attempt)
    if candidate in {"G2", "G2P"}:
        return g2_observation(rep, prefix, attempt)
    if candidate == "G3":
        event = g3_event(rep, prefix, attempt)
        return str(event["verdict"]) if event is not None else "inadmissible"
    if candidate == "G4":
        return g4_lookup(rep, prefix, attempt)
    raise KeyError(f"unknown gradient candidate {candidate!r}")


def distinction_potential_value(
    candidate: str,
    rep: dict[str, Any],
    prefix: int,
    *,
    attempts: tuple[tuple[int, int, int], ...] = A0_RELEVANT_ATTEMPTS,
) -> int:
    """Evaluate the frozen finite V_{t,O} on one candidate-owned structure."""
    return sum(
        candidate_lookup_for_gradient(candidate, rep, prefix, attempt) == "unresolved"
        for attempt in attempts
    )


def measure_gradient_update(
    candidate: str,
    rep: dict[str, Any],
    update: AdmissibleGradientUpdate,
    *,
    attempts: tuple[tuple[int, int, int], ...] = A0_RELEVANT_ATTEMPTS,
) -> dict[str, Any]:
    before = distinction_potential_value(
        candidate,
        rep,
        update.source_prefix,
        attempts=attempts,
    )
    after = distinction_potential_value(
        candidate,
        rep,
        update.target_prefix,
        attempts=attempts,
    )
    signed_gradient = before - after
    return {
        "candidate": candidate,
        "update_id": update.update_id,
        "source_prefix": update.source_prefix,
        "target_prefix": update.target_prefix,
        "role": update.role,
        "obligation_attempts": [list(attempt) for attempt in attempts],
        "potential_before": before,
        "potential_after": after,
        "signed_gradient": signed_gradient,
        "magnitude": abs(signed_gradient),
        "tolerance": DISTINCTION_POTENTIAL.tolerance_epsilon,
        "gradient_witnessed": abs(signed_gradient) > DISTINCTION_POTENTIAL.tolerance_epsilon,
        "predicted_direction_observed": signed_gradient > DISTINCTION_POTENTIAL.tolerance_epsilon,
    }


def measure_declared_updates(
    candidate: str,
    rep: dict[str, Any],
    *,
    attempts: tuple[tuple[int, int, int], ...] = A0_RELEVANT_ATTEMPTS,
) -> dict[str, dict[str, Any]]:
    return {
        update.update_id: measure_gradient_update(
            candidate,
            rep,
            update,
            attempts=attempts,
        )
        for update in ADMISSIBLE_GRADIENT_UPDATES
    }


def injected_result_dependent_potential(evaluations: dict[str, dict[str, Any]]) -> int:
    """Deliberately hostile functional: it reads outcome fields and is unlicensed."""
    return len(CANDIDATE_IDS) - sum(
        int(bool(evaluations[candidate]["survived"]))
        for candidate in CANDIDATE_IDS
    )


def gradient_license_detector(potential_function: Callable[..., Any]) -> dict[str, Any]:
    registered_function = potential_function is distinction_potential_value
    code = potential_function.__code__
    code_surface = sorted(
        {
            str(value)
            for value in (*code.co_names, *code.co_varnames, *code.co_consts)
            if isinstance(value, (str, int, float, bool))
        }
    )
    result_markers = ("evaluations", "survived", "frontier", "selected", "outcome")
    result_dependent = any(
        marker in token.lower()
        for token in code_surface
        for marker in result_markers
    )
    failures: list[str] = []
    if not registered_function:
        failures.append("functional is not the preregistered distinction_potential_value callable")
    if result_dependent:
        failures.append("functional bytecode surface reads candidate outcome data")
    return {
        "callable": potential_function.__qualname__,
        "registered_callable": distinction_potential_value.__qualname__,
        "callable_identity_matches": registered_function,
        "code_surface": code_surface,
        "result_dependent": result_dependent,
        "frozen_before_outcomes": registered_function and DISTINCTION_POTENTIAL.frozen_before_outcomes,
        "detector_fired": bool(failures),
        "licensed": not failures,
        "intrinsic": not failures,
        "failures": failures,
    }


def classify_gradient_transition(
    *,
    licensed: bool,
    gradient_witnessed: bool,
    intrinsic: bool,
    obligation_coupled: bool,
    survivors: list[str],
    frontier: list[str],
    controls_pass: bool,
    context: str,
) -> dict[str, Any]:
    if not gradient_witnessed:
        decision = "HOLD_NO_GRADIENT"
        reason = f"{context}: measured magnitude is at or below the frozen tolerance."
    elif not intrinsic:
        decision = "HOLD_EXTRINSIC_DRIVE"
        reason = f"{context}: the potential is injected or result-dependent."
    elif not licensed or not controls_pass:
        decision = "HOLD_UNLICENSED_GRADIENT"
        reason = f"{context}: the functional or required control record is unlicensed."
    elif not obligation_coupled:
        decision = "HOLD_UNCOUPLED_GRADIENT"
        reason = f"{context}: no admissible candidate response couples to the frozen obligation."
    elif survivors and frontier:
        decision = "CLIMB"
        reason = f"{context}: licensed nonzero intrinsic obligation-coupled drive and frontier exist."
    else:
        decision = "REOPEN"
        reason = f"{context}: drive exists but the survivor/frontier prerequisite is absent."
    return {
        "executed": True,
        "decision": decision,
        "reason": reason,
        "selected_frontier_members": list(frontier) if decision == "CLIMB" else [],
        "evidence_tooth_recorded": decision == "CLIMB",
    }


def build_gradient_evidence(evaluations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    main_measurements = {
        candidate: measure_declared_updates(candidate, evaluations[candidate]["main"])
        for candidate in CANDIDATE_IDS
    }
    balanced_measurements = {
        candidate: measure_declared_updates(
            candidate,
            candidate_build_for_gradient(candidate, BALANCED_STREAM),
        )
        for candidate in CANDIDATE_IDS
    }
    relabelled_attempts = tuple(mapped_attempt(attempt) for attempt in A0_RELEVANT_ATTEMPTS)
    relabelled_measurements = {
        candidate: measure_declared_updates(
            candidate,
            candidate_build_for_gradient(candidate, RELABELLED_STREAM),
            attempts=relabelled_attempts,
        )
        for candidate in CANDIDATE_IDS
    }
    frozen_update = AdmissibleGradientUpdate(
        "frozen_base_identity",
        P_BASE,
        P_BASE,
        "freeze the licensed P_BASE -> P_OPEN change by replacing it with identity",
    )
    frozen_measurements = {
        candidate: measure_gradient_update(
            candidate,
            evaluations[candidate]["main"],
            frozen_update,
        )
        for candidate in CANDIDATE_IDS
    }
    closure_update = AdmissibleGradientUpdate(
        "closed_held_identity",
        P_HELD,
        P_HELD,
        "the held surface has satisfied the frozen A0 distinction demand; residual update is identity",
    )
    closed_measurements = {
        candidate: measure_gradient_update(
            candidate,
            evaluations[candidate]["main"],
            closure_update,
        )
        for candidate in CANDIDATE_IDS
    }
    swapped_obligation_measurements = {
        candidate: measure_gradient_update(
            candidate,
            evaluations[candidate]["main"],
            next(update for update in ADMISSIBLE_GRADIENT_UPDATES if update.update_id == LICENSED_DRIVE_UPDATE_ID),
            attempts=(O,),
        )
        for candidate in CANDIDATE_IDS
    }
    erased_obligation_measurements = {
        candidate: measure_gradient_update(
            candidate,
            evaluations[candidate]["main"],
            next(update for update in ADMISSIBLE_GRADIENT_UPDATES if update.update_id == LICENSED_DRIVE_UPDATE_ID),
            attempts=(),
        )
        for candidate in CANDIDATE_IDS
    }
    honest_license = gradient_license_detector(distinction_potential_value)
    injected_license = gradient_license_detector(injected_result_dependent_potential)
    injected_candidate_scores = {
        candidate: int(bool(evaluations[candidate]["survived"]))
        for candidate in CANDIDATE_IDS
    }
    injected_before = len(CANDIDATE_IDS)
    injected_after = injected_result_dependent_potential(evaluations)
    injected_variant = {
        "executed": True,
        "functional": "V_injected = candidate_count - sum(int(candidate.survived))",
        "candidate_outcome_scores": injected_candidate_scores,
        "potential_before": injected_before,
        "potential_after": injected_after,
        "magnitude": abs(injected_before - injected_after),
        "uses_result_fields": ["evaluations.*.survived", "computed_survivor_frontier"],
        "detector": injected_license,
    }
    selected_main = {
        candidate: main_measurements[candidate][LICENSED_DRIVE_UPDATE_ID]
        for candidate in CANDIDATE_IDS
    }
    selected_balanced = {
        candidate: balanced_measurements[candidate][LICENSED_DRIVE_UPDATE_ID]
        for candidate in CANDIDATE_IDS
    }
    selected_relabelled = {
        candidate: relabelled_measurements[candidate][LICENSED_DRIVE_UPDATE_ID]
        for candidate in CANDIDATE_IDS
    }
    coupling_eligible = {
        "G1": "contextual table update is directly candidate-operative",
        "G3": "event-incidence update is directly candidate-operative",
        "G4": "history-indexed table update is directly candidate-operative",
    }
    candidate_coupling_status = {
        candidate: {
            "coupled": candidate in coupling_eligible and selected_main[candidate]["predicted_direction_observed"],
            "reason": (
                coupling_eligible[candidate]
                if candidate in coupling_eligible
                else "G2/G2P quotient-time dynamics remain an explicit open attack; pre-quotient V is measured but not promoted to quotient-level coupling"
            ),
        }
        for candidate in CANDIDATE_IDS
    }
    honest_decision = classify_gradient_transition(
        licensed=honest_license["licensed"],
        gradient_witnessed=all(row["gradient_witnessed"] for row in selected_main.values()),
        intrinsic=honest_license["intrinsic"],
        obligation_coupled=any(row["coupled"] for row in candidate_coupling_status.values()),
        survivors=["G1", "G2P", "G3", "G4"],
        frontier=["G1"],
        controls_pass=True,
        context="honest licensed drive",
    )
    frozen_decision = classify_gradient_transition(
        licensed=True,
        gradient_witnessed=any(row["gradient_witnessed"] for row in frozen_measurements.values()),
        intrinsic=True,
        obligation_coupled=False,
        survivors=["G1", "G2P", "G3", "G4"],
        frontier=["G1"],
        controls_pass=True,
        context="gradient_freeze identity variant",
    )
    closed_decision = classify_gradient_transition(
        licensed=True,
        gradient_witnessed=any(row["gradient_witnessed"] for row in closed_measurements.values()),
        intrinsic=True,
        obligation_coupled=False,
        survivors=["G1", "G2P", "G3", "G4"],
        frontier=["G1"],
        controls_pass=True,
        context="gradient_closure held-surface variant",
    )
    injected_decision = classify_gradient_transition(
        licensed=injected_license["licensed"],
        gradient_witnessed=injected_variant["magnitude"] > DISTINCTION_POTENTIAL.tolerance_epsilon,
        intrinsic=injected_license["intrinsic"],
        obligation_coupled=True,
        survivors=["G1", "G2P", "G3", "G4"],
        frontier=["G1"],
        controls_pass=False,
        context="gradient_injection result-dependent variant",
    )
    swapped_obligation_decision = classify_gradient_transition(
        licensed=True,
        gradient_witnessed=any(row["gradient_witnessed"] for row in swapped_obligation_measurements.values()),
        intrinsic=True,
        obligation_coupled=False,
        survivors=["G1", "G2P", "G3", "G4"],
        frontier=["G1"],
        controls_pass=True,
        context="gradient_obligation_coupling replacement-obligation variant",
    )
    erased_obligation_decision = classify_gradient_transition(
        licensed=True,
        gradient_witnessed=any(row["gradient_witnessed"] for row in erased_obligation_measurements.values()),
        intrinsic=True,
        obligation_coupled=False,
        survivors=["G1", "G2P", "G3", "G4"],
        frontier=["G1"],
        controls_pass=True,
        context="gradient_obligation_coupling erased-obligation variant",
    )
    freeze_control = {
        "honest_side": {
            "executed": True,
            "measurements": selected_main,
            "nonzero": all(row["gradient_witnessed"] for row in selected_main.values()),
            "transition": honest_decision,
        },
        "frozen_side": {
            "executed": True,
            "manipulation": "replace licensed P_BASE -> P_OPEN with identity P_BASE -> P_BASE",
            "measurements": frozen_measurements,
            "gradient_collapsed": all(not row["gradient_witnessed"] for row in frozen_measurements.values()),
            "transition": frozen_decision,
        },
        "balanced_A0_side": {
            "executed": True,
            "stream_hash": sha256_json(stream_json(BALANCED_STREAM)),
            "measurements": selected_balanced,
            "gradient_collapsed": all(not row["gradient_witnessed"] for row in selected_balanced.values()),
            "A0_asymmetry_collapsed": all(not evaluations[candidate]["a0_negative"]["A0_drive"] for candidate in CANDIDATE_IDS),
            "genuine_role": "The balanced stream is the existing flat A0 inter-tendency witness, but it is not a literal freeze of the count-valued V; its nonzero V gradient is retained rather than relabeled as HOLD.",
        },
    }
    freeze_control["verdict"] = bool(
        freeze_control["honest_side"]["nonzero"]
        and freeze_control["frozen_side"]["gradient_collapsed"]
        and freeze_control["frozen_side"]["transition"]["decision"] == "HOLD_NO_GRADIENT"
        and freeze_control["balanced_A0_side"]["A0_asymmetry_collapsed"]
    )
    closure_control = {
        "open_obligation_side": {
            "executed": True,
            "measurements": selected_main,
            "residual_drive_present": all(row["gradient_witnessed"] for row in selected_main.values()),
            "transition": honest_decision,
        },
        "closed_or_removed_obligation_side": {
            "executed": True,
            "manipulation": "evaluate the candidate-owned P_HELD closure surface, where N/L1/L2 are resolved, under the residual identity P_HELD -> P_HELD",
            "measurements": closed_measurements,
            "residual_drive_collapsed": all(not row["gradient_witnessed"] for row in closed_measurements.values()),
            "transition": closed_decision,
        },
    }
    closure_control["verdict"] = bool(
        closure_control["open_obligation_side"]["residual_drive_present"]
        and closure_control["closed_or_removed_obligation_side"]["residual_drive_collapsed"]
        and closure_control["closed_or_removed_obligation_side"]["transition"]["decision"] == "HOLD_NO_GRADIENT"
    )
    injection_control = {
        "claim_scope": (
            "DEMO of one hostile instance: an object-identity whitelist fired on the shipped injected example; "
            "explicitly NOT a behavioral source-attribution test."
        ),
        "detector_kind": "object_identity_whitelist_demo",
        "behavioral_source_attribution_test": False,
        "honest_side": {
            "executed": True,
            "functional": DISTINCTION_POTENTIAL.functional,
            "detector": honest_license,
        },
        "injected_side": injected_variant,
    }
    injection_control["injected_side"]["transition"] = injected_decision
    injection_control["verdict"] = bool(
        honest_license["licensed"]
        and not injected_license["licensed"]
        and injected_license["detector_fired"]
        and injected_decision["decision"] == "HOLD_EXTRINSIC_DRIVE"
    )
    coupling_control = {
        "active_obligation_side": {
            "executed": True,
            "measurements": selected_main,
            "predicted_direction_candidates": [
                candidate
                for candidate, row in candidate_coupling_status.items()
                if row["coupled"]
            ],
            "candidate_coupling_status": candidate_coupling_status,
            "transition": honest_decision,
        },
        "erased_obligation_side": {
            "executed": True,
            "manipulation": "erase the frozen A0 attempt set so the obligation-relative domain is empty and recompute",
            "measurements": erased_obligation_measurements,
            "gradient_changed": {
                candidate: selected_main[candidate]["signed_gradient"]
                != erased_obligation_measurements[candidate]["signed_gradient"]
                for candidate in CANDIDATE_IDS
            },
            "transition": erased_obligation_decision,
        },
        "replacement_obligation_side": {
            "executed": True,
            "manipulation": "replace the frozen A0 attempt set {N,L1,L2} with retention attempt {O} and recompute on each candidate-owned structure",
            "measurements": swapped_obligation_measurements,
            "gradient_changed": {
                candidate: selected_main[candidate]["signed_gradient"]
                != swapped_obligation_measurements[candidate]["signed_gradient"]
                for candidate in CANDIDATE_IDS
            },
            "transition": swapped_obligation_decision,
        },
    }
    coupling_control["verdict"] = bool(
        coupling_control["active_obligation_side"]["predicted_direction_candidates"]
        and all(coupling_control["erased_obligation_side"]["gradient_changed"].values())
        and coupling_control["erased_obligation_side"]["transition"]["decision"] == "HOLD_NO_GRADIENT"
        and all(coupling_control["replacement_obligation_side"]["gradient_changed"].values())
        and coupling_control["replacement_obligation_side"]["transition"]["decision"] == "HOLD_NO_GRADIENT"
    )
    representation_robust = all(
        selected_main[candidate]["signed_gradient"] == selected_relabelled[candidate]["signed_gradient"]
        for candidate in CANDIDATE_IDS
    )
    controls = {
        "gradient_freeze": freeze_control,
        "gradient_closure": closure_control,
        "gradient_injection": injection_control,
        "gradient_obligation_coupling": coupling_control,
    }
    license_conditions = [
        {
            "condition": 1,
            "name": "typed",
            "passed": bool(
                DISTINCTION_POTENTIAL.functional
                and DISTINCTION_POTENTIAL.domain
                and DISTINCTION_POTENTIAL.codomain
                and DISTINCTION_POTENTIAL.orientation
                and DISTINCTION_POTENTIAL.sign_convention
                and DISTINCTION_POTENTIAL.frozen_before_outcomes
            ),
            "evidence": asdict(DISTINCTION_POTENTIAL),
        },
        {
            "condition": 2,
            "name": "licensed_at_current_rung",
            "passed": True,
            "evidence": "asserted by inspection, not computed: uses only finite candidate-owned verdict categories and counts; installs no entropy, metric, geometry, quotient, or continuum.",
        },
        {
            "condition": 3,
            "name": "nonzero",
            "passed": all(row["gradient_witnessed"] for row in selected_main.values()),
            "evidence": selected_main,
        },
        {
            "condition": 4,
            "name": "intrinsic",
            "passed": honest_license["licensed"] and injection_control["verdict"],
            "evidence": {
                "scope": "Condition-4 intrinsic evidence rests on this demo only; it is explicitly not a behavioral source-attribution test.",
                "demo": injection_control,
            },
        },
        {
            "condition": 5,
            "name": "obligation_coupled",
            "passed": coupling_control["verdict"],
            "evidence": coupling_control,
        },
        {
            "condition": 6,
            "name": "freeze_sensitive",
            "passed": freeze_control["verdict"],
            "evidence": freeze_control,
        },
        {
            "condition": 7,
            "name": "closure_sensitive",
            "passed": closure_control["verdict"],
            "evidence": closure_control,
        },
        {
            "condition": 8,
            "name": "representation_robust",
            "passed": representation_robust,
            "evidence": {
                "main": selected_main,
                "bijectively_relabelled": selected_relabelled,
                "existing_label_controls": {
                    candidate: evaluations[candidate]["controls"]["label_metadata_erasure"]
                    for candidate in CANDIDATE_IDS
                },
            },
        },
    ]
    return {
        "typed_potential": asdict(DISTINCTION_POTENTIAL),
        "admissible_updates": [asdict(update) for update in ADMISSIBLE_GRADIENT_UPDATES],
        "licensed_update_id": LICENSED_DRIVE_UPDATE_ID,
        "main_measurements": main_measurements,
        "balanced_measurements": balanced_measurements,
        "relabelled_measurements": relabelled_measurements,
        "selected_main": selected_main,
        "controls": controls,
        "license_conditions": license_conditions,
        "all_license_conditions_pass": all(row["passed"] for row in license_conditions),
        "honest_license_detector": honest_license,
        "candidate_coupling_status": candidate_coupling_status,
        "honest_transition": honest_decision,
    }


def gradient_control_rows(gradient_evidence: dict[str, Any]) -> list[dict[str, Any]]:
    expected = {
        "gradient_freeze": "The licensed P_BASE -> P_OPEN gradient is nonzero; replacing it by P_BASE -> P_BASE must compute zero and execute HOLD_NO_GRADIENT. The balanced stream remains an A0-flat but V-nonflat supplemental witness.",
        "gradient_closure": "The candidate-read P_HELD closure surface must have zero residual gradient and execute HOLD_NO_GRADIENT.",
        "gradient_injection": "DEMO only: the shipped deliberately result-dependent callable must make the object-identity whitelist fire and execute HOLD_EXTRINSIC_DRIVE; this is explicitly NOT a behavioral source-attribution test.",
        "gradient_obligation_coupling": "At least one operative candidate update reduces V in the predicted direction; erasing the obligation and replacing it with O must each change the measured gradient and execute HOLD_NO_GRADIENT.",
    }
    rows: list[dict[str, Any]] = []
    for family in (
        "gradient_freeze",
        "gradient_closure",
        "gradient_injection",
        "gradient_obligation_coupling",
    ):
        evidence = gradient_evidence["controls"][family]
        rows.append(
            {
                "family": family,
                "result": "pass" if evidence["verdict"] else "fail",
                "fired": True,
                "expected_effect": expected[family],
                "observed_effect": json.dumps(evidence, sort_keys=True),
                "both_sides_evidence": evidence,
            }
        )
    return rows


def run_candidate_evaluations() -> dict[str, dict[str, Any]]:
    # This controller dispatch aggregates only completed candidate-owned
    # receipts; it does not compute any candidate observable.
    return {
        "G1": g1_evaluate(),
        "G2": g2_evaluate(),
        "G2P": g2p_evaluate(),
        "G3": g3_evaluate(),
        "G4": g4_evaluate(),
    }


def root_smuggling_control(evaluations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    honest_representations = {candidate: evaluations[candidate]["main"] for candidate in CANDIDATE_IDS}
    honest_readouts = {
        candidate: {
            "obligation_retention": bool(evaluations[candidate]["battery"]["obligation_retention"]),
            "N01": bool(evaluations[candidate]["battery"]["N01"]),
        }
        for candidate in CANDIDATE_IDS
    }
    honest = root_independence_observation(honest_representations, honest_readouts)

    shared = merged_shared_build(RAW_STREAM)
    attacked_representations = {
        candidate: {
            "wrapper_candidate": candidate,
            "irrelevant_padding": index,
            "claim_bearing_table": shared,
        }
        for index, candidate in enumerate(CANDIDATE_IDS)
    }
    attacked_claim_bearing = {
        candidate: wrapper["claim_bearing_table"]
        for candidate, wrapper in attacked_representations.items()
    }
    attacked_readouts = {
        candidate: merged_shared_readout(attacked_claim_bearing[candidate])
        for candidate in CANDIDATE_IDS
    }
    attacked = root_independence_observation(
        attacked_representations,
        attacked_readouts,
        attacked_claim_bearing,
    )
    flip = bool(honest["passed"] and not attacked["passed"])
    return {
        "manipulation": "give every candidate a distinct wrapper with unique padding while forcing all claim-bearing readers to consume the same pre-built merged table object",
        "honest_side": honest,
        "attacked_side": attacked,
        "attacked_side_executed": attacked["executed"],
        "detected_failure": not attacked["passed"],
        "flip_observed": flip,
        "verdict": bool(honest["executed"] and attacked["executed"] and flip),
    }


def g1_projection_from_observations(rep: dict[str, Any]) -> dict[str, Any]:
    rows = tuple(
        (int(prefix), int(probe), int(mark_a), int(mark_b), str(verdict))
        for prefix, observations in rep["observations"].items()
        for probe, mark_a, mark_b, verdict in observations
    )
    return g1_build(rows)


def g1_projection_from_events(rep: dict[str, Any]) -> dict[str, Any]:
    rows = tuple(
        (
            int(event["history_prefix_index"]),
            int(event["probe"]),
            int(event["mark_a"]),
            int(event["mark_b"]),
            str(event["verdict"]),
        )
        for event in rep["events"]
    )
    return g1_build(rows)


def g1_projection_from_total_table(rep: dict[str, Any]) -> dict[str, Any]:
    rows: list[Record] = []
    for prefix, table in rep["tables"].items():
        for key in rep["observed_keys"][prefix]:
            verdict = table[key]
            probe, mark_a, mark_b = (int(part) for part in key.split(":"))
            rows.append((int(prefix), probe, mark_a, mark_b, str(verdict)))
    return g1_build(tuple(rows))


def projection_profile(rep: dict[str, Any]) -> dict[str, bool]:
    return {
        "F01": g1_f01(rep),
        "N01": g1_n01(rep),
        "obligation_retention": g1_obligation(rep),
        "A0_drive": g1_a0(rep)["A0_drive"],
    }


def projection_checks(evaluations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    g2_projection = g1_projection_from_observations(evaluations["G2"]["main"])
    g2p_projection = g1_projection_from_observations(evaluations["G2P"]["main"])
    g3_projection = g1_projection_from_events(evaluations["G3"]["main"])
    g4_projection = g1_projection_from_total_table(evaluations["G4"]["main"])
    g2p_probe_blind = g2_build(
        tuple(
            (int(prefix), int(probe), int(mark_a), int(mark_b), str(verdict))
            for prefix, observations in evaluations["G2P"]["main"]["observations"].items()
            for probe, mark_a, mark_b, verdict in observations
        )
    )
    exact_g1 = g1_build(RAW_STREAM)
    return [
        {
            "id": "G2_to_G1_forget_transitivity",
            "operator": "forget-transitivity",
            "source": "G2",
            "target": "G1",
            "executed": True,
            "preserves_obligation": g1_obligation(g2_projection),
            "projected_profile": projection_profile(g2_projection),
            "witness": "Dropped G2's probe-blind classes/equivalence/quotient and rebuilt a G1 contextual table from G2-owned observations; the projected G1 directly retains O.",
        },
        {
            "id": "G2P_to_G1_forget_transitivity",
            "operator": "forget-transitivity",
            "source": "G2P",
            "target": "G1",
            "executed": True,
            "preserves_obligation": g1_obligation(g2p_projection),
            "projected_profile": projection_profile(g2p_projection),
            "witness": "Dropped G2P's per-probe classes/equivalence/quotient and rebuilt G1 from G2P-owned observations; the projection retains O.",
        },
        {
            "id": "G3_to_G1_forget_incidence",
            "operator": "forget-incidence",
            "source": "G3",
            "target": "G1",
            "executed": True,
            "preserves_obligation": g1_obligation(g3_projection),
            "projected_profile": projection_profile(g3_projection),
            "witness": "Dropped G3 event ids, parent ids, and incidence edges, then rebuilt G1 from the remaining event records; O remains retained.",
        },
        {
            "id": "G4_to_G1_forget_totality",
            "operator": "forget-totality",
            "source": "G4",
            "target": "G1",
            "executed": True,
            "preserves_obligation": g1_obligation(g4_projection) and representation_payload_hash(g4_projection) == representation_payload_hash(exact_g1),
            "projected_profile": projection_profile(g4_projection),
            "projection_matches_exact_G1_payload": representation_payload_hash(g4_projection) == representation_payload_hash(exact_g1),
            "witness": "Used G4's observed-key provenance to drop only installed default cells, including all six genuinely observed inadmissible rows in the projection; the rebuilt candidate payload exactly matches G1 (source record order is non-claim metadata) and retains O.",
        },
        {
            "id": "G2P_to_G2_forget_probe_context",
            "operator": "forget-probe-context",
            "source": "G2P",
            "target": "G2",
            "executed": True,
            "preserves_obligation": g2_obligation(g2p_probe_blind),
            "projected_profile": {
                "F01": g2_f01(g2p_probe_blind),
                "N01": g2_n01(g2p_probe_blind),
                "obligation_retention": g2_obligation(g2p_probe_blind),
                "A0_drive": g2_a0(g2p_probe_blind)["A0_drive"],
            },
            "witness": "Forgot G2P's probe partition and recomputed one probe-blind closure. The executable weakening reproduces G2 and kills O, so it is registered as tested_killed rather than a strict weakness edge.",
        },
        {
            "id": "all_candidates_erase_labels",
            "operator": "erase-labels",
            "source": "G1,G2,G2P,G3,G4",
            "target": "index-isomorphic candidate-owned presentations",
            "executed": True,
            "preserves_obligation": all(
                evaluations[candidate]["controls"]["label_metadata_erasure"]
                for candidate in CANDIDATE_IDS
            ),
            "witness": "Every family independently rebuilt from the bijectively relabeled stream and reproduced its own mapped obligation/N01 outcome.",
        },
    ]


def weakening_coverage() -> list[dict[str, str]]:
    tested = {
        ("G1", "erase-labels"): "tested_survivor",
        ("G2", "forget-transitivity"): "tested_survivor",
        ("G2", "erase-labels"): "tested_killed",
        ("G2P", "forget-transitivity"): "tested_survivor",
        ("G2P", "forget-probe-context"): "tested_killed",
        ("G2P", "erase-labels"): "tested_survivor",
        ("G3", "forget-incidence"): "tested_survivor",
        ("G3", "erase-labels"): "tested_survivor",
        ("G4", "forget-totality"): "tested_survivor",
        ("G4", "erase-labels"): "tested_survivor",
    }
    rows: list[dict[str, str]] = []
    for candidate in CANDIDATE_IDS:
        for operator in LOCAL_WEAKENINGS:
            status = tested.get((candidate, operator), "undefined")
            detail = (
                f"Candidate-local {operator} check returned {status.replace('_', ' ')}."
                if status != "undefined"
                else f"{operator} is not a defined one-step weakening of {candidate} in this finite grammar."
            )
            rows.append({"candidate": candidate, "operator": operator, "status": status, "detail": detail})
    return rows


def installed_weakening_results(evaluations: dict[str, dict[str, Any]], projections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    projection_by_id = {row["id"]: row for row in projections}
    executed = [
        ("erase_primitive", not g1_obligation(g1_build(OBLIGATION_ERASED_STREAM)), "A fresh G1 rebuild from the obligation-erased stream loses O; this computation is independent of the merged-shared-structure attack."),
        ("forget_structure", all(projection_by_id[key]["preserves_obligation"] for key in ("G2_to_G1_forget_transitivity", "G2P_to_G1_forget_transitivity", "G3_to_G1_forget_incidence", "G4_to_G1_forget_totality")), "Four source-specific projections independently discard quotient, incidence, or totality structure and rebuild G1 while retaining O."),
        ("quotient_marks", evaluations["G2"]["controls"]["probe_quotient"] and evaluations["G2P"]["controls"]["probe_quotient"], "Fresh probe erasure resurrects O in probe-blind G2 and preserves probe-local O in rebuilt G2P; the two quotient choices remain distinct."),
        ("restrict_operations", all(evaluations[c]["controls"]["order_commutation"] for c in CANDIDATE_IDS), "The order-collapsed stream removes every candidate-owned N01 witness."),
        ("reduce_history", all(evaluations[c]["controls"]["history_memory"] for c in CANDIDATE_IDS), "A separate hostile stream swaps the two order-bearing history prefixes and erases the full held segment; every candidate's checked order pair reverses and the segment disappears."),
        ("coarsen_resolution", all(evaluations[c]["controls"]["resolution"] for c in CANDIDATE_IDS), "The genuine two-bin stream preserves F01/N01/A0 while breaking O for G1/G2P/G3/G4 and preserving G2's prior O=false; raw substitution changes the coarsened-side readout."),
        ("remove_equivalence_closure", projection_by_id["G2_to_G1_forget_transitivity"]["preserves_obligation"] and projection_by_id["G2P_to_G1_forget_transitivity"]["preserves_obligation"], "Dropping either quotient's closure fields and rebuilding G1 from candidate-owned observations retains O; this is an independent lower-structure computation."),
    ]
    rows = [
        {"operator": operator, "status": "tested" if passed else "failed", "executed": True, "observed": observed}
        for operator, passed, observed in executed
    ]
    undefined = {
        "reduce_locality": "No locality or adjacency structure is installed.",
        "carrier_substitution": "Rival carrier families are not yet formalized.",
        "algebra_restriction": "No algebra is installed.",
        "remove_independent_entropy_geometry_fields": "No independent entropy or geometry fields are installed.",
    }
    rows.extend(
        {"operator": operator, "status": "undefined", "executed": False, "observed": reason}
        for operator, reason in undefined.items()
    )
    return rows


def negative_results(
    evaluations: dict[str, dict[str, Any]],
    root_evidence: dict[str, Any],
    lineage_evidence: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in CANDIDATE_IDS:
        evaluation = evaluations[candidate]
        rows.append(
            {
                "id": f"{candidate}_A0_balanced",
                "family": candidate,
                "variant_stream_hash": sha256_json(stream_json(BALANCED_STREAM)),
                "expected": "A0_drive=false",
                "result": "pass" if not evaluation["a0_negative"]["A0_drive"] else "fail",
                "observed": evaluation["a0_negative"],
            }
        )
        rows.append(
            {
                "id": f"{candidate}_order_collapsed",
                "family": candidate,
                "variant_stream_hash": sha256_json(stream_json(ORDER_COLLAPSED_STREAM)),
                "expected": "N01=false",
                "result": "pass" if evaluation["controls"]["order_commutation"] else "fail",
            }
        )
        rows.append(
            {
                "id": f"{candidate}_history_permuted_erased",
                "family": candidate,
                "variant_stream_hash": sha256_json(stream_json(HISTORY_PERMUTED_ERASED_STREAM)),
                "expected": "order pair reverses and P_HELD segment is erased",
                "result": "pass" if evaluation["controls"]["history_memory"] else "fail",
                "observed": evaluation["history_evidence"],
            }
        )
        rows.append(
            {
                "id": f"{candidate}_resolution_coarsened",
                "family": candidate,
                "variant_stream_hash": sha256_json(stream_json(COARSENED_STREAM)),
                "expected": "coarsened-side profile matches prediction and changes when RAW_STREAM is substituted",
                "result": "pass" if evaluation["controls"]["resolution"] else "fail",
                "observed": evaluation["resolution_evidence"],
            }
        )
    rows.append(
        {
            "id": "ALL_root_smuggling_merged_shared_structure",
            "family": "G1,G2,G2P,G3,G4",
            "variant_stream_hash": sha256_json(stream_json(RAW_STREAM)),
            "expected": "honest independent construction passes; forced common pre-built table is detected and fails",
            "result": "pass" if root_evidence["verdict"] else "fail",
            "observed": root_evidence,
        }
    )
    rows.append(
        {
            "id": "ALL_lineage_stale_v0_1_receipt_hash",
            "family": "G1,G2,G2P,G3,G4",
            "expected": "honest frozen hashes pass; one stale predecessor source hash fails closed",
            "result": "pass" if lineage_evidence["verdict"] else "fail",
            "observed": lineage_evidence,
        }
    )
    return rows


def control_rows(
    evaluations: dict[str, dict[str, Any]],
    root_evidence: dict[str, Any],
    lineage_evidence: dict[str, Any],
    projections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    projection_by_id = {row["id"]: row for row in projections}
    lower_projection_ids = {
        "G2": "G2_to_G1_forget_transitivity",
        "G2P": "G2P_to_G1_forget_transitivity",
        "G3": "G3_to_G1_forget_incidence",
        "G4": "G4_to_G1_forget_totality",
    }
    lower_per_candidate = {
        candidate: bool(projection_by_id[projection_id]["executed"] and projection_by_id[projection_id]["preserves_obligation"])
        for candidate, projection_id in lower_projection_ids.items()
    }
    rows: list[dict[str, Any]] = [
        {
            "family": "root_smuggling",
            "result": "pass" if root_evidence["verdict"] else "fail",
            "fired": True,
            "expected_effect": "Independent candidate builds pass; forcing all readers through one common pre-built merged table must be detected as a failed independence check.",
            "observed_effect": json.dumps(root_evidence, sort_keys=True),
            "per_candidate": {
                "honest": {candidate: root_evidence["honest_side"]["passed"] for candidate in CANDIDATE_IDS},
                "attacked": {candidate: root_evidence["attacked_side"]["passed"] for candidate in CANDIDATE_IDS},
            },
        },
        {
            "family": "lineage_freshness",
            "result": "pass" if lineage_evidence["verdict"] else "fail",
            "fired": True,
            "expected_effect": "The exact frozen v0/v0.1 hashes pass; staling the v0.1 receipt source hash must fail closed.",
            "observed_effect": json.dumps(lineage_evidence, sort_keys=True),
        },
        {
            "family": "lower_structure",
            "result": "pass" if all(lower_per_candidate.values()) else "fail",
            "fired": True,
            "expected_effect": "Source-specific projections must independently drop G2/G2P closure, G3 incidence, and G4 totality, rebuild G1, and retain O. G1 has no registered lower candidate in this finite grammar.",
            "observed_effect": json.dumps(
                {
                    "per_candidate": lower_per_candidate,
                    "G1": {"status": "undefined", "reason": "no registered strictly lower candidate in this finite grammar"},
                    "projection_ids": lower_projection_ids,
                },
                sort_keys=True,
            ),
            "per_candidate": lower_per_candidate,
        },
        {
            "family": "history_memory",
            "result": "pass" if all(evaluations[c]["controls"]["history_memory"] for c in CANDIDATE_IDS) else "fail",
            "fired": True,
            "expected_effect": "A distinct hostile stream swaps the two order-bearing history prefixes and erases P_HELD; every candidate must reverse its checked order pair and lose that segment.",
            "observed_effect": json.dumps({c: evaluations[c]["history_evidence"] for c in CANDIDATE_IDS}, sort_keys=True),
            "per_candidate": {c: evaluations[c]["controls"]["history_memory"] for c in CANDIDATE_IDS},
        },
        {
            "family": "resolution",
            "result": "pass" if all(evaluations[c]["controls"]["resolution"] for c in CANDIDATE_IDS) else "fail",
            "fired": True,
            "expected_effect": "Rebuild from the genuine two-bin mark stream; report each F01/N01/O/A0 persistence transition, then substitute RAW_STREAM into the coarsened-side readout and require a changed outcome.",
            "observed_effect": json.dumps({c: evaluations[c]["resolution_evidence"] for c in CANDIDATE_IDS}, sort_keys=True),
            "per_candidate": {c: evaluations[c]["controls"]["resolution"] for c in CANDIDATE_IDS},
        },
    ]
    applicable = {
        "label_metadata_erasure": list(CANDIDATE_IDS),
        "anti_by_construction": list(CANDIDATE_IDS),
        "probe_quotient": ["G2", "G2P"],
        "order_commutation": list(CANDIDATE_IDS),
    }
    expected = {
        "label_metadata_erasure": "Each family must rebuild from a bijectively relabeled stream and preserve its mapped outcome.",
        "anti_by_construction": "Each family must reach both sides of its decisive outcome, including A0_drive=true on the main stream and false on the balanced stream.",
        "probe_quotient": "G2 and G2P must rebuild after probe erasure: probe-blind G2 changes O false-to-true, while probe-respecting G2P preserves probe-0 O and removes probe-1 state.",
        "order_commutation": "Each family must lose N01 after rebuilding from the order-collapsed stream.",
    }
    for family, candidates in applicable.items():
        per_candidate = {candidate: bool(evaluations[candidate]["controls"][family]) for candidate in candidates}
        passed = all(per_candidate.values())
        observed = {
            "per_candidate": per_candidate,
            "A0_main": {candidate: evaluations[candidate]["a0"] for candidate in CANDIDATE_IDS}
            if family == "anti_by_construction"
            else None,
            "A0_balanced": {candidate: evaluations[candidate]["a0_negative"] for candidate in CANDIDATE_IDS}
            if family == "anti_by_construction"
            else None,
        }
        rows.append(
            {
                "family": family,
                "result": "pass" if passed else "fail",
                "fired": True,
                "expected_effect": expected[family],
                "observed_effect": json.dumps(observed, sort_keys=True),
                "per_candidate": per_candidate,
            }
        )
    not_applicable = {
        "carrier_family": "Rival non-isomorphic carrier families remain unformalized; this is carried as an open attack.",
        "topology_locality": "No topology, adjacency, or locality claim is installed in the raw stream.",
        "entropy_geometry_split": "A0 is pre-entropic and no entropy or geometry state is installed.",
        "field_vs_token": "No token or configuration-field dynamics claim is made.",
        "held_out_contact": "The frozen finite stream makes no held-out prediction claim.",
    }
    rows.extend(
        {
            "family": family,
            "result": "not_applicable",
            "fired": False,
            "expected_effect": "No effect is predicted inside this frozen root-presentation scope.",
            "observed_effect": reason,
            "justification": reason,
        }
        for family, reason in not_applicable.items()
    )
    return rows


def kernel_survivors(receipt: dict[str, Any]) -> list[str]:
    ids = [candidate["id"] for candidate in receipt["candidates"]]
    for size in range(len(ids) + 1):
        for subset in itertools.combinations(ids, size):
            probe = copy.deepcopy(receipt)
            probe["survivors"] = list(subset)
            probe["declared_frontier"] = [ids[0]]
            errors = validate_receipt(probe)
            survivor_errors = [error for error in errors if error.startswith("survivors ")]
            if not survivor_errors:
                return list(subset)
    raise RuntimeError("ratchet kernel did not accept any survivor declaration")


def kernel_frontier(receipt: dict[str, Any], survivors: list[str]) -> list[str]:
    for size in range(1, len(survivors) + 1):
        for subset in itertools.combinations(survivors, size):
            probe = copy.deepcopy(receipt)
            probe["survivors"] = survivors
            probe["declared_frontier"] = list(subset)
            errors = validate_receipt(probe)
            frontier_errors = [error for error in errors if error.startswith("declared_frontier")]
            if not frontier_errors:
                return list(subset)
    raise RuntimeError("ratchet kernel did not accept any non-empty frontier declaration")


def frozen_predecessor_evidence() -> dict[str, Any]:
    manifest_path = HERE / "graveyard/SHA256SUMS"
    expected_entries = {
        "graveyard/packet_v0_postrepair_frozen_20260710.py": "0cd05bc69805840dae0aea540df82cc9fa86fb413a8712ca81c395e55e90f9d3",
        "graveyard/receipt_v0_postrepair_frozen_20260710.json": "3d3230bcb0d4e4b6497e36e5c73d3035db0348c125c2fa75ee17e3a1f84ff706",
        "graveyard/packet_v0_1_frozen_20260710.py": "deeda38abaa413a8020c6a7e586f6a0c4d898b5c7d2cb2f83d322bd0f050550a",
        "graveyard/receipt_v0_1_frozen_20260710.json": "c39a6aa6cd2f3e48befe9a9e677dee6e0cff0bd57676dc9c9b3196b4e199b819",
    }
    manifest_entries: dict[str, str] = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(maxsplit=1)
        manifest_entries[relative.strip()] = digest
    if any(manifest_entries.get(relative) != digest for relative, digest in expected_entries.items()):
        raise RuntimeError("graveyard/SHA256SUMS does not cite both frozen predecessor pairs exactly")

    verified_entries: dict[str, dict[str, Any]] = {}
    for relative, expected_hash in expected_entries.items():
        path = HERE / relative
        actual_hash = sha256_bytes(path.read_bytes())
        if actual_hash != expected_hash:
            raise RuntimeError(f"frozen predecessor evidence changed: {path}")
        verified_entries[relative] = {
            "path": str(path.relative_to(BUNDLE_ROOT)),
            "sha256": actual_hash,
            "verified": True,
        }
    findings_path = HERE / "graveyard/AUDIT_FINDINGS_v0_20260710.md"
    return {
        "checksum_manifest": {
            "path": str(manifest_path.relative_to(BUNDLE_ROOT)),
            "sha256": sha256_bytes(manifest_path.read_bytes()),
            "verified": True,
        },
        "audit_findings": {
            "path": str(findings_path.relative_to(BUNDLE_ROOT)),
            "sha256": sha256_bytes(findings_path.read_bytes()),
            "verified_present": True,
        },
        "v0": {
            "receipt_id": "root_presentation_packet_v0.seed0.001",
            "packet": verified_entries["graveyard/packet_v0_postrepair_frozen_20260710.py"],
            "receipt": verified_entries["graveyard/receipt_v0_postrepair_frozen_20260710.json"],
        },
        "v0_1": {
            "receipt_id": "root_presentation_packet_v0_1.seed0.002",
            "packet": verified_entries["graveyard/packet_v0_1_frozen_20260710.py"],
            "receipt": verified_entries["graveyard/receipt_v0_1_frozen_20260710.json"],
        },
    }


def lineage_freshness_control(predecessor_evidence: dict[str, Any]) -> dict[str, Any]:
    expected = {
        ("v0", "packet"): "0cd05bc69805840dae0aea540df82cc9fa86fb413a8712ca81c395e55e90f9d3",
        ("v0", "receipt"): "3d3230bcb0d4e4b6497e36e5c73d3035db0348c125c2fa75ee17e3a1f84ff706",
        ("v0_1", "packet"): "deeda38abaa413a8020c6a7e586f6a0c4d898b5c7d2cb2f83d322bd0f050550a",
        ("v0_1", "receipt"): "c39a6aa6cd2f3e48befe9a9e677dee6e0cff0bd57676dc9c9b3196b4e199b819",
    }

    def gate(evidence: dict[str, Any]) -> bool:
        return all(
            evidence[version][artifact]["verified"] is True
            and evidence[version][artifact]["sha256"] == digest
            for (version, artifact), digest in expected.items()
        )

    honest = gate(predecessor_evidence)
    attacked_evidence = copy.deepcopy(predecessor_evidence)
    attacked_evidence["v0_1"]["receipt"]["sha256"] = "0" * 64
    attacked = gate(attacked_evidence)
    return {
        "manipulation": "stale the frozen v0.1 predecessor receipt source hash in the in-memory lineage evidence",
        "honest_side": {"executed": True, "passed": honest},
        "attacked_side": {
            "executed": True,
            "passed": attacked,
            "mutated_field": "predecessor_evidence.v0_1.receipt.sha256",
        },
        "detected_failure": not attacked,
        "flip_observed": bool(honest and not attacked),
        "verdict": bool(honest and not attacked),
    }


def build_receipt() -> dict[str, Any]:
    packet_sha = sha256_bytes(Path(__file__).read_bytes())
    predecessor_evidence = frozen_predecessor_evidence()
    lineage_evidence = lineage_freshness_control(predecessor_evidence)
    evaluations = run_candidate_evaluations()
    gradient_evidence = build_gradient_evidence(evaluations)
    projections = projection_checks(evaluations)
    projection_by_id = {row["id"]: row for row in projections}
    root_evidence = root_smuggling_control(evaluations)
    controls = control_rows(evaluations, root_evidence, lineage_evidence, projections)
    controls.extend(gradient_control_rows(gradient_evidence))
    negatives = negative_results(evaluations, root_evidence, lineage_evidence)
    installed_results = installed_weakening_results(evaluations, projections)
    candidate_spec = {
        "families": [
            "contextual_partial_distinction_table",
            "probe_blind_support_equivalence_quotient",
            "probe_respecting_support_equivalence_quotient",
            "pre_object_event_incidence",
            "history_indexed_order_table",
        ],
        "builder_input": "only tuple[history_prefix_index, probe, mark_a, mark_b, verdict] records",
        "negative_per_family": True,
    }
    weakening_spec = {
        "local_operators": list(LOCAL_WEAKENINGS),
        "installed_source_operators": list(INSTALLED_WEAKENINGS),
        "projection_witnesses": projections,
    }
    battery_spec = {
        "tests": ["F01", "N01", "A0_drive", "obligation_retention"],
        "controls": [row["family"] for row in controls],
        "negative_variants": [row["id"] for row in negatives],
    }
    data_spec = {
        "seed": SEED,
        "schema": ["history_prefix_index", "probe", "mark_a", "mark_b", "verdict"],
        "allowed_verdicts": list(VERDICTS),
        "ground_truth_kind": "immutable_python_tuple_stream",
        "persistent_state_tensor": False,
        "records": stream_json(RAW_STREAM),
        "stream_sha256": sha256_json(stream_json(RAW_STREAM)),
        "hostile_variant_hashes": {
            "balanced_A0": sha256_json(stream_json(BALANCED_STREAM)),
            "obligation_erased": sha256_json(stream_json(OBLIGATION_ERASED_STREAM)),
            "order_collapsed": sha256_json(stream_json(ORDER_COLLAPSED_STREAM)),
            "history_permuted_erased": sha256_json(stream_json(HISTORY_PERMUTED_ERASED_STREAM)),
            "probe1_erased": sha256_json(stream_json(PROBE1_ERASED_STREAM)),
            "relabeled": sha256_json(stream_json(RELABELLED_STREAM)),
            "coarsened": sha256_json(stream_json(COARSENED_STREAM)),
        },
    }
    open_attacks = [
        "D2 nonassociativity remains open: it may be an evolving constraint, and the rung reopens if a future obligation makes it load-bearing.",
        "rival carrier families not yet formalized",
        "reduce_locality: no locality or adjacency structure is installed, so this weakening could not be executed as a claim-bearing projection",
        "carrier_substitution: rival carrier families are not yet formalized, so this weakening could not be executed",
        "algebra_restriction: no algebra is installed, so this weakening could not be executed as a claim-bearing projection",
        "remove_independent_entropy_geometry_fields: no independent entropy or geometry fields are installed, so this weakening could not be executed",
        "G2/G2P quotient-time semantics remain open: both read A0 from candidate-owned pre-quotient observations. G2P shows a quotient can retain O when probe-respecting, but quotient-level dynamics carrying A0 have not been tested.",
        "local forget-symmetry remains undefined for G2/G2P: no directed non-symmetric closure candidate is registered, and remove-equivalence-closure does not discharge that distinct weakening.",
        "candidate-local restrict-history projections remain undefined: the executed history_memory hostile control is not claimed as a strict obligation-preserving weakness witness.",
        "gradient_injection detector is an object-identity whitelist, killed by direct adversarial test (renamed clone, honest wrapper falsely rejected, monkey-patched constant certified); a behavioral source-attribution test per the NVIDIA referee finding 4 is future work; condition-4 intrinsic evidence is demo-grade until then.",
    ]
    candidates: list[dict[str, Any]] = []
    family_names = {
        "G1": "contextual_partial_distinction_table",
        "G2": "probe_blind_support_equivalence_quotient",
        "G2P": "probe_respecting_support_equivalence_quotient",
        "G3": "pre_object_event_incidence",
        "G4": "history_indexed_order_table",
    }
    assumptions = {
        "G1": ["finite attempt records", "contextual partial directed table", "no closure laws"],
        "G2": ["support derived from observed marks", "probe-blind equivalence closure across all probes", "fresh quotient classes"],
        "G2P": ["support derived separately per probe", "probe-respecting equivalence closure", "fresh per-probe quotient classes"],
        "G3": ["finite attempt events", "candidate-local baseline incidence", "no total table"],
        "G4": ["finite prefix indices", "candidate-installed inadmissible defaults", "no shared persistence flag"],
    }
    for candidate in CANDIDATE_IDS:
        row = {
            "id": candidate,
            "family": family_names[candidate],
            "survived": evaluations[candidate]["survived"],
            "assumptions": assumptions[candidate],
            "builder_input": "RAW_STREAM only",
            "representation_kind": evaluations[candidate]["main"]["kind"],
            "battery": evaluations[candidate]["battery"],
            "A0_witness": evaluations[candidate]["a0"],
            "A0_balanced_negative": evaluations[candidate]["a0_negative"],
            "control_results": evaluations[candidate]["controls"],
            "resolution_evidence": evaluations[candidate]["resolution_evidence"],
            "history_evidence": evaluations[candidate]["history_evidence"],
            "gradient_measurements": gradient_evidence["main_measurements"][candidate],
        }
        if candidate == "G2" and evaluations[candidate].get("defeat_reason"):
            row["defeat_reason"] = evaluations[candidate]["defeat_reason"]
        candidates.append(row)
    receipt: dict[str, Any] = {
        "schema_version": "ratchet-run/0.3",
        "receipt": {
            "id": "root_presentation_packet_v0_3.seed0.004",
            "generated_at": "2026-07-10T00:00:00Z",
            "append_only": True,
            "self_adjudicating": False,
        },
        "lineage": {
            "predecessor_receipts": ["root_presentation_packet_v0.seed0.001", "root_presentation_packet_v0_1.seed0.002"],
            "predecessor_evidence": predecessor_evidence,
            "constraint_hash": "sha256:" + sha256_json(
                {
                    "F01": "finite",
                    "N01": "order-sensitive",
                    "A0": "opening-locking",
                    "gradient_drive": "licensed finite obligation-coupled distinction potential",
                }
            ),
            "obligation_hash": "sha256:" + sha256_json(
                {
                    "probe": O[0],
                    "marks": list(O[1:]),
                    "history_prefix_index": P_LOCK,
                    "A0_relevant_attempts": [list(attempt) for attempt in A0_RELEVANT_ATTEMPTS],
                    "licensed_drive_update": LICENSED_DRIVE_UPDATE_ID,
                }
            ),
            "code_hash": "sha256:" + packet_sha,
            "packet_py_sha256": packet_sha,
            "data_hash": "sha256:" + sha256_json(data_spec),
            "test_battery_hash": "sha256:" + sha256_json(battery_spec),
            "candidate_grammar_hash": "sha256:" + sha256_json(candidate_spec),
            "weakening_grammar_hash": "sha256:" + sha256_json(weakening_spec),
            "independent_audit": {
                "performed": False,
                "auditor": "",
                "freshness": "v0.3 schema migration is frozen after verification; final fresh independent audit is pending.",
                "found_fabrication": None,
            },
        },
        "claim": {
            "id": "root_presentation_packet_v0_3",
            "text": "Within the frozen finite grammar and battery, compare independently built stream-only root presentations including probe-blind G2 and probe-respecting G2P, execute real hostile flips, and compute the minimal-survivor frontier.",
            "obligation": "Retain the constrained distinction at attempt (0,0,1) through lock prefix 2 without a shared carrier, and expose the pre-entropic A0 asymmetry to a balanced negative.",
            "claim_ceiling": "scratch_diagnostic",
        },
        "root": {
            "primitive": "constrained_distinguishability",
            "presumes_objects": False,
            "presumes_equivalence": False,
            "relation_total": False,
            "ground_truth": "one immutable finite distinction-attempt tuple stream",
            "persistent_state_tensor": False,
        },
        "drive": {
            "kind": "distinction_gradient",
            "entropy_type": "untyped_root_precursor",
            "licensed": gradient_evidence["all_license_conditions_pass"],
            "functional": DISTINCTION_POTENTIAL.functional,
            "orientation": DISTINCTION_POTENTIAL.orientation + "; " + DISTINCTION_POTENTIAL.sign_convention,
            "potential_before": gradient_evidence["selected_main"]["G1"]["potential_before"],
            "potential_after": gradient_evidence["selected_main"]["G1"]["potential_after"],
            "magnitude": gradient_evidence["selected_main"]["G1"]["magnitude"],
            "tolerance": DISTINCTION_POTENTIAL.tolerance_epsilon,
            "gradient_witnessed": gradient_evidence["selected_main"]["G1"]["gradient_witnessed"],
            "intrinsic": gradient_evidence["honest_license_detector"]["intrinsic"],
            "obligation_coupled": gradient_evidence["controls"]["gradient_obligation_coupling"]["verdict"],
            "witness": (
                "Each candidate-owned P_BASE surface has three unresolved frozen A0-relevant distinctions and its "
                "recorded P_OPEN successor has two, so g=3-2=1. G1, G3, and G4 have direct operative coupling; "
                "G2/G2P retain measured pre-quotient gradients but coupled=false because quotient-time dynamics "
                "remain an open attack. Frozen, closed, injected, obligation-swapped, balanced, and relabelled "
                "variants execute separately."
            ),
            "candidate_responses": [
                {
                    "candidate": candidate,
                    "delta": gradient_evidence["selected_main"][candidate]["signed_gradient"],
                    "coupled": gradient_evidence["candidate_coupling_status"][candidate]["coupled"],
                    "coupling_reason": gradient_evidence["candidate_coupling_status"][candidate]["reason"],
                }
                for candidate in CANDIDATE_IDS
            ],
            "typed_potential": gradient_evidence["typed_potential"],
            "admissible_updates": gradient_evidence["admissible_updates"],
            "licensed_update_id": gradient_evidence["licensed_update_id"],
            "gradient_measurements_per_candidate": gradient_evidence["main_measurements"],
            "per_candidate_balanced_flat": gradient_evidence["balanced_measurements"],
            "license_conditions": gradient_evidence["license_conditions"],
            "legacy_A0_record": {
                "id": "A0",
                "declaration": "Pre-entropic asymmetry between distinction-opening and distinction-locking record deltas; no entropy functional is selected.",
                "discharged_by_obligation": True,
                "per_candidate_positive": {candidate: evaluations[candidate]["a0"] for candidate in CANDIDATE_IDS},
                "per_candidate_balanced_negative": {candidate: evaluations[candidate]["a0_negative"] for candidate in CANDIDATE_IDS},
            },
        },
        "finite_scope": {
            "candidate_limit": 8,
            "test_limit": 64,
            "history_limit": 5,
            "resolution_limit": len(MARKS),
            "budget_label": "root-presentation-v0.3-schema-migration-seed0-finite-no-hardening",
            "marks": len(MARKS),
            "probes": len(PROBES),
            "prefixes": len(PREFIXES),
            "records": len(RAW_STREAM),
        },
        "data_spec": data_spec,
        "candidate_grammar": {
            "id": "root-presentation-candidates-v0.2",
            "hash": "sha256:" + sha256_json(candidate_spec),
            "families": candidate_spec["families"],
            "globally_complete": False,
        },
        "weakening_grammar": {
            "id": "root-presentation-local-weakenings-v0.2",
            "hash": "sha256:" + sha256_json(weakening_spec),
            "operators": list(LOCAL_WEAKENINGS),
            "globally_complete": False,
            "source_grammar": "ratchet/weakening_grammar.json",
            "operator_mapping": {
                "forget-transitivity": ["forget_structure", "remove_equivalence_closure"],
                "forget-symmetry": ["forget_structure", "remove_equivalence_closure"],
                "forget-totality": ["forget_structure"],
                "forget-incidence": ["forget_structure"],
                "forget-probe-context": ["quotient_marks"],
                "restrict-history": ["reduce_history"],
                "erase-labels": [],
            },
        },
        "candidates": candidates,
        "weakness_edges": [
            {
                "weaker": "G1",
                "stronger": "G2",
                "operator": "forget-transitivity",
                "witness": projection_by_id["G2_to_G1_forget_transitivity"]["witness"],
                "preserves_obligation": True,
            },
            {
                "weaker": "G1",
                "stronger": "G2P",
                "operator": "forget-transitivity",
                "witness": projection_by_id["G2P_to_G1_forget_transitivity"]["witness"],
                "preserves_obligation": True,
            },
            {
                "weaker": "G1",
                "stronger": "G3",
                "operator": "forget-incidence",
                "witness": projection_by_id["G3_to_G1_forget_incidence"]["witness"],
                "preserves_obligation": True,
            },
            {
                "weaker": "G1",
                "stronger": "G4",
                "operator": "forget-totality",
                "witness": projection_by_id["G4_to_G1_forget_totality"]["witness"],
                "preserves_obligation": True,
            },
        ],
        "projection_checks": projections,
        "installed_weakening_results": installed_results,
        "weakening_coverage": weakening_coverage(),
        "tests": [
            {"id": "finite_bounds", "kind": "F01", "result": "pass" if all(evaluations[c]["battery"]["F01"] for c in CANDIDATE_IDS) else "fail"},
            {"id": "ordered_update_witness", "kind": "N01", "result": "pass" if all(evaluations[c]["battery"]["N01"] for c in CANDIDATE_IDS) else "fail", "per_candidate": {c: evaluations[c]["battery"]["N01"] for c in CANDIDATE_IDS}},
            {"id": "pre_entropic_drive", "kind": "A0", "result": "pass" if all(evaluations[c]["battery"]["A0_drive"] for c in CANDIDATE_IDS) else "fail", "per_candidate": {c: evaluations[c]["a0"] for c in CANDIDATE_IDS}},
            {"id": "balanced_A0_attack", "kind": "A0_negative", "result": "pass" if all(not evaluations[c]["battery"]["A0_balanced_negative"] for c in CANDIDATE_IDS) else "fail", "per_candidate": {c: evaluations[c]["a0_negative"] for c in CANDIDATE_IDS}},
            {"id": "candidate_owned_obligation", "kind": "adequacy", "result": "pass" if {c: evaluations[c]["survived"] for c in CANDIDATE_IDS} == {"G1": True, "G2": False, "G2P": True, "G3": True, "G4": True} else "fail", "per_candidate": {c: evaluations[c]["battery"]["obligation_retention"] for c in CANDIDATE_IDS}},
            {"id": "per_family_negative", "kind": "killability", "result": "pass" if all(row["result"] == "pass" for row in negatives) else "fail"},
            {"id": "projection_witnesses", "kind": "weakness_witness", "result": "pass" if all(row["executed"] for row in projections) and all(projection_by_id[key]["preserves_obligation"] for key in ("G2_to_G1_forget_transitivity", "G2P_to_G1_forget_transitivity", "G3_to_G1_forget_incidence", "G4_to_G1_forget_totality", "all_candidates_erase_labels")) and not projection_by_id["G2P_to_G2_forget_probe_context"]["preserves_obligation"] else "fail"},
            {"id": "kernel_frontier_oracle", "kind": "minimal_frontier", "result": "pass"},
            {
                "id": "gradient_drive_license",
                "kind": "drive",
                "result": "pass" if gradient_evidence["all_license_conditions_pass"] else "fail",
                "conditions": gradient_evidence["license_conditions"],
            },
        ],
        "controls": controls,
        "control_flip_evidence": {
            "root_smuggling": root_evidence,
            "lineage_freshness": lineage_evidence,
            "resolution": {candidate: evaluations[candidate]["resolution_evidence"] for candidate in CANDIDATE_IDS},
            "history_memory": {candidate: evaluations[candidate]["history_evidence"] for candidate in CANDIDATE_IDS},
            "lower_structure": {
                candidate: projection_by_id[projection_id]
                for candidate, projection_id in {
                    "G2": "G2_to_G1_forget_transitivity",
                    "G2P": "G2P_to_G1_forget_transitivity",
                    "G3": "G3_to_G1_forget_incidence",
                    "G4": "G4_to_G1_forget_totality",
                }.items()
            },
            "gradient_freeze": gradient_evidence["controls"]["gradient_freeze"],
            "gradient_closure": gradient_evidence["controls"]["gradient_closure"],
            "gradient_injection": gradient_evidence["controls"]["gradient_injection"],
            "gradient_obligation_coupling": gradient_evidence["controls"]["gradient_obligation_coupling"],
        },
        "negative_results": negatives,
        "survivors": [],
        "declared_frontier": ["G1"],
        "open_world": {
            "global_minimum_claimed": False,
            "defeated_weaker_candidates": ["G2", "G2P_to_G2_forget_probe_context"] + [row["id"] for row in negatives],
            "open_weaker_attacks": open_attacks,
            "executed_installed_weakenings": [
                "erase_primitive",
                "forget_structure",
                "quotient_marks",
                "restrict_operations",
                "reduce_history",
                "coarsen_resolution",
                "remove_equivalence_closure",
            ],
            "unexecuted_installed_weakenings": [
                "reduce_locality",
                "carrier_substitution",
                "algebra_restriction",
                "remove_independent_entropy_geometry_fields",
            ],
        },
        "entropy_geometry": {
            "applicable": False,
            "single_surface": True,
            "independent_entropy_state": False,
            "independent_geometry_state": False,
            "scope_note": "A0 is pre-entropic; no entropy or geometry functional is selected.",
        },
        "transition": {
            "decision": gradient_evidence["honest_transition"]["decision"],
            "reason": gradient_evidence["honest_transition"]["reason"],
            "selected_frontier_members": gradient_evidence["honest_transition"]["selected_frontier_members"],
            "evidence_tooth_recorded": gradient_evidence["honest_transition"]["evidence_tooth_recorded"],
        },
        "status": {
            "lifecycle_status": "TESTED_SURVIVOR",
            "evidence_grade": "executable_diagnostic",
            "claim_ceiling": "scratch_diagnostic",
            "self_promotes": False,
            "promotion_allowed": False,
            "fresh_audit": "pending",
        },
        "conclusion": {
            "quotient_family_status": "not_excluded",
            "plain_statement": "The equivalence/quotient family is NOT excluded; only the probe-blind G2 variant died. Probe-respecting G2P survives the frozen obligation but is nonminimal because an executable G2P-to-G1 projection retains O.",
            "round_budget": "HARDEN ROUND 2 FINAL remains exhausted; v0.3 is schema migration plus required gradient controls only. Any remaining weakness is an open attack for final fresh audit, never an implied pass.",
        },
        "next_rung": None,
        "reopen_triggers": [
            "A new weaker candidate retains the same frozen obligation.",
            "A new weakening operator or rival carrier family is registered.",
            "The finite stream, prefix set, probe set, resolution, or battery changes.",
            "A fresh audit finds hidden candidate sharing, label leakage, or an ornamental control.",
            "A future rung makes D2 nonassociativity load-bearing.",
            "A final fresh audit finds any unfixed Round-2 attack; it remains recorded open because the harden budget is exhausted.",
        ],
    }
    receipt["survivors"] = kernel_survivors(receipt)
    receipt["declared_frontier"] = kernel_frontier(receipt, receipt["survivors"])
    receipt["transition"] = classify_gradient_transition(
        licensed=receipt["drive"]["licensed"],
        gradient_witnessed=receipt["drive"]["gradient_witnessed"],
        intrinsic=receipt["drive"]["intrinsic"],
        obligation_coupled=receipt["drive"]["obligation_coupled"],
        survivors=receipt["survivors"],
        frontier=receipt["declared_frontier"],
        controls_pass=(
            not any(row["result"] == "fail" for row in receipt["controls"])
            and all(
                next(row for row in receipt["controls"] if row["family"] == family)["result"] == "pass"
                for family in (
                    "gradient_freeze",
                    "gradient_closure",
                    "gradient_injection",
                    "gradient_obligation_coupling",
                )
            )
        ),
        context="primary migrated receipt",
    )
    if receipt["transition"]["decision"].startswith("HOLD_"):
        receipt["status"]["lifecycle_status"] = receipt["transition"]["decision"]
    final_errors = validate_receipt(receipt)
    if final_errors:
        raise RuntimeError("ratchet kernel rejected generated receipt: " + "; ".join(final_errors))
    if any(row["result"] == "fail" for row in receipt["controls"] if row["fired"]):
        raise RuntimeError("a fired hostile control failed; freeze is refused")
    return receipt


def print_summary(receipt: dict[str, Any]) -> None:
    print("ROOT PRESENTATION PACKET v0.3 — 0.2->0.3 SCHEMA MIGRATION; MATH UNCHANGED")
    print("ground truth: immutable finite distinction-attempt tuple stream; no persistent state tensor")
    print("candidates: " + ", ".join(candidate["id"] for candidate in receipt["candidates"]))
    print("survivors: " + ", ".join(receipt["survivors"]))
    print("frontier members: " + ", ".join(receipt["declared_frontier"]))
    print("gradient per candidate (declared admissible updates):")
    for candidate in CANDIDATE_IDS:
        rows = receipt["drive"]["gradient_measurements_per_candidate"][candidate]
        rendered = ", ".join(
            f"{update_id}:V={row['potential_before']}->{row['potential_after']},g={row['signed_gradient']}"
            for update_id, row in rows.items()
        )
        print(f"- {candidate}: {rendered}")
    gradient_controls = receipt["control_flip_evidence"]
    freeze = gradient_controls["gradient_freeze"]
    print(
        "gradient_freeze both sides: "
        f"honest_g={{{', '.join(f'{c}:{freeze['honest_side']['measurements'][c]['signed_gradient']}' for c in CANDIDATE_IDS)}}} "
        f"frozen_g={{{', '.join(f'{c}:{freeze['frozen_side']['measurements'][c]['signed_gradient']}' for c in CANDIDATE_IDS)}}} "
        f"frozen_decision={freeze['frozen_side']['transition']['decision']} pass={freeze['verdict']}"
    )
    print(
        "balanced A0 supplemental witness (honest non-freeze classification): "
        f"balanced_g={{{', '.join(f'{c}:{freeze['balanced_A0_side']['measurements'][c]['signed_gradient']}' for c in CANDIDATE_IDS)}}} "
        f"A0_flat={freeze['balanced_A0_side']['A0_asymmetry_collapsed']} "
        f"V_flat={freeze['balanced_A0_side']['gradient_collapsed']}"
    )
    closure = gradient_controls["gradient_closure"]
    print(
        "gradient_closure both sides: "
        f"open_g={{{', '.join(f'{c}:{closure['open_obligation_side']['measurements'][c]['signed_gradient']}' for c in CANDIDATE_IDS)}}} "
        f"closed_g={{{', '.join(f'{c}:{closure['closed_or_removed_obligation_side']['measurements'][c]['signed_gradient']}' for c in CANDIDATE_IDS)}}} "
        f"closed_decision={closure['closed_or_removed_obligation_side']['transition']['decision']} pass={closure['verdict']}"
    )
    injection = gradient_controls["gradient_injection"]
    print(
        "gradient_injection both sides: "
        f"honest_licensed={injection['honest_side']['detector']['licensed']} "
        f"injected_licensed={injection['injected_side']['detector']['licensed']} "
        f"detector_fired={injection['injected_side']['detector']['detector_fired']} "
        f"injected_decision={injection['injected_side']['transition']['decision']} pass={injection['verdict']}"
    )
    coupling = gradient_controls["gradient_obligation_coupling"]
    print(
        "gradient_obligation_coupling both sides: "
        f"active_g={{{', '.join(f'{c}:{coupling['active_obligation_side']['measurements'][c]['signed_gradient']}' for c in CANDIDATE_IDS)}}} "
        f"erased_g={{{', '.join(f'{c}:{coupling['erased_obligation_side']['measurements'][c]['signed_gradient']}' for c in CANDIDATE_IDS)}}} "
        f"erased_changed={all(coupling['erased_obligation_side']['gradient_changed'].values())} "
        f"erased_decision={coupling['erased_obligation_side']['transition']['decision']} pass={coupling['verdict']}"
    )
    print(
        "gradient_obligation_coupling replacement witness: "
        f"replacement_g={{{', '.join(f'{c}:{coupling['replacement_obligation_side']['measurements'][c]['signed_gradient']}' for c in CANDIDATE_IDS)}}} "
        f"changed={all(coupling['replacement_obligation_side']['gradient_changed'].values())} "
        f"decision={coupling['replacement_obligation_side']['transition']['decision']}"
    )
    print(
        "transition: "
        f"decision={receipt['transition']['decision']} "
        f"selected={receipt['transition']['selected_frontier_members']} "
        f"evidence_tooth_recorded={receipt['transition']['evidence_tooth_recorded']}"
    )
    root_flip = receipt["control_flip_evidence"]["root_smuggling"]
    print(
        "root_smuggling flip: "
        f"honest_pass={root_flip['honest_side']['passed']} "
        f"attacked_pass={root_flip['attacked_side']['passed']} "
        f"attacked_executed={root_flip['attacked_side_executed']} "
        f"detected_failure={root_flip['detected_failure']} flip={root_flip['flip_observed']}"
    )
    resolution = receipt["control_flip_evidence"]["resolution"]
    print(
        "resolution flip: "
        f"coarsened_executed={all(row['executed'] for row in resolution.values())} "
        f"coarsened_expected={all(row['coarsened_side_expected'] for row in resolution.values())} "
        f"raw_substitution_matches={any(row['raw_substitution_matches_coarsened'] for row in resolution.values())} "
        f"flip={all(row['verdict'] for row in resolution.values())}"
    )
    print(receipt["conclusion"]["plain_statement"])
    print("A0 balanced negatives: " + ", ".join(row["id"] for row in receipt["negative_results"] if "A0_balanced" in row["id"]))
    print("final fresh independent audit: pending; harden budget exhausted; packet frozen after this migration verification")
    print("open attacks:")
    for attack in receipt["open_world"]["open_weaker_attacks"]:
        print(f"- {attack}")


def main() -> int:
    receipt = build_receipt()
    target = HERE / "receipt.json"
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
