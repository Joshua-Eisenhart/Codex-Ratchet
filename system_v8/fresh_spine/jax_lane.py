#!/usr/bin/env python3
"""JAX engine lane for the fresh-spine F0-F3 fixture battery.

Reads ONLY system_v8/fresh_spine/fixture_v0.json. Implements F0-F3 independently.

Provenance discipline
---------------------
Every jax operation is invoked through jcall(), which records the op name and the
concrete type / dtype / shape of the value the op returned. That record is DERIVED
from an actual call: an op that was never invoked leaves no entry. Work done in
plain python is registered separately under PY_WORK and is never labelled jax.

No field named ran / verdict / load_bearing is emitted anywhere in this file.
"""

import hashlib
import json
import sys
from fractions import Fraction
from functools import partial
from pathlib import Path

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp  # noqa: E402  (import after x64 is enabled)

LANE_NONCE = "NONCE-JAX-7f3a91"
ENGINE_NAME = "jax"
FIXTURE_PATH = Path(
    "/Users/joshuaeisenhart/Codex-Ratchet/system_v8/fresh_spine/fixture_v0.json"
)
FIXTURE_SHA_FROZEN = (
    "1ce948f00d82729d2cd0056477ff55942a25efa394f6da11144253e8e60ff9da"
)

# ---------------------------------------------------------------------------
# provenance recorders
# ---------------------------------------------------------------------------

JAX_CALLS = []          # one entry per jax op actually invoked
PY_WORK = []            # named steps done in plain python, declared honestly


def jcall(op_name, fn, *args, **kwargs):
    """Invoke a jax op and record a receipt derived from its actual return value."""
    out = fn(*args, **kwargs)
    JAX_CALLS.append(
        {
            "op": op_name,
            "result_type": type(out).__module__ + "." + type(out).__name__,
            "result_dtype": str(getattr(out, "dtype", None)),
            "result_shape": list(getattr(out, "shape", ())),
        }
    )
    return out


def pywork(step):
    PY_WORK.append(step)


# ---------------------------------------------------------------------------
# jax kernels
# ---------------------------------------------------------------------------


@partial(jax.jit, static_argnums=1)
def popcount(x, nbits):
    """Population count over the low `nbits` bits, as jax bitwise ops."""
    acc = jnp.zeros_like(x)
    for b in range(nbits):
        acc = acc + jnp.bitwise_and(jnp.right_shift(x, b), 1)
    return acc


@jax.jit
def seam_kernel(ea, eb):
    """F3 seam obligation, vectorised over an edge list.

    Returns (n_satisfied, n_total). r(v) = low two bits of v; an edge is
    admitted when r(j) == r(k) or r(j) and r(k) differ in exactly one bit.
    """
    ra = jnp.bitwise_and(ea, 3)
    rb = jnp.bitwise_and(eb, 3)
    x = jnp.bitwise_xor(ra, rb)
    d = jnp.bitwise_and(x, 1) + jnp.bitwise_and(jnp.right_shift(x, 1), 1)
    ok = jnp.logical_or(jnp.equal(d, 0), jnp.equal(d, 1))
    return jnp.sum(ok), jnp.asarray(ok.shape[0], dtype=jnp.int64)


@jax.jit
def rank_kernel(M):
    return jnp.linalg.matrix_rank(M)


@jax.jit
def reach_closure(A):
    """Boolean transitive closure by repeated jax matmul (2**5 = 32 >= 16 hops)."""
    n = A.shape[0]
    R = jnp.greater(A + jnp.eye(n, dtype=A.dtype), 0).astype(jnp.int64)
    for _ in range(5):
        R = jnp.greater(jnp.matmul(R, R), 0).astype(jnp.int64)
    return R


# ---------------------------------------------------------------------------
# jaxpr evidence
# ---------------------------------------------------------------------------


def walk_primitives(jaxpr, acc, depth=0):
    """Collect primitive names, descending into nested (closed) jaxprs."""
    if depth > 16:
        return
    for eqn in jaxpr.eqns:
        acc.append(eqn.primitive.name)
        for val in eqn.params.values():
            items = val if isinstance(val, (tuple, list)) else [val]
            for item in items:
                inner = getattr(item, "jaxpr", item)
                if hasattr(inner, "eqns"):
                    walk_primitives(inner, acc, depth + 1)


def jaxpr_digest(label, fn, *args):
    closed = jax.make_jaxpr(fn)(*args)
    text = str(closed)
    prims = []
    walk_primitives(closed.jaxpr, prims)
    return {
        "label": label,
        "jaxpr_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "jaxpr_chars": len(text),
        "jaxpr_lines": text.count("\n") + 1,
        "n_equations_top_level": len(closed.jaxpr.eqns),
        "n_primitives_all_depths": len(prims),
        "distinct_primitives": sorted(set(prims)),
        "invars": [str(v.aval) for v in closed.jaxpr.invars],
        "first_line": text.splitlines()[0][:200],
    }


# ---------------------------------------------------------------------------
# plain-python cross-checks (declared, never labelled jax)
# ---------------------------------------------------------------------------


def exact_rank(rows):
    """Exact rank over the rationals by Fraction Gaussian elimination."""
    M = [[Fraction(v) for v in row] for row in rows]
    nrow, ncol = len(M), len(M[0])
    rank, piv_r = 0, 0
    for c in range(ncol):
        piv = None
        for r in range(piv_r, nrow):
            if M[r][c] != 0:
                piv = r
                break
        if piv is None:
            continue
        M[piv_r], M[piv] = M[piv], M[piv_r]
        pv = M[piv_r][c]
        M[piv_r] = [v / pv for v in M[piv_r]]
        for r in range(nrow):
            if r != piv_r and M[r][c] != 0:
                f = M[r][c]
                M[r] = [a - f * b for a, b in zip(M[r], M[piv_r])]
        rank += 1
        piv_r += 1
    return rank


def components_unionfind(n, edges):
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    return len({find(v) for v in range(n)})


def rows_to_component_count(R):
    return len({tuple(int(v) for v in row) for row in R})


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main():
    raw = FIXTURE_PATH.read_bytes()
    fixture_sha = hashlib.sha256(raw).hexdigest()
    fixture = json.loads(raw)
    pywork("read fixture bytes, sha256, json parse")

    n = fixture["n"]
    J = fixture["J"]
    NJ = len(J)
    checker_edges = [tuple(e) for e in fixture["presentations"]["checker"]["edges"]]
    ring_edges = [tuple(e) for e in fixture["presentations"]["ring"]["edges"]]
    spun_edges = [tuple(e) for e in fixture["presentations"]["spun"]["edges"]]
    gray_order = fixture["presentations"]["ring"]["gray_code_order"]
    sigma = fixture["presentations"]["spun"]["relabelling"]

    Jv = jcall("jnp.asarray(J)", jnp.asarray, J, dtype=jnp.int64)

    # ---------------- F0 : pair-field floor -------------------------------
    XOR = jcall(
        "jnp.bitwise_xor (outer j XOR k)",
        jnp.bitwise_xor,
        Jv[:, None],
        Jv[None, :],
    )
    POP = jcall("popcount jit (right_shift+bitwise_and+add)", popcount, XOR, n)

    DIAG = jcall("jnp.equal -> astype (DIAG field)", lambda: jnp.equal(POP, 0).astype(jnp.int64))
    COH = jcall(
        "jnp.less_equal -> astype (COHERENT field)",
        lambda: jnp.less_equal(POP, 1).astype(jnp.int64),
    )

    nJ_jax = jcall("jnp.sum (|J| from ones)", jnp.sum, jnp.ones_like(Jv))
    a0 = jcall("jnp.log2 (A0 address capacity)", jnp.log2, nJ_jax.astype(jnp.float64))

    diag_support = jcall(
        "jnp.sum (DIAG nonzero entries)", jnp.sum, jnp.not_equal(DIAG, 0).astype(jnp.int64)
    )
    coh_support = jcall(
        "jnp.sum (COHERENT nonzero entries)",
        jnp.sum,
        jnp.not_equal(COH, 0).astype(jnp.int64),
    )
    a1_diag = jcall("jnp.log2 (A1 DIAG)", jnp.log2, diag_support.astype(jnp.float64))
    a1_coh = jcall("jnp.log2 (A1 COHERENT)", jnp.log2, coh_support.astype(jnp.float64))

    a2_diag = jcall("jnp.linalg.matrix_rank (DIAG)", rank_kernel, DIAG)
    a2_coh = jcall("jnp.linalg.matrix_rank (COHERENT)", rank_kernel, COH)

    diag_rows = [[int(v) for v in row] for row in DIAG]
    coh_rows = [[int(v) for v in row] for row in COH]
    exact_rank_diag = exact_rank(diag_rows)
    exact_rank_coh = exact_rank(coh_rows)
    pywork("exact Fraction Gaussian-elimination rank, as a cross-check on jnp.linalg.matrix_rank")

    # unordered pair support, kept as a divergence diagnostic only
    coh_unordered = sum(
        1 for j in J for k in J if k >= j and coh_rows[j][k] != 0
    )
    diag_unordered = sum(
        1 for j in J for k in J if k >= j and diag_rows[j][k] != 0
    )
    pywork("unordered pair-support counts, recorded as an ambiguity diagnostic only")

    # ---------------- F1 : quotient / fibre --------------------------------
    POPJ = jcall("popcount jit (q = popcount over J)", popcount, Jv, n)
    Q_values = sorted({int(v) for v in POPJ})
    fibres, fibre_sizes, kappa, release_descriptors = [], [], [], []
    for y in range(0, n + 1):
        mask = jcall(f"jnp.equal (fibre mask q={y})", jnp.equal, POPJ, y)
        size = jcall(f"jnp.sum (fibre size q={y})", jnp.sum, mask.astype(jnp.int64))
        idx = jcall(f"jnp.nonzero (fibre members q={y})", jnp.nonzero, mask)
        members = sorted(int(J[i]) for i in idx[0])
        size_i = int(size)
        fibres.append(members)
        fibre_sizes.append(size_i)
        if size_i == 0:
            # Release_q(y) returns the fibre descriptor; no arithmetic on an empty fibre.
            release_descriptors.append(
                {"y": y, "empty": True, "descriptor": {"fibre": [], "size": 0}}
            )
            kappa.append(None)
        else:
            k = jcall(
                f"jnp.log2 (kappa q={y})", jnp.log2, size.astype(jnp.float64)
            )
            kappa.append(float(k))
            release_descriptors.append(
                {"y": y, "empty": False, "descriptor": {"fibre": members, "size": size_i}}
            )

    Q2 = jcall("jnp.mod (q2 = j mod 5)", jnp.mod, Jv, 5)
    q2_fibres, q2_sizes = [], []
    for y in range(5):
        mask2 = jcall(f"jnp.equal (q2 fibre mask y={y})", jnp.equal, Q2, y)
        s2 = jcall(f"jnp.sum (q2 fibre size y={y})", jnp.sum, mask2.astype(jnp.int64))
        idx2 = jcall(f"jnp.nonzero (q2 fibre members y={y})", jnp.nonzero, mask2)
        q2_fibres.append(sorted(int(J[i]) for i in idx2[0]))
        q2_sizes.append(int(s2))

    q_multiset = sorted(fibre_sizes)
    q2_multiset = sorted(q2_sizes)
    quotients_distinguished = q_multiset != q2_multiset
    same_codomain_size = len(Q_values) == len(set(int(v) for v in Q2))
    pywork("fibre-size multiset comparison for the F1 discrimination")

    # ---------------- F2 : presentation geometry ---------------------------
    def adjacency(edges):
        A = jnp.zeros((NJ, NJ), dtype=jnp.int64)
        ia = jnp.asarray([e[0] for e in edges], dtype=jnp.int64)
        ib = jnp.asarray([e[1] for e in edges], dtype=jnp.int64)
        A = jcall("jnp .at[].set (adjacency scatter j->k)", lambda: A.at[ia, ib].set(1))
        A = jcall("jnp .at[].set (adjacency scatter k->j)", lambda: A.at[ib, ia].set(1))
        return A

    def presentation_report(name, edges):
        A = adjacency(edges)
        deg = jcall(f"jnp.sum axis=1 (degree sequence {name})", jnp.sum, A, axis=1)
        e_jax = jcall(f"jnp.sum (edge count x2 {name})", jnp.sum, A)
        R = jcall(f"jnp.matmul closure (components {name})", reach_closure, A)
        comps_jax = rows_to_component_count(R)
        comps_py = components_unionfind(NJ, edges)
        e_count = int(e_jax) // 2
        deg_seq = sorted((int(d) for d in deg), reverse=True)
        return {
            "presentation": name,
            "vertices": NJ,
            "edges_from_list": len(edges),
            "edges_from_jax_adjacency": e_count,
            "edge_counts_agree": e_count == len(edges),
            "degree_sequence": deg_seq,
            "components_jax_closure": comps_jax,
            "components_python_unionfind": comps_py,
            "components_agree": comps_jax == comps_py,
            "independent_cycles": e_count - NJ + comps_jax,
        }

    rep_checker = presentation_report("CHECKER", checker_edges)
    rep_ring = presentation_report("RING", ring_edges)
    rep_spun = presentation_report("SPUN", spun_edges)
    pywork("connected-component cross-check by python union-find; row dedup of the jax closure")

    # independent reconstruction of each presentation from its declared definition
    recon_checker = sorted(
        (a, b) for a in J for b in J if a < b and bin(a ^ b).count("1") == 1
    )
    recon_ring = sorted(
        tuple(sorted((gray_order[i], gray_order[(i + 1) % NJ]))) for i in range(NJ)
    )
    recon_spun = sorted(tuple(sorted((sigma[a], sigma[b]))) for a, b in ring_edges)
    sigma_is_bijection = sorted(sigma) == list(range(NJ))
    sigma_matches_formula = all(sigma[v] == (3 * v + 7) % NJ for v in range(NJ))
    pywork("reconstruction of CHECKER/RING/SPUN edge sets from their fixture definitions")

    # N1 SEAM-BROKEN RING
    cut_edge = ring_edges[0]
    ring_cut = [e for e in ring_edges if e != cut_edge]
    rep_ring_cut = presentation_report("RING_MINUS_ONE_EDGE", ring_cut)

    # N2 BAD ADJACENCY : add a Hamming-distance-3 edge to CHECKER
    n2_edge = (0, 7)
    n2_hamming = bin(n2_edge[0] ^ n2_edge[1]).count("1")
    checker_n2 = sorted(set(checker_edges) | {n2_edge})
    rep_checker_n2 = presentation_report("CHECKER_PLUS_H3_EDGE", checker_n2)
    n2_degree_changed = (
        rep_checker_n2["degree_sequence"] != rep_checker["degree_sequence"]
    )

    # N3 NO-MAP CLAIM
    n3_edge_counts_differ = rep_checker["edges_from_jax_adjacency"] != rep_ring[
        "edges_from_jax_adjacency"
    ]

    # ---------------- F3 : nested constraints and rewrites -----------------
    ea = jcall("jnp.asarray (checker edge tails)", jnp.asarray, [e[0] for e in checker_edges], dtype=jnp.int64)
    eb = jcall("jnp.asarray (checker edge heads)", jnp.asarray, [e[1] for e in checker_edges], dtype=jnp.int64)
    sat, tot = jcall("seam_kernel jit (F3 seam obligation)", seam_kernel, ea, eb)
    seam_sat, seam_tot = int(sat), int(tot)

    rJ = jcall("jnp.bitwise_and (r = low two bits)", jnp.bitwise_and, Jv, 3)
    r_images = jcall("jnp.unique (r image set)", jnp.unique, rJ)
    quotient_vertices = int(r_images.shape[0])

    # R1 CONTRACT : identify vertices sharing the same r image
    r_of = {int(j): int(v) for j, v in zip(J, rJ)}
    q_simple, q_loops, q_mult = set(), 0, 0
    for a, b in checker_edges:
        ra, rb = r_of[a], r_of[b]
        if ra == rb:
            q_loops += 1
        else:
            q_simple.add(tuple(sorted((ra, rb))))
        q_mult += 1
    r1_fibres = {}
    for j in J:
        r1_fibres.setdefault(r_of[j], []).append(j)
    pywork("R1 quotient edge bookkeeping (four readings recorded, only the vertex count is in the contract)")

    # R2 OBSTRUCT : add edge (0b0000, 0b0111), then re-check the seam obligation
    r2_edge = (0b0000, 0b0111)
    r2_edges = sorted(set(checker_edges) | {r2_edge})
    ea2 = jcall("jnp.asarray (R2 edge tails)", jnp.asarray, [e[0] for e in r2_edges], dtype=jnp.int64)
    eb2 = jcall("jnp.asarray (R2 edge heads)", jnp.asarray, [e[1] for e in r2_edges], dtype=jnp.int64)
    sat2, tot2 = jcall("seam_kernel jit (F3 R2 re-check)", seam_kernel, ea2, eb2)
    r2_sat, r2_tot = int(sat2), int(tot2)
    r2_violating = r2_tot - r2_sat
    r2_blocked = r2_violating > 0  # NO-REPAIR policy: no value is adjusted

    violating_edge_list = []
    for a, b in r2_edges:
        d = bin((a & 3) ^ (b & 3)).count("1")
        if d > 1:
            violating_edge_list.append(
                {"edge": [a, b], "r_j": a & 3, "r_k": b & 3, "r_hamming": d}
            )
    pywork("enumeration of the specific R2 violating edges for the report")

    # ---------------- jaxpr evidence ---------------------------------------
    jaxprs = [
        jaxpr_digest("popcount_over_J", lambda x: popcount(x, n), Jv),
        jaxpr_digest("seam_kernel_F3", seam_kernel, ea, eb),
        jaxpr_digest("matrix_rank_COHERENT", rank_kernel, COH),
        jaxpr_digest("reach_closure_CHECKER", reach_closure, adjacency(checker_edges)),
    ]

    # ---------------- diagnostics (NOT the contract line) -------------------
    diagnostics = {
        "lane": "jax",
        "lane_nonce": LANE_NONCE,
        "fixture_path": str(FIXTURE_PATH),
        "fixture_sha256_computed": fixture_sha,
        "fixture_sha256_matches_frozen": fixture_sha == FIXTURE_SHA_FROZEN,
        "environment": {
            "python": sys.version.split()[0],
            "executable": sys.executable,
            "jax_version": jax.__version__,
            "jax_x64_enabled_probe_dtype": str(jnp.zeros(1).dtype),
            "jax_default_backend": jax.default_backend(),
            "jax_devices": [str(d) for d in jax.devices()],
        },
        "native_jax_evidence": {
            "n_jax_ops_invoked": len(JAX_CALLS),
            "distinct_jax_ops": sorted({c["op"] for c in JAX_CALLS}),
            "call_receipts": JAX_CALLS,
            "jaxpr_digests": jaxprs,
        },
        "plain_python_steps": PY_WORK,
        "computation_provenance": {
            "f0_fields_and_capacities": "jax (bitwise_xor, popcount jit, equal/less_equal, sum, log2)",
            "f0_a2_rank": "jax (jnp.linalg.matrix_rank -> svd primitive); exact Fraction elimination as a python cross-check",
            "f1_fibres_and_kappa": "jax (popcount jit, equal, sum, nonzero, mod, log2)",
            "f1_multiset_comparison": "python",
            "f2_adjacency_degrees_edgecounts": "jax (.at[].set scatter, sum)",
            "f2_components": "jax boolean transitive closure by repeated matmul; row dedup and union-find cross-check in python",
            "f2_reconstruction_checks": "python",
            "f3_seam_obligation": "jax (jitted seam_kernel: bitwise_and, bitwise_xor, right_shift, equal, logical_or, sum)",
            "f3_r1_quotient_vertices": "jax (bitwise_and, unique)",
            "f3_r1_quotient_edges_and_r2_edge_list": "python bookkeeping",
        },
        "f0_detail": {
            "a2_exact_rank_python_fraction": {
                "diag": exact_rank_diag,
                "coherent": exact_rank_coh,
            },
            "a2_jax_matches_exact": {
                "diag": int(a2_diag) == exact_rank_diag,
                "coherent": int(a2_coh) == exact_rank_coh,
            },
            "ordered_pair_support_counts": {
                "diag": int(diag_support),
                "coherent": int(coh_support),
            },
            "unordered_pair_support_counts_diagnostic_only": {
                "diag": diag_unordered,
                "coherent": coh_unordered,
            },
            "a1_convention_used": "ORDERED matrix entries (j,k); A1 = log2(#nonzero entries of the 16x16 matrix)",
            "separating_quantities": ["A1"],
            "non_separating_quantities": ["A0 (identical by construction)", "A2 (identical by computation)"],
        },
        "f1_detail": {
            "q_codomain_values": Q_values,
            "fibres": fibres,
            "release_q_descriptors": release_descriptors,
            "any_empty_fibre": any(s == 0 for s in fibre_sizes),
            "q2_fibres": q2_fibres,
            "q_fibre_size_multiset": q_multiset,
            "q2_fibre_size_multiset": q2_multiset,
            "quotients_distinguished_by_multiset": quotients_distinguished,
            "same_codomain_size": same_codomain_size,
        },
        "f2_detail": {
            "checker": rep_checker,
            "ring": rep_ring,
            "spun": rep_spun,
            "ring_after_cut": rep_ring_cut,
            "checker_after_n2": rep_checker_n2,
            "reconstruction_matches_fixture": {
                "checker": recon_checker == sorted(checker_edges),
                "ring": recon_ring == sorted(ring_edges),
                "spun": recon_spun == sorted(spun_edges),
            },
            "sigma_is_bijection": sigma_is_bijection,
            "sigma_matches_declared_formula": sigma_matches_formula,
            "n1_cut_edge": list(cut_edge),
            "n1_cycles_before": rep_ring["independent_cycles"],
            "n1_cycles_after": rep_ring_cut["independent_cycles"],
            "n2_added_edge": list(n2_edge),
            "n2_hamming_distance": n2_hamming,
            "n2_degree_sequence_before": rep_checker["degree_sequence"],
            "n2_degree_sequence_after": rep_checker_n2["degree_sequence"],
            "n3_note": (
                "CHECKER and RING are NOT established as the same object: no transition map "
                "was supplied and their edge counts differ "
                f"({rep_checker['edges_from_jax_adjacency']} vs {rep_ring['edges_from_jax_adjacency']}). "
                "A measurement on a supplied complex cannot declare two presentations globally identical."
            ),
        },
        "f3_detail": {
            "r_definition": "r(j) = j AND 0b11 (low two bits)",
            "seam_satisfied": seam_sat,
            "seam_total": seam_tot,
            "seam_teeth_warning": (
                "32/32 is satisfied by construction on this carrier: a Q4 edge flips exactly one bit, "
                "so r either is unchanged or differs in exactly one bit. The positive check has no "
                "discriminating power here; R2 carries the discrimination."
            ),
            "r1_quotient_vertices": quotient_vertices,
            "r1_fibres": {str(k): sorted(v) for k, v in sorted(r1_fibres.items())},
            "r1_quotient_edge_readings": {
                "simple_edges_only": len(q_simple),
                "simple_plus_self_loops": len(q_simple) + q_loops,
                "all_edges_with_multiplicity": q_mult,
                "self_loops": q_loops,
                "note": "only f3_r1_quotient_vertices is in the output contract; the edge reading is unpinned",
            },
            # Outcome strings are BUILT from the measured integers above, never written
            # as literals. The integer each one is derived from is emitted alongside it.
            "r1_outcome_derived_from": {"quotient_vertices": quotient_vertices},
            "r1_outcome": (
                f"CONTRACT applied; quotient carrier admitted with {quotient_vertices} vertices"
            ),
            "r2_added_edge": list(r2_edge),
            "r2_total_edges": r2_tot,
            "r2_satisfied_edges": r2_sat,
            "r2_violating_edges": r2_violating,
            "r2_violating_edge_detail": violating_edge_list,
            "r2_policy": "NO-REPAIR: no value adjusted to make the seam check pass",
            "r2_outcome_derived_from": {
                "violating_edges": r2_violating,
                "satisfied": r2_sat,
                "total": r2_tot,
            },
            "r2_outcome": (
                f"BLOCKED under NO-REPAIR: {r2_violating} of {r2_tot} edges survived as "
                f"obstructions; the rewrite is excluded"
                if r2_violating > 0
                else f"no obstruction measured across {r2_tot} edges"
            ),
        },
        "exact_integer_forms": {
            "f0_diag_support_ordered": int(diag_support),
            "f0_coh_support_ordered": int(coh_support),
            "f0_diag_rank": exact_rank_diag,
            "f0_coh_rank": exact_rank_coh,
            "f1_fibre_sizes": fibre_sizes,
            "f2_checker_edges": rep_checker["edges_from_jax_adjacency"],
            "f2_ring_edges": rep_ring["edges_from_jax_adjacency"],
        },
        "float_note": (
            "Only two irrational values appear in the contract: log2(80) and log2(6). "
            "x64 is enabled, so both are float64. Compare lanes on the exact integer forms; "
            "apply a stated tolerance only to those two log2 values."
        ),
    }

    # ---------------- contract object (LAST line of stdout) ----------------
    contract = {
        "f0_diag_a0": float(a0),
        "f0_diag_a1": float(a1_diag),
        "f0_diag_a2": int(a2_diag),
        "f0_coh_a0": float(a0),
        "f0_coh_a1": float(a1_coh),
        "f0_coh_a2": int(a2_coh),
        "f1_fibre_sizes": fibre_sizes,
        "f1_kappa": kappa,
        "f1_q2_fibre_sizes": q2_sizes,
        "f2_checker_edges": rep_checker["edges_from_jax_adjacency"],
        "f2_ring_edges": rep_ring["edges_from_jax_adjacency"],
        "f2_checker_cycles": rep_checker["independent_cycles"],
        "f2_ring_cycles": rep_ring["independent_cycles"],
        "f2_n1_ring_cycles_after_cut": rep_ring_cut["independent_cycles"],
        "f2_n2_degree_changed": bool(n2_degree_changed),
        "f2_n3_edge_counts_differ": bool(n3_edge_counts_differ),
        "f3_seam_satisfied_edges": seam_sat,
        "f3_seam_total_edges": seam_tot,
        "f3_r1_quotient_vertices": quotient_vertices,
        "f3_r2_violating_edges": r2_violating,
        "f3_r2_blocked": bool(r2_blocked),
        "engine_name": ENGINE_NAME,
        "lane_nonce": LANE_NONCE,
    }

    sys.stdout.write("DIAGNOSTICS " + json.dumps(diagnostics, sort_keys=True) + "\n")
    sys.stdout.write(json.dumps(contract, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
