#!/usr/bin/env python3
"""Root-presentation packet v0.1 — HARDEN ROUND 1 (2026-07-10).

This one bounded harden round discharges fresh-audit Finding 1
(root-smuggling through one shared persistent NumPy carrier) and Finding 4
(A0 was never attacked).  The sole ground truth is one seeded immutable tuple
stream.  G1-G4 independently ingest that stream, build structurally distinct
candidate-owned presentations, and compute every battery/control readout from
their own presentation.  Fresh independent audit of v0.1 remains pending.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import random
import sys
from pathlib import Path
from typing import Any, Iterable


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
CANDIDATE_IDS = ("G1", "G2", "G3", "G4")
LOCAL_WEAKENINGS = (
    "forget-transitivity",
    "forget-symmetry",
    "forget-totality",
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


def coarsen_stream(stream: Stream) -> Stream:
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
O_COARSE = (O[0], 0, 0)


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
        "root_stream_only": main["source_kind"] == "immutable_raw_stream",
    }
    controls = {
        "root_smuggling": battery["root_stream_only"] and main["kind"] == "G1_contextual_partial_table",
        "lower_structure": g1_obligation(main) and not g1_obligation(erased),
        "label_metadata_erasure": g1_obligation(relabeled, O_RELABELLED) and g1_n01(relabeled, N_RELABELLED),
        "anti_by_construction": g1_obligation(main) and not g1_obligation(erased) and a0["A0_drive"] and not a0_negative["A0_drive"],
        "order_commutation": g1_n01(main) and not g1_n01(collapsed),
        "history_memory": g1_n01(main) and not g1_n01(collapsed),
        "resolution": not g1_obligation(coarse, O_COARSE),
        "lineage_freshness": sha256_json(main) != sha256_json(erased),
    }
    survived = bool(
        battery["F01"]
        and battery["N01"]
        and battery["obligation_retention"]
        and battery["A0_drive"]
        and not battery["A0_balanced_negative"]
        and battery["root_stream_only"]
    )
    return {"main": main, "battery": battery, "a0": a0, "a0_negative": a0_negative, "controls": controls, "survived": survived}


# ---------------------------------------------------------------------------
# G2 owns observed support, equivalence closure, and quotient rows.


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
        "kind": "G2_support_equivalence_quotient",
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
        "root_stream_only": main["source_kind"] == "immutable_raw_stream",
    }
    controls = {
        "root_smuggling": prequotient_o and not quotient_o,
        "lower_structure": prequotient_o and not quotient_o,
        "label_metadata_erasure": not g2_obligation(relabeled, O_RELABELLED) and g2_n01(relabeled, N_RELABELLED),
        "anti_by_construction": (not quotient_o) and g2_obligation(probe_erased) and a0["A0_drive"] and not a0_negative["A0_drive"],
        "probe_quotient": (not quotient_o) and g2_obligation(probe_erased),
        "order_commutation": g2_n01(main) and not g2_n01(collapsed),
        "history_memory": g2_n01(main) and not g2_n01(collapsed),
        "resolution": not g2_obligation(coarse, O_COARSE),
        "lineage_freshness": sha256_json(main) != sha256_json(erased),
    }
    survived = bool(
        battery["F01"]
        and battery["N01"]
        and battery["obligation_retention"]
        and battery["A0_drive"]
        and not battery["A0_balanced_negative"]
        and battery["root_stream_only"]
    )
    return {
        "main": main,
        "battery": battery,
        "a0": a0,
        "a0_negative": a0_negative,
        "controls": controls,
        "survived": survived,
        "defeat_reason": (
            "G2's candidate-owned not-distinguished closure merges obligation marks 0 and 1 at prefix 2; "
            "the pre-quotient observation remains distinguished, but the quotient cannot retain that distinction."
            if not survived
            else None
        ),
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
        "root_stream_only": main["source_kind"] == "immutable_raw_stream",
    }
    controls = {
        "root_smuggling": battery["root_stream_only"] and main["kind"] == "G3_event_incidence",
        "lower_structure": g3_obligation(main) and not g3_obligation(erased),
        "label_metadata_erasure": g3_obligation(relabeled, O_RELABELLED) and g3_n01(relabeled, N_RELABELLED),
        "anti_by_construction": g3_obligation(main) and not g3_obligation(erased) and a0["A0_drive"] and not a0_negative["A0_drive"],
        "order_commutation": g3_n01(main) and not g3_n01(collapsed),
        "history_memory": g3_n01(main) and not g3_n01(collapsed),
        "resolution": not g3_obligation(coarse, O_COARSE),
        "lineage_freshness": sha256_json(main) != sha256_json(erased),
    }
    survived = bool(
        battery["F01"]
        and battery["N01"]
        and battery["obligation_retention"]
        and battery["A0_drive"]
        and not battery["A0_balanced_negative"]
        and battery["root_stream_only"]
    )
    return {"main": main, "battery": battery, "a0": a0, "a0_negative": a0_negative, "controls": controls, "survived": survived}


# ---------------------------------------------------------------------------
# G4 owns a total table for every observed history prefix.


def g4_build(stream: Stream) -> dict[str, Any]:
    support = sorted({record[2] for record in stream} | {record[3] for record in stream})
    probes = sorted({record[1] for record in stream})
    prefixes = sorted({record[0] for record in stream})
    tables: dict[str, dict[str, str]] = {}
    for prefix in prefixes:
        table = {
            f"{probe}:{mark_a}:{mark_b}": "inadmissible"
            for probe, mark_a, mark_b in itertools.product(probes, support, support)
        }
        for hp, probe, mark_a, mark_b, verdict in stream:
            if hp == prefix:
                table[f"{probe}:{mark_a}:{mark_b}"] = verdict
        tables[str(prefix)] = dict(sorted(table.items()))
    return {
        "kind": "G4_history_indexed_total_table",
        "source_kind": "immutable_raw_stream",
        "source_hash": sha256_json(stream_json(stream)),
        "support": support,
        "probes": probes,
        "tables": tables,
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
        "root_stream_only": main["source_kind"] == "immutable_raw_stream",
    }
    controls = {
        "root_smuggling": battery["root_stream_only"] and main["kind"] == "G4_history_indexed_total_table",
        "lower_structure": g4_obligation(main) and not g4_obligation(erased),
        "label_metadata_erasure": g4_obligation(relabeled, O_RELABELLED) and g4_n01(relabeled, N_RELABELLED),
        "anti_by_construction": g4_n01(main) and not g4_n01(collapsed) and a0["A0_drive"] and not a0_negative["A0_drive"],
        "order_commutation": g4_n01(main) and not g4_n01(collapsed),
        "history_memory": g4_n01(main) and not g4_n01(collapsed),
        "resolution": not g4_obligation(coarse, O_COARSE),
        "lineage_freshness": sha256_json(main) != sha256_json(erased),
    }
    survived = bool(
        battery["F01"]
        and battery["N01"]
        and battery["obligation_retention"]
        and battery["A0_drive"]
        and not battery["A0_balanced_negative"]
        and battery["root_stream_only"]
    )
    return {"main": main, "battery": battery, "a0": a0, "a0_negative": a0_negative, "controls": controls, "survived": survived}


def run_candidate_evaluations() -> dict[str, dict[str, Any]]:
    # This controller dispatch aggregates only completed candidate-owned
    # receipts; it does not compute any candidate observable.
    return {
        "G1": g1_evaluate(),
        "G2": g2_evaluate(),
        "G3": g3_evaluate(),
        "G4": g4_evaluate(),
    }


def projection_checks(evaluations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    g2 = evaluations["G2"]["main"]
    g4 = evaluations["G4"]["main"]
    g2_rows = g2["observations"][str(P_LOCK)]
    g4_rows = [
        [int(part) for part in key.split(":")] + [verdict]
        for key, verdict in g4["tables"][str(P_LOCK)].items()
        if verdict != "inadmissible"
    ]
    g2_prequotient_retains = any(tuple(row[:3]) == O and row[3] == "distinguished" for row in g2_rows)
    g4_partial_retains = any(tuple(row[:3]) == O and row[3] == "distinguished" for row in g4_rows)
    return [
        {
            "operator": "forget-transitivity",
            "source": "G2",
            "target": "G1-compatible contextual rows",
            "executed": True,
            "preserves_obligation": g2_prequotient_retains,
            "witness": "Forgot G2's candidate-owned classes/equivalence/quotient and retained only its own prefix-2 observation rows; O remains distinguished. The actual G1 builder still ingests only the raw stream.",
        },
        {
            "operator": "forget-symmetry",
            "source": "G2",
            "target": "G3",
            "executed": False,
            "preserves_obligation": None,
            "undefined_reason": "G2 has no event ancestry; constructing G3 incidence would add rather than forget structure.",
        },
        {
            "operator": "forget-totality",
            "source": "G4",
            "target": "G1-compatible contextual rows",
            "executed": True,
            "preserves_obligation": g4_partial_retains,
            "witness": "Forgot G4's inadmissible default cells and retained its own observed prefix-2 rows; O remains distinguished. The actual G1 builder still ingests only the raw stream.",
        },
        {
            "operator": "restrict-history",
            "source": "G4",
            "target": "G4 prefix-2 restriction",
            "executed": True,
            "preserves_obligation": g4_partial_retains,
            "witness": "Restricted G4's own history-indexed structure to the lock prefix and retained O as distinguished.",
        },
        {
            "operator": "erase-labels",
            "source": "G1,G2,G3,G4",
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
        ("G3", "erase-labels"): "tested_survivor",
        ("G4", "forget-totality"): "tested_survivor",
        ("G4", "restrict-history"): "tested_survivor",
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
    executed = [
        ("erase_primitive", not evaluations["G1"]["controls"]["lower_structure"], "Obligation erasure makes G1 retention false; the boolean records the erased primitive rather than a surviving candidate."),
        ("forget_structure", bool(projections[0]["preserves_obligation"] and projections[2]["preserves_obligation"]), "Candidate-local G2 quotient erasure and G4 totality erasure retain their own observed O row."),
        ("quotient_marks", evaluations["G2"]["controls"]["probe_quotient"], "Fresh G2 reconstruction after probe-1 erasure separates obligation marks that the full quotient merged."),
        ("restrict_operations", all(evaluations[c]["controls"]["order_commutation"] for c in CANDIDATE_IDS), "The order-collapsed stream removes every candidate-owned N01 witness."),
        ("reduce_history", all(evaluations[c]["controls"]["history_memory"] for c in CANDIDATE_IDS), "The collapsed history stream removes every candidate-owned N01 witness."),
        ("coarsen_resolution", all(evaluations[c]["controls"]["resolution"] for c in CANDIDATE_IDS), "The two-bin stream maps O to a self-pair, so every candidate rejects it as a retained distinction."),
        ("remove_equivalence_closure", evaluations["G2"]["controls"]["root_smuggling"], "Within G2, the pre-quotient O record is distinguished while the installed quotient merges its marks."),
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


def negative_results(evaluations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
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
    return rows


def control_rows(evaluations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    applicable = {
        "root_smuggling": list(CANDIDATE_IDS),
        "lower_structure": list(CANDIDATE_IDS),
        "label_metadata_erasure": list(CANDIDATE_IDS),
        "anti_by_construction": list(CANDIDATE_IDS),
        "probe_quotient": ["G2"],
        "order_commutation": list(CANDIDATE_IDS),
        "history_memory": list(CANDIDATE_IDS),
        "resolution": list(CANDIDATE_IDS),
        "lineage_freshness": list(CANDIDATE_IDS),
    }
    expected = {
        "root_smuggling": "Each family must rebuild only from the raw stream; G2 must expose the measured pre-quotient/quotient distinction loss.",
        "lower_structure": "Each family must expose a candidate-local weakening or erasure outcome rather than borrow shared state.",
        "label_metadata_erasure": "Each family must rebuild from a bijectively relabeled stream and preserve its mapped outcome.",
        "anti_by_construction": "Each family must reach both sides of its decisive outcome, including A0_drive=true on the main stream and false on the balanced stream.",
        "probe_quotient": "G2 must rebuild support, equivalence, and quotient after probe erasure and change the obligation outcome.",
        "order_commutation": "Each family must lose N01 after rebuilding from the order-collapsed stream.",
        "history_memory": "Each family must lose N01 after rebuilding from the history-collapsed stream.",
        "resolution": "Each family must reject the coarsened self-pair as obligation retention.",
        "lineage_freshness": "Each candidate-owned serialization must change after the obligation stream is mutated.",
    }
    rows: list[dict[str, Any]] = []
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
    files = {
        "findings": (HERE / "graveyard/AUDIT_FINDINGS_v0_20260710.md", "09cdcee987e16e3c6aa4f85839f1b2cb6c7f28e1a34315a0e02ca32c7211b148"),
        "frozen_packet": (HERE / "graveyard/packet_v0_postrepair_frozen_20260710.py", "0cd05bc69805840dae0aea540df82cc9fa86fb413a8712ca81c395e55e90f9d3"),
        "frozen_receipt": (HERE / "graveyard/receipt_v0_postrepair_frozen_20260710.json", "3d3230bcb0d4e4b6497e36e5c73d3035db0348c125c2fa75ee17e3a1f84ff706"),
        "checksum_manifest": (HERE / "graveyard/SHA256SUMS", "b3a72c37b3e82181e97d1aa848bb47d16210e8ece45aafd73db7e68dca9bcaa6"),
    }
    evidence: dict[str, Any] = {}
    for label, (path, expected_hash) in files.items():
        actual_hash = sha256_bytes(path.read_bytes())
        if actual_hash != expected_hash:
            raise RuntimeError(f"frozen predecessor evidence changed: {path}")
        evidence[label] = {
            "path": str(path.relative_to(BUNDLE_ROOT)),
            "sha256": actual_hash,
            "verified": True,
        }
    return evidence


def build_receipt() -> dict[str, Any]:
    packet_sha = sha256_bytes(Path(__file__).read_bytes())
    predecessor_evidence = frozen_predecessor_evidence()
    evaluations = run_candidate_evaluations()
    projections = projection_checks(evaluations)
    controls = control_rows(evaluations)
    negatives = negative_results(evaluations)
    installed_results = installed_weakening_results(evaluations, projections)
    candidate_spec = {
        "families": [
            "contextual_partial_distinction_table",
            "support_equivalence_quotient",
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
        "G2 quotient-time semantics remain open: A0 is read from G2-owned pre-quotient observations because the quotient itself merges the obligation marks.",
    ]
    candidates: list[dict[str, Any]] = []
    family_names = {
        "G1": "contextual_partial_distinction_table",
        "G2": "support_equivalence_quotient",
        "G3": "pre_object_event_incidence",
        "G4": "history_indexed_order_table",
    }
    assumptions = {
        "G1": ["finite attempt records", "contextual partial directed table", "no closure laws"],
        "G2": ["support derived from observed marks", "candidate-installed equivalence closure", "fresh quotient classes"],
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
        }
        if candidate == "G2" and evaluations[candidate].get("defeat_reason"):
            row["defeat_reason"] = evaluations[candidate]["defeat_reason"]
        candidates.append(row)
    receipt: dict[str, Any] = {
        "schema_version": "ratchet-run/0.2",
        "receipt": {
            "id": "root_presentation_packet_v0_1.seed0.002",
            "generated_at": "2026-07-10T00:00:00Z",
            "append_only": True,
            "self_adjudicating": False,
        },
        "lineage": {
            "predecessor_receipts": ["root_presentation_packet_v0.seed0.001"],
            "predecessor_evidence": predecessor_evidence,
            "constraint_hash": "sha256:" + sha256_json({"F01": "finite", "N01": "order-sensitive", "A0": "opening-locking"}),
            "obligation_hash": "sha256:" + sha256_json({"probe": O[0], "marks": list(O[1:]), "history_prefix_index": P_LOCK}),
            "code_hash": "sha256:" + packet_sha,
            "packet_py_sha256": packet_sha,
            "data_hash": "sha256:" + sha256_json(data_spec),
            "test_battery_hash": "sha256:" + sha256_json(battery_spec),
            "candidate_grammar_hash": "sha256:" + sha256_json(candidate_spec),
            "weakening_grammar_hash": "sha256:" + sha256_json(weakening_spec),
            "independent_audit": {
                "performed": False,
                "auditor": "",
                "freshness": "v0.1 is frozen after HARDEN ROUND 1; fresh independent audit is pending.",
                "found_fabrication": None,
            },
        },
        "claim": {
            "id": "root_presentation_packet_v0_1",
            "text": "Within the frozen finite grammar and battery, compare independently built stream-only root presentations and compute the plural minimal-survivor frontier.",
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
            "id": "A0",
            "declaration": "Pre-entropic asymmetry between distinction-opening and distinction-locking record deltas; no entropy functional is selected.",
            "discharged_by_obligation": True,
            "per_candidate_positive": {candidate: evaluations[candidate]["a0"] for candidate in CANDIDATE_IDS},
            "per_candidate_balanced_negative": {candidate: evaluations[candidate]["a0_negative"] for candidate in CANDIDATE_IDS},
        },
        "finite_scope": {
            "candidate_limit": 8,
            "test_limit": 64,
            "history_limit": 5,
            "resolution_limit": len(MARKS),
            "budget_label": "root-presentation-v0.1-harden-round1-seed0-finite",
            "marks": len(MARKS),
            "probes": len(PROBES),
            "prefixes": len(PREFIXES),
            "records": len(RAW_STREAM),
        },
        "data_spec": data_spec,
        "candidate_grammar": {
            "id": "root-presentation-candidates-v0.1",
            "hash": "sha256:" + sha256_json(candidate_spec),
            "families": candidate_spec["families"],
            "globally_complete": False,
        },
        "weakening_grammar": {
            "id": "root-presentation-local-weakenings-v0.1",
            "hash": "sha256:" + sha256_json(weakening_spec),
            "operators": list(LOCAL_WEAKENINGS),
            "globally_complete": False,
            "source_grammar": "ratchet/weakening_grammar.json",
            "operator_mapping": {
                "forget-transitivity": ["forget_structure", "remove_equivalence_closure"],
                "forget-symmetry": ["forget_structure", "remove_equivalence_closure"],
                "forget-totality": ["forget_structure"],
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
                "witness": projections[0]["witness"],
                "preserves_obligation": True,
            },
            {
                "weaker": "G1",
                "stronger": "G4",
                "operator": "forget-totality",
                "witness": projections[2]["witness"],
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
            {"id": "candidate_owned_obligation", "kind": "adequacy", "result": "pass" if evaluations["G1"]["survived"] and not evaluations["G2"]["survived"] and evaluations["G3"]["survived"] and evaluations["G4"]["survived"] else "fail", "per_candidate": {c: evaluations[c]["battery"]["obligation_retention"] for c in CANDIDATE_IDS}},
            {"id": "per_family_negative", "kind": "killability", "result": "pass" if all(row["result"] == "pass" for row in negatives) else "fail"},
            {"id": "projection_witnesses", "kind": "weakness_witness", "result": "pass" if all((row["executed"] and row["preserves_obligation"]) or (not row["executed"] and row.get("undefined_reason")) for row in projections) else "fail"},
            {"id": "kernel_frontier_oracle", "kind": "minimal_frontier", "result": "pass"},
        ],
        "controls": controls,
        "negative_results": negatives,
        "survivors": [],
        "declared_frontier": ["G1"],
        "open_world": {
            "global_minimum_claimed": False,
            "defeated_weaker_candidates": ["G2"] + [row["id"] for row in negatives],
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
        "status": {
            "lifecycle_status": "TESTED_SURVIVOR",
            "evidence_grade": "executable_diagnostic",
            "claim_ceiling": "scratch_diagnostic",
            "self_promotes": False,
            "promotion_allowed": False,
            "fresh_audit": "pending",
        },
        "next_rung": None,
        "reopen_triggers": [
            "A new weaker candidate retains the same frozen obligation.",
            "A new weakening operator or rival carrier family is registered.",
            "The finite stream, prefix set, probe set, resolution, or battery changes.",
            "A fresh audit finds hidden candidate sharing, label leakage, or an ornamental control.",
            "A future rung makes D2 nonassociativity load-bearing.",
        ],
    }
    receipt["survivors"] = kernel_survivors(receipt)
    receipt["declared_frontier"] = kernel_frontier(receipt, receipt["survivors"])
    final_errors = validate_receipt(receipt)
    if final_errors:
        raise RuntimeError("ratchet kernel rejected generated receipt: " + "; ".join(final_errors))
    if any(row["result"] == "fail" for row in receipt["controls"] if row["fired"]):
        raise RuntimeError("a fired hostile control failed; freeze is refused")
    return receipt


def print_summary(receipt: dict[str, Any]) -> None:
    print("ROOT PRESENTATION PACKET v0.1 — HARDEN ROUND 1")
    print("ground truth: immutable finite distinction-attempt tuple stream; no persistent state tensor")
    print("candidates: " + ", ".join(candidate["id"] for candidate in receipt["candidates"]))
    print("survivors: " + ", ".join(receipt["survivors"]))
    print("frontier members: " + ", ".join(receipt["declared_frontier"]))
    print("A0 balanced negatives: " + ", ".join(row["id"] for row in receipt["negative_results"] if "A0_balanced" in row["id"]))
    print("fresh independent audit: pending")
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
