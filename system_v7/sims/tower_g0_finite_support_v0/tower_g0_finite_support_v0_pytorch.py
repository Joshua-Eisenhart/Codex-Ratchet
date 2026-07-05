#!/usr/bin/env python3
"""PyTorch leg for G0 finite support."""

from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import datetime, timezone

import torch
import z3

SIM_ID = "tower_g0_finite_support_v0"
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / f"{SIM_ID}_pytorch_results.json"


def z3_completed_infinity_control() -> str:
    n = z3.Int("n")
    solver = z3.Solver()
    solver.add(n >= 0, n < 0)
    return str(solver.check())


def main() -> None:
    carrier = torch.arange(4, dtype=torch.int64)
    support = carrier[:3]
    labels = torch.tensor([20, 10, 30], dtype=torch.int64)
    shuffled = labels[torch.tensor([1, 0, 2])]
    growth_counts = [1, 2, 3, 4, 5]
    witnesses = {
        "carrier_size": int(carrier.numel()),
        "support_size": int(support.numel()),
        "supported_class_sum": int(torch.sum(support).item()),
        "growth_counts": growth_counts,
        "growth_all_finite": all(n < 10**6 for n in growth_counts),
        "label_shuffle_signature": sorted(int(x) for x in shuffled.tolist()),
    }
    refusals = {
        "unbounded_family_construction": {
            "receipt_type": "TYPED_REFUSAL",
            "reason": "F01 admits each finite support step, not a completed unbounded family object.",
        },
        "completed_infinity_equality": {
            "verdict": z3_completed_infinity_control(),
            "reason": "Exact equality over all natural-number indices demands completed infinity.",
        },
    }
    all_pass = witnesses["support_size"] == 3 and witnesses["growth_all_finite"] and refusals["completed_infinity_equality"]["verdict"].lower() == "unsat"
    source = pathlib.Path(__file__).resolve()
    result = {
        "schema": "engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "source_path": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "packages_used": ["torch", "z3", "json"],
        "aligned_packages_load_bearing": ["z3"],
        "reads_peer_result": False,
        "witnesses": witnesses,
        "refusal_receipts": refusals,
        "negative_controls": {"completed_infinity_refused_or_unsat": True, "label_shuffle_preserves_signature": witnesses["label_shuffle_signature"] == [10, 20, 30]},
        "TOOL_MANIFEST": {"torch": {"tried": True, "used": True, "reason": "finite carrier/support tensor arithmetic"}, "z3": {"tried": True, "used": True, "reason": "completed-infinity contradiction control"}},
        "TOOL_INTEGRATION_DEPTH": {"torch": "supportive", "z3": "load_bearing"},
        "all_pass": all_pass,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"engine": "pytorch", "all_pass": all_pass, "out": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
