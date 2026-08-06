from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from constraintbox.contracts import Disposition
from constraintbox.intake import canonical_json
from constraintbox.levos_flowmind import (
    LevDnaFlowMindGraphProfile,
    _PINNED_FLOWMIND_TOPOLOGY_SHA256,
)


ROOT = Path(__file__).resolve().parents[1]
PINNED_FIXTURE = (
    ROOT
    / "fixtures"
    / "formal"
    / "levos_flowmind_dna_compile_pinned_topology_fixture.json"
)


def compiler_output() -> dict[str, object]:
    """A small non-pinned envelope for early-rejection controls."""

    return {
        "version": 1,
        "operation": {
            "id": "dna.compile",
            "service": "dna",
            "method": "compile",
            "surface": "cli",
            "request_id": "cli:dna:compile",
        },
        "side_effect": {"class": "read", "dry_run": False},
        "policy": {"decision": "allow"},
        "result": {
            "status": "ok",
            "data": {
                "path": "/external/lev/dna/core/flowmind.dna.yaml",
                "entry": "gate_compiler_not_executor",
                "nodeCount": 3,
                "executionProfileHint": {"eligible": False},
                "kellyProfileHint": {"eligible": False},
                "executionProfileAlignment": {"status": "synthetic"},
                "graph": {
                    "name": "flowmind_contract",
                    "entry": "gate_compiler_not_executor",
                    "nodes": {
                        "gate_compiler_not_executor": {
                            "description": "synthetic structural gate",
                            "eval": "this string is never evaluated by CB",
                            "branches": {"pass": "compile", "fail": "done"},
                        },
                        "compile": {
                            "description": "synthetic compiler step",
                            "op": "this string is never executed by CB",
                            "next": "done",
                        },
                        "done": {
                            "description": "synthetic terminal",
                            "terminal": True,
                        },
                    },
                },
            },
            "exit_code": 0,
        },
        "evidence": {
            "receipt_refs": [],
            "event_refs": [],
            "artifact_refs": [],
            "proof_refs": [],
        },
    }


class LevDnaFlowMindGraphProfileTests(unittest.TestCase):
    @staticmethod
    def pinned_compiler_output() -> dict[str, object]:
        """Load a non-provenance fixture of the controller-pinned topology."""

        return json.loads(PINNED_FIXTURE.read_text(encoding="utf-8"))

    def evaluate(
        self,
        body: dict[str, object],
        root: Path,
        request_id: str = "foreign-1",
    ):
        payload = canonical_json(body)
        return LevDnaFlowMindGraphProfile().evaluate(
            payload,
            root / request_id,
        ), payload

    def test_positive_output_is_retained_and_checked_by_rustworkx(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            decision, payload = self.evaluate(self.pinned_compiler_output(), root)
            self.assertEqual(decision.disposition, Disposition.ELIGIBLE)
            self.assertEqual(
                decision.reason,
                "levos_flowmind_structure_obligations_satisfied",
            )
            evidence = decision.evidence
            self.assertEqual(
                evidence["foreign_observation"]["sha256"],
                hashlib.sha256(payload).hexdigest(),
            )
            self.assertFalse(
                evidence["foreign_observation"]["producer_authenticated"]
            )
            self.assertFalse(
                evidence["foreign_observation"]["source_path_authenticated"]
            )
            self.assertEqual(evidence["foreign_system_claim"], "LevOS")
            self.assertEqual(
                evidence["workflow_graph"]["tool"]["name"],
                "rustworkx",
            )
            observation = root / "foreign-1" / "foreign_lev_dna_compile.json"
            self.assertEqual(observation.read_bytes(), payload)

    def test_non_pinned_topology_is_rejected_before_graph_execution(self) -> None:
        body = compiler_output()
        graph = body["result"]["data"]["graph"]
        graph["nodes"]["compile"]["next"] = "gate_compiler_not_executor"
        with tempfile.TemporaryDirectory() as temporary:
            decision, _ = self.evaluate(body, Path(temporary).resolve())
        self.assertEqual(decision.disposition, Disposition.BLOCKED)
        self.assertEqual(decision.reason, "levos_flowmind_topology_digest_mismatch")

    def test_missing_branch_target_is_rejected_before_graph_execution(self) -> None:
        body = compiler_output()
        graph = body["result"]["data"]["graph"]
        graph["nodes"]["gate_compiler_not_executor"]["branches"][
            "pass"
        ] = "not_declared"
        with tempfile.TemporaryDirectory() as temporary:
            decision, _ = self.evaluate(body, Path(temporary).resolve())
        self.assertEqual(decision.disposition, Disposition.BLOCKED)
        self.assertEqual(decision.reason, "levos_flowmind_branch_target_invalid")

    def test_foreign_authority_and_nonread_operation_are_rejected(self) -> None:
        authority_body = compiler_output()
        authority_body["promotion_allowed"] = True
        nonread_body = compiler_output()
        nonread_body["operation"]["id"] = "dna.validate"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            authority, _ = self.evaluate(authority_body, root, "authority")
            nonread, _ = self.evaluate(nonread_body, root, "nonread")
        self.assertEqual(authority.disposition, Disposition.BLOCKED)
        self.assertEqual(
            authority.reason,
            "levos_foreign_authority_field_present",
        )
        self.assertEqual(nonread.disposition, Disposition.BLOCKED)
        self.assertEqual(nonread.reason, "levos_dna_compile_operation_mismatch")

    def test_nonstructural_node_text_cannot_change_canonical_projection(self) -> None:
        first = self.pinned_compiler_output()
        second = copy.deepcopy(first)
        graph = second["result"]["data"]["graph"]
        node_id = sorted(graph["nodes"])[0]
        graph["nodes"][node_id]["description"] = "different text"
        graph["nodes"][node_id]["op"] = "do not run this text"
        graph["nodes"][node_id]["eval"] = "do not run this either"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            first_decision, _ = self.evaluate(first, root, "first")
            second_decision, _ = self.evaluate(second, root, "second")
        self.assertEqual(first_decision.disposition, Disposition.ELIGIBLE)
        self.assertEqual(second_decision.disposition, Disposition.ELIGIBLE)
        self.assertNotEqual(
            first_decision.evidence["foreign_observation"]["sha256"],
            second_decision.evidence["foreign_observation"]["sha256"],
        )
        self.assertEqual(
            first_decision.evidence["structural_projection"][
                "canonical_graph_sha256"
            ],
            second_decision.evidence["structural_projection"][
                "canonical_graph_sha256"
            ],
        )

    def test_default_controller_pin_rejects_a_smaller_forged_topology(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            decision, _ = self.evaluate(
                compiler_output(),
                Path(temporary).resolve(),
            )
        self.assertEqual(decision.disposition, Disposition.BLOCKED)
        self.assertEqual(decision.reason, "levos_flowmind_topology_digest_mismatch")
        self.assertEqual(
            decision.evidence["expected_canonical_graph_sha256"],
            _PINNED_FLOWMIND_TOPOLOGY_SHA256,
        )

    def test_constructor_rejects_substituted_controller_pins(self) -> None:
        with self.assertRaisesRegex(ValueError, "controller-pinned"):
            LevDnaFlowMindGraphProfile(
                expected_canonical_graph_sha256="0" * 64,
            )
        with self.assertRaisesRegex(ValueError, "controller-pinned"):
            LevDnaFlowMindGraphProfile(
                expected_workflow_graph_source_sha256="0" * 64,
            )
        with self.assertRaisesRegex(ValueError, "controller-pinned"):
            LevDnaFlowMindGraphProfile(claim_ceiling="overclaimed")

    def test_non_utf8_foreign_text_is_blocked_before_persistence(self) -> None:
        cases: list[tuple[str, dict[str, object]]] = []
        surrogate_request_id = self.pinned_compiler_output()
        surrogate_request_id["operation"]["request_id"] = chr(0xD800)
        cases.append(("surrogate-request-id", surrogate_request_id))
        surrogate_source_path = self.pinned_compiler_output()
        surrogate_source_path["result"]["data"]["path"] = chr(0xD800)
        cases.append(("surrogate-source-path", surrogate_source_path))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for request_id, body in cases:
                with self.subTest(request_id=request_id):
                    payload = json.dumps(
                        body,
                        ensure_ascii=True,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                    decision = LevDnaFlowMindGraphProfile().evaluate(
                        payload,
                        root / request_id,
                    )
                    self.assertEqual(decision.disposition, Disposition.BLOCKED)
                    self.assertEqual(
                        decision.reason,
                        "levos_dna_compile_text_not_utf8_encodable",
                    )
                    self.assertFalse((root / request_id).exists())

    def test_strict_scalar_alias_and_transition_controls_are_rejected(self) -> None:
        cases: list[tuple[str, dict[str, object], str]] = []
        dry_run_zero = compiler_output()
        dry_run_zero["side_effect"]["dry_run"] = 0
        cases.append(("dry-run-zero", dry_run_zero, "levos_dna_compile_side_effect_mismatch"))
        false_exit = compiler_output()
        false_exit["result"]["exit_code"] = False
        cases.append(("false-exit", false_exit, "levos_dna_compile_result_mismatch"))
        authority_alias = compiler_output()
        authority_alias["result"]["data"]["executionProfileHint"][
            "promotionAllowed"
        ] = True
        cases.append(
            (
                "authority-alias",
                authority_alias,
                "levos_foreign_authority_field_present",
            )
        )
        explicit_null_terminal = compiler_output()
        explicit_null_terminal["result"]["data"]["graph"]["nodes"]["done"][
            "next"
        ] = None
        cases.append(
            (
                "explicit-null-terminal",
                explicit_null_terminal,
                "levos_flowmind_next_invalid",
            )
        )
        excessive_branches = compiler_output()
        excessive_branches["result"]["data"]["graph"]["nodes"][
            "gate_compiler_not_executor"
        ]["branches"] = {f"branch-{index}": "compile" for index in range(513)}
        cases.append(
            (
                "excessive-branches",
                excessive_branches,
                "levos_flowmind_declared_edge_limit_exceeded",
            )
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for request_id, body, expected_reason in cases:
                with self.subTest(request_id=request_id):
                    decision, _ = self.evaluate(body, root, request_id)
                    self.assertEqual(decision.disposition, Disposition.BLOCKED)
                    self.assertEqual(decision.reason, expected_reason)


if __name__ == "__main__":
    unittest.main()
