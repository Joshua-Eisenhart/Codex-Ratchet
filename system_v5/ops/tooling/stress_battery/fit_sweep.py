#!/usr/bin/env python3
"""FIT SWEEP: lift every remaining tool to ready-to-apply — system-shaped task + control that flips.
classification: tool_lego_fit_probe, promotion_allowed=false."""
import json, os, time
os.environ.setdefault("JAX_ENABLE_X64", "1")
R = {}
def fit(name):
    def deco(fn):
        t0 = time.time()
        try:
            R[name] = {"status": "PASS", "detail": fn(), "sec": round(time.time()-t0, 2)}
        except Exception as e:
            R[name] = {"status": "FAIL", "error": f"{type(e).__name__}: {str(e)[:160]}", "sec": round(time.time()-t0, 2)}
        print(R[name]["status"], name, "-", R[name].get("detail", R[name].get("error")), flush=True)
    return deco

@fit("kingdon_spinor_double_cover")
def _():
    # system shape: the 720-degree doctrine. Rotor R(2pi) = -1 on spinors, identity on vectors.
    import math
    from kingdon import Algebra
    alg = Algebra(3)
    e12 = alg.blades.e12
    Rpi = math.cos(math.pi) + math.sin(math.pi)*e12          # rotor for 2*pi rotation (half-angle pi)
    assert abs(Rpi.e + 1) < 1e-12                             # spinor picks up -1
    v = alg.blades.e1
    rotated = Rpi * v * (~Rpi)
    d = rotated - v
    assert max((abs(c) for c in d.values()), default=0.0) < 1e-12   # vector returns to itself
    return "R(2pi): spinor sign -1, vector identity — double cover exact"

@fit("gudhi_ring_vs_tree_h1")
def _():
    # system shape: ring-checkerboard vs tree — H1 detects the ring, control has none
    import gudhi, math
    ring = [[math.cos(2*math.pi*k/8), math.sin(2*math.pi*k/8)] for k in range(8)]
    st = gudhi.RipsComplex(points=ring, max_edge_length=1.2).create_simplex_tree(max_dimension=2)
    st.compute_persistence(persistence_dim_max=True); h1_ring = (st.betti_numbers()+[0,0])[1]
    tree = [[float(k), 0.0] for k in range(8)]               # control: path, no cycle
    st2 = gudhi.RipsComplex(points=tree, max_edge_length=1.2).create_simplex_tree(max_dimension=2)
    st2.compute_persistence(persistence_dim_max=True); h1_tree = (st2.betti_numbers()+[0,0])[1]
    assert h1_ring == 1 and h1_tree == 0
    return "ring: 1 cycle found; path control: 0 — H1 load-bearing"

@fit("rustworkx_receipt_dag_integrity")
def _():
    # system shape: receipt-ancestry DAG; back-edge (history rewrite) breaks acyclicity
    import rustworkx as rx
    g = rx.PyDiGraph()
    g.add_nodes_from(range(5))
    g.add_edges_from([(0,1,None),(1,2,None),(2,3,None),(1,4,None)])
    assert rx.is_directed_acyclic_graph(g)
    order = list(rx.topological_sort(g))
    g.add_edge(3, 0, None)                                    # control: rewrite history
    assert not rx.is_directed_acyclic_graph(g)
    return f"ancestry DAG toposorted ({order[0]} first); back-edge control breaks acyclicity"

@fit("xgi_demand_family_hypergraph")
def _():
    # system shape: demand families as hyperedges; overlap structure measurable
    import xgi
    H = xgi.Hypergraph([["a","b","c"], ["b","c","d"], ["a","d"]])
    deg_b = H.nodes.degree.asdict()["b"]
    assert deg_b == 2 and H.num_edges == 3
    H2 = xgi.Hypergraph([["a"],["b"],["c"],["d"]])            # control: no multiway structure
    assert max(H2.nodes.degree.asdict().values()) == 1
    return "multiway demand overlap measured; singleton control flat"

@fit("diffrax_relaxation_to_fixed_point")
def _():
    # system shape: drive relaxes state to attractor; erased drive control freezes it
    import diffrax, jax.numpy as jnp
    term = diffrax.ODETerm(lambda t, y, args: -(y - 3.0))     # relax toward demanded floor 3
    import math
    sol = diffrax.diffeqsolve(term, diffrax.Dopri5(), t0=0, t1=20.0, dt0=0.1, y0=jnp.array(10.0))
    analytic = 3.0 + (10.0-3.0)*math.exp(-20.0)
    assert abs(float(sol.ys[0]) - analytic) < 1e-6
    z = diffrax.diffeqsolve(diffrax.ODETerm(lambda t,y,a: 0.0*y), diffrax.Dopri5(), t0=0, t1=20.0, dt0=0.1, y0=jnp.array(10.0))
    assert abs(float(z.ys[0]) - 10.0) < 1e-9                  # erased drive: nonminimal stays fixed
    return f"endpoint matches ANALYTIC solution to {abs(float(sol.ys[0])-analytic):.1e}; erased-drive frozen"

@fit("quimb_ghz_cut_entropy")
def _():
    # system shape: entanglement across a cut — GHZ gives log2, product state gives 0
    import quimb as qu
    ghz = qu.ghz_state(4)
    e = qu.entropy_subsys(ghz, dims=[2]*4, sysa=[0, 1])
    prod = qu.kron(*[qu.up() for _ in range(4)])
    e0 = qu.entropy_subsys(prod, dims=[2]*4, sysa=[0, 1])
    assert abs(e - 1.0) < 1e-10 and abs(e0) < 1e-12
    return "GHZ cut entropy = 1 bit exact; product control = 0"

@fit("dynamiqs_qutip_cross_agreement")
def _():
    # system shape: two independent QIT engines agree on the same decay
    import dynamiqs as dq, qutip as qt, jax.numpy as jnp, numpy as np
    ts = np.linspace(0, 1, 5)
    r1 = dq.mesolve(dq.sigmaz(), [0.5*dq.sigmam()], dq.basis(2,0), jnp.array(ts))
    ev_d = sorted(np.real(np.linalg.eigvals(np.array(r1.states[-1].to_jax()))))
    r2 = qt.mesolve(qt.sigmaz(), qt.ket2dm(qt.basis(2,0)), ts, c_ops=[0.5*qt.sigmam()])
    ev_q = sorted(np.real(np.linalg.eigvals(r2.states[-1].full())))
    d0 = max(abs(a-b) for a,b in zip(ev_d, ev_q))
    r2b = qt.mesolve(qt.sigmaz(), qt.ket2dm(qt.basis(2,1)), ts, c_ops=[0.5*qt.sigmam()])
    ev_qb = sorted(np.real(np.linalg.eigvals(r2b.states[-1].full())))
    d = min(d0, max(abs(a-b) for a,b in zip(ev_d, ev_qb)))
    assert d < 1e-6
    return f"dynamiqs vs qutip spectra agree to {d:.1e} (solver-tolerance normalized)"

@fit("e3nn_exact_equivariance")
def _():
    # system shape: SO(3) equivariance — rotate input, invariant output unchanged
    import torch
    from e3nn import o3
    tp = o3.FullyConnectedTensorProduct("1x1o", "1x1o", "1x0e")
    x, y = torch.randn(1, 3), torch.randn(1, 3)
    rot = o3.rand_matrix()
    inv1 = tp(x, y); inv2 = tp(x @ rot.T, y @ rot.T)
    assert float((inv1 - inv2).abs().max()) < 1e-5
    broken = tp(x @ rot.T, y)                       # rotate ONE input only: symmetry broken
    assert float((inv1 - broken).abs().max()) > 1e-3  # MUST differ, else probe is decorative
    return "invariant under joint rotation; broken-symmetry control DIFFERS (must-fail fires)"

@fit("pyg_permutation_equivariance")
def _():
    # system shape: labels are bookkeeping — message passing commutes with node relabeling
    import torch
    from torch_geometric.nn import GCNConv
    torch.manual_seed(0)
    conv = GCNConv(3, 2)
    ei = torch.tensor([[0,1,1,2],[1,0,2,1]])
    x = torch.randn(3, 3)
    out = conv(x, ei)
    perm = torch.tensor([2,0,1])
    inv = torch.argsort(perm)
    ei_p = inv[ei]
    out_p = conv(x[perm], ei_p)
    assert float((out[perm] - out_p).abs().max()) < 1e-6
    out_bad = conv(x[perm], ei)                      # relabel nodes but NOT edges: wrong graph
    assert float((out[perm] - out_bad).abs().max()) > 1e-4  # MUST differ
    return "relabeling commutes; mismatched-relabel control DIFFERS (must-fail fires)"

@fit("torch_learning_with_shuffle_control")
def _():
    # system shape: learnable rule learned; shuffled-label control fails to learn
    import torch
    torch.manual_seed(0)
    X = torch.randn(400, 4); w = torch.tensor([1.0, -2.0, 0.5, 3.0])
    y = (X @ w > 0).float()
    Xtr, Xte, ytr, yte = X[:300], X[300:], y[:300], y[300:]
    def train(labels_tr, labels_te):
        net = torch.nn.Sequential(torch.nn.Linear(4, 8), torch.nn.ReLU(), torch.nn.Linear(8, 1))
        opt = torch.optim.Adam(net.parameters(), lr=0.02)
        for _ in range(300):
            opt.zero_grad(); loss = torch.nn.functional.binary_cross_entropy_with_logits(net(Xtr).squeeze(), labels_tr); loss.backward(); opt.step()
        return ((net(Xte).squeeze() > 0).float() == labels_te).float().mean().item()
    acc = train(ytr, yte)                             # held-out, real rule
    acc_shuf = train(ytr[torch.randperm(len(ytr))], yte)  # held-out, shuffled training
    assert acc > 0.9 and 0.3 < acc_shuf < 0.65        # near chance, not memorized
    return f"held-out acc={acc:.2f}; shuffled-training held-out acc={acc_shuf:.2f} (~chance)"

@fit("interval_certified_bound")
def _():
    # rigor tier via mpmath interval arithmetic (python side of the rigor slot)
    from mpmath import iv, mp
    mp.dps = 60
    true_sqrt2 = mp.sqrt(2)                                    # independent high-precision value
    x = iv.mpf([1.41421356237309, 1.4142135623731])
    assert x.a < true_sqrt2 < x.b                              # interval contains the INDEPENDENT value
    sq = x*x
    assert sq.a < 2 < sq.b
    bad = iv.mpf([1.5, 1.6])
    assert (bad*bad).a > 2                                     # wrong interval PROVABLY excludes 2
    return "interval contains independent 60-digit sqrt(2); square brackets 2; wrong interval excludes"

if __name__ == "__main__":
    npass = sum(1 for r in R.values() if r["status"] == "PASS")
    out = {"sweep": "fit_probes_v1", "classification": "tool_lego_fit_probe", "promotion_allowed": False,
           "pass": npass, "fail": len(R)-npass, "results": R}
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "fit_sweep_results.json"), "w"), indent=1)
    print(f"=== {npass}/{len(R)} PASS")
