#!/usr/bin/env python3
"""Packet-local validator for ecd02_chiral_information_routing_v0."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "ecd02_chiral_information_routing_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
DEFAULT_RESULT = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"
REQUIRED_FILES = [
    "build_card.md",
    f"{SIM_ID}_common.py",
    f"{SIM_ID}_julia.jl",
    f"{SIM_ID}_jax.py",
    f"{SIM_ID}_pytorch.py",
    f"{SIM_ID}_envelope.py",
    f"validate_{SIM_ID}.py",
    f"tests/test_{SIM_ID}.py",
]

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from scripts.validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, errors: list[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for file_name in REQUIRED_FILES:
        require(errors, (SIM_DIR / file_name).is_file(), f"missing packet file: {file_name}")

    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == "capability_discriminator_only", "claim ceiling drift")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    require(errors, payload.get("no_builder_audit_verdict") is True, "builder must not write audit verdict")

    errors.extend(
        f"generic three-engine validator: {error}"
        for error in validate_three_engine(
            payload,
            require_pytorch=True,
            strict_source_backed=True,
            require_tool_intent=True,
        )
    )

    engines = as_dict(payload.get("engines"), errors, "engines")
    require(errors, set(engines) == {"julia", "jax", "pytorch"}, "all three engine lanes required")
    for name, engine in engines.items():
        row = as_dict(engine, errors, f"engines.{name}")
        require(errors, row.get("ran") is True, f"{name}.ran must be true")
        require(errors, row.get("reads_peer_result") is False, f"{name}.reads_peer_result must be false")
        require(errors, bool(row.get("aligned_packages_load_bearing")), f"{name}.aligned packages missing")

    values = as_dict(payload.get("engine_values"), errors, "engine_values")
    require(errors, values.get("L_index") == -1, "L index must be -1")
    require(errors, values.get("R_index") == 1, "R index must be +1")
    require(errors, values.get("index0") == 0, "index0 must be 0")
    require(errors, values.get("R_routing_asymmetry") == 1.0, "R routing asymmetry drift")
    require(errors, values.get("L_routing_asymmetry") == -1.0, "L routing asymmetry drift")
    require(errors, values.get("szilard_routing_asymmetry") == 0.0, "Szilard baseline must be symmetric")

    routing = as_dict(payload.get("routing"), errors, "routing")
    diode = as_dict(routing.get("diode_row"), errors, "routing.diode_row")
    mirror = as_dict(routing.get("mirror_diode_row"), errors, "routing.mirror_diode_row")
    require(errors, diode.get("diode_pass") is True, "R diode row must pass")
    require(errors, mirror.get("mirror_pass") is True, "L mirror diode row must pass")

    controls = as_dict(payload.get("controls"), errors, "controls")
    for gate in (
        "index_sign_predicts_routing_direction",
        "szilard_baseline_fails",
        "index0_symmetric",
        "diode_pass",
        "mirror_pass",
        "swapped_chirality_mirror_flips_direction",
        "falsifier_reachable_and_kills_original_R_direction",
    ):
        require(errors, controls.get(gate) is True, f"control failed: {gate}")

    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    for name in ("z3", "cvc5", "julia_z3"):
        proof = as_dict(proofs.get(name), errors, f"proofs.{name}")
        require(errors, proof.get("ran") is True, f"{name} did not run")
        require(errors, proof.get("load_bearing") is True, f"{name} not load-bearing")
        require(errors, proof.get("verdict") == "unsat", f"{name} expected unsat")
    gates = as_dict(payload.get("build_gates"), errors, "build_gates")
    for key, value in gates.items():
        require(errors, value is True, f"build gate failed: {key}")
    return errors


def main() -> int:
    payload = json.loads(DEFAULT_RESULT.read_text(encoding="utf-8"))
    errors = validate(payload)
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    result = {
        "ok": not errors,
        "errors": errors,
        "result_json": rel(DEFAULT_RESULT),
        "validator": rel(Path(__file__)),
    }
    VALIDATOR_RESULT.parent.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
