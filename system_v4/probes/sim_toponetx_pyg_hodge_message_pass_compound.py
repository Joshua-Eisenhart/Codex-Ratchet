#!/usr/bin/env python3
"""
sim_toponetx_pyg_hodge_message_pass_compound

Scope note: compound admissibility claim -- a signal on 1-simplices (edge
flow) on a loop complex admits a harmonic component (kernel of L1) that
survives a PyG-driven Hodge message-passing diffusion step x_{t+1} =
x_t - alpha * L1 x_t (with small alpha). Specifically: the kernel component
is fixed under the diffusion (excluded from decay), while the orthogonal
component decays. This ties the topology (toponetx L1) to geometry-of-flow
(pyg message passing on the signed incidence edge_index). Fence: see
LADDERS_FENCES_ADMISSION_REFERENCE.md (harmonic admission + dynamical fence).
Both tools are load_bearing:
  * toponetx supplies the oriented L1 whose kernel defines "harmonic";
  * pyg supplies the sparse scatter-based message pass that enacts the
    diffusion. Swapping either for dense numpy collapses the compound claim
    into an empty coincidence.

Classification: canonical.
"""
import json, os, sys
import numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from toponetx.classes import SimplicialComplex
    TOOL_MANIFEST["toponetx"] = {"tried": True, "used": True,
        "reason": "Hodge-1 Laplacian from SimplicialComplex defines the harmonic "
                  "admissibility kernel under the compound claim -- load_bearing."}
    TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"
except ImportError as e:
    print(f"BROKEN ENV: toponetx missing: {e}", file=sys.stderr); sys.exit(2)
try:
    import torch
    from torch_geometric.utils import scatter
    TOOL_MANIFEST["pytorch"] = {"tried": True, "used": True,
        "reason": "Hosts tensors for the message-pass iteration."}
    TOOL_MANIFEST["pyg"] = {"tried": True, "used": True,
        "reason": "torch_geometric.utils.scatter is the sparse message-pass "
                  "operator enacting the diffusion; removing it removes the "
                  "dynamical half of the compound claim -- load_bearing."}
    TOOL_INTEGRATION_DEPTH["pyg"] = "load_bearing"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
except ImportError as e:
    print(f"BROKEN ENV: pyg/torch missing: {e}", file=sys.stderr); sys.exit(2)


def _loop_L1_and_edge_index(n=6):
    # Cycle graph as a SimplicialComplex (dim 1): edges (i, i+1 mod n)
    simplices = [[i, (i+1) % n] for i in range(n)]
    sc = SimplicialComplex(simplices)
    L1 = sc.hodge_laplacian_matrix(1).toarray().astype(np.float64)
    # Build edge_index over 1-simplex dual graph: two 1-simplices share a vertex
    edges = sc.skeleton(1)  # list of 1-simplices
    edge_list = list(edges)
    # map to deterministic order matching L1
    idx_of = {frozenset(e): i for i, e in enumerate(edge_list)}
    src, dst, w = [], [], []
    for i, ei in enumerate(edge_list):
        si = set(ei)
        for j, ej in enumerate(edge_list):
            if i == j: continue
            sj = set(ej)
            if si & sj:
                src.append(i); dst.append(j); w.append(float(L1[i, j]))
    return L1, (src, dst, w), len(edge_list)


def _diffuse_pyg(x, edge_index, edge_w, diag, alpha, steps):
    src = torch.tensor(edge_index[0], dtype=torch.long)
    dst = torch.tensor(edge_index[1], dtype=torch.long)
    w = torch.tensor(edge_index[2], dtype=torch.float64)
    d = torch.tensor(diag, dtype=torch.float64)
    x = torch.tensor(x, dtype=torch.float64)
    n = x.numel()
    for _ in range(steps):
        msg = w * x[src]
        agg = scatter(msg, dst, dim=0, dim_size=n, reduce="sum")
        Lx = d * x + agg
        x = x - alpha * Lx
    return x.numpy()


def _harmonic_basis(L1):
    w, V = np.linalg.eigh((L1 + L1.T) / 2.0)
    ker = V[:, np.abs(w) < 1e-8]
    return ker


def run_positive_tests():
    out = {}
    L1, (src, dst, w), n = _loop_L1_and_edge_index(n=6)
    ker = _harmonic_basis(L1)
    # for a cycle, dim ker L1 = b1 = 1
    if ker.shape[1] != 1:
        out["kernel_dim_one"] = {"PASS": False, "ker_dim": int(ker.shape[1])}
        return out
    out["kernel_dim_one"] = {"PASS": True, "ker_dim": 1,
        "language": "admissible: unique harmonic flow on the loop"}
    h = ker[:, 0]
    diag = np.diag(L1).copy()
    # harmonic signal is fixed by diffusion
    y_h = _diffuse_pyg(h, (src, dst, w), w, diag, alpha=0.1, steps=50)
    drift_h = float(np.linalg.norm(y_h - h))
    out["harmonic_fixed_under_diffusion"] = {
        "PASS": drift_h < 1e-8, "drift": drift_h,
        "language": "admissible: harmonic component excluded from decay"}
    # orthogonal signal decays
    rng = np.random.default_rng(0)
    r = rng.normal(0, 1, size=n)
    r = r - (h @ r) / (h @ h) * h  # project OUT the harmonic
    y_r = _diffuse_pyg(r, (src, dst, w), w, diag, alpha=0.1, steps=50)
    decay = float(np.linalg.norm(y_r) / (np.linalg.norm(r) + 1e-18))
    out["orthogonal_decays"] = {
        "PASS": decay < 0.1, "remaining_fraction": decay,
        "language": "admissible: non-harmonic component decays under diffusion"}
    return out


def run_negative_tests():
    out = {}
    # Negative: on a PATH (no loop) b1=0 -> no harmonic; all signals decay
    simplices = [[i, i+1] for i in range(5)]
    sc = SimplicialComplex(simplices)
    L1 = sc.hodge_laplacian_matrix(1).toarray().astype(np.float64)
    ker = _harmonic_basis(L1)
    out["path_no_harmonic"] = {"PASS": ker.shape[1] == 0, "ker_dim": int(ker.shape[1]),
        "language": "excluded: path admits no harmonic 1-form"}
    # Build edge_index same way
    edge_list = list(sc.skeleton(1))
    src, dst, w = [], [], []
    for i, ei in enumerate(edge_list):
        si = set(ei)
        for j, ej in enumerate(edge_list):
            if i == j: continue
            if si & set(ej):
                src.append(i); dst.append(j); w.append(float(L1[i, j]))
    diag = np.diag(L1).copy()
    rng = np.random.default_rng(1)
    r = rng.normal(0, 1, size=L1.shape[0])
    y = _diffuse_pyg(r, (src, dst, w), w, diag, alpha=0.05, steps=200)
    decay = float(np.linalg.norm(y) / (np.linalg.norm(r) + 1e-18))
    out["path_all_decays"] = {"PASS": decay < 0.2, "remaining_fraction": decay,
        "language": "excluded: no harmonic => every signal excluded from persistence"}
    # Negative 2: wrong-sign alpha (large) blows up a harmonic-orthogonal signal
    L1c, (sc_s, sc_d, sc_w), nc = _loop_L1_and_edge_index(n=6)
    ker_c = _harmonic_basis(L1c)
    rng = np.random.default_rng(2)
    r = rng.normal(0, 1, size=nc)
    h = ker_c[:, 0]; r = r - (h @ r)/(h @ h)*h
    y = _diffuse_pyg(r, (sc_s, sc_d, sc_w), sc_w, np.diag(L1c).copy(), alpha=2.0, steps=20)
    ratio = float(np.linalg.norm(y) / (np.linalg.norm(r) + 1e-18))
    out["bad_step_diverges"] = {"PASS": ratio > 1.0, "growth": ratio,
        "language": "excluded: step outside admissibility window violates decay"}
    return out


def run_boundary_tests():
    out = {}
    # minimal loop: triangle boundary (3 edges), b1 = 1
    L1, (s, d, w), n = _loop_L1_and_edge_index(n=3)
    ker = _harmonic_basis(L1)
    out["triangle_loop_b1_one"] = {"PASS": ker.shape[1] == 1, "ker_dim": int(ker.shape[1])}
    # 4-cycle: b1 = 1 still
    L1b, _, _ = _loop_L1_and_edge_index(n=4)
    ker_b = _harmonic_basis(L1b)
    out["4cycle_b1_one"] = {"PASS": ker_b.shape[1] == 1, "ker_dim": int(ker_b.shape[1])}
    return out


if __name__ == "__main__":
    name = "sim_toponetx_pyg_hodge_message_pass_compound"
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(v["PASS"] for v in pos.values()) and all(v["PASS"] for v in neg.values()) and all(v["PASS"] for v in bnd.values())
    results = {"name": name, "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md (harmonic + dynamical fence)",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "ALL_PASS": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, f"{name}_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{name}: ALL_PASS={all_pass} -> {p}")
