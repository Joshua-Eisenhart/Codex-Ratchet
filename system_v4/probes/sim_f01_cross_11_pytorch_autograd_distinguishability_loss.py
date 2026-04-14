#!/usr/bin/env python3
"""F01 cross 11: pytorch autograd differentiates a distinguishability loss; gradient vanishes iff states indistinguishable.
pytorch load-bearing: autograd.
"""
import json, os, torch

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["pytorch"] = {"tried":True,"used":True,"reason":"autograd through distinguishability loss; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"pytorch":"load_bearing"}

def distinguishability_loss(a, b):
    # squared L2 distance; vanishes iff a=b
    return ((a-b)**2).sum()

def run_positive_tests():
    a = torch.tensor([1.0,0.0,0.0], requires_grad=True)
    b = torch.tensor([0.0,1.0,0.0], requires_grad=True)
    L = distinguishability_loss(a,b)
    L.backward()
    return {"loss_positive": L.item() > 0,
            "grad_a_nonzero": a.grad.abs().sum().item() > 0,
            "grad_b_nonzero": b.grad.abs().sum().item() > 0}

def run_negative_tests():
    # Identical states -> L=0, grad=0
    a = torch.tensor([1.0,2.0,3.0], requires_grad=True)
    b = torch.tensor([1.0,2.0,3.0], requires_grad=True)
    L = distinguishability_loss(a,b)
    L.backward()
    return {"loss_zero": abs(L.item()) < 1e-9,
            "grad_zero": a.grad.abs().sum().item() < 1e-9}

def run_boundary_tests():
    # Near-equal states: loss tiny, grad tiny but finite
    a = torch.tensor([1.0,0.0,0.0], requires_grad=True)
    b = torch.tensor([1.0+1e-4,0.0,0.0], requires_grad=True)
    L = distinguishability_loss(a,b)
    L.backward()
    return {"loss_tiny_positive": 0 < L.item() < 1e-6,
            "grad_scales_with_diff": a.grad.abs().sum().item() > 0}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"f01_cross_11_pytorch_autograd_distinguishability_loss","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"f01_cross_11_pytorch_autograd_distinguishability_loss_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
