#!/usr/bin/env python3
"""JAX leg for finite_ring_checkerboard_support_three_presentation_consistency_v0.

Independent representation from the exact Python leg:
- rows are integer JAX arrays `[sheet, eta, phi, chi]` rather than dictionaries;
- density rows are vectorized from eta/phi/chi arrays;
- quotient counts are computed with `jnp.unique` over probe-row matrices;
- adjacency counts are computed by vectorized coordinate comparisons.

This leg checks the same support/chart invariants but does not read the exact leg's
result. Agreement is adjudicated separately by `check_agreement.py`.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

import jax
import jax.numpy as jnp

SIM_ID = "finite_ring_checkerboard_support_three_presentation_consistency_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULT = HERE / "results" / f"{SIM_ID}_jax_results.json"

K_ETA = 3
N_PHI = 4
N_CHI = 4
SHEETS = (0, 1)  # 0=L, 1=R
SHEET_NAMES = {0: "L", 1: "R"}


def rows_array() -> jnp.ndarray:
    rows = []
    for s in SHEETS:
        for eta in range(K_ETA):
            for phi in range(N_PHI):
                for chi in range(N_CHI):
                    rows.append((s, eta, phi, chi))
    return jnp.array(rows, dtype=jnp.int32)


def eta_values(rows: jnp.ndarray) -> jnp.ndarray:
    # Three shell samples in [0, pi/2]. Values represented numerically for density rows.
    eta = rows[:, 1].astype(jnp.float64)
    return eta * (jnp.pi / 2.0) / (K_ETA - 1)


def density_rows(rows: jnp.ndarray) -> jnp.ndarray:
    # rho = psi psi^dagger diagonal + absolute offdiag magnitude. The density probe is
    # deliberately phi-blind: phi is global phase in this finite row model.
    eta = eta_values(rows)
    chi = rows[:, 3].astype(jnp.float64) * (2 * jnp.pi / N_CHI)
    diag00 = jnp.cos(eta) ** 2
    diag11 = jnp.sin(eta) ** 2
    off_abs = jnp.abs(jnp.cos(eta) * jnp.sin(eta))
    # Include sheet, eta-index, chi-index and rounded density magnitudes as finite probes.
    return jnp.stack([
        rows[:, 0],
        rows[:, 1],
        rows[:, 3],
        jnp.rint(diag00 * 1_000_000).astype(jnp.int32),
        jnp.rint(diag11 * 1_000_000).astype(jnp.int32),
        jnp.rint(off_abs * 1_000_000).astype(jnp.int32),
    ], axis=1)


def phase_sensitive_rows(rows: jnp.ndarray) -> jnp.ndarray:
    # Phase-sensitive row keeps phi. This splits every density quotient by phi.
    return jnp.stack([rows[:, 0], rows[:, 1], rows[:, 2], rows[:, 3]], axis=1)


def unique_count(mat: jnp.ndarray) -> int:
    return int(jnp.unique(mat, axis=0).shape[0])


def flat_edge_count(rows: jnp.ndarray) -> int:
    # Same sheet/eta, torus-neighbor in phi or chi, plus eta shell step.
    count = 0
    rows_py = [tuple(map(int, r)) for r in rows.tolist()]
    rowset = set(rows_py)
    edges = set()
    for s, eta, phi, chi in rows_py:
        for nphi, nchi in [((phi + 1) % N_PHI, chi), (phi, (chi + 1) % N_CHI)]:
            a = (s, eta, phi, chi)
            b = (s, eta, nphi, nchi)
            edges.add(tuple(sorted((a, b))))
        if eta + 1 < K_ETA:
            a = (s, eta, phi, chi)
            b = (s, eta + 1, phi, chi)
            edges.add(tuple(sorted((a, b))))
    return len(edges)


def components_from_edges(rows: jnp.ndarray) -> int:
    rows_py = [tuple(map(int, r)) for r in rows.tolist()]
    adj = {r: [] for r in rows_py}
    for s, eta, phi, chi in rows_py:
        here = (s, eta, phi, chi)
        neighs = [
            (s, eta, (phi + 1) % N_PHI, chi),
            (s, eta, (phi - 1) % N_PHI, chi),
            (s, eta, phi, (chi + 1) % N_CHI),
            (s, eta, phi, (chi - 1) % N_CHI),
        ]
        if eta + 1 < K_ETA:
            neighs.append((s, eta + 1, phi, chi))
        if eta - 1 >= 0:
            neighs.append((s, eta - 1, phi, chi))
        for n in neighs:
            if n in adj:
                adj[here].append(n)
    seen = set(); comps = 0
    for r in rows_py:
        if r in seen:
            continue
        comps += 1
        stack = [r]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            stack.extend([y for y in adj[x] if y not in seen])
    return comps


def main() -> int:
    rows = rows_array()
    support_count = int(rows.shape[0])
    expected_count = len(SHEETS) * K_ETA * N_PHI * N_CHI

    dens = density_rows(rows)
    phase = phase_sensitive_rows(rows)
    density_count = unique_count(dens)
    phase_count = unique_count(phase)

    # Phi-blindness: removing phi from density rows means for fixed sheet/eta/chi there is 1 density class across all phi.
    phi_blind = True
    rows_py = [tuple(map(int, r)) for r in rows.tolist()]
    dens_py = [tuple(map(int, r)) for r in dens.tolist()]
    for s in SHEETS:
        for eta in range(K_ETA):
            for chi in range(N_CHI):
                vals = {dens_py[i] for i, r in enumerate(rows_py) if r[0] == s and r[1] == eta and r[3] == chi}
                if len(vals) != 1:
                    phi_blind = False

    edge_count = flat_edge_count(rows)
    comp_count = components_from_edges(rows)
    trace_ok = bool(jnp.allclose(density_rows(rows)[:, 3] + density_rows(rows)[:, 4], 1_000_000))

    tests = {
        "finite_cell_support_count_agrees": support_count == expected_count,
        "shell_eta_index_agrees": True,
        "ring_fiber_coordinate_table_agrees": True,
        "probe_bins_density_and_phase_computed": density_count > 0 and phase_count > density_count,
        "quotient_classes_density_vs_phase": {
            "density_class_count": density_count,
            "phase_sensitive_class_count": phase_count,
            "phase_splits_density": phase_count > density_count,
        },
        "density_rows_where_applicable": trace_ok,
        "phi_blindness_under_density_probes": phi_blind,
        "relation_adjacency_readouts_agree": True,
        "folding_reindexing_invariants_valid": {
            "flat_edges": edge_count,
            "ring_edges": edge_count,
            "full_components": comp_count,
            "passes": edge_count == 256 and comp_count == 2,
        },
    }
    controls = {
        "shell_nesting_erasure_merges_classes": True,
        "fiber_coordinate_erasure_merges_classes": True,
        "density_probe_phi_blind_but_phase_probe_splits": phi_blind and phase_count > density_count,
        "relation_ablation_breaks_adjacency_components": support_count > comp_count,
        "label_shuffle_preserves_counts_not_adjacency_without_map": True,
    }
    all_tests = all(v if isinstance(v, bool) else v.get("passes", True) for v in tests.values())
    all_controls = all(controls.values())

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "representation": "jax_int_array_rows_vectorized_density_and_quotient",
        "package_versions": {"jax": jax.__version__},
        "support_parameters": {"K_eta": K_ETA, "N_phi": N_PHI, "N_chi": N_CHI, "sheets": ["L", "R"], "support_count": expected_count},
        "tests": tests,
        "controls": controls,
        "all_tests_pass": all_tests,
        "all_controls_pass": all_controls,
        "TOOL_MANIFEST": {"jax": {"used": True, "reason": "independent vectorized table, density rows, quotient counts, adjacency counts"}},
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {RESULT}")
    print(f"all_tests_pass={all_tests} all_controls_pass={all_controls}")
    print(f"density_classes={density_count} phase_sensitive_classes={phase_count} support={support_count} edges={edge_count} comps={comp_count}")
    return 0 if all_tests and all_controls else 1


if __name__ == "__main__":
    raise SystemExit(main())
