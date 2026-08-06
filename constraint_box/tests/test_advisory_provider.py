from __future__ import annotations

import hashlib
import inspect
import json
import unittest
from unittest import mock

import constraintbox.advisory_provider as provider_module
from constraintbox.advice import (
    ADVICE_SCHEMA,
    build_audit_brief,
    decision_sha256,
)
from constraintbox.advisory_provider import (
    MAX_ASSISTANT_BYTES,
    MAX_RESPONSE_BYTES,
    MAX_TOKENS,
    PROVIDER_REGISTRY,
    STATE_ACCEPTED,
    STATE_PARKED,
    STATE_REJECTED,
    SYSTEM_PROMPT,
    TIMEOUT_SECONDS,
    TransportResponse,
    run_advisory_audit,
)
from constraintbox.intake import canonical_json, parse_json_object


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class CapturingTransport:
    def __init__(self, response: TransportResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, str], bytes, float]] = []

    def __call__(
        self,
        endpoint: str,
        headers: object,
        body: bytes,
        timeout_seconds: float,
    ) -> TransportResponse:
        self.calls.append(
            (endpoint, dict(headers), body, timeout_seconds)  # type: ignore[arg-type]
        )
        return self.response


class AdvisoryProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.decision = {
            "schema": "constraintbox.test-decision.v1",
            "disposition": "PARKED",
            "reason": "The owner must make one assumption explicit.",
            "failed_clauses": ["assumption_status"],
            "questions": ["Should the boundary be inclusive?"],
            "claim_ceiling": "proposal_only",
        }

    def advice_body(
        self,
        *,
        extra: dict[str, object] | None = None,
    ) -> dict[str, object]:
        body: dict[str, object] = {
            "schema": ADVICE_SCHEMA,
            "decision_sha256": decision_sha256(self.decision),
            "plain_explanation": "The boundary assumption is still unknown.",
            "questions": ["Should the boundary be inclusive?"],
            "suggested_resubmission": {
                "assumption": "The boundary is inclusive."
            },
        }
        if extra:
            body.update(extra)
        return body

    def provider_response(
        self,
        *,
        model: str,
        advice: bytes | None = None,
    ) -> bytes:
        assistant = (
            canonical_json(self.advice_body()) if advice is None else advice
        )
        return canonical_json(
            {
                "id": "offline-test",
                "object": "chat.completion",
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": assistant.decode("utf-8"),
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 10,
                },
            }
        )

    def test_registry_is_fixed_to_the_two_advisory_providers(self) -> None:
        self.assertEqual(set(PROVIDER_REGISTRY), {"nvidia", "openrouter"})
        self.assertEqual(
            PROVIDER_REGISTRY["nvidia"].endpoint,
            "https://integrate.api.nvidia.com/v1/chat/completions",
        )
        self.assertEqual(
            PROVIDER_REGISTRY["nvidia"].model,
            "nvidia/nemotron-3-nano-30b-a3b",
        )
        self.assertEqual(
            PROVIDER_REGISTRY["nvidia"].credential_env,
            "NVIDIA_API_KEY",
        )
        self.assertEqual(
            PROVIDER_REGISTRY["openrouter"].endpoint,
            "https://openrouter.ai/api/v1/chat/completions",
        )
        self.assertEqual(
            PROVIDER_REGISTRY["openrouter"].model,
            "openrouter/free",
        )
        self.assertEqual(
            PROVIDER_REGISTRY["openrouter"].credential_env,
            "OPENROUTER_API_KEY",
        )
        with self.assertRaises(TypeError):
            PROVIDER_REGISTRY["nvidia"] = PROVIDER_REGISTRY["openrouter"]  # type: ignore[index]

    def test_caller_can_select_provider_but_not_request_authority(self) -> None:
        parameters = inspect.signature(run_advisory_audit).parameters
        self.assertEqual(
            set(parameters),
            {
                "provider",
                "frozen_decision",
                "output_contract",
                "environ",
                "transport",
            },
        )
        for forbidden in ("endpoint", "model", "temperature", "tools"):
            self.assertNotIn(forbidden, parameters)
        with self.assertRaises(TypeError):
            run_advisory_audit(
                "nvidia",
                self.decision,
                environ={"NVIDIA_API_KEY": "offline"},
                endpoint="https://attacker.invalid",  # type: ignore[call-arg]
            )
        with self.assertRaises(TypeError):
            run_advisory_audit(
                "nvidia",
                self.decision,
                environ={"NVIDIA_API_KEY": "offline"},
                model="attacker/model",  # type: ignore[call-arg]
            )

    def test_exact_payload_is_controller_built_for_each_provider(self) -> None:
        for provider, env_name in (
            ("nvidia", "NVIDIA_API_KEY"),
            ("openrouter", "OPENROUTER_API_KEY"),
        ):
            with self.subTest(provider=provider):
                spec = PROVIDER_REGISTRY[provider]
                response = self.provider_response(model=spec.model)
                transport = CapturingTransport(
                    TransportResponse(200, response)
                )
                receipt = run_advisory_audit(
                    provider,
                    self.decision,
                    output_contract=("plain_explanation", "questions"),
                    environ={env_name: "offline-secret"},
                    transport=transport,
                )

                self.assertEqual(receipt.provider_state, STATE_ACCEPTED)
                self.assertEqual(len(transport.calls), 1)
                endpoint, headers, raw, timeout = transport.calls[0]
                brief = canonical_json(
                    build_audit_brief(
                        self.decision,
                        output_contract=(
                            "plain_explanation",
                            "questions",
                        ),
                    )
                ).decode("utf-8")
                expected = {
                    "model": spec.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": brief},
                    ],
                    "response_format": {"type": "json_object"},
                    "stream": False,
                    "temperature": 0,
                    "max_tokens": MAX_TOKENS,
                }
                self.assertEqual(endpoint, spec.endpoint)
                self.assertEqual(parse_json_object(raw), expected)
                self.assertNotIn("tools", expected)
                self.assertEqual(timeout, TIMEOUT_SECONDS)
                self.assertEqual(
                    headers,
                    {
                        "Authorization": "Bearer offline-secret",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                )
                self.assertNotIn(
                    "offline-secret",
                    canonical_json(receipt.to_dict()).decode("utf-8"),
                )

    def test_missing_credential_is_typed_parked_without_transport(self) -> None:
        def must_not_run(*args: object) -> TransportResponse:
            self.fail(f"transport ran without a credential: {args!r}")

        receipt = run_advisory_audit(
            "nvidia",
            self.decision,
            environ={},
            transport=must_not_run,
        )

        self.assertEqual(receipt.provider_state, STATE_PARKED)
        self.assertEqual(receipt.reason_code, "missing_credential")
        self.assertIsNotNone(receipt.request_sha256)
        self.assertIsNone(receipt.response_sha256)
        self.assertRegex(
            receipt.provider_policy_sha256 or "",
            r"^[0-9a-f]{64}$",
        )
        self.assertFalse(receipt.decision_authority)
        self.assertFalse(receipt.release_allowed)
        self.assertFalse(receipt.promotion_allowed)

    def test_default_transport_installs_the_no_redirect_handler(self) -> None:
        class OfflineResponse:
            status = 200

            def __enter__(self) -> "OfflineResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def read(self, amount: int) -> bytes:
                self.amount = amount
                return b"{}"

        class OfflineOpener:
            def open(
                self,
                request: object,
                *,
                timeout: float,
            ) -> OfflineResponse:
                self.request = request
                self.timeout = timeout
                return OfflineResponse()

        opener = OfflineOpener()
        with mock.patch.object(
            provider_module.urllib.request,
            "build_opener",
            return_value=opener,
        ) as build_opener:
            response = provider_module._default_transport(
                PROVIDER_REGISTRY["nvidia"].endpoint,
                {"Authorization": "Bearer offline-secret"},
                b"{}",
                TIMEOUT_SECONDS,
            )

        self.assertEqual(response, TransportResponse(200, b"{}"))
        handler = build_opener.call_args.args[0]
        self.assertIsInstance(
            handler,
            provider_module._NoRedirectHandler,
        )
        self.assertIsNone(
            handler.redirect_request(
                None,
                None,
                302,
                "redirect",
                {},
                "https://attacker.invalid",
            )
        )

    def test_valid_assistant_json_is_accepted_only_as_advice(self) -> None:
        raw_response = self.provider_response(
            model=PROVIDER_REGISTRY["nvidia"].model
        )
        transport = CapturingTransport(TransportResponse(200, raw_response))

        receipt = run_advisory_audit(
            "nvidia",
            self.decision,
            environ={"NVIDIA_API_KEY": "offline-secret"},
            transport=transport,
        )
        rendered = receipt.to_dict()

        self.assertEqual(receipt.provider_state, STATE_ACCEPTED)
        self.assertEqual(receipt.reason_code, "advice_schema_accepted")
        self.assertEqual(receipt.http_status, 200)
        self.assertEqual(receipt.response_id, "offline-test")
        self.assertEqual(receipt.finish_reason, "stop")
        self.assertEqual(
            receipt.usage,
            {"prompt_tokens": 10, "completion_tokens": 10},
        )
        self.assertEqual(receipt.cost_status, "UNREPORTED")
        self.assertFalse(receipt.billing_verified)
        self.assertEqual(
            receipt.decision_sha256,
            decision_sha256(self.decision),
        )
        self.assertEqual(receipt.response_sha256, sha256(raw_response))
        self.assertEqual(
            receipt.request_sha256,
            sha256(transport.calls[0][2]),
        )
        self.assertEqual(
            receipt.advice_sha256,
            receipt.advice["advice_sha256"],  # type: ignore[index]
        )
        self.assertTrue(rendered["advisory_only"])
        self.assertFalse(rendered["decision_authority"])
        self.assertFalse(rendered["release_allowed"])
        self.assertFalse(rendered["promotion_allowed"])
        self.assertNotIn("verdict", rendered)

    def test_returned_model_mismatch_is_retained_without_authority(self) -> None:
        actual_model = "router-selected/free-model"
        response = self.provider_response(model=actual_model)
        receipt = run_advisory_audit(
            "openrouter",
            self.decision,
            environ={"OPENROUTER_API_KEY": "offline-secret"},
            transport=CapturingTransport(TransportResponse(200, response)),
        )

        self.assertEqual(receipt.provider_state, STATE_ACCEPTED)
        self.assertEqual(receipt.requested_model, "openrouter/free")
        self.assertEqual(receipt.returned_model, actual_model)
        self.assertFalse(receipt.returned_model_matches_request)
        self.assertEqual(
            receipt.returned_model_sha256,
            sha256(actual_model.encode("utf-8")),
        )
        self.assertFalse(receipt.decision_authority)
        self.assertFalse(receipt.release_allowed)

    def test_oversized_response_and_assistant_are_rejected(self) -> None:
        oversized_response = b"{" + b" " * MAX_RESPONSE_BYTES + b"}"
        response_receipt = run_advisory_audit(
                "nvidia",
                self.decision,
                environ={
                    "NVIDIA_API_KEY": "test-provider-key-not-in-response"
                },
                transport=CapturingTransport(
                    TransportResponse(200, oversized_response)
                ),
        )
        self.assertEqual(response_receipt.provider_state, STATE_REJECTED)
        self.assertEqual(
            response_receipt.reason_code,
            "oversized_provider_response",
        )

        oversized_assistant = json.dumps(
            {
                "schema": ADVICE_SCHEMA,
                "decision_sha256": decision_sha256(self.decision),
                "plain_explanation": "x" * MAX_ASSISTANT_BYTES,
                "questions": [],
                "suggested_resubmission": {},
            },
            separators=(",", ":"),
        ).encode("utf-8")
        assistant_receipt = run_advisory_audit(
            "nvidia",
            self.decision,
            environ={
                "NVIDIA_API_KEY": "test-provider-key-not-in-response"
            },
            transport=CapturingTransport(
                TransportResponse(
                    200,
                    self.provider_response(
                        model=PROVIDER_REGISTRY["nvidia"].model,
                        advice=oversized_assistant,
                    ),
                )
            ),
        )
        self.assertEqual(assistant_receipt.provider_state, STATE_REJECTED)
        self.assertEqual(
            assistant_receipt.reason_code,
            "invalid_advisory_output",
        )

    def test_non_json_and_forbidden_verdict_are_rejected(self) -> None:
        cases = {
            "outer-not-json": b"not JSON",
            "assistant-not-json": self.provider_response(
                model=PROVIDER_REGISTRY["nvidia"].model,
                advice=b"not JSON",
            ),
            "forbidden-verdict": self.provider_response(
                model=PROVIDER_REGISTRY["nvidia"].model,
                advice=canonical_json(
                    self.advice_body(extra={"verdict": "PASS"})
                ),
            ),
        }
        for name, response in cases.items():
            with self.subTest(name=name):
                receipt = run_advisory_audit(
                    "nvidia",
                    self.decision,
                    environ={
                        "NVIDIA_API_KEY": "test-provider-key-not-in-response"
                    },
                    transport=CapturingTransport(
                        TransportResponse(200, response)
                    ),
                )
                self.assertEqual(receipt.provider_state, STATE_REJECTED)
                self.assertEqual(
                    receipt.reason_code,
                    "invalid_advisory_output",
                )
                self.assertFalse(receipt.decision_authority)

    def test_nested_authority_field_and_nonstop_completion_are_rejected(
        self,
    ) -> None:
        nested = self.advice_body()
        nested["suggested_resubmission"] = {
            "request": {
                "checker": "self",
                "tool": "self",
                "Pass": True,
            }
        }
        nested_receipt = run_advisory_audit(
            "nvidia",
            self.decision,
            environ={
                "NVIDIA_API_KEY": "test-provider-key-not-in-response"
            },
            transport=CapturingTransport(
                TransportResponse(
                    200,
                    self.provider_response(
                        model=PROVIDER_REGISTRY["nvidia"].model,
                        advice=canonical_json(nested),
                    ),
                )
            ),
        )
        self.assertEqual(nested_receipt.provider_state, STATE_REJECTED)
        self.assertEqual(
            nested_receipt.reason_code,
            "invalid_advisory_output",
        )

        truncated_response = parse_json_object(
            self.provider_response(
                model=PROVIDER_REGISTRY["nvidia"].model,
            )
        )
        truncated_response["choices"][0]["finish_reason"] = "length"
        truncated_receipt = run_advisory_audit(
            "nvidia",
            self.decision,
            environ={
                "NVIDIA_API_KEY": "test-provider-key-not-in-response"
            },
            transport=CapturingTransport(
                TransportResponse(200, canonical_json(truncated_response))
            ),
        )
        self.assertEqual(truncated_receipt.provider_state, STATE_REJECTED)
        self.assertEqual(
            truncated_receipt.reason_code,
            "invalid_advisory_output",
        )
        self.assertIsNone(truncated_receipt.advice)

    def test_reported_zero_cost_is_metadata_not_authority(self) -> None:
        response = parse_json_object(
            self.provider_response(model="router-selected/free-model")
        )
        response["usage"]["total_tokens"] = 20
        response["usage"]["cost"] = 0
        receipt = run_advisory_audit(
            "openrouter",
            self.decision,
            environ={
                "OPENROUTER_API_KEY": "test-provider-key-not-in-response"
            },
            transport=CapturingTransport(
                TransportResponse(200, canonical_json(response))
            ),
        )
        self.assertEqual(receipt.provider_state, STATE_ACCEPTED)
        self.assertEqual(receipt.cost_status, "REPORTED_ZERO")
        self.assertEqual(receipt.usage["cost"], 0)  # type: ignore[index]
        self.assertFalse(receipt.billing_verified)
        self.assertFalse(receipt.decision_authority)
        self.assertFalse(receipt.release_allowed)

    def test_transport_failure_and_rate_limit_are_typed_parked(self) -> None:
        secret = "do-not-copy-this-secret"

        def failing_transport(*args: object) -> TransportResponse:
            raise RuntimeError(f"provider failed with {secret}")

        transport_receipt = run_advisory_audit(
            "nvidia",
            self.decision,
            environ={"NVIDIA_API_KEY": secret},
            transport=failing_transport,
        )
        self.assertEqual(transport_receipt.provider_state, STATE_PARKED)
        self.assertEqual(transport_receipt.reason_code, "transport_error")
        self.assertNotIn(
            secret,
            canonical_json(transport_receipt.to_dict()).decode("utf-8"),
        )

        rate_receipt = run_advisory_audit(
            "openrouter",
            self.decision,
            environ={"OPENROUTER_API_KEY": secret},
            transport=CapturingTransport(
                TransportResponse(429, b'{"error":"rate limited"}')
            ),
        )
        self.assertEqual(rate_receipt.provider_state, STATE_PARKED)
        self.assertEqual(rate_receipt.reason_code, "provider_unavailable")
        self.assertNotIn(
            secret,
            canonical_json(rate_receipt.to_dict()).decode("utf-8"),
        )

    def test_provider_incompatibility_and_quota_are_typed_parked(self) -> None:
        for status, reason in (
            (400, "provider_request_or_model_incompatible"),
            (404, "provider_request_or_model_incompatible"),
            (415, "provider_request_or_model_incompatible"),
            (422, "provider_request_or_model_incompatible"),
            (402, "provider_quota_or_billing_unavailable"),
        ):
            with self.subTest(status=status):
                receipt = run_advisory_audit(
                    "openrouter",
                    self.decision,
                    environ={"OPENROUTER_API_KEY": "test-key"},
                    transport=CapturingTransport(
                        TransportResponse(status, b"{}")
                    ),
                )
                self.assertEqual(receipt.provider_state, STATE_PARKED)
                self.assertEqual(receipt.reason_code, reason)
                self.assertFalse(receipt.decision_authority)
                self.assertFalse(receipt.release_allowed)
                self.assertFalse(receipt.promotion_allowed)

    def test_provider_cannot_echo_the_credential_into_recorded_advice(self) -> None:
        secret = "never-record-this-provider-key"
        echoed_advice = self.advice_body()
        echoed_advice["plain_explanation"] = f"Credential: {secret}"
        raw_response = self.provider_response(
            model=PROVIDER_REGISTRY["nvidia"].model,
            advice=canonical_json(echoed_advice),
        )

        receipt = run_advisory_audit(
            "nvidia",
            self.decision,
            environ={"NVIDIA_API_KEY": secret},
            transport=CapturingTransport(
                TransportResponse(200, raw_response)
            ),
        )

        self.assertEqual(receipt.provider_state, STATE_REJECTED)
        self.assertEqual(
            receipt.reason_code,
            "credential_echoed_by_provider",
        )
        self.assertIsNone(receipt.advice)
        self.assertNotIn(
            secret,
            canonical_json(receipt.to_dict()).decode("utf-8"),
        )

    def test_unknown_provider_is_rejected_without_becoming_a_verdict(self) -> None:
        receipt = run_advisory_audit(
            "attacker-provider",
            self.decision,
            environ={},
        )
        rendered = receipt.to_dict()
        self.assertEqual(receipt.provider_state, STATE_REJECTED)
        self.assertEqual(receipt.reason_code, "unknown_provider")
        self.assertFalse(rendered["decision_authority"])
        self.assertFalse(rendered["release_allowed"])
        self.assertFalse(rendered["promotion_allowed"])
        self.assertNotIn("disposition", rendered)
        self.assertNotIn("verdict", rendered)


if __name__ == "__main__":
    unittest.main()
