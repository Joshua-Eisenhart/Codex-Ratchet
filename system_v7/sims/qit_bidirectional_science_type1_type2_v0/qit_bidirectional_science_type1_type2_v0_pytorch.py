#!/usr/bin/env python3
"""PyTorch autograd leg for qit_bidirectional_science_type1_type2_v0."""

from __future__ import annotations

import json

import torch
from torch.func import jacrev, vmap

from qit_bidirectional_science_type1_type2_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULTS,
    SIM_DIR,
    SIM_ID,
    build_core_measurement,
    now_z,
    rel,
    sha256_file,
    write_json,
)

SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULTS / f"{SIM_ID}_pytorch_results.json"
DTYPE = torch.float64


def torch_method_summary(core: dict) -> dict:
    type1 = torch.tensor([1.0 if row["roundtrip_survived"] else 0.0 for row in core["type1"]["nominal"]["rows"]], dtype=DTYPE)
    type2 = torch.tensor([1.0 if row["roundtrip_survived"] else 0.0 for row in core["type2"]["nominal"]["rows"]], dtype=DTYPE)
    pair = torch.stack([type1, type2], dim=1)
    type1_only = torch.logical_and(pair[:, 0] == 1.0, pair[:, 1] == 0.0).to(DTYPE)
    type2_only = torch.logical_and(pair[:, 0] == 0.0, pair[:, 1] == 1.0).to(DTYPE)
    shared_win = torch.logical_and(pair[:, 0] == 1.0, pair[:, 1] == 1.0).to(DTYPE)
    shared_fail = torch.logical_and(pair[:, 0] == 0.0, pair[:, 1] == 0.0).to(DTYPE)

    def margin(row: torch.Tensor) -> torch.Tensor:
        return row[0] - row[1]

    grads = vmap(jacrev(margin))(pair)
    grad_norms = torch.linalg.norm(grads, dim=1)
    return {
        "trial_count": int(type1.numel() + type2.numel()),
        "paired_trial_count": int(type1.numel()),
        "type1_accuracy": float(torch.mean(type1).item()),
        "type2_accuracy": float(torch.mean(type2).item()),
        "unique_win_counts": {
            "type1_only": int(torch.sum(type1_only).item()),
            "type2_only": int(torch.sum(type2_only).item()),
            "shared_win": int(torch.sum(shared_win).item()),
            "shared_fail": int(torch.sum(shared_fail).item()),
        },
        "method_order_delta_mean": float(torch.mean(type1 - type2).item()),
        "torch_func_jacrev_grad_norms": [float(value) for value in grad_norms.tolist()],
        "torch_func_jacrev_nonzero": bool(torch.min(grad_norms).item() > 1.0e-9),
    }


def build_result() -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    core = build_core_measurement()
    summary = torch_method_summary(core)
    all_pass = (
        core["all_pass"]
        and summary["type1_accuracy"] == 1.0
        and summary["type2_accuracy"] >= 0.85
        and summary["unique_win_counts"]["type1_only"] >= 1
        and summary["torch_func_jacrev_nonzero"]
    )
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "ran": True,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "object_count": core["type1"]["nominal"]["object_count"],
        "view_count": core["type1"]["nominal"]["view_count"],
        "trial_count": summary["trial_count"],
        "method_summary": summary,
        "packages_used": ["torch", "torch.func"],
        "aligned_packages_load_bearing": ["torch.func"],
        "package_observables": {
            "torch.func": "jacrev/vmap gradient norms of the Type-1 minus Type-2 method-order margin; nonzero sensitivity is required"
        },
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "supportive finite tensor method table"},
            "torch.func": {
                "tried": True,
                "used": True,
                "reason": "load-bearing jacrev/vmap sensitivity check on method-order margin",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "supportive", "torch.func": "load_bearing"},
    }
    write_json(RESULT_PATH, result)
    return result


def main() -> int:
    result = build_result()
    print(json.dumps({"engine": "pytorch", "all_pass": result["all_pass"], "out": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
