#!/usr/bin/env python3
"""
sim_jax_algebra_capability -- bounded JAX-native algebra/spinor capability probe.

This isolates finite Cayley-Dickson and Clifford-gamma operations implemented
with jax.numpy, with a Z3 sidecar over computed quaternion structure constants.
It does not promote any lego, bridge, axis, or canonical theory claim.
"""

classification = "canonical"

from jax import config
config.update("jax_enable_x64", True)

import json
import os

import jax
import jax.numpy as jnp

from receipt_boundary import apply_default_receipt_boundary


_NOT_USED_REASON = (
    "not used: this bounded JAX algebra capability receipt isolates "
    "Cayley-Dickson multiplication, Clifford gamma anticommutation, vmap "
    "batching, and one SMT sidecar; other tool families require separate receipts."
)

TOOL_MANIFEST = {
    "jax_algebra": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing capability under test: jax.numpy Cayley-Dickson "
            "doubling, Clifford gamma matrices, and jax.vmap batch products "
            "decide the receipt verdicts."
        ),
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "load-bearing sidecar under test -- overwritten on import",
    },
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "jax_algebra": "load_bearing",
    "z3": "load_bearing",
    "pytorch": None,
    "pyg": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import z3

    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "load-bearing SMT sidecar: binds JAX-computed quaternion structure "
        "constants entry-wise and derives antisymmetry in solver."
    )
    Z3_OK = True
    Z3_VERSION = z3.get_version_string()
except Exception as exc:
    Z3_OK = False
    Z3_VERSION = None
    TOOL_MANIFEST["z3"]["reason"] = f"import failed: {exc}"


TOL = 1e-12
NONZERO_TOL = 1e-9


def _basis(dim: int, idx: int):
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def cd_conj(x):
    n = x.shape[0]
    if n == 1:
        return x
    half = n // 2
    return jnp.concatenate([cd_conj(x[:half]), -x[half:]])


def cd_mul(x, y):
    n = x.shape[0]
    if n == 1:
        return x * y
    half = n // 2
    a, b = x[:half], x[half:]
    c, d = y[:half], y[half:]
    left = cd_mul(a, c) - cd_mul(cd_conj(d), b)
    right = cd_mul(d, a) + cd_mul(b, cd_conj(c))
    return jnp.concatenate([left, right])


def cd_norm(x):
    return jnp.linalg.norm(x)


def norm_multiplicativity_residual(x, y):
    return jnp.abs(cd_norm(cd_mul(x, y)) - cd_norm(x) * cd_norm(y))


def associator(x, y, z):
    return cd_mul(cd_mul(x, y), z) - cd_mul(x, cd_mul(y, z))


def _float(x):
    return float(jnp.asarray(x))


def _vec(x):
    return [float(v) for v in jnp.asarray(x).tolist()]


def run_positive_tests():
    r = {}

    qi = _basis(4, 1)
    qj = _basis(4, 2)
    q_noncomm_gap = cd_norm(cd_mul(qi, qj) - cd_mul(qj, qi))
    r["quaternion_noncommutation_gap"] = {
        "gap": _float(q_noncomm_gap),
        "pass": bool(q_noncomm_gap > NONZERO_TOL),
    }

    oi = _basis(8, 1)
    oj = _basis(8, 2)
    ok = _basis(8, 4)
    oct_assoc = associator(oi, oj, ok)
    oct_assoc_norm = cd_norm(oct_assoc)
    r["octonion_associator_nonzero"] = {
        "associator_norm": _float(oct_assoc_norm),
        "associator": _vec(oct_assoc),
        "pass": bool(oct_assoc_norm > NONZERO_TOL),
    }

    qx = jnp.array([0.25, -1.5, 2.0, 0.75], dtype=jnp.float64)
    qy = jnp.array([1.25, 0.5, -0.375, 2.5], dtype=jnp.float64)
    q_resid = norm_multiplicativity_residual(qx, qy)
    r["quaternion_norm_multiplicativity"] = {
        "residual": _float(q_resid),
        "tolerance": TOL,
        "pass": bool(q_resid < TOL),
    }

    ox = jnp.array([0.5, -1.25, 0.75, 2.0, -0.5, 1.5, -2.25, 0.125], dtype=jnp.float64)
    oy = jnp.array([1.0, 0.25, -1.75, 0.5, 2.25, -0.75, 1.125, -1.5], dtype=jnp.float64)
    o_resid = norm_multiplicativity_residual(ox, oy)
    r["octonion_norm_multiplicativity"] = {
        "residual": _float(o_resid),
        "tolerance": TOL,
        "pass": bool(o_resid < TOL),
    }

    sigma_x = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
    sigma_y = jnp.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
    sigma_z = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
    gammas = jnp.stack([sigma_x, sigma_y, sigma_z])
    ident = jnp.eye(2, dtype=jnp.complex128)
    residuals = []
    for i in range(3):
        for j in range(3):
            anticom = gammas[i] @ gammas[j] + gammas[j] @ gammas[i]
            target = (2.0 if i == j else 0.0) * ident
            residuals.append(jnp.max(jnp.abs(anticom - target)))
    gamma_max_resid = jnp.max(jnp.stack(residuals))
    r["clifford_gamma_anticommutation"] = {
        "gamma_count": 3,
        "matrix_shape": [2, 2],
        "max_residual": _float(gamma_max_resid),
        "tolerance": TOL,
        "pass": bool(gamma_max_resid < TOL),
    }

    key = jax.random.PRNGKey(314159)
    k1, k2, k3, k4 = jax.random.split(key, 4)
    q_batch_x = jax.random.normal(k1, (8, 4), dtype=jnp.float64)
    q_batch_y = jax.random.normal(k2, (8, 4), dtype=jnp.float64)
    o_batch_x = jax.random.normal(k3, (8, 8), dtype=jnp.float64)
    o_batch_y = jax.random.normal(k4, (8, 8), dtype=jnp.float64)
    q_products = jax.vmap(cd_mul, in_axes=(0, 0))(q_batch_x, q_batch_y)
    o_products = jax.vmap(cd_mul, in_axes=(0, 0))(o_batch_x, o_batch_y)
    q_batch_resid = jnp.max(jax.vmap(norm_multiplicativity_residual)(q_batch_x, q_batch_y))
    o_batch_resid = jnp.max(jax.vmap(norm_multiplicativity_residual)(o_batch_x, o_batch_y))
    batch_ok = (
        q_products.shape == (8, 4)
        and o_products.shape == (8, 8)
        and bool(q_batch_resid < TOL)
        and bool(o_batch_resid < TOL)
    )
    r["vmap_batched_algebra"] = {
        "quaternion_product_shape": list(q_products.shape),
        "octonion_product_shape": list(o_products.shape),
        "quaternion_max_norm_residual": _float(q_batch_resid),
        "octonion_max_norm_residual": _float(o_batch_resid),
        "tolerance": TOL,
        "pass": bool(batch_ok),
    }

    return r


def run_negative_tests():
    r = {}

    sx = _basis(16, 1) + _basis(16, 10)
    sy = _basis(16, 4) - _basis(16, 15)
    s_prod = cd_mul(sx, sy)
    s_prod_norm = cd_norm(s_prod)
    s_resid = jnp.abs(s_prod_norm - cd_norm(sx) * cd_norm(sy))
    r["sedenion_norm_multiplicativity_fails"] = {
        "witness_x_nonzero_indices": [1, 10],
        "witness_y_nonzero_indices": [4, 15],
        "product_norm": _float(s_prod_norm),
        "norm_multiplicativity_residual": _float(s_resid),
        "pass": bool(s_resid > NONZERO_TOL),
    }

    oi = _basis(8, 1)
    oj = _basis(8, 2)
    ok = _basis(8, 4)
    assoc_norm = cd_norm(associator(oi, oj, ok))
    r["octonion_associativity_claim_fails"] = {
        "claim": "octonion multiplication is associative for all triples",
        "counterexample_basis_indices": [1, 2, 4],
        "associator_norm": _float(assoc_norm),
        "pass": bool(assoc_norm > NONZERO_TOL),
    }

    return r


def run_boundary_tests():
    r = {}

    for dim, name in [(2, "complex"), (4, "quaternion"), (8, "octonion")]:
        one = _basis(dim, 0)
        sample = jnp.linspace(-1.0, 1.0, dim, dtype=jnp.float64) + 0.25
        left_err = cd_norm(cd_mul(one, sample) - sample)
        right_err = cd_norm(cd_mul(sample, one) - sample)
        r[f"{name}_identity"] = {
            "left_err": _float(left_err),
            "right_err": _float(right_err),
            "tolerance": TOL,
            "pass": bool(left_err < TOL and right_err < TOL),
        }

    for dim, name in [(2, "complex"), (4, "quaternion"), (8, "octonion"), (16, "sedenion")]:
        sample = jnp.linspace(-1.0, 1.0, dim, dtype=jnp.float64) + 0.125
        involution_err = cd_norm(cd_conj(cd_conj(sample)) - sample)
        r[f"{name}_conjugation_involution"] = {
            "involution_err": _float(involution_err),
            "tolerance": TOL,
            "pass": bool(involution_err < TOL),
        }

    return r


def run_z3_sidecar():
    r = {}
    if not Z3_OK:
        return {
            "z3_available": {
                "pass": False,
                "detail": "z3 missing",
            }
        }

    basis = [_basis(4, i) for i in range(4)]
    constants = {}
    solver = z3.Solver()
    c_symbols = {}

    for k in range(4):
        for i in range(4):
            for j in range(4):
                coeff = int(round(_float(cd_mul(basis[i], basis[j])[k])))
                constants[f"C_{k}_{i}_{j}"] = coeff
                sym = z3.Int(f"C_{k}_{i}_{j}")
                c_symbols[(k, i, j)] = sym
                solver.add(sym == coeff)

    violation_terms = []
    for i in range(1, 4):
        for j in range(i + 1, 4):
            for k in range(4):
                violation_terms.append(c_symbols[(k, i, j)] + c_symbols[(k, j, i)] != 0)

    solver.push()
    solver.add(z3.Or(violation_terms))
    antisym_violation = solver.check()
    solver.pop()

    solver.push()
    solver.add(z3.Or([c_symbols[(k, 1, 2)] - c_symbols[(k, 2, 1)] != 0 for k in range(4)]))
    noncomm_witness = solver.check()
    solver.pop()

    r["quaternion_structure_constants_bound"] = {
        "pass": len(constants) == 64,
        "entry_count": len(constants),
        "sample": {
            "C_3_1_2": constants["C_3_1_2"],
            "C_3_2_1": constants["C_3_2_1"],
        },
    }
    r["antisymmetry_derived_in_solver"] = {
        "pass": antisym_violation == z3.unsat,
        "violation_query_result": str(antisym_violation),
        "bound_entry_count": len(constants),
    }
    r["noncommutation_witness_derived_in_solver"] = {
        "pass": noncomm_witness == z3.sat,
        "witness_query_result": str(noncomm_witness),
    }
    return r


def _collect_pass_flags(d):
    flags = []
    for value in d.values():
        if isinstance(value, dict) and "pass" in value:
            flags.append(bool(value["pass"]))
    return flags


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    side = run_z3_sidecar()
    flags = (
        _collect_pass_flags(pos)
        + _collect_pass_flags(neg)
        + _collect_pass_flags(bnd)
        + _collect_pass_flags(side)
    )
    all_pass = bool(flags) and all(flags)

    results = {
        "name": "sim_jax_algebra_capability",
        "purpose": (
            "bounded isolation probe of JAX-native algebra/spinor capability: "
            "Cayley-Dickson complex/quaternion/octonion/sedenion operations, "
            "Clifford gamma anticommutation, vmap-batched algebra, and a Z3 "
            "sidecar over computed quaternion structure constants"
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "sidecar": side,
        "tool_calls": [
            {
                "tool": "jax_algebra",
                "qualified_api/function": "jax.numpy + jax.vmap over cd_mul/gamma anticommutators",
                "input_object": "finite real Cayley-Dickson vectors and complex Clifford gamma matrices",
                "output_object": "products, associators, norm residuals, anticommutator residuals",
                "positive_case": "quaternion/octonion norm multiplicativity and gamma anticommutation pass",
                "negative/erased_control": "sedenion norm multiplicativity and octonion associativity claims fail",
                "boundary_case": "identity and conjugation involution",
                "demotion_condition": "demote if x64, vmap, algebra residuals, or boundary controls fail",
                "gates": ["all_pass"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.check",
                "input_object": "JAX-computed quaternion structure constants bound entry-wise as Int symbols",
                "output_object": "UNSAT antisymmetry-violation query and SAT noncommutation-witness query",
                "positive_case": "solver derives antisymmetry over imaginary quaternion constants",
                "negative/erased_control": "solver asks for a violation rather than accepting a precomputed boolean",
                "boundary_case": "64 finite structure constants are bound before the query",
                "demotion_condition": "demote if z3 import fails, entry binding changes, or solver verdicts drift",
                "gates": ["all_pass"],
            },
        ],
        "classification": "canonical",
        "all_pass": all_pass,
        "pass_count": int(sum(flags)),
        "total_count": int(len(flags)),
        "summary": {
            "all_pass": all_pass,
            "x64_enabled": bool(jax.config.jax_enable_x64),
            "packages_used": ["jax", "jax.numpy", "z3"],
            "aligned_packages_load_bearing": ["jax_algebra", "z3"],
            "reads_peer_result": False,
        },
        "surviving_alternatives": [
            "This receipt covers only bounded JAX-native algebra/spinor capability; it does not promote division-algebra rows, Clifford rows, bridge, axis, GStack, or nonclassical admission."
        ],
        "demotion_condition": (
            "Demote this JAX algebra capability receipt if Cayley-Dickson "
            "products, gamma anticommutation, vmap batching, negative controls, "
            "boundary controls, or the Z3 structure-constant sidecar fail on rerun."
        ),
        "out_of_scope": [
            "no division-algebra row promotion",
            "no Clifford row promotion",
            "no manifold lego promotion",
            "no bridge claim",
            "no axis claim",
            "no GStack claim",
            "no nonclassical admission",
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_jax_algebra_capability",
        target=(
            "Use as bounded JAX-native algebra/spinor capability evidence before "
            "exact tool-lego fit probes or coupling packets."
        ),
    )
    results["claim_ceiling"] = (
        "finite sim_jax_algebra_capability capability receipt only; no division-algebra "
        "row promotion, Clifford row promotion, bridge, GStack, axis, QIT, or nonclassical admission"
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "jax_algebra_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {out_path}")
    print(f"all_pass={results.get('all_pass')} pass={results.get('pass_count')}/{results.get('total_count')}")
