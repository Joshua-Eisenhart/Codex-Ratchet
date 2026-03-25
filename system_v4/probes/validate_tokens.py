import json
from pathlib import Path

def validate_tokens():
    print("Loading Unified Evidence Report...")
    with open("a2_state/sim_results/unified_evidence_report.json") as f:
        report = json.load(f)
    
    tokens = report.get("all_tokens", [])
    token_ids = {t["token_id"] for t in tokens if "token_id" in t}
    print(f"Found {len(token_ids)} unique Token IDs in SIM results.")

    print("Loading Master Graph (system_graph_a2_refinery.json)...")
    _repo_root = Path(__file__).resolve().parent.parent.parent
    with open(str(_repo_root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json")) as f:
        graph = json.load(f)
    
    nodes = graph.get("nodes", {})
    if isinstance(nodes, list):
        node_ids = {n.get("id") for n in nodes if n.get("id")}
    else:
        node_ids = set(nodes.keys())
        
    print(f"Found {len(node_ids)} Node IDs in Master Graph.")

    missing = token_ids - node_ids
    print(f"\nResults: {len(missing)} tokens missing from Master Graph.")
    
    if missing:
        print("Sample missing tokens:")
        for m in list(missing)[:10]:
            print(f"  - {m}")
    else:
        print("ALL TOKENS SUCCESSFULLY BRIDGED!")

if __name__ == "__main__":
    validate_tokens()
