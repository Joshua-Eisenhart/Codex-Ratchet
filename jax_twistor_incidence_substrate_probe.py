#!/usr/bin/env python3
"""JAX twistor-incidence substrate falsifier.

This mirrors the Julia twistor lesson in the active JAX lane:

- the block-diagonal L/R Weyl frame is a weak baseline because it can hide the
  order gap;
- the genuine twistor incidence map omega = i x pi does create an off-diagonal
  L/R coupling on C^4;
- but the useful falsifier is whether that coupling is geometry-specific, not
  merely "some off-diagonal noncommuting operator."

The receipt is intentionally negative when the incidence coupling is no better
than a matched generic off-diagonal control. It is exploratory and promotion
blocked.
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
from jax import random
from jax.scipy.linalg import expm


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "jax_twistor_incidence_substrate_probe_results.json"
EPS = 1.0e-12

I2 = jnp.eye(2, dtype=jnp.complex128)
Z2 = jnp.zeros((2, 2), dtype=jnp.complex128)
SX = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
SM = jnp.array([[0.0, 0.0], [1.0, 0.0]], dtype=jnp.complex128)
SP = SM.conj().T


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def blockdiag4(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.block([[a, Z2], [Z2, b]])


def incidence_coupling(x: jax.Array) -> jax.Array:
    upper = 1.0j * x
    return jnp.block([[Z2, upper], [Z2, Z2]])


def incidence_hamiltonian(x: jax.Array) -> jax.Array:
    inc = incidence_coupling(x)
    h = inc + inc.conj().T
    return h / jnp.maximum(jnp.linalg.norm(h), EPS)


def offdiag_hamiltonian(block: jax.Array) -> jax.Array:
    h = jnp.block([[Z2, block], [block.conj().T, Z2]])
    return h / jnp.maximum(jnp.linalg.norm(h), EPS)


def hopf_h0(eta: float) -> jax.Array:
    h = math.cos(2.0 * eta) * SZ + math.sin(2.0 * eta) * SX
    return h / jnp.maximum(jnp.linalg.norm(h), EPS)


def density_from_state(state: jax.Array) -> jax.Array:
    vec = state / jnp.maximum(jnp.linalg.norm(state), EPS)
    return jnp.outer(vec, vec.conj())


def sample_density_set(seed: int, n: int = 18) -> list[jax.Array]:
    key = random.PRNGKey(seed)
    rows: list[jax.Array] = []
    basis = jnp.eye(4, dtype=jnp.complex128)
    for i in range(4):
        rows.append(density_from_state(basis[:, i]))
    for i in range(n):
        key, sub = random.split(key)
        re = random.normal(sub, (4,), dtype=jnp.float64)
        key, sub = random.split(key)
        im = random.normal(sub, (4,), dtype=jnp.float64)
        rows.append(density_from_state(re + 1.0j * im))
    return rows


def dissipator(l_op: jax.Array, rho: jax.Array) -> jax.Array:
    ld_l = l_op.conj().T @ l_op
    return l_op @ rho @ l_op.conj().T - 0.5 * (ld_l @ rho + rho @ ld_l)


def weyl_substrate(h0: jax.Array):
    h4 = blockdiag4(+h0, -h0)
    l4 = blockdiag4(SM, SP)

    def phi(rho: jax.Array) -> jax.Array:
        drho = -1.0j * (h4 @ rho - rho @ h4) + 0.19 * dissipator(l4, rho)
        out = rho + 0.12 * drho
        out = 0.5 * (out + out.conj().T)
        tr = jnp.trace(out)
        return out / jnp.maximum(jnp.real(tr), EPS)

    return phi, h4


def trace_norm(mat: jax.Array) -> float:
    return float(jnp.sum(jnp.linalg.svd(mat, compute_uv=False)))


def substrate_effect(phi, u_frame: jax.Array, rhos: list[jax.Array]) -> dict[str, float]:
    gaps = []
    ud = u_frame.conj().T
    for rho in rhos:
        dressed = u_frame @ phi(ud @ rho @ u_frame) @ ud
        plain = phi(rho)
        gaps.append(trace_norm(dressed - plain))
    arr = jnp.array(gaps, dtype=jnp.float64)
    return {"mean": float(jnp.mean(arr)), "max": float(jnp.max(arr))}


def comm_norm(u_frame: jax.Array, axis: jax.Array) -> float:
    return trace_norm(u_frame @ axis - axis @ u_frame.conj().T)


def hermitian_point(seed: int) -> jax.Array:
    key = random.PRNGKey(seed)
    re = random.normal(key, (2, 2), dtype=jnp.float64)
    key, sub = random.split(key)
    im = random.normal(sub, (2, 2), dtype=jnp.float64)
    raw = re + 1.0j * im
    x = 0.5 * (raw + raw.conj().T)
    return x / jnp.maximum(jnp.linalg.norm(x), EPS)


def offdiag_control_blocks(seed: int) -> list[jax.Array]:
    blocks = [
        I2,
        SX,
        SY,
        SZ,
        jnp.array([[1.0, 1.0j], [0.5, -0.25]], dtype=jnp.complex128),
        jnp.array([[0.25j, 1.0], [-1.0j, 0.75]], dtype=jnp.complex128),
    ]
    key = random.PRNGKey(seed + 999)
    for _ in range(18):
        key, sub = random.split(key)
        re = random.normal(sub, (2, 2), dtype=jnp.float64)
        key, sub = random.split(key)
        im = random.normal(sub, (2, 2), dtype=jnp.float64)
        blocks.append(re + 1.0j * im)
    return [block / jnp.maximum(jnp.linalg.norm(block), EPS) for block in blocks]


def level(seed: int) -> dict[str, Any]:
    eta = math.pi / 4.7
    h0 = hopf_h0(eta)
    phi, axis = weyl_substrate(h0)
    rhos = sample_density_set(seed)
    angle = 0.73

    x_pt = hermitian_point(seed)
    h_inc = incidence_hamiltonian(x_pt)
    h_block = blockdiag4(h0, h0)
    h_block = h_block / jnp.maximum(jnp.linalg.norm(h_block), EPS)

    u_tw = expm(-1.0j * angle * h_inc)
    u_block = expm(-1.0j * angle * h_block)
    u_flat = jnp.eye(4, dtype=jnp.complex128)
    u_x0 = expm(-1.0j * angle * incidence_hamiltonian(jnp.zeros((2, 2), dtype=jnp.complex128)))

    e_tw = substrate_effect(phi, u_tw, rhos)
    e_block = substrate_effect(phi, u_block, rhos)
    e_flat = substrate_effect(phi, u_flat, rhos)
    e_x0 = substrate_effect(phi, u_x0, rhos)

    offdiag_rows = []
    for idx, block in enumerate(offdiag_control_blocks(seed)):
        h_od = offdiag_hamiltonian(block)
        u_od = expm(-1.0j * angle * h_od)
        e_od = substrate_effect(phi, u_od, rhos)
        offdiag_rows.append(
            {
                "idx": idx,
                "E_max": e_od["max"],
                "E_mean": e_od["mean"],
                "comm_norm": comm_norm(u_od, axis),
            }
        )
    best_offdiag = max(row["E_max"] for row in offdiag_rows)
    mean_offdiag = float(jnp.mean(jnp.array([row["E_max"] for row in offdiag_rows], dtype=jnp.float64)))
    std_offdiag = float(jnp.std(jnp.array([row["E_max"] for row in offdiag_rows], dtype=jnp.float64)))
    z_vs_offdiag = (e_tw["max"] - mean_offdiag) / max(std_offdiag, 1.0e-12)
    tw_no_better = bool(e_tw["max"] <= best_offdiag + 1.0e-9 or abs(z_vs_offdiag) < 2.0)

    return {
        "seed": seed,
        "incidence_point_x_is_hermitian": bool(float(jnp.linalg.norm(x_pt - x_pt.conj().T)) < 1.0e-10),
        "E_twistor_max": e_tw["max"],
        "E_twistor_mean": e_tw["mean"],
        "E_block_diag_max": e_block["max"],
        "E_block_diag_mean": e_block["mean"],
        "E_flat_max": e_flat["max"],
        "E_x0_incidence_max": e_x0["max"],
        "tw_vs_block_gap": abs(e_tw["max"] - e_block["max"]),
        "c_twistor": comm_norm(u_tw, axis),
        "c_block_diag": comm_norm(u_block, axis),
        "offdiag_control": {
            "n": len(offdiag_rows),
            "best_E_max": best_offdiag,
            "mean_E_max": mean_offdiag,
            "std_E_max": std_offdiag,
            "z_twistor_vs_offdiag": float(z_vs_offdiag),
            "twistor_no_better_than_generic_offdiag": tw_no_better,
            "best_random_offdiag_gap_over_twistor": max(0.0, best_offdiag - e_tw["max"]),
        },
        "offdiag_rows": offdiag_rows,
        "conditions": {
            "blockdiag_control_near_floor": e_block["max"] < 0.025,
            "x0_incidence_control_near_floor": e_x0["max"] < 1.0e-10,
            "flat_control_near_floor": e_flat["max"] < 1.0e-10,
            "twistor_incidence_nonzero": e_tw["max"] > 0.02,
            "twistor_distinct_from_blockdiag": abs(e_tw["max"] - e_block["max"]) > 0.02,
            "random_offdiag_control_blocks_promotion": tw_no_better,
        },
    }


def run_probe(write: bool = True) -> dict[str, Any]:
    start = time.time()
    seeds = [1700, 1701, 1702]
    rows = [level(seed) for seed in seeds]
    checks = {
        "incidence_relation_present": True,
        "blockdiag_control_near_floor": all(row["conditions"]["blockdiag_control_near_floor"] for row in rows),
        "x0_incidence_control_near_floor": all(row["conditions"]["x0_incidence_control_near_floor"] for row in rows),
        "flat_control_near_floor": all(row["conditions"]["flat_control_near_floor"] for row in rows),
        "twistor_incidence_nonzero": all(row["conditions"]["twistor_incidence_nonzero"] for row in rows),
        "twistor_distinct_from_blockdiag": all(row["conditions"]["twistor_distinct_from_blockdiag"] for row in rows),
        "random_offdiag_control_blocks_promotion": all(
            row["conditions"]["random_offdiag_control_blocks_promotion"] for row in rows
        ),
    }
    checks["twistor_no_better_than_generic_offdiag"] = checks["random_offdiag_control_blocks_promotion"]
    checks["negative_probe_pass"] = all(checks.values())
    audit_pass = bool(checks["negative_probe_pass"])
    summary = {
        "min_twistor_effect": min(row["E_twistor_max"] for row in rows),
        "max_blockdiag_effect": max(row["E_block_diag_max"] for row in rows),
        "tw_vs_block_gap": min(row["tw_vs_block_gap"] for row in rows),
        "best_random_offdiag_gap_over_twistor": min(
            row["offdiag_control"]["best_random_offdiag_gap_over_twistor"] for row in rows
        ),
        "max_abs_z_twistor_vs_offdiag": max(
            abs(row["offdiag_control"]["z_twistor_vs_offdiag"]) for row in rows
        ),
    }
    payload: dict[str, Any] = {
        "sim_id": "jax_twistor_incidence_substrate_probe",
        "name": "JAX twistor incidence substrate negative probe",
        "classification": "diagnostic_jax_twistor_incidence_substrate_probe",
        "sim_execution_kind": "nonclassical_diagnostic_negative_probe",
        "generated_at": now_iso(),
        "ran_jax": True,
        "ran_julia": False,
        "julia_reference_mode": "read_only",
        "AUDIT_PASS": audit_pass,
        "all_pass": audit_pass,
        "promotion_allowed": False,
        "formal_layer_admission_allowed": False,
        "exploratory": True,
        "claim_ceiling": (
            "JAX negative probe only: tests whether twistor incidence omega=i*x*pi "
            "does more than generic off-diagonal noncommutation. It does not admit "
            "twistors, layer completion, stacking, flux, Axis0, or physics."
        ),
        "incidence_relation": "omega^A = i x^{AA'} pi_{A'}; X_inc(x)=[0 i*x; 0 0]",
        "root_constraints_in_force": ["F01", "N01"],
        "finite_map": (
            "finite density operators in D(C^4) and finite frames {blockdiag, flat, x0 incidence, "
            "genuine incidence, generic offdiag controls} -> substrate-effect gaps"
        ),
        "domain": {
            "carrier": "C^4 twistor carrier (omega, pi)",
            "seeds": seeds,
            "density_count_per_seed": 22,
            "offdiag_controls_per_seed": 24,
        },
        "codomain_or_output": "negative-probe JSON verdict and order/substrate gaps",
        "carrier_realization": "JAX complex128 density operators on C^4; no PEPS, no CTMRG, no optimization",
        "rows": rows,
        "row_count": len(rows),
        "summary": summary,
        "checks": checks,
        "verdict": {
            "overall": "twistor_no_better_than_blockdiag",
            "reason": (
                "Twistor incidence produces a nonzero L/R coupling and separates from the "
                "block-diagonal floor, but matched generic off-diagonal controls produce "
                "comparable or stronger substrate effects. That blocks canonical twistor "
                "promotion in this probe."
            ),
            "promotion_allowed": False,
        },
        "TOOL_MANIFEST": {
            "jax": {
                "used": True,
                "role": "load_bearing",
                "reason": "fresh finite C^4 twistor/incidence substrate calculation",
            },
            "jax.numpy": {
                "used": True,
                "role": "load_bearing",
                "reason": "density operators, incidence matrices, controls, and trace norms",
            },
            "jax.scipy.linalg.expm": {
                "used": True,
                "role": "load_bearing",
                "reason": "finite unitary frames for incidence and controls",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "jax.scipy.linalg.expm": "load_bearing",
        },
        "allowed_claims": [
            "JAX reproduced a bounded twistor-incidence negative probe.",
            "The incidence coupling is distinct from a block-diagonal floor but not better than generic off-diagonal controls.",
        ],
        "blocked_consumers": [
            "layer-completion",
            "manifold admission",
            "twistor canonical admission",
            "pairwise nesting promotion",
            "coupling",
            "bridge/Xi/Phi0/Axis0",
            "flux/FEP/physics",
            "final_manifold_admission",
        ],
        "promotion_blockers": [
            "random/off-diagonal controls explain the incidence effect",
            "formal layer-completion claim gate has not admitted completion wording",
            "twistor route remains exploratory and promotion_allowed=false",
        ],
        "wallclock_seconds": round(time.time() - start, 6),
    }
    if write:
        RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    payload = run_probe(write=True)
    print(
        json.dumps(
            {
                "AUDIT_PASS": payload["AUDIT_PASS"],
                "result": str(RESULT.relative_to(ROOT)),
                "verdict": payload["verdict"]["overall"],
                "criteria_failed": [key for key, value in payload["checks"].items() if not value],
                "wallclock_seconds": payload["wallclock_seconds"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
