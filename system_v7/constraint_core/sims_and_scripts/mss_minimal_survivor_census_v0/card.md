# MSS minimal-survivor census v0

## Claim

Exhaustively classify the `3^9 = 19,683` binary-operation tables on the
labelled carrier `{0,1,2}` under this deliberately narrow first-pass MSS
floor:

1. **N01:** some ordered pair has `x*y != y*x`.
2. **Probe distinguishability:** some distinct carrier pair has unequal left
   translations or unequal right translations.  For `a != b`, the probes are
   `L_a(x)=a*x` and `R_a(x)=x*a`; the pair is distinguishable when
   `L_a != L_b` or `R_a != R_b` as functions on the carrier.
3. **Minimality:** a survivor is quotient-minimal when no witnessed
   surjective homomorphism onto a 2-element or 1-element magma has a target
   that also satisfies N01 and probe distinguishability.  This is
   **QUOTIENT-ONLY**; subquotient minimality is explicitly open.

Tables are iso-deduplicated using all six permutations of `{0,1,2}`.

## Association boundary (binding correction)

The floor is **association-unspecified**: associativity is not assumed, and
nonassociativity is not asserted merely by placing a table at this floor.
After minima are found, this census measures the split between:

- associative minima; and
- minima with an explicit nonzero associator witness
  `(a*b)*c != a*(b*c)`.

This follows
`system_v7/constraint_core/corrections/OWNER_NONASSOCIATIVITY_FLOOR_CORRECTION_20260711.md`.

## Bounded execution and evidence

- `census.py` is standard-library Python for the enumeration and quotient
  witness search; it prints progress every 2,000 source tables.
- `results_v1.json` records all counts, isomorphism summaries, kill
  attribution, and one witnessed surjective homomorphism for each
  quotient-killed survivor.
- `z3_load_bearing_check.py` separately binds measured census counts in Z3.
  Its real direct claim must be SAT; its erased-control claim, which erases
  the measured quotient-kill contribution, must be UNSAT.  Its verdict gates
  the check artifact's `all_pass` field.
- A second run is compared byte-for-byte with `results_v1.json` before this
  v0 surface is frozen.

## Claim ceiling

This is a finite, classical exhaustive diagnostic of the stated quotient-only
floor.  It does not establish subquotient minimality, a general MSS theorem,
or an association/nonassociativity claim beyond the enumerated 3-carrier
tables.

## Claim-to-evidence table

| Claim | Source | Result | Required gate | Allowed status |
|---|---|---|---|---|
| 3-carrier quotient-only census | `census.py` | `results_v1.json` | exhaustive count, witnesses, deterministic rerun | passes local rerun |
| Count-consistency proof check | `z3_load_bearing_check.py` | `z3_load_bearing_check_v1.json` | real SAT / erased UNSAT | passes local rerun |

Blocked consumers: subquotient claims, unbounded-carrier claims, and any
theory or ratchet-promotion claim.
