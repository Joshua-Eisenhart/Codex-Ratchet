#!/usr/bin/env python3
"""Code-only controller: execute sealed lanes, compare closed receipts, authorize or HOLD."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parents[2]
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = Path(__file__).resolve()
PYTHON = Path(os.environ.get("CODEX_RATCHET_PYTHON", "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"))
JULIA = Path(os.environ.get("CODEX_RATCHET_JULIA", "/opt/homebrew/bin/julia"))
JULIA_PROJECT = Path(
    os.environ.get("CODEX_RATCHET_JULIA_PROJECT", "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run(label: str, command: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False, env=env)
    return {
        "label": label,
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "pass": proc.returncode == 0,
    }


def expected_controls() -> dict[str, Any]:
    return {
        "reverse_drive": -1,
        "reverse_decision": "HOLD",
        "null_drive": 0,
        "null_decision": "HOLD",
        "universal_proposal_drive": 0,
        "universal_proposal_decision": "HOLD",
        "scrambled_drive": 0,
        "scrambled_decision": "HOLD",
        "flat_drive": 0,
        "flat_decision": "HOLD",
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["JULIA_LOAD_PATH"] = "@:@stdlib"
    env["CODEX_RATCHET_JULIA_PROJECT"] = str(JULIA_PROJECT)
    commands = [
        run("preregistration", [str(PYTHON), "-B", str(SIM_DIR / "validate_preregistration.py")], env),
        run("runtime_doctor", [str(PYTHON), "-B", str(ROOT / "scripts/codex_runtime_env_doctor.py")], env),
        run("julia", [str(JULIA), "--startup-file=no", f"--project={JULIA_PROJECT}", str(SIM_DIR / "run_julia.jl")], env),
        run("jax", [str(PYTHON), "-B", str(SIM_DIR / "run_jax.py")], env),
        run("pytorch", [str(PYTHON), "-B", str(SIM_DIR / "run_pytorch.py")], env),
        run("dual_smt", [str(PYTHON), "-B", str(SIM_DIR / "run_proofs.py")], env),
    ]
    result_paths = {
        "julia": RESULT_DIR / "julia_results.json",
        "jax": RESULT_DIR / "jax_results.json",
        "pytorch": RESULT_DIR / "pytorch_results.json",
        "proof": RESULT_DIR / "proof_results.json",
    }
    payloads = {name: load(path) for name, path in result_paths.items() if path.is_file()}
    spec = load(SIM_DIR / "spec.json")
    prereg = load(SIM_DIR / "preregistration_receipt.json")
    expected_census = spec["root_contract"]["expected_census"]
    engines_present = all(name in payloads for name in ("julia", "jax", "pytorch", "proof"))
    engine_payloads = [payloads.get(name, {}) for name in ("julia", "jax", "pytorch")]
    census_match = engines_present and all(payload.get("census") == expected_census for payload in engine_payloads)
    witness_match = engines_present and len(
        {json.dumps(payload.get("transitivity_witness"), sort_keys=True) for payload in engine_payloads}
    ) == 1
    drive_match = engines_present and len(
        {json.dumps(payload.get("drive_fixture"), sort_keys=True) for payload in engine_payloads}
    ) == 1
    source_bindings = {}
    for name, payload in payloads.items():
        source = ROOT / payload.get("source_path", "missing")
        source_bindings[name] = {
            "source_exists": source.is_file(),
            "source_path": payload.get("source_path"),
            "source_sha256": payload.get("source_sha256"),
            "source_hash_match": source.is_file() and sha256(source) == payload.get("source_sha256"),
            "result_path": str(result_paths[name].relative_to(ROOT)),
            "result_sha256": sha256(result_paths[name]),
        }
    proof = payloads.get("proof", {})
    expected_proof = proof.get("expected")
    proof_pass = bool(
        expected_proof
        and proof.get("z3", {}).get("queries") == expected_proof
        and proof.get("cvc5", {}).get("queries") == expected_proof
        and proof.get("free_boolean_relation_variables") is True
        and proof.get("ground_literal_only") is False
    )
    representative = payloads.get("julia", {}).get("drive_fixture", {})
    controls_pass = representative.get("controls") == expected_controls()
    mss = representative.get("mss_antichain", [])
    mss_pass = mss == [
        {"labels": [0, 0, 1, 1], "added_pair_count": 0, "quotient_class_count": 2},
        {"labels": [0, 0, 0, 0], "added_pair_count": 4, "quotient_class_count": 1},
    ]
    checks = {
        "G0_preregistered_object": commands[0]["pass"] and prereg["spec_sha256"] == sha256(SIM_DIR / "spec.json"),
        "G1_exact_census": census_match,
        "G2_three_engine_closure_parity": witness_match and drive_match,
        "G3_dual_smt": proof_pass,
        "G4_coface_drive": representative.get("initial_coface_loss") == 1 and representative.get("proposal_coface_loss") == 0 and representative.get("drive") == 1,
        "G5_tooth_and_hold_controls": representative.get("decision") == "COMMIT_TOOTH" and controls_pass,
        "G6_plural_mss": mss_pass and len(mss) == 2,
        "G7_closed_engine_lanes": engines_present and all(payload.get("reads_peer_result") is False for payload in payloads.values()),
        "G8_source_runtime_ceiling_binding": commands[1]["pass"] and all(item["source_hash_match"] for item in source_bindings.values()) and all(payload.get("classification") == "scratch_diagnostic" and payload.get("promotion_allowed") is False and payload.get("formal_admission_allowed") is False and payload.get("all_pass") is True for payload in payloads.values()),
    }
    all_pass = all(command["pass"] for command in commands) and all(checks.values())
    decision = "COMMIT_TOOTH_CANDIDATE" if all_pass else "HOLD"
    envelope = {
        "schema": "codex_ratchet.tolerance_to_equivalence.controller_envelope.v1",
        "sim_id": spec["sim_id"],
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "llm_verdict_used": False,
        "controller_source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "controller_source_sha256": sha256(SOURCE_PATH),
        "python_executable": sys.executable,
        "julia_executable": str(JULIA),
        "julia_project": str(JULIA_PROJECT),
        "commands": commands,
        "checks": checks,
        "source_bindings": source_bindings,
        "engines": {name: {"payload": payloads[name], **source_bindings[name]} for name in payloads},
        "divergence": {
            "census_match": census_match,
            "witness_match": witness_match,
            "drive_match": drive_match,
            "max_numeric_divergence": 0 if census_match and drive_match else 1,
        },
        "proof_contract": {"expected": expected_proof, "pass": proof_pass},
        "drive": representative,
        "mss_antichain": mss,
        "all_pass": all_pass,
        "decision": decision,
        "ratchet_state_before": "OPEN",
        "ratchet_state_after": "TOOTH_1_CANDIDATE" if all_pass else "HOLD",
        "claim_ceiling": spec["accepted_green_ceiling"] if all_pass else spec["accepted_red_ceiling"],
        "blocked_consumers": spec["blocked_consumers"],
        "pending_gates": ["G9 independent mutation rejection", "G10 deterministic Lev replay"],
    }
    envelope_path = RESULT_DIR / "controller_envelope.json"
    envelope_path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"TOLERANCE_RUNG_CONTROLLER_DONE all_pass={str(all_pass).lower()} decision={decision} envelope={envelope_path}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
