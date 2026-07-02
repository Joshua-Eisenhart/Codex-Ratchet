#!/usr/bin/env python3
"""JAX audit for a geometry-is-information admissibility result."""

from __future__ import annotations

import json
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


TOL = 0.3
EPS = 1.0e-6
PARTIAL_PAIR_INFO_SWEEP = (0.10, 0.50, 0.77, 0.89, 0.92, 0.97)
RESULT_PATH = Path(__file__).with_name("jax_geometry_is_information_audit_results.json")


def diagonal_correlated_ac_state(num_pairs: int, theta: jnp.ndarray) -> jnp.ndarray:
    """AC state prod_i(cos(theta)|00> + sin(theta)|11>) in A-block,C-block order."""
    dim = 2**num_pairs
    idx = jnp.arange(dim, dtype=jnp.uint32)
    shifts = jnp.arange(num_pairs, dtype=jnp.uint32)
    bits = (idx[:, None] >> shifts[None, :]) & jnp.uint32(1)
    pop = jnp.sum(bits, axis=1)
    c = jnp.cos(theta)
    s = jnp.sin(theta)
    amps = (c ** (num_pairs - pop)) * (s ** pop)
    mat = jnp.zeros((dim, dim), dtype=jnp.complex128).at[idx, idx].set(
        amps.astype(jnp.complex128)
    )
    return mat.reshape((dim * dim,))


def product_ac_state(num_pairs: int) -> jnp.ndarray:
    """A is |+>^L and C is |0>^L."""
    dim = 2**num_pairs
    a_state = jnp.ones((dim,), dtype=jnp.complex128) / jnp.sqrt(float(dim))
    c_state = jnp.zeros((dim,), dtype=jnp.complex128).at[0].set(1.0 + 0.0j)
    return jnp.kron(a_state, c_state)


def rho_ac_from_3region_state(ac_state: jnp.ndarray, num_pairs: int) -> jnp.ndarray:
    """Embed AC with B=|0...0>, then trace B from the 3L-qubit pure state."""
    dim = 2**num_pairs
    ac_mat = ac_state.reshape((dim, dim))
    psi_abc = jnp.zeros((dim, dim, dim), dtype=jnp.complex128).at[:, 0, :].set(ac_mat)
    rho4 = jnp.einsum("abc,dbe->acde", psi_abc, jnp.conj(psi_abc))
    return rho4.reshape((dim * dim, dim * dim))


def dephase_computational(rho: jnp.ndarray) -> jnp.ndarray:
    return rho * jnp.eye(rho.shape[0], dtype=rho.dtype)


def partial_transpose_c(rho_ac: jnp.ndarray, num_pairs: int) -> jnp.ndarray:
    dim = 2**num_pairs
    rho4 = rho_ac.reshape((dim, dim, dim, dim))
    return jnp.transpose(rho4, (0, 3, 2, 1)).reshape((dim * dim, dim * dim))


def log_negativity(rho_ac: jnp.ndarray, num_pairs: int) -> jnp.ndarray:
    pt = partial_transpose_c(rho_ac, num_pairs)
    hermitian_pt = 0.5 * (pt + jnp.conj(pt.T))
    eigvals = jnp.linalg.eigvalsh(hermitian_pt)
    trace_norm = jnp.sum(jnp.abs(eigvals))
    return jnp.log2(jnp.maximum(trace_norm, jnp.asarray(1.0e-300)))


def genuine_info(num_pairs: int) -> float:
    state = diagonal_correlated_ac_state(num_pairs, jnp.pi / 4.0)
    rho = rho_ac_from_3region_state(state, num_pairs)
    return float(log_negativity(rho, num_pairs))


def theta_for_pair_info(pair_info: jnp.ndarray) -> jnp.ndarray:
    return 0.5 * jnp.arcsin(jnp.power(2.0, pair_info) - 1.0)


def admit_from_gap(geo: float, info: float) -> bool:
    return bool(float(jnp.abs(jnp.asarray(geo) - jnp.asarray(info))) < TOL)


def row(
    *,
    L: int,
    mode: str,
    geo: float,
    info: float,
    family: str,
    theta: float | None = None,
    target_pair_info: float | None = None,
    pre_dephase_info: float | None = None,
) -> dict:
    gap = abs(float(geo) - float(info))
    out = {
        "L": L,
        "mode": mode,
        "geo": float(geo),
        "info": float(info),
        "gap": gap,
        "admit": gap < TOL,
        "family": family,
    }
    if theta is not None:
        out["theta"] = float(theta)
    if target_pair_info is not None:
        out["target_pair_info"] = float(target_pair_info)
    if pre_dephase_info is not None:
        out["pre_dephase_info"] = float(pre_dephase_info)
    return out


def build_base_rows() -> list[dict]:
    rows: list[dict] = []
    for L in (1, 2, 3):
        genuine_state = diagonal_correlated_ac_state(L, jnp.pi / 4.0)
        genuine_rho = rho_ac_from_3region_state(genuine_state, L)
        genuine = float(log_negativity(genuine_rho, L))

        product_rho = rho_ac_from_3region_state(product_ac_state(L), L)
        product = float(log_negativity(product_rho, L))

        dephased_rho = dephase_computational(genuine_rho)
        dephased = float(log_negativity(dephased_rho, L))

        rows.append(row(L=L, mode="genuine", geo=float(L), info=genuine, family="linked"))
        rows.append(row(L=L, mode="product", geo=float(L), info=product, family="linked"))
        rows.append(
            row(
                L=L,
                mode="dephased",
                geo=float(L),
                info=dephased,
                family="linked",
                pre_dephase_info=genuine,
            )
        )
        rows.append(
            row(
                L=L,
                mode="genuine",
                geo=0.0,
                info=genuine,
                family="unlinked_entangled",
            )
        )
    return rows


def build_partial_rows() -> list[dict]:
    rows: list[dict] = []
    pair_infos = jnp.asarray(PARTIAL_PAIR_INFO_SWEEP, dtype=jnp.float64)
    thetas = theta_for_pair_info(pair_infos)
    for L in (1, 2, 3):

        def info_for_theta(theta: jnp.ndarray) -> jnp.ndarray:
            state = diagonal_correlated_ac_state(L, theta)
            rho = rho_ac_from_3region_state(state, L)
            return log_negativity(rho, L)

        infos = jax.vmap(info_for_theta)(thetas)
        for pair_info, theta, info in zip(pair_infos, thetas, infos):
            rows.append(
                row(
                    L=L,
                    mode=f"partial_q={float(pair_info):.2f}",
                    geo=float(L),
                    info=float(info),
                    family="partial_entanglement",
                    theta=float(theta),
                    target_pair_info=float(pair_info),
                )
            )
    return rows


def build_scale_rows() -> list[dict]:
    rows: list[dict] = []
    for L in (1, 2, 3):
        info_2x = float(jnp.asarray(2.0 * L, dtype=jnp.float64))
        info_1x = genuine_info(L)
        rows.append(
            row(
                L=L,
                mode="scale_info_2x",
                geo=float(L),
                info=info_2x,
                family="scale_stress",
            )
        )
        rows.append(
            row(
                L=L,
                mode="scale_geo_2x",
                geo=float(2 * L),
                info=info_1x,
                family="scale_stress",
            )
        )
    return rows


def evaluate(rows: list[dict]) -> dict:
    linked_genuine = [
        r for r in rows if r["family"] == "linked" and r["mode"] == "genuine"
    ]
    linked_no_info = [
        r
        for r in rows
        if r["family"] == "linked" and r["mode"] in {"product", "dephased"}
    ]
    unlinked_entangled = [r for r in rows if r["family"] == "unlinked_entangled"]
    dephased = [r for r in rows if r["mode"] == "dephased"]
    scale_rows = [r for r in rows if r["family"] == "scale_stress"]
    admitted_discordant = [
        r
        for r in rows
        if r["family"] == "partial_entanglement"
        and r["admit"]
        and r["gap"] > EPS
    ]
    survivors = [r for r in rows if r["admit"]]

    checks = {
        "genuine_linked_all_admitted": all(r["admit"] for r in linked_genuine),
        "product_and_dephased_linked_all_pruned": all(
            not r["admit"] for r in linked_no_info
        ),
        "unlinked_entangled_all_pruned": all(not r["admit"] for r in unlinked_entangled),
        "every_survivor_within_tol": all(r["gap"] < TOL for r in survivors),
        "dephased_info_zero_and_pre_dephase_info_L": all(
            abs(r["info"]) < EPS and abs(r["pre_dephase_info"] - r["L"]) < EPS
            for r in dephased
        ),
        "scale_rows_all_pruned": all(not r["admit"] for r in scale_rows),
        "tol_band_admits_geo_not_equal_info": len(admitted_discordant) > 0,
    }
    circularity_verdict = (
        "planted"
        if checks["scale_rows_all_pruned"]
        and checks["tol_band_admits_geo_not_equal_info"]
        else "genuine"
    )
    checks["circularity_verdict_is_planted"] = circularity_verdict == "planted"
    audit_pass = all(checks.values())

    return {
        "survivors": survivors,
        "checks": checks,
        "bidirectional_result": {
            "linked_genuine_admitted": checks["genuine_linked_all_admitted"],
            "geometry_without_information_pruned": checks[
                "product_and_dephased_linked_all_pruned"
            ],
            "information_without_geometry_pruned": checks[
                "unlinked_entangled_all_pruned"
            ],
            "unlinked_entangled_futures": unlinked_entangled,
        },
        "circularity": {
            "admitted_but_discordant_states": admitted_discordant,
            "scale_rows": scale_rows,
            "tol_band_admits_geo_not_equal_info": checks[
                "tol_band_admits_geo_not_equal_info"
            ],
            "verdict": circularity_verdict,
            "verdict_reason": (
                "geo and info meet on planted slope-1 L rows; the tolerance band "
                "admits discordant partial-entanglement futures, while scale changes "
                "in either direction prune."
            ),
        },
        "AUDIT_PASS": audit_pass,
        "CIRCULARITY_VERDICT": circularity_verdict,
    }


def print_table(rows: list[dict], audit_pass: bool, circularity_verdict: str) -> None:
    print(f"{'L':>1}  {'mode':<16} {'geo':>7} {'info':>10} {'gap':>10} {'admit':>5}")
    for r in rows:
        print(
            f"{r['L']:>1}  {r['mode']:<16} "
            f"{r['geo']:>7.3f} {r['info']:>10.6f} {r['gap']:>10.6f} "
            f"{str(r['admit']):>5}"
        )
    print(f"AUDIT_PASS={audit_pass}")
    print(f"CIRCULARITY_VERDICT={circularity_verdict}")


def main() -> None:
    rows = build_base_rows() + build_partial_rows() + build_scale_rows()
    evaluation = evaluate(rows)
    receipt = {
        "audit": "jax_geometry_is_information_audit",
        "tol": TOL,
        "futures": rows,
        "survivors": evaluation["survivors"],
        "bidirectional_result": evaluation["bidirectional_result"],
        "circularity": evaluation["circularity"],
        "checks": evaluation["checks"],
        "AUDIT_PASS": evaluation["AUDIT_PASS"],
        "CIRCULARITY_VERDICT": evaluation["CIRCULARITY_VERDICT"],
    }
    RESULT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print_table(rows, evaluation["AUDIT_PASS"], evaluation["CIRCULARITY_VERDICT"])


if __name__ == "__main__":
    main()
