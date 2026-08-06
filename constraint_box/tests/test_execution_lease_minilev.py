from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from constraintbox.execution_lease import (
    ClockSample,
    ExecutionLeasePersistenceError,
    ExecutionLeaseStore,
)
from constraintbox.mini_levos import (
    ExecutionLeaseGuard,
    ExecutionLeaseRequirement,
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


def leased_pass(_context: dict[str, object]) -> HookResult:
    return HookResult(HookSignal.PASS, {"bounded": "observation"})


def leased_failure(_context: dict[str, object]) -> HookResult:
    raise RuntimeError("controlled hook failure")


class _Clock:
    def __init__(self, ticks: list[int]):
        self._ticks = iter(ticks)

    def sample(self) -> ClockSample:
        return ClockSample("lease-test-clock", next(self._ticks))


class _ReleaseFailingStore(ExecutionLeaseStore):
    def release(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise ExecutionLeasePersistenceError(
            "injected release persistence failure",
            state_may_have_changed=False,
        )


class ExecutionLeaseMiniLevTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def _registration(self, handler=leased_pass) -> HookRegistration:
        source = Path(__file__).resolve()
        return HookRegistration(
            hook_id="leased-hook",
            kind=HookKind.GATE,
            handler=handler,
            source_path=source,
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            code_sha256=handler_code_sha256(handler),
            allowed_signals=(HookSignal.PASS,),
        )

    def _policy(self, requirement: ExecutionLeaseRequirement) -> FlowPolicy:
        return FlowPolicy(
            flow_id="leased-mini-flow",
            entry_node="leased-node",
            nodes=(FlowNode("leased-node", "leased-hook"),),
            transitions=(
                FlowTransition("leased-node", HookSignal.PASS, "RELEASED"),
                FlowTransition("leased-node", HookSignal.HOLD, "HOLD"),
            ),
            terminal_nodes=("HOLD", "RELEASED"),
            required_nodes=("leased-node",),
            max_steps=1,
            max_visits_per_node=1,
            max_retries=0,
            max_context_bytes=4_096,
            max_event_bytes=65_536,
            max_receipt_bytes=262_144,
            claim_ceiling="local cooperative execution-lease test only",
            execution_lease=requirement,
        )

    def _runtime(
        self,
        *,
        name: str,
        handler=leased_pass,
        ticks: list[int],
        store_type=ExecutionLeaseStore,
        requirement_clock_id: str = "lease-test-clock",
    ) -> MiniLevRuntime:
        store = store_type(self.root / f"{name}.lease.json")
        requirement = ExecutionLeaseRequirement(
            node_id="leased-node",
            hook_id="leased-hook",
            owner_id="constraintbox-test-controller",
            slot_sha256=store.slot_sha256,
            ttl_ns=10,
            clock_source="test-monotonic-clock-v1",
            clock_id=requirement_clock_id,
        )
        registration = self._registration(handler)
        return MiniLevRuntime(
            self._policy(requirement),
            (registration,),
            run_id=name,
            ledger_path=self.root / f"{name}.ledger.jsonl",
            execution_lease_guard=ExecutionLeaseGuard(
                requirement,
                store,
                clock_sample=_Clock(ticks).sample,
            ),
        )

    @staticmethod
    def _record(receipt: dict[str, object]) -> dict[str, object]:
        ledger_path = Path(receipt["ledger"]["path"])
        return json.loads(
            ledger_path.read_text(encoding="utf-8").strip()
        )["record"]

    def _verify(self, runtime: MiniLevRuntime, receipt: dict[str, object]) -> None:
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

    def test_required_policy_cannot_run_without_its_matching_guard(self) -> None:
        store = ExecutionLeaseStore(self.root / "missing-guard.lease.json")
        requirement = ExecutionLeaseRequirement(
            node_id="leased-node",
            hook_id="leased-hook",
            owner_id="constraintbox-test-controller",
            slot_sha256=store.slot_sha256,
            ttl_ns=10,
            clock_source="test-monotonic-clock-v1",
            clock_id="lease-test-clock",
        )
        with self.assertRaisesRegex(MiniLevError, "requires its matching guard"):
            MiniLevRuntime(
                self._policy(requirement),
                (self._registration(),),
                run_id="missing-guard",
                ledger_path=self.root / "missing-guard.ledger.jsonl",
            )

    def test_clock_not_matching_the_frozen_policy_holds_before_the_hook(self) -> None:
        runtime = self._runtime(
            name="wrong-clock-domain",
            handler=leased_pass,
            ticks=[0],
            requirement_clock_id="other-policy-clock",
        )
        receipt = runtime.run({})

        self.assertEqual(receipt["terminal"], "HOLD")
        audit = self._record(receipt)["execution_lease"]
        self.assertEqual(audit["failure_stage"], "acquire")
        self.assertEqual(audit["clock_id"], "other-policy-clock")
        self.assertFalse(audit["handler_started"])
        self._verify(runtime, receipt)

    def test_valid_lifecycle_releases_before_a_positive_terminal(self) -> None:
        runtime = self._runtime(name="lease-success", ticks=[0, 1, 2, 3])
        receipt = runtime.run({"fixed": True})

        self.assertEqual(receipt["terminal"], "RELEASED")
        event = self._record(receipt)
        audit = event["execution_lease"]
        self.assertEqual(audit["pre_hook_verdict"]["status"], "VALID")
        self.assertEqual(audit["post_hook_verdict"]["status"], "VALID")
        self.assertEqual(audit["release_status"], "RELEASED")
        self.assertEqual(audit["release_cause"], "COMPLETED")
        self.assertIsNone(audit["failure_stage"])
        self.assertNotIn("nonce", audit)
        self.assertNotIn("nonce", audit["acquire_record"])
        self.assertNotIn("nonce", audit["release_record"])
        self.assertTrue(receipt["execution_lease"]["all_protected_events_released"])
        self._verify(runtime, receipt)

    def test_exact_expiry_after_callback_holds_and_cannot_release(self) -> None:
        runtime = self._runtime(name="lease-expiry", ticks=[0, 1, 10, 11])
        receipt = runtime.run({})

        self.assertEqual(receipt["terminal"], "HOLD")
        event = self._record(receipt)
        audit = event["execution_lease"]
        self.assertEqual(event["controller_reason"], "execution_lease_post_hook_verify")
        self.assertEqual(audit["failure_stage"], "post_hook_verify")
        self.assertEqual(audit["release_status"], "RELEASE_FAILED")
        self.assertFalse(receipt["execution_lease"]["all_protected_events_released"])
        self._verify(runtime, receipt)

    def test_hook_exception_releases_failed_ownership_and_holds(self) -> None:
        runtime = self._runtime(
            name="lease-handler-error",
            handler=leased_failure,
            ticks=[0, 1, 2],
        )
        receipt = runtime.run({})

        self.assertEqual(receipt["terminal"], "HOLD")
        audit = self._record(receipt)["execution_lease"]
        self.assertEqual(audit["failure_stage"], "handler")
        self.assertEqual(audit["release_status"], "RELEASED")
        self.assertEqual(audit["release_cause"], "FAILED")
        self._verify(runtime, receipt)

    def test_release_persistence_failure_holds_after_a_valid_callback(self) -> None:
        runtime = self._runtime(
            name="lease-release-error",
            ticks=[0, 1, 2, 3],
            store_type=_ReleaseFailingStore,
        )
        receipt = runtime.run({})

        self.assertEqual(receipt["terminal"], "HOLD")
        audit = self._record(receipt)["execution_lease"]
        self.assertEqual(audit["failure_stage"], "release")
        self.assertEqual(audit["release_status"], "RELEASE_FAILED")
        self.assertEqual(audit["post_hook_verdict"]["status"], "VALID")
        self._verify(runtime, receipt)


if __name__ == "__main__":
    unittest.main()
