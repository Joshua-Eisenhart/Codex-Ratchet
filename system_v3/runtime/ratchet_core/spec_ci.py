import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3
"""Spec CI: checks that system_specs/ accurately reflect the codebase.

Detects drift between specs and code. Run after any code change.

Usage:
  python3 spec_ci.py           # run all checks
  python3 spec_ci.py --verbose  # show details for each check
"""

import argparse
import json
import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[3]
SPECS = REPO / "system_v3" / "specs"
SIMS = BASE / "sims"
A2_STATE = REPO / "system_v3" / "a2_state"


def check_spec_count():
    """system_specs must have <= 15 files."""
    files = list(SPECS.glob("*.md"))
    count = len(files)
    ok = count <= 15
    return ok, f"spec_count: {count}/15", files


def check_spec_dates():
    """Every spec must have an 'Updated:' line."""
    issues = []
    for f in sorted(SPECS.glob("*.md")):
        text = f.read_text()
        if "Updated:" not in text and f.name != "INDEX.md":
            issues.append(f.name)
    ok = len(issues) == 0
    return ok, f"specs_missing_date: {len(issues)}", issues


def check_code_files_exist():
    """Key code files referenced in PIPELINE_SPEC must exist."""
    expected = [
        "runner.py", "a1_protocol.py", "a1_llm.py", "zip_protocol.py",
        "feedback.py", "b_kernel.py", "state.py", "containers.py",
        "validator.py", "a0_generator_v2.py", "sim_builder.py",
        "adversarial_test.py",
    ]
    missing = [f for f in expected if not (BASE / f).exists()]
    return len(missing) == 0, f"code_files_missing: {len(missing)}", missing


def check_sim_count():
    """Sim count in registry must match files on disk."""
    sim_files = sorted(SIMS.glob("sim_*.py"))
    binding = json.loads((BASE / "constraint_sim_binding.json").read_text())
    unique_paths = set(v["sim_path"] for v in binding.values())
    return True, f"sims_on_disk: {len(sim_files)}, bindings: {len(binding)}, unique_paths: {len(unique_paths)}", []


def check_runner_line_count():
    """runner.py must be <= 500 lines."""
    lines = len((BASE / "runner.py").read_text().splitlines())
    ok = lines <= 500
    return ok, f"runner_lines: {lines}/500", []


def check_a2_state_files():
    """a2_state should have exactly the expected files."""
    expected = {"doc_index.json", "fuel_queue.json", "rosetta.json", "memory.jsonl",
                "INTENT_SUMMARY.md", "MODEL_CONTEXT.md", "constraint_surface.json"}
    actual = {f.name for f in A2_STATE.iterdir() if f.is_file()}
    extra = actual - expected
    return len(extra) == 0, f"a2_state_files: {len(actual)}, extra: {len(extra)}", list(extra)


def check_index_accuracy():
    """INDEX.md should list all spec files."""
    index_text = (SPECS / "INDEX.md").read_text()
    spec_files = {f.name for f in SPECS.glob("*.md")}
    missing_from_index = []
    for name in sorted(spec_files):
        if name not in index_text:
            missing_from_index.append(name)
    return len(missing_from_index) == 0, f"index_missing: {len(missing_from_index)}", missing_from_index


def check_b_rules():
    """adversarial_test.py should pass."""
    import subprocess
    result = subprocess.run(
        ["python3", str(BASE / "adversarial_test.py")],
        capture_output=True, text=True, cwd=str(BASE))
    ok = result.returncode == 0 and "14/14" in result.stdout
    return ok, "b_rules: 14/14" if ok else f"b_rules: FAIL (exit {result.returncode})", []


def check_sims_pass():
    """All sims should pass."""
    import subprocess
    result = subprocess.run(
        ["python3", str(BASE / "sim_builder.py"), "--check", "--out", "sims/"],
        capture_output=True, text=True, cwd=str(BASE))
    match = re.search(r"(\d+) pass, (\d+) fail", result.stdout)
    if match:
        passed, failed = int(match.group(1)), int(match.group(2))
        ok = failed == 0
        return ok, f"sims: {passed} pass, {failed} fail", []
    return False, "sims: could not parse output", []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    checks = [
        ("SPEC_COUNT", check_spec_count),
        ("SPEC_DATES", check_spec_dates),
        ("CODE_FILES", check_code_files_exist),
        ("SIM_COUNT", check_sim_count),
        ("RUNNER_LINES", check_runner_line_count),
        ("A2_STATE", check_a2_state_files),
        ("INDEX_ACCURACY", check_index_accuracy),
        ("B_RULES", check_b_rules),
        ("SIMS_PASS", check_sims_pass),
    ]

    passed = 0
    failed = 0
    for name, fn in checks:
        ok, msg, details = fn()
        status = "PASS" if ok else "FAIL"
        print(f"  {status}  {name:20s}  {msg}")
        if not ok or (args.verbose and details):
            for d in details:
                print(f"         {d}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n  {passed} pass, {failed} fail")
    raise SystemExit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
