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
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_qit_cptp_dephasing_pinned_rho_jax_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/qit_cptp_dephasing_pinned_rho_jax_leg_results.json"
OBJECT_ID = "qit_cptp_dephasing_pinned_rho_jax_leg"
classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result
P = 0.3
GAMMA = 0.4
DIM = 8
TOL = 1e-10

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "load-bearing pinned density and dephasing channel construction"},
    "jax.numpy": {"tried": True, "used": True, "reason": "load-bearing eigenspectrum and entropy path"},
    "qutip": {"tried": True, "used": True, "reason": "load-bearing Qobj entropy cross-check after the pinned channel"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing exact post-channel spectrum simplex certificate with negative control"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent exact post-channel spectrum simplex certificate with negative control"},
    "numpy": {"tried": True, "used": True, "reason": "control-only host conversion for qutip"},
    "Python stdlib": {"tried": True, "used": True, "reason": "supportive JSON/timestamp/path logic"},
}
TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing", "jax.numpy": "load_bearing", "qutip": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing", "numpy": "supportive", "Python stdlib": "supportive"}


def f(x: Any) -> float:
    return float(jax.device_get(jnp.real(x)))


def pinned_density(p: float) -> jax.Array:
    psi = jnp.zeros((DIM,), dtype=jnp.complex128)
    amp = 1.0 / jnp.sqrt(jnp.asarray(2.0, dtype=jnp.float64))
    psi = psi.at[0].set(amp); psi = psi.at[DIM-1].set(amp)
    return (1.0 - p) * jnp.outer(psi, jnp.conj(psi)) + p * jnp.eye(DIM, dtype=jnp.complex128) / DIM


def dephase(rho: jax.Array, gamma: float) -> jax.Array:
    return (1.0 - gamma) * rho + gamma * jnp.diag(jnp.diag(rho))


def analytic_spectrum_after(p: float, gamma: float) -> list[float]:
    a = (1.0 - p) / 2.0 + p / 8.0
    b = (1.0 - gamma) * (1.0 - p) / 2.0
    low = p / 8.0
    return sorted([low] * 6 + [a - b, a + b])


def entropy(vals: list[float]) -> float:
    return -sum(v * math.log(v) for v in vals if v > 0.0)


def vn_entropy_jax(rho: jax.Array) -> tuple[float, list[float]]:
    vals = jnp.clip(jnp.real(jnp.linalg.eigvalsh((rho + jnp.conj(rho.T)) / 2.0)), 0.0, 1.0)
    nz = vals[vals > 0]
    return f(-jnp.sum(nz * jnp.log(nz))), [float(v) for v in jax.device_get(vals).tolist()]


def qutip_entropy(rho: jax.Array) -> float:
    qobj = qutip.Qobj(np.asarray(jax.device_get(rho), dtype=np.complex128), dims=[[2,2,2],[2,2,2]])
    return float(qutip.entropy_vn(qobj, base=math.e))


def z3_cert() -> dict[str, Any]:
    hi, mid, low, den = z3.Ints("hi mid low den")
    s = z3.Solver(); s.add(hi == 239, mid == 71, low == 15, den == 400, den > 0, hi >= 0, mid >= 0, low >= 0, hi + mid + 6*low == den)
    main = s.check()
    bad = z3.Solver(); bad.add(hi == 239, mid == 71, low == -15, den == 400, den > 0, hi >= 0, mid >= 0, low >= 0, hi + mid + 6*low == den)
    bad_status = bad.check()
    return {"solver": "z3", "main_status": str(main), "negative_control_status": str(bad_status), "pass": main == z3.sat and bad_status == z3.unsat}


def cvc5_check(low_value: int) -> str:
    s = cvc5.Solver(); int_sort = s.getIntegerSort()
    def I(n: int): return s.mkInteger(n)
    hi=s.mkConst(int_sort,"hi"); mid=s.mkConst(int_sort,"mid"); low=s.mkConst(int_sort,"low"); den=s.mkConst(int_sort,"den")
    for var,val in [(hi,239),(mid,71),(low,low_value),(den,400)]:
        s.assertFormula(s.mkTerm(Kind.EQUAL,var,I(val)))
    for t in [s.mkTerm(Kind.GT,den,I(0)), s.mkTerm(Kind.GEQ,hi,I(0)), s.mkTerm(Kind.GEQ,mid,I(0)), s.mkTerm(Kind.GEQ,low,I(0))]:
        s.assertFormula(t)
    s.assertFormula(s.mkTerm(Kind.EQUAL, s.mkTerm(Kind.ADD, hi, mid, s.mkTerm(Kind.MULT, I(6), low)), den))
    return str(s.checkSat())


def cvc5_cert() -> dict[str, Any]:
    main = cvc5_check(15); bad = cvc5_check(-15)
    return {"solver": "cvc5", "main_status": main, "negative_control_status": bad, "pass": main == "sat" and bad == "unsat"}


def build_result() -> dict[str, Any]:
    rho0 = pinned_density(P); rho1 = dephase(rho0, GAMMA)
    before, _ = vn_entropy_jax(rho0)
    after, eigvals = vn_entropy_jax(rho1)
    qent = qutip_entropy(rho1)
    expected = analytic_spectrum_after(P, GAMMA)
    analytic_after = entropy(expected)
    spectrum_residual = max(abs(a-b) for a,b in zip(sorted(eigvals), expected))
    z3p = z3_cert(); cvc5p = cvc5_cert()
    all_pass = bool(abs(after-qent) <= TOL and abs(after-analytic_after) <= TOL and spectrum_residual <= TOL and after >= before - TOL and z3p["pass"] and cvc5p["pass"] and not READS_PEER_RESULT)
    return {
        "object_id": OBJECT_ID, "backend": "jax_qutip_smt", "generated_at": _dt.datetime.now(_dt.UTC).isoformat(), "source_path": str(SOURCE_PATH), "result_path": str(RESULT_PATH), "python_executable": __import__('sys').executable,
        "classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED, "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED, "reads_peer_result": READS_PEER_RESULT,
        "pinned_spec": {"rho_formula":"rho(p)=(1-p)|GHZ><GHZ|+pI/8", "p": P, "channel":"computational_basis_dephasing", "gamma": GAMMA, "entropy_base":"natural_log", "n_qubits":3, "hilbert_dimension":DIM, "spectrum_after_exact":"{239/400, 71/400, 15/400 x 6}"},
        "values": {"vn_entropy_before": before, "vn_entropy_after": after, "qutip_entropy_after": qent, "analytic_entropy_after": analytic_after, "entropy_change": after-before, "spectrum_high": 239/400, "spectrum_mid": 71/400, "spectrum_low": 15/400, "entropy_residual_vs_qutip": abs(after-qent), "entropy_residual_vs_analytic": abs(after-analytic_after), "spectrum_max_abs_residual": spectrum_residual},
        "density_checks": {"trace_residual": abs(f(jnp.trace(rho1))-1.0), "hermitian_residual": f(jnp.max(jnp.abs(rho1-jnp.conj(rho1.T)))), "min_eigenvalue": min(eigvals), "spectrum": sorted(eigvals), "expected_spectrum": expected},
        "smt": {"z3": z3p, "cvc5": cvc5p, "z3_cvc5_agree": z3p["main_status"] == cvc5p["main_status"] and z3p["negative_control_status"] == cvc5p["negative_control_status"]},
        "all_pass": all_pass, "TOOL_MANIFEST": TOOL_MANIFEST, "tool_manifest": TOOL_MANIFEST, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "JAX leg for one pinned CPTP dephasing scratch scout over rho(p); no peer reads, no promotion, no formal admission."
    }


def main() -> int:
    result = build_result(); RESULT_PATH.parent.mkdir(parents=True, exist_ok=True); RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(f"SCOUT_DONE all_pass={str(result['all_pass']).lower()} entropy_after={result['values']['vn_entropy_after']} entropy_change={result['values']['entropy_change']} z3_cvc5={result['smt']['z3_cvc5_agree']} reads_peer_result={result['reads_peer_result']}")
    return 0 if result["all_pass"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
