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

FOUR CONTROLS, none of which inspect engine internals (so none rot when JAX or
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

--------------------------------------------------------------------------------
JULIA (added here). Before this, Julia had no execution witness of any kind: the
seal invoked the julia binary zero times, so "JAX and Julia agree" was two copied
numbers in one JSON file and nothing more. Julia is a separate process, not an
importable Python module, so the four controls are re-derived for a subprocess
engine rather than copied across:

  PRESENCE   `julia --startup-file=no --color=no --trace-compile=stderr <leg.jl>`
             must exit 0 AND emit parseable JSON on stdout. Recorded: julia
             version, CPU/machine, BINDIR, the active project julia itself
             reports, and sha256 of every Project.toml / Manifest.toml found from
             the leg's directory upward. If `julia` is not on PATH the verdict is
             ENGINE_UNAVAILABLE, which BLOCKS — an absent engine is never a pass.

  DISPATCH   Julia has no import hook to wrap, so counting proxies do not apply.
             `--trace-compile=stderr` emits one `precompile(Tuple{...})` line per
             method that was compiled BECAUSE IT WAS CALLED. It can undercount
             (already-compiled methods emit nothing) but it cannot overcount, so
             it fails closed. A line counts as a NUMERIC dispatch when its
             signature mentions a numeric or array type AND its entry point is
             not an IO/printing function. Measured on this host, julia 1.12.6:

               leg computing eigvals of a 3x3 Symmetric      numeric_dispatch = 5
                 (hvcat/Float64, Symmetric{Float64,Array} ctor, LinearAlgebra.
                  eigvals, getindex(Array{Float64,1}), sum(Array{Float64,1}))
               leg printing a constant JSON string           numeric_dispatch = 0
               leg with `using LinearAlgebra` then a constant numeric_dispatch = 0
               leg printing Float64 VALUES, computing none   numeric_dispatch = 0
                 (both traced lines are Base.println / Base.print — IO, excluded)

             The last row is why the IO exclusion exists: printing a float is not
             computing with one. If the primary run scores zero, the leg is re-run
             once with `--pkgimages=no` so work hidden inside package images has
             to compile in-process. That fallback can only ADD evidence of real
             calls; trace-compile never fires without one.

  POISON     a shadow package directory goes FIRST on JULIA_LOAD_PATH, holding
             `module <Dep>; error(...); end` for every package the leg declares
             with `using` / `import`. The leg MUST fail, and the failure is
             attributed by looking for the marker string in stderr rather than
             assumed from the exit code. JULIA_DEPOT_PATH is layered
             temp-first-real-second so poisoned precompile output lands in a temp
             dir: the real depot is neither written to nor rebuilt from scratch.
             A leg declaring no package at all is run with the load path stripped
             to the empty shadow dir; if it still succeeds, its output depends on
             no Julia package and it is DECORATIVE.

  MUTATION   identical rule, different runner. The mutated copy is written as a
             SIBLING of the leg, not into a temp dir, so `@__DIR__`, relative
             `include`, and Project.toml activation still resolve. A mutant that
             failed on a path lookup would otherwise be scored "source is
             load-bearing", which is a false pass.

Exit: 0 witnessed | 1 not witnessed | 2 usage.
Nonzero is a policy/infra disposition, never a scientific verdict.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
TOL = 1e-9

SUPPORTED_ENGINES = ("jax", "julia")

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

# ------------------------------------------------------------------ julia pieces
JULIA_MARKER = "engine dependency poisoned by claimgate engine_witness"
_JULIA_POISON_MODULE = 'module {name}\nerror("' + JULIA_MARKER + '")\nend\n'
JULIA_FLAGS = ["--startup-file=no", "--color=no"]

# `using X` / `import X` / `using X: a, b` / `using X, Y`. Base and Core live in
# the sysimage and cannot be shadowed, so they are not poison targets.
_JULIA_USING = re.compile(r"^\s*(?:using|import)\s+([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)", re.M)
_JULIA_UNSHADOWABLE = {"Base", "Core", "Main"}

# One trace-compile line: precompile(Tuple{typeof(Mod.fn), ArgT, ...}), or
# precompile(Tuple{Type{Mod.T{...}}, ArgT, ...}) for a constructor call.
_TRACE_LINE = re.compile(r"^\s*precompile\(Tuple\{(.*)\}\)\s*$")
_TRACE_HEAD = re.compile(r"^\s*(?:typeof\(([^)]*)\)|Type\{\s*([A-Za-z_][\w.]*))")

# A dispatch counts as numeric when a numeric scalar, a numeric container, or a
# linear-algebra type appears anywhere in the signature. Types, not function
# names — function names rot faster than the type lattice does.
_NUMERIC_TOKEN = re.compile(
    r"Float64|Float32|Float16|BigFloat|BigInt|ComplexF64|ComplexF32|Complex\{"
    r"|Rational\{|Array\{|Matrix\{|Vector\{|SparseMatrixCSC|StaticArrays"
    r"|LinearAlgebra|SparseArrays|Hermitian|Symmetric|Diagonal|Tridiagonal"
    r"|UpperTriangular|LowerTriangular|Bidiagonal|Factorization|BLAS|LAPACK")

# Printing a Float64 is not computing with one. These entry points are excluded
# so `println(1.5)` cannot score as engine work. Short, stable, IO-only list.
_IO_ENTRYPOINTS = {
    "print", "println", "show", "display", "string", "repr", "write", "format",
    "sprint", "showerror", "print_to_string", "with_output_color", "escape_string",
    "join", "printstyled", "Format", "Spec", "text_colors",
}


def _run(argv, cwd=REPO, timeout=900, env=None):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, cwd=str(cwd),
                           timeout=timeout, env=env)
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


def _sha256(path: Path):
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        return f"unreadable: {exc}"


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


# =============================================================================
# JULIA — same four controls, re-derived for a subprocess engine
# =============================================================================

def julia_binary():
    """Resolve the julia binary. Absent is a BLOCKING verdict, never a pass."""
    return shutil.which("julia")


def julia_env(jbin: str):
    """Version and machine identity, read out of the running julia, not guessed."""
    probe = (
        'print("{\\"version\\":\\"", string(VERSION),'
        '"\\",\\"cpu\\":\\"", Sys.CPU_NAME,'
        '"\\",\\"machine\\":\\"", Sys.MACHINE,'
        '"\\",\\"bindir\\":\\"", Sys.BINDIR,'
        '"\\",\\"active_project\\":\\"", something(Base.active_project(), "none"),'
        '"\\",\\"nthreads\\":", Threads.nthreads(), "}")'
    )
    rc, out, err = _run([jbin] + JULIA_FLAGS + ["-e", probe], timeout=180)
    if rc != 0:
        return {"error": f"julia env probe exit {rc}: {(err or '')[-160:]}"}
    parsed = _last_json(out)
    return parsed if parsed is not None else {"error": f"unparseable env probe: {out[-160:]}"}


def julia_project_digests(leg: Path, active_project):
    """sha256 of every Project.toml / Manifest.toml governing this leg.

    Walked from the leg's own directory upward to the repo root, plus whatever
    project julia itself reported as active — those can differ, and a witness
    recording only one of them would be recording the wrong environment.
    """
    found, seen = {}, set()
    d = leg.parent.resolve()
    stop = REPO.resolve()
    while True:
        for name in ("Project.toml", "Manifest.toml"):
            p = d / name
            if p.is_file() and str(p) not in seen:
                seen.add(str(p))
                found[str(p)] = _sha256(p)
        if d == stop or d == d.parent:
            break
        d = d.parent
    if active_project and active_project != "none":
        ap = Path(active_project)
        if ap.is_file() and str(ap) not in seen:
            found[str(ap)] = _sha256(ap)
            man = ap.parent / "Manifest.toml"
            if man.is_file() and str(man) not in seen:
                found[str(man)] = _sha256(man)
    return found or {"note": "no Project.toml or Manifest.toml found for this leg"}


def julia_declared_packages(src: str):
    """Packages the leg pulls in. These are the poison targets."""
    names = []
    for m in _JULIA_USING.finditer(src):
        for n in m.group(1).split(","):
            n = n.strip()
            if n and n not in _JULIA_UNSHADOWABLE and n not in names:
                names.append(n)
    return names


def parse_trace(stderr_text: str):
    """Classify --trace-compile lines into total / numeric / numeric-but-IO.

    Every line here is a method that was compiled BECAUSE IT WAS CALLED. The
    count can be low (already-compiled methods emit nothing) but it cannot be
    inflated without a real call, so a zero reading fails closed.
    """
    total, numeric, io_only, samples = 0, 0, 0, []
    for ln in (stderr_text or "").splitlines():
        m = _TRACE_LINE.match(ln.strip())
        if not m:
            continue
        total += 1
        sig = m.group(1)
        head = _TRACE_HEAD.match(sig)
        fn = ((head.group(1) or head.group(2)) if head else "") or ""
        leaf = fn.split(".")[-1].strip().split("{")[0]
        is_io = leaf in _IO_ENTRYPOINTS
        if _NUMERIC_TOKEN.search(sig):
            if is_io:
                io_only += 1
            else:
                numeric += 1
                if len(samples) < 6:
                    samples.append(sig[:120])
    return {"trace_total": total, "numeric_dispatch": numeric,
            "numeric_but_io_only": io_only, "numeric_samples": samples}


def presence_julia(leg: Path, jbin: str):
    """Execute the leg under julia. It must exit 0 and emit JSON."""
    rc, out, err = _run([jbin] + JULIA_FLAGS + ["--trace-compile=stderr", str(leg)],
                        cwd=leg.parent)
    if rc is None or rc != 0:
        return False, {"error": f"leg exit {rc} under julia: {(err or '')[-240:]}",
                       "argv": f"julia {' '.join(JULIA_FLAGS)} --trace-compile=stderr {leg.name}"}
    result = _last_json(out)
    if result is None:
        return False, {"error": "leg ran under julia but emitted no parseable JSON on stdout; "
                                "an unreadable leg is not a witnessed one",
                       "stdout_tail": (out or "")[-200:]}
    env = julia_env(jbin)
    info = {
        "julia_binary": jbin,
        "julia_version": env.get("version"),
        "cpu": env.get("cpu"),
        "machine": env.get("machine"),
        "bindir": env.get("bindir"),
        "active_project": env.get("active_project"),
        "env_probe_error": env.get("error"),
        "project_digests": julia_project_digests(leg, env.get("active_project")),
        "leg_declared_packages": julia_declared_packages(leg.read_text()),
        "harness_preloaded_for_instrumentation": False,
    }
    info.update(parse_trace(err))
    # Fallback only when the primary reading is zero: package images can hide
    # real calls behind already-compiled code. Disabling them forces in-process
    # compilation, which can only ADD evidence of calls that actually happened.
    if info["numeric_dispatch"] == 0:
        rc2, _out2, err2 = _run([jbin] + JULIA_FLAGS +
                                ["--pkgimages=no", "--trace-compile=stderr", str(leg)],
                                cwd=leg.parent)
        second = parse_trace(err2)
        info["nopkgimages_rerun"] = {"exit": rc2, **second}
        if rc2 == 0 and second["numeric_dispatch"] > 0:
            info["numeric_dispatch"] = second["numeric_dispatch"]
            info["numeric_samples"] = second["numeric_samples"]
            info["dispatch_source"] = "pkgimages=no rerun"
    info.setdefault("dispatch_source", "primary trace-compile run")
    return True, {"witness": info, "output": result}


def poison_julia(leg: Path, jbin: str):
    """Make every package the leg declares unloadable. The leg MUST fail."""
    deps = julia_declared_packages(leg.read_text())
    with tempfile.TemporaryDirectory() as td:
        shadow = Path(td) / "shadow"
        depot = Path(td) / "depot"
        shadow.mkdir(parents=True)
        depot.mkdir(parents=True)
        for name in deps:
            src = shadow / name / "src"
            src.mkdir(parents=True, exist_ok=True)
            (src / f"{name}.jl").write_text(_JULIA_POISON_MODULE.format(name=name))
        env = dict(os.environ)
        # Temp depot FIRST so poisoned precompile output is written there and the
        # real depot is neither corrupted nor rebuilt from scratch.
        env["JULIA_DEPOT_PATH"] = f"{depot}:{Path.home() / '.julia'}"
        if deps:
            # The shadow wins over @stdlib for the named packages; everything else
            # resolves normally, so a failure is attributable to the poison.
            env["JULIA_LOAD_PATH"] = f"{shadow}:@stdlib"
        else:
            # Nothing declared: strip the load path so NO package is reachable.
            env["JULIA_LOAD_PATH"] = str(shadow)
        rc, out, err = _run([jbin] + JULIA_FLAGS + [str(leg)], cwd=leg.parent, env=env)
    if rc == 0:
        if deps:
            msg = (f"leg SUCCEEDED with {deps} unloadable — those packages are decorative; "
                   f"the leg's output does not depend on them")
        else:
            msg = ("leg declares no Julia package at all AND still succeeded with the load "
                   "path stripped, so its output depends on no Julia package")
        return False, {"error": msg, "poisoned_packages": deps,
                       "output_without_engine": _last_json(out)}
    return True, {"failed_closed_exit": rc, "poisoned_packages": deps,
                  "failure_attributed_to_poison": JULIA_MARKER in (err or ""),
                  "detail": (err or "")[-200:]}


# =============================================================================
# SHARED CONTROLS
# =============================================================================

def mutation(leg: Path, eng: str, baseline: dict, runner=None):
    """Perturb one numeric literal in the source; the output MUST change.

    `runner` takes a path and returns (rc, stdout, stderr). Julia mutants run as
    a SIBLING of the leg so @__DIR__, relative include, and Project.toml
    activation still resolve — a mutant that failed on a path lookup would
    otherwise be scored "source is load-bearing", which is a false pass.
    """
    if runner is None:
        def runner(p):
            return _run([SIM_PY, str(p)])
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
    if eng == "julia":
        mleg = leg.parent / f".engine_witness_mutant_{os.getpid()}{leg.suffix}"
        try:
            mleg.write_text(mutated)
            rc, out, err = runner(mleg)
        finally:
            try:
                mleg.unlink()
            except OSError:
                pass
    else:
        with tempfile.TemporaryDirectory() as td:
            mleg = Path(td) / leg.name
            mleg.write_text(mutated)
            rc, out, err = runner(mleg)
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
    if eng == "julia":
        return witness_leg_julia(leg)
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


def witness_leg_julia(leg: Path) -> tuple[bool, dict]:
    eng = "julia"
    rep = {"engine": eng,
           "leg": str(leg.relative_to(REPO)) if leg.is_relative_to(REPO) else str(leg)}
    jbin = julia_binary()
    if not jbin:
        # An engine that is not installed cannot have run. This BLOCKS. It is a
        # distinct verdict from every failure below, so an absent toolchain is
        # never mistaken for a defeated leg — and never read as a pass.
        return False, {**rep, "verdict": "ENGINE_UNAVAILABLE",
                       "error": "julia is not on PATH, so no Julia execution evidence can "
                                "exist on this host. Any receipt claiming a Julia leg here is "
                                "unsupported. UNAVAILABLE blocks; it is not a pass.",
                       "searched": "shutil.which('julia')"}
    rep["julia_binary"] = jbin
    if not leg.exists():
        return False, {**rep, "verdict": "NO_LEG",
                       "error": f"julia declared load_bearing but no runnable leg at {leg.name}"}
    if leg.suffix != ".jl":
        return False, {**rep, "verdict": "NOT_A_JULIA_LEG",
                       "error": f"{leg.name} is not a .jl source, so julia cannot be witnessed "
                                f"through it"}
    ok_p, det_p = presence_julia(leg, jbin)
    rep["presence"] = det_p
    if not ok_p:
        return False, {**rep, "verdict": "NOT_PRESENT"}
    w = det_p.get("witness") or {}
    if "trace_total" not in w:
        return False, {**rep, "verdict": "DISPATCH_UNMEASURED",
                       "error": "--trace-compile produced no readable output, so dispatch is "
                                "unmeasured; unmeasured is not a pass"}
    if w.get("trace_total", 0) <= 0:
        return False, {**rep, "verdict": "DISPATCH_UNMEASURED",
                       "error": "julia compiled nothing at all during the leg, so no dispatch "
                                "could be counted; unmeasured is not a pass"}
    if w.get("numeric_dispatch", 0) <= 0:
        verdict = ("DECORATIVE_IMPORT" if w.get("leg_declared_packages")
                   else "ENGINE_NEVER_USED")
        detail = (f". The leg does load {w.get('leg_declared_packages')}, but never dispatches "
                  f"on a numeric or array type."
                  if w.get("leg_declared_packages")
                  else ". The leg loads no Julia package and dispatches on no numeric type.")
        if w.get("numeric_but_io_only"):
            detail += (f" {w['numeric_but_io_only']} numeric-typed compile event(s) were IO "
                       f"entry points (print/println/show) — printing a float is not "
                       f"computing with one.")
        return False, {**rep, "verdict": verdict,
                       "error": "ZERO numeric julia operations were dispatched, so the numbers "
                                "do not come from the engine" + detail}
    ok_k, det_k = poison_julia(leg, jbin)
    rep["poison_control"] = det_k
    if not ok_k:
        return False, {**rep, "verdict": "DECORATIVE"}

    def _jrun(p):
        return _run([jbin] + JULIA_FLAGS + [str(p)], cwd=p.parent)

    ok_m, det_m = mutation(leg, eng, det_p.get("output"), runner=_jrun)
    rep["mutation_control"] = det_m
    if ok_m is False:
        return False, {**rep, "verdict": "PRINTS_CONSTANTS"}
    if ok_m is None:
        return False, {**rep, "verdict": "MUTATION_INCONCLUSIVE",
                       "error": "the mutation control could not run, so 'computed' is "
                                "unverified. Inconclusive is not a pass."}
    return True, {**rep, "verdict": "WITNESSED"}


def main(argv):
    if len(argv) != 3 or argv[2] not in SUPPORTED_ENGINES:
        print(f"usage: engine_witness.py <leg> <{'|'.join(SUPPORTED_ENGINES)}>", file=sys.stderr)
        return 2
    ok, rep = witness_leg(Path(argv[1]).resolve(), argv[2])
    print(json.dumps(rep, indent=1))
    print(f"engine_witness: {rep['verdict']} for {argv[2]}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
