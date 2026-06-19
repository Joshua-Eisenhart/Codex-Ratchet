# Owner doctrine — the entropy-type / operator co-ratchet (pre-registered 2026-06-11)

Owner (verbatim intent): "as the layers ratchet the types of entropy/information and operators
will also ratchet i think."

## The thesis (registered before any build)

Entropy types are layer-indexed readouts of constraint structure, never primitive (the standing
static rule, a54224476). The DYNAMIC form now registered: **as the constraint layers ratchet, the
set of ADMISSIBLE entropy/information types ratchets with them, and the admissible operator
families co-ratchet.** Each ratchet step does not just shrink/quotient the state — it changes
WHICH functionals are well-defined on the survivor:

| enabling layer (committed object) | types that become admissible |
|---|---|
| finite support (F01) | counting entropy |
| chart/measure layer | differential (chart-uniform) entropy |
| density quotient S/~_M | von Neumann entropy |
| bipartition/subsystem split | conditional vN S(A|B), mutual information |
| channel/update semigroup R_C | coherent information I_c, capacities |
| record/syndrome object | state-plus-record conservation accounts |

and dually for operators: which probe/update families are admissible co-varies with the layer
(e.g. CPTP maps need the density quotient; record-conditioned operations need the syndrome).

## Already on disk (the thesis's existing support, typed correctly)
- conditional vN: S(A|B) 0 -> -0.36 -> -0.68 across ratchet steps (the nested Hopf+Weyl signed-cut
  ratchet) — negativity = the quantum signature, appearing ONLY after the bipartition layer.
- coherent information: I_c rows in the dual-stack probe (0.41650) + certified I_c bounds in
  manifold_information_throughput_v0 (Ni rows) — appearing ONLY after the channel layer.
- counting/typed deltas: the basin/fusion campaign; the deep chain's per-step -ln4/-ln2/-ln2.
- the conservation account: stateable only after z4_syndrome_record_v0 constructed the record.
What does NOT yet exist: the co-ratchet AS ITS OWN OBJECT — no packet computes the
type-admissibility table per ratchet step with witnesses.

## Pre-registered predictions (falsifiable)
1. At each committed ratchet step, the admissible-type set changes at NAMED steps only, and a
   type evaluated BEFORE its enabling layer fails with the named missing structure (not a number).
2. The availability ORDER is itself order-sensitive (N01 on the type ladder): permuting the
   constraint order changes the step at which types become admissible.
3. The admissible operator family co-varies with the same steps (witnessed, not asserted).
Falsifier: a type computable with full meaning before its enabling layer exists, or a shuffled
layer order leaving the availability sequence unchanged — either kills the co-ratchet reading.

Ceiling: doctrine registration; the packet (entropy_type_ratchet_v0) must earn every row.

---

## Adjudication entry — v0 (2026-06-11, audit BY_CONSTRUCTION)

`entropy_type_ratchet_v0` did NOT test this doctrine: its availability table was computed from a
hand-written step plan with declared enables (the schedule confirming itself). Earned: the in-
packet N01 ladder mechanics only (real order-sensitive availability sequences under genuine step
permutation). The doctrine remains OPEN pending v1's DISCOVERY DESIGN: each enabling object
(density quotient, bipartition, channel, record) must be CONSTRUCTED-or-fail against the actual
consumed parent state objects, with availability = the computed construction outcome and the
failure reason = the named missing structure. No declared enables lists anywhere on the claim path.

---

## Adjudication entry — v1 (2026-06-11, audit EARNED at scratch strength)

`entropy_type_ratchet_v1` (the discovery design) EARNS the doctrine at scratch strength: all three
pre-registered predictions adjudicated EARNED by the fresh cross-backend audit — availability
discovered by attempted construction (no declared enables; the v0 trap verified absent),
N01-on-the-type-ladder real (operation functions permuted, availability indices move), operator
co-ratchet via the same constructors (tool-depth caveat carried). Citable as: scratch evidence
that the type-availability table and operator co-ratchet are DISCOVERED by construction attempts
over one evolving state lineage. Ceiling: scratch_diagnostic, promotion_allowed=false — the
doctrine is earned as a computed object, not formal/canonical.

---

## Correction entry — the Sonnet cross-model lens on v1 (2026-06-12)

The v1 EARNED verdict is narrowed: the v0 TEXTUAL declared-enables schedule is absent, but the
operation-sequence ORDER itself embeds an implicit structural ordering that places each enabling
object at the doctrine-named step — a SOFTER form of the trap, not its full elimination. The
corrected citation: the availability table is REPRODUCED by attempted constructors against a
state lineage whose enabling objects were placed at the doctrine-named positions (not "discovered"
free of placement choices). What fully survives: the construction-attempt mechanics (real
MissingStructure from real paths), the N01 shuffle result, the spoofed-enable gate. The v2 gate
(if pursued): derive the operation sequence itself from a consumed parent (the unified-run
ratchet order as-committed) rather than composing it in-packet, and test a legitimate alternative
sequence for off-doctrine availability steps. Ceiling unchanged: scratch, the doctrine earned at
this narrower scope.

---

## Adjudication entry — v2 + THE REGRESS RESOLUTION (2026-06-12)

v2's gate did not close (the translation-table level of the same trap). THE DETERMINABLE
RESOLUTION (recorded per the no-fake-decisions rule): the regress BOTTOMS OUT — the consumed
parent artifacts do not contain executable operation semantics, so "full sequence-origin
discovery" is not achievable from this parent BY ITS NATURE; any realization requires some
in-packet semantics. The doctrine's PERMANENT EARNED SCOPE on this parent is therefore the v1
form, now precisely stated: **the type-availability table is REPRODUCED by genuine construction
attempts (real MissingStructure failures, real N01 order-sensitivity, anti-spoof gates) against a
parent-mapped lineage** — earned at scratch strength, with "discovered free of any in-packet
semantics" retired as ill-posed rather than open. A future parent that pins executable operation
semantics (e.g. a committed operation registry) would reopen the stronger form; until then, no
v3 is warranted (chasing the regress further would be theater).
