#!/usr/bin/env python3
"""JAX/SymPy/SMT leg for the SO(3)-vs-SU(2) S1 discriminator."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_vector_vs_spinor_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
PIN_SPEC = (
    "geo_s1_vector_vs_spinor_v0|routes=SO3_vector_vs_SU2_spinor|"
    "U(theta)=diag(exp(-i theta/2),exp(i theta/2))|R(theta)=Rz(theta)|"
    "density_quotient=psi psi_dagger|compare_2pi_4pi|"
    "classification=scratch_diagnostic|promotion_allowed=false"
)

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic SU(2)->SO(3) map and U/-U quotient derivation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite discriminator truth-table proof",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite discriminator truth-table proof",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive vectorized continuous-path sample evaluation",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive array substrate for sampled path distances",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "jax": "supportive",
    "jax.numpy": "supportive",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def matrix_to_strings(matrix: sp.Matrix) -> list[list[str]]:
    return [[sp.sstr(sp.simplify(matrix[i, j])) for j in range(matrix.cols)] for i in range(matrix.rows)]


def su2_to_so3_symbolic() -> dict[str, Any]:
    c, s = sp.symbols("c s", real=True)
    u = sp.Matrix([[c - sp.I * s, 0], [0, c + sp.I * s]])
    minus_u = -u
    sigmas = [
        sp.Matrix([[0, 1], [1, 0]]),
        sp.Matrix([[0, -sp.I], [sp.I, 0]]),
        sp.Matrix([[1, 0], [0, -1]]),
    ]

    def map_matrix(unitary: sp.Matrix) -> sp.Matrix:
        return sp.Matrix(
            3,
            3,
            lambda i, j: sp.simplify(sp.trace(sigmas[i] * unitary * sigmas[j] * unitary.conjugate().T) / 2),
        )

    r_u = map_matrix(u)
    r_minus = map_matrix(minus_u)
    reduced = sp.simplify(r_u.subs(c**2 + s**2, 1))
    expected = sp.Matrix([[c**2 - s**2, 2 * c * s, 0], [-2 * c * s, c**2 - s**2, 0], [0, 0, c**2 + s**2]])
    quotient_diff = sp.simplify(r_u - r_minus)
    return {
        "map": "R_ij = 1/2 Tr(sigma_i U sigma_j U^dagger)",
        "U_parameterization": "diag(c - i s, c + i s), c^2+s^2=1",
        "R_from_U": matrix_to_strings(r_u),
        "R_expected_z_form": matrix_to_strings(expected),
        "R_minus_expected": matrix_to_strings(sp.simplify(r_u - expected)),
        "R_from_U_minus_R_from_minus_U": matrix_to_strings(quotient_diff),
        "double_cover_collision_symbolic": all(sp.simplify(item) == 0 for item in quotient_diff),
        "unit_reduced_R": matrix_to_strings(reduced),
        "pass": all(sp.simplify(item) == 0 for item in quotient_diff),
    }


def su2_z(theta: jax.Array) -> jax.Array:
    return jnp.array(
        [[jnp.cos(theta / 2) - 1j * jnp.sin(theta / 2), 0.0j], [0.0j, jnp.cos(theta / 2) + 1j * jnp.sin(theta / 2)]],
        dtype=jnp.complex128,
    )


def so3_z(theta: jax.Array) -> jax.Array:
    c = jnp.cos(theta)
    s = jnp.sin(theta)
    return jnp.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=jnp.float64)


def sampled_path_receipt() -> dict[str, Any]:
    angles = jnp.linspace(0.0, 4.0 * jnp.pi, 33, dtype=jnp.float64)
    i2 = jnp.eye(2, dtype=jnp.complex128)
    i3 = jnp.eye(3, dtype=jnp.float64)
    so3_distances = jax.vmap(lambda t: jnp.linalg.norm(so3_z(t) - i3))(angles)
    su2_identity_distances = jax.vmap(lambda t: jnp.linalg.norm(su2_z(t) - i2))(angles)
    su2_minus_identity_distances = jax.vmap(lambda t: jnp.linalg.norm(su2_z(t) + i2))(angles)
    index_2pi = int(jnp.argmin(jnp.abs(angles - 2.0 * jnp.pi)))
    index_4pi = int(jnp.argmin(jnp.abs(angles - 4.0 * jnp.pi)))
    vector_closes_at_2pi = bool(so3_distances[index_2pi] < 1e-12)
    spinor_closes_at_2pi = bool(su2_identity_distances[index_2pi] < 1e-12)
    vector_closes_at_4pi = bool(so3_distances[index_4pi] < 1e-12)
    spinor_closes_at_4pi = bool(su2_identity_distances[index_4pi] < 1e-12)
    n01_closure_order_gap = int(vector_closes_at_2pi) - int(spinor_closes_at_2pi)
    return {
        "angle_count": int(angles.shape[0]),
        "angle_grid_endpoints": [float(angles[0]), float(angles[-1])],
        "so3_distance_at_2pi": float(so3_distances[index_2pi]),
        "so3_distance_at_4pi": float(so3_distances[index_4pi]),
        "su2_identity_distance_at_2pi": float(su2_identity_distances[index_2pi]),
        "su2_minus_identity_distance_at_2pi": float(su2_minus_identity_distances[index_2pi]),
        "su2_identity_distance_at_4pi": float(su2_identity_distances[index_4pi]),
        "n01_closure_order_gap": {
            "name": "n01_closure_order_gap",
            "functional": "boolean identity closure at theta=2pi under each route's own representation",
            "routes": {
                "vector_SO3_Rz": {
                    "representation": "R(theta)=Rz(theta) in SO(3)",
                    "theta": "2pi",
                    "closes_to_identity": vector_closes_at_2pi,
                    "normalized_boolean_value": int(vector_closes_at_2pi),
                },
                "spinor_SU2_U": {
                    "representation": "U(theta)=diag(exp(-i theta/2), exp(i theta/2)) in SU(2)",
                    "theta": "2pi",
                    "closes_to_identity": spinor_closes_at_2pi,
                    "normalized_boolean_value": int(spinor_closes_at_2pi),
                },
            },
            "gap_direction": "vector_minus_spinor",
            "gap": n01_closure_order_gap,
            "four_pi_check": {
                "vector_closes_to_identity": vector_closes_at_4pi,
                "spinor_closes_to_identity": spinor_closes_at_4pi,
            },
            "scale": "normalized_boolean_closure_not_raw_matrix_norm",
            "raw_norm_cross_dimension_comparison_excluded": True,
            "exclusion_reason": "does not compare ||R-I3|| with ||U-I2|| as one numeric gap because the representations have different matrix dimensions",
            "pass": n01_closure_order_gap == 1 and vector_closes_at_4pi and spinor_closes_at_4pi,
        },
        "pass": bool(
            so3_distances[index_2pi] < 1e-12
            and su2_identity_distances[index_2pi] > 1.0
            and su2_minus_identity_distances[index_2pi] < 1e-12
            and su2_identity_distances[index_4pi] < 1e-12
            and n01_closure_order_gap == 1
        ),
    }


def density_quotient_symbolic() -> dict[str, Any]:
    a, b = sp.symbols("a b", real=True)
    psi = sp.Matrix([a + sp.I * b, 0])
    minus_psi = -psi
    rho = psi * psi.conjugate().T
    minus_rho = minus_psi * minus_psi.conjugate().T
    spinor_delta = sp.simplify(sum((psi[i] - minus_psi[i]) * sp.conjugate(psi[i] - minus_psi[i]) for i in range(2)))
    density_delta = sp.simplify(rho - minus_rho)
    return {
        "spinor_squared_distance_psi_to_minus_psi": sp.sstr(sp.expand(spinor_delta)),
        "density_difference": matrix_to_strings(density_delta),
        "density_quotient_collapses_sign_symbolic": all(sp.simplify(item) == 0 for item in density_delta),
        "pass": all(sp.simplify(item) == 0 for item in density_delta) and sp.simplify(spinor_delta) != 0,
    }


def z3_truth_table(actuals: dict[str, bool]) -> str:
    solver = z3.Solver()
    terms = {name: z3.Bool(name) for name in actuals}
    for name, value in actuals.items():
        solver.add(terms[name] == bool(value))
    accepted = z3.Bool("route_discriminator_accepts")
    solver.add(accepted == z3.And(*[terms[name] for name in sorted(terms)]))
    solver.add(z3.Not(accepted))
    return str(solver.check())


def cvc5_truth_table(actuals: dict[str, bool]) -> str:
    solver = cvc5.Solver()
    bool_sort = solver.getBooleanSort()
    terms = {name: solver.mkConst(bool_sort, name) for name in actuals}
    for name, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[name], solver.mkBoolean(bool(value))))
    accepted = solver.mkConst(bool_sort, "route_discriminator_accepts")
    conjunction = solver.mkTerm(Kind.AND, *[terms[name] for name in sorted(terms)])
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, accepted, conjunction))
    solver.assertFormula(solver.mkTerm(Kind.NOT, accepted))
    return str(solver.checkSat())


def build_proofs(actuals: dict[str, bool]) -> dict[str, Any]:
    corrupted = dict(actuals)
    corrupted["su2_2pi_not_closed"] = False
    return {
        "z3": {
            "nominal_not_accepted": z3_truth_table(actuals),
            "corrupted_control_not_accepted": z3_truth_table(corrupted),
        },
        "cvc5": {
            "nominal_not_accepted": cvc5_truth_table(actuals),
            "corrupted_control_not_accepted": cvc5_truth_table(corrupted),
        },
        "actuals": actuals,
        "corrupted_actuals": corrupted,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    map_receipt = su2_to_so3_symbolic()
    path_receipt = sampled_path_receipt()
    density_receipt = density_quotient_symbolic()
    actuals = {
        "so3_2pi_closed": path_receipt["so3_distance_at_2pi"] < 1e-12,
        "su2_2pi_not_closed": path_receipt["su2_identity_distance_at_2pi"] > 1.0
        and path_receipt["su2_minus_identity_distance_at_2pi"] < 1e-12,
        "su2_4pi_closed": path_receipt["su2_identity_distance_at_4pi"] < 1e-12,
        "n01_closure_order_gap_pass": path_receipt["n01_closure_order_gap"]["pass"],
        "u_minus_u_same_rotation": map_receipt["double_cover_collision_symbolic"],
        "spinor_sign_visible_before_density": density_receipt["spinor_squared_distance_psi_to_minus_psi"] != "0",
        "density_quotient_collapses_sign": density_receipt["density_quotient_collapses_sign_symbolic"],
    }
    proofs = build_proofs(actuals)
    proof_pass = (
        proofs["z3"]["nominal_not_accepted"] == "unsat"
        and proofs["z3"]["corrupted_control_not_accepted"] == "sat"
        and proofs["cvc5"]["nominal_not_accepted"] == "unsat"
        and proofs["cvc5"]["corrupted_control_not_accepted"] == "sat"
    )
    all_pass = bool(map_receipt["pass"] and path_receipt["pass"] and density_receipt["pass"] and proof_pass)
    payload = {
        "schema_version": f"{SIM_ID}_leg_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "role_id": "jax_rich_mirror_sim_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "packages_used": ["jax", "jax.numpy", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "route_receipts": {
            "symbolic_double_cover_map": map_receipt,
            "continuous_path_samples": path_receipt,
            "n01_closure_order_gap": path_receipt["n01_closure_order_gap"],
            "density_quotient": density_receipt,
        },
        "proofs": {
            "route_truth_table": proofs,
        },
        "shared_scalars": {
            "so3_2pi_distance": path_receipt["so3_distance_at_2pi"],
            "su2_2pi_identity_distance": path_receipt["su2_identity_distance_at_2pi"],
            "su2_4pi_identity_distance": path_receipt["su2_identity_distance_at_4pi"],
            "n01_closure_order_gap": path_receipt["n01_closure_order_gap"]["gap"],
            "density_quotient_sign_distance": 0.0,
            "u_minus_u_rotation_distance": 0.0,
        },
        "controls": {
            "corrupted_su2_2pi_closure_control": {
                "z3": proofs["z3"]["corrupted_control_not_accepted"],
                "cvc5": proofs["cvc5"]["corrupted_control_not_accepted"],
                "pass": proofs["z3"]["corrupted_control_not_accepted"] == "sat"
                and proofs["cvc5"]["corrupted_control_not_accepted"] == "sat",
            }
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "engine": "jax", "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
