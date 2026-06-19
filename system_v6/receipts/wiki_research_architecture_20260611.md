# Wiki Research Architecture Receipt - 2026-06-11

Status: kickoff complete.
Evidence ceiling: research architecture and corpus kickoff only; not sim result
evidence, not admission, not global uniqueness.

## Source Anchors

- Round-3 registry anchor: `de44219ed`,
  `system_v6/receipts/round3_discriminator_registry_20260611.md`.
- Knowledge-stack doctrine anchor: `c77898565`,
  `system_v5/codex_skills/sim-wizard/SKILL.md`.
- Wiki corpus root: `/Users/joshuaeisenhart/wiki/codex-ratchet-research`.

## Structure Created

The wiki corpus root now has a README contract and the requested layer
directories:

- `s2-connections`
- `s3-probes`
- `s4-operators`
- `s5-flows`
- `s67-topologies`
- `s9-transport`
- `s10-g2`
- `ratchet-order`

Each layer directory has the four-file contract:

- `standard-math.md`
- `alternatives.md`
- `negatives.md`
- `distillate.md`

`old-sims-mined/` was already present under the same root and was left
untouched by this kickoff.

## Populated Priority Layers

Priority came from the round-3 heavy/close-neighbor rows: S2 connections, S4
operators, S5 flows, and S9 transport.

| File | Lines | Status |
| --- | ---: | --- |
| `README.md` | 80 | architecture contract |
| `s2-connections/standard-math.md` | 50 | populated |
| `s2-connections/alternatives.md` | 45 | populated |
| `s2-connections/negatives.md` | 31 | populated |
| `s2-connections/distillate.md` | 27 | populated |
| `s4-operators/standard-math.md` | 49 | populated |
| `s4-operators/alternatives.md` | 40 | populated |
| `s4-operators/negatives.md` | 29 | populated |
| `s4-operators/distillate.md` | 26 | populated |
| `s5-flows/standard-math.md` | 48 | populated |
| `s5-flows/alternatives.md` | 39 | populated |
| `s5-flows/negatives.md` | 27 | populated |
| `s5-flows/distillate.md` | 26 | populated |
| `s9-transport/standard-math.md` | 39 | populated |
| `s9-transport/alternatives.md` | 42 | populated |
| `s9-transport/negatives.md` | 25 | populated |
| `s9-transport/distillate.md` | 26 | populated |

## Standing Queue Placeholders

The remaining layer dirs were created with explicit queue placeholders, not
researched claims.

| File | Lines | Status |
| --- | ---: | --- |
| `s3-probes/standard-math.md` | 10 | standing queue |
| `s3-probes/alternatives.md` | 11 | standing queue |
| `s3-probes/negatives.md` | 8 | standing queue |
| `s3-probes/distillate.md` | 8 | standing queue |
| `s67-topologies/standard-math.md` | 10 | standing queue |
| `s67-topologies/alternatives.md` | 9 | standing queue |
| `s67-topologies/negatives.md` | 9 | standing queue |
| `s67-topologies/distillate.md` | 8 | standing queue |
| `s10-g2/standard-math.md` | 9 | standing queue |
| `s10-g2/alternatives.md` | 8 | standing queue |
| `s10-g2/negatives.md` | 8 | standing queue |
| `s10-g2/distillate.md` | 8 | standing queue |
| `ratchet-order/standard-math.md` | 10 | standing queue |
| `ratchet-order/alternatives.md` | 7 | standing queue |
| `ratchet-order/negatives.md` | 8 | standing queue |
| `ratchet-order/distillate.md` | 7 | standing queue |

## Child Receipts

Codex-native child lanes wrote one packet each under `/tmp` and reported clean
write boundaries.

| Layer | Child packet | Lines | Use |
| --- | --- | ---: | --- |
| S2 | `/tmp/codex-ratchet-research-kickoff/s2_connections_child_packet.md` | 119 | accepted synthesis input |
| S4 | `/tmp/codex-ratchet-research-kickoff/s4_operators_child_packet.md` | 155 | accepted synthesis input |
| S5 | `/tmp/codex-ratchet-research-kickoff/s5_flows_child_packet.md` | 220 | accepted synthesis input |
| S9 | `/tmp/codex-ratchet-research-kickoff/s9_transport_child_packet.md` | 135 | accepted synthesis input |

External Gemini TUI cross-checks were attempted and captured as advisory
external notes, not Codex-native child receipts:

| Layer | Gemini note | Lines | Count status |
| --- | --- | ---: | --- |
| S2 | `/tmp/codex-ratchet-research-kickoff/s2_gemini_crosscheck.md` | 27 | advisory |
| S4 | `/tmp/codex-ratchet-research-kickoff/s4_gemini_crosscheck.md` | 32 | advisory |
| S5 | `/tmp/codex-ratchet-research-kickoff/s5_gemini_crosscheck.md` | 20 | advisory |
| S9 | `/tmp/codex-ratchet-research-kickoff/s9_gemini_crosscheck.md` | 17 | advisory |

No `grok-4.3` CLI was available on PATH during this kickoff, so no Grok receipt
is claimed.

## What Was Researched

S2:
- U(1)/Hopf connection one-forms, curvature, first Chern class, gauge versus
  lifted-holonomy distinctions, Stokes/annular flux validity.
- Round-3 same-curvature shifted-holonomy, endpoint-Chern-preserving bump,
  two-leaf match, and boundary-conditioning variants.
- Negatives: equal `c1` is not connection equality; same `F` is not lifted
  holonomy equality; sparse leaf matches are not global equality.

S4:
- Qubit CPTP channels as affine Bloch maps, Choi positivity, unital/non-unital
  split, Pauli geometry, amplitude damping, and axis-role preservation.
- Round-3 amplitude-damping, dephase-rotate, axis-permuted, and weak non-unital
  neighbors.
- Negatives: positive is not CP; non-unital shifts are not Pauli channels; axis
  relabels are not aliases when the parent z-probe moves.

S5:
- Affine flows `dr/dt = Ar+b`, fixed points versus transient flow, ball
  invariance, GKSL/Lindblad generator constraints, contraction/rotation
  mixtures.
- Round-3 alpha-mix, epsilon coefficient, weak shift, mirror-preserver, and
  basin-preserving null families.
- Negatives: finite-step ball preservation is not generator validity; same
  fixed point is not same flow; quotient survival is not alias.

S9:
- Connection moduli, curvature density, same-Chern/different-holonomy families,
  annular flux, and path-ordered transport for noncommuting loops.
- Round-3 same-`c1` bumps, one-leaf and two-leaf matches, and path-ordered loop
  neighbor.
- Negatives: equal `c1` is only co-survival; finite holonomy anchors are not
  global equality; noncommuting transport cannot drop path ordering.

## Remaining Research Queue

- `s3-probes`: POVM/SIC/MUB/probe-frame standard math, exact effect aliasing,
  and projective/order negatives.
- `s67-topologies`: cover/graph/lens-action classification, Mobius/Klein/shear
  negatives, and support-graph controls.
- `s10-g2`: no finite candidate ids were pinned by the cited round-3 registry;
  first task is to pin candidate ids and teeth.
- `ratchet-order`: read the round-2 breadth discriminator, then pin order
  canonicalizers and noncommutation negatives.

## Pollution Rule

Corpus never flows directly into MMMs.

Only `distillate.md` files may feed future cards, blind sheets, or MMM heads,
and even then only as bounded extraction. Distillates must keep the
nominalist/empiricist register: labels are tested distinctions, identity is
probe-relative, exclusion language comes before construction language, and no
reified abstraction or global uniqueness claim is promoted from research notes.

## Verification

Fresh local checks run by the controller:

- `find ~/wiki/codex-ratchet-research -maxdepth 2 -type f | sort | xargs wc -l`
- `wc -l /tmp/codex-ratchet-research-kickoff/*_child_packet.md /tmp/codex-ratchet-research-kickoff/*_gemini_crosscheck.md`
- `git status --short`

Observed before this receipt was written: repo status showed only unrelated
untracked `system_v6/sims/geo_s10_intertwiner_depth_v0/`. No git add or commit
was run.

