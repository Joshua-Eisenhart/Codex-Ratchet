# gcm_3q_freeze_and_cuts_v0 Build Card

Declare: freeze/registry + cut layers | carve-attached | 3Q.

Goal: freeze the content-derived 3Q attachment surface from the committed `gcm_constraint_carve_3q_v1` packet, then attach all three bipartition cuts: A|BC, B|AC, and C|AB.

Scope:
- Input authority: 3Q carve v1 commit surface with 545 state-artifacted survivors and zero-mismatch matrix.
- Registry: `gcm3qobj_...` content id plus 545 survivor IDs, 9 quotient classes, and class-local candidate regions.
- Cut lattice: reduced `rho_left` and `rho_right` stored for A|BC, B|AC, and C|AB.
- Entropy families: S, S(.|.), mutual information I, coherent information I_c, and negativity per cut.
- CKW: recompute monogamy from stored `rho_ABC` for the tripartite entangled survivor set.
- Controls: stale, forged, and lineage-free negatives at 1Q, 2Q, and 3Q; 2Q partial trace regression.

Boundary:
- classification: scratch_diagnostic.
- runtime flux is blocked here; J_ent/J_cut at 3Q is the next packet, not this one.
- G.2a from birth.
- NO git add/commit.
