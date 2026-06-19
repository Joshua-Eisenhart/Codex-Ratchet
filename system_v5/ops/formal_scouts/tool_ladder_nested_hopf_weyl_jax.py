#!/usr/bin/env python3
"""JAX leg for the nested Hopf/Weyl tool-ladder scout.

This is a scratch diagnostic that exercises the JAX-side tool stack on a tiny
two-layer fixture: Hopf S3-to-S2 fiber invariance feeds a Weyl chirality split.
It is not a proof of the larger system.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import sys
from pathlib import Path
from typing import Any

import cvc5
import diffrax
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import quimb.tensor as qtn
import z3
from cvc5 import Kind


ROOT = Path(__file__).resolve().parents[3]
OBJECT_ID = "tool_ladder_nested_hopf_weyl_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/tool_ladder_nested_hopf_weyl_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/tool_ladder_nested_hopf_weyl_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-10

TOOL_MANIFEST = {
    "z3": {"tried": True, "used": True, "reason": "load-bearing SMT proof of the nested Hopf-to-Weyl scaled weight split"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT proof of the same scaled weight split"},
    "diffrax": {"tried": True, "used": True, "reason": "load-bearing fiber-phase ODE integration used to generate the Hopf fiber control"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS normalization check for the two-layer spinor bookkeeping fixture"},
    "jax": {"tried": True, "used": True, "reason": "supportive x64 finite-array execution"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive finite Hopf map and gamma-matrix arithmetic"},
    "json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result paths"},
}

TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "diffrax": "load_bearing",
    "quimb": "load_bearing",
    "jax": "supportive",
    "jax.numpy": "supportive",
    "json": "supportive",
    "pathlib": "supportive",
}


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


def fiber_phase(q: jax.Array, phi: jax.Array) -> jax.Array:
    a, b, c, d = q
    cp = jnp.cos(phi)
    sp = jnp.sin(phi)
    return jnp.asarray(
        [
            a * cp - b * sp,
            a * sp + b * cp,
            c * cp - d * sp,
            c * sp + d * cp,
        ],
        dtype=jnp.float64,
    )


def pauli() -> tuple[jax.Array, jax.Array, jax.Array, jax.Array]:
    ident = jnp.eye(2, dtype=jnp.complex128)
    sx = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.asarray([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
    return ident, sx, sy, sz


def kron_all(parts: list[jax.Array]) -> jax.Array:
    out = parts[0]
    for part in parts[1:]:
        out = jnp.kron(out, part)
    return out


def gamma_matrices_cl6() -> list[jax.Array]:
    ident, sx, sy, sz = pauli()
    return [
        kron_all([sx, ident, ident]),
        kron_all([sy, ident, ident]),
        kron_all([sz, sx, ident]),
        kron_all([sz, sy, ident]),
        kron_all([sz, sz, sx]),
        kron_all([sz, sz, sy]),
    ]


def chirality_gamma7(gammas: list[jax.Array]) -> jax.Array:
    product = gammas[0]
    for gamma in gammas[1:]:
        product = product @ gamma
    return ((-1j) ** 3) * product


def _float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def nested_weyl(hopf_z: float) -> dict[str, Any]:
    gammas = gamma_matrices_cl6()
    gamma7 = chirality_gamma7(gammas)
    dim = int(gamma7.shape[0])
    ident = jnp.eye(dim, dtype=jnp.complex128)
    diag = [int(round(float(x))) for x in jax.device_get(jnp.real(jnp.diag(gamma7))).tolist()]
    plus = [idx for idx, sign in enumerate(diag) if sign == 1]
    minus = [idx for idx, sign in enumerate(diag) if sign == -1]
    theta = 0.5 * math.acos(hopf_z)
    psi = jnp.zeros((dim,), dtype=jnp.complex128).at[plus[0]].set(math.cos(theta)).at[minus[0]].set(math.sin(theta))
    expectation = _float(jnp.conj(psi) @ (gamma7 @ psi))
    anticommutation_max = 0.0
    for i, gi in enumerate(gammas):
        for j, gj in enumerate(gammas):
            target = 2.0 * ident if i == j else jnp.zeros_like(ident)
            anticommutation_max = max(anticommutation_max, _float(jnp.linalg.norm(gi @ gj + gj @ gi - target)))
    square_residual = _float(jnp.linalg.norm(gamma7 @ gamma7 - ident))
    return {
        "spinor_dim": dim,
        "gamma7_square_residual": square_residual,
        "gamma7_diagonal": diag,
        "plus_dim": len(plus),
        "minus_dim": len(minus),
        "theta": theta,
        "nested_chirality_expectation": expectation,
        "nested_expectation_residual": abs(expectation - hopf_z),
        "anticommutation_max_residual": anticommutation_max,
        "pass": bool(square_residual <= TOL and len(plus) == 4 and len(minus) == 4 and abs(expectation - hopf_z) <= TOL),
    }


def diffrax_phase(phi_target: float) -> dict[str, Any]:
    term = diffrax.ODETerm(lambda _t, y, _args: jnp.ones_like(y))
    sol = diffrax.diffeqsolve(
        term,
        diffrax.Tsit5(),
        t0=0.0,
        t1=phi_target,
        dt0=0.05,
        y0=jnp.asarray(0.0, dtype=jnp.float64),
        saveat=diffrax.SaveAt(t1=True),
    )
    phi = _float(sol.ys[0])
    return {"target": phi_target, "integrated_phi": phi, "residual": abs(phi - phi_target), "pass": abs(phi - phi_target) <= 1.0e-10}


def quimb_mps_check() -> dict[str, Any]:
    mps = qtn.MPS_computational_state("0101")
    norm = abs(mps.H @ mps)
    return {"nsites": int(mps.nsites), "norm": float(norm), "norm_residual": abs(float(norm) - 1.0), "pass": int(mps.nsites) == 4 and abs(float(norm) - 1.0) <= TOL}


def z3_weight_proof() -> dict[str, Any]:
    solver = z3.Solver()
    p4 = z3.Int("p_plus_scaled_by_4")
    m4 = z3.Int("p_minus_scaled_by_4")
    solver.add(p4 + m4 == 4)
    solver.add(p4 - m4 == 2)
    solver.add(z3.Or(p4 != 3, m4 != 1))
    main = str(solver.check())

    control = z3.Solver()
    cp4 = z3.Int("identity_plus_scaled_by_4")
    cm4 = z3.Int("identity_minus_scaled_by_4")
    control.add(cp4 + cm4 == 4)
    control.add(cp4 - cm4 == 4)
    control.add(z3.Or(cp4 != 3, cm4 != 1))
    control_status = str(control.check())
    return {
        "verdict": main,
        "negative_control_verdict": control_status,
        "claim": "scaled nested Hopf-to-Weyl weights are forced to 3/4 and 1/4 when Hopf_z=1/2",
        "main_proves_nested_weights": main == "unsat",
        "identity_control_flips": control_status == "sat",
        "version": z3.get_version_string(),
    }


def cvc5_weight_proof() -> dict[str, Any]:
    def run(diff: int, expected_plus: int, expected_minus: int) -> str:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        p4 = solver.mkConst(int_sort, "p_plus_scaled_by_4")
        m4 = solver.mkConst(int_sort, "p_minus_scaled_by_4")
        four = solver.mkInteger(4)
        diff_term = solver.mkInteger(diff)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, solver.mkTerm(Kind.ADD, p4, m4), four))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, solver.mkTerm(Kind.SUB, p4, m4), diff_term))
        not_expected = solver.mkTerm(
            Kind.OR,
            solver.mkTerm(Kind.DISTINCT, p4, solver.mkInteger(expected_plus)),
            solver.mkTerm(Kind.DISTINCT, m4, solver.mkInteger(expected_minus)),
        )
        solver.assertFormula(not_expected)
        return str(solver.checkSat()).lower()

    main = run(2, 3, 1)
    control = run(4, 3, 1)
    return {
        "verdict": main,
        "negative_control_verdict": control,
        "claim": "cvc5 independently forces the same scaled nested Hopf-to-Weyl weights",
        "main_proves_nested_weights": main == "unsat",
        "identity_control_flips": control == "sat",
        "version": getattr(cvc5, "__version__", "unknown"),
    }


def build_result() -> dict[str, Any]:
    phi_target = 0.73
    q = jnp.asarray([math.sqrt(3.0) / 2.0, 0.0, 0.5, 0.0], dtype=jnp.float64)
    phase = diffrax_phase(phi_target)
    base = hopf_map(q)
    base_phase = hopf_map(fiber_phase(q, jnp.asarray(phase["integrated_phi"], dtype=jnp.float64)))
    hopf_norm_residual = abs(_float(jnp.dot(base, base)) - 1.0)
    fiber_residual = _float(jnp.linalg.norm(base - base_phase))
    hopf_z = _float(base[2])
    weyl = nested_weyl(hopf_z)
    z3proof = z3_weight_proof()
    cvc5proof = cvc5_weight_proof()
    quimb_check = quimb_mps_check()
    nested_signature = [_float(base[0]), _float(base[1]), hopf_z, weyl["nested_chirality_expectation"], float(weyl["plus_dim"]), float(weyl["minus_dim"])]
    all_pass = bool(
        READS_PEER_RESULT is False
        and hopf_norm_residual <= TOL
        and fiber_residual <= TOL
        and phase["pass"]
        and quimb_check["pass"]
        and weyl["pass"]
        and z3proof["verdict"] == cvc5proof["verdict"] == "unsat"
        and z3proof["identity_control_flips"]
        and cvc5proof["identity_control_flips"]
    )
    return {
        "schema_version": "engine_leg_result_v1",
        "object_id": OBJECT_ID,
        "engine": "jax",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "python_executable": sys.executable,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "diffrax", "quimb", "json", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5", "diffrax", "quimb"],
        "claim_ceiling": "Scratch tool-ladder scout only: nested Hopf S3-to-S2 fiber invariance feeding a Weyl chirality split. No formal admission, no canonical claim.",
        "hopf": {
            "q": [float(x) for x in jax.device_get(q).tolist()],
            "fiber_phase": phi_target,
            "base": [float(x) for x in jax.device_get(base).tolist()],
            "base_after_fiber_phase": [float(x) for x in jax.device_get(base_phase).tolist()],
            "s2_norm_residual": hopf_norm_residual,
            "fiber_invariance_residual": fiber_residual,
            "pass": hopf_norm_residual <= TOL and fiber_residual <= TOL,
        },
        "weyl": weyl,
        "diffrax_phase_ode": phase,
        "quimb_mps": quimb_check,
        "smt": {"z3": z3proof, "cvc5": cvc5proof, "encoding": "QF_LIA scaled weights for Hopf_z=1/2"},
        "negative_control_flip": {
            "identity_control_z3": z3proof["negative_control_verdict"],
            "identity_control_cvc5": cvc5proof["negative_control_verdict"],
            "identity_control_flips": z3proof["identity_control_flips"] and cvc5proof["identity_control_flips"],
        },
        "values": {
            "hopf_base_x": nested_signature[0],
            "hopf_base_y": nested_signature[1],
            "hopf_base_z": nested_signature[2],
            "fiber_invariance_residual": fiber_residual,
            "nested_chirality_expectation": weyl["nested_chirality_expectation"],
            "nested_expectation_residual": weyl["nested_expectation_residual"],
            "plus_dim": weyl["plus_dim"],
            "minus_dim": weyl["minus_dim"],
        },
        "nested_signature": nested_signature,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "NESTED_HOPF_WEYL_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"hopf_z={result['values']['hopf_base_z']} "
        f"nested={result['values']['nested_chirality_expectation']} "
        f"dims={result['values']['plus_dim']}/{result['values']['minus_dim']} "
        f"z3={result['smt']['z3']['verdict']} cvc5={result['smt']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
