#!/usr/bin/env python3
"""Capability probe for `ott` Sinkhorn transport."""

from __future__ import annotations

import json
import os
from pathlib import Path

classification = "canonical"
promotion_allowed = False

ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = ROOT / "system_v4/probes/a2_state/sim_results/ott_capability_results.json"

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 array runtime for OTT"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive point-cloud array construction"},
    "ott": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PointCloud, LinearProblem, and Sinkhorn output decide all checks",
    },
}

TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "jax.numpy": "supportive", "ott": "load_bearing"}


def main() -> int:
    import jax
    import jax.numpy as jnp
    from ott.geometry import pointcloud
    from ott.problems.linear import linear_problem
    from ott.solvers.linear import sinkhorn

    jax.config.update("jax_enable_x64", True)

    xs = jnp.linspace(0.0, 1.0, 6, dtype=jnp.float64)[:, None]
    near = xs + 0.01
    far = xs + 1.0

    solver = sinkhorn.Sinkhorn(threshold=1.0e-3, max_iterations=200)

    def cost(a, b) -> float:
        geom = pointcloud.PointCloud(a, b, epsilon=5.0e-2)
        out = solver(linear_problem.LinearProblem(geom))
        return float(jax.device_get(out.reg_ot_cost))

    near_cost = cost(xs, near)
    far_cost = cost(xs, far)
    self_cost = cost(xs, xs)
    positive = near_cost < far_cost
    negative = far_cost > near_cost * 5.0
    boundary = self_cost <= near_cost
    all_pass = positive and negative and boundary

    payload = {
        "name": "sim_ott_capability",
        "schema_version": "capability_probe_v1",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "python_executable": os.sys.executable,
        "jax_version": jax.__version__,
        "positive": {"near_cloud_cheaper_than_reversed": {"pass": positive, "near_cost": near_cost, "far_cost": far_cost}},
        "negative": {"reversed_cloud_cost_separates": {"pass": negative, "ratio": far_cost / max(near_cost, 1.0e-12)}},
        "boundary": {"self_transport_not_more_expensive": {"pass": boundary, "self_cost": self_cost}},
        "summary": {"all_pass": bool(all_pass)},
        "overall_pass": bool(all_pass),
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
