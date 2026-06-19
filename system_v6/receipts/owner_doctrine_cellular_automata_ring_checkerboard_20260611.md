# Owner doctrine — the cellular-automata reading + the ring checkerboard (pre-registered 2026-06-11)

Owner (verbatim intent): "is cellular automata relevant? it seems my system could end like a
cellular automata manifold. or that is one way to process and visualize it. that is discrete
finite maps. the ring checkerboard model aligns with that."

## The thesis (registered before any build; standard terms lead, owner labels in parens)

1. **The system's analysis layer is already CA-grade:** finite state sets + discrete update maps
   + transition-graph/SCC/terminal-class machinery (the basin contract) is exactly how finite
   automata are analyzed. What a CA ADDS over a generic finite map is LOCALITY + HOMOGENEITY:
   one rule applied per cell over its neighborhood. The committed realizations (chart generators,
   the 1024-state joint automaton) are finite maps WITHOUT locality — the CA reading names the
   missing ingredient.
2. **The ring checkerboard (owner pre-AI provenance: the apple-notes Ring Checkerboard /
   engines-on-manifold chain) = the block-partitioned (Margolus) / brickwork normal form:** a
   finite periodic 1D lattice with two-phase updating (even cells then odd cells). The two-phase
   alternation aligns with the mined two-loop periodicity (deductive = ALTERNATING = the
   checkerboard phases; inductive = PAIRED = the blocks). The owner's model is the standard
   partitioned-automaton normal form, reached pre-AI.
3. **Quantum CA as the surface's local-update form (standard-math alignment, NOT owner-source):**
   a QCA = local unitary/CPTP rule on a finite lattice. 1D QCA carry the quantized GNVW INDEX =
   net left-vs-right information flow per step — a chirality invariant. Candidate alignment with
   the registered flux doctrine (O1: flux IN left / flux OUT right): the L/R engines as QCA with
   OPPOSITE indices, the index as the computable flux/chirality invariant. This composes with the
   spinor-network-surface doctrine: network + local rule = QCA; brickwork = the checkerboard;
   the QNN-as-channels reading and the QCA reading are the same object plus locality.

## Pre-registered expectations (falsifiable)
1. A ring-checkerboard finite automaton (classical first, then quantum) realizes the two-loop
   alternation as its two update phases, and the basin contract runs on it natively.
2. The QCA realization admits a computed index/information-flux invariant; the L/R engines
   realized with opposite signs; index 0 controls (non-chiral rules) must show NO L/R distinction
   (the flipping control).
3. If locality is the missing structure: a LOCAL realization of the engine dynamics should change
   the coupling-law behavior vs the global v2/v3 automata (the checkerboard alternation is itself
   a candidate coupling row for v4 — the brickwork coupling).
Falsifiers: a checkerboard realization that cannot express the two directed loop orders (B
constraints) is source-invalid; an index invariant that fails to distinguish the flux-signed
engines kills the alignment (3).

## Gate order (binding): MINE the ring-checkerboard provenance (apple-notes chain, wiki raw,
Rosetta-era artifacts) before any build — the owner's actual model defines the object, not the
standard form. Then ONE bounded packet: classical ring-checkerboard automaton + the basin
contract + the alternating/paired phase test. QCA/index rows only after the classical floor.

Ceiling: doctrine registration; packets must earn every row.

---

## Adjudication entry — v0 classical floor (2026-06-11/12, audit PASS at scratch)

`ring_checkerboard_automaton_v0` EARNS the classical floor: the owner-shaped support (ring steps,
parity coloring, one attached-ring nesting level) realized faithfully per the provenance quotes;
the phase test earned label-free — alternating(deductive)=period-2 vs paired(inductive)=period-4
terminal/orbit structure on the same support; nesting effect survives a size-matched control;
locality real. Scope caveat: single-active-token transition graph, not the full all-cells CA
configuration space (the v1 widening). THE QCA/INDEX GATE NOW OPENS per the registered order:
v1 may realize the quantum/local-channel form and compute the index/information-flux invariant
(the flux IN/OUT alignment candidate), plus optionally the full-configuration-space classical
widening. Expectation 1 earned; expectations 2-3 (QCA index, locality-changes-coupling) remain
open for v1+.

---

## Correction entry — the Sonnet cross-model lens on v0 (2026-06-12; the third shared-blind-spot catch)

The period-2 vs period-4 headline is DEFINITIONALLY FORCED, not discovered: the alternating rule
applies TWO phase updates per transition call, paired applies ONE — the period ratio is an
algebraic identity of the rule definitions (zero variance at all sizes; terminal_state_count =
class_count x period exactly). The phase-test "falsifier" was analytically unreachable. Also: the
two disciplines run on DISJOINT halves of the engine-loop state space (deductive-order vs
inductive-order tokens) — same ring geometry, different token populations; and the period claim is
a SINGLE-TOKEN readout-trajectory property, not full-CA field dynamics (2^(n(n+1)) configurations
untested). Both codex backends shared the blind spot; the builder and auditor treated an
implementation identity as an empirical finding.

**The genuinely earned structural content (survives the adversarial lens): the TRANSIENT SCC
TOPOLOGY difference** — alternating vs paired transient SCC counts 112/64, 352/128, 1216/256 at
n=4/8/16 (ratios 1.75, 2.75, 4.75 — growing, non-integer, NOT predicted by the period identity).
THE CORRECTED CITATION: cite the SCC/transient-topology difference as the v0 structural result;
cite period-2-vs-4 only as an implementation-correctness check; carry the disjoint-population and
single-token scope caveats. The classical floor remains earned at this corrected, narrower scope.

---

## Adjudication entry — QCA v1 (2026-06-12, audit REJECT for the index claim)

`ring_checkerboard_qca_v1` did NOT earn doctrine expectation 2: the index was a rule-table flow
parameter read back, not an invariant computed from the realized rule (the definitional lens from
the v0 correction, applied by the auditor, fired). The QCA/index gate stays OPEN. The v2 design
rule (binding): rules enter as local unitaries WITHOUT flow metadata; the index is extracted by
the genuine finite GNVW-class procedure over the realized operators' support algebras, with
calibrations (+1/-1/0) that could fail and a gauge-invariance check that could fail.

---

## v2 design-rule amendment — the finite-ring triviality (2026-06-12, the Sonnet research note's catch BEFORE the build)

Standard-math fact (the corpus note `~/wiki/codex-ratchet-research/standard-math/gnvw-index-1d-qca.md`,
recall-labeled): on a FINITE PERIODIC ring, the automorphism-class GNVW index is ALWAYS trivial
(Skolem–Noether: all unitary automorphisms of the full matrix algebra are inner) — the registered
v2 rule (index from support algebras on the committed ring) would return 1 for every rule, making
the calibrations unfailable in the wrong direction. THE AMENDED v2 RULE: either (a) realize the
rules on an OPEN CHAIN (where the quantization theorem holds and calibrations can genuinely fail),
with the ring as a separately-labeled closure row; or (b) compute the CIRCUIT-PRESENTATION index
on the ring and label every index row phase-convention-relative (a property of how the circuit is
written, not of the dynamics — the a=a iff a~b discipline applied to the index itself). Either
way: crossing ranks computed from realized operators (partial trace/Schmidt rank at the cut), the
gauge check = a REAL inserted onsite unitary w/ recomputed ranks, never metadata.

---

## Adjudication entry — QCA v2 (2026-06-12, audit: the fixture earned, the engine claim rejected)

v2 earns the open-chain crossing-rank EXTRACTION FIXTURE (the calibrations computed from realized
operators; the ring triviality honest) — the v1 metadata sin is gone. Expectation 2 stays OPEN:
the L/R engine rows were the calibration shifts relabeled (the FIFTH species: shift-calibration
relabeling), not distinct engine operators. The v3 rule (binding): the L/R engines enter as
DISTINCT local unitaries realizing committed engine dynamics — non-shift operators whose extracted
indices then test the flux alignment; an engine row numerically equal to a calibration row is
self-rejecting.

---

## Adjudication entry — QCA v3 (2026-06-12, audit: EXPECTATION 2 EARNED at fixture ceiling)

v3 cures both v2 defects (distinct engine unitaries + a real gauge perturbation). The L/R engine
disciplines carry opposite extracted open-chain indices (L=-1, R=+1; the paired form balanced at
0) — the flux IN-left/OUT-right alignment EARNED as a computed invariant at the open-chain
local-unitary fixture ceiling. Not finite-ring admission (the triviality stands), not coupling
evidence. The doctrine's expectations 1-2 now both earned; expectation 3 (locality-changes-
coupling) remains the open row.
