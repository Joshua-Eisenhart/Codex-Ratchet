#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for foundation_r6_g2_associative_calibration."""

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


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_g2_associative_calibration"
OBJECT_ID = "foundation_r6_g2_associative_calibration_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_g2_associative_calibration_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_g2_associative_calibration_jax_results.json"
TOL = 1.0e-12

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Cayley-Dickson octonion table and phi-coordinate calibration probe values",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite tensor arithmetic for phi and coordinate 3-plane probe family",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing in-solver derivation of phi(u,v,w) from bound phi and plane coordinates",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent in-solver derivation of the same calibration and erase-flip claims",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization, timestamps, and hashing",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def cd_conj(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate([jnp.ones((1,), dtype=x.dtype), -jnp.ones((x.shape[0] - 1,), dtype=x.dtype)])
    return x * signs


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
    return jnp.concatenate([first, second])


def cd_double(parent: jax.Array) -> jax.Array:
    dim = 2 * int(parent.shape[0])
    table = jnp.zeros((dim, dim, dim), dtype=jnp.int64)
    eye = jnp.eye(dim, dtype=jnp.int64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(cd_pair_multiply(parent, eye[i], eye[j]))
    return table


def octonion_table() -> jax.Array:
    real = jnp.zeros((1, 1, 1), dtype=jnp.int64).at[0, 0, 0].set(1)
    complex_table = cd_double(real)
    quaternion = cd_double(complex_table)
    return cd_double(quaternion)


def phi_tensor(table: jax.Array) -> jax.Array:
    phi = jnp.zeros((7, 7, 7), dtype=jnp.int64)
    for i in range(7):
        for j in range(7):
            for k in range(7):
                phi = phi.at[i, j, k].set(table[k + 1, i + 1, j + 1])
    return phi


def combos(n: int, k: int) -> list[tuple[int, ...]]:
    out: list[tuple[int, ...]] = []

    def rec(start: int, acc: list[int]) -> None:
        if len(acc) == k:
            out.append(tuple(acc))
            return
        for value in range(start, n):
            acc.append(value)
            rec(value + 1, acc)
            acc.pop()

    rec(0, [])
    return out


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def phi_value(phi: jax.Array, u: jax.Array, v: jax.Array, w: jax.Array) -> float:
    return float(jax.device_get(jnp.einsum("ijk,i,j,k->", phi.astype(jnp.float64), u, v, w)))


def table_sha(table: jax.Array) -> str:
    flat = [str(int(x)) for x in jax.device_get(table).reshape((-1,)).tolist()]
    return hashlib.sha256(",".join(flat).encode("utf-8")).hexdigest()


def oriented_from_sorted(phi: jax.Array, comp: tuple[int, int, int]) -> tuple[int, int, int]:
    value = int(jax.device_get(phi[comp[0], comp[1], comp[2]]))
    if value == 1:
        return comp
    return (comp[0], comp[2], comp[1])


def oriented_fano_lines(phi: jax.Array) -> list[dict[str, Any]]:
    lines = []
    for comp in combos(7, 3):
        value = int(jax.device_get(phi[comp[0], comp[1], comp[2]]))
        if abs(value) != 1:
            continue
        oriented = oriented_from_sorted(phi, comp)
        lines.append(
            {
                "plane": [idx + 1 for idx in comp],
                "oriented_plane": [idx + 1 for idx in oriented],
                "sorted_phi": value,
                "oriented_phi": 1,
                "label": "span(" + ",".join(f"e{idx + 1}" for idx in comp) + ")",
            }
        )
    return lines


def erased_phi(phi: jax.Array, oriented_line: list[int]) -> jax.Array:
    out = phi
    zero_based = [idx - 1 for idx in oriented_line]
    for i in zero_based:
        for j in zero_based:
            for k in zero_based:
                if len({i, j, k}) == 3:
                    out = out.at[i, j, k].set(0)
    return out


def coordinate_plane_report(phi: jax.Array) -> dict[str, Any]:
    rows = []
    for comp in combos(7, 3):
        u, v, w = (basis(7, comp[0]), basis(7, comp[1]), basis(7, comp[2]))
        value = phi_value(phi, u, v, w)
        rows.append(
            {
                "plane": [idx + 1 for idx in comp],
                "phi_on_sorted_orientation": value,
                "abs_phi": abs(value),
                "calibrated_as_unoriented_plane": abs(abs(value) - 1.0) <= TOL,
            }
        )
    return {
        "plane_count": len(rows),
        "calibrated_plane_count": sum(1 for row in rows if row["calibrated_as_unoriented_plane"]),
        "uncalibrated_plane_count": sum(1 for row in rows if not row["calibrated_as_unoriented_plane"]),
        "planes": rows,
    }


def cross_product(table: jax.Array, i: int, j: int) -> jax.Array:
    product = table[:, i + 1, j + 1]
    return product[1:].astype(jnp.int64)


def closure_report(table: jax.Array, planes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for plane in planes:
        indices = [idx - 1 for idx in plane["plane"]]
        support = set(indices)
        closed = True
        products = []
        for i in indices:
            for j in indices:
                if i == j:
                    continue
                cp = cross_product(table, i, j)
                nz = [idx for idx, value in enumerate(jax.device_get(cp).tolist()) if int(value) != 0]
                if any(idx not in support for idx in nz):
                    closed = False
                products.append({"pair": [i + 1, j + 1], "support": [idx + 1 for idx in nz]})
        rows.append({"plane": plane["plane"], "closed_under_cross_product": closed, "products": products})
    return rows


def density_guard() -> dict[str, Any]:
    rho = jnp.eye(7, dtype=jnp.float64) / 7.0
    return {
        "trace": float(jax.device_get(jnp.trace(rho))),
        "trace_eq_1": abs(float(jax.device_get(jnp.trace(rho))) - 1.0) <= TOL,
        "psd": bool(jax.device_get(jnp.min(jnp.linalg.eigvalsh(rho)) >= -TOL)),
        "hermitian": bool(jax.device_get(jnp.max(jnp.abs(rho - rho.T)) <= TOL)),
        "hermitian_defect": float(jax.device_get(jnp.max(jnp.abs(rho - rho.T)))),
        "normalization": "control-only rho=I/7 guard; calibration result is from phi probes, not rho",
    }


def z3_expr_from_bound(phi_values: list[list[list[int]]], plane: tuple[int, int, int], *, erase_line: list[int] | None = None) -> tuple[z3.Solver, z3.ArithRef]:
    solver = z3.Solver()
    pvars = [[[z3.Real(f"phi_{i}_{j}_{k}") for k in range(7)] for j in range(7)] for i in range(7)]
    uvars = [z3.Real(f"u_{i}") for i in range(7)]
    vvars = [z3.Real(f"v_{i}") for i in range(7)]
    wvars = [z3.Real(f"w_{i}") for i in range(7)]
    erase_set = set(erase_line or [])
    for i in range(7):
        for j in range(7):
            for k in range(7):
                value = 0 if {i, j, k} == erase_set and len({i, j, k}) == 3 else phi_values[i][j][k]
                solver.add(pvars[i][j][k] == z3.RealVal(value))
    for idx, vars_ in enumerate((uvars, vvars, wvars)):
        for coord in range(7):
            vars_[coord] = vars_[coord]
            solver.add(vars_[coord] == z3.RealVal(1 if coord == plane[idx] else 0))
    expr = z3.Sum([pvars[i][j][k] * uvars[i] * vvars[j] * wvars[k] for i in range(7) for j in range(7) for k in range(7)])
    return solver, expr


def z3_calibration_proof(phi: jax.Array, fano: tuple[int, int, int], generic: tuple[int, int, int]) -> dict[str, Any]:
    values = [[[int(jax.device_get(phi[i, j, k])) for k in range(7)] for j in range(7)] for i in range(7)]
    solver, expr = z3_expr_from_bound(values, fano)
    solver.add(expr != z3.RealVal(1))
    fano_status = solver.check()

    generic_solver, generic_expr = z3_expr_from_bound(values, generic)
    generic_solver.add(generic_expr < z3.RealVal(1))
    generic_status = generic_solver.check()

    erased_solver, erased_expr = z3_expr_from_bound(values, fano, erase_line=list(fano))
    erased_solver.add(erased_expr != z3.RealVal(1))
    erased_status = erased_solver.check()

    return {
        "solver": "z3",
        "verdict": str(fano_status),
        "claim": "With phi components and plane coordinates bound, solver derives phi(fano_plane)=1; asserted phi!=1 is UNSAT",
        "generic_control_verdict": str(generic_status),
        "negative_control_verdict": str(erased_status),
        "erase_flip_unsat_to_sat": fano_status == z3.unsat and erased_status == z3.sat,
        "generic_phi_less_than_one_sat": generic_status == z3.sat,
        "bound_phi_components": 343,
        "bound_plane_coordinates": 21,
        "derived_expression": "sum_ijk phi_ijk*u_i*v_j*w_k",
        "asserted_precomputed_scalar_literal": False,
    }


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkReal(str(value))


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_sum(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return cvc5_int(solver, 0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_expr_from_bound(phi_values: list[list[list[int]]], plane: tuple[int, int, int], *, erase_line: list[int] | None = None) -> tuple[cvc5.Solver, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    real_sort = solver.getRealSort()
    pvars = [[[solver.mkConst(real_sort, f"phi_{i}_{j}_{k}") for k in range(7)] for j in range(7)] for i in range(7)]
    uvars = [solver.mkConst(real_sort, f"u_{i}") for i in range(7)]
    vvars = [solver.mkConst(real_sort, f"v_{i}") for i in range(7)]
    wvars = [solver.mkConst(real_sort, f"w_{i}") for i in range(7)]
    erase_set = set(erase_line or [])
    for i in range(7):
        for j in range(7):
            for k in range(7):
                value = 0 if {i, j, k} == erase_set and len({i, j, k}) == 3 else phi_values[i][j][k]
                solver.assertFormula(solver.mkTerm(Kind.EQUAL, pvars[i][j][k], cvc5_int(solver, value)))
    for idx, vars_ in enumerate((uvars, vvars, wvars)):
        for coord, var in enumerate(vars_):
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, cvc5_int(solver, 1 if coord == plane[idx] else 0)))
    terms = []
    for i in range(7):
        for j in range(7):
            for k in range(7):
                terms.append(solver.mkTerm(Kind.MULT, pvars[i][j][k], uvars[i], vvars[j], wvars[k]))
    return solver, cvc5_sum(solver, terms)


def cvc5_calibration_proof(phi: jax.Array, fano: tuple[int, int, int], generic: tuple[int, int, int]) -> dict[str, Any]:
    values = [[[int(jax.device_get(phi[i, j, k])) for k in range(7)] for j in range(7)] for i in range(7)]
    solver, expr = cvc5_expr_from_bound(values, fano)
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, expr, cvc5_int(solver, 1))))
    fano_result = solver.checkSat()

    generic_solver, generic_expr = cvc5_expr_from_bound(values, generic)
    generic_solver.assertFormula(generic_solver.mkTerm(Kind.LT, generic_expr, cvc5_int(generic_solver, 1)))
    generic_result = generic_solver.checkSat()

    erased_solver, erased_expr = cvc5_expr_from_bound(values, fano, erase_line=list(fano))
    erased_solver.assertFormula(erased_solver.mkTerm(Kind.NOT, erased_solver.mkTerm(Kind.EQUAL, erased_expr, cvc5_int(erased_solver, 1))))
    erased_result = erased_solver.checkSat()

    return {
        "solver": "cvc5",
        "verdict": cvc5_status(fano_result),
        "claim": "With phi components and plane coordinates bound, solver derives phi(fano_plane)=1; asserted phi!=1 is UNSAT",
        "generic_control_verdict": cvc5_status(generic_result),
        "negative_control_verdict": cvc5_status(erased_result),
        "erase_flip_unsat_to_sat": fano_result.isUnsat() and erased_result.isSat(),
        "generic_phi_less_than_one_sat": generic_result.isSat(),
        "bound_phi_components": 343,
        "bound_plane_coordinates": 21,
        "derived_expression": "sum_ijk phi_ijk*u_i*v_j*w_k",
        "asserted_precomputed_scalar_literal": False,
    }


def build_result() -> dict[str, Any]:
    table = octonion_table()
    phi = phi_tensor(table)
    fano_lines = oriented_fano_lines(phi)
    coordinate = coordinate_plane_report(phi)
    first_line = tuple(idx - 1 for idx in fano_lines[0]["oriented_plane"])
    generic_plane = next(tuple(idx - 1 for idx in row["plane"]) for row in coordinate["planes"] if not row["calibrated_as_unoriented_plane"])
    erased = erased_phi(phi, fano_lines[0]["oriented_plane"])
    erased_coordinate = coordinate_plane_report(erased)
    zero_coordinate = coordinate_plane_report(jnp.zeros((7, 7, 7), dtype=jnp.int64))
    fano_value = phi_value(phi, *(basis(7, idx) for idx in first_line))
    generic_value = phi_value(phi, *(basis(7, idx) for idx in generic_plane))
    z3_proof = z3_calibration_proof(phi, first_line, generic_plane)
    cvc5_proof = cvc5_calibration_proof(phi, first_line, generic_plane)
    guard = density_guard()
    closure = closure_report(table, fano_lines)
    negative = {
        "drop_one_fano_probe_count_7_to_6": coordinate["calibrated_plane_count"] == 7 and erased_coordinate["calibrated_plane_count"] == 6,
        "force_commutative_zero_phi_count_7_to_0": coordinate["calibrated_plane_count"] == 7 and zero_coordinate["calibrated_plane_count"] == 0,
        "generic_coordinate_plane_phi_less_than_one": generic_value < 1.0,
        "z3_erase_flip_unsat_to_sat": z3_proof["erase_flip_unsat_to_sat"],
        "cvc5_erase_flip_unsat_to_sat": cvc5_proof["erase_flip_unsat_to_sat"],
    }
    all_pass = bool(
        jax.config.jax_enable_x64
        and len(fano_lines) == 7
        and coordinate["calibrated_plane_count"] == 7
        and all(row["closed_under_cross_product"] for row in closure)
        and abs(fano_value - 1.0) <= TOL
        and generic_value < 1.0
        and z3_proof["verdict"] == cvc5_proof["verdict"] == "unsat"
        and z3_proof["generic_control_verdict"] == cvc5_proof["generic_control_verdict"] == "sat"
        and z3_proof["negative_control_verdict"] == cvc5_proof["negative_control_verdict"] == "sat"
        and all(value for value in negative.values())
        and guard["trace_eq_1"]
        and guard["psd"]
        and guard["hermitian"]
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
        "runtime_preflight": {"jax_enable_x64": bool(jax.config.jax_enable_x64), "jax_version": jax.__version__},
        "M": {
            "name": "G2 associative calibration probe family",
            "explicit_probe_family": "All 35 coordinate oriented 3-plane probes e_i wedge e_j wedge e_k, evaluated by phi(u,v,w) against unit volume.",
            "finite_probe_counts": {"coordinate_3_planes": 35, "calibrated_planes": coordinate["calibrated_plane_count"]},
            "measurement_map": "M(P)=(phi(e_i,e_j,e_k), volume(e_i,e_j,e_k)=1, cross-product closure flag) for each coordinate 3-plane P",
        },
        "C": {
            "trace_eq_1": guard["trace_eq_1"],
            "psd": guard["psd"],
            "hermitian": guard["hermitian"],
            "normalization": "orthonormal imaginary octonion basis; each coordinate 3-plane has unit volume",
            "rung_specific_constraint": "phi_ijk is computed from the Cayley-Dickson octonion table by e_i e_j = sum_k phi_ijk e_k on Im(O)",
            "density_guard": guard,
        },
        "S_mod_M": {
            "definition": "Coordinate 3-planes are equivalent by M when their calibration/closure probe vector agrees; calibrated class is phi=1 after orientation and closed under octonion cross product.",
            "calibrated_class_count": coordinate["calibrated_plane_count"],
            "uncalibrated_class_count": coordinate["uncalibrated_plane_count"],
            "calibrated_planes": fano_lines,
        },
        "octonion_structure": {
            "construction": "Cayley-Dickson R -> C -> H -> O",
            "table_sha256": table_sha(table),
            "phi_nonzero_component_count": int(jax.device_get(jnp.count_nonzero(phi))),
        },
        "calibration": {
            "fano_lines": fano_lines,
            "coordinate_probe_summary": coordinate,
            "cross_product_closure": closure,
            "first_fano_oriented_plane": [idx + 1 for idx in first_line],
            "first_fano_phi": fano_value,
            "generic_control_plane": [idx + 1 for idx in generic_plane],
            "generic_control_phi": generic_value,
            "erased_first_fano_calibrated_count": erased_coordinate["calibrated_plane_count"],
            "forced_commutative_zero_phi_calibrated_count": zero_coordinate["calibrated_plane_count"],
        },
        "smt": {"z3": z3_proof, "cvc5": cvc5_proof, "agreement": z3_proof["verdict"] == cvc5_proof["verdict"]},
        "crossover_proofs": {
            "z3": {"ran": True, "load_bearing": True, **z3_proof},
            "cvc5": {"ran": True, "load_bearing": True, **cvc5_proof},
        },
        "negative_control_flip": negative,
        "summary": {
            "calibrated_plane_count": coordinate["calibrated_plane_count"],
            "fano_line_count": len(fano_lines),
            "first_fano_phi": fano_value,
            "generic_control_phi": generic_value,
            "erased_first_fano_calibrated_count": erased_coordinate["calibrated_plane_count"],
            "forced_commutative_zero_phi_calibrated_count": zero_coordinate["calibrated_plane_count"],
            "z3_verdict": z3_proof["verdict"],
            "cvc5_verdict": cvc5_proof["verdict"],
            "all_pass": all_pass,
        },
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R6_G2_ASSOCIATIVE_CALIBRATION_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"calibrated={s['calibrated_plane_count']} "
        f"first_fano_phi={s['first_fano_phi']} "
        f"generic_phi={s['generic_control_phi']} "
        f"z3={s['z3_verdict']} cvc5={s['cvc5_verdict']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
