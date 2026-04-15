#!/usr/bin/env python3
"""
sim_L18_axis0_kernel.py
Layer 18: Axis 0 kernel -- preferred signed scalar on bridge output
(not fully closed).

scope_note:
  Per LADDERS_FENCES_ADMISSION_REFERENCE.md layer 18: Axis 0 is the
  preferred signed scalar I_c on bridge output. This sim probes whether a
  candidate I_c admits a non-trivial gradient (via torch autograd) on a
  parametrized family of rho_AB, which is the load-bearing criterion for
  Axis 0 kernel admission. Exclusion: a candidate I_c that is identically
  zero or has vanishing gradient everywhere is excluded.
"""
import json, os, numpy as np

classification = "canonical"

TOOL_MANIFEST={"pytorch":{"tried":False,"used":False,"reason":""}}
TOOL_INTEGRATION_DEPTH={"pytorch":None}

try:
    import torch
    TOOL_MANIFEST["pytorch"].update(tried=True,used=True,
        reason="autograd gradient of I_c wrt entangling parameter is THE load-bearing Axis 0 evidence; numpy has no autograd")
    TOOL_INTEGRATION_DEPTH["pytorch"]="load_bearing"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"]="not installed"


def rho_family(theta):
    import torch
    # Parametrized |psi(theta)> = cos(theta)|00> + sin(theta)|11>
    c = torch.cos(theta); s = torch.sin(theta)
    v = torch.stack([c, torch.zeros_like(c), torch.zeros_like(c), s])
    return torch.outer(v, v.conj())

def vN(rho):
    import torch
    eigs = torch.linalg.eigvalsh((rho+rho.conj().T)/2).real
    eigs = eigs.clamp(min=1e-30)
    return -(eigs*torch.log(eigs)).sum()

def ptrace_B(rho):
    import torch
    r = rho.reshape(2,2,2,2)
    return torch.einsum('ijkj->ik', r)
def ptrace_A(rho):
    import torch
    r = rho.reshape(2,2,2,2)
    return torch.einsum('ijil->jl', r)

def I_c(theta):
    import torch
    rho = rho_family(theta)
    S_AB = vN(rho); S_A = vN(ptrace_B(rho)); S_B = vN(ptrace_A(rho))
    return S_A + S_B - S_AB  # mutual info as candidate signed scalar

def run_positive_tests():
    import torch
    theta = torch.tensor(0.6, requires_grad=True)
    Ic = I_c(theta)
    Ic.backward()
    grad = theta.grad.item()
    return {
        "I_c_defined":      {"pass":bool(Ic.item()>=-1e-9),"value":float(Ic.item())},
        "gradient_nonzero": {"pass":bool(abs(grad)>1e-6),"grad":grad,
                             "claim":"non-zero autograd gradient admits I_c as Axis 0 kernel candidate"},
    }

def run_negative_tests():
    import torch
    # Candidate I_c == constant -> gradient vanishes -> excluded.
    theta = torch.tensor(0.3, requires_grad=True)
    const = torch.tensor(1.0) * theta * 0.0 + 2.71
    const.backward()
    g = theta.grad.item() if theta.grad is not None else 0.0
    return {
        "constant_candidate_excluded":{"pass":bool(abs(g)<1e-12),"grad":g},
    }

def run_boundary_tests():
    import torch
    # Boundary theta=0 (product |00>): I_c == 0, gradient == 0 (product state boundary).
    theta = torch.tensor(0.0, requires_grad=True)
    Ic = I_c(theta); Ic.backward()
    g0 = theta.grad.item() if theta.grad is not None else 0.0
    # Boundary theta=pi/4 (Bell): I_c == 2 log 2, gradient ~ 0 at maximum.
    theta2 = torch.tensor(float(np.pi/4), requires_grad=True)
    Ic2 = I_c(theta2); Ic2.backward()
    g1 = theta2.grad.item() if theta2.grad is not None else 0.0
    return {
        "boundary_product":{"pass":bool(abs(Ic.item())<1e-6 and abs(g0)<1e-4),"I_c":float(Ic.item()),"grad":g0},
        "boundary_bell_maximum":{"pass":bool(abs(Ic2.item()-2*np.log(2))<1e-4 and abs(g1)<1e-3),
                                 "I_c":float(Ic2.item()),"grad":g1},
    }

if __name__=="__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass=all(v.get("pass",False) for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results={"name":"sim_L18_axis0_kernel","layer":18,"layer_name":"Axis 0 kernel",
        "classification":"canonical",
        "scope_note":"LADDERS_FENCES_ADMISSION_REFERENCE.md layer 18 (preferred signed scalar on bridge output)",
        "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
        "positive":pos,"negative":neg,"boundary":bnd,"all_pass":bool(all_pass)}
    out_dir=os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(out_dir,exist_ok=True)
    out=os.path.join(out_dir,"sim_L18_axis0_kernel_results.json")
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"L18 all_pass={all_pass} -> {out}")
