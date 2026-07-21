#!/usr/bin/env python3
"""
canfail_probe — deterministic mutation test: which checks CAN actually fail?

The corpus-wide finding (every LLM audit agreed): ~half of each all_pass=N/N is
deterministic code that CANNOT fail on the data — entropy theorems, algebraic
identities, symmetry-forced controls. They inflate the gate count. The auditors
caught them by hand: patch the constant that severs a mechanism (GAMMA_BASE=0),
re-run, see if the verdict moves. This tool does that severing DETERMINISTICALLY.

    canfail_probe <spec.json> [--json]
        exit 0 = every claimed check flipped under some tested mutation
        exit 3 = SUSPECT checks found (never flipped -> candidate by-construction)
        exit 2 = usage / IO error

Honest framing (the whole point):
  - A check that FLIPS under a mutation is POSITIVELY PROVEN can-fail.
  - A check that flips under NO tested mutation is SUSPECT_BY_CONSTRUCTION —
    either a true-but-cannot-fail identity, OR its severing mutation is not in
    the deck. The tool proves can-fail and names the deck; it never declares a
    check dead without saying which mutations were tried.
  This is "controls must flip" as code: a genuine check names a mutation that
  breaks it. all_pass should count only CAN_FAIL checks.

Mechanism (robust): each run happens in an ISOLATED temp dir with a COPY of the
sim whose top-level constant assignments are regex-patched. The copy is run as a
subprocess, writes its receipt into the temp tree (Path(__file__).parent/results),
and the real repo is never touched. In-process monkeypatching is NOT used — some
sims re-exec/re-import internally and silently revert a patched global.

spec.json:
  { "sim": "system_v8/nested_manifold/manifold_one.py",
    "checks_key": "checks",           # dict name->bool in the receipt
    "receipt_glob": "results/manifold_one/receipt.json",  # path under the sim's dir
    "mutations": [
      {"name": "sever_drive_quantum", "set": {"GAMMA_BASE": 0.0}},
      {"name": "sever_outer_nesting", "set": {"OUTER": {"Delta4":0.0}}} ] }
Only top-level `NAME = ...` assignments are patchable (they are what the sim reads).

No third-party deps beyond the sim's own. Python 3.
"""
import json, os, re, sys, shutil, tempfile, subprocess, glob, ast

def die(m, c=2): sys.stderr.write(f"canfail_probe: {m}\n"); sys.exit(c)

def patch_source(src, overrides):
    """Replace top-level `NAME = <expr>` (even MULTI-LINE dicts/lists) with the
    override literal, using AST line spans so a multi-line constant is fully
    replaced (the old regex left dangling fragments -> IndentationError). Returns
    (new_src, missed)."""
    missed = []
    lines = src.split("\n")
    spans = {}
    try:
        tree = ast.parse(src)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id in overrides:
                        spans[t.id] = (node.lineno, getattr(node, "end_lineno", node.lineno))
    except SyntaxError:
        spans = {}
    edits = []
    for name, val in overrides.items():
        if name in spans:
            edits.append((spans[name][0], spans[name][1], f"{name} = {json.dumps(val)}"))
        else:
            missed.append(name)
    for start, end, rep in sorted(edits, key=lambda e: -e[0]):   # bottom-to-top keeps indices valid
        lines[start - 1:end] = [rep]
    return "\n".join(lines), missed

def run_variant(sim_path, overrides, receipt_rel, checks_key):
    """Copy the sim into a temp dir with constants patched, run it, read the receipt.
    Returns (checks_dict_or_None, missed, err). A crashing variant returns None +
    the error — the caller records it and continues (one bad mutation must not
    abort the whole probe, and a crash is NOT evidence about any check)."""
    sim_dir = os.path.dirname(os.path.abspath(sim_path))
    src = open(sim_path).read()
    patched, missed = patch_source(src, overrides) if overrides else (src, [])
    with tempfile.TemporaryDirectory() as td:
        for f in os.listdir(sim_dir):
            fp = os.path.join(sim_dir, f)
            if os.path.isfile(fp) and f.endswith((".py", ".json", ".txt")):
                shutil.copy2(fp, os.path.join(td, f))
        open(os.path.join(td, os.path.basename(sim_path)), "w").write(patched)
        try:
            r = subprocess.run([sys.executable, os.path.basename(sim_path)], cwd=td,
                               capture_output=True, text=True, timeout=1800)
        except Exception as e:
            return None, missed, f"subprocess error: {e}"
        cand = os.path.join(td, receipt_rel)
        if not os.path.exists(cand):
            found = glob.glob(os.path.join(td, "**", "receipt.json"), recursive=True)
            cand = found[0] if found else None
        if not cand or not os.path.exists(cand):
            return None, missed, f"no receipt (rc={r.returncode}); {r.stderr[-160:]}"
        checks = json.load(open(cand)).get(checks_key, {})
        return {k: bool(v) for k, v in checks.items()}, missed, None

def main():
    args = sys.argv[1:]
    spec_path = next((a for a in args if not a.startswith("--")), None)
    if not spec_path: die("usage: canfail_probe <spec.json> [--json]")
    spec = json.load(open(spec_path))
    # resolve the sim's repo-relative path against the repo root (walk up from the
    # spec file to find .git), so the result is independent of the caller's cwd
    d = os.path.dirname(os.path.abspath(spec_path))
    root = d
    while root != "/" and not os.path.isdir(os.path.join(root, ".git")):
        root = os.path.dirname(root)
    if root == "/": root = os.getcwd()
    sim = spec["sim"] if os.path.isabs(spec["sim"]) else os.path.join(root, spec["sim"])
    if not os.path.exists(sim): die(f"sim not found: {sim}")
    ckey = spec.get("checks_key", "checks")
    receipt_rel = spec.get("receipt_glob") or "results/receipt.json"

    base, _, berr = run_variant(sim, None, receipt_rel, ckey)
    if not base: die(f"baseline produced no checks: {berr}")

    muts = spec.get("mutations") or []
    if not muts: die("spec has no mutations — a can-fail probe needs a mutation deck that severs each claimed mechanism")

    flips = {k: [] for k in base}
    targeted = {k: False for k in base}   # was this check named as a target of a mutation that ACTUALLY RAN?
    mlog = []
    for mut in muts:
        mutated, missed, err = run_variant(sim, mut["set"], receipt_rel, ckey)
        if mutated is None:
            # a crash is not evidence about any check; record and move on, do not mark targeted
            mlog.append({"mutation": mut["name"], "set": mut["set"], "targets": mut.get("targets", []),
                         "crashed": err, "flipped": []})
            continue
        for k in mut.get("targets", []):
            if k in targeted: targeted[k] = True   # only after a successful run
        changed = [k for k in base if k in mutated and mutated[k] != base[k]]
        for k in changed: flips[k].append(mut["name"])
        mlog.append({"mutation": mut["name"], "set": mut["set"], "targets": mut.get("targets", []),
                     "missed_consts": missed, "flipped": changed})

    # three honest classes — the corpus workflow flagged that lumping them lies:
    #   CAN_FAIL          : flipped under some mutation (proven genuine)
    #   BY_CONSTRUCTION   : a mutation TARGETED it (claims to sever its mechanism) yet it never flipped
    #   UNTESTED          : no mutation targeted it — deck gap, NOT a verdict on the check
    can_fail = [k for k, v in flips.items() if v]
    by_construction = [k for k, v in flips.items() if not v and targeted[k]]
    untested = [k for k, v in flips.items() if not v and not targeted[k]]
    report = {
        "tool": "canfail_probe", "sim": spec["sim"],
        "mutations_tried": [m["name"] for m in muts],
        "n_checks": len(base),
        "can_fail": can_fail,
        "by_construction": by_construction,           # targeted-but-never-flipped = real finding
        "untested": untested,                          # deck did not reach the mechanism
        "can_fail_ratio": round(len(can_fail) / len(base), 3) if base else 0.0,
        "honest_all_pass_count": f"{len(can_fail)} proven can-fail, {len(by_construction)} by-construction, {len(untested)} untested, of {len(base)} claimed",
        "per_mutation": mlog,
    }
    print(json.dumps(report, indent=1))
    # exit 1 iff a by-construction check was PROVEN (targeted, never flipped); untested alone is exit 3 (incomplete), clean is 0
    sys.exit(1 if by_construction else (3 if untested else 0))

if __name__ == "__main__":
    main()
