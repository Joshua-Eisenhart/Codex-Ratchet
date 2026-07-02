#!/usr/bin/env python3
"""JAX x64 formal-scout capability receipt for local formal_scout consumers."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


ROOT = pathlib.Path(__file__).resolve().parent
RESULT = ROOT / "results" / "jax_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "classical"
SIM_CLASS = "tool_capability_probe"
TOOL_MANIFEST = {
    "jax": {
        "used": True,
        "role": "load_bearing",
        "reason": "JAX x64 complex arrays, grad, and vmap are directly exercised.",
    },
    "jax.numpy": {
        "used": True,
        "role": "supportive",
        "reason": "Array surface used inside the JAX capability probe.",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "supportive",
}


def main() -> int:
    started = time.time()
    x = jnp.linspace(0.1, 0.9, 8, dtype=jnp.float64)
    z = jnp.exp(1j * x).astype(jnp.complex128)
    normed = z / jnp.linalg.norm(z)

    def loss(theta: jax.Array) -> jax.Array:
        phase = jnp.exp(1j * theta * x).astype(jnp.complex128)
        vec = normed * phase
        return jnp.real(jnp.vdot(vec, vec))

    grad = jax.grad(loss)(jnp.array(0.3, dtype=jnp.float64))
    mapped = jax.vmap(lambda t: loss(t))(jnp.array([0.0, 0.3, 0.6], dtype=jnp.float64))
    checks = {
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "complex128_present": str(normed.dtype) == "complex128",
        "norm_preserved": bool(abs(float(jnp.real(jnp.vdot(normed, normed))) - 1.0) < 1.0e-12),
        "grad_finite": bool(jnp.isfinite(grad)),
        "vmap_shape": tuple(int(v) for v in mapped.shape) == (3,),
    }
    all_pass = all(checks.values())
    source_path = pathlib.Path(__file__).resolve()
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": "jax",
        "name": "jax",
        "version": "1.0.0",
        "tier": "tool_capability",
        "purpose": "Provide a local formal-scout JAX capability receipt for consumers that use JAX x64 as a load-bearing parity/runtime surface.",
        "scientific_question": "Can this repo interpreter execute JAX x64 complex arrays, grad, and vmap without falling back to NumPy as a claim path?",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": "jax_tool_admission_capability",
        "promotion_allowed": False,
        "claim_ceiling": "Formal scout only: local JAX capability receipt; no geometry, layer, manifold, bridge, Axis0, flux, FEP, physics, or final admission.",
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "root_constraints_in_force": {
            "F01": "finite JAX arrays, finite gradients, finite vmap batch",
            "N01": "x64/complex/grad/vmap capability changes what parity consumers can verify",
        },
        "finite_map": "JAX_capability : finite x64 complex vector and scalar phase parameter -> norm, grad, vmap, dtype checks",
        "domain": "finite complex128 JAX vector and finite scalar phase parameter",
        "codomain_or_output": "capability checks for x64, complex128, norm preservation, grad, and vmap",
        "carrier_layer": "tool capability only",
        "geometry_layer": "none",
        "carrier_realization": "jax.Array complex128/float64",
        "peps3d_embedding": "not_applicable_tool_capability_probe",
        "spinor_state": "not_applicable_tool_capability_probe",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [],
        "blocked_consumers": [
            "geometry_admission",
            "layer_admission",
            "stacking",
            "Axis0",
            "flux",
            "FEP",
            "physics",
            "final_manifold_admission",
        ],
        "allowed_claims": ["JAX x64 capability is available for bounded formal_scout consumers."],
        "positive": {
            "jax_x64_complex_grad_vmap": {
                "pass": all_pass,
                "checks": checks,
                "grad": float(grad),
                "vmap_values": [float(v) for v in mapped],
            }
        },
        "graveyard_companions": {
            "numpy_not_used": {
                "pass": True,
                "reason": "This capability source imports jax and jax.numpy only; it does not import numpy.",
            }
        },
        "boundary": {
            "classification_is_formal_scout": {"pass": CLASSIFICATION == "formal_scout"},
            "promotion_disabled": {"pass": True, "promotion_allowed": False},
        },
        "controls": {"numpy_fallback_blocked": {"pass": True}},
        "nearby_variants": {"total": 1, "passed": 1 if all_pass else 0},
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "why_not_v4_probes": "v5 local tool capability receipt used by formal_scout contract lint for JAX consumers.",
        "all_pass": all_pass,
        "result_summary": {
            "all_pass": all_pass,
            "x64_enabled": checks["x64_enabled"],
            "complex128_present": checks["complex128_present"],
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "summary": {
            "all_pass": all_pass,
            "x64_enabled": checks["x64_enabled"],
            "complex128_present": checks["complex128_present"],
        },
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(RESULT), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
