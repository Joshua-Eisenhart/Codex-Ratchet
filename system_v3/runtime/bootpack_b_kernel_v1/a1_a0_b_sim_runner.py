import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
import zipfile

from a0_compiler import compile_export_block, compute_state_transition_digest
from a1_autowiggle import AutowiggleConfig
from a1_bridge import A1Bridge
from a1_model_selector import select_best_model_across_runs
from a1_strategy import load_strategy
from containers import parse_export_block
from pipeline import A0BSimPipeline
from snapshot import build_snapshot_v2
from state import KernelState
from zip_protocol_v2_validator import validate_zip_protocol_v2
from zip_protocol_v2_writer import write_zip_protocol_v2


_FIXED_CREATED_UTC = "1980-01-01T00:00:00Z"
_SEQ_SOURCES = {"A2", "A1", "A0", "B", "SIM"}
_RUN_SUBDIR_EXPLICIT_ALIASES = {
    "a1_inbox": "a1_packet_inbox_surface",
    "a1_strategies": "optional_a1_strategy_duplicate_surface",
    "b_reports": "thread_b_report_surface",
    "logs": "append_only_event_log_surface",
    "outbox": "deterministic_outbound_export_block_cache_surface",
    "reports": "deterministic_compile_and_kernel_report_surface",
    "sim": "optional_plaintext_sim_evidence_duplicate_surface",
    "snapshots": "optional_plaintext_snapshot_duplicate_surface",
    "tapes": "append_only_tape_surface",
    "zip_packets": "zip_protocol_v2_packet_journal_surface",
}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def _relpath(run_dir: Path, path: str | Path) -> str:
    if not path:
        return ""
    try:
        return str(Path(path).resolve().relative_to(run_dir.resolve()))
    except Exception:
        return str(path)


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            rows.append(json.loads(text))
        except Exception:
            continue
    return rows


def _write_soak_report(run_dir: Path, summary: dict, events_path: Path) -> None:
    rows = _read_jsonl(events_path)
    tag_counts: dict[str, int] = {}
    for row in rows:
        for tag in row.get("reject_tags", []) if isinstance(row.get("reject_tags"), list) else []:
            tag_counts[str(tag)] = tag_counts.get(str(tag), 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))[:10]
    last_rows = rows[-20:]

    lines = []
    lines.append("# SOAK REPORT")
    lines.append("")
    lines.append(f"- cycle_count: {summary.get('steps_completed', 0)}")
    lines.append(f"- accepted_total: {summary.get('accepted_total', 0)}")
    lines.append(f"- parked_total: {summary.get('parked_total', 0)}")
    lines.append(f"- rejected_total: {summary.get('rejected_total', 0)}")
    lines.append(f"- stop_reason: {summary.get('stop_reason', '')}")
    lines.append("")
    lines.append("## top_failure_tags")
    if top_tags:
        for tag, count in top_tags:
            lines.append(f"- {tag}: {count}")
    else:
        lines.append("- NONE")
    lines.append("")
    lines.append("## sim_tier_legend")
    lines.append("- T0_ATOM: atomic / minimal primitive checks")
    lines.append("- T1_COMPOUND: small compositions (few linked terms)")
    lines.append("- T2_OPERATOR: operator-level objects (transformations/actions)")
    lines.append("- T3_STRUCTURE: multi-part structures / composed systems")
    lines.append("")
    lines.append("## last_20_events")
    if not last_rows:
        lines.append("- NONE")
    else:
        for row in last_rows:
            lines.append(f"- {json.dumps(row, sort_keys=True, separators=(',', ':'))}")
    (run_dir / "soak_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _update_runs_registry(runs_root: Path, summary: dict) -> None:
    """
    Writes small, human-operational indexing metadata to runs/.

    This does not affect determinism: it is out-of-band bookkeeping for humans to
    identify the "current" ratchet run and to list runs without relying on folder names.
    """
    runs_root.mkdir(parents=True, exist_ok=True)
    run_id = str(summary.get("run_id", "")).strip()
    if not run_id:
        return

    (runs_root / "_CURRENT_RUN.txt").write_text(run_id + "\n", encoding="utf-8")

    # Append-only registry log.
    row = {
        "run_id": run_id,
        "steps_completed": int(summary.get("steps_completed", 0) or 0),
        "stop_reason": str(summary.get("stop_reason", "") or ""),
        "accepted_total": int(summary.get("accepted_total", 0) or 0),
        "parked_total": int(summary.get("parked_total", 0) or 0),
        "rejected_total": int(summary.get("rejected_total", 0) or 0),
        "final_state_hash": str(summary.get("final_state_hash", "") or ""),
        "sim_registry_count": int(summary.get("sim_registry_count", 0) or 0),
        "master_sim_status": str(summary.get("master_sim_status", "") or ""),
    }
    registry_path = runs_root / "_RUNS_REGISTRY.jsonl"
    with registry_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _campaign_strategy_meta(compiled: dict) -> tuple[str, str]:
    repaired = compiled.get("repaired_strategy", {}) if isinstance(compiled, dict) else {}
    if not isinstance(repaired, dict):
        return "", ""
    sim_program = repaired.get("sim_program", {})
    if not isinstance(sim_program, dict):
        return "", ""
    program_id = str(sim_program.get("program_id", "")).strip()
    replay_source = str(sim_program.get("replay_source", "")).strip()
    return program_id, replay_source


def _now_run_id() -> str:
    return time.strftime("RUN__%Y%m%d_%H%M%SZ__a1_a0_b_sim", time.gmtime())


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


_ID_TOKEN_RE = re.compile(r"\b[SPRFWKM][A-Za-z0-9_]*\b")
_EVIDENCE_TOKEN_RE = re.compile(r"\b(?:PT|E|MT|TT|LT|PP|KT)_[A-Za-z0-9_]+\b")


def _content_digest(export_text: str) -> str:
    block = parse_export_block(export_text)
    payload = "\n".join(block.content_lines)
    return _sha256_text(payload)


def _structural_digest(export_text: str) -> str:
    block = parse_export_block(export_text)
    normalized_lines: list[str] = []
    for line in block.content_lines:
        row = _EVIDENCE_TOKEN_RE.sub("<TOKEN>", line)
        row = _ID_TOKEN_RE.sub("<ID>", row)
        normalized_lines.append(row)
    return _sha256_text("\n".join(normalized_lines))


def _graveyard_by_target_class(state: KernelState) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item_id in sorted(state.graveyard.keys()):
        meta = state.spec_meta.get(item_id, {})
        if meta.get("kind") != "SIM_SPEC":
            continue
        target_class = str(meta.get("target_class", "")).strip()
        if not target_class:
            continue
        counts[target_class] = counts.get(target_class, 0) + 1
    # Backward-compat fallback for old states without explicit graveyard entries.
    if counts:
        return counts
    killed_ids = {
        str(row.get("id", "")).strip()
        for row in state.kill_log
        if str(row.get("tag", "")) == "KILL_SIGNAL" and str(row.get("id", "")).strip()
    }
    for item_id in sorted(killed_ids):
        meta = state.spec_meta.get(item_id, {})
        if meta.get("kind") != "SIM_SPEC":
            continue
        target_class = str(meta.get("target_class", "")).strip()
        if not target_class:
            continue
        counts[target_class] = counts.get(target_class, 0) + 1
    return counts


def _assert_no_legacy_runtime_modules_loaded() -> None:
    banned_fragments = ("/runtime/loop_minimal/", "/runtime/ratchet_core/")
    offenders: list[str] = []
    for name, module in sorted(sys.modules.items()):
        module_file = getattr(module, "__file__", "") or ""
        normalized = str(module_file).replace("\\", "/")
        if any(fragment in normalized for fragment in banned_fragments):
            offenders.append(f"{name}:{normalized}")
    if offenders:
        raise RuntimeError("legacy runtime module loaded: " + ";".join(offenders[:10]))


def _load_resume_state(
    *,
    run_id: str,
    run_state_path: Path,
    run_sequence_state_path: Path,
    run_zip_packets_dir: Path,
    current_state_path: Path,
    sequence_state_path: Path,
) -> tuple[KernelState, dict[tuple[str, str], int], dict[str, int]]:
    state = KernelState()
    seq_state: dict[tuple[str, str], int] = {}
    seq_by_source: dict[str, int] = {}

    # Prefer run-local state to avoid cross-run contamination from shared current_state.
    state_source = run_state_path if run_state_path.exists() else current_state_path
    if state_source.exists():
        payload = json.loads(state_source.read_text(encoding="utf-8"))
        state = KernelState.from_dict(payload)
        heavy_path = run_state_path.with_name("state.heavy.json")
        if state_source == run_state_path and heavy_path.exists():
            heavy_payload = json.loads(heavy_path.read_text(encoding="utf-8"))
            state.apply_heavy_dict(heavy_payload)

    # Prefer run-local sequence state; fallback to shared state for legacy runs.
    seq_source = run_sequence_state_path if run_sequence_state_path.exists() else sequence_state_path
    if seq_source.exists():
        payload = json.loads(seq_source.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and str(payload.get("run_id", "")) == run_id:
            raw_seq = payload.get("seq_by_source", {})
            if isinstance(raw_seq, dict):
                for source, value in raw_seq.items():
                    source_key = str(source)
                    if source_key not in _SEQ_SOURCES:
                        continue
                    seq_value = int(value)
                    if seq_value < 0:
                        raise ValueError(f"sequence_regression_protection:negative:{source_key}")
                    seq_by_source[source_key] = seq_value
                    seq_state[(run_id, source_key)] = seq_value

    # Backfill sequence maxima from existing run packets when sequence state
    # is unavailable (legacy runs / interrupted writes).
    if not seq_by_source and run_zip_packets_dir.exists():
        for zip_path in sorted(run_zip_packets_dir.glob("*.zip")):
            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    header = json.loads(zf.read("ZIP_HEADER.json").decode("utf-8"))
            except Exception:
                continue
            if str(header.get("run_id", "")) != run_id:
                continue
            source = str(header.get("source_layer", ""))
            if source not in _SEQ_SOURCES:
                continue
            try:
                seq = int(header.get("sequence", 0))
            except Exception:
                continue
            if seq < 0:
                continue
            prev = int(seq_by_source.get(source, 0))
            if seq > prev:
                seq_by_source[source] = seq
        for source, seq in seq_by_source.items():
            seq_state[(run_id, source)] = int(seq)

    return state, seq_state, seq_by_source


def _persist_resume_state(
    *,
    run_id: str,
    state: KernelState,
    seq_by_source: dict[str, int],
    run_state_path: Path,
    run_sequence_state_path: Path,
    current_state_path: Path,
    sequence_state_path: Path,
) -> None:
    run_state_text = state.to_json(include_heavy=False)
    heavy_state_text = json.dumps(state.heavy_dict(), sort_keys=True, separators=(",", ":")) + "\n"
    run_state_hash = _sha256_text(run_state_text)
    seq_payload = {
        "run_id": run_id,
        "seq_by_source": {key: int(seq_by_source.get(key, 0)) for key in sorted(_SEQ_SOURCES)},
    }

    # Run-local persistence (authoritative for resume continuity).
    run_state_path.parent.mkdir(parents=True, exist_ok=True)
    run_state_path.write_text(run_state_text, encoding="utf-8")
    run_state_path.with_name("state.heavy.json").write_text(heavy_state_text, encoding="utf-8")
    _write_json(run_sequence_state_path, seq_payload)

    # Shared persistence is a lean resume pointer/cache, not a duplicate full state.
    current_payload = {
        "schema": "CURRENT_RUN_POINTER_v1",
        "run_id": run_id,
        "run_state_relpath": _relpath(current_state_path.parent.parent, run_state_path),
        "run_sequence_state_relpath": _relpath(current_state_path.parent.parent, run_sequence_state_path),
        "state_hash": run_state_hash,
        "canonical_ledger_count": len(state.canonical_ledger),
        "sim_registry_count": len(state.sim_registry),
    }
    current_state_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(current_state_path, current_payload)
    _write_json(sequence_state_path, seq_payload)


def _remove_tree_retry(path: Path, attempts: int = 8) -> None:
    for _ in range(attempts):
        if not path.exists():
            return
        shutil.rmtree(path, ignore_errors=True)
    if path.exists():
        raise RuntimeError(f"clean_remove_failed:{path}")


def _ensure_explicit_run_aliases(run_dir: Path) -> None:
    for short_name, long_name in sorted(_RUN_SUBDIR_EXPLICIT_ALIASES.items()):
        target = run_dir / short_name
        link = run_dir / long_name
        if not target.exists():
            continue
        if link.exists() or link.is_symlink():
            continue
        rel_target = os.path.relpath(str(target), str(link.parent))
        link.symlink_to(rel_target)


def run_loop(
    strategy_path: Path,
    steps: int,
    run_id: str,
    a1_source: str,
    a1_model: str,
    a1_timeout_sec: int,
    autowiggle_config: AutowiggleConfig | None = None,
    clean: bool = False,
    retain_diagnostics: bool = True,
    retain_snapshots: bool = False,
    retain_sim_text: bool = False,
    runs_root_override: str | None = None,
) -> tuple[Path, str]:
    _assert_no_legacy_runtime_modules_loaded()
    bootpack_root = Path(__file__).resolve().parent
    system_v3_root = bootpack_root.parents[1]
    runs_root = (
        Path(str(runs_root_override)).expanduser().resolve()
        if runs_root_override and str(runs_root_override).strip()
        else (system_v3_root / "runs")
    )
    runs_root.mkdir(parents=True, exist_ok=True)
    run_dir = runs_root / run_id
    run_state_path = run_dir / "state.json"
    run_sequence_state_path = run_dir / "sequence_state.json"
    current_state_path = runs_root / "_CURRENT_STATE" / "state.json"
    sequence_state_path = runs_root / "_CURRENT_STATE" / "sequence_state.json"
    if clean and run_dir.exists():
        _remove_tree_retry(run_dir)
    if clean:
        if current_state_path.exists():
            current_state_path.unlink()
        if sequence_state_path.exists():
            sequence_state_path.unlink()
    if retain_diagnostics:
        (run_dir / "outbox").mkdir(parents=True, exist_ok=True)
        (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    # Minimal deterministic surfaces that must exist regardless of diagnostics.
    (run_dir / "b_reports").mkdir(parents=True, exist_ok=True)
    (run_dir / "tapes").mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    (run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
    # These dirs exist for compatibility with prior runs/tools, but the default
    # behavior is now "ZIP-only" to avoid redundant disk bloat.
    (run_dir / "sim").mkdir(parents=True, exist_ok=True)
    (run_dir / "snapshots").mkdir(parents=True, exist_ok=True)
    if retain_diagnostics:
        (run_dir / "a1_strategies").mkdir(parents=True, exist_ok=True)
    (run_dir / "a1_inbox").mkdir(parents=True, exist_ok=True)
    _ensure_explicit_run_aliases(run_dir)

    events_path = run_dir / "logs" / "events.000.jsonl"
    legacy_events_path = run_dir / "events.jsonl"
    if legacy_events_path.exists() and not events_path.exists():
        events_path = legacy_events_path
    elif not legacy_events_path.exists() and events_path != legacy_events_path:
        try:
            rel_target = os.path.relpath(str(events_path), str(legacy_events_path.parent))
            legacy_events_path.symlink_to(rel_target)
        except OSError:
            # Best-effort only; determinism is carried by the canonical logs/ shard path.
            pass
    if clean:
        state = KernelState()
        seq_state: dict[tuple[str, str], int] = {}
        seq_by_source: dict[str, int] = {}
        # Deterministic empty tape shards.
        for tape in [
            run_dir / "tapes" / "export_tape.000.jsonl",
            run_dir / "tapes" / "campaign_tape.000.jsonl",
        ]:
            tape.write_text("", encoding="utf-8")
    else:
        state, seq_state, seq_by_source = _load_resume_state(
            run_id=run_id,
            run_state_path=run_state_path,
            run_sequence_state_path=run_sequence_state_path,
            run_zip_packets_dir=run_dir / "zip_packets",
            current_state_path=current_state_path,
            sequence_state_path=sequence_state_path,
        )
    pipeline = A0BSimPipeline()
    a1 = A1Bridge(
        source=a1_source,
        model=a1_model,
        timeout_sec=a1_timeout_sec,
        inbox_dir=run_dir / "a1_inbox",
        autowiggle_config=autowiggle_config,
    )

    def _next_seq(source_layer: str) -> int:
        seq_by_source[source_layer] = int(seq_by_source.get(source_layer, 0)) + 1
        return int(seq_by_source[source_layer])

    def _validate_ok(zip_path: Path) -> None:
        result = validate_zip_protocol_v2(str(zip_path), seq_state)
        outcome = str(result.get("outcome", ""))
        if outcome != "OK":
            raise ValueError(f"zip_protocol_v2_invalid:{outcome}:{result}")
        with zipfile.ZipFile(zip_path, "r") as zf:
            header = json.loads(zf.read("ZIP_HEADER.json").decode("utf-8"))
        run = str(header.get("run_id", ""))
        src = str(header.get("source_layer", ""))
        seq = int(header.get("sequence", 0))
        seq_state[(run, src)] = int(seq)

    step_offset = int(len(state.canonical_ledger))
    repeated_noop = 0
    repeated_schema_fail = 0
    a1_generation_fail_count = 0
    last_tags: list[str] = []
    accepted_total = 0
    parked_total = 0
    rejected_total = 0
    stop_reason = "MAX_STEPS"
    escalation_reasons: list[str] = []
    strategy_digests: set[str] = set()
    export_content_digests: set[str] = set()
    export_structural_digests: set[str] = set()
    campaign_program_ids: set[str] = set()
    campaign_stage_ids_seen: set[str] = set()
    campaign_suite_modes_seen: set[str] = set()
    blocked_stage_ids_seen: set[str] = set()
    blocked_suite_modes_seen: set[str] = set()
    failure_isolation_total = 0
    graveyard_rescue_total = 0
    replay_from_tape_total = 0
    final_coverage_report = {}
    steps_completed_local = 0

    for step in range(1, steps + 1):
        global_step = step_offset + step
        steps_completed_local = step
        state_hash_before = state.hash()
        try:
            strategy_result = a1.next_strategy(
                strategy_path=strategy_path,
                step=global_step,
                state_hash=state_hash_before,
                last_tags=last_tags,
                state=state,
            )
            strategy = strategy_result["strategy"]
            a1_generation_fail_count = 0
        except Exception as exc:
            if a1_source == "packet" and str(exc) == "a1_inbox_empty":
                base_strategy = load_strategy(strategy_path)["strategy"]
                out_zip = run_dir / "zip_packets" / f"{_next_seq('A0'):06d}_A0_TO_A1_SAVE_ZIP.zip"
                write_zip_protocol_v2(
                    out_path=out_zip,
                    header={
                        "zip_type": "A0_TO_A1_SAVE_ZIP",
                        "direction": "BACKWARD",
                        "source_layer": "A0",
                        "target_layer": "A1",
                        "run_id": run_id,
                        "sequence": seq_by_source["A0"],
                        "created_utc": _FIXED_CREATED_UTC,
                        "compiler_version": "bootpack_b_kernel_v1",
                    },
                    payload_json={
                        "A0_SAVE_SUMMARY.json": {
                            "schema": "A0_SAVE_SUMMARY_v1",
                            "run_id": run_id,
                            "step": global_step,
                            "state_hash": state_hash_before,
                            "last_reject_tags": sorted(set(last_tags)),
                            "base_strategy": base_strategy,
                        }
                    },
                )
                _validate_ok(out_zip)
                _append_jsonl(
                    events_path,
                    {
                        "step": global_step,
                        "event": "a1_strategy_request_emitted",
                        "source": "ZIP_PROTOCOL_v2",
                        "state_hash": state_hash_before,
                        "last_reject_tags": sorted(set(last_tags)),
                        "a0_to_a1_save_zip_relpath": _relpath(run_dir, out_zip),
                    },
                )
                stop_reason = "A1_NEEDS_EXTERNAL_STRATEGY"
                break
            a1_generation_fail_count += 1
            _append_jsonl(
                events_path,
                {
                    "step": global_step,
                    "event": "a1_generation_fail",
                    "source": a1_source,
                    "model": "",
                    "error": str(exc)[:1200],
                    "a1_generation_fail_count": a1_generation_fail_count,
                },
            )
            # Escalation is strictly reserved for operator-set exhaustion.
            if a1_generation_fail_count >= 3:
                stop_reason = "A1_GENERATION_FAIL_LIMIT"
                break
            continue

        if retain_diagnostics:
            strategy_file = run_dir / "a1_strategies" / f"a1_strategy_{global_step:04d}.json"
            _write_json(strategy_file, strategy)
        strategy_digest = _sha256_text(json.dumps(strategy, sort_keys=True, separators=(",", ":")))
        strategy_digests.add(strategy_digest)

        a1_zip = run_dir / "zip_packets" / f"{_next_seq('A1'):06d}_A1_TO_A0_STRATEGY_ZIP.zip"
        write_zip_protocol_v2(
            out_path=a1_zip,
            header={
                "zip_type": "A1_TO_A0_STRATEGY_ZIP",
                "direction": "FORWARD",
                "source_layer": "A1",
                "target_layer": "A0",
                "run_id": run_id,
                "sequence": seq_by_source["A1"],
                "created_utc": _FIXED_CREATED_UTC,
                "compiler_version": "",
            },
            payload_json={"A1_STRATEGY_v1.json": strategy},
        )
        _validate_ok(a1_zip)
        strategy_packet = {"relpath": _relpath(run_dir, a1_zip)}

        # Packet mode already supplies explicit A1 artifacts; keep compile deterministic
        # and avoid carrying prior reject tags as an implicit repair channel.
        compile_prior_tags = [] if a1_source == "packet" else last_tags
        compiled = compile_export_block(
            state=state,
            strategy=strategy,
            canonical_state_hash=state_hash_before,
            step=global_step,
            prior_tags=compile_prior_tags,
        )
        export_text = compiled["export_text"]
        export_file = run_dir / "outbox" / f"export_block_{global_step:04d}.txt"
        if retain_diagnostics:
            export_file.write_text(export_text, encoding="utf-8")
        export_content_digest = _content_digest(export_text)
        export_structural_digest = _structural_digest(export_text)
        export_content_digests.add(export_content_digest)
        export_structural_digests.add(export_structural_digest)
        if retain_diagnostics:
            compile_report_file = run_dir / "reports" / f"a0_compile_{global_step:04d}.json"
            _write_json(compile_report_file, compiled["report"])
        else:
            compile_report_file = run_dir / "_omitted_a0_compile_report.json"
        exhausted_tags = list(compiled["report"].get("operator_exhausted_tags", []))
        if exhausted_tags and a1_source != "packet":
            stop_reason = "A2_OPERATOR_SET_EXHAUSTED"
            escalation_reasons = [f"OPERATOR_SET_EXHAUSTED:{tag}" for tag in sorted(set(exhausted_tags))]
            recommended_model, recommended_source = select_best_model_across_runs(run_dir.parent)
            request_path = run_dir / "reports" / "a2_escalation_request.json"
            _write_json(
                request_path,
                {
                    "run_id": run_id,
                    "step": global_step,
                    "stop_reason": stop_reason,
                    "reasons": escalation_reasons,
                    "prior_reject_tags": sorted(set(last_tags)),
                    "operator_exhausted_tags": sorted(set(exhausted_tags)),
                    "compile_report_path": str(compile_report_file),
                    "recommended_local_model": recommended_model,
                    "recommended_model_source": recommended_source,
                },
            )
            break

        a0_export_zip = run_dir / "zip_packets" / f"{_next_seq('A0'):06d}_A0_TO_B_EXPORT_BATCH_ZIP.zip"
        write_zip_protocol_v2(
            out_path=a0_export_zip,
            header={
                "zip_type": "A0_TO_B_EXPORT_BATCH_ZIP",
                "direction": "FORWARD",
                "source_layer": "A0",
                "target_layer": "B",
                "run_id": run_id,
                "sequence": seq_by_source["A0"],
                "created_utc": _FIXED_CREATED_UTC,
                "compiler_version": "bootpack_b_kernel_v1",
            },
            payload_text={"EXPORT_BLOCK.txt": export_text},
        )
        _validate_ok(a0_export_zip)
        export_packet = {"relpath": _relpath(run_dir, a0_export_zip)}

        eval_result = pipeline.handle_message(export_text, state, batch_id=f"STEP_{global_step:04d}")
        report_file = run_dir / "b_reports" / f"b_report_{global_step:04d}.txt"
        report_file.write_text(eval_result.get("output_text", ""), encoding="utf-8")

        accepted = 0
        parked = 0
        rejected = 0
        reject_tags: list[str] = []
        if eval_result.get("result"):
            accepted = len(eval_result["result"]["accepted"])
            parked = len(eval_result["result"]["parked"])
            rejected = len(eval_result["result"]["rejected"])
            reject_tags = sorted({row.get("reason", "") for row in eval_result["result"]["rejected"]})
        accepted_total += accepted
        parked_total += parked
        rejected_total += rejected
        last_tags = reject_tags
        if reject_tags and all(tag == "SCHEMA_FAIL" for tag in reject_tags):
            repeated_schema_fail += 1
        else:
            repeated_schema_fail = 0

        snapshot_text = build_snapshot_v2(state, timestamp_utc="", lexicographic=True)
        if retain_snapshots:
            snapshot_path = run_dir / "snapshots" / f"snapshot_{global_step:04d}.txt"
            snapshot_path.write_text(snapshot_text, encoding="utf-8")
        b_state_zip = run_dir / "zip_packets" / f"{_next_seq('B'):06d}_B_TO_A0_STATE_UPDATE_ZIP.zip"
        write_zip_protocol_v2(
            out_path=b_state_zip,
            header={
                "zip_type": "B_TO_A0_STATE_UPDATE_ZIP",
                "direction": "BACKWARD",
                "source_layer": "B",
                "target_layer": "A0",
                "run_id": run_id,
                "sequence": seq_by_source["B"],
                "created_utc": _FIXED_CREATED_UTC,
                "compiler_version": "",
            },
            payload_text={"THREAD_S_SAVE_SNAPSHOT_v2.txt": snapshot_text},
        )
        _validate_ok(b_state_zip)
        snapshot_hash = _sha256_text(snapshot_text)
        export_block_hash = str(compiled["report"].get("export_block_sha256", ""))
        compiler_version = str(compiled["report"].get("compiler_version", ""))
        state_transition_digest = compute_state_transition_digest(
            previous_state_hash=state_hash_before,
            export_block_hash=export_block_hash,
            snapshot_hash=snapshot_hash,
            compiler_version=compiler_version,
        )
        try:
            export_id = parse_export_block(export_text).export_id
        except Exception:
            export_id = "UNKNOWN_EXPORT_ID"
        export_relpath = str(a0_export_zip.relative_to(run_dir))
        b_report_relpath = str(report_file.relative_to(run_dir))
        _append_jsonl(
            run_dir / "tapes" / "export_tape.000.jsonl",
            {
                "seq": int(seq_by_source.get("A0", 0)),
                "export_id": export_id,
                "export_block_sha256": export_block_hash,
                "export_block_relpath": export_relpath,
            },
        )
        _append_jsonl(
            run_dir / "tapes" / "campaign_tape.000.jsonl",
            {
                "seq": int(seq_by_source.get("A0", 0)),
                "export_id": export_id,
                "export_block_sha256": export_block_hash,
                "export_block_relpath": export_relpath,
                "thread_b_report_sha256": _sha256_file(report_file),
                "thread_b_report_relpath": b_report_relpath,
            },
        )
        a0_sequence = int(seq_by_source.get("A0", 0))
        last_sequence = 0
        if state.canonical_ledger:
            last_sequence = int(state.canonical_ledger[-1].get("sequence", 0))
        if a0_sequence <= last_sequence:
            raise ValueError(f"state_transition_sequence_regression:{a0_sequence}:{last_sequence}")
        state.canonical_ledger.append(
            {
                "step": global_step,
                "sequence": a0_sequence,
                "previous_state_hash": state_hash_before,
                "export_block_hash": export_block_hash,
                "snapshot_hash": snapshot_hash,
                "compiler_version": compiler_version,
                "state_transition_digest": state_transition_digest,
            }
        )

        plan = pipeline.dispatcher.build_campaign_plan(state)
        tasks = list(plan.tasks)
        # Deterministic budget enforcement: cap SIM execution per step to the
        # (repaired) strategy budget. This prevents evidence_pending fanout from
        # exploding run surfaces during mass-batch phases.
        try:
            max_sims = int((compiled.get("repaired_strategy", {}) or {}).get("budget", {}).get("max_sims", 0) or 0)
        except Exception:
            max_sims = 0
        if max_sims > 0 and len(tasks) > max_sims:
            tasks = tasks[:max_sims]
        campaign_program_id, replay_source = _campaign_strategy_meta(compiled)
        if campaign_program_id:
            campaign_program_ids.add(campaign_program_id)
        campaign_stage_ids_seen.update(stage_id for stage_id in plan.stages_seen if stage_id)
        campaign_suite_modes_seen.update(mode for mode in plan.suite_modes_seen if mode)
        blocked_stage_ids_seen.update(stage_id for stage_id in plan.blocked_stage_ids if stage_id)
        blocked_suite_modes_seen.update(mode for mode in plan.blocked_suite_modes if mode)
        sim_outputs = []
        for sim_index, task in enumerate(tasks, start=1):
            evidence_text = pipeline.sim_engine.run_task(state, task)
            evidence_path = ""
            if retain_sim_text:
                evidence_file = run_dir / "sim" / f"sim_evidence_{global_step:04d}_{sim_index:03d}.txt"
                evidence_file.write_text(evidence_text, encoding="utf-8")
                evidence_path = str(evidence_file)
            sim_zip = run_dir / "zip_packets" / f"{_next_seq('SIM'):06d}_SIM_TO_A0_SIM_RESULT_ZIP.zip"
            write_zip_protocol_v2(
                out_path=sim_zip,
                header={
                    "zip_type": "SIM_TO_A0_SIM_RESULT_ZIP",
                    "direction": "BACKWARD",
                    "source_layer": "SIM",
                    "target_layer": "A0",
                    "run_id": run_id,
                    "sequence": seq_by_source["SIM"],
                    "created_utc": _FIXED_CREATED_UTC,
                    "compiler_version": "",
                },
                payload_text={"SIM_EVIDENCE.txt": evidence_text},
            )
            _validate_ok(sim_zip)
            ingest = pipeline.kernel.ingest_sim_evidence_pack(
                evidence_text,
                state,
                batch_id=f"STEP_{global_step:04d}_SIM_{sim_index:03d}",
            )
            sim_outputs.append(
                {
                    "sim_id": task.sim_id,
                    "stage_id": task.stage_id,
                    "stage_suite_kind": task.stage_suite_kind,
                    "zip_relpath": _relpath(run_dir, sim_zip),
                    "ingest_status": str(ingest.get("status", "")),
                    "satisfied_count": len(ingest.get("satisfied", []) or []),
                    "evidence_relpath": _relpath(run_dir, evidence_path) if evidence_path else "",
                }
            )
        executed_stage_counts: dict[str, int] = {}
        executed_suite_counts: dict[str, int] = {}
        for task in tasks:
            if task.stage_id:
                executed_stage_counts[task.stage_id] = int(executed_stage_counts.get(task.stage_id, 0)) + 1
            if task.stage_suite_kind:
                executed_suite_counts[task.stage_suite_kind] = int(executed_suite_counts.get(task.stage_suite_kind, 0)) + 1
        failure_isolation_total += int(executed_suite_counts.get("failure_isolation", 0))
        graveyard_rescue_total += int(executed_suite_counts.get("graveyard_rescue", 0))
        replay_from_tape_total += int(executed_suite_counts.get("replay_from_tape", 0))

        state_hash_after = state.hash()
        repeated_noop = repeated_noop + 1 if state_hash_after == state_hash_before else 0
        final_coverage_report = pipeline.sim_engine.coverage_report(
            state,
            graveyard_by_target_class=_graveyard_by_target_class(state),
        )
        sim_status_counts: dict[str, int] = {}
        satisfied_total = 0
        for row in sim_outputs:
            status = str(row.get("ingest_status", "")).strip() or "UNKNOWN"
            sim_status_counts[status] = int(sim_status_counts.get(status, 0)) + 1
            satisfied_total += int(row.get("satisfied_count", 0) or 0)
        sim_event_payload: dict = {
            "count": len(sim_outputs),
            "status_counts": sim_status_counts,
            "satisfied_total": satisfied_total,
            "campaign_program_id": campaign_program_id,
            "replay_source": replay_source,
            "stages_seen": list(plan.stages_seen),
            "suite_modes_seen": list(plan.suite_modes_seen),
            "blocked_stage_ids": list(plan.blocked_stage_ids),
            "blocked_suite_modes": list(plan.blocked_suite_modes),
            "planned_stage_task_counts": dict(plan.stage_task_counts),
            "planned_suite_mode_task_counts": dict(plan.suite_mode_task_counts),
            "executed_stage_task_counts": executed_stage_counts,
            "executed_suite_mode_task_counts": executed_suite_counts,
            "failure_isolation_count": int(executed_suite_counts.get("failure_isolation", 0)),
            "graveyard_rescue_count": int(executed_suite_counts.get("graveyard_rescue", 0)),
            "replay_from_tape_count": int(executed_suite_counts.get("replay_from_tape", 0)),
        }
        if retain_sim_text or retain_diagnostics:
            sim_event_payload["items"] = sim_outputs
        if retain_diagnostics:
            _write_json(
                run_dir / "reports" / f"sim_campaign_{global_step:04d}.json",
                {
                    "schema": "SIM_CAMPAIGN_REPORT_v1",
                    "run_id": run_id,
                    "step": global_step,
                    "campaign_program_id": campaign_program_id,
                    "replay_source": replay_source,
                    "planned_stage_task_counts": dict(plan.stage_task_counts),
                    "planned_suite_mode_task_counts": dict(plan.suite_mode_task_counts),
                    "blocked_stage_ids": list(plan.blocked_stage_ids),
                    "blocked_suite_modes": list(plan.blocked_suite_modes),
                    "executed_stage_task_counts": executed_stage_counts,
                    "executed_suite_mode_task_counts": executed_suite_counts,
                },
            )
        _append_jsonl(
            events_path,
            {
                "step": global_step,
                "state_hash_before": state_hash_before,
                "state_hash_after": state_hash_after,
                "strategy_packet": strategy_packet,
                "export_packet": export_packet,
                "strategy_digest": strategy_digest,
                "export_content_digest": export_content_digest,
                "export_structural_digest": export_structural_digest,
                "accepted": accepted,
                "parked": parked,
                "rejected": rejected,
                "reject_tags": reject_tags,
                "state_transition_digest": state_transition_digest,
                "sim": sim_event_payload,
                "master_sim_status": final_coverage_report.get("master_sim_status", "NOT_READY"),
                "unresolved_promotion_blocker_count": len(final_coverage_report.get("unresolved_promotion_blockers", [])),
                "repeated_noop": repeated_noop,
                "repeated_schema_fail": repeated_schema_fail,
            },
        )
        _persist_resume_state(
            run_id=run_id,
            state=state,
            seq_by_source=seq_by_source,
            run_state_path=run_state_path,
            run_sequence_state_path=run_sequence_state_path,
            current_state_path=current_state_path,
            sequence_state_path=sequence_state_path,
        )

        if repeated_noop >= 25:
            stop_reason = "REPEATED_NOOP"
            break
        if repeated_schema_fail >= 5:
            stop_reason = "REPEATED_SCHEMA_FAIL"
            break

    _persist_resume_state(
        run_id=run_id,
        state=state,
        seq_by_source=seq_by_source,
        run_state_path=run_state_path,
        run_sequence_state_path=run_sequence_state_path,
        current_state_path=current_state_path,
        sequence_state_path=sequence_state_path,
    )
    state_hash = state.hash()
    state_file_hash = _sha256_file(run_state_path)
    (run_dir / "state.json.sha256").write_text(f"{state_file_hash}  state.json\n", encoding="utf-8")
    (run_dir / "state.heavy.json.sha256").write_text(
        f"{_sha256_file(run_state_path.with_name('state.heavy.json'))}  state.heavy.json\n",
        encoding="utf-8",
    )
    _write_json(
        run_dir / "summary.json",
        {
            "run_id": run_id,
            "steps_requested": steps,
            "steps_completed": step_offset + steps_completed_local,
            "steps_completed_local": steps_completed_local,
            "stop_reason": stop_reason,
            "accepted_total": accepted_total,
            "parked_total": parked_total,
            "rejected_total": rejected_total,
            "final_state_hash": state_hash,
            "state_file_sha256": state_file_hash,
            "a1_source": a1_source,
            "a1_model": "",
            "needs_real_llm": stop_reason == "A2_OPERATOR_SET_EXHAUSTED",
            "escalation_reasons": escalation_reasons,
            "unique_strategy_digest_count": len(strategy_digests),
            "unique_export_content_digest_count": len(export_content_digests),
            "unique_export_structural_digest_count": len(export_structural_digests),
            "id_churn_signal": (
                len(export_content_digests) > len(export_structural_digests)
                and len(export_structural_digests) <= 2
                and len(export_content_digests) >= 5
            ),
            "sim_registry_count": len(state.sim_registry),
            "campaign_program_ids": sorted(campaign_program_ids),
            "campaign_stage_ids_seen": sorted(campaign_stage_ids_seen),
            "campaign_suite_modes_seen": sorted(campaign_suite_modes_seen),
            "blocked_stage_ids_seen": sorted(blocked_stage_ids_seen),
            "blocked_suite_modes_seen": sorted(blocked_suite_modes_seen),
            "failure_isolation_total": failure_isolation_total,
            "graveyard_rescue_total": graveyard_rescue_total,
            "replay_from_tape_total": replay_from_tape_total,
            "master_sim_status": final_coverage_report.get("master_sim_status", "NOT_READY"),
            "unresolved_promotion_blocker_count": len(final_coverage_report.get("unresolved_promotion_blockers", [])),
            "promotion_counts_by_tier": final_coverage_report.get("promotion_counts_by_tier", {}),
        },
    )
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    if retain_diagnostics:
        _write_soak_report(run_dir, summary, events_path)
    _update_runs_registry(runs_root, summary)
    return run_dir, state_hash


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default="a1_strategies/sample_strategy.json")
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--run-id", default=None)
    parser.add_argument(
        "--runs-root",
        default=None,
        help="Override runs root dir. Default is system_v3/runs. Useful for sandbox test runs under work/.",
    )
    parser.add_argument("--a1-source", choices=["replay", "packet", "autowiggle"], default="packet")
    # AUTOWIGGLE knobs (only used when --a1-source autowiggle)
    parser.add_argument("--autowiggle-max-items", type=int, default=140)
    parser.add_argument("--autowiggle-max-sims", type=int, default=110)
    parser.add_argument("--autowiggle-target-count", type=int, default=90)
    parser.add_argument("--autowiggle-alternative-count", type=int, default=50)
    parser.add_argument("--autowiggle-rescue-fraction", type=float, default=0.50)
    parser.add_argument("--a1-model", default="disabled", help="Deprecated. Ollama source has been removed.")
    parser.add_argument("--a1-timeout-sec", type=int, default=60)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument(
        "--retain-diagnostics",
        action="store_true",
        help="Write duplicate human-readable artifacts (reports/, outbox/, a1_strategies/, soak_report.md).",
    )
    parser.add_argument(
        "--retain-snapshots",
        action="store_true",
        help="Also write snapshot_*.txt to runs/<RUN_ID>/snapshots (duplicates B snapshot ZIP payload).",
    )
    parser.add_argument(
        "--retain-sim-text",
        action="store_true",
        help="Also write sim_evidence_*.txt to runs/<RUN_ID>/sim (duplicates SIM ZIP payload).",
    )
    args = parser.parse_args()

    autowiggle_config = None
    if args.a1_source == "autowiggle":
        autowiggle_config = AutowiggleConfig(
            max_items=int(args.autowiggle_max_items),
            max_sims=int(args.autowiggle_max_sims),
            target_count=int(args.autowiggle_target_count),
            alternative_count=int(args.autowiggle_alternative_count),
            graveyard_rescue_fraction=float(args.autowiggle_rescue_fraction),
        )

    run_id = args.run_id or _now_run_id()
    run_dir, state_hash = run_loop(
        strategy_path=Path(args.strategy),
        steps=args.steps,
        run_id=run_id,
        a1_source=args.a1_source,
        a1_model=args.a1_model,
        a1_timeout_sec=args.a1_timeout_sec,
        autowiggle_config=autowiggle_config,
        clean=args.clean,
        retain_diagnostics=bool(args.retain_diagnostics),
        retain_snapshots=bool(args.retain_snapshots),
        retain_sim_text=bool(args.retain_sim_text),
        runs_root_override=args.runs_root,
    )
    print(str(run_dir))
    print(state_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
