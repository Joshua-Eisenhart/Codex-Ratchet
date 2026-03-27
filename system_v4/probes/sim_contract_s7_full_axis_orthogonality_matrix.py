#!/usr/bin/env python3
"""
SIM 7 — Contract Full Axis Orthogonality Matrix
===============================================
Measurement-only 0..6 axis overlap matrix using displacement channels.

Axis 0 is measured as the South-vs-North entropic-gradient displacement.
Axes 1..6 are measured as channel displacement from identity.

This avoids pretending the current engine satisfies the contract. It
simply measures pairwise overlap in the current probe basis.
"""

from __future__ import annotations

import json
import os
import sys
from itertools import combinations
from datetime import UTC, datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axis_orthogonality_suite import AXES, A0_north, A0_south, build_choi, hs_inner
from proto_ratchet_sim_runner import EvidenceToken


RESULT_NAME = "contract_s7_full_axis_orthogonality_matrix_results.json"
DIMS = [4, 8, 16]


def identity_channel(rho: np.ndarray, d: int) -> np.ndarray:
    return rho


def displacement_channel(base_fn, ref_fn):
    def _channel(rho: np.ndarray, d: int) -> np.ndarray:
        return base_fn(rho, d) - ref_fn(rho, d)
    return _channel


AXES7 = {
    "A0_EntropicGradient": displacement_channel(A0_south, A0_north),
    "A1_Coupling": displacement_channel(AXES["A1_Coupling"], identity_channel),
    "A2_Frame": displacement_channel(AXES["A2_Frame"], identity_channel),
    "A3_Chirality": displacement_channel(AXES["A3_Chirality"], identity_channel),
    "A4_Variance": displacement_channel(AXES["A4_Variance"], identity_channel),
    "A5_Texture": displacement_channel(AXES["A5_Texture"], identity_channel),
    "A6_Precedence": displacement_channel(AXES["A6_Precedence"], identity_channel),
}


def run_probe() -> dict:
    per_dim = {}
    avg_by_pair = {}

    for d in DIMS:
        choi = {name: build_choi(fn, d) for name, fn in AXES7.items()}
        rows = []
        for a, b in combinations(AXES7.keys(), 2):
            overlap = float(abs(hs_inner(choi[a], choi[b])))
            rows.append({"pair": f"{a} x {b}", "overlap": overlap})
            avg_by_pair.setdefault(f"{a} x {b}", []).append(overlap)
        per_dim[f"d={d}"] = rows

    pair_summary = {
        pair: {
            "avg_overlap": float(np.mean(values)),
            "max_overlap": float(np.max(values)),
        }
        for pair, values in avg_by_pair.items()
    }

    threshold = 1e-2
    verdicts = {
        pair: bool(stats["avg_overlap"] < threshold)
        for pair, stats in pair_summary.items()
    }
    verdicts["all_pairs_below_threshold"] = bool(all(verdicts.values()))

    token = EvidenceToken(
        token_id="E_SIM_CONTRACT_S7_FULL_AXIS_MATRIX"
        if verdicts["all_pairs_below_threshold"]
        else "",
        sim_spec_id="S_SIM_CONTRACT_S7_FULL_AXIS_ORTHOGONALITY_V1",
        status="PASS" if verdicts["all_pairs_below_threshold"] else "KILL",
        measured_value=float(max(stats["avg_overlap"] for stats in pair_summary.values())),
        kill_reason=None if verdicts["all_pairs_below_threshold"] else "PAIRWISE_AXIS_OVERLAP_ABOVE_THRESHOLD",
    )

    return {
        "schema": "SIM_EVIDENCE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "sim_name": "contract_s7_full_axis_orthogonality_matrix",
        "status": "current_basis_measurement",
        "threshold": threshold,
        "dimensions": DIMS,
        "pair_summary": pair_summary,
        "per_dimension": per_dim,
        "verdicts": verdicts,
        "evidence_ledger": [token.__dict__],
    }


def main() -> None:
    result = run_probe()
    base = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, RESULT_NAME)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {out_path}")
    print(json.dumps({"all_pairs_below_threshold": result["verdicts"]["all_pairs_below_threshold"]}, indent=2))


if __name__ == "__main__":
    main()
