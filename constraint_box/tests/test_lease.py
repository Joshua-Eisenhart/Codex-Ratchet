from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from constraintbox.lease import (
    ABSENT,
    MALFORMED,
    STALE,
    TREE_MISMATCH,
    VALID,
    LeaseDenied,
    LeaseError,
    Verdict,
    issue_lease,
    lease_digest,
    read_lease,
    staged_tree_id,
    verify_lease,
    verify_lease_file,
    write_lease,
)


NOW = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
TTL = 3600.0

# Every git command in this file runs inside a throwaway temporary repository
# created by setUp. No test touches the repository this module lives in.


class TempRepo:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(root),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_AUTHOR_NAME": "lease-test",
            "GIT_AUTHOR_EMAIL": "lease-test@example.invalid",
            "GIT_COMMITTER_NAME": "lease-test",
            "GIT_COMMITTER_EMAIL": "lease-test@example.invalid",
            "GIT_AUTHOR_DATE": "2026-07-26T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-07-26T00:00:00+00:00",
        }
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(self.root),
            env=self.env,
            capture_output=True,
            check=True,
        )
        return completed.stdout.decode("utf-8").strip()

    def write(self, name: str, text: str) -> None:
        (self.root / name).write_text(text, encoding="utf-8")

    def stage(self, name: str, text: str) -> str:
        """Write a file and stage it. Returns the resulting staged tree id."""
        self.write(name, text)
        self.git("add", name)
        return staged_tree_id(self.root)

    def head_short(self) -> str:
        return self.git("rev-parse", "--short", "HEAD")


SAFE_RUNNER = ["grep", "-q", "SAFE", "payload.txt"]


class LeaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = TempRepo(Path(self.temp.name) / "repo")
        self.repo.stage("payload.txt", "PLACEHOLDER\n")
        self.repo.git("commit", "-q", "-m", "initial")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def issue_safe_lease(self, **kwargs) -> dict:
        return issue_lease(
            self.repo.root, [SAFE_RUNNER], ttl_seconds=TTL, now=NOW, **kwargs
        )


class TreeIdentityTests(LeaseTestCase):
    """Requirement 1: identity is the staged tree, not HEAD."""

    def test_restaging_different_content_changes_the_tree_id(self) -> None:
        tree_a = self.repo.stage("payload.txt", "SAFE\n")
        tree_b = self.repo.stage("payload.txt", "MALICIOUS\n")
        self.assertNotEqual(tree_a, tree_b)

    def test_restaging_does_not_change_head(self) -> None:
        head_before = self.repo.head_short()
        self.repo.stage("payload.txt", "SAFE\n")
        after_safe = self.repo.head_short()
        self.repo.stage("payload.txt", "MALICIOUS\n")
        head_after = self.repo.head_short()
        self.assertEqual(head_before, after_safe)
        self.assertEqual(head_before, head_after)

    def test_unstaged_working_tree_edit_does_not_change_the_tree_id(self) -> None:
        tree_a = self.repo.stage("payload.txt", "SAFE\n")
        self.repo.write("payload.txt", "MALICIOUS\n")
        self.assertEqual(tree_a, staged_tree_id(self.repo.root))

    def test_lease_stays_valid_for_unstaged_edits_and_dies_on_staging(self) -> None:
        self.repo.stage("payload.txt", "SAFE\n")
        lease = self.issue_safe_lease()
        self.repo.write("payload.txt", "MALICIOUS\n")
        self.assertEqual(
            verify_lease_file_status(self, lease), VALID, "unstaged edit is not staged"
        )
        self.repo.git("add", "payload.txt")
        self.assertEqual(verify_lease_file_status(self, lease), TREE_MISMATCH)


def verify_lease_file_status(case: LeaseTestCase, lease: dict) -> str:
    return verify_lease(lease, staged_tree_id(case.repo.root), NOW).status


class BypassReproductionTests(LeaseTestCase):
    """The measured agentguard sequence, replayed against the tree-bound lease."""

    def test_agentguard_bypass_sequence_is_tree_mismatch(self) -> None:
        # 1. stage SAFE -- this is the tree the proof gets earned against.
        head_before = self.repo.head_short()
        tree_safe = self.repo.stage("payload.txt", "SAFE\n")

        # 2. earn the lease by actually running the declared runner.
        lease = self.issue_safe_lease()
        self.assertEqual(lease["tree_id"], tree_safe)
        self.assertEqual(lease["runners"][0]["exit_code"], 0)
        self.assertEqual(verify_lease(lease, tree_safe, NOW).status, VALID)

        # 3. swap the staged content -- the agentguard bypass move.
        tree_malicious = self.repo.stage("payload.txt", "MALICIOUS\n")
        head_after = self.repo.head_short()

        # The key agentguard used cannot see the swap.
        self.assertEqual(
            head_before,
            head_after,
            "HEAD is identical across the swap, which is why keying on it admits "
            "a different tree",
        )
        # The key this lease uses can.
        self.assertNotEqual(tree_safe, tree_malicious)

        # 4. the same lease, presented against the swapped tree.
        verdict = verify_lease(lease, tree_malicious, NOW)
        self.assertEqual(verdict.status, TREE_MISMATCH)
        self.assertIn(tree_safe, verdict.reason)
        self.assertIn(tree_malicious, verdict.reason)

    def test_reissuing_against_the_swapped_tree_is_denied(self) -> None:
        self.repo.stage("payload.txt", "SAFE\n")
        self.issue_safe_lease()
        self.repo.stage("payload.txt", "MALICIOUS\n")
        with self.assertRaises(LeaseDenied) as caught:
            self.issue_safe_lease()
        self.assertEqual(caught.exception.runs[0]["exit_code"], 1)

    def test_tree_mismatch_is_reported_even_when_also_expired(self) -> None:
        self.repo.stage("payload.txt", "SAFE\n")
        lease = self.issue_safe_lease()
        tree_malicious = self.repo.stage("payload.txt", "MALICIOUS\n")
        long_after = NOW + timedelta(seconds=TTL * 10)
        self.assertEqual(
            verify_lease(lease, tree_malicious, long_after).status, TREE_MISMATCH
        )


class LeaseContentTests(LeaseTestCase):
    """Requirement 2: what a lease carries."""

    def test_lease_carries_tree_runners_codes_digests_and_window(self) -> None:
        tree = self.repo.stage("payload.txt", "SAFE\n")
        lease = self.issue_safe_lease()
        self.assertEqual(lease["tree_id"], tree)
        self.assertEqual(lease["issued_at_utc"], NOW.isoformat())
        self.assertEqual(
            lease["expires_at_utc"], (NOW + timedelta(seconds=TTL)).isoformat()
        )
        self.assertEqual(lease["ttl_seconds"], TTL)
        self.assertIn("issued_at_utc <= now < issued_at_utc + ttl_seconds", lease["freshness_rule"])
        row = lease["runners"][0]
        self.assertEqual(row["argv"], SAFE_RUNNER)
        self.assertEqual(row["exit_code"], 0)
        self.assertEqual(len(row["stdout_sha256"]), 64)
        self.assertEqual(len(row["stderr_sha256"]), 64)
        self.assertEqual(lease["lease_sha256"], lease_digest(lease))

    def test_output_digest_records_what_the_runner_actually_printed(self) -> None:
        self.repo.stage("payload.txt", "SAFE\n")
        quiet = issue_lease(
            self.repo.root,
            [[sys.executable, "-c", "pass"]],
            ttl_seconds=TTL,
            now=NOW,
        )
        loud = issue_lease(
            self.repo.root,
            [[sys.executable, "-c", "print('output')"]],
            ttl_seconds=TTL,
            now=NOW,
        )
        self.assertNotEqual(
            quiet["runners"][0]["stdout_sha256"], loud["runners"][0]["stdout_sha256"]
        )

    def test_every_declared_runner_is_recorded(self) -> None:
        self.repo.stage("payload.txt", "SAFE\n")
        lease = issue_lease(
            self.repo.root,
            [SAFE_RUNNER, [sys.executable, "-c", "pass"]],
            ttl_seconds=TTL,
            now=NOW,
        )
        self.assertEqual(len(lease["runners"]), 2)
        self.assertEqual([row["exit_code"] for row in lease["runners"]], [0, 0])


class FreshnessTests(LeaseTestCase):
    """Requirement 2/3: the stated freshness rule, enforced."""

    def setUp(self) -> None:
        super().setUp()
        self.tree = self.repo.stage("payload.txt", "SAFE\n")
        self.lease = self.issue_safe_lease()

    def test_valid_inside_the_window(self) -> None:
        inside = NOW + timedelta(seconds=TTL - 1)
        self.assertEqual(verify_lease(self.lease, self.tree, inside).status, VALID)

    def test_stale_exactly_at_expiry(self) -> None:
        at_expiry = NOW + timedelta(seconds=TTL)
        self.assertEqual(verify_lease(self.lease, self.tree, at_expiry).status, STALE)

    def test_stale_after_expiry(self) -> None:
        after = NOW + timedelta(seconds=TTL + 1)
        self.assertEqual(verify_lease(self.lease, self.tree, after).status, STALE)

    def test_future_dated_lease_is_stale_not_valid(self) -> None:
        before = NOW - timedelta(seconds=1)
        self.assertEqual(verify_lease(self.lease, self.tree, before).status, STALE)


class VerdictTests(LeaseTestCase):
    """Requirement 3: a verdict is a name, never a bool."""

    def test_verdict_refuses_boolean_coercion(self) -> None:
        verdict = Verdict(TREE_MISMATCH, "swapped")
        with self.assertRaises(TypeError):
            bool(verdict)
        with self.assertRaises(TypeError):
            if verdict:  # pragma: no cover - the raise is the assertion
                pass

    def test_absent_lease_is_absent(self) -> None:
        tree = self.repo.stage("payload.txt", "SAFE\n")
        self.assertEqual(verify_lease(None, tree, NOW).status, ABSENT)

    def test_missing_lease_file_is_absent(self) -> None:
        self.repo.stage("payload.txt", "SAFE\n")
        missing = Path(self.temp.name) / "nope.json"
        self.assertEqual(verify_lease_file(missing, self.repo.root, now=NOW).status, ABSENT)

    def test_verification_is_pure_and_repeatable(self) -> None:
        tree = self.repo.stage("payload.txt", "SAFE\n")
        lease = self.issue_safe_lease()
        first = verify_lease(lease, tree, NOW)
        second = verify_lease(lease, tree, NOW)
        self.assertEqual(first, second)
        self.assertEqual(first.status, VALID)


class MalformedTests(LeaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tree = self.repo.stage("payload.txt", "SAFE\n")
        self.lease = self.issue_safe_lease()

    def status_for(self, lease) -> Verdict:
        return verify_lease(lease, self.tree, NOW)

    def test_tampered_body_breaks_the_digest(self) -> None:
        tampered = dict(self.lease)
        tampered["ttl_seconds"] = TTL * 100
        self.assertEqual(self.status_for(tampered).status, MALFORMED)

    def test_recorded_failing_exit_code_is_malformed(self) -> None:
        forged = json.loads(json.dumps(self.lease))
        forged["runners"][0]["exit_code"] = 1
        forged["lease_sha256"] = lease_digest(forged)
        verdict = self.status_for(forged)
        self.assertEqual(verdict.status, MALFORMED)
        self.assertIn("exit_code 1", verdict.reason)

    def test_empty_runner_list_is_malformed(self) -> None:
        forged = json.loads(json.dumps(self.lease))
        forged["runners"] = []
        forged["lease_sha256"] = lease_digest(forged)
        self.assertEqual(self.status_for(forged).status, MALFORMED)

    def test_missing_field_is_malformed(self) -> None:
        for field in ("tree_id", "issued_at_utc", "expires_at_utc", "runners", "schema"):
            with self.subTest(field=field):
                forged = json.loads(json.dumps(self.lease))
                del forged[field]
                forged["lease_sha256"] = lease_digest(forged)
                self.assertEqual(self.status_for(forged).status, MALFORMED)

    def test_non_object_lease_is_malformed(self) -> None:
        for body in ("VALID", ["VALID"], 1, True):
            with self.subTest(body=body):
                self.assertEqual(self.status_for(body).status, MALFORMED)

    def test_unparseable_lease_file_is_malformed(self) -> None:
        path = Path(self.temp.name) / "lease.json"
        path.write_bytes(b"{not json")
        self.assertEqual(
            verify_lease_file(path, self.repo.root, now=NOW).status, MALFORMED
        )

    def test_bad_tree_id_shape_is_malformed(self) -> None:
        forged = json.loads(json.dumps(self.lease))
        forged["tree_id"] = "not-a-tree"
        forged["lease_sha256"] = lease_digest(forged)
        self.assertEqual(self.status_for(forged).status, MALFORMED)


class NoSubmittedProofTests(LeaseTestCase):
    """Requirement 4: a lease exists only if the commands really ran and passed."""

    def test_failing_runner_issues_no_lease(self) -> None:
        self.repo.stage("payload.txt", "MALICIOUS\n")
        with self.assertRaises(LeaseDenied) as caught:
            self.issue_safe_lease()
        self.assertEqual(caught.exception.runs[0]["exit_code"], 1)

    def test_unrunnable_command_issues_no_lease(self) -> None:
        self.repo.stage("payload.txt", "SAFE\n")
        with self.assertRaises(LeaseError):
            issue_lease(
                self.repo.root,
                [["constraintbox-no-such-binary-xyz"]],
                ttl_seconds=TTL,
                now=NOW,
            )

    def test_timed_out_runner_issues_no_lease(self) -> None:
        self.repo.stage("payload.txt", "SAFE\n")
        with self.assertRaises(LeaseError) as caught:
            issue_lease(
                self.repo.root,
                [[sys.executable, "-c", "import time; time.sleep(30)"]],
                ttl_seconds=TTL,
                now=NOW,
                timeout_seconds=0.5,
            )
        self.assertIn("timed out", str(caught.exception))

    def test_later_runner_failure_denies_the_whole_lease(self) -> None:
        self.repo.stage("payload.txt", "SAFE\n")
        with self.assertRaises(LeaseDenied) as caught:
            issue_lease(
                self.repo.root,
                [SAFE_RUNNER, [sys.executable, "-c", "raise SystemExit(3)"]],
                ttl_seconds=TTL,
                now=NOW,
            )
        self.assertEqual(
            [row["exit_code"] for row in caught.exception.runs], [0, 3]
        )

    def test_no_lease_is_written_when_a_runner_fails(self) -> None:
        self.repo.stage("payload.txt", "MALICIOUS\n")
        path = Path(self.temp.name) / "lease.json"
        try:
            write_lease(path, self.issue_safe_lease())
        except LeaseDenied:
            pass
        self.assertIsNone(read_lease(path))
        self.assertEqual(
            verify_lease_file(path, self.repo.root, now=NOW).status, ABSENT
        )


class ExitCodeIsTheVerdictTests(LeaseTestCase):
    """Requirement 5: no free-text verdict parsing, in either direction."""

    def test_output_saying_pass_with_nonzero_exit_is_denied(self) -> None:
        self.repo.stage("payload.txt", "SAFE\n")
        with self.assertRaises(LeaseDenied):
            issue_lease(
                self.repo.root,
                [
                    [
                        sys.executable,
                        "-c",
                        "print('PASS: all checks green'); raise SystemExit(1)",
                    ]
                ],
                ttl_seconds=TTL,
                now=NOW,
            )

    def test_output_saying_fail_with_zero_exit_is_admitted(self) -> None:
        tree = self.repo.stage("payload.txt", "SAFE\n")
        lease = issue_lease(
            self.repo.root,
            [[sys.executable, "-c", "print('FAILED: everything is broken')"]],
            ttl_seconds=TTL,
            now=NOW,
        )
        self.assertEqual(verify_lease(lease, tree, NOW).status, VALID)


class RunnerWorkspaceTests(LeaseTestCase):
    """The runner sees the staged tree, not the working tree."""

    def test_runner_reads_staged_bytes_not_working_tree_bytes(self) -> None:
        # Stage SAFE, then leave MALICIOUS in the working tree unstaged.
        self.repo.stage("payload.txt", "SAFE\n")
        self.repo.write("payload.txt", "MALICIOUS\n")
        lease = self.issue_safe_lease()
        self.assertEqual(lease["runners"][0]["exit_code"], 0)

        # Reverse it: stage MALICIOUS while the working tree reads SAFE.
        self.repo.stage("payload.txt", "MALICIOUS\n")
        self.repo.write("payload.txt", "SAFE\n")
        with self.assertRaises(LeaseDenied):
            self.issue_safe_lease()

    def test_untracked_files_are_not_visible_to_the_runner(self) -> None:
        self.repo.stage("payload.txt", "SAFE\n")
        self.repo.write("smuggled.txt", "SAFE\n")
        with self.assertRaises(LeaseDenied):
            issue_lease(
                self.repo.root,
                [["grep", "-q", "SAFE", "smuggled.txt"]],
                ttl_seconds=TTL,
                now=NOW,
            )


class RoundTripTests(LeaseTestCase):
    def test_written_lease_verifies_from_disk(self) -> None:
        self.repo.stage("payload.txt", "SAFE\n")
        path = Path(self.temp.name) / "lease.json"
        write_lease(path, self.issue_safe_lease())
        self.assertEqual(
            verify_lease_file(path, self.repo.root, now=NOW).status, VALID
        )
        self.repo.stage("payload.txt", "MALICIOUS\n")
        self.assertEqual(
            verify_lease_file(path, self.repo.root, now=NOW).status, TREE_MISMATCH
        )


if __name__ == "__main__":
    unittest.main()
