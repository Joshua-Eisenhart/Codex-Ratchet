#!/usr/bin/env python3
"""
sim_e3nn_jax_capability.py -- Tool-capability isolation sim for `e3nn_jax`.

This mirrors the bounded PyTorch `sim_e3nn_capability.py` fixture on the JAX
side. Load-bearing means the SO(3) representation/equivariance residuals and
negative controls gate summary.all_pass.
"""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

classification = "canonical"

import json
import math
import os
import sys

import jax
import jax.numpy as jnp

from receipt_boundary import apply_default_receipt_boundary

_NOT_USED_REASON = (
    "not used: this bounded e3nn_jax capability receipt isolates SO(3) irrep, "
    "D-matrix, spherical-harmonics, and JAX vmap equivariance APIs; other tool "
    "families require separate receipts."
)

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "used as the JAX runtime for x64 arrays and vmap batch execution",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "array support only; e3nn_jax and jax.vmap gate the receipt",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "canonical capability family row for SO(3) equivariance; JAX implementation is e3nn_jax",
    },
    "e3nn_jax": {
        "tried": False,
        "used": False,
        "reason": "under test",
    },
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "clifford": None,
    "cvc5": None,
    "e3nn": "load_bearing",
    "e3nn_jax": "load_bearing",
    "geomstats": None,
    "gudhi": None,
    "jax": "supportive",
    "jax.numpy": "supportive",
    "pyg": None,
    "pytorch": None,
    "rustworkx": None,
    "sympy": None,
    "toponetx": None,
    "xgi": None,
    "z3": None,
}

E3NN_JAX_OK = False
E3NN_JAX_VERSION = None
E3NN_JAX_IMPORT_ERROR = None
try:
    import e3nn_jax as e3nn

    TOOL_MANIFEST["e3nn_jax"]["tried"] = True
    TOOL_MANIFEST["e3nn_jax"]["used"] = True
    TOOL_MANIFEST["e3nn_jax"]["reason"] = (
        "load-bearing capability under test: e3nn_jax Irreps.D_from_matrix, "
        "spherical_harmonics, matrix_z, and JAX-vmapped rotation equivariance "
        "decide the receipt verdicts."
    )
    E3NN_JAX_OK = True
    E3NN_JAX_VERSION = getattr(e3nn, "__version__", "unknown")
except Exception as exc:  # pragma: no cover - exercised only when package is missing
    E3NN_JAX_IMPORT_ERROR = repr(exc)
    TOOL_MANIFEST["e3nn_jax"]["reason"] = f"not installed/importable: {exc}"


TOL = 1.0e-10
NEGATIVE_MIN = 1.0e-2


def _float(x) -> float:
    return float(jax.device_get(x))


def _max_abs(x) -> float:
    return _float(jnp.max(jnp.abs(x)))


def _rotation_z(theta: float):
    return e3nn.matrix_z(jnp.asarray(theta, dtype=jnp.float64))


def _equivariant_map(x):
    # Nonlinear radial scaling times a vector remains SO(3)-equivariant:
    # f(Rx) = ||x||^2 Rx = R f(x).
    return jnp.sum(x * x) * x


def _spherical_array(x):
    y = e3nn.spherical_harmonics(
        e3nn.Irreps("1x1o"),
        x,
        normalize=True,
        normalization="component",
    )
    return y.array


def _section_all_pass(section: dict) -> bool:
    return all(bool(v.get("pass", False)) for v in section.values())


def run_positive_tests() -> dict:
    r = {}
    if not E3NN_JAX_OK:
        r["e3nn_jax_available"] = {
            "pass": False,
            "importable": False,
            "error": E3NN_JAX_IMPORT_ERROR,
        }
        return r

    r["e3nn_jax_available"] = {"pass": True, "version": E3NN_JAX_VERSION}
    r["jax_x64_enabled"] = {
        "pass": bool(jax.config.jax_enable_x64),
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "jax_version": getattr(jax, "__version__", "unknown"),
    }

    irreps = e3nn.Irreps("1x1o")
    r["irrep_parsing"] = {
        "pass": irreps.dim == 3,
        "irreps": str(irreps),
        "dim": irreps.dim,
    }

    x = jnp.array([0.7, -1.1, 0.4], dtype=jnp.float64)
    R = _rotation_z(0.73)
    D = irreps.D_from_matrix(R)
    fx = _equivariant_map(x)
    residual = jnp.linalg.norm(D @ fx - _equivariant_map(R @ x))
    r["so3_equivariant_map_residual"] = {
        "pass": _float(residual) < TOL,
        "l2_residual": _float(residual),
        "threshold": TOL,
    }

    y = _spherical_array(x)
    y_rot = _spherical_array(R @ x)
    sh_residual = jnp.linalg.norm(D @ y - y_rot)
    r["spherical_harmonics_transform_consistency"] = {
        "pass": _float(sh_residual) < TOL,
        "l2_residual": _float(sh_residual),
        "threshold": TOL,
    }

    angles = jnp.linspace(0.1, 1.0, 7, dtype=jnp.float64)

    def one_rotation(theta):
        Ri = _rotation_z(theta)
        Di = irreps.D_from_matrix(Ri)
        return jnp.linalg.norm(Di @ _equivariant_map(x) - _equivariant_map(Ri @ x))

    batch_residuals = jax.vmap(one_rotation)(angles)
    r["vmap_batch_rotation_equivariance"] = {
        "pass": _float(jnp.max(batch_residuals)) < TOL,
        "max_l2_residual": _float(jnp.max(batch_residuals)),
        "batch_size": int(angles.shape[0]),
        "threshold": TOL,
    }

    D_1o = irreps.D_from_matrix(R)
    orth_err = _max_abs(D_1o @ D_1o.T - jnp.eye(3, dtype=jnp.float64))
    r["D_matrix_orthogonal"] = {
        "pass": orth_err < TOL,
        "max_abs_err": orth_err,
        "threshold": TOL,
    }

    return r


def run_negative_tests() -> dict:
    r = {}
    if not E3NN_JAX_OK:
        r["e3nn_jax_available"] = {"pass": False, "detail": "e3nn_jax missing"}
        return r

    raised = False
    err = None
    try:
        _ = e3nn.Irreps("not_a_real_irrep_string!!")
    except Exception as exc:
        raised = True
        err = type(exc).__name__
    r["bad_irrep_raises"] = {"pass": raised, "error_type": err}

    irreps = e3nn.Irreps("1x1o")
    x = jnp.array([0.7, -1.1, 0.4], dtype=jnp.float64)
    R = _rotation_z(0.73)
    D_wrong = irreps.D_from_matrix(R.T)
    wrong_residual = jnp.linalg.norm(D_wrong @ _equivariant_map(x) - _equivariant_map(R @ x))
    r["transposed_rotation_breaks_equivariance"] = {
        "pass": _float(wrong_residual) > NEGATIVE_MIN,
        "l2_residual": _float(wrong_residual),
        "minimum_expected": NEGATIVE_MIN,
    }

    reflection = jnp.diag(jnp.array([1.0, 1.0, -1.0], dtype=jnp.float64))
    D_reflected = irreps.D_from_matrix(reflection @ R)
    reflected_residual = jnp.linalg.norm(D_reflected @ _equivariant_map(x) - _equivariant_map(R @ x))
    r["reflected_transform_breaks_equivariance"] = {
        "pass": _float(reflected_residual) > NEGATIVE_MIN,
        "l2_residual": _float(reflected_residual),
        "minimum_expected": NEGATIVE_MIN,
    }

    wrong_sh = jnp.linalg.norm(D_wrong @ _spherical_array(x) - _spherical_array(R @ x))
    r["wrong_spherical_harmonics_transform_fails"] = {
        "pass": _float(wrong_sh) > NEGATIVE_MIN,
        "l2_residual": _float(wrong_sh),
        "minimum_expected": NEGATIVE_MIN,
    }

    return r


def run_boundary_tests() -> dict:
    r = {}
    if not E3NN_JAX_OK:
        r["e3nn_jax_available"] = {"pass": False, "detail": "e3nn_jax missing"}
        return r

    irreps = e3nn.Irreps("1x1o")
    x = jnp.array([0.7, -1.1, 0.4], dtype=jnp.float64)

    I = jnp.eye(3, dtype=jnp.float64)
    D_identity = irreps.D_from_matrix(I)
    identity_residual = jnp.linalg.norm(D_identity @ _equivariant_map(x) - _equivariant_map(I @ x))
    r["identity_rotation_exact"] = {
        "pass": _float(identity_residual) < TOL,
        "l2_residual": _float(identity_residual),
        "threshold": TOL,
    }

    R_2pi = _rotation_z(2.0 * math.pi)
    D_2pi = irreps.D_from_matrix(R_2pi)
    two_pi_err = _max_abs(D_2pi - I)
    r["two_pi_integer_spin_identity"] = {
        "pass": two_pi_err < TOL,
        "max_abs_err": two_pi_err,
        "threshold": TOL,
    }

    y_identity = _spherical_array(x)
    sh_identity = jnp.linalg.norm(D_identity @ y_identity - _spherical_array(x))
    r["identity_spherical_harmonics_exact"] = {
        "pass": _float(sh_identity) < TOL,
        "l2_residual": _float(sh_identity),
        "threshold": TOL,
    }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    summary = {
        "positive_all_pass": _section_all_pass(pos),
        "negative_all_pass": _section_all_pass(neg),
        "boundary_all_pass": _section_all_pass(bnd),
        "importable": E3NN_JAX_OK,
        "jax_x64_enabled": bool(jax.config.jax_enable_x64),
    }
    summary["all_pass"] = bool(
        E3NN_JAX_OK
        and summary["jax_x64_enabled"]
        and summary["positive_all_pass"]
        and summary["negative_all_pass"]
        and summary["boundary_all_pass"]
    )

    results = {
        "name": "sim_e3nn_jax_capability",
        "purpose": (
            "Tool-capability isolation probe for e3nn_jax -- SO(3) vector-irrep "
            "D-matrix equivariance, spherical-harmonics transform consistency, "
            "JAX-native vmap batching, and fail-capable wrong-transform controls."
        ),
        "schema_version": "capability_probe_v1",
        "classification": classification,
        "promotion_allowed": False,
        "claim_ceiling": (
            "bounded capability probe only; closes JAX-side e3nn_jax equivariance "
            "capability gap but does not promote a lego, bridge, axis, GStack, or "
            "nonclassical carrier claim"
        ),
        "python_executable": sys.executable,
        "jax_version": getattr(jax, "__version__", "unknown"),
        "jax_x64_enabled": bool(jax.config.jax_enable_x64),
        "e3nn_jax_version": E3NN_JAX_VERSION,
        "importable": E3NN_JAX_OK,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "operation_sequence": [
            "enable JAX x64 before importing jax.numpy",
            "parse e3nn_jax Irreps('1x1o') and compute D_from_matrix for a known SO(3) z rotation",
            "check D(R) f(x) == f(R x) for the explicit nonlinear vector-equivariant map f(x)=||x||^2 x",
            "check spherical harmonics transform consistency under the same rotation",
            "vmap the equivariance residual over a batch of known rotations",
            "run wrong transposed/reflected transform controls that must exceed tolerance",
            "run boundary controls for identity rotation and 2pi integer-spin identity",
        ],
        "observable": {
            "equivariance_residual": "l2 residual between D(R) f(x) and f(R x)",
            "spherical_harmonics_residual": "l2 residual between D(R)Y(x) and Y(Rx)",
            "vmap_batch_residual": "max l2 residual across a JAX-vmapped batch of rotations",
            "negative_controls": "transposed and reflected transforms must produce residuals above threshold",
            "boundary_controls": "identity and 2pi integer-spin D-matrices must act as identity",
        },
        "pass_fail_predicate": (
            "E3NN_JAX_OK, jax x64, positive_all_pass, negative_all_pass, and "
            "boundary_all_pass must all be true; positive and boundary residuals "
            "must be below tolerance while wrong-transform controls must exceed "
            "the negative threshold."
        ),
        "tool_function_needs": [
            "e3nn_jax.Irreps",
            "Irreps.D_from_matrix",
            "e3nn_jax.spherical_harmonics",
            "e3nn_jax.matrix_z",
            "jax.vmap",
        ],
        "aligned_packages_load_bearing": ["e3nn_jax"],
        "reads_peer_result": False,
        "surviving_alternatives": [
            "This receipt covers only bounded e3nn_jax equivariance API capability; it does not promote spinor geometry, graph equivariance, bridge, axis, GStack, or nonclassical admission."
        ],
        "demotion_condition": (
            "Demote this e3nn_jax capability receipt if D_from_matrix equivariance, "
            "spherical-harmonics transform consistency, vmap batching, wrong-transform "
            "controls, or identity/2pi boundary controls fail on rerun."
        ),
        "out_of_scope": [
            "no spinor-geometry lego promotion",
            "no graph-equivariance promotion",
            "no bridge claim",
            "no axis claim",
            "no GStack claim",
            "no nonclassical admission",
        ],
    }

    results = apply_default_receipt_boundary(
        results,
        source_name="sim_e3nn_jax_capability",
        target=(
            "Use as bounded JAX-side e3nn_jax SO(3)-equivariance capability "
            "evidence before exact equivariance lego-fit or coupling packets."
        ),
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "e3nn_jax_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
