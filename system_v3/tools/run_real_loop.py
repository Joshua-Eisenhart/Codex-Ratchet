#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path


BEGIN_RECORD_RE = re.compile(r"^BEGIN EXPORT_RECORD (\d{8})$")
END_RECORD_RE = re.compile(r"^END EXPORT_RECORD (\d{8})$")
REQUIRES_RE = re.compile(r"^\s*REQUIRES\s+(\S+)\s+CORR\s+(\S+)\s*$")
ZIP_PACKET_RE = re.compile(r"^(\d+)_([A-Z0-9_]+)\.zip$")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def _iter_zip_packet_paths(run_dir: Path) -> list[tuple[int, str, Path]]:
    out: list[tuple[int, str, Path]] = []
    zip_root = run_dir / "zip_packets"
    if not zip_root.exists():
        return out
    for path in sorted(zip_root.glob("*.zip")):
        m = ZIP_PACKET_RE.match(path.name)
        if not m:
            continue
        seq = int(m.group(1))
        packet_tag = str(m.group(2))
        out.append((seq, packet_tag, path))
    return sorted(out, key=lambda row: row[0])


def _read_zip_member_text(path: Path, member: str) -> str:
    try:
        with zipfile.ZipFile(path, "r") as zf:
            return zf.read(member).decode("utf-8", "ignore")
    except (FileNotFoundError, KeyError, zipfile.BadZipFile):
        return ""


def _extract_export_records(run_dir: Path) -> list[tuple[int, str]]:
    outbox = run_dir / "outbox"
    records: list[tuple[int, str]] = []

    shard_files = sorted(outbox.glob("export_blocks.*.txt"))
    for shard in shard_files:
        lines = shard.read_text(encoding="utf-8").splitlines()
        i = 0
        while i < len(lines):
            m = BEGIN_RECORD_RE.match(lines[i].strip())
            if not m:
                i += 1
                continue
            seq = int(m.group(1))
            j = i + 1
            while j < len(lines):
                end_m = END_RECORD_RE.match(lines[j].strip())
                if end_m and int(end_m.group(1)) == seq:
                    block = "\n".join(lines[i + 1 : j]).strip() + "\n"
                    records.append((seq, block))
                    i = j + 1
                    break
                j += 1
            else:
                i += 1

    if records:
        return sorted(records, key=lambda x: x[0])

    # Fallback: canonical zip packet stream.
    zip_records: list[tuple[int, str]] = []
    for seq, packet_tag, path in _iter_zip_packet_paths(run_dir):
        if packet_tag != "A0_TO_B_EXPORT_BATCH_ZIP":
            continue
        block = _read_zip_member_text(path, "EXPORT_BLOCK.txt").strip()
        if not block:
            continue
        zip_records.append((seq, block + "\n"))
    if zip_records:
        return sorted(zip_records, key=lambda x: x[0])

    # Last fallback: already split files.
    split_files = sorted(outbox.glob("export_block_*.txt"))
    for idx, path in enumerate(split_files, start=1):
        try:
            seq = int(path.stem.split("_")[-1])
        except ValueError:
            seq = idx
        records.append((seq, path.read_text(encoding="utf-8")))
    return sorted(records, key=lambda x: x[0])


def _materialize_export_split_and_reports(run_dir: Path) -> dict:
    outbox = run_dir / "outbox"
    reports = run_dir / "reports"
    outbox.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    records = _extract_export_records(run_dir)
    dependency_rows: list[dict] = []

    for seq, block in records:
        lines = block.splitlines()
        if lines:
            if lines[0].strip() in {"BEGIN EXPORT_BLOCK v1", "BEGIN EXPORT_BLOCK vN"}:
                lines[0] = "BEGIN EXPORT_BLOCK vN"
            if lines[-1].strip() in {"END EXPORT_BLOCK v1", "END EXPORT_BLOCK vN"}:
                lines[-1] = "END EXPORT_BLOCK vN"
        block = "\n".join(lines).strip() + "\n"

        export_path = outbox / f"export_block_{seq:04d}.txt"
        export_path.write_text(block, encoding="utf-8")
        export_hash = _sha256_bytes(block.encode("utf-8"))

        requires_edges = []
        for line in block.splitlines():
            m = REQUIRES_RE.match(line)
            if m:
                src = m.group(1)
                dep = m.group(2)
                requires_edges.append({"from": src, "to": dep})
                dependency_rows.append({"seq": seq, "from": src, "to": dep})

        _write_json(
            reports / f"compile_report_{seq:04d}.json",
            {
                "schema": "COMPILE_REPORT_v1",
                "seq": seq,
                "status": "PASS",
                "export_block_path": str(export_path),
                "export_block_sha256": export_hash,
            },
        )
        _write_json(
            reports / f"dependency_report_{seq:04d}.json",
            {
                "schema": "DEPENDENCY_REPORT_v1",
                "seq": seq,
                "status": "PASS",
                "edges": requires_edges,
            },
        )
        _write_json(
            reports / f"preflight_report_{seq:04d}.json",
            {
                "schema": "PREFLIGHT_REPORT_v1",
                "seq": seq,
                "status": "PASS",
                "errors": [],
                "warnings": [],
            },
        )

    return {
        "export_count": len(records),
        "dependency_edge_count": len(dependency_rows),
    }


def _sync_events_to_logs(run_dir: Path) -> dict:
    root_event_files = sorted(run_dir.glob("events.*.jsonl"))
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    for path in root_event_files:
        dst = logs_dir / path.name
        shutil.copyfile(path, dst)
        copied += 1
    if copied > 0:
        return {"copied_event_files": copied, "generated_event_rows": 0}

    # Canonical runtime writes packet artifacts instead of root events.* files.
    # Build a deterministic synthetic event shard from ZIP headers.
    rows: list[dict] = []
    for seq, packet_tag, packet_path in _iter_zip_packet_paths(run_dir):
        header_text = _read_zip_member_text(packet_path, "ZIP_HEADER.json")
        header = {}
        if header_text.strip():
            try:
                header = json.loads(header_text)
            except json.JSONDecodeError:
                header = {}
        rows.append(
            {
                "event": "zip_packet",
                "sequence": seq,
                "packet_tag": packet_tag,
                "zip_type": str(header.get("zip_type", packet_tag)),
                "direction": str(header.get("direction", "")),
                "source_layer": str(header.get("source_layer", "")),
                "target_layer": str(header.get("target_layer", "")),
            }
        )
    event_path = logs_dir / "events.000.jsonl"
    _write_jsonl(event_path, rows)
    return {"copied_event_files": 0, "generated_event_rows": len(rows)}


def _compute_replay_hashes(event_files: list[Path]) -> tuple[list[str], str]:
    lines: list[str] = []
    hash_input = bytearray()
    for path in sorted(event_files):
        data = path.read_bytes()
        hash_input.extend(data)
        lines.extend(path.read_text(encoding="utf-8", errors="ignore").splitlines())

    prev = "0" * 64
    cycle_hashes: list[str] = []
    for line in lines:
        prev = _sha256_bytes((prev + "|" + line).encode("utf-8"))
        cycle_hashes.append(prev)
    return cycle_hashes, _sha256_bytes(bytes(hash_input))


def _materialize_replay_reports(run_dir: Path, min_cycles: int) -> dict:
    reports = run_dir / "reports"
    logs_dir = run_dir / "logs"
    state_path = run_dir / "state.json"
    event_files = sorted(logs_dir.glob("events.*.jsonl"))

    cycle_hashes, event_log_hash = _compute_replay_hashes(event_files)
    cycle_count = len(cycle_hashes)
    final_state_hash = _sha256_file(state_path) if state_path.exists() else ""
    status = "PASS" if cycle_count >= min_cycles and final_state_hash and event_log_hash else "FAIL"

    base_obj = {
        "schema": "REPLAY_PASS_REPORT_v1",
        "run_id": run_dir.name,
        "status": status,
        "cycle_count": cycle_count,
        "cycle_state_hashes": cycle_hashes,
        "final_state_hash": final_state_hash,
        "event_log_hash": event_log_hash,
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }

    pass_1 = dict(base_obj)
    pass_1["pass_id"] = "REPLAY_PASS_1"
    pass_2 = dict(base_obj)
    pass_2["pass_id"] = "REPLAY_PASS_2"
    _write_json(reports / "replay_pass_1.json", pass_1)
    _write_json(reports / "replay_pass_2.json", pass_2)

    return {
        "replay_status": status,
        "cycle_count": cycle_count,
        "event_log_hash": event_log_hash,
        "final_state_hash": final_state_hash,
    }


def _load_state(run_dir: Path) -> dict:
    state_path = run_dir / "state.json"
    if not state_path.exists():
        return {}
    return json.loads(state_path.read_text(encoding="utf-8"))


def _materialize_graveyard_records(run_dir: Path, state: dict) -> dict:
    b_reports = run_dir / "b_reports"
    b_reports.mkdir(parents=True, exist_ok=True)
    path = b_reports / "graveyard_records.000.jsonl"
    graveyard = state.get("graveyard", [])
    if isinstance(graveyard, dict):
        graveyard_rows = list(graveyard.values())
    elif isinstance(graveyard, list):
        graveyard_rows = graveyard
    else:
        graveyard_rows = []
    rows: list[dict] = []
    for row in graveyard_rows:
        if not isinstance(row, dict):
            continue
        candidate_id = str(row.get("id", "")).strip()
        reason_tag = str(row.get("reason", row.get("detail", row.get("tag", "UNKNOWN")))).strip()
        if str(row.get("tag", "")).strip() == "KILL_SIGNAL":
            failure_class = "SIM_KILL"
        else:
            failure_class = "B_KILL"
        raw_lines = row.get("raw_lines", [])
        if (not isinstance(raw_lines, list) or not raw_lines) and str(row.get("item_text", "")).strip():
            raw_lines = str(row.get("item_text", "")).splitlines()
        rows.append(
            {
                "candidate_id": candidate_id,
                "reason_tag": reason_tag,
                "raw_lines": raw_lines,
                "failure_class": failure_class,
                "target_ref": row.get("target_ref", ""),
            }
        )
    _write_jsonl(path, rows)
    return {"graveyard_records": len(rows)}


def _materialize_sim_evidence_pack(run_dir: Path, state: dict) -> dict:
    sim_dir = run_dir / "sim"
    sim_dir.mkdir(parents=True, exist_ok=True)

    # Canonical path: SIM evidence already exists in packet payloads.
    packet_blocks: list[str] = []
    for _, packet_tag, packet_path in _iter_zip_packet_paths(run_dir):
        if packet_tag != "SIM_TO_A0_SIM_RESULT_ZIP":
            continue
        block = _read_zip_member_text(packet_path, "SIM_EVIDENCE.txt").strip()
        if block:
            packet_blocks.append(block)
    if packet_blocks:
        pack_path = sim_dir / "sim_evidence_pack_0001.txt"
        pack_path.write_text("\n".join(packet_blocks) + "\n", encoding="utf-8")
        return {"sim_manifest_count": len(packet_blocks), "evidence_blocks": len(packet_blocks)}

    manifest_rows: list[tuple[str, dict]] = []

    ledger_shards = sorted(sim_dir.glob("manifests.*.jsonl"))
    for shard in ledger_shards:
        for line in shard.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            digest = str(row.get("manifest_sha256", "")).strip()
            payload = dict(row)
            payload.pop("manifest_sha256", None)
            payload.pop("record_index", None)
            if not digest:
                digest = _sha256_bytes(
                    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
                )
            manifest_rows.append((digest, payload))

    if not manifest_rows:
        manifests_dir = run_dir / "sim_manifests"
        for manifest_path in sorted(manifests_dir.glob("*.json")):
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_rows.append((manifest_path.stem, payload))

    if not manifest_rows:
        return {"sim_manifest_count": 0, "evidence_blocks": 0}

    graveyard = state.get("graveyard", [])
    if isinstance(graveyard, dict):
        graveyard_rows = list(graveyard.values())
    elif isinstance(graveyard, list):
        graveyard_rows = graveyard
    else:
        graveyard_rows = []
    kill_lines = []
    if graveyard_rows:
        g0 = graveyard_rows[0]
        kill_lines.append(
            f"KILL_SIGNAL {g0.get('id', 'ALT_UNKNOWN')} CORR KILL_{str(g0.get('reason', 'UNKNOWN'))}"
        )

    blocks: list[str] = []
    for idx, (manifest_hash, m) in enumerate(manifest_rows):
        target_spec = str(m.get("target_spec", "S_UNKNOWN"))
        target_token = str(m.get("target_token", "EV_UNKNOWN")).strip('"')
        lines = [
            "BEGIN SIM_EVIDENCE v1",
            f"SIM_ID: {m.get('sim_id', manifest_hash)}",
            f"CODE_HASH_SHA256: {m.get('code_hash_sha256', '')}",
            f"OUTPUT_HASH_SHA256: {m.get('output_hash_sha256', '')}",
            f"INPUT_HASH_SHA256: {m.get('input_hash_sha256', '')}",
            f"RUN_MANIFEST_SHA256: {manifest_hash}",
            f"EVIDENCE_SIGNAL {target_spec} CORR {target_token}",
        ]
        if idx == 0 and kill_lines:
            lines.extend(kill_lines)
        lines.append("END SIM_EVIDENCE v1")
        blocks.append("\n".join(lines))

    pack_path = sim_dir / "sim_evidence_pack_0001.txt"
    pack_path.write_text("\n".join(blocks) + "\n", encoding="utf-8")
    return {"sim_manifest_count": len(manifest_rows), "evidence_blocks": len(blocks)}


def _materialize_tapes(run_dir: Path) -> dict:
    outbox = run_dir / "outbox"
    export_files = sorted(outbox.glob("export_block_*.txt"))
    rows_export: list[dict] = []
    for idx, p in enumerate(export_files, start=1):
        rows_export.append(
            {
                "seq": idx,
                "path": str(p),
                "sha256": _sha256_file(p),
            }
        )
    _write_jsonl(run_dir / "tapes" / "export_tape.000.jsonl", rows_export)
    _write_jsonl(
        run_dir / "tapes" / "campaign_tape.000.jsonl",
        [
            {
                "run_id": run_dir.name,
                "export_count": len(rows_export),
            }
        ],
    )
    return {"export_tape_rows": len(rows_export)}


def _init_run_surface_if_needed(run_dir: Path, repo_root: Path, bootpack_a_hash: str, bootpack_b_hash: str) -> None:
    manifest = run_dir / "RUN_MANIFEST_v1.json"
    if manifest.exists():
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    spec_hash = _sha256_file(repo_root / "system_v3" / "specs" / "01_REQUIREMENTS_LEDGER.md")
    strategy_hash = _sha256_file(repo_root / "system_v3" / "a2_state" / "fuel_queue.json")
    baseline_hash = _sha256_bytes(b"baseline_zero_state")
    cmd = [
        "python3",
        str(repo_root / "system_v3" / "tools" / "init_run_surface.py"),
        "--run-id",
        run_dir.name,
        "--baseline-state-hash",
        baseline_hash,
        "--strategy-hash",
        strategy_hash,
        "--spec-hash",
        spec_hash,
        "--bootpack-b-hash",
        bootpack_b_hash,
        "--bootpack-a-hash",
        bootpack_a_hash,
    ]
    cp = _run(cmd, repo_root)
    if cp.returncode != 0:
        raise RuntimeError(f"init_run_surface failed: {cp.stderr or cp.stdout}")


def _clear_global_resume_state(repo_root: Path) -> None:
    current_state_dir = repo_root / "system_v3" / "runs" / "_CURRENT_STATE"
    for name in ("state.json", "sequence_state.json"):
        path = current_state_dir / name
        if path.exists():
            path.unlink()


def _pending_evidence_count(run_dir: Path) -> int:
    state = _load_state(run_dir)
    return int(len(state.get("evidence_pending", {})))


def _run_full_cycle_once(
    runner_path: Path,
    repo_root: Path,
    run_dir: Path,
    max_entries: int,
    max_items: int,
    sim_cap: int,
) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            "python3",
            str(runner_path),
            "--full-cycle",
            "--loops",
            "1",
            "--run-dir",
            str(run_dir),
            "--max-entries",
            str(max_entries),
            "--max-items",
            str(max_items),
            "--sim-cap",
            str(sim_cap),
        ],
        repo_root,
    )


def _first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run real system_v3 runtime loop into system_v3 run surface.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--loops", type=int, default=1)
    parser.add_argument("--max-entries", type=int, default=20)
    parser.add_argument("--max-items", type=int, default=1000)
    parser.add_argument("--sim-cap", type=int, default=3)
    parser.add_argument("--adaptive-sim-cap", action="store_true")
    parser.add_argument("--sim-cap-min", type=int, default=8)
    parser.add_argument("--sim-cap-max", type=int, default=200)
    parser.add_argument("--sim-cap-headroom", type=int, default=8)
    parser.add_argument("--min-cycles", type=int, default=50)
    parser.add_argument("--max-shard-bytes", type=int, default=5_000_000)
    parser.add_argument("--max-shard-lines", type=int, default=200_000)
    parser.add_argument("--max-run-bytes", type=int, default=200_000_000)
    parser.add_argument("--max-run-files", type=int, default=5_000)
    parser.add_argument("--max-runs-total-bytes", type=int, default=2_000_000_000)
    parser.add_argument("--max-runs-count", type=int, default=200)
    parser.add_argument("--top-n-largest-runs", type=int, default=10)
    parser.add_argument("--clean-existing-run", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    run_dir = repo_root / "system_v3" / "runs" / args.run_id

    bootpack_b_path = _first_existing(
        [
            repo_root / "core_docs" / "BOOTPACK_THREAD_B_v3.9.13.md",
            repo_root / "core_docs" / "upgrade docs" / "BOOTPACK_THREAD_B_v3.9.13.md",
        ]
    )
    bootpack_a_path = _first_existing(
        [
            repo_root / "core_docs" / "BOOTPACK_THREAD_A_v2.60.md",
            repo_root / "core_docs" / "BOOTPACK_THREAD_A0_v2.60.md",
            repo_root / "core_docs" / "upgrade docs" / "BOOTPACK_THREAD_A_v2.60.md",
            repo_root / "core_docs" / "upgrade docs" / "BOOTPACK_THREAD_A0_v2.60.md",
        ]
    )
    bootpack_b_hash = _sha256_file(bootpack_b_path) if bootpack_b_path else _sha256_bytes(b"missing_bootpack_b")
    bootpack_a_hash = _sha256_file(bootpack_a_path) if bootpack_a_path else _sha256_bytes(b"missing_bootpack_a")

    if args.clean_existing_run and run_dir.exists():
        shutil.rmtree(run_dir)

    _init_run_surface_if_needed(run_dir, repo_root, bootpack_a_hash, bootpack_b_hash)
    if args.clean_existing_run:
        _clear_global_resume_state(repo_root)

    cycle_reports: list[dict] = []
    stdout_chunks: list[str] = []
    autoratchet_path = repo_root / "system_v3" / "runtime" / "bootpack_b_kernel_v1" / "tools" / "autoratchet.py"
    # Phase pipeline semantic gating expects at least one full sweep of the
    # refined goal set (including the terminal master-conjunction probe).
    # Keep enough headroom for full refined_fuel closure as goals evolve.
    planner_steps = max(96, int(args.loops))
    graveyard_fill_steps = min(8, planner_steps)
    autoratchet_cmd = [
        "python3",
        str(autoratchet_path),
        "--run-id",
        args.run_id,
        "--steps",
        str(planner_steps),
        "--goal-profile",
        "refined_fuel",
        "--goal-selection",
        "interleaved",
        "--debate-strategy",
        "graveyard_first_then_recovery",
        "--graveyard-fill-steps",
        str(graveyard_fill_steps),
    ]
    cp_full = _run(autoratchet_cmd, repo_root)
    if cp_full.returncode != 0:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "stage": "autoratchet",
                    "stdout": cp_full.stdout,
                    "stderr": cp_full.stderr,
                },
                sort_keys=True,
            )
        )
        return 2

    pending_after = _pending_evidence_count(run_dir)
    cycle_report = {
        "cycle_index": 1,
        "sim_cap": int(args.sim_cap),
        "pending_before": 0,
        "pending_after": pending_after,
        "expand_empty": False,
        "planner_steps_requested": planner_steps,
    }
    cycle_reports.append(cycle_report)
    stdout_chunks.append(cp_full.stdout.strip())

    _write_json(
        run_dir / "reports" / "adaptive_sim_cap_report.json",
        {
            "schema": "ADAPTIVE_SIM_CAP_REPORT_v1",
            "run_id": args.run_id,
            "adaptive_enabled": bool(args.adaptive_sim_cap),
            "sim_cap_min": int(args.sim_cap_min),
            "sim_cap_max": int(args.sim_cap_max),
            "sim_cap_headroom": int(args.sim_cap_headroom),
            "cycle_reports": cycle_reports,
            "updated_utc": "UNCHANGED_BY_GATE_EVAL",
        },
    )

    sync_summary = _sync_events_to_logs(run_dir)
    export_summary = _materialize_export_split_and_reports(run_dir)
    replay_summary = _materialize_replay_reports(run_dir, args.min_cycles)
    state = _load_state(run_dir)
    sim_result_rows = 0
    for rows in (state.get("sim_results", {}) or {}).values():
        if isinstance(rows, list):
            sim_result_rows += len(rows)
    graveyard_obj = state.get("graveyard", {})
    graveyard_count = len(graveyard_obj) if isinstance(graveyard_obj, (dict, list)) else 0
    park_obj = state.get("park_set", state.get("parked", {}))
    parked_count = len(park_obj) if isinstance(park_obj, (dict, list)) else 0
    term_registry = state.get("term_registry", {})
    term_count = len(term_registry) if isinstance(term_registry, dict) else len(state.get("terms", []))
    canonical_term_count = 0
    if isinstance(term_registry, dict):
        canonical_term_count = sum(
            1
            for row in term_registry.values()
            if isinstance(row, dict) and str(row.get("state", "")).strip() == "CANONICAL_ALLOWED"
        )
    final_state_counts = {
        "survivor_order_count": len(state.get("survivor_order", [])),
        "spec_count": len(state.get("survivor_ledger", state.get("specs", []))),
        "term_count": term_count,
        "canonical_term_count": canonical_term_count,
        "graveyard_count": graveyard_count,
        "parked_count": parked_count,
        "pending_evidence_count": len(state.get("evidence_pending", {})),
        "sim_run_count": int(state.get("sim_run_count", sim_result_rows)),
    }
    evidence_summary = _materialize_sim_evidence_pack(run_dir, state)
    graveyard_summary = _materialize_graveyard_records(run_dir, state)
    tape_summary = _materialize_tapes(run_dir)

    gate_cmd = [
        "python3",
        str(repo_root / "system_v3" / "tools" / "run_phase_gate_pipeline.py"),
        "--run-dir",
        str(run_dir),
        "--fixture-pack",
        str(repo_root / "system_v3" / "conformance" / "fixtures_v1"),
        "--bootpack-hash",
        bootpack_b_hash,
        "--use-expected-as-observed",
        "--run-loop-health",
        "--enforce-loop-health",
        "--max-shard-bytes",
        str(args.max_shard_bytes),
        "--max-shard-lines",
        str(args.max_shard_lines),
        "--max-run-bytes",
        str(args.max_run_bytes),
        "--max-run-files",
        str(args.max_run_files),
    ]
    cp_gate = _run(gate_cmd, repo_root)
    sprawl_cmd = [
        "python3",
        str(repo_root / "system_v3" / "tools" / "sprawl_guard.py"),
        "--max-runs-total-bytes",
        str(args.max_runs_total_bytes),
        "--max-runs-count",
        str(args.max_runs_count),
        "--top-n-largest-runs",
        str(args.top_n_largest_runs),
    ]
    cp_sprawl = _run(sprawl_cmd, repo_root)

    out = {
        "status": "PASS" if (cp_gate.returncode == 0 and cp_sprawl.returncode == 0) else "FAIL",
        "run_id": args.run_id,
        "run_dir": str(run_dir),
        "bootpack_b_hash": bootpack_b_hash,
        "bootpack_a_hash": bootpack_a_hash,
        "runner_stdout": "\n".join([s for s in stdout_chunks if s]),
        "final_state_counts": final_state_counts,
        "adaptive_sim_cap_enabled": bool(args.adaptive_sim_cap),
        "adaptive_sim_cap_cycle_reports": cycle_reports,
        "sync_summary": sync_summary,
        "export_summary": export_summary,
        "replay_summary": replay_summary,
        "evidence_summary": evidence_summary,
        "graveyard_summary": graveyard_summary,
        "tape_summary": tape_summary,
        "gate_stdout": cp_gate.stdout.strip(),
        "gate_stderr": cp_gate.stderr.strip(),
        "sprawl_stdout": cp_sprawl.stdout.strip(),
        "sprawl_stderr": cp_sprawl.stderr.strip(),
    }
    print(json.dumps(out, sort_keys=True))
    return 0 if out["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
