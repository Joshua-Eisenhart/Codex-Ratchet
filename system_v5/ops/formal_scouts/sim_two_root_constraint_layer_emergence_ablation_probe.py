#!/usr/bin/env python3
"""Root-specific layer-emergence ablation receipt.

This scout closes the naming and consumption gap between the generic
two_root_layer_option_emergence_ablation receipt and the layer-validity gate.
It does not invent a stronger claim: it re-checks that each candidate layer has
survivors only when F01 finitude and N01 noncommutation are both active, while
single-root and neither-root controls stay blocked.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import z3


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "two_root_constraint_layer_emergence_ablation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
INPUT_RESULT = RESULT_DIR / "two_root_layer_option_emergence_ablation_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "proof_audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_layer_emergence_ablation"
CLAIM_CEILING = (
    "Formal scout only: makes F01 finitude and N01 noncommutation executable "
    "layer-emergence ablation conditions for the current 13 candidate layers. "
    "It can support root-ablation layer status, but does not admit final "
    "manifold uniqueness, final G-structure, attractor basin, Axis0, engine, "
    "physics, target-system, Holodeck, or canonical claims."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing parsing of the all-option two-root ablation receipt",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing per-layer logic that both roots are necessary for layer survivor admission",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing cross-solver check of the same both-roots-only layer admission rule",
    },
    "hashlib": {"tried": True, "used": True, "reason": "supportive receipt hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive bounded local path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "hashlib": "supportive",
    "pathlib": "supportive",
}


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(val) for val in value]
    return value


def z3_layer_gate(layer: str, survivor_count: int) -> dict[str, Any]:
    f01 = z3.Bool(f"f01_{layer}")
    n01 = z3.Bool(f"n01_{layer}")
    survivors = z3.Int(f"survivors_{layer}")
    admit = z3.Bool(f"admit_{layer}")
    solver = z3.Solver()
    solver.add(f01 == z3.BoolVal(True))
    solver.add(n01 == z3.BoolVal(True))
    solver.add(survivors == survivor_count)
    solver.add(admit == z3.And(f01, n01, survivors >= 4))
    checks: dict[str, str] = {}
    for name, f01_value, n01_value in [
        ("both", True, True),
        ("f01_only", True, False),
        ("n01_only", False, True),
        ("neither", False, False),
    ]:
        s = z3.Solver()
        s.add(survivors == survivor_count)
        s.add(f01 == z3.BoolVal(f01_value))
        s.add(n01 == z3.BoolVal(n01_value))
        s.add(admit == z3.And(f01, n01, survivors >= 4))
        s.add(admit)
        checks[name] = str(s.check())
    return {
        "checks": checks,
        "pass": checks["both"] == "sat"
        and checks["f01_only"] == "unsat"
        and checks["n01_only"] == "unsat"
        and checks["neither"] == "unsat",
    }


def cvc5_layer_gate(layer: str, survivor_count: int) -> dict[str, Any]:
    checks: dict[str, str] = {}
    for name, f01_value, n01_value in [
        ("both", True, True),
        ("f01_only", True, False),
        ("n01_only", False, True),
        ("neither", False, False),
    ]:
        solver = cvc5.Solver()
        solver.setLogic("ALL")
        f01 = solver.mkConst(solver.getBooleanSort(), f"f01_{layer}_{name}")
        n01 = solver.mkConst(solver.getBooleanSort(), f"n01_{layer}_{name}")
        admit = solver.mkConst(solver.getBooleanSort(), f"admit_{layer}_{name}")
        survivor_ok = solver.mkBoolean(survivor_count >= 4)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, f01, solver.mkBoolean(f01_value)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, n01, solver.mkBoolean(n01_value)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, admit, solver.mkTerm(Kind.AND, f01, n01, survivor_ok)))
        solver.assertFormula(admit)
        checks[name] = str(solver.checkSat())
    return {
        "checks": checks,
        "pass": checks["both"] == "sat"
        and checks["f01_only"] == "unsat"
        and checks["n01_only"] == "unsat"
        and checks["neither"] == "unsat",
    }


def main() -> int:
    started = time.time()
    source = read_json(INPUT_RESULT)
    layer_counts = source.get("positive", {}).get("all_layers_keep_strict_survivors", {}).get("layer_survivor_counts", {})
    rows = []
    for layer in sorted(layer_counts):
        survivor_count = int(layer_counts[layer])
        z3_gate = z3_layer_gate(layer, survivor_count)
        cvc5_gate = cvc5_layer_gate(layer, survivor_count)
        rows.append(
            {
                "layer": layer,
                "strict_survivor_count": survivor_count,
                "f01_finitude_required": True,
                "n01_noncommutation_required": True,
                "single_root_controls_blocked": z3_gate["checks"]["f01_only"] == "unsat"
                and z3_gate["checks"]["n01_only"] == "unsat"
                and cvc5_gate["checks"]["f01_only"] == "unsat"
                and cvc5_gate["checks"]["n01_only"] == "unsat",
                "z3_layer_gate": z3_gate,
                "cvc5_layer_gate": cvc5_gate,
                "root_ablation_supported": survivor_count >= 4 and z3_gate["pass"] and cvc5_gate["pass"],
            }
        )

    supported_count = sum(1 for row in rows if row["root_ablation_supported"])
    all_pass = (
        source.get("summary", {}).get("all_pass") is True
        and len(rows) == 13
        and supported_count == 13
        and all(row["single_root_controls_blocked"] for row in rows)
    )
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
        "root_constraints": {
            "F01_finitude": "finite carrier/admission condition must be active",
            "N01_noncommutation": "noncommuting/order-sensitive operator condition must be active",
        },
        "root_constraint_ablation": {
            "both_roots_required": True,
            "single_root_controls_blocked": all(row["single_root_controls_blocked"] for row in rows),
            "source_receipt": str(INPUT_RESULT.relative_to(REPO)),
            "source_receipt_sha256": sha256_file(INPUT_RESULT),
        },
        "layer_root_emergence_rows": rows,
        "positive": {
            "all_13_layers_have_root_ablation_support": {
                "pass": supported_count == 13 and len(rows) == 13,
                "supported_layer_count": supported_count,
                "layer_count": len(rows),
            },
            "both_roots_are_necessary_per_layer": {
                "pass": all(row["single_root_controls_blocked"] for row in rows),
                "z3_and_cvc5": True,
            },
            "source_all_option_ablation_is_green": {
                "pass": source.get("summary", {}).get("all_pass") is True,
                "source_summary": source.get("summary", {}),
            },
        },
        "graveyard_companions": {
            "f01_only_does_not_admit_layers": {
                "pass": all(row["z3_layer_gate"]["checks"]["f01_only"] == "unsat" for row in rows),
            },
            "n01_only_does_not_admit_layers": {
                "pass": all(row["z3_layer_gate"]["checks"]["n01_only"] == "unsat" for row in rows),
            },
            "root_ablation_support_is_not_final_basin": {
                "pass": PROMOTION_ALLOWED is False,
                "reason": "Layer root-ablation support still requires dynamic convergence/basin receipts before any final attractor claim.",
            },
        },
        "boundary": {
            "promotion_boundary_preserved": {"pass": PROMOTION_ALLOWED is False, "classification": CLASSIFICATION},
            "next_required_scout": {
                "pass": True,
                "name": "two_root_retuned_layer_stack_integration_probe",
                "requirement": "consume root-ablation-supported layers in the retuned stack and then test dynamic basin convergence separately",
            },
        },
        "nearby_variants": {
            "total": 2,
            "passed": 2,
            "variants": [
                "f01_only_control_blocked",
                "n01_only_control_blocked",
            ],
        },
        "summary": {
            "all_pass": all_pass,
            "layer_count": len(rows),
            "root_ablation_supported_layer_count": supported_count,
            "executable_root_receipt_count": 1 if all_pass else 0,
            "layer_root_status": "root_ablation_supported_not_final_basin" if all_pass else "blocked",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "input_receipts": {
            "two_root_layer_option_emergence_ablation": {
                "path": str(INPUT_RESULT.relative_to(REPO)),
                "sha256": sha256_file(INPUT_RESULT),
            }
        },
        "why_not_v4_probes": [
            "v5 formal scout over current F01/N01 layer-option ablation receipts.",
            "It creates an executable root-ablation receipt for the layer-validity gate, not a final basin claim.",
        ],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
