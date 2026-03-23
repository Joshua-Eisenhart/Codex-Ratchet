"""
evidence_witness_bridge.py
===========================
Bridges probe EvidenceTokens → skills WitnessRecorder.

This closes the gap identified by Codex audit:
  probes/ (evidence tokens) ←→ skills/ (witness recorder)

JP architecture mapping:
  EvidenceToken → Witness (FlowMind runtime record)
  PASS token   → POSITIVE witness
  KILL token   → NEGATIVE witness (violation)
  unified_evidence_report.json → witness corpus
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from system_v4.skills.runtime_state_kernel import (
    Witness, WitnessKind, StepEvent, BoundaryTag, utc_iso,
)
from system_v4.skills.witness_recorder import WitnessRecorder


def evidence_token_to_witness(token: dict) -> Witness:
    """Convert a probe EvidenceToken dict to a skills Witness."""
    passed = token.get("status") == "PASS"
    
    step = StepEvent(
        at=utc_iso(),
        op=f"probe:{token.get('sim_spec_id', 'unknown')}",
        before_hash="",
        after_hash=str(token.get("measured_value", "")),
        notes=[
            f"token_id={token.get('token_id', '')}",
            f"value={token.get('measured_value', '')}",
        ],
    )
    
    violations = []
    if not passed:
        kill_reason = token.get("kill_reason", "UNKNOWN")
        violations.append(f"KILL:{kill_reason}")
    
    boundaries = []
    sim_id = token.get("sim_spec_id", "")
    if "AXIOM" in sim_id or "F01" in sim_id or "N01" in sim_id:
        boundaries.append(BoundaryTag.STABLE)
    if "KILL" in str(token.get("status", "")):
        boundaries.append(BoundaryTag.BLOCKED)
    
    return Witness(
        kind=WitnessKind.POSITIVE if passed else WitnessKind.NEGATIVE,
        passed=passed,
        violations=violations,
        touched_boundaries=boundaries,
        trace=[step],
    )


def bridge_evidence_to_witnesses(
    evidence_report_path: str,
    witness_output_path: str,
) -> dict:
    """
    Read unified_evidence_report.json and convert all tokens
    to Witness entries in the witness recorder.
    
    Returns summary dict.
    """
    report = json.loads(Path(evidence_report_path).read_text())
    tokens = report.get("all_tokens", report.get("evidence_ledger", []))
    
    recorder = WitnessRecorder(witness_output_path)
    
    pass_count = 0
    kill_count = 0
    
    for token in tokens:
        witness = evidence_token_to_witness(token)
        tags = {
            "source": "probe",
            "sim_spec_id": token.get("sim_spec_id", ""),
            "token_id": token.get("token_id", ""),
        }
        recorder.record(witness, tags=tags)
        
        if token.get("status") == "PASS":
            pass_count += 1
        else:
            kill_count += 1
    
    recorder.flush()
    
    summary = {
        "bridged_at": utc_iso(),
        "total_tokens": len(tokens),
        "pass_witnesses": pass_count,
        "kill_witnesses": kill_count,
        "witness_corpus_path": str(witness_output_path),
        "witness_corpus_size": len(recorder),
    }
    
    return summary


if __name__ == "__main__":
    repo = str(Path(__file__).resolve().parents[2])
    
    evidence_path = os.path.join(
        repo, "system_v4/probes/a2_state/sim_results/unified_evidence_report.json"
    )
    witness_path = os.path.join(
        repo, "system_v4/runtime_state/probe_witnesses.json"
    )
    
    if not os.path.exists(evidence_path):
        print(f"No evidence report at {evidence_path}")
        print("Run: python3 system_v4/probes/run_all_sims.py first")
        sys.exit(1)
    
    summary = bridge_evidence_to_witnesses(evidence_path, witness_path)
    
    print(f"EVIDENCE → WITNESS BRIDGE")
    print(f"  Tokens bridged:    {summary['total_tokens']}")
    print(f"  PASS witnesses:    {summary['pass_witnesses']}")
    print(f"  KILL witnesses:    {summary['kill_witnesses']}")
    print(f"  Corpus saved to:   {summary['witness_corpus_path']}")
    print(f"  Total in corpus:   {summary['witness_corpus_size']}")
