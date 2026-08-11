#!/usr/bin/env python3
"""Read-only installation truth for the 91-row CB Light proposal manifest."""

from __future__ import annotations

import hashlib
import importlib.metadata as metadata
import argparse
import datetime as dt
import json
import pathlib
import platform
import site
import subprocess
import sys
import sysconfig
from collections import deque

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/cb_light_tools_v1.json"
OUTPUT = ROOT / "receipts/cb_light_install_runtime_v1.json"
# The installer and local ConstraintBox package are controller infrastructure,
# not members of the finite third-party CB Light candidate domain.
RUNTIME_INFRASTRUCTURE_DISTRIBUTIONS = frozenset({"pip", "constraintbox"})


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256_stream(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_runtime_infrastructure_artifact(path: pathlib.Path) -> bool:
    """Exclude editable controller metadata from the candidate file snapshot."""
    if path.name.startswith("__editable__.constraintbox-") and path.suffix == ".pth":
        return True
    return any(
        part.startswith("constraintbox-") and part.endswith(".dist-info")
        for part in path.parts
    )


def site_packages_snapshot() -> dict[str, object]:
    """Hash the complete persistent site-packages file set for this interpreter.

    Bytecode caches are excluded because imports may create or replace them without
    changing installed source.  Every other regular file, including ``.pth`` files
    and unowned modules, is included so a post-tool hook can detect shadow files.
    """

    prefix = pathlib.Path(sys.prefix).resolve()
    roots = sorted(
        {
            pathlib.Path(raw).resolve()
            for raw in site.getsitepackages()
            if pathlib.Path(raw).is_dir()
            and pathlib.Path(raw).resolve().is_relative_to(prefix)
        },
        key=str,
    )
    entries: list[dict[str, object]] = []
    for root in roots:
        for path in sorted(root.rglob("*"), key=str):
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            if is_runtime_infrastructure_artifact(path):
                continue
            try:
                if not path.is_file():
                    continue
                relative = str(path.resolve().relative_to(prefix))
                size = path.stat().st_size
                digest = sha256_stream(path)
            except (OSError, ValueError):
                continue
            entries.append({"path": relative, "bytes": size, "sha256": digest})
    return {
        "algorithm": "sha256(canonical(path,bytes,sha256) rows)",
        "excluded": [
            "**/__pycache__/**",
            "*.pyc",
            "*.pyo",
            "**/__editable__.constraintbox-*.pth",
            "**/constraintbox-*.dist-info/**",
        ],
        "roots": [str(root.relative_to(prefix)) for root in roots],
        "file_count": len(entries),
        "total_bytes": sum(int(row["bytes"]) for row in entries),
        "digest": hashlib.sha256(canonical_json(entries)).hexdigest(),
    }


def load_manifest(path: pathlib.Path) -> dict[str, object]:
    body = json.loads(path.read_text(encoding="utf-8"))
    if body.get("schema") != "constraintbox.cb-light-tool-manifest.v1":
        raise SystemExit("invalid CB Light manifest schema")
    claimed = body.get("manifest_sha256")
    identity = dict(body)
    identity.pop("manifest_sha256", None)
    observed = hashlib.sha256(canonical_json(identity)).hexdigest()
    if claimed != observed:
        raise SystemExit(
            f"CB Light manifest digest mismatch: claimed={claimed}, observed={observed}"
        )
    tools = body.get("tools")
    expected = int((body.get("counts") or {}).get("tools", -1))
    if not isinstance(tools, list) or len(tools) != expected:
        raise SystemExit(
            f"CB Light manifest must contain {expected} rows, got {len(tools or [])}"
        )
    return body


def distribution_size(dist: metadata.Distribution) -> int:
    total = 0
    for relative in dist.files or ():
        path = pathlib.Path(dist.locate_file(relative))
        try:
            if path.is_file():
                total += path.stat().st_size
        except OSError:
            pass
    return total


def import_probe(python: str, import_name: str) -> dict[str, object]:
    code = (
        "import importlib,json,sys; "
        f"m=importlib.import_module({import_name!r}); "
        "print(json.dumps({'module':m.__name__,'file':getattr(m,'__file__',None),"
        "'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix}))"
    )
    proc = subprocess.run(
        [python, "-I", "-c", code],
        capture_output=True,
        text=True,
        timeout=15,
        cwd="/tmp",
    )
    try:
        observation = json.loads(proc.stdout) if proc.returncode == 0 else None
    except ValueError:
        observation = None
    prefix_matches = bool(
        isinstance(observation, dict)
        and pathlib.Path(str(observation.get("prefix", ""))).resolve()
        == pathlib.Path(sys.prefix).resolve()
    )
    origin = (
        pathlib.Path(str(observation.get("file"))).resolve()
        if isinstance(observation, dict) and observation.get("file")
        else None
    )
    try:
        origin_under_prefix = bool(origin and origin.is_relative_to(pathlib.Path(sys.prefix).resolve()))
    except (OSError, ValueError):
        origin_under_prefix = False
    return {
        "passed": bool(
            proc.returncode == 0
            and observation is not None
            and prefix_matches
            and origin_under_prefix
        ),
        "returncode": proc.returncode,
        "observation": observation,
        "prefix_matches_probe_process": prefix_matches,
        "origin_under_probe_prefix": origin_under_prefix,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def active_runtime_requirements(dist: metadata.Distribution) -> list[str]:
    names: list[str] = []
    for raw in dist.requires or ():
        try:
            req = Requirement(raw)
        except Exception:
            continue
        if req.marker is not None and not req.marker.evaluate():
            continue
        names.append(canonicalize_name(req.name))
    return sorted(set(names))


def closure(roots: set[str], by_name: dict[str, metadata.Distribution]) -> set[str]:
    seen: set[str] = set()
    queue = deque(sorted(roots))
    while queue:
        name = queue.popleft()
        if name in seen:
            continue
        seen.add(name)
        dist = by_name.get(name)
        if dist is None:
            continue
        for dependency in active_runtime_requirements(dist):
            if dependency not in seen:
                queue.append(dependency)
    return seen


def distribution_file_owners(
    by_name: dict[str, metadata.Distribution],
) -> dict[str, list[str]]:
    owners: dict[str, set[str]] = {}
    for name, dist in by_name.items():
        for relative in dist.files or ():
            try:
                resolved = str(pathlib.Path(dist.locate_file(relative)).resolve())
            except OSError:
                continue
            owners.setdefault(resolved, set()).add(name)
    return {path: sorted(names) for path, names in owners.items()}


def scoped_dependency_issues(
    names: set[str], by_name: dict[str, metadata.Distribution]
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for source in sorted(names):
        dist = by_name.get(source)
        if dist is None:
            continue
        for raw in dist.requires or ():
            try:
                requirement = Requirement(raw)
            except Exception:
                continue
            if requirement.marker is not None and not requirement.marker.evaluate():
                continue
            target = canonicalize_name(requirement.name)
            installed = by_name.get(target)
            version = installed.version if installed else None
            satisfied = bool(
                installed is not None
                and (
                    not requirement.specifier
                    or requirement.specifier.contains(version, prereleases=True)
                )
            )
            if not satisfied:
                issues.append(
                    {
                        "source": source,
                        "requirement": raw,
                        "target": target,
                        "installed_version": version,
                    }
                )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-python")
    parser.add_argument(
        "--environment-role", choices=("runtime", "clean"), default="runtime"
    )
    parser.add_argument("--install-report", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path, default=MANIFEST)
    parser.add_argument("--output", type=pathlib.Path, default=OUTPUT)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    manifest = load_manifest(manifest_path)
    mandated_python = pathlib.Path(str(manifest["mandated_interpreter"])).expanduser()
    expected_python = pathlib.Path(
        str(
            args.expected_python
            or (mandated_python if args.environment_role == "runtime" else sys.executable)
        )
    ).expanduser()
    output = args.output.resolve()

    observed_prefix = pathlib.Path(sys.prefix).resolve()
    expected_prefix = expected_python.parent.parent.resolve()
    mandated_prefix = mandated_python.parent.parent.resolve()
    if observed_prefix != expected_prefix:
        raise SystemExit(
            f"wrong interpreter environment: executable={sys.executable}, "
            f"prefix={observed_prefix}, expected_prefix={expected_prefix}"
        )
    if args.environment_role == "runtime" and observed_prefix != mandated_prefix:
        raise SystemExit(f"runtime probe is not in contained environment: {observed_prefix}")
    if args.environment_role == "clean" and observed_prefix == mandated_prefix:
        raise SystemExit("clean probe cannot run in the contained runtime environment")

    declared = list(manifest["tools"])
    installed = {
        canonicalize_name(dist.metadata["Name"]): dist
        for dist in metadata.distributions()
        if dist.metadata.get("Name")
    }
    provider_map = metadata.packages_distributions()
    file_owners = distribution_file_owners(installed)
    rows: list[dict[str, object]] = []
    for tool in declared:
        normalized = canonicalize_name(str(tool["distribution"]))
        dist = installed.get(normalized)
        import_names = list(tool["import_names"])
        import_name = str(import_names[0])
        top_level_provider_candidates = sorted(
            canonicalize_name(name)
            for name in provider_map.get(import_name.split(".")[0], [])
        )
        expected_providers = sorted(
            canonicalize_name(str(name))
            for name in tool["expected_provider_distributions"]
        )
        version = dist.version if dist else None
        probe = import_probe(sys.executable, import_name) if dist else {
            "passed": False,
            "returncode": None,
            "observation": None,
            "prefix_matches_probe_process": False,
            "stdout": "",
            "stderr": "distribution missing",
        }
        origin = (
            str((probe.get("observation") or {}).get("file") or "")
            if isinstance(probe.get("observation"), dict)
            else ""
        )
        providers = file_owners.get(str(pathlib.Path(origin).resolve()), []) if origin else []
        rows.append(
            {
                "distribution": tool["distribution"],
                "normalized_name": normalized,
                "required": f"{tool['locked_distribution']}=={tool['locked_version']}",
                "locked_version": tool["locked_version"],
                "installed": dist is not None,
                "installed_version": version,
                "version_matches": bool(dist is not None and version == tool["locked_version"]),
                "import_name": import_name,
                "import_providers": providers,
                "top_level_provider_candidates": top_level_provider_candidates,
                "expected_provider_distributions": expected_providers,
                "expected_provider_present": set(expected_providers) == set(providers),
                "import_probe": probe,
                "installed_bytes": distribution_size(dist) if dist else 0,
                "requires_dist": active_runtime_requirements(dist) if dist else [],
            }
        )

    expected_roots = int((manifest.get("counts") or {}).get("tools", -1))
    roots = {canonicalize_name(str(tool["distribution"])) for tool in declared}
    closure_names = closure(roots, installed)
    dependency_issues = scoped_dependency_issues(closure_names, installed)
    closure_rows = []
    for name in sorted(closure_names):
        dist = installed.get(name)
        closure_rows.append(
            {
                "distribution": name,
                "root": name in roots,
                "installed": dist is not None,
                "version": dist.version if dist else None,
                "installed_bytes": distribution_size(dist) if dist else 0,
                "requires_dist": list(dist.requires or ()) if dist else [],
            }
        )

    pip_check = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=ROOT,
    )
    # ``constraintbox`` is the contained controller package, not a proposed
    # third-party Light tool.  It must be installed for the public CLI/hooks
    # to be runnable, so exclude only this literal infrastructure distribution
    # alongside pip from the candidate-environment closure check.
    environment_extras = sorted(
        set(installed) - closure_names - RUNTIME_INFRASTRUCTURE_DISTRIBUTIONS
    )
    environment_exact = not environment_extras
    rows_by_name = {str(row["normalized_name"]): row for row in rows}
    for name in sorted(roots):
        row = rows_by_name[name]
        root_closure = closure({name}, installed)
        root_missing = sorted(candidate for candidate in root_closure if candidate not in installed)
        root_issues = scoped_dependency_issues(root_closure, installed)
        root_ok = bool(
            row["installed"]
            and row["version_matches"]
            and row["import_probe"]["passed"]
            and row["expected_provider_present"]
            and not root_missing
            and not root_issues
        )
        row.update(
            {
                "root_dependency_closure": sorted(root_closure),
                "root_dependency_missing": root_missing,
                "root_dependency_requirement_issues": root_issues,
                "root_install_constraints_satisfied": root_ok,
            }
        )
    install_report = None
    if args.install_report is not None:
        report_path = args.install_report.resolve()
        if not report_path.is_file():
            raise SystemExit(f"install report missing: {report_path}")
        report_body = json.loads(report_path.read_text(encoding="utf-8"))
        report_records = []
        for record in report_body.get("install") or []:
            record_metadata = record.get("metadata") or {}
            download = record.get("download_info") or {}
            archive = download.get("archive_info") or {}
            report_records.append(
                {
                    "distribution": canonicalize_name(str(record_metadata.get("name", ""))),
                    "version": str(record_metadata.get("version", "")),
                    "requested": record.get("requested") is True,
                    "url": download.get("url"),
                    "archive_hashes": dict(archive.get("hashes") or {}),
                }
            )
        report_records.sort(key=lambda row: (row["distribution"], row["version"]))
        install_report = {
            "path": str(report_path.relative_to(ROOT)),
            "sha256": sha256(report_path),
            "pip_version": report_body.get("pip_version"),
            "install_records": len(report_records),
            "records": report_records,
        }
    counts = {
        "proposed_roots": len(rows),
        "distribution_present": sum(bool(row["installed"]) for row in rows),
        "version_matches": sum(bool(row["version_matches"]) for row in rows),
        "import_passed": sum(bool(row["import_probe"]["passed"]) for row in rows),
        "provider_bound": sum(bool(row["expected_provider_present"]) for row in rows),
        "closure_distributions": len(closure_rows),
        "closure_missing": sum(not bool(row["installed"]) for row in closure_rows),
        "closure_requirement_violations": len(dependency_issues),
        "environment_extras": len(environment_extras),
    }
    all_root_constraints_satisfied = (
        counts["proposed_roots"] == expected_roots
        and all(row["root_install_constraints_satisfied"] for row in rows)
        and counts["closure_missing"] == 0
        and counts["closure_requirement_violations"] == 0
    )
    all_install_constraints_satisfied = (
        all_root_constraints_satisfied and environment_exact
    )
    receipt = {
        "schema": "constraintbox.cb-light-install-probe.v1",
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "environment_role": args.environment_role,
        "interpreter": sys.executable,
        "python_version": sys.version.split()[0],
        "environment": {
            "prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
            "expected_prefix": str(expected_prefix),
            "mandated_prefix": str(mandated_prefix),
            "user_site_enabled": bool(site.ENABLE_USER_SITE),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "sysconfig_platform": sysconfig.get_platform(),
            "extra_distributions": environment_extras,
            "environment_exact": environment_exact,
        },
        "install_report": install_report,
        "manifest": str(manifest_path.relative_to(ROOT)),
        "manifest_file_sha256": sha256(manifest_path),
        "manifest_identity_sha256": manifest["manifest_sha256"],
        "probe_source_sha256": sha256(pathlib.Path(__file__).resolve()),
        "counts": counts,
        "sizes": {
            "direct_installed_bytes": sum(int(row["installed_bytes"]) for row in rows),
            "closure_installed_bytes": sum(
                int(row["installed_bytes"]) for row in closure_rows
            ),
        },
        "rows": rows,
        "closure": closure_rows,
        "runtime_inventory_sha256": hashlib.sha256(
            canonical_json(
                {
                    row["distribution"]: row["version"]
                    for row in closure_rows
                    if row["installed"]
                }
            )
        ).hexdigest(),
        "site_packages_snapshot": site_packages_snapshot(),
        "scoped_dependency_check": {
            "passed": not dependency_issues,
            "issues": dependency_issues,
        },
        "pip_check": {
            "scope": "ambient_environment_observation_not_cb_light_disposition",
            "passed": pip_check.returncode == 0,
            "returncode": pip_check.returncode,
            "stdout": pip_check.stdout.strip(),
            "stderr": pip_check.stderr.strip(),
        },
        "all_root_constraints_satisfied": all_root_constraints_satisfied,
        "all_install_constraints_satisfied": all_install_constraints_satisfied,
        "disposition": "ADMIT" if all_install_constraints_satisfied else "HOLD",
        "reason_code": (
            "INSTALL_CONSTRAINTS_SATISFIED"
            if all_install_constraints_satisfied
            else "INSTALL_CONSTRAINTS_INCOMPLETE"
        ),
        "promotion_allowed": False,
        "claim_ceiling": (
            "root installation, exact root version, resolved-file provider, isolated "
            "subprocess import, and scoped dependency-closure truth in this interpreter "
            "only; transitive artifact reproducibility, operation, and adoption remain unproven"
        ),
    }
    encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(encoded, encoding="utf-8")
    if args.quiet:
        print(
            f"CB Light install facts: roots={counts['distribution_present']}/{expected_roots}, "
            f"versions={counts['version_matches']}/{expected_roots}, "
            f"imports={counts['import_passed']}/{expected_roots}, "
            f"providers={counts['provider_bound']}/{expected_roots}, "
            f"closure_missing={counts['closure_missing']}, "
            f"scoped_deps={'PASS' if not dependency_issues else 'HOLD'}, "
            f"ambient_pip_check={'PASS' if pip_check.returncode == 0 else 'HOLD'}"
        )
        print(f"receipt: {output}")
    else:
        print(encoded, end="")
    # A HOLD is a completed measurement, not a probe-process failure.  The
    # selector consumes per-tool failures and emits HOLD rows deterministically.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
