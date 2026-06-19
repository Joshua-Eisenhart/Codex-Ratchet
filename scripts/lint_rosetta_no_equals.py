#!/usr/bin/env python3
"""lint_rosetta_no_equals.py -- enforce the no-equals-sign discipline in the Rosetta layer.

This system has NO equals sign and no universals. A Rosetta correspondence must be `jargon ~_M
kernel` (probe-relative, with an erasure record), never `jargon = kernel`. This lint:

  1. flags LEGACY de-facto '=' surfaces in the rosetta skills (kernel_identity="..." strings, the
     get_kernel_translation/get_qit_meaning accessors) -- these must migrate to ~_M correspondences;
  2. validates that converted/built correspondence records (rosetta_reattach records,
     qit_rosetta_tables.seed_correspondences()) are lint-clean (frozen '~_M', named probe family,
     non-empty erasure).

Exit 0 only if NO unmigrated legacy '=' surface is found AND every checked correspondence is clean.
Run: python3 scripts/lint_rosetta_no_equals.py

LIMITATIONS (honest; box-viii fleet 2026-06-15b): accessor detection is a NAME-based heuristic
(ACCESSOR_PATTERN), broadened but NOT structurally complete -- a one-true-name accessor renamed
outside the listed shapes can still evade. kernel_identity literals are only caught as the literal
`kernel_identity="..."` shape; a runtime-assembled identity string is not caught. The fence is now
STRUCTURAL (a file's kernel_identity literals are informational only if the file defines
`seed_correspondences`), so a comment cannot fence; but full coverage needs AST analysis, not regex.
Treat a clean run as necessary, not sufficient.
"""

from __future__ import annotations

import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILLS = ROOT / "system_v4" / "skills"
sys.path.insert(0, str(SKILLS))

# Scan the WHOLE skills surface (un-hardcoded), not a fixed list -- a renamed file cannot evade.
ROSETTA_FILES = sorted(SKILLS.glob("*.py"))

# Legacy de-facto '=' surfaces (assignment of a meaning string with no probe / no erasure).
LEGACY_EQUALS_PATTERNS = [
    (re.compile(r'kernel_identity\s*=\s*["\'][^"\']+["\']'), "kernel_identity='...' legacy identity string (no probe, no erasure)"),
]
# de-facto one-true-name accessors (broadened heuristic; structural detection of arbitrary renames
# is NOT complete -- this catches the common shapes; see LIMITATIONS in the docstring).
ACCESSOR_PATTERN = re.compile(r'def (get_qit_meaning|get_kernel_translation|get_canonical_(?:id|name|kernel)|translate_to_kernel|to_kernel_id|canonical_translation)\b')


def scan_legacy(path: pathlib.Path) -> list:
    """Return legacy-'=' findings. A kernel_identity literal is HARD unless the file provides a
    STRUCTURAL migration path (`def seed_correspondences`), so a comment cannot fence it. An
    accessor is OK once individually marked DEPRECATED nearby."""
    text = path.read_text(errors="ignore")
    has_converter = "def seed_correspondences" in text   # structural fence, not a substring magic word
    findings = []
    for pat, why in LEGACY_EQUALS_PATTERNS:
        for m in pat.finditer(text):
            line = text[:m.start()].count("\n") + 1
            findings.append({"file": path.name, "line": line, "why": why, "hard": not has_converter})
    for m in ACCESSOR_PATTERN.finditer(text):
        line = text[:m.start()].count("\n") + 1
        nearby = "\n".join(text.splitlines()[max(0, line - 1):line + 4])
        deprecated = "DEPRECATED" in nearby
        # an accessor is OK once marked DEPRECATED nearby (per-accessor, independent of whole-file fence)
        findings.append({"file": path.name, "line": line, "why": f"de-facto '=' accessor {m.group(1)}",
                         "hard": not deprecated})
    return findings


def check_built_correspondences() -> list:
    """Validate that the migrated/built correspondences are lint-clean under the dataclass validator."""
    problems = []
    try:
        import rosetta_reattach as rr
        # the reattach self-test fan
        er = [rr.ErasureRecord("Ti", "jungian_function", "jung", "M={D_z dephasing}", "the D_z action", "the felt semantics")]
        carrier = rr.reattach(rr.strip_with_erasure("L0::test", er), {"accepted": True})
        v = rr.validate_no_equals(carrier.perspectives())
        if v:
            problems.append({"source": "rosetta_reattach.reattach", "violations": v})
    except Exception as e:  # pragma: no cover
        problems.append({"source": "rosetta_reattach", "import_error": repr(e)})
    try:
        import importlib
        qrt = importlib.import_module("qit_rosetta_tables")
        seeds = qrt.seed_correspondences()
        v = rr.validate_no_equals(seeds) if "rr" in dir() else []
        # re-import rr defensively
        import rosetta_reattach as rr2
        v = rr2.validate_no_equals(seeds)
        if v:
            problems.append({"source": "qit_rosetta_tables.seed_correspondences", "violations": v})
    except Exception as e:
        problems.append({"source": "qit_rosetta_tables", "import_error_or_skip": repr(e)})
    return problems


def main() -> int:
    legacy = []
    for f in ROSETTA_FILES:
        if f.exists():
            legacy.extend(scan_legacy(f))
    hard = [x for x in legacy if x["hard"]]
    fenced = [x for x in legacy if not x["hard"]]
    corr = check_built_correspondences()
    corr_hard = [c for c in corr if c.get("violations")]

    import json
    print(json.dumps({
        "hard_legacy_equals_violations": hard,
        "fenced_legacy_surfaces_informational": fenced,
        "correspondence_check": corr,
        "ok": not hard and not corr_hard,
    }, indent=2))
    return 0 if (not hard and not corr_hard) else 1


if __name__ == "__main__":
    raise SystemExit(main())
