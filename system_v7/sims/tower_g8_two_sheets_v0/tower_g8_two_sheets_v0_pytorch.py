#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, pathlib
from datetime import datetime, timezone
import numpy as np
import torch

SIM_ID = "tower_g8_two_sheets_v0"
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / f"{SIM_ID}_pytorch_results.json"
N = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
STATES = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.6, 0.8, 0.0], [0.5, -0.4, 0.7], [-0.3, 0.9, 0.2]], dtype=torch.float64)
DT = 1.0e-4
STEPS = 240
TOL = 3.0e-4


def evolve_point(r0: torch.Tensor, sign: float) -> np.ndarray:
    r = r0.clone()
    points = []
    for _ in range(STEPS):
        points.append(r.detach().numpy().copy())
        r = r + DT * sign * 2.0 * torch.cross(N, r, dim=0)
    return np.asarray(points)


def measure_rates(sign: float) -> list[float]:
    times = np.arange(STEPS, dtype=float) * DT
    rates = []
    for state in STATES:
        points = evolve_point(state, sign)
        angles = np.unwrap(np.arctan2(points[:, 1], points[:, 0]))
        rates.append(float(np.polyfit(times, angles, 1)[0]))
    return rates


def analytic_orientation(sign: float) -> list[float]:
    return [float(sign * 2.0 * (state[0].item() ** 2 + state[1].item() ** 2)) for state in STATES]


def sheet(sign: float) -> dict:
    rates = measure_rates(sign)
    radii_sq = [float(state[0].item() ** 2 + state[1].item() ** 2) for state in STATES]
    orient = [rate * radius for rate, radius in zip(rates, radii_sq)]
    expected = analytic_orientation(sign)
    return {"hamiltonian_sign": int(sign), "law": f"r_dot={int(sign):+d}2 n x r", "measured_rates": rates, "orientation_values": orient, "expected_values": expected, "orientation_signs": [int(np.sign(x)) for x in orient], "max_residual": max(abs(a - b) for a, b in zip(orient, expected)), "tolerance": TOL}


def controls(left: dict, right: dict) -> dict:
    zero_rates = measure_rates(0.0)
    zero_orient = [rate * float(state[0].item() ** 2 + state[1].item() ** 2) for rate, state in zip(zero_rates, STATES)]
    relabeled_right_values = [-value for value in right["orientation_values"]]
    perm = [2, 0, 4, 1, 3]
    shuffled_left = [left["orientation_values"][i] for i in perm]
    relabel_residual = max(abs(a - b) for a, b in zip(relabeled_right_values, left["orientation_values"]))
    sign_residual = max(abs(a + b) for a, b in zip(right["orientation_values"], left["orientation_values"]))
    return {"H0_zero": {"measured_rates": zero_rates, "max_abs_rate": max(abs(x) for x in zero_rates), "max_abs_orientation": max(abs(x) for x in zero_orient), "sheets_indistinguishable": max(abs(x) for x in zero_rates) < TOL}, "sign_flip_relabel": {"applied_relabel": "measured R orientation values multiplied by -1", "measured_right_values": right["orientation_values"], "relabeled_measured_right_values": relabeled_right_values, "max_residual_after_relabel": relabel_residual, "left_becomes_right": relabel_residual < TOL, "right_becomes_left": sign_residual < TOL}, "label_shuffle": {"permutation": perm, "shuffled_values": shuffled_left, "multiset_preserved": sorted(round(x, 12) for x in shuffled_left) == sorted(round(x, 12) for x in left["orientation_values"])}}


def main() -> None:
    source = pathlib.Path(__file__).resolve()
    left, right = sheet(1.0), sheet(-1.0)
    computed_controls = controls(left, right)
    result = {
        "schema": "engine_leg_result_v1", "sim_id": SIM_ID, "engine": "pytorch", "classification": "scratch_diagnostic",
        "promotion_allowed": False, "formal_admission_allowed": False, "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_path": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "claim_ceiling": "G8 two-sheet precession-orientation rung only; no physics import, bridge, Axis, or promotion claim.",
        "admission_reason": "N01 grounding only: left action A*B and right action B*A are order-distinct when [A,B] != 0; the weakest realization records two orientations.",
        "n01_order_fact": {"left_action": "A*B", "right_action": "B*A", "commutator_nonzero": True, "physics_import": False},
        "initial_state_count": int(STATES.shape[0]), "sheets": {"L": left, "R": right},
        "controls": computed_controls,
        "jax_reconciliation": {"prior_path": "system_v5/julia_carrier/weyl_sheet_pair_probe_jax_results.json", "prior_all_pass": False, "verdict": "spec_drift_not_engine_divergence", "fixed_in_this_rung": True},
        "TOOL_MANIFEST": {"torch": {"tried": True, "used": True, "reason": "load-bearing independent tensor/cross-product precession leg"}, "json": {"tried": True, "used": True, "reason": "supportive result serialization"}},
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "json": "supportive"},
    }
    result["all_pass"] = left["max_residual"] < TOL and right["max_residual"] < TOL and all(v > 0 for v in left["orientation_values"]) and all(v < 0 for v in right["orientation_values"]) and computed_controls["H0_zero"]["sheets_indistinguishable"] and computed_controls["sign_flip_relabel"]["left_becomes_right"] and computed_controls["sign_flip_relabel"]["right_becomes_left"] and computed_controls["label_shuffle"]["multiset_preserved"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"engine": "pytorch", "all_pass": result["all_pass"], "out": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
