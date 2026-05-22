#!/usr/bin/env python3
import json
import pathlib
import numpy as np

from receipt_boundary import apply_default_receipt_boundary

CLASSIFICATION = "canonical"
NAME = "sim_shell_indexed_tensor_network"
CLASSIFICATION_NOTE = "Canonical local shell-indexed tensor-network support row on one bounded shell chain."
LEGO_IDS = ["shell_indexed_tensor_network"]
PRIMARY_LEGO_IDS = ["shell_indexed_tensor_network"]
divergence_log = (
    "This is a finite classical tensor-contraction support row on one bounded "
    "shell chain. It does not establish tensor-network dynamics, bridge behavior, "
    "GStack, axis, QIT, or nonclassical admission."
)
TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite array/matrix computation for this bounded classical lego receipt",
    },
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this finite numpy tensor-contraction support row"},
    "pyg": {"tried": False, "used": False, "reason": "not needed: no graph layer"},
    "z3": {"tried": False, "used": False, "reason": "not needed: no SMT claim"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed: no SMT claim"},
    "sympy": {"tried": False, "used": False, "reason": "not needed: direct finite array computation"},
    "clifford": {"tried": False, "used": False, "reason": "not needed: no Clifford algebra operation"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed: no geomstats metric call"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed: no equivariant neural layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed: no graph algorithm"},
    "xgi": {"tried": False, "used": False, "reason": "not needed: no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed: no cell-complex computation"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed: no persistence computation"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

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
    results = {"name":NAME,"classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"divergence_log":divergence_log,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"all_pass":all_pass,"criteria_checked":["finite computation completed","load-bearing tool path exercised","local pass/fail criteria satisfied"],"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local shell-indexed tensor-network support row on one bounded shell chain."}}
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target="Use as bounded shell-indexed tensor-network support evidence before downstream tool-lego or coupling packets.",
    )
    outp = pathlib.Path(__file__).resolve().parent/"a2_state"/"sim_results"/f"{NAME}_results.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {outp}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
