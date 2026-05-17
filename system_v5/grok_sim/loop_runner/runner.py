#!/usr/bin/env python3
"""runner.py — fixed loop runner with goal-stability enforcement.

Architecture:
  - Imports a candidate module (Grok-generated implementation)
  - Runs phases in order against frozen contracts
  - Goal-stability rule: writes a `_frozen_manifest.json` per run hashing the
    runner, candidate, and every phase contract by SHA-256. Compares against
    prior runs' manifests to flag drift. A passing phase is only equivalent to
    a prior passing phase when all relevant hashes match.
  - Writes 10-field side-quest receipts per phase with full provenance

Roles (Codex's spec):
  - Codex owns: runner + receipt schema + repo layout + verification
  - Opus owns:  hidden test design + Auditor diagnosis + Teacher patch prompts
  - Grok owns:  candidate implementation only
  - Runner owns: acceptance (boolean pass/fail per phase)

Usage:
  python runner.py --candidate <path/to/candidate.py> [--phases 00,01]
  python runner.py --candidate candidates/candidate_seed_iter_83.py
"""
import argparse
import ast
import importlib.util
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

THIS_DIR = Path(__file__).parent
SIM_DIR = THIS_DIR.parent  # system_v5/grok_sim/
sys.path.insert(0, str(THIS_DIR))

from receipts import (
    write_receipt, write_frozen_manifest, build_frozen_manifest,
    check_manifest_drift, write_run_hash,
)

CONTRACTS_DIR = THIS_DIR / "contracts"
RECEIPTS_DIR = THIS_DIR / "receipts"
RUNNER_PATH = Path(__file__).resolve()


def discover_phases():
    """Return [(phase_id, module_path)] sorted by phase id."""
    phases = []
    for p in sorted(CONTRACTS_DIR.glob("phase_*.py")):
        if p.stem.startswith("phase_") and not p.stem.endswith("__init__"):
            phase_id = p.stem.replace("phase_", "")
            phases.append((phase_id, p))
    return phases


def load_module(path: Path, name: str):
    """Dynamic import of a python file by path."""
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _candidate_guard(candidate_path: Path) -> list[dict]:
    """Source-level guard for candidate attempts to inspect harness internals.

    This is not a sandbox. It is a fail-closed tripwire for the concrete leak
    class that bit this loop: generated candidates learning the runner/contract
    surface and shaping outputs to tests instead of the public API contract.
    """
    failures = []
    try:
        src = candidate_path.read_text()
        tree = ast.parse(src)
    except Exception as e:
        return [{"check": "candidate_source_guard_parse", "msg": str(e)[:200]}]

    blocked_strings = (
        "loop_runner/contracts",
        "/contracts/",
        "contracts/phase_",
        "phase_32_axis_cliff.py",
        "phase_98_prime_resonance",
        "runner.py",
        "_frozen_manifest",
        "_run_hash",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            hit = next((s for s in blocked_strings if s in node.value), None)
            if hit:
                failures.append({
                    "check": "candidate_harness_string_reference",
                    "msg": f"source string references harness internals `{hit}` at line {node.lineno}",
                })

        if isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                parts = []
                cur = func
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                name = ".".join(reversed(parts))
            if name in {
                "inspect.stack", "inspect.currentframe",
                "sys._getframe", "os.walk", "Path.glob", "pathlib.Path.glob",
                "eval", "exec", "__import__", "getattr",
            }:
                failures.append({
                    "check": "candidate_harness_introspection_call",
                    "msg": f"blocked dynamic/introspection call `{name}` at line {node.lineno}",
                })
            if name == "globals":
                failures.append({
                    "check": "candidate_wholesale_reexport_call",
                    "msg": f"blocked wholesale `globals()` re-export at line {node.lineno}",
                })
    return failures


def run_phase(phase_id: str, phase_module_path: Path, candidate_module) -> dict:
    """Execute a phase's run() function on the candidate. Return phase result dict."""
    t0 = time.time()
    try:
        phase_module = load_module(phase_module_path, f"phase_{phase_id}")
        result = phase_module.run(candidate_module)
        result.setdefault("phase_id", phase_id)
        result.setdefault("elapsed_s", round(time.time() - t0, 3))
        return result
    except Exception:
        return {
            "phase_id": phase_id,
            "pass": False,
            "failures": [{"check": "phase_execution_crash", "msg": traceback.format_exc()[-2000:]}],
            "elapsed_s": round(time.time() - t0, 3),
        }


def _find_latest_manifest_for(candidate_path: Path, phase_ids: set[str]) -> Path:
    """Find the most recent prior run's manifest for this candidate and phase set.

    Per-candidate filtering is essential: cross-candidate drift comparison drowns
    real phase-contract drift in candidate_sha256 noise. We compare runs whose
    candidate.path and selected phase set match; if none exist, returns None
    (first-run baseline). This lets a focused one-phase probe and a later full
    run coexist without treating the added phases as unauthorized drift."""
    if not RECEIPTS_DIR.exists():
        return None
    cand_path_str = str(candidate_path)
    runs = sorted([d for d in RECEIPTS_DIR.iterdir()
                   if d.is_dir() and (d / "_frozen_manifest.json").exists()],
                  key=lambda d: d.name, reverse=True)
    for run_dir in runs:
        summary_path = run_dir / "_summary.json"
        if summary_path.exists():
            try:
                summary = json.loads(summary_path.read_text())
                if summary.get("aborted_reason"):
                    continue
            except Exception:
                pass
        try:
            m = json.loads((run_dir / "_frozen_manifest.json").read_text())
        except Exception:
            continue
        if (
            m.get("candidate", {}).get("path") == cand_path_str
            and set(m.get("phases", {}).keys()) == set(phase_ids)
        ):
            return run_dir / "_frozen_manifest.json"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True, help="path to candidate .py module implementing the API")
    ap.add_argument("--phases", default=None, help="comma-separated phase ids to run (default: all)")
    ap.add_argument("--run-id", default=None, help="run id (default: timestamp)")
    ap.add_argument("--allow-drift", action="store_true",
                    help="allow runner/phase/receipts module drift vs prior manifest. "
                         "Default is STRICT: runner exits non-zero if phase contracts or "
                         "runner code changed since the most recent prior manifest. "
                         "Use --allow-drift when intentionally evolving contracts (and "
                         "expect to land a new frozen baseline).")
    ap.add_argument("--candidates-root", default=None,
                    help="restrict candidate path to this directory (default: any path). "
                         "Set this when running in adversarial mode to prevent reading "
                         "arbitrary files into the loop driver's Grok prompt.")
    args = ap.parse_args()

    candidate_path = Path(args.candidate).resolve()
    if not candidate_path.exists():
        print(f"ERROR: candidate not found at {candidate_path}", file=sys.stderr)
        sys.exit(2)

    # P1 fix: when --candidates-root is set, the candidate path must live under it.
    # Prevents the loop driver from later embedding arbitrary file contents into the
    # Grok prompt (e.g. a secret file being shipped as if it were a candidate).
    if args.candidates_root:
        root = Path(args.candidates_root).resolve()
        try:
            candidate_path.relative_to(root)
        except ValueError:
            print(f"ERROR: candidate {candidate_path} is not under --candidates-root {root}",
                  file=sys.stderr)
            sys.exit(2)

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print(f"=== runner: candidate={candidate_path.name}  run_id={run_id} ===\n")

    # Discover and filter phases (need this before building manifest)
    all_phases = discover_phases()
    selected_ids = set(args.phases.split(",")) if args.phases else {p[0] for p in all_phases}
    known_ids = {p[0] for p in all_phases}
    unknown_ids = sorted(selected_ids - known_ids)
    if unknown_ids:
        print(f"ERROR: unknown phase id(s): {', '.join(unknown_ids)}", file=sys.stderr)
        sys.exit(2)
    phases = [(pid, ppath) for pid, ppath in all_phases if pid in selected_ids]
    if not phases:
        print("ERROR: no phases selected", file=sys.stderr)
        sys.exit(2)

    # Build + write the frozen manifest BEFORE running anything
    run_dir = RECEIPTS_DIR / run_id
    manifest = build_frozen_manifest(
        runner_path=RUNNER_PATH,
        candidate_path=candidate_path,
        phase_paths=[pp for _, pp in phases],
        command_argv=sys.argv,
        run_id=run_id,
    )
    manifest_path = write_frozen_manifest(run_dir, manifest)

    # Check drift against the most recent prior manifest FOR THIS CANDIDATE
    prior_manifest = _find_latest_manifest_for(candidate_path, {pid for pid, _ in phases})
    drift_entries = []
    if prior_manifest and prior_manifest != manifest_path:
        drift_entries = check_manifest_drift(prior_manifest, manifest)
        if drift_entries:
            print(f"DRIFT vs {prior_manifest.parent.name}: {len(drift_entries)} field(s) changed")
            for d in drift_entries[:10]:
                print(f"  - {d['field']}: prior={str(d['prior'])[:50]} current={str(d['current'])[:50]}")
            if not args.allow_drift:
                # P0 fix: enforce drift gate. Default is STRICT — abort the run.
                # Receipts from prior passing phases stay valid; this run is
                # NOT one of them until drift is resolved or --allow-drift passed.
                summary_path = run_dir / "_summary.json"
                run_dir.mkdir(parents=True, exist_ok=True)
                summary_path.write_text(json.dumps({
                    "run_id": run_id,
                    "candidate": str(candidate_path),
                    "frozen_manifest": str(manifest_path),
                    "drift_vs_prior": drift_entries,
                    "phases": [],
                    "aborted_reason": "manifest_drift_without_allow_drift_flag",
                }, indent=2))
                print(f"\nABORTED — manifest drift vs prior run not authorized. "
                      f"Pass --allow-drift to override, or revert the changed files.")
                print(f"Summary: {summary_path}")
                sys.exit(3)
            print("  (continuing under --allow-drift; passing phases below are NOT "
                  "equivalent to prior passing phases)")
            print()

    # Load candidate
    t_load = time.time()
    guard_failures = _candidate_guard(candidate_path)
    if guard_failures:
        write_receipt(run_dir, "00_smoke", {
            "phase_id": "00_smoke",
            "pass": False,
            "failures": guard_failures,
            "elapsed_s": round(time.time() - t_load, 3),
        }, candidate_path, phase_path=None, manifest_path=manifest_path)
        print("CANDIDATE FAILED SOURCE GUARD — receipt written, exiting.")
        sys.exit(1)

    try:
        candidate = load_module(candidate_path, "candidate")
    except Exception:
        write_receipt(run_dir, "00_smoke", {
            "phase_id": "00_smoke",
            "pass": False,
            "failures": [{"check": "candidate_import", "msg": traceback.format_exc()[-2000:]}],
            "elapsed_s": round(time.time() - t_load, 3),
        }, candidate_path, phase_path=None, manifest_path=manifest_path)
        print("CANDIDATE FAILED TO IMPORT — receipt written, exiting.")
        sys.exit(1)
    print(f"Loaded candidate in {time.time() - t_load:.2f}s\n")

    # Run phases in order — goal-stability: stop at first hard failure for THIS run
    # (later iterations may revisit; manifest hashes guarantee provenance)
    overall = {
        "run_id": run_id,
        "candidate": str(candidate_path),
        "frozen_manifest": str(manifest_path),
        "drift_vs_prior": drift_entries,
        "phases": [],
    }
    for phase_id, phase_path in phases:
        print(f"--- Phase {phase_id} ---")
        result = run_phase(phase_id, phase_path, candidate)
        overall["phases"].append({"phase_id": phase_id, "pass": result["pass"], "elapsed_s": result.get("elapsed_s")})
        write_receipt(run_dir, phase_id, result, candidate_path,
                      phase_path=phase_path, manifest_path=manifest_path)
        if result["pass"]:
            print(f"  PASS  ({result.get('elapsed_s')}s)")
        else:
            print(f"  FAIL  ({result.get('elapsed_s')}s)")
            for f in result.get("failures", [])[:5]:
                print(f"    - {f.get('check')}: {f.get('msg', '')[:200]}")
            # Goal-stability: subsequent phases not run until this one passes
            print(f"  STOP at phase {phase_id}; later phases not attempted this run.\n")
            break
        print()

    # Run summary
    summary_path = run_dir / "_summary.json"
    summary_path.write_text(json.dumps(overall, indent=2))

    # P1 fix: write _run_hash.txt over manifest + all receipts so post-hoc
    # tampering with any single receipt is detectable.
    run_hash_path = write_run_hash(run_dir)

    print(f"\nSummary: {summary_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Run hash: {run_hash_path}")
    all_pass = all(p["pass"] for p in overall["phases"]) and len(overall["phases"]) == len(phases)
    print(f"Overall: {'ALL PASS' if all_pass else 'STOPPED'}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
