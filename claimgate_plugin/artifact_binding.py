#!/usr/bin/env python3
"""ARTIFACT BINDING — coverage-based binding of every receipt number to a
verifier-regenerated artifact position.

WHY THIS EXISTS. Four detector designs failed the same way. Each established a
RELIEVING SURFACE — a set of positions where a number is presumed not to be a
claim — and each time the payload fit into it:

    1  path-prefix exclusion   -> park poison under a fixture prefix
    2  key-name denylist       -> fixtures b7 / b8 / b9
    3  exempt full paths       -> b11 payload under `digest`, b12 array wrapper
    4  typed roles + bounds    -> a measured 2.2e-15 in a slot bounded [0,1e-3]

A NAME, a PATH, a TYPE and a BOUND are the same object under four skins: a
syntactic property standing in for a judgement about what a number MEANS.

THIS MODULE ASKS A DIFFERENT QUESTION. It never classifies a position. It asks
of EVERY numeric leaf, without exception:

    which position of a VERIFIER-REGENERATED artifact holds this value?

There is no exemption list of key names, paths, types or bounds anywhere in this
file. The denominator is every numeric leaf at every depth. The only exit from
the denominator is a declared binding that RESOLVES, AGREES, and survives the
input-dependence probe. Relocation buys a producer nothing, because the test is
indexed by the VALUE, not by the position: moving 2.2e-15 does not change
2.2e-15, and an artifact still has to hold 2.2e-15 at the declared pointer.

WHAT THE RECEIPT DECLARES (the only fields this gate READS as configuration —
everything else in the receipt is data to be covered, never configuration):

  "artifact_binding": {
    "artifacts": [
      {"artifact_id":   "jax_leg",
       "interpreter":   "python3" | "julia",
       "script":        "probe_jax.py",
       "inputs":        ["inputs/H.json"],
       "stdout_sha256": "<hex of the artifact bytes the producer recorded>"}
    ],
    "bindings": [
      {"receipt_pointer":  "/metrics/spectral_gap",
       "artifact_id":      "jax_leg",
       "artifact_pointer": "/spectral_gap"}
    ]
  }

FLOAT SEMANTICS, stated and enforced. Coverage compares two copies of ONE
number, so it is IDENTITY and identity takes no epsilon. int vs int is exact
integer equality. Anything else is exact IEEE-754 float64 BIT identity via
struct.pack('<d'). Consequences, deliberate: -0.0 does not cover 0.0, and NaN
never covers NaN. NO tolerance, epsilon, significant-digit budget or bound is
read from the receipt, from the environment, or from any library parameter.
There is no numeric comparison parameter in this file for a measurement to hide
inside. That is the structural reason design 4's defect cannot re-enter here.

BYTE COMPARISON vs VALUE COMPARISON — two different comparisons, on purpose.
  artifact-vs-artifact  (recorded digest vs regenerated stdout) is BYTES. Both
                        sides are the same program's stdout, so this is a
                        determinism requirement, not a formatting requirement.
  receipt-vs-artifact   (a claimed number vs an artifact position) is PARSED
                        VALUE at bit identity, so a leg printing 4.685e-8 where
                        the receipt records 4.685e-08 still binds.

DERIVED OPS ARE DELIBERATELY ABSENT. A producer-extensible op table would read
"this number is a derivation, not a claim", which is the same object as a name,
a path, a type and a bound. IDENTICAL alone is sufficient whenever the leg emits
what the receipt claims, so the escape hatch buys nothing and costs the design.

WHAT THIS DOES NOT CLOSE, stated up front rather than discovered later. Coverage
does not eliminate the trust root, it RELOCATES it from "which positions are
excused" to "what did the verifier actually cause to run". An identity-function
leg — one that reads a producer-written input and prints it — regenerates,
agrees, and is input-dependent while computing nothing. Measured, not argued;
see the header of the results record. Coverage is also NON-UNIFORM in strength:
near-conclusive for a distinctive value, near-vacuous for a small integer that
occurs everywhere.

KNOWN GAPS, measured or named rather than left to be discovered.
  - IDENTITY-FUNCTION LEG. A leg that reads a producer-written input and prints
    it regenerates, agrees, and is input-dependent. MEASURED at exit 0. The
    fabrication moves one file over; coverage does not close it.
  - SELECTION LAUNDERING. DERIVED ops are absent, but a leg can still compute
    honestly over positions the producer chose. The recompute is honest and the
    selection is the fabrication. Closing it needs the artifact's output shape
    fixed by a layout the producer cannot write.
  - RESTATED INPUT CONSTANTS PARK. A receipt that repeats a matrix dimension
    binds it and then fails the dependence probe, because a constant is not a
    function of the inputs. MEASURED: an honest jax receipt carrying n=3 parks.
    That is a wrong-direction cost, and the producer-side fix is to emit the
    receipt FROM the artifact rather than restate its inputs.
  - THE DEPENDENCE PROBE VARIES FLOAT LEAVES ONLY. A leg whose declared inputs
    carry no float leaf scores UNDETERMINED, which parks. Fail-closed, but it
    means integer-only input contracts cannot reach exit 0.
  - COPYTREE COST. Each probe copies the whole receipt root to a verifier-owned
    temp dir. Fine for a leg directory, untested on a large results tree.
  - TRUST ROOT. This file must be unwritable by the producing agent. No
    CODEOWNERS is tracked in this repo today, so a green result here measures
    what the verifier ran, not who was allowed to change the rule.

Exit: 0 all covered | 1 BLOCK | 3 PARK | 2 usage.
Nonzero is a policy disposition, never a scientific verdict.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# strict_parse is REUSED, never reimplemented. duplicate_json_key is a closed
# defect that has already returned TWICE in new components that reached for the
# stdlib default: {"metrics":{"gap":1.78},"metrics":{}} parses to {"metrics":{}}
# under json.loads and the claim is gone before any rule can run.
from claimgate_plugin.intake_supervisor import strict_parse  # noqa: E402

# ---------------------------------------------------------------------------
# GATE-OWNED CONSTANTS. None of these is readable from a receipt.
# ---------------------------------------------------------------------------
INTERPRETERS = {
    "python3": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
    "julia": "/opt/homebrew/bin/julia",
}
JULIA_ARGS = ["--startup-file=no"]
RUN_TIMEOUT_S = 300

# Input-dependence probes. Gate-owned, applied to FLOAT leaves of a declared
# input document. Ints are left alone because they are usually structural
# (dimensions, indices) and perturbing them mostly crashes the leg; a crash is
# not evidence about any check, so that direction only produces UNDETERMINED,
# which never admits.
PERTURBATIONS = (
    ("scale_1p5", lambda x: x * 1.5),
    ("plus_1", lambda x: x + 1.0),
    ("negate", lambda x: -x),
)


# ---------------------------------------------------------------------------
# NUMERIC LEAF ENUMERATION — no exemption list, at any depth, in any container.
# ---------------------------------------------------------------------------
def _esc(tok: str) -> str:
    return str(tok).replace("~", "~0").replace("/", "~1")


def numeric_leaves(obj, pointer=""):
    """Every numeric leaf of a document as (json_pointer, python_value, kind).

    int, float, and any string whose FULL content parses as a number. A float
    encoded as text is the same claim — that is fixture b9 exactly, and the
    recorded relieving-string problem is wider than it looks: short_label's own
    regex accepts 1.7807764064044151 while its comment says "not a number in
    disguise".

    Booleans are excluded, and that is not a relieving surface: a bool carries
    two values, so no measurement can be hidden in one. Nothing else is excluded.
    """
    out = []
    if isinstance(obj, bool):
        return out
    if isinstance(obj, int):
        return [(pointer or "", obj, "int")]
    if isinstance(obj, float):
        return [(pointer or "", obj, "float")]
    if isinstance(obj, str):
        v = _as_number(obj)
        if v is not None:
            return [(pointer or "", v, "numeric_string")]
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += numeric_leaves(v, f"{pointer}/{_esc(k)}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += numeric_leaves(v, f"{pointer}/{i}")
    return out


def _as_number(s: str):
    """A string is numeric iff its full content parses as a number."""
    t = s.strip()
    if not t:
        return None
    try:
        return int(t)
    except (TypeError, ValueError):
        pass
    try:
        return float(t)
    except (TypeError, ValueError):
        return None


def resolve_pointer(doc, pointer: str):
    """RFC 6901 resolution. Returns (found, value)."""
    if pointer in ("", "/"):
        return True, doc
    if not pointer.startswith("/"):
        return False, None
    cur = doc
    for raw in pointer.split("/")[1:]:
        tok = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, dict):
            if tok not in cur:
                return False, None
            cur = cur[tok]
        elif isinstance(cur, list):
            try:
                idx = int(tok)
            except ValueError:
                return False, None
            if idx < 0 or idx >= len(cur):
                return False, None
            cur = cur[idx]
        else:
            return False, None
    return True, cur


# ---------------------------------------------------------------------------
# IDENTITY. No tolerance exists in this function or anywhere it is called from.
# ---------------------------------------------------------------------------
def identical(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return False
    if isinstance(a, int) and isinstance(b, int):
        return a == b
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if math.isnan(fa) or math.isnan(fb):
        return False          # a NaN pair reads as zero difference; never bind it
    return struct.pack("<d", fa) == struct.pack("<d", fb)


# ---------------------------------------------------------------------------
# VERIFIER-CAUSED EXECUTION
# ---------------------------------------------------------------------------
def receipt_root(receipt_path: Path) -> Path:
    """Leg directory. A receipt at <root>/results/probe.json has legs at <root>."""
    parent = receipt_path.parent
    if parent.name == "results":
        return parent.parent
    return parent


def _run(interpreter: str, script: Path, cwd: Path):
    """Run a leg the VERIFIER chose, in a process the verifier started."""
    exe = INTERPRETERS.get(interpreter)
    if exe is None or not Path(exe).exists():
        return None, f"interpreter {interpreter!r} is not on the gate-owned table"
    cmd = [exe] + (JULIA_ARGS if interpreter == "julia" else []) + [str(script)]
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    try:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True,
                           timeout=RUN_TIMEOUT_S, env=env)
    except subprocess.TimeoutExpired:
        return None, f"leg exceeded {RUN_TIMEOUT_S}s"
    except OSError as exc:
        return None, f"leg could not be started ({exc})"
    if p.returncode != 0:
        tail = p.stderr.decode("utf-8", "replace").strip().splitlines()[-1:] or [""]
        return None, f"leg exited {p.returncode} ({tail[0][:180]})"
    return p.stdout, None


def _perturb_floats(obj, fn):
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        return fn(obj)
    if isinstance(obj, dict):
        return {k: _perturb_floats(v, fn) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_perturb_floats(v, fn) for v in obj]
    return obj


def dependence_probe(art, root: Path, script: Path, pointers):
    """Does the value at each bound artifact pointer MOVE when the DECLARED
    INPUTS move?

    This is the corrected form of the mutation control that engine_witness got
    wrong twice. F5 scored ANY nonzero exit as a pass, so a leg that hashes its
    own source and exits 3 passed a control designed to prove the opposite. F6
    passed when ANY shared numeric field moved and perturbed only the LAST
    literal, so a decoy field satisfied it while every claimed observable stayed
    constant. Here the probe is PER BOUND POINTER — the exact position the
    receipt cites must move — and a crash or unparseable output scores
    UNDETERMINED, never a pass.
    """
    result = {p: "UNDETERMINED" for p in pointers}
    notes = []
    inputs = art.get("inputs") or []
    if not inputs:
        notes.append("no declared inputs: nothing to vary, so dependence is UNDETERMINED")
        return result, notes

    docs = {}
    for rel in inputs:
        ip = (root / str(rel)).resolve()
        if not str(ip).startswith(str(root.resolve()) + os.sep) or not ip.is_file():
            notes.append(f"declared input {rel!r} does not resolve inside the receipt root")
            return result, notes
        try:
            docs[rel] = strict_parse(ip.read_bytes())
        except Exception as exc:  # noqa: BLE001
            notes.append(f"declared input {rel!r} is not a strict-parseable JSON document ({exc})")
            return result, notes
        if not numeric_leaves(docs[rel]):
            notes.append(f"declared input {rel!r} carries no numeric leaf to vary")

    moved = {p: False for p in pointers}
    determined = {p: False for p in pointers}
    for name, fn in PERTURBATIONS:
        tmp = Path(tempfile.mkdtemp(prefix="cg_bind_dep_"))
        try:
            work = tmp / "leg"
            shutil.copytree(root, work, symlinks=True)
            changed_any = False
            for rel, doc in docs.items():
                new = _perturb_floats(doc, fn)
                if json.dumps(new, sort_keys=True) != json.dumps(doc, sort_keys=True):
                    changed_any = True
                (work / str(rel)).write_text(json.dumps(new), encoding="utf-8")
            if not changed_any:
                notes.append(f"probe {name}: declared inputs hold no float leaf; probe is vacuous")
                continue
            out, err = _run(art["interpreter"], work / script.relative_to(root), work)
            if out is None:
                notes.append(f"probe {name}: perturbed run did not complete ({err}) — "
                             f"UNDETERMINED, a crash is not evidence about any check")
                continue
            try:
                pdoc = strict_parse(out)
            except Exception as exc:  # noqa: BLE001
                notes.append(f"probe {name}: perturbed output not strict-parseable ({exc}) — UNDETERMINED")
                continue
            for p in pointers:
                ok, val = resolve_pointer(pdoc, p)
                if not ok:
                    notes.append(f"probe {name}: pointer {p} absent from perturbed output — "
                                 f"UNDETERMINED for that pointer")
                    continue
                determined[p] = True
                base_ok, base = resolve_pointer(art["_baseline_doc"], p)
                if base_ok and not identical(base, val):
                    moved[p] = True
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    for p in pointers:
        if moved[p]:
            result[p] = "INPUT_DEPENDENT"
        elif determined[p]:
            result[p] = "INPUT_INDEPENDENT"
    return result, notes


# ---------------------------------------------------------------------------
# THE GATE
# ---------------------------------------------------------------------------
def evaluate(receipt_path: Path):
    v = {
        "gate": "artifact_binding",
        "receipt": str(receipt_path),
        "float_semantics": ("int/int exact integer equality; otherwise exact IEEE-754 "
                            "float64 bit identity (struct.pack '<d'). No tolerance, "
                            "epsilon, significant-digit budget or bound is read from the "
                            "receipt, the environment, or any library parameter."),
        "exemptions": {"key_names": [], "paths": [], "types": [], "bounds": [],
                       "_note": "empty by design: the denominator is every numeric leaf"},
        "blocks": [], "artifacts": [], "covered": [], "uncovered": [],
    }
    if not receipt_path.exists():
        v["blocks"].append(f"required artifact absent: {receipt_path}")
        v["disposition"] = "BLOCK_MISSING_RECEIPT"
        return v, 1

    raw = receipt_path.read_bytes()
    v["receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    try:
        receipt = strict_parse(raw)
    except Exception as exc:  # noqa: BLE001
        v["blocks"].append(f"strict parse refused the receipt bytes: {exc}")
        v["disposition"] = "BLOCK_UNPARSEABLE"
        return v, 1

    leaves = numeric_leaves(receipt)
    v["numeric_leaf_count"] = len(leaves)

    ab = receipt.get("artifact_binding") if isinstance(receipt, dict) else None
    if ab is not None and not isinstance(ab, dict):
        v["blocks"].append(f"artifact_binding is a {type(ab).__name__}, not an object; a "
                           f"malformed binding block is refused, never read as absent")
        ab = None
    arts_decl = (ab or {}).get("artifacts")
    binds_decl = (ab or {}).get("bindings")
    for name, val in (("artifacts", arts_decl), ("bindings", binds_decl)):
        if val is not None and not isinstance(val, list):
            v["blocks"].append(f"artifact_binding.{name} is a {type(val).__name__}, not a list")
    arts_decl = arts_decl if isinstance(arts_decl, list) else []
    binds_decl = binds_decl if isinstance(binds_decl, list) else []

    # ---- regenerate every declared artifact, verifier-caused ----------------
    root = receipt_root(receipt_path)
    arts = {}
    for a in arts_decl:
        if not isinstance(a, dict):
            v["blocks"].append("artifact_binding.artifacts holds a non-object entry")
            continue
        aid = str(a.get("artifact_id"))
        rec = {"artifact_id": aid, "interpreter": a.get("interpreter"),
               "script": a.get("script"), "inputs": a.get("inputs") or [],
               "declared_stdout_sha256": a.get("stdout_sha256")}
        v["artifacts"].append(rec)
        if a.get("interpreter") not in INTERPRETERS:
            v["blocks"].append(f"artifact {aid}: interpreter {a.get('interpreter')!r} is not "
                               f"on the gate-owned table {sorted(INTERPRETERS)}")
            continue
        script = (root / str(a.get("script") or "")).resolve()
        # checked AFTER resolution, never by a regex on the string
        if not str(script).startswith(str(root.resolve()) + os.sep) or not script.is_file():
            v["blocks"].append(f"artifact {aid}: script {a.get('script')!r} does not resolve "
                               f"to a file inside the receipt root {root}")
            continue

        out1, err1 = _run(a["interpreter"], script, root)
        if out1 is None:
            v["blocks"].append(f"artifact {aid}: the verifier could not regenerate it ({err1})")
            continue
        out2, err2 = _run(a["interpreter"], script, root)
        rec["regenerated_stdout_sha256"] = hashlib.sha256(out1).hexdigest()
        if out2 is None or out1 != out2:
            rec["deterministic"] = False
            v["blocks"].append(f"artifact {aid}: two verifier-caused runs disagreed, so no "
                               f"digest can be pinned (nondeterminism must be declared, "
                               f"not absorbed by a per-leg tolerance)")
            continue
        rec["deterministic"] = True
        if rec["declared_stdout_sha256"] != rec["regenerated_stdout_sha256"]:
            v["blocks"].append(f"artifact {aid}: recorded stdout_sha256 "
                               f"{rec['declared_stdout_sha256']} does not match the "
                               f"verifier-regenerated {rec['regenerated_stdout_sha256']}")
            continue
        try:
            doc = strict_parse(out1)
        except Exception as exc:  # noqa: BLE001
            v["blocks"].append(f"artifact {aid}: regenerated output is not a strict-parseable "
                               f"JSON document ({exc})")
            continue
        arts[aid] = {"interpreter": a["interpreter"], "script": script,
                     "inputs": rec["inputs"], "_baseline_doc": doc, "_rec": rec}

    # ---- resolve every declared binding ------------------------------------
    bound = {}          # receipt_pointer -> binding record
    seen_slots = {}     # (artifact_id, artifact_pointer) -> receipt_pointer
    for b in binds_decl:
        if not isinstance(b, dict):
            v["blocks"].append("artifact_binding.bindings holds a non-object entry")
            continue
        rp, aid, ap = str(b.get("receipt_pointer")), str(b.get("artifact_id")), str(b.get("artifact_pointer"))
        if rp in bound:
            v["blocks"].append(f"binding {rp}: declared twice")
            continue
        if aid not in arts:
            v["blocks"].append(f"binding {rp}: artifact {aid!r} was not regenerated, so the "
                               f"binding cannot resolve")
            continue
        slot = (aid, ap)
        if slot in seen_slots:
            v["blocks"].append(f"binding {rp}: artifact position {aid}{ap} is already bound by "
                               f"{seen_slots[slot]} — one artifact position cannot discharge "
                               f"two receipt claims")
            continue
        seen_slots[slot] = rp
        r_ok, r_val = resolve_pointer(receipt, rp)
        if not r_ok:
            v["blocks"].append(f"binding {rp}: that pointer does not resolve in the receipt")
            continue
        a_ok, a_val = resolve_pointer(arts[aid]["_baseline_doc"], ap)
        if not a_ok:
            v["blocks"].append(f"binding {rp}: artifact position {aid}{ap} does not exist")
            continue
        if isinstance(r_val, str):
            r_val = _as_number(r_val)
        if isinstance(a_val, str):
            a_val = _as_number(a_val)
        if r_val is None or a_val is None:
            v["blocks"].append(f"binding {rp}: one side is not a number")
            continue
        if not identical(r_val, a_val):
            v["blocks"].append(f"binding {rp}: receipt holds {r_val!r} and artifact position "
                               f"{aid}{ap} holds {a_val!r} — not identical")
            continue
        bound[rp] = {"artifact_id": aid, "artifact_pointer": ap, "value": r_val}

    # ---- input-dependence, per bound artifact position ---------------------
    for aid, art in arts.items():
        ptrs = sorted({rec["artifact_pointer"] for rec in bound.values()
                       if rec["artifact_id"] == aid})
        if not ptrs:
            art["_rec"]["dependence"] = {}
            art["_rec"]["dependence_notes"] = ["no bound position in this artifact"]
            continue
        dep, notes = dependence_probe(art, root, art["script"], ptrs)
        art["_rec"]["dependence"] = dep
        art["_rec"]["dependence_notes"] = notes
        for rp, rec in bound.items():
            if rec["artifact_id"] == aid:
                rec["dependence"] = dep.get(rec["artifact_pointer"], "UNDETERMINED")

    # ---- verdict over the FULL denominator ---------------------------------
    declared_ptrs = {str(b.get("receipt_pointer")) for b in binds_decl if isinstance(b, dict)}
    for ptr, val, kind in leaves:
        rec = bound.get(ptr)
        if rec is None:
            reason = ("BINDING_DECLARED_BUT_FAILED — a binding names this leaf and did not "
                      "survive; see blocks"
                      if ptr in declared_ptrs else
                      "UNBOUND — no declared binding names this leaf")
            v["uncovered"].append({"pointer": ptr, "value": val, "kind": kind, "reason": reason})
            continue
        if rec.get("dependence") == "INPUT_DEPENDENT":
            v["covered"].append({"pointer": ptr, "value": val, "kind": kind,
                                 "artifact_id": rec["artifact_id"],
                                 "artifact_pointer": rec["artifact_pointer"],
                                 "dependence": rec["dependence"]})
        else:
            v["uncovered"].append({
                "pointer": ptr, "value": val, "kind": kind,
                "reason": f"BOUND_BUT_{rec.get('dependence', 'UNDETERMINED')} — the artifact "
                          f"position reproduces the value, but varying the declared inputs did "
                          f"not show the value is a function of them"})

    v["covered_count"] = len(v["covered"])
    v["uncovered_count"] = len(v["uncovered"])

    if v["blocks"]:
        v["disposition"] = "BLOCK_BINDING_FAILED"
        return v, 1
    if not leaves:
        v["disposition"] = "PARK_VACUOUS_NO_NUMERIC_LEAF"
        v["_why"] = ("a receipt with no numeric leaf witnesses no number; an obligation "
                     "discharged is not a number witnessed, so this is never COVERED")
        return v, 3
    if v["uncovered"]:
        v["disposition"] = "PARK_UNBOUND_NUMERIC_CLAIM"
        v["_why"] = ("an unbound number is missing evidence, not a proven fabrication, so it "
                     "PARKs; PARK must keep blocking and must never be reissued as an "
                     "ADMITTED_PENDING_* label, which is an ADMITTING disposition")
        return v, 3
    v["disposition"] = "COVERED"
    v["_strength_note"] = ("coverage strength is NON-UNIFORM and is reported, never gated: it is "
                           "near-conclusive for a distinctive value and near-vacuous for a small "
                           "integer that occurs everywhere. A multiplicity threshold would be a "
                           "bound, and a bound is design 4.")
    return v, 0


def main(argv):
    if len(argv) != 2:
        print("usage: artifact_binding.py <receipt.json>", file=sys.stderr)
        return 2
    try:
        verdict, code = evaluate(Path(argv[1]).resolve())
    except RecursionError:
        print("artifact_binding: BLOCK — document nesting exceeded the interpreter's "
              "recursion limit; failing CLOSED", file=sys.stderr)
        print(json.dumps({"gate": "artifact_binding", "disposition": "BLOCK_RECURSION",
                          "exit": 1}))
        return 1
    except Exception as exc:  # noqa: BLE001
        # evaluate() sitting outside a handler is a recorded defect in this estate:
        # receipt_grammar exited 1 with ZERO bytes on stdout, so an exit-code consumer
        # failed closed while a stdout consumer got nothing to attribute the refusal to.
        print(f"artifact_binding: BLOCK — the gate could not complete "
              f"({type(exc).__name__}: {exc}); failing CLOSED", file=sys.stderr)
        print(json.dumps({"gate": "artifact_binding", "disposition": "BLOCK_GATE_ERROR",
                          "error": f"{type(exc).__name__}: {exc}", "exit": 1}))
        return 1
    verdict["exit"] = code
    print(json.dumps(verdict, indent=1, default=str))
    print(f"artifact_binding: {verdict['disposition']} — "
          f"{verdict.get('covered_count', 0)}/{verdict.get('numeric_leaf_count', 0)} numeric "
          f"leaves covered, {len(verdict['blocks'])} block(s)", file=sys.stderr)
    for u in verdict["uncovered"][:6]:
        print(f"  UNCOVERED {u['pointer'] or '<root>'} = {u['value']!r}  [{u['reason']}]",
              file=sys.stderr)
    for b in verdict["blocks"][:6]:
        print(f"  BLOCK {b}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
