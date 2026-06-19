#!/usr/bin/env python3
"""Run and score proposal-only model audit lanes for Codex Ratchet.

This collector exists to prevent "many models" from degrading into a count
badge. It asks several model runtimes the same repo-grounded question, records
provider facts, extracts reasoning-only outputs when content is null, and
scores each output with a deterministic local rubric.

The report is advisory only. It is never sim evidence, never admission
evidence, and never a Codex-native parent/child hierarchy receipt.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any
from urllib import error, request


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPO_ROOT / "system_v5" / "ops" / "codex_sim_runner" / "model_quality_swarm"
REPORT_SCHEMA = "codex_model_quality_swarm_report_v1"
CHILD_SCHEMA = "codex_model_quality_child_receipt_v1"
MODEL_CHILD_SCHEMA = "codex_model_child_receipt_v1"
CLAIM_CEILING = (
    "proposal-only model audit; not sim evidence, not Wizard FULL proof, "
    "not admission evidence, not promotion evidence"
)
ELIGIBLE_CONSUMERS = ["proposal_synthesis", "audit_synthesis", "next_step_selection"]
BLOCKED_CONSUMERS = [
    "sim_admission",
    "formal_evidence",
    "canonical_status",
    "layer_claim",
    "manifold_claim",
    "axis_claim",
    "wizard_full_claim",
]
DETERMINISTIC_CHECKS_REQUIRED = [
    "python_runner_rerun",
    "three_engine_validator_when_applicable",
    "wizard_sim_admission_validator",
    "repo_contract_tests",
]


@dataclass(frozen=True)
class ModelRoute:
    key: str
    runtime: str
    provider: str
    model: str
    route: str
    launch_surface: str
    env_keys: tuple[str, ...]


DEFAULT_ROUTES: tuple[ModelRoute, ...] = (
    ModelRoute(
        key="gemini-tui",
        runtime="gemini-tui",
        provider="gemini_cli",
        model="gemini-2.5-flash",
        route="tool_function_scout",
        launch_surface="gemini_tui_cli",
        env_keys=(),
    ),
    ModelRoute(
        key="gemini-api-fallback",
        runtime="gemini-api",
        provider="gemini_api",
        model="models/gemini-2.5-flash",
        route="tool_function_scout",
        launch_surface="direct_gemini_api_reroute_after_tui_block",
        env_keys=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    ),
    ModelRoute(
        key="grok-api",
        runtime="grok-api",
        provider="xai",
        model="grok-4.3",
        route="failure_council",
        launch_surface="direct_xai_api",
        env_keys=("XAI_API_KEY", "GROK_API_KEY"),
    ),
    ModelRoute(
        key="openrouter-fusion",
        runtime="openrouter-fusion",
        provider="openrouter",
        model="openrouter/fusion",
        route="decision_council",
        launch_surface="direct_openrouter_api",
        env_keys=("OPENROUTER_API_KEY",),
    ),
    ModelRoute(
        key="glm-5.2",
        runtime="top-chinese-models",
        provider="openrouter",
        model="z-ai/glm-5.2",
        route="followup_scout",
        launch_surface="direct_openrouter_api",
        env_keys=("OPENROUTER_API_KEY",),
    ),
    ModelRoute(
        key="kimi-k2.7-code",
        runtime="top-chinese-models",
        provider="openrouter",
        model="moonshotai/kimi-k2.7-code",
        route="followup_audit",
        launch_surface="direct_openrouter_api",
        env_keys=("OPENROUTER_API_KEY",),
    ),
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "item"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_json_atomic(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)
    return path


def _first_env(keys: tuple[str, ...]) -> tuple[str | None, str | None]:
    for key in keys:
        value = os.environ.get(key)
        if value:
            return key, value
    return None, None


def _text_from_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = [_text_from_value(item) for item in value]
        return "\n".join(part for part in parts if part.strip())
    if isinstance(value, dict):
        for key in ("text", "content", "output_text", "reasoning", "summary"):
            if key in value:
                text = _text_from_value(value.get(key))
                if text.strip():
                    return text
        return json.dumps(value, sort_keys=True)
    return str(value)


def extract_openai_chat_text(body: dict[str, Any]) -> dict[str, Any]:
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        return {
            "output_text": "",
            "extraction_source": "missing_choices",
            "content_was_null": False,
            "content_empty": True,
            "reasoning_present": False,
        }
    choice = choices[0] if isinstance(choices[0], dict) else {}
    message = choice.get("message") if isinstance(choice.get("message"), dict) else {}
    candidates: list[tuple[str, Any]] = [
        ("content", message.get("content")),
        ("reasoning", message.get("reasoning")),
        ("reasoning_content", message.get("reasoning_content")),
        ("reasoning_details", message.get("reasoning_details")),
        ("refusal", message.get("refusal")),
        ("choice_text", choice.get("text")),
    ]
    extracted_parts: list[str] = []
    extraction_sources: list[str] = []
    for source, value in candidates:
        text = _text_from_value(value)
        if text.strip():
            extracted_parts.append(text.strip())
            extraction_sources.append(source)
    output_text = "\n\n".join(dict.fromkeys(extracted_parts))
    content = message.get("content")
    extraction_status = "empty_content"
    if output_text and content is None and any(source.startswith("reasoning") for source in extraction_sources):
        extraction_status = "reasoning_only_content_null"
    elif output_text:
        extraction_status = "usable_content"
    return {
        "output_text": output_text,
        "extraction_source": "+".join(extraction_sources) if extraction_sources else "empty_message",
        "extraction_status": extraction_status,
        "content_was_null": content is None,
        "content_empty": not bool(_text_from_value(content).strip()),
        "reasoning_present": any(source.startswith("reasoning") for source in extraction_sources),
        "finish_reason": choice.get("finish_reason"),
        "native_finish_reason": choice.get("native_finish_reason"),
    }


def extract_gemini_text(body: dict[str, Any]) -> dict[str, Any]:
    candidates = body.get("candidates")
    parts: list[str] = []
    if isinstance(candidates, list):
        for candidate in candidates:
            content = candidate.get("content") if isinstance(candidate, dict) else {}
            for part in content.get("parts", []) if isinstance(content, dict) else []:
                text = _text_from_value(part)
                if text.strip():
                    parts.append(text.strip())
    output_text = "\n\n".join(parts)
    return {
        "output_text": output_text,
        "extraction_source": "gemini_candidates_parts" if output_text else "empty_gemini_response",
        "extraction_status": "usable_content" if output_text else "empty_content",
        "content_was_null": False,
        "content_empty": not bool(output_text),
        "reasoning_present": False,
    }


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int) -> tuple[int, dict[str, Any], int]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    started = time.monotonic()
    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            status = int(response.status)
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = int(exc.code)
    duration_ms = int((time.monotonic() - started) * 1000)
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        body = {"error": {"code": status, "message": raw[:1000]}}
    return status, body if isinstance(body, dict) else {"raw": body}, duration_ms


def run_openrouter(route: ModelRoute, prompt: str, timeout: int, max_tokens: int) -> dict[str, Any]:
    key_name, key = _first_env(route.env_keys)
    if not key:
        return child_blocked(route, "missing_api_key", f"missing one of {', '.join(route.env_keys)}")
    payload = {
        "model": route.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    status, body, duration_ms = post_json(
        "https://openrouter.ai/api/v1/chat/completions",
        {
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://codex-ratchet.local",
            "X-Title": "Codex Ratchet quality swarm",
        },
        payload,
        timeout,
    )
    extracted = extract_openai_chat_text(body)
    return child_completed(route, body, extracted, http_status=status, duration_ms=duration_ms, env_key=key_name)


def run_xai(route: ModelRoute, prompt: str, timeout: int, max_tokens: int) -> dict[str, Any]:
    key_name, key = _first_env(route.env_keys)
    if not key:
        return child_blocked(route, "missing_api_key", f"missing one of {', '.join(route.env_keys)}")
    payload = {
        "model": route.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    status, body, duration_ms = post_json(
        "https://api.x.ai/v1/chat/completions",
        {"Authorization": f"Bearer {key}"},
        payload,
        timeout,
    )
    extracted = extract_openai_chat_text(body)
    return child_completed(route, body, extracted, http_status=status, duration_ms=duration_ms, env_key=key_name)


def run_gemini_cli(route: ModelRoute, prompt: str, timeout: int, max_tokens: int) -> dict[str, Any]:
    del max_tokens
    started = time.monotonic()
    command = ["gemini", "-m", route.model, "-p", prompt]
    try:
        proc = subprocess.run(
            command,
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        body = {
            "stdout": proc.stdout,
            "stderr_tail": proc.stderr[-2000:],
            "returncode": proc.returncode,
            "command": ["gemini", "-m", route.model, "-p", "<prompt>"],
        }
        extracted = {
            "output_text": proc.stdout.strip(),
            "extraction_source": "stdout" if proc.stdout.strip() else "empty_stdout",
            "extraction_status": "usable_content" if proc.stdout.strip() else "empty_content",
            "content_was_null": False,
            "content_empty": not bool(proc.stdout.strip()),
            "reasoning_present": False,
        }
        child = child_completed(route, body, extracted, returncode=proc.returncode, duration_ms=duration_ms)
        if proc.returncode != 0:
            child["status"] = "error"
        return child
    except subprocess.TimeoutExpired as exc:
        return child_blocked(
            route,
            "timed_out",
            f"gemini cli timed out after {timeout}s",
            raw={"stdout_tail": (exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else ""},
        )


def run_gemini_api(route: ModelRoute, prompt: str, timeout: int, max_tokens: int) -> dict[str, Any]:
    key_name, key = _first_env(route.env_keys)
    if not key:
        return child_blocked(route, "missing_api_key", f"missing one of {', '.join(route.env_keys)}")
    model_path = route.model if route.model.startswith("models/") else f"models/{route.model}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": max_tokens},
    }
    status, body, duration_ms = post_json(
        f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={key}",
        {},
        payload,
        timeout,
    )
    extracted = extract_gemini_text(body)
    return child_completed(route, body, extracted, http_status=status, duration_ms=duration_ms, env_key=key_name)


def child_completed(
    route: ModelRoute,
    raw_body: dict[str, Any],
    extraction: dict[str, Any],
    *,
    http_status: int | None = None,
    returncode: int | None = 0,
    duration_ms: int | None = None,
    env_key: str | None = None,
) -> dict[str, Any]:
    output_text = str(extraction.get("output_text") or "")
    score = score_output(output_text, status="completed")
    return {
        "schema": CHILD_SCHEMA,
        "model_child_schema": MODEL_CHILD_SCHEMA,
        "child_id": f"{slug(route.key)}_{slug(route.route)}",
        "runtime": route.runtime,
        "provider": route.provider,
        "model": route.model,
        "route": route.route,
        "launch_surface": route.launch_surface,
        "status": "completed",
        "evidence_role": evidence_role_for_route(route.route),
        "proposal_only": True,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "not_codex_native_subsubagent": route.launch_surface != "multi_agent_v1_parent_spawned_child",
        "model_outputs_are_sim_evidence": False,
        "claim_ceiling": CLAIM_CEILING,
        "eligible_consumers": ELIGIBLE_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "proposed_deterministic_checks": DETERMINISTIC_CHECKS_REQUIRED,
        "http_status": http_status,
        "returncode": returncode,
        "duration_ms": duration_ms,
        "env_key_used": env_key,
        "content": output_text,
        "content_sha256": sha256_text(output_text),
        "extraction": extraction,
        "usage": raw_body.get("usage") if isinstance(raw_body.get("usage"), dict) else None,
        "raw_response_excerpt": json.dumps(raw_body, sort_keys=True)[:2000],
        "raw_response_path": None,
        "score": score,
    }


def child_blocked(route: ModelRoute, status: str, reason: str, raw: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema": CHILD_SCHEMA,
        "model_child_schema": MODEL_CHILD_SCHEMA,
        "child_id": f"{slug(route.key)}_{slug(route.route)}",
        "runtime": route.runtime,
        "provider": route.provider,
        "model": route.model,
        "route": route.route,
        "launch_surface": route.launch_surface,
        "status": status,
        "evidence_role": evidence_role_for_route(route.route),
        "proposal_only": True,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "not_codex_native_subsubagent": route.launch_surface != "multi_agent_v1_parent_spawned_child",
        "model_outputs_are_sim_evidence": False,
        "claim_ceiling": CLAIM_CEILING,
        "eligible_consumers": ELIGIBLE_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "proposed_deterministic_checks": DETERMINISTIC_CHECKS_REQUIRED,
        "reason": reason,
        "content": "",
        "content_sha256": sha256_text(""),
        "extraction": {
            "output_text": "",
            "extraction_source": status,
            "extraction_status": status if status in {"malformed_response", "provider_error"} else "empty_content",
            "content_was_null": False,
            "content_empty": True,
            "reasoning_present": False,
        },
        "raw_response_excerpt": json.dumps(raw or {}, sort_keys=True)[:2000],
        "raw_response_path": None,
        "score": score_output("", status=status),
    }


def evidence_role_for_route(route: str) -> str:
    if "audit" in route or "failure" in route:
        return "audit"
    if "scout" in route or "followup" in route or "tool_function" in route:
        return "scout"
    return "proposal"


def _contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in text for pattern in patterns)


def _regex_hits(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def score_output(output_text: str, *, status: str = "completed") -> dict[str, Any]:
    text = output_text.lower()
    word_count = len(re.findall(r"\w+", output_text))
    if status != "completed" or not output_text.strip():
        return {
            "total": 0,
            "accepted": False,
            "components": {
                "extraction_health": 0,
                "evidence_specificity": 0,
                "actionability": 0,
                "gate_alignment": 0,
                "novel_failure_detection": 0,
                "overclaim_resistance": 0,
            },
            "penalties": ["no_completed_output"],
            "word_count": word_count,
        }

    path_hits = _regex_hits(output_text, r"(scripts|system_v[0-9]|AGENTS|CODEX)[A-Za-z0-9_./-]+")
    command_hits = _regex_hits(output_text, r"(\bpytest\b|\bpython3?\b|\bmake\b|wizard_sim_admission|validate_)")
    finding_hits = sum(
        marker in text
        for marker in (
            "nonclassical_load_bearing_tool_missing_two_root_registry",
            "nonclassical_suitable_load_bearing_tool_missing",
            "wizard_sim_admission",
            "two_root_constraints",
            "tool_target",
            "load_bearing",
        )
    )
    action_hits = sum(
        marker in text
        for marker in ("patch", "change", "edit", "add test", "demote", "set ", "run ", "verify", "rerun")
    )
    gate_hits = sum(
        marker in text
        for marker in (
            "proposal-only",
            "proposal only",
            "no promotion",
            "not sim evidence",
            "scratch_diagnostic",
            "deterministic",
            "jax",
            "julia",
            "pytorch",
            "root evidence",
            "f01",
            "n01",
        )
    )
    novelty_hits = sum(
        marker in text
        for marker in (
            "demote",
            "stale",
            "reasoning-only",
            "content null",
            "registry",
            "tool_target",
            "root evidence",
            "pyTorch-centric".lower(),
            "jax/julia",
            "supportive",
        )
    )
    overclaim_penalty = sum(
        marker in text
        for marker in (
            "mark it admitted",
            "promote it",
            "full wizard passed",
            "final manifold",
            "just add jax",
            "ignore the gate",
        )
    )
    caution_hits = sum(
        marker in text
        for marker in (
            "do not",
            "must not",
            "blocked",
            "proposal-only",
            "not evidence",
            "no promotion",
            "should not",
        )
    )
    components = {
        "extraction_health": min(15, 5 + min(word_count // 40, 10)),
        "evidence_specificity": min(20, path_hits * 4 + command_hits * 3 + finding_hits * 3),
        "actionability": min(20, action_hits * 4 + command_hits * 2),
        "gate_alignment": min(20, gate_hits * 3),
        "novel_failure_detection": min(15, novelty_hits * 3),
        "overclaim_resistance": max(0, min(10, caution_hits * 2) - overclaim_penalty * 5),
    }
    penalties: list[str] = []
    if word_count < 80:
        penalties.append("too_short")
        components["extraction_health"] = max(0, components["extraction_health"] - 5)
    if overclaim_penalty:
        penalties.append("overclaim_language")
    total = max(0, min(100, sum(components.values()) - 5 * len(penalties)))
    return {
        "total": total,
        "accepted": total >= 55,
        "components": components,
        "penalties": penalties,
        "word_count": word_count,
    }


def run_route(route: ModelRoute, prompt: str, timeout: int, max_tokens: int) -> dict[str, Any]:
    if route.provider == "openrouter":
        return run_openrouter(route, prompt, timeout, max_tokens)
    if route.provider == "xai":
        return run_xai(route, prompt, timeout, max_tokens)
    if route.provider == "gemini_cli":
        return run_gemini_cli(route, prompt, timeout, max_tokens)
    if route.provider == "gemini_api":
        return run_gemini_api(route, prompt, timeout, max_tokens)
    return child_blocked(route, "blocked_unknown_provider", f"unknown provider {route.provider}")


def build_report(
    *,
    prompt: str,
    prompt_path: Path | None,
    children: list[dict[str, Any]],
    child_paths: list[str],
    run_id: str,
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    completed = [child for child in children if child.get("status") == "completed"]
    accepted = [child for child in completed if (child.get("score") or {}).get("accepted") is True]
    usable_content = [
        child
        for child in accepted
        if ((child.get("extraction") or {}).get("extraction_status") == "usable_content")
    ]
    reasoning_only = [
        child
        for child in children
        if ((child.get("extraction") or {}).get("extraction_status") == "reasoning_only_content_null")
    ]
    top = sorted(
        (
            {
                "key": child.get("runtime"),
                "model": child.get("model"),
                "route": child.get("route"),
                "score": (child.get("score") or {}).get("total", 0),
                "receipt_path": path,
            }
            for child, path in zip(children, child_paths, strict=False)
        ),
        key=lambda item: item["score"],
        reverse=True,
    )
    return {
        "schema": REPORT_SCHEMA,
        "run_id": run_id,
        "created_at": completed_at,
        "started_at": started_at,
        "completed_at": completed_at,
        "repo_root": str(REPO_ROOT),
        "prompt_path": str(prompt_path) if prompt_path else None,
        "prompt_sha256": sha256_text(prompt),
        "proposal_only": True,
        "model_outputs_are_sim_evidence": False,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "eligible_consumers": ELIGIBLE_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "proposed_deterministic_checks": DETERMINISTIC_CHECKS_REQUIRED,
        "required_model_keys": [route.key for route in DEFAULT_ROUTES],
        "completed_model_keys": [child.get("runtime") for child in completed],
        "usable_model_outputs": [
            child.get("child_id")
            for child in usable_content
        ],
        "unusable_model_outputs": [
            child.get("child_id")
            for child in children
            if (child.get("score") or {}).get("accepted") is not True
        ],
        "reasoning_only_outputs": [
            child.get("child_id")
            for child in reasoning_only
        ],
        "direct_external_children": [
            child.get("child_id")
            for child in children
            if child.get("not_codex_native_subsubagent") is True
        ],
        "non_proposal_children": [
            child.get("child_id")
            for child in children
            if child.get("proposal_only") is not True
        ],
        "accepted_model_count": len(accepted),
        "usable_content_model_count": len(usable_content),
        "reasoning_only_model_count": len(reasoning_only),
        "completed_model_count": len(completed),
        "status": "quality_passed" if len(accepted) >= 3 else "quality_partial",
        "accepted_threshold": 55,
        "children": children,
        "child_receipt_paths": child_paths,
        "top_models": top,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--prompt-file", type=Path)
    source.add_argument("--prompt")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-id")
    parser.add_argument("--include", action="append", help="Route key to include. Repeatable. Default: all.")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--max-workers", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prompt_path = args.prompt_file.resolve() if args.prompt_file else None
    prompt = prompt_path.read_text(encoding="utf-8") if prompt_path else str(args.prompt)
    include = set(args.include or [route.key for route in DEFAULT_ROUTES])
    routes = [route for route in DEFAULT_ROUTES if route.key in include]
    run_id = args.run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir.resolve() / run_id
    started_at = utc_now()
    child_payloads: list[dict[str, Any]] = []
    child_paths_by_id: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max(1, min(args.max_workers, len(routes) or 1))) as pool:
        futures = {
            pool.submit(run_route, route, prompt, args.timeout, args.max_tokens): route
            for route in routes
        }
        for future in as_completed(futures):
            route = futures[future]
            try:
                child = future.result()
            except Exception as exc:
                child = child_blocked(route, "exception", f"{type(exc).__name__}: {exc}")
            child["created_at"] = utc_now()
            child["prompt_sha256"] = sha256_text(prompt)
            child_path = out_dir / f"{slug(route.key)}_{slug(route.route)}_quality_child_receipt.json"
            write_json_atomic(child_path, child)
            child_payloads.append(child)
            child_paths_by_id[str(child.get("child_id"))] = str(child_path)
    child_payloads.sort(key=lambda item: str(item.get("child_id")))
    child_paths = [child_paths_by_id[str(child.get("child_id"))] for child in child_payloads]
    completed_at = utc_now()
    report = build_report(
        prompt=prompt,
        prompt_path=prompt_path,
        children=child_payloads,
        child_paths=child_paths,
        run_id=run_id,
        started_at=started_at,
        completed_at=completed_at,
    )
    report_path = out_dir / "model_quality_swarm_report.json"
    write_json_atomic(report_path, report)
    summary = {
        "report_path": str(report_path),
        "status": report["status"],
        "completed_model_count": report["completed_model_count"],
        "accepted_model_count": report["accepted_model_count"],
        "top_models": report["top_models"][:3],
        "claim_ceiling": CLAIM_CEILING,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
