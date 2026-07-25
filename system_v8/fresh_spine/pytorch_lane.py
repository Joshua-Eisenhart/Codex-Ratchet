#!/usr/bin/env python3
"""PyTorch engine lane for fresh_spine fixture v0 (F0-F3).

Reads ONLY system_v8/fresh_spine/fixture_v0.json. Computes every reported
quantity from that raw data with torch tensor operations. No ran/verdict/
load_bearing field is written anywhere: every boolean in the contract is
derived from an integer this script computed in this process.

Engine discipline notes recorded by this lane:
  - integer objects are torch.int64 tensors; float appears only where a float
    is genuinely needed (log2 capacities, the float-SVD rank path, spectra).
  - a TorchFunctionMode census records, at dispatch level, which torch
    functions were actually invoked. That census is emitted to stderr and
    summarised in the stdout diagnostics, so "used torch" is measured here,
    not asserted.
"""

import hashlib
import json
import math
import os
import sys

import torch
from torch.overrides import TorchFunctionMode

FIXTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixture_v0.json")
EXPECTED_FIXTURE_SHA256 = "1ce948f00d82729d2cd0056477ff55942a25efa394f6da11144253e8e60ff9da"
ENGINE_NAME = "pytorch"
LANE_NONCE = "NONCE-TOR-5b1d77"

INT = torch.int64
FLT = torch.float64


# --------------------------------------------------------------------------
# dispatch census: which torch functions this process actually called
# --------------------------------------------------------------------------
class OpCensus(TorchFunctionMode):
    def __init__(self):
        super().__init__()
        self.counts = {}

    def __torch_function__(self, func, types, args=(), kwargs=None):
        kwargs = kwargs or {}
        mod = getattr(func, "__module__", "") or ""
        qn = getattr(func, "__qualname__", None) or getattr(func, "__name__", str(func))
        key = (mod + "." + qn) if mod else str(qn)
        self.counts[key] = self.counts.get(key, 0) + 1
        return func(*args, **kwargs)


CENSUS = OpCensus()
LOG = []


def note(msg):
    LOG.append(msg)


# --------------------------------------------------------------------------
# torch primitives
# --------------------------------------------------------------------------
def t_popcount(x, bits):
    """popcount over an int64 tensor, via torch bitwise shift + and + add."""
    acc = torch.zeros_like(x)
    for b in range(bits):
        acc = acc + torch.bitwise_and(torch.bitwise_right_shift(x, b), 1)
    return acc


def t_log2(n_int):
    """capacity log2(n) computed by torch on a float64 tensor."""
    return float(torch.log2(torch.tensor(float(n_int), dtype=FLT)).item())


def torch_bareiss(M):
    """Fraction-free (Bareiss) elimination on an int64 torch tensor.

    Exact integer arithmetic end to end - no float is created. Returns
    (rank, det_or_None, max_abs_intermediate, all_divisions_exact).
    max_abs_intermediate is measured so int64 overflow can be excluded
    rather than assumed.
    """
    A = M.clone()
    n, m = A.shape
    prev = torch.tensor(1, dtype=INT)
    sign = 1
    row = 0
    max_abs = int(torch.max(torch.abs(A)).item())
    exact = True
    for col in range(m):
        if row >= n:
            break
        piv = -1
        for r in range(row, n):
            if int(A[r, col].item()) != 0:
                piv = r
                break
        if piv < 0:
            continue
        if piv != row:
            tmp = A[row].clone()
            A[row] = A[piv]
            A[piv] = tmp
            sign = -sign
        p = A[row, col].clone()
        for r in range(row + 1, n):
            factor = A[r, col].clone()
            num = A[r, col:] * p - A[row, col:] * factor
            if int(torch.count_nonzero(torch.remainder(num, prev)).item()) != 0:
                exact = False
            cand = int(torch.max(torch.abs(num)).item())
            if cand > max_abs:
                max_abs = cand
            A[r, col:] = torch.div(num, prev, rounding_mode="trunc")
        prev = p
        row += 1
    rank = row
    det = None
    if n == m:
        det = (int(A[n - 1, n - 1].item()) * sign) if rank == n else 0
    return rank, det, max_abs, exact


def py_bareiss(rows):
    """Same algorithm in arbitrary-precision python ints. CONTROL ONLY.

    Its single job is to detect silent int64 overflow in torch_bareiss.
    It is not the engine path and no contract value is taken from it.
    """
    A = [list(r) for r in rows]
    n = len(A)
    m = len(A[0]) if n else 0
    prev = 1
    sign = 1
    row = 0
    max_abs = max((abs(v) for r in A for v in r), default=0)
    for col in range(m):
        if row >= n:
            break
        piv = -1
        for r in range(row, n):
            if A[r][col] != 0:
                piv = r
                break
        if piv < 0:
            continue
        if piv != row:
            A[row], A[piv] = A[piv], A[row]
            sign = -sign
        p = A[row][col]
        for r in range(row + 1, n):
            factor = A[r][col]
            for c in range(col, m):
                num = A[r][c] * p - A[row][c] * factor
                max_abs = max(max_abs, abs(num))
                A[r][c] = num // prev
        prev = p
        row += 1
    rank = row
    det = (A[n - 1][n - 1] * sign) if (n == m and rank == n) else (0 if n == m else None)
    return rank, det, max_abs


def build_adjacency(n, edges):
    """0/1 symmetric int64 adjacency from an undirected edge list."""
    adj = torch.zeros((n, n), dtype=INT)
    if edges:
        E = torch.tensor(edges, dtype=INT)
        adj[E[:, 0], E[:, 1]] = 1
        adj[E[:, 1], E[:, 0]] = 1
    return adj


def components_from_adjacency(adj):
    """Connected components by int64 boolean-matmul reachability closure."""
    n = adj.shape[0]
    reach = torch.clamp(adj + torch.eye(n, dtype=INT), max=1)
    steps = 0
    for _ in range(n + 1):
        nxt = (torch.matmul(reach, reach) > 0).to(INT)
        steps += 1
        if bool(torch.equal(nxt, reach)):
            break
        reach = nxt
    return int(torch.unique(reach, dim=0).shape[0]), steps


def graph_report(name, n, edges):
    adj = build_adjacency(n, edges)
    deg = torch.sum(adj, dim=1)
    e_from_adj = int(torch.sum(adj).item()) // 2
    comps, steps = components_from_adjacency(adj)
    degseq = sorted(int(v) for v in deg.tolist())
    rep = {
        "name": name,
        "vertices": n,
        "edges_in_list": len(edges),
        "edges_from_adjacency": e_from_adj,
        "edge_list_has_duplicates": len(edges) != e_from_adj,
        "degree_sequence": degseq,
        "degree_multiset": sorted(set(degseq)),
        "components": comps,
        "closure_steps": steps,
        "independent_cycles": e_from_adj - n + comps,
    }
    return rep, adj, degseq


# --------------------------------------------------------------------------
# main computation
# --------------------------------------------------------------------------
def main():
    raw = open(FIXTURE_PATH, "rb").read()
    got_sha = hashlib.sha256(raw).hexdigest()
    if got_sha != EXPECTED_FIXTURE_SHA256:
        print("FIXTURE SHA MISMATCH: got %s expected %s" % (got_sha, EXPECTED_FIXTURE_SHA256),
              file=sys.stderr)
        return 2
    fx = json.loads(raw.decode("utf-8"))
    note("fixture sha256 recomputed in-process and matched: %s" % got_sha)

    n_bits = fx["n"]
    J_list = fx["J"]
    N = len(J_list)
    J = torch.tensor(J_list, dtype=INT)
    note("n=%d, |J|=%d, J dtype=%s" % (n_bits, N, J.dtype))

    detail = {}

    # ---------------- F0 PAIR-FIELD FLOOR ----------------
    XOR = torch.bitwise_xor(J.unsqueeze(1), J.unsqueeze(0))          # 16x16 int64
    POP = t_popcount(XOR, n_bits)                                     # 16x16 int64
    F_diag = (POP == 0).to(INT)
    F_coh = (POP <= 1).to(INT)

    # sanity on the field definitions, computed not assumed
    assert bool(torch.equal(F_diag, torch.eye(N, dtype=INT)))

    f0 = {}
    for label, F in (("diag", F_diag), ("coh", F_coh)):
        nz_ordered = int(torch.count_nonzero(F).item())
        # unordered reading of "pair support", kept as a diagnostic only
        upper = torch.triu(F, diagonal=1)
        nz_unordered = int(torch.count_nonzero(upper).item()) + int(
            torch.count_nonzero(torch.diagonal(F)).item())

        a0 = t_log2(N)
        a1 = t_log2(nz_ordered)

        # engine rank path: float SVD (torch.linalg.matrix_rank)
        int_refusal = None
        try:
            torch.linalg.matrix_rank(F)
            int_refusal = "accepted int64 (unexpected)"
        except Exception as exc:  # measured, not assumed
            int_refusal = "%s: %s" % (type(exc).__name__, str(exc).strip())
        Ff = F.to(FLT)
        rank_svd = int(torch.linalg.matrix_rank(Ff).item())
        svals = torch.linalg.svdvals(Ff)
        eigs = torch.linalg.eigvalsh(Ff)
        det_float = float(torch.linalg.det(Ff).item())

        # exact integer path, in torch int64, no float
        rank_exact, det_exact, max_abs, div_exact = torch_bareiss(F)
        # arbitrary-precision control to exclude int64 overflow
        rank_py, det_py, max_abs_py = py_bareiss(F.tolist())

        f0[label] = {
            "a0": a0,
            "a1": a1,
            "a2_rank_float_svd": rank_svd,
            "a2_rank_exact_int64_bareiss": rank_exact,
            "a2_ranks_agree": rank_svd == rank_exact,
            "nonzero_entries_ordered": nz_ordered,
            "nonzero_pairs_unordered_diagnostic": nz_unordered,
            "det_exact_int64_bareiss": det_exact,
            "det_float_linalg": det_float,
            "bareiss_divisions_exact": div_exact,
            "bareiss_max_abs_intermediate_torch": max_abs,
            "bareiss_max_abs_intermediate_pyint_control": max_abs_py,
            "int64_overflow_excluded": (max_abs == max_abs_py
                                        and rank_exact == rank_py
                                        and det_exact == det_py),
            "pyint_control_rank": rank_py,
            "pyint_control_det": det_py,
            "matrix_rank_on_int64_response": int_refusal,
            "singular_value_min": float(torch.min(svals).item()),
            "singular_value_max": float(torch.max(svals).item()),
            "eigenvalue_abs_min": float(torch.min(torch.abs(eigs)).item()),
            "eigenvalues_sorted": [round(float(v), 12) for v in eigs.tolist()],
        }
    detail["f0"] = f0
    note("F0 A0 identical by construction (same J): diag %.17g vs coh %.17g"
         % (f0["diag"]["a0"], f0["coh"]["a0"]))
    note("F0 A1 separates: diag %.17g (support %d) vs coh %.17g (support %d)"
         % (f0["diag"]["a1"], f0["diag"]["nonzero_entries_ordered"],
            f0["coh"]["a1"], f0["coh"]["nonzero_entries_ordered"]))
    note("F0 A2 does NOT separate: rank %d vs %d (computed, not by construction)"
         % (f0["diag"]["a2_rank_float_svd"], f0["coh"]["a2_rank_float_svd"]))

    # ---------------- F1 QUOTIENT / FIBRE ----------------
    q = t_popcount(J, n_bits)
    q2 = torch.remainder(J, 5)

    def fibres(qvals, q_size):
        sizes = torch.bincount(qvals, minlength=q_size)
        out = []
        for y in range(q_size):
            mask = qvals == y
            members = [int(v) for v in torch.masked_select(J, mask).tolist()]
            members.sort()
            out.append({"y": y, "members": members, "size": len(members)})
        return sizes, out

    sizes_q, fib_q = fibres(q, 5)
    sizes_q2, fib_q2 = fibres(q2, 5)

    kappa = []
    release_descriptors = []
    for f in fib_q:
        if f["size"] == 0:
            # NO arithmetic on an empty fibre. Release_q(y) yields the descriptor.
            kappa.append(None)
            release_descriptors.append({"y": f["y"], "empty": True, "fibre": [],
                                        "release": "descriptor_only_no_capacity"})
        else:
            kappa.append(t_log2(f["size"]))
            release_descriptors.append({"y": f["y"], "empty": False,
                                        "fibre": f["members"],
                                        "release": "fibre_descriptor"})

    f1_sizes = [int(v) for v in sizes_q.tolist()]
    f1_q2_sizes = [int(v) for v in sizes_q2.tolist()]
    detail["f1"] = {
        "q_definition": "q(j) = popcount(j), computed by torch bitwise shift/and/add",
        "q2_definition": "q2(j) = j mod 5, computed by torch.remainder",
        "fibres_q": fib_q,
        "fibres_q2": fib_q2,
        "size_multiset_q": sorted(f1_sizes),
        "size_multiset_q2": sorted(f1_q2_sizes),
        "quotients_distinguished_by_size_multiset": sorted(f1_sizes) != sorted(f1_q2_sizes),
        "same_codomain_cardinality": len(f1_sizes) == len(f1_q2_sizes),
        "any_empty_fibre_q": any(v == 0 for v in f1_sizes),
        "any_empty_fibre_q2": any(v == 0 for v in f1_q2_sizes),
        "release_q_descriptors": release_descriptors,
        "sizes_sum_equals_J": int(torch.sum(sizes_q).item()) == N,
    }
    note("F1 fibre sizes by enumeration: %s ; q2 sizes: %s" % (f1_sizes, f1_q2_sizes))

    # ---------------- F2 PRESENTATION GEOMETRY ----------------
    checker_edges = [list(map(int, e)) for e in fx["presentations"]["checker"]["edges"]]
    ring_edges = [list(map(int, e)) for e in fx["presentations"]["ring"]["edges"]]
    spun_edges_fixture = [list(map(int, e)) for e in fx["presentations"]["spun"]["edges"]]
    sigma = [int(v) for v in fx["presentations"]["spun"]["relabelling"]]

    # transition map CHECKER <- ring order, and RING -> SPUN, both explicit
    gray = [int(v) for v in fx["presentations"]["ring"]["gray_code_order"]]
    sigma_t = torch.tensor(sigma, dtype=INT)
    sigma_is_bijection = int(torch.unique(sigma_t).numel()) == N

    # rebuild CHECKER from its stated definition and compare to the fixture list
    checker_derived = []
    POP_np = POP.tolist()
    for a in range(N):
        for b in range(a + 1, N):
            if POP_np[a][b] == 1:
                checker_derived.append([a, b])
    checker_matches_definition = sorted(checker_derived) == sorted(checker_edges)

    # rebuild RING from the gray code order and compare
    ring_derived = []
    for i in range(N):
        a, b = gray[i], gray[(i + 1) % N]
        ring_derived.append([min(a, b), max(a, b)])
    ring_matches_definition = sorted(ring_derived) == sorted(ring_edges)

    # apply sigma to RING to obtain SPUN, compare with the fixture's spun list
    spun_derived = []
    for a, b in ring_edges:
        x, y = sigma[a], sigma[b]
        spun_derived.append([min(x, y), max(x, y)])
    spun_matches_relabelling = sorted(spun_derived) == sorted(spun_edges_fixture)

    rep_checker, adj_checker, deg_checker = graph_report("checker", N, checker_edges)
    rep_ring, adj_ring, deg_ring = graph_report("ring", N, ring_edges)
    rep_spun, adj_spun, deg_spun = graph_report("spun", N, spun_edges_fixture)

    # N1 SEAM-BROKEN RING: delete one declared ring edge
    cut_edge = ring_edges[0]
    ring_cut_edges = [e for e in ring_edges if e != cut_edge]
    rep_ring_cut, _, _ = graph_report("ring_minus_%s" % cut_edge, N, ring_cut_edges)

    # N2 BAD ADJACENCY: add an edge at Hamming distance 3 in CHECKER
    n2_pair = [0, 7]
    n2_hamming = int(POP[n2_pair[0], n2_pair[1]].item())
    checker_plus = checker_edges + [n2_pair]
    rep_checker_n2, _, deg_checker_n2 = graph_report("checker_plus_bad_edge", N, checker_plus)
    n2_degree_changed = deg_checker_n2 != deg_checker

    # N3 NO-MAP CLAIM
    n3_edge_counts_differ = rep_checker["edges_from_adjacency"] != rep_ring["edges_from_adjacency"]

    detail["f2"] = {
        "checker": rep_checker,
        "ring": rep_ring,
        "spun": rep_spun,
        "spun_contract_gap": "the output contract declares no f2_spun_* key, so a lane can omit SPUN entirely and still satisfy it literally; SPUN is reported here anyway",
        "transition_maps": {
            "gray_code_order_from_fixture": gray,
            "sigma_from_fixture": sigma,
            "sigma_is_bijection_verified_by_enumeration": sigma_is_bijection,
            "checker_edges_match_stated_definition": checker_matches_definition,
            "ring_edges_match_gray_order": ring_matches_definition,
            "spun_edges_match_sigma_of_ring": spun_matches_relabelling,
        },
        "n1": {
            "cut_edge": cut_edge,
            "cycles_before": rep_ring["independent_cycles"],
            "cycles_after": rep_ring_cut["independent_cycles"],
            "cycle_count_dropped": rep_ring_cut["independent_cycles"] < rep_ring["independent_cycles"],
            "components_after": rep_ring_cut["components"],
        },
        "n2": {
            "added_edge": n2_pair,
            "hamming_distance_computed": n2_hamming,
            "degree_sequence_before": deg_checker,
            "degree_sequence_after": deg_checker_n2,
            "degree_changed": n2_degree_changed,
        },
        "n3": {
            "checker_edges": rep_checker["edges_from_adjacency"],
            "ring_edges": rep_ring["edges_from_adjacency"],
            "edge_counts_differ": n3_edge_counts_differ,
            # derived, not asserted: a differing isomorphism invariant excludes the claim
            "same_object_claim_excluded_by_computed_invariant": bool(n3_edge_counts_differ),
            "ground": "edge count is an isomorphism invariant; the two computed counts differ, which excludes identification. A topology tool may measure a supplied complex; without the transition map it cannot license a global identity claim.",
        },
        "independent_cycles_definition": "edges - vertices + components (cycle rank / first Betti number), NOT a count of cycles",
    }
    note("F2 checker E=%d V=%d C=%d cyc=%d ; ring E=%d cyc=%d ; spun E=%d cyc=%d"
         % (rep_checker["edges_from_adjacency"], rep_checker["vertices"],
            rep_checker["components"], rep_checker["independent_cycles"],
            rep_ring["edges_from_adjacency"], rep_ring["independent_cycles"],
            rep_spun["edges_from_adjacency"], rep_spun["independent_cycles"]))

    # ---------------- F3 NESTED CONSTRAINTS AND REWRITES ----------------
    r_map = torch.bitwise_and(J, 3)                                    # low two bits
    E_ck = torch.tensor(checker_edges, dtype=INT)
    rj = r_map[E_ck[:, 0]]
    rk = r_map[E_ck[:, 1]]
    rx = torch.bitwise_xor(rj, rk)
    rpop = t_popcount(rx, 2)
    seam_ok = torch.logical_or(rj == rk, rpop == 1)
    seam_satisfied = int(torch.count_nonzero(seam_ok).item())
    seam_total = int(E_ck.shape[0])

    # R1 CONTRACT
    quotient_vertices = int(torch.unique(r_map).numel())
    self_loop_mask = rj == rk
    self_loops = int(torch.count_nonzero(self_loop_mask).item())
    nonloop = seam_total - self_loops
    qedges = {}
    for i in range(seam_total):
        a, b = int(rj[i].item()), int(rk[i].item())
        if a == b:
            continue
        key = (min(a, b), max(a, b))
        qedges[key] = qedges.get(key, 0) + 1
    quotient_simple_edges = len(qedges)

    # R2 OBSTRUCT
    r2_pair = [0b0000, 0b0111]
    r2_hamming = int(POP[r2_pair[0], r2_pair[1]].item())
    E_r2 = torch.tensor(checker_edges + [r2_pair], dtype=INT)
    rj2 = r_map[E_r2[:, 0]]
    rk2 = r_map[E_r2[:, 1]]
    rpop2 = t_popcount(torch.bitwise_xor(rj2, rk2), 2)
    seam_ok2 = torch.logical_or(rj2 == rk2, rpop2 == 1)
    violating_idx = torch.masked_select(torch.arange(E_r2.shape[0], dtype=INT),
                                        torch.logical_not(seam_ok2))
    violating = [ [int(E_r2[i,0].item()), int(E_r2[i,1].item())] for i in violating_idx.tolist() ]
    r2_violating_edges = len(violating)
    r2_blocked = r2_violating_edges > 0     # NO-REPAIR policy: nothing is adjusted

    detail["f3"] = {
        "r_definition": "r(j) = j AND 0b11 (low two bits), torch.bitwise_and",
        "seam_obligation": "for every CHECKER edge (j,k): r(j)==r(k) OR popcount(r(j) XOR r(k))==1",
        "seam_satisfied_edges": seam_satisfied,
        "seam_total_edges": seam_total,
        "seam_positive_check_has_no_discriminating_power": seam_satisfied == seam_total,
        "seam_why_no_teeth": "a Q4 edge flips exactly one bit; that bit is low (r differs in one bit) or high (r equal). 32/32 is forced by the carrier, so this check cannot fail here.",
        "r1_contract": {
            "quotient_vertices": quotient_vertices,
            "edges_becoming_self_loops": self_loops,
            "edges_mapping_to_quotient_edges": nonloop,
            "quotient_simple_edges_excluding_loops": quotient_simple_edges,
            "quotient_edge_multiplicities": {"%d-%d" % k: v for k, v in sorted(qedges.items())},
            "quotient_total_edges_with_multiplicity_including_loops": seam_total,
            # derived: every carrier edge is accounted for as either a loop or a quotient edge
            "edge_accounting_closes": bool(self_loops + nonloop == seam_total),
            "note": "R1 applied; quotient carrier is the 4-vertex bit-flip graph on the r-images",
            "ambiguity": "'the quotient graph' admits 4 (simple), 20 (simple+loops) or 32 (all with multiplicity); only quotient_vertices is pinned by the contract",
        },
        "r2_obstruct": {
            "added_edge": r2_pair,
            "hamming_distance_computed": r2_hamming,
            "r_images": [int(r_map[r2_pair[0]].item()), int(r_map[r2_pair[1]].item())],
            "r_image_hamming": int(t_popcount(torch.bitwise_xor(r_map[r2_pair[0]], r_map[r2_pair[1]]), 2).item()),
            "violating_edges": violating,
            "violating_edge_count": r2_violating_edges,
            "seam_satisfied_after": int(torch.count_nonzero(seam_ok2).item()),
            "seam_total_after": int(E_r2.shape[0]),
            # derived from the computed violating count, not asserted
            "blocked_under_no_repair": r2_blocked,
            "note": "obstruction survives; no value was adjusted to make the check pass",
            "repair_policy": "NO-REPAIR: resettlement is only by applying a declared rewrite",
        },
    }
    note("F3 seam %d/%d (forced by carrier); R1 quotient V=%d; R2 violating=%d blocked=%s"
         % (seam_satisfied, seam_total, quotient_vertices, r2_violating_edges, r2_blocked))

    # ---------------- float honesty ----------------
    detail["float_notes"] = {
        "torch_log2_vs_math_log2": {
            "log2_80_torch": t_log2(80),
            "log2_80_math": math.log2(80),
            "identical_bits": t_log2(80) == math.log2(80),
            "log2_6_torch": t_log2(6),
            "log2_6_math": math.log2(6),
            "identical_bits_6": t_log2(6) == math.log2(6),
        },
        "dtype_policy": "int64 for all combinatorics and the exact rank; float64 only for log2 capacities, SVD/eig, and linalg.det",
        "matrix_rank_int64": "torch.linalg.matrix_rank rejects int64 outright; the float64 cast is mandatory, so the engine rank path is a float SVD by construction",
    }

    # ---------------- contract ----------------
    contract = {
        "f0_diag_a0": f0["diag"]["a0"],
        "f0_diag_a1": f0["diag"]["a1"],
        "f0_diag_a2": f0["diag"]["a2_rank_exact_int64_bareiss"],
        "f0_coh_a0": f0["coh"]["a0"],
        "f0_coh_a1": f0["coh"]["a1"],
        "f0_coh_a2": f0["coh"]["a2_rank_exact_int64_bareiss"],
        "f1_fibre_sizes": f1_sizes,
        "f1_kappa": kappa,
        "f1_q2_fibre_sizes": f1_q2_sizes,
        "f2_checker_edges": rep_checker["edges_from_adjacency"],
        "f2_ring_edges": rep_ring["edges_from_adjacency"],
        "f2_checker_cycles": rep_checker["independent_cycles"],
        "f2_ring_cycles": rep_ring["independent_cycles"],
        "f2_n1_ring_cycles_after_cut": rep_ring_cut["independent_cycles"],
        "f2_n2_degree_changed": bool(n2_degree_changed),
        "f2_n3_edge_counts_differ": bool(n3_edge_counts_differ),
        "f3_seam_satisfied_edges": seam_satisfied,
        "f3_seam_total_edges": seam_total,
        "f3_r1_quotient_vertices": quotient_vertices,
        "f3_r2_violating_edges": r2_violating_edges,
        "f3_r2_blocked": bool(r2_blocked),
        "engine_name": ENGINE_NAME,
        "lane_nonce": LANE_NONCE,
    }

    # ---------------- diagnostics to stdout, contract as the LAST line ----------------
    print("=== pytorch lane :: fresh_spine fixture v0 ===")
    print("interpreter      : %s" % sys.executable)
    print("python           : %s" % sys.version.split()[0])
    print("torch            : %s   default_dtype=%s" % (torch.__version__, torch.get_default_dtype()))
    print("fixture          : %s" % FIXTURE_PATH)
    print("fixture sha256   : %s (recomputed in-process, matched)" % got_sha)
    print()
    for line in LOG:
        print("note  " + line)
    print()
    census_snapshot = dict(CENSUS.counts)
    print("--- torch dispatch census (functions this process actually invoked) ---")
    for k, v in sorted(census_snapshot.items(), key=lambda kv: (-kv[1], kv[0])):
        print("  %6d  %s" % (v, k))
    print("  distinct torch functions dispatched: %d ; total dispatches: %d"
          % (len(census_snapshot), sum(census_snapshot.values())))
    print()
    print("--- detail ---")
    print(json.dumps(detail, indent=2, sort_keys=True))
    print()
    print("--- census (json) ---")
    print(json.dumps({"distinct": len(census_snapshot),
                      "total": sum(census_snapshot.values()),
                      "counts": census_snapshot}, sort_keys=True))
    print()
    print(json.dumps(contract, sort_keys=True))
    return 0


if __name__ == "__main__":
    with CENSUS:
        rc = main()
    sys.exit(rc)
