"""Dataclasses for the offline deterministic LLM harness core.

These types describe the OFFLINE deterministic prune layer of the inverted-tree
engine.  Determinism applies to the SELECTION objects defined here -- the
receipt schema, the gate verdict, the recorded test commands, and artifact
hashes -- NOT to model outputs (which are non-deterministic variation captured
verbatim as data).

Field names are reconciled with the existing receipt family in
``scripts/receipt_schema.py`` (the ``codex_ratchet.sim_result.v1`` /
``engine_leg_result.v*`` schemas):

  * ``schema``            : "codex_ratchet.<thing>.vN" string identifier.
  * ``classification``    : one of the project classifications.
  * ``claim_ceiling``     : FAMILY FREE-TEXT scope string (e.g.
    ``"diagonal_open_channel_memory_fixture_only; not full quantum Hopfield"``).
    A real on-disk ``codex_ratchet.sim_result.v1`` receipt carries this as a
    prose scope sentence -- it is NOT a ranked enum.  See box-viii L2 (2026-06-15):
    the harness gate previously indexed ``claim_ceiling`` into an ordered ladder,
    which COLLIDES with the family's free-text meaning.  The harness promotion
    ladder now lives in the DISTINCT field ``gate_ceiling_rung``.
  * ``gate_ceiling_rung`` : NEW.  The harness promotion ladder (one of
    ``GATE_CEILING_LADDER``).  The gate ranks THIS, never ``claim_ceiling``.
  * ``promotion_allowed`` / ``formal_admission_allowed`` : scope gates.
  * ``tests``             : list of recorded test commands + verdicts.

No conflicting keys are introduced: the new LLM-run-specific keys
(``provider``, ``model_requested``, ``prompt_sha256``, ``returncode`` ...) do
not collide with any key the existing validators read, and ``claim_ceiling``
keeps its family free-text meaning.
"""
from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Schema + enum constants (kept in lock-step with scripts/receipt_schema.py).
# ---------------------------------------------------------------------------

RECEIPT_SCHEMA = "codex_ratchet.llm_run_receipt.v1"

# Classifications accepted on an LLM-run receipt.  This is the project family;
# we deliberately do NOT include the audit/supporting-only labels here because
# an LLM-run receipt is an executable result, not an audit artifact.
VALID_CLASSIFICATIONS = (
    "scratch_diagnostic",
    "classical_baseline",
    "tool_lego_fit_probe",
    "canonical",
)

# Ordered HARNESS promotion ladder.  This ranks ``gate_ceiling_rung`` only --
# NEVER ``claim_ceiling`` (which is family free-text scope).  A receipt may not
# be GATED above ``scratch_diagnostic`` without a separate auditor receipt (no
# self-grading).
GATE_CEILING_LADDER = (
    "scratch_diagnostic",
    "classical_baseline",
    "tool_lego_fit_probe",
    "canonical",
)

# Run lifecycle status.  Success and error are STRUCTURALLY DISJOINT shapes on
# an OpenRouter response (success carries choices/usage/model; error carries
# only {error:{code,message}, user_id} + HTTP 400).  These statuses are the
# harness-side discriminator over those two shapes plus the local fakes.
VALID_STATUSES = (
    "success",
    "blocked",
    "error",
    "timed_out",
    # legacy local-fake aliases kept so the fake providers still classify; the
    # gate admits only "success".
    "completed",
    "failed",
    "not_launched",
)

# Canonical finish_reason values (OpenAI-style).  ``native_finish_reason`` is
# the PROVIDER-SPECIFIC raw value (grok "completed"/"max_output_tokens", gemini
# "STOP"/"MAX_TOKENS", deepseek "stop"/"length") and is preserved VERBATIM --
# do NOT normalize it away.
CANONICAL_FINISH_REASONS = (
    "stop",
    "length",
    "tool_calls",
    "content_filter",
)


def sha256_text(text: str) -> str:
    """Deterministic sha256 hex digest of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Deterministic sha256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def canonicalize_content(content: Optional[str]) -> str:
    """Canonicalize model output text BEFORE hashing.

    The non-deterministic model output is canonicalized so that trivially
    different encodings of the SAME content collapse to one hash:

      * NFC unicode normalization (composed form);
      * trailing whitespace stripped from every line;
      * a single trailing newline removed.

    This is the DETERMINISM-CONSTRUCTED step: two responses whose content
    differs ONLY by trailing whitespace / NFC form hash identically.  It does
    NOT touch interior content (that stays non-deterministic data).
    """
    if content is None:
        return ""
    normalized = unicodedata.normalize("NFC", content)
    lines = [ln.rstrip() for ln in normalized.split("\n")]
    return "\n".join(lines).rstrip("\n")


def content_canonical_hash(
    content: Optional[str],
    finish_reason: Optional[str],
    native_finish_reason: Optional[str],
) -> str:
    """sha256 of the canonicalized content joined with both finish reasons.

    Binds the OUTPUT (after canonicalization) to BOTH the canonical and the
    provider-native stop reason.  Same canonical content + same reasons -> same
    hash regardless of trailing-whitespace / NFC differences (load-bearing:
    different content OR different finish reason -> different hash)."""
    canon = canonicalize_content(content)
    payload = "␟".join(  # unit-separator-ish join, unambiguous
        [canon, finish_reason or "", native_finish_reason or ""]
    )
    return sha256_text(payload)


def sandbox_config_hash(
    *,
    model_resolved: Optional[str],
    temperature: Optional[float],
    max_tokens: Optional[int],
    effort: Optional[str],
    system_prompt: Optional[str],
    tools: Optional[Any],
    endpoint: Optional[str],
) -> str:
    """sha256 binding the GENERATION CONFIG that produced an output.

    Binds: resolved model + temperature + max_tokens + effort/thinkingConfig +
    system prompt + tool definitions + endpoint.  Two runs with a DIFFERENT
    config -> DIFFERENT sandbox_config_hash (load-bearing); identical config ->
    identical hash."""
    import json as _json

    payload = _json.dumps(
        {
            "model_resolved": model_resolved,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "effort": effort,
            "system_prompt": system_prompt,
            "tools": tools,
            "endpoint": endpoint,
        },
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    return sha256_text(payload)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TaskSpec:
    """A single unit of LLM work to dispatch.

    ``task_id`` and ``prompt`` are the load-bearing identity fields; everything
    else is metadata that flows through onto the receipt.

    ``claim_ceiling`` is the FAMILY free-text scope string (kept).
    ``gate_ceiling_rung`` is the harness promotion ladder rung the run REQUESTS
    (the gate ranks this, not claim_ceiling).
    """

    task_id: str
    role: str  # e.g. "builder", "auditor"
    prompt: str
    classification: str = "scratch_diagnostic"
    claim_ceiling: str = ""  # FAMILY free-text scope (may be a prose sentence)
    gate_ceiling_rung: str = "scratch_diagnostic"  # harness ladder rung requested
    input_refs: list[str] = field(default_factory=list)
    audit_required: bool = False

    def prompt_sha256(self) -> str:
        return sha256_text(self.prompt)


@dataclass(frozen=True)
class ModelJob:
    """A TaskSpec bound to a concrete provider + model + output location.

    A ModelJob is what a Provider actually runs.  For LocalToolProvider the
    ``command`` carries the real argv to execute as a subprocess.  For
    OpenRouterProvider ``model`` is the REQUESTED model id (the resolved dated
    slug comes back on the receipt as ``model_resolved``).
    """

    task: TaskSpec
    provider: str  # provider name, e.g. "fake_success", "local_tool", "openrouter"
    model: str  # REQUESTED model id, e.g. "x-ai/grok-4.3"
    output_path: str  # where the provider writes its primary output
    command: Optional[list[str]] = None  # argv for LocalToolProvider
    cwd: Optional[str] = None
    produced_by: str = ""  # trusted author identity; run_job stamps it onto the receipt
    # generation config (used to compute sandbox_config_hash for live providers)
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    effort: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[Any] = None


@dataclass
class TestRecord:
    """One recorded test command + its real verdict.

    ``passed`` is the deterministic verdict.  ``could_fail`` records whether
    this is a load-bearing test (a by-construction check that is true for all
    inputs is NOT a test; it MUST be marked could_fail=False).
    """

    name: str
    command: list[str]
    returncode: Optional[int]
    passed: bool
    could_fail: bool = True
    detail: str = ""


@dataclass
class ModelReceipt:
    """Receipt for a single model/tool run -- schema codex_ratchet.llm_run_receipt.v1.

    The field set is EMPIRICALLY DERIVED from a real OpenRouter chat-completions
    response (x-ai/grok-4.3 -> x-ai/grok-4.3-20260430, provider xAI; recorded
    fixtures under system_v5/tests/fixtures/llm_harness/).  Success and error
    are STRUCTURALLY DISJOINT: a success response carries choices/usage/model; an
    error response carries only ``{error:{code,message}, user_id}`` + HTTP 400.
    Both are representable here; we do not force one shape onto the other.

    Timestamps are passed IN by the caller (started_at / completed_at) so the
    receipt is reproducible: nothing inside the pure logic calls a clock.
    """

    # --- identity / provenance ---
    task_id: str
    role: str
    provider: str  # UPSTREAM provider as reported (e.g. "xAI"); set to launch-surface name for fakes
    launch_surface: str  # how the call was launched, e.g. "openrouter", "local_tool", "fake"
    model_requested: str  # the model id we asked for, e.g. "x-ai/grok-4.3"
    prompt_sha256: str
    input_refs: list[str]
    output_path: Optional[str]
    artifact_paths: list[str]

    # --- execution facts (REAL, captured -- not hardcoded) ---
    status: str  # one of VALID_STATUSES
    returncode: Optional[int]
    started_at: str  # ISO timestamp, passed in
    completed_at: str  # ISO timestamp, passed in

    # --- model-resolution / transport ---
    model_resolved: Optional[str] = None  # dated slug, e.g. "x-ai/grok-4.3-20260430" (!= requested)
    http_status: Optional[int] = None  # 200 / 400 transport status (distinct from in-body error.code)
    # success vs error discriminator: "choices_present" | "top_level_error" | None
    success_or_error_discriminator: Optional[str] = None
    duration_ms: Optional[int] = None

    # --- response identity (success shape) ---
    response_id: Optional[str] = None  # body "id"
    created: Optional[int] = None  # body "created" epoch
    service_tier: Optional[str] = None
    system_fingerprint: Optional[str] = None  # nullable on many providers

    # --- finish reasons (do NOT normalize native away) ---
    finish_reason: Optional[str] = None  # canonical: stop|length|tool_calls|content_filter
    native_finish_reason: Optional[str] = None  # provider-specific, VERBATIM

    # --- message ---
    message_role: Optional[str] = None
    content: Optional[str] = None  # may be empty even on finish_reason=length
    content_empty: bool = True
    reasoning_content: Optional[str] = None  # message.reasoning, nullable
    reasoning_details: Optional[Any] = None  # OPTIONAL, model-dependent (list/dict/None)
    has_reasoning: bool = False
    refusal: Optional[str] = None
    content_filter_triggered: bool = False
    tool_calls: Optional[Any] = None  # optional
    has_tool_calls: bool = False
    logprobs: Optional[Any] = None  # nullable

    # --- usage (success shape) ---
    usage_prompt_tokens: Optional[int] = None
    usage_completion_tokens: Optional[int] = None
    usage_total_tokens: Optional[int] = None
    usage_completion_tokens_details: Optional[Any] = None
    usage_cost: Optional[float] = None
    usage_is_byok: Optional[bool] = None
    cost_usd: Optional[float] = None  # convenience mirror of usage.cost

    # --- error shape (DISJOINT from success) ---
    error_body: Optional[dict[str, Any]] = None  # {"code": int, "message": str}
    error_user_id: Optional[str] = None

    # --- reserved transport diagnostics ---
    rate_limit: Optional[Any] = None  # reserved
    transport_error: Optional[str] = None  # reserved

    # --- provider passthrough + raw excerpt ---
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    raw_response_excerpt: Optional[str] = None

    # --- hashes of captured streams / artifacts ---
    stdout_sha256: Optional[str] = None
    stderr_sha256: Optional[str] = None
    artifact_sha256: dict[str, str] = field(default_factory=dict)

    # --- determinism-constructed hashes ---
    content_canonical_hash: Optional[str] = None  # sha256(NFC+trailing-ws-stripped content + reasons)
    sandbox_config_hash: Optional[str] = None  # sha256(model_resolved+temp+max_tokens+effort+sysprompt+tools+endpoint)

    # tests recorded on this run
    tests: list[TestRecord] = field(default_factory=list)

    # --- mandatory project scope fields ---
    classification: str = "scratch_diagnostic"
    # FAMILY free-text scope (kept, reconciled with receipt_schema.py).  May be a
    # prose sentence -- the gate NEVER ranks this.
    claim_ceiling: str = ""
    # NEW: harness promotion ladder rung -- DISTINCT from claim_ceiling.  The gate
    # ranks THIS against GATE_CEILING_LADDER.
    gate_ceiling_rung: str = "scratch_diagnostic"
    promotion_allowed: bool = False
    formal_admission_allowed: bool = False
    audit_required: bool = False

    # TRUSTED producer/author identity. The no-self-grading rule requires the auditor receipt to
    # carry a DIFFERENT produced_by, not merely a different task_id -- box-viii L1 audit (2026-06-15)
    # caught task_id-difference as a forgeable bypass: the same author mints an "auditor" receipt
    # with a fresh task_id and self-promotes. Author-identity closes that hole.
    produced_by: str = ""

    # link to the separate auditor receipt that satisfies audit_required, if any.
    audit_receipt_id: Optional[str] = None

    # key_id of the PER-IDENTITY notary key this receipt was signed under (executor/notary split).
    # It is part of the signed payload, so author-distinctness for no-self-grading can be verified
    # by key_id (key-backed) rather than by the free-string produced_by (label-backed). A legacy
    # single-key receipt carries key_id=None and verifies under the default boundary key.
    key_id: Optional[str] = None

    # HMAC signature over the canonical receipt (trusted-boundary anchor; box-viii L1c). Produced
    # ONLY by notary.Notary -- the executor (runner/orchestrator) hands an UNSIGNED observation to
    # the notary and never holds key material. The gate verifies this; an unsigned / hand-edited
    # receipt cannot be promoted above scratch_diagnostic.
    signature: Optional[str] = None

    schema: str = RECEIPT_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        """Stable, JSON-serializable dict.  Key order is fixed for byte-stable
        receipts (the gate hashes the canonical JSON of this)."""
        return {
            "schema": self.schema,
            "task_id": self.task_id,
            "role": self.role,
            "provider": self.provider,
            "launch_surface": self.launch_surface,
            "model_requested": self.model_requested,
            "model_resolved": self.model_resolved,
            "prompt_sha256": self.prompt_sha256,
            "input_refs": list(self.input_refs),
            "output_path": self.output_path,
            "artifact_paths": list(self.artifact_paths),
            "status": self.status,
            "success_or_error_discriminator": self.success_or_error_discriminator,
            "returncode": self.returncode,
            "http_status": self.http_status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "response_id": self.response_id,
            "created": self.created,
            "service_tier": self.service_tier,
            "system_fingerprint": self.system_fingerprint,
            "finish_reason": self.finish_reason,
            "native_finish_reason": self.native_finish_reason,
            "message_role": self.message_role,
            "content": self.content,
            "content_empty": self.content_empty,
            "reasoning_content": self.reasoning_content,
            "reasoning_details": self.reasoning_details,
            "has_reasoning": self.has_reasoning,
            "refusal": self.refusal,
            "content_filter_triggered": self.content_filter_triggered,
            "tool_calls": self.tool_calls,
            "has_tool_calls": self.has_tool_calls,
            "logprobs": self.logprobs,
            "usage": {
                "prompt_tokens": self.usage_prompt_tokens,
                "completion_tokens": self.usage_completion_tokens,
                "total_tokens": self.usage_total_tokens,
                "completion_tokens_details": self.usage_completion_tokens_details,
                "cost": self.usage_cost,
                "is_byok": self.usage_is_byok,
            },
            "cost_usd": self.cost_usd,
            "error_body": self.error_body,
            "error_user_id": self.error_user_id,
            "rate_limit": self.rate_limit,
            "transport_error": self.transport_error,
            "provider_metadata": dict(self.provider_metadata),
            "raw_response_excerpt": self.raw_response_excerpt,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
            "artifact_sha256": dict(self.artifact_sha256),
            "content_canonical_hash": self.content_canonical_hash,
            "sandbox_config_hash": self.sandbox_config_hash,
            "tests": [asdict(t) for t in self.tests],
            "classification": self.classification,
            "claim_ceiling": self.claim_ceiling,
            "gate_ceiling_rung": self.gate_ceiling_rung,
            "promotion_allowed": self.promotion_allowed,
            "formal_admission_allowed": self.formal_admission_allowed,
            "audit_required": self.audit_required,
            "produced_by": self.produced_by,
            "audit_receipt_id": self.audit_receipt_id,
            "key_id": self.key_id,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ModelReceipt":
        tests = [TestRecord(**t) for t in payload.get("tests", [])]
        usage = payload.get("usage") or {}
        return cls(
            task_id=payload["task_id"],
            role=payload["role"],
            provider=payload["provider"],
            launch_surface=payload.get("launch_surface", payload["provider"]),
            model_requested=payload.get("model_requested") or payload.get("model", ""),
            prompt_sha256=payload["prompt_sha256"],
            input_refs=list(payload.get("input_refs", [])),
            output_path=payload.get("output_path"),
            artifact_paths=list(payload.get("artifact_paths", [])),
            status=payload["status"],
            returncode=payload.get("returncode"),
            started_at=payload["started_at"],
            completed_at=payload["completed_at"],
            model_resolved=payload.get("model_resolved"),
            http_status=payload.get("http_status"),
            success_or_error_discriminator=payload.get("success_or_error_discriminator"),
            duration_ms=payload.get("duration_ms"),
            response_id=payload.get("response_id"),
            created=payload.get("created"),
            service_tier=payload.get("service_tier"),
            system_fingerprint=payload.get("system_fingerprint"),
            finish_reason=payload.get("finish_reason"),
            native_finish_reason=payload.get("native_finish_reason"),
            message_role=payload.get("message_role"),
            content=payload.get("content"),
            content_empty=bool(payload.get("content_empty", True)),
            reasoning_content=payload.get("reasoning_content"),
            reasoning_details=payload.get("reasoning_details"),
            has_reasoning=bool(payload.get("has_reasoning", False)),
            refusal=payload.get("refusal"),
            content_filter_triggered=bool(payload.get("content_filter_triggered", False)),
            tool_calls=payload.get("tool_calls"),
            has_tool_calls=bool(payload.get("has_tool_calls", False)),
            logprobs=payload.get("logprobs"),
            usage_prompt_tokens=usage.get("prompt_tokens"),
            usage_completion_tokens=usage.get("completion_tokens"),
            usage_total_tokens=usage.get("total_tokens"),
            usage_completion_tokens_details=usage.get("completion_tokens_details"),
            usage_cost=usage.get("cost"),
            usage_is_byok=usage.get("is_byok"),
            cost_usd=payload.get("cost_usd"),
            error_body=payload.get("error_body"),
            error_user_id=payload.get("error_user_id"),
            rate_limit=payload.get("rate_limit"),
            transport_error=payload.get("transport_error"),
            provider_metadata=dict(payload.get("provider_metadata", {})),
            raw_response_excerpt=payload.get("raw_response_excerpt"),
            stdout_sha256=payload.get("stdout_sha256"),
            stderr_sha256=payload.get("stderr_sha256"),
            artifact_sha256=dict(payload.get("artifact_sha256", {})),
            content_canonical_hash=payload.get("content_canonical_hash"),
            sandbox_config_hash=payload.get("sandbox_config_hash"),
            tests=tests,
            classification=payload.get("classification", "scratch_diagnostic"),
            claim_ceiling=payload.get("claim_ceiling", ""),
            gate_ceiling_rung=payload.get("gate_ceiling_rung", "scratch_diagnostic"),
            promotion_allowed=bool(payload.get("promotion_allowed", False)),
            formal_admission_allowed=bool(payload.get("formal_admission_allowed", False)),
            audit_required=bool(payload.get("audit_required", False)),
            produced_by=payload.get("produced_by", ""),
            audit_receipt_id=payload.get("audit_receipt_id"),
            key_id=payload.get("key_id"),
            signature=payload.get("signature"),
            schema=payload.get("schema", RECEIPT_SCHEMA),
        )


@dataclass
class GateResult:
    """Deterministic verdict on a ModelReceipt.

    Same receipt in -> identical GateResult out.  No clock, no random.
    """

    schema: str
    task_id: str
    receipt_sha256: str  # hash of the canonical receipt JSON the gate verdict is bound to
    admitted: bool
    verdict: str  # "admit" | "reject"
    reasons: list[str]
    checks: list[dict[str, Any]]  # per-check {name, passed, could_fail, detail}
    granted_rung: str  # the harness ladder rung actually granted by the gate

    GATE_SCHEMA = "codex_ratchet.llm_gate_result.v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "task_id": self.task_id,
            "receipt_sha256": self.receipt_sha256,
            "admitted": self.admitted,
            "verdict": self.verdict,
            "reasons": list(self.reasons),
            "checks": [dict(c) for c in self.checks],
            "granted_rung": self.granted_rung,
        }


@dataclass
class HarnessRun:
    """A batch of jobs, their receipts, and their gate results."""

    run_id: str
    jobs: list[ModelJob] = field(default_factory=list)
    receipts: list[ModelReceipt] = field(default_factory=list)
    gate_results: list[GateResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "codex_ratchet.llm_harness_run.v1",
            "run_id": self.run_id,
            "receipts": [r.to_dict() for r in self.receipts],
            "gate_results": [g.to_dict() for g in self.gate_results],
        }
