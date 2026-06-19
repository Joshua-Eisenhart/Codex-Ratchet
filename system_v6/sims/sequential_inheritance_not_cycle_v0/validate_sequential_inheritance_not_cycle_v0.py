#!/usr/bin/env python3
"""Packet validator for sequential_inheritance_not_cycle_v0."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SIM_ID = "sequential_inheritance_not_cycle_v0"
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

    require(payload.get("schema_version") == "three_engine_sim_result_v1", errors, "schema version mismatch")
    require(payload.get("sim_id") == SIM_ID, errors, "sim_id mismatch")
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification mismatch")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")
    require(set(payload.get("engines", {})) == {"julia", "jax", "pytorch"}, errors, "all three engines required")

    parent_rows = payload.get("parent_terminal_table")
    require(isinstance(parent_rows, list) and len(parent_rows) == 24, errors, "parent terminal table must have 24 rows")
    record = as_dict(payload.get("record_convention"), errors, "record_convention")
    require(record.get("standard") == "z4_syndrome_record_v0_packet_local_convention", errors, "wrong Z4 record standard")
    require(record.get("record_is_not_loss_assignment") is True, errors, "record must not be assigned as loss")
    require(as_dict(record.get("syndrome_entropy"), errors, "record.syndrome_entropy").get("entropy_log2_coefficient") == 2, errors, "record entropy must be two Z4 bits")

    regimes = as_dict(payload.get("regimes"), errors, "regimes")
    inherited = as_dict(regimes.get("inheritance"), errors, "regimes.inheritance")
    cycle = as_dict(regimes.get("cycle_null"), errors, "regimes.cycle_null")
    random = as_dict(regimes.get("random_null"), errors, "regimes.random_null")
    require(inherited.get("terminal_structure_match_count") == 24, errors, "inheritance must match 24/24 parent terminal structures")
    require(cycle.get("terminal_structure_match_count") == 0, errors, "cycle-null must match 0/24")
    require(random.get("terminal_structure_match_count") == 6, errors, "random-null must match 6/24")
    require(inherited.get("mean_stability_score") == 1.0, errors, "inheritance stability must be 1.0")
    require(cycle.get("mean_stability_score") == 0.0, errors, "cycle-null stability must be 0.0")
    require(random.get("mean_stability_score") == 0.25, errors, "random-null stability must be 0.25")

    discriminator = as_dict(payload.get("discriminator"), errors, "discriminator")
    require(discriminator.get("all_regime_signatures_distinct") is True, errors, "regime signatures must be distinct")
    require(discriminator.get("inheritance_gt_cycle_stability") is True, errors, "inheritance must beat cycle-null")
    require(discriminator.get("inheritance_gt_random_stability") is True, errors, "inheritance must beat random-null")
    require(discriminator.get("cycle_null_distinct_from_random_null") is True, errors, "cycle-null and random-null must be distinct")
    require(discriminator.get("reported_if_no_teeth") is False, errors, "discriminator has no teeth")

    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    for name in ["z3", "cvc5", "julia_z3"]:
        require(as_dict(proofs.get(name), errors, f"proofs.{name}").get("verdict") == "unsat", errors, f"{name} inheritance proof must be unsat")

    require("tool_intent" in payload, errors, "tool_intent payload missing")
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
