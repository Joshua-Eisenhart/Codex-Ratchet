# Cellular-automaton MSS research program

_Status: hypothesis/search design under Ratchet v0.5. No CA family, gate boundary, or gate order is admitted by this
document._

## Question

Does some finite local automaton provide a weaker surviving presentation of the currently required constrained-
distinguishability dynamics than the installed global-map, density-operator, manifold, or other carrier families?

F01 motivates finite realizations. It does not by itself imply cells, a lattice, locality, a global clock, homogeneity,
reversibility, or quantum state structure. Those are precisely what this bakeoff must test.

## Root boundary

The input to the bakeoff is a finite constrained-distinguishability obligation and finite history, not a set of already
real objects or cells. A candidate earns cells only if stable local distinction bundles survive and a non-cell
presentation cannot carry the same obligation more weakly.

Generate CA and non-CA candidates together with rival drive/readout hypotheses. A missing drive witness prevents a CA
tooth in that packet, but triggers more gradient/probe/carrier digging rather than a terminal HOLD. Finitude or the
availability of a CA implementation is not itself a reason for the Ratchet to move.

## Candidate families

Freeze at least one candidate from each applicable family:

| ID | Family | Additional structure it installs |
|---|---|---|
| C0 | finite partial distinction/update table | finite marks and supplied transitions only |
| C1 | finite-state transducer | explicit state and input/output interface |
| C2 | asynchronous local rewrite or event structure | locality without a global synchronous clock |
| C3 | partitioned ring/checkerboard automaton | cyclic adjacency, parity/block partition, alternating schedule |
| C4 | reversible block automaton | C3 plus invertibility/reversibility |
| C5 | bounded-degree evolving graph automaton | local updates with geometry/topology allowed to change |
| C6 | QCA/open-chain local-unitary fixture | finite local Hilbert/operator structure and unitarity |

Add rivals rather than choosing from this table when a new family may be weaker. The table is an initial finite grammar,
not an exhaustive ontology.

## Frozen obligations

Do not test “is CA good?” Mine finite obligation families, then test fused and split gate-boundary hypotheses rather
than assuming “one obligation at a time” is the canonical decomposition. Candidate obligation families include:

1. retain a finite distinction under a supplied update;
2. exhibit a genuine order witness `U_B U_A != U_A U_B`;
3. preserve a distinction under finite perturbation/history when persistence is demanded;
4. reproduce only the locality behavior actually required by held-out probes;
5. make geometry/entropy co-views recompute from one altered distinction surface;
6. project to the current weaker predecessor without importing later labels;
7. remain killable by reachable controls.

If C0 or C1 closes the active obligation set, a CA lift is nonminimal for that schedule step. Locality becomes a
provisional tooth only when a named observation or constraint demands it across the tested gate/order population.

## Ring-checkerboard hypothesis

The ring checkerboard is a strong C3/C4 candidate because two disjoint block partitions can support

\[
U=U_BU_A,\qquad \widetilde U=U_AU_B,
\]

with an observable noncommutation witness. Its installed assumptions must be individually attacked:

- cyclic adjacency;
- a fixed even/odd coloring;
- fixed cell identity;
- homogeneous local rule;
- global or two-phase clock;
- fixed versus evolving topology;
- single-token versus full-field configuration semantics;
- classical versus quantum local state.

The existing Codex-Ratchet evidence gives useful ceilings, not CA admission:

- `system_v6/sims/ring_checkerboard_automaton_v0/`: bounded classical single-active-token floor; its headline period
  ratio was definitionally forced, while a transient-SCC difference survived audit.
- `system_v6/sims/gcm_ring_checkerboard_runner_v1/`: frozen 16-survivor brickwork fixture; strict locality belongs to a
  separate ring-local variant; no full field dynamics.
- `system_v6/sims/ring_checkerboard_qca_v3/`: bounded open-chain crossing-rank fixture with opposite L/R signs; not a
  nontrivial finite-ring automorphism-class index or full QCA admission.

These failures and ceilings should seed the negative-control registry.

## Generated CA control library

Select and generate the controls relevant to the precise CA claim; do not impose this entire list on unrelated gates:

- phase-label and parity-label erasure;
- `AB` versus `BA`, phase merge, and commuting-rule controls;
- ring shuffle and same-size non-ring graph control;
- local rule versus all-to-all/global successor;
- fixed topology versus an evolving bounded-degree graph;
- single-token versus full configuration-field dynamics;
- synchronous versus asynchronous update;
- definitionally pinned period versus a statistic not algebraically fixed by the schedule;
- calibration/shift relabel rejection for QCA rows;
- finite open chain versus periodic ring, with boundary-dependent claims separated;
- resolution/alphabet/site-count sweeps without a limit-to-infinity claim.
- source/schedule freeze when the proposed drive predicts a freeze response;
- exogenous-versus-endogenous source accounting;
- candidate-response coupling to each proposed distinction/entropy drive.

## Weakness witnesses

Useful candidate-to-candidate weakenings include:

- forget the metric/amplitudes but retain the transition relation;
- forget cell identity and retain local event incidences;
- remove cyclic closure to obtain an open chain;
- remove the clock and retain a partial order of events;
- remove homogeneity and retain finite local rewrite rules;
- remove quantum phases and retain the induced classical transition structure;
- restrict full-field dynamics to a single-particle sector, never treating that restriction as proof of the reverse;
- allow graph adjacency to evolve, testing whether a fixed ring was ornamental.

Every edge must name the executable projection and show that the frozen obligation is preserved.

## Decision rule

The output is the set of all tested surviving candidates with no strictly weaker tested survivor. It may be plural.

Allowed statement:

> Within CA grammar hash `g`, weakening grammar hash `w`, tests `b`, resolution `r`, and budget `k`, candidates
> `{...}` form the current minimal-survivor frontier.

Forbidden statement:

> Finitude proves the universe is this CA.

## First order-open bounded packet

1. Express one existing ring-checkerboard N01 obligation as a carrier-neutral finite distinction/history table.
2. Mine competing demand families; generate fusions, splits, and every finite order allowed by the schedule budget.
3. Generate thousands of CA and non-CA parameter proposals, while reporting behavioural aliases separately from
   independently acting compilers.
4. Implement C0, C2, C3, and C5 against exactly that table and budget; park failures visibly with continuation cursors.
5. Generate rival coface gradients, weakenings, topology/clock negatives, and counter-surfaces where lower candidates win.
6. Measure every candidate response and kill drive hypotheses that do not couple or survive their declared controls.
7. Register explicit forgetting maps and compute every schedule-indexed provisional frontier with `ratchet_engine.py`.
8. Emit a `ratchet-order-open-run/0.5` receipt with deaths, attacks, aliases, schedule divergences, authored seeds, and
   separately run-derived unordered digs.
9. Only if drive, MSS, and claim-specific controls all survive should locality become a provisional tooth. Otherwise
   continue digging until the finite budget boundary; do not convert one inconclusive packet into global absence.
