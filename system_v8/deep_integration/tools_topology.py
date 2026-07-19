#!/usr/bin/env python3
"""v8 deep-integration lane: topology (gudhi + toponetx + rustworkx/networkx).

UNOFFICIAL working-sim bar, NOT proof-level. promotion_allowed: false.

Three sub-lanes, each with a package whose computation DECIDES the verdict:

1) gudhi (load-bearing): Vietoris-Rips persistence.
   (a) 384-state Bloch census point cloud pushed to final states under three
       damping-terrain surrogate flows (declared in-script, working-sim bar):
         - pit terrain: two damping wells at the Bloch poles (basin = sign(z))
         - source terrain: four equatorial wells at +/-x, +/-y (basin = nearest)
         - depolarizing: uniform contraction toward the maximally mixed center
       H0 persistence at scale 0.5 must recover the basin count (2 / 4 / 1);
       depolarizing must collapse to 1 cluster. A persistence-gap check
       (basin-separating H0 bars >= 10x intra-cluster bars) must also hold.
   (b) precession-orbit trajectory cloud (Bloch vector precessing about z,
       fixed polar angle pi/3, 200 ticks): H1 must detect the loop
       (betti_1 >= 1 at scale, max H1 persistence > 3x scrambled control and
       > 0.75). Scrambled control (fixed-seed independent per-axis coordinate
       permutation — NOT a point reorder, which VR ignores) must kill the
       H1 loop signal (< 0.5 and < loop/3).

2) toponetx (load-bearing): nested-leaf strip as a combinatorial 2-complex.
   Two leaves x 16 discretized loop points; edges = leaf links + rungs;
   faces = 16 plaquettes. Euler characteristic (toponetx's own method AND
   V-E+F from the toponetx object) must equal 0 (annulus) and hodge-Laplacian
   betti numbers must be (1,1,0). Flattened control (single leaf cut open —
   flattening kills the loop, matching the flux_flat=0 convention): chi = 1,
   betti_1 = 0, differs from the annulus.

3) rustworkx + networkx (both load-bearing): per-packet Hamming-1 capacity
   graph from source_packets accepted_words (same construction as the torch
   lane). Laplacian spectral gap (2nd smallest eigenvalue) and component
   counts computed independently through BOTH libraries' graph objects must
   agree bitwise with each other AND bitwise/exactly with the torch receipt.

numpy is substrate-only (point-cloud generation, eigvalsh backend); no check
verdict rests on a numpy-only quantity. No heavy stack (torch/jax/julia) is
loaded — torch values are read from its receipt JSON.
"""

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "results", "topology")
SRC_PACKETS = "/Users/joshuaeisenhart/Codex-Ratchet/system_v8/manifold/results/source_packets.json"
TORCH_RECEIPT = "/Users/joshuaeisenhart/Codex-Ratchet/system_v8/engine_native/results/torch_graph/receipt.json"

if os.path.exists(OUTDIR):
    sys.exit(f"REFUSE-TO-REUSE: outdir already exists: {OUTDIR} — move or delete it explicitly first.")
os.makedirs(OUTDIR)

checks = {}
data = {}
findings = []

# ----------------------------------------------------------------------------
# Lane 1: gudhi
# ----------------------------------------------------------------------------
import gudhi

def fibonacci_sphere(n):
    i = np.arange(n) + 0.5
    z = 1.0 - 2.0 * i / n
    r = np.sqrt(1.0 - z * z)
    phi = np.pi * (1.0 + 5.0 ** 0.5) * i
    return np.stack([r * np.cos(phi), r * np.sin(phi), z], axis=1)

N_CENSUS = 384
LAM = 0.12            # residual spread factor after finite-time damping
H0_SCALE = 0.5        # cluster-count readout scale
census = fibonacci_sphere(N_CENSUS)

# pit terrain: two wells at the poles
att_pit = np.array([[0.0, 0.0, 1.0], [0.0, 0.0, -1.0]])
a = att_pit[(census[:, 2] < 0).astype(int)]
final_pit = a + LAM * (census - a)
# source terrain: four equatorial wells
att_src = np.array([[1.0, 0, 0], [0, 1.0, 0], [-1.0, 0, 0], [0, -1.0, 0]])
idx = np.argmax(census @ att_src.T, axis=1)
final_src = att_src[idx] + LAM * (census - att_src[idx])
# depolarizing: uniform contraction to center
final_dep = 0.15 * census

def h0_diagram(points):
    st = gudhi.RipsComplex(points=points, max_edge_length=2.5).create_simplex_tree(max_dimension=1)
    st.compute_persistence()
    return st.persistence_intervals_in_dimension(0)

def basin_readout(d0, scale):
    """gudhi-decided: components at `scale` = H0 bars with death > scale (inf bar included)."""
    deaths = d0[:, 1]
    count = int(np.sum(deaths > scale))
    finite = np.sort(deaths[np.isfinite(deaths)])
    return count, finite

terrains = {}
for name, pts, expected in [("pit", final_pit, 2), ("source", final_src, 4), ("depolarizing", final_dep, 1)]:
    d0 = h0_diagram(pts)
    count, finite = basin_readout(d0, H0_SCALE)
    sep_bars = finite[finite > H0_SCALE]          # basin-separating finite bars
    intra_bars = finite[finite <= H0_SCALE]       # intra-cluster merges
    gap_ratio = (float(sep_bars.min()) / float(intra_bars.max())) if (len(sep_bars) and len(intra_bars)) else None
    terrains[name] = {
        "expected_basins": expected,
        "h0_count_at_scale_0p5": count,
        "n_finite_bars": int(len(finite)),
        "max_intra_cluster_death": float(intra_bars.max()) if len(intra_bars) else None,
        "min_separating_death": float(sep_bars.min()) if len(sep_bars) else None,
        "persistence_gap_ratio": gap_ratio,
    }

checks["gudhi_h0_pit_terrain_basins_eq_2"] = terrains["pit"]["h0_count_at_scale_0p5"] == 2
checks["gudhi_h0_source_terrain_basins_eq_4"] = terrains["source"]["h0_count_at_scale_0p5"] == 4
checks["gudhi_h0_depolarizing_collapses_to_1"] = terrains["depolarizing"]["h0_count_at_scale_0p5"] == 1
checks["gudhi_h0_persistence_gap_ge_10x_pit_and_source"] = all(
    terrains[t]["persistence_gap_ratio"] is not None and terrains[t]["persistence_gap_ratio"] >= 10.0
    for t in ("pit", "source")
)

# (b) precession orbit H1
N_ORBIT = 200
theta0 = np.pi / 3.0
phi = 2.0 * np.pi * np.arange(N_ORBIT) / N_ORBIT
r0, z0 = np.sin(theta0), np.cos(theta0)
orbit = np.stack([r0 * np.cos(phi), r0 * np.sin(phi), np.full(N_ORBIT, z0)], axis=1)

def h1_max_persistence(points):
    st = gudhi.RipsComplex(points=points, max_edge_length=2.0).create_simplex_tree(max_dimension=2)
    st.compute_persistence()
    d1 = st.persistence_intervals_in_dimension(1)
    if len(d1) == 0:
        return 0.0, 0
    pers = d1[:, 1] - d1[:, 0]
    pers = pers[np.isfinite(pers)]
    return (float(pers.max()) if len(pers) else 0.0), int(len(d1))

rng = np.random.default_rng(0)
scrambled = orbit.copy()
scrambled[:, 0] = scrambled[rng.permutation(N_ORBIT), 0]
scrambled[:, 1] = scrambled[rng.permutation(N_ORBIT), 1]

h1_loop, n_bars_loop = h1_max_persistence(orbit)
h1_scr, n_bars_scr = h1_max_persistence(scrambled)
data["precession_h1"] = {
    "n_points": N_ORBIT,
    "orbit_radius": float(r0),
    "loop_max_h1_persistence": h1_loop,
    "loop_n_h1_bars": n_bars_loop,
    "scrambled_max_h1_persistence": h1_scr,
    "scrambled_n_h1_bars": n_bars_scr,
    "loop_over_scrambled_ratio": (h1_loop / h1_scr) if h1_scr > 0 else None,
    "scramble_convention": "fixed-seed(0) independent per-axis coordinate permutation (x, y); a point reorder would be VR-invariant and is NOT a control",
}
checks["gudhi_h1_precession_loop_betti1_ge_1"] = (h1_loop > 0.75) and (h1_loop > 3.0 * h1_scr)
checks["gudhi_h1_scramble_control_kills_loop"] = (h1_scr < 0.5) and (h1_scr < h1_loop / 3.0)

data["bloch_census_terrains"] = terrains
findings.append(
    f"gudhi H0 basin readout at scale 0.5: pit={terrains['pit']['h0_count_at_scale_0p5']} "
    f"source={terrains['source']['h0_count_at_scale_0p5']} depolarizing={terrains['depolarizing']['h0_count_at_scale_0p5']}; "
    f"H1: loop {h1_loop:.4f} vs scrambled {h1_scr:.4f}"
)

# ----------------------------------------------------------------------------
# Lane 2: toponetx
# ----------------------------------------------------------------------------
from toponetx.classes import CellComplex

N_LEAF = 16
annulus = CellComplex()
for i in range(N_LEAF):
    j = (i + 1) % N_LEAF
    # plaquette between leaf-1 (0..15) and leaf-2 (16..31); boundary covers
    # both leaf-loop edges and the two rungs
    annulus.add_cell([i, j, j + N_LEAF, i + N_LEAF], rank=2)

V_a, E_a, F_a = len(annulus.nodes), len(annulus.edges), len(annulus.cells)
chi_a_counts = V_a - E_a + F_a
chi_a_method = int(annulus.euler_characterisitics())  # toponetx's own (misspelled) method

def betti_from_hodge(cc, max_rank):
    bettis = []
    for r in range(max_rank + 1):
        L = cc.hodge_laplacian_matrix(rank=r)
        Ld = L.toarray() if hasattr(L, "toarray") else np.asarray(L)
        bettis.append(int(Ld.shape[0] - np.linalg.matrix_rank(Ld)))
    return bettis

betti_a = betti_from_hodge(annulus, 2)

# flattened control: single leaf, cut open (flattening kills the loop), no faces
control = CellComplex()
for i in range(N_LEAF - 1):
    control.add_cell([i, i + 1], rank=1)
V_c, E_c, F_c = len(control.nodes), len(control.edges), len(control.cells)
chi_c_counts = V_c - E_c + F_c
chi_c_method = int(control.euler_characterisitics())
betti_c = betti_from_hodge(control, 1)

data["nested_leaf_strip"] = {
    "annulus": {"V": V_a, "E": E_a, "F": F_a, "chi_counts": chi_a_counts,
                "chi_toponetx_method": chi_a_method, "betti_hodge": betti_a},
    "flattened_control": {"V": V_c, "E": E_c, "F": F_c, "chi_counts": chi_c_counts,
                          "chi_toponetx_method": chi_c_method, "betti_hodge": betti_c},
}
checks["toponetx_annulus_chi_eq_0_both_methods"] = (chi_a_counts == 0) and (chi_a_method == 0)
checks["toponetx_annulus_betti_1_1_0"] = betti_a == [1, 1, 0]
checks["toponetx_flattened_control_differs"] = (
    chi_c_counts == 1 and chi_c_method == 1 and chi_c_counts != chi_a_counts and betti_c == [1, 0]
)
findings.append(
    f"toponetx nested-leaf strip: chi={chi_a_method} betti={betti_a} (annulus); "
    f"flattened control chi={chi_c_method} betti={betti_c}. NOTE: a CLOSED single leaf would also "
    f"have chi=0 — chi alone cannot distinguish annulus from circle; the flattened (cut) control is "
    f"the honest discriminator here."
)

# ----------------------------------------------------------------------------
# Lane 3: rustworkx + networkx vs torch receipt
# ----------------------------------------------------------------------------
import networkx as nx
import rustworkx as rx

src = json.load(open(SRC_PACKETS))
torch_rec = json.load(open(TORCH_RECEIPT))
# torch stored source_digest = src["result_digest"] verbatim
result_digest_ok = src.get("result_digest") == torch_rec["source_digest"]

def hamming_edges(words):
    n = len(words)
    return [(i, j) for i in range(n) for j in range(i + 1, n)
            if sum(a != b for a, b in zip(words[i], words[j])) == 1]

def spectral_from_laplacian(L, n):
    ev = np.linalg.eigvalsh(L)
    gap = float(ev[1]) if n > 1 else 0.0
    n_comp_spec = int(np.sum(ev < 1e-9))
    return gap, n_comp_spec

per_packet = {}
agree_rx_nx_comp, agree_rx_nx_gap_bitwise = [], []
agree_torch_comp, agree_torch_gap_bitwise = [], []
for pk in src["base_packets"]:
    words, n = pk["accepted_words"], len(pk["accepted_words"])
    edges = hamming_edges(words)

    # rustworkx lane: graph object + its own component algorithm + adjacency
    g_rx = rx.PyGraph()
    g_rx.add_nodes_from(range(n))
    g_rx.add_edges_from([(i, j, 1.0) for i, j in edges])
    comp_rx = len(rx.connected_components(g_rx))
    A_rx = rx.adjacency_matrix(g_rx)                      # float64 numpy from rustworkx
    L_rx = np.diag(A_rx.sum(axis=1)) - A_rx
    gap_rx, comp_spec_rx = spectral_from_laplacian(L_rx, n)

    # networkx lane: independent graph object + its own algorithms
    g_nx = nx.Graph()
    g_nx.add_nodes_from(range(n))
    g_nx.add_edges_from(edges)
    comp_nx = nx.number_connected_components(g_nx)
    L_nx = nx.laplacian_matrix(g_nx, nodelist=list(range(n))).toarray().astype(np.float64)
    gap_nx, comp_spec_nx = spectral_from_laplacian(L_nx, n)

    t = torch_rec["data"]["packets"][pk["packet_id"]]
    per_packet[pk["packet_id"]] = {
        "n_words": n, "n_hamming1_edges": len(edges),
        "rx": {"components": comp_rx, "components_spectral": comp_spec_rx, "gap": gap_rx},
        "nx": {"components": comp_nx, "components_spectral": comp_spec_nx, "gap": gap_nx},
        "torch_receipt": {"components_spectral": t["components_spectral"],
                          "components_unionfind": t["components_unionfind"],
                          "gap": t["spectral_gap"]},
    }
    agree_rx_nx_comp.append(comp_rx == comp_nx == comp_spec_rx == comp_spec_nx)
    agree_rx_nx_gap_bitwise.append(gap_rx == gap_nx)
    agree_torch_comp.append(comp_rx == t["components_spectral"] == t["components_unionfind"])
    agree_torch_gap_bitwise.append(gap_rx == t["spectral_gap"] and gap_nx == t["spectral_gap"])

checks["rx_nx_components_equal_all9"] = all(agree_rx_nx_comp) and len(agree_rx_nx_comp) == 9
checks["rx_nx_gap_bitwise_equal_all9"] = all(agree_rx_nx_gap_bitwise) and len(agree_rx_nx_gap_bitwise) == 9
checks["components_match_torch_receipt_all9"] = all(agree_torch_comp)
checks["gap_matches_torch_receipt_bitwise_all9"] = all(agree_torch_gap_bitwise)
checks["source_result_digest_matches_torch_receipt"] = bool(result_digest_ok)

data["capacity_graph_per_packet"] = per_packet
findings.append(
    "rustworkx and networkx Hamming-1 capacity graphs agree bitwise with each other and with the "
    "torch receipt spectral gaps/components on all 9 packets"
    if checks["gap_matches_torch_receipt_bitwise_all9"] and checks["components_match_torch_receipt_all9"]
    else "DISAGREEMENT between rustworkx/networkx/torch capacity-graph values — see per-packet data"
)

# ----------------------------------------------------------------------------
# Receipt
# ----------------------------------------------------------------------------
all_pass = all(checks.values())
import importlib.metadata as _im
receipt = {
    "schema": "ratchet.v8.deep-integration.topology.v0",
    "lane": "topology",
    "engine": "light-libs (gudhi+toponetx+rustworkx+networkx), numpy substrate; NO heavy stack loaded",
    "packages": {
        "gudhi": "load_bearing: VR persistence decides all 6 H0/H1 checks (basin counts, gap ratio, loop vs scrambled control)",
        "toponetx": "load_bearing: CellComplex bookkeeping + euler method + hodge-Laplacian betti decide all 3 strip checks",
        "rustworkx": "load_bearing: independent graph object, connected_components, adjacency_matrix in the 5 agreement checks",
        "networkx": "load_bearing: independent graph object, number_connected_components, laplacian_matrix in the 5 agreement checks",
        "numpy": "substrate-only: point-cloud generation + eigvalsh backend; no verdict rests on a numpy-only quantity",
    },
    "versions": {p: _im.version(p) for p in ["gudhi", "toponetx", "rustworkx", "networkx", "numpy"]},
    "inputs": {
        "source_packets": SRC_PACKETS,
        "torch_receipt": TORCH_RECEIPT,
        "bloch_census": "in-script 384-point Fibonacci sphere (working-sim surrogate; the jax L13 census grid is not exported in its receipt)",
        "terrain_flows": "in-script declared surrogates: pit=2 pole wells, source=4 equatorial wells, depolarizing=uniform contraction (lambda=0.12, depol 0.15)",
    },
    "conventions": {
        "h0_basin_count": "H0 bars with death > 0.5 (infinite bar included) = components at scale 0.5",
        "h1_signal": "max finite H1 persistence, Rips max_edge_length 2.0, max_dimension 2",
        "chi": "V - E + F from the toponetx object AND toponetx euler_characterisitics(), both gated",
        "betti": "nullity of toponetx hodge_laplacian_matrix(rank=r) via numpy matrix_rank",
        "capacity_graph": "Hamming-1 graph on accepted_words, L = D - A float64, gap = 2nd smallest eigvalsh value (torch-lane convention)",
    },
    "checks": checks,
    "all_pass": all_pass,
    "data": data,
    "findings": findings,
    "promotion_allowed": False,
    "formal_admission_allowed": False,
    "claim_ceiling": "scratch_diagnostic / working-sim: executed finite topological readouts on surrogate flows + receipt cross-checks; no manifold, basin-doctrine, or bridge claim",
}
out = os.path.join(OUTDIR, "receipt.json")
with open(out, "w") as f:
    json.dump(receipt, f, indent=2)

print(json.dumps({"lane": "topology", "file": out, "all_pass": all_pass, "checks": checks}, indent=2))
for fdg in findings:
    print("FINDING:", fdg)
