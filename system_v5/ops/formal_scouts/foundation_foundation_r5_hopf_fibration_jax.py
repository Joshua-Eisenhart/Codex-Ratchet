#!/usr/bin/env python3
"""JAX + z3/cvc5 leg for foundation_r5_hopf_fibration.

The SMT scope is the algebraic Hopf image relation:
if a^2+b^2+c^2+d^2 = 1, then h(a,b,c,d) lies on S^2.
Fiber linking is intentionally not encoded in SMT; Julia computes it.
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
import jax.numpy as jnp
import z3
from cvc5 import Kind


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r5_hopf_fibration"
OBJECT_ID = "foundation_foundation_r5_hopf_fibration_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r5_hopf_fibration_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_hopf_fibration_jax_results.json"
TOL = 1.0e-10

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 finite spinor probe family and numeric residual checks"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive S^3 samples and Hopf coordinate arithmetic"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing in-solver polynomial derivation of the Hopf S^2 image relation"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent in-solver polynomial derivation of the same relation"},
}
TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"}


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def hopf_map(q: jax.Array) -> jax.Array:
    a, b, c, d = q
    return jnp.asarray(
        [
            2.0 * (a * c + b * d),
            2.0 * (b * c - a * d),
            a * a + b * b - c * c - d * d,
        ],
        dtype=jnp.float64,
    )


def sample_spinors() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for theta, phi, psi, name in [
        (0.0, 0.0, 0.0, "north_0"),
        (0.0, 0.0, 1.0, "north_1"),
        (jnp.pi, 0.0, 0.0, "south_0"),
        (jnp.pi, 0.0, 1.0, "south_1"),
        (jnp.pi / 2.0, 0.0, 0.0, "equator_x"),
        (jnp.pi / 2.0, jnp.pi / 2.0, 0.5, "equator_y"),
    ]:
        z1_phase = psi + phi
        z2_phase = psi
        q = jnp.asarray(
            [
                jnp.cos(theta / 2.0) * jnp.cos(z1_phase),
                jnp.cos(theta / 2.0) * jnp.sin(z1_phase),
                jnp.sin(theta / 2.0) * jnp.cos(z2_phase),
                jnp.sin(theta / 2.0) * jnp.sin(z2_phase),
            ],
            dtype=jnp.float64,
        )
        h = hopf_map(q)
        rows.append(
            {
                "id": name,
                "spinor": [py_float(v) for v in q],
                "hopf_image": [py_float(v) for v in h],
                "s3_norm_sq": py_float(jnp.dot(q, q)),
                "s2_norm_sq": py_float(jnp.dot(h, h)),
            }
        )
    return rows


def quotient_from_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    classes: dict[str, list[str]] = {}
    for row in rows:
        key = json.dumps([round(v, 10) for v in row["hopf_image"]], separators=(",", ":"))
        classes.setdefault(key, []).append(row["id"])
    ordered = [
        {"class_id": f"hopf_q{idx}", "signature": json.loads(key), "members": sorted(members)}
        for idx, (key, members) in enumerate(sorted(classes.items()))
    ]
    return {
        "S": [row["id"] for row in rows],
        "equivalence_relation": "q ~_M q' iff all Hopf projection coordinates h(q) and h(q') agree",
        "classes": ordered,
        "class_count": len(ordered),
        "drop_Hopf_projection_probe_class_count": 1,
        "coarsening_flip": len(ordered) != 1,
    }


def z3_hopf_terms() -> dict[str, Any]:
    a, b, c, d = z3.Reals("a b c d")
    x = 2 * (a * c + b * d)
    y = 2 * (b * c - a * d)
    z = a * a + b * b - c * c - d * d
    norm = a * a + b * b + c * c + d * d
    image_norm = x * x + y * y + z * z
    return {"a": a, "b": b, "c": c, "d": d, "x": x, "y": y, "z": z, "norm": norm, "image_norm": image_norm}


def z3_check(assert_norm: bool, mode: str) -> dict[str, Any]:
    t = z3_hopf_terms()
    solver = z3.Solver()
    solver.set(timeout=20_000)
    if assert_norm:
        solver.add(t["norm"] == 1)
    if mode == "counterexample_to_s2_image":
        solver.add(t["image_norm"] != 1)
    elif mode == "wrong_zero_sphere_relation":
        solver.add(t["image_norm"] == 0)
    elif mode == "identity_counterexample":
        solver.add(t["image_norm"] != t["norm"] * t["norm"])
    else:
        raise ValueError(mode)
    return {
        "status": str(solver.check()),
        "asserts_s3_normalization": assert_norm,
        "mode": mode,
        "derived_expressions": {
            "x": "2*(a*c+b*d)",
            "y": "2*(b*c-a*d)",
            "z": "a*a+b*b-c*c-d*d",
            "image_norm": "x*x+y*y+z*z",
        },
    }


def cvc5_real(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkReal(str(value))


def cvc5_add(solver: cvc5.Solver, *terms: Any) -> Any:
    if not terms:
        return cvc5_real(solver, 0)
    return terms[0] if len(terms) == 1 else solver.mkTerm(Kind.ADD, *terms)


def cvc5_mul(solver: cvc5.Solver, *terms: Any) -> Any:
    return terms[0] if len(terms) == 1 else solver.mkTerm(Kind.MULT, *terms)


def cvc5_sub(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.SUB, left, right)


def cvc5_eq(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.EQUAL, left, right)


def cvc5_neq(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(Kind.NOT, cvc5_eq(solver, left, right))


def cvc5_hopf_terms(solver: cvc5.Solver) -> dict[str, Any]:
    real_sort = solver.getRealSort()
    a = solver.mkConst(real_sort, "a")
    b = solver.mkConst(real_sort, "b")
    c = solver.mkConst(real_sort, "c")
    d = solver.mkConst(real_sort, "d")
    two = cvc5_real(solver, 2)
    x = cvc5_mul(solver, two, cvc5_add(solver, cvc5_mul(solver, a, c), cvc5_mul(solver, b, d)))
    y = cvc5_mul(solver, two, cvc5_sub(solver, cvc5_mul(solver, b, c), cvc5_mul(solver, a, d)))
    z = cvc5_sub(
        solver,
        cvc5_add(solver, cvc5_mul(solver, a, a), cvc5_mul(solver, b, b)),
        cvc5_add(solver, cvc5_mul(solver, c, c), cvc5_mul(solver, d, d)),
    )
    norm = cvc5_add(solver, cvc5_mul(solver, a, a), cvc5_mul(solver, b, b), cvc5_mul(solver, c, c), cvc5_mul(solver, d, d))
    image_norm = cvc5_add(solver, cvc5_mul(solver, x, x), cvc5_mul(solver, y, y), cvc5_mul(solver, z, z))
    return {"norm": norm, "image_norm": image_norm}


def cvc5_check(assert_norm: bool, mode: str) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")
    solver.setOption("produce-models", "true")
    solver.setOption("tlimit-per", "20000")
    t = cvc5_hopf_terms(solver)
    if assert_norm:
        solver.assertFormula(cvc5_eq(solver, t["norm"], cvc5_real(solver, 1)))
    if mode == "counterexample_to_s2_image":
        solver.assertFormula(cvc5_neq(solver, t["image_norm"], cvc5_real(solver, 1)))
    elif mode == "wrong_zero_sphere_relation":
        solver.assertFormula(cvc5_eq(solver, t["image_norm"], cvc5_real(solver, 0)))
    elif mode == "identity_counterexample":
        solver.assertFormula(cvc5_neq(solver, t["image_norm"], cvc5_mul(solver, t["norm"], t["norm"])))
    else:
        raise ValueError(mode)
    return {
        "status": str(solver.checkSat()),
        "asserts_s3_normalization": assert_norm,
        "mode": mode,
        "derived_expressions": {
            "x": "2*(a*c+b*d)",
            "y": "2*(b*c-a*d)",
            "z": "a*a+b*b-c*c-d*d",
            "image_norm": "x*x+y*y+z*z",
        },
    }


def smt_report() -> dict[str, Any]:
    z3_main = z3_check(True, "counterexample_to_s2_image")
    z3_erase = z3_check(False, "counterexample_to_s2_image")
    z3_wrong = z3_check(True, "wrong_zero_sphere_relation")
    z3_identity = z3_check(False, "identity_counterexample")
    cvc5_main = cvc5_check(True, "counterexample_to_s2_image")
    cvc5_erase = cvc5_check(False, "counterexample_to_s2_image")
    cvc5_wrong = cvc5_check(True, "wrong_zero_sphere_relation")
    cvc5_identity = cvc5_check(False, "identity_counterexample")
    return {
        "scope": "Algebraic Hopf relation only: normalized S^3 spinor implies Bloch/Hopf image on S^2. Linking is computed in Julia.",
        "forbidden_pattern_guard": "No precomputed scalar/boolean is asserted. The solvers derive x,y,z and x^2+y^2+z^2 from symbolic a,b,c,d.",
        "z3": {
            "version": z3.get_version_string(),
            "verdict": z3_main["status"],
            "main_counterexample_to_s2_image": z3_main,
            "erase_s3_normalization_flip": z3_erase,
            "wrong_zero_sphere_relation": z3_wrong,
            "polynomial_identity_counterexample_without_normalization": z3_identity,
            "pass": z3_main["status"] == "unsat"
            and z3_erase["status"] == "sat"
            and z3_wrong["status"] == "unsat"
            and z3_identity["status"] == "unsat",
        },
        "cvc5": {
            "version": getattr(cvc5, "__version__", "unknown"),
            "verdict": cvc5_main["status"],
            "main_counterexample_to_s2_image": cvc5_main,
            "erase_s3_normalization_flip": cvc5_erase,
            "wrong_zero_sphere_relation": cvc5_wrong,
            "polynomial_identity_counterexample_without_normalization": cvc5_identity,
            "pass": cvc5_main["status"] == "unsat"
            and cvc5_erase["status"] == "sat"
            and cvc5_wrong["status"] == "unsat"
            and cvc5_identity["status"] == "unsat",
        },
    }


def build_result() -> dict[str, Any]:
    rows = sample_spinors()
    quotient = quotient_from_rows(rows)
    max_s3_residual = max(abs(row["s3_norm_sq"] - 1.0) for row in rows)
    max_s2_residual = max(abs(row["s2_norm_sq"] - 1.0) for row in rows)
    smt = smt_report()
    negative = {
        "drop_Hopf_projection_probe_coarsens_quotient": quotient["coarsening_flip"],
        "erase_s3_normalization_z3_unsat_to_sat": smt["z3"]["verdict"] == "unsat" and smt["z3"]["erase_s3_normalization_flip"]["status"] == "sat",
        "erase_s3_normalization_cvc5_unsat_to_sat": smt["cvc5"]["verdict"] == "unsat" and smt["cvc5"]["erase_s3_normalization_flip"]["status"] == "sat",
        "wrong_zero_sphere_relation_unsat": smt["z3"]["wrong_zero_sphere_relation"]["status"] == "unsat"
        and smt["cvc5"]["wrong_zero_sphere_relation"]["status"] == "unsat",
    }
    all_pass = bool(
        max_s3_residual <= TOL
        and max_s2_residual <= TOL
        and smt["z3"]["pass"]
        and smt["cvc5"]["pass"]
        and smt["z3"]["verdict"] == smt["cvc5"]["verdict"] == "unsat"
        and all(negative.values())
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
        "python_executable": sys.executable,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["jax", "jax.numpy", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "M": {
            "name": "Hopf_projection_probe",
            "explicit_probe_family": ["h(q) = (2(ac+bd), 2(bc-ad), a^2+b^2-c^2-d^2)"],
            "finite_probe_domain": {"sampled_spinor_ids": [row["id"] for row in rows]},
        },
        "C": {
            "trace_equals_one": "rho=q*q^T for sampled unit spinors has trace 1",
            "psd": "rho=q*q^T is PSD",
            "hermiticity": "rho=q*q^T is real symmetric/Hermitian",
            "normalization": "a^2+b^2+c^2+d^2=1",
            "rung_specific_constraint": "Hopf/Bloch projection image satisfies x^2+y^2+z^2=1",
        },
        "S_mod_M": quotient,
        "samples": rows,
        "summary": {
            "max_s3_norm_residual": max_s3_residual,
            "max_s2_image_norm_residual": max_s2_residual,
            "smt_scope": smt["scope"],
            "class_count": quotient["class_count"],
            "drop_probe_class_count": quotient["drop_Hopf_projection_probe_class_count"],
        },
        "smt": smt,
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": smt["z3"]["verdict"],
                "negative_control_verdict": smt["z3"]["wrong_zero_sphere_relation"]["status"],
                "erase_flip_verdict": smt["z3"]["erase_s3_normalization_flip"]["status"],
                "claim": "No normalized S^3 spinor has Hopf image outside S^2",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": smt["cvc5"]["verdict"],
                "negative_control_verdict": smt["cvc5"]["wrong_zero_sphere_relation"]["status"],
                "erase_flip_verdict": smt["cvc5"]["erase_s3_normalization_flip"]["status"],
                "claim": "No normalized S^3 spinor has Hopf image outside S^2",
            },
        },
        "negative_control_flip": negative,
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FOUNDATION_R5_HOPF_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"erase_z3={result['crossover_proofs']['z3']['erase_flip_verdict']} "
        f"erase_cvc5={result['crossover_proofs']['cvc5']['erase_flip_verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
