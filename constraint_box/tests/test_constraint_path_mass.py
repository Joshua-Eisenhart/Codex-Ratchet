from __future__ import annotations

import importlib
import os
from dataclasses import replace
import hashlib
from pathlib import Path
import tempfile
import unittest

from constraintbox.bound_quotient import decide_bound_packet
from constraintbox.constraint_path_mass import (
    ConstraintPathMassRequest,
    DEFAULT_PROBES,
    OPERATION,
    PathMassError,
    PathMassLimits,
    _bound_packet,
    enumerate_policy_paths,
    fixture_material_from_policy,
    module_imports_jax_at_top_level,
    reference_allowed_signals,
    reference_fixture_material,
    reference_flow_policy,
    replay_receipt,
    run_constraint_path_mass,
    write_receipt,
)
from constraintbox.constraint_path_mass import HookSignal


class ConstraintPathMassTests(unittest.TestCase):
    def test_fixture_matches_live_reference_policy(self) -> None:
        from constraintbox.proposal_minilev_flow import (
            reference_allowed_signals as live_allowed_signals,
            reference_flow_policy as live_flow_policy,
        )

        live = fixture_material_from_policy(
            live_flow_policy(), live_allowed_signals()
        )
        fixture = reference_fixture_material()
        self.assertEqual(fixture["policy"], live["policy"])
        self.assertEqual(fixture["allowed_signals"], live["allowed_signals"])
        source = Path(__file__).parents[1] / "src" / "constraintbox" / "proposal_minilev_flow.py"
        self.assertEqual(
            fixture["provenance"]["source_sha256"],
            hashlib.sha256(source.read_bytes()).hexdigest(),
        )

    def test_module_does_not_import_jax_at_top_level(self) -> None:
        self.assertFalse(module_imports_jax_at_top_level())

    def test_allowed_signals_are_real_policy_transitions(self) -> None:
        policy = reference_flow_policy()
        allowed = reference_allowed_signals()
        present = {
            (transition.from_node, transition.signal)
            for transition in policy.transitions
        }
        for node, signals in allowed.items():
            self.assertTrue(signals)
            for signal in signals:
                self.assertIn((node, signal), present)
        self.assertNotIn(
            HookSignal.HOLD, allowed["topology-preflight"]
        )

    def test_enumeration_is_finite_and_includes_released_and_blocked(self) -> None:
        paths = enumerate_policy_paths(reference_flow_policy())
        terminals = {path["observation"]["terminal"] for path in paths}
        self.assertGreaterEqual(len(paths), 8)
        self.assertLessEqual(len(paths), 32)
        self.assertIn("RELEASED", terminals)
        self.assertIn("BLOCKED", terminals)
        self.assertIn("PARKED", terminals)
        ids = [path["id"] for path in paths]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(set(ids)), len(ids))

    def test_bound_table_is_complete_and_missing_row_holds(self) -> None:
        paths = enumerate_policy_paths(reference_flow_policy())
        packet = _bound_packet(paths, DEFAULT_PROBES, "complete")
        receipt = decide_bound_packet(packet)
        self.assertEqual(receipt["status"], "PASS")
        incomplete = dict(packet)
        incomplete["rows"] = list(packet["rows"][:-1])
        held = decide_bound_packet(incomplete)
        self.assertEqual(held["status"], "HOLD")
        self.assertFalse(held["quotient_admitted"])

    def test_operation_receipt_is_honest_and_smt_writes_disposition(self) -> None:
        receipt = run_constraint_path_mass()
        self.assertEqual(receipt["operation"], OPERATION)
        self.assertFalse(receipt["promotion_allowed"])
        self.assertIn("attractor_basin", receipt["not"])
        self.assertIn("spinor_memory_geometry", receipt["not"])
        self.assertEqual(receipt["status"], "PASS")

        masses = receipt["baseline"]["mass"]
        self.assertTrue(masses)
        total = sum(
            item["mu_numerator"] / item["mu_denominator"] for item in masses
        )
        self.assertAlmostEqual(total, 1.0)
        self.assertEqual(
            sum(item["size"] for item in masses), receipt["baseline"]["n_paths"]
        )

        by_id = {item["mutation"]["id"]: item for item in receipt["mutations"]}
        self.assertIn("remove_repair", by_id)
        self.assertLess(
            by_id["remove_repair"]["n_paths"], receipt["baseline"]["n_paths"]
        )
        self.assertTrue(by_id["remove_repair"]["changes_entropy"])
        self.assertTrue(by_id["remove_repair"]["changes_topology"])
        self.assertTrue(by_id["restrict_probes_to_terminal"]["changes_entropy"])
        self.assertFalse(by_id["restrict_probes_to_terminal"]["changes_topology"])
        self.assertTrue(by_id["erase_release"]["changes_entropy"])
        self.assertTrue(by_id["erase_release"]["changes_topology"])
        self.assertLess(
            by_id["erase_release"]["entropy"]["released_count"],
            receipt["baseline"]["entropy"]["released_count"],
        )

        stored = receipt["recall"]["stored"]
        erased = receipt["recall"]["erased"]
        self.assertEqual(stored["correct"]["hash_lookup"], stored["n_paths"])
        self.assertEqual(erased["survivors"]["hash_lookup"], 0)
        self.assertEqual(erased["survivors"]["scalar_hopfield"], 0)
        self.assertEqual(erased["survivors"]["quaternion_recall"], 0)
        self.assertGreater(
            stored["correct"]["hash_lookup"], stored["correct"]["hostile_random"]
        )

        smt = receipt["smt"]
        self.assertTrue(smt["real_memory"]["agree"])
        self.assertEqual(smt["real_memory"]["z3"], "BOUNDED_SAT")
        self.assertEqual(smt["real_memory"]["cvc5"], "BOUNDED_SAT")
        self.assertEqual(smt["real_memory"]["enumeration"], "BOUNDED_SAT")
        self.assertTrue(smt["erased_memory"]["agree"])
        self.assertEqual(smt["erased_memory"]["z3"], "BOUNDED_UNSAT")
        self.assertEqual(smt["erased_memory"]["cvc5"], "BOUNDED_UNSAT")
        self.assertEqual(smt["erased_memory"]["enumeration"], "BOUNDED_UNSAT")
        disposition = receipt["disposition"]
        self.assertIsNotNone(disposition)
        self.assertEqual(disposition["admit_hash"], 1)
        self.assertEqual(disposition["admit_hostile"], 0)
        self.assertEqual(disposition["admit_same_object"], 0)
        self.assertEqual(smt["facts"]["fact_hash_exact"], 1)
        self.assertEqual(smt["facts"]["fact_erased_hash_empty"], 1)
        self.assertEqual(smt["facts"]["fact_probe_restriction_entropy_only"], 1)
        self.assertEqual(smt["facts"]["fact_some_mutation_changes_both"], 1)

        self.assertTrue(receipt["baseline"]["topology"]["agree"])
        self.assertFalse(receipt["baseline"]["topology"]["is_dag"])
        self.assertTrue(by_id["remove_repair"]["topology"]["is_dag"])

    def test_imported_module_has_no_jax_binding(self) -> None:
        module = importlib.import_module("constraintbox.constraint_path_mass")
        self.assertNotIn("jax", module.__dict__)

    def test_request_is_typed_and_bounded(self) -> None:
        with self.assertRaises(PathMassError):
            ConstraintPathMassRequest(probes=("not-a-probe",))
        with self.assertRaises(PathMassError):
            ConstraintPathMassRequest(
                limits=PathMassLimits(max_paths=1_025)
            )
        with self.assertRaises(PathMassError):
            run_constraint_path_mass({})  # type: ignore[arg-type]

    def test_foreign_policy_is_refused(self) -> None:
        foreign = replace(reference_flow_policy(), flow_id="foreign-flow")
        with self.assertRaises(PathMassError):
            enumerate_policy_paths(foreign, reference_allowed_signals())

    def test_reason_specific_negative_controls_are_real(self) -> None:
        receipt = run_constraint_path_mass()
        controls = {item["id"]: item for item in receipt["negative_controls"]}
        self.assertEqual(controls["missing_observation_row"]["status"], "HOLD")
        self.assertEqual(
            controls["missing_observation_row"]["reason_code"],
            "REFUSE_UNBOUND_OBSERVATION",
        )
        self.assertEqual(controls["unknown_probe_request"]["status"], "REFUSE")
        self.assertEqual(controls["foreign_policy_request"]["status"], "REFUSE")

    def test_external_jax_crossing_is_declared_and_hashed(self) -> None:
        interpreter_value = os.environ.get("CB_JAX_PYTHON")
        if not interpreter_value:
            self.skipTest("CB_JAX_PYTHON is not declared")
        interpreter = Path(interpreter_value)
        if not interpreter.is_file():
            self.skipTest("declared JAX interpreter is unavailable")
        receipt = run_constraint_path_mass(
            ConstraintPathMassRequest(
                jax_interpreter=interpreter,
                require_jax=True,
            )
        )
        self.assertEqual(receipt["status"], "PASS")
        crossing = receipt["jax_crossing"]
        self.assertEqual(crossing["status"], "PASS")
        self.assertTrue(crossing["declared"])
        for key in ("source_sha256", "runtime_sha256", "interpreter_sha256"):
            self.assertRegex(crossing[key], r"^[0-9a-f]{64}$")
        self.assertTrue(crossing["hopfield_agree"])
        self.assertTrue(crossing["quaternion_agree"])

    def test_receipt_replays_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.subTest("temporary receipt"):
                path = Path(directory) / "receipt.json"
                receipt = write_receipt(path)
                replay = replay_receipt(path)
                self.assertEqual(replay["status"], "PASS")
                self.assertEqual(
                    replay["stored_receipt_sha256"], receipt["receipt_sha256"]
                )


if __name__ == "__main__":
    unittest.main()
