#!/usr/bin/env python3
"""Packet-local validator for basin_generating_set_sweep_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SIM_ID = "basin_generating_set_sweep_v0"
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


def validate_leg(errors: list[str], name: str, payload: dict[str, Any]) -> None:
    require(errors, payload.get("sim_id") == SIM_ID, f"{name} sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", f"{name} classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, f"{name} promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, f"{name} formal_admission_allowed must be false")
    require(errors, payload.get("reads_peer_result") is False, f"{name} reads_peer_result must be false")
    require(errors, payload.get("all_pass") is True, f"{name} all_pass must be true")
    require(errors, bool(payload.get("packages_used")), f"{name} packages_used missing")
    require(errors, bool(payload.get("aligned_packages_load_bearing")), f"{name} aligned load-bearing packages missing")
    require(errors, payload.get("one_to_one_tool_calls", {}).get("pass") is True, f"{name} one-to-one tool calls failed")
    sweep = payload.get("sweep", {})
    require(errors, set(sweep) >= {"G0", "G1", "G2", "G3L", "G3R", "G4", "G5"}, f"{name} sweep rows missing")
    if "G0" in sweep:
        require(errors, sweep["G0"].get("terminal_class_count") == 1, f"{name} G0 terminal class count drift")
        require(errors, sweep["G0"].get("terminal_class_sizes") == [1], f"{name} G0 terminal size drift")
        require(errors, sweep["G0"].get("may_basin_sizes") == [33], f"{name} G0 may basin drift")
        require(errors, sweep["G0"].get("must_basin_sizes") == [1], f"{name} G0 must basin drift")
    if "G1" in sweep:
        require(errors, sweep["G1"].get("terminal_class_count") == 3, f"{name} G1 should split into three terminal classes")
    if "G2" in sweep:
        require(errors, sweep["G2"].get("terminal_class_count") == 1, f"{name} G2 should preserve one terminal class")
    for key in ("G3L", "G3R"):
        if key in sweep:
            require(errors, sweep[key].get("terminal_class_count") == 3, f"{name} {key} should split into three terminal classes")
            require(errors, sweep[key].get("terminal_class_sizes") == [1, 1, 6], f"{name} {key} terminal sizes drift")
    if "G4" in sweep:
        require(errors, sweep["G4"].get("state_count") == 4, f"{name} G4 conditioned state count drift")
        require(errors, sweep["G4"].get("terminal_class_count") == 1, f"{name} G4 terminal class count drift")
        require(errors, sweep["G4"].get("terminal_class_sizes") == [2], f"{name} G4 terminal size drift")
    if "G5" in sweep:
        require(errors, sweep["G5"].get("terminal_class_count") == 5, f"{name} G5 should split into five terminal classes")
        require(errors, sweep["G5"].get("terminal_class_sizes") == [1, 1, 1, 1, 3], f"{name} G5 terminal sizes drift")


def validate_envelope(errors: list[str], env: dict[str, Any], legs: dict[str, dict[str, Any]]) -> None:
    require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, env.get("sim_id") == SIM_ID, "envelope sim_id mismatch")
    require(errors, env.get("classification") == "scratch_diagnostic", "envelope classification mismatch")
    require(errors, env.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, env.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, env.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, set(env.get("engines", {})) == {"julia", "jax", "pytorch"}, "envelope must include all three engines")
    require(errors, env.get("ceiling") == "scratch_diagnostic", "ceiling mismatch")
    require(errors, env.get("sub_basin_answer", {}).get("any_second_terminal_class") is True, "sub-basin split answer missing")
    require(errors, env.get("engine_dof_reading", {}).get("generating_set_is_dof_choice") is True, "engine DoF reading missing")
    table = env.get("partition_fate_table", [])
    require(errors, len(table) == 7, "partition fate table must contain G0, G1, G2, G3L, G3R, G4, G5")
    by_id = {row.get("set_id"): row for row in table}
    require(errors, by_id.get("G0", {}).get("baseline_anchor_byte_exact") is True, "G0 byte-exact anchor failed")
    require(errors, by_id.get("G1", {}).get("fate") == "SPLITS", "G1 fate must be SPLITS")
    require(errors, by_id.get("G2", {}).get("fate") == "survives", "G2 fate must be survives")
    require(errors, by_id.get("G3L", {}).get("fate") == "SPLITS", "G3L fate must be SPLITS")
    require(errors, by_id.get("G3R", {}).get("fate") == "SPLITS", "G3R fate must be SPLITS")
    require(errors, by_id.get("G4", {}).get("fate") == "shrinks", "G4 fate must be shrinks")
    require(errors, by_id.get("G5", {}).get("fate") == "SPLITS", "G5 fate must be SPLITS")
    controls = env.get("controls", {})
    for set_id in ("G0", "G1", "G2", "G3L", "G3R", "G4", "G5"):
        row = controls.get(set_id, {})
        require(errors, "similarity_cluster_contrast" in row, f"{set_id} similarity contrast missing")
        require(errors, "root_off_contrast" in row, f"{set_id} root-off contrast missing")
    require(errors, controls.get("G5", {}).get("commutative_collapse_contrast", {}).get("computed") is True, "G5 commutative contrast missing")
    proofs = env.get("crossover_proofs", {})
    require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 identity proof must be unsat")
    require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 identity proof must be unsat")
    require(errors, proofs.get("z3", {}).get("erased_flip_verdict") == "sat", "z3 erased flip must be sat")
    require(errors, proofs.get("cvc5", {}).get("erased_flip_verdict") == "sat", "cvc5 erased flip must be sat")
    require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "Julia Z3 identity proof must be unsat")
    sig_hashes = {name: legs[name].get("sweep_signature_sha256") for name in ("julia", "jax", "pytorch")}
    require(errors, len(set(sig_hashes.values())) == 1, f"leg sweep signatures disagree: {sig_hashes}")


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
