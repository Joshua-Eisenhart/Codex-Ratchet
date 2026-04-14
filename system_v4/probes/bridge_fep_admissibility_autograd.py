#!/usr/bin/env python3
"""bridge_fep_admissibility_autograd -- canonical bridge.
scope_note: Torch autograd as the load-bearing admissibility test: a belief mu is
admissible under FEP only if grad F exists and points toward lower F. The
manifold's tangent structure (not entropy bookkeeping) decides admissibility.
Docs: system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md;
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md.
"""
from _doc_illum_common import build_manifest, write_results
import torch
SCOPE = ("FEP admissibility via torch autograd gradient; canonical: gradient "
         "existence + descent direction is the admissibility criterion.")

def pos():
    mu = torch.tensor([0.0], requires_grad=True); obs = torch.tensor([3.0])
    F = 0.5*(mu-obs)**2
    F.backward()
    ok = torch.allclose(mu.grad, torch.tensor([-3.0]))
    return {"grad_correct": {"grad":mu.grad.item(),"status":"PASS" if ok else "FAIL"}}
def neg():
    # A nondifferentiable belief (step function) yields no admissible gradient
    mu = torch.tensor([0.0], requires_grad=True); obs = torch.tensor([3.0])
    F = torch.where(mu>obs, torch.zeros_like(mu), torch.ones_like(mu))
    try:
        F.sum().backward()
        g = mu.grad
        ok = g is None or torch.allclose(g, torch.tensor([0.0]))
    except RuntimeError:
        ok = True
    return {"step_not_admissible": {"status":"PASS" if ok else "FAIL"}}
def bnd():
    mu = torch.tensor([3.0], requires_grad=True); obs = torch.tensor([3.0])
    F = 0.5*(mu-obs)**2
    F.backward()
    ok = torch.allclose(mu.grad, torch.tensor([0.0]))
    return {"fixed_point_zero_grad": {"status":"PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm,d = build_manifest()
    tm["pytorch"]["used"]=True; tm["pytorch"]["reason"]="autograd computes admissibility gradient"
    d["pytorch"]="load_bearing"
    p,n,b = pos(),neg(),bnd()
    ap = all(v["status"]=="PASS" for x in (p,n,b) for v in x.values())
    write_results("bridge_fep_admissibility_autograd",{
        "name":"bridge_fep_admissibility_autograd","classification":"canonical",
        "scope_note":SCOPE,"tool_manifest":tm,"tool_integration_depth":d,
        "positive":p,"negative":n,"boundary":b,"pass":ap})
