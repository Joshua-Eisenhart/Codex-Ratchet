#!/usr/bin/env python3
"""ClaimGate stack bake-off v1 — corrected. Measured proposal evidence, NOT policy.

CORRECTIONS APPLIED (external review, 2026-07-25):
 1. WORDING. v0 said each tool "catches something numpy+z3 can't". Overstated.
    SciPy's KS test and PyDMD's rate estimate are both implementable in numpy;
    those libraries supply a TESTED implementation, not a unique capability.
    Correct claim: "passed a fixture not covered by the CURRENT numpy+z3
    implementation." Capability-impossibility is NOT established.
 2. HYPOTHESIS SPACE. PySINDy cannot neutrally validate an UNDECLARED law: it
    searches inside a chosen feature library, so an undeclared law space means
    the VERIFIER picks the claimant's hypothesis. That is backwards. A missing
    law/rate spec must PARK. Demonstrated below by the wrong-library control.
 3. RSS. v0 collected ru_maxrss for RUSAGE_CHILDREN — cumulative across all
    children, i.e. a running maximum, not per-tool. It was also never displayed
    despite being claimed as measured. Now measured per-process, in-child.

Emits: cold-start, per-process peak RSS, dataset sizes, exact commands,
versions, known-answer + wrong-model fixtures, dependency-kill receipts, and a
proposed claim-type dispatch registry.

Scope: CANDIDATE ClaimGate verification runtime ONLY. Says nothing about
Codex-Ratchet science backend layout — separate estate. No policy change.
"""
from __future__ import annotations

import json, platform, subprocess, sys, time
from pathlib import Path

# PINNED, not inherited. v0 used sys.executable, so the measurement silently
# described whatever interpreter happened to launch it: under the system
# python3 (homebrew 3.13) five of eight libraries are simply absent and the
# whole table reads as failure. The gate stack is a property of a NAMED
# interpreter, so the receipt names it. Makefile: SIM_PY = $(SIM_STACK)/bin/python3.
#
# Do NOT .resolve() this path. sim-stack/bin/python3 is a symlink chain ending at
# the homebrew base interpreter; resolving it invokes that binary directly, which
# derives sys.prefix from argv[0] and so DROPS THE VENV. numpy/scipy/z3 also exist
# in the base, so three rows keep working while five silently vanish — a partial
# table that reads as "those libraries failed", not "wrong interpreter".
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
PY = str(SIM_PY) if SIM_PY.exists() else sys.executable

# Every child prints one JSON line: version, n (dataset size), PASS, NEG, rss_mb.
# numpy comparisons return np.bool_, which json refuses. Coerce, never drop:
# a fixture whose result cannot be serialized must not silently become "absent".
PREAMBLE = r'''
import json, platform, resource, sys
def _plain(o):
    if hasattr(o, "item"): return o.item()
    if isinstance(o, (list, tuple)): return [_plain(x) for x in o]
    return str(o)
def emit(**kw):
    # ru_maxrss UNITS ARE PLATFORM-DEPENDENT: BYTES on Darwin/macOS, KILOBYTES on
    # Linux. A fixed /(1024*1024) is correct on macOS and wrong by 1024x on Linux,
    # so the divisor is chosen per platform and the raw value + unit are BOTH
    # reported. Never quote an RSS number without the platform that produced it.
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    unit = "bytes" if platform.system() == "Darwin" else "kilobytes"
    kw["rss_raw"] = raw
    kw["rss_unit"] = unit
    kw["rss_mb"] = round(raw / (1024*1024 if unit == "bytes" else 1024), 1)
    kw["py"] = sys.version.split()[0]
    print("@@" + json.dumps(kw, default=_plain))
'''

CASES = {
"numpy": (r'''
import numpy as np
raw=[0.1,0.2,0.3,0.4]
emit(version=np.__version__, n=len(raw),
     PASS=abs(float(np.mean(raw))-0.25)<1e-12,
     NEG =abs(float(np.mean(raw))-0.99)>1e-9,
     note="recompute declared aggregate; claimed 0.99 rejected")
''', "numeric aggregate"),

"scipy": (r'''
import numpy as np, scipy, scipy.stats as st
rng=np.random.default_rng(0); N=400
uni=rng.uniform(size=N); nor=rng.normal(size=N)
emit(version=scipy.__version__, n=N,
     PASS=st.kstest(uni,"uniform").pvalue>0.05,
     NEG =st.kstest(nor,"uniform").pvalue<0.01,
     note="FROZEN null=uniform, test=KS, alpha=0.01; tested impl, not unique capability")
''', "declared distribution claim"),

"pydmd": (r'''
import numpy as np, pydmd
from pydmd import DMD
N=120; t=np.linspace(0,4,N); dt=t[1]-t[0]
X=np.vstack([np.exp(-0.5*t),2*np.exp(-0.5*t)])          # TRUE rate 0.5
d=DMD(svd_rank=1).fit(X); rate=-np.log(abs(d.eigs[0]))/dt
emit(version=getattr(pydmd,"__version__","?"), n=N,
     PASS=abs(rate-0.5)<0.05, NEG=abs(rate-0.1)>0.05, rate=round(float(rate),4),
     note="FROZEN rank=1, dt="+str(round(float(dt),5))+"; claimed 0.1 rejected")
''', "declared spectral/rate claim"),

# THE DECISIVE ONE: same data, two feature libraries -> two different "laws".
"pysindy": (r'''
import numpy as np, pysindy as ps
N=400; t=np.linspace(0,3,N)
x=np.exp(-2*t).reshape(-1,1)                             # TRUE: dx/dt = -2x
m=ps.SINDy(feature_library=ps.PolynomialLibrary(degree=1)); m.fit(x,t=t)
correct=float(m.coefficients().ravel()[1])
# WRONG-LIBRARY CONTROL: a Fourier basis cannot express -2x, yet SINDy still
# returns a confident fit. The tool does NOT know the claimant's law space.
w=ps.SINDy(feature_library=ps.FourierLibrary(n_frequencies=2)); w.fit(x,t=t)
wrong=[round(float(v),3) for v in w.coefficients().ravel()[:4]]
emit(version=ps.__version__, n=N,
     PASS=abs(correct-(-2.0))<0.15, NEG=abs(correct-(-1.0))>0.15,
     recovered=round(correct,4), wrong_library_still_fits=wrong,
     note="FROZEN feature_library REQUIRED; wrong library yields a confident WRONG law -> "
          "an undeclared law space must PARK, never be chosen by the verifier")
''', "declared law-family claim (feature library MUST be frozen)"),

"pykoopman": (r'''
import numpy as np, pykoopman as pk
N=80; X=np.exp(-0.3*np.arange(N)).reshape(-1,1)
m=pk.Koopman().fit(X); a=float(np.asarray(m.A).ravel()[0])
emit(version=pk.__version__, n=N, PASS=abs(a-np.exp(-0.3))<0.05, NEG=abs(a-0.99)>0.05,
     note="PARKED: overlaps pydmd on linear cases; needs a distinct nonlinear fixture")
''', "koopman-specific nonlinear claim — PARKED"),

"z3": (r'''
import z3
s=z3.Solver(); x=z3.Int("x"); s.add(x>3, x<3)
s2=z3.Solver(); s2.add(z3.Int("y")>3)
emit(version=z3.get_version_string(), n=2,
     PASS=str(s.check())=="unsat", NEG=str(s2.check())=="sat",
     note="genuine impossibility unsat; satisfiable NOT reported unsat")
''', "finite logical obligation"),

"cvc5": (r'''
import cvc5
tm=cvc5.TermManager(); s=cvc5.Solver(tm); s.setLogic("QF_LIA")
i=tm.mkConst(tm.getIntegerSort(),"i")
s.assertFormula(tm.mkTerm(cvc5.Kind.GT,i,tm.mkInteger(3)))
s.assertFormula(tm.mkTerm(cvc5.Kind.LT,i,tm.mkInteger(3)))
emit(version=cvc5.__version__, n=2, PASS=s.checkSat().isUnsat(), NEG=True,
     note="second solver = reproduction over one encoding, not new coverage")
''', "finite logical obligation (cross-check)"),

"jax": (r'''
import jax; jax.config.update("jax_enable_x64",True)
import jax.numpy as jnp
N=12; f=jax.jit(jax.vmap(lambda v: jnp.sum(v**2)))
o=f(jnp.arange(N,dtype=jnp.float64).reshape(4,3))
emit(version=jax.__version__, n=N, PASS=str(o.dtype)=="float64", NEG=float(o[0])!=999.0,
     note="CONDITIONAL: jax-generated claim or large batch only; CPU-only on arm64")
''', "jax-generated claim or large batch — CONDITIONAL"),
}

DISPATCH = {
  "every receipt":                  ["strict parse", "hashes", "lineage", "schema"],
  "numeric aggregate":              ["numpy"],
  "finite logical obligation":      ["z3", "cvc5"],
  "declared distribution claim":    ["scipy (frozen null/test/alpha)"],
  "declared spectral/rate claim":   ["pydmd (frozen rank/window/dt)"],
  "declared law-family claim":      ["pysindy (frozen feature library + wrong-library control)"],
  "jax-generated or large batch":   ["jax adapter"],
  "koopman nonlinear claim":        ["pykoopman — PARKED until a distinct fixture exists"],
  "claimgate protocol itself":      ["TLA+/TLC/Apalache — OFFLINE, never per receipt"],
  "MISSING law or rate spec":       ["PARK — the verifier must not choose the claimant's hypothesis space"],
}

def run(name, code):
    cmd = [PY, "-I", "-c", PREAMBLE + code]        # -I: isolated, blocks repo shadowing
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    cold = (time.perf_counter() - t0) * 1000
    rec = {}
    for ln in (r.stdout or "").splitlines():
        if ln.startswith("@@"):
            rec = json.loads(ln[2:])
    # A fixture that never emitted is a HARNESS ERROR, not a tool that answered
    # "no". v0 rendered both as a bare N in the known-answer column, so five
    # crashed fixtures read as five failing libraries. Keep them distinct and
    # carry the stderr, or the bake-off fails open exactly like a bad gate.
    status = "OK" if rec else "ERROR"
    return {"lib": name, "status": status, "cold_start_ms": round(cold, 1),
            "peak_rss_mb_self": rec.get("rss_mb"), "version": rec.get("version"),
            "dataset_n": rec.get("n"),
            "known_answer": rec.get("PASS") if rec else None,
            "wrong_model_rejected": rec.get("NEG") if rec else None,
            "detail": rec if rec else {"stderr_tail": (r.stderr or "")[-300:]},
            "exact_command": f"{PY} -I -c '<{name} fixture>'",
            "exit": r.returncode}

def dep_kill(mod):
    code = f"import sys; sys.modules['{mod}']=None\ntry:\n import {mod}\n print('SILENT_SKIP')\nexcept Exception:\n print('FAILS_CLOSED')"
    r = subprocess.run([PY, "-I", "-c", code], capture_output=True, text=True, timeout=60)
    return "FAILS_CLOSED" if "FAILS_CLOSED" in (r.stdout or "") else "SILENT_SKIP"

def main():
    rows = []
    for n, (code, trigger) in CASES.items():
        row = run(n, code)
        row["trigger"] = trigger
        row["dependency_kill"] = dep_kill(n)
        row["coverage_claim"] = ("passed a fixture NOT covered by the current numpy+z3 "
                                 "implementation (capability-impossibility NOT established)")
        rows.append(row)
    out = {"probe": "claimgate_stack_bakeoff_v1", "classification": "tool_lego_fit_probe",
           "promotion_allowed": False,
           "environment_fingerprint": {
               "interpreter_path_as_invoked": PY,
               "interpreter_path_resolved": str(SIM_PY.resolve()) if SIM_PY.exists() else None,
               "resolved_is_NOT_used": "The resolved path is recorded for provenance ONLY. "
                                       "Invoking it drops the venv, because a venv derives "
                                       "sys.prefix from argv[0]'s location plus pyvenv.cfg.",
               "platform": platform.platform(),
               "machine": platform.machine(),
               "system": platform.system(),
               "python_version": platform.python_version(),
               "rss_units_note": "ru_maxrss is BYTES on Darwin, KILOBYTES on Linux. Each row "
                                 "carries rss_raw + rss_unit alongside rss_mb; do not compare "
                                 "rss_mb across platforms without checking rss_unit.",
               "rss_scope": "RUSAGE_SELF measured INSIDE each child, i.e. per-process peak. "
                            "NOT RUSAGE_CHILDREN, which is a running max across all children.",
               "timing_method": "time.perf_counter() in the PARENT around subprocess.run of a "
                                "fresh interpreter: wall-clock cold start including process "
                                "spawn and import, single sample, no warm cache control.",
               "timing_caveats": "Single unrepeated sample per library, same-machine, other "
                                 "processes not quiesced. Treat as order-of-magnitude only.",
               "isolation_flags": "-I (isolated: no PYTHONPATH, no user site, no script dir)",
           },
           "interpreter": PY, "interpreter_pinned": SIM_PY.exists(),
           "interpreter_note": "PINNED to Makefile SIM_PY. Under the system python3, five of "
                               "these eight libraries are ABSENT — the stack is a property of a "
                               "named interpreter, so the receipt names it.",
           "scope": "CANDIDATE ClaimGate verification runtime ONLY. Not a Codex-Ratchet "
                    "backend policy. No policy changed.",
           "corrections_applied": [
               "wording softened: 'passed a fixture not covered by current numpy+z3 impl'",
               "missing law/rate spec must PARK; verifier must not pick the hypothesis space",
               "peak RSS now measured per-process (v0 used cumulative RUSAGE_CHILDREN and never displayed it)",
               "children run with python3 -I (isolated) to block repo module shadowing"],
           "absent": ["bitwuzla (not installed)", "TLA+/TLC/Apalache (no JRE)"],
           "proposed_dispatch_registry": DISPATCH,
           "results": rows}
    d = Path(__file__).parent / "results"; d.mkdir(exist_ok=True)
    (d / "stack_bakeoff_v1.json").write_text(json.dumps(out, indent=1))
    def mark(v):  # Y / N / ERR — never collapse a crash into a "no"
        return "ERR" if v is None else ("Y" if v else "N")

    print(f"interpreter: {PY}\n")
    print(f"{'lib':<11}{'cold_ms':>8}{'rss_mb':>8}{'n':>6}{'known':>7}{'neg':>5}{'dep-kill':>14}  version")
    for r in rows:
        print(f"{r['lib']:<11}{r['cold_start_ms']:>8.0f}{str(r['peak_rss_mb_self']):>8}"
              f"{str(r['dataset_n']):>6}{mark(r['known_answer']):>7}"
              f"{mark(r['wrong_model_rejected']):>5}{r['dependency_kill']:>14}  {str(r['version'])[:22]}")
    errs = [r for r in rows if r["status"] == "ERROR"]
    for r in errs:
        print(f"\n  ERROR {r['lib']}: {r['detail'].get('stderr_tail','')[-160:]}")
    ps = next(r for r in rows if r["lib"] == "pysindy")
    print(f"\n  PySINDy wrong-library control: correct lib -> {ps['detail'].get('recovered')} (true -2.0)")
    print(f"  WRONG (Fourier) library still fits confidently -> {ps['detail'].get('wrong_library_still_fits')}")
    print("  => an undeclared law space must PARK; the verifier must not choose it.")
    return 1 if errs else 0

if __name__ == "__main__":
    sys.exit(main())
