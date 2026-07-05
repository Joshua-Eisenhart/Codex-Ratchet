#!/usr/bin/env python3
"""NumPy oracle/control leg for ratchet_climb_engine_v1_drive."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import ratchet_climb_core as core

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "control-only finite matrix equality oracle plus Axis-0 drive parity baseline",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing non-definitional contextuality UNSAT/SAT bias-check flip",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent second solver for the same contextuality flip",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive run orchestration and receipt JSON emission",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def numpy_observables() -> dict[str, object]:
    formal = core.load_formal_result("numpy")
    carrier = core.source_carrier(formal)
    matrix = np.asarray([row["pvec"] for row in carrier["states"]], dtype=float)
    eq = np.all(np.isclose(matrix[:, None, :], matrix[None, :, :], atol=1e-12, rtol=0.0), axis=2)
    coarse_idx = carrier["pauli_labels"].index("ZII")
    coarse = np.rint(matrix[:, coarse_idx])
    coarse_eq = coarse[:, None] == coarse[None, :]
    return {
        "full_equality_true_count": int(np.sum(eq)),
        "coarse_equality_true_count": int(np.sum(coarse_eq)),
        "full_singleton_classes_measured": int(np.sum(eq)) == matrix.shape[0],
        "coarse_merges_measured": int(np.sum(coarse_eq)) > matrix.shape[0],
    }


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    spec = core.load_spec()
    obs = numpy_observables()
    runs = [core.run_climb("numpy", cfg, {"numpy_oracle_observables": obs}) for cfg in spec["drive_variants"]]
    payload = core.result_envelope(
        "numpy",
        runs,
        {
            "source_path": core.rel(Path(__file__)),
            "source_sha256": core.sha256_file(Path(__file__)),
            "packages_used": ["numpy", "z3", "cvc5", "python_stdlib"],
            "aligned_packages_load_bearing": ["z3", "cvc5"],
            "package_observables": {
                "numpy": "control-only full/coarse equality matrix oracle",
                "z3": "Peres-Mermin non-definitional UNSAT/SAT flip",
                "cvc5": "second-solver Peres-Mermin non-definitional UNSAT/SAT flip",
            },
            "control_only_tools": ["numpy"],
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        },
    )
    out = RESULTS / "ratchet_climb_engine_v1_drive_numpy_results.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"result_path": str(out), "all_pass": payload["all_pass"], "frontier": payload["frontier_reached"]}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
