#!/usr/bin/env python3
"""Shared finite fixture for sequential_inheritance_not_cycle_v0."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any


SIM_ID = "sequential_inheritance_not_cycle_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = PACKET / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
LN2 = math.log(2.0)

BASE_ORBITS = [
    {"orbit_id": "z_plus", "terminal_family": "axis_z", "terminal_bit": 0},
    {"orbit_id": "z_minus", "terminal_family": "axis_z", "terminal_bit": 1},
    {"orbit_id": "x_plus", "terminal_family": "axis_x", "terminal_bit": 0},
    {"orbit_id": "x_minus", "terminal_family": "axis_x", "terminal_bit": 1},
    {"orbit_id": "y_plus", "terminal_family": "axis_y", "terminal_bit": 0},
    {"orbit_id": "y_minus", "terminal_family": "axis_y", "terminal_bit": 1},
]

PHASES = [
    {"syndrome": 0, "global_phase": "1", "phase_quarter": 0},
    {"syndrome": 1, "global_phase": "i", "phase_quarter": 1},
    {"syndrome": 2, "global_phase": "-1", "phase_quarter": 2},
    {"syndrome": 3, "global_phase": "-i", "phase_quarter": 3},
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def entropy_from_counts(counts: list[int]) -> dict[str, Any]:
    total = sum(counts)
    probs = [Fraction(count, total) for count in counts if count]
    entropy_nats = -sum(float(p) * math.log(float(p)) for p in probs)
    return {
        "entropy_type": "finite_counting_entropy_nats",
        "log_base": "e",
        "counts": counts,
        "probabilities_exact": [f"{p.numerator}/{p.denominator}" for p in probs],
        "entropy_nats": entropy_nats,
        "entropy_log2_coefficient": int(round(entropy_nats / LN2)),
        "code_path_id": "distribution_counts_to_shannon_entropy",
    }


def build_parent_terminal_table() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for orbit_index, orbit in enumerate(BASE_ORBITS):
        for phase in PHASES:
            syndrome = int(phase["syndrome"])
            parent_terminal_label = (
                f"{orbit['terminal_family']}::bit_{orbit['terminal_bit']}::z4_{syndrome}"
            )
            rows.append(
                {
                    "parent_representative_id": f"{orbit['orbit_id']}::phase_{syndrome}",
                    "orbit_id": orbit["orbit_id"],
                    "orbit_index": orbit_index,
                    "quotient_output": f"orbit::{orbit['orbit_id']}",
                    "terminal_family": orbit["terminal_family"],
                    "terminal_bit": orbit["terminal_bit"],
                    "terminal_structure_id": parent_terminal_label,
                    "syndrome": syndrome,
                    "syndrome_bits": format(syndrome, "02b"),
                    "global_phase": phase["global_phase"],
                    "phase_quarter": phase["phase_quarter"],
                    "record_object_standard": "packet_local_z4_syndrome_distribution",
                    "generator": "alpha += pi/2",
                    "orbit_order": len(PHASES),
                }
            )
    return rows


def record_object(parent_rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(int(row["syndrome"]) for row in parent_rows)
    orbit_support: dict[str, list[int]] = defaultdict(list)
    for row in parent_rows:
        orbit_support[str(row["orbit_id"])].append(int(row["syndrome"]))
    return {
        "standard": "z4_syndrome_record_v0_packet_local_convention",
        "semantic_role": "record_of_parent_terminal_structure",
        "record_is_not_loss_assignment": True,
        "syndrome_distribution": dict(sorted(counts.items())),
        "syndrome_entropy": entropy_from_counts([counts[k] for k in sorted(counts)]),
        "orbit_syndrome_support": {k: sorted(v) for k, v in sorted(orbit_support.items())},
        "source_convention_commit": "bd7a54080",
    }


def assigned_syndrome(row: dict[str, Any], regime: str) -> int:
    parent = int(row["syndrome"])
    orbit_index = int(row["orbit_index"])
    if regime == "inheritance":
        return parent
    if regime == "cycle_null":
        return (parent + 1) % 4
    if regime == "random_null":
        return (3 * orbit_index + 1) % 4
    raise ValueError(f"unknown regime: {regime}")


def daughter_rows(parent_rows: list[dict[str, Any]], regime: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for parent in parent_rows:
        inherited_syndrome = assigned_syndrome(parent, regime)
        daughter_terminal_id = (
            f"{parent['terminal_family']}::bit_{parent['terminal_bit']}::z4_{inherited_syndrome}"
        )
        matches_parent = daughter_terminal_id == parent["terminal_structure_id"]
        rows.append(
            {
                "regime": regime,
                "parent_representative_id": parent["parent_representative_id"],
                "daughter_initial_constraint": {
                    "orbit_id": parent["orbit_id"],
                    "terminal_family": parent["terminal_family"],
                    "terminal_bit": parent["terminal_bit"],
                    "record_syndrome": inherited_syndrome,
                    "initializer_source": regime,
                },
                "parent_terminal_structure_id": parent["terminal_structure_id"],
                "daughter_terminal_structure_id": daughter_terminal_id,
                "parent_syndrome": int(parent["syndrome"]),
                "daughter_syndrome": inherited_syndrome,
                "record_alignment": int(inherited_syndrome == int(parent["syndrome"])),
                "terminal_structure_match": matches_parent,
                "stability_score": 1.0 if matches_parent else 0.0,
                "structure_row_hash": stable_hash(
                    {
                        "family": parent["terminal_family"],
                        "bit": parent["terminal_bit"],
                        "parent_z4": int(parent["syndrome"]),
                        "daughter_z4": inherited_syndrome,
                    }
                ),
            }
        )
    return rows


def regime_summary(parent_rows: list[dict[str, Any]], regime: str) -> dict[str, Any]:
    rows = daughter_rows(parent_rows, regime)
    syndrome_counts = Counter(row["daughter_syndrome"] for row in rows)
    match_count = sum(1 for row in rows if row["terminal_structure_match"])
    unique_structures = len({row["daughter_terminal_structure_id"] for row in rows})
    stability_sum = sum(float(row["stability_score"]) for row in rows)
    return {
        "regime": regime,
        "row_count": len(rows),
        "daughter_rows": rows,
        "record_alignment_count": sum(row["record_alignment"] for row in rows),
        "terminal_structure_match_count": match_count,
        "terminal_structure_mismatch_count": len(rows) - match_count,
        "mean_stability_score": stability_sum / len(rows),
        "stability_score_sum": stability_sum,
        "unique_daughter_terminal_structures": unique_structures,
        "daughter_syndrome_distribution": dict(sorted(syndrome_counts.items())),
        "daughter_record_entropy": entropy_from_counts([syndrome_counts[k] for k in sorted(syndrome_counts)]),
        "structure_signature_hash": stable_hash(
            [row["daughter_terminal_structure_id"] for row in rows]
        ),
    }


def build_fixture() -> dict[str, Any]:
    parent_rows = build_parent_terminal_table()
    regimes = {
        name: regime_summary(parent_rows, name)
        for name in ["inheritance", "cycle_null", "random_null"]
    }
    signatures = {name: row["structure_signature_hash"] for name, row in regimes.items()}
    return {
        "parent_terminal_table": parent_rows,
        "record_object": record_object(parent_rows),
        "regimes": regimes,
        "discriminator": {
            "all_regime_signatures_distinct": len(set(signatures.values())) == 3,
            "inheritance_gt_cycle_stability": regimes["inheritance"]["mean_stability_score"]
            > regimes["cycle_null"]["mean_stability_score"],
            "inheritance_gt_random_stability": regimes["inheritance"]["mean_stability_score"]
            > regimes["random_null"]["mean_stability_score"],
            "cycle_null_distinct_from_random_null": signatures["cycle_null"] != signatures["random_null"],
            "reported_if_no_teeth": not (
                len(set(signatures.values())) == 3
                and regimes["inheritance"]["mean_stability_score"]
                > regimes["cycle_null"]["mean_stability_score"]
                and regimes["inheritance"]["mean_stability_score"]
                > regimes["random_null"]["mean_stability_score"]
            ),
        },
        "regime_signature_hashes": signatures,
    }


def expected_all_pass(fixture: dict[str, Any]) -> bool:
    parent_rows = fixture["parent_terminal_table"]
    regimes = fixture["regimes"]
    discriminator = fixture["discriminator"]
    return all(
        [
            len(parent_rows) == 24,
            fixture["record_object"]["syndrome_entropy"]["entropy_log2_coefficient"] == 2,
            regimes["inheritance"]["terminal_structure_match_count"] == 24,
            regimes["cycle_null"]["terminal_structure_match_count"] == 0,
            regimes["random_null"]["terminal_structure_match_count"] == 6,
            discriminator["all_regime_signatures_distinct"],
            discriminator["inheritance_gt_cycle_stability"],
            discriminator["inheritance_gt_random_stability"],
            discriminator["cycle_null_distinct_from_random_null"],
            discriminator["reported_if_no_teeth"] is False,
        ]
    )
