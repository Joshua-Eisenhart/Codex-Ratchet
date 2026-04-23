import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_graph_refinery import A2GraphRefinery
from system_v4.skills.a2_thermodynamic_purge import A2ThermodynamicPurge

def run_purge():
    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session("THERMODYNAMIC_PURGE_PASS")
    print(f"Session started: {sid}")

    purger = A2ThermodynamicPurge(refinery)

    # We will simulate purging some entries that Opus identified as HOLD_CANDIDATE
    # or that are known A2 high-entropy noise.
    # Looking for 'Entropy-First Unified Framework' or 'Mirror-Driven Self-Governance'
    
    targets = [
        ("Entropy-First Unified Framework", "Name collision / Redundant to kernel logic"),
        ("Mirror-Driven Self-Governance Stack", "High entropy narrative vibe. Unverifiable constraints."),
        ("Non-Classical Operatory Framework", "Duplicative of non-classical invariants already extracted.")
    ]

    purged_count = 0
    for name, reason in targets:
        print(f"Purging '{name}'...")
        success = purger.purge_concept(
            node_id=name,
            reason=reason,
            violating_anchors=["A2_HIGH_ENTROPY", "NARRATIVE_VIBE"]
        )
        if success:
            purged_count += 1
            print(f"  -> Routed to GRAVEYARD")

    log_path = refinery.end_session()
    print(f"Purged {purged_count} concepts to the thermodynamic waste channel.")
    print(f"Log path: {log_path}")

if __name__ == "__main__":
    run_purge()
