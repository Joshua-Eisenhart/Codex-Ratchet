import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_graph_refinery import A2GraphRefinery
from system_v4.skills.a1_rosetta_stripper import A1RosettaStripper

def run_pass():
    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session("A1_ROSETTA_STRIP_PASS")
    print(f"Session started: {sid}")

    stripper = A1RosettaStripper(refinery)

    # We will find the exact node IDs for some newly extracted concepts
    # and strip them into A1 equivalents.
    targets = {
        "a2_refinery_bootpack": {
            "stripped_name": "A2_REFINERY_BOOTPACK_CONTRACT",
            "stripped_desc": "Strict execution contract ensuring fail-closed, invariant-locked extraction.",
            "dropped_jargon": ["prioritize", "over-capture", "high-entropy"],
            "required_anchors": ["FAIL_CLOSED", "INVARIANT_LOCK"]
        },
        "a1_wiggle_execution_contract": {
            "stripped_name": "A1_MULTI_NARRATIVE_EXECUTION_CONTRACT",
            "stripped_desc": "A1 adversarial exploration requiring explicit negative and rescue lanes.",
            "dropped_jargon": ["wiggle", "proposals", "from A2 outputs"],
            "required_anchors": ["STEELMAN_LANE", "ADVERSARIAL_NEG_LANE"]
        },
        "a1_ratchet_fuel_packaging": {
            "stripped_name": "A1_CANDIDATE_FUEL_PACKET",
            "stripped_desc": "Strict packaging envelope forcing dual positive/negative structural items over hidden assumptions.",
            "dropped_jargon": ["ratchet-ready", "exploratory outputs", "silent fallback to prose"],
            "required_anchors": ["CANDIDATE", "NEGATIVE_CLASS"]
        },
        "stage_0_canonical_filename_format": {
            "stripped_name": "STAGE_0_CANONICAL_GRAMMAR",
            "stripped_desc": "5-field unspaced artifact naming rule for deterministic pipeline sorting.",
            "dropped_jargon": ["double underscore", "No spaces, hyphens, or parentheses"],
            "required_anchors": ["ARTIFACT_ROLE", "VERSION"]
        },
        "sim_staged_campaign": {
            "stripped_name": "SIM_STAGED_CAMPAIGN",
            "stripped_desc": "Hierarchical mega-check ordering from TERM_SEED up to WHOLE_SYSTEM.",
            "dropped_jargon": ["flat queue", "Higher stages are meaningless"],
            "required_anchors": ["TERM_SEED", "MEGA_SUITE"]
        }
    }

    stripped_count = 0
    
    # Needs to iterate over a copy of the graph or just find the IDs first
    matches = []
    for nid, data in refinery.builder.graph.nodes(data=True):
        if data.get("name") in targets:
            matches.append((nid, data.get("name")))

    for node_id, orig_name in matches:
        spec = targets[orig_name]
        print(f"Stripping {orig_name}...")
        stripped_id = stripper.strip_concept(
            node_id=node_id,
            stripped_name=spec["stripped_name"],
            stripped_desc=spec["stripped_desc"],
            dropped_jargon=spec["dropped_jargon"],
            required_anchors=spec["required_anchors"]
        )
        if stripped_id:
            stripped_count += 1
            print(f"  -> {stripped_id}")

    log_path = refinery.end_session()
    print(f"Stripped {stripped_count} concepts. Log explicitly contains ROSETTA_MAP edges.")
    print(f"Log path: {log_path}")

if __name__ == "__main__":
    run_pass()
