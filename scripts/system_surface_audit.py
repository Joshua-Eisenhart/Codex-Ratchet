#!/usr/bin/env python3
from __future__ import annotations

import ast
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
RESULTS_DIR = PROBES / "a2_state" / "sim_results"
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
IMPORT_TOOL_ALIASES = {
    "torch": "pytorch",
    "torch_geometric": "pyg",
    "z3": "z3",
    "cvc5": "cvc5",
    "sympy": "sympy",
    "clifford": "clifford",
    "geomstats": "geomstats",
    "e3nn": "e3nn",
    "rustworkx": "rustworkx",
    "xgi": "xgi",
    "toponetx": "toponetx",
    "gudhi": "gudhi",
    "networkx": "networkx",
    "igraph": "igraph",
    "hypothesis": "hypothesis",
    "optuna": "optuna",
    "evotorch": "evotorch",
    "datasketch": "datasketch",
    "pynndescent": "pynndescent",
    "sklearn": "sklearn",
    "hdbscan": "hdbscan",
    "umap": "umap",
    "pymoo": "pymoo",
    "ribs": "ribs",
    "deap": "deap",
    "networkx": "networkx",
    "igraph": "igraph",
    "scipy": "scipy",
    "cma": "cma",
}
TOOL_BUNDLES = {
    "symbolic_solver_stack": {
        "goal": "solver + symbolic + rotor reference lane",
        "tools": ["pytorch", "z3", "cvc5", "sympy", "clifford"],
    },
    "equivariant_geometry_stack": {
        "goal": "equivariant geometry reference lane",
        "tools": ["pytorch", "clifford", "e3nn", "geomstats", "sympy"],
    },
    "graph_topology_stack": {
        "goal": "graph/hypergraph/topology reference lane",
        "tools": ["pytorch", "pyg", "rustworkx", "xgi", "toponetx", "gudhi"],
    },
    "manifold_cluster_stack": {
        "goal": "manifold + ANN + embedding + density clustering reference lane",
        "tools": ["pytorch", "datasketch", "pynndescent", "umap", "hdbscan", "sklearn"],
    },
    "manifold_search_archive_stack": {
        "goal": "search-tuned manifold + archive reference lane",
        "tools": ["pytorch", "datasketch", "pynndescent", "umap", "hdbscan", "sklearn", "optuna", "ribs"],
    },
    "search_archive_stack": {
        "goal": "optimizer/archive/search reference lane",
        "tools": ["pytorch", "optuna", "pymoo", "ribs", "deap", "evotorch"],
    },
}


def _canonical_tool(name: str) -> str:
    return IMPORT_TOOL_ALIASES.get(name.strip().lower().replace("-", "_"), name.strip().lower().replace("-", "_"))


def _results_dir() -> Path:
    return PROBES / "a2_state" / "sim_results"


def _rel_or_abs(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


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


def _blocked_surface(limit: int = 8) -> dict:
    blocked_dir = adaptive_controller.QUEUE / "blocked"
    reasons: Counter[str] = Counter()
    sim_counts: Counter[str] = Counter()
    samples = []
    if blocked_dir.exists():
        for path in sorted(blocked_dir.iterdir()):
            if not path.is_file():
                continue
            data = adaptive_controller.load_result(path)
            reason = str(data.get("blocked_reason") or data.get("reason") or "unknown")
            sim = Path(str(data.get("sim_path", ""))).name
            reasons[reason] += 1
            if sim:
                sim_counts[sim] += 1
            if len(samples) < limit:
                samples.append({
                    "file": path.name,
                    "reason": reason,
                    "sim": sim,
                    "lane": data.get("lane"),
                })
    duplicate_sims = {sim: count for sim, count in sim_counts.items() if count > 1}
    return {
        "active_count": sum(reasons.values()),
        "resolved_count": adaptive_controller.resolved_blocked_count(),
        "reasons": dict(reasons),
        "unique_sims": len(sim_counts),
        "duplicate_entries": sum(count - 1 for count in duplicate_sims.values()),
        "duplicate_sims": duplicate_sims,
        "samples": samples,
    }


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


def _claimed_age_surface(claimed_dir: Path, limit: int = 5) -> dict:
    now = time.time()
    ages: list[dict[str, object]] = []
    if claimed_dir.exists():
        for path in claimed_dir.glob("*.json.*"):
            try:
                data = adaptive_controller.load_result(path)
            except Exception:
                data = {}
            try:
                fallback_ts = path.stat().st_mtime
            except OSError:
                fallback_ts = now
            claimed_at = data.get("claimed_at") if isinstance(data, dict) else None
            ts = claimed_at if isinstance(claimed_at, (int, float)) else fallback_ts
            age = max(0.0, now - float(ts))
            ages.append({
                "file": path.name,
                "sim": Path(str(data.get("sim_path", ""))).name if isinstance(data, dict) else "",
                "age_sec": age,
            })
    ages.sort(key=lambda row: float(row["age_sec"]), reverse=True)
    return {
        "count": len(ages),
        "oldest_age_sec": ages[0]["age_sec"] if ages else None,
        "over_300s": sum(1 for row in ages if float(row["age_sec"]) >= 300),
        "over_900s": sum(1 for row in ages if float(row["age_sec"]) >= 900),
        "samples": ages[:limit],
    }


def _git_layer(path: str) -> str:
    if path.startswith("READ ONLY Legacy "):
        return "legacy_copies"
    if path.startswith("obsidian_vault/"):
        return "owner_vault"
    if path.startswith("system_v5/new docs/") or path.endswith(".md"):
        return "owner_docs"
    if (
        path.startswith("system_v4/probes/")
        and path.endswith("_results.json")
        and not path.startswith("system_v4/probes/a2_state/sim_results/")
        and not path.startswith("system_v4/probes/sim_results/")
    ):
        return "misplaced_probe_results"
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
            "misplaced_probe_results": "REPAIR_TO_CANONICAL_ROOT",
            "probe_results": "KEEP_ACTIVE",
            "system_results": "KEEP_ACTIVE",
            "owner_vault": "BLOCKED_REQUIRES_PREP",
            "owner_docs": "BLOCKED_REQUIRES_PREP",
            "legacy_copies": "MOVE_TO_QUARANTINE",
            "other": "BLOCKED_REQUIRES_PREP",
        },
    }


def _string_key(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _depth_value(node: ast.AST | None):
    if isinstance(node, ast.Constant) and (node.value is None or isinstance(node.value, str)):
        return node.value
    return None


def _module_literal(tree: ast.AST, name: str):
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                try:
                    return ast.literal_eval(node.value)
                except Exception:
                    return None
    return None


def _module_dict_keys(tree: ast.AST, name: str) -> set[str]:
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id != name:
                continue
            if isinstance(node.value, ast.Dict):
                return {
                    str(raw)
                    for raw in (
                        _string_key(key)
                        for key in node.value.keys
                    )
                    if raw is not None
                }
            literal = _module_literal(tree, name)
            if isinstance(literal, dict):
                return {str(raw) for raw in literal}
            return set()
    return set()


def _module_depth_map(tree: ast.AST, name: str, manifest_keys: set[str] | None = None) -> dict[str, object] | None:
    base: dict[str, object] | None = None
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                if isinstance(node.value, ast.Dict):
                    parsed: dict[str, object] = {}
                    for key_node, value_node in zip(node.value.keys, node.value.values):
                        key = _string_key(key_node)
                        if key is None:
                            continue
                        value = _depth_value(value_node)
                        if value is None and not (
                            isinstance(value_node, ast.Constant) and value_node.value is None
                        ):
                            continue
                        parsed[key] = value
                    base = parsed
                elif (
                    isinstance(node.value, ast.DictComp)
                    and isinstance(node.value.key, ast.Name)
                    and node.value.key.id
                    and isinstance(node.value.value, ast.Constant)
                    and node.value.value.value is None
                    and len(node.value.generators) == 1
                    and isinstance(node.value.generators[0].iter, ast.Name)
                    and node.value.generators[0].iter.id == "TOOL_MANIFEST"
                    and manifest_keys
                ):
                    base = {key: None for key in manifest_keys}
                else:
                    literal = _module_literal(tree, name)
                    base = literal if isinstance(literal, dict) else None
            elif (
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id == name
                and base is not None
            ):
                key = _string_key(target.slice)
                value = _depth_value(node.value)
                if key is not None and value is not None:
                    base[key] = value
    return base


def _imported_tools(path: Path) -> tuple[set[str], bool]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return set(), False
    tools: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                head = alias.name.split(".", 1)[0]
                tool = IMPORT_TOOL_ALIASES.get(head)
                if tool:
                    tools.add(tool)
        elif isinstance(node, ast.ImportFrom):
            if not node.module:
                continue
            head = node.module.split(".", 1)[0]
            tool = IMPORT_TOOL_ALIASES.get(head)
            if tool:
                tools.add(tool)
    return tools, True


def _capability_probe_status(tool: str) -> dict[str, object]:
    results_dir = _results_dir()
    candidates = [
        (
            PROBES / f"sim_{tool}_capability.py",
            results_dir / f"{tool}_capability_results.json",
        ),
        (
            PROBES / f"sim_capability_{tool}_isolated.py",
            results_dir / f"sim_capability_{tool}_isolated_results.json",
        ),
    ]
    probe_files = [_rel_or_abs(probe) for probe, _ in candidates if probe.exists()]
    result_files = [_rel_or_abs(result) for _, result in candidates if result.exists()]
    status = "missing"
    if probe_files:
        status = "probe_stale"
    for _probe, result in candidates:
        if not result.exists():
            continue
        try:
            data = json.loads(result.read_text(encoding="utf-8"))
        except Exception:
            status = "probe_failing"
            continue
        summary = data.get("summary") if isinstance(data, dict) else {}
        passing = (
            data.get("overall_pass") is True
            or data.get("all_pass") is True
            or (isinstance(summary, dict) and summary.get("all_pass") is True)
            or (isinstance(summary, dict) and summary.get("all_passed") is True)
            or (
                isinstance(summary, dict)
                and isinstance(summary.get("passed"), int)
                and isinstance(summary.get("total"), int)
                and summary.get("total", 0) > 0
                and summary.get("passed") == summary.get("total")
            )
        )
        status = "passing" if passing else "probe_failing"
        if passing:
            break
    return {
        "status": status,
        "probe_files": probe_files,
        "result_files": result_files,
    }


def tool_integration_surface(limit: int = 12) -> dict:
    missing_depth: Counter[str] = Counter()
    missing_manifest: Counter[str] = Counter()
    samples: list[dict[str, object]] = []
    sim_rows: list[dict[str, object]] = []
    per_tool: defaultdict[str, dict[str, object]] = defaultdict(
        lambda: {
            "imported_in_sims": 0,
            "missing_manifest": 0,
            "missing_depth": 0,
            "load_bearing_witnesses": 0,
            "supportive_witnesses": 0,
            "decorative_witnesses": 0,
            "header_declared_without_depth": 0,
            "sample_witnesses": [],
        }
    )
    parse_failures = 0
    audited = 0

    for path in sorted(PROBES.glob("sim_*.py")):
        if " 2" in path.name:
            continue
        imported_tools, parsed = _imported_tools(path)
        if not parsed:
            parse_failures += 1
            continue
        if not imported_tools:
            continue
        audited += 1
        for tool in imported_tools:
            per_tool[tool]["imported_in_sims"] = int(per_tool[tool]["imported_in_sims"]) + 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            parse_failures += 1
            continue
        manifest_tools = _module_dict_keys(tree, "TOOL_MANIFEST")
        depth = _module_depth_map(tree, "TOOL_INTEGRATION_DEPTH", manifest_tools)
        manifest = {tool: True for tool in manifest_tools} if manifest_tools else None
        depth_tools = set(depth) if isinstance(depth, dict) else set()
        load_bearing_tools = (
            {
                _canonical_tool(str(raw_tool))
                for raw_tool, level in depth.items()
                if level == "load_bearing"
            }
            if isinstance(depth, dict)
            else set()
        )
        sim_rows.append({
            "sim": path.name,
            "imported_tools": set(imported_tools),
            "manifest_tools": {_canonical_tool(str(tool)) for tool in manifest_tools},
            "depth_tools": {_canonical_tool(str(tool)) for tool in depth_tools},
            "load_bearing_tools": load_bearing_tools,
        })
        if isinstance(depth, dict):
            for raw_tool, level in depth.items():
                tool = _canonical_tool(str(raw_tool))
                row = per_tool[tool]
                if level == "load_bearing":
                    row["load_bearing_witnesses"] = int(row["load_bearing_witnesses"]) + 1
                elif level == "supportive":
                    row["supportive_witnesses"] = int(row["supportive_witnesses"]) + 1
                elif level == "decorative":
                    row["decorative_witnesses"] = int(row["decorative_witnesses"]) + 1
                elif tool in imported_tools:
                    row["header_declared_without_depth"] = int(row["header_declared_without_depth"]) + 1
                if (
                    level in {"load_bearing", "supportive", "decorative"}
                    and len(row["sample_witnesses"]) < 5
                ):
                    row["sample_witnesses"].append(path.name)
        missing_manifest_tools = sorted(
            tool for tool in imported_tools
            if not isinstance(manifest, dict) or tool not in manifest
        )
        missing_depth_tools = sorted(
            tool for tool in imported_tools
            if not isinstance(depth, dict) or tool not in depth
        )
        for tool in missing_manifest_tools:
            missing_manifest[tool] += 1
            per_tool[tool]["missing_manifest"] = int(per_tool[tool]["missing_manifest"]) + 1
        for tool in missing_depth_tools:
            missing_depth[tool] += 1
            per_tool[tool]["missing_depth"] = int(per_tool[tool]["missing_depth"]) + 1
        if (missing_manifest_tools or missing_depth_tools) and len(samples) < limit:
            samples.append({
                "sim": path.name,
                "imported_tools": sorted(imported_tools),
                "missing_manifest_tools": missing_manifest_tools,
                "missing_depth_tools": missing_depth_tools,
            })

    all_tools = sorted(
        set(per_tool)
        | {_canonical_tool(path.stem.removeprefix("sim_").removesuffix("_capability")) for path in PROBES.glob("sim_*_capability.py")}
        | {_canonical_tool(path.stem.removeprefix("sim_capability_").removesuffix("_isolated")) for path in PROBES.glob("sim_capability_*_isolated.py")}
    )
    per_tool_report: dict[str, dict[str, object]] = {}
    for tool in all_tools:
        row = dict(per_tool[tool])
        row.update(_capability_probe_status(tool))
        per_tool_report[tool] = row

    bundle_report: dict[str, dict[str, object]] = {}
    for bundle_name, spec in TOOL_BUNDLES.items():
        tools = [_canonical_tool(tool) for tool in spec["tools"]]
        tool_set = set(tools)
        deep_threshold = max(3, (2 * len(tools) + 2) // 3)
        witnesses: list[dict[str, object]] = []
        full_bundle_witness_count = 0
        deep_bundle_witness_count = 0

        for row in sim_rows:
            imported_overlap = sorted(tool_set & set(row["imported_tools"]))
            if not imported_overlap:
                continue
            manifest_overlap = sorted(tool_set & set(row["manifest_tools"]))
            depth_overlap = sorted(tool_set & set(row["depth_tools"]))
            load_bearing_overlap = sorted(tool_set & set(row["load_bearing_tools"]))
            missing_tools = sorted(tool_set - set(row["imported_tools"]))
            header_complete = tool_set.issubset(set(row["imported_tools"])) and tool_set.issubset(set(row["manifest_tools"])) and tool_set.issubset(set(row["depth_tools"]))
            deep_witness = (
                len(imported_overlap) >= deep_threshold
                and len(manifest_overlap) >= deep_threshold
                and len(depth_overlap) >= deep_threshold
            )
            if header_complete:
                full_bundle_witness_count += 1
            if deep_witness:
                deep_bundle_witness_count += 1
            witnesses.append({
                "sim": row["sim"],
                "imported_overlap_count": len(imported_overlap),
                "header_declared_overlap_count": min(len(manifest_overlap), len(depth_overlap)),
                "load_bearing_overlap_count": len(load_bearing_overlap),
                "missing_tools": missing_tools,
                "header_complete": header_complete,
                "deep_witness": deep_witness,
            })

        witnesses.sort(
            key=lambda row: (
                -int(row["imported_overlap_count"]),
                -int(row["header_declared_overlap_count"]),
                -int(row["load_bearing_overlap_count"]),
                len(row["missing_tools"]),
                str(row["sim"]),
            )
        )

        capability_gap_tools = [
            tool for tool in tools
            if per_tool_report.get(tool, {}).get("status") != "passing"
        ]
        weak_tools = [
            tool for tool in tools
            if int(per_tool_report.get(tool, {}).get("imported_in_sims", 0)) == 0
        ]
        load_bearing_gap_tools = [
            tool for tool in tools
            if int(per_tool_report.get(tool, {}).get("load_bearing_witnesses", 0)) == 0
        ]
        recommendation = (
            "repair_capability_first"
            if capability_gap_tools
            else "add_reference_sim"
            if full_bundle_witness_count == 0
            else "expand_existing_bundle"
        )
        bundle_report[bundle_name] = {
            "goal": spec["goal"],
            "tools": tools,
            "capability_gap_tools": capability_gap_tools,
            "weak_tools": weak_tools,
            "load_bearing_gap_tools": load_bearing_gap_tools,
            "deep_threshold": deep_threshold,
            "full_bundle_witness_count": full_bundle_witness_count,
            "deep_bundle_witness_count": deep_bundle_witness_count,
            "needs_reference_sim": full_bundle_witness_count == 0,
            "recommendation": recommendation,
            "best_existing_witnesses": witnesses[:limit],
        }

    return {
        "audited_sims_with_tool_imports": audited,
        "parse_failures": parse_failures,
        "missing_manifest_by_tool": dict(missing_manifest),
        "missing_depth_by_tool": dict(missing_depth),
        "per_tool": per_tool_report,
        "bundles": bundle_report,
        "samples": samples,
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


def _source_state_for_result(
    root: Path,
    result_path: Path,
    dirty_probe_sources: set[str],
    untracked_probe_sources: set[str],
) -> dict[str, object] | None:
    if root == REPO / "system_v4/a2_state/sim_results":
        return None
    if not result_path.name.endswith("_results.json"):
        return None
    stem = result_path.name[:-13]
    candidates = [PROBES / f"{stem}.py"]
    if not stem.startswith("sim_"):
        candidates.append(PROBES / f"sim_{stem}.py")
    source = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    rel_source = str(source.relative_to(REPO))
    state = {
        "source_path": rel_source,
        "source_exists": source.exists(),
        "source_canonical_name": source.name.startswith("sim_"),
        "source_dirty": rel_source in dirty_probe_sources,
        "source_untracked": rel_source in untracked_probe_sources,
        "source_newer_than_result": False,
        "result_newer_than_source": False,
    }
    if source.exists():
        try:
            source_mtime = source.stat().st_mtime
            result_mtime = result_path.stat().st_mtime
            if source_mtime > result_mtime:
                state["source_newer_than_result"] = True
            elif result_mtime > source_mtime:
                state["result_newer_than_source"] = True
        except OSError:
            pass
    return state


def _source_state_label(state: dict[str, object] | None) -> str | None:
    if state is None:
        return None
    if state["source_untracked"]:
        prefix = "source_untracked"
    elif state["source_dirty"]:
        prefix = "source_dirty"
    elif not state["source_exists"]:
        prefix = "source_missing"
    else:
        prefix = "source_clean"
    if state["source_exists"]:
        if state["source_newer_than_result"]:
            return f"{prefix}_source_newer"
        if state["result_newer_than_source"]:
            return f"{prefix}_result_newer"
    return prefix


def _fail_action_bucket(
    fail_mode: str | None,
    source_state: dict[str, object] | None,
) -> str | None:
    if source_state is None:
        return None
    if not source_state["source_exists"]:
        return "missing_source_repair"
    if not source_state["source_canonical_name"]:
        return "noncanonical_source_repair"
    if source_state["source_untracked"] or source_state["source_dirty"]:
        return "source_drift_review"
    if source_state["source_newer_than_result"]:
        return "rerun_candidate"
    if source_state["result_newer_than_source"]:
        if fail_mode == "summary_gate_false":
            return "current_fail_review"
        return "current_fail_review"
    return "fail_review"


def result_surface() -> dict:
    dirty_probe_sources, untracked_probe_sources = _dirty_probe_source_paths()
    roots = {}
    for root in RESULT_ROOTS:
        files = list(root.glob("*.json")) if root.exists() else []
        status_counts: Counter[str] = Counter()
        schema_counts: Counter[str] = Counter()
        fail_families: Counter[str] = Counter()
        fail_modes: Counter[str] = Counter()
        fail_source_states: Counter[str] = Counter()
        fail_actions: Counter[str] = Counter()
        unknown_families: Counter[str] = Counter()
        dirty_source_results = 0
        untracked_source_results = 0
        orphan_like = 0
        samples: defaultdict[str, list[str]] = defaultdict(list)
        fail_details: list[dict[str, object]] = []
        for path in files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                data = None
            pass_state = _pass_state(data)
            source_state = _source_state_for_result(root, path, dirty_probe_sources, untracked_probe_sources)
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
            source_label = _source_state_label(source_state)
            if pass_state == "fail" and source_label:
                fail_source_states[source_label] += 1
                action = _fail_action_bucket(fail_mode, source_state)
                if action:
                    fail_actions[action] += 1
                if len(fail_details) < 8:
                    fail_details.append({
                        "result": path.name,
                        "source": source_state["source_path"],
                        "fail_mode": fail_mode,
                        "source_state": source_label,
                        "action": action,
                    })
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
            if source_state is not None:
                rel_source = str(source_state["source_path"])
                if rel_source in dirty_probe_sources:
                    dirty_source_results += 1
                    if len(samples["dirty_source_results"]) < 8:
                        samples["dirty_source_results"].append(path.name)
                if rel_source in untracked_probe_sources:
                    untracked_source_results += 1
                    if len(samples["untracked_source_results"]) < 8:
                        samples["untracked_source_results"].append(path.name)
                if not source_state["source_exists"]:
                    orphan_like += 1
                    if len(samples["orphan_like"]) < 8:
                        samples["orphan_like"].append(path.name)
        roots[str(root.relative_to(REPO))] = {
            "count": len(files),
            "status": dict(status_counts),
            "schema": dict(schema_counts),
            "fail_families": dict(fail_families.most_common(10)),
            "fail_modes": dict(fail_modes.most_common(10)),
            "fail_source_states": dict(fail_source_states.most_common(10)),
            "fail_actions": dict(fail_actions.most_common(10)),
            "unknown_families": dict(unknown_families.most_common(10)),
            "dirty_source_results": dirty_source_results,
            "untracked_source_results": untracked_source_results,
            "orphan_like": orphan_like,
            "fail_details": fail_details,
            "samples": dict(samples),
        }
    return roots


def _runner_health(queue_counts: dict, freshness: dict, claimed_age: dict | None = None) -> dict:
    claimed = int(queue_counts.get("claimed", 0) or 0)
    done_fresh = freshness.get("done", {}).get("active_within_60s") is True
    claimed_fresh = freshness.get("claimed", {}).get("active_within_60s") is True
    lane_b_fresh = freshness.get("lane_B", {}).get("active_within_60s") is True
    backlog = int(queue_counts.get("lane_A", 0) or 0) + int(queue_counts.get("lane_B", 0) or 0)
    long_claims = int((claimed_age or {}).get("over_900s", 0) or 0)
    if claimed > 0 and done_fresh and long_claims > 0:
        return {"status": "draining_with_long_claims", "reason": "done surface is fresh but some claims exceed 15 minutes"}
    if claimed > 0 and not done_fresh and long_claims > 0:
        return {"status": "possibly_stuck", "reason": "claims exceed 15 minutes and done surface is stale"}
    if claimed > 0 and done_fresh:
        return {"status": "draining", "reason": "claimed and done surfaces are both fresh"}
    if claimed > 0 and not done_fresh:
        return {"status": "possibly_stuck", "reason": "claims exist but done surface is stale"}
    if claimed == 0 and backlog > 0 and lane_b_fresh:
        return {"status": "feeding", "reason": "queue is active but workers are between claims"}
    if claimed == 0 and backlog > 0:
        return {"status": "idle_with_backlog", "reason": "backlog exists without fresh claim/done movement"}
    return {"status": "idle", "reason": "no active claims and no material backlog"}


def _runner_warnings(
    queue_counts: dict,
    freshness: dict,
    claimed_age: dict | None = None,
    blocked: dict | None = None,
) -> list[str]:
    warnings: list[str] = []
    claimed = int(queue_counts.get("claimed", 0) or 0)
    blocked_state = blocked or {}
    duplicate_entries = int(blocked_state.get("duplicate_entries", 0) or 0)
    if duplicate_entries > 0:
        active_count = int(blocked_state.get("active_count", 0) or 0)
        unique_sims = int(blocked_state.get("unique_sims", 0) or 0)
        warnings.append(
            f"{active_count} blocked entry(s) across {unique_sims} unique sim(s)"
        )
    if claimed <= 0:
        return warnings
    ages = claimed_age or {}
    over_900 = int(ages.get("over_900s", 0) or 0)
    over_300 = int(ages.get("over_300s", 0) or 0)
    if over_900:
        warnings.append(f"{over_900} claim(s) over 900s")
    elif over_300:
        warnings.append(f"{over_300} claim(s) over 300s")
    if freshness.get("done", {}).get("active_within_60s") is not True:
        warnings.append("done surface not fresh within 60s")
    return warnings


def runner_surface() -> dict:
    queue_counts = adaptive_controller.queue_counts()
    freshness = {
        lane: _queue_dir_freshness(adaptive_controller.QUEUE / lane)
        for lane in ("lane_A", "lane_B", "claimed", "done")
    }
    claimed_age = _claimed_age_surface(adaptive_controller.QUEUE / "claimed")
    blocked = _blocked_surface()
    return {
        "pidfiles": {name: _pidfile_status(name, pidfile) for name, pidfile in PIDFILES.items()},
        "wrappers": _wrapper_processes(),
        "queue": queue_counts,
        "freshness": freshness,
        "claimed_age": claimed_age,
        "blocked": blocked,
        "health": _runner_health(queue_counts, freshness, claimed_age),
        "warnings": _runner_warnings(queue_counts, freshness, claimed_age, blocked),
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


def _git_maintenance_queue(git: dict) -> dict:
    cleanup_posture = git.get("cleanup_posture", {})
    layers = git.get("layers", {})
    blocked_layers = {
        key: value
        for key, value in layers.items()
        if cleanup_posture.get(key) == "BLOCKED_REQUIRES_PREP"
    }
    active_layers = {
        key: value
        for key, value in layers.items()
        if cleanup_posture.get(key) == "KEEP_ACTIVE"
    }
    repair_layers = {
        key: value
        for key, value in layers.items()
        if cleanup_posture.get(key) == "REPAIR_TO_CANONICAL_ROOT"
    }
    return {
        "blocked_entries": sum(blocked_layers.values()),
        "blocked_layers": blocked_layers,
        "repair_entries": sum(repair_layers.values()),
        "repair_layers": repair_layers,
        "active_churn_entries": sum(active_layers.values()),
        "active_churn_layers": active_layers,
    }


def _results_maintenance_queue(results: dict) -> dict:
    main = results.get("system_v4/probes/a2_state/sim_results", {})
    grouped: defaultdict[str, list[dict]] = defaultdict(list)
    for row in main.get("fail_details", []):
        action = str(row.get("action", "unclassified"))
        if len(grouped[action]) < 5:
            grouped[action].append(row)
    return {
        "fail_actions": dict(main.get("fail_actions", {})),
        "fail_action_samples": dict(grouped),
        "dirty_source_results": int(main.get("dirty_source_results", 0) or 0),
        "untracked_source_results": int(main.get("untracked_source_results", 0) or 0),
    }


def maintenance_queue_surface(git: dict, runner: dict, results: dict) -> dict:
    return {
        "git": _git_maintenance_queue(git),
        "runner": {
            "status": runner.get("health", {}).get("status"),
            "warnings": list(runner.get("warnings", [])),
            "claimed_age": dict(runner.get("claimed_age", {})),
            "blocked": {
                "active_count": int(runner.get("blocked", {}).get("active_count", 0) or 0),
                "reasons": dict(runner.get("blocked", {}).get("reasons", {})),
                "unique_sims": int(runner.get("blocked", {}).get("unique_sims", 0) or 0),
                "duplicate_entries": int(runner.get("blocked", {}).get("duplicate_entries", 0) or 0),
                "samples": list(runner.get("blocked", {}).get("samples", [])),
            },
        },
        "results": _results_maintenance_queue(results),
    }


def main() -> int:
    git = git_surface()
    runner = runner_surface()
    results = result_surface()
    report = {
        "git": git,
        "runner": runner,
        "program": program_surface(),
        "tool_integration": tool_integration_surface(),
        "results": results,
        "maintenance_queue": maintenance_queue_surface(git, runner, results),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
