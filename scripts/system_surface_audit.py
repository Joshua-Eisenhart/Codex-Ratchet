#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path

import adaptive_controller
import sim_program_audit


REPO = Path(__file__).resolve().parents[1]
PROBES = adaptive_controller.PROBES
RESULT_ROOTS = [
    REPO / "system_v4/probes/a2_state/sim_results",
    REPO / "system_v4/probes/sim_results",
    REPO / "system_v4/a2_state/sim_results",
]
PIDFILES = {
    "perpetual_runner": Path("/tmp/codex_ratchet_perpetual_runner.pid"),
    "adaptive_controller": Path("/tmp/codex_ratchet_adaptive_controller.pid"),
    "autonomous_reseed": Path("/tmp/codex_ratchet_autonomous_reseed.pid"),
    "overnight_lock": Path("/tmp/codex_ratchet_overnight.lock"),
}


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(args, cwd=cwd or REPO, capture_output=True, text=True)
    except (FileNotFoundError, PermissionError, OSError):
        return None


def _process_command(pid: int) -> str | None:
    proc = _run(["ps", "-p", str(pid), "-o", "command="])
    if proc is None or proc.returncode != 0:
        return None
    text = proc.stdout.strip()
    return text or None


def _pidfile_status(name: str, pidfile: Path) -> dict:
    status = {
        "name": name,
        "pidfile": str(pidfile),
        "pid": None,
        "alive": None,
        "alive_state": "missing_pidfile",
        "command": None,
    }
    if not pidfile.exists():
        return status
    try:
        pid = int(pidfile.read_text(encoding="utf-8").strip())
    except Exception:
        status["alive_state"] = "invalid_pidfile"
        return status
    status["pid"] = pid
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        status["alive"] = False
        status["alive_state"] = "stale_pid"
        return status
    except PermissionError:
        status["command"] = _process_command(pid)
        if status["command"]:
            status["alive"] = True
            status["alive_state"] = "ps_visible_permission_limited"
            return status
        status["alive"] = None
        status["alive_state"] = "permission_limited"
        return status
    except OSError:
        status["command"] = _process_command(pid)
        if status["command"]:
            status["alive"] = True
            status["alive_state"] = "ps_visible_os_error_limited"
            return status
        status["alive"] = None
        status["alive_state"] = "os_error_limited"
        return status
    status["alive"] = True
    status["alive_state"] = "alive"
    status["command"] = _process_command(pid)
    return status


def _wrapper_processes() -> list[dict]:
    rows = []
    for args in (["ps", "aux"], ["ps", "-Ao", "pid=,command="]):
        proc = _run(args)
        if proc is None or proc.returncode != 0:
            continue
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line or "scripts/perpetual_runner.sh" not in line:
                continue
            if args == ["ps", "aux"]:
                parts = line.split(None, 10)
                if len(parts) < 11:
                    continue
                pid_text = parts[1]
                cmd = parts[10]
            else:
                pid_text, _, cmd = line.partition(" ")
            try:
                pid = int(pid_text.strip())
            except ValueError:
                continue
            rows.append({"pid": pid, "command": cmd.strip()})
        if rows:
            break
    return rows


def _queue_claim_summary(limit: int = 8) -> dict:
    claimed_dir = adaptive_controller.QUEUE / "claimed"
    samples = []
    if claimed_dir.exists():
        for path in sorted(claimed_dir.glob("*.json.*"))[:limit]:
            data = adaptive_controller.load_result(path)
            samples.append({
                "file": path.name,
                "sim": Path(str(data.get("sim_path", ""))).name,
                "lane": data.get("lane"),
                "claimed_at": data.get("claimed_at"),
            })
    return {"count": adaptive_controller.queue_counts().get("claimed", 0), "samples": samples}


def _queue_dir_freshness(path: Path) -> dict:
    newest_name = None
    newest_mtime = None
    if path.exists():
        for entry in path.iterdir():
            if not entry.is_file():
                continue
            try:
                mtime = entry.stat().st_mtime
            except OSError:
                continue
            if newest_mtime is None or mtime > newest_mtime:
                newest_mtime = mtime
                newest_name = entry.name
    age = None if newest_mtime is None else max(0.0, time.time() - newest_mtime)
    return {
        "newest_file": newest_name,
        "newest_age_sec": age,
        "active_within_60s": age is not None and age < 60,
        "active_within_300s": age is not None and age < 300,
    }


def _git_layer(path: str) -> str:
    if path.startswith("READ ONLY Legacy "):
        return "legacy_copies"
    if path.startswith("obsidian_vault/"):
        return "owner_vault"
    if path.startswith("system_v5/new docs/") or path.endswith(".md"):
        return "owner_docs"
    if path.startswith("system_v4/probes/sim_") and path.endswith(".py"):
        return "probe_sources"
    if path.startswith("system_v4/probes/a2_state/sim_results/") or path.startswith("system_v4/probes/sim_results/"):
        return "probe_results"
    if path.startswith("system_v4/a2_state/sim_results/") or path.startswith("system_v4/a2_state/audit_logs/"):
        return "system_results"
    if path.startswith("overnight_logs/"):
        return "runner_logs"
    if path.startswith("scripts/") or path.startswith("system_v5/tests/"):
        return "code_and_tests"
    return "other"


def _git_status_entries() -> list[dict[str, str]]:
    proc = _run(["git", "status", "--short", "--untracked-files=all"])
    if proc is None:
        return []
    entries: list[dict[str, str]] = []
    for line in proc.stdout.splitlines():
        if not line:
            continue
        status = line[:2]
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        entries.append({"status": status, "path": path.strip('"')})
    return entries


def git_surface() -> dict:
    entries = _git_status_entries()
    if not entries:
        return {"total_entries": 0, "layers": {}, "samples": {}, "error": "git_status_unavailable"}
    counts: Counter[str] = Counter()
    samples: defaultdict[str, list[dict]] = defaultdict(list)
    total = 0
    for entry in entries:
        total += 1
        status = entry["status"]
        path = entry["path"]
        layer = _git_layer(path)
        counts[layer] += 1
        if len(samples[layer]) < 8:
            samples[layer].append({"status": status, "path": path})
    return {
        "total_entries": total,
        "layers": dict(counts),
        "samples": dict(samples),
        "cleanup_posture": {
            "code_and_tests": "KEEP_ACTIVE",
            "runner_logs": "KEEP_ACTIVE",
            "probe_sources": "BLOCKED_REQUIRES_PREP",
            "probe_results": "KEEP_ACTIVE",
            "system_results": "KEEP_ACTIVE",
            "owner_vault": "BLOCKED_REQUIRES_PREP",
            "owner_docs": "BLOCKED_REQUIRES_PREP",
            "legacy_copies": "MOVE_TO_QUARANTINE",
            "other": "BLOCKED_REQUIRES_PREP",
        },
    }


def _pass_state(data: object) -> str:
    if not isinstance(data, dict):
        return "non_dict_json"
    value = adaptive_controller.is_passing(data)
    if value is True:
        return "pass"
    if value is False:
        return "fail"
    if _looks_like_legacy_pass(data):
        return "pass_inferred"
    return "unknown"


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


def _all_check_flags_pass(section: object) -> bool | None:
    saw_flag = False
    failed = False
    if isinstance(section, dict):
        for key, value in section.items():
            if key in {"pass", "passed", "ok"}:
                flag = _boolish(value)
                if flag is None:
                    continue
                saw_flag = True
                if not flag:
                    failed = True
            else:
                nested = _all_check_flags_pass(value)
                if nested is True:
                    saw_flag = True
                elif nested is False:
                    saw_flag = True
                    failed = True
    elif isinstance(section, list):
        for value in section:
            nested = _all_check_flags_pass(value)
            if nested is True:
                saw_flag = True
            elif nested is False:
                saw_flag = True
                failed = True
    if not saw_flag:
        return None
    return not failed


def _summary_counts_all_pass(summary: dict) -> bool:
    passed = summary.get("passed")
    total = summary.get("total")
    if isinstance(passed, int) and isinstance(total, int) and total > 0:
        return passed == total
    for value in summary.values():
        if isinstance(value, str) and "/" in value:
            left, _, right = value.partition("/")
            try:
                if int(left) != int(right):
                    return False
            except ValueError:
                continue
    return any(isinstance(value, str) and "/" in value for value in summary.values())


def _looks_like_legacy_pass(data: dict) -> bool:
    if isinstance(data.get("evidence_ledger"), list) and data["evidence_ledger"]:
        statuses = [str(item.get("status", "")).upper() for item in data["evidence_ledger"] if isinstance(item, dict)]
        if statuses and all(status == "PASS" for status in statuses):
            return True
    if data.get("ALL_PASS") is True:
        return True
    if isinstance(data.get("summary"), dict) and _summary_counts_all_pass(data["summary"]):
        return True
    if isinstance(data.get("summary"), dict) and adaptive_controller._summary_bools_all_true(data["summary"]):
        return True
    if adaptive_controller._nested_statuses_all_ok(data):
        return True
    section_votes = []
    for key in ("positive", "negative", "boundary", "results"):
        if key in data:
            vote = _all_check_flags_pass(data[key])
            if vote is not None:
                section_votes.append(vote)
    return bool(section_votes) and all(section_votes)


def _section_flag_counts(section: object) -> tuple[int, int]:
    total = 0
    failed = 0

    def walk(value: object) -> None:
        nonlocal total, failed
        if isinstance(value, dict):
            for key, nested in value.items():
                if key in {"pass", "passed", "ok"}:
                    flag = _boolish(nested)
                    if flag is None:
                        continue
                    total += 1
                    if not flag:
                        failed += 1
                else:
                    walk(nested)
            return
        if isinstance(value, list):
            for nested in value:
                walk(nested)

    walk(section)
    return total, failed


def _result_fail_mode(data: object) -> str | None:
    if not isinstance(data, dict):
        return None
    if _pass_state(data) != "fail":
        return None
    if data.get("error") or data.get("failure_reason"):
        return "explicit_error"
    if isinstance(data.get("summary"), dict):
        summary = data["summary"]
        tests_failed = summary.get("tests_failed")
        if isinstance(tests_failed, int) and tests_failed > 0:
            return "tests_failed"
        passed = summary.get("passed")
        total = summary.get("total")
        if isinstance(passed, int) and isinstance(total, int) and passed < total:
            return "partial_pass"
        for key in ("all_pass", "all_passed"):
            verdict = _boolish(summary.get(key))
            if verdict is False:
                return "summary_gate_false"
    top_all_pass = _boolish(data.get("all_pass"))
    if top_all_pass is False:
        return "top_level_gate_false"
    total_flags = 0
    failed_flags = 0
    for key in ("positive", "negative", "boundary", "results"):
        section_total, section_failed = _section_flag_counts(data.get(key))
        total_flags += section_total
        failed_flags += section_failed
    if total_flags and failed_flags:
        return "section_check_failed"
    return "unclassified_fail"


def _result_family(path: Path) -> str:
    stem = path.name
    if stem.endswith("_results.json"):
        stem = stem[:-13]
    elif stem.endswith(".json"):
        stem = stem[:-5]
    if stem.startswith("sim_"):
        stem = stem[4:]
    return stem.split("_", 1)[0] if "_" in stem else stem


def _dirty_probe_source_paths() -> tuple[set[str], set[str]]:
    dirty: set[str] = set()
    untracked: set[str] = set()
    for entry in _git_status_entries():
        path = entry["path"]
        if _git_layer(path) != "probe_sources":
            continue
        dirty.add(path)
        if entry["status"] == "??":
            untracked.add(path)
    return dirty, untracked


def result_surface() -> dict:
    dirty_probe_sources, untracked_probe_sources = _dirty_probe_source_paths()
    roots = {}
    for root in RESULT_ROOTS:
        files = list(root.glob("*.json")) if root.exists() else []
        status_counts: Counter[str] = Counter()
        schema_counts: Counter[str] = Counter()
        fail_families: Counter[str] = Counter()
        fail_modes: Counter[str] = Counter()
        unknown_families: Counter[str] = Counter()
        dirty_source_results = 0
        untracked_source_results = 0
        orphan_like = 0
        samples: defaultdict[str, list[str]] = defaultdict(list)
        for path in files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                data = None
            pass_state = _pass_state(data)
            status_counts[pass_state] += 1
            if pass_state == "fail" and len(samples["fail"]) < 8:
                samples["fail"].append(path.name)
                fail_families[_result_family(path)] += 1
            elif pass_state == "fail":
                fail_families[_result_family(path)] += 1
            elif pass_state == "unknown":
                unknown_families[_result_family(path)] += 1
            fail_mode = _result_fail_mode(data)
            if fail_mode:
                fail_modes[fail_mode] += 1
            if isinstance(data, dict):
                if "overall_pass" in data:
                    schema_counts["overall_pass"] += 1
                elif "passed" in data:
                    schema_counts["passed_only"] += 1
                elif "all_pass" in data:
                    schema_counts["all_pass"] += 1
                elif "ALL_PASS" in data:
                    schema_counts["ALL_PASS"] += 1
                elif isinstance(data.get("summary"), dict) and "all_pass" in data["summary"]:
                    schema_counts["summary_all_pass"] += 1
                elif isinstance(data.get("summary"), dict) and "all_passed" in data["summary"]:
                    schema_counts["summary_all_passed"] += 1
                elif isinstance(data.get("summary"), dict) and adaptive_controller._summary_bools_all_true(data["summary"]):
                    schema_counts["summary_bool_inferred"] += 1
                elif adaptive_controller._nested_statuses_all_ok(data):
                    schema_counts["nested_status_inferred"] += 1
                elif _looks_like_legacy_pass(data):
                    schema_counts["legacy_pass_inferred"] += 1
                else:
                    schema_counts["no_pass_key"] += 1
                    if len(samples["no_pass_key"]) < 8:
                        samples["no_pass_key"].append(path.name)
            else:
                schema_counts["non_dict_json"] += 1
                if len(samples["non_dict_json"]) < 8:
                    samples["non_dict_json"].append(path.name)
            if root != REPO / "system_v4/a2_state/sim_results" and path.name.endswith("_results.json"):
                stem = path.name[:-13]
                rel_source = str((PROBES / f"{stem}.py").relative_to(REPO))
                if rel_source in dirty_probe_sources:
                    dirty_source_results += 1
                    if len(samples["dirty_source_results"]) < 8:
                        samples["dirty_source_results"].append(path.name)
                if rel_source in untracked_probe_sources:
                    untracked_source_results += 1
                    if len(samples["untracked_source_results"]) < 8:
                        samples["untracked_source_results"].append(path.name)
                if not (PROBES / f"{stem}.py").exists():
                    orphan_like += 1
                    if len(samples["orphan_like"]) < 8:
                        samples["orphan_like"].append(path.name)
        roots[str(root.relative_to(REPO))] = {
            "count": len(files),
            "status": dict(status_counts),
            "schema": dict(schema_counts),
            "fail_families": dict(fail_families.most_common(10)),
            "fail_modes": dict(fail_modes.most_common(10)),
            "unknown_families": dict(unknown_families.most_common(10)),
            "dirty_source_results": dirty_source_results,
            "untracked_source_results": untracked_source_results,
            "orphan_like": orphan_like,
            "samples": dict(samples),
        }
    return roots


def _runner_health(queue_counts: dict, freshness: dict) -> dict:
    claimed = int(queue_counts.get("claimed", 0) or 0)
    done_fresh = freshness.get("done", {}).get("active_within_60s") is True
    claimed_fresh = freshness.get("claimed", {}).get("active_within_60s") is True
    lane_b_fresh = freshness.get("lane_B", {}).get("active_within_60s") is True
    backlog = int(queue_counts.get("lane_A", 0) or 0) + int(queue_counts.get("lane_B", 0) or 0)
    if claimed > 0 and done_fresh:
        return {"status": "draining", "reason": "claimed and done surfaces are both fresh"}
    if claimed > 0 and not done_fresh:
        return {"status": "possibly_stuck", "reason": "claims exist but done surface is stale"}
    if claimed == 0 and backlog > 0 and lane_b_fresh:
        return {"status": "feeding", "reason": "queue is active but workers are between claims"}
    if claimed == 0 and backlog > 0:
        return {"status": "idle_with_backlog", "reason": "backlog exists without fresh claim/done movement"}
    return {"status": "idle", "reason": "no active claims and no material backlog"}


def runner_surface() -> dict:
    queue_counts = adaptive_controller.queue_counts()
    freshness = {
        lane: _queue_dir_freshness(adaptive_controller.QUEUE / lane)
        for lane in ("lane_A", "lane_B", "claimed", "done")
    }
    return {
        "pidfiles": {name: _pidfile_status(name, pidfile) for name, pidfile in PIDFILES.items()},
        "wrappers": _wrapper_processes(),
        "queue": queue_counts,
        "freshness": freshness,
        "health": _runner_health(queue_counts, freshness),
        "claimed": _queue_claim_summary(),
    }


def program_surface() -> dict:
    state = adaptive_controller.triage_cycle(dry=True)
    integration = adaptive_controller.build_integration_summary(state)
    snapshot = adaptive_controller.build_plane_snapshot(state, integration)
    return {
        "triage": snapshot["state_plane"]["triage"],
        "queue_duplicates": sim_program_audit.queue_duplicate_summary(),
        "queue_noncanonical_names": sim_program_audit.queue_noncanonical_summary(),
        "queue_claimed_overlaps": sim_program_audit.queue_claimed_overlap_summary(),
        "next_queue_candidates": {
            "lane_A": sim_program_audit.next_queue_candidates("lane_A", limit=6),
            "lane_B": sim_program_audit.next_queue_candidates("lane_B", limit=6),
        },
        "never_run_families": snapshot["state_plane"]["program"]["never_run_families"],
        "never_run_buckets": snapshot["state_plane"]["program"]["never_run_buckets"],
        "never_run_stages": snapshot["state_plane"]["program"]["never_run_stages"],
    }


def main() -> int:
    report = {
        "git": git_surface(),
        "runner": runner_surface(),
        "program": program_surface(),
        "results": result_surface(),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
