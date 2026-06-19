#!/usr/bin/env python3
"""Exact ledger helpers for carnot_szilard_landauer_ledger_v1."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import cvc5
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "carnot_szilard_landauer_ledger_v1"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
T_H = Fraction(2, 1)
T_C = Fraction(1, 1)
ETA_C = Fraction(1, 1) - T_C / T_H
CLASSIFICATION = "scratch_diagnostic"
ROW_CLASSIFICATION = "classical_baseline"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frac_json(value: Fraction) -> dict[str, Any]:
    return {
        "num": value.numerator,
        "den": value.denominator,
        "string": f"{value.numerator}/{value.denominator}",
        "float": float(value),
    }


def z3_real(value: Fraction) -> z3.RatNumRef:
    return z3.RealVal(f"{value.numerator}/{value.denominator}")


def cvc5_real(solver: cvc5.Solver, value: Fraction) -> cvc5.Term:
    return solver.mkReal(value.numerator, value.denominator)


def z3_model_dict(model: z3.ModelRef, vars_by_name: dict[str, Any]) -> dict[str, str]:
    return {name: str(model.eval(var, model_completion=True)) for name, var in vars_by_name.items()}


def ledger_totals(strokes: list[dict[str, Any]]) -> dict[str, Fraction]:
    totals = {"q_hot": Fraction(0), "q_cold": Fraction(0), "work_out": Fraction(0)}
    for stroke in strokes:
        for key in totals:
            totals[key] += stroke[key]
    totals["energy_residual"] = totals["q_hot"] + totals["q_cold"] - totals["work_out"]
    totals["entropy_production"] = -totals["q_hot"] / T_H - totals["q_cold"] / T_C
    totals["eta"] = totals["work_out"] / totals["q_hot"] if totals["q_hot"] != 0 else Fraction(0)
    return totals


def stroke(name: str, q_hot: Fraction, q_cold: Fraction, work_out: Fraction) -> dict[str, Any]:
    return {"stroke": name, "q_hot": q_hot, "q_cold": q_cold, "work_out": work_out}


def cycle_ledgers() -> dict[str, dict[str, Any]]:
    return {
        "reversible_carnot_cycle": {
            "expected": "sat",
            "description": "four-stroke reversible boundary ledger",
            "strokes": [
                stroke("hot_isothermal_expansion", Fraction(2), Fraction(0), Fraction(3, 2)),
                stroke("adiabatic_expansion", Fraction(0), Fraction(0), Fraction(1, 2)),
                stroke("cold_isothermal_compression", Fraction(0), Fraction(-1), Fraction(-1)),
                stroke("adiabatic_compression", Fraction(0), Fraction(0), Fraction(0)),
            ],
        },
        "sub_carnot_irreversible_cycle": {
            "expected": "sat",
            "description": "finite loss row; positive entropy production lowers eta",
            "strokes": [
                stroke("hot_contact", Fraction(2), Fraction(0), Fraction(1)),
                stroke("finite_loss_internal", Fraction(0), Fraction(-1, 2), Fraction(-1, 2)),
                stroke("cold_rejection", Fraction(0), Fraction(-1), Fraction(0)),
            ],
        },
        "candidate_super_carnot_cycle": {
            "expected": "unsat",
            "description": "ledger that would be needed for eta 3/4; entropy production is negative",
            "strokes": [
                stroke("hot_contact", Fraction(2), Fraction(0), Fraction(3, 2)),
                stroke("too_small_cold_rejection", Fraction(0), Fraction(-1, 2), Fraction(0)),
            ],
        },
        "trivial_zero_work_cycle": {
            "expected": "sat",
            "description": "boundary control with no work extraction",
            "strokes": [
                stroke("idle_hot", Fraction(0), Fraction(0), Fraction(0)),
                stroke("idle_cold", Fraction(0), Fraction(0), Fraction(0)),
            ],
        },
    }


def serialize_cycle(name: str, row: dict[str, Any]) -> dict[str, Any]:
    totals = ledger_totals(row["strokes"])
    return {
        "name": name,
        "description": row["description"],
        "expected": row["expected"],
        "classification": ROW_CLASSIFICATION,
        "strokes": [
            {key: frac_json(value) if isinstance(value, Fraction) else value for key, value in item.items()}
            for item in row["strokes"]
        ],
        "derived": {
            "q_hot_total": frac_json(totals["q_hot"]),
            "q_cold_total": frac_json(totals["q_cold"]),
            "work_out_total": frac_json(totals["work_out"]),
            "energy_residual": frac_json(totals["energy_residual"]),
            "entropy_production": frac_json(totals["entropy_production"]),
            "eta": frac_json(totals["eta"]),
            "eta_c": frac_json(ETA_C),
            "eta_relation": (
                "equal_to_eta_C"
                if totals["eta"] == ETA_C
                else "below_eta_C"
                if totals["eta"] < ETA_C
                else "above_eta_C"
            ),
        },
    }


def solve_cycle_z3(name: str, row: dict[str, Any], *, include_entropy_constraint: bool = True) -> dict[str, Any]:
    totals = ledger_totals(row["strokes"])
    qh, qc, w, sigma, eta = z3.Reals(f"{name}_q_hot {name}_q_cold {name}_work_out {name}_entropy_prod {name}_eta")
    solver = z3.Solver()
    solver.add(qh == z3_real(totals["q_hot"]))
    solver.add(qc == z3_real(totals["q_cold"]))
    solver.add(w == z3_real(totals["work_out"]))
    solver.add(sigma == -qh / z3_real(T_H) - qc / z3_real(T_C))
    solver.add(qh + qc - w == 0)
    if totals["q_hot"] > 0:
        solver.add(eta * qh == w)
    else:
        solver.add(eta == 0)
    if include_entropy_constraint:
        solver.add(sigma >= 0)
    status = str(solver.check())
    result: dict[str, Any] = {
        "status": status,
        "constraints": {
            "first_law_q_hot_plus_q_cold_minus_work_eq_0": True,
            "entropy_production_nonnegative": include_entropy_constraint,
            "no_asserted_eta_bound": True,
        },
        "derived": {
            "eta": frac_json(totals["eta"]),
            "eta_c": frac_json(ETA_C),
            "entropy_production": frac_json(totals["entropy_production"]),
            "energy_residual": frac_json(totals["energy_residual"]),
        },
    }
    if status == "sat":
        result["model"] = z3_model_dict(
            solver.model(),
            {"q_hot": qh, "q_cold": qc, "work_out": w, "entropy_production": sigma, "eta": eta},
        )
    return result


def solve_cycle_cvc5(name: str, row: dict[str, Any], *, include_entropy_constraint: bool = True) -> dict[str, Any]:
    totals = ledger_totals(row["strokes"])
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("QF_LRA")
    real = solver.getRealSort()
    qh = solver.mkConst(real, f"{name}_q_hot")
    qc = solver.mkConst(real, f"{name}_q_cold")
    w = solver.mkConst(real, f"{name}_work_out")
    sigma = solver.mkConst(real, f"{name}_entropy_prod")
    eta = solver.mkConst(real, f"{name}_eta")
    zero = cvc5_real(solver, Fraction(0))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, qh, cvc5_real(solver, totals["q_hot"])))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, qc, cvc5_real(solver, totals["q_cold"])))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, w, cvc5_real(solver, totals["work_out"])))
    entropy_expr = solver.mkTerm(
        cvc5.Kind.SUB,
        solver.mkTerm(cvc5.Kind.NEG, solver.mkTerm(cvc5.Kind.DIVISION, qh, cvc5_real(solver, T_H))),
        solver.mkTerm(cvc5.Kind.DIVISION, qc, cvc5_real(solver, T_C)),
    )
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, sigma, entropy_expr))
    solver.assertFormula(
        solver.mkTerm(cvc5.Kind.EQUAL, solver.mkTerm(cvc5.Kind.SUB, solver.mkTerm(cvc5.Kind.ADD, qh, qc), w), zero)
    )
    if totals["q_hot"] > 0:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, solver.mkTerm(cvc5.Kind.MULT, eta, qh), w))
    else:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, eta, zero))
    if include_entropy_constraint:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, sigma, zero))
    status = str(solver.checkSat())
    result: dict[str, Any] = {
        "status": status,
        "constraints": {
            "first_law_q_hot_plus_q_cold_minus_work_eq_0": True,
            "entropy_production_nonnegative": include_entropy_constraint,
            "no_asserted_eta_bound": True,
        },
    }
    if status == "sat":
        result["model"] = {
            "q_hot": str(solver.getValue(qh)),
            "q_cold": str(solver.getValue(qc)),
            "work_out": str(solver.getValue(w)),
            "entropy_production": str(solver.getValue(sigma)),
            "eta": str(solver.getValue(eta)),
        }
    return result


def solve_erasure_z3(name: str, paid_ln2: Fraction, required_ln2: Fraction) -> dict[str, Any]:
    paid, required, surplus = z3.Reals(f"{name}_paid_ln2 {name}_required_ln2 {name}_surplus_ln2")
    solver = z3.Solver()
    solver.add(paid == z3_real(paid_ln2), required == z3_real(required_ln2), surplus == paid - required)
    solver.add(paid >= required)
    status = str(solver.check())
    result: dict[str, Any] = {
        "status": status,
        "constraints": {"paid_erasure_cost_gte_required_landauer_cost": True},
        "derived": {"paid_ln2_coeff": frac_json(paid_ln2), "required_ln2_coeff": frac_json(required_ln2)},
    }
    if status == "sat":
        result["model"] = z3_model_dict(solver.model(), {"paid_ln2": paid, "required_ln2": required, "surplus_ln2": surplus})
    return result


def solve_erasure_cvc5(name: str, paid_ln2: Fraction, required_ln2: Fraction) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    solver.setLogic("QF_LRA")
    real = solver.getRealSort()
    paid = solver.mkConst(real, f"{name}_paid_ln2")
    required = solver.mkConst(real, f"{name}_required_ln2")
    surplus = solver.mkConst(real, f"{name}_surplus_ln2")
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, paid, cvc5_real(solver, paid_ln2)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, required, cvc5_real(solver, required_ln2)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, surplus, solver.mkTerm(cvc5.Kind.SUB, paid, required)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, paid, required))
    status = str(solver.checkSat())
    result: dict[str, Any] = {
        "status": status,
        "constraints": {"paid_erasure_cost_gte_required_landauer_cost": True},
    }
    if status == "sat":
        result["model"] = {
            "paid_ln2": str(solver.getValue(paid)),
            "required_ln2": str(solver.getValue(required)),
            "surplus_ln2": str(solver.getValue(surplus)),
        }
    return result


def szilard_rows() -> dict[str, dict[str, Any]]:
    return {
        "szilard_paid_measure_feedback_erase": {
            "expected": "sat",
            "classification": ROW_CLASSIFICATION,
            "ledger": [
                {"stroke": "measure_record_one_bit", "nats_recorded_ln2_coeff": frac_json(Fraction(1)), "work_out_ln2_coeff": frac_json(Fraction(0)), "erasure_paid_ln2_coeff": frac_json(Fraction(0))},
                {"stroke": "feedback_isothermal_expansion", "nats_recorded_ln2_coeff": frac_json(Fraction(0)), "work_out_ln2_coeff": frac_json(Fraction(1)), "erasure_paid_ln2_coeff": frac_json(Fraction(0))},
                {"stroke": "erase_record", "nats_recorded_ln2_coeff": frac_json(Fraction(-1)), "work_out_ln2_coeff": frac_json(Fraction(0)), "erasure_paid_ln2_coeff": frac_json(Fraction(1))},
            ],
            "derived": {"work_out": "k*T*ln(2)", "required_erasure": "k*T*ln(2)", "net_after_paid_erasure_ln2_coeff": frac_json(Fraction(0))},
            "z3": solve_erasure_z3("szilard_paid", Fraction(1), Fraction(1)),
            "cvc5": solve_erasure_cvc5("szilard_paid", Fraction(1), Fraction(1)),
        },
        "szilard_unpaid_erasure_variant": {
            "expected": "unsat",
            "classification": ROW_CLASSIFICATION,
            "derived": {"work_out": "k*T*ln(2)", "paid_erasure_ln2_coeff": frac_json(Fraction(0)), "required_erasure_ln2_coeff": frac_json(Fraction(1))},
            "z3": solve_erasure_z3("szilard_unpaid", Fraction(0), Fraction(1)),
            "cvc5": solve_erasure_cvc5("szilard_unpaid", Fraction(0), Fraction(1)),
        },
        "below_landauer_half_paid": {
            "expected": "unsat",
            "classification": ROW_CLASSIFICATION,
            "derived": {"paid_erasure_ln2_coeff": frac_json(Fraction(1, 2)), "required_erasure_ln2_coeff": frac_json(Fraction(1))},
            "z3": solve_erasure_z3("below_landauer_half_paid", Fraction(1, 2), Fraction(1)),
            "cvc5": solve_erasure_cvc5("below_landauer_half_paid", Fraction(1, 2), Fraction(1)),
        },
    }


def misledger_control() -> dict[str, Any]:
    bad = [
        stroke("hot_contact", Fraction(2), Fraction(0), Fraction(3, 2)),
    ]
    totals = ledger_totals(bad)
    required_names = {"hot_contact", "too_small_cold_rejection"}
    present = {item["stroke"] for item in bad}
    errors = []
    if required_names - present:
        errors.append(f"missing_strokes:{','.join(sorted(required_names - present))}")
    if totals["energy_residual"] != 0:
        errors.append("first_law_energy_residual_nonzero")
    return {
        "status": "caught" if errors else "missed",
        "errors": errors,
        "omitted_entry": "too_small_cold_rejection",
        "derived": {
            "energy_residual": frac_json(totals["energy_residual"]),
            "entropy_production": frac_json(totals["entropy_production"]),
        },
    }


def summarize_cycle_rows() -> dict[str, Any]:
    rows = {}
    for name, row in cycle_ledgers().items():
        rows[name] = serialize_cycle(name, row)
        rows[name]["z3"] = solve_cycle_z3(name, row)
        rows[name]["cvc5"] = solve_cycle_cvc5(name, row)
    super_row = cycle_ledgers()["candidate_super_carnot_cycle"]
    rows["broken_fence_drop_entropy_constraint_super_carnot"] = {
        "name": "broken_fence_drop_entropy_constraint_super_carnot",
        "expected": "sat",
        "classification": ROW_CLASSIFICATION,
        "description": "same super-Carnot ledger with entropy-production constraint dropped",
        "z3": solve_cycle_z3("broken_super_carnot", super_row, include_entropy_constraint=False),
        "cvc5": solve_cycle_cvc5("broken_super_carnot", super_row, include_entropy_constraint=False),
    }
    rows["broken_fence_drop_entropy_constraint_super_carnot"]["numeric_eta_gt_eta_c"] = (
        rows["broken_fence_drop_entropy_constraint_super_carnot"]["z3"]["status"] == "sat"
        and ledger_totals(super_row["strokes"])["eta"] > ETA_C
    )
    return rows


def typed_entropy() -> dict[str, Any]:
    return {
        "bits": frac_json(Fraction(1)),
        "nats_exact": "ln(2)",
        "conversion": "1 bit * ln(2) = ln(2) nats",
        "landauer_one_bit_cost": "k*T*ln(2)",
        "units_policy": "bit counts are converted to nats before ledger rows are compared",
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
