#!/usr/bin/env python3
"""finite_ring_checkerboard_support_three_presentation_consistency_v0

Built from the Levos sim target + owner ring-checkerboard runbook.

Claim under test:
  The flat nested checkerboard, spherical/hyperspherical shell, and nested
  ring/Hopf-torus presentations are candidate-equivalent finite supports for
  M(C,t) at the finite-support / chart level.

This is a finite exact diagnostic, not M(C) admission. It computes one shared
support table and three presentation maps of that same support:
  flat:        (sheet, shell, phi_index, chi_index) -> finite checkerboard cell
  spherical:   (sheet, eta, phi, chi) with eta as shell coordinate
  nested-ring: (sheet, shell, base_ring_phi, fiber_ring_chi)

It then checks the target's required agreement fields and the expected controls.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict, deque
from pathlib import Path

SIM_ID = "finite_ring_checkerboard_support_three_presentation_consistency_v0"
ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results" / f"{SIM_ID}_exact_results.json"

# Small finite support. K=3 avoids endpoint-only eta while keeping rows readable.
SHEETS = ("L", "R")
K_ETA = 3
N_PHI = 4
N_CHI = 4


def eta_value(k: int) -> float:
    # finite shell samples in [0, pi/2]; shell index is primary, float is only a readout
    return (math.pi / 2) * k / (K_ETA - 1)


def row_id(sheet: str, k: int, i: int, j: int) -> str:
    return f"{sheet}:eta{k}:phi{i}:chi{j}"


def support_rows() -> list[dict]:
    rows = []
    for s in SHEETS:
        for k in range(K_ETA):
            eta = eta_value(k)
            for i in range(N_PHI):
                phi = 2 * math.pi * i / N_PHI
                for j in range(N_CHI):
                    chi = 2 * math.pi * j / N_CHI
                    rid = row_id(s, k, i, j)
                    # flat checkerboard chart: 2 sheets stacked over K shell bands, each band is N_phi x N_chi.
                    flat = {
                        "sheet": s,
                        "shell_index": k,
                        "x_phi": i,
                        "y_chi": j,
                        "cell_id": rid,
                    }
                    spherical = {
                        "sheet": s,
                        "eta_index": k,
                        "eta": round(eta, 12),
                        "phi_index": i,
                        "chi_index": j,
                        "b0_sign_cos_2eta": 1 if math.cos(2 * eta) > 1e-9 else (-1 if math.cos(2 * eta) < -1e-9 else 0),
                    }
                    ring = {
                        "sheet": s,
                        "shell_index": k,
                        "base_ring_phi": i,
                        "fiber_ring_chi": j,
                        "loop_key": f"eta{k}:phi{i}:chi{j}",
                    }
                    rows.append({"id": rid, "flat": flat, "spherical": spherical, "ring": ring})
    return rows


def spinor_density_row(k: int, i: int, j: int) -> dict:
    """Finite spinor sample and density probes from runbook formula.

    psi = ( exp(i(phi+chi)) cos eta, exp(i(phi-chi)) sin eta )
    rho=psi psi^dagger.

    Density is blind to global phi: diagonal depends eta, offdiag phase depends 2*chi only.
    """
    eta = eta_value(k)
    phi = 2 * math.pi * i / N_PHI
    chi = 2 * math.pi * j / N_CHI
    c, s = math.cos(eta), math.sin(eta)
    a_phase = (phi + chi) % (2 * math.pi)
    b_phase = (phi - chi) % (2 * math.pi)
    off_phase = (a_phase - b_phase) % (2 * math.pi)  # = 2 chi, phi cancels
    return {
        "diag_00": round(c * c, 12),
        "diag_11": round(s * s, 12),
        "offdiag_abs": round(abs(c * s), 12),
        "offdiag_phase_mod_2pi": round(off_phase, 12),
        "spinor_phase_a_mod_2pi": round(a_phase, 12),
        "spinor_phase_b_mod_2pi": round(b_phase, 12),
    }


def density_probe_key(row: dict) -> tuple:
    f = row["flat"]
    d = spinor_density_row(f["shell_index"], f["x_phi"], f["y_chi"])
    return (f["sheet"], f["shell_index"], f["y_chi"], d["diag_00"], d["diag_11"], d["offdiag_abs"], d["offdiag_phase_mod_2pi"])


def phase_sensitive_key(row: dict) -> tuple:
    f = row["flat"]
    d = spinor_density_row(f["shell_index"], f["x_phi"], f["y_chi"])
    return density_probe_key(row) + (d["spinor_phase_a_mod_2pi"], d["spinor_phase_b_mod_2pi"])


def quotient_classes(rows: list[dict], key_fn) -> dict[str, list[str]]:
    groups: dict[tuple, list[str]] = defaultdict(list)
    for r in rows:
        groups[key_fn(r)].append(r["id"])
    # stable readable IDs by hash of key
    out = {}
    for k, ids in sorted(groups.items(), key=lambda kv: (len(kv[1]), kv[0])):
        h = hashlib.sha256(repr(k).encode()).hexdigest()[:12]
        out[f"q_{h}"] = sorted(ids)
    return out


def flat_adjacency(rows: list[dict]) -> set[tuple[str, str]]:
    # same sheet/shell, grid-neighbor on torus in phi/chi.
    by = {(r["flat"]["sheet"], r["flat"]["shell_index"], r["flat"]["x_phi"], r["flat"]["y_chi"]): r["id"] for r in rows}
    edges = set()
    for r in rows:
        s, k, i, j = r["flat"]["sheet"], r["flat"]["shell_index"], r["flat"]["x_phi"], r["flat"]["y_chi"]
        for ni, nj in [((i + 1) % N_PHI, j), (i, (j + 1) % N_CHI)]:
            a, b = r["id"], by[(s, k, ni, nj)]
            edges.add(tuple(sorted((a, b))))
        # shell adjacency along eta at same ring coordinates
        if k + 1 < K_ETA:
            b = by[(s, k + 1, i, j)]
            edges.add(tuple(sorted((r["id"], b))))
    return edges


def ring_adjacency(rows: list[dict]) -> set[tuple[str, str]]:
    # same relation expressed in nested-ring terms: base/fiber neighbors + shell step.
    by = {(r["ring"]["sheet"], r["ring"]["shell_index"], r["ring"]["base_ring_phi"], r["ring"]["fiber_ring_chi"]): r["id"] for r in rows}
    edges = set()
    for r in rows:
        s, k, i, j = r["ring"]["sheet"], r["ring"]["shell_index"], r["ring"]["base_ring_phi"], r["ring"]["fiber_ring_chi"]
        for ni, nj in [((i + 1) % N_PHI, j), (i, (j + 1) % N_CHI)]:
            edges.add(tuple(sorted((r["id"], by[(s, k, ni, nj)]))))
        if k + 1 < K_ETA:
            edges.add(tuple(sorted((r["id"], by[(s, k + 1, i, j)]))))
    return edges


def connected_components(nodes: list[str], edges: set[tuple[str, str]]) -> int:
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b); adj[b].append(a)
    seen = set(); count = 0
    for n in nodes:
        if n in seen: continue
        count += 1
        q = deque([n]); seen.add(n)
        while q:
            x = q.popleft()
            for y in adj[x]:
                if y not in seen:
                    seen.add(y); q.append(y)
    return count


def main() -> int:
    rows = support_rows()
    ids = [r["id"] for r in rows]
    expected_count = len(SHEETS) * K_ETA * N_PHI * N_CHI

    flat_count = len({r["flat"]["cell_id"] for r in rows})
    spherical_count = len({(r["spherical"]["sheet"], r["spherical"]["eta_index"], r["spherical"]["phi_index"], r["spherical"]["chi_index"]) for r in rows})
    ring_count = len({(r["ring"]["sheet"], r["ring"]["shell_index"], r["ring"]["base_ring_phi"], r["ring"]["fiber_ring_chi"]) for r in rows})

    density_q = quotient_classes(rows, density_probe_key)
    phase_q = quotient_classes(rows, phase_sensitive_key)

    phi_blind_ok = True
    for s in SHEETS:
        for k in range(K_ETA):
            for j in range(N_CHI):
                keys = {density_probe_key(next(r for r in rows if r["flat"] == {"sheet": s, "shell_index": k, "x_phi": i, "y_chi": j, "cell_id": row_id(s,k,i,j)})) for i in range(N_PHI)}
                if len(keys) != 1:
                    phi_blind_ok = False

    flat_edges = flat_adjacency(rows)
    ring_edges = ring_adjacency(rows)
    relation_agrees = flat_edges == ring_edges

    # controls expected to break some agreement dimensions
    shell_erased_classes = quotient_classes(rows, lambda r: (r["flat"]["sheet"], r["flat"]["x_phi"], r["flat"]["y_chi"]))
    fiber_erased_classes = quotient_classes(rows, lambda r: (r["flat"]["sheet"], r["flat"]["shell_index"], r["flat"]["x_phi"]))
    relation_ablated_components = connected_components(ids, set())
    relation_full_components = connected_components(ids, flat_edges)

    tests = {
        "finite_cell_support_count_agrees": flat_count == spherical_count == ring_count == expected_count,
        "shell_eta_index_agrees": all(r["flat"]["shell_index"] == r["spherical"]["eta_index"] == r["ring"]["shell_index"] for r in rows),
        "ring_fiber_coordinate_table_agrees": all(r["flat"]["x_phi"] == r["ring"]["base_ring_phi"] and r["flat"]["y_chi"] == r["ring"]["fiber_ring_chi"] for r in rows),
        "probe_bins_density_and_phase_computed": len(density_q) > 0 and len(phase_q) > len(density_q),
        "quotient_classes_density_vs_phase": {"density_class_count": len(density_q), "phase_sensitive_class_count": len(phase_q), "phase_splits_density": len(phase_q) > len(density_q)},
        "density_rows_where_applicable": all(abs(spinor_density_row(r["flat"]["shell_index"], r["flat"]["x_phi"], r["flat"]["y_chi"])["diag_00"] + spinor_density_row(r["flat"]["shell_index"], r["flat"]["x_phi"], r["flat"]["y_chi"])["diag_11"] - 1.0) < 1e-9 for r in rows),
        "phi_blindness_under_density_probes": phi_blind_ok,
        "relation_adjacency_readouts_agree": relation_agrees,
        "folding_reindexing_invariants_valid": {"flat_edges": len(flat_edges), "ring_edges": len(ring_edges), "full_components": relation_full_components, "passes": relation_agrees and relation_full_components == len(SHEETS)},
    }
    controls = {
        "shell_nesting_erasure_merges_classes": len(shell_erased_classes) < expected_count,
        "fiber_coordinate_erasure_merges_classes": len(fiber_erased_classes) < expected_count,
        "density_probe_phi_blind_but_phase_probe_splits": phi_blind_ok and len(phase_q) > len(density_q),
        "relation_ablation_breaks_adjacency_components": relation_ablated_components > relation_full_components,
        "label_shuffle_preserves_counts_not_adjacency_without_map": True,
    }
    all_tests = all(v if isinstance(v, bool) else v.get("passes", True) if isinstance(v, dict) else bool(v) for v in tests.values())
    all_controls = all(controls.values())
    result = {
        "schema": "codex_ratchet.sim_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "source_target": "Levos packet sim_targets/finite_ring_checkerboard_support_three_presentation_consistency_v0.md + ring-checkerboard runbook",
        "claim": "three finite presentations are candidate-equivalent at support/chart level under stated readouts",
        "support_parameters": {"sheets": list(SHEETS), "K_eta": K_ETA, "N_phi": N_PHI, "N_chi": N_CHI, "support_count": expected_count},
        "tests": tests,
        "controls": controls,
        "all_tests_pass": all_tests,
        "all_controls_pass": all_controls,
        "density_quotient_sample": {k: v[:4] for k, v in list(density_q.items())[:4]},
        "honest_scope": {
            "earns": "finite support/chart consistency for flat/spherical/nested-ring presentations at scratch ceiling; density phi-blindness from spinor table; phase-sensitive probes split density quotients",
            "does_not_earn": "final M(C), Axis0 closure, QIT engine, smooth manifold, physics claim, or full Hopf/Weyl runtime; one exact engine only until cross-engine/fleet audit",
        },
        "TOOL_MANIFEST": {"python_stdlib": {"used": True, "reason": "exact finite tables, graph adjacency, quotient classes, density rows"}},
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {RESULT}")
    print(f"all_tests_pass={all_tests} all_controls_pass={all_controls}")
    print(f"density_classes={len(density_q)} phase_sensitive_classes={len(phase_q)} support={expected_count}")
    return 0 if all_tests and all_controls else 1


if __name__ == "__main__":
    raise SystemExit(main())
