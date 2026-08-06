#!/usr/bin/env python3
"""D3 QUOTIENT ORDER discriminator, n = 4.

Rival A (the diagram's own order): CONSTRAIN then QUOTIENT.
    E_C = {e in E : C(e)} ;  q_Pi : E_C ->> Q_Pi ;  Fib(u) = q^-1(u) inter E_C
Rival B: QUOTIENT then push the constraint down to classes.
    q_Pi : E ->> Q_Pi ; a class survives iff ALL of its members satisfy C (B_all)
                        or iff SOME member satisfies C (B_some)

Both orders are applied to the SAME finite fixture, twice: once with a
Pi-MEASURABLE constraint and once with a constraint that is not a function of
the probe responses. The second leg is the one that can separate them.

Then the same fork is run on the restriction diagram C_AB / global sections
Gamma / obstruction Z(b), including a Z(b) = 0 case.
"""
import json
import os
import sys
from itertools import product

N = 4
J = list(range(2 ** N))
E = [(j, k) for j in J for k in J]


def popcount(x):
    return bin(x).count("1")


def q_pi(e):
    """Probe family Pi = { popcount of the first index, popcount of the second }."""
    j, k = e
    return (popcount(j), popcount(k))


C_MEASURABLE = lambda e: popcount(e[0]) + popcount(e[1]) <= 4
C_NOT_MEASURABLE = lambda e: popcount(e[0] ^ e[1]) <= 1


def classes(elements):
    out = {}
    for e in elements:
        out.setdefault(q_pi(e), []).append(e)
    return out


def order_A(C):
    E_C = [e for e in E if C(e)]
    cl = classes(E_C)
    return {
        "constrained_support_cardinality": len(E_C),
        "surviving_class_count": len(cl),
        "fibre_cardinality_by_class": {str(u): len(v) for u, v in sorted(cl.items())},
    }


def order_B(C, quantifier):
    cl = classes(E)
    keep = {}
    for u, members in cl.items():
        flags = [C(e) for e in members]
        if (all(flags) if quantifier == "all" else any(flags)):
            keep[u] = members  # the fibre is the FULL class: the constraint acted on classes
    return {
        "constrained_support_cardinality": sum(len(v) for v in keep.values()),
        "surviving_class_count": len(keep),
        "fibre_cardinality_by_class": {str(u): len(v) for u, v in sorted(keep.items())},
    }


def compare(a, b):
    keys = sorted(set(a) | set(b))
    fa, fb = a["fibre_cardinality_by_class"], b["fibre_cardinality_by_class"]
    return {
        "scalar_fields_that_differ": [k for k in keys
                                      if k != "fibre_cardinality_by_class" and a[k] != b[k]],
        "classes_only_in_first": sorted(set(fa) - set(fb)),
        "classes_only_in_second": sorted(set(fb) - set(fa)),
        "shared_classes_with_different_fibre_cardinality":
            sorted(k for k in set(fa) & set(fb) if fa[k] != fb[k]),
        "fibre_maps_identical": fa == fb,
    }


# ---- restriction diagram / global sections -------------------------------------
SITES_A = (0, 1, 2)
SITES_B = (1, 2, 3)
OVERLAP = (1, 2)


def local_states(sites, local_ok):
    return [dict(zip(sites, bits)) for bits in product((0, 1), repeat=len(sites))
            if local_ok(dict(zip(sites, bits)))]


def restrict(x):
    return tuple(x[s] for s in OVERLAP)


def sections(XA, XB):
    return [(a, b) for a in XA for b in XB if restrict(a) == restrict(b)]


def overlap_probe(pair):
    """A COARSER probe on the seam: parity of the overlap bits only."""
    return sum(restrict(pair[0])) % 2


def sections_leg(name, ok_a, ok_b):
    XA, XB = local_states(SITES_A, ok_a), local_states(SITES_B, ok_b)
    G = sections(XA, XB)
    # order 1: take sections on the fine diagram, THEN quotient them by the seam probe
    fine_then_quotient = sorted({overlap_probe(p) for p in G})
    # order 2: quotient each local space by the seam probe FIRST. After the
    # quotient the fine overlap value is GONE, so gluing can only compare classes.
    coarse = lambda X: {sum(restrict(x)) % 2 for x in X}
    cA, cB = coarse(XA), coarse(XB)
    quotient_then_sections = sorted(cA & cB)
    return {
        "leg": name,
        "X_A_cardinality": len(XA),
        "X_B_cardinality": len(XB),
        "Z_b_global_section_count": len(G),
        "seam_classes_from_sections_then_quotient": fine_then_quotient,
        "seam_classes_from_quotient_then_sections": quotient_then_sections,
        "seam_class_sets_agree": fine_then_quotient == quotient_then_sections,
    }


def main():
    legs = {}
    for cname, C in (("C_pi_measurable_weight_sum_le_4", C_MEASURABLE),
                     ("C_not_pi_measurable_xor_weight_le_1", C_NOT_MEASURABLE)):
        A = order_A(C)
        Ball = order_B(C, "all")
        Bsome = order_B(C, "some")
        legs[cname] = {
            "order_A_constrain_then_quotient": A,
            "order_B_quotient_then_constrain_ALL": Ball,
            "order_B_quotient_then_constrain_SOME": Bsome,
            "A_vs_B_all": compare(A, Ball),
            "A_vs_B_some": compare(A, Bsome),
            "B_all_vs_B_some": compare(Ball, Bsome),
        }

    section_legs = [
        sections_leg("both_local_spaces_unconstrained",
                     lambda x: True, lambda x: True),
        sections_leg("A_constrained_by_a_seam_measurable_rule",
                     lambda x: (x[1] + x[2]) % 2 == 0, lambda x: True),
        sections_leg("A_constrained_by_a_NON_seam_measurable_rule",
                     lambda x: x[0] == 1, lambda x: True),
        sections_leg("incompatible_pair_forcing_Z_b_zero",
                     lambda x: x[1] == 0 and x[2] == 0,
                     lambda x: x[1] == 1 and x[2] == 1),
        # DECISIVE leg: the two local spaces keep DIFFERENT overlap values that the
        # seam probe cannot tell apart (both have parity 1). Fine sections are empty;
        # quotienting the seam FIRST glues them anyway.
        sections_leg("distinct_overlap_values_sharing_one_seam_class",
                     lambda x: (x[1], x[2]) == (0, 1),
                     lambda x: (x[1], x[2]) == (1, 0)),
    ]
    result = {
        "discriminator": "D3_quotient_order",
        "n": N,
        "total_support_cardinality": len(E),
        "probe_family": "Pi = { popcount(j), popcount(k) }",
        "class_count_before_any_constraint": len(classes(E)),
        "constraint_legs": legs,
        "restriction_diagram_legs": section_legs,
    }
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "results", "d3_quotient_order.json")
    with open(path, "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
    print(json.dumps(result, indent=1, sort_keys=True))
    print(f"WROTE {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
