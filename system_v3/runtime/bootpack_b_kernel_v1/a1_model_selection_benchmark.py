import argparse
import json
import time
from pathlib import Path

from a1_a0_b_sim_runner import run_loop


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _now_id() -> str:
    return time.strftime("A1_MODEL_BENCH__%Y%m%d_%H%M%SZ", time.gmtime())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default="a1_strategies/sample_strategy.json")
    parser.add_argument("--models", required=True, help="comma-separated ollama models")
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--timeout-sec", type=int, default=90)
    parser.add_argument("--bench-id", default=None)
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    bench_id = args.bench_id or _now_id()
    bench_dir = base / "runs" / bench_id
    bench_dir.mkdir(parents=True, exist_ok=True)

    models = [item.strip() for item in args.models.split(",") if item.strip()]
    rows = []
    for index, model in enumerate(models, start=1):
        run_id = f"{bench_id}__{index:02d}__{model.replace(':', '_').replace('/', '_')}"
        run_dir, final_hash = run_loop(
            strategy_path=Path(args.strategy),
            steps=args.steps,
            run_id=run_id,
            a1_source="ollama",
            a1_model=model,
            a1_timeout_sec=args.timeout_sec,
            clean=True,
        )
        summary = _read_json(run_dir / "summary.json")
        rows.append(
            {
                "model": model,
                "run_id": run_id,
                "run_dir": str(run_dir),
                "final_state_hash": final_hash,
                "stop_reason": summary.get("stop_reason", ""),
                "needs_real_llm": bool(summary.get("needs_real_llm", False)),
                "accepted_total": int(summary.get("accepted_total", 0)),
                "parked_total": int(summary.get("parked_total", 0)),
                "rejected_total": int(summary.get("rejected_total", 0)),
                "unique_strategy_digest_count": int(summary.get("unique_strategy_digest_count", 0)),
                "unique_export_content_digest_count": int(summary.get("unique_export_content_digest_count", 0)),
                "unique_export_structural_digest_count": int(summary.get("unique_export_structural_digest_count", 0)),
                "id_churn_signal": bool(summary.get("id_churn_signal", False)),
                "escalation_reasons": list(summary.get("escalation_reasons", [])),
            }
        )

    rows.sort(key=lambda row: (row["needs_real_llm"], row["id_churn_signal"], row["rejected_total"], -row["accepted_total"], row["model"]))
    result = {"bench_id": bench_id, "strategy": args.strategy, "steps": args.steps, "timeout_sec": args.timeout_sec, "results": rows}
    _write_json(bench_dir / "benchmark_summary.json", result)
    print(str(bench_dir / "benchmark_summary.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

