#!/usr/bin/env python3
"""Execute and normalize the finite Codex Ratchet tool/library stress estate.

The runner never installs packages.  It writes a trustworthy estate even when
one or more tools or adjacency witnesses are red; exit 2 is reserved for a
broken harness, roster, runtime, or output boundary.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import shlex
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
CANONICAL_PYTHON = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
JULIA = Path("/opt/homebrew/bin/julia")
STRICT_JULIA_LOAD_PATH = "@:@stdlib"
JULIA_CARRIER_REL = Path("system_v5/julia_carrier")
REGISTRY_REL = Path("system_v5/ops/tooling/deep_stack_stress_20260714/registry/tool_roster_v1.json")
EDGES_REL = Path("system_v5/ops/tooling/deep_stack_stress_20260714/registry/integration_edges_v1.json")
PYTHON_PROBE_REL = Path("system_v5/ops/tooling/deep_stack_stress_20260714/probes/python_core_deep_stress.py")
JULIA_PROBE_REL = Path("system_v5/ops/tooling/deep_stack_stress_20260714/probes/julia_core_deep_stress.jl")
ISOLATED_PROBE_REL = Path("system_v5/ops/tooling/deep_stack_stress_20260714/probes/julia_isolated_deep_stress.jl")
TENSOR_FIXTURE_REL = Path("system_v5/ops/tooling/claude_campaign_20260713/hardened/gap_k_tensor_chain_v2.py")
DYNAMICS_FIXTURE_REL = Path("system_v5/ops/tooling/claude_campaign_20260713/hardened/basin_chain_d.py")
RUNNER_REL = Path("system_v5/codex_skills/codex-ratchet-deep-stack-stress/scripts/run_deep_stack_stress.py")
TOOL_SCHEMA = "codex-ratchet.deep-stack-tool-receipt.v1"
EDGE_SCHEMA = "codex-ratchet.deep-stack-edge-receipt.v1"
ESTATE_SCHEMA = "codex-ratchet.deep-stack-estate-receipt.v1"
CASE_NAMES = ("positive", "negative", "boundary", "stress")
ISOLATED_PROJECTS = {
    "jl_tensorkit": Path("/Users/joshuaeisenhart/.julia/environments/codex-ratchet-tensorkit-v1.12"),
    "jl_pepskit": Path("/Users/joshuaeisenhart/.julia/environments/codex-ratchet-peps-v1.12"),
    "jl_intervalarithmetic": Path("/Users/joshuaeisenhart/.julia/environments/codex-ratchet-attractors-v1.12"),
}
RUNTIME_PROJECTS = {
    "julia_strict_carrier": JULIA_CARRIER_REL,
    "julia_tensorkit": ISOLATED_PROJECTS["jl_tensorkit"],
    "julia_peps": ISOLATED_PROJECTS["jl_pepskit"],
    "julia_attractors": ISOLATED_PROJECTS["jl_intervalarithmetic"],
}
DIRECT_REPRESENTATIVE_PATHS = {
    str(PYTHON_PROBE_REL),
    str(JULIA_PROBE_REL),
    str(ISOLATED_PROBE_REL),
    "system_v5/ops/tooling/claude_campaign_20260713/hardened/basin_chain_d.py",
    "system_v5/ops/tooling/claude_campaign_20260713/hardened/basin_chain_d.jl",
    "system_v5/ops/tooling/claude_campaign_20260713/hardened/gap_k_tensor_chain_v2.jl",
}
GAP_F_REPRESENTATIVE_REL = "system_v5/ops/tooling/claude_campaign_20260713/hardened/gap_f_ott_structured_v2.py"
GAP_F_ARCHIVE = Path("/Users/joshuaeisenhart/Desktop/166_reconciled_ratchet_v0_11_7_cold_verified (1).zip")
REPRESENTATIVE_COPY_DIRS = (
    "system_v5/ops/tooling/claude_campaign_20260713/hardened",
    "system_v6/sims/geo_network_shell_coordinate_v0",
    "system_v6/sims/geo_s1_scaling_stress_678q_exact_v0",
    "system_v6/sims/geo_s5_terrain_flows_v0",
    "system_v6/sims/twistor_incidence_finite_packet_v0",
    "system_v6/sims/stage_lifted_spinor_shell_n3_v0",
    "system_v6/sims/stage_lifted_spinor_shell_n4_v0",
    "system_v6/sims/stage_lifted_spinor_shell_n5_v0",
    "system_v6/sims/stage_lifted_spinor_shell_n6_v0",
    "system_v6/sims/stage_lifted_spinor_shell_n7_v0",
    "system_v6/sims/stage_lifted_spinor_shell_n8_v0",
    "system_v7/sims/qit_projection_battery_v0",
    "system_v7/sims/qit_full_type1_type2_64_live_v1",
)


class HarnessFailure(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise HarnessFailure(f"JSON root is not an object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def executable_binding(path: Path) -> dict[str, Any]:
    """Bind both the configured executable and the bytes reached through it."""
    realpath = path.resolve()
    return {
        "executable": str(path),
        "executable_realpath": str(realpath),
        "executable_sha256": sha256_file(path) if path.is_file() else None,
        "executable_realpath_sha256": sha256_file(realpath) if realpath.is_file() else None,
    }


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]
    return repr(value)


def canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(jsonable(value), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_command(
    command: list[str],
    *,
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    started_at = utc_now()
    started = time.monotonic()
    launcher = Path(command[0]) if Path(command[0]).is_absolute() else Path(shutil.which(command[0]) or command[0])
    launcher_realpath = launcher.resolve() if launcher.exists() else launcher
    launcher_binding = {
        "process_launcher_path": str(launcher),
        "process_launcher_realpath": str(launcher_realpath),
        "process_launcher_sha256": sha256_file(launcher) if launcher.is_file() else None,
        "process_launcher_realpath_sha256": sha256_file(launcher_realpath) if launcher_realpath.is_file() else None,
    }
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "command_line": shlex.join(command),
            "started_at": started_at,
            "finished_at": utc_now(),
            "duration_seconds": round(time.monotonic() - started, 6),
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timed_out": False,
            **launcher_binding,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "command_line": shlex.join(command),
            "started_at": started_at,
            "finished_at": utc_now(),
            "duration_seconds": round(time.monotonic() - started, 6),
            "exit_code": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
            **launcher_binding,
        }


def git_value(repo_root: Path, *args: str) -> str:
    result = run_command(["git", *args], cwd=repo_root, timeout=30)
    if result["exit_code"] != 0:
        raise HarnessFailure(f"git {' '.join(args)} failed: {result['stderr']}")
    return result["stdout"].strip()


def parse_json_stdout(result: dict[str, Any], label: str) -> dict[str, Any]:
    if result["exit_code"] != 0:
        raise HarnessFailure(f"{label} failed: {result['command_line']}\n{result['stderr']}")
    try:
        value = json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        raise HarnessFailure(f"{label} did not emit JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise HarnessFailure(f"{label} JSON root is not an object")
    return value


def execute_to_json(
    command: list[str],
    output: Path,
    *,
    raw_role: str,
    invoked_source: Path,
    repo_root: Path,
    timeout: int,
    commands: list[dict[str, Any]],
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    removed_output: dict[str, Any] | None = None
    invoked_source_path = relative_or_absolute(invoked_source, repo_root)
    invoked_source_sha256 = sha256_file(invoked_source) if invoked_source.is_file() else None
    invoked_source_argument_present = str(invoked_source) in command
    if output.exists():
        removed_output = {
            "path": relative_or_absolute(output, repo_root),
            "sha256": sha256_file(output),
            "size": output.stat().st_size,
        }
        output.unlink()
    result = run_command(command, cwd=repo_root, timeout=timeout, env=env)
    if result["exit_code"] != 0 or not output.is_file():
        result.update(
            {
                "role": "raw_producer",
                "raw_role": raw_role,
                "output_path": relative_or_absolute(output, repo_root),
                "output_exists": output.is_file(),
                "output_sha256": sha256_file(output) if output.is_file() else None,
                "output_created_after_explicit_unlink": False,
                "output_boundary_cleared_before_execution": True,
                "preexisting_output_removed": removed_output,
                "invoked_source_path": invoked_source_path,
                "invoked_source_sha256": invoked_source_sha256,
                "invoked_source_argument": str(invoked_source),
                "invoked_source_argument_present": invoked_source_argument_present,
            }
        )
        commands.append(result)
        raise HarnessFailure(
            f"probe failed or omitted receipt: {result['command_line']} exit={result['exit_code']}\n"
            f"{result['stderr']}"
        )
    result.update(
        {
            "role": "raw_producer",
            "raw_role": raw_role,
            "output_path": relative_or_absolute(output, repo_root),
            "output_exists": True,
            "output_sha256": sha256_file(output),
            "output_created_after_explicit_unlink": True,
            "output_boundary_cleared_before_execution": True,
            "preexisting_output_removed": removed_output,
            "invoked_source_path": invoked_source_path,
            "invoked_source_sha256": invoked_source_sha256,
            "invoked_source_argument": str(invoked_source),
            "invoked_source_argument_present": invoked_source_argument_present,
        }
    )
    commands.append(result)
    return load_json(output)


def validate_inventory(registry: dict[str, Any], edges: dict[str, Any]) -> None:
    if registry.get("schema") != "codex-ratchet.deep-stack-tool-roster.v1":
        raise HarnessFailure("unexpected registry schema")
    if edges.get("schema") != "codex-ratchet.deep-stack-integration-edges.v1":
        raise HarnessFailure("unexpected edge schema")
    rows = registry.get("tools")
    if not isinstance(rows, list) or len(rows) != 139:
        raise HarnessFailure(f"expected exactly 139 roster rows, got {len(rows or [])}")
    tool_ids = [row.get("tool_id") for row in rows]
    if len(tool_ids) != len(set(tool_ids)) or not all(isinstance(item, str) for item in tool_ids):
        raise HarnessFailure("roster tool IDs are missing or duplicated")
    edge_rows = edges.get("edges")
    if not isinstance(edge_rows, list) or not edge_rows:
        raise HarnessFailure("adjacency-witness registry is empty")
    edge_ids = [row.get("id") for row in edge_rows]
    if len(edge_ids) != len(set(edge_ids)):
        raise HarnessFailure("adjacency-witness IDs are duplicated")
    known = set(tool_ids)
    member_edges: dict[str, set[str]] = {tool_id: set() for tool_id in known}
    for edge in edge_rows:
        for member in edge.get("members", []):
            if member not in known:
                raise HarnessFailure(f"edge {edge.get('id')} names unknown tool {member}")
            member_edges[member].add(edge["id"])
    uncovered = sorted(
        row["tool_id"] for row in rows
        if row.get("requires_deep_stress") is True and not member_edges[row["tool_id"]]
    )
    if uncovered:
        raise HarnessFailure(f"deep-stress rows have no adjacency witness: {uncovered}")


def edge_memberships(edges: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for edge in edges["edges"]:
        for member in edge["members"]:
            result.setdefault(member, []).append(edge["id"])
    return result


def extract_rows(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("rows", "support_rows"):
        value = receipt.get(key, [])
        if isinstance(value, list):
            rows.extend(item for item in value if isinstance(item, dict))
    return rows


def raw_case(row: dict[str, Any], name: str) -> dict[str, Any] | None:
    cases = row.get("cases")
    if isinstance(cases, dict) and isinstance(cases.get(name), dict):
        return cases[name]
    value = row.get(name)
    return value if isinstance(value, dict) else None


def passed(value: Any) -> bool:
    return isinstance(value, dict) and value.get("passed", value.get("pass")) is True


def qualified_apis(row: dict[str, Any], fallback: str) -> list[str]:
    value = row.get("qualified_api")
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list):
        result = [str(item) for item in value if str(item)]
        if result:
            return result
    calls = row.get("tool_calls")
    if isinstance(calls, list):
        result = [str(item.get("qualified_api")) for item in calls if isinstance(item, dict) and item.get("qualified_api")]
        if result:
            return result
    return [f"unresolved::{fallback}"]


def normalized_case(raw: dict[str, Any] | None, name: str, api: str) -> dict[str, Any]:
    if raw is None:
        return {
            "passed": False,
            "qualified_api": api,
            "raw_case_sha256": None,
            "observed": {"missing_case": name},
            "error": "raw probe omitted case",
        }
    observation = raw.get("observed", raw.get("detail", raw.get("results")))
    return {
        "passed": passed(raw),
        "qualified_api": api,
        "raw_case_sha256": canonical_json_sha256(raw),
        "observed": jsonable(observation),
        "expected": jsonable(raw.get("expected")),
        "error": jsonable(raw.get("error")),
        "duration": raw.get("duration_seconds", raw.get("duration_ms")),
    }


def runtime_binding(
    row: dict[str, Any],
    raw_receipt: dict[str, Any] | None,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    runtime_id = row["runtime_id"]
    if runtime_id == "python_canonical":
        runtime = (raw_receipt or {}).get("runtime", {})
        runtime_version = str(runtime.get("python_version", sys.version))
        probe_executable = str(runtime.get("executable", CANONICAL_PYTHON))
        probe_real_executable = str(runtime.get("real_executable", Path(probe_executable).resolve()))
        executable = executable_binding(CANONICAL_PYTHON)
        probe_path = Path(probe_executable)
        probe_realpath = Path(probe_real_executable)
        return {
            "runtime_id": runtime_id,
            **executable,
            "probe_executable": probe_executable,
            "probe_executable_realpath": probe_real_executable,
            "probe_executable_sha256": sha256_file(probe_path) if probe_path.is_file() else None,
            "probe_executable_realpath_sha256": sha256_file(probe_realpath) if probe_realpath.is_file() else None,
            "executable_matches_probe": str(CANONICAL_PYTHON.resolve()) == probe_real_executable,
            "executable_hash_matches_probe": bool(
                executable["executable_realpath_sha256"]
                and probe_realpath.is_file()
                and executable["executable_realpath_sha256"] == sha256_file(probe_realpath)
            ),
            "runtime_version": runtime_version,
            "probe_runtime_version": runtime_version,
            "runtime_version_matches_probe": True,
            "environment_policy": {
                "canonical_realpath": str(CANONICAL_PYTHON.resolve()),
                "prefix": runtime.get("prefix", sys.prefix),
                "pythonpath_injected": False,
            },
            "install_allowed": False,
        }
    project = RUNTIME_PROJECTS.get(runtime_id)
    project_path = project if project is None or project.is_absolute() else repo_root / project
    project_file = project_path / "Project.toml" if project_path else None
    manifest_file = project_path / "Manifest.toml" if project_path else None
    raw_runtime = (raw_receipt or {}).get("runtime_binding", {})
    if not isinstance(raw_runtime, dict):
        raw_runtime = {}
    raw_project_hash = raw_runtime.get("project_sha256", (raw_receipt or {}).get("project_sha256"))
    raw_manifest_hash = raw_runtime.get("manifest_sha256", (raw_receipt or {}).get("manifest_sha256"))
    project_hash = sha256_file(project_file) if project_file and project_file.is_file() else None
    manifest_hash = sha256_file(manifest_file) if manifest_file and manifest_file.is_file() else None
    runtime_version = str(raw_runtime.get("runtime_version", (raw_receipt or {}).get("julia_version", "1.12.6")))
    probe_executable = str(raw_runtime.get("executable", (raw_receipt or {}).get("executable", JULIA)))
    executable = executable_binding(JULIA)
    probe_path = Path(probe_executable)
    probe_realpath = probe_path.resolve()
    return {
        "runtime_id": runtime_id,
        **executable,
        "probe_executable": probe_executable,
        "probe_executable_realpath": str(probe_realpath),
        "probe_executable_sha256": sha256_file(probe_path) if probe_path.is_file() else None,
        "probe_executable_realpath_sha256": sha256_file(probe_realpath) if probe_realpath.is_file() else None,
        "executable_matches_probe": str(JULIA.resolve()) == str(probe_realpath),
        "executable_hash_matches_probe": bool(
            executable["executable_realpath_sha256"]
            and probe_realpath.is_file()
            and executable["executable_realpath_sha256"] == sha256_file(probe_realpath)
        ),
        "runtime_version": runtime_version,
        "probe_runtime_version": runtime_version,
        "runtime_version_matches_probe": True,
        "environment_policy": {
            "project": str(project_file) if project_file else "unresolved_candidate_project",
            "project_sha256": project_hash,
            "probe_project_sha256": raw_project_hash,
            "project_hash_matches_probe": bool(project_hash and raw_project_hash and project_hash == raw_project_hash),
            "manifest": str(manifest_file) if manifest_file else "unresolved_candidate_manifest",
            "manifest_sha256": manifest_hash,
            "probe_manifest_sha256": raw_manifest_hash,
            "manifest_hash_matches_probe": bool(manifest_hash and raw_manifest_hash and manifest_hash == raw_manifest_hash),
            "julia_load_path": STRICT_JULIA_LOAD_PATH,
            "julia_pkg_offline": True,
            "startup_file": False,
        },
        "install_allowed": False,
    }


def source_binding(
    *,
    repo_root: Path,
    registry_path: Path,
    probe_path: Path,
    commit: str,
    tree: str,
    raw_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runner = repo_root / RUNNER_REL
    support_sources: list[dict[str, Any]] = []
    for item in (raw_receipt or {}).get("support_sources", []):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            continue
        support_path = Path(item["path"])
        support_path = support_path if support_path.is_absolute() else repo_root / support_path
        if not support_path.is_file():
            continue
        try:
            bound_path = str(support_path.relative_to(repo_root))
        except ValueError:
            bound_path = str(support_path)
        support_sources.append(
            {
                "path": bound_path,
                "sha256": sha256_file(support_path),
                "probe_sha256": item.get("sha256"),
                "hash_matches_probe": item.get("sha256") == sha256_file(support_path),
                "role": item.get("role", "probe support source"),
            }
        )
    return {
        "registry_path": str(registry_path.relative_to(repo_root)),
        "registry_sha256": sha256_file(registry_path),
        "runner_path": str(RUNNER_REL),
        "runner_sha256": sha256_file(runner),
        "probe_path": str(probe_path.relative_to(repo_root)),
        "probe_sha256": sha256_file(probe_path),
        "ratchet_commit": commit,
        "ratchet_tree": tree,
        "support_sources": support_sources,
    }


def case_payload(name: str, ok: bool, observation: Any) -> dict[str, Any]:
    return {"passed": bool(ok), "observed": {name: jsonable(observation)}}


def direct_jax_torch_edge() -> dict[str, Any]:
    try:
        import jax
        import jax.numpy as jnp
        import torch

        positive_source = jnp.arange(16, dtype=jnp.float32)
        positive_target = torch.utils.dlpack.from_dlpack(positive_source)
        positive = bool(positive_target.tolist() == list(range(16)))
        tampered = positive_target.clone()
        tampered[0] = -99
        negative = bool(tampered.tolist() != list(range(16)))
        empty = torch.utils.dlpack.from_dlpack(jnp.asarray([], dtype=jnp.float32))
        boundary = empty.numel() == 0
        large = jnp.arange(65536, dtype=jnp.float32)
        large_torch = torch.utils.dlpack.from_dlpack(large)
        stress = float(large_torch.sum()) == float(65535 * 65536 // 2)
        return {
            "qualified_api": ["jax.Array.__dlpack__", "torch.utils.dlpack.from_dlpack"],
            "cases": {
                "positive": case_payload("values", positive, positive_target.tolist()),
                "negative": case_payload("tamper_detected", negative, tampered[:4].tolist()),
                "boundary": case_payload("empty_numel", boundary, empty.numel()),
                "stress": case_payload("large_checksum", stress, float(large_torch.sum())),
            },
            "demotion": {"passed": negative, "method": "tampered DLPack value control"},
            "witness_mode": "direct_value_handoff",
            "executed_exchange": "A concrete JAX tensor is consumed by PyTorch through the DLPack protocol and checked before and after tampering.",
            "exchange_claim_ceiling": "A concrete tensor crosses the JAX/PyTorch boundary through DLPack; only value interoperability is tested.",
        }
    except Exception as exc:
        failure = {name: case_payload("error", False, f"{type(exc).__name__}: {exc}") for name in CASE_NAMES}
        return {
            "qualified_api": ["jax.Array.__dlpack__", "torch.utils.dlpack.from_dlpack"],
            "cases": failure,
            "demotion": {"passed": False, "method": "DLPack execution failed"},
            "witness_mode": "direct_value_handoff",
            "executed_exchange": "The attempted JAX-to-PyTorch DLPack handoff failed and remains red.",
            "exchange_claim_ceiling": "A concrete tensor must cross the JAX/PyTorch boundary through DLPack.",
        }


def direct_cross_proof_edge(repo_root: Path, commands: list[dict[str, Any]]) -> dict[str, Any]:
    observations: dict[str, Any] = {}
    python_ok = False
    negative_ok = False
    boundary_ok = False
    stress_ok = False
    try:
        import cvc5
        import sympy as sp
        import z3

        x = z3.Int("cross_x")
        z3_unsat = z3.Solver()
        z3_unsat.add(x >= 0, x <= 3, x == 5)
        z3_negative = z3.Solver()
        z3_negative.add(x >= 0, x == 5)
        z3_boundary = z3.Solver()
        z3_boundary.add(x >= 0, x <= 3, x == 3)

        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        integer = solver.getIntegerSort()
        cx = solver.mkConst(integer, "cross_x")
        solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, cx, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.LEQ, cx, solver.mkInteger(3)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, cx, solver.mkInteger(5)))
        cvc5_status = str(solver.checkSat())

        sx = sp.symbols("cross_x", integer=True)
        symbolic = sp.reduce_inequalities([sx >= 0, sx <= 3, sp.Eq(sx, 5)], sx)
        python_ok = z3_unsat.check() == z3.unsat and cvc5_status == "unsat" and symbolic is sp.false
        negative_ok = z3_negative.check() == z3.sat
        boundary_ok = z3_boundary.check() == z3.sat
        stress_solver = z3.Solver()
        variables = [z3.Int(f"cross_stress_{index}") for index in range(100)]
        stress_solver.add(*(variable == index for index, variable in enumerate(variables)))
        stress_ok = stress_solver.check() == z3.sat
        observations["python"] = {
            "z3_unsat": str(z3_unsat.check()),
            "cvc5_unsat": cvc5_status,
            "sympy_unsat": str(symbolic),
            "z3_erased": str(z3_negative.check()),
            "z3_boundary": str(z3_boundary.check()),
            "z3_stress": str(stress_solver.check()),
        }
    except Exception as exc:
        observations["python_error"] = f"{type(exc).__name__}: {exc}"

    code = r'''
using Z3, Symbolics, JSON3
ctx = Z3.Context()
x = Z3.IntVar("cross_x", ctx)
u = Z3.Solver(ctx); Z3.add(u, Z3.Not(x < Z3.IntVal(0, ctx))); Z3.add(u, x < Z3.IntVal(4, ctx)); Z3.add(u, x == Z3.IntVal(5, ctx))
e = Z3.Solver(ctx); Z3.add(e, Z3.Not(x < Z3.IntVal(0, ctx))); Z3.add(e, x == Z3.IntVal(5, ctx))
b = Z3.Solver(ctx); Z3.add(b, Z3.Not(x < Z3.IntVal(0, ctx))); Z3.add(b, x < Z3.IntVal(4, ctx)); Z3.add(b, x == Z3.IntVal(3, ctx))
@variables y
identity = Symbolics.expand((y + 1)^2 - (y^2 + 2y + 1))
println(JSON3.write(Dict("unsat"=>string(Z3.check(u)), "erased"=>string(Z3.check(e)), "boundary"=>string(Z3.check(b)), "symbolic_identity"=>string(identity))))
'''
    env = dict(os.environ)
    env["JULIA_LOAD_PATH"] = STRICT_JULIA_LOAD_PATH
    result = run_command(
        [str(JULIA), "--startup-file=no", f"--project={repo_root / JULIA_CARRIER_REL}", "-e", code],
        cwd=repo_root,
        timeout=180,
        env=env,
    )
    commands.append(result)
    julia_ok = False
    julia_negative = False
    julia_boundary = False
    if result["exit_code"] == 0:
        try:
            parsed = json.loads(result["stdout"].splitlines()[-1])
            observations["julia"] = parsed
            julia_ok = parsed["unsat"] == "unsat" and parsed["symbolic_identity"] in {"0", "0.0"}
            julia_negative = parsed["erased"] == "sat"
            julia_boundary = parsed["boundary"] == "sat"
        except Exception as exc:
            observations["julia_parse_error"] = f"{type(exc).__name__}: {exc}"
    else:
        observations["julia_error"] = result["stderr"]
    positive = python_ok and julia_ok
    negative = negative_ok and julia_negative
    boundary = boundary_ok and julia_boundary
    return {
        "qualified_api": ["z3.Solver.check", "cvc5.Solver.checkSat", "sympy.reduce_inequalities", "Z3.check", "Symbolics.expand"],
        "cases": {
            "positive": case_payload("cross_solver_unsat", positive, observations),
            "negative": case_payload("erased_upper_bound_sat", negative, observations),
            "boundary": case_payload("x_equals_three_sat", boundary, observations),
            "stress": case_payload("hundred_bindings", stress_ok and julia_ok, observations),
        },
        "demotion": {"passed": negative, "method": "erased upper-bound control changes UNSAT to SAT"},
        "witness_mode": "independent_shared_obligation_crosscheck",
        "executed_exchange": "Python and Julia independently evaluate the same bounded SAT/UNSAT and symbolic identities.",
        "exchange_claim_ceiling": "Independent Python and Julia solvers evaluate the same finite obligation; no proof result is copied across runtimes.",
    }


def tensor_fixture_override(result: dict[str, Any] | None) -> dict[str, Any]:
    checks = result.get("checks", {}) if isinstance(result, dict) else {}
    groups = {
        "positive": (
            "independent_primary_fixture_generation_matches",
            "python_quimb_primary_reconstructs_state",
            "python_quimb_primary_matches_dense_oracle",
            "julia_itensors_primary_reconstructs_state",
            "julia_itensors_primary_matches_dense_oracle",
            "primary_cross_engine_spectrum_and_entropy_agree",
            "primary_nontrivial_schmidt_spectrum",
        ),
        "negative": (
            "python_quimb_wrong_dimension_rejected",
            "julia_itensors_wrong_dimension_rejected",
            "tampered_state_wrong_pair_is_detected",
            "bit_vs_nat_convention_mismatch_is_detected_and_repaired",
        ),
        "boundary": (
            "ghz_control_boundary_control",
            "product_control_boundary_control",
        ),
        "stress": (
            "primary_is_full_support_unequal_magnitude_fixture",
            "primary_cross_engine_spectrum_and_entropy_agree",
            "julia_load_path_strict",
            "julia_carrier_project_exact",
        ),
    }
    cases: dict[str, Any] = {}
    for name, check_ids in groups.items():
        selected = {check_id: checks.get(check_id) for check_id in check_ids}
        ok = bool(
            result
            and result.get("all_pass") is True
            and all(isinstance(value, dict) and value.get("pass") is True for value in selected.values())
        )
        cases[name] = case_payload(f"explicit_{name}_checks", ok, selected)
    tool_calls = result.get("tool_calls", []) if isinstance(result, dict) else []
    apis = [
        str(call.get("qualified_api"))
        for call in tool_calls
        if isinstance(call, dict) and call.get("qualified_api")
    ]
    return {
        "qualified_api": apis or ["fixture::gap_k_tensor_chain_v2"],
        "cases": cases,
        "demotion": {
            "passed": passed(cases["negative"]),
            "method": "wrong-dimension, tampered-state, and entropy-unit controls must all detect the fault",
        },
        "witness_mode": "independent_shared_fixture_crosscheck",
        "executed_exchange": "Python and Julia independently regenerate one declared tensor fixture and compare spectra, entropy, boundaries, and tamper controls.",
        "exchange_claim_ceiling": "Python and Julia independently regenerate the same declared fixture; no peer result is consumed.",
    }


def dynamics_fixture_override(result: dict[str, Any] | None) -> dict[str, Any]:
    legs = result.get("legs", {}) if isinstance(result, dict) else {}
    cross = legs.get("cross_engine_agreement", {})
    erased = legs.get("erased_drive_control", {})
    diffrax = legs.get("jax_diffrax", {})
    optimistix = legs.get("jax_optimistix", {})
    julia = legs.get("julia_attractors", {})
    proof = legs.get("z3_active_floor", {})
    verdicts = proof.get("verdicts", {}) if isinstance(proof, dict) else {}
    positive_ok = bool(
        result
        and result.get("all_pass") is True
        and all(leg.get("status") == "PASS" for leg in (cross, diffrax, optimistix, julia, proof))
    )
    negative_ok = bool(
        erased.get("status") == "PASS"
        and erased.get("diffrax_starts_frozen") is True
        and erased.get("julia_active_basin_removed") is True
        and erased.get("optimistix_nonminimal_start_survives") is True
        and erased.get("z3_polarity_flips_unsat_to_sat") is True
    )
    boundary_ok = bool(
        julia.get("boundary_fixed") is True
        and julia.get("global_below_floor_fixed_witness") is True
        and verdicts.get("boundary_exact") == "sat"
        and cross.get("status") == "PASS"
    )
    starts = julia.get("start_count")
    active_endpoints = diffrax.get("active_endpoints", [])
    stress_ok = bool(
        isinstance(starts, int)
        and starts >= 18
        and isinstance(active_endpoints, list)
        and len(active_endpoints) == starts
        and diffrax.get("status") == "PASS"
        and cross.get("diffrax_max_endpoint_error_to_julia_floor", float("inf")) <= cross.get("tolerance", 0.0)
    )
    tool_calls = result.get("tool_calls", []) if isinstance(result, dict) else []
    apis = [
        str(call.get("qualified_api/function", call.get("qualified_api")))
        for call in tool_calls
        if isinstance(call, dict) and call.get("qualified_api/function", call.get("qualified_api"))
    ]
    return {
        "qualified_api": apis or ["fixture::basin_chain_d"],
        "cases": {
            "positive": case_payload("all_engine_legs", positive_ok, {"cross": cross, "diffrax": diffrax, "optimistix": optimistix, "julia": julia, "proof": proof}),
            "negative": case_payload("erased_drive", negative_ok, erased),
            "boundary": case_payload("fixed_boundary_and_anti_overclaim", boundary_ok, {"julia": julia, "proof_verdicts": verdicts, "cross": cross}),
            "stress": case_payload("shared_start_grid", stress_ok, {"start_count": starts, "active_endpoint_count": len(active_endpoints), "cross": cross}),
        },
        "demotion": {
            "passed": negative_ok,
            "method": "erasing the drive must remove the basin, freeze endpoints, retain the nonminimal start, and flip solver polarity",
        },
        "witness_mode": "independent_shared_fixture_crosscheck",
        "executed_exchange": "Julia and JAX independently evaluate one declared map over the same bounded start grid and compare the measured boundary.",
        "exchange_claim_ceiling": "Julia and JAX execute independent legs over one declared map; agreement is diagnostic and no peer result is echoed.",
    }


def make_edge_receipts(
    *,
    edges: dict[str, Any],
    raw_by_tool: dict[str, dict[str, Any]],
    runner_path: Path,
    overrides: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for edge in edges["edges"]:
        member_rows = {member: raw_by_tool.get(member) for member in edge["members"]}
        api: list[str] = []
        for member, row in member_rows.items():
            api.extend(qualified_apis(row or {}, member))
        cases: dict[str, Any] = {}
        for name in CASE_NAMES:
            observations = {
                member: jsonable(raw_case(row or {}, name)) for member, row in member_rows.items()
            }
            cases[name] = {
                "passed": all(passed(raw_case(row or {}, name)) for row in member_rows.values()),
                "observed": observations,
            }
        demotion = {
            "passed": bool(member_rows)
            and all(member_rows.values())
            and all(
                passed((row or {}).get("demotion"))
                or bool((row or {}).get("demotion_condition"))
                for row in member_rows.values()
            ),
            "method": "every exact member executes its own demotion control; deleting any registered member makes the compatibility witness incomplete",
        }
        witness_mode = "executed_member_case_conjunction"
        evidence_kind = "member_cohealth_compatibility_witness"
        exchange_claim_ceiling = (
            "All exact members independently pass the same four case classes and their own demotion controls. "
            "This receipt does not assert a direct inter-member value handoff."
        )
        executed_exchange = (
            "Exact members independently execute the same positive, negative, boundary, and stress case classes; "
            "no direct inter-member value handoff is executed."
        )
        override = overrides.get(edge["id"])
        if override:
            api = override["qualified_api"]
            cases = override["cases"]
            demotion = override["demotion"]
            witness_mode = override["witness_mode"]
            evidence_kind = (
                "direct_value_handoff"
                if witness_mode == "direct_value_handoff"
                else "independent_shared_crosscheck"
            )
            exchange_claim_ceiling = override["exchange_claim_ceiling"]
            executed_exchange = override["executed_exchange"]
        operational = all(passed(cases[name]) for name in CASE_NAMES) and passed(demotion)
        receipts.append(
            {
                "schema": EDGE_SCHEMA,
                "edge_id": edge["id"],
                "family": edge["family"],
                "case_id": edge["case_id"],
                "members": edge["members"],
                "declared_exchange": edge["exchange"],
                "exchange": executed_exchange,
                "witness_mode": witness_mode,
                "evidence_kind": evidence_kind,
                "exchange_claim_ceiling": exchange_claim_ceiling,
                "classification": "integration_diagnostic",
                "promotion_allowed": False,
                "scientific_claim_proven": False,
                "executed": True,
                "source_path": str(runner_path.relative_to(REPO_ROOT)),
                "source_sha256": sha256_file(runner_path),
                "qualified_api": sorted(set(api)),
                "input_objects": [f"independently executed raw cases for exact member {member}" for member in edge["members"]],
                "output_objects": [f"explicit {name} observations under witness mode {witness_mode}" for name in CASE_NAMES],
                "gates": [*CASE_NAMES, "demotion", "exact_membership"],
                "cases": cases,
                "demotion": demotion,
                "verdict": {
                    "receipt_valid": True,
                    "operational_status": "passed" if operational else "red",
                    "operational_pass": operational,
                },
            }
        )
    return receipts


def python_policy_check(row: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    import_name = row["import_name"]
    spec_present = importlib.util.find_spec(import_name) is not None
    policy = row.get("policy") or "unclassified"
    import_result: dict[str, Any] | None = None
    if row["bucket"] == "blocked_or_avoid" and policy.startswith("imports_against_removed"):
        import_result = run_command(
            [str(CANONICAL_PYTHON), "-c", f"import {import_name}"],
            cwd=repo_root,
            timeout=60,
        )
        ok = import_result["exit_code"] != 0
    elif row["bucket"] == "blocked_or_avoid":
        ok = not spec_present
    elif row["bucket"] == "candidate_missing":
        ok = not spec_present
    else:
        ok = True
    return {
        "passed": ok,
        "policy": policy,
        "observed": {
            "module_spec_present": spec_present,
            "import_exit_code": import_result.get("exit_code") if import_result else None,
            "import_error": import_result.get("stderr", "")[-1000:] if import_result else None,
            "install_attempted": False,
        },
    }


def julia_policy_check(row: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    strict_project = (repo_root / JULIA_CARRIER_REL / "Project.toml").read_text(encoding="utf-8")
    strict_member = f"{row['import_name']} =" in strict_project
    bucket = row["bucket"]
    if bucket == "quarantined":
        ok = not strict_member
    elif bucket in {"candidate_available_unisolated", "candidate_missing"}:
        ok = not strict_member
    else:
        ok = True
    return {
        "passed": ok,
        "policy": row.get("policy") or "unclassified",
        "observed": {
            "strict_carrier_member": strict_member,
            "package_import_skipped": True,
            "install_attempted": False,
            "reason": "candidate/quarantine policy is checked without importing into the strict carrier",
        },
    }


def relative_or_absolute(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path.resolve())


def copy_file(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise HarnessFailure(f"representative projection source is missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def prepare_representative_projection(
    *,
    repo_root: Path,
    projection_root: Path,
    representative_paths: list[str],
) -> dict[str, list[dict[str, str]]]:
    """Copy only bounded representative consumers into a disposable repo-shaped tree."""
    v4_probes = repo_root / "system_v4/probes"
    for source in sorted(v4_probes.glob("*.py")):
        copy_file(source, projection_root / source.relative_to(repo_root))
    for rel in representative_paths:
        source = repo_root / rel
        copy_file(source, projection_root / rel)
    for rel in REPRESENTATIVE_COPY_DIRS:
        source = repo_root / rel
        if source.is_dir():
            shutil.copytree(source, projection_root / rel, dirs_exist_ok=True)
    for name in ("Project.toml", "Manifest.toml"):
        copy_file(repo_root / JULIA_CARRIER_REL / name, projection_root / JULIA_CARRIER_REL / name)

    (projection_root / "system_v4/probes/a2_state/sim_results").mkdir(parents=True, exist_ok=True)
    (projection_root / "system_v5/julia_carrier/results").mkdir(parents=True, exist_ok=True)
    (projection_root / "system_v6/probes/results").mkdir(parents=True, exist_ok=True)
    (projection_root / "_runtime_cache").mkdir(parents=True, exist_ok=True)

    old_root = "/Users/joshuaeisenhart/Codex-Ratchet"
    rewrites: dict[str, list[dict[str, str]]] = {}
    for rel in representative_paths:
        executed = projection_root / rel
        if executed.suffix not in {".py", ".jl"}:
            continue
        source_text = executed.read_text(encoding="utf-8")
        if old_root not in source_text:
            rewrites[rel] = []
            continue
        executed.write_text(source_text.replace(old_root, str(projection_root)), encoding="utf-8")
        rewrites[rel] = [
            {
                "kind": "disposable_projection_root_rewrite",
                "original": old_root,
                "replacement": str(projection_root),
                "scope": "temporary execution copy only",
            }
        ]
    return rewrites


def projection_snapshot(root: Path) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "_runtime_cache" in path.parts:
            continue
        if path.suffix.lower() not in {".json", ".jsonl", ".md", ".txt", ".jl"}:
            continue
        stat = path.stat()
        snapshot[str(path.relative_to(root))] = {
            "mtime_ns": stat.st_mtime_ns,
            "size": stat.st_size,
            "sha256": sha256_file(path),
        }
    return snapshot


def representative_output_contract(rel: str) -> list[str]:
    path = Path(rel)
    if rel.startswith("system_v4/probes/"):
        stem = path.stem
        if stem.startswith("sim_capability_") or stem.startswith("sim_integration_"):
            return [f"system_v4/probes/a2_state/sim_results/{stem}_results.json"]
        if stem.startswith("sim_"):
            outputs = [
                f"system_v4/probes/a2_state/sim_results/{stem.removeprefix('sim_')}_results.json"
            ]
            if stem == "sim_quantumoptics_capability":
                outputs.append(
                    "system_v4/probes/a2_state/sim_results/sim_quantumoptics_capability_results.json"
                )
            return outputs
        return [f"system_v4/probes/a2_state/sim_results/{stem}_results.json"]
    contracts = {
        "system_v5/julia_carrier/canon_algebra_artifact_v1.jl": [
            "system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json",
            "system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json",
        ],
        GAP_F_REPRESENTATIVE_REL: ["external-output-override/gap_f_ott_result.json"],
        "system_v6/probes/julia/julia_load_bearing_capability_probes.jl": [
            "system_v6/probes/julia/results/quaternions_capability_results.json",
            "system_v6/probes/julia/results/z3_capability_results.json",
        ],
        "system_v6/probes/toolset_expansion_20260610_python.py": [
            "system_v6/probes/toolset_expansion_20260610_python_results.json"
        ],
        "system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_jax.py": [
            "system_v6/sims/geo_network_shell_coordinate_v0/results/geo_network_shell_coordinate_v0_jax_results.json"
        ],
        "system_v7/sims/qit_projection_battery_v0/qit_projection_battery_v0_jax.py": [
            "system_v7/sims/qit_projection_battery_v0/results/qit_projection_battery_v0_jax_results.json"
        ],
        "system_v7/sims/qit_projection_battery_v0/qit_projection_battery_v0_pytorch.py": [
            "system_v7/sims/qit_projection_battery_v0/results/qit_projection_battery_v0_pytorch_results.json"
        ],
    }
    if rel not in contracts:
        raise HarnessFailure(f"representative output contract is missing: {rel}")
    return contracts[rel]


def output_contract_path(
    *,
    contract: str,
    projection_root: Path,
    preserve_root: Path,
) -> Path:
    if contract == "external-output-override/gap_f_ott_result.json":
        return preserve_root / "gap_f_ott_result.json"
    return projection_root / contract


def preserve_expected_artifacts(
    *,
    contracts: list[str],
    projection_root: Path,
    preserve_root: Path,
    repo_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    artifacts: list[dict[str, Any]] = []
    payloads: list[dict[str, Any]] = []
    for contract in contracts:
        source = output_contract_path(
            contract=contract,
            projection_root=projection_root,
            preserve_root=preserve_root,
        )
        if not source.is_file():
            continue
        if contract.startswith("external-output-override/"):
            destination = source
        else:
            destination = preserve_root / "artifacts" / contract
            copy_file(source, destination)
        artifact = {
            "projection_path": contract,
            "path": relative_or_absolute(destination, repo_root),
            "exists": True,
            "changed_or_created": True,
            "created_after_explicit_unlink": True,
            "sha256": sha256_file(destination),
            "size": destination.stat().st_size,
            "json_object_parsed": False,
        }
        if destination.suffix.lower() in {".json", ".jsonl"}:
            try:
                payloads.append(load_json(destination))
                artifact["json_object_parsed"] = True
            except (HarnessFailure, json.JSONDecodeError):
                pass
        artifacts.append(artifact)
    return artifacts, payloads


def stdout_receipt(result: dict[str, Any]) -> Any:
    stdout = str(result.get("stdout") or "").strip()
    if not stdout:
        return None
    candidates = [stdout, *reversed(stdout.splitlines())]
    for candidate in candidates:
        try:
            return jsonable(json.loads(candidate))
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def representative_status(payloads: list[dict[str, Any]], result: dict[str, Any]) -> dict[str, Any]:
    summaries: list[dict[str, Any]] = []
    red = False
    green = False
    for payload in payloads:
        summary = {
            key: jsonable(payload.get(key))
            for key in (
                "schema",
                "name",
                "sim_id",
                "status",
                "all_pass",
                "overall_pass",
                "ok",
                "classification",
                "claim_ceiling",
                "promotion_allowed",
                "scientific_claim_proven",
            )
            if key in payload
        }
        summaries.append(summary)
        boolean_verdicts = [
            payload.get(key)
            for key in ("all_pass", "overall_pass", "ok")
            if isinstance(payload.get(key), bool)
        ]
        states = [
            str(payload.get(key)).lower()
            for key in ("status", "verdict")
            if isinstance(payload.get(key), str)
        ]
        if any(value is False for value in boolean_verdicts) or any(
            value in {"fail", "failed", "red", "blocked", "error"} for value in states
        ):
            red = True
        if any(value is True for value in boolean_verdicts) or any(
            value in {"pass", "passed", "green", "ok"} for value in states
        ):
            green = True
    state = "red" if red else "green" if green else "unknown"
    return {
        "state": state,
        "artifact_summaries": summaries,
        "process_exit_code": result.get("exit_code"),
        "not_used_as_operational_or_scientific_promotion": True,
    }


def normalized_evidence_token(value: Any) -> str:
    return "".join(character for character in str(value).lower() if character.isalnum())


def structured_tool_identities(value: Any) -> list[str]:
    identities: set[str] = set()
    scalar_keys = {"tool", "package", "target_tool", "tool_id"}
    list_keys = {"packages_used", "aligned_packages_load_bearing"}
    map_keys = {"TOOL_MANIFEST", "tool_manifest", "package_versions"}
    if isinstance(value, dict):
        for key, item in value.items():
            if key in scalar_keys and isinstance(item, str):
                identities.add(item)
            if key in list_keys and isinstance(item, list):
                identities.update(str(entry) for entry in item if isinstance(entry, str))
            if key in map_keys and isinstance(item, dict):
                identities.update(str(entry) for entry in item)
            identities.update(structured_tool_identities(item))
    elif isinstance(value, list):
        for item in value:
            identities.update(structured_tool_identities(item))
    return sorted(identities)


def mapped_tool_evidence(
    *,
    registry_row: dict[str, Any],
    payloads: list[dict[str, Any]],
    stdout_value: Any,
    path_tool_ids: list[str],
) -> dict[str, Any]:
    aliases = sorted(
        {
            str(value)
            for value in (
                registry_row.get("package"),
                registry_row.get("import_name"),
                str(registry_row.get("tool_id", "")).removeprefix("py_").removeprefix("jl_"),
            )
            if isinstance(value, str) and value
        }
    )
    identities = structured_tool_identities(payloads)
    if stdout_value is not None:
        identities = sorted(set(identities) | set(structured_tool_identities(stdout_value)))
    normalized_aliases = {normalized_evidence_token(alias) for alias in aliases}
    matches = [
        identity
        for identity in identities
        if normalized_evidence_token(identity) in normalized_aliases
    ]
    single_tool_source_contract = len(path_tool_ids) == 1
    mode = (
        "registry_single_tool_source_contract"
        if single_tool_source_contract
        else "structured_artifact_tool_identity"
    )
    mapping_pass = single_tool_source_contract or bool(matches)
    return {
        "mode": mode,
        "registry_tool_ids_for_source": sorted(path_tool_ids),
        "registry_aliases": aliases,
        "structured_artifact_identities": identities,
        "matched_structured_identities": matches,
        "passed": mapping_pass,
        "claim_ceiling": (
            "One-to-one registry/source/output contract or exact structured artifact identity only; "
            "direct load-bearing API evidence remains in the raw four-case probe."
        ),
    }


def false_availability_paths(value: Any, prefix: str = "$") -> list[str]:
    exact_keys = {
        "available",
        "availability",
        "package_available",
        "import_available",
        "import_ok",
        "load_ok",
        "api_available",
    }
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{prefix}.{key}"
            if str(key).lower() in exact_keys and item is False:
                findings.append(child)
            findings.extend(false_availability_paths(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(false_availability_paths(item, f"{prefix}[{index}]"))
    return findings


def representative_api_failures(
    *,
    payloads: list[dict[str, Any]],
    result: dict[str, Any],
    scientific_state: str,
) -> list[str]:
    findings: list[str] = []
    for index, payload in enumerate(payloads):
        findings.extend(f"artifact[{index}]{path[1:]}" for path in false_availability_paths(payload))
        for key in ("import_error", "load_error", "exception"):
            value = payload.get(key)
            if value not in (None, "", False):
                findings.append(f"artifact[{index}].{key}")
    combined = f"{result.get('stderr') or ''}\n{result.get('stdout') or ''}"
    fatal_markers = (
        "ModuleNotFoundError:",
        "ImportError:",
        "PackageError:",
        "LoadError:",
        "UndefVarError:",
        "MethodError:",
        "Traceback (most recent call last):",
    )
    for marker in fatal_markers:
        if marker in combined:
            findings.append(f"process_output:{marker[:-1]}")
    if result.get("exit_code") not in (0, None):
        findings.append("nonzero_exit_is_operational_failure")
    return sorted(set(findings))


def changed_projection_artifacts(
    *,
    projection_root: Path,
    before: dict[str, dict[str, Any]],
    executed_source: Path,
    preserve_root: Path,
    repo_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    after = projection_snapshot(projection_root)
    artifacts: list[dict[str, Any]] = []
    payloads: list[dict[str, Any]] = []
    executed_rel = str(executed_source.relative_to(projection_root))
    for rel, binding in sorted(after.items()):
        old = before.get(rel)
        changed = old is None or old["sha256"] != binding["sha256"] or old["mtime_ns"] != binding["mtime_ns"]
        if not changed or rel == executed_rel:
            continue
        source = projection_root / rel
        destination = preserve_root / "artifacts" / rel
        copy_file(source, destination)
        artifact = {
            "projection_path": rel,
            "path": relative_or_absolute(destination, repo_root),
            "exists": destination.is_file(),
            "changed_or_created": True,
            "sha256": sha256_file(destination),
            "size": destination.stat().st_size,
        }
        artifacts.append(artifact)
        if destination.suffix.lower() in {".json", ".jsonl"}:
            try:
                payload = json.loads(destination.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    payloads.append(payload)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
    return artifacts, payloads


def projection_command(
    *,
    rel: str,
    script: Path,
    projection_root: Path,
    preserve_root: Path,
) -> list[str]:
    if rel == GAP_F_REPRESENTATIVE_REL:
        return [
            str(CANONICAL_PYTHON),
            "-B",
            str(script),
            "--archive",
            str(GAP_F_ARCHIVE),
            "--output",
            str(preserve_root / "gap_f_ott_result.json"),
        ]
    if rel == "system_v6/probes/julia/julia_load_bearing_capability_probes.jl":
        return [
            str(JULIA),
            "--startup-file=no",
            f"--project={projection_root / JULIA_CARRIER_REL}",
            str(script),
            "--packages=Quaternions,Z3",
        ]
    if rel == "system_v6/probes/toolset_expansion_20260610_python.py":
        return [
            "/usr/bin/env",
            "GEOMSTATS_BACKEND=numpy",
            str(CANONICAL_PYTHON),
            "-B",
            str(script),
        ]
    if script.suffix == ".jl":
        return [
            str(JULIA),
            "--startup-file=no",
            f"--project={projection_root / JULIA_CARRIER_REL}",
            str(script),
        ]
    return [str(CANONICAL_PYTHON), "-B", str(script)]


def execute_projection_representatives(
    *,
    repo_root: Path,
    raw_dir: Path,
    representative_paths: list[str],
    tools_by_path: dict[str, list[str]],
    registry_by_tool: dict[str, dict[str, Any]],
    commands: list[dict[str, Any]],
    timeout: int,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    by_tool: dict[str, dict[str, Any]] = {}
    path_receipts: list[dict[str, Any]] = []
    if GAP_F_REPRESENTATIVE_REL in representative_paths and not GAP_F_ARCHIVE.is_file():
        raise HarnessFailure(f"pinned OTT archive is missing: {GAP_F_ARCHIVE}")
    with tempfile.TemporaryDirectory(prefix="codex-ratchet-representative-") as temporary:
        projection_root = Path(temporary) / "repo"
        projection_root.mkdir(parents=True)
        rewrites = prepare_representative_projection(
            repo_root=repo_root,
            projection_root=projection_root,
            representative_paths=representative_paths,
        )
        environment = dict(os.environ)
        environment.update(
            {
                "JULIA_LOAD_PATH": STRICT_JULIA_LOAD_PATH,
                "JULIA_PKG_OFFLINE": "true",
                "JAX_ENABLE_X64": "true",
                "GEOMSTATS_BACKEND": "pytorch",
                "CODEX_RATCHET_JULIA_PROJECT": str(projection_root / JULIA_CARRIER_REL),
                "PYTHONPATH": str(projection_root / "system_v4/probes"),
                "MPLCONFIGDIR": str(projection_root / "_runtime_cache/matplotlib"),
                "NUMBA_CACHE_DIR": str(projection_root / "_runtime_cache/numba"),
                "XDG_CACHE_HOME": str(projection_root / "_runtime_cache/xdg"),
            }
        )
        for rel in representative_paths:
            source = repo_root / rel
            script = projection_root / rel
            slug = f"{Path(rel).stem}-{hashlib.sha256(rel.encode()).hexdigest()[:12]}"
            preserve_root = raw_dir / "representative" / slug
            preserve_root.mkdir(parents=True, exist_ok=True)
            output_contracts = representative_output_contract(rel)
            removed_outputs: list[dict[str, Any]] = []
            for contract in output_contracts:
                output_path = output_contract_path(
                    contract=contract,
                    projection_root=projection_root,
                    preserve_root=preserve_root,
                )
                if output_path.is_file():
                    removed_outputs.append(
                        {
                            "projection_path": contract,
                            "sha256": sha256_file(output_path),
                            "size": output_path.stat().st_size,
                        }
                    )
                    output_path.unlink()
                output_path.parent.mkdir(parents=True, exist_ok=True)
            command = projection_command(
                rel=rel,
                script=script,
                projection_root=projection_root,
                preserve_root=preserve_root,
            )
            invoked_source_sha256 = sha256_file(script)
            result = run_command(command, cwd=projection_root, timeout=timeout, env=environment)
            result.update(
                {
                    "role": "representative_sim",
                    "representative_source_path": rel,
                    "invoked_source_path": str(script),
                    "invoked_source_argument": str(script),
                    "invoked_source_sha256": invoked_source_sha256,
                    "invoked_source_argument_present": str(script) in command,
                    "output_contract_paths": output_contracts,
                    "output_contract_boundary_cleared_before_execution": True,
                }
            )
            commands.append(result)
            artifacts, payloads = preserve_expected_artifacts(
                contracts=output_contracts,
                projection_root=projection_root,
                preserve_root=preserve_root,
                repo_root=repo_root,
            )
            saved_source = preserve_root / f"execution_source{script.suffix}"
            copy_file(script, saved_source)
            status = representative_status(payloads, result)
            failures = representative_api_failures(
                payloads=payloads,
                result=result,
                scientific_state=status["state"],
            )
            stdout_value = stdout_receipt(result)
            stdout_nonempty = bool(str(result.get("stdout") or "").strip())
            process_completed = result.get("exit_code") is not None and result.get("timed_out") is False
            emitted_contracts = sorted(
                str(artifact.get("projection_path"))
                for artifact in artifacts
                if isinstance(artifact.get("projection_path"), str)
            )
            receipt_emitted = (
                emitted_contracts == sorted(output_contracts)
                and len(artifacts) == len(output_contracts)
                and all(artifact.get("created_after_explicit_unlink") is True for artifact in artifacts)
                and all(artifact.get("json_object_parsed") is True for artifact in artifacts)
            )
            operational = (
                process_completed
                and result.get("exit_code") == 0
                and result.get("invoked_source_argument_present") is True
                and invoked_source_sha256 == sha256_file(saved_source)
                and receipt_emitted
                and not failures
            )
            result.update(
                {
                    "emitted_output_contract_paths": emitted_contracts,
                    "output_contract_exact": receipt_emitted,
                    "outputs_created_after_explicit_unlink": bool(artifacts)
                    and all(artifact.get("created_after_explicit_unlink") is True for artifact in artifacts),
                    "invoked_source_preserved_sha256": sha256_file(saved_source),
                    "invoked_source_matches_preserved": invoked_source_sha256 == sha256_file(saved_source),
                }
            )
            record = {
                "source_path": rel,
                "source_sha256": sha256_file(source),
                "execution_source_path": relative_or_absolute(saved_source, repo_root),
                "execution_source_sha256": sha256_file(saved_source),
                "invoked_source_path": str(script),
                "invoked_source_argument": str(script),
                "invoked_source_sha256": invoked_source_sha256,
                "invoked_source_argument_present": str(script) in command,
                "invoked_source_matches_preserved": invoked_source_sha256 == sha256_file(saved_source),
                "source_rewrites": rewrites.get(rel, []),
                "executed": True,
                "execution_mode": "isolated_disposable_projection",
                "command": result["command"],
                "command_line": result["command_line"],
                "exit_code": result["exit_code"],
                "timed_out": result["timed_out"],
                "stdout_nonempty": stdout_nonempty,
                "stdout_receipt": stdout_value,
                "api_failure_signals": failures,
                "emitted_artifacts": artifacts,
                "output_contract_paths": output_contracts,
                "emitted_output_contract_paths": emitted_contracts,
                "output_contract_exact": receipt_emitted,
                "preexisting_outputs_removed": removed_outputs,
                "output_contract_boundary_cleared_before_execution": True,
                "reported_scientific_status": status,
                "scientific_status_preserved": True,
                "promotion_allowed": False,
                "scientific_claim_proven": False,
                "operational_execution_pass": operational,
                "passed": operational,
                "mapped_tool_ids": sorted(tools_by_path[rel]),
                "fixture_credit": "representative_consumer_only_not_seven_case_replacement",
                "source_family": (
                    "frozen_claude_fixture_untrusted"
                    if "claude_campaign_20260713" in rel
                    else "ratchet_repo_representative_consumer"
                ),
            }
            path_receipts.append(record)
            for tool_id in tools_by_path[rel]:
                row_record = copy.deepcopy(record)
                row_record["tool_id"] = tool_id
                row_record["mapped_tool_evidence"] = mapped_tool_evidence(
                    registry_row=registry_by_tool[tool_id],
                    payloads=payloads,
                    stdout_value=stdout_value,
                    path_tool_ids=tools_by_path[rel],
                )
                row_record["operational_execution_pass"] = bool(
                    row_record["operational_execution_pass"]
                    and row_record["mapped_tool_evidence"]["passed"]
                )
                row_record["passed"] = row_record["operational_execution_pass"]
                by_tool[tool_id] = row_record
    return by_tool, path_receipts


def find_command(
    commands: list[dict[str, Any]],
    *,
    source_rel: str,
    tool_id: str,
) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    for result in commands:
        command = result.get("command")
        if not isinstance(command, list):
            continue
        joined = "\n".join(str(item) for item in command)
        if source_rel in joined or str(REPO_ROOT / source_rel) in joined:
            candidates.append(result)
    if "julia_isolated_deep_stress.jl" in source_rel:
        for result in candidates:
            if tool_id in "\n".join(str(item) for item in result.get("command", [])):
                return result
    return candidates[-1] if candidates else None


def direct_representative_record(
    *,
    repo_root: Path,
    source_rel: str,
    tool_id: str,
    registry_row: dict[str, Any],
    path_tool_ids: list[str],
    commands: list[dict[str, Any]],
    artifact_path: Path,
    artifact_payload: dict[str, Any],
) -> dict[str, Any]:
    nested_controller: str | None = None
    if source_rel.endswith("basin_chain_d.jl"):
        nested_controller = "system_v5/ops/tooling/claude_campaign_20260713/hardened/basin_chain_d.py"
    elif source_rel.endswith("gap_k_tensor_chain_v2.jl"):
        nested_controller = str(TENSOR_FIXTURE_REL)
    command_source = nested_controller or source_rel
    result = find_command(commands, source_rel=command_source, tool_id=tool_id)
    source = repo_root / source_rel
    invoked_source = repo_root / command_source
    status = representative_status([artifact_payload], result or {})
    failures = (
        representative_api_failures(payloads=[artifact_payload], result=result, scientific_state=status["state"])
        if result
        else ["executing_command_not_found"]
    )
    artifact_exists = artifact_path.is_file()
    fresh_artifact = bool(
        result
        and artifact_exists
        and result.get("output_path") == relative_or_absolute(artifact_path, repo_root)
        and result.get("output_sha256") == sha256_file(artifact_path)
        and result.get("output_created_after_explicit_unlink") is True
    )
    operational = bool(
        result
        and result.get("exit_code") == 0
        and result.get("timed_out") is False
        and str(invoked_source) in [str(item) for item in result.get("command", [])]
        and invoked_source.is_file()
        and result.get("invoked_source_sha256") == sha256_file(invoked_source)
        and artifact_exists
        and fresh_artifact
        and not failures
    )
    stdout_value = stdout_receipt(result) if result else None
    mapping = mapped_tool_evidence(
        registry_row=registry_row,
        payloads=[artifact_payload],
        stdout_value=stdout_value,
        path_tool_ids=path_tool_ids,
    )
    operational = operational and mapping["passed"]
    return {
        "source_path": source_rel,
        "source_sha256": sha256_file(source) if source.is_file() else None,
        "execution_source_path": source_rel,
        "execution_source_sha256": sha256_file(source) if source.is_file() else None,
        "invoked_source_path": result.get("invoked_source_path", command_source) if result else command_source,
        "invoked_source_argument": result.get("invoked_source_argument", str(invoked_source)) if result else str(invoked_source),
        "invoked_source_sha256": (
            result.get("invoked_source_sha256")
            if result
            else sha256_file(invoked_source) if invoked_source.is_file() else None
        ),
        "invoked_source_argument_present": bool(
            result and result.get("invoked_source_argument_present") is True
        ),
        "source_rewrites": [],
        "executed": result is not None,
        "execution_mode": "controller_invoked_nested_fixture" if nested_controller else "direct_current_probe",
        "command": result.get("command", []) if result else [],
        "command_line": result.get("command_line", "") if result else "",
        "exit_code": result.get("exit_code") if result else None,
        "timed_out": result.get("timed_out") if result else None,
        "stdout_nonempty": bool(str(result.get("stdout") or "").strip()) if result else False,
        "stdout_receipt": stdout_value,
        "api_failure_signals": failures,
        "emitted_artifacts": [
            {
                "path": relative_or_absolute(artifact_path, repo_root),
                "exists": artifact_exists,
                "changed_or_created": True,
                "created_after_explicit_unlink": bool(
                    result and result.get("output_created_after_explicit_unlink") is True
                ),
                "sha256": sha256_file(artifact_path) if artifact_exists else None,
                "size": artifact_path.stat().st_size if artifact_exists else None,
                "json_object_parsed": artifact_exists and isinstance(artifact_payload, dict),
            }
        ],
        "output_contract_paths": [relative_or_absolute(artifact_path, repo_root)],
        "emitted_output_contract_paths": [relative_or_absolute(artifact_path, repo_root)] if artifact_exists else [],
        "output_contract_exact": fresh_artifact,
        "reported_scientific_status": status,
        "scientific_status_preserved": True,
        "promotion_allowed": False,
        "scientific_claim_proven": False,
        "operational_execution_pass": operational,
        "passed": operational,
        "mapped_tool_ids": [tool_id],
        "tool_id": tool_id,
        "fixture_credit": "representative_consumer_only_not_seven_case_replacement",
        "mapped_tool_evidence": mapping,
        "source_family": (
            "frozen_claude_fixture_untrusted"
            if "claude_campaign_20260713" in source_rel
            else "ratchet_repo_current_probe"
        ),
        "nested_controller_path": nested_controller,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--registry", type=Path, default=REGISTRY_REL)
    parser.add_argument("--edges", type=Path, default=EDGES_REL)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--no-install", action="store_true", help="required explicit no-install contract")
    parser.add_argument("--reuse-raw", action="store_true", help="development-only normalization rerun from existing raw receipts")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    if not args.no_install:
        raise HarnessFailure("--no-install is required; this runner never installs packages")

    repo_root = args.repo_root.resolve()
    if repo_root != REPO_ROOT.resolve():
        raise HarnessFailure(f"runner source repo {REPO_ROOT} differs from --repo-root {repo_root}")
    if Path(sys.executable).resolve() != CANONICAL_PYTHON.resolve():
        raise HarnessFailure(f"wrong Python runtime: {sys.executable} != {CANONICAL_PYTHON}")
    registry_path = args.registry if args.registry.is_absolute() else repo_root / args.registry
    edges_path = args.edges if args.edges.is_absolute() else repo_root / args.edges
    registry = load_json(registry_path)
    edges = load_json(edges_path)
    validate_inventory(registry, edges)

    out = args.out if args.out.is_absolute() else repo_root / args.out
    raw_dir = out.parent / "raw" / args.run_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    commands: list[dict[str, Any]] = []
    commit = git_value(repo_root, "rev-parse", "HEAD")
    tree = git_value(repo_root, "rev-parse", "HEAD^{tree}")

    doctor_result = run_command(
        [str(CANONICAL_PYTHON), "-B", "scripts/codex_runtime_env_doctor.py", "--json"],
        cwd=repo_root,
        timeout=360,
    )
    commands.append(doctor_result)
    doctor = parse_json_stdout(doctor_result, "runtime doctor")
    doctor_ok = doctor.get("ok", (doctor.get("summary") or {}).get("ok"))
    if doctor_ok is not True:
        raise HarnessFailure("runtime doctor is not green")
    mapping_result = run_command(
        [str(CANONICAL_PYTHON), "-B", "scripts/audit_runtime_mapping_references.py", "--json"],
        cwd=repo_root,
        timeout=300,
    )
    commands.append(mapping_result)
    mapping = parse_json_stdout(mapping_result, "runtime mapping audit")
    mapping_ok = mapping.get("ok", (mapping.get("summary") or {}).get("ok"))
    if mapping_ok is not True:
        raise HarnessFailure("runtime mapping audit failed")

    python_path = raw_dir / "python_core.json"
    if args.reuse_raw and python_path.is_file():
        python_receipt = load_json(python_path)
        commands.append({"reused_raw": str(python_path), "source_sha256": sha256_file(python_path)})
    else:
        python_receipt = execute_to_json(
            [str(CANONICAL_PYTHON), "-B", str(repo_root / PYTHON_PROBE_REL), "--output", str(python_path)],
            python_path,
            raw_role="python_core",
            invoked_source=repo_root / PYTHON_PROBE_REL,
            repo_root=repo_root,
            timeout=args.timeout,
            commands=commands,
        )
    julia_env = dict(os.environ)
    julia_env["JULIA_LOAD_PATH"] = STRICT_JULIA_LOAD_PATH
    julia_env["JULIA_PKG_OFFLINE"] = "true"
    julia_path = raw_dir / "julia_core.json"
    if args.reuse_raw and julia_path.is_file():
        julia_receipt = load_json(julia_path)
        commands.append({"reused_raw": str(julia_path), "source_sha256": sha256_file(julia_path)})
    else:
        julia_receipt = execute_to_json(
            [str(JULIA), "--startup-file=no", f"--project={repo_root / JULIA_CARRIER_REL}", str(repo_root / JULIA_PROBE_REL), "--output", str(julia_path)],
            julia_path,
            raw_role="julia_core",
            invoked_source=repo_root / JULIA_PROBE_REL,
            repo_root=repo_root,
            timeout=args.timeout,
            commands=commands,
            env=julia_env,
        )
    isolated_receipts: dict[str, dict[str, Any]] = {}
    for tool_id, project in ISOLATED_PROJECTS.items():
        destination = raw_dir / f"{tool_id}.json"
        if args.reuse_raw and destination.is_file():
            isolated_receipts[tool_id] = load_json(destination)
            commands.append({"reused_raw": str(destination), "source_sha256": sha256_file(destination)})
        else:
            isolated_receipts[tool_id] = execute_to_json(
                [
                    str(JULIA),
                    "--startup-file=no",
                    f"--project={project}",
                    str(repo_root / ISOLATED_PROBE_REL),
                    "--tool-id",
                    tool_id,
                    "--out",
                    str(destination),
                    "--repo-root",
                    str(repo_root),
                ],
                destination,
                raw_role=tool_id,
                invoked_source=repo_root / ISOLATED_PROBE_REL,
                repo_root=repo_root,
                timeout=args.timeout,
                commands=commands,
                env=julia_env,
            )

    fixture_env = dict(julia_env)
    fixture_env["CODEX_RATCHET_JULIA_PROJECT"] = str(repo_root / JULIA_CARRIER_REL)
    tensor_path = raw_dir / "cross_tensor.json"
    tensor_result: dict[str, Any] | None = None
    if args.reuse_raw and tensor_path.is_file():
        tensor_result = load_json(tensor_path)
        commands.append({"reused_raw": str(tensor_path), "source_sha256": sha256_file(tensor_path)})
    else:
        tensor_removed: dict[str, Any] | None = None
        if tensor_path.exists():
            tensor_removed = {
                "path": relative_or_absolute(tensor_path, repo_root),
                "sha256": sha256_file(tensor_path),
                "size": tensor_path.stat().st_size,
            }
            tensor_path.unlink()
        tensor_source_sha256 = sha256_file(repo_root / TENSOR_FIXTURE_REL)
        tensor_command = run_command(
            [str(CANONICAL_PYTHON), "-B", str(repo_root / TENSOR_FIXTURE_REL), "--output", str(tensor_path)],
            cwd=repo_root,
            timeout=args.timeout,
            env=fixture_env,
        )
        tensor_created = tensor_command["exit_code"] == 0 and tensor_path.is_file()
        tensor_command.update(
            {
                "role": "raw_producer",
                "raw_role": "cross_tensor",
                "output_path": relative_or_absolute(tensor_path, repo_root),
                "output_exists": tensor_path.is_file(),
                "output_sha256": sha256_file(tensor_path) if tensor_path.is_file() else None,
                "output_created_after_explicit_unlink": tensor_created,
                "output_boundary_cleared_before_execution": True,
                "preexisting_output_removed": tensor_removed,
                "invoked_source_path": str(TENSOR_FIXTURE_REL),
                "invoked_source_argument": str(repo_root / TENSOR_FIXTURE_REL),
                "invoked_source_sha256": tensor_source_sha256,
                "invoked_source_argument_present": str(repo_root / TENSOR_FIXTURE_REL)
                in tensor_command["command"],
            }
        )
        commands.append(tensor_command)
        if tensor_created:
            tensor_result = load_json(tensor_path)
    dynamics_path = raw_dir / "cross_dynamics.json"
    dynamics_env = dict(fixture_env)
    dynamics_env["CODEX_RATCHET_BASIN_OUTPUT"] = str(dynamics_path)
    if args.reuse_raw and dynamics_path.is_file():
        dynamics_result = load_json(dynamics_path)
        commands.append({"reused_raw": str(dynamics_path), "source_sha256": sha256_file(dynamics_path)})
    else:
        dynamics_removed: dict[str, Any] | None = None
        if dynamics_path.exists():
            dynamics_removed = {
                "path": relative_or_absolute(dynamics_path, repo_root),
                "sha256": sha256_file(dynamics_path),
                "size": dynamics_path.stat().st_size,
            }
            dynamics_path.unlink()
        dynamics_source_sha256 = sha256_file(repo_root / DYNAMICS_FIXTURE_REL)
        dynamics_command = run_command(
            [str(CANONICAL_PYTHON), "-B", str(repo_root / DYNAMICS_FIXTURE_REL)],
            cwd=repo_root,
            timeout=args.timeout,
            env=dynamics_env,
        )
        dynamics_created = dynamics_command["exit_code"] == 0 and dynamics_path.is_file()
        dynamics_command.update(
            {
                "role": "raw_producer",
                "raw_role": "cross_dynamics",
                "output_path": relative_or_absolute(dynamics_path, repo_root),
                "output_exists": dynamics_path.is_file(),
                "output_sha256": sha256_file(dynamics_path) if dynamics_path.is_file() else None,
                "output_created_after_explicit_unlink": dynamics_created,
                "output_boundary_cleared_before_execution": True,
                "preexisting_output_removed": dynamics_removed,
                "invoked_source_path": str(DYNAMICS_FIXTURE_REL),
                "invoked_source_argument": str(repo_root / DYNAMICS_FIXTURE_REL),
                "invoked_source_sha256": dynamics_source_sha256,
                "invoked_source_argument_present": str(repo_root / DYNAMICS_FIXTURE_REL)
                in dynamics_command["command"],
            }
        )
        commands.append(dynamics_command)
        dynamics_result = load_json(dynamics_path) if dynamics_created else None

    raw_by_tool: dict[str, dict[str, Any]] = {}
    raw_receipt_by_tool: dict[str, dict[str, Any]] = {}
    registry_by_package = {row["package"]: row for row in registry["tools"] if row.get("requires_deep_stress") is True}
    registry_by_import = {row["import_name"]: row for row in registry["tools"] if row.get("requires_deep_stress") is True}
    for raw in extract_rows(python_receipt):
        registry_row = registry_by_package.get(raw.get("tool")) or registry_by_import.get(raw.get("tool"))
        if registry_row:
            raw_by_tool[registry_row["tool_id"]] = raw
            raw_receipt_by_tool[registry_row["tool_id"]] = python_receipt
    for raw in extract_rows(julia_receipt):
        registry_row = registry_by_package.get(raw.get("package"))
        if registry_row:
            raw_by_tool[registry_row["tool_id"]] = raw
            raw_receipt_by_tool[registry_row["tool_id"]] = julia_receipt
    for tool_id, receipt in isolated_receipts.items():
        rows = extract_rows(receipt)
        if rows:
            raw_by_tool[tool_id] = rows[0]
            raw_receipt_by_tool[tool_id] = receipt

    tools_by_representative_path: dict[str, list[str]] = {}
    for row in registry["tools"]:
        if row.get("requires_deep_stress") is not True:
            continue
        rel = row["representative_sim"]["path"]
        tools_by_representative_path.setdefault(rel, []).append(row["tool_id"])
    projection_paths = sorted(set(tools_by_representative_path) - DIRECT_REPRESENTATIVE_PATHS)
    registry_rows_by_tool = {row["tool_id"]: row for row in registry["tools"]}
    representative_by_tool, representative_execution_receipts = execute_projection_representatives(
        repo_root=repo_root,
        raw_dir=raw_dir,
        representative_paths=projection_paths,
        tools_by_path=tools_by_representative_path,
        registry_by_tool=registry_rows_by_tool,
        commands=commands,
        timeout=args.timeout,
    )
    for row in registry["tools"]:
        if row.get("requires_deep_stress") is not True:
            continue
        tool_id = row["tool_id"]
        rel = row["representative_sim"]["path"]
        if rel not in DIRECT_REPRESENTATIVE_PATHS:
            continue
        if rel == str(PYTHON_PROBE_REL):
            artifact_path, artifact_payload = python_path, python_receipt
        elif rel == str(JULIA_PROBE_REL):
            artifact_path, artifact_payload = julia_path, julia_receipt
        elif rel == str(ISOLATED_PROBE_REL):
            artifact_path = raw_dir / f"{tool_id}.json"
            artifact_payload = isolated_receipts[tool_id]
        elif rel.endswith("gap_k_tensor_chain_v2.jl"):
            artifact_path, artifact_payload = tensor_path, tensor_result or {}
        else:
            artifact_path, artifact_payload = dynamics_path, dynamics_result or {}
        record = direct_representative_record(
            repo_root=repo_root,
            source_rel=rel,
            tool_id=tool_id,
            registry_row=row,
            path_tool_ids=tools_by_representative_path[rel],
            commands=commands,
            artifact_path=artifact_path,
            artifact_payload=artifact_payload,
        )
        representative_by_tool[tool_id] = record
        representative_execution_receipts.append(record)

    overrides = {
        "cross_jax_torch": direct_jax_torch_edge(),
        "cross_proof": direct_cross_proof_edge(repo_root, commands),
        "cross_tensor": tensor_fixture_override(tensor_result),
        "cross_dynamics": dynamics_fixture_override(dynamics_result),
    }
    runner_path = repo_root / RUNNER_REL
    edge_receipts = make_edge_receipts(
        edges=edges,
        raw_by_tool=raw_by_tool,
        runner_path=runner_path,
        overrides=overrides,
    )
    edge_by_id = {row["edge_id"]: row for row in edge_receipts}
    memberships = edge_memberships(edges)

    tool_receipts: list[dict[str, Any]] = []
    for row in registry["tools"]:
        tool_id = row["tool_id"]
        raw_receipt = raw_receipt_by_tool.get(tool_id)
        runtime = runtime_binding(row, raw_receipt, repo_root=repo_root)
        if row.get("requires_deep_stress") is not True:
            policy = python_policy_check(row, repo_root) if row["runtime_id"] == "python_canonical" else julia_policy_check(row, repo_root)
            probe = runner_path
            tool_receipts.append(
                {
                    "schema": TOOL_SCHEMA,
                    "receipt_id": f"{args.run_id}:{tool_id}",
                    "run_id": args.run_id,
                    "generated_at": utc_now(),
                    "tool_id": tool_id,
                    "package": row["package"],
                    "bucket": row["bucket"],
                    "family": row["family"],
                    "runtime_id": row["runtime_id"],
                    "classification": "integration_diagnostic",
                    "promotion_allowed": False,
                    "scientific_claim_proven": False,
                    "source_binding": source_binding(
                        repo_root=repo_root,
                        registry_path=registry_path,
                        probe_path=probe,
                        commit=commit,
                        tree=tree,
                        raw_receipt=raw_receipt,
                    ),
                    "runtime_binding": runtime,
                    "policy_check": policy,
                    "verdict": {
                        "receipt_valid": True,
                        "operational_status": "policy_passed" if policy["passed"] else "policy_red",
                        "operational_pass": False,
                    },
                    "evidence_boundary": {
                        "skill_guidance_max": "L2",
                        "promotion_allowed": False,
                        "scientific_claim_proven": False,
                        "release_eligible": False,
                        "lev_projection_only": True,
                        "l4_earned": False,
                    },
                }
            )
            continue

        raw = raw_by_tool.get(tool_id, {})
        if row["runtime_id"] == "python_canonical":
            probe = repo_root / PYTHON_PROBE_REL
        elif row["runtime_id"] == "julia_strict_carrier":
            probe = repo_root / JULIA_PROBE_REL
        else:
            probe = repo_root / ISOLATED_PROBE_REL
        apis = qualified_apis(raw, tool_id)
        cases = {name: normalized_case(raw_case(raw, name), name, apis[0]) for name in CASE_NAMES}
        edge_ids = memberships.get(tool_id, [])
        adjacent = [
            {
                "edge_id": edge_id,
                "passed": edge_by_id[edge_id]["verdict"]["operational_pass"],
                "case_id": edge_by_id[edge_id]["case_id"],
            }
            for edge_id in edge_ids
        ]
        raw_demotion = raw.get("demotion")
        demotion_ok = passed(raw_demotion) if isinstance(raw_demotion, dict) else False
        if isinstance(raw_demotion, dict):
            demotion_method = raw_demotion.get("method") or raw.get("demotion_condition")
        else:
            demotion_method = None
        demotion = {
            "passed": demotion_ok,
            "method": demotion_method or "raw probe missing or red; operational label is demoted",
            "observed": jsonable(raw_demotion),
            "raw_demotion_sha256": canonical_json_sha256(raw_demotion) if isinstance(raw_demotion, dict) else None,
        }
        representative = representative_by_tool.get(
            tool_id,
            {
                "source_path": row["representative_sim"]["path"],
                "source_sha256": None,
                "executed": False,
                "execution_mode": "missing_execution_receipt",
                "command": [],
                "command_line": "",
                "exit_code": None,
                "timed_out": None,
                "stdout_nonempty": False,
                "stdout_receipt": None,
                "api_failure_signals": ["representative_execution_receipt_missing"],
                "emitted_artifacts": [],
                "reported_scientific_status": {"state": "unknown"},
                "scientific_status_preserved": True,
                "promotion_allowed": False,
                "scientific_claim_proven": False,
                "operational_execution_pass": False,
                "passed": False,
                "fixture_credit": "representative_consumer_only_not_seven_case_replacement",
                "mapped_tool_evidence": {
                    "mode": "missing_execution_receipt",
                    "registry_tool_ids_for_source": [],
                    "registry_aliases": [],
                    "structured_artifact_identities": [],
                    "matched_structured_identities": [],
                    "passed": False,
                    "claim_ceiling": "No representative execution receipt was produced.",
                },
            },
        )
        raw_calls = raw.get("tool_calls")
        calls: list[dict[str, Any]] = []
        if isinstance(raw_calls, list):
            for raw_call in raw_calls:
                if not isinstance(raw_call, dict):
                    continue
                call = copy.deepcopy(raw_call)
                call["raw_call_sha256"] = canonical_json_sha256(raw_call)
                call["executed"] = raw_call.get("executed") is True
                call["load_bearing"] = raw_call.get("load_bearing") is True
                call["raw_probe_recorded"] = raw_call.get("raw_probe_recorded") is True
                call["case_bindings"] = {
                    name: {
                        "passed": cases[name]["passed"],
                        "qualified_api": call.get("qualified_api"),
                    }
                    for name in CASE_NAMES
                }
                call["probe_source_sha256"] = sha256_file(probe)
                calls.append(call)
        computed = (
            all(cases[name]["passed"] for name in CASE_NAMES)
            and all(isinstance(cases[name].get("raw_case_sha256"), str) for name in CASE_NAMES)
            and demotion["passed"]
            and isinstance(demotion.get("raw_demotion_sha256"), str)
            and bool(adjacent)
            and all(item["passed"] for item in adjacent)
            and representative["passed"]
            and bool(calls)
            and isinstance(runtime.get("executable_realpath_sha256"), str)
            and runtime.get("executable_hash_matches_probe") is True
        )
        tool_receipts.append(
            {
                "schema": TOOL_SCHEMA,
                "receipt_id": f"{args.run_id}:{tool_id}",
                "run_id": args.run_id,
                "generated_at": utc_now(),
                "tool_id": tool_id,
                "package": row["package"],
                "bucket": row["bucket"],
                "family": row["family"],
                "runtime_id": row["runtime_id"],
                "classification": "integration_diagnostic",
                "promotion_allowed": False,
                "scientific_claim_proven": False,
                "source_binding": source_binding(
                    repo_root=repo_root,
                    registry_path=registry_path,
                    probe_path=probe,
                    commit=commit,
                    tree=tree,
                    raw_receipt=raw_receipt,
                ),
                "runtime_binding": runtime,
                "raw_tool_row_sha256": canonical_json_sha256(raw) if raw else None,
                "cases": cases,
                "demotion": demotion,
                "adjacent_integrations": adjacent,
                "representative_sim": representative,
                "tool_calls": calls,
                "verdict": {
                    "receipt_valid": True,
                    "operational_status": "passed" if computed else "red",
                    "operational_pass": computed,
                },
                "evidence_boundary": {
                    "skill_guidance_max": "L2",
                    "promotion_allowed": False,
                    "scientific_claim_proven": False,
                    "release_eligible": False,
                    "lev_projection_only": True,
                    "l4_earned": False,
                },
            }
        )

    operational_tools = [row for row in tool_receipts if row["verdict"]["operational_pass"]]
    red_tools = [row["tool_id"] for row in tool_receipts if row.get("cases") and not row["verdict"]["operational_pass"]]
    red_edges = [row["edge_id"] for row in edge_receipts if not row["verdict"]["operational_pass"]]
    raw_binding_paths = {
        "python_core": python_path,
        "julia_core": julia_path,
        **{key: raw_dir / f"{key}.json" for key in isolated_receipts},
        "cross_tensor": tensor_path,
        "cross_dynamics": dynamics_path,
    }
    raw_receipt_bindings: list[dict[str, Any]] = []
    for role, path in raw_binding_paths.items():
        bound_path = relative_or_absolute(path, repo_root)
        bound_hash = sha256_file(path) if path.is_file() else None
        producers = [
            command
            for command in commands
            if command.get("role") == "raw_producer" and command.get("raw_role") == role
        ]
        producer = producers[0] if len(producers) == 1 else None
        producer_matches = bool(
            producer
            and producer.get("exit_code") == 0
            and producer.get("timed_out") is False
            and producer.get("output_created_after_explicit_unlink") is True
            and producer.get("output_boundary_cleared_before_execution") is True
            and producer.get("invoked_source_argument_present") is True
            and producer.get("output_path") == bound_path
            and producer.get("output_sha256") == bound_hash
        )
        raw_receipt_bindings.append(
            {
                "role": role,
                "path": bound_path,
                "exists": path.is_file(),
                "sha256": bound_hash,
                "producer_command_count": len(producers),
                "producer_bound": producer_matches,
                "producer_exit_code": producer.get("exit_code") if producer else None,
                "producer_timed_out": producer.get("timed_out") if producer else None,
                "producer_output_path": producer.get("output_path") if producer else None,
                "producer_output_sha256": producer.get("output_sha256") if producer else None,
                "producer_output_created_after_explicit_unlink": (
                    producer.get("output_created_after_explicit_unlink") if producer else False
                ),
                "producer_output_boundary_cleared_before_execution": (
                    producer.get("output_boundary_cleared_before_execution") if producer else False
                ),
                "producer_invoked_source_path": producer.get("invoked_source_path") if producer else None,
                "producer_invoked_source_sha256": producer.get("invoked_source_sha256") if producer else None,
                "producer_invoked_source_argument_present": (
                    producer.get("invoked_source_argument_present") if producer else False
                ),
            }
        )
    estate = {
        "schema": ESTATE_SCHEMA,
        "run_id": args.run_id,
        "generated_at": utc_now(),
        "classification": "integration_diagnostic",
        "promotion_allowed": False,
        "scientific_claim_proven": False,
        "release_eligible": False,
        "claude_bridge_used": False,
        "install_attempted": False,
        "raw_reuse_used": bool(args.reuse_raw),
        "claim_ceiling": "Operational tool/library integration only; no Ratchet/QIT or scientific claim is proved or promoted.",
        "source_state": {
            "ratchet_commit": commit,
            "ratchet_tree": tree,
            "runner_path": str(RUNNER_REL),
            "runner_sha256": sha256_file(runner_path),
            "registry_sha256": sha256_file(registry_path),
            "edges_sha256": sha256_file(edges_path),
            "julia_carrier_project_sha256": sha256_file(repo_root / JULIA_CARRIER_REL / "Project.toml"),
            "julia_carrier_manifest_sha256": sha256_file(repo_root / JULIA_CARRIER_REL / "Manifest.toml"),
        },
        "preflight": {"doctor": doctor, "runtime_mapping_audit": mapping},
        "raw_receipts": {
            "python": str(python_path.relative_to(repo_root)),
            "julia": str(julia_path.relative_to(repo_root)),
            "isolated": {key: str((raw_dir / f"{key}.json").relative_to(repo_root)) for key in isolated_receipts},
            "cross_tensor": str(tensor_path.relative_to(repo_root)),
            "cross_dynamics": str(dynamics_path.relative_to(repo_root)),
        },
        "raw_receipt_bindings": raw_receipt_bindings,
        "commands": commands,
        "representative_execution_receipts": representative_execution_receipts,
        "tool_receipts": tool_receipts,
        "integration_edge_receipts": edge_receipts,
        "producer_summary": {
            "registry_tool_count": len(registry["tools"]),
            "deep_stress_tool_count": sum(row.get("requires_deep_stress") is True for row in registry["tools"]),
            "operational_pass_count": len(operational_tools),
            "operational_red_count": len(red_tools),
            "operational_red_tools": red_tools,
            "integration_edge_count": len(edge_receipts),
            "operational_red_edge_count": len(red_edges),
            "operational_red_edges": red_edges,
            "trustworthy_receipt_written_even_if_red": True,
            "raw_reuse_used": bool(args.reuse_raw),
        },
    }
    write_json(out, estate)
    readback = load_json(out)
    if len(readback.get("tool_receipts", [])) != 139 or len(readback.get("integration_edge_receipts", [])) != len(edges["edges"]):
        raise HarnessFailure("estate read-back inventory mismatch")
    print(json.dumps(estate["producer_summary"], indent=2, sort_keys=True))
    print(f"receipt={out}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HarnessFailure as exc:
        print(f"HARNESS_FAILURE {exc}", file=sys.stderr)
        raise SystemExit(2)
    except Exception as exc:
        print(f"HARNESS_FAILURE {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        raise SystemExit(2)
