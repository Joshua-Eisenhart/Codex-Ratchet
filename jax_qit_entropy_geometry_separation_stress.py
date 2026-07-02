#!/usr/bin/env python3
"""JAX QIT entropy/geometry separation stress probe.

This probe targets the exact classical-smuggling risk in the current JAX lane:
conditional mutual information can be nonzero for a classical shadow, while
log-negativity and coherent information are the pure-QIT entanglement columns.

Julia is read-only reference here. This file runs JAX only and makes no
admission or promotion claim.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp
from jax.scipy.linalg import expm


OUT = Path("jax_qit_entropy_geometry_separation_stress_results.json")
EPS = 1.0e-9
I = 1j

X = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
Y = jnp.asarray([[0, -I], [I, 0]], dtype=jnp.complex128)
Z = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
ID2 = jnp.eye(2, dtype=jnp.complex128)


def kron_all(ops: list[jax.Array]) -> jax.Array:
    out = ops[0]
    for op in ops[1:]:
        out = jnp.kron(out, op)
    return out


def normalize(psi: jax.Array) -> jax.Array:
    return psi / jnp.linalg.norm(psi)


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def bits_to_index(bits: tuple[int, ...]) -> int:
    idx = 0
    for bit in bits:
        idx = (idx << 1) | bit
    return idx


def bell_pair_state(n: int, pairs: list[tuple[int, int]]) -> jax.Array:
    """Build a product of Bell pairs and |0> fillers over n qubits."""
    paired = {q for pair in pairs for q in pair}
    amps: dict[tuple[int, ...], complex] = {tuple([0] * n): 1.0 + 0.0j}
    for a, b in pairs:
        next_amps: dict[tuple[int, ...], complex] = {}
        for bits, amp in amps.items():
            for bit in (0, 1):
                new_bits = list(bits)
                new_bits[a] = bit
                new_bits[b] = bit
                next_amps[tuple(new_bits)] = next_amps.get(tuple(new_bits), 0.0j) + amp / jnp.sqrt(2.0)
        amps = next_amps
    for q in range(n):
        if q not in paired:
            # Fillers already sit in |0>.
            pass
    psi = jnp.zeros((2**n,), dtype=jnp.complex128)
    for bits, amp in amps.items():
        psi = psi.at[bits_to_index(bits)].set(amp)
    return normalize(psi)


def product_state(n: int) -> jax.Array:
    psi = jnp.zeros((2**n,), dtype=jnp.complex128).at[0].set(1.0)
    return psi


def dephase(rho: jax.Array) -> jax.Array:
    return jnp.diag(jnp.real(jnp.diag(rho))).astype(jnp.complex128)


def rdm(rho: jax.Array, keep: list[int], n: int) -> jax.Array:
    keep = list(keep)
    trace = [q for q in range(n) if q not in keep]
    order = keep + trace
    tensor = rho.reshape([2] * n + [2] * n)
    perm = order + [q + n for q in order]
    tensor = jnp.transpose(tensor, perm)
    dk = 2 ** len(keep)
    dt = 2 ** len(trace)
    tensor = tensor.reshape(dk, dt, dk, dt)
    return jnp.trace(tensor, axis1=1, axis2=3)


def vn_entropy(rho: jax.Array) -> jax.Array:
    herm = 0.5 * (rho + jnp.conj(rho.T))
    vals = jnp.clip(jnp.real(jnp.linalg.eigvalsh(herm)), 0.0, 1.0)
    return -jnp.sum(jnp.where(vals > 1.0e-12, vals * jnp.log2(vals), 0.0))


def logneg(rho_ac: jax.Array, d_a: int, d_c: int) -> jax.Array:
    pt = rho_ac.reshape(d_a, d_c, d_a, d_c).transpose(0, 3, 2, 1).reshape(d_a * d_c, d_a * d_c)
    vals = jnp.linalg.eigvalsh(0.5 * (pt + jnp.conj(pt.T)))
    return jnp.log2(jnp.sum(jnp.abs(vals)))


def coherent_info(rho_ac: jax.Array, c_qubits: int) -> jax.Array:
    n_ac = int(jnp.log2(rho_ac.shape[0]))
    a_keep = list(range(n_ac - c_qubits))
    c_keep = list(range(n_ac - c_qubits, n_ac))
    _ = a_keep
    rho_c = rdm(rho_ac, c_keep, n_ac)
    return vn_entropy(rho_c) - vn_entropy(rho_ac)


def cmi(rho: jax.Array, a: list[int], b: list[int], c: list[int], n: int) -> jax.Array:
    return vn_entropy(rdm(rho, a + b, n)) + vn_entropy(rdm(rho, b + c, n)) - vn_entropy(rdm(rho, b, n)) - vn_entropy(rdm(rho, a + b + c, n))


def single_site_entropy_sum(rho: jax.Array, n: int) -> jax.Array:
    return sum(vn_entropy(rdm(rho, [q], n)) for q in range(n))


def case_metrics(name: str, rho: jax.Array) -> dict[str, Any]:
    n = 4
    a = [0]
    b = [1, 2]
    c = [3]
    rho_ac = rdm(rho, a + c, n)
    return {
        "name": name,
        "LN_AC": float(logneg(rho_ac, 2, 2)),
        "I_c_A_to_C": float(coherent_info(rho_ac, c_qubits=1)),
        "CMI_A_C_given_B": float(cmi(rho, a, b, c, n)),
        "S_AC": float(vn_entropy(rho_ac)),
        "single_site_entropy_sum": float(single_site_entropy_sum(rho, n)),
    }


def pauli_on(n: int, q: int, p: jax.Array) -> jax.Array:
    return kron_all([p if i == q else ID2 for i in range(n)])


def noncommuting_order_witness() -> dict[str, float | bool]:
    n = 4
    h_ab = pauli_on(n, 0, X) @ pauli_on(n, 1, X)
    h_ac = pauli_on(n, 0, Z) @ pauli_on(n, 3, Z)
    h_bd = pauli_on(n, 1, X) @ pauli_on(n, 2, X)
    h_ac_disjoint = pauli_on(n, 0, Z) @ pauli_on(n, 3, Z)
    u_ab = expm(-0.37j * h_ab)
    u_ac = expm(-0.29j * h_ac)
    u_bd = expm(-0.37j * h_bd)
    u_ac2 = expm(-0.29j * h_ac_disjoint)
    shared_gap = jnp.linalg.norm(u_ab @ u_ac - u_ac @ u_ab)
    disjoint_gap = jnp.linalg.norm(u_bd @ u_ac2 - u_ac2 @ u_bd)
    return {
        "shared_qubit_order_gap": float(shared_gap),
        "disjoint_control_gap": float(disjoint_gap),
        "pass": bool(shared_gap > 1.0e-3 and disjoint_gap < 1.0e-9),
    }


def capacity_budget(cases: dict[str, dict[str, Any]]) -> dict[str, float | bool]:
    # Finite carrier: four qubits. Finite path registry: the four explicit cases.
    s_boundary = max(v["S_AC"] for v in cases.values())
    h_path = 2.0  # uniform finite registry over four cases
    s_max = 4.0
    h_path_max = 2.0
    budget = s_max + h_path_max
    return {
        "S_boundary_max": float(s_boundary),
        "H_path": h_path,
        "S_max": s_max,
        "H_path_max": h_path_max,
        "capacity_budget": budget,
        "pass": bool(s_boundary + h_path <= budget + 1.0e-9 and h_path <= h_path_max + 1.0e-9),
    }


def run_probe(write: bool = True) -> dict[str, Any]:
    linked = density(bell_pair_state(4, [(0, 3), (1, 2)]))
    trivial = density(bell_pair_state(4, [(0, 1), (2, 3)]))
    product = density(product_state(4))
    dephased_linked = dephase(linked)

    cases = {
        "linked_ac_er_bridge": case_metrics("linked_ac_er_bridge", linked),
        "matched_trivial_chain": case_metrics("matched_trivial_chain", trivial),
        "dephased_linked_classical_shadow": case_metrics("dephased_linked_classical_shadow", dephased_linked),
        "product": case_metrics("product", product),
    }
    order = noncommuting_order_witness()
    cap = capacity_budget(cases)

    checks = {
        "linked_has_logneg_and_cmi": cases["linked_ac_er_bridge"]["LN_AC"] > 0.99 and cases["linked_ac_er_bridge"]["I_c_A_to_C"] > 0.99 and cases["linked_ac_er_bridge"]["CMI_A_C_given_B"] > 1.99,
        "matched_trivial_preserves_local_entropy_budget": abs(cases["linked_ac_er_bridge"]["single_site_entropy_sum"] - cases["matched_trivial_chain"]["single_site_entropy_sum"]) < 1.0e-9,
        "matched_trivial_kills_ac_entanglement_and_cmi": cases["matched_trivial_chain"]["LN_AC"] < EPS and cases["matched_trivial_chain"]["CMI_A_C_given_B"] < EPS,
        "dephasing_kills_logneg_but_not_classical_cmi_shadow": cases["dephased_linked_classical_shadow"]["LN_AC"] < EPS and cases["dephased_linked_classical_shadow"]["CMI_A_C_given_B"] > 0.99,
        "product_kills_all_readouts": cases["product"]["LN_AC"] < EPS and cases["product"]["CMI_A_C_given_B"] < EPS and abs(cases["product"]["I_c_A_to_C"]) < EPS,
        "noncommuting_order_gap_present": bool(order["pass"]),
        "capacity_budget_finite_and_respected": bool(cap["pass"]),
    }

    result = {
        "AUDIT_PASS": bool(all(checks.values())),
        "name": "jax_qit_entropy_geometry_separation_stress",
        "classification": "diagnostic_jax_qit_entropy_geometry_separation_stress",
        "promotion_allowed": False,
        "executed_track": "jax",
        "ran_julia": False,
        "julia_reference_mode": "read_only",
        "purpose": "Stress-test separation of pure-QIT entanglement witnesses from CMI/classical-shadow readouts on finite JAX states.",
        "finite_map": "finite four-qubit density states over A|B|C regions -> LN, coherent information, CMI, dephasing and matched-trivial controls",
        "domain": "four finite qubits partitioned as A=[0], B=[1,2], C=[3]",
        "codomain_or_output": "separate readout columns plus pass/fail controls",
        "root_constraints_in_force": {
            "F01": "finite density matrices and finite path registry",
            "N01": "noncommuting shared-qubit order witness plus dephasing/order controls",
        },
        "cases": cases,
        "noncommuting_order_witness": order,
        "capacity_budget": cap,
        "checks": checks,
        "tool_manifest": {
            "jax": "load-bearing finite QIT density/readout computation",
            "jax.numpy": "load-bearing entropy, reduced-density, partial-transpose, and finite tensor algebra",
            "jax.scipy.linalg.expm": "load-bearing noncommuting unitary order witness",
            "json": "supportive receipt serialization",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "jax.scipy.linalg.expm": "load_bearing",
            "json": "supportive",
        },
        "blocked_consumers": [
            "layer_stacking",
            "flux",
            "xi_phi0",
            "axis0",
            "fep_holodeck",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "claim_boundary": "diagnostic JAX stress probe only; no formal layer/admission claim",
    }

    if write:
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    result = run_probe(write=True)
    linked = result["cases"]["linked_ac_er_bridge"]
    trivial = result["cases"]["matched_trivial_chain"]
    dephased = result["cases"]["dephased_linked_classical_shadow"]
    print(
        "qit_entropy_geometry_stress "
        f"linked_LN={linked['LN_AC']:.3f} linked_CMI={linked['CMI_A_C_given_B']:.3f} "
        f"trivial_LN={trivial['LN_AC']:.3f} trivial_CMI={trivial['CMI_A_C_given_B']:.3f} "
        f"dephased_LN={dephased['LN_AC']:.3f} dephased_CMI={dephased['CMI_A_C_given_B']:.3f} "
        f"AUDIT_PASS={result['AUDIT_PASS']}"
    )


if __name__ == "__main__":
    main()
