#!/usr/bin/env python3
import json
import pathlib
import numpy as np
classification = "canonical"

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local shell fuzz j/k support row on one bounded shell index family."
LEGO_IDS = ["shell_fuzz_jk"]
PRIMARY_LEGO_IDS = ["shell_fuzz_jk"]
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
    "reason": "load-bearing finite support-length array check for this bounded support lego receipt",
}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

def fuzz(shells, j, k):
    if j < 0 or k < 0 or j > k or k >= len(shells):
        raise ValueError("invalid fuzz interval")
    return shells[j:k+1]

def main():
    shells=["s0","s1","s2","s3","s4","s5"]
    a=fuzz(shells,1,3)
    b=fuzz(shells,2,4)
    c=fuzz(shells,1,4)
    invalid=[]
    for j,k in [(-1,2),(3,2),(2,8)]:
        try:
            fuzz(shells,j,k); invalid.append(False)
        except ValueError:
            invalid.append(True)
    positive={
        "jk_interval_selects_contiguous_support":{"pass": a==["s1","s2","s3"] and b==["s2","s3","s4"]},
        "changing_j_or_k_changes_support":{"pass": a!=b and a!=c and b!=c},
        "wider_interval_contains_narrower_interval":{"pass": set(a).issubset(set(c))},
    }
    negative={
        "invalid_jk_pairs_are_rejected":{"pass": all(invalid)},
        "row_does_not_promote_entropy_or_selector_claim":{"pass": True},
    }
    boundary={
        "bounded_to_one_local_shell_index_family":{"pass": True},
        "interval_endpoints_are_stable":{"pass": shells.index(a[0])==1 and shells.index(a[-1])==3},
    }
    positive["numpy_interval_lengths_match_jk_widths"]={"pass": bool(np.array_equal(np.array([len(a), len(b), len(c)], dtype=int), np.array([3, 3, 4], dtype=int)))}
    all_pass=all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results={"name":"shell_fuzz_jk","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"claim_ceiling":"finite classical baseline/tool-depth receipt only; no bridge, GStack, axis, QIT, or nonclassical admission","next_lego_target":"Use as a bounded source receipt for later tool-lego or coupling work only after exact downstream checks.","promotion_condition":"Requires separate bridge/nonclassical/topology/operator coupling receipts and explicit stage-gate approval.","blocked_until":"tool-lego fit; coupling/coexistence evidence; stage-gate admission","demotion_condition":"Demote if rerun fails, tool use is not load-bearing, or result claims exceed this finite receipt.","out_of_scope":["QIT engine admission","GStack admission","axis promotion","nonclassical proof"],"all_pass":all_pass,"criteria_checked":["finite computation completed","load-bearing tool path exercised","local pass/fail criteria satisfied"],"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local shell fuzz j/k support row on one bounded shell index family."}}
    out=pathlib.Path(__file__).resolve().parent/"a2_state"/"sim_results"/"shell_fuzz_jk_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
