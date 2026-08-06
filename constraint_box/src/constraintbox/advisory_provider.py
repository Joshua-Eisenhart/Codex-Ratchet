"""Fixed, advisory-only HTTP providers for external ConstraintBox explanations.

The provider boundary has no decision authority.  A caller may choose one
registered provider name; the controller fixes every other request parameter.
"""

from __future__ import annotations

import hashlib
import math
import os
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping

from .advice import (
    AdviceError,
    FORBIDDEN_FIELDS,
    accept_external_advice,
    build_audit_brief,
    decision_sha256,
)
from .intake import IntakeError, canonical_json, parse_json_object
from .user_request import AUTHORITY_FIELDS


RECEIPT_SCHEMA = "constraintbox.advisory-provider-receipt.v1"
STATE_ACCEPTED = "ADVICE_ACCEPTED"
STATE_PARKED = "PARKED"
STATE_REJECTED = "REJECTED"

MAX_BRIEF_BYTES = 32_768
MAX_RESPONSE_BYTES = 65_536
MAX_ASSISTANT_BYTES = 16_384
MAX_TOKENS = 768
TIMEOUT_SECONDS = 20.0

SYSTEM_PROMPT = (
    "You are an advisory-only ConstraintBox explainer. Return exactly one JSON "
    "object and no markdown. The object must contain exactly schema, "
    "decision_sha256, plain_explanation, questions, and suggested_resubmission. "
    "Set schema to constraintbox.audit-advice.v1 and copy decision_sha256 from "
    "the supplied audit brief. plain_explanation must be a JSON string; "
    "questions must be a JSON array of strings; suggested_resubmission must be "
    "a JSON object, using {} when there is no suggestion. Never issue a verdict, alter the frozen "
    "disposition, claim release or promotion authority, or add tool calls."
)
ADVISORY_AUTHORITY_FIELDS = frozenset(
    FORBIDDEN_FIELDS | AUTHORITY_FIELDS
)


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    endpoint: str
    model: str
    credential_env: str
    selection_basis: str
    billing_verified: bool = False


PROVIDER_REGISTRY: Mapping[str, ProviderSpec] = MappingProxyType(
    {
        "nvidia": ProviderSpec(
            name="nvidia",
            endpoint="https://integrate.api.nvidia.com/v1/chat/completions",
            model="nvidia/nemotron-3-nano-30b-a3b",
            credential_env="NVIDIA_API_KEY",
            selection_basis="controller_registry_selected_not_live_verified",
        ),
        "openrouter": ProviderSpec(
            name="openrouter",
            endpoint="https://openrouter.ai/api/v1/chat/completions",
            model="openrouter/free",
            credential_env="OPENROUTER_API_KEY",
            selection_basis=(
                "controller_registry_selected_route_not_live_verified"
            ),
        ),
    }
)


@dataclass(frozen=True)
class TransportResponse:
    status_code: int
    body: bytes


Transport = Callable[
    [str, Mapping[str, str], bytes, float],
    TransportResponse,
]


@dataclass(frozen=True)
class AdvisoryProviderReceipt:
    provider_state: str
    reason_code: str
    provider: str
    provider_sha256: str
    provider_policy_sha256: str | None
    endpoint: str | None
    endpoint_sha256: str | None
    requested_model: str | None
    requested_model_sha256: str | None
    returned_model: str | None
    returned_model_sha256: str | None
    returned_model_matches_request: bool | None
    request_sha256: str | None
    response_sha256: str | None
    decision_sha256: str | None
    advice_sha256: str | None
    advice: dict[str, Any] | None
    http_status: int | None
    response_id: str | None
    finish_reason: str | None
    usage: dict[str, Any] | None
    cost_status: str
    provider_selection_basis: str | None
    billing_verified: bool
    schema: str = RECEIPT_SCHEMA
    advisory_only: bool = True
    decision_authority: bool = False
    release_allowed: bool = False
    promotion_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "provider_state": self.provider_state,
            "reason_code": self.reason_code,
            "provider": self.provider,
            "provider_sha256": self.provider_sha256,
            "provider_policy_sha256": self.provider_policy_sha256,
            "endpoint": self.endpoint,
            "endpoint_sha256": self.endpoint_sha256,
            "requested_model": self.requested_model,
            "requested_model_sha256": self.requested_model_sha256,
            "returned_model": self.returned_model,
            "returned_model_sha256": self.returned_model_sha256,
            "returned_model_matches_request": (
                self.returned_model_matches_request
            ),
            "request_sha256": self.request_sha256,
            "response_sha256": self.response_sha256,
            "decision_sha256": self.decision_sha256,
            "advice_sha256": self.advice_sha256,
            "advice": self.advice,
            "http_status": self.http_status,
            "response_id": self.response_id,
            "finish_reason": self.finish_reason,
            "usage": self.usage,
            "cost_status": self.cost_status,
            "provider_selection_basis": self.provider_selection_basis,
            "billing_verified": self.billing_verified,
            "advisory_only": self.advisory_only,
            "decision_authority": self.decision_authority,
            "release_allowed": self.release_allowed,
            "promotion_allowed": self.promotion_allowed,
        }


class AdvisoryTransportError(RuntimeError):
    """Internal marker whose message is never copied into a receipt."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Keep bearer credentials on the configured origin only."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _text_sha256(value: str) -> str:
    return _sha256(value.encode("utf-8"))


def _provider_policy_sha256(spec: ProviderSpec) -> str:
    """Bind the fixed route and every controller-owned request bound."""

    return _sha256(
        canonical_json(
            {
                "schema": "constraintbox.advisory-provider-policy.v1",
                "provider": spec.name,
                "endpoint": spec.endpoint,
                "model": spec.model,
                "credential_env": spec.credential_env,
                "selection_basis": spec.selection_basis,
                "billing_verified": spec.billing_verified,
                "max_brief_bytes": MAX_BRIEF_BYTES,
                "max_response_bytes": MAX_RESPONSE_BYTES,
                "max_assistant_bytes": MAX_ASSISTANT_BYTES,
                "max_tokens": MAX_TOKENS,
                "timeout_seconds": TIMEOUT_SECONDS,
                "system_prompt": SYSTEM_PROMPT,
                "response_format": "json_object",
                "stream": False,
                "temperature": 0,
            }
        )
    )


def provider_policy_sha256(provider: str) -> str:
    """Return the fixed controller-policy digest for a registered route."""

    spec = PROVIDER_REGISTRY.get(provider)
    if spec is None:
        raise ValueError("unknown advisory provider")
    return _provider_policy_sha256(spec)


def _default_transport(
    endpoint: str,
    headers: Mapping[str, str],
    body: bytes,
    timeout_seconds: float,
) -> TransportResponse:
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers=dict(headers),
        method="POST",
    )
    try:
        opener = urllib.request.build_opener(_NoRedirectHandler())
        with opener.open(request, timeout=timeout_seconds) as response:
            status_code = int(response.status)
            response_body = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        status_code = int(exc.code)
        response_body = exc.read(MAX_RESPONSE_BYTES + 1)
    except (
        urllib.error.URLError,
        TimeoutError,
        socket.timeout,
        OSError,
    ) as exc:
        raise AdvisoryTransportError from exc
    return TransportResponse(status_code=status_code, body=response_body)


def _fixed_request_bytes(
    spec: ProviderSpec,
    frozen_decision: dict[str, Any],
    output_contract: tuple[str, ...],
) -> tuple[bytes, str]:
    if not isinstance(output_contract, tuple) or any(
        not isinstance(item, str) or not item.strip()
        for item in output_contract
    ):
        raise ValueError("output_contract_invalid")
    brief = build_audit_brief(
        frozen_decision,
        output_contract=output_contract,
    )
    brief_bytes = canonical_json(brief)
    if len(brief_bytes) > MAX_BRIEF_BYTES:
        raise ValueError("audit_brief_too_large")
    payload = {
        "model": spec.model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": brief_bytes.decode("utf-8"),
            },
        ],
        "response_format": {"type": "json_object"},
        "stream": False,
        "temperature": 0,
        "max_tokens": MAX_TOKENS,
    }
    return canonical_json(payload), decision_sha256(frozen_decision)


def _receipt(
    *,
    state: str,
    reason_code: str,
    provider: str,
    spec: ProviderSpec | None,
    request_sha256: str | None,
    response_sha256: str | None,
    frozen_decision_sha256: str | None,
    returned_model: str | None = None,
    advice_sha256: str | None = None,
    advice: dict[str, Any] | None = None,
    http_status: int | None = None,
    response_id: str | None = None,
    finish_reason: str | None = None,
    usage: dict[str, Any] | None = None,
    cost_status: str = "UNREPORTED",
) -> AdvisoryProviderReceipt:
    return AdvisoryProviderReceipt(
        provider_state=state,
        reason_code=reason_code,
        provider=provider,
        provider_sha256=_text_sha256(provider),
        provider_policy_sha256=(
            _provider_policy_sha256(spec) if spec is not None else None
        ),
        endpoint=spec.endpoint if spec else None,
        endpoint_sha256=_text_sha256(spec.endpoint) if spec else None,
        requested_model=spec.model if spec else None,
        requested_model_sha256=_text_sha256(spec.model) if spec else None,
        returned_model=returned_model,
        returned_model_sha256=(
            _text_sha256(returned_model) if returned_model is not None else None
        ),
        returned_model_matches_request=(
            returned_model == spec.model
            if returned_model is not None and spec is not None
            else None
        ),
        request_sha256=request_sha256,
        response_sha256=response_sha256,
        decision_sha256=frozen_decision_sha256,
        advice_sha256=advice_sha256,
        advice=advice,
        http_status=http_status,
        response_id=response_id,
        finish_reason=finish_reason,
        usage=usage,
        cost_status=cost_status,
        provider_selection_basis=(
            spec.selection_basis if spec is not None else None
        ),
        billing_verified=spec.billing_verified if spec is not None else False,
    )


@dataclass(frozen=True)
class ExtractedAssistant:
    returned_model: str
    response_id: str
    finish_reason: str
    usage: dict[str, Any] | None
    cost_status: str
    content: bytes


def _sanitized_usage(
    raw_usage: Any,
) -> tuple[dict[str, Any] | None, str]:
    if raw_usage is None:
        return None, "UNREPORTED"
    if not isinstance(raw_usage, dict):
        raise AdviceError("provider usage must be an object")
    try:
        usage = parse_json_object(canonical_json(raw_usage))
    except (IntakeError, TypeError, ValueError, RecursionError) as exc:
        raise AdviceError("provider usage is not canonical JSON") from exc
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        if key not in raw_usage:
            continue
        value = raw_usage[key]
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            raise AdviceError(f"provider usage {key} must be a nonnegative integer")

    cost_fields: list[Any] = []
    stack: list[Any] = [raw_usage]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                if "cost" in key.casefold():
                    cost_fields.append(value)
                elif isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
    if not cost_fields:
        return usage, "UNREPORTED"

    cost_values: list[float] = []
    unresolved = False
    pending = list(cost_fields)
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if not value:
                unresolved = True
            pending.extend(value.values())
        elif isinstance(value, list):
            if not value:
                unresolved = True
            pending.extend(value)
        elif isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            cost_values.append(value)
        elif isinstance(value, float) and math.isfinite(value) and value >= 0:
            cost_values.append(value)
        else:
            unresolved = True
    if unresolved or not cost_values:
        return usage, "REPORTED_UNRESOLVED"
    if any(value != 0 for value in cost_values):
        return usage, "REPORTED_NONZERO"
    return usage, "REPORTED_ZERO"


def _reject_nested_authority_fields(raw: bytes) -> None:
    try:
        body = parse_json_object(raw)
    except IntakeError:
        return
    stack: list[Any] = [body]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            forbidden = sorted(
                key
                for key in current
                if key.casefold() in ADVISORY_AUTHORITY_FIELDS
            )
            if forbidden:
                raise AdviceError(
                    "advice attempted nested decision authority: "
                    + ", ".join(forbidden)
                )
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)


def _extract_assistant(
    raw: bytes,
) -> ExtractedAssistant:
    try:
        response = parse_json_object(raw)
    except IntakeError as exc:
        raise AdviceError("provider response is not strict JSON") from exc
    returned_model = response.get("model")
    if not isinstance(returned_model, str) or not returned_model.strip():
        raise AdviceError("provider response model is missing")
    response_id = response.get("id")
    if not isinstance(response_id, str) or not response_id.strip():
        raise AdviceError("provider response id is missing")
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise AdviceError("provider response must contain exactly one choice")
    choice = choices[0]
    if not isinstance(choice, dict):
        raise AdviceError("provider choice must be an object")
    message = choice.get("message")
    if not isinstance(message, dict):
        raise AdviceError("provider choice message must be an object")
    if "tool_calls" in message or "function_call" in message:
        raise AdviceError("provider attempted a tool call")
    role = message.get("role")
    if role != "assistant":
        raise AdviceError("provider message role must be assistant")
    content = message.get("content")
    if not isinstance(content, str):
        raise AdviceError("provider assistant content must be text")
    finish_reason = choice.get("finish_reason")
    if finish_reason != "stop":
        raise AdviceError("provider completion did not finish with stop")
    content_bytes = content.encode("utf-8")
    if len(content_bytes) > MAX_ASSISTANT_BYTES:
        raise AdviceError("provider assistant content is oversized")
    usage, cost_status = _sanitized_usage(response.get("usage"))
    return ExtractedAssistant(
        returned_model=returned_model,
        response_id=response_id,
        finish_reason=finish_reason,
        usage=usage,
        cost_status=cost_status,
        content=content_bytes,
    )


def run_advisory_audit(
    provider: str,
    frozen_decision: dict[str, Any],
    *,
    output_contract: tuple[str, ...] = (),
    environ: Mapping[str, str] | None = None,
    transport: Transport | None = None,
) -> AdvisoryProviderReceipt:
    """Request advisory text without delegating any ConstraintBox authority."""

    spec = PROVIDER_REGISTRY.get(provider)
    if spec is None:
        return _receipt(
            state=STATE_REJECTED,
            reason_code="unknown_provider",
            provider=provider,
            spec=None,
            request_sha256=None,
            response_sha256=None,
            frozen_decision_sha256=None,
        )

    try:
        request_body, frozen_digest = _fixed_request_bytes(
            spec,
            frozen_decision,
            output_contract,
        )
    except (AttributeError, TypeError, ValueError, RecursionError):
        return _receipt(
            state=STATE_REJECTED,
            reason_code="invalid_or_oversized_audit_brief",
            provider=provider,
            spec=spec,
            request_sha256=None,
            response_sha256=None,
            frozen_decision_sha256=None,
        )
    request_digest = _sha256(request_body)

    environment = os.environ if environ is None else environ
    credential = environment.get(spec.credential_env)
    if not isinstance(credential, str) or not credential.strip():
        return _receipt(
            state=STATE_PARKED,
            reason_code="missing_credential",
            provider=provider,
            spec=spec,
            request_sha256=request_digest,
            response_sha256=None,
            frozen_decision_sha256=frozen_digest,
        )
    try:
        credential_bytes = credential.encode("utf-8")
    except UnicodeEncodeError:
        return _receipt(
            state=STATE_PARKED,
            reason_code="invalid_credential_encoding",
            provider=provider,
            spec=spec,
            request_sha256=request_digest,
            response_sha256=None,
            frozen_decision_sha256=frozen_digest,
        )

    headers = {
        "Authorization": f"Bearer {credential}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    selected_transport = _default_transport if transport is None else transport
    try:
        transported = selected_transport(
            spec.endpoint,
            headers,
            request_body,
            TIMEOUT_SECONDS,
        )
    except Exception:
        # Provider and injected-transport errors are reduced to a fixed code.
        # Raw exception text may contain the credential and is never retained.
        return _receipt(
            state=STATE_PARKED,
            reason_code="transport_error",
            provider=provider,
            spec=spec,
            request_sha256=request_digest,
            response_sha256=None,
            frozen_decision_sha256=frozen_digest,
        )
    if (
        not isinstance(transported, TransportResponse)
        or not isinstance(transported.status_code, int)
        or isinstance(transported.status_code, bool)
        or not isinstance(transported.body, bytes)
    ):
        return _receipt(
            state=STATE_REJECTED,
            reason_code="invalid_transport_response",
            provider=provider,
            spec=spec,
            request_sha256=request_digest,
            response_sha256=None,
            frozen_decision_sha256=frozen_digest,
        )

    response_digest = _sha256(transported.body)
    if credential_bytes in transported.body:
        return _receipt(
            state=STATE_REJECTED,
            reason_code="credential_echoed_by_provider",
            provider=provider,
            spec=spec,
            request_sha256=request_digest,
            response_sha256=response_digest,
            frozen_decision_sha256=frozen_digest,
            http_status=transported.status_code,
        )
    if transported.status_code in {401, 403}:
        return _receipt(
            state=STATE_PARKED,
            reason_code="credential_rejected",
            provider=provider,
            spec=spec,
            request_sha256=request_digest,
            response_sha256=response_digest,
            frozen_decision_sha256=frozen_digest,
            http_status=transported.status_code,
        )
    if transported.status_code in {400, 404, 415, 422}:
        return _receipt(
            state=STATE_PARKED,
            reason_code="provider_request_or_model_incompatible",
            provider=provider,
            spec=spec,
            request_sha256=request_digest,
            response_sha256=response_digest,
            frozen_decision_sha256=frozen_digest,
            http_status=transported.status_code,
        )
    if transported.status_code == 402:
        return _receipt(
            state=STATE_PARKED,
            reason_code="provider_quota_or_billing_unavailable",
            provider=provider,
            spec=spec,
            request_sha256=request_digest,
            response_sha256=response_digest,
            frozen_decision_sha256=frozen_digest,
            http_status=transported.status_code,
        )
    if (
        transported.status_code in {408, 429}
        or 500 <= transported.status_code <= 599
    ):
        return _receipt(
            state=STATE_PARKED,
            reason_code="provider_unavailable",
            provider=provider,
            spec=spec,
            request_sha256=request_digest,
            response_sha256=response_digest,
            frozen_decision_sha256=frozen_digest,
            http_status=transported.status_code,
        )
    if not 200 <= transported.status_code <= 299:
        return _receipt(
            state=STATE_REJECTED,
            reason_code="provider_http_rejected",
            provider=provider,
            spec=spec,
            request_sha256=request_digest,
            response_sha256=response_digest,
            frozen_decision_sha256=frozen_digest,
            http_status=transported.status_code,
        )
    if len(transported.body) > MAX_RESPONSE_BYTES:
        return _receipt(
            state=STATE_REJECTED,
            reason_code="oversized_provider_response",
            provider=provider,
            spec=spec,
            request_sha256=request_digest,
            response_sha256=response_digest,
            frozen_decision_sha256=frozen_digest,
            http_status=transported.status_code,
        )

    returned_model: str | None = None
    response_id: str | None = None
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None
    cost_status = "UNREPORTED"
    try:
        extracted = _extract_assistant(transported.body)
        returned_model = extracted.returned_model
        response_id = extracted.response_id
        finish_reason = extracted.finish_reason
        usage = extracted.usage
        cost_status = extracted.cost_status
        _reject_nested_authority_fields(extracted.content)
        sidecar = accept_external_advice(
            extracted.content,
            frozen_decision=frozen_decision,
        )
    except AdviceError:
        return _receipt(
            state=STATE_REJECTED,
            reason_code="invalid_advisory_output",
            provider=provider,
            spec=spec,
            request_sha256=request_digest,
            response_sha256=response_digest,
            frozen_decision_sha256=frozen_digest,
            returned_model=returned_model,
            http_status=transported.status_code,
            response_id=response_id,
            finish_reason=finish_reason,
            usage=usage,
            cost_status=cost_status,
        )

    rendered_advice = sidecar.to_dict()
    return _receipt(
        state=STATE_ACCEPTED,
        reason_code="advice_schema_accepted",
        provider=provider,
        spec=spec,
        request_sha256=request_digest,
        response_sha256=response_digest,
        frozen_decision_sha256=frozen_digest,
        returned_model=returned_model,
        advice_sha256=sidecar.advice_sha256,
        advice=rendered_advice,
        http_status=transported.status_code,
        response_id=response_id,
        finish_reason=finish_reason,
        usage=usage,
        cost_status=cost_status,
    )
