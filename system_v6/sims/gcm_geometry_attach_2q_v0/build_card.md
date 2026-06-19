# gcm_geometry_attach_2q_v0 Build Card

DECLARE: layers 3-12 + 17-18 | integrated-onto-the-carve | 2Q.

Scope: attach geometry to the 544 survivors from `gcm_constraint_carve_2q_v0`, using `gcm_geometry_attach_v0` as the 1Q realization authority. The packet is `scratch_diagnostic`, carrier-and-pins-relative, and not THE manifold.

Substrate-first gate: every result consumes `gcm_object_id gcmobj_a40e54e13cec01466c9d675028b3574b` through `scripts/gcm_substrate_check.py`, cites the frozen registry body hash, and keeps the lineage-free negative red.

Authority:
- `748fca97c`: 1Q attach, realization rule, G1 caveat pattern, and NESTED definition.
- `218fac1a1`: 2Q carve, 544 survivors, and 16 entangled purification-boundary survivors.
- `gcm_2q_freeze_and_cut_v0`: dependency checked by path/hash when landed; otherwise this packet derives provisional 2Q ids by the content rule and records the dependency.

Geometry:
- Product survivors get pairs of realized 1Q Bloch points from the normalized x/z probe-signature rule. Raw carve coordinates remain pins; product geometric marginal radii are checked as exactly 1.
- Entangled survivors get reduced-state Bloch radii below 1, Schmidt angles, marginal positions in `D(C^2) x D(C^2)`, and correlation data that the marginals miss.
- The fiber over each entangled marginal pair records finite carved members plus phase witnesses with identical marginals and distinct correlations; this is the fiber over each marginal pair check.
- Cross-rung shell map reports which 1Q eta shells the normalized marginal directions occupy.

G1-pattern honesty: any pattern found here is only a carved-support signature reading until proven more.

Controls:
- Product survivors' geometric marginal radii = 1 exactly.
- Carve-erasure removes nested attachment status.
- 1Q regression through partial trace checks the normalized A-marginal image against the 1Q attach Hopf set.

G.2a boundary: builder output sets `no_builder_audit_verdict=true` and uses `scripts/builder_audit_boundary.py`. No builder-written `audit_verdict.md`.

NO git add/commit.
