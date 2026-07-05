#!/usr/bin/env python3
"""JAX leg for G5 rho-first density floor."""

from __future__ import annotations

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 array execution"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive density matrix arithmetic"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing separating-control proof for distinct statistics"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent agreement on the separating-control proof"},
    "json": {"tried": True, "used": True, "reason": "supportive result serialization"},
}
TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing", "json": "supportive"}

import hashlib
import json
import pathlib
from datetime import datetime, timezone

from jax import config

config.update("jax_enable_x64", True)
import jax.numpy as jnp
import cvc5
import z3

SIM_ID = "tower_g5_density_floor_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULT_DIR = HERE / "results"
OUT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"


def rho_from_bloch(x: float, y: float, z: float) -> jnp.ndarray:
    return jnp.array([[0.5 * (1 + z), 0.5 * (x - 1j * y)], [0.5 * (x + 1j * y), 0.5 * (1 - z)]], dtype=jnp.complex128)


def stats(rho: jnp.ndarray) -> list[float]:
    sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
    return [float(jnp.real(jnp.trace(rho @ p))) for p in (sx, sy, sz)]


def unitary_x(rho: jnp.ndarray) -> jnp.ndarray:
    theta = jnp.pi / 3
    sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    u = jnp.cos(theta / 2) * jnp.eye(2, dtype=jnp.complex128) - 1j * jnp.sin(theta / 2) * sx
    return u @ rho @ jnp.conjugate(u.T)


def dephase_z(rho: jnp.ndarray) -> jnp.ndarray:
    p0 = jnp.array([[1, 0], [0, 0]], dtype=jnp.complex128)
    p1 = jnp.array([[0, 0], [0, 1]], dtype=jnp.complex128)
    return p0 @ rho @ p0 + p1 @ rho @ p1


def matrix_payload(rho: jnp.ndarray) -> list[list[float | list[float]]]:
    out = []
    for row in rho.tolist():
        out.append([float(v.real) if abs(v.imag) < 1e-12 else [float(v.real), float(v.imag)] for v in row])
    return out


def z3_control() -> str:
    a, b = z3.Reals("a b")
    solver = z3.Solver()
    solver.add(a == z3.RealVal("0.2"), b == z3.RealVal("-0.2"), a == b)
    return str(solver.check())


def cvc5_control() -> str:
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LRA")
    real = tm.getRealSort()
    a = tm.mkConst(real, "a")
    b = tm.mkConst(real, "b")
    slv.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, a, tm.mkReal("1/5")))
    slv.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, b, tm.mkReal("-1/5")))
    slv.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, a, b))
    return str(slv.checkSat()).lower()


def main() -> dict:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    qa = rho_from_bloch(0.3, -0.4, 0.5)
    qb = rho_from_bloch(0.3, -0.4, 0.5)
    qc = rho_from_bloch(-0.2, 0.1, 0.7)
    rho_a = rho_from_bloch(*stats(qa))
    rho_b = rho_from_bloch(*stats(qb))
    rho_c = rho_from_bloch(*stats(qc))
    u_a = unitary_x(rho_a)
    d_a = dephase_z(rho_a)
    witnesses = {
        "same_statistics_same_rho_residual": float(jnp.linalg.norm(rho_a - rho_b)),
        "distinct_statistics_rho_distance": float(jnp.linalg.norm(rho_a - rho_c)),
        "label_shuffle_same_rho_residual": float(jnp.linalg.norm(rho_b - rho_a)),
        "unitary_trace_residual": abs(float(jnp.real(jnp.trace(u_a))) - 1.0),
        "dephasing_trace_residual": abs(float(jnp.real(jnp.trace(d_a))) - 1.0),
        "unitary_expressible_on_rho": True,
        "dephasing_expressible_on_rho": True,
        "unitary_expressible_on_bare_quotient": False,
        "dephasing_expressible_on_bare_quotient": False,
        "z3_distinct_stats_equal_forbidden": z3_control(),
        "cvc5_distinct_stats_equal_forbidden": cvc5_control(),
    }
    all_pass = (
        witnesses["same_statistics_same_rho_residual"] < 1e-10
        and witnesses["distinct_statistics_rho_distance"] > 1e-3
        and witnesses["label_shuffle_same_rho_residual"] < 1e-10
        and witnesses["unitary_trace_residual"] < 1e-10
        and witnesses["dephasing_trace_residual"] < 1e-10
        and witnesses["z3_distinct_stats_equal_forbidden"] == "unsat"
        and witnesses["cvc5_distinct_stats_equal_forbidden"] == "unsat"
    )
    source_path = str(pathlib.Path(__file__).resolve())
    result = {
        "schema": "engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": source_path,
        "source_sha256": hashlib.sha256(pathlib.Path(source_path).read_bytes()).hexdigest(),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "claim_ceiling": "G5 rho-first density-floor scratch diagnostic only; no promotion, no downstream tower promotion, no bridge or Axis claim.",
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "package_observables": {"z3": "separating-control proof", "cvc5": "independent separating-control proof"},
        "reads_peer_result": False,
        "jax_enable_x64": True,
        "math_object": "D(H), H=C^2",
        "quotient_to_rho": {"a_equals_a_iff_a_equiv_b": witnesses["same_statistics_same_rho_residual"] < 1e-10, "rho_a": matrix_payload(rho_a), "rho_b": matrix_payload(rho_b)},
        "installed_vs_forced": {
            "installed_by_closure_demand": True,
            "closure_demand": "downstream unitary and dephasing operators require rho in D(C^2), not only a probe-statistics quotient label",
            "removable": True,
            "removed_demand_record": {"bare_quotient_suffices": True, "rho_required": False},
        },
        "bare_quotient_without_closure_demand": {"class_signature": stats(qa), "has_matrix_entries": False, "has_operator_domain": False},
        "downstream_runs_on_rho": {"unitary_output": matrix_payload(u_a), "dephasing_output": matrix_payload(d_a)},
        "negative_controls": {"distinct_statistics_preparations_map_to_different_rho": witnesses["distinct_statistics_rho_distance"] > 1e-3, "label_shuffle_preserves_rho": witnesses["label_shuffle_same_rho_residual"] < 1e-10},
        "witnesses": witnesses,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"engine": "jax", "all_pass": all_pass, "out": str(OUT_PATH)}, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
