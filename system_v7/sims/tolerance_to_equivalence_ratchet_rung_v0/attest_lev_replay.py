#!/usr/bin/env python3
"""Bind one sealed Lev gate run to the frozen flow and finalize the bounded tooth."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess


SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parents[2]
FLOW = SIM_DIR / "lev" / "flow.yaml"
RESULT_DIR = SIM_DIR / "results"
G0_G9 = RESULT_DIR / "g0_g9_report.json"
LEV_RECEIPT = RESULT_DIR / "lev_replay_receipt.json"
FINAL_REPORT = RESULT_DIR / "final_report.json"
LEV_ROOT = Path("/Users/joshuaeisenhart/lev-main/.worktrees/eval-projection-contract")
LEV_EXECUTABLE = LEV_ROOT / "core/poly/bin/lev"
EXPECTED_LEV_HEAD = "856acb1a5de42528a9a54272435d98a9fe226186"
EXPECTED_LEV_TREE = "3f3488781d48a64b22c43c08ccfaa2b503d49524"
EXPECTED_LEV_SHA256 = "f258ae313d515cae4ff848a45df78cfcc6a2d48c9ce1ade9c316276b00ef0c61"
EXPECTED_NODES = ["flow_contract_gate", "preregistration_gate", "g0_g9_pipeline_gate", "g0_g9_report_gate"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=LEV_ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--exec-id", required=True)
    parser.add_argument("--receipt-id", required=True)
    args = parser.parse_args()
    findings: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            findings.append(message)

    events_path = args.events.resolve()
    runs_path = args.runs.resolve()
    events = [event for event in jsonl(events_path) if event.get("data", {}).get("execId") == args.exec_id]
    sealed = [run for run in jsonl(runs_path) if run.get("exec_id") == args.exec_id]
    flow_events = [event for event in events if event.get("type") == "exec.flow_validated"]
    gate_events = [event for event in events if event.get("type") == "exec.gate.run"]
    branch_events = [event for event in events if event.get("type") == "exec.branch.selected"]
    completed_nodes = [event for event in events if event.get("type") == "exec.node.completed"]
    require(len(flow_events) == 1, "expected one flow validation event")
    if flow_events:
        flow_data = flow_events[0]["data"]
        require(flow_data.get("flowPath") == str(FLOW), "Lev flow path mismatch")
        require(flow_data.get("adapter") == "no-model" and flow_data.get("model") == "no-model", "Lev was not initialized with the no-model adapter")
        require(flow_data.get("graph", {}).get("name") == "tolerance-to-equivalence-ratchet-rung-v0", "compiled graph name mismatch")
    observed_nodes = [event["data"].get("nodeId") for event in gate_events]
    require(observed_nodes == EXPECTED_NODES, f"gate node order mismatch: {observed_nodes}")
    require(all(event["data"].get("verdict") == "pass" and event["data"].get("exit_code") == 0 for event in gate_events), "one or more command GateProofs failed")
    require([event["data"].get("branch_taken") for event in branch_events] == ["pass"] * len(EXPECTED_NODES), "one or more non-pass branches selected")
    require(all(event["data"].get("adapter") == "shell" and event["data"].get("model") == "none" for event in completed_nodes), "a completed node used a model adapter")
    require(len(sealed) == 1, "expected one sealed run")
    proof_backed = None
    evaluator_advisory_red = False
    if sealed:
        run = sealed[0]
        require(run.get("receipt_id") == args.receipt_id, "receipt ID mismatch")
        require(run.get("seal", {}).get("outcome") == "candidate_effect", "sealed outcome is not candidate_effect")
        receipt_refs = [item for item in run.get("seal", {}).get("evidence_refs", []) if item.get("kind") == "receipt"]
        require(len(receipt_refs) == 1 and receipt_refs[0].get("passed") is True, "sealed receipt is not passed")
        if receipt_refs:
            proof_backed = receipt_refs[0].get("proof_backed_execution")
        evaluator_advisory_red = "gate:evaluator:evaluation_error" in run.get("seal", {}).get("verdict_refs", [])
    require(LEV_EXECUTABLE.is_file() and sha256(LEV_EXECUTABLE) == EXPECTED_LEV_SHA256, "Lev executable hash mismatch")
    require(git("rev-parse", "HEAD") == EXPECTED_LEV_HEAD, "Lev HEAD mismatch")
    require(git("rev-parse", "HEAD^{tree}") == EXPECTED_LEV_TREE, "Lev tree mismatch")
    require(not git("status", "--short"), "Lev worktree dirty")
    require(G0_G9.is_file(), "G0-G9 report missing")
    g0_g9 = json.loads(G0_G9.read_text(encoding="utf-8")) if G0_G9.is_file() else {}
    require(g0_g9.get("mechanical_pass") is True, "G0-G9 mechanical boundary invalid")
    require(g0_g9.get("semantic_forcing_pass") is True, "semantic forcing gate is red; Lev cannot authorize a v0 tooth")
    evidence = []
    for event in gate_events:
        data = event["data"]
        refs = []
        for reference in data.get("evidence_refs", []):
            path = Path(reference)
            require(path.is_file(), f"GateProof evidence missing: {path}")
            refs.append({"path": str(path), "sha256": sha256(path) if path.is_file() else None})
        evidence.append({"node_id": data.get("nodeId"), "gate_id": data.get("gate_id"), "verdict": data.get("verdict"), "exit_code": data.get("exit_code"), "evidence": refs})
    g10_pass = not findings
    lev_receipt = {
        "schema": "codex_ratchet.tolerance_to_equivalence.lev_replay_receipt.v1",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "exec_id": args.exec_id,
        "receipt_id": args.receipt_id,
        "flow_path": str(FLOW.relative_to(ROOT)),
        "flow_sha256": sha256(FLOW),
        "events_path": str(events_path),
        "events_sha256": sha256(events_path),
        "runs_path": str(runs_path),
        "runs_sha256": sha256(runs_path),
        "lev": {"path": str(LEV_EXECUTABLE), "sha256": sha256(LEV_EXECUTABLE), "head": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"), "clean": not bool(git("status", "--short"))},
        "adapter": "no-model",
        "model_dispatched": False,
        "gate_proofs": evidence,
        "blocking_gate_count": len(gate_events),
        "all_blocking_gates_pass": all(event["data"].get("verdict") == "pass" for event in gate_events),
        "receipt_passed": True if sealed else False,
        "proof_backed_execution": proof_backed,
        "evaluator_advisory_red": evaluator_advisory_red,
        "g10_pass": g10_pass,
        "findings": findings,
        "claim_ceiling": "deterministic no-model Lev replay only; current Lev ProofBundle is not assembled and production promotion remains blocked",
    }
    LEV_RECEIPT.write_text(json.dumps(lev_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    gates = dict(g0_g9.get("gates", {}))
    gates["G10_deterministic_lev_replay"] = g10_pass
    all_pass = bool(
        g0_g9.get("candidate_pass")
        and g0_g9.get("semantic_forcing_pass")
        and all(gates.values())
        and g10_pass
    )
    final_report = {
        "schema": "codex_ratchet.tolerance_to_equivalence.final_report.v2",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "sim_id": "tolerance_to_equivalence_ratchet_rung_v0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "scientific_claim_proven": False,
        "release_eligible": False,
        "official_launch_allowed": False,
        "llm_verdict_used": False,
        "gates": gates,
        "all_code_gates_pass": all_pass,
        "decision": "COMMIT_ONE_BOUNDED_SCRATCH_TOOTH" if all_pass else "HOLD",
        "ratchet_state_before": "OPEN",
        "ratchet_state_after": "TOOTH_1_COMMITTED_SCRATCH" if all_pass else "OPEN",
        "drive": g0_g9.get("candidate_decision"),
        "artifacts": {
            "g0_g9_report": {"path": str(G0_G9.relative_to(ROOT)), "sha256": sha256(G0_G9)},
            "lev_replay_receipt": {"path": str(LEV_RECEIPT.relative_to(ROOT)), "sha256": sha256(LEV_RECEIPT)},
        },
        "lev_boundary": {"proof_backed_execution": proof_backed, "evaluator_advisory_red": evaluator_advisory_red, "proof_bundle_written": False},
        "claim_ceiling": "Lev replay cannot repair the red v0 semantic-forcing gate; no Ratchet tooth",
        "blocked_consumers": [
            "official V8 launch until a runtime caller assembles and independently validates a Lev ProofBundle",
            "canonical Ratchet definition",
            "QIT engine derivation",
            "terrain/operator and Axis promotion",
            "physics, cosmology, biology, cognition, or consciousness claims"
        ],
    }
    FINAL_REPORT.write_text(json.dumps(final_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"LEV_REPLAY_ATTESTED g10_pass={str(g10_pass).lower()} decision={final_report['decision']} proof_backed={proof_backed}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
