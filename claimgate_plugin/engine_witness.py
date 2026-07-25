#!/usr/bin/env python3
"""ENGINE WITNESS — evidence that an engine RAN, not metadata saying it did.

WHAT THIS REPLACES, and why it had to be replaced. three_engine_seal's
_rerun_jax_reproduces re-executed <name>_jax.py and compared numbers. Measured by
grep over that file, it checked ZERO of: `import jax`, `jaxpr`, `make_jaxpr`,
`StableHLO`, `devices`, `__version__`. So "jax leg re-derived" meant only "a
Python script printed matching JSON". A three-line file with no imports and a
single print satisfied it. Julia was never executed at all — zero occurrences of
any Julia subprocess in the seal — so "JAX and Julia agree to 1e-13" was two
copied numbers in one JSON file.

THREE CONTROLS, none of which inspect engine internals (so none rot when JAX or
Julia change their APIs):

  PRESENCE   run the leg under a wrapper that reports sys.modules afterwards.
             The engine module must actually be loaded, with its version and
             device list recorded. A leg that never imports the engine fails.

  POISON     run the leg again with the engine's import forced to raise. The leg
             MUST fail. If it still produces the same answer without the engine
             available, the engine is decorative — this is the single strongest
             signal and needs no knowledge of what the engine does.

  MUTATION   perturb one numeric literal in the leg's source and re-run. The
             output MUST change. A leg whose numbers are invariant to its own
             source is printing constants, not computing.

  DISPATCH   count actual engine operations. Added after the first three produced
             a FALSE PASS on the obvious middle case, found by testing rather
             than reasoning: a leg reading

                 import json
                 import jax          # imported, never used
                 print(json.dumps({"spectral_gap": 1.5}))

             was reported WITNESSED. Presence passed (jax really is loaded),
             poison passed (the bare import line raises, so the leg does fail),
             and mutation passed (the printed literal IS source-dependent). None
             of the three asked whether the engine COMPUTED anything. So key
             engine entry points are wrapped with counting proxies before the leg
             runs, and a leg that invokes zero of them is decorative.

A leg passes only on PRESENCE and POISON and MUTATION and DISPATCH. Any one
failing means the engine did not do the work, whatever the receipt says.

Exit: 0 witnessed | 1 not witnessed | 2 usage.
Nonzero is a policy/infra disposition, never a scientific verdict.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
TOL = 1e-9

# Reported by the wrapper AFTER the leg runs, so it reflects real imports rather
# than a source grep (which a leg could satisfy with a comment).
_PRESENCE_WRAPPER = r'''
import json, runpy, sys
_ENG = {eng!r}
_CALLS = {{}}

def _instrument(mod, names, label):
    """Wrap callables with counting proxies. The leg imports the SAME module
    object, so its calls go through these."""
    for n in names:
        try:
            f = getattr(mod, n)
        except AttributeError:
            continue
        if not callable(f):
            continue
        def make(fn, key):
            def proxy(*a, **k):
                _CALLS[key] = _CALLS.get(key, 0) + 1
                return fn(*a, **k)
            return proxy
        try:
            setattr(mod, n, make(f, f"{{label}}.{{n}}"))
        except Exception:
            pass

if _ENG == "jax":
    try:
        import jax, jax.numpy as _jnp
        _instrument(_jnp, ["array","asarray","dot","matmul","sum","mean","trace","exp",
                           "log","sqrt","abs","zeros","ones","linspace","arange","einsum",
                           "concatenate","stack","reshape","where","max","min"], "jnp")
        _instrument(jax, ["jit","grad","vmap","pmap","value_and_grad","devices"], "jax")
        for sub, fns in (("linalg", ["eigvalsh","eigh","eig","svd","inv","solve","norm","det"]),):
            try:
                _instrument(getattr(_jnp, sub), fns, f"jnp.{{sub}}")
            except Exception:
                pass
    except Exception as e:
        sys.stderr.write("@@INSTRUMENT_FAILED" + str(e) + "\n")

try:
    runpy.run_path({leg!r}, run_name="__main__")
finally:
    mods = sorted(m for m in sys.modules if m.split(".")[0] == _ENG)
    info = {{"engine_modules": mods[:12], "loaded": bool(mods),
            "dispatch_counts": dict(sorted(_CALLS.items())),
            "dispatch_total": sum(_CALLS.values())}}
    if _ENG == "jax" and "jax" in sys.modules:
        j = sys.modules["jax"]
        info["version"] = getattr(j, "__version__", None)
        try:
            info["devices"] = [str(d) for d in j.devices()]
        except Exception as e:
            info["devices_error"] = str(e)
    sys.stderr.write("@@WITNESS" + json.dumps(info) + "\n")
'''

# Makes `import <eng>` raise. Placed FIRST on sys.path via a real directory so it
# wins over the installed package without touching the environment permanently.
_POISON_MODULE = 'raise ImportError("engine poisoned by claimgate engine_witness")\n'


def _run(argv, cwd=REPO, timeout=900):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, cwd=str(cwd), timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except Exception as exc:  # noqa: BLE001
        return None, "", f"dispatch failed: {exc}"


def _last_json(text):
    for ln in reversed((text or "").splitlines()):
        ln = ln.strip()
        if ln.startswith("{"):
            try:
                return json.loads(ln)
            except json.JSONDecodeError:
                continue
    return None


def _numeric_flat(obj, prefix="", out=None):
    out = {} if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            _numeric_flat(v, f"{prefix}.{k}" if prefix else str(k), out)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out[prefix] = float(obj)
    return out


def presence(leg: Path, eng: str):
    """Run the leg; require the engine module to be loaded afterwards."""
    code = _PRESENCE_WRAPPER.format(eng=eng, leg=str(leg))
    rc, out, err = _run([SIM_PY, "-c", code])
    if rc is None or rc != 0:
        return False, {"error": f"leg exit {rc}: {(err or '')[-200:]}"}
    info = {}
    for ln in (err or "").splitlines():
        if ln.startswith("@@WITNESS"):
            info = json.loads(ln[len("@@WITNESS"):])
    result = _last_json(out)
    # HONEST LABELLING. For an instrumented engine the harness must import the
    # module itself in order to wrap its entry points, so `loaded` is true even
    # for a leg that never mentions the engine. Saying "imported but unused" about
    # such a leg would be a false description of the evidence. Module presence is
    # therefore NOT a verdict for instrumented engines; DISPATCH is. Whether the
    # leg's own source imports the engine is reported separately, from the source.
    info["harness_preloaded_for_instrumentation"] = (eng == "jax")
    info["leg_source_imports_engine"] = bool(
        re.search(rf"^\s*(import\s+{eng}|from\s+{eng})", leg.read_text(), re.M))
    if not info.get("loaded"):
        return False, {"error": f"leg ran but {eng} is not in sys.modules; "
                                f"'{eng} load_bearing' is not supported by execution",
                       "witness": info}
    return True, {"witness": info, "output": result}


def poison(leg: Path, eng: str):
    """Force `import <eng>` to raise. The leg MUST fail."""
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / f"{eng}.py").write_text(_POISON_MODULE)
        code = (f"import sys; sys.path.insert(0, {td!r})\n"
                f"import runpy; runpy.run_path({str(leg)!r}, run_name='__main__')\n")
        rc, out, err = _run([SIM_PY, "-c", code])
    if rc == 0:
        return False, {"error": f"leg SUCCEEDED with {eng} unavailable — the engine is "
                                f"decorative; its output does not depend on it",
                       "output_without_engine": _last_json(out)}
    return True, {"failed_closed_exit": rc, "detail": (err or "")[-160:]}


def mutation(leg: Path, eng: str, baseline: dict):
    """Perturb one numeric literal in the source; the output MUST change."""
    src = leg.read_text()
    # Pick the last standalone float/int literal that is not an index-ish 0/1.
    cands = [m for m in re.finditer(r"(?<![\w.])(\d+\.\d+|\d{2,})(?![\w.])", src)
             if m.group(1) not in ("0", "1")]
    if not cands:
        return None, {"skipped": "no perturbable numeric literal in the leg source"}
    m = cands[-1]
    try:
        val = float(m.group(1))
    except ValueError:
        return None, {"skipped": "unparseable literal"}
    mutated = src[:m.start(1)] + repr(val * 1.7 + 0.31) + src[m.end(1):]
    with tempfile.TemporaryDirectory() as td:
        mleg = Path(td) / leg.name
        mleg.write_text(mutated)
        rc, out, err = _run([SIM_PY, str(mleg)])
    if rc != 0:
        # A mutation that breaks the leg still proves the source is load-bearing.
        return True, {"mutated_literal": m.group(1), "effect": f"leg failed (exit {rc}) — "
                      f"source is load-bearing"}
    fresh = _numeric_flat(_last_json(out) or {})
    base = _numeric_flat(baseline or {})
    shared = set(fresh) & set(base)
    if not shared:
        return None, {"skipped": "mutated run shares no numeric field with the baseline"}
    changed = [k for k in shared if abs(fresh[k] - base[k]) > TOL]
    if not changed:
        return False, {"error": f"perturbing literal {m.group(1)} changed NOTHING in "
                                f"{sorted(shared)[:6]} — the leg prints constants rather than "
                                f"computing from its own source",
                       "mutated_literal": m.group(1)}
    return True, {"mutated_literal": m.group(1), "fields_that_moved": changed[:6]}


def witness_leg(leg: Path, eng: str) -> tuple[bool, dict]:
    rep = {"engine": eng, "leg": str(leg.relative_to(REPO)) if leg.is_relative_to(REPO) else str(leg)}
    if not leg.exists():
        return False, {**rep, "verdict": "NO_LEG",
                       "error": f"{eng} declared load_bearing but no runnable leg at {leg.name}"}
    ok_p, det_p = presence(leg, eng)
    rep["presence"] = det_p
    if not ok_p:
        return False, {**rep, "verdict": "NOT_PRESENT"}
    # DISPATCH — the control that closes the decorative-import false pass.
    w = det_p.get("witness") or {}
    if eng == "jax":
        if "dispatch_total" not in w:
            return False, {**rep, "verdict": "DISPATCH_UNMEASURED",
                           "error": "instrumentation did not report a dispatch count; "
                                    "unmeasured is not a pass"}
        if w.get("dispatch_total", 0) <= 0:
            verdict = ("DECORATIVE_IMPORT" if w.get("leg_source_imports_engine")
                       else "ENGINE_NEVER_USED")
            return False, {**rep, "verdict": verdict,
                           "error": f"ZERO {eng} operations were invoked, so the numbers do "
                                    f"not come from the engine"
                                    + (f". The leg does import {eng}, but never calls it."
                                       if w.get("leg_source_imports_engine")
                                       else f". The leg does not import {eng} at all.")}
    ok_k, det_k = poison(leg, eng)
    rep["poison_control"] = det_k
    if not ok_k:
        return False, {**rep, "verdict": "DECORATIVE"}
    ok_m, det_m = mutation(leg, eng, det_p.get("output"))
    rep["mutation_control"] = det_m
    if ok_m is False:
        return False, {**rep, "verdict": "PRINTS_CONSTANTS"}
    if ok_m is None:
        return False, {**rep, "verdict": "MUTATION_INCONCLUSIVE",
                       "error": "the mutation control could not run, so 'computed' is "
                                "unverified. Inconclusive is not a pass."}
    return True, {**rep, "verdict": "WITNESSED"}


def main(argv):
    if len(argv) != 3:
        print("usage: engine_witness.py <leg.py> <engine-module>", file=sys.stderr)
        return 2
    ok, rep = witness_leg(Path(argv[1]).resolve(), argv[2])
    print(json.dumps(rep, indent=1))
    print(f"engine_witness: {rep['verdict']} for {argv[2]}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
