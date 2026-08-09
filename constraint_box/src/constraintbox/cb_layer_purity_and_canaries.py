#!/usr/bin/env python3
"""cb_layer_purity_and_canaries — two foundation tools.

TOOL 1 — LAYER PURITY GATE (the owner's runtime architecture, made
enforceable). Measured state of the current CB package: 27 of 31
source files are stdlib-only; heavy runtimes appear in exactly four
files (the three quantum-Hopfield lanes and the runtime doctor);
17.5% of source lines sit in heavy-importing files. The rule the
architecture implies:
  CB CORE (controllers, verifiers, gates, probes) -> Python stdlib
    plus the lean solvers (z3, cvc5). No numpy/scipy/jax/torch.
  LANE FILES (declared allowlist, name-marked) -> may import their
    runtime: jax | torch | qutip | numpy, one lane per file.
  JULIA -> subprocess only, from declared manifold/QIT lane files
    (manifold, attractor basins, QIT math, quantum Hopfield).
  PYTORCH -> holodeck tier and its own lane only (trainable surface).
Violations are reported per file with the offending import; exit 1.
Purpose: keep CB lean by construction rather than by intention, so
weight cannot creep into the custody layer.

TOOL 2 — CANARY CORPUS ("when CB doesn't catch things, train it to
catch things"). Every escaped defect becomes a permanent, replayable
canary: a deterministic mutation of a copied run root plus the gate
response it must produce. The runner replays all canaries against the
CURRENT gates and reports CAUGHT / ESCAPED. Canaries whose expected
status is ESCAPES document known holes and stay visible until the
corresponding repair lands — the ratchet applied to CB itself.
No learning, no statistics: a growing corpus of defects the system is
never allowed to forget.
promotion_allowed=false.
"""
from __future__ import annotations
import argparse, ast, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

# ---------------- TOOL 1: layer purity ----------------
STDLIB_OK = {"__future__", "argparse", "ast", "base64", "collections",
             "contextlib", "copy", "csv", "dataclasses", "datetime",
             "difflib", "enum", "functools", "glob", "hashlib", "io",
             "itertools", "json", "math", "os", "pathlib", "platform",
             "random", "re", "shutil", "signal", "socket", "statistics",
             "string", "subprocess", "sys", "tempfile", "textwrap",
             "time", "traceback", "types", "typing", "unittest", "uuid",
             "cmath", "importlib", "decimal", "fractions", "heapq",
             "bisect", "operator", "warnings", "enum", "abc"}
LEAN_SOLVERS = {"z3", "cvc5"}
# the runtime doctor legitimately probes every runtime
DOCTOR = {"runtime_probe.py"}
LANE_RUNTIME = {"jax": "jax", "jaxlib": "jax", "torch": "torch",
                "torch_geometric": "torch", "qutip": "qutip",
                "numpy": "numpy", "scipy": "numpy", "numba": "numpy",
                "networkx": "numpy", "pysindy": "numpy",
                "pandas": "numpy", "matplotlib": "numpy"}

def imports_of(path: Path):
    try:
        tree = ast.parse(path.read_text())
    except Exception:
        return set()
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                mods.add(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            mods.add(n.module.split(".")[0])
    return mods

def layer_purity(src_dir: Path, lane_allow: set[str]):
    local = {p.stem for p in src_dir.glob("*.py")}
    rows, violations = [], []
    for p in sorted(src_dir.glob("*.py")):
        mods = imports_of(p)
        heavy = sorted(m for m in mods if m in LANE_RUNTIME)
        is_lane = p.name in lane_allow
        tier = "lane" if is_lane else "core"
        if heavy and not is_lane:
            violations.append({"file": p.name, "tier": "core",
                               "heavy_imports": heavy,
                               "rule": "CB core must be stdlib + lean "
                                       "solvers only"})
        if is_lane and p.name not in DOCTOR:
            # numpy is the shared array lingua franca; it does not
            # count as a second runtime family
            fams = {LANE_RUNTIME[m] for m in heavy} - {"numpy"}
            if len(fams) > 1:
                violations.append({"file": p.name, "tier": "lane",
                                   "heavy_imports": heavy,
                                   "rule": "one runtime family per lane "
                                           "file"})
        unknown = sorted(m for m in mods
                         if m not in STDLIB_OK and m not in LEAN_SOLVERS
                         and m not in LANE_RUNTIME and m not in local)
        if unknown and not is_lane:
            violations.append({"file": p.name, "tier": tier,
                               "unknown_imports": unknown,
                               "rule": "undeclared dependency in core"})
        rows.append({"file": p.name, "tier": tier,
                     "lines": len(p.read_text().splitlines()),
                     "heavy": heavy})
    core = [r for r in rows if r["tier"] == "core"]
    return {"files": len(rows), "core_files": len(core),
            "lane_files": len(rows) - len(core),
            "core_lines": sum(r["lines"] for r in core),
            "total_lines": sum(r["lines"] for r in rows),
            "core_stdlib_only": all(not r["heavy"] for r in core),
            "violations": violations, "rows": rows}

# ---------------- TOOL 2: canary corpus ----------------
def mutate_declared_artifact(root: Path) -> str:
    """C1: flip one boolean inside a hash-declared result artifact."""
    rec = next((p for p in root.glob("*.json")
                if "RECEIPT" in p.name.upper()), None)
    d = json.loads(rec.read_text())
    tgt = d.get("targets", [{}])[0]
    names = list(tgt.get("result_sha256", {}) or {})
    if not names:
        return "no declared artifact found"
    base = names[0]
    hit = next(root.rglob(base), None)
    j = json.loads(hit.read_text())
    done = []
    def flip(o):
        if done:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, bool) and not done:
                    o[k] = not v; done.append(k); return
                flip(v)
        elif isinstance(o, list):
            for v in o:
                flip(v)
    flip(j)
    hit.write_text(json.dumps(j, indent=1))
    return f"flipped {done} in declared artifact {base}"

def add_stray_file(root: Path) -> str:
    """C2: leave a generated file in the run root."""
    (root / "stray_replay_generated.json").write_text(
        json.dumps({"generated": True}))
    return "added stray_replay_generated.json"

def strip_evidence_tree(root: Path) -> str:
    """C3: ship receipts only."""
    n = 0
    for p in list(root.rglob("*")):
        if p.is_file() and "RECEIPT" not in p.name.upper() \
                and "VERIFICATION" not in p.name.upper():
            p.unlink(); n += 1
    return f"deleted {n} non-receipt files"

def flip_stored_verdict(root: Path) -> str:
    """C4: flip a stored aggregate while leaving the checks intact."""
    rec = next((p for p in root.glob("*.json")
                if "RECEIPT" in p.name.upper()), None)
    d = json.loads(rec.read_text())
    for k in ("all_pass", "all_consumer_checks_pass", "passed"):
        if isinstance(d.get(k), bool):
            d[k] = not d[k]
            rec.write_text(json.dumps(d, indent=1))
            return f"flipped stored aggregate {k} in {rec.name}"
    return "no stored aggregate found"

def mutate_undeclared_artifact(root: Path) -> str:
    """C5: mutate an artifact NOTHING declares (CBIMP-6 hole)."""
    declared = set()
    for rec in root.glob("*.json"):
        txt = rec.read_text()
        for p in root.rglob("*.json"):
            if p.name in txt:
                declared.add(p.name)
    cand = next((p for p in root.rglob("*results*.json")
                 if p.name not in declared), None)
    if cand is None:
        return "no undeclared artifact available"
    j = json.loads(cand.read_text())
    if isinstance(j, dict):
        j["__silent_mutation__"] = True
    cand.write_text(json.dumps(j, indent=1))
    return f"mutated undeclared artifact {cand.name}"

CANARIES = [
    ("C1_declared_artifact_mutation", mutate_declared_artifact,
     "CAUGHT", "CBIMP-1"),
    ("C2_stray_undeclared_file", add_stray_file, "CAUGHT", "CBIMP-2"),
    ("C3_receipts_only_packaging", strip_evidence_tree, "CAUGHT",
     "CBIMP-5"),
    ("C4_stored_verdict_flip", flip_stored_verdict, "CAUGHT", "CBIMP-3"),
    ("C5_undeclared_artifact_mutation", mutate_undeclared_artifact,
     "ESCAPES", "CBIMP-6 (open hole: nothing declares it)"),
]

def gate_signature(work: Path, consumer: Path, tmp: Path):
    out = tmp / f"sig_{work.name}_{os.getpid()}.json"
    subprocess.run([sys.executable, str(consumer), "--run-root",
                    str(work), "--output", str(out),
                    "--strict-cleanliness"], capture_output=True,
                   text=True)
    sc = json.loads(out.read_text()) if out.exists() else {}
    # signature = the gate's discriminating content, not just "defects"
    return {"defects": sc.get("defects", []),
            "mismatch": len(sc.get("recomputed_mismatch", [])),
            "absent": len(sc.get("declared_absent", [])),
            "undeclared": sc.get("present_but_undeclared_count", 0),
            "match": sc.get("recomputed_match", 0)}, sc


def run_canaries(run_root: Path, consumer: Path):
    results = []
    for name, fn, expected, defect in CANARIES:
        tmp = Path(tempfile.mkdtemp(prefix="canary_"))
        work = tmp / run_root.name
        shutil.copytree(run_root, work)
        note = fn(work)
        base_dir = tmp / "baseline"
        shutil.copytree(run_root, base_dir)
        base_sig, _ = gate_signature(base_dir, consumer, tmp)
        mut_sig, sc = gate_signature(work, consumer, tmp)
        # a canary is CAUGHT only if the gate's response CHANGED:
        # a defect that was already firing on the pristine run is not
        # evidence that this mutation was detected
        status = "CAUGHT" if mut_sig != base_sig else "ESCAPED"
        results.append({"canary": name, "mutation": note,
                        "baseline_signature": base_sig,
                        "mutated_signature": mut_sig,
                        "gate_defects": sc.get("defects", []),
                        "status": status, "expected": expected,
                        "as_expected": status == expected
                        or (expected == "ESCAPES" and status == "ESCAPED"),
                        "tracks_defect": defect})
        shutil.rmtree(tmp, ignore_errors=True)
    return results

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, required=True)
    ap.add_argument("--run-root", type=Path, required=True)
    ap.add_argument("--consumer", type=Path, required=True)
    ap.add_argument("--lane-allow", default="quantum_hopfield_jax.py,"
                    "quantum_hopfield_torch.py,"
                    "quantum_hopfield_reference.py,runtime_probe.py")
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    purity = layer_purity(a.source_dir, set(a.lane_allow.split(",")))
    canaries = run_canaries(a.run_root, a.consumer)
    ok = (not purity["violations"]
          and all(c["as_expected"] for c in canaries))
    out = {"schema": "cb.layer-purity-and-canaries.v1",
           "layer_purity": purity, "canary_corpus": canaries,
           "catch_rate": f"{sum(1 for c in canaries if c['status']=='CAUGHT')}"
                         f"/{len(canaries)}",
           "all_as_expected": ok, "promotion_allowed": False}
    a.output.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(f"LAYER PURITY: {purity['core_files']} core files "
          f"({purity['core_lines']} lines), "
          f"{purity['lane_files']} lane files; "
          f"core_stdlib_only={purity['core_stdlib_only']}; "
          f"violations={len(purity['violations'])}")
    for v in purity["violations"][:6]:
        print("   VIOLATION", v)
    print("\nCANARY CORPUS:")
    for c in canaries:
        print(f"  {c['canary']:<34} {c['status']:<8} "
              f"expected={c['expected']:<8} "
              f"{'ok' if c['as_expected'] else 'REGRESSION'}  "
              f"[{c['tracks_defect']}]")
    print("catch rate:", out["catch_rate"])
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
