"""
Thread SIM Evidence Normalizer
==============================
Deterministic wrapper that converts raw simulation outputs into
kernel-safe SIM_EVIDENCE v1 containers for Thread B consumption.

Thread SIM does NOT execute simulations — it WRAPS results.

Protocol:
  1. Compute CODE_HASH_SHA256 of the source code that ran the SIM
  2. Compute OUTPUT_HASH_SHA256 of canonically sorted JSON outputs
  3. Validate required fields (SIM_ID, hashes, EVIDENCE_TOKEN)
  4. Inject BRANCH_ID and BATCH_ID metadata
  5. Format as strict SIM_EVIDENCE v1 grammar
  6. Strip all human-readable prose
  7. Flush as SIM_EVIDENCE_PACK
"""

import hashlib
import json
import os
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional


def compute_code_hash(filepath: str) -> str:
    """Compute SHA256 hash of the exact source code file."""
    with open(filepath, 'r') as f:
        code = f.read()
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def compute_output_hash(output_data: Dict[str, Any]) -> str:
    """Compute SHA256 hash of canonically sorted JSON output."""
    canonical = json.dumps(output_data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def validate_hash(h: str) -> bool:
    """Validate hash is exactly 64 lowercase hex characters."""
    if len(h) != 64:
        return False
    try:
        int(h, 16)
        return h == h.lower()
    except ValueError:
        return False


def normalize_evidence(
    sim_id: str,
    code_hash: str,
    output_hash: str,
    evidence_token: str,
    metrics: Dict[str, Any],
    branch_id: str = "PROTO_DIRECTIONAL_ACCUMULATOR_V1",
    batch_id: str = "BATCH_001",
) -> Optional[str]:
    """
    Normalize a single SIM result into SIM_EVIDENCE v1 format.
    
    Returns the formatted evidence block, or None if validation fails.
    """
    # Validate hashes
    if not validate_hash(code_hash):
        print(f"  REJECT: Invalid CODE_HASH_SHA256 for {sim_id}: {code_hash}")
        return None
    if not validate_hash(output_hash):
        print(f"  REJECT: Invalid OUTPUT_HASH_SHA256 for {sim_id}: {output_hash}")
        return None
    
    # Validate required fields
    if not sim_id or not evidence_token:
        print(f"  REJECT: Missing SIM_ID or EVIDENCE_TOKEN")
        return None
    
    # Build SIM_EVIDENCE v1 block
    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append(f"SIM_ID {sim_id}")
    lines.append(f"CODE_HASH_SHA256 {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256 {output_hash}")
    
    # Inject metadata
    lines.append(f"METRIC BRANCH_ID {branch_id}")
    lines.append(f"METRIC BATCH_ID {batch_id}")
    
    # Add all metrics
    for key, value in sorted(metrics.items()):
        # Sanitize: strip prose, keep only numeric/token values
        if isinstance(value, float):
            lines.append(f"METRIC {key} {value:.10f}")
        elif isinstance(value, int):
            lines.append(f"METRIC {key} {value}")
        elif isinstance(value, str):
            # Only allow token-safe strings (no spaces, no prose)
            sanitized = value.replace(" ", "_").upper()
            lines.append(f"METRIC {key} {sanitized}")
    
    lines.append(f"EVIDENCE_SIGNAL {evidence_token}")
    lines.append("END SIM_EVIDENCE v1")
    
    return "\n".join(lines)


def emit_sim_evidence_pack(
    results_filepath: str,
    code_filepath: str,
    branch_id: str = "PROTO_DIRECTIONAL_ACCUMULATOR_V1",
    batch_id: str = "BATCH_001",
) -> str:
    """
    Read raw SIM results JSON and emit a normalized SIM_EVIDENCE_PACK.
    
    This is the main entry point for Thread SIM normalization.
    """
    print(f"{'='*60}")
    print(f"THREAD SIM: EVIDENCE NORMALIZATION")
    print(f"  Source: {os.path.basename(results_filepath)}")
    print(f"  Code:   {os.path.basename(code_filepath)}")
    print(f"  Branch: {branch_id}")
    print(f"  Batch:  {batch_id}")
    print(f"{'='*60}")
    
    # Load raw results
    with open(results_filepath, 'r') as f:
        raw = json.load(f)
    
    # Compute hashes
    code_hash = compute_code_hash(code_filepath)
    print(f"  CODE_HASH_SHA256: {code_hash}")
    
    # Check for duplicate SIM_IDs
    evidence_ledger = raw.get("evidence_ledger", [])
    sim_ids = [e["sim_spec_id"] for e in evidence_ledger]
    duplicates = set([x for x in sim_ids if sim_ids.count(x) > 1])
    if duplicates:
        print(f"  REJECT: Duplicate SIM_IDs detected: {duplicates}")
        return ""
    
    # Normalize each evidence entry
    blocks = []
    accepted = 0
    rejected = 0
    
    for entry in evidence_ledger:
        sim_id = entry.get("sim_spec_id", "")
        token = entry.get("token_id", "")
        status = entry.get("status", "")
        
        # Only wrap PASS results — KILL results go to Graveyard, not Thread B
        if status != "PASS":
            print(f"  SKIP: {sim_id} (status={status}, goes to Graveyard)")
            continue
        
        if not token:
            print(f"  SKIP: {sim_id} (no evidence token)")
            continue
        
        # Build output data for this specific SIM
        output_data = {
            "sim_id": sim_id,
            "status": status,
            "measured_value": entry.get("measured_value"),
            "token_id": token,
        }
        output_hash = compute_output_hash(output_data)
        
        # Build metrics from the entry
        metrics = {
            "STATUS": status,
            "MEASURED_VALUE": entry.get("measured_value", 0.0),
        }
        if entry.get("kill_reason"):
            metrics["KILL_REASON"] = entry["kill_reason"]
        
        block = normalize_evidence(
            sim_id=sim_id,
            code_hash=code_hash,
            output_hash=output_hash,
            evidence_token=token,
            metrics=metrics,
            branch_id=branch_id,
            batch_id=batch_id,
        )
        
        if block:
            blocks.append(block)
            accepted += 1
            print(f"  ACCEPTED: {sim_id} → {token}")
        else:
            rejected += 1
    
    # Assemble the pack
    pack = "\n\n".join(blocks)
    
    print(f"\n  --- NORMALIZATION SUMMARY ---")
    print(f"  Accepted: {accepted}")
    print(f"  Rejected: {rejected}")
    print(f"  Skipped (KILL→Graveyard): {len(evidence_ledger) - accepted - rejected}")
    
    return pack


def normalize_all_results():
    """Normalize both proto-directional_accumulator and dual-process_cycle results."""
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    output_dir = os.path.join(base, "..", "a2_state", "sim_evidence")
    os.makedirs(output_dir, exist_ok=True)
    
    packs = []
    
    # Proto-directional_accumulator results
    proto_results = os.path.join(results_dir, "proto_directional_accumulator_results.json")
    proto_code = os.path.join(base, "proto_directional_accumulator_sim_runner.py")
    if os.path.exists(proto_results):
        pack = emit_sim_evidence_pack(
            proto_results, proto_code,
            branch_id="PROTO_DIRECTIONAL_ACCUMULATOR_V1",
            batch_id="BATCH_PROTO_001",
        )
        if pack:
            packs.append(pack)
    
    # Dual process_cycle results
    dual_results = os.path.join(results_dir, "dual_process_cycle_results.json")
    dual_code = os.path.join(base, "dual_weyl_spinor_process_cycle_sim.py")
    if os.path.exists(dual_results):
        pack = emit_sim_evidence_pack(
            dual_results, dual_code,
            branch_id="DUAL_WEYL_SPINOR_V1",
            batch_id="BATCH_DUAL_001",
        )
        if pack:
            packs.append(pack)
    
    # Write combined evidence pack
    full_pack = "\n\n".join(packs)
    
    outpath = os.path.join(output_dir, "SIM_EVIDENCE_PACK__v1.txt")
    with open(outpath, "w") as f:
        f.write(full_pack)
    
    print(f"\n{'='*60}")
    print(f"SIM_EVIDENCE_PACK written to: {outpath}")
    print(f"{'='*60}")
    print(f"\n{full_pack}")
    
    return full_pack


if __name__ == "__main__":
    normalize_all_results()
