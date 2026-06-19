#!/usr/bin/env python3
"""Packet-local builder validator for s8_local_information_table_v0."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from s8_local_information_table_v0_common import (
    PACKET,
    RESULT_DIR,
    ROOT,
    SIM_ID,
    build_packet_payload,
    rel,
    stable_hash,
    write_json,
)


ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"
sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402

STRICT_COMMAND = [
    sys.executable,
    str(ROOT / "scripts" / "validate_three_engine_sim_result.py"),
    "--require-pytorch",
    "--strict-source-backed",
    "--require-tool-intent",
    str(ENVELOPE),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_packet(phase: str) -> dict[str, Any]:
    errors: list[str] = []
    packet = build_packet_payload("validator")
    require(errors, phase in {"builder", "final"}, "phase must be builder or final")
    require(errors, (PACKET / "build_card.md").is_file(), "build_card.md is required")
    require(errors, packet["classification"] == "scratch_diagnostic", "classification must be scratch_diagnostic")
    require(errors, packet["promotion_allowed"] is False, "promotion_allowed must be false")
    require(errors, packet["formal_admission_allowed"] is False, "formal_admission_allowed must be false")
    require(errors, packet["continuity_anchors"]["nested_ratchet"]["all_match"] is True, "nested-ratchet anchors must match")
    require(
        errors,
        packet["continuity_anchors"]["dual_stack"]["Phi0_Ic_S_to_M"]["all_match"] is True,
        "dual-stack Phi0 I_c anchor must match",
    )
    require(errors, packet["controls"]["separable_state_control"]["pass"] is True, "separable-state control must pass")
    require(errors, packet["controls"]["entangled_positive_case"]["pass"] is True, "entangled positive control must pass")
    require(errors, packet["controls"]["erased_channel_Ic_flip"]["pass"] is True, "erasure I_c flip control must pass")
    require(errors, packet["controls"]["typed_confusion_rejection"]["pass"] is True, "typed-confusion rejection must pass")
    require(errors, len(packet["local_information_table"]["rows"]) >= 60, "local information table must include all declared state/bipartition rows")

    legs = {}
    for engine in ("julia", "jax", "pytorch"):
        path = RESULT_DIR / f"{SIM_ID}_{engine}_results.json"
        require(errors, path.is_file(), f"{engine} result is missing")
        if path.is_file():
            legs[engine] = load_json(path)
            require(errors, legs[engine].get("all_pass") is True, f"{engine} all_pass must be true")
            require(errors, legs[engine].get("reads_peer_result") is False, f"{engine} must not read peer result")

    envelope: dict[str, Any] | None = None
    if ENVELOPE.is_file():
        envelope = load_json(ENVELOPE)
        errors.extend(builder_audit_boundary_errors(envelope, PACKET / "audit_verdict.md"))
        require(errors, envelope.get("schema_version") == "three_engine_sim_result_v1", "envelope schema_version mismatch")
        require(errors, envelope.get("sim_id") == SIM_ID, "envelope sim_id mismatch")
        require(errors, envelope.get("classification") == "scratch_diagnostic", "envelope classification mismatch")
        require(errors, envelope.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
        require(errors, envelope.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
        require(errors, envelope.get("all_pass") is True, "envelope all_pass must be true")
        require(errors, envelope.get("no_builder_audit_verdict") is True, "envelope no_builder_audit_verdict gate missing")
        require(errors, envelope.get("builder_gates", {}).get("no_builder_audit_verdict") is True, "builder gate missing")
        require(errors, set(envelope.get("engines", {})) == {"julia", "jax", "pytorch"}, "envelope must have all three engines")
        require(errors, envelope.get("table_hash") == stable_hash(packet["local_information_table"]), "table hash drift")
        require(errors, envelope.get("controls_hash") == stable_hash(packet["controls"]), "controls hash drift")
    else:
        errors.append("envelope result is missing")

    strict = subprocess.run(STRICT_COMMAND, cwd=ROOT, text=True, capture_output=True)
    if strict.returncode != 0:
        errors.append("strict three-engine validator failed")

    result = {
        "schema": f"{SIM_ID}_validator_v1",
        "sim_id": SIM_ID,
        "phase": phase,
        "ok": not errors,
        "errors": errors,
        "packet_path": rel(PACKET),
        "envelope_path": rel(ENVELOPE),
        "strict_three_engine_validator": {
            "command": " ".join(STRICT_COMMAND),
            "returncode": strict.returncode,
            "stdout": strict.stdout.strip(),
            "stderr": strict.stderr.strip(),
        },
        "table_hash": stable_hash(packet["local_information_table"]),
        "controls_hash": stable_hash(packet["controls"]),
        "envelope_all_pass": envelope.get("all_pass") if envelope else None,
    }
    write_json(VALIDATOR_RESULT, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["builder", "final"], default="builder")
    args = parser.parse_args()
    result = validate_packet(args.phase)
    print(json.dumps({"ok": result["ok"], "result_path": rel(VALIDATOR_RESULT), "errors": result["errors"]}, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
