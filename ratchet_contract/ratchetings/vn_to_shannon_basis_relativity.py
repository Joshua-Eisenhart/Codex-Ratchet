#!/usr/bin/env python3
"""Basis-relativity disclosure for vn_to_shannon.py's one-way dephasing arrow.

vn_to_shannon.py's committed claim: dephasing D(rho)=diag(rho) in the
COMPUTATIONAL basis is one-way (S(D(rho)) >= S(rho), non-invertible). This
probe checks whether that one-way-ness is a BASIS-FREE structural fact about
dephasing, or whether it is relative to the FIXED reference (pointer) basis
vn_to_shannon actually uses.

Result: dephasing in rho's OWN eigenbasis, D_eigen(rho) = sum_i lambda_i
|v_i><v_i|, reconstructs rho EXACTLY (that is what an eigendecomposition is),
so S(D_eigen(rho)) - S(rho) == 0 and the map is trivially invertible at that
state. The one-way drop only appears once the reference basis is FIXED
independently of the state -- the computational basis, chosen by the Layer-2
carrier Delta^1's z-axis.

This is NOT a refutation of vn_to_shannon's RATCHETED_ONE_WAY verdict: that
arrow holds exactly as claimed relative to the fixed pointer basis it
actually uses, which is the physical content of decoherence relative to a
fixed measurement basis. It IS a disclosure the receipt should carry: the
one-way claim is basis-relative, not basis-free.

classification = "tool_lego_fit_probe"; promotion_allowed = False;
ordering_status = "PROPOSED not canon". Engine substrate (2026-07-22): the
compute path is jax.numpy x64 -- numpy fully removed. The receipt carries a
julia:QuantumOptics + jax:dynamiqs witness-leg pair (both load-bearing): each
leg independently re-derives the basis-relativity witness (computational-basis
pinch raises entropy; eigenbasis pinch is the identity), and the jax leg is
re-run by claimgate_plugin/three_engine_seal.py as execution evidence.
"""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Any

import os
os.environ.setdefault("JAX_ENABLE_X64", "1")
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

classification = "tool_lego_fit_probe"
promotion_allowed = False
ordering_status = "PROPOSED not canon"
TOL = 1.0e-10
LEG_TOL = 1.0e-9
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True,
            "reason": "Base engine (jax.numpy x64): Bloch-ball sampled states, eigenbasis rotation/pinch, "
                      "entropy and invertibility checks; plus the standalone dynamiqs witness leg the seal re-runs."},
    "julia": {"tried": False, "used": False,
              "reason": "Authoritative QuantumOptics basis-rotation witness leg run by main(); "
                        "updated at runtime with its actual result."},
    "sympy": {"tried": False, "used": False,
              "reason": "The numeric jax/julia witness pair is sufficient for this disclosure probe."},
    "z3": {"tried": False, "used": False, "reason": "Not run for this disclosure probe."},
    "cvc5": {"tried": False, "used": False, "reason": "Not run for this disclosure probe."},
    "qutip": {"tried": False, "used": False, "reason": "Not run for this disclosure probe."},
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "julia": None, "sympy": None, "z3": None, "cvc5": None, "qutip": None,
}


def density_from_bloch(x: float, y: float, z: float) -> jnp.ndarray:
    return jnp.array([[1.0 + z, x - 1j * y], [x + 1j * y, 1.0 - z]], dtype=jnp.complex128) / 2.0


def vn_entropy(rho: jnp.ndarray) -> float:
    eigenvalues = jnp.linalg.eigvalsh(rho)
    eigenvalues = jnp.clip(jnp.real(eigenvalues), 0.0, 1.0)
    positive = eigenvalues[eigenvalues > 0.0]
    return float(-jnp.sum(positive * jnp.log(positive)))


def dephase_computational(rho: jnp.ndarray) -> jnp.ndarray:
    """Pinch rho in the FIXED computational (pointer) basis. This is the
    channel vn_to_shannon.py commits its RATCHETED_ONE_WAY verdict to."""
    return jnp.diag(jnp.diag(rho)).astype(jnp.complex128)


def dephase_eigenbasis(rho: jnp.ndarray) -> jnp.ndarray:
    """Pinch rho in ITS OWN eigenbasis: D_eigen(rho) = sum_i lambda_i |v_i><v_i|.
    By definition of the eigendecomposition of a Hermitian rho this reconstructs
    rho exactly -- confirmed numerically below, not assumed."""
    eigenvalues, eigenvectors = jnp.linalg.eigh(rho)
    reconstructed = jnp.zeros_like(rho)
    for lam, vec in zip(eigenvalues, eigenvectors.T):
        reconstructed = reconstructed + lam * jnp.outer(vec, vec.conj())
    return reconstructed


def sampled_states() -> list[tuple[str, jnp.ndarray, jnp.ndarray]]:
    """Same interior grid + pure-boundary sweep as vn_to_shannon.py's sampler."""
    states: list[tuple[str, jnp.ndarray, jnp.ndarray]] = []
    grid = jnp.arange(-0.75, 0.751, 0.25)
    for x in grid:
        for y in grid:
            for z in grid:
                vector = jnp.array([x, y, z], dtype=float)
                if float(jnp.dot(vector, vector)) < 1.0 - 1.0e-12:
                    states.append(("interior", vector, density_from_bloch(x, y, z)))
    for theta in jnp.linspace(0.0, math.pi, 7):
        for phi in jnp.linspace(0.0, 2.0 * math.pi, 8, endpoint=False):
            vector = jnp.array([
                math.sin(theta) * math.cos(phi),
                math.sin(theta) * math.sin(phi),
                math.cos(theta),
            ])
            states.append(("pure_boundary", vector, density_from_bloch(*vector)))
    return states


def basis_relativity_report() -> dict[str, Any]:
    states = sampled_states()

    comp_gaps: list[float] = []
    comp_offdiag_gaps: list[float] = []
    eigen_gaps: list[float] = []
    eigen_recon_errors: list[float] = []
    for kind, vector, rho in states:
        s_rho = vn_entropy(rho)
        d_comp = dephase_computational(rho)
        d_eigen = dephase_eigenbasis(rho)
        comp_gap = vn_entropy(d_comp) - s_rho
        eigen_gap = vn_entropy(d_eigen) - s_rho
        comp_gaps.append(comp_gap)
        eigen_gaps.append(eigen_gap)
        eigen_recon_errors.append(float(jnp.max(jnp.abs(d_eigen - rho))))
        if abs(rho[0, 1]) > TOL:
            comp_offdiag_gaps.append(comp_gap)

    comp_basis_drop = float(min(comp_offdiag_gaps)) if comp_offdiag_gaps else 0.0
    eigenbasis_gap = float(max(abs(g) for g in eigen_gaps))
    eigenbasis_recon_max_error = float(max(eigen_recon_errors))

    # Invertibility witness, FIXED computational basis (same pair vn_to_shannon.py uses):
    rho = jnp.array([[0.5, 0.25], [0.25, 0.5]], dtype=jnp.complex128)
    rho_prime = jnp.array([[0.5, 0.25j], [-0.25j, 0.5]], dtype=jnp.complex128)
    d_comp_rho, d_comp_rho_prime = dephase_computational(rho), dephase_computational(rho_prime)
    comp_noninvertible = bool(
        (not jnp.allclose(rho, rho_prime, atol=TOL))
        and jnp.allclose(d_comp_rho, d_comp_rho_prime, atol=TOL)
    )

    # Witness-state quantities the julia/jax engine legs independently re-derive:
    witness_s_rho = vn_entropy(rho)
    witness_comp_gap = vn_entropy(d_comp_rho) - witness_s_rho
    witness_eigen_gap = abs(vn_entropy(dephase_eigenbasis(rho)) - witness_s_rho)

    # Eigenbasis-dephasing invertibility: D_eigen(rho) reconstructs rho exactly at
    # every sampled state (the map is the identity ON that state, by construction
    # of its own eigendecomposition) -- confirmed numerically, not assumed.
    eigen_invertible_on_samples = bool(eigenbasis_recon_max_error < TOL)

    comp_basis_monotone_always_geq = bool(min(comp_gaps) >= -TOL)
    eigen_basis_always_zero = bool(eigenbasis_gap < TOL)

    disclosure = (
        "The vn_to_shannon one-way dephasing arrow is BASIS-RELATIVE, not basis-free. "
        f"Relative to the FIXED computational (pointer) basis, D_comp raises entropy on every "
        f"off-diagonal sampled state (min gap {comp_basis_drop:.6f} > 0) and is NOT invertible "
        f"(the witness pair rho, rho_prime share a computational-basis diagonal but differ in "
        f"off-diagonal coherence, and both collapse to the same D_comp image). Relative to EACH "
        f"state's OWN eigenbasis, dephasing is the identity on that state: D_eigen(rho) = rho "
        f"exactly (max entropy gap over all sampled states = {eigenbasis_gap:.3e}, reconstruction "
        f"error = {eigenbasis_recon_max_error:.3e}), and is trivially invertible there. This is the "
        "physical content of decoherence relative to a fixed pointer basis, not a refutation of "
        "the committed arrow -- but it IS a disclosure: the committed one-way claim smuggles the "
        "computational basis as its reference, and does not hold basis-free."
    )

    verdict = ("BASIS_RELATIVE_DISCLOSURE"
               if (comp_basis_monotone_always_geq and comp_noninvertible
                   and eigen_basis_always_zero and eigen_invertible_on_samples)
               else "FAILED")

    return {
        "schema_version": "1.0",
        "object": ("Same Layer-1/Layer-2 pair as vn_to_shannon.py: 2x2 density operators "
                   "(Bloch ball) -> diagonal simplex Delta^1, dephasing/pinching channel D."),
        "sampled_state_count": len(states),
        "comp_basis_drop": comp_basis_drop,
        "comp_basis_monotone_always_geq": comp_basis_monotone_always_geq,
        "comp_basis_noninvertible_witness": comp_noninvertible,
        "eigenbasis_gap": eigenbasis_gap,
        "eigenbasis_gap_is_zero": eigen_basis_always_zero,
        "eigenbasis_reconstruction_max_error": eigenbasis_recon_max_error,
        "eigenbasis_invertible_on_samples": eigen_invertible_on_samples,
        "witness_vn_entropy_rho": witness_s_rho,
        "witness_comp_basis_entropy_gap": witness_comp_gap,
        "witness_eigenbasis_gap": witness_eigen_gap,
        "disclosure": disclosure,
        "verdict": verdict,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "ordering_status": ordering_status,
        "floor_claims": [{"key": "ratcheting.vn_to_shannon_basis_relativity.eigenbasis_gap",
                          "value": eigenbasis_gap, "direction": "lower_is_better"}],
        "notes": [
            "This does NOT refute vn_to_shannon's committed RATCHETED_ONE_WAY verdict -- the "
            "arrow holds exactly as claimed relative to the fixed computational/pointer basis "
            "vn_to_shannon actually uses (the Layer-2 carrier Delta^1's z-axis).",
            "It DOES disclose that the arrow is basis-relative: a differently-chosen reference "
            "basis (the state's own eigenbasis) makes the SAME channel act as the identity, "
            "entropy-preserving and invertible, on that state.",
            "Engine substrate 2026-07-22: compute path is jax.numpy x64 (numpy fully removed); "
            "the receipt carries julia:QuantumOptics + jax:dynamiqs witness legs, and the jax leg "
            "is re-run by the three-engine seal as execution evidence.",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "engines_ran": {"jax": True, "julia": False, "sympy": False, "z3": False,
                        "cvc5": False, "qutip": False},
    }


def _run_leg(cmd: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except Exception as exc:  # noqa: BLE001 -- dispatch failure is recorded, not smoothed
        return {"ran": False, "reason": f"leg dispatch failed: {exc}"}
    if proc.returncode != 0:
        return {"ran": False, "reason": f"leg exit {proc.returncode}: {proc.stderr.strip()[-200:]}"}
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
    if not lines:
        return {"ran": False, "reason": "leg produced no JSON on stdout"}
    data = json.loads(lines[-1])
    data["ran"] = True
    return data


def main() -> None:
    report = basis_relativity_report()

    # Engine witness legs -- sequential (julia startup is expensive; never parallel julia).
    here = Path(__file__).resolve().parent
    legs = {"julia": _run_leg(["julia", str(here / "vn_to_shannon_basis_relativity_julia.jl")])}
    legs["jax"] = _run_leg([SIM_PY, str(here / "vn_to_shannon_basis_relativity_jax.py")])

    # Loud cross-check, not smoothed: each leg must re-derive the in-process witness numbers.
    for engine, leg in legs.items():
        if not leg.get("ran"):
            continue
        divergence = max(
            abs(float(leg["vn_entropy_rho"]) - report["witness_vn_entropy_rho"]),
            abs(float(leg["comp_basis_entropy_gap"]) - report["witness_comp_basis_entropy_gap"]),
            abs(float(leg["eigenbasis_gap"]) - report["witness_eigenbasis_gap"]),
        )
        if divergence > LEG_TOL:
            raise AssertionError(f"{engine} witness leg diverges from the in-process jax.numpy "
                                 f"witness by {divergence} > {LEG_TOL} -- report, do not smooth.")

    if legs["julia"].get("ran"):
        TOOL_INTEGRATION_DEPTH["julia"] = "load_bearing"
        TOOL_MANIFEST["julia"]["tried"] = True
        TOOL_MANIFEST["julia"]["used"] = True
        TOOL_MANIFEST["julia"]["reason"] = (
            "Authoritative QuantumOptics basis-rotation leg: the same pinching channel raises entropy "
            "in the fixed computational basis and is the identity in rho's own eigenbasis; agrees with "
            "the jax witness to <1e-9.")
        report["engines_ran"]["julia"] = True
    if not legs["jax"].get("ran"):
        # The in-process compute path is jax, but the seal's execution evidence is the
        # standalone leg; without it the receipt must not claim a re-runnable jax witness.
        TOOL_INTEGRATION_DEPTH["jax"] = None
        report["engines_ran"]["jax"] = False

    report["three_engine_legs"] = legs
    report["engine_values"] = {
        "julia_comp_basis_entropy_gap": legs["julia"].get("comp_basis_entropy_gap") if legs["julia"].get("ran") else None,
        "jax_comp_basis_entropy_gap": legs["jax"].get("comp_basis_entropy_gap") if legs["jax"].get("ran") else None,
    }
    report["TOOL_INTEGRATION_DEPTH"] = dict(TOOL_INTEGRATION_DEPTH)

    output = Path(__file__).resolve().parent / "results" / "vn_to_shannon_basis_relativity.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": str(output),
        "verdict": report["verdict"],
        "comp_basis_drop": report["comp_basis_drop"],
        "eigenbasis_gap": report["eigenbasis_gap"],
        "julia_comp_basis_entropy_gap": report["engine_values"]["julia_comp_basis_entropy_gap"],
        "jax_comp_basis_entropy_gap": report["engine_values"]["jax_comp_basis_entropy_gap"],
    }, indent=2))


if __name__ == "__main__":
    main()
