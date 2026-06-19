#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import cvc5
from cvc5 import Kind
import jax
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_foundation_r1_f01_finite_admissibility_unsat_jax_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r1_f01_finite_admissibility_unsat_jax_results.json"
OBJECT_ID = "foundation_r1_f01_finite_admissibility_unsat_v1"
classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result
N = 4
SUPPORT = tuple(range(N))
POSITIVE_K = 4
NEGATIVE_K = 5
RAISED_N = 5

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive local finite support tensor construction and size observables"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive support-mask mirror; not the only claim path"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite injection SAT/UNSAT proof for F01 support predicate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite injection SAT/UNSAT proof for the same predicate"},
    "Python stdlib": {"tried": True, "used": True, "reason": "supportive JSON/timestamp/path logic"},
}
TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing", "Python stdlib": "supportive"}


def z3_injection_status(k: int, n: int, *, finite_bound: bool, label: str) -> dict[str, Any]:
    solver = z3.Solver()
    variables = [z3.Int(f"{label}_x{i}") for i in range(k)]
    if finite_bound:
        solver.add([z3.And(x >= 0, x < n) for x in variables])
    solver.add(z3.Distinct(*variables))
    status = solver.check()
    record: dict[str, Any] = {"solver": "z3", "status": str(status), "k": k, "n": n, "finite_bound": finite_bound}
    if status == z3.sat:
        model = solver.model()
        record["model_values"] = [int(str(model.evaluate(x, model_completion=True))) for x in variables]
    return record


def cvc5_injection_status(k: int, n: int, *, finite_bound: bool, label: str) -> dict[str, Any]:
    solver = cvc5.Solver()
    int_sort = solver.getIntegerSort()
    variables = [solver.mkConst(int_sort, f"{label}_x{i}") for i in range(k)]
    zero = solver.mkInteger(0)
    bound = solver.mkInteger(n)
    if finite_bound:
        for x in variables:
            solver.assertFormula(solver.mkTerm(Kind.GEQ, x, zero))
            solver.assertFormula(solver.mkTerm(Kind.LT, x, bound))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, *variables))
    status = str(solver.checkSat())
    return {"solver": "cvc5", "status": status, "k": k, "n": n, "finite_bound": finite_bound}


def add_expectation(record: dict[str, Any], expected: str) -> dict[str, Any]:
    out = dict(record)
    out["expected"] = expected
    out["pass"] = out["status"] == expected
    return out


def local_support_observables() -> dict[str, Any]:
    atoms = jnp.arange(N, dtype=jnp.int64)
    positive_mask = atoms < POSITIVE_K
    negative_requested = jnp.arange(NEGATIVE_K, dtype=jnp.int64)
    return {
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "support_vector": [int(x) for x in jax.device_get(atoms).tolist()],
        "positive_mask": [bool(x) for x in jax.device_get(positive_mask).tolist()],
        "positive_mask_count": int(jax.device_get(jnp.sum(positive_mask))),
        "negative_candidate_requested_atoms": [int(x) for x in jax.device_get(negative_requested).tolist()],
        "negative_excess_atoms": int(max(NEGATIVE_K - N, 0)),
    }


def build_result() -> dict[str, Any]:
    z3_results = {
        "positive_K4_into_N4": add_expectation(z3_injection_status(POSITIVE_K, N, finite_bound=True, label="z3_positive"), "sat"),
        "negative_K5_into_N4": add_expectation(z3_injection_status(NEGATIVE_K, N, finite_bound=True, label="z3_negative"), "unsat"),
        "no_finitude_K5_distinct_unbounded": add_expectation(z3_injection_status(NEGATIVE_K, N, finite_bound=False, label="z3_nofinitude"), "sat"),
        "raised_bound_K5_into_N5": add_expectation(z3_injection_status(NEGATIVE_K, RAISED_N, finite_bound=True, label="z3_raised"), "sat"),
    }
    cvc5_results = {
        "positive_K4_into_N4": add_expectation(cvc5_injection_status(POSITIVE_K, N, finite_bound=True, label="cvc5_positive"), "sat"),
        "negative_K5_into_N4": add_expectation(cvc5_injection_status(NEGATIVE_K, N, finite_bound=True, label="cvc5_negative"), "unsat"),
        "no_finitude_K5_distinct_unbounded": add_expectation(cvc5_injection_status(NEGATIVE_K, N, finite_bound=False, label="cvc5_nofinitude"), "sat"),
        "raised_bound_K5_into_N5": add_expectation(cvc5_injection_status(NEGATIVE_K, RAISED_N, finite_bound=True, label="cvc5_raised"), "sat"),
    }
    solver_agreement = {
        key: z3_results[key]["status"] == cvc5_results[key]["status"]
        for key in z3_results
    }
    negative_controls = {
        "K5_cannot_inject_into_N4": {"pass": z3_results["negative_K5_into_N4"]["status"] == cvc5_results["negative_K5_into_N4"]["status"] == "unsat"},
        "removing_finite_support_bound_makes_K5_sat": {"pass": z3_results["no_finitude_K5_distinct_unbounded"]["status"] == cvc5_results["no_finitude_K5_distinct_unbounded"]["status"] == "sat"},
        "raising_bound_to_N5_makes_K5_sat": {"pass": z3_results["raised_bound_K5_into_N5"]["status"] == cvc5_results["raised_bound_K5_into_N5"]["status"] == "sat"},
    }
    all_pass = bool(
        all(item["pass"] for item in z3_results.values())
        and all(item["pass"] for item in cvc5_results.values())
        and all(solver_agreement.values())
        and all(item["pass"] for item in negative_controls.values())
        and READS_PEER_RESULT is False
    )
    return {
        "object_id": OBJECT_ID,
        "engine": "jax",
        "backend": "jax_z3_cvc5_finite_injection",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "executable": sys.executable,
        "finite_support": {"S": list(SUPPORT), "N": N, "predicate": "admit(candidate) iff occupied support atoms inject into finite S"},
        "candidates": {"positive": {"K": POSITIVE_K, "expected": "sat_admitted"}, "negative": {"K": NEGATIVE_K, "expected": "unsat_excluded"}},
        "solver_results": {"z3": z3_results, "cvc5": cvc5_results, "z3_cvc5_agreement": solver_agreement},
        "negative_controls": negative_controls,
        "support_observables": local_support_observables(),
        "packages": {
            "load_bearing": ["z3", "cvc5"],
            "supportive": ["jax", "jax.numpy", "json", "pathlib"],
            "control_only": [],
            "missing_required": [],
        },
        "package_observables": {
            "z3": "encoded finite injective map into S and produced SAT/UNSAT controls",
            "cvc5": "independently encoded the same finite injective map controls",
            "jax.numpy": "mirrored finite support masks and candidate-size observables only",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "claim_ceiling": "R1 F01 scratch finite-object certificate only: tests one encoded finite support/admissibility predicate. Not full M(C), R2, formal, canonical, bridge, axis, physics, gravity, or entropy-master evidence.",
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    z3_negative = result["solver_results"]["z3"]["negative_K5_into_N4"]["status"]
    cvc5_negative = result["solver_results"]["cvc5"]["negative_K5_into_N4"]["status"]
    print(f"SCOUT_DONE all_pass={str(result['all_pass']).lower()} positive={result['solver_results']['z3']['positive_K4_into_N4']['status']} negative_z3={z3_negative} negative_cvc5={cvc5_negative} no_finitude={result['solver_results']['z3']['no_finitude_K5_distinct_unbounded']['status']} raised_bound={result['solver_results']['z3']['raised_bound_K5_into_N5']['status']} reads_peer_result={result['reads_peer_result']}")
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
