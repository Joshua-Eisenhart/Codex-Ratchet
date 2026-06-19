#!/usr/bin/env python3
"""Python/JAX-side exact consumer for malcev_akivis_tangent_micro_v0."""

from __future__ import annotations

import json
from pathlib import Path

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp

from malcev_akivis_tangent_micro_v0_common import ROOT, RESULT_DIR, SIM_ID, build_engine_payload


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"


def main() -> int:
    payload = build_engine_payload(ENGINE, SOURCE_PATH, include_smt=True)
    payload["runtime_preflight"] = {
        "jax_version": jax.__version__,
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "jax_int64_basis_probe": jax.device_get(jnp.arange(7, dtype=jnp.int64)).tolist(),
    }
    payload["packages_used"] = ["jax", "jax.numpy", *payload["packages_used"]]
    payload["TOOL_MANIFEST"]["jax"] = {"tried": True, "used": True, "reason": "supportive x64/int64 runtime guard for the Python mirror; exact proof remains integer residual computation"}
    payload["TOOL_MANIFEST"]["jax.numpy"] = {"tried": True, "used": True, "reason": "supportive int64 basis probe; not a numeric tolerance proof"}
    payload["TOOL_INTEGRATION_DEPTH"]["jax"] = "supportive"
    payload["TOOL_INTEGRATION_DEPTH"]["jax.numpy"] = "supportive"
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "engine": ENGINE, "result_path": str(RESULT_PATH.relative_to(ROOT))}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
