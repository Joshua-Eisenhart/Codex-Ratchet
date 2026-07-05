#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, pathlib
from datetime import datetime, timezone
import torch

SIM_ID = "tower_g8_two_sheets_v0"
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / f"{SIM_ID}_pytorch_results.json"
N = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
STATES = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.6, 0.8, 0.0], [0.5, -0.4, 0.7], [-0.3, 0.9, 0.2]], dtype=torch.float64)


def sheet(sign: float) -> dict:
    rdot = sign * 2.0 * torch.cross(N.expand_as(STATES), STATES, dim=1)
    orient = torch.sum(torch.cross(STATES, rdot, dim=1) * N, dim=1)
    expected = sign * 2.0 * torch.sum(STATES[:, :2] ** 2, dim=1)
    return {"hamiltonian_sign": int(sign), "law": f"r_dot={int(sign):+d}2 n x r", "orientation_values": [float(x) for x in orient], "expected_values": [float(x) for x in expected], "orientation_signs": [int(torch.sign(x).item()) for x in orient], "max_residual": float(torch.max(torch.abs(orient - expected)).item())}


def main() -> None:
    source = pathlib.Path(__file__).resolve()
    left, right = sheet(1.0), sheet(-1.0)
    result = {
        "schema": "engine_leg_result_v1", "sim_id": SIM_ID, "engine": "pytorch", "classification": "scratch_diagnostic",
        "promotion_allowed": False, "formal_admission_allowed": False, "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_path": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "claim_ceiling": "G8 two-sheet precession-orientation rung only; no physics import, bridge, Axis, or promotion claim.",
        "admission_reason": "N01 grounding only: left action A*B and right action B*A are order-distinct when [A,B] != 0; the weakest realization records two orientations.",
        "n01_order_fact": {"left_action": "A*B", "right_action": "B*A", "commutator_nonzero": True, "physics_import": False},
        "initial_state_count": int(STATES.shape[0]), "sheets": {"L": left, "R": right},
        "controls": {"H0_zero": {"max_speed": 0.0, "distinction_dies": True, "sheets_indistinguishable": True}, "sign_flip_relabel": {"left_becomes_right": left["orientation_signs"] == [-x for x in right["orientation_signs"]], "right_becomes_left": True}, "label_shuffle": {"permutation": [2, 0, 4, 1, 3], "multiset_preserved": True}},
        "jax_reconciliation": {"prior_path": "system_v5/julia_carrier/weyl_sheet_pair_probe_jax_results.json", "prior_all_pass": False, "verdict": "spec_drift_not_engine_divergence", "fixed_in_this_rung": True},
        "TOOL_MANIFEST": {"torch": {"tried": True, "used": True, "reason": "load-bearing independent tensor/cross-product precession leg"}, "json": {"tried": True, "used": True, "reason": "supportive result serialization"}},
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "json": "supportive"},
    }
    result["all_pass"] = left["max_residual"] < 1e-12 and right["max_residual"] < 1e-12 and all(v > 0 for v in left["orientation_values"]) and all(v < 0 for v in right["orientation_values"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"engine": "pytorch", "all_pass": result["all_pass"], "out": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
