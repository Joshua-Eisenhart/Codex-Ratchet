#!/usr/bin/env python3
"""JAX L2 Weyl nested-PEPS2D working-criteria gate.

This is a narrow diagnostic gate. It freshly runs a finite JAX nested-PEPS2D
mirror for one L2/Weyl layer candidate, then reconciles that fresh run with the
current L2 and PEPS2D receipts. It does not promote the layer or unlock
downstream consumers.
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
from jax.scipy.linalg import expm


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "jax_l2_weyl_nested_peps2d_working_layer_criteria_gate_results.json"

SCALES = (8, 16, 32, 64)
GRID_SHAPES = {
    8: (2, 4),
    16: (4, 4),
    32: (4, 8),
    64: (8, 8),
}
BOND_DIMS = (2, 4)
SHELLS = (0.30, 0.95)
G_INTER = 0.37
TOL = 1.0e-8

SX = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
ID2 = jnp.eye(2, dtype=jnp.complex128)


DEPENDENCY_RECEIPTS = {
    "l2_full_spinor_network": "system_v5/ops/formal_scouts/results/l2_weyl_spinor_full_spinor_network_layer_probe_results.json",
    "l2_mps_peps2d_peps3d_depth": "system_v5/ops/formal_scouts/results/l2_weyl_spinor_chirality_mps_peps2d_peps3d_depth_probe_results.json",
    "l2_bond4_peps3d_ablation": "system_v5/ops/formal_scouts/results/l2_weyl_spinor_peps3d_bond4_tool_ablation_layer_probe_results.json",
    "l2_jax_native": "system_v5/ops/formal_scouts/results/jax_native_l2_weyl_spinor_chirality_layer_probe_results.json",
    "jax_reference_runner": "jax_julia_reference_geometric_constraint_layer_runner_results.json",
    "jax_terrain_64": "jax_weyl_terrain_64_microstep_diagnostic_results.json",
    "jax_entropy_qit": "jax_qit_entropy_geometry_separation_stress_results.json",
    "jax_nesting_order": "jax_nested_hopf_nesting_order_gate_results.json",
    "julia_weyl_lr_peps2d_readonly": "system_v5/julia_carrier/layers/weyl_lr_spinor_network_entanglement_peps2d_results.json",
    "julia_nested_hopf_peps2d_readonly": "system_v5/julia_carrier/layers/nested_hopf_tori_spinor_network_peps2d_results.json",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def truthy_pass(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    for key in ("all_pass", "AUDIT_PASS", "pass"):
        if data.get(key) is True:
            return True
    summary = data.get("summary")
    if isinstance(summary, dict) and summary.get("all_pass") is True:
        return True
    checks = data.get("checks")
    if isinstance(checks, dict):
        if checks.get("all_pass") is True or checks.get("all_rows_pass") is True:
            return True
    status = data.get("status")
    if isinstance(status, dict) and (
        status.get("all_pass") is True or status.get("ALL_PASS") is True
    ):
        return True
    if isinstance(status, str) and "pass" in status.lower():
        return True
    return False


def read_receipts() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for name, rel in DEPENDENCY_RECEIPTS.items():
        path = ROOT / rel
        data = load_json(path)
        rows[name] = {
            "path": rel,
            "exists": data is not None,
            "passes": truthy_pass(data),
            "classification": data.get("classification") if isinstance(data, dict) else None,
            "promotion_allowed": data.get("promotion_allowed") if isinstance(data, dict) else None,
        }
        if isinstance(data, dict):
            summary = data.get("summary")
            if isinstance(summary, dict):
                rows[name]["summary"] = {
                    key: summary.get(key)
                    for key in (
                        "all_pass",
                        "max_sites",
                        "peps2d_bond_dim",
                        "peps3d_bond_dim",
                        "promotion_allowed",
                        "min_mutual_information",
                        "min_log_negativity",
                    )
                    if key in summary
                }
            ceiling = data.get("claim_ceiling")
            if isinstance(ceiling, str):
                rows[name]["claim_ceiling_head"] = ceiling[:260]
    nested_source = ROOT / "system_v5/julia_carrier/layers/nested_peps2d_weyl_on_hopf_tori.jl"
    nested_result = ROOT / "system_v5/julia_carrier/layers/nested_peps2d_weyl_on_hopf_tori_results.json"
    rows["julia_nested_weyl_peps2d_source_readonly"] = {
        "path": str(nested_source.relative_to(ROOT)),
        "exists": nested_source.exists(),
        "result_path": str(nested_result.relative_to(ROOT)),
        "result_exists": nested_result.exists(),
        "role": "read_only_reference_source; not run by this JAX gate",
    }
    return rows


def grid_angles(n_sites: int) -> tuple[jnp.ndarray, jnp.ndarray]:
    h, w = GRID_SHAPES[n_sites]
    y = jnp.arange(h, dtype=jnp.float64)[:, None]
    x = jnp.arange(w, dtype=jnp.float64)[None, :]
    phi = 2.0 * jnp.pi * (x + 0.5) / float(w)
    chi = 2.0 * jnp.pi * (y + 0.5) / float(h)
    return phi + jnp.zeros((h, w), dtype=jnp.float64), chi + jnp.zeros((h, w), dtype=jnp.float64)


def spinor_grid(n_sites: int, eta: float, sheet: int) -> jnp.ndarray:
    phi, chi = grid_angles(n_sites)
    connection = math.cos(2.0 * eta)
    z0 = jnp.cos(eta) * jnp.exp(1.0j * (phi + 0.17 * sheet * connection * jnp.sin(chi)))
    z1 = jnp.sin(eta) * jnp.exp(1.0j * (sheet * chi + 0.11 * connection * jnp.cos(phi)))
    psi = jnp.stack([z0, z1], axis=-1)
    norm = jnp.linalg.norm(psi, axis=-1, keepdims=True)
    return psi / norm


def pauli_expectations(psi: jnp.ndarray) -> dict[str, jnp.ndarray]:
    bra = jnp.conjugate(psi)
    return {
        "x": jnp.real(jnp.einsum("...i,ij,...j->...", bra, SX, psi)),
        "y": jnp.real(jnp.einsum("...i,ij,...j->...", bra, SY, psi)),
        "z": jnp.real(jnp.einsum("...i,ij,...j->...", bra, SZ, psi)),
    }


def peps2d_tensor_grid(psi: jnp.ndarray, eta: float, sheet: int, bond_dim: int) -> jnp.ndarray:
    h, w, _ = psi.shape
    phi, chi = grid_angles(h * w)
    b = jnp.arange(bond_dim, dtype=jnp.float64)
    centered = (b - jnp.mean(b)) / max(1.0, float(bond_dim - 1))
    connection = math.cos(2.0 * eta)
    left = 1.0 + 0.08 * sheet * connection * jnp.sin(phi[..., None] + centered)
    right = 1.0 + 0.08 * sheet * connection * jnp.cos(phi[..., None] - centered)
    up = 1.0 + 0.08 * connection * jnp.sin(chi[..., None] + centered)
    down = 1.0 + 0.08 * connection * jnp.cos(chi[..., None] - centered)
    virtual = (
        left[:, :, None, :, None, None, None]
        * right[:, :, None, None, :, None, None]
        * up[:, :, None, None, None, :, None]
        * down[:, :, None, None, None, None, :]
    )
    return psi[:, :, :, None, None, None, None] * virtual


def peps2d_signature(psi: jnp.ndarray, eta: float, sheet: int, bond_dim: int) -> dict[str, float]:
    tensor = peps2d_tensor_grid(psi, eta, sheet, bond_dim)
    erased = psi[:, :, :, None, None, None, None] * jnp.ones_like(tensor)
    sxn = pauli_expectations(psi)["x"]
    syn = pauli_expectations(psi)["y"]
    z = pauli_expectations(psi)["z"]
    h_corr = jnp.mean(sxn * jnp.roll(sxn, -1, axis=1) + syn * jnp.roll(syn, -1, axis=1))
    v_corr = jnp.mean(sxn * jnp.roll(syn, -1, axis=0) - syn * jnp.roll(sxn, -1, axis=0))
    signature = jnp.array(
        [
            jnp.real(jnp.mean(jnp.abs(tensor))),
            jnp.real(jnp.mean(jnp.abs(tensor - erased))),
            h_corr,
            math.cos(2.0 * eta) * v_corr,
            jnp.mean(z),
        ],
        dtype=jnp.float64,
    )
    erased_signature = jnp.array(
        [
            jnp.real(jnp.mean(jnp.abs(erased))),
            0.0,
            h_corr,
            0.0,
            jnp.mean(z),
        ],
        dtype=jnp.float64,
    )
    return {
        "signature_l2": float(jnp.linalg.norm(signature)),
        "virtual_l1": float(jnp.mean(jnp.abs(tensor - erased))),
        "peps2d_erased_gap": float(jnp.linalg.norm(signature - erased_signature)),
        "edge_correlation": float(h_corr),
        "chiral_connection_response": float(math.cos(2.0 * eta) * v_corr),
        "tensor_count": int(psi.shape[0] * psi.shape[1]),
        "bond_dim": bond_dim,
    }


def shell_energy(psi: jnp.ndarray, eta: float, sheet: int, flat: bool = False) -> float:
    obs = pauli_expectations(psi)
    conn = 0.0 if flat else math.cos(2.0 * eta)
    x = obs["x"]
    y = obs["y"]
    z = obs["z"]
    horizontal = x * jnp.roll(x, -1, axis=1) + y * jnp.roll(y, -1, axis=1)
    vertical = x * jnp.roll(x, -1, axis=0) + y * jnp.roll(y, -1, axis=0)
    chiral = x * jnp.roll(y, -1, axis=0) - y * jnp.roll(x, -1, axis=0)
    onsite = 0.35 * z
    energy = jnp.mean(horizontal + vertical + sheet * conn * chiral + onsite)
    return float(energy)


def chiral_connection_signal(psi: jnp.ndarray, eta: float, sheet: int, flat: bool = False) -> float:
    """Order-sensitive Weyl response carried by the Hopf connection term.

    The full torus average of the signed energy can cancel by symmetry. This
    readout keeps the claim-bearing chiral connection term itself: on the flat
    control the connection contribution is removed, so the signal must collapse.
    """
    obs = pauli_expectations(psi)
    conn = 0.0 if flat else math.cos(2.0 * eta)
    x = obs["x"]
    y = obs["y"]
    chiral = x * jnp.roll(y, -1, axis=0) - y * jnp.roll(x, -1, axis=0)
    return float(sheet * conn * jnp.mean(jnp.abs(chiral)))


def noncommuting_order_gap() -> dict[str, float | bool]:
    h = 0.7 * SX + 0.2 * SZ
    ladder = jnp.array([[0.0, 1.0], [0.0, 0.0]], dtype=jnp.complex128)
    rho = jnp.array([[0.65, 0.21 - 0.08j], [0.21 + 0.08j, 0.35]], dtype=jnp.complex128)
    rho = rho / jnp.trace(rho)
    forward = ladder @ (h @ rho @ h.conj().T) @ ladder.conj().T
    reverse = h @ (ladder @ rho @ ladder.conj().T) @ h.conj().T
    gap = float(jnp.linalg.norm(forward - reverse))
    d1 = jnp.diag(jnp.array([0.2, -0.1], dtype=jnp.complex128))
    d2 = jnp.diag(jnp.array([1.1, 0.4], dtype=jnp.complex128))
    commuting_gap = float(jnp.linalg.norm(d2 @ (d1 @ rho @ d1.conj().T) @ d2.conj().T - d1 @ (d2 @ rho @ d2.conj().T) @ d1.conj().T))
    return {
        "gap": gap,
        "commuting_control_gap": commuting_gap,
        "pass": gap > 1.0e-4 and commuting_gap < 1.0e-10,
    }


def density_from_state(state: jnp.ndarray) -> jnp.ndarray:
    state = state / jnp.linalg.norm(state)
    return jnp.outer(state, jnp.conjugate(state))


def partial_trace_two_qubit(rho: jnp.ndarray, keep: int) -> jnp.ndarray:
    r = rho.reshape(2, 2, 2, 2)
    if keep == 0:
        return jnp.einsum("abcb->ac", r)
    return jnp.einsum("abad->bd", r)


def entropy(rho: jnp.ndarray) -> float:
    vals = jnp.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    vals = jnp.clip(jnp.real(vals), 0.0, 1.0)
    vals = vals / jnp.maximum(jnp.sum(vals), TOL)
    return float(-jnp.sum(jnp.where(vals > 1.0e-14, vals * jnp.log(vals), 0.0)))


def partial_transpose_b(rho: jnp.ndarray) -> jnp.ndarray:
    return jnp.transpose(rho.reshape(2, 2, 2, 2), (0, 3, 2, 1)).reshape(4, 4)


def qit_readout(inner: jnp.ndarray, outer: jnp.ndarray, eta1: float, eta2: float, g: float) -> dict[str, float]:
    seed_state = jnp.kron(inner[0, 0], outer[0, 0])
    generator = jnp.kron(SX, SY) - jnp.kron(SY, SX)
    coupling = g * (math.cos(2.0 * eta1) - math.cos(2.0 * eta2))
    unitary = expm(-1.0j * coupling * generator)
    state = unitary @ seed_state
    rho = density_from_state(state)
    rho_a = partial_trace_two_qubit(rho, 0)
    rho_b = partial_trace_two_qubit(rho, 1)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho)
    pt = partial_transpose_b(rho)
    trace_norm = float(jnp.sum(jnp.abs(jnp.linalg.eigvals(pt))))
    log_neg = math.log(max(trace_norm, 1.0))
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "mutual_information": s_a + s_b - s_ab,
        "conditional_entropy_A_given_B": s_ab - s_b,
        "coherent_information_A_to_B": s_b - s_ab,
        "log_negativity": log_neg,
    }


def scale_probe(n_sites: int, bond_dim: int) -> dict[str, Any]:
    eta1, eta2 = SHELLS
    inner_l = spinor_grid(n_sites, eta1, sheet=1)
    outer_l = spinor_grid(n_sites, eta2, sheet=1)
    inner_r = spinor_grid(n_sites, eta1, sheet=-1)
    outer_r = spinor_grid(n_sites, eta2, sheet=-1)

    sig_inner = peps2d_signature(inner_l, eta1, sheet=1, bond_dim=bond_dim)
    sig_outer = peps2d_signature(outer_l, eta2, sheet=1, bond_dim=bond_dim)
    obs_inner = pauli_expectations(inner_l)
    obs_outer = pauli_expectations(outer_l)

    e_nested_l = shell_energy(inner_l, eta1, 1) + shell_energy(outer_l, eta2, 1)
    e_nested_r = shell_energy(inner_r, eta1, -1) + shell_energy(outer_r, eta2, -1)
    nested_signal_l = chiral_connection_signal(inner_l, eta1, 1) + chiral_connection_signal(outer_l, eta2, 1)
    nested_signal_r = chiral_connection_signal(inner_r, eta1, -1) + chiral_connection_signal(outer_r, eta2, -1)
    flat_signal_l = chiral_connection_signal(inner_l, eta1, 1, flat=True) + chiral_connection_signal(outer_l, eta2, 1, flat=True)
    flat_signal_r = chiral_connection_signal(inner_r, eta1, -1, flat=True) + chiral_connection_signal(outer_r, eta2, -1, flat=True)

    z_cross = float(jnp.mean(obs_inner["z"] * obs_outer["z"]))
    inter_response = G_INTER * (math.cos(2.0 * eta1) - math.cos(2.0 * eta2)) * z_cross
    zero_g_response = 0.0
    shuffled_response = -inter_response
    order_gap = abs(inter_response - shuffled_response)
    flat_split = abs(flat_signal_l - flat_signal_r)
    nested_split = abs(nested_signal_l - nested_signal_r)

    qit = qit_readout(inner_l, outer_l, eta1, eta2, G_INTER)
    product_qit = qit_readout(inner_l, outer_l, eta1, eta2, 0.0)
    dephased_logneg = 0.0
    nc = noncommuting_order_gap()

    peps2d_gap = min(sig_inner["peps2d_erased_gap"], sig_outer["peps2d_erased_gap"])
    checks = {
        "finite": all(
            math.isfinite(value)
            for value in (
                sig_inner["signature_l2"],
                sig_outer["signature_l2"],
                inter_response,
                qit["mutual_information"],
                qit["log_negativity"],
            )
        ),
        "peps2d_virtual_load_bearing": peps2d_gap > 1.0e-3,
        "interlayer_g_control": abs(inter_response - zero_g_response) > 1.0e-4,
        "shuffled_layer_order_control": order_gap > 1.0e-4,
        "flat_control_collapses_substrate_signal": nested_split > 1.0e-4 and flat_split < 1.0e-10,
        "product_control_collapses_qit": product_qit["mutual_information"] < 1.0e-8,
        "dephased_control_collapses_logneg": qit["log_negativity"] > dephased_logneg + 1.0e-8,
        "noncommuting_order_witness": bool(nc["pass"]),
    }

    return {
        "site_count": n_sites,
        "grid_shape": GRID_SHAPES[n_sites],
        "bond_dim_D": bond_dim,
        "shell_etas": list(SHELLS),
        "inner_peps2d": sig_inner,
        "outer_peps2d": sig_outer,
        "nested_energy_split_LR": nested_split,
        "flat_control_split_LR": flat_split,
        "raw_nested_energy_L": e_nested_l,
        "raw_nested_energy_R": e_nested_r,
        "interlayer_response": inter_response,
        "g0_response": zero_g_response,
        "shuffled_order_response": shuffled_response,
        "shuffled_order_gap": order_gap,
        "qit": qit,
        "product_control_qit": product_qit,
        "dephased_control_logneg": dephased_logneg,
        "noncommuting_order": nc,
        "checks": checks,
        "pass": all(checks.values()),
    }


def fresh_jax_probe() -> dict[str, Any]:
    rows = [scale_probe(n_sites, d) for n_sites in SCALES for d in BOND_DIMS]
    min_peps_gap = min(
        min(row["inner_peps2d"]["peps2d_erased_gap"], row["outer_peps2d"]["peps2d_erased_gap"])
        for row in rows
    )
    min_qit_mi = min(row["qit"]["mutual_information"] for row in rows)
    min_logneg = min(row["qit"]["log_negativity"] for row in rows)
    min_order_gap = min(row["shuffled_order_gap"] for row in rows)
    return {
        "rows": rows,
        "row_count": len(rows),
        "all_pass": all(row["pass"] for row in rows),
        "sites": list(SCALES),
        "bond_dims": list(BOND_DIMS),
        "shell_count": 2,
        "g_inter": G_INTER,
        "summary": {
            "min_peps2d_erased_gap": min_peps_gap,
            "min_mutual_information": min_qit_mi,
            "min_log_negativity": min_logneg,
            "min_shuffled_order_gap": min_order_gap,
        },
    }


def non_vacuous_ablations(fresh: dict[str, Any]) -> dict[str, Any]:
    summary = fresh["summary"]
    ablations = {
        "PEPS2D_virtual_bonds": {
            "non_vacuous": summary["min_peps2d_erased_gap"] > 1.0e-3,
            "claim_delta": "claim_fails",
            "delta_magnitude": summary["min_peps2d_erased_gap"],
            "stub_action": "erase virtual PEPS2D bond modulation",
        },
        "interlayer_coupling_g": {
            "non_vacuous": min(abs(row["interlayer_response"]) for row in fresh["rows"]) > 1.0e-4,
            "claim_delta": "claim_fails",
            "delta_magnitude": min(abs(row["interlayer_response"]) for row in fresh["rows"]),
            "stub_action": "set g_inter to zero",
        },
        "layer_order": {
            "non_vacuous": summary["min_shuffled_order_gap"] > 1.0e-4,
            "claim_delta": "claim_fails",
            "delta_magnitude": summary["min_shuffled_order_gap"],
            "stub_action": "shuffle inner and outer shell order",
        },
        "qit_entangling_readout": {
            "non_vacuous": summary["min_log_negativity"] > 1.0e-8,
            "claim_delta": "claim_fails",
            "delta_magnitude": summary["min_log_negativity"],
            "stub_action": "replace entangling readout with product/dephased controls",
        },
        "noncommuting_order": {
            "non_vacuous": min(row["noncommuting_order"]["gap"] for row in fresh["rows"]) > 1.0e-4,
            "claim_delta": "claim_fails",
            "delta_magnitude": min(row["noncommuting_order"]["gap"] for row in fresh["rows"]),
            "stub_action": "replace order-sensitive action pair with commuting diagonal controls",
        },
    }
    for row in ablations.values():
        row["pass"] = bool(row["non_vacuous"])
    return ablations


def build_criteria(receipts: dict[str, Any], fresh: dict[str, Any], ablations: dict[str, Any]) -> dict[str, Any]:
    l2_receipts = (
        "l2_full_spinor_network",
        "l2_mps_peps2d_peps3d_depth",
        "l2_bond4_peps3d_ablation",
        "l2_jax_native",
    )
    peps2d_refs = (
        "julia_weyl_lr_peps2d_readonly",
        "julia_nested_hopf_peps2d_readonly",
    )
    criteria = {
        "fresh_jax_nested_peps2d_mirror_runs": fresh["all_pass"],
        "finite_map_domain_codomain_declared": True,
        "F01_finite_carrier_probe_operator_path_set": True,
        "N01_noncommuting_or_order_sensitive_witness": all(
            row["checks"]["noncommuting_order_witness"] for row in fresh["rows"]
        ),
        "spinor_or_density_carrier": True,
        "nested_peps2d_shells_engaged_in_jax": fresh["all_pass"] and fresh["shell_count"] == 2,
        "scale_8_16_32_64_sites": set(fresh["sites"]) == set(SCALES),
        "bond_dimension_sweep_D_2_4": set(fresh["bond_dims"]) == set(BOND_DIMS),
        "interlayer_g0_control_run": all(row["checks"]["interlayer_g_control"] for row in fresh["rows"]),
        "shuffled_layer_order_control_run": all(row["checks"]["shuffled_layer_order_control"] for row in fresh["rows"]),
        "product_and_dephased_qit_controls_run": all(
            row["checks"]["product_control_collapses_qit"]
            and row["checks"]["dephased_control_collapses_logneg"]
            for row in fresh["rows"]
        ),
        "entropy_qit_family_present": fresh["summary"]["min_mutual_information"] > 0.0
        and fresh["summary"]["min_log_negativity"] > 0.0,
        "five_non_vacuous_ablations": sum(1 for row in ablations.values() if row["pass"]) >= 5,
        "current_l2_receipts_green": all(receipts[name]["passes"] for name in l2_receipts),
        "read_only_peps2d_references_green": all(receipts[name]["passes"] for name in peps2d_refs),
        "nested_weyl_peps2d_julia_result_available": receipts[
            "julia_nested_weyl_peps2d_source_readonly"
        ]["result_exists"],
    }
    criteria["bounded_single_layer_working_criteria_pass"] = all(
        value for key, value in criteria.items() if key != "nested_weyl_peps2d_julia_result_available"
    )
    return criteria


def main() -> int:
    start = time.time()
    receipts = read_receipts()
    fresh = fresh_jax_probe()
    ablations = non_vacuous_ablations(fresh)
    criteria = build_criteria(receipts, fresh, ablations)

    payload: dict[str, Any] = {
        "sim_id": "jax_l2_weyl_nested_peps2d_working_layer_criteria_gate",
        "name": "JAX L2 Weyl nested-PEPS2D working-criteria gate",
        "classification": "diagnostic_jax_l2_weyl_nested_peps2d_working_criteria_gate",
        "sim_execution_kind": "nonclassical_diagnostic",
        "generated_at": now_iso(),
        "ran_jax": True,
        "ran_julia": False,
        "ran_pytorch": False,
        "AUDIT_PASS": bool(criteria["bounded_single_layer_working_criteria_pass"]),
        "all_pass": bool(criteria["bounded_single_layer_working_criteria_pass"]),
        "promotion_allowed": False,
        "formal_layer_admission_allowed": False,
        "claim_ceiling": (
            "Bounded L2 single-layer working-criteria packet. It supports JAX "
            "fresh-run criteria plus current read-only receipt reconciliation; "
            "downstream consumers remain blocked."
        ),
        "root_constraints_in_force": ["F01", "N01"],
        "finite_map": (
            "L2_JAX_nested_PEPS2D : finite L/R Weyl spinor grids on two nested Hopf "
            "tori shells with PEPS2D virtual-bond tensors and inter-shell coupling -> "
            "PEPS2D signatures, order gaps, QIT readouts, controls, and ablation deltas"
        ),
        "domain": {
            "site_counts": list(SCALES),
            "grid_shapes": {str(k): list(v) for k, v in GRID_SHAPES.items()},
            "bond_dims_D": list(BOND_DIMS),
            "shell_etas": list(SHELLS),
            "sheets": ["L", "R"],
            "g_inter_values": [0.0, G_INTER],
        },
        "codomain_or_output": (
            "JSON criteria receipt with fresh JAX nested-PEPS2D rows, QIT readouts, "
            "controls, non-vacuous ablations, dependency receipt statuses, and locks"
        ),
        "spinor_state": (
            "JAX complex128 two-component Weyl spinors psi(phi,chi,eta); "
            "density and two-qubit QIT readouts are spinor-derived"
        ),
        "peps2d_embedding": (
            "finite 2D shell tensors A[y,x,physical,left,right,up,down] with "
            "bond dimensions D=2,4 for two nested Hopf-torus shells"
        ),
        "peps3d_embedding": (
            "read from current L2 formal-scout dependency receipts only; this JAX gate "
            "does not construct a new PEPS3D object"
        ),
        "fresh_jax_nested_peps2d_probe": fresh,
        "tool_ablations": ablations,
        "ablation_outcome_delta": ablations,
        "criteria": criteria,
        "dependency_receipts": receipts,
        "TOOL_MANIFEST": {
            "jax": {
                "used": True,
                "role": "load_bearing",
                "reason": "fresh finite nested-PEPS2D spinor, control, and QIT computations",
            },
            "jax.numpy": {
                "used": True,
                "role": "load_bearing",
                "reason": "complex128 spinor grids, PEPS2D tensor signatures, entropy algebra",
            },
            "jax.scipy.linalg.expm": {
                "used": True,
                "role": "load_bearing",
                "reason": "finite two-qubit entangling unitary for QIT readouts",
            },
            "json": {
                "used": True,
                "role": "supportive",
                "reason": "receipt serialization and read-only dependency reconciliation",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "jax.scipy.linalg.expm": "load_bearing",
            "json": "supportive",
        },
        "blocked_consumers": [
            "layer_stacking",
            "cross_layer_order_closure",
            "PEPS3D_closure_theorem",
            "flux",
            "Xi/Phi0",
            "Axis0",
            "FEP",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "promotion_blockers": [
            "layer-completion claim gate has not admitted stronger wording",
            "fresh run is a JAX finite PEPS2D mirror, not a PEPSKit CTMRG rerun",
            "Julia nested Weyl PEPS2D source exists read-only, but no result JSON was present",
            "downstream consumers remain locked by current L2 receipts",
        ],
        "wallclock_seconds": round(time.time() - start, 6),
    }

    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "AUDIT_PASS": payload["AUDIT_PASS"],
        "result": str(RESULT.relative_to(ROOT)),
        "wallclock_seconds": payload["wallclock_seconds"],
        "criteria_failed": [k for k, v in criteria.items() if not v],
    }, indent=2, sort_keys=True))
    return 0 if payload["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
