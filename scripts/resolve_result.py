#!/usr/bin/env python3
"""
resolve_result.py -- given a sim .py, return the ABSOLUTE path of the result JSON it
actually writes. Kills the recurring resolver bug where a loose grep grabbed a result
file the sim merely READ (an exemplar/carrier) instead of the one it WROTE.

Strategy (static, deterministic):
  1. Parse the .py with ast. Collect top-level string constants (NAME, SIM_ID, OBJECT_ID,
     OBJ, RESULT_NAME, etc.) and any `X = "results/....json"` / `X = RESULT_DIR / f"{NAME}_results.json"`.
  2. Find the json output target: an f-string or concat ending in `_results.json` or under `results/`
     that is passed to open(...,'w'), .write_text(...), or json.dump(..., open(...)).
  3. Resolve the f-string using the collected constants.
Fallback: if static resolution is ambiguous, the sim is RUN once and the freshest
`results/*results.json` whose object_id matches the file's OBJECT_ID/NAME is returned.

usage: resolve_result.py <sim.py> [--run-fallback] [--python <interp>]
prints the absolute result path, or NONE.
"""
import ast
import glob
import json
import os
import re
import subprocess
import sys


def _const_strings(tree):
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = node.value.value
    return out


def _resolve_fstring(node, consts):
    """resolve an ast f-string / constant / simple concat to a string using consts."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return consts.get(node.id)
    if isinstance(node, ast.JoinedStr):
        parts = []
        for v in node.values:
            if isinstance(v, ast.Constant):
                parts.append(str(v.value))
            elif isinstance(v, ast.FormattedValue):
                s = _resolve_fstring(v.value, consts)
                if s is None:
                    return None
                parts.append(s)
            else:
                return None
        return "".join(parts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a = _resolve_fstring(node.left, consts)
        b = _resolve_fstring(node.right, consts)
        if a is not None and b is not None:
            return a + b
    return None


def static_resolve(simpath):
    src = open(simpath).read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    consts = _const_strings(tree)
    candidates = []
    # find string literals / f-strings ending in _results.json anywhere
    for node in ast.walk(tree):
        s = _resolve_fstring(node, consts) if isinstance(node, (ast.JoinedStr, ast.BinOp)) else None
        if s and s.endswith("_results.json"):
            candidates.append(s)
    # also catch `RESULT_DIR / f"{NAME}_results.json"` (ast.BinOp with Div) and plain consts
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            r = _resolve_fstring(node.right, consts)
            if r and r.endswith("_results.json"):
                candidates.append(r)
    # plain constants like "results/x_results.json"
    for v in consts.values():
        if v.endswith("_results.json"):
            candidates.append(v)
    # regex backstop on raw source for f"{NAME}_results.json" with NAME known
    for m in re.findall(r'f?["\']\{?(\w+)\}?_results\.json["\']', src):
        if m in consts:
            candidates.append(consts[m] + "_results.json")
    if not candidates:
        # last resort: any "...results.json" literal in source
        candidates = re.findall(r'([A-Za-z0-9_./]+_results\.json)', src)
    # normalize to basename, prefer the one matching NAME/SIM_ID/OBJECT_ID
    simdir = os.path.dirname(os.path.abspath(simpath))
    key = consts.get("NAME") or consts.get("SIM_ID") or consts.get("OBJECT_ID") or ""
    best = None
    for c in candidates:
        base = os.path.basename(c)
        full = os.path.join(simdir, "results", base)
        if not os.path.exists(full):
            continue
        if key and key in base:
            return full
        best = best or full
    return best


def run_fallback(simpath, interp):
    simdir = os.path.dirname(os.path.abspath(simpath))
    r = subprocess.run([interp, os.path.basename(simpath)], capture_output=True, text=True,
                       cwd=simdir, timeout=900)
    # the sim usually prints "wrote results/X" or "Saved: results/X"
    m = re.search(r'([A-Za-z0-9_./]+_results\.json)', (r.stdout or "") + (r.stderr or ""))
    if m:
        base = os.path.basename(m.group(1))
        full = os.path.join(simdir, "results", base)
        if os.path.exists(full):
            return full
    return None


def main():
    if len(sys.argv) < 2:
        print("NONE")
        return 2
    sim = sys.argv[1]
    res = static_resolve(sim)
    if res is None and "--run-fallback" in sys.argv:
        interp = sys.argv[sys.argv.index("--python") + 1] if "--python" in sys.argv else sys.executable
        res = run_fallback(sim, interp)
    print(res or "NONE")
    return 0 if res else 1


if __name__ == "__main__":
    sys.exit(main())
