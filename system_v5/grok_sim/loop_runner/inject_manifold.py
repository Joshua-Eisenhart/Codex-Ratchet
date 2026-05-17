#!/usr/bin/env python3
"""inject_manifold.py — inject build_constraint_manifold() into best honest candidate.

Takes the manifold-foundation proposal (Gemini) and injects its module-level code
into the existing best-honest-passing candidate. The injected primitive becomes
available alongside the existing functions.

Then runs the runner against the full phase suite and reports.
"""
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
CANDS = HERE.parent / "candidates"
PYTHON = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"

BASE = CANDS / "candidate_loop_iter03_codex_20260513T233724Z.py"
MANIFOLD = CANDS / "manifold_proposal_gemini_20260514T000643Z.py"


def extract_manifold_body(src: str) -> str:
    """Pull everything from imports through the `build_constraint_manifold` definition."""
    return src   # the proposal IS the manifold module; inject it verbatim


def main():
    if not BASE.exists() or not MANIFOLD.exists():
        print(f"Missing source files."); sys.exit(1)
    base_src = BASE.read_text()
    manifold_src = MANIFOLD.read_text()
    # Strip already-imported modules from manifold to avoid double-imports
    # Keep only the function definitions + module-level constants. Simple approach:
    # find the `def build_constraint_manifold` line and take everything from there.
    m = re.search(r"^def\s+build_constraint_manifold", manifold_src, re.MULTILINE)
    if m:
        body = manifold_src[m.start():]
    else:
        body = manifold_src

    # Also pull any helper functions defined BEFORE build_constraint_manifold
    # by finding all `def` blocks that come before. For simplicity, just inject
    # the entire manifold file as a comment-separated block before the existing
    # functions in the base candidate.
    injection = (
        "\n\n# =====================================================================\n"
        "# INJECTED MANIFOLD FOUNDATION (from Gemini-3.1-pro proposal, Codex-picked)\n"
        "# Source: manifold_proposal_gemini_20260514T000643Z.py\n"
        "# =====================================================================\n\n"
        + manifold_src + "\n\n"
        "# =====================================================================\n"
        "# END MANIFOLD INJECTION — base candidate continues below\n"
        "# =====================================================================\n\n"
    )

    # Inject right after the imports section of the base candidate.
    # Find the last top-level import line.
    lines = base_src.split("\n")
    last_import = 0
    for i, line in enumerate(lines):
        if re.match(r"^(import|from)\s", line):
            last_import = i
    out = "\n".join(lines[:last_import + 1]) + injection + "\n".join(lines[last_import + 1:])

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = CANDS / f"candidate_with_manifold_{ts}.py"
    out_path.write_text(out)
    print(f"Injected manifold → {out_path.name} ({len(out)} chars)")

    # Validate import
    r = subprocess.run([PYTHON, "-c", f"""
import importlib.util as u
spec = u.spec_from_file_location('c', '{out_path}')
m = u.module_from_spec(spec)
spec.loader.exec_module(m)
print('build_constraint_manifold in module:', hasattr(m, 'build_constraint_manifold'))
print('axis_transform in module:',           hasattr(m, 'axis_transform'))
print('engine_stage in module:',             hasattr(m, 'engine_stage'))
print('prime_resonance in module:',          hasattr(m, 'prime_resonance'))
"""], capture_output=True, text=True, timeout=120)
    print(r.stdout)
    if r.returncode != 0:
        print("Import failed:"); print(r.stderr[-800:]); sys.exit(2)

    # Now run the runner — show the phase trajectory
    print(f"\n=== Running full phase suite on injected candidate ===")
    r = subprocess.run([PYTHON, str(HERE / "runner.py"),
                        "--candidate", str(out_path),
                        "--allow-drift"],
                       capture_output=True, text=True, timeout=900)
    # Print just the phase lines
    for line in r.stdout.split("\n"):
        if line.startswith("--- Phase") or line.startswith("  PASS") or line.startswith("  FAIL") or line.startswith("Overall"):
            print(line)
    print(f"\nFinal candidate: {out_path}")


if __name__ == "__main__":
    main()
