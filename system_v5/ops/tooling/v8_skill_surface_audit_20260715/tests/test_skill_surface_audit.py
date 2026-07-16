#!/usr/bin/env python3
"""Focused tests for deterministic skill-surface inventory and red-gap binding."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
REPO_ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))

from audit_skill_surface import build_audit  # noqa: E402
from run_mutation_tests import MUTATIONS  # noqa: E402
from validate_skill_surface import validate_document  # noqa: E402


class SkillSurfaceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = build_audit(
            repo_root=REPO_ROOT,
            codex_root=Path("/Users/joshuaeisenhart/.codex/skills"),
            agents_root=Path("/Users/joshuaeisenhart/.agents/skills"),
            observed_at_utc="2026-07-15T00:00:00Z",
        )

    def test_live_document_validates(self) -> None:
        self.assertEqual(validate_document(copy.deepcopy(self.document)), [])

    def test_known_red_boundaries_are_preserved(self) -> None:
        summary = self.document["summary"]
        self.assertEqual(summary["missing_repo_source"], [])
        self.assertEqual(summary["candidate_not_installed"], ["claude-bridge"])
        self.assertEqual(summary["repo_codex_body_drift"], ["claude-bridge"])
        self.assertIn("codex-ratchet-sim-audit-spine", summary["exact_repo_codex_body_parity"])
        self.assertIn("codex-ratchet-deep-stack-stress", summary["exact_repo_codex_body_parity"])
        self.assertFalse(self.document["verdict"]["operational_surface_ready"])

    def test_narrow_normalization_is_only_for_engine_preamble(self) -> None:
        normalized = self.document["summary"]["normalized_repo_codex_body_parity"]
        self.assertEqual(
            normalized,
            ["jax-sim", "julia-sim", "pytorch-sim", "sim-stack-maintenance", "three-engine-sim"],
        )
        self.assertNotIn("codex-ratchet-deep-stack-stress", self.document["summary"]["repo_codex_body_drift"])

    def test_every_negative_mutation_is_rejected(self) -> None:
        for case_id, mutator in MUTATIONS:
            with self.subTest(case_id=case_id):
                candidate = copy.deepcopy(self.document)
                mutator(candidate)
                self.assertTrue(validate_document(candidate))


if __name__ == "__main__":
    unittest.main()
