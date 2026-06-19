#!/usr/bin/env python3
"""Validator for rpf_v5_broader_irreducibility."""

from __future__ import annotations

import importlib.util
import json
import os
import sys


SIM_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_PATH = os.path.join(SIM_DIR, "rpf_v5_broader_irreducibility.py")


def _mod():
    spec = importlib.util.spec_from_file_location("rpf_v5", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def main() -> int:
    m = _mod()
    result = m.build_result(restarts=8, max_iter=220)
    errors: list[str] = []

    if result["classification"] != "scratch_diagnostic":
        errors.append("classification is not scratch_diagnostic")
    if result["promotion_allowed"] is not False:
        errors.append("promotion_allowed must be false")
    if result["formal_admission_allowed"] is not False:
        errors.append("formal_admission_allowed must be false")
    if not result["negative_controls_pass"]:
        errors.append("negative controls did not fit at tv~0")
    if not result["all_invariants_hold"]:
        errors.append("invariants failed")

    toy = result["cases"]["toy_v3_global"]["stochastic_hmm_fit"]
    grounded = result["cases"]["grounded_M_C_global"]["stochastic_hmm_fit"]
    if max(toy["hidden_state_counts"]) != 2 * result["measured_N_f"]["toy_v3"]["N_f"]:
        errors.append("toy sweep did not reach 2*N_f")
    if max(grounded["hidden_state_counts"]) != 2 * result["measured_N_f"]["grounded_M_C"]["N_f"]:
        errors.append("grounded sweep did not reach 2*N_f")

    ok = not errors
    print(json.dumps({
        "ok": ok,
        "errors": errors,
        "toy_tv": toy["tv_infimum_estimate"],
        "grounded_tv": grounded["tv_infimum_estimate"],
        "status": result["strong_retrocausal_global_claim_status"],
    }, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
