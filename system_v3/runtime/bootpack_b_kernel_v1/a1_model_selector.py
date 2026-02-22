import json
from pathlib import Path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_latest_benchmark_summary(runs_root: Path) -> Path | None:
    candidates = sorted(runs_root.glob("A1_MODEL_BENCH_*/benchmark_summary.json"))
    if not candidates:
        return None
    return candidates[-1]


def select_best_model(summary_path: Path) -> str:
    data = _read_json(summary_path)
    rows = data.get("results", [])
    return _select_best_model_from_rows(rows)


def _select_best_model_from_rows(rows: list[dict]) -> str:
    if not isinstance(rows, list) or not rows:
        return ""
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            bool(row.get("needs_real_llm", True)),
            bool(row.get("id_churn_signal", True)),
            int(row.get("rejected_total", 10**9)),
            int(row.get("parked_total", 10**9)),
            -int(row.get("accepted_total", 0)),
            -int(row.get("unique_export_structural_digest_count", 0)),
            -int(row.get("unique_strategy_digest_count", 0)),
            str(row.get("model", "")),
        ),
    )
    best = sorted_rows[0]
    if best.get("needs_real_llm", True):
        return ""
    return str(best.get("model", ""))


def select_best_model_across_runs(runs_root: Path) -> tuple[str, str]:
    summaries = sorted(runs_root.glob("A1_MODEL_BENCH_*/benchmark_summary.json"))
    all_rows: list[dict] = []
    for summary in summaries:
        data = _read_json(summary)
        rows = data.get("results", [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            item = dict(row)
            item["_summary_path"] = str(summary)
            all_rows.append(item)
    if not all_rows:
        return "", ""

    model = _select_best_model_from_rows(all_rows)
    if not model:
        return "", ""
    ranked = sorted(
        [row for row in all_rows if str(row.get("model", "")) == model and not bool(row.get("needs_real_llm", True))],
        key=lambda row: (
            bool(row.get("id_churn_signal", True)),
            int(row.get("rejected_total", 10**9)),
            int(row.get("parked_total", 10**9)),
            -int(row.get("accepted_total", 0)),
            -int(row.get("unique_export_structural_digest_count", 0)),
            -int(row.get("unique_strategy_digest_count", 0)),
            str(row.get("_summary_path", "")),
        ),
    )
    source = str(ranked[0].get("_summary_path", "")) if ranked else ""
    return model, source
