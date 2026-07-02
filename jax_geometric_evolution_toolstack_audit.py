#!/usr/bin/env python3
"""JAX geometric-evolution tool-stack audit.

Diagnostic only. This is the JAX lane as numerical stress/audit machinery, not a
Julia replacement, not a retired-lane port, and not a layer-admission claim.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import warnings
from functools import cache
from pathlib import Path

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import diffrax
import jaxlie
import optax


RESULT_PATH = Path("jax_geometric_evolution_toolstack_audit_results.json")
EPS = 1e-12


def _float(x) -> float:
    return float(jax.device_get(x))


def _bool(x) -> bool:
    return bool(jax.device_get(x))


def unit(x):
    return x / jnp.maximum(jnp.linalg.norm(x), EPS)


@jax.custom_vjp
def retract_s3(x):
    return unit(x)


def _retract_s3_fwd(x):
    y = unit(x)
    return y, y


def _retract_s3_bwd(y, g):
    tangent = g - jnp.vdot(y, g) * y
    return (tangent,)


retract_s3.defvjp(_retract_s3_fwd, _retract_s3_bwd)


def _blade_mul_sign(a: int, b: int) -> tuple[int, int]:
    swaps = 0
    for i in range(3):
        if (a >> i) & 1:
            swaps += int((b & ((1 << i) - 1)).bit_count())
    return (-1 if swaps % 2 else 1), a ^ b


_GP_OUT = []
_GP_SIGN = []
for i in range(8):
    out_row = []
    sign_row = []
    for j in range(8):
        s, blade = _blade_mul_sign(i, j)
        out_row.append(blade)
        sign_row.append(s)
    _GP_OUT.append(out_row)
    _GP_SIGN.append(sign_row)

GP_OUT = jnp.array(_GP_OUT, dtype=jnp.int32)
GP_SIGN = jnp.array(_GP_SIGN, dtype=jnp.float64)
REVERSE_SIGN = jnp.array([1.0, 1.0, 1.0, -1.0, 1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)


@jax.jit
def clifford_gp(a, b):
    out = jnp.zeros((8,), dtype=jnp.result_type(a, b))
    for i in range(8):
        for j in range(8):
            out = out.at[GP_OUT[i, j]].add(GP_SIGN[i, j] * a[i] * b[j])
    return out


@jax.jit
def clifford_reverse(a):
    return a * REVERSE_SIGN


def custom_clifford_check():
    e1 = jnp.zeros((8,), dtype=jnp.float64).at[1].set(1.0)
    e2 = jnp.zeros((8,), dtype=jnp.float64).at[2].set(1.0)
    e12 = jnp.zeros((8,), dtype=jnp.float64).at[3].set(1.0)
    gp12 = clifford_gp(e1, e2)
    gp21 = clifford_gp(e2, e1)

    theta = 0.37
    rotor = jnp.zeros((8,), dtype=jnp.float64).at[0].set(jnp.cos(theta / 2.0))
    rotor = rotor.at[3].set(-jnp.sin(theta / 2.0))
    rotated = clifford_gp(clifford_gp(rotor, e1), clifford_reverse(rotor))
    rotor_norm = clifford_gp(rotor, clifford_reverse(rotor))[0]
    vector_norm = jnp.linalg.norm(rotated[jnp.array([1, 2, 4])])

    return {
        "anti_commutator_norm": _float(jnp.linalg.norm(gp12 + gp21)),
        "e1e2_minus_e12_norm": _float(jnp.linalg.norm(gp12 - e12)),
        "rotor_unit_error": _float(jnp.abs(rotor_norm - 1.0)),
        "rotated_vector_norm_error": _float(jnp.abs(vector_norm - 1.0)),
        "pass": _bool(
            (jnp.linalg.norm(gp12 + gp21) < 1e-12)
            & (jnp.linalg.norm(gp12 - e12) < 1e-12)
            & (jnp.abs(rotor_norm - 1.0) < 1e-12)
            & (jnp.abs(vector_norm - 1.0) < 1e-12)
        ),
    }


def jaxga_package_check():
    status = {
        "installed": importlib.util.find_spec("jaxga") is not None,
        "product_status": "not_checked",
        "runtime_patch_applied": False,
        "vanilla_error": None,
        "error": None,
        "pass": False,
    }
    if not status["installed"]:
        status["product_status"] = "missing"
        return status
    from jaxga.mv import MultiVector

    def _try_product():
        e1 = MultiVector.e(0)
        e2 = MultiVector.e(1)
        return e1 * e2, e2 * e1

    try:
        prod12, prod21 = _try_product()
        status.update({"product_status": "ok_vanilla", "prod12": repr(prod12), "prod21": repr(prod21)})
    except Exception as exc:
        status["vanilla_error"] = f"{type(exc).__name__}: {exc}"
        _patch_jaxga_multiply_runtime()
        status["runtime_patch_applied"] = True
        try:
            prod12, prod21 = _try_product()
            status.update({"product_status": "ok_after_runtime_compat_patch", "prod12": repr(prod12), "prod21": repr(prod21)})
        except Exception as patched_exc:
            status.update(
                {
                    "product_status": "blocked_broken_runtime",
                    "error": f"{type(patched_exc).__name__}: {patched_exc}",
                    "pass": False,
                }
            )
            return status

    anti_error = jnp.linalg.norm(jnp.asarray(prod12.values) + jnp.asarray(prod21.values))
    status.update(
        {
            "anti_commutator_norm": _float(anti_error),
            "indices12": [list(idx) for idx in prod12.indices],
            "indices21": [list(idx) for idx in prod21.indices],
            "pass": _bool(anti_error < 1e-6),
        }
    )
    return status


def _patch_jaxga_multiply_runtime():
    """Patch jaxga's JAX-0.10 static_argnames mismatch inside this process only."""
    import jaxga.mv as mv_module
    import jaxga.ops.multiply as multiply_module
    from jaxga.jaxga import reduce_bases

    @cache
    def get_mv_multiply(a_blade_indices, b_blade_indices, signature, prod="gp"):
        out_indices = []
        out_blade_indices = []
        out_signs = []
        indices_a = []
        indices_b = []
        blade_to_index = {}

        for (i_a, index_a), (i_b, index_b) in itertools.product(
            enumerate(a_blade_indices), enumerate(b_blade_indices)
        ):
            out_sign, out_index = reduce_bases(index_a, index_b, signature)
            if out_sign != 0 and (
                prod == "gp"
                or (prod == "op" and len(out_index) == abs(len(index_a) + len(index_b)))
                or (prod == "ip" and len(out_index) == abs(len(index_a) - len(index_b)))
            ):
                out_signs.append(out_sign)
                indices_a.append(i_a)
                indices_b.append(i_b)
                if out_index in blade_to_index:
                    out_indices.append(blade_to_index[out_index])
                else:
                    blade_to_index[out_index] = len(blade_to_index)
                    out_indices.append(blade_to_index[out_index])
                    out_blade_indices.append(out_index)

        if len(out_indices) == 0:
            def _values_mv_mul(a_values, b_values):
                return jnp.zeros((), dtype=jnp.result_type(a_values, b_values))
        else:
            out_size = max(out_indices) + 1

            def _values_mv_mul(a_values, b_values):
                out_batch_shape = jnp.broadcast_shapes(a_values.shape[1:], b_values.shape[1:])
                out_values = jnp.zeros([out_size, *out_batch_shape], dtype=jnp.result_type(a_values, b_values))
                for index_a, index_b, out_sign, out_index in zip(indices_a, indices_b, out_signs, out_indices):
                    out_values = out_values.at[out_index].add(out_sign * a_values[index_a] * b_values[index_b])
                return out_values

        return jax.jit(_values_mv_mul), tuple(out_blade_indices)

    multiply_module.get_mv_multiply = get_mv_multiply
    mv_module.get_mv_multiply = get_mv_multiply


def jaxlie_check():
    omega = jnp.array([0.2, -0.1, 0.3], dtype=jnp.float64)
    v = jnp.array([0.0, 0.0, 1.0], dtype=jnp.float64)

    @jax.jit
    def transport(w, vec):
        rot = jaxlie.SO3.exp(w)
        return rot.apply(vec), rot.log(), rot.as_quaternion_xyzw()

    rv, recovered, quat = transport(omega, v)
    return {
        "rotated_norm_error": _float(jnp.abs(jnp.linalg.norm(rv) - 1.0)),
        "log_exp_roundtrip_error": _float(jnp.linalg.norm(recovered - omega)),
        "quaternion_norm_error": _float(jnp.abs(jnp.linalg.norm(quat) - 1.0)),
        "pass": _bool(
            (jnp.abs(jnp.linalg.norm(rv) - 1.0) < 1e-12)
            & (jnp.linalg.norm(recovered - omega) < 1e-12)
            & (jnp.abs(jnp.linalg.norm(quat) - 1.0) < 1e-12)
        ),
    }


def diffrax_event_prune_check():
    target = unit(jnp.array([0.5, 0.5, 0.5, 0.5], dtype=jnp.float64))

    def vector_field(t, y, args):
        q = unit(y)
        return 2.0 * (args - jnp.dot(args, q) * q)

    def forbidden_event(state, **kwargs):
        del kwargs
        return state.y[0] < -0.01

    def solve(y0):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*discrete_terminating_event=.*deprecated.*")
            return diffrax.diffeqsolve(
                diffrax.ODETerm(vector_field),
                diffrax.Dopri5(),
                t0=0.0,
                t1=4.0,
                dt0=0.01,
                y0=unit(y0),
                args=target,
                stepsize_controller=diffrax.PIDController(rtol=1e-7, atol=1e-9),
                discrete_terminating_event=diffrax.DiscreteTerminatingEvent(forbidden_event),
                saveat=diffrax.SaveAt(t1=True),
                max_steps=4096,
                throw=False,
            )

    alive0 = jnp.array([0.2, 0.9, 0.1, -0.2], dtype=jnp.float64)
    dead0 = jnp.array([-0.2, 0.97, 0.0, 0.0], dtype=jnp.float64)
    alive_sol = solve(alive0)
    dead_sol = solve(dead0)
    alive_final = alive_sol.ys[-1]
    dead_result = str(dead_sol.result)
    alive_result = str(alive_sol.result)
    dead_event = "event occurred" in dead_result
    alive_success = "event occurred" not in alive_result and alive_final[0] > 0.0
    alive_norm_drift = jnp.abs(jnp.linalg.norm(alive_final) - 1.0)
    return {
        "alive_result": alive_result,
        "dead_result": dead_result,
        "alive_final_q0": _float(alive_final[0]),
        "alive_norm_drift": _float(alive_norm_drift),
        "dead_event_pruned": dead_event,
        "alive_success": _bool(alive_success),
        "pass": _bool(dead_event & alive_success & (alive_norm_drift < 1e-6)),
    }


def optax_retraction_check():
    target = unit(jnp.array([0.5, 0.5, 0.5, 0.5], dtype=jnp.float64))
    start = unit(jnp.array([0.2, -0.8, 0.5, -0.1], dtype=jnp.float64))
    opt = optax.adam(learning_rate=0.08)

    def loss(x):
        q = retract_s3(x)
        return 1.0 - jnp.dot(q, target)

    @jax.jit
    def run():
        state = opt.init(start)

        def step(carry, _):
            x, opt_state = carry
            value, grad = jax.value_and_grad(loss)(x)
            updates, opt_state = opt.update(grad, opt_state, x)
            x = retract_s3(optax.apply_updates(x, updates))
            drift = jnp.abs(jnp.linalg.norm(x) - 1.0)
            return (x, opt_state), (value, drift)

        (final_x, _), (values, drifts) = jax.lax.scan(step, (start, state), jnp.arange(96))
        return final_x, values, drifts

    final_x, values, drifts = run()
    initial_loss = values[0]
    final_loss = loss(final_x)
    return {
        "initial_loss": _float(initial_loss),
        "final_loss": _float(final_loss),
        "loss_improvement": _float(initial_loss - final_loss),
        "max_norm_drift": _float(jnp.max(drifts)),
        "pass": _bool((final_loss < initial_loss) & (jnp.max(drifts) < 1e-12)),
    }


def custom_vjp_check():
    x = jnp.array([0.7, -0.3, 0.2, 0.1], dtype=jnp.float64)

    def loss(raw):
        q = retract_s3(raw)
        return q[0] + 0.25 * q[1] ** 2 - 0.1 * q[2]

    q = retract_s3(x)
    grad = jax.grad(loss)(x)
    tangent_dot = jnp.abs(jnp.vdot(q, grad))
    return {
        "tangent_dot": _float(tangent_dot),
        "gradient_norm": _float(jnp.linalg.norm(grad)),
        "pass": _bool(tangent_dot < 1e-12),
    }


def lax_scan_retraction_check():
    targets = jnp.array(
        [
            [0.5, 0.5, 0.5, 0.5],
            [0.5, 0.5, -0.5, -0.5],
            [-0.5, -0.5, 0.5, -0.5],
            [-0.5, -0.5, -0.5, 0.5],
        ],
        dtype=jnp.float64,
    )

    @jax.jit
    def run():
        key = jax.random.PRNGKey(42)
        q = jax.random.normal(key, (128, 4), dtype=jnp.float64)
        q = q / jnp.linalg.norm(q, axis=1, keepdims=True)
        alive = jnp.ones((128,), dtype=bool)
        dt = 1e-3

        def step(carry, _):
            q, alive = carry
            dots = q @ targets.T
            nearest = targets[jnp.argmax(dots, axis=1)]
            flow = 2.0 * (nearest - jnp.sum(nearest * q, axis=1, keepdims=True) * q)
            q = q + dt * flow
            q = q / jnp.linalg.norm(q, axis=1, keepdims=True)
            alive = alive & ~(q[:, 0] < -0.01)
            return (q, alive), jnp.max(jnp.abs(jnp.linalg.norm(q, axis=1) - 1.0))

        (qf, alivef), drifts = jax.lax.scan(step, (q, alive), jnp.arange(2000))
        return qf, alivef, drifts

    qf, alivef, drifts = run()
    return {
        "survivors": int(jax.device_get(jnp.sum(alivef))),
        "pruned": int(jax.device_get(qf.shape[0] - jnp.sum(alivef))),
        "max_norm_drift": _float(jnp.max(drifts)),
        "pass": _bool((jnp.sum(~alivef) > 0) & (jnp.max(drifts) < 1e-12)),
    }


def main():
    surfaces = {
        "jaxga_package": jaxga_package_check(),
        "custom_clifford_primitive": custom_clifford_check(),
        "jaxlie_so3_manifold": jaxlie_check(),
        "diffrax_event_pruning": diffrax_event_prune_check(),
        "optax_retracted_optimization": optax_retraction_check(),
        "custom_vjp_tangent_projection": custom_vjp_check(),
        "lax_scan_stepwise_retraction": lax_scan_retraction_check(),
        "riemannax": {
            "installed": importlib.util.find_spec("riemannax") is not None,
            "status": "ok" if importlib.util.find_spec("riemannax") else "blocked_missing_package",
            "pass": importlib.util.find_spec("riemannax") is not None,
        },
    }

    load_bearing_checks = {
        "jaxga_package_product": surfaces["jaxga_package"]["pass"],
        "custom_clifford_primitive": surfaces["custom_clifford_primitive"]["pass"],
        "jaxlie_so3_manifold": surfaces["jaxlie_so3_manifold"]["pass"],
        "diffrax_event_pruning": surfaces["diffrax_event_pruning"]["pass"],
        "optax_retracted_optimization": surfaces["optax_retracted_optimization"]["pass"],
        "custom_vjp_tangent_projection": surfaces["custom_vjp_tangent_projection"]["pass"],
        "lax_scan_stepwise_retraction": surfaces["lax_scan_stepwise_retraction"]["pass"],
        "blocked_surfaces_are_explicit": (
            surfaces["jaxga_package"]["product_status"] in {"ok_vanilla", "ok_after_runtime_compat_patch"}
            and surfaces["riemannax"]["status"] in {"ok", "blocked_missing_package"}
        ),
    }
    audit_pass = all(bool(v) for v in load_bearing_checks.values())

    receipt = {
        "script": str(Path(__file__).name),
        "classification": "diagnostic_jax_geometric_evolution_toolstack_audit",
        "promotion_allowed": False,
        "sim_execution_kind": "nonclassical_diagnostic",
        "purpose": "Exercise the JAX lane as batched/manifold-aware audit machinery while recording package blockers.",
        "root_constraints_in_force": {
            "F01": "finite Clifford basis, finite S3/quaternion states, finite ODE/scan steps",
            "N01": "order-sensitive Clifford product e1*e2=-e2*e1 plus monotone prune/retraction controls",
        },
        "finite_map": {
            "domain": "finite Cl(3,0) multivector coefficients, S3 unit quaternions, finite branch batch",
            "codomain_or_output": "anti-commutation/rotor invariants, event-pruned trajectories, tangent-projected gradients",
        },
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "tool_manifest": {
            "jax": "load-bearing JIT, grad, random, lax.scan, x64 arrays",
            "jaxga": "load-bearing audited Clifford package surface; runtime shim is recorded if needed for JAX compatibility",
            "custom_clifford_jax": "load-bearing cross-check geometric product for anti-commutation and rotor invariants",
            "jaxlie": "load-bearing SO3 exp/log/quaternion manifold transport check",
            "diffrax": "load-bearing ODE solve with DiscreteTerminatingEvent pruning check",
            "optax": "load-bearing optimization with explicit S3 retraction after each update",
            "custom_vjp": "load-bearing tangent-space gradient projection for S3 retraction",
            "riemannax": "optional manifold package surface; recorded as missing if unavailable",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jaxga": "load_bearing",
            "custom_clifford_jax": "load_bearing",
            "jaxlie": "load_bearing",
            "diffrax": "load_bearing",
            "optax": "load_bearing",
            "riemannax": "blocked_or_supportive",
        },
        "surfaces": surfaces,
        "load_bearing_checks": load_bearing_checks,
        "AUDIT_PASS": audit_pass,
        "blocked_consumers": [
            "layer_stacking",
            "flux",
            "Xi/Phi0",
            "Axis0",
            "bridge",
            "basin_admission",
            "physics/gravity",
            "final_manifold_admission",
        ],
        "honesty_notes": [
            "jaxga is not counted as load-bearing unless its geometric product runs.",
            "riemannax is absent in this environment and is recorded as a blocked optional surface.",
            "This diagnostic does not touch the retired legacy tensor lane and does not claim Julia-equivalent spinor geometry truth.",
        ],
    }

    RESULT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    print(
        "custom_clifford={custom} jaxga={jaxga} jaxlie={jaxlie} diffrax_event={diffrax} "
        "optax_retract={optax} custom_vjp={vjp} lax_scan={scan} riemannax={riemannax}".format(
            custom=surfaces["custom_clifford_primitive"]["pass"],
            jaxga=surfaces["jaxga_package"]["product_status"],
            jaxlie=surfaces["jaxlie_so3_manifold"]["pass"],
            diffrax=surfaces["diffrax_event_pruning"]["pass"],
            optax=surfaces["optax_retracted_optimization"]["pass"],
            vjp=surfaces["custom_vjp_tangent_projection"]["pass"],
            scan=surfaces["lax_scan_stepwise_retraction"]["pass"],
            riemannax=surfaces["riemannax"]["status"],
        )
    )
    print(f"AUDIT_PASS={audit_pass}")


if __name__ == "__main__":
    main()
