from __future__ import annotations

from collections.abc import Mapping


_WARNING_META_BY_MESSAGE: dict[str, tuple[str, str]] = {
    "wiggle minimum content is incomplete: targets, alternatives, and both positive/negative sim lanes should be present": (
        "minimum_content_incomplete",
        "content_shape",
    ),
    "residue/load is dominating strategy output; do not treat term volume as movement": (
        "movement_over_throughput_failed",
        "content_balance",
    ),
    "non-head material is still too close to executable promotion lanes": (
        "evidence_gated_promotion_failed",
        "promotion_boundary",
    ),
    "sim evidence boundary is weak: strategy is not carrying a clear positive/negative sims split": (
        "sim_boundary_weak",
        "sim_boundary",
    ),
    "sim evidence is not hash-anchored by either inputs.evidence_summary_hash or state-backed sim digest": (
        "sim_evidence_not_hash_anchored",
        "sim_provenance",
    ),
    "selector used transient cold-core fallback; regenerate run-local cold_core when possible": (
        "transient_cold_core_fallback",
        "cold_core_provenance",
    ),
    "selector used external cold-core path; run-local regeneration provenance is bypassed": (
        "external_cold_core_path",
        "cold_core_provenance",
    ),
    "explicit cold-core basename sequence mismatches payload sequence; provenance may reflect a renamed or swapped artifact": (
        "cold_core_basename_sequence_mismatch",
        "cold_core_sequence",
    ),
    "selector output sequence differs from cold-core payload sequence; direct caller override may have split regeneration provenance": (
        "selector_cold_core_sequence_mismatch",
        "cold_core_sequence",
    ),
    "target scope clamp is narrower than family role context; use target_terms for local selection and admissibility for surrounding family context": (
        "target_scope_family_context_split",
        "scope_boundary",
    ),
    "noncanon mining witnesses are present; keep them support-side and do not treat them as executable head authority": (
        "noncanon_mining_support_only",
        "support_boundary",
    ),
}


def _infer_warning_meta(message: str) -> tuple[str, str]:
    exact = _WARNING_META_BY_MESSAGE.get(message)
    if exact is not None:
        return exact
    if "pack selector reported sequence" in message:
        return ("pack_selector_reported_sequence_mismatch", "cold_core_sequence")
    if "selector output sequence differs" in message:
        return ("selector_cold_core_sequence_mismatch", "cold_core_sequence")
    if "basename sequence" in message:
        return ("cold_core_basename_sequence_mismatch", "cold_core_sequence")
    if "cold-core" in message or "provenance" in message or "external path" in message:
        return ("external_cold_core_path", "cold_core_provenance")
    return ("uncategorized_warning", "uncategorized")


def _dedup_strings(values: list[str] | tuple[str, ...] | None) -> list[str]:
    out: list[str] = []
    for raw in values or []:
        value = str(raw).strip()
        if value and value not in out:
            out.append(value)
    return out


def extract_selector_warning_fields(row: Mapping[str, object]) -> dict:
    raw_warnings = row.get("selector_process_warnings", [])
    warnings = _dedup_strings(raw_warnings if isinstance(raw_warnings, list) else [])
    raw_warning_codes = row.get("selector_warning_codes", [])
    warning_codes = _dedup_strings(raw_warning_codes if isinstance(raw_warning_codes, list) else [])
    raw_warning_categories = row.get("selector_warning_categories", [])
    warning_categories = _dedup_strings(raw_warning_categories if isinstance(raw_warning_categories, list) else [])
    raw_warning_examples = row.get("selector_warning_examples", [])
    warning_examples = _dedup_strings(raw_warning_examples if isinstance(raw_warning_examples, list) else [])
    summary = str(row.get("selector_warning_summary", "") or "").strip()
    try:
        warning_count = int(row.get("selector_warning_count", 0) or 0)
    except Exception:
        warning_count = 0
    support_warning_present = bool(row.get("selector_support_warning_present", False))
    out: dict = {
        "selector_process_warnings": warnings,
        "selector_warning_codes": warning_codes,
        "selector_warning_categories": warning_categories,
        "selector_warning_examples": warning_examples,
        "selector_support_warning_present": support_warning_present,
        "selector_warning_count": int(warning_count),
    }
    if summary:
        out["selector_warning_summary"] = summary
    return out


def build_selector_provenance_fields(
    *,
    cold_core_path: str = "",
    cold_core_source: str = "",
    cold_core_path_class: str = "",
    cold_core_sha256: str = "",
    cold_core_sequence: int | str = 0,
    cold_core_sequence_mismatch_stage: str = "",
    selector_prefixed: bool = True,
) -> dict:
    selector_cold_core_path = str(cold_core_path or "").strip()
    selector_cold_core_source = str(cold_core_source or "").strip()
    selector_cold_core_path_class = str(cold_core_path_class or "").strip()
    selector_cold_core_sha256 = str(cold_core_sha256 or "").strip()
    try:
        selector_cold_core_sequence = int(cold_core_sequence or 0)
    except Exception:
        selector_cold_core_sequence = 0
    mismatch_stage = str(cold_core_sequence_mismatch_stage or "").strip()
    prefix = "selector_" if selector_prefixed else ""
    out: dict = {}
    if selector_cold_core_path:
        out[f"{prefix}cold_core_path"] = selector_cold_core_path
    if selector_cold_core_source:
        out[f"{prefix}cold_core_source"] = selector_cold_core_source
    if selector_cold_core_path_class:
        out[f"{prefix}cold_core_path_class"] = selector_cold_core_path_class
    if selector_cold_core_sha256:
        out[f"{prefix}cold_core_sha256"] = selector_cold_core_sha256
    if selector_cold_core_sequence > 0:
        out[f"{prefix}cold_core_sequence"] = int(selector_cold_core_sequence)
    if mismatch_stage:
        out["cold_core_sequence_mismatch_stage"] = mismatch_stage
    return out


def extract_selector_provenance_fields(row: Mapping[str, object]) -> dict:
    return build_selector_provenance_fields(
        cold_core_path=str(
            row.get("selector_cold_core_path") or row.get("cold_core_path") or ""
        ),
        cold_core_source=str(
            row.get("selector_cold_core_source") or row.get("cold_core_source") or ""
        ),
        cold_core_path_class=str(
            row.get("selector_cold_core_path_class") or row.get("cold_core_path_class") or ""
        ),
        cold_core_sha256=str(
            row.get("selector_cold_core_sha256") or row.get("cold_core_sha256") or ""
        ),
        cold_core_sequence=row.get(
            "selector_cold_core_sequence", row.get("cold_core_sequence", 0)
        ),
        cold_core_sequence_mismatch_stage=str(
            row.get("cold_core_sequence_mismatch_stage", "") or ""
        ),
        selector_prefixed=True,
    )


def _warning_priority(category: str, code: str) -> int:
    cat = str(category).strip()
    cod = str(code).strip()
    if cat == "cold_core_sequence" or cod in {
        "cold_core_basename_sequence_mismatch",
        "selector_cold_core_sequence_mismatch",
        "pack_selector_reported_sequence_mismatch",
    }:
        return 0
    if cat == "cold_core_provenance":
        return 1
    if cat == "support_boundary":
        return 2
    if cat == "scope_boundary":
        return 3
    return 4


def _warning_details_from_inputs(
    warnings: list[str],
    warning_codes: list[str],
    warning_categories: list[str],
    warning_details: list[dict] | None,
) -> list[dict]:
    out: list[dict] = []
    seen_messages: set[str] = set()
    if isinstance(warning_details, list) and warning_details:
        for raw in warning_details:
            if not isinstance(raw, Mapping):
                continue
            message = str(raw.get("message", "")).strip()
            if not message or message in seen_messages:
                continue
            code = str(raw.get("code", "")).strip()
            category = str(raw.get("category", "")).strip()
            if not code or not category:
                fallback_code, fallback_category = _infer_warning_meta(message)
                code = code or fallback_code
                category = category or fallback_category
            out.append({"message": message, "code": code, "category": category})
            seen_messages.add(message)
        if out:
            return out
    if warnings and len(warnings) == len(warning_codes) == len(warning_categories):
        for idx, message in enumerate(warnings):
            if message in seen_messages:
                continue
            code = str(warning_codes[idx]).strip()
            category = str(warning_categories[idx]).strip()
            if not code or not category:
                code, category = _infer_warning_meta(message)
            out.append({"message": message, "code": code, "category": category})
            seen_messages.add(message)
        if out:
            return out
    for message in warnings:
        if message in seen_messages:
            continue
        code, category = _infer_warning_meta(message)
        out.append({"message": message, "code": code, "category": category})
        seen_messages.add(message)
    return out


def build_process_warning_snapshot(
    warnings: list[str] | None,
    *,
    warning_codes: list[str] | None = None,
    warning_categories: list[str] | None = None,
    warning_details: list[dict] | None = None,
    summary_limit: int = 160,
    example_limit: int = 3,
) -> dict:
    normalized = _dedup_strings(warnings)
    dedup_codes = _dedup_strings(warning_codes)
    dedup_categories = _dedup_strings(warning_categories)
    details = _warning_details_from_inputs(
        normalized,
        dedup_codes,
        dedup_categories,
        warning_details,
    )
    for row in details:
        code = str(row.get("code", "")).strip()
        category = str(row.get("category", "")).strip()
        if code and code not in dedup_codes:
            dedup_codes.append(code)
        if category and category not in dedup_categories:
            dedup_categories.append(category)
    if not normalized and not details and not dedup_codes and not dedup_categories:
        return {}
    warning_summary = ""
    ordered_details = sorted(
        enumerate(details),
        key=lambda item: (
            _warning_priority(
                str(item[1].get("category", "")).strip(),
                str(item[1].get("code", "")).strip(),
            ),
            item[0],
        ),
    )
    if ordered_details:
        warning_summary = str(ordered_details[0][1].get("message", "")).strip()
    elif normalized:
        warning_summary = normalized[0]
    if len(warning_summary) > int(summary_limit):
        warning_summary = warning_summary[-int(summary_limit):]
    warning_examples = [
        str(row.get("message", "")).strip()
        for row in details[: max(1, int(example_limit))]
        if str(row.get("message", "")).strip()
    ]
    if not warning_examples:
        warning_examples = normalized[: max(1, int(example_limit))]
    return {
        "warning_count": max(len(normalized), len(details)),
        "warning_codes": dedup_codes,
        "warning_categories": dedup_categories,
        "warning_examples": warning_examples,
        "warning_details": details,
        "support_warning_present": (
            "noncanon_mining_support_only" in dedup_codes
            or "support_boundary" in dedup_categories
        ),
        "warning_summary": warning_summary,
    }


def build_selector_warning_snapshot(
    warnings: list[str] | None,
    *,
    warning_codes: list[str] | None = None,
    warning_categories: list[str] | None = None,
    warning_details: list[dict] | None = None,
    summary_limit: int = 160,
    example_limit: int = 3,
) -> dict:
    process_snapshot = build_process_warning_snapshot(
        warnings,
        warning_codes=warning_codes,
        warning_categories=warning_categories,
        warning_details=warning_details,
        summary_limit=summary_limit,
        example_limit=example_limit,
    )
    if not process_snapshot:
        return {}
    return {
        "selector_warning_count": int(process_snapshot.get("warning_count", 0) or 0),
        "selector_warning_codes": list(process_snapshot.get("warning_codes", []) or []),
        "selector_warning_categories": list(process_snapshot.get("warning_categories", []) or []),
        "selector_warning_summary": str(process_snapshot.get("warning_summary", "") or "").strip(),
        "selector_warning_examples": list(process_snapshot.get("warning_examples", []) or []),
        "selector_support_warning_present": bool(process_snapshot.get("support_warning_present", False)),
    }


def selector_stop_summary(row: Mapping[str, object]) -> str:
    failure_summary = str(row.get("failure_summary", "") or "").strip()
    if failure_summary:
        return failure_summary
    compact_summary = str(row.get("selector_warning_summary", "") or "").strip()
    if compact_summary:
        return compact_summary
    raw_warnings = row.get("selector_process_warnings", [])
    warnings = _dedup_strings(raw_warnings if isinstance(raw_warnings, list) else [])
    raw_warning_codes = row.get("selector_warning_codes", [])
    warning_codes = _dedup_strings(raw_warning_codes if isinstance(raw_warning_codes, list) else [])
    raw_warning_categories = row.get("selector_warning_categories", [])
    warning_categories = _dedup_strings(raw_warning_categories if isinstance(raw_warning_categories, list) else [])
    snapshot = build_selector_warning_snapshot(
        warnings,
        warning_codes=warning_codes,
        warning_categories=warning_categories,
    )
    return str(snapshot.get("selector_warning_summary", "") or "").strip()
