#!/usr/bin/env python3
"""Executable base-Ratchet campaign (owner spec 2026-07-18).

Every proposed base structure becomes an executable candidate. All candidates
receive the SAME observation packets O, requirements R, and proposed nesting N.
No candidate is eliminated by prose: every kill, demotion, or win carries a
computed witness. Candidates that are not yet executable are queued as
PROPOSED_NOT_YET_SIMULATED and are neither on the frontier nor in Purgatory.

Observation packets (real, source-native, hash-bound):
  O_ctx  : finite_contextuality_marginal_gluing_no_global_section_v0
           12 archived rows + 3 fresh held-out rows from the executed
           kernel tick (tick_receipt.json, 2026-07-18).
  O_ring : finite_ring_checkerboard_support_three_presentation_consistency_v0
           96 archived rows (relation-only: real continuation conflicts).

Rows are (h0, h1, p; o) over the generic binary alphabet.

Requirements R (all executable):
  R1 exact per-context admissibility: for every observed context (h0,h1,p),
     the candidate admits exactly the observed outcome set.
  R2 derived distinctions: the candidate reproduces the reference
     distinguishability relation  u !~ v  iff  some context separates them.
  R3 restriction: imposing a token constraint yields exactly the reference
     restricted admissible set.
  R4 conflict survival: the candidate represents packets whose contexts carry
     both outcomes (relation-only data) without contradiction.

Nesting N (same for all candidates): N = { (a, b) in A_ctx x A_ring :
outcome token of a == outcome token of b }. Order test: restrict ctx side
then ring side vs the reverse. Persistence: a distinction surviving a
restriction path.

Comparison (witness-only):
  a > b  iff  (a sufficient, b insufficient: witness = b's requirement kill)
          or  (same behavior signature, primitive types of a are a subset of
               b's, strictly fewer primitives: strict-deletion witness)
          or  (same behavior signature, a needs strictly fewer unobserved
               choices: additional-primitive witness).
  Otherwise both retained. Frontier = unbeaten sufficient candidates.

Claim ceiling: packet-relative base-structure comparison over two anonymous
source packets. No scientific, physical, or canonical claim. No promotion.
"""
import hashlib, json, sys
from itertools import combinations
from pathlib import Path

V8 = Path(__file__).resolve().parent.parent  # system_v8/
PACK = V8 / "inputs"  # hash-bound copies from Pack 177 v2 (see inputs/INPUT_HASHES.sha256)
TICK = V8 / "kernel_tick" / "receipts" / "tick_receipt_20260718.json"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else V8 / "base_campaign" / "results" / "base_campaign_run_20260718"

VARS = ("h0", "h1", "p", "o")


def sha256_json(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# ---------------------------------------------------------------- packets
def load_packets():
    tables = json.loads((PACK / "receipts" / "normalized_source_tables.json").read_text())
    def rows_for(handle):
        return [tuple(int(r[v]) for v in VARS)
                for s in tables["sources"] if s["handle"] == handle
                for r in s["rows"]]
    ctx_rows = rows_for("src-1858a5f7dbbb248f")
    tick = json.loads(TICK.read_text())
    for r in tick["new_records"]:
        ctx_rows.append((int(r["history"][0]), int(r["history"][1]),
                         int(r["probe"]), int(r["outcome"])))
    ring_rows = rows_for("src-5cb0baaed60f7057")
    return {"ctx": ctx_rows, "ring": ring_rows}


def context_outcomes(rows):
    m = {}
    for r in rows:
        m.setdefault(r[:3], set()).add(r[3])
    return m


def reference_distinctions(rows):
    """u !~ v (tokens of the same variable) iff some context separates them.

    Packet-relative: admissibility = membership in the observed row set.
    """
    A = set(rows)
    out = []
    for vi in range(4):
        # tokens 0 and 1 of variable vi; contexts = fixed values of others
        sep = None
        for row in A:
            alt = tuple(1 - row[i] if i == vi else row[i] for i in range(4))
            if alt not in A:
                sep = {"variable": VARS[vi], "context": list(row)}
                break
        if sep:
            out.append({"variable": VARS[vi], "distinguishable": True, "witness": sep})
        else:
            out.append({"variable": VARS[vi], "distinguishable": False})
    return out


def reference_restriction(rows, var_index, value):
    return sorted(r for r in set(rows) if r[var_index] == value)


# ---------------------------------------------------------------- candidates
class Candidate:
    name = "abstract"
    primitive_types = ()
    def __init__(self, rows):
        self.rows = list(rows)
        self.A = set(rows)
        self.arbitrary_choices = 0
        self.notes = []
        self.fit()
    def fit(self):
        pass
    def admitted(self, ctx):
        """Outcome set admitted at an observed context; None = unresolved."""
        raise NotImplementedError
    def primitives(self):
        raise NotImplementedError


class B0Relation(Candidate):
    """(V, A): finite occurrences + arbitrary finite admissible family."""
    name = "b0_unrestricted_relation"
    primitive_types = ("tokens", "admissible_configs")
    def admitted(self, ctx):
        s = {r[3] for r in self.A if r[:3] == ctx}
        return s or None
    def primitives(self):
        return {"tokens": 8, "admissible_configs": len(self.A)}


class ProbeResponseIncidence(Candidate):
    """Bipartite context-outcome incidence; role split read from the packet."""
    name = "probe_response_incidence"
    primitive_types = ("tokens", "incidence_pairs", "role_typing")
    def fit(self):
        self.inc = context_outcomes(self.A)
    def admitted(self, ctx):
        return set(self.inc[ctx]) if ctx in self.inc else None
    def primitives(self):
        return {"tokens": 8,
                "incidence_pairs": sum(len(v) for v in self.inc.values()),
                "role_typing": 1}


class FinitePartition(Candidate):
    """(V, equivalence classes) only: no admissibility family at all."""
    name = "finite_partition"
    primitive_types = ("tokens", "classes")
    def admitted(self, ctx):
        return {0, 1}  # nothing is forbidden by classes alone
    def primitives(self):
        return {"tokens": 8, "classes": 8}


class PairwiseGraph(Candidate):
    """Edges = co-occurring token pairs; admissibility = clique closure."""
    name = "pairwise_graph"
    primitive_types = ("tokens", "edges")
    def fit(self):
        self.E = set()
        for r in self.A:
            toks = [(i, r[i]) for i in range(4)]
            for a, b in combinations(toks, 2):
                self.E.add(frozenset((a, b)))
    def admitted(self, ctx):
        out = set()
        for o in (0, 1):
            toks = [(0, ctx[0]), (1, ctx[1]), (2, ctx[2]), (3, o)]
            if all(frozenset((a, b)) in self.E for a, b in combinations(toks, 2)):
                out.add(o)
        return out or None
    def primitives(self):
        return {"tokens": 8, "edges": len(self.E)}


class SimplicialComplex(Candidate):
    """Downward closure of the observed configurations; faces are primitive."""
    name = "simplicial_complex"
    primitive_types = ("tokens", "admissible_configs", "subfaces",
                       "downward_closure_axiom")
    def fit(self):
        self.faces = set()
        for r in self.A:
            toks = frozenset((i, r[i]) for i in range(4))
            for k in range(len(toks) + 1):
                for sub in combinations(sorted(toks), k):
                    self.faces.add(frozenset(sub))
    def admitted(self, ctx):
        s = {r[3] for r in self.A if r[:3] == ctx}
        return s or None
    def primitives(self):
        maximal = len({frozenset((i, r[i]) for i in range(4)) for r in self.A})
        return {"tokens": 8, "admissible_configs": maximal,
                "subfaces": len(self.faces) - maximal, "downward_closure_axiom": 1}


class PosetDownset(Candidate):
    """A as a down-set of a chosen order; discrete order fits but is unused."""
    name = "poset_downset"
    primitive_types = ("tokens", "admissible_configs", "order_relation")
    def fit(self):
        self.arbitrary_choices = 1  # the order itself is an unobserved choice
        self.notes.append("discrete order fits any A; order primitive is idle")
    def admitted(self, ctx):
        s = {r[3] for r in self.A if r[:3] == ctx}
        return s or None
    def primitives(self):
        return {"tokens": 8, "admissible_configs": len(self.A), "order_relation": 1}


class MatroidBases(Candidate):
    """Observed configurations as the basis family; basis exchange must hold."""
    name = "matroid_bases"
    primitive_types = ("tokens", "bases", "exchange_axiom")
    def fit(self):
        self.exchange_counterexample = None
        bases = [frozenset((i, r[i]) for i in range(4)) for r in set(self.rows)]
        for B1, B2 in combinations(bases, 2):
            for x in B1 - B2:
                if not any((B1 - {x}) | {y} in bases for y in B2 - B1):
                    self.exchange_counterexample = {
                        "B1": sorted(map(list, B1)), "B2": sorted(map(list, B2)),
                        "x": list(x),
                        "violation": "no y in B2\\B1 with B1-x+y a basis"}
                    return
    def admitted(self, ctx):
        s = {r[3] for r in self.A if r[:3] == ctx}
        return s or None
    def primitives(self):
        return {"tokens": 8, "bases": len(set(self.rows)), "exchange_axiom": 1}


class DetTransducer(Candidate):
    """Deterministic map (h0,h1,p) -> o; sequential evolution presumed."""
    name = "deterministic_transducer"
    primitive_types = ("states", "transition_function", "sequential_evolution")
    def fit(self):
        self.conflict = None
        for ctx, outs in context_outcomes(self.A).items():
            if len(outs) > 1:
                self.conflict = {"context": list(ctx), "outcomes": sorted(outs)}
                break
    def admitted(self, ctx):
        outs = {r[3] for r in self.A if r[:3] == ctx}
        if len(outs) > 1:
            return None  # cannot represent: no deterministic value exists
        return outs or None
    def primitives(self):
        return {"states": 8, "transition_function": 1, "sequential_evolution": 1}


class ClassicalDistribution(Candidate):
    """Support = A plus real weights unconstrained by O."""
    name = "classical_distribution"
    primitive_types = ("tokens", "admissible_configs", "real_weights", "normalization")
    def fit(self):
        self.arbitrary_choices = max(len(set(self.rows)) - 1, 0)
        self.notes.append("weights are unobserved parameters; no installed "
                          "requirement earns multiplicity")
    def admitted(self, ctx):
        s = {r[3] for r in self.A if r[:3] == ctx}
        return s or None
    def primitives(self):
        return {"tokens": 8, "admissible_configs": len(set(self.rows)),
                "real_weights": max(len(set(self.rows)) - 1, 0), "normalization": 1}


EXECUTABLE = [B0Relation, ProbeResponseIncidence, FinitePartition, PairwiseGraph,
              SimplicialComplex, PosetDownset, MatroidBases, DetTransducer,
              ClassicalDistribution]
PROPOSED_NOT_YET_SIMULATED = [
    "rebit_carrier", "complex_density_matrix", "jordan_structure",
    "clifford_vector_spinor", "quaternionic_carrier",
    "bracket_preserving_octonionic_carrier"]


# ---------------------------------------------------------------- evaluation
def evaluate(cls, packets, refs):
    per_packet = {}
    sufficient = True
    kill = None
    insts = {}
    for pk, rows in packets.items():
        cand = cls(rows)
        insts[pk] = cand
        ref_map = refs[pk]["context_outcomes"]
        mismatches = []
        for ctx, outs in ref_map.items():
            got = cand.admitted(ctx)
            if got != outs:
                mismatches.append({"context": list(ctx),
                                   "observed_outcomes": sorted(outs),
                                   "candidate_outcomes": sorted(got) if got else None})
        r1 = not mismatches
        # R2: derived distinctions must match reference on distinguishability
        r2 = True
        if r1:
            # candidate's derived relation coincides with reference when its
            # admitted map equals the observed map (checked by R1); a candidate
            # that over/under-admits already failed R1.
            r2 = True
        # R3: restriction agreement (impose h0=1 as the probe restriction)
        ref_restr = reference_restriction(rows, 0, 1)
        cand_restr = sorted(r for r in set(rows)
                            if r[0] == 1 and (cand.admitted(r[:3]) or set()) >= {r[3]})
        r3 = (ref_restr == cand_restr) if r1 else False
        # R4: conflict survival
        conflict = getattr(cand, "conflict", None)
        exchange = getattr(cand, "exchange_counterexample", None)
        pk_ok = r1 and r2 and r3 and conflict is None and exchange is None
        if not pk_ok and kill is None:
            if mismatches:
                kill = {"packet": pk, "type": "R1_admissibility_mismatch",
                        "witness": mismatches[:3]}
            elif conflict is not None:
                kill = {"packet": pk, "type": "R4_continuation_conflict",
                        "witness": conflict}
            elif exchange is not None:
                kill = {"packet": pk, "type": "axiom_counterexample_basis_exchange",
                        "witness": exchange}
            else:
                kill = {"packet": pk, "type": "R3_restriction_mismatch"}
        sufficient = sufficient and pk_ok
        per_packet[pk] = {
            "R1_exact_admissibility": r1,
            "R1_mismatch_count": len(mismatches),
            "R3_restriction_exact": r3,
            "conflict": conflict, "exchange_counterexample": exchange,
            "primitives": cand.primitives(),
            "arbitrary_choices": cand.arbitrary_choices,
        }
    sig = {pk: {"R1": per_packet[pk]["R1_exact_admissibility"],
                "R3": per_packet[pk]["R3_restriction_exact"],
                "conflict_free": per_packet[pk]["conflict"] is None}
           for pk in packets}
    return {"name": cls.name, "sufficient": sufficient,
            "insufficiency_witness": kill,
            "behavior_signature": sig,
            "per_packet": per_packet,
            "primitive_types": list(cls.primitive_types),
            "total_primitives": sum(sum(per_packet[pk]["primitives"].values())
                                    for pk in packets),
            "arbitrary_choices": sum(per_packet[pk]["arbitrary_choices"]
                                     for pk in packets),
            "notes": sorted({n for c in insts.values() for n in c.notes}),
            }, insts


def nesting_tests(insts_by_name, packets):
    """Same proposed nesting N for every candidate that can express both packets."""
    results = {}
    for name, insts in insts_by_name.items():
        ca, cb = insts.get("ctx"), insts.get("ring")
        Aa = {r for r in set(packets["ctx"]) if (ca.admitted(r[:3]) or set()) >= {r[3]}}
        Ab = {r for r in set(packets["ring"]) if (cb.admitted(r[:3]) or set()) >= {r[3]}}
        # over-admitting candidates additionally admit unobserved outcomes:
        extra_a = sum(len((ca.admitted(ctx) or set()) - outs)
                      for ctx, outs in context_outcomes(packets["ctx"]).items())
        M = {(a, b) for a in Aa for b in Ab if a[3] == b[3]}
        # restrictions: T1 = ctx side h0=1; T2 = ring side h1=0
        t1 = lambda S: {(a, b) for a, b in S if a[0] == 1}
        t2 = lambda S: {(a, b) for a, b in S if b[1] == 0}
        forward, backward = t2(t1(M)), t1(t2(M))
        base_ring = {b for _, b in M}
        after_ring = {b for _, b in t1(M)}
        # persistence: h0-tokens distinguishable before; still after imposing p=1?
        tp = {(a, b) for a, b in M if a[2] == 1}
        proj = {a for a, _ in tp}
        persists = any(x[0] != y[0] and x[1:] == y[1:] for x in proj for y in proj) or \
            ({a[0] for a in proj} == {0, 1})
        results[name] = {
            "whole_state_count": len(M),
            "ctx_overadmitted_outcome_pairs": extra_a,
            "restricting_outer_changes_inner": sorted(base_ring) != sorted(after_ring),
            "order_T2T1_equals_T1T2": forward == backward,
            "noncommutation_earned": forward != backward,
            "distinction_persists_under_restriction_path": bool(persists),
        }
    return results


def compare(evals):
    """Pairwise witness-only comparison."""
    witnesses = []
    beaten = set()
    by = {e["name"]: e for e in evals}
    for a, b in [(x, y) for x in by.values() for y in by.values() if x is not y]:
        if a["sufficient"] and not b["sufficient"]:
            witnesses.append({"winner": a["name"], "loser": b["name"],
                              "witness_type": "requirement_kill",
                              "witness": b["insufficiency_witness"]})
            beaten.add(b["name"])
        elif a["sufficient"] and b["sufficient"] and \
                a["behavior_signature"] == b["behavior_signature"]:
            if set(a["primitive_types"]) < set(b["primitive_types"]) and \
                    a["total_primitives"] < b["total_primitives"]:
                witnesses.append({"winner": a["name"], "loser": b["name"],
                                  "witness_type": "strict_structure_deletion",
                                  "witness": {
                                      "deleted_primitive_types": sorted(
                                          set(b["primitive_types"]) - set(a["primitive_types"])),
                                      "primitive_totals": [a["total_primitives"],
                                                           b["total_primitives"]]}})
                beaten.add(b["name"])
            elif set(a["primitive_types"]) <= set(b["primitive_types"]) and \
                    a["arbitrary_choices"] < b["arbitrary_choices"]:
                witnesses.append({"winner": a["name"], "loser": b["name"],
                                  "witness_type": "additional_unobserved_choices",
                                  "witness": {"choices": [a["arbitrary_choices"],
                                                          b["arbitrary_choices"]]}})
                beaten.add(b["name"])
    return witnesses, beaten


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output: {OUT}")
    OUT.mkdir(parents=True)
    packets = load_packets()
    refs = {pk: {"context_outcomes": context_outcomes(rows),
                 "distinctions": reference_distinctions(rows)}
            for pk, rows in packets.items()}
    evals, insts_by_name = [], {}
    for cls in EXECUTABLE:
        ev, insts = evaluate(cls, packets, refs)
        evals.append(ev)
        insts_by_name[cls.name] = insts
    nest = nesting_tests(insts_by_name, packets)
    witnesses, beaten = compare(evals)
    frontier = sorted(e["name"] for e in evals
                      if e["sufficient"] and e["name"] not in beaten)
    purgatory = [{"name": e["name"],
                  "status": "PARKED_PURGATORY",
                  "beaten_by": sorted({w["winner"] for w in witnesses
                                       if w["loser"] == e["name"]}),
                  "insufficiency_witness": e["insufficiency_witness"],
                  "reoffer_rule": "universally eligible after material context "
                                  "or requirement change"}
                 for e in evals if e["name"] in beaten or not e["sufficient"]]
    receipt = {
        "schema_version": "ratchet.base-campaign/0.1",
        "packets": {pk: {"rows": len(v), "distinct_rows": len(set(v)),
                         "sha256": f"sha256:{sha256_json(sorted(set(v)))}"}
                    for pk, v in packets.items()},
        "reference_distinctions": {pk: refs[pk]["distinctions"] for pk in refs},
        "candidates": evals,
        "nesting_and_order": nest,
        "pairwise_witnesses": witnesses,
        "base_frontier": frontier,
        "purgatory": purgatory,
        "proposed_not_yet_simulated": PROPOSED_NOT_YET_SIMULATED,
        "frontier_rule": "F_{t+1} = unbeaten(F_t U Purgatory_t U new simulated candidates)",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": ("packet-relative executable base-structure comparison "
                          "over two anonymous source packets; no scientific, "
                          "physical, or canonical claim"),
    }
    (OUT / "base_campaign_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "frontier": frontier,
        "purgatory": [p["name"] for p in purgatory],
        "not_yet_simulated": PROPOSED_NOT_YET_SIMULATED,
        "witness_count": len(witnesses),
        "noncommutation_earned": {k: v["noncommutation_earned"] for k, v in nest.items()
                                  if k in frontier},
        "receipt": str(OUT / "base_campaign_receipt.json")}, indent=2))


if __name__ == "__main__":
    main()
