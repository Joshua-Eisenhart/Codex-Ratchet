from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from constraintbox.intake import canonical_json
from constraintbox.ledger import GENESIS, HashChainLedger
from constraintbox.mini_levos import (
    CONTROLLER_METADATA_KEY,
    CONTROLLER_METADATA_SCHEMA,
    FlowNode,
    FlowPolicy,
    FlowTransition,
    HookKind,
    HookRegistration,
    HookResult,
    HookSignal,
    MiniLevError,
    MiniLevRuntime,
    handler_code_sha256,
    verify_flow_receipt,
)
from constraintbox.python_runtime import PythonRuntimeError


def retry_then_pass(context: dict[str, object]) -> HookResult:
    attempt = int(context.get("attempt", 0)) + 1
    signal = HookSignal.RETRY if attempt == 1 else HookSignal.PASS
    return HookResult(
        signal,
        {"attempt": attempt},
        {"attempt": attempt},
    )


def always_retry(_context: dict[str, object]) -> HookResult:
    return HookResult(HookSignal.RETRY, {"status": "retry"})


def pass_gate(_context: dict[str, object]) -> HookResult:
    return HookResult(HookSignal.PASS, {"status": "pass"})


def second_pass_gate(_context: dict[str, object]) -> HookResult:
    return HookResult(HookSignal.PASS, {"status": "second-pass"})


def replacement_pass_gate(_context: dict[str, object]) -> HookResult:
    return HookResult(HookSignal.PASS, {"status": "replacement"})


def authority_injection(_context: dict[str, object]) -> HookResult:
    return HookResult(
        HookSignal.PASS,
        {"candidate": {"provider": "model", "verdict": "PASS"}},
    )


def proposal_pass(_context: dict[str, object]) -> HookResult:
    return HookResult(HookSignal.PASS, {"proposal": "self-approved"})


def proposal_observed(_context: dict[str, object]) -> HookResult:
    return HookResult(HookSignal.OBSERVED, {"proposal": "observed"})


def exploding_gate(_context: dict[str, object]) -> HookResult:
    raise ValueError("deterministic hook failure")


def oversized_output(_context: dict[str, object]) -> HookResult:
    return HookResult(HookSignal.PASS, {"payload": "x" * 512})


def oversized_context_update(_context: dict[str, object]) -> HookResult:
    return HookResult(
        HookSignal.PASS,
        {"status": "update"},
        {"payload": "x" * 512},
    )


def controller_metadata_gate(context: dict[str, object]) -> HookResult:
    expected = {
        "schema": CONTROLLER_METADATA_SCHEMA,
        "run_id": context.get("expected_run_id"),
        "policy_sha256": context.get("expected_policy_sha256"),
        "node_id": "gate",
        "hook_id": "metadata-gate",
        "hook_kind": HookKind.GATE.value,
    }
    matched = context.get(CONTROLLER_METADATA_KEY) == expected
    return HookResult(
        HookSignal.PASS if matched else HookSignal.BLOCKED,
        {"controller_metadata_matched": matched},
    )


def overwrite_controller_metadata(_context: dict[str, object]) -> HookResult:
    return HookResult(
        HookSignal.PASS,
        {"status": "attempted-overwrite"},
        {CONTROLLER_METADATA_KEY: {"forged": True}},
    )


class MiniLevRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary_directory.name)

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def _registration(
        self,
        handler,
        *,
        hook_id: str = "gate",
        kind: HookKind = HookKind.GATE,
        allowed_signals: tuple[HookSignal, ...] = (
            HookSignal.PASS,
            HookSignal.RETRY,
            HookSignal.BLOCKED,
            HookSignal.PARKED,
        ),
        allowed_update_keys: tuple[str, ...] = (),
        max_output_bytes: int = 65_536,
    ) -> HookRegistration:
        source_path = Path(__file__).resolve()
        return HookRegistration(
            hook_id=hook_id,
            kind=kind,
            handler=handler,
            source_path=source_path,
            source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
            code_sha256=handler_code_sha256(handler),
            allowed_signals=allowed_signals,
            allowed_update_keys=allowed_update_keys,
            max_output_bytes=max_output_bytes,
        )

    def _single_node_policy(
        self,
        registration: HookRegistration,
        *,
        max_steps: int = 8,
        max_visits_per_node: int = 8,
        max_retries: int = 4,
        max_context_bytes: int = 8_192,
        max_event_bytes: int = 16_384,
        max_receipt_bytes: int = 262_144,
    ) -> FlowPolicy:
        terminal_for_signal = {
            HookSignal.OBSERVED: "ELIGIBLE",
            HookSignal.PASS: "RELEASED",
            HookSignal.RETRY: "gate",
            HookSignal.BLOCKED: "BLOCKED",
            HookSignal.PARKED: "PARKED",
        }
        transitions = tuple(
            FlowTransition(
                "gate",
                signal,
                terminal_for_signal[signal],
            )
            for signal in registration.allowed_signals
        ) + (FlowTransition("gate", HookSignal.HOLD, "HOLD"),)
        terminal_nodes = tuple(
            sorted(
                {
                    transition.to_node
                    for transition in transitions
                    if transition.to_node != "gate"
                }
            )
        )
        return FlowPolicy(
            flow_id="bounded-flow",
            entry_node="gate",
            nodes=(FlowNode("gate", registration.hook_id),),
            transitions=transitions,
            terminal_nodes=terminal_nodes,
            required_nodes=("gate",),
            max_steps=max_steps,
            max_visits_per_node=max_visits_per_node,
            max_retries=max_retries,
            max_context_bytes=max_context_bytes,
            max_event_bytes=max_event_bytes,
            max_receipt_bytes=max_receipt_bytes,
            claim_ceiling="bounded deterministic test flow only",
        )

    def _runtime(
        self,
        registration: HookRegistration,
        *,
        name: str,
        policy: FlowPolicy | None = None,
    ) -> MiniLevRuntime:
        return MiniLevRuntime(
            policy or self._single_node_policy(registration),
            (registration,),
            run_id=name,
            ledger_path=self.root / f"{name}.jsonl",
        )

    def _required_retry_runtime(self, *, name: str) -> MiniLevRuntime:
        required = self._registration(
            always_retry,
            hook_id="required-hook",
            allowed_signals=(HookSignal.RETRY,),
        )
        final = self._registration(
            pass_gate,
            hook_id="final-hook",
            allowed_signals=(HookSignal.PASS,),
        )
        policy = FlowPolicy(
            flow_id="required-retry-flow",
            entry_node="required",
            nodes=(
                FlowNode("required", required.hook_id),
                FlowNode("final", final.hook_id),
            ),
            transitions=(
                FlowTransition("required", HookSignal.RETRY, "final"),
                FlowTransition("required", HookSignal.HOLD, "HOLD"),
                FlowTransition("final", HookSignal.PASS, "RELEASED"),
                FlowTransition("final", HookSignal.HOLD, "HOLD"),
            ),
            terminal_nodes=("HOLD", "RELEASED"),
            required_nodes=("required", "final"),
            max_steps=2,
            max_visits_per_node=1,
            max_retries=1,
            max_context_bytes=1_024,
            max_event_bytes=16_384,
            max_receipt_bytes=262_144,
            claim_ceiling="required gate PASS test only",
        )
        return MiniLevRuntime(
            policy,
            (required, final),
            run_id=name,
            ledger_path=self.root / f"{name}.jsonl",
        )

    def _two_gate_runtime(self, *, name: str) -> MiniLevRuntime:
        first = self._registration(
            pass_gate,
            hook_id="first-hook",
            allowed_signals=(HookSignal.PASS,),
        )
        second = self._registration(
            second_pass_gate,
            hook_id="second-hook",
            allowed_signals=(HookSignal.PASS,),
        )
        policy = FlowPolicy(
            flow_id="two-gate-flow",
            entry_node="first",
            nodes=(
                FlowNode("first", first.hook_id),
                FlowNode("second", second.hook_id),
            ),
            transitions=(
                FlowTransition("first", HookSignal.PASS, "second"),
                FlowTransition("first", HookSignal.HOLD, "HOLD"),
                FlowTransition("second", HookSignal.PASS, "RELEASED"),
                FlowTransition("second", HookSignal.HOLD, "HOLD"),
            ),
            terminal_nodes=("HOLD", "RELEASED"),
            required_nodes=("first", "second"),
            max_steps=2,
            max_visits_per_node=1,
            max_retries=0,
            max_context_bytes=1_024,
            max_event_bytes=16_384,
            max_receipt_bytes=262_144,
            claim_ceiling="two-gate entry test only",
        )
        return MiniLevRuntime(
            policy,
            (first, second),
            run_id=name,
            ledger_path=self.root / f"{name}.jsonl",
        )

    @staticmethod
    def _records(receipt: dict[str, object]) -> list[dict[str, object]]:
        ledger_path = Path(receipt["ledger"]["path"])
        return [
            json.loads(raw)["record"]
            for raw in ledger_path.read_text(encoding="utf-8").splitlines()
        ]

    @staticmethod
    def _recompute_receipt_digest(receipt: dict[str, object]) -> None:
        digest_body = dict(receipt)
        digest_body.pop("receipt_sha256", None)
        receipt["receipt_sha256"] = hashlib.sha256(
            canonical_json(digest_body)
        ).hexdigest()

    def _rewrite_valid_ledger(
        self,
        receipt: dict[str, object],
        records: list[dict[str, object]],
    ) -> None:
        previous_sha256 = GENESIS
        event_hashes: list[str] = []
        rows: list[dict[str, object]] = []
        for record in records:
            body = {
                "previous_sha256": previous_sha256,
                "record": record,
            }
            line_sha256 = hashlib.sha256(canonical_json(body)).hexdigest()
            rows.append({**body, "line_sha256": line_sha256})
            event_hashes.append(line_sha256)
            previous_sha256 = line_sha256

        ledger_path = Path(receipt["ledger"]["path"])
        head_path = Path(receipt["ledger"]["head_path"])
        ledger_path.write_text(
            "".join(
                canonical_json(row).decode("utf-8") + "\n" for row in rows
            ),
            encoding="utf-8",
        )
        head_path.write_text(previous_sha256 + "\n", encoding="ascii")
        receipt["steps"] = len(rows)
        receipt["event_hashes"] = event_hashes
        receipt["ledger"]["retained_head_sha256"] = previous_sha256
        receipt["ledger"]["verification"] = f"{len(rows)} record(s)"
        self._recompute_receipt_digest(receipt)

    def _rebind_forged_policy_and_ledger(
        self,
        receipt: dict[str, object],
        records: list[dict[str, object]],
    ) -> str:
        policy_sha256 = hashlib.sha256(
            canonical_json(receipt["policy"])
        ).hexdigest()
        receipt["policy_sha256"] = policy_sha256
        for record in records:
            record["policy_sha256"] = policy_sha256
        self._rewrite_valid_ledger(receipt, records)
        return policy_sha256

    def test_golden_bounded_retry_releases_on_second_attempt(self) -> None:
        registration = self._registration(
            retry_then_pass,
            allowed_update_keys=("attempt",),
        )
        runtime = self._runtime(registration, name="golden-retry")

        receipt = runtime.run({"seed": "fixed"})
        records = self._records(receipt)
        semantic_golden = {
            "terminal": receipt["terminal"],
            "steps": receipt["steps"],
            "retries": receipt["retries"],
            "visits": receipt["visits"],
            "final_context": receipt["final_context"],
            "promotion_allowed": receipt["promotion_allowed"],
            "events": [
                {
                    "sequence": record["sequence"],
                    "node_id": record["node_id"],
                    "visit": record["visit"],
                    "typed_signal": record["typed_signal"],
                    "controller_selected_next": record[
                        "controller_selected_next"
                    ],
                    "controller_reason": record["controller_reason"],
                }
                for record in records
            ],
        }
        self.assertEqual(
            semantic_golden,
            {
                "terminal": "RELEASED",
                "steps": 2,
                "retries": 1,
                "visits": {"gate": 2},
                "final_context": {"attempt": 2, "seed": "fixed"},
                "promotion_allowed": False,
                "events": [
                    {
                        "sequence": 1,
                        "node_id": "gate",
                        "visit": 1,
                        "typed_signal": "RETRY",
                        "controller_selected_next": "gate",
                        "controller_reason": None,
                    },
                    {
                        "sequence": 2,
                        "node_id": "gate",
                        "visit": 2,
                        "typed_signal": "PASS",
                        "controller_selected_next": "RELEASED",
                        "controller_reason": None,
                    },
                ],
            },
        )
        hook_material = receipt["policy"]["hooks"][0]
        self.assertEqual(hook_material["source_sha256"], registration.source_sha256)
        self.assertEqual(hook_material["code_sha256"], registration.code_sha256)
        self.assertEqual(
            receipt["policy_sha256"],
            hashlib.sha256(canonical_json(receipt["policy"])).hexdigest(),
        )
        receipt_body = dict(receipt)
        receipt_digest = receipt_body.pop("receipt_sha256")
        self.assertEqual(
            receipt_digest,
            hashlib.sha256(canonical_json(receipt_body)).hexdigest(),
        )

    def test_receipt_and_retained_ledger_verify(self) -> None:
        registration = self._registration(
            retry_then_pass,
            allowed_update_keys=("attempt",),
        )
        runtime = self._runtime(registration, name="verified-retry")
        receipt = runtime.run({})

        self.assertEqual(
            runtime.retained_head_sha256,
            receipt["ledger"]["retained_head_sha256"],
        )
        self.assertEqual(runtime.receipt_sha256, receipt["receipt_sha256"])
        self.assertEqual(
            verify_flow_receipt(
                receipt,
                expected_run_id=runtime.run_id,
                expected_policy_sha256=runtime.policy_sha256,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=runtime.retained_head_sha256,
                expected_receipt_sha256=runtime.receipt_sha256,
            ),
            (True, "flow receipt and semantic ledger match"),
        )
        ledger = HashChainLedger(
            Path(receipt["ledger"]["path"]),
            Path(receipt["ledger"]["head_path"]),
        )
        self.assertEqual(ledger.verify(), (True, "2 record(s)"))
        self.assertEqual(
            receipt["ledger"]["retained_head_sha256"],
            receipt["event_hashes"][-1],
        )

    def test_handler_receives_unpersisted_controller_metadata(self) -> None:
        registration = self._registration(
            controller_metadata_gate,
            hook_id="metadata-gate",
            allowed_signals=(HookSignal.PASS, HookSignal.BLOCKED),
        )
        runtime = self._runtime(registration, name="controller-metadata")
        initial_context = {
            "expected_run_id": runtime.run_id,
            "expected_policy_sha256": runtime.policy_sha256,
        }

        receipt = runtime.run(initial_context)

        self.assertEqual(receipt["terminal"], "RELEASED")
        self.assertEqual(receipt["initial_context"], initial_context)
        self.assertEqual(receipt["final_context"], initial_context)
        self.assertNotIn(CONTROLLER_METADATA_KEY, receipt["initial_context"])
        self.assertNotIn(CONTROLLER_METADATA_KEY, receipt["final_context"])
        event = self._records(receipt)[0]
        self.assertEqual(
            event["hook_observation"],
            {"controller_metadata_matched": True},
        )
        self.assertEqual(
            event["input_sha256"],
            hashlib.sha256(canonical_json(initial_context)).hexdigest(),
        )
        self.assertNotIn(
            CONTROLLER_METADATA_KEY,
            event["applied_context_updates"],
        )

    def test_initial_context_cannot_supply_controller_metadata(self) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        runtime = self._runtime(registration, name="reserved-controller-context")

        with self.assertRaisesRegex(
            MiniLevError,
            "initial context contains reserved controller metadata",
        ):
            runtime.run(
                {
                    CONTROLLER_METADATA_KEY: {
                        "run_id": "caller-selected",
                    }
                }
            )
        self.assertFalse(runtime.ledger_path.exists())

    def test_offline_verifier_rejects_persisted_controller_metadata(
        self,
    ) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        runtime = self._runtime(
            registration,
            name="persisted-controller-metadata",
        )
        forged = copy.deepcopy(runtime.run({}))
        records = self._records(forged)
        forged_context = {
            CONTROLLER_METADATA_KEY: {
                "schema": CONTROLLER_METADATA_SCHEMA,
                "run_id": runtime.run_id,
                "policy_sha256": runtime.policy_sha256,
                "node_id": "gate",
                "hook_id": "gate",
                "hook_kind": HookKind.GATE.value,
            }
        }
        forged_context_sha256 = hashlib.sha256(
            canonical_json(forged_context)
        ).hexdigest()
        forged["initial_context"] = forged_context
        forged["initial_context_sha256"] = forged_context_sha256
        forged["final_context"] = forged_context
        forged["final_context_sha256"] = forged_context_sha256
        records[0]["input_sha256"] = forged_context_sha256
        records[0]["context_sha256"] = forged_context_sha256
        self._rewrite_valid_ledger(forged, records)

        valid, reason = verify_flow_receipt(
            forged,
            expected_run_id=runtime.run_id,
            expected_policy_sha256=runtime.policy_sha256,
            expected_ledger_path=runtime.ledger_path,
            expected_retained_head_sha256=forged["ledger"][
                "retained_head_sha256"
            ],
            expected_receipt_sha256=forged["receipt_sha256"],
        )
        self.assertFalse(valid)
        self.assertEqual(
            reason,
            "initial context contains reserved controller metadata",
        )

    def test_hook_cannot_register_or_write_controller_metadata(self) -> None:
        forbidden_registration = self._registration(
            overwrite_controller_metadata,
            allowed_signals=(HookSignal.PASS,),
            allowed_update_keys=(CONTROLLER_METADATA_KEY,),
        )
        with self.assertRaisesRegex(
            MiniLevError,
            "hook allowed_update_keys are invalid",
        ):
            self._runtime(
                forbidden_registration,
                name="registered-controller-overwrite",
            )

        registration = self._registration(
            overwrite_controller_metadata,
            allowed_signals=(HookSignal.PASS,),
        )
        receipt = self._runtime(
            registration,
            name="runtime-controller-overwrite",
        ).run({})
        self.assertEqual(receipt["terminal"], "HOLD")
        self.assertNotIn(CONTROLLER_METADATA_KEY, receipt["final_context"])
        self.assertEqual(
            self._records(receipt)[0]["controller_reason"],
            "hook_attempted_controller_authority",
        )

    def test_authority_field_injection_is_held(self) -> None:
        registration = self._registration(authority_injection)
        receipt = self._runtime(
            registration,
            name="authority-injection",
        ).run({"safe": True})

        self.assertEqual(receipt["terminal"], "HOLD")
        self.assertEqual(receipt["final_context"], {"safe": True})
        self.assertEqual(
            self._records(receipt)[-1]["controller_reason"],
            "hook_attempted_controller_authority",
        )

    def test_proposal_cannot_register_or_emit_pass(self) -> None:
        forbidden_registration = self._registration(
            proposal_pass,
            kind=HookKind.PROPOSAL,
            allowed_signals=(HookSignal.PASS,),
        )
        with self.assertRaisesRegex(
            MiniLevError,
            "proposal cannot emit one of its signals",
        ):
            self._runtime(
                forbidden_registration,
                name="proposal-pass-registration",
            )

        runtime_registration = self._registration(
            proposal_pass,
            kind=HookKind.PROPOSAL,
            allowed_signals=(HookSignal.OBSERVED,),
        )
        runtime_policy = FlowPolicy(
            flow_id="proposal-runtime-flow",
            entry_node="gate",
            nodes=(FlowNode("gate", runtime_registration.hook_id),),
            transitions=(
                FlowTransition("gate", HookSignal.OBSERVED, "PARKED"),
                FlowTransition("gate", HookSignal.HOLD, "HOLD"),
            ),
            terminal_nodes=("HOLD", "PARKED"),
            required_nodes=("gate",),
            max_steps=1,
            max_visits_per_node=1,
            max_retries=0,
            max_context_bytes=1_024,
            max_event_bytes=16_384,
            max_receipt_bytes=262_144,
            claim_ceiling="proposal signal authorization test only",
        )
        receipt = self._runtime(
            runtime_registration,
            name="proposal-pass-runtime",
            policy=runtime_policy,
        ).run({})
        self.assertEqual(receipt["terminal"], "HOLD")
        self.assertEqual(
            self._records(receipt)[-1]["controller_reason"],
            "hook_signal_not_authorized",
        )

    def test_proposal_observed_cannot_reach_a_positive_terminal(self) -> None:
        registration = self._registration(
            proposal_observed,
            kind=HookKind.PROPOSAL,
            allowed_signals=(HookSignal.OBSERVED,),
        )
        policy = FlowPolicy(
            flow_id="proposal-positive-flow",
            entry_node="proposal",
            nodes=(FlowNode("proposal", registration.hook_id),),
            transitions=(
                FlowTransition("proposal", HookSignal.OBSERVED, "ELIGIBLE"),
                FlowTransition("proposal", HookSignal.HOLD, "HOLD"),
            ),
            terminal_nodes=("ELIGIBLE", "HOLD"),
            required_nodes=("proposal",),
            max_steps=1,
            max_visits_per_node=1,
            max_retries=0,
            max_context_bytes=1_024,
            max_event_bytes=16_384,
            max_receipt_bytes=262_144,
            claim_ceiling="positive terminal authority test only",
        )

        with self.assertRaisesRegex(
            MiniLevError,
            "positive terminals are reachable only from a gate PASS",
        ):
            MiniLevRuntime(
                policy,
                (registration,),
                run_id="proposal-positive",
                ledger_path=self.root / "proposal-positive.jsonl",
            )

    def test_mutable_allowed_update_keys_are_rejected(self) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        mutable_registration = replace(
            registration,
            allowed_update_keys=["attempt"],
        )

        with self.assertRaisesRegex(
            MiniLevError,
            "hook allowed_update_keys are invalid",
        ):
            self._runtime(
                mutable_registration,
                name="mutable-update-keys",
            )

    def test_hook_exception_is_held(self) -> None:
        registration = self._registration(
            exploding_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        receipt = self._runtime(registration, name="hook-exception").run(
            {"unchanged": True}
        )

        self.assertEqual(receipt["terminal"], "HOLD")
        self.assertEqual(receipt["final_context"], {"unchanged": True})
        self.assertEqual(
            self._records(receipt)[-1]["controller_reason"],
            "hook_execution_error",
        )

    def test_retry_budget_exhaustion_is_held(self) -> None:
        registration = self._registration(always_retry)
        policy = self._single_node_policy(
            registration,
            max_steps=5,
            max_visits_per_node=5,
            max_retries=1,
        )
        receipt = self._runtime(
            registration,
            name="retry-budget",
            policy=policy,
        ).run({})

        self.assertEqual(receipt["terminal"], "HOLD")
        self.assertEqual(receipt["steps"], 2)
        self.assertEqual(receipt["retries"], 1)
        self.assertEqual(
            self._records(receipt)[-1]["controller_reason"],
            "retry_budget_exhausted",
        )

    def test_step_budget_exhaustion_is_held(self) -> None:
        registration = self._registration(always_retry)
        policy = self._single_node_policy(
            registration,
            max_steps=1,
            max_visits_per_node=5,
            max_retries=5,
        )
        receipt = self._runtime(
            registration,
            name="step-budget",
            policy=policy,
        ).run({})

        self.assertEqual(receipt["terminal"], "HOLD")
        self.assertEqual(receipt["steps"], 1)
        self.assertEqual(receipt["retries"], 0)
        self.assertEqual(
            self._records(receipt)[-1]["controller_reason"],
            "step_budget_exhausted",
        )

    def test_visit_budget_exhaustion_is_held(self) -> None:
        registration = self._registration(always_retry)
        policy = self._single_node_policy(
            registration,
            max_steps=5,
            max_visits_per_node=1,
            max_retries=5,
        )
        receipt = self._runtime(
            registration,
            name="visit-budget",
            policy=policy,
        ).run({})

        self.assertEqual(receipt["terminal"], "HOLD")
        self.assertEqual(receipt["steps"], 2)
        self.assertEqual(receipt["visits"], {"gate": 2})
        self.assertEqual(
            self._records(receipt)[-1]["controller_reason"],
            "node_visit_budget_exhausted",
        )

    def test_initial_context_bound_is_enforced_before_execution(self) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        policy = self._single_node_policy(
            registration,
            max_context_bytes=16,
        )
        runtime = self._runtime(
            registration,
            name="initial-context-bound",
            policy=policy,
        )

        with self.assertRaisesRegex(
            MiniLevError,
            "initial context exceeds the controller bound",
        ):
            runtime.run({"payload": "x" * 64})
        self.assertFalse(runtime.ledger_path.exists())

    def test_hook_output_bound_is_held(self) -> None:
        registration = self._registration(
            oversized_output,
            allowed_signals=(HookSignal.PASS,),
            max_output_bytes=128,
        )
        receipt = self._runtime(
            registration,
            name="output-bound",
        ).run({})

        self.assertEqual(receipt["terminal"], "HOLD")
        self.assertEqual(
            self._records(receipt)[-1]["controller_reason"],
            "hook_output_exceeds_bound",
        )

    def test_context_update_bound_is_held_without_applying_update(self) -> None:
        registration = self._registration(
            oversized_context_update,
            allowed_signals=(HookSignal.PASS,),
            allowed_update_keys=("payload",),
        )
        policy = self._single_node_policy(
            registration,
            max_context_bytes=32,
        )
        receipt = self._runtime(
            registration,
            name="context-update-bound",
            policy=policy,
        ).run({})

        self.assertEqual(receipt["terminal"], "HOLD")
        self.assertEqual(receipt["final_context"], {})
        self.assertEqual(
            self._records(receipt)[-1]["controller_reason"],
            "context_exceeds_bound",
        )

    def test_hook_source_substitution_is_rejected(self) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        substituted_source = self.root / "substituted_hook.py"
        substituted_source.write_text(
            "def pass_gate(context):\n    return context\n",
            encoding="utf-8",
        )
        substituted_registration = replace(
            registration,
            source_path=substituted_source,
            source_sha256=hashlib.sha256(
                substituted_source.read_bytes()
            ).hexdigest(),
        )

        with self.assertRaisesRegex(MiniLevError, "hook source path drift"):
            self._runtime(
                substituted_registration,
                name="source-substitution",
            )

    def test_hook_live_binding_substitution_is_held(self) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        runtime = self._runtime(
            registration,
            name="binding-substitution",
        )
        module = sys.modules[pass_gate.__module__]

        with mock.patch.object(
            module,
            pass_gate.__name__,
            replacement_pass_gate,
        ):
            receipt = runtime.run({})

        self.assertEqual(receipt["terminal"], "HOLD")
        self.assertEqual(
            self._records(receipt)[-1]["controller_reason"],
            "runtime_or_hook_identity_changed",
        )

    def test_non_retry_cycle_is_rejected(self) -> None:
        first = self._registration(
            pass_gate,
            hook_id="first-hook",
            allowed_signals=(HookSignal.PASS,),
        )
        second = self._registration(
            second_pass_gate,
            hook_id="second-hook",
            allowed_signals=(HookSignal.PASS,),
        )
        policy = FlowPolicy(
            flow_id="cycle-flow",
            entry_node="first",
            nodes=(
                FlowNode("first", first.hook_id),
                FlowNode("second", second.hook_id),
            ),
            transitions=(
                FlowTransition("first", HookSignal.PASS, "second"),
                FlowTransition("first", HookSignal.HOLD, "HOLD"),
                FlowTransition("second", HookSignal.PASS, "first"),
                FlowTransition("second", HookSignal.HOLD, "HOLD"),
            ),
            terminal_nodes=("HOLD",),
            required_nodes=("first", "second"),
            max_steps=4,
            max_visits_per_node=2,
            max_retries=0,
            max_context_bytes=1_024,
            max_event_bytes=4_096,
            max_receipt_bytes=65_536,
            claim_ceiling="cycle rejection test only",
        )

        with self.assertRaisesRegex(
            MiniLevError,
            "non-retry flow edges must form a DAG",
        ):
            MiniLevRuntime(
                policy,
                (first, second),
                run_id="cycle-rejection",
                ledger_path=self.root / "cycle.jsonl",
            )

    def test_incomplete_transition_map_is_rejected(self) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        policy = FlowPolicy(
            flow_id="incomplete-flow",
            entry_node="gate",
            nodes=(FlowNode("gate", registration.hook_id),),
            transitions=(
                FlowTransition("gate", HookSignal.PASS, "RELEASED"),
            ),
            terminal_nodes=("RELEASED",),
            required_nodes=("gate",),
            max_steps=1,
            max_visits_per_node=1,
            max_retries=0,
            max_context_bytes=1_024,
            max_event_bytes=4_096,
            max_receipt_bytes=65_536,
            claim_ceiling="transition completeness test only",
        )

        with self.assertRaisesRegex(
            MiniLevError,
            "lacks an exhaustive transition map",
        ):
            MiniLevRuntime(
                policy,
                (registration,),
                run_id="incomplete-transitions",
                ledger_path=self.root / "incomplete.jsonl",
            )

    def test_positive_terminal_is_refused_when_required_node_was_skipped(
        self,
    ) -> None:
        first = self._registration(
            pass_gate,
            hook_id="first-hook",
            allowed_signals=(HookSignal.PASS, HookSignal.RETRY),
        )
        required = self._registration(
            second_pass_gate,
            hook_id="required-hook",
            allowed_signals=(HookSignal.PASS,),
        )
        policy = FlowPolicy(
            flow_id="required-node-flow",
            entry_node="first",
            nodes=(
                FlowNode("first", first.hook_id),
                FlowNode("required", required.hook_id),
            ),
            transitions=(
                FlowTransition("first", HookSignal.PASS, "RELEASED"),
                FlowTransition("first", HookSignal.RETRY, "required"),
                FlowTransition("first", HookSignal.HOLD, "HOLD"),
                FlowTransition("required", HookSignal.PASS, "RELEASED"),
                FlowTransition("required", HookSignal.HOLD, "HOLD"),
            ),
            terminal_nodes=("HOLD", "RELEASED"),
            required_nodes=("first", "required"),
            max_steps=2,
            max_visits_per_node=1,
            max_retries=1,
            max_context_bytes=1_024,
            max_event_bytes=16_384,
            max_receipt_bytes=262_144,
            claim_ceiling="required-node execution test only",
        )
        runtime = MiniLevRuntime(
            policy,
            (first, required),
            run_id="required-node-skip",
            ledger_path=self.root / "required-node-skip.jsonl",
        )

        receipt = runtime.run({})

        self.assertEqual(receipt["terminal"], "HOLD")
        self.assertEqual(receipt["visits"], {"first": 1, "required": 0})
        self.assertEqual(
            self._records(receipt)[-1]["controller_reason"],
            "required_nodes_not_executed",
        )
        self.assertEqual(
            verify_flow_receipt(
                receipt,
                expected_run_id=runtime.run_id,
                expected_policy_sha256=runtime.policy_sha256,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=runtime.retained_head_sha256,
                expected_receipt_sha256=runtime.receipt_sha256,
            ),
            (True, "flow receipt and semantic ledger match"),
        )

    def test_required_gate_retry_does_not_discharge_required_node(self) -> None:
        runtime = self._required_retry_runtime(name="required-gate-retry")

        receipt = runtime.run({})

        self.assertEqual(receipt["terminal"], "HOLD")
        self.assertEqual(receipt["retries"], 1)
        self.assertEqual(receipt["visits"], {"final": 1, "required": 1})
        self.assertNotIn("required", receipt["completed_nodes"])
        self.assertEqual(
            self._records(receipt)[-1]["controller_reason"],
            "required_nodes_not_executed",
        )
        self.assertEqual(
            verify_flow_receipt(
                receipt,
                expected_run_id=runtime.run_id,
                expected_policy_sha256=runtime.policy_sha256,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=runtime.retained_head_sha256,
                expected_receipt_sha256=runtime.receipt_sha256,
            ),
            (True, "flow receipt and semantic ledger match"),
        )

    def test_rechained_first_event_must_still_be_policy_entry_node(self) -> None:
        runtime = self._two_gate_runtime(name="wrong-entry-node")
        receipt = runtime.run({})
        records = self._records(receipt)
        records[0]["node_id"] = "second"
        self._rewrite_valid_ledger(receipt, records)

        self.assertEqual(
            HashChainLedger(runtime.ledger_path).verify(),
            (True, "2 record(s)"),
        )
        self.assertEqual(
            verify_flow_receipt(
                receipt,
                expected_run_id=runtime.run_id,
                expected_policy_sha256=runtime.policy_sha256,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=receipt["ledger"][
                    "retained_head_sha256"
                ],
                expected_receipt_sha256=receipt["receipt_sha256"],
            ),
            (False, "event stream did not start at the entry node"),
        )

    def test_receipt_rejects_wrong_run_and_policy_bindings(self) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        runtime = self._runtime(registration, name="receipt-bindings")
        receipt = runtime.run({})

        self.assertEqual(
            verify_flow_receipt(
                receipt,
                expected_run_id="other-run",
                expected_policy_sha256=runtime.policy_sha256,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=runtime.retained_head_sha256,
                expected_receipt_sha256=runtime.receipt_sha256,
            ),
            (False, "run binding mismatch"),
        )
        self.assertEqual(
            verify_flow_receipt(
                receipt,
                expected_run_id=runtime.run_id,
                expected_policy_sha256="0" * 64,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=runtime.retained_head_sha256,
                expected_receipt_sha256=runtime.receipt_sha256,
            ),
            (False, "policy binding mismatch"),
        )

    def test_policy_material_tamper_with_fresh_receipt_digest_is_rejected(
        self,
    ) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        runtime = self._runtime(registration, name="policy-material-tamper")
        receipt = runtime.run({})
        tampered = copy.deepcopy(receipt)
        tampered["policy"]["claim_ceiling"] = "forged policy material"
        self._recompute_receipt_digest(tampered)

        self.assertEqual(
            verify_flow_receipt(
                tampered,
                expected_run_id=runtime.run_id,
                expected_policy_sha256=runtime.policy_sha256,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=runtime.retained_head_sha256,
                expected_receipt_sha256=tampered["receipt_sha256"],
            ),
            (False, "policy material digest mismatch"),
        )

    def test_recomputed_receipt_is_rejected_by_original_receipt_root(self) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        runtime = self._runtime(registration, name="receipt-root-tamper")
        receipt = runtime.run({})
        tampered = copy.deepcopy(receipt)
        tampered["claim_ceiling"] = "forged broader claim"
        self._recompute_receipt_digest(tampered)

        self.assertEqual(
            verify_flow_receipt(
                tampered,
                expected_run_id=runtime.run_id,
                expected_policy_sha256=runtime.policy_sha256,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=runtime.retained_head_sha256,
                expected_receipt_sha256=runtime.receipt_sha256,
            ),
            (False, "receipt root binding mismatch"),
        )

    def test_offline_verifier_rejects_forged_proposal_positive_terminal(
        self,
    ) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        runtime = self._runtime(registration, name="forged-proposal-positive")
        original = runtime.run({})
        forged = copy.deepcopy(original)
        records = self._records(original)

        hook = forged["policy"]["hooks"][0]
        hook["kind"] = HookKind.PROPOSAL.value
        hook["allowed_signals"] = [HookSignal.OBSERVED.value]
        forged["policy"]["transitions"] = [
            {
                "from_node": "gate",
                "signal": HookSignal.OBSERVED.value,
                "to_node": "ELIGIBLE",
            },
            {
                "from_node": "gate",
                "signal": HookSignal.HOLD.value,
                "to_node": "HOLD",
            },
        ]
        forged["policy"]["terminal_nodes"] = ["ELIGIBLE", "HOLD"]
        forged["terminal"] = "ELIGIBLE"

        event = records[0]
        event["node_kind"] = HookKind.PROPOSAL.value
        event["hook_reported_signal"] = HookSignal.OBSERVED.value
        event["controller_accepted_signal"] = HookSignal.OBSERVED.value
        event["typed_signal"] = HookSignal.OBSERVED.value
        event["controller_selected_next"] = "ELIGIBLE"
        event["controller_output"]["signal"] = HookSignal.OBSERVED.value
        event["output_sha256"] = hashlib.sha256(
            canonical_json(event["controller_output"])
        ).hexdigest()

        policy_sha256 = self._rebind_forged_policy_and_ledger(
            forged,
            records,
        )
        self.assertEqual(
            HashChainLedger(runtime.ledger_path).verify(),
            (True, "1 record(s)"),
        )
        forged_digest_body = dict(forged)
        forged_digest = forged_digest_body.pop("receipt_sha256")
        self.assertEqual(
            forged_digest,
            hashlib.sha256(canonical_json(forged_digest_body)).hexdigest(),
        )

        valid, reason = verify_flow_receipt(
            forged,
            expected_run_id=runtime.run_id,
            expected_policy_sha256=policy_sha256,
            expected_ledger_path=runtime.ledger_path,
            expected_retained_head_sha256=forged["ledger"][
                "retained_head_sha256"
            ],
            expected_receipt_sha256=forged["receipt_sha256"],
        )
        self.assertFalse(valid)
        self.assertIn(
            "embedded policy positive terminals require a gate PASS",
            reason,
        )

    def test_offline_verifier_rechecks_embedded_policy_bounds_and_hooks(
        self,
    ) -> None:
        cases = (
            ("hard-bound", "max_steps", 4_097, "exceeds the kernel ceiling"),
            ("empty-claim", "claim_ceiling", "", "must be non-empty"),
            (
                "kernel-digest",
                "kernel_source_sha256",
                "not-a-digest",
                "must be a lowercase SHA-256",
            ),
            (
                "hook-source-digest",
                "hook.source_sha256",
                "f" * 63,
                "must be a lowercase SHA-256",
            ),
            (
                "hook-output-bound",
                "hook.max_output_bytes",
                1_048_577,
                "exceeds the kernel ceiling",
            ),
            (
                "hook-authority-key",
                "hook.allowed_update_keys",
                ["next_node"],
                "hook update keys are invalid",
            ),
            (
                "hook-signal-kind",
                "hook.allowed_signals",
                [HookSignal.OBSERVED.value],
                "hook signals are invalid",
            ),
        )
        for case, field, value, expected_reason in cases:
            with self.subTest(case=case):
                registration = self._registration(
                    pass_gate,
                    allowed_signals=(HookSignal.PASS,),
                )
                runtime = self._runtime(
                    registration,
                    name=f"forged-policy-{case}",
                )
                forged = copy.deepcopy(runtime.run({}))
                records = self._records(forged)
                if field == "max_steps":
                    forged["policy"]["bounds"][field] = value
                elif field.startswith("hook."):
                    forged["policy"]["hooks"][0][field.split(".", 1)[1]] = value
                else:
                    forged["policy"][field] = value
                policy_sha256 = self._rebind_forged_policy_and_ledger(
                    forged,
                    records,
                )

                valid, reason = verify_flow_receipt(
                    forged,
                    expected_run_id=runtime.run_id,
                    expected_policy_sha256=policy_sha256,
                    expected_ledger_path=runtime.ledger_path,
                    expected_retained_head_sha256=forged["ledger"][
                        "retained_head_sha256"
                    ],
                    expected_receipt_sha256=forged["receipt_sha256"],
                )
                self.assertFalse(valid)
                self.assertIn(expected_reason, reason)

    def test_offline_verifier_rechecks_embedded_policy_graph(self) -> None:
        cases = (
            ("hold-mismatch", "matching terminal"),
            ("retry-terminal", "RETRY must map to a bounded flow node"),
            ("incomplete", "lacks exhaustive transitions"),
            ("cycle", "non-retry edges must form a DAG"),
            ("unreachable", "flow nodes are not fully reachable"),
        )
        for case, expected_reason in cases:
            with self.subTest(case=case):
                registration = self._registration(
                    pass_gate,
                    allowed_signals=(HookSignal.PASS, HookSignal.RETRY),
                )
                runtime = self._runtime(
                    registration,
                    name=f"forged-graph-{case}",
                )
                forged = copy.deepcopy(runtime.run({}))
                records = self._records(forged)
                transitions = forged["policy"]["transitions"]
                if case == "hold-mismatch":
                    next(
                        transition
                        for transition in transitions
                        if transition["signal"] == HookSignal.HOLD.value
                    )["to_node"] = "PARKED"
                    forged["policy"]["terminal_nodes"].append("PARKED")
                elif case == "retry-terminal":
                    next(
                        transition
                        for transition in transitions
                        if transition["signal"] == HookSignal.RETRY.value
                    )["to_node"] = "HOLD"
                elif case == "incomplete":
                    forged["policy"]["transitions"] = [
                        transition
                        for transition in transitions
                        if transition["signal"] != HookSignal.HOLD.value
                    ]
                elif case == "cycle":
                    next(
                        transition
                        for transition in transitions
                        if transition["signal"] == HookSignal.PASS.value
                    )["to_node"] = "gate"
                else:
                    forged["policy"]["nodes"].append(
                        {"node_id": "orphan", "hook_id": "gate"}
                    )
                    forged["policy"]["transitions"].extend(
                        [
                            {
                                "from_node": "orphan",
                                "signal": HookSignal.PASS.value,
                                "to_node": "RELEASED",
                            },
                            {
                                "from_node": "orphan",
                                "signal": HookSignal.RETRY.value,
                                "to_node": "orphan",
                            },
                            {
                                "from_node": "orphan",
                                "signal": HookSignal.HOLD.value,
                                "to_node": "HOLD",
                            },
                        ]
                    )
                policy_sha256 = self._rebind_forged_policy_and_ledger(
                    forged,
                    records,
                )

                valid, reason = verify_flow_receipt(
                    forged,
                    expected_run_id=runtime.run_id,
                    expected_policy_sha256=policy_sha256,
                    expected_ledger_path=runtime.ledger_path,
                    expected_retained_head_sha256=forged["ledger"][
                        "retained_head_sha256"
                    ],
                    expected_receipt_sha256=forged["receipt_sha256"],
                )
                self.assertFalse(valid)
                self.assertIn(expected_reason, reason)

    def test_receipt_cannot_redirect_to_another_valid_local_ledger(self) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        policy = self._single_node_policy(registration)
        primary = MiniLevRuntime(
            policy,
            (registration,),
            run_id="ledger-redirection",
            ledger_path=self.root / "primary.jsonl",
        )
        decoy = MiniLevRuntime(
            policy,
            (registration,),
            run_id="ledger-redirection",
            ledger_path=self.root / "decoy.jsonl",
        )
        primary_receipt = primary.run({})
        decoy_receipt = decoy.run({})
        self.assertEqual(primary_receipt["event_hashes"], decoy_receipt["event_hashes"])
        self.assertEqual(
            HashChainLedger(
                decoy.ledger_path,
                decoy.ledger_path.with_name(decoy.ledger_path.name + ".head"),
            ).verify(),
            (True, "1 record(s)"),
        )
        redirected = copy.deepcopy(primary_receipt)
        redirected["ledger"] = copy.deepcopy(decoy_receipt["ledger"])
        self._recompute_receipt_digest(redirected)

        self.assertEqual(
            verify_flow_receipt(
                redirected,
                expected_run_id=primary.run_id,
                expected_policy_sha256=primary.policy_sha256,
                expected_ledger_path=primary.ledger_path,
                expected_retained_head_sha256=redirected["ledger"][
                    "retained_head_sha256"
                ],
                expected_receipt_sha256=redirected["receipt_sha256"],
            ),
            (False, "ledger path binding mismatch"),
        )

    def test_runtime_receipt_tamper_with_fresh_top_digest_is_rejected(
        self,
    ) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        runtime = self._runtime(registration, name="runtime-receipt-tamper")
        receipt = runtime.run({})
        tampered = copy.deepcopy(receipt)
        tampered["python_runtime"]["before"]["identity_sha256"] = "0" * 64
        tampered["python_runtime"]["after"]["identity_sha256"] = "0" * 64
        self._recompute_receipt_digest(tampered)

        self.assertEqual(
            verify_flow_receipt(
                tampered,
                expected_run_id=runtime.run_id,
                expected_policy_sha256=runtime.policy_sha256,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=runtime.retained_head_sha256,
                expected_receipt_sha256=tampered["receipt_sha256"],
            ),
            (False, "Python runtime receipt digest mismatch"),
        )

    def test_verifier_converts_python_runtime_error_to_false(self) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        runtime = self._runtime(registration, name="verifier-runtime-error")
        receipt = runtime.run({})

        with mock.patch(
            "constraintbox.mini_levos.capture_python_runtime",
            side_effect=PythonRuntimeError("forced verifier runtime failure"),
        ):
            result = verify_flow_receipt(
                receipt,
                expected_run_id=runtime.run_id,
                expected_policy_sha256=runtime.policy_sha256,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=runtime.retained_head_sha256,
                expected_receipt_sha256=runtime.receipt_sha256,
            )

        self.assertEqual(
            result,
            (
                False,
                "receipt verification error: forced verifier runtime failure",
            ),
        )

    def test_receipt_digest_tamper_is_rejected(self) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        runtime = self._runtime(registration, name="receipt-tamper")
        receipt = runtime.run({})
        tampered = copy.deepcopy(receipt)
        tampered["claim_ceiling"] = "forged broader claim"

        valid, reason = verify_flow_receipt(
            tampered,
            expected_run_id=runtime.run_id,
            expected_policy_sha256=runtime.policy_sha256,
            expected_ledger_path=runtime.ledger_path,
            expected_retained_head_sha256=runtime.retained_head_sha256,
            expected_receipt_sha256=runtime.receipt_sha256,
        )
        self.assertFalse(valid)
        self.assertEqual(reason, "receipt digest mismatch")

    def test_ledger_tamper_is_rejected(self) -> None:
        registration = self._registration(
            pass_gate,
            allowed_signals=(HookSignal.PASS,),
        )
        runtime = self._runtime(registration, name="ledger-tamper")
        receipt = runtime.run({})
        ledger_path = Path(receipt["ledger"]["path"])
        rows = ledger_path.read_text(encoding="utf-8").splitlines()
        first = json.loads(rows[0])
        first["record"]["typed_signal"] = "BLOCKED"
        rows[0] = json.dumps(first, sort_keys=True, separators=(",", ":"))
        ledger_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

        valid, reason = verify_flow_receipt(
            receipt,
            expected_run_id=runtime.run_id,
            expected_policy_sha256=runtime.policy_sha256,
            expected_ledger_path=runtime.ledger_path,
            expected_retained_head_sha256=runtime.retained_head_sha256,
            expected_receipt_sha256=runtime.receipt_sha256,
        )
        self.assertFalse(valid)
        self.assertIn("semantic ledger invalid: line hash mismatch", reason)

    def test_same_path_rechained_ledger_fails_original_runtime_root(self) -> None:
        registration = self._registration(
            retry_then_pass,
            allowed_update_keys=("attempt",),
        )
        runtime = self._runtime(registration, name="same-path-rewrite")
        receipt = runtime.run({})
        original_head = runtime.retained_head_sha256
        records = self._records(receipt)
        records[1]["input_sha256"] = "e" * 64
        self._rewrite_valid_ledger(receipt, records)

        self.assertEqual(
            HashChainLedger(runtime.ledger_path).verify(),
            (True, "2 record(s)"),
        )
        self.assertNotEqual(
            receipt["ledger"]["retained_head_sha256"],
            original_head,
        )
        self.assertEqual(
            verify_flow_receipt(
                receipt,
                expected_run_id=runtime.run_id,
                expected_policy_sha256=runtime.policy_sha256,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=original_head,
                expected_receipt_sha256=receipt["receipt_sha256"],
            ),
            (False, "ledger root binding mismatch"),
        )

    def test_rechained_event_deletion_is_rejected(self) -> None:
        registration = self._registration(
            retry_then_pass,
            allowed_update_keys=("attempt",),
        )
        runtime = self._runtime(registration, name="event-deletion")
        receipt = runtime.run({})
        records = self._records(receipt)
        self._rewrite_valid_ledger(receipt, records[1:])

        self.assertEqual(
            HashChainLedger(runtime.ledger_path).verify(),
            (True, "1 record(s)"),
        )
        self.assertEqual(
            verify_flow_receipt(
                receipt,
                expected_run_id=runtime.run_id,
                expected_policy_sha256=runtime.policy_sha256,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=receipt["ledger"][
                    "retained_head_sha256"
                ],
                expected_receipt_sha256=receipt["receipt_sha256"],
            ),
            (False, "event sequence mismatch"),
        )

    def test_rechained_event_reordering_is_rejected(self) -> None:
        registration = self._registration(
            retry_then_pass,
            allowed_update_keys=("attempt",),
        )
        runtime = self._runtime(registration, name="event-reordering")
        receipt = runtime.run({})
        records = self._records(receipt)
        self._rewrite_valid_ledger(receipt, list(reversed(records)))

        self.assertEqual(
            HashChainLedger(runtime.ledger_path).verify(),
            (True, "2 record(s)"),
        )
        self.assertEqual(
            verify_flow_receipt(
                receipt,
                expected_run_id=runtime.run_id,
                expected_policy_sha256=runtime.policy_sha256,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=receipt["ledger"][
                    "retained_head_sha256"
                ],
                expected_receipt_sha256=receipt["receipt_sha256"],
            ),
            (False, "event sequence mismatch"),
        )

    def test_rechained_context_chain_mutation_is_rejected(self) -> None:
        registration = self._registration(
            retry_then_pass,
            allowed_update_keys=("attempt",),
        )
        runtime = self._runtime(registration, name="context-chain-mutation")
        receipt = runtime.run({})
        records = self._records(receipt)
        records[1]["input_sha256"] = "f" * 64
        self._rewrite_valid_ledger(receipt, records)

        self.assertEqual(
            HashChainLedger(runtime.ledger_path).verify(),
            (True, "2 record(s)"),
        )
        self.assertEqual(
            verify_flow_receipt(
                receipt,
                expected_run_id=runtime.run_id,
                expected_policy_sha256=runtime.policy_sha256,
                expected_ledger_path=runtime.ledger_path,
                expected_retained_head_sha256=receipt["ledger"][
                    "retained_head_sha256"
                ],
                expected_receipt_sha256=receipt["receipt_sha256"],
            ),
            (False, "event context chain mismatch"),
        )


if __name__ == "__main__":
    unittest.main()
