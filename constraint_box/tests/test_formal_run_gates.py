"""Run-path formal gates (G1 wiring): cb:sympy-exact-gate and
cb:maude-transition-gate executed against the REAL proposal FlowPolicy.

These tests exercise the actual operations — sympy exact budget arithmetic
and per-transition Maude rewrite observation — on the same FlowPolicy that
``run_proposal_minilev_flow`` executes, plus negative controls built from
deliberately inconsistent policies.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from constraintbox.agentrun import _run_formal_run_path_gates
from constraintbox.gate_operations import (
    gate_maude_flow_transitions,
    gate_sympy_flow_budgets,
    run_formal_flow_gates,
)
from constraintbox.mini_levos import (
    FlowNode,
    FlowPolicy,
    FlowTransition,
    HookSignal,
)
from constraintbox.proposal_minilev_flow import (
    FLOW_ID,
    reference_flow_policy,
)


def _toy_policy(
    *,
    nodes: tuple[FlowNode, ...],
    transitions: tuple[FlowTransition, ...],
    entry_node: str,
    max_steps: int,
    max_retries: int = 0,
) -> FlowPolicy:
    return FlowPolicy(
        flow_id="test.formal-gates.toy.v1",
        entry_node=entry_node,
        nodes=nodes,
        transitions=transitions,
        terminal_nodes=("RELEASED", "BLOCKED", "PARKED", "HOLD"),
        required_nodes=tuple(node.node_id for node in nodes),
        max_steps=max_steps,
        max_visits_per_node=2,
        max_retries=max_retries,
        max_context_bytes=8_192,
        max_event_bytes=65_536,
        max_receipt_bytes=524_288,
        claim_ceiling="toy policy for formal gate negative controls",
        execution_lease=None,
    )


class ReferenceFlowPolicyTest(unittest.TestCase):
    def test_reference_policy_matches_run_path_shape(self) -> None:
        policy = reference_flow_policy()
        self.assertEqual(policy.flow_id, FLOW_ID)
        self.assertEqual(policy.entry_node, "topology-preflight")
        self.assertEqual(len(policy.nodes), 4)
        self.assertEqual(len(policy.transitions), 16)
        self.assertEqual(policy.max_steps, 6)
        self.assertEqual(policy.max_visits_per_node, 2)
        self.assertEqual(policy.max_retries, 1)
        self.assertIsNone(policy.execution_lease)
        self.assertEqual(
            policy.terminal_nodes, ("RELEASED", "BLOCKED", "PARKED", "HOLD")
        )


class FormalGatesOnRealPolicyTest(unittest.TestCase):
    """Both gates on the run path's own FlowPolicy (one shared execution)."""

    receipt: dict

    @classmethod
    def setUpClass(cls) -> None:
        cls.receipt = run_formal_flow_gates(reference_flow_policy())

    def test_both_gates_execute_every_time(self) -> None:
        executions = self.receipt["executions"]
        self.assertEqual(
            [execution["gate_id"] for execution in executions],
            ["cb:sympy-exact-gate", "cb:maude-transition-gate"],
        )
        for execution in executions:
            self.assertEqual(len(execution["input_sha256"]), 64)
            self.assertEqual(len(execution["output_sha256"]), 64)
        self.assertFalse(self.receipt["any_mismatch"])
        self.assertFalse(self.receipt["promotion_allowed"])

    def test_sympy_gate_exact_budget_facts(self) -> None:
        report = self.receipt["reports"]["cb:sympy-exact-gate"]
        self.assertEqual(report["verdict"], "VERIFIED")
        facts = report["exact_facts"]
        # nodes x max_visits_per_node = 4 x 2 = 8 >= max_steps = 6.
        self.assertEqual(facts["visit_capacity"], 8)
        self.assertEqual(facts["longest_linear_steps"], 4)
        self.assertEqual(facts["max_retry_cycle_steps"], 2)
        # Fully retried run: 4 + 1 x 2 = 6 = max_steps exactly.
        self.assertEqual(facts["worst_case_steps"], 6)
        self.assertEqual(facts["retry_slack"], 0)
        self.assertEqual(facts["min_steps_to_positive_terminal"], 4)
        consistency = report["consistency"]
        self.assertTrue(consistency["step_budget_reachable_by_pigeonhole"])
        self.assertTrue(
            consistency["retry_budget_exhausts_before_step_budget"]
        )
        self.assertEqual(consistency["binding_budget"], "retry_budget")
        self.assertTrue(report["sympy_crosscheck"]["agrees"])
        self.assertEqual(
            report["polynomial_profile"]["disposition"], "ELIGIBLE"
        )
        self.assertEqual(
            report["classification"]["tool_integration_depth"],
            "load_bearing",
        )

    def test_maude_gate_observes_every_transition(self) -> None:
        report = self.receipt["reports"]["cb:maude-transition-gate"]
        self.assertEqual(report["verdict"], "VERIFIED")
        self.assertEqual(report["transition_count"], 16)
        self.assertEqual(report["eligible_count"], 16)
        self.assertEqual(report["blocked_count"], 0)
        self.assertEqual(report["parked_count"], 0)
        facts = report["rewrite_relation_facts"]
        self.assertEqual(facts["non_terminal_dead_ends"], [])
        self.assertTrue(
            facts["every_node_reaches_terminal_via_confirmed_edges"]
        )
        self.assertTrue(facts["terminals_are_normal_forms"])
        # Honest classification: construction-time mini_levos checks already
        # enforce these facts, so the independent Maude re-derivation is
        # supportive, not load_bearing.
        self.assertEqual(
            report["classification"]["tool_integration_depth"],
            "supportive",
        )


class SympyGateNegativeControlTest(unittest.TestCase):
    def test_positive_terminal_beyond_step_budget_is_mismatch(self) -> None:
        # Three hops to the only positive terminal, but max_steps = 2.
        policy = _toy_policy(
            nodes=(
                FlowNode("a", "hook-a"),
                FlowNode("b", "hook-b"),
                FlowNode("c", "hook-c"),
            ),
            transitions=(
                FlowTransition("a", HookSignal.PASS, "b"),
                FlowTransition("a", HookSignal.HOLD, "HOLD"),
                FlowTransition("b", HookSignal.PASS, "c"),
                FlowTransition("b", HookSignal.HOLD, "HOLD"),
                FlowTransition("c", HookSignal.PASS, "RELEASED"),
                FlowTransition("c", HookSignal.HOLD, "HOLD"),
            ),
            entry_node="a",
            max_steps=2,
        )
        execution = gate_sympy_flow_budgets(policy)
        self.assertEqual(execution.gate_id, "cb:sympy-exact-gate")
        self.assertEqual(execution.verdict, "MISMATCH")
        self.assertEqual(
            execution.reason,
            "positive_terminal_unreachable_within_step_budget",
        )

    def test_non_flow_policy_input_is_mismatch(self) -> None:
        execution = gate_sympy_flow_budgets({"not": "a policy"})
        self.assertEqual(execution.verdict, "MISMATCH")
        self.assertEqual(execution.reason, "input_is_not_a_flow_policy")


class MaudeGateNegativeControlTest(unittest.TestCase):
    def test_dead_end_node_is_mismatch(self) -> None:
        # "zombie" is a declared node with no transitions at all: the Maude
        # rewrite system confirms edges only for a and b, so zombie is a
        # non-terminal dead end in the confirmed relation.
        policy = _toy_policy(
            nodes=(
                FlowNode("a", "hook-a"),
                FlowNode("b", "hook-b"),
                FlowNode("zombie", "hook-z"),
            ),
            transitions=(
                FlowTransition("a", HookSignal.PASS, "b"),
                FlowTransition("b", HookSignal.HOLD, "HOLD"),
            ),
            entry_node="a",
            max_steps=3,
        )
        execution = gate_maude_flow_transitions(policy)
        self.assertEqual(execution.gate_id, "cb:maude-transition-gate")
        self.assertEqual(execution.verdict, "MISMATCH")
        self.assertEqual(
            execution.reason,
            "confirmed_rewrite_relation_has_unreachable_terminal",
        )

    def test_non_flow_policy_input_is_mismatch(self) -> None:
        execution = gate_maude_flow_transitions(["not", "a", "policy"])
        self.assertEqual(execution.verdict, "MISMATCH")
        self.assertEqual(execution.reason, "input_is_not_a_flow_policy")


class AgentRunFormalGatesWiringTest(unittest.TestCase):
    def test_run_path_helper_persists_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw)
            receipt = _run_formal_run_path_gates(run_dir)
            written = json.loads(
                (run_dir / "formal_gates_receipt.json").read_text()
            )
        self.assertEqual(
            written["schema"], "constraintbox.formal-run-gates.v1"
        )
        self.assertEqual(
            [execution["gate_id"] for execution in written["executions"]],
            ["cb:sympy-exact-gate", "cb:maude-transition-gate"],
        )
        self.assertEqual(receipt["any_mismatch"], written["any_mismatch"])
        self.assertFalse(written["promotion_allowed"])


if __name__ == "__main__":
    unittest.main()
