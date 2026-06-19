#!/usr/bin/env python3
"""JAX leg for foundation_nested_hopf_weyl_signed_cut_ratchet."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import z3


PIN_SPEC = """object_id=foundation_nested_hopf_weyl_signed_cut_ratchet
rung_count=3
eta_shells_rad=[eta_1=1.17,eta_2=0.86,eta_3=0.53] with eta_1 > eta_2 > eta_3 nested Hopf tori in S^3
stacking_order=Stack_r = Phi_r after Phi_{r-1} after ... after Phi_1; adjacent order test compares Phi_r after Phi_{r+1} vs Phi_{r+1} after Phi_r on rho_probe=rho_2
constraint_filters_left_sheet=K_1=[[1,0],[0,-1]], K_2=[[1,1],[1,-1]], K_3=[[1,1],[0,1]], Phi_r(rho)=normalize((K_r kron I_R) rho (K_r kron I_R)^adjoint)
rho_family=rho_r=|psi_r><psi_r|, |psi_r>=cos(theta_r)|L0 R0>+sin(theta_r)|L1 R1>, theta_r=0.70*(r-1)/2 for r=1,2,3
separable_control=rho_sep_r=diag(cos(theta_r)^2,sin(theta_r)^2)_L kron diag(cos(theta_r)^2,sin(theta_r)^2)_R
cut=A|B is Weyl-L sheet vs Weyl-R sheet
entropy_log_base=e
probe_sets=M_1=[Z_L Z_R]; M_2=M_1+[X_L X_R]; M_3=M_2+[Z_L,Z_R,Y_L Y_R]
claim_ceiling=scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false; feeds Xi/Axis-0 bridge problem but does not close bridge, Axis0, manifold, or M(C)
"""

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "foundation_nested_hopf_weyl_signed_cut_ratchet"
ENGINE = "jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_nested_hopf_weyl_signed_cut_ratchet_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
KAPPA = 0.70
TOL = 1.0e-9

SOURCE_DEPENDENCIES = [
    ROOT / "system_v5/julia_carrier/clifford_torus_nested_hopf_foliation.jl",
    ROOT / "system_v5/julia_carrier/jax_clifford_torus_nested_hopf_foliation.py",
    ROOT / "system_v5/julia_carrier/weyl_sheet_pair_probe.jl",
    ROOT / "system_v5/julia_carrier/jax_weyl_sheet_pair_probe.py",
    ROOT / "system_v5/ops/formal_scouts/foundation_qit_operator_composition_mcp_jax.py",
]

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 runtime for local density, filter, entropy, quotient, and order-gap arithmetic; solver proofs gate the JAX claim path",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive array substrate for local matrix arithmetic; no numpy/scipy claim-path use",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing derive-in-solver UNSAT proof that bound rung-2 adjacent stacking matrices cannot commute",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent derive-in-solver check matching z3 on noncommuting and commuting-control matrices",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON, timestamp, path, and sha256 receipt logic",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_float(value: Any) -> float:
    return float(jax.device_get(value))


def py_bool(value: Any) -> bool:
    return bool(jax.device_get(value))


def mat_payload(matrix: jax.Array) -> list[list[float]]:
    rows: list[list[float]] = []
    for i in range(int(matrix.shape[0])):
        rows.append([py_float(jnp.real(matrix[i, j])) for j in range(int(matrix.shape[1]))])
    return rows


I2 = jnp.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
X = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
Y = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
Z = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
K_FILTERS = {
    1: Z,
    2: jnp.asarray([[1.0, 1.0], [1.0, -1.0]], dtype=jnp.complex128),
    3: jnp.asarray([[1.0, 1.0], [0.0, 1.0]], dtype=jnp.complex128),
}
COMMUTING_FILTERS = {
    1: jnp.asarray([[1.0, 0.0], [0.0, 0.80]], dtype=jnp.complex128),
    2: jnp.asarray([[1.0, 0.0], [0.0, 0.60]], dtype=jnp.complex128),
    3: jnp.asarray([[1.0, 0.0], [0.0, 0.40]], dtype=jnp.complex128),
}
ETA_SHELLS = {1: 1.17, 2: 0.86, 3: 0.53}


def theta(rung: int) -> jax.Array:
    return jnp.asarray(KAPPA * (rung - 1) / 2.0, dtype=jnp.float64)


def rho_for_rung(rung: int) -> jax.Array:
    th = theta(rung)
    psi = jnp.asarray([jnp.cos(th), 0.0, 0.0, jnp.sin(th)], dtype=jnp.complex128)
    return jnp.outer(psi, jnp.conj(psi))


def separable_rho_for_rung(rung: int) -> jax.Array:
    th = theta(rung)
    probs = jnp.asarray([jnp.cos(th) ** 2, jnp.sin(th) ** 2], dtype=jnp.float64)
    left = jnp.diag(probs).astype(jnp.complex128)
    right = jnp.diag(probs).astype(jnp.complex128)
    return jnp.kron(left, right)


def hermitize(rho: jax.Array) -> jax.Array:
    return 0.5 * (rho + jnp.conj(rho.T))


def trace_real(rho: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(rho))


def normalize_density(rho: jax.Array) -> jax.Array:
    herm = hermitize(rho)
    return herm / trace_real(herm)


def apply_filter(rho: jax.Array, filter_matrix: jax.Array) -> jax.Array:
    lifted = jnp.kron(filter_matrix, I2)
    return normalize_density(lifted @ rho @ jnp.conj(lifted.T))


def stack_state(rung: int, rho: jax.Array, filters: dict[int, jax.Array]) -> jax.Array:
    out = rho
    for idx in range(1, rung + 1):
        out = apply_filter(out, filters[idx])
    return out


def partial_trace_left_to_b(rho: jax.Array) -> jax.Array:
    shaped = rho.reshape((2, 2, 2, 2))
    return jnp.einsum("abac->bc", shaped)


def entropy_vn(rho: jax.Array) -> jax.Array:
    vals = jnp.linalg.eigvalsh(hermitize(rho))
    positive = vals > TOL
    safe = jnp.where(positive, vals, 1.0)
    return -jnp.sum(jnp.where(positive, vals * jnp.log(safe), 0.0))


def conditional_entropy(rho: jax.Array) -> jax.Array:
    return entropy_vn(rho) - entropy_vn(partial_trace_left_to_b(rho))


def entropy_components(rho: jax.Array) -> dict[str, float]:
    s_ab = entropy_vn(rho)
    s_b = entropy_vn(partial_trace_left_to_b(rho))
    return {"S_AB": py_float(s_ab), "S_B": py_float(s_b)}


def trace_norm_hermitian(matrix: jax.Array) -> jax.Array:
    return jnp.sum(jnp.abs(jnp.linalg.eigvalsh(hermitize(matrix))))


def order_gap(first: jax.Array, second: jax.Array, rho_probe: jax.Array) -> float:
    left = apply_filter(apply_filter(rho_probe, second), first)
    right = apply_filter(apply_filter(rho_probe, first), second)
    return py_float(trace_norm_hermitian(left - right))


def probe_ops() -> dict[str, jax.Array]:
    return {
        "Z_L Z_R": jnp.kron(Z, Z),
        "X_L X_R": jnp.kron(X, X),
        "Z_L": jnp.kron(Z, I2),
        "Z_R": jnp.kron(I2, Z),
        "Y_L Y_R": jnp.kron(Y, Y),
    }


def probe_family(rung: int) -> list[str]:
    if rung == 1:
        return ["Z_L Z_R"]
    if rung == 2:
        return ["Z_L Z_R", "X_L X_R"]
    return ["Z_L Z_R", "X_L X_R", "Z_L", "Z_R", "Y_L Y_R"]


def expectation(rho: jax.Array, op: jax.Array) -> float:
    return py_float(jnp.real(jnp.trace(op @ rho)))


def class_count(vectors: list[list[float]]) -> int:
    classes: list[list[float]] = []
    for vector in vectors:
        if not any(all(abs(a - b) <= 1.0e-8 for a, b in zip(vector, existing)) for existing in classes):
            classes.append(vector)
    return len(classes)


def quotient_report() -> dict[str, Any]:
    ops = probe_ops()
    rhos = [rho_for_rung(r) for r in (1, 2, 3)]
    report: dict[str, Any] = {}
    for rung in (1, 2, 3):
        family = probe_family(rung)
        vectors = [[expectation(rho, ops[name]) for name in family] for rho in rhos]
        report[f"M_{rung}"] = {
            "operators": family,
            "operator_count": len(family),
            "distinguishable_class_count": class_count(vectors),
            "expectation_vectors_by_rung": {str(idx + 1): vectors[idx] for idx in range(3)},
        }
    return report


def smt_matrices() -> tuple[list[list[int]], list[list[int]], list[list[int]], list[list[int]]]:
    noncommuting_a = [[1, 1], [1, -1]]
    noncommuting_b = [[1, 1], [0, 1]]
    commuting_a = [[1, 0], [0, 3]]
    commuting_b = [[2, 0], [0, 5]]
    return noncommuting_a, noncommuting_b, commuting_a, commuting_b


def z3_force_commute_status(a_values: list[list[int]], b_values: list[list[int]], label: str) -> dict[str, Any]:
    solver = z3.Solver()
    a = [[z3.Int(f"{label}_a_{i}_{j}") for j in range(2)] for i in range(2)]
    b = [[z3.Int(f"{label}_b_{i}_{j}") for j in range(2)] for i in range(2)]
    for i in range(2):
        for j in range(2):
            solver.add(a[i][j] == z3.IntVal(a_values[i][j]))
            solver.add(b[i][j] == z3.IntVal(b_values[i][j]))
    ab = [[sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
    ba = [[sum(b[i][k] * a[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
    for i in range(2):
        for j in range(2):
            solver.add(ab[i][j] == ba[i][j])
    status = solver.check()
    return {
        "solver": "z3",
        "level": "filter_level",
        "force_commute_verdict": str(status),
        "verdict": str(status),
        "bound_entries": 8,
        "derived_products": "AB and BA entries are computed inside z3 from bound matrix entries",
        "asserted_precomputed_scalar": False,
    }


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(int(value))


def cvc5_add(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_int(solver, 0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_mul(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.MULT, left, right)


def cvc5_status_text(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def z3_zero() -> Any:
    return z3.RealVal("0")


def z3_real(value: float | int) -> Any:
    return z3.RealVal(repr(float(value)))


def z3_sum(terms: list[Any]) -> Any:
    if not terms:
        return z3_zero()
    out = terms[0]
    for term in terms[1:]:
        out = out + term
    return out


def cvc5_real(solver: cvc5.Solver, value: float | int) -> Any:
    return solver.mkReal(repr(float(value)))


def cvc5_real_add(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_real(solver, 0.0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def z3_matmul(left: list[list[Any]], right: list[list[Any]]) -> list[list[Any]]:
    rows = len(left)
    inner = len(right)
    cols = len(right[0])
    return [[z3_sum([left[i][k] * right[k][j] for k in range(inner)]) for j in range(cols)] for i in range(rows)]


def cvc5_real_matmul(solver: cvc5.Solver, left: list[list[Any]], right: list[list[Any]]) -> list[list[Any]]:
    rows = len(left)
    inner = len(right)
    cols = len(right[0])
    return [
        [
            cvc5_real_add(solver, [solver.mkTerm(Kind.MULT, left[i][k], right[k][j]) for k in range(inner)])
            for j in range(cols)
        ]
        for i in range(rows)
    ]


def transpose_terms(matrix: list[list[Any]]) -> list[list[Any]]:
    return [[matrix[j][i] for j in range(len(matrix))] for i in range(len(matrix[0]))]


def z3_lift_left_filter(filter_terms: list[list[Any]]) -> list[list[Any]]:
    return [
        [filter_terms[row // 2][col // 2] if row % 2 == col % 2 else z3_zero() for col in range(4)]
        for row in range(4)
    ]


def cvc5_lift_left_filter(solver: cvc5.Solver, filter_terms: list[list[Any]]) -> list[list[Any]]:
    return [
        [filter_terms[row // 2][col // 2] if row % 2 == col % 2 else cvc5_real(solver, 0.0) for col in range(4)]
        for row in range(4)
    ]


def z3_channel_action(filter_terms: list[list[Any]], rho_terms: list[list[Any]]) -> list[list[Any]]:
    lifted = z3_lift_left_filter(filter_terms)
    return z3_matmul(z3_matmul(lifted, rho_terms), transpose_terms(lifted))


def cvc5_channel_action(
    solver: cvc5.Solver, filter_terms: list[list[Any]], rho_terms: list[list[Any]]
) -> list[list[Any]]:
    lifted = cvc5_lift_left_filter(solver, filter_terms)
    return cvc5_real_matmul(solver, cvc5_real_matmul(solver, lifted, rho_terms), transpose_terms(lifted))


def rho_probe_real_entries(rho_probe: jax.Array) -> list[list[float]]:
    return [[py_float(jnp.real(rho_probe[i, j])) for j in range(4)] for i in range(4)]


def z3_force_channel_commute_status(
    a_values: list[list[int]], b_values: list[list[int]], rho_values: list[list[float]], label: str
) -> dict[str, Any]:
    solver = z3.Solver()
    a = [[z3_real(a_values[i][j]) for j in range(2)] for i in range(2)]
    b = [[z3_real(b_values[i][j]) for j in range(2)] for i in range(2)]
    rho = [[z3.Real(f"{label}_rho_{i}_{j}") for j in range(4)] for i in range(4)]
    for i in range(4):
        for j in range(4):
            solver.add(rho[i][j] == z3_real(rho_values[i][j]))
    ab = z3_channel_action(a, z3_channel_action(b, rho))
    ba = z3_channel_action(b, z3_channel_action(a, rho))
    for i in range(4):
        for j in range(4):
            solver.add(ab[i][j] == ba[i][j])
    status = solver.check()
    return {
        "solver": "z3",
        "level": "channel_level",
        "normalization": "unnormalized_channel_action",
        "force_channel_commute_verdict": str(status),
        "verdict": str(status),
        "bound_filter_entries": 8,
        "bound_rho_probe_entries": 16,
        "bound_entries": 24,
        "rho_probe_source": "rho_2 real entries",
        "derived_products": "Phi_a(Phi_b(rho_probe)) and Phi_b(Phi_a(rho_probe)) 4x4 entries are constructed inside z3 from bound filter and rho entries",
        "asserted_precomputed_scalar": False,
    }


def cvc5_force_channel_commute_status(
    a_values: list[list[int]], b_values: list[list[int]], rho_values: list[list[float]], label: str
) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    real_sort = solver.getRealSort()
    a = [[cvc5_real(solver, a_values[i][j]) for j in range(2)] for i in range(2)]
    b = [[cvc5_real(solver, b_values[i][j]) for j in range(2)] for i in range(2)]
    rho = [[solver.mkConst(real_sort, f"{label}_rho_{i}_{j}") for j in range(4)] for i in range(4)]
    for i in range(4):
        for j in range(4):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, rho[i][j], cvc5_real(solver, rho_values[i][j])))
    ab = cvc5_channel_action(solver, a, cvc5_channel_action(solver, b, rho))
    ba = cvc5_channel_action(solver, b, cvc5_channel_action(solver, a, rho))
    for i in range(4):
        for j in range(4):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, ab[i][j], ba[i][j]))
    result = solver.checkSat()
    status = cvc5_status_text(result)
    return {
        "solver": "cvc5",
        "level": "channel_level",
        "normalization": "unnormalized_channel_action",
        "force_channel_commute_verdict": status,
        "verdict": status,
        "bound_filter_entries": 8,
        "bound_rho_probe_entries": 16,
        "bound_entries": 24,
        "rho_probe_source": "rho_2 real entries",
        "derived_products": "Phi_a(Phi_b(rho_probe)) and Phi_b(Phi_a(rho_probe)) 4x4 entries are constructed inside cvc5 from bound filter and rho entries",
        "asserted_precomputed_scalar": False,
    }


def cvc5_force_commute_status(a_values: list[list[int]], b_values: list[list[int]], label: str) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")
    int_sort = solver.getIntegerSort()
    a = [[solver.mkConst(int_sort, f"{label}_a_{i}_{j}") for j in range(2)] for i in range(2)]
    b = [[solver.mkConst(int_sort, f"{label}_b_{i}_{j}") for j in range(2)] for i in range(2)]
    for i in range(2):
        for j in range(2):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, a[i][j], cvc5_int(solver, a_values[i][j])))
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, b[i][j], cvc5_int(solver, b_values[i][j])))
    ab = [[cvc5_add(solver, [cvc5_mul(solver, a[i][k], b[k][j]) for k in range(2)]) for j in range(2)] for i in range(2)]
    ba = [[cvc5_add(solver, [cvc5_mul(solver, b[i][k], a[k][j]) for k in range(2)]) for j in range(2)] for i in range(2)]
    for i in range(2):
        for j in range(2):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, ab[i][j], ba[i][j]))
    result = solver.checkSat()
    status = cvc5_status_text(result)
    return {
        "solver": "cvc5",
        "level": "filter_level",
        "force_commute_verdict": status,
        "verdict": status,
        "bound_entries": 8,
        "derived_products": "AB and BA entries are computed inside cvc5 from bound matrix entries",
        "asserted_precomputed_scalar": False,
    }


def smt_report(rho_probe: jax.Array) -> dict[str, Any]:
    a, b, ca, cb = smt_matrices()
    rho_values = rho_probe_real_entries(rho_probe)
    z3_non = z3_force_commute_status(a, b, "rung2_noncommuting")
    cvc5_non = cvc5_force_commute_status(a, b, "rung2_noncommuting")
    z3_ctrl = z3_force_commute_status(ca, cb, "rung2_commuting_control")
    cvc5_ctrl = cvc5_force_commute_status(ca, cb, "rung2_commuting_control")
    z3_channel_non = z3_force_channel_commute_status(a, b, rho_values, "rung2_channel_noncommuting")
    cvc5_channel_non = cvc5_force_channel_commute_status(a, b, rho_values, "rung2_channel_noncommuting")
    z3_channel_ctrl = z3_force_channel_commute_status(ca, cb, rho_values, "rung2_channel_commuting_control")
    cvc5_channel_ctrl = cvc5_force_channel_commute_status(ca, cb, rho_values, "rung2_channel_commuting_control")
    return {
        "rung2_adjacent_pair": {
            "A": a,
            "B": b,
            "filter_level": {"z3": z3_non, "cvc5": cvc5_non},
            "channel_level": {"z3": z3_channel_non, "cvc5": cvc5_channel_non},
            "z3": z3_channel_non,
            "cvc5": cvc5_channel_non,
            "agreement": z3_non["verdict"] == cvc5_non["verdict"],
            "channel_agreement": z3_channel_non["verdict"] == cvc5_channel_non["verdict"],
        },
        "commuting_control": {
            "A": ca,
            "B": cb,
            "filter_level": {"z3": z3_ctrl, "cvc5": cvc5_ctrl},
            "channel_level": {"z3": z3_channel_ctrl, "cvc5": cvc5_channel_ctrl},
            "z3": z3_channel_ctrl,
            "cvc5": cvc5_channel_ctrl,
            "agreement": z3_ctrl["verdict"] == cvc5_ctrl["verdict"],
            "channel_agreement": z3_channel_ctrl["verdict"] == cvc5_channel_ctrl["verdict"],
        },
    }


def density_diagnostics(rho: jax.Array) -> dict[str, Any]:
    vals = jnp.linalg.eigvalsh(hermitize(rho))
    return {
        "trace": py_float(trace_real(rho)),
        "min_eigenvalue": py_float(jnp.min(vals)),
        "hermitian_residual": py_float(jnp.max(jnp.abs(rho - jnp.conj(rho.T)))),
        "psd": py_bool(jnp.min(vals) >= -1.0e-9),
    }


def build_result() -> dict[str, Any]:
    quotients = quotient_report()
    rhos = {r: rho_for_rung(r) for r in (1, 2, 3)}
    sep_rhos = {r: separable_rho_for_rung(r) for r in (1, 2, 3)}
    rho_probe = rhos[2]

    conditional = {r: py_float(conditional_entropy(rhos[r])) for r in (1, 2, 3)}
    signed_cut = {r: -conditional[r] for r in (1, 2, 3)}
    sep_conditional = {r: py_float(conditional_entropy(sep_rhos[r])) for r in (1, 2, 3)}
    carrier_components = {r: entropy_components(rhos[r]) for r in (1, 2, 3)}
    sep_components = {r: entropy_components(sep_rhos[r]) for r in (1, 2, 3)}
    gaps = {
        "r1_r2": order_gap(K_FILTERS[1], K_FILTERS[2], rho_probe),
        "r2_r3": order_gap(K_FILTERS[2], K_FILTERS[3], rho_probe),
    }
    commuting_gaps = {
        "r1_r2": order_gap(COMMUTING_FILTERS[1], COMMUTING_FILTERS[2], rho_probe),
        "r2_r3": order_gap(COMMUTING_FILTERS[2], COMMUTING_FILTERS[3], rho_probe),
    }
    smt = smt_report(rho_probe)
    negative_crossings = [r for r, value in conditional.items() if value < -TOL]
    class_counts = [quotients[f"M_{r}"]["distinguishable_class_count"] for r in (1, 2, 3)]
    source_deps = {str(path.relative_to(ROOT)): file_sha256(path) for path in SOURCE_DEPENDENCIES}
    shared_scalars = {
        "conditional_entropy_r1": conditional[1],
        "conditional_entropy_r2": conditional[2],
        "conditional_entropy_r3": conditional[3],
        "signed_cut_Ic_r1": signed_cut[1],
        "signed_cut_Ic_r2": signed_cut[2],
        "signed_cut_Ic_r3": signed_cut[3],
        "separable_conditional_entropy_r1": sep_conditional[1],
        "separable_conditional_entropy_r2": sep_conditional[2],
        "separable_conditional_entropy_r3": sep_conditional[3],
        "carrier_S_AB_r1": carrier_components[1]["S_AB"],
        "carrier_S_AB_r2": carrier_components[2]["S_AB"],
        "carrier_S_AB_r3": carrier_components[3]["S_AB"],
        "carrier_S_B_r1": carrier_components[1]["S_B"],
        "carrier_S_B_r2": carrier_components[2]["S_B"],
        "carrier_S_B_r3": carrier_components[3]["S_B"],
        "separable_control_S_AB_r1": sep_components[1]["S_AB"],
        "separable_control_S_AB_r2": sep_components[2]["S_AB"],
        "separable_control_S_AB_r3": sep_components[3]["S_AB"],
        "separable_control_S_B_r1": sep_components[1]["S_B"],
        "separable_control_S_B_r2": sep_components[2]["S_B"],
        "separable_control_S_B_r3": sep_components[3]["S_B"],
        "order_gap_r1_r2": gaps["r1_r2"],
        "order_gap_r2_r3": gaps["r2_r3"],
        "commuting_order_gap_r1_r2": commuting_gaps["r1_r2"],
        "commuting_order_gap_r2_r3": commuting_gaps["r2_r3"],
        "quotient_class_count_M1": float(class_counts[0]),
        "quotient_class_count_M2": float(class_counts[1]),
        "quotient_class_count_M3": float(class_counts[2]),
        "negative_crossing_rung": float(negative_crossings[0] if negative_crossings else 0),
        "boundary_rung1_conditional_entropy": conditional[1],
    }
    controls = {
        "separable_nonnegative_every_rung": all(value >= -TOL for value in sep_conditional.values()),
        "commuting_control_zero_order_gap": all(value <= TOL for value in commuting_gaps.values()),
        "commuting_control_classification": "not_a_ratchet_zero_order_gap",
        "boundary_rung_count_1_no_signed_cut_crossing": conditional[1] >= -TOL,
        "carrier_conditional_entropy_strictly_decreases": conditional[1] > conditional[2] > conditional[3],
        "carrier_crosses_negative": bool(negative_crossings),
        "order_gap_nonzero_every_adjacent_pair": all(value > TOL for value in gaps.values()),
        "quotient_tightens": class_counts[0] < class_counts[1] and class_counts[1] <= class_counts[2],
        "smt_filter_level_noncommuting_unsat": smt["rung2_adjacent_pair"]["filter_level"]["z3"]["verdict"]
        == smt["rung2_adjacent_pair"]["filter_level"]["cvc5"]["verdict"]
        == "unsat",
        "smt_filter_level_commuting_control_sat": smt["commuting_control"]["filter_level"]["z3"]["verdict"]
        == smt["commuting_control"]["filter_level"]["cvc5"]["verdict"]
        == "sat",
        "smt_channel_level_noncommuting_unsat": smt["rung2_adjacent_pair"]["channel_level"]["z3"]["verdict"]
        == smt["rung2_adjacent_pair"]["channel_level"]["cvc5"]["verdict"]
        == "unsat",
        "smt_channel_level_commuting_control_sat": smt["commuting_control"]["channel_level"]["z3"]["verdict"]
        == smt["commuting_control"]["channel_level"]["cvc5"]["verdict"]
        == "sat",
    }
    rungs = []
    for rung in (1, 2, 3):
        stack = stack_state(rung, rhos[rung], K_FILTERS)
        rungs.append(
            {
                "rung": rung,
                "eta": ETA_SHELLS[rung],
                "theta": py_float(theta(rung)),
                "probe_family": probe_family(rung),
                "density": density_diagnostics(rhos[rung]),
                "stacked_density": density_diagnostics(stack),
                "conditional_entropy_S_A_given_B": conditional[rung],
                "entropy_components": carrier_components[rung],
                "signed_cut_Ic": signed_cut[rung],
                "separable_control_S_A_given_B": sep_conditional[rung],
                "separable_control_entropy_components": sep_components[rung],
                "density_quotient": quotients[f"M_{rung}"],
            }
        )
    all_pass = bool(
        jax.config.jax_enable_x64
        and all(value["psd"] for value in (density_diagnostics(rhos[r]) for r in (1, 2, 3)))
        and all(controls[key] for key in controls if isinstance(controls[key], bool))
        and READS_PEER_RESULT is False
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "schema_version": "three_engine_sim_result_v1",
        "engine_contract": {"mode": "all_three_full_sims", "reads_peer_result": False},
        "object_id": OBJECT_ID,
        "engine": ENGINE,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "source_dependencies": source_deps,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_path_tools": ["z3", "cvc5"],
        "control_only_tools": [],
        "rungs": rungs,
        "quotient": quotients,
        "signed_cut": {
            "cut": "Weyl-L sheet | Weyl-R sheet",
            "log_base": "e",
            "conditional_entropy_by_rung": {str(k): v for k, v in conditional.items()},
            "signed_cut_Ic_by_rung": {str(k): v for k, v in signed_cut.items()},
            "headline_claim_under_test": "S(A|B) decreases monotonically and goes negative once nesting forces L/R entanglement",
        },
        "order_gaps": gaps,
        "controls": controls,
        "negative_controls": {
            "separable": {str(k): v for k, v in sep_conditional.items()},
            "commuting": commuting_gaps,
            "boundary": {"rung_count": 1, "conditional_entropy": conditional[1], "crosses_negative": conditional[1] < -TOL},
        },
        "smt": smt,
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": smt["rung2_adjacent_pair"]["z3"]["verdict"],
                "commuting_control_verdict": smt["commuting_control"]["z3"]["verdict"],
                "filter_level": smt["rung2_adjacent_pair"]["filter_level"]["z3"],
                "channel_level": smt["rung2_adjacent_pair"]["channel_level"]["z3"],
                "commuting_control_filter_level": smt["commuting_control"]["filter_level"]["z3"],
                "commuting_control_channel_level": smt["commuting_control"]["channel_level"]["z3"],
                "claim": "z3 binds rung-2 adjacent filters and rho_probe entries, derives channel-level noncommutation because forcing unnormalized Phi_a(Phi_b(rho_probe)) == Phi_b(Phi_a(rho_probe)) is UNSAT",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": smt["rung2_adjacent_pair"]["cvc5"]["verdict"],
                "commuting_control_verdict": smt["commuting_control"]["cvc5"]["verdict"],
                "filter_level": smt["rung2_adjacent_pair"]["filter_level"]["cvc5"],
                "channel_level": smt["rung2_adjacent_pair"]["channel_level"]["cvc5"],
                "commuting_control_filter_level": smt["commuting_control"]["filter_level"]["cvc5"],
                "commuting_control_channel_level": smt["commuting_control"]["channel_level"]["cvc5"],
                "claim": "cvc5 independently binds the same filter and rho_probe entries and derives the same unnormalized channel-level UNSAT/SAT flip",
            },
        },
        "shared_scalars": shared_scalars,
        "shared_observable_keys": sorted(shared_scalars),
        "all_pass": all_pass,
        "claim_ceiling": "scratch_diagnostic only; promotion_allowed=false; formal_admission_allowed=false; no bridge, Axis0, manifold, or M(C) closure.",
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_NESTED_HOPF_WEYL_SIGNED_CUT_RATCHET_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"S=[{result['shared_scalars']['conditional_entropy_r1']},"
        f"{result['shared_scalars']['conditional_entropy_r2']},"
        f"{result['shared_scalars']['conditional_entropy_r3']}] "
        f"gaps=[{result['shared_scalars']['order_gap_r1_r2']},"
        f"{result['shared_scalars']['order_gap_r2_r3']}] "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
