#!/usr/bin/env python3
"""Ablation harness: formalize compound-sim irreducibility.

For each load_bearing tool declared in a sim's TOOL_INTEGRATION_DEPTH,
inject a broken stub into sys.modules BEFORE the sim runs, then check
whether overall_pass flips from True to False. A tool is "irreducible"
iff ablating it breaks the claim. A claimed load-bearing tool that the
sim still passes without is flagged "decorative".

Usage:  python scripts/ablation_harness.py <sim_path> [<sim_path> ...]
        --out overnight_logs/ablation_report.json
"""
from __future__ import annotations
import argparse, ast, json, os, subprocess, sys, tempfile, textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Manifest-key -> actual import module name(s) to poison.
TOOL_IMPORT_MAP = {
    "z3": ["z3"],
    "cvc5": ["cvc5"],
    "sympy": ["sympy"],
    "clifford": ["clifford"],
    "pytorch": ["torch"],
    "autograd": ["torch.autograd", "torch"],
    "pyg": ["torch_geometric", "torch_geometric.data",
            "torch_geometric.utils", "torch_geometric.nn"],
    "toponetx": ["toponetx", "toponetx.classes"],
    "gudhi": ["gudhi"],
    "xgi": ["xgi"],
    "e3nn": ["e3nn", "e3nn.o3"],
    "rustworkx": ["rustworkx"],
    "geomstats": ["geomstats"],
}


def extract_load_bearing(sim_path: Path) -> list[str]:
    """Parse TOOL_INTEGRATION_DEPTH without importing the sim."""
    tree = ast.parse(sim_path.read_text())
    depth = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "TOOL_INTEGRATION_DEPTH":
                    try:
                        depth = ast.literal_eval(node.value)
                    except Exception:
                        depth = {}
    # Walk entire tree for TOOL_INTEGRATION_DEPTH["x"] = "load_bearing"
    # and for-loop variants anywhere in the module.
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Constant)
            and node.value.value == "load_bearing"):
            for tgt in node.targets:
                if (isinstance(tgt, ast.Subscript)
                    and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == "TOOL_INTEGRATION_DEPTH"
                    and isinstance(tgt.slice, ast.Constant)
                    and isinstance(tgt.slice.value, str)):
                    depth[tgt.slice.value] = "load_bearing"
        if isinstance(node, ast.For) and isinstance(node.iter, (ast.Tuple, ast.List)):
            keys = [e.value for e in node.iter.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            for stmt in node.body:
                if (isinstance(stmt, ast.Assign)
                    and isinstance(stmt.value, ast.Constant)
                    and stmt.value.value == "load_bearing"):
                    for k in keys:
                        depth[k] = "load_bearing"
    return [k for k, v in depth.items() if v == "load_bearing"]


RUNNER = textwrap.dedent("""
    import sys, types, runpy, json
    POISON = {poison!r}
    class _Broken(types.ModuleType):
        def __getattr__(self, name):
            raise ImportError(f"ablated: {{self.__name__}}.{{name}}")
    for mod in POISON:
        sys.modules[mod] = _Broken(mod)
    # Block re-imports too.
    _orig_import = __builtins__.__import__ if isinstance(__builtins__, dict) else __import__
    import builtins
    def _guard(name, *a, **kw):
        root = name.split('.')[0]
        for p in POISON:
            if name == p or name.startswith(p + '.') or root == p.split('.')[0] and p == root:
                raise ImportError(f"ablated import: {{name}}")
        return _orig_import(name, *a, **kw)
    builtins.__import__ = _guard
    try:
        g = runpy.run_path({sim!r}, run_name="__main__")
        print("ABLATION_OK")
    except Exception as e:
        print(f"ABLATION_RAISED: {{type(e).__name__}}: {{e}}")
""")


PASS_KEYS = ("overall_pass", "compound_claim_holds", "all_pass", "pass")


def _detect_pass(sim_path: Path, stdout: str) -> bool:
    if "PASS=True" in stdout:
        return True
    # Fall back to JSON result file written next to the sim.
    result_dir = sim_path.parent / "a2_state" / "sim_results"
    candidate = result_dir / f"{sim_path.stem}_results.json"
    if candidate.exists():
        try:
            data = json.loads(candidate.read_text())
            for key in PASS_KEYS:
                if key in data:
                    return bool(data[key])
        except Exception:
            pass
    return False


def run_sim_raw(sim_path: Path) -> tuple[bool, str]:
    r = subprocess.run([sys.executable, str(sim_path)],
                       capture_output=True, text=True, cwd=str(REPO), timeout=300)
    out = r.stdout + r.stderr
    return _detect_pass(sim_path, r.stdout), out[-400:]


def run_sim_ablated(sim_path: Path, tool_key: str) -> tuple[bool, str]:
    mods = TOOL_IMPORT_MAP.get(tool_key, [tool_key])
    code = RUNNER.format(poison=mods, sim=str(sim_path))
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code); runner = f.name
    try:
        r = subprocess.run([sys.executable, runner],
                           capture_output=True, text=True,
                           cwd=str(REPO), timeout=300)
    finally:
        os.unlink(runner)
    out = r.stdout + r.stderr
    # Ablated-pass means: sim ran to completion AND reported pass.
    if "ABLATION_RAISED" in r.stdout or "ABLATION_OK" not in r.stdout:
        return False, out[-400:]
    return _detect_pass(sim_path, r.stdout), out[-400:]


def ablate_sim(sim_path: Path) -> list[dict]:
    lb = extract_load_bearing(sim_path)
    if not lb:
        return [{"sim": sim_path.name, "tool": None, "note": "no load_bearing tools declared"}]
    base_pass, base_tail = run_sim_raw(sim_path)
    reports = []
    for tool in lb:
        abl_pass, abl_tail = run_sim_ablated(sim_path, tool)
        irreducible = bool(base_pass and not abl_pass)
        reports.append({
            "sim": sim_path.name,
            "tool": tool,
            "original_pass": base_pass,
            "ablated_pass": abl_pass,
            "irreducible": irreducible,
            "decorative": base_pass and abl_pass,
            "ablated_tail": abl_tail.strip().splitlines()[-3:],
        })
    return reports


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sims", nargs="+")
    ap.add_argument("--out", default="overnight_logs/ablation_irreducibility_report.json")
    args = ap.parse_args()
    all_reports = []
    for s in args.sims:
        p = Path(s)
        if not p.is_absolute():
            p = REPO / s
        print(f"[ablate] {p.name}", flush=True)
        rs = ablate_sim(p)
        for r in rs:
            print(f"  tool={r.get('tool')} orig={r.get('original_pass')} "
                  f"abl={r.get('ablated_pass')} irreducible={r.get('irreducible')}",
                  flush=True)
        all_reports.extend(rs)
    out_path = REPO / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(all_reports, indent=2))
    print(f"[wrote] {out_path}")


if __name__ == "__main__":
    main()
