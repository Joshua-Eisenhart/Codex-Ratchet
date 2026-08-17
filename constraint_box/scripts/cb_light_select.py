#!/usr/bin/env python3
"""Recompute and solve the contained CB Light finite selection problem."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.metadata as installed_metadata
import json
import pathlib
import re
import sys
import sysconfig
from typing import Any

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    # The finite decider executes from the installed Light wheel, not the
    # legacy root hookkernel package that happens to coexist in the checkout.
    sys.path.append(str(ROOT))

from hookkernel.cb_light_solver import solve_selection  # noqa: E402


DEFAULT_MANIFEST = ROOT / "config/cb_light_tools_v1.json"
DEFAULT_CONTRACT = ROOT / "config/cb_light_contract_v1.json"
DEFAULT_RUNTIME = ROOT / "receipts/cb_light_install_runtime_v1.json"
DEFAULT_CLEAN = ROOT / "receipts/cb_light_install_clean_v1.json"
DEFAULT_OPERATION = ROOT / "receipts/cb_light_tool_probes_v1.json"
DEFAULT_METADATA = ROOT / "receipts/cb_light_metadata_v1.json"
DEFAULT_OUTPUT = ROOT / "receipts/cb_light_selection_v1.json"
INSTALL_PROBE_SOURCE = ROOT / "scripts/cb_light_install_probe.py"
METADATA_PROBE_SOURCE = ROOT / "scripts/cb_light_metadata_probe.py"
OPERATION_PROBE_SOURCE = ROOT / "light_runtime/src/constraintbox/cb_light_tool_probes.py"


def manifest_interpreter(manifest: dict[str, Any]) -> pathlib.Path:
    """Resolve the relocatable launcher declaration against this CB root."""

    declared = pathlib.Path(str(manifest["mandated_interpreter"])).expanduser()
    if declared.is_absolute():
        return declared
    return ROOT / declared


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def aware_timestamp(receipt: dict[str, Any], source: str, *, hours: float = 24) -> dt.datetime:
    raw = receipt.get("observed_at")
    if not isinstance(raw, str):
        raise ValueError(f"{source} observed_at is missing")
    observed = dt.datetime.fromisoformat(raw)
    if observed.tzinfo is None:
        raise ValueError(f"{source} observed_at is not timezone-aware")
    observed = observed.astimezone(dt.timezone.utc)
    now = dt.datetime.now(dt.timezone.utc)
    if observed > now + dt.timedelta(minutes=5):
        raise ValueError(f"{source} observed_at is in the future")
    if now - observed > dt.timedelta(hours=hours):
        raise ValueError(f"{source} evidence is older than {hours:g} hours")
    return observed


def by_name(
    rows: list[dict[str, Any]], source: str, *, expected_count: int
) -> dict[str, dict[str, Any]]:
    mapped = {str(row.get("normalized_name")): row for row in rows}
    if len(rows) != expected_count or len(mapped) != expected_count:
        raise ValueError(
            f"{source} must contain exactly {expected_count} unique rows"
        )
    return mapped


def verify_manifest_and_contract(
    manifest_path: pathlib.Path, contract_path: pathlib.Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = read_json(manifest_path)
    identity = dict(manifest)
    claimed = identity.pop("manifest_sha256", None)
    observed = hashlib.sha256(canonical_json(identity)).hexdigest()
    if manifest.get("schema") != "constraintbox.cb-light-tool-manifest.v1":
        raise ValueError("invalid manifest schema")
    if claimed != observed:
        raise ValueError("manifest identity digest mismatch")
    contract = read_json(contract_path)
    if contract.get("schema") != "constraintbox.cb-light-contract.v1":
        raise ValueError("invalid contract schema")
    expected_counts = contract.get("expected_counts")
    if not isinstance(expected_counts, dict):
        raise ValueError("contract expected_counts missing")
    expected_roots = int(expected_counts.get("install_proposals", -1))
    expected_exclusions = int(expected_counts.get("preinstall_excluded", -1))
    rows = list(manifest.get("tools") or [])
    names = [str(row.get("normalized_name")) for row in rows]
    if len(rows) != expected_roots or len(set(names)) != expected_roots:
        raise ValueError(
            f"manifest must contain exactly {expected_roots} unique roots"
        )
    if set(names) != set(contract.get("install_proposal_names") or []):
        raise ValueError("manifest membership differs from contained contract")
    required = list(contract.get("usable_now_requires") or [])
    if manifest.get("constraints", {}).get("usable_now_requires") != required:
        raise ValueError("manifest usable-now law differs from contained contract")
    if manifest.get("constraints", {}).get("portable_adoption_requires_in_addition") != list(
        contract.get("portable_adoption_requires_in_addition") or []
    ):
        raise ValueError("manifest adoption law differs from contained contract")
    excluded = {
        str(row.get("normalized_name"))
        for row in manifest.get("preinstall_excluded_candidates") or []
    }
    if excluded != set(contract.get("preinstall_excluded_names") or []):
        raise ValueError("manifest exclusions differ from contained contract")
    if len(excluded) != expected_exclusions:
        raise ValueError("manifest exclusion count differs from contained contract")

    derived_counts = manifest.get("counts") or {}
    expected_derived = {
        "tools": expected_roots,
        "core": int(expected_counts.get("core", -1)),
        "extended": int(expected_counts.get("extended", -1)),
        "candidate_passing": int(expected_counts.get("candidate_passing", -1)),
        "preinstall_excluded": expected_exclusions,
        "evaluated_candidate_domain": expected_roots + expected_exclusions,
    }
    if derived_counts != expected_derived:
        raise ValueError("manifest counts differ from contained contract")

    source_hashes = manifest.get("source_hashes")
    if not isinstance(source_hashes, dict):
        raise ValueError("manifest source hashes missing")
    required_source_paths = contract.get("required_source_paths")
    if (
        not isinstance(required_source_paths, list)
        or len(required_source_paths) != len(set(required_source_paths))
        or set(source_hashes) != set(required_source_paths)
    ):
        raise ValueError("manifest source hash key set differs from contract")
    for relative, expected in source_hashes.items():
        source = (ROOT / relative).resolve()
        try:
            source.relative_to(ROOT)
        except ValueError as exc:
            raise ValueError(f"manifest source escapes contained root: {relative}") from exc
        if not source.is_file() or sha256_file(source) != expected:
            raise ValueError(f"manifest source digest mismatch: {relative}")
    if manifest.get("membership_authority") != "config/cb_light_contract_v1.json":
        raise ValueError("manifest has wrong membership authority")
    return manifest, contract


def require_receipt(
    path: pathlib.Path, *, schema: str, manifest_identity: str
) -> dict[str, Any]:
    receipt = read_json(path)
    if receipt.get("schema") != schema:
        raise ValueError(f"wrong receipt schema for {path}")
    if receipt.get("manifest_identity_sha256") != manifest_identity:
        raise ValueError(f"manifest identity mismatch in {path}")
    return receipt


def active_requirement_issues(closure_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    versions = {
        canonicalize_name(str(row.get("distribution"))): str(row.get("version"))
        for row in closure_rows
        if row.get("installed") is True
    }
    issues: list[dict[str, Any]] = []
    for row in closure_rows:
        source = canonicalize_name(str(row.get("distribution")))
        for raw in row.get("requires_dist") or []:
            try:
                requirement = Requirement(raw)
            except Exception:
                continue
            if requirement.marker is not None and not requirement.marker.evaluate():
                continue
            target = canonicalize_name(requirement.name)
            version = versions.get(target)
            satisfied = bool(
                version is not None
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


def dependency_closure_for_root(
    root: str, closure_rows: list[dict[str, Any]]
) -> set[str]:
    mapped = {
        canonicalize_name(str(row.get("distribution"))): row for row in closure_rows
    }
    seen: set[str] = set()
    pending = [root]
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        row = mapped.get(name)
        if row is None:
            continue
        for raw in row.get("requires_dist") or []:
            try:
                requirement = Requirement(raw)
            except Exception:
                continue
            if requirement.marker is not None and not requirement.marker.evaluate():
                continue
            target = canonicalize_name(requirement.name)
            if target not in seen:
                pending.append(target)
    return seen


def validate_site_packages_snapshot(snapshot: Any, source: str) -> None:
    if not isinstance(snapshot, dict):
        raise ValueError(f"{source} site-packages snapshot missing")
    digest = snapshot.get("digest")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError(f"{source} site-packages snapshot digest malformed")
    if not isinstance(snapshot.get("roots"), list) or not snapshot.get("roots"):
        raise ValueError(f"{source} site-packages roots missing")
    if type(snapshot.get("file_count")) is not int or snapshot["file_count"] <= 0:
        raise ValueError(f"{source} site-packages file count malformed")
    if type(snapshot.get("total_bytes")) is not int or snapshot["total_bytes"] <= 0:
        raise ValueError(f"{source} site-packages byte count malformed")


def live_runtime_inventory(runtime_prefix: pathlib.Path) -> tuple[dict[str, str], bool]:
    if pathlib.Path(sys.prefix).resolve() != runtime_prefix:
        raise ValueError(
            "selector must run inside the contained runtime for live remeasurement"
        )

    # ``importlib.metadata.distributions()`` searches every entry on
    # ``sys.path``.  This selector deliberately adds the project root so it can
    # import the contained hook kernel, and a checkout can contain an
    # ``*.egg-info`` directory.  That source-tree metadata must not be counted
    # as an extra distribution in the managed runtime.  Restrict discovery to
    # the venv's own site-packages directories instead.
    site_packages = {
        pathlib.Path(value).resolve()
        for key, value in sysconfig.get_paths().items()
        if key in {"purelib", "platlib"} and value
    }
    if not site_packages:
        raise ValueError("contained runtime has no site-packages path")
    for path in site_packages:
        try:
            path.relative_to(runtime_prefix)
        except ValueError as exc:
            raise ValueError(
                f"contained runtime site-packages escapes prefix: {path}"
            ) from exc
    observed = {
        canonicalize_name(dist.metadata["Name"]): dist.version
        for dist in installed_metadata.distributions(path=[str(path) for path in site_packages])
        if dist.metadata.get("Name")
    }
    return observed, True


def normalized_report_records(report_body: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in report_body.get("install") or []:
        metadata = record.get("metadata") or {}
        download = record.get("download_info") or {}
        archive = download.get("archive_info") or {}
        rows.append(
            {
                "distribution": canonicalize_name(str(metadata.get("name", ""))),
                "version": str(metadata.get("version", "")),
                "requested": record.get("requested") is True,
                "url": download.get("url"),
                "archive_hashes": dict(archive.get("hashes") or {}),
            }
        )
    rows.sort(key=lambda row: (row["distribution"], row["version"]))
    return rows


def validate_install_receipt(
    receipt: dict[str, Any],
    *,
    role: str,
    manifest: dict[str, Any],
    manifest_rows: dict[str, dict[str, Any]],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, str],
    dict[str, bool],
    dict[str, Any],
]:
    observed_at = aware_timestamp(receipt, f"{role} install receipt")
    if receipt.get("environment_role") != role:
        raise ValueError(f"install role mismatch: expected {role}")
    if receipt.get("probe_source_sha256") != sha256_file(INSTALL_PROBE_SOURCE):
        raise ValueError(f"{role} install probe source drift")
    environment = receipt.get("environment")
    if not isinstance(environment, dict):
        raise ValueError(f"{role} environment evidence missing")
    prefix = pathlib.Path(str(environment.get("prefix", ""))).resolve()
    runtime_prefix = manifest_interpreter(manifest).parent.parent.resolve()
    if role == "runtime" and prefix != runtime_prefix:
        raise ValueError("runtime receipt is not from contained .venv")
    if role == "clean" and prefix == runtime_prefix:
        raise ValueError("clean receipt aliases the contained runtime")

    report = receipt.get("install_report")
    if not isinstance(report, dict):
        raise ValueError(f"{role} pip install report binding missing")
    report_path = (ROOT / str(report.get("path", ""))).resolve()
    try:
        report_path.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"{role} install report escapes contained root") from exc
    if not report_path.is_file() or sha256_file(report_path) != report.get("sha256"):
        raise ValueError(f"{role} install report digest mismatch")
    report_body = read_json(report_path)
    report_records = normalized_report_records(report_body)
    if report.get("records") != report_records or report.get("install_records") != len(
        report_records
    ):
        raise ValueError(f"{role} install report self-summary mismatch")
    requested_names = {
        row["distribution"] for row in report_records if row["requested"]
    }
    if requested_names != set(manifest_rows):
        raise ValueError(
            f"{role} install report does not bind all {len(manifest_rows)} requested roots"
        )
    if any(not row["archive_hashes"].get("sha256") for row in report_records):
        raise ValueError(f"{role} installed artifact lacks a pip-reported sha256")

    rows = by_name(
        list(receipt.get("rows") or []),
        f"{role} install",
        expected_count=len(manifest_rows),
    )
    if set(rows) != set(manifest_rows):
        raise ValueError(f"{role} install identities differ from manifest")
    root_truth: dict[str, bool] = {}
    for name, row in rows.items():
        tool = manifest_rows[name]
        if row.get("distribution") != tool.get("distribution"):
            raise ValueError(f"{role} distribution identity mismatch: {name}")
        expected_providers = {
            canonicalize_name(str(value))
            for value in row.get("expected_provider_distributions") or []
        }
        observed_providers = {
            canonicalize_name(str(value))
            for value in row.get("import_providers") or []
        }
        probe = row.get("import_probe") or {}
        observation = probe.get("observation")
        origin = (
            pathlib.Path(str(observation.get("file"))).resolve()
            if isinstance(observation, dict) and observation.get("file")
            else None
        )
        try:
            origin_under_prefix = bool(origin and origin.is_relative_to(prefix))
        except (OSError, ValueError):
            origin_under_prefix = False
        import_passed = bool(
            probe.get("returncode") == 0
            and isinstance(observation, dict)
            and pathlib.Path(str(observation.get("prefix", ""))).resolve() == prefix
            and probe.get("prefix_matches_probe_process") is True
            and probe.get("origin_under_probe_prefix") is True
            and origin_under_prefix
        )
        installed = row.get("installed") is True
        version_matches = bool(
            installed and row.get("installed_version") == tool.get("locked_version")
        )
        provider_bound = bool(expected_providers and expected_providers == observed_providers)
        if row.get("version_matches") is not version_matches:
            raise ValueError(f"{role} version self-report mismatch: {name}")
        if row.get("expected_provider_present") is not provider_bound:
            raise ValueError(f"{role} provider self-report mismatch: {name}")
        if probe.get("passed") is not import_passed:
            raise ValueError(f"{role} import self-report mismatch: {name}")
        root_truth[name] = bool(installed and version_matches and provider_bound and import_passed)

    closure_rows = list(receipt.get("closure") or [])
    closure_identities = [
        canonicalize_name(str(row.get("distribution"))) for row in closure_rows
    ]
    if len(set(closure_identities)) != len(closure_rows):
        raise ValueError(f"{role} closure contains duplicate identities")
    closure = {
        canonicalize_name(str(row.get("distribution"))): str(row.get("version"))
        for row in closure_rows
        if row.get("installed") is True
    }
    if not set(manifest_rows).issubset(set(closure_identities)):
        raise ValueError(f"{role} closure omits proposed root identities")
    issues = active_requirement_issues(closure_rows)
    stored_check = receipt.get("scoped_dependency_check") or {}
    if stored_check.get("passed") is not (not issues) or stored_check.get("issues") != issues:
        raise ValueError(f"{role} dependency check self-report mismatch")
    inventory_sha = hashlib.sha256(canonical_json(closure)).hexdigest()
    if receipt.get("runtime_inventory_sha256") != inventory_sha:
        raise ValueError(f"{role} inventory digest mismatch")
    validate_site_packages_snapshot(
        receipt.get("site_packages_snapshot"), f"{role} install receipt"
    )

    closure_row_map = {
        canonicalize_name(str(row.get("distribution"))): row for row in closure_rows
    }
    for name, row in rows.items():
        root_closure = dependency_closure_for_root(name, closure_rows)
        root_rows = [
            closure_row_map[candidate]
            for candidate in sorted(root_closure)
            if candidate in closure_row_map
        ]
        root_missing = sorted(
            candidate
            for candidate in root_closure
            if candidate not in closure_row_map
            or closure_row_map[candidate].get("installed") is not True
        )
        root_issues = active_requirement_issues(root_rows)
        expected_root_truth = bool(
            root_truth[name] and not root_missing and not root_issues
        )
        if row.get("root_dependency_closure") != sorted(root_closure):
            raise ValueError(f"{role} root closure self-report mismatch: {name}")
        if row.get("root_dependency_missing") != root_missing:
            raise ValueError(f"{role} root missing self-report mismatch: {name}")
        if row.get("root_dependency_requirement_issues") != root_issues:
            raise ValueError(f"{role} root requirement self-report mismatch: {name}")
        if row.get("root_install_constraints_satisfied") is not expected_root_truth:
            raise ValueError(f"{role} root install self-report mismatch: {name}")
        root_truth[name] = expected_root_truth

    counts = receipt.get("counts") or {}
    derived_counts = {
        "proposed_roots": len(manifest_rows),
        "distribution_present": sum(row.get("installed") is True for row in rows.values()),
        "version_matches": sum(
            row.get("installed") is True
            and row.get("installed_version") == manifest_rows[name].get("locked_version")
            for name, row in rows.items()
        ),
        "import_passed": sum(row.get("import_probe", {}).get("passed") is True for row in rows.values()),
        "provider_bound": sum(
            {
                canonicalize_name(str(value))
                for value in row.get("expected_provider_distributions") or []
            }
            == {
                canonicalize_name(str(value))
                for value in row.get("import_providers") or []
            }
            for row in rows.values()
        ),
        "closure_distributions": len(closure_rows),
        "closure_missing": sum(row.get("installed") is not True for row in closure_rows),
        "closure_requirement_violations": len(issues),
        "environment_extras": len(environment.get("extra_distributions") or []),
    }
    if any(counts.get(key) != value for key, value in derived_counts.items()):
        raise ValueError(f"{role} install aggregate mismatch")
    all_roots = (
        all(root_truth.values())
        and not issues
        and derived_counts["closure_missing"] == 0
    )
    all_install = bool(all_roots and environment.get("environment_exact") is True)
    if receipt.get("all_root_constraints_satisfied") is not all_roots:
        raise ValueError(f"{role} root aggregate mismatch")
    if receipt.get("all_install_constraints_satisfied") is not all_install:
        raise ValueError(f"{role} install aggregate mismatch")
    if receipt.get("disposition") != ("ADMIT" if all_install else "HOLD"):
        raise ValueError(f"{role} install disposition mismatch")
    return rows, closure, root_truth, {
        "observed_at": observed_at,
        "environment_exact": environment.get("environment_exact") is True,
        "all_install_constraints_satisfied": all_install,
        "install_report_path": report_path,
        "site_packages_snapshot": receipt.get("site_packages_snapshot"),
    }


def _platform_facts(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    wheels = [row for row in artifacts if row.get("packagetype") == "bdist_wheel"]
    names = [str(row.get("filename", "")).lower() for row in wheels]
    pure = any("-none-any.whl" in name for name in names)
    platforms = {
        "linux": pure or any("manylinux" in name or "musllinux" in name for name in names),
        "macos": pure or any("macosx" in name for name in names),
        "windows": pure
        or any(
            "-win32.whl" in name or "-win_amd64.whl" in name or "-win_arm64.whl" in name
            for name in names
        ),
    }
    return {
        "pure_python_wheel": pure,
        "platform_wheel_available": platforms,
        "all_required_platforms_have_wheel": all(platforms.values()),
        "wheel_count": len(wheels),
        "largest_wheel_bytes": max((int(row.get("size") or 0) for row in wheels), default=None),
        "wheel_filenames": sorted(str(row.get("filename")) for row in wheels),
        "wheel_sha256": {
            str(row.get("filename")): row.get("sha256") for row in wheels
        },
    }


def _active_runtime_dependencies(
    raw_requirements: list[str], marker_environment: dict[str, str]
) -> list[str]:
    environment = dict(default_environment())
    environment.update({str(key): str(value) for key, value in marker_environment.items()})
    environment["extra"] = ""
    names: set[str] = set()
    for raw in raw_requirements:
        try:
            requirement = Requirement(raw)
        except Exception:
            continue
        if requirement.marker is not None and not requirement.marker.evaluate(environment):
            continue
        names.add(requirement.name)
    return sorted(names, key=str.lower)


def validate_metadata_receipt(
    receipt: dict[str, Any], manifest_rows: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    observed_at = aware_timestamp(receipt, "metadata receipt")
    if receipt.get("probe_source_sha256") != sha256_file(METADATA_PROBE_SOURCE):
        raise ValueError("metadata probe source drift")
    rows = by_name(
        list(receipt.get("rows") or []),
        "metadata receipt",
        expected_count=len(manifest_rows),
    )
    if set(rows) != set(manifest_rows):
        raise ValueError("metadata identities differ from manifest")
    available_count = 0
    local_admit = 0
    bar_count = 0
    today = observed_at.date()
    for name, row in rows.items():
        tool = manifest_rows[name]
        if row.get("distribution") != tool.get("distribution") or row.get(
            "locked_version"
        ) != tool.get("locked_version"):
            raise ValueError(f"metadata identity mismatch: {name}")
        authority = row.get("authority") or {}
        available = not authority.get("error")
        available_count += available
        if not available:
            continue
        artifacts = list(row.get("release_artifacts") or [])
        platforms = _platform_facts(artifacts)
        if row.get("platforms") != platforms:
            raise ValueError(f"metadata platform self-report mismatch: {name}")
        requires_python = row.get("requires_python")
        try:
            py312 = (
                SpecifierSet(str(requires_python)).contains("3.12", prereleases=True)
                if requires_python
                else None
            )
            py313 = (
                SpecifierSet(str(requires_python)).contains("3.13", prereleases=True)
                if requires_python
                else None
            )
        except Exception:
            py312 = py313 = None
        dependencies = _active_runtime_dependencies(
            list(row.get("requires_dist") or []), dict(row.get("marker_environment") or {})
        )
        if row.get("runtime_dependencies") != dependencies:
            raise ValueError(f"metadata dependency self-report mismatch: {name}")
        release_date_raw = row.get("release_date")
        release_date = dt.date.fromisoformat(release_date_raw) if release_date_raw else None
        age_days = (today - release_date).days if release_date else None
        if row.get("age_days") != age_days:
            raise ValueError(f"metadata age self-report mismatch: {name}")
        vulnerabilities = list(row.get("vulnerabilities") or [])
        predicates = {
            "locked_release_exists": bool(
                artifacts
                and row.get("observed_pinned_version") == tool.get("locked_version")
            ),
            "release_within_548_days": age_days is not None and age_days <= 548,
            "pinned_release_not_yanked": bool(artifacts)
            and not any(item.get("yanked") is True for item in artifacts),
            "requires_python_declared": bool(requires_python),
            "python_3_12_admitted": py312,
            "python_3_13_admitted": py313,
            "no_known_vulnerabilities": not vulnerabilities,
            "linux_macos_windows_wheels": platforms["all_required_platforms_have_wheel"],
            "declared_runtime_deps_at_most_3": len(dependencies) <= 3,
            "largest_wheel_at_most_5mib": bool(
                platforms["largest_wheel_bytes"] is not None
                and platforms["largest_wheel_bytes"] <= 5 * 1024 * 1024
            ),
            "wheel_hashes_present": bool(platforms["wheel_sha256"])
            and all(bool(value) for value in platforms["wheel_sha256"].values()),
        }
        if row.get("predicates") != predicates:
            raise ValueError(f"metadata predicate self-report mismatch: {name}")
        failed = sorted(key for key, value in predicates.items() if value is not True)
        local_safe = bool(
            predicates["locked_release_exists"]
            and predicates["pinned_release_not_yanked"]
            and predicates["no_known_vulnerabilities"]
            and predicates["python_3_13_admitted"] is not False
        )
        bar = all(value is True for value in predicates.values())
        if row.get("failed_predicates") != failed:
            raise ValueError(f"metadata failed predicate mismatch: {name}")
        if row.get("local_metadata_safe") is not local_safe:
            raise ValueError(f"metadata local safety mismatch: {name}")
        if row.get("candidate_metadata_bar_satisfied") is not bar:
            raise ValueError(f"metadata candidate bar mismatch: {name}")
        if row.get("disposition") != ("ADMIT" if local_safe else "HOLD"):
            raise ValueError(f"metadata disposition mismatch: {name}")
        local_admit += local_safe
        bar_count += bar
    counts = receipt.get("counts") or {}
    expected_counts = {
        "tools": len(manifest_rows),
        "authority_available": available_count,
        "local_metadata_admit": local_admit,
        "local_metadata_hold": len(manifest_rows) - local_admit,
        "candidate_metadata_bar_satisfied": bar_count,
    }
    if any(counts.get(key) != value for key, value in expected_counts.items()):
        raise ValueError("metadata aggregate mismatch")
    return rows


def operation_facts(row: dict[str, Any], tool: dict[str, Any]) -> dict[str, bool]:
    if row.get("distribution") != tool.get("distribution") or row.get(
        "locked_version"
    ) != tool.get("locked_version"):
        raise ValueError(f"operation identity mismatch: {tool.get('normalized_name')}")
    first = row.get("first") or {}
    payload = first.get("payload") or {}
    replay = row.get("replay") or {}
    replay_run = replay.get("run") or {}
    severance = row.get("severance") or {}
    severance_payload = severance.get("payload") or {}
    negative = payload.get("negative") or {}
    severed = severance_payload.get("severance") or {}
    expected_root = str(tool.get("import_names", [""])[0]).split(".")[0]
    derived = {
        "positive_api_operation": bool(
            first.get("returncode") == 0 and payload.get("positive", {}).get("passed") is True
        ),
        "reason_specific_negative": bool(
            first.get("returncode") == 0
            and negative.get("passed") is True
            and negative.get("contract_passed") is True
            and negative.get("reason_code") not in {None, "NEGATIVE_REASON_CONTRACT_MISSING"}
            and negative.get("broad_exception_contract") is False
        ),
        "boundary_observed": bool(
            first.get("returncode") == 0 and payload.get("boundary", {}).get("passed") is True
        ),
        "deterministic_replay": bool(
            first.get("returncode") == 0
            and replay_run.get("returncode") == 0
            and replay.get("equal") is True
            and replay.get("semantic_sha256_a")
            and replay.get("semantic_sha256_a") == replay.get("semantic_sha256_b")
        ),
        "import_severance_observed": bool(
            severance.get("returncode") == 0
            and severed.get("passed") is True
            and severed.get("reason_code") == "DECLARED_IMPORT_SEVERED"
            and severed.get("severed_root") == expected_root
        ),
        "bounded_reference_agreement": bool(
            first.get("returncode") == 0 and payload.get("reference", {}).get("passed") is True
        ),
        "probe_structure_non_vacuous": row.get("probe_structure_issues") == [],
    }
    if row.get("facts") != derived:
        raise ValueError(f"operation fact self-report mismatch: {tool.get('normalized_name')}")
    if row.get("disposition") != ("ADMIT" if all(derived.values()) else "HOLD"):
        raise ValueError(f"operation disposition mismatch: {tool.get('normalized_name')}")
    return derived


def validate_operation_receipt(
    receipt: dict[str, Any], manifest_rows: dict[str, dict[str, Any]], runtime_prefix: pathlib.Path
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, bool]]]:
    aware_timestamp(receipt, "operation receipt")
    if receipt.get("probe_source_sha256") != sha256_file(OPERATION_PROBE_SOURCE):
        raise ValueError("operation probe source drift")
    if pathlib.Path(str(receipt.get("sys_prefix", ""))).resolve() != runtime_prefix:
        raise ValueError("operation probes did not run in contained runtime")
    rows = by_name(
        list(receipt.get("tool_decisions") or []),
        "operation receipt",
        expected_count=len(manifest_rows),
    )
    if set(rows) != set(manifest_rows):
        raise ValueError("operation identities differ from manifest")
    facts = {
        name: operation_facts(row, manifest_rows[name]) for name, row in rows.items()
    }
    derived_counts = {
        "probed": len(manifest_rows),
        "admit": sum(all(values.values()) for values in facts.values()),
        "hold": sum(not all(values.values()) for values in facts.values()),
    }
    if receipt.get("counts") != derived_counts:
        raise ValueError("operation aggregate mismatch")
    return rows, facts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--contract", type=pathlib.Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--runtime-install", type=pathlib.Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--clean-install", type=pathlib.Path, default=DEFAULT_CLEAN)
    parser.add_argument("--operation", type=pathlib.Path, default=DEFAULT_OPERATION)
    parser.add_argument("--metadata", type=pathlib.Path, default=DEFAULT_METADATA)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    paths = {
        "manifest": args.manifest.resolve(),
        "contract": args.contract.resolve(),
        "runtime_install": args.runtime_install.resolve(),
        "clean_install": args.clean_install.resolve(),
        "operation": args.operation.resolve(),
        "metadata": args.metadata.resolve(),
    }
    manifest, contract = verify_manifest_and_contract(paths["manifest"], paths["contract"])
    manifest_identity = str(manifest["manifest_sha256"])
    expected_counts = dict(contract["expected_counts"])
    expected_roots = int(expected_counts["install_proposals"])
    expected_exclusions = int(expected_counts["preinstall_excluded"])
    manifest_rows = by_name(
        list(manifest["tools"]), "manifest", expected_count=expected_roots
    )
    runtime = require_receipt(
        paths["runtime_install"],
        schema="constraintbox.cb-light-install-probe.v1",
        manifest_identity=manifest_identity,
    )
    clean = require_receipt(
        paths["clean_install"],
        schema="constraintbox.cb-light-install-probe.v1",
        manifest_identity=manifest_identity,
    )
    operation = require_receipt(
        paths["operation"],
        schema="constraintbox.cb-light-tool-probes.v1",
        manifest_identity=manifest_identity,
    )
    metadata = require_receipt(
        paths["metadata"],
        schema="constraintbox.cb-light-metadata-probe.v1",
        manifest_identity=manifest_identity,
    )

    runtime_rows, runtime_closure, runtime_root_truth, runtime_install_facts = validate_install_receipt(
        runtime, role="runtime", manifest=manifest, manifest_rows=manifest_rows
    )
    clean_rows, clean_closure, clean_root_truth, clean_install_facts = validate_install_receipt(
        clean, role="clean", manifest=manifest, manifest_rows=manifest_rows
    )
    if (
        pathlib.Path(runtime_install_facts["install_report_path"]).resolve()
        == pathlib.Path(clean_install_facts["install_report_path"]).resolve()
    ):
        raise ValueError("runtime and clean install reports must use distinct paths")
    closure_agreement = runtime_closure == clean_closure
    metadata_rows = validate_metadata_receipt(metadata, manifest_rows)
    runtime_prefix = manifest_interpreter(manifest).parent.parent.resolve()
    operation_rows, operation_by_name = validate_operation_receipt(
        operation, manifest_rows, runtime_prefix
    )
    evidence_times = {
        "runtime_install": runtime_install_facts["observed_at"],
        "clean_install": clean_install_facts["observed_at"],
        "operation": aware_timestamp(operation, "operation receipt"),
        "metadata": aware_timestamp(metadata, "metadata receipt"),
    }
    evidence_skew_seconds = (
        max(evidence_times.values()) - min(evidence_times.values())
    ).total_seconds()
    maximum_skew_seconds = float(contract["evidence_max_skew_minutes"]) * 60
    if evidence_skew_seconds > maximum_skew_seconds:
        raise ValueError(
            f"input receipt skew exceeds contract: {evidence_skew_seconds:.1f}s"
        )
    observed_runtime, _ = live_runtime_inventory(runtime_prefix)
    observed_runtime_without_bootstrap = {
        name: version
        for name, version in observed_runtime.items()
        if name not in {"pip", "constraintbox"}
    }
    live_runtime_exact = observed_runtime_without_bootstrap == runtime_closure

    required = list(contract["usable_now_requires"])
    facts_by_tool: dict[str, dict[str, bool]] = {}
    for name, tool in manifest_rows.items():
        runtime_row = runtime_rows[name]
        clean_row = clean_rows[name]
        metadata_row = metadata_rows[name]
        py313 = metadata_row.get("predicates", {}).get("python_3_13_admitted")
        metadata_compatible = bool(
            metadata_row.get("local_metadata_safe") is True
            and (py313 is True or (py313 is None and clean_row.get("import_probe", {}).get("passed") is True))
        )
        facts = {
            "proposed_light_identity": tool.get("membership") == "PROPOSED_LIGHT",
            "role_declared": bool(str(tool.get("role", "")).strip()),
            "exact_root_pin_installed": bool(
                runtime_row.get("installed_version") == tool.get("locked_version")
                and clean_row.get("installed_version") == tool.get("locked_version")
            ),
            "declared_import_provider": bool(
                set(runtime_row.get("expected_provider_distributions") or [])
                == set(runtime_row.get("import_providers") or [])
                and set(clean_row.get("expected_provider_distributions") or [])
                == set(clean_row.get("import_providers") or [])
            ),
            "fresh_subprocess_import": bool(
                runtime_row.get("import_probe", {}).get("passed") is True
                and clean_row.get("import_probe", {}).get("passed") is True
            ),
            "clean_dependency_closure": bool(clean_root_truth[name]),
            "contained_environment_exact": bool(
                runtime_install_facts["environment_exact"]
                and clean_install_facts["environment_exact"]
                and live_runtime_exact
            ),
            "clean_runtime_closure_agreement": closure_agreement,
            "local_metadata_compatible": metadata_compatible,
            **operation_by_name[name],
            "cross_receipt_identity_bound": bool(
                runtime_root_truth[name] is bool(
                    runtime_row.get("root_install_constraints_satisfied")
                )
                and clean_root_truth[name] is bool(
                    clean_row.get("root_install_constraints_satisfied")
                )
                and runtime_row.get("distribution") == tool.get("distribution")
                and clean_row.get("distribution") == tool.get("distribution")
                and metadata_row.get("distribution") == tool.get("distribution")
                and operation_rows[name].get("distribution") == tool.get("distribution")
                and runtime_row.get("locked_version") == tool.get("locked_version")
                and clean_row.get("locked_version") == tool.get("locked_version")
                and metadata_row.get("locked_version") == tool.get("locked_version")
                and operation_rows[name].get("locked_version") == tool.get("locked_version")
                and runtime_row.get("import_name") == tool.get("import_names", [None])[0]
                and clean_row.get("import_name") == tool.get("import_names", [None])[0]
            ),
        }
        if set(facts) != set(required):
            raise ValueError(
                f"implemented constraint set differs from contract for {name}: "
                f"missing={sorted(set(required)-set(facts))}, extra={sorted(set(facts)-set(required))}"
            )
        if any(type(value) is not bool for value in facts.values()):
            raise ValueError(f"non-Boolean usable-now fact for {name}")
        facts_by_tool[name] = facts

    finite_decision = solve_selection(facts_by_tool, required)
    assignments = finite_decision.get("assignment") or {}
    deciders = finite_decision.get("deciders") or {}
    rows: list[dict[str, Any]] = []
    for name in sorted(manifest_rows):
        tool = manifest_rows[name]
        facts = facts_by_tool[name]
        votes = {
            decider_name: (decider.get("assignment") or {}).get(name)
            for decider_name, decider in deciders.items()
        }
        if not finite_decision.get("agree") or not finite_decision.get("unique_assignment"):
            disposition = "HOLD_DECIDER_DISAGREEMENT"
            reason_code = "FINITE_DECIDERS_NOT_IN_AGREEMENT"
        elif assignments.get(name) is True:
            disposition = "SELECTED_FOR_WORK"
            reason_code = "USABLE_NOW_CONSTRAINTS_SATISFIED"
        else:
            disposition = "HOLD_MISSING_EVIDENCE"
            reason_code = "USABLE_NOW_CONSTRAINTS_UNSAT"
        failed = sorted(key for key, value in facts.items() if not value)
        if votes and len(set(votes.values())) != 1:
            raise ValueError(f"row decider votes diverge: {name}")
        portable_missing = list(contract["portable_adoption_requires_in_addition"])
        rows.append(
            {
                "distribution": tool["distribution"],
                "normalized_name": name,
                "locked_version": tool["locked_version"],
                "role": tool["role"],
                "role_class": tool["role_class"],
                "source_group": tool["source_group"],
                "work_disposition": disposition,
                "reason_code": reason_code,
                "failed_usable_now_constraints": failed,
                "usable_now_facts": facts,
                "decider_votes": votes,
                "metadata_failed_predicates": metadata_rows[name].get("failed_predicates", []),
                "operation_control_issues": operation_rows[name].get("probe_structure_issues", []),
                "portable_adoption_disposition": "HOLD_NOT_ADOPTED",
                "portable_adoption_missing": portable_missing,
                "adopted": False,
            }
        )

    counts = {
        "evaluated_candidate_domain": expected_roots + expected_exclusions,
        "preinstall_excluded": len(manifest.get("preinstall_excluded_candidates") or []),
        "proposed": len(rows),
        "selected_for_work": sum(row["work_disposition"] == "SELECTED_FOR_WORK" for row in rows),
        "hold_missing_evidence": sum(row["work_disposition"] == "HOLD_MISSING_EVIDENCE" for row in rows),
        "hold_decider_disagreement": sum(
            row["work_disposition"] == "HOLD_DECIDER_DISAGREEMENT" for row in rows
        ),
        "selected_core": sum(
            row["work_disposition"] == "SELECTED_FOR_WORK" and row["source_group"] == "core"
            for row in rows
        ),
        "portable_adopted": 0,
    }
    accounted = (
        counts["selected_for_work"]
        + counts["hold_missing_evidence"]
        + counts["hold_decider_disagreement"]
    )
    evaluation_complete = bool(
        counts["proposed"] == expected_roots
        and counts["preinstall_excluded"] == expected_exclusions
        and accounted == expected_roots
        and counts["hold_decider_disagreement"] == 0
        and finite_decision.get("agree") is True
        and finite_decision.get("unique_assignment") is True
    )
    core_names = {
        name for name, row in manifest_rows.items() if row.get("source_group") == "core"
    }
    runtime_ready = bool(
        evaluation_complete
        and counts["selected_for_work"] > 0
        and all(assignments.get(name) is True for name in core_names)
    )
    receipt = {
        "schema": "constraintbox.cb-light-selection.v1",
        "profile": "cb_light",
        "evaluated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "manifest_identity_sha256": manifest_identity,
        "contract": {
            "path": str(paths["contract"]),
            "sha256": sha256_file(paths["contract"]),
        },
        "input_receipts": {
            name: {"path": str(path), "sha256": sha256_file(path)}
            for name, path in paths.items()
            if name not in {"contract"}
        },
        "probe_sources": {
            "install": {"path": str(INSTALL_PROBE_SOURCE), "sha256": sha256_file(INSTALL_PROBE_SOURCE)},
            "metadata": {"path": str(METADATA_PROBE_SOURCE), "sha256": sha256_file(METADATA_PROBE_SOURCE)},
            "operation": {"path": str(OPERATION_PROBE_SOURCE), "sha256": sha256_file(OPERATION_PROBE_SOURCE)},
        },
        "finite_selection_decision": finite_decision,
        "finite_selection_interpretation": (
            "Z3, cvc5, and enumeration are deterministic backend evaluations of "
            "the same fully specified Boolean law; agreement cross-checks the solver "
            "implementation but is not independent fact validation"
        ),
        "evidence_time_coherence": {
            "passed": True,
            "maximum_skew_minutes": contract["evidence_max_skew_minutes"],
            "observed_skew_seconds": evidence_skew_seconds,
            "timestamps": {
                name: value.isoformat() for name, value in evidence_times.items()
            },
        },
        "install_environment_separation": {
            "passed": True,
            "runtime_report_path": str(runtime_install_facts["install_report_path"]),
            "clean_report_path": str(clean_install_facts["install_report_path"]),
            "byte_identity_permitted": (
                "both independent environments may resolve the same deterministic artifacts"
            ),
        },
        "closure_agreement": {
            "passed": closure_agreement,
            "runtime_inventory_sha256": runtime.get("runtime_inventory_sha256"),
            "clean_inventory_sha256": clean.get("runtime_inventory_sha256"),
            "selector_live_runtime_exact": live_runtime_exact,
        },
        "counts": counts,
        "preinstall_excluded_candidates": manifest.get("preinstall_excluded_candidates"),
        "selected_tools": [
            row["distribution"] for row in rows if row["work_disposition"] == "SELECTED_FOR_WORK"
        ],
        "held_tools": [
            {
                "distribution": row["distribution"],
                "reason_code": row["reason_code"],
                "failed_constraints": row["failed_usable_now_constraints"],
                "control_issues": row["operation_control_issues"],
            }
            for row in rows
            if row["work_disposition"] != "SELECTED_FOR_WORK"
        ],
        "rows": rows,
        "evaluation_complete": evaluation_complete,
        "runtime_ready": runtime_ready,
        "all_proposed_selected": counts["selected_for_work"] == expected_roots,
        # This is deliberately a *scoped evaluation* result, not a system
        # completion transition.  The selector has no authority to establish
        # portability, a real downstream consumer, owner adoption, a CB Heavy
        # setup/bridge, promotion, or release.  Keeping the generic completion
        # bit false prevents an exhaustive local bookkeeping pass from
        # collapsing those separate lifecycle states into one green label.
        "evaluation_allowed": runtime_ready,
        "completion_allowed": False,
        "system_completion_reason": (
            "SELECTION_IS_LOCAL_CB_LIGHT_EVALUATION_ONLY"
        ),
        "promotion_allowed": False,
        "claim_ceiling": (
            "complete local evaluation and bounded current-work selection in the contained "
            "macOS/arm64 Python 3.13 runtime only; held rows remain held, and portable adoption, "
            "production integration, CB Heavy, simulation, promotion, and release remain false"
        ),
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        print(
            f"CB Light selection: {counts['selected_for_work']} SELECTED_FOR_WORK, "
            f"{counts['hold_missing_evidence']} HOLD_MISSING_EVIDENCE, "
            f"{counts['hold_decider_disagreement']} HOLD_DECIDER_DISAGREEMENT"
        )
        for row in receipt["held_tools"]:
            print(
                f"  HOLD {row['distribution']}: "
                f"{', '.join(row['failed_constraints']) or row['reason_code']}"
            )
    return 0 if evaluation_complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
