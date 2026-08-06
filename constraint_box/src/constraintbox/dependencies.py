from __future__ import annotations

import ast
import importlib.metadata
import platform
import re
import sys
import tomllib
from pathlib import Path
from typing import Iterable, Mapping


EXIT_CODES = {
    "OK": 0,
    "ACTION_REQUIRED": 1,
    "IO_ERROR": 2,
    "ADVISORY": 3,
}

LATEST_REASON = "no offline package index available"
ROW_STRATEGY = "one row per (distribution, declaration source)"
_LOCK_NAME = re.compile(r".*-py(?P<python>\d+)-(?P<platform>[^.]+)\.lock$")
_NORMALIZE = re.compile(r"[-_.]+")
_NUMERIC_VERSION = re.compile(r"\d+(?:\.\d+)*")


class DependencyScanError(RuntimeError):
    """A guarded input failure that prevented the dependency scan."""


def normalize_name(name: str) -> str:
    return _NORMALIZE.sub("-", name).casefold()


def parse_lock(path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DependencyScanError(f"cannot read lock file {path}: {exc}") from exc

    declarations: list[dict[str, object]] = []
    invalid: list[dict[str, object]] = []
    for line_number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            invalid.append(
                {
                    "source": str(path),
                    "line": line_number,
                    "text": line,
                    "reason": "lock entry is not pinned with ==",
                }
            )
            continue
        name, version = (part.strip() for part in line.split("==", 1))
        if not name or not version:
            invalid.append(
                {
                    "source": str(path),
                    "line": line_number,
                    "text": line,
                    "reason": "lock entry has an empty name or version",
                }
            )
            continue
        declarations.append(
            {
                "distribution": name,
                "normalized_name": normalize_name(name),
                "required_spec": f"=={version}",
                "source_kind": "lock",
                "source": str(path),
                "extra": None,
            }
        )
    return declarations, invalid


def _parse_requirement(text: str) -> tuple[str, str]:
    try:
        from packaging.requirements import Requirement

        requirement = Requirement(text)
        return requirement.name, str(requirement.specifier)
    except (ImportError, ValueError):
        match = re.fullmatch(
            r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]+\])?\s*(.*)\s*",
            text,
        )
        if not match:
            raise ValueError(f"cannot parse dependency declaration: {text!r}")
        return match.group(1), match.group(2).strip()


def _read_pyproject(path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    try:
        with path.open("rb") as handle:
            body = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise DependencyScanError(f"cannot read pyproject {path}: {exc}") from exc

    project = body.get("project")
    if not isinstance(project, dict):
        raise DependencyScanError(f"pyproject {path} has no [project] table")

    declarations: list[dict[str, object]] = []
    invalid: list[dict[str, object]] = []

    def add(items: object, source: str, extra: str | None) -> None:
        if not isinstance(items, list):
            invalid.append(
                {
                    "source": source,
                    "line": None,
                    "text": repr(items),
                    "reason": "dependency declaration list is not an array",
                }
            )
            return
        for item in items:
            if not isinstance(item, str):
                invalid.append(
                    {
                        "source": source,
                        "line": None,
                        "text": repr(item),
                        "reason": "dependency declaration is not a string",
                    }
                )
                continue
            try:
                name, spec = _parse_requirement(item)
            except ValueError as exc:
                invalid.append(
                    {
                        "source": source,
                        "line": None,
                        "text": item,
                        "reason": str(exc),
                    }
                )
                continue
            declarations.append(
                {
                    "distribution": name,
                    "normalized_name": normalize_name(name),
                    "required_spec": spec,
                    "source_kind": "extra" if extra is not None else "project",
                    "source": source,
                    "extra": extra,
                }
            )

    add(project.get("dependencies", []), f"{path}:[project].dependencies", None)
    extras = project.get("optional-dependencies", {})
    if not isinstance(extras, dict):
        raise DependencyScanError(
            f"pyproject {path} [project.optional-dependencies] is not a table"
        )
    for extra, items in extras.items():
        add(
            items,
            f"{path}:[project.optional-dependencies].{extra}",
            str(extra),
        )
    return declarations, invalid


def _numeric_tuple(version: str) -> tuple[int, ...] | None:
    if not _NUMERIC_VERSION.fullmatch(version):
        return None
    return tuple(int(part) for part in version.split("."))


def _compare_pin(installed: str, required: str) -> tuple[str, str]:
    try:
        from packaging.version import InvalidVersion, Version

        try:
            left = Version(installed)
            right = Version(required)
        except InvalidVersion:
            pass
        else:
            if left == right:
                return "OK", "pep440"
            return ("BEHIND" if left < right else "AHEAD"), "pep440"
    except ImportError:
        pass

    left_numeric = _numeric_tuple(installed)
    right_numeric = _numeric_tuple(required)
    if left_numeric is None or right_numeric is None:
        return "UNKNOWN", "incomparable"
    if left_numeric == right_numeric:
        return "OK", "numeric_fallback"
    return (
        "BEHIND" if left_numeric < right_numeric else "AHEAD",
        "numeric_fallback",
    )


def _compare_range(installed: str, spec: str) -> tuple[str, str]:
    try:
        from packaging.specifiers import InvalidSpecifier, SpecifierSet
        from packaging.version import InvalidVersion, Version

        try:
            version = Version(installed)
            specifier = SpecifierSet(spec)
        except (InvalidVersion, InvalidSpecifier):
            pass
        else:
            if version in specifier:
                return "OK", "pep440"
            lower_bounds = [
                candidate
                for candidate in specifier
                if candidate.operator in {">", ">="}
            ]
            if lower_bounds:
                try:
                    if any(version < Version(bound.version) for bound in lower_bounds):
                        return "BEHIND", "pep440"
                except InvalidVersion:
                    pass
            return "UNKNOWN", "pep440"
    except ImportError:
        pass

    match = re.fullmatch(r">=?\s*(\d+(?:\.\d+)*)", spec)
    left_numeric = _numeric_tuple(installed)
    if match and left_numeric is not None:
        right_numeric = _numeric_tuple(match.group(1))
        if right_numeric is not None:
            satisfies = left_numeric >= right_numeric
            if spec.lstrip().startswith(">") and not spec.lstrip().startswith(">="):
                satisfies = left_numeric > right_numeric
            return (
                ("OK" if satisfies else "BEHIND"),
                "numeric_fallback",
            )
    return "UNKNOWN", "incomparable"


def _classify(installed: str | None, required_spec: str) -> tuple[str, str]:
    if installed is None:
        return "MISSING", "incomparable"
    if required_spec.startswith("=="):
        return _compare_pin(installed, required_spec[2:])
    if not required_spec:
        return "UNKNOWN", "incomparable"
    return _compare_range(installed, required_spec)


def _lock_environment(path: Path) -> dict[str, str | None]:
    match = _LOCK_NAME.fullmatch(path.name)
    if not match:
        return {"file": str(path), "platform": None, "python": None}
    digits = match.group("python")
    python_version = (
        f"{digits[0]}.{digits[1:]}" if len(digits) > 1 else digits
    )
    return {
        "file": str(path),
        "platform": match.group("platform"),
        "python": python_version,
    }


def _is_cross_platform(
    lock_environment: Mapping[str, str | None],
    host_platform: str,
    host_python: str,
) -> bool:
    lock_platform = lock_environment.get("platform")
    lock_python = lock_environment.get("python")
    host_major_minor = ".".join(host_python.split(".")[:2])
    return bool(
        (lock_platform and lock_platform != host_platform)
        or (lock_python and lock_python != host_major_minor)
    )


def _imported_module_roots(project_root: Path) -> set[str]:
    roots: set[str] = set()
    patterns = (
        project_root / "src" / "constraintbox",
        project_root / "workers",
    )
    for base in patterns:
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots.update(alias.name.split(".", 1)[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    roots.add(node.module.split(".", 1)[0])
    return roots


def _installed_version(
    normalized_name: str,
    installed_versions: Mapping[str, str | None] | None,
) -> str | None:
    if installed_versions is not None:
        normalized = {
            normalize_name(name): version for name, version in installed_versions.items()
        }
        return normalized.get(normalized_name)
    try:
        return importlib.metadata.version(normalized_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _base_row(
    declaration: Mapping[str, object],
    installed: str | None,
    state: str,
    compare_method: str,
    cross_platform_lock: bool,
) -> dict[str, object]:
    return {
        **declaration,
        "installed": installed,
        "latest": None,
        "latest_source": None,
        "latest_reason": LATEST_REASON,
        "state": state,
        "compare_method": compare_method,
        "cross_platform_lock": cross_platform_lock,
    }


def scan(
    project_root: Path | None = None,
    *,
    installed_versions: Mapping[str, str | None] | None = None,
    package_map: Mapping[str, Iterable[str]] | None = None,
    stdlib_modules: Iterable[str] | None = None,
    host_platform: str | None = None,
    host_python: str | None = None,
    host_machine: str | None = None,
) -> dict[str, object]:
    root = (
        Path(project_root)
        if project_root is not None
        else Path(__file__).resolve().parents[2]
    )
    locks_directory = root / "requirements" / "locks"
    if not locks_directory.is_dir():
        raise DependencyScanError(f"missing locks directory: {locks_directory}")
    try:
        lock_paths = sorted(locks_directory.glob("*.lock"))
    except OSError as exc:
        raise DependencyScanError(
            f"cannot read locks directory {locks_directory}: {exc}"
        ) from exc
    if not lock_paths:
        raise DependencyScanError(f"no .lock files found in {locks_directory}")

    declarations: list[dict[str, object]] = []
    invalid: list[dict[str, object]] = []
    lock_environments: list[dict[str, str | None]] = []
    for lock_path in lock_paths:
        parsed, rejected = parse_lock(lock_path)
        declarations.extend(parsed)
        invalid.extend(rejected)
        lock_environments.append(_lock_environment(lock_path))

    pyproject_declarations, pyproject_invalid = _read_pyproject(
        root / "pyproject.toml"
    )
    declarations.extend(pyproject_declarations)
    invalid.extend(pyproject_invalid)

    measured_platform = host_platform if host_platform is not None else sys.platform
    measured_python = (
        host_python if host_python is not None else platform.python_version()
    )
    measured_machine = host_machine if host_machine is not None else platform.machine()
    lock_by_source = {
        environment["file"]: environment for environment in lock_environments
    }

    rows: list[dict[str, object]] = []
    declared_names = {
        str(declaration["normalized_name"]) for declaration in declarations
    }
    for declaration in declarations:
        normalized = str(declaration["normalized_name"])
        installed = _installed_version(normalized, installed_versions)
        state, method = _classify(installed, str(declaration["required_spec"]))
        lock_environment = lock_by_source.get(str(declaration["source"]))
        cross_platform = bool(
            lock_environment
            and _is_cross_platform(
                lock_environment,
                measured_platform,
                measured_python,
            )
        )
        rows.append(
            _base_row(
                declaration,
                installed,
                state,
                method,
                cross_platform,
            )
        )

    measured_package_map = (
        package_map
        if package_map is not None
        else importlib.metadata.packages_distributions()
    )
    measured_stdlib = (
        set(stdlib_modules)
        if stdlib_modules is not None
        else set(sys.stdlib_module_names)
    )
    unresolved_imports: list[str] = []
    undeclared_seen: set[tuple[str, str]] = set()
    for module in sorted(_imported_module_roots(root)):
        if module in measured_stdlib or module == "constraintbox":
            continue
        distributions = measured_package_map.get(module)
        if not distributions:
            unresolved_imports.append(module)
            continue
        resolved_installed = False
        for distribution in distributions:
            normalized = normalize_name(distribution)
            installed = _installed_version(normalized, installed_versions)
            if installed is None:
                continue
            resolved_installed = True
            key = (normalized, module)
            if normalized in declared_names or key in undeclared_seen:
                continue
            undeclared_seen.add(key)
            rows.append(
                _base_row(
                    {
                        "distribution": distribution,
                        "normalized_name": normalized,
                        "required_spec": None,
                        "source_kind": "imported",
                        "source": f"imported module {module}",
                        "extra": None,
                        "imported_module": module,
                    },
                    installed,
                    "UNDECLARED",
                    "incomparable",
                    False,
                )
            )
        if not resolved_installed:
            unresolved_imports.append(module)

    lock_targets = sorted(
        {
            f"{environment['platform'] or 'unknown platform'}/"
            f"py{environment['python'] or 'unknown'}"
            for environment in lock_environments
        }
    )
    host_text = (
        f"{measured_platform}/{measured_machine or 'unknown machine'} "
        f"running Python {measured_python}"
    )
    lock_text = ", ".join(lock_targets)
    limitations = {
        "lock_environment": (
            f"The required lock versions were resolved for {lock_text}."
        ),
        "host_environment": f"This scan measured {host_text}.",
        "cross_platform_warning": (
            "AHEAD/BEHIND across that platform or Python boundary may reflect "
            "the platform split rather than genuine staleness."
        ),
        "latest": (
            "Latest available versions were not measured because no offline "
            "package index is available and network access is forbidden."
        ),
        "unresolved_imports": (
            "Imported module roots with no installed distribution mapping are "
            "listed separately and are not classified as UNDECLARED."
        ),
    }
    return {
        "schema": "constraintbox.dependencies.v1",
        "row_strategy": ROW_STRATEGY,
        "rows": rows,
        "invalid_declarations": invalid,
        "unresolved_imports": sorted(set(unresolved_imports)),
        "limitations": limitations,
        "lock_environments": lock_environments,
        "host": {
            "platform": measured_platform,
            "machine": measured_machine,
            "python": measured_python,
        },
    }


def exit_code_for(report: Mapping[str, object]) -> int:
    rows = report.get("rows", [])
    states = {
        row.get("state")
        for row in rows
        if isinstance(row, Mapping)
    }
    if states & {"MISSING", "BEHIND", "UNKNOWN"}:
        return EXIT_CODES["ACTION_REQUIRED"]
    if states & {"AHEAD", "UNDECLARED"}:
        return EXIT_CODES["ADVISORY"]
    return EXIT_CODES["OK"]


def render_check(report: Mapping[str, object]) -> str:
    rows = report.get("rows", [])
    counts = {
        state: sum(
            1
            for row in rows
            if isinstance(row, Mapping) and row.get("state") == state
        )
        for state in ("OK", "BEHIND", "AHEAD", "MISSING", "UNDECLARED", "UNKNOWN")
    }
    return (
        f"deps: exit={exit_code_for(report)} rows={len(rows)} "
        + " ".join(f"{state}={counts[state]}" for state in counts)
    )


def render_table(report: Mapping[str, object]) -> str:
    headers = (
        "DISTRIBUTION",
        "INSTALLED",
        "REQUIRED",
        "STATE",
        "METHOD",
        "CROSS",
        "SOURCE",
    )
    table_rows = [
        (
            str(row.get("distribution", "")),
            str(row.get("installed") or "-"),
            str(row.get("required_spec") or "-"),
            str(row.get("state", "")),
            str(row.get("compare_method", "")),
            "yes" if row.get("cross_platform_lock") else "no",
            str(row.get("source", "")),
        )
        for row in report.get("rows", [])
        if isinstance(row, Mapping)
    ]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in table_rows))
        for index in range(len(headers))
    ]

    def line(values: Iterable[str]) -> str:
        return "  ".join(
            value.ljust(widths[index]) for index, value in enumerate(values)
        ).rstrip()

    output = [line(headers), line("-" * width for width in widths)]
    output.extend(line(row) for row in table_rows)
    output.extend(
        [
            "",
            f"Row strategy: {report.get('row_strategy', ROW_STRATEGY)}",
            "Latest: null for every row; " + LATEST_REASON + ".",
            "Unresolved imports: "
            + (
                ", ".join(str(item) for item in report.get("unresolved_imports", []))
                or "none"
            ),
            "Invalid declarations: "
            + str(len(report.get("invalid_declarations", []))),
            "",
            "Limitations:",
        ]
    )
    limitations = report.get("limitations", {})
    if isinstance(limitations, Mapping):
        output.extend(f"- {value}" for value in limitations.values())
    return "\n".join(output)
