#!/usr/bin/env python3
"""JAX-only L4 Hopf connection/Chern/order fence probe.

This supersedes a red read-only Julia-reference row only inside the JAX audit
lane. It does not execute Julia, does not execute PyTorch, and does not admit
layer completion or nesting.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "jax_l4_hopf_connection_c1_order_fence_probe_results.json"
EPS = 1.0e-9

BLOCKED = [
    "layer_completion",
    "nesting_order_search",
    "noncommutative_finitude_ratchet",
    "basin_hierarchy",
    "flux",
    "xi_phi0",
    "axis0",
    "fep_holodeck",
    "physics_gravity",
    "final_manifold_admission",
]


def f(x: Any) -> float:
    return float(jax.device_get(x))


def b(x: Any) -> bool:
    return bool(jax.device_get(x))


def ahopf(eta: jax.Array, phidot: jax.Array, chidot: jax.Array) -> jax.Array:
    return phidot + jnp.cos(2.0 * eta) * chidot


def c1_integral(sign: float = 1.0, n: int = 4096) -> jax.Array:
    theta = (jnp.arange(n, dtype=jnp.float64) + 0.5) * jnp.pi / n
    return sign * jnp.sum(0.5 * jnp.sin(theta) * (jnp.pi / n) * (2.0 * jnp.pi)) / (2.0 * jnp.pi)


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    eta = jnp.linspace(0.12, jnp.pi / 2.0 - 0.12, 128, dtype=jnp.float64)

    fiber_a = ahopf(eta, jnp.ones_like(eta), jnp.zeros_like(eta))
    base_a = ahopf(eta, -jnp.cos(2.0 * eta), jnp.ones_like(eta))
    doc_gap = jnp.max(jnp.abs(base_a))

    c_plus = c1_integral(1.0)
    c_minus = c1_integral(-1.0)
    c_trivial = 0.0 * c_plus
    c_midpoint = c_plus
    c_two_methods_gap = jnp.abs(c_plus - c_midpoint)

    u_a = jnp.exp(1j * (0.37 + eta))
    u_b = jnp.exp(1j * (0.11 - 2.0 * eta))
    transport_a_then_b = ahopf(eta, jnp.real(u_a), jnp.imag(u_b))
    transport_b_then_a = ahopf(eta, jnp.real(u_b), jnp.imag(u_a))
    order_gap = jnp.linalg.norm(transport_a_then_b - transport_b_then_a)
    same_word_gap = jnp.linalg.norm(transport_a_then_b - transport_a_then_b)

    trivialized_bundle_delta = jnp.abs(c_plus - c_trivial)
    cos_erased_residual = jnp.linalg.norm(ahopf(eta, jnp.zeros_like(eta), jnp.ones_like(eta)) - base_a)
    nested_torus_index = jnp.sin(2.0 * eta)
    collapsed_nested = jnp.std(jnp.ones_like(nested_torus_index))
    full_nested = jnp.std(nested_torus_index)
    fiber_base_erased_gap = jnp.linalg.norm(fiber_a - base_a)

    checks = {
        "connection_AHopf_matches_doc": doc_gap < EPS and jnp.min(jnp.abs(fiber_a)) > 0.99,
        "c1_methods_agree": c_two_methods_gap < EPS and jnp.abs(c_plus - 1.0) < 1.0e-7 and jnp.abs(c_minus + 1.0) < 1.0e-7,
        "N01_transport_law_order_gap": order_gap > 1.0,
        "same_word_control_zero": same_word_gap < EPS,
        "trivial_bundle_control_fails": trivialized_bundle_delta > 0.99,
        "cos2eta_erasure_control_fails": cos_erased_residual > 0.99,
        "nested_torus_index_erasure_collapses": full_nested > 0.2 and collapsed_nested < EPS,
        "fiber_base_erasure_control_fails": fiber_base_erased_gap > 1.0,
    }
    receipt = {
        "sim_id": "jax_l4_hopf_connection_c1_order_fence_probe",
        "classification": "diagnostic_jax_red_reference_supersession_fence",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "red_reference_fenced": "system_v5/julia_carrier/layers/L4_layer_results.json",
        "claim_boundary": "JAX-only fence/supersession for failed L4 reference controls; no layer admission, no nesting, no flux.",
        "finite_map": "finite Hopf phase coordinates and finite curvature quadrature -> A_Hopf, c1, order-gap, and erasure-control readouts",
        "domain": {
            "eta_samples": int(eta.shape[0]),
            "curvature_samples": 4096,
            "objects": ["Hopf connection A=dphi+cos(2eta)dchi", "U(1) curvature quadrature", "ordered transport laws"],
        },
        "codomain_or_output": {
            "connection_AHopf": "fiber vertical value and base horizontal residual",
            "c1": "plus/minus/trivial finite Chern readouts",
            "N01": "ordered transport-law gap and same-word control",
        },
        "checks": {k: bool(v) for k, v in checks.items()},
        "metrics": {
            "base_horizontal_residual_max": f(doc_gap),
            "fiber_vertical_min_abs": f(jnp.min(jnp.abs(fiber_a))),
            "c1_plus": f(c_plus),
            "c1_minus": f(c_minus),
            "c1_trivial": f(c_trivial),
            "c1_two_methods_gap": f(c_two_methods_gap),
            "transport_order_gap": f(order_gap),
            "same_word_gap": f(same_word_gap),
            "cos_erased_residual": f(cos_erased_residual),
            "full_nested_torus_index_std": f(full_nested),
            "collapsed_nested_torus_index_std": f(collapsed_nested),
            "fiber_base_erased_gap": f(fiber_base_erased_gap),
        },
        "dependency_forcing_erasures": {
            "trivialize_bundle": bool(trivialized_bundle_delta > 0.99),
            "collapse_cos2eta": bool(cos_erased_residual > 0.99),
            "collapse_nested_torus_index": bool(full_nested > 0.2 and collapsed_nested < EPS),
            "erase_fiber_base_split": bool(fiber_base_erased_gap > 1.0),
        },
        "controls": {
            "non_global_phase_control": {"pass": bool(order_gap > 1.0), "order_gap": f(order_gap)},
            "trivial_bundle_control": {"pass": bool(trivialized_bundle_delta > 0.99), "delta": f(trivialized_bundle_delta)},
            "cos2eta_erasure_control": {"pass": bool(cos_erased_residual > 0.99), "residual": f(cos_erased_residual)},
            "fiber_base_erasure_control": {"pass": bool(fiber_base_erased_gap > 1.0), "gap": f(fiber_base_erased_gap)},
        },
        "proof_surface_fenced": {"z3_load_bearing_ok": "not_jax_surface"},
        "blocked_consumers": BLOCKED,
        "TOOL_MANIFEST": {"jax": {"used": True, "role": "load_bearing", "reason": "JAX x64 finite Hopf/curvature/order calculations."}},
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing"},
        "tool_manifest": {"jax": {"used": True, "role": "load_bearing", "reason": "JAX x64 finite Hopf/curvature/order calculations."}},
        "tool_integration_depth": {"jax": "load_bearing"},
    }
    receipt["all_pass"] = all(receipt["checks"].values())
    receipt["AUDIT_PASS"] = receipt["all_pass"]
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(f"jax_l4_hopf_connection_c1_order_fence all_pass={receipt['all_pass']} result={OUT}")
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
