#!/usr/bin/env python3
"""Build a machine-readable inventory of Codex Ratchet evidence artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR_NAMES = {"results", "sim_results"}
EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}

EXPLICIT_RESULT_DIRS = (
    Path("system_v4/probes/a2_state/sim_results"),
    Path("system_v5/legos/results"),
    Path("system_v5/ops/formal_scouts/results"),
)
EXPLICIT_RESULT_GLOBS = (
    "system_v5/julia_carrier/*.json",
    "system_v7/sims/*/results/*.json",
)

# Required-key fingerprints are intentionally conservative and are based on
# checked-in examples:
# - system_v7/sims/probe_quotient_fingerprint_floor_v1/..._jax_results.json
# - system_v7/sims/probe_quotient_fingerprint_floor_v1/..._three_engine_results.json
# - system_v5/legos/results/finite_density_matrix_carrier_trace_psd_...json
# - system_v5/ops/formal_scouts/results/first_order_gradient_...json
# - system_v4/probes/a2_state/sim_results/*_capability_results.json
ENGINE_LEG_REQUIRED_KEYSETS = (
    frozenset(
        {
            "schema",
            "sim_id",
            "engine",
            "classification",
            "TOOL_MANIFEST",
            "TOOL_INTEGRATION_DEPTH",
            "negative_tests",
            "written_at",
            "source_path",
        }
    ),
    frozenset(
        {
            "schema_version",
            "rung_id",
            "engine",
            "classification",
            "generated_at",
            "source_path",
            "result_path",
            "promotion_allowed",
            "formal_admission_allowed",
            "reads_peer_result",
        }
    ),
)
THREE_ENGINE_REQUIRED_KEYSETS = (
    frozenset(
        {
            "schema_version",
            "sim_id",
            "engine",
            "engines",
            "classification",
            "negative_tests",
            "written_at",
            "TOOL_MANIFEST",
            "TOOL_INTEGRATION_DEPTH",
        }
    ),
    frozenset(
        {
            "schema",
            "schema_version",
            "object_id",
            "engines",
            "engine_result_paths",
            "classification",
            "TOOL_MANIFEST",
            "TOOL_INTEGRATION_DEPTH",
        }
    ),
)
FORMAL_SCOUT_REQUIRED_KEYS = frozenset(
    {
        "schema",
        "classification",
        "TOOL_MANIFEST",
        "TOOL_INTEGRATION_DEPTH",
        "claim_ceiling",
        "promotion_allowed",
        "positive",
        "summary",
    }
)
LEGO_REQUIRED_KEYS = frozenset(
    {
        "schema",
        "classification",
        "TOOL_MANIFEST",
        "TOOL_INTEGRATION_DEPTH",
        "math_object",
        "predicate",
        "observable",
        "positive",
        "boundary",
        "summary",
        "claim_ceiling",
        "promotion_allowed",
    }
)
CAPABILITY_REQUIRED_KEYSETS = (
    frozenset(
        {
            "classification",
            "name",
            "summary",
            "tool_manifest",
            "tool_integration_depth",
            "positive",
            "negative",
            "boundary",
            "purpose",
        }
    ),
    frozenset(
        {
            "schema_version",
            "classification",
            "summary",
            "TOOL_MANIFEST",
            "TOOL_INTEGRATION_DEPTH",
            "promotion_allowed",
        }
    ),
    frozenset(
        {
            "schema",
            "classification",
            "summary",
            "TOOL_MANIFEST",
            "TOOL_INTEGRATION_DEPTH",
            "positive",
            "negative",
        }
    ),
)

FORMAL_SCOUT_SCHEMAS = {
    "FORMAL_SCOUT_RESULT_v1",
    "formal_scout_result_v1",
    "formal_scout_result.v1",
    "formal_scout_result/v1",
    "codex_ratchet.formal_scout.v1",
}
LEGO_SCHEMAS = {"LEGO_RESULT_v1"}
CAPABILITY_SCHEMAS = {"tool_capability_probe_v1"}
CAPABILITY_SCHEMA_VERSIONS = {"capability_probe_v1", "capability_probe_result_v1"}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def iso_mtime(path: Path) -> str:
    return (
        dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def keys_fingerprint(keys: set[str]) -> str:
    joined = "\n".join(sorted(keys)).encode("utf-8")
    return f"keys{len(keys)}-{hashlib.sha256(joined).hexdigest()[:16]}"


def has_any_required(keys: set[str], required_sets: tuple[frozenset[str], ...]) -> bool:
    return any(required.issubset(keys) for required in required_sets)


def schema_class(payload: dict[str, Any] | None) -> str:
    if payload is None:
        return "other:unreadable-json"

    keys = set(payload)
    schema = payload.get("schema")
    schema_version = payload.get("schema_version")

    if has_any_required(keys, THREE_ENGINE_REQUIRED_KEYSETS) and (
        schema_version == "three_engine_sim_result_v1"
        or schema == "codex_ratchet.three_engine_sim_result.v1"
    ):
        return "three_engine_sim_result_v1"

    if has_any_required(keys, ENGINE_LEG_REQUIRED_KEYSETS) and (
        schema == "codex_ratchet.engine_leg_result.v1"
        or schema_version == "engine_leg_result_v1"
    ):
        return "engine_leg_result.v1"

    if FORMAL_SCOUT_REQUIRED_KEYS.issubset(keys) and schema in FORMAL_SCOUT_SCHEMAS:
        return "FORMAL_SCOUT_RESULT-like"

    if LEGO_REQUIRED_KEYS.issubset(keys) and schema in LEGO_SCHEMAS:
        return "LEGO_RESULT-like"

    if has_any_required(keys, CAPABILITY_REQUIRED_KEYSETS) and (
        schema in CAPABILITY_SCHEMAS
        or schema_version in CAPABILITY_SCHEMA_VERSIONS
        or "capability" in str(payload.get("name", "")).lower()
    ):
        return "capability_receipt"

    return f"other:{keys_fingerprint(keys)}"


def truthy_key(payload: dict[str, Any] | None, *names: str) -> bool:
    if payload is None:
        return False
    for name in names:
        if name in payload and bool(payload[name]):
            return True
    return False


def resolve_source_from_field(value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    if candidate.exists() and candidate.suffix in {".py", ".jl"}:
        return candidate
    return None


def stem_without_result_suffix(path: Path) -> str:
    stem = path.stem
    for suffix in ("_results", "_result"):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def resolve_sim_source(path: Path, payload: dict[str, Any] | None) -> str | None:
    if payload is not None:
        field_source = resolve_source_from_field(payload.get("source_path"))
        if field_source is not None:
            return rel(field_source)

    base = stem_without_result_suffix(path)
    source_dirs: list[Path] = [path.parent]
    if path.parent.name in RESULT_DIR_NAMES:
        source_dirs.append(path.parent.parent)
    source_dirs.append(path.parent.parent if path.parent.parent != path.parent else path.parent)

    stems = [base]
    if not base.startswith("sim_"):
        stems.append(f"sim_{base}")
    for source_dir in dict.fromkeys(source_dirs):
        for stem in stems:
            for suffix in (".py", ".jl"):
                candidate = source_dir / f"{stem}{suffix}"
                if candidate.exists():
                    return rel(candidate)
    return None


def discover_result_dirs(root: Path) -> list[Path]:
    dirs: set[Path] = set()
    for current, dirnames, _filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        path = Path(current)
        if path.name in RESULT_DIR_NAMES:
            dirs.add(path)
    for explicit in EXPLICIT_RESULT_DIRS:
        path = root / explicit
        if path.exists() and path.is_dir():
            dirs.add(path)
    return sorted(dirs, key=rel)


def discover_artifacts(root: Path) -> list[Path]:
    artifacts: set[Path] = set()
    for result_dir in discover_result_dirs(root):
        artifacts.update(path for path in result_dir.rglob("*.json") if path.is_file())
    for pattern in EXPLICIT_RESULT_GLOBS:
        artifacts.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(artifacts, key=rel)


def build_record(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    stat = path.stat()
    return {
        "path": rel(path),
        "sha256": sha256_file(path),
        "bytes": stat.st_size,
        "mtime_iso": iso_mtime(path),
        "schema_class": schema_class(payload),
        "classification": payload.get("classification") if payload else None,
        "has_tool_manifest": truthy_key(payload, "TOOL_MANIFEST", "tool_manifest"),
        "has_negative_tests": truthy_key(payload, "negative_tests"),
        "has_written_at": truthy_key(payload, "written_at"),
        "status_label": "runs-evidence-only" if payload is not None else "exists",
        "sim_source": resolve_sim_source(path, payload),
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_class_status: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    per_directory: Counter[str] = Counter()
    missing_negative_tests: list[str] = []
    missing_written_at: list[str] = []

    for record in records:
        by_class_status[record["schema_class"]][record["status_label"]] += 1
        per_directory[str(Path(record["path"]).parent)] += 1
        if not record["has_negative_tests"]:
            missing_negative_tests.append(record["path"])
        if not record["has_written_at"]:
            missing_written_at.append(record["path"])

    by_class = {
        schema: dict(sorted(status_counts.items()))
        for schema, status_counts in sorted(by_class_status.items())
    }
    by_class_total = {
        schema: sum(status_counts.values()) for schema, status_counts in by_class.items()
    }
    lev_eligible_now = sum(
        1 for record in records if record["has_negative_tests"] and record["has_written_at"]
    )

    return {
        "catalog_version": 0,
        "artifact_count": len(records),
        "counts_by_schema_class_x_status": by_class,
        "counts_by_schema_class": by_class_total,
        "status_totals": dict(Counter(record["status_label"] for record in records)),
        "lev_eligible_now": lev_eligible_now,
        "eligibility_gaps": {
            "missing_negative_tests": len(missing_negative_tests),
            "missing_written_at": len(missing_written_at),
        },
        "top_gaps": {
            "missing_negative_tests": missing_negative_tests[:50],
            "missing_written_at": missing_written_at[:50],
        },
        "per_directory_totals": dict(sorted(per_directory.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        default="evidence_catalog.json",
        help="Output path for the full catalog, relative to repo root by default.",
    )
    parser.add_argument(
        "--summary",
        default="evidence_catalog_summary.json",
        help="Output path for the summary, relative to repo root by default.",
    )
    args = parser.parse_args()

    records = [build_record(path) for path in discover_artifacts(ROOT)]
    catalog = {
        "catalog_version": 0,
        "artifact_count": len(records),
        "records": records,
    }
    summary = summarize(records)

    catalog_path = Path(args.catalog)
    summary_path = Path(args.summary)
    if not catalog_path.is_absolute():
        catalog_path = ROOT / catalog_path
    if not summary_path.is_absolute():
        summary_path = ROOT / summary_path

    catalog_path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "artifacts": len(records),
                "catalog": rel(catalog_path),
                "summary": rel(summary_path),
                "lev_eligible_now": summary["lev_eligible_now"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
