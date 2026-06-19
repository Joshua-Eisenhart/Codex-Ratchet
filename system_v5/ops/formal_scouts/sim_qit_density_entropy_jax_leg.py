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
import qutip
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SRC_PATH = ROOT / "system_v5/ops/formal_scouts/sim_qit_density_entropy_jax_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/qit_density_entropy_jax_leg_results.json"

P = 0.3
DIM = 8
QUBITS = 3
MEASURED_SPECTRUM = [0.7375] + [0.0375] * 7
EXPECTED_ENTROPY = 1.086457
ENTROPY_TOL = 5.0e-6
SPECTRUM_TOL = 1.0e-12

RHO_SPEC = {
    "state": "GHZ_3qubit",
    "formula": "(1-p)|psi><psi| + p*I8/8",
    "p": 0.3,
    "basis": "computational e0..e7, |000>=e0, |111>=e7",
    "dephasing": False,
    "entropy_base": "e",
}

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 construction of the pinned 3-qubit GHZ depolarizing rho(p) and eigenspectrum check",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density algebra and spectrum computation for the pinned rho(p)",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Qobj construction of GHZ rho(p) and von Neumann entropy computation in nats",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT proof of simplex, mixed-spectrum, and pure-state erase-flip verdicts",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT proof matching z3 on every spectrum verdict",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive paths, JSON serialization, constants, and timestamps",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "qutip": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "Python stdlib": "supportive",
}


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def build_ghz_qutip() -> qutip.Qobj:
    zero = qutip.basis(2, 0)
    one = qutip.basis(2, 1)
    ket_000 = qutip.tensor(zero, zero, zero)
    ket_111 = qutip.tensor(one, one, one)
    return (ket_000 + ket_111).unit()


def build_rho_qutip(p: float) -> qutip.Qobj:
    psi = build_ghz_qutip()
    pure = psi.proj()
    identity = qutip.qeye([2, 2, 2])
    return (1.0 - p) * pure + p * (identity / DIM)


def build_rho_jax(p: float) -> jax.Array:
    psi = jnp.zeros((DIM,), dtype=jnp.complex128)
    amp = jnp.asarray(1.0 / math.sqrt(2.0), dtype=jnp.float64)
    psi = psi.at[0].set(amp)
    psi = psi.at[7].set(amp)
    pure = jnp.outer(psi, jnp.conj(psi))
    identity = jnp.eye(DIM, dtype=jnp.complex128)
    return (1.0 - p) * pure + p * (identity / jnp.asarray(DIM, dtype=jnp.float64))


def qutip_entropy_nats(rho: qutip.Qobj) -> float:
    return float(qutip.entropy_vn(rho, base=math.e))


def jax_spectrum(rho: jax.Array) -> list[float]:
    eigvals = jnp.real(jnp.linalg.eigvalsh(rho))
    return [float(x) for x in jax.device_get(eigvals).tolist()]


def density_diagnostics(rho_jax: jax.Array, rho_qutip: qutip.Qobj, eigvals: list[float]) -> dict[str, Any]:
    qutip_dense = jnp.asarray(rho_qutip.full(), dtype=jnp.complex128)
    return {
        "trace": py_float(jnp.trace(rho_jax)),
        "hermitian_residual": py_float(jnp.max(jnp.abs(rho_jax - jnp.conj(rho_jax.T)))),
        "jax_qutip_max_abs_diff": py_float(jnp.max(jnp.abs(rho_jax - qutip_dense))),
        "eigenvalues_ascending": eigvals,
        "measured_spectrum_descending": sorted(eigvals, reverse=True),
        "expected_spectrum_descending": MEASURED_SPECTRUM,
        "spectrum_matches_expected": all(
            abs(a - b) <= SPECTRUM_TOL
            for a, b in zip(sorted(eigvals, reverse=True), MEASURED_SPECTRUM, strict=True)
        ),
    }


def _z3_lambdas(solver: z3.Solver) -> list[z3.ArithRef]:
    lambdas = [z3.Real(f"lambda_{i}") for i in range(DIM)]
    solver.add(z3.Sum(lambdas) == z3.RealVal("1"))
    for lam in lambdas:
        solver.add(lam >= z3.RealVal("0"))
        solver.add(lam <= z3.RealVal("1"))
    return lambdas


def _z3_assert_measured_spectrum(solver: z3.Solver, lambdas: list[z3.ArithRef]) -> None:
    for lam, value in zip(lambdas, MEASURED_SPECTRUM, strict=True):
        solver.add(lam == z3.RealVal(str(value)))


def _z3_assert_pure(solver: z3.Solver, lambdas: list[z3.ArithRef]) -> None:
    pure_cases = []
    zero = z3.RealVal("0")
    one = z3.RealVal("1")
    for i, lam in enumerate(lambdas):
        pure_cases.append(z3.And(lam == one, *[other == zero for j, other in enumerate(lambdas) if j != i]))
    solver.add(z3.Or(*pure_cases))


def z3_spectrum_proof() -> dict[str, Any]:
    simplex = z3.Solver()
    simplex_lambdas = _z3_lambdas(simplex)
    _z3_assert_measured_spectrum(simplex, simplex_lambdas)
    simplex_status = simplex.check()

    mixed = z3.Solver()
    mixed_lambdas = _z3_lambdas(mixed)
    _z3_assert_measured_spectrum(mixed, mixed_lambdas)
    for lam in mixed_lambdas:
        mixed.add(lam < z3.RealVal("1"))
    mixed_status = mixed.check()

    pure_with_spectrum = z3.Solver()
    pure_lambdas = _z3_lambdas(pure_with_spectrum)
    _z3_assert_measured_spectrum(pure_with_spectrum, pure_lambdas)
    _z3_assert_pure(pure_with_spectrum, pure_lambdas)
    pure_with_spectrum_status = pure_with_spectrum.check()

    pure_without_spectrum = z3.Solver()
    pure_without_lambdas = _z3_lambdas(pure_without_spectrum)
    _z3_assert_pure(pure_without_spectrum, pure_without_lambdas)
    pure_without_spectrum_status = pure_without_spectrum.check()

    return {
        "solver": "z3",
        "simplex_measured_spectrum": str(simplex_status),
        "mixed_measured_spectrum": str(mixed_status),
        "pure_with_measured_spectrum": str(pure_with_spectrum_status),
        "pure_without_measured_spectrum": str(pure_without_spectrum_status),
        "pass": bool(
            simplex_status == z3.sat
            and mixed_status == z3.sat
            and pure_with_spectrum_status == z3.unsat
            and pure_without_spectrum_status == z3.sat
        ),
    }


def _cvc5_add(solver: cvc5.Solver, terms: list[cvc5.Term]) -> cvc5.Term:
    return terms[0] if len(terms) == 1 else solver.mkTerm(Kind.ADD, *terms)


def _cvc5_lambdas(solver: cvc5.Solver) -> list[cvc5.Term]:
    solver.setLogic("QF_LRA")
    real_sort = solver.getRealSort()
    zero = solver.mkReal("0")
    one = solver.mkReal("1")
    lambdas = [solver.mkConst(real_sort, f"lambda_{i}") for i in range(DIM)]
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, _cvc5_add(solver, lambdas), one))
    for lam in lambdas:
        solver.assertFormula(solver.mkTerm(Kind.GEQ, lam, zero))
        solver.assertFormula(solver.mkTerm(Kind.LEQ, lam, one))
    return lambdas


def _cvc5_assert_measured_spectrum(solver: cvc5.Solver, lambdas: list[cvc5.Term]) -> None:
    for lam, value in zip(lambdas, MEASURED_SPECTRUM, strict=True):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, lam, solver.mkReal(str(value))))


def _cvc5_assert_pure(solver: cvc5.Solver, lambdas: list[cvc5.Term]) -> None:
    zero = solver.mkReal("0")
    one = solver.mkReal("1")
    pure_cases = []
    for i, lam in enumerate(lambdas):
        conjuncts = [solver.mkTerm(Kind.EQUAL, lam, one)]
        conjuncts.extend(
            solver.mkTerm(Kind.EQUAL, other, zero) for j, other in enumerate(lambdas) if j != i
        )
        pure_cases.append(solver.mkTerm(Kind.AND, *conjuncts))
    solver.assertFormula(solver.mkTerm(Kind.OR, *pure_cases))


def cvc5_spectrum_proof() -> dict[str, Any]:
    simplex = cvc5.Solver()
    simplex_lambdas = _cvc5_lambdas(simplex)
    _cvc5_assert_measured_spectrum(simplex, simplex_lambdas)
    simplex_status = simplex.checkSat()

    mixed = cvc5.Solver()
    mixed_lambdas = _cvc5_lambdas(mixed)
    _cvc5_assert_measured_spectrum(mixed, mixed_lambdas)
    for lam in mixed_lambdas:
        mixed.assertFormula(mixed.mkTerm(Kind.LT, lam, mixed.mkReal("1")))
    mixed_status = mixed.checkSat()

    pure_with_spectrum = cvc5.Solver()
    pure_lambdas = _cvc5_lambdas(pure_with_spectrum)
    _cvc5_assert_measured_spectrum(pure_with_spectrum, pure_lambdas)
    _cvc5_assert_pure(pure_with_spectrum, pure_lambdas)
    pure_with_spectrum_status = pure_with_spectrum.checkSat()

    pure_without_spectrum = cvc5.Solver()
    pure_without_lambdas = _cvc5_lambdas(pure_without_spectrum)
    _cvc5_assert_pure(pure_without_spectrum, pure_without_lambdas)
    pure_without_spectrum_status = pure_without_spectrum.checkSat()

    return {
        "solver": "cvc5",
        "simplex_measured_spectrum": str(simplex_status),
        "mixed_measured_spectrum": str(mixed_status),
        "pure_with_measured_spectrum": str(pure_with_spectrum_status),
        "pure_without_measured_spectrum": str(pure_without_spectrum_status),
        "pass": bool(
            simplex_status.isSat()
            and mixed_status.isSat()
            and pure_with_spectrum_status.isUnsat()
            and pure_without_spectrum_status.isSat()
        ),
    }


def proof_agreement(z3_proof: dict[str, Any], cvc5_proof: dict[str, Any]) -> bool:
    verdict_keys = [
        "simplex_measured_spectrum",
        "mixed_measured_spectrum",
        "pure_with_measured_spectrum",
        "pure_without_measured_spectrum",
    ]
    return all(z3_proof[key] == cvc5_proof[key] for key in verdict_keys)


def build_result() -> dict[str, Any]:
    rho_qutip = build_rho_qutip(P)
    rho_jax = build_rho_jax(P)
    vn_entropy = qutip_entropy_nats(rho_qutip)
    eigvals = jax_spectrum(rho_jax)
    diagnostics = density_diagnostics(rho_jax, rho_qutip, eigvals)
    z3_proof = z3_spectrum_proof()
    cvc5_proof = cvc5_spectrum_proof()
    z3_cvc5_agree = proof_agreement(z3_proof, cvc5_proof)
    purity_assertion_unsat = (
        z3_proof["pure_with_measured_spectrum"] == "unsat"
        and cvc5_proof["pure_with_measured_spectrum"] == "unsat"
    )
    erase_flip_sat = (
        z3_proof["pure_without_measured_spectrum"] == "sat"
        and cvc5_proof["pure_without_measured_spectrum"] == "sat"
    )
    entropy_expected_pass = abs(vn_entropy - EXPECTED_ENTROPY) <= ENTROPY_TOL
    all_pass = bool(
        diagnostics["spectrum_matches_expected"]
        and entropy_expected_pass
        and z3_proof["pass"]
        and cvc5_proof["pass"]
        and z3_cvc5_agree
        and purity_assertion_unsat
        and erase_flip_sat
    )

    return {
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(SRC_PATH),
        "result_path": str(RESULT_PATH),
        "rho_spec": RHO_SPEC,
        "vn_entropy": vn_entropy,
        "vn_entropy_units": "nats",
        "expected_vn_entropy_approx": EXPECTED_ENTROPY,
        "entropy_expected_pass": entropy_expected_pass,
        "z3_cvc5_agree": z3_cvc5_agree,
        "purity_assertion_unsat": purity_assertion_unsat,
        "erase_flip": "pure-state assertion UNSAT with measured spectrum {0.7375, 0.0375x7}; dropping measured spectrum -> SAT",
        "erase_flip_drop_measured_spectrum_sat": erase_flip_sat,
        "engine": "jax",
        "package": "qutip+z3+cvc5",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
        "all_pass": all_pass,
        "diagnostics": diagnostics,
        "smt_proof": {
            "claim": "The measured spectrum is a valid mixed density spectrum; adding a pure-state spectrum assertion is UNSAT, and erasing the measured spectrum flips the pure-state assertion back to SAT.",
            "entropy_bound_connection": "Measured spectrum has all 0 < lambda_i < 1 over dim 8, so rho is genuinely mixed and the live von Neumann entropy bound is 0 < S < ln(8).",
            "z3": z3_proof,
            "cvc5": cvc5_proof,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> None:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote={RESULT_PATH}")
    print(f"vn_entropy={result['vn_entropy']:.12f} nats")
    print(f"z3_cvc5_agree={result['z3_cvc5_agree']}")
    print(f"purity_assertion_unsat={result['purity_assertion_unsat']}")
    print(f"erase_flip={result['erase_flip']}")


if __name__ == "__main__":
    main()
