#!/usr/bin/env python3
"""Capability probe for the `torch.func` API surface."""

from __future__ import annotations

import json
import os
from pathlib import Path

classification = "canonical"
promotion_allowed = False

ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = ROOT / "system_v4/probes/a2_state/sim_results/torch_func_capability_results.json"

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive tensor substrate for torch.func jacrev and vmap capability checks",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacrev and vmap calls decide positive, negative, and boundary checks",
    },
}

TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing"}


def main() -> int:
    import torch
    from torch.func import jacrev, vmap

    torch.set_default_dtype(torch.float64)

    def cubic(x: torch.Tensor) -> torch.Tensor:
        return x**3 + 2.0 * x

    x = torch.tensor(2.0, dtype=torch.float64)
    grad = jacrev(cubic)(x)
    positive_jacrev = abs(float(grad) - 14.0) < 1.0e-10

    xs = torch.arange(5, dtype=torch.float64)
    batched = vmap(lambda t: t * t + 1.0)(xs)
    positive_vmap = torch.equal(batched, xs * xs + 1.0)

    wrong_grad = jacrev(lambda t: t * t)(x)
    negative_control = abs(float(wrong_grad) - 14.0) > 1.0

    singleton = torch.tensor([0.0], dtype=torch.float64)
    singleton_out = vmap(lambda t: t + 1.0)(singleton)
    boundary_singleton_vmap = tuple(singleton_out.shape) == (1,) and float(singleton_out[0]) == 1.0

    all_pass = positive_jacrev and positive_vmap and negative_control and boundary_singleton_vmap
    payload = {
        "name": "sim_torch_func_capability",
        "schema_version": "capability_probe_v1",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "python_executable": os.sys.executable,
        "torch_version": torch.__version__,
        "positive": {
            "jacrev_cubic_plus_linear": {"pass": positive_jacrev, "observed": float(grad), "expected": 14.0},
            "vmap_square_plus_one": {"pass": bool(positive_vmap), "observed": batched.tolist()},
        },
        "negative": {
            "wrong_function_gradient_does_not_match": {
                "pass": negative_control,
                "observed": float(wrong_grad),
                "forbidden_expected": 14.0,
            }
        },
        "boundary": {"vmap_singleton_batch": {"pass": boundary_singleton_vmap, "observed": singleton_out.tolist()}},
        "summary": {"all_pass": bool(all_pass)},
        "overall_pass": bool(all_pass),
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
