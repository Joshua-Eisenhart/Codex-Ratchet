#!/usr/bin/env python3
"""
canfail_probe — deterministic mutation test: which checks CAN actually fail?

The corpus-wide finding (every LLM audit agreed): ~half of each all_pass=N/N is
deterministic code that CANNOT fail on the data — entropy theorems, algebraic
identities, symmetry-forced controls. They inflate the gate count. The auditors
caught them by hand: patch the constant that severs a mechanism (GAMMA_BASE=0),
re-run, see if the verdict moves. This tool does that severing DETERMINISTICALLY.

    canfail_probe <spec.json> [--json]
        exit 0 = every claimed check flipped under some non-crashing mutation
        exit 1 = BY_CONSTRUCTION found (cleanly targeted, never flipped) — finding
        exit 4 = SUSPECT found (targeting mutations ALL crashed — could not test;
                 a crash must NOT downgrade a targeted check to a clean deck-gap)
        exit 3 = UNTESTED only (no mutation reached the check) — genuine deck gap
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

def _first_positional_name(args):
    """First positional-or-keyword param name of an ast.arguments node, or None."""
    if args.posonlyargs:
        return args.posonlyargs[0].arg
    if args.args:
        return args.args[0].arg
    return None


def _returns_tuple(func_node):
    for n in ast.walk(func_node):
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Tuple):
            return len(n.value.elts)
    return None


def _returns_dictish(func_node):
    for n in ast.walk(func_node):
        if isinstance(n, ast.Return) and n.value is not None:
            v = n.value
            if isinstance(v, ast.Dict):
                return True
            if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "dict":
                return True
    return False


def _returns_listish(func_node):
    for n in ast.walk(func_node):
        if isinstance(n, ast.Return) and n.value is not None:
            v = n.value
            if isinstance(v, ast.List):
                return True
            if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "list":
                return True
    return False


def _returns_setish(func_node):
    for n in ast.walk(func_node):
        if isinstance(n, ast.Return) and n.value is not None:
            v = n.value
            if isinstance(v, ast.Set):
                return True
            if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "set":
                return True
    return False


def _indent_of(line):
    return line[:len(line) - len(line.lstrip(" "))]


def patch_function(src, func_name, mode, warnings=None):
    """AST-replace a module-level function's BODY (signature line kept as-is),
    using the same bottom-to-top end_lineno-span convention as patch_source.

    'identity'      -> body is `return <first_positional_param>` (or `return
                       None` if the function takes no positional args — a
                       recorded fallback, not a crash).
    'zero'          -> best-effort zero-like return, matched against the
                       function's OWN return statements (never deep type
                       inference, just enough to dodge the common unpack
                       crash): a Tuple return -> tuple of 0.0 of matching
                       arity; a Dict/dict(...) return -> {}; a List/list(...)
                       return -> []; a Set/set(...) return -> set(); else
                       plain 0.0.
    'shuffle_args'  -> keeps a renamed `_orig_<name>` copy of the ORIGINAL
                       body, and the replacement body swaps the first two
                       positional arg names before calling it. Fewer than 2
                       positional params -> a no-op passthrough wrapper
                       (recorded, not a crash).

    Returns (new_src, missed) — missed=[func_name] if no module-level
    ast.FunctionDef named func_name is found, exactly mirroring patch_source's
    contract so the caller can report a miss without crashing.
    """
    if warnings is None:
        warnings = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return src, [func_name]
    target = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            target = node
            break
    if target is None:
        return src, [func_name]

    lines = src.split("\n")
    start, end = target.lineno, getattr(target, "end_lineno", target.lineno)
    sig_line = lines[start - 1]
    indent = _indent_of(lines[start] if start < len(lines) else "    ")
    if not indent.strip() == "" or indent == "":
        # fall back to a conservative 4-space body indent under the def line
        body_indent = "    "
    else:
        body_indent = indent

    if mode == "identity":
        first = _first_positional_name(target.args)
        if first is None:
            warnings.append(f"{func_name}:identity_no_positional_arg->return None")
            body = [f"{body_indent}return None"]
        else:
            body = [f"{body_indent}return {first}"]
        new_def = [sig_line] + body
    elif mode == "zero":
        arity = _returns_tuple(target)
        if arity:
            body = [f"{body_indent}return (" + ", ".join(["0.0"] * arity) + ("," if arity == 1 else "") + ")"]
        elif _returns_dictish(target):
            body = [f"{body_indent}return {{}}"]
        elif _returns_listish(target):
            body = [f"{body_indent}return []"]
        elif _returns_setish(target):
            body = [f"{body_indent}return set()"]
        else:
            body = [f"{body_indent}return 0.0"]
        new_def = [sig_line] + body
    elif mode == "shuffle_args":
        posargs = [a.arg for a in target.args.posonlyargs] + [a.arg for a in target.args.args]
        orig_name = f"_orig_{func_name}"
        orig_def_lines = list(lines[start - 1:end])
        orig_def_lines[0] = orig_def_lines[0].replace(f"def {func_name}(", f"def {orig_name}(", 1)
        if len(posargs) < 2:
            warnings.append(f"{func_name}:shuffle_args_fewer_than_2_positional_args->passthrough")
            call_args = ", ".join(posargs)
        else:
            swapped = list(posargs)
            swapped[0], swapped[1] = swapped[1], swapped[0]
            call_args = ", ".join(swapped)
        wrapper = [sig_line, f"{body_indent}return {orig_name}({call_args})"]
        new_def = orig_def_lines + wrapper
    else:
        return src, [func_name]

    lines[start - 1:end] = new_def
    return "\n".join(lines), []


def run_variant(sim_path, overrides, receipt_rel, checks_key, defunc=None):
    """Copy the sim into a temp dir with constants (or a named function) patched,
    run it, read the receipt. Returns (checks_dict_or_None, missed, err). A
    crashing variant returns None + the error — the caller records it and
    continues (one bad mutation must not abort the whole probe, and a crash is
    NOT evidence about any check)."""
    sim_dir = os.path.dirname(os.path.abspath(sim_path))
    src = open(sim_path).read()
    if defunc is not None:
        patched, missed = patch_function(src, defunc["defunc"], defunc["mode"])
    else:
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
    targeted = {k: False for k in base}         # named target of a mutation that ran CLEANLY (no crash)
    crashed_target = {k: False for k in base}   # named target of a mutation that CRASHED (could not test)
    mlog = []
    for mut in muts:
        is_defunc = "defunc" in mut
        if is_defunc and "set" in mut:
            die(f"mutation {mut.get('name')!r} has both 'set' and 'defunc' — exactly one required")
        if is_defunc:
            mutated, missed, err = run_variant(sim, None, receipt_rel, ckey, defunc=mut)
        else:
            mutated, missed, err = run_variant(sim, mut["set"], receipt_rel, ckey)
        if is_defunc:
            entry = {"mutation": mut["name"], "defunc": mut["defunc"], "mode": mut["mode"],
                     "targets": mut.get("targets", [])}
        else:
            entry = {"mutation": mut["name"], "set": mut["set"], "targets": mut.get("targets", [])}
        if mutated is None:
            # a crash is NOT evidence a check can fail — but it must NOT downgrade a
            # targeted check to a clean UNTESTED deck-gap (the crash-hides-finding hole:
            # a builder could pick a crashing sever value to bury a by-construction check).
            # Record the targeting independent of the crash so an all-crashed target
            # surfaces as SUSPECT, not clean UNTESTED. This is a distinct third state from
            # `targeted` (clean run): a crashed target was never given a clean chance to flip.
            entry["crashed"] = err
            entry["flipped"] = []
            entry["crash_targets"] = mut.get("targets", [])
            for k in mut.get("targets", []):
                if k in crashed_target: crashed_target[k] = True
            mlog.append(entry)
            continue
        for k in mut.get("targets", []):
            if k in targeted: targeted[k] = True   # only after a successful (non-crashing) run
        changed = [k for k in base if k in mutated and mutated[k] != base[k]]
        for k in changed: flips[k].append(mut["name"])
        entry["missed_consts"] = missed
        entry["flipped"] = changed
        mlog.append(entry)

    # four honest classes — the corpus workflow flagged that lumping them lies, and a
    # crash must not let a targeted check masquerade as a mere deck-gap:
    #   CAN_FAIL          : flipped under some NON-crashing mutation (proven genuine)
    #   BY_CONSTRUCTION   : a CLEANLY-RUN mutation TARGETED it yet it never flipped (real finding)
    #   SUSPECT           : every mutation that TARGETED it CRASHED (never got a clean chance
    #                       to flip) -> could not test; must NOT be cleared as a deck-gap, and
    #                       must NOT be scored as an honest all_pass. A check must flip under a
    #                       non-crashing mutation before it is cleared.
    #   UNTESTED          : no mutation targeted it at all — genuine deck gap, NOT a verdict
    can_fail = [k for k, v in flips.items() if v]
    by_construction = [k for k, v in flips.items() if not v and targeted[k]]
    # suspect = never flipped, never cleanly targeted, but a crashing mutation DID target it
    suspect = [k for k, v in flips.items() if not v and not targeted[k] and crashed_target[k]]
    untested = [k for k, v in flips.items() if not v and not targeted[k] and not crashed_target[k]]
    report = {
        "tool": "canfail_probe", "sim": spec["sim"],
        "mutations_tried": [m["name"] for m in muts],
        "n_checks": len(base),
        "can_fail": can_fail,
        "by_construction": by_construction,           # cleanly-targeted-but-never-flipped = real finding
        "suspect": suspect,                            # targeting mutations all crashed = could not test
        "untested": untested,                          # deck did not reach the mechanism
        "can_fail_ratio": round(len(can_fail) / len(base), 3) if base else 0.0,
        "honest_all_pass_count": f"{len(can_fail)} proven can-fail, {len(by_construction)} by-construction, {len(suspect)} suspect (targeting mutation crashed), {len(untested)} untested, of {len(base)} claimed",
        "per_mutation": mlog,
    }
    print(json.dumps(report, indent=1))
    # exit priority (strictest first): a proven by-construction finding is exit 1; a SUSPECT
    # (crash hid the test) is a distinct exit 4 that is NOT a clean deck-gap and NOT cleared;
    # untested-only is the deck-gap exit 3; all clean is 0.
    if by_construction:
        sys.exit(1)
    if suspect:
        sys.exit(4)
    sys.exit(3 if untested else 0)

if __name__ == "__main__":
    main()
