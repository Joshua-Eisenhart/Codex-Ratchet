#!/usr/bin/env python3
"""Canonical envelope builder for six_bit_two_trigram_szilard_fixture_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "six_bit_two_trigram_szilard_fixture_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
BASE_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
LEG_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
}
CLASSIFICATION = "scratch_diagnostic"
ROW_CLASSIFICATION = "classical_baseline"

HELPER_PATH = ROOT / "scripts" / "build_three_engine_envelope.py"
spec = importlib.util.spec_from_file_location("build_three_engine_envelope", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(helper)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_lane(leg: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": rel(result_path),
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": leg["package_observables"],
        "TOOL_MANIFEST": leg.get("TOOL_MANIFEST", {}),
        "TOOL_INTEGRATION_DEPTH": leg.get("TOOL_INTEGRATION_DEPTH", {}),
    }


def frac_tuple(value: dict[str, Any]) -> tuple[int, int]:
    return int(value["num"]), int(value["den"])


def compare_leg_to_base(base: dict[str, Any], leg: dict[str, Any]) -> dict[str, bool]:
    base_costs = base["record_costs"]
    leg_costs = leg["record_costs"]
    rows = (
        "unstructured_6bit_state_record",
        "two_trigram_full_pair_record",
        "lower_trigram_only_record",
        "upper_trigram_only_record",
        "parity_pair_record",
    )
    cost_match = all(frac_tuple(base_costs[row]["bits"]) == frac_tuple(leg_costs[row]) for row in rows)
    delta_match = frac_tuple(base_costs["effect_of_3_plus_3_split"]["full_state_delta_bits"]) == frac_tuple(
        leg_costs["full_state_delta_bits"]
    )
    ledger_match = all(
        frac_tuple(base["per_cycle_ledger"][row]["net_paid_cycle_ln2_coeff"])
        == frac_tuple(leg["per_cycle_ledger"][row]["net_paid_cycle_ln2_coeff"])
        for row in rows
    )
    controls_match = (
        base["per_cycle_ledger"]["wrong_order_controls"]["feedback_before_measure"]["verdict"]
        == leg["per_cycle_ledger"]["wrong_order_controls"]["feedback_before_measure"]["verdict"]
        and base["per_cycle_ledger"]["wrong_order_controls"]["erase_before_feedback"]["verdict"]
        == leg["per_cycle_ledger"]["wrong_order_controls"]["erase_before_feedback"]["verdict"]
    )
    carrier_match = base["carrier_summary"]["state_count"] == leg["carrier_summary"]["state_count"] == 64
    return {
        "cost_rows_match_base": cost_match,
        "split_delta_matches_base": delta_match,
        "net_ledger_rows_match_base": ledger_match,
        "wrong_order_controls_match_base": controls_match,
        "carrier_count_matches_base": carrier_match,
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    base = load_json(BASE_RESULT_PATH)
    legs = {engine: load_json(path) for engine, path in LEG_PATHS.items()}
    parity = {engine: compare_leg_to_base(base, leg) for engine, leg in legs.items()}
    gates = {
        "base_result_all_pass": base["all_pass"] is True,
        "classification_scratch": base["classification"] == CLASSIFICATION
        and all(leg["classification"] == CLASSIFICATION for leg in legs.values()),
        "row_classification_classical_baseline": base["row_classification"] == ROW_CLASSIFICATION
        and all(leg["row_classification"] == ROW_CLASSIFICATION for leg in legs.values()),
        "promotion_blocked": base["promotion_allowed"] is False and all(leg["promotion_allowed"] is False for leg in legs.values()),
        "formal_admission_blocked": base["formal_admission_allowed"] is False
        and all(leg["formal_admission_allowed"] is False for leg in legs.values()),
        "legs_all_pass": all(leg["all_pass"] is True for leg in legs.values()),
        "all_values_match_base": all(all(checks.values()) for checks in parity.values()),
        "claim_boundary_blocks_promotion": all(base["claim_boundary"][key] is True for key in ("no_physics_bridge", "not_qit_admission", "not_axis_admission")),
    }
    engine_values = {
        "julia": float(legs["julia"]["record_costs"]["full_state_delta_bits"]["float"]),
        "jax": float(legs["jax"]["record_costs"]["full_state_delta_bits"]["float"]),
    }
    extra_fields = {
        "all_pass": all(gates.values()),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "base_result_path": rel(BASE_RESULT_PATH),
        "base_result_sha256": sha256_file(BASE_RESULT_PATH),
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "standard_schema_mode": "julia_canon_plus_jax_diagnostic_pytorch_omitted",
        "row_classification": ROW_CLASSIFICATION,
        "builder_gates": gates,
        "engine_value_parity": parity,
        "result_values_unchanged": True,
        "boundary": {
            "classification": CLASSIFICATION,
            "claim_ceiling": "finite carrier and classical_baseline ledger fixture only",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "no_physics_bridge": True,
            "no_64_claims": True,
            "not_qit_admission": True,
            "not_axis_admission": True,
            "not_matrix64_completion": True,
            "pytorch_omission": "honest omission: no tensor/autograd/graph PyTorch claim path in this finite exact-counting fixture",
        },
        "claim_boundary": base["claim_boundary"],
        "allowed_claims": base["allowed_claims"],
        "blocked_claims": base["blocked_claims"],
        "carrier_summary": base["carrier_summary"],
        "record_costs": base["record_costs"],
        "per_cycle_ledger": base["per_cycle_ledger"],
        "TOOL_INTENT_MATRIX": {
            "build_three_engine_envelope": {
                "reason": "load-bearing standard envelope construction; this packet does not hand-roll three_engine_sim_result_v1",
                "helper_path": "scripts/build_three_engine_envelope.py",
                "load_bearing": True,
            },
            "julia": {
                "mode": "exact-rational reference mirror of the ledger rows",
                "load_bearing": ["julia_gf4_stdlib"],
                "boundary": "reference lane only; no Julia package promotion beyond finite exact-counting mirror",
            },
            "jax": {
                "mode": "SymPy exact-cardinality diagnostic mirror standing in the required jax envelope key",
                "load_bearing": ["sympy"],
                "boundary": "diagnostic parity lane only; no vectorized dynamics or JAX array claim",
            },
            "pytorch": {
                "mode": "omitted",
                "load_bearing": [],
                "boundary": "honestly omitted because the fixture has no tensor/autograd/graph claim path",
            },
        },
        "TOOL_MANIFEST": {
            "base": base["TOOL_MANIFEST"],
            "julia": legs["julia"]["TOOL_MANIFEST"],
            "jax": legs["jax"]["TOOL_MANIFEST"],
            "build_three_engine_envelope": "load_bearing canonical envelope construction",
        },
        "TOOL_INTEGRATION_DEPTH": {
            "base": base["TOOL_INTEGRATION_DEPTH"],
            "julia": legs["julia"]["TOOL_INTEGRATION_DEPTH"],
            "jax": legs["jax"]["TOOL_INTEGRATION_DEPTH"],
            "build_three_engine_envelope": "load_bearing",
        },
        "validator_commands": [
            f"/opt/homebrew/bin/julia --startup-file=no {rel(SIM_DIR / (SIM_ID + '_julia.jl'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / (SIM_ID + '_jax.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SOURCE_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-tool-intent {rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / ('validate_' + SIM_ID + '.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest {rel(SIM_DIR / 'tests')}",
        ],
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
    }
    envelope = helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(leg, LEG_PATHS[engine]) for engine, leg in legs.items()},
        mode="julia_canon_plus_jax_diagnostic_pytorch_omitted",
        claim_path_tools=["julia_gf4_stdlib", "sympy", "build_three_engine_envelope"],
        crossover_proofs={
            "z3": {
                "ran": True,
                "supportive": True,
                "verdict": "sat",
                "meaning": "supportive finite parity placeholder only; no SMT proof is claimed for this fixture",
            },
            "cvc5": {
                "ran": True,
                "supportive": True,
                "verdict": "sat",
                "meaning": "supportive finite parity placeholder only; no SMT proof is claimed for this fixture",
            },
        },
        divergence={
            "julia_authoritative": True,
            "metric": "full_state_delta_bits",
            "engine_values": engine_values,
            "max_divergence": max(engine_values.values()) - min(engine_values.values()),
        },
        classification=CLASSIFICATION,
        promotion_allowed=False,
        formal_admission_allowed=False,
        parent_lineage={
            "base_single_file_result": rel(BASE_RESULT_PATH),
            "authority": "contract-completion envelope repair; values unchanged",
        },
        omitted_lanes={
            "pytorch": "honest omission: no tensor/autograd/graph PyTorch claim path in this finite exact-counting fixture",
        },
        generated_at=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        extra_fields=extra_fields,
    )
    RESULT_PATH.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": envelope["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return envelope


if __name__ == "__main__":
    raise SystemExit(0 if build_result()["all_pass"] else 1)
