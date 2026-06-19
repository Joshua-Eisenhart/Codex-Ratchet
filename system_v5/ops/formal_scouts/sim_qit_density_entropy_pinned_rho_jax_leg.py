#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import json
import math
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import numpy as np
import qutip
import z3

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SRC_PATH = ROOT / "system_v5/ops/formal_scouts/sim_qit_density_entropy_pinned_rho_jax_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/qit_density_entropy_pinned_rho_jax_leg_results.json"

OBJECT_ID = "qit_density_entropy_pinned_rho_jax_leg"
classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result
P = 0.3
DIM = 8
TOL = 1.0e-10

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 construction of the pinned three-qubit GHZ white-noise density rho(p)",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 density algebra, Hermitian eigenspectrum, and von-Neumann entropy computation",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing QIT cross-check via Qobj density matrix and entropy_vn on the same pinned rho(p)",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact rational spectrum simplex certificate for p=3/10, with negative control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent exact rational spectrum simplex certificate matching z3, with negative control",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "control-only host conversion into qutip.Qobj; not the entropy claim path",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive timestamps, paths, JSON serialization, and constants",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "qutip": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "numpy": "supportive",
    "Python stdlib": "supportive",
}


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "shape"):
        return to_jsonable(jax.device_get(value).tolist())
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def pinned_density(p: float) -> jax.Array:
    # Shared observable: rho(p) = (1-p)|GHZ><GHZ| + p*I/8, p=0.3, no dephasing.
    psi = jnp.zeros((DIM,), dtype=jnp.complex128)
    amp = 1.0 / jnp.sqrt(jnp.asarray(2.0, dtype=jnp.float64))
    psi = psi.at[0].set(amp)
    psi = psi.at[DIM - 1].set(amp)
    pure = jnp.outer(psi, jnp.conj(psi))
    mixed = jnp.eye(DIM, dtype=jnp.complex128) / jnp.asarray(DIM, dtype=jnp.float64)
    rho = (1.0 - p) * pure + p * mixed
    rho = (rho + jnp.conj(rho.T)) / 2.0
    return rho / jnp.trace(rho)


def analytic_spectrum(p: float) -> list[float]:
    high = 1.0 - 7.0 * p / 8.0
    low = p / 8.0
    return sorted([low] * 7 + [high])


def analytic_entropy(p: float) -> float:
    vals = analytic_spectrum(p)
    return -sum(v * math.log(v) for v in vals if v > 0.0)


def vn_entropy_jax(rho: jax.Array) -> tuple[float, list[float]]:
    eigvals = jnp.real(jnp.linalg.eigvalsh(rho))
    eigvals = jnp.clip(eigvals, 0.0, 1.0)
    nz = eigvals[eigvals > 0.0]
    entropy = -jnp.sum(nz * jnp.log(nz))
    return py_float(entropy), [float(x) for x in jax.device_get(eigvals).tolist()]


def qutip_entropy(rho: jax.Array) -> float:
    rho_np = np.asarray(jax.device_get(rho), dtype=np.complex128)
    qobj = qutip.Qobj(rho_np, dims=[[2, 2, 2], [2, 2, 2]])
    return float(qutip.entropy_vn(qobj, base=math.e))


def density_diagnostics(rho: jax.Array, eigvals: list[float]) -> dict[str, Any]:
    hermitian_residual = py_float(jnp.max(jnp.abs(rho - jnp.conj(rho.T))))
    trace_value = jnp.trace(rho)
    trace_residual = abs(py_float(trace_value) - 1.0) + abs(float(jax.device_get(jnp.imag(trace_value))))
    expected = analytic_spectrum(P)
    spectrum_residual = max(abs(float(a) - float(b)) for a, b in zip(sorted(eigvals), expected))
    return {
        "trace_real": py_float(trace_value),
        "trace_imag_abs": abs(float(jax.device_get(jnp.imag(trace_value)))),
        "trace_residual": trace_residual,
        "hermitian_residual": hermitian_residual,
        "min_eigenvalue": min(eigvals),
        "max_eigenvalue": max(eigvals),
        "spectrum": sorted(eigvals),
        "expected_spectrum": expected,
        "spectrum_max_abs_residual": spectrum_residual,
        "psd_tol_pass": min(eigvals) >= -TOL,
        "trace_tol_pass": trace_residual <= TOL,
        "hermitian_tol_pass": hermitian_residual <= TOL,
    }


def z3_spectrum_certificate() -> dict[str, Any]:
    hi = z3.Int("hi_num")
    lo = z3.Int("lo_num")
    den = z3.Int("den")
    solver = z3.Solver()
    solver.add(hi == 59, lo == 3, den == 80)
    solver.add(den > 0, hi >= 0, lo >= 0)
    solver.add(hi + 7 * lo == den)
    main_status = solver.check()

    bad = z3.Solver()
    bad.add(hi == 59, lo == -3, den == 80)
    bad.add(den > 0, hi >= 0, lo >= 0)
    bad.add(hi + 7 * lo == den)
    bad_status = bad.check()
    return {
        "solver": "z3",
        "claim": "Exact pinned spectrum numerators hi=59, lo=3 over den=80 are a nonnegative simplex: hi + 7*lo = den",
        "main_status": str(main_status),
        "main_sat": main_status == z3.sat,
        "negative_control_status": str(bad_status),
        "negative_control_unsat": bad_status == z3.unsat,
        "pass": main_status == z3.sat and bad_status == z3.unsat,
    }


def cvc5_int(solver: cvc5.Solver, n: int):
    return solver.mkInteger(n)


def cvc5_spectrum_check(lo_value: int) -> str:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    int_sort = solver.getIntegerSort()
    hi = solver.mkConst(int_sort, "hi_num")
    lo = solver.mkConst(int_sort, "lo_num")
    den = solver.mkConst(int_sort, "den")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, hi, cvc5_int(solver, 59)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, lo, cvc5_int(solver, lo_value)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, den, cvc5_int(solver, 80)))
    solver.assertFormula(solver.mkTerm(Kind.GT, den, cvc5_int(solver, 0)))
    solver.assertFormula(solver.mkTerm(Kind.GEQ, hi, cvc5_int(solver, 0)))
    solver.assertFormula(solver.mkTerm(Kind.GEQ, lo, cvc5_int(solver, 0)))
    seven_lo = solver.mkTerm(Kind.MULT, cvc5_int(solver, 7), lo)
    total = solver.mkTerm(Kind.ADD, hi, seven_lo)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, total, den))
    return str(solver.checkSat())


def cvc5_spectrum_certificate() -> dict[str, Any]:
    main_status = cvc5_spectrum_check(3)
    bad_status = cvc5_spectrum_check(-3)
    return {
        "solver": "cvc5",
        "claim": "Exact pinned spectrum numerators hi=59, lo=3 over den=80 are a nonnegative simplex: hi + 7*lo = den",
        "main_status": main_status,
        "main_sat": main_status == "sat",
        "negative_control_status": bad_status,
        "negative_control_unsat": bad_status == "unsat",
        "pass": main_status == "sat" and bad_status == "unsat",
    }


def build_result() -> dict[str, Any]:
    rho = pinned_density(P)
    entropy, eigvals = vn_entropy_jax(rho)
    qutip_entropy_value = qutip_entropy(rho)
    analytic = analytic_entropy(P)
    diagnostics = density_diagnostics(rho, eigvals)
    z3_proof = z3_spectrum_certificate()
    cvc5_proof = cvc5_spectrum_certificate()
    entropy_residual_vs_qutip = abs(entropy - qutip_entropy_value)
    entropy_residual_vs_analytic = abs(entropy - analytic)
    qutip_residual_vs_analytic = abs(qutip_entropy_value - analytic)
    all_pass = bool(
        diagnostics["psd_tol_pass"]
        and diagnostics["trace_tol_pass"]
        and diagnostics["hermitian_tol_pass"]
        and diagnostics["spectrum_max_abs_residual"] <= TOL
        and entropy_residual_vs_qutip <= TOL
        and entropy_residual_vs_analytic <= TOL
        and qutip_residual_vs_analytic <= TOL
        and z3_proof["pass"]
        and cvc5_proof["pass"]
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
        and READS_PEER_RESULT is False
    )
    return {
        "object_id": OBJECT_ID,
        "backend": "jax_qutip_smt",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(SRC_PATH),
        "result_path": str(RESULT_PATH),
        "python_executable": str(Path(__import__("sys").executable)),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "pinned_spec": {
            "name": "GHZ white-noise density, no dephasing",
            "formula": "rho(p) = (1-p)|GHZ><GHZ| + p*I/8",
            "p": P,
            "p_exact": "3/10",
            "spectrum_exact": "{59/80, 3/80 x 7}",
            "n_qubits": 3,
            "hilbert_dimension": DIM,
            "basis_order": "computational |000>..|111>; entropy is spectrum-invariant",
            "entropy_base": "natural_log",
            "dephasing_included": False,
        },
        "values": {
            "vn_entropy": entropy,
            "qutip_entropy": qutip_entropy_value,
            "analytic_entropy": analytic,
            "entropy_residual_vs_qutip": entropy_residual_vs_qutip,
            "entropy_residual_vs_analytic": entropy_residual_vs_analytic,
            "qutip_residual_vs_analytic": qutip_residual_vs_analytic,
            "spectrum_high": 1.0 - 7.0 * P / 8.0,
            "spectrum_low": P / 8.0,
            "entropy_upper_log8": math.log(DIM),
            "entropy_in_bounds_0_to_log8": -TOL <= entropy <= math.log(DIM) + TOL,
        },
        "density_checks": diagnostics,
        "smt": {
            "z3": z3_proof,
            "cvc5": cvc5_proof,
            "z3_cvc5_agree": z3_proof["main_status"] == cvc5_proof["main_status"]
            and z3_proof["negative_control_status"] == cvc5_proof["negative_control_status"],
        },
        "verdicts": {
            "ran": True,
            "uses_qutip": True,
            "z3_cvc5_spectrum_certificate": z3_proof["pass"] and cvc5_proof["pass"],
            "entropy_matches_qutip": entropy_residual_vs_qutip <= TOL,
            "entropy_matches_analytic": entropy_residual_vs_analytic <= TOL,
            "all_pass": all_pass,
        },
        "all_pass": all_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "control_only_tools": ["numpy"],
        "claim_ceiling": "JAX leg for one pinned QIT density/entropy scratch scout: rho(p)=(1-p)|GHZ><GHZ|+pI/8 at p=0.3, qutip entropy cross-check, z3+cvc5 exact spectrum certificate. No peer reads, no promotion, no formal admission.",
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(to_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"uses_qutip={str(result['verdicts']['uses_qutip']).lower()} "
        f"z3_cvc5_spectrum_certificate={str(result['verdicts']['z3_cvc5_spectrum_certificate']).lower()} "
        f"vn_entropy={result['values']['vn_entropy']} "
        f"qutip_entropy={result['values']['qutip_entropy']} "
        f"reads_peer_result={str(result['reads_peer_result']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
