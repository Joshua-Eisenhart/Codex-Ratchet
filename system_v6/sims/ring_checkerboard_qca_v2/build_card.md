# BUILD CARD - ring_checkerboard_qca_v2

Builder: codex2 (builder, xhigh). Repo: `/Users/joshuaeisenhart/Codex-Ratchet`.

Boundary: build everything inside `system_v6/sims/ring_checkerboard_qca_v2/`. No `git add` or commit.

## Authority

Read in order:

1. CA doctrine with all entries: `3d1932d8f`, QCA-v1 kill `88b5e9ff1`, and amendment `0df679d94`.
2. Research note: `~/wiki/codex-ratchet-research/standard-math/gnvw-index-1d-qca.md`.
3. Classical floor: `fe06d49bd`, for the dephased-limit continuity row.

Binding amendment:

- v1 died because the "index" was rule-table flow metadata read back.
- On the finite periodic ring, the automorphism-class index is always trivial by the finite-ring/Skolem-Noether caveat.
- v2 primary realization must be on an open chain; the ring is a separately labeled closure row.
- Rules enter as local unitaries without flow metadata.
- The index is extracted by the finite crossing-rank procedure from realized operators at a cut.
- Gauge means an actual inserted onsite unitary with ranks recomputed.

## Object

On a pinned small open chain:

- realize right shift, left shift, a non-shifting onsite/two-site rule, and O1 L/R engine rules as actual unitaries;
- extract index per rule from crossing ranks, not stored wire counts;
- require +1/-1/0 calibrations to come out of computation;
- require L/R engine rows to compute opposite signs;
- require index-0 controls to show no L/R distinction under declared probes;
- insert a real onsite unitary and recompute ranks for the gauge row;
- compute the same rules on a periodic ring as closure rows and label the automorphism-class result as trivial;
- include the dephased classical-limit row reproducing the committed/corrected v0 phase structure.

## Engineering Contract

- Honest `TOOL_INTENT_MATRIX`.
- QuantumOptics and QuantumClifford genuinely load-bearing in the Julia leg.
- SMT binds computed ranks and indices with real-unitary flips.
- Use the standard envelope builder.
- Use the builder/audit boundary helper fully.
- Include validators and pytest.

## Claim Ceiling

`scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

This packet may support only the bounded open-chain fixture and closure-row claims above. It must not claim canonical QCA admission, a nontrivial finite-ring automorphism-class GNVW index, full engine admission, v4 coupling-law admission, or owner-source status for GNVW/index terminology.
