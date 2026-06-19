#!/usr/bin/env python3
"""JAX + z3/cvc5 v2 leg for the octonion-left-action Cl(0,6) foundation rung."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
import jax.numpy as jnp
import z3
from cvc5 import Kind


OBJECT_ID = "foundation_r3_octonion_cl6_link_xhigh"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_octonion_cl6_link_xhigh_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_octonion_cl6_link_xhigh_jax_results.json"
TOL = 1.0e-9


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


def left_matrix(dim: int, unit_idx: int) -> jax.Array:
    e = basis(dim, unit_idx)
    return jnp.stack([cd_mul(e, basis(dim, col)) for col in range(dim)], axis=1)


def left_matrices(dim: int) -> list[jax.Array]:
    return [left_matrix(dim, idx) for idx in range(1, dim)]


def matrix_entry_table(mats: list[jax.Array]) -> list[list[list[int]]]:
    return [
        [[py_int(mat[row, col]) for col in range(int(mat.shape[1]))] for row in range(int(mat.shape[0]))]
        for mat in mats
    ]


def rank_from_columns(cols: list[jax.Array]) -> dict[str, Any]:
    mat = jnp.stack(cols, axis=1)
    singular = jnp.linalg.svd(mat, compute_uv=False)
    max_s = py_float(jnp.max(singular)) if singular.size else 0.0
    tol = max(mat.shape) * jnp.finfo(jnp.float64).eps * max_s * 100.0
    rank = int(jax.device_get(jnp.sum(singular > tol)))
    return {"rank": rank, "rank_tol": float(tol)}


def generated_rank(mats: list[jax.Array], generator_count: int) -> dict[str, Any]:
    dim = int(mats[0].shape[0])
    cols: list[jax.Array] = []
    for mask in range(2**generator_count):
        acc = jnp.eye(dim, dtype=jnp.float64)
        for idx in range(generator_count):
            if (mask >> idx) & 1:
                acc = acc @ mats[idx]
        cols.append(jnp.reshape(acc, (-1,)))
    report = rank_from_columns(cols)
    report.update({"generator_count": generator_count, "word_count": len(cols)})
    return report


def anticommutation_tensor(mats: list[jax.Array], self_sign: float = -2.0) -> jax.Array:
    dim = int(mats[0].shape[0])
    rows: list[jax.Array] = []
    for i, left in enumerate(mats):
        for j, right in enumerate(mats):
            target = self_sign * jnp.eye(dim, dtype=jnp.float64) if i == j else jnp.zeros((dim, dim), dtype=jnp.float64)
            rows.append(jnp.reshape(left @ right + right @ left - target, (-1,)))
    return jnp.concatenate(rows)


def anticommutation_report(mats: list[jax.Array]) -> dict[str, Any]:
    residual = anticommutation_tensor(mats, self_sign=-2.0)
    return {
        "relation": "L_i L_j + L_j L_i = -2 delta_ij I",
        "max_abs_residual": py_float(jnp.max(jnp.abs(residual))),
        "l2_residual": py_float(jnp.linalg.norm(residual)),
        "entry_count": int(residual.shape[0]),
        "pass": py_float(jnp.max(jnp.abs(residual))) <= TOL,
    }


def skew_report(mats: list[jax.Array]) -> dict[str, Any]:
    residuals = [py_float(jnp.linalg.norm(mat.T + mat)) for mat in mats]
    return {"max_residual": max(residuals), "per_generator_residuals": residuals, "pass": max(residuals) <= TOL}


def pseudoscalar_link_report(o_mats: list[jax.Array]) -> dict[str, Any]:
    product = jnp.eye(8, dtype=jnp.float64)
    for idx in range(6):
        product = product @ o_mats[idx]
    plus_residual = py_float(jnp.linalg.norm(product - o_mats[6]))
    minus_residual = py_float(jnp.linalg.norm(product + o_mats[6]))
    return {
        "relation": "L_e1 L_e2 L_e3 L_e4 L_e5 L_e6 = L_e7 under this Cayley-Dickson orientation",
        "plus_residual": plus_residual,
        "minus_residual": minus_residual,
        "pass": plus_residual <= TOL,
    }


ProofMode = Literal[
    "correct_all_violation",
    "offdiag_violation",
    "self_square_violation",
    "wrong_sign_violation",
    "single_offdiag_violation",
]


def z3_real_from_int(value: int) -> z3.ArithRef:
    return z3.RealVal(str(value))


def z3_bound_entries(values: list[list[list[int]]], bind_entries: bool) -> tuple[z3.Solver, list[list[list[z3.ArithRef]]]]:
    solver = z3.Solver()
    solver.set(timeout=20_000)
    entries = [
        [[z3.Real(f"L_{i}_{row}_{col}") for col in range(8)] for row in range(8)]
        for i in range(7)
    ]
    if bind_entries:
        for i in range(7):
            for row in range(8):
                for col in range(8):
                    solver.add(entries[i][row][col] == z3_real_from_int(values[i][row][col]))
    return solver, entries


def z3_anticommutator_entry(entries: list[list[list[z3.ArithRef]]], i: int, j: int, row: int, col: int) -> z3.ArithRef:
    return z3.Sum(
        [
            entries[i][row][k] * entries[j][k][col] + entries[j][row][k] * entries[i][k][col]
            for k in range(8)
        ]
    )


def z3_violation_terms(entries: list[list[list[z3.ArithRef]]], mode: ProofMode) -> list[z3.BoolRef]:
    terms: list[z3.BoolRef] = []
    if mode == "single_offdiag_violation":
        anti = z3_anticommutator_entry(entries, 0, 1, 0, 0)
        return [anti != z3_real_from_int(0)]
    for i in range(7):
        for j in range(7):
            if mode == "offdiag_violation" and i == j:
                continue
            if mode in {"self_square_violation", "wrong_sign_violation"} and i != j:
                continue
            for row in range(8):
                for col in range(8):
                    anti = z3_anticommutator_entry(entries, i, j, row, col)
                    if i == j:
                        sign = 2 if mode == "wrong_sign_violation" else -2
                        target = sign if row == col else 0
                    else:
                        target = 0
                    terms.append(anti != z3_real_from_int(target))
    return terms


def z3_status(values: list[list[list[int]]], *, bind_entries: bool, mode: ProofMode) -> dict[str, Any]:
    solver, entries = z3_bound_entries(values, bind_entries)
    solver.add(z3.Or(z3_violation_terms(entries, mode)))
    return {
        "status": str(solver.check()),
        "mode": mode,
        "binds_L_entries": bind_entries,
        "sort": "Real",
        "bound_entry_count": 7 * 8 * 8 if bind_entries else 0,
        "derived_expression": "sum_c(L_i[a,c]*L_j[c,b] + L_j[a,c]*L_i[c,b])",
    }


def cvc5_real_from_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkReal(str(value))


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_real_from_int(solver, 0)
    acc = terms[0]
    for term in terms[1:]:
        acc = solver.mkTerm(Kind.ADD, acc, term)
    return acc


def cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if len(terms) == 1:
        return terms[0]
    acc = terms[0]
    for term in terms[1:]:
        acc = solver.mkTerm(Kind.OR, acc, term)
    return acc


def cvc5_bound_entries(values: list[list[list[int]]], bind_entries: bool) -> tuple[cvc5.Solver, list[list[list[Any]]]]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    solver.setOption("produce-models", "true")
    solver.setOption("tlimit-per", "20000")
    real_sort = solver.getRealSort()
    entries = [
        [[solver.mkConst(real_sort, f"L_{i}_{row}_{col}") for col in range(8)] for row in range(8)]
        for i in range(7)
    ]
    if bind_entries:
        for i in range(7):
            for row in range(8):
                for col in range(8):
                    solver.assertFormula(solver.mkTerm(Kind.EQUAL, entries[i][row][col], cvc5_real_from_int(solver, values[i][row][col])))
    return solver, entries


def cvc5_anticommutator_entry(solver: cvc5.Solver, entries: list[list[list[Any]]], i: int, j: int, row: int, col: int) -> Any:
    return cvc5_sum(
        solver,
        [
            solver.mkTerm(
                Kind.ADD,
                solver.mkTerm(Kind.MULT, entries[i][row][k], entries[j][k][col]),
                solver.mkTerm(Kind.MULT, entries[j][row][k], entries[i][k][col]),
            )
            for k in range(8)
        ],
    )


def cvc5_violation_terms(solver: cvc5.Solver, entries: list[list[list[Any]]], mode: ProofMode) -> list[Any]:
    terms: list[Any] = []
    if mode == "single_offdiag_violation":
        anti = cvc5_anticommutator_entry(solver, entries, 0, 1, 0, 0)
        eq = solver.mkTerm(Kind.EQUAL, anti, cvc5_real_from_int(solver, 0))
        return [solver.mkTerm(Kind.NOT, eq)]
    for i in range(7):
        for j in range(7):
            if mode == "offdiag_violation" and i == j:
                continue
            if mode in {"self_square_violation", "wrong_sign_violation"} and i != j:
                continue
            for row in range(8):
                for col in range(8):
                    anti = cvc5_anticommutator_entry(solver, entries, i, j, row, col)
                    if i == j:
                        sign = 2 if mode == "wrong_sign_violation" else -2
                        target = sign if row == col else 0
                    else:
                        target = 0
                    eq = solver.mkTerm(Kind.EQUAL, anti, cvc5_real_from_int(solver, target))
                    terms.append(solver.mkTerm(Kind.NOT, eq))
    return terms


def cvc5_status(values: list[list[list[int]]], *, bind_entries: bool, mode: ProofMode) -> dict[str, Any]:
    solver, entries = cvc5_bound_entries(values, bind_entries)
    solver.assertFormula(cvc5_or(solver, cvc5_violation_terms(solver, entries, mode)))
    return {
        "status": str(solver.checkSat()),
        "mode": mode,
        "binds_L_entries": bind_entries,
        "sort": "Real",
        "bound_entry_count": 7 * 8 * 8 if bind_entries else 0,
        "derived_expression": "sum_c(L_i[a,c]*L_j[c,b] + L_j[a,c]*L_i[c,b])",
    }


def smt_proofs(o_mats: list[jax.Array]) -> dict[str, Any]:
    values = matrix_entry_table(o_mats)
    z3_correct = z3_status(values, bind_entries=True, mode="correct_all_violation")
    z3_offdiag = z3_status(values, bind_entries=True, mode="offdiag_violation")
    z3_self = z3_status(values, bind_entries=True, mode="self_square_violation")
    z3_erased = z3_status(values, bind_entries=False, mode="single_offdiag_violation")
    z3_wrong = z3_status(values, bind_entries=True, mode="wrong_sign_violation")

    cvc5_correct = cvc5_status(values, bind_entries=True, mode="correct_all_violation")
    cvc5_offdiag = cvc5_status(values, bind_entries=True, mode="offdiag_violation")
    cvc5_self = cvc5_status(values, bind_entries=True, mode="self_square_violation")
    cvc5_erased = cvc5_status(values, bind_entries=False, mode="single_offdiag_violation")
    cvc5_wrong = cvc5_status(values, bind_entries=True, mode="wrong_sign_violation")

    return {
        "encoding": (
            "v2 non-decorative SMT: bind all 7 computed octonion left-multiplication "
            "8x8 matrix entries as SMT Reals, then derive each anticommutator entry "
            "inside the solver as sum_c(L_i[a,c]*L_j[c,b] + L_j[a,c]*L_i[c,b]). "
            "The main verdict asserts existence of a Clifford-relation violation and is UNSAT."
        ),
        "forbidden_pattern_guard": "No precomputed residual/count/boolean is asserted to either solver; only L-entry bindings and in-solver matrix products are used.",
        "L_entry_count": 7 * 8 * 8,
        "derived_anticommutator_entry_count": 7 * 7 * 8 * 8,
        "z3": {
            "version": z3.get_version_string(),
            "verdict": z3_correct["status"],
            "correct_relation_violation": z3_correct,
            "offdiag_pair_violation": z3_offdiag,
            "self_square_violation": z3_self,
            "erase_L_entry_binding_flip": z3_erased,
            "wrong_sign_plus_I_violation_control": z3_wrong,
            "pass": z3_correct["status"] == "unsat"
            and z3_offdiag["status"] == "unsat"
            and z3_self["status"] == "unsat"
            and z3_erased["status"] == "sat"
            and z3_wrong["status"] == "sat",
        },
        "cvc5": {
            "version": getattr(cvc5, "__version__", "unknown"),
            "verdict": cvc5_correct["status"],
            "correct_relation_violation": cvc5_correct,
            "offdiag_pair_violation": cvc5_offdiag,
            "self_square_violation": cvc5_self,
            "erase_L_entry_binding_flip": cvc5_erased,
            "wrong_sign_plus_I_violation_control": cvc5_wrong,
            "pass": cvc5_correct["status"] == "unsat"
            and cvc5_offdiag["status"] == "unsat"
            and cvc5_self["status"] == "unsat"
            and cvc5_erased["status"] == "sat"
            and cvc5_wrong["status"] == "sat",
        },
    }


def quotient_report(o_rank: dict[str, Any], h_rank: dict[str, Any], o_anti: dict[str, Any], h_anti: dict[str, Any]) -> dict[str, Any]:
    full_signatures = {
        "octonion_left_action_on_O": f"O:generators=7;carrier_dim=8;rank={o_rank['rank']};spinor_dim=8;anticommutes={o_anti['pass']}",
        "quaternion_left_action_control_on_H": f"H:generators=3;carrier_dim=4;rank={h_rank['rank']};spinor_dim=2;anticommutes={h_anti['pass']}",
    }
    coarse_signatures = {
        "octonion_left_action_on_O": f"skew=True;anticommutes={o_anti['pass']}",
        "quaternion_left_action_control_on_H": f"skew=True;anticommutes={h_anti['pass']}",
    }
    full_count = len(set(full_signatures.values()))
    coarse_count = len(set(coarse_signatures.values()))
    return {
        "S": ["octonion_left_action_on_O", "quaternion_left_action_control_on_H"],
        "equivalence_relation": "x ~_M y iff all finite M probes match: generator count, carrier dimension, anticommutation signature, generated Clifford rank, and spinor dimension",
        "full_probe_signatures": full_signatures,
        "coarse_probe_signatures_after_dropping_dimension_and_rank": coarse_signatures,
        "full_probe_class_count": full_count,
        "drop_dimension_and_rank_probe_class_count": coarse_count,
        "octonion_class": {"label": "Cl(0,6)_spinor_from_O_left_multiplication", "generated_rank": o_rank["rank"], "spinor_dim": 8},
        "quaternion_control_class": {"label": "Cl(0,2)_control_from_H_left_multiplication", "generated_rank": h_rank["rank"], "spinor_dim": 2},
        "coarsening_flip": {
            "dropped_probe": "carrier dimension + generated Clifford rank",
            "before_class_count": full_count,
            "after_class_count": coarse_count,
            "flips": full_count != coarse_count,
        },
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    o_mats = left_matrices(8)
    h_mats = left_matrices(4)

    o_skew = skew_report(o_mats)
    h_skew = skew_report(h_mats)
    o_anti = anticommutation_report(o_mats)
    h_anti = anticommutation_report(h_mats)
    o_rank6 = generated_rank(o_mats, 6)
    o_rank7 = generated_rank(o_mats, 7)
    h_rank2 = generated_rank(h_mats, 2)
    h_rank3 = generated_rank(h_mats, 3)
    pseudoscalar_link = pseudoscalar_link_report(o_mats)
    smt = smt_proofs(o_mats)
    quotient = quotient_report(o_rank6, h_rank2, o_anti, h_anti)

    all_pass = bool(
        o_skew["pass"]
        and h_skew["pass"]
        and o_anti["pass"]
        and h_anti["pass"]
        and o_rank6["rank"] == 64
        and o_rank7["rank"] == 64
        and h_rank2["rank"] == 4
        and h_rank3["rank"] == 4
        and pseudoscalar_link["pass"]
        and smt["z3"]["pass"]
        and smt["cvc5"]["pass"]
        and smt["z3"]["verdict"] == smt["cvc5"]["verdict"] == "unsat"
        and quotient["coarsening_flip"]["flips"]
    )

    return {
        "schema": "codex_ratchet.engine_leg.v1",
        "object_id": OBJECT_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "Scratch JAX + dual-SMT v2 leg for octonion left-action Cl(0,6) link only; no promotion/admission.",
        "engine": "jax",
        "ran": True,
        "standalone": True,
        "reads_peer_result": False,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "M": {
            "probe_family": "finite octonion left-multiplication observables and anticommutator matrix entries",
            "operators": [f"L_e{idx}" for idx in range(1, 8)],
            "probe_entries": "<basis_a | (L_ei L_ej + L_ej L_ei) | basis_b> for i,j=1..7 and a,b=1..8",
            "pair_probe_count": 49,
            "entry_probe_count": 49 * 8 * 8,
            "quotient_discriminators": ["generator_count", "carrier_dimension", "anticommutation_signature", "generated_clifford_rank", "spinor_dimension"],
        },
        "C": {
            "state_constraints": ["trace(rho)=1", "rho PSD", "rho Hermitian", "normalization"],
            "rung_specific_constraints": [
                "Cayley-Dickson octonion multiplication table",
                "L_ei^T = -L_ei",
                "L_ei L_ej + L_ej L_ei = -2 delta_ij I",
                "first six L_ei generate a 64-dimensional Cl(0,6) carrier on an 8-dimensional spinor",
            ],
        },
        "quotient": quotient,
        "octonion_left_action": {
            "carrier_real_dimension": 8,
            "generator_count": 7,
            "skew": o_skew,
            "anticommutation": o_anti,
            "generated_rank_first_six": o_rank6,
            "generated_rank_all_seven_matrix_image": o_rank7,
            "spinor_dim": 8,
            "pseudoscalar_link": pseudoscalar_link,
        },
        "quaternion_control": {
            "carrier_real_dimension": 4,
            "generator_count": 3,
            "skew": h_skew,
            "anticommutation": h_anti,
            "generated_rank_first_two": h_rank2,
            "generated_rank_all_three_matrix_image": h_rank3,
            "spinor_dim": 2,
            "control_result": "Cl(0,2) rank 4 / spinor 2, not Cl(0,6) rank 64 / spinor 8",
        },
        "smt": smt,
        "negative_controls": {
            "quaternion_H_control": {
                "octonion_rank": o_rank6["rank"],
                "quaternion_rank": h_rank2["rank"],
                "octonion_spinor_dim": 8,
                "quaternion_spinor_dim": 2,
                "flips": o_rank6["rank"] != h_rank2["rank"],
            },
            "drop_dimension_and_rank_probe": quotient["coarsening_flip"],
            "smt_erase_L_entry_binding_flip": {
                "z3_with_L_entry_bindings": smt["z3"]["verdict"],
                "z3_after_erasing_L_entry_bindings": smt["z3"]["erase_L_entry_binding_flip"]["status"],
                "cvc5_with_L_entry_bindings": smt["cvc5"]["verdict"],
                "cvc5_after_erasing_L_entry_bindings": smt["cvc5"]["erase_L_entry_binding_flip"]["status"],
                "flips": smt["z3"]["verdict"] != smt["z3"]["erase_L_entry_binding_flip"]["status"]
                and smt["cvc5"]["verdict"] != smt["cvc5"]["erase_L_entry_binding_flip"]["status"],
            },
            "wrong_sign_plus_I_control": {
                "z3_violation_verdict": smt["z3"]["wrong_sign_plus_I_violation_control"]["status"],
                "cvc5_violation_verdict": smt["cvc5"]["wrong_sign_plus_I_violation_control"]["status"],
                "flips_against_correct_violation": smt["z3"]["verdict"] != smt["z3"]["wrong_sign_plus_I_violation_control"]["status"]
                and smt["cvc5"]["verdict"] != smt["cvc5"]["wrong_sign_plus_I_violation_control"]["status"],
            },
        },
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": {
            "z3": {"tried": True, "used": True, "reason": "load-bearing in-solver derivation of all octonion L-entry anticommutator products"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT mirror of the same Real-valued in-solver matrix-product proof"},
            "jax": {"tried": True, "used": True, "reason": "supportive x64 Cayley-Dickson table and finite matrix construction"},
            "jax.numpy": {"tried": True, "used": True, "reason": "supportive x64 array substrate for computed operator entries"},
            "json": {"tried": True, "used": True, "reason": "supportive result serialization"},
            "hashlib": {"tried": True, "used": True, "reason": "supportive source hash"},
            "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic paths"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "jax": "supportive",
            "jax.numpy": "supportive",
            "json": "supportive",
            "hashlib": "supportive",
            "pathlib": "supportive",
        },
        "summary": {
            "octonion_cl6_rank": o_rank6["rank"],
            "octonion_all7_matrix_rank": o_rank7["rank"],
            "octonion_spinor_dim": 8,
            "quaternion_cl2_rank": h_rank2["rank"],
            "quaternion_all3_matrix_rank": h_rank3["rank"],
            "quaternion_spinor_dim": 2,
            "octonion_anticommutation_max_residual": o_anti["max_abs_residual"],
            "quaternion_anticommutation_max_residual": h_anti["max_abs_residual"],
            "pseudoscalar_link_plus_residual": pseudoscalar_link["plus_residual"],
            "full_quotient_class_count": quotient["full_probe_class_count"],
            "coarse_quotient_class_count": quotient["drop_dimension_and_rank_probe_class_count"],
            "z3_verdict": smt["z3"]["verdict"],
            "z3_offdiag_violation": smt["z3"]["offdiag_pair_violation"]["status"],
            "z3_self_square_violation": smt["z3"]["self_square_violation"]["status"],
            "z3_erased_status": smt["z3"]["erase_L_entry_binding_flip"]["status"],
            "z3_wrong_sign_control": smt["z3"]["wrong_sign_plus_I_violation_control"]["status"],
            "cvc5_verdict": smt["cvc5"]["verdict"],
            "cvc5_offdiag_violation": smt["cvc5"]["offdiag_pair_violation"]["status"],
            "cvc5_self_square_violation": smt["cvc5"]["self_square_violation"]["status"],
            "cvc5_erased_status": smt["cvc5"]["erase_L_entry_binding_flip"]["status"],
            "cvc5_wrong_sign_control": smt["cvc5"]["wrong_sign_plus_I_violation_control"]["status"],
            "all_pass": all_pass,
        },
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"octonion_cl6_rank={result['summary']['octonion_cl6_rank']} "
        f"quaternion_cl2_rank={result['summary']['quaternion_cl2_rank']} "
        f"z3={result['summary']['z3_verdict']} "
        f"cvc5={result['summary']['cvc5_verdict']} "
        f"wrong_sign_z3={result['summary']['z3_wrong_sign_control']} "
        f"wrong_sign_cvc5={result['summary']['cvc5_wrong_sign_control']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
