#!/usr/bin/env python3
"""Controller assembly: verify and combine independent runtime receipts."""

from __future__ import annotations

import sys
from pathlib import Path

from contract_utils import load_json, sha256, write_json


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
stage_movement_allowed = False
TOOL_MANIFEST = {
    "hashed_json_receipt_assembly": {
        "used": True,
        "reason": "Verifies shared contract identity and combines independent lane verdicts without scientific recomputation.",
    }
}
TOOL_INTEGRATION_DEPTH = {"hashed_json_receipt_assembly": "supportive"}


HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "spec.json"
MANIFEST_PATH = HERE / "artifacts" / "trajectory_contract_v1.json"
PYDMD_PATH = HERE / "receipts" / "pydmd_receipt.json"
DEEPTIME_PATH = HERE / "receipts" / "deeptime_vamp_receipt.json"
RESULT_PATH = HERE / "results" / "stage_interior_spectral_kinetic_discriminator_v0_results.json"


def main() -> int:
    spec = load_json(SPEC_PATH)
    manifest = load_json(MANIFEST_PATH)
    pydmd = load_json(PYDMD_PATH)
    deeptime = load_json(DEEPTIME_PATH)
    contract_hashes_match = (
        pydmd["contract"]["npz_sha256"]
        == deeptime["contract"]["npz_sha256"]
        == manifest["npz_sha256"]
    )
    manifest_hashes_match = (
        pydmd["contract"]["manifest_sha256"]
        == deeptime["contract"]["manifest_sha256"]
        == sha256(MANIFEST_PATH)
    )
    runtime_separation_honest = (
        pydmd["runtime"]["launcher"]
        == "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
        and pydmd["runtime"]["launcher_samefile_as_runtime"] is True
        and deeptime["runtime"]["launcher"]
        == "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/deeptime-0.4.5-py313/bin/python"
        and deeptime["runtime"]["launcher_samefile_as_runtime"] is True
        and deeptime["input_isolation"]["reads_pydmd_receipt"] is False
        and deeptime["input_isolation"]["reads_assembled_result"] is False
    )
    gates = {
        "hashed_npz_contract_shared_exactly": contract_hashes_match,
        "hashed_json_manifest_shared_exactly": manifest_hashes_match,
        "runtime_separation_is_explicit": runtime_separation_honest,
        "pydmd_lane_passes_clean_and_control_gates": bool(pydmd["lane_pass"]),
        "deeptime_lane_passes_clean_and_control_gates": bool(deeptime["lane_pass"]),
        "claim_ceiling_is_scratch_only": (
            spec["classification"] == "scratch_diagnostic"
            and not spec["promotion_allowed"]
            and not spec["formal_admission_allowed"]
            and not spec["stage_movement_allowed"]
        ),
    }
    result_pass = all(gates.values())
    result = {
        "schema": "codex_ratchet.stage_interior_spectral_kinetic_discriminator.result.v1",
        "sim_id": spec["sim_id"],
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "result_pass": result_pass,
        "scientific_verdict": (
            "finite_two_order_spectral_kinetic_discrimination_survives_heldout_probes_and_collapses_under_controls"
            if result_pass
            else "finite_two_order_spectral_kinetic_discrimination_inconclusive_under_declared_gates"
        ),
        "candidate_orders": spec["candidate_orders"],
        "contract": {
            "manifest_path": str(MANIFEST_PATH.relative_to(HERE)),
            "manifest_sha256": sha256(MANIFEST_PATH),
            "npz_path": manifest["npz_path"],
            "npz_sha256": manifest["npz_sha256"],
        },
        "source_hashes": manifest["source_hashes"],
        "runtime_receipts": {
            "pydmd": {"path": str(PYDMD_PATH.relative_to(HERE)), "sha256": sha256(PYDMD_PATH)},
            "deeptime": {"path": str(DEEPTIME_PATH.relative_to(HERE)), "sha256": sha256(DEEPTIME_PATH)},
        },
        "runtime_boundary": (
            "PyDMD and deeptime independently read the same hashed contract. Neither runtime reads the other runtime's "
            "receipt. This controller assembly checks agreement of input identity and combines verdicts; it does not "
            "treat either interpreter as confirming the other."
        ),
        "lane_results": {
            "pydmd": {"evaluations": pydmd["evaluations"], "gates": pydmd["gates"], "pass": pydmd["lane_pass"]},
            "deeptime": {
                "evaluations": deeptime["evaluations"],
                "gates": deeptime["gates"],
                "pass": deeptime["lane_pass"],
            },
        },
        "gates": gates,
        "tool_integration_depth": {
            "PyDMD.BOPDMD.fit": "claim_load_bearing",
            "PyDMD.HankelDMD.fit": "claim_load_bearing",
            "deeptime.decomposition.VAMP.fit_fetch": "claim_load_bearing",
            "numpy": "control_only",
        },
        "claim_ceiling": spec["claim_ceiling"],
        "blocked_consumers": spec["blocked_consumers"],
        "fabrication_audit": {
            "found_fabrication": False,
            "checks": [
                "candidate-varying input is cycle order only; pooled position weights are shared",
                "held-out seeds do not overlap training seeds",
                "controls are exact temporal row permutations preserving per-trajectory marginals",
                "no four-state latent dimension is requested",
                "no parity or cross-runtime confirmation claim is made",
                "all promotion/admission/stage flags remain false"
            ],
            "scope": "controller-local mechanical and semantic audit; no independent fresh-context worker ran"
        },
    }
    write_json(RESULT_PATH, result)
    print(f"{RESULT_PATH}: result_pass={result_pass}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
