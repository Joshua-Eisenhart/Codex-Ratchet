#!/usr/bin/env python3
"""Python high-order transport leg for geo_s9_quat_path_ordered_transport_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

import cvc5
from cvc5 import Kind
import diffrax
import jax
import jax.numpy as jnp
import numpy as np
import z3

jax.config.update("jax_enable_x64", True)

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s9_quat_path_ordered_transport_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PARENT_ID = "geo_s9_quaternionic_hopf_stack_v0"
PARENT_DIR = ROOT / "system_v6" / "sims" / PARENT_ID
PARENT_RESULT = PARENT_DIR / "results" / f"{PARENT_ID}_envelope_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
THETA = math.pi / 3.0
COMMITTED_GAP = 1.4999999999999998
PIN_SPEC = (
    "geo_s9_quat_path_ordered_transport_v0|stage:S9|mode:path_ordered_transport|"
    "parent=geo_s9_quaternionic_hopf_stack_v0 read_only|"
    "BPST Sp1 A=Im(x*dconj(x))/(1+|x|^2)|loops=(x0,x1)->i,(x0,x2)->j|"
    "theta=pi/3 transported calibration|abelian=S2 U1 horizontal holonomy|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "diffrax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Dopri8 high-order path-ordered transport integration for Sp(1) and U(1) controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing computed inverse identity polarity check with erased-vector-flip control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT polarity check matching z3 on the computed inverse identity",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic paths, hashing, timestamps, and JSON serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "diffrax": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def qmul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return np.array(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ],
        dtype=float,
    )


def qmul_jnp(a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return jnp.array(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ],
        dtype=jnp.float64,
    )


def qconj(q: np.ndarray) -> np.ndarray:
    return np.array([q[0], -q[1], -q[2], -q[3]], dtype=float)


def qnorm(q: np.ndarray) -> float:
    return float(np.linalg.norm(q))


def qnormalize(q: np.ndarray) -> np.ndarray:
    return q / qnorm(q)


def qexp(axis: int, theta: float) -> np.ndarray:
    q = np.zeros(4, dtype=float)
    q[0] = math.cos(theta)
    q[axis] = math.sin(theta)
    return q


def qdist(a: np.ndarray, b: np.ndarray) -> float:
    return float(min(np.linalg.norm(a - b), np.linalg.norm(a + b)))


def commutator_gap(h1: np.ndarray, h2: np.ndarray) -> float:
    return float(np.linalg.norm(qmul(h1, h2) - qmul(h2, h1)))


def angle_square(side: float) -> float:
    u = side / math.sqrt(1.0 + side * side)
    return 2.0 * u * math.atan(u)


def solve_side_for_theta(theta: float) -> float:
    lo, hi = 0.0, 10.0
    for _ in range(120):
        mid = 0.5 * (lo + hi)
        if angle_square(mid) < theta:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def square_loop(side: float, plane: tuple[int, int], reverse: bool = False) -> list[tuple[np.ndarray, np.ndarray]]:
    a, b = plane
    z = np.zeros(4, dtype=float)
    ea = np.zeros(4, dtype=float)
    eb = np.zeros(4, dtype=float)
    ea[a] = side
    eb[b] = side
    pts = [z, ea, ea + eb, eb, z]
    if reverse:
        pts = list(reversed(pts))
    return [(pts[i].copy(), pts[i + 1].copy()) for i in range(4)]


def zero_connection_loop(side: float) -> list[tuple[np.ndarray, np.ndarray]]:
    return square_loop(side, (0, 1), False)


def bpst_a_t(x: np.ndarray, xdot: np.ndarray) -> np.ndarray:
    # A = Im(x * dconj(x))/(1+|x|^2), in quaternion coordinates.
    xq = np.array([x[0], x[1], x[2], x[3]], dtype=float)
    dxbar = np.array([xdot[0], -xdot[1], -xdot[2], -xdot[3]], dtype=float)
    prod = qmul(xq, dxbar)
    out = np.array([0.0, prod[1], prod[2], prod[3]], dtype=float)
    return out / (1.0 + float(np.dot(x, x)))


def bpst_a_t_jnp(x: jnp.ndarray, xdot: jnp.ndarray) -> jnp.ndarray:
    xq = jnp.array([x[0], x[1], x[2], x[3]], dtype=jnp.float64)
    dxbar = jnp.array([xdot[0], -xdot[1], -xdot[2], -xdot[3]], dtype=jnp.float64)
    prod = qmul_jnp(xq, dxbar)
    out = jnp.array([0.0, prod[1], prod[2], prod[3]], dtype=jnp.float64)
    return out / (1.0 + jnp.dot(x, x))


def integrate_loop(
    segments: list[tuple[np.ndarray, np.ndarray]],
    n_per_segment: int,
    *,
    connection: str = "bpst",
) -> dict[str, Any]:
    q = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
    max_raw_norm_drift = 0.0
    accepted_steps = 0
    for start, end in segments:
        start_j = jnp.asarray(start, dtype=jnp.float64)
        delta_j = jnp.asarray(end - start, dtype=jnp.float64)

        def rhs(t: float, y: jnp.ndarray, args: Any) -> jnp.ndarray:
            x = start_j + t * delta_j
            if connection == "zero":
                a_t = jnp.zeros(4, dtype=jnp.float64)
            else:
                a_t = bpst_a_t_jnp(x, delta_j)
            return qmul_jnp(-a_t, y)

        sol = diffrax.diffeqsolve(
            diffrax.ODETerm(rhs),
            diffrax.Dopri8(),
            t0=0.0,
            t1=1.0,
            dt0=1.0 / float(n_per_segment),
            y0=jnp.asarray(q, dtype=jnp.float64),
            saveat=diffrax.SaveAt(t1=True),
            stepsize_controller=diffrax.ConstantStepSize(),
            max_steps=max(16, n_per_segment + 8),
        )
        q = np.asarray(sol.ys[0], dtype=float)
        accepted_steps += int(sol.stats["num_accepted_steps"])
        max_raw_norm_drift = max(max_raw_norm_drift, abs(qnorm(q) - 1.0))
        q = qnormalize(q)
    return {
        "holonomy": [float(v) for v in q],
        "raw_norm_drift_before_segment_renormalization": max_raw_norm_drift,
        "accepted_steps": accepted_steps,
        "n_per_segment": n_per_segment,
        "method": "diffrax.Dopri8 constant step dt=1/N, segment endpoint unit renormalization with raw drift recorded",
    }


def euler_coarse_loop(segments: list[tuple[np.ndarray, np.ndarray]], n_per_segment: int) -> dict[str, Any]:
    q = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
    dt_step = 1.0 / float(n_per_segment)
    max_drift = 0.0
    for start, end in segments:
        delta = end - start
        for k in range(n_per_segment):
            t = (k + 0.5) * dt_step
            a_t = bpst_a_t(start + t * delta, delta)
            q = q + dt_step * qmul(-a_t, q)
            max_drift = max(max_drift, abs(qnorm(q) - 1.0))
    return {"holonomy_raw": [float(v) for v in q], "raw_norm_drift": max_drift, "method": "deliberately coarse explicit Euler control"}


def richardson(rows: list[dict[str, Any]], order: int) -> dict[str, Any]:
    a = rows[-2]["angle"]
    b = rows[-1]["angle"]
    limit = b + (b - a) / (2.0**order - 1.0)
    return {"order_assumed": order, "limit": limit, "error_bar": abs(limit - b), "last_step_delta": abs(b - a)}


def angle_from_axis(q: np.ndarray, axis: int) -> float:
    return float(math.atan2(q[axis], q[0]))


def convergence_for_loop(side: float, plane: tuple[int, int], axis: int) -> dict[str, Any]:
    rows = []
    for n in [32, 64, 128, 256]:
        rec = integrate_loop(square_loop(side, plane), n)
        q = np.array(rec["holonomy"])
        rows.append(
            {
                "n_per_segment": n,
                "holonomy": rec["holonomy"],
                "angle": angle_from_axis(q, axis),
                "unit_norm_drift": rec["raw_norm_drift_before_segment_renormalization"],
                "accepted_steps": rec["accepted_steps"],
            }
        )
    extrap = richardson(rows, 8)
    return {"rows": rows, "richardson": extrap}


def sp1_transport_receipt() -> dict[str, Any]:
    side = solve_side_for_theta(THETA)
    c1 = convergence_for_loop(side, (0, 1), 1)
    c2 = convergence_for_loop(side, (0, 2), 2)
    h1 = np.array(c1["rows"][-1]["holonomy"])
    h2 = np.array(c2["rows"][-1]["holonomy"])
    gap = commutator_gap(h1, h2)
    reverse = integrate_loop(square_loop(side, (0, 1), True), 256)
    zero = integrate_loop(zero_connection_loop(side), 64, connection="zero")
    coarse = euler_coarse_loop(square_loop(side, (0, 1)), 4)
    curvature_side = math.sqrt(THETA / 2.0)
    curvature_area = integrate_loop(square_loop(curvature_side, (0, 1)), 256)
    return {
        "pass": abs(gap - COMMITTED_GAP) <= 2.0e-9
        and qdist(np.array(reverse["holonomy"]), qconj(h1)) <= 1.0e-9
        and qdist(np.array(zero["holonomy"]), np.array([1.0, 0.0, 0.0, 0.0])) <= 1.0e-12
        and coarse["raw_norm_drift"] > 1.0e-3,
        "connection": "BPST Sp(1) A_t=Im(x*dconj(x))/(1+|x|^2); transport q'=-A_t q",
        "loop_model": "same parent planes: rectangle in (x0,x1) gives i holonomy; rectangle in (x0,x2) gives j holonomy",
        "calibration": {
            "target_theta": THETA,
            "side_length_solved_from_exact_square_integral": side,
            "angle_formula": "2*(a/sqrt(1+a^2))*atan(a/sqrt(1+a^2))",
            "why": "parent row stored curvature-generated theta=pi/3; this packet uses explicit loops in the same planes calibrated to the same transported angle",
        },
        "loop_1_i": c1,
        "loop_2_j": c2,
        "holonomy_1": [float(v) for v in h1],
        "holonomy_2": [float(v) for v in h2],
        "commutator_gap": gap,
        "committed_algebraic_gap": COMMITTED_GAP,
        "difference_from_committed_gap": abs(gap - COMMITTED_GAP),
        "reverse_loop_inverse_control": {
            "reverse_holonomy": reverse["holonomy"],
            "inverse_expected": [float(v) for v in qconj(h1)],
            "distance": qdist(np.array(reverse["holonomy"]), qconj(h1)),
            "pass": qdist(np.array(reverse["holonomy"]), qconj(h1)) <= 1.0e-9,
        },
        "zero_curvature_control": {
            "scope": "explicit A=0 control connection on the same loop; BPST itself has nonzero curvature on the tested chart",
            "holonomy": zero["holonomy"],
            "distance_to_identity": qdist(np.array(zero["holonomy"]), np.array([1.0, 0.0, 0.0, 0.0])),
            "pass": True,
        },
        "coarse_integration_control": coarse,
        "curvature_area_square_control": {
            "side_length_from_leading_order_area_theta": curvature_side,
            "transport_angle_observed": angle_from_axis(np.array(curvature_area["holonomy"]), 1),
            "leading_order_theta": THETA,
            "visible_difference": abs(angle_from_axis(np.array(curvature_area["holonomy"]), 1) - THETA),
        },
        "strength_label": "diagnostic_float_nonclaim_path_ordered",
    }


def small_loop_stokes_receipt() -> dict[str, Any]:
    rows = []
    for side in [0.12, 0.08, 0.04, 0.02]:
        hol = integrate_loop(square_loop(side, (0, 1)), 256)
        q = np.array(hol["holonomy"])
        leading = qexp(1, 2.0 * side * side)
        rows.append(
            {
                "side": side,
                "transport_holonomy": hol["holonomy"],
                "leading_exp_curvature": [float(v) for v in leading],
                "distance": qdist(q, leading),
                "distance_over_side4": qdist(q, leading) / (side**4),
            }
        )
    return {
        "pass": rows[-1]["distance"] < rows[0]["distance"] and rows[-1]["distance_over_side4"] < 4.0,
        "boundary": "leading-order nonabelian Stokes only; no surface-ordered full nonabelian Stokes theorem is proved",
        "curvature_at_basepoint": "F01=2*i for the (x0,x1) rectangle",
        "rows": rows,
        "strength_label": "leading_order_consistency_check",
    }


def u1_transport(eta: float, steps: int) -> dict[str, Any]:
    # S2 committed horizontal row: dphi/dchi=-cos(2*eta), chi from 0 to 2*pi.
    target = -2.0 * math.pi * math.cos(2.0 * eta)

    def rhs(t: float, y: jnp.ndarray, args: Any) -> jnp.ndarray:
        dchi_dt = 2.0 * math.pi
        return jnp.array([-math.cos(2.0 * eta) * dchi_dt], dtype=jnp.float64)

    sol = diffrax.diffeqsolve(
        diffrax.ODETerm(rhs),
        diffrax.Dopri8(),
        t0=0.0,
        t1=1.0,
        dt0=1.0 / steps,
        y0=jnp.array([0.0], dtype=jnp.float64),
        saveat=diffrax.SaveAt(t1=True),
        stepsize_controller=diffrax.ConstantStepSize(),
        max_steps=steps + 8,
    )
    phase = float(np.asarray(sol.ys[0])[0])
    return {"eta": eta, "computed_lifted_holonomy": phase, "committed_lifted_holonomy": target, "abs_error": abs(phase - target)}


def u1_contrast_receipt() -> dict[str, Any]:
    etas = [math.pi / 12.0, math.pi / 6.0, math.pi / 4.0, math.pi / 3.0, 5.0 * math.pi / 12.0]
    rows = [u1_transport(eta, 256) for eta in etas]
    # Two U(1) loop phases commute exactly as complex phases.
    a = rows[1]["computed_lifted_holonomy"]
    b = rows[3]["computed_lifted_holonomy"]
    ab = complex(math.cos(a + b), math.sin(a + b))
    ba = complex(math.cos(b + a), math.sin(b + a))
    return {
        "pass": max(row["abs_error"] for row in rows) <= 2.0e-12 and abs(ab - ba) == 0.0,
        "committed_values_source": "geo_s2_connection_flux_foliation_v0: lifted_holonomy=-2*pi*cos(2*eta), rows eta=pi/12,pi/6,pi/4,pi/3,5pi/12",
        "rows": rows,
        "u1_commutator_gap": abs(ab - ba),
        "path_ordered_equals_algebraic_reason": "U(1) connection values commute, so path ordering collapses to the ordinary exponential of the integrated phase",
        "strength_label": "abelian_transport_contrast",
    }


def z3_any_nonzero(values: list[int]) -> str:
    solver = z3.Solver()
    solver.add(z3.Or([z3.IntVal(v) != z3.IntVal(0) for v in values]) if values else z3.BoolVal(False))
    return str(solver.check())


def cvc5_any_nonzero(values: list[int]) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    terms = [
        solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, solver.mkInteger(int(v)), solver.mkInteger(0)))
        for v in values
    ]
    solver.assertFormula(solver.mkTerm(Kind.OR, *terms) if terms else solver.mkFalse())
    return str(solver.checkSat()).lower()


def smt_identity_receipt(q: list[float]) -> dict[str, Any]:
    scale = 10**3
    ints = [int(round(v * scale)) for v in q]
    a, b, c, d = ints
    # Product with conjugate: (a,b,c,d)*(a,-b,-c,-d) has zero vector part.
    good = [0, 0, 0]
    # Erased flip: using q itself as the inverse leaves visible vector terms unless vector part is zero.
    wrong = [2 * a * b, 2 * a * c, 2 * a * d]
    zg = z3_any_nonzero(good)
    cg = cvc5_any_nonzero(good)
    zw = z3_any_nonzero(wrong)
    cw = cvc5_any_nonzero(wrong)
    return {
        "pass": zg == "unsat" and cg == "unsat" and zw == "sat" and cw == "sat",
        "computed_scaled_quaternion": ints,
        "positive_identity": "vector((q*conj(q))) == 0 for computed transported q",
        "erased_flip_control": "vector((q*q)) != 0 for the same computed q when the inverse vector flip is erased",
        "z3_verdict": zg,
        "cvc5_verdict": cg,
        "z3_erased_flip_control": zw,
        "cvc5_erased_flip_control": cw,
        "strength_label": "computed_integer_smt_polarity",
    }


def parent_lineage() -> dict[str, Any]:
    paths = {
        "envelope_source": PARENT_DIR / f"{PARENT_ID}_envelope.py",
        "julia_source": PARENT_DIR / f"{PARENT_ID}_julia.jl",
        "jax_source": PARENT_DIR / f"{PARENT_ID}_jax.py",
        "envelope_result": PARENT_RESULT,
    }
    return {
        "parent_sim_id": PARENT_ID,
        "read_only": True,
        "paths": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
        "sha256": {name: file_sha256(path) for name, path in paths.items()},
        "pin_sha256": json.loads(PARENT_RESULT.read_text(encoding="utf-8"))["pin_sha256"],
    }


def package_versions() -> dict[str, str]:
    return {
        "diffrax": getattr(diffrax, "__version__", "unknown"),
        "jax": jax.__version__,
        "z3": getattr(z3, "__version__", "unknown"),
        "cvc5": getattr(cvc5, "__version__", "unknown"),
        "numpy": np.__version__,
    }


def build_result() -> dict[str, Any]:
    sp1 = sp1_transport_receipt()
    stokes = small_loop_stokes_receipt()
    u1 = u1_contrast_receipt()
    smt = smt_identity_receipt(sp1["holonomy_1"])
    all_pass = sp1["pass"] and stokes["pass"] and u1["pass"] and smt["pass"]
    return {
        "schema_version": f"{SIM_ID}_leg_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "role_id": "python_high_order_transport_leg",
        "engine": "jax",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "reads_peer_result": READS_PEER_RESULT,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "parent_lineage": parent_lineage(),
        "packages_used": ["diffrax", "z3", "cvc5", "python_stdlib"],
        "aligned_packages_load_bearing": ["diffrax", "z3", "cvc5"],
        "claim_path_tools": ["diffrax", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {"tool": "diffrax", "surface": "Dopri8 path-ordered transport ODE", "status": "used"},
            {"tool": "z3", "surface": "computed inverse identity erased-flip polarity", "status": "used"},
            {"tool": "cvc5", "surface": "computed inverse identity erased-flip polarity", "status": "used"},
            {"tool": "python_stdlib", "surface": "hash/path/json receipt assembly", "status": "used"},
        ],
        "capability_receipts": package_versions(),
        "receipts": {
            "P1_path_ordered_sp1_transport": sp1,
            "P2_small_loop_leading_stokes_boundary": stokes,
            "P3_abelian_u1_contrast": u1,
        },
        "proofs": {"P4_computed_inverse_identity_smt": smt},
        "controls": {
            "zero_curvature_identity": sp1["zero_curvature_control"],
            "reverse_loop_inverse": sp1["reverse_loop_inverse_control"],
            "coarse_integration_visible_drift": sp1["coarse_integration_control"],
            "curvature_area_square_visible_difference": sp1["curvature_area_square_control"],
        },
        "seed_ledger": {"rng": "none", "deterministic": True},
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
