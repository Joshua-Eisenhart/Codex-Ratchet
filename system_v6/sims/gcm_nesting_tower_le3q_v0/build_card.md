# gcm_nesting_tower_le3q_v0 Build Card

## Scope

Build the nesting law's next rung: the carrier-and-pins-relative <=3Q inverse-limit tower over the frozen 1Q registry, frozen 2Q registry, and state-artifacted `gcm_constraint_carve_3q_v1` survivor registry.

Declared coordinates:

- `nesting/tower`
- `inverse-limit`
- `<=3Q`

## Authority

- `gcm_nesting_tower_le2q_v0` + audit: `28052037d`
- `gcm_constraint_carve_3q_v1`: `5544ad21c`
- `nesting_law_final_object_spec_20260612.md`: `afe7aa57b`

## Contract

- Classification: `scratch_diagnostic`
- Ceiling: `scratch_diagnostic_le3q_tower_carrier_and_pins_relative`
- Promotion allowed: `false`
- Formal admission allowed: `false`
- G.2a from birth: no builder-authored audit verdict, file-disjoint packet, independent-audit boundary preserved.
- Substrate-first: hardened `scripts/gcm_substrate_check.py` is load-bearing for 1Q/2Q lineage; 3Q v1 source/count/content-id lineage is checked packet-locally because the hardened helper is intentionally scoped through 2Q.

## Computation

For each stored 3Q survivor `rho_ABC`, recompute all three cut partial traces:

- `A|BC`
- `B|AC`
- `C|AB`

Each cut tests:

- single-side exact/probe relation to the frozen 1Q registry;
- pair-side exact/probe relation to the frozen 2Q registry;
- all-cut compatible family multiplicity.

The result also records:

- compressed compatible family rows for exact and probe relations;
- extension fibers `F_3` over 2Q survivors for `AB`, `AC`, and `BC`;
- root-axiom replication question at 3Q;
- Schmidt/pure-state strata and mixed density-rank strata per cut;
- tower-orphan characterization;
- controls: <=2Q regression, scrambled-pairing negative, product baseline.
