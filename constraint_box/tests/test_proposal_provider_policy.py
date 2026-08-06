from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from constraintbox._provider_harness.providers import OpenRouterProvider
from constraintbox._provider_harness.types import ModelJob, TaskSpec
from constraintbox.proposal_provider_policy import (
    POLICY_SCHEMA,
    ROUTE_ENV,
    ProposalProviderPolicyError,
    select_proposal_provider,
)


class _LocalProvider:
    name = "local_tool"


class _OpenRouterProvider:
    name = "openrouter"

    def __init__(self, *, api_key: str) -> None:
        self.api_key = api_key


class _NvidiaProvider:
    name = "nvidia"

    def __init__(self, *, api_key: str) -> None:
        self.api_key = api_key


def _components() -> dict[str, object]:
    return {
        "LocalToolProvider": _LocalProvider,
        "OpenRouterProvider": _OpenRouterProvider,
        "NvidiaProvider": _NvidiaProvider,
    }


class ProposalProviderPolicyTests(unittest.TestCase):
    def test_default_route_is_local_and_has_no_operator_override(self) -> None:
        selection = select_proposal_provider(_components(), environ={})

        self.assertEqual(selection.route.route, "local_tool")
        self.assertIsInstance(selection.provider, _LocalProvider)
        self.assertFalse(selection.operator_selected)
        binding = selection.public_binding()
        self.assertEqual(binding["schema"], POLICY_SCHEMA)
        self.assertEqual(binding["requested_model"], "codex-cli-default")
        self.assertFalse(binding["credential_configured"])
        self.assertFalse(binding["llm_decision_authority"])
        self.assertFalse(binding["promotion_allowed"])

    def test_remote_routes_are_exact_static_models_with_explicit_credentials(self) -> None:
        cases = (
            ("openrouter", "OPENROUTER_API_KEY", _OpenRouterProvider, "openrouter/free"),
            ("nvidia", "NVIDIA_API_KEY", _NvidiaProvider, "nvidia/nemotron-3-nano-30b-a3b"),
        )
        for route, key_name, provider_type, model in cases:
            with self.subTest(route=route):
                secret = f"{route}-secret"
                selection = select_proposal_provider(
                    _components(),
                    environ={ROUTE_ENV: route, key_name: secret},
                )
                self.assertTrue(selection.operator_selected)
                self.assertIsInstance(selection.provider, provider_type)
                self.assertEqual(selection.provider.api_key, secret)
                binding = selection.public_binding()
                self.assertEqual(binding["route"], route)
                self.assertEqual(binding["requested_model"], model)
                self.assertTrue(binding["credential_configured"])
                self.assertNotIn(secret, json.dumps(binding, sort_keys=True))

    def test_invalid_or_missing_operator_route_fails_closed_without_local_fallback(self) -> None:
        with self.assertRaisesRegex(ProposalProviderPolicyError, ROUTE_ENV):
            select_proposal_provider(
                _components(),
                environ={ROUTE_ENV: "untrusted-request-value"},
            )
        with self.assertRaisesRegex(ProposalProviderPolicyError, "OPENROUTER_API_KEY"):
            select_proposal_provider(
                _components(),
                environ={ROUTE_ENV: "openrouter"},
            )

    def test_openrouter_transport_is_stdlib_injectable_and_never_serializes_key(self) -> None:
        captured: dict[str, object] = {}

        def transport(
            endpoint: str,
            headers: dict[str, str],
            body: bytes,
            timeout_seconds: float,
        ) -> tuple[int, bytes]:
            captured.update(
                {
                    "endpoint": endpoint,
                    "headers": headers,
                    "body": json.loads(body),
                    "timeout_seconds": timeout_seconds,
                }
            )
            return (
                200,
                json.dumps(
                    {
                        "id": "offline-openrouter-response",
                        "model": "openrouter/free",
                        "provider": "offline-upstream",
                        "choices": [
                            {
                                "finish_reason": "stop",
                                "native_finish_reason": "stop",
                                "message": {
                                    "role": "assistant",
                                    "content": "{\"bounded\":true}",
                                },
                            }
                        ],
                        "usage": {"prompt_tokens": 3, "completion_tokens": 2},
                    }
                ).encode("utf-8"),
            )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "provider-output.json"
            job = ModelJob(
                task=TaskSpec(
                    task_id="provider-policy-offline",
                    role="builder",
                    prompt="return one JSON object",
                    claim_ceiling="bounded_tool_execution",
                ),
                provider="openrouter",
                model="openrouter/free",
                output_path=str(output),
                max_tokens=64,
                temperature=0.0,
            )
            provider = OpenRouterProvider(
                api_key="never-in-receipt",
                transport=transport,
            )
            receipt = provider.run(
                job,
                timeout=3,
                started_at="2026-07-31T00:00:00+00:00",
                completed_at="2026-07-31T00:00:01+00:00",
            )

            self.assertEqual(captured["body"]["model"], "openrouter/free")
            self.assertEqual(captured["body"]["max_tokens"], 64)
            self.assertEqual(captured["headers"]["Content-Type"], "application/json")
            self.assertEqual(receipt.launch_surface, "openrouter")
            self.assertEqual(receipt.status, "success")
            self.assertEqual(receipt.content, '{"bounded":true}')
            self.assertEqual(output.read_text(encoding="utf-8"), '{"bounded":true}')
            self.assertNotIn("never-in-receipt", json.dumps(receipt.to_dict()))


if __name__ == "__main__":
    unittest.main()
