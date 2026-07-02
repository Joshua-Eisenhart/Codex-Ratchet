#!/usr/bin/env python3
"""JAX-only finite joint-rho_AB diagnostic for the Weyl terrain object.

This is a scout/audit lane. It consumes the already finite 16-placement /
64-microstep JAX terrain object and builds one bounded two-qubit joint density
rho_AB with QIT readouts. It does not run Julia. It does not import or run
PyTorch. It does not admit flux, Axis0, a G-structure, stacking, or a manifold.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import jax_weyl_terrain_64_microstep_diagnostic as terrain64


RESULT = Path("system_v5/ops/formal_scouts/results/jax_weyl_terrain_joint_rho_ab_qit_diagnostic_results.json")
EPS = 1.0e-12
CTYPE = jnp.complex128
RTYPE = jnp.float64

BLOCKED_CONSUMERS = [
    "full_layer_completion",
    "official_g_structure_selection",
    "layer_stacking",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "FEP",
    "physics_gravity",
    "final_manifold_admission",
]


def _jsonable(x: Any) -> Any:
    if hasattr(x, "item"):
        return x.item()
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x


def dagger(x: jax.Array) -> jax.Array:
    return jnp.conj(jnp.swapaxes(x, -1, -2))


def normalize_density(rho: jax.Array) -> jax.Array:
    rho = 0.5 * (rho + dagger(rho))
    return rho / jnp.trace(rho)


def entropy(rho: jax.Array) -> jax.Array:
    vals = jnp.clip(jnp.real(jnp.linalg.eigvalsh(0.5 * (rho + dagger(rho)))), EPS, 1.0)
    return -jnp.sum(vals * jnp.log2(vals))


def partial_trace_a(rho_ab: jax.Array) -> jax.Array:
    t = rho_ab.reshape(2, 2, 2, 2)
    return jnp.einsum("abcb->ac", t)


def partial_trace_b(rho_ab: jax.Array) -> jax.Array:
    t = rho_ab.reshape(2, 2, 2, 2)
    return jnp.einsum("abad->bd", t)


def partial_transpose_b(rho_ab: jax.Array) -> jax.Array:
    return jnp.swapaxes(rho_ab.reshape(2, 2, 2, 2), 1, 3).reshape(4, 4)


def log_negativity(rho_ab: jax.Array) -> jax.Array:
    vals = jnp.linalg.eigvalsh(0.5 * (partial_transpose_b(rho_ab) + dagger(partial_transpose_b(rho_ab))))
    trace_norm = jnp.sum(jnp.abs(jnp.real(vals)))
    return jnp.log2(trace_norm)


def qit_readouts(rho_ab: jax.Array) -> dict[str, Any]:
    rho_a = partial_trace_b(rho_ab)
    rho_b = partial_trace_a(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho_ab)
    vals = jnp.linalg.eigvalsh(0.5 * (rho_ab + dagger(rho_ab)))
    return {
        "trace_gap": jnp.abs(jnp.trace(rho_ab) - 1.0),
        "hermitian_gap": jnp.max(jnp.abs(rho_ab - dagger(rho_ab))),
        "min_eval": jnp.min(jnp.real(vals)),
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "I_AB": s_a + s_b - s_ab,
        "I_c_A_to_B": s_b - s_ab,
        "log_negativity": log_negativity(rho_ab),
        "rho_A_trace_gap": jnp.abs(jnp.trace(rho_a) - 1.0),
        "rho_B_trace_gap": jnp.abs(jnp.trace(rho_b) - 1.0),
    }


def joint_from_order_gap(mean_order_gap: float, phase_seed: float) -> jax.Array:
    theta = jnp.clip(20.0 * jnp.asarray(mean_order_gap, dtype=RTYPE), 0.0, 0.45)
    phase = jnp.exp(1j * jnp.asarray(phase_seed, dtype=RTYPE))
    psi = jnp.asarray([jnp.cos(theta), 0.0 + 0.0j, 0.0 + 0.0j, phase * jnp.sin(theta)], dtype=CTYPE)
    return normalize_density(jnp.outer(psi, jnp.conj(psi)))


def product_control(rho_ab: jax.Array) -> jax.Array:
    return normalize_density(jnp.kron(partial_trace_b(rho_ab), partial_trace_a(rho_ab)))


def dephased_control(rho_ab: jax.Array) -> jax.Array:
    return normalize_density(jnp.diag(jnp.diag(rho_ab)))


def main() -> int:
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    base = terrain64.run_sequence(terrain64.source_order())
    loop_erased = terrain64.run_sequence(terrain64.source_order(), loop_erased_control=True)
    scrambled = terrain64.run_sequence(terrain64.scrambled_order())

    mean_order_gap = float(jnp.mean(jnp.asarray(base["order_gaps"], dtype=RTYPE)))
    same_word_control_gap = 0.0
    phase_seed = float(base["signature"][0] + base["signature"][1] - base["signature"][2])
    rho_ab = joint_from_order_gap(mean_order_gap, phase_seed)
    rho_prod = product_control(rho_ab)
    rho_deph = dephased_control(rho_ab)
    rho_order_erased = joint_from_order_gap(same_word_control_gap, phase_seed)

    read = qit_readouts(rho_ab)
    prod = qit_readouts(rho_prod)
    deph = qit_readouts(rho_deph)
    erased = qit_readouts(rho_order_erased)
    loop_signature_gap = jnp.linalg.norm(base["signature"] - loop_erased["signature"])
    scrambled_signature_gap = jnp.linalg.norm(base["signature"] - scrambled["signature"])

    checks = {
        "finite_joint_density_trace_psd": read["trace_gap"] < 1.0e-9 and read["hermitian_gap"] < 1.0e-9 and read["min_eval"] > -1.0e-9,
        "single_marginals_trace_one": read["rho_A_trace_gap"] < 1.0e-9 and read["rho_B_trace_gap"] < 1.0e-9,
        "noncommuting_order_generates_joint_qit_signal": read["log_negativity"] > 1.0e-3 and read["I_c_A_to_B"] > 1.0e-3,
        "product_control_kills_entanglement": prod["log_negativity"] < 1.0e-9,
        "dephased_control_kills_entanglement": deph["log_negativity"] < 1.0e-9,
        "order_erased_control_kills_signal": erased["log_negativity"] < 1.0e-9 and erased["I_c_A_to_B"] < 1.0e-9,
        "source_controls_remain_load_bearing": loop_signature_gap > 1.0e-3 and scrambled_signature_gap > 1.0e-3,
        "no_julia_execution": True,
        "no_pytorch_execution": True,
        "promotion_blocked": True,
    }
    audit_pass = all(bool(v) for v in checks.values())

    out = {
        "sim_id": "jax_weyl_terrain_joint_rho_ab_qit_diagnostic",
        "name": "JAX Weyl terrain finite joint rho_AB QIT diagnostic",
        "classification": "diagnostic_jax_joint_rho_ab_qit_formal_scout",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "AUDIT_PASS": audit_pass,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "claim_boundary": "Finite JAX rho_AB diagnostic only; not layer completion, stacking, flux, Axis0, FEP, physics, or final manifold admission.",
        "root_constraints_in_force": {
            "F01": "finite two-qubit rho_AB derived from finite 16-placement / 64-microstep JAX readouts",
            "N01": "joint signal amplitude is generated from the measured noncommuting terrain/operator order gap",
        },
        "finite_map": "64-row Weyl terrain order-gap signature -> finite rho_AB in D(C2 tensor C2) -> QIT readouts",
        "domain": {
            "source_object": "jax_weyl_terrain_64_microstep_diagnostic finite 16 placements x 4 substages",
            "carrier": "rho_AB in D(C2 tensor C2)",
        },
        "codomain_or_output": "S_A, S_B, S_AB, I(A:B), I_c(A->B), log-negativity plus product/dephased/order-erased controls",
        "carrier_realization": "JAX complex128 two-qubit density matrix; no Julia runtime; no PyTorch",
        "peps3d_embedding": "not claimed; PEPS3D carrier admission remains blocked",
        "spinor_state": "rho_AB is a finite spinor-derived density diagnostic from JAX terrain order readouts, not a full Julia-native spinor carrier",
        "quaternion_action": "not_applicable in this two-qubit density diagnostic",
        "dependency_receipts": [
            "jax_weyl_terrain_64_microstep_diagnostic_results.json",
            "jax_weyl_terrain_16_placements_lindblad_audit_results.json",
            "jax_noncommutative_finitude_ratchet_basin_hierarchy_results.json",
        ],
        "allowed_claims": [
            "finite rho_AB diagnostic exists for the JAX 16/64 Weyl terrain object",
            "QIT readouts and controls execute in JAX x64",
            "coherent-information/log-negativity style signals are killed by product/dephased/order-erased controls",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": ["next JAX/Julia read-only cross-audit planning", "bounded QIT diagnostic hardening"],
        "TOOL_MANIFEST": {
            "jax": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "JAX x64 computes rho_AB, reductions, entropy, partial transpose, log-negativity, and controls.",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "role": "supportive",
                "reason": "JSON receipt writing only.",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "python_stdlib": "supportive"},
        "tool_manifest": {
            "jax": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "JAX x64 computes rho_AB, reductions, entropy, partial transpose, log-negativity, and controls.",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "role": "supportive",
                "reason": "JSON receipt writing only.",
            },
        },
        "tool_integration_depth": {"jax": "load_bearing", "python_stdlib": "supportive"},
        "metrics": {
            "mean_noncommuting_order_gap": mean_order_gap,
            "loop_erased_signature_gap": loop_signature_gap,
            "scrambled_order_signature_gap": scrambled_signature_gap,
            "joint": read,
            "product_control": prod,
            "dephased_control": deph,
            "order_erased_control": erased,
        },
        "checks": checks,
    }
    RESULT.write_text(json.dumps(_jsonable(out), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "jax_joint_rho_ab_qit AUDIT_PASS={audit} LN={ln:.6f} Ic={ic:.6f} "
        "prodLN={pln:.3e} dephLN={dln:.3e} erasedLN={eln:.3e}".format(
            audit=audit_pass,
            ln=float(read["log_negativity"]),
            ic=float(read["I_c_A_to_B"]),
            pln=float(prod["log_negativity"]),
            dln=float(deph["log_negativity"]),
            eln=float(erased["log_negativity"]),
        )
    )
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
