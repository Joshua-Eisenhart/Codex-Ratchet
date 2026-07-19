#!/usr/bin/env python3
"""Redundant finite connection layer for the v8 deep manifold lane."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

from common import digest, write_json

INPUTS = Path(__file__).resolve().parents[1] / "inputs"
sys.path.insert(0, str(INPUTS))

from finite_algebra import spinor_memory_report  # noqa: E402
import finite_qca_runner_trajectories_v0_exact as qca  # noqa: E402


State = tuple[int, int, int]


def state_key(state: State) -> str:
    return "".join(str(bit) for bit in state)


def pack_bits(bits: State, positions: tuple[int, int, int]) -> int:
    value = 0
    for bit, position in zip(bits, positions):
        value |= (bit & 1) << position
    return value


def read_bits(value: int, positions: tuple[int, int, int]) -> State:
    return tuple((value >> position) & 1 for position in positions)  # type: ignore[return-value]


def identity_transport(state: State) -> State:
    return state


def spinor_parity_transport(state: State) -> State:
    report = spinor_memory_report()
    sign_bit = int(report["overlaps_0_2pi_4pi"][1] < 0)
    density_erased = int(max(report["density_distances"]) < 1e-12)
    a, b, c = state
    return (a ^ (sign_bit & c), b, c ^ (density_erased & a & b))


def qca_permutation_transport(state: State) -> State:
    embedded = pack_bits(state, (0, 2, 4))
    moved = qca.transition("right_shift", embedded)
    return read_bits(moved, (2, 3, 4))


TRANSPORTS: tuple[tuple[str, Callable[[State], State], str, int], ...] = (
    ("identity_transport", identity_transport, "default literal inner-to-outer coordinates", 0),
    ("spinor_parity_sign_transport", spinor_parity_transport, "spinor lift sign and density-erased parity", 1),
    ("qca_permutation_transport", qca_permutation_transport, "right-shift finite QCA transition table projection", 2),
)


def states_from_packet(packet: dict[str, Any], layer: int) -> list[State]:
    return [tuple(int(bit) for bit in state) for state in packet["layer_values"][layer]]


def evaluate_transport(name: str, fn: Callable[[State], State], source: dict[str, Any]) -> dict[str, Any]:
    packet_rows = {}
    transport_table: dict[str, list[int]] = {}
    for packet in source["nesting_packets"]:
        outer_values = set(states_from_packet(packet, 0))
        inner_values = states_from_packet(packet, 2)
        violations = []
        for inner in sorted(inner_values):
            transported = fn(inner)
            transport_table[state_key(inner)] = list(transported)
            if transported not in outer_values:
                violations.append({
                    "state": list(inner),
                    "transport": name,
                    "transported_outer": list(transported),
                    "witness": "transported inner state is absent from the packet outer layer",
                })
        packet_rows[packet["packet_id"]] = {
            "inner_state_count": len(inner_values),
            "outer_state_count": len(outer_values),
            "transported_outer_count": len({tuple(fn(inner)) for inner in inner_values}),
            "violations": violations,
            "all_inner_states_outer_admissible": not violations,
        }
    all_admissible = all(row["all_inner_states_outer_admissible"] for row in packet_rows.values())
    first_violation = next((row["violations"][0] for row in packet_rows.values() if row["violations"]), None)
    return {
        "candidate_id": name,
        "packet_results": packet_rows,
        "transport_table": transport_table,
        "all_transports_admissible": all_admissible,
        "first_violation": first_violation,
    }


def run(source: dict[str, Any], prior_whole: dict[str, Any]) -> dict[str, Any]:
    candidates = {
        name: {
            **evaluate_transport(name, fn, source),
            "derivation": derivation,
            "connection_cost": cost,
        }
        for name, fn, derivation, cost in TRANSPORTS
    }
    frontier = sorted(name for name, row in candidates.items() if row["all_transports_admissible"])
    default = "identity_transport" if "identity_transport" in frontier else frontier[0]
    purgatory = [
        {
            "candidate_id": name,
            "witness": row["first_violation"],
            "reoffer_rule": "re-offer if a later source packet makes every transported inner state outer-admissible",
        }
        for name, row in sorted(candidates.items())
        if name not in frontier
    ]
    receipt = {
        "step": 0,
        "reason": "propose and settle finite transport candidates against nesting packet outer layers",
        "frontier": frontier,
        "default": default,
        "purgatory": purgatory,
        "candidate_count_recomputed": len(candidates),
        "global_mss_claimed": False,
        "terminal_state": False,
    }
    receipt["receipt_digest"] = digest(receipt)
    checks = {
        "source_packet_count_pinned_9": len(source.get("base_packets", [])) == 9,
        "source_all_pass": source.get("all_pass") is True,
        "prior_whole_all_pass": prior_whole.get("all_pass") is True,
        "three_transport_candidates_including_default": set(candidates) == {row[0] for row in TRANSPORTS},
        "qca_transport_survives": "qca_permutation_transport" in frontier,
        "excluded_candidates_have_concrete_witnesses": all(row["witness"] for row in purgatory),
        "frontier_nonempty": bool(frontier),
        "no_promotion": True,
    }
    result = {
        "schema": "ratchet.pack183.deep.connection-alt.v1",
        "source_packet_digest": source["result_digest"],
        "prior_whole_digest": prior_whole["result_digest"],
        "candidate_count": len(candidates),
        "candidate_evaluations": candidates,
        "frontier": frontier,
        "operational_default": default,
        "purgatory": purgatory,
        "receipts": [receipt],
        "checks": checks,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "global_mss_claimed": False,
        "terminal_state": False,
        "claim_ceiling": "packet-relative finite transport admissibility only; no canonical connection or physical transport claim",
    }
    result["all_pass"] = all(checks.values())
    result["result_digest"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    prior = json.loads(args.prior.read_text(encoding="utf-8"))
    result = run(source, prior)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "candidate_count": result["candidate_count"],
        "frontier": result["frontier"],
        "default": result["operational_default"],
        "failed_transports": [row["candidate_id"] for row in result["purgatory"]],
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
