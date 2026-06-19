#!/usr/bin/env python3
"""JAX + z3/cvc5 structural leg for foundation_r0_distinguishability.

The SMT path binds only the finite density-matrix and POVM-effect entries.
Every Born value is derived in-solver as Tr(M rho) = sum_ij M_ij * rho_ji.
No precomputed probability scalar or Boolean is bound into either solver.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import cvc5
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import z3


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r0_distinguishability_jax_smt_results.json"
TOL = 1.0e-12

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed

FAMILIES = {"M1_Z": ["Z"], "M2_ZX": ["Z", "X"]}
PROBES = {
    "Z": ["Z_plus", "Z_minus"],
    "X": ["X_plus", "X_minus"],
}


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def ket(values: list[complex]) -> jax.Array:
    vector = jnp.asarray(values, dtype=jnp.complex128).reshape((2, 1))
    return vector / jnp.sqrt(jnp.real(jnp.vdot(vector, vector)))


def dm(vector: jax.Array) -> jax.Array:
    return vector @ jnp.conjugate(vector.T)


def states() -> dict[str, jax.Array]:
    z0 = ket([1.0 + 0.0j, 0.0 + 0.0j])
    z1 = ket([0.0 + 0.0j, 1.0 + 0.0j])
    xp = ket([1.0 + 0.0j, 1.0 + 0.0j])
    xm = ket([1.0 + 0.0j, -1.0 + 0.0j])
    return {
        "pure_z0": dm(z0),
        "pure_z1": dm(z1),
        "rho_a_x_plus": dm(xp),
        "rho_b_x_minus": dm(xm),
        "maximally_mixed": 0.5 * dm(z0) + 0.5 * dm(z1),
    }


def probe_effects() -> dict[str, list[jax.Array]]:
    z0 = ket([1.0 + 0.0j, 0.0 + 0.0j])
    z1 = ket([0.0 + 0.0j, 1.0 + 0.0j])
    xp = ket([1.0 + 0.0j, 1.0 + 0.0j])
    xm = ket([1.0 + 0.0j, -1.0 + 0.0j])
    return {"Z": [dm(z0), dm(z1)], "X": [dm(xp), dm(xm)]}


def born(effect: jax.Array, rho: jax.Array) -> float:
    return round(float(jax.device_get(jnp.real(jnp.trace(effect @ rho)))), 12)


def family_stats(rho: jax.Array, family: list[str], effects: dict[str, list[jax.Array]]) -> list[list[float]]:
    return [[born(effect, rho) for effect in effects[probe]] for probe in family]


def quotient(state_map: dict[str, jax.Array], family_name: str, effects: dict[str, list[jax.Array]]) -> dict[str, Any]:
    classes: dict[str, dict[str, Any]] = {}
    family = FAMILIES[family_name]
    for state_id in sorted(state_map):
        sig = family_stats(state_map[state_id], family, effects)
        key = json.dumps(sig, sort_keys=True, separators=(",", ":"))
        classes.setdefault(key, {"members": [], "signature": sig})["members"].append(state_id)
    rows = []
    for idx, key in enumerate(sorted(classes)):
        rows.append(
            {
                "class_id": f"{family_name}_class_{idx}",
                "members": sorted(classes[key]["members"]),
                "signature": classes[key]["signature"],
            }
        )
    return {"name": family_name, "probe_names": family, "class_count": len(rows), "classes": rows}


def real_matrix(matrix: jax.Array) -> list[list[float]]:
    imag_gap = float(jax.device_get(jnp.max(jnp.abs(jnp.imag(matrix)))))
    if imag_gap > TOL:
        raise ValueError(f"expected real matrix for this finite R0 witness; imag_gap={imag_gap}")
    real = jax.device_get(jnp.real(matrix))
    return [[round(float(real[i, j]), 12) for j in range(real.shape[1])] for i in range(real.shape[0])]


def frac(value: float) -> Fraction:
    return Fraction(str(round(float(value), 12))).limit_denominator(10**12)


def z3_real_value(value: float) -> z3.RatNumRef:
    f = frac(value)
    return z3.RealVal(f"{f.numerator}/{f.denominator}")


def z3_sum(terms: list[z3.ArithRef]) -> z3.ArithRef:
    if not terms:
        return z3_real_value(0.0)
    return terms[0] if len(terms) == 1 else sum(terms[1:], terms[0])


def z3_bind_matrix(
    solver: z3.Solver,
    prefix: str,
    entries: list[list[float]],
    bindings: list[dict[str, Any]],
) -> list[list[z3.ArithRef]]:
    matrix = []
    for i, row in enumerate(entries):
        out_row = []
        for j, value in enumerate(row):
            var = z3.Real(f"{prefix}_{i}_{j}")
            solver.add(var == z3_real_value(value))
            bindings.append({"kind": "matrix_entry", "matrix": prefix, "i": i, "j": j, "var": str(var), "value": value})
            out_row.append(var)
        matrix.append(out_row)
    return matrix


def z3_density_constraints(matrix: list[list[z3.ArithRef]]) -> list[z3.BoolRef]:
    det = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    return [
        matrix[0][0] + matrix[1][1] == z3_real_value(1.0),
        matrix[0][1] == matrix[1][0],
        matrix[0][0] >= z3_real_value(0.0),
        matrix[1][1] >= z3_real_value(0.0),
        det >= z3_real_value(0.0),
    ]


def z3_effect_constraints(effect: list[list[z3.ArithRef]]) -> list[z3.BoolRef]:
    det = effect[0][0] * effect[1][1] - effect[0][1] * effect[1][0]
    return [
        effect[0][1] == effect[1][0],
        effect[0][0] >= z3_real_value(0.0),
        effect[1][1] >= z3_real_value(0.0),
        det >= z3_real_value(0.0),
    ]


def z3_trace_term(effect: list[list[z3.ArithRef]], rho: list[list[z3.ArithRef]]) -> z3.ArithRef:
    return z3_sum([effect[i][j] * rho[j][i] for i in range(2) for j in range(2)])


def z3_to_float(value: z3.ExprRef) -> float:
    if hasattr(value, "as_fraction"):
        return float(value.as_fraction())
    return float(str(value).replace("?", ""))


def z3_build_problem(
    rho_a: jax.Array,
    rho_b: jax.Array,
    family: list[str],
    effects: dict[str, list[jax.Array]],
) -> tuple[z3.Solver, dict[str, dict[str, list[z3.ArithRef]]], dict[str, Any]]:
    solver = z3.Solver()
    bindings: list[dict[str, Any]] = []
    assertions: list[dict[str, str]] = []

    rho_vars = {
        "rho_a": z3_bind_matrix(solver, "rho_a", real_matrix(rho_a), bindings),
        "rho_b": z3_bind_matrix(solver, "rho_b", real_matrix(rho_b), bindings),
    }
    for state_name, matrix in rho_vars.items():
        for idx, assertion in enumerate(z3_density_constraints(matrix)):
            solver.add(assertion)
            assertions.append({"kind": "density_C", "target": state_name, "index": str(idx), "expr": str(assertion)})

    distinct_terms = [
        rho_vars["rho_a"][i][j] != rho_vars["rho_b"][i][j]
        for i in range(2)
        for j in range(2)
    ]
    distinct_assertion = z3.Or(*distinct_terms)
    solver.add(distinct_assertion)
    assertions.append({"kind": "rung_specific_C", "target": "rho_a_vs_rho_b", "expr": str(distinct_assertion)})

    effect_vars: dict[str, list[list[list[z3.ArithRef]]]] = {}
    for probe in family:
        effect_vars[probe] = []
        for outcome, effect in enumerate(effects[probe]):
            prefix = f"M_{probe}_{outcome}"
            effect_matrix = z3_bind_matrix(solver, prefix, real_matrix(effect), bindings)
            effect_vars[probe].append(effect_matrix)
            for idx, assertion in enumerate(z3_effect_constraints(effect_matrix)):
                solver.add(assertion)
                assertions.append({"kind": "effect_C", "target": prefix, "index": str(idx), "expr": str(assertion)})

        for i in range(2):
            for j in range(2):
                target = z3_real_value(1.0 if i == j else 0.0)
                assertion = z3_sum([effect_vars[probe][outcome][i][j] for outcome in range(len(effect_vars[probe]))]) == target
                solver.add(assertion)
                assertions.append({"kind": "povm_normalization_C", "target": probe, "entry": f"{i},{j}", "expr": str(assertion)})

    trace_terms: dict[str, dict[str, list[z3.ArithRef]]] = {"rho_a": {}, "rho_b": {}}
    for state_name, rho in rho_vars.items():
        for probe in family:
            trace_terms[state_name][probe] = [
                z3_trace_term(effect_vars[probe][outcome], rho)
                for outcome in range(len(effect_vars[probe]))
            ]

    metadata = {
        "bound_input": "density-matrix entries and POVM-effect matrix entries only",
        "born_derivation": "Tr(M_k rho) is the in-solver arithmetic term sum_ij M_k[i,j] * rho[j,i]",
        "matrix_entry_bindings": len(bindings),
        "constraint_assertions": len(assertions),
        "bindings": bindings,
        "constraints": assertions,
        "trace_terms": {
            state: {
                probe: [str(term) for term in terms]
                for probe, terms in probe_map.items()
            }
            for state, probe_map in trace_terms.items()
        },
    }
    return solver, trace_terms, metadata


def z3_derived_values(
    rho_a: jax.Array,
    rho_b: jax.Array,
    family: list[str],
    effects: dict[str, list[jax.Array]],
) -> dict[str, Any]:
    solver, trace_terms, metadata = z3_build_problem(rho_a, rho_b, family, effects)
    verdict = str(solver.check())
    values: dict[str, dict[str, list[float]]] = {"rho_a": {}, "rho_b": {}}
    exact: dict[str, dict[str, list[str]]] = {"rho_a": {}, "rho_b": {}}
    if verdict == "sat":
        model = solver.model()
        for state, probe_map in trace_terms.items():
            for probe, terms in probe_map.items():
                evaluated = [model.eval(term, model_completion=True) for term in terms]
                values[state][probe] = [z3_to_float(value) for value in evaluated]
                exact[state][probe] = [str(value) for value in evaluated]
    return {"ran": True, "verdict": verdict, "values": values, "exact": exact, "metadata": metadata}


def z3_relation_query(
    rho_a: jax.Array,
    rho_b: jax.Array,
    family: list[str],
    effects: dict[str, list[jax.Array]],
) -> dict[str, Any]:
    solver, trace_terms, metadata = z3_build_problem(rho_a, rho_b, family, effects)
    equalities = [
        trace_terms["rho_a"][probe][outcome] == trace_terms["rho_b"][probe][outcome]
        for probe in family
        for outcome in range(len(trace_terms["rho_a"][probe]))
    ]
    solver.add(z3.And(*equalities) if equalities else z3.BoolVal(True))
    verdict = str(solver.check())
    return {
        "ran": True,
        "verdict": verdict,
        "predicate": "rho_a ~_M rho_b iff all solver-derived Tr(M_k rho_a) and Tr(M_k rho_b) terms are equal for active probes in M",
        "asserted_relation_equalities": len(equalities),
        "relation_equality_terms": [str(item) for item in equalities],
        "metadata": metadata,
    }


def z3_separator_query(
    rho_a: jax.Array,
    rho_b: jax.Array,
    family: list[str],
    effects: dict[str, list[jax.Array]],
) -> dict[str, Any]:
    solver, trace_terms, metadata = z3_build_problem(rho_a, rho_b, family, effects)
    disequalities = [
        trace_terms["rho_a"][probe][outcome] != trace_terms["rho_b"][probe][outcome]
        for probe in family
        for outcome in range(len(trace_terms["rho_a"][probe]))
    ]
    solver.add(z3.Or(*disequalities) if disequalities else z3.BoolVal(False))
    verdict = str(solver.check())
    return {
        "ran": True,
        "verdict": verdict,
        "predicate": "there exists an active probe outcome whose solver-derived Tr(M_k rho) separates rho_a from rho_b",
        "asserted_separator_disequalities": len(disequalities),
        "separator_disequality_terms": [str(item) for item in disequalities],
        "metadata": metadata,
    }


def cvc5_real_value(solver: cvc5.Solver, value: float) -> Any:
    f = frac(value)
    return solver.mkReal(f.numerator, f.denominator)


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_real_value(solver, 0.0)
    return terms[0] if len(terms) == 1 else solver.mkTerm(cvc5.Kind.ADD, *terms)


def cvc5_product(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(cvc5.Kind.MULT, left, right)


def cvc5_fraction_to_float(text: str) -> float:
    item = text.strip()
    if item.startswith("(/ (- ") and item.endswith(")"):
        numerator, denominator = item[len("(/ (- ") : -1].split(") ")
        return float(Fraction(-int(numerator), int(denominator)))
    if item.startswith("(/ ") and item.endswith(")"):
        numerator, denominator = item[len("(/ ") : -1].split()
        return float(Fraction(int(numerator), int(denominator)))
    return float(Fraction(item))


def cvc5_bind_matrix(
    solver: cvc5.Solver,
    prefix: str,
    entries: list[list[float]],
    bindings: list[dict[str, Any]],
) -> list[list[Any]]:
    real_sort = solver.getRealSort()
    matrix = []
    for i, row in enumerate(entries):
        out_row = []
        for j, value in enumerate(row):
            var = solver.mkConst(real_sort, f"{prefix}_{i}_{j}")
            solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, var, cvc5_real_value(solver, value)))
            bindings.append({"kind": "matrix_entry", "matrix": prefix, "i": i, "j": j, "var": str(var), "value": value})
            out_row.append(var)
        matrix.append(out_row)
    return matrix


def cvc5_geq_zero(solver: cvc5.Solver, term: Any) -> Any:
    return solver.mkTerm(cvc5.Kind.GEQ, term, cvc5_real_value(solver, 0.0))


def cvc5_sub(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(cvc5.Kind.SUB, left, right)


def cvc5_density_constraints(solver: cvc5.Solver, matrix: list[list[Any]]) -> list[Any]:
    det = cvc5_sub(
        solver,
        cvc5_product(solver, matrix[0][0], matrix[1][1]),
        cvc5_product(solver, matrix[0][1], matrix[1][0]),
    )
    return [
        solver.mkTerm(cvc5.Kind.EQUAL, cvc5_sum(solver, [matrix[0][0], matrix[1][1]]), cvc5_real_value(solver, 1.0)),
        solver.mkTerm(cvc5.Kind.EQUAL, matrix[0][1], matrix[1][0]),
        cvc5_geq_zero(solver, matrix[0][0]),
        cvc5_geq_zero(solver, matrix[1][1]),
        cvc5_geq_zero(solver, det),
    ]


def cvc5_effect_constraints(solver: cvc5.Solver, effect: list[list[Any]]) -> list[Any]:
    det = cvc5_sub(
        solver,
        cvc5_product(solver, effect[0][0], effect[1][1]),
        cvc5_product(solver, effect[0][1], effect[1][0]),
    )
    return [
        solver.mkTerm(cvc5.Kind.EQUAL, effect[0][1], effect[1][0]),
        cvc5_geq_zero(solver, effect[0][0]),
        cvc5_geq_zero(solver, effect[1][1]),
        cvc5_geq_zero(solver, det),
    ]


def cvc5_trace_term(solver: cvc5.Solver, effect: list[list[Any]], rho: list[list[Any]]) -> Any:
    return cvc5_sum(
        solver,
        [cvc5_product(solver, effect[i][j], rho[j][i]) for i in range(2) for j in range(2)],
    )


def cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(False)
    return terms[0] if len(terms) == 1 else solver.mkTerm(cvc5.Kind.OR, *terms)


def cvc5_and(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(True)
    return terms[0] if len(terms) == 1 else solver.mkTerm(cvc5.Kind.AND, *terms)


def cvc5_build_problem(
    rho_a: jax.Array,
    rho_b: jax.Array,
    family: list[str],
    effects: dict[str, list[jax.Array]],
    *,
    produce_models: bool = False,
) -> tuple[cvc5.Solver, dict[str, dict[str, list[Any]]], dict[str, Any]]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    if produce_models:
        solver.setOption("produce-models", "true")
    bindings: list[dict[str, Any]] = []
    assertions: list[dict[str, str]] = []

    rho_vars = {
        "rho_a": cvc5_bind_matrix(solver, "rho_a", real_matrix(rho_a), bindings),
        "rho_b": cvc5_bind_matrix(solver, "rho_b", real_matrix(rho_b), bindings),
    }
    for state_name, matrix in rho_vars.items():
        for idx, assertion in enumerate(cvc5_density_constraints(solver, matrix)):
            solver.assertFormula(assertion)
            assertions.append({"kind": "density_C", "target": state_name, "index": str(idx), "expr": str(assertion)})

    distinct_terms = [
        solver.mkTerm(cvc5.Kind.NOT, solver.mkTerm(cvc5.Kind.EQUAL, rho_vars["rho_a"][i][j], rho_vars["rho_b"][i][j]))
        for i in range(2)
        for j in range(2)
    ]
    distinct_assertion = cvc5_or(solver, distinct_terms)
    solver.assertFormula(distinct_assertion)
    assertions.append({"kind": "rung_specific_C", "target": "rho_a_vs_rho_b", "expr": str(distinct_assertion)})

    effect_vars: dict[str, list[list[list[Any]]]] = {}
    for probe in family:
        effect_vars[probe] = []
        for outcome, effect in enumerate(effects[probe]):
            prefix = f"M_{probe}_{outcome}"
            effect_matrix = cvc5_bind_matrix(solver, prefix, real_matrix(effect), bindings)
            effect_vars[probe].append(effect_matrix)
            for idx, assertion in enumerate(cvc5_effect_constraints(solver, effect_matrix)):
                solver.assertFormula(assertion)
                assertions.append({"kind": "effect_C", "target": prefix, "index": str(idx), "expr": str(assertion)})

        for i in range(2):
            for j in range(2):
                target = cvc5_real_value(solver, 1.0 if i == j else 0.0)
                assertion = solver.mkTerm(
                    cvc5.Kind.EQUAL,
                    cvc5_sum(solver, [effect_vars[probe][outcome][i][j] for outcome in range(len(effect_vars[probe]))]),
                    target,
                )
                solver.assertFormula(assertion)
                assertions.append({"kind": "povm_normalization_C", "target": probe, "entry": f"{i},{j}", "expr": str(assertion)})

    trace_terms: dict[str, dict[str, list[Any]]] = {"rho_a": {}, "rho_b": {}}
    for state_name, rho in rho_vars.items():
        for probe in family:
            trace_terms[state_name][probe] = [
                cvc5_trace_term(solver, effect_vars[probe][outcome], rho)
                for outcome in range(len(effect_vars[probe]))
            ]

    metadata = {
        "bound_input": "density-matrix entries and POVM-effect matrix entries only",
        "born_derivation": "Tr(M_k rho) is the in-solver arithmetic term sum_ij M_k[i,j] * rho[j,i]",
        "matrix_entry_bindings": len(bindings),
        "constraint_assertions": len(assertions),
        "bindings": bindings,
        "constraints": assertions,
        "trace_terms": {
            state: {
                probe: [str(term) for term in terms]
                for probe, terms in probe_map.items()
            }
            for state, probe_map in trace_terms.items()
        },
    }
    return solver, trace_terms, metadata


def cvc5_derived_values(
    rho_a: jax.Array,
    rho_b: jax.Array,
    family: list[str],
    effects: dict[str, list[jax.Array]],
) -> dict[str, Any]:
    solver, trace_terms, metadata = cvc5_build_problem(rho_a, rho_b, family, effects, produce_models=True)
    verdict = str(solver.checkSat())
    values: dict[str, dict[str, list[float]]] = {"rho_a": {}, "rho_b": {}}
    exact: dict[str, dict[str, list[str]]] = {"rho_a": {}, "rho_b": {}}
    if verdict == "sat":
        for state, probe_map in trace_terms.items():
            for probe, terms in probe_map.items():
                evaluated = [str(solver.getValue(term)) for term in terms]
                values[state][probe] = [cvc5_fraction_to_float(value) for value in evaluated]
                exact[state][probe] = evaluated
    return {"ran": True, "verdict": verdict, "values": values, "exact": exact, "metadata": metadata}


def cvc5_relation_query(
    rho_a: jax.Array,
    rho_b: jax.Array,
    family: list[str],
    effects: dict[str, list[jax.Array]],
) -> dict[str, Any]:
    solver, trace_terms, metadata = cvc5_build_problem(rho_a, rho_b, family, effects)
    equalities = [
        solver.mkTerm(cvc5.Kind.EQUAL, trace_terms["rho_a"][probe][outcome], trace_terms["rho_b"][probe][outcome])
        for probe in family
        for outcome in range(len(trace_terms["rho_a"][probe]))
    ]
    solver.assertFormula(cvc5_and(solver, equalities))
    verdict = str(solver.checkSat())
    return {
        "ran": True,
        "verdict": verdict,
        "predicate": "rho_a ~_M rho_b iff all solver-derived Tr(M_k rho_a) and Tr(M_k rho_b) terms are equal for active probes in M",
        "asserted_relation_equalities": len(equalities),
        "relation_equality_terms": [str(item) for item in equalities],
        "metadata": metadata,
    }


def cvc5_separator_query(
    rho_a: jax.Array,
    rho_b: jax.Array,
    family: list[str],
    effects: dict[str, list[jax.Array]],
) -> dict[str, Any]:
    solver, trace_terms, metadata = cvc5_build_problem(rho_a, rho_b, family, effects)
    disequalities = [
        solver.mkTerm(
            cvc5.Kind.NOT,
            solver.mkTerm(cvc5.Kind.EQUAL, trace_terms["rho_a"][probe][outcome], trace_terms["rho_b"][probe][outcome]),
        )
        for probe in family
        for outcome in range(len(trace_terms["rho_a"][probe]))
    ]
    solver.assertFormula(cvc5_or(solver, disequalities))
    verdict = str(solver.checkSat())
    return {
        "ran": True,
        "verdict": verdict,
        "predicate": "there exists an active probe outcome whose solver-derived Tr(M_k rho) separates rho_a from rho_b",
        "asserted_separator_disequalities": len(disequalities),
        "separator_disequality_terms": [str(item) for item in disequalities],
        "metadata": metadata,
    }


def constraint_report(state_map: dict[str, jax.Array], effects: dict[str, list[jax.Array]]) -> dict[str, Any]:
    report = {}
    for state_id, rho in state_map.items():
        trace = round(float(jax.device_get(jnp.real(jnp.trace(rho)))), 12)
        hermitian_gap = round(float(jax.device_get(jnp.max(jnp.abs(rho - jnp.conjugate(rho.T))))), 15)
        eig_floor = round(float(jax.device_get(jnp.min(jnp.linalg.eigvalsh(rho)))), 15)
        norms = {}
        for probe, rows in effects.items():
            norms[probe] = round(sum(born(effect, rho) for effect in rows), 12)
        report[state_id] = {
            "trace": trace,
            "trace_is_one": abs(trace - 1.0) <= TOL,
            "hermitian_max_gap": hermitian_gap,
            "psd_min_eigenvalue": eig_floor,
            "probability_normalizations": norms,
        }
    return report


def matrix_payload(state_map: dict[str, jax.Array], effects: dict[str, list[jax.Array]]) -> dict[str, Any]:
    return {
        "density_matrices_real": {state_id: real_matrix(rho) for state_id, rho in sorted(state_map.items())},
        "probe_effect_matrices_real": {
            probe: [real_matrix(effect) for effect in effect_list]
            for probe, effect_list in sorted(effects.items())
        },
    }


def main() -> int:
    state_map = states()
    effects = probe_effects()
    rho_a = state_map["rho_a_x_plus"]
    rho_b = state_map["rho_b_x_minus"]
    q_z = quotient(state_map, "M1_Z", effects)
    q_zx = quotient(state_map, "M2_ZX", effects)
    z_stats_a = [born(effect, rho_a) for effect in effects["Z"]]
    z_stats_b = [born(effect, rho_b) for effect in effects["Z"]]
    x_stats_a = [born(effect, rho_a) for effect in effects["X"]]
    x_stats_b = [born(effect, rho_b) for effect in effects["X"]]

    z3_z = z3_relation_query(rho_a, rho_b, FAMILIES["M1_Z"], effects)
    z3_zx = z3_relation_query(rho_a, rho_b, FAMILIES["M2_ZX"], effects)
    z3_sep_z = z3_separator_query(rho_a, rho_b, FAMILIES["M1_Z"], effects)
    z3_sep_zx = z3_separator_query(rho_a, rho_b, FAMILIES["M2_ZX"], effects)
    z3_derive_z = z3_derived_values(rho_a, rho_b, FAMILIES["M1_Z"], effects)
    z3_derive_zx = z3_derived_values(rho_a, rho_b, FAMILIES["M2_ZX"], effects)

    cvc5_z = cvc5_relation_query(rho_a, rho_b, FAMILIES["M1_Z"], effects)
    cvc5_zx = cvc5_relation_query(rho_a, rho_b, FAMILIES["M2_ZX"], effects)
    cvc5_sep_z = cvc5_separator_query(rho_a, rho_b, FAMILIES["M1_Z"], effects)
    cvc5_sep_zx = cvc5_separator_query(rho_a, rho_b, FAMILIES["M2_ZX"], effects)
    cvc5_derive_z = cvc5_derived_values(rho_a, rho_b, FAMILIES["M1_Z"], effects)
    cvc5_derive_zx = cvc5_derived_values(rho_a, rho_b, FAMILIES["M2_ZX"], effects)

    constraints = constraint_report(state_map, effects)

    z_equal = all(abs(a - b) <= TOL for a, b in zip(z_stats_a, z_stats_b))
    x_different = any(abs(a - b) > TOL for a, b in zip(x_stats_a, x_stats_b))
    all_constraints_ok = all(
        row["trace_is_one"]
        and row["hermitian_max_gap"] <= TOL
        and row["psd_min_eigenvalue"] >= -TOL
        and all(abs(v - 1.0) <= TOL for v in row["probability_normalizations"].values())
        for row in constraints.values()
    )
    all_pass = (
        z_equal
        and x_different
        and q_z["class_count"] < q_zx["class_count"]
        and z3_z["verdict"] == cvc5_z["verdict"] == "sat"
        and z3_zx["verdict"] == cvc5_zx["verdict"] == "unsat"
        and z3_sep_z["verdict"] == cvc5_sep_z["verdict"] == "unsat"
        and z3_sep_zx["verdict"] == cvc5_sep_zx["verdict"] == "sat"
        and z3_derive_zx["values"] == cvc5_derive_zx["values"]
        and all_constraints_ok
    )

    result = {
        "schema": "foundation_r0_distinguishability_engine_leg_v3_derived_smt",
        "object_id": "foundation_r0_distinguishability_jax_smt",
        "rung_id": "foundation_r0_distinguishability",
        "classification": CLASSIFICATION,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_sha256(),
        "result_path": str(RESULT_PATH),
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "fractions", "hashlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["jax", "jax.numpy", "z3", "cvc5"],
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "M": {
            "M1": ["Z"],
            "M2": ["Z", "X"],
            "probe_effects": {
                "Z": ["|0><0|", "|1><1|"],
                "X": ["|+><+|", "|-><-|"],
            },
        },
        "C": {
            "trace_one": True,
            "psd": True,
            "hermitian": True,
            "povm_normalization": True,
            "distinct_configs": "rho_a_x_plus and rho_b_x_minus have unequal bound density-matrix entries",
            "rung_specific_constraint": "rho_a ~_M rho_b and separator existence are solver queries over derived trace terms, not bound probability variables",
            "per_state": constraints,
        },
        "S": matrix_payload(state_map, effects),
        "S_mod_M": {"M1_Z": q_z, "M2_ZX": q_zx},
        "witness_pair": {
            "rho_a": "rho_a_x_plus",
            "rho_b": "rho_b_x_minus",
            "Z_stats_a_control_numeric": z_stats_a,
            "Z_stats_b_control_numeric": z_stats_b,
            "X_stats_a_control_numeric": x_stats_a,
            "X_stats_b_control_numeric": x_stats_b,
            "Z_equal": z_equal,
            "X_different": x_different,
        },
        "smt": {
            "z3": {
                "version": z3.get_version_string(),
                "derived_values_M1_Z": z3_derive_z,
                "derived_values_M2_ZX": z3_derive_zx,
                "relation_M1_Z": z3_z,
                "relation_M2_ZX": z3_zx,
                "separator_M1_Z": z3_sep_z,
                "separator_M2_ZX": z3_sep_zx,
            },
            "cvc5": {
                "version": getattr(cvc5, "__version__", "unknown"),
                "derived_values_M1_Z": cvc5_derive_z,
                "derived_values_M2_ZX": cvc5_derive_zx,
                "relation_M1_Z": cvc5_z,
                "relation_M2_ZX": cvc5_zx,
                "separator_M1_Z": cvc5_sep_z,
                "separator_M2_ZX": cvc5_sep_zx,
            },
        },
        "negative_control_flip": {
            "control": "erase_X_from_M2_ZX",
            "relation_with_ZX": z3_zx["verdict"],
            "relation_after_erasing_X": z3_z["verdict"],
            "separator_with_ZX": z3_sep_zx["verdict"],
            "separator_after_erasing_X": z3_sep_z["verdict"],
            "z3_relation_flip": [z3_zx["verdict"], z3_z["verdict"]],
            "cvc5_relation_flip": [cvc5_zx["verdict"], cvc5_z["verdict"]],
            "z3_separator_flip": [z3_sep_z["verdict"], z3_sep_zx["verdict"]],
            "cvc5_separator_flip": [cvc5_sep_z["verdict"], cvc5_sep_zx["verdict"]],
            "n_classes_Z": q_z["class_count"],
            "n_classes_ZX": q_zx["class_count"],
            "solver_derived_bound_entry_probabilities": {
                "z3": z3_derive_zx["values"],
                "cvc5": cvc5_derive_zx["values"],
            },
            "solver_derived_X_probabilities": {
                "rho_a": z3_derive_zx["values"]["rho_a"]["X"],
                "rho_b": z3_derive_zx["values"]["rho_b"]["X"],
                "derivation_source": "z3 model evaluation of trace terms over bound matrix entries; not precomputed probability bindings",
            },
        },
        "summary": {
            "n_classes_Z": q_z["class_count"],
            "n_classes_ZX": q_zx["class_count"],
            "Z_equal": z_equal,
            "X_different": x_different,
            "z3_M1_Z": z3_z["verdict"],
            "z3_M2_ZX": z3_zx["verdict"],
            "cvc5_M1_Z": cvc5_z["verdict"],
            "cvc5_M2_ZX": cvc5_zx["verdict"],
            "z3_separator_M1_Z": z3_sep_z["verdict"],
            "z3_separator_M2_ZX": z3_sep_zx["verdict"],
            "cvc5_separator_M1_Z": cvc5_sep_z["verdict"],
            "cvc5_separator_M2_ZX": cvc5_sep_zx["verdict"],
            "all_pass": all_pass,
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "JAX_SMT_FOUNDATION_R0_DERIVED_DONE "
        f"all_pass={str(all_pass).lower()} "
        f"relation_z3_Z={z3_z['verdict']} relation_z3_ZX={z3_zx['verdict']} "
        f"relation_cvc5_Z={cvc5_z['verdict']} relation_cvc5_ZX={cvc5_zx['verdict']} "
        f"separator_z3_Z={z3_sep_z['verdict']} separator_z3_ZX={z3_sep_zx['verdict']} "
        f"separator_cvc5_Z={cvc5_sep_z['verdict']} separator_cvc5_ZX={cvc5_sep_zx['verdict']} "
        f"n_classes_Z={q_z['class_count']} n_classes_ZX={q_zx['class_count']}"
    )
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
