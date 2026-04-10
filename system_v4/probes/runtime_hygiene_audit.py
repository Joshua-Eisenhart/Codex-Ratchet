#!/usr/bin/env python3
"""
Runtime hygiene audit.

Checks that the repo runs through the intended external interpreter, keeps
cache dirs outside the repo, and satisfies declared package floors.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, UTC
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version as pkg_version
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULTS_DIR / "runtime_hygiene_audit_results.json"
MAKEFILE_PATH = PROJECT_DIR / "Makefile"
BOT_PATH = PROJECT_DIR / "telegram_bot.py"
REQ_RUNTIME_PATH = PROJECT_DIR / "requirements-runtime.txt"
REQ_SIM_STACK_PATH = PROJECT_DIR / "requirements-sim-stack.txt"
ACTIVE_RUNTIME_SCAN_ROOTS = (
    PROJECT_DIR / "system_v4" / "probes",
    PROJECT_DIR / "system_v4" / "skills",
)
ACTIVE_RUNTIME_SCAN_FILES = (
    PROJECT_DIR / "Makefile",
    PROJECT_DIR / "imessage_bot.py",
    PROJECT_DIR / "telegram_bot.py",
)
ACTIVE_RUNTIME_SKIP_PARTS = {"a2_state", "sim_results", "__pycache__"}
ACTIVE_RUNTIME_SCAN_SUFFIXES = {".py", ".sh"}
RUNTIME_REFERENCE_EXCLUDES = {
    PROJECT_DIR / "system_v4" / "probes" / "controller_alignment_audit.py",
    PROJECT_DIR / "system_v4" / "probes" / "runtime_hygiene_audit.py",
}
LEGACY_RUNTIME_PATTERNS = (
    "/opt/homebrew/bin/python3",
    ".venv_spec_graph/bin/python",
    ".venv_spec_graph/bin/python3",
)

PACKAGE_MAP = {
    "torch": ("torch", "torch"),
    "torch-geometric": ("torch_geometric", "torch-geometric"),
    "z3-solver": ("z3", "z3-solver"),
    "cvc5": ("cvc5", "cvc5"),
    "sympy": ("sympy", "sympy"),
    "clifford": ("clifford", "clifford"),
    "geomstats": ("geomstats", "geomstats"),
    "e3nn": ("e3nn", "e3nn"),
    "rustworkx": ("rustworkx", "rustworkx"),
    "xgi": ("xgi", "xgi"),
    "TopoNetX": ("toponetx", "TopoNetX"),
    "gudhi": ("gudhi", "gudhi"),
    "matplotlib": ("matplotlib", "matplotlib"),
    "pandas": ("pandas", "pandas"),
    "networkx": ("networkx", "networkx"),
    "pydantic": ("pydantic", "pydantic"),
    "requests": ("requests", "requests"),
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def parse_make_var(text: str, name: str) -> str | None:
    match = re.search(rf"^{re.escape(name)}\s*:=\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def parse_python_bin_from_bot(text: str) -> str | None:
    match = re.search(r'^PYTHON_BIN\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    return match.group(1) if match else None


def parse_requirement_floors(path: Path, seen: set[Path] | None = None) -> dict[str, str]:
    seen = seen or set()
    if path in seen or not path.exists():
        return {}
    seen.add(path)

    floors: dict[str, str] = {}
    for raw_line in read_text(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-r "):
            nested = (path.parent / line[3:].strip()).resolve()
            floors.update(parse_requirement_floors(nested, seen))
            continue
        if ">=" in line:
            name, floor = line.split(">=", 1)
            floors[name.strip()] = floor.strip()
        else:
            floors[line] = ""
    return floors


def major_minor_patch_tuple(ver: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", ver)
    return tuple(int(n) for n in nums[:3])


def compare_floor(installed: str, floor: str) -> bool | None:
    if not installed or not floor:
        return None
    return major_minor_patch_tuple(installed) >= major_minor_patch_tuple(floor)


def package_status(floors: dict[str, str]) -> dict[str, dict]:
    statuses: dict[str, dict] = {}
    for req_name, floor in sorted(floors.items()):
        import_name, dist_name = PACKAGE_MAP.get(req_name, (req_name.replace("-", "_"), req_name))
        try:
            installed = pkg_version(dist_name)
        except PackageNotFoundError:
            installed = ""
        try:
            import_module(import_name)
            import_ok = True
            import_error = ""
        except Exception as exc:  # noqa: BLE001
            import_ok = False
            import_error = f"{exc.__class__.__name__}: {exc}"
        statuses[req_name] = {
            "import_name": import_name,
            "distribution_name": dist_name,
            "floor": floor,
            "installed": installed,
            "meets_floor": compare_floor(installed, floor),
            "import_ok": import_ok,
            "import_error": import_error,
        }
    return statuses


def compare_requirement_sets(runtime_floors: dict[str, str], sim_stack_floors: dict[str, str]) -> list[dict]:
    conflicts: list[dict] = []
    for req_name in sorted(set(runtime_floors) & set(sim_stack_floors)):
        runtime_floor = runtime_floors[req_name]
        sim_stack_floor = sim_stack_floors[req_name]
        if runtime_floor != sim_stack_floor:
            conflicts.append({
                "package": req_name,
                "runtime_floor": runtime_floor,
                "sim_stack_floor": sim_stack_floor,
            })
    return conflicts


def cache_dir_status(raw_path: str | None) -> dict:
    if not raw_path:
        return {
            "path": "",
            "exists": False,
            "writable": False,
            "parent_exists": False,
            "parent_writable": False,
        }

    cache_path = Path(raw_path).expanduser()
    target = cache_path if cache_path.exists() else cache_path.parent
    return {
        "path": str(cache_path),
        "exists": cache_path.exists(),
        "writable": os.access(cache_path, os.W_OK) if cache_path.exists() else False,
        "parent_exists": cache_path.parent.exists(),
        "parent_writable": os.access(target, os.W_OK) if target.exists() else False,
    }


def scan_active_runtime_references(make_python: str | None) -> list[dict]:
    findings: list[dict] = []
    expected = make_python or ""

    def scan_path(path: Path) -> None:
        if path in RUNTIME_REFERENCE_EXCLUDES or not path.exists():
            return
        rel_path = path.relative_to(PROJECT_DIR)
        for index, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            for pattern in LEGACY_RUNTIME_PATTERNS:
                if pattern not in line:
                    continue
                if expected and pattern == expected:
                    continue
                findings.append({
                    "kind": "stale_runtime_reference",
                    "file": str(rel_path),
                    "line": index,
                    "pattern": pattern,
                    "line_excerpt": line.strip()[:240],
                })

    for root in ACTIVE_RUNTIME_SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if set(path.parts) & ACTIVE_RUNTIME_SKIP_PARTS:
                continue
            if path.suffix not in ACTIVE_RUNTIME_SCAN_SUFFIXES:
                continue
            scan_path(path)

    for path in ACTIVE_RUNTIME_SCAN_FILES:
        scan_path(path)

    return findings


def main() -> int:
    strict = "--strict" in sys.argv[1:]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    makefile_text = read_text(MAKEFILE_PATH)
    bot_text = read_text(BOT_PATH) if BOT_PATH.exists() else ""
    make_python = parse_make_var(makefile_text, "PYTHON")
    mpl_cache = parse_make_var(makefile_text, "MPLCONFIGDIR")
    numba_cache = parse_make_var(makefile_text, "NUMBA_CACHE_DIR")
    bot_python = parse_python_bin_from_bot(bot_text) if bot_text else None

    runtime_floors = parse_requirement_floors(REQ_RUNTIME_PATH)
    sim_stack_floors = parse_requirement_floors(REQ_SIM_STACK_PATH)
    all_floors = dict(runtime_floors)
    all_floors.update(sim_stack_floors)
    packages = package_status(all_floors)
    requirement_conflicts = compare_requirement_sets(runtime_floors, sim_stack_floors)

    blockers: list[dict] = []
    advisories: list[dict] = []
    repair_candidates: list[dict] = []

    if not make_python:
        blockers.append({"kind": "makefile_python_missing"})
    else:
        make_python_path = Path(make_python).expanduser()
        if not make_python_path.exists():
            blockers.append({
                "kind": "configured_python_missing",
                "path": str(make_python_path),
            })
        if is_within(make_python_path, PROJECT_DIR):
            blockers.append({
                "kind": "configured_python_inside_repo",
                "path": str(make_python_path),
            })
        if Path(sys.executable).resolve() != make_python_path.resolve():
            advisories.append({
                "kind": "current_interpreter_differs_from_makefile",
                "current": sys.executable,
                "expected": str(make_python_path),
            })

    if bot_python and make_python and Path(bot_python).expanduser() != Path(make_python).expanduser():
        blockers.append({
            "kind": "bot_makefile_python_mismatch",
            "bot_python": bot_python,
            "makefile_python": make_python,
        })

    for label, raw_path in (("MPLCONFIGDIR", mpl_cache), ("NUMBA_CACHE_DIR", numba_cache)):
        if not raw_path:
            blockers.append({"kind": "makefile_cache_var_missing", "var": label})
            continue
        cache_path = Path(raw_path).expanduser()
        if is_within(cache_path, PROJECT_DIR):
            blockers.append({
                "kind": "cache_dir_inside_repo",
                "var": label,
                "path": str(cache_path),
            })
        status = cache_dir_status(raw_path)
        if status["exists"] and not status["writable"]:
            blockers.append({
                "kind": "cache_dir_not_writable",
                "var": label,
                "path": status["path"],
            })
        elif not status["exists"] and not status["parent_writable"]:
            blockers.append({
                "kind": "cache_dir_parent_not_writable",
                "var": label,
                "path": status["path"],
            })
        elif not status["exists"] and status["parent_writable"]:
            advisories.append({
                "kind": "cache_dir_missing_but_creatable",
                "var": label,
                "path": status["path"],
            })

    for req_name, info in packages.items():
        if info["installed"] == "":
            blockers.append({
                "kind": "required_package_missing",
                "package": req_name,
                "floor": info["floor"],
            })
            continue
        if info["meets_floor"] is False:
            blockers.append({
                "kind": "package_below_floor",
                "package": req_name,
                "installed": info["installed"],
                "floor": info["floor"],
            })
            continue
        if not info["import_ok"]:
            blockers.append({
                "kind": "required_package_import_broken",
                "package": req_name,
                "installed": info["installed"],
                "import_error": info["import_error"],
            })

    if requirement_conflicts:
        advisories.append({
            "kind": "requirement_floor_conflicts",
            "count": len(requirement_conflicts),
            "packages": requirement_conflicts[:20],
        })

    stale_runtime_refs = scan_active_runtime_references(make_python)
    if stale_runtime_refs:
        advisories.append({
            "kind": "stale_runtime_references",
            "count": len(stale_runtime_refs),
            "findings": stale_runtime_refs[:40],
        })

    if blockers:
        repair_candidates.append({
            "kind": "runtime_alignment_required",
            "action_class": "manual_env_repair",
            "safe_auto": False,
            "recommendation": "Repair interpreter or dependency floors before relying on unattended hygiene automation.",
        })

    summary = {
        "blocker_count": len(blockers),
        "advisory_count": len(advisories),
        "repair_candidate_count": len(repair_candidates),
        "requirements_package_count": len(packages),
        "ok": len(blockers) == 0,
    }

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "strict": strict,
        "current_interpreter": sys.executable,
        "makefile_python": make_python,
        "bot_python": bot_python,
        "makefile_cache_dirs": {
            "MPLCONFIGDIR": mpl_cache,
            "NUMBA_CACHE_DIR": numba_cache,
        },
        "cache_dir_status": {
            "MPLCONFIGDIR": cache_dir_status(mpl_cache),
            "NUMBA_CACHE_DIR": cache_dir_status(numba_cache),
        },
        "requirements_runtime_path": str(REQ_RUNTIME_PATH.relative_to(PROJECT_DIR)),
        "requirements_sim_stack_path": str(REQ_SIM_STACK_PATH.relative_to(PROJECT_DIR)),
        "requirement_floor_conflicts": requirement_conflicts,
        "stale_runtime_references": stale_runtime_refs,
        "package_status": packages,
        "summary": summary,
        "blockers": blockers,
        "advisories": advisories,
        "repair_candidates": repair_candidates,
    }

    OUT_PATH.write_text(json.dumps(report, indent=2))
    print(f"Wrote {OUT_PATH}")
    print(f"blocker_count={summary['blocker_count']}")
    print(f"advisory_count={summary['advisory_count']}")

    if strict and blockers:
        print("RUNTIME HYGIENE AUDIT FAILED")
        return 1

    print("RUNTIME HYGIENE AUDIT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
