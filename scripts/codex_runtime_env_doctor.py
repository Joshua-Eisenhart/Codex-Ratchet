#!/usr/bin/env python3
"""Read-only Codex Ratchet runtime environment doctor.

This script exists to stop LLM workers from installing packages into the wrong
place because they checked bare ``python3`` or the wrong Julia project. It does
not install, delete, upgrade, or import optional bridge packages that are known
to create local CondaPkg environments.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
PHYSICAL_PYTHON_ENV = Path(
    os.environ.get(
        "CODEX_RATCHET_PHYSICAL_PYTHON_ENV",
        "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main",
    )
)
SIM_STACK_ALIAS = Path(
    os.environ.get("CODEX_RATCHET_SIM_STACK", "/Users/joshuaeisenhart/.local/share/sim-stack")
)
DEFAULT_PYTHON = (
    SIM_STACK_ALIAS / "bin/python3"
    if SIM_STACK_ALIAS.exists()
    else PHYSICAL_PYTHON_ENV / "bin/python3"
)
CANONICAL_PYTHON = Path(
    os.environ.get(
        "CODEX_RATCHET_PYTHON",
        str(DEFAULT_PYTHON),
    )
)
JULIA = Path(os.environ.get("CODEX_RATCHET_JULIA", "/opt/homebrew/bin/julia"))
JULIA_PROJECT = Path(
    os.environ.get("CODEX_RATCHET_JULIA_PROJECT", str(REPO / "system_v5/julia_carrier"))
)
STRICT_JULIA_LOAD_PATH = "@:@stdlib"

PYTHON_EXPECT_OK = [
    "jax",
    "diffrax",
    "dynamiqs",
    "qutip",
    "quimb",
    "cotengra",
    "netket",
    "e3nn_jax",
    "ott",
    "blackjax",
    "optimistix",
    "jaxopt",
    "lineax",
    "torch",
    "torch_geometric",
    "torch_ga",
    "clifford",
    "geomstats",
    "e3nn",
    "torchdiffeq",
    "torchode",
    "xitorch",
    "cvxpylayers",
    "z3",
    "cvc5",
    "sympy",
    "pysindy",
]

# Import-probed for visibility but deliberately excluded from canonical-core
# success/failure. Its bounded Identity+EDMD surface has a function receipt,
# while the full distribution remains dependency-quarantined.
PYTHON_EXPECT_QUARANTINED = [
    "pykoopman",
]

PYTHON_EXPECT_BLOCKED = [
    "dgl",
    "torch_scatter",
    "torch_sparse",
    "bayeux",
]

JULIA_EXPECT_OK = [
    "JSON3",
    "JSON",
    "CliffordAlgebras",
    "Grassmann",
    "Z3",
    "Quaternions",
    "Octonions",
    "Graphs",
    "ITensors",
    "ITensorMPS",
    "QuantumClifford",
    "QuantumOptics",
    "QuantumToolbox",
    "Manifolds",
    "Yao",
    "DifferentialEquations",
    "Attractors",
    "DynamicalSystems",
    "ChaosTools",
    "StaticArrays",
    "Symbolics",
]

JULIA_EXPECT_OPTIONAL = [
    "Zygote",
]

FORBIDDEN_REPO_PROJECT_DEPS = {"PythonCall", "DLPack", "CondaPkg"}
POLLUTION_DIR_NAMES = {".CondaPkg", "site-packages", ".venv", "venv", "node_modules"}
POLLUTION_SKIP_DIRS = {
    ".git",
    "archive",
    "system_v3",
    "system_v4/probes/a2_state/sim_results_archive",
}


def run(cmd: list[str], timeout: int = 120, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=env,
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
        }
    except OSError as exc:
        return {
            "cmd": cmd,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
            "error_type": type(exc).__name__,
        }


def sim_stack_alias_state() -> dict[str, Any]:
    state: dict[str, Any] = {
        "path": str(SIM_STACK_ALIAS),
        "expected_target": str(PHYSICAL_PYTHON_ENV),
        "exists": SIM_STACK_ALIAS.exists() or SIM_STACK_ALIAS.is_symlink(),
        "is_symlink": SIM_STACK_ALIAS.is_symlink(),
        "physical_env_exists": PHYSICAL_PYTHON_ENV.exists(),
        "preferred_python": str(SIM_STACK_ALIAS / "bin/python3"),
        "physical_python": str(PHYSICAL_PYTHON_ENV / "bin/python3"),
    }
    if state["exists"]:
        try:
            state["target"] = str(SIM_STACK_ALIAS.resolve())
            state["ok"] = SIM_STACK_ALIAS.resolve() == PHYSICAL_PYTHON_ENV.resolve()
        except OSError as exc:
            state["target"] = None
            state["ok"] = False
            state["error"] = str(exc)
    else:
        state["target"] = None
        state["ok"] = False
    return state


def python_probe() -> dict[str, Any]:
    if not CANONICAL_PYTHON.exists():
        return {"exists": False, "path": str(CANONICAL_PYTHON), "modules": {}}
    code = r"""
import importlib, json, site, sys
mods_ok = __MODS_OK__
mods_blocked = __MODS_BLOCKED__
mods_quarantined = __MODS_QUARANTINED__
out = {
    "executable": sys.executable,
    "version": sys.version,
    "prefix": sys.prefix,
    "user_site": getattr(site, "getusersitepackages", lambda: None)(),
    "modules": {},
}
for name in mods_ok + mods_blocked + mods_quarantined:
    try:
        mod = importlib.import_module(name)
        out["modules"][name] = {
            "ok": True,
            "version": getattr(mod, "__version__", None),
            "file": getattr(mod, "__file__", None),
        }
    except Exception as exc:
        out["modules"][name] = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc).splitlines()[0][:240],
        }
print(json.dumps(out, sort_keys=True))
""".replace("__MODS_OK__", repr(PYTHON_EXPECT_OK)).replace(
        "__MODS_BLOCKED__", repr(PYTHON_EXPECT_BLOCKED)
    ).replace(
        "__MODS_QUARANTINED__", repr(PYTHON_EXPECT_QUARANTINED)
    )
    result = run([str(CANONICAL_PYTHON), "-c", code], timeout=180)
    parsed: dict[str, Any] = {"exists": True, "path": str(CANONICAL_PYTHON), "raw": result}
    if result["returncode"] == 0:
        parsed.update(json.loads(result["stdout"]))
    return parsed


def julia_probe(skip_julia: bool) -> dict[str, Any]:
    if skip_julia:
        return {"skipped": True}
    if not JULIA.exists():
        return {"exists": False, "path": str(JULIA), "modules": {}}
    project_arg = f"--project={JULIA_PROJECT}"
    modules_literal = "[" + ",".join(json.dumps(m) for m in JULIA_EXPECT_OK + JULIA_EXPECT_OPTIONAL) + "]"
    code = f"""
using Pkg
mods = {modules_literal}
println("JSON_BEGIN")
println("{{")
println("\\\"executable\\\": " * repr(joinpath(Sys.BINDIR, "julia")) * ",")
println("\\\"version\\\": " * repr(string(VERSION)) * ",")
println("\\\"active_project\\\": " * repr(string(Base.active_project())) * ",")
println("\\\"load_path\\\": " * repr(join(Base.LOAD_PATH, ":")) * ",")
println("\\\"depot_path\\\": " * repr(join(Base.DEPOT_PATH, ":")) * ",")
println("\\\"modules\\\": {{")
for (i, pkg) in enumerate(mods)
    ok = true
    err = ""
    try
        @eval using $(Symbol(pkg))
    catch e
        ok = false
        err = first(split(string(e), "\\n"))
    end
    comma = i == length(mods) ? "" : ","
    println(repr(pkg) * ": " * "{{\\\"ok\\\": " * string(ok) * ", \\\"error\\\": " * repr(err) * "}}" * comma)
end
println("}}")
println("}}")
println("JSON_END")
"""
    julia_env = os.environ.copy()
    julia_env["JULIA_LOAD_PATH"] = STRICT_JULIA_LOAD_PATH
    result = run(
        [
            str(JULIA),
            "--startup-file=no",
            project_arg,
            "-e",
            code,
        ],
        timeout=240,
        env=julia_env,
    )
    parsed: dict[str, Any] = {"exists": True, "path": str(JULIA), "raw": result}
    if result["returncode"] == 0:
        stdout = result["stdout"]
        if "JSON_BEGIN" in stdout and "JSON_END" in stdout:
            body = stdout.split("JSON_BEGIN", 1)[1].split("JSON_END", 1)[0].strip()
            parsed.update(json.loads(body))
    return parsed


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_dep_scan(repo: Path = REPO) -> dict[str, Any]:
    carrier = repo / "system_v5/julia_carrier"
    project = carrier / "Project.toml"
    manifest = carrier / "Manifest.toml"
    present: list[str] = []
    if project.exists():
        text = project.read_text()
        for dep in sorted(FORBIDDEN_REPO_PROJECT_DEPS):
            if f"{dep} =" in text:
                present.append(dep)
    rel_manifest = "system_v5/julia_carrier/Manifest.toml"
    tracked = run(["git", "-C", str(repo), "ls-files", "--error-unmatch", "--", rel_manifest])
    ignored = run(["git", "-C", str(repo), "check-ignore", "--quiet", "--", rel_manifest])
    manifest_metadata: dict[str, Any] = {}
    manifest_parse_error: str | None = None
    absolute_path_entries: list[str] = []
    if manifest.is_file():
        manifest_text = manifest.read_text(encoding="utf-8")
        try:
            parsed = tomllib.loads(manifest_text)
            manifest_metadata = {
                "julia_version": parsed.get("julia_version"),
                "manifest_format": parsed.get("manifest_format"),
                "project_hash": parsed.get("project_hash"),
            }
        except tomllib.TOMLDecodeError as exc:
            manifest_parse_error = str(exc)
        for line in manifest_text.splitlines():
            match = re.match(r"\s*path\s*=\s*[\"']([^\"']+)[\"']", line)
            if match and Path(match.group(1)).is_absolute():
                absolute_path_entries.append(match.group(1))
    manifest_present = manifest.is_file()
    manifest_ignored = ignored.get("returncode") == 0
    return {
        "project": str(project),
        "forbidden_deps_present": present,
        "forbidden_deps_expected_absent": sorted(FORBIDDEN_REPO_PROJECT_DEPS),
        "manifest": str(manifest),
        "manifest_present": manifest_present,
        "manifest_tracked": tracked.get("returncode") == 0,
        "manifest_ignored": manifest_ignored,
        "manifest_present_local_ignored": manifest_present and manifest_ignored,
        "manifest_sha256": sha256_file(manifest),
        "manifest_metadata": manifest_metadata,
        "manifest_parse_error": manifest_parse_error,
        "manifest_absolute_path_entries": absolute_path_entries,
    }


def pollution_scan() -> list[str]:
    found: list[str] = []
    skip_abs = {str((REPO / p).resolve()) for p in POLLUTION_SKIP_DIRS}
    for root, dirs, _files in os.walk(REPO):
        root_path = Path(root).resolve()
        if str(root_path) in skip_abs:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in {".git", "archive", "system_v3"}]
        for dirname in list(dirs):
            if dirname in POLLUTION_DIR_NAMES:
                found.append(str(root_path / dirname))
                dirs.remove(dirname)
    return sorted(found)


def active_installers() -> dict[str, Any]:
    result = run(["ps", "-axo", "pid,command"], timeout=20)
    if result.get("timed_out") or result.get("error_type") or result.get("returncode") != 0:
        return {
            "ok": False,
            "matches": [],
            "error_type": result.get("error_type"),
            "stderr": result.get("stderr", ""),
            "timed_out": result.get("timed_out", False),
        }
    needles = [
        "Pkg.add",
        "Pkg.instantiate",
        "Pkg.update",
        "pip install",
        "uv pip",
        "conda install",
        "conda env",
        "pixi install",
        "poetry add",
    ]
    out: list[str] = []
    for line in result.get("stdout", "").splitlines():
        if "codex_runtime_env_doctor.py" in line:
            continue
        if "=== CLEANUP:" in line or "remove repo env-pollution" in line:
            continue
        if any(n in line for n in needles):
            out.append(line.strip())
    return {"ok": True, "matches": out}


def summarize(report: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []

    alias = report["sim_stack_alias"]
    if alias["exists"] and not alias["ok"]:
        failures.append(
            "preferred sim-stack alias points at the wrong target: "
            f"{alias.get('path')} -> {alias.get('target')}"
        )
    if not alias["exists"]:
        warnings.append("preferred sim-stack alias missing; falling back to physical env path")

    py = report["python"]
    if not py.get("exists"):
        failures.append(f"canonical python missing: {CANONICAL_PYTHON}")
    else:
        modules = py.get("modules", {})
        for name in PYTHON_EXPECT_OK:
            if not modules.get(name, {}).get("ok"):
                failures.append(f"python module failed in canonical env: {name}")
        for name in PYTHON_EXPECT_BLOCKED:
            if modules.get(name, {}).get("ok"):
                warnings.append(f"blocked/avoid python module unexpectedly imports: {name}")

    julia = report["julia"]
    if not julia.get("skipped"):
        if not julia.get("exists"):
            failures.append(f"julia missing: {JULIA}")
        else:
            if julia.get("load_path") != STRICT_JULIA_LOAD_PATH:
                failures.append(
                    f"julia carrier probe did not use strict load path: {julia.get('load_path')}"
                )
            modules = julia.get("modules", {})
            for name in JULIA_EXPECT_OK:
                if not modules.get(name, {}).get("ok"):
                    failures.append(f"julia module failed in carrier project: {name}")

    repo_project = report["repo_project"]
    if repo_project["forbidden_deps_present"]:
        failures.append(
            "repo Julia Project.toml contains forbidden bridge deps: "
            + ",".join(repo_project["forbidden_deps_present"])
        )
    if not repo_project.get("manifest_present"):
        failures.append("strict Julia carrier Manifest.toml is missing")
    if repo_project.get("manifest_ignored"):
        failures.append("strict Julia carrier Manifest.toml is ignored")
    if not repo_project.get("manifest_tracked"):
        failures.append("strict Julia carrier Manifest.toml is not tracked by git")
    if repo_project.get("manifest_parse_error"):
        failures.append("strict Julia carrier Manifest.toml does not parse")
    metadata = repo_project.get("manifest_metadata", {})
    for field in ("julia_version", "manifest_format", "project_hash"):
        if not metadata.get(field):
            failures.append(f"strict Julia carrier Manifest.toml missing {field}")
    if repo_project.get("manifest_absolute_path_entries"):
        failures.append("strict Julia carrier Manifest.toml contains absolute path dependencies")
    if report["repo_pollution"]:
        failures.append("repo-local environment pollution found")
    active = report["active_installers"]
    if not active.get("ok", False):
        warnings.append("active installer process scan unavailable")
    elif active.get("matches"):
        warnings.append("active package installer or env mutator observed")

    return {
        "ok": not failures,
        "install_state": "in_flux" if report["active_installers"].get("matches") else "stable_observed",
        "failures": failures,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    parser.add_argument("--skip-julia", action="store_true", help="skip Julia import probe")
    parser.add_argument("--strict", action="store_true", help="exit nonzero on warnings too")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "schema": "codex_runtime_env_doctor.v1",
        "repo": str(REPO),
        "expected": {
            "sim_stack_alias": str(SIM_STACK_ALIAS),
            "physical_python_env": str(PHYSICAL_PYTHON_ENV),
            "python": str(CANONICAL_PYTHON),
            "julia": str(JULIA),
            "julia_project": str(JULIA_PROJECT),
            "julia_load_path": STRICT_JULIA_LOAD_PATH,
        },
        "sim_stack_alias": sim_stack_alias_state(),
        "python": python_probe(),
        "julia": julia_probe(args.skip_julia),
        "repo_project": project_dep_scan(),
        "repo_pollution": pollution_scan(),
        "active_installers": active_installers(),
    }
    report["summary"] = summarize(report)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(f"ok={summary['ok']} install_state={summary['install_state']}")
        print(f"repo={report['repo']}")
        print(f"sim_stack_alias={report['expected']['sim_stack_alias']}")
        print(f"physical_python_env={report['expected']['physical_python_env']}")
        print(f"python={report['expected']['python']}")
        print(f"julia={report['expected']['julia']}")
        print(f"julia_project={report['expected']['julia_project']}")
        print(f"julia_load_path={report['expected']['julia_load_path']}")
        for failure in summary["failures"]:
            print(f"FAIL {failure}")
        for warning in summary["warnings"]:
            print(f"WARN {warning}")
        if not summary["failures"] and not summary["warnings"]:
            print("No repo-local env pollution, missing expected modules, or active installers observed.")

    if not report["summary"]["ok"]:
        return 1
    if args.strict and report["summary"]["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
