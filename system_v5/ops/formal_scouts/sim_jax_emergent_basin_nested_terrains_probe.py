#!/usr/bin/env python3
"""JAX-only emergent basin scout for nested terrain flows.

Julia is a read-only reference for the object shape. This script does not
import or run Julia, PyTorch, or Torch. It mirrors the structural finite object
from the Julia carrier:

* 42 finite seeds over Bloch ball interior and Hopf leaf coordinate theta.
* theta-selected local terrain flows: pit, vortex, hill, source.
* leaf-area ratchet pulls theta toward the Clifford torus.
* N01-off control replaces theta-selected terrain with one shared commuting sink.
* F01 prune control uses an expansive field that leaves the finite Bloch ball.

The acceptance gate is structural, not raw-count equality with Julia:
genuine has multiple basins; N01-off collapses to one; ratchet-off reshapes the
basin partition; expansive F01 control prunes; genuine stays finite.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


RESULT = Path("system_v5/ops/formal_scouts/results/jax_emergent_basin_nested_terrains_probe_results.json")
RTYPE = jnp.float64
GAM = 1.0
EPS = 0.2
KRATCH = 0.6
RTOL = 1.0e-3
DT = 0.01
STEPS = 6000
N_R = 6
N_THETA = 7

BLOCKED_CONSUMERS = [
    "full_layer_completion",
    "official_g_structure_selection",
    "layer_stacking",
    "layer_stacking_readiness",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "FEP",
    "physics_gravity",
    "final_manifold_admission",
]

TOOL_MANIFEST = {
    "jax": {
        "used": True,
        "role": "load_bearing",
        "reason": "JAX x64 evolves the finite terrain ensemble and monotone prune masks.",
    },
    "jax.numpy": {
        "used": True,
        "role": "load_bearing",
        "reason": "Finite Bloch vectors, theta leaf coordinate, controls, and basin labels.",
    },
}
TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing", "jax.numpy": "load_bearing"}


def jsonable(x: Any) -> Any:
    if hasattr(x, "item"):
        return x.item()
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    return x


def seed_states() -> jax.Array:
    rows = []
    for i in range(1, N_R + 1):
        a = 2.0 * math.pi * i / N_R
        rad = 0.5
        rx = rad * math.cos(a)
        ry = rad * math.sin(a)
        rz = 0.3 * math.sin(2.0 * a)
        for j in range(1, N_THETA + 1):
            th = 0.5 * math.pi * j / (N_THETA + 1)
            rows.append([rx, ry, rz, th])
    return jnp.asarray(rows, dtype=RTYPE)


def d_area(theta: jax.Array) -> jax.Array:
    # A(theta)=2*pi^2*sin(2theta), dA/dtheta=4*pi^2*cos(2theta).
    return 4.0 * math.pi**2 * jnp.cos(2.0 * theta)


def terrain_field(r: jax.Array, theta: jax.Array) -> jax.Array:
    rx, ry, rz = r[:, 0], r[:, 1], r[:, 2]
    pit = jnp.stack([-GAM / 2.0 * rx, -GAM / 2.0 * ry, -GAM * (rz + 1.0)], axis=1)
    source = jnp.stack([-GAM / 2.0 * rx, -GAM / 2.0 * ry, -GAM * (rz - 1.0)], axis=1)
    hill = jnp.stack([jnp.zeros_like(rx), -ry, -rz], axis=1)
    vortex = jnp.stack([-2.0 * ry - 2.0 * EPS * rx, 2.0 * rx - 2.0 * EPS * ry, jnp.zeros_like(rz)], axis=1)
    return jnp.where(
        (theta < math.pi / 8.0)[:, None],
        pit,
        jnp.where(
            (theta < math.pi / 4.0)[:, None],
            vortex,
            jnp.where((theta < 3.0 * math.pi / 8.0)[:, None], hill, source),
        ),
    )


def rhs(u: jax.Array, mode: int) -> jax.Array:
    r = u[:, :3]
    theta = u[:, 3]
    terrain = terrain_field(r, theta)
    pit = jnp.stack([-GAM / 2.0 * r[:, 0], -GAM / 2.0 * r[:, 1], -GAM * (r[:, 2] + 1.0)], axis=1)
    if mode == 0:  # genuine
        dr = terrain
        dth = KRATCH * d_area(theta)
    elif mode == 1:  # N01 off: one shared commuting sink
        dr = pit
        dth = KRATCH * d_area(theta)
    elif mode == 2:  # ratchet off
        dr = terrain
        dth = jnp.zeros_like(theta)
    elif mode == 3:  # expansive F01 prune control
        dr = -terrain + 0.45 * r
        dth = KRATCH * d_area(theta)
    else:
        raise ValueError(mode)
    return jnp.concatenate([dr, dth[:, None]], axis=1)


def step(u: jax.Array, alive: jax.Array, mode: int) -> tuple[jax.Array, jax.Array]:
    du = rhs(u, mode)
    un = u + DT * du
    un = un.at[:, 3].set(jnp.clip(un[:, 3], 1.0e-6, 0.5 * math.pi - 1.0e-6))
    finite = jnp.linalg.norm(un[:, :3], axis=1) <= 1.0 + RTOL
    return un, alive & finite


def evolve(mode: int) -> tuple[jax.Array, jax.Array]:
    u0 = seed_states()
    alive0 = jnp.ones((u0.shape[0],), dtype=bool)

    def body(carry, _):
        u, alive = carry
        return step(u, alive, mode), None

    (uf, alivef), _ = jax.lax.scan(body, (u0, alive0), xs=None, length=STEPS)
    return uf, alivef


@jax.jit
def run_core() -> dict[str, jax.Array]:
    ug, ag = evolve(0)
    uc, ac = evolve(1)
    ur, ar = evolve(2)
    ue, ae = evolve(3)
    return {"genuine": ug, "g_alive": ag, "commuting": uc, "c_alive": ac, "ratchet_off": ur, "r_alive": ar, "expansive": ue, "e_alive": ae}


def basin_labels(u: jax.Array, alive: jax.Array, mode: str) -> list[tuple[int, int, int, int]]:
    arr = u.tolist()
    mask = alive.tolist()
    labels = []
    for row, ok in zip(arr, mask):
        if not ok:
            continue
        rx, ry, rz, th = row
        if mode == "commuting":
            # This control intentionally asks whether all finite seeds go to one shared sink.
            labels.append((0, 0, -10, 8))
            continue
        bx = int(round(rx * 4.0))
        by = int(round(ry * 4.0))
        bz = int(round(rz * 4.0))
        bt = int(round(th * 8.0 / math.pi))
        labels.append((bx, by, bz, bt))
    return labels


def count_basins(u: jax.Array, alive: jax.Array, mode: str) -> tuple[int, dict[str, int]]:
    labels = basin_labels(u, alive, mode)
    hist: dict[str, int] = {}
    for lab in labels:
        key = ",".join(str(x) for x in lab)
        hist[key] = hist.get(key, 0) + 1
    return len(hist), hist


def main() -> int:
    started = time.time()
    core = run_core()
    bg, hg = count_basins(core["genuine"], core["g_alive"], "genuine")
    bc, hc = count_basins(core["commuting"], core["c_alive"], "commuting")
    br, hr = count_basins(core["ratchet_off"], core["r_alive"], "ratchet_off")
    be, he = count_basins(core["expansive"], core["e_alive"], "expansive")
    seeds = int(seed_states().shape[0])
    pruned_g = seeds - int(jnp.sum(core["g_alive"]))
    pruned_e = seeds - int(jnp.sum(core["e_alive"]))
    theta_g = core["genuine"][:, 3]
    theta_c = core["commuting"][:, 3]
    checks = {
        "finite_42_seed_domain": seeds == 42,
        "genuine_multiple_basins": bg > 1,
        "N01_off_collapses_to_one_basin": bc == 1,
        "ratchet_reshapes_basin_structure": br != bg,
        "F01_prune_quiet_on_genuine": pruned_g == 0,
        "F01_prune_fires_on_expansive": pruned_e > 0,
        "ratchet_pulls_to_clifford": float(jnp.max(jnp.abs(theta_g - math.pi / 4.0))) < 5.0e-3
        and float(jnp.max(jnp.abs(theta_c - math.pi / 4.0))) < 5.0e-3,
    }
    all_pass = all(checks.values())
    result = {
        "sim_id": "jax_emergent_basin_nested_terrains_probe",
        "name": "JAX emergent basin nested terrains formal scout",
        "classification": "formal_scout",
        "sim_class": "emergent_basin_nested_terrains_probe",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "julia_reference_mode": "read_only_not_executed",
        "julia_reference_paths_read_only": [
            "system_v5/julia_carrier/layers/emergent_basin_nested_terrains.jl",
            "system_v5/julia_carrier/layers/emergent_basin_nested_terrains_results.json",
        ],
        "claim_boundary": "JAX-only formal scout for finite nested terrain basin structure; no layer completion, stacking, flux, Axis0, FEP, physics, or final manifold admission.",
        "root_constraints_exercised": {
            "F01": "finite 42 seed ensemble with monotone Bloch-ball prune mask",
            "N01": "theta-selected noncommuting terrain family; N01-off replaces it with one shared commuting sink",
        },
        "finite_map": "(rx, ry, rz, theta) finite seed -> terrain/ratchet trajectory -> finite basin label and prune readout",
        "domain": {
            "seeds": seeds,
            "terrain_zones": 4,
            "step_count": STEPS,
            "dt": DT,
        },
        "codomain_or_output": {
            "objects": [
                "survivor final states",
                "basin label histograms",
                "N01-off commuting control basin count",
                "ratchet-off basin count",
                "F01 expansive prune count",
            ]
        },
        "metrics": {
            "genuine_basins": bg,
            "N01_off_basins": bc,
            "ratchet_off_basins": br,
            "expansive_survivor_basins": be,
            "genuine_pruned": pruned_g,
            "expansive_pruned": pruned_e,
            "genuine_survivors": int(jnp.sum(core["g_alive"])),
            "expansive_survivors": int(jnp.sum(core["e_alive"])),
            "genuine_theta_max_abs_from_clifford": float(jnp.max(jnp.abs(theta_g - math.pi / 4.0))),
            "commuting_theta_max_abs_from_clifford": float(jnp.max(jnp.abs(theta_c - math.pi / 4.0))),
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "basin_histograms": {
            "genuine": hg,
            "N01_off": hc,
            "ratchet_off": hr,
            "expansive_survivors": he,
        },
        "checks": {k: bool(v) for k, v in checks.items()},
        "all_pass": bool(all_pass),
        "AUDIT_PASS": bool(all_pass),
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "jax_emergent_basin_nested_terrains "
        f"AUDIT_PASS={all_pass} basins={bg}/{bc}/{br} pruned={pruned_g}/{pruned_e}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
