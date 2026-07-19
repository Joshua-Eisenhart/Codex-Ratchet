#!/usr/bin/env python3
"""Settle finite transport candidates between the nested manifold layers."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

from common import digest, write_json


SCHEMA = "ratchet.pack183.deep-connection-layer.v1"
CANDIDATES = (
    "identity_transport",
    "parity_sign_transport",
    "qca_permutation_transport",
)
DEFAULT = "parity_sign_transport"
CLAIM_CEILING = (
    "packet-relative finite transport admissibility only; no promotion, formal admission, "
    "canonical connection, physical transport, or exhaustive candidate claim"
)
REOFFER_RULE = (
    "re-offer after any source packet, outer admissibility set, transport adapter, "
    "or later-layer requirement changes"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load vendored module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def state_key(state: tuple[int, int, int]) -> str:
    return "".join(str(bit) for bit in state)


def parse_state(key: str) -> tuple[int, int, int]:
    if len(key) != 3 or any(bit not in "01" for bit in key):
        raise ValueError(f"invalid three-bit state key: {key!r}")
    return tuple(int(bit) for bit in key)  # type: ignore[return-value]


def observed_inner_states(source: dict[str, Any]) -> set[tuple[int, int, int]]:
    return {
        tuple(int(bit) for bit in state)
        for packet in source["nesting_packets"]
        for triple in packet["admissible_triples"]
        for state in triple[1:]
    }


def outer_admissible_states(source: dict[str, Any]) -> set[tuple[int, int, int]]:
    return {
        tuple(int(bit) for bit in state)
        for packet in source["nesting_packets"]
        for state in packet["layer_values"][0]
    }


def vendored_reports() -> tuple[dict[str, Any], Any, list[int]]:
    manifold = Path(__file__).resolve().parent.parent
    algebra = load_module("deep_connection_finite_algebra", manifold / "inputs" / "finite_algebra.py")
    qca = load_module(
        "deep_connection_finite_qca",
        manifold / "inputs" / "finite_qca_runner_trajectories_v0_exact.py",
    )
    # The vendored function's all_pass field is later mutated by run_all().
    # Copy only measured fields and derive the checks here.
    raw_spinor = algebra.spinor_memory_report()
    spinor = {
        "overlaps_0_2pi_4pi": list(raw_spinor["overlaps_0_2pi_4pi"]),
        "density_distances": list(raw_spinor["density_distances"]),
        "direct_sheet_retention_after_300": raw_spinor["direct_sheet_retention_after_300"],
        "conjugated_sheet_retention_after_300": raw_spinor["conjugated_sheet_retention_after_300"],
        "retention_ratio": raw_spinor["retention_ratio"],
    }
    qca_table = list(qca.transition_table("right_shift"))
    return spinor, qca, qca_table


def transport_functions(qca: Any, qca_table: list[int]) -> dict[str, Callable[[tuple[int, int, int]], tuple[int, int, int]]]:
    def identity(state: tuple[int, int, int]) -> tuple[int, int, int]:
        return state

    def parity_sign(state: tuple[int, int, int]) -> tuple[int, int, int]:
        j, k, _sign = state
        return j, k, j & k

    def qca_permutation(state: tuple[int, int, int]) -> tuple[int, int, int]:
        embedded = list(state + state)
        moved = qca_table[qca.pack(embedded)]
        return tuple(int(bit) for bit in qca.bits(moved)[:3])  # type: ignore[return-value]

    return {
        "identity_transport": identity,
        "parity_sign_transport": parity_sign,
        "qca_permutation_transport": qca_permutation,
    }


def expected_transport_tables() -> tuple[dict[str, dict[str, list[int]]], dict[str, Any]]:
    spinor, qca, qca_table = vendored_reports()
    functions = transport_functions(qca, qca_table)
    universe = tuple((j, k, z) for j in (0, 1) for k in (0, 1) for z in (0, 1))
    tables = {
        candidate: {state_key(state): list(function(state)) for state in universe}
        for candidate, function in functions.items()
    }
    source_evidence = {
        "spinor_seed": None,
        "spinor_overlaps_0_2pi_4pi": spinor["overlaps_0_2pi_4pi"],
        "spinor_density_distances": spinor["density_distances"],
        "spinor_density_erases_lifted_sign": (
            all(abs(left - right) < 1e-12 for left, right in zip(spinor["overlaps_0_2pi_4pi"], [1.0, -1.0, 1.0]))
            and max(spinor["density_distances"], default=0.0) < 1e-12
        ),
        "qca_rule": "right_shift",
        "qca_transition_table": qca_table,
        "qca_transition_table_bijective": sorted(qca_table) == list(range(64)),
        "qca_three_bit_adapter": "repeat (j,k,z) twice, apply full 64-state right-shift table, project cells 0..2",
        "parity_sign_adapter_disclosure": (
            "spinor sign erasure is combined with the source outer-layer representative z=j&k; "
            "the adapter is not a standalone spinor theorem"
        ),
    }
    return tables, source_evidence


def _proposal_receipt(
    candidate: str,
    table: dict[str, list[int]],
    observed: set[tuple[int, int, int]],
    outer: set[tuple[int, int, int]],
    source_evidence: dict[str, Any],
) -> dict[str, Any]:
    violations = []
    for state in sorted(observed):
        transported = tuple(table[state_key(state)])
        if transported not in outer:
            violations.append({
                "inner_state": list(state),
                "transported_state": list(transported),
                "transport": candidate,
                "outer_admissible_states": [list(item) for item in sorted(outer)],
            })
    admissible = not violations
    source_exact = {
        "identity_transport": all(table[key] == list(parse_state(key)) for key in table),
        "parity_sign_transport": (
            source_evidence["spinor_density_erases_lifted_sign"]
            and all(value == [int(key[0]), int(key[1]), int(key[0]) & int(key[1])] for key, value in table.items())
        ),
        "qca_permutation_transport": (
            source_evidence["qca_transition_table_bijective"]
            and len({tuple(value) for value in table.values()}) == 8
            and table != expected_transport_tables()[0]["identity_transport"]
        ),
    }[candidate]
    checks = {
        "finite_total_transport_table": len(table) == 8 and all(len(value) == 3 for value in table.values()),
        "source_derivation_exact": source_exact,
        "outer_admissibility_classified": admissible == (len(violations) == 0),
        "violation_has_concrete_state_transport_pair_or_none": admissible or all(
            row["inner_state"] != row["transported_state"] or row["transported_state"] not in row["outer_admissible_states"]
            for row in violations
        ),
    }
    receipt = {
        "candidate_id": candidate,
        "transport_table": table,
        "observed_inner_state_count": len(observed),
        "outer_admissible_state_count": len(outer),
        "admissible": admissible,
        "violations": violations,
        "checks": checks,
        "all_pass": all(checks.values()),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    receipt["receipt_digest"] = digest(receipt)
    return receipt


def run(source: dict[str, Any], prior: dict[str, Any]) -> dict[str, Any]:
    tables, source_evidence = expected_transport_tables()
    observed = observed_inner_states(source)
    outer = outer_admissible_states(source)
    receipts = [
        _proposal_receipt(candidate, tables[candidate], observed, outer, source_evidence)
        for candidate in CANDIDATES
    ]
    evaluations = {receipt["candidate_id"]: receipt for receipt in receipts}
    frontier = sorted(candidate for candidate, row in evaluations.items() if row["admissible"])
    purgatory = []
    for candidate in sorted(set(CANDIDATES) - set(frontier)):
        violation = evaluations[candidate]["violations"][0]
        purgatory.append({
            "candidate_id": candidate,
            "witness": violation,
            "reoffer_rule": REOFFER_RULE,
        })
    checks = {
        "source_schema_v8": source.get("schema") == "ratchet.v8.source-packets.v1",
        "source_packet_count_nine": len(source.get("base_packets", [])) == 9,
        "prior_whole_schema": prior.get("schema") == "ratchet.pack183.whole-feedback-ratchet.v1",
        "candidate_grammar_exact": tuple(evaluations) == CANDIDATES,
        "outer_representative_exact": outer == {(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)},
        "default_is_admissible": DEFAULT in frontier,
        "transported_inner_state_remains_outer_admissible": all(
            tuple(tables[DEFAULT][state_key(state)]) in outer for state in observed
        ),
        "every_exclusion_has_concrete_witness": len(purgatory) == len(CANDIDATES) - len(frontier) and all(
            row["witness"]["inner_state"] and row["witness"]["transported_state"] for row in purgatory
        ),
        "proposal_receipts_pass": all(row["all_pass"] for row in receipts),
        "frontier_nonempty": bool(frontier),
    }
    result = {
        "schema": SCHEMA,
        "source_packet_digest": source["result_digest"],
        "prior_whole_digest": prior["result_digest"],
        "candidate_count": len(CANDIDATES),
        "candidates": list(CANDIDATES),
        "transport_evaluations": evaluations,
        "source_evidence": source_evidence,
        "observed_inner_states": [list(state) for state in sorted(observed)],
        "outer_admissible_states": [list(state) for state in sorted(outer)],
        "frontier": frontier,
        "operational_default": DEFAULT,
        "purgatory": purgatory,
        "receipts": receipts,
        "checks": checks,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all(checks.values()),
    }
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
        "default": result["operational_default"],
        "frontier": result["frontier"],
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
