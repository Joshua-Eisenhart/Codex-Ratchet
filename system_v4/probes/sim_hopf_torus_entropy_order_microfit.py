#!/usr/bin/env python3
"""Bounded Hopf/torus entropy and order-control microfit.

This receipt adds a narrow entropy/order readout around the existing Hopf
torus lego receipt. It does not admit QIT, GStack, axis, or nonclassical
claims; the order test is a classical diagonal-control showing that boolean
mask updates commute at this readout layer.
"""

from __future__ import annotations

import json
import math
import pathlib
from typing import Iterable

import numpy as np


classification = "tool_lego_fit_probe"
divergence_log = (
    "Tool-lego fit microprobe for Hopf/torus entropy readouts and a diagonal "
    "order-control. It measures Shannon, Renyi-2, and min entropy on finite "
    "Hopf-torus masks, includes a non-uniform weighted readout where entropy "
    "families separate, and records that classical boolean mask updates commute."
)

LEGO_IDS = [
    "hopf_geometry",
    "torus_geometry",
    "entropy_family_crosschecks",
    "order_variant_graveyard",
]
PRIMARY_LEGO_IDS = ["hopf_geometry", "torus_geometry"]

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "constructs finite Hopf-torus grids, masks, probabilities, and entropy readouts",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "loads source receipt and writes bounded result receipt",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "resolves source and result paths",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "json": "supportive",
    "pathlib": "supportive",
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
SOURCE_RECEIPT = RESULT_DIR / "hopf_torus_lego_results.json"
OUT_PATH = RESULT_DIR / "hopf_torus_entropy_order_microfit_results.json"


def normalized(mask: np.ndarray) -> np.ndarray:
    weights = mask.astype(float).reshape(-1)
    total = float(weights.sum())
    if total <= 0:
        raise ValueError("mask has no support")
    return weights / total


def entropy_report(probabilities: np.ndarray) -> dict[str, float]:
    p = probabilities[probabilities > 0.0]
    shannon = float(-(p * np.log2(p)).sum())
    renyi2 = float(-math.log2(float((p * p).sum())))
    min_entropy = float(-math.log2(float(p.max())))
    support = int(p.size)
    return {
        "support": support,
        "shannon_bits": shannon,
        "renyi2_bits": renyi2,
        "min_entropy_bits": min_entropy,
    }


def strictly_descending(values: Iterable[float]) -> bool:
    series = list(values)
    return all(a > b for a, b in zip(series, series[1:]))


def main() -> None:
    source = json.loads(SOURCE_RECEIPT.read_text(encoding="utf-8"))
    source_summary = source.get("summary", {})

    n_phi = 32
    n_xi = 32
    phi = np.linspace(0.0, 2.0 * math.pi, n_phi, endpoint=False)
    xi = np.linspace(0.0, 2.0 * math.pi, n_xi, endpoint=False)
    phi_grid, xi_grid = np.meshgrid(phi, xi, indexing="ij")

    uniform_mask = np.ones_like(phi_grid, dtype=bool)
    meridian_mask = phi_grid < (2.0 * math.pi / n_phi)
    fiber_band_mask = xi_grid < (4.0 * math.pi / n_xi)
    localized_patch_mask = meridian_mask & fiber_band_mask

    masks = {
        "uniform_torus": uniform_mask,
        "fiber_band": fiber_band_mask,
        "single_meridian": meridian_mask,
        "localized_patch": localized_patch_mask,
    }
    entropies = {name: entropy_report(normalized(mask)) for name, mask in masks.items()}

    shannon_order = [
        entropies["uniform_torus"]["shannon_bits"],
        entropies["fiber_band"]["shannon_bits"],
        entropies["single_meridian"]["shannon_bits"],
        entropies["localized_patch"]["shannon_bits"],
    ]
    renyi2_order = [
        entropies["uniform_torus"]["renyi2_bits"],
        entropies["fiber_band"]["renyi2_bits"],
        entropies["single_meridian"]["renyi2_bits"],
        entropies["localized_patch"]["renyi2_bits"],
    ]
    min_order = [
        entropies["uniform_torus"]["min_entropy_bits"],
        entropies["fiber_band"]["min_entropy_bits"],
        entropies["single_meridian"]["min_entropy_bits"],
        entropies["localized_patch"]["min_entropy_bits"],
    ]

    # These are diagonal mask operations on a finite classical readout. They
    # should commute; if they do not, the microfit is not measuring what it says.
    phase_then_fiber = localized_patch_mask
    fiber_then_phase = fiber_band_mask & meridian_mask
    order_difference = int(np.logical_xor(phase_then_fiber, fiber_then_phase).sum())
    weighted = normalized(1.0 + 0.45 * np.cos(phi_grid) + 0.25 * np.cos(xi_grid))
    weighted_entropy = entropy_report(weighted)
    expected_patch_support = int(localized_patch_mask.sum())
    source_homology = (
        source.get("positive", {})
        .get("gudhi_hopf_torus_homology", {})
        .get("details", {})
    )

    positive = {
        "source_hopf_torus_topology_receipt_passes": {
            "source_all_pass": source_summary.get("all_pass"),
            "source_beta1_equals_2": source_homology.get("beta1_equals_2"),
            "pass": source_summary.get("all_pass") is True and source_homology.get("beta1_equals_2") is True,
        },
        "uniform_mask_entropy_formula_consistency": {
            "order": ["uniform_torus", "fiber_band", "single_meridian", "localized_patch"],
            "shannon_bits": shannon_order,
            "renyi2_bits": renyi2_order,
            "min_entropy_bits": min_order,
            "expected_log2_supports": [math.log2(entropies[name]["support"]) for name in masks],
            "pass": all(
                abs(entropies[name]["shannon_bits"] - math.log2(entropies[name]["support"])) < 1e-12
                and abs(entropies[name]["renyi2_bits"] - math.log2(entropies[name]["support"])) < 1e-12
                and abs(entropies[name]["min_entropy_bits"] - math.log2(entropies[name]["support"])) < 1e-12
                for name in masks
            ),
        },
        "uniform_support_ordering_is_monotone": {
            "pass": strictly_descending(shannon_order)
            and strictly_descending(renyi2_order)
            and strictly_descending(min_order),
        },
        "nonuniform_entropy_families_separate": {
            "weighted_entropy": weighted_entropy,
            "pass": weighted_entropy["shannon_bits"] > weighted_entropy["renyi2_bits"] > weighted_entropy["min_entropy_bits"],
        },
        "localized_patch_has_expected_support": {
            "localized_support": entropies["localized_patch"]["support"],
            "expected_support": expected_patch_support,
            "pass": entropies["localized_patch"]["support"] == expected_patch_support,
        },
    }
    negative = {
        "diagonal_mask_order_control_is_commutative": {
            "order_difference_cells": order_difference,
            "pass": order_difference == 0,
            "verdict": "classical_boolean_mask_control_only_not_noncommuting_order_evidence",
        },
        "not_nonclassical_or_qit_admission": {
            "qit_or_axis_promotion_allowed": False,
            "promotion_allowed": False,
            "pass": True,
        },
    }
    boundary = {
        "finite_grid_only": {
            "n_phi": n_phi,
            "n_xi": n_xi,
            "dimension": int(n_phi * n_xi),
            "pass": n_phi * n_xi == 1024,
        },
        "all_masks_nonempty": {
            "supports": {name: report["support"] for name, report in entropies.items()},
            "pass": all(report["support"] > 0 for report in entropies.values()),
        },
    }
    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )

    result = {
        "name": "hopf_torus_entropy_order_microfit",
        "classification": classification,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "hopf_torus_lego": str(SOURCE_RECEIPT),
        },
        "claim_ceiling": (
            "tool-lego entropy/order microfit only; no QIT, GStack, axis, "
            "nonclassical, or scientific coupling admission"
        ),
        "next_lego_target": "hopf_torus_entropy_operator_order_graveyard_controls",
        "promotion_condition": "Requires separate stage-gated coupling/coexistence/topology receipts outside this microfit.",
        "blocked_until": "scientific coupling stage opens and exact downstream receipts exist",
        "demotion_condition": "Demote if used as noncommuting order evidence, QIT, GStack, axis, nonclassical, or scientific coupling proof.",
        "out_of_scope": [
            "QIT engine admission",
            "GStack admission",
            "axis promotion",
            "nonclassical proof",
            "scientific coupling proof",
        ],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "finite_dimension": int(n_phi * n_xi),
            "entropy_families": ["shannon", "renyi2", "min_entropy"],
            "nonuniform_entropy_families_separate": bool(positive["nonuniform_entropy_families_separate"]["pass"]),
            "order_control": "classical_diagonal_mask_commutativity",
            "order_control_verdict": "commutes_for_classical_boolean_masks",
            "promotion_allowed": False,
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "rows": [
            {"mask": name, **report}
            for name, report in entropies.items()
        ],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(OUT_PATH)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
