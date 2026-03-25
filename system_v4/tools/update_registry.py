import sys
from pathlib import Path

# Fix path to load system_v4 skills
sys.path.insert(0, str(Path(".").resolve()))

from system_v4.skills.skill_registry import SkillRegistry

def main():
    r = SkillRegistry(".")
    
    # Define the 6 explicit layer bindings
    updates = {
        "a2-high-intake-graph-builder": "PHASE_A2_3_INTAKE",
        "a2-mid-refinement-graph-builder": "PHASE_A2_2_CONTRADICTION",
        "a2-low-control-graph-builder": "PHASE_A2_1_PROMOTION",
        "a1-rosetta-mapper": "PHASE_A1_ROSETTA",
        "a1-rosetta-stripper": "PHASE_A1_STRIPPER",
        "a1-cartridge-assembler": "PHASE_A1_CARTRIDGE",
    }
    
    for skill_id, layer_id in updates.items():
        if skill_id in r.skills:
            skill = r.skills[skill_id]
            # Ensure the exact layer_id is in applicable_trust_zones
            if layer_id not in skill.applicable_trust_zones:
                skill.applicable_trust_zones.append(layer_id)
            
            # Ensure the capability is set so the runner can distinguish them from passive tools
            if "capabilities" not in skill.__dict__ or skill.capabilities is None:
                skill.capabilities = {}
            skill.capabilities["is_phase_runner"] = True
            
            print(f"Updated {skill_id}: added layer '{layer_id}', capability 'is_phase_runner'=True")
        else:
            print(f"WARNING: Skill {skill_id} not found in registry!")
            
    r.save()
    print("Registry saved.")

if __name__ == "__main__":
    main()
