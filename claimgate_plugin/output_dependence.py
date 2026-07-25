#!/usr/bin/env python3
"""output_dependence — does the number the receipt DEMANDS depend on the declared
engine operation?

STATUS: candidate. Not wired into any hook, gate chain, or CI job. Its exit codes
are measurements, not admissions.

WHY THIS EXISTS
---------------
Dispatch counting (claimgate_plugin/engine_witness.py, now Purgatory) proves that
AN engine operation ran. It never proves the ASSERTED OUTPUT came from it. Fixture
b10 makes one jnp call, discards the result, and types the observables by hand.
Recorded as finding F9/b10.

This module asks a different question, once per number:

    the receipt asserts x. Replace what the engine returns. Does x move?

If x does not move when the engine's own return values are replaced, x did not
come from the engine, whatever the dispatch counter says.

THE FOUR RECORDED DEFECTS THIS IS DESIGNED AGAINST
--------------------------------------------------
F5  a crash scored as a pass (`if rc != 0: return True`). Here a nonzero exit
    makes that severance UNMEASURED for every demanded output. Absence of a
    measurement is never dependence. See `classify`.
F5b a leg that hashes its own source and refuses to run when mutated is provably
    INVARIANT to its source, yet passed a source-mutation control. Severance here
    is SEMANTIC, not textual: the leg's bytes are never modified, so a source
    guard computes its usual digest and proceeds. See `_HARNESS`.
F6  a decoy field moving while every claimed observable stayed constant. Here the
    demanded set is read from the RECEIPT before any severance runs, and EVERY
    demanded output must move. A field the receipt does not assert is not in the
    denominator and cannot discharge anything. See `demanded_outputs`.
F7  a poison string detected by name. Semantic severance raises no exception and
    writes no marker: `import jax` succeeds, every call returns a real array, only
    the values differ. There is no string to grep for.
F11 real JAX work via off-list ops (eye, diag, full, slogdet, var) labelled
    DECORATIVE_IMPORT because DISPATCH counted membership in a hand-written name
    list. There is no name list here. The wrapper enumerates every public callable
    of every public jax module at runtime, and a meta-path hook covers modules the
    leg imports later. A control that rejects honest work trains people around the
    gate, so the off-list case is a fixture, not an assumption.

THE SEVERANCE LADDER
--------------------
S0 NULL     the harness installed, perturbation set to identity. Establishes that
            the harness is NEUTRAL and the leg is BIT-REPRODUCIBLE. Nothing else is
            evidence until this holds. Because it holds, "moved" is bit-inequality
            and NO TOLERANCE PARAMETER EXISTS ANYWHERE IN THIS FILE.
S1 ENTRY    perturb only DATA-ENTRY calls — an outermost engine call none of whose
            arguments is already an engine array. The leg then does genuine engine
            work on wrong data.
S2 ALL      perturb the result of every outermost engine call.
S3 ZERO     ANNIHILATE the engine's entry data (x -> x*0). Added because ENTRY and
            ALL alone registered an unearned pass on fixture od9: a hand-typed
            constant plus an honestly-zero engine term moves under any scaling and
            does not move when the engine contributes nothing.
S4 SINGLE k perturb only the k-th outermost engine call. Swept, capped.

S1-S3 are REFUTING: each perturbs every entry position at once, so a number that
does not move under one of them in a completed run is measured INVARIANT.
S4 is EXISTENTIAL ONLY. It can establish dependence and can never refute it,
because an honest output may legitimately be independent of one of several data
sources — measured on fixture od3, whose diag_median does not respond to the
second `full` call. Letting SINGLE refute would reject honest work, which is F11's
failure direction. The measured cost of that discipline is fixture od8, which moves
from REFUSED to UNMEASURED; both block, neither admits.

DISPOSITIONS (exit codes)
-------------------------
0 DEPENDENT   every demanded output moved under at least one severance that RAN,
              S0 was neutral, and no leaf was left unbound.
1 REFUSED     at least one demanded output was measured INVARIANT: the leg ran,
              produced output, and the asserted number did not move.
3 UNMEASURED  blocking. No demanded outputs, an unbound leaf, a non-neutral
              harness, or every severance crashed. Never an admission. Do not mint
              an ADMITTED_PENDING_* label for this; the recorded reason is that
              ADMITTED_PENDING_DEPTH sets gate_admits=1.
2 usage / infrastructure error.

THE CEILING, STATED UP FRONT
----------------------------
Severance proves an asserted number RESPONDS to the engine. It cannot prove the
engine COMPUTED it. Fixture od13_offset_cancelled_laundering measures exit 0 while
printing a hand-typed constant: it adds a nonzero engine term and subtracts a
hand-typed constant equal to that term's honest value, so the two cancel in an
honest run and the number moves under every refuting severance. No further
severance closes this, because an honest value and a constant-plus-engine-term are
both functions that respond to the engine. Closing it requires the VERIFIER to
compute the declared function itself and compare, which is a layout-owned
recompute and is not in this file.

So a DEPENDENT verdict here is not admission evidence. It excludes b10-shaped and
b4/b5-shaped fabrication and it does not exclude od13-shaped fabrication.

KNOWN GAPS — read `known_gaps()` before citing any result from this file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from intake_supervisor import strict_parse  # noqa: E402  (reused, never reimplemented)

REPO = Path(__file__).resolve().parent.parent
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"

# Perturbation constants. These are properties of the CHECK, fixed in this source
# and never read from a receipt. They are not a tolerance: nothing is compared
# against them. They are chosen large so a severed value cannot survive a leg's
# own print formatting (a leg printing %.3f could hide a 1e-9 nudge).
FACTOR = 1.37
OFFSET = 0.11

SINGLE_CAP = 32          # bound on the S3 sweep, so a leg with 10^5 calls terminates
LEG_TIMEOUT = 600

NUMERIC_STR = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")

# Engine names, used ONLY to REFUSE a binding, never to excuse a number. Measured
# on ratchet_contract/ratchetings/results/bures_to_fubini_study.json: ten leaves
# under three_engine_legs.julia matched the JAX leg's output keys exactly and
# inherited its DEPENDENT verdict, so a julia claim was being witnessed by a leg
# julia never ran. Getting this list wrong yields FEWER witnessed leaves, never
# more, so its incompleteness cannot register an unearned pass.
ENGINE_NAMES = ("julia", "jax", "torch", "pytorch", "numpy", "scipy", "mpmath")


# =============================================================================
# THE HARNESS — runs inside the leg's own process
# =============================================================================
# Wrapping rules, all DERIVED at runtime rather than written down:
#   * which modules: every module in sys.modules named `jax` or `jax.<...>` with
#     no underscore-prefixed path component, plus a meta-path hook that wraps any
#     further such module the leg imports. jax._src.* is left alone deliberately:
#     wrapping engine internals would sever the engine from itself.
#   * which callables: every public non-class callable attribute of those modules.
#   * which results: engine arrays of float or complex dtype. Integer arrays are
#     left alone because they index; see known_gaps().
#   * DEPTH GUARD: only the OUTERMOST wrapped call is perturbed. A wrapped public
#     function that internally reaches another wrapped public function must not be
#     perturbed twice, and jax reaching its own public surface must not be severed
#     from within.
_HARNESS = r'''
import builtins, hashlib, json, os, runpy, sys, types as _types

_MODE   = os.environ["OD_MODE"]              # NULL | ENTRY | ZERO | ALL | SINGLE
_FACTOR = float(os.environ["OD_FACTOR"])
_OFFSET = float(os.environ["OD_OFFSET"])
_TARGET = int(os.environ.get("OD_TARGET", "-1"))
_LEG    = os.environ["OD_LEG"]

_trace = []          # (qualified_name, is_entry, out_kind) for OUTERMOST calls only
_depth = [0]
_idx   = [0]
_perturbed = []
_wrapped_modules = []

import jax                                    # noqa: E402
_ArrT = jax.Array


def _has_arr(x, d=0):
    if d > 3:
        return False
    if isinstance(x, _ArrT):
        return True
    if isinstance(x, (list, tuple)):
        return any(_has_arr(i, d + 1) for i in x)
    if isinstance(x, dict):
        return any(_has_arr(v, d + 1) for v in x.values())
    return False


def _perturb(o):
    # dtype.kind avoids calling jnp.issubdtype, which would itself be a wrapped
    # call and would pollute the trace the harness is trying to record.
    try:
        if isinstance(o, _ArrT) and getattr(o.dtype, "kind", "") in ("f", "c"):
            return o * _FACTOR + _OFFSET
    except Exception:
        pass
    return o


def _kind(o):
    try:
        if isinstance(o, _ArrT):
            return "%s%s" % (o.dtype.name, tuple(o.shape))
    except Exception:
        pass
    return type(o).__name__


def _mk(fn, key):
    def proxy(*a, **k):
        outer = _depth[0] == 0
        _depth[0] += 1
        try:
            out = fn(*a, **k)
        finally:
            _depth[0] -= 1
        if not outer:
            return out
        entry = not (_has_arr(a) or _has_arr(list(k.values())))
        i = _idx[0]
        _idx[0] += 1
        _trace.append((key, entry, _kind(out)))
        if _MODE == "NULL":
            return out
        fire = (_MODE == "ALL"
                or (_MODE in ("ENTRY", "ZERO") and entry)
                or (_MODE == "SINGLE" and i == _TARGET))
        if not fire:
            return out
        new = _perturb(out)
        if new is not out:
            _perturbed.append(i)
        return new
    proxy.__name__ = getattr(fn, "__name__", "proxy")
    return proxy


def _public(name):
    return name == "jax" or (
        name.startswith("jax.")
        and all(not p.startswith("_") for p in name.split("."))
    )


def _wrap_module(mod):
    name = getattr(mod, "__name__", "")
    if name in _wrapped_modules:
        return
    _wrapped_modules.append(name)
    for attr in dir(mod):
        if attr.startswith("_"):
            continue
        try:
            f = getattr(mod, attr)
        except Exception:
            continue
        if not callable(f) or isinstance(f, type):
            continue
        # A TYPE ALIAS is callable and is not a class, so the isinstance(f, type)
        # guard above lets it through. Measured: jax.typing.ArrayLike is a
        # _UnionGenericAlias; replacing it with a function proxy made jaxtyping's
        # issubclass(array_type, AbstractArray) raise TypeError, which crashed the
        # real ratchet_contract jax leg under an IDENTITY harness. 11 such aliases
        # sit on the public jax surface. Derived from what the object IS, not from
        # a name list.
        if type(f).__module__ == "typing" or isinstance(f, _types.GenericAlias):
            continue
        if getattr(f, "__module__", "").startswith("importlib"):
            continue
        try:
            setattr(mod, attr, _mk(f, name + "." + attr))
        except Exception:
            pass


class _PostImportWrapper:
    """Wrap public jax modules the leg imports AFTER the harness installs.

    Delegates spec resolution to the remaining finders, then wraps the module once
    the real loader has executed it. Keeps coverage derived rather than listed.
    """

    def find_spec(self, fullname, path=None, target=None):
        if not _public(fullname):
            return None
        for finder in sys.meta_path:
            if finder is self:
                continue
            try:
                spec = finder.find_spec(fullname, path, target)
            except Exception:
                continue
            if spec is None or spec.loader is None:
                continue
            loader = spec.loader
            real_exec = getattr(loader, "exec_module", None)
            if real_exec is None:
                return spec

            def exec_module(module, _real=real_exec):
                _real(module)
                try:
                    _wrap_module(module)
                except Exception:
                    pass

            try:
                loader.exec_module = exec_module
            except Exception:
                return spec
            return spec
        return None


for _n in [n for n in list(sys.modules) if _public(n)]:
    _m = sys.modules.get(_n)
    if _m is not None:
        try:
            _wrap_module(_m)
        except Exception:
            pass
sys.meta_path.insert(0, _PostImportWrapper())

_src = open(_LEG, "rb").read()
_rc = 0
sys.argv = [_LEG]
try:
    runpy.run_path(_LEG, run_name="__main__")
except SystemExit as e:
    _rc = int(e.code or 0)
except BaseException as e:                      # noqa: BLE001
    sys.stderr.write("@@LEG_RAISED %s: %s\n" % (type(e).__name__, e))
    _rc = 70
finally:
    _outer = [t for t in _trace]
    info = {
        "mode": _MODE,
        "modules_wrapped": len(_wrapped_modules),
        "outermost_calls": len(_outer),
        "entry_calls": sum(1 for t in _outer if t[1]),
        "perturbed_call_indices": _perturbed[:64],
        "trace_head": _outer[:24],
        "trace_digest": hashlib.sha256(
            json.dumps([[t[0], t[1], t[2]] for t in _outer],
                       sort_keys=True).encode()).hexdigest()[:16],
        "leg_source_sha256_16": hashlib.sha256(_src).hexdigest()[:16],
        "jax_version": getattr(jax, "__version__", None),
    }
    sys.stderr.write("@@OD" + json.dumps(info) + "\n")
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(_rc)
'''


# =============================================================================
# PLUMBING
# =============================================================================
def _run(argv, env=None, cwd=None, timeout=LEG_TIMEOUT):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                           env=env, cwd=cwd)
        return p.returncode, p.stdout, p.stderr
    except Exception as exc:                    # noqa: BLE001
        return None, "", "dispatch failed: %s" % exc


def _last_json(text):
    for ln in reversed((text or "").splitlines()):
        ln = ln.strip()
        if ln.startswith("{"):
            try:
                v = json.loads(ln)
                if isinstance(v, dict):
                    return v
            except json.JSONDecodeError:
                continue
    return None


def _od_info(stderr_text):
    for ln in (stderr_text or "").splitlines():
        if ln.startswith("@@OD"):
            try:
                return json.loads(ln[4:])
            except json.JSONDecodeError:
                return None
    return None


def numeric_leaves(obj, prefix="", out=None):
    """Every numeric leaf, at every depth, in lists and in keys nobody anticipated.

    A float encoded as text is the same claim (fixture b9), so numeric strings are
    leaves. Booleans are not. There is no exemption list here, by name, by path, by
    type or by magnitude: that is the surface four previous designs established and
    the payload fitted into every time.
    """
    if out is None:
        out = []
    if isinstance(obj, bool):
        return out
    if isinstance(obj, (int, float)):
        out.append((prefix or "<root>", float(obj), "number"))
        return out
    if isinstance(obj, str):
        if NUMERIC_STR.match(obj.strip()):
            try:
                out.append((prefix or "<root>", float(obj), "numeric_string"))
            except ValueError:
                pass
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            numeric_leaves(v, "%s.%s" % (prefix, k) if prefix else str(k), out)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            numeric_leaves(v, "%s[%d]" % (prefix, i), out)
    return out


def _flat_numeric(obj, prefix="", out=None):
    """Numeric leaves of a leg's stdout JSON, keyed by dotted path."""
    if out is None:
        out = {}
    if isinstance(obj, bool):
        return out
    if isinstance(obj, (int, float)):
        out[prefix or "<root>"] = float(obj)
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            _flat_numeric(v, "%s.%s" % (prefix, k) if prefix else str(k), out)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            _flat_numeric(v, "%s[%d]" % (prefix, i), out)
    return out


def demanded_outputs(receipt, leg_out, engine):
    """Bind every numeric leaf of the RECEIPT to a position in the LEG's output.

    Read from the receipt BEFORE any severance runs, which is what stops a decoy
    (finding F6) from discharging anything: a field the receipt does not assert is
    not in the denominator, and every leaf that IS in it must move.

    Binding modes, tried in order, each recorded:
      exact_key            receipt leaf's last path component == leg output path
      engine_prefix_key    'jax_spectral_gap' -> 'spectral_gap'
      value                exact float equality against a leg output position
    A leaf that binds by none of these is UNBOUND — reported, never excused.
    """
    flat = _flat_numeric(leg_out or {})
    by_tail = {}
    for path, val in flat.items():
        by_tail.setdefault(path.split(".")[-1], []).append(path)
    bound, unbound = [], []
    for path, val, kind in numeric_leaves(receipt):
        tail = path.split(".")[-1].split("[")[0]
        target, mode = None, None
        parts = [p.split("[")[0].lower() for p in path.split(".")]
        other = [p for p in parts if p in ENGINE_NAMES and p != engine]
        if other:
            unbound.append({"receipt_path": path, "value": val, "leaf_kind": kind,
                            "why": "claimed for %s, and this control severs %s only"
                                   % (other[0], engine)})
            continue
        if tail in by_tail and len(by_tail[tail]) == 1:
            target, mode = by_tail[tail][0], "exact_key"
        if target is None and tail.startswith(engine + "_"):
            t2 = tail[len(engine) + 1:]
            if t2 in by_tail and len(by_tail[t2]) == 1:
                target, mode = by_tail[t2][0], "engine_prefix_key"
        if target is None:
            # VALUE-ONLY binding is WEAK and does not discharge anything. Measured
            # on fixture od10: a receipt asserting a JULIA number that happens to
            # equal the jax leg's output bound by value and inherited the jax
            # leaf's DEPENDENT verdict — an unearned pass for a number this control
            # never witnessed. A value collision is not provenance. Recorded, and
            # counted as UNBOUND, which blocks.
            hits = [p for p, v in flat.items() if v == val]
            if len(hits) == 1:
                unbound.append({"receipt_path": path, "value": val, "leaf_kind": kind,
                                "collides_with_leg_path": hits[0],
                                "why": "value-only binding is not provenance"})
                continue
        if target is None:
            unbound.append({"receipt_path": path, "value": val, "leaf_kind": kind,
                            "why": "no leg output position carries this claim"})
        else:
            bound.append({"receipt_path": path, "value": val, "leaf_kind": kind,
                          "leg_path": target, "binding": mode,
                          "baseline": flat[target]})
    return bound, unbound


def _moved(a, b):
    """Bit-inequality. No tolerance: S0 established that an unsevered run under the
    harness reproduces the raw run exactly, so any difference at all is real."""
    if a is None or b is None:
        return None
    an, bn = isinstance(a, float) and math.isnan(a), isinstance(b, float) and math.isnan(b)
    if an and bn:
        return False
    if an != bn:
        return True
    return a != b


# =============================================================================
# RUNNERS
# =============================================================================
def run_raw(leg):
    rc, out, err = _run([SIM_PY, str(leg)], cwd=str(leg.parent))
    return {"stage": "raw", "rc": rc, "out": _last_json(out), "stderr_tail": (err or "")[-300:]}


def run_severed(leg, mode, target=-1, harness_path=None):
    # ZERO annihilates the engine's entry data instead of scaling it. A hand-typed
    # constant carrying an honestly-zero engine term MOVES under ENTRY and does NOT
    # move under ZERO, which is the only reason this mode exists (fixture od9).
    factor, offset = (0.0, 0.0) if mode == "ZERO" else (FACTOR, OFFSET)
    env = dict(os.environ)
    env.update({"OD_MODE": mode, "OD_FACTOR": repr(factor), "OD_OFFSET": repr(offset),
                "OD_TARGET": str(target), "OD_LEG": str(leg)})
    rc, out, err = _run([SIM_PY, str(harness_path)], env=env, cwd=str(leg.parent))
    return {"stage": mode if target < 0 else "%s[%d]" % (mode, target),
            "rc": rc, "out": _last_json(out), "info": _od_info(err),
            "stderr_tail": (err or "")[-300:]}


# =============================================================================
# THE CONTROL
# =============================================================================
def classify(leg, receipt, engine="jax"):
    report = {
        "schema": "cr.output_dependence.v1",
        "engine": engine,
        "leg": str(leg),
        "no_tolerance_parameter": True,
        "movement_test": "bit_inequality_after_S0_neutrality",
        "stages": [],
    }

    # --- baseline, twice: a nondeterministic leg makes "moved" meaningless ------
    b1 = run_raw(leg)
    b2 = run_raw(leg)
    report["stages"] += [b1, b2]
    if b1["rc"] != 0 or b1["out"] is None:
        report["verdict"] = "UNMEASURED_LEG_WILL_NOT_RUN"
        report["reason"] = ("the leg does not run clean, so nothing about its outputs "
                            "can be measured. rc=%s" % b1["rc"])
        return 3, report
    if _flat_numeric(b1["out"]) != _flat_numeric(b2["out"]):
        report["verdict"] = "UNMEASURED_NONDETERMINISTIC_LEG"
        report["reason"] = ("two clean runs disagree, so a value that moves under "
                            "severance proves nothing. Declare determinism (seed, "
                            "device, dtype) in a layout-owned contract.")
        return 3, report

    # --- demanded set, read from the RECEIPT before any severance --------------
    bound, unbound = demanded_outputs(receipt, b1["out"], engine)
    report["demanded"] = bound
    report["unbound_receipt_leaves"] = unbound

    with tempfile.TemporaryDirectory() as td:
        hp = Path(td) / "od_harness.py"
        hp.write_text(_HARNESS)

        # --- S0 NULL: the harness must be neutral and the leg reproducible -----
        s0 = run_severed(leg, "NULL", harness_path=hp)
        report["stages"].append(s0)
        if s0["rc"] != 0 or s0["out"] is None:
            report["verdict"] = "UNMEASURED_HARNESS_DETECTED"
            report["reason"] = ("the leg runs clean but fails under an identity "
                                "harness (rc=%s). Unmeasured is not a pass." % s0["rc"])
            return 3, report
        if _flat_numeric(s0["out"]) != _flat_numeric(b1["out"]):
            report["verdict"] = "UNMEASURED_HARNESS_NOT_NEUTRAL"
            report["reason"] = ("the identity harness changed the leg's output, so "
                                "bit-inequality is not a sound movement test here.")
            return 3, report
        info0 = s0.get("info") or {}
        report["wrap"] = {k: info0.get(k) for k in
                          ("modules_wrapped", "outermost_calls", "entry_calls",
                           "trace_digest", "jax_version", "leg_source_sha256_16")}

        n_calls = int(info0.get("outermost_calls") or 0)
        if n_calls == 0:
            report["verdict"] = "REFUSED_ENGINE_NEVER_CALLED"
            report["reason"] = ("zero %s operations ran, so no asserted number can "
                                "have come from %s in this execution." % (engine, engine))
            for d in bound:
                d["verdict"] = "INVARIANT"
                d["evidence"] = "engine made no calls at all"
            return 1, report

        # --- the ladder ---------------------------------------------------------
        # REFUTING severances perturb EVERY data-entry position at once, so an
        # asserted number that does not move under one of them, in a run that
        # completed, is measured INVARIANT.
        # EXISTENTIAL severances (SINGLE k) perturb one call. They can establish
        # dependence and can NEVER refute it: an honest output may legitimately be
        # independent of one of several data sources. Measured on fixture od3,
        # whose diag_median is honestly independent of the second `full` call —
        # letting SINGLE refute would have rejected honest work, which is F11's
        # failure direction.
        refuting = [("ENTRY", -1), ("ALL", -1), ("ZERO", -1)]
        existential = [("SINGLE", k) for k in range(min(n_calls, SINGLE_CAP))]
        for d in bound:
            d["verdict"] = "UNMEASURED"
            d["moved_under"] = []
            d["invariant_under_refuting"] = []
        ran_any = False

        def sever(mode, tgt, can_refute):
            nonlocal ran_any
            st = run_severed(leg, mode, tgt, harness_path=hp)
            info = st.get("info") or {}
            report["stages"].append(
                {"stage": st["stage"], "rc": st["rc"], "out": st["out"],
                 "refuting": can_refute,
                 "perturbed": info.get("perturbed_call_indices")})
            # A CRASH IS NOT EVIDENCE ABOUT ANY DEMANDED OUTPUT (finding F5).
            if st["rc"] != 0 or st["out"] is None:
                return
            if not (info.get("perturbed_call_indices") or []):
                return               # nothing was actually severed: not evidence
            ran_any = True
            flat = _flat_numeric(st["out"])
            for d in bound:
                mv = _moved(d["baseline"], flat.get(d["leg_path"]))
                if mv is True:
                    d["moved_under"].append(st["stage"])
                elif mv is False and can_refute:
                    d["invariant_under_refuting"].append(st["stage"])

        for mode, tgt in refuting:
            sever(mode, tgt, True)
        if any(not d["moved_under"] and not d["invariant_under_refuting"] for d in bound):
            for mode, tgt in existential:
                sever(mode, tgt, False)
                if all(d["moved_under"] or d["invariant_under_refuting"] for d in bound):
                    break

        for d in bound:
            if d["invariant_under_refuting"]:
                d["verdict"] = "INVARIANT"
            elif d["moved_under"]:
                d["verdict"] = "DEPENDENT"
            else:
                d["verdict"] = "UNMEASURED"

    # --- disposition ----------------------------------------------------------
    inv = [d for d in bound if d["verdict"] == "INVARIANT"]
    unm = [d for d in bound if d["verdict"] == "UNMEASURED"]
    if inv:
        report["verdict"] = "REFUSED_OUTPUT_INVARIANT"
        report["reason"] = ("%d asserted number(s) did not move when the engine's "
                            "return values were replaced, in runs that completed: %s"
                            % (len(inv), [d["receipt_path"] for d in inv]))
        return 1, report
    if not bound:
        report["verdict"] = "UNMEASURED_NO_DEMANDED_OUTPUT"
        report["reason"] = ("no numeric leaf of the receipt binds to any position in "
                            "the leg's output, so there is nothing to witness. A "
                            "receipt that asserts no engine number is VACUOUS here, "
                            "never covered.")
        return 3, report
    if unm:
        report["verdict"] = "UNMEASURED_SEVERANCE_DID_NOT_COMPLETE"
        report["reason"] = ("%d asserted number(s) were never observed in a completed "
                            "severed run: %s. Unmeasured is not a pass."
                            % (len(unm), [d["receipt_path"] for d in unm]))
        return 3, report
    if unbound:
        report["verdict"] = "UNMEASURED_UNBOUND_RECEIPT_LEAVES"
        report["reason"] = ("%d numeric leaf/leaves of the receipt bind to no leg "
                            "output position: %s. They are not exempt; they are "
                            "unwitnessed by this control."
                            % (len(unbound), [u["receipt_path"] for u in unbound]))
        return 3, report
    if not ran_any:
        report["verdict"] = "UNMEASURED_NO_SEVERANCE_COMPLETED"
        return 3, report
    report["verdict"] = "DEPENDENT"
    report["reason"] = ("every asserted number moved when the engine's return values "
                        "were replaced, and an identity harness reproduced the raw "
                        "run exactly.")
    return 0, report


def known_gaps():
    """Every entry below was MEASURED, not anticipated. Cite none of this file's
    exit codes without reading it."""
    return [
        "OPEN, UNEARNED PASS — OFFSET-CANCELLED LAUNDERING. Fixture "
        "od13_offset_cancelled_laundering measures exit 0. Its asserted number is a "
        "hand-typed constant with a nonzero engine term added and a hand-typed "
        "constant equal to that term's honest value subtracted. In an honest run "
        "the two cancel; under ENTRY, ALL and ZERO the number moves. This is the "
        "structural ceiling of the whole design: severance proves an asserted "
        "number RESPONDS to the engine, and cannot prove the engine COMPUTED it. "
        "No further severance closes it, because both an honest value and "
        "constant-plus-engine-term respond to the engine. Closing it needs the "
        "VERIFIER to compute the declared function itself and compare — a "
        "layout-owned recompute, which is not in this file.",
        "INTEGER-VALUED ENGINE DATA — MEASURED at exit 3, fixture "
        "od12_integer_only_engine_data. Perturbation applies to float and complex "
        "engine arrays only, because perturbing an integer array breaks indexing, "
        "so a leg whose data is entirely integer has nothing severed and every "
        "asserted number comes back UNMEASURED. Fail-closed, and UNMEASURED must "
        "never read as a pass.",
        "HARNESS DETECTION COSTS ACCURACY, NOT SAFETY — MEASURED at exit 3, "
        "fixtures od6_harness_detector and od8_probe_then_constants. A leg that "
        "probes for replaced return values and exits can force UNMEASURED. It "
        "cannot force a pass. od8 prints constants and would be more accurately "
        "REFUSED; it measures UNMEASURED because SINGLE is existential-only. Both "
        "dispositions block.",
        "AN INPUT PARAMETER RECORDED INSIDE AN ENGINE-OUTPUT BLOCK IS REFUSED — "
        "MEASURED at exit 1 on ratchet_contract/ratchetings/results/"
        "bures_to_fubini_study.json, the estate's strongest receipt. Its "
        "three_engine_legs.jax.theta0 is pi/2, a hand-typed INPUT the leg echoes, "
        "and it is invariant under severance exactly as a fabricated output would "
        "be. This control cannot tell an honest input echo from a fabrication, and "
        "the wrong-direction cost is real: 10 of that receipt's 11 jax-bound leaves "
        "measure DEPENDENT and the eleventh sinks the verdict. The fix is a producer "
        "convention (inputs go in an inputs block), not a rule this file can add "
        "without inventing a position where a number is presumed not to be a claim.",
        "COVERAGE ON A REAL RECEIPT IS 11 OF 69 LEAVES — MEASURED on the same "
        "receipt: 11 numeric leaves bind to a jax leg output position by key, 58 do "
        "not, and the 58 include the headline berry_curvature_value.value and every "
        "floor_claims entry. Those are UNBOUND, which blocks; they are not exempt. "
        "A DEPENDENT verdict on this file covers what it names and nothing else.",
        "ZERO CRASHED ON THE REAL LEG — MEASURED rc=70 for the ZERO stage on "
        "bures_to_fubini_study_jax.py, so the one severance that catches od9-shaped "
        "laundering produced no evidence there. Annihilating engine data breaks legs "
        "that divide by it or take its logarithm. Where ZERO crashes, od9-class "
        "laundering is unprotected and the report says so in its stage list.",
        "SINGLE IS NEARLY USELESS ON A REAL LEG — MEASURED 1435 outermost engine "
        "calls on bures_to_fubini_study_jax.py against SINGLE_CAP=32, and the first "
        "32 are library import-time registration calls, not the leg's computation. "
        "The sweep is meaningful on small legs only.",
        "PRINT FORMATTING. A leg printing few significant digits could round a "
        "severed value back onto its baseline. FACTOR=1.37 and OFFSET=0.11 are "
        "large for exactly this reason; a leg printing one significant digit is "
        "not covered. UNTESTED.",
        "NON-JAX ENGINES ARE NOT WITNESSED. Only jax is severed. julia and torch "
        "return exit 3 without running. The j1/j2/j3 julia fixtures are UNTESTED "
        "by this file, and a julia number in a receipt is unwitnessed here.",
        "VALUE-ONLY BINDING IS REFUSED, NOT REPAIRED — MEASURED, fixture "
        "od10_value_binding_freeride. A receipt leaf that binds to a leg output "
        "only by value equality is counted UNBOUND and blocks. That is fail-closed "
        "and it is not a solution: a genuinely-claimed number whose key does not "
        "match any leg output key is now unwitnessed rather than witnessed weakly.",
        "SELECTION LAUNDERING IS UNTOUCHED. A leg can compute an honest function of "
        "positions IT chose. Severance proves response to the engine, never that "
        "the right quantity was computed from the right inputs.",
        "THE LEG IS PRODUCER-WRITTEN. This control causes the execution rather than "
        "reading a producer-written artifact, which is stronger, but the SOURCE it "
        "executes is still the producer's and so is the receipt naming it. The "
        "trust root moves from 'which positions are excused' to 'who wrote the leg "
        "and the layout'. It is not zero.",
        "jax._src IS NOT WRAPPED, deliberately: severing engine internals would "
        "sever the engine from itself. A leg calling a private jax internal "
        "directly escapes severance and would be REFUSED even if honest. UNTESTED.",
        "MODULE COVERAGE IS DERIVED, NOT PROVEN COMPLETE. 43 public jax modules "
        "were wrapped in the measured runs. The meta-path hook covers modules the "
        "leg imports later; a module reached without going through the import "
        "system would escape. UNTESTED.",
        "A JAXPR/StableHLO DIGEST WAS MEASURED AND DELIBERATELY NOT USED AS THE "
        "VERDICT. jax.make_jaxpr discriminates honest from constant and "
        "token-dispatch computations (eqns 6/0/2; C1 literal-return false/true/true; "
        "C2 input-reachable true/false/false) and its digests were identical across "
        "three processes. It does not witness the RECEIPT'S number: the jaxpr of an "
        "honest traced function is byte-identical (da0b93b242d8d450) whether or not "
        "the leg PRINTS that function's result, and it requires the producer to "
        "declare which function is traced, which lets the producer choose what is "
        "inspected. Severance tests the printed value, so it is preferred here.",
    ]


def main(argv=None):
    ap = argparse.ArgumentParser(description="output-dependence control")
    ap.add_argument("receipt")
    ap.add_argument("--leg", default=None,
                    help="path to the engine leg; default results/<n>.json -> ../<n>_<engine>.py")
    ap.add_argument("--engine", default="jax")
    ap.add_argument("--json", default=None, help="write the full report here")
    ap.add_argument("--gaps", action="store_true", help="print known gaps and exit 0")
    a = ap.parse_args(argv)
    if a.gaps:
        print(json.dumps(known_gaps(), indent=1))
        return 0
    rp = Path(a.receipt).resolve()
    if not rp.exists():
        print("output_dependence: usage — no receipt at %s" % rp, file=sys.stderr)
        return 2
    # strict_parse is REUSED, not reimplemented. duplicate_json_key was the first
    # hostile class this estate closed, and it came back the moment a brand-new
    # component reached for the stdlib default — receipt_grammar.main did exactly
    # that. A number deleted by last-wins parsing is gone before any severance can
    # ask where it came from, so this has to sit upstream of the whole ladder.
    try:
        receipt = strict_parse(rp.read_bytes())
    except Exception as exc:                    # noqa: BLE001
        print("output_dependence: receipt refused at raw parse (%s); failing CLOSED"
              % exc, file=sys.stderr)
        return 3
    leg = Path(a.leg).resolve() if a.leg else (rp.parent.parent / ("%s_%s.py" % (rp.stem, a.engine)))
    if not leg.exists():
        print("output_dependence: UNMEASURED — no %s leg at %s" % (a.engine, leg),
              file=sys.stderr)
        return 3
    if a.engine != "jax":
        print("output_dependence: UNMEASURED — semantic severance is implemented for "
              "jax only; %s is not witnessed by this file." % a.engine, file=sys.stderr)
        return 3
    code, report = classify(leg, receipt, a.engine)
    report["exit"] = code
    report["known_gaps"] = known_gaps()
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1))
    print("output_dependence: %s — %s" % (report.get("verdict"), report.get("reason", "")),
          file=sys.stderr)
    print(json.dumps({"verdict": report.get("verdict"), "exit": code,
                      "demanded": [{k: d[k] for k in
                                    ("receipt_path", "leg_path", "binding", "verdict",
                                     "moved_under", "invariant_under_refuting")
                                    if k in d}
                                   for d in report.get("demanded", [])],
                      "unbound_receipt_leaves": [u["receipt_path"] for u in
                                                 report.get("unbound_receipt_leaves", [])],
                      "wrap": report.get("wrap")}, indent=1))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
