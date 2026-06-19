#!/usr/bin/env python3
"""Contract tests for retrocausal_possibility_field_carrier_grounded_v0.

Positive: the field instantiates on the real M(C) carrier, the quotient is reproduced,
the gate is earned, and constraint surgery moves the survivor.
Negative: an empty observable family collapses the earned probe.
Boundary: the canonical partition matches the deterministic rule; the global score
strictly beats forward greedy (separation is a real gap, not a tie-break).
"""

import importlib.util
import os

SIM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(SIM_DIR, "retrocausal_possibility_field_carrier_grounded_v0.py")


def _mod():
    spec = importlib.util.spec_from_file_location("rpf_cg_v0", MODULE_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_carrier_is_real_frozen_M_C_density_matrices():
    m = _mod()
    c = m.load_frozen_carrier()
    assert c["carve_survivor_count"] == 16
    assert len(c["branch_ids"]) == 16
    assert c["all_density_matrices_valid"] is True
    assert all(m.is_valid_density_matrix(m.rho_of(c, b)) for b in c["branch_ids"])
    assert c["carve_result_sha256"]


def test_observable_sign_classes_reproduce_carve_8_quotient():
    m = _mod()
    c = m.load_frozen_carrier()
    classes = m.signature_classes(c, m.PROBE_FAMILY_C)
    assert len(classes) == 8 == c["carve_quotient_class_count"]


def test_acceptance_gate_earned_and_real_gap():
    m = _mod()
    c = m.load_frozen_carrier()
    sh = m.CANONICAL_SHELLS_OUTER_TO_INNER
    gate = m.acceptance_gate(c, sh, m.PROBE_FAMILY_C)
    assert gate["retrocausal_earned"] is True
    # real gap: global strictly beats forward greedy on the co-adm pair count
    fwd = [b for _, b in m.forward_single_anchor(c, sh, m.PROBE_FAMILY_C)["path"]]
    glob = m.global_compressor(c, sh, m.PROBE_FAMILY_C)
    gassign = [glob["global_joint_assignment"][i] for i in range(3)]

    def score(a, fam):
        return sum(m.coadmissibility_overlap(c, a[i], a[j], fam)
                   for i in range(len(a)) for j in range(i + 1, len(a)))
    assert score(gassign, m.PROBE_FAMILY_C) > score(fwd, m.PROBE_FAMILY_C)


def test_HARD_constraint_surgery_moves_survivor_carrier_fixed():
    m = _mod()
    c = m.load_frozen_carrier()
    sh = m.CANONICAL_SHELLS_OUTER_TO_INNER
    surg = m.constraint_surgery_test(c, sh)
    assert surg["carrier_held_rigidly_fixed"] is True
    assert surg["coadm_relation_changed"] is True
    assert surg["constraint_surgery_moves_survivor"] is True
    assert surg["present_survivor_before"] != surg["present_survivor_after"]
    assert surg["appended_observable"] == "sigma_y"


def test_negative_empty_observable_family_collapses_probe():
    m = _mod()
    c = m.load_frozen_carrier()
    sh = m.CANONICAL_SHELLS_OUTER_TO_INNER
    ctrl = m.uniform_observable_control(c, sh)
    assert ctrl["degenerate_correctly_kills_probe"] is True
    assert ctrl["still_differs_from_forward"] is False


def test_boundary_canonical_partition_matches_deterministic_rule():
    m = _mod()
    c = m.load_frozen_carrier()
    can = m.select_canonical_partition(c)
    assert can["frozen_matches_recomputed_canonical"] is True


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
