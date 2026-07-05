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


class TypedRefusal(Exception):
    pass


def construct_carrier(spec: dict) -> torch.Tensor:
    if spec.get("family") == "unbounded":
        raise TypedRefusal("F01 refuses completed unbounded family construction; only finite support carriers are admissible.")
    return torch.arange(int(spec["carrier_size"]), dtype=torch.int64)


def z3_completed_infinity_control(carrier_ids: list[int]) -> dict:
    k = len(carrier_ids)
    images = [z3.Int(f"carrier_image_{i}") for i in range(k + 1)]
    solver = z3.Solver()
    for image in images:
        solver.add(z3.Or([image == class_id for class_id in carrier_ids]))
    solver.add(z3.Distinct(images))
    injective = str(solver.check()).lower()
    erased = z3.Solver()
    for image in images:
        erased.add(z3.Or([image == class_id for class_id in carrier_ids]))
    return {
        "solver_backend": "z3",
        "carrier_class_ids": carrier_ids,
        "carrier_size": k,
        "index_set_size": k + 1,
        "injective_pigeonhole_verdict": injective,
        "erased_injectivity_verdict": str(erased.check()).lower(),
        "claim": "No injective map exists from k+1 indices into the run's actual size-k carrier.",
    }


def main() -> None:
    carrier = construct_carrier({"family": "finite", "carrier_size": 4})
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
    try:
        construct_carrier({"family": "unbounded"})
        caught_refusal = {"receipt_type": "NOT_CAUGHT", "caught": False}
    except TypedRefusal as exc:
        caught_refusal = {"receipt_type": "TYPED_REFUSAL", "caught": True, "caught_type": type(exc).__name__, "message": str(exc)}
    pigeonhole = z3_completed_infinity_control([int(x) for x in carrier.tolist()])
    refusals = {
        "unbounded_family_construction": caught_refusal,
        "completed_infinity_pigeonhole": pigeonhole,
    }
    all_pass = witnesses["support_size"] == 3 and witnesses["growth_all_finite"] and caught_refusal["caught"] and pigeonhole["injective_pigeonhole_verdict"] == "unsat" and pigeonhole["erased_injectivity_verdict"] == "sat"
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
        "negative_controls": {"completed_infinity_pigeonhole_unsat": pigeonhole["injective_pigeonhole_verdict"] == "unsat", "erased_injectivity_control_sat": pigeonhole["erased_injectivity_verdict"] == "sat", "label_shuffle_preserves_signature": witnesses["label_shuffle_signature"] == [10, 20, 30]},
        "TOOL_MANIFEST": {"torch": {"tried": True, "used": True, "reason": "finite carrier/support tensor arithmetic"}, "z3": {"tried": True, "used": True, "reason": "pigeonhole unsat over the actual constructed carrier"}},
        "TOOL_INTEGRATION_DEPTH": {"torch": "supportive", "z3": "load_bearing"},
        "all_pass": all_pass,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"engine": "pytorch", "all_pass": all_pass, "out": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
