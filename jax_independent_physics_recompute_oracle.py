#!/usr/bin/env python3
"""Independent JAX recompute oracle for high-risk diagnostic rows.

This oracle does not import `jax_manifold_layer_independent_suite.py` and does
not trust row-local pass flags. It recomputes the highest-risk row physics from
finite JAX objects, compares the metrics against the existing diagnostic
receipt, and preserves the no-promotion / no-Julia-execution ceiling.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


SOURCE = Path("jax_manifold_layer_independent_suite_results.json")
OUT = Path("jax_independent_physics_recompute_oracle_results.json")
EPS = 1.0e-9

I = 1j
C2 = jnp.eye(2, dtype=jnp.complex128)
C4 = jnp.eye(4, dtype=jnp.complex128)
SX = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.asarray([[0, -I], [I, 0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
Z2 = jnp.zeros((2, 2), dtype=jnp.complex128)

Q_TARGETS = jnp.asarray(
    [
        [0.5, 0.5, 0.5, 0.5],
        [0.5, 0.5, -0.5, -0.5],
        [-0.5, -0.5, 0.5, -0.5],
        [-0.5, -0.5, -0.5, 0.5],
    ],
    dtype=jnp.float64,
)

TARGET_ROWS = [
    "boundary_environment_cut",
    "nested_hopf_shells",
    "weyl_gamma5_chirality",
    "qit_entropy_information",
    "conditional_mutual_information_readout",
    "spectral_triple_dirac",
    "survivor_quotient_branch_prune",
]


def normalize(x: jax.Array) -> jax.Array:
    return x / jnp.linalg.norm(x, axis=-1, keepdims=True)


def density(psi: jax.Array) -> jax.Array:
    return jnp.einsum("...i,...j->...ij", psi, jnp.conj(psi))


def vn_entropy(rho: jax.Array) -> jax.Array:
    herm = 0.5 * (rho + jnp.conj(rho.T))
    ev = jnp.clip(jnp.real(jnp.linalg.eigvalsh(herm)), 0.0, 1.0)
    return -jnp.sum(jnp.where(ev > 1.0e-12, ev * jnp.log2(ev), 0.0))


def rho_a_2q(rho: jax.Array) -> jax.Array:
    return jnp.trace(rho.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def rho_b_2q(rho: jax.Array) -> jax.Array:
    return jnp.trace(rho.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def log_negativity_2q(rho: jax.Array) -> jax.Array:
    pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    ev = jnp.linalg.eigvalsh(0.5 * (pt + jnp.conj(pt.T)))
    return jnp.log2(jnp.sum(jnp.abs(ev)))


def mutual_information_2q(rho: jax.Array) -> jax.Array:
    return vn_entropy(rho_a_2q(rho)) + vn_entropy(rho_b_2q(rho)) - vn_entropy(rho)


def rdm_pure(psi: jax.Array, keep: list[int], n: int) -> jax.Array:
    trace = [i for i in range(n) if i not in keep]
    t = jnp.transpose(psi.reshape([2] * n), keep + trace).reshape(2 ** len(keep), 2 ** len(trace))
    return t @ jnp.conj(t.T)


def rdm_mixed(rho: jax.Array, keep: list[int], n: int) -> jax.Array:
    keep = sorted(keep)
    trace = [i for i in range(n) if i not in keep]
    t = rho.reshape([2] * n + [2] * n)
    for q in sorted(trace, reverse=True):
        t = jnp.trace(t, axis1=q, axis2=q + t.ndim // 2)
    return t.reshape(2 ** len(keep), 2 ** len(keep))


def cmi(get_rdm, n: int) -> jax.Array:
    return (
        vn_entropy(get_rdm([0, 1], n))
        + vn_entropy(get_rdm([1, 2], n))
        - vn_entropy(get_rdm([1], n))
        - vn_entropy(get_rdm([0, 1, 2], n))
    )


def hopf_base(q: jax.Array) -> jax.Array:
    a, b, c, d = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return jnp.stack(
        [
            2.0 * (a * c + b * d),
            2.0 * (b * c - a * d),
            a * a + b * b - c * c - d * d,
        ],
        axis=-1,
    )


def lift_base_to_quat(base: jax.Array) -> jax.Array:
    x, y, z = base[..., 0], base[..., 1], base[..., 2]
    r = jnp.sqrt(jnp.maximum((1.0 + z) / 2.0, 1.0e-12))
    c = x / (2.0 * r)
    d = -y / (2.0 * r)
    return normalize(jnp.stack([r, jnp.zeros_like(r), c, d], axis=-1))


def nearest_q_labels(q: jax.Array) -> jax.Array:
    return jnp.argmax(q @ Q_TARGETS.T, axis=-1) + 1


def nearest_q_targets(q: jax.Array) -> jax.Array:
    return Q_TARGETS[jnp.argmax(q @ Q_TARGETS.T, axis=-1)]


def adjacent_base_distance(q: jax.Array) -> jax.Array:
    base = hopf_base(q)
    return jnp.linalg.norm(base[:, 1:, :] - base[:, :-1, :], axis=-1)


@jax.jit
def evolve_nested(q0: jax.Array, coupling: jax.Array, prune_active: bool) -> tuple[jax.Array, jax.Array]:
    alive0 = jnp.ones((q0.shape[0],), dtype=bool)

    def step(carry, _):
        q, alive = carry
        local = nearest_q_targets(q)
        lifted = lift_base_to_quat(hopf_base(q[:, :-1, :]))
        coupled = normalize((1.0 - coupling) * local[:, 1:, :] + coupling * lifted)
        target = jnp.concatenate([local[:, :1, :], coupled], axis=1)
        align = jnp.sum(target * q, axis=-1, keepdims=True)
        q_next = normalize(q + 0.003 * 2.0 * (target - align * q))
        killed = jnp.logical_and(prune_active, jnp.any(q_next[:, :, 0] < -0.01, axis=1))
        return (q_next, jnp.logical_and(alive, jnp.logical_not(killed))), None

    (qf, alivef), _ = jax.lax.scan(step, (q0, alive0), xs=None, length=1600)
    return qf, alivef


def nested_summary(q0: jax.Array, coupling: float, prune_active: bool) -> tuple[list[int], int, float, jax.Array]:
    qf, alive = evolve_nested(q0, jnp.asarray(coupling, dtype=jnp.float64), prune_active)
    labels = nearest_q_labels(qf[:, 0, :])
    populated = sorted(int(x) for x in jnp.unique(labels[alive]))
    pruned = int(q0.shape[0] - jnp.sum(alive))
    align = float(jnp.mean(adjacent_base_distance(qf)[alive]))
    return populated, pruned, align, alive


def blk(a: jax.Array, b: jax.Array, c: jax.Array, d: jax.Array) -> jax.Array:
    return jnp.block([[a, b], [c, d]])


G0 = blk(Z2, C2, C2, Z2)
G1 = blk(Z2, SX, -SX, Z2)
G2 = blk(Z2, SY, -SY, Z2)
G3 = blk(Z2, SZ, -SZ, Z2)
GAMMAS = jnp.stack([G0, G1, G2, G3], axis=0)
ETA = jnp.diag(jnp.asarray([1, -1, -1, -1], dtype=jnp.complex128))
G5 = 1j * G0 @ G1 @ G2 @ G3
DIRAC_TARGETS = normalize(
    jnp.asarray(
        [[0, 0, 1, 0.3], [0, 0, 0.3, 1], [1, 0.3, 0, 0], [0.3, 1, 0, 0]],
        dtype=jnp.complex128,
    )
)


def chiral_charge(psi: jax.Array) -> jax.Array:
    return jnp.real(jnp.einsum("...i,ij,...j->...", jnp.conj(psi), G5, psi))


def nearest_dirac_labels(psi: jax.Array, targets: jax.Array) -> jax.Array:
    return jnp.argmax(jnp.abs(jnp.conj(psi) @ targets.T) ** 2, axis=-1) + 1


def nearest_dirac_targets(psi: jax.Array, targets: jax.Array) -> jax.Array:
    return targets[jnp.argmax(jnp.abs(jnp.conj(psi) @ targets.T) ** 2, axis=-1)]


def dirac_flow(psi: jax.Array, targets: jax.Array) -> jax.Array:
    target = nearest_dirac_targets(psi, targets)
    align = jnp.sum(jnp.conj(psi) * target, axis=-1, keepdims=True)
    return 2.0 * (target - align * psi)


@jax.jit
def evolve_dirac(psi0: jax.Array, targets: jax.Array, prune_code: jax.Array) -> tuple[jax.Array, jax.Array]:
    alive0 = jnp.ones((psi0.shape[0],), dtype=bool)

    def step(carry, _):
        psi, alive = carry
        k1 = dirac_flow(psi, targets)
        k2 = dirac_flow(normalize(psi + 0.005 * k1), targets)
        psi_next = normalize(psi + 0.01 * k2)
        q = chiral_charge(psi_next)
        killed = jnp.where(prune_code == 1, q < -0.01, jnp.where(prune_code == 2, q > 0.99, False))
        return (psi_next, jnp.logical_and(alive, jnp.logical_not(killed))), None

    (psif, alivef), _ = jax.lax.scan(step, (psi0, alive0), xs=None, length=1200)
    return psif, alivef


def dirac_classify(psi0: jax.Array, targets: jax.Array, code: int) -> tuple[list[int], int, jax.Array, jax.Array]:
    psif, alive = evolve_dirac(psi0, targets, jnp.asarray(code))
    labels = nearest_dirac_labels(psif, targets)
    return sorted(int(x) for x in jnp.unique(labels[alive])), int(psi0.shape[0] - jnp.sum(alive)), labels, alive


@jax.jit
def evolve_simple_branch(q0: jax.Array, prune_active: bool) -> tuple[jax.Array, jax.Array]:
    alive0 = jnp.ones((q0.shape[0],), dtype=bool)

    def step(carry, _):
        q, alive = carry
        target = nearest_q_targets(q)
        align = jnp.sum(target * q, axis=-1, keepdims=True)
        q_next = normalize(q + 0.003 * 2.0 * (target - align * q))
        killed = jnp.logical_and(prune_active, q_next[:, 0] < -0.01)
        return (q_next, jnp.logical_and(alive, jnp.logical_not(killed))), None

    (qf, alivef), _ = jax.lax.scan(step, (q0, alive0), xs=None, length=2600)
    return qf, alivef


def branch_summary(q0: jax.Array, prune: bool) -> tuple[list[int], int, jax.Array]:
    qf, alive = evolve_simple_branch(q0, prune)
    labels = nearest_q_labels(qf)
    return sorted(int(x) for x in jnp.unique(labels[alive])), int(q0.shape[0] - jnp.sum(alive)), alive


def row_boundary_environment_cut() -> dict[str, Any]:
    bell = jnp.asarray([1, 0, 0, 1], dtype=jnp.complex128) / jnp.sqrt(2.0)
    product = jnp.asarray([1, 0, 0, 0], dtype=jnp.complex128)
    rho_bell = density(bell)
    rho_product = density(product)
    rho_classical = jnp.diag(jnp.asarray([0.5, 0.0, 0.0, 0.5], dtype=jnp.complex128))
    return {
        "MI_bell": float(mutual_information_2q(rho_bell)),
        "MI_product": float(mutual_information_2q(rho_product)),
        "MI_classical": float(mutual_information_2q(rho_classical)),
        "LN_classical": float(log_negativity_2q(rho_classical)),
        "S_boundary": float(vn_entropy(rho_a_2q(rho_bell))),
    }


def row_qit_entropy_information() -> dict[str, Any]:
    bell = jnp.asarray([1, 0, 0, 1], dtype=jnp.complex128) / jnp.sqrt(2.0)
    product = jnp.asarray([1, 0, 0, 0], dtype=jnp.complex128)
    rho_bell = density(bell)
    rho_product = density(product)
    rho_classical = jnp.diag(jnp.asarray([0.5, 0.0, 0.0, 0.5], dtype=jnp.complex128))
    s_ab = vn_entropy(rho_bell)
    s_b = vn_entropy(rho_b_2q(rho_bell))
    return {
        "LN_bell": float(log_negativity_2q(rho_bell)),
        "LN_classical": float(log_negativity_2q(rho_classical)),
        "LN_product": float(log_negativity_2q(rho_product)),
        "S_A_given_B_bell": float(s_ab - s_b),
        "I_c_A_to_B_bell": float(s_b - s_ab),
        "I_AB_classical": float(mutual_information_2q(rho_classical)),
    }


def row_conditional_mutual_information_readout() -> dict[str, Any]:
    n = 3
    ghz = jnp.zeros((2**n,), dtype=jnp.complex128).at[0].set(1.0 / jnp.sqrt(2.0)).at[7].set(1.0 / jnp.sqrt(2.0))
    markov = jnp.zeros((2**n,), dtype=jnp.complex128).at[0].set(1.0 / jnp.sqrt(2.0)).at[6].set(1.0 / jnp.sqrt(2.0))
    classical_ac = jnp.diag(jnp.asarray([0.5, 0, 0, 0, 0, 0.5, 0, 0], dtype=jnp.complex128))
    return {
        "CMI_GHZ": float(cmi(lambda keep, nn: rdm_pure(ghz, keep, nn), n)),
        "CMI_markov_control": float(cmi(lambda keep, nn: rdm_pure(markov, keep, nn), n)),
        "CMI_classical_shadow": float(cmi(lambda keep, nn: rdm_mixed(classical_ac, keep, nn), n)),
        "LN_classical_AC": float(log_negativity_2q(rdm_mixed(classical_ac, [0, 2], n))),
    }


def row_spectral_triple_dirac() -> dict[str, Any]:
    dirac = jnp.kron(SX, C2)
    algebra = jnp.diag(jnp.asarray([0.0, 1.0, 2.0, 4.0], dtype=jnp.complex128))
    comm = dirac @ algebra - algebra @ dirac
    ev = jnp.linalg.eigvalsh(dirac)
    return {"commutator_norm": float(jnp.linalg.norm(comm)), "spectrum": [float(x) for x in ev]}


def row_nested_hopf_shells() -> dict[str, Any]:
    n = 256
    raw = jax.random.normal(jax.random.PRNGKey(303), (12 * n, 3, 4), dtype=jnp.float64)
    unit = normalize(raw)
    idx = jnp.nonzero(jnp.all(unit[:, :, 0] > 0.05, axis=1), size=n, fill_value=0)[0]
    q0 = unit[idx]
    initial_align = float(jnp.mean(adjacent_base_distance(q0)))
    a, a_pruned, a_align, _alive_a = nested_summary(q0, 0.63, False)
    b, b_pruned, _b_align, _alive_b = nested_summary(q0, 0.63, True)
    _z, _z_pruned, zero_align, _alive_z = nested_summary(q0, 0.0, False)
    return {
        "A_basins": a,
        "B_basins": b,
        "B_pruned": b_pruned,
        "initial_alignment": initial_align,
        "coupled_alignment_delta": initial_align - a_align,
        "zero_control_alignment_delta": initial_align - zero_align,
    }


def row_weyl_gamma5_chirality() -> dict[str, Any]:
    n = 320
    raw = jax.random.normal(jax.random.PRNGKey(404), (10 * n, 4, 2), dtype=jnp.float64)
    unit = normalize(raw[..., 0] + 1j * raw[..., 1])
    idx = jnp.nonzero(chiral_charge(unit) > 0.1, size=n, fill_value=0)[0]
    psi0 = unit[idx]
    a, a_pruned, labels_a, _alive_a = dirac_classify(psi0, DIRAC_TARGETS, 0)
    b, b_pruned, _labels_b, _alive_b = dirac_classify(psi0, DIRAC_TARGETS, 1)
    c, _c_pruned, _labels_c, _alive_c = dirac_classify(psi0, DIRAC_TARGETS, 0)
    inv, _inv_pruned, _labels_inv, _alive_inv = dirac_classify(psi0, DIRAC_TARGETS, 2)
    perm = jax.random.permutation(jax.random.PRNGKey(11), n)
    doomed = jnp.zeros((n,), dtype=bool).at[perm[:b_pruned]].set(True)
    random_pop = sorted(int(x) for x in jnp.unique(labels_a[jnp.logical_not(doomed)]))
    return {"A": a, "B": b, "C": c, "B_pruned": b_pruned, "random": random_pop, "inverted": inv}


def row_survivor_quotient_branch_prune() -> dict[str, Any]:
    n = 320
    raw = jax.random.normal(jax.random.PRNGKey(505), (4 * n, 4), dtype=jnp.float64)
    unit = normalize(raw)
    idx = jnp.nonzero(unit[:, 0] > 0.05, size=n, fill_value=0)[0]
    q0 = unit[idx]
    a, a_pruned, _alive_a = branch_summary(q0, False)
    b, b_pruned, _alive_b = branch_summary(q0, True)
    c, _c_pruned, _alive_c = branch_summary(q0, False)
    return {"A": a, "B": b, "C": c, "B_pruned": b_pruned}


RECOMPUTE = {
    "boundary_environment_cut": row_boundary_environment_cut,
    "nested_hopf_shells": row_nested_hopf_shells,
    "weyl_gamma5_chirality": row_weyl_gamma5_chirality,
    "qit_entropy_information": row_qit_entropy_information,
    "conditional_mutual_information_readout": row_conditional_mutual_information_readout,
    "spectral_triple_dirac": row_spectral_triple_dirac,
    "survivor_quotient_branch_prune": row_survivor_quotient_branch_prune,
}


def compare_metrics(expected: dict[str, Any], actual: dict[str, Any]) -> tuple[bool, float, list[str]]:
    failures: list[str] = []
    max_delta = 0.0
    for key, exp in expected.items():
        act = actual.get(key)
        if isinstance(exp, list):
            if exp and all(isinstance(x, (int, float)) for x in exp) and act and all(isinstance(x, (int, float)) for x in act):
                deltas = [abs(float(a) - float(e)) for a, e in zip(act, exp)] if len(act) == len(exp) else [float("inf")]
                max_delta = max(max_delta, max(deltas) if deltas else 0.0)
                if len(act) != len(exp) or any(d > 1.0e-8 for d in deltas):
                    failures.append(key)
            elif act != exp:
                failures.append(key)
        else:
            delta = abs(float(act) - float(exp))
            max_delta = max(max_delta, delta)
            if delta > 1.0e-8:
                failures.append(key)
    return not failures, max_delta, failures


def row_control_pass(layer_id: str, metrics: dict[str, Any]) -> bool:
    if layer_id == "boundary_environment_cut":
        return metrics["MI_bell"] > 1.9 and abs(metrics["MI_product"]) < EPS and metrics["MI_classical"] > 0.9 and abs(metrics["LN_classical"]) < EPS
    if layer_id == "nested_hopf_shells":
        return metrics["A_basins"] == [1, 2, 3, 4] and metrics["B_basins"] == [1, 2] and metrics["B_pruned"] > 0 and metrics["coupled_alignment_delta"] > metrics["zero_control_alignment_delta"]
    if layer_id == "weyl_gamma5_chirality":
        return metrics["A"] == [1, 2, 3, 4] and metrics["B"] == [1, 2] and metrics["C"] == [1, 2, 3, 4] and metrics["random"] == [1, 2, 3, 4] and metrics["inverted"] == [3, 4]
    if layer_id == "qit_entropy_information":
        return metrics["LN_bell"] > 0.9 and abs(metrics["LN_classical"]) < EPS and abs(metrics["LN_product"]) < EPS and metrics["S_A_given_B_bell"] < -0.9
    if layer_id == "conditional_mutual_information_readout":
        return metrics["CMI_GHZ"] > 0.9 and abs(metrics["CMI_markov_control"]) < EPS and metrics["CMI_classical_shadow"] > 0.9 and abs(metrics["LN_classical_AC"]) < EPS
    if layer_id == "spectral_triple_dirac":
        return metrics["commutator_norm"] > 1.0e-2 and metrics["spectrum"] == [-1.0, -1.0, 1.0, 1.0]
    if layer_id == "survivor_quotient_branch_prune":
        return metrics["A"] == [1, 2, 3, 4] and metrics["B"] == [1, 2] and metrics["C"] == [1, 2, 3, 4] and metrics["B_pruned"] > 0
    return False


def run_audit(write: bool = True) -> dict[str, Any]:
    source = json.loads(SOURCE.read_text())
    by_id = {row["layer_id"]: row for row in source["layer_results"]}
    results = []
    max_delta = 0.0

    for layer_id in TARGET_ROWS:
        recomputed = RECOMPUTE[layer_id]()
        expected = by_id[layer_id]["metrics"]
        metrics_match, delta, failures = compare_metrics(expected, recomputed)
        max_delta = max(max_delta, delta)
        controls_pass = row_control_pass(layer_id, recomputed)
        results.append(
            {
                "layer_id": layer_id,
                "recompute_pass": bool(metrics_match and controls_pass),
                "metrics_match_receipt": bool(metrics_match),
                "independent_controls_pass": bool(controls_pass),
                "max_abs_metric_delta": delta,
                "metric_failures": failures,
                "recomputed_metrics": recomputed,
            }
        )

    all_pass = (
        source.get("executed_track") == "jax"
        and source.get("ran_julia") is False
        and source.get("julia_reference_mode") == "read_only"
        and source.get("promotion_allowed") is False
        and len(results) == len(TARGET_ROWS)
        and all(row["recompute_pass"] for row in results)
        and max_delta < 1.0e-8
    )

    output = {
        "AUDIT_PASS": bool(all_pass),
        "name": "jax_independent_physics_recompute_oracle",
        "classification": "independent_jax_recompute_oracle_diagnostic_only",
        "promotion_allowed": False,
        "executed_track": "jax",
        "ran_julia": False,
        "julia_reference_mode": "read_only",
        "purpose": "Recompute high-risk diagnostic row physics without importing the original suite row functions.",
        "source_receipt": str(SOURCE),
        "rows_checked": len(results),
        "rows_recomputed_pass": sum(1 for row in results if row["recompute_pass"]),
        "max_abs_metric_delta": max_delta,
        "blocked_consumers": source.get("blocked_consumers", []),
        "target_rows": TARGET_ROWS,
        "root_constraints_in_force": {
            "F01": "finite qubit densities, finite S3 branch ensembles, finite Dirac/gamma matrices",
            "N01": "log-negativity/classical controls, gamma5 sign prune, nonzero Dirac commutator, monotone branch/prune order",
        },
        "tool_manifest": {
            "jax": "load-bearing recomputation of finite row physics",
            "jax.numpy": "load-bearing finite linear algebra and density/readout math",
            "jax.lax.scan": "load-bearing branch/prune and nested shell trajectory recomputation",
            "json": "receipt comparison only",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "jax.lax.scan": "load_bearing",
            "json": "supportive",
        },
        "results": results,
    }

    if write:
        OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    return output


def main() -> None:
    result = run_audit(write=True)
    print(
        f"independent_recompute rows={result['rows_checked']} "
        f"pass={result['rows_recomputed_pass']} "
        f"max_delta={result['max_abs_metric_delta']:.3e} "
        f"AUDIT_PASS={result['AUDIT_PASS']}"
    )


if __name__ == "__main__":
    main()
