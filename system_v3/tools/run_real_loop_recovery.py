from __future__ import annotations

import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path


BEGIN_RECORD_RE = re.compile(r"^BEGIN EXPORT_RECORD (\d{8})$")
END_RECORD_RE = re.compile(r"^END EXPORT_RECORD (\d{8})$")
REQUIRES_RE = re.compile(r"^\s*REQUIRES\s+(\S+)\s+CORR\s+(\S+)\s*$")
ZIP_PACKET_RE = re.compile(r"^(\d+)_([A-Z0-9_]+)\.zip$")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _read_jsonl_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            return []
    return rows


def _count_sim_evidence_blocks(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip() == "BEGIN SIM_EVIDENCE v1":
            count += 1
    return count


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


def _extract_export_records(run_dir: Path) -> list[dict]:
    outbox = run_dir / "outbox"
    records: list[dict] = []

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
                    records.append(
                        {
                            "seq": seq,
                            "block": block,
                            "source_surface": "outbox",
                            "source_path": str(shard),
                        }
                    )
                    i = j + 1
                    break
                j += 1
            else:
                i += 1

    if records:
        seen_seq = {int(row["seq"]) for row in records}
        split_files = sorted(outbox.glob("export_block_*.txt"))
        for idx, path in enumerate(split_files, start=1):
            try:
                seq = int(path.stem.split("_")[-1])
            except ValueError:
                seq = idx
            if seq in seen_seq:
                continue
            records.append(
                {
                    "seq": seq,
                    "block": path.read_text(encoding="utf-8"),
                    "source_surface": "outbox",
                    "source_path": str(path),
                }
            )
        return sorted(records, key=lambda x: int(x["seq"]))

    zip_records: list[dict] = []
    for seq, packet_tag, path in _iter_zip_packet_paths(run_dir):
        if packet_tag != "A0_TO_B_EXPORT_BATCH_ZIP":
            continue
        block = _read_zip_member_text(path, "EXPORT_BLOCK.txt").strip()
        if not block:
            continue
        zip_records.append(
            {
                "seq": seq,
                "block": block + "\n",
                "source_surface": "zip_packets",
                "source_path": f"{path}#EXPORT_BLOCK.txt",
            }
        )
    if zip_records:
        seen_seq = {int(row["seq"]) for row in zip_records}
        split_files = sorted(outbox.glob("export_block_*.txt"))
        for idx, path in enumerate(split_files, start=1):
            try:
                seq = int(path.stem.split("_")[-1])
            except ValueError:
                seq = idx
            if seq in seen_seq:
                continue
            zip_records.append(
                {
                    "seq": seq,
                    "block": path.read_text(encoding="utf-8"),
                    "source_surface": "outbox",
                    "source_path": str(path),
                }
            )
        return sorted(zip_records, key=lambda x: int(x["seq"]))

    split_files = sorted(outbox.glob("export_block_*.txt"))
    for idx, path in enumerate(split_files, start=1):
        try:
            seq = int(path.stem.split("_")[-1])
        except ValueError:
            seq = idx
        records.append(
            {
                "seq": seq,
                "block": path.read_text(encoding="utf-8"),
                "source_surface": "outbox",
                "source_path": str(path),
            }
        )
    return sorted(records, key=lambda x: int(x["seq"]))


def _materialize_export_split_and_reports(run_dir: Path, *, allow_reconstructed_artifacts: bool = False) -> dict:
    reports = run_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    records = _extract_export_records(run_dir)
    dependency_rows: list[dict] = []

    compile_reports = sorted(reports.glob("compile_report_*.json"))
    dependency_reports = sorted(reports.glob("dependency_report_*.json"))
    preflight_reports = sorted(reports.glob("preflight_report_*.json"))
    if compile_reports or dependency_reports or preflight_reports:
        return {
            "export_count": len(records),
            "dependency_edge_count": 0,
            "report_mode": "PRESERVED_EXISTING",
            "reconstructed_artifacts": False,
        }

    if not allow_reconstructed_artifacts:
        return {
            "export_count": len(records),
            "dependency_edge_count": 0,
            "report_mode": "STRICT_NO_RECONSTRUCTION",
            "reconstructed_artifacts": False,
        }

    for row in records:
        seq = int(row.get("seq", 0))
        block = str(row.get("block", ""))
        source_surface = str(row.get("source_surface", "unknown"))
        source_path = str(row.get("source_path", ""))
        lines = block.splitlines()
        if lines:
            if lines[0].strip() in {"BEGIN EXPORT_BLOCK v1", "BEGIN EXPORT_BLOCK vN"}:
                lines[0] = "BEGIN EXPORT_BLOCK vN"
            if lines[-1].strip() in {"END EXPORT_BLOCK v1", "END EXPORT_BLOCK vN"}:
                lines[-1] = "END EXPORT_BLOCK vN"
        block = "\n".join(lines).strip() + "\n"
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
                "export_block_path": source_path,
                "export_block_sha256": export_hash,
                "source_surface": source_surface,
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
        "report_mode": "RECONSTRUCTED_FROM_EXPORT_BLOCKS",
        "reconstructed_artifacts": True,
    }


def _sync_events_to_logs(run_dir: Path, *, allow_reconstructed_artifacts: bool = False) -> dict:
    root_event_files = sorted(run_dir.glob("events.*.jsonl"))
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    existing_log_events = sorted(logs_dir.glob("events.*.jsonl"))
    if existing_log_events:
        return {
            "copied_event_files": 0,
            "generated_event_rows": 0,
            "event_mode": "PRESERVED_EXISTING",
            "reconstructed_artifacts": False,
        }

    copied = 0
    for path in root_event_files:
        dst = logs_dir / path.name
        shutil.copyfile(path, dst)
        copied += 1
    if copied > 0:
        return {
            "copied_event_files": copied,
            "generated_event_rows": 0,
            "event_mode": "COPIED_ROOT_EVENTS",
            "reconstructed_artifacts": False,
        }

    if not allow_reconstructed_artifacts:
        return {
            "copied_event_files": 0,
            "generated_event_rows": 0,
            "event_mode": "MISSING_CANONICAL_EVENTS",
            "reconstructed_artifacts": False,
        }

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
    return {
        "copied_event_files": 0,
        "generated_event_rows": len(rows),
        "event_mode": "RECONSTRUCTED_FROM_ZIP_HEADERS",
        "reconstructed_artifacts": True,
    }


def _materialize_graveyard_records(run_dir: Path, state: dict, *, allow_reconstructed_artifacts: bool = False) -> dict:
    b_reports = run_dir / "b_reports"
    b_reports.mkdir(parents=True, exist_ok=True)
    path = b_reports / "graveyard_records.000.jsonl"
    existing_rows = _read_jsonl_rows(path)
    if existing_rows:
        return {
            "graveyard_records": len(existing_rows),
            "graveyard_mode": "PRESERVED_EXISTING",
            "reconstructed_artifacts": False,
        }
    if not allow_reconstructed_artifacts:
        return {
            "graveyard_records": 0,
            "graveyard_mode": "MISSING_CANONICAL_GRAVEYARD_RECORDS",
            "reconstructed_artifacts": False,
        }
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
    return {
        "graveyard_records": len(rows),
        "graveyard_mode": "RECONSTRUCTED_FROM_STATE",
        "reconstructed_artifacts": True,
    }


def _materialize_sim_evidence_pack(run_dir: Path, state: dict, *, allow_reconstructed_artifacts: bool = False) -> dict:
    sim_dir = run_dir / "sim"
    sim_dir.mkdir(parents=True, exist_ok=True)
    pack_path = sim_dir / "sim_evidence_pack_0001.txt"
    if pack_path.exists():
        return {
            "sim_manifest_count": 0,
            "evidence_blocks": _count_sim_evidence_blocks(pack_path),
            "evidence_mode": "PRESERVED_EXISTING",
            "reconstructed_artifacts": False,
        }

    packet_blocks: list[str] = []
    for _, packet_tag, packet_path in _iter_zip_packet_paths(run_dir):
        if packet_tag != "SIM_TO_A0_SIM_RESULT_ZIP":
            continue
        block = _read_zip_member_text(packet_path, "SIM_EVIDENCE.txt").strip()
        if block:
            packet_blocks.append(block)
    if packet_blocks:
        if allow_reconstructed_artifacts:
            pack_path.write_text("\n".join(packet_blocks) + "\n", encoding="utf-8")
            return {
                "sim_manifest_count": len(packet_blocks),
                "evidence_blocks": len(packet_blocks),
                "evidence_mode": "RECONSTRUCTED_FROM_SIM_ZIPS",
                "reconstructed_artifacts": True,
            }
        return {
            "sim_manifest_count": len(packet_blocks),
            "evidence_blocks": len(packet_blocks),
            "evidence_mode": "VISIBLE_IN_SIM_ZIPS_ONLY",
            "reconstructed_artifacts": False,
        }

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
        return {
            "sim_manifest_count": 0,
            "evidence_blocks": 0,
            "evidence_mode": "MISSING_CANONICAL_SIM_EVIDENCE",
            "reconstructed_artifacts": False,
        }

    if not allow_reconstructed_artifacts:
        return {
            "sim_manifest_count": len(manifest_rows),
            "evidence_blocks": 0,
            "evidence_mode": "STRICT_NO_RECONSTRUCTION",
            "reconstructed_artifacts": False,
        }

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
    for idx, (manifest_hash, payload) in enumerate(manifest_rows):
        target_spec = str(payload.get("target_spec", "S_UNKNOWN"))
        target_token = str(payload.get("target_token", "EV_UNKNOWN")).strip('"')
        lines = [
            "BEGIN SIM_EVIDENCE v1",
            f"SIM_ID: {payload.get('sim_id', manifest_hash)}",
            f"CODE_HASH_SHA256: {payload.get('code_hash_sha256', '')}",
            f"OUTPUT_HASH_SHA256: {payload.get('output_hash_sha256', '')}",
            f"INPUT_HASH_SHA256: {payload.get('input_hash_sha256', '')}",
            f"RUN_MANIFEST_SHA256: {manifest_hash}",
            f"EVIDENCE_SIGNAL {target_spec} CORR {target_token}",
        ]
        if idx == 0 and kill_lines:
            lines.extend(kill_lines)
        lines.append("END SIM_EVIDENCE v1")
        blocks.append("\n".join(lines))

    pack_path.write_text("\n".join(blocks) + "\n", encoding="utf-8")
    return {
        "sim_manifest_count": len(manifest_rows),
        "evidence_blocks": len(blocks),
        "evidence_mode": "RECONSTRUCTED_FROM_MANIFESTS",
        "reconstructed_artifacts": True,
    }


def _materialize_tapes(run_dir: Path, *, allow_reconstructed_artifacts: bool = False) -> dict:
    records = _extract_export_records(run_dir)
    export_tape_path = run_dir / "tapes" / "export_tape.000.jsonl"
    campaign_tape_path = run_dir / "tapes" / "campaign_tape.000.jsonl"

    existing_export_rows = _read_jsonl_rows(export_tape_path)
    existing_campaign_rows = _read_jsonl_rows(campaign_tape_path)

    if existing_export_rows and existing_campaign_rows:
        return {
            "export_tape_rows": len(existing_export_rows),
            "campaign_tape_rows": len(existing_campaign_rows),
            "tape_mode": "PRESERVED_EXISTING",
            "reconstructed_artifacts": False,
        }

    if not allow_reconstructed_artifacts:
        return {
            "export_tape_rows": len(existing_export_rows),
            "campaign_tape_rows": len(existing_campaign_rows),
            "tape_mode": "MISSING_CANONICAL_TAPES",
            "reconstructed_artifacts": False,
        }

    rows_export: list[dict] = []
    for row in records:
        rows_export.append(
            {
                "seq": int(row.get("seq", 0)),
                "export_id": "UNKNOWN_EXPORT_ID",
                "export_block_relpath": str(row.get("source_path", "")),
                "export_block_sha256": _sha256_bytes(str(row.get("block", "")).encode("utf-8")),
            }
        )
    if not existing_export_rows:
        _write_jsonl(export_tape_path, rows_export)
    if not existing_campaign_rows:
        _write_jsonl(
            campaign_tape_path,
            [
                {
                    "run_id": run_dir.name,
                    "export_count": len(rows_export),
                    "note": "FALLBACK_SUMMARY_ONLY",
                }
            ],
        )
    return {
        "export_tape_rows": len(existing_export_rows) if existing_export_rows else len(rows_export),
        "campaign_tape_rows": len(existing_campaign_rows) if existing_campaign_rows else 1,
        "tape_mode": "FALLBACK_MATERIALIZED",
        "reconstructed_artifacts": True,
    }


def _reconstructed_artifact_classes(
    sync_summary: dict,
    export_summary: dict,
    evidence_summary: dict,
    graveyard_summary: dict,
    tape_summary: dict,
) -> list[str]:
    classes: list[str] = []
    for name, summary in [
        ("events", sync_summary),
        ("export_reports", export_summary),
        ("sim_evidence_pack", evidence_summary),
        ("graveyard_records", graveyard_summary),
        ("tapes", tape_summary),
    ]:
        if bool(summary.get("reconstructed_artifacts")):
            classes.append(name)
    return classes
