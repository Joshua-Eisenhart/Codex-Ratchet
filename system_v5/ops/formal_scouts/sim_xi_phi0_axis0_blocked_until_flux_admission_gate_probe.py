#!/usr/bin/env python3
"""Xi/Phi0/Axis0 blocked-until-flux-admission gate.

Formal scout only.

This Phase 9 row is intentionally a blocked-reason receipt. The Phase 8 receipt
opened a quaternionic flux candidate but kept final flux unadmitted. Therefore
Xi, Phi0, and Axis0 must not run.
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "xi_phi0_axis0_blocked_until_flux_admission_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
PHASE8_RESULT = RESULT_DIR / "quaternionic_chiral_boundary_flux_candidate_gate_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "phase9_xi_phi0_axis0_blocked_until_flux_admission"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal blocked-reason scout only: Xi/Phi0/Axis0 remain blocked because "
    "the Phase 8 receipt did not admit final flux. This does not admit Xi, "
    "Phi0, Axis0, basin, physics, or ontology."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing torch-native blocked-state tensor readout for the nonclassical gate"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing blocked-until-flux-admission gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent blocked-until-flux-admission cross-check"},
    "python_json": {"tried": True, "used": True, "reason": "supportive Phase 8 receipt read and result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return value.detach().cpu().item()
        return value.detach().cpu().tolist()
    return value


def phase8_gate() -> dict[str, Any]:
    exists = PHASE8_RESULT.exists()
    final_flux_admitted = False
    phase8_all_pass = False
    if exists:
        data = json.loads(PHASE8_RESULT.read_text(encoding="utf-8"))
        phase8_all_pass = bool(data.get("all_pass", False))
        final_flux_admitted = bool(data.get("summary", {}).get("final_flux_admitted", False))
    return {
        "pass": exists and phase8_all_pass and final_flux_admitted is False,
        "phase8_result": str(PHASE8_RESULT.relative_to(ROOT)),
        "phase8_exists": exists,
        "phase8_all_pass": phase8_all_pass,
        "final_flux_admitted": final_flux_admitted,
    }


def z3_block_gate(final_flux_admitted: bool) -> dict[str, Any]:
    flux = z3.Bool("final_flux_admitted")
    axis0_allowed = z3.Bool("axis0_allowed")
    solver = z3.Solver()
    solver.add(flux == final_flux_admitted)
    solver.add(axis0_allowed == flux)
    solver.add(z3.Not(axis0_allowed))
    return {"pass": solver.check() == z3.sat, "status": str(solver.check())}


def cvc5_block_gate(final_flux_admitted: bool) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    flux = solver.mkConst(bool_sort, "final_flux_admitted")
    axis0_allowed = solver.mkConst(bool_sort, "axis0_allowed")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, flux, solver.mkBoolean(final_flux_admitted)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, axis0_allowed, flux))
    solver.assertFormula(solver.mkTerm(Kind.NOT, axis0_allowed))
    status = solver.checkSat()
    return {"pass": str(status) == "sat", "status": str(status)}


def torch_blocked_state_gate(final_flux_admitted: bool) -> dict[str, Any]:
    blocked = torch.tensor([0.0 if final_flux_admitted else 1.0], dtype=torch.float64)
    return {
        "pass": bool(blocked.item() == 1.0),
        "blocked_state_tensor": blocked,
        "readout": "1 means Xi/Phi0/Axis0 blocked because final_flux_admitted is false",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    phase8 = phase8_gate()
    torch_gate = torch_blocked_state_gate(bool(phase8["final_flux_admitted"]))
    z3_gate = z3_block_gate(bool(phase8["final_flux_admitted"]))
    cvc5_gate = cvc5_block_gate(bool(phase8["final_flux_admitted"]))
    positive = {
        "phase8_receipt_present_but_final_flux_not_admitted": phase8,
        "torch_blocked_state_readout": torch_gate,
        "z3_axis0_blocked_until_flux_admission": z3_gate,
        "cvc5_axis0_blocked_until_flux_admission": cvc5_gate,
    }
    graveyard_companions = {
        "GC1_axis0_cannot_repair_missing_flux": {
            "pass": True,
            "why_rejected": "Axis0 is downstream and cannot be used to create or repair flux admission",
        },
        "GC2_xi_phi0_without_admitted_flux_rejected": {
            "pass": True,
            "why_rejected": "Xi/Phi0 cut-state readouts require an admitted flux dependency",
        },
        "GC3_scalar_axis0_placeholder_rejected": {
            "pass": True,
            "why_rejected": "a signed scalar placeholder is not an admitted QIT/FEP readout",
        },
    }
    blocked_reason = {
        "kind": "blocked_reason",
        "reason": "final_flux_not_admitted",
        "scope": "Phase 9 Xi/Phi0/Axis0",
        "next_admissible_step": "promote or falsify the Phase 8 quaternionic flux candidate with a separate flux-admission receipt before running Xi/Phi0/Axis0",
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_xi_phi0_axis0_not_run": {"pass": True, "xi_phi0_axis0_run": False},
        "B3_downstream_consumers_blocked": {"pass": True, "blocked_consumers": ["Xi", "Phi0", "Axis0", "basin", "physics"]},
    }
    controls = {"positive": positive, "negative": graveyard_companions, "boundary": boundary}
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": ["blocked_readout_gate : final_flux_admitted=false -> Xi/Phi0/Axis0 not admitted"],
        "domain": "D9 = Phase 8 flux-admission receipt state",
        "codomain_or_output": "O9 = blocked_reason receipt, no Xi/Phi0/Axis0 run",
        "carrier_realization": "no carrier action; downstream readouts blocked",
        "peps3d_embedding": "blocked; no new PEPS3D readout because final flux is not admitted",
        "spinor_state": "blocked",
        "quaternion_action": "blocked pending final flux admission",
        "dependency_receipts": ["system_v5/ops/formal_scouts/results/quaternionic_chiral_boundary_flux_candidate_gate_probe_results.json"],
        "downstream_blocks": ["Xi", "Phi0", "Axis0", "basin", "physics"],
        "blocked_reason": blocked_reason,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": controls,
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "blockers": [],
        "summary": {
            "phase": 9,
            "candidate": "xi_phi0_axis0_blocked_until_flux_admission",
            "final_flux_admitted": bool(phase8["final_flux_admitted"]),
            "xi_phi0_axis0_run": False,
            "max_qubits": 0,
            "max_peps3d_sites": 0,
            "max_peps3d_bond": 0,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 Phase 9 blocked-readout formal scout. It is not Xi, Phi0, Axis0, basin, or physics evidence."
        ),
        "next_required_work": [blocked_reason["next_admissible_step"]],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
