#!/usr/bin/env python3
"""Codex-owned sim runner with honest gate, swarm, and grounding reporting.

This runner can re-run one sim under a deterministic Python harness, report
exact three-engine schema gaps, check the live stage gate, validate the existing
admission packet shape, and write a Codex receipt.

It also records the sim-mode orchestration obligations that were missing from
the first narrow runner: Wizard v4.3 object preservation, parent/child model
swarm receipts, and CocoIndex wiki/repo grounding receipts. Those planes are
receipt-driven and intentionally fail partial when the work did not actually
run. External models may propose candidates only; Python/JAX/Julia/SMT reruns
own evidence.
"""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECEIPT_DIR = REPO_ROOT / "system_v5" / "ops" / "codex_sim_runner"
DEFAULT_ADMISSION_DIR = REPO_ROOT / "system_v5" / "ops" / "wizard_admissions"

# This is a validator schema string, not a current Wizard runtime claim.
WIZARD_ADMISSION_SCHEMA = "wizard_sim_admission_v4_2"
CURRENT_WIZARD_RUNTIME = "wizard_v4_3_object_preservation_plus_full_council_topology"
THREE_ENGINE_SCHEMA = "three_engine_sim_result_v1"
SWARM_SCHEMA = "codex_model_swarm_manifest_v1"
COCOINDEX_SCHEMA = "codex_cocoindex_grounding_receipt_v1"
MODEL_QUALITY_SWARM_SCHEMA = "codex_model_quality_swarm_report_v1"
DEFAULT_REQUIRED_MODELS = [
    "codex-native",
    "gemini-tui",
    "grok-api",
    "openrouter-fusion",
    "top-chinese-models",
]
DEFAULT_REQUIRED_SWARM_ROUTES = [
    "preflight_registry",
    "voice_wave",
    "decision_council",
    "failure_council",
    "follow_up_council",
    "tool_function_scout",
    "followup_make",
    "followup_scout",
    "followup_audit",
]
DEFAULT_REQUIRED_GROUNDING_CORPORA = ["wiki", "repo"]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_if_exists(path: Path) -> str | None:
    return sha256(path) if path.exists() else None


# Wall-clock/timing metadata a deterministic same-source rerun is EXPECTED to
# vary. The determinism gate tests scientific reproducibility, not wall-clock
# identity, so these named keys are normalized out of the stability hash
# (the raw byte hash is still recorded for transparency). Narrow + named on
# purpose: a scientific field is never silently dropped.
VOLATILE_RESULT_FIELDS = frozenset({
    "elapsed_seconds",
    "elapsed",
    "elapsed_ms",
    "wall_clock_seconds",
    "wall_time_seconds",
    "runtime_seconds",
    "duration_seconds",
    "duration_ms",
    "timestamp",
    "iso_timestamp",
    "generated_at",
    "created_at",
    "run_started_at",
    "run_finished_at",
    "started_at",
    "finished_at",
})


def _strip_volatile(obj: Any, stripped: set[str]) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            if key in VOLATILE_RESULT_FIELDS:
                stripped.add(key)
                continue
            out[key] = _strip_volatile(value, stripped)
        return out
    if isinstance(obj, list):
        return [_strip_volatile(value, stripped) for value in obj]
    return obj


def canonical_result_hash(path: Path) -> tuple[str, list[str]]:
    """Hash a result file with wall-clock/timing fields normalized out.

    Returns (hash, sorted list of volatile fields that were normalized). Falls
    back to the raw byte hash for non-JSON/unreadable files so the gate never
    silently weakens for a payload it cannot canonicalize.
    """

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return sha256(path), []
    stripped: set[str] = set()
    normalized = _strip_volatile(data, stripped)
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return digest, sorted(stripped)


def write_json_atomic(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)
    return path


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_load_error": f"{type(exc).__name__}: {exc}"}
    return payload if isinstance(payload, dict) else {"_load_error": "top-level JSON is not an object"}


def parse_json_stdout(report: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(report.get("stdout_tail") or "{}")
    except json.JSONDecodeError:
        return {"parse_error": True}
    return payload if isinstance(payload, dict) else {"parse_error": "stdout JSON is not an object"}


def rel_to_root(path: Path, root: Path = REPO_ROOT) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def run_command(command: list[str], *, cwd: Path, timeout: int = 120) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-8000:],
            "stderr_tail": proc.stderr[-8000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": None,
            "stdout_tail": (exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-8000:] if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def three_engine_schema_gap_report(payload: dict[str, Any]) -> dict[str, Any]:
    missing_or_invalid: list[str] = []
    if payload.get("schema_version") != THREE_ENGINE_SCHEMA:
        missing_or_invalid.append("schema_version=three_engine_sim_result_v1")

    engines = payload.get("engines")
    if not isinstance(engines, dict):
        missing_or_invalid.extend(["engines.julia", "engines.jax"])
    else:
        for name in ("julia", "jax"):
            record = engines.get(name)
            if not isinstance(record, dict) or record.get("ran") is not True:
                missing_or_invalid.append(f"engines.{name}")

    proofs = payload.get("crossover_proofs")
    if not isinstance(proofs, dict):
        missing_or_invalid.extend(["crossover_proofs.z3", "crossover_proofs.cvc5"])
    else:
        for name in ("z3", "cvc5"):
            record = proofs.get(name)
            if not isinstance(record, dict) or record.get("ran") is not True:
                missing_or_invalid.append(f"crossover_proofs.{name}")

    divergence = payload.get("divergence")
    if not isinstance(divergence, dict):
        missing_or_invalid.extend(
            [
                "divergence.engine_values.julia",
                "divergence.engine_values.jax",
                "divergence.max_divergence",
                "divergence.julia_authoritative=true",
            ]
        )
    else:
        engine_values = divergence.get("engine_values")
        if not isinstance(engine_values, dict) or "julia" not in engine_values:
            missing_or_invalid.append("divergence.engine_values.julia")
        if not isinstance(engine_values, dict) or "jax" not in engine_values:
            missing_or_invalid.append("divergence.engine_values.jax")
        if "max_divergence" not in divergence:
            missing_or_invalid.append("divergence.max_divergence")
        if divergence.get("julia_authoritative") is not True:
            missing_or_invalid.append("divergence.julia_authoritative=true")

    return {
        "schema": THREE_ENGINE_SCHEMA if not missing_or_invalid else "not_three_engine_sim_result_v1",
        "ok": not missing_or_invalid,
        "missing_or_invalid": missing_or_invalid,
    }


def result_math_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "all_pass": payload.get("all_pass"),
        "honest_scope": payload.get("honest_scope") or payload.get("claim_ceiling"),
    }
    if "quotient" in payload:
        summary["quotient"] = payload.get("quotient")
    if "pairs" in payload and isinstance(payload["pairs"], list):
        pair_summaries = []
        for pair in payload["pairs"]:
            if not isinstance(pair, dict):
                continue
            solver = pair.get("solver_flip") or pair.get("smt_flip") or {}
            pair_summaries.append(
                {
                    "pair_id": pair.get("pair_id"),
                    "verdict": pair.get("verdict"),
                    "differing_configs": pair.get("differing_configs"),
                    "z3": (solver.get("z3") if isinstance(solver, dict) else None),
                    "cvc5": (solver.get("cvc5") if isinstance(solver, dict) else None),
                    "a_then_b": pair.get("a_then_b", {}).get("partition")
                    if isinstance(pair.get("a_then_b"), dict)
                    else None,
                    "b_then_a": pair.get("b_then_a", {}).get("partition")
                    if isinstance(pair.get("b_then_a"), dict)
                    else None,
                }
            )
        summary["pairs"] = pair_summaries
    return summary


def seat_certify(
    *,
    python: Path,
    sim_path: Path,
    result_path: Path,
    runs: int,
    timeout: int,
) -> dict[str, Any]:
    run_reports: list[dict[str, Any]] = []
    result_hashes: list[str] = []
    canonical_hashes: list[str] = []
    normalized_fields: set[str] = set()
    for index in range(runs):
        command = [str(python), str(sim_path)]
        before_stat = result_path.stat() if result_path.exists() else None
        run_started_at_ns = time.time_ns()
        report = run_command(command, cwd=sim_path.parent, timeout=timeout)
        report["run_index"] = index + 1
        report["result_existed_before_run"] = before_stat is not None
        report["result_mtime_ns_before_run"] = before_stat.st_mtime_ns if before_stat is not None else None
        report["result_exists_after_run"] = result_path.exists()
        if result_path.exists():
            after_stat = result_path.stat()
            digest = sha256(result_path)
            canonical_digest, stripped = canonical_result_hash(result_path)
            report["result_sha256_after_run"] = digest
            report["result_canonical_sha256_after_run"] = canonical_digest
            report["result_mtime_ns_after_run"] = after_stat.st_mtime_ns
            report["result_written_after_run"] = after_stat.st_mtime_ns >= run_started_at_ns
            result_hashes.append(digest)
            canonical_hashes.append(canonical_digest)
            normalized_fields.update(stripped)
        else:
            report["result_mtime_ns_after_run"] = None
            report["result_written_after_run"] = False
        run_reports.append(report)

    all_exited_zero = all(item.get("returncode") == 0 for item in run_reports)
    all_result_exists = all(item.get("result_exists_after_run") is True for item in run_reports)
    all_result_fresh = all(item.get("result_written_after_run") is True for item in run_reports)
    # Determinism gate compares CANONICAL hashes (wall-clock/timing fields
    # normalized out) so a same-source rerun that differs only in
    # elapsed_seconds is still certified stable. Raw hashes stay in the
    # receipt for transparency.
    stable_result_hash = len(set(canonical_hashes)) == 1 if canonical_hashes else False
    return {
        "ok": all_exited_zero and all_result_exists and all_result_fresh and stable_result_hash,
        "runs_requested": runs,
        "all_exited_zero": all_exited_zero,
        "all_result_exists": all_result_exists,
        "all_result_fresh": all_result_fresh,
        "stable_result_hash": stable_result_hash,
        "result_hashes": result_hashes,
        "canonical_result_hashes": canonical_hashes,
        "normalized_volatile_fields": sorted(normalized_fields),
        "run_reports": run_reports,
    }


def deterministic_python_harness_report(seat: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "codex_deterministic_python_harness_v1",
        "ok": bool(seat.get("ok")),
        "claim": "deterministic same-source Python rerun only; no promotion or model-derived evidence",
        "runs_requested": seat.get("runs_requested"),
        "all_exited_zero": seat.get("all_exited_zero"),
        "all_result_exists": seat.get("all_result_exists"),
        "all_result_fresh": seat.get("all_result_fresh"),
        "stable_result_hash": seat.get("stable_result_hash"),
        "result_hashes": seat.get("result_hashes", []),
    }


def validate_wizard_v43_object_packet(
    *,
    python: Path,
    packet_path: Path | None,
    timeout: int,
) -> dict[str, Any]:
    if packet_path is None:
        return {
            "ok": False,
            "status": "blocked_missing_packet",
            "runtime": CURRENT_WIZARD_RUNTIME,
            "reason": "pass --wizard-packet with the current task object-card JSON before claiming Wizard v4.3 preflight",
        }
    packet_path = packet_path.resolve()
    if not packet_path.exists():
        return {
            "ok": False,
            "status": "blocked_missing_packet",
            "runtime": CURRENT_WIZARD_RUNTIME,
            "packet_path": str(packet_path),
            "reason": "wizard packet path does not exist",
        }
    command = [
        str(python),
        "scripts/wizard_v4_3_object_preservation.py",
        "validate",
        "--input",
        str(packet_path),
    ]
    report = run_command(command, cwd=REPO_ROOT, timeout=timeout)
    parsed = parse_json_stdout(report)
    parsed_ok = parsed.get("ok") is True
    return {
        "ok": report.get("returncode") == 0 and parsed_ok,
        "status": "passed" if report.get("returncode") == 0 and parsed_ok else "failed",
        "runtime": CURRENT_WIZARD_RUNTIME,
        "packet_path": str(packet_path),
        "command_report": report,
        "parsed": parsed,
    }


def _completed(status: Any) -> bool:
    return str(status) in {"completed", "accepted", "passed", "ok", "succeeded"}


def _receipt_exists(record: dict[str, Any]) -> bool:
    receipt_path = record.get("receipt_path") or record.get("artifact_path")
    if not receipt_path:
        return False
    return Path(str(receipt_path)).expanduser().exists()


def _load_child_receipt(record: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    receipt_path = record.get("receipt_path") or record.get("artifact_path")
    if not receipt_path:
        return {}, "missing receipt_path"
    path = Path(str(receipt_path)).expanduser()
    if not path.exists():
        return {}, "receipt_path does not exist"
    payload = load_json(path)
    if payload.get("_load_error"):
        return {}, str(payload["_load_error"])
    return payload, None


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _has_usable_child_output(payload: dict[str, Any]) -> bool:
    for field in ("content", "stdout_tail", "summary", "conclusion", "final"):
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, dict) and value:
            return True
        if isinstance(value, list) and value:
            return True
    return False


def swarm_truth_report(
    *,
    manifest_path: Path | None,
    required_models: list[str],
    required_routes: list[str],
) -> dict[str, Any]:
    required_models_floor = [str(item) for item in required_models]
    required_routes_floor = [str(item) for item in required_routes]
    if manifest_path is None:
        return {
            "ok": False,
            "status": "blocked_missing_manifest",
            "schema": SWARM_SCHEMA,
            "required_models": required_models_floor,
            "required_routes": required_routes_floor,
            "missing_required_models": required_models_floor,
            "missing_required_routes": required_routes_floor,
            "reason": "pass --swarm-manifest with completed parent/child receipts before claiming model swarm work",
        }
    manifest_path = manifest_path.resolve()
    payload = load_json(manifest_path)
    if payload.get("_load_error"):
        return {
            "ok": False,
            "status": "invalid_manifest",
            "schema": SWARM_SCHEMA,
            "manifest_path": str(manifest_path),
            "reason": payload["_load_error"],
        }

    parents = payload.get("parents", [])
    if not isinstance(parents, list):
        parents = []
    completed_parent_count = 0
    completed_child_count = 0
    completed_models: set[str] = set()
    completed_runtimes: set[str] = set()
    completed_model_keys: set[str] = set()
    completed_routes: set[str] = set()
    missing_receipts: list[str] = []
    receipt_integrity_errors: list[str] = []
    non_proposal_children: list[str] = []
    unusable_child_outputs: list[str] = []
    direct_external_children: list[str] = []
    parent_summaries: list[dict[str, Any]] = []

    manifest_required_models = payload.get("required_models")
    if isinstance(manifest_required_models, list) and manifest_required_models:
        required_models_floor = _unique(required_models_floor + [str(item) for item in manifest_required_models])
    manifest_required_routes = payload.get("required_routes")
    if isinstance(manifest_required_routes, list) and manifest_required_routes:
        required_routes_floor = _unique(required_routes_floor + [str(item) for item in manifest_required_routes])

    for parent in parents:
        if not isinstance(parent, dict):
            continue
        parent_complete = _completed(parent.get("status"))
        if parent_complete:
            completed_parent_count += 1
            route = parent.get("route")
            if route:
                completed_routes.add(str(route))
        children = parent.get("children", [])
        if not isinstance(children, list):
            children = []
        child_summaries: list[dict[str, Any]] = []
        for child in children:
            if not isinstance(child, dict):
                continue
            receipt_payload, receipt_error = _load_child_receipt(child)
            child_id = child.get("child_id") or child.get("id")
            runtime = child.get("runtime")
            model = child.get("model") or child.get("runtime")
            route = child.get("route") or child.get("role")
            proposal_only = child.get("proposal_only", True)
            launch_surface = child.get("launch_surface")
            if receipt_error:
                missing_receipts.append(str(child_id or model or "child"))
            else:
                receipt_schema = receipt_payload.get("schema")
                receipt_child_id = receipt_payload.get("child_id") or receipt_payload.get("id")
                receipt_runtime = receipt_payload.get("runtime")
                receipt_model = receipt_payload.get("model") or receipt_payload.get("runtime")
                receipt_route = receipt_payload.get("route") or receipt_payload.get("role")
                receipt_status = receipt_payload.get("status")
                receipt_proposal_only = receipt_payload.get("proposal_only")
                if receipt_schema != "codex_model_child_receipt_v1":
                    receipt_integrity_errors.append(f"{child_id or model}: bad child receipt schema {receipt_schema!r}")
                if child_id and receipt_child_id and str(child_id) != str(receipt_child_id):
                    receipt_integrity_errors.append(f"{child_id}: child_id mismatch in receipt")
                if runtime and receipt_runtime and str(runtime) != str(receipt_runtime):
                    receipt_integrity_errors.append(f"{child_id or runtime}: runtime mismatch in receipt")
                if model and receipt_model and str(model) != str(receipt_model):
                    receipt_integrity_errors.append(f"{child_id or model}: model mismatch in receipt")
                if route and receipt_route and str(route) != str(receipt_route):
                    receipt_integrity_errors.append(f"{child_id or model}: route mismatch in receipt")
                if not _completed(receipt_status):
                    receipt_integrity_errors.append(f"{child_id or model}: child receipt status is not completed")
                if receipt_proposal_only is not True:
                    non_proposal_children.append(str(child_id or model or "child"))
                if not _has_usable_child_output(receipt_payload):
                    unusable_child_outputs.append(str(child_id or model or "child"))
                launch_surface = launch_surface or receipt_payload.get("launch_surface")
                if not runtime and receipt_runtime:
                    runtime = receipt_runtime
                if not model and receipt_model:
                    model = receipt_model
                if not route and receipt_route:
                    route = receipt_route
                proposal_only = receipt_proposal_only
            child_complete = _completed(child.get("status")) and not receipt_error
            if child_complete:
                if launch_surface != "multi_agent_v1_parent_spawned_child":
                    direct_external_children.append(str(child_id or model or runtime or "child"))
                completed_child_count += 1
                if model:
                    completed_models.add(str(model))
                    completed_model_keys.add(str(model))
                if runtime:
                    completed_runtimes.add(str(runtime))
                    completed_model_keys.add(str(runtime))
                if route:
                    completed_routes.add(str(route))
            child_summaries.append(
                {
                    "id": child_id,
                    "runtime": runtime,
                    "model": model,
                    "route": route,
                    "status": child.get("status"),
                    "receipt_exists": _receipt_exists(child),
                    "receipt_error": receipt_error,
                    "proposal_only": proposal_only,
                    "launch_surface": launch_surface,
                }
            )
        parent_summaries.append(
            {
                "id": parent.get("parent_id") or parent.get("id"),
                "runtime": parent.get("runtime"),
                "route": parent.get("route"),
                "status": parent.get("status"),
                "completed": parent_complete,
                "children": child_summaries,
            }
        )

    missing_models = [model for model in required_models_floor if model not in completed_model_keys]
    missing_routes = [route for route in required_routes_floor if route not in completed_routes]
    schema_ok = payload.get("schema") == SWARM_SCHEMA
    ok = (
        schema_ok
        and completed_parent_count > 0
        and completed_child_count > 0
        and not missing_models
        and not missing_routes
        and not missing_receipts
        and not receipt_integrity_errors
        and not non_proposal_children
        and not unusable_child_outputs
    )
    hierarchy_complete = ok and not direct_external_children
    return {
        "ok": ok,
        "status": "coverage_passed" if ok else "partial_or_blocked",
        "hierarchy_complete": hierarchy_complete,
        "schema": payload.get("schema"),
        "expected_schema": SWARM_SCHEMA,
        "manifest_path": str(manifest_path),
        "manifest_claim_ceiling": payload.get("claim_ceiling"),
        "known_limitations": payload.get("known_limitations", []),
        "required_models": required_models_floor,
        "completed_models": sorted(completed_models),
        "completed_runtimes": sorted(completed_runtimes),
        "completed_model_keys": sorted(completed_model_keys),
        "missing_required_models": missing_models,
        "required_routes": required_routes_floor,
        "completed_routes": sorted(completed_routes),
        "missing_required_routes": missing_routes,
        "completed_parents": completed_parent_count,
        "completed_children": completed_child_count,
        "missing_child_receipts": missing_receipts,
        "receipt_integrity_errors": receipt_integrity_errors,
        "non_proposal_children": non_proposal_children,
        "unusable_child_outputs": unusable_child_outputs,
        "direct_external_children": direct_external_children,
        "claim_ceiling": "model proposal/audit route truth only; never sim evidence or promotion evidence",
        "proposal_policy": "children may propose/audit only; runner evidence must come from deterministic sim/proof tools",
        "parents": parent_summaries,
    }


def cocoindex_grounding_report(
    *,
    receipt_path: Path | None,
    required_corpora: list[str],
) -> dict[str, Any]:
    if receipt_path is None:
        return {
            "ok": False,
            "status": "blocked_missing_receipt",
            "schema": COCOINDEX_SCHEMA,
            "required_corpora": required_corpora,
            "missing_required_corpora": required_corpora,
            "reason": "pass --cocoindex-receipt with wiki and repo hits that were exact-read after retrieval",
        }
    receipt_path = receipt_path.resolve()
    payload = load_json(receipt_path)
    if payload.get("_load_error"):
        return {
            "ok": False,
            "status": "invalid_receipt",
            "schema": COCOINDEX_SCHEMA,
            "receipt_path": str(receipt_path),
            "reason": payload["_load_error"],
        }

    hits = payload.get("hits", [])
    if not isinstance(hits, list):
        hits = []
    corpora_with_exact_reads: set[str] = set()
    missing_paths: list[str] = []
    non_exact_hits: list[str] = []
    hit_summaries: list[dict[str, Any]] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        corpus = str(hit.get("corpus") or "")
        path_text = str(hit.get("path") or "")
        exact_read = hit.get("exact_read") is True
        path_exists = Path(path_text).expanduser().exists() if path_text else False
        if not path_exists:
            missing_paths.append(path_text or "<missing path>")
        if not exact_read:
            non_exact_hits.append(path_text or corpus or "<unknown hit>")
        if corpus and exact_read and path_exists:
            corpora_with_exact_reads.add(corpus)
        hit_summaries.append(
            {
                "corpus": corpus,
                "path": path_text,
                "exact_read": exact_read,
                "path_exists": path_exists,
                "retrieval": hit.get("retrieval"),
                "lines": hit.get("lines"),
            }
        )

    manifest_required_corpora = payload.get("required_corpora")
    if isinstance(manifest_required_corpora, list) and manifest_required_corpora:
        required_corpora = [str(item) for item in manifest_required_corpora]
    missing_corpora = [corpus for corpus in required_corpora if corpus not in corpora_with_exact_reads]
    schema_ok = payload.get("schema") == COCOINDEX_SCHEMA
    ok = schema_ok and not missing_corpora and not missing_paths and not non_exact_hits
    return {
        "ok": ok,
        "status": "passed" if ok else "partial_or_blocked",
        "schema": payload.get("schema"),
        "expected_schema": COCOINDEX_SCHEMA,
        "receipt_path": str(receipt_path),
        "required_corpora": required_corpora,
        "corpora_with_exact_reads": sorted(corpora_with_exact_reads),
        "missing_required_corpora": missing_corpora,
        "missing_paths": missing_paths,
        "non_exact_hits": non_exact_hits,
        "queries": payload.get("queries", []),
        "hits": hit_summaries,
        "claim": "CocoIndex is a semantic retrieval map only; exact file reads remain the evidence surface",
    }


def model_quality_swarm_report(*, report_path: Path | None) -> dict[str, Any]:
    if report_path is None:
        return {
            "ok": False,
            "status": "not_provided",
            "schema": MODEL_QUALITY_SWARM_SCHEMA,
            "gate_participation": "advisory_only_not_sim_gate",
            "reason": "pass --model-quality-report to attach proposal-only many-model quality audit results",
        }
    report_path = report_path.resolve()
    payload = load_json(report_path)
    if payload.get("_load_error"):
        return {
            "ok": False,
            "status": "invalid_report",
            "schema": MODEL_QUALITY_SWARM_SCHEMA,
            "report_path": str(report_path),
            "gate_participation": "advisory_only_not_sim_gate",
            "reason": payload["_load_error"],
        }
    children = payload.get("children", [])
    if not isinstance(children, list):
        children = []
    boundary_errors: list[str] = []
    usable_outputs: list[str] = []
    reasoning_only_outputs: list[str] = []
    required_blocked = {"sim_admission", "formal_evidence", "canonical_status"}
    for child in children:
        if not isinstance(child, dict):
            boundary_errors.append("child_not_object")
            continue
        child_id = str(child.get("child_id") or child.get("model") or "child")
        if child.get("proposal_only") is not True:
            boundary_errors.append(f"{child_id}:proposal_only_not_true")
        if child.get("promotion_allowed") is not False:
            boundary_errors.append(f"{child_id}:promotion_allowed_not_false")
        if child.get("formal_admission_allowed") is not False:
            boundary_errors.append(f"{child_id}:formal_admission_allowed_not_false")
        if child.get("model_outputs_are_sim_evidence") is not False:
            boundary_errors.append(f"{child_id}:model_outputs_are_sim_evidence_not_false")
        blocked_consumers = set(str(item) for item in child.get("blocked_consumers") or [])
        if not required_blocked.issubset(blocked_consumers):
            boundary_errors.append(f"{child_id}:blocked_consumers_missing_evidence_boundaries")
        extraction = child.get("extraction") if isinstance(child.get("extraction"), dict) else {}
        extraction_status = str(extraction.get("extraction_status") or "")
        if extraction_status == "reasoning_only_content_null":
            reasoning_only_outputs.append(child_id)
        score = child.get("score") if isinstance(child.get("score"), dict) else {}
        if score.get("accepted") is True and extraction_status == "usable_content":
            usable_outputs.append(child_id)
    schema_ok = payload.get("schema") == MODEL_QUALITY_SWARM_SCHEMA
    top_level_boundary_ok = (
        payload.get("proposal_only") is True
        and payload.get("promotion_allowed") is False
        and payload.get("formal_admission_allowed") is False
        and payload.get("model_outputs_are_sim_evidence") is False
    )
    ok = schema_ok and top_level_boundary_ok and not boundary_errors
    return {
        "ok": ok,
        "status": "accepted_advisory" if ok else "blocked_or_invalid",
        "schema": payload.get("schema"),
        "expected_schema": MODEL_QUALITY_SWARM_SCHEMA,
        "report_path": str(report_path),
        "gate_participation": "advisory_only_not_sim_gate",
        "quality_status": payload.get("status"),
        "completed_model_count": payload.get("completed_model_count"),
        "accepted_model_count": payload.get("accepted_model_count"),
        "usable_content_model_count": payload.get("usable_content_model_count"),
        "reasoning_only_model_count": payload.get("reasoning_only_model_count"),
        "usable_outputs": usable_outputs,
        "reasoning_only_outputs": reasoning_only_outputs,
        "direct_external_children": payload.get("direct_external_children", []),
        "boundary_errors": boundary_errors,
        "top_models": payload.get("top_models", []),
        "claim_ceiling": "proposal quality ranking only; deterministic runner gates remain authoritative",
    }


def full_wizard_obligation_report(
    *,
    wizard_v43: dict[str, Any],
    deterministic_harness: dict[str, Any],
    swarm: dict[str, Any],
    cocoindex_grounding: dict[str, Any],
) -> dict[str, Any]:
    missing: list[str] = []
    if not wizard_v43.get("ok"):
        missing.append("wizard_v4_3_object_preservation_packet")
    if not deterministic_harness.get("ok"):
        missing.append("deterministic_python_harness")
    if not swarm.get("ok"):
        for route in swarm.get("missing_required_routes", []) or []:
            missing.append(f"swarm_route:{route}")
        for model in swarm.get("missing_required_models", []) or []:
            missing.append(f"swarm_model:{model}")
        if not swarm.get("missing_required_routes") and not swarm.get("missing_required_models"):
            missing.append("parent_child_swarm_receipts")
    elif swarm.get("hierarchy_complete") is not True:
        missing.append("parent_child_hierarchy_for_external_models")
    if not cocoindex_grounding.get("ok"):
        for corpus in cocoindex_grounding.get("missing_required_corpora", []) or []:
            missing.append(f"cocoindex_grounding:{corpus}")
        if not cocoindex_grounding.get("missing_required_corpora"):
            missing.append("cocoindex_grounding_receipt")

    ok = not missing
    return {
        "ok": ok,
        "status": "all_required_receipts_present" if ok else "partial",
        "runtime": CURRENT_WIZARD_RUNTIME,
        "full_label_allowed": False,
        "claim_ceiling": "receipt coverage for required orchestration planes only; not a sim promotion or final FULL Wizard proof",
        "legacy_boundary": (
            "wizard_sim_admission_v4_2 is only the existing admission validator schema; "
            "it is not evidence that current Wizard v4.3 full topology ran"
        ),
        "missing_obligations": missing,
        "counts": {
            "parents_completed": swarm.get("completed_parents", 0),
            "children_completed": swarm.get("completed_children", 0),
            "models_completed": len(swarm.get("completed_models", []) or []),
            "grounding_corpora": len(cocoindex_grounding.get("corpora_with_exact_reads", []) or []),
        },
    }


def build_admission_payload(
    *,
    repo_root: Path,
    basename: str,
    sim_path: Path,
    result_path: Path,
    artifact_path: Path,
    stage: str,
    tool_target: str,
    claim_ceiling: str,
) -> dict[str, Any]:
    return {
        "schema": WIZARD_ADMISSION_SCHEMA,
        "basename": basename,
        "sim_path": rel_to_root(sim_path, repo_root),
        "status": "queue_ready",
        "admitted_by": "guard.receipt_audit",
        "admission_artifact": str(artifact_path),
        "controller_read_artifacts": [str(artifact_path), str(result_path)],
        "formal_sim_profile": {
            "stage": stage,
            "claim": basename,
            "expected_result_path": str(result_path),
        },
        "packet_contract": {
            "type": "codex_sim_runner_micro_receipt",
            "tool_target": tool_target,
            "claim_ceiling": claim_ceiling,
            "promotion_boundary": "no promotion beyond scratch_diagnostic without a later admitted packet",
            "prior_function_receipts": [],
        },
    }


def admission_artifact_payload(
    *,
    basename: str,
    sim_path: Path,
    result_path: Path,
    result_payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "kind": "codex_sim_runner_admission_artifact",
        "basename": basename,
        "sim_path": str(sim_path),
        "sim_sha256": sha256_if_exists(sim_path),
        "result_path": str(result_path),
        "result_sha256": sha256_if_exists(result_path),
        "classification": result_payload.get("classification"),
        "promotion_allowed": result_payload.get("promotion_allowed"),
        "formal_admission_allowed": result_payload.get("formal_admission_allowed"),
        "claim_ceiling": result_payload.get("claim_ceiling") or result_payload.get("honest_scope"),
    }


def stage_gate_report(*, python: Path, claim: str, timeout: int) -> dict[str, Any]:
    command = [str(python), "scripts/stage_gate.py", "--claim", claim]
    report = run_command(command, cwd=REPO_ROOT, timeout=timeout)
    parsed = parse_json_stdout(report)
    return {
        "ok": report.get("returncode") == 0,
        "claim": claim,
        "command_report": report,
        "parsed": parsed,
    }


def validate_three_engine(*, python: Path, result_path: Path, timeout: int) -> dict[str, Any]:
    command = [str(python), "scripts/validate_three_engine_sim_result.py", str(result_path)]
    report = run_command(command, cwd=REPO_ROOT, timeout=timeout)
    parsed = parse_json_stdout(report)
    return {"ok": report.get("returncode") == 0, "command_report": report, "parsed": parsed}


def validate_admission(
    *,
    python: Path,
    basename: str,
    sim_path: Path,
    admission_path: Path,
    result_path: Path,
    timeout: int,
) -> dict[str, Any]:
    command = [
        str(python),
        "scripts/wizard_sim_admission.py",
        "--basename",
        basename,
        "--sim-path",
        str(sim_path),
        "--admission-file",
        str(admission_path),
        "--expected-result-path",
        str(result_path),
    ]
    report = run_command(command, cwd=REPO_ROOT, timeout=timeout)
    parsed = parse_json_stdout(report)
    return {"ok": report.get("returncode") == 0, "command_report": report, "parsed": parsed}


def purgatory_record(
    *,
    basename: str,
    result_path: Path,
    result_payload: dict[str, Any],
    gate_reports: dict[str, Any],
) -> dict[str, Any]:
    return {
        "kind": "codex_sim_runner_purgatory_record",
        "candidate_id": basename,
        "candidate_name": basename,
        "status": "resident_purgatory",
        "reason_tag": "scratch_diagnostic_not_promoted",
        "failure_class": "PARKED_NOT_FAILURE",
        "target_ref": str(result_path),
        "raw_lines": [
            "Codex runner keeps scratch diagnostics below promotion.",
            "Model proposals are not sim evidence.",
            "Graph graveyard routing is opt-in because the live graph is shared mutable state.",
        ],
        "sim_evidence": {
            "classification": result_payload.get("classification"),
            "promotion_allowed": result_payload.get("promotion_allowed"),
            "formal_admission_allowed": result_payload.get("formal_admission_allowed"),
            "all_pass": result_payload.get("all_pass"),
            "gate_reports": gate_reports,
        },
    }


def route_to_graveyard_if_requested(
    *,
    repo_root: Path,
    record: dict[str, Any],
    enabled: bool,
) -> dict[str, Any]:
    if not enabled:
        return {
            "status": "not_written",
            "reason": "write_graveyard not requested; shared graph mutation stays controller-serial",
            "record": record,
        }
    try:
        sys.path.insert(0, str(repo_root))
        from system_v4.skills.a2_graph_refinery import A2GraphRefinery
        from system_v4.skills.graveyard_router import GraveyardRouter

        refinery = A2GraphRefinery(str(repo_root))
        router = GraveyardRouter(refinery)
        graveyard_id = router.route_to_graveyard(
            candidate_id=str(record["candidate_id"]),
            reason_tag=str(record["reason_tag"]),
            failure_class="SIM_KILL",
            raw_lines=[str(item) for item in record.get("raw_lines", [])],
            sim_evidence=dict(record.get("sim_evidence", {})),
            target_ref=str(record.get("target_ref") or ""),
        )
        return {"status": "written", "graveyard_id": graveyard_id}
    except Exception as exc:
        return {"status": "write_failed", "error": f"{type(exc).__name__}: {exc}", "record": record}


def basename_from_paths(sim_path: Path, result_path: Path | None) -> str:
    if result_path is not None:
        name = result_path.name
        if name.endswith("_results.json"):
            return name[: -len("_results.json")]
        if name.endswith(".json"):
            return name[:-5]
    return sim_path.stem


def admission_basename_from_result(result_payload: dict[str, Any], fallback: str) -> str:
    """Use a neutral object id for admission when a result filename is an envelope.

    The result file may legitimately end in `_three_engine` while the claim is a
    rung-0 scratch diagnostic. Using the filename as the admission claim can
    accidentally trigger nonclassical/engine heuristics in the admission guard.
    """

    sim_id = str(result_payload.get("sim_id") or result_payload.get("object_id") or "").strip()
    if sim_id and fallback == f"{sim_id}_three_engine":
        return sim_id
    return fallback


def derive_result_path(sim_path: Path, override: Path | None) -> Path:
    """Derive the watched result path when --result-path is not given.

    Sims write `<stem>_results.json` in one of three layouts: next to the sim
    file (system_v4/probes), in a sibling results/ dir (system_v5/legos,
    system_v5/ops/formal_scouts), or under a2_state/sim_results/ (SIM_TEMPLATE
    probes). Formal scouts additionally strip their `sim_` filename prefix in
    the result name (sim_foo_probe.py -> foo_probe_results.json). An existing
    result file wins, exact stem before stripped stem, sibling before
    results/ before a2_state. With no existing file, a sibling results/ dir
    is preferred only when it already holds *_results.json files —
    system_v4/probes has a results/ dir that is not a sim-results dir, and
    its sibling-writing sims must keep the sibling default.
    """

    if override is not None:
        return override.resolve()
    stems = [sim_path.stem]
    if sim_path.stem.startswith("sim_"):
        stems.append(sim_path.stem[len("sim_"):])
    candidates = [
        parent / f"{stem}_results.json"
        for parent in (sim_path.parent, sim_path.parent / "results", sim_path.parent / "a2_state" / "sim_results")
        for stem in stems
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    results_dir = sim_path.parent / "results"
    if results_dir.is_dir() and any(results_dir.glob("*_results.json")):
        # Scout convention: sim_-prefixed sims write the stripped name.
        return (results_dir / f"{stems[-1]}_results.json").resolve()
    return candidates[0].resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim-path", required=True, type=Path)
    parser.add_argument("--result-path", type=Path)
    parser.add_argument("--basename")
    parser.add_argument("--admission-basename")
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--seat-runs", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--stage-claim", default="tool_micro")
    parser.add_argument("--formal-stage", default="micro")
    parser.add_argument("--tool-target", default="z3")
    parser.add_argument("--receipt-dir", type=Path, default=DEFAULT_RECEIPT_DIR)
    parser.add_argument("--admission-dir", type=Path, default=DEFAULT_ADMISSION_DIR)
    parser.add_argument("--write-admission", action="store_true")
    parser.add_argument("--write-graveyard", action="store_true")
    parser.add_argument("--wizard-packet", type=Path)
    parser.add_argument("--swarm-manifest", type=Path)
    parser.add_argument("--cocoindex-receipt", type=Path)
    parser.add_argument("--model-quality-report", type=Path)
    parser.add_argument("--required-model", action="append")
    parser.add_argument("--required-swarm-route", action="append")
    parser.add_argument("--required-grounding-corpus", action="append")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sim_path = args.sim_path.resolve()
    result_path = derive_result_path(sim_path, args.result_path)
    basename = args.basename or basename_from_paths(sim_path, result_path)
    receipt_dir = args.receipt_dir.resolve()
    receipt_path = receipt_dir / f"{basename}_codex_sim_runner_receipt.json"

    initial_result_payload = load_json(result_path) if result_path.exists() else {}
    seat = seat_certify(
        python=args.python.resolve(),
        sim_path=sim_path,
        result_path=result_path,
        runs=args.seat_runs,
        timeout=args.timeout,
    )
    deterministic_harness = deterministic_python_harness_report(seat)
    wizard_v43 = validate_wizard_v43_object_packet(
        python=args.python.resolve(),
        packet_path=args.wizard_packet,
        timeout=args.timeout,
    )
    swarm = swarm_truth_report(
        manifest_path=args.swarm_manifest,
        required_models=args.required_model or DEFAULT_REQUIRED_MODELS,
        required_routes=args.required_swarm_route or DEFAULT_REQUIRED_SWARM_ROUTES,
    )
    cocoindex_grounding = cocoindex_grounding_report(
        receipt_path=args.cocoindex_receipt,
        required_corpora=args.required_grounding_corpus or DEFAULT_REQUIRED_GROUNDING_CORPORA,
    )
    quality_swarm = model_quality_swarm_report(report_path=args.model_quality_report)
    full_wizard_obligations = full_wizard_obligation_report(
        wizard_v43=wizard_v43,
        deterministic_harness=deterministic_harness,
        swarm=swarm,
        cocoindex_grounding=cocoindex_grounding,
    )
    if seat["ok"]:
        result_payload = load_json(result_path) if result_path.exists() else {}
        result_payload_status = "fresh_from_deterministic_harness"
        schema_gaps = three_engine_schema_gap_report(result_payload)
        three_engine = validate_three_engine(
            python=args.python.resolve(),
            result_path=result_path,
            timeout=args.timeout,
        )
    else:
        result_payload = {}
        result_payload_status = "blocked_not_fresh_from_deterministic_harness"
        schema_gaps = {
            "schema": "not_checked",
            "ok": False,
            "missing_or_invalid": ["deterministic_python_harness_not_fresh"],
        }
        three_engine = {
            "ok": False,
            "status": "blocked_not_fresh_from_deterministic_harness",
            "reason": "three-engine validation is skipped when the result was not freshly written by this run",
        }
    admission_basename = args.admission_basename or admission_basename_from_result(result_payload, basename)
    artifact_path = receipt_dir / f"{admission_basename}_admission_artifact.json"
    admission_path = args.admission_dir.resolve() / f"codex_{admission_basename}.json"
    stage = stage_gate_report(
        python=args.python.resolve(),
        claim=args.stage_claim,
        timeout=args.timeout,
    )

    claim_ceiling = str(
        result_payload.get("claim_ceiling")
        or result_payload.get("honest_scope")
        or "scratch_diagnostic; no promotion"
    )
    artifact = admission_artifact_payload(
        basename=admission_basename,
        sim_path=sim_path,
        result_path=result_path,
        result_payload=result_payload,
    )
    write_json_atomic(artifact_path, artifact)

    admission_payload = build_admission_payload(
        repo_root=REPO_ROOT,
        basename=admission_basename,
        sim_path=sim_path,
        result_path=result_path,
        artifact_path=artifact_path,
        stage=args.formal_stage,
        tool_target=args.tool_target,
        claim_ceiling=claim_ceiling,
    )
    admission_write = {
        "status": "not_written",
        "reason": "pass --write-admission to create the validator packet under system_v5/ops/wizard_admissions",
        "path": str(admission_path),
    }
    if args.write_admission:
        write_json_atomic(admission_path, admission_payload)
        admission_write = {"status": "written", "path": str(admission_path)}

    if seat["ok"]:
        admission_validation = validate_admission(
            python=args.python.resolve(),
            basename=admission_basename,
            sim_path=sim_path,
            admission_path=admission_path,
            result_path=result_path,
            timeout=args.timeout,
        )
    else:
        admission_validation = {
            "ok": False,
            "status": "blocked_not_fresh_from_deterministic_harness",
            "reason": "wizard_sim_admission validation is skipped when the result was not freshly written by this run",
            "parsed": {"findings": ["deterministic_python_harness_not_fresh"]},
        }

    gate_reports = {
        "seat_certify": {"ok": seat["ok"]},
        "deterministic_python_harness": deterministic_harness,
        "wizard_v43_object_preservation": {"ok": wizard_v43["ok"], "status": wizard_v43["status"]},
        "parent_child_model_swarm": {
            "ok": swarm["ok"],
            "status": swarm["status"],
            "missing_required_models": swarm.get("missing_required_models", []),
            "missing_required_routes": swarm.get("missing_required_routes", []),
        },
        "cocoindex_grounding": {
            "ok": cocoindex_grounding["ok"],
            "status": cocoindex_grounding["status"],
            "missing_required_corpora": cocoindex_grounding.get("missing_required_corpora", []),
        },
        "model_quality_swarm": {
            "ok": quality_swarm["ok"],
            "status": quality_swarm["status"],
            "gate_participation": quality_swarm["gate_participation"],
            "accepted_model_count": quality_swarm.get("accepted_model_count"),
            "boundary_errors": quality_swarm.get("boundary_errors", []),
        },
        "three_engine_validator": {
            "ok": three_engine["ok"],
            "schema_gaps": schema_gaps,
        },
        "stage_gate": {"ok": stage["ok"], "parsed": stage["parsed"]},
        "wizard_sim_admission": {
            "ok": admission_validation["ok"],
            "path": str(admission_path),
            "write": admission_write,
            "parsed": admission_validation["parsed"],
        },
    }
    purgatory = purgatory_record(
        basename=basename,
        result_path=result_path,
        result_payload=result_payload,
        gate_reports=gate_reports,
    )
    graveyard = route_to_graveyard_if_requested(
        repo_root=REPO_ROOT,
        record=purgatory,
        enabled=args.write_graveyard,
    )

    pipeline_completed = bool(seat["ok"] and stage["ok"])
    execution_gates_passed = bool(
        seat["ok"]
        and three_engine["ok"]
        and stage["ok"]
        and admission_validation["ok"]
    )
    orchestration_gates_passed = bool(full_wizard_obligations["ok"])
    all_checked_gates_passed = bool(execution_gates_passed and orchestration_gates_passed)
    receipt = {
        "schema": "codex_sim_runner_receipt_v1",
        "created_at": utc_now(),
        "repo_root": str(REPO_ROOT),
        "runner": str(Path(__file__).resolve()),
        "python": str(args.python.resolve()),
        "basename": basename,
        "admission_basename": admission_basename,
        "sim_path": str(sim_path),
        "sim_sha256": sha256_if_exists(sim_path),
        "result_path": str(result_path),
        "initial_result_sha256": sha256_if_exists(result_path) if initial_result_payload else None,
        "final_result_sha256": sha256_if_exists(result_path),
        "claim_ceiling": "scratch_diagnostic_or_lower; no promotion; no canonical claim",
        "model_proposal_policy": "external model outputs may propose candidates only; Python/JAX/Julia/SMT reruns own evidence",
        "current_wizard_runtime": CURRENT_WIZARD_RUNTIME,
        "math_summary": result_math_summary(result_payload),
        "result_payload_status": result_payload_status,
        "seat_certify": seat,
        "deterministic_python_harness": deterministic_harness,
        "wizard_v43_object_preservation": wizard_v43,
        "parent_child_model_swarm": swarm,
        "model_quality_swarm": quality_swarm,
        "cocoindex_grounding": cocoindex_grounding,
        "full_wizard_obligations": full_wizard_obligations,
        "three_engine_schema_gap_report": schema_gaps,
        "three_engine_validator": three_engine,
        "stage_gate": stage,
        "admission_artifact_path": str(artifact_path),
        "admission_packet_path": str(admission_path),
        "admission_packet_write": admission_write,
        "admission_packet_payload": admission_payload,
        "wizard_sim_admission": admission_validation,
        "purgatory_record": purgatory,
        "graveyard_router": graveyard,
        "pipeline_completed": pipeline_completed,
        "execution_gates_passed": execution_gates_passed,
        "orchestration_gates_passed": orchestration_gates_passed,
        "all_checked_gates_passed": all_checked_gates_passed,
        "all_pass": all_checked_gates_passed,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }
    write_json_atomic(receipt_path, receipt)

    summary = {
        "pipeline_completed": pipeline_completed,
        "all_checked_gates_passed": all_checked_gates_passed,
        "receipt_path": str(receipt_path),
        "basename": basename,
        "admission_basename": admission_basename,
        "admission_artifact_path": str(artifact_path),
        "admission_packet_path": str(admission_path),
        "seat_certify_ok": seat["ok"],
        "result_payload_status": result_payload_status,
        "deterministic_python_harness_ok": deterministic_harness["ok"],
        "wizard_v43_object_preservation_status": wizard_v43["status"],
        "parent_child_model_swarm_status": swarm["status"],
        "model_quality_swarm_status": quality_swarm["status"],
        "model_quality_accepted_count": quality_swarm.get("accepted_model_count"),
        "cocoindex_grounding_status": cocoindex_grounding["status"],
        "full_wizard_status": full_wizard_obligations["status"],
        "missing_full_wizard_obligations": full_wizard_obligations["missing_obligations"],
        "three_engine_ok": three_engine["ok"],
        "three_engine_schema_gaps": schema_gaps["missing_or_invalid"],
        "stage_gate_ok": stage["ok"],
        "wizard_sim_admission_ok": admission_validation["ok"],
        "wizard_sim_admission_findings": admission_validation.get("parsed", {}).get("findings"),
        "graveyard_status": graveyard.get("status"),
        "claim_ceiling": receipt["claim_ceiling"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if pipeline_completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
