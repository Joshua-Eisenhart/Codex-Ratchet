#!/usr/bin/env python3
"""
Canonical Axis 0 Xi-history law fingerprints.

These helpers normalize the current Xi strict-bakeoff law across the
strict-bakeoff result, the carrier-selection packet, the pre-entropy packet,
and the entropy-readout packet so stack-level audits can compare one shared
semantic surface instead of re-encoding the law by hand in each validator.
"""

from __future__ import annotations


EARLY_WIDTH_LABELS = ("0_3", "0_7", "0_11", "0_15")
PREFIX_DROP_LABELS = ("0_15", "1_15", "2_15", "4_15", "8_15")
PLACEMENT_LABELS = ("0_15", "8_23", "16_31")


def _normalize_counts(mapping: dict[str, object], labels: tuple[str, ...]) -> dict[str, int]:
    return {label: int(mapping.get(label, 0)) for label in labels}


def _law_fingerprint_from_summary(law_summary: dict[str, object]) -> dict[str, object]:
    late_anchor = dict(law_summary["late_anchor_equivalence"])
    anchor_profile = dict(law_summary["anchor_and_width_profile"])
    counts = dict(law_summary["counts"])
    return {
        "law_name": str(law_summary["law_name"]),
        "owner_read": str(law_summary["owner_read"]),
        "placement_label": "8_23",
        "equivalent_anchor_labels": ["16_31", "8_15"],
        "canonical_prefix_drop": "8_15",
        "canonical_early_width": "0_7",
        "comparison_width": "0_3",
        "total_rows": int(counts["total_rows"]),
        "off_clifford_rows": int(counts["off_clifford_rows"]),
        "clifford_rows": int(counts["clifford_rows"]),
        "placement_8_23_equals_16_31": bool(late_anchor["placement_8_23_equals_16_31"]),
        "placement_8_23_equals_prefix_8_15_on_mi": bool(
            late_anchor["placement_8_23_equals_prefix_8_15_on_mi"]
        ),
        "placement_8_23_equals_prefix_8_15_on_ic": bool(
            late_anchor["placement_8_23_equals_prefix_8_15_on_ic"]
        ),
        "placement_8_23_equals_prefix_8_15_on_signed_cut": bool(
            late_anchor["placement_8_23_equals_prefix_8_15_on_signed_cut"]
        ),
        "best_prefix_drop_by_ic_is_8_15": bool(
            anchor_profile["best_prefix_drop_by_ic_is_8_15"]
        ),
        "best_early_width_by_ic_is_0_7_majority": bool(
            anchor_profile["best_early_width_by_ic_is_0_7_majority"]
        ),
        "late_anchor_beats_0_3_globally_on_ic": bool(
            anchor_profile["late_anchor_beats_0_3_globally_on_ic"]
        ),
        "front_half_signed_cut_preference_all_seats": bool(
            anchor_profile["front_half_signed_cut_preference_all_seats"]
        ),
        "clifford_mi_0_7_vs_0_15_is_tied": bool(
            anchor_profile["clifford_mi_0_7_vs_0_15_is_tied"]
        ),
        "placement_8_23_beats_0_3_on_ic_count": int(
            counts["placement_8_23_beats_0_3_on_ic_count"]
        ),
        "placement_8_23_beats_0_3_on_ic_off_clifford_count": int(
            counts["placement_8_23_beats_0_3_on_ic_off_clifford_count"]
        ),
        "short_width_0_3_beats_8_23_on_ic_clifford_count": int(
            counts["short_width_0_3_beats_8_23_on_ic_clifford_count"]
        ),
        "best_early_width_by_ic_counts": _normalize_counts(
            dict(counts["best_early_width_by_ic_counts"]),
            EARLY_WIDTH_LABELS,
        ),
        "best_prefix_drop_by_ic_counts": _normalize_counts(
            dict(counts["best_prefix_drop_by_ic_counts"]),
            PREFIX_DROP_LABELS,
        ),
    }


def strict_law_fingerprint(strict_result: dict[str, object]) -> dict[str, object]:
    return _law_fingerprint_from_summary(
        dict(strict_result["verdict"]["xi_hist_signed_law_summary"])
    )


def pre_entropy_law_fingerprint(pre_entropy_validation: dict[str, object]) -> dict[str, object]:
    gate_map = {item["name"]: item for item in pre_entropy_validation["gates"]}
    return _law_fingerprint_from_summary(
        dict(gate_map["P14_xi_hist_signed_law_is_explicit_in_strict_bakeoff"]["detail"])
    )


def entropy_law_fingerprint(entropy_validation: dict[str, object]) -> dict[str, object]:
    gate_map = {item["name"]: item for item in entropy_validation["gates"]}
    e12_detail = dict(gate_map["E12_xi_hist_law_summary_binds_pre_entropy_to_readout"]["detail"])
    return _law_fingerprint_from_summary(dict(e12_detail["p14_detail"]))


def carrier_law_fingerprint(carrier_validation: dict[str, object]) -> dict[str, object]:
    gate_map = {item["name"]: item for item in carrier_validation["gates"]}
    detail = dict(
        gate_map["C5_strict_bakeoff_confirms_structured_history_without_shell_shortcut"]["detail"]
    )
    window_counts = _normalize_counts(
        dict(detail["best_window_by_mi_counts"]),
        EARLY_WIDTH_LABELS,
    )
    placement_counts = _normalize_counts(
        dict(detail["best_placement_by_mi_counts"]),
        PLACEMENT_LABELS,
    )
    prefix_counts = _normalize_counts(
        dict(detail["best_prefix_drop_by_mi_counts"]),
        PREFIX_DROP_LABELS,
    )
    total_rows = int(sum(window_counts.values()))
    return {
        "history_nontrivial_while_shell_flat": bool(detail["history_nontrivial_while_shell_flat"]),
        "point_ref_minus_shell_base_std": float(detail["point_ref_minus_shell_base_std"]),
        "total_rows": total_rows,
        "best_window_by_mi_counts": window_counts,
        "best_placement_by_mi_counts": placement_counts,
        "best_prefix_drop_by_mi_counts": prefix_counts,
        "window_0_7_is_global_mi_winner": window_counts["0_7"] == total_rows,
        "placement_8_23_is_global_mi_winner": placement_counts["8_23"] == total_rows,
        "prefix_8_15_is_global_mi_winner": prefix_counts["8_15"] == total_rows,
        "early_window_beats_shifted_count": int(detail["early_window_beats_shifted_count"]),
    }


def carrier_matches_law(
    carrier_fingerprint: dict[str, object],
    law_fingerprint: dict[str, object],
) -> bool:
    total_rows = int(law_fingerprint["total_rows"])
    return bool(
        carrier_fingerprint["history_nontrivial_while_shell_flat"]
        and float(carrier_fingerprint["point_ref_minus_shell_base_std"]) > 0.1
        and int(carrier_fingerprint["total_rows"]) == total_rows
        and carrier_fingerprint["best_window_by_mi_counts"]["0_7"] == total_rows
        and carrier_fingerprint["best_placement_by_mi_counts"]["8_23"] == total_rows
        and carrier_fingerprint["best_prefix_drop_by_mi_counts"]["8_15"] == total_rows
        and int(carrier_fingerprint["early_window_beats_shifted_count"]) == 0
    )


def runner_law_fingerprints_consistent(run_payload: dict[str, object]) -> bool:
    fingerprints = dict(run_payload.get("xi_hist_law_fingerprints", {}))
    if not fingerprints:
        return False
    rendered = [fingerprints[key] for key in sorted(fingerprints)]
    return all(fingerprint == rendered[0] for fingerprint in rendered[1:])
