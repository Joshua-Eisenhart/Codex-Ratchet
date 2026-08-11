#!/usr/bin/env python3
"""Fail closed unless the distributable CB Light surface excludes CB Heavy.

The repository intentionally retains a legacy mixed ConstraintBox package and
its simulation adapters for CB Heavy work.  This audit does not relabel that
code as Light.  It instead examines the separately packaged Light runtime,
then builds and imports it from a fresh interpreter to prove that the public
Light distribution has no Heavy module path or interpreter dependency.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import importlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
LIGHT_PROJECT = ROOT / "light_runtime"
LIGHT_SOURCE = LIGHT_PROJECT / "src" / "constraintbox"
LIGHT_HOOKKERNEL_SOURCE = LIGHT_PROJECT / "src" / "hookkernel"
FORBIDDEN_IMPORT_ROOTS = {
    "e3nn",
    "jax",
    "jaxlib",
    "torch",
    "torch_geometric",
    "juliacall",
    "juliapkg",
    "diffrax",
    "gudhi",
    "igraph",
    "pydmd",
    "pymdp",
    "pykoopman",
    "pysindy",
    "quimb",
    "toponetx",
    "xgi",
}
FORBIDDEN_LIGHT_MODULES = tuple(
    sorted(
        {
            "constraintbox.capability_dispatch",
            "constraintbox.external_capability",
            "constraintbox.external_e3nn_capability",
            "constraintbox.external_s3_capability",
            "constraintbox.graph_topology_worker",
            # These generic root-kernel modules belong to the retained legacy
            # estate.  The Light wheel deliberately contains only the finite
            # domain/gate/runtime/state subset below.
            "hookkernel.kernel",
            "hookkernel.pypi_authority",
            "hookkernel.receipts",
            *FORBIDDEN_IMPORT_ROOTS,
        }
    )
)
ALLOWED_LIGHT_HOOKKERNEL_PYTHON_PATHS = (
    "hookkernel/__init__.py",
    "hookkernel/cb_light_domain.py",
    "hookkernel/cb_light_gate.py",
    "hookkernel/cb_light_runtime.py",
    "hookkernel/cb_light_solver.py",
    "hookkernel/cb_light_state.py",
    # This is a local SQLite fixture ledger only.  The public ``wave`` command
    # may use it only after a current Light evaluation; it does not invoke a
    # model, provider, network, or CB Heavy engine.
    "hookkernel/cb_light_wave_state.py",
)
REQUIRED_LIGHT_HOOKKERNEL_MODULES = tuple(
    path.removesuffix(".py").replace("/", ".")
    for path in ALLOWED_LIGHT_HOOKKERNEL_PYTHON_PATHS
    if path != "hookkernel/__init__.py"
)
FORBIDDEN_WHEEL_PATH_PARTS = (
    "/external_",
    "/capability_dispatch.py",
    "/graph_topology_worker.py",
    "/cli.py",
    "/hookkernel/kernel.py",
    "/hookkernel/pypi_authority.py",
    "/hookkernel/receipts.py",
)
FORBIDDEN_SHELL_OR_CONFIG_REFS = (
    "system_v5/",
    "sim_engines/",
    ".local/share/codex-ratchet/envs/main",
    "constraintbox-legacy",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def python_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id not in {"__import__", "import_module"}:
                continue
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(
                node.args[0].value, str
            ):
                roots.append(node.args[0].value.split(".", 1)[0])
    return sorted(set(roots))


def executable_python_paths() -> list[Path]:
    paths: list[Path] = []
    for directory in (LIGHT_SOURCE, LIGHT_HOOKKERNEL_SOURCE, ROOT / "hooks"):
        paths.extend(sorted(directory.rglob("*.py")))
    paths.extend(
        sorted(
            path
            for path in (ROOT / "scripts").glob("*.py")
            if path.name.startswith(("cb_light_", "audit_cb_light_", "exercise_cb_light_"))
        )
    )
    return sorted(set(paths))


def shell_and_config_paths() -> list[Path]:
    return [
        REPO / ".claude" / "settings.json",
        REPO / ".claude" / "hooks" / "cb_pretooluse_guard.sh",
        REPO / ".claude" / "hooks" / "cb_posttooluse_record.sh",
        REPO / ".claude" / "hooks" / "session-start.sh",
        ROOT / "bin" / "cb-light",
        ROOT / "hooks" / "pre_tool.sh",
        ROOT / "hooks" / "post_tool.sh",
        ROOT / "hooks" / "session_start.sh",
    ]


def _base_interpreter() -> Path:
    return Path(getattr(sys, "_base_executable", sys.executable)).resolve()


def _surface_probe_code() -> str:
    """Return the isolated probe run against an installed Light wheel.

    Both the fresh wheel and the actual contained runtime must satisfy this
    exact surface check.  It rejects both Heavy imports and legacy generic
    ``hookkernel`` modules, which otherwise could carry a shared interpreter
    path into Light without appearing in the five direct Python dependencies.
    """

    return """
import importlib, importlib.metadata as metadata, importlib.util, json, sys
from pathlib import Path
forbidden = %r
allowed_hookkernel_paths = set(%r)
required_hookkernel_modules = %r
package = importlib.import_module('constraintbox')
hookkernel = importlib.import_module('hookkernel')
from hookkernel.cb_light_domain import compile_domain
domain = compile_domain(installed={}, distribution_imports={})
attempts = {}
for name in forbidden:
    try:
        importlib.import_module(name)
    except ModuleNotFoundError:
        attempts[name] = 'MISSING'
    except Exception as exc:
        attempts[name] = 'ERROR:' + type(exc).__name__
    else:
        attempts[name] = 'IMPORTED'
files = [str(item).replace('\\\\', '/') for item in (metadata.distribution('constraintbox').files or [])]
hookkernel_root = Path(hookkernel.__file__).resolve().parent
# Metadata proves what the wheel recorded, but this physical walk proves the
# running interpreter cannot hide an extra ``.py`` beside that record.
hookkernel_python_paths = sorted(
    str(path.resolve().relative_to(hookkernel_root.parent)).replace('\\\\', '/')
    for path in hookkernel_root.rglob('*.py')
    if '__pycache__' not in path.parts
)
prefix = Path(sys.prefix).resolve()
def under_prefix(raw):
    try:
        return Path(raw).resolve().is_relative_to(prefix)
    except (OSError, ValueError):
        return False
print(json.dumps({
  'package_file': package.__file__,
  'hookkernel_file': hookkernel.__file__,
  'attempts': attempts,
  'find_spec': {name: bool(importlib.util.find_spec(name)) for name in forbidden},
  'expected_hookkernel_modules': {name: bool(importlib.util.find_spec(name)) for name in required_hookkernel_modules},
  'loaded_heavy': sorted(name for name in sys.modules if name in forbidden or name.startswith('constraintbox.external_')),
  'wheel_forbidden_paths': sorted(path for path in files if any(part in '/' + path for part in %r)),
  'hookkernel_python_paths': hookkernel_python_paths,
  'unexpected_hookkernel_python_paths': sorted(set(hookkernel_python_paths) - allowed_hookkernel_paths),
  'missing_hookkernel_python_paths': sorted(allowed_hookkernel_paths - set(hookkernel_python_paths)),
  'package_under_sys_prefix': under_prefix(package.__file__),
  'hookkernel_under_sys_prefix': under_prefix(hookkernel.__file__),
  'domain_compiled': domain.get('schema') == 'constraintbox.cb-light-proposal-domain.v1' and int((domain.get('counts') or {}).get('objects', 0)) > 0,
  'legacy_entrypoint_present': bool((Path(sys.executable).parent / 'constraintbox-legacy').exists()),
}, sort_keys=True))
""" % (
        list(FORBIDDEN_LIGHT_MODULES),
        list(ALLOWED_LIGHT_HOOKKERNEL_PYTHON_PATHS),
        list(REQUIRED_LIGHT_HOOKKERNEL_MODULES),
        list(FORBIDDEN_WHEEL_PATH_PARTS),
    )


def _probe_installed_surface(python: Path, prefix: Path) -> dict[str, Any]:
    """Interrogate one installed Light distribution under ``python -I``."""

    observed = subprocess.run(
        [str(python), "-I", "-c", _surface_probe_code()],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    try:
        payload = json.loads(observed.stdout)
    except json.JSONDecodeError:
        payload = None
    if observed.returncode != 0 or not isinstance(payload, dict):
        return {
            "passed": False,
            "probe_error": "INSTALLED_SURFACE_PROBE_FAILED",
            "returncode": observed.returncode,
            "stderr_tail": observed.stderr[-600:],
        }
    attempts = payload.get("attempts")
    find_spec = payload.get("find_spec")
    expected_modules = payload.get("expected_hookkernel_modules")
    try:
        package_under_prefix = Path(
            str(payload.get("package_file", ""))
        ).resolve().is_relative_to(prefix.resolve())
        hookkernel_under_prefix = Path(
            str(payload.get("hookkernel_file", ""))
        ).resolve().is_relative_to(prefix.resolve())
    except (OSError, ValueError):
        package_under_prefix = False
        hookkernel_under_prefix = False
    passed = bool(
        isinstance(attempts, dict)
        and isinstance(find_spec, dict)
        and isinstance(expected_modules, dict)
        and all(value == "MISSING" for value in attempts.values())
        and not any(bool(value) for value in find_spec.values())
        and all(value is True for value in expected_modules.values())
        and not payload.get("loaded_heavy")
        and not payload.get("wheel_forbidden_paths")
        and payload.get("unexpected_hookkernel_python_paths") == []
        and payload.get("missing_hookkernel_python_paths") == []
        and payload.get("hookkernel_python_paths")
        == list(ALLOWED_LIGHT_HOOKKERNEL_PYTHON_PATHS)
        and payload.get("package_under_sys_prefix") is True
        and payload.get("hookkernel_under_sys_prefix") is True
        and payload.get("domain_compiled") is True
        and payload.get("legacy_entrypoint_present") is False
        and package_under_prefix
        and hookkernel_under_prefix
    )
    return {
        "passed": passed,
        "package_under_target_prefix": package_under_prefix,
        "hookkernel_under_target_prefix": hookkernel_under_prefix,
        "observation": payload,
    }


def _fresh_wheel_probe() -> dict[str, Any]:
    """Build and interrogate a fresh Light-only wheel without network access.

    The wheel is built from a verifier-owned copy rather than the live source
    directory.  A status/complete check is read-only from the project's point
    of view: it must not create or delete ``build/`` or ``*.egg-info`` beside
    the active Light source, and two live checks must be safe to run together.
    """

    base = _base_interpreter()
    if not base.is_file():
        return {"passed": False, "reason_code": "LIGHT_BUILD_INTERPRETER_MISSING"}
    with tempfile.TemporaryDirectory(prefix="cb-light-heavy-audit-") as temporary:
        work = Path(temporary)
        project_snapshot = work / "light_runtime"
        # ``SOURCES.txt`` can retain modules from an older package layout.
        # Copying only source inputs gives each verifier a clean, immutable
        # build context and prevents one audit from perturbing another.
        shutil.copytree(
            LIGHT_PROJECT,
            project_snapshot,
            ignore=shutil.ignore_patterns(
                "build", "*.egg-info", "__pycache__", "*.pyc", "*.pyo"
            ),
        )
        wheels = work / "wheels"
        fresh = work / "fresh"
        wheels.mkdir()
        build = subprocess.run(
            [
                str(base),
                "-m",
                "pip",
                "wheel",
                "--disable-pip-version-check",
                "--no-deps",
                "--no-build-isolation",
                "--wheel-dir",
                str(wheels),
                str(project_snapshot),
            ],
            cwd=work,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        candidates = sorted(wheels.glob("constraintbox-*.whl"))
        if build.returncode != 0 or len(candidates) != 1:
            return {
                "passed": False,
                "reason_code": "LIGHT_WHEEL_BUILD_FAILED",
                "returncode": build.returncode,
                "stderr_tail": build.stderr[-600:],
            }
        wheel = candidates[0]
        created = subprocess.run(
            [str(base), "-m", "venv", str(fresh)],
            cwd=work,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        fresh_python = fresh / "bin" / "python"
        if created.returncode != 0 or not fresh_python.is_file():
            return {
                "passed": False,
                "reason_code": "LIGHT_FRESH_VENV_CREATE_FAILED",
                "returncode": created.returncode,
                "stderr_tail": created.stderr[-600:],
            }
        installed = subprocess.run(
            [
                str(fresh_python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--isolated",
                "--no-deps",
                str(wheel),
            ],
            cwd=work,
            capture_output=True,
            text=True,
            check=False,
            timeout=90,
        )
        if installed.returncode != 0:
            return {
                "passed": False,
                "reason_code": "LIGHT_WHEEL_INSTALL_FAILED",
                "returncode": installed.returncode,
                "stderr_tail": installed.stderr[-600:],
            }
        surface = _probe_installed_surface(fresh_python, fresh)
        if surface.get("probe_error"):
            return {
                "passed": False,
                "reason_code": "LIGHT_WHEEL_IMPORT_PROBE_FAILED",
                "returncode": surface.get("returncode"),
                "stderr_tail": surface.get("stderr_tail"),
            }
        passed = surface["passed"] is True
        return {
            "passed": passed,
            "reason_code": (
                "LIGHT_WHEEL_FRESH_IMPORT_SEPARATION_VERIFIED"
                if passed
                else "LIGHT_WHEEL_HEAVY_SURFACE_OBSERVED"
            ),
            "build_source": "VERIFIER_OWNED_TEMPORARY_COPY",
            "wheel_sha256": __import__("hashlib").sha256(
                wheel.read_bytes()
            ).hexdigest(),
            "package_under_fresh_prefix": surface["package_under_target_prefix"],
            "hookkernel_under_fresh_prefix": surface[
                "hookkernel_under_target_prefix"
            ],
            "fresh_observation": surface["observation"],
        }


def _contained_runtime_probe() -> dict[str, Any]:
    """Verify the actual contained runtime, not just a newly built wheel."""

    contained = ROOT / ".venv"
    python = contained / "bin" / "python"
    if not python.is_file():
        return {"passed": False, "reason_code": "CONTAINED_LIGHT_RUNTIME_MISSING"}
    surface = _probe_installed_surface(python, contained)
    if surface.get("probe_error"):
        return {
            "passed": False,
            "reason_code": "CONTAINED_LIGHT_RUNTIME_IMPORT_PROBE_FAILED",
            "returncode": surface.get("returncode"),
            "stderr_tail": surface.get("stderr_tail"),
        }
    passed = surface["passed"] is True
    return {
        "passed": passed,
        "reason_code": (
            "CONTAINED_LIGHT_RUNTIME_SEPARATION_VERIFIED"
            if passed
            else "CONTAINED_LIGHT_RUNTIME_HEAVY_SURFACE_OBSERVED"
        ),
        "package_under_contained_prefix": surface["package_under_target_prefix"],
        "hookkernel_under_contained_prefix": surface[
            "hookkernel_under_target_prefix"
        ],
        "contained_observation": surface["observation"],
    }


def render() -> dict[str, Any]:
    manifest = load_json(ROOT / "config" / "cb_light_tools_v1.json")
    contract = load_json(ROOT / "config" / "cb_light_contract_v1.json")
    pyproject = tomllib.loads((LIGHT_PROJECT / "pyproject.toml").read_text(encoding="utf-8"))
    candidate_names = {str(row["normalized_name"]) for row in manifest.get("tools", [])}
    forbidden_candidates = sorted(candidate_names & FORBIDDEN_IMPORT_ROOTS)
    forbidden_imports: dict[str, list[str]] = {}
    for path in executable_python_paths():
        hits = sorted(set(python_imports(path)) & FORBIDDEN_IMPORT_ROOTS)
        if hits:
            forbidden_imports[str(path.relative_to(ROOT))] = hits
    forbidden_refs: dict[str, list[str]] = {}
    for path in shell_and_config_paths():
        if not path.is_file():
            forbidden_refs[str(path)] = ["MISSING_ACTIVE_HOOK_OR_CONFIG"]
            continue
        text = path.read_text(encoding="utf-8")
        hits = [needle for needle in FORBIDDEN_SHELL_OR_CONFIG_REFS if needle in text]
        if hits:
            forbidden_refs[str(path.relative_to(REPO))] = hits
    direct_dependencies = {
        re.match(r"\s*([A-Za-z0-9_.-]+)", requirement).group(1).lower()
        for requirement in pyproject["project"]["dependencies"]
    }
    forbidden_direct_dependencies = sorted(direct_dependencies & FORBIDDEN_IMPORT_ROOTS)
    audit_source_bound = (
        "scripts/audit_cb_light_heavy_separation.py"
        in set(contract.get("required_source_paths") or [])
    )
    wheel_probe = _fresh_wheel_probe()
    contained_runtime_probe = _contained_runtime_probe()
    failures = {
        "forbidden_candidate_names": forbidden_candidates,
        "forbidden_python_imports": forbidden_imports,
        "forbidden_shell_or_config_references": forbidden_refs,
        "forbidden_direct_dependencies": forbidden_direct_dependencies,
        "manifest_sim_engine_members": manifest.get("set_separation", {}).get(
            "sim_engine_members"
        ),
        "audit_source_bound": audit_source_bound,
        "fresh_wheel_probe": wheel_probe,
        "contained_runtime_probe": contained_runtime_probe,
    }
    passed = (
        not forbidden_candidates
        and not forbidden_imports
        and not forbidden_refs
        and not forbidden_direct_dependencies
        and failures["manifest_sim_engine_members"] == 0
        and audit_source_bound
        and wheel_probe.get("passed") is True
        and contained_runtime_probe.get("passed") is True
    )
    return {
        "schema": "constraintbox.cb-light-heavy-separation-audit.v2",
        "audited_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "manifest_identity_sha256": manifest["manifest_sha256"],
        "contract_path": "config/cb_light_contract_v1.json",
        "light_project_path": "light_runtime/pyproject.toml",
        "required_source_path_count": len(contract["required_source_paths"]),
        "claim_ceiling": (
            "CB Light package and contained hook executable separation only; "
            "it does not establish a CB Heavy setup, bridge, simulation, portable adoption, or release claim."
        ),
        "disposition": "ADMIT" if passed else "REFUSE",
        "reason_code": (
            "LIGHT_PACKAGE_AND_FRESH_INTERPRETER_HAVE_NO_HEAVY_SURFACE"
            if passed
            else "LIGHT_HEAVY_EXECUTABLE_BOUNDARY_VIOLATION"
        ),
        "checked": {
            "python_files": [str(path.relative_to(ROOT)) for path in executable_python_paths()],
            "shell_and_config_files": [str(path.relative_to(REPO)) for path in shell_and_config_paths()],
            "forbidden_import_roots": sorted(FORBIDDEN_IMPORT_ROOTS),
            "forbidden_light_modules": list(FORBIDDEN_LIGHT_MODULES),
            "allowed_light_hookkernel_python_paths": list(
                ALLOWED_LIGHT_HOOKKERNEL_PYTHON_PATHS
            ),
            "forbidden_shell_or_config_references": list(FORBIDDEN_SHELL_OR_CONFIG_REFS),
        },
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="audit-cb-light-heavy-separation")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "receipts" / "cb_light_heavy_separation_audit_v2.json",
    )
    args = parser.parse_args()
    body = render()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"disposition": body["disposition"], "reason_code": body["reason_code"]}))
    return 0 if body["disposition"] == "ADMIT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
