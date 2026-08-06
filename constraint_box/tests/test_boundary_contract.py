from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from constraintbox.boundary_contract import (
    BoundaryContractProfile,
    EXTERNAL_SIM_PROFILE_IDS,
    TASK_BOUNDARY_CONTRACT,
    controller_boundary_context,
)
from constraintbox.contracts import Disposition
from constraintbox.formal_flow import FORMAL_FLOW_LEDGER, FORMAL_FLOW_RECEIPT
from constraintbox.formal_registry import run_formal_task


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "formal"


class BoundaryContractProfileTests(unittest.TestCase):
    def test_controller_context_names_role_boundary_without_authority(self) -> None:
        context = controller_boundary_context()
        self.assertIn("cb:* IDs", context)
        self.assertIn("sim:* IDs", context)
        self.assertIn("free prose has no", context)

    def test_valid_contract_is_eligible_through_the_actual_formal_minilev_flow(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary).resolve()
            decision = run_formal_task(
                task_kind=TASK_BOUNDARY_CONTRACT,
                request_id="boundary-valid",
                payload=(FIXTURES / "boundary_contract_valid.json").read_bytes(),
                run_root=run_root,
            )
            receipt = json.loads(
                (run_root / FORMAL_FLOW_RECEIPT).read_text(encoding="utf-8")
            )
            self.assertTrue((run_root / FORMAL_FLOW_LEDGER).is_file())

        self.assertEqual(decision.disposition, Disposition.ELIGIBLE)
        self.assertEqual(decision.reason, "boundary_contract_roles_separated")
        self.assertEqual(
            decision.evidence["scope_solver"]["z3"], "BOUNDED_SAT"
        )
        self.assertEqual(
            decision.evidence["scope_solver"]["cvc5"], "BOUNDED_SAT"
        )
        self.assertEqual(
            decision.evidence["scope_solver"]["enumeration"], "BOUNDED_SAT"
        )
        matrix = decision.evidence["controller_role_matrix"]
        self.assertEqual(
            matrix["EXTERNAL_SIM_OPERATION_PROFILES"],
            list(EXTERNAL_SIM_PROFILE_IDS),
        )
        self.assertFalse(matrix["bundle_contains_external_sim_engines"])
        self.assertEqual(receipt["terminal"], "ELIGIBLE")

    def test_observed_flat_tool_list_regression_is_blocked_by_all_deciders(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary).resolve()
            decision = run_formal_task(
                task_kind=TASK_BOUNDARY_CONTRACT,
                request_id="boundary-conflated",
                payload=(
                    FIXTURES
                    / "boundary_contract_conflated_sim_as_cb_core.json"
                ).read_bytes(),
                run_root=run_root,
            )
            receipt = json.loads(
                (run_root / FORMAL_FLOW_RECEIPT).read_text(encoding="utf-8")
            )

        self.assertEqual(decision.disposition, Disposition.BLOCKED)
        self.assertEqual(decision.reason, "boundary_role_conflation")
        self.assertTrue(
            decision.evidence["scope_flags"]["core_contains_external_sim_profile"]
        )
        self.assertTrue(
            decision.evidence["scope_flags"]["external_sim_profiles_are_cb_core"]
        )
        self.assertEqual(
            decision.evidence["scope_solver"]["z3"], "BOUNDED_UNSAT"
        )
        self.assertEqual(
            decision.evidence["scope_solver"]["cvc5"], "BOUNDED_UNSAT"
        )
        self.assertEqual(
            decision.evidence["scope_solver"]["enumeration"], "BOUNDED_UNSAT"
        )
        self.assertIn("Move every sim:* ID", decision.evidence["constraint_feedback"])
        self.assertEqual(receipt["terminal"], "BLOCKED")

    def test_unstructured_or_incomplete_claim_is_not_silently_classified(self) -> None:
        profile = BoundaryContractProfile()
        outcome = profile.evaluate(
            b'{"schema":"constraintbox.boundary-contract.v1","tools":["PyTorch"]}',
            Path("/unused"),
        )
        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "boundary_contract_invalid")
        self.assertIn("boundary_contract_keys_mismatch", outcome.evidence["errors"])
