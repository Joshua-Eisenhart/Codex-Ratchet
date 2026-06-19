#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
from torch.func import jacrev, vmap
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_foundation_r1_f01_finite_admissibility_unsat_pytorch_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r1_f01_finite_admissibility_unsat_pytorch_results.json"
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
    "torch": {"tried": True, "used": True, "reason": "supportive finite support tensors and occupancy masks"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing support-excess observable over candidate sizes via vmap/jacrev"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite injection SAT/UNSAT proof for F01 support predicate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite injection SAT/UNSAT proof for the same predicate"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact integer pigeonhole inequality crossover"},
    "Python stdlib": {"tried": True, "used": True, "reason": "supportive JSON/timestamp/path logic"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing", "sympy": "load_bearing", "Python stdlib": "supportive"}


def z3_injection_status(k: int, n: int, *, finite_bound: bool, label: str) -> dict[str, Any]:
    solver = z3.Solver()
    variables = [z3.Int(f"{label}_x{i}") for i in range(k)]
    if finite_bound:
        solver.add([z3.And(x >= 0, x < n) for x in variables])
    solver.add(z3.Distinct(*variables))
    status = solver.check()
    return {"solver": "z3", "status": str(status), "k": k, "n": n, "finite_bound": finite_bound}


def cvc5_injection_status(k: int, n: int, *, finite_bound: bool, label: str) -> dict[str, Any]:
    solver = cvc5.Solver()
    int_sort = solver.getIntegerSort()
    variables = [solver.mkConst(int_sort, f"{label}_x{i}") for i in range(k)]
    if finite_bound:
        zero = solver.mkInteger(0)
        bound = solver.mkInteger(n)
        for x in variables:
            solver.assertFormula(solver.mkTerm(Kind.GEQ, x, zero))
            solver.assertFormula(solver.mkTerm(Kind.LT, x, bound))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, *variables))
    return {"solver": "cvc5", "status": str(solver.checkSat()), "k": k, "n": n, "finite_bound": finite_bound}


def add_expectation(record: dict[str, Any], expected: str) -> dict[str, Any]:
    out = dict(record)
    out["expected"] = expected
    out["pass"] = out["status"] == expected
    return out


def support_excess(candidate_k: torch.Tensor, bound_n: torch.Tensor) -> torch.Tensor:
    return torch.relu(candidate_k - bound_n)


def torch_support_observables() -> dict[str, Any]:
    support_atoms = torch.arange(N, dtype=torch.int64)
    positive_mask = support_atoms < POSITIVE_K
    candidate_sizes = torch.tensor([float(POSITIVE_K), float(NEGATIVE_K)], dtype=torch.float64)
    bound = torch.tensor(float(N), dtype=torch.float64)
    excesses = vmap(lambda k: support_excess(k, bound))(candidate_sizes)
    jacobian = vmap(jacrev(lambda k: support_excess(k, bound)))(candidate_sizes)
    return {
        "support_vector": [int(v) for v in support_atoms.tolist()],
        "positive_mask": [bool(v) for v in positive_mask.tolist()],
        "positive_mask_count": int(positive_mask.to(torch.int64).sum().item()),
        "candidate_sizes": [float(v) for v in candidate_sizes.tolist()],
        "support_excess_values": [float(v) for v in excesses.tolist()],
        "support_excess_jacrev_values": [float(v) for v in jacobian.tolist()],
        "negative_excess_atoms": int(max(NEGATIVE_K - N, 0)),
    }


def sympy_crossover() -> dict[str, Any]:
    n = sp.Integer(N)
    positive_k = sp.Integer(POSITIVE_K)
    negative_k = sp.Integer(NEGATIVE_K)
    raised_n = sp.Integer(RAISED_N)
    return {
        "positive_K4_le_N4": {"status": bool(positive_k <= n), "expected": True, "pass": bool(positive_k <= n)},
        "negative_K5_gt_N4": {"status": bool(negative_k > n), "expected": True, "pass": bool(negative_k > n)},
        "raised_bound_K5_le_N5": {"status": bool(negative_k <= raised_n), "expected": True, "pass": bool(negative_k <= raised_n)},
        "pigeonhole_formula": "injective finite map K -> N is impossible when K > N",
    }


def build_result() -> dict[str, Any]:
    z3_results = {
        "positive_K4_into_N4": add_expectation(z3_injection_status(POSITIVE_K, N, finite_bound=True, label="torch_z3_positive"), "sat"),
        "negative_K5_into_N4": add_expectation(z3_injection_status(NEGATIVE_K, N, finite_bound=True, label="torch_z3_negative"), "unsat"),
        "no_finitude_K5_distinct_unbounded": add_expectation(z3_injection_status(NEGATIVE_K, N, finite_bound=False, label="torch_z3_nofinitude"), "sat"),
        "raised_bound_K5_into_N5": add_expectation(z3_injection_status(NEGATIVE_K, RAISED_N, finite_bound=True, label="torch_z3_raised"), "sat"),
    }
    cvc5_results = {
        "positive_K4_into_N4": add_expectation(cvc5_injection_status(POSITIVE_K, N, finite_bound=True, label="torch_cvc5_positive"), "sat"),
        "negative_K5_into_N4": add_expectation(cvc5_injection_status(NEGATIVE_K, N, finite_bound=True, label="torch_cvc5_negative"), "unsat"),
        "no_finitude_K5_distinct_unbounded": add_expectation(cvc5_injection_status(NEGATIVE_K, N, finite_bound=False, label="torch_cvc5_nofinitude"), "sat"),
        "raised_bound_K5_into_N5": add_expectation(cvc5_injection_status(NEGATIVE_K, RAISED_N, finite_bound=True, label="torch_cvc5_raised"), "sat"),
    }
    sympy_results = sympy_crossover()
    solver_agreement = {key: z3_results[key]["status"] == cvc5_results[key]["status"] for key in z3_results}
    torch_observables = torch_support_observables()
    negative_controls = {
        "K5_cannot_inject_into_N4": {"pass": z3_results["negative_K5_into_N4"]["status"] == cvc5_results["negative_K5_into_N4"]["status"] == "unsat" and sympy_results["negative_K5_gt_N4"]["pass"]},
        "removing_finite_support_bound_makes_K5_sat": {"pass": z3_results["no_finitude_K5_distinct_unbounded"]["status"] == cvc5_results["no_finitude_K5_distinct_unbounded"]["status"] == "sat"},
        "raising_bound_to_N5_makes_K5_sat": {"pass": z3_results["raised_bound_K5_into_N5"]["status"] == cvc5_results["raised_bound_K5_into_N5"]["status"] == "sat" and sympy_results["raised_bound_K5_le_N5"]["pass"]},
        "torch_support_excess_detects_negative_candidate": {"pass": torch_observables["support_excess_values"] == [0.0, 1.0]},
    }
    all_pass = bool(
        all(item["pass"] for item in z3_results.values())
        and all(item["pass"] for item in cvc5_results.values())
        and all(solver_agreement.values())
        and all(item["pass"] for key, item in sympy_results.items() if isinstance(item, dict))
        and all(item["pass"] for item in negative_controls.values())
        and READS_PEER_RESULT is False
    )
    return {
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "backend": "pytorch_torchfunc_z3_cvc5_sympy_finite_injection",
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
        "solver_results": {"z3": z3_results, "cvc5": cvc5_results, "sympy": sympy_results, "z3_cvc5_agreement": solver_agreement},
        "negative_controls": negative_controls,
        "support_observables": torch_observables,
        "packages": {
            "load_bearing": ["torch.func", "z3", "cvc5", "sympy"],
            "supportive": ["torch", "json", "pathlib"],
            "control_only": [],
            "missing_required": [],
        },
        "package_observables": {
            "torch.func": "vmap/jacrev support-excess observable distinguishes K=4 from K=5 over N=4",
            "z3": "encoded finite injective map into S and produced SAT/UNSAT controls",
            "cvc5": "independently encoded the same finite injective map controls",
            "sympy": "exact integer K<=N and K>N pigeonhole crossover facts",
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
    print(f"SCOUT_DONE all_pass={str(result['all_pass']).lower()} positive={result['solver_results']['z3']['positive_K4_into_N4']['status']} negative_z3={result['solver_results']['z3']['negative_K5_into_N4']['status']} negative_cvc5={result['solver_results']['cvc5']['negative_K5_into_N4']['status']} torch_excess={result['support_observables']['support_excess_values']} reads_peer_result={result['reads_peer_result']}")
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
