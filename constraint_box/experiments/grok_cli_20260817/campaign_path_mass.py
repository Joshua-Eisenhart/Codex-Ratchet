"""Attach mass, joint entropy/topology, recall comparison, and SMT to the real campaign.

This operation does not spawn a new field. It reads the replayed
manifold-capability rows, applies the Mini-Lev/CB gates that already
existed, and measures leftover mass and the one-DOF mutation graph on
those same rows.

The 14-path policy enumerator is not this object.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any

from constraintbox.bound_quotient import decide_bound_packet
from constraintbox.constraint_path_mass import (
    PACKET_SCHEMA,
    _as_quaternion,
    _hopfield_recall,
    _hostile_label,
    _nearest_pattern,
    _quaternion_recall,
    _sha256,
    _sign_vec,
    _smt_problems,
)


RECEIPT_SCHEMA = "constraintbox.campaign-path-mass.receipt.v1"
OPERATION = "campaign_path_mass.v1"
EXPECTED_PROBE_ROWS = "7648f2d338fbfbf30cf937e469f112c2a4bbf0c93ce5ca20a0cae01a2375b6e2"
EXPECTED_GATE_ROWS = "eda6f185f7ea80f67254d34e335fd4a34304e880ee6799e236be5c48c4bf6683"
DEFAULT_RERUN = Path(
    "/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/receipts/manifold_capability/v1/rerun1"
)
DEFAULT_MINILEV = Path(
    "/Users/joshuaeisenhart/.config/superpowers/worktrees/Codex-Ratchet/"
    "constraintbox-integrated-20260817/constraint_box/receipts/"
    "first_released_run_20260809/run/proposal_minilev_flow/proposal_flow_receipt.json"
)
DOF_KEYS = (
    "mixture_angle_id",
    "corruption_mask_id",
    "corruption_angle_id",
    "rotation_sign_id",
    "bond_geometry_id",
    "dephasing_strength_id",
    "density_fault_id",
)
CORRUPTION_MASK_VALUES = (0, 1, 2, 4, 8, 3, 5, 15)
ERASED_BOND_ID = 3
QUOTIENT_PROBES = (
    "recall_class",
    "initial_nearest_memory",
    "bond_geometry_id",
    "qit_validity",
    "spinor_memory",
)
CLAIM_CEILING = (
    "replay of the existing finite campaign rows plus Mini-Lev/CB gate "
    "contraction; probe-relative leftover mass; one-DOF mutation graph; "
    "hash/Hopfield/quaternion/hostile retrieval of the recorded recall "
    "label; SMT writes admission; not an attractor basin, not a new "
    "6144-row campaign, not spinor-memory geometry, not a jointly "
    "evolving (S_C/~_P, mu_C)"
)
_NOT = (
    "attractor_basin",
    "new_cartesian_campaign",
    "physical_time",
    "jointly_evolving_mass_entropy_topology",
    "spinor_memory_geometry",
    "hopfield_energy_as_hartley",
    "promotion",
)


class CampaignMassError(ValueError):
    """The replayed campaign object could not be measured."""


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _coords(dofs: dict[str, int]) -> tuple[int, ...]:
    return tuple(int(dofs[key]) for key in DOF_KEYS)


def neighbor_coordinates(coordinates: tuple[int, ...]):
    mixture, mask_id, angle, sign, bond, dephase, fault = coordinates
    for delta in (-1, 1):
        changed = mixture + delta
        if 0 <= changed < 8:
            yield (changed, mask_id, angle, sign, bond, dephase, fault), "mixture_angle"
    mask = CORRUPTION_MASK_VALUES[mask_id]
    for other_id, other_mask in enumerate(CORRUPTION_MASK_VALUES):
        if (mask ^ other_mask).bit_count() == 1:
            yield (mixture, other_id, angle, sign, bond, dephase, fault), "corruption_bit"
    for delta in (-1, 1):
        changed = angle + delta
        if 0 <= changed < 2:
            yield (mixture, mask_id, changed, sign, bond, dephase, fault), "corruption_angle"
    yield (mixture, mask_id, angle, 1 - sign, bond, dephase, fault), "rotation_sign"
    for delta in (-1, 1):
        changed = bond + delta
        if 0 <= changed < 4:
            yield (mixture, mask_id, angle, sign, changed, dephase, fault), "bond_geometry"
    yield (mixture, mask_id, angle, sign, bond, 1 - dephase, fault), "dephasing"
    for changed in range(3):
        if changed != fault:
            yield (mixture, mask_id, angle, sign, bond, dephase, changed), "density_fault"


def load_campaign(rerun: Path) -> dict[str, Any]:
    probe_path = rerun / "probe_rows.jsonl"
    gate_path = rerun / "gate_rows.jsonl"
    map_path = rerun / "map.json"
    if not probe_path.is_file() or not gate_path.is_file():
        raise CampaignMassError(f"campaign replay is missing under {rerun}")
    probe_sha = _file_sha(probe_path)
    gate_sha = _file_sha(gate_path)
    if probe_sha != EXPECTED_PROBE_ROWS:
        raise CampaignMassError(f"probe_rows hash mismatch: {probe_sha}")
    if gate_sha != EXPECTED_GATE_ROWS:
        raise CampaignMassError(f"gate_rows hash mismatch: {gate_sha}")
    gates: dict[str, dict[str, Any]] = {}
    with gate_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            gates[row["candidate_id"]] = row["gate_dispositions"]
    rows: list[dict[str, Any]] = []
    with probe_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            cid = row["candidate_id"]
            dispositions = gates.get(cid) or {}
            observation = {
                "recall_class": int(round(row["probes"]["recall_class"])),
                "initial_nearest_memory": int(
                    round(row["probes"]["initial_nearest_memory"])
                ),
                "bond_geometry_id": int(row["dofs"]["bond_geometry_id"]),
                "qit_validity": dispositions.get("qit_validity") or "ABSENT",
                "spinor_memory": dispositions.get("spinor_memory") or "ABSENT",
            }
            rows.append(
                {
                    "id": cid,
                    "dofs": {key: int(row["dofs"][key]) for key in DOF_KEYS},
                    "observation": observation,
                    "coords": _coords(row["dofs"]),
                }
            )
    compact_map = json.loads(map_path.read_text(encoding="utf-8")) if map_path.is_file() else {}
    return {
        "rows": rows,
        "probe_sha256": probe_sha,
        "gate_sha256": gate_sha,
        "map_artifact": compact_map,
        "rerun": str(rerun),
    }


def load_minilev(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CampaignMassError(f"Mini-Lev receipt missing: {path}")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    return {
        "path": str(path),
        "sha256": _file_sha(path),
        "flow_id": receipt.get("flow_id"),
        "terminal": receipt.get("terminal"),
        "completed_nodes": list(receipt.get("completed_nodes") or []),
        "steps": receipt.get("steps"),
        "schema": receipt.get("schema"),
    }


def mutation_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    index = {row["coords"]: row["id"] for row in rows}
    edges: list[tuple[str, str, str]] = []
    axes: Counter[str] = Counter()
    labels = {row["id"]: row["observation"]["recall_class"] for row in rows}
    boundary = 0
    for row in rows:
        for neighbor, axis in neighbor_coordinates(row["coords"]):
            other = index.get(neighbor)
            if other is None or row["id"] >= other:
                continue
            edges.append((row["id"], other, axis))
            axes[axis] += 1
            if labels[row["id"]] != labels[other]:
                boundary += 1
    parent = {row["id"]: row["id"] for row in rows}

    def find(name: str) -> str:
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name

    for left, right, _axis in edges:
        parent[find(left)] = find(right)
    sizes = Counter(find(row["id"]) for row in rows)
    return {
        "n_nodes": len(rows),
        "n_edges": len(edges),
        "n_weak_components": len(sizes),
        "component_sizes": sorted(sizes.values(), reverse=True),
        "boundary_edge_count": boundary,
        "edge_axes": dict(sorted(axes.items())),
        "nodes_sha256": _sha256(sorted(row["id"] for row in rows)),
        "edges_sha256": _sha256(sorted(edges)),
    }


def _bound_packet(rows: list[dict[str, Any]], probes: tuple[str, ...], claim: str) -> dict[str, Any]:
    return {
        "schema": PACKET_SCHEMA,
        "claim": claim,
        "candidates": [row["id"] for row in rows],
        "probes": list(probes),
        "rows": [
            {"candidate": row["id"], "probe": probe, "value": row["observation"][probe]}
            for row in rows
            for probe in probes
        ],
        "authority": "none",
        "promotion_allowed": False,
    }


def _fast_quotient(rows: list[dict[str, Any]], probes: tuple[str, ...]) -> dict[str, Any]:
    """Induce S/~_P by grouping complete rows. Same classes as pairwise union-find."""

    groups: dict[tuple[Any, ...], list[str]] = {}
    for row in rows:
        key = tuple(row["observation"][probe] for probe in probes)
        groups.setdefault(key, []).append(row["id"])
    basins = [
        {"id": f"B{index}", "members": members, "size": len(members)}
        for index, members in enumerate(groups.values())
    ]
    distinct = len(groups)
    return {
        "status": "PASS",
        "quotient_admitted": True,
        "basins": basins,
        "packet_sha256": _sha256(_bound_packet(rows, probes, "fast-quotient")),
        "capacities": {
            "record": {
                "distinct_observation_tuples": distinct,
            }
        },
        "method": "complete_tuple_partition",
    }


def _mass(quotient: dict[str, Any], n_rows: int) -> list[dict[str, Any]]:
    if n_rows <= 0 or not quotient.get("quotient_admitted"):
        return []
    out = []
    for basin in quotient["basins"]:
        fraction = Fraction(int(basin["size"]), n_rows)
        out.append(
            {
                "id": basin["id"],
                "size": int(basin["size"]),
                "mu_numerator": fraction.numerator,
                "mu_denominator": fraction.denominator,
                "members_head": list(basin["members"][:8]),
            }
        )
    return out


def measure(
    rows: list[dict[str, Any]], probes: tuple[str, ...], claim: str
) -> dict[str, Any]:
    if not rows:
        return {
            "n_rows": 0,
            "entropy": {
                "support_W": 0,
                "support_K": 0.0,
                "class_count": 0,
                "record_K": 0.0,
                "released_like_selected": 0,
                "erased_bond_count": 0,
            },
            "topology": {
                "n_nodes": 0,
                "n_edges": 0,
                "n_weak_components": 0,
                "component_sizes": [],
                "boundary_edge_count": 0,
                "nodes_sha256": _sha256([]),
                "edges_sha256": _sha256([]),
            },
            "mass": [],
            "quotient_admitted": False,
        }
    packet = _bound_packet(rows, probes, claim)
    if len(rows) <= 1200:
        quotient = decide_bound_packet(packet)
    else:
        quotient = _fast_quotient(rows, probes)
    n_classes = len(quotient.get("basins") or [])
    distinct = int(
        (quotient.get("capacities") or {})
        .get("record", {})
        .get("distinct_observation_tuples", 0)
    )
    selected = sum(
        1
        for row in rows
        if row["observation"]["qit_validity"] == "PASS"
        and row["observation"]["spinor_memory"] == "PASS"
    )
    erased = sum(1 for row in rows if row["observation"]["bond_geometry_id"] == ERASED_BOND_ID)
    return {
        "n_rows": len(rows),
        "probes": list(probes),
        "packet_sha256": quotient.get("packet_sha256"),
        "quotient_admitted": bool(quotient.get("quotient_admitted")),
        "mass": _mass(quotient, len(rows)),
        "entropy": {
            "support_W": len(rows),
            "support_K": math.log2(len(rows)) if rows else 0.0,
            "class_count": n_classes,
            "record_K": math.log2(distinct) if distinct else 0.0,
            "record_distinct_tuples": distinct,
            "released_like_selected": selected,
            "erased_bond_count": erased,
        },
        "topology": mutation_graph(rows),
    }


def _delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {
        "support_W": after["entropy"]["support_W"] - before["entropy"]["support_W"],
        "record_K": after["entropy"]["record_K"] - before["entropy"]["record_K"],
        "class_count": after["entropy"]["class_count"] - before["entropy"]["class_count"],
        "erased_bond_count": after["entropy"]["erased_bond_count"]
        - before["entropy"]["erased_bond_count"],
        "n_edges": after["topology"]["n_edges"] - before["topology"]["n_edges"],
        "n_weak_components": after["topology"]["n_weak_components"]
        - before["topology"]["n_weak_components"],
        "boundary_edge_count": after["topology"]["boundary_edge_count"]
        - before["topology"]["boundary_edge_count"],
        "node_set_changed": before["topology"]["nodes_sha256"]
        != after["topology"]["nodes_sha256"],
        "edge_set_changed": before["topology"]["edges_sha256"]
        != after["topology"]["edges_sha256"],
    }


def _changes_entropy(delta: dict[str, Any]) -> bool:
    return (
        delta["support_W"] != 0
        or delta["record_K"] != 0.0
        or delta["class_count"] != 0
        or delta["erased_bond_count"] != 0
    )


def _changes_topology(delta: dict[str, Any]) -> bool:
    return (
        delta["n_edges"] != 0
        or delta["n_weak_components"] != 0
        or delta["boundary_edge_count"] != 0
        or delta["node_set_changed"]
        or delta["edge_set_changed"]
    )


def _onehot(value: int, size: int) -> list[int]:
    bits = [-1] * size
    if 0 <= value < size:
        bits[value] = 1
    return bits


def _feature(row: dict[str, Any]) -> tuple[int, ...]:
    dofs = row["dofs"]
    bits: list[int] = []
    bits.extend(_onehot(dofs["mixture_angle_id"], 8))
    bits.extend(_onehot(dofs["corruption_mask_id"], 8))
    bits.extend(_onehot(dofs["corruption_angle_id"], 2))
    bits.extend(_onehot(dofs["rotation_sign_id"], 2))
    bits.extend(_onehot(dofs["bond_geometry_id"], 4))
    bits.extend(_onehot(dofs["dephasing_strength_id"], 2))
    bits.extend(_onehot(dofs["density_fault_id"], 3))
    bits.append(1 if row["observation"]["initial_nearest_memory"] else -1)
    return tuple(bits)


def score_recall(rows: list[dict[str, Any]], *, erased: bool) -> dict[str, Any]:
    if not rows:
        return {"status": "HOLD", "reason": "NO_ROWS"}
    labels = sorted({str(row["observation"]["recall_class"]) for row in rows})
    members: dict[str, list[str]] = {label: [] for label in labels}
    vectors = {row["id"]: _feature(row) for row in rows}
    for row in rows:
        members[str(row["observation"]["recall_class"])].append(row["id"])
    prototypes: list[tuple[str, tuple[int, ...]]] = []
    hash_store: dict[tuple[int, ...], str] = {}
    if not erased:
        for label in labels:
            acc = [0] * len(next(iter(vectors.values())))
            for path_id in members[label]:
                for index, bit in enumerate(vectors[path_id]):
                    acc[index] += bit
            prototypes.append((label, _sign_vec(acc)))
        for row in rows:
            hash_store.setdefault(row["coords"], str(row["observation"]["recall_class"]))
    correct = {
        "hash_lookup": 0,
        "scalar_hopfield": 0,
        "quaternion_recall": 0,
        "hostile_random": 0,
    }
    survivors = {name: 0 for name in correct}
    for row in rows:
        truth = str(row["observation"]["recall_class"])
        hash_guess = hash_store.get(row["coords"])
        hopfield_state = _hopfield_recall(
            vectors[row["id"]], [pattern for _, pattern in prototypes]
        )
        hopfield_guess = (
            _nearest_pattern(hopfield_state, prototypes) if hopfield_state else None
        )
        quat_guess = _quaternion_recall(vectors[row["id"]], prototypes)
        hostile_guess = _hostile_label(row["id"], labels) if labels and not erased else None
        guesses = {
            "hash_lookup": hash_guess,
            "scalar_hopfield": hopfield_guess,
            "quaternion_recall": quat_guess,
            "hostile_random": hostile_guess,
        }
        for name, guess in guesses.items():
            if guess is not None:
                survivors[name] += 1
            if guess is not None and guess == truth:
                correct[name] += 1
    return {
        "status": "PASS",
        "erased": erased,
        "n_rows": len(rows),
        "n_classes": len(labels),
        "correct": correct,
        "survivors": survivors,
        "label_note": "target is the campaign's recorded recall_class; spinor is the label, not a peer method",
    }


def _jax_crossing(rows: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        import jax
        import jax.numpy as jnp
    except ImportError:
        return {"status": "HOLD", "reason": "jax_not_importable", "ran": False}
    if not rows:
        return {"status": "HOLD", "reason": "NO_ROWS", "ran": False}
    # Compare one prototype-overlap step on a bounded sample.
    sample = rows[:64]
    python = []
    jax_out = []
    labels = sorted({str(row["observation"]["recall_class"]) for row in rows})
    members = {label: [] for label in labels}
    vectors = {row["id"]: _feature(row) for row in rows}
    for row in rows:
        members[str(row["observation"]["recall_class"])].append(row["id"])
    prototypes = []
    dim = len(next(iter(vectors.values())))
    for label in labels:
        acc = [0] * dim
        for path_id in members[label]:
            for index, bit in enumerate(vectors[path_id]):
                acc[index] += bit
        prototypes.append((label, _sign_vec(acc)))
    stack = jnp.asarray([pattern for _, pattern in prototypes], dtype=jnp.int32)
    for row in sample:
        query = vectors[row["id"]]
        state = _hopfield_recall(query, [pattern for _, pattern in prototypes])
        python.append(_nearest_pattern(state, prototypes) if state else None)
        q = jnp.asarray(query, dtype=jnp.int32)
        weights = jnp.zeros((dim, dim), dtype=jnp.int32)
        for pattern in stack:
            weights = weights + jnp.outer(pattern, pattern)
        weights = weights.at[jnp.diag_indices(dim)].set(0)
        cur = q
        for _ in range(8):
            acc = weights @ cur
            cur = jnp.where(acc > 0, 1, jnp.where(acc < 0, -1, cur))
        overlaps = stack @ cur
        if int(jnp.max(overlaps)) <= 0:
            jax_out.append(None)
        else:
            jax_out.append(prototypes[int(jnp.argmax(overlaps))][0])
    return {
        "status": "PASS" if python == jax_out else "HOLD",
        "ran": True,
        "jax_version": str(jax.__version__),
        "hopfield_agree": python == jax_out,
        "sample": len(sample),
        "prefix_is_jax_qit_stack": "jax-qit-stack" in sys.prefix,
    }


def run_campaign_path_mass(
    rerun: Path | None = None,
    minilev: Path | None = None,
) -> dict[str, Any]:
    rerun = Path(os.environ.get("CB_CAMPAIGN_RERUN", rerun or DEFAULT_RERUN))
    minilev = Path(os.environ.get("CB_MINILEV_RECEIPT", minilev or DEFAULT_MINILEV))
    campaign = load_campaign(rerun)
    minilev_info = load_minilev(minilev)
    rows = campaign["rows"]
    probes = QUOTIENT_PROBES

    def select(predicate) -> list[dict[str, Any]]:
        return [row for row in rows if predicate(row)]

    both = select(
        lambda row: row["observation"]["qit_validity"] == "PASS"
        and row["observation"]["spinor_memory"] == "PASS"
    )
    qit = select(lambda row: row["observation"]["qit_validity"] == "PASS")
    erased = select(lambda row: row["observation"]["bond_geometry_id"] == ERASED_BOND_ID)
    erased_selected = [
        row
        for row in both
        if row["observation"]["bond_geometry_id"] == ERASED_BOND_ID
    ]

    # Mini-Lev first_released_run was topology PASS, observed, gate PASS, claim PASS.
    ratchet_spec = [
        ("minilev_topology_pass", rows, "all measured campaign rows"),
        ("minilev_proposal_gate", qit, "CB qit_validity PASS — proposal-gate analogue"),
        ("minilev_claim_gate", both, "CB spinor_memory PASS — claim-gate analogue"),
    ]
    ratchet = []
    previous = None
    both_changed = False
    for name, subset, why in ratchet_spec:
        measured = measure(subset, probes, why)
        entry = {
            "step": name,
            "why": why,
            "n_rows": measured["n_rows"],
            "entropy": measured["entropy"],
            "topology": {
                key: measured["topology"][key]
                for key in (
                    "n_nodes",
                    "n_edges",
                    "n_weak_components",
                    "component_sizes",
                    "boundary_edge_count",
                )
            },
            "mass": measured["mass"],
            "quotient_admitted": measured["quotient_admitted"],
            "packet_sha256": measured.get("packet_sha256"),
        }
        if previous is not None:
            delta = _delta(previous, measured)
            entry["delta_from_previous"] = delta
            entry["changes_entropy"] = _changes_entropy(delta)
            entry["changes_topology"] = _changes_topology(delta)
            if entry["changes_entropy"] and entry["changes_topology"]:
                both_changed = True
        ratchet.append(entry)
        previous = measured

    restricted = measure(both, ("recall_class",), "probe restriction to recall_class")
    selected_full = measure(both, probes, "gated survivors under the full probe family")
    restrict_delta = _delta(selected_full, restricted)
    probe_restriction_entropy_only = _changes_entropy(restrict_delta) and not _changes_topology(
        restrict_delta
    )

    independent = [
        {
            "id": "erase_bond",
            "n_rows": len(erased),
            "selected_survivors": len(erased_selected),
            "why": "bond_geometry_id=3 is the campaign erased bond",
        }
    ]

    stored = score_recall(both, erased=False)
    wiped = score_recall(both, erased=True)
    facts = {
        "fact_hash_exact": int(
            stored.get("status") == "PASS"
            and stored["correct"]["hash_lookup"] == stored["n_rows"]
        ),
        "fact_hopfield_beats_hostile": int(
            stored["correct"]["scalar_hopfield"] > stored["correct"]["hostile_random"]
        ),
        "fact_spinor_beats_hostile": int(
            stored["correct"]["quaternion_recall"] > stored["correct"]["hostile_random"]
        ),
        "fact_erased_hash_empty": int(wiped["survivors"]["hash_lookup"] == 0),
        "fact_erased_hopfield_empty": int(wiped["survivors"]["scalar_hopfield"] == 0),
        "fact_erased_spinor_empty": int(wiped["survivors"]["quaternion_recall"] == 0),
        "fact_probe_restriction_entropy_only": int(probe_restriction_entropy_only),
        "fact_some_mutation_changes_both": int(both_changed),
    }
    smt = _smt_problems(facts)
    reconstructed = selected_full["topology"]
    expected_map = campaign["map_artifact"]
    map_replay = {
        "n_nodes": reconstructed["n_nodes"],
        "n_edges": reconstructed["n_edges"],
        "components": reconstructed["n_weak_components"],
        "component_sizes": reconstructed["component_sizes"],
        "boundary_edge_count": reconstructed["boundary_edge_count"],
        "matches_compact_map": (
            reconstructed["n_nodes"] == expected_map.get("nodes")
            and reconstructed["n_edges"] == expected_map.get("edges")
            and reconstructed["n_weak_components"] == expected_map.get("components")
            and reconstructed["component_sizes"] == expected_map.get("component_sizes")
            and reconstructed["boundary_edge_count"]
            == expected_map.get("boundary_edge_count")
        ),
    }
    status = (
        "PASS"
        if (
            selected_full["quotient_admitted"]
            and map_replay["matches_compact_map"]
            and len(both) == 972
            and len(erased_selected) == 0
            and smt["real_memory"]["agree"]
            and smt["real_memory"]["z3"] == "BOUNDED_SAT"
            and smt["real_memory"]["witness"] is not None
            and smt["erased_memory"]["agree"]
            and smt["erased_memory"]["z3"] == "BOUNDED_UNSAT"
            and minilev_info["terminal"] == "RELEASED"
            and minilev_info["flow_id"]
            == "constraintbox.bounded-proposal-retry-claim.v1"
        )
        else "HOLD"
    )
    payload = {
        "schema": RECEIPT_SCHEMA,
        "operation": OPERATION,
        "status": status,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "not": list(_NOT),
        "generator": {
            "rerun": campaign["rerun"],
            "probe_rows_sha256": campaign["probe_sha256"],
            "gate_rows_sha256": campaign["gate_sha256"],
            "n_probe_rows": len(rows),
            "n_qit_pass": len(qit),
            "n_both_pass": len(both),
            "minilev": minilev_info,
        },
        "ratchet": ratchet,
        "probe_restriction": {
            "entropy": restricted["entropy"],
            "topology": {
                key: restricted["topology"][key]
                for key in (
                    "n_nodes",
                    "n_edges",
                    "n_weak_components",
                    "boundary_edge_count",
                )
            },
            "delta_from_gated_full_probes": restrict_delta,
            "changes_entropy": _changes_entropy(restrict_delta),
            "changes_topology": _changes_topology(restrict_delta),
        },
        "independent": independent,
        "map_replay": map_replay,
        "recall": {"stored": stored, "erased": wiped},
        "jax_crossing": _jax_crossing(both),
        "smt": smt,
        "disposition": smt["real_memory"]["witness"],
    }
    payload["receipt_sha256"] = _sha256(
        {key: value for key, value in payload.items() if key != "receipt_sha256"}
    )
    return payload


def write_receipt(path: Path, **kwargs: Any) -> dict[str, Any]:
    receipt = run_campaign_path_mass(**kwargs)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=OPERATION)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("receipts/campaign_path_mass/v1/result.json"),
    )
    args = parser.parse_args()
    receipt = write_receipt(args.out)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "receipt_sha256": receipt["receipt_sha256"],
                "n_both": receipt["generator"]["n_both_pass"],
                "map_replay": receipt["map_replay"],
                "smt_real": receipt["smt"]["real_memory"]["z3"],
                "smt_erased": receipt["smt"]["erased_memory"]["z3"],
                "disposition": receipt["disposition"],
                "jax": receipt["jax_crossing"],
            },
            sort_keys=True,
        )
    )
    return 0 if receipt["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
