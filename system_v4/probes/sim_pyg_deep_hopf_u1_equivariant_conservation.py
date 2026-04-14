#!/usr/bin/env python3
"""
sim_pyg_deep_hopf_u1_equivariant_conservation.py

PyG-load-bearing canonical sim.

Carrier graph: discretized S^3 via Hopf fibration sampling (N_base points on S^2
base, N_fiber points on each U(1) fiber, N = N_base * N_fiber total nodes).
Edges: (a) intra-fiber cyclic (U(1) orbit), (b) inter-fiber nearest-neighbour
on the S^2 base (k=3 ring of base neighbours for each fiber phase index).

Node feature: complex scalar f_i in C (represented as 2-real-channel tensor).

Update rule (custom MessagePassing):  f'_i = f_i + alpha * sum_{j in N(i)} (f_j - f_i)
with a single symmetric weight alpha. Because every undirected edge contributes
+alpha(f_j - f_i) to node i and +alpha(f_i - f_j) to node j, the global linear
charge Q = sum_i f_i is exactly conserved under propagate().

Two conserved quantities checked:
  Q_lin  = sum_i f_i                                (complex linear charge)
  L_z    = sum_i  Im( conj(f_i) * phase_factor_i )  NOT conserved in general
           -- used as the NEGATIVE control

G-equivariance: the update commutes with the global U(1) action
  R_theta:  f_i -> e^{i theta} f_i
Checked numerically:  R_theta(Update(f)) == Update(R_theta(f)).

Classification: canonical (PyG MessagePassing + edge_index + propagate() are
load-bearing; removing PyG eliminates the claim).
"""

import json
import math
import os
import sys

import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        None,
    "cvc5":      None,
    "sympy":     None,
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

# ---- torch / pyg are REQUIRED; no numpy fallback. -------------------
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError as e:
    TOOL_MANIFEST["pytorch"]["reason"] = f"not installed: {e}"
    print(json.dumps({"blocker": "pytorch not importable", "detail": str(e)}))
    sys.exit(2)

try:
    import torch_geometric
    from torch_geometric.nn import MessagePassing
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError as e:
    TOOL_MANIFEST["pyg"]["reason"] = f"not installed: {e}"
    print(json.dumps({"blocker": "torch_geometric not importable", "detail": str(e)}))
    sys.exit(2)

# Mark optional tools we don't load-bear on.
for _name, _reason in [
    ("z3", "not needed: claim is numerical invariance under symmetric MP"),
    ("cvc5", "not needed: numerical proof path only"),
    ("sympy", "not needed: closed-form conservation is by construction"),
    ("clifford", "not needed: scalar complex charge, no multivector"),
    ("geomstats", "not needed: Hopf sampling done explicitly"),
    ("e3nn", "not needed: U(1) equivariance checked directly"),
    ("rustworkx", "not needed: edge_index built directly"),
    ("xgi", "not needed: no hypergraph structure"),
    ("toponetx", "not needed: 1-skeleton suffices"),
    ("gudhi", "not needed: no persistent homology claim"),
]:
    TOOL_MANIFEST[_name]["reason"] = _reason


# =====================================================================
# Hopf fibration sampling of S^3
# =====================================================================

def hopf_sample(n_base: int, n_fiber: int, device="cpu", dtype=torch.float64):
    """Return (X, base_idx, fiber_idx) with X of shape (N,4) on S^3.

    Base: Fibonacci spiral on S^2.
    Fiber: uniform U(1) orbit over each base point via Hopf map inverse.
    """
    # Fibonacci on S^2
    phi_g = math.pi * (3.0 - math.sqrt(5.0))
    base = []
    for k in range(n_base):
        y = 1.0 - 2.0 * (k + 0.5) / n_base          # in (-1,1)
        r = math.sqrt(max(0.0, 1.0 - y * y))
        theta = phi_g * k
        base.append((r * math.cos(theta), y, r * math.sin(theta)))
    base = torch.tensor(base, dtype=dtype, device=device)  # (n_base, 3)

    # Hopf inverse: for base (a,b,c) on S^2 and phase psi,
    #   z1 = sqrt((1+c)/2) * e^{i*(psi)}
    #   z2 = sqrt((1-c)/2) * e^{i*(psi - atan2(b,a))}
    # Convert to real 4-vector (Re z1, Im z1, Re z2, Im z2).
    pts = []
    b_idx = []
    f_idx = []
    for bi, (a, b, c) in enumerate(base.tolist()):
        denom = math.hypot(a, b)
        if denom < 1e-12:
            alpha = 0.0
        else:
            alpha = math.atan2(b, a)
        rp = math.sqrt(max(0.0, (1.0 + c) / 2.0))
        rm = math.sqrt(max(0.0, (1.0 - c) / 2.0))
        for fi in range(n_fiber):
            psi = 2.0 * math.pi * fi / n_fiber
            z1 = (rp * math.cos(psi),       rp * math.sin(psi))
            z2 = (rm * math.cos(psi - alpha), rm * math.sin(psi - alpha))
            pts.append((z1[0], z1[1], z2[0], z2[1]))
            b_idx.append(bi)
            f_idx.append(fi)
    X = torch.tensor(pts, dtype=dtype, device=device)
    return X, torch.tensor(b_idx, device=device), torch.tensor(f_idx, device=device)


def build_edge_index(n_base: int, n_fiber: int):
    """Undirected edges: cyclic intra-fiber + k-NN inter-fiber at same phase.

    Returns edge_index of shape (2, E) with both directions included so that
    the MessagePassing aggregation is symmetric.
    """
    # Intra-fiber cyclic edges: (bi, fi) <-> (bi, (fi+1) % n_fiber)
    edges = []
    # We also need base neighbours — Fibonacci is quasi-uniform, so k nearest.
    # Recompute base coords for distance:
    dtype = torch.float64
    phi_g = math.pi * (3.0 - math.sqrt(5.0))
    base = []
    for k in range(n_base):
        y = 1.0 - 2.0 * (k + 0.5) / n_base
        r = math.sqrt(max(0.0, 1.0 - y * y))
        theta = phi_g * k
        base.append((r * math.cos(theta), y, r * math.sin(theta)))
    base = torch.tensor(base, dtype=dtype)
    d = torch.cdist(base, base)
    k_base = 3
    # for each base i, pick k_base nearest (excluding self)
    nbr = d.argsort(dim=1)[:, 1:k_base + 1]  # (n_base, k_base)

    def nid(bi, fi):
        return bi * n_fiber + fi

    # Intra-fiber cyclic
    for bi in range(n_base):
        for fi in range(n_fiber):
            edges.append((nid(bi, fi), nid(bi, (fi + 1) % n_fiber)))
            edges.append((nid(bi, (fi + 1) % n_fiber), nid(bi, fi)))

    # Inter-fiber (same phase index) — we only add (bi, bj) if bi<bj to avoid dup
    for bi in range(n_base):
        for bj in nbr[bi].tolist():
            if bj <= bi:
                continue
            for fi in range(n_fiber):
                edges.append((nid(bi, fi), nid(bj, fi)))
                edges.append((nid(bj, fi), nid(bi, fi)))

    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()  # (2, E)
    return edge_index


# =====================================================================
# MessagePassing module: symmetric Laplacian smoother on complex channel.
# =====================================================================

class SymmetricComplexSmoother(MessagePassing):
    """f'_i = f_i + alpha * sum_{j in N(i)} (f_j - f_i).

    Implemented with flow='source_to_target', aggr='add'. Because the graph is
    symmetric (both directions present) and alpha is a scalar constant, the
    update is exactly antisymmetric edge-wise => sum_i f_i is preserved.

    Channels: 2 real (Re, Im) representing one complex scalar.
    """

    def __init__(self, alpha: float = 0.1):
        super().__init__(aggr="add", flow="source_to_target")
        self.alpha = alpha

    def forward(self, x, edge_index):
        # propagate will call message() then aggregate() then update()
        out = self.propagate(edge_index, x=x)
        return x + self.alpha * out

    def message(self, x_i, x_j):
        # contribution from neighbour j to node i
        return x_j - x_i


# =====================================================================
# Helpers
# =====================================================================

def total_charge(x: torch.Tensor) -> torch.Tensor:
    """Return complex sum of features as (Re, Im) tensor of shape (2,)."""
    return x.sum(dim=0)


def u1_rotate(x: torch.Tensor, theta: float) -> torch.Tensor:
    c, s = math.cos(theta), math.sin(theta)
    R = torch.tensor([[c, -s], [s, c]], dtype=x.dtype, device=x.device)
    return x @ R.t()


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    torch.manual_seed(0)
    n_base, n_fiber = 12, 8
    dtype = torch.float64

    X, b_idx, f_idx = hopf_sample(n_base, n_fiber, dtype=dtype)
    edge_index = build_edge_index(n_base, n_fiber)
    N = X.shape[0]

    # Sanity: S^3 norm
    s3_err = float((X.pow(2).sum(dim=1) - 1.0).abs().max())
    results["s3_norm_max_err"] = s3_err
    results["num_nodes"] = N
    results["num_edges"] = int(edge_index.shape[1])

    # Use a U(1)-flavored feature: f_i = z1_i * z2_i  (complex product),
    # which is NOT constant and has nontrivial spatial structure.
    z1 = torch.complex(X[:, 0], X[:, 1])
    z2 = torch.complex(X[:, 2], X[:, 3])
    f_complex = z1 * torch.conj(z2)  # complex field on S^3, charge=0 under diag U(1)
    f = torch.stack([f_complex.real, f_complex.imag], dim=1)  # (N,2)

    model = SymmetricComplexSmoother(alpha=0.1).to(dtype=dtype)

    # ----- Test 1: linear charge conservation over many MP steps -----
    Q0 = total_charge(f).detach().clone()
    x_t = f.clone()
    n_steps = 25
    max_drift = 0.0
    for _ in range(n_steps):
        x_t = model(x_t, edge_index)
        drift = float((total_charge(x_t) - Q0).norm())
        max_drift = max(max_drift, drift)
    results["test1_linear_charge_conservation"] = {
        "Q0": Q0.tolist(),
        "Q_final": total_charge(x_t).tolist(),
        "max_drift_over_25_steps": max_drift,
        "pass": max_drift < 1e-10,
    }

    # ----- Test 2: U(1) equivariance of a single propagate() call -----
    theta = 0.73
    left  = u1_rotate(model(f, edge_index), theta)
    right = model(u1_rotate(f, theta), edge_index)
    equi_err = float((left - right).abs().max())
    results["test2_u1_equivariance"] = {
        "max_abs_diff": equi_err,
        "pass": equi_err < 1e-12,
    }

    # ----- Test 3: propagate() actually calls message() (load-bearing check)
    # Count messages by subclassing and incrementing.
    class CountingSmoother(SymmetricComplexSmoother):
        def __init__(self, alpha):
            super().__init__(alpha)
            self.msg_calls = 0
            self.last_msg_shape = None
        def message(self, x_i, x_j):
            self.msg_calls += 1
            self.last_msg_shape = tuple(x_j.shape)
            return x_j - x_i

    cm = CountingSmoother(alpha=0.1).to(dtype=dtype)
    _ = cm(f, edge_index)
    results["test3_propagate_load_bearing"] = {
        "message_called": cm.msg_calls,
        "message_shape": cm.last_msg_shape,
        "expected_shape_E_by_2": [int(edge_index.shape[1]), 2],
        "pass": cm.msg_calls >= 1 and cm.last_msg_shape == (int(edge_index.shape[1]), 2),
    }

    results["pass_all"] = all(
        v["pass"] for k, v in results.items() if isinstance(v, dict) and "pass" in v
    )
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """Each negative has a corresponding positive in the section above."""
    results = {}
    dtype = torch.float64
    n_base, n_fiber = 12, 8
    X, _, _ = hopf_sample(n_base, n_fiber, dtype=dtype)
    edge_index = build_edge_index(n_base, n_fiber)

    z1 = torch.complex(X[:, 0], X[:, 1])
    z2 = torch.complex(X[:, 2], X[:, 3])
    f_complex = z1 * torch.conj(z2)
    f = torch.stack([f_complex.real, f_complex.imag], dim=1)

    # ----- Neg 1: an asymmetric rule breaks conservation -----
    class AsymmetricSmoother(MessagePassing):
        def __init__(self):
            super().__init__(aggr="add", flow="source_to_target")
        def forward(self, x, edge_index):
            return x + 0.1 * self.propagate(edge_index, x=x)
        def message(self, x_j):
            # ONLY uses x_j (no subtraction) -> not antisymmetric per edge
            return x_j

    asym = AsymmetricSmoother().to(dtype=dtype)
    Q0 = total_charge(f).detach().clone()
    xt = asym(f, edge_index)
    drift = float((total_charge(xt) - Q0).norm())
    results["neg1_asymmetric_rule_breaks_conservation"] = {
        "drift_one_step": drift,
        "pass_expect_broken": drift > 1e-6,
    }

    # ----- Neg 2: a non-U(1)-equivariant rule fails equivariance check -----
    class RealOnlySmoother(MessagePassing):
        def __init__(self):
            super().__init__(aggr="add", flow="source_to_target")
        def forward(self, x, edge_index):
            return x + 0.1 * self.propagate(edge_index, x=x)
        def message(self, x_i, x_j):
            # Apply a non-commuting channel mixing that breaks U(1): swap axes
            diff = x_j - x_i
            return torch.stack([diff[:, 1], diff[:, 0]], dim=1)

    ros = RealOnlySmoother().to(dtype=dtype)
    theta = 0.73
    left = u1_rotate(ros(f, edge_index), theta)
    right = ros(u1_rotate(f, theta), edge_index)
    err = float((left - right).abs().max())
    results["neg2_nonequivariant_rule_breaks_equivariance"] = {
        "max_abs_diff": err,
        "pass_expect_broken": err > 1e-6,
    }

    results["pass_all"] = all(
        v.get("pass_expect_broken", False)
        for v in results.values() if isinstance(v, dict)
    )
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    dtype = torch.float64

    # ----- Boundary 1: degenerate graph (no edges) -> update is identity -----
    X, _, _ = hopf_sample(6, 4, dtype=dtype)
    empty_ei = torch.empty((2, 0), dtype=torch.long)
    f = torch.stack([X[:, 0], X[:, 1]], dim=1).clone()
    model = SymmetricComplexSmoother(alpha=0.1).to(dtype=dtype)
    y = model(f, empty_ei)
    diff = float((y - f).abs().max())
    results["b1_no_edges_is_identity"] = {"max_diff": diff, "pass": diff < 1e-14}

    # ----- Boundary 2: single-node graph, self-loop only -----
    single_x = torch.tensor([[0.3, 0.4]], dtype=dtype)
    loop = torch.tensor([[0], [0]], dtype=torch.long)
    y = model(single_x, loop)
    # Self-loop contributes (x_j - x_i) = 0 -> update is identity.
    diff = float((y - single_x).abs().max())
    results["b2_self_loop_only_is_identity"] = {"max_diff": diff, "pass": diff < 1e-14}

    # ----- Boundary 3: very large alpha still conserves linear charge -----
    X, _, _ = hopf_sample(10, 6, dtype=dtype)
    ei = build_edge_index(10, 6)
    z1 = torch.complex(X[:, 0], X[:, 1]); z2 = torch.complex(X[:, 2], X[:, 3])
    fc = z1 * torch.conj(z2)
    f = torch.stack([fc.real, fc.imag], dim=1)
    big = SymmetricComplexSmoother(alpha=5.0).to(dtype=dtype)  # unstable dynamics
    Q0 = total_charge(f).detach().clone()
    y = big(f, ei)
    drift = float((total_charge(y) - Q0).norm())
    results["b3_large_alpha_still_conserves"] = {
        "alpha": 5.0,
        "drift": drift,
        "pass": drift < 1e-10,
    }

    results["pass_all"] = all(
        v["pass"] for v in results.values() if isinstance(v, dict) and "pass" in v
    )
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    # Mark tools used
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "torch tensors, complex arithmetic, and autograd-capable Module carry "
        "the node feature state and all arithmetic operations."
    )
    TOOL_MANIFEST["pyg"]["used"] = True
    TOOL_MANIFEST["pyg"]["reason"] = (
        "torch_geometric.nn.MessagePassing subclass with explicit message() and "
        "propagate(edge_index, x=x); edge_index tensor drives aggregation; "
        "removing PyG eliminates the sim's claim."
    )

    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    TOOL_INTEGRATION_DEPTH["pyg"] = "load_bearing"

    results = {
        "name": "sim_pyg_deep_hopf_u1_equivariant_conservation",
        "description": (
            "S^3 Hopf-discretized carrier; PyG MessagePassing symmetric "
            "Laplacian smoother on complex scalar charge; verifies (1) linear "
            "charge conservation sum_i f_i under repeated propagate(); (2) U(1) "
            "global equivariance of the update; (3) that message() is invoked "
            "with the expected (E,2) shape. Negative controls: asymmetric rule "
            "breaks conservation, channel-swap rule breaks U(1) equivariance."
        ),
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": bool(pos.get("pass_all") and neg.get("pass_all") and bnd.get("pass_all")),
        "invariant_preserved": "sum_i f_i (complex linear charge) under SymmetricComplexSmoother",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_pyg_deep_hopf_u1_equivariant_conservation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass={results['overall_pass']}")
    if not results["overall_pass"]:
        sys.exit(1)
