#!/usr/bin/env python3
"""
Adaptive Controller — replaces autonomous_reseed_loop.sh brain.
Real-time triage, schema repair, integration pass, and priority queueing.
Zero tokens. Local compute only.

Triage buckets (priority order):
  1. FAILING   — result JSON exists, overall_pass=False  → re-queue
  2. SCHEMA_DEBT — result JSON exists, but classification missing/wrong or stub reasons
  3. NEVER_RUN  — no result JSON
  4. STALE      — result JSON >7 days old (canonical only)
  5. PASSING    — green; feed into integration pass

Run: python3 scripts/adaptive_controller.py [--once] [--dry]
Loops indefinitely unless --once. Cycle = CYCLE_SEC (default 300s).
"""

import argparse
import atexit
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROBES = ROOT / "system_v4/probes"
RESULTS = PROBES / "a2_state/sim_results"
QUEUE = PROBES / "a2_state/queue"
LOGS = ROOT / "overnight_logs"
SKILL_LOG = ROOT / "system_v4" / "a1_state" / "skill_invocation_log.jsonl"
PY = os.environ.get(
    "CODEX_RATCHET_PYTHON",
    os.environ.get("SIM_PY", "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"),
)
STAGE_GATE_SCRIPT = ROOT / "scripts" / "stage_gate.py"
CONTROLLER_PIDFILE = pathlib.Path("/tmp/codex_ratchet_adaptive_controller.pid")
CYCLE_SEC = 300
STUB_PATTERNS = {"not relevant", "n/a", "na", "tbd", "todo", "stub",
                 "schema compliance", "boilerplate", "placeholder"}
# Meta-benchmarks/harnesses that must never enter the queue as regular sims.
QUEUE_BLACKLIST = {
    "sim_timing_benchmark",
    "autoresearch_sim_harness",
    "exploratory_process_cycle_stage_matrix_sim",
    "stage_matrix_neg_lib",
}
CORE_LADDER_FAMILIES = {
    "axis",
    "axis0",
    "bridge",
    "capability",
    "clifford",
    "cvc5",
    "geom",
    "geomstats",
    "gerbe",
    "gtower",
    "gudhi",
    "integration",
    "lego",
    "pure",
    "pyg",
    "qit",
    "rustworkx",
    "spectral",
    "toponetx",
    "torch",
    "weyl",
    "xgi",
    "z3",
}
FRAMEWORK_DOCTRINE_FAMILIES = {
    "fep",
    "holodeck",
    "iching",
    "igt",
    "leviathan",
}
LATE_INFO_KEYWORDS = (
    "bipartite",
    "entanglement",
    "mutual_information",
    "mutual_info",
    "coherent_information",
    "coherent_info",
    "concurrence",
    "negativity",
    "schmidt",
    "entropy",
    "capacity",
    "capacities",
    "carnot",
    "szilard",
    "landauer",
    "thermo",
)
BRIDGE_RUNNER_TOKENS = (
    "bridge",
    "coupling",
    "pairwise",
    "coexistence",
    "xi",
    "rho_ab",
    "phi0",
    "cut",
)
NONCLASSICAL_TOOL_TOKENS = (
    "pytorch",
    "torch",
    "pyg",
    "torch_geometric",
    "clifford",
    "z3",
    "cvc5",
    "gudhi",
    "toponetx",
    "xgi",
    "geomstats",
    "e3nn",
)

# ── helpers ──────────────────────────────────────────────────────────────────

def load_result(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _boolish(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return None


def _summary_bools_all_true(section: object) -> bool:
    bools: list[bool] = []

    def walk(value: object) -> None:
        if isinstance(value, bool):
            bools.append(value)
            return
        if isinstance(value, dict):
            for nested in value.values():
                walk(nested)
            return
        if isinstance(value, list):
            for nested in value:
                walk(nested)

    walk(section)
    return bool(bools) and all(bools)


def _nested_statuses_all_ok(section: object) -> bool:
    statuses: list[str] = []

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if key == "evidence_ledger":
                    continue
                if key == "status" and isinstance(nested, str):
                    statuses.append(nested.strip().lower())
                else:
                    walk(nested)
            return
        if isinstance(value, list):
            for nested in value:
                walk(nested)

    walk(section)
    return bool(statuses) and all(s in {"ok", "pass", "passed", "success"} for s in statuses)


def is_passing(r: dict) -> bool:
    # Only treat as failing if overall_pass is explicitly False.
    # Legacy JSONs (pre-SIM_TEMPLATE, no overall_pass field) are NOT failures —
    # they use different schemas (verdict/timestamp/axis). Treat them as "unknown".
    if "overall_pass" in r:
        return bool(r["overall_pass"])
    if "pass" in r:
        return bool(r["pass"])
    if "all_pass" in r:
        return bool(r["all_pass"])
    if "ALL_PASS" in r:
        return bool(r["ALL_PASS"])
    if isinstance(r.get("summary"), dict):
        summary = r["summary"]
        if "all_pass" in summary:
            return bool(summary["all_pass"])
        if "all_passed" in summary:
            return bool(summary["all_passed"])
        if "all_checks_pass" in summary:
            verdict = _boolish(summary["all_checks_pass"])
            if verdict is not None:
                return verdict
        if _summary_bools_all_true(summary):
            return True
    if _nested_statuses_all_ok(r):
        return True
    if r.get("result") == "PASS":
        return True
    if r.get("result") == "FAIL":
        return False
    # No known pass/fail field → legacy schema, not a real failure
    return None  # type: ignore  — caller must handle None = unknown

def is_legacy_schema(r: dict) -> bool:
    """Pre-SIM_TEMPLATE result: has no overall_pass but has old-style fields."""
    return ("overall_pass" not in r and "pass" not in r and "all_pass" not in r and
            "ALL_PASS" not in r and
            not (isinstance(r.get("summary"), dict) and
                 any(k in r["summary"] for k in ("all_pass", "all_passed"))) and
            any(k in r for k in ("timestamp", "verdict", "axis", "evidence_ledger")))

def has_stub_reasons(r: dict) -> bool:
    tm = r.get("tool_manifest", {})
    if not isinstance(tm, dict):
        return False
    for entry in tm.values():
        if not isinstance(entry, dict):
            continue
        reason = str(entry.get("reason", "")).strip().lower()
        if reason in STUB_PATTERNS or (reason and len(reason) < 25 and
                any(p in reason for p in STUB_PATTERNS)):
            return True
    return False

def result_age_days(path: pathlib.Path) -> float:
    return (time.time() - path.stat().st_mtime) / 86400


def normalize_sim_path(sim_path: str | pathlib.Path) -> str:
    path = pathlib.Path(str(sim_path))
    if not path.is_absolute():
        path = ROOT / path
    try:
        return str(path.resolve(strict=False))
    except Exception:
        return str(path)


def is_queued(sim_path: str) -> bool:
    return is_tracked(sim_path, include_blocked=False)


def is_tracked(sim_path: str, include_blocked: bool = False) -> bool:
    wanted = normalize_sim_path(sim_path)
    lanes = ["lane_A", "lane_B", "claimed"]
    if include_blocked:
        lanes.append("blocked")
    for lane in lanes:
        d = QUEUE / lane
        if not d.exists():
            continue
        for qf in d.iterdir():
            if not qf.is_file():
                continue
            try:
                queued = load_result(qf).get("sim_path", "")
                if normalize_sim_path(str(queued)) == wanted:
                    return True
            except Exception:
                pass
    return False


def active_blocked_entries() -> dict[str, list[tuple[pathlib.Path, dict]]]:
    blocked = QUEUE / "blocked"
    groups: dict[str, list[tuple[pathlib.Path, dict]]] = {}
    if not blocked.exists():
        return groups
    for bf in blocked.iterdir():
        if not bf.is_file():
            continue
        data = load_result(bf)
        sim_path = str(data.get("sim_path", ""))
        if not sim_path:
            continue
        groups.setdefault(normalize_sim_path(sim_path), []).append((bf, data))
    return groups


def queue_item_path(lane: str, sim_path: str | pathlib.Path) -> pathlib.Path:
    normalized = normalize_sim_path(sim_path)
    digest = hashlib.sha1(f"{lane}:{normalized}".encode()).hexdigest()[:16]
    return QUEUE / lane / f"{digest}.json"


def stage_gate_claim_for_sim(sim_path: pathlib.Path | str) -> str | None:
    """Return the narrowest stage-gate claim needed before queueing a sim."""
    path = pathlib.Path(sim_path)
    result_json = RESULTS / f"{path.stem}_results.json"
    result = load_result(result_json) if result_json.exists() else {}
    if (
        result.get("classification") == "tool_lego_fit_probe"
        and result.get("promotion_allowed") is False
    ):
        return None
    runner_class = runner_class_for(path)
    stage = plan_stage(path.name)
    stem = path.stem.lower()
    family = sim_family(path.name)
    if "tier_d" in stem or "boundary_flux" in stem or (
        "boundary" in stem and "admissibility" in stem
    ):
        return "tier_d"
    if family in {"axis", "axis0"} or stage == "late_axis":
        return "axis"
    if runner_class == "bridge":
        return "scientific_coupling"
    if stage == "late_info":
        return "default_late_stage"
    return None


def stage_gate_allows_sim(sim_path: pathlib.Path | str) -> bool:
    claim = stage_gate_claim_for_sim(sim_path)
    if claim is None:
        return True
    try:
        proc = subprocess.run(
            [PY, str(STAGE_GATE_SCRIPT), "--claim", claim],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
    except Exception:
        return False
    return proc.returncode == 0


def record_stage_gate_block(sim_path: pathlib.Path | str, lane: str, priority: str) -> pathlib.Path:
    (QUEUE / "blocked").mkdir(parents=True, exist_ok=True)
    normalized = normalize_sim_path(sim_path)
    claim = stage_gate_claim_for_sim(sim_path)
    bucket = plan_bucket(normalized)
    payload = {
        "blocked_at": int(time.time()),
        "blocked_reason": "stage_gate_blocked",
        "blocked_stage_claim": claim,
        "lane": lane,
        "sim_path": normalized,
        "runner_class": runner_class_for(sim_path),
        "runner_class_reason": runner_class_reason(sim_path),
        "priority": canonical_priority(priority, bucket),
        "plan_bucket": bucket,
        "plan_stage": plan_stage(normalized),
    }
    digest = hashlib.sha1(f"{lane}:{normalized}:stage_gate_blocked".encode()).hexdigest()[:16]
    target = QUEUE / "blocked" / f"{digest}.json"
    target.write_text(json.dumps(payload, sort_keys=True))
    return target


def canonicalize_queue_payload(data: dict, lane: str, normalized: str) -> dict:
    bucket = str(data.get("plan_bucket") or plan_bucket(normalized))
    sim_path = pathlib.Path(normalized)
    runner_class = str(data.get("runner_class") or runner_class_for(sim_path))
    canonical = dict(data)
    canonical["sim_path"] = normalized
    canonical["lane"] = lane
    canonical["runner_class"] = runner_class
    canonical["runner_class_reason"] = str(
        canonical.get("runner_class_reason") or runner_class_reason(sim_path)
    )
    canonical["plan_bucket"] = bucket
    canonical["plan_stage"] = plan_stage(normalized)
    canonical["priority"] = canonical_priority(canonical.get("priority"), bucket)
    canonical["enqueued_at"] = canonical.get("enqueued_at", int(time.time()))
    return canonical


def enqueue(sim_path: pathlib.Path, lane: str, priority: str = "normal") -> pathlib.Path | None:
    if not stage_gate_allows_sim(sim_path):
        record_stage_gate_block(sim_path, lane, priority)
        return None
    (QUEUE / lane).mkdir(parents=True, exist_ok=True)
    normalized = normalize_sim_path(sim_path)
    bucket = plan_bucket(normalized)
    runner_class = runner_class_for(sim_path)
    priority = canonical_priority(priority, bucket)
    payload = {
        "enqueued_at": int(time.time()),
        "lane": lane,
        "sim_path": normalized,
        "runner_class": runner_class,
        "runner_class_reason": runner_class_reason(sim_path),
        "priority": priority,
        "plan_bucket": bucket,
        "plan_stage": plan_stage(normalized),
    }
    target = queue_item_path(lane, normalized)
    try:
        fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        existing = load_result(target)
        existing["sim_path"] = normalized
        existing["lane"] = lane
        existing["runner_class"] = existing.get("runner_class") or runner_class
        existing["runner_class_reason"] = (
            existing.get("runner_class_reason") or runner_class_reason(sim_path)
        )
        existing["plan_bucket"] = bucket
        existing["plan_stage"] = plan_stage(normalized)
        existing["priority"] = canonical_priority(existing.get("priority") or priority, bucket)
        existing["enqueued_at"] = existing.get("enqueued_at", payload["enqueued_at"])
        target.write_text(json.dumps(existing, sort_keys=True))
        return target
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
    return target


def normalize_queue_filenames() -> int:
    removed = 0
    for lane in ("lane_A", "lane_B"):
        lane_dir = QUEUE / lane
        if not lane_dir.exists():
            continue
        for item in list(lane_dir.iterdir()):
            if not item.is_file():
                continue
            data = load_result(item)
            sim_path = str(data.get("sim_path", ""))
            if not sim_path:
                continue
            normalized = normalize_sim_path(sim_path)
            canonical = canonicalize_queue_payload(data, lane, normalized)
            target = queue_item_path(lane, normalized)
            if item == target:
                item.write_text(json.dumps(canonical, sort_keys=True))
                continue
            if target.exists():
                existing = canonicalize_queue_payload(load_result(target), lane, normalized)
                merged = dict(existing)
                merged.update(canonical)
                old_ts = existing.get("enqueued_at")
                new_ts = canonical.get("enqueued_at")
                if isinstance(old_ts, (int, float)) and isinstance(new_ts, (int, float)):
                    merged["enqueued_at"] = min(old_ts, new_ts)
                elif old_ts is not None:
                    merged["enqueued_at"] = old_ts
                elif new_ts is not None:
                    merged["enqueued_at"] = new_ts
                target.write_text(json.dumps(merged, sort_keys=True))
                item.unlink(missing_ok=True)
                removed += 1
                continue
            tmp = lane_dir / f".{target.name}.tmp"
            tmp.write_text(json.dumps(canonical, sort_keys=True))
            os.rename(tmp, target)
            item.unlink(missing_ok=True)
    return removed


def remove_claimed_queue_overlaps() -> int:
    claimed_dir = QUEUE / "claimed"
    if not claimed_dir.exists():
        return 0
    claimed_sims = set()
    for item in claimed_dir.glob("*.json.*"):
        data = load_result(item)
        sim_path = str(data.get("sim_path", ""))
        if sim_path:
            claimed_sims.add(normalize_sim_path(sim_path))
    if not claimed_sims:
        return 0
    removed = 0
    for lane in ("lane_A", "lane_B"):
        lane_dir = QUEUE / lane
        if not lane_dir.exists():
            continue
        for item in list(lane_dir.glob("*.json")):
            data = load_result(item)
            sim_path = str(data.get("sim_path", ""))
            if sim_path and normalize_sim_path(sim_path) in claimed_sims:
                item.unlink(missing_ok=True)
                removed += 1
    return removed


def remove_blocked_queue_overlaps() -> int:
    blocked_sims = set(active_blocked_entries())
    if not blocked_sims:
        return 0
    removed = 0
    for lane in ("lane_A", "lane_B"):
        lane_dir = QUEUE / lane
        if not lane_dir.exists():
            continue
        for item in list(lane_dir.glob("*.json")):
            data = load_result(item)
            sim_path = str(data.get("sim_path", ""))
            if sim_path and normalize_sim_path(sim_path) in blocked_sims:
                item.unlink(missing_ok=True)
                removed += 1
    return removed


def queue_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for lane in ("lane_A", "lane_B", "claimed", "blocked", "done"):
        d = QUEUE / lane
        if not d.exists():
            counts[lane] = 0
            continue
        counts[lane] = sum(1 for child in d.iterdir() if child.is_file())
    return counts


def resolved_blocked_count() -> int:
    resolved = _resolved_blocked_dir()
    if not resolved.exists():
        return 0
    return sum(1 for child in resolved.iterdir() if child.is_file())


def recent_dispatch(limit: int = 8) -> list[dict]:
    if limit <= 0 or not SKILL_LOG.exists():
        return []
    try:
        lines = SKILL_LOG.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []

    recent: list[dict] = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        recent.append({
            "timestamp": item.get("timestamp"),
            "batch_id": item.get("batch_id"),
            "phase": item.get("phase"),
            "layer_id": item.get("layer_id"),
            "graph_family": item.get("graph_family"),
            "selected_skill_id": item.get("selected_skill_id"),
            "execution_runtime": item.get("execution_runtime"),
        })
        if len(recent) >= limit:
            break
    recent.reverse()
    return recent


def sim_family(name: str) -> str:
    stem = pathlib.Path(name).stem
    if stem.startswith("sim_"):
        stem = stem[4:]
    match = re.match(r"([a-z0-9]+)", stem)
    return match.group(1) if match else "other"


def plan_bucket(name: str) -> str:
    family = sim_family(name)
    if family in CORE_LADDER_FAMILIES:
        return "core_ladder"
    if family in FRAMEWORK_DOCTRINE_FAMILIES:
        return "framework_doctrine"
    return "exploratory"


def plan_stage(name: str) -> str:
    stem = pathlib.Path(name).stem
    if stem.startswith("sim_"):
        stem = stem[4:]
    if stem.startswith("classical_baseline_"):
        return "early_core"
    family = sim_family(name)
    if family in {"axis", "axis0"}:
        return "late_axis"
    if any(token in stem for token in LATE_INFO_KEYWORDS):
        return "late_info"
    return "early_core"


def _source_classification(text: str) -> str:
    match = re.search(r'^classification\s*=\s*["\']([^"\']+)["\']', text, re.M)
    return match.group(1) if match else ""


def _source_execution_kind(text: str) -> str:
    match = re.search(r'^(?:sim_execution_kind|SIM_EXECUTION_KIND)\s*=\s*["\']([^"\']+)["\']', text, re.M)
    return match.group(1).lower() if match else ""


def _runner_class_from_execution_kind(execution_kind: str) -> str:
    if execution_kind in {"classical", "classical_baseline"}:
        return "classical"
    if "bridge" in execution_kind or execution_kind in {"semiclassical", "semiclassical_szilard"}:
        return "bridge"
    if execution_kind == "nonclassical":
        return "nonclassical"
    return ""


def runner_class_for(sim_path: pathlib.Path | str, source_text: str | None = None) -> str:
    """Return runner admission class, separate from result classification.

    `classification` remains the result/status label (`classical_baseline`,
    `canonical`, etc.). `runner_class` answers which execution path should
    admit the sim: classical, nonclassical, bridge, or unknown.
    """
    path = pathlib.Path(sim_path)
    stem = path.stem.lower()
    if stem.startswith("sim_"):
        stem = stem[4:]
    family = sim_family(path.name)
    if family in {"axis", "axis0"}:
        return "bridge"
    if any(token in stem for token in BRIDGE_RUNNER_TOKENS):
        return "bridge"

    text = source_text
    if text is None:
        try:
            text = path.read_text()
        except Exception:
            text = ""

    classification = _source_classification(text)
    execution_kind = _source_execution_kind(text)
    explicit_runner_class = _runner_class_from_execution_kind(execution_kind)
    if explicit_runner_class:
        return explicit_runner_class
    if classification == "classical_baseline" or "classical" in stem:
        return "classical"
    if classification == "canonical":
        return "nonclassical"
    if any(token in text.lower() for token in NONCLASSICAL_TOOL_TOKENS):
        return "nonclassical"
    return "unknown"


def runner_class_reason(sim_path: pathlib.Path | str, source_text: str | None = None) -> str:
    path = pathlib.Path(sim_path)
    stem = path.stem.lower()
    text = source_text
    if text is None:
        try:
            text = path.read_text()
        except Exception:
            text = ""
    if any(token in stem for token in BRIDGE_RUNNER_TOKENS):
        return "bridge_token"
    classification = _source_classification(text)
    execution_kind = _source_execution_kind(text)
    explicit_runner_class = _runner_class_from_execution_kind(execution_kind)
    if explicit_runner_class:
        return f"sim_execution_kind_{explicit_runner_class}"
    if classification == "classical_baseline":
        return "classification_classical_baseline"
    if classification == "canonical":
        return "classification_canonical"
    if any(token in text.lower() for token in NONCLASSICAL_TOOL_TOKENS):
        return "nonclassical_tool_reference"
    return "insufficient_metadata"


def default_priority_for_bucket(bucket: str) -> str:
    if bucket == "core_ladder":
        return "high"
    if bucket == "framework_doctrine":
        return "low"
    return "normal"


def canonical_priority(priority: str | None, bucket: str) -> str:
    desired = default_priority_for_bucket(bucket)
    if not priority:
        return desired
    rank = {"high": 0, "normal": 1, "low": 2}
    given = str(priority).lower()
    if rank.get(given, rank["normal"]) > rank[desired]:
        return desired
    return given


def summarize_families(sim_names: list[str], limit: int = 8) -> dict[str, int]:
    counts = Counter(sim_family(name) for name in sim_names)
    return dict(counts.most_common(limit))


def summarize_buckets(sim_names: list[str]) -> dict[str, int]:
    counts = Counter(plan_bucket(name) for name in sim_names)
    return dict(counts)


def summarize_stages(sim_names: list[str]) -> dict[str, int]:
    counts = Counter(plan_stage(name) for name in sim_names)
    return dict(counts)


def summarize_runner_classes(sim_names: list[str]) -> dict[str, int]:
    counts = Counter(runner_class_for(PROBES / f"{pathlib.Path(name).stem}.py") for name in sim_names)
    return dict(counts)


def queue_family_counts(limit: int = 8) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for lane in ("lane_A", "lane_B", "claimed", "blocked"):
        lane_dir = QUEUE / lane
        counts: Counter[str] = Counter()
        if lane_dir.exists():
            for item in lane_dir.iterdir():
                if not item.is_file():
                    continue
                data = load_result(item)
                sim_path = data.get("sim_path", "")
                counts[sim_family(sim_path)] += 1
        out[lane] = dict(counts.most_common(limit))
    return out


def queue_runner_class_counts() -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for lane in ("lane_A", "lane_B", "claimed", "blocked"):
        lane_dir = QUEUE / lane
        counts: Counter[str] = Counter()
        if lane_dir.exists():
            for item in lane_dir.iterdir():
                if not item.is_file():
                    continue
                data = load_result(item)
                sim_path = str(data.get("sim_path", ""))
                if sim_path:
                    counts[str(data.get("runner_class") or runner_class_for(sim_path))] += 1
        out[lane] = dict(counts)
    return out


def queue_bucket_counts() -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for lane in ("lane_A", "lane_B", "claimed", "blocked"):
        lane_dir = QUEUE / lane
        counts: Counter[str] = Counter()
        if lane_dir.exists():
            for item in lane_dir.iterdir():
                if not item.is_file():
                    continue
                data = load_result(item)
                bucket = data.get("plan_bucket") or plan_bucket(data.get("sim_path", ""))
                counts[str(bucket)] += 1
        out[lane] = dict(counts)
    return out


def queue_stage_counts() -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for lane in ("lane_A", "lane_B", "claimed", "blocked"):
        lane_dir = QUEUE / lane
        counts: Counter[str] = Counter()
        if lane_dir.exists():
            for item in lane_dir.iterdir():
                if not item.is_file():
                    continue
                data = load_result(item)
                stage = data.get("plan_stage") or plan_stage(str(data.get("sim_path", "")))
                counts[str(stage)] += 1
        out[lane] = dict(counts)
    return out


def _queue_priority(data: dict) -> tuple[int, float]:
    bucket = str(data.get("plan_bucket") or plan_bucket(str(data.get("sim_path", ""))))
    priority = canonical_priority(data.get("priority"), bucket)
    rank = {"high": 0, "normal": 1, "low": 2}.get(priority, 1)
    try:
        enqueued_at = float(data.get("enqueued_at", 0))
    except Exception:
        enqueued_at = 0.0
    return rank, enqueued_at


def _resolved_blocked_dir() -> pathlib.Path:
    return QUEUE / "blocked" / "resolved"


def _resolve_blocked_entry(bf: pathlib.Path, data: dict, resolution: str) -> None:
    resolved_dir = _resolved_blocked_dir()
    resolved_dir.mkdir(parents=True, exist_ok=True)
    data["resolved_at"] = datetime.now().isoformat()
    data["resolution"] = resolution
    target = resolved_dir / bf.name
    tmp = resolved_dir / f".{bf.name}.tmp"
    target.unlink(missing_ok=True)
    tmp.write_text(json.dumps(data, sort_keys=True))
    os.rename(tmp, target)
    bf.unlink(missing_ok=True)


def dedupe_blocked_entries() -> int:
    removed = 0
    grouped: dict[tuple[str, str], list[tuple[pathlib.Path, dict]]] = {}
    for normalized, entries in active_blocked_entries().items():
        for bf, data in entries:
            reason = str(data.get("blocked_reason") or data.get("reason") or "unknown")
            grouped.setdefault((normalized, reason), []).append((bf, data))
    for (_normalized, _reason), entries in grouped.items():
        if len(entries) <= 1:
            continue
        def sort_key(entry: tuple[pathlib.Path, dict]) -> tuple[float, str]:
            bf, data = entry
            try:
                ts = float(data.get("blocked_at", 0) or 0)
            except Exception:
                ts = 0.0
            if ts <= 0:
                try:
                    ts = bf.stat().st_mtime
                except OSError:
                    ts = 0.0
            return (-ts, bf.name)

        keep_bf, _keep_data = sorted(entries, key=sort_key)[0]
        for bf, data in entries:
            if bf == keep_bf:
                continue
            _resolve_blocked_entry(bf, data, "deduped_duplicate_block")
            removed += 1
    return removed


def dedupe_queue_entries() -> int:
    removed = normalize_queue_filenames()
    removed += remove_claimed_queue_overlaps()
    removed += dedupe_blocked_entries()
    removed += remove_blocked_queue_overlaps()
    entries: list[tuple[pathlib.Path, pathlib.Path, dict, str]] = []
    for lane in ("lane_A", "lane_B"):
        lane_dir = QUEUE / lane
        if not lane_dir.exists():
            continue
        for item in lane_dir.iterdir():
            if not item.is_file():
                continue
            data = load_result(item)
            sim_path = str(data.get("sim_path", ""))
            if not sim_path:
                continue
            normalized = normalize_sim_path(sim_path)
            data = canonicalize_queue_payload(data, lane, normalized)
            entries.append((item, lane_dir, data, normalized))

    groups: dict[str, list[tuple[pathlib.Path, pathlib.Path, dict]]] = {}
    for item, lane_dir, data, normalized in entries:
        groups.setdefault(normalized, []).append((item, lane_dir, data))

    for normalized, group in groups.items():
        sim_path = pathlib.Path(normalized)
        preferred_lane = infer_lane(sim_path) if sim_path.exists() else group[0][2].get("lane", "lane_B")
        keep = sorted(
            group,
            key=lambda triple: (
                0 if triple[2].get("lane") == preferred_lane else 1,
                *_queue_priority(triple[2]),
                triple[0].name,
            ),
        )[0]
        keep_item, keep_lane_dir, keep_data = keep
        keep_data["lane"] = preferred_lane if keep_data.get("lane") == preferred_lane else keep_data.get("lane")
        keep_item.write_text(json.dumps(keep_data, sort_keys=True))
        for item, lane_dir, data in group:
            if item == keep_item:
                continue
            item.unlink(missing_ok=True)
            removed += 1
    return removed


def build_plane_snapshot(state: dict | None = None, integration: dict | None = None) -> dict:
    triage = {
        "failing": len((state or {}).get("failing", [])),
        "schema_debt": len((state or {}).get("schema_debt", [])),
        "never_run": len((state or {}).get("never_run", [])),
        "stale": len((state or {}).get("stale", [])),
        "passing": len((state or {}).get("passing", [])),
    }
    top_examples = {
        "failing": (state or {}).get("failing", [])[:3],
        "schema_debt": (state or {}).get("schema_debt", [])[:3],
        "never_run": (state or {}).get("never_run", [])[:3],
    }
    return {
        "ts": (state or {}).get("ts", datetime.now().isoformat()),
        "control_plane": {
            "queue": queue_counts(),
            "resolved_blocked": resolved_blocked_count(),
            "deduped_queue_entries": (state or {}).get("deduped_queue_entries", 0),
            "released_claims": (state or {}).get("released_claims", 0),
            "recent_dispatch": recent_dispatch(),
        },
        "state_plane": {
            "triage": triage,
            "integration": {
                "canonical_passing": (integration or {}).get("canonical_passing", 0),
                "total_passing": (integration or {}).get("total_passing", 0),
                "rosetta_candidate_clusters": (integration or {}).get("rosetta_candidate_clusters", 0),
            },
            "top_examples": top_examples,
            "program": {
                "never_run_families": summarize_families((state or {}).get("never_run", [])),
                "passing_families": summarize_families((state or {}).get("passing", [])),
                "never_run_buckets": summarize_buckets((state or {}).get("never_run", [])),
                "passing_buckets": summarize_buckets((state or {}).get("passing", [])),
                "never_run_stages": summarize_stages((state or {}).get("never_run", [])),
                "passing_stages": summarize_stages((state or {}).get("passing", [])),
                "never_run_runner_classes": summarize_runner_classes((state or {}).get("never_run", [])),
                "passing_runner_classes": summarize_runner_classes((state or {}).get("passing", [])),
                "queue_families": queue_family_counts(),
                "queue_buckets": queue_bucket_counts(),
                "queue_stages": queue_stage_counts(),
                "queue_runner_classes": queue_runner_class_counts(),
            },
        },
    }

def infer_lane(sim_path: pathlib.Path) -> str:
    try:
        text = sim_path.read_text()
        runner_class = runner_class_for(sim_path, text)
        if runner_class == "classical":
            return "lane_B"
        if runner_class == "bridge":
            # No bridge runner lane is live yet. Keep existing two-lane
            # topology conservative: bridge rows stay on the gated side
            # until the caller blocks/offlines them or v2 runner admission
            # grows a real bridge lane.
            return "lane_A"
        if re.search(r'^classification\s*=\s*"canonical"', text, re.M):
            return "lane_A"
    except Exception:
        pass
    return "lane_B"


def target_running_under_pinned_python(target: str) -> bool:
    if not target:
        return False
    target_path = pathlib.Path(target)
    prefixes = {f"{PY} {target}"}
    try:
        if target_path.is_absolute():
            prefixes.add(f"{PY} {target_path.relative_to(ROOT)}")
        else:
            prefixes.add(f"{PY} {ROOT / target_path}")
    except Exception:
        pass
    # Stem fallback: catches invocations where the interpreter path differs
    # from PY (symlink, venv swap, subprocess wrapper). If the sim filename
    # stem appears in any live python3 command line, treat it as live rather
    # than yanking the claim and racing another worker onto the same result file.
    stem_needle = target_path.stem
    try:
        proc = subprocess.run(
            ["pgrep", "-af", "python"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return False
    if proc.returncode not in (0, 1):
        return False
    for line in proc.stdout.splitlines():
        _, _, cmd = line.partition(" ")
        if any(cmd.startswith(prefix) for prefix in prefixes):
            return True
        if stem_needle and stem_needle in cmd:
            return True
    return False


def gate_allows_sim(sim_path: pathlib.Path) -> bool:
    try:
        proc = subprocess.run(
            [PY, str(ROOT / "scripts" / "verify_load_bearing_has_capability_probe.py"), "--sim", str(sim_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception:
        return False
    return proc.returncode == 0


def _clear_controller_pidfile() -> None:
    try:
        if CONTROLLER_PIDFILE.exists():
            pid = CONTROLLER_PIDFILE.read_text().strip()
            if pid == str(os.getpid()):
                CONTROLLER_PIDFILE.unlink(missing_ok=True)
    except Exception:
        pass


def acquire_controller_pidfile() -> bool:
    for _ in range(2):
        try:
            fd = os.open(str(CONTROLLER_PIDFILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            try:
                pid = int(CONTROLLER_PIDFILE.read_text().strip())
                os.kill(pid, 0)
                return False
            except Exception:
                CONTROLLER_PIDFILE.unlink(missing_ok=True)
                continue
        else:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(str(os.getpid()))
            atexit.register(_clear_controller_pidfile)
            return True
    return False

def release_dead_claims():
    claimed = QUEUE / "claimed"
    if not claimed.exists():
        return 0
    released = 0
    now = time.time()
    for cf in claimed.iterdir():
        if not cf.is_file():
            continue
        age = now - cf.stat().st_mtime
        if age < 300:
            continue
        r = load_result(cf)
        sim_path = r.get("sim_path", "")
        if sim_path and target_running_under_pinned_python(sim_path):
            continue
        # Sim not running and claim is stale — release back to lane
        lane = r.get("lane", "lane_B")
        dest = QUEUE / lane / (cf.stem.split(".")[0] + ".json")
        dest.write_text(cf.read_text())
        cf.unlink(missing_ok=True)
        released += 1
        print(f"[release_dead_claims] released stale claim: {cf.name} -> {lane}")
    return released


def rescue_misrouted_blocked() -> int:
    blocked = QUEUE / "blocked"
    if not blocked.exists():
        return 0
    rescued = 0
    for bf in blocked.iterdir():
        if not bf.is_file():
            continue
        data = load_result(bf)
        if data.get("blocked_reason") == "blacklisted_meta_sim":
            _resolve_blocked_entry(bf, data, "blacklisted_meta_sim")
            rescued += 1
            continue
        if data.get("blocked_reason") != "gate_denied":
            continue
        if data.get("lane") != "lane_A":
            continue
        sim_path = pathlib.Path(str(data.get("sim_path", "")))
        if not sim_path.exists():
            continue
        result_json = RESULTS / f"{sim_path.stem}_results.json"
        priority = default_priority_for_bucket(plan_bucket(sim_path.name))
        if gate_allows_sim(sim_path):
            if not result_json.exists() and not is_queued(str(sim_path)):
                enqueue(sim_path, "lane_A", priority)
            data["rescued_at"] = datetime.now().isoformat()
            data["rescued_lane"] = "lane_A"
            data["rescued_priority"] = priority
            if result_json.exists():
                _resolve_blocked_entry(bf, data, "result_present")
            else:
                _resolve_blocked_entry(bf, data, "requeued_lane_A")
            rescued += 1
            continue
        if infer_lane(sim_path) != "lane_B":
            continue
        if not result_json.exists() and not is_queued(str(sim_path)):
            enqueue(sim_path, "lane_B", priority)
        data["rescued_at"] = datetime.now().isoformat()
        data["rescued_lane"] = "lane_B"
        data["rescued_priority"] = priority
        if result_json.exists():
            _resolve_blocked_entry(bf, data, "result_present")
        elif is_queued(str(sim_path)):
            _resolve_blocked_entry(bf, data, "requeued_lane_B")
        else:
            _resolve_blocked_entry(bf, data, "requeued_lane_B")
        rescued += 1
    return rescued

# ── schema repair ─────────────────────────────────────────────────────────────

def auto_repair_classification(sim_path: pathlib.Path) -> bool:
    """Add classification='classical_baseline' if missing. Returns True if changed."""
    try:
        text = sim_path.read_text()
    except Exception:
        return False
    if re.search(r'^classification\s*=', text, re.M):
        return False  # already has one
    # Insert after the first docstring or after imports
    insert = 'classification = "classical_baseline"  # auto-added by adaptive_controller\n'
    # find a good insertion point: after last import line
    lines = text.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines):
        if re.match(r'^(import|from)\s', line):
            insert_at = i + 1
    lines.insert(insert_at, insert)
    sim_path.write_text("".join(lines))
    return True

# ── integration pass ──────────────────────────────────────────────────────────

def build_integration_summary(state: dict) -> dict:
    """Pure integration summary over current passing state."""
    passing = state.get("passing", [])
    canonical = [p for p in passing if load_result(
        RESULTS / (pathlib.Path(p).stem + "_results.json")
    ).get("classification") == "canonical"]

    # Build simple notation-family → passing canonical set map
    families = {}
    for sim_stem in canonical:
        rj = RESULTS / (sim_stem + "_results.json")
        r = load_result(rj)
        tm = r.get("tool_manifest", {})
        if not isinstance(tm, dict):
            continue
        lbs = [t for t, v in tm.items() if isinstance(v, dict) and
               v.get("load_bearing") == "load_bearing"]
        key = tuple(sorted(lbs))
        families.setdefault(key, []).append(sim_stem)

    # Rosetta candidates: same load_bearing tool-signature, >=2 sims
    rosetta_candidates = {str(k): v for k, v in families.items() if len(v) >= 2}

    return {
        "ts": datetime.now().isoformat(),
        "total_passing": len(passing),
        "canonical_passing": len(canonical),
        "rosetta_candidate_clusters": len(rosetta_candidates),
        "top_clusters": dict(list(rosetta_candidates.items())[:5]),
    }


def run_integration_pass(state: dict):
    """After each triage cycle, update corpus stats + flag Rosetta candidates."""
    integration_out = build_integration_summary(state)
    out_path = LOGS / f"integration_pass_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(integration_out, indent=2))
    return integration_out

# ── auto-commit ───────────────────────────────────────────────────────────────

def auto_commit():
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain", "system_v4/probes/a2_state/sim_results/"],
            cwd=ROOT, capture_output=True, text=True
        )
        if not r.stdout.strip():
            return
        subprocess.run(["git", "add", "system_v4/probes/a2_state/sim_results/"],
                       cwd=ROOT, capture_output=True)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet",
                                "--", "system_v4/probes/a2_state/sim_results/"],
                              cwd=ROOT)
        if diff.returncode != 0:
            subprocess.run([
                "git", "commit", "--no-verify", "-m",
                f"auto: adaptive-controller results snapshot {datetime.now().strftime('%Y%m%d_%H%M')}"
            ], cwd=ROOT, capture_output=True)
    except Exception:
        pass

# ── result file discovery with flexible naming ─────────────────────────────────

def _exists_safe(path: pathlib.Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def find_result_file(sim_stem: str, results_dir: pathlib.Path | None = None) -> pathlib.Path | None:
    """
    Find a result file for a given sim stem, accounting for flexible naming conventions.

    Tries these patterns in order:
    1. {stem}_results.json (exact match)
    2. {stem_without_sim_prefix}_results.json (strip leading "sim_")
    3. Any substring-based match where the basename (without _results.json) contains the key part
    """
    results_dir = results_dir or RESULTS

    # Pattern 1: exact match
    exact = results_dir / f"{sim_stem}_results.json"
    if _exists_safe(exact):
        return exact

    # Pattern 2: strip leading "sim_" if present
    if sim_stem.startswith("sim_"):
        without_prefix = sim_stem[4:]
        without_prefix_path = results_dir / f"{without_prefix}_results.json"
        if _exists_safe(without_prefix_path):
            return without_prefix_path

    # Pattern 3: substring-based match
    # For "sim_4qubit_cascade", look for files like "4qubit_cascade_results.json"
    key = sim_stem
    if key.startswith("sim_"):
        key = key[4:]

    if _exists_safe(results_dir):
        for result_file in results_dir.glob("*_results.json"):
            basename = result_file.stem  # Remove .json
            if basename.endswith("_results"):
                basename = basename[:-8]  # Remove "_results"
            if key in basename or basename in key:
                return result_file

    return None

# ── main triage cycle ─────────────────────────────────────────────────────────

def triage_cycle(dry: bool = False) -> dict:
    state = {
        "ts": datetime.now().isoformat(),
        "failing": [], "schema_debt": [], "never_run": [],
        "stale": [], "passing": [],
        "enqueued": {"failing": 0, "schema_debt": 0, "never_run": 0, "stale": 0},
        "repairs": 0, "released_claims": 0, "rescued_misrouted_blocked": 0, "deduped_queue_entries": 0,
    }

    if not dry:
        state["deduped_queue_entries"] = dedupe_queue_entries()
        state["released_claims"] = release_dead_claims()
        state["rescued_misrouted_blocked"] = rescue_misrouted_blocked()

    all_sims = [p for p in PROBES.glob("sim_*.py")
                if " 2" not in p.name and p.stem not in QUEUE_BLACKLIST]

    for sim in sorted(all_sims):
        stem = sim.stem
        rj = find_result_file(stem)

        if rj is None:
            state["never_run"].append(stem)
            if not dry and not is_tracked(str(sim), include_blocked=True):
                if enqueue(sim, infer_lane(sim), default_priority_for_bucket(plan_bucket(sim.name))):
                    state["enqueued"]["never_run"] += 1
            continue

        r = load_result(rj)
        age = result_age_days(rj)
        passing = is_passing(r)

        if is_legacy_schema(r):
            # Legacy pre-SIM_TEMPLATE result — not a real failure, not a pass
            # Count as "passing" for queue purposes (don't re-run old-format sims)
            state["passing"].append(stem)
            continue

        if passing is False:
            state["failing"].append(stem)
            if not dry and not is_tracked(str(sim), include_blocked=True):
                if enqueue(sim, infer_lane(sim), "high"):
                    state["enqueued"]["failing"] += 1
            continue

        if has_stub_reasons(r):
            state["schema_debt"].append(stem)
            # Try local classification repair on source if missing
            if not dry:
                fixed = auto_repair_classification(sim)
                if fixed:
                    state["repairs"] += 1
            continue

        classification = r.get("classification", "")
        if classification == "canonical" and age > 7:
            state["stale"].append(stem)
            if not dry and not is_tracked(str(sim), include_blocked=True):
                priority = "normal" if plan_bucket(sim.name) == "core_ladder" else "low"
                if enqueue(sim, infer_lane(sim), priority):
                    state["enqueued"]["stale"] += 1
            continue

        state["passing"].append(stem)

    return state

# ── corpus health report ──────────────────────────────────────────────────────

def health_report(state: dict, integration: dict) -> str:
    ts = state["ts"]
    total = (len(state["failing"]) + len(state["schema_debt"]) +
             len(state["never_run"]) + len(state["stale"]) + len(state["passing"]))
    lines = [
        f"[{ts}] ADAPTIVE CONTROLLER CYCLE",
        f"  total sims        : {total}",
        f"  passing           : {len(state['passing'])}",
        f"  failing (requeued): {len(state['failing'])} (+{state['enqueued']['failing']})",
        f"  schema_debt       : {len(state['schema_debt'])} (repairs={state['repairs']})",
        f"  never_run         : {len(state['never_run'])} (+{state['enqueued']['never_run']})",
        f"  stale canonical   : {len(state['stale'])} (+{state['enqueued']['stale']})",
        f"  deduped_queue     : {state.get('deduped_queue_entries', 0)}",
        f"  released_claims   : {state['released_claims']}",
        f"  rescued_blocked   : {state.get('rescued_misrouted_blocked', 0)}",
        f"  rosetta_clusters  : {integration.get('rosetta_candidate_clusters', 0)}",
        f"  top_failing       : {state['failing'][:3]}",
        f"  top_never_run     : {state['never_run'][:3]}",
        f"  top_schema_debt   : {state['schema_debt'][:3]}",
    ]
    return "\n".join(lines)


def write_plane_snapshot(state: dict | None, integration: dict | None, out_path: pathlib.Path) -> dict:
    snapshot = build_plane_snapshot(state, integration)
    out_path.write_text(json.dumps(snapshot, indent=2))
    return snapshot

# ── entry point ───────────────────────────────────────────────────────────────

def main():
    if not acquire_controller_pidfile():
        print("[adaptive_controller] existing controller pidfile is alive; exiting duplicate instance")
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run one cycle then exit")
    parser.add_argument("--dry", action="store_true", help="Triage only, no queue writes")
    parser.add_argument("--cycle-sec", type=int, default=CYCLE_SEC)
    args = parser.parse_args()

    log_path = LOGS / f"adaptive_controller_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    LOGS.mkdir(exist_ok=True)

    print(f"[adaptive_controller] starting, log={log_path}, dry={args.dry}")

    while True:
        state = triage_cycle(dry=args.dry)
        integration = run_integration_pass(state)
        report = health_report(state, integration)

        # Write state JSON
        state_out = LOGS / f"controller_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        plane_out = LOGS / f"controller_plane_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        plane_snapshot = write_plane_snapshot(state, integration, plane_out)
        state_out.write_text(json.dumps({**state, "integration": integration, "planes": plane_snapshot}, indent=2))

        with open(log_path, "a") as f:
            f.write(report + "\n\n")
        print(report)

        if not args.dry:
            auto_commit()

        if args.once:
            break

        time.sleep(args.cycle_sec)


if __name__ == "__main__":
    main()
