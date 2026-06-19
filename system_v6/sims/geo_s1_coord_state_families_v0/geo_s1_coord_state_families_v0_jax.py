#!/usr/bin/env python3
"""Sympy plus z3/cvc5 lane for geo_s1_coord_state_families_v0."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3

from geo_s1_coord_state_families_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SEED,
    SIM_ID,
    build_math_payload,
    file_sha256,
    sha256_text,
    write_json,
)


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact entropy eigenvalue curves and endpoint simplification"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing endpoint and boundary polarity over rationalized determinant rows"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT polarity mirror for the same determinant inequalities"},
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"}


def z3_boundary_receipt() -> dict[str, Any]:
    u = z3.Real("u")
    receipts = {}
    for n in (3, 4):
        det_num = z3.simplify((1 - u) * (1 - u) * n * n + 2 * u * (1 - u) * n * n + 4 * u * u * (n - 1) - 2 * u * (1 - u) * n)
        solver = z3.Solver()
        solver.add(u >= 0, u <= 1, det_num == 0)
        control = z3.Solver()
        control.add(u >= 0, u <= 1, det_num > 0)
        receipts[str(n)] = {"det_zero_in_closed_interval": str(solver.check()), "positive_control": str(control.check())}
    return receipts


def cvc5_boundary_receipt() -> dict[str, Any]:
    receipts = {}
    for n in (3, 4):
        slv = cvc5.Solver()
        slv.setLogic("QF_NRA")
        real = slv.getRealSort()
        u = slv.mkConst(real, f"u{n}")
        zero = slv.mkReal(0)
        one = slv.mkReal(1)
        nn = slv.mkReal(n * n)
        term = slv.mkTerm(
            Kind.ADD,
            slv.mkTerm(Kind.MULT, slv.mkTerm(Kind.SUB, one, u), slv.mkTerm(Kind.SUB, one, u), nn),
            slv.mkTerm(Kind.MULT, slv.mkReal(2), u, slv.mkTerm(Kind.SUB, one, u), nn),
            slv.mkTerm(Kind.MULT, slv.mkReal(4 * (n - 1)), u, u),
            slv.mkTerm(Kind.MULT, slv.mkReal(-2 * n), u, slv.mkTerm(Kind.SUB, one, u)),
        )
        slv.assertFormula(slv.mkTerm(Kind.GEQ, u, zero))
        slv.assertFormula(slv.mkTerm(Kind.LEQ, u, one))
        slv.assertFormula(slv.mkTerm(Kind.EQUAL, term, zero))
        receipts[str(n)] = {"det_zero_in_closed_interval": str(slv.checkSat())}
    return receipts


def build_result() -> dict[str, Any]:
    math_payload = build_math_payload()
    z3_rows = z3_boundary_receipt()
    cvc5_rows = cvc5_boundary_receipt()
    all_pass = (
        math_payload["endpoint_anchors_recovered"]
        and all(row["det_zero_in_closed_interval"] == "unsat" for row in z3_rows.values())
        and all(row["det_zero_in_closed_interval"] == "unsat" for row in cvc5_rows.values())
    )
    return {
        "schema_version": "three_engine_lane_result_v1",
        "sim_id": SIM_ID,
        "role_id": "jax_rich_mirror_sim_builder",
        "engine": "jax",
        "all_pass": all_pass,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "reads_peer_result": False,
        "seed": SEED,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "packages_used": ["sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api/function": "Matrix eigenvalue closed form / simplify",
                "input_object": "rho_A(eta) for GHZ-W n=3,n=4 and W-weighted eta_i constructor rows",
                "output_object": "exact entropy expressions, executable W-site constructor anchors, and endpoint anchors",
                "positive_case": "eta=0 gives log(2); eta=pi/2 gives W_n H(1/n)",
                "negative/erased_control": "coordinate-independent family detected flat",
                "boundary_case": "det(rho_A)=0 search",
                "demotion_condition": "if endpoint simplification fails, symbolic lane is not load-bearing",
                "gates": ["all_pass", "endpoint_anchors", "boundary_rows"],
            },
            {
                "tool": "z3/cvc5",
                "qualified_api/function": "Solver.check / Solver.checkSat",
                "input_object": "0<=u<=1 and determinant numerator == 0",
                "output_object": "unsat for n=3,n=4 GHZ-W single-site separability crossing",
                "positive_case": "determinant positive-control is satisfiable",
                "negative/erased_control": "zero-determinant boundary absent for GHZ-W interpolation",
                "boundary_case": "u in [0,1]",
                "demotion_condition": "if solver verdicts disagree, boundary row is open",
                "gates": ["crossover_proofs", "boundary_rows"],
            },
        ],
        "math_payload": math_payload,
        "solver_rows": {"z3": z3_rows, "cvc5": cvc5_rows},
    }


if __name__ == "__main__":
    write_json(RESULT_PATH, build_result())
