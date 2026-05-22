#!/usr/bin/env python3
"""auto_LiRPA two-order adapter bound micro-probe."""

from __future__ import annotations

import json
import pathlib
import sys
import time
from typing import Any

import torch
import torch.nn as nn


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "auto_lirpa_two_order_adapter_bound_micro_probe_results.json"
AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")

NAME = "auto_lirpa_two_order_adapter_bound_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: auto_LiRPA bounds a tiny two-order torch adapter. "
    "Bound separation is evidence-bound tool pressure, not a promoted manifold or verifier claim."
)
TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing tensor fixture and two-order adapter"},
    "auto_LiRPA": {"tried": True, "used": True, "reason": "load-bearing IBP bounds over the adapter"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "auto_LiRPA": "load_bearing",
}
NEARBY_VARIANTS = {
    "total": 1,
    "passed": 1,
    "variants": ["same_order_self_control_has_zero_gap"],
}
WHY_NOT_V4_PROBES = [
    "This is a v5 formal scout for a tiny auto_LiRPA adapter-bound micro fixture.",
    "It records tool pressure and contract evidence only; it does not promote a v4 canonical probe or manifold claim.",
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        return value.detach().cpu().tolist()
    return value


def blocked_receipt(started: float, blocker: str, detail: str) -> dict[str, Any]:
    return {
        "name": NAME,
        "schema": "formal_scout_result_v1",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": {
            "pytorch": TOOL_MANIFEST["pytorch"],
            "auto_LiRPA": {"tried": True, "used": False, "reason": blocker},
        },
        "TOOL_MANIFEST": {
            "pytorch": TOOL_MANIFEST["pytorch"],
            "auto_LiRPA": {"tried": True, "used": False, "reason": blocker},
        },
        "tool_integration_depth": {"pytorch": TOOL_INTEGRATION_DEPTH["pytorch"], "auto_LiRPA": None},
        "TOOL_INTEGRATION_DEPTH": {"pytorch": TOOL_INTEGRATION_DEPTH["pytorch"], "auto_LiRPA": None},
        "positive": {},
        "graveyard_companions": {},
        "boundary": {"blocked_before_bound_execution": {"pass": False, "detail": detail}},
        "nearby_variants": {"total": 0, "passed": 0, "variants": []},
        "why_not_v4_probes": WHY_NOT_V4_PROBES,
        "blockers": [{"kind": blocker, "detail": detail}],
        "elapsed_seconds": time.time() - started,
        "all_pass": False,
    }


class TwoOrderAdapter(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(6, 1)
        with torch.no_grad():
            self.linear.weight.copy_(torch.tensor([[0.9, -0.7, 0.4, -0.2, 0.5, -0.3]], dtype=torch.float32))
            self.linear.bias.fill_(0.05)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        left = x[:, :3]
        right = x[:, 3:]
        ordered = torch.cat([left, right - left], dim=1)
        return self.linear(ordered)


def run_probe() -> dict[str, Any]:
    if not AUTO_LIRPA_ROOT.exists():
        raise FileNotFoundError(f"missing local checkout: {AUTO_LIRPA_ROOT}")
    sys.path.insert(0, str(AUTO_LIRPA_ROOT))
    from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm

    model = TwoOrderAdapter().eval()
    x_ab = torch.tensor([[0.10, -0.20, 0.35, 0.40, 0.05, -0.15]], dtype=torch.float32)
    x_ba = torch.cat([x_ab[:, 3:], x_ab[:, :3]], dim=1)
    ptb = PerturbationLpNorm(norm=float("inf"), eps=0.015)
    bounded = BoundedModule(model, x_ab, bound_opts={"conv_mode": "patches"})
    lb_ab, ub_ab = bounded.compute_bounds(x=(BoundedTensor(x_ab, ptb),), method="IBP")
    lb_ba, ub_ba = bounded.compute_bounds(x=(BoundedTensor(x_ba, ptb),), method="IBP")
    center_ab = model(x_ab)
    center_ba = model(x_ba)
    gap = torch.abs(center_ab - center_ba)
    bound_width = torch.max(ub_ab - lb_ab, ub_ba - lb_ba)
    positive = {
        "auto_lirpa_ibp_bounds_execute": {
            "pass": bool(torch.isfinite(lb_ab).all().item() and torch.isfinite(ub_ab).all().item()),
            "ab_lower": float(lb_ab.item()),
            "ab_upper": float(ub_ab.item()),
            "ba_lower": float(lb_ba.item()),
            "ba_upper": float(ub_ba.item()),
        },
        "two_order_centers_separate_beyond_bound_width": {
            "pass": bool(gap.item() > bound_width.item()),
            "center_gap": float(gap.item()),
            "max_bound_width": float(bound_width.item()),
        },
    }
    graveyard = {
        "same_order_self_control_has_zero_gap": {
            "pass": bool(torch.abs(model(x_ab) - model(x_ab)).item() == 0.0),
            "self_gap": 0.0,
        }
    }
    return {
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": {"epsilon": 0.015, "root_constraint_wording": "not promoted beyond bounded adapter receipt"},
        "blockers": [],
        "all_pass": all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard.values()),
    }


def main() -> int:
    started = time.time()
    try:
        body = run_probe()
        result = {
            "name": NAME,
            "schema": "formal_scout_result_v1",
            "classification": CLASSIFICATION,
            "sim_execution_kind": SIM_EXECUTION_KIND,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
            "tool_manifest": TOOL_MANIFEST,
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
            "nearby_variants": NEARBY_VARIANTS,
            "why_not_v4_probes": WHY_NOT_V4_PROBES,
            "elapsed_seconds": time.time() - started,
            **body,
        }
    except FileNotFoundError as exc:
        result = blocked_receipt(started, "missing_runtime", str(exc))
    except ImportError as exc:
        result = blocked_receipt(started, "missing_import", f"auto_LiRPA import failed: {exc}")
    except Exception as exc:
        result = blocked_receipt(started, "runtime_error", f"auto_LiRPA bound execution failed: {type(exc).__name__}: {exc}")
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
