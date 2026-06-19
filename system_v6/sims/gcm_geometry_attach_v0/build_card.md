# Build Card - gcm_geometry_attach_v0

Status: ladder step 3 nested attachment packet.
Claim ceiling: `scratch_diagnostic`; first nested packet; layers 3-12 at 1Q; carrier-and-pins-relative; not THE manifold, terrain, stage, engine, axis, or runtime claim.
Write scope: `system_v6/sims/gcm_geometry_attach_v0/` only, including generated result JSONs under `results/`.
Git boundary: NO git add/commit.

## Authority

Read-first authority:

1. `system_v6/receipts/gcm_layer_stack_reference_20260612.md`
   - `c9ccf9991`: standing layer-stack reference and ladder step 3.
   - `437f837ea`: three-axis declaration rule and anti-bias rule.
   - `e4f03353a`: entropy/readout family and nesting-license rule.
2. `system_v6/sims/gcm_object_id_freeze_v0/results/gcm_object_id_freeze_v0_registry.json`
   - frozen `gcm_object_id`: `gcmobj_a40e54e13cec01466c9d675028b3574b`
   - frozen registry body hash: `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`
3. `scripts/gcm_substrate_check.py`
4. `system_v6/receipts/audit_standards_codex_v1.md`
5. `scripts/builder_audit_boundary.py`

## Three-Axis Declaration

- layer coordinate: layers 3-12, minimal QIT carrier through Hopf tori.
- nesting coordinate: `integrated-onto-the-carve`.
- qubit-depth coordinate: `1Q`.

Anti-bias boundary: 1Q establishes exact Hopf/spinor geometry on the frozen candidate substrate. It does not prove terrain, runtime, flux-runtime, axis, bridge, engine, or full layer completion.

Entropy/readout declaration: density quotient readout (`rho = psi psi^dagger`) and pure-state von Neumann entropy check. Because the attached 1Q states are pure density quotients, entropy is expected to be zero for every quotient class. This is an attachment readout, not an entropy-family promotion.

## Packet Contract

This packet is the first consumer of the frozen GCM object IDs. It must attach base geometry to the same frozen object, survivor, quotient-class, and candidate-region lineage:

- `gcm_object_id`
- every `survivor_id`
- every `quotient_class_id`
- every `candidate_region_id`

The packet emits maps lower -> upper:

`survivor_id -> spinor coords -> quotient_class_id -> rho -> candidate_region_id -> T_eta shell`

## Realization Rule

The carve was density-state-derived on a finite Bloch-grid carrier. This packet uses the frozen active probe signature `(2*x, 2*z)` as the pinned 1Q realization rule:

1. Take each frozen survivor's `probe_signature = (sx, sz)`.
2. Form the pure Bloch direction `n = (sx, 0, sz) / sqrt(sx^2 + sz^2)`.
3. Fix the Hopf section by `psi = (cos(theta/2), exp(i*phi) sin(theta/2))`, with `theta = arccos(n_z)` and `phi = 0` for `n_x >= 0`, `phi = pi` for `n_x < 0`.
4. This intentionally quotients away the hidden `y` coordinate for the 1Q Hopf carrier; the survivor anchoring still retains the two y-sign survivors through lineage, not through the pure density quotient.

Expected outcome: the 16 survivor rows map to 16 anchored spinors but only 8 density quotient states, one per quotient class. The class structure must survive the density quotient; if it does not, the packet reports that as the finding.

## Required Computations

- compute normalized spinor `psi` in `C^2` and `S^3` for all 16 survivors;
- compute Hopf projection / Bloch image for every survivor;
- compute density quotient `rho = psi psi^dagger`;
- recompute quotient-class survival under density quotient;
- compute Hopf connection readouts and curvature/geometric-flux readouts on survivor loci;
- compute occupied `T_eta` shell strata;
- attach fiber-loop and base-loop formulas to the frozen lineage;
- run phase-quotient control;
- run carve-erasure / lineage-free negative control;
- run `gcm_substrate_check(payload)` green and a lineage-free variant red inside the validator.

## G.2a Boundary

This packet uses `scripts/builder_audit_boundary.py` from birth. The builder does not write `audit_verdict.md`; if a later independent audit creates one, the validator accepts it only through the shared independent/fresh/read-only header gate.
