#!/usr/bin/env python3
"""cvc5 microfit for a finite constraint-admissibility fence.

This bounded tool-lego fit gives `constraint_probe_admissibility` one small
cvc5-backed fence: finite carrier dimension, normalized two-weight mixtures,
and local Bloch-disk admissibility. It is a proof-tool fence packet only, not a
carrier, operator, coupling, bridge, QIT, GStack, axis, engine, or nonclassical
admission.
"""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime

import sympy as sp
import z3

import cvc5
from cvc5 import Kind


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
divergence_log = (
    "Bounded cvc5 microfit for constraint_probe_admissibility. cvc5 is "
    "load-bearing for small SAT/UNSAT admission-fence checks over integer, "
    "linear-real, and nonlinear-real slices; z3 and sympy are supportive. This "
    "does not admit any full lego, carrier, operator family, bridge, QIT, "
    "GStack, axis, engine, or nonclassical claim."
)

LEGO_IDS = ["constraint_probe_admissibility"]
PRIMARY_LEGO_IDS = ["constraint_probe_admissibility"]

TOOL_MANIFEST = {
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing QF_NRA Bloch-disk admissibility fence; QF_LIA/QF_LRA cases are supportive sanity fences",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive parity checks for selected invalid fence witnesses",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive symbolic guard expressions for finite fence predicates",
    },
    "numpy": {"tried": False, "used": False, "reason": "not needed; no numeric witness sweep"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed; no tensor/autograd dynamics"},
}
TOOL_INTEGRATION_DEPTH = {
    "cvc5": "load_bearing",
    "z3": "supportive",
    "sympy": "supportive",
    "numpy": None,
    "pytorch": None,
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
PARENT_RESULT = RESULT_DIR / "cvc5_capability_results.json"


def source_receipt() -> dict[str, object]:
    if not PARENT_RESULT.exists():
        return {"path": str(PARENT_RESULT), "exists": False, "all_pass": False}
    data = json.loads(PARENT_RESULT.read_text(encoding="utf-8"))
    return {
        "path": str(PARENT_RESULT),
        "exists": True,
        "all_pass": bool(data.get("all_pass") or data.get("summary", {}).get("all_pass")),
        "classification": data.get("classification"),
    }


def solver(logic: str) -> cvc5.Solver:
    s = cvc5.Solver()
    s.setOption("produce-models", "true")
    s.setLogic(logic)
    return s


def cvc5_dimension_fence() -> dict[str, object]:
    rows = {}
    for name, fixed_value, expected_sat in (
        ("admit_d2", 2, True),
        ("reject_d0", 0, False),
        ("reject_d5", 5, False),
    ):
        s = solver("QF_LIA")
        d = s.mkConst(s.getIntegerSort(), f"d_{name}")
        s.assertFormula(s.mkTerm(Kind.GEQ, d, s.mkInteger(1)))
        s.assertFormula(s.mkTerm(Kind.LEQ, d, s.mkInteger(4)))
        s.assertFormula(s.mkTerm(Kind.EQUAL, d, s.mkInteger(fixed_value)))
        result = s.checkSat()
        rows[name] = {
            "fixed_dimension": fixed_value,
            "cvc5_result": str(result),
            "expected_sat": expected_sat,
            "pass": bool(result.isSat()) == expected_sat,
        }
    return {"guard": "1 <= d <= 4", "rows": rows, "pass": all(row["pass"] for row in rows.values())}


def cvc5_mixture_weight_fence() -> dict[str, object]:
    rows = {}
    cases = (
        ("admit_half_half", "1/2", "1/2", True),
        ("reject_two_thirds_two_thirds", "2/3", "2/3", False),
        ("reject_negative_weight", "-1/5", "6/5", False),
    )
    for name, p_val, q_val, expected_sat in cases:
        s = solver("QF_LRA")
        real = s.getRealSort()
        p = s.mkConst(real, f"p_{name}")
        q = s.mkConst(real, f"q_{name}")
        s.assertFormula(s.mkTerm(Kind.GEQ, p, s.mkReal(0)))
        s.assertFormula(s.mkTerm(Kind.GEQ, q, s.mkReal(0)))
        s.assertFormula(s.mkTerm(Kind.EQUAL, s.mkTerm(Kind.ADD, p, q), s.mkReal(1)))
        s.assertFormula(s.mkTerm(Kind.EQUAL, p, s.mkReal(p_val)))
        s.assertFormula(s.mkTerm(Kind.EQUAL, q, s.mkReal(q_val)))
        result = s.checkSat()
        rows[name] = {
            "p": p_val,
            "q": q_val,
            "cvc5_result": str(result),
            "expected_sat": expected_sat,
            "pass": bool(result.isSat()) == expected_sat,
        }
    return {"guard": "p >= 0 and q >= 0 and p+q = 1", "rows": rows, "pass": all(row["pass"] for row in rows.values())}


def cvc5_bloch_disk_fence() -> dict[str, object]:
    rows = {}
    cases = (
        ("admit_boundary_x", "1", "0", True),
        ("admit_inside", "1/5", "2/5", True),
        ("reject_outside_disk", "4/5", "4/5", False),
    )
    for name, rx_val, rz_val, expected_sat in cases:
        s = solver("QF_NRA")
        real = s.getRealSort()
        rx = s.mkConst(real, f"rx_{name}")
        rz = s.mkConst(real, f"rz_{name}")
        radius_sq = s.mkTerm(Kind.ADD, s.mkTerm(Kind.MULT, rx, rx), s.mkTerm(Kind.MULT, rz, rz))
        s.assertFormula(s.mkTerm(Kind.LEQ, radius_sq, s.mkReal(1)))
        s.assertFormula(s.mkTerm(Kind.EQUAL, rx, s.mkReal(rx_val)))
        s.assertFormula(s.mkTerm(Kind.EQUAL, rz, s.mkReal(rz_val)))
        result = s.checkSat()
        rows[name] = {
            "rx": rx_val,
            "rz": rz_val,
            "cvc5_result": str(result),
            "expected_sat": expected_sat,
            "pass": bool(result.isSat()) == expected_sat,
        }
    return {"guard": "rx^2 + rz^2 <= 1", "rows": rows, "pass": all(row["pass"] for row in rows.values())}


def z3_parity_checks() -> dict[str, object]:
    d = z3.Int("d_bad")
    dimension = z3.Solver()
    dimension.add(d >= 1, d <= 4, d == 5)
    dim_result = dimension.check()

    p, q = z3.Reals("p_bad q_bad")
    weights = z3.Solver()
    weights.add(p >= 0, q >= 0, p + q == 1, p == z3.RealVal("2") / 3, q == z3.RealVal("2") / 3)
    weights_result = weights.check()

    rx, rz = z3.Reals("rx_bad rz_bad")
    bloch = z3.Solver()
    bloch.add(rx * rx + rz * rz <= 1, rx == z3.RealVal("4") / 5, rz == z3.RealVal("4") / 5)
    bloch_result = bloch.check()
    rows = {
        "reject_d5": {"z3_result": str(dim_result), "pass": dim_result == z3.unsat},
        "reject_two_thirds_two_thirds": {"z3_result": str(weights_result), "pass": weights_result == z3.unsat},
        "reject_outside_disk": {"z3_result": str(bloch_result), "pass": bloch_result == z3.unsat},
    }
    return {"rows": rows, "pass": all(row["pass"] for row in rows.values())}


def sympy_guard_expressions() -> dict[str, object]:
    d, p, q, rx, rz = sp.symbols("d p q rx rz", real=True)
    expressions = {
        "dimension_interval": "1 <= d <= 4",
        "mixture_residual": str(sp.simplify(p + (1 - p) - 1)),
        "bloch_radius_expression": str(sp.simplify(rx**2 + rz**2)),
    }
    return {
        "expressions": expressions,
        "pass": expressions["mixture_residual"] == "0" and str(rx**2 + rz**2) == expressions["bloch_radius_expression"],
    }


def boundary_checks() -> dict[str, object]:
    result = {
        "single_primary_lego": {"primary_lego_ids": PRIMARY_LEGO_IDS, "pass": PRIMARY_LEGO_IDS == ["constraint_probe_admissibility"]},
        "classification_is_tool_lego_fit_probe": {"classification": CLASSIFICATION, "pass": CLASSIFICATION == "tool_lego_fit_probe"},
        "no_neighbor_lego_credit": {"lego_ids": LEGO_IDS, "pass": LEGO_IDS == ["constraint_probe_admissibility"]},
    }
    result["pass"] = all(row["pass"] for row in result.values())
    return result


def main() -> None:
    parent = source_receipt()
    prerequisite = {
        "parent_cvc5_capability_receipt": parent,
        "parent_cvc5_capability_available_and_passing": bool(parent["exists"] and parent["all_pass"]),
        "note": "Prerequisite metadata only; not counted as a positive fence row.",
    }
    positive = {
        "cvc5_dimension_fence": cvc5_dimension_fence(),
        "cvc5_mixture_weight_fence": cvc5_mixture_weight_fence(),
        "cvc5_bloch_disk_fence": cvc5_bloch_disk_fence(),
    }
    negative = {
        "z3_parity_rejects_selected_invalid_witnesses": z3_parity_checks(),
    }
    scope_declaration = {
        "claim_rejected": "this microfit alone admits the full constraint_probe_admissibility lego",
        "reason": "only three tiny finite fence families are checked",
        "counts_toward_all_pass": False,
    }
    boundary = {
        "sympy_guard_expression_support": sympy_guard_expressions(),
        "scope_and_promotion_boundary": boundary_checks(),
    }
    fence_all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    all_pass = bool(prerequisite["parent_cvc5_capability_available_and_passing"] and fence_all_pass)
    result = {
        "name": "constraint_admissibility_fence_cvc5_microfit",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "tool_lego_fit_probe",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {"cvc5_capability": str(PARENT_RESULT)},
        "prerequisite": prerequisite,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "scope_declaration": scope_declaration,
        "summary": {
            "all_pass": bool(all_pass),
            "fence_rows_all_pass": bool(fence_all_pass),
            "promotion_allowed": False,
            "load_bearing_tool": "cvc5",
            "load_bearing_scope": "QF_NRA Bloch-disk admissibility fence",
            "supportive_scope": "QF_LIA dimension and QF_LRA mixture-weight sanity fences",
            "claim_ceiling": "three_family_constraint_admissibility_fence_microfit_only",
            "sygus_status": "deferred_to_separate_packet",
            "scope_note": divergence_log,
        },
        "all_pass": bool(all_pass),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / "constraint_admissibility_fence_cvc5_microfit_results.json"
    out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
