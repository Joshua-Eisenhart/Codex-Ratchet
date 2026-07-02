#!/usr/bin/env python3
"""Run a bounded Wizard external child matrix.

This helper is intentionally receipt-first. A Codex parent calls it for one
route. It launches Claude child fanout for Opus, Sonnet, and Haiku, attempts a
bounded Gemini direct-API read-only child, and writes one parent-readable matrix
receipt. It must not shell out through the Gemini CLI; API keys are already
available in the shell environment and the CLI path can hang on auth/trust.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import ssl
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

try:
    import certifi
except Exception:  # pragma: no cover - optional dependency on some hosts.
    certifi = None

from wizard_topology import FORMAL_CHILDREN as V4_1_FORMAL_CHILDREN

try:
    from wizard_topology_v4_2 import FORMAL_CHILDREN as V4_2_FORMAL_CHILDREN
except Exception:
    V4_2_FORMAL_CHILDREN = {}

FORMAL_CHILDREN = {**V4_1_FORMAL_CHILDREN, **V4_2_FORMAL_CHILDREN}


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKET_ROOT_V4_1 = Path.home() / "wiki/wizard/packet-v4-1-current"
PACKET_ROOT_V4_2 = Path.home() / "wiki/wizard/packet-v4-2-current"
CANONICAL_CLAUDE_FANOUT = Path.home() / ".codex/skills/claude-bridge/scripts/claude_child_fanout.py"
HERMES_ENV_FILE = Path.home() / ".hermes/.env"
SHELL_ENV_FILE = Path.home() / ".zshrc"
SAFE_PROVIDER_KEY_NAMES = {
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "XAI_API_KEY",
    "GROK_API_KEY",
    "WIZARD_GEMINI_MODEL",
    "WIZARD_GROK_MODEL",
}


def ssl_context() -> ssl.SSLContext:
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def parse_named_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in SAFE_PROVIDER_KEY_NAMES:
            continue
        value = value.strip()
        try:
            parts = shlex.split(value, posix=True)
            if len(parts) == 1:
                value = parts[0]
        except Exception:
            value = value.strip("\"'")
        if value:
            values[key] = value
    return values


def key_from_env_or_files(names: tuple[str, ...], *, files: list[Path] | None = None) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    for path in files or [HERMES_ENV_FILE, SHELL_ENV_FILE]:
        parsed = parse_named_env_file(path)
        for name in names:
            value = parsed.get(name, "").strip()
            if value:
                return value
    return ""


def claude_python_executable() -> str:
    """Use a stable shell-visible Python for Claude CLI fanout."""
    configured = os.environ.get("WIZARD_CLAUDE_PYTHON", "").strip()
    if configured:
        return configured
    return shutil.which("python3") or sys.executable


def claude_bridge_path() -> Path:
    return CANONICAL_CLAUDE_FANOUT.with_name("claude_bridge.py")


def claude_auth_warmup(args: argparse.Namespace, model: str, out_dir: Path) -> dict[str, Any]:
    """Run a tiny direct bridge call to refresh Claude CLI auth state."""
    bridge_path = claude_bridge_path()
    if not bridge_path.exists():
        return {"status": "skipped", "reason": "missing_claude_bridge", "path": str(bridge_path)}
    warmup_dir = out_dir / "_auth_warmup" / model
    warmup_dir.mkdir(parents=True, exist_ok=True)
    command = [
        claude_python_executable(),
        str(bridge_path),
        "--model",
        model,
        "--effort",
        args.effort if hasattr(args, "effort") else "high",
        "--budget",
        "0.05",
        "--timeout-sec",
        "45",
        "--cwd",
        args.cwd,
        "--out-dir",
        str(warmup_dir),
        "--name",
        f"{slug(args.route)}-{model}-auth-warmup",
        "--prompt",
        "Return YAML only: id: claude_auth_warmup status: accepted conclusion: auth_ready",
    ]
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return {
        "status": "completed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "stdout_preview": completed.stdout[:1000],
    }


def has_claude_auth_failure(receipt: dict[str, Any]) -> bool:
    """Detect the fast Claude CLI auth-cache failure seen under fanout pressure."""
    text = json.dumps(receipt, ensure_ascii=False)
    return "Not logged in" in text or "Please run /login" in text


def nested_claude_auth_probe(args: argparse.Namespace, model: str, group_dir: Path) -> dict[str, Any]:
    """Fast preflight for the current Python process tree's Claude auth visibility."""
    if os.environ.get("WIZARD_SKIP_NESTED_CLAUDE_PROBE", "").strip() == "1":
        return {"status": "skipped", "reason": "WIZARD_SKIP_NESTED_CLAUDE_PROBE=1"}
    probe_dir = group_dir / "_nested_auth_probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    command = [
        claude_python_executable(),
        str(claude_bridge_path()),
        "--model",
        model,
        "--effort",
        "high",
        "--budget",
        "0.05",
        "--timeout-sec",
        "20",
        "--cwd",
        args.cwd,
        "--out-dir",
        str(probe_dir),
        "--name",
        f"{slug(args.route)}-{model}-nested-auth-probe",
        "--prompt",
        "Return OK only.",
    ]
    started = now_iso()
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    finished = now_iso()
    parsed: dict[str, Any] = {}
    try:
        candidate = json.loads(completed.stdout)
        if isinstance(candidate, dict):
            parsed = candidate
    except json.JSONDecodeError:
        pass
    blocked = completed.returncode != 0 and ("Not logged in" in completed.stdout or "Please run /login" in completed.stdout)
    return {
        "status": "blocked" if blocked else "accepted" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "started_at": started,
        "completed_at": finished,
        "receipt_path": parsed.get("receipt_path"),
        "output_path": parsed.get("output_path"),
        "stdout_preview": completed.stdout[:1000],
        "blocked_reason": "nested_claude_auth_not_visible" if blocked else None,
    }


def bridge_child_result(
    job: dict[str, str],
    *,
    started_at: datetime,
    completed_at: datetime,
    raw: str,
    returncode: int,
    wrapper_timed_out: bool = False,
) -> dict[str, Any]:
    parsed_receipt: dict[str, Any] = {}
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            parsed_receipt = parsed
    except json.JSONDecodeError:
        pass
    bridge_timed_out = bool(parsed_receipt.get("timed_out"))
    parsed = parsed_receipt.get("parsed") if isinstance(parsed_receipt.get("parsed"), dict) else {}
    status = (
        "completed"
        if returncode == 0 and not bridge_timed_out and not wrapper_timed_out
        else "timed_out"
        if returncode == 124 or bridge_timed_out or wrapper_timed_out
        else "failed"
    )
    return {
        "id": job["id"],
        "status": status,
        "returncode": returncode,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "duration_ms": int((completed_at - started_at).total_seconds() * 1000),
        "bridge_receipt_path": parsed_receipt.get("receipt_path"),
        "bridge_output_path": parsed_receipt.get("output_path"),
        "model": parsed_receipt.get("model"),
        "cost_usd": parsed.get("total_cost_usd"),
        "result_preview": str(parsed.get("result_preview") or "")[:800],
        "raw_preview": raw[:800],
    }


def run_direct_bridge_group(
    *,
    args: argparse.Namespace,
    model: str,
    jobs: list[dict[str, str]],
    timeout_sec: float,
    budget: float,
    group_dir: Path,
    name_suffix: str,
) -> dict[str, Any]:
    """Fallback around fanout when direct Claude Bridge works but fanout auth fails."""
    bridge_path = claude_bridge_path()
    run_dir = group_dir / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{slug(args.route)}-{model}{name_suffix}"
    child_root = run_dir / "children"
    child_root.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc)
    children: list[dict[str, Any]] = []
    for job in jobs:
        child_dir = child_root / slug(job["id"])
        child_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = child_dir / "prompt.txt"
        prompt_path.write_text(job["prompt"].rstrip() + "\n", encoding="utf-8")
        command = [
            claude_python_executable(),
            str(bridge_path),
            "--model",
            model,
            "--effort",
            "high",
            "--budget",
            str(budget),
            "--timeout-sec",
            str(timeout_sec),
            "--cwd",
            args.cwd,
            "--out-dir",
            str(child_dir),
            "--name",
            job["id"],
            "--prompt-file",
            str(prompt_path),
        ]
        child_started = datetime.now(timezone.utc)
        attempts: list[dict[str, Any]] = []
        raw = ""
        returncode = 1
        wrapper_timed_out = False
        for attempt in range(1, 4):
            attempt_started = datetime.now(timezone.utc)
            try:
                completed = subprocess.run(
                    command,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                    timeout=timeout_sec + 15,
                )
                raw = completed.stdout
                returncode = completed.returncode
                wrapper_timed_out = False
            except subprocess.TimeoutExpired as exc:
                raw = exc.stdout or ""
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8", errors="replace")
                raw += f"\n[WRAPPER TIMEOUT after {timeout_sec + 15}s]\n"
                returncode = 124
                wrapper_timed_out = True
            attempt_completed = datetime.now(timezone.utc)
            auth_transient = "Not logged in" in raw or "Please run /login" in raw
            attempts.append(
                {
                    "attempt": attempt,
                    "started_at": attempt_started.isoformat(),
                    "completed_at": attempt_completed.isoformat(),
                    "returncode": returncode,
                    "wrapper_timed_out": wrapper_timed_out,
                    "auth_transient": auth_transient,
                    "stdout_preview": raw[:300],
                }
            )
            if returncode == 0 or not auth_transient or attempt == 3:
                break
            time.sleep(15 * attempt)
        child_completed = datetime.now(timezone.utc)
        (child_dir / "direct_bridge_stdout.json").write_text(raw, encoding="utf-8", errors="replace")
        child = bridge_child_result(
            job,
            started_at=child_started,
            completed_at=child_completed,
            raw=raw,
            returncode=returncode,
            wrapper_timed_out=wrapper_timed_out,
        )
        child["direct_bridge_attempts"] = attempts
        children.append(child)
    completed_at = datetime.now(timezone.utc)
    counts = {
        "completed": sum(1 for child in children if child["status"] == "completed"),
        "failed": sum(1 for child in children if child["status"] == "failed"),
        "timed_out": sum(1 for child in children if child["status"] == "timed_out"),
        "abandoned": 0,
        "not_launched": 0,
        "total": len(children),
    }
    receipt = {
        "route": f"{slug(args.route)}-{model}{name_suffix}",
        "status": "completed" if counts["completed"] == len(jobs) else "partial" if counts["completed"] else "failed",
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "duration_ms": int((completed_at - started_at).total_seconds() * 1000),
        "model": model,
        "effort": "high",
        "timeout_sec": timeout_sec,
        "budget": budget,
        "direct_bridge_fallback": True,
        "counts": counts,
        "children": sorted(children, key=lambda child: child["id"]),
    }
    receipt_path = run_dir / "direct_bridge_receipt.json"
    receipt["receipt_path"] = str(receipt_path)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def packet_root_for_route(route: str) -> Path:
    if route in V4_2_FORMAL_CHILDREN:
        return PACKET_ROOT_V4_2
    return PACKET_ROOT_V4_1

def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", text.strip()).strip("-")[:80] or "route"


def claude_fanout_path() -> tuple[Path, str]:
    """Use the runtime-installed bridge when available; keep packet copy as fallback."""
    if CANONICAL_CLAUDE_FANOUT.exists():
        return CANONICAL_CLAUDE_FANOUT, "canonical_codex_skill"
    return PACKET_ROOT_V4_2 / "skills/claude-bridge/scripts/claude_child_fanout.py", "packet_local_v4_2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Wizard v4.2 child model matrix for one parent route.")
    parser.add_argument("--route", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--followup-prompt", required=True)
    parser.add_argument("--payoff", required=True)
    parser.add_argument("--use-when", required=True)
    parser.add_argument("--stop-if", required=True)
    parser.add_argument("--boundary", required=True)
    parser.add_argument("--cwd", default=str(REPO_ROOT))
    parser.add_argument("--out-dir", default="/tmp/wizard_v4_2_child_matrix")
    parser.add_argument("--sonnet-count", type=int, default=0, help="Sonnet child count. Defaults to the full formal route obligation, or 6 for generic routes.")
    parser.add_argument("--opus-count", type=int, default=0, help="Opus child count. Defaults to one; with --full-model-council, defaults to the full formal route obligation.")
    parser.add_argument("--haiku-count", type=int, default=1, help="Haiku child count. Set 0 for long Sonnet-first loops.")
    parser.add_argument("--full-model-council", action="store_true", help="For each parent route, ask each Claude model family to cover the full active formal child obligation.")
    parser.add_argument("--only-children", default="", help="Comma-separated formal child ids to run for a narrow repair.")
    parser.add_argument("--sonnet-timeout-sec", type=float, default=260.0)
    parser.add_argument("--opus-timeout-sec", type=float, default=320.0)
    parser.add_argument("--haiku-timeout-sec", type=float, default=160.0)
    parser.add_argument("--gemini-timeout-sec", type=float, default=90.0)
    parser.add_argument("--grok-timeout-sec", type=float, default=90.0)
    parser.add_argument("--sonnet-budget", type=float, default=1.5)
    parser.add_argument("--opus-budget", type=float, default=2.0)
    parser.add_argument("--haiku-budget", type=float, default=0.5)
    parser.add_argument("--global-max-active", type=int, default=8)
    parser.add_argument("--max-concurrency", type=int, default=4)
    parser.add_argument("--parallel-model-groups", action="store_true", help="Run Sonnet/Opus/Haiku groups concurrently inside one parent. Off by default to avoid Claude socket pressure in long full loops.")
    parser.add_argument("--codex-local-children", action="store_true", help="Generate bounded local Codex child receipts instead of launching Claude children. Intended for compact diagnostics when external model quota is exhausted.")
    parser.add_argument("--skip-claude-groups", action="store_true", help="Run only non-Claude provider lanes such as Gemini direct API. Intended for provider health checks.")
    parser.add_argument("--attempt-gemini", action="store_true", help="Actually launch Gemini through the direct API. Default is degraded-safe to avoid provider hangs.")
    parser.add_argument("--attempt-grok", action="store_true", help="Actually launch Grok through the direct xAI API. Default is degraded-safe to avoid provider hangs.")
    parser.add_argument("--rescore-existing", help="Existing route timestamp directory containing fanout receipts; rescore without launching children.")
    parser.add_argument("--run-id", default="", help="Shared Wizard run id. Required by full-run harness to prevent mixed-run FULL claims.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_receipt(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"load_error": str(exc), "receipt_path": str(path)}


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout, context=ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def gemini_api_key() -> str:
    return key_from_env_or_files(("GEMINI_API_KEY", "GOOGLE_API_KEY"))


def grok_api_key() -> str:
    return key_from_env_or_files(("XAI_API_KEY", "GROK_API_KEY"))


def extract_gemini_text(raw: Any) -> str:
    try:
        parts = raw["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError):
        return ""
    return "\n".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()


def load_child_result_text(child: dict[str, Any]) -> str:
    output_path = child.get("bridge_output_path") or child.get("output_path")
    if output_path:
        try:
            output_data = json.loads(Path(str(output_path)).read_text(encoding="utf-8", errors="replace"))
            if isinstance(output_data, dict):
                result = output_data.get("result")
                if result:
                    return str(result)
                text = output_data.get("text")
                if text:
                    return str(text)
        except Exception:
            pass
    receipt_path = child.get("bridge_receipt_path")
    if receipt_path:
        try:
            receipt_data = json.loads(Path(str(receipt_path)).read_text(encoding="utf-8", errors="replace"))
            parsed = receipt_data.get("parsed") if isinstance(receipt_data, dict) else {}
            if isinstance(parsed, dict) and parsed.get("result_preview"):
                return str(parsed.get("result_preview"))
        except Exception:
            pass
    return str(child.get("result_preview") or child.get("raw_preview") or "")


def parse_child_yaml(text: str) -> Any:
    stripped = text.strip()
    fenced = re.search(r"```(?:yaml|yml)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        stripped = fenced.group(1).strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return yaml.safe_load(stripped)
    except Exception:
        repaired = []
        def needs_scalar_quote(value: str) -> bool:
            value = value.strip()
            if not value or value[0] in "|>{[":
                return False
            if (value[0] == value[-1] and value[0] in {"'", '"'}) or value in {"[]", "{}"}:
                return False
            return ":" in value or value.startswith(("'", '"'))

        for line in stripped.splitlines():
            if re.match(r"^\s*[A-Za-z0-9_.-]+:\s+.*$", line):
                indent, key, value = re.match(r"^(\s*)([A-Za-z0-9_.-]+):\s+(.*)$", line).groups()
                repaired.append(f"{indent}{key}: {json.dumps(value)}" if needs_scalar_quote(value) else line)
            elif re.match(r"^\s*-\s+[A-Za-z0-9_.-]+:\s+.*$", line):
                indent, key, value = re.match(r"^(\s*-\s+)([A-Za-z0-9_.-]+):\s+(.*)$", line).groups()
                repaired.append(f"{indent}{key}: {json.dumps(value)}" if needs_scalar_quote(value) else line)
            else:
                repaired.append(line)
        try:
            return yaml.safe_load("\n".join(repaired))
        except Exception:
            return None


def nonempty_value(data: Any, field: str) -> bool:
    if not isinstance(data, dict) or field not in data:
        return False
    value = data.get(field)
    if value is None:
        return False
    if isinstance(value, str):
        stripped = value.strip()
        return bool(stripped) and stripped.lower() != field.lower()
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def present_value(data: Any, field: str) -> bool:
    if not isinstance(data, dict) or field not in data:
        return False
    value = data.get(field)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() != field.lower()
    return True


def premortem_novelty_structured(data: Any) -> bool:
    if isinstance(data, dict) and "premortem" in data and isinstance(data["premortem"], dict):
        data = data["premortem"]
    if not isinstance(data, dict):
        return False
    count = data.get("novel_findings_count")
    try:
        if isinstance(count, str):
            return False
        if int(count) <= 0:
            return False
    except Exception:
        return False
    reasons = data.get("novel_failure_reasons")
    if not isinstance(reasons, list) or not reasons:
        return False
    dives = data.get("deep_dives")
    if not isinstance(dives, list) or not dives:
        return False
    for dive in dives:
        if not isinstance(dive, dict):
            return False
        novelty = str(dive.get("novelty") or "").strip().lower()
        if novelty and novelty not in {"repeated", "user_named_only", "none", "not_novel"}:
            return True
    return False


def premortem_deep_dive_fields_ok(data: Any) -> bool:
    if isinstance(data, dict) and "premortem" in data and isinstance(data["premortem"], dict):
        data = data["premortem"]
    if not isinstance(data, dict):
        return False
    dives = data.get("deep_dives")
    if not isinstance(dives, list) or not dives:
        return False
    required = ("failure_story", "hidden_assumption", "early_warning_signs", "prevention")
    return any(isinstance(dive, dict) and all(nonempty_value(dive, field) for field in required) for dive in dives)


def formal_children_for(route: str) -> list[str]:
    return FORMAL_CHILDREN.get(route, [])


def selected_formal_children(args: argparse.Namespace, formal_children: list[str]) -> list[str]:
    if not args.only_children.strip():
        return formal_children
    selected = [child.strip() for child in args.only_children.split(",") if child.strip()]
    unknown = [child for child in selected if child not in formal_children]
    if unknown:
        raise ValueError(f"unknown formal children for {args.route}: {', '.join(unknown)}")
    return selected


def is_premortem_child_id(child_id: str) -> bool:
    return child_id == "skill.premortem" or "skill.premortem" in child_id or "skill-premortem" in child_id or child_id.startswith("premortem.")


def is_loophole_child_id(child_id: str) -> bool:
    return child_id == "skill.loophole_auditor" or "skill.loophole_auditor" in child_id or "skill-loophole-auditor" in child_id or child_id.startswith("loophole.")


def specialist_opus_children(route: str, active_formal_children: list[str]) -> list[str]:
    if route in {"failure.premortem_council", "failure.premortem"}:
        return [child for child in active_formal_children if is_premortem_child_id(child)]
    if route in {"failure.loophole_auditor_council", "failure.loophole_auditor"}:
        return [child for child in active_formal_children if is_loophole_child_id(child)]
    return []


def asymmetric_model_role_specs(
    *,
    route: str,
    roles: list[str],
    active_formal_children: list[str],
    full_model_council: bool,
    sonnet_count: int,
    opus_count: int,
    haiku_count: int,
) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {
        "sonnet": {"count": sonnet_count, "roles": roles},
        "opus": {
            "count": opus_count,
            "roles": roles
            if full_model_council
            else [
                active_formal_children[0]
                if active_formal_children
                else
                "premortem.skill_opus"
                if route in {"failure.premortem_council", "failure.premortem"}
                else "loophole.skill_opus"
                if route in {"failure.loophole_auditor_council", "failure.loophole_auditor"}
                else "arbitration and hard-boundary check"
            ],
        },
        "haiku": {
            "count": haiku_count,
            "roles": roles if full_model_council else [active_formal_children[0] if active_formal_children else "inventory and liveness check"],
        },
    }
    delegated = specialist_opus_children(route, active_formal_children)
    if delegated and not full_model_council and opus_count > 0:
        sonnet_roles = [role for role in roles if role not in delegated]
        if sonnet_roles:
            specs["sonnet"] = {
                "count": min(sonnet_count, len(sonnet_roles)),
                "roles": sonnet_roles,
            }
            specs["opus"] = {
                "count": min(max(opus_count, len(delegated)), len(delegated)),
                "roles": delegated,
            }
    return specs


def blocking_usefulness_failures(groups: list[dict[str, Any]], formal_completed: list[str], active_formal_children: list[str]) -> list[dict[str, Any]]:
    def child_aliases(child: str) -> set[str]:
        base = slug(child).lower()
        return {base, base.replace(".", "-").replace("_", "-")}

    completed_slugs = {alias for child in formal_completed for alias in child_aliases(child)}
    formal_slugs = {alias for child in active_formal_children for alias in child_aliases(child)}
    blockers: list[dict[str, Any]] = []
    for group in groups:
        for failure in group.get("usefulness_failures") or []:
            child_id = str(failure.get("id") or "").lower()
            matched_formal = [formal_slug for formal_slug in formal_slugs if formal_slug in child_id]
            if matched_formal and all(formal_slug in completed_slugs for formal_slug in matched_formal):
                continue
            blockers.append(failure)
    return blockers


def mini_mmm_hint(child_id: str) -> str:
    if child_id.startswith("voice."):
        name = child_id.split(".", 1)[1].upper()
        return f"mmm/mini/full/voices/md/MMM_VOICE_{name}_FULL_v4_1.md or sparse registry fallback"
    if child_id.startswith("lane."):
        name = child_id.split(".", 1)[1].upper()
        return f"mmm/mini/full/lanes/md/MMM_LANE_{name}_FULL_v4_1.md or sparse registry fallback"
    if child_id.startswith("guard."):
        name = child_id.split(".", 1)[1].upper()
        return f"mmm/mini/full/checks_guards/md/MMM_CHECK_GUARD_{name}_FULL_v4_1.md or sparse registry fallback"
    if child_id.startswith("manager."):
        return "mmm/mini/MEMBER_MINI_MMM_REGISTRY_v4_2.md management slice plus WIZARD_v4_2 management receipt contract"
    return "sparse registry slice plus definition row"


def child_prompt(args: argparse.Namespace, child_id: str, role: str) -> str:
    packet_root = packet_root_for_route(args.route)
    premortem_skill = packet_root / "skills/premortem/SKILL.md"
    loophole_skill = packet_root / "skills/council-members/loophole-auditor/SKILL.md"
    premortem_contract = ""
    if is_premortem_child_id(child_id):
        premortem_contract = (
            f"\nPacket-local Premortem skill: {premortem_skill}\n"
            "You MUST follow that skill. Do not output docs, reports, a web UI, browser actions, or a web page. "
            "Return only the requested receipt YAML. Include top-level premortem with user_named_issues, "
            "novel_failure_reasons, novel_findings_count, and deep_dives. Each deep_dive MUST include "
            "novelty, failure_story, hidden_assumption, early_warning_signs, and prevention. "
            "novel_findings_count MUST be a positive integer. A premortem that only repeats issues already named by the user/controller is invalid. "
            "Do not merely mention novel_findings_count in prose; emit it as the exact YAML key premortem.novel_findings_count. "
            "Use this exact nested shape:\n"
            "premortem:\n"
            "  user_named_issues: [\"issue\"]\n"
            "  novel_failure_reasons: [\"novel failure\"]\n"
            "  novel_findings_count: 1\n"
            "  deep_dives:\n"
            "    - novelty: \"why this is not just a user-named issue\"\n"
            "      failure_story: \"how the failure unfolds\"\n"
            "      hidden_assumption: \"assumption exposed\"\n"
            "      early_warning_signs: [\"observable signal\"]\n"
            "      prevention: \"specific prevention\"\n"
        )
    loophole_contract = ""
    if is_loophole_child_id(child_id):
        loophole_contract = (
            f"\nPacket-local Loophole Auditor skill: {loophole_skill}\n"
            "You MUST follow that skill. Interpret 100% confidence as no known unresolved loophole under the declared evidence standard, not literal omniscience. "
            "Return only the requested receipt YAML. Include top-level loophole_audit, confidence_status, and stop_condition. "
            "loophole_audit MUST include strategy_under_test, evidence_standard, loopholes_found, fixes_applied, verification_result, and unresolved_loopholes. "
            "loopholes_found and unresolved_loopholes may be empty lists when none are found; fixes_applied MUST be a non-empty list. "
            "If this read-only child cannot apply fixes, include proposed_fix/not_applied_read_only entries with the exact gate or prompt change needed. "
            "Set status: accepted when the receipt is complete under the declared evidence boundary; do not mark it partial only because the work is read-only.\n"
        )
    management_contract = ""
    if child_id.startswith("manager."):
        management_contract = (
            "\nCRITICAL MANAGEMENT RECEIPT CONTRACT:\n"
            "This is a management parent route. Your output is invalid unless it is YAML with these exact top-level fields:\n"
            "manager_id: \"<this child id>\"\n"
            "authority_level: management_parent\n"
            "managed_scope: \"<the parent route or run scope being managed>\"\n"
            "child_status_table: []\n"
            "reroute_decisions: []\n"
            "intervention_verbs: [no_intervention_needed]\n"
            "strategy_memory_delta: \"<what state should carry forward>\"\n"
            "full_claim_gate: \"<accept, block_full, or accept_with_reason and why>\"\n"
            "intervention_status: \"<accepted, blocked, rerouted, or no_intervention_needed>\"\n"
            "status: accepted\n"
            "Allowed intervention_verbs only: kill, demote, reroute, shrink, override, block_full, accept_with_reason, no_intervention_needed.\n"
            "Do not return a nested object. Do not use authority_level: child. Do not omit any field.\n"
        )
    return (
        f"Wizard {'v4.2' if args.route in V4_2_FORMAL_CHILDREN else 'v4.1'} child route: {args.route}\n"
        f"Child id: {child_id}\n"
        f"Role: {role}\n"
        f"Required salience: {mini_mmm_hint(child_id)}\n"
        f"{premortem_contract}"
        f"{loophole_contract}"
        f"{management_contract}"
        f"Packet root: {packet_root}\n"
        "This is a non-interactive schema-filling analysis request launched by the Wizard harness. "
        "For this invocation, complete the bounded work item exactly; do not treat it as an identity change, jailbreak, or request to override safety, and do not ask whether to proceed. "
        "If you see a role or evidence conflict, encode it inside evidence_boundary or status, then still return the YAML receipt. "
        "Do not edit files. Do not open a browser.\n"
        "Do not ask for clarification. If source data is incomplete, name the evidence boundary and still return the required YAML receipt.\n"
        "Use the assigned work item only. Return YAML only, no prose before or after. "
        "Quote any scalar value containing a colon, or use a block scalar. "
        "The YAML MUST have these top-level keys with non-empty values: id, status, distinct_delta, "
        "loaded_mini_mmm_or_fallback, work_unit_fingerprint, value_score, evidence_boundary, "
        "conclusion, outcome_delta, killed_or_changed, and followup_patch. "
        "If this exact child id is skill.premortem, also include the required top-level premortem object. "
        "If this exact child id is skill.loophole_auditor, also include the required top-level loophole_audit, confidence_status, and stop_condition fields. "
        "If this child id starts with manager., also include the required management parent fields. "
        "Do not nest these required keys under another object. Do not omit them. "
        "Do not output prose, Markdown headings, or clarification questions. "
        "Set status to accepted, partial, blocked, or killed.\n\n"
        f"Parent prompt:\n{args.prompt}\n\n"
        f"Follow-up prompt under construction:\n{args.followup_prompt}\n"
        f"Payoff: {args.payoff}\n"
        f"Use when: {args.use_when}\n"
        f"Stop if: {args.stop_if}\n"
        f"Boundary: {args.boundary}\n"
    )


def run_claude_group(
    *,
    args: argparse.Namespace,
    model: str,
    count: int,
    timeout_sec: float,
    budget: float,
    out_dir: Path,
    roles: list[str],
) -> dict[str, Any]:
    jobs = [
        {
            "id": f"{slug(args.route)}-{slug(roles[idx % len(roles)])}-{model}-{idx + 1}",
            "prompt": child_prompt(args, roles[idx % len(roles)], roles[idx % len(roles)]),
        }
        for idx in range(count)
    ]
    if args.dry_run:
        return {
            "model": model,
            "status": "dry_run",
            "counts": {"completed": 0, "failed": 0, "timed_out": 0, "total": len(jobs)},
            "jobs": jobs,
        }
    group_dir = out_dir / model
    group_dir.mkdir(parents=True, exist_ok=True)
    jobs_file = group_dir / "jobs.json"
    jobs_file.write_text(json.dumps(jobs, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fanout_path, fanout_source = claude_fanout_path()
    packet_root = packet_root_for_route(args.route)
    packet_fanout_path = packet_root / "skills/claude-bridge/scripts/claude_child_fanout.py"

    auth_probe = nested_claude_auth_probe(args, model, group_dir)
    if auth_probe.get("status") == "blocked":
        return {
            "model": model,
            "status": "blocked",
            "returncode": 1,
            "claude_fanout_path": str(fanout_path),
            "claude_fanout_source": fanout_source,
            "claude_launch_mode": "blocked_by_nested_auth_probe",
            "packet_root": str(packet_root),
            "packet_claude_fanout_path": str(packet_fanout_path),
            "jobs_file": str(jobs_file),
            "started_at": auth_probe.get("started_at"),
            "completed_at": auth_probe.get("completed_at"),
            "retry_reason": "nested_claude_auth_not_visible",
            "retry_warmup": None,
            "retry_started_at": None,
            "retry_completed_at": None,
            "auth_probe": auth_probe,
            "auth_fallback": {
                "reason": "nested_claude_auth_not_visible",
                "action": "blocked_fast_do_not_launch_children_from_python_process_tree",
                "top_level_claude_bridge_note": "Top-level Codex exec_command Claude Bridge may still work, but it is not proof that Wizard Python child launch works.",
            },
            "receipt_path": auth_probe.get("receipt_path"),
            "stdout_preview": str(auth_probe.get("stdout_preview") or "")[:1000],
            "completed_child_ids": [],
            "completed_child_receipt_paths": [],
            "usefulness_failures": [
                {
                    "id": job["id"],
                    "status": "not_launched",
                    "reason": "nested_claude_auth_not_visible",
                    "receipt_path": auth_probe.get("receipt_path"),
                }
                for job in jobs
            ],
            "counts": {
                "completed": 0,
                "process_completed": 0,
                "failed": 0,
                "timed_out": 0,
                "abandoned": 0,
                "not_launched": len(jobs),
                "total": len(jobs),
            },
        }

    direct_primary = run_direct_bridge_group(
        args=args,
        model=model,
        jobs=jobs,
        timeout_sec=timeout_sec,
        budget=budget,
        group_dir=group_dir,
        name_suffix="-direct-bridge-primary",
    )
    direct_children = direct_primary.get("children") if isinstance(direct_primary.get("children"), list) else []
    direct_useful_children = [child for child in direct_children if child_is_useful(child)]
    if direct_useful_children:
        direct_counts = direct_primary.get("counts") or {}
        completed_child_ids = [str(child.get("id")) for child in direct_useful_children]
        completed_paths = [
            str(child.get("bridge_receipt_path"))
            for child in direct_useful_children
            if child.get("bridge_receipt_path")
        ]
        usefulness_failures = [
            {
                "id": str(child.get("id")),
                "status": child.get("status"),
                "reason": child_usefulness_failure_reason(child),
                "receipt_path": child.get("bridge_receipt_path"),
            }
            for child in direct_children
            if isinstance(child, dict) and not child_is_useful(child)
        ]
        return {
            "model": model,
            "status": "completed",
            "returncode": 0,
            "claude_fanout_path": str(fanout_path),
            "claude_fanout_source": fanout_source,
            "claude_launch_mode": "direct_bridge_primary",
            "packet_root": str(packet_root),
            "packet_claude_fanout_path": str(packet_fanout_path),
            "jobs_file": str(jobs_file),
            "started_at": direct_primary.get("started_at"),
            "completed_at": direct_primary.get("completed_at"),
            "retry_reason": None,
            "retry_warmup": None,
            "retry_started_at": None,
            "retry_completed_at": None,
            "auth_fallback": None,
            "receipt_path": str(direct_primary.get("receipt_path")),
            "stdout_preview": json.dumps(
                {
                    "direct_bridge_primary": True,
                    "receipt_path": direct_primary.get("receipt_path"),
                    "counts": direct_counts,
                },
                sort_keys=True,
            ),
            "completed_child_ids": completed_child_ids,
            "completed_child_receipt_paths": completed_paths,
            "usefulness_failures": usefulness_failures,
            "counts": {
                "completed": len(direct_useful_children),
                "process_completed": int(direct_counts.get("completed") or 0),
                "failed": int(direct_counts.get("failed") or 0),
                "timed_out": int(direct_counts.get("timed_out") or 0),
                "abandoned": int(direct_counts.get("abandoned") or 0),
                "not_launched": int(direct_counts.get("not_launched") or 0),
                "total": int(direct_counts.get("total") or count),
            },
        }

    def fanout_command(*, max_concurrency: int | None = None, global_max_active: int | None = None, name_suffix: str = "") -> list[str]:
        return [
            claude_python_executable(),
            str(fanout_path),
            "--jobs-file",
            str(jobs_file),
            "--model",
            model,
            "--effort",
            "high",
            "--budget",
            str(budget),
            "--timeout-sec",
            str(timeout_sec),
            "--max-concurrency",
            str(max_concurrency if max_concurrency is not None else args.max_concurrency),
            "--global-max-active",
            str(global_max_active if global_max_active is not None else args.global_max_active),
            "--cwd",
            args.cwd,
            "--out-dir",
            str(group_dir),
            "--name",
            f"{slug(args.route)}-{model}{name_suffix}",
        ]

    command = fanout_command()
    started = now_iso()
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    finished = now_iso()
    group_returncode = completed.returncode
    group_stdout_preview = completed.stdout[:1000]
    receipt = {}
    try:
        parsed_stdout = json.loads(completed.stdout)
        if isinstance(parsed_stdout, dict) and "children" in parsed_stdout:
            receipt = parsed_stdout
    except json.JSONDecodeError:
        pass
    receipt_path = None
    receipt_paths = sorted(group_dir.rglob("fanout_receipt.json"), key=lambda path: path.stat().st_mtime)
    if receipt_paths:
        receipt_path = receipt_paths[-1]
        receipt = load_receipt(receipt_path)
    counts = receipt.get("counts") or {}
    children = receipt.get("children") if isinstance(receipt.get("children"), list) else []
    retry_reason = None
    retry_warmup = None
    retry_started = None
    retry_finished = None
    auth_fallback = None
    if int(counts.get("completed") or 0) == 0 and has_claude_auth_failure(receipt):
        retry_reason = "claude_auth_cache_transient_not_logged_in"
        retry_warmup = claude_auth_warmup(args, model, group_dir)
        time.sleep(2)
        retry_started = now_iso()
        completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        retry_finished = now_iso()
        group_returncode = completed.returncode
        group_stdout_preview = completed.stdout[:1000]
        try:
            parsed_stdout = json.loads(completed.stdout)
            if isinstance(parsed_stdout, dict) and "children" in parsed_stdout:
                receipt = parsed_stdout
        except json.JSONDecodeError:
            pass
        receipt_paths = sorted(group_dir.rglob("fanout_receipt.json"), key=lambda path: path.stat().st_mtime)
        if receipt_paths:
            receipt_path = receipt_paths[-1]
            receipt = load_receipt(receipt_path)
        counts = receipt.get("counts") or {}
        children = receipt.get("children") if isinstance(receipt.get("children"), list) else []
    if int(counts.get("completed") or 0) == 0 and has_claude_auth_failure(receipt):
        auth_fallback = {
            "reason": "parallel_auth_retry_still_not_logged_in",
            "action": "cooldown_then_serialized_fanout",
            "cooldown_sec": 8,
            "max_concurrency": 1,
            "global_max_active": 1,
        }
        time.sleep(8)
        fallback_command = fanout_command(max_concurrency=1, global_max_active=1, name_suffix="-auth-serialized")
        fallback_started = now_iso()
        completed = subprocess.run(fallback_command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        fallback_finished = now_iso()
        group_returncode = completed.returncode
        group_stdout_preview = completed.stdout[:1000]
        auth_fallback["started_at"] = fallback_started
        auth_fallback["completed_at"] = fallback_finished
        auth_fallback["returncode"] = completed.returncode
        auth_fallback["stdout_preview"] = completed.stdout[:1000]
        try:
            parsed_stdout = json.loads(completed.stdout)
            if isinstance(parsed_stdout, dict) and "children" in parsed_stdout:
                receipt = parsed_stdout
        except json.JSONDecodeError:
            pass
        receipt_paths = sorted(group_dir.rglob("fanout_receipt.json"), key=lambda path: path.stat().st_mtime)
        if receipt_paths:
            receipt_path = receipt_paths[-1]
            receipt = load_receipt(receipt_path)
        counts = receipt.get("counts") or {}
        children = receipt.get("children") if isinstance(receipt.get("children"), list) else []
    if int(counts.get("completed") or 0) == 0 and has_claude_auth_failure(receipt):
        direct_receipt = run_direct_bridge_group(
            args=args,
            model=model,
            jobs=jobs,
            timeout_sec=timeout_sec,
            budget=budget,
            group_dir=group_dir,
            name_suffix="-direct-bridge-auth-fallback",
        )
        if auth_fallback is None:
            auth_fallback = {
                "reason": "fanout_auth_not_logged_in",
                "action": "direct_bridge_fallback",
            }
        else:
            auth_fallback["direct_bridge_action"] = "direct_bridge_fallback"
        auth_fallback["direct_bridge_receipt_path"] = direct_receipt.get("receipt_path")
        auth_fallback["direct_bridge_status"] = direct_receipt.get("status")
        auth_fallback["direct_bridge_counts"] = direct_receipt.get("counts")
        receipt = direct_receipt
        receipt_path = Path(str(direct_receipt["receipt_path"]))
        counts = receipt.get("counts") or {}
        children = receipt.get("children") if isinstance(receipt.get("children"), list) else []
        group_returncode = 0 if int(counts.get("completed") or 0) > 0 else 1
        group_stdout_preview = json.dumps(
            {
                "direct_bridge_fallback": True,
                "receipt_path": direct_receipt.get("receipt_path"),
                "counts": counts,
            },
            sort_keys=True,
        )
    useful_children = [child for child in children if child_is_useful(child)]
    completed_child_ids = [str(child.get("id")) for child in useful_children]
    completed_paths = [
        str(child.get("bridge_receipt_path"))
        for child in useful_children
        if child.get("bridge_receipt_path")
    ]
    usefulness_failures = [
        {
            "id": str(child.get("id")),
            "status": child.get("status"),
            "reason": child_usefulness_failure_reason(child),
            "receipt_path": child.get("bridge_receipt_path"),
        }
        for child in children
        if isinstance(child, dict) and not child_is_useful(child)
    ]
    return {
        "model": model,
        "status": "completed" if group_returncode == 0 else "failed",
        "returncode": group_returncode,
        "claude_fanout_path": str(fanout_path),
        "claude_fanout_source": fanout_source,
        "packet_root": str(packet_root),
        "packet_claude_fanout_path": str(packet_fanout_path),
        "jobs_file": str(jobs_file),
        "started_at": started,
        "completed_at": finished,
        "retry_reason": retry_reason,
        "retry_warmup": retry_warmup,
        "retry_started_at": retry_started,
        "retry_completed_at": retry_finished,
        "auth_fallback": auth_fallback,
        "receipt_path": str(receipt_path) if receipt_path else None,
        "stdout_preview": group_stdout_preview,
        "completed_child_ids": completed_child_ids,
        "completed_child_receipt_paths": completed_paths,
        "usefulness_failures": usefulness_failures,
        "counts": {
            "completed": len(useful_children),
            "process_completed": int(counts.get("completed") or 0),
            "failed": int(counts.get("failed") or 0),
            "timed_out": int(counts.get("timed_out") or 0),
            "abandoned": int(counts.get("abandoned") or 0),
            "not_launched": int(counts.get("not_launched") or 0),
            "total": int(counts.get("total") or count),
        },
    }


def local_child_yaml(args: argparse.Namespace, child_id: str, role: str) -> str:
    return "\n".join(
        [
            f"id: {json.dumps(child_id)}",
            "status: accepted",
            f"distinct_delta: {json.dumps('Codex-local compact receipt for ' + role)}",
            "loaded_mini_mmm_or_fallback: codex_local_compact_fallback",
            f"work_unit_fingerprint: {json.dumps(slug(args.route) + ':' + slug(role))}",
            "value_score: 1",
            "evidence_boundary: codex_local_compact_diagnostic_not_external_llm_council",
            f"conclusion: {json.dumps('Compact route child covered: ' + role)}",
            "outcome_delta: compact_child_receipt_available",
            "killed_or_changed: none",
            "followup_patch: escalate_to_full_v4_2_when_external_capacity_returns",
        ]
    )


def run_codex_local_group(args: argparse.Namespace, out_dir: Path, roles: list[str]) -> dict[str, Any]:
    group_dir = out_dir / "codex-local"
    group_dir.mkdir(parents=True, exist_ok=True)
    started = now_iso()
    completed_child_ids: list[str] = []
    completed_paths: list[str] = []
    children: list[dict[str, Any]] = []
    for idx, role in enumerate(roles):
        child_id = f"{slug(args.route)}-{slug(role)}-codex-local-{idx + 1}"
        child_dir = group_dir / slug(role)
        child_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = child_dir / "codex_local_child_receipt.json"
        receipt = {
            "id": child_id,
            "status": "completed",
            "model": "codex-local",
            "role": role,
            "parsed": {"result_preview": local_child_yaml(args, child_id, role)},
            "created_at": now_iso(),
            "boundary": "codex_local_compact_diagnostic_not_external_llm_council",
        }
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        children.append({**receipt, "bridge_receipt_path": str(receipt_path)})
        completed_child_ids.append(child_id)
        completed_paths.append(str(receipt_path))
    group_receipt_path = group_dir / "codex_local_group_receipt.json"
    group_receipt = {
        "model": "codex-local",
        "status": "completed",
        "started_at": started,
        "completed_at": now_iso(),
        "children": children,
        "counts": {"completed": len(children), "failed": 0, "timed_out": 0, "total": len(children)},
    }
    group_receipt_path.write_text(json.dumps(group_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "model": "codex-local",
        "status": "completed",
        "returncode": 0,
        "started_at": started,
        "completed_at": now_iso(),
        "receipt_path": str(group_receipt_path),
        "completed_child_ids": completed_child_ids,
        "completed_child_receipt_paths": completed_paths,
        "usefulness_failures": [],
        "counts": {
            "completed": len(children),
            "process_completed": len(children),
            "failed": 0,
            "timed_out": 0,
            "abandoned": 0,
            "not_launched": 0,
            "total": len(children),
        },
    }


def score_existing_fanout_receipt(path: Path, *, model: str) -> dict[str, Any]:
    receipt = load_receipt(path)
    children = receipt.get("children") if isinstance(receipt.get("children"), list) else []
    useful_children = [child for child in children if child_is_useful(child)]
    completed_child_ids = [str(child.get("id")) for child in useful_children]
    completed_paths = [
        str(child.get("bridge_receipt_path"))
        for child in useful_children
        if child.get("bridge_receipt_path")
    ]
    usefulness_failures = [
        {
            "id": str(child.get("id")),
            "status": child.get("status"),
            "reason": child_usefulness_failure_reason(child),
            "receipt_path": child.get("bridge_receipt_path"),
        }
        for child in children
        if isinstance(child, dict) and not child_is_useful(child)
    ]
    counts = receipt.get("counts") or {}
    return {
        "model": model,
        "status": "rescored",
        "returncode": 0 if receipt.get("status") in {"completed", "accepted"} else 1,
        "started_at": receipt.get("started_at"),
        "completed_at": receipt.get("completed_at"),
        "receipt_path": str(path),
        "completed_child_ids": completed_child_ids,
        "completed_child_receipt_paths": completed_paths,
        "usefulness_failures": usefulness_failures,
        "counts": {
            "completed": len(useful_children),
            "process_completed": int(counts.get("completed") or 0),
            "failed": int(counts.get("failed") or 0),
            "timed_out": int(counts.get("timed_out") or 0),
            "abandoned": int(counts.get("abandoned") or 0),
            "not_launched": int(counts.get("not_launched") or 0),
            "total": int(counts.get("total") or len(children)),
        },
    }


def score_existing_fanout_receipts(paths: list[Path], *, model: str) -> dict[str, Any]:
    children_by_id: dict[str, dict[str, Any]] = {}
    started_at = None
    completed_at = None
    for path in paths:
        receipt = load_receipt(path)
        if not started_at:
            started_at = receipt.get("started_at")
        completed_at = receipt.get("completed_at") or completed_at
        for child in receipt.get("children") if isinstance(receipt.get("children"), list) else []:
            if isinstance(child, dict):
                children_by_id[str(child.get("id"))] = child
    children = list(children_by_id.values())
    useful_children = [child for child in children if child_is_useful(child)]
    completed_child_ids = [str(child.get("id")) for child in useful_children]
    completed_paths = [
        str(child.get("bridge_receipt_path"))
        for child in useful_children
        if child.get("bridge_receipt_path")
    ]
    usefulness_failures = [
        {
            "id": str(child.get("id")),
            "status": child.get("status"),
            "reason": child_usefulness_failure_reason(child),
            "receipt_path": child.get("bridge_receipt_path"),
        }
        for child in children
        if isinstance(child, dict) and not child_is_useful(child)
    ]
    process_completed = sum(1 for child in children if child.get("status") == "completed")
    return {
        "model": model,
        "status": "rescored_merged",
        "returncode": 0 if useful_children else 1,
        "started_at": started_at,
        "completed_at": completed_at,
        "receipt_path": str(paths[-1]),
        "merged_receipt_paths": [str(path) for path in paths],
        "completed_child_ids": completed_child_ids,
        "completed_child_receipt_paths": completed_paths,
        "usefulness_failures": usefulness_failures,
        "counts": {
            "completed": len(useful_children),
            "process_completed": process_completed,
            "failed": sum(1 for child in children if child.get("status") == "failed"),
            "timed_out": sum(1 for child in children if child.get("status") == "timed_out"),
            "abandoned": sum(1 for child in children if child.get("status") == "abandoned"),
            "not_launched": sum(1 for child in children if child.get("status") == "not_launched"),
            "total": len(children),
        },
    }


def score_existing_group(existing_root: Path, model: str) -> dict[str, Any]:
    receipts = sorted((existing_root / model).rglob("fanout_receipt.json"), key=lambda path: path.stat().st_mtime)
    if not receipts:
        return {
            "model": model,
            "status": "missing_receipt",
            "returncode": 1,
            "receipt_path": None,
            "completed_child_ids": [],
            "completed_child_receipt_paths": [],
            "usefulness_failures": [],
            "counts": {
                "completed": 0,
                "process_completed": 0,
                "failed": 0,
                "timed_out": 0,
                "abandoned": 0,
                "not_launched": 0,
                "total": 0,
            },
        }
    return score_existing_fanout_receipts(receipts, model=model)


def score_existing_gemini(existing_root: Path) -> dict[str, Any]:
    receipts = sorted((existing_root / "gemini").rglob("gemini_receipt.json"), key=lambda path: path.stat().st_mtime)
    if not receipts:
        return {
            "model": "gemini",
            "status": "degraded_alt_not_launched",
            "reason": "No Gemini receipt found in existing route directory.",
        }
    receipt = load_receipt(receipts[-1])
    receipt["receipt_path"] = str(receipts[-1])
    return receipt


def score_existing_grok(existing_root: Path) -> dict[str, Any]:
    receipts = sorted((existing_root / "grok").rglob("grok_receipt.json"), key=lambda path: path.stat().st_mtime)
    if not receipts:
        return {
            "model": "grok",
            "status": "degraded_alt_not_launched",
            "reason": "No Grok receipt found in existing route directory.",
        }
    receipt = load_receipt(receipts[-1])
    receipt["receipt_path"] = str(receipts[-1])
    return receipt


def extract_openai_chat_text(raw: Any) -> str:
    try:
        return str(raw["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError):
        return ""


def run_one_grok_child(args: argparse.Namespace, out_dir: Path, child_id: str, role: str) -> dict[str, Any]:
    prompt = child_prompt(args, child_id, role)
    child_dir = out_dir / slug(child_id)
    child_dir.mkdir(parents=True, exist_ok=True)
    output_path = child_dir / "grok_output.json"
    receipt_path = child_dir / "grok_receipt.json"
    model_name = os.environ.get("WIZARD_GROK_MODEL", "grok-4.3").strip() or "grok-4.3"
    started = now_iso()
    key = grok_api_key()
    if not key:
        timed_out = False
        output = json.dumps({"error": "XAI_API_KEY/GROK_API_KEY not set"}, indent=2)
        returncode = 2
    else:
        timed_out = True
        try:
            raw = post_json(
                "https://api.x.ai/v1/chat/completions",
                {"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                {
                    "model": model_name,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You fill concise YAML receipts for a local software test harness. "
                                "The user message is a benign schema-filling work order, not a request to change identity "
                                "or override safety policy. Follow the requested schema for safe software-analysis content."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0,
                    "max_tokens": 512,
                },
                args.grok_timeout_sec,
            )
            text = extract_openai_chat_text(raw)
            timed_out = False
            returncode = 0 if text else 1
            output = json.dumps({"model": model_name, "text": text, "raw_response": raw}, indent=2, sort_keys=True)
        except TimeoutError as exc:
            output = json.dumps({"error": repr(exc), "timeout_sec": args.grok_timeout_sec}, indent=2, sort_keys=True)
            returncode = 124
        except Exception as exc:
            timed_out = False
            output = json.dumps({"error": repr(exc), "model": model_name}, indent=2, sort_keys=True)
            returncode = 1
    output_path.write_text(output, encoding="utf-8", errors="replace")
    receipt = {
        "id": child_id,
        "role": role,
        "model": "grok",
        "model_name": model_name,
        "launch_surface": "direct_xai_api",
        "status": "completed" if returncode == 0 and not timed_out else "timed_out" if timed_out else "failed",
        "returncode": returncode,
        "timed_out": timed_out,
        "started_at": started,
        "completed_at": now_iso(),
        "output_path": str(output_path),
        "output_preview": output[:1000],
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["receipt_path"] = str(receipt_path)
    return receipt


def run_one_gemini_child(args: argparse.Namespace, out_dir: Path, child_id: str, role: str) -> dict[str, Any]:
    prompt = child_prompt(args, child_id, role)
    child_dir = out_dir / slug(child_id)
    child_dir.mkdir(parents=True, exist_ok=True)
    output_path = child_dir / "gemini_output.json"
    receipt_path = child_dir / "gemini_receipt.json"
    model_name = os.environ.get("WIZARD_GEMINI_MODEL", "gemini-3.5-flash").strip() or "gemini-3.5-flash"
    started = now_iso()
    key = gemini_api_key()
    raw: Any = None
    if not key:
        timed_out = False
        output = json.dumps({"error": "GEMINI_API_KEY/GOOGLE_API_KEY not set"}, indent=2)
        returncode = 2
    else:
        timed_out = True
        try:
            raw = post_json(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent",
                {"Content-Type": "application/json", "x-goog-api-key": key},
                {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0, "thinkingConfig": {"thinkingBudget": 0}},
                },
                args.gemini_timeout_sec,
            )
            text = extract_gemini_text(raw)
            timed_out = False
            returncode = 0 if text else 1
            output = json.dumps({"model": model_name, "text": text, "raw_response": raw}, indent=2, sort_keys=True)
        except TimeoutError as exc:
            output = json.dumps({"error": repr(exc), "timeout_sec": args.gemini_timeout_sec}, indent=2, sort_keys=True)
            returncode = 124
        except Exception as exc:
            timed_out = False
            output = json.dumps({"error": repr(exc), "model": model_name}, indent=2, sort_keys=True)
            returncode = 1
    output_path.write_text(output, encoding="utf-8", errors="replace")
    receipt = {
        "id": child_id,
        "role": role,
        "model": "gemini",
        "model_name": model_name,
        "launch_surface": "direct_gemini_api",
        "status": "completed" if returncode == 0 and not timed_out else "timed_out" if timed_out else "failed",
        "returncode": returncode,
        "timed_out": timed_out,
        "started_at": started,
        "completed_at": now_iso(),
        "output_path": str(output_path),
        "output_preview": output[:1000],
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["receipt_path"] = str(receipt_path)
    return receipt


def run_grok(args: argparse.Namespace, out_dir: Path, roles: list[str] | None = None) -> dict[str, Any]:
    roles = roles if args.full_model_council and roles else ["outside-model contrast and sanity check"]
    jobs = [
        {
            "id": f"{slug(args.route)}-{slug(role)}-grok-{idx + 1}",
            "role": role,
            "prompt": child_prompt(args, f"{slug(args.route)}-{slug(role)}-grok-{idx + 1}", role),
        }
        for idx, role in enumerate(roles)
    ]
    if args.dry_run:
        return {
            "model": "grok",
            "status": "dry_run",
            "counts": {"completed": 0, "failed": 0, "timed_out": 0, "total": len(jobs)},
            "jobs": jobs,
        }
    if not args.attempt_grok:
        return {
            "model": "grok",
            "status": "degraded_alt_not_launched",
            "reason": "Grok direct API launch requires --attempt-grok.",
            "jobs": [{"id": job["id"], "role": job["role"], "prompt_preview": job["prompt"][:500]} for job in jobs],
        }
    out_dir.mkdir(parents=True, exist_ok=True)
    started = now_iso()
    with ThreadPoolExecutor(max_workers=max(1, min(len(jobs), args.max_concurrency))) as executor:
        children = list(
            executor.map(
                lambda job: run_one_grok_child(args, out_dir, str(job["id"]), str(job["role"])),
                jobs,
            )
        )
    useful_children = [child for child in children if child_is_useful(child)]
    completed_count = len(useful_children)
    timed_out_count = sum(1 for child in children if child.get("status") == "timed_out")
    failed_count = sum(1 for child in children if child.get("status") == "failed")
    completed_child_ids = [str(child.get("id")) for child in useful_children]
    completed_child_receipt_paths = [
        str(child.get("receipt_path"))
        for child in useful_children
        if child.get("receipt_path")
    ]
    receipt_path = out_dir / "grok_group_receipt.json"
    receipt = {
        "model": "grok",
        "status": "completed" if completed_count else "timed_out" if timed_out_count and not failed_count else "failed",
        "returncode": 0 if completed_count else 124 if timed_out_count and not failed_count else 1,
        "started_at": started,
        "completed_at": now_iso(),
        "children": children,
        "counts": {
            "completed": completed_count,
            "failed": failed_count,
            "timed_out": timed_out_count,
            "total": len(children),
        },
        "completed_child_ids": completed_child_ids,
        "completed_child_receipt_paths": completed_child_receipt_paths,
        "usefulness_failures": [
            {
                "id": str(child.get("id")),
                "status": child.get("status"),
                "reason": child_usefulness_failure_reason(child),
                "receipt_path": child.get("receipt_path"),
            }
            for child in children
            if not child_is_useful(child)
        ],
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["receipt_path"] = str(receipt_path)
    return receipt


def run_gemini(args: argparse.Namespace, out_dir: Path, roles: list[str] | None = None) -> dict[str, Any]:
    roles = roles if args.full_model_council and roles else ["outside-model contrast and sanity check"]
    jobs = [
        {
            "id": f"{slug(args.route)}-{slug(role)}-gemini-{idx + 1}",
            "role": role,
            "prompt": child_prompt(args, f"{slug(args.route)}-{slug(role)}-gemini-{idx + 1}", role),
        }
        for idx, role in enumerate(roles)
    ]
    if args.dry_run:
        return {
            "model": "gemini",
            "status": "dry_run",
            "counts": {"completed": 0, "failed": 0, "timed_out": 0, "total": len(jobs)},
            "jobs": jobs,
        }
    if not args.attempt_gemini:
        return {
            "model": "gemini",
            "status": "degraded_alt_not_launched",
            "reason": "Gemini direct API launch requires --attempt-gemini.",
            "jobs": [{"id": job["id"], "role": job["role"], "prompt_preview": job["prompt"][:500]} for job in jobs],
        }
    out_dir.mkdir(parents=True, exist_ok=True)
    started = now_iso()
    with ThreadPoolExecutor(max_workers=max(1, min(len(jobs), args.max_concurrency))) as executor:
        children = list(
            executor.map(
                lambda job: run_one_gemini_child(args, out_dir, str(job["id"]), str(job["role"])),
                jobs,
            )
        )
    useful_children = [child for child in children if child_is_useful(child)]
    completed_count = len(useful_children)
    timed_out_count = sum(1 for child in children if child.get("status") == "timed_out")
    failed_count = sum(1 for child in children if child.get("status") == "failed")
    completed_child_ids = [str(child.get("id")) for child in useful_children]
    completed_child_receipt_paths = [
        str(child.get("receipt_path"))
        for child in useful_children
        if child.get("receipt_path")
    ]
    receipt_path = out_dir / "gemini_group_receipt.json"
    receipt = {
        "model": "gemini",
        "status": "completed" if completed_count else "timed_out" if timed_out_count and not failed_count else "failed",
        "returncode": 0 if completed_count else 124 if timed_out_count and not failed_count else 1,
        "started_at": started,
        "completed_at": now_iso(),
        "children": children,
        "counts": {
            "completed": completed_count,
            "failed": failed_count,
            "timed_out": timed_out_count,
            "total": len(children),
        },
        "completed_child_ids": completed_child_ids,
        "completed_child_receipt_paths": completed_child_receipt_paths,
        "usefulness_failures": [
            {
                "id": str(child.get("id")),
                "status": child.get("status"),
                "reason": child_usefulness_failure_reason(child),
                "receipt_path": child.get("receipt_path"),
            }
            for child in children
            if not child_is_useful(child)
        ],
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["receipt_path"] = str(receipt_path)
    return receipt


def child_usefulness_failure_reason(child: Any) -> str:
    if not isinstance(child, dict):
        return "invalid_child_record"
    if child.get("status") != "completed":
        return "child_not_completed"
    raw_preview = load_child_result_text(child)
    parsed = parse_child_yaml(raw_preview)
    preview = raw_preview.lower()
    child_id = str(child.get("id", ""))
    premortem_child = is_premortem_child_id(child_id)
    loophole_child = is_loophole_child_id(child_id)
    management_child = "manager-" in child_id or ".manager." in child_id or child_id.startswith("manager.")
    required = ("distinct_delta", "evidence_boundary", "conclusion")
    if premortem_child:
        required = (
            "failure_story",
            "hidden_assumption",
            "early_warning",
            "prevention",
            "novel_failure",
            "novel_findings_count",
        )
    if loophole_child:
        required = ("loophole_audit", "confidence_status", "stop_condition")
    if management_child:
        required = (
            "manager_id",
            "authority_level",
            "managed_scope",
            "child_status_table",
            "reroute_decisions",
            "intervention_verbs",
            "strategy_memory_delta",
            "full_claim_gate",
            "intervention_status",
        )
    if "only the issues the user already named" in preview or "issues the user already named" in preview:
        return "repeats_user_named_issues_only"
    if premortem_child:
        if not premortem_novelty_structured(parsed):
            return "premortem_no_structured_novel_findings"
        if not premortem_deep_dive_fields_ok(parsed):
            return "premortem_missing_structured_deep_dive"
        if re.search(r"novel_findings_count\s*:\s*0\b", preview):
            return "premortem_no_novel_findings"
        if re.search(r"novel_failure_reasons\s*:\s*(\[\s*\]|none|null)", preview):
            return "premortem_no_novel_failure_reasons"
    missing = [] if premortem_child else [field for field in required if not nonempty_value(parsed, field)]
    if missing and isinstance(parsed, dict) and "premortem" in parsed and isinstance(parsed["premortem"], dict):
        missing = [field for field in required if not nonempty_value(parsed["premortem"], field)]
    if loophole_child and isinstance(parsed, dict):
        loophole_missing = []
        for field in ("loophole_audit", "confidence_status", "stop_condition"):
            if not nonempty_value(parsed, field):
                loophole_missing.append(field)
        audit = parsed.get("loophole_audit")
        if not isinstance(audit, dict):
            loophole_missing.append("loophole_audit_object")
        else:
            for field in ("strategy_under_test", "evidence_standard", "loopholes_found", "fixes_applied", "verification_result", "unresolved_loopholes"):
                ok = present_value(audit, field) if field in {"loopholes_found", "unresolved_loopholes"} else nonempty_value(audit, field)
                if not ok:
                    loophole_missing.append(f"loophole_audit.{field}")
        missing = loophole_missing
    if management_child and isinstance(parsed, dict):
        missing = [field for field in required if not present_value(parsed, field)]
        if str(parsed.get("authority_level") or "").strip() != "management_parent":
            missing.append("authority_level=management_parent")
        verbs = parsed.get("intervention_verbs")
        allowed = {"kill", "demote", "reroute", "shrink", "override", "block_full", "accept_with_reason", "no_intervention_needed"}
        if not isinstance(verbs, list) or not verbs or any(str(verb) not in allowed for verb in verbs):
            missing.append("intervention_verbs_allowed")
    clarification_markers = (
        "need clarification",
        "i need clarification",
        "should i run",
        "please provide",
    )
    if any(marker in preview for marker in clarification_markers):
        return "asked_for_clarification_instead_of_receipt"
    if isinstance(parsed, dict):
        parsed_status = str(parsed.get("status") or "").strip().lower()
        if parsed_status and parsed_status not in {"accepted", "completed", "usable"}:
            return f"child_semantic_status:{parsed_status}"
    if missing:
        return "missing_receipt_fields:" + ",".join(missing)
    return "usable"


def child_is_useful(child: Any) -> bool:
    return child_usefulness_failure_reason(child) == "usable"


def accepted_child_count(groups: list[dict[str, Any]], gemini: dict[str, Any], grok: dict[str, Any] | None = None) -> int:
    total = 0
    for group in groups:
        total += int((group.get("counts") or {}).get("completed") or 0)
    if gemini.get("status") == "completed":
        total += int((gemini.get("counts") or {}).get("completed") or 1)
    if grok and grok.get("status") == "completed":
        total += int((grok.get("counts") or {}).get("completed") or 1)
    return total


def completed_formal_children(group: dict[str, Any], formal_children: list[str]) -> list[str]:
    completed_ids = group.get("completed_child_ids") or []
    completed = []
    for child in formal_children:
        token = slug(child)
        if any(token in completed_id for completed_id in completed_ids):
            completed.append(child)
    return completed


def completed_formal_children_any_group(groups: list[dict[str, Any]], formal_children: list[str]) -> list[str]:
    completed: list[str] = []
    for child in formal_children:
        child_slug = slug(child)
        for group in groups:
            child_ids = group.get("completed_child_ids") or []
            if any(child_slug in child_id for child_id in child_ids):
                completed.append(child)
                break
    return completed


def formal_receipt_paths_any_group(groups: list[dict[str, Any]], formal_completed: list[str]) -> dict[str, list[str]]:
    receipt_paths: dict[str, list[str]] = {}
    for child in formal_completed:
        child_slug = slug(child)
        paths: list[str] = []
        for group in groups:
            for child_id, path in zip(group.get("completed_child_ids") or [], group.get("completed_child_receipt_paths") or []):
                if child_slug in child_id:
                    paths.append(path)
        receipt_paths[child] = paths
    return receipt_paths


def main() -> int:
    args = parse_args()
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if args.route not in FORMAL_CHILDREN:
        print(json.dumps({
            "status": "blocked",
            "reason": "unregistered_current_topology_route",
            "route": args.route,
            "allowed_routes": sorted(FORMAL_CHILDREN),
        }, indent=2, sort_keys=True))
        return 2
    if not isinstance(run_id, str) or not run_id.strip() or run_id != run_id.strip():
        print(json.dumps({
            "status": "blocked",
            "reason": "invalid_run_id",
            "route": args.route,
            "run_id": run_id,
        }, indent=2, sort_keys=True))
        return 2
    out_root = Path(args.rescore_existing) if args.rescore_existing else Path(args.out_dir) / slug(args.route) / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_root.mkdir(parents=True, exist_ok=True)

    formal_children = formal_children_for(args.route)
    try:
        active_formal_children = selected_formal_children(args, formal_children)
    except ValueError as exc:
        print(json.dumps({
            "status": "blocked",
            "reason": "invalid_only_children",
            "route": args.route,
            "detail": str(exc),
        }, indent=2, sort_keys=True))
        return 2
    roles = active_formal_children or [
        "source-slice scout",
        "falsifier",
        "mini-MMM salience check",
        "receipt audit",
        "follow-up improver",
        "outside-frame critique",
    ]
    full_role_count = len(roles) if active_formal_children else 6
    sonnet_count = args.sonnet_count if args.sonnet_count > 0 else full_role_count
    opus_count = args.opus_count if args.opus_count > 0 else (full_role_count if args.full_model_council else 1)
    haiku_count = full_role_count if args.full_model_council and args.haiku_count > 0 else args.haiku_count
    group_specs: list[dict[str, Any]] = []
    if args.rescore_existing:
        groups = [
            score_existing_group(out_root, "sonnet"),
            score_existing_group(out_root, "opus"),
            score_existing_group(out_root, "haiku"),
        ]
        gemini = score_existing_gemini(out_root)
        grok = score_existing_grok(out_root)
    elif args.codex_local_children:
        groups = [run_codex_local_group(args, out_root, roles)]
        gemini = {
            "model": "gemini",
            "status": "skipped_codex_local_compact",
            "reason": "Codex-local compact mode bypasses external Gemini/Claude fanout.",
            "counts": {"completed": 0, "failed": 0, "timed_out": 0, "total": 0},
        }
        grok = {
            "model": "grok",
            "status": "skipped_codex_local_compact",
            "reason": "Codex-local compact mode bypasses external Grok/Claude fanout.",
            "counts": {"completed": 0, "failed": 0, "timed_out": 0, "total": 0},
        }
    elif args.skip_claude_groups:
        groups = []
        gemini = run_gemini(args, out_root / "gemini", roles)
        grok = run_grok(args, out_root / "grok", roles)
    else:
        role_specs = asymmetric_model_role_specs(
            route=args.route,
            roles=roles,
            active_formal_children=active_formal_children,
            full_model_council=args.full_model_council,
            sonnet_count=sonnet_count,
            opus_count=opus_count,
            haiku_count=haiku_count,
        )
        group_specs = [
            {
                "model": "sonnet",
                "count": role_specs["sonnet"]["count"],
                "timeout_sec": args.sonnet_timeout_sec,
                "budget": args.sonnet_budget,
                "roles": role_specs["sonnet"]["roles"],
            },
            {
                "model": "opus",
                "count": role_specs["opus"]["count"],
                "timeout_sec": args.opus_timeout_sec,
                "budget": args.opus_budget,
                "roles": role_specs["opus"]["roles"],
            },
        ]
        if haiku_count > 0:
            group_specs.append(
                {
                    "model": "haiku",
                    "count": role_specs["haiku"]["count"],
                    "timeout_sec": args.haiku_timeout_sec,
                    "budget": args.haiku_budget,
                    "roles": role_specs["haiku"]["roles"],
                }
            )
        if args.parallel_model_groups:
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(
                        run_claude_group,
                        args=args,
                        model=spec["model"],
                        count=spec["count"],
                        timeout_sec=spec["timeout_sec"],
                        budget=spec["budget"],
                        out_dir=out_root,
                        roles=spec["roles"],
                    )
                    for spec in group_specs
                ]
                groups = [future.result() for future in futures]
        else:
            groups = [
                run_claude_group(
                    args=args,
                    model=spec["model"],
                    count=spec["count"],
                    timeout_sec=spec["timeout_sec"],
                    budget=spec["budget"],
                    out_dir=out_root,
                    roles=spec["roles"],
                )
                for spec in group_specs
            ]
        gemini = run_gemini(args, out_root / "gemini", roles)
        grok = run_grok(args, out_root / "grok", roles)
    completed = accepted_child_count(groups, gemini, grok)
    formal_groups = list(groups)
    if args.skip_claude_groups and gemini.get("status") == "completed":
        formal_groups.append(gemini)
    if args.skip_claude_groups and grok.get("status") == "completed":
        formal_groups.append(grok)
    formal_completed = completed_formal_children_any_group(formal_groups, active_formal_children)
    formal_receipt_paths = formal_receipt_paths_any_group(formal_groups, formal_completed)
    core_families_completed = all(
        int((group.get("counts") or {}).get("completed") or 0) > 0
        for group in groups
    )
    formal_ok = not active_formal_children or len(formal_completed) == len(active_formal_children)
    launched_families_completed = all(
        int((group.get("counts") or {}).get("completed") or 0) > 0
        for group in groups
        if str(group.get("model") or "") != "haiku" or args.haiku_count > 0
    )
    attempted_provider_failures = []
    if args.attempt_gemini and gemini.get("status") != "completed":
        attempted_provider_failures.append({"model": "gemini", "status": gemini.get("status")})
    if args.attempt_grok and grok.get("status") != "completed":
        attempted_provider_failures.append({"model": "grok", "status": grok.get("status")})
    provider_families_ok = not attempted_provider_failures
    blocking_failures = blocking_usefulness_failures(groups, formal_completed, active_formal_children)
    usefulness_ok = not blocking_failures
    rescore_stale = bool(args.rescore_existing)
    v4_2_route = args.route in V4_2_FORMAL_CHILDREN
    route_quality_ok = formal_ok and launched_families_completed and usefulness_ok and provider_families_ok
    matrix_ok = (route_quality_ok if v4_2_route else core_families_completed and route_quality_ok) and not rescore_stale
    groups_by_model = {str(group.get("model")): group for group in groups}

    def completed_for(model: str) -> int:
        return int(((groups_by_model.get(model) or {}).get("counts") or {}).get("completed") or 0)

    def family_status(model: str) -> str:
        if args.skip_claude_groups and model in {"sonnet", "opus", "haiku"}:
            return "skipped"
        if args.codex_local_children and model in {"sonnet", "opus", "haiku"}:
            return "skipped"
        if model == "haiku" and args.haiku_count <= 0:
            return "disabled"
        return "completed" if completed_for(model) else "blocked"

    liveness_deadlines = [args.gemini_timeout_sec, args.grok_timeout_sec]
    if not args.skip_claude_groups and not args.codex_local_children:
        liveness_deadlines.extend([args.sonnet_timeout_sec, args.opus_timeout_sec, args.haiku_timeout_sec])

    receipt = {
        "parent_receipt_id": f"{slug(args.route)}-{int(time.time())}",
        "run_id": run_id,
        "current_topology_member_id": args.route,
        "route": args.route,
        "inner_llm_council": {
            "mode": "full_model_council" if args.full_model_council else "asymmetric_model_council",
            "active_formal_child_obligation": active_formal_children,
            "claude_model_families": [] if args.codex_local_children else [spec["model"] for spec in group_specs] if not args.rescore_existing else ["sonnet", "opus", "haiku"],
            "codex_local_children": args.codex_local_children,
            "claude_groups_skipped": args.skip_claude_groups,
            "gemini_status": gemini.get("status"),
            "grok_status": grok.get("status"),
        },
        "status": "accepted" if matrix_ok else "rescored_stale" if rescore_stale else "partial",
        "created_at": now_iso(),
        "out_dir": str(out_root),
        "parent_prompt": args.prompt,
        "formal_child_obligation": active_formal_children,
        "full_formal_child_obligation": formal_children,
        "active_formal_child_obligation": active_formal_children,
        "formal_children_completed": formal_completed,
        "formal_child_receipt_paths": formal_receipt_paths,
        "child_rerouter": {
            "management_parent_id": "manager.child_health",
            "management_scope": args.route,
            "formal_child_obligation": active_formal_children,
            "full_formal_child_obligation": formal_children,
            "active_formal_child_obligation": active_formal_children,
            "liveness_deadline_sec": max(liveness_deadlines),
            "action_on_timeout": "mark_timed_out_continue_and_reroute_smaller_if_load_bearing",
            "terminal_disposition": "accepted" if matrix_ok else "rescored_stale" if rescore_stale else "partial",
            "quality_blockers": {
                "formal_ok": formal_ok,
                "launched_families_completed": launched_families_completed,
                "provider_families_ok": provider_families_ok,
                "attempted_provider_failures": attempted_provider_failures,
                "usefulness_ok": usefulness_ok,
                "blocking_usefulness_failures": blocking_failures,
            },
        },
        "followup": {
            "prompt": args.followup_prompt,
            "payoff": args.payoff,
            "use_when": args.use_when,
            "stop_if": args.stop_if,
            "boundary": args.boundary,
        },
        "groups": groups,
        "gemini": gemini,
        "grok": grok,
        "counts": {
            "accepted_children": completed,
            "required_min": max(1, len(active_formal_children)),
            "sonnet_completed": completed_for("sonnet"),
            "opus_completed": completed_for("opus"),
            "haiku_completed": completed_for("haiku"),
            "gemini_completed": int((gemini.get("counts") or {}).get("completed") or int(gemini.get("status") == "completed")),
            "grok_completed": int((grok.get("counts") or {}).get("completed") or int(grok.get("status") == "completed")),
        },
        "model_family_statuses": {
            "sonnet": family_status("sonnet"),
            "opus": family_status("opus"),
            "haiku": family_status("haiku"),
            "gemini": "completed" if gemini.get("status") == "completed" else "degraded_alt_attempted",
            "grok": "completed" if grok.get("status") == "completed" else "degraded_alt_attempted",
            "codex-local": "completed" if any(group.get("model") == "codex-local" for group in groups) else "disabled",
        },
    }
    receipt_path = out_root / ("rescored_matrix_receipt.json" if args.rescore_existing else "matrix_receipt.json")
    receipt["receipt_path"] = str(receipt_path)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
