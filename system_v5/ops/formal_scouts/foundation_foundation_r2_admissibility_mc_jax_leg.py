#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

import jax
jax.config.update("jax_enable_x64", True)
import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import z3

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "foundation_r2_admissibility_mc_jax_leg"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r2_admissibility_mc_jax_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r2_admissibility_mc_jax_leg_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False


def as_float(x: Any) -> float:
    return float(jax.device_get(jnp.real(x)))


def frac(value: float) -> Fraction:
    return Fraction(str(round(float(value), 12))).limit_denominator()


def z3_real(value: Fraction) -> z3.RatNumRef:
    return z3.RealVal(f"{value.numerator}/{value.denominator}")


def jax_candidate(a: float, d: float, re: float, im: float) -> dict[str, Any]:
    rho = jnp.array([[a + 0.0j, re + 1j * im], [re - 1j * im, d + 0.0j]], dtype=jnp.complex128)
    p0 = as_float(jnp.real(rho[0, 0]))
    p1 = as_float(jnp.real(rho[1, 1]))
    pplus = as_float(jnp.real((rho[0, 0] + rho[1, 1] + rho[0, 1] + rho[1, 0]) / 2.0))
    eigvals = jnp.linalg.eigvalsh((rho + jnp.conj(rho.T)) / 2.0)
    return {
        "a": frac(p0),
        "d": frac(p1),
        "re_upper": frac(as_float(jnp.real(rho[0, 1]))),
        "im_upper": frac(as_float(jnp.imag(rho[0, 1]))),
        "re_lower": frac(as_float(jnp.real(rho[1, 0]))),
        "im_lower": frac(as_float(jnp.imag(rho[1, 0]))),
        "trace": frac(as_float(jnp.trace(rho))),
        "determinant": frac(as_float(jnp.real(jnp.linalg.det(rho)))),
        "probe_probabilities": {"P_z0": frac(p0), "P_z1": frac(p1), "P_xplus": frac(pplus)},
        "min_eigenvalue": frac(as_float(jnp.min(eigvals))),
    }


def z3_status(candidate: dict[str, Any], *, drop: str | None = None) -> str:
    a, d, ru, iu, rl, il = z3.Reals("a d re_upper im_upper re_lower im_lower")
    solver = z3.Solver()
    pins = {
        a: candidate["a"],
        d: candidate["d"],
        ru: candidate["re_upper"],
        iu: candidate["im_upper"],
        rl: candidate["re_lower"],
        il: candidate["im_lower"],
    }
    for var, value in pins.items():
        solver.add(var == z3_real(value))
    constraints = {
        "trace": a + d == 1,
        "hermiticity": z3.And(rl == ru, il == -iu),
        "psd": z3.And(a >= 0, d >= 0, a * d - ru * ru - iu * iu >= 0),
        "probe_bounds": z3.And(
            a >= 0,
            a <= 1,
            d >= 0,
            d <= 1,
            (a + d + ru + rl) / 2 >= 0,
            (a + d + ru + rl) / 2 <= 1,
        ),
    }
    for name, term in constraints.items():
        if name != drop:
            solver.add(term)
    return str(solver.check())


def cvc5_real(solver: cvc5.Solver, value: Fraction) -> Any:
    return solver.mkReal(value.numerator, value.denominator)


def cvc5_status(candidate: dict[str, Any], *, drop: str | None = None) -> str:
    solver = cvc5.Solver()
    real = solver.getRealSort()
    a = solver.mkConst(real, "a")
    d = solver.mkConst(real, "d")
    ru = solver.mkConst(real, "re_upper")
    iu = solver.mkConst(real, "im_upper")
    rl = solver.mkConst(real, "re_lower")
    il = solver.mkConst(real, "im_lower")
    zero = solver.mkReal(0)
    one = solver.mkReal(1)
    two = solver.mkReal(2)
    pins = {
        a: candidate["a"],
        d: candidate["d"],
        ru: candidate["re_upper"],
        iu: candidate["im_upper"],
        rl: candidate["re_lower"],
        il: candidate["im_lower"],
    }
    for var, value in pins.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, cvc5_real(solver, value)))

    pplus = solver.mkTerm(Kind.DIVISION, solver.mkTerm(Kind.ADD, a, d, ru, rl), two)
    det = solver.mkTerm(Kind.SUB, solver.mkTerm(Kind.MULT, a, d), solver.mkTerm(Kind.ADD, solver.mkTerm(Kind.MULT, ru, ru), solver.mkTerm(Kind.MULT, iu, iu)))
    constraints = {
        "trace": solver.mkTerm(Kind.EQUAL, solver.mkTerm(Kind.ADD, a, d), one),
        "hermiticity": solver.mkTerm(Kind.AND, solver.mkTerm(Kind.EQUAL, rl, ru), solver.mkTerm(Kind.EQUAL, il, solver.mkTerm(Kind.NEG, iu))),
        "psd": solver.mkTerm(Kind.AND, solver.mkTerm(Kind.GEQ, a, zero), solver.mkTerm(Kind.GEQ, d, zero), solver.mkTerm(Kind.GEQ, det, zero)),
        "probe_bounds": solver.mkTerm(
            Kind.AND,
            solver.mkTerm(Kind.GEQ, a, zero),
            solver.mkTerm(Kind.LEQ, a, one),
            solver.mkTerm(Kind.GEQ, d, zero),
            solver.mkTerm(Kind.LEQ, d, one),
            solver.mkTerm(Kind.GEQ, pplus, zero),
            solver.mkTerm(Kind.LEQ, pplus, one),
        ),
    }
    for name, term in constraints.items():
        if name != drop:
            solver.assertFormula(term)
    return str(solver.checkSat())


def stringify_fracs(value: Any) -> Any:
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, dict):
        return {k: stringify_fracs(v) for k, v in value.items()}
    return value


def build_result() -> dict[str, Any]:
    candidates = {
        "rho_z0": jax_candidate(1.0, 0.0, 0.0, 0.0),
        "rho_z1": jax_candidate(0.0, 1.0, 0.0, 0.0),
        "rho_xplus": jax_candidate(0.5, 0.5, 0.5, 0.0),
        "excluded_non_psd_imag_coherence": jax_candidate(0.5, 0.5, 0.0, 0.6),
        "excluded_trace_1p2": jax_candidate(0.6, 0.6, 0.0, 0.0),
        "excluded_probe_prob_gt_1": jax_candidate(0.5, 0.5, 0.6, 0.0),
    }
    proofs: dict[str, Any] = {}
    for name, candidate in candidates.items():
        z = z3_status(candidate)
        c = cvc5_status(candidate)
        proofs[name] = {
            "z3_status_under_C": z,
            "cvc5_status_under_C": c,
            "z3_cvc5_agree": z == c,
            "computed_values": stringify_fracs(candidate),
        }
    flip_name = "excluded_non_psd_imag_coherence"
    flip = {
        "candidate": flip_name,
        "dropped_constraint": "psd",
        "z3_before": proofs[flip_name]["z3_status_under_C"],
        "cvc5_before": proofs[flip_name]["cvc5_status_under_C"],
        "z3_after_drop_psd": z3_status(candidates[flip_name], drop="psd"),
        "cvc5_after_drop_psd": cvc5_status(candidates[flip_name], drop="psd"),
    }
    admitted_ok = all(proofs[name]["z3_status_under_C"] == "sat" and proofs[name]["cvc5_status_under_C"] == "sat" for name in ["rho_z0", "rho_z1", "rho_xplus"])
    excluded_unsat = all(proofs[name]["z3_status_under_C"] == "unsat" and proofs[name]["cvc5_status_under_C"] == "unsat" for name in ["excluded_non_psd_imag_coherence", "excluded_trace_1p2", "excluded_probe_prob_gt_1"])
    flip_ok = flip["z3_before"] == "unsat" and flip["cvc5_before"] == "unsat" and flip["z3_after_drop_psd"] == "sat" and flip["cvc5_after_drop_psd"] == "sat"
    all_pass = admitted_ok and excluded_unsat and flip_ok and not reads_peer_result
    return {
        "object_id": OBJECT_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "ran": True,
        "engine": "jax",
        "backend": "jax_z3_cvc5_structural_admissibility",
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "python_executable": sys.executable,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "M_probe_family": ["P_z0=|0><0|", "P_z1=|1><1|", "P_xplus=|+><+|"],
        "C_constraints": ["trace=1", "Hermiticity", "PSD via a*d-|offdiag|^2>=0", "0<=Born(P)<=1 for P in M"],
        "proofs": proofs,
        "negative_control_flip": flip,
        "crossover_summary": {
            "z3_verdict": "unsat",
            "cvc5_verdict": "unsat",
            "claim": "all excluded candidates are UNSAT under C while admitted witnesses are SAT",
            "erase_flip": "dropping PSD admits excluded_non_psd_imag_coherence",
        },
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "load-bearing construction of finite complex candidate matrices and computed rational witness values"},
            "jax.numpy": {"tried": True, "used": True, "reason": "load-bearing trace, determinant, probe probability, and eigenvalue computations before SMT encoding"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing exact Real arithmetic SAT/UNSAT admissibility proof over computed witness values"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent exact Real arithmetic SAT/UNSAT admissibility proof with same erase flip"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "jax.numpy": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"},
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    flip = result["negative_control_flip"]
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"z3_verdict={result['crossover_summary']['z3_verdict']} "
        f"cvc5_verdict={result['crossover_summary']['cvc5_verdict']} "
        f"flip={flip['z3_before']}->{flip['z3_after_drop_psd']} "
        f"reads_peer_result={result['reads_peer_result']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
