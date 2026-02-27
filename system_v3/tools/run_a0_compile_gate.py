#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


EXPORT_RE = re.compile(r"^export_block_(\d+)\.txt$")
COMPILE_RE = re.compile(r"^compile_report_(\d+)\.json$")
DEPEND_RE = re.compile(r"^dependency_report_(\d+)\.json$")
PREFLIGHT_RE = re.compile(r"^preflight_report_(\d+)\.json$")
ZIP_EXPORT_RE = re.compile(r"^(\d+)_A0_TO_B_EXPORT_BATCH_ZIP\.zip$")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _status(flag: bool) -> str:
    return "PASS" if flag else "FAIL"


def _extract_seq_map(path: Path, pattern: re.Pattern[str]) -> dict[int, Path]:
    out: dict[int, Path] = {}
    for p in sorted(path.glob("*")):
        if not p.is_file():
            continue
        m = pattern.match(p.name)
        if not m:
            continue
        seq = int(m.group(1))
        out[seq] = p
    return out


def _extract_export_blocks_from_zip_packets(run_dir: Path) -> dict[int, tuple[Path, str]]:
    out: dict[int, tuple[Path, str]] = {}
    zip_root = run_dir / "zip_packets"
    if not zip_root.exists():
        return out
    for p in sorted(zip_root.glob("*_A0_TO_B_EXPORT_BATCH_ZIP.zip")):
        if not p.is_file():
            continue
        m = ZIP_EXPORT_RE.match(p.name)
        if not m:
            continue
        seq = int(m.group(1))
        try:
            with zipfile.ZipFile(p, "r") as zf:
                text = zf.read("EXPORT_BLOCK.txt").decode("utf-8", errors="ignore")
        except (zipfile.BadZipFile, KeyError, OSError):
            continue
        out[seq] = (p, text)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate P3 A0 compile gate.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--min-export-blocks", type=int, default=1)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    outbox_dir = run_dir / "outbox"
    reports_dir = run_dir / "reports"

    export_payloads: dict[int, dict[str, str]] = {}
    exports = _extract_seq_map(outbox_dir, EXPORT_RE)
    if exports:
        for seq, p in sorted(exports.items()):
            export_payloads[seq] = {
                "path": str(p),
                "text": p.read_text(encoding="utf-8"),
                "source": "outbox",
            }
    else:
        zip_exports = _extract_export_blocks_from_zip_packets(run_dir)
        for seq, (zip_path, text) in sorted(zip_exports.items()):
            export_payloads[seq] = {
                "path": f"{zip_path}#EXPORT_BLOCK.txt",
                "text": text,
                "source": "zip_packets",
            }

    compile_reports = _extract_seq_map(reports_dir, COMPILE_RE)
    dependency_reports = _extract_seq_map(reports_dir, DEPEND_RE)
    preflight_reports = _extract_seq_map(reports_dir, PREFLIGHT_RE)

    checks: list[dict] = []
    checks.append(
        {
            "check_id": "MIN_EXPORT_BLOCKS",
            "status": _status(len(export_payloads) >= args.min_export_blocks),
            "detail": f"export_count={len(export_payloads)} min_required={args.min_export_blocks}",
        }
    )

    export_sequences = sorted(export_payloads.keys())
    checks.append(
        {
            "check_id": "EXPORT_SEQUENCE_UNIQUE_ASC",
            "status": _status(export_sequences == sorted(set(export_sequences))),
            "detail": f"sequences={export_sequences}",
        }
    )

    export_hashes: list[dict] = []
    export_container_ok = True
    export_target_ok = True
    for seq in export_sequences:
        payload = export_payloads[seq]
        text = payload["text"]
        lines = text.splitlines()
        has_begin = len(lines) > 0 and lines[0].strip() in {"BEGIN EXPORT_BLOCK vN", "BEGIN EXPORT_BLOCK v1"}
        has_end = len(lines) > 0 and lines[-1].strip() in {"END EXPORT_BLOCK vN", "END EXPORT_BLOCK v1"}
        has_target = "TARGET: THREAD_B_ENFORCEMENT_KERNEL" in lines
        export_container_ok = export_container_ok and has_begin and has_end
        export_target_ok = export_target_ok and has_target
        export_hashes.append(
            {
                "seq": seq,
                "path": payload["path"],
                "sha256": _sha256_text(text),
            }
        )

    checks.append(
        {
            "check_id": "EXPORT_CONTAINER_SHAPE",
            "status": _status(export_container_ok),
            "detail": "all export blocks begin/end with required container lines",
        }
    )
    checks.append(
        {
            "check_id": "EXPORT_TARGET_LINE",
            "status": _status(export_target_ok),
            "detail": "all export blocks include TARGET: THREAD_B_ENFORCEMENT_KERNEL",
        }
    )

    all_reports_parse_ok = True
    report_files_present = any(bool(m) for m in [compile_reports, dependency_reports, preflight_reports])
    if report_files_present:
        for seq_map in [compile_reports, dependency_reports, preflight_reports]:
            for _, p in sorted(seq_map.items()):
                try:
                    json.loads(p.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    all_reports_parse_ok = False
    checks.append(
        {
            "check_id": "A0_REPORTS_JSON_PARSE",
            "status": _status(all_reports_parse_ok),
            "detail": (
                "compile/dependency/preflight reports parse as JSON"
                if report_files_present
                else "no compile/dependency/preflight reports present (zip-only run surface)"
            ),
        }
    )

    report_seq_match_ok = True
    missing_links: list[dict] = []
    if report_files_present:
        for seq in export_sequences:
            missing = []
            if seq not in compile_reports:
                missing.append("compile_report")
            if seq not in dependency_reports:
                missing.append("dependency_report")
            if seq not in preflight_reports:
                missing.append("preflight_report")
            if missing:
                report_seq_match_ok = False
                missing_links.append({"seq": seq, "missing": missing})
    checks.append(
        {
            "check_id": "EXPORT_REPORT_SEQUENCE_LINKS",
            "status": _status(report_seq_match_ok),
            "detail": (
                f"missing_links={len(missing_links)}"
                if report_files_present
                else "no report sequence links required for zip-only run surface"
            ),
        }
    )

    status = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    report = {
        "schema": "A0_COMPILE_REPORT_v1",
        "run_id": run_dir.name,
        "status": status,
        "checks": checks,
        "export_sequences": export_sequences,
        "missing_links": missing_links,
        "export_hashes": export_hashes,
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }
    out_path = reports_dir / "a0_compile_report.json"
    _write_json(out_path, report)
    print(json.dumps({"status": status, "report_path": str(out_path)}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
