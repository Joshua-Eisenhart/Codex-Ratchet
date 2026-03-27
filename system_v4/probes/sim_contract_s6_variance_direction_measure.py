#!/usr/bin/env python3
"""
SIM 6 — Contract Variance Direction
===================================
Measurement-only probe for Axis 4.

Contract target from qit_complete_math_reference.py:
  V(rho) = Tr(rho^2)
  Deductive should decrease early.
  Inductive should increase early.

This probe measures the four canonical quadrants directly using the
same operator order as axis3_orthogonality_sim.py.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axis3_orthogonality_sim import C_Fe, C_Fi, C_Te, C_Ti
from orthogonality_sim import build_Fe_ops, build_Fi_filter, build_Te_hamiltonian, build_Ti_ops
from proto_ratchet_sim_runner import EvidenceToken, make_random_density_matrix


RESULT_NAME = "contract_s6_variance_direction_results.json"


def variance_purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def run_probe(n_trials: int = 200, d: int = 2) -> dict:
    rng = np.random.default_rng(42)
    Ti_ops = build_Ti_ops(d)
    Fe_ops = build_Fe_ops(d)
    Fi_op = build_Fi_filter(d)
    Te_op = build_Te_hamiltonian(d, seed=42)

    quadrants = {
        "Type1_Deductive": [lambda rho: C_Ti(rho, Ti_ops), lambda rho: C_Fe(rho, Fe_ops)],
        "Type1_Inductive": [lambda rho: C_Fe(rho, Fe_ops), lambda rho: C_Ti(rho, Ti_ops)],
        "Type2_Deductive": [lambda rho: C_Fi(rho, Fi_op), lambda rho: C_Te(rho, Te_op)],
        "Type2_Inductive": [lambda rho: C_Te(rho, Te_op), lambda rho: C_Fi(rho, Fi_op)],
    }

    measurements = {}
    for name, ops in quadrants.items():
        early_deltas = []
        full_deltas = []
        for _ in range(n_trials):
            rho0 = make_random_density_matrix(d)
            v0 = variance_purity(rho0)
            rho1 = ops[0](rho0.copy())
            v1 = variance_purity(rho1)
            rho2 = ops[1](rho1.copy())
            v2 = variance_purity(rho2)
            early_deltas.append(v1 - v0)
            full_deltas.append(v2 - v0)
        measurements[name] = {
            "n_trials": n_trials,
            "avg_early_delta_v": float(np.mean(early_deltas)),
            "avg_full_delta_v": float(np.mean(full_deltas)),
            "early_positive_rate": float(np.mean([x > 0 for x in early_deltas])),
            "early_negative_rate": float(np.mean([x < 0 for x in early_deltas])),
        }

    verdicts = {
        "Type1_Deductive_early_decreases": bool(measurements["Type1_Deductive"]["avg_early_delta_v"] < 0.0),
        "Type1_Inductive_early_increases": bool(measurements["Type1_Inductive"]["avg_early_delta_v"] > 0.0),
        "Type2_Deductive_early_decreases": bool(measurements["Type2_Deductive"]["avg_early_delta_v"] < 0.0),
        "Type2_Inductive_early_increases": bool(measurements["Type2_Inductive"]["avg_early_delta_v"] > 0.0),
    }
    verdicts["all_contract_signs_hold"] = bool(all(verdicts.values()))

    token = EvidenceToken(
        token_id="E_SIM_CONTRACT_S6_VARIANCE_DIRECTION"
        if verdicts["all_contract_signs_hold"]
        else "",
        sim_spec_id="S_SIM_CONTRACT_S6_VARIANCE_DIRECTION_V1",
        status="PASS" if verdicts["all_contract_signs_hold"] else "KILL",
        measured_value=float(
            measurements["Type1_Inductive"]["avg_early_delta_v"]
            - measurements["Type1_Deductive"]["avg_early_delta_v"]
        ),
        kill_reason=None if verdicts["all_contract_signs_hold"] else "EARLY_VARIANCE_SIGNS_DO_NOT_MATCH_CONTRACT",
    )

    return {
        "schema": "SIM_EVIDENCE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "sim_name": "contract_s6_variance_direction",
        "status": "current_basis_measurement",
        "variance_definition": "V(rho) = Tr(rho^2)",
        "measurements": measurements,
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
    print(json.dumps(result["verdicts"], indent=2))


if __name__ == "__main__":
    main()
