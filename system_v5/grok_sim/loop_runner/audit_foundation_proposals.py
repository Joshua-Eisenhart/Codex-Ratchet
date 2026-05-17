#!/usr/bin/env python3
"""Audit manifold-foundation scout proposals.

This is intentionally stricter than the proposal generator. Grok/Gemini are
allowed to explore broadly, but their outputs must be sorted into useful
scouts, corpses, and repair targets before any downstream work can use them.
"""

import argparse
import ast
import importlib.util
import json
import multiprocessing as mp
from pathlib import Path
from typing import Any


REQUIRED_EXPORTS = {
    "classification",
    "admission_scope",
    "promotion_allowed",
    "claim_ceiling",
    "branch_attempts",
    "run_branch",
    "main",
}

OPEN_TOKENS = ("OPEN", "NOT_YET_TESTED")
CLASSICAL_IMPORTS = {"numpy", "sympy"}
JARGON_TOKENS = {
    "axis",
    "ax0",
    "ax1",
    "ax2",
    "ax3",
    "ax4",
    "ax5",
    "ax6",
    "engine_stage",
    "gstack",
    "terrain",
    "type 1",
    "type 2",
    "prime_resonance",
    "hexagram",
    "igt",
    "jung",
}
TOY_TOKENS = {
    "hardcoded",
    "chosen to satisfy",
    "synthetic",
    "dummy",
    "placeholder",
    "toy",
    "fake",
}


def _jsonish(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _flatten(value: Any):
    if isinstance(value, dict):
        for item in value.values():
            yield from _flatten(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _flatten(item)
    else:
        yield value


def _has_null_survivor(value: Any) -> bool:
    if isinstance(value, dict):
        status = str(value.get("status", "")).upper()
        if status == "SURVIVED" and any(v is None for v in value.values()):
            return True
        return any(_has_null_survivor(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(_has_null_survivor(v) for v in value)
    return False


def _worker(path_s: str, queue: mp.Queue) -> None:
    path = Path(path_s)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        queue.put({"run_ok": False, "run_error": "cannot load import spec"})
        return
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        out = mod.main() if hasattr(mod, "main") else None
        queue.put({"run_ok": True, "main": _jsonish(out)})
    except Exception as exc:
        queue.put({"run_ok": False, "run_error": f"{type(exc).__name__}: {exc}"})


def _run_main(path: Path, timeout_s: int) -> dict:
    queue: mp.Queue = mp.Queue()
    proc = mp.Process(target=_worker, args=(str(path), queue))
    proc.start()
    proc.join(timeout_s)
    if proc.is_alive():
        proc.terminate()
        proc.join(3)
        if proc.is_alive():
            proc.kill()
        return {"run_ok": False, "run_error": f"timeout>{timeout_s}s"}
    if not queue.empty():
        return queue.get()
    return {"run_ok": False, "run_error": f"process_exit_{proc.exitcode}"}


def audit_file(path: Path, timeout_s: int) -> dict:
    finding = {
        "path": str(path),
        "verdict": "NEEDS_REVISION",
        "findings": [],
    }
    try:
        text = path.read_text()
    except Exception as exc:
        finding["findings"].append(f"read_error:{type(exc).__name__}:{exc}")
        return finding

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        finding["findings"].append(f"syntax_error:{exc.msg}:line_{exc.lineno}")
        return finding

    lowered = text.lower()
    jargon_hits = sorted(token for token in JARGON_TOKENS if token in lowered)
    if jargon_hits:
        finding["findings"].append(f"jargon_tokens_present:{','.join(jargon_hits)}")
    toy_hits = sorted(token for token in TOY_TOKENS if token in lowered)
    if toy_hits:
        finding["findings"].append(f"toy_or_fake_language_present:{','.join(toy_hits)}")

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    classical_used = sorted(imports & CLASSICAL_IMPORTS)
    if classical_used:
        finding["findings"].append(f"classical_bridge_imports_in_nonclassical_lane:{','.join(classical_used)}")

    module_defs = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    module_assigns = {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    exports = module_defs | module_assigns
    missing = sorted(REQUIRED_EXPORTS - exports)
    if missing:
        finding["findings"].append(f"missing_exports:{','.join(missing)}")

    if "promotion_allowed = True" in text or "promotion_allowed=True" in text:
        finding["findings"].append("promotion_allowed_true")

    run = _run_main(path, timeout_s)
    finding.update(run)
    if not run.get("run_ok"):
        finding["findings"].append(f"main_run_failed:{run.get('run_error')}")
    else:
        main_out = run.get("main")
        flat = [str(x).upper() for x in _flatten(main_out)]
        if not any(tok in item for tok in OPEN_TOKENS for item in flat):
            finding["findings"].append("does_not_preserve_open_boundary")
        if _has_null_survivor(main_out):
            finding["findings"].append("null_value_inside_survived_claim")

    if not finding["findings"]:
        finding["verdict"] = "SCOUT_USABLE"
    elif all(f.startswith("classical_bridge_imports") for f in finding["findings"]):
        finding["verdict"] = "SCOUT_USABLE_WITH_SUBSTRATE_WARNING"
    else:
        finding["verdict"] = "NEEDS_REVISION"
    return finding


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--timeout-s", type=int, default=30)
    parser.add_argument("--out")
    args = parser.parse_args()

    results = [audit_file(Path(p), args.timeout_s) for p in args.paths]
    summary = {
        "total": len(results),
        "by_verdict": {},
        "results": results,
    }
    for item in results:
        summary["by_verdict"][item["verdict"]] = summary["by_verdict"].get(item["verdict"], 0) + 1
    text = json.dumps(summary, indent=2, default=str)
    if args.out:
        Path(args.out).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
