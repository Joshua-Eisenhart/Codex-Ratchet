#!/usr/bin/env python3
"""Validate gcm_nested_geometry_delta_4q_v0."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from gcm_nested_geometry_delta_4q_v0_common import (
    ALTERNATE_PIN,
    ALTERNATE_PROBE,
    CLAIM_CEILING,
    CLASSIFICATION,
    ENVELOPE_PATH,
    RESULT_PATH,
    SIM_DIR,
    SIM_ID,
    VALIDATOR_RESULT_PATH,
    load_json,
    rel,
    write_json,
)


ROOT = SIM_DIR.parents[2]
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
REQUIRED_FILES = [
    SIM_DIR / "build_card.md",
    SIM_DIR / "builder_self_assessment.md",
    SIM_DIR / f"{SIM_ID}.py",
    SIM_DIR / f"{SIM_ID}_common.py",
    SIM_DIR / f"{SIM_ID}_boundary.py",
    SIM_DIR / f"{SIM_ID}_julia.jl",
    SIM_DIR / f"{SIM_ID}_jax.py",
    SIM_DIR / f"{SIM_ID}_pytorch.py",
    SIM_DIR / "write_envelope_spec.py",
    SIM_DIR / f"validate_{SIM_ID}.py",
    SIM_DIR / "tests" / f"test_{SIM_ID}.py",
    RESULT_PATH,
    ENVELOPE_PATH,
    SIM_DIR / "results" / f"{SIM_ID}_julia_results.json",
    SIM_DIR / "results" / f"{SIM_ID}_jax_results.json",
    SIM_DIR / "results" / f"{SIM_ID}_pytorch_results.json",
]


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def run_command(args: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return result.returncode, result.stdout, result.stderr


def validate_packet(packet: dict[str, Any], errors: list[str]) -> None:
    require(packet.get("sim_id") == SIM_ID, errors, "sim_id mismatch")
    require(packet.get("classification") == CLASSIFICATION, errors, "classification mismatch")
    require(packet.get("claim_ceiling") == CLAIM_CEILING, errors, "claim ceiling mismatch")
    require(packet.get("layer_declaration", {}).get("layer") == "nested-geometry-delta", errors, "layer declaration mismatch")
    require(packet.get("layer_declaration", {}).get("integration") == "integrated", errors, "integration declaration mismatch")
    require(packet.get("layer_declaration", {}).get("qubit_depth") == "4Q", errors, "depth declaration mismatch")
    require(packet.get("cut_state_available") is True, errors, "cut_state_available must be true")
    require(packet.get("blocked_consumer_enforced") is True, errors, "blocked_consumer_enforced must be true")
    delta = packet.get("geometry_delta_from_free", {})
    main = delta.get("main", {})
    flip = packet.get("flip_control_runs", {})
    stable_null = flip.get("same_input_stable_null", {})
    alt_pin = flip.get("alternate_registry_pin", {})
    alt_probe = flip.get("alternate_probe_family", {})
    require(main.get("free_count") == 554, errors, "main free count must be 554")
    require(main.get("nested_count") == 546, errors, "main nested count must be 546")
    require(float(main.get("delta_l1", 0.0)) > 0.0, errors, "main delta_l1 must be nonzero")
    null_control = packet.get("same_input_stability_control", {})
    require(stable_null.get("pin_name") == main.get("pin_name"), errors, "same-input null pin mismatch")
    require(stable_null.get("probe_family") == main.get("probe_family"), errors, "same-input null probe mismatch")
    require(null_control.get("stable") is True, errors, "same-input null control must be stable")
    require(float(null_control.get("null_delta_l1", 1.0)) <= 1.0e-12, errors, "same-input null delta_l1 must be <= 1e-12")
    require(null_control.get("pass") is True, errors, "same-input null control must pass")
    require(alt_pin.get("pin_name") == ALTERNATE_PIN, errors, "alternate pin name mismatch")
    require(alt_pin.get("nested_count", 0) > main.get("nested_count", 0), errors, "alternate pin did not add nested rows")
    require(alt_pin.get("delta_vector_sha256") != main.get("delta_vector_sha256"), errors, "alternate pin delta hash did not move")
    require(alt_probe.get("probe_family") == ALTERNATE_PROBE, errors, "alternate probe family mismatch")
    require(alt_probe.get("delta_vector_sha256") != main.get("delta_vector_sha256"), errors, "alternate probe delta hash did not move")
    require(packet.get("cross_pin_stability", {}).get("stable") is False, errors, "cross_pin_stability must be false")
    require(packet.get("cross_probe_stability", {}).get("stable") is False, errors, "cross_probe_stability must be false")
    require(packet.get("geometry_delta_stability_class") in {"pin_relative", "probe_relative"}, errors, "stability class must be relative")
    negative = packet.get("negative_control_status", {})
    require(negative.get("control") == "killed_candidate_count_delta", errors, "negative control mismatch")
    require(negative.get("pass") is True, errors, "negative control did not pass")
    require(packet.get("substrate_checks", {}).get("result", {}).get("ok") is True, errors, "substrate helper did not pass")
    require(packet.get("schema_check", {}).get("ok") is True, errors, "embedded schema check did not pass")
    roles = packet.get("engine_role_ceiling", {})
    require(roles.get("claim") == "no all-three-engine independence claim", errors, "engine independence ceiling claim mismatch")
    require(roles.get("julia", {}).get("depth") == "load_bearing", errors, "julia role must be load_bearing")
    require(roles.get("python_packet", {}).get("depth") == "load_bearing", errors, "python packet role must be load_bearing")
    require(roles.get("jax", {}).get("depth") == "supportive", errors, "jax role must be supportive")
    require(roles.get("pytorch", {}).get("depth") == "supportive", errors, "pytorch role must be supportive")
    depth = packet.get("TOOL_INTEGRATION_DEPTH", {})
    require(depth.get("z3") == "supportive", errors, "z3 must be supportive")
    require(depth.get("cvc5") == "supportive", errors, "cvc5 must be supportive")
    proofs = packet.get("crossover_proofs", {})
    require(proofs.get("z3", {}).get("load_bearing") is False, errors, "z3 crossover proof must not be load_bearing")
    require(proofs.get("cvc5", {}).get("load_bearing") is False, errors, "cvc5 crossover proof must not be load_bearing")


def validate_envelope(envelope: dict[str, Any], errors: list[str]) -> None:
    require(envelope.get("schema_version") == "three_engine_sim_result_v1", errors, "envelope schema_version mismatch")
    require(envelope.get("classification") == CLASSIFICATION, errors, "envelope classification mismatch")
    require(set(envelope.get("engines", {})) == {"julia", "jax", "pytorch"}, errors, "envelope engines mismatch")
    require(envelope.get("divergence", {}).get("max_divergence") == 0, errors, "engine divergence is nonzero")
    require(envelope.get("no_builder_audit_verdict") is True, errors, "no_builder_audit_verdict missing")
    require(envelope.get("engine_contract", {}).get("mode") == "julia_python_packet_geometry_with_supportive_jax_pytorch_guards", errors, "engine contract mode mismatch")
    roles = envelope.get("engine_role_ceiling", {})
    require(roles.get("claim") == "no all-three-engine independence claim", errors, "envelope engine independence ceiling missing")
    engines = envelope.get("engines", {})
    require(engines.get("julia", {}).get("claim_path_depth") == "load_bearing", errors, "julia envelope depth mismatch")
    require(engines.get("jax", {}).get("claim_path_depth") == "supportive", errors, "jax envelope depth mismatch")
    require(engines.get("pytorch", {}).get("claim_path_depth") == "supportive", errors, "pytorch envelope depth mismatch")
    require(envelope.get("same_input_stability_control", {}).get("stable") is True, errors, "envelope same-input null control must be stable")
    require(float(envelope.get("same_input_stability_control", {}).get("null_delta_l1", 1.0)) <= 1.0e-12, errors, "envelope same-input null delta_l1 must be <= 1e-12")
    depth = envelope.get("TOOL_INTEGRATION_DEPTH", {})
    require(depth.get("z3") == "supportive", errors, "envelope z3 must be supportive")
    require(depth.get("cvc5") == "supportive", errors, "envelope cvc5 must be supportive")
    require("z3" not in envelope.get("claim_path_tools", []), errors, "z3 must not be claim-bearing")
    require("cvc5" not in envelope.get("claim_path_tools", []), errors, "cvc5 must not be claim-bearing")
    proofs = envelope.get("crossover_proofs", {})
    require(proofs.get("z3", {}).get("load_bearing") is False, errors, "envelope z3 crossover proof must not be load_bearing")
    require(proofs.get("cvc5", {}).get("load_bearing") is False, errors, "envelope cvc5 crossover proof must not be load_bearing")


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        require(path.is_file(), errors, f"missing required file: {rel(path)}")
    packet = load_json(RESULT_PATH) if RESULT_PATH.is_file() else {}
    envelope = load_json(ENVELOPE_PATH) if ENVELOPE_PATH.is_file() else {}
    if packet:
        validate_packet(packet, errors)
    if envelope:
        validate_envelope(envelope, errors)

    schema_code, schema_stdout, schema_stderr = run_command([SIM_PY, "scripts/gcm_nested_schema_check.py", rel(RESULT_PATH)])
    require(schema_code == 0, errors, f"nested schema check failed: {schema_stdout}{schema_stderr}")

    from builder_audit_boundary import builder_audit_boundary_errors

    errors.extend(builder_audit_boundary_errors(envelope, SIM_DIR / "audit_verdict.md"))
    result = {
        "ok": not errors,
        "sim_id": SIM_ID,
        "result_path": rel(RESULT_PATH),
        "envelope_path": rel(ENVELOPE_PATH),
        "errors": errors,
    }
    write_json(VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
