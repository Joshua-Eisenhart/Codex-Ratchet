#!/usr/bin/env python3
"""Terrain Weyl spinor L/R scratch diagnostic.

This packet consumes the committed S5 affine Bloch generators by hash and lifts
them to one explicit quantum-jump unraveling. The unraveling is a convention:
the ensemble density flow is load-bearing; no-jump spinor paths are not unique.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.metadata as md
import json
import math
from pathlib import Path
from typing import Any

import cvc5
import numpy as np
import scipy.linalg
import sympy as sp
import z3


SIM_ID = "terrain_weyl_spinor_lr_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_python_results.json"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"

S5_PATH = ROOT / "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json"
S1_PATH = ROOT / "system_v6/sims/geo_s1_spinor_hopf_free_v0/results/geo_s1_spinor_hopf_free_v0_envelope_results.json"
S2S5_PATH = ROOT / "system_v6/sims/geo_s2_s5_mode_sweep_v0/results/geo_s2_s5_mode_sweep_v0_envelope_results.json"
NONASSOC_PATH = ROOT / "system_v6/sims/mct_nonassoc_weld_packet_v0/results/mct_nonassoc_weld_packet_v0_envelope_results.json"
ENV_DOCTOR_PATH = ROOT / "system_v5/ops/formal_scouts/env_doctor_report_20260610.json"

EXPECTED_S5_RESULT_HASH = "8c5474786973f067e55c0200392c1a27cbe8bf5d71cfd632b507d066b6cc9b1e"
TOL = 1.0e-9

SQRT3 = sp.sqrt(3)
M_SIGMA_Y = sp.diag(-1, 1, -1)
M_SIGMA_X = sp.diag(1, -1, -1)

FAMILY_PAIRS = {
    "Se": ("Se_Funnel_L", "Se_Cannon_R"),
    "Ne": ("Ne_Vortex_L", "Ne_Spiral_R"),
    "Ni": ("Ni_Pit_L", "Ni_Source_R"),
    "Si": ("Si_Hill_L", "Si_Citadel_R"),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def package_version(name: str, fallback: str | None = None) -> str:
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        if fallback is not None:
            return fallback
        return "unknown"


def sexpr(value: Any) -> sp.Expr:
    return sp.sympify(str(value), locals={"sqrt": sp.sqrt, "pi": sp.pi})


def parse_committed_generators(s5: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for name, row in s5["bloch_generator_table"].items():
        pinned = row["pinned"]
        out[name] = {
            "family": row["family"],
            "label": row["label"],
            "A": sp.Matrix([[sexpr(x) for x in line] for line in pinned["A"]]),
            "b": sp.Matrix([sexpr(x) for x in pinned["b"]]),
            "source_ref": row.get("source_ref", {}),
            "pin_consistency": row.get("pin_consistency", {}),
        }
    return out


def find_exact_special_case(obj: Any, name: str) -> dict[str, Any] | None:
    if isinstance(obj, dict):
        maybe = obj.get(name)
        if isinstance(maybe, dict) and isinstance(maybe.get("exact_special_case_check"), dict):
            check = maybe["exact_special_case_check"]
            if isinstance(check.get("r_t"), list):
                return check
        for value in obj.values():
            found = find_exact_special_case(value, name)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_exact_special_case(value, name)
            if found is not None:
                return found
    return None


def find_density_erasure_row(obj: Any) -> dict[str, Any] | None:
    required = {"spinor_gap_norm", "density_gap_norm", "visible_on_lifted_spinor_row", "erased_under_density_quotient"}
    if isinstance(obj, dict):
        if required.issubset(obj.keys()):
            return obj
        for value in obj.values():
            found = find_density_erasure_row(value)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_density_erasure_row(value)
            if found is not None:
                return found
    return None


def matrix_strings(mat: sp.Matrix) -> list[list[str]]:
    return [[str(sp.simplify(mat[i, j])) for j in range(mat.cols)] for i in range(mat.rows)]


def vector_strings(vec: sp.Matrix) -> list[str]:
    return [str(sp.simplify(vec[i])) for i in range(vec.rows)]


def max_abs_sympy(values: list[sp.Expr]) -> float:
    if not values:
        return 0.0
    return float(max(abs(float(sp.N(v))) for v in values))


def coeff_pair(expr: sp.Expr) -> tuple[sp.Rational, sp.Rational]:
    expr = sp.expand(sp.simplify(expr))
    c1 = sp.Rational(sp.simplify(expr.coeff(SQRT3)))
    c0 = sp.Rational(sp.simplify(expr - c1 * SQRT3))
    return c0, c1


def scaled_coefficients(exprs: list[sp.Expr]) -> dict[str, Any]:
    coeffs: list[sp.Rational] = []
    for expr in exprs:
        c0, c1 = coeff_pair(expr)
        coeffs.extend([c0, c1])
    denom = 1
    for c in coeffs:
        denom = math.lcm(denom, int(c.q))
    return {
        "scale": denom,
        "values": [int(c * denom) for c in coeffs],
        "pairs": [{"rational": str(c), "scaled": int(c * denom)} for c in coeffs],
    }


def z3_nonzero_unsat(values: list[int], label: str) -> dict[str, Any]:
    solver = z3.Solver()
    xs = [z3.Int(f"{label}_{i}") for i in range(len(values))]
    for x, v in zip(xs, values):
        solver.add(x == v)
    solver.add(z3.Or([x != 0 for x in xs]) if xs else z3.BoolVal(False))
    status = solver.check()
    return {"solver": "z3", "label": label, "query": "bound_values_and_assert_any_nonzero", "status": str(status)}


def z3_zero_forced_unsat(values: list[int], label: str) -> dict[str, Any]:
    solver = z3.Solver()
    xs = [z3.Int(f"{label}_{i}") for i in range(len(values))]
    for x, v in zip(xs, values):
        solver.add(x == v)
    solver.add(z3.And([x == 0 for x in xs]) if xs else z3.BoolVal(True))
    status = solver.check()
    return {"solver": "z3", "label": label, "query": "bound_values_and_force_all_zero", "status": str(status)}


def cvc5_int_const(solver: cvc5.Solver, value: int) -> cvc5.Term:
    return solver.mkInteger(str(value))


def cvc5_nonzero_unsat(values: list[int], label: str) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    sort = solver.getIntegerSort()
    vars_ = [solver.mkConst(sort, f"{label}_{i}") for i in range(len(values))]
    for var, value in zip(vars_, values):
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, var, cvc5_int_const(solver, value)))
    if vars_:
        neq = [solver.mkTerm(cvc5.Kind.NOT, solver.mkTerm(cvc5.Kind.EQUAL, var, cvc5_int_const(solver, 0))) for var in vars_]
        solver.assertFormula(solver.mkTerm(cvc5.Kind.OR, *neq))
    else:
        solver.assertFormula(solver.mkFalse())
    status = str(solver.checkSat())
    return {"solver": "cvc5", "label": label, "query": "bound_values_and_assert_any_nonzero", "status": status}


def cvc5_zero_forced_unsat(values: list[int], label: str) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    sort = solver.getIntegerSort()
    vars_ = [solver.mkConst(sort, f"{label}_{i}") for i in range(len(values))]
    for var, value in zip(vars_, values):
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, var, cvc5_int_const(solver, value)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, var, cvc5_int_const(solver, 0)))
    status = str(solver.checkSat())
    return {"solver": "cvc5", "label": label, "query": "bound_values_and_force_all_zero", "status": status}


def paulis() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ident = np.eye(2, dtype=complex)
    sx = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
    sy = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
    sz = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    return ident, sx, sy, sz


IDENT2, SX, SY, SZ = paulis()
SIGMA_MINUS = np.array([[0.0, 0.0], [1.0, 0.0]], dtype=complex)
SIGMA_PLUS = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)
PZ_PLUS = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
PZ_MINUS = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)
PX_PLUS = 0.5 * np.array([[1.0, 1.0], [1.0, 1.0]], dtype=complex)
PX_MINUS = 0.5 * np.array([[1.0, -1.0], [-1.0, 1.0]], dtype=complex)


def hamiltonian(axis: np.ndarray, coeff: float) -> np.ndarray:
    axis = axis / np.linalg.norm(axis)
    return coeff * (axis[0] * SX + axis[1] * SY + axis[2] * SZ)


def native_lift_spec(name: str) -> dict[str, Any]:
    n111 = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)
    if name == "Se_Funnel_L":
        jumps = [math.sqrt(1 / 5) * SX, math.sqrt(1 / 5) * SY, math.sqrt(1 / 5) * SZ]
        return {"hamiltonian_axis": [1, 1, 1], "hamiltonian_coeff": 1 / 5, "H": hamiltonian(n111, 1 / 5), "jumps": jumps, "jump_names": ["sqrt(1/5)*sigma_x", "sqrt(1/5)*sigma_y", "sqrt(1/5)*sigma_z"], "chirality": "L"}
    if name == "Se_Cannon_R":
        jumps = [math.sqrt(1 / 5) * SX, math.sqrt(1 / 5) * SY, math.sqrt(1 / 5) * SZ]
        return {"hamiltonian_axis": [1, 1, 1], "hamiltonian_coeff": -1 / 5, "H": hamiltonian(n111, -1 / 5), "jumps": jumps, "jump_names": ["sqrt(1/5)*sigma_x", "sqrt(1/5)*sigma_y", "sqrt(1/5)*sigma_z"], "chirality": "R"}
    if name == "Ne_Vortex_L":
        return {"hamiltonian_axis": [1, 1, 1], "hamiltonian_coeff": 1.0, "H": hamiltonian(n111, 1.0), "jumps": [], "jump_names": [], "chirality": "L"}
    if name == "Ne_Spiral_R":
        return {"hamiltonian_axis": [1, 1, 1], "hamiltonian_coeff": -1.0, "H": hamiltonian(n111, -1.0), "jumps": [], "jump_names": [], "chirality": "R"}
    if name == "Ni_Pit_L":
        return {"hamiltonian_axis": [1, 1, 1], "hamiltonian_coeff": 1 / 5, "H": hamiltonian(n111, 1 / 5), "jumps": [math.sqrt(1 / 2) * SIGMA_MINUS], "jump_names": ["sqrt(1/2)*sigma_minus_to_-z"], "chirality": "L"}
    if name == "Ni_Source_R":
        return {"hamiltonian_axis": [1, 1, 1], "hamiltonian_coeff": -1 / 5, "H": hamiltonian(n111, -1 / 5), "jumps": [math.sqrt(1 / 2) * SIGMA_PLUS], "jump_names": ["sqrt(1/2)*sigma_plus_to_+z"], "chirality": "R"}
    if name == "Si_Hill_L":
        return {"hamiltonian_axis": [0, 0, 1], "hamiltonian_coeff": 1 / 5, "H": hamiltonian(np.array([0.0, 0.0, 1.0]), 1 / 5), "jumps": [math.sqrt(2 / 5) * PZ_PLUS, math.sqrt(2 / 5) * PZ_MINUS], "jump_names": ["sqrt(2/5)*P_z_plus", "sqrt(2/5)*P_z_minus"], "chirality": "L"}
    if name == "Si_Citadel_R":
        return {"hamiltonian_axis": [1, 0, 0], "hamiltonian_coeff": 1 / 5, "H": hamiltonian(np.array([1.0, 0.0, 0.0]), 1 / 5), "jumps": [math.sqrt(2 / 5) * PX_PLUS, math.sqrt(2 / 5) * PX_MINUS], "jump_names": ["sqrt(2/5)*P_x_plus", "sqrt(2/5)*P_x_minus"], "chirality": "R"}
    raise KeyError(name)


def weyl_sheet_spec(name: str, sheet: str) -> dict[str, Any]:
    spec = native_lift_spec(name)
    coeff_mag = abs(float(spec["hamiltonian_coeff"]))
    sheet_sign = 1.0 if sheet == "L" else -1.0
    n111 = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)
    return {
        **spec,
        "sheet": sheet,
        "hamiltonian_axis": [1, 1, 1],
        "hamiltonian_coeff": sheet_sign * coeff_mag,
        "H": hamiltonian(n111, sheet_sign * coeff_mag),
        "sheet_override": "H_L=+H0, H_R=-H0 with each terrain dissipator kept fixed",
    }


def lindblad_rhs(rho: np.ndarray, H: np.ndarray, jumps: list[np.ndarray]) -> np.ndarray:
    out = -1.0j * (H @ rho - rho @ H)
    for jump in jumps:
        jd = jump.conj().T
        out = out + jump @ rho @ jd - 0.5 * (jd @ jump @ rho + rho @ jd @ jump)
    return out


def liouvillian(H: np.ndarray, jumps: list[np.ndarray]) -> np.ndarray:
    basis = []
    for i in range(2):
        for j in range(2):
            e = np.zeros((2, 2), dtype=complex)
            e[i, j] = 1.0
            basis.append(e)
    L = np.zeros((4, 4), dtype=complex)
    for col, e in enumerate(basis):
        L[:, col] = lindblad_rhs(e, H, jumps).reshape(4)
    return L


def density_from_bloch(r: np.ndarray) -> np.ndarray:
    return 0.5 * (IDENT2 + r[0] * SX + r[1] * SY + r[2] * SZ)


def bloch_from_density(rho: np.ndarray) -> np.ndarray:
    return np.array([
        np.real(np.trace(rho @ SX)),
        np.real(np.trace(rho @ SY)),
        np.real(np.trace(rho @ SZ)),
    ])


def density_evolve(spec: dict[str, Any], r0: np.ndarray, t: float) -> np.ndarray:
    rho0 = density_from_bloch(r0)
    L = liouvillian(spec["H"], spec["jumps"])
    return scipy.linalg.expm(L * t) @ rho0.reshape(4)


def bloch_evolve_from_lift(spec: dict[str, Any], r0: np.ndarray, t: float) -> np.ndarray:
    rho_t = density_evolve(spec, r0, t).reshape((2, 2))
    rho_t = 0.5 * (rho_t + rho_t.conj().T)
    return bloch_from_density(rho_t)


def affine_evolve(A: sp.Matrix, b: sp.Matrix, r0: np.ndarray, t: float) -> np.ndarray:
    A_np = np.array(A.tolist(), dtype=float)
    b_np = np.array([float(v) for v in b], dtype=float)
    aug = np.zeros((4, 4), dtype=float)
    aug[:3, :3] = A_np
    aug[:3, 3] = b_np
    start = np.array([r0[0], r0[1], r0[2], 1.0], dtype=float)
    return (scipy.linalg.expm(aug * t) @ start)[:3]


def spinor(theta: float, phi: float, global_phase: float = 0.0) -> np.ndarray:
    return np.exp(1.0j * global_phase) * np.array([
        math.cos(theta / 2.0),
        np.exp(1.0j * phi) * math.sin(theta / 2.0),
    ], dtype=complex)


def spinor_density(psi: np.ndarray) -> np.ndarray:
    psi = psi / np.linalg.norm(psi)
    return np.outer(psi, psi.conj())


def canonical_complex_list(vec: np.ndarray) -> list[list[float]]:
    return [[float(np.real(x)), float(np.imag(x))] for x in vec.ravel()]


def mirror_rows(gens: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    proof_exprs_sigma_y: list[sp.Expr] = []
    proof_exprs_wrong: list[sp.Expr] = []
    proof_exprs_erased: list[sp.Expr] = []
    for family, (left, right) in FAMILY_PAIRS.items():
        A_l, b_l = gens[left]["A"], gens[left]["b"]
        A_r, b_r = gens[right]["A"], gens[right]["b"]
        exact_A = sp.simplify(A_r - M_SIGMA_Y * A_l * M_SIGMA_Y)
        exact_b = sp.simplify(b_r - M_SIGMA_Y * b_l)
        wrong_A = sp.simplify(A_r - M_SIGMA_X * A_l * M_SIGMA_X)
        wrong_b = sp.simplify(b_r - M_SIGMA_X * b_l)
        erased_A = sp.simplify(A_r - A_l)
        erased_b = sp.simplify(b_r - b_l)
        exact_exprs = list(exact_A) + list(exact_b)
        wrong_exprs = list(wrong_A) + list(wrong_b)
        erased_exprs = list(erased_A) + list(erased_b)
        row = {
            "family": family,
            "left_generator": left,
            "right_generator": right,
            "sigma_y_residual_A": matrix_strings(exact_A),
            "sigma_y_residual_b": vector_strings(exact_b),
            "sigma_y_exact": all(sp.simplify(x) == 0 for x in exact_exprs),
            "sigma_y_max_abs_residual": max_abs_sympy(exact_exprs),
            "wrong_sigma_x_exact": all(sp.simplify(x) == 0 for x in wrong_exprs),
            "wrong_sigma_x_max_abs_residual": max_abs_sympy(wrong_exprs),
            "chirality_erased_identity_exact": all(sp.simplify(x) == 0 for x in erased_exprs),
            "chirality_erased_identity_max_abs_residual": max_abs_sympy(erased_exprs),
        }
        rows.append(row)
        proof_exprs_sigma_y.extend(exact_exprs)
        if family == "Se":
            proof_exprs_wrong.extend(wrong_exprs)
            proof_exprs_erased.extend(erased_exprs)
    sigma_y_scaled = scaled_coefficients(proof_exprs_sigma_y)
    wrong_scaled = scaled_coefficients(proof_exprs_wrong)
    erased_scaled = scaled_coefficients(proof_exprs_erased)
    smt = {
        "computed_sigma_y_residuals_have_nonzero_entries": {
            "scaled_coefficients": sigma_y_scaled,
            "z3": z3_nonzero_unsat(sigma_y_scaled["values"], "computed_sigma_y_residuals_have_nonzero_entries"),
            "cvc5": cvc5_nonzero_unsat(sigma_y_scaled["values"], "computed_sigma_y_residuals_have_nonzero_entries"),
            "pass": True,
        },
        "sigma_y_forced_exact_all_pairs_control": {
            "scaled_coefficients": sigma_y_scaled,
            "z3": z3_zero_forced_unsat(sigma_y_scaled["values"], "sigma_y_forced_exact_all_pairs_control"),
            "cvc5": cvc5_zero_forced_unsat(sigma_y_scaled["values"], "sigma_y_forced_exact_all_pairs_control"),
            "pass": True,
        },
        "wrong_sigma_x_se_forced_exact_control": {
            "scaled_coefficients": wrong_scaled,
            "z3": z3_zero_forced_unsat(wrong_scaled["values"], "wrong_sigma_x_se_forced_exact_control"),
            "cvc5": cvc5_zero_forced_unsat(wrong_scaled["values"], "wrong_sigma_x_se_forced_exact_control"),
            "pass": True,
        },
        "chirality_erased_identity_se_forced_exact_control": {
            "scaled_coefficients": erased_scaled,
            "z3": z3_zero_forced_unsat(erased_scaled["values"], "chirality_erased_identity_se_forced_exact_control"),
            "cvc5": cvc5_zero_forced_unsat(erased_scaled["values"], "chirality_erased_identity_se_forced_exact_control"),
            "pass": True,
        },
    }
    for key, row in smt.items():
        if key == "computed_sigma_y_residuals_have_nonzero_entries":
            row["pass"] = row["z3"]["status"] == "sat" and row["cvc5"]["status"] == "sat"
        else:
            row["pass"] = row["z3"]["status"] == "unsat" and row["cvc5"]["status"] == "unsat"
    return rows, smt


def projection_rows(gens: dict[str, dict[str, Any]], s5: dict[str, Any]) -> dict[str, Any]:
    r0 = np.array([1 / 5, -2 / 5, 1 / 3], dtype=float)
    t = 1.0
    rows = []
    for name in sorted(gens):
        spec = native_lift_spec(name)
        r_lift = bloch_evolve_from_lift(spec, r0, t)
        r_affine = affine_evolve(gens[name]["A"], gens[name]["b"], r0, t)
        resid = float(np.max(np.abs(r_lift - r_affine)))
        rows.append({
            "generator": name,
            "time": t,
            "r0": [float(x) for x in r0],
            "lift_projected_bloch": [float(x) for x in r_lift],
            "committed_affine_bloch": [float(x) for x in r_affine],
            "max_abs_projection_residual": resid,
            "pass": resid <= 2.0e-12,
        })
    se_special = find_exact_special_case(s5, "Se_Funnel_L")
    if se_special is None:
        raise KeyError("Se_Funnel_L exact_special_case_check not found in committed S5 result")
    se_target = np.array(se_special["r_t"], dtype=float)
    se_lift = bloch_evolve_from_lift(native_lift_spec("Se_Funnel_L"), r0, t)
    se_affine = affine_evolve(gens["Se_Funnel_L"]["A"], gens["Se_Funnel_L"]["b"], r0, t)
    se_gap = {
        "anchor": "Se_Funnel_L lift projects to committed special-case trajectory and carries Bloch Hamiltonian frequency squared 4/25",
        "source_note": "No literal 4/25 field was present in committed S5 result; this row computes 4*(1/5)^2 from the lifted Se Hamiltonian coefficient.",
        "hamiltonian_coeff": "1/5",
        "bloch_angular_frequency_squared": "4/25",
        "r0": [float(x) for x in r0],
        "time": t,
        "committed_special_case_method": se_special.get("method"),
        "committed_special_case_role": se_special.get("role"),
        "lift_projected_bloch": [float(x) for x in se_lift],
        "committed_special_case_bloch": [float(x) for x in se_target],
        "committed_affine_bloch": [float(x) for x in se_affine],
        "lift_vs_special_case_max_abs_residual": float(np.max(np.abs(se_lift - se_target))),
        "lift_vs_affine_max_abs_residual": float(np.max(np.abs(se_lift - se_affine))),
        "pass": float(np.max(np.abs(se_lift - se_target))) <= 2.0e-12,
    }
    return {
        "native_lift_projection_rows": rows,
        "max_native_projection_residual": max(row["max_abs_projection_residual"] for row in rows),
        "se_funnel_l_gap_4_25_anchor": se_gap,
        "pass": all(row["pass"] for row in rows) and se_gap["pass"],
    }


def sheet_rows(gens: dict[str, dict[str, Any]]) -> dict[str, Any]:
    r0 = np.array([1 / 5, -2 / 5, 1 / 3], dtype=float)
    rows = []
    for name in sorted(gens):
        native_sheet = native_lift_spec(name)["chirality"]
        for sheet in ("L", "R"):
            spec = weyl_sheet_spec(name, sheet)
            r_sheet = bloch_evolve_from_lift(spec, r0, 1.0)
            r_committed = affine_evolve(gens[name]["A"], gens[name]["b"], r0, 1.0)
            resid = float(np.max(np.abs(r_sheet - r_committed)))
            rows.append({
                "generator": name,
                "computed_sheet": sheet,
                "native_label_sheet": native_sheet,
                "sheet_override": spec["sheet_override"],
                "hamiltonian_axis": spec["hamiltonian_axis"],
                "hamiltonian_coeff": spec["hamiltonian_coeff"],
                "jump_names": spec["jump_names"],
                "projected_bloch": [float(x) for x in r_sheet],
                "committed_same_generator_bloch": [float(x) for x in r_committed],
                "projection_residual_vs_committed_same_generator": resid,
                "native_label_sheet_projection_exact": sheet == native_sheet and resid <= 2.0e-12,
            })
    native_failures = [row for row in rows if row["computed_sheet"] == row["native_label_sheet"] and not row["native_label_sheet_projection_exact"]]
    return {
        "unraveling_convention": "standard quantum-jump unraveling: K_eff=-iH-1/2 sum_j L_j^dagger L_j for no-jump drift, jump maps psi -> L_j psi/||L_j psi||, ensemble density obeys the Lindblad generator. This is a choice; the density generator is the invariant object.",
        "rows": rows,
        "native_label_sheet_failures": native_failures,
        "finding": "Se/Ne/Ni native L/R labels are compatible with H_L=+H0 and H_R=-H0. Si native rows use z/x dephasing frames, so the H0 sheet override is not the committed Si dynamics.",
    }


def quotient_erasure_rows(nonassoc: dict[str, Any]) -> dict[str, Any]:
    theta = 0.91
    phi = -0.43
    psi0 = spinor(theta, phi)
    psi_phase = spinor(theta, phi, global_phase=math.pi / 2)
    rho0 = spinor_density(psi0)
    rho_phase = spinor_density(psi_phase)
    n111 = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)
    H = hamiltonian(n111, 1.0)
    U_2pi_bloch = scipy.linalg.expm(-1.0j * math.pi * H)
    psi_flip = U_2pi_bloch @ psi0
    rho_flip = spinor_density(psi_flip)
    committed_b1 = find_density_erasure_row(nonassoc)
    if committed_b1 is None:
        raise KeyError("committed nonassoc density-erasure row not found")
    return {
        "picked_terrains": ["Ne_Vortex_L", "Ne_Spiral_R"],
        "phase_row": {
            "spinor_distance": float(np.linalg.norm(psi0 - psi_phase)),
            "density_gap_norm": float(np.linalg.norm(rho0 - rho_phase)),
            "erased_by_density_quotient": float(np.linalg.norm(rho0 - rho_phase)) <= TOL,
        },
        "two_pi_flip_row": {
            "terrain": "Ne_Vortex_L",
            "H": "H0=(sigma_x+sigma_y+sigma_z)/sqrt(3)",
            "time": "pi gives Bloch 2pi rotation for H0",
            "spinor_after": canonical_complex_list(psi_flip),
            "spinor_distance_to_initial": float(np.linalg.norm(psi_flip - psi0)),
            "spinor_distance_to_negative_initial": float(np.linalg.norm(psi_flip + psi0)),
            "density_return_gap_norm": float(np.linalg.norm(rho_flip - rho0)),
            "erased_by_bloch_density_quotient": float(np.linalg.norm(rho_flip - rho0)) <= TOL,
        },
        "committed_nonassoc_b1_precedent": {
            "source": str(NONASSOC_PATH.relative_to(ROOT)),
            "visible_on_lifted_spinor_row": committed_b1.get("visible_on_lifted_spinor_row"),
            "erased_under_density_quotient": committed_b1.get("erased_under_density_quotient"),
            "spinor_gap_norm": committed_b1.get("spinor_gap_norm"),
            "density_gap_norm": committed_b1.get("density_gap_norm"),
        },
        "pass": float(np.linalg.norm(rho0 - rho_phase)) <= TOL and float(np.linalg.norm(rho_flip - rho0)) <= TOL,
    }


def chirality_readout_rows(gens: dict[str, dict[str, Any]]) -> dict[str, Any]:
    times = [0.0, 0.25, 0.5, 1.0, 1.5]
    r_l0 = np.array([1 / 5, -2 / 5, 1 / 3], dtype=float)
    M = np.diag([-1.0, 1.0, -1.0])
    r_r0 = M @ r_l0
    rows = []
    for family, (left, right) in FAMILY_PAIRS.items():
        for t in times:
            r_l = affine_evolve(gens[left]["A"], gens[left]["b"], r_l0, t)
            r_r = affine_evolve(gens[right]["A"], gens[right]["b"], r_r0, t)
            rows.append({
                "family": family,
                "time": t,
                "left_generator": left,
                "right_generator": right,
                "gamma5_odd_sigma_z_L_minus_R": float(r_l[2] - r_r[2]),
                "mirror_counterpart_residual": float(np.max(np.abs(r_r - M @ r_l))),
            })
    blind = []
    for t in times:
        r_l = affine_evolve(gens["Se_Funnel_L"]["A"], gens["Se_Funnel_L"]["b"], r_l0, t)
        r_r = affine_evolve(gens["Se_Funnel_L"]["A"], gens["Se_Funnel_L"]["b"], r_l0, t)
        blind.append({
            "time": t,
            "generator_on_both_sheets": "Se_Funnel_L",
            "gamma5_odd_sigma_z_L_minus_R": float(r_l[2] - r_r[2]),
        })
    wrong_mirror = []
    Mx = np.diag([1.0, -1.0, -1.0])
    for t in times:
        r_l = affine_evolve(gens["Se_Funnel_L"]["A"], gens["Se_Funnel_L"]["b"], r_l0, t)
        r_r_wrong = affine_evolve(gens["Se_Cannon_R"]["A"], gens["Se_Cannon_R"]["b"], Mx @ r_l0, t)
        wrong_mirror.append({
            "time": t,
            "wrong_sigma_x_counterpart_residual": float(np.max(np.abs(r_r_wrong - Mx @ r_l))),
        })
    return {
        "observable": "<sigma_z>_L - <sigma_z>_R",
        "initial_left_bloch": [float(x) for x in r_l0],
        "initial_right_bloch_sigma_y_mirror": [float(x) for x in r_r0],
        "mirror_paired_timeseries": rows,
        "chirality_blind_control": blind,
        "wrong_mirror_control": wrong_mirror,
        "max_blind_abs_signal": max(abs(x["gamma5_odd_sigma_z_L_minus_R"]) for x in blind),
        "max_sigma_y_mirror_residual_se_ne_ni": max(x["mirror_counterpart_residual"] for x in rows if x["family"] in {"Se", "Ne", "Ni"}),
        "si_mirror_residual_max": max(x["mirror_counterpart_residual"] for x in rows if x["family"] == "Si"),
        "pass": max(abs(x["gamma5_odd_sigma_z_L_minus_R"]) for x in blind) <= TOL,
    }


def permuted_control(gens: dict[str, dict[str, Any]]) -> dict[str, Any]:
    r0 = np.array([1 / 5, -2 / 5, 1 / 3], dtype=float)
    target = affine_evolve(gens["Se_Funnel_L"]["A"], gens["Se_Funnel_L"]["b"], r0, 1.0)
    wrong = bloch_evolve_from_lift(native_lift_spec("Ne_Vortex_L"), r0, 1.0)
    residual = float(np.max(np.abs(wrong - target)))
    return {
        "control": "permuted generator: Ne_Vortex_L lift tested against Se_Funnel_L committed anchor",
        "residual": residual,
        "breaks_anchor": residual > 1.0e-3,
        "pass": residual > 1.0e-3,
    }


def lineage(s5: dict[str, Any], s1: dict[str, Any], s2s5: dict[str, Any], nonassoc: dict[str, Any]) -> dict[str, Any]:
    return {
        "consumed_inputs": [
            {"path": str(S5_PATH.relative_to(ROOT)), "sha256": sha256_file(S5_PATH), "expected_sha256": EXPECTED_S5_RESULT_HASH, "role": "committed S5 terrain affine generators consumed by hash"},
            {"path": str(S1_PATH.relative_to(ROOT)), "sha256": sha256_file(S1_PATH), "role": "committed S1 Hopf/Weyl spinor and 720-degree quotient rows"},
            {"path": str(S2S5_PATH.relative_to(ROOT)), "sha256": sha256_file(S2S5_PATH), "role": "committed 56/56 S5 quotient-survival matrix"},
            {"path": str(NONASSOC_PATH.relative_to(ROOT)), "sha256": sha256_file(NONASSOC_PATH), "role": "committed spinor-lift-visible/density-erased B1 precedent"},
        ],
        "s5_source_sha256": s5.get("source_sha256"),
        "s5_engine_result_hashes": s5.get("engine_result_hashes"),
        "s5_result_hash_from_mode_sweep_anchor": s2s5.get("anchor_hashes", {}).get("s5_result_hash"),
        "s5_quotient_survival": s2s5.get("quotient_analysis", {}).get("S5"),
        "s1_double_cover_reference": s1.get("results", {}).get("double_cover", [])[:1],
        "nonassoc_density_erasure_reference": find_density_erasure_row(nonassoc),
    }


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    s5 = load_json(S5_PATH)
    s1 = load_json(S1_PATH)
    s2s5 = load_json(S2S5_PATH)
    nonassoc = load_json(NONASSOC_PATH)
    gens = parse_committed_generators(s5)
    mirrors, smt = mirror_rows(gens)
    projections = projection_rows(gens, s5)
    sheets = sheet_rows(gens)
    quotient = quotient_erasure_rows(nonassoc)
    chirality = chirality_readout_rows(gens)
    permuted = permuted_control(gens)
    s5_hash_ok = sha256_file(S5_PATH) == EXPECTED_S5_RESULT_HASH
    exact_families = {row["family"]: row["sigma_y_exact"] for row in mirrors}
    honest_mirror_outcome_ok = exact_families == {"Se": False, "Ne": False, "Ni": False, "Si": False}
    smt_ok = all(row["pass"] for row in smt.values())
    all_pass = all([
        s5_hash_ok,
        projections["pass"],
        quotient["pass"],
        chirality["pass"],
        permuted["pass"],
        honest_mirror_outcome_ok,
        smt_ok,
    ])
    payload = {
        "schema_version": "terrain_weyl_spinor_lr_v0.python_result.v1",
        "sim_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": all_pass,
        "validator_intended_declared_mode": "julia_canon_plus_python_exact_diagnostic",
        "claim_under_test": "Committed S5 L/R terrain suffixes are chirality labels on two Weyl sheets H_L=+H0, H_R=-H0, paired by sigma_y mirror on the Bloch ball.",
        "honest_outcome": "The committed L/R terrain pairs are not exact sigma_y mirrors under M=diag(-1,1,-1). Se, Ne, and Ni leave xz-plane skew residuals because the committed n=(1,1,1) Hamiltonian includes a sigma_y component; Si also fails because its committed L/R rows use z/x frames.",
        "owner_claim_sigma_y_exact_survives": False,
        "tool_manifest": {
            "sympy": {"version": package_version("sympy"), "depth": "load_bearing", "reason": "exact A,b mirror residuals and coefficient extraction"},
            "scipy": {"version": package_version("scipy"), "depth": "load_bearing", "reason": "finite Liouvillian and affine exponentials for lift projection and chirality rows"},
            "z3": {"version": package_version("z3-solver", getattr(z3, "get_version_string", lambda: "unknown")()), "depth": "load_bearing", "reason": "SMT residual identity and negative-control contradiction checks"},
            "cvc5": {"version": package_version("cvc5"), "depth": "load_bearing", "reason": "independent SMT residual identity and negative-control contradiction checks"},
            "numpy": {"version": package_version("numpy"), "depth": "supportive", "reason": "matrix numerics and norms"},
        },
        "tool_calls": [
            {"tool": "sympy", "one_to_one_row": "mirror_pairing_exact_residuals"},
            {"tool": "scipy.linalg.expm", "one_to_one_row": "lift_projection_and_chirality_timeseries"},
            {"tool": "z3", "one_to_one_row": "mirror_residual_identity_with_erased_flip_controls"},
            {"tool": "cvc5", "one_to_one_row": "mirror_residual_identity_with_erased_flip_controls"},
        ],
        "seeds": {"deterministic": True, "random_seed": None},
        "parent_lineage": lineage(s5, s1, s2s5, nonassoc),
        "source_sha256": sha256_file(SOURCE_PATH),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "s5_hash_ok": s5_hash_ok,
        "spinor_lift_rows": sheets,
        "mirror_pairing_rows": mirrors,
        "smt_mirror_residual_identities": smt,
        "quotient_erasure_row": quotient,
        "chirality_readout_row": chirality,
        "consistency_anchors": projections,
        "controls": {
            "chirality_blind": chirality["chirality_blind_control"],
            "wrong_mirror_sigma_x": [row for row in mirrors],
            "permuted_generator": permuted,
            "phase_erased": quotient["phase_row"],
        },
        "positive_negative_boundary": {
            "positive": ["native lift projects back to committed S5 affine trajectories", "2pi spinor sign flip is erased by density quotient", "chirality-blind same-terrain control has zero gamma5-odd signal"],
            "negative": ["sigma_y mirror exactness is false for all four committed L/R pairs", "wrong sigma_x mirror exactness is false for Se", "permuted generator breaks the Se anchor"],
            "boundary": ["quantum-jump spinor unraveling is one convention; density generator is invariant", "scratch diagnostic only; no formal admission"],
        },
    }
    dump_json(RESULT_PATH, payload)
    print(json.dumps({"result_path": str(RESULT_PATH), "all_pass": all_pass, "honest_mirror_outcome_ok": honest_mirror_outcome_ok}, sort_keys=True))


if __name__ == "__main__":
    main()
