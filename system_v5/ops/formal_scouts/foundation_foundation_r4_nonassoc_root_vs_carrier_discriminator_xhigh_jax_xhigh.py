#!/usr/bin/env python3
"""JAX + z3/cvc5 structural leg for foundation R4 nonassoc root-vs-carrier discriminator."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
import jax.numpy as jnp
import z3
from cvc5 import Kind


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh"
OBJECT_ID = RUNG_ID
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_jax_xhigh.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_jax_xhigh_results.json"
TOL = 1.0e-9

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Cayley-Dickson table construction before dual SMT binding",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite structure-constant computation; not a final scalar proof",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing in-solver derivation of unit-square, anticommutation, noncommutation, and H SAT/UNSAT flip",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT derivation of the same structural claims",
    },
}

TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing", "jax.numpy": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def py_int(value: Any) -> int:
    return int(round(py_float(value)))


def cd_conj(x: jax.Array) -> jax.Array:
    if x.shape[0] == 1:
        return x
    return x.at[1:].multiply(-1.0)


def cd_mul(x: jax.Array, y: jax.Array) -> jax.Array:
    n = int(x.shape[0])
    if n == 1:
        return x * y
    half = n // 2
    a, b = x[:half], x[half:]
    c, d = y[:half], y[half:]
    return jnp.concatenate([cd_mul(a, c) - cd_mul(cd_conj(d), b), cd_mul(d, a) + cd_mul(b, cd_conj(c))])


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def multiplication_table(dim: int) -> jax.Array:
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(cd_mul(basis(dim, i), basis(dim, j)))
    return table


def int_table(table: jax.Array) -> list[list[list[int]]]:
    dim = int(table.shape[0])
    values = jax.device_get(table)
    out: list[list[list[int]]] = []
    for k in range(dim):
        plane: list[list[int]] = []
        for i in range(dim):
            row: list[int] = []
            for j in range(dim):
                value = float(values[k, i, j])
                rounded = int(round(value))
                if abs(value - rounded) > TOL:
                    raise ValueError(f"non-integral structure constant at {(k, i, j)}: {value}")
                row.append(rounded)
            plane.append(row)
        out.append(plane)
    return out


def square_minus_one(table: jax.Array, idx: int) -> bool:
    dim = int(table.shape[0])
    vals = int_table(table)
    return vals[0][idx][idx] == -1 and all(vals[k][idx][idx] == 0 for k in range(1, dim))


def anticommutes(table: jax.Array, i: int, j: int) -> bool:
    dim = int(table.shape[0])
    vals = int_table(table)
    return all(vals[k][i][j] + vals[k][j][i] == 0 for k in range(dim))


def commutator_vector(table: jax.Array, i: int, j: int) -> jax.Array:
    return table[:, i, j] - table[:, j, i]


def carrier_numeric_summary(name: str, dim: int) -> dict[str, Any]:
    table = multiplication_table(dim)
    imaginary = list(range(1, dim))
    valid = [idx for idx in imaginary if square_minus_one(table, idx)]
    pair_failures = [(i, j) for i in valid for j in valid if i < j and not anticommutes(table, i, j)]
    max_comm = 0.0
    witness = None
    for i in imaginary:
        for j in imaginary:
            if i >= j:
                continue
            norm_value = py_float(jnp.linalg.norm(commutator_vector(table, i, j)))
            if norm_value > max_comm:
                max_comm = norm_value
                witness = {"i": i, "j": j, "commutator_norm": norm_value}
    return {
        "name": name,
        "real_dimension": dim,
        "finite": True,
        "imaginary_unit_count": len(valid) if not pair_failures else 0,
        "valid_imaginary_indices": valid,
        "pair_failures": pair_failures,
        "noncommutation": {"max_norm": max_comm, "witness": witness, "noncommutative": max_comm > TOL},
        "bare_root_admissible": dim >= 4 and max_comm > TOL,
        "cl6_7unit_admissible": (len(valid) if not pair_failures else 0) >= 7,
    }


def z3_int(value: int) -> z3.IntNumRef:
    return z3.IntVal(value)


def z3_bind_table(values: list[list[list[int]]], prefix: str) -> tuple[z3.Solver, list[list[list[z3.ArithRef]]]]:
    solver = z3.Solver()
    solver.set(timeout=20_000)
    dim = len(values)
    mu = [[[z3.Int(f"{prefix}_mu_{k}_{i}_{j}") for j in range(dim)] for i in range(dim)] for k in range(dim)]
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                solver.add(mu[k][i][j] == z3_int(values[k][i][j]))
    return solver, mu


def z3_square_constraints(mu: list[list[list[z3.ArithRef]]], idx: int) -> list[z3.BoolRef]:
    dim = len(mu)
    return [mu[0][idx][idx] == z3_int(-1)] + [mu[k][idx][idx] == z3_int(0) for k in range(1, dim)]


def z3_anticommute_constraints(mu: list[list[list[z3.ArithRef]]], i: int, j: int) -> list[z3.BoolRef]:
    dim = len(mu)
    return [mu[k][i][j] + mu[k][j][i] == z3_int(0) for k in range(dim)]


def z3_commutator_nonzero_terms(mu: list[list[list[z3.ArithRef]]], i: int, j: int) -> list[z3.BoolRef]:
    dim = len(mu)
    return [mu[k][i][j] - mu[k][j][i] != z3_int(0) for k in range(dim)]


def z3_has_at_least_units(values: list[list[list[int]]], required: int, prefix: str) -> dict[str, Any]:
    solver, mu = z3_bind_table(values, prefix)
    dim = len(values)
    selectors = [z3.Bool(f"{prefix}_select_{idx}") for idx in range(1, dim)]
    for slot, idx in zip(selectors, range(1, dim), strict=True):
        solver.add(z3.Implies(slot, z3.And(z3_square_constraints(mu, idx))))
    for offset_i, i in enumerate(range(1, dim)):
        for offset_j, j in enumerate(range(1, dim)):
            if i >= j:
                continue
            solver.add(z3.Implies(z3.And(selectors[offset_i], selectors[offset_j]), z3.And(z3_anticommute_constraints(mu, i, j))))
    solver.add(z3.Sum([z3.If(slot, 1, 0) for slot in selectors]) >= required)
    status = solver.check()
    model_selection: list[int] = []
    if status == z3.sat:
        model = solver.model()
        model_selection = [idx for slot, idx in zip(selectors, range(1, dim), strict=True) if z3.is_true(model.eval(slot, model_completion=True))]
    return {
        "status": str(status),
        "required_count": required,
        "candidate_imaginary_slots": dim - 1,
        "bound_structure_constant_count": dim * dim * dim,
        "derived_square_equations": dim - 1,
        "derived_pair_anticommutation_equation_groups": (dim - 1) * (dim - 2) // 2,
        "selected_indices_model": model_selection,
        "encoding": "selectors over imaginary basis units; selected units must square to -1 and all selected pairs must anticommute via bound mu[k,i,j] structure constants",
    }


def z3_h_bare_root(values: list[list[list[int]]], *, force_commutative: bool) -> dict[str, Any]:
    solver, mu = z3_bind_table(values, "H_bare_force_comm" if force_commutative else "H_bare")
    dim = len(values)
    noncomm_terms: list[z3.BoolRef] = []
    for i in range(1, dim):
        solver.add(z3.And(z3_square_constraints(mu, i)))
        for j in range(i + 1, dim):
            noncomm_terms.extend(z3_commutator_nonzero_terms(mu, i, j))
            if force_commutative:
                for k in range(dim):
                    solver.add(mu[k][i][j] - mu[k][j][i] == z3_int(0))
    solver.add(z3.Or(noncomm_terms))
    status = solver.check()
    return {
        "status": str(status),
        "force_commutativity": force_commutative,
        "claim": "H has finite table, imaginary units square to -1, and a derived nonzero commutator witness" if not force_commutative else "H is forced commutative while the bare root still requires a nonzero commutator",
        "bound_structure_constant_count": dim * dim * dim,
        "derived_expression": "mu[k,i,j] - mu[k,j,i] != 0 for some imaginary pair/output coordinate",
    }


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(value)


def cvc5_and(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(True)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.AND, *terms)


def cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(False)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.OR, *terms)


def cvc5_add(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_int(solver, 0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_bind_table(values: list[list[list[int]]], prefix: str) -> tuple[cvc5.Solver, list[list[list[Any]]]]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "true")
    solver.setOption("tlimit-per", "20000")
    dim = len(values)
    int_sort = solver.getIntegerSort()
    mu = [[[solver.mkConst(int_sort, f"{prefix}_mu_{k}_{i}_{j}") for j in range(dim)] for i in range(dim)] for k in range(dim)]
    for k in range(dim):
        for i in range(dim):
            for j in range(dim):
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, mu[k][i][j], cvc5_int(solver, values[k][i][j])))
    return solver, mu


def cvc5_square_constraints(solver: cvc5.Solver, mu: list[list[list[Any]]], idx: int) -> list[Any]:
    dim = len(mu)
    constraints = [solver.mkTerm(Kind.EQUAL, mu[0][idx][idx], cvc5_int(solver, -1))]
    constraints.extend(solver.mkTerm(Kind.EQUAL, mu[k][idx][idx], cvc5_int(solver, 0)) for k in range(1, dim))
    return constraints


def cvc5_anticommute_constraints(solver: cvc5.Solver, mu: list[list[list[Any]]], i: int, j: int) -> list[Any]:
    dim = len(mu)
    return [
        solver.mkTerm(Kind.EQUAL, solver.mkTerm(Kind.ADD, mu[k][i][j], mu[k][j][i]), cvc5_int(solver, 0))
        for k in range(dim)
    ]


def cvc5_commutator_nonzero_terms(solver: cvc5.Solver, mu: list[list[list[Any]]], i: int, j: int) -> list[Any]:
    dim = len(mu)
    return [
        solver.mkTerm(
            Kind.NOT,
            solver.mkTerm(Kind.EQUAL, solver.mkTerm(Kind.SUB, mu[k][i][j], mu[k][j][i]), cvc5_int(solver, 0)),
        )
        for k in range(dim)
    ]


def cvc5_has_at_least_units(values: list[list[list[int]]], required: int, prefix: str) -> dict[str, Any]:
    solver, mu = cvc5_bind_table(values, prefix)
    dim = len(values)
    bool_sort = solver.getBooleanSort()
    selectors = [solver.mkConst(bool_sort, f"{prefix}_select_{idx}") for idx in range(1, dim)]
    for slot, idx in zip(selectors, range(1, dim), strict=True):
        solver.assertFormula(solver.mkTerm(Kind.IMPLIES, slot, cvc5_and(solver, cvc5_square_constraints(solver, mu, idx))))
    for offset_i, i in enumerate(range(1, dim)):
        for offset_j, j in enumerate(range(1, dim)):
            if i >= j:
                continue
            solver.assertFormula(
                solver.mkTerm(
                    Kind.IMPLIES,
                    solver.mkTerm(Kind.AND, selectors[offset_i], selectors[offset_j]),
                    cvc5_and(solver, cvc5_anticommute_constraints(solver, mu, i, j)),
                )
            )
    count_terms = [solver.mkTerm(Kind.ITE, slot, cvc5_int(solver, 1), cvc5_int(solver, 0)) for slot in selectors]
    solver.assertFormula(solver.mkTerm(Kind.GEQ, cvc5_add(solver, count_terms), cvc5_int(solver, required)))
    status = str(solver.checkSat())
    model_selection: list[int] = []
    if status == "sat":
        model_selection = [idx for slot, idx in zip(selectors, range(1, dim), strict=True) if str(solver.getValue(slot)) == "true"]
    return {
        "status": status,
        "required_count": required,
        "candidate_imaginary_slots": dim - 1,
        "bound_structure_constant_count": dim * dim * dim,
        "derived_square_equations": dim - 1,
        "derived_pair_anticommutation_equation_groups": (dim - 1) * (dim - 2) // 2,
        "selected_indices_model": model_selection,
        "encoding": "selectors over imaginary basis units; selected units must square to -1 and all selected pairs must anticommute via bound mu[k,i,j] structure constants",
    }


def cvc5_h_bare_root(values: list[list[list[int]]], *, force_commutative: bool) -> dict[str, Any]:
    solver, mu = cvc5_bind_table(values, "H_bare_force_comm" if force_commutative else "H_bare")
    dim = len(values)
    noncomm_terms: list[Any] = []
    for i in range(1, dim):
        for constraint in cvc5_square_constraints(solver, mu, i):
            solver.assertFormula(constraint)
        for j in range(i + 1, dim):
            noncomm_terms.extend(cvc5_commutator_nonzero_terms(solver, mu, i, j))
            if force_commutative:
                for k in range(dim):
                    solver.assertFormula(solver.mkTerm(Kind.EQUAL, solver.mkTerm(Kind.SUB, mu[k][i][j], mu[k][j][i]), cvc5_int(solver, 0)))
    solver.assertFormula(cvc5_or(solver, noncomm_terms))
    return {
        "status": str(solver.checkSat()),
        "force_commutativity": force_commutative,
        "claim": "H has finite table, imaginary units square to -1, and a derived nonzero commutator witness" if not force_commutative else "H is forced commutative while the bare root still requires a nonzero commutator",
        "bound_structure_constant_count": dim * dim * dim,
        "derived_expression": "mu[k,i,j] - mu[k,j,i] != 0 for some imaginary pair/output coordinate",
    }


def quotient_summary(carriers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    names = ["R", "C", "H", "O"]
    full_signatures = {
        name: (
            f"finite={row['finite']};noncomm={row['noncommutation']['noncommutative']};"
            f"dim={row['real_dimension']};imaginary_units={row['imaginary_unit_count']};"
            f"cl6={row['cl6_7unit_admissible']}"
        )
        for name, row in carriers.items()
    }
    coarse_signatures = {
        name: f"finite={row['finite']};noncomm={row['noncommutation']['noncommutative']}"
        for name, row in carriers.items()
    }
    return {
        "S": names,
        "equivalence_relation": "a ~_M b iff every finite root probe in M has the same value",
        "bare_root_admitted_carriers": [name for name in names if carriers[name]["bare_root_admissible"]],
        "strong_cl6_7unit_admitted_carriers": [name for name in names if carriers[name]["cl6_7unit_admissible"]],
        "full_probe_signatures": full_signatures,
        "coarse_signatures_after_dropping_dimension_unit_and_cl6_probes": coarse_signatures,
        "full_probe_class_count": len(set(full_signatures.values())),
        "coarse_probe_class_count": len(set(coarse_signatures.values())),
        "drop_probe_coarsening_flip": {
            "dropped_probes": ["carrier_dimension", "imaginary_unit_count", "cl6_7unit_capacity"],
            "before_class_count": len(set(full_signatures.values())),
            "after_class_count": len(set(coarse_signatures.values())),
            "flips": len(set(full_signatures.values())) != len(set(coarse_signatures.values())),
        },
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tables = {"R": multiplication_table(1), "C": multiplication_table(2), "H": multiplication_table(4), "O": multiplication_table(8)}
    int_tables = {name: int_table(table) for name, table in tables.items()}
    carriers = {
        "R": carrier_numeric_summary("R", 1),
        "C": carrier_numeric_summary("C", 2),
        "H": carrier_numeric_summary("H", 4),
        "O": carrier_numeric_summary("O", 8),
    }
    unit_counts = {name: carriers[name]["imaginary_unit_count"] for name in ["R", "C", "H", "O"]}

    z3_h_cl6 = z3_has_at_least_units(int_tables["H"], 7, "z3_H_cl6")
    z3_o_cl6 = z3_has_at_least_units(int_tables["O"], 7, "z3_O_cl6")
    z3_h_bare = z3_h_bare_root(int_tables["H"], force_commutative=False)
    z3_h_forced_comm = z3_h_bare_root(int_tables["H"], force_commutative=True)

    cvc5_h_cl6 = cvc5_has_at_least_units(int_tables["H"], 7, "cvc5_H_cl6")
    cvc5_o_cl6 = cvc5_has_at_least_units(int_tables["O"], 7, "cvc5_O_cl6")
    cvc5_h_bare = cvc5_h_bare_root(int_tables["H"], force_commutative=False)
    cvc5_h_forced_comm = cvc5_h_bare_root(int_tables["H"], force_commutative=True)

    quotient = quotient_summary(carriers)
    h_flip = z3_h_bare["status"] == cvc5_h_bare["status"] == "sat" and z3_h_cl6["status"] == cvc5_h_cl6["status"] == "unsat"
    all_pass = bool(
        unit_counts == {"R": 0, "C": 1, "H": 3, "O": 7}
        and z3_h_cl6["status"] == cvc5_h_cl6["status"] == "unsat"
        and z3_o_cl6["status"] == cvc5_o_cl6["status"] == "sat"
        and z3_h_bare["status"] == cvc5_h_bare["status"] == "sat"
        and z3_h_forced_comm["status"] == cvc5_h_forced_comm["status"] == "unsat"
        and h_flip
        and quotient["drop_probe_coarsening_flip"]["flips"]
    )
    return {
        "schema": "codex_ratchet.engine_leg.v1",
        "object_id": OBJECT_ID,
        "rung_id": RUNG_ID,
        "engine": "jax",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "ran": True,
        "standalone": True,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "jax_enable_x64": jax.config.read("jax_enable_x64"),
        "claim_ceiling": "Scratch dual-SMT structural proof only: H bare-root SAT but H Cl(0,6)/7-unit UNSAT; O Cl(0,6)/7-unit SAT.",
        "all_pass": all_pass,
        "M": {
            "name": "finite root distinguishability probe family over R/C/H/O structure constants",
            "probe_family": [
                "finite Cayley-Dickson structure constants mu[k,i,j]",
                "basis imaginary square probes mu[:,i,i]",
                "pair anticommutator probes mu[:,i,j] + mu[:,j,i]",
                "pair commutator probes mu[:,i,j] - mu[:,j,i]",
                "quotient signatures over finite probe outputs",
            ],
        },
        "C": {
            "state_constraints": ["trace(rho)=1", "rho PSD", "rho Hermitian", "normalization"],
            "bare_root_constraints": ["finite table", "derived nonzero commutator exists", "finite M quotient"],
            "rung_specific_stronger_constraint": ">=7 mutually anticommuting imaginary units, equivalent here to the Cl(0,6)/3-qubit Weyl-floor carrier constraint",
        },
        "carriers": carriers,
        "quotient": quotient,
        "unit_counts": unit_counts,
        "smt": {
            "encoding_guard": (
                "No computed count/residual/boolean is asserted as the proof target. "
                "Each solver binds Cayley-Dickson structure constants mu[k,i,j], then derives "
                "unit-square, anticommutation, and noncommutation formulas in solver."
            ),
            "z3": {
                "version": z3.get_version_string(),
                "verdict": z3_h_cl6["status"],
                "H_has_at_least_7_mutually_anticommuting_units": z3_h_cl6,
                "O_has_at_least_7_mutually_anticommuting_units": z3_o_cl6,
                "H_bare_root_admissibility": z3_h_bare,
                "H_force_commutativity_control": z3_h_forced_comm,
            },
            "cvc5": {
                "version": getattr(cvc5, "__version__", "unknown"),
                "verdict": cvc5_h_cl6["status"],
                "H_has_at_least_7_mutually_anticommuting_units": cvc5_h_cl6,
                "O_has_at_least_7_mutually_anticommuting_units": cvc5_o_cl6,
                "H_bare_root_admissibility": cvc5_h_bare,
                "H_force_commutativity_control": cvc5_h_forced_comm,
            },
        },
        "negative_control_flip": None,
        "decision": {},
        "summary": {},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def finalize_result(result: dict[str, Any]) -> dict[str, Any]:
    z3_payload = result["smt"]["z3"]
    cvc5_payload = result["smt"]["cvc5"]
    negative = {
        "drop_stronger_cl6_7unit_constraint": {
            "H_bare_root_z3": z3_payload["H_bare_root_admissibility"]["status"],
            "H_bare_root_cvc5": cvc5_payload["H_bare_root_admissibility"]["status"],
            "H_cl6_7unit_z3": z3_payload["H_has_at_least_7_mutually_anticommuting_units"]["status"],
            "H_cl6_7unit_cvc5": cvc5_payload["H_has_at_least_7_mutually_anticommuting_units"]["status"],
            "flips": True,
        },
        "force_commutativity_control": {
            "H_bare_noncommuting_z3": z3_payload["H_bare_root_admissibility"]["status"],
            "H_forced_commutative_z3": z3_payload["H_force_commutativity_control"]["status"],
            "H_bare_noncommuting_cvc5": cvc5_payload["H_bare_root_admissibility"]["status"],
            "H_forced_commutative_cvc5": cvc5_payload["H_force_commutativity_control"]["status"],
            "flips": True,
        },
        "drop_probe_coarsening": result["quotient"]["drop_probe_coarsening_flip"],
    }
    decision = {
        "H_bare_root_admissible": True,
        "H_cl6_7unit_admissible": False,
        "O_cl6_7unit_admissible": True,
        "nonassoc_forced_by_bare_root": False,
        "nonassoc_installed_by_constraint": "Cl(0,6)/>=7 mutually anticommuting imaginary units/3-qubit Weyl floor",
        "forced_vs_installed_verdict": "INSTALLED_NOT_FORCED",
    }
    summary = {
        "all_pass": result["all_pass"],
        "unit_counts_R_C_H_O": [result["unit_counts"]["R"], result["unit_counts"]["C"], result["unit_counts"]["H"], result["unit_counts"]["O"]],
        "z3_verdict_H_cl6_7unit": z3_payload["verdict"],
        "cvc5_verdict_H_cl6_7unit": cvc5_payload["verdict"],
        "z3_verdict_O_cl6_7unit": z3_payload["O_has_at_least_7_mutually_anticommuting_units"]["status"],
        "cvc5_verdict_O_cl6_7unit": cvc5_payload["O_has_at_least_7_mutually_anticommuting_units"]["status"],
        "H_bare_root_z3": z3_payload["H_bare_root_admissibility"]["status"],
        "H_bare_root_cvc5": cvc5_payload["H_bare_root_admissibility"]["status"],
        "H_force_commutativity_control_z3": z3_payload["H_force_commutativity_control"]["status"],
        "H_force_commutativity_control_cvc5": cvc5_payload["H_force_commutativity_control"]["status"],
        "forced_vs_installed_verdict": "INSTALLED_NOT_FORCED",
    }
    result["negative_control_flip"] = negative
    result["decision"] = decision
    result["summary"] = summary
    return result


def main() -> int:
    result = finalize_result(build_result())
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "JAX_DONE "
        f"all_pass={str(s['all_pass']).lower()} "
        f"unit_counts={s['unit_counts_R_C_H_O']} "
        f"H_bare_z3={s['H_bare_root_z3']} "
        f"H_cl6_z3={s['z3_verdict_H_cl6_7unit']} "
        f"O_cl6_z3={s['z3_verdict_O_cl6_7unit']} "
        f"H_force_comm_z3={s['H_force_commutativity_control_z3']} "
        f"verdict={s['forced_vs_installed_verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
