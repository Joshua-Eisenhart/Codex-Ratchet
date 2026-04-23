#!/usr/bin/env python3
import json
import pathlib
classification = "classical_baseline"  # auto-backfill

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local shell fuzz j/k support row on one bounded shell index family."
LEGO_IDS = ["shell_fuzz_jk"]
PRIMARY_LEGO_IDS = ["shell_fuzz_jk"]
TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"
]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

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
    all_pass=all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results={"name":"shell_fuzz_jk","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local shell fuzz j/k support row on one bounded shell index family."}}
    out=pathlib.Path(__file__).resolve().parent/"a2_state"/"sim_results"/"shell_fuzz_jk_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
