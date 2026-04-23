#!/usr/bin/env python3
"""check_classification.py -- guard: every sim must declare a module-level classification.

For every system_v4/probes/sim_*.py (excluding sim_*_capability.py, which are canonical
by role), require a module-level assignment of `classification` to one of:
  - "classical_baseline"
  - "canonical"

Exit 1 with a JSON list of offenders (missing or invalid). Pre-commit hook safe.
No external dependencies.

Note: many sims also set `classification` inside a results dict inside __main__. A
module-level assignment is what this guard requires; an assignment inside any function
body does not count.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROBES_DIR = REPO / "system_v4" / "probes"
VALID = {"classical_baseline", "canonical"}


def _is_ignored_sim_path(path: Path) -> bool:
    name = path.name
    return name.endswith(" 2.py")


def _module_level_classification(path: Path) -> tuple[str, object]:
    """Return (status, value).

    status in {"ok", "missing", "invalid", "parse_error", "non_literal"}.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        return "parse_error", str(exc)

    found_value = None
    found = False
    for node in tree.body:  # module-level only
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "classification":
                    found = True
                    try:
                        found_value = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return "non_literal", None
        elif isinstance(node, ast.AnnAssign):
            t = node.target
            if isinstance(t, ast.Name) and t.id == "classification" and node.value is not None:
                found = True
                try:
                    found_value = ast.literal_eval(node.value)
                except (ValueError, SyntaxError):
                    return "non_literal", None

    if not found:
        return "missing", None
    if found_value not in VALID:
        return "invalid", found_value
    return "ok", found_value


def main() -> int:
    sims = sorted(
        p for p in PROBES_DIR.glob("sim_*.py")
        if not p.name.endswith("_capability.py")
        and not _is_ignored_sim_path(p)
        and "_archive_lane_c" not in p.parts
    )

    missing: list[str] = []
    invalid: list[dict] = []
    parse_errors: list[dict] = []
    non_literal: list[str] = []
    ok_count = 0

    for sim in sims:
        status, value = _module_level_classification(sim)
        rel = str(sim.relative_to(REPO))
        if status == "ok":
            ok_count += 1
        elif status == "missing":
            missing.append(rel)
        elif status == "invalid":
            invalid.append({"sim": rel, "value": value})
        elif status == "parse_error":
            parse_errors.append({"sim": rel, "detail": value})
        elif status == "non_literal":
            non_literal.append(rel)

    report = {
        "checked": len(sims),
        "ok": ok_count,
        "missing_count": len(missing),
        "invalid_count": len(invalid),
        "parse_error_count": len(parse_errors),
        "non_literal_count": len(non_literal),
        "missing": missing,
        "invalid": invalid,
        "parse_errors": parse_errors,
        "non_literal": non_literal,
    }
    print(json.dumps(report, indent=2))
    fail = bool(missing or invalid or parse_errors or non_literal)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
