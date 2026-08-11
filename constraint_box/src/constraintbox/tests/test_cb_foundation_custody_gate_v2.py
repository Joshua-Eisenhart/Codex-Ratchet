#!/usr/bin/env python3
"""Regression test for the CB foundation custody gate's real boundaries."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent.parent
SOURCE = HERE / "source"
# Try to find modules; if running from repo, look in parent directory
SEALER = HERE / "seal_artifact_scope.py" if (HERE / "seal_artifact_scope.py").exists() else SOURCE / "seal_artifact_scope.py"
STRICT = HERE / "strict_receipt_consumer_v2.py" if (HERE / "strict_receipt_consumer_v2.py").exists() else SOURCE / "strict_receipt_consumer_v2.py"
CUSTODY = HERE / "cb_foundation_custody_gate_v2.py" if (HERE / "cb_foundation_custody_gate_v2.py").exists() else SOURCE / "cb_foundation_custody_gate_v2.py"
EXECUTIONS = ("fep", "hopfield", "hopf", "spinor", "type1", "type2", "cross_runtime", "hierarchy", "deformations")
LANE_EXECUTIONS = ("1q_numpy_oracle", "1q_jax", "1q_torch", "1q_julia", "3q_numpy_oracle", "3q_jax", "3q_torch", "3q_julia")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def invoke(command: list[str]) -> tuple[int, str]:
    completed = subprocess.run(command, capture_output=True, text=True)
    return completed.returncode, completed.stdout + completed.stderr


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_integrity(root: Path, control: Path, label: str) -> tuple[Path, str]:
    manifest = control / f"{label}_manifest.json"
    rc, output = invoke([sys.executable, str(SEALER), "--artifact-root", str(root), "--output", str(manifest)])
    require(rc == 0, output)
    integrity = control / f"{label}_integrity.json"
    rc, output = invoke([
        sys.executable, str(STRICT), "--artifact-root", str(root), "--receipt", str(manifest),
        "--expected-receipt-sha256", digest(manifest), "--output", str(integrity),
    ])
    require(rc == 0, output)
    return integrity, digest(integrity)


def run_custody(root: Path, integrity: Path, integrity_sha: str, foundation: Path, cross: Path, output: Path) -> tuple[int, dict]:
    rc, logs = invoke([
        sys.executable, str(CUSTODY), "--artifact-root", str(root),
        "--integrity-receipt", str(integrity), "--expected-integrity-sha256", integrity_sha,
        "--foundation-receipt", str(foundation), "--expected-foundation-sha256", digest(foundation),
        "--cross-runtime-receipt", str(cross), "--expected-cross-runtime-sha256", digest(cross),
        "--output", str(output),
    ])
    require(output.exists(), logs)
    return rc, json.loads(output.read_text())


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        root = temp / "handoff"
        control = temp / "control"
        root.mkdir()
        control.mkdir()

        foundation_source = root / "source" / "foundation.py"
        foundation_source.parent.mkdir(parents=True)
        foundation_source.write_text("print('foundation')\n")
        foundation_output = root / "output" / "fep.json"
        write_json(foundation_output, {"result": "bounded"})

        engine = root / "cross_runtime_engines"
        engine.mkdir()
        engine_source = engine / "jax_engine.py"
        engine_source.write_text("print('jax lane')\n")
        one_results, three_results = {}, {}
        for scale, suffix, destination in (("1q", "", one_results), ("3q", "_3q", three_results)):
            for lane in ("jax", "torch", "julia"):
                result_path = engine / f"{lane}_results{suffix}.json"
                write_json(result_path, {"scale": scale, "lane": lane, "value": 1})
                destination[lane] = {"errors": [], "result_hash": digest(result_path), "min_pairwise_distance": 1.0}

        foundation = root / "results" / "CB_FOUNDATION_EXTERNAL_GATE_RECEIPT.json"
        write_json(foundation, {
            "receipt_kind": "candidate_cb_external_workload_gate",
            "promotion_allowed": False,
            "source_hashes": {"source/foundation.py": digest(foundation_source)},
            "output_hashes": {"output/fep.json": digest(foundation_output)},
            "executions": {name: {"ran": True, "exit_code": 0} for name in EXECUTIONS},
            "overall": {"all_workloads_executed": True, "tooling_gate": True, "paired_genealogy_gate": "fail", "downstream_engine_consumption_allowed": False},
        })
        cross = root / "results" / "CB_CROSS_RUNTIME_CONTRACT_RECEIPT.json"
        write_json(cross, {
            "receipt_kind": "candidate_cb_cross_runtime_contract_gate",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "fresh_rerun_requested": True,
            "engine_directory": "cross_runtime_engines",
            "source_hashes": {"jax_engine.py": digest(engine_source)},
            "lane_executions": [{"name": name, "exit_code": 0} for name in LANE_EXECUTIONS],
            "one_qubit_contract": {"lanes": one_results},
            "three_qubit_contract": {"lanes": three_results},
            "overall": {"all_requested_lane_commands_exit_zero": True, "downstream_engine_admission_allowed": False},
        })

        integrity, integrity_sha = make_integrity(root, control, "good")
        rc, result = run_custody(root, integrity, integrity_sha, foundation, cross, control / "good_custody.json")
        require(rc == 0 and result["evidence_packet_ready"], "complete custody fixture must pass")
        require(result["downstream_engine_or_holodeck_allowed"] is False, "custody must not admit downstream systems")

        (engine / "torch_results.json").write_text('{"scale":"1q","lane":"torch","value":"mutated"}\n')
        integrity, integrity_sha = make_integrity(root, control, "mutated")
        rc, result = run_custody(root, integrity, integrity_sha, foundation, cross, control / "mutated_custody.json")
        require(rc == 1 and not result["conditions"]["cross_runtime_result_bindings"], "fresh scope seal must not conceal a lane-receipt mismatch")

    print("PASS cb_foundation_custody_gate_v2 regression suite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
