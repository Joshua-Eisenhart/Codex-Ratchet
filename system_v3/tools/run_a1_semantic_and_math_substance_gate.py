#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from zipfile import ZipFile

from a1_selector_warning_snapshot import build_process_warning_snapshot


SIM_CODE_HASH_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+SIM_CODE_HASH_SHA256\s+(\S+)\s*$", re.MULTILINE)
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
PLACEHOLDER_NEGATIVE_CLASS_RE = re.compile(r"^(NEG_)?(BRANCH|ALT|DUMMY|PLACEHOLDER)", re.IGNORECASE)


def _status(flag: bool) -> str:
    return "PASS" if flag else "FAIL"


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_state(run_dir: Path) -> dict:
    path = run_dir / "state.json"
    heavy_path = run_dir / "state.heavy.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    if heavy_path.exists():
        try:
            heavy = json.loads(heavy_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            heavy = {}
        if isinstance(heavy, dict):
            data.update(heavy)
    return data


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _strategy_objs_from_zip_packets(run_dir: Path, *, last_n: int = 12) -> list[dict]:
    zip_dir = run_dir / "zip_packets"
    paths = sorted(zip_dir.glob("*_A1_TO_A0_STRATEGY_ZIP.zip"))[-int(last_n) :]
    out: list[dict] = []
    for path in paths:
        try:
            with ZipFile(path, "r") as zf:
                with zf.open("A1_STRATEGY_v1.json") as fh:
                    obj = json.loads(fh.read().decode("utf-8"))
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out


def _strategy_objs_from_outgoing_or_zip(run_dir: Path, *, last_n: int = 12) -> tuple[list[dict], str]:
    outgoing_dir = run_dir / "a1_sandbox" / "outgoing"
    paths = sorted(outgoing_dir.glob("*_A1_STRATEGY_v1__PACK_SELECTOR.json"))[-int(last_n) :]
    strategy_objs: list[dict] = []
    source_surface = "a1_sandbox_outgoing"
    for path in paths:
        obj = _read_json(path)
        if isinstance(obj, dict):
            strategy_objs.append(obj)
    if strategy_objs:
        return strategy_objs, source_surface
    strategy_objs = _strategy_objs_from_zip_packets(run_dir, last_n=last_n)
    if strategy_objs:
        return strategy_objs, "zip_packets"
    return [], "none"


def _selector_support_metadata_summary(run_dir: Path, *, last_n: int = 12) -> dict:
    strategy_objs, source_surface = _strategy_objs_from_outgoing_or_zip(run_dir, last_n=last_n)
    if not strategy_objs:
        return {
            "strategy_count": 0,
            "source_surface": "none",
            "warning_count": 0,
            "warning_codes": [],
            "warning_categories": [],
            "support_warning_present": False,
            "mining_support_terms": [],
            "mining_artifact_input_count": 0,
            "max_mining_negative_pressure_count": 0,
        }

    warnings_seen: list[str] = []
    warning_codes: list[str] = []
    warning_categories: list[str] = []
    mining_terms: list[str] = []
    mining_artifact_inputs: set[str] = set()
    max_negative_pressure = 0
    max_warning_count = 0
    support_warning_present = False

    for strategy in strategy_objs:
        if not isinstance(strategy, dict):
            continue
        admissibility = strategy.get("admissibility", {}) if isinstance(strategy.get("admissibility", {}), dict) else {}
        process_audit = admissibility.get("process_audit", {}) if isinstance(admissibility.get("process_audit", {}), dict) else {}
        raw_warnings = process_audit.get("warnings", []) if isinstance(process_audit.get("warnings", []), list) else []
        for raw in raw_warnings:
            msg = str(raw).strip()
            if msg and msg not in warnings_seen:
                warnings_seen.append(msg)
        raw_warning_codes = process_audit.get("warning_codes", []) if isinstance(process_audit.get("warning_codes", []), list) else []
        for raw in raw_warning_codes:
            code = str(raw).strip()
            if code and code not in warning_codes:
                warning_codes.append(code)
        raw_warning_categories = process_audit.get("warning_categories", []) if isinstance(process_audit.get("warning_categories", []), list) else []
        for raw in raw_warning_categories:
            category = str(raw).strip()
            if category and category not in warning_categories:
                warning_categories.append(category)
        try:
            warning_count = int(process_audit.get("warning_count", 0) or 0)
        except Exception:
            warning_count = 0
        if warning_count > max_warning_count:
            max_warning_count = warning_count
        fallback_snapshot = build_process_warning_snapshot(raw_warnings)
        fallback_warning_codes = fallback_snapshot.get("warning_codes", []) if isinstance(fallback_snapshot.get("warning_codes", []), list) else []
        for raw in fallback_warning_codes:
            code = str(raw).strip()
            if code and code not in warning_codes:
                warning_codes.append(code)
        fallback_warning_categories = fallback_snapshot.get("warning_categories", []) if isinstance(fallback_snapshot.get("warning_categories", []), list) else []
        for raw in fallback_warning_categories:
            category = str(raw).strip()
            if category and category not in warning_categories:
                warning_categories.append(category)
        try:
            fallback_warning_count = int(fallback_snapshot.get("warning_count", 0) or 0)
        except Exception:
            fallback_warning_count = 0
        if fallback_warning_count > max_warning_count:
            max_warning_count = fallback_warning_count
        if (
            bool(process_audit.get("support_warning_present", False))
            or "noncanon_mining_support_only" in warning_codes
            or "support_boundary" in warning_categories
            or bool(fallback_snapshot.get("support_warning_present", False))
        ):
            support_warning_present = True
        for raw in (process_audit.get("mining_support_terms", []) or []):
            term = str(raw).strip()
            if term and term not in mining_terms:
                mining_terms.append(term)
        for raw in (process_audit.get("mining_artifact_inputs", []) or []):
            value = str(raw).strip()
            if value:
                mining_artifact_inputs.add(value)
        try:
            negative_pressure = int(process_audit.get("mining_negative_pressure_count", 0) or 0)
        except Exception:
            negative_pressure = 0
        if negative_pressure > max_negative_pressure:
            max_negative_pressure = negative_pressure

    return {
        "strategy_count": len(strategy_objs),
        "source_surface": source_surface,
        "warning_count": max(len(warnings_seen), int(max_warning_count)),
        "warning_codes": warning_codes,
        "warning_categories": warning_categories,
        "support_warning_present": support_warning_present,
        "mining_support_terms": mining_terms,
        "mining_artifact_input_count": len(mining_artifact_inputs),
        "max_mining_negative_pressure_count": max_negative_pressure,
    }


def _flatten_sim_rows(state: dict) -> list[dict]:
    out: list[dict] = []
    sim_results = state.get("sim_results", {}) or {}
    if not isinstance(sim_results, dict):
        return out
    for rows in sim_results.values():
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                out.append(row)
    return out


def _collect_sim_code_hashes(state: dict) -> list[str]:
    out: list[str] = []
    survivors = state.get("survivor_ledger", {}) or {}
    if not isinstance(survivors, dict):
        return out
    for row in survivors.values():
        if not isinstance(row, dict):
            continue
        item_text = str(row.get("item_text", ""))
        for m in SIM_CODE_HASH_RE.finditer(item_text):
            out.append(m.group(1).strip().lower())
    return out


def _canonical_term_count(state: dict) -> int:
    term_registry = state.get("term_registry", {}) or {}
    if not isinstance(term_registry, dict):
        return 0
    return sum(
        1
        for row in term_registry.values()
        if isinstance(row, dict) and str(row.get("state", "")).strip() == "CANONICAL_ALLOWED"
    )


def _run_check(
    *,
    run_dir: Path,
    phase: str,
    recent_semantic_rows: int,
    required_probe_terms: list[str],
    min_canonical_terms: int,
    min_graveyard_count: int,
    min_unique_probe_terms: int,
    max_fallback_probe_fraction: float,
) -> dict:
    state = _load_state(run_dir)
    state_loaded = bool(state)

    sim_rows = _flatten_sim_rows(state)
    total_sim_rows = len(sim_rows)
    semantic_rows = [
        row
        for row in sim_rows
        if str(row.get("target_class", "")).strip() != "TC_ATOMIC_TERM_BOOTSTRAP"
    ]
    if int(recent_semantic_rows) > 0 and len(semantic_rows) > int(recent_semantic_rows):
        semantic_rows = semantic_rows[-int(recent_semantic_rows) :]
    semantic_sim_rows = len(semantic_rows)
    probe_terms_seen = {
        str(row.get("probe_term", "")).strip().lower()
        for row in sim_rows
        if str(row.get("probe_term", "")).strip()
    }
    probe_terms_seen.discard("none")
    unique_probe_terms = len(probe_terms_seen)

    fallback_probe_count = sum(
        1
        for row in semantic_rows
        if str(row.get("probe_name", "")).strip() == "no_term_specific_probe"
        or str(row.get("probe_term", "")).strip().lower() == "none"
    )
    fallback_probe_fraction = (fallback_probe_count / semantic_sim_rows) if semantic_sim_rows else 1.0

    required_probe_status = {
        term: (term.lower() in probe_terms_seen) for term in required_probe_terms
    }
    required_probe_missing = sorted([term for term, ok in required_probe_status.items() if not ok])

    sim_registry = state.get("sim_registry", {}) or {}
    negative_classes = [
        str((row or {}).get("negative_class", "")).strip()
        for row in sim_registry.values()
        if isinstance(row, dict) and str((row or {}).get("negative_class", "")).strip()
    ]
    adversarial_negative_count = sum(
        1
        for row in sim_registry.values()
        if isinstance(row, dict)
        and str((row or {}).get("family", "")).strip() == "ADVERSARIAL_NEG"
    )
    placeholder_negative_class_count = sum(
        1 for nc in negative_classes if PLACEHOLDER_NEGATIVE_CLASS_RE.match(nc)
    )
    negative_class_values = sorted(set(negative_classes))

    sim_code_hashes = _collect_sim_code_hashes(state)
    invalid_sim_code_hash_count = sum(1 for h in sim_code_hashes if not HEX64_RE.match(h))
    placeholder_sim_code_hash_count = sum(1 for h in sim_code_hashes if h == ("0" * 64))
    sim_code_hash_value_count = len(sim_code_hashes)
    sim_code_hash_unique_count = len(set(sim_code_hashes))

    canonical_terms = _canonical_term_count(state)
    graveyard = state.get("graveyard", {}) or {}
    graveyard_count = len(graveyard) if isinstance(graveyard, dict) else 0
    kill_log = state.get("kill_log", []) or []
    kill_log_count = len(kill_log) if isinstance(kill_log, list) else 0

    kill_ids = {
        str(row.get("id", "")).strip()
        for row in kill_log
        if isinstance(row, dict) and str(row.get("id", "")).strip()
    }
    graveyard_ids = set(graveyard.keys()) if isinstance(graveyard, dict) else set()
    graveyard_kill_overlap_count = len(kill_ids.intersection(graveyard_ids))
    selector_support = _selector_support_metadata_summary(run_dir)

    phase_norm = str(phase).strip().lower()
    strict_semantic = phase_norm != "graveyard_fill"

    checks = [
        {
            "check_id": "STATE_LOADED",
            "status": _status(state_loaded),
            "detail": f"state_loaded={state_loaded}",
        },
        {
            "check_id": "CANONICAL_TERM_DEPTH",
            "status": _status((canonical_terms >= min_canonical_terms) if strict_semantic else True),
            "detail": (
                f"canonical_terms={canonical_terms} min_required={min_canonical_terms}"
                if strict_semantic
                else f"SKIP_BY_PHASE phase={phase_norm} canonical_terms={canonical_terms}"
            ),
        },
        {
            "check_id": "REAL_PROBE_DIVERSITY",
            "status": _status((unique_probe_terms >= min_unique_probe_terms) if strict_semantic else True),
            "detail": (
                f"unique_probe_terms={unique_probe_terms} min_required={min_unique_probe_terms}"
                if strict_semantic
                else f"SKIP_BY_PHASE phase={phase_norm} unique_probe_terms={unique_probe_terms}"
            ),
        },
        {
            "check_id": "REQUIRED_PROBE_TERMS",
            "status": _status((not required_probe_missing) if strict_semantic else True),
            "detail": (
                (
                    "all required probe terms covered"
                    if not required_probe_missing
                    else f"missing={','.join(required_probe_missing)}"
                )
                if strict_semantic
                else f"SKIP_BY_PHASE phase={phase_norm} required_probe_terms_not_enforced"
            ),
        },
        {
            "check_id": "NO_FALLBACK_PROBE_DOMINANCE",
            "status": _status((fallback_probe_fraction <= max_fallback_probe_fraction) if strict_semantic else True),
            "detail": (
                (
                    f"fallback_probe_fraction={fallback_probe_fraction:.6f} "
                    f"max_allowed={max_fallback_probe_fraction:.6f}"
                )
                if strict_semantic
                else (
                    f"SKIP_BY_PHASE phase={phase_norm} "
                    f"fallback_probe_fraction={fallback_probe_fraction:.6f}"
                )
            ),
        },
        {
            "check_id": "NEGATIVE_CLASS_SPECIFICITY",
            "status": _status(adversarial_negative_count > 0 and placeholder_negative_class_count == 0),
            "detail": (
                f"adversarial_negative_count={adversarial_negative_count} "
                f"placeholder_negative_class_count={placeholder_negative_class_count}"
            ),
        },
        {
            "check_id": "SIM_CODE_HASH_VALIDITY",
            "status": _status(
                sim_code_hash_value_count > 0
                and invalid_sim_code_hash_count == 0
                and placeholder_sim_code_hash_count == 0
            ),
            "detail": (
                f"sim_code_hash_values={sim_code_hash_value_count} "
                f"invalid={invalid_sim_code_hash_count} "
                f"all_zero={placeholder_sim_code_hash_count}"
            ),
        },
        {
            "check_id": "GRAVEYARD_PRESSURE_REAL",
            "status": _status(
                graveyard_count >= min_graveyard_count
                and kill_log_count >= graveyard_count
                and graveyard_kill_overlap_count > 0
            ),
            "detail": (
                f"graveyard_count={graveyard_count} min_required={min_graveyard_count} "
                f"kill_log_count={kill_log_count} overlap={graveyard_kill_overlap_count}"
            ),
        },
    ]

    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    return {
        "schema": "A1_SEMANTIC_AND_MATH_SUBSTANCE_GATE_REPORT_v1",
        "run_id": run_dir.name,
        "phase": phase_norm,
        "status": status,
        "checks": checks,
        "metrics": {
            "canonical_term_count": canonical_terms,
            "total_sim_rows": total_sim_rows,
            "semantic_sim_rows": semantic_sim_rows,
            "recent_semantic_rows_window": int(recent_semantic_rows),
            "atomic_bootstrap_sim_rows_excluded": max(0, total_sim_rows - semantic_sim_rows),
            "unique_probe_terms": unique_probe_terms,
            "fallback_probe_count": fallback_probe_count,
            "fallback_probe_fraction": round(fallback_probe_fraction, 8),
            "required_probe_terms": required_probe_terms,
            "required_probe_missing": required_probe_missing,
            "adversarial_negative_count": adversarial_negative_count,
            "negative_class_values": negative_class_values,
            "placeholder_negative_class_count": placeholder_negative_class_count,
            "sim_code_hash_value_count": sim_code_hash_value_count,
            "sim_code_hash_unique_count": sim_code_hash_unique_count,
            "invalid_sim_code_hash_count": invalid_sim_code_hash_count,
            "placeholder_sim_code_hash_count": placeholder_sim_code_hash_count,
            "selector_support_strategy_count": selector_support.get("strategy_count", 0),
            "selector_support_source_surface": selector_support.get("source_surface", "none"),
            "selector_warning_count": selector_support.get("warning_count", 0),
            "selector_warning_codes": selector_support.get("warning_codes", []),
            "selector_warning_categories": selector_support.get("warning_categories", []),
            "selector_support_warning_present": bool(selector_support.get("support_warning_present", False)),
            "selector_mining_support_terms": selector_support.get("mining_support_terms", []),
            "selector_mining_artifact_input_count": selector_support.get("mining_artifact_input_count", 0),
            "selector_max_mining_negative_pressure_count": selector_support.get("max_mining_negative_pressure_count", 0),
            "graveyard_count": graveyard_count,
            "kill_log_count": kill_log_count,
            "graveyard_kill_overlap_count": graveyard_kill_overlap_count,
        },
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate whether a run shows real A1 semantic/math substance.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument(
        "--phase",
        choices=["mixed", "graveyard_fill", "recovery"],
        default="mixed",
        help="graveyard_fill relaxes semantic-coverage checks while the run is intentionally fill-first.",
    )
    parser.add_argument(
        "--recent-semantic-rows",
        type=int,
        default=0,
        help="If >0, evaluate semantic checks on the most recent N semantic sim rows.",
    )
    parser.add_argument("--min-canonical-terms", type=int, default=10)
    parser.add_argument("--min-graveyard-count", type=int, default=10)
    parser.add_argument("--min-unique-probe-terms", type=int, default=8)
    parser.add_argument("--max-fallback-probe-fraction", type=float, default=0.10)
    parser.add_argument(
        "--required-probe-terms",
        default="density_matrix,cptp_channel,partial_trace,unitary_operator,correlation_polarity,qit_master_conjunction",
        help="Comma-separated list of probe_term values that must be present in sim_results.",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    required_probe_terms = [t.strip() for t in str(args.required_probe_terms).split(",") if t.strip()]

    report = _run_check(
        run_dir=run_dir,
        phase=str(args.phase),
        recent_semantic_rows=int(args.recent_semantic_rows),
        required_probe_terms=required_probe_terms,
        min_canonical_terms=int(args.min_canonical_terms),
        min_graveyard_count=int(args.min_graveyard_count),
        min_unique_probe_terms=int(args.min_unique_probe_terms),
        max_fallback_probe_fraction=float(args.max_fallback_probe_fraction),
    )
    out_path = run_dir / "reports" / "a1_semantic_and_math_substance_gate_report.json"
    _write_json(out_path, report)
    print(json.dumps({"status": report["status"], "report_path": str(out_path)}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
