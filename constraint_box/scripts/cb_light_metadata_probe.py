#!/usr/bin/env python3
"""Observe live PyPI facts for every row in the 91-tool CB Light manifest."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config/cb_light_tools_v1.json"
DEFAULT_OUTPUT = ROOT / "receipts/cb_light_metadata_v1.json"
USER_AGENT = "constraintbox-cb-light/1 (+finite metadata probe)"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def load_manifest(path: pathlib.Path) -> dict[str, Any]:
    body = json.loads(path.read_text(encoding="utf-8"))
    identity = dict(body)
    claimed = identity.pop("manifest_sha256", None)
    observed = hashlib.sha256(canonical_json(identity)).hexdigest()
    if body.get("schema") != "constraintbox.cb-light-tool-manifest.v1" or claimed != observed:
        raise ValueError("invalid or tampered CB Light manifest")
    if len(body.get("tools", [])) != 91:
        raise ValueError("CB Light manifest must contain exactly 91 rows")
    return body


def fetch_json(
    name: str, version: str, timeout: float
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    encoded = urllib.parse.quote(name, safe="")
    encoded_version = urllib.parse.quote(version, safe="")
    url = f"https://pypi.org/pypi/{encoded}/{encoded_version}/json"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    retrieved = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        return None, {
            "url": url,
            "retrieved_at": retrieved,
            "error": "HTTPError",
            "http_status": exc.code,
            "detail": str(exc)[:300],
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, {
            "url": url,
            "retrieved_at": retrieved,
            "error": type(exc).__name__,
            "detail": str(exc)[:300],
        }
    try:
        data = json.loads(raw)
    except ValueError as exc:
        return None, {
            "url": url,
            "retrieved_at": retrieved,
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "error": "MalformedJSON",
            "detail": str(exc)[:300],
        }
    return data, {
        "url": url,
        "retrieved_at": retrieved,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "response_bytes": len(raw),
    }


def admits_python(specifier: str | None, version: str) -> bool | None:
    if not specifier:
        return None
    try:
        return SpecifierSet(specifier).contains(version, prereleases=True)
    except Exception:
        return None


def runtime_dependencies(raw_requirements: list[str] | None) -> list[str]:
    environment = default_environment()
    environment["extra"] = ""
    names: set[str] = set()
    for raw in raw_requirements or []:
        try:
            requirement = Requirement(raw)
        except Exception:
            continue
        marker = requirement.marker
        if marker is not None:
            try:
                active = marker.evaluate(environment)
            except Exception:
                active = False
            if not active:
                continue
        names.add(requirement.name)
    return sorted(names, key=str.lower)


def platform_facts(files: list[dict[str, Any]]) -> dict[str, Any]:
    wheels = [row for row in files if row.get("packagetype") == "bdist_wheel"]
    names = [str(row.get("filename", "")).lower() for row in wheels]
    pure = any("-none-any.whl" in name for name in names)
    platforms = {
        "linux": pure or any("manylinux" in name or "musllinux" in name for name in names),
        "macos": pure or any("macosx" in name for name in names),
        "windows": pure or any("-win32.whl" in name or "-win_amd64.whl" in name or "-win_arm64.whl" in name for name in names),
    }
    return {
        "pure_python_wheel": pure,
        "platform_wheel_available": platforms,
        "all_required_platforms_have_wheel": all(platforms.values()),
        "wheel_count": len(wheels),
        "largest_wheel_bytes": max((int(row.get("size") or 0) for row in wheels), default=None),
        "wheel_filenames": sorted(str(row.get("filename")) for row in wheels),
        "wheel_sha256": {
            str(row.get("filename")): (row.get("digests") or {}).get("sha256")
            for row in wheels
        },
    }


def observe(tool: dict[str, Any], timeout: float, today: dt.date) -> dict[str, Any]:
    data, retrieval = fetch_json(
        str(tool["distribution"]), str(tool["locked_version"]), timeout
    )
    base = {
        "distribution": tool["distribution"],
        "normalized_name": tool["normalized_name"],
        "locked_version": tool["locked_version"],
        "source_group": tool["source_group"],
        "authority": retrieval,
    }
    if data is None:
        return {
            **base,
            "disposition": "HOLD",
            "reason_code": (
                "PINNED_RELEASE_NOT_FOUND"
                if retrieval.get("http_status") == 404
                else "PYPI_AUTHORITY_UNAVAILABLE"
            ),
            "predicates": {},
            "failed_predicates": ["authority_available"],
        }

    info = data.get("info") or {}
    observed_version = str(info.get("version") or "")
    locked_files = list(data.get("urls") or [])
    uploads = sorted(
        str(row.get("upload_time_iso_8601"))
        for row in locked_files
        if row.get("upload_time_iso_8601")
    )
    release_date = dt.date.fromisoformat(uploads[0][:10]) if uploads else None
    age_days = (today - release_date).days if release_date else None
    requires_python = info.get("requires_python")
    dependencies = runtime_dependencies(info.get("requires_dist"))
    platforms = platform_facts(locked_files)
    vulnerabilities = list(data.get("vulnerabilities") or [])
    vulnerability_rows = sorted(
        [
            {
                "id": row.get("id"),
                "aliases": sorted(row.get("aliases") or []),
                "fixed_in": sorted(row.get("fixed_in") or []),
            }
            for row in vulnerabilities
        ],
        key=lambda row: str(row.get("id")),
    )
    predicates: dict[str, bool | None] = {
        "locked_release_exists": bool(
            locked_files and observed_version == str(tool["locked_version"])
        ),
        "release_within_548_days": age_days is not None and age_days <= 548,
        "pinned_release_not_yanked": bool(locked_files)
        and not any(bool(row.get("yanked")) for row in locked_files),
        "requires_python_declared": bool(requires_python),
        "python_3_12_admitted": admits_python(requires_python, "3.12"),
        "python_3_13_admitted": admits_python(requires_python, "3.13"),
        "no_known_vulnerabilities": not vulnerability_rows,
        "linux_macos_windows_wheels": platforms["all_required_platforms_have_wheel"],
        "declared_runtime_deps_at_most_3": len(dependencies) <= 3,
        "largest_wheel_at_most_5mib": (
            platforms["largest_wheel_bytes"] is not None
            and platforms["largest_wheel_bytes"] <= 5 * 1024 * 1024
        ),
        "wheel_hashes_present": bool(platforms["wheel_sha256"])
        and all(bool(value) for value in platforms["wheel_sha256"].values()),
    }
    local_names = {
        "locked_release_exists",
        "pinned_release_not_yanked",
        "no_known_vulnerabilities",
    }
    local_metadata_safe = all(predicates[name] is True for name in local_names) and predicates[
        "python_3_13_admitted"
    ] is not False
    metadata_bar_satisfied = all(value is True for value in predicates.values())
    return {
        **base,
        "observed_pinned_version": observed_version,
        "release_artifacts": sorted(
            [
                {
                    "filename": row.get("filename"),
                    "packagetype": row.get("packagetype"),
                    "size": int(row.get("size") or 0),
                    "sha256": (row.get("digests") or {}).get("sha256"),
                    "upload_time_iso_8601": row.get("upload_time_iso_8601"),
                    "yanked": bool(row.get("yanked")),
                }
                for row in locked_files
            ],
            key=lambda row: str(row.get("filename")),
        ),
        "release_date": release_date.isoformat() if release_date else None,
        "age_days": age_days,
        "requires_python": requires_python,
        "requires_dist": list(info.get("requires_dist") or []),
        "marker_environment": default_environment(),
        "runtime_dependencies": dependencies,
        "declared_runtime_dependency_count": len(dependencies),
        "platforms": platforms,
        "vulnerabilities": vulnerability_rows,
        "known_vulnerability_count": len(vulnerability_rows),
        "license": {
            "license_expression": info.get("license_expression"),
            "license": info.get("license"),
            "classifiers": sorted(
                value
                for value in info.get("classifiers") or []
                if str(value).startswith("License ::")
            ),
        },
        "predicates": predicates,
        "local_metadata_safe": local_metadata_safe,
        "candidate_metadata_bar_satisfied": metadata_bar_satisfied,
        "failed_predicates": sorted(name for name, value in predicates.items() if value is not True),
        "disposition": "ADMIT" if local_metadata_safe else "HOLD",
        "reason_code": (
            "PINNED_METADATA_LOCAL_SAFETY_SATISFIED"
            if local_metadata_safe
            else "PINNED_METADATA_LOCAL_SAFETY_INCOMPLETE"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--jobs", type=int, default=16)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    manifest = load_manifest(manifest_path)
    today = dt.datetime.now(dt.timezone.utc).date()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        rows = list(pool.map(lambda tool: observe(tool, args.timeout, today), manifest["tools"]))
    rows.sort(key=lambda row: row["normalized_name"])
    counts = {
        "tools": len(rows),
        "authority_available": sum(not row["authority"].get("error") for row in rows),
        "local_metadata_admit": sum(row["disposition"] == "ADMIT" for row in rows),
        "local_metadata_hold": sum(row["disposition"] == "HOLD" for row in rows),
        "candidate_metadata_bar_satisfied": sum(
            row.get("candidate_metadata_bar_satisfied") is True for row in rows
        ),
    }
    receipt = {
        "schema": "constraintbox.cb-light-metadata-probe.v1",
        "profile": "cb_light",
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authority": "https://pypi.org/pypi/{distribution}/{locked_version}/json",
        "manifest_identity_sha256": manifest["manifest_sha256"],
        "probe_source_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        "counts": counts,
        "rows": rows,
        "promotion_allowed": False,
        "claim_ceiling": (
            "pinned PyPI release, Python, wheel, vulnerability, license, hash, and "
            "declared-dependency metadata only; "
            "no install, operation, production integration, adoption, or release claim"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        print(
            f"CB Light pinned metadata: {counts['local_metadata_admit']} ADMIT, "
            f"{counts['local_metadata_hold']} HOLD; full candidate bar "
            f"{counts['candidate_metadata_bar_satisfied']}/91"
        )
        for row in rows:
            if row["disposition"] == "HOLD":
                print(f"  HOLD {row['distribution']}: {', '.join(row['failed_predicates'])}")
        print(f"receipt: {args.output}")
    return 0 if counts["authority_available"] == 91 else 1


if __name__ == "__main__":
    raise SystemExit(main())
