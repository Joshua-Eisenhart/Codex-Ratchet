#!/usr/bin/env python3
"""Packet validator for axis0_amendment_light_sweep_v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "axis0_amendment_light_sweep_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE_RESULT = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT / "scripts"))
import validate_three_engine_sim_result as generic_validator  # noqa: E402


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def candidate(payload: dict[str, Any], cid: str) -> dict[str, Any]:
    for row in payload["candidate_verdict_table"]:
        if row["candidate"] == cid:
            return row
    raise AssertionError(f"missing candidate {cid}")


def validate_packet(envelope: dict[str, Any], jax: dict[str, Any], julia: dict[str, Any]) -> dict[str, bool]:
    cp11 = candidate(envelope, "A0.CP.11")
    cp12 = candidate(envelope, "A0.CP.12")
    cp13 = candidate(envelope, "A0.CP.13")
    cp14 = candidate(envelope, "A0.CP.14")
    return {
        "generic_three_engine_validator_passes": generic_validator.validate(
            envelope, require_pytorch=False, require_tool_intent=False
        )
        == [],
        "supplement_commit_pinned": envelope["authority_binding"]["supplement"]["commit"] == "34596316d",
        "scratch_no_promotion": envelope["classification"] == "scratch_diagnostic"
        and envelope["promotion_allowed"] is False
        and envelope["formal_admission_allowed"] is False,
        "cp11_full_33_vector": cp11["vector_status"] == "computed_33_cell" and len(cp11["sign_vector"]) == 33,
        "cp12_light_33_vector_heavy_queued": cp12["vector_status"] == "computed_33_cell"
        and len(cp12["sign_vector"]) == 33
        and cp12["queued_heavy"] is True,
        "cp13_global_heavy_queued_no_fake_vector": cp13["vector_status"] == "not_computed_heavy_global_bipartition_required"
        and cp13["queued_heavy"] is True
        and "sign_vector" not in cp13,
        "cp14_full_33_vector": cp14["vector_status"] == "computed_33_cell" and len(cp14["sign_vector"]) == 33,
        "canonical_alias_forms_present": all(
            row.get("canonical_alias_form_sha256") for row in [cp11, cp12, cp14]
        ),
        "disagreement_tables_present": all(
            len(row.get("cell_level_disagreement_table", [])) == 33 for row in [cp11, cp12, cp14]
        ),
        "boundary_helper_full": all(
            "reads_axis0_feedback_distinction" in row.get("distinction_boundary_check", {}) for row in [cp11, cp12, cp14]
        ),
        "owner_guard_row_present": all(
            "tracks_type1_type2_chirality" in row.get("owner_chirality_guard", {}) for row in [cp11, cp12, cp14]
        ),
        "owner_guard_control_fires": any(
            row["id"] == "control.deliberate_chirality_tracker"
            and row["verdict"] == "excluded-by-owner-type1-type2-chirality-guard"
            for row in envelope["control_verdicts"]
        ),
        "fork_row_tests_v0_twenty_under_pins": envelope["fork_row"]["v0_observation"]["pre_pin_disagreement_count"] == 20
        and envelope["fork_row"]["disagreement_count"] == 21
        and envelope["fork_row"]["pin_shift_vs_v0"]["count_delta"] == 1,
        "v0_regression_pin_bite_computed": {
            row["candidate"]: row["pin_bite_count"] for row in envelope["v0_regression_rows"]
        }
        == {"A0.CP.11": 13, "A0.CP.14": 8},
        "julia_exact_mirror_aligned": envelope["divergence"]["max_divergence"] == 0
        and jax["computed_vector_hashes"] == julia["computed_vector_hashes"],
        "pythorch_honestly_omitted": "pytorch" in envelope["engine_contract"]["omitted_lanes"],
        "smt_crossovers_pass": envelope["crossover_proofs"]["z3"]["verdict"] == "unsat"
        and envelope["crossover_proofs"]["cvc5"]["verdict"] == "unsat",
    }


def main() -> int:
    envelope = load_json(ENVELOPE_RESULT)
    jax = load_json(JAX_RESULT)
    julia = load_json(JULIA_RESULT)
    gates = validate_packet(envelope, jax, julia)
    result = {
        "schema": f"{SIM_ID}_validator_v1",
        "sim_id": SIM_ID,
        "result_path": rel(VALIDATOR_RESULT),
        "validated_envelope": rel(ENVELOPE_RESULT),
        "all_pass": all(gates.values()),
        "gates": gates,
    }
    write_json(VALIDATOR_RESULT, result)
    print(json.dumps({"result_path": rel(VALIDATOR_RESULT), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
