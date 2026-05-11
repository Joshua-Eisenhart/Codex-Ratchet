#!/usr/bin/env python3
"""Bounded graveyard probe for quantum metric nonuniqueness.

This is not an assembly or QIT promotion surface. It checks a narrow claim:
finite qubit state pairs can change nearest-neighbor/ranking structure when
the metric family changes, so metric choice remains a boundary pressure surface
until a later coupling proves which metric is load-bearing.
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
    "Finite qubit metric-choice graveyard: Bures, trace, Hilbert-Schmidt, and "
    "Bloch-angle readouts are compared on the same bounded state pairs. This "
    "records nonuniqueness pressure only; it does not admit a geometry, axis, "
    "GStack, QIT, nonclassical, or assembly claim."
)

LEGO_IDS = ["quantum_metric_nonuniqueness", "bures_geometry", "geomstats_shell_metrics"]
PRIMARY_LEGO_IDS = ["quantum_metric_nonuniqueness"]

CLAIM_CEILING = "metric_choice_graveyard_control_only"
NEXT_LEGO_TARGET = "none"
PROMOTION_CONDITION = "requires a separate admitted metric-choice coupling receipt"
BLOCKED_UNTIL = "metric choice has fixed-carrier, fixed-operator coupling evidence"
DEMOTION_CONDITION = "demote if metrics induce identical rankings on the test family"
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
        "reason": "constructs finite qubit density matrices and metric readouts",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "writes canonical result receipt",
    },
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "json": "supportive"}

RESULT_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
OUT_PATH = RESULT_DIR / "quantum_metric_nonuniqueness_graveyard_results.json"


def rho_from_bloch(vec: np.ndarray) -> np.ndarray:
    x, y, z = vec
    return 0.5 * np.array(
        [
            [1.0 + z, x - 1j * y],
            [x + 1j * y, 1.0 - z],
        ],
        dtype=complex,
    )


def trace_distance(a: np.ndarray, b: np.ndarray) -> float:
    eigs = np.linalg.eigvalsh(a - b)
    return float(0.5 * np.sum(np.abs(eigs)))


def hilbert_schmidt(a: np.ndarray, b: np.ndarray) -> float:
    diff = a - b
    return float(np.sqrt(np.real(np.trace(diff.conj().T @ diff))))


def fidelity_qubit(a: np.ndarray, b: np.ndarray) -> float:
    det_a = float(np.real(np.linalg.det(a)))
    det_b = float(np.real(np.linalg.det(b)))
    root = np.real(np.trace(a @ b)) + 2.0 * math.sqrt(max(det_a * det_b, 0.0))
    return float(min(1.0, max(0.0, root)))


def bures_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(math.sqrt(max(0.0, 2.0 - 2.0 * math.sqrt(fidelity_qubit(a, b)))))


def bloch_angle(a_vec: np.ndarray, b_vec: np.ndarray) -> float:
    na = float(np.linalg.norm(a_vec))
    nb = float(np.linalg.norm(b_vec))
    if na == 0.0 or nb == 0.0:
        return 0.0
    cos = float(np.dot(a_vec, b_vec) / (na * nb))
    return float(math.acos(min(1.0, max(-1.0, cos))))


def rank_signature(rows: list[dict], metric: str) -> list[str]:
    return [row["pair"] for row in sorted(rows, key=lambda item: (item[metric], item["pair"]))]


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    states = {
        "pure_z": np.array([0.0, 0.0, 1.0]),
        "pure_x": np.array([1.0, 0.0, 0.0]),
        "mixed_z_05": np.array([0.0, 0.0, 0.5]),
        "mixed_x_05": np.array([0.5, 0.0, 0.0]),
        "mixed_diag": np.array([0.35, 0.0, 0.35]),
        "center": np.array([0.0, 0.0, 0.0]),
    }
    rhos = {name: rho_from_bloch(vec) for name, vec in states.items()}

    rows = []
    names = list(states)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            a = rhos[left]
            b = rhos[right]
            av = states[left]
            bv = states[right]
            rows.append(
                {
                    "pair": f"{left}::{right}",
                    "trace": trace_distance(a, b),
                    "hilbert_schmidt": hilbert_schmidt(a, b),
                    "bures": bures_distance(a, b),
                    "bloch_angle": bloch_angle(av, bv),
                }
            )

    signatures = {
        metric: rank_signature(rows, metric)
        for metric in ["trace", "hilbert_schmidt", "bures", "bloch_angle"]
    }
    distinct_signature_count = len({tuple(sig) for sig in signatures.values()})

    same_ray_pairs = [row for row in rows if row["pair"] in {"pure_z::mixed_z_05", "pure_x::mixed_x_05"}]
    identical_zero = {
        metric: metric_fn(rhos["pure_z"], rhos["pure_z"]) if metric != "bloch_angle" else bloch_angle(states["pure_z"], states["pure_z"])
        for metric, metric_fn in {
            "trace": trace_distance,
            "hilbert_schmidt": hilbert_schmidt,
            "bures": bures_distance,
            "bloch_angle": bloch_angle,
        }.items()
    }

    positive = {
        "metric_rankings_are_not_unique": {
            "distinct_signature_count": distinct_signature_count,
            "pass": distinct_signature_count >= 2,
        },
        "bures_and_trace_differ_somewhere": {
            "signature_equal": signatures["bures"] == signatures["trace"],
            "pass": signatures["bures"] != signatures["trace"],
        },
    }
    negative = {
        "identical_state_zero_distance": {
            "values": identical_zero,
            "pass": all(abs(value) < 1e-10 for value in identical_zero.values()),
        },
        "same_ray_pairs_are_not_spurious_zero": {
            "rows": same_ray_pairs,
            "pass": all(row["trace"] > 0.0 and row["bures"] > 0.0 for row in same_ray_pairs),
        },
    }
    boundary = {
        "finite_qubit_family_only": {"state_count": len(states), "pair_count": len(rows), "pass": True},
        "no_assembly_or_metric_admission": {"pass": True},
    }

    all_pass = all(item["pass"] for section in [positive, negative, boundary] for item in section.values())
    result = {
        "name": "quantum_metric_nonuniqueness_graveyard",
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
        "states": {name: vec.tolist() for name, vec in states.items()},
        "pair_rows": rows,
        "rank_signatures": signatures,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "distinct_metric_rank_signature_count": distinct_signature_count,
            "recommendation": "keep_blocked_as_metric_choice_graveyard",
        },
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(OUT_PATH)
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
