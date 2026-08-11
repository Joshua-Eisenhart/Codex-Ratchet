"""Tests for gate operations and execution receipts (operationalism).

A gate is defined by the operation it performs. No execution receipt = no gate.
These tests verify that each gate ID produces a GateExecution with input_sha256,
output_sha256, and enumerated verdict.
"""

import unittest
from pathlib import Path

from constraintbox.gate_operations import (
    GateExecution,
    gate_boundary_contract,
    gate_cvc5_request,
    gate_rustworkx_workflow,
    gate_sympy_exact,
    gate_maude_transition,
    gate_z3_request,
)
from constraintbox.mini_levos import FlowNode, FlowPolicy, FlowTransition, HookSignal
from constraintbox.intake import canonical_json


class TestGateOperationStructure(unittest.TestCase):
    """Verify gate operations produce well-formed execution receipts."""

    def test_gate_execution_is_frozen_dataclass(self) -> None:
        """GateExecution must be immutable."""
        exc = GateExecution(
            gate_id="test:gate",
            input_sha256="a" * 64,
            output_sha256="b" * 64,
            verdict="PASS",
            reason="test",
        )
        self.assertEqual(exc.gate_id, "test:gate")
        # Verify frozen (immutable)
        with self.assertRaises(AttributeError):
            exc.verdict = "FAIL"  # type: ignore

    def test_gate_execution_sha256_lengths(self) -> None:
        """SHA256 hashes must be exactly 64 hex characters."""
        exc = GateExecution(
            gate_id="test:gate",
            input_sha256="a" * 64,
            output_sha256="b" * 64,
            verdict="PASS",
            reason="test",
        )
        self.assertEqual(len(exc.input_sha256), 64)
        self.assertEqual(len(exc.output_sha256), 64)
        # Verify they are hex
        int(exc.input_sha256, 16)
        int(exc.output_sha256, 16)


class TestGateZ3Request(unittest.TestCase):
    """Test z3 gate operation."""

    def test_z3_gate_simple_spec(self) -> None:
        """Z3 gate should execute on a simple finite constraint problem."""
        spec = {
            "variables": {"x": [0, 1, 2]},
            "constraints": [
                {"op": "eq", "left": {"var": "x"}, "right": {"const": 1}}
            ],
        }
        result = gate_z3_request(spec)

        self.assertEqual(result.gate_id, "cb:z3-request-gate")
        self.assertEqual(len(result.input_sha256), 64)
        self.assertEqual(len(result.output_sha256), 64)
        self.assertIn(
            result.verdict,
            ["BOUNDED_SAT", "BOUNDED_UNSAT", "UNKNOWN"]
        )

    def test_z3_gate_input_output_differ(self) -> None:
        """Z3 gate input and output hashes should differ."""
        spec = {
            "variables": {"x": [0, 1]},
            "constraints": [
                {"op": "eq", "left": {"var": "x"}, "right": {"const": 0}}
            ],
        }
        result = gate_z3_request(spec)
        # Input is the spec, output is the result
        self.assertNotEqual(result.input_sha256, result.output_sha256)

    def test_z3_gate_malformed_spec(self) -> None:
        """Z3 gate should handle malformed specs gracefully."""
        bad_spec = {"malformed": "spec"}
        result = gate_z3_request(bad_spec)

        self.assertEqual(result.gate_id, "cb:z3-request-gate")
        self.assertEqual(result.verdict, "UNKNOWN")
        self.assertIn("error", result.reason.lower())


class TestGateCvc5Request(unittest.TestCase):
    """Test cvc5 gate operation."""

    def test_cvc5_gate_simple_spec(self) -> None:
        """CVC5 gate should execute on a simple finite constraint problem."""
        spec = {
            "variables": {"x": [0, 1, 2]},
            "constraints": [
                {"op": "eq", "left": {"var": "x"}, "right": {"const": 1}}
            ],
        }
        result = gate_cvc5_request(spec)

        self.assertEqual(result.gate_id, "cb:cvc5-request-gate")
        self.assertEqual(len(result.input_sha256), 64)
        self.assertEqual(len(result.output_sha256), 64)
        self.assertIn(
            result.verdict,
            ["BOUNDED_SAT", "BOUNDED_UNSAT", "UNKNOWN"]
        )


class TestGateRustworkxWorkflow(unittest.TestCase):
    """Test rustworkx gate operation."""

    def test_rustworkx_gate_requires_flow_policy(self) -> None:
        """Rustworkx gate should fail gracefully on non-FlowPolicy input."""
        result = gate_rustworkx_workflow(None)

        self.assertEqual(result.gate_id, "cb:rustworkx-workflow-gate")
        self.assertEqual(result.verdict, "FAILED")
        self.assertIn("invalid", result.reason.lower())

    def test_rustworkx_gate_distinguishes_cycle_and_unreachable_controls(self) -> None:
        common = dict(
            flow_id="test-flow",
            entry_node="a",
            terminal_nodes=("HOLD",),
            required_nodes=(),
            max_steps=10,
            max_visits_per_node=2,
            max_retries=1,
            max_context_bytes=100,
            max_event_bytes=100,
            max_receipt_bytes=100,
            claim_ceiling="test",
        )
        cyclic = FlowPolicy(
            nodes=(FlowNode("a", "hook"), FlowNode("b", "hook")),
            transitions=(
                FlowTransition("a", HookSignal.PASS, "b"),
                FlowTransition("b", HookSignal.PASS, "a"),
            ),
            **common,
        )
        unreachable = FlowPolicy(
            nodes=(FlowNode("a", "hook"), FlowNode("b", "hook")),
            transitions=(FlowTransition("a", HookSignal.PASS, "HOLD"),),
            **common,
        )
        valid = FlowPolicy(
            nodes=(FlowNode("a", "hook"), FlowNode("b", "hook")),
            transitions=(
                FlowTransition("a", HookSignal.PASS, "b"),
                FlowTransition("b", HookSignal.PASS, "HOLD"),
            ),
            **common,
        )

        cycle_result = gate_rustworkx_workflow(cyclic)
        unreachable_result = gate_rustworkx_workflow(unreachable)
        valid_result = gate_rustworkx_workflow(valid)

        self.assertEqual(valid_result.verdict, "ACYCLIC_REACHABLE")
        self.assertEqual(valid_result.reason, "rustworkx_acyclic_and_reachable")
        self.assertEqual(cycle_result.verdict, "CYCLIC")
        self.assertEqual(cycle_result.reason, "cycle_detected")
        self.assertEqual(unreachable_result.verdict, "UNREACHABLE")
        self.assertEqual(unreachable_result.reason, "unreachable_node")


class TestGateSympyExact(unittest.TestCase):
    """Test sympy gate operation."""

    def test_sympy_gate_declaration_only(self) -> None:
        """Sympy gate is declaration-only; returns HOLD."""
        spec = {"arithmetic": "verification"}
        result = gate_sympy_exact(spec)

        self.assertEqual(result.gate_id, "cb:sympy-exact-gate")
        self.assertEqual(result.verdict, "HOLD")
        self.assertIn("not_wired", result.reason)

    def test_sympy_gate_produces_receipt(self) -> None:
        """Sympy gate must produce a valid execution receipt."""
        spec = {}
        result = gate_sympy_exact(spec)

        self.assertEqual(len(result.input_sha256), 64)
        self.assertEqual(len(result.output_sha256), 64)
        self.assertIsNotNone(result.reason)


class TestGateMaudeTransition(unittest.TestCase):
    """Test maude gate operation."""

    def test_maude_gate_declaration_only(self) -> None:
        """Maude gate is declaration-only; returns HOLD."""
        spec = {"transitions": "verification"}
        result = gate_maude_transition(spec)

        self.assertEqual(result.gate_id, "cb:maude-transition-gate")
        self.assertEqual(result.verdict, "HOLD")
        self.assertIn("not_wired", result.reason)


class TestGateBoundaryContract(unittest.TestCase):
    """Test boundary contract gate operation."""

    def test_boundary_contract_gate_malformed_payload(self) -> None:
        """Boundary contract gate should handle malformed payloads."""
        bad_payload = b"not json"
        result = gate_boundary_contract(bad_payload)

        self.assertEqual(result.gate_id, "cb:boundary-contract-gate")
        self.assertEqual(result.verdict, "FAIL")
        self.assertEqual(result.reason, "boundary_contract_intake_failed")

    def test_boundary_contract_gate_produces_receipt(self) -> None:
        """Boundary contract gate must produce a valid execution receipt."""
        payload = canonical_json({})
        result = gate_boundary_contract(payload)

        self.assertEqual(len(result.input_sha256), 64)
        self.assertEqual(len(result.output_sha256), 64)
        self.assertNotEqual(result.input_sha256, result.output_sha256)


class TestGateOperationalismPrinciples(unittest.TestCase):
    """Verify gates follow operationalism: gate = execution."""

    def test_all_gates_produce_input_output_hashes(self) -> None:
        """Every gate must produce input_sha256 and output_sha256."""
        # Test each gate
        spec = {"variables": {"x": [0, 1]}, "constraints": []}
        gates_tested = [
            gate_z3_request(spec),
            gate_cvc5_request(spec),
            gate_sympy_exact(spec),
            gate_maude_transition(spec),
            gate_boundary_contract(canonical_json({})),
        ]

        for gate_exec in gates_tested:
            self.assertEqual(len(gate_exec.input_sha256), 64)
            self.assertEqual(len(gate_exec.output_sha256), 64)

    def test_gate_verdict_is_enumerated(self) -> None:
        """Gate verdicts must be enumerated values, not prose."""
        spec = {"variables": {"x": [0, 1]}, "constraints": []}
        result = gate_z3_request(spec)

        # Verdict should be a short identifier, not prose
        self.assertIsInstance(result.verdict, str)
        self.assertLess(len(result.verdict), 50)
        # Should not contain prose markers
        self.assertNotIn("please", result.verdict.lower())
        self.assertNotIn("should", result.verdict.lower())

    def test_reason_is_commentary_only(self) -> None:
        """Reason field is commentary; verdict carries the decision."""
        spec = {"variables": {"x": [0, 1]}, "constraints": []}
        result = gate_z3_request(spec)

        # Reason is for human explanation
        self.assertIsInstance(result.reason, str)
        # Verdict is what's checked, not reason
        self.assertIn(result.verdict, ["BOUNDED_SAT", "BOUNDED_UNSAT", "UNKNOWN"])


if __name__ == "__main__":
    unittest.main()
