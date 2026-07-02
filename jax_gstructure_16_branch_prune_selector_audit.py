#!/usr/bin/env python3
"""JAX branch/prune selector audit over the 16 G-structure placements.

This is the JAX scale/audit lane. It runs no Julia, imports no PyTorch, and
does not claim official G-structure selection or manifold admission.

Finite object:

    P = {L,R} x {fiber,base} x {Se,Ne,Ni,Si}

The selector stress-test couples the 16-placement lattice to monotone
branch/prune dynamics on S3 unit-quaternion spinors. The chirality selector is
the sign of q0: L-sheet targets are q0>0, R-sheet targets are q0<0.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp


OUT = Path("jax_gstructure_16_branch_prune_selector_audit_results.json")
N = 4096
STEPS = 5000
DT = 0.002
EPS = 1.0e-10

TOPOLOGIES = ("Se", "Ne", "Ni", "Si")
LEFT_TERRAINS = {"Se": "Funnel", "Ne": "Vortex", "Ni": "Pit", "Si": "Hill"}
RIGHT_TERRAINS = {"Se": "Cannon", "Ne": "Spiral", "Ni": "Source", "Si": "Citadel"}
ALLOWED_LABELS = set(range(1, 9))
FORBIDDEN_LABELS = set(range(9, 17))


@dataclass(frozen=True)
class Placement:
    label: int
    sheet: str
    path: str
    topology: str
    terrain: str
    chern_sign: int
    target: tuple[float, float, float, float]


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def unit(q: jax.Array) -> jax.Array:
    return q / jnp.linalg.norm(q, axis=-1, keepdims=True)


def qrot(q: jax.Array) -> jax.Array:
    q = q / jnp.linalg.norm(q)
    w, x, y, z = q
    return jnp.asarray(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=jnp.float64,
    )


def spinor_raw(phi: jax.Array, chi: jax.Array, eta: jax.Array) -> jax.Array:
    z1 = jnp.exp(1j * (phi + chi)) * jnp.cos(eta)
    z2 = jnp.exp(1j * (phi - chi)) * jnp.sin(eta)
    return jnp.asarray([z1, z2], dtype=jnp.complex128)


def spinor_to_q(psi: jax.Array) -> jax.Array:
    return unit(jnp.asarray([jnp.real(psi[0]), jnp.imag(psi[0]), jnp.real(psi[1]), jnp.imag(psi[1])], dtype=jnp.float64))


def density_from_q(q: jax.Array) -> jax.Array:
    q = unit(q)
    psi = jnp.asarray([q[0] + 1j * q[1], q[2] + 1j * q[3]], dtype=jnp.complex128)
    return jnp.outer(psi, psi.conj())


def initial_params(sheet: str) -> tuple[float, float, float]:
    if sheet == "L":
        return 0.23, -0.41, 0.47
    return -0.19, 0.62, 0.71


def path_q(sheet: str, path: str, u: jax.Array) -> jax.Array:
    phi0, chi0, eta0 = initial_params(sheet)
    if path == "fiber":
        phi = phi0 + u
        chi = chi0
    elif path == "base":
        phi = phi0 - jnp.cos(2.0 * eta0) * u
        chi = chi0 + u
    else:
        raise ValueError(path)
    return spinor_to_q(spinor_raw(phi, chi, eta0))


def path_phase_coords(sheet: str, path: str, u: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    phi0, chi0, eta0 = initial_params(sheet)
    if path == "fiber":
        return phi0 + u, jnp.asarray(chi0), jnp.asarray(eta0)
    if path == "base":
        return phi0 - jnp.cos(2.0 * eta0) * u, chi0 + u, jnp.asarray(eta0)
    raise ValueError(path)


def path_metrics(sheet: str, path: str) -> dict[str, float]:
    q0 = path_q(sheet, path, 0.0)
    q1 = path_q(sheet, path, 1.0)
    rho_delta = jnp.linalg.norm(density_from_q(q1) - density_from_q(q0))
    phi_a, chi_a, eta0 = path_phase_coords(sheet, path, 0.0)
    phi_b, chi_b, _ = path_phase_coords(sheet, path, 1.0)
    phidot = phi_b - phi_a
    chidot = chi_b - chi_a
    connection_value = phidot + jnp.cos(2.0 * eta0) * chidot
    horizontal_residual = jnp.where(path == "base", jnp.abs(connection_value), jnp.asarray(0.0))
    fiber_vertical_connection = jnp.where(path == "fiber", jnp.abs(connection_value), jnp.asarray(0.0))
    return {
        "density_delta": _f(rho_delta),
        "horizontal_connection_residual": _f(jnp.abs(horizontal_residual)),
        "fiber_vertical_connection_abs": _f(fiber_vertical_connection),
        "connection_value": _f(connection_value),
    }


def placements() -> list[Placement]:
    rows: list[Placement] = []
    label = 1
    for sheet, terrains in (("L", LEFT_TERRAINS), ("R", RIGHT_TERRAINS)):
        q0 = 0.5 if sheet == "L" else -0.5
        chern = 1 if sheet == "L" else -1
        for path_bit, path in enumerate(("fiber", "base")):
            for topo_i, topology in enumerate(TOPOLOGIES):
                s1 = 0.5 if path_bit == 0 else -0.5
                s2 = 0.5 if (topo_i & 1) == 0 else -0.5
                s3 = 0.5 if (topo_i & 2) == 0 else -0.5
                rows.append(Placement(label, sheet, path, topology, terrains[topology], chern, (q0, s1, s2, s3)))
                label += 1
    return rows


PLACEMENTS = placements()
TARGETS = jnp.asarray([row.target for row in PLACEMENTS], dtype=jnp.float64)
CHERN_BY_LABEL = jnp.asarray([row.chern_sign for row in PLACEMENTS], dtype=jnp.int32)


def initial_ensemble() -> jax.Array:
    key = jax.random.PRNGKey(20260602)
    q = jax.random.normal(key, (N, 4), dtype=jnp.float64)
    return unit(q)


@jax.jit
def evolve(prune_code: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    q0 = initial_ensemble()
    alive0 = jnp.ones((N,), dtype=bool)

    def step(carry: tuple[jax.Array, jax.Array], _: Any) -> tuple[tuple[jax.Array, jax.Array], jax.Array]:
        q, alive = carry
        nearest = TARGETS[jnp.argmax(q @ TARGETS.T, axis=1)]
        flow = 2.0 * (nearest - jnp.sum(nearest * q, axis=1, keepdims=True) * q)
        q_next = unit(q + DT * flow)
        killed_negative = q_next[:, 0] < -0.01
        killed_positive = q_next[:, 0] > 0.01
        killed = jnp.where(prune_code == 1, killed_negative, jnp.where(prune_code == 3, killed_positive, False))
        alive_next = alive & ~killed
        drift = jnp.max(jnp.abs(jnp.linalg.norm(q_next, axis=1) - 1.0))
        return (q_next, alive_next), drift

    (qf, alive), drifts = jax.lax.scan(step, (q0, alive0), None, length=STEPS)
    labels = 1 + jnp.argmax(qf @ TARGETS.T, axis=1)
    return qf, alive, labels, drifts


def populated(labels: jax.Array, alive: jax.Array) -> list[int]:
    values = jnp.unique(labels[alive], size=16, fill_value=-1)
    return [int(x) for x in jax.device_get(values) if int(x) > 0]


def run_one(name: str, code: int) -> dict[str, Any]:
    qf, alive, labels, drifts = evolve(jnp.asarray(code, dtype=jnp.int32))
    pop = populated(labels, alive)
    survivor_count = int(jax.device_get(jnp.sum(alive)))
    survivor_labels = labels[alive]
    survivor_chern = CHERN_BY_LABEL[survivor_labels - 1] if survivor_count else jnp.asarray([], dtype=jnp.int32)
    q_surv = qf[alive] if survivor_count else qf[:0]
    if survivor_count:
        double_cover_gap = jax.vmap(lambda q: jnp.linalg.norm(qrot(q) - qrot(-q)))(q_surv)
        max_double_cover_gap = jnp.max(double_cover_gap)
        mean_q0 = jnp.mean(q_surv[:, 0])
    else:
        max_double_cover_gap = jnp.asarray(float("nan"))
        mean_q0 = jnp.asarray(float("nan"))
    return {
        "name": name,
        "populated": pop,
        "survivors": survivor_count,
        "pruned": int(N - survivor_count),
        "max_norm_drift": _f(jnp.max(drifts)),
        "max_double_cover_gap": _f(max_double_cover_gap) if survivor_count else None,
        "survivor_chern_signs": sorted(int(x) for x in jax.device_get(jnp.unique(survivor_chern))) if survivor_count else [],
        "mean_survivor_q0": _f(mean_q0) if survivor_count else None,
    }


def random_rate_matched_population(pruned: int) -> dict[str, Any]:
    qf, _, labels, _ = evolve(jnp.asarray(0, dtype=jnp.int32))
    del qf
    key = jax.random.PRNGKey(17)
    perm = jax.random.permutation(key, N)
    killed = jnp.zeros((N,), dtype=bool).at[perm[:pruned]].set(True)
    alive = ~killed
    pop = populated(labels, alive)
    return {"populated": pop, "survivors": int(jax.device_get(jnp.sum(alive))), "pruned": int(pruned)}


def c1(sign: int) -> float:
    n = 4096
    theta = (jnp.arange(n, dtype=jnp.float64) + 0.5) * jnp.pi / n
    val = sign * jnp.sum(0.5 * jnp.sin(theta) * (jnp.pi / n) * (2.0 * jnp.pi)) / (2.0 * jnp.pi)
    return _f(val)


def path_table_checks() -> dict[str, Any]:
    rows = []
    for placement in PLACEMENTS:
        metrics = path_metrics(placement.sheet, placement.path)
        if placement.path == "fiber":
            ok = metrics["density_delta"] < 1.0e-9 and metrics["fiber_vertical_connection_abs"] > 0.9
        else:
            ok = metrics["density_delta"] > 0.2 and metrics["horizontal_connection_residual"] < 1.0e-12
        rows.append({"label": placement.label, "path": placement.path, "pass": ok, **metrics})
    return {
        "rows": rows,
        "all_base_horizontal": all(row["horizontal_connection_residual"] < 1.0e-12 for row in rows if row["path"] == "base"),
        "all_fiber_vertical": all(row["fiber_vertical_connection_abs"] > 0.9 for row in rows if row["path"] == "fiber"),
        "all_fiber_density_invariant": all(row["density_delta"] < 1.0e-9 for row in rows if row["path"] == "fiber"),
        "all_pass": all(row["pass"] for row in rows),
    }


def run_probe(write: bool = True) -> dict[str, Any]:
    run_a = run_one("A_no_prune", 0)
    run_b = run_one("B_chirality_prune", 1)
    run_c = run_one("C_trivial_control", 2)
    run_inv = run_one("D_inverted_sign_prune", 3)
    run_rand = random_rate_matched_population(run_b["pruned"])
    paths = path_table_checks()
    c_plus = c1(+1)
    c_minus = c1(-1)
    target_labels = {row.label for row in PLACEMENTS}
    allowed = ALLOWED_LABELS
    forbidden = FORBIDDEN_LABELS
    a_set = set(run_a["populated"])
    b_set = set(run_b["populated"])
    c_set = set(run_c["populated"])
    inv_set = set(run_inv["populated"])
    rand_set = set(run_rand["populated"])
    checks = {
        "sixteen_targets_exist": set(range(1, 17)) == target_labels,
        "A_populates_all_16_placements": a_set == target_labels,
        "B_kills_forbidden_R_sheet_for_every_path_topology": b_set == allowed and not (b_set & forbidden),
        "B_preserves_all_allowed_L_sheet_placements": allowed <= b_set,
        "C_noop_matches_A": c_set == a_set and run_c["pruned"] == 0,
        "random_rate_matched_prune_keeps_forbidden": forbidden <= rand_set,
        "inverted_sign_flips_to_forbidden_side": inv_set == forbidden and not (inv_set & allowed),
        "real_chirality_prune_fired": run_b["pruned"] > 0 and run_a["pruned"] == 0,
        "bookkeeping_consistent": all(run["survivors"] == N - run["pruned"] for run in (run_a, run_b, run_c, run_inv, run_rand)),
        "spin3_s3_norm_and_double_cover_survive": (
            max(run["max_norm_drift"] for run in (run_a, run_b, run_c, run_inv)) < 1.0e-12
            and max(run["max_double_cover_gap"] or 0.0 for run in (run_a, run_b, run_c, run_inv)) < 1.0e-12
        ),
        "base_paths_horizontal_and_fiber_paths_invariant": paths["all_pass"],
        "survivor_chern_sign_stable": run_b["survivor_chern_signs"] == [1] and run_inv["survivor_chern_signs"] == [-1],
        "u1_chern_signs_measured": abs(c_plus - 1.0) < 1.0e-7 and abs(c_minus + 1.0) < 1.0e-7,
        "no_julia_execution": True,
        "no_pytorch_execution": True,
        "promotion_blocked": True,
    }
    result = {
        "AUDIT_PASS": all(checks.values()),
        "name": "jax_gstructure_16_branch_prune_selector_audit",
        "classification": "diagnostic_jax_gstructure_16_branch_prune_selector_audit",
        "executed_track": "jax",
        "ran_julia": False,
        "ran_pytorch": False,
        "julia_reference_mode": "read_only_external_reference_only",
        "legacy_tensor_lane_used": False,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_boundary": "JAX diagnostic selector over 16 placements; no official G-structure selection, layer completion, stacking, Axis0, flux, bridge, or physics admission.",
        "root_constraints_in_force": {
            "F01": "finite 16-placement target set, finite branch ensemble, finite S3 retraction steps, finite Chern quadrature",
            "N01": "monotone chirality/event latch, noncommuting target flow geometry, sheet-sign selector controls",
        },
        "domain": "finite S3 unit-quaternion branch ensemble with 16 placement attractors",
        "codomain_or_output": "survivor placement basins under no-prune, chirality-prune, no-op, random, and inverted-sign controls",
        "finite_map": "16 placement targets x Spin(3)/SU(2) quaternion path -> monotone selector prune -> survivor placement basins plus path/Chern controls",
        "placement_targets": [
            {
                "label": p.label,
                "sheet": p.sheet,
                "path": p.path,
                "topology": p.topology,
                "terrain": p.terrain,
                "chern_sign": p.chern_sign,
                "target": list(p.target),
            }
            for p in PLACEMENTS
        ],
        "runs": {
            "A": run_a,
            "B": run_b,
            "C": run_c,
            "random_rate_matched": run_rand,
            "inverted": run_inv,
        },
        "path_table": paths,
        "chern": {"c1_plus": c_plus, "c1_minus": c_minus, "trivial_c1": 0.0},
        "checks": checks,
        "tool_manifest": {
            "jax": "load-bearing finite branch ensemble, random controls, JIT/lax.scan retraction dynamics",
            "jax.numpy": "load-bearing finite quaternion, basin, Chern, and path-control readouts",
            "json": "supportive receipt serialization",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "json": "supportive",
        },
        "blocked_consumers": [
            "official_g_structure_selection",
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
            "This couples branch/prune to the 16-placement selector, but remains a JAX diagnostic rather than Julia-native G-structure truth.",
            "The random rate-matched control keeps forbidden placements, so the chirality selector is not just deleting many futures generically.",
            "The inverted-sign control flips survivors to the R/forbidden side.",
        ],
    }
    if write:
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    result = run_probe(write=True)
    runs = result["runs"]
    print(
        "jax_gstructure_16_branch_prune_selector "
        f"A={runs['A']['populated']} B={runs['B']['populated']} "
        f"C={runs['C']['populated']} random={runs['random_rate_matched']['populated']} "
        f"inverted={runs['inverted']['populated']} AUDIT_PASS={result['AUDIT_PASS']}"
    )


if __name__ == "__main__":
    main()
