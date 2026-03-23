#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


BOOTPACK_ROOT = _repo_root() / "system_v3" / "runtime" / "bootpack_b_kernel_v1"
if str(BOOTPACK_ROOT) not in sys.path:
    sys.path.insert(0, str(BOOTPACK_ROOT))

from containers import parse_export_block, split_items  # noqa: E402
from kernel import BootpackBKernel  # noqa: E402
from state import KernelState  # noqa: E402


def _status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _read_export_text_from_run(run_dir: Path) -> tuple[str, str]:
    outbox = sorted((run_dir / "outbox").glob("export_block_*.txt"))
    if outbox:
        path = outbox[-1]
        return str(path), path.read_text(encoding="utf-8")
    zip_packets = sorted((run_dir / "zip_packets").glob("*_A0_TO_B_EXPORT_BATCH_ZIP.zip"))
    for path in reversed(zip_packets):
        try:
            with zipfile.ZipFile(path, "r") as zf:
                return f"{path}#EXPORT_BLOCK.txt", zf.read("EXPORT_BLOCK.txt").decode("utf-8")
        except Exception:
            continue
    raise SystemExit(f"no export block found under run dir: {run_dir}")


def _load_state_from_path(path: Path) -> KernelState:
    payload = json.loads(path.read_text(encoding="utf-8"))
    state = KernelState.from_dict(payload)
    heavy_path = path.with_name("state.heavy.json")
    if heavy_path.exists():
        heavy_payload = json.loads(heavy_path.read_text(encoding="utf-8"))
        state.apply_heavy_dict(heavy_payload)
    return state


def _load_state(run_dir: Path | None, state_json: Path | None) -> tuple[str, KernelState]:
    if state_json is not None:
        return str(state_json), _load_state_from_path(state_json)
    if run_dir is not None:
        candidate = run_dir / "state.json"
        if candidate.exists():
            return str(candidate), _load_state_from_path(candidate)
    return "fresh_kernel_state", KernelState()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EXPORT_BLOCK_LINT_REPORT_v1.")
    parser.add_argument("--export-file", default="")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--state-json", default="")
    parser.add_argument("--out-json", default="")
    args = parser.parse_args()

    export_file = Path(args.export_file).resolve() if str(args.export_file).strip() else None
    run_dir = Path(args.run_dir).resolve() if str(args.run_dir).strip() else None
    state_json = Path(args.state_json).resolve() if str(args.state_json).strip() else None

    if export_file is None and run_dir is None:
        raise SystemExit("must provide --export-file or --run-dir")

    if export_file is not None:
        source_path = str(export_file)
        export_text = export_file.read_text(encoding="utf-8")
    else:
        source_path, export_text = _read_export_text_from_run(run_dir)

    state_source, state = _load_state(run_dir, state_json)
    kernel = BootpackBKernel()
    checks: list[dict] = []
    violations: list[dict] = []
    item_ids: list[str] = []
    block = None

    try:
        block = parse_export_block(export_text)
        checks.append({"check_id": "EXPORT_PARSE", "status": "PASS", "detail": "parse_export_block succeeded"})
    except Exception as exc:
        checks.append({"check_id": "EXPORT_PARSE", "status": "FAIL", "detail": f"parse_export_block error: {exc}"})
        report = {
            "schema": "EXPORT_BLOCK_LINT_REPORT_v1",
            "status": "FAIL",
            "source_path": source_path,
            "state_source": state_source,
            "checks": checks,
            "violations": [],
            "duplicate_item_ids": [],
            "item_count": 0,
            "export_id": "",
            "target": "",
            "proposal_type": "",
        }
        out_path = Path(args.out_json).resolve() if str(args.out_json).strip() else None
        if out_path:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
        return 2

    items = split_items(block.content_lines)
    for item in items:
        item_id = str(item.get("id", "")).strip()
        item_ids.append(item_id)
        parse = kernel._parse_item(item, state)  # type: ignore[attr-defined]
        if parse is None:
            violations.append(
                {
                    "item_id": item_id,
                    "tag": "SCHEMA_FAIL",
                    "detail": "ITEM_PARSE",
                    "offender_rule": "STAGE_2_SCHEMA_CHECK",
                    "offender_line": "\n".join(item.get("lines", [])),
                    "offender_literal": "",
                }
            )
            continue
        line_violation = kernel._line_fence_check(parse, state)  # type: ignore[attr-defined]
        if line_violation:
            violations.append(
                {
                    "item_id": item_id,
                    "tag": line_violation.tag,
                    "detail": "LINE_FENCE",
                    "offender_rule": line_violation.rule_id,
                    "offender_line": line_violation.offender_line,
                    "offender_literal": line_violation.offender_literal,
                }
            )

    duplicate_ids = sorted(item_id for item_id, count in Counter(item_ids).items() if item_id and count > 1)
    checks.extend(
        [
            {
                "check_id": "EXPORT_TARGET_KERNEL",
                "status": _status(block.target == "THREAD_B_ENFORCEMENT_KERNEL"),
                "detail": f"target={block.target}",
            },
            {
                "check_id": "ITEM_IDS_UNIQUE",
                "status": _status(len(duplicate_ids) == 0),
                "detail": f"duplicate_item_ids={duplicate_ids}",
            },
            {
                "check_id": "LINE_FENCE_DRY_RUN",
                "status": _status(len(violations) == 0),
                "detail": f"violation_count={len(violations)}",
            },
        ]
    )

    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    report = {
        "schema": "EXPORT_BLOCK_LINT_REPORT_v1",
        "status": status,
        "source_path": source_path,
        "state_source": state_source,
        "checks": checks,
        "violations": violations,
        "duplicate_item_ids": duplicate_ids,
        "item_count": len(items),
        "export_id": block.export_id,
        "target": block.target,
        "proposal_type": block.proposal_type,
    }
    out_path = Path(args.out_json).resolve() if str(args.out_json).strip() else None
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
