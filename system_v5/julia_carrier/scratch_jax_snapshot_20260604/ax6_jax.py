#!/usr/bin/env python3
"""Axis 6 finite noncommutation-pressure map, JAX implementation.

This is a bounded receipt, not a layer-completion or bridge claim.
"""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

import jax
import jax.numpy as jnp


OUT = Path("/tmp/ax6_jax_results.json")
DTYPE = jnp.complex128
RTYPE = jnp.float64
EPS = 1.0e-10

I2 = jnp.eye(2, dtype=DTYPE)
X = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=DTYPE)
Z = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=DTYPE)
PZ_PLUS = (I2 + Z) / 2.0
PZ_MINUS = (I2 - Z) / 2.0
PX_PLUS = (I2 + X) / 2.0
PX_MINUS = (I2 - X) / 2.0

SHELL_RADII = (0.6, 1.0)
N_PHI = 6
N_CHI = 6
N_ETA = 4


def scalar(x: Any) -> float:
    return float(jax.device_get(jnp.real(x)))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite_sites() -> jax.Array:
    rows: list[tuple[float, float, float, float]] = []
    for radius in SHELL_RADII:
        for i in range(N_PHI):
            phi = 2.0 * math.pi * i / N_PHI
            for j in range(N_CHI):
                chi = 2.0 * math.pi * j / N_CHI
                for k in range(N_ETA):
                    eta = 0.5 * math.pi * (k + 0.5) / N_ETA
                    rows.append((radius, phi, chi, eta))
    return jnp.asarray(rows, dtype=RTYPE)


def weyl_spinor(phi: jax.Array, chi: jax.Array, eta: jax.Array, sheet_sign: float) -> jax.Array:
    psi = jnp.stack(
        [
            jnp.exp(1j * (phi + sheet_sign * chi)) * jnp.cos(eta),
            jnp.exp(1j * (phi - sheet_sign * chi)) * jnp.sin(eta),
        ],
        axis=-1,
    ).astype(DTYPE)
    norm = jnp.sqrt(jnp.sum(jnp.abs(psi) ** 2, axis=-1, keepdims=True))
    return psi / norm


def density_batch(psi: jax.Array) -> jax.Array:
    return psi[:, :, None] * jnp.conj(psi[:, None, :])


def build_lr_density_carrier(sites: jax.Array) -> tuple[jax.Array, jax.Array]:
    radius = sites[:, 0]
    phi = sites[:, 1]
    chi = sites[:, 2]
    eta = sites[:, 3] * radius
    rho_l = density_batch(weyl_spinor(phi, chi, eta, +1.0))
    rho_r = density_batch(weyl_spinor(phi, chi, eta, -1.0))
    return rho_l, rho_r


def density_validity(all_rho: jax.Array) -> dict[str, Any]:
    dag = jnp.conj(jnp.swapaxes(all_rho, -1, -2))
    hermitian_errors = jnp.sqrt(jnp.sum(jnp.abs(all_rho - dag) ** 2, axis=(1, 2)))
    trace_errors = jnp.abs(jnp.trace(all_rho, axis1=1, axis2=2) - 1.0)
    hermitian = (all_rho + dag) / 2.0
    eigenvalues = jnp.linalg.eigvalsh(hermitian)
    max_trace_error = scalar(jnp.max(trace_errors))
    max_hermitian_error = scalar(jnp.max(hermitian_errors))
    min_eigenvalue = scalar(jnp.min(eigenvalues))
    return {
        "max_trace_error": max_trace_error,
        "max_hermitian_error": max_hermitian_error,
        "min_eigenvalue": min_eigenvalue,
        "all_valid_density_matrices": bool(
            max_trace_error <= 1.0e-12
            and max_hermitian_error <= 1.0e-12
            and min_eigenvalue >= -1.0e-12
        ),
    }


def rotation(axis: jax.Array, theta: float) -> jax.Array:
    return jnp.cos(theta / 2.0) * I2 - 1j * jnp.sin(theta / 2.0) * axis


def operators() -> dict[str, jax.Array]:
    return {
        "Ti": Z,
        "Te": X,
        "Fi": rotation(X, 0.7),
        "Fe": rotation(Z, 0.7),
    }


def terrain_generators() -> dict[str, jax.Array]:
    return {
        "TerrainZ": Z,
        "TerrainX": X,
    }


def terrain_z_channel(rho: jax.Array, tau: float = 0.5) -> jax.Array:
    pinched = PZ_PLUS @ rho @ PZ_PLUS + PZ_MINUS @ rho @ PZ_MINUS
    return (1.0 - tau) * rho + tau * pinched


def terrain_x_channel(rho: jax.Array, tau: float = 0.5) -> jax.Array:
    pinched = PX_PLUS @ rho @ PX_PLUS + PX_MINUS @ rho @ PX_MINUS
    return (1.0 - tau) * rho + tau * pinched


def terrain_channels() -> dict[str, Callable[[jax.Array], jax.Array]]:
    return {
        "TerrainZ": terrain_z_channel,
        "TerrainX": terrain_x_channel,
    }


def operator_channels(ops: dict[str, jax.Array]) -> dict[str, Callable[[jax.Array], jax.Array]]:
    return {
        "Ti": terrain_z_channel,
        "Te": terrain_x_channel,
        "Fi": lambda rho: unitary_action(ops["Fi"], rho),
        "Fe": lambda rho: unitary_action(ops["Fe"], rho),
    }


def fro_norm(matrix: jax.Array) -> float:
    return scalar(jnp.linalg.norm(matrix))


def commutator_pressure(a: jax.Array, b: jax.Array, rho: jax.Array) -> float:
    return fro_norm((a @ b - b @ a) @ rho)


def left_order_gap(a: jax.Array, b: jax.Array, rho: jax.Array) -> float:
    return fro_norm(a @ (b @ rho) - b @ (a @ rho))


def unitary_action(u: jax.Array, rho: jax.Array) -> jax.Array:
    return u @ rho @ jnp.conj(u.T)


def channel_order_gap(
    first: Callable[[jax.Array], jax.Array],
    second: Callable[[jax.Array], jax.Array],
    rho: jax.Array,
) -> float:
    return fro_norm(first(second(rho)) - second(first(rho)))


def terrain_channel_order_gap(
    terrain_fn: Callable[[jax.Array], jax.Array],
    op: jax.Array,
    rho: jax.Array,
) -> float:
    return fro_norm(terrain_fn(unitary_action(op, rho)) - unitary_action(op, terrain_fn(rho)))


def pair_entry(a_name: str, a: jax.Array, b_name: str, b: jax.Array, rho: jax.Array) -> dict[str, Any]:
    pressure = commutator_pressure(a, b, rho)
    gap = left_order_gap(a, b, rho)
    return {
        "lhs": a_name,
        "rhs": b_name,
        "commutator_pressure": pressure,
        "order_gap": gap,
        "pressure_class": "low" if pressure <= EPS else "high",
    }


def build_payload() -> dict[str, Any]:
    sites = finite_sites()
    rho_l, rho_r = build_lr_density_carrier(sites)
    all_rho = jnp.concatenate([rho_l, rho_r], axis=0)
    rho_eval = jnp.mean(all_rho, axis=0)

    if int(sites.shape[0]) != len(SHELL_RADII) * N_PHI * N_CHI * N_ETA:
        raise AssertionError("F01 site count mismatch")
    if not bool(jax.device_get(jnp.all(jnp.isfinite(jnp.real(all_rho))))):
        raise AssertionError("F01 nonfinite real density component")
    if not bool(jax.device_get(jnp.all(jnp.isfinite(jnp.imag(all_rho))))):
        raise AssertionError("F01 nonfinite imag density component")
    density_stats = density_validity(all_rho)
    if not density_stats["all_valid_density_matrices"]:
        raise AssertionError("F01 density validity violation")

    ops = operators()
    terrains = terrain_generators()
    terrain_fns = terrain_channels()
    op_channels = operator_channels(ops)
    op_names = ("Ti", "Te", "Fi", "Fe")

    operator_pairs: dict[str, dict[str, Any]] = {}
    for i, left_name in enumerate(op_names):
        for right_name in op_names[i + 1 :]:
            key = f"{left_name}_{right_name}"
            entry = pair_entry(left_name, ops[left_name], right_name, ops[right_name], rho_eval)
            entry["left_action_order_gap"] = entry["order_gap"]
            entry["order_gap"] = channel_order_gap(op_channels[left_name], op_channels[right_name], rho_eval)
            entry["order_gap_definition"] = "density-channel composition ||A(B(rho))-B(A(rho))||_F"
            operator_pairs[key] = entry

    terrain_operator_pairs: dict[str, dict[str, Any]] = {}
    for terrain_name, terrain_matrix in terrains.items():
        for op_name in op_names:
            key = f"{terrain_name}_{op_name}"
            entry = pair_entry(terrain_name, terrain_matrix, op_name, ops[op_name], rho_eval)
            channel_gap = terrain_channel_order_gap(terrain_fns[terrain_name], ops[op_name], rho_eval)
            entry["left_action_order_gap"] = entry["order_gap"]
            entry["order_gap"] = channel_gap
            entry["order_gap_definition"] = "terrain channel versus operator channel composition ||T(O(rho))-O(T(rho))||_F"
            entry["channel_order_gap"] = channel_gap
            entry["channel_pressure_class"] = "low" if channel_gap <= EPS else "high"
            terrain_operator_pairs[key] = entry

    monotone_vector: dict[str, float] = {}
    for key, value in operator_pairs.items():
        monotone_vector[f"operator_pair:{key}:commutator_pressure"] = value["commutator_pressure"]
        monotone_vector[f"operator_pair:{key}:order_gap"] = value["order_gap"]
    for key, value in terrain_operator_pairs.items():
        monotone_vector[f"terrain_operator:{key}:commutator_pressure"] = value["commutator_pressure"]
        monotone_vector[f"terrain_operator:{key}:order_gap"] = value["order_gap"]
        monotone_vector[f"terrain_operator:{key}:channel_order_gap"] = value["channel_order_gap"]

    split_inputs = {
        f"operator_pair:{key}": value["commutator_pressure"]
        for key, value in operator_pairs.items()
    }
    split_inputs.update(
        {
            f"terrain_operator:{key}": value["commutator_pressure"]
            for key, value in terrain_operator_pairs.items()
        }
    )
    high = sorted(key for key, value in split_inputs.items() if value > EPS)
    low = sorted(key for key, value in split_inputs.items() if value <= EPS)

    per_site_pressure = jnp.asarray([commutator_pressure(ops["Ti"], ops["Fi"], rho) for rho in all_rho], dtype=RTYPE)
    median_pressure = scalar(jnp.median(per_site_pressure))
    per_site_high = int(jax.device_get(jnp.sum(per_site_pressure > median_pressure)))
    per_site_low = int(jax.device_get(jnp.sum(per_site_pressure <= median_pressure)))

    expected_zero = {
        "operator_pair:Ti_Fe",
        "operator_pair:Te_Fi",
        "terrain_operator:TerrainZ_Ti",
        "terrain_operator:TerrainZ_Fe",
        "terrain_operator:TerrainX_Te",
        "terrain_operator:TerrainX_Fi",
    }
    expected_nonzero = {
        "operator_pair:Ti_Te",
        "operator_pair:Ti_Fi",
        "operator_pair:Te_Fe",
        "operator_pair:Fi_Fe",
        "terrain_operator:TerrainZ_Te",
        "terrain_operator:TerrainZ_Fi",
        "terrain_operator:TerrainX_Ti",
        "terrain_operator:TerrainX_Fe",
    }
    n01_pass = (
        expected_zero.issubset(set(low))
        and expected_nonzero.issubset(set(high))
        and operator_pairs["Ti_Fe"]["commutator_pressure"] <= EPS
        and operator_pairs["Te_Fi"]["commutator_pressure"] <= EPS
        and operator_pairs["Ti_Fi"]["commutator_pressure"] > EPS
        and operator_pairs["Te_Fe"]["commutator_pressure"] > EPS
    )

    return {
        "object_id": "ax6_noncommutation_pressure_jax",
        "engine": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__)),
        "source_sha256": sha256_file(Path(__file__)),
        "run_command": "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 /tmp/ax6_jax.py",
        "claim_ceiling": "bounded finite-map receipt; not layer-complete; not bridge",
        "promotion_allowed": False,
        "root_constraints_in_force": [
            "F01: finite carrier/probe/operator/path set",
            "N01: noncommuting/order-sensitive operator control",
        ],
        "finite_map": {
            "domain": "finite L/R Weyl spinor density matrices on 2 shell radii x 6 phi x 6 chi x 4 eta sites, plus finite operator and terrain-generator pairs",
            "codomain_or_output": "named noncommutation-pressure monotone vector and high/low Axis-6 pressure split",
            "rho_evaluation": "mean over all L and R local density matrices",
            "axis6_action_side": "left-action commutator pressure plus density-channel composition order gap",
            "closure_type": "composition",
        },
        "carrier_realization": "JAX complex128 L/R Weyl spinor-derived 2x2 density matrices",
        "spinor_state": "psi_L/R(phi,chi,eta) = [exp(i(phi +/- chi)) cos(eta), exp(i(phi -/+ chi)) sin(eta)] normalized; rho = psi psi^dagger",
        "peps3d_embedding": "finite local-cell anchor only: each shell/phi/chi/eta site is treated as a bounded PEPS3D-carried spinor-density cell; no downstream PEPS3D closure claim",
        "downstream_blocks": ["full layer completion", "Axis0", "flux", "bridge", "physics"],
        "operator_basis": {
            "Ti": "z-basis generator Z",
            "Fe": "z-basis rotation exp(-i 0.7 Z/2)",
            "Te": "x-basis generator X",
            "Fi": "x-basis rotation exp(-i 0.7 X/2)",
        },
        "terrain_channels": {
            "TerrainZ": "finite z-basis dephasing channel with generator Z",
            "TerrainX": "finite x-basis dephasing channel with generator X",
        },
        "f01_check": {
            "site_count_per_sheet": int(sites.shape[0]),
            "sheet_count": 2,
            "density_count": int(all_rho.shape[0]),
            "density_shape": [2, 2],
            "finite": True,
            "density_validity": density_stats,
        },
        "n01_check": {
            "n01_pass": bool(n01_pass),
            "epsilon": EPS,
            "commuting_pairs_near_zero": {
                "Ti_Fe": operator_pairs["Ti_Fe"]["commutator_pressure"],
                "Te_Fi": operator_pairs["Te_Fi"]["commutator_pressure"],
            },
            "noncommuting_pairs_nonzero": {
                "Ti_Fi": operator_pairs["Ti_Fi"]["commutator_pressure"],
                "Te_Fe": operator_pairs["Te_Fe"]["commutator_pressure"],
            },
            "expected_zero_keys_in_low_split": sorted(expected_zero.intersection(low)),
            "expected_nonzero_keys_in_high_split": sorted(expected_nonzero.intersection(high)),
        },
        "operator_pair_monotones": operator_pairs,
        "terrain_operator_monotones": terrain_operator_pairs,
        "monotone_vector": monotone_vector,
        "axis6_split": {
            "pressure_threshold": EPS,
            "high_pressure_keys": high,
            "low_pressure_keys": low,
            "split_respects_commuting_controls": bool(expected_zero.issubset(set(low))),
            "split_respects_noncommuting_controls": bool(expected_nonzero.issubset(set(high))),
        },
        "per_site_axis6_split": {
            "probe": "Ti_Fi commutator pressure over L/R local density cells",
            "threshold": median_pressure,
            "high_pressure_count": per_site_high,
            "low_pressure_count": per_site_low,
            "split_nontrivial": bool(per_site_high > 0 and per_site_low > 0),
        },
    }


def main() -> int:
    payload = build_payload()
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "ok": payload["n01_check"]["n01_pass"],
                "engine": payload["engine"],
                "monotone_count": len(payload["monotone_vector"]),
                "receipt": str(OUT),
            },
            sort_keys=True,
        )
    )
    return 0 if payload["n01_check"]["n01_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
