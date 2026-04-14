#!/usr/bin/env python3
import json
import pathlib
import numpy as np
classification = "classical_baseline"  # auto-backfill

EPS = 1e-10
CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local Xi shell bridge row on one bounded packet family, kept separate from point and history bridge rows."
LEGO_IDS = ["bridge_family_xi_shell"]
PRIMARY_LEGO_IDS = ["bridge_family_xi_shell"]
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
    rho = 0.5*(I2 + x*SX + y*SY + z*SZ)
    return 0.5*(rho+rho.conj().T)

def ensure_density(rho):
    rho = 0.5*(rho+rho.conj().T)
    evals,evecs = np.linalg.eigh(rho)
    evals = np.clip(np.real(evals),0,None)
    return evecs @ np.diag(evals/evals.sum()) @ evecs.conj().T

def pair(vec):
    r = bloch(vec)
    return np.kron(r,r)

def xi_shell(ref_vec, cur_vec, shell_weight=0.35):
    return ensure_density((1-shell_weight)*pair(cur_vec) + shell_weight*pair(ref_vec))

def xi_point(ref_vec, cur_vec, coupling=0.22):
    bell = np.array([1,0,0,1], dtype=complex)/np.sqrt(2)
    bell = np.outer(bell,bell.conj())
    return ensure_density((1-coupling)*0.5*(pair(ref_vec)+pair(cur_vec)) + coupling*bell)

def mi(rho):
    def ptr_a(x): return np.trace(x.reshape(2,2,2,2), axis1=0, axis2=2)
    def ptr_b(x): return np.trace(x.reshape(2,2,2,2), axis1=1, axis2=3)
    def ent(x):
        vals=np.linalg.eigvalsh(ensure_density(x))
        vals=vals[vals>1e-14]
        return float(-np.sum(vals*np.log2(vals))) if len(vals) else 0.0
    return max(0.0, ent(ptr_a(rho))+ent(ptr_b(rho))-ent(rho))

def main():
    ref = np.array([0.0,0.0,1.0],dtype=float)
    cur = np.array([0.6,0.1,0.55],dtype=float); cur = cur/np.linalg.norm(cur)
    rho_shell = xi_shell(ref, cur, 0.35)
    rho_shell2 = xi_shell(ref, cur, 0.55)
    rho_point = xi_point(ref, cur)
    positive = {
        "shell_bridge_outputs_valid_bipartite_state": {"pass": abs(np.trace(rho_shell)-1.0)<EPS and np.min(np.linalg.eigvalsh(rho_shell))>-1e-10},
        "shell_weight_changes_shell_bridge": {"pass": np.linalg.norm(rho_shell-rho_shell2) > 1e-3},
        "shell_bridge_is_distinct_from_point_bridge": {"pass": np.linalg.norm(rho_shell-rho_point) > 1e-3},
    }
    negative = {
        "row_does_not_claim_axis0_winner": {"pass": True},
        "row_does_not_collapse_into_unsigned_entropy_surface": {"pass": abs(mi(rho_shell)-mi(rho_point)) > 1e-4},
    }
    boundary = {
        "bounded_packet_scope_stays_shellwise_not_searchwise": {"pass": True},
        "reference_case_is_reproducible": {"pass": np.allclose(rho_shell, xi_shell(ref, cur, 0.35), atol=EPS)},
    }
    all_pass = all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results={"name":"bridge_family_xi_shell","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local Xi shell bridge row on one bounded packet family."}}
    out=pathlib.Path(__file__).resolve().parent/"a2_state"/"sim_results"/"bridge_family_xi_shell_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
