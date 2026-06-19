#!/usr/bin/env python3
"""Packet-local validator for basin_grid_refinement_control_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SIM_ID = "basin_grid_refinement_control_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
    "envelope": RESULT_DIR / f"{SIM_ID}_envelope_results.json",
}
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def scan_for_forbidden_word(errors: list[str]) -> None:
    forbidden = "fix" + "ture"
    for path in SIM_DIR.rglob("*"):
        if "__pycache__" in path.parts:
            continue
        if not path.is_file() or path.name == f"{SIM_ID}_validator_results.json":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if forbidden in text:
            errors.append(f"forbidden wording appears in {rel(path)}")


def key_summary(payload: dict[str, Any]) -> dict[str, Any]:
    table = payload["persistence_table"]
    return {
        "refinement": [
            {
                "state_count": row["state_count"],
                "terminal_class_count": row["terminal_class_count"],
                "overall_fate": row["persistence"]["overall_fate"],
                "class_fates": {
                    key: value["fate"]
                    for key, value in sorted(row["persistence"]["committed_class_fates"].items())
                },
            }
            for row in table["refinement"]
        ],
        "rotated_terminal_class_count": table["rotated_grid"]["terminal_class_count"],
        "rotated_overall_fate": table["rotated_grid"]["persistence"]["overall_fate"],
        "rotated_class_fates": {
            key: value["fate"]
            for key, value in sorted(table["rotated_grid"]["persistence"]["committed_class_fates"].items())
        },
        "g0_counts": [row["terminal_class_count"] for row in table["g0_dissipative_refined_control"]],
        "axis_artifact": table["axis_artifact_control"]["dies_under_rotation"],
    }


def validate_leg(errors: list[str], name: str, payload: dict[str, Any]) -> None:
    require(errors, payload.get("sim_id") == SIM_ID, f"{name} sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", f"{name} classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, f"{name} promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, f"{name} formal_admission_allowed must be false")
    require(errors, payload.get("reads_peer_result") is False, f"{name} reads_peer_result must be false")
    require(errors, payload.get("all_pass") is True, f"{name} all_pass must be true")
    require(errors, bool(payload.get("packages_used")), f"{name} packages_used missing")
    require(errors, bool(payload.get("aligned_packages_load_bearing")), f"{name} load-bearing packages missing")
    require(errors, payload.get("one_to_one_tool_calls", {}).get("pass") is True, f"{name} one-to-one tool calls failed")
    table = payload.get("persistence_table", {})
    require(errors, len(table.get("refinement", [])) == 2, f"{name} must include 2x and 3x refinement rows")
    if table.get("refinement"):
        require(errors, table["refinement"][0].get("state_count") == 66, f"{name} 2x cell count drift")
        require(errors, table["refinement"][0].get("persistence", {}).get("overall_fate") == "PERSIST", f"{name} 2x should persist")
        require(errors, table["refinement"][1].get("state_count") == 99, f"{name} 3x cell count drift")
        require(errors, table["refinement"][1].get("persistence", {}).get("overall_fate") == "PERSIST", f"{name} 3x should persist")
    rotated = table.get("rotated_grid", {})
    require(errors, rotated.get("state_count") == 33, f"{name} rotated grid cell count drift")
    require(errors, rotated.get("persistence", {}).get("overall_fate") == "CHANGED", f"{name} rotated grid should change classes")
    require(errors, rotated.get("terminal_class_count") == 2, f"{name} rotated grid terminal count drift")
    require(errors, all(row.get("stays_one_class") is True for row in table.get("g0_dissipative_refined_control", [])), f"{name} G0 refined control failed")
    require(errors, table.get("axis_artifact_control", {}).get("dies_under_rotation") is True, f"{name} axis artifact did not die")


def validate_envelope(errors: list[str], env: dict[str, Any], legs: dict[str, dict[str, Any]]) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "envelope sim_id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "envelope classification mismatch")
    require(errors, env.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, env.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, set(env.get("engines", {})) == {"julia", "jax", "pytorch"}, "envelope must include all three engines")
    require(errors, env.get("ceiling") == "scratch_diagnostic", "ceiling mismatch")
    require(errors, env.get("grid_declaration", {}).get("refined_cell_counts") == {"2x": 66, "3x": 99}, "refined cell counts mismatch")
    gates = env.get("build_gates", {})
    for gate in (
        "g1_anchor_byte_exact",
        "refined_2x_persists",
        "refined_3x_persists",
        "rotated_grid_changes_classes",
        "g0_refined_stays_one_class",
        "axis_artifact_dies",
        "continuous_closure_so3",
        "source_backed_lanes_present",
    ):
        require(errors, gates.get(gate) is True, f"build gate failed: {gate}")
    proofs = env.get("crossover_proofs", {})
    require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 identity proof must be unsat")
    require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 identity proof must be unsat")
    require(errors, proofs.get("z3", {}).get("erased_flip_verdict") == "sat", "z3 erased flip must be sat")
    require(errors, proofs.get("cvc5", {}).get("erased_flip_verdict") == "sat", "cvc5 erased flip must be sat")
    require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "Julia Z3 proof must be unsat")
    summaries = {name: key_summary(legs[name]) for name in ("julia", "jax", "pytorch")}
    require(errors, summaries["julia"] == summaries["jax"] == summaries["pytorch"], "engine key fate summaries disagree")
    require(errors, env.get("c1_answer", {}).get("promotion_allowed") is False, "C1 answer must preserve promotion block")


def main() -> int:
    errors: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for name, path in RESULT_PATHS.items():
        if not path.exists():
            errors.append(f"missing result {rel(path)}")
            continue
        payloads[name] = load(path)
    for name in ("julia", "jax", "pytorch"):
        if name in payloads:
            validate_leg(errors, name, payloads[name])
    if "envelope" in payloads and all(name in payloads for name in ("julia", "jax", "pytorch")):
        validate_envelope(errors, payloads["envelope"], payloads)
    scan_for_forbidden_word(errors)
    result = {
        "ok": not errors,
        "errors": errors,
        "result_json": rel(RESULT_PATHS["envelope"]),
        "validator": rel(Path(__file__).resolve()),
    }
    write_json(VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
