#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolResult:
    tool: str
    returncode: int
    stdout: str
    stderr: str


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run_tool(argv: list[str]) -> ToolResult:
    p = subprocess.run(argv, capture_output=True, text=True)
    return ToolResult(tool=Path(argv[1]).name if len(argv) > 1 else argv[0], returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)


def _safe_unzip(zip_path: Path, dst_dir: Path) -> None:
    with zipfile.ZipFile(str(zip_path), "r") as z:
        # Basic zip-slip guard.
        for member in z.namelist():
            target = (dst_dir / member).resolve()
            if not str(target).startswith(str(dst_dir.resolve())):
                raise RuntimeError(f"zip_slip_detected:{member}")
        z.extractall(str(dst_dir))


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest ChatGPT Pro claw downloads: unpack, validate (fail-closed), and stage artifacts.")
    ap.add_argument("--download-dir", required=True, help="Directory containing downloaded .zip outputs.")
    ap.add_argument("--out-dir", default="", help="Output staging dir (default: <download-dir>/ingested).")
    ap.add_argument("--mode", choices=["discovery", "focus"], default="discovery", help="A2 topic validation mode.")
    ap.add_argument("--min-topic-slugs", type=int, default=10, help="Minimum topic slugs required (discovery mode).")
    ap.add_argument("--max-topic-slugs", type=int, default=0, help="Optional maximum topic slugs allowed (0 disables).")
    ap.add_argument("--validate-zip-job", action="store_true", help="Also run ZIP_JOB bundle validator in run mode after unzip.")
    ap.add_argument("--move", action="store_true", help="Move zips into PASS/REJECT staging folders under out-dir.")
    args = ap.parse_args()

    download_dir = Path(args.download_dir).expanduser().resolve()
    if not download_dir.is_dir():
        print(f"MISSING_DOWNLOAD_DIR: {download_dir}", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir).expanduser().resolve() if str(args.out_dir).strip() else (download_dir / "ingested")
    pass_dir = out_dir / "PASS"
    reject_dir = out_dir / "REJECT"
    reports_dir = out_dir / "reports"
    for d in [pass_dir, reject_dir, reports_dir]:
        d.mkdir(parents=True, exist_ok=True)

    repo_root = Path(__file__).resolve().parents[3]
    validate_topics = repo_root / "system_v3" / "tools" / "validate_a2_topic_outputs.py"
    validate_zip_job = repo_root / "system_v3" / "tools" / "zip_job_bundle_validator.py"

    zips = sorted(download_dir.glob("*.zip"), key=lambda p: p.name.lower())
    results: list[dict] = []

    for zip_path in zips:
        sha = _sha256_file(zip_path)
        item_id = f"{zip_path.stem}__{sha[:12]}"
        item_report_path = reports_dir / f"{item_id}__ingest_report.json"

        item: dict = {
            "schema": "CHATUI_CLAW_INGEST_ITEM_REPORT_v1",
            "zip_path": str(zip_path),
            "zip_sha256": sha,
            "mode": args.mode,
            "min_topic_slugs": int(args.min_topic_slugs),
            "max_topic_slugs": int(args.max_topic_slugs),
            "validate_zip_job": bool(args.validate_zip_job),
            "tools": [],
            "verdict": "UNSET",
            "reasons": [],
        }

        with tempfile.TemporaryDirectory(prefix="claw_ingest_") as td:
            unpack_dir = Path(td) / "bundle"
            unpack_dir.mkdir(parents=True, exist_ok=True)
            try:
                _safe_unzip(zip_path, unpack_dir)
            except Exception as e:
                item["verdict"] = "REJECT"
                item["reasons"].append(f"UNZIP_FAIL:{type(e).__name__}:{e}")
                item_report_path.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                results.append(item)
                continue

            # 1) A2 topic outputs validation (fail-closed).
            tr = _run_tool(
                [
                    sys.executable,
                    str(validate_topics),
                    "--path",
                    str(unpack_dir),
                    "--mode",
                    str(args.mode),
                    "--min-topic-slugs",
                    str(int(args.min_topic_slugs)),
                    "--max-topic-slugs",
                    str(int(args.max_topic_slugs)),
                    "--json",
                ]
            )
            item["tools"].append({"tool": "validate_a2_topic_outputs.py", "returncode": tr.returncode})
            # parse JSON report for verdict/reasons
            try:
                rep = json.loads(tr.stdout) if tr.stdout.strip() else {}
            except json.JSONDecodeError:
                rep = {"schema": "A2_TOPIC_OUTPUTS_VALIDATION_REPORT_v1", "verdict": "REJECT", "reasons": ["NON_JSON_VALIDATOR_OUTPUT"]}
            item["a2_topics_validation_report"] = rep
            if rep.get("verdict") != "PASS":
                item["verdict"] = "REJECT"
                item["reasons"].extend([f"A2_TOPICS:{r}" for r in rep.get("reasons", [])])

            # 2) Optional ZIP_JOB bundle validator (run mode).
            if args.validate_zip_job:
                zr = _run_tool(
                    [
                        sys.executable,
                        str(validate_zip_job),
                        "--bundle-root",
                        str(unpack_dir),
                        "--mode",
                        "run",
                    ]
                )
                item["tools"].append({"tool": "zip_job_bundle_validator.py", "returncode": zr.returncode})
                try:
                    zrep = json.loads(zr.stdout) if zr.stdout.strip() else {}
                except json.JSONDecodeError:
                    zrep = {"schema": "ZIP_JOB_BUNDLE_VALIDATION_RESULT_v1", "status": "FAIL", "errors": ["NON_JSON_VALIDATOR_OUTPUT"]}
                item["zip_job_validation_report"] = zrep
                if zrep.get("status") != "PASS":
                    item["verdict"] = "REJECT"
                    for err in zrep.get("errors", []) or []:
                        item["reasons"].append(f"ZIP_JOB:{err}")

        if item["verdict"] == "UNSET":
            item["verdict"] = "PASS"

        item_report_path.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        results.append(item)

        if args.move:
            target_dir = pass_dir if item["verdict"] == "PASS" else reject_dir
            dest = target_dir / zip_path.name
            if dest.exists():
                dest = target_dir / f"{zip_path.stem}__{sha[:8]}.zip"
            shutil.move(str(zip_path), str(dest))

    summary = {
        "schema": "CHATUI_CLAW_INGEST_SUMMARY_v1",
        "download_dir": str(download_dir),
        "out_dir": str(out_dir),
        "zip_count": len(zips),
        "pass_count": sum(1 for r in results if r.get("verdict") == "PASS"),
        "reject_count": sum(1 for r in results if r.get("verdict") == "REJECT"),
        "reports_dir": str(reports_dir),
        "items": [{"zip_path": r["zip_path"], "verdict": r["verdict"], "reasons": r.get("reasons", [])[:8]} for r in results],
    }
    (reports_dir / "INGEST_SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["reject_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

