import argparse
import hashlib
import json
import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

from a1_strategy import build_default_strategy, parse_strategy
from a0_compiler import compile_strategy
from b_kernel import BKernel
from state import KernelState
from sim_runner import run_pending

LOG_SHARD_BYTES = 200_000
OUTBOX_SHARD_BYTES = 200_000
GRAVEYARD_CAP = 1000
PARK_CAP = 1000
SNAPSHOT_PERIOD = 10
NOOP_LIMIT = 5
SCHEMA_FAIL_LIMIT = 3


class ShardedJsonl:
    def __init__(self, root: Path, stem: str, shard_bytes: int):
        self.root = root
        self.stem = stem
        self.shard_bytes = shard_bytes
        self.index = 0
        self.path = self._path()

    def _path(self) -> Path:
        return self.root / f"{self.stem}.{self.index:03d}.jsonl"

    def write(self, obj: dict):
        self.root.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"
        if self.path.exists() and self.path.stat().st_size + len(payload.encode("utf-8")) > self.shard_bytes:
            self.index += 1
            self.path = self._path()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(payload)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--max-cycles", type=int, default=200)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]
    run_dir = repo_root / "system_v3" / "runs" / args.run_id
    outbox_dir = run_dir / "outbox"
    logs_dir = run_dir / "logs"
    snapshots_dir = run_dir / "snapshots"
    reports_dir = run_dir / "reports"

    log = ShardedJsonl(logs_dir, "events", LOG_SHARD_BYTES)
    outbox_dir.mkdir(parents=True, exist_ok=True)

    kernel = BKernel()
    state = KernelState()

    last20 = []
    accept_count = 0
    reject_count = 0
    park_count = 0
    noop_streak = 0
    schema_fail_streak = 0

    last_state_hash = None

    for cycle in range(1, args.max_cycles + 1):
        # A1
        strategy_text = build_default_strategy()
        strategy = parse_strategy(strategy_text)

        # A0
        export_block = compile_strategy(strategy, export_id=f"BIND_MS_A_FULL16X4_{cycle:04d}")
        outbox_path = outbox_dir / f"export_block_{cycle:04d}.txt"
        _write_text(outbox_path, export_block)

        # B
        result = kernel.evaluate_export_block(export_block, state)
        accepts = len(result["accepted"])
        rejects = len(result["rejected"])

        accept_count += accepts
        reject_count += rejects

        for r in result["rejected"]:
            entry = {"id": r.get("id"), "reason": r.get("reason")}
            state.graveyard.append(entry)
            if len(state.graveyard) > GRAVEYARD_CAP:
                state.graveyard = state.graveyard[-GRAVEYARD_CAP:]
            if r.get("reason") in {"PROBE_SCHEMA_FAIL", "SPEC_KIND_UNSUPPORTED"} or str(r.get("reason", "")).startswith("PARSE_FAIL"):
                schema_fail_streak += 1
            else:
                schema_fail_streak = 0

        # SIM
        evidence_blocks = run_pending(state)
        for ev in evidence_blocks:
            kernel.ingest_sim_evidence(ev, state)

        # Log event
        event = {
            "cycle": cycle,
            "accepted": accepts,
            "rejected": rejects,
            "pending_evidence": len(state.evidence_pending),
        }
        log.write(event)
        last20.append(event)
        if len(last20) > 20:
            last20 = last20[-20:]

        # Snapshot
        if cycle % SNAPSHOT_PERIOD == 0:
            snap_path = snapshots_dir / f"state_{cycle:04d}.json"
            _write_text(snap_path, state.to_json())

        # No-op detection
        state_hash = state.hash()
        if last_state_hash == state_hash:
            noop_streak += 1
        else:
            noop_streak = 0
        last_state_hash = state_hash

        if noop_streak >= NOOP_LIMIT:
            break
        if schema_fail_streak >= SCHEMA_FAIL_LIMIT:
            break

    # Final save
    state_path = run_dir / "state.json"
    _write_text(state_path, state.to_json())
    _write_text(run_dir / "state.json.sha256", f"{_sha256_file(state_path)}  state.json\n")

    # Report
    top_fail = {}
    for g in state.graveyard:
        top_fail[g.get("reason")] = top_fail.get(g.get("reason"), 0) + 1
    top_fail_sorted = sorted(top_fail.items(), key=lambda x: (-x[1], x[0]))[:10]

    report_lines = []
    report_lines.append("# SOAK_REPORT")
    report_lines.append("")
    report_lines.append(f"cycle_count: {cycle}")
    report_lines.append(f"accept_count: {accept_count}")
    report_lines.append(f"park_count: {park_count}")
    report_lines.append(f"reject_count: {reject_count}")
    report_lines.append("")
    report_lines.append("top_failure_tags:")
    for tag, cnt in top_fail_sorted:
        report_lines.append(f"- {tag}: {cnt}")
    if not top_fail_sorted:
        report_lines.append("- NONE")
    report_lines.append("")
    report_lines.append("last_20_events:")
    for ev in last20:
        report_lines.append("- " + json.dumps(ev, sort_keys=True, separators=(",", ":")))

    report_path = reports_dir / "soak_report.md"
    _write_text(report_path, "\n".join(report_lines) + "\n")
    print(str(report_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
