from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import constraintbox.advisory_run as advisory_run_module
from constraintbox.advice import (
    ADVICE_SCHEMA,
    build_audit_brief,
    deterministic_explanation,
)
from constraintbox.advisory_provider import (
    PROVIDER_REGISTRY,
    STATE_ACCEPTED,
    STATE_PARKED,
    STATE_REJECTED,
    TransportResponse,
)
from constraintbox.advisory_run import (
    SIDECAR_ROOT_SCHEMA,
    AdvisoryRunError,
    run_advisory_sidecar,
)
from constraintbox.boxrun import READY_FOR_PROPOSAL, run_first_box
from constraintbox.intake import canonical_json, parse_json_object


BOX_ROOT = Path(__file__).resolve().parents[1]
REQUEST = BOX_ROOT / "fixtures" / "requests" / "assemble_constraintbox_v1.json"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class FakePassingBroker:
    def run(self) -> dict[str, object]:
        return {
            "schema": "constraintbox.external-engine-packet-receipt.v1",
            "status": "PASS",
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "engine_readiness_claim": False,
            "promotion_allowed": False,
        }


class AdaptiveTransport:
    def __init__(self, *, forbidden_authority: bool = False) -> None:
        self.forbidden_authority = forbidden_authority
        self.calls = 0
        self.briefs: list[dict[str, object]] = []

    def __call__(
        self,
        endpoint: str,
        headers: object,
        body: bytes,
        timeout_seconds: float,
    ) -> TransportResponse:
        del endpoint, headers, timeout_seconds
        self.calls += 1
        payload = parse_json_object(body)
        messages = payload["messages"]
        if not isinstance(messages, list):
            raise TypeError("messages must be a list")
        user_message = messages[1]
        if not isinstance(user_message, dict):
            raise TypeError("user message must be an object")
        content = user_message["content"]
        if not isinstance(content, str):
            raise TypeError("user content must be text")
        brief = parse_json_object(content.encode("utf-8"))
        self.briefs.append(brief)
        suggested: dict[str, object] = {
            "goal": "A more explicit restatement."
        }
        if self.forbidden_authority:
            suggested = {"nested": {"verdict": "PASS"}}
        advice = {
            "schema": ADVICE_SCHEMA,
            "decision_sha256": brief["decision_sha256"],
            "plain_explanation": (
                "The deterministic box decision is frozen; this text only "
                "explains it."
            ),
            "questions": ["Would you like to make the boundary more explicit?"],
            "suggested_resubmission": suggested,
        }
        response = {
            "id": "offline-advisory-test",
            "object": "chat.completion",
            "model": payload["model"],
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": canonical_json(advice).decode("utf-8"),
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 8,
                "total_tokens": 20,
                "cost": 0,
            },
        }
        return TransportResponse(200, canonical_json(response))


class AdvisorySidecarTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.box_run = self.root / "box"
        with patch(
            "constraintbox.boxrun.ExternalEnginePacketBroker",
            FakePassingBroker,
        ), patch(
            "constraintbox.boxrun.validate_pass_receipt",
            return_value=(),
        ):
            result, code = run_first_box(REQUEST.read_bytes(), self.box_run)
        self.assertEqual(code, 0)
        self.assertEqual(result["disposition"], READY_FOR_PROPOSAL)
        external_validator = patch(
            "constraintbox.advisory_run.validate_pass_receipt",
            return_value=(),
        )
        external_validator.start()
        self.addCleanup(external_validator.stop)

    def test_valid_accepted_sidecar_is_separate_and_self_verifiable(self) -> None:
        source_before = {
            path.name: path.read_bytes()
            for path in self.box_run.iterdir()
        }
        sidecar = self.root / "accepted-sidecar"
        transport = AdaptiveTransport()

        receipt, code = run_advisory_sidecar(
            self.box_run,
            "nvidia",
            sidecar,
            environ={"NVIDIA_API_KEY": "offline-secret"},
            transport=transport,
        )

        self.assertEqual(code, 0)
        self.assertEqual(receipt["provider_state"], STATE_ACCEPTED)
        self.assertEqual(receipt["frozen_box_disposition"], READY_FOR_PROPOSAL)
        self.assertFalse(receipt["changes_box_decision"])
        self.assertFalse(receipt["decision_authority"])
        self.assertFalse(receipt["release_allowed"])
        self.assertFalse(receipt["promotion_allowed"])
        self.assertEqual(transport.calls, 1)
        self.assertEqual(
            set(path.name for path in sidecar.iterdir()),
            {
                "frozen_box_decision.json",
                "advisory_provider_receipt.json",
                "advisory_sidecar_receipt.json",
            },
        )
        source_after = {
            path.name: path.read_bytes()
            for path in self.box_run.iterdir()
        }
        self.assertEqual(source_after, source_before)

        persisted = parse_json_object(
            (sidecar / "advisory_sidecar_receipt.json").read_bytes()
        )
        digest_body = {
            key: value
            for key, value in persisted.items()
            if key not in {"receipt_sha256", "root_sha256"}
        }
        self.assertEqual(
            persisted["receipt_sha256"],
            sha256(canonical_json(digest_body)),
        )
        root_body = {
            "schema": SIDECAR_ROOT_SCHEMA,
            "receipt_sha256": persisted["receipt_sha256"],
            "artifacts": persisted["artifacts"],
        }
        self.assertEqual(
            persisted["root_sha256"],
            sha256(canonical_json(root_body)),
        )
        for name, digest in persisted["artifacts"].items():
            self.assertEqual(digest, sha256((sidecar / name).read_bytes()))

    def test_missing_credential_persists_parked_without_transport(self) -> None:
        sidecar = self.root / "parked-sidecar"

        def must_not_run(*args: object) -> TransportResponse:
            self.fail(f"transport ran without a credential: {args!r}")

        receipt, code = run_advisory_sidecar(
            self.box_run,
            "openrouter",
            sidecar,
            environ={},
            transport=must_not_run,
        )

        self.assertEqual(code, 4)
        self.assertEqual(receipt["provider_state"], STATE_PARKED)
        self.assertEqual(receipt["provider_reason_code"], "missing_credential")
        self.assertTrue(sidecar.is_dir())
        provider = parse_json_object(
            (sidecar / "advisory_provider_receipt.json").read_bytes()
        )
        self.assertFalse(provider["decision_authority"])
        self.assertFalse(provider["release_allowed"])
        self.assertFalse(provider["promotion_allowed"])

    def test_tampered_artifact_is_rejected_before_transport_or_sidecar(self) -> None:
        context_path = self.box_run / "compiled_user_context.txt"
        context_path.write_bytes(context_path.read_bytes() + b"\ntampered")
        sidecar = self.root / "must-not-exist"
        transport = AdaptiveTransport()

        with self.assertRaisesRegex(AdvisoryRunError, "digest mismatch"):
            run_advisory_sidecar(
                self.box_run,
                "nvidia",
                sidecar,
                environ={"NVIDIA_API_KEY": "offline-secret"},
                transport=transport,
            )

        self.assertEqual(transport.calls, 0)
        self.assertFalse(sidecar.exists())

    def test_tampered_receipt_is_rejected_before_transport_or_sidecar(self) -> None:
        receipt_path = self.box_run / "box_receipt.json"
        receipt = parse_json_object(receipt_path.read_bytes())
        receipt["release_allowed"] = True
        receipt_path.write_bytes(canonical_json(receipt) + b"\n")
        sidecar = self.root / "must-not-exist"
        transport = AdaptiveTransport()

        with self.assertRaisesRegex(AdvisoryRunError, "release must remain false"):
            run_advisory_sidecar(
                self.box_run,
                "nvidia",
                sidecar,
                environ={"NVIDIA_API_KEY": "offline-secret"},
                transport=transport,
            )

        self.assertEqual(transport.calls, 0)
        self.assertFalse(sidecar.exists())

    def test_coherently_rehashed_forgery_fails_current_policy_recheck(self) -> None:
        receipt_path = self.box_run / "box_receipt.json"
        receipt = parse_json_object(receipt_path.read_bytes())
        assessment = dict(receipt["request_assessment"])
        assessment["reason"] = "forged_controller_reason"
        explanation = deterministic_explanation(assessment).to_dict()
        output_contract = tuple(receipt["user_context"]["output_contract"])
        brief = build_audit_brief(
            assessment,
            output_contract=output_contract,
        )
        replacements = {
            "request_assessment.json": assessment,
            "deterministic_explanation.json": explanation,
            "external_audit_brief.json": brief,
        }
        for name, value in replacements.items():
            raw = canonical_json(value) + b"\n"
            (self.box_run / name).write_bytes(raw)
            receipt["artifacts"][name] = sha256(raw)
        receipt["request_assessment"] = assessment
        receipt["deterministic_explanation"] = explanation
        receipt["external_audit_brief"] = brief
        receipt_path.write_bytes(canonical_json(receipt) + b"\n")
        sidecar = self.root / "forged-sidecar"
        transport = AdaptiveTransport()

        with self.assertRaisesRegex(
            AdvisoryRunError,
            "current controller policy",
        ):
            run_advisory_sidecar(
                self.box_run,
                "nvidia",
                sidecar,
                environ={"NVIDIA_API_KEY": "offline-secret"},
                transport=transport,
            )

        self.assertEqual(transport.calls, 0)
        self.assertFalse(sidecar.exists())

    def test_symlink_artifact_and_symlink_root_are_rejected(self) -> None:
        original = self.box_run / "compiled_user_context.txt"
        moved = self.root / "context-copy.txt"
        moved.write_bytes(original.read_bytes())
        original.unlink()
        original.symlink_to(moved)
        artifact_sidecar = self.root / "artifact-sidecar"
        transport = AdaptiveTransport()

        with self.assertRaisesRegex(AdvisoryRunError, "non-symlink"):
            run_advisory_sidecar(
                self.box_run,
                "nvidia",
                artifact_sidecar,
                environ={"NVIDIA_API_KEY": "offline-secret"},
                transport=transport,
            )
        self.assertEqual(transport.calls, 0)
        self.assertFalse(artifact_sidecar.exists())

        box_link = self.root / "box-link"
        box_link.symlink_to(self.box_run, target_is_directory=True)
        with self.assertRaisesRegex(AdvisoryRunError, "root must not be a symlink"):
            run_advisory_sidecar(
                box_link,
                "nvidia",
                self.root / "root-sidecar",
                environ={"NVIDIA_API_KEY": "offline-secret"},
                transport=transport,
            )
        self.assertEqual(transport.calls, 0)

    def test_sidecar_overlap_is_rejected_before_transport(self) -> None:
        sidecar = self.box_run / "advice"
        transport = AdaptiveTransport()

        with self.assertRaisesRegex(AdvisoryRunError, "outside the box run"):
            run_advisory_sidecar(
                self.box_run,
                "nvidia",
                sidecar,
                environ={"NVIDIA_API_KEY": "offline-secret"},
                transport=transport,
            )

        self.assertEqual(transport.calls, 0)
        self.assertFalse(sidecar.exists())

    def test_provider_rejection_is_persisted_without_authority(self) -> None:
        box_receipt = parse_json_object(
            (self.box_run / "box_receipt.json").read_bytes()
        )
        sidecar = self.root / "rejected-sidecar"
        transport = AdaptiveTransport(forbidden_authority=True)

        receipt, code = run_advisory_sidecar(
            self.box_run,
            "nvidia",
            sidecar,
            environ={"NVIDIA_API_KEY": "offline-secret"},
            transport=transport,
        )

        self.assertEqual(code, 1)
        self.assertEqual(receipt["provider_state"], STATE_REJECTED)
        self.assertEqual(
            receipt["provider_reason_code"],
            "invalid_advisory_output",
        )
        self.assertEqual(
            receipt["frozen_box_disposition"],
            box_receipt["disposition"],
        )
        self.assertEqual(receipt["frozen_box_reason"], box_receipt["reason"])
        self.assertFalse(receipt["changes_box_decision"])
        self.assertFalse(receipt["decision_authority"])
        provider = parse_json_object(
            (sidecar / "advisory_provider_receipt.json").read_bytes()
        )
        self.assertIsNone(provider["advice"])
        self.assertFalse(provider["decision_authority"])

    def test_output_contract_is_preserved_exactly_to_provider_and_receipts(
        self,
    ) -> None:
        box_receipt = parse_json_object(
            (self.box_run / "box_receipt.json").read_bytes()
        )
        expected = box_receipt["user_context"]["output_contract"]
        sidecar = self.root / "contract-sidecar"
        transport = AdaptiveTransport()

        receipt, code = run_advisory_sidecar(
            self.box_run,
            "openrouter",
            sidecar,
            environ={"OPENROUTER_API_KEY": "offline-secret"},
            transport=transport,
        )

        self.assertEqual(code, 0)
        self.assertEqual(receipt["output_contract"], expected)
        self.assertEqual(len(transport.briefs), 1)
        self.assertEqual(transport.briefs[0]["output_contract"], expected)
        frozen = parse_json_object(
            (sidecar / "frozen_box_decision.json").read_bytes()
        )
        self.assertEqual(frozen["output_contract"], expected)
        self.assertEqual(
            frozen["user_context"]["output_contract"],
            expected,
        )

    def test_replay_is_bound_to_identical_frozen_decision(self) -> None:
        first = self.root / "replay-one"
        second = self.root / "replay-two"
        first_transport = AdaptiveTransport()
        second_transport = AdaptiveTransport()

        first_receipt, first_code = run_advisory_sidecar(
            self.box_run,
            "nvidia",
            first,
            environ={"NVIDIA_API_KEY": "offline-secret"},
            transport=first_transport,
        )
        second_receipt, second_code = run_advisory_sidecar(
            self.box_run,
            "nvidia",
            second,
            environ={"NVIDIA_API_KEY": "offline-secret"},
            transport=second_transport,
        )

        self.assertEqual((first_code, second_code), (0, 0))
        self.assertEqual(
            (first / "frozen_box_decision.json").read_bytes(),
            (second / "frozen_box_decision.json").read_bytes(),
        )
        self.assertEqual(
            first_receipt["frozen_decision_sha256"],
            second_receipt["frozen_decision_sha256"],
        )
        self.assertEqual(
            first_receipt["box_receipt_sha256"],
            second_receipt["box_receipt_sha256"],
        )
        self.assertEqual(
            first_receipt["root_sha256"],
            second_receipt["root_sha256"],
        )
        for root in (first, second):
            provider = parse_json_object(
                (root / "advisory_provider_receipt.json").read_bytes()
            )
            self.assertEqual(
                provider["decision_sha256"],
                first_receipt["frozen_decision_sha256"],
            )

    def test_partial_write_failure_never_publishes_final_directory(self) -> None:
        sidecar = self.root / "atomic-sidecar"
        transport = AdaptiveTransport()
        real_write = advisory_run_module._write_exclusive_json

        def fail_second_write(
            root: Path,
            name: str,
            value: dict[str, object],
        ) -> bytes:
            if name == "advisory_provider_receipt.json":
                raise OSError("offline injected write failure")
            return real_write(root, name, value)

        with patch(
            "constraintbox.advisory_run._write_exclusive_json",
            side_effect=fail_second_write,
        ):
            with self.assertRaisesRegex(OSError, "injected write failure"):
                run_advisory_sidecar(
                    self.box_run,
                    "nvidia",
                    sidecar,
                    environ={"NVIDIA_API_KEY": "offline-secret"},
                    transport=transport,
                )

        self.assertEqual(transport.calls, 1)
        self.assertFalse(sidecar.exists())
        self.assertEqual(
            list(self.root.glob(f".{sidecar.name}.*.staging")),
            [],
        )

    def test_resealed_provider_authority_is_rejected_by_self_verifier(
        self,
    ) -> None:
        sidecar = self.root / "resealed-sidecar"
        transport = AdaptiveTransport()
        run_advisory_sidecar(
            self.box_run,
            "nvidia",
            sidecar,
            environ={"NVIDIA_API_KEY": "offline-secret"},
            transport=transport,
        )
        provider_path = sidecar / "advisory_provider_receipt.json"
        provider = parse_json_object(provider_path.read_bytes())
        provider["decision_authority"] = True
        provider_raw = canonical_json(provider) + b"\n"
        provider_path.write_bytes(provider_raw)

        receipt_path = sidecar / "advisory_sidecar_receipt.json"
        receipt = parse_json_object(receipt_path.read_bytes())
        receipt["artifacts"]["advisory_provider_receipt.json"] = sha256(
            provider_raw
        )
        digest_body = {
            key: value
            for key, value in receipt.items()
            if key not in {"receipt_sha256", "root_sha256"}
        }
        receipt["receipt_sha256"] = sha256(canonical_json(digest_body))
        receipt["root_sha256"] = sha256(
            canonical_json(
                {
                    "schema": SIDECAR_ROOT_SCHEMA,
                    "receipt_sha256": receipt["receipt_sha256"],
                    "artifacts": receipt["artifacts"],
                }
            )
        )
        receipt_path.write_bytes(canonical_json(receipt) + b"\n")

        with self.assertRaisesRegex(
            AdvisoryRunError,
            "provider authority field",
        ):
            advisory_run_module._verify_persisted_sidecar(sidecar)

    def test_registered_provider_model_is_controller_owned(self) -> None:
        sidecar = self.root / "provider-sidecar"
        transport = AdaptiveTransport()

        receipt, code = run_advisory_sidecar(
            self.box_run,
            "nvidia",
            sidecar,
            environ={"NVIDIA_API_KEY": "offline-secret"},
            transport=transport,
        )

        self.assertEqual(code, 0)
        provider = parse_json_object(
            (sidecar / "advisory_provider_receipt.json").read_bytes()
        )
        self.assertEqual(
            provider["requested_model"],
            PROVIDER_REGISTRY["nvidia"].model,
        )
        self.assertEqual(receipt["provider"], "nvidia")
        self.assertNotIn("endpoint", receipt)
        self.assertNotIn("model", receipt)


if __name__ == "__main__":
    unittest.main()
