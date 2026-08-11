#!/usr/bin/env python3
"""Deterministic gate: is every declared dependency installed, and is it used?

Answers two separate questions and never merges them:

  PRESENT  the package imports in this interpreter
  USED     some file under constraint_box/src or constraint_box/scripts imports it

Exits 0 only when every non-excluded declared package is PRESENT.
Exits 1 otherwise, naming exactly what is missing.

No LLM is involved. No network. Standard library only. Run it yourself:

    <interpreter> constraint_box/scripts/gate_dependency_stack.py

Add --json for a receipt, --self-test to run the negative control.
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REQ = ROOT / "requirements" / "candidates"

# Groups of declared packages. "excluded" groups may be absent by policy and
# never fail the gate; they are reported separately so a total cannot hide them.
GROUPS: list[tuple[str, str, bool]] = [
    ("core", "pyproject", False),
    ("extended", "cb-light-extended.in", False),
    ("candidates_passing", "cb-candidates-passing.in", False),
    ("candidates_failing", "cb-candidates-failing.in", True),
]

# Distribution name -> import name, where they differ.
IMPORT_NAME = {
    "annotated-types": "annotated_types",
    "argon2-cffi": "argon2",
    "ast-comments": "ast_comments",
    "beautifulsoup4": "bs4",
    "charset-normalizer": "charset_normalizer",
    "cvc5": "cvc5",
    "dirty-equals": "dirty_equals",
    "email-validator": "email_validator",
    "flake8-simplify": "flake8_simplify",
    "GitPython": "git",
    "import-linter": "importlinter",
    "markdown-it-py": "markdown_it",
    "patch-ng": "patch_ng",
    "pip-audit": "pip_audit",
    "protobuf": "google.protobuf",
    "PyJWT": "jwt",
    "pytest-benchmark": "pytest_benchmark",
    "pytest-randomly": "pytest_randomly",
    "pytest-timeout": "pytest_timeout",
    "pytest-xdist": "xdist",
    "python-json-logger": "pythonjsonlogger",
    "python-Levenshtein": "Levenshtein",
    "python-statemachine": "statemachine",
    "python-ulid": "ulid",
    "ruamel.yaml": "ruamel",
    "Unidecode": "unidecode",
    "vcrpy": "vcr",
    "whatthepatch": "whatthepatch",
    "z3-solver": "z3",
}


def declared(source: str) -> list[str]:
    """Package names declared by one source."""
    if source == "pyproject":
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        block = re.search(r"^dependencies\s*=\s*\[(.*?)\]", text, re.S | re.M)
        if not block:
            return []
        return [
            re.split(r"[><=!~\[]", spec, maxsplit=1)[0].strip()
            for spec in re.findall(r'"([^"]+)"', block.group(1))
        ]
    path = REQ / source
    if not path.exists():
        return []
    return [
        re.split(r"[=<>#\s]", line.strip())[0]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def import_name(pkg: str) -> str:
    return IMPORT_NAME.get(pkg, pkg.replace("-", ".").replace(".", "_"))


def is_present(pkg: str) -> bool:
    top = import_name(pkg).split(".")[0]
    try:
        return importlib.util.find_spec(top) is not None
    except (ImportError, ValueError):
        return False


def imported_modules() -> set[str]:
    """Top-level modules imported anywhere in CB's own source, by AST not grep.

    Grep matches strings, comments and docstrings. Parsing does not.
    """
    found: set[str] = set()
    for base in ("src", "scripts"):
        for py in (ROOT / base).rglob("*.py"):
            try:
                tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    found.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    found.add(node.module.split(".")[0])
    return found


def evaluate() -> dict:
    used = imported_modules()
    groups = []
    blocking_absent: list[str] = []
    for name, source, excluded in GROUPS:
        rows = []
        for pkg in declared(source):
            present = is_present(pkg)
            rows.append({
                "package": pkg,
                "import_name": import_name(pkg),
                "present": present,
                "used_by_cb_source": import_name(pkg).split(".")[0] in used,
            })
            if not present and not excluded:
                blocking_absent.append(pkg)
        groups.append({
            "group": name,
            "source": source,
            "excluded_from_gate": excluded,
            "declared": len(rows),
            "present": sum(r["present"] for r in rows),
            "used": sum(r["used_by_cb_source"] for r in rows),
            "absent": [r["package"] for r in rows if not r["present"]],
            "rows": rows,
        })
    return {
        "schema": "cb.dependency-stack-gate.v1",
        "interpreter": sys.executable,
        "verdict": "PASS" if not blocking_absent else "FAIL",
        "reason_code": None if not blocking_absent else "DECLARED_DEPENDENCY_ABSENT",
        "blocking_absent": sorted(blocking_absent),
        "groups": groups,
        "promotion_allowed": False,
    }


def self_test() -> int:
    """Negative control: the gate must FAIL on a package that cannot exist."""
    real = declared("cb-candidates-passing.in")
    ok_present = all(is_present(p) for p in real) if real else False
    fake_present = is_present("cb-definitely-not-a-real-package-xyzzy")
    print(f"  positive: every candidates_passing package present -> {ok_present}")
    print(f"  negative: a nonexistent package reports present     -> {fake_present}")
    if fake_present:
        print("  SELF-TEST FAIL: the presence check reports a fake package as present")
        return 1
    if not ok_present:
        print("  SELF-TEST INCONCLUSIVE: positive control is not installed")
        return 1
    print("  SELF-TEST PASS: presence check discriminates")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit the receipt as JSON")
    ap.add_argument("--self-test", action="store_true", help="run the negative control")
    args = ap.parse_args()

    if args.self_test:
        print("negative control for the presence check:")
        return self_test()

    receipt = evaluate()
    if args.json:
        print(json.dumps(receipt, indent=1))
        return 0 if receipt["verdict"] == "PASS" else 1

    print(f"interpreter: {receipt['interpreter']}\n")
    print(f"{'group':<22}{'declared':>9}{'present':>9}{'used':>7}   note")
    print("-" * 72)
    for g in receipt["groups"]:
        note = "excluded from gate" if g["excluded_from_gate"] else ""
        print(f"{g['group']:<22}{g['declared']:>9}{g['present']:>9}{g['used']:>7}   {note}")
        if g["absent"] and not g["excluded_from_gate"]:
            print(f"  ABSENT: {', '.join(g['absent'])}")
    print()
    print(f"VERDICT: {receipt['verdict']}"
          + (f"   {receipt['reason_code']}: {len(receipt['blocking_absent'])} package(s)"
             if receipt["reason_code"] else ""))
    print("\n'present' means it imports here. 'used' means CB source imports it.")
    print("They are different claims and this gate never merges them.")
    return 0 if receipt["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
