#!/usr/bin/env python3
"""Code-based semantic ceiling audit for the frozen v0 surrogate."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "The semantic audit uses standard-library source inspection, hashing, and JSON receipt emission.",
    },
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "results" / "semantic_audit.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    spec = json.loads((HERE / "spec.json").read_text(encoding="utf-8"))
    engine_paths = [
        HERE / "run_julia.jl",
        HERE / "run_jax.py",
        HERE / "run_pytorch.py",
    ]
    engine_text = "\n".join(path.read_text(encoding="utf-8") for path in engine_paths)
    validator_text = (HERE / "validate_controller_envelope.py").read_text(
        encoding="utf-8"
    )
    controller_text = (HERE / "run_controller.py").read_text(encoding="utf-8")
    mutation_text = (HERE / "run_mutation_tests.py").read_text(encoding="utf-8")
    controls_recomputed = all(
        token in engine_text
        for token in (
            "reverse_drive = proposal_loss - initial_loss",
            "null_drive = coface_loss",
            "universal_drive = initial_loss - coface_loss",
            "flat_drive = coface_loss",
        )
    )
    validator_recomputes = all(
        token in validator_text
        for token in (
            "def transitive_closure",
            "def mss_antichain",
            "def expected_drive",
        )
    )
    semantic_gates = {
        "S0_fact_only_generation": False,
        "S1_controls_same_code_path": controls_recomputed,
        "S2_independent_drive_mss_reconstruction": validator_recomputes,
        "S3_mss_selects_proposal": False,
        "S4_label_equivariance": False,
        "S5_post_seal_held_out_estate": False,
        "S6_persistent_append_only_pawl": False,
        "S7_source_level_coherent_mutations": False,
        "S8_independently_measured_drive_facts": False,
    }
    findings = [
        {
            "code": "designed_positive_fixture",
            "evidence": "spec.fixtures.positive_drive contains initial/proposal/demand and expected decision",
        },
        {
            "code": "mss_bypassed",
            "evidence": "engine proposal is graph closure before MSS antichain is computed",
        },
        {
            "code": "label_equivariance_absent",
            "evidence": "demand relocation is not a simultaneous permutation of T, E0, D, and weights",
        },
        {
            "code": "held_out_policy_absent",
            "evidence": "drive policy has one positive and one flat declared fixture",
        },
        {
            "code": "pawl_absent",
            "evidence": "results overwrite files and do not bind before/fact/evidence/after state hashes",
        },
        {
            "code": "mutations_envelope_only",
            "evidence": "mutation runner edits assembled envelope fields without regenerating engine receipts",
        },
    ]
    audit = {
        "schema": "codex_ratchet.tolerance_to_equivalence.semantic_audit.v1",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "classification": CLASSIFICATION,
        "semantic_role": "semantic_audit",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "sim_id": spec["sim_id"],
        "found_fabrication": True,
        "fabrication_meaning": "by-construction controls or hardcoded semantic expectations, not bad-faith authorship",
        "semantic_gates": semantic_gates,
        "semantic_forcing_pass": all(semantic_gates.values()),
        "mechanical_repairs": {
            "controls_recomputed_through_loss": controls_recomputed,
            "validator_recomputes_drive_and_mss": validator_recomputes,
            "portable_julia_default": 'str(ROOT / "system_v5/julia_carrier")'
            in controller_text,
        },
        "findings": findings,
        "source_bindings": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in [
                HERE / "spec.json",
                HERE / "run_controller.py",
                *engine_paths,
                HERE / "validate_controller_envelope.py",
                HERE / "run_mutation_tests.py",
                Path(__file__).resolve(),
            ]
        },
        "mutation_scope": (
            "envelope_only"
            if "copy.deepcopy(baseline)" in mutation_text
            else "unknown"
        ),
        "decision": "HOLD_DESIGNED_SURROGATE",
        "ratchet_state": "OPEN",
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "official_launch_allowed": False,
        "scientific_claim_proven": False,
        "claim_ceiling": "mechanically tested finite pair-collapse-loss surrogate; no forced or persistent Ratchet tooth",
        "replacement_preregistration": "system_v7/sims/tolerance_to_equivalence_ratchet_rung_v1_semantic_forcing/preregistration_receipt.json",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "semantic_forcing_pass": audit["semantic_forcing_pass"],
                "decision": audit["decision"],
                "finding_count": len(findings),
                "out": str(OUT),
            },
            sort_keys=True,
        )
    )
    return 0 if audit["semantic_forcing_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
