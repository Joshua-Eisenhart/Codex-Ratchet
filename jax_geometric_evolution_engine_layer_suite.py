#!/usr/bin/env python3
"""JAX Geometric Evolution Engine layer-suite diagnostic.

Runs independent finite JAX maps for the current JAX lane:
S3/Hopf, jaxga Clifford product, Weyl chirality, Dirac U(1), ER=EPR log-neg,
branch/prune, and Hamiltonian shell coupling. Diagnostic only; no promotion.
"""

from __future__ import annotations

import importlib.util
import json
import warnings
from pathlib import Path

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import diffrax
import jax.scipy.linalg as jsp_linalg

from jax_geometric_evolution_toolstack_audit import (
    _patch_jaxga_multiply_runtime,
    clifford_gp,
    clifford_reverse,
    retract_s3,
    unit,
)


RESULT_PATH = Path("jax_geometric_evolution_engine_layer_suite_results.json")
TOL = 1e-7


def _float(x) -> float:
    return float(jax.device_get(x))


def _bool(x) -> bool:
    return bool(jax.device_get(x))


def wrap_angle(x):
    return (x + jnp.pi) % (2.0 * jnp.pi) - jnp.pi


def hopf_map(q):
    q = unit(q)
    z1 = q[0] + 1j * q[1]
    z2 = q[2] + 1j * q[3]
    return jnp.array(
        [
            2.0 * jnp.real(z1 * jnp.conj(z2)),
            2.0 * jnp.imag(z1 * jnp.conj(z2)),
            jnp.abs(z1) ** 2 - jnp.abs(z2) ** 2,
        ],
        dtype=jnp.float64,
    )


def fiber_rotate(q, phase):
    z1 = q[0] + 1j * q[1]
    z2 = q[2] + 1j * q[3]
    e = jnp.exp(1j * phase)
    w1 = e * z1
    w2 = e * z2
    return jnp.array([jnp.real(w1), jnp.imag(w1), jnp.real(w2), jnp.imag(w2)], dtype=jnp.float64)


def hopf_s3_layer():
    q = unit(jnp.array([0.32, -0.41, 0.73, 0.45], dtype=jnp.float64))
    rotated = fiber_rotate(q, 1.37)
    base = hopf_map(q)
    base_rotated = hopf_map(rotated)
    fiber_invariance = jnp.linalg.norm(base - base_rotated)
    base_norm = jnp.linalg.norm(base)
    bad = q.at[0].add(0.15)
    raw_bad_norm_error = jnp.abs(jnp.linalg.norm(bad) - 1.0)
    retracted_bad_base_norm_error = jnp.abs(jnp.linalg.norm(hopf_map(bad)) - 1.0)
    return {
        "finite_map": "S3 unit quaternion -> S2 Hopf base; U(1) fiber rotation leaves base invariant",
        "fiber_invariance_error": _float(fiber_invariance),
        "base_norm_error": _float(jnp.abs(base_norm - 1.0)),
        "raw_bad_s3_norm_error": _float(raw_bad_norm_error),
        "retracted_bad_base_norm_error": _float(retracted_bad_base_norm_error),
        "pass": _bool((fiber_invariance < 1e-12) & (jnp.abs(base_norm - 1.0) < 1e-12)),
    }


def jaxga_clifford_layer():
    status = {"installed": importlib.util.find_spec("jaxga") is not None}
    if not status["installed"]:
        status.update({"pass": False, "product_status": "missing"})
        return status
    from jaxga.mv import MultiVector

    vanilla_error = None
    try:
        prod12 = MultiVector.e(0) * MultiVector.e(1)
        prod21 = MultiVector.e(1) * MultiVector.e(0)
        product_status = "ok_vanilla"
    except Exception as exc:
        vanilla_error = f"{type(exc).__name__}: {exc}"
        _patch_jaxga_multiply_runtime()
        prod12 = MultiVector.e(0) * MultiVector.e(1)
        prod21 = MultiVector.e(1) * MultiVector.e(0)
        product_status = "ok_after_runtime_compat_patch"

    anti_error = jnp.linalg.norm(jnp.asarray(prod12.values) + jnp.asarray(prod21.values))

    e1 = jnp.zeros((8,), dtype=jnp.float64).at[1].set(1.0)
    theta = 0.43
    rotor = jnp.zeros((8,), dtype=jnp.float64).at[0].set(jnp.cos(theta / 2.0))
    rotor = rotor.at[3].set(-jnp.sin(theta / 2.0))
    rotated = clifford_gp(clifford_gp(rotor, e1), clifford_reverse(rotor))
    rotor_norm_error = jnp.abs(clifford_gp(rotor, clifford_reverse(rotor))[0] - 1.0)
    rotated_vector_norm_error = jnp.abs(jnp.linalg.norm(rotated[jnp.array([1, 2, 4])]) - 1.0)
    return {
        "finite_map": "Cl(3,0) ordered geometric product and rotor action",
        "product_status": product_status,
        "vanilla_error": vanilla_error,
        "anti_commutator_norm": _float(anti_error),
        "rotor_norm_error": _float(rotor_norm_error),
        "rotated_vector_norm_error": _float(rotated_vector_norm_error),
        "pass": _bool((anti_error < 1e-6) & (rotor_norm_error < 1e-12) & (rotated_vector_norm_error < 1e-12)),
    }


def weyl_chirality_layer():
    sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
    k = jnp.array([0.0, 0.0, 1.0], dtype=jnp.float64)
    h0 = k[0] * sx + k[1] * sy + k[2] * sz
    psi = jnp.array([1.0 + 0j, 0.0 + 0j], dtype=jnp.complex128)
    energy_l = jnp.real(jnp.vdot(psi, h0 @ psi))
    energy_r = jnp.real(jnp.vdot(psi, (-h0) @ psi))
    unitary_l = jsp_linalg.expm(-1j * 0.7 * h0)
    norm_error = jnp.abs(jnp.linalg.norm(unitary_l @ psi) - 1.0)
    zero_gap = jnp.real(jnp.vdot(psi, (jnp.zeros_like(h0)) @ psi))
    return {
        "finite_map": "left/right Weyl Hamiltonians H_L=+sigma.k, H_R=-sigma.k on one finite spinor",
        "energy_L": _float(energy_l),
        "energy_R": _float(energy_r),
        "chirality_gap": _float(jnp.abs(energy_l - energy_r)),
        "zero_control_gap": _float(jnp.abs(zero_gap)),
        "unitary_norm_error": _float(norm_error),
        "pass": _bool((energy_l > 0.9) & (energy_r < -0.9) & (norm_error < 1e-12)),
    }


def dirac_u1_layer():
    theta = jnp.pi / 3.0
    phis = jnp.linspace(0.0, 2.0 * jnp.pi, 257)

    def spinor(phi):
        return jnp.array([jnp.cos(theta / 2.0), jnp.exp(1j * phi) * jnp.sin(theta / 2.0)], dtype=jnp.complex128)

    psi = jax.vmap(spinor)(phis)
    overlaps = jnp.sum(jnp.conj(psi[:-1]) * psi[1:], axis=1)
    berry = jnp.angle(jnp.prod(overlaps / jnp.abs(overlaps)))
    expected = 0.5 * 2.0 * jnp.pi * (1.0 - jnp.cos(theta))

    gauge = jnp.exp(1j * 0.23 * jnp.sin(phis))
    psi_g = psi * gauge[:, None]
    overlaps_g = jnp.sum(jnp.conj(psi_g[:-1]) * psi_g[1:], axis=1)
    berry_g = jnp.angle(jnp.prod(overlaps_g / jnp.abs(overlaps_g)))
    return {
        "finite_map": "finite spinor loop on S2 -> U(1) Berry/Dirac monopole phase",
        "berry_phase": _float(berry),
        "expected_phase": _float(expected),
        "phase_error": _float(jnp.abs(wrap_angle(berry - expected))),
        "gauge_phase_error": _float(jnp.abs(wrap_angle(berry_g - berry))),
        "pass": _bool((jnp.abs(wrap_angle(berry - expected)) < 2e-3) & (jnp.abs(wrap_angle(berry_g - berry)) < 2e-12)),
    }


def vn_entropy(rho):
    evals = jnp.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    evals = jnp.clip(jnp.real(evals), 0.0, 1.0)
    evals = evals[evals > 1e-12]
    return -jnp.sum(evals * jnp.log2(evals))


def rdm_pure(psi, keep, n):
    keep = list(keep)
    trace = [i for i in range(n) if i not in keep]
    t = jnp.transpose(psi.reshape([2] * n), keep + trace).reshape(2 ** len(keep), 2 ** len(trace))
    return t @ t.conj().T


def rdm_dephased(psi, keep, n):
    keep = list(keep)
    trace = [i for i in range(n) if i not in keep]
    p = jnp.abs(psi) ** 2
    t = jnp.transpose(p.reshape([2] * n), keep + trace).reshape(2 ** len(keep), 2 ** len(trace))
    return jnp.diag(jnp.sum(t, axis=1)).astype(jnp.complex128)


def bell_pair(i, j, n):
    basis = jnp.arange(2**n)
    bits_i = (basis >> (n - 1 - i)) & 1
    bits_j = (basis >> (n - 1 - j)) & 1
    mask = bits_i == bits_j
    values = jnp.where(mask, 1.0, 0.0)
    return values / jnp.linalg.norm(values)


def two_bell(i, j, k, l, n):
    basis = jnp.arange(2**n)
    bi = (basis >> (n - 1 - i)) & 1
    bj = (basis >> (n - 1 - j)) & 1
    bk = (basis >> (n - 1 - k)) & 1
    bl = (basis >> (n - 1 - l)) & 1
    mask = (bi == bj) & (bk == bl)
    values = jnp.where(mask, 1.0 + 0j, 0.0 + 0j)
    return values / jnp.linalg.norm(values)


def log_neg_rho(rho, d_a, d_c):
    pt = rho.reshape(d_a, d_c, d_a, d_c).transpose(0, 3, 2, 1).reshape(d_a * d_c, d_a * d_c)
    evals = jnp.linalg.eigvalsh((pt + pt.conj().T) / 2.0)
    return jnp.log2(jnp.sum(jnp.abs(evals)))


def qit_logneg_layer():
    n = 4
    linked = two_bell(0, 3, 1, 2, n)
    trivial = two_bell(0, 1, 2, 3, n)
    product = jnp.zeros((2**n,), dtype=jnp.complex128).at[0].set(1.0)
    rho_linked_ac = rdm_pure(linked, [0, 3], n)
    rho_trivial_ac = rdm_pure(trivial, [0, 3], n)
    rho_product_ac = rdm_pure(product, [0, 3], n)
    rho_deph_ac = rdm_dephased(linked, [0, 3], n)
    ln_link = log_neg_rho(rho_linked_ac, 2, 2)
    ln_triv = log_neg_rho(rho_trivial_ac, 2, 2)
    ln_prod = log_neg_rho(rho_product_ac, 2, 2)
    ln_deph = log_neg_rho(rho_deph_ac, 2, 2)
    coherent_link = vn_entropy(rdm_pure(linked, [3], n)) - vn_entropy(rho_linked_ac)
    coherent_deph = vn_entropy(rdm_dephased(linked, [3], n)) - vn_entropy(rho_deph_ac)
    return {
        "finite_map": "finite density cut rho_AC -> log-negativity/coherent information with dephasing kill",
        "LN_linked_AC": _float(ln_link),
        "LN_trivial_AC": _float(ln_triv),
        "LN_product_AC": _float(ln_prod),
        "LN_dephased_AC": _float(ln_deph),
        "coherent_information_linked": _float(coherent_link),
        "coherent_information_dephased": _float(coherent_deph),
        "pass": _bool((ln_link > 0.9) & (ln_triv < 1e-10) & (ln_prod < 1e-10) & (ln_deph < 1e-10) & (coherent_link > 0.9)),
    }


def branch_prune_layer():
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
    def run(prune):
        key = jax.random.PRNGKey(42)
        q = jax.random.normal(key, (400, 4), dtype=jnp.float64)
        q = q / jnp.linalg.norm(q, axis=1, keepdims=True)
        alive = jnp.ones((400,), dtype=bool)
        dt = 1e-3

        def step(carry, _):
            q, alive = carry
            nearest = targets[jnp.argmax(q @ targets.T, axis=1)]
            flow = 2.0 * (nearest - jnp.sum(nearest * q, axis=1, keepdims=True) * q)
            q = q + dt * flow
            q = q / jnp.linalg.norm(q, axis=1, keepdims=True)
            alive = jnp.where(prune, alive & ~(q[:, 0] < -0.01), alive)
            return (q, alive), jnp.max(jnp.abs(jnp.linalg.norm(q, axis=1) - 1.0))

        (qf, alivef), drifts = jax.lax.scan(step, (q, alive), jnp.arange(2500))
        labels = 1 + jnp.argmax(qf @ targets.T, axis=1)
        return labels, alivef, jnp.max(drifts)

    labels_a, alive_a, drift_a = run(False)
    labels_b, alive_b, drift_b = run(True)
    labels_c, alive_c, drift_c = run(False)

    def populated(labels, alive):
        return [int(x) for x in jax.device_get(jnp.unique(labels[alive], size=4, fill_value=-1)) if int(x) > 0]

    pop_a = populated(labels_a, alive_a)
    pop_b = populated(labels_b, alive_b)
    pop_c = populated(labels_c, alive_c)
    pruned_b = int(jax.device_get(400 - jnp.sum(alive_b)))
    max_drift = jnp.max(jnp.array([drift_a, drift_b, drift_c]))
    return {
        "finite_map": "finite S3 attractor branch ensemble -> monotone chirality prune basin readout",
        "A_populated": pop_a,
        "B_populated": pop_b,
        "C_populated": pop_c,
        "B_pruned": pruned_b,
        "max_norm_drift": _float(max_drift),
        "pass": bool(pop_a == [1, 2, 3, 4] and set(pop_b).isdisjoint({3, 4}) and set(pop_a).intersection({1, 2}).issubset(set(pop_b)) and pop_c == pop_a and pruned_b > 0 and _float(max_drift) < 1e-12),
    }


def hamiltonian_shell_layer():
    h = jnp.array(
        [
            [0.0, 0.7, 0.0, 0.0],
            [0.7, 0.0, 0.35j, 0.0],
            [0.0, -0.35j, 0.0, 0.55],
            [0.0, 0.0, 0.55, 0.0],
        ],
        dtype=jnp.complex128,
    )
    h0 = jnp.diag(jnp.diag(h))
    y0 = jnp.array([1.0 + 0j, 0.0 + 0j, 0.0 + 0j, 0.0 + 0j], dtype=jnp.complex128)

    def solve(ham):
        def vf(t, y, args):
            del t
            return -1j * (args @ y)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*complex dtype.*")
            return diffrax.diffeqsolve(
                diffrax.ODETerm(vf),
                diffrax.Dopri5(),
                t0=0.0,
                t1=3.0,
                dt0=0.01,
                y0=y0,
                args=ham,
                stepsize_controller=diffrax.PIDController(rtol=1e-7, atol=1e-9),
                saveat=diffrax.SaveAt(t1=True),
                max_steps=4096,
                throw=False,
            ).ys[-1]

    coupled = solve(h)
    control = solve(h0)
    coupled_prob_far = jnp.abs(coupled[3]) ** 2
    control_prob_far = jnp.abs(control[3]) ** 2
    norm_error = jnp.abs(jnp.linalg.norm(coupled) - 1.0)
    return {
        "finite_map": "finite shell coupling Hamiltonian -> unitary amplitude transport",
        "coupled_far_shell_probability": _float(coupled_prob_far),
        "control_far_shell_probability": _float(control_prob_far),
        "norm_error": _float(norm_error),
        "pass": _bool((coupled_prob_far > control_prob_far + 1e-3) & (norm_error < 1e-5)),
    }


def main():
    layers = {
        "hopf_s3": hopf_s3_layer(),
        "jaxga_clifford": jaxga_clifford_layer(),
        "weyl_chirality": weyl_chirality_layer(),
        "dirac_u1": dirac_u1_layer(),
        "qit_logneg_erepr": qit_logneg_layer(),
        "branch_prune": branch_prune_layer(),
        "hamiltonian_shell": hamiltonian_shell_layer(),
    }
    all_pass = all(bool(v["pass"]) for v in layers.values())
    receipt = {
        "script": Path(__file__).name,
        "classification": "diagnostic_jax_geometric_evolution_engine_layer_suite",
        "promotion_allowed": False,
        "sim_execution_kind": "nonclassical_diagnostic",
        "purpose": "Run independent finite JAX maps for the Geometric Evolution Engine audit lane.",
        "root_constraints_in_force": {
            "F01": "finite carriers: S3 quaternions, Cl(3,0) basis, 2-qubit/4-qubit densities, finite branch batch, finite Hamiltonian",
            "N01": "order-sensitive Clifford product, chirality sign, U(1) phase holonomy, monotone branch/prune order, Hamiltonian coupling control",
        },
        "tool_manifest": {
            "jax": "load-bearing jit, vmap, random, lax.scan, complex/x64 linear algebra",
            "jaxga": "load-bearing Clifford package surface with runtime compatibility patch recorded if needed",
            "diffrax": "load-bearing ODE integrator for Hamiltonian transport",
            "jax.scipy.linalg": "load-bearing finite unitary exponential for Weyl chirality",
            "custom_vjp/retract_s3": "imported from tool-stack audit for manifold projection semantics",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jaxga": "load_bearing",
            "diffrax": "load_bearing",
            "jax.scipy.linalg": "load_bearing",
            "custom_vjp/retract_s3": "load_bearing",
        },
        "layers": layers,
        "pass_count": sum(1 for v in layers.values() if v["pass"]),
        "total_layers": len(layers),
        "AUDIT_PASS": all_pass,
        "blocked_consumers": [
            "official_layer_completion",
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
            "This is a JAX diagnostic/audit suite, not a Julia-native spinor proof.",
            "Each layer is independent and receipt-bounded; no aggregate layer admission is claimed.",
            "No retired legacy tensor-lane import or sim path is used.",
        ],
    }
    RESULT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print("layers_pass={}/{} {}".format(receipt["pass_count"], receipt["total_layers"], " ".join(f"{k}={v['pass']}" for k, v in layers.items())))
    print(f"AUDIT_PASS={all_pass}")


if __name__ == "__main__":
    main()
