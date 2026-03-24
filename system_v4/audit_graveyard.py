import yaml
import json

def audit_graveyard():
    print("Loading dna.yaml Graveyard...")
    with open("skills/intent-compiler/dna.yaml", "r") as f:
        dna = yaml.safe_load(f)
    
    graveyard = dna.get("graveyard", {})
    resolved = graveyard.get("resolved_kills", [])
    
    print("Loading Unified Evidence Report...")
    with open("probes/a2_state/sim_results/unified_evidence_report.json", "r") as f:
        report = json.load(f)
        
    all_tokens = report.get("all_tokens", [])
    token_dict = {t["token_id"]: t for t in all_tokens if "token_id" in t}
    
    print("\n--- RESOLVED KILLS AUDIT ---")
    all_pass = True
    for entry in resolved:
        t_id = entry.get("token", entry) # Handle string or dict
        if isinstance(entry, dict) and "token" in entry:
            t_id = entry["token"]
            
        if t_id not in token_dict:
            print(f"⚠ MISSING: {t_id} is not emitted by any active probe.")
            all_pass = False
        else:
            status = token_dict[t_id].get("status")
            if status != "PASS":
                print(f"❌ REGRESSION: {t_id} is marked resolved but its status is {status}")
                all_pass = False
            else:
                print(f"✅ VERIFIED PASS: {t_id}")
                
    if all_pass:
        print("\nAll resolved kills successfully VERIFIED.")
    
    with open("a2_state/audit_logs/A2_GRAVEYARD_AUDIT__v1.md", "w") as f:
        f.write("# Graveyard Audit\\n\\n")
        f.write("All resolved_kills from dna.yaml have been cross-referenced with the unified evidence report.\\n")
        if all_pass:
            f.write("STATUS: **100% VERIFIED**.\\nNo regressions found in resolved tokens.\\n")
        else:
            f.write("STATUS: **FAILED**.\\nMismatches or regressions detected.\\n")

if __name__ == "__main__":
    audit_graveyard()
