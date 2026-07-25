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

CORRECTIONS APPLIED (external audit, 2026-07-25 — three MEASURED defects):
 4. DEPENDENCY KILL WAS A TAUTOLOGY. v1 ran `sys.modules['x']=None; import x`,
    which always raises, and printed FAILS_CLOSED for all eight libraries. That
    measures CPython import semantics, not whether any VERIFIER fails closed.
    Replaced by a control that runs REAL gate operations with the library
    genuinely unimportable and reads the GATE's exit code. See DEP-KILL v2.
 5. cvc5 HAD NO NEGATIVE CONTROL. Its NEG column was the literal constant True,
    so the "wrong model rejected" cell was decorative for that row while every
    other solver row was measured. cvc5 now gets a real wrong-model fixture: a
    SATISFIABLE formula that must NOT be reported unsat, checked with a model
    witness so the sat verdict is exhibited rather than trusted.
 6. THE "PINNED" INTERPRETER WAS NOT PINNED. It fell back to sys.executable when
    the venv path was absent, so the entire table could silently describe a
    different interpreter while every row still read as measured. Absence is now
    a hard error.

Emits: cold-start, per-process peak RSS, dataset sizes, exact commands,
versions, known-answer + wrong-model fixtures, gate dependency-kill receipts,
and a proposed claim-type dispatch registry.

Scope: CANDIDATE ClaimGate verification runtime ONLY. Says nothing about
Codex-Ratchet science backend layout — separate estate. No policy change.
"""
from __future__ import annotations

import json, os, platform, re, subprocess, sys, tempfile, time
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

# ABSENCE IS A HARD ERROR, NOT A FALLBACK (audit defect 3, 2026-07-25).
# v1 read `PY = str(SIM_PY) if SIM_PY.exists() else sys.executable`. That is the
# same fail-open shape this whole probe exists to expose: the receipt still said
# "interpreter_pinned", every row still printed a version and an RSS, and the
# only signal that the table described a DIFFERENT interpreter was one boolean
# nobody reads. A measurement of a named stack that quietly measures some other
# stack is worse than no measurement, because it is citable. There is no valid
# bake-off without the pinned interpreter, so refuse to produce one.
if not SIM_PY.exists():
    raise SystemExit(
        f"stack_bakeoff_v1: HARD ERROR — pinned interpreter absent: {SIM_PY}\n"
        f"  This probe measures a NAMED interpreter's stack. v1 fell back to "
        f"sys.executable here ({sys.executable}), so the whole table could "
        f"silently describe a different interpreter.\n"
        f"  Refusing to emit a receipt. Restore the sim-stack venv, or invoke a "
        f"different pinned path deliberately by editing SIM_PY.")
PY = str(SIM_PY)

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

# NEG WAS THE CONSTANT `True` HERE until 2026-07-25. Every other solver row had a
# real wrong-model fixture; this one asserted its own negative control, so the
# "wrong model rejected" cell was decorative for the one library whose entire
# job is refusing wrong models. Now it runs a SATISFIABLE formula that must NOT
# come back unsat, and pulls the MODEL WITNESS out, so the sat verdict is
# exhibited rather than trusted — the same polarity discipline z3's row uses.
"cvc5": (r'''
import cvc5
tm=cvc5.TermManager(); s=cvc5.Solver(tm); s.setLogic("QF_LIA")
i=tm.mkConst(tm.getIntegerSort(),"i")
s.assertFormula(tm.mkTerm(cvc5.Kind.GT,i,tm.mkInteger(3)))
s.assertFormula(tm.mkTerm(cvc5.Kind.LT,i,tm.mkInteger(3)))
real=s.checkSat()
# WRONG-MODEL FIXTURE: j > 3 alone is satisfiable. A solver (or an adapter bug)
# that reported this unsat would manufacture an impossibility proof out of a
# perfectly consistent claim, which is the failure mode that matters for a gate.
w=cvc5.Solver(tm); w.setOption("produce-models","true"); w.setLogic("QF_LIA")
j=tm.mkConst(tm.getIntegerSort(),"j")
w.assertFormula(tm.mkTerm(cvc5.Kind.GT,j,tm.mkInteger(3)))
wrong=w.checkSat()
emit(version=cvc5.__version__, n=2,
     PASS=real.isUnsat(), NEG=(wrong.isSat() and not wrong.isUnsat()),
     real_model_result=str(real), wrong_model_result=str(wrong),
     wrong_model_witness="j="+str(w.getValue(j)),
     note="genuine impossibility unsat; SATISFIABLE j>3 NOT reported unsat, model "
          "witness exhibited. Second solver = reproduction over one encoding, not "
          "new coverage")
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

# ============================================================== DEP-KILL v2 ===
# v1's control was a TAUTOLOGY:
#     sys.modules['x'] = None ; import x        -> always raises
# and it printed FAILS_CLOSED for all eight libraries. A None entry in
# sys.modules is a hard block by CPython's own import rules, so that check can
# only ever return FAILS_CLOSED. It measured Python, not ClaimGate. No gate was
# invoked, no gate exit code was read, and four of the eight libraries are not
# imported by any gate at all — yet every row still read FAILS_CLOSED, which is
# exactly the "convincing receipt over a real computation" shape the gate exists
# to refuse. A control that cannot fail is not a control.
#
# The question a dependency-kill control must answer is: WHEN THIS LIBRARY IS
# GONE, WHAT DOES THE GATE DO? So v2 runs REAL gate operations twice, changing
# exactly ONE variable, and reads the GATE's exit code:
#     baseline   gate op with the library importable
#     blocked    same gate op, same argv, same cwd, same PYTHONPATH, with the
#                library made genuinely unimportable
# Both arms carry the blocker directory on PYTHONPATH and neither uses -I, so
# the only difference between them is the CLAIMGATE_DEPKILL_MODULE variable.
# Otherwise a changed exit could come from the isolation flag rather than the
# missing library.
#
# FIDELITY CEILING, stated because it is real: absence is simulated at the
# IMPORT BOUNDARY, not by uninstalling the package. The gate receives exactly
# the ModuleNotFoundError an uninstalled package produces, and the blocker is
# VERIFIED to fire before any verdict is recorded — but the files remain on
# disk. A control whose own precondition is unverified is not a pass, so a
# blocker that does not fire yields BLOCKER_FAILED, never a quiet FAILS_CLOSED.
_BLOCKER = r'''
import os, sys
_t = os.environ.get("CLAIMGATE_DEPKILL_MODULE")
if _t:
    import importlib.abc
    class _Absent(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            if name == _t or name.startswith(_t + "."):
                raise ModuleNotFoundError("No module named %r" % name, name=name)
            return None
    sys.meta_path.insert(0, _Absent())
    for _m in [m for m in sys.modules if m == _t or m.startswith(_t + ".")]:
        del sys.modules[_m]
'''

PLUGIN = Path(__file__).resolve().parent
REPO = PLUGIN.parent


def _gate_inputs(tmp: Path):
    """Inputs the gate operations need, written to a temp dir, never the repo."""
    recv = tmp / "recompute_ok.json"
    recv.write_text(json.dumps({
        "classification": "tool_lego_fit_probe", "promotion_allowed": False,
        "recompute": [{"raw": "metrics.raw_x", "claim": "metrics.mean_x",
                       "op": "mean", "tol": 1e-9}],
        "metrics": {"raw_x": [0.1, 0.2, 0.3, 0.4], "mean_x": 0.25}}))
    leg = tmp / "witness_leg_jax.py"
    leg.write_text('import json\n'
                   'import jax\n'
                   'jax.config.update("jax_enable_x64", True)\n'
                   'import jax.numpy as jnp\n'
                   'v = jnp.linspace(0.0, 3.0, 7)\n'
                   'print(json.dumps({"spectral_gap": float(jnp.sum(v ** 2))}))\n')
    return recv, leg


def gate_ops(tmp: Path):
    """Real ClaimGate operations, each chosen because it EXITS 0 on a good input
    and is the gate a claim of this shape would actually meet."""
    recv, leg = _gate_inputs(tmp)
    return {
        "recompute_veto": {
            "argv": [PY, str(PLUGIN / "recompute_veto.py"), str(recv)],
            "script": PLUGIN / "recompute_veto.py", "writes": [],
            "what": "re-derives a claimed aggregate from the raw array beside it"},
        "chain_bmc_z3": {
            "argv": [PY, str(PLUGIN / "formal" / "chain_bmc_z3.py")],
            "script": PLUGIN / "formal" / "chain_bmc_z3.py",
            "writes": [PLUGIN / "formal" / "results" / "chain_bmc_v0.json"],
            "what": "bounded model check of the gate chain (z3, with a cvc5 cross-check)"},
        "chain_bmc_cvc5": {
            "argv": [PY, str(PLUGIN / "formal" / "chain_bmc_cvc5.py")],
            "script": PLUGIN / "formal" / "chain_bmc_cvc5.py",
            "writes": [PLUGIN / "formal" / "results" / "chain_bmc_cvc5_v0.json"],
            "what": "same bounded model check, cvc5 encoding"},
        "engine_witness_jax": {
            "argv": [PY, str(PLUGIN / "engine_witness.py"), str(leg), "jax"],
            "script": PLUGIN / "engine_witness.py", "writes": [],
            "what": "presence/dispatch/poison/mutation witness of a real JAX leg"},
    }


def _gate_run(op, blockdir: Path, kill=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(blockdir)          # IDENTICAL in both arms
    env.pop("CLAIMGATE_DEPKILL_MODULE", None)
    if kill:
        env["CLAIMGATE_DEPKILL_MODULE"] = kill
    try:
        p = subprocess.run(op["argv"], capture_output=True, text=True,
                           timeout=600, env=env, cwd=str(REPO))
        return p.returncode, (p.stderr or "").strip().splitlines()[-1][:160] if (p.stderr or "").strip() else ""
    except Exception as exc:                    # noqa: BLE001
        return None, f"harness dispatch failed: {exc.__class__.__name__}: {exc}"


def _blocker_fires(lib, blockdir: Path):
    """Verify the precondition of the whole control before trusting any verdict."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(blockdir)
    env["CLAIMGATE_DEPKILL_MODULE"] = lib
    try:
        p = subprocess.run([PY, "-c", f"import {lib}"], capture_output=True,
                           text=True, timeout=120, env=env)
    except Exception:                           # noqa: BLE001
        return False
    return p.returncode != 0 and "ModuleNotFoundError" in (p.stderr or "")


def _imports(script: Path, lib: str):
    """Source-level: does this gate op import the library DIRECTLY? Used only to
    separate a silent degradation (imports it, still exits 0) from a library the
    gate never touches. A grep is weak evidence, so it never decides FAILS_CLOSED
    — only exit codes do that."""
    try:
        return bool(re.search(rf"^\s*(import\s+{re.escape(lib)}|from\s+{re.escape(lib)})\b",
                              script.read_text(), re.M))
    except OSError:
        return False


def dep_kill_sweep(libs, tmp: Path):
    """-> (per-library verdicts, gate-op baselines). Reads GATE exit codes."""
    blockdir = tmp / "blockdir"
    blockdir.mkdir(exist_ok=True)
    (blockdir / "sitecustomize.py").write_text(_BLOCKER)
    ops = gate_ops(tmp)

    # A BLOCKED gate run must not leave a degraded receipt in the repo: with cvc5
    # absent, chain_bmc_z3 still writes its output, minus the cross-check. Snapshot
    # every declared output and restore it after the sweep.
    snap = {w: (w.read_bytes() if w.exists() else None)
            for op in ops.values() for w in op["writes"]}

    baselines = {}
    for name, op in ops.items():
        if not op["script"].exists():
            baselines[name] = {"exit": None, "note": f"gate script absent: {op['script']}"}
            continue
        rc, err = _gate_run(op, blockdir)
        baselines[name] = {"exit": rc, "what": op["what"], "stderr_tail": err,
                           "command": " ".join(op["argv"])}

    usable = [n for n, b in baselines.items() if b["exit"] == 0]
    out = {}
    for lib in libs:
        if not _blocker_fires(lib, blockdir):
            out[lib] = {"verdict": "BLOCKER_FAILED", "coupling": None, "evidence":
                        "the import blocker did not fire, so nothing about the gate was "
                        "measured; an unverified control is not a pass", "per_gate_op": {}}
            continue
        if not usable:
            out[lib] = {"verdict": "CONTROL_INVALID", "coupling": None, "evidence":
                        "no gate operation exits 0 at baseline, so a changed exit code "
                        "could not be attributed to the missing library", "per_gate_op": {}}
            continue
        per = {}
        for name in usable:
            rc, err = _gate_run(ops[name], blockdir, kill=lib)
            per[name] = {"baseline_exit": 0, "blocked_exit": rc,
                         "gate_imports_lib_directly": _imports(ops[name]["script"], lib),
                         "stderr_tail": err}
        closed = [n for n in usable if per[n]["blocked_exit"] not in (0, None)]
        broke = [n for n in usable if per[n]["blocked_exit"] is None]
        degraded = [n for n in usable if per[n]["blocked_exit"] == 0
                    and per[n]["gate_imports_lib_directly"]]
        if broke:
            verdict, coupling = "CONTROL_INVALID", None
            ev = f"harness could not dispatch {broke}; no exit code to read"
        elif closed:
            direct = any(per[n]["gate_imports_lib_directly"] for n in closed)
            verdict = "FAILS_CLOSED"
            coupling = "direct" if direct else "transitive"
            ev = ("; ".join(f"{n} exit 0->{per[n]['blocked_exit']}" for n in closed)
                  + ("" if direct else " (no gate op imports it directly; the coupling "
                                       "runs through another library)"))
        elif degraded:
            verdict, coupling = "FAILS_OPEN", "direct"
            ev = ("; ".join(f"{n} imports it yet still exits 0" for n in degraded)
                  + " — the gate admitted with the library absent")
        else:
            verdict, coupling = "NOT_WIRED", "none"
            ev = (f"all {len(usable)} gate operations returned an identical exit code "
                  f"with the library absent, and none imports it: no ClaimGate gate "
                  f"depends on it, so there is nothing here to fail closed")
        out[lib] = {"verdict": verdict, "coupling": coupling, "evidence": ev,
                    "silently_degraded_gate_ops": degraded, "per_gate_op": per}

    for w, b in snap.items():                   # restore, or remove if it was absent
        if b is None:
            w.unlink(missing_ok=True)
        else:
            w.write_bytes(b)
    return out, baselines

def main():
    with tempfile.TemporaryDirectory(prefix="claimgate_bakeoff_") as td:
        killed, gate_baselines = dep_kill_sweep(list(CASES), Path(td))
    rows = []
    for n, (code, trigger) in CASES.items():
        row = run(n, code)
        row["trigger"] = trigger
        row["dependency_kill"] = killed[n]["verdict"]
        row["dependency_kill_detail"] = killed[n]
        row["coverage_claim"] = ("passed a fixture NOT covered by the current numpy+z3 "
                                 "implementation (capability-impossibility NOT established)")
        rows.append(row)
    out = {"probe": "claimgate_stack_bakeoff_v1", "classification": "tool_lego_fit_probe",
           "promotion_allowed": False,
           "environment_fingerprint": {
               "interpreter_path_as_invoked": PY,
               "interpreter_path_resolved": str(SIM_PY.resolve()),
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
           "interpreter": PY, "interpreter_pinned": True,
           "interpreter_pinned_note": "True is the ONLY reachable value: absence of the pinned "
                                      "path now raises SystemExit before any measurement, so "
                                      "this field can no longer read True beside a table that "
                                      "silently describes sys.executable (v1 fell back).",
           "interpreter_note": "PINNED to Makefile SIM_PY. Under the system python3, five of "
                               "these eight libraries are ABSENT — the stack is a property of a "
                               "named interpreter, so the receipt names it.",
           "dependency_kill_control": {
               "question": "when this library is gone, what does the GATE do?",
               "method": "run a real ClaimGate gate operation twice — library importable, then "
                         "genuinely unimportable — and read the GATE's exit code. Both arms use "
                         "the same argv, cwd and PYTHONPATH; only CLAIMGATE_DEPKILL_MODULE "
                         "differs, so a changed exit cannot come from the harness.",
               "blocker": "a sitecustomize meta_path finder that raises ModuleNotFoundError for "
                          "the module and its submodules; VERIFIED to fire per library before "
                          "any verdict is recorded",
               "fidelity_ceiling": "absence is simulated at the IMPORT BOUNDARY. The gate sees "
                                   "exactly the exception an uninstalled package produces, but "
                                   "the package files remain on disk.",
               "supersedes": "v1 ran sys.modules['x']=None; import x, which ALWAYS raises. It "
                             "measured CPython import semantics, never a gate, and returned "
                             "FAILS_CLOSED for all eight libraries including four that no gate "
                             "imports. A control that cannot fail is not a control.",
               "verdicts": {
                   "FAILS_CLOSED": "a gate op that exited 0 now exits nonzero without the library",
                   "FAILS_OPEN": "a gate op imports the library yet still exits 0 without it",
                   "NOT_WIRED": "no gate op imports it and no gate exit code changed",
                   "BLOCKER_FAILED": "the blocker did not fire; nothing was measured",
                   "CONTROL_INVALID": "no clean baseline, so no attribution is possible"},
               "gate_operations": gate_baselines,
               "repo_side_effects": "outputs the gate ops write are snapshotted before the sweep "
                                    "and restored after, so a blocked run cannot leave a degraded "
                                    "receipt behind",
               "results": killed},
           "scope": "CANDIDATE ClaimGate verification runtime ONLY. Not a Codex-Ratchet "
                    "backend policy. No policy changed.",
           "corrections_applied": [
               "wording softened: 'passed a fixture not covered by current numpy+z3 impl'",
               "missing law/rate spec must PARK; verifier must not pick the hypothesis space",
               "peak RSS now measured per-process (v0 used cumulative RUSAGE_CHILDREN and never displayed it)",
               "children run with python3 -I (isolated) to block repo module shadowing",
               "dependency kill now runs REAL gate operations and reads the GATE's exit code "
               "(v1 ran sys.modules['x']=None; import x, a tautology that always raises)",
               "cvc5 negative control is now a real wrong-model fixture with a model witness "
               "(v1 hard-coded NEG=True, so the one solver row whose job is refusing wrong "
               "models had no negative control at all)",
               "absent pinned interpreter is a HARD ERROR (v1 fell back to sys.executable, so "
               "the whole table could silently describe a different interpreter)"],
           "absent": ["bitwuzla (not installed)", "TLA+/TLC/Apalache (no JRE)"],
           "proposed_dispatch_registry": DISPATCH,
           "results": rows}
    d = Path(__file__).parent / "results"; d.mkdir(exist_ok=True)
    (d / "stack_bakeoff_v1.json").write_text(json.dumps(out, indent=1))
    def mark(v):  # Y / N / ERR — never collapse a crash into a "no"
        return "ERR" if v is None else ("Y" if v else "N")

    print(f"interpreter: {PY}  (pinned; absence is a hard error, not a fallback)\n")
    print(f"{'lib':<11}{'cold_ms':>8}{'rss_mb':>8}{'n':>6}{'known':>7}{'neg':>5}{'gate-dep-kill':>16}  version")
    for r in rows:
        print(f"{r['lib']:<11}{r['cold_start_ms']:>8.0f}{str(r['peak_rss_mb_self']):>8}"
              f"{str(r['dataset_n']):>6}{mark(r['known_answer']):>7}"
              f"{mark(r['wrong_model_rejected']):>5}{r['dependency_kill']:>16}  {str(r['version'])[:22]}")
    errs = [r for r in rows if r["status"] == "ERROR"]
    for r in errs:
        print(f"\n  ERROR {r['lib']}: {r['detail'].get('stderr_tail','')[-160:]}")

    print("\ngate dependency-kill control — REAL gate operations, GATE exit codes measured")
    for name, b in gate_baselines.items():
        print(f"  baseline  {name:<20} exit={b['exit']}   {b.get('what', b.get('note',''))}")
    for lib, k in killed.items():
        print(f"  {lib:<11}{k['verdict']:<16}{str(k['coupling']):<11}{k['evidence'][:104]}")
    degraded = {l: k["silently_degraded_gate_ops"] for l, k in killed.items()
                if k.get("silently_degraded_gate_ops")}
    for lib, ops_ in degraded.items():
        print(f"  NOTE  {lib}: {ops_} import it and still exit 0 — that gate op degrades "
              f"silently, even though another one fails closed.")

    ps = next(r for r in rows if r["lib"] == "pysindy")
    print(f"\n  PySINDy wrong-library control: correct lib -> {ps['detail'].get('recovered')} (true -2.0)")
    print(f"  WRONG (Fourier) library still fits confidently -> {ps['detail'].get('wrong_library_still_fits')}")
    print("  => an undeclared law space must PARK; the verifier must not choose it.")
    cv = next(r for r in rows if r["lib"] == "cvc5")
    print(f"\n  cvc5 wrong-model control (v1 hard-coded NEG=True): real formula -> "
          f"{cv['detail'].get('real_model_result')}, satisfiable j>3 -> "
          f"{cv['detail'].get('wrong_model_result')} ({cv['detail'].get('wrong_model_witness')})")

    # A control that could not run has not passed — same doctrine the gates use.
    void = [l for l, k in killed.items()
            if k["verdict"] in ("BLOCKER_FAILED", "CONTROL_INVALID")]
    if void:
        print(f"\n  UNMEASURED dependency-kill control for {void} — not a pass.")
    open_ = [l for l, k in killed.items() if k["verdict"] == "FAILS_OPEN"]
    if open_:
        print(f"\n  FAILS OPEN: {open_} — a gate imports the library and still exits 0 "
              f"without it.")
    return 1 if (errs or void) else 0

if __name__ == "__main__":
    sys.exit(main())
