# gcm_entropy_family_sweep_v0 Build Card

## Contract

Build `gcm_entropy_family_sweep_v0` as a file-disjoint GCM successor packet.
NO git add/commit.

Declared coordinates:

- layers 3-12 (the entropy dimension)
- integrated-onto-the-carve
- 1Q

Ceiling:

- `scratch_diagnostic`
- carrier-and-pins-relative
- not THE manifold
- no Axis0, bridge, runtime-engine, terrain, or 2Q+ entanglement promotion

## Substrate

The packet consumes the frozen GCM object:

- `gcm_object_id`: `gcmobj_a40e54e13cec01466c9d675028b3574b`
- `registry_body_sha256`: `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`
- lineage IDs: `survivor_id`, `quotient_class_id`, `candidate_region_id`, and geometry-attach `object_maps`

The validator must pass `scripts/gcm_substrate_check.py` on the real lineage and must keep the lineage-free negative red.

## Authority

- Wiki contract: every layer tests its admissible entropy families; nesting constrains survival.
- `/Users/joshuaeisenhart/wiki/concepts/entropy-sweep-protocol.md`
- `/Users/joshuaeisenhart/wiki/concepts/axis-and-entropy-reference.md`
- `system_v6/receipts/gcm_layer_stack_reference_20260612.md`
- Freeze registry by hash.
- Carve and geometry-attach packets by hash. Geometry attach is consumed conditionally: the local validator is green, but this packet does not claim that the independent attach audit is closed.

## Computation

For the 16 survivors, 8 quotient classes, and 5 occupied shells:

- compute 1Q survivor-state von Neumann entropy;
- compute the Renyi-alpha ladder;
- compute Tsallis-q forms;
- compute min entropy, max entropy, and linear entropy;
- compute shell-weighted forms over occupied strata;
- compute class-level mixed-state entropies;
- emit a nesting-constraint row naming which families are admissible at 1Q and which require missing structure;
- emit a survival row naming which families separate classes or shells and which are degenerate.

At 1Q on this attached carve, conditional entropy, mutual information, coherent information, entanglement entropy, entanglement spectrum, negativity, and logarithmic negativity require structure that is not installed yet: a bipartition, cut state, or 2Q+ carrier.

## Controls

- Real lineage substrate positive.
- Lineage-free substrate negative red.
- Phase-quotient invariance per scalar entropy family.
- Scrambled-class assignment control. If a family is claimed to separate classes, this control must break that separation; current expected result is stricter and more conservative: no 1Q entropy scalar separates the 8 classes.

## G.2a Boundary

G.2a from birth:

- builder writes no `audit_verdict.md`;
- envelope includes `no_builder_audit_verdict`;
- validator uses `scripts/builder_audit_boundary.py`;
- any future audit verdict must be independent/fresh.
