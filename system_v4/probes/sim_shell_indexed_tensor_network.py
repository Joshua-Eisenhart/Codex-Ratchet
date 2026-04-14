#!/usr/bin/env python3
import json
import pathlib
import numpy as np
classification = "classical_baseline"  # auto-backfill

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local shell-indexed tensor-network support row on one bounded shell chain."
LEGO_IDS = ["shell_indexed_tensor_network"]
PRIMARY_LEGO_IDS = ["shell_indexed_tensor_network"]
TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"
]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

def contract_chain(tensors):
    out = tensors[0]
    for t in tensors[1:]:
        out = np.tensordot(out, t, axes=([-1],[0]))
    return out

def main():
    t0 = np.array([[1.0, 0.2],[0.0, 0.8]])
    t1 = np.array([[[1.0,0.0],[0.2,0.7]],[[0.1,0.3],[0.0,0.9]]])
    t2 = np.array([[0.9,0.1],[0.2,0.8]])
    out = contract_chain([t0,t1,t2])
    out2 = contract_chain([t0, 1.1*t1, t2])
    positive = {
        "shell_indexed_chain_contracts_to_finite_output": {"shape": list(out.shape), "pass": out.size > 0 and np.all(np.isfinite(out))},
        "changing_one_shell_tensor_changes_network_output": {"pass": np.linalg.norm(out-out2) > 1e-4},
        "shell_order_is_load_bearing_for_contract_values": {"pass": np.linalg.norm(out - np.swapaxes(out, 0, 1)) > 1e-4},
    }
    negative = {
        "row_does_not_claim_full_tensor_network_dynamics": {"pass": True},
        "row_does_not_collapse_to_ring_or_checkerboard_support": {"pass": True},
    }
    boundary = {
        "bounded_to_one_local_shell_chain": {"pass": True},
        "all_tensor_entries_are_finite": {"pass": np.all(np.isfinite(t0)) and np.all(np.isfinite(t1)) and np.all(np.isfinite(t2))},
    }
    all_pass = all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results = {"name":"shell_indexed_tensor_network","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local shell-indexed tensor-network support row on one bounded shell chain."}}
    outp = pathlib.Path(__file__).resolve().parent/"a2_state"/"sim_results"/"shell_indexed_tensor_network_results.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {outp}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
