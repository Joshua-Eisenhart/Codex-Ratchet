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


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _log_writer(run_dir: Path):
    seq = {"n": 0}
    log_path = run_dir / "events.jsonl"
    def _log(event: dict):
        seq["n"] += 1
        payload = {"seq": seq["n"], **event}
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    return _log


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--strategy", default=None)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]
    run_dir = repo_root / "system_v3" / "runs" / args.run_id
    outbox = run_dir / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)

    log_fn = _log_writer(run_dir)

    # A1
    if args.strategy:
        strategy_text = Path(args.strategy).read_text(encoding="utf-8")
    else:
        strategy_text = build_default_strategy()
    (run_dir / "a1_strategy_0001.txt").write_text(strategy_text, encoding="utf-8")
    strategy = parse_strategy(strategy_text)
    log_fn({"event": "a1_strategy_loaded", "version": strategy.version})

    # A0
    export_block = compile_strategy(strategy, export_id="BIND_MS_A_FULL16X4")
    export_path = outbox / "export_block_0001.txt"
    export_path.write_text(export_block, encoding="utf-8")
    log_fn({"event": "a0_export_written", "path": str(export_path)})

    # B
    state = KernelState()
    kernel = BKernel()
    kernel.evaluate_export_block(export_block, state, log_fn=log_fn)

    # SIM
    evidence_blocks = run_pending(state)
    for idx, ev in enumerate(evidence_blocks, start=1):
        ev_path = run_dir / f"sim_evidence_{idx:04d}.txt"
        ev_path.write_text(ev, encoding="utf-8")
        kernel.ingest_sim_evidence(ev, state, log_fn=log_fn)

    # SAVE
    state_path = run_dir / "state.json"
    state_path.write_text(state.to_json(), encoding="utf-8")
    state_hash = _sha256_file(state_path)
    (run_dir / "state.json.sha256").write_text(f"{state_hash}  state.json\n", encoding="utf-8")
    log_fn({"event": "state_saved", "state_hash": state_hash})

    print(state_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
