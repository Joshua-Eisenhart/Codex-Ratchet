# Independent Audit Verdict - gcm_geometry_attach_v0

Fresh audit / read-only audit. Auditor: independent cross-backend auditor. Freshness tier:
TIER-2 results-available; no prior audit verdict was present before this file. Authorized
live write: this file only. No git add/commit.

Bottom line: VERDICT = GENUINE-WITH-CAVEATS. The packet genuinely attaches the frozen
`gcm_object_id` survivor/class/region lineage to 1Q `C^2/S^3/Hopf/density/T_eta` geometry,
and my independent recomputations matched the emitted result. The ceiling is
`scratch_diagnostic_first_nested_packet_layers_3_12_1Q_carrier_and_pins_relative`;
`promotion_allowed=false`; `formal_admission_allowed=false`; not THE manifold, not terrain,
not stage, not engine, not axis, not runtime flux.

Main caveat: `G1_shell_pattern_is_carved_grid_signature`. The 2-4-4-4-2 shell pattern is
real for the committed survivor set, but it is not independent first-manifold geometry. It
is the geometry readout of the C1/C2/C3 carved active-probe support: the eight nonzero
`(sx, sz)` signatures of the local grid, doubled by the hidden `y` lineage. Citation must
say "carved-grid/probe-signature shell readout", not "manifold shell law".

## What I Checked

- Authority and scope: the build card declares layers 3-12, integrated-on-carve nesting,
  1Q depth, scratch ceiling, no git add/commit, and the anti-bias boundary
  (`build_card.md:1-6`, `:23-31`).
- NESTED bar: the layer-stack reference requires same object/lineage, lower-to-upper maps,
  removal/quotient controls, and recomputed induced geometry (`gcm_layer_stack_reference_20260612.md:45-49`).
- Realization rule: the build card pins `(sx, sz)` from each frozen survivor before the
  advertised result (`build_card.md:46-55`), and the source implements that rule directly
  (`gcm_geometry_attach_v0_common.py:248-270`).
- Boundary/process: G.2a requires builder/audit separation and post-audit idempotency
  (`audit_standards_codex_v1.md:152-180`); this packet delegates through the boundary helper
  (`gcm_geometry_attach_v0_boundary.py:12-26`).

## Recomputations

Realization rule:

- Recomputed candidates 31, 32, 33, 41, 42, and 43 from the frozen registry only.
- The recomputed `psi`, Hopf projection, and `eta` labels matched emitted rows within
  `2e-15` tolerance.
- This is not a post-hoc free fit: the rule uses only the frozen `probe_signature`, then
  `n=(sx,0,sz)/sqrt(sx^2+sz^2)` and the fixed Hopf section.

Shell pattern:

- Survivor recomputation: `0:2`, `pi/8:4`, `pi/4:4`, `3pi/8:4`, `pi/2:2`.
- Original 125 grid under the same rule does not force the headline pattern: it has 120
  realizable active signatures across 9 eta labels plus 5 zero-signature rows.
- C1 density carrier with active probes has 28 realizable rows with counts
  `0:4`, `pi/8:6`, `pi/4:8`, `3pi/8:6`, `pi/2:4`, plus 5 zero-signature rows.
- The full C1/C2/C3 survivor rule has exactly 16 rows and exactly the packet pattern
  `0:2`, `pi/8:4`, `pi/4:4`, `3pi/8:4`, `pi/2:2`.

Adjudication: not realization-rule-induced in the bad sense; the rule was pinned and
recomputes. But the symmetric shell headline is a carved-grid/probe-support shadow, not a
new free geometry law.

Class preservation:

- Density quotient recomputation produced 8 quotient density states for 8 frozen quotient
  classes.
- Members inside each quotient class shared the same density readout, while the 8 class
  readouts remained distinct.
- The emitted source computes the density hash and class survival from row data, not by
  assuming it (`gcm_geometry_attach_v0_common.py:389-448`).

NESTED definition, five requirements:

- Same `gcm_object_id`: pass. The packet consumes
  `gcmobj_a40e54e13cec01466c9d675028b3574b` and the frozen registry body hash declared in
  the build card (`build_card.md:16-18`).
- Same survivor/class/region lineage: pass. The result emits all survivor, quotient-class,
  and candidate-region IDs plus object maps (`gcm_geometry_attach_v0_common.py:642-649`).
- Lower-to-upper maps: pass. Each row maps survivor -> spinor -> quotient class -> rho ->
  candidate region -> shell (`gcm_geometry_attach_v0_common.py:352-432`).
- Removal controls: pass. Phase quotient preserves density/class/region/shell readouts but
  loses S3 fiber anchoring; carve erasure leaves unanchored feedstock and no lineage
  (`gcm_geometry_attach_v0_common.py:464-514`).
- Induced geometry recomputed: pass. Hopf projection, density matrix, connection/curvature,
  and shell rows are recomputed from the survivor signatures (`gcm_geometry_attach_v0_common.py:288-326`,
  `:650-663`).

Substrate enforcement:

- Fresh `gcm_substrate_check` on the real payload returned `ok=true`.
- Fresh lineage-free variant returned `ok=false` with named errors:
  `gcm_object_id mismatch`, `registry_body_sha256 missing from lineage`, and
  `missing lineage consumption`.
- The helper enforces object id, registry body hash, registry identity, and at least one
  resolved survivor/class/region lineage citation (`scripts/gcm_substrate_check.py:83-90`,
  `:100-146`, `:148-169`).

Seven contract questions:

- Which layer? Layers 3-12.
- Which nesting relation? Integrated onto the frozen carve.
- Which qubit depth? 1Q.
- Which surface/network? No CA/QCA runtime surface. Only a lineage graph check plus
  attached 1Q geometry. This is honest for first nested attachment, but not a full rich sim.
- Which engines? Julia, JAX, and PyTorch lanes ran and are distinct.
- Which entropy/readout families varied? No sweep. Density quotient and pure-state vN-zero
  readout only.
- What broke when depth/nesting/surface was removed? Phase quotient loses S3 fiber
  anchoring; carve erasure loses nested-substrate status; depth/surface-removal sweeps are
  not claimed.

## Engines And Tools

The three-engine claim is acceptable at scratch scope. The packet is not just parity prose:

- Julia uses `Manifolds.Sphere(3)` to instantiate the S3 carrier and gate dimension/unit
  rows (`gcm_geometry_attach_v0_julia.jl:64-101`, `:113-139`).
- JAX lane uses `networkx` for lineage graph resolution and `sympy` for exact count guards;
  JAX arrays are supportive, not claimed load-bearing (`gcm_geometry_attach_v0_jax.py:34-56`,
  `:79-154`).
- PyTorch lane uses `torch.func.vmap` over density observables plus `sympy` exact guards
  (`gcm_geometry_attach_v0_pytorch.py:31-84`, `:96-123`).
- The generic strict three-engine validator returned no errors with `require_pytorch`,
  `strict_source_backed`, and `require_tool_intent`.

This is still a thin 1Q attachment, not a rich surface/runtime packet. Julia's `Manifolds`
use is load-bearing because it gates the S3 carrier row, but it is minimal and should not be
cited as deeper manifold evidence.

## Checks Run

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py --json`
  - Result: `summary.ok=true`, `install_state=stable_observed`, no repo pollution or active installers.
- Read-only Python audit with `PYTHONPATH=system_v6/sims/gcm_geometry_attach_v0:scripts`.
  - Result: fresh `common.build_packet()` returned `all_pass=true`; counts and shell rows matched live results; `common.validate_payload(live_result)` returned `[]`; boundary errors `[]`; strict three-engine validator errors `[]`; substrate positive green and lineage-free negative red.
- Read-only Julia recomputation under
  `JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=system_v5/julia_carrier`.
  - Result: 16 survivors, 8 density states, 5 shells, shell counts `0:2`, `pi/8:4`,
    `pi/4:4`, `3pi/8:4`, `pi/2:2`, `Manifolds.Sphere(3)` dimension 3, max norm errors 0.

I did not run the packet validator command in-place because it writes
`results/gcm_geometry_attach_v0_validator_results.json`, outside this audit's allowed live
write scope. The equivalent validator functions were run read-only.

## Citation Rule

Allowed citation:

`gcm_geometry_attach_v0` = `GENUINE-WITH-CAVEATS` first nested 1Q attachment:
16 frozen survivors -> normalized C2/S3 spinors; density quotient preserves 8 frozen
classes; shell occupancy is `0:2, pi/8:4, pi/4:4, 3pi/8:4, pi/2:2`; substrate enforcement
green on real payload and red on lineage-free variant.

Required caveat on every citation:

`G1_shell_pattern_is_carved_grid_signature`: the shell symmetry is a computed readout of
the C1/C2/C3 carved active-probe grid support, not independent manifold geometry.

Forbidden citation:

Do not cite this as THE manifold, terrain/stage/engine/axis/runtime admission, runtime
flux, physics evidence, formal admission, full rich sim, or proof that 1Q/2Q proves a
layer. The current checkout also shows `system_v6/sims/gcm_geometry_attach_v0/` as
untracked, so until a separate checkpoint exists, cite it as a current checkout packet
rather than a committed packet.
