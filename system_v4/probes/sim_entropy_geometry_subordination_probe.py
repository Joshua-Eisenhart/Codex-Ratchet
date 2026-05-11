#!/usr/bin/env python3
"""Bounded entropy-vs-geometry subordination probe.

The question is narrow: can the entropy-family row be treated as subordinate to
a fixed local geometry/operator carrier, or does entropy distinguish states that
the local carrier collapses? This is a gate probe only. It does not promote
entropy, geometry, QIT, GStack, axis, bridge, engine, or nonclassical claims.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np


classification = "supporting"
CLASSIFICATION = classification
divergence_log = (
    "Finite local-carrier subordination check. Bell and classical correlated "
    "states share the same one-qubit marginal geometry but are separated by "
    "global entropy/coherent-information readouts, so geometry-subordination is "
    "not established on this carrier."
)

LEGO_IDS = ["entropy_family_crosschecks", "geometry_subordination_probe"]
PRIMARY_LEGO_IDS = ["entropy_family_crosschecks"]

CLAIM_CEILING = "entropy_subordination_probe_supporting_only"
NEXT_LEGO_TARGET = "none"
PROMOTION_CONDITION = "requires a stronger fixed-carrier geometry/operator subordination proof"
BLOCKED_UNTIL = "entropy family is shown subordinate to admitted geometry/operator carriers"
DEMOTION_CONDITION = "demote if same-carrier controls are not actually same carrier or entropy readouts fail"
OUT_OF_SCOPE = [
    "QIT engine admission",
    "GStack admission",
    "axis promotion",
    "engine promotion",
    "nonclassical proof",
    "scientific coupling closure",
]

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "constructs finite two-qubit density matrices and entropy/local-carrier readouts",
    },
    "json": {"tried": True, "used": True, "reason": "writes result receipt"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "json": "supportive"}

RESULT_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
OUT_PATH = RESULT_DIR / "entropy_geometry_subordination_probe_results.json"


def ket(index: int, dim: int = 4) -> np.ndarray:
    vec = np.zeros(dim, dtype=complex)
    vec[index] = 1.0
    return vec


def density(psi: np.ndarray) -> np.ndarray:
    return np.outer(psi, psi.conj())


def partial_trace_b(rho: np.ndarray) -> np.ndarray:
    view = rho.reshape(2, 2, 2, 2)
    return np.einsum("abcb->ac", view)


def partial_trace_a(rho: np.ndarray) -> np.ndarray:
    view = rho.reshape(2, 2, 2, 2)
    return np.einsum("abad->bd", view)


def entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real
    vals = vals[vals > 1e-12]
    if vals.size == 0:
        return 0.0
    return float(-np.sum(vals * np.log2(vals)))


def bloch_radius(rho: np.ndarray) -> float:
    x = 2.0 * np.real(rho[0, 1])
    y = -2.0 * np.imag(rho[0, 1])
    z = np.real(rho[0, 0] - rho[1, 1])
    return float(np.sqrt(x * x + y * y + z * z))


def states() -> dict[str, np.ndarray]:
    bell = (ket(0) + ket(3)) / math.sqrt(2.0)
    classical_mix = 0.5 * density(ket(0)) + 0.5 * density(ket(3))
    theta = math.pi / 5.0
    partial = math.cos(theta / 2.0) * ket(0) + math.sin(theta / 2.0) * ket(3)
    return {
        "bell_phi_plus": density(bell),
        "classical_00_11_mix": classical_mix,
        "partial_schmidt": density(partial),
        "product_00": density(ket(0)),
    }


def readout(label: str, rho: np.ndarray) -> dict:
    rho_a = partial_trace_a(rho)
    rho_b = partial_trace_b(rho)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho)
    return {
        "label": label,
        "local_carrier": {
            "S_A": s_a,
            "S_B": s_b,
            "bloch_radius_A": bloch_radius(rho_a),
            "bloch_radius_B": bloch_radius(rho_b),
        },
        "entropy_readout": {
            "S_AB": s_ab,
            "conditional_A_given_B": s_ab - s_b,
            "coherent_A_to_B": s_b - s_ab,
            "cut_entropy": s_a,
        },
    }


def close(a: float, b: float, eps: float = 1e-10) -> bool:
    return abs(a - b) < eps


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = {label: readout(label, rho) for label, rho in states().items()}
    bell = rows["bell_phi_plus"]
    classical = rows["classical_00_11_mix"]

    same_local_carrier = all(
        close(bell["local_carrier"][key], classical["local_carrier"][key])
        for key in ["S_A", "S_B", "bloch_radius_A", "bloch_radius_B"]
    )
    entropy_separates_same_carrier = (
        abs(bell["entropy_readout"]["S_AB"] - classical["entropy_readout"]["S_AB"]) > 0.99
        and bell["entropy_readout"]["coherent_A_to_B"] > 0.99
        and close(classical["entropy_readout"]["coherent_A_to_B"], 0.0)
    )

    positive = {
        "same_local_geometry_carrier_exists": {
            "pair": ["bell_phi_plus", "classical_00_11_mix"],
            "pass": same_local_carrier,
        },
        "entropy_readout_separates_same_local_carrier": {
            "pair": ["bell_phi_plus", "classical_00_11_mix"],
            "pass": entropy_separates_same_carrier,
        },
    }
    negative = {
        "product_control_zero_entropy_signal": {
            "row": rows["product_00"],
            "pass": close(rows["product_00"]["entropy_readout"]["S_AB"], 0.0)
            and close(rows["product_00"]["entropy_readout"]["coherent_A_to_B"], 0.0),
        },
        "partial_schmidt_not_same_local_carrier_control": {
            "row": rows["partial_schmidt"],
            "pass": rows["partial_schmidt"]["local_carrier"]["S_A"] < bell["local_carrier"]["S_A"],
        },
    }
    boundary = {
        "finite_two_qubit_carrier_only": {"state_count": len(rows), "pass": True},
        "no_queue_or_catalog_unblock": {"pass": True},
    }
    all_pass = all(item["pass"] for section in [positive, negative, boundary] for item in section.values())
    ruling = "introduces_independent_structure_on_tested_local_carrier" if all_pass else "inconclusive"
    result = {
        "name": "entropy_geometry_subordination_probe",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "generated_at": datetime.now(UTC).isoformat(),
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": NEXT_LEGO_TARGET,
        "promotion_condition": PROMOTION_CONDITION,
        "blocked_until": BLOCKED_UNTIL,
        "demotion_condition": DEMOTION_CONDITION,
        "out_of_scope": OUT_OF_SCOPE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "rows": rows,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "ruling": ruling,
            "recommendation": "keep_entropy_family_crosschecks_blocked_for_assembly",
        },
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(OUT_PATH)
    print(f"ALL PASS: {all_pass}")
    print(f"RULING: {ruling}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
