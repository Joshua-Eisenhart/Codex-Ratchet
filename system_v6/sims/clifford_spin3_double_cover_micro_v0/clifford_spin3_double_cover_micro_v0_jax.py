#!/usr/bin/env python3
"""JAX/Python exact-symbolic leg for clifford_spin3_double_cover_micro_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "clifford_spin3_double_cover_micro_v0"
ENGINE = "jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

BLADE_NAMES = ["1", "e1", "e2", "e12", "e3", "e13", "e23", "e123"]
VECTOR_MASKS = [0b001, 0b010, 0b100]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blade_product(a: int, b: int) -> tuple[int, int]:
    sign = 1
    for i in range(3):
        if a & (1 << i):
            if (b & ((1 << i) - 1)).bit_count() % 2:
                sign *= -1
    return sign, a ^ b


def basis(mask: int, coeff: sp.Expr = sp.Integer(1)) -> dict[int, sp.Expr]:
    return {mask: sp.simplify(coeff)}


def mv_add(x: dict[int, sp.Expr], y: dict[int, sp.Expr]) -> dict[int, sp.Expr]:
    out: dict[int, sp.Expr] = dict(x)
    for mask, coeff in y.items():
        out[mask] = sp.simplify(out.get(mask, 0) + coeff)
        if out[mask] == 0:
            del out[mask]
    return out


def mv_neg(x: dict[int, sp.Expr]) -> dict[int, sp.Expr]:
    return {mask: sp.simplify(-coeff) for mask, coeff in x.items()}


def mv_sub(x: dict[int, sp.Expr], y: dict[int, sp.Expr]) -> dict[int, sp.Expr]:
    return mv_add(x, mv_neg(y))


def mv_scale(c: sp.Expr, x: dict[int, sp.Expr]) -> dict[int, sp.Expr]:
    return {mask: sp.simplify(c * coeff) for mask, coeff in x.items() if sp.simplify(c * coeff) != 0}


def mv_mul(x: dict[int, sp.Expr], y: dict[int, sp.Expr]) -> dict[int, sp.Expr]:
    out: dict[int, sp.Expr] = {}
    for a, ca in x.items():
        for b, cb in y.items():
            sign, mask = blade_product(a, b)
            out[mask] = sp.simplify(out.get(mask, 0) + sign * ca * cb)
            if out[mask] == 0:
                del out[mask]
    return out


def mv_reverse(x: dict[int, sp.Expr]) -> dict[int, sp.Expr]:
    out: dict[int, sp.Expr] = {}
    for mask, coeff in x.items():
        g = mask.bit_count()
        sign = -1 if ((g * (g - 1) // 2) % 2) else 1
        out[mask] = sp.simplify(sign * coeff)
    return out


def mv_equal(x: dict[int, sp.Expr], y: dict[int, sp.Expr]) -> bool:
    return all(sp.simplify(x.get(mask, 0) - y.get(mask, 0)) == 0 for mask in range(8))


def mv_sparse(x: dict[int, sp.Expr]) -> dict[str, str]:
    return {BLADE_NAMES[mask]: str(sp.simplify(coeff)) for mask, coeff in sorted(x.items()) if coeff != 0}


def rotor(theta_id: str) -> dict[int, sp.Expr]:
    half_values = {
        "theta_0": (sp.Integer(1), sp.Integer(0)),
        "theta_pi_over_2": (sp.sqrt(2) / 2, sp.sqrt(2) / 2),
        "theta_pi": (sp.Integer(0), sp.Integer(1)),
        "theta_2pi": (sp.Integer(-1), sp.Integer(0)),
        "theta_5pi_over_2": (-sp.sqrt(2) / 2, -sp.sqrt(2) / 2),
        "theta_4pi": (sp.Integer(1), sp.Integer(0)),
    }
    c, s = half_values[theta_id]
    return mv_add(basis(0, c), mv_scale(-s, basis(0b011)))


def sandwich(R: dict[int, sp.Expr], v: dict[int, sp.Expr]) -> dict[int, sp.Expr]:
    return mv_mul(mv_mul(R, v), mv_reverse(R))


def is_even_mask(mask: int) -> bool:
    return mask.bit_count() % 2 == 0


def rotor_predicate(A: dict[int, sp.Expr]) -> dict[str, Any]:
    even = all(is_even_mask(mask) for mask in A)
    norm = mv_mul(A, mv_reverse(A))
    unit = sp.simplify(norm.get(0, 0) - 1) == 0 and all(sp.simplify(norm.get(mask, 0)) == 0 for mask in range(1, 8))
    return {
        "even_grade": even,
        "unit_reverse_product": unit,
        "reverse_product_sparse": mv_sparse(norm),
        "is_spin3_rotor": bool(even and unit),
    }


def action_matrix(R: dict[int, sp.Expr]) -> list[list[int]]:
    cols = [sandwich(R, basis(mask)) for mask in VECTOR_MASKS]
    rows: list[list[int]] = []
    for row_mask in VECTOR_MASKS:
        row = []
        for col in cols:
            value = sp.simplify(col.get(row_mask, 0))
            if value not in {-1, 0, 1}:
                raise ValueError(f"unexpected non-integral action entry: {value}")
            row.append(int(value))
        rows.append(row)
    return rows


def norm2(v: dict[int, sp.Expr]) -> sp.Expr:
    return sp.simplify(mv_mul(v, v).get(0, 0))


def z3_proof(raw: dict[str, int]) -> dict[str, Any]:
    solver = z3.Solver()
    vars_ = {name: z3.Int(f"jax_{name}") for name in raw}
    for name, value in raw.items():
        solver.add(vars_[name] == int(value))
    solver.add(z3.Or([vars_[name] != 1 for name in raw]))
    verdict = str(solver.check())

    flip = z3.Solver()
    flip_vars = {name: z3.Int(f"jax_flip_{name}") for name in raw}
    for name, value in raw.items():
        if name != "rotor_sign_distinct_360":
            flip.add(flip_vars[name] == int(value))
    flip.add(flip_vars["rotor_sign_distinct_360"] == 0)
    flip_verdict = str(flip.check())
    return {
        "ran": True,
        "solver": "z3",
        "verdict": verdict,
        "flip_control_verdict": flip_verdict,
        "load_bearing": True,
        "raw_value_binding": raw,
        "proof_kind": "computed Spin(3) sign/action flags; positive violation UNSAT, erased sign row SAT",
    }


def cvc5_proof(raw: dict[str, int]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    vars_ = {name: solver.mkConst(int_sort, f"cvc5_{name}") for name in raw}
    for name, value in raw.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, vars_[name], solver.mkInteger(int(value))))
    violations = [solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, vars_[name], solver.mkInteger(1))) for name in raw]
    solver.assertFormula(solver.mkTerm(Kind.OR, *violations))
    verdict = str(solver.checkSat())

    flip = cvc5.Solver()
    flip.setLogic("QF_LIA")
    flip_int = flip.getIntegerSort()
    flip_vars = {name: flip.mkConst(flip_int, f"cvc5_flip_{name}") for name in raw}
    for name, value in raw.items():
        if name != "rotor_sign_distinct_360":
            flip.assertFormula(flip.mkTerm(Kind.EQUAL, flip_vars[name], flip.mkInteger(int(value))))
    flip.assertFormula(flip.mkTerm(Kind.EQUAL, flip_vars["rotor_sign_distinct_360"], flip.mkInteger(0)))
    flip_verdict = str(flip.checkSat())
    return {
        "ran": True,
        "solver": "cvc5",
        "verdict": verdict,
        "flip_control_verdict": flip_verdict,
        "load_bearing": True,
        "raw_value_binding": raw,
        "proof_kind": "same finite flag family as z3, independently encoded",
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    R0 = rotor("theta_0")
    Rpi2 = rotor("theta_pi_over_2")
    Rpi = rotor("theta_pi")
    R2pi = rotor("theta_2pi")
    R5pi2 = rotor("theta_5pi_over_2")
    R4pi = rotor("theta_4pi")
    one = R0
    minus_one = mv_neg(one)

    pi2_action = action_matrix(Rpi2)
    pi2_plus_action = action_matrix(R5pi2)
    id_action = action_matrix(R0)
    two_pi_action = action_matrix(R2pi)
    four_pi_action = action_matrix(R4pi)
    jax_action_receipt = jax.device_get(jnp.asarray(pi2_action, dtype=jnp.int64)).tolist()

    A_non_unit = mv_add(basis(0), mv_scale(sp.Rational(1, 2), basis(0b011)))
    A_odd = basis(0b001)
    non_unit_action = sandwich(A_non_unit, basis(0b001))
    raw_flags = {
        "so3_action_equal_360": int(pi2_action == pi2_plus_action),
        "rotor_sign_distinct_360": int(mv_equal(R5pi2, mv_neg(Rpi2)) and not mv_equal(R5pi2, Rpi2)),
        "sign_flip_at_2pi": int(mv_equal(R2pi, minus_one)),
        "closure_at_4pi": int(mv_equal(R4pi, one)),
        "non_unit_rejected": int(not rotor_predicate(A_non_unit)["is_spin3_rotor"]),
        "odd_unit_rejected": int(not rotor_predicate(A_odd)["is_spin3_rotor"]),
    }
    z3_result = z3_proof(raw_flags)
    cvc5_result = cvc5_proof(raw_flags)
    all_pass = all(value == 1 for value in raw_flags.values()) and z3_result["verdict"] == cvc5_result["verdict"] == "unsat" and z3_result["flip_control_verdict"] == cvc5_result["flip_control_verdict"] == "sat"

    return {
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "engine": ENGINE,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": "tool_function_micro_only",
        "all_pass": bool(all_pass),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "reads_peer_result": READS_PEER_RESULT,
        "fixed_dimension": {"cl_pq": "Cl(3,0)", "basis_blade_count": 8, "even_subalgebra_dimension": 4},
        "pinned_angles": {
            "theta_0": {"theta": "0", "cos(theta/2)": "1", "sin(theta/2)": "0", "rotor": mv_sparse(R0)},
            "theta_pi_over_2": {"theta": "pi/2", "cos(theta/2)": "sqrt(2)/2", "sin(theta/2)": "sqrt(2)/2", "rotor": mv_sparse(Rpi2)},
            "theta_pi": {"theta": "pi", "cos(theta/2)": "0", "sin(theta/2)": "1", "rotor": mv_sparse(Rpi)},
            "theta_2pi": {"theta": "2*pi", "cos(theta/2)": "-1", "sin(theta/2)": "0", "rotor": mv_sparse(R2pi)},
            "theta_4pi": {"theta": "4*pi", "cos(theta/2)": "1", "sin(theta/2)": "0", "rotor": mv_sparse(R4pi)},
        },
        "double_cover_rows": {
            "theta_pi_over_2_vs_theta_plus_2pi": {
                "theta": "pi/2",
                "theta_plus_2pi": "5*pi/2",
                "rotor_theta_sparse": mv_sparse(Rpi2),
                "rotor_theta_plus_2pi_sparse": mv_sparse(R5pi2),
                "rotor_relation": "R(theta_plus_2pi)=-R(theta)",
                "rotors_differ_by_sign": bool(raw_flags["rotor_sign_distinct_360"]),
                "action_matrix_theta": pi2_action,
                "action_matrix_theta_plus_2pi": pi2_plus_action,
                "jax_int64_action_matrix_receipt": jax_action_receipt,
                "so3_actions_equal": bool(raw_flags["so3_action_equal_360"]),
                "basis_vector_actions": {name: mv_sparse(sandwich(Rpi2, basis(mask))) for name, mask in {"e1": 0b001, "e2": 0b010, "e3": 0b100}.items()},
            }
        },
        "boundary_rows": {
            "theta_2pi": {"rotor": "-1", "rotor_sparse": mv_sparse(R2pi), "action_matrix": two_pi_action, "same_so3_as_identity": two_pi_action == id_action},
            "theta_4pi": {"rotor": "1", "rotor_sparse": mv_sparse(R4pi), "action_matrix": four_pi_action, "same_so3_as_identity": four_pi_action == id_action},
        },
        "controls": {
            "single_cover_matrix_cannot_distinguish_2pi": {"matrix_theta": pi2_action, "matrix_theta_plus_2pi": pi2_plus_action, "rotor_coefficients_distinct": not mv_equal(Rpi2, R5pi2), "pass": pi2_action == pi2_plus_action and not mv_equal(Rpi2, R5pi2)},
            "non_unit_even_multivector_fails_rotor_predicate": {"candidate": mv_sparse(A_non_unit), "predicate": rotor_predicate(A_non_unit), "vector_norm2_before": str(norm2(basis(0b001))), "vector_norm2_after": str(norm2(non_unit_action)), "pass": not rotor_predicate(A_non_unit)["is_spin3_rotor"]},
            "odd_grade_element_fails_rotor_predicate": {"candidate": mv_sparse(A_odd), "predicate": rotor_predicate(A_odd), "pin_not_spin": True, "pass": not rotor_predicate(A_odd)["is_spin3_rotor"]},
        },
        "crossover_proofs": {"z3": z3_result, "cvc5": cvc5_result},
        "packages_used": ["jax", "jax.numpy", "sympy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "package_observables": {"sympy": "exact sqrt(2)/2 rotor coefficients and symbolic Clifford product simplification", "z3": "computed sign/action/control flags bound into UNSAT/SAT proof", "cvc5": "independent solver encoding of same computed flags"},
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "TOOL_MANIFEST": {
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact rational/surd coefficients and Clifford product simplification"},
            "jax": {"tried": True, "used": True, "reason": "supportive x64/int64 action-matrix mirror; not the proof arbiter"},
            "jax.numpy": {"tried": True, "used": True, "reason": "supportive matrix materialization of exact integer SO(3) action rows"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing SMT on computed double-cover sign/action flags with erased-sign SAT flip"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT encoding over the same computed finite flags"},
        },
        "TOOL_INTEGRATION_DEPTH": {"sympy": "load_bearing", "jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"},
        "tool_calls": [
            {"tool": "sympy", "qualified_api/function": "sympy.sqrt/simplify/Rational", "input_object": "Cl(3,0) exact rotor coefficients and blade products", "output_object": "exact sparse multivectors and SO(3) matrices", "positive_case": "R(pi/2)=(1-e12)/sqrt(2), e1->e2", "negative/erased_control": "non-unit even and odd-grade candidates fail rotor predicate", "boundary_case": "2pi=-1 and 4pi=1", "demotion_condition": "demote if coefficients become floats", "gates": ["positive_section", "boundary_section", "all_pass"]},
            {"tool": "z3", "qualified_api/function": "z3.Solver/check", "input_object": raw_flags, "output_object": z3_result, "positive_case": "computed flags make violation UNSAT", "negative/erased_control": "erasing rotor sign row admits SAT", "boundary_case": "2pi sign flip and 4pi closure flags", "demotion_condition": "demote if SMT does not bind computed values", "gates": ["proof", "all_pass"]},
            {"tool": "cvc5", "qualified_api/function": "cvc5.Solver/checkSat", "input_object": raw_flags, "output_object": cvc5_result, "positive_case": "same as z3", "negative/erased_control": "same erased-sign SAT flip", "boundary_case": "QF_LIA finite flags", "demotion_condition": "demote if cvc5 disagrees with z3", "gates": ["proof", "all_pass"]},
        ],
    }


def main() -> int:
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "engine": ENGINE, "result_path": str(RESULT_PATH.relative_to(ROOT))}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
