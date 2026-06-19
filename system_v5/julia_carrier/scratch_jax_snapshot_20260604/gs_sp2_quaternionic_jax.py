#!/usr/bin/env python3
"""JAX parity for gs_sp2_quaternionic.

PoC carrier probe only. No torch import. No promotion claim.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "gs_sp2_quaternionic"
JULIA_RESULTS = Path(
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/gs_sp2_quaternionic_results.json"
)
JAX_RESULTS = Path("/tmp/gs_sp2_quaternionic_jax_results.json")
TOL = 1.0e-10


def ffloat(x: Any) -> float:
    return float(jax.device_get(x))


def bbool(x: Any) -> bool:
    return bool(jax.device_get(x))


def max_abs(mat: jnp.ndarray) -> jnp.ndarray:
    return jnp.max(jnp.abs(mat))


def frob(mat: jnp.ndarray) -> jnp.ndarray:
    return jnp.sqrt(jnp.sum(jnp.abs(mat) ** 2))


def direct_sum_copies(base: jnp.ndarray, copies: int) -> jnp.ndarray:
    rows, cols = base.shape
    out = jnp.zeros((rows * copies, cols * copies), dtype=jnp.complex128)
    for c in range(copies):
        r0 = c * rows
        c0 = c * cols
        out = out.at[r0 : r0 + rows, c0 : c0 + cols].set(base)
    return out


def quat_structure(n: int) -> tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray]:
    sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
    q_i = 1j * sz
    q_j = 1j * sx
    q_k = -1j * sy
    copies = n // 2
    return (
        direct_sum_copies(q_i, copies),
        direct_sum_copies(q_j, copies),
        direct_sum_copies(q_k, copies),
    )


def algebra_profile(iq: jnp.ndarray, jq: jnp.ndarray, kq: jnp.ndarray) -> dict[str, float]:
    n = iq.shape[0]
    ident = jnp.eye(n, dtype=jnp.complex128)
    return {
        "IJ_residual": ffloat(max_abs(iq @ jq - kq)),
        "JK_residual": ffloat(max_abs(jq @ kq - iq)),
        "KI_residual": ffloat(max_abs(kq @ iq - jq)),
        "I2_residual": ffloat(max_abs(iq @ iq + ident)),
        "J2_residual": ffloat(max_abs(jq @ jq + ident)),
        "K2_residual": ffloat(max_abs(kq @ kq + ident)),
        "I_antihermitian_residual": ffloat(max_abs(iq + iq.conj().T)),
        "J_antihermitian_residual": ffloat(max_abs(jq + jq.conj().T)),
        "K_antihermitian_residual": ffloat(max_abs(kq + kq.conj().T)),
        "JI_plus_K_residual": ffloat(max_abs(jq @ iq + kq)),
        "noncomm_gap": ffloat(max_abs(iq @ jq - jq @ iq)),
    }


def sector_norm(a: jnp.ndarray, p: jnp.ndarray) -> float:
    return ffloat(jnp.linalg.norm(p @ a @ p, ord=2))


def compute() -> dict[str, Any]:
    iq = jnp.array(
        [
            [1j, 0, 0, 0],
            [0, -1j, 0, 0],
            [0, 0, 1j, 0],
            [0, 0, 0, -1j],
        ],
        dtype=jnp.complex128,
    )
    jq = jnp.array(
        [
            [0, 1j, 0, 0],
            [1j, 0, 0, 0],
            [0, 0, 0, 1j],
            [0, 0, 1j, 0],
        ],
        dtype=jnp.complex128,
    )
    kq = jnp.array(
        [
            [0, -1, 0, 0],
            [1, 0, 0, 0],
            [0, 0, 0, -1],
            [0, 0, 1, 0],
        ],
        dtype=jnp.complex128,
    )
    ident = jnp.eye(4, dtype=jnp.complex128)

    base = algebra_profile(iq, jq, kq)
    ij = iq @ jq
    ij_broken = -kq
    boundary_vs_negative_identity = ffloat(max_abs(iq @ iq + ident))
    boundary_vs_k = ffloat(max_abs(iq @ iq - kq))

    chi_i = -1j * iq
    pplus = (ident + chi_i) / 2
    pminus = (ident - chi_i) / 2
    raw_pplus = (ident + iq) / 2
    raw_pminus = (ident - iq) / 2

    theta = 0.37
    # I is diagonal, so exp(theta*I/2) is exact through eigenspace exponentials.
    u = jnp.diag(jnp.exp(theta * jnp.diag(iq) / 2))
    ui = jnp.linalg.inv(u)
    ih = u @ iq @ ui
    jh = u @ jq @ ui
    kh = u @ kq @ ui

    epsilon = 0.1
    i_eps = iq + epsilon * jq

    scalar_invariants = dict(base)
    scalar_invariants.update(
        {
            "IJ_broken_vs_K_frob": ffloat(frob(ij_broken - kq)),
            "IJ_vs_IJ_broken_frob": ffloat(frob(ij - ij_broken)),
            "boundary_vs_negative_identity": boundary_vs_negative_identity,
            "boundary_vs_K": boundary_vs_k,
            "chi_square_residual": ffloat(max_abs(chi_i @ chi_i - ident)),
            "Pplus_idempotent_residual": ffloat(max_abs(pplus @ pplus - pplus)),
            "Pminus_idempotent_residual": ffloat(max_abs(pminus @ pminus - pminus)),
            "Pplus_Pminus_residual": ffloat(max_abs(pplus @ pminus)),
            "Psum_identity_residual": ffloat(max_abs(pplus + pminus - ident)),
            "raw_Pplus_idempotent_residual": ffloat(max_abs(raw_pplus @ raw_pplus - raw_pplus)),
            "raw_Pminus_idempotent_residual": ffloat(max_abs(raw_pminus @ raw_pminus - raw_pminus)),
            "holonomy_residual": ffloat(max_abs(ih @ jh - kh)),
            "holonomy_erased_transport_residual": ffloat(max_abs(ih @ jh - kq)),
            "gap_plus": sector_norm(iq, pplus),
            "gap_minus": sector_norm(iq, pminus),
            "gap_plus_after_uniform_epsJ": sector_norm(i_eps, pplus),
            "gap_minus_after_uniform_epsJ": sector_norm(i_eps, pminus),
        }
    )
    scalar_invariants["symmetry_breaking_gap"] = abs(
        scalar_invariants["gap_plus_after_uniform_epsJ"]
        - scalar_invariants["gap_minus_after_uniform_epsJ"]
    )

    ladder = []
    for n in (2, 4, 8, 16):
        in_, jn, kn = quat_structure(n)
        profile = algebra_profile(in_, jn, kn)
        scalar_invariants[f"ladder_n{n}_IJ_residual"] = profile["IJ_residual"]
        scalar_invariants[f"ladder_n{n}_JK_residual"] = profile["JK_residual"]
        scalar_invariants[f"ladder_n{n}_KI_residual"] = profile["KI_residual"]
        scalar_invariants[f"ladder_n{n}_I2_residual"] = profile["I2_residual"]
        scalar_invariants[f"ladder_n{n}_noncomm_gap"] = profile["noncomm_gap"]
        ladder.append(
            {
                "n": n,
                "IJ_residual": profile["IJ_residual"],
                "JK_residual": profile["JK_residual"],
                "KI_residual": profile["KI_residual"],
                "I2_residual": profile["I2_residual"],
                "noncomm_gap": profile["noncomm_gap"],
                "algebra_closed": all(
                    profile[key] < TOL
                    for key in (
                        "IJ_residual",
                        "JK_residual",
                        "KI_residual",
                        "I2_residual",
                        "J2_residual",
                        "K2_residual",
                    )
                ),
            }
        )

    return {
        "object_id": OBJECT_ID,
        "classification": "PoC",
        "promotion_allowed": False,
        "claim_ceiling": "JAX parity probe only; no layer, manifold, bridge, flux, or physics claim.",
        "positive_checks": {
            "IJ_equals_K": scalar_invariants["IJ_residual"] < TOL,
            "JK_equals_I": scalar_invariants["JK_residual"] < TOL,
            "KI_equals_J": scalar_invariants["KI_residual"] < TOL,
            "squares_equal_negative_identity": all(
                scalar_invariants[key] < TOL
                for key in ("I2_residual", "J2_residual", "K2_residual")
            ),
            "all_antihermitian": all(
                scalar_invariants[key] < TOL
                for key in (
                    "I_antihermitian_residual",
                    "J_antihermitian_residual",
                    "K_antihermitian_residual",
                )
            ),
        },
        "control_broken_wrong_sign": {
            "IJ_broken_equals_K": scalar_invariants["IJ_broken_vs_K_frob"] < TOL,
            "IJ_equals_IJ_broken": scalar_invariants["IJ_vs_IJ_broken_frob"] < TOL,
        },
        "boundary_commutative_limit": {
            "equals_negative_identity": boundary_vs_negative_identity < TOL,
            "equals_K": boundary_vs_k < TOL,
        },
        "chirality_projectors": {
            "projectors_pass": all(
                scalar_invariants[key] < TOL
                for key in (
                    "Pplus_idempotent_residual",
                    "Pminus_idempotent_residual",
                    "Pplus_Pminus_residual",
                    "Psum_identity_residual",
                )
            ),
            "raw_complex_structure_projectors_pass": all(
                scalar_invariants[key] < TOL
                for key in ("raw_Pplus_idempotent_residual", "raw_Pminus_idempotent_residual")
            ),
        },
        "holonomy_preserved": scalar_invariants["holonomy_residual"] < TOL,
        "symmetry_breaking": {
            "symmetry_breaking_gap": scalar_invariants["symmetry_breaking_gap"],
            "real_asymmetry": scalar_invariants["symmetry_breaking_gap"] > TOL,
            "status": (
                "asymmetry_survived_probe"
                if scalar_invariants["symmetry_breaking_gap"] > TOL
                else "convention_only_under_uniform_epsJ"
            ),
        },
        "size_ladder": ladder,
        "scalar_invariants": scalar_invariants,
    }


def main() -> None:
    jax_result = compute()
    if not JULIA_RESULTS.exists():
        raise FileNotFoundError(f"Julia result missing: {JULIA_RESULTS}")
    julia_result = json.loads(JULIA_RESULTS.read_text())
    julia_scalars = julia_result["scalar_invariants"]
    jax_scalars = jax_result["scalar_invariants"]

    diffs: dict[str, float] = {}
    missing: list[str] = []
    for name, julia_value in sorted(julia_scalars.items()):
        if name not in jax_scalars:
            missing.append(name)
            continue
        diffs[name] = abs(float(julia_value) - float(jax_scalars[name]))

    max_name = max(diffs, key=diffs.get) if diffs else ""
    parity_max_diff = diffs[max_name] if max_name else float("nan")

    jax_result.update(
        {
            "julia_result_path": str(JULIA_RESULTS),
            "jax_result_path": str(JAX_RESULTS),
            "parity_diffs": diffs,
            "parity_missing_scalars": missing,
            "parity_max_diff": parity_max_diff,
            "parity_max_diff_name": max_name,
            "parity_pass_le_1e10": parity_max_diff <= TOL and not missing,
        }
    )

    JAX_RESULTS.write_text(json.dumps(jax_result, indent=2) + "\n")
    print("gs_sp2_quaternionic_jax")
    print(f"julia_result_path={JULIA_RESULTS}")
    print(f"jax_result_path={JAX_RESULTS}")
    print(f"parity_max_diff={parity_max_diff:.17g}")
    print(f"parity_max_diff_name={max_name}")


if __name__ == "__main__":
    main()
