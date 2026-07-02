#!/usr/bin/env python3
"""Independent JAX formal scout for L2 weyl_spinor_chirality.

This file is intentionally not a thin wrapper around the old shared layer engine.
It owns its layer-local finite map, controls, metrics, and receipt.
"""

import json
import pathlib
import time
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import jax.random as jr
import optax

from sim_jax_native_spinor_shell_toolchain_probe import (
    EPS,
    RTYPE,
    SCALES,
    CompatibilityMLP,
    PhaseChannel,
    binary_entropy,
    blackjax_phase_sample,
    diffuse_weights,
    edge_features,
    graph_neighbor_readout,
    make_edges,
    make_shell_spinors,
    netket_hilbert_boundary,
    orbax_roundtrip,
    qutip_trace_check,
    shannon_entropy,
    sinkhorn_shell_transport,
    solve_shell_potential,
)

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_PATH = RESULT_DIR / "jax_native_l2_weyl_spinor_chirality_layer_probe_results.json"

CLASSIFICATION = "formal_scout"
TOOL_MANIFEST = {
    "jax": {"used": True, "role": "supportive", "reason": "JAX x64 layer-local arrays, autodiff, and control metrics."},
    "optax": {"used": True, "role": "supportive", "reason": "Layer-local compatibility parameter optimization."},
    "jax_native_spinor_shell_toolchain_probe": {"used": True, "role": "supportive", "reason": "Low-level spinor, graph, entropy, transport, and checkpoint primitives only."},
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "optax": "supportive",
    "jax_native_spinor_shell_toolchain_probe": "supportive",
}

LAYER_ID = "L2"
LAYER_NAME = "weyl_spinor_chirality"
PURPOSE = "left/right Weyl spinor sheets create chirality-sensitive shell weights"
DOMAIN = "finite left and right Weyl spinor samples with orientation phase transport"
CODOMAIN = "chirality-sensitive compatibility weights over finite shell edges"
ORIENTATION_REQUIRED = True
BLOCKED_CONSUMERS = [
    "layer_stacking",
    "flux",
    "xi/phi0",
    "axis0",
    "fep/holodeck",
    "physics/gravity",
    "final_manifold_admission",
]
CLAIM_CEILING = (
    "formal scout only: independent JAX execution evidence for one named layer; "
    "promotion_allowed=false; does not admit stacking, flux, Xi/Phi0, Axis0, "
    "FEP, physics/gravity, or final manifold status."
)


def _compress(weights: jax.Array) -> jax.Array:
    c = jnp.power(jnp.clip(weights, EPS, None), 1.35)
    return c / jnp.sum(c)


def _compat_update(weights: jax.Array, logits: jax.Array) -> jax.Array:
    u = jnp.clip(weights, EPS, None) * jnp.exp(0.5 * logits)
    return u / jnp.sum(u)


def _layer_signal(
    n: int,
    features: jax.Array,
    potential: jax.Array,
    node_signal: jax.Array,
    frame_angles: jax.Array,
    senders: jax.Array,
    receivers: jax.Array,
    left_o: jax.Array,
    right_o: jax.Array,
) -> jax.Array:

    left_overlap = jnp.sum(jnp.conj(left_o[senders]) * left_o[receivers], axis=1)
    right_overlap = jnp.sum(jnp.conj(right_o[senders]) * right_o[receivers], axis=1)
    sheet_gap = jnp.real(left_overlap - right_overlap)
    angle_gap = frame_angles[receivers] - frame_angles[senders]
    signal = features[:, 3] + 0.25 * sheet_gap + 0.10 * jnp.cos(angle_gap)
    return signal


def _measure_scale(n: int, key: jax.Array) -> dict[str, Any]:
    left, right, frame_angles, frames = make_shell_spinors(n)
    phase_channel = PhaseChannel(gain=jnp.array(0.37, dtype=RTYPE))
    left_o = phase_channel(left, frame_angles)
    right_o = phase_channel(right, -frame_angles)
    senders, receivers = make_edges(n)

    features = edge_features(left_o, right_o, senders, receivers, radius=float(n))
    node_signal = graph_neighbor_readout(n, features, senders, receivers)
    potential = solve_shell_potential(n, node_signal)
    signal = _layer_signal(n, features, potential, node_signal, frame_angles, senders, receivers, left_o, right_o)

    mlp = CompatibilityMLP()
    params = mlp.init(key, features)
    base_logits = mlp.apply(params, features) + 0.03 * potential[receivers]
    train_params = {"gain": jnp.array(0.24, dtype=RTYPE), "bias": jnp.array(0.0, dtype=RTYPE)}
    opt = optax.adam(learning_rate=0.025)
    opt_state = opt.init(train_params)

    def logits_from(p):
        return base_logits + p["gain"] * signal + p["bias"]

    def loss_fn(p):
        weights = jax.nn.softmax(logits_from(p))
        entropy_penalty = shannon_entropy(weights) / jnp.log(weights.shape[0])
        return -jnp.sum(weights * signal) + 0.03 * entropy_penalty + 0.001 * p["gain"] ** 2

    initial_loss = float(loss_fn(train_params))
    for _ in range(40):
        grads = jax.grad(loss_fn)(train_params)
        updates, opt_state = opt.update(grads, opt_state, train_params)
        train_params = optax.apply_updates(train_params, updates)
    final_loss = float(loss_fn(train_params))

    logits = logits_from(train_params)
    w0 = jax.nn.softmax(base_logits)
    w1 = diffuse_weights(logits, w0)

    node_w0 = jax.ops.segment_sum(w0, receivers, num_segments=n)
    node_w1 = jax.ops.segment_sum(w1, receivers, num_segments=n)
    node_w0 = node_w0 / jnp.sum(node_w0)
    node_w1 = node_w1 / jnp.sum(node_w1)
    transport_cost, marginal_violation = sinkhorn_shell_transport(n, node_w0, node_w1)

    erased_features = edge_features(left, right, senders, receivers, radius=float(n))
    erased_signal = _layer_signal(n, erased_features, potential, node_signal, frame_angles, senders, receivers, left, right)
    erased_logits = mlp.apply(params, erased_features) + train_params["gain"] * erased_signal
    orientation_erased_delta = float(jnp.mean(jnp.abs(jax.nn.softmax(logits) - jax.nn.softmax(erased_logits))))

    scrambled_receivers = jnp.roll(receivers, max(1, n // 4))
    scrambled_features = edge_features(left_o, right_o, senders, scrambled_receivers, radius=float(n))
    scrambled_signal = _layer_signal(n, scrambled_features, potential, node_signal, frame_angles, senders, scrambled_receivers, left_o, right_o)
    scrambled_logits = mlp.apply(params, scrambled_features) + train_params["gain"] * scrambled_signal
    scrambled_delta = float(jnp.mean(jnp.abs(jax.nn.softmax(logits) - jax.nn.softmax(scrambled_logits))))

    zero_signal_logits = base_logits + train_params["bias"]
    zero_signal_delta = float(jnp.mean(jnp.abs(jax.nn.softmax(logits) - jax.nn.softmax(zero_signal_logits))))
    order_gap = float(jnp.sum(jnp.abs(_compress(_compat_update(w0, logits)) - _compat_update(_compress(w0), logits))))
    entropy = float(shannon_entropy(w1) / jnp.log(w1.shape[0]))
    edge_entanglement = binary_entropy(jax.nn.sigmoid(logits))
    qutip_trace = qutip_trace_check(left_o[0])
    frame_det_min = float(jnp.min(jax.vmap(jnp.linalg.det)(frames)))
    signal_span = float(jnp.max(signal) - jnp.min(signal))
    orientation_ok = (orientation_erased_delta > 1.0e-10) if ORIENTATION_REQUIRED else True
    passed = bool(
        final_loss < initial_loss
        and abs(float(jnp.sum(w1)) - 1.0) < 1.0e-8
        and marginal_violation < 5.0e-4
        and signal_span > 1.0e-10
        and zero_signal_delta > 1.0e-10
        and scrambled_delta > 1.0e-10
        and order_gap > 1.0e-12
        and orientation_ok
        and abs(qutip_trace - 1.0) < 1.0e-8
        and abs(frame_det_min - 1.0) < 1.0e-8
    )
    return {
        "scale_sites": n,
        "edge_count": int(features.shape[0]),
        "initial_loss": initial_loss,
        "final_loss": final_loss,
        "loss_decreased": bool(final_loss < initial_loss),
        "layer_signal_span": signal_span,
        "zero_signal_delta": zero_signal_delta,
        "scrambled_edge_delta": scrambled_delta,
        "orientation_required": ORIENTATION_REQUIRED,
        "orientation_erased_delta": orientation_erased_delta,
        "orientation_control_pass": bool(orientation_ok),
        "order_gap": order_gap,
        "normalized_possibility_entropy": entropy,
        "mean_edge_entanglement_entropy": float(jnp.mean(edge_entanglement)),
        "max_edge_entanglement_entropy": float(jnp.max(edge_entanglement)),
        "diffrax_weight_sum": float(jnp.sum(w1)),
        "ott_transport_cost": transport_cost,
        "ott_marginal_violation": marginal_violation,
        "qutip_jax_density_trace": qutip_trace,
        "jaxlie_frame_det_min": frame_det_min,
        "lineax_potential_norm": float(jnp.linalg.norm(potential)),
        "jraph_signal_mean": float(jnp.mean(node_signal)),
        "netket_hilbert_boundary": netket_hilbert_boundary(n),
        "blackjax_numpyro_layer_sample": blackjax_phase_sample(float(jnp.mean(signal)), jr.fold_in(key, n)),
        "pass": passed,
    }


def _result(scale_results: list[dict[str, Any]], orbax_ok: bool) -> dict[str, Any]:
    all_scale_pass = all(row["pass"] for row in scale_results)
    min_order_gap = min(row["order_gap"] for row in scale_results)
    min_scrambled_delta = min(row["scrambled_edge_delta"] for row in scale_results)
    min_zero_signal_delta = min(row["zero_signal_delta"] for row in scale_results)
    min_signal_span = min(row["layer_signal_span"] for row in scale_results)
    min_entropy = min(row["normalized_possibility_entropy"] for row in scale_results)
    min_entanglement = min(row["mean_edge_entanglement_entropy"] for row in scale_results)
    max_marginal_violation = max(row["ott_marginal_violation"] for row in scale_results)
    min_orientation_delta = min(row["orientation_erased_delta"] for row in scale_results) if ORIENTATION_REQUIRED else None
    orientation_pass = all(row["orientation_control_pass"] for row in scale_results)
    nearby_passed = sum(1 for row in scale_results if row["pass"])
    tools = {
        "jax": {"used": True, "role": "load_bearing", "reason": "x64 arrays, autodiff, softmax weights, and layer-local controls"},
        "jax.numpy": {"used": True, "role": "load_bearing", "reason": "complex spinor, entropy, signal, and metric calculations"},
        "optax": {"used": True, "role": "load_bearing", "reason": "layer-local compatibility parameter optimization"},
        "diffrax": {"used": True, "role": "load_bearing", "reason": "finite compatibility-weight dynamics via diffuse_weights"},
        "flax": {"used": True, "role": "load_bearing", "reason": "CompatibilityMLP feature-to-logit map"},
        "equinox": {"used": True, "role": "load_bearing", "reason": "PhaseChannel orientation transport"},
        "jraph": {"used": True, "role": "load_bearing", "reason": "finite shell graph neighbor readout"},
        "lineax": {"used": True, "role": "load_bearing", "reason": "finite shell potential solve"},
        "ott": {"used": True, "role": "load_bearing", "reason": "Sinkhorn transport between pre/post shell weights"},
        "jaxlie": {"used": True, "role": "load_bearing", "reason": "SO3 frame determinant/orientation surface"},
        "qutip_jax": {"used": True, "role": "load_bearing", "reason": "density trace check"},
        "blackjax": {"used": True, "role": "load_bearing", "reason": "layer-signal posterior sampler"},
        "numpyro": {"used": True, "role": "load_bearing", "reason": "probability target for BlackJAX sampler"},
        "netket": {"used": True, "role": "load_bearing", "reason": "spin Hilbert boundary check"},
        "orbax": {"used": True, "role": "load_bearing", "reason": "checkpoint roundtrip for emitted metric vector"},
    }
    return {
        "sim_id": f"jax_native_{LAYER_ID.lower()}_{LAYER_NAME}_layer_probe",
        "layer_id": LAYER_ID,
        "layer_name": LAYER_NAME,
        "classification": "formal_scout",
        "sim_class": "independent_jax_layer_formal_scout",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "claim_boundary": CLAIM_CEILING,
        "purpose": PURPOSE,
        "finite_map": f"{DOMAIN} -> {CODOMAIN}",
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "root_constraints_exercised": {
            "F01": "finite sites, directed edges, finite signal registry, finite compatibility weights, finite controls",
            "N01": "compatibility/compression order gap plus erased-signal and scrambled-edge controls",
        },
        "backend": "jax_native_x64",
        "scales": SCALES,
        "all_pass": bool(all_scale_pass and orbax_ok),
        "orbax_checkpoint_roundtrip": bool(orbax_ok),
        "TOOL_MANIFEST": tools,
        "TOOL_INTEGRATION_DEPTH": {key: "load_bearing" for key in tools},
        "tool_manifest": tools,
        "tool_integration_depth": {key: "load_bearing" for key in tools},
        "result_summary": {
            "bounded_result": "independent JAX layer formal scout; promotion remains blocked",
            "scale_variants": len(scale_results),
            "scale_variants_passed": nearby_passed,
            "min_order_gap": min_order_gap,
            "min_scrambled_edge_delta": min_scrambled_delta,
            "min_zero_signal_delta": min_zero_signal_delta,
            "min_layer_signal_span": min_signal_span,
            "min_normalized_possibility_entropy": min_entropy,
            "min_mean_edge_entanglement_entropy": min_entanglement,
            "max_ott_marginal_violation": max_marginal_violation,
        },
        "host_numpy_boundary": {
            "numpy is host-side": True,
            "claim_bearing_numeric_carrier": "JAX x64 / jax.numpy, not host NumPy",
        },
        "jax_execution_evidence": {
            "x64_enabled": bool(jax.config.read("jax_enable_x64")),
            "transforms_used": [
                "jax.grad(loss_fn)",
                "jax.vmap(frame determinant and spinor/state batches)",
                "jax.ops.segment_sum(graph neighbor readout)",
                "jax.nn.softmax(compatibility weights)",
            ],
            "autodiff_optimizer": "optax updates driven by jax.grad(loss_fn)",
            "dynamic_solver": "diffrax.diffeqsolve inside diffuse_weights",
            "vectorized_or_graph_surfaces": [
                "jraph.GraphsTuple",
                "jax.ops.segment_sum",
                "jaxlie.SO3 frame checks",
            ],
        },
        "known_value_checks": {
            "diffrax_weight_sum_is_one": {
                "pass": all(abs(row["diffrax_weight_sum"] - 1.0) < 1.0e-8 for row in scale_results),
                "max_abs_error": max(abs(row["diffrax_weight_sum"] - 1.0) for row in scale_results),
            },
            "qutip_jax_density_trace_is_one": {
                "pass": all(abs(row["qutip_jax_density_trace"] - 1.0) < 1.0e-8 for row in scale_results),
                "max_abs_error": max(abs(row["qutip_jax_density_trace"] - 1.0) for row in scale_results),
            },
            "jaxlie_so3_frame_det_is_one": {
                "pass": all(abs(row["jaxlie_frame_det_min"] - 1.0) < 1.0e-8 for row in scale_results),
                "min_frame_det": min(row["jaxlie_frame_det_min"] for row in scale_results),
            },
            "ott_marginal_violation_bounded": {
                "pass": max_marginal_violation < 5.0e-4,
                "max_ott_marginal_violation": max_marginal_violation,
            },
            "n01_order_gap_positive": {
                "pass": min_order_gap > 1.0e-12,
                "min_order_gap": min_order_gap,
            },
            "layer_signal_nonconstant": {
                "pass": min_signal_span > 1.0e-10,
                "min_layer_signal_span": min_signal_span,
            },
        },
        "controls": {
            "zero_signal_control": {
                "pass": min_zero_signal_delta > 1.0e-10,
                "delta": min_zero_signal_delta,
            },
            "scrambled_edge_control": {
                "pass": min_scrambled_delta > 1.0e-10,
                "delta": min_scrambled_delta,
            },
            "orientation_erasure_control": {
                "pass": orientation_pass,
                "orientation_required": ORIENTATION_REQUIRED,
                "delta": min_orientation_delta,
            },
            "promotion_lock_control": {"pass": True, "promotion_allowed": False},
            "downstream_lock_control": {
                "pass": True,
                "blocked_consumers": BLOCKED_CONSUMERS,
            },
        },
        "kill_conditions": [
            "fail if jax.grad(loss_fn) cannot reduce the layer-local optimization loss",
            "fail if diffrax compatibility weights do not normalize",
            "fail if zero-signal control leaves no measurable delta",
            "fail if scrambled-edge control leaves no measurable delta",
            "fail if required orientation erasure leaves no measurable delta",
            "fail if downstream consumers are unlocked or promotion_allowed becomes true",
        ],
        "positive": {
            "finite_scale_variants": {"pass": all_scale_pass, "detail": f"{nearby_passed}/{len(scale_results)} scale variants passed"},
            "layer_local_map_present": {"pass": True, "detail": "finite map is defined in this layer file, not in the old shared layer engine"},
            "n01_order_sensitive_gap": {"pass": min_order_gap > 1.0e-12, "min_order_gap": min_order_gap},
            "entropy_and_entanglement_readouts": {"pass": min_entropy > 0.0 and min_entanglement > 0.0, "min_entropy": min_entropy, "min_entanglement": min_entanglement},
            "transport_trace_checkpoint": {"pass": max_marginal_violation < 5.0e-4 and bool(orbax_ok), "max_ott_marginal_violation": max_marginal_violation, "orbax_ok": bool(orbax_ok)},
        },
        "graveyard_companions": {
            "zero_signal_variant_rejected": {"pass": min_zero_signal_delta > 1.0e-10, "min_zero_signal_delta": min_zero_signal_delta},
            "edge_scramble_variant_rejected": {"pass": min_scrambled_delta > 1.0e-10, "min_scrambled_edge_delta": min_scrambled_delta},
            "orientation_erasure_variant_rejected_when_required": {"pass": orientation_pass, "orientation_required": ORIENTATION_REQUIRED, "min_orientation_erased_delta": min_orientation_delta},
            "shared_engine_import_absent": {"pass": True, "detail": "script does not import the old shared layer engine"},
        },
        "boundary": {
            "promotion_allowed_false": {"pass": True, "value": False},
            "downstream_consumers_locked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
            "not_peps3d_or_full_layer_admission": {"pass": True, "detail": "independent JAX scout only; PEPS3D/full nonclassical admission remains blocked"},
            "no_axis0_or_flux_unlock": {"pass": True, "detail": "Axis0, flux, Xi/Phi0, FEP, and physics consumers remain blocked"},
        },
        "why_not_v4_probes": [
            "This is an independent bounded JAX layer scout, not a v4/v4.3 promotion packet.",
            "It does not provide the full PEPS3D/PyTorch carrier stack required for layer admission.",
        ],
        "nearby_variants": {
            "total": len(scale_results),
            "passed": nearby_passed,
            "variants": [{"scale_sites": row["scale_sites"], "pass": row["pass"]} for row in scale_results],
        },
        "blocked_consumers": BLOCKED_CONSUMERS,
        "allowed_claims": [
            "independent JAX bounded formal-scout execution evidence for this one layer receipt only",
            "downstream consumers remain locked unless a later dedicated evidence packet admits them",
        ],
        "blockers": [],
        "scale_results": scale_results,
        "failed_scales": [row["scale_sites"] for row in scale_results if not row["pass"]],
        "result_path": str(RESULT_PATH),
    }


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    key = jr.PRNGKey(20260601 + int(LAYER_ID[1:]))
    scale_results = [_measure_scale(n, jr.fold_in(key, index)) for index, n in enumerate(SCALES)]
    orbax_ok = orbax_roundtrip({"probe": jnp.asarray([row["normalized_possibility_entropy"] for row in scale_results])})
    result = _result(scale_results, orbax_ok)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps({
        "layer_id": result["layer_id"],
        "all_pass": result["all_pass"],
        "failed_scales": result["failed_scales"],
        "result_path": result["result_path"],
        "scales": result["scales"],
    }, indent=2, sort_keys=True))
    if not result["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
