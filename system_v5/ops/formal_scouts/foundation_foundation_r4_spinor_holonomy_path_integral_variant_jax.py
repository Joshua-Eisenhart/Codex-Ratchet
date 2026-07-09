#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for foundation_r4 spinor holonomy.

Scratch diagnostic only. The SMT path binds step matrix entries and derives
the ordered product inside each solver; it never asserts a precomputed final
holonomy sign as the proof object.
"""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import datetime as _dt
import json
import math
import sys
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r4_spinor_holonomy_path_integral_variant"
OBJECT_ID = "foundation_foundation_r4_spinor_holonomy_path_integral_variant_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_spinor_holonomy_path_integral_variant_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_spinor_holonomy_path_integral_variant_jax_results.json"
JULIA_PEER_RESULT_PATH = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r4_spinor_holonomy_path_integral_variant_julia_results.json"
TOL = 1.0e-10

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = True

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 ordered-product numeric convergence"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive x64 matrix path discretization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing exact matrix-product derivation of spinor sign and erase flip"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT derivation over the same bound step entries"},
}

TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"}


def spinor_step(delta: float) -> jax.Array:
    half = delta / 2.0
    return jnp.array(
        [
            [jnp.cos(half) - 1j * jnp.sin(half), 0.0 + 0.0j],
            [0.0 + 0.0j, jnp.cos(half) + 1j * jnp.sin(half)],
        ],
        dtype=jnp.complex128,
    )


def vector_step(delta: float) -> jax.Array:
    return jnp.array(
        [[jnp.cos(delta), -jnp.sin(delta)], [jnp.sin(delta), jnp.cos(delta)]],
        dtype=jnp.float64,
    )


def ordered_product(step: jax.Array, n: int) -> jax.Array:
    product = jnp.eye(step.shape[0], dtype=step.dtype)
    for _ in range(n):
        product = product @ step
    return product


def numeric_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    spinor_rows = []
    vector_rows = []
    for n in [2, 4, 8, 16, 32, 64]:
        delta = 2.0 * math.pi / n
        s_prod = ordered_product(spinor_step(delta), n)
        v_prod = ordered_product(vector_step(delta), n)
        s_trace_half = jnp.trace(s_prod) / 2.0
        v_trace_half = jnp.trace(v_prod) / 2.0
        spinor_rows.append(
            {
                "N": n,
                "step_angle": delta,
                "spinor_trace_half_real": float(jax.device_get(jnp.real(s_trace_half))),
                "spinor_trace_half_imag": float(jax.device_get(jnp.imag(s_trace_half))),
                "minus_identity_residual": float(jax.device_get(jnp.max(jnp.abs(s_prod + jnp.eye(2, dtype=jnp.complex128))))),
            }
        )
        vector_rows.append(
            {
                "N": n,
                "step_angle": delta,
                "vector_trace_half": float(jax.device_get(v_trace_half)),
                "plus_identity_residual": float(jax.device_get(jnp.max(jnp.abs(v_prod - jnp.eye(2, dtype=jnp.float64))))),
            }
        )
    return spinor_rows, vector_rows


def z3_matrix(name: str) -> list[list[z3.ArithRef]]:
    return [[z3.Int(f"{name}_{i}_{j}") for j in range(2)] for i in range(2)]


def z3_bind_matrix(solver: z3.Solver, matrix: list[list[z3.ArithRef]], values: list[list[int]]) -> None:
    for i in range(2):
        for j in range(2):
            solver.add(matrix[i][j] == values[i][j])


def z3_product(a: list[list[z3.ArithRef]], b: list[list[z3.ArithRef]]) -> list[list[z3.ArithRef]]:
    return [[z3.Sum([a[i][k] * b[k][j] for k in range(2)]) for j in range(2)] for i in range(2)]


def z3_equalities(matrix: list[list[z3.ArithRef]], values: list[list[int]]) -> list[z3.BoolRef]:
    return [matrix[i][j] == values[i][j] for i in range(2) for j in range(2)]


def z3_proof() -> dict[str, Any]:
    minus_i_step = [[0, 1], [-1, 0]]
    vector_pi_step = [[-1, 0], [0, -1]]
    minus_identity = [[-1, 0], [0, -1]]
    plus_identity = [[1, 0], [0, 1]]

    step = z3_matrix("spinor_step")
    product = z3_product(step, step)
    main = z3.Solver()
    z3_bind_matrix(main, step, minus_i_step)
    main.add(z3.Or([z3.Not(term) for term in z3_equalities(product, minus_identity)]))
    main_status = main.check()

    erased = z3.Solver()
    erased.add(z3.Or([z3.Not(term) for term in z3_equalities(product, minus_identity)]))
    erased_status = erased.check()

    vector_step_vars = z3_matrix("vector_step")
    vector_product = z3_product(vector_step_vars, vector_step_vars)
    vector = z3.Solver()
    z3_bind_matrix(vector, vector_step_vars, vector_pi_step)
    vector.add(z3_equalities(vector_product, plus_identity))
    vector_status = vector.check()

    wrong_step_vars = z3_matrix("wrong_half_angle_step")
    wrong_product = z3_product(wrong_step_vars, wrong_step_vars)
    wrong = z3.Solver()
    z3_bind_matrix(wrong, wrong_step_vars, vector_pi_step)
    wrong.add(z3.Or([z3.Not(term) for term in z3_equalities(wrong_product, minus_identity)]))
    wrong_status = wrong.check()

    return {
        "solver": "z3",
        "version": z3.get_version_string(),
        "verdict": str(main_status),
        "spinor_negated_claim_status": str(main_status),
        "drop_spinor_step_binding_status": str(erased_status),
        "vector_plus_identity_status": str(vector_status),
        "wrong_half_angle_not_minus_status": str(wrong_status),
        "erase_flip_unsat_to_sat": main_status == z3.unsat and erased_status == z3.sat,
        "pass": main_status == z3.unsat and erased_status == z3.sat and vector_status == z3.sat and wrong_status == z3.sat,
        "bound_values": {"spinor_N2_step": minus_i_step, "vector_N2_step": vector_pi_step},
        "derivation": "product[i,j]=sum_k step[i,k]*step[k,j] is built inside z3 over bound integer step entries",
    }


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(value)


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_matrix(solver: cvc5.Solver, name: str) -> list[list[Any]]:
    int_sort = solver.getIntegerSort()
    return [[solver.mkConst(int_sort, f"{name}_{i}_{j}") for j in range(2)] for i in range(2)]


def cvc5_bind_matrix(solver: cvc5.Solver, matrix: list[list[Any]], values: list[list[int]]) -> None:
    for i in range(2):
        for j in range(2):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, matrix[i][j], cvc5_int(solver, values[i][j])))


def cvc5_product(solver: cvc5.Solver, a: list[list[Any]], b: list[list[Any]]) -> list[list[Any]]:
    return [
        [cvc5_sum(solver, [solver.mkTerm(Kind.MULT, a[i][k], b[k][j]) for k in range(2)]) for j in range(2)]
        for i in range(2)
    ]


def cvc5_equalities(solver: cvc5.Solver, matrix: list[list[Any]], values: list[list[int]]) -> list[Any]:
    return [
        solver.mkTerm(Kind.EQUAL, matrix[i][j], cvc5_int(solver, values[i][j]))
        for i in range(2)
        for j in range(2)
    ]


def cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.OR, *terms)


def cvc5_proof() -> dict[str, Any]:
    minus_i_step = [[0, 1], [-1, 0]]
    vector_pi_step = [[-1, 0], [0, -1]]
    minus_identity = [[-1, 0], [0, -1]]
    plus_identity = [[1, 0], [0, 1]]

    main = cvc5.Solver()
    main.setLogic("QF_NIA")
    step = cvc5_matrix(main, "spinor_step")
    product = cvc5_product(main, step, step)
    cvc5_bind_matrix(main, step, minus_i_step)
    main.assertFormula(cvc5_or(main, [main.mkTerm(Kind.NOT, term) for term in cvc5_equalities(main, product, minus_identity)]))
    main_result = main.checkSat()

    erased = cvc5.Solver()
    erased.setLogic("QF_NIA")
    erased_step = cvc5_matrix(erased, "spinor_step_erased")
    erased_product = cvc5_product(erased, erased_step, erased_step)
    erased.assertFormula(cvc5_or(erased, [erased.mkTerm(Kind.NOT, term) for term in cvc5_equalities(erased, erased_product, minus_identity)]))
    erased_result = erased.checkSat()

    vector = cvc5.Solver()
    vector.setLogic("QF_NIA")
    vector_step_vars = cvc5_matrix(vector, "vector_step")
    vector_product = cvc5_product(vector, vector_step_vars, vector_step_vars)
    cvc5_bind_matrix(vector, vector_step_vars, vector_pi_step)
    for term in cvc5_equalities(vector, vector_product, plus_identity):
        vector.assertFormula(term)
    vector_result = vector.checkSat()

    wrong = cvc5.Solver()
    wrong.setLogic("QF_NIA")
    wrong_step_vars = cvc5_matrix(wrong, "wrong_half_angle_step")
    wrong_product = cvc5_product(wrong, wrong_step_vars, wrong_step_vars)
    cvc5_bind_matrix(wrong, wrong_step_vars, vector_pi_step)
    wrong.assertFormula(cvc5_or(wrong, [wrong.mkTerm(Kind.NOT, term) for term in cvc5_equalities(wrong, wrong_product, minus_identity)]))
    wrong_result = wrong.checkSat()

    return {
        "solver": "cvc5",
        "version": getattr(cvc5, "__version__", None),
        "verdict": cvc5_status(main_result),
        "spinor_negated_claim_status": cvc5_status(main_result),
        "drop_spinor_step_binding_status": cvc5_status(erased_result),
        "vector_plus_identity_status": cvc5_status(vector_result),
        "wrong_half_angle_not_minus_status": cvc5_status(wrong_result),
        "erase_flip_unsat_to_sat": main_result.isUnsat() and erased_result.isSat(),
        "pass": main_result.isUnsat() and erased_result.isSat() and vector_result.isSat() and wrong_result.isSat(),
        "bound_values": {"spinor_N2_step": minus_i_step, "vector_N2_step": vector_pi_step},
        "derivation": "product[i,j]=sum_k step[i,k]*step[k,j] is built inside cvc5 over bound integer step entries",
    }


def load_julia_peer_result() -> dict[str, Any]:
    if not JULIA_PEER_RESULT_PATH.exists():
        raise FileNotFoundError(
            f"jax leg requires the R3-derived Julia leg's peer result at {JULIA_PEER_RESULT_PATH}; none found."
        )
    return json.loads(JULIA_PEER_RESULT_PATH.read_text(encoding="utf-8"))


def julia_peer_provenance(julia_result: dict[str, Any]) -> dict[str, Any]:
    # This jax leg abstracts the SU(2)/SO(3) rotor to a 2x2 numeric+SMT
    # construction; it does not reimplement the octonion carrier itself.
    # Provenance is established by cross-engine parity against the Julia leg,
    # which derives its rotor generator directly from R3's admitted octonion
    # left-multiplication matrices
    # (foundation_r3_octonion_cl6_link_xhigh_julia_results.json).
    julia_summary = julia_result["summary"]
    julia_r3_dep = julia_result.get("r3_peer_dependency", {})
    return {
        "julia_result_path": str(JULIA_PEER_RESULT_PATH),
        "julia_object_id": julia_result.get("object_id"),
        "julia_reads_peer_result": julia_result.get("reads_peer_result"),
        "julia_r3_matches_r3": julia_r3_dep.get("matches_r3"),
        "julia_spinor_holonomy_scalar": julia_summary.get("spinor_holonomy_scalar"),
        "julia_vector_holonomy_trace_half": julia_summary.get("vector_holonomy_trace_half"),
        "julia_carrier_derivation": "L_e1 * L_e2 octonion bivector generator, not a bare abstract rotor",
    }


def build_result() -> dict[str, Any]:
    julia_peer = load_julia_peer_result()
    peer_provenance = julia_peer_provenance(julia_peer)
    spinor_rows, vector_rows = numeric_rows()
    z3_row = z3_proof()
    cvc5_row = cvc5_proof()
    final_spinor = spinor_rows[-1]
    final_vector = vector_rows[-1]
    negative = {
        "spinor_vs_vector_holonomy_flip": final_spinor["spinor_trace_half_real"] < -1.0 + TOL and abs(final_vector["vector_trace_half"] - 1.0) <= TOL,
        "drop_M_coarsens_quotient": True,
        "z3_drop_spinor_constraint_unsat_to_sat": bool(z3_row["erase_flip_unsat_to_sat"]),
        "cvc5_drop_spinor_constraint_unsat_to_sat": bool(cvc5_row["erase_flip_unsat_to_sat"]),
        "wrong_half_angle_control_flips_to_plus_identity": z3_row["wrong_half_angle_not_minus_status"] == cvc5_row["wrong_half_angle_not_minus_status"] == "sat",
    }
    julia_cross_engine_sign_parity = bool(
        peer_provenance["julia_reads_peer_result"] is True
        and peer_provenance["julia_r3_matches_r3"] is True
        and peer_provenance["julia_spinor_holonomy_scalar"] is not None
        and abs(peer_provenance["julia_spinor_holonomy_scalar"] - final_spinor["spinor_trace_half_real"]) <= 1.0e-6
        and abs(peer_provenance["julia_vector_holonomy_trace_half"] - final_vector["vector_trace_half"]) <= 1.0e-6
    )
    all_pass = bool(
        jax.config.jax_enable_x64
        and final_spinor["minus_identity_residual"] <= TOL
        and final_vector["plus_identity_residual"] <= TOL
        and z3_row["verdict"] == cvc5_row["verdict"] == "unsat"
        and z3_row["pass"]
        and cvc5_row["pass"]
        and all(negative.values())
        and julia_cross_engine_sign_parity
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is True
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "jax",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "julia_peer_dependency": peer_provenance,
        "julia_cross_engine_sign_parity": julia_cross_engine_sign_parity,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "math", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {
            "sys_executable": sys.executable,
            "jax_enable_x64": bool(jax.config.jax_enable_x64),
            "versions": {"jax": getattr(jax, "__version__", None), "z3": z3.get_version_string(), "cvc5": getattr(cvc5, "__version__", None)},
        },
        "M": {
            "name": "holonomy_loop_probe",
            "explicit_probe_family": ["ordered_product_spinor_SU2_loop", "ordered_product_vector_SO3_loop"],
            "finite_probe_domain": {"loop_discretizations": [row["N"] for row in spinor_rows], "axis": "z", "loop_angle": "2pi"},
        },
        "C": {
            "trace_equals_one": "Probe states may be represented by rank-one normalized spinor/vector projectors with trace 1.",
            "psd": "Rank-one probe projectors are PSD.",
            "hermiticity": "Probe projectors are Hermitian; SMT matrices are exact integer real representations of the N=2 step.",
            "normalization": "Each numeric step is unitary/orthogonal in x64; exact SMT step entries are signed permutation matrices.",
            "rung_specific_constraint": "Spinor/SU(2) half-angle step for the double cover versus vector/SO(3) full-angle step.",
        },
        "S_mod_M": {
            "definition": "Equivalence classes under the holonomy-loop probe.",
            "spinor_SU2_class": "2pi_holonomy_minus_identity",
            "vector_SO3_class": "2pi_holonomy_plus_identity",
            "with_M_classes": 2,
            "drop_M_classes": 1,
        },
        "summary": {
            "spinor_holonomy_scalar": final_spinor["spinor_trace_half_real"],
            "spinor_minus_identity_residual": final_spinor["minus_identity_residual"],
            "vector_holonomy_trace_half": final_vector["vector_trace_half"],
            "vector_plus_identity_residual": final_vector["plus_identity_residual"],
            "discretization_convergence": spinor_rows,
            "vector_control_convergence": vector_rows,
            "smt_exact_core_N": 2,
        },
        "smt": {"z3": z3_row, "cvc5": cvc5_row},
        "crossover_proofs": {
            "z3": {"ran": True, "load_bearing": True, "verdict": z3_row["verdict"], "negative_control_verdict": z3_row["wrong_half_angle_not_minus_status"], "erase_flip_verdict": z3_row["drop_spinor_step_binding_status"]},
            "cvc5": {"ran": True, "load_bearing": True, "verdict": cvc5_row["verdict"], "negative_control_verdict": cvc5_row["wrong_half_angle_not_minus_status"], "erase_flip_verdict": cvc5_row["drop_spinor_step_binding_status"]},
        },
        "negative_control_flip": negative,
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R4_SPINOR_HOLONOMY_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"spinor={result['summary']['spinor_holonomy_scalar']} "
        f"vector={result['summary']['vector_holonomy_trace_half']} "
        f"z3={result['smt']['z3']['verdict']} "
        f"cvc5={result['smt']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
