#!/usr/bin/env python3
"""Redundant chirality discriminator for the v8 deep manifold lane."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from common import digest, write_json

INPUTS = Path(__file__).resolve().parents[1] / "inputs"
sys.path.insert(0, str(INPUTS))

from finite_algebra import octonion_network_report  # noqa: E402


def bracketing_packet(source: dict[str, Any]) -> dict[str, Any]:
    return next(packet for packet in source["base_packets"] if packet["packet_id"] == "octonion_bracketing_relation")


def run(source: dict[str, Any], persistence: dict[str, Any]) -> dict[str, Any]:
    report = octonion_network_report()
    packet = bracketing_packet(source)
    bracketing_values = {word[0] for word in packet["accepted_words"]}
    expressible = (
        report["path_bracketing_gap_squared"] > 0
        and report["left_right_chirality_gap_squared"] > 0
        and report["all_pass"] is True
    )
    forced = len(bracketing_values) == 1
    installable = expressible and not forced
    candidates = {
        "orientation_erased": {
            "candidate_id": "orientation_erased",
            "orientation_distinction_installed": False,
            "admissible": True,
            "forced": False,
        },
        "orientation_left_installed": {
            "candidate_id": "orientation_left_installed",
            "orientation_distinction_installed": True,
            "admissible": installable,
            "forced": False,
        },
        "orientation_right_installed": {
            "candidate_id": "orientation_right_installed",
            "orientation_distinction_installed": True,
            "admissible": installable,
            "forced": False,
        },
    }
    receipt = {
        "step": 0,
        "reason": "test left-vs-mixed octonion bracketing as an installed-not-forced discriminator",
        "expressible": expressible,
        "forced": forced,
        "installable": installable,
        "bracketing_values_seen": sorted(bracketing_values),
        "witness": {
            "deterministic_integer_witness_trial": report["deterministic_integer_witness_trial"],
            "path_bracketing_gap_squared": report["path_bracketing_gap_squared"],
            "left_right_chirality_gap_squared": report["left_right_chirality_gap_squared"],
        },
        "global_mss_claimed": False,
        "terminal_state": False,
    }
    receipt["receipt_digest"] = digest(receipt)
    checks = {
        "source_packet_count_pinned_9": len(source.get("base_packets", [])) == 9,
        "persistence_all_pass": persistence.get("all_pass") is True,
        "octonion_report_passes": report.get("all_pass") is True,
        "chirality_expressible": expressible,
        "chirality_not_forced": not forced,
        "chirality_merely_installable": installable,
        "orientation_not_forced_into_frontier": candidates["orientation_erased"]["admissible"] is True,
        "no_promotion": True,
    }
    result = {
        "schema": "ratchet.pack183.deep.chirality-alt.v1",
        "source_packet_digest": source["result_digest"],
        "persistence_digest": persistence["result_digest"],
        "candidate_evaluations": candidates,
        "status": {
            "expressible": expressible,
            "forced": forced,
            "installable": installable,
            "classification": "merely_installable" if installable else "not_installable",
        },
        "octonion_witness": receipt["witness"],
        "receipts": [receipt],
        "checks": checks,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "global_mss_claimed": False,
        "terminal_state": False,
        "claim_ceiling": "finite octonion bracketing discriminator only; orientation is not forced",
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
    persistence = json.loads(args.prior.read_text(encoding="utf-8"))
    result = run(source, persistence)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "chirality_status": result["status"],
        "witness_trial": result["octonion_witness"]["deterministic_integer_witness_trial"],
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
