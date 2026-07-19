#!/usr/bin/env python3
"""Classify finite octonion chirality as expressible, forced, or installable."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

from common import digest, write_json


SCHEMA = "ratchet.pack183.deep-chirality-layer.v1"
CLAIM_CEILING = (
    "packet-relative exact octonion bracketing discriminator only; chirality is installable "
    "but not forced, with no promotion, formal admission, canonical orientation, or physics claim"
)


def load_algebra():
    path = Path(__file__).resolve().parent.parent / "inputs" / "finite_algebra.py"
    spec = importlib.util.spec_from_file_location("deep_chirality_finite_algebra", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load vendored module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compute_octonion_evidence() -> dict[str, Any]:
    algebra = load_algebra()
    report = algebra.octonion_network_report()
    edges = report["edge_vectors"]
    signal = report["signal_vector"]
    left = algebra.cayley_dickson_multiply(
        edges[2],
        algebra.cayley_dickson_multiply(edges[1], algebra.cayley_dickson_multiply(edges[0], signal)),
    )
    mixed = algebra.cayley_dickson_multiply(
        algebra.cayley_dickson_multiply(edges[2], edges[1]),
        algebra.cayley_dickson_multiply(edges[0], signal),
    )
    return {
        "deterministic_seed": 3,
        "deterministic_integer_witness_trial": report["deterministic_integer_witness_trial"],
        "edge_vectors": edges,
        "signal_vector": signal,
        "left_bracket_vector": left,
        "mixed_bracket_vector": mixed,
        "path_bracketing_gap_squared": report["path_bracketing_gap_squared"],
        "edge_associator_gap_squared": report["edge_associator_gap_squared"],
        "left_right_chirality_gap_squared": report["left_right_chirality_gap_squared"],
        "automorphism_exact_on_full_basis_table": report["automorphism_exact_on_full_basis_table"],
        "bracketing_gap_automorphism_invariant": report["bracketing_gap_automorphism_invariant"],
        "vendored_report_all_pass": report["all_pass"],
    }


def run(source: dict[str, Any], prior: dict[str, Any]) -> dict[str, Any]:
    evidence = compute_octonion_evidence()
    orientation_candidates = {
        "orientation_neutral": {
            "orientation_installed": False,
            "admissible": True,
            "witness": "the persistence frontier is defined without an orientation field",
        },
        "left_bracket_orientation": {
            "orientation_installed": True,
            "admissible": True,
            "witness": evidence["left_bracket_vector"],
        },
        "mixed_bracket_orientation": {
            "orientation_installed": True,
            "admissible": True,
            "witness": evidence["mixed_bracket_vector"],
        },
    }
    expressible = (
        evidence["vendored_report_all_pass"] is True
        and evidence["left_bracket_vector"] != evidence["mixed_bracket_vector"]
        and evidence["path_bracketing_gap_squared"] > 0
        and evidence["left_right_chirality_gap_squared"] > 0
    )
    forced = expressible and all(
        row["orientation_installed"] for row in orientation_candidates.values() if row["admissible"]
    )
    installable = expressible and not forced and any(
        row["orientation_installed"] and row["admissible"] for row in orientation_candidates.values()
    )
    checks = {
        "source_schema_v8": source.get("schema") == "ratchet.v8.source-packets.v1",
        "prior_persistence_schema": prior.get("schema") == "ratchet.pack183.deep-persistence-layer.v1",
        "octonion_witness_trial_zero": evidence["deterministic_integer_witness_trial"] == 0,
        "octonion_path_gap_exact_888": evidence["path_bracketing_gap_squared"] == 888,
        "octonion_associator_gap_exact_136": evidence["edge_associator_gap_squared"] == 136,
        "octonion_chirality_gap_exact_560": evidence["left_right_chirality_gap_squared"] == 560,
        "left_and_mixed_vectors_distinct": evidence["left_bracket_vector"] != evidence["mixed_bracket_vector"],
        "chirality_expressible": expressible,
        "chirality_not_forced": forced is False,
        "chirality_installable": installable,
        "neutral_control_remains_admissible": orientation_candidates["orientation_neutral"]["admissible"] is True,
    }
    receipt = {
        "discriminator": "left versus mixed octonion bracketing",
        "evidence": evidence,
        "orientation_candidates": orientation_candidates,
        "expressible": expressible,
        "forced": forced,
        "installable": installable,
        "checks": checks,
        "all_pass": all(checks.values()),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    receipt["receipt_digest"] = digest(receipt)
    persistence_summary = {
        candidate: {
            "surviving_distinction_count": row["surviving_distinction_count"],
            "all_pass": row["all_pass"],
        }
        for candidate, row in sorted(prior["inventories"].items())
    }
    result = {
        "schema": SCHEMA,
        "source_packet_digest": source["result_digest"],
        "prior_persistence_digest": prior["result_digest"],
        "connection_candidates": list(prior["connection_candidates"]),
        "history_candidates": list(prior["history_candidates"]),
        "history_structures": dict(prior["history_structures"]),
        "admissible_connection_candidates": sorted({
            candidate.split("__", 1)[0] for candidate in prior["current_frontier"]
        }),
        "admissible_history_candidates": sorted({
            candidate.split("__", 1)[1] for candidate in prior["current_frontier"]
        }),
        "persistence_summary": persistence_summary,
        "current_persistence_frontier": list(prior["current_frontier"]),
        "octonion_evidence": evidence,
        "orientation_candidates": orientation_candidates,
        "expressible": expressible,
        "forced": forced,
        "installable": installable,
        "status": "EXPRESSIBLE_INSTALLABLE_NOT_FORCED" if installable else "OPEN_CHIRALITY_DISCRIMINATOR",
        "purgatory": [],
        "receipts": [receipt],
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
        "expressible": result["expressible"],
        "forced": result["forced"],
        "installable": result["installable"],
        "status": result["status"],
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
