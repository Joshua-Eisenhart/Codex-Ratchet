#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from a1_selector_warning_snapshot import (
    build_selector_provenance_fields,
    build_selector_warning_snapshot,
    extract_selector_warning_fields,
)


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_DEFAULT = SYSTEM_V3 / "runs"
SINK_TOOL = SYSTEM_V3 / "tools" / "a1_lawyer_sink.py"
COLD_CORE_TOOL = SYSTEM_V3 / "tools" / "a1_cold_core_strip.py"
PACK_SELECTOR_TOOL = SYSTEM_V3 / "tools" / "a1_pack_selector.py"
BOOTPACK = SYSTEM_V3 / "runtime" / "bootpack_b_kernel_v1"
TERM_TOKEN_RE = re.compile(r"[a-z][a-z0-9_]*")
TARGET_ID_TERM_SUFFIX_RE = re.compile(r"(?:EXTRA\d+_)?([A-Z][A-Z0-9_]+)$")


def _now_utc_compact() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_json_cmd(cmd: list[str], *, cwd: Path) -> dict:
    raw = subprocess.check_output(cmd, cwd=str(cwd), text=True).strip()
    return json.loads(raw)


def _validate_strategy_file(path: Path) -> None:
    bootpack_path = str(BOOTPACK)
    if bootpack_path not in sys.path:
        sys.path.insert(0, bootpack_path)
    from a1_strategy import validate_strategy  # type: ignore

    errors = validate_strategy(_read_json(path))
    if errors:
        raise SystemExit("invalid direct A1_STRATEGY_v1 input:\n- " + "\n- ".join(errors))


def _next_sandbox_sequence(sandbox_root: Path, fallback: int = 1, explicit: int = 0) -> int:
    state_path = sandbox_root / "sequence_counter.json"
    if int(explicit) > 0:
        last = 0
        if state_path.exists():
            try:
                raw = json.loads(state_path.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and isinstance(raw.get("last"), int):
                    last = int(raw["last"])
            except Exception:
                last = 0
        chosen = int(explicit)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps({"last": max(last, chosen)}, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        return chosen
    if state_path.exists():
        try:
            raw = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and isinstance(raw.get("last"), int):
                nxt = int(raw["last"]) + 1
                state_path.write_text(json.dumps({"last": nxt}, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
                return nxt
        except Exception:
            pass
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"last": int(fallback)}, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return int(fallback)


def _collect_json_inputs(paths: list[Path], staging_dir: Path) -> list[Path]:
    collected: list[Path] = []
    for raw in paths:
        path = raw.expanduser().resolve()
        if path.is_dir():
            for candidate in sorted(path.rglob("*.json")):
                if candidate.is_file():
                    collected.append(candidate)
            continue
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path, "r") as zf:
                for name in sorted(zf.namelist()):
                    if not name.lower().endswith(".json"):
                        continue
                    target = staging_dir / Path(name).name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(zf.read(name))
                    collected.append(target)
            continue
        if path.is_file():
            collected.append(path)
    dedup: list[Path] = []
    seen: set[str] = set()
    for item in collected:
        key = str(item.resolve())
        if key in seen:
            continue
        seen.add(key)
        dedup.append(item)
    return dedup


def _schema_of(path: Path) -> str:
    try:
        obj = _read_json(path)
    except Exception:
        return ""
    return str(obj.get("schema", "")).strip()


def _parse_allowed_terms(csv_text: str) -> set[str]:
    return {str(x).strip() for x in str(csv_text).split(",") if str(x).strip()}


def _failure_summary(*texts: str, limit: int = 160) -> str:
    for text in texts:
        lines = [str(line).strip() for line in str(text or "").splitlines() if str(line).strip()]
        if not lines:
            continue
        summary = lines[-1]
        if len(summary) > int(limit):
            summary = summary[-int(limit):]
        return summary
    return ""


def _selector_warning_snapshot(
    warnings: list[str],
    *,
    warning_codes: list[str] | None = None,
    warning_categories: list[str] | None = None,
    summary_limit: int = 160,
    example_limit: int = 3,
) -> dict:
    return build_selector_warning_snapshot(
        warnings,
        warning_codes=warning_codes,
        warning_categories=warning_categories,
        summary_limit=summary_limit,
        example_limit=example_limit,
    )


def _payload_selector_warning_lists(payload: dict) -> tuple[list[str], list[str]]:
    selector_warning_fields = extract_selector_warning_fields(payload if isinstance(payload, dict) else {})
    warning_codes = list(selector_warning_fields.get("selector_warning_codes", []) or [])
    warning_categories = list(selector_warning_fields.get("selector_warning_categories", []) or [])
    return warning_codes, warning_categories


def _with_selector_warning_snapshot(payload: dict, warnings: list[str]) -> dict:
    out = dict(payload)
    warning_codes, warning_categories = _payload_selector_warning_lists(out)
    snapshot = _selector_warning_snapshot(
        warnings,
        warning_codes=warning_codes,
        warning_categories=warning_categories,
    )
    if snapshot:
        out.update(snapshot)
    return out


def _selector_provenance_payload(
    *,
    cold_core_path: str,
    selector_cold_core_source: str,
    selector_cold_core_path_class: str,
    selector_cold_core_sha256: str,
) -> dict:
    out: dict = {}
    if cold_core_path:
        out["cold_core_path"] = cold_core_path
    selector_fields = build_selector_provenance_fields(
        cold_core_path=cold_core_path,
        cold_core_source=selector_cold_core_source,
        cold_core_path_class=selector_cold_core_path_class,
        cold_core_sha256=selector_cold_core_sha256,
        selector_prefixed=True,
    )
    selector_fields.pop("selector_cold_core_path", None)
    out.update(selector_fields)
    return out


def _clamp_rescue_targets_by_allowed_terms(rescue_targets: list[str], *, allowed_terms: set[str]) -> list[str]:
    if not allowed_terms:
        return [str(x).strip() for x in rescue_targets if str(x).strip()]
    filtered: list[str] = []
    for raw in rescue_targets:
        target = str(raw).strip()
        if not target:
            continue
        m = TARGET_ID_TERM_SUFFIX_RE.search(target)
        if not m:
            continue
        term = str(m.group(1)).strip().lower()
        if TERM_TOKEN_RE.fullmatch(term) and term in allowed_terms and target not in filtered:
            filtered.append(target)
    return filtered


def _sanitize_memo_terms(memo: dict, *, allowed_terms: set[str]) -> dict:
    if not allowed_terms:
        return memo
    clean = dict(memo)
    proposed_terms = clean.get("proposed_terms")
    if isinstance(proposed_terms, list):
        filtered: list[str] = []
        for item in proposed_terms:
            term = str(item).strip()
            if term and term in allowed_terms and term not in filtered:
                filtered.append(term)
        clean["proposed_terms"] = filtered
    rescue_targets = clean.get("graveyard_rescue_targets")
    if isinstance(rescue_targets, list):
        clean["graveyard_rescue_targets"] = _clamp_rescue_targets_by_allowed_terms(
            [str(item).strip() for item in rescue_targets if str(item).strip()],
            allowed_terms=allowed_terms,
        )
    return clean


def _expand_external_memo_response(
    path: Path,
    staging_dir: Path,
    *,
    run_id: str,
    sequence: int,
    allowed_terms: set[str],
) -> list[Path]:
    obj = _read_json(path)
    memos = obj.get("memos", [])
    if not isinstance(memos, list):
        raise SystemExit(f"invalid A1_EXTERNAL_MEMO_RESPONSE_v1 memos list: {path}")
    out: list[Path] = []
    response_dir = staging_dir / "expanded_external_memos"
    response_dir.mkdir(parents=True, exist_ok=True)
    for index, row in enumerate(memos, start=1):
        if not isinstance(row, dict):
            raise SystemExit(f"external memo response contains non-object memo at index {index}: {path}")
        memo = dict(row)
        memo["schema"] = "A1_LAWYER_MEMO_v1"
        memo["run_id"] = str(memo.get("run_id", run_id)).strip() or run_id
        memo["sequence"] = int(memo.get("sequence", sequence) or sequence)
        memo["role"] = str(memo.get("role", "")).strip().upper()
        memo = _sanitize_memo_terms(memo, allowed_terms=allowed_terms)
        target = response_dir / f"{path.stem}__memo_{index:04d}.json"
        target.write_text(json.dumps(memo, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        out.append(target)
    return out


def _write_report(
    path: Path,
    *,
    status: str,
    failure_code: int,
    run_id: str,
    sequence: int,
    inputs: list[Path],
    memo_count: int,
    effective_memo_count: int,
    strategy_count: int,
    external_response_count: int,
    cold_core: str,
    strategy_out: str,
    mode: str,
    selector_cold_core_source: str,
    selector_cold_core_path_class: str,
    selector_cold_core_sha256: str,
    selector_process_warnings: list[str],
    selector_warning_codes: list[str] | None,
    selector_warning_categories: list[str] | None,
    failure_summary: str,
) -> None:
    lines = [
        "# A1 Consolidation Prepack Report",
        "",
        f"- `status`: `{status}`",
        f"- `run_id`: `{run_id}`",
        f"- `sequence`: `{sequence}`",
        f"- `mode`: `{mode}`",
        f"- `input_count`: `{len(inputs)}`",
        f"- `memo_count`: `{memo_count}`",
        f"- `effective_memo_count`: `{effective_memo_count}`",
        f"- `strategy_count`: `{strategy_count}`",
        f"- `external_response_count`: `{external_response_count}`",
    ]
    if cold_core:
        lines.append(f"- `cold_core_path`: `{cold_core}`")
    if selector_cold_core_source:
        lines.append(f"- `selector_cold_core_source`: `{selector_cold_core_source}`")
    if selector_cold_core_path_class:
        lines.append(f"- `selector_cold_core_path_class`: `{selector_cold_core_path_class}`")
    if selector_cold_core_sha256:
        lines.append(f"- `selector_cold_core_sha256`: `{selector_cold_core_sha256}`")
    if strategy_out:
        lines.append(f"- `strategy_out`: `{strategy_out}`")
    if selector_process_warnings:
        lines.append("- `selector_process_warnings`:")
        for msg in selector_process_warnings:
            lines.append(f"  - `{msg}`")
        snapshot = _selector_warning_snapshot(
            selector_process_warnings,
            warning_codes=selector_warning_codes,
            warning_categories=selector_warning_categories,
        )
        if snapshot:
            lines.append(f"- `selector_warning_count`: `{int(snapshot.get('selector_warning_count', 0) or 0)}`")
            lines.append(
                f"- `selector_support_warning_present`: "
                f"`{bool(snapshot.get('selector_support_warning_present', False))}`"
            )
            examples = snapshot.get("selector_warning_examples", [])
            if isinstance(examples, list) and examples:
                lines.append("- `selector_warning_examples`:")
                for msg in examples:
                    lines.append(f"  - `{str(msg)}`")
    if int(failure_code) != 0:
        lines.append(f"- `failure_code`: `{int(failure_code)}`")
    if failure_summary:
        lines.append(f"- `failure_summary`: `{failure_summary}`")
    lines.extend(["", "## Inputs"])
    for item in inputs:
        lines.append(f"- `{item}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Consolidate many A1 worker outputs into one strict pre-A0 strategy surface. "
            "Memo inputs are ingested into the run-local sandbox, stripped to cold core, "
            "then routed through the deterministic pack selector."
        )
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--input", action="append", default=[], help="Input JSON file, ZIP bundle, or directory. Repeatable.")
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT))
    ap.add_argument("--track", default="ENGINE_ENTROPY_EXPLORATION")
    ap.add_argument("--debate-mode", choices=["balanced", "graveyard_first", "graveyard_recovery"], default="graveyard_first")
    ap.add_argument("--goal-selection", choices=["interleaved", "closure_first"], default="interleaved")
    ap.add_argument("--graveyard-fill-policy", choices=["anchor_replay", "fuel_full_load"], default="anchor_replay")
    ap.add_argument("--forbid-rescue-in-graveyard-first", action="store_true")
    ap.add_argument("--max-terms", type=int, default=0)
    ap.add_argument("--graveyard-library-terms", default="")
    ap.add_argument(
        "--allowed-terms",
        default="",
        help="Optional comma-separated hard allowlist for pack-selector term goals.",
    )
    ap.add_argument("--sequence", type=int, default=0, help="Optional explicit sandbox sequence override.")
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    runs_root = Path(args.runs_root).expanduser().resolve()
    run_dir = runs_root / run_id
    if not run_dir.is_dir():
        raise SystemExit(f"missing run dir: {run_dir}")
    sandbox_root = run_dir / "a1_sandbox"
    sandbox_root.mkdir(parents=True, exist_ok=True)
    report_dir = sandbox_root / "prepack_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    allowed_terms = _parse_allowed_terms(str(args.allowed_terms))

    raw_inputs = [Path(x) for x in args.input if str(x).strip()]
    if not raw_inputs:
        raise SystemExit("at least one --input is required")

    with tempfile.TemporaryDirectory(prefix="a1_prepack_") as td:
        staging_dir = Path(td)
        inputs = _collect_json_inputs(raw_inputs, staging_dir)
        if not inputs:
            raise SystemExit("no JSON inputs resolved from --input values")

        memos: list[Path] = []
        strategies: list[Path] = []
        external_responses: list[Path] = []
        unsupported: list[Path] = []
        for path in inputs:
            schema = _schema_of(path)
            if schema == "A1_LAWYER_MEMO_v1":
                memos.append(path)
            elif schema == "A1_STRATEGY_v1":
                strategies.append(path)
            elif schema == "A1_EXTERNAL_MEMO_RESPONSE_v1":
                external_responses.append(path)
            else:
                unsupported.append(path)

        if unsupported:
            raise SystemExit("unsupported input schemas:\n- " + "\n- ".join(str(p) for p in unsupported))
        if (memos or external_responses) and strategies:
            raise SystemExit("mixed memo and direct strategy inputs are not allowed in one prepack run")
        if len(strategies) > 1:
            raise SystemExit("multiple direct A1_STRATEGY_v1 inputs are not merge-defined; fail closed")

        sequence = _next_sandbox_sequence(sandbox_root, explicit=int(args.sequence))
        status = "PASS"
        cold_core_path = ""
        strategy_out = ""
        mode = "memo_consolidation"
        pack_result: dict = {}
        selector_cold_core_source = ""
        selector_cold_core_path_class = ""
        selector_cold_core_sha256 = ""
        selector_process_warnings: list[str] = []
        selector_warning_codes: list[str] = []
        selector_warning_categories: list[str] = []
        failure_summary = ""

        if memos or external_responses:
            staged_memos_dir = staging_dir / "memos"
            staged_memos_dir.mkdir(parents=True, exist_ok=True)
            expanded_memos: list[Path] = []
            for response_path in external_responses:
                expanded_memos.extend(
                    _expand_external_memo_response(
                        response_path,
                        staging_dir,
                        run_id=run_id,
                        sequence=sequence,
                        allowed_terms=allowed_terms,
                    )
                )
            memo_inputs = list(memos) + expanded_memos
            for index, src in enumerate(memo_inputs, start=1):
                obj = _read_json(src)
                obj["run_id"] = run_id
                obj["sequence"] = sequence
                obj = _sanitize_memo_terms(obj, allowed_terms=allowed_terms)
                staged = staged_memos_dir / f"{index:04d}__A1_LAWYER_MEMO_v1.json"
                staged.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
                _run_json_cmd(
                    ["python3", str(SINK_TOOL), "--run-id", run_id, "--runs-root", str(runs_root), "--input-json", str(staged)],
                    cwd=REPO,
                )

            cold_core_result = _run_json_cmd(
                [
                    "python3",
                    str(COLD_CORE_TOOL),
                    "--run-id",
                    run_id,
                    "--runs-root",
                    str(runs_root),
                    "--sequence",
                    str(sequence),
                    "--allowed-terms",
                    str(args.allowed_terms).strip(),
                ],
                cwd=REPO,
            )
            cold_core_path = str(cold_core_result.get("out", "")).strip()
            selector_cold_core_source = "explicit_arg"
            selector_cold_core_path_class = str(cold_core_result.get("cold_core_path_class", "")).strip()
            selector_cold_core_sha256 = str(cold_core_result.get("cold_core_sha256", "")).strip()
            pack_cmd = [
                "python3",
                str(PACK_SELECTOR_TOOL),
                "--run-id",
                run_id,
                "--runs-root",
                str(runs_root),
                "--cold-core",
                cold_core_path,
                "--sequence",
                str(sequence),
                "--track",
                str(args.track),
                "--debate-mode",
                str(args.debate_mode),
                "--goal-selection",
                str(args.goal_selection),
                "--graveyard-fill-policy",
                str(args.graveyard_fill_policy),
            ]
            if bool(args.forbid_rescue_in_graveyard_first):
                pack_cmd.append("--forbid-rescue-in-graveyard-first")
            if int(args.max_terms) > 0:
                pack_cmd.extend(["--max-terms", str(int(args.max_terms))])
            if str(args.graveyard_library_terms).strip():
                pack_cmd.extend(["--graveyard-library-terms", str(args.graveyard_library_terms).strip()])
            if str(args.allowed_terms).strip():
                pack_cmd.extend(["--allowed-terms", str(args.allowed_terms).strip()])
            pack_proc = subprocess.run(pack_cmd, cwd=str(REPO), check=False, capture_output=True, text=True)
            pack_stdout = (pack_proc.stdout or "").strip()
            pack_stderr = (pack_proc.stderr or "").strip()
            if pack_proc.returncode != 0:
                status = "PACK_SELECTOR_FAILED"
                failure_summary = _failure_summary(pack_stderr, pack_stdout)
                report_path = report_dir / f"{sequence:06d}__A1_CONSOLIDATION_PREPACK_REPORT__{_now_utc_compact()}.md"
                _write_report(
                    report_path,
                    status=status,
                    failure_code=int(pack_proc.returncode),
                    run_id=run_id,
                    sequence=sequence,
                    inputs=inputs,
                    memo_count=len(memos),
                    effective_memo_count=len(memo_inputs),
                    strategy_count=len(strategies),
                    external_response_count=len(external_responses),
                    cold_core=cold_core_path,
                    strategy_out=strategy_out,
                    mode=mode,
                    selector_cold_core_source=selector_cold_core_source,
                    selector_cold_core_path_class=selector_cold_core_path_class,
                    selector_cold_core_sha256=selector_cold_core_sha256,
                    selector_process_warnings=selector_process_warnings,
                    selector_warning_codes=selector_warning_codes,
                    selector_warning_categories=selector_warning_categories,
                    failure_summary=failure_summary,
                )
                result = _with_selector_warning_snapshot({
                    "schema": "A1_CONSOLIDATION_PREPACK_RESULT_v1",
                    "status": status,
                    "run_id": run_id,
                    "sequence": sequence,
                    "mode": mode,
                    "input_count": len(inputs),
                    "memo_count": len(memos),
                    "effective_memo_count": len(memo_inputs),
                    "strategy_count": len(strategies),
                    "external_response_count": len(external_responses),
                    **_selector_provenance_payload(
                        cold_core_path=cold_core_path,
                        selector_cold_core_source=selector_cold_core_source,
                        selector_cold_core_path_class=selector_cold_core_path_class,
                        selector_cold_core_sha256=selector_cold_core_sha256,
                    ),
                    "selector_process_warnings": list(selector_process_warnings),
                    "selector_warning_codes": list(selector_warning_codes),
                    "selector_warning_categories": list(selector_warning_categories),
                    "strategy_out": strategy_out,
                    "report_path": str(report_path),
                    "code": int(pack_proc.returncode),
                    "stdout": pack_stdout[-400:],
                    "stderr": pack_stderr[-400:],
                }, selector_process_warnings)
                if failure_summary:
                    result["failure_summary"] = failure_summary
                print(json.dumps(result, sort_keys=True))
                return int(pack_proc.returncode) or 1
            pack_result = json.loads(pack_stdout or "{}")
            if not isinstance(pack_result, dict):
                raise SystemExit("pack selector did not emit a JSON object")
            strategy_out = str(pack_result.get("out", "")).strip()
            selector_cold_core_source = str(pack_result.get("cold_core_source", "")).strip()
            selector_cold_core_path_class = str(pack_result.get("cold_core_path_class", "")).strip()
            selector_cold_core_sha256 = str(pack_result.get("cold_core_sha256", "")).strip()
            raw_selector_warnings = pack_result.get("selector_process_warnings", [])
            for raw in raw_selector_warnings if isinstance(raw_selector_warnings, list) else []:
                msg = str(raw).strip()
                if msg and msg not in selector_process_warnings:
                    selector_process_warnings.append(msg)
            raw_selector_warning_codes = pack_result.get("selector_warning_codes", [])
            for raw in raw_selector_warning_codes if isinstance(raw_selector_warning_codes, list) else []:
                code = str(raw).strip()
                if code and code not in selector_warning_codes:
                    selector_warning_codes.append(code)
            raw_selector_warning_categories = pack_result.get("selector_warning_categories", [])
            for raw in raw_selector_warning_categories if isinstance(raw_selector_warning_categories, list) else []:
                category = str(raw).strip()
                if category and category not in selector_warning_categories:
                    selector_warning_categories.append(category)
            selector_reported_sequence = int(pack_result.get("sequence", sequence) or sequence)
            if selector_reported_sequence != int(sequence):
                status = "PACK_SELECTOR_FAILED"
                failure_summary = (
                    f"pack selector reported sequence {selector_reported_sequence}, "
                    f"expected {int(sequence)}; refusing mismatched strategy handoff"
                )
                if failure_summary not in selector_process_warnings:
                    selector_process_warnings.append(failure_summary)
                if "pack_selector_reported_sequence_mismatch" not in selector_warning_codes:
                    selector_warning_codes.append("pack_selector_reported_sequence_mismatch")
                if "cold_core_sequence" not in selector_warning_categories:
                    selector_warning_categories.append("cold_core_sequence")
                report_path = report_dir / f"{sequence:06d}__A1_CONSOLIDATION_PREPACK_REPORT__{_now_utc_compact()}.md"
                _write_report(
                    report_path,
                    status=status,
                    failure_code=1,
                    run_id=run_id,
                    sequence=sequence,
                    inputs=inputs,
                    memo_count=len(memos),
                    effective_memo_count=len(memo_inputs),
                    strategy_count=len(strategies),
                    external_response_count=len(external_responses),
                    cold_core=cold_core_path,
                    strategy_out=strategy_out,
                    mode=mode,
                    selector_cold_core_source=selector_cold_core_source,
                    selector_cold_core_path_class=selector_cold_core_path_class,
                    selector_cold_core_sha256=selector_cold_core_sha256,
                    selector_process_warnings=selector_process_warnings,
                    selector_warning_codes=selector_warning_codes,
                    selector_warning_categories=selector_warning_categories,
                    failure_summary=failure_summary,
                )
                result = _with_selector_warning_snapshot({
                    "schema": "A1_CONSOLIDATION_PREPACK_RESULT_v1",
                    "status": status,
                    "run_id": run_id,
                    "sequence": sequence,
                    "mode": mode,
                    "input_count": len(inputs),
                    "memo_count": len(memos),
                    "effective_memo_count": len(memo_inputs),
                    "strategy_count": len(strategies),
                    "external_response_count": len(external_responses),
                    **_selector_provenance_payload(
                        cold_core_path=cold_core_path,
                        selector_cold_core_source=selector_cold_core_source,
                        selector_cold_core_path_class=selector_cold_core_path_class,
                        selector_cold_core_sha256=selector_cold_core_sha256,
                    ),
                    "selector_process_warnings": list(selector_process_warnings),
                    "selector_warning_codes": list(selector_warning_codes),
                    "selector_warning_categories": list(selector_warning_categories),
                    "strategy_out": strategy_out,
                    "report_path": str(report_path),
                    "code": 1,
                    "selector_reported_sequence": selector_reported_sequence,
                }, selector_process_warnings)
                if failure_summary:
                    result["failure_summary"] = failure_summary
                print(json.dumps(result, sort_keys=True))
                return 1
        else:
            mode = "direct_strategy_passthrough"
            _validate_strategy_file(strategies[0])
            strategy_out = str(strategies[0])

        report_path = report_dir / f"{sequence:06d}__A1_CONSOLIDATION_PREPACK_REPORT__{_now_utc_compact()}.md"
        _write_report(
            report_path,
            status=status,
            failure_code=0,
            run_id=run_id,
            sequence=sequence,
            inputs=inputs,
            memo_count=len(memos),
            effective_memo_count=len(memo_inputs) if (memos or external_responses) else 0,
            strategy_count=len(strategies),
            external_response_count=len(external_responses),
            cold_core=cold_core_path,
            strategy_out=strategy_out,
            mode=mode,
            selector_cold_core_source=selector_cold_core_source,
            selector_cold_core_path_class=selector_cold_core_path_class,
            selector_cold_core_sha256=selector_cold_core_sha256,
            selector_process_warnings=selector_process_warnings,
            selector_warning_codes=selector_warning_codes,
            selector_warning_categories=selector_warning_categories,
            failure_summary=failure_summary,
        )

        result = _with_selector_warning_snapshot({
            "schema": "A1_CONSOLIDATION_PREPACK_RESULT_v1",
            "status": "PASS",
            "run_id": run_id,
            "sequence": sequence,
            "mode": mode,
            "input_count": len(inputs),
            "memo_count": len(memos),
            "effective_memo_count": len(memo_inputs) if (memos or external_responses) else 0,
            "strategy_count": len(strategies),
            "external_response_count": len(external_responses),
            **_selector_provenance_payload(
                cold_core_path=cold_core_path,
                selector_cold_core_source=selector_cold_core_source,
                selector_cold_core_path_class=selector_cold_core_path_class,
                selector_cold_core_sha256=selector_cold_core_sha256,
            ),
            "selector_process_warnings": list(selector_process_warnings),
            "selector_warning_codes": list(selector_warning_codes),
            "selector_warning_categories": list(selector_warning_categories),
            "strategy_out": strategy_out,
            "report_path": str(report_path),
        }, selector_process_warnings)
        print(json.dumps(result, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
