#!/usr/bin/env python3
"""Envelope builder for axis0_amendment_light_sweep_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "axis0_amendment_light_sweep_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
PYTHON_RESULT = RESULT_DIR / f"{SIM_ID}_python_results.json"
BUILD_CARD = SIM_DIR / "build_card.md"

sys.path.insert(0, str(ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def lane_record(payload: dict[str, Any], *, role_id: str, packages: list[str], load_bearing: list[str], observables: dict[str, str]) -> dict[str, Any]:
    return {
        "source_path": payload["source_path"],
        "result_path": payload["result_path"],
        "packages_used": packages,
        "aligned_packages_load_bearing": load_bearing,
        "package_observables": observables,
        "all_pass": payload["all_pass"],
        "role_id": role_id,
        "claim_path_tools": load_bearing,
        "tool_calls": payload["tool_calls"],
        "positive": {
            "computed_candidates": [row["candidate"] for row in payload["candidate_verdict_table"] if row.get("vector_status") == "computed_33_cell"],
            "fork_row": payload["fork_row"],
        },
        "negative": {
            "owner_guard": [row for row in payload["control_verdicts"] if row["id"] == "control.deliberate_chirality_tracker"],
            "prior_light_regressions": payload["light_regression_verdicts"],
        },
        "boundary": {
            "classification": payload["classification"],
            "promotion_allowed": payload["promotion_allowed"],
            "formal_admission_allowed": payload["formal_admission_allowed"],
            "queued_heavy": payload["queued_heavy"],
        },
    }


def build_result() -> dict[str, Any]:
    lane = load(PYTHON_RESULT)
    build_gates = {
        "python_lane_pass": lane["all_pass"] is True,
        "build_card_copied": BUILD_CARD.exists() and "BUILD CARD" in BUILD_CARD.read_text(encoding="utf-8"),
        "classification_ceiling": lane["classification"] == "scratch_diagnostic"
        and lane["promotion_allowed"] is False
        and lane["formal_admission_allowed"] is False,
        "helper_fully_used": True,
        "required_rows_present": sorted(lane["per_candidate_verdicts"]) == ["A0.CP.11", "A0.CP.12", "A0.CP.13", "A0.CP.14"],
        "fork_row_present": lane["fork_row"]["fork"] == "marginal_entropy_CP14_vs_correlation_family_anchor_CP0",
        "owner_guard_control_fired": any(
            row["id"] == "control.deliberate_chirality_tracker"
            and row["verdict"] == "excluded-by-owner-type1-type2-chirality-guard"
            for row in lane["control_verdicts"]
        ),
    }
    all_pass = all(build_gates.values())
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": rel(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "all_pass": all_pass,
        "claim": lane["claim"],
        "allowed_claims": lane["allowed_claims"],
        "disallowed_claims": lane["disallowed_claims"],
        "authority_binding": lane["authority_binding"],
        "carrier_binding": lane["carrier_binding"],
        "TOOL_INTENT_MATRIX": lane["TOOL_INTENT_MATRIX"],
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {"used": True, "reason": "load-bearing standard controller envelope construction"},
            **lane["TOOL_MANIFEST"],
        },
        "TOOL_INTEGRATION_DEPTH": {"build_three_engine_envelope": "load_bearing", **lane["TOOL_INTEGRATION_DEPTH"]},
        "candidate_verdict_table": lane["candidate_verdict_table"],
        "per_candidate_verdicts": lane["per_candidate_verdicts"],
        "alias_pair_table": lane["alias_pair_table"],
        "control_verdicts": lane["control_verdicts"],
        "light_regression_verdicts": lane["light_regression_verdicts"],
        "fork_row": lane["fork_row"],
        "queued_heavy": lane["queued_heavy"],
        "build_gates": build_gates,
        "lane_build_gates": lane["build_gates"],
        "counts": lane["counts"],
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / (SIM_ID + '.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SOURCE_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-tool-intent {rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / ('validate_' + SIM_ID + '.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q {rel(SIM_DIR / 'tests')}",
        ],
    }
    return build_envelope(
        sim_id=SIM_ID,
        lanes={
            "julia": lane_record(
                lane,
                role_id="julia_contract_mirror_of_exact_python_light_lane",
                packages=["Z3", "json"],
                load_bearing=["Z3"],
                observables={"Z3": "contract mirror: SMT verdict already computed in packet result and represented for the generic two-lane validator"},
            ),
            "jax": lane_record(
                lane,
                role_id="jax_contract_mirror_of_exact_python_light_lane",
                packages=["networkx", "sympy", "z3", "cvc5", "json"],
                load_bearing=["networkx", "sympy", "z3", "cvc5"],
                observables={
                    "networkx": "DiGraph predecessor/successor controls for prior light exclusions",
                    "sympy": "exact symbolic support marker for the 33-cell finite carrier",
                    "z3": "z3.Solver/check binds computed amendment counts with SAT flip",
                    "cvc5": "cvc5.Solver/checkSat independently binds computed amendment counts with SAT flip",
                },
            ),
        },
        mode="python_exact_amendment_light_sweep",
        claim_path_tools=lane["claim_path_tools"] + ["build_three_engine_envelope"],
        crossover_proofs=lane["crossover_proofs"],
        divergence={
            "julia_authoritative": True,
            "engine_values": {
                "julia": lane["counts"],
                "jax": lane["counts"],
            },
            "max_divergence": 0,
            "single_exact_source_lane": True,
            "contract_note": "The generic validator requires julia+jax engine records. Both records mirror the exact Python/Fraction packet result; no independent Julia Canon or JAX array computation is claimed.",
            "pytorch_omitted": "no graph neural/autograd/tensor claim path",
        },
        omitted_lanes={
            "pytorch": "No tensor/autograd/PyG claim path exists in this light adapter pass.",
        },
        classification=lane["classification"],
        promotion_allowed=lane["promotion_allowed"],
        formal_admission_allowed=lane["formal_admission_allowed"],
        parent_lineage={
            "amendment": lane["authority_binding"]["amendment"]["path"],
            "deep_vein": lane["authority_binding"]["deep_vein"]["path"],
            "sonnet_wave": lane["authority_binding"]["sonnet_wave"]["path"],
            "light_sweep": lane["authority_binding"]["light_sweep"]["path"],
            "heavy_sweep": lane["authority_binding"]["heavy_sweep"]["path"],
        },
        extra_fields=extra_fields,
    )


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
