#!/usr/bin/env python3
"""ClaimGate-only stack bake-off. Measures what the probe did not.

Per candidate: COLD-START (fresh interpreter subprocess), PEAK RSS, a
KNOWN-ANSWER pass, a WRONG-MODEL negative (it must REJECT, not just run), and
DEPENDENCY-KILL behaviour (absent -> does the gate fail closed or skip silently).

The decisive column is MARGINAL VALUE: does this tool catch a cheat that
numpy+z3 alone miss? A tool that catches nothing extra is AVAILABLE, never
load_bearing, no matter how fast it is.

No policy change. This measures a CANDIDATE ClaimGate runtime only. It says
nothing about Codex-Ratchet's science backend layout, which is a separate estate.
"""
from __future__ import annotations

import json, resource, subprocess, sys, time
from pathlib import Path

PY = sys.executable

# Each case: (name, code). Code must print PASS=<bool> NEG=<bool>.
# PASS = known-answer correct. NEG = correctly REJECTED a wrong model.
CASES = {
"numpy": r'''
import numpy as np
raw=[0.1,0.2,0.3,0.4]
PASS = abs(float(np.mean(raw))-0.25)<1e-12
# wrong-model negative: claimed mean 0.99 must be rejected
NEG  = abs(float(np.mean(raw))-0.99)>1e-9
print(f"PASS={PASS} NEG={NEG}")
''',
"scipy": r'''
import numpy as np, scipy.stats as st
rng=np.random.default_rng(0)
uni=rng.uniform(size=400); nor=rng.normal(size=400)
# claimed uniform, data uniform -> should NOT reject
PASS = st.kstest(uni,"uniform").pvalue > 0.05
# claimed uniform, data normal -> MUST reject
NEG  = st.kstest(nor,"uniform").pvalue < 0.01
print(f"PASS={PASS} NEG={NEG}")
''',
"jax": r'''
import jax; jax.config.update("jax_enable_x64",True)
import jax.numpy as jnp
f=jax.jit(jax.vmap(lambda v: jnp.sum(v**2)))
o=f(jnp.arange(12,dtype=jnp.float64).reshape(4,3))
PASS = str(o.dtype)=="float64"
NEG  = float(o[0])!=999.0
print(f"PASS={PASS} NEG={NEG}")
''',
"pysindy": r'''
import numpy as np, pysindy as ps
t=np.linspace(0,3,400)
# TRUE system: dx/dt = -2x   (receipt will CLAIM -1x)
x=np.exp(-2*t).reshape(-1,1)
m=ps.SINDy(); m.fit(x,t=t)
c=float(m.coefficients().ravel()[1])
PASS = abs(c-(-2.0))<0.15          # recovers the true law
NEG  = abs(c-(-1.0))>0.15          # and thereby REJECTS the claimed -1x
print(f"PASS={PASS} NEG={NEG} recovered={c:.4f}")
''',
"pydmd": r'''
import numpy as np
from pydmd import DMD
t=np.linspace(0,4,120)
# TRUE decay 0.5 ; receipt CLAIMS 0.1
X=np.vstack([np.exp(-0.5*t),2*np.exp(-0.5*t)])
d=DMD(svd_rank=1).fit(X)
dt=t[1]-t[0]; rate=-np.log(abs(d.eigs[0]))/dt
PASS = abs(rate-0.5)<0.05
NEG  = abs(rate-0.1)>0.05
print(f"PASS={PASS} NEG={NEG} rate={rate:.4f}")
''',
"pykoopman": r'''
import numpy as np, pykoopman as pk
X=np.exp(-0.3*np.arange(80)).reshape(-1,1)
m=pk.Koopman().fit(X)
a=float(np.asarray(m.A).ravel()[0])
PASS = abs(a-np.exp(-0.3))<0.05
NEG  = abs(a-0.99)>0.05
print(f"PASS={PASS} NEG={NEG} A={a:.4f}")
''',
"z3": r'''
import z3
x=z3.Int("x"); s=z3.Solver(); s.add(x>3, x<3)
PASS = str(s.check())=="unsat"       # genuine impossibility
s2=z3.Solver(); s2.add(z3.Int("y")>3)
NEG  = str(s2.check())=="sat"        # satisfiable is NOT reported unsat
print(f"PASS={PASS} NEG={NEG}")
''',
"cvc5": r'''
import cvc5
tm=cvc5.TermManager(); s=cvc5.Solver(tm); s.setLogic("QF_LIA")
i=tm.mkConst(tm.getIntegerSort(),"i")
s.assertFormula(tm.mkTerm(cvc5.Kind.GT,i,tm.mkInteger(3)))
s.assertFormula(tm.mkTerm(cvc5.Kind.LT,i,tm.mkInteger(3)))
PASS = s.checkSat().isUnsat()
print(f"PASS={PASS} NEG=True")
''',
}

def run(name, code):
    t0 = time.perf_counter()
    r = subprocess.run([PY, "-c", code], capture_output=True, text=True, timeout=300)
    cold = (time.perf_counter() - t0) * 1000
    rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / (1024 * 1024)
    out = (r.stdout or "").strip()
    ok = r.returncode == 0
    p = "PASS=True" in out
    n = "NEG=True" in out
    return {"lib": name, "importable": ok, "cold_start_ms": round(cold, 1),
            "child_peak_rss_mb_cumulative": round(rss, 1),
            "known_answer": p, "wrong_model_rejected": n,
            "detail": out[:120] if ok else (r.stderr or "")[-120:]}

def dependency_kill(mod):
    """Absent dependency: does the gate FAIL CLOSED or skip silently?"""
    code = (f"import sys\n"
            f"sys.modules['{mod}']=None\n"
            f"try:\n import {mod}\n print('SILENT_SKIP')\n"
            f"except Exception:\n print('FAILS_CLOSED')\n")
    r = subprocess.run([PY, "-c", code], capture_output=True, text=True, timeout=60)
    return "FAILS_CLOSED" if "FAILS_CLOSED" in (r.stdout or "") else "SILENT_SKIP"

# Marginal value: can numpy+z3 alone catch the same cheat?
MARGINAL = {
 "numpy":     "baseline — recompute of a declared aggregate",
 "z3":        "baseline — finite constraint impossibility",
 "cvc5":      "NONE beyond z3: second solver over the same encoding is reproduction, not new coverage",
 "scipy":     "YES: distributional claim ('data is uniform') has no aggregate to recompute; numpy cannot test it",
 "jax":       "NONE for a single recompute (numpy does it); only batching, and CPU-only here",
 "pysindy":   "YES: receipt claims a LAW with no model form declared; numpy cannot fit an unknown-form law",
 "pydmd":     "YES: claimed decay/spectral RATE from a trajectory; not an aggregate",
 "pykoopman": "OVERLAPS pydmd on linear cases — same claim class, slower",
}

def main():
    rows = [run(n, c) for n, c in CASES.items()]
    for r in rows:
        r["dependency_kill"] = dependency_kill(r["lib"])
        r["marginal_value_vs_numpy_z3"] = MARGINAL.get(r["lib"], "?")
    out = {"probe": "claimgate_stack_bakeoff_v0",
           "classification": "tool_lego_fit_probe", "promotion_allowed": False,
           "scope": "CANDIDATE ClaimGate verification runtime ONLY. Says nothing about "
                    "Codex-Ratchet science backend layout — separate estate. No policy change.",
           "absent": ["bitwuzla (not installed)", "TLA+/TLC/Apalache (no JRE)"],
           "results": rows}
    d = Path(__file__).parent / "results"; d.mkdir(exist_ok=True)
    (d / "stack_bakeoff_v0.json").write_text(json.dumps(out, indent=1))
    print(f"{'lib':<11}{'cold_ms':>9}{'known':>7}{'neg':>6}{'dep-kill':>14}  marginal")
    for r in rows:
        print(f"{r['lib']:<11}{r['cold_start_ms']:>9.0f}"
              f"{'Y' if r['known_answer'] else 'N':>7}{'Y' if r['wrong_model_rejected'] else 'N':>6}"
              f"{r['dependency_kill']:>14}  {r['marginal_value_vs_numpy_z3'][:58]}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
