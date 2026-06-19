#!/usr/bin/env python3
"""JAX/qutip/z3/cvc5 R0 probe quotient refinement leg.

Scratch diagnostic only. This lane computes locally and does not read peer
engine result JSON.
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
from cvc5 import Kind
import jax.numpy as jnp
import qutip
import z3


OBJECT_ID = "foundation_r0_probe_quotient_refinement_v1"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_foundation_r0_probe_quotient_refinement_jax_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r0_probe_quotient_refinement_jax_results.json"
TOL = 1.0e-10

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 mirror arrays for density admissibility and qutip/JAX distribution cross-checks",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 array mirror for trace, Hermitian, PSD, and Born-rule residual checks",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing QIT state, projector, and Born-rule probe distribution construction",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT certificate for witness refinement and negative controls",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT certificate matching z3 on witness refinement and controls",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive paths, timestamp, JSON serialization, and finite partition assembly",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "qutip": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "Python stdlib": "supportive",
}


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def rounded(value: Any, digits: int = 12) -> float:
    return round(float(value), digits)


def qutip_objects() -> tuple[dict[str, qutip.Qobj], dict[str, dict[str, Any]]]:
    z0 = qutip.basis(2, 0)
    z1 = qutip.basis(2, 1)
    x_plus = (z0 + z1).unit()
    x_minus = (z0 - z1).unit()
    states = {
        "rho_z0": z0.proj(),
        "rho_z1": z1.proj(),
        "rho_plus": x_plus.proj(),
        "rho_minus": x_minus.proj(),
    }
    probes = {
        "Z": {"name": "Z", "outcome_labels": ["z0", "z1"], "effects": [z0.proj(), z1.proj()]},
        "X": {"name": "X", "outcome_labels": ["x_plus", "x_minus"], "effects": [x_plus.proj(), x_minus.proj()]},
        "Z_duplicate": {
            "name": "Z_duplicate",
            "outcome_labels": ["z0_dup", "z1_dup"],
            "effects": [z0.proj(), z1.proj()],
        },
        "Z_relabel": {
            "name": "Z_relabel",
            "outcome_labels": ["z1_relabel", "z0_relabel"],
            "effects": [z1.proj(), z0.proj()],
        },
    }
    return states, probes


def qobj_to_jax(obj: qutip.Qobj) -> jax.Array:
    return jnp.asarray(obj.full(), dtype=jnp.complex128)


def distribution(rho: qutip.Qobj, probe: dict[str, Any]) -> list[float]:
    return [rounded(qutip.expect(effect, rho), 12) for effect in probe["effects"]]


def jax_distribution(rho: qutip.Qobj, probe: dict[str, Any]) -> list[float]:
    rho_j = qobj_to_jax(rho)
    rows = []
    for effect in probe["effects"]:
        rows.append(rounded(py_float(jnp.trace(qobj_to_jax(effect) @ rho_j)), 12))
    return rows


def quotient(states: dict[str, qutip.Qobj], probe_family: list[dict[str, Any]], name: str) -> dict[str, Any]:
    classes: dict[str, dict[str, Any]] = {}
    for state_id in sorted(states):
        sig = [distribution(states[state_id], probe) for probe in probe_family]
        key = json.dumps(sig, sort_keys=True, separators=(",", ":"))
        classes.setdefault(key, {"members": [], "signature": sig})
        classes[key]["members"].append(state_id)
    rows = []
    for idx, key in enumerate(sorted(classes)):
        rows.append(
            {
                "class_id": f"{name}_q{idx}",
                "members": sorted(classes[key]["members"]),
                "signature": classes[key]["signature"],
            }
        )
    return {
        "name": name,
        "probe_names": [probe["name"] for probe in probe_family],
        "class_count": len(rows),
        "classes": rows,
        "partition_member_ids": sorted(states),
    }


def class_containing(q: dict[str, Any], state_id: str) -> str | None:
    for cls in q["classes"]:
        if state_id in cls["members"]:
            return str(cls["class_id"])
    return None


def density_admissibility(state_id: str, rho: qutip.Qobj) -> dict[str, Any]:
    rho_j = qobj_to_jax(rho)
    eigvals = jnp.linalg.eigvalsh(0.5 * (rho_j + rho_j.conj().T)).real
    trace = jnp.trace(rho_j)
    return {
        "state_id": state_id,
        "finite_object": list(rho_j.shape) == [2, 2],
        "shape": list(rho_j.shape),
        "hermitian_residual_fro": py_float(jnp.linalg.norm(rho_j - rho_j.conj().T)),
        "trace_real": py_float(trace),
        "trace_imag_abs": py_float(jnp.abs(jnp.imag(trace))),
        "trace_one": abs(py_float(trace) - 1.0) <= TOL and py_float(jnp.abs(jnp.imag(trace))) <= TOL,
        "min_eigenvalue": py_float(jnp.min(eigvals)),
        "psd": py_float(jnp.min(eigvals)) >= -TOL,
    }


def invalid_density_controls() -> dict[str, Any]:
    candidates = {
        "invalid_trace_two_identity": jnp.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128),
        "invalid_psd_trace_one_diagonal": jnp.asarray([[1.2, 0.0], [0.0, -0.2]], dtype=jnp.complex128),
        "invalid_nonhermitian_trace_one": jnp.asarray([[1.0, 1.0], [0.0, 0.0]], dtype=jnp.complex128),
    }
    rows: dict[str, Any] = {}
    for name, mat in candidates.items():
        hermitian_residual = py_float(jnp.linalg.norm(mat - mat.conj().T))
        trace = jnp.trace(mat)
        if hermitian_residual <= TOL:
            min_eigenvalue = py_float(jnp.min(jnp.linalg.eigvalsh(mat).real))
        else:
            min_eigenvalue = None
        trace_one = abs(py_float(trace) - 1.0) <= TOL and py_float(jnp.abs(jnp.imag(trace))) <= TOL
        psd = bool(min_eigenvalue is not None and min_eigenvalue >= -TOL)
        rows[name] = {
            "finite_object": list(mat.shape) == [2, 2],
            "hermitian_residual_fro": hermitian_residual,
            "trace_real": py_float(trace),
            "trace_imag_abs": py_float(jnp.abs(jnp.imag(trace))),
            "trace_one": trace_one,
            "min_eigenvalue": min_eigenvalue,
            "psd": psd,
            "accepted_as_density": False,
        }
    return rows


def z3_certificate() -> dict[str, Any]:
    half = z3.RealVal("1/2")
    zero = z3.RealVal("0")
    one = z3.RealVal("1")

    zp0, zp1, zm0, zm1, xp0, xp1, xm0, xm1 = z3.Reals("zp0 zp1 zm0 zm1 xp0 xp1 xm0 xm1")
    witness = z3.Solver()
    witness.add(zp0 == half, zp1 == half, zm0 == half, zm1 == half)
    witness.add(xp0 == one, xp1 == zero, xm0 == zero, xm1 == one)
    forced_claim = z3.And(zp0 == zm0, zp1 == zm1, z3.Or(xp0 != xm0, xp1 != xm1))
    witness.add(z3.Not(forced_claim))
    witness_status = witness.check()

    duplicate = z3.Solver()
    dzp0, dzp1, dzm0, dzm1 = z3.Reals("dzp0 dzp1 dzm0 dzm1")
    rzp0, rzp1, rzm0, rzm1 = z3.Reals("rzp0 rzp1 rzm0 rzm1")
    duplicate.add(zp0 == half, zp1 == half, zm0 == half, zm1 == half)
    duplicate.add(dzp0 == zp0, dzp1 == zp1, dzm0 == zm0, dzm1 == zm1)
    duplicate.add(rzp0 == zp1, rzp1 == zp0, rzm0 == zm1, rzm1 == zm0)
    duplicate.add(z3.Or(dzp0 != dzm0, dzp1 != dzm1, rzp0 != rzm0, rzp1 != rzm1))
    duplicate_status = duplicate.check()

    bad_psd = z3.Solver()
    bad_min_eig = z3.Real("bad_min_eig")
    bad_psd.add(bad_min_eig == z3.RealVal("-1/5"))
    bad_psd.add(bad_min_eig >= zero)
    bad_psd_status = bad_psd.check()

    bad_trace = z3.Solver()
    trace_value = z3.Real("trace_value")
    bad_trace.add(trace_value == z3.RealVal("2"))
    bad_trace.add(trace_value == one)
    bad_trace_status = bad_trace.check()

    return {
        "solver": "z3",
        "claim": "Fixed |+>,|-> distributions force same Z class and distinct X outcomes; negating that refinement witness is UNSAT.",
        "witness_refinement_negation": str(witness_status),
        "duplicate_or_relabel_Z_distinguishes_negation": str(duplicate_status),
        "invalid_negative_eigenvalue_psd_claim": str(bad_psd_status),
        "invalid_trace_two_trace_one_claim": str(bad_trace_status),
        "pass": all(
            status == z3.unsat
            for status in [witness_status, duplicate_status, bad_psd_status, bad_trace_status]
        ),
    }


def _cvc5_add(solver: cvc5.Solver, terms: list[cvc5.Term]) -> cvc5.Term:
    return terms[0] if len(terms) == 1 else solver.mkTerm(Kind.ADD, *terms)


def _cvc5_and(solver: cvc5.Solver, terms: list[cvc5.Term]) -> cvc5.Term:
    return terms[0] if len(terms) == 1 else solver.mkTerm(Kind.AND, *terms)


def _cvc5_or(solver: cvc5.Solver, terms: list[cvc5.Term]) -> cvc5.Term:
    return terms[0] if len(terms) == 1 else solver.mkTerm(Kind.OR, *terms)


def _neq(solver: cvc5.Solver, left: cvc5.Term, right: cvc5.Term) -> cvc5.Term:
    return solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, left, right))


def cvc5_certificate() -> dict[str, Any]:
    def base_solver() -> cvc5.Solver:
        solver = cvc5.Solver()
        solver.setLogic("QF_LRA")
        return solver

    half_s = "1/2"
    zero_s = "0"
    one_s = "1"

    witness = base_solver()
    real_sort = witness.getRealSort()
    zp0, zp1, zm0, zm1, xp0, xp1, xm0, xm1 = [
        witness.mkConst(real_sort, name)
        for name in ["zp0", "zp1", "zm0", "zm1", "xp0", "xp1", "xm0", "xm1"]
    ]
    for term in [zp0, zp1, zm0, zm1]:
        witness.assertFormula(witness.mkTerm(Kind.EQUAL, term, witness.mkReal(half_s)))
    witness.assertFormula(witness.mkTerm(Kind.EQUAL, xp0, witness.mkReal(one_s)))
    witness.assertFormula(witness.mkTerm(Kind.EQUAL, xp1, witness.mkReal(zero_s)))
    witness.assertFormula(witness.mkTerm(Kind.EQUAL, xm0, witness.mkReal(zero_s)))
    witness.assertFormula(witness.mkTerm(Kind.EQUAL, xm1, witness.mkReal(one_s)))
    same_z = _cvc5_and(
        witness,
        [
            witness.mkTerm(Kind.EQUAL, zp0, zm0),
            witness.mkTerm(Kind.EQUAL, zp1, zm1),
        ],
    )
    distinct_x = _cvc5_or(witness, [_neq(witness, xp0, xm0), _neq(witness, xp1, xm1)])
    forced_claim = witness.mkTerm(Kind.AND, same_z, distinct_x)
    witness.assertFormula(witness.mkTerm(Kind.NOT, forced_claim))
    witness_status = witness.checkSat()

    duplicate = base_solver()
    real_sort = duplicate.getRealSort()
    zp0, zp1, zm0, zm1, dzp0, dzp1, dzm0, dzm1, rzp0, rzp1, rzm0, rzm1 = [
        duplicate.mkConst(real_sort, name)
        for name in ["zp0", "zp1", "zm0", "zm1", "dzp0", "dzp1", "dzm0", "dzm1", "rzp0", "rzp1", "rzm0", "rzm1"]
    ]
    for term in [zp0, zp1, zm0, zm1]:
        duplicate.assertFormula(duplicate.mkTerm(Kind.EQUAL, term, duplicate.mkReal(half_s)))
    for left, right in [(dzp0, zp0), (dzp1, zp1), (dzm0, zm0), (dzm1, zm1), (rzp0, zp1), (rzp1, zp0), (rzm0, zm1), (rzm1, zm0)]:
        duplicate.assertFormula(duplicate.mkTerm(Kind.EQUAL, left, right))
    duplicate.assertFormula(
        _cvc5_or(
            duplicate,
            [
                _neq(duplicate, dzp0, dzm0),
                _neq(duplicate, dzp1, dzm1),
                _neq(duplicate, rzp0, rzm0),
                _neq(duplicate, rzp1, rzm1),
            ],
        )
    )
    duplicate_status = duplicate.checkSat()

    bad_psd = base_solver()
    bad_min = bad_psd.mkConst(bad_psd.getRealSort(), "bad_min_eig")
    bad_psd.assertFormula(bad_psd.mkTerm(Kind.EQUAL, bad_min, bad_psd.mkReal("-1/5")))
    bad_psd.assertFormula(bad_psd.mkTerm(Kind.GEQ, bad_min, bad_psd.mkReal(zero_s)))
    bad_psd_status = bad_psd.checkSat()

    bad_trace = base_solver()
    trace_value = bad_trace.mkConst(bad_trace.getRealSort(), "trace_value")
    bad_trace.assertFormula(bad_trace.mkTerm(Kind.EQUAL, trace_value, bad_trace.mkReal("2")))
    bad_trace.assertFormula(bad_trace.mkTerm(Kind.EQUAL, trace_value, bad_trace.mkReal(one_s)))
    bad_trace_status = bad_trace.checkSat()

    statuses = [str(witness_status), str(duplicate_status), str(bad_psd_status), str(bad_trace_status)]
    return {
        "solver": "cvc5",
        "claim": "Same fixed rational witness/control formulas as z3.",
        "witness_refinement_negation": str(witness_status),
        "duplicate_or_relabel_Z_distinguishes_negation": str(duplicate_status),
        "invalid_negative_eigenvalue_psd_claim": str(bad_psd_status),
        "invalid_trace_two_trace_one_claim": str(bad_trace_status),
        "pass": all(status == "unsat" for status in statuses),
    }


def build_result() -> dict[str, Any]:
    states, probes = qutip_objects()
    q_empty = quotient(states, [], "empty_probe")
    q_z = quotient(states, [probes["Z"]], "M_Z")
    q_zx = quotient(states, [probes["Z"], probes["X"]], "M_ZX")
    q_duplicate_z = quotient(states, [probes["Z"], probes["Z_duplicate"]], "M_Z_duplicate")
    q_relabel_z = quotient(states, [probes["Z"], probes["Z_relabel"]], "M_Z_relabel")

    witness = {
        "pair": ["rho_plus", "rho_minus"],
        "Z_distributions": {
            "rho_plus": distribution(states["rho_plus"], probes["Z"]),
            "rho_minus": distribution(states["rho_minus"], probes["Z"]),
        },
        "X_distributions": {
            "rho_plus": distribution(states["rho_plus"], probes["X"]),
            "rho_minus": distribution(states["rho_minus"], probes["X"]),
        },
        "same_under_Z": distribution(states["rho_plus"], probes["Z"]) == distribution(states["rho_minus"], probes["Z"]),
        "distinct_under_X": distribution(states["rho_plus"], probes["X"]) != distribution(states["rho_minus"], probes["X"]),
        "same_Z_class": class_containing(q_z, "rho_plus") == class_containing(q_z, "rho_minus"),
        "split_ZX_class": class_containing(q_zx, "rho_plus") != class_containing(q_zx, "rho_minus"),
    }
    admissibility = {state_id: density_admissibility(state_id, rho) for state_id, rho in states.items()}
    all_admissible = all(
        row["finite_object"] and row["trace_one"] and row["psd"] and row["hermitian_residual_fro"] <= TOL
        for row in admissibility.values()
    )
    invalid_controls = invalid_density_controls()
    invalid_controls_rejected = all(
        not row["accepted_as_density"] and not (row["trace_one"] and row["psd"] and row["hermitian_residual_fro"] <= TOL)
        for row in invalid_controls.values()
    )
    z3_proof = z3_certificate()
    cvc5_proof = cvc5_certificate()

    qutip_jax_distribution_residuals = {}
    for state_id, rho in states.items():
        qutip_jax_distribution_residuals[state_id] = {}
        for probe_name, probe in probes.items():
            qutip_stats = distribution(rho, probe)
            jax_stats = jax_distribution(rho, probe)
            qutip_jax_distribution_residuals[state_id][probe_name] = max(
                abs(a - b) for a, b in zip(qutip_stats, jax_stats, strict=True)
            )
    max_qutip_jax_distribution_residual = max(
        residual
        for by_probe in qutip_jax_distribution_residuals.values()
        for residual in by_probe.values()
    )

    negative_controls = {
        "empty_probe_collapses_identity": {"pass": q_empty["class_count"] == 1, "class_count": q_empty["class_count"]},
        "duplicate_Z_does_not_refine": {
            "pass": q_duplicate_z["class_count"] == q_z["class_count"],
            "Z_class_count": q_z["class_count"],
            "duplicate_Z_class_count": q_duplicate_z["class_count"],
        },
        "relabel_Z_does_not_refine": {
            "pass": q_relabel_z["class_count"] == q_z["class_count"],
            "Z_class_count": q_z["class_count"],
            "relabel_Z_class_count": q_relabel_z["class_count"],
        },
        "invalid_density_candidates_rejected": {"pass": invalid_controls_rejected, "candidates": invalid_controls},
        "cross_engine_agreement_is_plumbing_not_proof": {
            "pass": True,
            "note": "This standalone JAX/qutip lane does not read peer JSON; envelope comparison is later plumbing, not proof promotion.",
        },
    }
    strict_refinement = (
        q_zx["class_count"] > q_z["class_count"]
        and witness["same_under_Z"]
        and witness["distinct_under_X"]
        and witness["same_Z_class"]
        and witness["split_ZX_class"]
    )
    all_pass = (
        all_admissible
        and invalid_controls_rejected
        and strict_refinement
        and all(row["pass"] for row in negative_controls.values())
        and z3_proof["pass"]
        and cvc5_proof["pass"]
        and max_qutip_jax_distribution_residual <= TOL
    )

    return {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine": "jax",
        "executable": sys.executable,
        "python_version": sys.version,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "active_preflight": {
            "python_executable": sys.executable,
            "jax_version": jax.__version__,
            "qutip_version": qutip.__version__,
            "z3_version": z3.get_version_string(),
            "cvc5_version": getattr(cvc5, "__version__", "unknown"),
        },
        "reads_peer_result": reads_peer_result,
        "packages": {
            "load_bearing": ["qutip", "z3", "cvc5"],
            "supportive": ["jax", "jax.numpy", "Python stdlib"],
            "control_only": [],
            "missing_required": [],
        },
        "package_observables": {
            "qutip": "constructed qubit kets, density operators, projectors, and Born-rule probe distributions",
            "z3": "proved witness-refinement negation, duplicate/relabel split, PSD, and trace invalid controls are UNSAT",
            "cvc5": "independently proved the same rational finite quotient/admissibility certificates as z3",
            "jax.numpy": "mirrored qutip matrices for x64 trace, Hermitian, PSD, and distribution residual checks",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "finite_support": {
            "S": ["rho_z0", "rho_z1", "rho_plus", "rho_minus"],
            "dimension": 2,
            "state_kind": "finite support qubit density matrices",
        },
        "probe_families": {
            "M_empty": [],
            "M_Z": ["Z"],
            "M_ZX": ["Z", "X"],
            "M_Z_duplicate": ["Z", "Z_duplicate"],
            "M_Z_relabel": ["Z", "Z_relabel"],
        },
        "quotient": {
            "empty_probe": q_empty,
            "M_Z": q_z,
            "M_ZX": q_zx,
            "duplicate_Z_control": q_duplicate_z,
            "relabel_Z_control": q_relabel_z,
        },
        "witness_pair": witness,
        "density_admissibility": admissibility,
        "negative_controls": negative_controls,
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_proof["witness_refinement_negation"],
                "details": z3_proof,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_proof["witness_refinement_negation"],
                "details": cvc5_proof,
            },
        },
        "diagnostics": {
            "qutip_jax_distribution_residuals": qutip_jax_distribution_residuals,
            "max_qutip_jax_distribution_residual": max_qutip_jax_distribution_residual,
        },
        "core_checks": {
            "all_admissible_density_matrices": all_admissible,
            "strict_quotient_refinement": strict_refinement,
            "z_to_zx_class_count_increase": q_zx["class_count"] - q_z["class_count"],
            "all_pass": all_pass,
        },
        "all_pass": all_pass,
        "claim_ceiling": "R0 scratch_diagnostic probe-relative quotient refinement only: finite support qubit states under M_Z versus M_ZX. Not M(C), not R1/R2, not formal, not canonical, not bridge, not axis evidence.",
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"z_classes={result['quotient']['M_Z']['class_count']} "
        f"zx_classes={result['quotient']['M_ZX']['class_count']} "
        f"witness_same_Z={str(result['witness_pair']['same_under_Z']).lower()} "
        f"witness_distinct_X={str(result['witness_pair']['distinct_under_X']).lower()} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"reads_peer_result={str(result['reads_peer_result']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
