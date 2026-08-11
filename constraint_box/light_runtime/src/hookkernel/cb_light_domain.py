"""Compile the CB Light proposal domain without consulting ambient membership.

The proposal domain and the observed interpreter are deliberately separate.
Installed distributions never become candidates merely because they are present.
Locks, sim profiles, system_v5, Heavy engines, build products, and receipts are
not candidate sources.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import re
import sys
import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
# CB Light's proposal-domain inputs must travel with the installed
# ``hookkernel`` package.  They are a byte-for-byte bundle of the declared
# project sources, checked by tests so the bundle cannot silently drift.
DATA_ROOT = Path(__file__).resolve().parent / "cb_light_data"
POLICY = DATA_ROOT / "config" / "cb_light_domain_policy_v1.json"
_PEP503 = re.compile(r"[-_.]+")
_REQ_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9_.-]*)")
_MARKDOWN_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|(.*)$")


class DomainError(RuntimeError):
    """The proposal domain cannot be reproduced from its declared sources."""


def _logical_path(path: Path) -> str:
    """Return the stable project-relative identity for a bundled source."""

    resolved = path.resolve()
    try:
        return resolved.relative_to(DATA_ROOT.resolve()).as_posix()
    except ValueError:
        if resolved == Path(__file__).resolve():
            return "hookkernel/cb_light_domain.py"
        return resolved.relative_to(ROOT.resolve()).as_posix()


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalize_distribution(name: str) -> str:
    normalized = _PEP503.sub("-", name.strip()).lower()
    if not normalized or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", normalized):
        raise DomainError(f"invalid distribution name: {name!r}")
    return normalized


def _clean_markdown_name(value: str) -> str:
    return re.sub(r"[*~`]", "", value).strip()


def _requirement_name(value: str) -> str | None:
    match = _REQ_NAME.match(value)
    return normalize_distribution(match.group(1)) if match else None


def _source(
    source_id: str,
    path: Path,
    *,
    line: int | None = None,
    bucket: str | None = None,
    authority: str,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "source_id": source_id,
        "path": _logical_path(path),
        "authority": authority,
    }
    if line is not None:
        record["line"] = line
    if bucket is not None:
        record["bucket"] = bucket
    return record


def _new_distribution(name: str) -> dict[str, Any]:
    normalized = normalize_distribution(name)
    return {
        "candidate_id": f"pypi:{normalized}",
        "kind": "distribution",
        "normalized_name": normalized,
        "display_names": [],
        "provenance": [],
        "role_claims": [],
        "import_names": [],
        "core_contract": None,
        "registry_metadata": None,
        "declarations": {
            "pyproject_direct": False,
            "pyproject_direct_requirement": None,
            "pyproject_optional_groups": [],
            "candidate_requirement_buckets": [],
            "historical_proposal": False,
            "registry_candidate": False,
        },
    }


def _entry(rows: dict[tuple[str, str], dict[str, Any]], name: str) -> dict[str, Any]:
    normalized = normalize_distribution(name)
    key = ("distribution", normalized)
    if key not in rows:
        rows[key] = _new_distribution(name)
    entry = rows[key]
    if name not in entry["display_names"]:
        entry["display_names"].append(name)
    return entry


def _append_unique(target: list[Any], value: Any) -> None:
    if value not in target:
        target.append(value)


def _metadata_predicates(
    verified: Mapping[str, Any], policy: Mapping[str, Any]
) -> dict[str, bool | None]:
    required_platforms = set(policy["platforms_required"])
    platforms_text = str(verified.get("platforms") or "").lower()
    platform_tokens = {
        token.strip() for token in platforms_text.split(",") if token.strip()
    }
    if bool(verified.get("pure_python")) or platforms_text == "pure(all)":
        platforms_ok: bool | None = True
    elif platforms_text:
        platforms_ok = required_platforms.issubset(platform_tokens)
    else:
        platforms_ok = None

    days = verified.get("days_since_release")
    wheel = verified.get("largest_wheel_bytes")
    deps = verified.get("declared_runtime_deps")
    predicates: dict[str, bool | None] = {
        "release_within_bar": (
            int(days) <= int(policy["stale_days_max"])
            if isinstance(days, int)
            else None
        ),
        "requires_python_declared": (
            bool(verified.get("requires_python"))
            if "requires_python" in verified
            else None
        ),
        "python_3_12_admitted": (
            bool(verified["admits_3_12"])
            if "admits_3_12" in verified
            else None
        ),
        "python_3_13_admitted": (
            bool(verified["admits_3_13"])
            if "admits_3_13" in verified
            else None
        ),
        "platform_set_admitted": platforms_ok,
        "wheel_within_bar": (
            int(wheel) <= int(policy["max_wheel_bytes"])
            if isinstance(wheel, int)
            else None
        ),
        "runtime_deps_within_bar": (
            int(deps) <= int(policy["max_declared_runtime_deps"])
            if isinstance(deps, int)
            else None
        ),
        # The v1 registry does not record this fact. Absence is an open basin,
        # not permission to convert the registry's old `keep` label to ADMIT.
        "current_release_not_yanked": (
            not bool(verified["yanked"]) if "yanked" in verified else None
        ),
    }
    return predicates


def _load_registry(
    rows: dict[tuple[str, str], dict[str, Any]], policy: Mapping[str, Any]
) -> None:
    path = DATA_ROOT / "config" / "cb_light_library_candidates.json"
    body = json.loads(path.read_text(encoding="utf-8"))
    candidates = body.get("candidates")
    if not isinstance(candidates, list):
        raise DomainError("candidate registry has no candidates list")
    for index, candidate in enumerate(candidates, start=1):
        name = candidate.get("pypi_name")
        if not isinstance(name, str):
            raise DomainError(f"candidate registry row {index} has no pypi_name")
        entry = _entry(rows, name)
        entry["declarations"]["registry_candidate"] = True
        entry["provenance"].append(
            _source(
                "verified_candidate_registry",
                path,
                bucket="candidate",
                authority="proposal_and_pypi_metadata_only",
            )
        )
        for role in [candidate.get("cb_job"), candidate.get("category")]:
            if isinstance(role, str) and role.strip():
                _append_unique(entry["role_claims"], role.strip())
        for role in candidate.get("also_categories", []):
            if isinstance(role, str) and role.strip():
                _append_unique(entry["role_claims"], role.strip())
        verified = candidate.get("verified")
        if not isinstance(verified, dict):
            verified = {}
        predicates = _metadata_predicates(verified, policy["metadata_constraints"])
        observed_expected = (
            "drop"
            if any(value is False for value in predicates.values())
            else (
                "keep"
                if predicates and all(value is True for value in predicates.values())
                else None
            )
        )
        entry["registry_metadata"] = {
            "registry_verdict": verified.get("verdict"),
            "observed_predicate_verdict": observed_expected,
            "verdict_consistent": (
                verified.get("verdict") == observed_expected
                if observed_expected is not None
                else None
            ),
            "drop_reasons": list(verified.get("drop_reasons") or []),
            "latest_version": verified.get("latest_version"),
            "release_date": verified.get("release_date"),
            "requires_python": verified.get("requires_python"),
            "platforms": verified.get("platforms"),
            "pure_python": verified.get("pure_python"),
            "largest_wheel_bytes": verified.get("largest_wheel_bytes"),
            "declared_runtime_deps": verified.get("declared_runtime_deps"),
            "functional_test_passed": bool(
                verified.get("functional_test_passed", False)
            ),
            "predicates": predicates,
        }


def _load_historical(rows: dict[tuple[str, str], dict[str, Any]]) -> None:
    path = DATA_ROOT / "docs" / "CB_LIGHT_LIBRARY_LIST_20260807.md"
    text = path.read_text(encoding="utf-8")
    before_stdlib = text.split("## STDLIB TIER", 1)[0]
    for line_number, line in enumerate(before_stdlib.splitlines(), start=1):
        match = _MARKDOWN_ROW.match(line)
        if not match:
            continue
        name = _clean_markdown_name(match.group(2))
        cells = [cell.strip() for cell in match.group(3).split("|")]
        if not name or not cells:
            continue
        entry = _entry(rows, name)
        entry["declarations"]["historical_proposal"] = True
        entry["provenance"].append(
            _source(
                "historical_light_list",
                path,
                line=line_number,
                bucket="historical_table",
                authority="historical_proposal_only",
            )
        )
        role = re.sub(r"[*`]", "", cells[0]).strip()
        if role:
            _append_unique(entry["role_claims"], role)

    if "## STDLIB TIER" not in text or "## VENDORED" not in text:
        raise DomainError("historical Light list has no bounded stdlib section")
    stdlib = text.split("## STDLIB TIER", 1)[1].split("## VENDORED", 1)[0]
    for raw in re.findall(r"`([^`]+)`", stdlib):
        module = raw.split("(", 1)[0]
        if module in {"difflib", "statistics", "tokenize", "symtable", "decimal"}:
            # These names are repeated by the prose's Unused sentence. They are
            # still retained once in the proposal domain.
            pass
        module = module.split(".", 1)[0] if module.startswith("random.") else module
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", module):
            continue
        key = ("stdlib_module", module)
        if key not in rows:
            rows[key] = {
                "candidate_id": f"stdlib:{module}",
                "kind": "stdlib_module",
                "normalized_name": module,
                "display_names": [module],
                "provenance": [
                    _source(
                        "historical_light_list",
                        path,
                        bucket="stdlib_tier",
                        authority="historical_proposal_only",
                    )
                ],
                "role_claims": ["historical CB Light stdlib proposal"],
                "import_names": [module],
                "core_contract": None,
                "registry_metadata": None,
                "declarations": {
                    "historical_proposal": True,
                    "stdlib": True,
                },
            }


def _load_candidate_requirements(
    rows: dict[tuple[str, str], dict[str, Any]]
) -> None:
    base = DATA_ROOT / "requirements" / "candidates"
    for path in sorted(base.glob("cb-*.in")):
        bucket = path.stem
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            name = _requirement_name(stripped)
            if name is None:
                raise DomainError(f"cannot parse requirement {path}:{line_number}")
            entry = _entry(rows, name)
            _append_unique(
                entry["declarations"]["candidate_requirement_buckets"], bucket
            )
            entry["provenance"].append(
                _source(
                    "candidate_requirements",
                    path,
                    line=line_number,
                    bucket=bucket,
                    authority="candidate_bucket_only",
                )
            )


def _load_pyproject(rows: dict[tuple[str, str], dict[str, Any]]) -> None:
    path = DATA_ROOT / "pyproject.toml"
    project = tomllib.loads(path.read_text(encoding="utf-8"))["project"]
    for requirement in project.get("dependencies", []):
        name = _requirement_name(requirement)
        if name is None:
            raise DomainError(f"cannot parse direct requirement {requirement!r}")
        entry = _entry(rows, name)
        entry["declarations"]["pyproject_direct"] = True
        existing = entry["declarations"].get("pyproject_direct_requirement")
        if existing not in {None, requirement}:
            raise DomainError(f"conflicting direct requirements for {name}")
        entry["declarations"]["pyproject_direct_requirement"] = requirement
        entry["provenance"].append(
            _source(
                "package_declarations",
                path,
                bucket="project.dependencies",
                authority="declared_runtime_root_only",
            )
        )
    for group, requirements in project.get("optional-dependencies", {}).items():
        for requirement in requirements:
            name = _requirement_name(requirement)
            if name is None:
                raise DomainError(f"cannot parse optional requirement {requirement!r}")
            entry = _entry(rows, name)
            _append_unique(
                entry["declarations"]["pyproject_optional_groups"], group
            )
            entry["provenance"].append(
                _source(
                    "package_declarations",
                    path,
                    bucket=f"project.optional-dependencies.{group}",
                    authority="declared_optional_root_only",
                )
            )


def _load_core_contract(rows: dict[tuple[str, str], dict[str, Any]]) -> None:
    path = DATA_ROOT / "config" / "core_tool_registry_v9.json"
    body = json.loads(path.read_text(encoding="utf-8"))
    for tool in body.get("tools", []):
        name = tool.get("distribution")
        if not isinstance(name, str):
            raise DomainError("core tool registry row has no distribution")
        entry = _entry(rows, name)
        import_name = tool.get("import")
        if isinstance(import_name, str):
            _append_unique(entry["import_names"], import_name)
        for role in tool.get("cb_roles", []):
            if isinstance(role, str):
                _append_unique(entry["role_claims"], role)
        entry["core_contract"] = {
            "tool_id": tool.get("id"),
            "import": import_name,
            "required_apis": list(tool.get("required_apis", [])),
            "cb_roles": list(tool.get("cb_roles", [])),
            "source": list(tool.get("source", [])),
            "tests": list(tool.get("tests", [])),
            "integration_level_claim": tool.get("integration_level"),
        }
        entry["provenance"].append(
            _source(
                "current_core_contract",
                path,
                bucket="tools",
                authority="current_work_role_and_binding_declaration",
            )
        )


def _installed_distributions() -> tuple[dict[str, str], dict[str, list[str]]]:
    installed: dict[str, str] = {}
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        if name:
            installed[normalize_distribution(name)] = distribution.version
    reverse: dict[str, list[str]] = {}
    for import_name, distributions in importlib.metadata.packages_distributions().items():
        for distribution in distributions:
            reverse.setdefault(normalize_distribution(distribution), []).append(import_name)
    return installed, reverse


def _import_visible(import_names: Iterable[str]) -> bool | None:
    names = list(import_names)
    if not names:
        return None
    for name in names:
        try:
            if importlib.util.find_spec(name) is not None:
                return True
        except (ImportError, ModuleNotFoundError, ValueError):
            continue
    return False


def _numeric_version(value: str) -> tuple[int, ...] | None:
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)*)(?:[-+].*)?\s*", value)
    if match is None:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def _compare_versions(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    width = max(len(left), len(right))
    padded_left = left + (0,) * (width - len(left))
    padded_right = right + (0,) * (width - len(right))
    return (padded_left > padded_right) - (padded_left < padded_right)


def version_satisfies_requirement(version: str, requirement: str) -> bool | None:
    """Evaluate the bounded numeric comparator subset used by direct CB roots."""
    installed = _numeric_version(version)
    if installed is None:
        return None
    match = _REQ_NAME.match(requirement)
    if match is None:
        return None
    suffix = requirement[match.end() :].strip()
    clauses = [clause.strip() for clause in suffix.split(",") if clause.strip()]
    if not clauses:
        return None
    for clause in clauses:
        parsed = re.fullmatch(r"(===|==|!=|>=|<=|>|<|~=)\s*(\d+(?:\.\d+)*)", clause)
        if parsed is None:
            return None
        operator, raw_target = parsed.groups()
        target = _numeric_version(raw_target)
        if target is None:
            return None
        comparison = _compare_versions(installed, target)
        if operator in {"==", "==="} and comparison != 0:
            return False
        if operator == "!=" and comparison == 0:
            return False
        if operator == ">=" and comparison < 0:
            return False
        if operator == ">" and comparison <= 0:
            return False
        if operator == "<=" and comparison > 0:
            return False
        if operator == "<" and comparison >= 0:
            return False
        if operator == "~=":
            prefix = target[:-1] if len(target) > 1 else target
            if comparison < 0 or installed[: len(prefix)] != prefix:
                return False
    return True


def _source_manifest(policy: Mapping[str, Any]) -> dict[str, str]:
    paths = {POLICY, Path(__file__).resolve()}
    for source in policy["candidate_sources"]:
        if "path" in source:
            paths.add(DATA_ROOT / source["path"])
        elif "glob" in source:
            paths.update(DATA_ROOT.glob(source["glob"]))
    missing = [path for path in paths if not path.exists()]
    if missing:
        raise DomainError(f"declared domain sources are missing: {missing!r}")
    return {
        _logical_path(path): sha256_file(path)
        for path in sorted(paths)
    }


def compile_domain(
    *,
    installed: Mapping[str, str] | None = None,
    distribution_imports: Mapping[str, Iterable[str]] | None = None,
    interpreter: str | None = None,
) -> dict[str, Any]:
    """Return the complete proposal rows plus a separate environment observation."""
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    _load_registry(rows, policy)
    _load_historical(rows)
    _load_candidate_requirements(rows)
    _load_pyproject(rows)
    _load_core_contract(rows)

    if installed is None or distribution_imports is None:
        observed_installed, observed_imports = _installed_distributions()
        if installed is None:
            installed = observed_installed
        if distribution_imports is None:
            distribution_imports = observed_imports
    installed_normalized = {
        normalize_distribution(name): str(version) for name, version in installed.items()
    }
    imports_normalized = {
        normalize_distribution(name): sorted(set(names))
        for name, names in distribution_imports.items()
    }

    rendered: list[dict[str, Any]] = []
    domain_distribution_names = {
        name for kind, name in rows if kind == "distribution"
    }
    for key in sorted(rows):
        entry = rows[key]
        entry["display_names"].sort(key=str.lower)
        entry["role_claims"].sort()
        entry["provenance"].sort(
            key=lambda item: (
                item["source_id"], item["path"], item.get("line", 0), item.get("bucket", "")
            )
        )
        if entry["kind"] == "distribution":
            name = entry["normalized_name"]
            for import_name in imports_normalized.get(name, []):
                _append_unique(entry["import_names"], import_name)
            entry["import_names"].sort()
            observed = {
                "installed": name in installed_normalized,
                "installed_version": installed_normalized.get(name),
                "import_visible": _import_visible(entry["import_names"]),
                "version_satisfies_declaration": (
                    version_satisfies_requirement(
                        installed_normalized[name],
                        entry["declarations"]["pyproject_direct_requirement"],
                    )
                    if name in installed_normalized
                    and entry["declarations"].get("pyproject_direct_requirement")
                    else None
                ),
            }
        else:
            observed = {
                "installed": True,
                "installed_version": sys.version.split()[0],
                "import_visible": _import_visible(entry["import_names"]),
                "version_satisfies_declaration": None,
            }
        entry["observation"] = observed
        rendered.append(entry)

    source_hashes = _source_manifest(policy)
    identity_rows = [
        {key: value for key, value in row.items() if key != "observation"}
        for row in rendered
    ]
    domain_sha256 = sha256_bytes(canonical_json(identity_rows))
    ambient = sorted(set(installed_normalized) - domain_distribution_names)
    environment = {
        "interpreter": interpreter or sys.executable,
        "python_version": sys.version.split()[0],
        "installed_distribution_count": len(installed_normalized),
        "domain_distributions_installed": sum(
            1
            for row in rendered
            if row["kind"] == "distribution" and row["observation"]["installed"]
        ),
        "ambient_installed_count": len(ambient),
        "ambient_installed": ambient,
    }
    environment["observation_sha256"] = sha256_bytes(canonical_json(environment))
    counts = {
        "objects": len(rendered),
        "distributions": sum(row["kind"] == "distribution" for row in rendered),
        "stdlib_modules": sum(row["kind"] == "stdlib_module" for row in rendered),
        "registry_candidates": sum(
            bool(row["declarations"].get("registry_candidate")) for row in rendered
        ),
        "pyproject_direct": sum(
            bool(row["declarations"].get("pyproject_direct")) for row in rendered
        ),
        "registry_verdict_disagreements": sum(
            row.get("registry_metadata", {}).get("verdict_consistent") is False
            for row in rendered
            if row.get("registry_metadata")
        ),
    }
    return {
        "schema": "constraintbox.cb-light-proposal-domain.v1",
        "profile": "cb_light",
        "completeness": policy["domain_completeness"],
        "domain_sha256": domain_sha256,
        "source_manifest_sha256": sha256_bytes(canonical_json(source_hashes)),
        "source_hashes": source_hashes,
        "forbidden_membership_sources": policy["forbidden_membership_sources"],
        "policy": policy,
        "counts": counts,
        "rows": rendered,
        "environment_observation": environment,
        "claim_ceiling": policy["claim_ceiling"],
        "promotion_allowed": False,
    }
