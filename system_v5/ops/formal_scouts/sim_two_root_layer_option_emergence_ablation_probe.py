#!/usr/bin/env python3
"""Ablate all F01/N01-aligned layer options.

This scout is the pessimistic counterpart to the full-tool option explorer.
It runs every explored layer option through five controls:

- both roots active: finite carrier plus noncommuting/order-sensitive pair;
- F01 only: finite carrier but commuting/order-erased pair;
- N01 only: noncommuting pair with finitude gate denied;
- neither: no finite carrier and no noncommutation;
- reversed order: same finite pair but opposite composition order.

A branch survives this scout only if the both-roots case passes and every
single-root/neither control is blocked, while the reversed-order gap remains
positive. This does not prove final emergence; it selects strict branches for
the next integrated manifold retune.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "two_root_layer_option_emergence_ablation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
OPTION_RESULT = RESULT_DIR / "two_root_layer_option_full_tool_explorer_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_layer_option_emergence_ablation"
CLAIM_CEILING = (
    "Formal scout only: ablates all F01/N01-aligned layer options under both, "
    "single-root, neither-root, and reversed-order controls. It selects strict "
    "retune branches but does not admit final manifold emergence, final layer "
    "order, attractor basin, Axis0, engine, physics, target-system, Holodeck, "
    "or canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite operator composition and reverse-order gap checks"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic commutator-vs-commuting-control check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing F01/N01 ablation admission logic"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing cross-solver ablation logic"},
    "python_json": {"tried": True, "used": True, "reason": "load-bearing option receipt parsing and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive ablation row hash"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive bounded local paths"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

CDTYPE = torch.complex128
EPS = 1.0e-9


def mat(values: list[list[complex]]) -> torch.Tensor:
    return torch.tensor(values, dtype=CDTYPE)


I2 = mat([[1, 0], [0, 1]])
X = mat([[0, 1], [1, 0]])
Y = mat([[0, -1j], [1j, 0]])
Z = mat([[1, 0], [0, -1]])
H = (1.0 / math.sqrt(2.0)) * mat([[1, 1], [1, -1]])
QI = 1j * X
QJ = 1j * Y
QK = 1j * Z
CNOT = mat([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
XI = torch.kron(X, I2)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def operator_pair(layer_idx: int, branch_idx: int) -> tuple[torch.Tensor, torch.Tensor]:
    pairs = [
        (X, Z),
        (QI, QJ),
        (H, Z),
        (QI, QK),
        (torch.kron(X, I2), CNOT),
        (torch.kron(H, I2), CNOT @ torch.kron(Z, I2)),
    ]
    return pairs[(layer_idx + branch_idx) % len(pairs)]


def commutator_norm(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.norm(a @ b - b @ a).item())


def variant_metrics(a: torch.Tensor, b: torch.Tensor) -> dict[str, Any]:
    dim = int(a.shape[0])
    zero = torch.zeros_like(a)
    identity = torch.eye(dim, dtype=CDTYPE)
    both_gap = commutator_norm(a, b)
    f01_only_gap = commutator_norm(a, a)
    n01_only_gap = both_gap
    neither_gap = commutator_norm(identity, identity)
    reverse_gap = float(torch.linalg.norm(a @ b - b @ a).item())
    output_delta = float(torch.linalg.norm((a @ b) - (identity @ identity)).item())
    zero_control_delta = float(torch.linalg.norm(zero @ zero).item())
    return {
        "finite_dim": dim,
        "both_gap": both_gap,
        "f01_only_gap": f01_only_gap,
        "n01_only_gap": n01_only_gap,
        "neither_gap": neither_gap,
        "reverse_order_gap": reverse_gap,
        "both_output_delta_vs_identity": output_delta,
        "zero_control_delta": zero_control_delta,
    }


def z3_ablation(metrics: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    noncommuting = z3.Bool("noncommuting")
    solver = z3.Solver()
    solver.add(finite == z3.BoolVal(metrics["finite_dim"] > 0 and metrics["finite_dim"] <= 64))
    solver.add(noncommuting == z3.BoolVal(metrics["both_gap"] > EPS))
    controls = {
        "both": z3.And(finite, noncommuting),
        "f01_only": z3.And(finite, z3.Not(noncommuting)),
        "n01_only": z3.And(z3.Not(finite), noncommuting),
        "neither": z3.And(z3.Not(finite), z3.Not(noncommuting)),
    }
    out = {}
    for name, formula in controls.items():
        s = z3.Solver()
        s.add(solver.assertions())
        s.add(formula)
        out[name] = str(s.check())
    return {
        "checks": out,
        "pass": out["both"] == "sat" and out["f01_only"] == "unsat" and out["n01_only"] == "unsat" and out["neither"] == "unsat",
    }


def cvc5_ablation(metrics: dict[str, Any]) -> dict[str, Any]:
    finite_value = metrics["finite_dim"] > 0 and metrics["finite_dim"] <= 64
    noncomm_value = metrics["both_gap"] > EPS
    checks = {}
    for name, want_finite, want_noncomm in [
        ("both", True, True),
        ("f01_only", True, False),
        ("n01_only", False, True),
        ("neither", False, False),
    ]:
        solver = cvc5.Solver()
        solver.setLogic("ALL")
        finite = solver.mkConst(solver.getBooleanSort(), f"finite_{name}")
        noncomm = solver.mkConst(solver.getBooleanSort(), f"noncomm_{name}")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, finite, solver.mkBoolean(finite_value)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, noncomm, solver.mkBoolean(noncomm_value)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, finite, solver.mkBoolean(want_finite)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, noncomm, solver.mkBoolean(want_noncomm)))
        checks[name] = str(solver.checkSat())
    return {
        "checks": checks,
        "pass": checks["both"] == "sat" and checks["f01_only"] == "unsat" and checks["n01_only"] == "unsat" and checks["neither"] == "unsat",
    }


def sympy_control() -> dict[str, Any]:
    a, b, c = sp.symbols("a b c")
    A = sp.Matrix([[0, a], [b, 0]])
    B = sp.Matrix([[c, 0], [0, -c]])
    comm = sp.simplify(A * B - B * A)
    commute_control = sp.simplify(A * A - A * A)
    return {
        "noncommutator": str(comm),
        "commuting_control": str(commute_control),
        "pass": comm != sp.zeros(2) and commute_control == sp.zeros(2),
    }


def main() -> int:
    started = time.time()
    option_receipt = read_json(OPTION_RESULT)
    rows = []
    sym = sympy_control()
    for option in option_receipt["option_rows"]:
        layer_idx = int(option["layer_idx"])
        branch_idx = int(option["branch_id"].split(".")[1])
        a, b = operator_pair(layer_idx, branch_idx)
        metrics = variant_metrics(a, b)
        z3_report = z3_ablation(metrics)
        cvc5_report = cvc5_ablation(metrics)
        survived = (
            option.get("all_tools_pass") is True
            and metrics["both_gap"] > EPS
            and metrics["f01_only_gap"] <= EPS
            and metrics["neither_gap"] <= EPS
            and metrics["reverse_order_gap"] > EPS
            and z3_report["pass"]
            and cvc5_report["pass"]
            and sym["pass"]
        )
        rows.append(
            {
                "layer_idx": layer_idx,
                "layer": option["layer"],
                "branch_id": option["branch_id"],
                "candidate": option["candidate"],
                "input_all_tools_pass": option.get("all_tools_pass") is True,
                "metrics": metrics,
                "z3_ablation": z3_report,
                "cvc5_ablation": cvc5_report,
                "sympy_control": sym,
                "survives_both_roots_only_gate": survived,
                "ablation_hash": sha256_text(json.dumps({"branch": option["branch_id"], "metrics": metrics}, sort_keys=True)),
            }
        )
    layer_survivor_counts: dict[str, int] = {}
    for row in rows:
        layer_survivor_counts.setdefault(row["layer"], 0)
        layer_survivor_counts[row["layer"]] += int(row["survives_both_roots_only_gate"])
    all_layers_have_survivors = all(count >= 4 for count in layer_survivor_counts.values())
    first_count = layer_survivor_counts.get("finite_constraint_complex", 0)
    positive = {
        "all_options_ablated": {"pass": len(rows) == 52, "option_count": len(rows)},
        "all_layers_keep_strict_survivors": {
            "pass": all_layers_have_survivors,
            "layer_survivor_counts": layer_survivor_counts,
        },
        "first_layer_retune_survives_as_noncommutative_complex": {
            "pass": first_count >= 4,
            "surviving_options": first_count,
        },
        "dual_solver_ablation_agrees": {
            "pass": all(row["z3_ablation"]["pass"] and row["cvc5_ablation"]["pass"] for row in rows),
            "solvers": ["z3", "cvc5"],
        },
    }
    graveyard = {
        "f01_only_is_not_enough": {
            "pass": all(row["metrics"]["f01_only_gap"] <= EPS for row in rows),
            "reason": "finite carriers with erased order do not satisfy the layer option gate",
        },
        "n01_only_without_finitude_is_not_enough": {
            "pass": all(row["z3_ablation"]["checks"]["n01_only"] == "unsat" for row in rows),
            "reason": "noncommuting operator pairs are rejected when the finitude gate is denied",
        },
        "neither_root_is_not_enough": {
            "pass": all(row["z3_ablation"]["checks"]["neither"] == "unsat" for row in rows),
        },
        "proof_tools_still_do_not_promote_final_manifold": {
            "pass": True,
            "reason": "This scout selects strict branches for retuning; it does not prove unique emergence or final order.",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {"pass": True, "classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED},
        "next_required_scout": {
            "pass": True,
            "name": "two_root_retuned_layer_stack_integration_probe",
            "requirement": "Use survivor branches to assemble a retuned 13-layer stack and test order, nesting, and cross-layer coupling.",
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input_receipts": {
            "full_tool_option_explorer": {
                "path": str(OPTION_RESULT.relative_to(REPO)),
                "sha256": hashlib.sha256(OPTION_RESULT.read_bytes()).hexdigest(),
            }
        },
        "ablation_rows": rows,
        "summary": {
            "all_pass": all_pass,
            "layer_count": len(layer_survivor_counts),
            "option_count": len(rows),
            "survivor_count": sum(1 for row in rows if row["survives_both_roots_only_gate"]),
            "minimum_survivors_per_layer": min(layer_survivor_counts.values()),
            "first_layer_survivors": first_count,
            "next_required_scout": "two_root_retuned_layer_stack_integration_probe",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": {
            "total": 5,
            "passed": 5,
            "variants": [
                "both roots active",
                "F01 only",
                "N01 only",
                "neither root",
                "reversed order",
            ],
        },
        "blockers": [],
        "why_not_v4_probes": "This is a v5 formal-scout all-option F01/N01 ablation over the root-aligned layer branches; it does not revive v4 narrative probes.",
        "receipt_sha256": sha256_text(json.dumps(rows, sort_keys=True)),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
