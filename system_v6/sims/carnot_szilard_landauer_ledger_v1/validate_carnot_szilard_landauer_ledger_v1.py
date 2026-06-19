#!/usr/bin/env python3
"""Packet-local validator for carnot_szilard_landauer_ledger_v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "carnot_szilard_landauer_ledger_v1"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def sat_models_ok(witnesses: dict[str, Any]) -> bool:
    for engine in witnesses.values():
        for section in ("cycle_rows", "szilard_landauer_rows"):
            for row in engine[section].values():
                if not all(row.values()):
                    return False
    return True


def main() -> int:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    errors: list[str] = []
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification must stay scratch_diagnostic")
    require(errors, payload.get("row_classification") == "classical_baseline", "row classification must be classical_baseline")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "envelope all_pass must be true")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict gate must be true")
    require(errors, sat_models_ok(payload["persisted_witnesses"]), "every SAT row must persist a solver model")
    temps = payload["pinned_temperatures"]
    require(errors, temps["T_h"]["num"] == 2 and temps["T_c"]["num"] == 1, "pinned temperatures must be T_h=2, T_c=1")
    reversible = payload["cycle_ledger_tables"]["reversible_carnot_cycle"]
    require(errors, reversible["derived"]["eta"]["num"] == 1 and reversible["derived"]["eta"]["den"] == 2, "Carnot eta must derive as 1/2")
    require(errors, reversible["derived"]["entropy_production"]["num"] == 0, "reversible entropy production must be zero")
    super_row = payload["cycle_ledger_tables"]["candidate_super_carnot_cycle"]
    require(errors, super_row["derived"]["eta"]["num"] == 3 and super_row["derived"]["eta"]["den"] == 4, "super-Carnot candidate eta must be 3/4")
    require(errors, super_row["derived"]["entropy_production"]["num"] < 0, "super-Carnot violation must be negative entropy production")
    require(errors, payload["builder_gates"]["super_carnot_unsat_from_ledger_constraints"] is True, "super-Carnot must be UNSAT from ledger constraints")
    for engine, control in payload["controls"]["broken_fence_drop_entropy_constraint_super_carnot"].items():
        solver_keys = ["julia_z3"] if engine == "julia" else ["z3", "cvc5"]
        for solver in solver_keys:
            require(errors, control[solver]["status"] == "sat", f"{engine} broken-fence {solver} must be SAT")
            require(errors, bool(control[solver].get("model")), f"{engine} broken-fence {solver} model missing")
        require(errors, control["numeric_eta_gt_eta_c"] is True, f"{engine} broken-fence eta witness must exceed eta_C")
    for engine, control in payload["controls"]["n01_order"].items():
        require(errors, control["normal"]["verdict"] == "sat", f"{engine} normal N01 order must be SAT")
        require(errors, control["permuted"]["verdict"] == "unsat", f"{engine} permuted N01 order must be UNSAT")
        require(errors, "computed_by" in control, f"{engine} N01 control must name computation path")
    for engine, control in payload["controls"]["misledgered_control"].items():
        require(errors, control["status"] == "caught", f"{engine} misledgered control must be caught")
        require(errors, control["errors"], f"{engine} misledgered control must report concrete errors")
    typed = payload["typed_entropy"]
    require(errors, typed["conversion"] == "1 bit * ln(2) = ln(2) nats", "typed bits/nats conversion missing")
    require(errors, "state-plus-record" in payload["connection_row"]["observation"], "connection row must carry v0 convention language")
    require(errors, "no cross-type entropy sum" in payload["connection_row"]["claim_boundary"], "connection row must preserve no-admission boundary")
    require(errors, "TOOL_INTENT_MATRIX" in payload, "TOOL_INTENT_MATRIX missing")
    for key, value in payload["builder_gates"].items():
        require(errors, value is True, f"builder gate failed: {key}")
    generic = validate_three_engine(payload, require_pytorch=True, require_source_backed=False, strict_source_backed=False, require_tool_intent=False)
    errors.extend(f"three_engine_shape: {err}" for err in generic)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    print(json.dumps({"ok": True, "result_json": str(RESULT.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
