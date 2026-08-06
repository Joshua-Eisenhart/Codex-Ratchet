from __future__ import annotations

import fcntl
import json
import math
import os
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest import mock

import constraintbox.execution_lease as execution_lease_module
from constraintbox.execution_lease import (
    MAX_TICK_NS,
    MAX_TTL_NS,
    ClockSample,
    ExecutionLeaseBinding,
    ExecutionLeaseConflict,
    ExecutionLeaseLockError,
    ExecutionLeasePersistenceError,
    ExecutionLeaseRejected,
    ExecutionLeaseStateError,
    ExecutionLeaseStore,
    ExecutionLeaseToken,
    ReleaseCause,
    VerificationStatus,
)
from constraintbox.intake import canonical_json


FLOW_SHA = "1" * 64
POLICY_SHA = "2" * 64
RUNTIME_SHA = "3" * 64


def make_binding(**changes: Any) -> ExecutionLeaseBinding:
    values = {
        "owner_id": "controller.worker-1",
        "run_id": "run-001",
        "node_id": "proposal_attempt",
        "visit": 1,
        "slot_sha256": "4" * 64,
        "flow_sha256": FLOW_SHA,
        "policy_sha256": POLICY_SHA,
        "runtime_sha256": RUNTIME_SHA,
        "instruction_sha256": "5" * 64,
    }
    values.update(changes)
    return ExecutionLeaseBinding(**values)


def sample(tick_ns: int, clock_id: str = "boot-A.controller-1") -> ClockSample:
    return ClockSample(clock_id=clock_id, tick_ns=tick_ns)


class ExecutionLeaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.path = self.root / "execution_lease.json"
        self.store = ExecutionLeaseStore(self.path)
        self.binding = make_binding(slot_sha256=self.store.slot_sha256)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def acquire(self, *, tick: int = 100, ttl: int = 100):
        return self.store.acquire(
            self.binding,
            ttl_ns=ttl,
            clock=sample(tick),
        )

    def test_binding_clock_and_ttl_are_strictly_typed_and_bounded(self) -> None:
        with self.assertRaises(ValueError):
            make_binding(owner_id="")
        with self.assertRaises(ValueError):
            make_binding(node_id="../escape")
        with self.assertRaises(ValueError):
            make_binding(owner_id="contrôller")
        with self.assertRaises(ValueError):
            make_binding(policy_sha256="A" * 64)
        with self.assertRaises(ValueError):
            make_binding(visit=True)
        with self.assertRaises(ValueError):
            make_binding(visit=0)
        with self.assertRaises(ValueError):
            make_binding(slot_sha256="A" * 64)
        with self.assertRaises(ValueError):
            make_binding(instruction_sha256="too-short")
        with self.assertRaises(ValueError):
            ClockSample(clock_id="boot-A", tick_ns=True)
        with self.assertRaises(ValueError):
            ClockSample(clock_id="boot-A", tick_ns=-1)
        with self.assertRaises(ValueError):
            ClockSample(clock_id="boot-A", tick_ns=MAX_TICK_NS + 1)
        with self.assertRaises(ValueError):
            self.store.acquire(self.binding, ttl_ns=True, clock=sample(0))
        with self.assertRaises(ValueError):
            self.store.acquire(self.binding, ttl_ns=0, clock=sample(0))
        with self.assertRaises(ValueError):
            self.store.acquire(
                self.binding, ttl_ns=MAX_TTL_NS + 1, clock=sample(0)
            )
        with self.assertRaises(ValueError):
            self.store.acquire(
                self.binding, ttl_ns=2, clock=sample(MAX_TICK_NS - 1)
            )
        with self.assertRaises(ValueError):
            ExecutionLeaseStore(
                self.root / "nan-lock.json",
                lock_timeout_seconds=math.nan,
            )

    def test_acquire_persists_canonical_public_receipt_without_nonce(self) -> None:
        grant = self.acquire()
        raw = self.path.read_bytes()
        parsed = json.loads(raw)

        self.assertEqual(raw, canonical_json(parsed))
        self.assertEqual(parsed, grant.receipt)
        self.assertNotIn(grant.token.nonce, raw.decode("ascii"))
        self.assertEqual(
            parsed["nonce_sha256"],
            execution_lease_module.hashlib.sha256(
                grant.token.nonce.encode("ascii")
            ).hexdigest(),
        )
        self.assertEqual(parsed["authority"]["purpose"], "execution_ownership_only")
        self.assertIs(parsed["authority"]["authorizes_output_release"], False)
        self.assertIs(parsed["authority"]["authorizes_transition"], False)
        self.assertEqual(parsed["generation"], 1)
        self.assertEqual(parsed["event"], "ACQUIRED")
        self.assertEqual(parsed["expires_tick_ns"], 200)
        self.assertEqual(self.store.read_receipt(), parsed)
        self.assertTrue(self.store.slot_path.is_file())
        self.assertTrue(self.store.head_path.is_file())
        head = json.loads(self.store.head_path.read_bytes())
        marker = json.loads(self.store.slot_path.read_bytes())
        self.assertEqual(head["record_sha256"], parsed["record_sha256"])
        self.assertEqual(head["generation"], parsed["generation"])
        self.assertEqual(head["slot_sha256"], self.store.slot_sha256)
        self.assertEqual(marker["slot_sha256"], self.store.slot_sha256)

        grant.receipt["status"] = "FORGED"
        self.assertEqual(self.store.read_receipt()["status"], "ACTIVE")

    def test_valid_verdict_is_deliberately_not_truthy(self) -> None:
        grant = self.acquire()
        verdict = self.store.verify(
            self.binding, grant.token, clock=sample(100)
        )
        self.assertIs(verdict.status, VerificationStatus.VALID)
        self.assertEqual(verdict.record_sha256, grant.token.record_sha256)
        with self.assertRaises(TypeError):
            bool(verdict)

    def test_every_controller_identity_field_is_bound(self) -> None:
        grant = self.acquire()
        mismatches = {
            "owner_id": "controller.worker-2",
            "run_id": "run-002",
            "node_id": "different_node",
            "visit": 2,
            "slot_sha256": "6" * 64,
            "flow_sha256": "7" * 64,
            "policy_sha256": "8" * 64,
            "runtime_sha256": "6" * 64,
            "instruction_sha256": "9" * 64,
        }
        for field, value in mismatches.items():
            with self.subTest(field=field):
                verdict = self.store.verify(
                    replace(self.binding, **{field: value}),
                    grant.token,
                    clock=sample(101),
                )
                self.assertIs(
                    verdict.status, VerificationStatus.IDENTITY_MISMATCH
                )

    def test_wrong_nonce_and_forged_token_fields_fail_closed(self) -> None:
        grant = self.acquire()
        variants = (
            replace(grant.token, nonce="f" * 64),
            replace(grant.token, lease_id="e" * 64),
            replace(grant.token, record_sha256="d" * 64),
            replace(grant.token, generation=grant.token.generation + 1),
            replace(grant.token, binding_sha256="c" * 64),
        )
        for token in variants:
            with self.subTest(token=token):
                verdict = self.store.verify(
                    self.binding, token, clock=sample(101)
                )
                self.assertIs(verdict.status, VerificationStatus.TOKEN_MISMATCH)

    def test_heartbeat_rotates_token_and_renews_the_fixed_ttl(self) -> None:
        first = self.acquire()
        second = self.store.heartbeat(
            self.binding, first.token, clock=sample(150)
        )

        self.assertNotEqual(first.token.nonce, second.token.nonce)
        self.assertEqual(second.receipt["generation"], 2)
        self.assertEqual(second.receipt["event"], "HEARTBEAT")
        self.assertEqual(second.receipt["ttl_ns"], 100)
        self.assertEqual(second.receipt["expires_tick_ns"], 250)
        self.assertEqual(
            second.receipt["previous_record_sha256"],
            first.token.record_sha256,
        )
        self.assertIs(
            self.store.verify(
                self.binding, first.token, clock=sample(151)
            ).status,
            VerificationStatus.TOKEN_MISMATCH,
        )
        self.assertIs(
            self.store.verify(
                self.binding, second.token, clock=sample(151)
            ).status,
            VerificationStatus.VALID,
        )

    def test_clock_domain_rollback_and_half_open_expiry_fail_closed(self) -> None:
        grant = self.acquire()
        self.assertIs(
            self.store.verify(
                self.binding, grant.token, clock=sample(199)
            ).status,
            VerificationStatus.VALID,
        )
        self.assertIs(
            self.store.verify(
                self.binding, grant.token, clock=sample(200)
            ).status,
            VerificationStatus.EXPIRED,
        )
        self.assertIs(
            self.store.verify(
                self.binding,
                grant.token,
                clock=sample(101, "boot-B.controller-1"),
            ).status,
            VerificationStatus.CLOCK_MISMATCH,
        )

        renewed = self.store.heartbeat(
            self.binding, grant.token, clock=sample(150)
        )
        self.assertIs(
            self.store.verify(
                self.binding, renewed.token, clock=sample(149)
            ).status,
            VerificationStatus.CLOCK_ROLLBACK,
        )

    def test_expired_lease_cannot_heartbeat_or_release(self) -> None:
        grant = self.acquire()
        original = self.path.read_bytes()

        with self.assertRaises(ExecutionLeaseRejected) as heartbeat_error:
            self.store.heartbeat(
                self.binding, grant.token, clock=sample(200)
            )
        self.assertIs(
            heartbeat_error.exception.verdict.status, VerificationStatus.EXPIRED
        )
        with self.assertRaises(ExecutionLeaseRejected) as release_error:
            self.store.release(
                self.binding,
                grant.token,
                clock=sample(201),
                cause=ReleaseCause.PARKED,
            )
        self.assertIs(
            release_error.exception.verdict.status, VerificationStatus.EXPIRED
        )
        self.assertEqual(self.path.read_bytes(), original)

    def test_release_only_ends_ownership_and_cannot_be_replayed(self) -> None:
        grant = self.acquire()
        receipt = self.store.release(
            self.binding,
            grant.token,
            clock=sample(150),
            cause=ReleaseCause.COMPLETED,
        )

        self.assertEqual(receipt["status"], "RELEASED")
        self.assertEqual(receipt["event"], "RELEASED")
        self.assertEqual(receipt["release_cause"], "COMPLETED")
        self.assertIsNone(receipt["nonce_sha256"])
        self.assertIs(receipt["authority"]["authorizes_output_release"], False)
        self.assertIs(receipt["authority"]["authorizes_transition"], False)
        self.assertIs(
            self.store.verify(
                self.binding, grant.token, clock=sample(151)
            ).status,
            VerificationStatus.RELEASED,
        )
        with self.assertRaises(ExecutionLeaseRejected) as replay_error:
            self.store.release(
                self.binding,
                grant.token,
                clock=sample(151),
                cause=ReleaseCause.COMPLETED,
            )
        self.assertIs(
            replay_error.exception.verdict.status, VerificationStatus.RELEASED
        )
        with self.assertRaises(TypeError):
            self.store.release(
                self.binding,
                grant.token,
                clock=sample(151),
                cause="COMPLETED",  # type: ignore[arg-type]
            )

    def test_acquire_conflicts_until_expiry_then_replaces_with_new_nonce(self) -> None:
        first = self.acquire()
        with self.assertRaises(ExecutionLeaseConflict):
            self.store.acquire(
                replace(self.binding, owner_id="controller.worker-2"),
                ttl_ns=100,
                clock=sample(199),
            )
        with self.assertRaises(ExecutionLeaseConflict):
            self.store.acquire(
                replace(self.binding, owner_id="controller.worker-2"),
                ttl_ns=100,
                clock=sample(200, "another-clock"),
            )

        second_binding = replace(self.binding, owner_id="controller.worker-2")
        second = self.store.acquire(
            second_binding,
            ttl_ns=50,
            clock=sample(200),
        )
        self.assertEqual(second.receipt["event"], "ACQUIRED_AFTER_EXPIRY")
        self.assertEqual(second.receipt["generation"], 2)
        self.assertEqual(
            second.receipt["previous_record_sha256"],
            first.token.record_sha256,
        )
        self.assertNotEqual(second.token.nonce, first.token.nonce)
        self.assertIs(
            self.store.verify(
                self.binding, first.token, clock=sample(201)
            ).status,
            VerificationStatus.IDENTITY_MISMATCH,
        )
        self.assertIs(
            self.store.verify(
                second_binding, second.token, clock=sample(201)
            ).status,
            VerificationStatus.VALID,
        )

    def test_released_slot_can_move_to_a_new_clock_domain(self) -> None:
        first = self.acquire()
        released = self.store.release(
            self.binding,
            first.token,
            clock=sample(110),
            cause=ReleaseCause.CANCELLED,
        )
        next_binding = replace(
            self.binding,
            run_id="run-002",
            slot_sha256=self.store.slot_sha256,
        )
        second = self.store.acquire(
            next_binding,
            ttl_ns=20,
            clock=sample(0, "boot-B.controller-1"),
        )
        self.assertEqual(second.receipt["event"], "ACQUIRED_AFTER_RELEASE")
        self.assertEqual(
            second.receipt["previous_record_sha256"],
            released["record_sha256"],
        )

    def test_released_slot_rejects_rollback_in_the_same_clock_domain(self) -> None:
        first = self.acquire()
        self.store.release(
            self.binding,
            first.token,
            clock=sample(150),
            cause=ReleaseCause.CANCELLED,
        )
        with self.assertRaises(ExecutionLeaseConflict):
            self.store.acquire(
                replace(self.binding, run_id="run-002"),
                ttl_ns=20,
                clock=sample(149),
            )

    def test_saved_state_replay_cannot_satisfy_the_newest_token(self) -> None:
        first = self.acquire()
        saved_first_state = self.path.read_bytes()
        second = self.store.heartbeat(
            self.binding, first.token, clock=sample(150)
        )

        self.path.write_bytes(saved_first_state)
        verdict = self.store.verify(
            self.binding, second.token, clock=sample(151)
        )
        self.assertIs(verdict.status, VerificationStatus.MALFORMED)
        self.assertIn("high-water", verdict.reason)

        old_verdict = self.store.verify(
            self.binding, first.token, clock=sample(151)
        )
        self.assertIs(old_verdict.status, VerificationStatus.MALFORMED)

    def test_deleted_active_state_cannot_reset_the_slot_to_genesis(self) -> None:
        self.acquire()
        self.path.unlink()
        placeholder = ExecutionLeaseToken(
            lease_id="a" * 64,
            binding_sha256=self.binding.sha256,
            generation=1,
            record_sha256="b" * 64,
            nonce="c" * 64,
        )
        verdict = self.store.verify(
            self.binding, placeholder, clock=sample(101)
        )
        self.assertIs(verdict.status, VerificationStatus.MALFORMED)
        with self.assertRaises(ExecutionLeaseStateError):
            self.store.acquire(
                replace(self.binding, owner_id="controller.worker-2"),
                ttl_ns=100,
                clock=sample(101),
            )

    def test_missing_marker_or_head_fails_closed(self) -> None:
        grant = self.acquire()
        for component in (self.store.slot_path, self.store.head_path):
            with self.subTest(component=component.name):
                saved = component.read_bytes()
                component.unlink()
                self.assertIs(
                    self.store.verify(
                        self.binding, grant.token, clock=sample(101)
                    ).status,
                    VerificationStatus.MALFORMED,
                )
                component.write_bytes(saved)

    def test_binding_cannot_validate_in_another_store_path(self) -> None:
        first = self.acquire()
        other_store = ExecutionLeaseStore(self.root / "other-slot.json")
        with self.assertRaises(ValueError):
            other_store.acquire(
                self.binding, ttl_ns=100, clock=sample(100)
            )

        for source, destination in (
            (self.store.slot_path, other_store.slot_path),
            (self.path, other_store.state_path),
            (self.store.head_path, other_store.head_path),
        ):
            destination.write_bytes(source.read_bytes())
        verdict = other_store.verify(
            self.binding, first.token, clock=sample(101)
        )
        self.assertIs(verdict.status, VerificationStatus.MALFORMED)

    def test_malformed_or_noncanonical_state_is_not_overwritten(self) -> None:
        cases = (
            b"not json",
            b'{"schema":"x","schema":"y"}',
            b"{}",
        )
        for index, payload in enumerate(cases):
            with self.subTest(index=index):
                path = self.root / f"malformed-{index}.json"
                path.write_bytes(payload)
                store = ExecutionLeaseStore(path)
                local_binding = replace(
                    self.binding, slot_sha256=store.slot_sha256
                )
                placeholder = ExecutionLeaseToken(
                    lease_id="a" * 64,
                    binding_sha256=local_binding.sha256,
                    generation=1,
                    record_sha256="b" * 64,
                    nonce="c" * 64,
                )
                verdict = store.verify(
                    local_binding, placeholder, clock=sample(0)
                )
                self.assertIs(verdict.status, VerificationStatus.MALFORMED)
                with self.assertRaises(ExecutionLeaseStateError):
                    store.acquire(
                        local_binding, ttl_ns=10, clock=sample(0)
                    )
                self.assertEqual(path.read_bytes(), payload)

    def test_type_confused_authority_and_unhashable_event_are_malformed(self) -> None:
        grant = self.acquire()
        for index, mutation in enumerate(("authority", "event")):
            with self.subTest(mutation=mutation):
                forged = dict(grant.receipt)
                if mutation == "authority":
                    forged["authority"] = {
                        "purpose": "execution_ownership_only",
                        "authorizes_output_release": 0,
                        "authorizes_transition": 0,
                    }
                else:
                    forged["event"] = ["ACQUIRED"]
                forged["record_sha256"] = execution_lease_module._record_digest(
                    forged
                )
                self.path.write_bytes(canonical_json(forged))
                placeholder = ExecutionLeaseToken(
                    lease_id=grant.token.lease_id,
                    binding_sha256=grant.token.binding_sha256,
                    generation=grant.token.generation,
                    record_sha256=forged["record_sha256"],
                    nonce=grant.token.nonce,
                )
                verdict = self.store.verify(
                    self.binding, placeholder, clock=sample(101)
                )
                self.assertIs(verdict.status, VerificationStatus.MALFORMED)
                self.path.write_bytes(canonical_json(grant.receipt))

    def test_invalid_nonce_source_cannot_persist_an_unusable_lease(self) -> None:
        with mock.patch.object(
            execution_lease_module.secrets,
            "token_hex",
            return_value="not-a-nonce",
        ):
            with self.assertRaises(ValueError):
                self.store.acquire(
                    self.binding, ttl_ns=10, clock=sample(0)
                )
        self.assertFalse(self.path.exists())

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink unavailable")
    def test_symlink_state_is_rejected(self) -> None:
        target = self.root / "target.json"
        target.write_bytes(b"{}")
        link = self.root / "linked-state.json"
        link.symlink_to(target)
        store = ExecutionLeaseStore(link)
        local_binding = replace(
            self.binding, slot_sha256=store.slot_sha256
        )
        placeholder = ExecutionLeaseToken(
            lease_id="a" * 64,
            binding_sha256=local_binding.sha256,
            generation=1,
            record_sha256="b" * 64,
            nonce="c" * 64,
        )
        self.assertIs(
            store.verify(
                local_binding, placeholder, clock=sample(0)
            ).status,
            VerificationStatus.MALFORMED,
        )
        with self.assertRaises(ExecutionLeaseStateError):
            store.acquire(local_binding, ttl_ns=10, clock=sample(0))
        self.assertEqual(target.read_bytes(), b"{}")

    def test_failed_atomic_replace_preserves_old_state_and_current_token(self) -> None:
        grant = self.acquire()
        original = self.path.read_bytes()

        with mock.patch.object(
            execution_lease_module.os,
            "replace",
            side_effect=OSError("injected replace failure"),
        ):
            with self.assertRaises(ExecutionLeasePersistenceError) as captured:
                self.store.heartbeat(
                    self.binding, grant.token, clock=sample(150)
                )
        self.assertIs(captured.exception.state_may_have_changed, False)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertIs(
            self.store.verify(
                self.binding, grant.token, clock=sample(151)
            ).status,
            VerificationStatus.VALID,
        )
        self.assertEqual(
            list(self.root.glob(f".{self.path.name}.*.tmp")),
            [],
        )

    def test_post_replace_fsync_failure_is_reported_as_uncertain_and_fails_closed(
        self,
    ) -> None:
        grant = self.acquire()
        real_fsync = execution_lease_module.os.fsync
        calls = 0

        def fail_directory_fsync(descriptor: int) -> None:
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError("injected directory fsync failure")
            real_fsync(descriptor)

        with mock.patch.object(
            execution_lease_module.os, "fsync", side_effect=fail_directory_fsync
        ):
            with self.assertRaises(ExecutionLeasePersistenceError) as captured:
                self.store.heartbeat(
                    self.binding, grant.token, clock=sample(150)
                )
        self.assertIs(captured.exception.state_may_have_changed, True)
        self.assertIs(
            self.store.verify(
                self.binding, grant.token, clock=sample(151)
            ).status,
            VerificationStatus.TOKEN_MISMATCH,
        )

    def test_state_head_partial_commit_is_detected_and_cannot_validate(self) -> None:
        grant = self.acquire()
        real_replace = execution_lease_module.os.replace
        calls = 0

        def fail_head_replace(source: Path, destination: Path) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected retained-head replace failure")
            real_replace(source, destination)

        with mock.patch.object(
            execution_lease_module.os,
            "replace",
            side_effect=fail_head_replace,
        ):
            with self.assertRaises(ExecutionLeasePersistenceError) as captured:
                self.store.heartbeat(
                    self.binding, grant.token, clock=sample(150)
                )
        self.assertIs(captured.exception.state_may_have_changed, True)
        verdict = self.store.verify(
            self.binding, grant.token, clock=sample(151)
        )
        self.assertIs(verdict.status, VerificationStatus.MALFORMED)
        self.assertIn("high-water", verdict.reason)

    def test_store_lock_timeout_fails_without_reading_or_writing_state(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path.parent, os.O_RDONLY)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            blocked_store = ExecutionLeaseStore(
                self.path, lock_timeout_seconds=0
            )
            with self.assertRaises(ExecutionLeaseLockError):
                blocked_store.acquire(
                    self.binding, ttl_ns=10, clock=sample(0)
                )
            self.assertFalse(self.path.exists())
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def test_concurrent_acquire_has_exactly_one_winner(self) -> None:
        barrier = threading.Barrier(2)

        def contend(owner_id: str) -> str:
            store = ExecutionLeaseStore(self.path)
            binding = make_binding(
                owner_id=owner_id,
                slot_sha256=store.slot_sha256,
            )
            barrier.wait(timeout=2)
            try:
                store.acquire(binding, ttl_ns=100, clock=sample(100))
            except ExecutionLeaseConflict:
                return "CONFLICT"
            return "ACQUIRED"

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(
                executor.map(
                    contend,
                    ("controller.worker-1", "controller.worker-2"),
                )
            )
        self.assertEqual(sorted(results), ["ACQUIRED", "CONFLICT"])

    def test_token_round_trip_rejects_extra_or_missing_fields(self) -> None:
        grant = self.acquire()
        restored = ExecutionLeaseToken.from_dict(grant.token.as_dict())
        self.assertEqual(restored, grant.token)

        extra = grant.token.as_dict()
        extra["verdict"] = "PASS"
        with self.assertRaises(ValueError):
            ExecutionLeaseToken.from_dict(extra)
        missing = grant.token.as_dict()
        del missing["nonce"]
        with self.assertRaises(ValueError):
            ExecutionLeaseToken.from_dict(missing)


if __name__ == "__main__":
    unittest.main()
