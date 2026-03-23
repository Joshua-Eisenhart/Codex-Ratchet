import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_graph_refinery import A2GraphRefinery
from system_v4.skills.a1_cartridge_assembler import A1CartridgeAssembler

def run_assembly():
    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session("A1_CARTRIDGE_ASSEMBLY_PASS")
    print(f"Session started: {sid}")

    assembler = A1CartridgeAssembler(refinery)

    # We mock out what the LLM would return for the 5 A1_STRIPPED nodes we generated
    # in the Rosetta Stripper pass.
    # Searching for A1_STRIPPED nodes specifically.
    
    strips = []
    for nid, data in refinery.builder.graph.nodes(data=True):
        if data.get("layer") == "A1_STRIPPED":
            strips.append((nid, data.get("name")))
            
    if not strips:
        print("No A1_STRIPPED nodes found to assemble.")
        return

    assembled_count = 0
    for node_id, name in strips:
        print(f"Assembling cartridge for {name}...")
        
        # Hardcoding the LLM mock responses based on the concept names
        shape = "TERM_DEF"
        pos = f"Rigorous constructive definition for {name}"
        neg = f"Adversarial negative boundary targeting assumed ontology for {name}"
        succ = f"Verifiable state transformation occurs interacting with {name}"
        fail = f"Symmetrical breakdown or non-commutative collapse for {name}"
        
        if "CAMPAIGN" in name:
            shape = "SIM_SPEC"
            
        cid = assembler.assemble_cartridge(
            node_id=node_id,
            candidate_shape=shape,
            steelman_positive=pos,
            adversarial_negative=neg,
            success_condition=succ,
            fail_condition=fail
        )
        if cid:
            assembled_count += 1
            print(f"  -> {cid}")

    log_path = refinery.end_session()
    print(f"Assembled {assembled_count} cartridges.")
    print(f"Log path: {log_path}")

if __name__ == "__main__":
    run_assembly()
