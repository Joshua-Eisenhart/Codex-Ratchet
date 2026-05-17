"""Small helpers for consuming the Axis0 anti-collapse guard receipt.

These helpers keep downstream scouts from silently treating raw Axis0 router
vectors as admitted world-model or LiRPA features after the multicarrier guard
has blocked specific candidates.
"""

from __future__ import annotations

from typing import Any

import numpy as np


AXIS0_GUARD_RESULT_NAME = "axis0_plural_candidate_multicarrier_drive_controls_probe_results.json"
AXIS0_CANDIDATE_NAMES = [
    "fep_gradient_polarity",
    "path_entropy",
    "correlation_diversity_derivative",
    "holographic_boundary_interior_reconstruction",
    "retrocausal_many_futures_policy_scoring",
]


def axis0_guard_signal(guard_receipt: dict[str, Any], *, feature_prefix: str = "axis0_") -> dict[str, Any]:
    outputs = guard_receipt.get("axis0_outputs_or_blockers") or {}
    positive = guard_receipt.get("positive") or {}
    correlation_report = (
        positive.get("control_family_correlation_report_is_recorded", {})
        .get("control_family_correlation_report", {})
    )
    admitted = [
        name
        for name in outputs.get("admitted_candidate_names", [])
        if name in AXIS0_CANDIDATE_NAMES
    ]
    blocked = [
        name
        for name in outputs.get("blocked_candidate_names", [])
        if name in AXIS0_CANDIDATE_NAMES
    ]
    classified = set(admitted) | set(blocked)
    unclassified = [name for name in AXIS0_CANDIDATE_NAMES if name not in classified]
    candidate_status = outputs.get("candidate_status", {})
    return {
        "pass": bool(
            guard_receipt.get("all_pass") is True
            and outputs.get("axis0_ready") is True
            and len(admitted) >= 3
            and not unclassified
        ),
        "guard_result": AXIS0_GUARD_RESULT_NAME,
        "admitted_candidate_names": admitted,
        "blocked_candidate_names": blocked,
        "unclassified_candidate_names": unclassified,
        "candidate_status": candidate_status,
        "blocked_candidate_status": {name: candidate_status.get(name, {}) for name in blocked},
        "adapter_active_axis0_feature_names": [f"{feature_prefix}{name}" for name in admitted],
        "blocked_axis0_feature_names_excluded": [f"{feature_prefix}{name}" for name in blocked],
        "scalar_weighted_drive_blocker": outputs.get("scalar_weighted_drive_blocker", {}),
        "control_family_degeneracy_blockers": correlation_report.get("control_family_degeneracy_blockers", {}),
        "guard_claim_ceiling": guard_receipt.get("claim_ceiling", ""),
    }


def guarded_router_vectors(
    router_receipt: dict[str, Any],
    guard: dict[str, Any],
    *,
    as_numpy: bool = False,
) -> dict[str, Any]:
    outputs = router_receipt.get("axis0_outputs_or_blockers") or {}
    vectors: dict[str, Any] = {}
    for name in guard.get("admitted_candidate_names", []):
        arr = np.asarray(outputs.get(name, {}).get("values", []), dtype=float)
        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
        scale = float(np.max(np.abs(arr))) if arr.size else 0.0
        if scale > 0.0:
            arr = arr / scale
        vectors[name] = arr if as_numpy else [float(x) for x in arr]
    return vectors


def filter_subdense_axis0_signature(axis0: dict[str, Any], guard: dict[str, Any]) -> dict[str, Any]:
    admitted = list(guard.get("admitted_candidate_names", []))
    old_vectors = axis0.get("candidate_vectors", {}) or {}
    vectors = {name: old_vectors.get(name, []) for name in admitted}
    filtered = dict(axis0)
    filtered["ready"] = bool(axis0.get("ready") and guard.get("pass") and all(vectors.values()))
    filtered["candidate_names"] = admitted
    filtered["candidate_vectors"] = vectors
    filtered["blocked_candidate_names_excluded"] = list(guard.get("blocked_candidate_names", []))
    filtered["scalar_weighted_drive_blocker"] = guard.get("scalar_weighted_drive_blocker", {})
    filtered["control_family_degeneracy_blockers"] = guard.get("control_family_degeneracy_blockers", {})
    return filtered
