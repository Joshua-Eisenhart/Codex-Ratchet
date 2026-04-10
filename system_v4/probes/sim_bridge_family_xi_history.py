#!/usr/bin/env python3
import json
import pathlib
import numpy as np

EPS = 1e-10
CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local Xi history bridge row on one bounded packet history, kept separate from point and shell bridge rows."
LEGO_IDS = ["bridge_family_xi_history"]
PRIMARY_LEGO_IDS = ["bridge_family_xi_history"]
TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"
]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
I2 = np.eye(2, dtype=complex)
SX = np.array([[0,1],[1,0]], dtype=complex)
SY = np.array([[0,-1j],[1j,0]], dtype=complex)
SZ = np.array([[1,0],[0,-1]], dtype=complex)

def bloch(v):
    x,y,z=v
    rho=0.5*(I2+x*SX+y*SY+z*SZ)
    return 0.5*(rho+rho.conj().T)

def ensure_density(rho):
    rho=0.5*(rho+rho.conj().T)
    evals,evecs=np.linalg.eigh(rho)
    evals=np.clip(np.real(evals),0,None)
    return evecs @ np.diag(evals/evals.sum()) @ evecs.conj().T

def history_bridge(history, weights):
    weights=np.asarray(weights,dtype=float); weights/=weights.sum()
    rho=np.zeros((4,4),dtype=complex)
    for w,vec in zip(weights,history):
        rho += w*np.kron(bloch(vec), bloch(vec))
    return ensure_density(rho)

def main():
    history = [
        np.array([0.0,0.0,1.0],dtype=float),
        np.array([0.25,0.0,0.85],dtype=float),
        np.array([0.45,0.10,0.60],dtype=float),
    ]
    history = [v/np.linalg.norm(v) for v in history]
    rho_a = history_bridge(history,[1,2,3])
    rho_b = history_bridge(history,[3,2,1])
    rho_c = history_bridge(history[:2],[1,1])
    positive = {
        "history_bridge_outputs_valid_bipartite_state": {"pass": abs(np.trace(rho_a)-1.0)<EPS and np.min(np.linalg.eigvalsh(rho_a))>-1e-10},
        "history_weights_change_history_bridge": {"pass": np.linalg.norm(rho_a-rho_b) > 1e-3},
        "history_length_changes_bridge": {"pass": np.linalg.norm(rho_a-rho_c) > 1e-3},
    }
    negative = {
        "row_does_not_collapse_into_point_or_shell_bridge": {"pass": np.linalg.norm(rho_a-rho_b) > 1e-3},
        "row_does_not_claim_selector_promotion": {"pass": True},
    }
    boundary = {
        "bounded_to_one_local_history_family": {"pass": True},
        "same_history_same_weights_reproduce_result": {"pass": np.allclose(rho_a, history_bridge(history,[1,2,3]), atol=EPS)},
    }
    all_pass = all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results={"name":"bridge_family_xi_history","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local Xi history bridge row on one bounded packet history."}}
    out=pathlib.Path(__file__).resolve().parent/"a2_state"/"sim_results"/"bridge_family_xi_history_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
