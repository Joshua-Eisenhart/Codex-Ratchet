"""
a2_evermem_backend_reachability_audit_operator.py

Bounded reachability audit for the local EverMemOS backend expected by Ratchet.

This slice checks local repo prerequisites, tooling availability, Docker daemon
reachability, and localhost health probes without starting services or widening
into bootstrap or broader memory claims.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVERMEMOS_REPO = "work/reference_repos/EverMind-AI/EverMemOS"
DEFAULT_HEALTH_URL = "http://localhost:1995/health"
DEFAULT_RETRIEVAL_REPORT = "system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.json"
DEFAULT_SYNC_REPORT = "system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json"
DEFAULT_REPORT_JSON = (
    "system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.json"
)
DEFAULT_REPORT_MD = (
    "system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.md"
)
DEFAULT_PACKET_JSON = (
    "system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_PACKET__CURRENT__v1.json"
)

CLUSTER_ID = "SKILL_CLUSTER::evermem-witness-memory"
SLICE_ID = "a2-evermem-backend-reachability-audit-operator"
DEFAULT_NON_GOALS = [
    "Do not start Docker services from this slice.",
    "Do not write .env or install dependencies from this slice.",
    "Do not claim startup bootstrap, pi-mono memory, or A2 replacement.",
    "Do not mutate canonical A2 state or EverMem runtime state from this slice.",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve_output_path(root: Path, raw: Any, default_rel: str) -> Path:
    if not raw:
        return root / default_rel
    path = Path(str(raw))
    return path if path.is_absolute() else root / path


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _which(name: str) -> str:
    return shutil.which(name) or ""


def _run_command(argv: list[str], cwd: Path | None = None, timeout_seconds: float = 3.0) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "argv": argv,
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "command_not_found",
            "argv": argv,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "timeout",
            "argv": argv,
        }


def _python_http_probe(url: str, timeout_seconds: float) -> dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {
                "ok": response.status == 200,
                "status_code": response.status,
                "body_preview": body[:180],
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status_code": exc.code,
            "body_preview": body[:180],
            "error": f"HTTPError: {exc.code}",
        }
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        return {
            "ok": False,
            "status_code": None,
            "body_preview": "",
            "error": f"URLError: {reason}",
        }
    except TimeoutError:
        return {
            "ok": False,
            "status_code": None,
            "body_preview": "",
            "error": "TimeoutError",
        }


def build_a2_evermem_backend_reachability_audit_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()
    timeout_seconds = float(ctx.get("timeout_seconds", 2.0))
    evermemos_repo = _resolve_output_path(root, ctx.get("evermemos_repo_path"), DEFAULT_EVERMEMOS_REPO)
    health_url = str(ctx.get("health_url", DEFAULT_HEALTH_URL))
    retrieval_report = _safe_load_json(_resolve_output_path(root, ctx.get("retrieval_report_path"), DEFAULT_RETRIEVAL_REPORT))
    sync_report = _safe_load_json(_resolve_output_path(root, ctx.get("sync_report_path"), DEFAULT_SYNC_REPORT))

    tooling = {
        "uv": _which("uv"),
        "curl": _which("curl"),
        "docker": _which("docker"),
        "docker_compose": _which("docker-compose"),
    }
    repo_state = {
        "repo_exists": evermemos_repo.exists(),
        "env_template_exists": (evermemos_repo / "env.template").exists(),
        "env_exists": (evermemos_repo / ".env").exists(),
        "venv_exists": (evermemos_repo / ".venv").exists(),
        "uv_lock_exists": (evermemos_repo / "uv.lock").exists(),
        "docker_compose_file_exists": (evermemos_repo / "docker-compose.yaml").exists(),
        "web_entry_exists": (evermemos_repo / "src/run.py").exists(),
    }

    docker_daemon = (
        _run_command(["docker", "ps"], timeout_seconds=timeout_seconds)
        if tooling["docker"]
        else {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "docker_missing",
            "argv": ["docker", "ps"],
        }
    )
    curl_probe = (
        _run_command(
            ["curl", "-sS", "--max-time", str(int(max(1.0, timeout_seconds))), health_url],
            timeout_seconds=timeout_seconds + 1.0,
        )
        if tooling["curl"]
        else {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "curl_missing",
            "argv": ["curl", health_url],
        }
    )
    python_probe = _python_http_probe(health_url, timeout_seconds)

    issues: list[str] = []
    if not repo_state["repo_exists"]:
        issues.append("EverMemOS repo checkout is missing")
    if not repo_state["env_template_exists"]:
        issues.append("EverMemOS env.template is missing")
    if not tooling["docker"]:
        issues.append("docker binary is missing")
    if not tooling["docker_compose"]:
        issues.append("docker-compose binary is missing")
    if not tooling["uv"]:
        issues.append("uv is missing")
    if not repo_state["env_exists"]:
        issues.append("EverMemOS .env is missing")
    if not repo_state["venv_exists"]:
        issues.append("EverMemOS .venv is missing")
    if not docker_daemon["ok"]:
        issues.append(f"docker daemon unavailable: {docker_daemon['stderr'] or docker_daemon['stdout'] or 'unknown'}")
    if not curl_probe["ok"]:
        issues.append(f"curl health probe failed: {curl_probe['stderr'] or curl_probe['stdout'] or 'unknown'}")
    if not python_probe["ok"]:
        issues.append(f"python health probe failed: {python_probe['error'] or 'unknown'}")

    if curl_probe["ok"] and python_probe["ok"]:
        next_step = "rerun_witness_memory_retriever"
    elif not tooling["docker"] or not tooling["docker_compose"] or not tooling["uv"]:
        next_step = "repair_local_tooling"
    elif not docker_daemon["ok"]:
        next_step = "start_docker_daemon"
    elif not repo_state["env_exists"]:
        next_step = "materialize_evermemos_env"
    elif not repo_state["venv_exists"]:
        next_step = "prepare_local_evermemos_boot"
    elif curl_probe["ok"] and not python_probe["ok"]:
        next_step = "investigate_python_localhost_policy"
    else:
        next_step = "hold_at_reachability_audit"

    status = "ok" if next_step == "rerun_witness_memory_retriever" else "attention_required"
    report = {
        "schema": "A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": status,
        "audit_only": True,
        "observer_only": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "source_family": "EverMemOS local backend bring-up path",
        "evermemos_repo_path": str(evermemos_repo),
        "health_url": health_url,
        "tooling": tooling,
        "repo_state": repo_state,
        "docker_daemon": docker_daemon,
        "health_probes": {
            "curl": curl_probe,
            "python": python_probe,
        },
        "current_ratchet_reports": {
            "sync_status": str(sync_report.get("status", "")),
            "retrieval_status": str(retrieval_report.get("status", "")),
            "retrieval_next_step": str(
                (retrieval_report.get("gate", {}) or {}).get("recommended_next_step", "")
            ),
        },
        "gate": {
            "allow_service_start_claims": False,
            "allow_bootstrap_claims": False,
            "allow_pimono_memory_claims": False,
            "allow_a2_replacement_claims": False,
            "recommended_next_step": next_step,
            "reason": (
                "local backend prerequisites and probes are aligned enough to rerun the bounded retriever"
                if next_step == "rerun_witness_memory_retriever"
                else "local backend preconditions are still incomplete, so hold at reachability audit instead of widening memory claims"
            ),
        },
        "recommended_next_actions": [
            "Keep this slice audit-only and environment-focused.",
            "Do not widen this result into startup bootstrap or broader EverMem integration claims.",
            "Use the recommended next step to decide whether to repair tooling, start Docker, prepare local boot, or rerun the retriever.",
        ],
        "non_goals": list(DEFAULT_NON_GOALS),
        "issues": issues,
    }
    packet = {
        "schema": "A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": status,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "health_url": health_url,
        "docker_daemon_ok": bool(docker_daemon["ok"]),
        "curl_health_ok": bool(curl_probe["ok"]),
        "python_health_ok": bool(python_probe["ok"]),
        "env_exists": bool(repo_state["env_exists"]),
        "venv_exists": bool(repo_state["venv_exists"]),
        "next_step": next_step,
        "issues": issues,
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    docker_daemon = report.get("docker_daemon", {})
    health = report.get("health_probes", {})
    curl_probe = health.get("curl", {})
    python_probe = health.get("python", {})
    repo_state = report.get("repo_state", {})
    lines = [
        "# EverMem Backend Reachability Audit Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- health_url: `{report.get('health_url', '')}`",
        f"- next_step: `{packet.get('next_step', '')}`",
        "",
        "## Local Repo State",
        f"- repo_exists: `{repo_state.get('repo_exists', False)}`",
        f"- env_template_exists: `{repo_state.get('env_template_exists', False)}`",
        f"- env_exists: `{repo_state.get('env_exists', False)}`",
        f"- venv_exists: `{repo_state.get('venv_exists', False)}`",
        f"- uv_lock_exists: `{repo_state.get('uv_lock_exists', False)}`",
        f"- docker_compose_file_exists: `{repo_state.get('docker_compose_file_exists', False)}`",
        "",
        "## Health Probes",
        f"- docker_daemon_ok: `{docker_daemon.get('ok', False)}`",
        f"- curl_health_ok: `{curl_probe.get('ok', False)}`",
        f"- python_health_ok: `{python_probe.get('ok', False)}`",
        f"- curl_error: `{curl_probe.get('stderr', '') or curl_probe.get('stdout', '')}`",
        f"- python_error: `{python_probe.get('error', '')}`",
        "",
        "## Current Ratchet Reports",
        f"- sync_status: `{report.get('current_ratchet_reports', {}).get('sync_status', '')}`",
        f"- retrieval_status: `{report.get('current_ratchet_reports', {}).get('retrieval_status', '')}`",
        f"- retrieval_next_step: `{report.get('current_ratchet_reports', {}).get('retrieval_next_step', '')}`",
    ]
    issues = report.get("issues", [])
    if issues:
        lines.extend(["", "## Issues"])
        for issue in issues:
            lines.append(f"- {issue}")
    return "\n".join(lines) + "\n"


def run_a2_evermem_backend_reachability_audit_operator(ctx: dict[str, Any]) -> dict[str, Any]:
    root = Path(ctx.get("repo_root", REPO_ROOT)).resolve()
    report, packet = build_a2_evermem_backend_reachability_audit_report(root, ctx)
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), DEFAULT_REPORT_JSON)
    md_path = _resolve_output_path(root, ctx.get("report_md_path"), DEFAULT_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), DEFAULT_PACKET_JSON)
    _write_json(report_path, report)
    _write_text(md_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)
    report["report_json_path"] = str(report_path)
    report["report_md_path"] = str(md_path)
    report["packet_path"] = str(packet_path)
    return report


if __name__ == "__main__":
    result = run_a2_evermem_backend_reachability_audit_operator({"repo_root": str(REPO_ROOT)})
    assert result["slice_id"] == SLICE_ID
    print("PASS: a2 evermem backend reachability audit operator self-test")
