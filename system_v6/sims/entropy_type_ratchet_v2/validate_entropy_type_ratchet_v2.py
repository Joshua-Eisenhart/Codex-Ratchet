#!/usr/bin/env python3
"""Packet-local validator for entropy_type_ratchet_v2."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from entropy_type_ratchet_v2_common import (
    PACKET,
    ROOT,
    SIM_ID,
    TYPE_ORDER,
    reject_composed_sequence,
    reject_shortcut_availability,
)

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


RESULT = PACKET / "results" / f"{SIM_ID}_envelope_results.json"
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, errors: list[str], name: str) -> dict[str, Any]:
    require(isinstance(value, dict), errors, f"{name} must be an object")
    return value if isinstance(value, dict) else {}


def forbidden_source_errors() -> list[str]:
    errors: list[str] = []
    forbidden = ["PRIMARY_STEP_PLAN", "\"en" + "ables\"", "'en" + "ables'"]
    for path in [
        PACKET / f"{SIM_ID}_common.py",
        PACKET / f"{SIM_ID}_jax.py",
        PACKET / f"{SIM_ID}_pytorch.py",
        PACKET / f"{SIM_ID}_envelope.py",
        PACKET / f"{SIM_ID}_julia.jl",
    ]:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                errors.append(f"forbidden claim-path token {token!r} in {path.relative_to(ROOT)}")
    return errors


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
    errors.extend(builder_audit_boundary_errors(payload, PACKET / "audit_verdict.md"))
    require(set(payload.get("engines", {})) == {"julia", "jax", "pytorch"}, errors, "all three engine lanes required")
    errors.extend(forbidden_source_errors())

    rows = payload.get("per_step_type_admissibility_table")
    require(isinstance(rows, list) and len(rows) == 9, errors, "expected 9 per-step rows")
    if isinstance(rows, list) and rows:
        require(all(row.get("availability_source") == "construction_attempt" for row in rows), errors, "rows must be construction-attempt sourced")
        require(all("new_en" + "abling_structures" not in row for row in rows), errors, "v0-style row field present")
        require(rows[0]["entropy_types"]["von_neumann_entropy"]["status"] == "undefined", errors, "vN must fail at seed")
        require(rows[0]["entropy_types"]["von_neumann_entropy"]["failure"]["missing_structure"] == "density_quotient_rho", errors, "vN failure object mismatch")
        require(rows[2]["entropy_types"]["von_neumann_entropy"]["status"] == "computable", errors, "vN must construct at lens quotient")
        require(rows[3]["entropy_types"]["conditional_vn_and_mutual_information"]["status"] == "degenerate", errors, "first bipartition must be degenerate")
        require(rows[4]["entropy_types"]["coherent_information"]["status"] == "computable", errors, "coherent information must construct at channel")
        require(rows[5]["entropy_types"]["state_plus_record_conservation"]["value"]["computed_defect_exact"] == "0", errors, "record conservation defect mismatch")
        require(len(rows[-1]["available_types"]) == len(TYPE_ORDER), errors, "final row must expose all six types")

    comparison = as_dict(payload.get("doctrine_table_comparison"), errors, "doctrine_table_comparison")
    require(comparison.get("agreement") is True, errors, "doctrine comparison did not agree")
    require(not comparison.get("findings"), errors, "doctrine comparison has findings")
    sequence_derivation = as_dict(payload.get("sequence_derivation"), errors, "sequence_derivation")
    require(sequence_derivation.get("sequence_source") == "consumed_parent_artifacts", errors, "primary sequence must be consumed_parent_artifacts")
    require(isinstance(sequence_derivation.get("parent_rows"), list) and len(sequence_derivation.get("parent_rows", [])) == 9, errors, "sequence_derivation must expose 9 parent rows")
    require(sequence_derivation.get("operation_order") == [row["step_id"] for row in rows] if isinstance(rows, list) else False, errors, "operation order must match emitted table rows")
    for parent_name in ["manifold_unified_run_v0_trajectory", "ratchet_deep_chain_v0", "ratchet_order_breadth_v0"]:
        parent = as_dict(as_dict(sequence_derivation.get("source_paths"), errors, "sequence_derivation.source_paths").get(parent_name), errors, f"sequence_derivation.source_paths.{parent_name}")
        require(bool(parent.get("git_head_blob")) and bool(parent.get("sha256")), errors, f"{parent_name} source hash missing")

    alternative = as_dict(payload.get("alternative_sequence_findings"), errors, "alternative_sequence_findings")
    require(as_dict(alternative.get("meta"), errors, "alternative.meta").get("alternative_source") == "ratchet_order_breadth_v0.controls.live_order_blind_signatures", errors, "alternative source mismatch")
    require(isinstance(alternative.get("off_doctrine_findings"), list), errors, "alternative off-doctrine findings must be explicit list")

    controls = as_dict(payload.get("controls"), errors, "controls")
    premature = as_dict(controls.get("premature_evaluation"), errors, "controls.premature_evaluation")
    for name in [
        "chart_uniform_differential_entropy",
        "von_neumann_entropy",
        "conditional_vn_and_mutual_information",
        "coherent_information",
        "state_plus_record_conservation",
    ]:
        require(as_dict(premature.get(name), errors, f"premature.{name}").get("pass") is True, errors, f"{name} premature failure control did not pass")
    require(as_dict(controls.get("spoofed_enable"), errors, "controls.spoofed_enable").get("pass") is True, errors, "spoofed shortcut control did not pass")
    require(as_dict(controls.get("composed_sequence_rejection"), errors, "controls.composed_sequence_rejection").get("pass") is True, errors, "composed sequence rejection control did not pass")
    require(as_dict(controls.get("alternative_sequence"), errors, "controls.alternative_sequence").get("pass") is True, errors, "alternative sequence control did not pass")
    require(as_dict(controls.get("type_confusion"), errors, "controls.type_confusion").get("pass") is True, errors, "type confusion control did not pass")
    require(as_dict(controls.get("order_shuffle"), errors, "controls.order_shuffle").get("prediction_2_status") == "survived", errors, "order shuffle did not survive")
    require(as_dict(controls.get("degenerate_flag"), errors, "controls.degenerate_flag").get("pass") is True, errors, "degenerate flag control did not pass")
    try:
        reject_shortcut_availability({"shortcut_availability": "computable"})
    except Exception as exc:
        require(str(exc) == "declared-enable shortcut rejected before construction", errors, "shortcut rejection reason mismatch")
    else:
        errors.append("shortcut rejection function accepted spoof")
    try:
        reject_composed_sequence({"sequence_source": "packet_local_literal", "operation_order": ["integrated_seed", "leaf_conditioning"]})
    except Exception as exc:
        require(str(exc) == "composed-in-packet sequence rejected; sequence must be consumed_parent_artifacts", errors, "composed-sequence rejection reason mismatch")
    else:
        errors.append("composed sequence rejection accepted packet-local literal")

    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    for solver_name in ["z3", "cvc5", "julia_z3"]:
        proof = as_dict(proofs.get(solver_name), errors, f"proofs.{solver_name}")
        require(proof.get("verdict") == "unsat", errors, f"{solver_name} identity must be unsat")
        require(proof.get("perturbed_construction_path_verdict") == "sat", errors, f"{solver_name} construction perturbation must be sat")
        require(proof.get("load_bearing") is True, errors, f"{solver_name} must be load-bearing")

    require("TOOL_INTENT_MATRIX" in payload, errors, "TOOL_INTENT_MATRIX missing")
    require("tool_intent" in payload, errors, "tool_intent missing")
    require("build_three_engine_envelope" in payload.get("TOOL_MANIFEST", {}), errors, "standard envelope helper manifest missing")
    gates = as_dict(payload.get("builder_gates"), errors, "builder_gates")
    require(gates.get("no_builder_audit_verdict") is True, errors, "no_builder_audit_verdict gate missing")
    require(gates.get("sequence_from_parent") is True, errors, "sequence_from_parent gate missing")
    require(gates.get("composed_sequence_rejected") is True, errors, "composed_sequence_rejected gate missing")

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
