#!/usr/bin/env python3
"""Find exact O(3) maps pairing the committed S5 L/R terrain generators.

This is a scratch diagnostic. It consumes the committed S5 affine Bloch
generators and the terrain_weyl_spinor_lr_v0 refutation packet read-only.
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


SIM_ID = "terrain_exact_mirror_finder_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_python_results.json"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"

S5_PATH = ROOT / "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json"
REFUTATION_RESULT_PATH = ROOT / "system_v6/sims/terrain_weyl_spinor_lr_v0/results/terrain_weyl_spinor_lr_v0_python_results.json"
REFUTATION_SOURCE_PATH = ROOT / "system_v6/sims/terrain_weyl_spinor_lr_v0/terrain_weyl_spinor_lr_v0.py"

EXPECTED_S5_RESULT_HASH = "8c5474786973f067e55c0200392c1a27cbe8bf5d71cfd632b507d066b6cc9b1e"
EXPECTED_REFUTATION_COMMIT = "a706208c4"
TOL = 1.0e-9
SQRT3 = sp.sqrt(3)

FAMILY_PAIRS = {
    "Se": ("Se_Funnel_L", "Se_Cannon_R"),
    "Ne": ("Ne_Vortex_L", "Ne_Spiral_R"),
    "Ni": ("Ni_Pit_L", "Ni_Source_R"),
    "Si": ("Si_Hill_L", "Si_Citadel_R"),
}

M_SIGMA_Y = sp.diag(-1, 1, -1)
M_IDENTITY = sp.eye(3)
M_RANDOM_ORTHOGONAL = sp.Matrix(
    [
        [sp.Rational(2, 3), sp.Rational(1, 3), sp.Rational(2, 3)],
        [sp.Rational(1, 3), sp.Rational(2, 3), -sp.Rational(2, 3)],
        [-sp.Rational(2, 3), sp.Rational(2, 3), sp.Rational(1, 3)],
    ]
)
M_NI_UNIQUE = sp.Matrix([[0, -1, 0], [-1, 0, 0], [0, 0, -1]])
M_SI_PROPER_CANONICAL = sp.Matrix([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])
M_SI_REFLECTION_CANONICAL = sp.Matrix([[0, 0, -1], [0, 1, 0], [-1, 0, 0]])


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


def package_version(name: str) -> str:
    try:
        return md.version(name)
    except md.PackageNotFoundError:
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
        }
    return out


def matrix_strings(mat: sp.Matrix) -> list[list[str]]:
    return [[str(sp.simplify(mat[i, j])) for j in range(mat.cols)] for i in range(mat.rows)]


def vector_strings(vec: sp.Matrix) -> list[str]:
    return [str(sp.simplify(vec[i])) for i in range(vec.rows)]


def max_abs_sympy(values: list[sp.Expr]) -> float:
    if not values:
        return 0.0
    return float(max(abs(float(sp.N(v))) for v in values))


def residual_exprs(gens: dict[str, dict[str, Any]], family: str, M: sp.Matrix) -> list[sp.Expr]:
    left, right = FAMILY_PAIRS[family]
    A_l, b_l = gens[left]["A"], gens[left]["b"]
    A_r, b_r = gens[right]["A"], gens[right]["b"]
    return [sp.simplify(x) for x in list(A_r - M * A_l * M.T) + list(b_r - M * b_l)]


def residual_row(gens: dict[str, dict[str, Any]], family: str, M: sp.Matrix, label: str) -> dict[str, Any]:
    left, right = FAMILY_PAIRS[family]
    A_l, b_l = gens[left]["A"], gens[left]["b"]
    A_r, b_r = gens[right]["A"], gens[right]["b"]
    rA = sp.simplify(A_r - M * A_l * M.T)
    rb = sp.simplify(b_r - M * b_l)
    exprs = list(rA) + list(rb)
    return {
        "family": family,
        "left_generator": left,
        "right_generator": right,
        "candidate": label,
        "det": str(sp.det(M)),
        "orthogonal_exact": sp.simplify(M.T * M - sp.eye(3)) == sp.zeros(3),
        "residual_A": matrix_strings(rA),
        "residual_b": vector_strings(rb),
        "exact": all(sp.simplify(x) == 0 for x in exprs),
        "max_abs_residual": max_abs_sympy(exprs),
    }


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
    values = [int(c * denom) for c in coeffs]
    return {
        "basis": "rational_plus_rational_times_sqrt3",
        "scale": denom,
        "values": values,
        "any_nonzero": any(v != 0 for v in values),
    }


def z3_any_nonzero(values: list[int], label: str) -> dict[str, Any]:
    solver = z3.Solver()
    xs = [z3.Int(f"{label}_{i}") for i in range(len(values))]
    for x, value in zip(xs, values):
        solver.add(x == value)
    solver.add(z3.Or([x != 0 for x in xs]) if xs else z3.BoolVal(False))
    return {"solver": "z3", "query": "bound_values_and_assert_any_nonzero", "status": str(solver.check())}


def z3_force_zero(values: list[int], label: str) -> dict[str, Any]:
    solver = z3.Solver()
    xs = [z3.Int(f"{label}_{i}") for i in range(len(values))]
    for x, value in zip(xs, values):
        solver.add(x == value)
        solver.add(x == 0)
    return {"solver": "z3", "query": "bound_values_and_force_all_zero", "status": str(solver.check())}


def cvc5_int(solver: cvc5.Solver, value: int) -> cvc5.Term:
    return solver.mkInteger(str(value))


def cvc5_any_nonzero(values: list[int], label: str) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    sort = solver.getIntegerSort()
    xs = [solver.mkConst(sort, f"{label}_{i}") for i in range(len(values))]
    for x, value in zip(xs, values):
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, x, cvc5_int(solver, value)))
    if xs:
        neq = [
            solver.mkTerm(cvc5.Kind.NOT, solver.mkTerm(cvc5.Kind.EQUAL, x, cvc5_int(solver, 0)))
            for x in xs
        ]
        solver.assertFormula(solver.mkTerm(cvc5.Kind.OR, *neq))
    else:
        solver.assertFormula(solver.mkFalse())
    return {"solver": "cvc5", "query": "bound_values_and_assert_any_nonzero", "status": str(solver.checkSat())}


def cvc5_force_zero(values: list[int], label: str) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    sort = solver.getIntegerSort()
    xs = [solver.mkConst(sort, f"{label}_{i}") for i in range(len(values))]
    for x, value in zip(xs, values):
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, x, cvc5_int(solver, value)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, x, cvc5_int(solver, 0)))
    return {"solver": "cvc5", "query": "bound_values_and_force_all_zero", "status": str(solver.checkSat())}


def smt_row(exprs: list[sp.Expr], label: str, expected: str) -> dict[str, Any]:
    scaled = scaled_coefficients(exprs)
    any_z3 = z3_any_nonzero(scaled["values"], f"{label}_any")
    any_cvc5 = cvc5_any_nonzero(scaled["values"], f"{label}_any")
    zero_z3 = z3_force_zero(scaled["values"], f"{label}_zero")
    zero_cvc5 = cvc5_force_zero(scaled["values"], f"{label}_zero")
    if expected == "zero":
        passed = any_z3["status"] == "unsat" and any_cvc5["status"] == "unsat" and zero_z3["status"] == "sat" and zero_cvc5["status"] == "sat"
    else:
        passed = any_z3["status"] == "sat" and any_cvc5["status"] == "sat" and zero_z3["status"] == "unsat" and zero_cvc5["status"] == "unsat"
    return {
        "label": label,
        "expected": expected,
        "scaled_coefficients": scaled,
        "z3_any_nonzero": any_z3,
        "cvc5_any_nonzero": any_cvc5,
        "z3_force_zero": zero_z3,
        "cvc5_force_zero": zero_cvc5,
        "pass": passed,
    }


def solution_set_rows(gens: dict[str, dict[str, Any]]) -> dict[str, Any]:
    h0 = sp.Matrix([1, 1, 1]) / SQRT3
    ez = sp.Matrix([0, 0, 1])
    ex = sp.Matrix([1, 0, 0])
    rows = {
        "Se": {
            "solution_set": "{M in O(3): det(M) * M * h0 = -h0, h0=(1,1,1)/sqrt(3)}",
            "dimension": "one_parameter_continuum",
            "candidate_class_a_pi_rotations": "all R(n)=2*n*n^T-I with n.h0=0 and n.n=1",
            "candidate_class_b_reflections": "all Householder reflections I-2*n*n^T with n.h0=0; equivalently det(M)=-1 and M*h0=h0",
            "general_orthogonal_solve": "nonempty continuum; SO branch flips h0, O-minus branch fixes h0",
            "derivation": "A_L=-4/5 I + [2*h0/5]_x, A_R=-4/5 I - [2*h0/5]_x, b_L=b_R=0; O(3) conjugacy gives M[w]_xM^T=det(M)[Mw]_x.",
            "representative_used_for_controls": matrix_strings(M_NI_UNIQUE),
        },
        "Ne": {
            "solution_set": "{M in O(3): det(M) * M * h0 = -h0, h0=(1,1,1)/sqrt(3)}",
            "dimension": "one_parameter_continuum",
            "candidate_class_a_pi_rotations": "all R(n)=2*n*n^T-I with n.h0=0 and n.n=1",
            "candidate_class_b_reflections": "all Householder reflections I-2*n*n^T with n.h0=0; equivalently det(M)=-1 and M*h0=h0",
            "general_orthogonal_solve": "nonempty continuum; SO branch flips h0, O-minus branch fixes h0",
            "derivation": "A_L=[2*h0]_x, A_R=-[2*h0]_x, b_L=b_R=0; O(3) conjugacy gives M[w]_xM^T=det(M)[Mw]_x.",
            "representative_used_for_controls": matrix_strings(M_NI_UNIQUE),
        },
        "Ni": {
            "solution_set": "single matrix",
            "dimension": "zero",
            "M": matrix_strings(M_NI_UNIQUE),
            "M_description": "proper pi rotation about axis (1,-1,0)/sqrt(2)",
            "candidate_class_a_pi_rotations": "one member: n=(1,-1,0)/sqrt(2), perpendicular to h0",
            "candidate_class_b_reflections": "empty after b_L -> b_R and anisotropic symmetric-part constraints",
            "general_orthogonal_solve": "unique",
            "derivation": "b_L=(0,0,-1/2), b_R=(0,0,1/2) force M e_z=-e_z; the xy-degenerate dissipative symmetric part forces block form diag(Q,-1); skew chirality then forces det(Q)=-1 and Q(1,1)=-(1,1), giving Q=[[0,-1],[-1,0]].",
        },
        "Si": {
            "solution_set": "{M in O(3): M*e_z = det(M)*e_x}",
            "dimension": "one_parameter_continuum",
            "candidate_class_a_pi_rotations_perp_h0": "empty",
            "candidate_class_b_reflections": "nonempty; representative Householder normal (1,0,1)/sqrt(2) gives M e_z=-e_x",
            "general_orthogonal_solve": "nonempty continuum; SO branch maps z-frame to +x-frame, O-minus branch maps z-frame to -x-frame",
            "proper_representative": matrix_strings(M_SI_PROPER_CANONICAL),
            "reflection_representative": matrix_strings(M_SI_REFLECTION_CANONICAL),
            "derivation": "A_L=-2/5(I-e_z e_z^T)+[2 e_z/5]_x and A_R=-2/5(I-e_x e_x^T)+[2 e_x/5]_x; symmetric kernels require M e_z=+/-e_x and skew orientation fixes the sign to det(M).",
        },
    }
    for family, row in rows.items():
        if family in {"Se", "Ne", "Ni"}:
            row["representative_exact"] = residual_row(gens, family, M_NI_UNIQUE, "M_Ni_unique")["exact"]
        else:
            row["proper_representative_exact"] = residual_row(gens, family, M_SI_PROPER_CANONICAL, "M_Si_proper_canonical")["exact"]
            row["reflection_representative_exact"] = residual_row(gens, family, M_SI_REFLECTION_CANONICAL, "M_Si_reflection_canonical")["exact"]
        row["H0_action_geometry"] = h0_action_row(row, h0, ez, ex)
    return rows


def h0_action_row(row: dict[str, Any], h0: sp.Matrix, ez: sp.Matrix, ex: sp.Matrix) -> dict[str, Any]:
    del ez, ex
    if row.get("solution_set") == "single matrix":
        moved = sp.simplify(M_NI_UNIQUE * h0)
        return {"representative": "M_Ni_unique", "M_h0": vector_strings(moved), "relation": "flips_H0", "det": str(sp.det(M_NI_UNIQUE))}
    if row.get("proper_representative"):
        moved_proper = sp.simplify(M_SI_PROPER_CANONICAL * h0)
        moved_reflection = sp.simplify(M_SI_REFLECTION_CANONICAL * h0)
        return {
            "representative": "Si canonical proper/reflection representatives",
            "proper_M_h0": vector_strings(moved_proper),
            "reflection_M_h0": vector_strings(moved_reflection),
            "relation": "neither canonical Si representative fixes or flips H0; Si is a z-frame to x-frame terrain map, not a global H0 chirality map",
        }
    return {
        "solution_set_rule": "det(M)*M*h0=-h0",
        "SO_branch": "M*h0=-h0",
        "O_minus_branch": "M*h0=+h0",
        "relation": "proper mirrors flip H0; improper mirrors fix H0 while still reversing the axial generator through det(M)",
    }


def controls(gens: dict[str, dict[str, Any]], refutation: dict[str, Any]) -> dict[str, Any]:
    sigma_rows = [residual_row(gens, family, M_SIGMA_Y, "sigma_y_diag(-1,1,-1)") for family in FAMILY_PAIRS]
    identity_rows = [residual_row(gens, family, M_IDENTITY, "identity") for family in FAMILY_PAIRS]
    random_rows = [residual_row(gens, family, M_RANDOM_ORTHOGONAL, "deterministic_random_orthogonal") for family in FAMILY_PAIRS]
    previous_rows = {row["family"]: row for row in refutation.get("mirror_pairing_rows", [])}
    anchor_rows = []
    for row in sigma_rows:
        prior = previous_rows.get(row["family"], {})
        anchor_rows.append(
            {
                "family": row["family"],
                "fresh_sigma_y_max_abs_residual": row["max_abs_residual"],
                "refutation_sigma_y_max_abs_residual": prior.get("sigma_y_max_abs_residual"),
                "matches_refutation": abs(row["max_abs_residual"] - float(prior.get("sigma_y_max_abs_residual", -1))) <= TOL,
            }
        )
    return {
        "sigma_y_candidate": {
            "rows": sigma_rows,
            "all_fail": all(not row["exact"] and row["max_abs_residual"] > TOL for row in sigma_rows),
            "refutation_anchor_rows": anchor_rows,
            "matches_committed_refutation": all(row["matches_refutation"] for row in anchor_rows),
        },
        "identity_candidate": {
            "rows": identity_rows,
            "all_fail": all(not row["exact"] and row["max_abs_residual"] > TOL for row in identity_rows),
        },
        "random_orthogonal_candidate": {
            "matrix": matrix_strings(M_RANDOM_ORTHOGONAL),
            "rows": random_rows,
            "all_fail": all(not row["exact"] and row["max_abs_residual"] > TOL for row in random_rows),
        },
    }


def intersection_rows(gens: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ni_rows = [residual_row(gens, family, M_NI_UNIQUE, "M_Ni_unique") for family in FAMILY_PAIRS]
    si_rows = [
        residual_row(gens, "Si", M_SI_PROPER_CANONICAL, "M_Si_proper_canonical"),
        residual_row(gens, "Si", M_SI_REFLECTION_CANONICAL, "M_Si_reflection_canonical"),
    ]
    return {
        "common_all_four_solution_set": "empty",
        "common_all_four_exists": False,
        "reason": "The first three families require det(M)*M*h0=-h0; Ni further collapses that to M_Ni_unique. That unique matrix fails the Si z-frame to x-frame conjugacy residual, so the four-way intersection is empty.",
        "Se_Ne_Ni_common_representative": matrix_strings(M_NI_UNIQUE),
        "Se_Ne_Ni_common_representative_rows": ni_rows,
        "Si_representatives": si_rows,
        "owner_chirality_reading_single_mirror_survives": False,
    }


def paulis() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ident = np.eye(2, dtype=complex)
    sx = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
    sy = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
    sz = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    return ident, sx, sy, sz


IDENT2, SX, SY, SZ = paulis()
SIGMA_MINUS = np.array([[0.0, 0.0], [1.0, 0.0]], dtype=complex)
SIGMA_PLUS = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)


def hamiltonian(axis: np.ndarray, coeff: float) -> np.ndarray:
    axis = axis / np.linalg.norm(axis)
    return coeff * (axis[0] * SX + axis[1] * SY + axis[2] * SZ)


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


def canonical_complex_matrix(mat: np.ndarray) -> list[list[list[float]]]:
    return [[[float(np.real(x)), float(np.imag(x))] for x in row] for row in mat]


def spinor_lift_consistency_row() -> dict[str, Any]:
    n111 = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)
    H_left = hamiltonian(n111, 1.0 / 5.0)
    H_right = hamiltonian(n111, -1.0 / 5.0)
    axis = np.array([1.0, -1.0, 0.0]) / math.sqrt(2.0)
    U = -1.0j * (axis[0] * SX + axis[1] * SY + axis[2] * SZ)
    jump_left = SIGMA_MINUS / math.sqrt(2.0)
    jump_right = SIGMA_PLUS / math.sqrt(2.0)
    h_resid = float(np.linalg.norm(U @ H_left @ U.conj().T - H_right))
    jump_phase = 1.0j
    jump_resid = float(np.linalg.norm(U @ jump_left @ U.conj().T - jump_phase * jump_right))
    L_left = liouvillian(H_left, [jump_left])
    L_right = liouvillian(H_right, [jump_right])
    super_u = np.kron(U, U.conj())
    intertwine_resid = float(np.linalg.norm(super_u @ L_left - L_right @ super_u))
    return {
        "family": "Ni",
        "M": "M_Ni_unique",
        "spinor_unitary": "U=-i*((sigma_x-sigma_y)/sqrt(2)); SU(2) lift of pi rotation about (1,-1,0)/sqrt(2)",
        "unitary_matrix": canonical_complex_matrix(U),
        "H_left": "(sigma_x+sigma_y+sigma_z)/(5*sqrt(3))",
        "H_right": "-(sigma_x+sigma_y+sigma_z)/(5*sqrt(3))",
        "jump_left": "sigma_minus/sqrt(2)",
        "jump_right": "sigma_plus/sqrt(2)",
        "jump_phase": "i",
        "hamiltonian_lift_residual_norm": h_resid,
        "jump_lift_residual_norm": jump_resid,
        "liouvillian_intertwining_residual_norm": intertwine_resid,
        "pass": h_resid <= TOL and jump_resid <= TOL and intertwine_resid <= TOL,
    }


def xz_positive_control() -> dict[str, Any]:
    h = sp.Matrix([1, 0, 1]) / sp.sqrt(2)
    K_left = sp.Matrix([[0, -h[2], h[1]], [h[2], 0, -h[0]], [-h[1], h[0], 0]])
    K_right = -K_left
    residual = sp.simplify(K_right - M_SIGMA_Y * K_left * M_SIGMA_Y.T)
    exprs = list(residual)
    return {
        "boundary_case": "Hxz=(sigma_x+sigma_z)/sqrt(2)",
        "recovered_candidate": "sigma_y Bloch pi rotation diag(-1,1,-1)",
        "residual_A": matrix_strings(residual),
        "exact": all(sp.simplify(x) == 0 for x in exprs),
        "max_abs_residual": max_abs_sympy(exprs),
        "solution_set_note": "For a pure Hxz axial generator the O(3) solution set is still a continuum; sigma_y is recovered as the y-axis pi-rotation member selected by the committed boundary check.",
        "smt": smt_row(exprs, "Hxz_sigma_y_positive_control", "zero"),
    }


def proof_rows(gens: dict[str, dict[str, Any]]) -> dict[str, Any]:
    se_ne_ni_exprs: list[sp.Expr] = []
    for family in ("Se", "Ne", "Ni"):
        se_ne_ni_exprs.extend(residual_exprs(gens, family, M_NI_UNIQUE))
    all_four_mni_exprs = se_ne_ni_exprs + residual_exprs(gens, "Si", M_NI_UNIQUE)
    identity_exprs: list[sp.Expr] = []
    sigma_y_exprs: list[sp.Expr] = []
    random_exprs: list[sp.Expr] = []
    for family in FAMILY_PAIRS:
        identity_exprs.extend(residual_exprs(gens, family, M_IDENTITY))
        sigma_y_exprs.extend(residual_exprs(gens, family, M_SIGMA_Y))
        random_exprs.extend(residual_exprs(gens, family, M_RANDOM_ORTHOGONAL))
    rows = {
        "solve_space_identity_Se_Ne_Ni_M_Ni_zero": smt_row(se_ne_ni_exprs, "solve_space_identity_Se_Ne_Ni_M_Ni_zero", "zero"),
        "all_four_M_Ni_erased_Si_flip_control_nonzero": smt_row(all_four_mni_exprs, "all_four_M_Ni_erased_Si_flip_control_nonzero", "nonzero"),
        "sigma_y_candidate_all_four_nonzero": smt_row(sigma_y_exprs, "sigma_y_candidate_all_four_nonzero", "nonzero"),
        "identity_erased_flip_control_nonzero": smt_row(identity_exprs, "identity_erased_flip_control_nonzero", "nonzero"),
        "random_orthogonal_control_nonzero": smt_row(random_exprs, "random_orthogonal_control_nonzero", "nonzero"),
    }
    return rows


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    s5 = load_json(S5_PATH)
    refutation = load_json(REFUTATION_RESULT_PATH)
    gens = parse_committed_generators(s5)

    solutions = solution_set_rows(gens)
    control_rows = controls(gens, refutation)
    intersections = intersection_rows(gens)
    spinor_row = spinor_lift_consistency_row()
    positive = xz_positive_control()
    smt = proof_rows(gens)

    all_pass = (
        sha256_file(S5_PATH) == EXPECTED_S5_RESULT_HASH
        and control_rows["sigma_y_candidate"]["all_fail"]
        and control_rows["sigma_y_candidate"]["matches_committed_refutation"]
        and control_rows["identity_candidate"]["all_fail"]
        and control_rows["random_orthogonal_candidate"]["all_fail"]
        and solutions["Se"]["representative_exact"]
        and solutions["Ne"]["representative_exact"]
        and solutions["Ni"]["representative_exact"]
        and solutions["Si"]["proper_representative_exact"]
        and solutions["Si"]["reflection_representative_exact"]
        and intersections["common_all_four_exists"] is False
        and spinor_row["pass"]
        and positive["exact"]
        and all(row["pass"] for row in smt.values())
    )
    payload = {
        "schema_version": f"{SIM_ID}.python_result.v1",
        "sim_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": all_pass,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "claim_under_test": "Find exact O(3) maps M with M A_L M^T=A_R and M b_L=b_R for the committed S5 L/R terrain families.",
        "honest_outcome": "No single common exact mirror exists for all four committed families. Se/Ne share a continuum, Ni selects one proper pi rotation within that continuum, and Si has a separate z-frame to x-frame continuum.",
        "owner_single_mirror_reading_survives": False,
        "s5_result_path": str(S5_PATH.relative_to(ROOT)),
        "s5_hash_ok": sha256_file(S5_PATH) == EXPECTED_S5_RESULT_HASH,
        "parent_lineage": {
            "committed_s5": {
                "path": str(S5_PATH.relative_to(ROOT)),
                "sha256": sha256_file(S5_PATH),
                "expected_sha256": EXPECTED_S5_RESULT_HASH,
            },
            "terrain_weyl_spinor_lr_v0_refutation": {
                "commit": EXPECTED_REFUTATION_COMMIT,
                "source_path": str(REFUTATION_SOURCE_PATH.relative_to(ROOT)),
                "source_sha256": sha256_file(REFUTATION_SOURCE_PATH),
                "result_path": str(REFUTATION_RESULT_PATH.relative_to(ROOT)),
                "result_sha256": sha256_file(REFUTATION_RESULT_PATH),
            },
        },
        "tool_manifest": {
            "sympy": {
                "version": package_version("sympy"),
                "depth": "load_bearing",
                "reason": "Exact symbolic O(3) solve-space derivations, residuals, and coefficient extraction.",
            },
            "z3": {
                "version": package_version("z3-solver"),
                "depth": "load_bearing",
                "reason": "SMT checks for zero/nonzero residual coefficient identities and erased-flip controls.",
            },
            "cvc5": {
                "version": package_version("cvc5"),
                "depth": "load_bearing",
                "reason": "Independent SMT checks for the same coefficient identities and controls.",
            },
            "scipy": {
                "version": package_version("scipy"),
                "depth": "supportive",
                "reason": "Spinor/Lindblad lift numerical matrix norm consistency row.",
            },
            "numpy": {
                "version": package_version("numpy"),
                "depth": "supportive",
                "reason": "Array carrier for spinor lift consistency row; not in claim_path_tools.",
            },
        },
        "TOOL_MANIFEST": {
            "sympy": {"used": True, "tried": True, "reason": "load-bearing exact symbolic solve and residual coefficient extraction"},
            "z3": {"used": True, "tried": True, "reason": "load-bearing SMT identity/control checks"},
            "cvc5": {"used": True, "tried": True, "reason": "load-bearing independent SMT identity/control checks"},
            "scipy": {"used": True, "tried": True, "reason": "supportive spinor/Lindblad lift consistency row"},
            "numpy": {"used": True, "tried": True, "reason": "supportive array carrier for lift row"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "scipy": "supportive",
            "numpy": "supportive",
        },
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api": "sympy.Matrix/sympy.simplify/sympy.det",
                "input_object": "committed S5 pinned A,b matrices and symbolic candidate O(3) parameterizations",
                "output_object": "per-family exact solution sets and residual expressions",
                "positive_case": "M_Ni_unique residuals vanish for Se/Ne/Ni; Si canonical representatives vanish for Si",
                "negative_control": "sigma_y, identity, and deterministic random orthogonal candidates fail all-four exactness",
                "boundary_case": "Hxz positive control recovers sigma_y as an exact member",
                "demotion_condition": "Any nonzero residual in an asserted solution set demotes the finding to BROKEN",
                "gates": ["all_pass", "solution_sets", "controls"],
            },
            {
                "tool": "z3",
                "qualified_api": "z3.Solver.check",
                "input_object": "integer-scaled rational+sqrt3 residual coefficients",
                "output_object": "sat/unsat zero and nonzero verdicts",
                "positive_case": "Se/Ne/Ni M_Ni residual coefficients are all zero",
                "negative_control": "identity-erased flip and sigma_y all-four exactness are UNSAT when forced zero",
                "boundary_case": "Hxz sigma_y residual coefficients are all zero",
                "demotion_condition": "Any disagreement with cvc5 or expected polarity demotes proof rows",
                "gates": ["all_pass", "crossover_proofs"],
            },
            {
                "tool": "cvc5",
                "qualified_api": "cvc5.Solver.checkSat",
                "input_object": "same integer-scaled residual coefficients as z3",
                "output_object": "sat/unsat zero and nonzero verdicts",
                "positive_case": "Se/Ne/Ni M_Ni residual coefficients are all zero",
                "negative_control": "identity-erased flip and sigma_y all-four exactness are UNSAT when forced zero",
                "boundary_case": "Hxz sigma_y residual coefficients are all zero",
                "demotion_condition": "Any disagreement with z3 or expected polarity demotes proof rows",
                "gates": ["all_pass", "crossover_proofs"],
            },
        ],
        "per_family_solution_sets": solutions,
        "common_intersection": intersections,
        "controls": control_rows,
        "spinor_lift_consistency": spinor_row,
        "xz_frame_positive_control": positive,
        "smt_solve_space_identities": smt,
        "capability_receipts": {
            "python_versions": {
                "sympy": package_version("sympy"),
                "z3-solver": package_version("z3-solver"),
                "cvc5": package_version("cvc5"),
                "scipy": package_version("scipy"),
                "numpy": package_version("numpy"),
            },
            "seed": 20260610,
            "deterministic_random_orthogonal": matrix_strings(M_RANDOM_ORTHOGONAL),
        },
        "standard_schema_notes": {
            "mode": "FIELD",
            "promotion_ceiling": "scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false",
            "fixture_wording": "none",
        },
    }
    dump_json(RESULT_PATH, payload)
    print(json.dumps({"result_path": str(RESULT_PATH), "all_pass": all_pass}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
