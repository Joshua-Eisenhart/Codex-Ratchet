# manifold_L8_cut_lattice_gate2_b

Gate 2 Builder B packet for the L8 cut lattice only.

Authority source: `system_v7/sims/GATE2_SPEC_EXTRACTION_20260703.md`.

The packet consumes Gate 1 data from `ratchet_formal_gates_v1` and reconstructs
the finite 3-qubit density roster from the full Pauli p-vectors. It enumerates
the contract-pinned `2^(n-1)-1 = 3` unordered bipartitions for `n=3`, computes
per-cut marginals by explicit partial trace, and verifies the label-echo seam
with a known-inconsistent parent/marginal pair.

This is quarantined as `scratch_diagnostic` with `promotion_allowed=false`.
The owner-tunable choice to bundle L9/L10 is followed as `OPEN-CHOICE: not
bundled`; any rank/entropy/control values are used as L8 controls, not as an
L9/L10 promotion claim.
