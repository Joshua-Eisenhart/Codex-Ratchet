#!/usr/bin/env python3
"""Deep standalone geometry lego: the finite distinguishability quotient Q = S/~.

KNOWN GEOMETRY (real, computed in torch -- no labels, no random claim-substrate):
    Finite state set S = {0,...,|S|-1} and a finite probe set P = {p_0,...,p_{|P|-1}}.
    Each probe is a map p_j : S -> C realized as a complex128 column of the probe-value
    tensor V where V[i, j] = p_j(s_i). Define probe-relative indistinguishability

        s ~ t   iff   p_j(s) = p_j(t)  for every probe p_j in P.

    Q = S / ~ is the survivor-state quotient: the first manifold object. As the probe
    family P grows, the induced partition refines monotonically (the refinement lattice).

This is the nominalist-harness primitive made concrete: identity is probe-relative
(a = a iff a ~ b under the active probe family). It is a real, textbook finite object
(a set partition induced by a family of functions / the kernel of the joint map
S -> C^{|P|}), and every named invariant is cross-checked against its KNOWN value.

TOOLS (all load-bearing in the execution path):
    torch   -- probe-value tensors V in complex128; the ~ relation is a torch all-equal
               reduction over probe columns; ablating torch (scalar-collapse probes)
               kills the carrier resolution and forces |Q| = 1.
    rustworkx -- the quotient/refinement graph: states are nodes, ~-edges are added,
               connected components ARE the equivalence classes. |Q| is read off the
               graph component count, independently of the torch partition.
    z3      -- certifies ~ is a genuine equivalence relation: the NEGATION of each of
               reflexivity / symmetry / transitivity over the computed relation table is
               UNSAT. Removing z3 removes the structural certificate.
    cvc5    -- second independent SMT engine; same equivalence-relation certificate
               (reflexive/symmetric/transitive negation UNSAT) on the same table.
    sympy   -- exact class counts: separating-probe partition count = |S| (Stirling
               S(n,n)=1 single-partition shape), constant-probe count = 1, and Bell(n)
               sanity for the number of admissible partitions of a small carrier.

KNOWN-VALUE CROSS-CHECKS (this is how depth is proven for known math):
    1. separating probe set       => |Q| == |S|            (identity probe family)
    2. single constant probe      => |Q| == 1              (no probe resolves anything)
    3. ~ is an equivalence relation => z3 AND cvc5 negation of refl/sym/trans = UNSAT
    4. rustworkx component count   == torch partition class count   (cross-engine agree)
    5. random probe family |Q|     == kernel of joint map (exact recompute) and
                                      1 <= |Q| <= |S|, monotone non-decreasing under
                                      probe-family growth (refinement lattice)
    6. exact partition combinatorics: Bell(n) total partitions, Stirling(n,n)=1,
       Stirling(n,1)=1 anchor the two extreme quotients.

classification = "diagnostic_only": hypothetical, unadmitted lego phase. No distinctness
gate, no manifold-membership forcing, no cross-layer rules. Pure known-math depth.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import cvc5
import rustworkx as rx
import sympy as sp
import torch
import z3
from cvc5 import Kind

CDTYPE = torch.complex128
RTYPE = torch.float64
ATOL = 1.0e-9
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_distinguishability_quotient_deep_probe"

# Wide variation grid: state-set sizes, probe-set sizes, seeds.
STATE_SIZES = [6, 8, 12, 16, 24, 32]
PROBE_SIZES = [1, 2, 3, 5, 8]
SEEDS = [0, 1, 2, 3, 4, 5, 6, 7]


# ---------------------------------------------------------------------------
# torch substrate: probe-value tensors V[i, j] = p_j(s_i) over C
# ---------------------------------------------------------------------------
def random_probe_values(n_states: int, n_probes: int, seed: int,
                        *, n_levels: int = 3) -> torch.Tensor:
    """Real probe-value tensor in complex128. Each probe p_j maps every state s_i to one
    of n_levels distinct complex levels; equal levels => probe cannot distinguish those
    states. This is a genuine finite family of functions S -> C, not a random claim
    matrix: the *only* thing that matters is the equality pattern of the columns."""
    g = torch.Generator().manual_seed(seed)
    # n_levels distinct complex "readings" on the unit circle (well separated)
    k = torch.arange(n_levels, dtype=RTYPE)
    levels = torch.exp(2j * torch.pi * k.to(CDTYPE) / float(n_levels))
    idx = torch.randint(0, n_levels, (n_states, n_probes), generator=g)
    return levels[idx].to(CDTYPE)


def separating_probe_values(n_states: int) -> torch.Tensor:
    """A probe family that fully separates S: probe j reads bit j of the state index.
    With ceil(log2 n) probes every state has a unique reading => Q = S exactly."""
    n_probes = max(1, (n_states - 1).bit_length())
    rows = []
    for i in range(n_states):
        rows.append([float((i >> j) & 1) for j in range(n_probes)])
    return torch.tensor(rows, dtype=CDTYPE)


def constant_probe_values(n_states: int) -> torch.Tensor:
    """A single constant probe: every state reads the same value => Q collapses to 1."""
    return torch.ones((n_states, 1), dtype=CDTYPE)


def scalar_label_collapse_values(n_states: int, n_probes: int) -> torch.Tensor:
    """Torch ablation: collapse every probe column to one scalar label (carrier payload
    erased). Distinguishability vanishes => |Q| = 1 regardless of n_probes."""
    return torch.zeros((n_states, n_probes), dtype=CDTYPE)


# ---------------------------------------------------------------------------
# the ~ relation and the quotient (torch reduction)
# ---------------------------------------------------------------------------
def indistinguishability_table(V: torch.Tensor) -> torch.Tensor:
    """Boolean (n_states x n_states) table: rel[i, t] iff p_j(s_i) == p_j(s_t) for all j.
    Computed as a torch all-close reduction over the probe axis."""
    diff = V.unsqueeze(1) - V.unsqueeze(0)        # (n, n, n_probes)
    same_col = diff.abs() <= ATOL                  # (n, n, n_probes)
    return same_col.all(dim=2)                      # (n, n)


def partition_from_table_torch(rel: torch.Tensor) -> list[list[int]]:
    """Equivalence classes purely from the torch relation table (no graph engine).
    Independent of the rustworkx path so the two can be cross-checked."""
    n = rel.shape[0]
    seen = [False] * n
    classes: list[list[int]] = []
    for i in range(n):
        if seen[i]:
            continue
        members = [t for t in range(n) if bool(rel[i, t])]
        for t in members:
            seen[t] = True
        classes.append(sorted(members))
    return sorted(classes)


def kernel_partition_exact(V: torch.Tensor) -> int:
    """Exact |Q| via the kernel of the joint map S -> C^{|P|}: count distinct reading
    tuples. This is the textbook definition of the quotient, recomputed independently
    of both torch-table and graph paths."""
    readings = set()
    for i in range(V.shape[0]):
        readings.add(tuple((round(float(c.real), 9), round(float(c.imag), 9))
                           for c in V[i]))
    return len(readings)


# ---------------------------------------------------------------------------
# rustworkx: quotient/refinement graph -> connected components = classes
# ---------------------------------------------------------------------------
def quotient_component_count_rustworkx(rel: torch.Tensor) -> tuple[int, list[list[int]]]:
    """Build the ~-graph in rustworkx and read |Q| off the connected components.
    States are nodes; an edge (i, t) is added iff s_i ~ s_t. Because ~ is a genuine
    equivalence relation, connected components ARE the classes exactly."""
    n = rel.shape[0]
    g = rx.PyGraph()
    idx = [g.add_node(i) for i in range(n)]
    for i in range(n):
        for t in range(i + 1, n):
            if bool(rel[i, t]):
                g.add_edge(idx[i], idx[t], None)
    comps = rx.connected_components(g)
    classes = sorted(sorted(g[node] for node in comp) for comp in comps)
    return len(comps), classes


# ---------------------------------------------------------------------------
# z3: certify ~ is an equivalence relation (negation of each axiom UNSAT)
# ---------------------------------------------------------------------------
def z3_equivalence_certificate(rel: torch.Tensor) -> dict[str, Any]:
    """Encode the computed relation table as z3 boolean atoms R(i,t) pinned to the
    observed truth values, then check that the NEGATION of reflexivity, symmetry, and
    transitivity is UNSAT (i.e. the table genuinely satisfies all three)."""
    n = rel.shape[0]
    R = [[z3.Bool(f"R_{i}_{t}") for t in range(n)] for i in range(n)]
    base = z3.And([R[i][t] if bool(rel[i, t]) else z3.Not(R[i][t])
                  for i in range(n) for t in range(n)])

    def neg_unsat(neg_axiom: z3.BoolRef) -> str:
        s = z3.Solver()
        s.add(base)
        s.add(neg_axiom)
        return str(s.check())

    refl_neg = z3.Or([z3.Not(R[i][i]) for i in range(n)])
    sym_neg = z3.Or([z3.And(R[i][t], z3.Not(R[t][i]))
                     for i in range(n) for t in range(n)])
    trans_neg = z3.Or([z3.And(R[i][t], R[t][u], z3.Not(R[i][u]))
                       for i in range(n) for t in range(n) for u in range(n)])
    refl = neg_unsat(refl_neg)
    sym = neg_unsat(sym_neg)
    trans = neg_unsat(trans_neg)
    return {
        "reflexive_negation_status": refl,
        "symmetric_negation_status": sym,
        "transitive_negation_status": trans,
        "pass": refl == "unsat" and sym == "unsat" and trans == "unsat",
    }


# ---------------------------------------------------------------------------
# cvc5: independent SMT certificate of the same three axioms
# ---------------------------------------------------------------------------
def cvc5_equivalence_certificate(rel: torch.Tensor) -> dict[str, Any]:
    n = rel.shape[0]

    def check(neg_kind: str) -> str:
        tm = cvc5.TermManager()
        s = cvc5.Solver(tm)
        s.setLogic("QF_UF")
        B = tm.getBooleanSort()
        R = [[tm.mkConst(B, f"R_{i}_{t}") for t in range(n)] for i in range(n)]
        TRUE = tm.mkTrue()
        FALSE = tm.mkFalse()
        # pin the table
        for i in range(n):
            for t in range(n):
                want = TRUE if bool(rel[i, t]) else FALSE
                s.assertFormula(tm.mkTerm(Kind.EQUAL, R[i][t], want))
        # assert the negation of the chosen axiom
        if neg_kind == "refl":
            terms = [tm.mkTerm(Kind.NOT, R[i][i]) for i in range(n)]
        elif neg_kind == "sym":
            terms = [tm.mkTerm(Kind.AND, R[i][t], tm.mkTerm(Kind.NOT, R[t][i]))
                     for i in range(n) for t in range(n)]
        else:  # trans
            terms = [tm.mkTerm(Kind.AND, R[i][t],
                              tm.mkTerm(Kind.AND, R[t][u], tm.mkTerm(Kind.NOT, R[i][u])))
                     for i in range(n) for t in range(n) for u in range(n)]
        if len(terms) == 1:
            s.assertFormula(terms[0])
        else:
            s.assertFormula(tm.mkTerm(Kind.OR, *terms))
        return str(s.checkSat())

    refl = check("refl")
    sym = check("sym")
    trans = check("trans")
    return {
        "reflexive_negation_status": refl,
        "symmetric_negation_status": sym,
        "transitive_negation_status": trans,
        "pass": refl == "unsat" and sym == "unsat" and trans == "unsat",
    }


# ---------------------------------------------------------------------------
# sympy: exact combinatorial cross-checks
# ---------------------------------------------------------------------------
def sympy_partition_facts(n: int) -> dict[str, Any]:
    """Exact textbook facts about partitions of an n-element set used as anchors:
    Stirling(n, n) = 1 (only the discrete partition gives |Q| = n),
    Stirling(n, 1) = 1 (only the trivial partition gives |Q| = 1),
    Bell(n)        = total number of admissible partitions of S."""
    stirling = sp.functions.combinatorial.numbers.stirling
    return {
        "n": n,
        "stirling_n_n": int(stirling(n, n)),
        "stirling_n_1": int(stirling(n, 1)),
        "bell_n": int(sp.bell(n)),
    }


def brute_force_partition_count(n: int) -> int:
    """Count set partitions of {0..n-1} by brute force (small n) to confirm Bell(n)."""
    def partitions(collection):
        if len(collection) == 1:
            yield [collection]
            return
        first, rest = collection[0], collection[1:]
        for smaller in partitions(rest):
            for k in range(len(smaller)):
                yield smaller[:k] + [[first] + smaller[k]] + smaller[k + 1:]
            yield [[first]] + smaller
    return sum(1 for _ in partitions(list(range(n))))


# ---------------------------------------------------------------------------
# witness rows: full wide-variation sweep
# ---------------------------------------------------------------------------
def sweep_rows() -> list[dict[str, Any]]:
    rows = []
    for n_states in STATE_SIZES:
        for n_probes in PROBE_SIZES:
            for seed in SEEDS:
                V = random_probe_values(n_states, n_probes, seed)
                rel = indistinguishability_table(V)
                torch_classes = partition_from_table_torch(rel)
                torch_q = len(torch_classes)
                rx_q, rx_classes = quotient_component_count_rustworkx(rel)
                kernel_q = kernel_partition_exact(V)
                rows.append({
                    "n_states": n_states,
                    "n_probes": n_probes,
                    "seed": seed,
                    "torch_class_count": torch_q,
                    "rustworkx_component_count": rx_q,
                    "kernel_exact_count": kernel_q,
                    "all_three_agree": torch_q == rx_q == kernel_q,
                    "bounds_ok": 1 <= torch_q <= n_states,
                })
    return rows


def refinement_lattice_rows() -> list[dict[str, Any]]:
    """Refinement lattice: grow the probe family one probe at a time and confirm |Q|
    is monotone NON-DECREASING (adding distinguishing power never coarsens the quotient)."""
    rows = []
    for n_states in [8, 12, 16, 24]:
        for seed in SEEDS:
            V_full = random_probe_values(n_states, 8, seed)
            qs = []
            for k in range(1, V_full.shape[1] + 1):
                rel = indistinguishability_table(V_full[:, :k])
                qs.append(len(partition_from_table_torch(rel)))
            monotone = all(qs[i] <= qs[i + 1] for i in range(len(qs) - 1))
            rows.append({
                "n_states": n_states,
                "seed": seed,
                "q_by_probe_count": qs,
                "monotone_nondecreasing": monotone,
            })
    return rows


# ---------------------------------------------------------------------------
# known-value cross-checks
# ---------------------------------------------------------------------------
def build_known_value_checks() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    detail: dict[str, Any] = {}

    # CHECK 1: separating probe family => |Q| == |S|
    sep_results = []
    for n in STATE_SIZES:
        V = separating_probe_values(n)
        rel = indistinguishability_table(V)
        q_torch = len(partition_from_table_torch(rel))
        q_rx, _ = quotient_component_count_rustworkx(rel)
        q_kernel = kernel_partition_exact(V)
        sep_results.append({"n_states": n, "q_torch": q_torch, "q_rx": q_rx,
                            "q_kernel": q_kernel})
    sep_match = all(r["q_torch"] == r["q_rx"] == r["q_kernel"] == r["n_states"]
                    for r in sep_results)
    detail["separating"] = sep_results
    checks.append({
        "invariant": "separating_probe_family__|Q|==|S|",
        "computed": str([r["q_torch"] for r in sep_results]),
        "known": str(STATE_SIZES),
        "match": bool(sep_match),
    })

    # CHECK 2: single constant probe => |Q| == 1
    const_results = []
    for n in STATE_SIZES:
        V = constant_probe_values(n)
        rel = indistinguishability_table(V)
        q_torch = len(partition_from_table_torch(rel))
        q_rx, _ = quotient_component_count_rustworkx(rel)
        q_kernel = kernel_partition_exact(V)
        const_results.append({"n_states": n, "q_torch": q_torch, "q_rx": q_rx,
                              "q_kernel": q_kernel})
    const_match = all(r["q_torch"] == r["q_rx"] == r["q_kernel"] == 1
                      for r in const_results)
    detail["constant"] = const_results
    checks.append({
        "invariant": "single_constant_probe__|Q|==1",
        "computed": str([r["q_torch"] for r in const_results]),
        "known": str([1] * len(STATE_SIZES)),
        "match": bool(const_match),
    })

    # CHECK 3: ~ is a genuine equivalence relation (z3 negation UNSAT) on a random table
    Vz = random_probe_values(10, 3, seed=7)
    relz = indistinguishability_table(Vz)
    z3_cert = z3_equivalence_certificate(relz)
    detail["z3_certificate"] = z3_cert
    checks.append({
        "invariant": "z3__refl/sym/trans_negation_UNSAT",
        "computed": f"refl={z3_cert['reflexive_negation_status']},"
                    f"sym={z3_cert['symmetric_negation_status']},"
                    f"trans={z3_cert['transitive_negation_status']}",
        "known": "refl=unsat,sym=unsat,trans=unsat",
        "match": bool(z3_cert["pass"]),
    })

    # CHECK 4: cvc5 independent equivalence-relation certificate (same table)
    cvc5_cert = cvc5_equivalence_certificate(relz)
    detail["cvc5_certificate"] = cvc5_cert
    checks.append({
        "invariant": "cvc5__refl/sym/trans_negation_UNSAT",
        "computed": f"refl={cvc5_cert['reflexive_negation_status']},"
                    f"sym={cvc5_cert['symmetric_negation_status']},"
                    f"trans={cvc5_cert['transitive_negation_status']}",
        "known": "refl=unsat,sym=unsat,trans=unsat",
        "match": bool(cvc5_cert["pass"]),
    })

    # CHECK 5: rustworkx component count == torch partition count across the full sweep
    sweep = sweep_rows()
    sweep_agree = all(r["all_three_agree"] and r["bounds_ok"] for r in sweep)
    detail["sweep_row_count"] = len(sweep)
    detail["sweep_disagreements"] = [r for r in sweep if not r["all_three_agree"]]
    checks.append({
        "invariant": "torch==rustworkx==kernel_exact__across_full_sweep",
        "computed": f"{sum(1 for r in sweep if r['all_three_agree'])}/{len(sweep)}_agree",
        "known": f"{len(sweep)}/{len(sweep)}_agree",
        "match": bool(sweep_agree),
    })

    # CHECK 6: refinement lattice monotone non-decreasing
    refine = refinement_lattice_rows()
    refine_ok = all(r["monotone_nondecreasing"] for r in refine)
    detail["refinement_rows"] = refine
    checks.append({
        "invariant": "refinement_lattice__|Q|_monotone_nondecreasing",
        "computed": f"{sum(1 for r in refine if r['monotone_nondecreasing'])}/{len(refine)}_monotone",
        "known": f"{len(refine)}/{len(refine)}_monotone",
        "match": bool(refine_ok),
    })

    # CHECK 7: exact partition combinatorics (sympy + brute force agree on Bell(n))
    comb_results = []
    for n in [2, 3, 4, 5, 6]:
        facts = sympy_partition_facts(n)
        bf = brute_force_partition_count(n)
        comb_results.append({**facts, "brute_force_bell": bf,
                            "ok": facts["bell_n"] == bf
                            and facts["stirling_n_n"] == 1
                            and facts["stirling_n_1"] == 1})
    comb_ok = all(r["ok"] for r in comb_results)
    detail["combinatorics"] = comb_results
    checks.append({
        "invariant": "sympy_Bell(n)==brute_force__and__Stirling(n,n)=Stirling(n,1)=1",
        "computed": str([(r["n"], r["bell_n"], r["brute_force_bell"]) for r in comb_results]),
        "known": str([(r["n"], int(sp.bell(r["n"])), int(sp.bell(r["n"]))) for r in comb_results]),
        "match": bool(comb_ok),
    })

    return checks, detail


# ---------------------------------------------------------------------------
# negatives (collapse / flatten controls)
# ---------------------------------------------------------------------------
def build_negatives() -> dict[str, Any]:
    neg: dict[str, Any] = {}

    # NEG 1: constant probe collapses Q to a single class (already a known-value check;
    # recorded here as an explicit negative artifact too).
    Vc = constant_probe_values(16)
    relc = indistinguishability_table(Vc)
    qc = len(partition_from_table_torch(relc))
    neg["constant_probe_collapses_to_one_class"] = {
        "n_states": 16, "computed_|Q|": qc, "expected_|Q|": 1, "pass": qc == 1,
    }

    # NEG 2: fully-separating probes => Q = S (no collapse).
    Vs = separating_probe_values(16)
    rels = indistinguishability_table(Vs)
    qs = len(partition_from_table_torch(rels))
    neg["separating_probe_recovers_full_Q==S"] = {
        "n_states": 16, "computed_|Q|": qs, "expected_|Q|": 16, "pass": qs == 16,
    }

    # NEG 3: torch scalar-label ablation (erase carrier payload) => |Q| = 1 even with
    # many probes; confirms torch carrier is load-bearing for the quotient.
    Vl = scalar_label_collapse_values(16, 5)
    rell = indistinguishability_table(Vl)
    ql = len(partition_from_table_torch(rell))
    neg["scalar_label_collapse_kills_resolution"] = {
        "n_states": 16, "n_probes": 5, "computed_|Q|": ql, "expected_|Q|": 1,
        "pass": ql == 1,
    }

    # NEG 4: duplicating an existing probe must NOT refine the quotient (adding redundant
    # distinguishing power changes nothing -- the refinement lattice is idempotent on
    # the relation it already induces).
    V = random_probe_values(16, 3, seed=2)
    q_before = len(partition_from_table_torch(indistinguishability_table(V)))
    V_dup = torch.cat([V, V[:, :1]], dim=1)  # duplicate first probe
    q_after = len(partition_from_table_torch(indistinguishability_table(V_dup)))
    neg["duplicate_probe_does_not_refine"] = {
        "q_before": q_before, "q_after": q_after, "expected_equal": True,
        "pass": q_before == q_after,
    }

    # NEG 5: BROKEN relation (deliberately non-transitive) must FAIL the SMT certificate.
    # Build a relation that is reflexive+symmetric but breaks transitivity, and confirm
    # z3's transitivity-negation is SAT (not UNSAT) -- i.e. the certificate has teeth.
    n = 3
    bad = torch.eye(n, dtype=torch.bool)
    bad[0, 1] = bad[1, 0] = True
    bad[1, 2] = bad[2, 1] = True   # 0~1, 1~2, but NOT 0~2 -> non-transitive
    bad_cert = z3_equivalence_certificate(bad)
    neg["nontransitive_relation_fails_certificate"] = {
        "transitive_negation_status": bad_cert["transitive_negation_status"],
        "expected": "sat", "pass": bad_cert["transitive_negation_status"] == "sat",
    }

    return neg


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    checks, detail = build_known_value_checks()
    negatives = build_negatives()

    known_value_checks = checks
    all_known_match = all(c["match"] for c in checks)
    all_negatives_pass = all(v["pass"] for v in negatives.values())
    all_pass = all_known_match and all_negatives_pass

    witness_trace = {
        "witness_trace_id": f"{SIM_ID}_witness",
        "transforms_applied": [
            "build complex128 probe-value tensor V[i,j]=p_j(s_i)",
            "compute ~ table via torch all-equal reduction over probe columns",
            "extract partition via torch reduction AND rustworkx connected components",
            "recompute |Q| via exact kernel-of-joint-map (distinct reading tuples)",
            "certify refl/sym/trans via z3 negation-UNSAT",
            "certify refl/sym/trans via cvc5 negation-UNSAT (independent engine)",
            "cross-check exact partition combinatorics via sympy Bell/Stirling + brute force",
        ],
        "negatives_run": list(negatives.keys()),
        "sweep_grid": {"state_sizes": STATE_SIZES, "probe_sizes": PROBE_SIZES, "seeds": SEEDS},
        "final_classification": "diagnostic_only",
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "tier": "geometry_lego_pre_sim",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": ("Deep standalone known-math lego: the finite distinguishability "
                    "quotient Q = S/~ (the survivor-state quotient, first manifold object), "
                    "computed in torch with rustworkx/z3/cvc5/sympy all load-bearing and "
                    "every named invariant cross-checked against its known value."),
        "scientific_question": ("For a finite state set S and finite probe family P with "
                                "s~t iff p(s)=p(t) for all p in P, does the computed quotient "
                                "Q=S/~ match the known textbook invariants (|Q|=|S| under "
                                "separating probes, |Q|=1 under a constant probe, ~ a genuine "
                                "equivalence relation, refinement-lattice monotone) across wide "
                                "variation, and do the collapse controls kill the signature?"),
        "claim_ceiling": ("bounded diagnostic_only geometry lego of KNOWN finite "
                          "distinguishability geometry; NOT manifold-admitted, NOT gated on "
                          "distinctness/forcing, does not support any axis/bridge/coupling claim"),
        "finite_map": ("(finite state set S = {0..|S|-1}, finite probe family P, probe-value "
                       "tensor V[i,j]=p_j(s_i) over C) -> equivalence relation s~t iff all "
                       "probe columns agree -> quotient Q = S/~ and its class count |Q|"),
        "domain": ("finite state set S (|S| in {6,8,12,16,24,32}) and finite probe family P "
                   "(|P| in {1,2,3,5,8}) realized as complex128 probe-value columns"),
        "codomain_or_output": ("the set partition Q = S/~ (equivalence classes), the class "
                               "count |Q|, the refinement lattice |Q| vs growing |P|, and the "
                               "equivalence-relation certificates"),
        "root_constraints_in_force": {
            "F01": "finite state set, finite probe family, finite probe-value tensor",
            "probe_relative_identity": "a~b iff every active probe gives equal readings; identity is the quotient class",
        },
        "carrier_layer": "finite distinguishability carrier (state set under probe family)",
        "geometry_layer": "finite quotient geometry S/~ (the survivor-state quotient)",
        "carrier_realization": ("torch.complex128 probe-value tensor V; ~ relation as torch "
                                "all-equal reduction; quotient via rustworkx connected components "
                                "and exact kernel recompute; no numpy claim substrate, no random "
                                "claim matrices, no labels"),
        "peps3d_embedding": "not_applicable_at_lego_phase",
        "spinor_state": "not_applicable (distinguishability quotient is a set partition, not a spinor object)",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_admission", "coupling", "axis0", "flux", "bridge", "physics"],
        "blocked_consumers": ["manifold_admission", "coupling", "axis0", "flux", "bridge", "physics"],
        "law_or_candidate_tested": ("finite distinguishability quotient Q = S/~ matches the "
                                    "known invariants of a set partition induced by a family of "
                                    "functions (kernel of the joint map S -> C^{|P|})"),
        "branch_status_before_run": "hypothetical_unadmitted_lego",
        "allowed_claims": ["known finite distinguishability quotient computed and cross-checked against textbook invariants"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase, not gated for admission)"],
        "required_tools": ["torch", "rustworkx", "z3", "cvc5", "sympy"],
        "actual_tools_used": ["torch", "rustworkx", "z3", "cvc5", "sympy"],
        "proof_surfaces_used": ["z3", "cvc5"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": [],
        "required_negatives": [
            "constant_probe_collapses_to_one_class",
            "separating_probe_recovers_full_Q==S",
            "scalar_label_collapse_kills_resolution",
            "duplicate_probe_does_not_refine",
            "nontransitive_relation_fails_certificate",
        ],
        "negatives_run": list(negatives.keys()),
        "kill_conditions": [
            "separating-probe |Q| != |S|",
            "constant-probe |Q| != 1",
            "torch/rustworkx/kernel class counts disagree",
            "z3 or cvc5 equivalence-axiom negation not UNSAT",
            "refinement lattice not monotone non-decreasing",
            "sympy Bell(n) != brute-force partition count",
        ],
        "known_value_checks": known_value_checks,
        "known_value_detail": detail,
        "negatives": negatives,
        "controls": {"negative": negatives},
        "result_summary": {
            "all_pass": all_pass,
            "all_known_value_checks_match": all_known_match,
            "all_negatives_pass": all_negatives_pass,
            "known_value_check_count": len(known_value_checks),
            "negative_count": len(negatives),
            "sweep_rows": detail["sweep_row_count"],
            "classification": "diagnostic_only",
            "promotion_allowed": False,
        },
        "witness_trace": witness_trace,
        "witness_trace_id": witness_trace["witness_trace_id"],
        "required_artifacts": ["json_result_packet", "witness_trace"],
        "artifacts_emitted": ["json_result_packet", "witness_trace"],
        "pass_rule": "all known_value_checks match AND all negatives pass",
        "fail_rule": "any known_value_check mismatch OR any negative not collapsing/recovering as expected",
        "promotion_status": "diagnostic_only",
        "eligible_consumers": ["other_lego_phase_diagnostics"],
        "TOOL_MANIFEST": {
            "torch": {"used": True, "role": "load_bearing",
                      "reason": "complex128 probe-value tensors V and the ~ relation as an "
                                "all-equal reduction over probe columns; scalar-label ablation "
                                "collapses |Q| to 1"},
            "rustworkx": {"used": True, "role": "load_bearing",
                          "reason": "the quotient/refinement graph: connected components ARE the "
                                    "equivalence classes; |Q| read off the component count and "
                                    "cross-checked against the torch/kernel counts"},
            "z3": {"used": True, "role": "load_bearing",
                   "reason": "certifies ~ is an equivalence relation: negation of refl/sym/trans "
                             "is UNSAT; a deliberately non-transitive relation makes it SAT"},
            "cvc5": {"used": True, "role": "load_bearing",
                     "reason": "independent SMT engine certifying the same three axioms "
                               "(refl/sym/trans negation UNSAT)"},
            "sympy": {"used": True, "role": "load_bearing",
                      "reason": "exact partition combinatorics: Bell(n) (matched to brute force) "
                                "and Stirling(n,n)=Stirling(n,1)=1 anchoring the two extreme quotients"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "torch": "load_bearing", "rustworkx": "load_bearing", "z3": "load_bearing",
            "cvc5": "load_bearing", "sympy": "load_bearing",
        },
        "all_pass": all_pass,
        "blockers": [] if all_pass else [
            c["invariant"] for c in known_value_checks if not c["match"]
        ] + [k for k, v in negatives.items() if not v["pass"]],
    }

    out = RESULT_DIR / f"{SIM_ID}_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "wrote": str(out),
        "all_pass": all_pass,
        "all_known_value_checks_match": all_known_match,
        "all_negatives_pass": all_negatives_pass,
        "known_value_checks": [{"invariant": c["invariant"], "match": c["match"]} for c in known_value_checks],
        "negatives": {k: v["pass"] for k, v in negatives.items()},
        "blockers": result["blockers"],
    }, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
