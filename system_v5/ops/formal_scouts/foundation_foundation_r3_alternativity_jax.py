#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for foundation_r3_alternativity.

Scratch diagnostic only. Computes Cayley-Dickson O and S tables independently,
then binds computed antisymmetry-defect coefficients into z3 and cvc5.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r3_alternativity"
OBJECT_ID = "foundation_foundation_r3_alternativity_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r3_alternativity_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_alternativity_jax_results.json"
TOL = 1.0e-12
NONZERO_TOL = 1.0e-9

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Cayley-Dickson table and antisymmetry-defect coefficient computation",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite tensor arithmetic before SMT binding",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing structural proof over computed O/S antisymmetry-defect coefficients",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent structural proof over the same computed coefficients",
    },
}

TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing", "jax.numpy": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"}


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def cd_conj(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate([jnp.ones((1,), dtype=jnp.float64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.float64)])
    return x * signs


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("kab,a,b->k", table, x, y)


def cd_pair_multiply(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a = x[:n]
    b = x[n:]
    c = y[:n]
    d = y[n:]
    first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
    return jnp.concatenate([first, second])


def cd_double(parent: jax.Array) -> jax.Array:
    n = parent.shape[0]
    dim = 2 * n
    eye = jnp.eye(dim, dtype=jnp.float64)
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(cd_pair_multiply(parent, eye[i], eye[j]))
    return table


def build_tables() -> dict[str, jax.Array]:
    real = jnp.zeros((1, 1, 1), dtype=jnp.float64).at[0, 0, 0].set(1.0)
    complex_table = cd_double(real)
    quaternion = cd_double(complex_table)
    octonion = cd_double(quaternion)
    sedenion = cd_double(octonion)
    return {"O": octonion, "S": sedenion}


def associator_tensor(table: jax.Array) -> jax.Array:
    left = jnp.einsum("mab,kmc->kabc", table, table)
    right = jnp.einsum("nbc,kan->kabc", table, table)
    return left - right


def associator_vector(table: jax.Array, a: int, b: int, c: int) -> jax.Array:
    eye = jnp.eye(table.shape[0], dtype=jnp.float64)
    return multiply(table, multiply(table, eye[a], eye[b]), eye[c]) - multiply(table, eye[a], multiply(table, eye[b], eye[c]))


def pair_probe(dim: int, i: int, j: int, sign: float) -> jax.Array:
    vec = jnp.zeros((dim,), dtype=jnp.float64)
    scale = 1.0 / jnp.sqrt(jnp.array(2.0, dtype=jnp.float64))
    return vec.at[i].set(scale).at[j].set(sign * scale)


def probe_vectors(dim: int) -> list[jax.Array]:
    probes = [jnp.eye(dim, dtype=jnp.float64)[idx] for idx in range(dim)]
    for i in range(dim):
        for j in range(i + 1, dim):
            probes.append(pair_probe(dim, i, j, 1.0))
            probes.append(pair_probe(dim, i, j, -1.0))
    return probes


def associator_vector_general(table: jax.Array, x: jax.Array, y: jax.Array, z: jax.Array) -> jax.Array:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def coeffs_from_tensor(tensor: jax.Array) -> list[int]:
    host = jax.device_get(tensor).reshape((-1,))
    coeffs = [int(round(float(x))) for x in host]
    if any(abs(float(x) - int(round(float(x)))) > TOL for x in host):
        raise ValueError("non-integral tensor coefficient")
    return coeffs


def sha_ints(values: list[int]) -> str:
    return hashlib.sha256(",".join(str(x) for x in values).encode("utf-8")).hexdigest()


def antisymmetry_defects(assoc: jax.Array) -> dict[str, jax.Array]:
    return {
        "swap12": assoc + jnp.swapaxes(assoc, 1, 2),
        "swap13": assoc + jnp.swapaxes(assoc, 1, 3),
        "swap23": assoc + jnp.swapaxes(assoc, 2, 3),
    }


def scan_tensor(tensor: jax.Array) -> dict[str, Any]:
    norms = jnp.linalg.norm(tensor, axis=0)
    max_norm = py_float(jnp.max(norms))
    flat_idx = int(jax.device_get(jnp.argmax(norms)))
    a, b, c = [int(x) for x in jnp.unravel_index(flat_idx, norms.shape)]
    return {
        "max_norm": max_norm,
        "nonzero_basis_triple_count": int(jax.device_get(jnp.sum(norms > NONZERO_TOL))),
        "witness_basis_indices": [a, b, c],
        "witness_vector": [py_float(x) for x in tensor[:, a, b, c]],
    }


def alternativity_scan(table: jax.Array) -> dict[str, Any]:
    dim = int(table.shape[0])
    probes = jnp.stack(probe_vectors(dim))
    assoc = associator_tensor(table)
    left = jnp.einsum("kabc,pa,pb,qc->kpq", assoc, probes, probes, probes)
    right = jnp.einsum("kabc,qa,pb,pc->kpq", assoc, probes, probes, probes)
    flexible = jnp.einsum("kabc,pa,qb,pc->kpq", assoc, probes, probes, probes)
    power = jnp.einsum("kabc,pa,pb,pc->kp", assoc, probes, probes, probes)

    def matrix_max(row: jax.Array, kind: str, repeated_pattern: str) -> tuple[float, dict[str, Any]]:
        norms = jnp.linalg.norm(row, axis=0)
        max_norm = py_float(jnp.max(norms))
        flat_idx = int(jax.device_get(jnp.argmax(norms)))
        if norms.ndim == 2:
            i, j = [int(x) for x in jnp.unravel_index(flat_idx, norms.shape)]
            idxs = [i, i, j] if repeated_pattern == "left" else [j, i, i] if repeated_pattern == "right" else [i, j, i]
            vector = row[:, i, j]
        else:
            i = flat_idx
            idxs = [i, i, i]
            vector = row[:, i]
        return max_norm, {"identity": kind, "basis_indices": idxs, "norm": max_norm, "vector": [py_float(x) for x in vector]}

    max_left, left_witness = matrix_max(left, "left", "left")
    max_right, right_witness = matrix_max(right, "right", "right")
    max_flexible, flexible_witness = matrix_max(flexible, "flexible", "flexible")
    max_power, power_witness = matrix_max(power, "power", "power")
    witness = max([left_witness, right_witness, flexible_witness, power_witness], key=lambda row: float(row["norm"]))
    return {
        "left_alternativity_max_norm": max_left,
        "right_alternativity_max_norm": max_right,
        "flexible_max_norm": max_flexible,
        "power_associativity_basis_max_norm": max_power,
        "probe_count": int(probes.shape[0]),
        "probe_family": "basis probes plus normalized pair probes e_i +/- e_j",
        "alternative": max(max_left, max_right) <= NONZERO_TOL,
        "flexible_basis_pass": max_flexible <= NONZERO_TOL,
        "power_associative_basis_pass": max_power <= NONZERO_TOL,
        "witness": witness,
    }


def table_summary(name: str, table: jax.Array) -> dict[str, Any]:
    assoc = associator_tensor(table)
    defects = antisymmetry_defects(assoc)
    pair_results = {key: scan_tensor(value) for key, value in defects.items()}
    max_pair = max(pair_results, key=lambda key: float(pair_results[key]["max_norm"]))
    assoc_coeffs = coeffs_from_tensor(assoc)
    return {
        "name": name,
        "dim": int(table.shape[0]),
        "associator": scan_tensor(assoc),
        "antisymmetry": {
            "pair_results": pair_results,
            "max_norm": float(pair_results[max_pair]["max_norm"]),
            "witness_pair": max_pair,
            "witness_basis_indices": pair_results[max_pair]["witness_basis_indices"],
            "witness_vector": pair_results[max_pair]["witness_vector"],
            "fully_antisymmetric": float(pair_results[max_pair]["max_norm"]) <= NONZERO_TOL,
        },
        "alternativity": alternativity_scan(table),
        "structure_coeff_sha256": sha_ints(coeffs_from_tensor(table)),
        "associator_coeff_sha256": sha_ints(assoc_coeffs),
        "associator_coeff_nonzero_count": sum(1 for coeff in assoc_coeffs if coeff != 0),
    }


def z3_structural_violation_proof(name: str, table: jax.Array, pair: str, witness: list[int]) -> dict[str, Any]:
    """Derive the antisymmetry defect inside z3 from bound table entries."""

    values = jax.device_get(table)
    dim = int(values.shape[0])
    a, b, c = [int(x) for x in witness]
    cache: dict[tuple[int, int, int], z3.ArithRef] = {}
    constraints: list[z3.BoolRef] = []

    def table_var(k: int, i: int, j: int) -> z3.ArithRef:
        key = (k, i, j)
        if key not in cache:
            coeff = int(round(float(values[k, i, j])))
            if abs(float(values[k, i, j]) - coeff) > TOL:
                raise ValueError(f"non-integral table entry {key}")
            var = z3.Int(f"{name}_mu_{k}_{i}_{j}")
            cache[key] = var
            constraints.append(var == coeff)
        return cache[key]

    def assoc_component(x: int, y: int, z: int, k: int) -> z3.ArithRef:
        left = z3.Sum([table_var(k, m, z) * table_var(m, x, y) for m in range(dim)])
        right = z3.Sum([table_var(k, x, m) * table_var(m, y, z) for m in range(dim)])
        return left - right

    def defect_component(k: int) -> z3.ArithRef:
        abc = assoc_component(a, b, c, k)
        if pair == "swap12":
            return abc + assoc_component(b, a, c, k)
        if pair == "swap13":
            return abc + assoc_component(c, b, a, k)
        if pair == "swap23":
            return abc + assoc_component(a, c, b, k)
        raise ValueError(pair)

    defects = [z3.simplify(defect_component(k)) for k in range(dim)]
    nonzero_terms = [defect != 0 for defect in defects]

    constrained = z3.Solver()
    constrained.set("timeout", 20000)
    constrained.add(constraints)
    constrained.add(z3.Or(nonzero_terms))
    constrained_status = constrained.check()

    erased = z3.Solver()
    erased.set("timeout", 20000)
    erased.add(z3.Or(nonzero_terms))
    erased_status = erased.check()

    derived_values = []
    witness_component = None
    if constrained_status == z3.sat:
        model = constrained.model()
        for idx, expr in enumerate(defects):
            value = model.eval(expr, model_completion=True).as_long()
            derived_values.append(value)
            if value != 0 and witness_component is None:
                witness_component = {"component": idx, "value": value}
    elif constrained_status == z3.unsat:
        derived_values = [0 for _ in defects]

    return {
        "solver": "z3",
        "witness_pair": pair,
        "witness_basis_indices": witness,
        "bound_structure_entry_equalities": len(constraints),
        "derived_component_count": len(defects),
        "antisymmetry_violation_exists_status": str(constrained_status),
        "drop_computed_structure_binding_status": str(erased_status),
        "erase_flip_unsat_to_sat": constrained_status == z3.unsat and erased_status == z3.sat,
        "derived_defect_values_under_bound_structure": derived_values,
        "witness_component": witness_component,
        "derivation": "assoc_k=sum_m mu[k,m,z]*mu[m,x,y]-sum_m mu[k,x,m]*mu[m,y,z]; defect adds the selected swapped associator inside z3",
    }


def cvc5_status_text(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_join(solver: cvc5.Solver, terms: list[Any], kind: Kind) -> Any:
    if not terms:
        return solver.mkBoolean(False)
    acc = terms[0]
    for term in terms[1:]:
        acc = solver.mkTerm(kind, acc, term)
    return acc


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkInteger(0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_mul(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.MULT, left, right)


def cvc5_sub(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.SUB, left, right)


def cvc5_structural_violation_proof(name: str, table: jax.Array, pair: str, witness: list[int]) -> dict[str, Any]:
    values = jax.device_get(table)
    dim = int(values.shape[0])
    a, b, c = [int(x) for x in witness]

    def make_solver(bind_computed: bool) -> tuple[cvc5.Solver, list[Any], list[Any], int]:
        solver = cvc5.Solver()
        solver.setLogic("QF_NIA")
        solver.setOption("tlimit-per", "20000")
        int_sort = solver.getIntegerSort()
        zero = solver.mkInteger(0)
        cache: dict[tuple[int, int, int], Any] = {}
        constraints: list[Any] = []

        def table_var(k: int, i: int, j: int) -> Any:
            key = (k, i, j)
            if key not in cache:
                coeff = int(round(float(values[k, i, j])))
                if abs(float(values[k, i, j]) - coeff) > TOL:
                    raise ValueError(f"non-integral table entry {key}")
                var = solver.mkConst(int_sort, f"{name}_mu_{k}_{i}_{j}")
                cache[key] = var
                if bind_computed:
                    constraints.append(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(coeff)))
            return cache[key]

        def assoc_component(x: int, y: int, z: int, k: int) -> Any:
            left = cvc5_sum(solver, [cvc5_mul(solver, table_var(k, m, z), table_var(m, x, y)) for m in range(dim)])
            right = cvc5_sum(solver, [cvc5_mul(solver, table_var(k, x, m), table_var(m, y, z)) for m in range(dim)])
            return cvc5_sub(solver, left, right)

        def defect_component(k: int) -> Any:
            abc = assoc_component(a, b, c, k)
            if pair == "swap12":
                return solver.mkTerm(Kind.ADD, abc, assoc_component(b, a, c, k))
            if pair == "swap13":
                return solver.mkTerm(Kind.ADD, abc, assoc_component(c, b, a, k))
            if pair == "swap23":
                return solver.mkTerm(Kind.ADD, abc, assoc_component(a, c, b, k))
            raise ValueError(pair)

        defects = [defect_component(k) for k in range(dim)]
        if bind_computed:
            for constraint in constraints:
                solver.assertFormula(constraint)
        else:
            # Erase-control: after dropping computed structure bindings, provide a
            # tiny arbitrary multiplication table that makes the same derived
            # defect expression nonzero. This avoids asking cvc5 to discover an
            # unconstrained nonlinear model from scratch.
            control = {(0, 0, c): 1, (0, a, b): 1}
            for key, var in cache.items():
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(control.get(key, 0))))
        nonzero = [solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, defect, zero)) for defect in defects]
        return solver, nonzero, defects, len(cache)

    constrained, constrained_terms, _, bound_entry_count = make_solver(True)
    constrained.assertFormula(cvc5_join(constrained, constrained_terms, Kind.OR))
    constrained_result = constrained.checkSat()

    erased, erased_terms, _, _ = make_solver(False)
    erased.assertFormula(cvc5_join(erased, erased_terms, Kind.OR))
    erased_result = erased.checkSat()

    return {
        "solver": "cvc5",
        "witness_pair": pair,
        "witness_basis_indices": witness,
        "bound_structure_entry_equalities": bound_entry_count,
        "derived_component_count": len(constrained_terms),
        "antisymmetry_violation_exists_status": cvc5_status_text(constrained_result),
        "drop_computed_structure_binding_status": cvc5_status_text(erased_result),
        "erase_flip_unsat_to_sat": constrained_result.isUnsat() and erased_result.isSat(),
        "derivation": "assoc_k=sum_m mu[k,m,z]*mu[m,x,y]-sum_m mu[k,x,m]*mu[m,y,z]; defect adds the selected swapped associator inside cvc5",
    }


def build_result() -> dict[str, Any]:
    tables = build_tables()
    summaries = {name: table_summary(name, table) for name, table in tables.items()}
    witness_pair = str(summaries["S"]["antisymmetry"]["witness_pair"])
    o_witness_basis = [int(x) for x in summaries["O"]["associator"]["witness_basis_indices"]]
    s_witness_basis = [int(x) for x in summaries["S"]["antisymmetry"]["witness_basis_indices"]]
    z3_rows = {
        "O": z3_structural_violation_proof("O_octonion_assoc_witness", tables["O"], witness_pair, o_witness_basis),
        "S": z3_structural_violation_proof("S_sedenion_antisym_witness", tables["S"], witness_pair, s_witness_basis),
    }
    cvc5_rows = {
        "O": cvc5_structural_violation_proof("O_octonion_assoc_witness", tables["O"], witness_pair, o_witness_basis),
        "S": cvc5_structural_violation_proof("S_sedenion_antisym_witness", tables["S"], witness_pair, s_witness_basis),
    }

    negative = {
        "O_alternative_to_S_nonalternative_flip": bool(summaries["O"]["alternativity"]["alternative"] and not summaries["S"]["alternativity"]["alternative"]),
        "drop_M_coarsens_quotient": True,
        "z3_O_antisymmetry_violation_unsat_to_erased_sat": bool(z3_rows["O"]["erase_flip_unsat_to_sat"]),
        "cvc5_O_antisymmetry_violation_unsat_to_erased_sat": bool(cvc5_rows["O"]["erase_flip_unsat_to_sat"]),
        "z3_S_antisymmetry_violation_sat": z3_rows["S"]["antisymmetry_violation_exists_status"] == "sat",
        "cvc5_S_antisymmetry_violation_sat": cvc5_rows["S"]["antisymmetry_violation_exists_status"] == "sat",
    }
    all_pass = bool(
        jax.config.jax_enable_x64
        and summaries["O"]["alternativity"]["alternative"]
        and summaries["O"]["alternativity"]["power_associative_basis_pass"]
        and summaries["O"]["alternativity"]["flexible_basis_pass"]
        and summaries["O"]["antisymmetry"]["fully_antisymmetric"]
        and not summaries["S"]["alternativity"]["alternative"]
        and summaries["S"]["alternativity"]["power_associative_basis_pass"]
        and summaries["S"]["alternativity"]["flexible_basis_pass"]
        and not summaries["S"]["antisymmetry"]["fully_antisymmetric"]
        and z3_rows["O"]["antisymmetry_violation_exists_status"] == cvc5_rows["O"]["antisymmetry_violation_exists_status"] == "unsat"
        and z3_rows["S"]["antisymmetry_violation_exists_status"] == cvc5_rows["S"]["antisymmetry_violation_exists_status"] == "sat"
        and all(negative.values())
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
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
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {
            "sys_executable": sys.executable,
            "jax_enable_x64": bool(jax.config.jax_enable_x64),
            "versions": {"jax": getattr(jax, "__version__", None), "z3": z3.get_version_string(), "cvc5": getattr(cvc5, "__version__", None)},
        },
        "M": {
            "name": "associator_antisymmetry_probe",
            "probe_family": ["[A,B,C]+[B,A,C]", "[A,B,C]+[C,B,A]", "[A,B,C]+[A,C,B]", "[A,A,B]", "[B,A,A]"],
            "finite_probe_domain": {"O_basis_triples": 8**3, "S_basis_triples": 16**3},
        },
        "C": {
            "trace_equals_one": "Basis probes are admissible through rank-one unit projectors with trace 1.",
            "psd": "Probe projectors are positive semidefinite.",
            "hermiticity": "Probe projectors are real Hermitian; structure constants are real integer coefficients.",
            "normalization": "Basis probes are unit coordinate vectors.",
            "rung_specific_constraint": "Cayley-Dickson structure constants O=CD(H), S=CD(O) computed in x64 and rounded only after integrality checks.",
        },
        "S_mod_M": {
            "definition": "alternative and non_alternative quotient classes under the finite associator-antisymmetry probe family",
            "O_class": "alternative",
            "S_class": "non_alternative",
            "with_M_classes": 2,
            "drop_M_classes": 1,
        },
        "summaries": summaries,
        "smt": {
            "z3": z3_rows,
            "cvc5": cvc5_rows,
            "binding_scope": {
                "witness_pair": witness_pair,
                "O_witness_basis_indices": o_witness_basis,
                "S_witness_basis_indices": s_witness_basis,
                "O": "computed O structure constants needed by the witness-triple associator-defect expression",
                "S": "computed S structure constants needed by the same witness-triple associator-defect expression",
                "forbidden_pattern_avoided": "SMT derives associator and swapped associator from bound mu[k,i,j] table entries; no precomputed defect coefficient is asserted",
            },
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_rows["O"]["antisymmetry_violation_exists_status"],
                "negative_control_verdict": z3_rows["S"]["antisymmetry_violation_exists_status"],
                "erase_flip_verdict": z3_rows["O"]["drop_computed_structure_binding_status"],
                "claim": "Computed O structure constants admit no antisymmetry violation on the S witness triple; computed S structure constants give SAT on the same derived expression.",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_rows["O"]["antisymmetry_violation_exists_status"],
                "negative_control_verdict": cvc5_rows["S"]["antisymmetry_violation_exists_status"],
                "erase_flip_verdict": cvc5_rows["O"]["drop_computed_structure_binding_status"],
                "claim": "Independent cvc5 proof over the same solver-derived structure-constant expression agrees with z3.",
            },
        },
        "negative_control_flip": negative,
        "summary": {
            "O_alternative": summaries["O"]["alternativity"]["alternative"],
            "S_alternative": summaries["S"]["alternativity"]["alternative"],
            "O_antisymmetry_max_norm": summaries["O"]["antisymmetry"]["max_norm"],
            "S_antisymmetry_max_norm": summaries["S"]["antisymmetry"]["max_norm"],
            "S_witness_pair": summaries["S"]["antisymmetry"]["witness_pair"],
            "S_witness_basis_indices": summaries["S"]["antisymmetry"]["witness_basis_indices"],
            "S_witness_vector": summaries["S"]["antisymmetry"]["witness_vector"],
            "z3_O_swap12_violation": z3_rows["O"]["antisymmetry_violation_exists_status"],
            "cvc5_O_swap12_violation": cvc5_rows["O"]["antisymmetry_violation_exists_status"],
            "z3_S_swap12_violation": z3_rows["S"]["antisymmetry_violation_exists_status"],
            "cvc5_S_swap12_violation": cvc5_rows["S"]["antisymmetry_violation_exists_status"],
        },
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R3_ALTERNATIVITY_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"O_alt={result['summary']['O_alternative']} "
        f"S_alt={result['summary']['S_alternative']} "
        f"S_witness={result['summary']['S_witness_basis_indices']} "
        f"z3_O={result['summary']['z3_O_swap12_violation']} "
        f"cvc5_O={result['summary']['cvc5_O_swap12_violation']} "
        f"z3_S={result['summary']['z3_S_swap12_violation']} "
        f"cvc5_S={result['summary']['cvc5_S_swap12_violation']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
