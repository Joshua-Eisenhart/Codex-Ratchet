#!/usr/bin/env python3
"""Packet-local validator for ecd02_chiral_information_routing_v1."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "ecd02_chiral_information_routing_v1"
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
    "builder_self_assessment.md",
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
    require(errors, payload.get("all_pass") is True, "all_pass must be true for the build/validator gates")
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

    gates = as_dict(payload.get("build_gates"), errors, "build_gates")
    for gate in (
        "two_bit_joint_state_test_computed",
        "equal_temperature_flux_test_computed",
        "real_mi_rows_computed",
        "fair_strongest_szilard_baseline_computed",
        "mirror_control_computed",
        "scrambled_schedule_control_computed",
        "no_identity_leak_check",
        "registry_contract_pass_or_candidate_dies",
        "no_builder_audit_verdict",
    ):
        require(errors, gates.get(gate) is True, f"build gate failed: {gate}")

    verdict = as_dict(payload.get("verdict"), errors, "verdict")
    require(errors, verdict.get("qit_engine_pass_computed") is True, "QIT candidate should pass its computed row")
    require(errors, verdict.get("strongest_szilard_baseline_fail_computed") is False, "strongest Szilard baseline should not be softened")
    require(errors, verdict.get("registry_contract_pass") is False, "registry contract should fail when Szilard does not fail")
    require(errors, verdict.get("ecd02_status") == "DIES", "ECD.02 must die under strongest baseline nonseparation")

    discovery = as_dict(payload.get("discovery"), errors, "discovery")
    flux = as_dict(discovery.get("computed_flux_by_engine"), errors, "computed_flux_by_engine")
    require(errors, flux.get("R_engine") == 1.0, "R computed current drift")
    require(errors, flux.get("L_engine") == -1.0, "L computed current drift")
    require(errors, abs(float(flux.get("scrambled_schedule_control", 1.0))) <= 1.0e-9, "scrambled control must kill current")

    mi_rows = as_dict(discovery.get("mutual_information_rows"), errors, "mutual_information_rows")
    require(errors, "signed_index" not in json.dumps(mi_rows), "MI rows must not condition on signed_index")
    require(errors, "chirality" not in json.dumps(mi_rows).lower(), "MI rows must not condition on chirality label")

    baseline = as_dict(payload.get("strongest_szilard_baseline"), errors, "strongest_szilard_baseline")
    require(errors, baseline.get("searched_policy_count") == 36, "baseline policy search count drift")
    require(errors, baseline.get("strongest_abs_directed_current") >= discovery.get("qit_abs_directed_current", 999), "baseline must match or exceed QIT current")

    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    for name in ("z3", "cvc5", "julia_z3"):
        proof = as_dict(proofs.get(name), errors, f"proofs.{name}")
        require(errors, proof.get("ran") is True, f"{name} did not run")
        require(errors, proof.get("load_bearing") is True, f"{name} not load-bearing")
        require(errors, proof.get("verdict") == "unsat", f"{name} expected unsat")

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
