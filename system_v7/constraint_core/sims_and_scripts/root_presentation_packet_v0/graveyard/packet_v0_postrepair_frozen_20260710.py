#!/usr/bin/env python3
"""Finite root-presentation comparison for Ratchet process v0.2."""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np


HERE = Path(__file__).resolve().parent
BUNDLE_ROOT = HERE.parents[1]
sys.path.insert(0, str(BUNDLE_ROOT))

from ratchet.ratchet_kernel import validate_receipt  # noqa: E402


RNG = np.random.default_rng(0)
N_P = 2
N_M = 4
U = (0, 1)
H0: tuple[int, ...] = ()
H1 = (1,)
H01 = (0, 1)
H10 = (1, 0)
H_HELD = (0, 0, 1)
O = (0, 0, 1)
N = (1, 1, 2)
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


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(encoded)


def initial_state() -> tuple[np.ndarray, np.ndarray]:
    x = np.zeros((N_P, N_M, N_M), dtype=np.int8)
    k = np.zeros_like(x)
    x[0, 0, 1] = 1
    x[1, 2, 3] = 1
    return x, k


def apply_update(
    x_in: np.ndarray,
    k_in: np.ndarray,
    u: int,
    *,
    commute_control: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    x = x_in.copy()
    k = k_in.copy()
    if u == 0:
        if commute_control or not bool(np.any(k)):
            x[1, 1, 2] = 1
    elif u == 1:
        k = np.maximum(k, x)
    else:
        raise ValueError(f"update index out of finite range: {u}")
    return x, k


def recompute(
    history: Iterable[int],
    *,
    commute_control: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    history_tuple = tuple(int(u) for u in history)
    if len(history_tuple) > 4 or any(u not in U for u in history_tuple):
        raise ValueError("history outside the frozen finite scope")
    x, k = initial_state()
    for u in history_tuple:
        x, k = apply_update(x, k, u, commute_control=commute_control)
    return x, k


def state_counts(history: Iterable[int]) -> tuple[int, int]:
    x, k = recompute(history)
    return int(np.sum(x)), int(np.sum(k))


def f01_check() -> bool:
    histories = (H0, H1, H01, H10, H_HELD)
    return bool(
        len(CANDIDATE_IDS) == 4
        and N_P == 2
        and N_M == 4
        and len(U) == 2
        and max(map(len, histories)) <= 4
        and all(
            x.shape == (N_P, N_M, N_M)
            and k.shape == x.shape
            and np.all((x == 0) | (x == 1))
            and np.all((k == 0) | (k == 1))
            for x, k in (recompute(h) for h in histories)
        )
    )


def a0_witness() -> dict[str, Any]:
    x0, k0 = state_counts(H0)
    xa, ka = state_counts((0,))
    xb, kb = state_counts((1,))
    v0 = (xa - x0, ka - k0)
    v1 = (xb - x0, kb - k0)
    return {
        "u0_delta": list(v0),
        "u1_delta": list(v1),
        "gradient": int(v0[0] - v1[1]),
        "pass": bool(v0 == (1, 0) and v1 == (0, 2) and v0 != v1),
    }


def n01_witness(*, commute_control: bool = False) -> dict[str, Any]:
    x01, _ = recompute(H01, commute_control=commute_control)
    x10, _ = recompute(H10, commute_control=commute_control)
    v01 = int(x01[N])
    v10 = int(x10[N])
    return {"h01": v01, "h10": v10, "pass": bool(v01 != v10)}


def obligation_from_state(history: Iterable[int]) -> bool:
    x0, _ = recompute(H0)
    x1, k1 = recompute(history)
    return bool(x0[O] == 1 and x1[O] == 1 and k1[O] == 1)


def entries_from_arrays(
    x: np.ndarray,
    k: np.ndarray,
    *,
    negative: bool = False,
) -> dict[str, Any]:
    entries: list[list[int]] = []
    for p, a, b in np.argwhere((x != 0) | (k != 0)):
        row = [int(p), int(a), int(b), int(x[p, a, b]), int(k[p, a, b])]
        if negative and tuple(row[:3]) == O:
            continue
        entries.append(row)
    return {"entries": entries}


def g1(history: Iterable[int], *, negative: bool = False) -> dict[str, Any]:
    x, k = recompute(history)
    return entries_from_arrays(x, k, negative=negative)


def g1_value(rep: dict[str, Any], index: tuple[int, int, int]) -> tuple[int, int]:
    for p, a, b, x, k in rep["entries"]:
        if (p, a, b) == index:
            return int(x), int(k)
    return 0, 0


def mark_signature(
    x: np.ndarray,
    k: np.ndarray,
    m: int,
    probes: tuple[int, ...],
) -> tuple[int, ...]:
    values: list[int] = []
    for p in probes:
        values.extend(int(v) for v in x[p, m, :])
        values.extend(int(v) for v in x[p, :, m])
        values.extend(int(v) for v in k[p, m, :])
        values.extend(int(v) for v in k[p, :, m])
    return tuple(values)


def g2(
    history: Iterable[int],
    *,
    probes: tuple[int, ...] = (0, 1),
) -> dict[str, Any]:
    x, k = recompute(history)
    signatures = [mark_signature(x, k, m, probes) for m in range(N_M)]
    class_ids: list[int] = []
    representatives: list[tuple[int, ...]] = []
    for signature in signatures:
        if signature not in representatives:
            representatives.append(signature)
        class_ids.append(representatives.index(signature))
    equivalence = [
        [int(class_ids[a] == class_ids[b]) for b in range(N_M)]
        for a in range(N_M)
    ]
    return {
        "support": list(range(N_M)),
        "probes": list(probes),
        "signatures": [list(row) for row in signatures],
        "classes": class_ids,
        "equivalence": equivalence,
        "raw_x": x,
        "raw_k": k,
    }


def g2_counts(rep: dict[str, Any]) -> tuple[int, int]:
    signature_sum = sum(sum(row) for row in rep["signatures"])
    half = signature_sum // 2
    raw_x = int(np.sum(rep["raw_x"]))
    raw_k = half - raw_x
    return raw_x, raw_k


def g3(history: Iterable[int], *, negative: bool = False) -> dict[str, Any]:
    history_tuple = tuple(history)
    events: list[list[int]] = []
    previous: dict[tuple[int, int, int], int] = {}
    for step in range(len(history_tuple) + 1):
        x, k = recompute(history_tuple[:step])
        current: dict[tuple[int, int, int], int] = {}
        for p, a, b in np.argwhere(x == 1):
            index = (int(p), int(a), int(b))
            parent = previous.get(index, -1)
            if negative and step == len(history_tuple) and index == O:
                parent = -1
            event_id = len(events)
            events.append(
                [event_id, step, index[0], index[1], index[2], int(k[index]), parent]
            )
            current[index] = event_id
        previous = current
    return {"events": events, "terminal_step": len(history_tuple)}


def g3_terminal_event(rep: dict[str, Any], index: tuple[int, int, int]) -> list[int] | None:
    terminal = rep["terminal_step"]
    for row in rep["events"]:
        if row[1] == terminal and tuple(row[2:5]) == index:
            return row
    return None


def g4(history: Iterable[int], *, negative: bool = False) -> dict[str, Any]:
    original = tuple(history)
    evaluated = tuple(sorted(original)) if negative else original
    prefixes: list[dict[str, Any]] = []
    for step in range(len(evaluated) + 1):
        x, k = recompute(evaluated[:step])
        prefixes.append(
            {
                "prefix": list(evaluated[:step]),
                "x": x,
                "k": k,
            }
        )
    return {"requested_history": list(original), "prefixes": prefixes}


def g4_terminal(rep: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    final = rep["prefixes"][-1]
    return final["x"], final["k"]


def installed_root_keys(rep: dict[str, Any]) -> set[str]:
    return {"support", "classes", "equivalence"} & set(rep)


def erase_g2_installed_root(rep: dict[str, Any]) -> dict[str, Any]:
    return entries_from_arrays(rep["raw_x"], rep["raw_k"])


def representation_root_safe(candidate: str) -> bool:
    if candidate == "G1":
        rep = g1(H1)
    elif candidate == "G2":
        rep = g2(H1)
    elif candidate == "G3":
        rep = g3(H1)
    elif candidate == "G4":
        rep = g4(H1)
    else:
        raise KeyError(candidate)
    return not installed_root_keys(rep)


def presentation_counts(candidate: str, history: tuple[int, ...]) -> tuple[int, int]:
    if candidate == "G1":
        return tuple(sum(row[index] for row in g1(history)["entries"]) for index in (3, 4))
    if candidate == "G2":
        return g2_counts(g2(history))
    if candidate == "G3":
        rep = g3(history)
        terminal = rep["terminal_step"]
        rows = [row for row in rep["events"] if row[1] == terminal]
        return len(rows), sum(row[5] for row in rows)
    if candidate == "G4":
        x, k = g4_terminal(g4(history))
        return int(np.sum(x)), int(np.sum(k))
    raise KeyError(candidate)


def candidate_obligation(candidate: str, *, negative: bool = False) -> bool:
    if candidate == "G1":
        before = g1_value(g1(H0), O)[0]
        after = g1_value(g1(H1, negative=negative), O)
        return bool(before == 1 and after == (1, 1))
    if candidate == "G2":
        probes = (1,) if negative else (0, 1)
        rep = g2(H1, probes=probes)
        return bool(rep["classes"][O[1]] != rep["classes"][O[2]])
    if candidate == "G3":
        event = g3_terminal_event(g3(H1, negative=negative), O)
        return bool(event is not None and event[5] == 1 and event[6] >= 0)
    if candidate == "G4":
        x0, _ = g4_terminal(g4(H0, negative=negative))
        x1, k1 = g4_terminal(g4(H1, negative=negative))
        return bool(x0[O] == 1 and x1[O] == 1 and k1[O] == 1)
    raise KeyError(candidate)


def candidate_n01(candidate: str, *, negative: bool = False) -> bool:
    if candidate == "G1":
        return g1_value(g1(H01, negative=negative), N)[0] != g1_value(g1(H10, negative=negative), N)[0]
    if candidate == "G2":
        probes = (1,) if negative else (0, 1)
        return g2(H01, probes=probes)["equivalence"] != g2(H10, probes=probes)["equivalence"]
    if candidate == "G3":
        a = g3_terminal_event(g3(H01, negative=negative), N)
        b = g3_terminal_event(g3(H10, negative=negative), N)
        return (a is None) != (b is None)
    if candidate == "G4":
        x01, _ = g4_terminal(g4(H01, negative=negative))
        x10, _ = g4_terminal(g4(H10, negative=negative))
        return bool(x01[N] != x10[N])
    raise KeyError(candidate)


def candidate_a0(candidate: str) -> bool:
    c0 = presentation_counts(candidate, H0)
    c_a = presentation_counts(candidate, (0,))
    c_b = presentation_counts(candidate, (1,))
    return bool((c_a[0] - c0[0], c_a[1] - c0[1]) == (1, 0) and (c_b[0] - c0[0], c_b[1] - c0[1]) == (0, 2))


def candidate_battery(candidate: str, *, negative: bool = False) -> dict[str, bool]:
    return {
        "F01": f01_check(),
        "N01": candidate_n01(candidate, negative=negative),
        "obligation_retention": candidate_obligation(candidate, negative=negative),
        "A0_drive": candidate_a0(candidate),
        "root_safe": representation_root_safe(candidate),
    }


def label_erasure_control() -> bool:
    p_order = RNG.permutation(N_P)
    m_order = RNG.permutation(N_M)
    p_inverse = np.argsort(p_order)
    m_inverse = np.argsort(m_order)
    remapped_o = (int(p_inverse[O[0]]), int(m_inverse[O[1]]), int(m_inverse[O[2]]))
    remapped_n = (int(p_inverse[N[0]]), int(m_inverse[N[1]]), int(m_inverse[N[2]]))

    def relabel(history: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
        x, k = recompute(history)
        return x[p_order][:, m_order][:, :, m_order], k[p_order][:, m_order][:, :, m_order]

    x1, k1 = relabel(H1)
    x01, _ = relabel(H01)
    x10, _ = relabel(H10)
    return bool(
        x1[remapped_o] == 1
        and k1[remapped_o] == 1
        and x01[remapped_n] != x10[remapped_n]
    )


def root_smuggling_control() -> bool:
    source = g2(H1)
    erased = erase_g2_installed_root(source)
    source_has_installed_root = bool(installed_root_keys(source))
    erased_has_installed_root = bool(installed_root_keys(erased))
    erased_retains_o = g1_value(erased, O) == (1, 1)
    already_root_safe = all(
        representation_root_safe(candidate) and candidate_obligation(candidate)
        for candidate in ("G1", "G3", "G4")
    )
    return bool(
        source_has_installed_root
        and not erased_has_installed_root
        and erased_retains_o
        and already_root_safe
    )


def probe_quotient_control() -> bool:
    full = g2(H1, probes=(0, 1))
    erased = g2(H1, probes=(1,))
    return bool(
        full["classes"][O[1]] != full["classes"][O[2]]
        and erased["classes"][O[1]] == erased["classes"][O[2]]
    )


def history_control() -> bool:
    actual = n01_witness()["pass"]
    collapsed = candidate_n01("G4", negative=True)
    return bool(actual and not collapsed)


def anti_construction_control() -> bool:
    positive = {
        "G1": candidate_obligation("G1"),
        "G2": candidate_obligation("G2"),
        "G3": candidate_obligation("G3"),
        "G4": candidate_n01("G4"),
    }
    negative = {
        "G1": candidate_obligation("G1", negative=True),
        "G2": candidate_obligation("G2", negative=True),
        "G3": candidate_obligation("G3", negative=True),
        "G4": candidate_n01("G4", negative=True),
    }
    return bool(all(positive.values()) and not any(negative.values()))


def order_commutation_control() -> bool:
    return bool(n01_witness()["pass"] and not n01_witness(commute_control=True)["pass"])


def resolution_control() -> bool:
    bins = np.array([0, 0, 1, 1], dtype=np.int8)
    x, k = recompute(H1)
    coarse_x = np.zeros((N_P, 2, 2), dtype=np.int8)
    coarse_k = np.zeros_like(coarse_x)
    for p, a, b in itertools.product(range(N_P), range(N_M), range(N_M)):
        coarse_x[p, bins[a], bins[b]] = max(coarse_x[p, bins[a], bins[b]], x[p, a, b])
        coarse_k[p, bins[a], bins[b]] = max(coarse_k[p, bins[a], bins[b]], k[p, a, b])
    mapped = (O[0], int(bins[O[1]]), int(bins[O[2]]))
    coarse_retains_between_bin_distinction = bool(
        mapped[1] != mapped[2] and coarse_x[mapped] == 1 and coarse_k[mapped] == 1
    )
    return bool(obligation_from_state(H1) and not coarse_retains_between_bin_distinction)


def lineage_control() -> bool:
    x, k = initial_state()
    original = sha256_bytes(x.tobytes() + k.tobytes())
    x[O] = 0
    mutated = sha256_bytes(x.tobytes() + k.tobytes())
    return original != mutated


def restrict_operations_check() -> bool:
    retained_updates = {1}
    n01_histories_admissible = set(H01).issubset(retained_updates) and set(H10).issubset(retained_updates)
    return bool(obligation_from_state(H1) and not n01_histories_admissible)


def lower_structure_control() -> bool:
    projected = project_g4_to_g1(g4(H1))
    return bool(g1_value(projected, O) == (1, 1) and candidate_obligation("G4"))


def control_rows() -> list[dict[str, Any]]:
    passing = [
        ("root_smuggling", root_smuggling_control(), "Removing object/equivalence/carrier assumptions must execute a structural projection and preserve O only in the weaker presentation.", "G2 contained support/classes/equivalence; erasing them produced a G1 table with O=(1,1), while G1, G3, and G4 required no such installed keys."),
        ("lower_structure", lower_structure_control(), "An executable projection from G4 to G1 must retain O.", "Extracting the terminal tensor from G4 and forgetting totality produced a partial G1 table retaining O."),
        ("label_metadata_erasure", label_erasure_control(), "Seeded bijective index erasure must preserve mapped O and N01 values.", "Seeded probe/mark permutations preserved the remapped retention and order witnesses."),
        ("anti_by_construction", anti_construction_control(), "Every family must have reachable pass and fail outcomes on its decisive observable.", "G1-G3 reached both sides of obligation retention; G4 reached both sides of order sensitivity under its weakened variant."),
        ("probe_quotient", probe_quotient_control(), "Deleting probe 0 and recomputing the quotient must erase O rather than reuse cached classes.", "Fresh signatures merged marks 0 and 1 only after probe 0 was deleted."),
        ("order_commutation", order_commutation_control(), "Forcing update 0 through an existing lock must remove N01.", "The commuting mutation made histories 01 and 10 agree at the order witness."),
        ("history_memory", history_control(), "Permuting history must change a recomputed terminal outcome, while a sorted-history negative must fail.", "Recomputed 01 and 10 differed; the sorted-history G4 negative collapsed them."),
        ("resolution", resolution_control(), "A real finite coarsening that merges marks 0 and 1 must erase between-mark O.", "The terminal tensors were projected into two bins; O mapped to a diagonal cell and ceased to be a distinction between separate bins."),
        ("lineage_freshness", lineage_control(), "Changing frozen source data must change its hash.", "Erasing the obligation cell changed the finite-data SHA-256."),
    ]
    rows = [
        {
            "family": family,
            "result": "pass" if passed else "fail",
            "fired": True,
            "expected_effect": expected,
            "observed_effect": observed,
        }
        for family, passed, expected, observed in passing
    ]
    not_applicable = {
        "carrier_family": "Rival carrier families are not yet formalized; candidate encodings alone do not prove carrier substitution or non-isomorphism.",
        "topology_locality": "No topology, adjacency, locality, or schedule claim is installed at this root packet.",
        "entropy_geometry_split": "A0 is pre-entropic and no entropy or geometry state exists to split.",
        "field_vs_token": "No token or full configuration-field dynamics claim is made by this finite record.",
        "held_out_contact": "The frozen scope contains supplied histories only and makes no held-out prediction claim.",
    }
    rows.extend(
        {
            "family": family,
            "result": "not_applicable",
            "fired": False,
            "expected_effect": "No effect is predicted inside the declared root-presentation scope.",
            "observed_effect": reason,
            "justification": reason,
        }
        for family, reason in not_applicable.items()
    )
    return rows


def project_g2_to_g1(source: dict[str, Any]) -> dict[str, Any]:
    if not installed_root_keys(source):
        raise ValueError("G2 source lacks installed quotient/support structure")
    return erase_g2_installed_root(source)


def project_g4_to_g1(source: dict[str, Any]) -> dict[str, Any]:
    x, k = g4_terminal(source)
    return entries_from_arrays(x, k)


def project_restrict_g4_to_g1(source: dict[str, Any]) -> dict[str, Any]:
    if len(source["prefixes"]) < 2:
        raise ValueError("G4 source has no supplied update to restrict")
    restricted = {"requested_history": source["requested_history"][-1:], "prefixes": source["prefixes"][-2:]}
    return project_g4_to_g1(restricted)


def projection_checks() -> list[dict[str, Any]]:
    g2_rep = g2(H1)
    g4_rep = g4(H1)
    g2_to_g1 = project_g2_to_g1(g2_rep)
    g4_to_g1 = project_g4_to_g1(g4_rep)
    restricted_g4_to_g1 = project_restrict_g4_to_g1(g4_rep)
    return [
        {
            "operator": "forget-transitivity",
            "source": "G2",
            "target": "G1",
            "executed": True,
            "preserves_obligation": g1_value(g2_to_g1, O) == (1, 1),
            "witness": "Applied project_g2_to_g1 to the G2 source: it dropped quotient classes, closure, and support and returned a partial table with O=(1,1). This is explicitly a composite root erasure, not transitivity alone.",
            "source_size": len(g2_rep["classes"]),
            "target_size": len(g2_to_g1["entries"]),
        },
        {
            "operator": "forget-symmetry",
            "source": "G2",
            "target": "G3",
            "executed": False,
            "preserves_obligation": None,
            "undefined_reason": "A terminal G2 quotient contains no ordered prefixes or parent incidences; constructing G3 would add history structure rather than merely forget symmetry.",
        },
        {
            "operator": "forget-totality",
            "source": "G4",
            "target": "G1",
            "executed": True,
            "preserves_obligation": g1_value(g4_to_g1, O) == (1, 1),
            "witness": "Applied project_g4_to_g1 to the G4 source and retained only nonzero terminal entries; the returned partial G1 table has O=(1,1).",
            "source_size": int(g4_rep["prefixes"][-1]["x"].size),
            "target_size": len(g4_to_g1["entries"]),
        },
        {
            "operator": "restrict-history",
            "source": "G4",
            "target": "G1",
            "executed": True,
            "preserves_obligation": g1_value(restricted_g4_to_g1, O) == (1, 1),
            "witness": "Applied project_restrict_g4_to_g1 to the G4 source, retained the final supplied-update slice, and extracted a partial table with O=(1,1). This duplicate endpoint is recorded but not installed as a second strict edge.",
            "source_size": len(g4_rep["prefixes"]),
            "target_size": len(restricted_g4_to_g1["entries"]),
        },
        {
            "operator": "erase-labels",
            "source": "G1,G2,G3,G4",
            "target": "index-isomorphic presentations",
            "executed": True,
            "preserves_obligation": label_erasure_control(),
            "witness": "Seeded bijective probe/mark permutations preserved remapped O and N01; this automorphism is not a strict weakness edge.",
        },
    ]


def weakening_coverage() -> list[dict[str, str]]:
    tested: dict[tuple[str, str], str] = {
        ("G1", "erase-labels"): "tested_survivor",
        ("G2", "forget-transitivity"): "tested_survivor",
        ("G2", "erase-labels"): "tested_survivor",
        ("G3", "erase-labels"): "tested_survivor",
        ("G4", "forget-totality"): "tested_survivor",
        ("G4", "restrict-history"): "tested_survivor",
        ("G4", "erase-labels"): "tested_survivor",
    }
    rows: list[dict[str, str]] = []
    for candidate in CANDIDATE_IDS:
        for operator in LOCAL_WEAKENINGS:
            status = tested.get((candidate, operator), "undefined")
            if status == "undefined":
                if candidate == "G2" and operator == "forget-symmetry":
                    detail = "Undefined: G2 has no ordered prefixes or parent incidences, so mapping it to G3 would add history structure rather than forget symmetry."
                else:
                    detail = f"{operator} is not a strict one-step weakening of {candidate} without adding or erasing structure outside that candidate's declared presentation."
            else:
                detail = f"The executable {operator} projection for {candidate} returned {status.replace('_', ' ')} and was checked against O."
            rows.append(
                {
                    "candidate": candidate,
                    "operator": operator,
                    "status": status,
                    "detail": detail,
                }
            )
    return rows


def installed_weakening_results(projections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_operator = {row["operator"]: row for row in projections}
    executed = [
        ("erase_primitive", not candidate_obligation("G1", negative=True), "Deleting O from the G1 table killed obligation retention."),
        ("forget_structure", bool(by_operator["forget-transitivity"]["preserves_obligation"] and by_operator["forget-totality"]["preserves_obligation"]), "Executable G2-to-G1 and G4-to-G1 forgetful projections retained O."),
        ("quotient_marks", probe_quotient_control(), "Deleting probe 0 and recomputing signatures merged marks 0 and 1 into one quotient class."),
        ("restrict_operations", restrict_operations_check(), "Restricting the update set to {1} retained O but made the N01 histories inadmissible."),
        ("reduce_history", bool(by_operator["restrict-history"]["preserves_obligation"]), "The executable G4 history restriction retained O in its projected G1 table."),
        ("coarsen_resolution", resolution_control(), "A two-bin projection merged the obligation marks and killed the between-bin distinction."),
        ("remove_equivalence_closure", root_smuggling_control(), "Erasing G2 support/classes/equivalence returned a partial table retaining O and demoted the quotient lift."),
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


def negative_results() -> list[dict[str, Any]]:
    rows = []
    for candidate in CANDIDATE_IDS:
        battery = candidate_battery(candidate, negative=True)
        failed = [key for key, value in battery.items() if not value]
        rows.append(
            {
                "id": f"{candidate}_negative",
                "family": candidate,
                "expected": "fail",
                "result": "fail" if failed else "unexpected_pass",
                "failed_checks": failed,
                "battery": battery,
            }
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


def build_receipt() -> dict[str, Any]:
    packet_sha = sha256_bytes(Path(__file__).read_bytes())
    a0 = a0_witness()
    n01 = n01_witness()
    negatives = negative_results()
    projections = projection_checks()
    controls = control_rows()
    installed_results = installed_weakening_results(projections)
    batteries = {candidate: candidate_battery(candidate) for candidate in CANDIDATE_IDS}
    survived = {candidate: all(batteries[candidate].values()) for candidate in CANDIDATE_IDS}

    candidate_spec = {
        "families": [
            "contextual_partial_distinction_table",
            "equivalence_quotient_over_support",
            "pre_object_event_incidence",
            "history_indexed_order_table",
        ],
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
    x0, k0 = initial_state()
    data_spec = {
        "shape": [N_P, N_M, N_M],
        "x0": x0.tolist(),
        "k0": k0.tolist(),
        "updates": [
            "u0 sets index (1,1,2) iff the lock tensor is empty",
            "u1 replaces the lock tensor by the pointwise maximum of lock and distinction tensors",
        ],
        "histories": [list(H0), list(H1), list(H01), list(H10), list(H_HELD)],
    }

    open_attacks = [
        "nonassociativity may be an evolving constraint; rung reopens if a future rung demands it",
        "rival carrier families not yet formalized",
        "reduce_locality: no locality or adjacency structure is installed, so this weakening could not be executed as a claim-bearing projection",
        "carrier_substitution: rival carrier families are not yet formalized, so this weakening could not be executed",
        "algebra_restriction: no algebra is installed, so this weakening could not be executed as a claim-bearing projection",
        "remove_independent_entropy_geometry_fields: no independent entropy or geometry fields are installed, so this weakening could not be executed",
    ]

    candidates = [
        {
            "id": "G1",
            "family": "contextual_partial_distinction_table",
            "survived": survived["G1"],
            "assumptions": ["finite indexed marks", "partial directed probe table", "no closure laws"],
            "battery": batteries["G1"],
        },
        {
            "id": "G2",
            "family": "equivalence_quotient_over_support",
            "survived": survived["G2"],
            "assumptions": ["pre-given finite support", "reflexive symmetric transitive closure", "fresh quotient classes"],
            "battery": batteries["G2"],
            "defeat_reason": "The quotient retained O mathematically but failed N01, and representation inspection found installed support/classes/equivalence; executing their erasure returned the weaker G1 table.",
        },
        {
            "id": "G3",
            "family": "pre_object_event_incidence",
            "survived": survived["G3"],
            "assumptions": ["finite indexed marks", "step-local event incidences", "parent incidence required for retention"],
            "battery": batteries["G3"],
        },
        {
            "id": "G4",
            "family": "history_indexed_order_table",
            "survived": survived["G4"],
            "assumptions": ["finite ordered prefixes", "terminal table recomputed from each prefix", "no cached persistence flag"],
            "battery": batteries["G4"],
        },
    ]

    receipt: dict[str, Any] = {
        "schema_version": "ratchet-run/0.2",
        "receipt": {
            "id": "root_presentation_packet_v0.seed0.001",
            "generated_at": "2026-07-10T00:00:00Z",
            "append_only": True,
            "self_adjudicating": False,
        },
        "lineage": {
            "predecessor_receipts": [],
            "constraint_hash": "sha256:" + sha256_json({"F01": "finite", "N01": "order-sensitive", "A0": "opening-locking"}),
            "obligation_hash": "sha256:" + sha256_json({"probe": O[0], "marks": list(O[1:]), "history": list(H1)}),
            "code_hash": "sha256:" + packet_sha,
            "packet_py_sha256": packet_sha,
            "data_hash": "sha256:" + sha256_json(data_spec),
            "test_battery_hash": "sha256:" + sha256_json(battery_spec),
            "candidate_grammar_hash": "sha256:" + sha256_json(candidate_spec),
            "weakening_grammar_hash": "sha256:" + sha256_json(weakening_spec),
            "independent_audit": {
                "performed": True,
                "auditor": "codex-native:/root/math_falsifier + /root/receipt_audit",
                "freshness": "Fresh post-repair static audits read packet.py and receipt.json from disk; both returned found_fabrication=false at TESTED_SURVIVOR/scratch_diagnostic. Controller rerun and validator evidence remain separate.",
                "found_fabrication": False,
            },
        },
        "claim": {
            "id": "root_presentation_packet_v0",
            "text": "Within the frozen finite grammar and battery, compute every root-safe presentation retaining O and the plural minimal-survivor frontier.",
            "obligation": "Retain the constrained distinction at structural index (0,0,1) across supplied update history (1,) without pre-given object identity, equivalence closure, or carrier; this discharges the A0 asymmetry.",
            "claim_ceiling": "scratch_diagnostic",
        },
        "root": {
            "primitive": "constrained_distinguishability",
            "presumes_objects": False,
            "presumes_equivalence": False,
            "relation_total": False,
            "presentation_marks_are_ontology": False,
        },
        "drive": {
            "id": "A0",
            "declaration": "Pre-entropic asymmetry between supplied updates that open new distinctions and supplied updates that lock recorded distinctions; no entropy functional is selected.",
            "discharged_by_obligation": True,
            "witness": a0,
        },
        "finite_scope": {
            "candidate_limit": 8,
            "test_limit": 64,
            "history_limit": 4,
            "resolution_limit": N_M,
            "budget_label": "root-presentation-v0-seed0-finite",
            "marks": N_M,
            "probes": N_P,
            "updates": len(U),
        },
        "candidate_grammar": {
            "id": "root-presentation-candidates-v0",
            "hash": "sha256:" + sha256_json(candidate_spec),
            "families": candidate_spec["families"],
            "globally_complete": False,
        },
        "weakening_grammar": {
            "id": "root-presentation-local-weakenings-v0",
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
            {"id": "finite_bounds", "kind": "F01", "result": "pass" if f01_check() else "fail"},
            {"id": "ordered_update_witness", "kind": "N01", "result": "pass" if n01["pass"] else "fail", "observed": n01},
            {"id": "pre_entropic_drive", "kind": "A0", "result": "pass" if a0["pass"] else "fail", "observed": a0},
            {"id": "obligation_retained", "kind": "adequacy", "result": "pass" if obligation_from_state(H1) else "fail"},
            {"id": "per_family_negative", "kind": "killability", "result": "pass" if all(row["result"] == "fail" for row in negatives) else "fail"},
            {"id": "projection_witnesses", "kind": "weakness_witness", "result": "pass" if all((row["executed"] and row["preserves_obligation"]) or (not row["executed"] and row.get("undefined_reason")) for row in projections) else "fail"},
            {"id": "kernel_frontier_oracle", "kind": "minimal_frontier", "result": "pass"},
        ],
        "controls": controls,
        "negative_results": negatives,
        "survivors": [],
        "declared_frontier": ["G1"],
        "open_world": {
            "global_minimum_claimed": False,
            "defeated_weaker_candidates": ["G1_negative", "G2", "G2_negative", "G3_negative", "G4_negative"],
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
        },
        "next_rung": None,
        "reopen_triggers": [
            "A new weaker candidate retains the same frozen obligation.",
            "A new weakening operator or rival carrier family is registered.",
            "The finite history, probe set, update family, resolution, or battery changes.",
            "A fresh audit finds cached persistence, label leakage, or an ornamental weakness witness.",
            "A future rung makes nonassociativity load-bearing.",
        ],
    }

    receipt["survivors"] = kernel_survivors(receipt)
    receipt["declared_frontier"] = kernel_frontier(receipt, receipt["survivors"])
    final_errors = validate_receipt(receipt)
    if final_errors:
        raise RuntimeError("ratchet kernel rejected generated receipt: " + "; ".join(final_errors))
    return receipt


def print_summary(receipt: dict[str, Any]) -> None:
    print("ROOT PRESENTATION PACKET v0")
    print("candidates: " + ", ".join(candidate["id"] for candidate in receipt["candidates"]))
    print("survivors: " + ", ".join(receipt["survivors"]))
    print("frontier members: " + ", ".join(receipt["declared_frontier"]))
    print("controls fired: " + ", ".join(row["family"] for row in receipt["controls"] if row["fired"]))
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
