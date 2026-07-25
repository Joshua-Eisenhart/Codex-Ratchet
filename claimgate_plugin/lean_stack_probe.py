#!/usr/bin/env python3
"""Can a LEAN slice run ClaimGate's gates? Test, don't theorize.

ClaimGate's numpy rule is set by the owner and is INDEPENDENT of Codex-Ratchet's
science numpy rule. Here numpy is allowed. No Julia, no PyTorch.

Each row does a real GATE job (recompute / veto / decide) and is timed.
"""
from __future__ import annotations
import json, time, sys
from pathlib import Path

R = []
def probe(name, fn):
    t = time.perf_counter()
    try:
        detail = fn()
        R.append({"lib": name, "ok": True, "ms": round((time.perf_counter()-t)*1000, 1), "gate_job": detail})
    except Exception as e:
        R.append({"lib": name, "ok": False, "ms": round((time.perf_counter()-t)*1000, 1),
                  "gate_job": f"UNAVAILABLE/FAILED: {type(e).__name__}: {str(e)[:90]}"})

# ---- numeric recompute + veto -------------------------------------------
def _numpy():
    import numpy as np
    claimed = 0.5
    raw = [0.1, 0.2, 0.3, 0.4]
    actual = float(np.mean(raw))
    return f"recompute mean: claimed {claimed} vs actual {actual} -> VETO={actual != claimed}"

def _scipy():
    import scipy.stats as st
    # gate job: is a claimed distribution consistent with the raw sample?
    p = float(st.kstest([0.1,0.2,0.3,0.4,0.5], "uniform").pvalue)
    return f"KS consistency of claimed uniform: p={p:.4f}"

def _jax():
    import jax; jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    f = jax.jit(jax.vmap(lambda v: jnp.sum(v**2)))
    out = f(jnp.arange(12, dtype=jnp.float64).reshape(4,3))
    return f"x64 batched recompute, dtype={out.dtype}, n={out.shape[0]}"

def _numba():
    from numba import njit
    @njit(cache=False)
    def s(a):
        t = 0.0
        for x in a: t += x
        return t
    import numpy as np
    return f"ordered (non-reassociated) sum = {s(np.array([1e16,1.0,-1e16]))}"

# ---- SMT / exact --------------------------------------------------------
def _z3():
    import z3
    x = z3.Real("x"); s = z3.Solver(); s.add(x*x == 2, x > 0)
    return f"finite obligation: {s.check()}"

def _cvc5():
    import cvc5
    tm = cvc5.TermManager(); sv = cvc5.Solver(tm); sv.setLogic("QF_LIA")
    i = tm.mkConst(tm.getIntegerSort(), "i")
    sv.assertFormula(tm.mkTerm(cvc5.Kind.GT, i, tm.mkInteger(3)))
    return f"second solver: {'sat' if sv.checkSat().isSat() else 'unsat'}"

def _sympy():
    import sympy as sp
    x = sp.symbols("x")
    return f"exact identity check: {sp.simplify(sp.sin(x)**2+sp.cos(x)**2) == 1}"

def _galois():
    import galois
    GF = galois.GF(2**8)
    return f"exact finite field: GF(256) 3*7 = {GF(3)*GF(7)}"

# ---- fast consistency vetoes (the pysindy family) ----------------------
def _pysindy():
    import numpy as np, pysindy as ps
    t = np.linspace(0, 2, 200); x = np.exp(-t).reshape(-1, 1)   # dx/dt = -x
    m = ps.SINDy(); m.fit(x, t=t)
    c = m.coefficients()
    return f"claimed-law-vs-data veto: recovered coeff {c.ravel()[:2].round(3).tolist()} (truth -1)"

def _pydmd():
    import numpy as np
    from pydmd import DMD
    t = np.linspace(0, 4, 80)
    X = np.vstack([np.exp(-0.5*t), 2*np.exp(-0.5*t)])
    d = DMD(svd_rank=1).fit(X)
    return f"spectral consistency: |eig|={abs(d.eigs[0]):.4f}"

def _pykoopman():
    import numpy as np, pykoopman as pk
    X = np.exp(-0.1*np.arange(60)).reshape(-1,1)
    mdl = pk.Koopman().fit(X)
    return f"koopman operator fitted, shape {np.shape(mdl.A)}"

for n, f in [("numpy", _numpy), ("scipy", _scipy), ("jax(x64)", _jax), ("numba", _numba),
             ("z3", _z3), ("cvc5", _cvc5), ("sympy", _sympy), ("galois", _galois),
             ("pysindy", _pysindy), ("pydmd", _pydmd), ("pykoopman", _pykoopman)]:
    probe(n, f)

out = {"probe": "claimgate_lean_stack_v0", "classification": "tool_lego_fit_probe",
       "promotion_allowed": False,
       "note": "ClaimGate lane only. numpy ALLOWED here by owner rule; independent of CR science rule.",
       "no_julia": True, "no_pytorch": True, "results": R,
       "available": sum(1 for r in R if r["ok"]), "total": len(R)}
Path(__file__).parent.joinpath("results").mkdir(exist_ok=True)
Path(__file__).parent.joinpath("results/lean_stack_v0.json").write_text(json.dumps(out, indent=1))
for r in R:
    print(f"  {'OK ' if r['ok'] else 'XX '} {r['lib']:<10} {r['ms']:>8.1f}ms  {r['gate_job']}")
print(f"\n  {out['available']}/{out['total']} available")
sys.exit(0)
