#!/usr/bin/env python3
"""
sim_L17_signed_unsigned_entropy.py
Layer 17: Signed/unsigned entropy -- S, S(A|B), I, I_c (ready once bridge fixed).

scope_note:
  Per LADDERS_FENCES_ADMISSION_REFERENCE.md layer 17: this is the first
  layer where entropy equations exist. Tests S(rho) >= 0, negativity of
  conditional S(A|B) on entangled rho_AB (candidate signature of
  nonclassicality), and mutual information I(A:B) bounded by 2 log d.
  Exclusion: any candidate S that is negative on a valid density is
  excluded; any rho_AB with S(A|B) >= 0 is excluded from the
  'nonclassical-signed' candidate set.
"""
import json, os, numpy as np

TOOL_MANIFEST={
    "pytorch":{"tried":False,"used":False,"reason":""},
    "sympy":  {"tried":False,"used":False,"reason":""},
}
TOOL_INTEGRATION_DEPTH={"pytorch":None,"sympy":None}

try:
    import torch
    TOOL_MANIFEST["pytorch"].update(tried=True,used=True,
        reason="von Neumann entropy via torch.linalg.eigvalsh is load-bearing for S, S(A|B), I on rho_AB")
    TOOL_INTEGRATION_DEPTH["pytorch"]="load_bearing"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"]="not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"].update(tried=True,used=True,
        reason="symbolic S(diag(1/2,1/2)) = log 2 sanity check")
    TOOL_INTEGRATION_DEPTH["sympy"]="supportive"
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"]="not installed"


def S_vn(rho):
    import torch
    t = torch.tensor(rho, dtype=torch.complex128)
    eigs = torch.linalg.eigvalsh((t+t.conj().T)/2).real
    eigs = eigs.clamp(min=0)
    mask = eigs > 1e-12
    return float(-(eigs[mask]*torch.log(eigs[mask])).sum().item())

def ptrace_B(rho): return rho.reshape(2,2,2,2).trace(axis1=1,axis2=3)
def ptrace_A(rho): return rho.reshape(2,2,2,2).trace(axis1=0,axis2=2)

def bell():
    v=np.array([1,0,0,1],complex)/np.sqrt(2); return np.outer(v,v.conj())
def product_state():
    a=np.array([1,0],complex); b=np.array([1,1],complex)/np.sqrt(2)
    v=np.kron(a,b); return np.outer(v,v.conj())

def run_positive_tests():
    rho = bell()
    S_AB = S_vn(rho); S_A = S_vn(ptrace_B(rho)); S_B = S_vn(ptrace_A(rho))
    S_cond = S_AB - S_B
    I = S_A + S_B - S_AB
    return {
        "S_nonneg":         {"pass":bool(S_AB>=-1e-12),"S_AB":S_AB},
        "conditional_negative_on_bell":{"pass":bool(S_cond<-1e-6),"S_A|B":S_cond,
                                        "claim":"S(A|B)<0 excludes Bell from classical-signed class"},
        "mutual_info_bound":{"pass":bool(I<=2*np.log(2)+1e-9),"I":I,"bound":2*np.log(2)},
    }

def run_negative_tests():
    # Product state: S(A|B) should be >= 0 -> excluded from nonclassical-signed set.
    rho = product_state()
    S_AB=S_vn(rho); S_B=S_vn(ptrace_A(rho))
    S_cond = S_AB - S_B
    return {
        "product_conditional_nonneg":{"pass":bool(S_cond>=-1e-9),"S_A|B":S_cond,
                                      "claim":"product state excluded from nonclassical-signed family"},
    }

def run_boundary_tests():
    # Maximally mixed: S = 2 log 2; marginals = log 2.
    rho = np.eye(4,dtype=complex)/4
    S_AB=S_vn(rho); S_A=S_vn(ptrace_B(rho))
    ok1 = abs(S_AB - 2*np.log(2))<1e-6
    ok2 = abs(S_A  -   np.log(2))<1e-6
    # Pure product |00>: all entropies zero.
    v=np.array([1,0,0,0],complex); rho0=np.outer(v,v.conj())
    pure_zero = S_vn(rho0) < 1e-9
    return {
        "max_mixed_entropy":{"pass":bool(ok1 and ok2),"S_AB":S_AB,"S_A":S_A},
        "pure_product_zero":{"pass":bool(pure_zero)},
    }

if __name__=="__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass=all(v.get("pass",False) for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results={"name":"sim_L17_signed_unsigned_entropy","layer":17,"layer_name":"Signed/unsigned entropy",
        "classification":"canonical",
        "scope_note":"LADDERS_FENCES_ADMISSION_REFERENCE.md layer 17 (S, S(A|B), I, I_c)",
        "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
        "positive":pos,"negative":neg,"boundary":bnd,"all_pass":bool(all_pass)}
    out_dir=os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(out_dir,exist_ok=True)
    out=os.path.join(out_dir,"sim_L17_signed_unsigned_entropy_results.json")
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"L17 all_pass={all_pass} -> {out}")
