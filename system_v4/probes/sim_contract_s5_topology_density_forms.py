#!/usr/bin/env python3
"""
SIM 5 — Contract Topology Density Forms
=======================================
Measurement-only probe for the four canonical d=2 density forms.

T1 Localized   = near-pure projective state
T2 Distributed = near-maximally mixed state
T3 Coherent    = strong off-diagonal phase state
T4 Partitioned = diagonal mixed partition

This probe does two things:
  1. Classify canonical forms and operator-induced transitions.
  2. Compare Type-1 vs Type-2 macro-stage outputs by topology label
     to see whether Axis 3 orientation changes topology class.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical contract baseline: this measures topology-density forms and operator transitions on the current engine, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "density-form classification and transition numerics"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, StageControls, STAGES
from geometric_operators import I2, apply_Fe, apply_Fi, apply_Te, apply_Ti, _ensure_valid_density
from proto_ratchet_sim_runner import EvidenceToken


RESULT_NAME = "contract_s5_topology_density_forms_results.json"


def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def offdiag_mag(rho: np.ndarray) -> float:
    return float(abs(rho[0, 1]))


def bloch_radius(rho: np.ndarray) -> float:
    x = 2 * np.real(rho[0, 1])
    y = -2 * np.imag(rho[0, 1])
    z = np.real(rho[0, 0] - rho[1, 1])
    return float(np.sqrt(x * x + y * y + z * z))


def classify_topology(rho: np.ndarray) -> str:
    p = purity(rho)
    off = offdiag_mag(rho)
    radius = bloch_radius(rho)
    if off > 0.25:
        return "T3_Coherent"
    if p > 0.95 or radius > 0.95:
        return "T1_Localized"
    if p < 0.60 or radius < 0.20:
        return "T2_Distributed"
    return "T4_Partitioned"


def canonical_forms() -> dict[str, np.ndarray]:
    return {
        "T1_Localized": np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex),
        "T2_Distributed": I2 / 2,
        "T3_Coherent": np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex),
        "T4_Partitioned": np.array([[0.75, 0.0], [0.0, 0.25]], dtype=complex),
    }


def run_operator_transition_catalog() -> list[dict]:
    ops = {
        "Ti_up": lambda rho: apply_Ti(rho, polarity_up=True, strength=0.6),
        "Ti_down": lambda rho: apply_Ti(rho, polarity_up=False, strength=0.6),
        "Fe_up": lambda rho: apply_Fe(rho, polarity_up=True, strength=0.6),
        "Fe_down": lambda rho: apply_Fe(rho, polarity_up=False, strength=0.6),
        "Te_up": lambda rho: apply_Te(rho, polarity_up=True, strength=0.6),
        "Te_down": lambda rho: apply_Te(rho, polarity_up=False, strength=0.6),
        "Fi_up": lambda rho: apply_Fi(rho, polarity_up=True, strength=0.6),
        "Fi_down": lambda rho: apply_Fi(rho, polarity_up=False, strength=0.6),
    }
    transitions = []
    for form_name, rho in canonical_forms().items():
        for op_name, op_fn in ops.items():
            rho_after = _ensure_valid_density(op_fn(rho.copy()))
            transitions.append({
                "form": form_name,
                "operator": op_name,
                "class_before": classify_topology(rho),
                "class_after": classify_topology(rho_after),
                "purity_before": purity(rho),
                "purity_after": purity(rho_after),
                "offdiag_before": offdiag_mag(rho),
                "offdiag_after": offdiag_mag(rho_after),
            })
    return transitions


def run_axis3_orientation_check(n_trials: int = 8) -> list[dict]:
    records = []
    for stage_idx, stage in enumerate(STAGES):
        torus_eta = 3 * np.pi / 8 if stage["loop"] == "base" else np.pi / 8
        for trial in range(n_trials):
            theta1 = 0.37 * (trial + 1)
            theta2 = 0.61 * (trial + 1)
            per_type = {}
            for engine_type in (1, 2):
                engine = GeometricEngine(engine_type=engine_type)
                state = engine.init_state(
                    eta=torus_eta,
                    theta1=theta1,
                    theta2=theta2,
                    rng=np.random.default_rng(5000 + 100 * stage_idx + 10 * trial + engine_type),
                )
                controls = StageControls(
                    piston=0.8,
                    lever=True,
                    torus=torus_eta,
                    spinor="both",
                )
                state_after = engine.step(state, stage_idx=stage_idx, controls=controls)
                rho_avg = _ensure_valid_density((state_after.rho_L + state_after.rho_R) / 2)
                per_type[engine_type] = {
                    "class_after": classify_topology(rho_avg),
                    "purity_after": purity(rho_avg),
                    "offdiag_after": offdiag_mag(rho_avg),
                }
            records.append({
                "terrain": stage["name"],
                "topology_label": stage["name"].split("_")[0],
                "loop": stage["loop"],
                "trial": trial,
                "type1": per_type[1],
                "type2": per_type[2],
                "same_class": per_type[1]["class_after"] == per_type[2]["class_after"],
            })
    return records


def main() -> None:
    transition_catalog = run_operator_transition_catalog()
    orientation_records = run_axis3_orientation_check()
    same_class_rate = float(np.mean([r["same_class"] for r in orientation_records]))

    token = EvidenceToken(
        token_id="E_SIM_CONTRACT_S5_TOPOLOGY_FORMS_BASELINE" if same_class_rate >= 0.75 else "",
        sim_spec_id="S_SIM_CONTRACT_S5_TOPOLOGY_FORMS_V1",
        status="PASS" if same_class_rate >= 0.75 else "KILL",
        measured_value=same_class_rate,
        kill_reason=None if same_class_rate >= 0.75 else "AXIS3_ORIENTATION_CHANGES_CLASS_TOO_OFTEN",
    )

    result = {
        "schema": "SIM_EVIDENCE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "sim_name": "contract_s5_topology_density_forms",
        "status": "current_engine_baseline_only",
        "canonical_forms": {
            name: {
                "class": classify_topology(rho),
                "purity": purity(rho),
                "offdiag": offdiag_mag(rho),
            }
            for name, rho in canonical_forms().items()
        },
        "operator_transition_catalog": transition_catalog,
        "axis3_orientation_check": {
            "same_class_rate": same_class_rate,
            "records_preview": orientation_records[:24],
        },
        "evidence_ledger": [token.__dict__],
    }

    base = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, RESULT_NAME)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {out_path}")
    print(json.dumps(result["axis3_orientation_check"], indent=2))


if __name__ == "__main__":
    main()
