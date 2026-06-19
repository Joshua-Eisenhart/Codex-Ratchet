"""Providers for the LLM harness.

A Provider turns a ModelJob into a ModelReceipt.  Providers know NOTHING of
Wizard doctrine, claim ceilings, or admission gates -- they only produce
faithful execution facts.  The fake providers are deterministic and offline;
``LocalToolProvider`` runs a REAL subprocess and captures the REAL returncode
and stdout/stderr (never a hardcoded pass).  ``OpenRouterProvider`` makes a REAL
HTTP call to OpenRouter and maps the response into the receipt; the mapping is
factored out (``map_openrouter_response``) so it is OFFLINE-testable against a
recorded fixture.

Timestamps are passed in to ``run`` so receipts are reproducible.
"""
from __future__ import annotations

import abc
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from .types import (
    ModelJob,
    ModelReceipt,
    content_canonical_hash,
    sandbox_config_hash,
    sha256_bytes,
    sha256_text,
)

OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


class ProviderError(RuntimeError):
    """Raised for provider misconfiguration (e.g. LocalToolProvider with no command)."""


def _now_pair(started_at: Optional[str], completed_at: Optional[str]) -> tuple[str, str]:
    """Providers accept caller timestamps; default to a fixed sentinel so a
    provider used without timestamps still yields a reproducible receipt."""
    s = started_at if started_at is not None else "1970-01-01T00:00:00+00:00"
    c = completed_at if completed_at is not None else s
    return s, c


def _hash_artifacts(artifact_paths: list[str]) -> dict[str, str]:
    """Hash every artifact that exists on disk.  Missing artifacts are skipped
    (their absence is itself recorded by the empty entry)."""
    out: dict[str, str] = {}
    for p in artifact_paths:
        path = Path(p)
        if path.is_file():
            out[p] = sha256_bytes(path.read_bytes())
    return out


class Provider(abc.ABC):
    """Abstract base: run a job -> receipt."""

    name: str = "provider"

    @abc.abstractmethod
    def run(
        self,
        job: ModelJob,
        *,
        timeout: Optional[float] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
    ) -> ModelReceipt:
        ...

    def _base_receipt_kwargs(self, job: ModelJob, *, launch_surface: str) -> dict:
        task = job.task
        return dict(
            task_id=task.task_id,
            role=task.role,
            provider=job.provider,
            launch_surface=launch_surface,
            model_requested=job.model,
            prompt_sha256=task.prompt_sha256(),
            input_refs=list(task.input_refs),
            output_path=job.output_path,
            classification=task.classification,
            claim_ceiling=task.claim_ceiling,
            gate_ceiling_rung=task.gate_ceiling_rung,
            audit_required=task.audit_required,
        )


# ---------------------------------------------------------------------------
# Deterministic offline fakes
# ---------------------------------------------------------------------------


class FakeSuccessProvider(Provider):
    """Writes a deterministic successful output and a success receipt."""

    name = "fake_success"

    def __init__(self, body: str = "FAKE-OK"):
        self.body = body

    def run(self, job, *, timeout=None, started_at=None, completed_at=None):
        s, c = _now_pair(started_at, completed_at)
        stdout = self.body
        artifacts: list[str] = []
        if job.output_path:
            Path(job.output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(job.output_path).write_text(stdout, encoding="utf-8")
            artifacts = [job.output_path]
        return ModelReceipt(
            **self._base_receipt_kwargs(job, launch_surface="fake"),
            artifact_paths=artifacts,
            status="success",
            returncode=0,
            started_at=s,
            completed_at=c,
            success_or_error_discriminator="choices_present",
            content=stdout,
            content_empty=(stdout == ""),
            message_role="assistant",
            finish_reason="stop",
            native_finish_reason="stop",
            content_canonical_hash=content_canonical_hash(stdout, "stop", "stop"),
            stdout_sha256=sha256_text(stdout),
            stderr_sha256=sha256_text(""),
            artifact_sha256=_hash_artifacts(artifacts),
        )


class FakeFailureProvider(Provider):
    """Emits an error receipt with a nonzero returncode."""

    name = "fake_failure"

    def __init__(self, returncode: int = 1, stderr: str = "FAKE-FAIL"):
        self.returncode = returncode
        self.stderr = stderr

    def run(self, job, *, timeout=None, started_at=None, completed_at=None):
        s, c = _now_pair(started_at, completed_at)
        return ModelReceipt(
            **self._base_receipt_kwargs(job, launch_surface="fake"),
            artifact_paths=[],
            status="error",
            returncode=self.returncode,
            started_at=s,
            completed_at=c,
            success_or_error_discriminator="top_level_error",
            stdout_sha256=sha256_text(""),
            stderr_sha256=sha256_text(self.stderr),
            artifact_sha256={},
        )


class FakeTimeoutProvider(Provider):
    """Emits a timed_out receipt (status timed_out, returncode None)."""

    name = "fake_timeout"

    def run(self, job, *, timeout=None, started_at=None, completed_at=None):
        s, c = _now_pair(started_at, completed_at)
        return ModelReceipt(
            **self._base_receipt_kwargs(job, launch_surface="fake"),
            artifact_paths=[],
            status="timed_out",
            returncode=None,
            started_at=s,
            completed_at=c,
            stdout_sha256=sha256_text(""),
            stderr_sha256=sha256_text("TIMEOUT"),
            artifact_sha256={},
        )


class FakeMalformedProvider(Provider):
    """Emits a blocked receipt: output is present but unparseable, so the run
    cannot be interpreted as a result."""

    name = "fake_malformed"

    def __init__(self, body: str = "\x00\x01not-json-not-anything"):
        self.body = body

    def run(self, job, *, timeout=None, started_at=None, completed_at=None):
        s, c = _now_pair(started_at, completed_at)
        artifacts: list[str] = []
        if job.output_path:
            Path(job.output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(job.output_path).write_text(self.body, encoding="utf-8")
            artifacts = [job.output_path]
        return ModelReceipt(
            **self._base_receipt_kwargs(job, launch_surface="fake"),
            artifact_paths=artifacts,
            status="blocked",
            returncode=0,
            started_at=s,
            completed_at=c,
            stdout_sha256=sha256_text(self.body),
            stderr_sha256=sha256_text("UNPARSEABLE_OUTPUT"),
            artifact_sha256=_hash_artifacts(artifacts),
        )


# ---------------------------------------------------------------------------
# Real local subprocess provider
# ---------------------------------------------------------------------------


class LocalToolProvider(Provider):
    """Runs a REAL local subprocess (job.command) and captures the REAL
    returncode + stdout/stderr.  Offline -- no network -- but the verdict is
    not hardcoded: a broken file -> nonzero rc -> error status.

    status mapping:
      * returncode == 0          -> success
      * subprocess.TimeoutExpired -> timed_out
      * nonzero returncode       -> error
    """

    name = "local_tool"

    def run(self, job, *, timeout=None, started_at=None, completed_at=None):
        s, c = _now_pair(started_at, completed_at)
        if not job.command:
            raise ProviderError("LocalToolProvider requires job.command (argv list)")

        stdout_text = ""
        stderr_text = ""
        status = "success"
        returncode: Optional[int] = None
        try:
            proc = subprocess.run(
                job.command,
                cwd=job.cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""
            returncode = proc.returncode
            status = "success" if returncode == 0 else "error"
        except subprocess.TimeoutExpired as exc:
            stdout_text = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr_text = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            status = "timed_out"
            returncode = None
        except FileNotFoundError as exc:
            stderr_text = f"command not found: {exc}"
            status = "error"
            returncode = 127

        artifacts: list[str] = []
        if job.output_path:
            Path(job.output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(job.output_path).write_text(stdout_text, encoding="utf-8")
            artifacts = [job.output_path]

        return ModelReceipt(
            **self._base_receipt_kwargs(job, launch_surface="local_tool"),
            artifact_paths=artifacts,
            status=status,
            returncode=returncode,
            started_at=s,
            completed_at=c,
            stdout_sha256=sha256_text(stdout_text),
            stderr_sha256=sha256_text(stderr_text),
            artifact_sha256=_hash_artifacts(artifacts),
        )


# ---------------------------------------------------------------------------
# Real OpenRouter provider + offline-testable response mapping
# ---------------------------------------------------------------------------


def _canonical_finish_reason(raw: Optional[str]) -> Optional[str]:
    """Map a provider finish_reason onto the canonical OpenAI vocabulary.

    The canonical set is {stop, length, tool_calls, content_filter}.  Anything
    already canonical passes through; unknown raw values map to None on the
    CANONICAL field (the verbatim value still lives in native_finish_reason --
    we never lose the provider signal)."""
    if raw is None:
        return None
    canon = {
        "stop": "stop",
        "length": "length",
        "tool_calls": "tool_calls",
        "content_filter": "content_filter",
    }
    return canon.get(raw)


def map_openrouter_response(
    job: ModelJob,
    *,
    http_status: int,
    body: dict[str, Any],
    started_at: str,
    completed_at: str,
    duration_ms: Optional[int] = None,
    base_kwargs: dict,
) -> ModelReceipt:
    """Map a (http_status, json body) pair into a ModelReceipt.

    Pure + offline: given a recorded fixture this reconstructs the receipt with
    no network.  Success and error are handled as STRUCTURALLY DISJOINT shapes:

      success: body has ``choices`` -> map finish_reason / native_finish_reason /
               message.content / message.reasoning / message.refusal /
               message.tool_calls / usage.* / model_resolved.
      error:   body has top-level ``error`` -> map error_body + error_user_id;
               NO choices/usage are forced.
    """
    raw_excerpt = _raw_excerpt(body)

    # discriminator: choices present vs top-level error (the empirically-derived
    # disjointness from the real OpenRouter responses).
    has_choices = isinstance(body.get("choices"), list) and len(body["choices"]) > 0
    has_top_error = isinstance(body.get("error"), dict)

    sbox = sandbox_config_hash(
        model_resolved=body.get("model"),
        temperature=job.temperature,
        max_tokens=job.max_tokens,
        effort=job.effort,
        system_prompt=job.system_prompt,
        tools=job.tools,
        endpoint=OPENROUTER_ENDPOINT,
    )

    if has_choices and not has_top_error:
        choice = body["choices"][0]
        message = choice.get("message") or {}
        content = message.get("content")
        finish_reason_raw = choice.get("finish_reason")
        native_finish = choice.get("native_finish_reason")
        usage = body.get("usage") or {}
        reasoning = message.get("reasoning")
        reasoning_details = message.get("reasoning_details")
        refusal = message.get("refusal")
        tool_calls = message.get("tool_calls")
        cost = usage.get("cost")
        return ModelReceipt(
            **base_kwargs,
            artifact_paths=[],
            status="success",
            returncode=0,
            started_at=started_at,
            completed_at=completed_at,
            model_resolved=body.get("model"),
            http_status=http_status,
            success_or_error_discriminator="choices_present",
            duration_ms=duration_ms,
            response_id=body.get("id"),
            created=body.get("created"),
            service_tier=body.get("service_tier"),
            system_fingerprint=body.get("system_fingerprint"),
            finish_reason=_canonical_finish_reason(finish_reason_raw),
            native_finish_reason=native_finish,
            message_role=message.get("role"),
            content=content,
            content_empty=(not content),
            reasoning_content=reasoning,
            reasoning_details=reasoning_details,
            has_reasoning=bool(reasoning),
            refusal=refusal,
            content_filter_triggered=(_canonical_finish_reason(finish_reason_raw) == "content_filter"),
            tool_calls=tool_calls,
            has_tool_calls=bool(tool_calls),
            logprobs=choice.get("logprobs"),
            usage_prompt_tokens=usage.get("prompt_tokens"),
            usage_completion_tokens=usage.get("completion_tokens"),
            usage_total_tokens=usage.get("total_tokens"),
            usage_completion_tokens_details=usage.get("completion_tokens_details"),
            usage_cost=cost,
            usage_is_byok=usage.get("is_byok"),
            cost_usd=cost,
            provider_metadata={
                "object": body.get("object"),
                "provider": body.get("provider"),
            },
            raw_response_excerpt=raw_excerpt,
            content_canonical_hash=content_canonical_hash(
                content, _canonical_finish_reason(finish_reason_raw), native_finish
            ),
            sandbox_config_hash=sbox,
        )

    # error shape (DISJOINT): only {error:{code,message}, user_id}
    err = body.get("error") if has_top_error else {"code": http_status, "message": "unrecognized response shape"}
    return ModelReceipt(
        **base_kwargs,
        artifact_paths=[],
        status="error",
        returncode=1,
        started_at=started_at,
        completed_at=completed_at,
        model_resolved=None,
        http_status=http_status,
        success_or_error_discriminator="top_level_error",
        duration_ms=duration_ms,
        error_body={"code": err.get("code"), "message": err.get("message")},
        error_user_id=body.get("user_id"),
        provider_metadata={},
        raw_response_excerpt=raw_excerpt,
        sandbox_config_hash=sbox,
    )


def _raw_excerpt(body: dict[str, Any], limit: int = 1200) -> str:
    import json as _json

    try:
        s = _json.dumps(body, sort_keys=True)
    except (TypeError, ValueError):
        s = str(body)
    return s[:limit]


class OpenRouterProvider(Provider):
    """Makes a REAL HTTP call to OpenRouter chat-completions and maps the
    response into a ModelReceipt.  Requires $OPENROUTER_API_KEY.

    The mapping itself (``map_openrouter_response``) is pure and offline-testable
    against a recorded fixture; this class only adds the network I/O + timing.
    """

    name = "openrouter"

    def __init__(self, api_key: Optional[str] = None, endpoint: str = OPENROUTER_ENDPOINT):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.endpoint = endpoint

    def run(self, job, *, timeout=None, started_at=None, completed_at=None):
        import time

        import requests

        if not self.api_key:
            raise ProviderError("OpenRouterProvider requires OPENROUTER_API_KEY")
        s, c = _now_pair(started_at, completed_at)
        base_kwargs = self._base_receipt_kwargs(job, launch_surface="openrouter")
        # the upstream provider name is filled from the response; default to the
        # launch surface until we know it.
        base_kwargs["provider"] = "openrouter"

        messages = []
        if job.system_prompt:
            messages.append({"role": "system", "content": job.system_prompt})
        messages.append({"role": "user", "content": job.task.prompt})
        payload: dict[str, Any] = {"model": job.model, "messages": messages}
        if job.max_tokens is not None:
            payload["max_tokens"] = job.max_tokens
        if job.temperature is not None:
            payload["temperature"] = job.temperature

        t0 = time.monotonic()
        resp = requests.post(
            self.endpoint,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=timeout or 60,
        )
        dt = int((time.monotonic() - t0) * 1000)
        try:
            body = resp.json()
        except ValueError:
            body = {"error": {"code": resp.status_code, "message": resp.text[:500]}}

        receipt = map_openrouter_response(
            job,
            http_status=resp.status_code,
            body=body,
            started_at=s,
            completed_at=c,
            duration_ms=dt,
            base_kwargs=base_kwargs,
        )
        # set the upstream provider name from the body if present
        if isinstance(body, dict) and body.get("provider"):
            receipt.provider = body["provider"]
        # persist the content as the output artifact, if any
        if job.output_path and receipt.content is not None:
            Path(job.output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(job.output_path).write_text(receipt.content, encoding="utf-8")
            receipt.artifact_paths = [job.output_path]
            receipt.artifact_sha256 = _hash_artifacts(receipt.artifact_paths)
            receipt.stdout_sha256 = sha256_text(receipt.content)
        return receipt
