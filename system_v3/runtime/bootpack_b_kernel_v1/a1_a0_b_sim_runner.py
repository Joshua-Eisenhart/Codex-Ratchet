import argparse
import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path
import zipfile

from a0_compiler import compile_export_block
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
    lines.append("## last_20_events")
    if not last_rows:
        lines.append("- NONE")
    else:
        for row in last_rows:
            lines.append(f"- {json.dumps(row, sort_keys=True, separators=(',', ':'))}")
    (run_dir / "soak_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    for item_id, row in state.park_set.items():
        if str(row.get("class", "")) != "SPEC_HYP":
            continue
        meta = state.spec_meta.get(item_id, {})
        if meta.get("kind") != "SIM_SPEC":
            continue
        target_class = str(meta.get("target_class", "")).strip()
        if not target_class:
            continue
        counts[target_class] = counts.get(target_class, 0) + 1
    for item_id, row in state.survivor_ledger.items():
        if str(row.get("class", "")) != "SPEC_HYP":
            continue
        if str(row.get("status", "")) != "KILLED":
            continue
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
    current_state_path: Path,
    sequence_state_path: Path,
) -> tuple[KernelState, dict[tuple[str, str], int], dict[str, int]]:
    state = KernelState()
    seq_state: dict[tuple[str, str], int] = {}
    seq_by_source: dict[str, int] = {}

    if current_state_path.exists():
        payload = json.loads(current_state_path.read_text(encoding="utf-8"))
        state = KernelState.from_dict(payload)

    if sequence_state_path.exists():
        payload = json.loads(sequence_state_path.read_text(encoding="utf-8"))
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

    return state, seq_state, seq_by_source


def _persist_resume_state(
    *,
    run_id: str,
    state: KernelState,
    seq_by_source: dict[str, int],
    current_state_path: Path,
    sequence_state_path: Path,
) -> None:
    current_state_path.parent.mkdir(parents=True, exist_ok=True)
    current_state_path.write_text(state.to_json(), encoding="utf-8")
    _write_json(
        sequence_state_path,
        {
            "run_id": run_id,
            "seq_by_source": {key: int(seq_by_source.get(key, 0)) for key in sorted(_SEQ_SOURCES)},
        },
    )


def run_loop(
    strategy_path: Path,
    steps: int,
    run_id: str,
    a1_source: str,
    a1_model: str,
    a1_timeout_sec: int,
    clean: bool = False,
) -> tuple[Path, str]:
    _assert_no_legacy_runtime_modules_loaded()
    base = Path(__file__).resolve().parent
    run_dir = base / "runs" / run_id
    current_state_path = base / "current_state" / "state.json"
    sequence_state_path = base / "current_state" / "sequence_state.json"
    if clean and run_dir.exists():
        shutil.rmtree(run_dir)
    if clean:
        if current_state_path.exists():
            current_state_path.unlink()
        if sequence_state_path.exists():
            sequence_state_path.unlink()
    (run_dir / "outbox").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    (run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
    (run_dir / "sim").mkdir(parents=True, exist_ok=True)
    (run_dir / "snapshots").mkdir(parents=True, exist_ok=True)
    (run_dir / "a1_strategies").mkdir(parents=True, exist_ok=True)
    (run_dir / "a1_inbox").mkdir(parents=True, exist_ok=True)

    events_path = run_dir / "events.jsonl"
    if clean:
        state = KernelState()
        seq_state: dict[tuple[str, str], int] = {}
        seq_by_source: dict[str, int] = {}
    else:
        state, seq_state, seq_by_source = _load_resume_state(
            run_id=run_id,
            current_state_path=current_state_path,
            sequence_state_path=sequence_state_path,
        )
    pipeline = A0BSimPipeline()
    a1 = A1Bridge(source=a1_source, model=a1_model, timeout_sec=a1_timeout_sec, inbox_dir=run_dir / "a1_inbox")

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
    final_coverage_report = {}
    steps_completed = 0

    for step in range(1, steps + 1):
        steps_completed = step
        state_hash_before = state.hash()
        try:
            strategy_result = a1.next_strategy(strategy_path=strategy_path, step=step, state_hash=state_hash_before, last_tags=last_tags)
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
                            "step": step,
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
                        "step": step,
                        "event": "a1_strategy_request_emitted",
                        "source": "ZIP_PROTOCOL_v2",
                        "state_hash": state_hash_before,
                        "last_reject_tags": sorted(set(last_tags)),
                        "a0_to_a1_save_zip": str(out_zip),
                    },
                )
                stop_reason = "A1_NEEDS_EXTERNAL_STRATEGY"
                break
            a1_generation_fail_count += 1
            _append_jsonl(
                events_path,
                {
                    "step": step,
                    "event": "a1_generation_fail",
                    "source": a1_source,
                    "model": a1_model if a1_source == "ollama" else "",
                    "error": str(exc)[:1200],
                    "a1_generation_fail_count": a1_generation_fail_count,
                },
            )
            # Escalation is strictly reserved for operator-set exhaustion.
            if a1_generation_fail_count >= 3:
                stop_reason = "A1_GENERATION_FAIL_LIMIT"
                break
            continue

        strategy_file = run_dir / "a1_strategies" / f"a1_strategy_{step:04d}.json"
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
        strategy_packet = {"path": str(a1_zip)}

        compiled = compile_export_block(
            state=state,
            strategy=strategy,
            canonical_state_hash=state_hash_before,
            step=step,
            prior_tags=last_tags,
        )
        export_text = compiled["export_text"]
        export_file = run_dir / "outbox" / f"export_block_{step:04d}.txt"
        export_file.write_text(export_text, encoding="utf-8")
        export_content_digest = _content_digest(export_text)
        export_structural_digest = _structural_digest(export_text)
        export_content_digests.add(export_content_digest)
        export_structural_digests.add(export_structural_digest)
        compile_report_file = run_dir / "reports" / f"a0_compile_{step:04d}.json"
        _write_json(compile_report_file, compiled["report"])
        exhausted_tags = list(compiled["report"].get("operator_exhausted_tags", []))
        if exhausted_tags:
            stop_reason = "A2_OPERATOR_SET_EXHAUSTED"
            escalation_reasons = [f"OPERATOR_SET_EXHAUSTED:{tag}" for tag in sorted(set(exhausted_tags))]
            recommended_model, recommended_source = select_best_model_across_runs(run_dir.parent)
            request_path = run_dir / "reports" / "a2_escalation_request.json"
            _write_json(
                request_path,
                {
                    "run_id": run_id,
                    "step": step,
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
        export_packet = {"path": str(a0_export_zip)}

        eval_result = pipeline.handle_message(export_text, state, batch_id=f"STEP_{step:04d}")
        report_file = run_dir / "reports" / f"b_report_{step:04d}.txt"
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
        snapshot_path = run_dir / "snapshots" / f"snapshot_{step:04d}.txt"
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

        tasks = pipeline.dispatcher.plan_tasks(state)
        sim_outputs = []
        for sim_index, task in enumerate(tasks, start=1):
            evidence_text = pipeline.sim_engine.run_task(state, task)
            evidence_path = run_dir / "sim" / f"sim_evidence_{step:04d}_{sim_index:03d}.txt"
            evidence_path.write_text(evidence_text, encoding="utf-8")
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
            ingest = pipeline.kernel.ingest_sim_evidence_pack(evidence_text, state, batch_id=f"STEP_{step:04d}_SIM_{sim_index:03d}")
            sim_outputs.append({"path": str(evidence_path), "sim_id": task.sim_id, "ingest": ingest, "zip": str(sim_zip)})

        state_hash_after = state.hash()
        repeated_noop = repeated_noop + 1 if state_hash_after == state_hash_before else 0
        final_coverage_report = pipeline.sim_engine.coverage_report(
            state,
            graveyard_by_target_class=_graveyard_by_target_class(state),
        )
        _append_jsonl(
            events_path,
            {
                "step": step,
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
                "sim_outputs": sim_outputs,
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
            current_state_path=current_state_path,
            sequence_state_path=sequence_state_path,
        )

        if repeated_noop >= 25:
            stop_reason = "REPEATED_NOOP"
            break
        if repeated_schema_fail >= 5:
            stop_reason = "REPEATED_SCHEMA_FAIL"
            break

    state_path = run_dir / "state.json"
    state_path.write_text(state.to_json(), encoding="utf-8")
    _persist_resume_state(
        run_id=run_id,
        state=state,
        seq_by_source=seq_by_source,
        current_state_path=current_state_path,
        sequence_state_path=sequence_state_path,
    )
    state_hash = _sha256_file(state_path)
    (run_dir / "state.json.sha256").write_text(f"{state_hash}  state.json\n", encoding="utf-8")
    _write_json(
        run_dir / "summary.json",
        {
            "run_id": run_id,
            "steps_requested": steps,
            "steps_completed": steps_completed,
            "stop_reason": stop_reason,
            "accepted_total": accepted_total,
            "parked_total": parked_total,
            "rejected_total": rejected_total,
            "final_state_hash": state_hash,
            "a1_source": a1_source,
            "a1_model": a1_model if a1_source == "ollama" else "",
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
            "master_sim_status": final_coverage_report.get("master_sim_status", "NOT_READY"),
            "unresolved_promotion_blocker_count": len(final_coverage_report.get("unresolved_promotion_blockers", [])),
            "promotion_counts_by_tier": final_coverage_report.get("promotion_counts_by_tier", {}),
        },
    )
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    _write_soak_report(run_dir, summary, events_path)
    return run_dir, state_hash


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default="a1_strategies/sample_strategy.json")
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--a1-source", choices=["replay", "ollama", "packet"], default="packet")
    parser.add_argument("--a1-model", default="phi4-mini")
    parser.add_argument("--a1-timeout-sec", type=int, default=60)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    run_id = args.run_id or _now_run_id()
    run_dir, state_hash = run_loop(
        strategy_path=Path(args.strategy),
        steps=args.steps,
        run_id=run_id,
        a1_source=args.a1_source,
        a1_model=args.a1_model,
        a1_timeout_sec=args.a1_timeout_sec,
        clean=args.clean,
    )
    print(str(run_dir))
    print(state_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
