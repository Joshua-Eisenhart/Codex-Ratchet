#!/usr/bin/env python3
"""Run a deterministic cumulative sequence of public ConstraintBox waves.

This is a scheduler candidate, not a wave authoring surface.  The stage order
comes from ``config/CUMULATIVE_WAVE_SEQUENCE.json`` and cannot be selected by a
model.  A prefix is repeated until its configured semantic fields stabilize or
its explicit round cap is reached.  The next prefix is then attempted.  A
locked or non-runnable stage is recorded and stops the sequence; it is never
simulated or silently skipped.

Only the already-admitted ``scripts/run_wave.py`` is used as the production
child runner.  The injectable ``child_runner`` argument exists solely for
deterministic unit tests and is not a second runtime route.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import signal
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


SCHEMA = "constraintbox.cumulative-wave-run.v1"
CONFIG_SCHEMA = "constraintbox.cumulative-wave-sequence.v1"
DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "CUMULATIVE_WAVE_SEQUENCE.json"
DEFAULT_CHILD_RUNNER = Path(__file__).resolve().with_name("run_wave.py")
ACTIVE_MANIFEST = Path("skills") / "ACTIVE_WAVES.json"
_MISSING = object()


class CumulativeWaveError(ValueError):
    """A malformed sequence or a path outside the product."""


ChildRunner = Callable[..., Mapping[str, Any]]


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value) + b"\n")


def confined_path(value: str | os.PathLike[str], root: Path, *, label: str) -> Path:
    """Resolve a path and reject symlink/``..`` escapes from ``root``."""

    root_resolved = root.expanduser().resolve(strict=True)
    raw = Path(value).expanduser()
    candidate = raw if raw.is_absolute() else root_resolved / raw
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise CumulativeWaveError(f"{label}_OUTSIDE_PRODUCT:{value}") from exc
    return resolved


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise CumulativeWaveError(f"PATH_OUTSIDE_PRODUCT:{path}") from exc


def _read_json(path: Path, *, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CumulativeWaveError(f"{label}_UNREADABLE:{type(exc).__name__}") from exc


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    path = (config_path or DEFAULT_CONFIG).expanduser().resolve(strict=True)
    value = _read_json(path, label="CONFIG")
    if not isinstance(value, dict) or value.get("schema") != CONFIG_SCHEMA:
        raise CumulativeWaveError("REFUSE_CONFIG_SCHEMA")
    return value


def _stage_rows(config: Mapping[str, Any], profile: str) -> tuple[dict[str, Any], list[str], dict[str, dict[str, Any]]]:
    profiles = config.get("profiles")
    if not isinstance(profiles, Mapping) or profile not in profiles:
        raise CumulativeWaveError(f"REFUSE_UNKNOWN_PROFILE:{profile}")
    profile_row = profiles[profile]
    if not isinstance(profile_row, Mapping):
        raise CumulativeWaveError(f"REFUSE_PROFILE_SCHEMA:{profile}")
    order = profile_row.get("stage_order")
    stages = profile_row.get("stages")
    active = profile_row.get("active_stage_ids")
    prefixes = profile_row.get("prefixes")
    if not isinstance(order, list) or not all(isinstance(item, str) for item in order):
        raise CumulativeWaveError("REFUSE_STAGE_ORDER_SCHEMA")
    if len(set(order)) != len(order) or not isinstance(stages, Mapping):
        raise CumulativeWaveError("REFUSE_STAGE_SET_SCHEMA")
    if not isinstance(active, list) or not all(isinstance(item, str) for item in active):
        raise CumulativeWaveError("REFUSE_ACTIVE_STAGE_SCHEMA")
    if any(item not in order for item in active) or set(active) != {
        item for item in order if isinstance(stages.get(item), Mapping) and stages[item].get("mode") == "ACTIVE"
    }:
        raise CumulativeWaveError("REFUSE_ACTIVE_STAGE_MISMATCH")
    stage_map = {key: dict(value) for key, value in stages.items() if isinstance(key, str) and isinstance(value, Mapping)}
    if set(stage_map) != set(order):
        raise CumulativeWaveError("REFUSE_STAGE_ORDER_MISMATCH")
    if not isinstance(prefixes, list) or len(prefixes) != len(order):
        raise CumulativeWaveError("REFUSE_PREFIX_COUNT")
    for index, prefix in enumerate(prefixes, start=1):
        if not isinstance(prefix, Mapping):
            raise CumulativeWaveError("REFUSE_PREFIX_SCHEMA")
        expected = order[:index]
        if prefix.get("prefix_id") != f"prefix-{index}" or prefix.get("stage_ids") != expected:
            raise CumulativeWaveError("REFUSE_PREFIX_ORDER")
        max_rounds = prefix.get("max_rounds")
        allowed = prefix.get("allowed_terminal_statuses")
        if not isinstance(max_rounds, int) or max_rounds < 1 or not isinstance(allowed, list) or not allowed:
            raise CumulativeWaveError("REFUSE_PREFIX_BUDGET")
    return dict(profile_row), order, stage_map


def _load_active_manifest(system_root: Path) -> tuple[dict[str, Any] | None, Path, str | None]:
    path = confined_path(str(ACTIVE_MANIFEST), system_root, label="MANIFEST")
    if not path.is_file():
        return None, path, None
    try:
        return _read_json(path, label="MANIFEST"), path, sha256_path(path)
    except CumulativeWaveError:
        return None, path, None


def _public_runner_path(system_root: Path) -> Path:
    """Return the extracted product's sole public child runner."""

    return confined_path("scripts/run_wave.py", system_root, label="RUNNER")


def _cohort(manifest: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(manifest, Mapping):
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for row in manifest.get("runnable_cohort", []) or []:
        if isinstance(row, Mapping) and isinstance(row.get("wave_id"), str):
            rows[row["wave_id"]] = dict(row)
    return rows


def _manifest_cohort_audit(manifest: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return the public cohort shape needed to bind it to the scheduler.

    ``_cohort`` intentionally projects rows by wave id for source checks.  The
    audit keeps malformed and duplicate rows visible so a public-manifest
    change cannot be silently ignored by that projection.
    """

    if not isinstance(manifest, Mapping):
        return {
            "row_count": None,
            "wave_ids": [],
            "malformed_rows": [],
            "duplicate_wave_ids": [],
        }
    raw_rows = manifest.get("runnable_cohort")
    if not isinstance(raw_rows, list):
        return {
            "row_count": None,
            "wave_ids": [],
            "malformed_rows": ["runnable_cohort"],
            "duplicate_wave_ids": [],
        }
    wave_ids: list[str] = []
    malformed_rows: list[int] = []
    duplicate_wave_ids: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(raw_rows):
        if not isinstance(row, Mapping) or not isinstance(row.get("wave_id"), str):
            malformed_rows.append(index)
            continue
        wave_id = row["wave_id"]
        wave_ids.append(wave_id)
        if wave_id in seen and wave_id not in duplicate_wave_ids:
            duplicate_wave_ids.append(wave_id)
        seen.add(wave_id)
    return {
        "row_count": len(raw_rows),
        "wave_ids": sorted(wave_ids),
        "malformed_rows": malformed_rows,
        "duplicate_wave_ids": sorted(duplicate_wave_ids),
    }


def source_binding(
    system_root: Path,
    *,
    profile: Mapping[str, Any],
    stage_map: Mapping[str, Mapping[str, Any]],
    active_order: Sequence[str],
    config_path: Path,
) -> dict[str, Any]:
    """Freeze the manifest, scheduler, and active-wave source hashes."""

    manifest, manifest_path, manifest_sha = _load_active_manifest(system_root)
    config_resolved = config_path.expanduser().resolve(strict=True)
    try:
        config_rel = _relative(config_resolved, system_root)
    except CumulativeWaveError:
        config_rel = str(config_resolved)
    runner_path = _public_runner_path(system_root)
    binding: dict[str, Any] = {
        "config_path": config_rel,
        "config_sha256": sha256_path(config_resolved),
        "manifest_path": _relative(manifest_path, system_root),
        "manifest_sha256": manifest_sha,
        "runner_path": _relative(runner_path, system_root),
        "runner_sha256": sha256_path(runner_path) if runner_path.is_file() else None,
        "profile_runtime": profile.get("runtime"),
        "active_waves": {},
        "valid": manifest is not None and manifest_sha is not None and runner_path.is_file(),
    }
    cohort = _cohort(manifest)
    cohort_audit = _manifest_cohort_audit(manifest)
    manifest_wave_ids = cohort_audit["wave_ids"]
    scheduler_wave_ids = sorted(set(active_order))
    manifest_only = sorted(set(manifest_wave_ids) - set(scheduler_wave_ids))
    scheduler_only = sorted(set(scheduler_wave_ids) - set(manifest_wave_ids))
    alignment: dict[str, Any] = {
        "manifest_wave_ids": manifest_wave_ids,
        "scheduler_active_wave_ids": scheduler_wave_ids,
        "manifest_only": manifest_only,
        "scheduler_only": scheduler_only,
        "row_count": cohort_audit["row_count"],
        "malformed_rows": cohort_audit["malformed_rows"],
        "duplicate_wave_ids": cohort_audit["duplicate_wave_ids"],
        "valid": False,
    }
    if manifest is None:
        alignment["reason_code"] = "HOLD_MANIFEST_UNREADABLE"
    elif alignment["malformed_rows"]:
        alignment["reason_code"] = "HOLD_MANIFEST_COHORT_SCHEMA"
    elif alignment["duplicate_wave_ids"]:
        alignment["reason_code"] = "HOLD_MANIFEST_DUPLICATE_WAVE_ID"
    elif manifest_only or scheduler_only:
        alignment["reason_code"] = "HOLD_MANIFEST_SCHEDULER_DRIFT"
    else:
        alignment["valid"] = True
    binding["manifest_scheduler_alignment"] = alignment
    if not alignment["valid"]:
        binding["valid"] = False
        binding["reason_code"] = alignment["reason_code"]
    for stage_id in active_order:
        stage = stage_map[stage_id]
        row = cohort.get(stage_id)
        item: dict[str, Any] = {
            "runner": stage.get("runner"),
            "script": None,
            "script_sha256": None,
            "definition": None,
            "definition_sha256": None,
            "valid": True,
        }
        if stage.get("runner") not in {"scripts/run_wave.py", "integrated_system/scripts/run_wave.py"}:
            item["valid"] = False
            item["reason"] = "REFUSE_NON_PUBLIC_RUNNER"
        if not isinstance(row, Mapping):
            item["valid"] = False
            item["reason"] = "HOLD_ACTIVE_WAVE_NOT_IN_MANIFEST"
        else:
            for key in ("script", "definition"):
                declared = row.get(key)
                item[key] = declared
                if not isinstance(declared, str):
                    item["valid"] = False
                    item["reason"] = f"HOLD_{key.upper()}_MISSING"
                    continue
                try:
                    path = confined_path(declared, system_root, label=key.upper())
                except CumulativeWaveError as exc:
                    item["valid"] = False
                    item["reason"] = str(exc)
                    continue
                if not path.is_file():
                    item["valid"] = False
                    item["reason"] = f"HOLD_{key.upper()}_MISSING"
                    continue
                actual_digest = sha256_path(path)
                expected_digest = row.get(f"{key}_sha256")
                item[f"{key}_sha256"] = actual_digest
                item[f"{key}_expected_sha256"] = expected_digest
                if not isinstance(expected_digest, str):
                    item["valid"] = False
                    item["reason"] = f"HOLD_{key.upper()}_DIGEST_UNDECLARED"
                elif expected_digest != actual_digest:
                    item["valid"] = False
                    item["reason"] = f"HOLD_{key.upper()}_DIGEST_MISMATCH"
        if not item["valid"]:
            binding["valid"] = False
        binding["active_waves"][stage_id] = item
    return binding


def _semantic_value(value: Any, field: str) -> Any:
    current = value
    for segment in field.split("."):
        if not isinstance(current, Mapping) or segment not in current:
            return _MISSING
        current = current[segment]
    return current


def semantic_projection(result: Mapping[str, Any], stage: Mapping[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    fields = stage.get("stability_fields")
    if not isinstance(fields, list) or not all(isinstance(field, str) for field in fields):
        return None, ["REFUSE_STABILITY_FIELDS_SCHEMA"]
    projection: dict[str, Any] = {}
    missing: list[str] = []
    for field in fields:
        value = _semantic_value(result, field)
        if value is _MISSING:
            missing.append(field)
        else:
            projection[field] = value
    return (projection if not missing else None), missing


def semantic_signature(projection: Mapping[str, Any]) -> str:
    """Hash only declared semantic fields; timestamps and process metadata are excluded."""

    return sha256_bytes(canonical_json_bytes(dict(projection)))


def _load_public_runner(system_root: Path) -> Any:
    runner_path = _public_runner_path(system_root)
    spec = importlib.util.spec_from_file_location("constraintbox_integrated_public_run_wave", runner_path)
    if spec is None or spec.loader is None:
        raise CumulativeWaveError("REFUSE_PUBLIC_RUNNER_IMPORT")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _default_child_runner(
    stage_id: str,
    *,
    system_root: Path,
    output_dir: Path,
    timeout_seconds: float,
    cancel_file: Path | None,
    run_id: str,
    python_executable: Path | None,
) -> Mapping[str, Any]:
    runner = _load_public_runner(system_root)
    return runner.run_wave(
        stage_id,
        system_root=system_root,
        output_dir=output_dir,
        python_executable=python_executable,
        timeout_seconds=timeout_seconds,
        cancel_file=cancel_file,
        run_id=run_id,
    )


def _safe_output(system_root: Path, requested: Path | None, run_id: str) -> tuple[Path, str | None]:
    default = system_root / "runs" / "cumulative" / run_id
    try:
        path = confined_path(str(requested or default), system_root, label="OUTPUT")
        path.mkdir(parents=True, exist_ok=True)
        return path, None
    except (CumulativeWaveError, OSError) as exc:
        fallback = system_root / "runs" / "cumulative" / "refused" / run_id
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback, str(exc).split(":", 1)[0]


def _write_refusal(system_root: Path, output_dir: Path, *, profile: str, reason: str, run_id: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "profile": profile,
        "run_id": run_id,
        "status": "REFUSE",
        "reason_code": reason,
        "promotion_allowed": False,
        "output_path": _relative(output_dir / "receipt.json", system_root),
        "prefixes": [],
    }
    body["receipt_sha256"] = sha256_bytes(canonical_json_bytes(body))
    _write_json(output_dir / "receipt.json", body)
    return body


def _record_stage_receipt(stage_dir: Path, result: Mapping[str, Any]) -> tuple[str, str]:
    """Preserve the public child receipt without replacing it."""

    existing = stage_dir / "receipt.json"
    if not existing.is_file():
        _write_json(stage_dir / "child_result.json", dict(result))
        existing = stage_dir / "child_result.json"
    return existing.as_posix(), sha256_path(existing)


def _load_child_payload(stage_dir: Path) -> dict[str, Any] | None:
    """Read the preserved public child's ``child.json`` when one exists."""

    path = stage_dir / "child.json"
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return dict(value) if isinstance(value, Mapping) else None


def _not_run_record(stage_id: str, reason: str) -> dict[str, Any]:
    return {
        "stage_id": stage_id,
        "status": "NOT_RUN",
        "reason_code": reason,
        "executed": False,
    }


def run_cumulative_waves(
    profile: str = "light",
    *,
    system_root: Path | None = None,
    output_dir: Path | None = None,
    config_path: Path | None = None,
    run_id: str | None = None,
    cancel_file: Path | None = None,
    timeout_seconds: float = 120.0,
    python_executable: Path | None = None,
    child_runner: ChildRunner | None = None,
) -> dict[str, Any]:
    """Run cumulative prefixes and return a receipt-bound result."""

    system = (system_root or DEFAULT_CONFIG.parents[1]).expanduser().resolve(strict=True)
    config = load_config(config_path)
    profile_row, order, stages = _stage_rows(config, profile)
    cfg_path = (config_path or DEFAULT_CONFIG).expanduser().resolve(strict=True)
    binding = source_binding(
        system,
        profile=profile_row,
        stage_map=stages,
        active_order=profile_row.get("active_stage_ids", []),
        config_path=cfg_path,
    )
    provisional_run_id = run_id or sha256_bytes(
        canonical_json_bytes({"profile": profile, "config": binding.get("config_sha256"), "manifest": binding.get("manifest_sha256")})
    )[:16]
    out_dir, output_refusal = _safe_output(system, output_dir, provisional_run_id)
    receipt_path = out_dir / "receipt.json"
    base: dict[str, Any] = {
        "schema": SCHEMA,
        "profile": profile,
        "runtime": profile_row.get("runtime"),
        "run_id": provisional_run_id,
        "config_schema": CONFIG_SCHEMA,
        "source_binding": binding,
        "output_path": _relative(receipt_path, system),
        "promotion_allowed": False,
        "prefixes": [],
        "cancel_file": None,
        "timeout_seconds": timeout_seconds,
    }
    if output_refusal is not None:
        return _write_refusal(system, out_dir, profile=profile, reason=output_refusal, run_id=provisional_run_id)
    cancel: Path | None = None
    if cancel_file is not None:
        try:
            cancel = confined_path(str(cancel_file), system, label="CANCEL")
            base["cancel_file"] = _relative(cancel, system)
        except CumulativeWaveError as exc:
            base.update({"status": "REFUSE", "reason_code": str(exc).split(":", 1)[0]})
            base["receipt_sha256"] = sha256_bytes(canonical_json_bytes(base))
            _write_json(receipt_path, base)
            return base
    if not binding.get("valid"):
        base.update({
            "status": "HOLD",
            "reason_code": binding.get("reason_code", "HOLD_SOURCE_BINDING_INCOMPLETE"),
        })
        base["receipt_sha256"] = sha256_bytes(canonical_json_bytes(base))
        _write_json(receipt_path, base)
        return base
    if cancel is not None and cancel.exists():
        base.update({"status": "CANCELLED", "reason_code": "CANCELLED_BEFORE_RUN"})
        base["receipt_sha256"] = sha256_bytes(canonical_json_bytes(base))
        _write_json(receipt_path, base)
        return base

    run_child = child_runner or _default_child_runner
    previous_signatures: dict[str, str] = {}
    stability_counts: dict[str, int] = {}
    final_status = "PASS"
    final_reason: str | None = None
    prefixes = profile_row["prefixes"]
    for prefix in prefixes:
        prefix_id = str(prefix["prefix_id"])
        stage_ids = list(prefix["stage_ids"])
        prefix_record: dict[str, Any] = {
            "prefix_id": prefix_id,
            "stage_ids": stage_ids,
            "max_rounds": prefix["max_rounds"],
            "allowed_terminal_statuses": list(prefix["allowed_terminal_statuses"]),
            "rounds": [],
            "status": "RUNNING",
            "stabilized": False,
        }
        locked_id = next(
            (stage_id for stage_id in stage_ids if stages[stage_id].get("mode") != "ACTIVE"),
            None,
        )
        if locked_id is not None:
            locked_index = stage_ids.index(locked_id)
            prefix_record["status"] = "LOCKED"
            prefix_record["reason_code"] = stages[locked_id].get("lock_reason", "LOCKED_STAGE")
            prefix_record["blocked_stage_id"] = locked_id
            prefix_record["stage_records"] = [
                _not_run_record(stage_id, "PREFIX_STOPPED_AT_LOCKED_STAGE")
                for stage_id in stage_ids[:locked_index]
            ] + [
                {
                    "stage_id": locked_id,
                    "status": "LOCKED",
                    "reason_code": prefix_record["reason_code"],
                    "executed": False,
                }
            ] + [
                _not_run_record(stage_id, "PREFIX_NOT_REACHED_AFTER_LOCKED_STAGE")
                for stage_id in stage_ids[locked_index + 1 :]
            ]
            base["prefixes"].append(prefix_record)
            final_status, final_reason = "LOCKED", "LOCKED_STAGE"
            break

        for round_number in range(1, int(prefix["max_rounds"]) + 1):
            if cancel is not None and cancel.exists():
                prefix_record["status"] = "CANCELLED"
                prefix_record["reason_code"] = "CANCELLED_DURING_PREFIX"
                prefix_record["rounds"].append({
                    "round": round_number,
                    "stages": [_not_run_record(stage_id, "CANCELLED_BEFORE_STAGE") for stage_id in stage_ids],
                })
                final_status, final_reason = "CANCELLED", "CANCELLED_DURING_PREFIX"
                break
            round_record: dict[str, Any] = {"round": round_number, "stages": [], "stable": False}
            round_failed = False
            for stage_id in stage_ids:
                stage = stages[stage_id]
                stage_dir = out_dir / prefix_id / f"round-{round_number}" / stage_id
                stage_dir.mkdir(parents=True, exist_ok=True)
                child_run_id = f"{provisional_run_id}-{prefix_id}-r{round_number}-{stage_id}"
                try:
                    result_value = run_child(
                        stage_id,
                        system_root=system,
                        output_dir=stage_dir,
                        timeout_seconds=timeout_seconds,
                        cancel_file=cancel,
                        run_id=child_run_id,
                        python_executable=python_executable,
                    )
                except (OSError, ValueError, CumulativeWaveError) as exc:
                    result_value = {"status": "HOLD", "reason_code": f"HOLD_CHILD_EXCEPTION:{type(exc).__name__}"}
                if not isinstance(result_value, Mapping):
                    result_value = {"status": "HOLD", "reason_code": "HOLD_CHILD_RESULT_INVALID"}
                result = dict(result_value)
                child_receipt_path, child_receipt_sha = _record_stage_receipt(stage_dir, result)
                child_payload = _load_child_payload(stage_dir)
                if child_payload is not None:
                    # The wrapper receipt remains unchanged; semantic stability
                    # is evaluated against the preserved child data instead of
                    # wrapper timing/process metadata.
                    result["child"] = child_payload
                projection, missing = semantic_projection(result, stage)
                stage_record: dict[str, Any] = {
                    "stage_id": stage_id,
                    "status": result.get("status"),
                    "reason_code": result.get("reason_code"),
                    "executed": True,
                    "child_receipt_path": _relative(Path(child_receipt_path), system),
                    "child_receipt_sha256": child_receipt_sha,
                    "stability_fields": list(stage.get("stability_fields", [])),
                    "semantic_projection": projection,
                    "semantic_signature": semantic_signature(projection) if projection is not None else None,
                    "missing_stability_fields": missing,
                }
                round_record["stages"].append(stage_record)
                status = result.get("status")
                allowed = set(stage.get("allowed_terminal_statuses", [])) & set(prefix.get("allowed_terminal_statuses", []))
                if status not in allowed:
                    stage_record["terminal_allowed"] = False
                    stage_record["failure_boundary"] = "CHILD_STATUS_NOT_ALLOWED"
                    round_failed = True
                    final_status = "CANCELLED" if status == "CANCELLED" else "HOLD"
                    final_reason = "CANCELLED_CHILD" if status == "CANCELLED" else "HOLD_CHILD_STATUS"
                    break
                if missing:
                    stage_record["terminal_allowed"] = False
                    stage_record["failure_boundary"] = "STABILITY_FIELD_MISSING"
                    round_failed = True
                    final_status, final_reason = "HOLD", "HOLD_STABILITY_FIELD_MISSING"
                    break
                signature = stage_record["semantic_signature"]
                if previous_signatures.get(stage_id) == signature:
                    stability_counts[stage_id] = stability_counts.get(stage_id, 1) + 1
                else:
                    stability_counts[stage_id] = 1
                previous_signatures[stage_id] = signature
                stage_record["stability_count"] = stability_counts[stage_id]
                stage_record["terminal_allowed"] = True
            if round_failed:
                for remaining in stage_ids[len(round_record["stages"]) :]:
                    round_record["stages"].append(_not_run_record(remaining, "PREFIX_STOPPED_AFTER_FAILURE"))
                prefix_record["rounds"].append(round_record)
                prefix_record["status"] = final_status
                prefix_record["reason_code"] = final_reason
                break
            round_record["stable"] = all(
                stability_counts.get(stage_id, 0) >= int(stages[stage_id].get("semantic_stability_rounds", 2))
                for stage_id in stage_ids
            )
            prefix_record["rounds"].append(round_record)
            if round_record["stable"]:
                prefix_record["status"] = "PASS"
                prefix_record["stabilized"] = True
                prefix_record["stable_round"] = round_number
                break
        else:
            prefix_record["status"] = "HOLD"
            prefix_record["reason_code"] = "HOLD_PREFIX_ROUND_CAP"
            final_status, final_reason = "HOLD", "HOLD_PREFIX_ROUND_CAP"
        base["prefixes"].append(prefix_record)
        if prefix_record["status"] != "PASS":
            if prefix_record["status"] == "CANCELLED":
                final_status, final_reason = "CANCELLED", prefix_record.get("reason_code")
            elif prefix_record["status"] == "HOLD":
                final_status, final_reason = "HOLD", prefix_record.get("reason_code", "HOLD_PREFIX")
            break

    after_binding = source_binding(
        system,
        profile=profile_row,
        stage_map=stages,
        active_order=profile_row.get("active_stage_ids", []),
        config_path=cfg_path,
    )
    base["source_binding_after"] = after_binding
    if after_binding != binding and final_status == "PASS":
        final_status, final_reason = "HOLD", "HOLD_SOURCE_BINDING_DRIFT"
    base.update({"status": final_status, "reason_code": final_reason})
    base["receipt_sha256"] = sha256_bytes(canonical_json_bytes(base))
    _write_json(receipt_path, base)
    return base


def _dump(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def compile_human_summary(value: Mapping[str, Any]) -> dict[str, Any]:
    """Project the full receipt into a compact, receipt-derived human surface."""

    prefixes: list[dict[str, Any]] = []
    executed = 0
    latest_worktrees: list[dict[str, Any]] = []
    context_projection: dict[str, Any] = {}
    executed_stage_ids: list[str] = []
    for prefix in value.get("prefixes", []) or []:
        if not isinstance(prefix, Mapping):
            continue
        rounds = prefix.get("rounds", []) or []
        for round_row in rounds:
            if not isinstance(round_row, Mapping):
                continue
            for stage in round_row.get("stages", []) or []:
                if not isinstance(stage, Mapping) or not stage.get("executed"):
                    continue
                executed += 1
                stage_id = stage.get("stage_id")
                if isinstance(stage_id, str) and stage_id not in executed_stage_ids:
                    executed_stage_ids.append(stage_id)
                projection = stage.get("semantic_projection")
                if not isinstance(projection, Mapping):
                    continue
                if stage_id == "cb-maintenance-wave":
                    worktrees = projection.get("child.diagnostics.git.worktrees")
                    if isinstance(worktrees, list):
                        latest_worktrees = []
                        for item in worktrees:
                            if not isinstance(item, Mapping):
                                continue
                            status = item.get("status")
                            latest_worktrees.append(
                                {
                                    "path": item.get("resolved_path"),
                                    "branch": item.get("branch"),
                                    "head": item.get("head"),
                                    "changed_count": status.get("changed_count")
                                    if isinstance(status, Mapping)
                                    else None,
                                }
                            )
                elif stage_id == "cb-context-strategy-wave":
                    context_projection = {
                        key.removeprefix("child."): item
                        for key, item in projection.items()
                        if key
                        in {
                            "child.prompt_corpus_digest",
                            "child.output_corpus_digest",
                            "child.owner_source_digest",
                            "child.project_source_digest",
                            "child.prompt_file_count",
                            "child.output_file_count",
                        }
                    }
        prefixes.append(
            {
                "prefix_id": prefix.get("prefix_id"),
                "stage_ids": prefix.get("stage_ids", []),
                "status": prefix.get("status"),
                "round_count": len(rounds),
                "stabilized": bool(prefix.get("stabilized", False)),
                "stable_round": prefix.get("stable_round"),
                "blocked_stage_id": prefix.get("blocked_stage_id"),
                "reason_code": prefix.get("reason_code"),
            }
        )
    return {
        "schema": "constraintbox.cumulative-wave-summary.v1",
        "status": value.get("status"),
        "reason_code": value.get("reason_code"),
        "profile": value.get("profile"),
        "run_id": value.get("run_id"),
        "full_receipt": value.get("output_path"),
        "full_receipt_sha256": value.get("receipt_sha256"),
        "prefixes": prefixes,
        "execution": {
            "model_free_wave_executions": executed,
            "executed_stage_ids": executed_stage_ids,
            "provider_model_calls": 0,
            "llm_agents": 0,
            "llm_subagents": 0,
            "llm_subsubagents": 0,
            "python_child_processes": executed,
        },
        "registered_worktrees": latest_worktrees,
        "context": context_projection,
        "promotion_allowed": False,
        "claim_ceiling": (
            "Receipt-derived cumulative scheduler summary only; see full_receipt "
            "for source bindings, child evidence, and complete diagnostics."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("light", "heavy"), default="light")
    parser.add_argument("--system-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--config", dest="config_path", type=Path, default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--cancel-file", type=Path, default=None)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--python", dest="python_executable", type=Path, default=None)
    parser.add_argument("--full", action="store_true", help="print the complete receipt")
    args = parser.parse_args(argv)
    try:
        result = run_cumulative_waves(
            args.profile,
            system_root=args.system_root,
            output_dir=args.output_dir,
            config_path=args.config_path,
            run_id=args.run_id,
            cancel_file=args.cancel_file,
            timeout_seconds=args.timeout,
            python_executable=args.python_executable,
        )
    except (CumulativeWaveError, OSError) as exc:
        print(json.dumps({"schema": SCHEMA, "status": "REFUSE", "reason_code": str(exc)}, sort_keys=True))
        return 3
    _dump(result if args.full else compile_human_summary(result))
    return 0 if result.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
