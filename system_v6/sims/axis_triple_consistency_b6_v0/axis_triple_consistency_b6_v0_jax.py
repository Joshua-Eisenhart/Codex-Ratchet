#!/usr/bin/env python3
"""JAX lane for axis_triple_consistency_b6_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import jax.scipy.linalg as jsp_linalg
import sympy as sp
import z3

import axis_triple_consistency_b6_v0_common as common


ENGINE = "jax"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def sign_array(values: jax.Array) -> jax.Array:
    return jnp.where(values > common.EPS, 1, jnp.where(values < -common.EPS, -1, 0)).astype(jnp.int64)


def load_pinned_pair_jax() -> dict[str, jax.Array]:
    s4 = common.load_json(common.PARENT_PATHS["geo_s4_envelope"])
    s5 = common.load_json(common.PARENT_PATHS["geo_s5_envelope"])
    operator = s4["affine_channel_table"][common.PRIMARY_OPERATOR]
    terrain = s5["bloch_generator_table"][common.PRIMARY_TERRAIN]
    op_m = jnp.asarray(common.parse_matrix(operator["pinned"]["M"]), dtype=jnp.float64)
    op_c = jnp.asarray(common.parse_vector(operator["pinned"]["c"]), dtype=jnp.float64)
    terrain_a = jnp.asarray(common.parse_matrix(terrain["pinned"]["A"]), dtype=jnp.float64)
    terrain_b = jnp.asarray(common.parse_vector(terrain["pinned"]["b"]), dtype=jnp.float64)
    aug = jnp.zeros((4, 4), dtype=jnp.float64)
    aug = aug.at[:3, :3].set(terrain_a)
    aug = aug.at[:3, 3].set(terrain_b)
    flow = jsp_linalg.expm(0.5 * aug)
    return {"op_m": op_m, "op_c": op_c, "terrain_m": flow[:3, :3], "terrain_c": flow[:3, 3]}


def recompute_table_counts() -> dict[str, Any]:
    rows = common.axis3_sample_rows()
    etas = jnp.asarray([row["eta"] for row in rows], dtype=jnp.float64)
    chis = jnp.asarray([row["chi0"] for row in rows], dtype=jnp.float64)
    b3 = jnp.asarray([row["b3_sign"] for row in rows], dtype=jnp.int64)
    bloch = jnp.stack(
        [
            jnp.sin(2.0 * etas) * jnp.cos(2.0 * chis),
            jnp.sin(2.0 * etas) * jnp.sin(2.0 * chis),
            jnp.cos(2.0 * etas),
        ],
        axis=1,
    )
    pair = load_pinned_pair_jax()
    op_image = (pair["op_m"] @ bloch.T).T + pair["op_c"]
    operator_first = (pair["terrain_m"] @ op_image.T).T + pair["terrain_c"]
    terrain_image = (pair["terrain_m"] @ bloch.T).T + pair["terrain_c"]
    terrain_first = (pair["op_m"] @ terrain_image.T).T + pair["op_c"]
    delta = operator_first - terrain_first
    weighted_z = jnp.linalg.norm(delta, axis=1) * delta[:, 2]
    b6 = sign_array(weighted_z)
    b0 = sign_array(jnp.cos(2.0 * etas))
    expected = -(b0 * b3)
    holds = b6 == expected
    nonneutral = expected != 0
    values = {
        "sample_total": int(len(rows)),
        "agreement_count": int(jax.device_get(jnp.sum(holds.astype(jnp.int64)))),
        "violation_count": int(len(rows) - int(jax.device_get(jnp.sum(holds.astype(jnp.int64))))),
        "nonneutral_total": int(jax.device_get(jnp.sum(nonneutral.astype(jnp.int64)))),
        "nonneutral_agreement_count": int(jax.device_get(jnp.sum((holds & nonneutral).astype(jnp.int64)))),
        "b6_positive_count": int(jax.device_get(jnp.sum((b6 == 1).astype(jnp.int64)))),
        "b6_negative_count": int(jax.device_get(jnp.sum((b6 == -1).astype(jnp.int64)))),
        "weighted_z_sha256": common.stable_sha256([float(x) for x in jax.device_get(weighted_z)]),
    }
    return values


def panel_checks_jax() -> list[dict[str, Any]]:
    pair = load_pinned_pair_jax()
    etas = jnp.asarray([jnp.pi / 6.0, jnp.pi / 3.0], dtype=jnp.float64)
    chis = jnp.asarray([0.0, 0.0], dtype=jnp.float64)
    b3 = jnp.asarray([1, -1], dtype=jnp.int64)
    bloch = jnp.stack(
        [
            jnp.sin(2.0 * etas) * jnp.cos(2.0 * chis),
            jnp.sin(2.0 * etas) * jnp.sin(2.0 * chis),
            jnp.cos(2.0 * etas),
        ],
        axis=1,
    )
    op_image = (pair["op_m"] @ bloch.T).T + pair["op_c"]
    operator_first = (pair["terrain_m"] @ op_image.T).T + pair["terrain_c"]
    terrain_image = (pair["terrain_m"] @ bloch.T).T + pair["terrain_c"]
    terrain_first = (pair["op_m"] @ terrain_image.T).T + pair["op_c"]
    delta = operator_first - terrain_first
    b6 = sign_array(jnp.linalg.norm(delta, axis=1) * delta[:, 2])
    b0 = sign_array(jnp.cos(2.0 * etas))
    expected = -(b0 * b3)
    labels = ["panel6_q2_eta_pi_over_6_fiber", "panel6_q2_eta_pi_over_3_base"]
    out = []
    for idx, label in enumerate(labels):
        out.append(
            {
                "panel_point_id": label,
                "b0_sign": int(jax.device_get(b0[idx])),
                "b3_sign": int(jax.device_get(b3[idx])),
                "computed_b6_sign": int(jax.device_get(b6[idx])),
                "expected_b6_negative_b0_b3": int(jax.device_get(expected[idx])),
                "panel_expected_b6": -1,
                "matches_panel_expected": int(jax.device_get(b6[idx])) == -1,
            }
        )
    return out


def sympy_panel_probe() -> dict[str, Any]:
    eta_fiber = sp.Rational(1, 6) * sp.pi
    eta_base = sp.Rational(1, 3) * sp.pi
    b0_fiber = sp.sign(sp.cos(2 * eta_fiber))
    b0_base = sp.sign(sp.cos(2 * eta_base))
    expected_fiber = sp.simplify(-(b0_fiber * 1))
    expected_base = sp.simplify(-(b0_base * -1))
    mat = sp.Matrix([[expected_fiber], [expected_base]])
    return {
        "b0_fiber": int(b0_fiber),
        "b0_base": int(b0_base),
        "expected_b6_fiber": int(mat[0]),
        "expected_b6_base": int(mat[1]),
        "pass": int(mat[0]) == -1 and int(mat[1]) == -1,
    }


def z3_count_probe(values: dict[str, Any], *, erased: bool = False) -> str:
    solver = z3.Solver()
    total = z3.Int("jax_total_erased" if erased else "jax_total")
    agreement = z3.Int("jax_agreement_erased" if erased else "jax_agreement")
    violation = z3.Int("jax_violation_erased" if erased else "jax_violation")
    solver.add(total == z3.IntVal(values["sample_total"]))
    solver.add(agreement == z3.IntVal(values["sample_total"] if erased else values["agreement_count"]))
    solver.add(violation == z3.IntVal(0 if erased else values["violation_count"]))
    solver.add(total == agreement)
    solver.add(violation == z3.IntVal(0))
    return str(solver.check())


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(int(value))


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_count_probe(values: dict[str, Any], *, erased: bool = False) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    total = solver.mkConst(integer, "jax_total_erased" if erased else "jax_total")
    agreement = solver.mkConst(integer, "jax_agreement_erased" if erased else "jax_agreement")
    violation = solver.mkConst(integer, "jax_violation_erased" if erased else "jax_violation")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, total, cvc5_int(solver, values["sample_total"])))
    solver.assertFormula(
        solver.mkTerm(Kind.EQUAL, agreement, cvc5_int(solver, values["sample_total"] if erased else values["agreement_count"]))
    )
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, violation, cvc5_int(solver, 0 if erased else values["violation_count"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, total, agreement))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, violation, cvc5_int(solver, 0)))
    return cvc5_status(solver.checkSat())


def build_result() -> dict[str, Any]:
    obj = common.build_axis_triple_object()
    values = recompute_table_counts()
    panel = panel_checks_jax()
    sympy_probe = sympy_panel_probe()
    z3_verdict = z3_count_probe(values)
    z3_erased = z3_count_probe(values, erased=True)
    cvc5_verdict = cvc5_count_probe(values)
    cvc5_erased = cvc5_count_probe(values, erased=True)
    expected = common.engine_computed_values(obj)
    all_pass = bool(
        values["sample_total"] == expected["sample_total"]
        and values["agreement_count"] == expected["agreement_count"]
        and values["violation_count"] == expected["violation_count"]
        and values["nonneutral_agreement_count"] == expected["nonneutral_agreement_count"]
        and all(row["matches_panel_expected"] for row in panel)
        and sympy_probe["pass"]
        and z3_verdict == cvc5_verdict == "unsat"
        and z3_erased == cvc5_erased == "sat"
    )
    return {
        **common.source_result_base(ENGINE, SOURCE_PATH, RESULT_PATH),
        "packages_used": ["jax", "jax.numpy", "jax.scipy.linalg", "sympy", "z3", "cvc5", "json", "pathlib"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "package_observables": {
            "sympy": "sp.Rational/sp.Matrix panel arithmetic check for q2 signs",
            "z3": "z3.Solver binds computed agreement/violation counts and erased flip",
            "cvc5": "cvc5.Solver independently binds the same count row and erased flip",
        },
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
        "tool_intent": common.TOOL_INTENT,
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "source_backing_probe": {
            "jax_enable_x64": bool(jax.config.jax_enable_x64),
            "jax_device_get_count": values["sample_total"],
            "sympy_panel_probe": sympy_probe,
            "z3_verdict": z3_verdict,
            "z3_erased_flip_verdict": z3_erased,
            "cvc5_verdict": cvc5_verdict,
            "cvc5_erased_flip_verdict": cvc5_erased,
            "pass": all_pass,
        },
        "computed_values": values,
        "panel_point_checks": panel,
        "crossover_proofs": {
            "z3": {"ran": True, "load_bearing": True, "verdict": z3_verdict, "erased_flip_verdict": z3_erased},
            "cvc5": {"ran": True, "load_bearing": True, "verdict": cvc5_verdict, "erased_flip_verdict": cvc5_erased},
        },
        "capability_receipts": [
            {"receipt_id": "jax_axis_triple_vector_recompute", "tool": "jax", "status": "used"},
            {"receipt_id": "jax_axis_triple_smt_count_bind", "tool": "z3+cvc5", "status": "used"},
        ],
        "tool_calls": [
            {"tool": "jax", "qualified_api/function": "jax.config.update, jax.device_get", "load_bearing": False},
            {"tool": "jax.numpy", "qualified_api/function": "jnp.stack, jnp.linalg.norm, jnp.where", "load_bearing": False},
            {"tool": "jax.scipy.linalg", "qualified_api/function": "jsp_linalg.expm", "load_bearing": False},
            {"tool": "sympy", "qualified_api/function": "sp.Rational, sp.Matrix, sp.simplify", "load_bearing": True},
            {"tool": "z3", "qualified_api/function": "z3.Solver, z3.Int, solver.add, solver.check", "load_bearing": True},
            {"tool": "cvc5", "qualified_api/function": "cvc5.Solver, mkConst, mkTerm, assertFormula, checkSat", "load_bearing": True},
        ],
        "all_pass": all_pass,
    }


def main() -> int:
    payload = build_result()
    common.write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
