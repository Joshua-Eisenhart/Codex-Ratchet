#!/usr/bin/env python3
"""Build a conservative QIT/engine evidence index from canonical result JSONs."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import receipt_schema
import wizard_sim_admission


QIT_TOKENS = ("qit", "engine", "hopf", "weyl", "spinor", "pauli", "clifford", "density")
EXTERNAL_SCAN_ROOTS = ("system_v4", "system_v5", "runs")
EXTERNAL_SCAN_SAMPLE_LIMIT = 50
TRACKED_ENTRY_SAMPLE_LIMIT = 100
TRACKED_TARGET_SAMPLE_LIMIT = 200
LATE_STAGE_RESULT_TOKENS = (
    "axis",
    "bridge",
    "coexistence",
    "coupling",
    "emergence",
    "engine",
    "pairwise",
    "triple",
)

def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def has_qit_signal(path: Path, payload: dict[str, Any]) -> bool:
    haystack = " ".join(
        [
            path.stem.lower(),
            str(payload.get("name", "")).lower(),
            str(payload.get("claim_ceiling", "")).lower(),
            str(payload.get("promotion_condition", "")).lower(),
            str(payload.get("blocked_until", "")).lower(),
            " ".join(map(str, payload.get("out_of_scope") or [])).lower(),
        ]
    )
    return any(token in haystack for token in QIT_TOKENS)


def payload_name(path: Path, payload: dict[str, Any]) -> str:
    stem = path.stem.removesuffix("_results").removesuffix("_result")
    return str(payload.get("name") or stem)


def result_basename(path: Path) -> str:
    return path.stem.removesuffix("_results").removesuffix("_result")


def evidence_basename(root: Path, path: Path, payload: dict[str, Any]) -> str:
    stem = result_basename(path)
    if source_path_for(root, stem).exists():
        return stem
    name = payload_name(path, payload)
    if name != stem and source_path_for(root, name).exists():
        return name
    return stem


def has_receipt_schema(payload: dict[str, Any]) -> bool:
    return bool(payload.get("tool_manifest") or payload.get("TOOL_MANIFEST")) and bool(
        payload.get("tool_integration_depth") or payload.get("TOOL_INTEGRATION_DEPTH")
    )


def load_bearing_depths(payload: dict[str, Any]) -> dict[str, str]:
    depths = payload.get("tool_integration_depth") or payload.get("TOOL_INTEGRATION_DEPTH") or {}
    if not isinstance(depths, dict):
        return {}
    return {
        str(tool): str(depth)
        for tool, depth in depths.items()
        if str(depth) == "load_bearing"
    }


def tool_role_sources(payload: dict[str, Any]) -> dict[str, str]:
    manifest = payload.get("tool_manifest") or payload.get("TOOL_MANIFEST") or {}
    raw = payload.get("tool_role_source") or payload.get("TOOL_ROLE_SOURCE") or {}
    role_sources: dict[str, str] = {}
    if isinstance(raw, dict):
        role_sources.update(
            {
                str(tool): str(source).strip().lower().replace("_", "-")
                for tool, source in raw.items()
            }
        )
    if isinstance(manifest, dict):
        for tool, entry in manifest.items():
            if not isinstance(entry, dict):
                continue
            source = (
                entry.get("role_source")
                or entry.get("tool_role_source")
                or entry.get("integration_source")
            )
            if source:
                role_sources.setdefault(str(tool), str(source).strip().lower().replace("_", "-"))
                continue
            reason = str(entry.get("reason") or "").lower()
            if "transitive" in reason or "through enginecore" in reason or "through engine_core" in reason:
                role_sources.setdefault(str(tool), "transitive")
    return role_sources


def local_load_bearing_depths(payload: dict[str, Any]) -> dict[str, str]:
    role_sources = tool_role_sources(payload)
    local_depths: dict[str, str] = {}
    for tool, depth in load_bearing_depths(payload).items():
        source = role_sources.get(tool) or role_sources.get(canonical_tool_name(tool))
        if source in {"transitive", "upstream", "imported", "delegated", "engine-core", "engine_core"}:
            continue
        local_depths[tool] = depth
    return local_depths


def canonical_tool_name(tool: str) -> str:
    return receipt_schema.canonical_tool_name(tool)


def normalized_execution_kind(payload: dict[str, Any]) -> str:
    value = payload.get("sim_execution_kind") or payload.get("SIM_EXECUTION_KIND")
    summary = payload.get("summary")
    if not value and isinstance(summary, dict):
        value = summary.get("sim_execution_kind") or summary.get("SIM_EXECUTION_KIND")
    normalized = receipt_schema.normalized_execution_kind(value)
    if normalized == "bridge":
        return "bridge"
    return normalized


def execution_kind_optional_for_micro(path: Path, payload: dict[str, Any]) -> bool:
    """Allow pure micro/capability rows to stay below bridge/nonclassical claims."""
    claim = str(payload.get("claim_ceiling") or "").strip().lower()
    haystack = " ".join(
        [
            path.stem.lower(),
            str(payload.get("name") or "").lower(),
            claim,
            str(payload.get("promotion_condition") or "").lower(),
            str(payload.get("blocked_until") or "").lower(),
        ]
    )
    return claim == "qit_micro_only" or any(
        token in haystack
        for token in (
            "tool_micro",
            "capability_only",
            "_capability",
        )
    )


def tool_policy_blockers(payload: dict[str, Any]) -> list[str]:
    execution_kind = normalized_execution_kind(payload)
    load_bearing = {canonical_tool_name(tool) for tool in load_bearing_depths(payload)}
    local_load_bearing = {canonical_tool_name(tool) for tool in local_load_bearing_depths(payload)}
    blockers: list[str] = []
    if execution_kind in {"bridge", "nonclassical"} and "numpy" in load_bearing:
        blockers.append("result:numpy_load_bearing_blocked_for_bridge_or_nonclassical")
    if execution_kind == "nonclassical" and "pytorch" not in local_load_bearing:
        blockers.append("result:nonclassical_requires_local_load_bearing_pytorch")
    return blockers


def execution_kind_blockers(path: Path, payload: dict[str, Any]) -> list[str]:
    if (
        payload.get("classification") == "canonical"
        and has_qit_signal(path, payload)
        and not normalized_execution_kind(payload)
        and not execution_kind_optional_for_micro(path, payload)
    ):
        return ["result:qit_execution_kind_missing"]
    return []


def source_path_for(root: Path, basename: str) -> Path:
    return root / "system_v4" / "probes" / f"{basename}.py"


def is_result_json(path: Path) -> bool:
    return path.name.endswith("_results.json") or path.name.endswith("_result.json")


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def external_triage_for(root: Path, path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    name = payload_name(path, payload)
    basename = evidence_basename(root, path, payload)
    classification = str(payload.get("classification") or "")
    lower = f"{relpath(root, path)} {name}".lower()
    source_path = source_path_for(root, basename)
    source_exists = source_path.exists()
    source_newer_than_result = False
    if source_exists:
        try:
            source_newer_than_result = source_path.stat().st_mtime > path.stat().st_mtime
        except OSError:
            source_newer_than_result = False
    late_stage_tokens = [token for token in LATE_STAGE_RESULT_TOKENS if token in lower]
    receipt_schema_present = has_receipt_schema(payload)
    load_bearing = load_bearing_depths(payload)
    policy_blockers = tool_policy_blockers(payload)
    if policy_blockers:
        if source_exists:
            bucket = "source_bound_contract_repair_candidate"
            next_action = "repair_tool_policy_before_any_admission"
        else:
            bucket = "source_unbound_tool_policy_quarantine"
            next_action = "quarantine_reference_only_bind_or_recreate_source_before_tool_repair"
    elif classification == "classical_baseline":
        bucket = "classical_baseline_reference_only"
        next_action = "do_not_promote_use_only_as_classical_reference_or_rerun_as_new_micro_if_needed"
    elif late_stage_tokens:
        bucket = "late_stage_or_coupling_blocked"
        next_action = "do_not_promote_extract_smaller_tool_or_geometry_micro_probe"
    elif classification == "canonical" and source_exists and source_newer_than_result:
        bucket = "source_bound_repaired_source_rerun_candidate"
        next_action = "rerun_repaired_source_under_canonical_micro_result_surface"
    elif classification == "canonical" and source_exists and receipt_schema_present and load_bearing:
        bucket = "source_bound_micro_rerun_candidate"
        next_action = "rerun_under_canonical_micro_result_surface_then_create_strict_admission"
    elif classification == "canonical" and source_exists:
        bucket = "source_bound_contract_repair_candidate"
        next_action = "repair_micro_contract_then_rerun_under_canonical_result_surface"
    elif classification == "canonical":
        bucket = "canonical_but_source_unbound"
        next_action = "bind_or_recreate_source_before_any_admission"
    else:
        bucket = "unclassified_or_legacy_shape"
        next_action = "inspect_then_rebuild_as_new_micro_probe_if_still_useful"
    return {
        "path": relpath(root, path),
        "basename": basename,
        "name": name,
        "classification": classification,
        "bucket": bucket,
        "next_action": next_action,
        "source_path": relpath(root, source_path) if source_exists else None,
        "source_exists": source_exists,
        "source_newer_than_result": source_newer_than_result,
        "late_stage_tokens": late_stage_tokens,
        "receipt_schema_present": receipt_schema_present,
        "load_bearing_depths": load_bearing,
        "sim_execution_kind": normalized_execution_kind(payload) or None,
        "tool_policy_blockers": policy_blockers,
    }


def external_qit_result_scan(
    root: Path,
    canonical_results_dir: Path,
    *,
    admitted_basenames: set[str] | None = None,
) -> dict[str, Any]:
    """Find QIT-like result receipts outside the current admissible result surface.

    These paths are diagnostics only. They are not admission candidates until a
    separate runner/admission path moves or recreates them under the canonical
    result surface and satisfies the sim contract.
    """
    admitted_basenames = admitted_basenames or set()
    external_result_count = 0
    external_qit_signal_count = 0
    sample: list[dict[str, str]] = []
    triage_samples: dict[str, list[dict[str, Any]]] = {}
    triage_counts: dict[str, int] = {}
    provisional_rerun_targets: list[dict[str, Any]] = []
    scanned_roots: list[str] = []
    for root_name in EXTERNAL_SCAN_ROOTS:
        scan_root = root / root_name
        if not scan_root.exists():
            continue
        scanned_roots.append(root_name)
        for path in sorted(scan_root.rglob("*.json")):
            if not is_result_json(path):
                continue
            try:
                path.relative_to(canonical_results_dir)
                continue
            except ValueError:
                pass
            external_result_count += 1
            payload = load_json(path)
            if not has_qit_signal(path, payload):
                continue
            external_qit_signal_count += 1
            triage = external_triage_for(root, path, payload)
            if triage["basename"] in admitted_basenames or triage["name"] in admitted_basenames:
                triage["bucket"] = "already_admitted_duplicate_reference"
                triage["next_action"] = "do_not_rerun_already_accepted_canonical_evidence"
            bucket = triage["bucket"]
            triage_counts[bucket] = triage_counts.get(bucket, 0) + 1
            triage_samples.setdefault(bucket, [])
            if len(triage_samples[bucket]) < 10:
                triage_samples[bucket].append(triage)
            if bucket in {
                "source_bound_micro_rerun_candidate",
                "source_bound_contract_repair_candidate",
                "source_bound_repaired_source_rerun_candidate",
            }:
                provisional_rerun_targets.append(triage)
            if len(sample) < EXTERNAL_SCAN_SAMPLE_LIMIT:
                sample.append(
                    {
                        "path": relpath(root, path),
                        "name": payload_name(path, payload),
                        "classification": str(payload.get("classification") or ""),
                    }
                )
    provisional_rerun_targets.sort(key=lambda item: (item["bucket"], item["path"]))
    status = "out_of_scope_qit_like_results_present" if external_qit_signal_count else "no_out_of_scope_qit_like_results"
    return {
        "status": status,
        "scanned_roots": scanned_roots,
        "external_result_count": external_result_count,
        "external_qit_signal_count": external_qit_signal_count,
        "sample_limit": EXTERNAL_SCAN_SAMPLE_LIMIT,
        "sample": sample,
        "triage": {
            "bucket_counts": triage_counts,
            "bucket_samples": triage_samples,
            "provisional_rerun_target_count": len(provisional_rerun_targets),
            "provisional_rerun_targets": provisional_rerun_targets[:20],
            "triage_boundary": "diagnostic_only_targets_require_canonical_rerun_and_strict_admission",
        },
        "admission_boundary": "diagnostic_only_not_accepted_evidence",
    }


def skipped_external_scan() -> dict[str, Any]:
    return {
        "status": "external_scan_skipped",
        "scanned_roots": [],
        "external_result_count": 0,
        "external_qit_signal_count": 0,
        "sample_limit": EXTERNAL_SCAN_SAMPLE_LIMIT,
        "sample": [],
        "triage": {
            "bucket_counts": {},
            "bucket_samples": {},
            "provisional_rerun_target_count": 0,
            "provisional_rerun_targets": [],
            "triage_boundary": "external_scan_skipped_run_without_skip_external_scan_for_diagnostics",
        },
        "admission_boundary": "diagnostic_only_not_accepted_evidence",
    }


def build_index(root: Path | None = None, *, include_external_scan: bool = True) -> dict[str, Any]:
    root = root or repo_root()
    results_dir = root / "system_v4" / "probes" / "a2_state" / "sim_results"
    entries: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    targets: list[dict[str, Any]] = []
    if not results_dir.exists():
        result_paths: list[Path] = []
    else:
        result_paths = sorted(results_dir.glob("*_results.json"))
    scanned_result_count = len(result_paths)
    scanned_result_sample = [path.name for path in result_paths[:20]]
    qit_signal_result_count = 0
    qit_signal_result_sample: list[str] = []

    for result_path in result_paths:
        payload = load_json(result_path)
        if not has_qit_signal(result_path, payload):
            continue
        qit_signal_result_count += 1
        if len(qit_signal_result_sample) < 20:
            qit_signal_result_sample.append(result_path.name)
        basename = evidence_basename(root, result_path, payload)
        result_name = payload_name(result_path, payload)
        sim_path = source_path_for(root, basename)
        blockers: list[str] = []
        receipt_schema_ok = has_receipt_schema(payload)
        receipt_validation = receipt_schema.validate_result_path(
            result_path,
            root=root,
            strict_scope=True,
            require_executable=True,
            require_run_boundary=True,
        )
        if not receipt_schema_ok:
            blockers.append("result:receipt_schema_incomplete")
        for finding in receipt_validation.get("hard_findings") or []:
            kind = finding.get("kind")
            if kind:
                blockers.append(f"result:{kind}")
        blockers.extend(execution_kind_blockers(result_path, payload))
        if payload.get("classification") != "canonical":
            blockers.append("result:result_classification_not_canonical")

        admission = wizard_sim_admission.load_and_validate(
            root=root,
            basename=basename,
            sim_path=f"system_v4/probes/{basename}.py",
            expected_result_path=result_path,
        )
        admission_status = "admitted" if admission.get("ok") else "missing_or_invalid"
        for finding in admission.get("findings") or []:
            blockers.append(f"admission:{finding}")

        status = "accepted" if not blockers else "blocked"
        admission_path = admission.get("path") if admission_status == "admitted" else None
        admission_payload = load_json(Path(admission_path)) if admission_path else {}
        contract = admission_payload.get("packet_contract") or {}
        entry = {
            "basename": basename,
            "result_name": result_name,
            "result_path": str(result_path),
            "result_sha256": sha256(result_path),
            "receipt_schema_ok": receipt_schema_ok,
            "receipt_validation_ok": bool(receipt_validation.get("ok")),
            "receipt_validation_hard_findings": [
                finding.get("kind")
                for finding in receipt_validation.get("hard_findings") or []
                if finding.get("kind")
            ],
            "status": status,
            "admission_status": admission_status,
            "admission_artifact": admission_path,
            "blockers": sorted(set(blockers)),
            "parent_receipt_sha256": contract.get("parent_receipt_sha256") or {},
            "tool_function_ancestry": {
                "tool_target": contract.get("tool_target"),
                "function_surface": contract.get("function_surface"),
            },
        }
        entries.append(entry)
        if status == "accepted":
            candidates.append(entry)
        else:
            quarantine.append(entry)
            if payload.get("classification") != "canonical":
                action = "do_not_promote_reclassify_or_replace_with_canonical_qit_result"
            elif "admission:nonclassical_suitable_load_bearing_tool_missing" in blockers or str(
                payload.get("claim_ceiling") or ""
            ) in {
                "tool_micro_scipy_capability_only",
                "tool_micro_sympy_capability_only",
            }:
                action = "do_not_promote_use_as_classical_or_bridge_tool_reference_only"
            elif any(blocker.startswith("result:numpy_load_bearing") or blocker.startswith("result:nonclassical_requires") for blocker in blockers) and not sim_path.exists():
                action = "quarantine_reference_only_bind_or_recreate_source_before_tool_repair"
            elif any(blocker.startswith("result:numpy_load_bearing") or blocker.startswith("result:nonclassical_requires") for blocker in blockers):
                action = "repair_tool_policy_before_any_admission"
            elif not sim_path.exists():
                action = "repair_or_bind_source_probe_before_admission"
            else:
                action = "create_or_repair_wizard_sim_admission"
            targets.append(
                {
                    "basename": basename,
                    "sim_path": f"system_v4/probes/{basename}.py" if sim_path.exists() else None,
                    "result_path": str(result_path),
                    "next_action": action,
                }
            )

    if include_external_scan:
        external_scan = external_qit_result_scan(
            root,
            results_dir,
            admitted_basenames={entry["basename"] for entry in candidates},
        )
    else:
        external_scan = skipped_external_scan()
    targets.sort(key=lambda item: (item.get("sim_path") is None, item["basename"]))
    accepted = len(candidates)
    summary = {
        "scanned_result_count": scanned_result_count,
        "qit_signal_result_count": qit_signal_result_count,
        "total_entries": len(entries),
        "accepted": accepted,
        "admitted_micro_entries": sum(1 for e in entries if e["admission_status"] == "admitted"),
        "candidate_entries": len(candidates),
        "quarantine_entries": len(quarantine),
        "blocked": len(quarantine),
        "missing_or_invalid_admission": sum(1 for e in entries if e["admission_status"] != "admitted"),
    }
    if accepted:
        status_reason = "accepted_qit_entries_present"
    elif entries:
        status_reason = "qit_entries_blocked"
    elif result_paths:
        status_reason = "no_qit_signal_results_indexed"
    else:
        status_reason = "sim_results_dir_missing_or_empty"
    return {
        "summary": summary,
        "operational_status": "has_accepted_qit_entry" if accepted else "blocked_no_accepted_qit_entries",
        "status_reason": status_reason,
        "qit_signal_filter": {
            "tokens": list(QIT_TOKENS),
            "fields": ["result_stem", "name", "claim_ceiling", "promotion_condition", "blocked_until", "out_of_scope"],
        },
        "scan_sample": {
            "scanned_result_files": scanned_result_sample,
            "qit_signal_result_files": qit_signal_result_sample,
            "sample_limit": 20,
        },
        "out_of_scope_qit_result_scan": external_scan,
        "entries": entries,
        "candidate_entries": candidates,
        "quarantine_entries": quarantine,
        "next_acceptance_targets": targets,
    }


def compact_for_tracking(index: dict[str, Any]) -> dict[str, Any]:
    """Keep tracked evidence index bounded while preserving routing counts.

    `build_index()` intentionally returns full rows for local audits and unit
    tests. The checked-in evidence file should stay small enough to review and
    should not grow with every old result receipt restored to disk.
    """
    quarantine_entries = list(index.get("quarantine_entries") or [])
    targets = list(index.get("next_acceptance_targets") or [])
    entries = list(index.get("entries") or [])
    out = dict(index)
    out["entries"] = entries[:TRACKED_ENTRY_SAMPLE_LIMIT]
    out["candidate_entries"] = list(index.get("candidate_entries") or [])
    out["quarantine_entries"] = quarantine_entries[:TRACKED_ENTRY_SAMPLE_LIMIT]
    out["next_acceptance_targets"] = targets[:TRACKED_TARGET_SAMPLE_LIMIT]
    out["tracked_compaction"] = {
        "full_audit_command": "scripts/qit_engine_evidence_index.py --include-entries",
        "entry_sample_limit": TRACKED_ENTRY_SAMPLE_LIMIT,
        "target_sample_limit": TRACKED_TARGET_SAMPLE_LIMIT,
        "full_entry_count": len(entries),
        "full_quarantine_entry_count": len(quarantine_entries),
        "full_next_acceptance_target_count": len(targets),
        "boundary": "tracked_index_is_bounded_sample_full_index_available_on_rerun",
    }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--out")
    parser.add_argument("--require-accepted", action="store_true")
    parser.add_argument(
        "--skip-external-scan",
        action="store_true",
        help="Skip diagnostic scan across system_v4/system_v5/runs and refresh only the canonical QIT result surface.",
    )
    parser.add_argument(
        "--include-entries",
        action="store_true",
        help="Write the full entry/target lists instead of the bounded tracked sample.",
    )
    args = parser.parse_args()
    index = build_index(Path(args.repo_root), include_external_scan=not args.skip_external_scan)
    output_index = index if args.include_entries else compact_for_tracking(index)
    text = json.dumps(output_index, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 1 if args.require_accepted and index["summary"]["accepted"] == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
