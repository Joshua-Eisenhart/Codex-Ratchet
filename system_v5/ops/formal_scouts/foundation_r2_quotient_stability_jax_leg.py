#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for foundation R2 quotient stability.

The solver path leaves the density matrices unbound.  z3 and cvc5 assert only
Hermitian 2x2 density constraints plus fixed probe/pullback effects, then
derive every Tr(M rho) expression from matrix entries in solver arithmetic.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

import cvc5
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import z3


OBJECT_ID = "foundation_r2_quotient_stability_v2"
ENGINE = "jax"
RUNG_ID = "foundation_r2_quotient_stability_v2"
ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r2_quotient_stability_jax_results.json"
TOL = 1.0e-10

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 finite carrier report values outside the SMT claim path",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive complex128 candidate-state quotient and unitary-control reports",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing existential violation checks over free density-matrix entries and solver-expanded traces",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent free-density SMT check matching the z3 trace encoding",
    },
}
TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"}


Effect = dict[str, Any]

I2 = jnp.eye(2, dtype=jnp.complex128)
U_PHASE = jnp.asarray([[1.0, 0.0], [0.0, 1.0j]], dtype=jnp.complex128)
U_H = jnp.asarray([[1.0, 1.0], [1.0, -1.0]], dtype=jnp.complex128) / jnp.sqrt(
    jnp.asarray(2.0, dtype=jnp.float64)
)

ACTIVE_Z0: Effect = {
    "name": "Z0",
    "description": "computational-basis |0><0| projector",
    "real": [["1", "0"], ["0", "0"]],
    "imag": [["0", "0"], ["0", "0"]],
}
ADMITTED_PHASE_Z0_PULLBACK: Effect = {
    "name": "phase_Z_pi_over_2_dagger_Z0_phase_Z_pi_over_2",
    "description": "U_phase^dagger |0><0| U_phase = |0><0|",
    "real": [["1", "0"], ["0", "0"]],
    "imag": [["0", "0"], ["0", "0"]],
}
HADAMARD_Z0_PULLBACK: Effect = {
    "name": "Hadamard_dagger_Z0_Hadamard",
    "description": "H^dagger |0><0| H = |+><+|",
    "real": [["1/2", "1/2"], ["1/2", "1/2"]],
    "imag": [["0", "0"], ["0", "0"]],
}
Y_PLUS_PULLBACK: Effect = {
    "name": "Y_plus_projector_pullback_guard",
    "description": "imaginary-control pullback |y+><y+|, used only to prove rho01_im is retained",
    "real": [["1/2", "0"], ["0", "1/2"]],
    "imag": [["0", "-1/2"], ["1/2", "0"]],
}

ACTIVE_PROBES = [ACTIVE_Z0]
ADMITTED_PULLBACKS = [ADMITTED_PHASE_Z0_PULLBACK]
NONADMITTED_PULLBACKS = [HADAMARD_Z0_PULLBACK]
IMAGINARY_GUARD_PULLBACKS = [Y_PLUS_PULLBACK]


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def rational(value: str | int | float | Fraction) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, float):
        return Fraction(str(round(value, 12))).limit_denominator(10**12)
    return Fraction(value)


def rational_float(value: str | int | float | Fraction) -> float:
    return float(rational(value))


def effect_matrix(effect: Effect) -> jax.Array:
    real = jnp.asarray([[rational_float(cell) for cell in row] for row in effect["real"]], dtype=jnp.float64)
    imag = jnp.asarray([[rational_float(cell) for cell in row] for row in effect["imag"]], dtype=jnp.float64)
    return real.astype(jnp.complex128) + 1j * imag.astype(jnp.complex128)


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def rounded(value: Any, digits: int = 12) -> float:
    return round(py_float(value), digits)


def ket(values: list[complex]) -> jax.Array:
    vec = jnp.asarray(values, dtype=jnp.complex128)
    return vec / jnp.sqrt(jnp.vdot(vec, vec))


def density(vec: jax.Array) -> jax.Array:
    return jnp.outer(vec, jnp.conj(vec))


def candidates() -> list[dict[str, Any]]:
    s2 = jnp.sqrt(jnp.asarray(2.0, dtype=jnp.float64))
    states = {
        "pure_z0": ket([1.0 + 0.0j, 0.0 + 0.0j]),
        "pure_z1": ket([0.0 + 0.0j, 1.0 + 0.0j]),
        "pure_x_plus": ket([1.0 + 0.0j, 1.0 + 0.0j]),
        "pure_x_minus": ket([1.0 + 0.0j, -1.0 + 0.0j]),
        "pure_y_plus": jnp.asarray([1.0 + 0.0j, 0.0 + 1.0j], dtype=jnp.complex128) / s2,
        "pure_y_minus": jnp.asarray([1.0 + 0.0j, 0.0 - 1.0j], dtype=jnp.complex128) / s2,
    }
    rows = [{"id": name, "rho": density(vec)} for name, vec in states.items()]
    rows.append({"id": "maximally_mixed", "rho": 0.5 * I2})
    return rows


def active_probe_family() -> list[dict[str, Any]]:
    return [
        {
            "name": effect["name"],
            "effect": effect_matrix(effect),
            "description": effect["description"],
        }
        for effect in ACTIVE_PROBES
    ]


def expectation(rho: jax.Array, effect: jax.Array) -> float:
    return rounded(jnp.trace(effect @ rho), 12)


def expectation_table(rows: list[dict[str, Any]], probes: list[dict[str, Any]]) -> list[list[float]]:
    return [[expectation(row["rho"], probe["effect"]) for probe in probes] for row in rows]


def apply_unitary(rho: jax.Array, unitary: jax.Array) -> jax.Array:
    return unitary @ rho @ jnp.conj(unitary.T)


def image_rows(rows: list[dict[str, Any]], unitary: jax.Array) -> list[dict[str, Any]]:
    return [{"id": row["id"], "rho": apply_unitary(row["rho"], unitary)} for row in rows]


def signature_key(sig: list[float]) -> str:
    return json.dumps(sig, sort_keys=True, separators=(",", ":"))


def quotient(rows: list[dict[str, Any]], probes: list[dict[str, Any]], name: str) -> dict[str, Any]:
    table = expectation_table(rows, probes) if probes else [[] for _ in rows]
    classes: dict[str, dict[str, Any]] = {}
    for row, sig in zip(rows, table, strict=True):
        key = signature_key(sig)
        classes.setdefault(key, {"members": [], "signature": sig})
        classes[key]["members"].append(row["id"])
    ordered = [
        {"class_id": f"{name}_q{idx}", "members": sorted(classes[key]["members"]), "signature": classes[key]["signature"]}
        for idx, key in enumerate(sorted(classes))
    ]
    return {"name": name, "probe_names": [probe["name"] for probe in probes], "class_count": len(ordered), "classes": ordered}


def relation_from_table(table: list[list[float]]) -> list[list[bool]]:
    return [[table[i] == table[j] for j in range(len(table))] for i in range(len(table))]


def relation_report(rel: list[list[bool]]) -> dict[str, bool]:
    n = len(rel)
    reflexive = all(rel[i][i] for i in range(n))
    symmetric = all((not rel[i][j]) or rel[j][i] for i in range(n) for j in range(n))
    transitive = all((not rel[i][j]) or (not rel[j][k]) or rel[i][k] for i in range(n) for j in range(n) for k in range(n))
    return {"reflexive": reflexive, "symmetric": symmetric, "transitive": transitive, "is_equivalence_relation": reflexive and symmetric and transitive}


def stability_report(base_rel: list[list[bool]], image_rel: list[list[bool]], ids: list[str]) -> dict[str, Any]:
    violating = [
        {"left": ids[i], "right": ids[j]}
        for i in range(len(ids))
        for j in range(len(ids))
        if base_rel[i][j] and not image_rel[i][j]
    ]
    return {"stable": not violating, "violating_pairs": violating}


def constraints_report(rows: list[dict[str, Any]], probes: list[dict[str, Any]]) -> dict[str, Any]:
    details = []
    for row in rows:
        rho = row["rho"]
        eigs = jnp.linalg.eigvalsh((rho + jnp.conj(rho.T)) / 2.0)
        details.append(
            {
                "id": row["id"],
                "trace_residual": py_float(jnp.abs(jnp.trace(rho) - 1.0)),
                "hermitian_residual": py_float(jnp.linalg.norm(rho - jnp.conj(rho.T))),
                "min_eigenvalue": py_float(jnp.min(eigs)),
                "active_expectations": [expectation(rho, probe["effect"]) for probe in probes],
                "rho01_im": rounded(jnp.imag(rho[0, 1])),
                "psd": py_float(jnp.min(eigs)) >= -TOL,
            }
        )
    return {
        "trace_one": all(row["trace_residual"] <= TOL for row in details),
        "hermitian": all(row["hermitian_residual"] <= TOL for row in details),
        "psd": all(row["psd"] for row in details),
        "details": details,
    }


def unitary_residual(unitary: jax.Array) -> float:
    return py_float(jnp.linalg.norm(jnp.conj(unitary.T) @ unitary - I2))


def effect_is_nonzero(effect: Effect) -> bool:
    entries = [*effect["real"][0], *effect["real"][1], *effect["imag"][0], *effect["imag"][1]]
    return any(rational(entry) != 0 for entry in entries)


def z3_real(value: str | int | float | Fraction) -> z3.RatNumRef:
    f = rational(value)
    return z3.RealVal(f"{f.numerator}/{f.denominator}")


def z3_sum(terms: list[z3.ArithRef]) -> z3.ArithRef:
    return z3.RealVal(0) if not terms else sum(terms, z3.RealVal(0))


def z3_and(terms: list[z3.BoolRef]) -> z3.BoolRef:
    return z3.BoolVal(True) if not terms else z3.And(*terms)


def z3_or(terms: list[z3.BoolRef]) -> z3.BoolRef:
    return z3.BoolVal(False) if not terms else z3.Or(*terms)


def z3_density_vars(prefix: str) -> tuple[dict[str, z3.ArithRef], list[z3.BoolRef]]:
    a = z3.Real(f"{prefix}_rho00_re")
    b = z3.Real(f"{prefix}_rho11_re")
    c = z3.Real(f"{prefix}_rho01_re")
    d = z3.Real(f"{prefix}_rho01_im")
    det = a * b - c * c - d * d
    constraints = [
        a >= 0,
        b >= 0,
        a + b == 1,
        det >= 0,
    ]
    return {"rho00_re": a, "rho11_re": b, "rho01_re": c, "rho01_im": d, "det": det}, constraints


def z3_state_matrix(state: dict[str, z3.ArithRef]) -> tuple[list[list[z3.ArithRef]], list[list[z3.ArithRef]]]:
    a = state["rho00_re"]
    b = state["rho11_re"]
    c = state["rho01_re"]
    d = state["rho01_im"]
    zero = z3.RealVal(0)
    return [[a, c], [c, b]], [[zero, d], [-d, zero]]


def z3_trace_effect(state: dict[str, z3.ArithRef], effect: Effect) -> z3.ArithRef:
    rho_r, rho_i = z3_state_matrix(state)
    terms: list[z3.ArithRef] = []
    for p in range(2):
        for q in range(2):
            er = z3_real(effect["real"][p][q])
            ei = z3_real(effect["imag"][p][q])
            rr = rho_r[q][p]
            ri = rho_i[q][p]
            terms.append(er * rr - ei * ri)
    return z3_sum(terms)


def z3_expectations(states: list[dict[str, z3.ArithRef]], effects: list[Effect]) -> list[list[z3.ArithRef]]:
    return [[z3_trace_effect(state, effect) for effect in effects] for state in states]


def z3_rel(expectations: list[list[z3.ArithRef]], i: int, j: int) -> z3.BoolRef:
    return z3_and([expectations[i][m] == expectations[j][m] for m in range(len(expectations[i]))])


def z3_model_value(model: z3.ModelRef, expr: z3.ExprRef) -> str:
    return str(model.evaluate(expr, model_completion=True))


def z3_witness_state(model: z3.ModelRef, state: dict[str, z3.ArithRef]) -> dict[str, str]:
    return {
        "rho00_re": z3_model_value(model, state["rho00_re"]),
        "rho11_re": z3_model_value(model, state["rho11_re"]),
        "rho01_re": z3_model_value(model, state["rho01_re"]),
        "rho01_im": z3_model_value(model, state["rho01_im"]),
        "det": z3_model_value(model, state["det"]),
    }


def z3_transitivity_query(effects: list[Effect], prefix: str) -> dict[str, Any]:
    solver = z3.Solver()
    states = []
    constraints: list[z3.BoolRef] = []
    for idx in range(3):
        state, state_constraints = z3_density_vars(f"{prefix}_s{idx}")
        states.append(state)
        constraints.extend(state_constraints)
    expectations = z3_expectations(states, effects)
    solver.add(*constraints)
    solver.add(z3_rel(expectations, 0, 1))
    solver.add(z3_rel(expectations, 1, 2))
    solver.add(z3.Not(z3_rel(expectations, 0, 2)))
    return {
        "verdict": str(solver.check()),
        "state_literal_bindings": 0,
        "state_constraint_terms": len(constraints),
        "derived_trace_terms": len(states) * len(effects),
        "probe_count": len(effects),
    }


def z3_stability_query(base_effects: list[Effect], post_effects: list[Effect], prefix: str) -> dict[str, Any]:
    solver = z3.Solver()
    states = []
    constraints: list[z3.BoolRef] = []
    for idx in range(2):
        state, state_constraints = z3_density_vars(f"{prefix}_s{idx}")
        states.append(state)
        constraints.extend(state_constraints)
    base_expectations = z3_expectations(states, base_effects)
    post_expectations = z3_expectations(states, post_effects)
    solver.add(*constraints)
    solver.add(z3_rel(base_expectations, 0, 1))
    solver.add(z3.Not(z3_rel(post_expectations, 0, 1)))
    verdict = str(solver.check())
    witness = None
    if verdict == "sat":
        model = solver.model()
        witness = {
            "rho_1": z3_witness_state(model, states[0]),
            "rho_2": z3_witness_state(model, states[1]),
            "base_trace_values": [
                [z3_model_value(model, expr) for expr in base_expectations[0]],
                [z3_model_value(model, expr) for expr in base_expectations[1]],
            ],
            "post_trace_values": [
                [z3_model_value(model, expr) for expr in post_expectations[0]],
                [z3_model_value(model, expr) for expr in post_expectations[1]],
            ],
        }
    return {
        "verdict": verdict,
        "witness": witness,
        "state_literal_bindings": 0,
        "state_constraint_terms": len(constraints),
        "derived_trace_terms": len(states) * (len(base_effects) + len(post_effects)),
        "probe_count": len(base_effects),
    }


def z3_nonvacuity_query(effects: list[Effect], prefix: str) -> dict[str, Any]:
    solver = z3.Solver()
    states = []
    constraints: list[z3.BoolRef] = []
    for idx in range(2):
        state, state_constraints = z3_density_vars(f"{prefix}_s{idx}")
        states.append(state)
        constraints.extend(state_constraints)
    expectations = z3_expectations(states, effects)
    solver.add(*constraints)
    solver.add(z3.Not(z3_rel(expectations, 0, 1)))
    verdict = str(solver.check())
    witness = None
    if verdict == "sat":
        model = solver.model()
        witness = {
            "rho_1": z3_witness_state(model, states[0]),
            "rho_2": z3_witness_state(model, states[1]),
            "trace_values": [
                [z3_model_value(model, expr) for expr in expectations[0]],
                [z3_model_value(model, expr) for expr in expectations[1]],
            ],
        }
    return {"verdict": verdict, "witness": witness, "state_literal_bindings": 0, "derived_trace_terms": len(states) * len(effects)}


def z3_boundary_psd_guard(prefix: str) -> dict[str, Any]:
    solver = z3.Solver()
    state, constraints = z3_density_vars(f"{prefix}_boundary")
    solver.add(*constraints)
    solver.add(state["rho00_re"] == z3_real("1/2"))
    solver.add(state["rho11_re"] == z3_real("1/2"))
    solver.add(state["rho01_re"] == z3_real("0"))
    solver.add(state["rho01_im"] == z3_real("1/2"))
    verdict = str(solver.check())
    witness = None
    if verdict == "sat":
        witness = z3_witness_state(solver.model(), state)
    return {"verdict": verdict, "witness": witness, "expected_det": "0", "state_literal_bindings": 4}


def cvc5_real(solver: cvc5.Solver, value: str | int | float | Fraction) -> Any:
    f = rational(value)
    return solver.mkReal(f.numerator, f.denominator)


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkReal(0)
    return terms[0] if len(terms) == 1 else solver.mkTerm(cvc5.Kind.ADD, *terms)


def cvc5_sub(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(cvc5.Kind.SUB, left, right)


def cvc5_mul(solver: cvc5.Solver, *terms: Any) -> Any:
    return terms[0] if len(terms) == 1 else solver.mkTerm(cvc5.Kind.MULT, *terms)


def cvc5_and(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(True)
    return terms[0] if len(terms) == 1 else solver.mkTerm(cvc5.Kind.AND, *terms)


def cvc5_eq(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(cvc5.Kind.EQUAL, left, right)


def cvc5_not(solver: cvc5.Solver, term: Any) -> Any:
    return solver.mkTerm(cvc5.Kind.NOT, term)


def cvc5_geq(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(cvc5.Kind.GEQ, left, right)


def cvc5_new_solver() -> cvc5.Solver:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    solver.setOption("produce-models", "true")
    return solver


def cvc5_density_vars(solver: cvc5.Solver, prefix: str) -> tuple[dict[str, Any], list[Any]]:
    real_sort = solver.getRealSort()
    a = solver.mkConst(real_sort, f"{prefix}_rho00_re")
    b = solver.mkConst(real_sort, f"{prefix}_rho11_re")
    c = solver.mkConst(real_sort, f"{prefix}_rho01_re")
    d = solver.mkConst(real_sort, f"{prefix}_rho01_im")
    det = cvc5_sub(solver, cvc5_sub(solver, cvc5_mul(solver, a, b), cvc5_mul(solver, c, c)), cvc5_mul(solver, d, d))
    constraints = [
        cvc5_geq(solver, a, solver.mkReal(0)),
        cvc5_geq(solver, b, solver.mkReal(0)),
        cvc5_eq(solver, solver.mkTerm(cvc5.Kind.ADD, a, b), solver.mkReal(1)),
        cvc5_geq(solver, det, solver.mkReal(0)),
    ]
    return {"rho00_re": a, "rho11_re": b, "rho01_re": c, "rho01_im": d, "det": det}, constraints


def cvc5_state_matrix(solver: cvc5.Solver, state: dict[str, Any]) -> tuple[list[list[Any]], list[list[Any]]]:
    a = state["rho00_re"]
    b = state["rho11_re"]
    c = state["rho01_re"]
    d = state["rho01_im"]
    zero = solver.mkReal(0)
    return [[a, c], [c, b]], [[zero, d], [cvc5_sub(solver, zero, d), zero]]


def cvc5_trace_effect(solver: cvc5.Solver, state: dict[str, Any], effect: Effect) -> Any:
    rho_r, rho_i = cvc5_state_matrix(solver, state)
    terms: list[Any] = []
    for p in range(2):
        for q in range(2):
            er = cvc5_real(solver, effect["real"][p][q])
            ei = cvc5_real(solver, effect["imag"][p][q])
            rr = rho_r[q][p]
            ri = rho_i[q][p]
            terms.append(cvc5_sub(solver, cvc5_mul(solver, er, rr), cvc5_mul(solver, ei, ri)))
    return cvc5_sum(solver, terms)


def cvc5_expectations(solver: cvc5.Solver, states: list[dict[str, Any]], effects: list[Effect]) -> list[list[Any]]:
    return [[cvc5_trace_effect(solver, state, effect) for effect in effects] for state in states]


def cvc5_rel(solver: cvc5.Solver, expectations: list[list[Any]], i: int, j: int) -> Any:
    return cvc5_and(solver, [cvc5_eq(solver, expectations[i][m], expectations[j][m]) for m in range(len(expectations[i]))])


def cvc5_model_value(solver: cvc5.Solver, expr: Any) -> str:
    return str(solver.getValue(expr))


def cvc5_witness_state(solver: cvc5.Solver, state: dict[str, Any]) -> dict[str, str]:
    return {
        "rho00_re": cvc5_model_value(solver, state["rho00_re"]),
        "rho11_re": cvc5_model_value(solver, state["rho11_re"]),
        "rho01_re": cvc5_model_value(solver, state["rho01_re"]),
        "rho01_im": cvc5_model_value(solver, state["rho01_im"]),
        "det": cvc5_model_value(solver, state["det"]),
    }


def cvc5_transitivity_query(effects: list[Effect], prefix: str) -> dict[str, Any]:
    solver = cvc5_new_solver()
    states = []
    constraints: list[Any] = []
    for idx in range(3):
        state, state_constraints = cvc5_density_vars(solver, f"{prefix}_s{idx}")
        states.append(state)
        constraints.extend(state_constraints)
    expectations = cvc5_expectations(solver, states, effects)
    for constraint in constraints:
        solver.assertFormula(constraint)
    solver.assertFormula(cvc5_rel(solver, expectations, 0, 1))
    solver.assertFormula(cvc5_rel(solver, expectations, 1, 2))
    solver.assertFormula(cvc5_not(solver, cvc5_rel(solver, expectations, 0, 2)))
    return {
        "verdict": str(solver.checkSat()),
        "state_literal_bindings": 0,
        "state_constraint_terms": len(constraints),
        "derived_trace_terms": len(states) * len(effects),
        "probe_count": len(effects),
    }


def cvc5_stability_query(base_effects: list[Effect], post_effects: list[Effect], prefix: str) -> dict[str, Any]:
    solver = cvc5_new_solver()
    states = []
    constraints: list[Any] = []
    for idx in range(2):
        state, state_constraints = cvc5_density_vars(solver, f"{prefix}_s{idx}")
        states.append(state)
        constraints.extend(state_constraints)
    base_expectations = cvc5_expectations(solver, states, base_effects)
    post_expectations = cvc5_expectations(solver, states, post_effects)
    for constraint in constraints:
        solver.assertFormula(constraint)
    solver.assertFormula(cvc5_rel(solver, base_expectations, 0, 1))
    solver.assertFormula(cvc5_not(solver, cvc5_rel(solver, post_expectations, 0, 1)))
    verdict = str(solver.checkSat())
    witness = None
    if verdict == "sat":
        witness = {
            "rho_1": cvc5_witness_state(solver, states[0]),
            "rho_2": cvc5_witness_state(solver, states[1]),
            "base_trace_values": [
                [cvc5_model_value(solver, expr) for expr in base_expectations[0]],
                [cvc5_model_value(solver, expr) for expr in base_expectations[1]],
            ],
            "post_trace_values": [
                [cvc5_model_value(solver, expr) for expr in post_expectations[0]],
                [cvc5_model_value(solver, expr) for expr in post_expectations[1]],
            ],
        }
    return {
        "verdict": verdict,
        "witness": witness,
        "state_literal_bindings": 0,
        "state_constraint_terms": len(constraints),
        "derived_trace_terms": len(states) * (len(base_effects) + len(post_effects)),
        "probe_count": len(base_effects),
    }


def cvc5_nonvacuity_query(effects: list[Effect], prefix: str) -> dict[str, Any]:
    solver = cvc5_new_solver()
    states = []
    constraints: list[Any] = []
    for idx in range(2):
        state, state_constraints = cvc5_density_vars(solver, f"{prefix}_s{idx}")
        states.append(state)
        constraints.extend(state_constraints)
    expectations = cvc5_expectations(solver, states, effects)
    for constraint in constraints:
        solver.assertFormula(constraint)
    solver.assertFormula(cvc5_not(solver, cvc5_rel(solver, expectations, 0, 1)))
    verdict = str(solver.checkSat())
    witness = None
    if verdict == "sat":
        witness = {
            "rho_1": cvc5_witness_state(solver, states[0]),
            "rho_2": cvc5_witness_state(solver, states[1]),
            "trace_values": [
                [cvc5_model_value(solver, expr) for expr in expectations[0]],
                [cvc5_model_value(solver, expr) for expr in expectations[1]],
            ],
        }
    return {"verdict": verdict, "witness": witness, "state_literal_bindings": 0, "derived_trace_terms": len(states) * len(effects)}


def cvc5_boundary_psd_guard(prefix: str) -> dict[str, Any]:
    solver = cvc5_new_solver()
    state, constraints = cvc5_density_vars(solver, f"{prefix}_boundary")
    for constraint in constraints:
        solver.assertFormula(constraint)
    solver.assertFormula(cvc5_eq(solver, state["rho00_re"], cvc5_real(solver, "1/2")))
    solver.assertFormula(cvc5_eq(solver, state["rho11_re"], cvc5_real(solver, "1/2")))
    solver.assertFormula(cvc5_eq(solver, state["rho01_re"], cvc5_real(solver, "0")))
    solver.assertFormula(cvc5_eq(solver, state["rho01_im"], cvc5_real(solver, "1/2")))
    verdict = str(solver.checkSat())
    witness = None
    if verdict == "sat":
        witness = cvc5_witness_state(solver, state)
    return {"verdict": verdict, "witness": witness, "expected_det": "0", "state_literal_bindings": 4}


def run_smt() -> dict[str, Any]:
    z3_trans = z3_transitivity_query(ACTIVE_PROBES, "z3_trans")
    z3_admitted = z3_stability_query(ACTIVE_PROBES, ADMITTED_PULLBACKS, "z3_admitted")
    z3_nonadmitted = z3_stability_query(ACTIVE_PROBES, NONADMITTED_PULLBACKS, "z3_nonadmitted")
    z3_nonvacuity = z3_nonvacuity_query(ACTIVE_PROBES, "z3_nonvacuity")
    z3_boundary = z3_boundary_psd_guard("z3")
    z3_imaginary = z3_stability_query(ACTIVE_PROBES, IMAGINARY_GUARD_PULLBACKS, "z3_imaginary")

    cvc5_trans = cvc5_transitivity_query(ACTIVE_PROBES, "cvc5_trans")
    cvc5_admitted = cvc5_stability_query(ACTIVE_PROBES, ADMITTED_PULLBACKS, "cvc5_admitted")
    cvc5_nonadmitted = cvc5_stability_query(ACTIVE_PROBES, NONADMITTED_PULLBACKS, "cvc5_nonadmitted")
    cvc5_nonvacuity = cvc5_nonvacuity_query(ACTIVE_PROBES, "cvc5_nonvacuity")
    cvc5_boundary = cvc5_boundary_psd_guard("cvc5")
    cvc5_imaginary = cvc5_stability_query(ACTIVE_PROBES, IMAGINARY_GUARD_PULLBACKS, "cvc5_imaginary")

    return {
        "z3": {
            "transitivity_violation_verdict": z3_trans["verdict"],
            "admitted_separating_witness_verdict": z3_admitted["verdict"],
            "nonadmitted_separating_witness_verdict": z3_nonadmitted["verdict"],
            "nonadmitted_separating_witness": z3_nonadmitted["witness"],
            "nonvacuous_probe_verdict": z3_nonvacuity["verdict"],
            "nonvacuous_probe_witness": z3_nonvacuity["witness"],
            "boundary_psd_feasible_verdict": z3_boundary["verdict"],
            "boundary_psd_witness": z3_boundary["witness"],
            "imaginary_retention_guard_verdict": z3_imaginary["verdict"],
            "imaginary_retention_guard_witness": z3_imaginary["witness"],
            "main_no_violation_verdict": z3_admitted["verdict"],
            "nonadmitted_stability_violation_verdict": z3_nonadmitted["verdict"],
            "main_asserted_real_equalities": 0,
            "main_state_constraint_terms": z3_admitted["state_constraint_terms"],
            "main_derived_trace_terms": z3_admitted["derived_trace_terms"],
            "state_literal_bindings": 0,
            "version": z3.get_version_string(),
        },
        "cvc5": {
            "transitivity_violation_verdict": cvc5_trans["verdict"],
            "admitted_separating_witness_verdict": cvc5_admitted["verdict"],
            "nonadmitted_separating_witness_verdict": cvc5_nonadmitted["verdict"],
            "nonadmitted_separating_witness": cvc5_nonadmitted["witness"],
            "nonvacuous_probe_verdict": cvc5_nonvacuity["verdict"],
            "nonvacuous_probe_witness": cvc5_nonvacuity["witness"],
            "boundary_psd_feasible_verdict": cvc5_boundary["verdict"],
            "boundary_psd_witness": cvc5_boundary["witness"],
            "imaginary_retention_guard_verdict": cvc5_imaginary["verdict"],
            "imaginary_retention_guard_witness": cvc5_imaginary["witness"],
            "main_no_violation_verdict": cvc5_admitted["verdict"],
            "nonadmitted_stability_violation_verdict": cvc5_nonadmitted["verdict"],
            "main_asserted_real_equalities": 0,
            "main_state_constraint_terms": cvc5_admitted["state_constraint_terms"],
            "main_derived_trace_terms": cvc5_admitted["derived_trace_terms"],
            "state_literal_bindings": 0,
            "version": getattr(cvc5, "__version__", "unknown"),
        },
        "encoding": {
            "state_variables": "Each SMT density matrix is free: rho00_re, rho11_re, rho01_re, rho01_im.",
            "state_constraints": "trace rho=1, rho00>=0, rho11>=0, rho00*rho11-rho01_re^2-rho01_im^2>=0.",
            "bound_structure_only": ["Z0 probe", "phase pullback Z0", "Hadamard pullback Z0", "Y-plus imaginary guard pullback"],
            "derived_quantity": "Tr(E rho) is expanded in solver as sum_{p,q}(E_re[p,q]*rho_re[q,p] - E_im[p,q]*rho_im[q,p]).",
            "relation_definition": "rho_i ~_M rho_j iff every solver-derived Tr(M_k rho_i) equals Tr(M_k rho_j).",
            "forbidden_pattern_avoided": "No candidate-state component, expectation scalar, relation boolean, class label, implication rule, or residual is bound as the solver claim.",
        },
    }


def main() -> int:
    rows = candidates()
    probes = active_probe_family()
    ids = [row["id"] for row in rows]
    base_table = expectation_table(rows, probes)
    admitted_table = expectation_table(image_rows(rows, U_PHASE), probes)
    nonadmitted_table = expectation_table(image_rows(rows, U_H), probes)
    base_rel = relation_from_table(base_table)
    admitted_rel = relation_from_table(admitted_table)
    nonadmitted_rel = relation_from_table(nonadmitted_table)

    q = quotient(rows, probes, "active_M_Z0")
    dropped_q = quotient(rows, [], "dropped_M_empty")
    constraints = constraints_report(rows, probes)
    equivalence = relation_report(base_rel)
    admitted_stability = stability_report(base_rel, admitted_rel, ids)
    nonadmitted_stability = stability_report(base_rel, nonadmitted_rel, ids)
    smt = run_smt()
    z3_main = smt["z3"]["main_no_violation_verdict"]
    cvc5_main = smt["cvc5"]["main_no_violation_verdict"]
    z3_bad = smt["z3"]["nonadmitted_stability_violation_verdict"]
    cvc5_bad = smt["cvc5"]["nonadmitted_stability_violation_verdict"]
    proof_encoding_note = (
        "z3/cvc5 leave rho_1,rho_2,rho_3 unbound as Hermitian trace-one PSD variables. "
        "They derive the quotient relation from solver-expanded Tr(M rho) arithmetic and query "
        "existence of a transitivity or stability separator. UNSAT is therefore the absence of a "
        "free density-matrix witness, not an asserted stability rule contradicted by its negation."
    )
    all_pass = bool(
        constraints["trace_one"]
        and constraints["hermitian"]
        and constraints["psd"]
        and equivalence["is_equivalence_relation"]
        and admitted_stability["stable"]
        and not nonadmitted_stability["stable"]
        and q["class_count"] == 3
        and dropped_q["class_count"] == 1
        and all(effect_is_nonzero(effect) for effect in ACTIVE_PROBES)
        and smt["z3"]["state_literal_bindings"] == smt["cvc5"]["state_literal_bindings"] == 0
        and smt["z3"]["transitivity_violation_verdict"] == smt["cvc5"]["transitivity_violation_verdict"] == "unsat"
        and z3_main == cvc5_main == "unsat"
        and z3_bad == cvc5_bad == "sat"
        and smt["z3"]["nonvacuous_probe_verdict"] == smt["cvc5"]["nonvacuous_probe_verdict"] == "sat"
        and smt["z3"]["boundary_psd_feasible_verdict"] == smt["cvc5"]["boundary_psd_feasible_verdict"] == "sat"
        and smt["z3"]["imaginary_retention_guard_verdict"] == smt["cvc5"]["imaginary_retention_guard_verdict"] == "sat"
    )
    result = {
        "schema_version": "engine_leg_result_v1",
        "object_id": OBJECT_ID,
        "engine": ENGINE,
        "rung_id": RUNG_ID,
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_sha256(),
        "result_path": str(RESULT_PATH),
        "python_executable": sys.executable,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "pathlib", "hashlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "M": {
            "active_probe_family": ["Z0"],
            "probes": [
                {
                    "name": ACTIVE_Z0["name"],
                    "effect": "|0><0|",
                    "exact_real": ACTIVE_Z0["real"],
                    "exact_imag": ACTIVE_Z0["imag"],
                    "nonzero_effect": effect_is_nonzero(ACTIVE_Z0),
                }
            ],
            "dropped_probe_family": [],
        },
        "C": {
            "state_constraints": [
                "Hermitian 2x2 represented by rho00_re,rho11_re,rho01_re,rho01_im",
                "trace=1",
                "PSD via principal minors rho00>=0, rho11>=0, determinant>=0",
            ],
            "admitted_operation": "phase_Z_pi_over_2",
            "nonadmitted_control_operation": "Hadamard",
            "rung_specific_constraint": "active-M equivalence must be stable under admitted operations",
            "solver_state_binding": "unbound density matrices; no candidate states are bound in z3/cvc5",
            "constraints_hold": constraints,
            "operation_constraints_hold": {
                "admitted_unitary_residual": unitary_residual(U_PHASE),
                "nonadmitted_control_unitary_residual": unitary_residual(U_H),
                "admitted_operation_stable": admitted_stability["stable"],
                "nonadmitted_operation_stable": nonadmitted_stability["stable"],
            },
        },
        "S": {"ids": ids, "size": len(ids), "density_matrix_shape": [2, 2]},
        "expectations": {
            "numeric_report_only_active_M": base_table,
            "numeric_report_only_post_admitted_operation": admitted_table,
            "numeric_report_only_post_nonadmitted_operation": nonadmitted_table,
            "row_ids": ids,
            "probe_order": ["Z0"],
            "claim_path_note": "SMT claim path uses free density variables and recomputes traces in solver; this finite table is report-only.",
        },
        "quotient": q,
        "S_quotient": {"classes": q["classes"], "class_count": q["class_count"]},
        "equivalence": equivalence,
        "stability": {"admitted_operation": admitted_stability, "nonadmitted_operation": nonadmitted_stability},
        "smt": smt,
        "negative_control_flip": {
            "active_M_class_count": q["class_count"],
            "drop_M_class_count": dropped_q["class_count"],
            "drop_M_changed_quotient": q["class_count"] > dropped_q["class_count"],
            "base_transitivity_violation_z3": smt["z3"]["transitivity_violation_verdict"],
            "base_transitivity_violation_cvc5": smt["cvc5"]["transitivity_violation_verdict"],
            "admitted_operation_stable": admitted_stability["stable"],
            "nonadmitted_operation_stable": nonadmitted_stability["stable"],
            "z3_main_verdict": z3_main,
            "cvc5_main_verdict": cvc5_main,
            "z3_nonadmitted_violation_verdict": z3_bad,
            "cvc5_nonadmitted_violation_verdict": cvc5_bad,
            "z3_nonadmitted_witness": smt["z3"]["nonadmitted_separating_witness"],
            "cvc5_nonadmitted_witness": smt["cvc5"]["nonadmitted_separating_witness"],
            "sat_unsat_sat_flip": (
                f"transitivity violator z3/cvc5={smt['z3']['transitivity_violation_verdict']}/"
                f"{smt['cvc5']['transitivity_violation_verdict']}; "
                f"admitted separator z3/cvc5={z3_main}/{cvc5_main}; "
                f"nonadmitted separator z3/cvc5={z3_bad}/{cvc5_bad}"
            ),
        },
        "falsifier_guards": {
            "probe_nonvacuous": {
                "z3": smt["z3"]["nonvacuous_probe_verdict"],
                "cvc5": smt["cvc5"]["nonvacuous_probe_verdict"],
                "z3_witness": smt["z3"]["nonvacuous_probe_witness"],
                "cvc5_witness": smt["cvc5"]["nonvacuous_probe_witness"],
            },
            "boundary_psd_det_zero_feasible": {
                "z3": smt["z3"]["boundary_psd_feasible_verdict"],
                "cvc5": smt["cvc5"]["boundary_psd_feasible_verdict"],
                "z3_witness": smt["z3"]["boundary_psd_witness"],
                "cvc5_witness": smt["cvc5"]["boundary_psd_witness"],
            },
            "imaginary_part_retained": {
                "z3": smt["z3"]["imaginary_retention_guard_verdict"],
                "cvc5": smt["cvc5"]["imaginary_retention_guard_verdict"],
                "z3_witness": smt["z3"]["imaginary_retention_guard_witness"],
                "cvc5_witness": smt["cvc5"]["imaginary_retention_guard_witness"],
                "note": "The Y-plus pullback SAT guard separates same-Z0-class states through rho01_im; truncating to real would remove this witness.",
            },
            "exact_rational_solver_constants": True,
        },
        "proof_encoding_note": proof_encoding_note,
        "values": {
            "class_count": q["class_count"],
            "drop_M_class_count": dropped_q["class_count"],
            "admitted_stable": admitted_stability["stable"],
            "nonadmitted_stable": nonadmitted_stability["stable"],
            "base_transitivity_violation_z3": smt["z3"]["transitivity_violation_verdict"],
            "base_transitivity_violation_cvc5": smt["cvc5"]["transitivity_violation_verdict"],
            "z3_main_verdict": z3_main,
            "cvc5_main_verdict": cvc5_main,
            "z3_nonadmitted_violation_verdict": z3_bad,
            "cvc5_nonadmitted_violation_verdict": cvc5_bad,
            "state_literal_bindings": 0,
            "imaginary_retention_guard_z3": smt["z3"]["imaginary_retention_guard_verdict"],
            "imaginary_retention_guard_cvc5": smt["cvc5"]["imaginary_retention_guard_verdict"],
        },
        "all_pass": all_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FOUNDATION_R2_JAX_V2_DONE "
        f"all_pass={str(all_pass).lower()} class_count={q['class_count']} drop_M_class_count={dropped_q['class_count']} "
        f"trans={smt['z3']['transitivity_violation_verdict']}/{smt['cvc5']['transitivity_violation_verdict']} "
        f"admitted={z3_main}/{cvc5_main} nonadmitted={z3_bad}/{cvc5_bad} "
        f"imag_guard={smt['z3']['imaginary_retention_guard_verdict']}/{smt['cvc5']['imaginary_retention_guard_verdict']} "
        f"result={RESULT_PATH}"
    )
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
