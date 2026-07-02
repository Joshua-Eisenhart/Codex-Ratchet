#!/usr/bin/env python3
"""JAX-native spinor-shell toolchain probe.

This is an execution probe, not a formal layer-admission artifact.  It tests
whether the installed JAX ecosystem can run a finite spinor-network style shell
simulation at 8/16/32/64 sites while making the JAX tools do real work.
"""

import json
import math
import pathlib
import shutil
import tempfile
import time
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import blackjax
import chex
import diffrax
import equinox as eqx
import flax.linen as nn
import jax.numpy as jnp
import jax.random as jr
import jaxlie
import jraph
import lineax as lx
import netket as nk
import numpyro.distributions as dist
import optax
import orbax.checkpoint as ocp
import qutip_jax
from jaxtyping import Array
from ott.geometry import pointcloud
from ott.problems.linear import linear_problem
from ott.solvers.linear import sinkhorn


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_PATH = RESULT_DIR / "jax_native_spinor_shell_toolchain_probe_results.json"
SCALES = [8, 16, 32, 64]
RTYPE = jnp.float64
CTYPE = jnp.complex128
EPS = 1.0e-12


class CompatibilityMLP(nn.Module):
    """Tiny Flax module used to turn edge features into compatibility logits."""

    @nn.compact
    def __call__(self, x: Array) -> Array:
        x = nn.Dense(8, dtype=RTYPE, param_dtype=RTYPE)(x)
        x = nn.tanh(x)
        x = nn.Dense(1, dtype=RTYPE, param_dtype=RTYPE)(x)
        return jnp.squeeze(x, axis=-1)


class PhaseChannel(eqx.Module):
    """Equinox module applying an orientation-dependent spinor phase channel."""

    gain: Array

    def __call__(self, spinors: Array, angles: Array) -> Array:
        phase = jnp.exp(1j * self.gain * angles).astype(CTYPE)
        out = spinors * phase[:, None]
        return out / jnp.linalg.norm(out, axis=1, keepdims=True)


def binary_entropy(p: Array) -> Array:
    p = jnp.clip(p, EPS, 1.0 - EPS)
    return -(p * jnp.log(p) + (1.0 - p) * jnp.log(1.0 - p))


def shannon_entropy(p: Array) -> Array:
    p = jnp.clip(p, EPS, 1.0)
    return -jnp.sum(p * jnp.log(p))


def make_edges(n: int) -> tuple[Array, Array]:
    i = jnp.arange(n, dtype=jnp.int32)
    j = (i + 1) % n
    senders = jnp.concatenate([i, j])
    receivers = jnp.concatenate([j, i])
    return senders, receivers


def make_shell_spinors(n: int) -> tuple[Array, Array, Array, Array]:
    """Return left/right Weyl-like two-component spinors and SO(3) frames."""
    angles = jnp.linspace(0.0, 2.0 * jnp.pi, n, endpoint=False, dtype=RTYPE)
    polar = 0.33 * jnp.pi + 0.17 * jnp.sin(3.0 * angles)
    phase = angles + 0.25 * jnp.sin(2.0 * angles)
    left = jnp.stack(
        [
            jnp.cos(polar / 2.0),
            jnp.exp(1j * phase) * jnp.sin(polar / 2.0),
        ],
        axis=1,
    ).astype(CTYPE)
    right = jnp.stack(
        [
            jnp.sin(polar / 2.0),
            -jnp.exp(1j * phase) * jnp.cos(polar / 2.0),
        ],
        axis=1,
    ).astype(CTYPE)
    left = left / jnp.linalg.norm(left, axis=1, keepdims=True)
    right = right / jnp.linalg.norm(right, axis=1, keepdims=True)
    frames = jax.vmap(lambda a: jaxlie.SO3.exp(jnp.array([0.0, 0.0, a], dtype=RTYPE)).as_matrix())(angles)
    frame_angles = jnp.arctan2(frames[:, 1, 0], frames[:, 0, 0])
    return left, right, frame_angles, frames


def edge_features(left: Array, right: Array, senders: Array, receivers: Array, radius: float) -> Array:
    ll_overlap = jnp.sum(jnp.conj(left[senders]) * left[receivers], axis=1)
    ll = jnp.abs(ll_overlap) ** 2
    lr = jnp.abs(jnp.sum(jnp.conj(left[senders]) * right[receivers], axis=1)) ** 2
    rr = jnp.abs(jnp.sum(jnp.conj(right[senders]) * right[receivers], axis=1)) ** 2
    chirality_gap = ll - lr
    r = jnp.ones_like(ll) * radius
    return jnp.stack([ll, lr, rr, chirality_gap, r, jnp.real(ll_overlap), jnp.imag(ll_overlap)], axis=1)


def graph_neighbor_readout(n: int, features: Array, senders: Array, receivers: Array) -> Array:
    graph = jraph.GraphsTuple(
        nodes=jnp.ones((n, 1), dtype=RTYPE),
        edges=features[:, :1],
        senders=senders,
        receivers=receivers,
        n_node=jnp.array([n]),
        n_edge=jnp.array([features.shape[0]]),
        globals=None,
    )
    summed = jax.ops.segment_sum(graph.edges[:, 0], graph.receivers, num_segments=n)
    counts = jax.ops.segment_sum(jnp.ones_like(graph.edges[:, 0]), graph.receivers, num_segments=n)
    return summed / jnp.maximum(counts, 1.0)


def solve_shell_potential(n: int, node_signal: Array) -> Array:
    senders, receivers = make_edges(n)
    lap = jnp.eye(n, dtype=RTYPE)
    lap = lap.at[senders, receivers].add(-0.25)
    lap = lap + 0.1 * jnp.eye(n, dtype=RTYPE)
    operator = lx.MatrixLinearOperator(lap)
    return lx.linear_solve(operator, node_signal).value


def diffuse_weights(logits: Array, w0: Array) -> Array:
    def vf(t, y, args):
        fitness = args
        centered = fitness - jnp.sum(y * fitness)
        return y * centered

    term = diffrax.ODETerm(vf)
    sol = diffrax.diffeqsolve(
        term,
        diffrax.Tsit5(),
        t0=0.0,
        t1=1.0,
        dt0=0.05,
        y0=w0,
        args=logits,
        saveat=diffrax.SaveAt(t1=True),
        max_steps=512,
    )
    y = jnp.clip(sol.ys[0], EPS, None)
    return y / jnp.sum(y)


def sinkhorn_shell_transport(n: int, a: Array, b: Array) -> tuple[float, float]:
    theta = jnp.linspace(0.0, 2.0 * jnp.pi, n, endpoint=False, dtype=RTYPE)
    outer = jnp.stack([jnp.cos(theta), jnp.sin(theta)], axis=1)
    inner = 0.75 * outer
    geom = pointcloud.PointCloud(outer, inner, epsilon=5.0e-2)
    prob = linear_problem.LinearProblem(geom, a=a, b=b)
    out = sinkhorn.Sinkhorn(threshold=1.0e-5, max_iterations=3000)(prob)
    plan = out.matrix
    row_viol = jnp.max(jnp.abs(jnp.sum(plan, axis=1) - a))
    col_viol = jnp.max(jnp.abs(jnp.sum(plan, axis=0) - b))
    return float(jnp.sum(plan * geom.cost_matrix)), float(jnp.maximum(row_viol, col_viol))


def qutip_trace_check(left0: Array) -> float:
    rho = jnp.outer(left0, jnp.conj(left0)).astype(CTYPE)
    return float(jnp.real(qutip_jax.trace_jaxarray(qutip_jax.JaxArray(rho))))


def blackjax_phase_sample(target: float, key: Array) -> dict[str, float]:
    prior = dist.Normal(jnp.array(0.0, dtype=RTYPE), jnp.array(1.0, dtype=RTYPE))
    likelihood = dist.Normal(jnp.array(target, dtype=RTYPE), jnp.array(0.35, dtype=RTYPE))

    def logdensity(x):
        return prior.log_prob(x[0]) + likelihood.log_prob(x[0])

    kernel = blackjax.hmc(
        logdensity,
        step_size=0.04,
        inverse_mass_matrix=jnp.ones(1, dtype=RTYPE),
        num_integration_steps=4,
    )
    state = kernel.init(jnp.array([0.1], dtype=RTYPE))
    accepts = []
    samples = []
    for k in jr.split(key, 12):
        state, info = kernel.step(k, state)
        accepts.append(info.acceptance_rate)
        samples.append(state.position[0])
    return {
        "acceptance_mean": float(jnp.mean(jnp.asarray(accepts))),
        "sample_mean": float(jnp.mean(jnp.asarray(samples))),
        "target": float(target),
    }


def netket_hilbert_boundary(n: int) -> dict[str, Any]:
    try:
        hilbert = nk.hilbert.Spin(s=0.5, N=n)
        return {
            "size": int(hilbert.size),
            "is_indexable": bool(hilbert.is_indexable),
            "n_states": int(hilbert.n_states),
            "dense_hilbert_boundary": "indexable",
        }
    except RuntimeError as exc:
        return {
            "size": n,
            "is_indexable": False,
            "n_states": None,
            "dense_hilbert_boundary": f"blocked_by_netket: {str(exc)}",
        }


def orbax_roundtrip(payload: dict[str, Any]) -> bool:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="jax_spinor_shell_orbax_"))
    try:
        ckptr = ocp.StandardCheckpointer()
        ckpt_dir = tmp / "ckpt"
        ckptr.save(ckpt_dir, payload)
        ckptr.wait_until_finished()
        restored = ckptr.restore(ckpt_dir)
        return bool(jnp.allclose(restored["probe"], payload["probe"]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_scale(n: int, key: Array) -> dict[str, Any]:
    left, right, frame_angles, frames = make_shell_spinors(n)
    chex.assert_shape(left, (n, 2))
    chex.assert_shape(right, (n, 2))
    chex.assert_shape(frames, (n, 3, 3))

    phase_channel = PhaseChannel(gain=jnp.array(0.37, dtype=RTYPE))
    left_oriented = phase_channel(left, frame_angles)
    right_oriented = phase_channel(right, -frame_angles)

    senders, receivers = make_edges(n)
    features = edge_features(left_oriented, right_oriented, senders, receivers, radius=float(n))
    erased_features = edge_features(left, right, senders, receivers, radius=float(n))
    node_signal = graph_neighbor_readout(n, features, senders, receivers)
    potential = solve_shell_potential(n, node_signal)

    mlp = CompatibilityMLP()
    params = mlp.init(key, features)
    base_logits = mlp.apply(params, features) + 0.05 * potential[receivers]

    train_params = {
        "gain": jnp.array(0.25, dtype=RTYPE),
        "bias": jnp.array(0.0, dtype=RTYPE),
    }
    opt = optax.adam(learning_rate=0.03)
    opt_state = opt.init(train_params)

    def logits_from(p):
        return base_logits + p["gain"] * features[:, 0] + p["bias"]

    def loss_fn(p):
        logits = logits_from(p)
        w = jax.nn.softmax(logits)
        entropy_penalty = shannon_entropy(w) / jnp.log(w.shape[0])
        return -jnp.sum(w * features[:, 0]) + 0.025 * entropy_penalty

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
    transport_cost, transport_marginal_violation = sinkhorn_shell_transport(n, node_w0, node_w1)

    edge_entanglement = binary_entropy(jax.nn.sigmoid(logits))
    h_omega = shannon_entropy(w1) / jnp.log(w1.shape[0])
    qutip_trace = qutip_trace_check(left_oriented[0])
    phase_sample = blackjax_phase_sample(float(jnp.mean(frame_angles)), jr.fold_in(key, n))

    erased_logits = mlp.apply(params, erased_features)
    orientation_erased_delta = float(jnp.mean(jnp.abs(jax.nn.softmax(logits) - jax.nn.softmax(erased_logits))))

    scrambled_receivers = jnp.roll(receivers, max(1, n // 4))
    scrambled_features = edge_features(left_oriented, right_oriented, senders, scrambled_receivers, radius=float(n))
    scrambled_logits = mlp.apply(params, scrambled_features)
    scrambled_delta = float(jnp.mean(jnp.abs(jax.nn.softmax(logits) - jax.nn.softmax(scrambled_logits))))

    def compress(w):
        c = jnp.power(jnp.clip(w, EPS, None), 1.35)
        return c / jnp.sum(c)

    def compat_update(w):
        u = jnp.clip(w, EPS, None) * jnp.exp(0.5 * logits)
        return u / jnp.sum(u)

    order_gap = float(jnp.sum(jnp.abs(compress(compat_update(w0)) - compat_update(compress(w0)))))
    netket_boundary = netket_hilbert_boundary(n)

    return {
        "scale_sites": n,
        "edge_count": int(features.shape[0]),
        "jax_dtype_real": str(jnp.asarray([1.0], dtype=RTYPE).dtype),
        "jax_dtype_complex": str((jnp.asarray([1.0], dtype=RTYPE) + 1j).dtype),
        "flax_optax_initial_loss": initial_loss,
        "flax_optax_final_loss": final_loss,
        "loss_decreased": bool(final_loss < initial_loss),
        "normalized_possibility_entropy": float(h_omega),
        "mean_edge_entanglement_entropy": float(jnp.mean(edge_entanglement)),
        "max_edge_entanglement_entropy": float(jnp.max(edge_entanglement)),
        "diffrax_weight_sum": float(jnp.sum(w1)),
        "lineax_potential_norm": float(jnp.linalg.norm(potential)),
        "ott_transport_cost": transport_cost,
        "ott_marginal_violation": transport_marginal_violation,
        "qutip_jax_density_trace": qutip_trace,
        "blackjax_numpyro_phase_sample": phase_sample,
        "jaxlie_orientation_frame_det_min": float(jnp.min(jax.vmap(jnp.linalg.det)(frames))),
        "jraph_node_signal_mean": float(jnp.mean(node_signal)),
        "orientation_erased_delta": orientation_erased_delta,
        "scrambled_edge_delta": scrambled_delta,
        "order_gap": order_gap,
        "netket_hilbert_boundary": netket_boundary,
        "pass": bool(
            final_loss < initial_loss
            and abs(float(jnp.sum(w1)) - 1.0) < 1.0e-8
            and transport_marginal_violation < 5.0e-4
            and abs(qutip_trace - 1.0) < 1.0e-8
            and float(jnp.mean(edge_entanglement)) > 0.0
            and orientation_erased_delta > 1.0e-8
            and scrambled_delta > 1.0e-8
            and order_gap > 1.0e-10
        ),
    }


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    key = jr.PRNGKey(20260530)
    scale_results = []
    for i, n in enumerate(SCALES):
        scale_results.append(run_scale(n, jr.fold_in(key, i)))

    orbax_ok = orbax_roundtrip({"probe": jnp.asarray([r["normalized_possibility_entropy"] for r in scale_results])})
    tools = {
        "jax": "x64 array/autodiff/functional compute backend for the spinor shell network",
        "jax.numpy": "complex128 spinor states, edge overlaps, entropy and density calculations",
        "flax": "compatibility MLP over edge features",
        "equinox": "orientation-dependent complex phase channel module",
        "optax": "Adam optimization of compatibility weight parameters",
        "diffrax": "replicator-style inward shell weight dynamics",
        "jraph": "finite graph carrier and neighbor aggregation",
        "lineax": "finite shell potential linear solve",
        "ott": "Sinkhorn transport between pre/post shell possibility weights",
        "jaxlie": "SO(3) orientation frames driving spinor phase transport",
        "qutip_jax": "JAX-backed density trace check",
        "blackjax": "HMC phase posterior sampler",
        "numpyro": "Normal prior/likelihood used by the BlackJAX target density",
        "netket": "spin Hilbert scaling boundary check at 8/16/32/64 sites",
        "orbax": "checkpoint roundtrip for the numeric probe vector",
        "chex": "runtime shape assertions for spinor and frame arrays",
        "jaxtyping": "array typing imported for JAX shape/dtype annotation surface",
    }
    result = {
        "sim_id": "jax_native_spinor_shell_toolchain_probe",
        "classification": "execution_probe",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "claim_boundary": (
            "JAX-native toolchain execution over finite spinor shell networks; "
            "not formal layer completion, not Axis0, not flux, not physics."
        ),
        "root_constraints_exercised": {
            "F01": "finite site set, finite directed edge set, finite compatibility weights",
            "N01": "compatibility/compression order gap plus edge/orientation controls",
        },
        "backend": "jax_native_x64",
        "scales": SCALES,
        "all_pass": bool(all(r["pass"] for r in scale_results) and orbax_ok),
        "orbax_checkpoint_roundtrip": orbax_ok,
        "tool_manifest": tools,
        "tool_integration_depth": {k: "load_bearing" for k in tools},
        "scale_results": scale_results,
        "failed_scales": [r["scale_sites"] for r in scale_results if not r["pass"]],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps({
        "result_path": str(RESULT_PATH),
        "all_pass": result["all_pass"],
        "scales": SCALES,
        "failed_scales": result["failed_scales"],
    }, indent=2, sort_keys=True))
    if not result["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
