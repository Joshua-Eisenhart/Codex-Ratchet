#!/usr/bin/env python3
from jax import config

config.update("jax_enable_x64", True)

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import jax
import jax.numpy as jnp


ENGINE = "jax"
ROLE = "diagnostic_x64"
REPO_ROOT = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet")
WORKFLOW_PATHS = [
    REPO_ROOT / ".claude/workflows/golden_weyl_holonomy_bars.json",
    REPO_ROOT / ".claude/workflows/jax_julia_contract.json",
]
RECEIPT_PATH = Path("/tmp/golden_holo_jax_receipt.json")
ETA_COUNT = 129
PARITY_TOLERANCE = 1.0e-10
ERROR_BOUND = 1.0e-12


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_obj(obj: Any) -> str:
    return sha256_bytes(canonical_json_bytes(obj))


def source_hashes() -> dict[str, str]:
    return {str(path): sha256_bytes(path.read_bytes()) for path in WORKFLOW_PATHS}


def eta_grid() -> jax.Array:
    return jnp.linspace(0.0, 0.5 * jnp.pi, ETA_COUNT, dtype=jnp.float64)


def nested_hopf_connection_coeff(eta: jax.Array) -> jax.Array:
    # Hopf connection A = d phi + cos(2 eta) d chi; H uses the chi holonomy coefficient.
    return jnp.cos(2.0 * eta)


def plain_s2_connection_coeff(eta: jax.Array) -> jax.Array:
    # Same eta base, plain S2 polar angle theta = 2 eta, no Hopf fiber/nesting.
    theta = 2.0 * eta
    return jnp.cos(theta)


def phase_from_connection(c: jax.Array) -> jax.Array:
    return jnp.exp(1j * 2.0 * jnp.pi * c)


def weyl_lr_state_from_connection(c: jax.Array) -> jax.Array:
    # Single code path for both bases. The base-specific connection supplies c in [-1, 1].
    c = jnp.clip(c, -1.0, 1.0)
    amp_up = jnp.sqrt((1.0 + c) / 2.0)
    amp_dn = jnp.sqrt((1.0 - c) / 2.0)
    phase = phase_from_connection(c)
    norm = 1.0 / jnp.sqrt(jnp.asarray(2.0, dtype=jnp.float64))
    left = jnp.stack([amp_up, phase * amp_dn], axis=-1) * norm
    right = jnp.stack([amp_dn, jnp.conj(phase) * amp_up], axis=-1) * norm
    return jnp.concatenate([left, right], axis=-1).astype(jnp.complex128)


def sigma_z_lr_expectations(psi: jax.Array) -> tuple[jax.Array, jax.Array]:
    left = psi[:, 0:2]
    right = psi[:, 2:4]
    sz_l = (jnp.abs(left[:, 0]) ** 2 - jnp.abs(left[:, 1]) ** 2).real
    sz_r = (jnp.abs(right[:, 0]) ** 2 - jnp.abs(right[:, 1]) ** 2).real
    return sz_l, sz_r


def gamma5_odd_h(psi: jax.Array) -> jax.Array:
    sz_l, sz_r = sigma_z_lr_expectations(psi)
    return sz_l - sz_r


def swap_lr(psi: jax.Array) -> jax.Array:
    return jnp.concatenate([psi[:, 2:4], psi[:, 0:2]], axis=-1)


def max_abs(x: jax.Array) -> float:
    return float(jax.device_get(jnp.max(jnp.abs(x))))


def as_float_list(x: jax.Array) -> list[float]:
    return [float(v) for v in jax.device_get(x)]


def realized_state_fingerprint(psi_nested: jax.Array, psi_plain: jax.Array) -> str:
    own_state = jnp.stack(
        [
            jnp.real(psi_nested),
            jnp.imag(psi_nested),
            jnp.real(psi_plain),
            jnp.imag(psi_plain),
        ],
        axis=-1,
    )
    return sha256_bytes(jax.device_get(own_state).tobytes())


def main() -> None:
    etas = eta_grid()
    source = source_hashes()
    symbolic_spec = {
        "eta_domain": "closed_interval_[0,pi/2]",
        "eta_count": ETA_COUNT,
        "observable": "H(eta)=<sigma_z>_L-<sigma_z>_R",
        "nested_base": "Hopf connection chi coefficient c_nested(eta)=cos(2 eta)",
        "plain_base": "plain S2 polar theta=2 eta coefficient c_plain(eta)=cos(theta)",
        "shared_state_map": "same Weyl L/R gamma5/sigma_z code path; only c(eta) provider changes",
        "no_peps_ctmrg": True,
    }
    control_input = {
        "engine": ENGINE,
        "role": ROLE,
        "program": "/tmp/golden_holo_jax.py",
        "symbolic_spec_hash": sha256_obj(symbolic_spec),
        "workflow_source_hashes": source,
        "eta_count": ETA_COUNT,
        "error_bound": ERROR_BOUND,
    }

    c_nested = nested_hopf_connection_coeff(etas)
    c_plain = plain_s2_connection_coeff(etas)
    psi_nested = weyl_lr_state_from_connection(c_nested)
    psi_plain = weyl_lr_state_from_connection(c_plain)
    h_nested = gamma5_odd_h(psi_nested)
    h_plain = gamma5_odd_h(psi_plain)
    delta_h = h_nested - h_plain
    h_nested_swapped = gamma5_odd_h(swap_lr(psi_nested))
    h_plain_swapped = gamma5_odd_h(swap_lr(psi_plain))

    norm_nested = jnp.sum(jnp.abs(psi_nested) ** 2, axis=-1)
    norm_plain = jnp.sum(jnp.abs(psi_plain) ** 2, axis=-1)
    odd_nested = max_abs(h_nested + h_nested_swapped)
    odd_plain = max_abs(h_plain + h_plain_swapped)

    receipt = {
        "engine": ENGINE,
        "engine_role": ROLE,
        "created_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "program_path": "/tmp/golden_holo_jax.py",
        "receipt_path": str(RECEIPT_PATH),
        "workflow_source_hashes": source,
        "symbolic_spec": symbolic_spec,
        "symbolic_spec_hash": sha256_obj(symbolic_spec),
        "control_input_hash": sha256_obj(control_input),
        "control_input": control_input,
        "sealed_independence": {
            "reads_other_engine_state": False,
            "reads_other_engine_receipt": False,
            "raw_state_exchange": False,
            "shared_inputs_only": ["workflow json source hashes", "symbolic formula spec", "eta grid manifest"],
        },
        "carrier": {
            "type": "exact_analytic",
            "eta_count": ETA_COUNT,
            "eta_domain": [0.0, 0.5 * math.pi],
            "nested_hopf": "A=dphi+cos(2eta)dchi; c_nested is chi holonomy coefficient",
            "plain_s2": "theta=2eta; c_plain is the plain-sphere z/Berry coefficient using same eta base",
            "peps_ctmrg": "not_used",
        },
        "realized_state_fingerprint": realized_state_fingerprint(psi_nested, psi_plain),
        "invariants": {
            "eta": as_float_list(etas),
            "H_nested": as_float_list(h_nested),
            "H_plain": as_float_list(h_plain),
            "delta_H": as_float_list(delta_h),
            "delta_H_max": max_abs(delta_h),
        },
        "checks": {
            "jax_x64": bool(jax.config.read("jax_enable_x64")),
            "psi_norm_error_nested_max": max_abs(norm_nested - 1.0),
            "psi_norm_error_plain_max": max_abs(norm_plain - 1.0),
            "gamma5_odd_swap_error_nested_max": odd_nested,
            "gamma5_odd_swap_error_plain_max": odd_plain,
            "H_nested_connection_error_max": max_abs(h_nested - c_nested),
            "H_plain_connection_error_max": max_abs(h_plain - c_plain),
            "two_sided_error_bound": {"minus": -ERROR_BOUND, "plus": ERROR_BOUND},
            "error_bound": ERROR_BOUND,
            "parity_tolerance": PARITY_TOLERANCE,
        },
        "decision_local": {
            "plain_sphere_reproduces": bool(max_abs(delta_h) <= ERROR_BOUND),
            "load_bearing": "none" if max_abs(delta_h) <= ERROR_BOUND else "holonomy",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        },
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"engine": ENGINE, "receipt": str(RECEIPT_PATH), "delta_H_max": receipt["invariants"]["delta_H_max"]}, sort_keys=True))


if __name__ == "__main__":
    main()
