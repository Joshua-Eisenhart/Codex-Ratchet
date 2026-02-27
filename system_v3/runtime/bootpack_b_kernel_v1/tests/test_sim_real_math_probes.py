import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from sim_engine import SimEngine, SimTask
from state import KernelState


class TestSimRealMathProbes(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SimEngine()
        self.state = KernelState()

    def test_density_matrix_probe_metrics_present(self) -> None:
        task = SimTask(
            sim_id="S000010_Z_SIM_CANON_DENSITY_MATRIX",
            spec_id="S000010_Z_SIM_CANON_DENSITY_MATRIX",
            evidence_token="E_CANON_DENSITY_MATRIX",
            tier="T0_ATOM",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=density_matrix", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: eig_min=", evidence)
        result = self.state.sim_results[task.sim_id][0]
        self.assertTrue(result["probe_pass"])
        self.assertEqual("density_matrix", result["probe_term"])

    def test_density_purity_probe_metrics_present(self) -> None:
        task = SimTask(
            sim_id="S000020_Z_SIM_CANON_DENSITY_PURITY",
            spec_id="S000020_Z_SIM_CANON_DENSITY_PURITY",
            evidence_token="E_CANON_DENSITY_PURITY",
            tier="T1_COMPOUND",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=density_purity", evidence)
        self.assertIn("METRIC: probe_name=density_purity_changes_under_cptp", evidence)
        self.assertIn("METRIC: purity_initial=", evidence)
        self.assertIn("METRIC: purity_depolarized=", evidence)
        self.assertIn("METRIC: purity_amplitude_damped=", evidence)
        result = self.state.sim_results[task.sim_id][0]
        self.assertTrue(result["probe_pass"])
        self.assertEqual("density_purity", result["probe_term"])

    def test_commutative_negative_kill_emits_when_marker_present(self) -> None:
        spec_id = "S000011_Z_SIM_ALT_NEG_COMMUTATOR_OPERATOR"
        self.state.survivor_ledger[spec_id] = {
            "class": "SPEC_HYP",
            "status": "ACTIVE",
            "item_text": "\n".join(
                [
                    f"SPEC_HYP {spec_id}",
                    f"DEF_FIELD {spec_id} CORR ASSUME_COMMUTATIVE TRUE",
                ]
            ),
            "metadata": {},
        }
        task = SimTask(
            sim_id=spec_id,
            spec_id=spec_id,
            evidence_token="E_ALT_NEG_COMMUTATOR_OPERATOR",
            tier="T1_COMPOUND",
            family="ADVERSARIAL_NEG",
            target_class="TC_QIT",
            negative_class="COMMUTATIVE_ASSUMPTION",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn(f"KILL_SIGNAL {spec_id} CORR NEG_COMMUTATIVE_ASSUMPTION", evidence)
        self.assertIn("METRIC: commutator_norm=", evidence)

    def test_commutative_negative_no_marker_no_kill(self) -> None:
        spec_id = "S000012_Z_SIM_ALT_NEG_COMMUTATOR_OPERATOR"
        self.state.survivor_ledger[spec_id] = {
            "class": "SPEC_HYP",
            "status": "ACTIVE",
            "item_text": "\n".join(
                [
                    f"SPEC_HYP {spec_id}",
                    f"DEF_FIELD {spec_id} CORR BRANCH_TRACK QIT_COMMUTATOR_OPERATOR_NEG",
                ]
            ),
            "metadata": {},
        }
        task = SimTask(
            sim_id=spec_id,
            spec_id=spec_id,
            evidence_token="E_ALT_NEG_COMMUTATOR_OPERATOR",
            tier="T1_COMPOUND",
            family="ADVERSARIAL_NEG",
            target_class="TC_QIT",
            negative_class="COMMUTATIVE_ASSUMPTION",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertNotIn("KILL_SIGNAL", evidence)

    def test_correlation_polarity_probe_emits_diversity_metrics_present(self) -> None:
        task = SimTask(
            sim_id="S000030_Z_SIM_CANON_CORRELATION_POLARITY",
            spec_id="S000030_Z_SIM_CANON_CORRELATION_POLARITY",
            evidence_token="E_CANON_CORRELATION_POLARITY",
            tier="T3_STRUCTURE",
            family="BASELINE",
            target_class="TC_AXIS0",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=correlation_polarity", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: mi2_pair_diversity_base=", evidence)
        self.assertIn("METRIC: mi2_pair_diversity_delta=", evidence)

    def test_trajectory_correlation_probe_emits_mi_metrics_present(self) -> None:
        task = SimTask(
            sim_id="S000033_Z_SIM_CANON_TRAJECTORY_CORRELATION",
            spec_id="S000033_Z_SIM_CANON_TRAJECTORY_CORRELATION",
            evidence_token="E_CANON_TRAJECTORY_CORRELATION",
            tier="T4_SYSTEM_SEGMENT",
            family="BASELINE",
            target_class="TC_AXIS0",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=trajectory_correlation", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: seq01_mi2_final_bits=", evidence)
        self.assertIn("METRIC: seq02_mi2_final_bits=", evidence)

    def test_kraus_representation_probe_emits_path_entropy_metrics_present(self) -> None:
        task = SimTask(
            sim_id="S000031_Z_SIM_CANON_KRAUS_REPRESENTATION",
            spec_id="S000031_Z_SIM_CANON_KRAUS_REPRESENTATION",
            evidence_token="E_CANON_KRAUS_REPRESENTATION",
            tier="T2_OPERATOR",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=kraus_representation", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: path_entropy_base_bits=", evidence)
        self.assertIn("METRIC: path_entropy_delta_bits=", evidence)

    def test_variance_order_probe_emits_sequence_metrics_present(self) -> None:
        task = SimTask(
            sim_id="S000032_Z_SIM_CANON_VARIANCE_ORDER",
            spec_id="S000032_Z_SIM_CANON_VARIANCE_ORDER",
            evidence_token="E_CANON_VARIANCE_ORDER",
            tier="T3_STRUCTURE",
            family="BASELINE",
            target_class="TC_AXIS4",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=variance_order", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: seq01_purity_delta=", evidence)
        self.assertIn("METRIC: seq01_entropy_delta_bits=", evidence)

    def test_channel_realization_probe_emits_edge_and_delta_metrics_present(self) -> None:
        task = SimTask(
            sim_id="S000034_Z_SIM_CANON_CHANNEL_REALIZATION",
            spec_id="S000034_Z_SIM_CANON_CHANNEL_REALIZATION",
            evidence_token="E_CANON_CHANNEL_REALIZATION",
            tier="T4_SYSTEM_SEGMENT",
            family="BASELINE",
            target_class="TC_AXIS12",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=channel_realization", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: seq01_edge_seni=", evidence)
        self.assertIn("METRIC: seq01_delta_entropy_bits_mean=", evidence)

    def test_engine_cycle_probe_emits_closure_and_sign_metrics_present(self) -> None:
        task = SimTask(
            sim_id="S000035_Z_SIM_CANON_ENGINE_CYCLE",
            spec_id="S000035_Z_SIM_CANON_ENGINE_CYCLE",
            evidence_token="E_CANON_ENGINE_CYCLE",
            tier="T5_ENGINE",
            family="BASELINE",
            target_class="TC_ENGINE",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=engine_cycle", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: plus_closure_gap=", evidence)
        self.assertIn("METRIC: minus_closure_gap=", evidence)

    def test_noncommutative_composition_order_probe_gap_nonzero(self) -> None:
        task = SimTask(
            sim_id="S000040_Z_SIM_CANON_NONCOMMUTATIVE_COMPOSITION_ORDER",
            spec_id="S000040_Z_SIM_CANON_NONCOMMUTATIVE_COMPOSITION_ORDER",
            evidence_token="E_CANON_NONCOMMUTATIVE_COMPOSITION_ORDER",
            tier="T3_STRUCTURE",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=noncommutative_composition_order", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        gap = None
        for line in evidence.splitlines():
            if line.startswith("METRIC: composition_order_gap="):
                _, raw = line.split("=", 1)
                gap = float(raw.strip())
                break
        self.assertIsNotNone(gap)
        self.assertGreater(gap, 1e-6)

    def test_pauli_operator_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000050_Z_SIM_CANON_PAULI_OPERATOR",
            spec_id="S000050_Z_SIM_CANON_PAULI_OPERATOR",
            evidence_token="E_CANON_PAULI_OPERATOR",
            tier="T2_OPERATOR",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=pauli_operator", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: commutator_norm_xz=", evidence)

    def test_right_action_superoperator_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000050_Z_SIM_CANON_RIGHT_ACTION_SUPEROPERATOR",
            spec_id="S000050_Z_SIM_CANON_RIGHT_ACTION_SUPEROPERATOR",
            evidence_token="E_CANON_RIGHT_ACTION_SUPEROPERATOR",
            tier="T2_OPERATOR",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=right_action_superoperator", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: left_right_gap=", evidence)

    def test_bloch_sphere_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000051_Z_SIM_CANON_BLOCH_SPHERE",
            spec_id="S000051_Z_SIM_CANON_BLOCH_SPHERE",
            evidence_token="E_CANON_BLOCH_SPHERE",
            tier="T3_STRUCTURE",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=bloch_sphere", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: bloch_r_norm=", evidence)

    def test_hopf_fibration_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000052_Z_SIM_CANON_HOPF_FIBRATION",
            spec_id="S000052_Z_SIM_CANON_HOPF_FIBRATION",
            evidence_token="E_CANON_HOPF_FIBRATION",
            tier="T3_STRUCTURE",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=hopf_fibration", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: density_phase_invariance_gap=", evidence)

    def test_hopf_torus_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000054_Z_SIM_CANON_HOPF_TORUS",
            spec_id="S000054_Z_SIM_CANON_HOPF_TORUS",
            evidence_token="E_CANON_HOPF_TORUS",
            tier="T4_SYSTEM_SEGMENT",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=hopf_torus", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: eta_z_gap=", evidence)

    def test_berry_flux_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000053_Z_SIM_CANON_BERRY_FLUX",
            spec_id="S000053_Z_SIM_CANON_BERRY_FLUX",
            evidence_token="E_CANON_BERRY_FLUX",
            tier="T3_STRUCTURE",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=berry_flux", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: berry_flux_plus=", evidence)

    def test_spinor_double_cover_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000055_Z_SIM_CANON_SPINOR_DOUBLE_COVER",
            spec_id="S000055_Z_SIM_CANON_SPINOR_DOUBLE_COVER",
            evidence_token="E_CANON_SPINOR_DOUBLE_COVER",
            tier="T4_SYSTEM_SEGMENT",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=spinor_double_cover", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: density_invariance_gap=", evidence)

    def test_left_weyl_spinor_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000056_Z_SIM_CANON_LEFT_WEYL_SPINOR",
            spec_id="S000056_Z_SIM_CANON_LEFT_WEYL_SPINOR",
            evidence_token="E_CANON_LEFT_WEYL_SPINOR",
            tier="T4_SYSTEM_SEGMENT",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=left_weyl_spinor", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: chirality_split_gap=", evidence)

    def test_right_weyl_spinor_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000057_Z_SIM_CANON_RIGHT_WEYL_SPINOR",
            spec_id="S000057_Z_SIM_CANON_RIGHT_WEYL_SPINOR",
            evidence_token="E_CANON_RIGHT_WEYL_SPINOR",
            tier="T4_SYSTEM_SEGMENT",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=right_weyl_spinor", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: chirality_split_gap=", evidence)

    def test_left_right_action_entropy_production_rate_orthogonality_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000058_Z_SIM_CANON_LEFT_RIGHT_ACTION_ENTROPY_PRODUCTION_RATE_ORTHOGONALITY",
            spec_id="S000058_Z_SIM_CANON_LEFT_RIGHT_ACTION_ENTROPY_PRODUCTION_RATE_ORTHOGONALITY",
            evidence_token="E_CANON_LR_ENTROPY_ORTHOGONALITY",
            tier="T4_SYSTEM_SEGMENT",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=left_right_action_entropy_production_rate_orthogonality", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: orthogonality_cosine_abs=", evidence)

    def test_variance_order_trajectory_correlation_orthogonality_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000059_Z_SIM_CANON_VARIANCE_ORDER_TRAJECTORY_CORRELATION_ORTHOGONALITY",
            spec_id="S000059_Z_SIM_CANON_VARIANCE_ORDER_TRAJECTORY_CORRELATION_ORTHOGONALITY",
            evidence_token="E_CANON_VAR_TRAJ_ORTHOGONALITY",
            tier="T4_SYSTEM_SEGMENT",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=variance_order_trajectory_correlation_orthogonality", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: orthogonality_cosine_abs=", evidence)

    def test_channel_realization_correlation_polarity_orthogonality_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000060_Z_SIM_CANON_CHANNEL_REALIZATION_CORRELATION_POLARITY_ORTHOGONALITY",
            spec_id="S000060_Z_SIM_CANON_CHANNEL_REALIZATION_CORRELATION_POLARITY_ORTHOGONALITY",
            evidence_token="E_CANON_CHAN_CORR_ORTHOGONALITY",
            tier="T4_SYSTEM_SEGMENT",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=channel_realization_correlation_polarity_orthogonality", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: orthogonality_cosine_abs=", evidence)

    def test_qit_master_conjunction_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000060_Z_SIM_MASTER_QIT_MASTER_CONJUNCTION",
            spec_id="S000060_Z_SIM_MASTER_QIT_MASTER_CONJUNCTION",
            evidence_token="E_CANON_QIT_MASTER_CONJUNCTION",
            tier="T6_WHOLE_SYSTEM",
            family="BASELINE",
            target_class="TC_QIT_MASTER",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=qit_master_conjunction", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: engine_left_entropy_gap_bits=", evidence)
        self.assertIn("METRIC: engine_right_entropy_gap_bits=", evidence)
        self.assertIn("METRIC: engine_distinct=true", evidence)

    def test_nested_constraint_manifold_compound_probe_passes(self) -> None:
        task = SimTask(
            sim_id="S000062_Z_SIM_CANON_NESTED_HOPF_TORUS_LEFT_WEYL_SPINOR_RIGHT_WEYL_SPINOR_ENGINE_CYCLE_CONSTRAINT_MANIFOLD_CONJUNCTION",
            spec_id="S000062_Z_SIM_CANON_NESTED_HOPF_TORUS_LEFT_WEYL_SPINOR_RIGHT_WEYL_SPINOR_ENGINE_CYCLE_CONSTRAINT_MANIFOLD_CONJUNCTION",
            evidence_token="E_CANON_NESTED_HOPF_TORUS_LEFT_WEYL_SPINOR_RIGHT_WEYL_SPINOR_ENGINE_CYCLE_CONSTRAINT_MANIFOLD_CONJUNCTION",
            tier="T6_WHOLE_SYSTEM",
            family="BASELINE",
            target_class="TC_QIT_MASTER",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn(
            "METRIC: probe_term=nested_hopf_torus_left_weyl_spinor_right_weyl_spinor_engine_cycle_constraint_manifold_conjunction",
            evidence,
        )
        self.assertIn("METRIC: probe_name=qit_master_conjunction_constraint_manifold_compound", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)
        self.assertIn("METRIC: engine_distinct=true", evidence)

    def test_probe_term_def_field_overrides_spec_id_for_probe_selection(self) -> None:
        spec_id = "S000061_Z_SIM_UNKNOWN_ID"
        self.state.survivor_ledger[spec_id] = {
            "class": "SPEC_HYP",
            "status": "ACTIVE",
            "item_text": "\n".join(
                [
                    f"SPEC_HYP {spec_id}",
                    f"DEF_FIELD {spec_id} CORR PROBE_TERM hopf_torus",
                ]
            ),
            "metadata": {},
        }
        task = SimTask(
            sim_id=spec_id,
            spec_id=spec_id,
            evidence_token="E_CANON_HOPF_TORUS_OVERRIDE",
            tier="T4_SYSTEM_SEGMENT",
            family="BASELINE",
            target_class="TC_QIT",
            negative_class="",
            depends_on=(),
        )
        evidence = self.engine.run_task(self.state, task)
        self.assertIn("METRIC: probe_term=hopf_torus", evidence)
        self.assertIn("METRIC: probe_pass=true", evidence)


if __name__ == "__main__":
    unittest.main()
