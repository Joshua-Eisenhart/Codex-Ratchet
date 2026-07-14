#!/usr/bin/env python3
"""Run the broad source-backed Ratchet surface without touching live checkouts.

Every mutable producer is copied to a temporary staging tree. Persistent
artifacts, command logs, source hashes, and scientific reds are then copied
into one append-only run directory. Execution completion is never promoted
into a scientific pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[4]
RESULTS = HERE / "results"
IMPORTED = HERE / "imported_claude"
HARDENED = HERE.parent / "hardened"
PYTHON = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
JULIA = Path("/opt/homebrew/bin/julia")
JULIA_PROJECT = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
JULIA_CORRECTION_PROJECT = Path("/Users/joshuaeisenhart/.julia/environments/v1.12")
LAKE = Path("/Users/joshuaeisenhart/.elan/bin/lake")
LEV_WORKTREE = Path("/Users/joshuaeisenhart/lev-main/.worktrees/eval-projection-contract")
LEV_COMMIT = "856acb1a5de42528a9a54272435d98a9fe226186"
JULIA_CORRECTIONS = HERE / "julia_correction_probes.jl"
SUITE_BINDING_PATHS = (
    "system_v5/ops/tooling/claude_campaign_20260713/full_surface/lev/flow.yaml",
    "system_v5/ops/tooling/claude_campaign_20260713/full_surface/lev/full_surface_campaign.eval.js",
    "system_v5/ops/tooling/claude_campaign_20260713/full_surface/lev/target.md",
    "system_v5/ops/tooling/claude_campaign_20260713/full_surface/lev/zero_execution.eval.js",
    "system_v5/ops/tooling/claude_campaign_20260713/full_surface/test_validate_full_surface.py",
    "system_v5/ops/tooling/claude_campaign_20260713/full_surface/validate_full_surface.py",
)
DEFAULT_ARCHIVE = Path(
    "/Users/joshuaeisenhart/Desktop/"
    "166_reconciled_ratchet_v0_11_7_cold_verified (1).zip"
)
ARCHIVE_MEMBERS = (
    "julia_canon/src/ExceptionalAlgebraCanon.jl",
    "sims_and_scripts/living_purgatory_ledger_r2_results.json",
    "sims_and_scripts/ontological_finitude_cosmogenesis_ratchet_sim.py",
)
BLOCKED_CONSUMERS = [
    "canonical scientific admission",
    "lego or layer promotion",
    "bridge, Axis0, basin, flux, or manifold completion",
    "Lev graph, ontology, or runtime authority",
    "provider-opinion promotion",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_source(relative: str, provenance: str = "committed_repo_source") -> dict[str, Any]:
    path = REPO_ROOT / relative
    return {
        "kind": "file",
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "provenance": provenance,
    }


def committed_suite_binding(relative: str, source_commit: str) -> dict[str, str]:
    path = REPO_ROOT / relative
    live_hash = sha256_file(path)
    committed = subprocess.run(
        ["git", "show", f"{source_commit}:{relative}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if committed.returncode != 0:
        raise RuntimeError(f"suite source absent from commit {source_commit}: {relative}")
    committed_hash = sha256_bytes(committed.stdout)
    if committed_hash != live_hash:
        raise RuntimeError(f"suite source differs from commit {source_commit}: {relative}")
    return {"path": relative, "sha256": live_hash}


def lev_commit_tree() -> str:
    current = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=LEV_WORKTREE,
        text=True,
    ).strip()
    if current != LEV_COMMIT:
        raise RuntimeError(f"live Lev executor is {current}, expected {LEV_COMMIT}")
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"{LEV_COMMIT}^{{commit}}"],
        cwd=LEV_WORKTREE,
        capture_output=True,
        check=False,
    )
    if exists.returncode != 0:
        raise RuntimeError(f"Lev executor commit is unavailable: {LEV_COMMIT}")
    return subprocess.check_output(
        ["git", "rev-parse", f"{LEV_COMMIT}^{{tree}}"],
        cwd=LEV_WORKTREE,
        text=True,
    ).strip()


def archive_source(archive: Path, member: str) -> dict[str, Any]:
    with zipfile.ZipFile(archive) as bundle:
        content = bundle.read(member)
    return {
        "kind": "archive_member",
        "path": str(archive),
        "member": member,
        "sha256": sha256_bytes(content),
        "provenance": "user_supplied_packet_archive",
    }


class RunContext:
    def __init__(self, artifact_root: Path):
        self.artifact_root = artifact_root
        self.groups: list[dict[str, Any]] = []
        self._command_counter = 0

    def command(
        self,
        group_id: str,
        command: list[str],
        *,
        cwd: Path,
        env_overrides: dict[str, str] | None = None,
        timeout: int = 900,
    ) -> dict[str, Any]:
        self._command_counter += 1
        group_dir = self.artifact_root / group_id
        group_dir.mkdir(parents=True, exist_ok=True)
        log_id = f"{self._command_counter:03d}"
        stdout_path = group_dir / f"{log_id}.stdout.txt"
        stderr_path = group_dir / f"{log_id}.stderr.txt"
        environment = dict(os.environ)
        overrides = env_overrides or {}
        environment.update(overrides)
        started_at = utc_now()
        started = time.perf_counter()
        timed_out = False
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                env=environment,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            exit_code: int | None = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except subprocess.TimeoutExpired as error:
            timed_out = True
            exit_code = None
            stdout = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
            stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        duration = time.perf_counter() - started
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        return {
            "command": command,
            "cwd": str(cwd.resolve()),
            "environment_overrides": overrides,
            "started_at": started_at,
            "finished_at": utc_now(),
            "duration_seconds": duration,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "stdout_path": str(stdout_path.resolve()),
            "stdout_sha256": sha256_file(stdout_path),
            "stderr_path": str(stderr_path.resolve()),
            "stderr_sha256": sha256_file(stderr_path),
        }

    def persist(self, group_id: str, source: Path, name: str | None = None) -> dict[str, Any]:
        destination = self.artifact_root / group_id / (name or source.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return {"path": str(destination.resolve()), "sha256": sha256_file(destination)}


def json_pointer(payload: Any, pointer: str) -> Any:
    value = payload
    for token in pointer.strip("/").split("/") if pointer != "/" else []:
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def group(
    *,
    group_id: str,
    kind: str,
    sources: list[dict[str, Any]],
    commands: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    required_artifact_count: int,
    execution_completed: bool,
    bounded_pass: bool | None,
    science_evidence: dict[str, Any],
    claim_ceiling: str,
    blockers: list[str] | None = None,
    red_preservation_required: bool = True,
) -> dict[str, Any]:
    status = (
        "execution_failed"
        if not execution_completed
        else "bounded_not_assessed"
        if bounded_pass is None
        else "bounded_pass"
        if bounded_pass
        else "bounded_red"
    )
    return {
        "id": group_id,
        "kind": kind,
        "classification": "integration_diagnostic",
        "sources": sources,
        "commands": commands,
        "artifacts": artifacts,
        "required_artifact_count": required_artifact_count,
        "execution_completed": execution_completed,
        "bounded_pass": bounded_pass,
        "science_evidence": science_evidence,
        "status": status,
        "claim_ceiling": claim_ceiling,
        "blockers": blockers or [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "red_preservation_required": red_preservation_required,
    }


def artifact_evidence(
    artifact: dict[str, Any], pointer: str, observed: Any, pass_value: Any
) -> dict[str, Any]:
    return {
        "kind": "artifact_json",
        "artifact_path": artifact["path"],
        "json_pointer": pointer,
        "command_index": None,
        "observed": observed,
        "pass_value": pass_value,
    }


def command_evidence(index: int, observed: int | None, pass_value: int) -> dict[str, Any]:
    return {
        "kind": "command_exit",
        "artifact_path": None,
        "json_pointer": None,
        "command_index": index,
        "observed": observed,
        "pass_value": pass_value,
    }


def copytree(source: Path, destination: Path, *, ignore_results: bool = True) -> None:
    def ignored(_directory: str, names: list[str]) -> set[str]:
        skipped = {"__pycache__", ".DS_Store", ".lake"}
        if ignore_results:
            skipped.update(
                name
                for name in names
                if name in {"results", "result.json", "rerun_result.json", "RESULTS.md"}
            )
        return skipped.intersection(names)

    shutil.copytree(source, destination, ignore=ignored)


def run_hardened(ctx: RunContext, stage: Path, archive: Path) -> dict[str, Any]:
    staged = stage / "repo/system_v5/ops/tooling/claude_campaign_20260713/hardened"
    copytree(HARDENED, staged)
    output = staged / "results/hardened_campaign_v2_envelope.json"
    command = ctx.command(
        "hardened_d_f_j_k_h",
        [str(PYTHON), str(staged / "run_hardened_campaign_v2.py"), "--archive", str(archive), "--output", str(output)],
        cwd=stage / "repo",
        env_overrides={"PYTHONDONTWRITEBYTECODE": "1"},
        timeout=1500,
    )
    parsed = load_json(output) if output.is_file() else {}
    artifacts = []
    for path in sorted((staged / "results").glob("*.json")):
        artifacts.append(ctx.persist("hardened_d_f_j_k_h", path))
    envelope_artifact = next((row for row in artifacts if row["path"].endswith("hardened_campaign_v2_envelope.json")), None)
    execution = bool(
        not command["timed_out"]
        and command["exit_code"] == 0
        and envelope_artifact
        and parsed.get("runner_all_completed") is True
    )
    observed = parsed.get("all_pass")
    evidence = artifact_evidence(envelope_artifact, "/all_pass", observed, True) if envelope_artifact else command_evidence(0, command["exit_code"], 0)
    sources = [
        repo_source(str(path.relative_to(REPO_ROOT)))
        for path in sorted(HARDENED.glob("*"))
        if path.suffix in {".py", ".jl"}
    ]
    return group(
        group_id="hardened_d_f_j_k_h",
        kind="hardened_stress_chain",
        sources=sources,
        commands=[command],
        artifacts=artifacts,
        required_artifact_count=1,
        execution_completed=execution,
        bounded_pass=observed is True,
        science_evidence=evidence,
        claim_ceiling="Function-level D/F/J/K diagnostics plus H semantic red; no campaign promotion.",
        blockers=list(parsed.get("summary", {}).get("semantic_blockers", [])),
        red_preservation_required=True,
    )


def run_imported_batteries(ctx: RunContext, stage: Path, archive: Path) -> list[dict[str, Any]]:
    staged = stage / "imported_claude"
    copytree(IMPORTED, staged, ignore_results=False)
    with zipfile.ZipFile(archive) as bundle:
        canon_bytes = bundle.read(ARCHIVE_MEMBERS[0])
    canon = staged / "ExceptionalAlgebraCanon.jl"
    canon.write_bytes(canon_bytes)
    project_snapshot = staged / "julia_correction_Project.toml"
    manifest_snapshot = staged / "julia_correction_Manifest.toml"
    shutil.copy2(JULIA_CORRECTION_PROJECT / "Project.toml", project_snapshot)
    shutil.copy2(JULIA_CORRECTION_PROJECT / "Manifest.toml", manifest_snapshot)
    specs = [
        {
            "id": "imported_python_battery",
            "source": "py_battery.py",
            "result": "py_battery_results.json",
            "command": [str(PYTHON), str(staged / "py_battery.py")],
            "env": {"JAX_ENABLE_X64": "1", "PYTHONDONTWRITEBYTECODE": "1"},
            "pointer": "/fail",
            "pass": 0,
            "ceiling": "Imported broad Python API/probe battery only; probe green is not scientific integration.",
        },
        {
            "id": "imported_fit_sweep",
            "source": "fit_sweep.py",
            "result": "fit_sweep_results.json",
            "command": [str(PYTHON), str(staged / "fit_sweep.py")],
            "env": {"JAX_ENABLE_X64": "1", "PYTHONDONTWRITEBYTECODE": "1"},
            "pointer": "/fail",
            "pass": 0,
            "ceiling": "Imported tool-lego fit fixtures only; synthetic fixtures do not admit consumers.",
        },
        {
            "id": "imported_julia_battery",
            "source": "jl_battery.jl",
            "result": "jl_battery_results.json",
            "command": [
                str(JULIA),
                "--startup-file=no",
                f"--project={JULIA_PROJECT}",
                str(staged / "jl_battery.jl"),
            ],
            "env": {"JULIA_LOAD_PATH": "@:@stdlib", "CANON_PATH": str(canon)},
            "pointer": "/fail",
            "pass": 0,
            "ceiling": "Imported Julia package/API battery only; optional-project and canon failures remain red.",
        },
    ]
    rows = []
    for spec in specs:
        command = ctx.command(spec["id"], spec["command"], cwd=staged, env_overrides=spec["env"], timeout=1200)
        result = staged / spec["result"]
        parsed = load_json(result) if result.is_file() else {}
        artifact = ctx.persist(spec["id"], result) if result.is_file() else None
        artifacts = [artifact] if artifact else []
        observed = json_pointer(parsed, spec["pointer"]) if parsed else None
        sources = [
            repo_source(
                str((IMPORTED / spec["source"]).relative_to(REPO_ROOT)),
                "newline_normalized_uncommitted_claude_snapshot",
            ),
            repo_source(
                str((IMPORTED / "source_provenance.json").relative_to(REPO_ROOT)),
                "source_snapshot_provenance",
            ),
        ]
        if spec["id"] == "imported_julia_battery":
            sources.append(archive_source(archive, ARCHIVE_MEMBERS[0]))
        rows.append(
            group(
                group_id=spec["id"],
                kind="imported_candidate_battery",
                sources=sources,
                commands=[command],
                artifacts=artifacts,
                required_artifact_count=1,
                execution_completed=bool(not command["timed_out"] and artifact and parsed),
                bounded_pass=observed == spec["pass"] if parsed else False,
                science_evidence=artifact_evidence(artifact, spec["pointer"], observed, spec["pass"]) if artifact else command_evidence(0, command["exit_code"], 0),
                claim_ceiling=spec["ceiling"],
                red_preservation_required=True,
            )
        )
    return rows


def run_julia_corrections(ctx: RunContext, stage: Path, archive: Path) -> dict[str, Any]:
    group_id = "julia_correction_probes"
    staged = stage / group_id
    staged.mkdir(parents=True)
    script = staged / JULIA_CORRECTIONS.name
    shutil.copy2(JULIA_CORRECTIONS, script)
    with zipfile.ZipFile(archive) as bundle:
        canon_bytes = bundle.read(ARCHIVE_MEMBERS[0])
    canon = staged / "ExceptionalAlgebraCanon.jl"
    canon.write_bytes(canon_bytes)
    output = staged / "julia_correction_probes_results.json"
    command = ctx.command(
        group_id,
        [
            str(JULIA),
            "--startup-file=no",
            f"--project={JULIA_CORRECTION_PROJECT}",
            str(script),
        ],
        cwd=staged,
        env_overrides={
            "CANON_PATH": str(canon),
            "OUTPUT_PATH": str(output),
            "CORRECTION_JULIA_EXECUTABLE": str(JULIA),
            "CORRECTION_JULIA_PROJECT": str(JULIA_CORRECTION_PROJECT),
            "CORRECTION_CANDIDATE_PROJECT": str(JULIA_PROJECT),
            "JULIA_LOAD_PATH": "@:@stdlib",
        },
        timeout=1200,
    )
    parsed = load_json(output) if output.is_file() else {}
    artifact = ctx.persist(group_id, output) if output.is_file() else None
    artifacts = [artifact] if artifact else []
    artifacts.extend(
        [
            ctx.persist(group_id, project_snapshot),
            ctx.persist(group_id, manifest_snapshot),
        ]
    )
    observed = parsed.get("all_pass")
    evidence = (
        artifact_evidence(artifact, "/all_pass", observed, True)
        if artifact
        else command_evidence(0, command["exit_code"], 0)
    )
    return group(
        group_id=group_id,
        kind="source_backed_correction_probe",
        sources=[
            repo_source(str(JULIA_CORRECTIONS.relative_to(REPO_ROOT))),
            archive_source(archive, ARCHIVE_MEMBERS[0]),
        ],
        commands=[command],
        artifacts=artifacts,
        required_artifact_count=3,
        execution_completed=bool(not command["timed_out"] and artifact),
        bounded_pass=command["exit_code"] == 0 and observed is True,
        science_evidence=evidence,
        claim_ceiling="Machine-local Julia API/environment correction probes only; no scientific admission or portable/canonical environment claim.",
        blockers=[],
        red_preservation_required=True,
    )


FOUNDATION_SCRIPTS = [
    (
        "foundation_entropy_gradient",
        "system_v7/constraint_core/sims_and_scripts/foundational_ratchet_entropy_gradient_sim.py",
        "/FOLLOWS_RATCHET_RULES",
    ),
    (
        "foundation_forcing_robustness",
        "system_v7/constraint_core/sims_and_scripts/foundations_reaudit_forcing_robustness_sim.py",
        "/policy_eval/FOUNDATIONS_EARNED_FORCED_ROBUST_LOADBEARING",
    ),
    (
        "foundation_drive_mss_tiebreak",
        "system_v7/constraint_core/sims_and_scripts/foundations_reaudit_drive_and_mss_tiebreak_sim.py",
        "/policy_eval/ROOT_DRIVE_AND_TIEBREAK_AUDITED",
    ),
]


def run_foundation_scripts(ctx: RunContext, stage: Path) -> list[dict[str, Any]]:
    rows = []
    staged = stage / "foundation_scripts"
    staged.mkdir(parents=True)
    for group_id, relative, pointer in FOUNDATION_SCRIPTS:
        source = REPO_ROOT / relative
        target = staged / source.name
        shutil.copy2(source, target)
        command = ctx.command(
            group_id,
            [str(PYTHON), str(target)],
            cwd=staged,
            env_overrides={"PYTHONDONTWRITEBYTECODE": "1"},
            timeout=600,
        )
        result = target.with_name(target.stem + "_results.json")
        parsed = load_json(result) if result.is_file() else {}
        evidence_from_artifact = False
        observed: Any = command["exit_code"] == 0
        if parsed:
            for candidate_pointer in (
                pointer,
                "/all_pass",
                "/OVERALL_PASS",
                "/follows_ratchet_rules",
            ):
                try:
                    observed = json_pointer(parsed, candidate_pointer)
                    pointer = candidate_pointer
                    evidence_from_artifact = True
                    break
                except (KeyError, IndexError, TypeError):
                    continue
        artifact = ctx.persist(group_id, result) if result.is_file() else None
        evidence = (
            artifact_evidence(artifact, pointer, observed, True)
            if artifact and evidence_from_artifact
            else command_evidence(0, command["exit_code"], 0)
        )
        rows.append(
            group(
                group_id=group_id,
                kind="foundation_scratch_diagnostic",
                sources=[repo_source(relative)],
                commands=[command],
                artifacts=[artifact] if artifact else [],
                required_artifact_count=1,
                execution_completed=bool(not command["timed_out"] and artifact and parsed),
                bounded_pass=observed is True,
                science_evidence=evidence,
                claim_ceiling="Copied foundation-only scratch diagnostic; no Axis0, basin, bridge, or manifold admission.",
                red_preservation_required=True,
            )
        )
    return rows


DUAL_SUITES = [
    "system_v7/sims/manifold_dual_ratchet_foundations_v0",
    "system_v7/sims/manifold_dual_ratchet_foundations_v0_1",
]


def run_dual_suites(ctx: RunContext, stage: Path) -> list[dict[str, Any]]:
    rows = []
    for relative in DUAL_SUITES:
        source_dir = REPO_ROOT / relative
        group_id = source_dir.name
        staged = stage / group_id
        copytree(source_dir, staged)
        py = staged / f"{group_id}_numpy.py"
        jl = staged / f"{group_id}_julia.jl"
        agreement = staged / "check_agreement.py"
        commands = [
            ctx.command(group_id, [str(PYTHON), str(py)], cwd=staged, env_overrides={"PYTHONDONTWRITEBYTECODE": "1"}, timeout=900),
            ctx.command(group_id, [str(JULIA), "--startup-file=no", f"--project={JULIA_PROJECT}", str(jl)], cwd=staged, env_overrides={"JULIA_LOAD_PATH": "@:@stdlib"}, timeout=1200),
            ctx.command(group_id, [str(PYTHON), str(agreement)], cwd=staged, env_overrides={"PYTHONDONTWRITEBYTECODE": "1"}, timeout=600),
        ]
        result = staged / "results" / f"{group_id}_agreement_results.json"
        parsed = load_json(result) if result.is_file() else {}
        artifact_rows = []
        for path in sorted((staged / "results").glob("*")):
            if path.is_file():
                artifact_rows.append(ctx.persist(group_id, path))
        agreement_artifact = next((row for row in artifact_rows if row["path"].endswith("_agreement_results.json")), None)
        observed = parsed.get("parity_passed")
        execution = bool(
            all(not command["timed_out"] for command in commands)
            and agreement_artifact
            and parsed
        )
        sources = [
            repo_source(str(path.relative_to(REPO_ROOT)))
            for path in sorted(source_dir.iterdir())
            if path.is_file() and path.suffix in {".py", ".jl", ".json"}
        ]
        rows.append(
            group(
                group_id=group_id,
                kind="cross_runtime_foundation_diagnostic",
                sources=sources,
                commands=commands,
                artifacts=artifact_rows,
                required_artifact_count=1,
                execution_completed=execution,
                bounded_pass=observed is True,
                science_evidence=artifact_evidence(agreement_artifact, "/parity_passed", observed, True) if agreement_artifact else command_evidence(2, commands[2]["exit_code"], 0),
                claim_ceiling="Quarantined NumPy/Julia foundations parity only; no scientific manifold admission.",
                red_preservation_required=True,
            )
        )
    return rows


def run_engine_suite(ctx: RunContext, stage: Path, three_qubit: bool) -> dict[str, Any]:
    group_id = "legacy_engine_3q" if three_qubit else "legacy_engine_1q"
    source_dir = REPO_ROOT / "system_v7/constraint_core/engines"
    staged = stage / group_id
    staged.mkdir(parents=True)
    suffix = "_3q" if three_qubit else ""
    names = [
        f"oracle_targets{suffix}.py",
        f"jax_engine{suffix}.py",
        f"julia_engine{suffix}.jl",
        f"torch_engine{suffix}.py",
        f"validate_engines{suffix}.py",
    ]
    for name in names:
        shutil.copy2(source_dir / name, staged / name)
    commands = [
        ctx.command(group_id, [str(PYTHON), str(staged / names[0])], cwd=staged, env_overrides={"PYTHONDONTWRITEBYTECODE": "1", "JAX_ENABLE_X64": "1"}, timeout=1500),
        ctx.command(group_id, [str(PYTHON), str(staged / names[1])], cwd=staged, env_overrides={"PYTHONDONTWRITEBYTECODE": "1", "JAX_ENABLE_X64": "1"}, timeout=1500),
        ctx.command(group_id, [str(JULIA), "--startup-file=no", f"--project={JULIA_PROJECT}", str(staged / names[2])], cwd=staged, env_overrides={"JULIA_LOAD_PATH": "@:@stdlib"}, timeout=1800),
        ctx.command(group_id, [str(PYTHON), str(staged / names[3])], cwd=staged, env_overrides={"PYTHONDONTWRITEBYTECODE": "1"}, timeout=1800),
        ctx.command(group_id, [str(PYTHON), str(staged / names[4])], cwd=staged, env_overrides={"PYTHONDONTWRITEBYTECODE": "1"}, timeout=600),
    ]
    artifacts = [
        ctx.persist(group_id, path)
        for path in sorted(staged.glob("*.json"))
        if path.is_file()
    ]
    expected_artifacts = 4 if three_qubit else 4
    execution = bool(
        all(not command["timed_out"] for command in commands)
        and len(artifacts) >= expected_artifacts
    )
    return group(
        group_id=group_id,
        kind="legacy_cross_substrate_engine_diagnostic",
        sources=[
            repo_source(f"system_v7/constraint_core/engines/{name}")
            for name in names
        ],
        commands=commands,
        artifacts=artifacts,
        required_artifact_count=expected_artifacts,
        execution_completed=execution,
        bounded_pass=commands[-1]["exit_code"] == 0,
        science_evidence=command_evidence(4, commands[-1]["exit_code"], 0),
        claim_ceiling="Legacy source-token engine parity diagnostic; banned labels and scratch status prevent canon.",
        red_preservation_required=True,
    )


def stage_process_test_tree(stage: Path) -> tuple[Path, list[Path]]:
    """Stage the process tests under a disposable repo-shaped root.

    The validator resolves card paths from ``Path(__file__).parents[3]``. A
    flat copy therefore turns every repo-relative manifest entry into a false
    file-not-found red. Preserve the repository layout and copy only the
    dependencies explicitly declared by the frozen proposal card.
    """

    relative = "system_v7/control/ratchet_process_v1"
    source_dir = REPO_ROOT / relative
    staged_repo = stage / "process_repo"
    staged = staged_repo / relative
    copytree(source_dir, staged, ignore_results=False)

    card_path = source_dir / "examples/coratchet_recursive_foundations_v1.card.json"
    card = load_json(card_path)
    declared_paths: list[Path] = []
    for field in ("source_manifest", "predecessor_receipts"):
        for index, entry in enumerate(card.get(field, [])):
            value = entry.get("path") if isinstance(entry, dict) else None
            if not isinstance(value, str) or not value:
                raise ValueError(f"{field}[{index}].path must be a non-empty string")
            relative_path = Path(value)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise ValueError(f"{field}[{index}].path escapes the staged repository")
            source = REPO_ROOT / relative_path
            if not source.is_file():
                raise FileNotFoundError(source)
            destination = staged_repo / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            declared_paths.append(source)

    staged_sources = {
        path
        for path in source_dir.rglob("*")
        if path.is_file()
    }
    staged_sources.update(declared_paths)
    return staged, sorted(staged_sources)


def run_process_tests(ctx: RunContext, stage: Path) -> dict[str, Any]:
    staged, staged_sources = stage_process_test_tree(stage)
    command = ctx.command(
        "ratchet_process_v1_tests",
        [str(PYTHON), "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test*.py", "-v"],
        cwd=staged,
        env_overrides={"PYTHONDONTWRITEBYTECODE": "1"},
        timeout=600,
    )
    sources = [
        repo_source(str(path.relative_to(REPO_ROOT)))
        for path in staged_sources
    ]
    return group(
        group_id="ratchet_process_v1_tests",
        kind="process_gate_test",
        sources=sources,
        commands=[command],
        artifacts=[],
        required_artifact_count=0,
        execution_completed=not command["timed_out"],
        bounded_pass=command["exit_code"] == 0,
        science_evidence=command_evidence(0, command["exit_code"], 0),
        claim_ceiling="Process-card validator tests only; no scientific admission.",
        red_preservation_required=True,
    )


def run_qics(ctx: RunContext, stage: Path) -> dict[str, Any]:
    relative = "system_v7/sims/qics_entropy_dpi_numeric_oracle_v0"
    source_dir = REPO_ROOT / relative
    staged = stage / "qics_entropy_dpi_numeric_oracle_v0"
    copytree(source_dir, staged)
    command = ctx.command(
        "qics_entropy_dpi_oracle",
        ["/bin/sh", str(staged / "run_all.sh")],
        cwd=staged,
        env_overrides={"PYTHONDONTWRITEBYTECODE": "1"},
        timeout=1800,
    )
    result = staged / "result.json"
    parsed = load_json(result) if result.is_file() else {}
    artifacts = [
        ctx.persist("qics_entropy_dpi_oracle", path)
        for path in sorted(staged.glob("*.json"))
        if path.name in {"result.json", "rerun_result.json"}
    ]
    artifact = next((row for row in artifacts if row["path"].endswith("/result.json")), None)
    pointer = "/all_tests_pass"
    try:
        observed = json_pointer(parsed, pointer)
    except (KeyError, TypeError):
        observed = command["exit_code"] == 0
        pointer = ""
    evidence = artifact_evidence(artifact, pointer, observed, True) if artifact and pointer else command_evidence(0, command["exit_code"], 0)
    return group(
        group_id="qics_entropy_dpi_oracle",
        kind="pinned_external_oracle_diagnostic",
        sources=[
            repo_source(str(path.relative_to(REPO_ROOT)))
            for path in sorted(source_dir.iterdir())
            if path.is_file() and path.suffix in {".py", ".sh", ".json"}
        ],
        commands=[command],
        artifacts=artifacts,
        required_artifact_count=1,
        execution_completed=bool(not command["timed_out"] and result.is_file()),
        bounded_pass=command["exit_code"] == 0 and observed is True,
        science_evidence=evidence,
        claim_ceiling="Pinned QICS fixed-input numeric oracle only; no formal or engine authority.",
        red_preservation_required=True,
    )


def run_lean(ctx: RunContext, stage: Path) -> dict[str, Any]:
    relative = "system_v4/lean"
    source_dir = REPO_ROOT / relative
    staged = stage / "lean"
    copytree(source_dir, staged, ignore_results=False)
    command = ctx.command(
        "lean_formal_surface",
        [str(LAKE), "build"],
        cwd=staged,
        env_overrides={},
        timeout=900,
    )
    return group(
        group_id="lean_formal_surface",
        kind="formal_build",
        sources=[
            repo_source(str(path.relative_to(REPO_ROOT)))
            for path in sorted(source_dir.rglob("*"))
            if path.is_file() and path.suffix in {".lean", ".toml", ""}
        ],
        commands=[command],
        artifacts=[],
        required_artifact_count=0,
        execution_completed=not command["timed_out"],
        bounded_pass=command["exit_code"] == 0,
        science_evidence=command_evidence(0, command["exit_code"], 0),
        claim_ceiling="Lean source build only; the current theorem library does not admit the Ratchet science.",
        red_preservation_required=True,
    )


def run_grok_advisory_validation(ctx: RunContext) -> dict[str, Any] | None:
    directory = HERE.parent / "cross_thinking"
    validator = directory / "validate_grok45_cross_thinking.py"
    receipt = directory / "results/grok45_cross_thinking_receipt.json"
    if not validator.is_file() or not receipt.is_file():
        return None
    command = ctx.command(
        "grok45_advisory_validation",
        [str(PYTHON), str(validator), str(receipt)],
        cwd=REPO_ROOT,
        env_overrides={"PYTHONDONTWRITEBYTECODE": "1"},
        timeout=120,
    )
    return group(
        group_id="grok45_advisory_validation",
        kind="provider_advisory_validation",
        sources=[
            {
                "kind": "file",
                "path": str(validator.resolve()),
                "sha256": sha256_file(validator),
                "provenance": "provider_advisory_validator",
            },
            {
                "kind": "file",
                "path": str(receipt.resolve()),
                "sha256": sha256_file(receipt),
                "provenance": "provider_advisory_receipt",
            },
        ],
        commands=[command],
        artifacts=[],
        required_artifact_count=0,
        execution_completed=not command["timed_out"],
        bounded_pass=None,
        science_evidence=command_evidence(0, command["exit_code"], 0),
        claim_ceiling="Advisory receipt integrity only; provider text is not scientific evidence or a pass.",
        red_preservation_required=False,
    )


def blocked_inventory() -> list[dict[str, Any]]:
    formal = REPO_ROOT / "system_v5/ops/formal_scouts"
    hardcoded = []
    for path in sorted(formal.glob("*_envelope*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if 'Path("/Users/joshuaeisenhart/Codex-Ratchet")' in text:
            hardcoded.append(
                {
                    "path": str(path.resolve()),
                    "sha256": sha256_file(path),
                    "reason": "hardcoded live-repo result paths; isolated execution would write dirty owner state",
                }
            )
    return [
        {
            "id": "formal_scout_absolute_write_family",
            "status": "blocked",
            "source_count": len(hardcoded),
            "sources": hardcoded,
            "reason": "not executed because the producers bind outputs to the dirty live checkout",
        },
        {
            "id": "alco_j3o_oracle",
            "status": "blocked",
            "source_count": 1,
            "sources": [
                {
                    "path": str((REPO_ROOT / "system_v7/sims/alco_j3o_exact_oracle_v0/run_oracle.py").resolve()),
                    "sha256": sha256_file(REPO_ROOT / "system_v7/sims/alco_j3o_exact_oracle_v0/run_oracle.py"),
                    "reason": "controller provenance hardcodes a currently dirty live j3o source",
                }
            ],
            "reason": "running a temp copy would still hash dirty live owner state",
        },
        {
            "id": "physlib_external_formal_surface",
            "status": "blocked",
            "source_count": 0,
            "sources": [],
            "reason": "no repo-local executable producer was identified for the claimed physlib leg",
        },
    ]


def set_coverage(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["id"]: row for row in groups}
    mapping: dict[str, dict[str, Any]] = {
        "A": {
            "blockers": [],
            "findings": [],
            "observations": [
                ("A_z3_flip", "imported_python_battery", "artifact_json", "/results/z3_unsat_sat_flip/status", "PASS", "py_battery_results.json"),
                ("A_cvc5_flip", "imported_python_battery", "artifact_json", "/results/cvc5_unsat_sat_flip/status", "PASS", "py_battery_results.json"),
                ("A_solver_agreement", "imported_python_battery", "artifact_json", "/results/z3_cvc5_agreement/status", "PASS", "py_battery_results.json"),
                ("A_sympy_identity", "imported_python_battery", "artifact_json", "/results/sympy_exact_identity/status", "PASS", "py_battery_results.json"),
            ],
        },
        "B": {
            "blockers": [],
            "findings": [
                "frozen imported Julia battery remains 12/15 red; corrected Albert, Clifford, and Enzyme probes show candidate API/environment defects"
            ],
            "observations": [
                ("B_albert_identity", "julia_correction_probes", "artifact_json", "/checks/albert_component_norm/corrected_pass", True, "julia_correction_probes_results.json"),
                ("B_octonion_associator", "imported_julia_battery", "artifact_json", "/results/canon_module_octonion_associator/status", "PASS", "jl_battery_results.json"),
            ],
        },
        "C": {
            "blockers": [],
            "findings": [],
            "observations": [
                ("C_jax_torch_agreement", "imported_python_battery", "artifact_json", "/results/jax_torch_numerical_agreement/status", "PASS", "py_battery_results.json"),
                ("C_legacy_1q", "legacy_engine_1q", "group_bounded_pass", None, True, None),
                ("C_legacy_3q", "legacy_engine_3q", "group_bounded_pass", None, True, None),
            ],
        },
        "D": {
            "blockers": [],
            "findings": [],
            "observations": [
                ("D_basin_chain", "hardened_d_f_j_k_h", "artifact_json", "/lanes/0/receipt_all_pass", True, "hardened_campaign_v2_envelope.json"),
            ],
        },
        "E": {
            "blockers": ["fixture-level Maude only"],
            "findings": [],
            "observations": [
                ("E_maude_bracketing", "imported_python_battery", "artifact_json", "/results/maude_t01_bracketing_flip/status", "PASS", "py_battery_results.json"),
            ],
        },
        "F": {
            "blockers": [],
            "findings": [],
            "observations": [
                ("F_structured_transport", "hardened_d_f_j_k_h", "artifact_json", "/lanes/1/receipt_all_pass", True, "hardened_campaign_v2_envelope.json"),
            ],
        },
        "G": {
            "blockers": [],
            "findings": [],
            "observations": [
                ("G_dynamiqs_qutip", "imported_fit_sweep", "artifact_json", "/results/dynamiqs_qutip_cross_agreement/status", "PASS", "fit_sweep_results.json"),
                ("G_quantumoptics_trace", "imported_julia_battery", "artifact_json", "/results/quantumoptics_lindblad_trace/status", "PASS", "jl_battery_results.json"),
            ],
        },
        "H": {
            "blockers": [],
            "findings": ["native ledger accepts a cycle and no ancestry-DAG rule was found"],
            "observations": [
                ("H_lineage_semantics", "hardened_d_f_j_k_h", "artifact_json", "/lanes/4/receipt_all_pass", True, "hardened_campaign_v2_envelope.json"),
            ],
        },
        "I": {
            "blockers": ["Flux/Lux consumer chain not executed"],
            "findings": [],
            "observations": [
                ("I_e3nn_equivariance", "imported_fit_sweep", "artifact_json", "/results/e3nn_exact_equivariance/status", "PASS", "fit_sweep_results.json"),
                ("I_pyg_equivariance", "imported_fit_sweep", "artifact_json", "/results/pyg_permutation_equivariance/status", "PASS", "fit_sweep_results.json"),
                ("I_learning_control", "imported_fit_sweep", "artifact_json", "/results/torch_learning_with_shuffle_control/status", "PASS", "fit_sweep_results.json"),
            ],
        },
        "J": {
            "blockers": ["Julia IntervalArithmetic leg not executed"],
            "findings": [],
            "observations": [
                ("J_autolirpa", "hardened_d_f_j_k_h", "artifact_json", "/lanes/2/receipt_all_pass", True, "hardened_campaign_v2_envelope.json"),
                ("J_interval_fixture", "imported_fit_sweep", "artifact_json", "/results/interval_certified_bound/status", "PASS", "fit_sweep_results.json"),
            ],
        },
        "K": {
            "blockers": [],
            "findings": [],
            "observations": [
                ("K_hardened_tensor_chain", "hardened_d_f_j_k_h", "artifact_json", "/lanes/3/receipt_all_pass", True, "hardened_campaign_v2_envelope.json"),
                ("K_quimb_entropy", "imported_fit_sweep", "artifact_json", "/results/quimb_ghz_cut_entropy/status", "PASS", "fit_sweep_results.json"),
                ("K_itensors_norm", "imported_julia_battery", "artifact_json", "/results/itensors_mps_norm/status", "PASS", "jl_battery_results.json"),
            ],
        },
        "L": {
            "blockers": ["ALCO and physlib legs blocked"],
            "findings": [],
            "observations": [
                ("L_lean_build", "lean_formal_surface", "group_bounded_pass", None, True, None),
                ("L_qics_oracle", "qics_entropy_dpi_oracle", "group_bounded_pass", None, True, None),
            ],
        },
    }
    rows = []
    for set_id, spec in mapping.items():
        observations = []
        group_ids: list[str] = []
        for observation_id, group_id, kind, pointer, pass_value, suffix in spec["observations"]:
            if group_id not in group_ids:
                group_ids.append(group_id)
            source_group = by_id[group_id]
            if kind == "artifact_json":
                artifact = next(
                    row for row in source_group["artifacts"] if row["path"].endswith(str(suffix))
                )
                observed = json_pointer(load_json(Path(artifact["path"])), str(pointer))
                artifact_path: str | None = artifact["path"]
            else:
                observed = source_group["bounded_pass"]
                artifact_path = None
            observations.append(
                {
                    "observation_id": observation_id,
                    "group_id": group_id,
                    "kind": kind,
                    "artifact_path": artifact_path,
                    "json_pointer": pointer,
                    "observed": observed,
                    "pass_value": pass_value,
                }
            )
        execution = all(by_id[group_id]["execution_completed"] for group_id in group_ids)
        observation_passes = [row["observed"] == row["pass_value"] for row in observations]
        if not execution:
            status = "execution_blocked"
        elif any(value is False for value in observation_passes):
            status = "red"
        elif spec["blockers"]:
            status = "partial"
        elif observation_passes and all(observation_passes):
            status = "bounded_green"
        else:
            status = "not_assessed"
        rows.append(
            {
                "set_id": set_id,
                "group_ids": group_ids,
                "status": status,
                "blockers": spec["blockers"],
                "findings": spec["findings"],
                "observations": observations,
                "promotion_allowed": False,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=RESULTS / "full_surface_envelope.json")
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    if Path(sys.executable).resolve() != PYTHON.resolve():
        raise RuntimeError(f"wrong Python runtime: {sys.executable}")
    lev_tree = lev_commit_tree()
    archive = args.archive.resolve()
    if not archive.is_file():
        raise FileNotFoundError(archive)
    artifact_root = args.artifact_dir.resolve()
    if artifact_root.exists():
        raise FileExistsError(f"artifact directory already exists: {artifact_root}")
    artifact_root.mkdir(parents=True)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    ctx = RunContext(artifact_root)
    started_at = utc_now()
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="codex-ratchet-full-surface-") as temp:
        stage = Path(temp)
        groups: list[dict[str, Any]] = []
        groups.append(run_hardened(ctx, stage, archive))
        groups.extend(run_imported_batteries(ctx, stage, archive))
        groups.append(run_julia_corrections(ctx, stage, archive))
        groups.extend(run_foundation_scripts(ctx, stage))
        groups.extend(run_dual_suites(ctx, stage))
        groups.append(run_engine_suite(ctx, stage, three_qubit=False))
        groups.append(run_engine_suite(ctx, stage, three_qubit=True))
        groups.append(run_process_tests(ctx, stage))
        groups.append(run_qics(ctx, stage))
        groups.append(run_lean(ctx, stage))
        advisory = run_grok_advisory_validation(ctx)
        if advisory is not None:
            groups.append(advisory)
    inventory = blocked_inventory()
    coverage = set_coverage(groups)
    bounded = [row["bounded_pass"] for row in groups if row["bounded_pass"] is not None]
    summary = {
        "group_count": len(groups),
        "command_count": sum(len(row["commands"]) for row in groups),
        "executed_command_count": sum(
            1
            for row in groups
            for command in row["commands"]
            if not command["timed_out"] and command["exit_code"] is not None
        ),
        "execution_failed_count": sum(not row["execution_completed"] for row in groups),
        "bounded_pass_count": sum(value is True for value in bounded),
        "bounded_red_count": sum(value is False for value in bounded),
        "bounded_not_assessed_count": sum(row["bounded_pass"] is None for row in groups),
        "blocked_inventory_count": len(inventory),
        "set_count": len(coverage),
        "set_evidence_complete_count": sum(row["status"] in {"bounded_green", "red"} for row in coverage),
        "set_bounded_green_count": sum(row["status"] == "bounded_green" for row in coverage),
        "set_red_count": sum(row["status"] == "red" for row in coverage),
        "set_partial_count": sum(row["status"] == "partial" for row in coverage),
        "set_execution_blocked_count": sum(row["status"] == "execution_blocked" for row in coverage),
    }
    runner_all_completed = summary["execution_failed_count"] == 0 and summary["executed_command_count"] == summary["command_count"]
    bounded_observations_all_pass = (
        bool(bounded)
        and all(bounded)
        and summary["set_partial_count"] == 0
        and summary["set_execution_blocked_count"] == 0
        and summary["set_red_count"] == 0
    )
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    suite_bindings = [
        committed_suite_binding(relative, source_commit)
        for relative in SUITE_BINDING_PATHS
    ]
    source_path = Path(__file__).resolve()
    command = [
        str(PYTHON),
        str(source_path),
        "--archive",
        str(archive),
        "--output",
        str(output),
        "--artifact-dir",
        str(artifact_root),
    ]
    envelope = {
        "schema": "codex-ratchet.full-surface-campaign-envelope.v1",
        "campaign_id": "claude_campaign_20260713_full_surface_v1",
        "created_at": utc_now(),
        "started_at": started_at,
        "duration_seconds": time.perf_counter() - started,
        "command": command,
        "runner_identity": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "platform": platform.platform(),
            "pid": os.getpid(),
        },
        "lev_executor": {
            "worktree": str(LEV_WORKTREE),
            "git_commit": LEV_COMMIT,
            "git_tree": lev_tree,
            "suite_bindings": suite_bindings,
            "expected_status": "projected",
            "expected_suite_status": "passed",
            "projection_only": True,
            "release_eligible": False,
        },
        "source": {
            "path": str(source_path),
            "sha256": sha256_file(source_path),
            "git_commit": source_commit,
        },
        "archive": {
            "path": str(archive),
            "sha256": sha256_file(archive),
            "members": [archive_source(archive, member) for member in ARCHIVE_MEMBERS],
        },
        "artifact_root": str(artifact_root),
        "classification": "integration_diagnostic",
        "promotion_allowed": False,
        "partial_promotion_allowed": False,
        "formal_admission_allowed": False,
        "provider_advisory_is_evidence": False,
        "projection_only": False,
        "runner_all_completed": runner_all_completed,
        "bounded_observations_all_pass": bounded_observations_all_pass,
        "all_pass": False,
        "truth_state": "host_recomputed_blocked",
        "summary": summary,
        "groups": groups,
        "set_coverage": coverage,
        "blocked_inventory": inventory,
        "tool_calls": [
            {
                "tool": "Lev commandCases",
                "function": "harness-backed command execution",
                "observable": "nonzero executed command count plus hashed stdout/stderr and artifacts",
            },
            {
                "tool": "Python subprocess",
                "function": "bounded isolated producer execution",
                "observable": "exit, timeout, timestamp, source hash, result hash, and preserved scientific polarity",
            },
        ],
        "claim_ceiling": (
            "Host-recomputed integration diagnostic across named source-backed surfaces. "
            "Execution green, tool-fit green, or provider advice cannot promote scientific claims."
        ),
        "blocked_consumers": BLOCKED_CONSUMERS,
    }
    write_json(output, envelope)
    print(
        json.dumps(
            {
                "runner_all_completed": runner_all_completed,
                "bounded_observations_all_pass": bounded_observations_all_pass,
                "all_pass": False,
                "summary": summary,
                "output": str(output),
            },
            sort_keys=True,
        )
    )
    return 0 if runner_all_completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
