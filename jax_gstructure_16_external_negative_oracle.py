#!/usr/bin/env python3
"""External negative oracle for the JAX G-structure 16-placement receipts.

This is not a promotion gate. It checks the two new G-structure JAX diagnostic
receipts from outside their row-local pass flags and verifies that targeted
corruptions are rejected.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


PLACEMENT_PATH = Path("jax_gstructure_16_placement_spin3_audit_results.json")
SELECTOR_PATH = Path("jax_gstructure_16_branch_prune_selector_audit_results.json")
OUT = Path("jax_gstructure_16_external_negative_oracle_results.json")
EPS = 1.0e-9


def close(x: float, y: float, tol: float = EPS) -> bool:
    return abs(float(x) - float(y)) <= tol


def placement_accept(d: dict[str, Any]) -> tuple[bool, list[str]]:
    fail: list[str] = []

    def need(name: str, ok: bool) -> None:
        if not ok:
            fail.append(name)

    checks = d.get("checks", {})
    candidates = d.get("candidates", {})
    spin = candidates.get("spin3_su2", {}).get("metrics", {})
    cl3 = candidates.get("cl3_jaxga", {}).get("metrics", {})
    chern = candidates.get("u1_chern", {}).get("metrics", {})
    noncomm = candidates.get("noncommuting_topology_rotors", {}).get("metrics", {})
    jvp = candidates.get("custom_jvp_retraction", {}).get("metrics", {})
    dlpack = candidates.get("dlpack_snapshot", {}).get("metrics", {})
    riemannax = candidates.get("riemannax", {}).get("metrics", {})

    need("receipt_boundaries", d.get("ran_julia") is False and d.get("ran_pytorch") is False and d.get("promotion_allowed") is False)
    need("all_public_checks_true", bool(checks) and all(bool(v) for v in checks.values()))
    need("sixteen_rows", len(d.get("rows", [])) == 16)
    need("all_rows_pass_by_checks", all(row.get("pass") and all(row.get("checks", {}).values()) for row in d.get("rows", [])))
    need("spin3_double_cover", float(spin.get("double_cover_gap", 1.0)) < 1.0e-12)
    need("spin3_rotation_det", close(spin.get("rotation_det", 0.0), 1.0, 1.0e-9))
    need("reflection_kill", float(spin.get("reflection_det", 1.0)) < 0.0)
    need("cl3_squares", cl3.get("squares") == [1.0, 1.0, 1.0])
    need("cl3_anti", float(cl3.get("max_anticommutator", 1.0)) < 1.0e-12)
    need("chern_pm", close(chern.get("c1_plus", 0.0), 1.0, 1.0e-7) and close(chern.get("c1_minus", 0.0), -1.0, 1.0e-7))
    need("noncommuting_order", float(noncomm.get("order_gap", 0.0)) > 1.0e-3 and close(noncomm.get("same_word_gap", 1.0), 0.0, 1.0e-12))
    need("custom_jvp_tangent", float(jvp.get("tangent_dot", 1.0)) < 1.0e-12 and float(jvp.get("finite_difference_gap", 1.0)) < 1.0e-4)
    need("dlpack_roundtrip", close(dlpack.get("roundtrip_gap", 1.0), 0.0, 1.0e-12))
    need("riemannax_block_recorded", riemannax.get("status") in {"ok", "blocked_missing_package"})
    return not fail, fail


def selector_accept(d: dict[str, Any]) -> tuple[bool, list[str]]:
    fail: list[str] = []

    def need(name: str, ok: bool) -> None:
        if not ok:
            fail.append(name)

    runs = d.get("runs", {})
    a = runs.get("A", {})
    b = runs.get("B", {})
    c = runs.get("C", {})
    r = runs.get("random_rate_matched", {})
    inv = runs.get("inverted", {})
    chern = d.get("chern", {})
    path_table = d.get("path_table", {})
    all16 = list(range(1, 17))
    allowed = list(range(1, 9))
    forbidden = list(range(9, 17))

    need("receipt_boundaries", d.get("ran_julia") is False and d.get("ran_pytorch") is False and d.get("promotion_allowed") is False)
    need("A_all_16", a.get("populated") == all16 and a.get("pruned") == 0)
    need("B_allowed_only", b.get("populated") == allowed and b.get("pruned", 0) > 0)
    need("C_equals_A", c.get("populated") == all16 and c.get("pruned") == 0)
    need("random_keeps_forbidden", r.get("populated") == all16 and r.get("pruned") == b.get("pruned"))
    need("inverted_forbidden_only", inv.get("populated") == forbidden and inv.get("pruned", 0) > 0)
    need("bookkeeping", all(run.get("survivors") == 4096 - run.get("pruned") for run in (a, b, c, r, inv)))
    need("norm_and_double_cover", max(float(run.get("max_norm_drift", 1.0)) for run in (a, b, c, inv)) < 1.0e-12 and max(float(run.get("max_double_cover_gap") or 0.0) for run in (a, b, c, inv)) < 1.0e-12)
    need("chern_survivors", b.get("survivor_chern_signs") == [1] and inv.get("survivor_chern_signs") == [-1])
    need("chern_measured", close(chern.get("c1_plus", 0.0), 1.0, 1.0e-7) and close(chern.get("c1_minus", 0.0), -1.0, 1.0e-7))
    need("paths_ok", path_table.get("all_pass") is True and path_table.get("all_base_horizontal") is True and path_table.get("all_fiber_density_invariant") is True)
    return not fail, fail


def corrupt_placement(d: dict[str, Any]) -> dict[str, Any]:
    d = copy.deepcopy(d)
    d["candidates"]["spin3_su2"]["metrics"]["double_cover_gap"] = 0.5
    d["AUDIT_PASS"] = True
    return d


def corrupt_selector(d: dict[str, Any]) -> dict[str, Any]:
    d = copy.deepcopy(d)
    d["runs"]["B"]["populated"] = list(range(1, 17))
    d["AUDIT_PASS"] = True
    return d


def main() -> None:
    placement = json.loads(PLACEMENT_PATH.read_text())
    selector = json.loads(SELECTOR_PATH.read_text())
    placement_ok, placement_fail = placement_accept(placement)
    selector_ok, selector_fail = selector_accept(selector)
    bad_placement_ok, bad_placement_fail = placement_accept(corrupt_placement(placement))
    bad_selector_ok, bad_selector_fail = selector_accept(corrupt_selector(selector))
    audit_pass = placement_ok and selector_ok and not bad_placement_ok and not bad_selector_ok
    result = {
        "AUDIT_PASS": audit_pass,
        "name": "jax_gstructure_16_external_negative_oracle",
        "classification": "external_negative_oracle_for_jax_gstructure_16_receipts",
        "promotion_allowed": False,
        "executed_track": "python_readonly_receipt_oracle",
        "ran_julia": False,
        "ran_pytorch": False,
        "source_receipts": [str(PLACEMENT_PATH), str(SELECTOR_PATH)],
        "placement_external_accepts_original": placement_ok,
        "selector_external_accepts_original": selector_ok,
        "placement_external_rejects_corruption": not bad_placement_ok,
        "selector_external_rejects_corruption": not bad_selector_ok,
        "failures": {
            "placement_original": placement_fail,
            "selector_original": selector_fail,
            "placement_corruption": bad_placement_fail,
            "selector_corruption": bad_selector_fail,
        },
        "blocked_consumers": [
            "official_g_structure_selection",
            "layer_stacking",
            "flux",
            "Xi/Phi0",
            "Axis0",
            "bridge",
            "basin_admission",
            "physics/gravity",
            "final_manifold_admission",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        "gstructure_external_oracle "
        f"placement={placement_ok} selector={selector_ok} "
        f"reject_corruptions={not bad_placement_ok and not bad_selector_ok} AUDIT_PASS={audit_pass}"
    )


if __name__ == "__main__":
    main()
