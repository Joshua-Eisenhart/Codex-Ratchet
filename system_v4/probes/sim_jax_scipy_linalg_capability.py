#!/usr/bin/env python3
"""Capability probe for `jax.scipy.linalg` matrix functions."""

from __future__ import annotations

import json
import os
from pathlib import Path

classification = "canonical"
promotion_allowed = False

ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = ROOT / "system_v4/probes/a2_state/sim_results/jax_scipy_linalg_capability_results.json"

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 array runtime"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive matrix construction"},
    "jax.scipy.linalg": {
        "tried": True,
        "used": True,
        "reason": "load-bearing expm calls decide rotation and noncommuting controls",
    },
}
TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "jax.numpy": "supportive", "jax.scipy.linalg": "load_bearing"}


def main() -> int:
    import jax
    import jax.numpy as jnp
    import jax.scipy.linalg as jsp_linalg

    jax.config.update("jax_enable_x64", True)

    theta = 0.37
    generator = jnp.asarray([[0.0, -theta], [theta, 0.0]], dtype=jnp.float64)
    observed = jsp_linalg.expm(generator)
    expected = jnp.asarray([[jnp.cos(theta), -jnp.sin(theta)], [jnp.sin(theta), jnp.cos(theta)]], dtype=jnp.float64)
    rotation_err = float(jax.device_get(jnp.max(jnp.abs(observed - expected))))

    a = jnp.asarray([[0.0, 1.0], [0.0, 0.0]], dtype=jnp.float64)
    b = jnp.asarray([[0.0, 0.0], [1.0, 0.0]], dtype=jnp.float64)
    noncomm_gap = float(jax.device_get(jnp.max(jnp.abs(jsp_linalg.expm(a + b) - jsp_linalg.expm(a) @ jsp_linalg.expm(b)))))
    identity_err = float(jax.device_get(jnp.max(jnp.abs(jsp_linalg.expm(jnp.zeros((2, 2), dtype=jnp.float64)) - jnp.eye(2)))))

    positive = rotation_err < 1.0e-10
    negative = noncomm_gap > 1.0e-2
    boundary = identity_err < 1.0e-12
    all_pass = positive and negative and boundary
    payload = {
        "name": "sim_jax_scipy_linalg_capability",
        "schema_version": "capability_probe_v1",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "python_executable": os.sys.executable,
        "jax_version": jax.__version__,
        "positive": {"expm_rotation_matches_closed_form": {"pass": positive, "max_abs_err": rotation_err}},
        "negative": {"noncommuting_expm_product_mismatch": {"pass": negative, "max_abs_gap": noncomm_gap}},
        "boundary": {"zero_matrix_expm_identity": {"pass": boundary, "max_abs_err": identity_err}},
        "summary": {"all_pass": bool(all_pass)},
        "overall_pass": bool(all_pass),
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
