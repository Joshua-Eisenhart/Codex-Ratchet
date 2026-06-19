#!/usr/bin/env python3
"""Packet-local validator for entropy_type_ratchet_v0."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

SIM_ID = "entropy_type_ratchet_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = PACKET / "results" / f"{SIM_ID}_envelope_results.json"
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, errors: list[str], name: str) -> dict[str, Any]:
    require(isinstance(value, dict), errors, f"{name} must be an object")
    return value if isinstance(value, dict) else {}


def main() -> int:
    result_path = Path(sys.argv[1]) if len(sys.argv) > 1 else RESULT
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    require(payload.get("schema_version") == "three_engine_sim_result_v1", errors, "schema_version mismatch")
    require(payload.get("sim_id") == SIM_ID, errors, "sim_id mismatch")
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification mismatch")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")
    require(set(payload.get("engines", {})) == {"julia", "jax", "pytorch"}, errors, "three engines required")

    rows = payload.get("per_step_type_admissibility_table")
    require(isinstance(rows, list) and len(rows) == 9, errors, "expected 9 per-step rows")
    if isinstance(rows, list) and rows:
        require(rows[-1]["entropy_types"]["state_plus_record_conservation"]["status"] == "computable", errors, "record row must be computable at final step")
        require(rows[0]["entropy_types"]["von_neumann_entropy"]["status"] == "undefined", errors, "vN must be undefined at seed")
        require(rows[0]["entropy_types"]["von_neumann_entropy"]["missing_structure"] == "density_quotient_rho", errors, "vN missing structure mismatch")
        require(rows[3]["entropy_types"]["conditional_vn_and_mutual_information"]["status"] == "degenerate", errors, "conditional row must be degenerate at first bipartition")
        require(rows[4]["entropy_types"]["conditional_vn_and_mutual_information"]["status"] == "computable", errors, "conditional row must become substantive after channel")
        require(rows[5]["entropy_types"]["state_plus_record_conservation"]["value"]["computed_defect_exact"] == "0", errors, "record conservation defect must be zero")

    controls = as_dict(payload.get("controls"), errors, "controls")
    premature = as_dict(controls.get("premature_evaluation"), errors, "controls.premature_evaluation")
    for name in ["von_neumann_entropy", "conditional_vn_and_mutual_information", "coherent_information"]:
        require(as_dict(premature.get(name), errors, f"premature.{name}").get("pass") is True, errors, f"{name} premature failure control did not pass")
    require(as_dict(controls.get("type_confusion"), errors, "controls.type_confusion").get("pass") is True, errors, "type confusion control did not pass")
    require(as_dict(controls.get("order_shuffle"), errors, "controls.order_shuffle").get("prediction_2_status") == "survived", errors, "order shuffle did not survive")
    require(as_dict(controls.get("degenerate_flag"), errors, "controls.degenerate_flag").get("pass") is True, errors, "degenerate flag control did not pass")

    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    for solver_name in ["z3", "cvc5", "julia_z3"]:
        proof = as_dict(proofs.get(solver_name), errors, f"proofs.{solver_name}")
        require(proof.get("verdict") == "unsat", errors, f"{solver_name} table/final identity must be unsat")
        require(proof.get("perturbed_availability_entry_verdict") == "sat", errors, f"{solver_name} perturbation must be sat")

    divergence = as_dict(payload.get("divergence"), errors, "divergence")
    require(float(divergence.get("max_divergence", 1.0)) <= 1.0e-10, errors, "max divergence too large")
    engine_values = as_dict(divergence.get("engine_values"), errors, "divergence.engine_values")
    for engine in ["julia", "jax", "pytorch"]:
        row = as_dict(engine_values.get(engine), errors, f"engine_values.{engine}")
        require(row.get("final_available_type_count") == 6, errors, f"{engine} final type count must be 6")
        require(abs(float(row.get("rho_entropy_nats", 0.0)) - math.log(2)) <= 1.0e-10, errors, f"{engine} rho entropy mismatch")

    require("TOOL_INTENT_MATRIX" in payload, errors, "TOOL_INTENT_MATRIX missing")
    require("build_three_engine_envelope" in payload.get("TOOL_MANIFEST", {}), errors, "standard envelope helper manifest missing")

    if not errors:
        nested = subprocess.run(
            [
                SIM_PY,
                "scripts/validate_three_engine_sim_result.py",
                "--require-pytorch",
                "--strict-source-backed",
                "--require-tool-intent",
                str(result_path),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        require(nested.returncode == 0, errors, f"nested strict validator failed: {nested.stdout} {nested.stderr}")

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    print(json.dumps({"ok": True, "result_json": str(result_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
