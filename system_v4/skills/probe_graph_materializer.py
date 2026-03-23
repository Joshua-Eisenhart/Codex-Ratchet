"""
probe_graph_materializer.py — Bridge probe evidence into graph format
======================================================================
Converts the unified_evidence_report.json into a graph with nodes and
edges that run_real_ratchet.py can consume as fuel.

This closes the Codex audit's finding #4:
  "two live systems still barely touch"

The materializer reads probe evidence and produces a graph JSON that
the A1 brain can use for candidate extraction.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone


def materialize_probe_graph(repo_root: str) -> dict:
    """
    Read unified evidence report and convert to graph format
    compatible with run_real_ratchet's load_bounded_graph_fuel().
    """
    report_path = os.path.join(
        repo_root, "system_v4/probes/a2_state/sim_results/unified_evidence_report.json"
    )
    
    if not os.path.exists(report_path):
        return {"ok": False, "errors": ["No unified evidence report found"]}
    
    report = json.loads(Path(report_path).read_text())
    tokens = report.get("all_tokens", [])
    
    nodes = {}
    edges = []
    
    # Create a node for each SIM file's result set
    sim_results = report.get("sim_results", [])
    if isinstance(sim_results, list):
        for sim_data in sim_results:
            sim_file = sim_data.get("file", "unknown")
            
            # Use evidence-level counts if available (from updated run_all_sims.py),
            # otherwise compute from tokens directly. DO NOT use process-level status
            # to infer pass/kill counts — a SIM can exit 0 with KILL tokens.
            if "pass_count" in sim_data and "kill_count" in sim_data:
                pass_count = sim_data["pass_count"]
                kill_count = sim_data["kill_count"]
                evidence_status = sim_data.get("evidence_status", "UNKNOWN")
            else:
                # Fallback: count tokens matching this SIM file
                sim_tokens = [t for t in tokens if any(
                    sim_file.replace('.py', '') in (t.get('sim_spec_id', '') or '')
                )]
                pass_count = sum(1 for t in sim_tokens if t.get('status') == 'PASS')
                kill_count = sum(1 for t in sim_tokens if t.get('status') == 'KILL')
                evidence_status = "ALL_PASS" if kill_count == 0 and pass_count > 0 else (
                    "KILL_PRESENT" if kill_count > 0 else "NO_TOKENS"
                )
            
            node_id = f"probe:{sim_file.replace('.py', '')}"
            nodes[node_id] = {
                "name": sim_file,
                "description": f"QIT probe: {evidence_status}, {pass_count}P/{kill_count}K",
                "type": "probe_evidence",
                "tags": ["probe", "qit", "evidence"],
                "process_status": sim_data.get("process_status", sim_data.get("status", "UNKNOWN")),
                "evidence_status": evidence_status,
                "pass_count": pass_count,
                "kill_count": kill_count,
                "token_count": sim_data.get("token_count", pass_count + kill_count),
            }
    
    # Build sim_file lookup from sim_results for edge linking
    sim_file_set = set()
    for sim_data in sim_results:
        if isinstance(sim_data, dict):
            sim_file_set.add(sim_data.get("file", ""))
    
    # Create tokens as individual leaf nodes
    orphan_counter = 0
    for token in tokens:
        tid = token.get("token_id", "")
        # Generate synthetic ID for tokens with blank token_id (often KILL tokens)
        if not tid:
            orphan_counter += 1
            tid = f"UNNAMED_TOKEN_{orphan_counter}_{token.get('status', 'UNK')}"
        
        node_id = f"token:{tid}"
        nodes[node_id] = {
            "name": tid,
            "description": f"{token.get('status', '?')}: {token.get('sim_spec_id', '')}",
            "type": "evidence_token",
            "tags": ["token", token.get("status", "").lower()],
            "status": token.get("status", "UNKNOWN"),
            "measured_value": token.get("measured_value", 0),
            "source_file": token.get("source_file", ""),
        }
        
        # Edge from SIM to token — use source_file (stamped by run_all_sims),
        # fall back to sim_spec_id-based matching, fail closed if no match
        source_file = token.get("source_file", "")
        matched_sim = None
        
        if source_file and source_file in sim_file_set:
            # Direct match via source_file (preferred path)
            matched_sim = source_file
        else:
            # Fallback: try to find a SIM whose filename base appears in sim_spec_id
            sim_spec = token.get("sim_spec_id", "").lower()
            for sim_data in sim_results:
                if isinstance(sim_data, dict):
                    sf = sim_data.get("file", "")
                    # Match by meaningful name parts, not just substring
                    base = sf.replace(".py", "").replace("_sim", "").replace("_", "")
                    spec_clean = sim_spec.replace("s_sim_", "").replace("_v1", "").replace("_", "")
                    if base and spec_clean and base in spec_clean or spec_clean in base:
                        matched_sim = sf
                        break
        
        if matched_sim:
            edges.append({
                "source": f"probe:{matched_sim.replace('.py', '')}",
                "target": node_id,
                "type": "produces",
            })
        # If no match found, token is an orphan — no edge created (fail closed)
    
    # Layer-based edges (dependency ordering)
    layer_names = sorted(
        [k for k in report.keys() if k.startswith("layer_")],
        key=lambda x: x
    )
    
    # Create the graph JSON
    graph = {
        "schema": "A2_PROBE_EVIDENCE_GRAPH_v1",
        "build_status": "MATERIALIZED",
        "materialized": True,
        "summary": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "total_tokens": len(tokens),
            "pass_count": report.get("pass_count", 0),
            "kill_count": report.get("kill_count", 0),
        },
        "blockers": [],
        "nodes": nodes,
        "edges": edges,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Save
    output_dir = os.path.join(repo_root, "system_v4/a2_state/graphs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "probe_evidence_graph.json")
    
    with open(output_path, "w") as f:
        json.dump(graph, f, indent=2)
    
    # Also save audit note
    audit_note_path = os.path.join(output_dir, "probe_evidence_graph_audit.md")
    with open(audit_note_path, "w") as f:
        f.write(f"# Probe Evidence Graph — Materialization Audit\n")
        f.write(f"Timestamp: {graph['timestamp']}\n\n")
        f.write(f"## Summary\n")
        f.write(f"- Nodes: {len(nodes)}\n")
        f.write(f"- Edges: {len(edges)}\n")
        f.write(f"- Tokens: {len(tokens)} ({report.get('pass_count',0)} PASS, {report.get('kill_count',0)} KILL)\n\n")
        f.write(f"## Node List\n")
        for nid, node in nodes.items():
            f.write(f"- `{nid}`: {node['description']}\n")
    
    return {
        "ok": True,
        "json_path": output_path,
        "audit_note_path": audit_note_path,
        "graph": graph,
    }


def create_probe_queue_packet(repo_root: str, graph_path: str) -> dict:
    """
    Create an A1 queue status packet that authorizes run_real_ratchet
    to consume probe evidence as fuel.
    """
    ts = datetime.now(timezone.utc).strftime("%Y_%m_%d")
    
    # Build worker launch packet
    worker_packet = {
        "schema": "A1_WORKER_LAUNCH_PACKET_v1",
        "dispatch_id": f"PROBE_EVIDENCE_DISPATCH_{int(datetime.now(timezone.utc).timestamp())}",
        "target_a1_role": "A1_PROBE_EVIDENCE_CONSUMER",
        "required_a1_boot": "system_v4/skills/intent-compiler/dna.yaml",
        "source_a2_artifacts": [graph_path],
        "prompt_to_send": (
            "Consume the probe evidence graph. For each KILL token, analyze the kill reason "
            "and propose a calibration fix. For each PASS token, verify the evidence is still "
            "consistent with current constraints. Report the overall engine health."
        ),
        "stop_rule": "After processing all nodes in the evidence graph, save results and stop.",
    }
    
    worker_packet_path = os.path.join(
        repo_root, f"system_v4/a2_state/A1_WORKER_LAUNCH_PACKET__PROBE_EVIDENCE__{ts}__v1.json"
    )
    os.makedirs(os.path.dirname(worker_packet_path), exist_ok=True)
    with open(worker_packet_path, "w") as f:
        json.dump(worker_packet, f, indent=2)
    
    # Update queue status to READY
    queue_packet = {
        "schema": "A1_QUEUE_STATUS_PACKET_v1",
        "queue_status": "READY_FROM_A2_PREBUILT_BATCH",
        "dispatch_id": worker_packet["dispatch_id"],
        "target_a1_role": worker_packet["target_a1_role"],
        "required_a1_boot": worker_packet["required_a1_boot"],
        "ready_packet_json": worker_packet_path,
        "reason": "Probe evidence ready for consumption via evidence graph",
    }
    
    return {
        "queue_packet": queue_packet,
        "worker_packet_path": worker_packet_path,
    }


if __name__ == "__main__":
    repo = str(Path(__file__).resolve().parents[2])
    
    print("PROBE GRAPH MATERIALIZER")
    print("=" * 50)
    
    result = materialize_probe_graph(repo)
    
    if result["ok"]:
        summary = result["graph"]["summary"]
        print(f"  ✓ Graph materialized:")
        print(f"    Nodes: {summary['total_nodes']}")
        print(f"    Edges: {summary['total_edges']}")
        print(f"    Tokens: {summary['total_tokens']} "
              f"({summary['pass_count']} PASS, {summary['kill_count']} KILL)")
        print(f"    Saved to: {result['json_path']}")
        
        queue_result = create_probe_queue_packet(repo, result["json_path"])
        print(f"\n  ✓ Queue packet created:")
        print(f"    Worker: {queue_result['worker_packet_path']}")
        print(f"    Status: READY_FROM_A2_PREBUILT_BATCH")
    else:
        print(f"  ✗ Failed: {result['errors']}")
