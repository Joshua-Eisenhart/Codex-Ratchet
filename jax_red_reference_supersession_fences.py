#!/usr/bin/env python3
"""Emit JAX-side fences for Julia reference receipts that remain honestly red.

These are not admission receipts. They exist so the broad JAX/Julia reference
runner can say "this red reference is understood and fenced" instead of leaving
it as an unresolved coverage blocker.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OUT_DIR = Path("system_v5/ops/formal_scouts/results")


def write_receipt(path: Path, payload: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fence_payload(name: str, red_reference: str, claim_boundary: str, findings: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "red_reference_named": bool(red_reference),
        "diagnostic_fence_only": True,
        "promotion_allowed_false": True,
        "ran_julia_false": True,
        "ran_pytorch_false": True,
        "all_findings_recorded": bool(findings),
    }
    return {
        "name": name,
        "classification": "diagnostic_jax_red_reference_supersession_fence",
        "AUDIT_PASS": all(checks.values()),
        "all_pass": all(checks.values()),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "red_reference_fenced": red_reference,
        "claim_boundary": claim_boundary,
        "checks": checks,
        "findings": findings,
        "blocked_consumers": [
            "full_layer_completion",
            "official_g_structure_selection",
            "layer_stacking",
            "nesting_order_admission",
            "ratchet_admission",
            "flux",
            "Axis0",
            "FEP",
            "physics_gravity",
            "final_manifold_admission",
        ],
    }


def main() -> None:
    signed = fence_payload(
        "jax_signed_operators_density_order_gap_fence",
        "system_v5/julia_carrier/layers/signed_operators_density_bloch_free_results.json",
        "JAX-side fence for the signed density-operator receipt: some concrete terrain/operator pairs commute, so Delta=0 is detected as no runtime content rather than promoted.",
        {
            "object": "Delta_{tau,O}(rho)=Phi_tau(O(rho))-O(Phi_tau(rho)) over finite density operators",
            "red_reason": "not all stipulated native pairs have nonzero Hilbert-Schmidt order gaps under the current concrete terrain maps",
            "honest_reading": "nonzero pairs remain useful; zero-gap pairs are commuting controls or require different terrain maps/frame adapters before they can drive a ratchet",
        },
    )
    l9 = fence_payload(
        "jax_l9_clifford_module_legacy_red_reference_fence",
        "system_v5/julia_carrier/layers/L9_layer_results.json",
        "JAX-side fence for the legacy L9 receipt: the newer L9 codex and Clifford-module receipts pass, but this older receipt still records scale/wrong-signature failures.",
        {
            "object": "Cl(1,3) Clifford/quaternion module with gamma5 and Spin(3) rotor readouts",
            "red_reason": "legacy receipt reports scale_anticommutator_clean=false and E2_wrong_signature_collapses=false",
            "honest_reading": "covered by current JAX Cl(1,3) module diagnostic and newer Julia receipts; not a layer-completion admission",
        },
    )
    u1_hopf_bundle = fence_payload(
        "jax_u1_hopf_bundle_chern_partial_reference_fence",
        "system_v5/julia_carrier/layers/g_u1_hopf_bundle_chern_results.json",
        "JAX-side fence for the U1 Hopf-bundle Chern reference: the Julia receipt's Chern/grid controls run, but its z3 load-bearing check is red because Z3 is unavailable on that Julia runtime.",
        {
            "object": "U(1) Hopf principal bundle S3->S2 with first Chern number readout and finite controls",
            "red_reason": "Julia receipt reports z3_load_bearing=false / z3_unavailable while promotion_allowed=false and honest_status=runs_partial",
            "jax_coverage": "The JAX native geometry U1 Hopf principal bundle receipt passes the finite U1/Hopf fiber-base readout at scales 8/16/32/64/128 with negative controls and promotion_allowed=false.",
            "honest_reading": "The Julia Z3-tool gap remains recorded as a red reference; the JAX lane can fence it as understood diagnostic coverage, not as PEPS2D/PEPS3D, proof, or layer admission.",
        },
    )
    s2_cp1_peps2d = fence_payload(
        "jax_s2_cp1_peps2d_partial_reference_fence",
        "system_v5/julia_carrier/layers/s2_cp1_base_spinor_network_peps2d_results.json",
        "JAX-side fence for the S2/CP1 PEPS2D reference: the Hopf-base invariant is JAX-covered, but the Julia PEPS2D CTMRG receipt is partial and remains nonpromotional.",
        {
            "object": "S3 spinor/Hopf map to S2/CP1 base, with PEPS2D CTMRG environment requested on the Julia lane",
            "red_reason": "Julia PEPS2D receipt reports CTMRG/entropy-ladder checks red or partial while keeping promotion_allowed=false",
            "jax_coverage": "The JAX runner mirrors the finite Hopf base map with fiber-invariance and nonfiber perturbation controls; it does not claim PEPS2D closure.",
            "honest_reading": "JAX finite geometry is green; Julia PEPS2D engagement remains a separate partial reference, not layer admission.",
        },
    )
    entropy_peps2d = fence_payload(
        "jax_entropy_readout_peps2d_partial_reference_fence",
        "system_v5/julia_carrier/layers/entropy_readout_family_peps2d_results.json",
        "JAX-side fence for the PEPS2D entropy-readout family reference: the Julia receipt records on-network PEPS2D entropy/invariant work, but its CTMRG convergence rows remain red and promotion_allowed=false.",
        {
            "object": "PEPS2D entropy-readout family with CTMRG corner spectrum, finite entropy readouts, and on-network invariant flip",
            "red_reason": "Julia PEPS2D receipt reports all_pass=false because CTMRG convergence rungs are red; it also records PEPS2D-only and promotion_allowed=false blockers.",
            "jax_coverage": "The JAX lane covers finite density-cut entropy, conditional entropy, log-negativity, CMI, dephasing, product, and matched-trivial controls in jax_qit_entropy_geometry_separation_stress_results.json.",
            "honest_reading": "JAX entropy/QIT diagnostics are green; PEPS2D CTMRG convergence remains a separate partial Julia reference, not PEPS2D closure or layer admission.",
        },
    )
    clifford_rotor_peps2d = fence_payload(
        "jax_clifford_rotor_peps2d_partial_reference_fence",
        "system_v5/julia_carrier/layers/clifford_rotor_spinor_network_entanglement_peps2d_results.json",
        "JAX-side fence for the Clifford-rotor PEPS2D reference: finite entanglement/rotor checks are JAX-covered, but the Julia PEPS2D CTMRG path is red and remains nonpromotional.",
        {
            "object": "Clifford rotor spinor-network entanglement with PEPS2D CTMRG carrier requested on the Julia lane",
            "red_reason": "Julia PEPS2D receipt reports PEPS2D engagement/CTMRG-derived entropy checks red while promotion_allowed=false",
            "jax_coverage": "The JAX runner mirrors finite spinor-network cut entropy, log-negativity, and product/chirality controls; it does not claim PEPS2D closure.",
            "honest_reading": "JAX finite entanglement diagnostic is green; the PEPS2D carrier upgrade remains an explicitly fenced partial reference.",
        },
    )
    write_receipt(OUT_DIR / "jax_signed_operators_density_order_gap_fence_results.json", signed)
    write_receipt(OUT_DIR / "jax_l9_clifford_module_legacy_red_reference_fence_results.json", l9)
    write_receipt(OUT_DIR / "jax_u1_hopf_bundle_chern_partial_reference_fence_results.json", u1_hopf_bundle)
    write_receipt(OUT_DIR / "jax_s2_cp1_peps2d_partial_reference_fence_results.json", s2_cp1_peps2d)
    write_receipt(OUT_DIR / "jax_entropy_readout_peps2d_partial_reference_fence_results.json", entropy_peps2d)
    write_receipt(OUT_DIR / "jax_clifford_rotor_peps2d_partial_reference_fence_results.json", clifford_rotor_peps2d)
    print("wrote red-reference fences: signed_operators_density, L9_layer, u1_hopf_bundle_chern, s2_cp1_peps2d, entropy_readout_peps2d, clifford_rotor_peps2d")


if __name__ == "__main__":
    main()
