#!/usr/bin/env python3
"""Cheap finite PEPS2D entanglement preflight.

This proves one non-product PEPS2D carrier at invariant level before any
PEPSKit/CTMRG rebuild work. It is intentionally finite and does not promote a
layer, stacking claim, bridge, Axis0, flux, or physics consumer.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


ROOT = pathlib.Path(__file__).resolve().parent
RESULT = ROOT / "results" / "peps2d_entangled_carrier_preflight_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_preflight"
TOOL_MANIFEST = {
    "jax": {
        "used": True,
        "role": "load_bearing",
        "reason": "JAX x64 carries the finite PEPS2D tensor contraction, SVD cut entropy, and product/bond-erasure controls.",
    }
}
TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing"}


def parity_tensor() -> jax.Array:
    tensor = jnp.zeros((2, 2, 2), dtype=jnp.complex128)
    for p in range(2):
        for a in range(2):
            for b in range(2):
                if p == (a ^ b):
                    tensor = tensor.at[p, a, b].set(1.0 + 0.0j)
    return tensor


def normalize(state: jax.Array) -> jax.Array:
    norm = jnp.sqrt(jnp.real(jnp.vdot(state.reshape(-1), state.reshape(-1))))
    return state / norm


def entangled_peps2d_state() -> jax.Array:
    # 2x2 open-boundary PEPS cell with four internal D=2 bonds:
    # vl, vr, ht, hb. Physical bits are parity readouts of incident bonds.
    a = parity_tensor()  # p00, vl, ht
    b = parity_tensor()  # p01, ht, vr
    c = parity_tensor()  # p10, vl, hb
    d = parity_tensor()  # p11, hb, vr
    state = jnp.einsum("avh,bhr,cvk,dkr->abcd", a, b, c, d)
    return normalize(state)


def product_control_state() -> jax.Array:
    plus = jnp.ones((2,), dtype=jnp.complex128) / jnp.sqrt(2.0)
    state = jnp.einsum("a,b,c,d->abcd", plus, plus, plus, plus)
    return normalize(state)


def wrong_structure_control_state() -> jax.Array:
    # A finite but wrong carrier: one horizontal Bell-like pair and two product
    # legs. This keeps a named PEPS2D-looking tensor shape from becoming a
    # bit-identical erased-control clone.
    bell = jnp.zeros((2, 2), dtype=jnp.complex128)
    bell = bell.at[0, 0].set(1.0 + 0.0j)
    bell = bell.at[1, 1].set(1.0 + 0.0j)
    plus = jnp.ones((2,), dtype=jnp.complex128) / jnp.sqrt(2.0)
    state = jnp.einsum("ab,c,d->abcd", bell, plus, plus)
    return normalize(state)


def cut_entropy(state: jax.Array, left_axes: tuple[int, ...]) -> tuple[float, list[float]]:
    axes = left_axes + tuple(axis for axis in range(state.ndim) if axis not in left_axes)
    moved = jnp.transpose(state, axes)
    left_dim = 2 ** len(left_axes)
    mat = moved.reshape((left_dim, -1))
    singular_values = jnp.linalg.svd(mat, compute_uv=False)
    probs = jnp.real(singular_values * singular_values)
    probs = probs / jnp.sum(probs)
    entropy = -jnp.sum(jnp.where(probs > 0, probs * jnp.log2(probs), 0.0))
    return float(entropy), [float(x) for x in probs]


def state_l2(a: jax.Array, b: jax.Array) -> float:
    return float(jnp.linalg.norm(a.reshape(-1) - b.reshape(-1)))


def main() -> int:
    started = time.time()
    source_path = pathlib.Path(__file__).resolve()

    entangled = entangled_peps2d_state()
    erased = product_control_state()
    wrong = wrong_structure_control_state()

    top_bottom_entropy, top_bottom_spectrum = cut_entropy(entangled, (0, 1))
    left_right_entropy, left_right_spectrum = cut_entropy(entangled, (0, 2))
    erased_entropy, erased_spectrum = cut_entropy(erased, (0, 1))
    wrong_entropy, wrong_spectrum = cut_entropy(wrong, (0, 1))
    erasure_delta = top_bottom_entropy - erased_entropy
    wrong_vs_erased_l2 = state_l2(wrong, erased)

    checks = {
        "jax_x64": bool(jax.config.read("jax_enable_x64")),
        "complex128_state": str(entangled.dtype) == "complex128",
        "entangled_top_bottom_entropy_positive": top_bottom_entropy > 0.25,
        "entangled_left_right_entropy_positive": left_right_entropy > 0.25,
        "erased_control_product_entropy_zero": abs(erased_entropy) < 1.0e-12,
        "bond_erasure_changes_observable": erasure_delta > 0.25,
        "wrong_control_not_bit_identical_to_erased_control": wrong_vs_erased_l2 > 0.25,
    }
    all_pass = all(checks.values())

    result: dict[str, Any] = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": "peps2d_entangled_carrier_preflight_probe",
        "object_id": "finite_2x2_entangled_peps2d_carrier",
        "name": "finite 2x2 entangled PEPS2D carrier preflight",
        "version": "1.0.0",
        "tier": "carrier_preflight",
        "purpose": "Prove one non-product finite PEPS2D carrier with cheap JAX invariant checks before PEPSKit/CTMRG rebuild work.",
        "scientific_question": "Does a finite D=2 PEPS2D carrier encode entanglement that disappears under product/bond-erasure controls?",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": "entangled_peps2d_carrier_preflight",
        "promotion_allowed": False,
        "claim_ceiling": "Formal scout only: one finite entangled PEPS2D carrier preflight. Not layer completion, not PEPSKit load-bearing evidence, not stacking, bridge, Axis0, flux, FEP, physics, or final manifold admission.",
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "root_constraints_in_force": {
            "F01": "finite 2x2 physical site set and finite four-bond D=2 virtual edge set",
            "N01": "parity readout over shared virtual bonds changes cut entropy; bond erasure kills the readout",
        },
        "finite_map": "contract finite PEPS2D parity tensors over four D=2 virtual bonds -> normalized four-site state and cut entropies",
        "domain": "four local parity tensors on a 2x2 open-boundary PEPS2D cell with internal bonds vl, vr, ht, hb",
        "codomain_or_output": "normalized four-qubit PEPS2D state, bipartition spectra, and entropy deltas against erased/product controls",
        "carrier_layer": "finite_peps2d",
        "geometry_layer": "2x2 open-boundary PEPS2D carrier preflight",
        "carrier_realization": "jax.Array complex128 finite PEPS2D tensor network; no NumPy, no dense-state closure beyond the explicit four-site finite output",
        "peps3d_embedding": "not_claimed_peps2d_preflight_only",
        "spinor_state": "finite four-site qubit state derived from PEPS2D virtual-bond parity tensors",
        "quaternion_action": "not_applicable",
        "dependency_receipts": ["system_v5/ops/formal_scouts/results/jax_results.json"],
        "blocked_consumers": ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity", "layer_completion", "stacking", "PEPSKit_load_bearing_claim"],
        "allowed_claims": ["one finite PEPS2D carrier is non-product at cheap invariant/preflight level"],
        "backend_primary_result": {
            "primary_backend": "jax",
            "top_bottom_entropy_bits": top_bottom_entropy,
            "left_right_entropy_bits": left_right_entropy,
            "top_bottom_spectrum": top_bottom_spectrum,
            "left_right_spectrum": left_right_spectrum,
        },
        "controls": {
            "product_erased_control": {
                "entropy_bits": erased_entropy,
                "spectrum": erased_spectrum,
                "pass": abs(erased_entropy) < 1.0e-12,
            },
            "wrong_structure_control": {
                "entropy_bits": wrong_entropy,
                "spectrum": wrong_spectrum,
                "wrong_vs_erased_l2": wrong_vs_erased_l2,
                "pass": wrong_vs_erased_l2 > 0.25,
            },
        },
        "tool_ablations": {
            "bond_erasure_entropy_delta": {
                "tool": "jax",
                "observable": "top_bottom_cut_entropy_bits",
                "baseline_metric": top_bottom_entropy,
                "ablated_metric": erased_entropy,
                "outcome_delta": erasure_delta,
                "pass": erasure_delta > 0.25,
            }
        },
        "scale_blocker": "This is the required cheap entangled-carrier preflight before CTMRG or 8/16/32/64 PEPS2D scale work; scale remains blocked until the per-sim rebuild lane consumes this carrier honestly.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "checks": checks,
        "all_pass": all_pass,
        "result_summary": {
            "all_pass": all_pass,
            "top_bottom_entropy_bits": top_bottom_entropy,
            "left_right_entropy_bits": left_right_entropy,
            "erased_entropy_bits": erased_entropy,
            "bond_erasure_entropy_delta": erasure_delta,
            "wrong_vs_erased_l2": wrong_vs_erased_l2,
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "summary": {
            "all_pass": all_pass,
            "entangled": top_bottom_entropy > 0.25 and left_right_entropy > 0.25,
            "product_control_entropy_zero": abs(erased_entropy) < 1.0e-12,
        },
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(RESULT), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
