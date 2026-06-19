# gcm_geometry_attach_2q_v1 Build Card

DECLARE: layers 3-12 + 17-18 | integrated-onto-the-carve | 2Q.

Scope: attach geometry to the 544 survivors from `gcm_constraint_carve_2q_v0`, using `gcm_geometry_attach_v0` as the 1Q realization authority and the landed `gcm_2q_freeze_and_cut_v0` stored actual 2Q states as the entangled-state authority. The packet is `scratch_diagnostic`, carrier-and-pins-relative, and not THE manifold.

Substrate-first gate: every result consumes `gcm_object_id gcmobj_a40e54e13cec01466c9d675028b3574b` and the 2Q registry `gcm2qobj_715e9424ea66468243108751fb59395f` by hash through `scripts/gcm_substrate_check.py`, cites the frozen registry body hashes, and keeps the lineage-free negative red.

Authority:
- `748fca97c`: 1Q attach, realization rule, G1 caveat pattern, and NESTED definition.
- `218fac1a1`: 2Q carve, 544 survivors, and 16 entangled purification-boundary survivors.
- `8326405e6`: committed `gcm_2q_freeze_and_cut_v0` keystone, landed 2Q registry, and stored state authority. This packet cites that committed registry; it does not keep claims conditional on an in-flight 2Q registry audit.
- `gcm_geometry_attach_2q_v0` plus audit `98c6e4874`: v0 is accepted only as the scalar-derived baseline whose entangled rows must be regressed against state-derived rows.

Geometry:
- Product survivors get pairs of realized 1Q Bloch points from the normalized x/z probe-signature rule. Raw carve coordinates remain pins; product geometric marginal radii are checked as exactly 1.
- Entangled survivors get geometry re-derived from stored actual 2Q states by final gcm2qsurv ids: Schmidt angles and bases from `rho_AB`, reduced matrices plus radii from `rho_A/rho_B`, marginal positions in `D(C^2) x D(C^2)`, and correlation data that the marginals miss.
- The fiber over each entangled marginal pair records finite carved members plus phase witnesses with identical marginals and distinct correlations; this is the fiber over each marginal pair check.
- Cross-rung shell map reports which 1Q eta shells the normalized marginal directions occupy.
- Final `gcm2qsurv_*` ids replace the v0 provisional `gcm2qgeom_*` / `gcm2qent_*` ids, with the old ids retained only in the v0 regression block.
- The negativity cross-check must reproduce the freeze values `0.25` and `1/(2sqrt2)` from the stored states.
- The v0 regression compares scalar-derived rows against state-derived rows; the diff is recorded as v0's honest error bars.

G1-pattern honesty: any pattern found here is only a carved-support signature reading until proven more.

Controls:
- Product survivors' geometric marginal radii = 1 exactly.
- Entangled-state derivation starts from stored matrices, not boundary scalar fields.
- Carve-erasure removes nested attachment status.
- 1Q regression through partial trace checks the normalized A-marginal image against the 1Q attach Hopf set.

G.2a boundary: builder output sets `no_builder_audit_verdict=true` and uses `scripts/builder_audit_boundary.py`. No builder-written `audit_verdict.md`.

NO git add/commit.
