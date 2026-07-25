#!/usr/bin/env python3
# =============================================================================
# JULIA WITNESS — a Julia leg executed in its own process, with its DEMANDED
# OUTPUT bound to the receipt's claimed values.
#
# NOT WIRED. This file is imported by nothing. It does not appear in any hook,
# any workflow, or gate_registry.json, and this build did not put it there.
# Read the STANDING GAP section before treating any exit 0 it emits as evidence.
#
# WHAT WAS MISSING. claim_policy_gate._witness builds every leg path as
# f"{stem}_{eng}.py", so a real probe_julia.jl beside a receipt is reported
# NO_LEG (recorded finding F3 in results/purgatory_engine_witness_v0.json). No
# gate in this estate has ever executed the julia binary. "JAX and Julia agree
# to 1e-13" has therefore been two numbers the producer typed into one JSON
# file, compared with each other.
#
# WHAT THIS ASKS THAT engine_witness.py DID NOT. engine_witness asked four
# questions about the PROCESS: did a module load, did a call happen, does the
# source matter, does the dependency matter. Every one of them can be satisfied
# alongside a fabricated answer. The question here is about the VALUE: for each
# number the receipt claims, did a process this verifier spawned emit that
# number, and is that number a function of something this verifier controls?
#
# THE FOUR RECORDED DEFECTS THIS IS BUILT AGAINST, and where each is closed:
#   F5  a crash scored as a pass  (`if rc != 0: return True`)
#       -> _perturb() records rc != 0 as CRASH and credits nothing. A crash is
#          not evidence about any check. Only a run that exits 0 AND emits a
#          parseable artifact can move a field.
#   F5b a second, unrecorded form of the same error, found by trying to defeat
#       THIS file rather than by reasoning about it. Source ablation perturbs a
#       numeric literal in a file the PRODUCER wrote, so the producer knows in
#       advance what will be perturbed and can spell any constant as an
#       expression over one. Measured: a leg reading
#           h1 = 0.587695264839553 ; gap = h1 * 2
#       claims the receipt's 1.175390529679106, agrees with no source literal to
#       6 significant digits so transcription misses it, moves when h1 is
#       perturbed so source ablation credits it, and computes nothing. It
#       reached exit 0.
#       -> source ablation is now REFUSAL-ONLY and credits nothing. Only INPUT
#          PERTURBATION credits, because the verifier chooses that value at run
#          time, after the leg source is fixed and hashed, and a constant cannot
#          track it. A leg with no input contract PARKS. Re-measured after the
#          split: the laundered leg exit 4, and the same trick combined with
#          shadow detection still exit 4.
#   F6  any shared numeric field moving was enough, and only the LAST literal
#       was perturbed, so a decoy field discharged the control
#       -> the DEMANDED SET is fixed from the receipt BEFORE any perturbation
#          runs, every field is tracked separately, and fields outside that set
#          are never consulted. Up to MAX_MUTANTS literals are perturbed, not
#          one.
#   F7  a fixed greppable poison string let a leg DETECT severing and fake a
#       failure, which the control scored as "dependency is load-bearing"
#       -> severing carries no marker to grep: the shadow is `module X end`,
#          an empty module with the package's own name. And severing is a
#          REFUSAL-ONLY control. Its only crediting outcome does not exist: a
#          leg that detects the shadow and dies converts a REFUSE into an
#          INCONCLUSIVE, never into a PASS. Detection buys nothing.
#   F8  a decorative `using Printf` satisfied severing, because severing was
#       scored by "the leg failed" and a `using` line really does fail when the
#       package is unloadable
#       -> the empty shadow LOADS. `using LinearAlgebra` against `module
#          LinearAlgebra end` succeeds; only a CALL into the package fails. So
#          a decorative `using` now runs to completion and produces IDENTICAL
#          demanded values, which is the refusal condition. Measured on julia
#          1.12.6: decorative leg exit 0 output unchanged; real leg exit 1
#          UndefVarError at the call site.
#
# THE ONE PLACE A NUMBER IS COMPARED, and where its tolerance lives. BIND_TOL
# and MOVE_TOL are constants in this file. Nothing is ever read from the
# receipt: a tolerance accepted from the document under test is the s3/s6
# defect (a measured 2.2e-15 agreement delta parked in a slot bounded
# [0,1e-3]). Any tolerance-shaped field found in the receipt is listed in the
# report under `receipt_supplied_tolerance_fields_ignored` so the refusal is
# visible rather than assumed.
#
# COMPARISON IS BY PARSED VALUE, NEVER BY BYTES. Julia prints 4.685032489737395e-8
# where a Python-written receipt records 4.685032489737395e-08. Same number,
# different bytes. Byte comparison fails on honest work.
#
# STANDING GAP — read before citing any verdict from this file.
#   The artifact is produced by a process THIS verifier spawns, into a directory
#   the leg is handed and the producer does not control, and it is hashed there.
#   That is verifier-caused execution, and it is BY_CONSTRUCTION, not measured.
#   It does not make the LEG trustworthy: the leg source is still producer-
#   written, and a producer who controls the leg controls what it computes.
#   Output-dependence and severing bound what a fabricated leg can look like;
#   they do not establish that the declared operation is the one that ran.
#   Selection laundering is open: a leg can compute an honest-looking function
#   of the verifier's inputs that is not the declared operation, and every
#   control here will pass it.
#
#   MEASURED OPEN RESIDUAL, F7-shaped. A leg can declare a package, detect that
#   the package has been shadowed, and die on purpose. That converts a
#   DECORATIVE_DEPENDENCY refusal into no finding at all, so a decorative
#   dependency can be concealed. Measured: fakecrash_julia.jl exit 0 with
#   severing INCONCLUSIVE_LEG_FAILED. What it CANNOT do is launder a number —
#   that leg's demanded values still moved under all three verifier-chosen
#   inputs, and the same trick combined with constant laundering measured exit 4.
#   The residual is concealment of a decorative dependency, not fabrication.
#
#   MEASURED FAIL-CLOSED COST. Every honest legacy Julia leg in this estate
#   parks, because none declares an input contract. Measured: the sanctioned
#   good fixture j1_real_julia_leg, which genuinely computes its eigenvalues,
#   exits 4 with NO_VERIFIER_CHOSEN_INPUT_DEPENDENCE. That is missing evidence
#   and it is blocking, which is the honest disposition — but a control that
#   blocks all existing work trains people around the gate (finding F11's
#   direction), so this must land as a burn-down debt with a declining count,
#   never as a permanent red.
#
# Exit: 0 WITNESSED | 1 REFUSED | 2 usage/infra | 4 PARK.
#
# WHY PARK IS 4 AND NOT 3. hooks/post_receipt_gate.sh maps a downstream exit 3
# onto gate_admits=1 with disposition ADMITTED_PENDING_DEPTH, and the estate's
# own regression runner names that disposition as a way a forged receipt passes
# by wearing an audit-owed label. PARK here means blocking-for-missing-evidence.
# It must never land on an admitting code, so it does not reuse 3.
# =============================================================================
"""Execute a Julia leg and bind its output to a receipt's claimed numbers.

Usage:
    julia_witness.py <leg.jl> [--receipt <receipt.json>]
                              [--demand-json '{"field": 1.5}']
                              [--input-params '{"a": 2.0}']
                              [--julia /path/to/julia]
                              [--json]

The leg is invoked as:

    julia --startup-file=no --color=no <leg.jl> <input_tsv> <artifact_json>

argv[1] is a verifier-written TSV of `key<TAB>value` lines, always carrying a
random `nonce`. argv[2] is a verifier-owned path the leg may write its JSON
artifact to. A leg that ignores both still works: stdout is captured as the
artifact instead, and the input-perturbation control reports UNTESTED rather
than passing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- fixed numbers
# Both live here, in the verifier's own source, and are reported in every run.
# BIND_TOL: how close an artifact value must be to the receipt's claimed value
# to count as the same number. Sized for the float->decimal->float round trip a
# receipt makes, not for a physics tolerance.
BIND_TOL = 1e-12
# MOVE_TOL: how far a demanded value must travel under a perturbation to count
# as having moved. Larger than BIND_TOL so a formatting wobble cannot register
# as output-dependence.
MOVE_TOL = 1e-9
# Agreement at this many significant digits between a source literal and a
# demanded value counts as transcription. Loosening it refuses more, tightening
# it refuses less; the fail-open direction is the tight one, so it is stated
# here and not tunable from outside this file.
TRANSCRIPTION_SIGDIGITS = 6
# Bound on perturbation effort. Fewer mutants can only make output-dependence
# HARDER to establish, never easier, so the cap fails closed.
MAX_MUTANTS = 16
RUN_TIMEOUT = 300

JULIA_FLAGS = ["--startup-file=no", "--color=no"]

# `using X` / `import X` / `using X: a, b` / `using X, Y`. Base, Core and Main
# live in the sysimage and cannot be shadowed, so they are not severing targets.
_USING = re.compile(r"^\s*(?:using|import)\s+([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)", re.M)
_UNSHADOWABLE = {"Base", "Core", "Main"}

# Every numeric literal, including ones inside string literals. Numbers in
# strings are deliberately NOT excluded: "a number inside a string is not a
# claim" is exactly the presumption that fixture b9 walked through.
_NUM_LITERAL = re.compile(r"(?<![\w.])(\d+\.\d+(?:[eE][-+]?\d+)?|\d+(?:[eE][-+]?\d+)?)(?![\w.])")

# Field names in a receipt that would carry a comparison tolerance. Found here,
# they are recorded and ignored — never read.
_TOLERANCE_KEYS = re.compile(r"^(tol|tols|tolerance|atol|rtol|eps|epsilon|math_epsilon"
                             r"|significant_digits|precision|max_.*_divergence)$", re.I)


# =============================================================================
# small helpers
# =============================================================================

def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha256_file(p: Path) -> str | None:
    try:
        return _sha256_bytes(p.read_bytes())
    except OSError:
        return None


def _run(argv, cwd, env=None, timeout=RUN_TIMEOUT):
    try:
        p = subprocess.run(argv, cwd=str(cwd), env=env, capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return None, "", f"timeout after {timeout}s"
    except OSError as e:
        return None, "", f"OSError: {e}"


def _last_json(text: str):
    """Last parseable JSON object on stdout. Legs print progress; the artifact
    is the last object, not the whole stream."""
    best = None
    for line in (text or "").splitlines():
        line = line.strip()
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            best = json.loads(line)
        except ValueError:
            continue
    return best


def _numeric_leaves(obj, prefix="", out=None):
    """Every numeric leaf, at every depth, including numeric strings. No name,
    path, type or magnitude removes a leaf from this walk."""
    if out is None:
        out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            _numeric_leaves(v, f"{prefix}.{k}" if prefix else str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _numeric_leaves(v, f"{prefix}[{i}]", out)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        out[prefix] = float(obj)
    elif isinstance(obj, str):
        try:
            out[prefix] = float(obj.strip())
        except ValueError:
            pass
    return out


def _same(a: float, b: float) -> bool:
    if a == b:
        return True
    scale = max(1.0, abs(a), abs(b))
    return abs(a - b) <= BIND_TOL * scale


def _moved(a: float, b: float) -> bool:
    scale = max(1.0, abs(a), abs(b))
    return abs(a - b) > MOVE_TOL * scale


def _sig_round(x: float, digits: int) -> str:
    if x == 0 or x != x or x in (float("inf"), float("-inf")):
        return repr(x)
    return f"{x:.{digits}e}"


# =============================================================================
# identity record
# =============================================================================

def julia_identity(jbin: str) -> dict:
    """Version and machine identity read OUT OF the running julia, not guessed
    from the binary path."""
    probe = ('print("{\\"version\\": \\"", string(VERSION), "\\", \\"bindir\\": \\"", '
             'Sys.BINDIR, "\\", \\"cpu\\": \\"", Sys.CPU_NAME, "\\", \\"machine\\": \\"", '
             'Sys.MACHINE, "\\", \\"project\\": \\"", something(Base.active_project(), "none"), '
             '"\\"}")')
    rc, out, err = _run([jbin] + JULIA_FLAGS + ["-e", probe], cwd=REPO, timeout=120)
    if rc != 0:
        return {"error": f"julia identity probe exit {rc}: {(err or '')[-200:]}"}
    got = _last_json(out)
    return got if got else {"error": "identity probe emitted no JSON", "stdout": (out or "")[-200:]}


def project_digests(leg: Path, active_project: str | None) -> dict:
    """sha256 of every Project.toml / Manifest.toml from the leg's directory
    upward, plus the directory julia itself reports as the active project."""
    found: dict[str, str] = {}
    roots = []
    d = leg.resolve().parent
    while True:
        roots.append(d)
        if d == d.parent or d == REPO:
            break
        d = d.parent
    if active_project and active_project not in ("none", ""):
        roots.append(Path(active_project).parent)
    seen = set()
    for r in roots:
        if r in seen:
            continue
        seen.add(r)
        for name in ("Project.toml", "Manifest.toml", "JuliaProject.toml", "JuliaManifest.toml"):
            p = r / name
            if p.is_file():
                try:
                    key = str(p.relative_to(REPO))
                except ValueError:
                    key = str(p)
                found[key] = _sha256_file(p)
    return {"files": found, "count": len(found),
            "note": "empty means the leg runs against julia's default environment"}


def declared_packages(src: str) -> list[str]:
    names = []
    for m in _USING.finditer(src):
        for n in m.group(1).split(","):
            n = n.strip()
            if n and n not in _UNSHADOWABLE and n not in names:
                names.append(n)
    return names


# =============================================================================
# demanded set — fixed BEFORE anything runs
# =============================================================================

def find_tolerance_fields(obj, prefix="", out=None):
    """Tolerance-shaped fields in the receipt, recorded so the refusal to read
    them is visible in the report."""
    if out is None:
        out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            if _TOLERANCE_KEYS.match(str(k)):
                out.append({"path": path, "value": v})
            find_tolerance_fields(v, path, out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_tolerance_fields(v, f"{prefix}[{i}]", out)
    return out


def demanded_from_receipt(receipt: dict) -> dict[str, float]:
    """The numbers the receipt claims Julia produced.

    Source is engines_ran.julia. This is a POSITIVE selection of what must be
    witnessed, not a negative list of what is excused: a field that is not in
    it is not exempted, it is simply not claimed of Julia by this receipt. If
    the receipt claims Julia numbers somewhere else, pass them with
    --demand-json rather than widening this.
    """
    block = (receipt.get("engines_ran") or {}).get("julia")
    if not isinstance(block, dict):
        return {}
    return _numeric_leaves(block)


def resolve_demand(key: str, artifact_vals: dict[str, float]) -> str | None:
    """Map a receipt field name onto an artifact field name.

    Exact match first, then the same name with a leading `julia_` stripped —
    receipts in this estate write engines_ran.julia.julia_spectral_gap for an
    artifact field named spectral_gap. Both resolutions are recorded.
    """
    if key in artifact_vals:
        return key
    if key.startswith("julia_") and key[len("julia_"):] in artifact_vals:
        return key[len("julia_"):]
    tail = key.split(".")[-1]
    if tail in artifact_vals:
        return tail
    if tail.startswith("julia_") and tail[len("julia_"):] in artifact_vals:
        return tail[len("julia_"):]
    return None


# =============================================================================
# execution
# =============================================================================

class Runner:
    """Spawns every julia process and owns every path the leg writes to."""

    def __init__(self, jbin: str, leg: Path, workdir: Path, params: dict):
        self.jbin = jbin
        self.leg = leg
        self.workdir = workdir
        self.params = dict(params)
        self.n = 0

    def input_file(self, nonce: str, params: dict) -> Path:
        p = self.workdir / f"input_{self.n}.tsv"
        lines = [f"nonce\t{nonce}"]
        for k, v in params.items():
            lines.append(f"{k}\t{v}")
        p.write_text("\n".join(lines) + "\n")
        return p

    def execute(self, leg: Path, params: dict | None = None, env: dict | None = None):
        """One run. Returns a dict describing what came back.

        The artifact is the file the leg wrote to the verifier-owned path if it
        wrote one, otherwise the leg's captured stdout. Both are inside the
        verifier's own directory; the producer supplies neither.
        """
        self.n += 1
        nonce = secrets.token_hex(12)
        inp = self.input_file(nonce, self.params if params is None else params)
        art = self.workdir / f"artifact_{self.n}.json"
        rc, out, err = _run([self.jbin] + JULIA_FLAGS + [str(leg), str(inp), str(art)],
                            cwd=leg.parent, env=env)
        rec = {"exit": rc, "nonce_sent": nonce, "input_file": str(inp),
               "stderr_tail": (err or "")[-300:]}
        if art.is_file():
            raw = art.read_bytes()
            rec["artifact_mode"] = "leg_wrote_verifier_path"
        else:
            raw = (out or "").encode()
            rec["artifact_mode"] = "stdout_capture"
        rec["artifact_sha256"] = _sha256_bytes(raw)
        rec["artifact_bytes"] = len(raw)
        parsed = _last_json(raw.decode(errors="replace"))
        rec["parsed"] = parsed
        rec["values"] = _numeric_leaves(parsed) if isinstance(parsed, dict) else {}
        rec["nonce_echoed"] = bool(isinstance(parsed, dict)
                                   and str(parsed.get("nonce", "")) == nonce)
        rec["ok"] = rc == 0 and isinstance(parsed, dict)
        return rec


# =============================================================================
# controls
# =============================================================================

def transcription(src: str, demanded: dict[str, float]) -> dict:
    """Does a demanded value already sit in the leg source as a literal?

    Refusal-only. It cannot make anything pass. A value that agrees with a
    source literal to TRANSCRIPTION_SIGDIGITS significant digits has not been
    shown to be computed by anything — the leg already had it.
    """
    lits = []
    for m in _NUM_LITERAL.finditer(src):
        try:
            lits.append((m.group(1), float(m.group(1))))
        except ValueError:
            pass
    hits = {}
    for key, val in demanded.items():
        for text, lit in lits:
            if _sig_round(lit, TRANSCRIPTION_SIGDIGITS - 1) == _sig_round(val, TRANSCRIPTION_SIGDIGITS - 1):
                hits[key] = {"source_literal": text, "demanded_value": val,
                             "agree_to_sigdigits": TRANSCRIPTION_SIGDIGITS}
                break
    return {"source_literal_count": len(lits), "transcribed": hits,
            "sigdigits": TRANSCRIPTION_SIGDIGITS}


def severing(runner: Runner, leg: Path, src: str, baseline: dict) -> dict:
    """Make every declared package load but export nothing, and re-run.

    `module X end` LOADS, so a decorative `using X` survives it and produces
    identical output — which is the refusal condition. A package that is
    actually called dies at the call site with UndefVarError, which is recorded
    as INCONCLUSIVE and credits nothing.

    There is no marker string anywhere in the shadow, so there is nothing for a
    leg to grep for. And because the only refusing outcome is "ran fine and
    changed nothing", a leg that detects the shadow and dies converts a REFUSE
    into an INCONCLUSIVE. Detection can lose evidence; it can never buy a pass.
    """
    deps = declared_packages(src)
    with tempfile.TemporaryDirectory() as td:
        shadow = Path(td) / "shadow"
        depot = Path(td) / "depot"
        shadow.mkdir(parents=True)
        depot.mkdir(parents=True)
        for name in deps:
            d = shadow / name / "src"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{name}.jl").write_text(f"module {name}\nend\n")
        env = dict(os.environ)
        # Temp depot FIRST so any precompile output from the shadow lands there
        # and the real depot is neither written to nor rebuilt.
        env["JULIA_DEPOT_PATH"] = f"{depot}:{Path.home() / '.julia'}"
        env["JULIA_LOAD_PATH"] = (f"{shadow}:@stdlib" if deps else str(shadow))
        rec = runner.execute(leg, env=env)

    out = {"declared_packages": deps, "run": {k: rec[k] for k in
           ("exit", "artifact_mode", "artifact_sha256", "nonce_echoed", "stderr_tail")}}
    if not deps:
        # Base is the sysimage and cannot be shadowed. A Base-only leg is not
        # thereby decorative — Julia still did the arithmetic. Recording this
        # as a refusal would reject honest work, which is the F11 direction.
        out["verdict"] = "NO_PACKAGE_DECLARED"
        out["_why"] = ("the leg declares no shadowable package, so severing says nothing "
                       "about whether julia computed the values; Base is the sysimage")
        return out
    if not rec["ok"]:
        out["verdict"] = "INCONCLUSIVE_LEG_FAILED"
        out["_why"] = ("the leg did not complete with its packages shadowed, so no severed "
                       "values exist to compare; a crash is not evidence in either direction")
        return out
    sev_vals = rec["values"]
    same, differ, missing = [], [], []
    for key, base_val in baseline.items():
        if key not in sev_vals:
            missing.append(key)
        elif _same(sev_vals[key], base_val):
            same.append(key)
        else:
            differ.append(key)
    out.update({"identical": sorted(same), "changed": sorted(differ), "absent": sorted(missing)})
    if same and not differ:
        out["verdict"] = "DECORATIVE_PACKAGES"
        out["_why"] = (f"the leg ran to completion with {deps} shadowed and every demanded "
                       f"value came back identical, so those packages contribute nothing to "
                       f"the numbers the receipt claims")
    else:
        out["verdict"] = "PACKAGES_AFFECT_OUTPUT"
        out["_why"] = ("recorded, not credited: a leg that detects the shadow could also "
                       "print different constants, so this outcome is not treated as "
                       "positive evidence anywhere in the verdict")
    return out


def _perturb(runner: Runner, leg: Path, baseline: dict, mutants: list, params_runs: list) -> dict:
    """Which demanded fields move under a perturbation the verifier controls.

    TWO FAMILIES, AND THEY ARE NOT EQUIVALENT. This asymmetry is the one thing
    in this file that was found by measurement rather than reasoning.

      SOURCE ABLATION perturbs a numeric literal in a file the PRODUCER wrote.
      It is REFUSAL-ONLY and credits nothing. Measured: a leg reading
          h1 = 0.587695264839553 ; gap = h1 * 2
      reaches the receipt's claimed 1.175390529679106 while no source literal
      agrees with it to 6 significant digits, so transcription misses it, and
      perturbing h1 moves gap, so source ablation credits it. It computes
      nothing. Any constant can be made source-dependent by writing it as an
      expression, because the producer knows in advance what will be perturbed.

      INPUT PERTURBATION substitutes a value the VERIFIER chooses at run time,
      after the leg source is already fixed and hashed. A constant cannot track
      it. This is the only family that credits.

    A run that does not exit 0 with a parseable artifact is CRASH and credits
    nothing — finding F5, where `if rc != 0: return True` scored a broken leg as
    proof its source mattered. Only fields in the demanded set are ever
    consulted — finding F6, where a decoy field derived from the perturbed
    literal discharged the control while every claimed observable stayed
    constant.
    """
    moved_src: dict[str, list] = {k: [] for k in baseline}
    moved_inp: dict[str, list] = {k: [] for k in baseline}
    trials = []
    for family, runs in (("source", mutants), ("input", params_runs)):
        for label, rec in runs:
            t = {"family": family, "perturbation": label, "exit": rec["exit"],
                 "artifact_sha256": rec["artifact_sha256"]}
            if not rec["ok"]:
                t["effect"] = "CRASH_OR_UNPARSEABLE — credits nothing"
                trials.append(t)
                continue
            vals = rec["values"]
            moved = [k for k in baseline if k in vals and _moved(vals[k], baseline[k])]
            for k in moved:
                (moved_src if family == "source" else moved_inp)[k].append(label)
            t["moved_demanded_fields"] = sorted(moved)
            t["absent_demanded_fields"] = sorted(k for k in baseline if k not in vals)
            t["effect"] = "OK"
            trials.append(t)
    return {
        "trials": trials,
        "moved_by_source_ablation": moved_src,
        "moved_by_input_perturbation": moved_inp,
        "_credit_rule": ("only moved_by_input_perturbation credits. source ablation "
                         "perturbs a literal the producer wrote and can be satisfied by a "
                         "laundered constant; it can refuse, never witness."),
        "fields_credited": sorted(k for k, v in moved_inp.items() if v),
        "fields_moved_by_source_only": sorted(k for k in baseline
                                              if moved_src[k] and not moved_inp[k]),
        "fields_that_never_moved": sorted(k for k in baseline
                                          if not moved_src[k] and not moved_inp[k]),
        "successful_source_trials": sum(1 for t in trials
                                        if t["family"] == "source" and t.get("effect") == "OK"),
        "successful_input_trials": sum(1 for t in trials
                                       if t["family"] == "input" and t.get("effect") == "OK"),
    }


def source_mutants(runner: Runner, leg: Path, src: str) -> list:
    """Perturb each numeric literal in turn, as a SIBLING of the leg.

    Sibling and not a temp dir so @__DIR__, relative include and Project.toml
    activation still resolve. A mutant that failed on a path lookup would be
    scored "source is load-bearing", which is a false pass.
    """
    cands = list(_NUM_LITERAL.finditer(src))[:MAX_MUTANTS]
    runs = []
    for m in cands:
        try:
            val = float(m.group(1))
        except ValueError:
            continue
        mutated = src[:m.start(1)] + repr(val * 1.7 + 0.31) + src[m.end(1):]
        mleg = leg.parent / f".julia_witness_mutant_{os.getpid()}_{m.start(1)}{leg.suffix}"
        try:
            mleg.write_text(mutated)
            rec = runner.execute(mleg)
        finally:
            try:
                mleg.unlink()
            except OSError:
                pass
        runs.append((f"source_literal@{m.start(1)}:{m.group(1)}", rec))
    return runs


def input_perturbations(runner: Runner, leg: Path, baseline_echoed: bool) -> tuple[list, dict]:
    """Perturb one declared input parameter at a time.

    This is the only crash-immune control here: a leg cannot satisfy it by
    dying. It runs only when the baseline artifact echoed the verifier's nonce,
    which is what proves the leg read the verifier's file in this run rather
    than ignoring it. No echo means UNTESTED, never a pass.
    """
    if not runner.params:
        return [], {"status": "UNTESTED_NO_PARAMS",
                    "_why": "no input parameters were declared for this leg"}
    if not baseline_echoed:
        return [], {"status": "UNTESTED_NO_INPUT_CONTRACT",
                    "_why": ("the baseline artifact did not echo the verifier's nonce, so "
                             "there is no evidence the leg read the verifier's input file; "
                             "perturbing an input it never reads would measure nothing")}
    runs = []
    for k, v in runner.params.items():
        try:
            nv = float(v) * 1.37 + 0.11
        except (TypeError, ValueError):
            continue
        pert = dict(runner.params)
        pert[k] = nv
        rec = runner.execute(leg, params=pert)
        runs.append((f"input_param:{k}", rec))
    return runs, {"status": "RAN", "params_perturbed": sorted(runner.params)}


# =============================================================================
# top level
# =============================================================================

def witness(leg: Path, receipt: dict | None, receipt_path: Path | None,
            demand_override: dict | None, params: dict | None,
            julia_override: str | None) -> tuple[int, dict]:
    rep: dict = {
        "schema": "cr.julia_witness.v1",
        "leg": str(leg),
        "receipt": str(receipt_path) if receipt_path else None,
        "fixed_by_this_verifier": {"BIND_TOL": BIND_TOL, "MOVE_TOL": MOVE_TOL,
                                   "TRANSCRIPTION_SIGDIGITS": TRANSCRIPTION_SIGDIGITS,
                                   "MAX_MUTANTS": MAX_MUTANTS},
        "receipt_supplied_tolerance_fields_ignored":
            find_tolerance_fields(receipt) if receipt else [],
        "refusals": [],
        "parks": [],
    }

    def park(code, why):
        rep["parks"].append({"id": code, "why": why})

    def refuse(code, why):
        rep["refusals"].append({"id": code, "why": why})

    # --- T0 toolchain -------------------------------------------------------
    jbin = julia_override or shutil.which("julia")
    rep["julia_binary"] = jbin
    if not jbin or not Path(jbin).exists():
        park("TOOLCHAIN_ABSENT",
             "no julia binary on PATH, so no Julia execution evidence can be produced. "
             "An absent engine is missing evidence, never a pass.")
        rep["verdict"] = "PARK"
        return 4, rep
    rep["julia_identity"] = julia_identity(jbin)

    # --- T1 leg -------------------------------------------------------------
    if not leg.is_file():
        park("NO_LEG", f"no runnable Julia leg at {leg}")
        rep["verdict"] = "PARK"
        return 4, rep
    if leg.suffix != ".jl":
        park("NOT_A_JULIA_SOURCE",
             f"{leg.name} is not a .jl source; claim_policy_gate._witness builds every leg "
             f"path as <stem>_<eng>.py, which is recorded finding F3 and is why the Julia "
             f"witness never fired")
        rep["verdict"] = "PARK"
        return 4, rep
    src = leg.read_text()
    rep["leg_source_sha256"] = _sha256_bytes(src.encode())
    rep["leg_declared_packages"] = declared_packages(src)
    rep["project_digests"] = project_digests(leg, (rep.get("julia_identity") or {}).get("project"))

    # --- demanded set, fixed before anything runs ---------------------------
    demanded_raw = dict(demand_override) if demand_override else (
        demanded_from_receipt(receipt) if receipt else {})
    rep["demanded_from"] = ("--demand-json" if demand_override else
                            "receipt engines_ran.julia" if receipt else "none")
    rep["demanded_raw"] = demanded_raw
    if not demanded_raw:
        park("NO_DEMANDED_SET",
             "the receipt claims no Julia numbers (engines_ran.julia carries no numeric "
             "leaf), so there is nothing for an execution to witness. A leg that witnesses "
             "no number is VACUOUS, not passing.")
        rep["verdict"] = "PARK"
        return 4, rep

    # --- T2 execution + artifact -------------------------------------------
    with tempfile.TemporaryDirectory(prefix="julia_witness_") as td:
        work = Path(td)
        runner = Runner(jbin, leg, work, params or {})
        base = runner.execute(leg)
        rep["baseline_run"] = {k: base[k] for k in
                               ("exit", "artifact_mode", "artifact_sha256", "artifact_bytes",
                                "nonce_echoed", "stderr_tail")}
        rep["baseline_run"]["_artifact_provenance"] = (
            "produced by a process this verifier spawned, written into a directory this "
            "verifier created and handed to the leg, and hashed there. BY_CONSTRUCTION, "
            "not measured.")
        if not base["ok"]:
            park("LEG_DID_NOT_PRODUCE_AN_ARTIFACT",
                 f"the leg exited {base['exit']} or emitted no parseable JSON. A crash is "
                 f"not evidence about any check, so this is missing evidence, not a "
                 f"refusal of the claim.")
            rep["verdict"] = "PARK"
            return 4, rep
        art_vals = base["values"]
        rep["artifact_numeric_fields"] = sorted(art_vals)

        # --- T3 binding: demanded value <-> artifact value -------------------
        binding, baseline_demanded, unbound = {}, {}, []
        for key, val in demanded_raw.items():
            field = resolve_demand(key, art_vals)
            if field is None:
                unbound.append(key)
                binding[key] = {"artifact_field": None, "status": "UNBOUND"}
                continue
            got = art_vals[field]
            ok = _same(got, val)
            binding[key] = {"artifact_field": field, "receipt_value": val,
                            "artifact_value": got, "status": "BOUND" if ok else "MISMATCH",
                            "abs_diff": abs(got - val)}
            if ok:
                baseline_demanded[field] = got
            else:
                unbound.append(key)
        rep["binding"] = binding
        if unbound:
            refuse("UNBOUND_OR_MISMATCHED",
                   f"these receipt-claimed Julia numbers were not produced by the leg this "
                   f"verifier just ran: {sorted(unbound)}. Comparison is by parsed value at "
                   f"BIND_TOL={BIND_TOL}, fixed in this file, never read from the receipt.")

        # --- T4 transcription -------------------------------------------------
        trans = transcription(src, {k: v for k, v in demanded_raw.items()})
        rep["transcription"] = trans
        if trans["transcribed"]:
            refuse("TRANSCRIBED_FROM_SOURCE",
                   f"these demanded values already sit in the leg source as literals agreeing "
                   f"to {TRANSCRIPTION_SIGDIGITS} significant digits: "
                   f"{sorted(trans['transcribed'])}. The leg had the number before it ran.")

        # --- T5/T7 output-dependence -----------------------------------------
        if baseline_demanded:
            muts = source_mutants(runner, leg, src)
            iruns, istatus = input_perturbations(runner, leg, base["nonce_echoed"])
            rep["input_perturbation"] = istatus
            dep = _perturb(runner, leg, baseline_demanded, muts, iruns)
            rep["output_dependence"] = dep
            never = dep["fields_that_never_moved"]
            n_ok = dep["successful_source_trials"] + dep["successful_input_trials"]
            if not n_ok:
                park("NO_SUCCESSFUL_PERTURBATION",
                     "every perturbation crashed or produced an unparseable artifact, so "
                     "output-dependence was not measured. A crash credits nothing.")
            elif never and len(never) == len(baseline_demanded):
                refuse("DEMANDED_OUTPUT_INVARIANT",
                       f"no demanded value moved under any of {n_ok} successful "
                       f"verifier-controlled perturbations: {never}. The numbers are not a "
                       f"function of anything this verifier can change.")
            elif never:
                refuse("INVARIANT_FIELDS",
                       f"these demanded values never moved under any successful perturbation "
                       f"while others did, so they are constants carried alongside computed "
                       f"work: {never}")
            # Crediting is separate from refusing, and only the input family
            # credits. A field that moved only under source ablation is
            # UNWITNESSED, not passing: measured, a laundered constant
            # (h1 = 0.587695264839553; gap = h1 * 2) satisfies source ablation
            # and reached exit 0 before this split existed.
            uncredited = [k for k in baseline_demanded if k not in dep["fields_credited"]]
            if uncredited:
                park("NO_VERIFIER_CHOSEN_INPUT_DEPENDENCE",
                     f"these demanded values never moved under a value this verifier chose at "
                     f"run time: {sorted(uncredited)}. input_perturbation status was "
                     f"'{istatus['status']}'. Source ablation alone cannot witness them, "
                     f"because the producer wrote the literal it perturbs and any constant "
                     f"can be spelled as an expression over one.")
        else:
            rep["output_dependence"] = {"skipped": "no demanded value bound to an artifact "
                                                   "field, so there is nothing to perturb"}

        # --- T6 severing --------------------------------------------------------
        sev = severing(runner, leg, src, baseline_demanded) if baseline_demanded else \
            {"verdict": "SKIPPED", "_why": "nothing bound to compare"}
        rep["severing"] = sev
        if sev.get("verdict") == "DECORATIVE_PACKAGES":
            declared_lb = ((receipt or {}).get("TOOL_INTEGRATION_DEPTH") or {}).get("julia")
            sev["receipt_declares_julia"] = declared_lb
            refuse("DECORATIVE_DEPENDENCY",
                   f"the leg completed with {sev['declared_packages']} shadowed and every "
                   f"demanded value came back identical. The receipt declares julia "
                   f"'{declared_lb}'.")
        if sev.get("verdict") == "INCONCLUSIVE_LEG_FAILED":
            # Recorded, and it neither refuses nor parks. Two reasons, and the
            # second one is a measured residual rather than a closure.
            #   1. Crediting it would be finding F7 exactly: engine_witness read
            #      "the leg died when its dependency was removed" as "the
            #      dependency is load-bearing", and a leg that DETECTS the
            #      shadow and dies on purpose satisfies that. Nothing here
            #      credits it.
            #   2. Parking on it would block every honest leg that really calls
            #      into a package, because a real call into an empty shadow is
            #      an UndefVarError. Measured: the genuine leg parked on exactly
            #      this before the disposition was corrected. A control that
            #      blocks all honest work is finding F11's direction.
            # RESIDUAL, OPEN: a leg can therefore detect the shadow, die, and
            # convert a DECORATIVE_PACKAGES refusal into no finding at all. What
            # that buys is concealment of a decorative dependency. It cannot
            # launder a fabricated number, because binding, transcription and
            # output-dependence do not consult severing.
            rep.setdefault("notes", []).append(
                {"id": "SEVERING_INCONCLUSIVE",
                 "why": "the leg did not complete with its packages shadowed, so severing "
                        "produced no comparison. Neither refusing nor crediting: crediting "
                        "is finding F7, parking blocks every leg that really calls a package."})

    if rep["refusals"]:
        rep["verdict"] = "REFUSED"
        return 1, rep
    if rep["parks"]:
        rep["verdict"] = "PARK"
        return 4, rep
    rep["verdict"] = "WITNESSED"
    rep["_ceiling"] = ("WITNESSED means: a process this verifier spawned produced the "
                       "receipt's claimed Julia numbers, those numbers are not literals in "
                       "the leg source, and they move under a perturbation this verifier "
                       "controls. It does NOT mean the declared operation is the one that "
                       "ran. The leg source is producer-written and selection laundering "
                       "is open.")
    return 0, rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Execute a Julia leg and bind its output to a receipt.")
    ap.add_argument("leg")
    ap.add_argument("--receipt")
    ap.add_argument("--demand-json")
    ap.add_argument("--input-params")
    ap.add_argument("--julia")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    receipt, receipt_path = None, None
    if a.receipt:
        receipt_path = Path(a.receipt)
        try:
            receipt = json.loads(receipt_path.read_text())
        except (OSError, ValueError) as e:
            print(f"julia_witness: cannot read receipt {a.receipt}: {e}", file=sys.stderr)
            return 2
    try:
        demand = json.loads(a.demand_json) if a.demand_json else None
        params = json.loads(a.input_params) if a.input_params else None
    except ValueError as e:
        print(f"julia_witness: bad --demand-json/--input-params: {e}", file=sys.stderr)
        return 2
    if params is None and isinstance(receipt, dict):
        params = ((receipt.get("julia_input_contract") or {}).get("params"))

    code, rep = witness(Path(a.leg).resolve(), receipt, receipt_path, demand, params, a.julia)
    if a.json:
        print(json.dumps(rep, indent=1, sort_keys=True, default=str))
    else:
        print(f"julia_witness: {rep['verdict']} (exit {code})")
        for r in rep.get("refusals", []):
            print(f"  REFUSE {r['id']}: {r['why']}")
        for p in rep.get("parks", []):
            print(f"  PARK   {p['id']}: {p['why']}")
        for n in rep.get("notes", []):
            print(f"  note   {n['id']}: {n['why']}")
        sev = (rep.get("severing") or {}).get("verdict")
        if sev:
            print(f"  severing: {sev}")
    return code


if __name__ == "__main__":
    sys.exit(main())
