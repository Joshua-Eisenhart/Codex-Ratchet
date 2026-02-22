import argparse
import hashlib
import json
import time
import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

from a0_compiler import compile_export_block
from a1_adapter import generate_strategy_with_ollama, load_strategy_artifact
from b_kernel import BKernel
from sim_runner import run_pending
from state import KernelState

LOG_SHARD_BYTES = 2_000_000
SNAPSHOT_PERIOD = 25
COMPILER_VERSION = "A0_COMPILER_v1"


class ShardedJsonlWriter:
    def __init__(self, root: Path, stem: str, max_bytes: int):
        self.root = root
        self.stem = stem
        self.max_bytes = max_bytes
        self.index = 0
        self.path = self._path()
        self.seq = 0

    def _path(self) -> Path:
        return self.root / f"{self.stem}.{self.index:03d}.jsonl"

    def write(self, payload: dict):
        self.root.mkdir(parents=True, exist_ok=True)
        self.seq += 1
        row = {"seq": self.seq, **payload}
        line = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        if self.path.exists() and self.path.stat().st_size + len(line.encode("utf-8")) > self.max_bytes:
            self.index += 1
            self.path = self._path()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _now_run_id() -> str:
    return time.strftime("RUN__%Y%m%d_%H%M%SZ__a1_a0_b_sim_v1", time.gmtime())


def _write_json(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _append_bounded(target: list[dict], entries: list[dict], cap: int):
    target.extend(entries)
    if len(target) > cap:
        del target[:-cap]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--a1-source", choices=["replay", "ollama"], default="replay")
    parser.add_argument("--a1-model", default="phi4-mini")
    parser.add_argument("--a1-timeout-sec", type=int, default=90)
    parser.add_argument("--a1-max-attempts", type=int, default=3)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--graveyard-cap", type=int, default=5000)
    parser.add_argument("--park-cap", type=int, default=5000)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    run_id = args.run_id or _now_run_id()
    run_dir = base_dir / "runs" / run_id
    outbox_dir = run_dir / "outbox"
    snapshots_dir = run_dir / "snapshots"
    sim_dir = run_dir / "sim"
    reports_dir = run_dir / "reports"
    a1_dir = run_dir / "a1_strategies"

    if args.clean and run_dir.exists():
        for p in sorted(run_dir.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                p.rmdir()

    run_dir.mkdir(parents=True, exist_ok=True)
    outbox_dir.mkdir(parents=True, exist_ok=True)
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    sim_dir.mkdir(parents=True, exist_ok=True)
    a1_dir.mkdir(parents=True, exist_ok=True)

    event_log = ShardedJsonlWriter(run_dir, "events", LOG_SHARD_BYTES)

    strategy_artifact = load_strategy_artifact(Path(args.strategy))
    base_strategy = strategy_artifact["strategy"]
    repeated_noop_limit = int(base_strategy["stop_conditions"]["repeated_noop_limit"])
    repeated_schema_fail_limit = int(base_strategy["stop_conditions"]["repeated_schema_fail_limit"])

    strategy_capture_path = a1_dir / "a1_strategy_seed.json"
    strategy_capture_path.write_bytes(Path(args.strategy).read_bytes())

    state = KernelState()
    kernel = BKernel()

    total_accept = 0
    total_reject = 0
    total_park = 0
    stop_reason = "MAX_STEPS"
    steps_completed = 0
    tag_counts: dict[str, int] = {}
    repeated_noop = 0
    repeated_schema_fail = 0
    last_reject_tags: list[str] = []
    previous_state_hash = None

    for step in range(1, args.steps + 1):
        steps_completed = step
        state_hash_before = state.hash()
        step_strategy = base_strategy
        a1_raw_path = None
        a1_attempts = []

        if args.a1_source == "ollama":
            try:
                generated = generate_strategy_with_ollama(
                    model=args.a1_model,
                    base_strategy=base_strategy,
                    step=step,
                    canonical_state_snapshot_hash=state_hash_before,
                    last_tags=last_reject_tags,
                    timeout_sec=args.a1_timeout_sec,
                    max_attempts=args.a1_max_attempts,
                )
                step_strategy = generated["strategy"]
                a1_raw_path = a1_dir / f"a1_output_raw_{step:04d}.txt"
                a1_raw_path.write_text(generated["raw_output"] + "\n", encoding="utf-8")
                a1_attempts = generated.get("attempts", [])
            except Exception as exc:
                repeated_schema_fail += 1
                event_log.write(
                    {
                        "event": "a1_generation_fail",
                        "step": step,
                        "source": args.a1_source,
                        "model": args.a1_model,
                        "reason": str(exc)[:2000],
                        "repeated_schema_fail": repeated_schema_fail,
                    }
                )
                if repeated_schema_fail >= repeated_schema_fail_limit:
                    stop_reason = "REPEATED_SCHEMA_FAIL"
                    event_log.write({"event": "stop", "reason": stop_reason, "step": step})
                    break
                continue

        a1_strategy_path = a1_dir / f"a1_strategy_{step:04d}.json"
        _write_json(a1_strategy_path, step_strategy)

        event_log.write(
            {
                "event": "a1_strategy_capture",
                "step": step,
                "source": args.a1_source,
                "model": args.a1_model if args.a1_source == "ollama" else None,
                "strategy_path": str(a1_strategy_path),
                "raw_output_path": str(a1_raw_path) if a1_raw_path else None,
                "attempts": a1_attempts,
            }
        )

        max_repair_attempts = int(step_strategy["stop_conditions"]["max_repair_attempts_per_step"])
        prior_tags: list[str] = []
        step_accept = 0
        step_reject = 0
        step_park = 0

        for attempt in range(1, max_repair_attempts + 1):
            compiled = compile_export_block(
                canonical_state_snapshot_hash=state.hash(),
                strategy=step_strategy,
                compiler_version=COMPILER_VERSION,
                prior_tags=prior_tags,
            )

            export_bytes = compiled["export_block_bytes"]
            export_text = export_bytes.decode("utf-8")
            export_path = outbox_dir / f"export_block_{step:04d}.txt"
            export_path.write_bytes(export_bytes)
            attempt_export_path = outbox_dir / f"export_block_{step:04d}_attempt_{attempt:02d}.txt"
            attempt_export_path.write_bytes(export_bytes)

            compile_report_path = reports_dir / f"compile_report_{step:04d}_{attempt:02d}.json"
            _write_json(compile_report_path, compiled["report"])

            b_result = kernel.evaluate_export_block(export_text, state)
            accepts = len(b_result["accepted"])
            rejects = len(b_result["rejected"])
            parks = len(b_result.get("parked", []))

            step_accept += accepts
            step_reject += rejects
            step_park += parks

            reject_entries = []
            reject_tags = []
            schema_fail_flag = False
            for item in b_result["rejected"]:
                tag = str(item.get("reason", "UNKNOWN"))
                reject_tags.append(tag)
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                reject_entries.append({"id": item.get("id", ""), "reason": tag, "step": step, "attempt": attempt})
                if tag.startswith("PARSE_FAIL") or tag.endswith("_SCHEMA_FAIL") or tag in {"SPEC_KIND_UNSUPPORTED", "PROBE_SCHEMA_FAIL"}:
                    schema_fail_flag = True

            _append_bounded(state.graveyard, reject_entries, args.graveyard_cap)
            parked_entries = []
            park_tags = []
            for item in b_result.get("parked", []):
                tag = str(item.get("reason", "PARKED"))
                park_tags.append(tag)
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                parked_entries.append({"id": item.get("id", ""), "reason": tag, "step": step, "attempt": attempt})
            _append_bounded(state.parked, parked_entries, args.park_cap)

            event_log.write(
                {
                    "event": "step_attempt",
                    "step": step,
                    "attempt": attempt,
                    "accepted": accepts,
                    "rejected": rejects,
                    "parked": parks,
                    "export_path": str(export_path),
                    "attempt_export_path": str(attempt_export_path),
                    "compile_report": str(compile_report_path),
                    "reject_tags": sorted(reject_tags),
                    "park_tags": sorted(park_tags),
                }
            )

            if rejects == 0 and parks == 0:
                repeated_schema_fail = 0
                prior_tags = []
                last_reject_tags = []
                break

            if schema_fail_flag:
                repeated_schema_fail += 1
            else:
                repeated_schema_fail = 0

            prior_tags = sorted(set(reject_tags))
            last_reject_tags = prior_tags

        evidence_blocks = run_pending(state)
        for idx, evidence_text in enumerate(evidence_blocks, start=1):
            evidence_path = sim_dir / f"sim_evidence_{step:04d}_{idx:02d}.txt"
            evidence_path.write_text(evidence_text, encoding="utf-8")
            evidence_result = kernel.ingest_sim_evidence(evidence_text, state)
            event_log.write(
                {
                    "event": "sim_evidence_ingest",
                    "step": step,
                    "index": idx,
                    "status": evidence_result.get("status"),
                    "satisfied": evidence_result.get("satisfied", []),
                    "path": str(evidence_path),
                }
            )

        total_accept += step_accept
        total_reject += step_reject
        total_park += step_park

        state_hash_after = state.hash()
        if previous_state_hash == state_hash_after:
            repeated_noop += 1
        else:
            repeated_noop = 0
        previous_state_hash = state_hash_after

        event_log.write(
            {
                "event": "step_summary",
                "step": step,
                "state_hash_before": state_hash_before,
                "state_hash_after": state_hash_after,
                "accepted": step_accept,
                "rejected": step_reject,
                "parked": step_park,
                "pending_evidence": len(state.evidence_pending),
                "repeated_noop": repeated_noop,
                "repeated_schema_fail": repeated_schema_fail,
            }
        )

        if step % SNAPSHOT_PERIOD == 0:
            snapshot_path = snapshots_dir / f"state_{step:04d}.json"
            snapshot_path.write_text(state.to_json(), encoding="utf-8")

        if repeated_noop >= repeated_noop_limit:
            stop_reason = "REPEATED_NOOP"
            event_log.write({"event": "stop", "reason": stop_reason, "step": step})
            break
        if repeated_schema_fail >= repeated_schema_fail_limit:
            stop_reason = "REPEATED_SCHEMA_FAIL"
            event_log.write({"event": "stop", "reason": stop_reason, "step": step})
            break
        if step >= args.steps:
            stop_reason = "MAX_STEPS"
            event_log.write({"event": "stop", "reason": stop_reason, "step": step})
            break

    state_path = run_dir / "state.json"
    state_path.write_text(state.to_json(), encoding="utf-8")
    state_hash = _sha256_file(state_path)
    (run_dir / "state.json.sha256").write_text(f"{state_hash}  state.json\n", encoding="utf-8")

    summary = {
        "run_id": run_id,
        "strategy_path": str(args.strategy),
        "strategy_sha256": strategy_artifact["sha256"],
        "a1_source": args.a1_source,
        "a1_model": args.a1_model if args.a1_source == "ollama" else None,
        "compiler_version": COMPILER_VERSION,
        "final_state_hash": state_hash,
        "accept_count": total_accept,
        "reject_count": total_reject,
        "park_count": total_park,
        "stop_reason": stop_reason,
        "steps_completed": steps_completed,
        "pending_evidence_count": len(state.evidence_pending),
        "graveyard_count": len(state.graveyard),
        "parked_count": len(state.parked),
        "top_tags": sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))[:20],
    }
    _write_json(run_dir / "summary.json", summary)
    print(state_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
