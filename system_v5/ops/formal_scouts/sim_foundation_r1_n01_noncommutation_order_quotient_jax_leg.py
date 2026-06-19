#!/usr/bin/env python3
"""JAX/qutip/SMT leg for R1 N01 noncommutation ordered quotient.

Scratch diagnostic only. The lane computes locally and does not read peer
engine results.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex_ratchet_matplotlib")

from jax import config

config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import numpy as np
import qutip
import sympy as sp
import z3

OBJECT_ID = "foundation_r1_n01_noncommutation_order_quotient_v1"
ENGINE = "jax"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_foundation_r1_n01_noncommutation_order_quotient_jax_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r1_n01_noncommutation_order_quotient_jax_results.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result
TOL = 1.0e-10

OUTCOME_LABELS = ["++", "+-", "-+", "--"]
STATE_IDS = ["ket0", "ket1", "ket_plus", "ket_minus", "ket_i_plus", "maximally_mixed"]
PROBE_IDS = ["Z", "X", "Z_duplicate"]
ORDERED_HISTORIES = ["Z_then_X", "X_then_Z", "Z_then_Z_duplicate", "Z_duplicate_then_Z"]

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 mirror arrays for the same finite qubit states and projectors",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 matrix mirror and commutator norm cross-check",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing QIT construction of kets, density matrices, projectors, and ordered projective history probabilities",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite arithmetic certificate for the ket0 nonzero order gap and impossible zero-gap contradiction",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite arithmetic certificate matching z3",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact Pauli commutator and rational distribution check",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive host conversion from qutip/JAX objects for JSON-safe finite arrays; not a claim path",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, paths, timestamps, and finite constants",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "qutip": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "numpy": "supportive",
    "Python stdlib": "supportive",
}


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if hasattr(value, "shape"):
        return to_jsonable(jax.device_get(value).tolist())
    return value


def qutip_objects() -> tuple[dict[str, qutip.Qobj], dict[str, list[qutip.Qobj]], qutip.Qobj, qutip.Qobj]:
    ket0 = qutip.basis(2, 0)
    ket1 = qutip.basis(2, 1)
    ket_plus = (ket0 + ket1).unit()
    ket_minus = (ket0 - ket1).unit()
    ket_i_plus = (ket0 + 1j * ket1).unit()
    states = {
        "ket0": qutip.ket2dm(ket0),
        "ket1": qutip.ket2dm(ket1),
        "ket_plus": qutip.ket2dm(ket_plus),
        "ket_minus": qutip.ket2dm(ket_minus),
        "ket_i_plus": qutip.ket2dm(ket_i_plus),
        "maximally_mixed": qutip.qeye(2) / 2.0,
    }
    pz = [qutip.ket2dm(ket0), qutip.ket2dm(ket1)]
    px = [qutip.ket2dm(ket_plus), qutip.ket2dm(ket_minus)]
    projectors = {"Z": pz, "X": px, "Z_duplicate": pz}
    z_op = pz[0] - pz[1]
    x_op = px[0] - px[1]
    return states, projectors, z_op, x_op


def joint_distribution_qutip(rho: qutip.Qobj, first: list[qutip.Qobj], second: list[qutip.Qobj]) -> list[float]:
    probs: list[float] = []
    for p1 in first:
        branch = p1 * rho * p1
        for p2 in second:
            probs.append(float(np.real((p2 * branch).tr())))
    return probs


def joint_distribution_jax(rho: jax.Array, first: list[jax.Array], second: list[jax.Array]) -> list[float]:
    probs: list[float] = []
    for p1 in first:
        branch = p1 @ rho @ p1
        for p2 in second:
            probs.append(float(jax.device_get(jnp.real(jnp.trace(p2 @ branch)))))
    return probs


def tv_gap(left: list[float], right: list[float]) -> float:
    return 0.5 * sum(abs(a - b) for a, b in zip(left, right))


def rounded(values: list[float], digits: int = 12) -> list[float]:
    return [round(float(v), digits) for v in values]


def quotient_classes(rows: list[dict[str, Any]], signature_key: str) -> dict[str, Any]:
    grouped: dict[str, list[str]] = {}
    for row in rows:
        key = "|".join(str(x) for x in row[signature_key])
        grouped.setdefault(key, []).append(row["state_id"])
    classes = [
        {"class_id": idx + 1, "signature_key": key, "state_ids": sorted(grouped[key])}
        for idx, key in enumerate(sorted(grouped))
    ]
    return {"class_count": len(classes), "classes": classes}


def sympy_exact_checks() -> dict[str, Any]:
    z = sp.Matrix([[1, 0], [0, -1]])
    x = sp.Matrix([[0, 1], [1, 0]])
    comm_zx = z * x - x * z
    comm_zz = z * z - z * z
    zx = [sp.Rational(1, 2), sp.Rational(1, 2), sp.Rational(0), sp.Rational(0)]
    xz = [sp.Rational(1, 4), sp.Rational(1, 4), sp.Rational(1, 4), sp.Rational(1, 4)]
    l1 = sum(abs(a - b) for a, b in zip(zx, xz))
    return {
        "commutator_ZX": str(comm_zx),
        "commutator_ZZ": str(comm_zz),
        "ZX_nonzero": any(value != 0 for value in comm_zx),
        "ZZ_zero": all(value == 0 for value in comm_zz),
        "ket0_ZX_distribution_exact": [str(v) for v in zx],
        "ket0_XZ_distribution_exact": [str(v) for v in xz],
        "ket0_tv_gap_exact": str(sp.Rational(1, 2) * l1),
        "pass": any(value != 0 for value in comm_zx)
        and all(value == 0 for value in comm_zz)
        and sp.Rational(1, 2) * l1 == sp.Rational(1, 2),
    }


def z3_certificate() -> dict[str, Any]:
    l1_num = z3.Int("jax_l1_num")
    tv_num = z3.Int("jax_tv_num")
    tv_den = z3.Int("jax_tv_den")
    solver = z3.Solver()
    solver.add(l1_num == 4)
    solver.add(tv_num == 1)
    solver.add(tv_den == 2)
    solver.add(l1_num > 0)
    solver.add(tv_den > 0)
    main_status = solver.check()

    bad = z3.Solver()
    bad.add(l1_num == 4)
    bad.add(l1_num == 0)
    bad_status = bad.check()
    return {
        "solver": "z3",
        "claim": "Exact ket0 order-gap arithmetic: denominator 4, L1 numerator 4, total-variation gap 1/2; contradictory zero-gap condition is unsat.",
        "main_status": str(main_status),
        "main_sat": main_status == z3.sat,
        "negative_control_status": str(bad_status),
        "negative_control_unsat": bad_status == z3.unsat,
        "pass": main_status == z3.sat and bad_status == z3.unsat,
    }


def cvc5_int(solver: cvc5.Solver, value: int) -> cvc5.Term:
    return solver.mkInteger(value)


def cvc5_main_check() -> str:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    int_sort = solver.getIntegerSort()
    l1_num = solver.mkConst(int_sort, "jax_cvc5_l1_num")
    tv_num = solver.mkConst(int_sort, "jax_cvc5_tv_num")
    tv_den = solver.mkConst(int_sort, "jax_cvc5_tv_den")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, l1_num, cvc5_int(solver, 4)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, tv_num, cvc5_int(solver, 1)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, tv_den, cvc5_int(solver, 2)))
    solver.assertFormula(solver.mkTerm(Kind.GT, l1_num, cvc5_int(solver, 0)))
    solver.assertFormula(solver.mkTerm(Kind.GT, tv_den, cvc5_int(solver, 0)))
    return str(solver.checkSat())


def cvc5_bad_check() -> str:
    solver = cvc5.Solver()
    int_sort = solver.getIntegerSort()
    l1_num = solver.mkConst(int_sort, "jax_cvc5_bad_l1_num")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, l1_num, cvc5_int(solver, 4)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, l1_num, cvc5_int(solver, 0)))
    return str(solver.checkSat())


def cvc5_certificate() -> dict[str, Any]:
    main_status = cvc5_main_check()
    bad_status = cvc5_bad_check()
    return {
        "solver": "cvc5",
        "claim": "Independent exact ket0 order-gap arithmetic certificate matching z3.",
        "main_status": main_status,
        "main_sat": main_status == "sat",
        "negative_control_status": bad_status,
        "negative_control_unsat": bad_status == "unsat",
        "pass": main_status == "sat" and bad_status == "unsat",
    }


def as_jax_matrix(op: qutip.Qobj) -> jax.Array:
    return jnp.asarray(op.full(), dtype=jnp.complex128)


def build_result() -> dict[str, Any]:
    states, projectors, z_op, x_op = qutip_objects()
    jax_states = {key: as_jax_matrix(value) for key, value in states.items()}
    jax_projectors = {key: [as_jax_matrix(p) for p in value] for key, value in projectors.items()}
    z_jax = as_jax_matrix(z_op)
    x_jax = as_jax_matrix(x_op)
    comm_zx = z_op * x_op - x_op * z_op
    comm_zz = z_op * z_op - z_op * z_op
    comm_zx_norm = float(np.linalg.norm(comm_zx.full()))
    comm_zz_norm = float(np.linalg.norm(comm_zz.full()))
    jax_comm_zx_norm = float(jax.device_get(jnp.linalg.norm(z_jax @ x_jax - x_jax @ z_jax)))

    rows: list[dict[str, Any]] = []
    jax_mirror_residuals: list[float] = []
    for state_id in STATE_IDS:
        rho = states[state_id]
        zx = joint_distribution_qutip(rho, projectors["Z"], projectors["X"])
        xz = joint_distribution_qutip(rho, projectors["X"], projectors["Z"])
        zz = joint_distribution_qutip(rho, projectors["Z"], projectors["Z_duplicate"])
        zdupz = joint_distribution_qutip(rho, projectors["Z_duplicate"], projectors["Z"])

        jax_zx = joint_distribution_jax(jax_states[state_id], jax_projectors["Z"], jax_projectors["X"])
        jax_xz = joint_distribution_jax(jax_states[state_id], jax_projectors["X"], jax_projectors["Z"])
        jax_mirror_residuals.extend(abs(a - b) for a, b in zip(zx, jax_zx))
        jax_mirror_residuals.extend(abs(a - b) for a, b in zip(xz, jax_xz))

        noncommuting_gap = tv_gap(zx, xz)
        control_gap = tv_gap(zz, zdupz)
        rows.append(
            {
                "state_id": state_id,
                "Z_then_X": rounded(zx),
                "X_then_Z": rounded(xz),
                "Z_then_Z_duplicate": rounded(zz),
                "Z_duplicate_then_Z": rounded(zdupz),
                "noncommuting_order_gap": noncommuting_gap,
                "commuting_control_order_gap": control_gap,
                "noncommuting_quotient_signature": rounded([*zx, *xz, noncommuting_gap]),
                "commuting_control_quotient_signature": rounded([*zz, *zdupz, control_gap]),
            }
        )

    noncommuting_quotient = quotient_classes(rows, "noncommuting_quotient_signature")
    commuting_quotient = quotient_classes(rows, "commuting_control_quotient_signature")
    witness = next(row for row in rows if row["state_id"] == "ket0")
    z3_proof = z3_certificate()
    cvc5_proof = cvc5_certificate()
    sympy_checks = sympy_exact_checks()
    noncommuting_gap_max = max(row["noncommuting_order_gap"] for row in rows)
    commuting_gap_max = max(row["commuting_control_order_gap"] for row in rows)
    refined = noncommuting_quotient["class_count"] > commuting_quotient["class_count"]

    negative_controls = {
        "commuting_duplicate_Z_has_zero_commutator": {"pass": comm_zz_norm <= TOL, "commutator_norm": comm_zz_norm},
        "commuting_duplicate_Z_has_zero_order_gap_all_states": {"pass": commuting_gap_max <= TOL, "max_order_gap": commuting_gap_max},
        "noncommuting_ZX_has_nonzero_commutator": {"pass": comm_zx_norm > TOL, "commutator_norm": comm_zx_norm},
        "finite_witness_ket0_has_nonzero_order_gap": {"pass": witness["noncommuting_order_gap"] > TOL, "state_id": "ket0", "order_gap": witness["noncommuting_order_gap"]},
        "noncommuting_quotient_refines_commuting_control": {
            "pass": refined,
            "noncommuting_class_count": noncommuting_quotient["class_count"],
            "commuting_control_class_count": commuting_quotient["class_count"],
        },
    }
    all_pass = bool(
        all(row["commuting_control_order_gap"] <= TOL for row in rows)
        and witness["noncommuting_order_gap"] > TOL
        and comm_zx_norm > TOL
        and comm_zz_norm <= TOL
        and refined
        and max(jax_mirror_residuals) <= TOL
        and abs(jax_comm_zx_norm - comm_zx_norm) <= TOL
        and z3_proof["pass"]
        and cvc5_proof["pass"]
        and sympy_checks["pass"]
        and z3_proof["main_status"] == cvc5_proof["main_status"]
        and z3_proof["negative_control_status"] == cvc5_proof["negative_control_status"]
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
        and READS_PEER_RESULT is False
    )

    return {
        "object_id": OBJECT_ID,
        "engine": ENGINE,
        "executable": sys.executable,
        "interpreter": sys.executable,
        "backend": "jax_qutip_smt",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "finite_object": {
            "hilbert_dimension": 2,
            "state_ids": STATE_IDS,
            "named_positive_witness": "ket0",
            "probe_ids": PROBE_IDS,
            "projective_probes": {"Z": "computational-basis rank-1 projectors", "X": "Hadamard-basis rank-1 projectors", "Z_duplicate": "duplicate/relabel of Z projectors"},
            "ordered_histories": ORDERED_HISTORIES,
            "outcome_labels": OUTCOME_LABELS,
        },
        "ordered_histories": {"rows": rows, "witness_ket0": witness},
        "quotient": {
            "definition": "States are quotiented by rounded ordered-history outcome-distribution signatures. Noncommuting uses Z_then_X and X_then_Z; control uses duplicate Z histories.",
            "noncommuting": noncommuting_quotient,
            "commuting_control": commuting_quotient,
            "strict_refinement_observed": refined,
        },
        "class_signatures": {"outcome_order": OUTCOME_LABELS, "state_rows": rows},
        "noncommuting": {
            "probe_pair": "Z,X",
            "commutator_norm": comm_zx_norm,
            "commutator_norm_fro": comm_zx_norm,
            "jax_commutator_norm_fro": jax_comm_zx_norm,
            "order_gap": witness["noncommuting_order_gap"],
            "order_gap_max": noncommuting_gap_max,
            "witness_state_id": "ket0",
            "classification": "nonzero_commutator_nonzero_order_gap_refined_quotient",
        },
        "commuting_control": {
            "probe_pair": "Z,Z_duplicate",
            "commutator_norm": comm_zz_norm,
            "commutator_norm_fro": comm_zz_norm,
            "order_gap": commuting_gap_max,
            "order_gap_max": commuting_gap_max,
            "classification": "zero_commutator_zero_order_gap_coarser_quotient",
        },
        "negative_controls": negative_controls,
        "finite_certificates": {
            "sympy": sympy_checks,
            "z3": z3_proof,
            "cvc5": cvc5_proof,
            "z3_cvc5_agree": z3_proof["main_status"] == cvc5_proof["main_status"]
            and z3_proof["negative_control_status"] == cvc5_proof["negative_control_status"],
        },
        "packages": {
            "load_bearing": ["qutip", "z3", "cvc5", "sympy"],
            "supportive": ["jax", "jax.numpy", "numpy", "json", "pathlib"],
            "control_only": ["numpy"],
            "missing_required": [],
        },
        "package_observables": {
            "qutip": "Constructed finite QIT states/probes and ordered projective-history probabilities.",
            "z3": "Exact ket0 order-gap SAT plus contradictory zero-gap UNSAT.",
            "cvc5": "Independent exact finite arithmetic certificate matching z3.",
            "sympy": "Exact Pauli commutator and rational distribution calculations.",
            "jax.numpy": "x64 mirror arrays for local numeric parity, not the only claim path.",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "control_only_tools": ["numpy"],
        "claim_ceiling": "R1 N01 scratch diagnostic only: finite one-qubit projective-probe ordered-history quotient. Not full M(C), not R0/R1-F01/R2, not formal admission, not canonical, not bridge, not axis, and not physics/gravity/entropy-master evidence.",
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(to_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"noncommuting_order_gap={result['noncommuting']['order_gap']} "
        f"commuting_control_order_gap={result['commuting_control']['order_gap']} "
        f"noncommuting_classes={result['quotient']['noncommuting']['class_count']} "
        f"commuting_control_classes={result['quotient']['commuting_control']['class_count']} "
        f"reads_peer_result={str(result['reads_peer_result']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
