#!/usr/bin/env python3
"""Build the single authoritative 91-row CB Light proposal manifest.

The output is a finite proposal domain.  It is not an adoption list.  The
three human-readable requirement surfaces remain pip inputs; this compiler
reconciles them with the exact macOS/Python 3.13 root lock and refuses drift.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

IMPORT_OVERRIDES = {
    "annotated-types": "annotated_types",
    "argon2-cffi": "argon2",
    "ast-comments": "ast_comments",
    "beautifulsoup4": "bs4",
    "charset-normalizer": "charset_normalizer",
    "dirty-equals": "dirty_equals",
    "email-validator": "email_validator",
    "flake8-simplify": "flake8_simplify",
    "gitpython": "git",
    "markdown-it-py": "markdown_it",
    "more-itertools": "more_itertools",
    "patch-ng": "patch_ng",
    "protobuf": "google.protobuf",
    "pyjwt": "jwt",
    "pytest-benchmark": "pytest_benchmark",
    "pytest-randomly": "pytest_randomly",
    "pytest-timeout": "pytest_timeout",
    "pytest-xdist": "xdist",
    "python-levenshtein": "Levenshtein",
    "python-ulid": "ulid",
    "ruamel-yaml": "ruamel.yaml",
    "typing-extensions": "typing_extensions",
    "unidecode": "unidecode",
    "vcrpy": "vcr",
    "z3-solver": "z3",
}

PROVIDER_OVERRIDES = {
    # python-Levenshtein is intentionally a meta-distribution.  Its exact
    # Levenshtein dependency supplies the import package.
    "python-levenshtein": ["Levenshtein"],
}

PASSING_ROLE_CLASS = {
    "blake3": "hash_integrity",
    "charset-normalizer": "text_drift",
    "fasteners": "concurrency_control",
    "grimp": "static_audit",
    "packaging": "package_semantics",
    "patch-ng": "mutation_tool",
    "platformdirs": "portability",
    "plumbum": "subprocess_control",
    "stamina": "bounded_retry",
    "structlog": "audit_telemetry",
    "xxhash": "hash_integrity",
}


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_name(spec: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9_.-]*)", spec)
    if not match:
        raise ValueError(f"cannot parse requirement: {spec!r}")
    return match.group(1)


def parse_requirement_file(path: Path, group: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    category = group
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        header = re.match(r"#\s*---\s*(.*?)\s*---", stripped)
        if header:
            category = header.group(1)
            continue
        if not stripped or stripped.startswith("#"):
            continue
        requirement, _, comment = stripped.partition("#")
        name = requirement_name(requirement)
        rows.append(
            {
                "distribution": name,
                "normalized_name": normalize(name),
                "declared_requirement": requirement.strip(),
                "role": comment.strip(),
                "role_class": (
                    PASSING_ROLE_CLASS.get(normalize(name), group)
                    if group == "candidate_passing"
                    else category
                ),
                "source_group": group,
                "source_line": str(line_number),
            }
        )
    return rows


def parse_lock(path: Path) -> dict[str, tuple[str, str]]:
    pins: dict[str, tuple[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        name, separator, version = stripped.partition("==")
        if (
            separator != "=="
            or not version
            or any(character.isspace() for character in version)
            or "#" in version
            or "--hash" in version
        ):
            raise ValueError(f"root lock line is not exact: {line!r}")
        key = normalize(name)
        if key in pins:
            raise ValueError(f"duplicate root lock row: {name}")
        pins[key] = (name, version)
    return pins


def parse_excluded_candidates(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            if current is not None and stripped.upper().startswith("#   BAR:"):
                current["failed_bar"] = stripped.split(":", 1)[1].strip()
            continue
        requirement, _, comment = stripped.partition("#")
        name = requirement_name(requirement)
        current = {
            "distribution": name,
            "normalized_name": normalize(name),
            "declared_requirement": requirement.strip(),
            "role": comment.strip(),
            "source_line": line_number,
            "disposition": "EXCLUDED_BEFORE_INSTALL",
            "reason_code": "CANDIDATE_METADATA_BAR_FAILED",
            "failed_bar": None,
        }
        rows.append(current)
    return rows


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contained_package_source_paths(root: Path) -> set[str]:
    """Return every source/resource file that setuptools can ship as Light.

    The contract may be intentionally expanded, but it cannot silently omit a
    new module that the wheel builder would include.  This is a source-domain
    guard, not a broad scan of the root legacy package or any CB Heavy tree.
    """

    source_root = root / "light_runtime" / "src"
    paths: set[str] = set()
    for package_name in ("constraintbox", "hookkernel"):
        package = source_root / package_name
        if not package.is_dir():
            raise ValueError(f"contained Light package missing: {package_name}")
        for path in sorted(package.rglob("*")):
            if (
                not path.is_file()
                or "__pycache__" in path.parts
                or path.suffix in {".pyc", ".pyo"}
            ):
                continue
            paths.add(path.relative_to(root).as_posix())
    return paths


def build(root: Path) -> dict[str, object]:
    # The CB Light controller has its own package.  The repo-root project is
    # the legacy mixed estate and must not define Light's direct dependencies.
    pyproject_path = root / "light_runtime/pyproject.toml"
    extended_path = root / "requirements/candidates/cb-light-extended.in"
    passing_path = root / "requirements/candidates/cb-candidates-passing.in"
    failing_path = root / "requirements/candidates/cb-candidates-failing.in"
    lock_path = root / "requirements/locks/constraintbox-py313-macos-estate.lock"
    registry_path = root / "config/core_tool_registry_v9.json"
    contract_path = root / "config/cb_light_contract_v1.json"

    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    selection_contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if selection_contract.get("schema") != "constraintbox.cb-light-contract.v1":
        raise ValueError("invalid CB Light contract schema")
    expected_counts = selection_contract.get("expected_counts")
    if not isinstance(expected_counts, dict):
        raise ValueError("CB Light contract expected_counts missing")
    expected_proposals = int(expected_counts.get("install_proposals", -1))
    expected_exclusions = int(expected_counts.get("preinstall_excluded", -1))
    core_by_distribution = {
        normalize(row["distribution"]): row for row in registry["tools"]
    }
    rows: list[dict[str, object]] = []
    for spec in pyproject["project"]["dependencies"]:
        name = requirement_name(spec)
        key = normalize(name)
        core_contract = core_by_distribution.get(key)
        if core_contract is None:
            raise ValueError(f"declared core lacks a core contract: {name}")
        rows.append(
            {
                "distribution": name,
                "normalized_name": key,
                "declared_requirement": spec,
                "role": "; ".join(core_contract.get("cb_roles", [])),
                "role_class": "core_deterministic_runtime",
                "source_group": "core",
                "source_line": "project.dependencies",
                "core_contract_id": core_contract["id"],
            }
        )
    rows.extend(parse_requirement_file(extended_path, "extended"))
    rows.extend(parse_requirement_file(passing_path, "candidate_passing"))

    keys = [str(row["normalized_name"]) for row in rows]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise ValueError(f"proposal groups overlap: {duplicates}")
    if len(rows) != expected_proposals:
        raise ValueError(
            f"expected {expected_proposals} proposed roots, observed {len(rows)}"
        )
    expected_names = set(selection_contract.get("install_proposal_names") or [])
    if set(keys) != expected_names:
        raise ValueError(
            "proposal membership differs from contained contract: "
            f"missing={sorted(expected_names - set(keys))}, "
            f"extra={sorted(set(keys) - expected_names)}"
        )

    excluded_candidates = parse_excluded_candidates(failing_path)
    excluded_names = {str(row["normalized_name"]) for row in excluded_candidates}
    expected_excluded = set(
        selection_contract.get("preinstall_excluded_names") or []
    )
    if excluded_names != expected_excluded:
        raise ValueError(
            "excluded candidate membership differs from contained contract: "
            f"missing={sorted(expected_excluded - excluded_names)}, "
            f"extra={sorted(excluded_names - expected_excluded)}"
        )
    if any(row.get("failed_bar") is None for row in excluded_candidates):
        raise ValueError("every preinstall exclusion must state the failed bar")
    if len(excluded_candidates) != expected_exclusions:
        raise ValueError(
            f"expected {expected_exclusions} preinstall exclusions, "
            f"observed {len(excluded_candidates)}"
        )

    pins = parse_lock(lock_path)
    if set(keys) != set(pins):
        raise ValueError(
            "root lock/domain mismatch: "
            f"missing={sorted(set(keys) - set(pins))}, "
            f"extra={sorted(set(pins) - set(keys))}"
        )

    for row in rows:
        key = str(row["normalized_name"])
        locked_name, version = pins[key]
        import_name = IMPORT_OVERRIDES.get(key, key.replace("-", "_"))
        row.update(
            {
                "locked_distribution": locked_name,
                "locked_version": version,
                "import_names": [import_name],
                "expected_provider_distributions": PROVIDER_OVERRIDES.get(
                    key, [locked_name]
                ),
                "membership": "PROPOSED_LIGHT",
                "identity_scope": (
                    "controller_runtime_candidate"
                    if row["source_group"] == "core"
                    else "supporting_probe_or_engineering_candidate"
                ),
                "runtime_identity_authority": row["source_group"] == "core",
                "adopted": False,
            }
        )

    rows.sort(key=lambda row: str(row["normalized_name"]))
    source_relatives = selection_contract.get("required_source_paths")
    if (
        not isinstance(source_relatives, list)
        or not source_relatives
        or len(source_relatives) != len(set(source_relatives))
        or any(not isinstance(relative, str) for relative in source_relatives)
    ):
        raise ValueError("contract required_source_paths must be a nonempty unique list")
    declared_package_sources = {
        relative
        for relative in source_relatives
        if relative.startswith("light_runtime/src/")
    }
    observed_package_sources = contained_package_source_paths(root)
    if declared_package_sources != observed_package_sources:
        raise ValueError(
            "contained Light package source set differs from contract: "
            f"missing={sorted(observed_package_sources - declared_package_sources)}, "
            f"extra={sorted(declared_package_sources - observed_package_sources)}"
        )
    source_hashes = {}
    for relative in source_relatives:
        path = root / relative
        if not path.is_file():
            raise ValueError(f"required contained CB Light source missing: {relative}")
        source_hashes[relative] = sha256(path)
    body: dict[str, object] = {
        "schema": "constraintbox.cb-light-tool-manifest.v1",
        "profile": "cb_light",
        "membership_authority": "config/cb_light_contract_v1.json",
        # A Light manifest must not name a shared Ratchet or Heavy runtime as
        # its bootstrap.  The contained venv is both the launcher target and
        # the runtime observed by the admission predicates.
        "bootstrap_interpreter": ".venv/bin/python",
        # Preserve the contained interpreter path itself.  Resolving the final
        # symlink would collapse a venv back onto its Homebrew base executable
        # after the venv exists and would make the manifest depend on build time.
        "mandated_interpreter": ".venv/bin/python",
        "runtime_environment": ".venv",
        "supported_current_execution": {
            "python": "3.13",
            "os": "macos",
            "architecture": "arm64",
        },
        "set_separation": {
            "proposed_roots": expected_proposals,
            "installed_environment": "contained .venv observed separately at runtime",
            "transitive_closure": "observed separately at runtime",
            "import_providers": "observed separately at runtime",
            "sim_engine_members": 0,
        },
        "role_layers": {
            "controller_runtime_candidates": sum(
                row["runtime_identity_authority"] is True for row in rows
            ),
            "supporting_probe_or_engineering_candidates": sum(
                row["runtime_identity_authority"] is False for row in rows
            ),
            "rule": (
                "supporting build, test, audit, and probe tools do not become "
                "CB Light runtime identity merely by being installed or selected"
            ),
        },
        "constraints": {
            "usable_now_requires": list(selection_contract["usable_now_requires"]),
            "portable_adoption_requires_in_addition": list(
                selection_contract["portable_adoption_requires_in_addition"]
            ),
            "candidate_metadata_bar": {
                "stale_days_max": 548,
                "max_declared_runtime_deps": 3,
                "max_wheel_bytes": 5242880,
                "applies_to": "non-core candidate discovery; core role exceptions remain explicit",
            },
        },
        "source_hashes": source_hashes,
        "counts": {
            "tools": len(rows),
            "core": sum(row["source_group"] == "core" for row in rows),
            "extended": sum(row["source_group"] == "extended" for row in rows),
            "candidate_passing": sum(
                row["source_group"] == "candidate_passing" for row in rows
            ),
            "preinstall_excluded": len(excluded_candidates),
            "evaluated_candidate_domain": len(rows) + len(excluded_candidates),
        },
        "tools": rows,
        "preinstall_excluded_candidates": sorted(
            excluded_candidates, key=lambda row: str(row["normalized_name"])
        ),
        "promotion_allowed": False,
        "claim_ceiling": (
            f"{expected_proposals}-row CB Light proposal identity only; no install, "
            "operation, adoption, CB Heavy, simulation, promotion, or release claim"
        ),
    }
    derived_counts = body["counts"]
    expected_derived = {
        "tools": expected_proposals,
        "core": int(expected_counts.get("core", -1)),
        "extended": int(expected_counts.get("extended", -1)),
        "candidate_passing": int(expected_counts.get("candidate_passing", -1)),
        "preinstall_excluded": expected_exclusions,
        "evaluated_candidate_domain": expected_proposals + expected_exclusions,
    }
    if derived_counts != expected_derived:
        raise ValueError(
            f"derived manifest counts differ from contract: "
            f"derived={derived_counts}, expected={expected_derived}"
        )
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    body["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    body = build(args.root.resolve())
    rendered = json.dumps(body, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
