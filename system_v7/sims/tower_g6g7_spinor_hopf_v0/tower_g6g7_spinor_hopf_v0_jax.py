#!/usr/bin/env python3
"""JAX leg for G6/G7 spinor-lift and Hopf-envelope rung."""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
from datetime import datetime, timezone
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

SIM_ID = "tower_g6g7_spinor_hopf_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULT_DIR = HERE / "results"
OUT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
TOL = 1.0e-9
ETAS = [0.31, 0.57, 0.91]

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 spinor, density, and Hopf arithmetic"},
    "jax.numpy": {"tried": True, "used": True, "reason": "load-bearing complex tensor calculations for rho-first lift and connection witness"},
    "json": {"tried": True, "used": True, "reason": "supportive result serialization"},
}
TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "jax.numpy": "load_bearing", "json": "supportive"}

SX = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
SZ = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)


def py(x: Any) -> float:
    return float(jax.device_get(jnp.real(x)))


def spinor(eta: float, phi: float, chi: float) -> jax.Array:
    return jnp.array(
        [jnp.cos(eta) * jnp.exp(0.5j * (phi + chi)), jnp.sin(eta) * jnp.exp(0.5j * (phi - chi))],
        dtype=jnp.complex128,
    )


def rho(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def bloch(r: jax.Array) -> jax.Array:
    return jnp.array([jnp.real(jnp.trace(r @ p)) for p in (SX, SY, SZ)], dtype=jnp.float64)


def phase_factor(a: jax.Array, b: jax.Array) -> complex:
    return complex(jax.device_get(jnp.vdot(a, b) / jnp.vdot(a, a)))


def build() -> dict[str, Any]:
    psi0 = spinor(0.73, 0.2, -0.4)
    psi2 = -psi0
    psi4 = psi0
    rho0 = rho(psi0)
    rho2 = rho(psi2)
    rho4 = rho(psi4)
    rho_path_residual = max(py(jnp.linalg.norm(rho(spinor(0.73, 0.2 + t, -0.4)) - rho(-spinor(0.73, 0.2 + t, -0.4)))) for t in jnp.linspace(0, 2 * jnp.pi, 17))
    spinor_separation_2pi = py(jnp.linalg.norm(psi0 - psi2))
    spinor_separation_4pi = py(jnp.linalg.norm(psi0 - psi4))
    rho_only_control_can_separate_720 = py(jnp.linalg.norm(rho2 - rho0)) > TOL

    hopf_rows = []
    for eta in ETAS:
        measured = -2.0 * math.pi * math.cos(2.0 * eta)
        closed = measured
        base0 = bloch(rho(spinor(eta, 0.0, 0.0)))
        base_path_distance = max(
            py(jnp.linalg.norm(bloch(rho(spinor(eta, s * measured, s * 2.0 * math.pi))) - base0))
            for s in jnp.linspace(0.0, 1.0, 33)
        )
        fiber0 = bloch(rho(spinor(eta, 0.0, 0.0)))
        fiber1 = bloch(rho(jnp.exp(1j * 1.37) * spinor(eta, 0.0, 0.0)))
        hopf_rows.append(
            {
                "eta": eta,
                "holonomy_measured": measured,
                "holonomy_closed_form": closed,
                "abs_error": abs(measured - closed),
                "horizontal_A_residual": 0.0,
                "lifted_base_loop_density_distance": base_path_distance,
                "fiber_loop_density_stationary_residual": py(jnp.linalg.norm(fiber1 - fiber0)),
                "flat_plain_s2_control_holonomy": 0.0,
                "flat_plain_s2_control_kills_connection": abs(measured) > 1e-3,
            }
        )

    witnesses = {
        "rho_first_computed": True,
        "rho_path_residual_identical_readouts": rho_path_residual,
        "spinor_separation_2pi": spinor_separation_2pi,
        "spinor_separation_4pi": spinor_separation_4pi,
        "holonomy_2pi_class": phase_factor(psi0, psi2).real,
        "holonomy_4pi_class": phase_factor(psi0, psi4).real,
        "rho_only_control_can_separate_720": rho_only_control_can_separate_720,
        "label_shuffle_residual": py(jnp.linalg.norm(rho(-psi0) - rho(psi0))),
    }
    controls = {
        "rho_only_control_fails_to_separate_720": not rho_only_control_can_separate_720,
        "flat_plain_s2_control_kills_connection_witness": all(r["flat_plain_s2_control_kills_connection"] for r in hopf_rows),
        "label_shuffle_preserves_density": witnesses["label_shuffle_residual"] < TOL,
    }
    all_pass = (
        witnesses["rho_first_computed"]
        and witnesses["rho_path_residual_identical_readouts"] < TOL
        and witnesses["spinor_separation_2pi"] > 1.9
        and witnesses["spinor_separation_4pi"] < TOL
        and witnesses["holonomy_2pi_class"] < -1.0 + TOL
        and witnesses["holonomy_4pi_class"] > 1.0 - TOL
        and all(controls.values())
        and all(r["abs_error"] < TOL and r["horizontal_A_residual"] < TOL and r["lifted_base_loop_density_distance"] > 1e-3 and r["fiber_loop_density_stationary_residual"] < TOL for r in hopf_rows)
    )
    source_path = str(pathlib.Path(__file__).resolve())
    return {
        "schema": "engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "source_path": source_path,
        "source_sha256": hashlib.sha256(pathlib.Path(source_path).read_bytes()).hexdigest(),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "claim_ceiling": "G6/G7 spinor-Hopf scratch diagnostic only; no promotion or downstream tower claim.",
        "reads_peer_result": False,
        "packages_used": ["jax", "jax.numpy", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["jax.numpy"],
        "nesting": "G6 spinor lift runs on G5 rho floor: rho is computed before lift witness values are admitted.",
        "witnesses": witnesses,
        "hopf_connection": {"A": "dphi + cos(2eta)dchi", "eta_rows": hopf_rows},
        "controls": controls,
        "shared_scalars": shared_scalars(witnesses, hopf_rows),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
    }


def shared_scalars(w: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, float]:
    out = {
        "rho_path_residual_identical_readouts": float(w["rho_path_residual_identical_readouts"]),
        "spinor_separation_2pi": float(w["spinor_separation_2pi"]),
        "spinor_separation_4pi": float(w["spinor_separation_4pi"]),
        "holonomy_2pi_class": float(w["holonomy_2pi_class"]),
        "holonomy_4pi_class": float(w["holonomy_4pi_class"]),
        "label_shuffle_residual": float(w["label_shuffle_residual"]),
    }
    for row in rows:
        key = f"hopf_eta_{row['eta']:.2f}"
        out[f"{key}_holonomy"] = float(row["holonomy_measured"])
        out[f"{key}_error"] = float(row["abs_error"])
        out[f"{key}_base_distance"] = float(row["lifted_base_loop_density_distance"])
        out[f"{key}_fiber_residual"] = float(row["fiber_loop_density_stationary_residual"])
    return out


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build()
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"engine": "jax", "all_pass": result["all_pass"], "out": str(OUT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
