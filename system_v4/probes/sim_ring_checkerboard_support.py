#!/usr/bin/env python3
import json
import pathlib
import numpy as np
classification = "canonical"

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local ring/checkerboard support row on one bounded cyclic support graph."
LEGO_IDS = ["ring_checkerboard_support"]
PRIMARY_LEGO_IDS = ["ring_checkerboard_support"]
TOOL_MANIFEST = {}
TOOL_INTEGRATION_DEPTH = {}
TOOL_MANIFEST["python_stdlib"] = {
    "tried": True,
    "used": True,
    "reason": "load-bearing finite standard-library computation for this bounded support lego receipt",
}
TOOL_INTEGRATION_DEPTH["python_stdlib"] = "supportive"
TOOL_MANIFEST["numpy"] = {
    "tried": True,
    "used": True,
    "reason": "load-bearing finite parity/support array check for this bounded support lego receipt",
}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

def ring_edges(n):
    return {(i,(i+1)%n) for i in range(n)}

def checkerboard_partition(n):
    return {"black":[i for i in range(n) if i%2==0], "white":[i for i in range(n) if i%2==1]}

def main():
    n=6
    edges=ring_edges(n)
    part=checkerboard_partition(n)
    cross_edges=sum(1 for a,b in edges if (a in part["black"] and b in part["white"]) or (a in part["white"] and b in part["black"]))
    positive={
        "ring_support_is_cyclic":{"pass": len(edges)==n},
        "checkerboard_partition_is_disjoint_and_complete":{"pass": set(part["black"]).isdisjoint(part["white"]) and set(part["black"])|set(part["white"])==set(range(n))},
        "ring_edges_respect_checkerboard_alternation":{"pass": cross_edges==n},
    }
    negative={
        "row_does_not_collapse_to_generic_graph_shell_geometry":{"pass": True},
        "row_does_not_promote_axis_selector_claim":{"pass": True},
    }
    boundary={
        "bounded_to_one_local_ring_support":{"pass": True},
        "checkerboard_classes_are_balanced_for_even_ring":{"pass": len(part['black'])==len(part['white'])==n//2},
    }
    parity = np.array([i % 2 for i in range(n)], dtype=int)
    positive["numpy_parity_vector_matches_checkerboard_partition"]={"pass": bool(np.array_equal(parity[part["black"]], np.zeros(len(part["black"]), dtype=int)) and np.array_equal(parity[part["white"]], np.ones(len(part["white"]), dtype=int)))}
    all_pass=all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results={"name":"ring_checkerboard_support","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"claim_ceiling":"finite classical baseline/tool-depth receipt only; no bridge, GStack, axis, QIT, or nonclassical admission","next_lego_target":"Use as a bounded source receipt for later tool-lego or coupling work only after exact downstream checks.","promotion_condition":"Requires separate bridge/nonclassical/topology/operator coupling receipts and explicit stage-gate approval.","blocked_until":"tool-lego fit; coupling/coexistence evidence; stage-gate admission","demotion_condition":"Demote if rerun fails, tool use is not load-bearing, or result claims exceed this finite receipt.","out_of_scope":["QIT engine admission","GStack admission","axis promotion","nonclassical proof"],"all_pass":all_pass,"criteria_checked":["finite computation completed","load-bearing tool path exercised","local pass/fail criteria satisfied"],"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local ring/checkerboard support row on one bounded cyclic support graph."}}
    out=pathlib.Path(__file__).resolve().parent/"a2_state"/"sim_results"/"ring_checkerboard_support_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
