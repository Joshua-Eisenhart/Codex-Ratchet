# Force Transition Channel Taxonomy

Claim ceiling: completed finite force/transition-channel taxonomy scratch diagnostic. The completed JAX receipt is:

`/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/spinor_network_force_transition_channel_taxonomy_results.json`

The Julia mirror is:

`/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/spinor_network_force_transition_channel_taxonomy_julia_results.json`

The result supports distinct finite transition-channel readouts over the same spinor-network substrate family used by the face taxonomy. It does not admit forces, particles, gravity, Axis0, physics, `M(C)`, PEPS3D, bridge promotion, final manifold closure, or a Standard Model claim.

## Source Boundary

Primary sources:

- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/sim_spinor_network_force_transition_channel_taxonomy.py`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/spinor_network_force_transition_channel_taxonomy_results.json`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/spinor_network_force_transition_channel_taxonomy.jl`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/spinor_network_force_transition_channel_taxonomy_julia_results.json`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/docs/session_20260606_physics_excavation/06_FACE_READOUT_TAXONOMY.md`

Dependency:

- face taxonomy source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/sim_spinor_network_face_readout_taxonomy.py`
- face taxonomy result: `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/spinor_network_face_readout_taxonomy_results.json`

## State

`COMPLETED`.

Receipt fields:

| Field | Value |
|---|---:|
| `schema` | `FINITE_SPINOR_NETWORK_FORCE_TRANSITION_CHANNEL_TAXONOMY_v1` |
| `classification` | `scratch_diagnostic` |
| `all_pass` | `true` |
| `formal_admission_allowed` | `false` |
| `promotion_allowed` | `false` |
| `channel_response_rank` | `4` |
| `parity.within_1e_10` | `true` |
| `parity.parity_max_diff` | `3.885780586188048e-16` |
| `parity.worst_key` | `weak_decay_topology_change.trace_distance` |

The scratch-diagnostic fence remains load-bearing: this is a finite transition taxonomy, not a force-admission result.

## Object

The finite object is a channel bank over a finite spinor-network state:

- primitive carrier: finite spinor-network state `psi`;
- derived readout layer: spinor-derived density/readouts from the face taxonomy;
- graph edges: `(0,1)`, `(1,2)`, `(2,3)`, `(3,4)`, `(0,4)`;
- Hilbert dimension: `32`;
- channel family: finite transformations over the carrier/readout family.

This is the follow-up to the face taxonomy: after showing one substrate can host distinguishable face readouts, this scout asks whether named transition channels can also be separated as finite transformations rather than one force scalar relabeled.

## Channel Labels

These are interpretation labels only. They are not physics admission.

| Channel key | Readout role |
|---|---|
| `identity_control` | no-op control; must move no readouts. |
| `electromagnetic_phase_coupling` | phase/coupling channel label only. |
| `strong_binding_confinement` | binding/confinement channel label only. |
| `weak_decay_topology_change` | decay/topology-change channel label only. |
| `gravity_sync_flattening` | synchronization/flattening channel label only. |

## Channel Deltas

| Channel | Trace distance | expansion / dark energy | preserved info / dark matter | knot / matter mass | composite knot / baryons | transition / forces | sync gradient / gravity |
|---|---:|---:|---:|---:|---:|---:|---:|
| `identity_control` | `0.0` | `0.0` | `0.0` | `0.0` | `0.0` | `0.0` | `0.0` |
| `electromagnetic_phase_coupling` | `0.2676165673298173` | `0.0` | `-0.00375272257535042` | `0.0` | `0.0` | `-0.000851922071860578` | `0.0` |
| `strong_binding_confinement` | `0.9114378277661476` | `0.0` | `0.10000000000000006` | `-0.5000000000000007` | `0.9999999999999986` | `0.16037802155404335` | `-0.5000000000000008` |
| `weak_decay_topology_change` | `0.5000000000000003` | `0.1999999999999995` | `0.0` | `-1.0` | `0.0` | `-0.15875000000000017` | `-1.0` |
| `gravity_sync_flattening` | `0.2474873734152916` | `0.13380316701131045` | `-0.1338031670113114` | `-1.0` | `0.0` | `0.05027091895948432` | `-1.0` |

## Controls

| Control | Completed result |
|---|---|
| identity channel | Pass: `identity_control` has trace distance `0.0` and all readout deltas `0.0`. |
| anti-single-force-scalar | Pass: `channel_response_rank=4`, with minimum required rank `3`; channels are not one scalar relabeled. |
| EM phase selectivity | Pass: phase/coupling changes preserved-info and transition readouts while leaving expansion, matter, composite, and gravity deltas at `0.0`. |
| strong binding selectivity | Pass: binding/confinement activates composite-knot/baryon delta near `+1.0` and changes matter/gravity together. |
| weak decay selectivity | Pass: decay/topology-change removes matter/gravity readouts and changes transition in a different profile from binding. |
| sync flatten selectivity | Pass: synchronization/flattening removes matter/gravity readouts while increasing expansion and shifting preserved information. |
| finite spinor-network boundary | Pass: `n_spinor_nodes=5`, `hilbert_dimension=32`. |
| dual-backend parity | Pass: Julia mirror available; max backend difference is `3.885780586188048e-16`. |
| promotion fence | Pass: `classification=scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`. |

## Audit State

Repo-local verification:

- JAX source exists and wrote the JAX result receipt.
- Julia mirror exists and wrote the Julia result receipt.
- JAX/Julia parity is within `1e-10`.

External model audit state for this document:

- Grok CLI is not installed in this shell, so no Grok verdict is claimed for this new rung.
- Gemini audit returned `BY_CONSTRUCTION`, not `GENUINE`: the diagnostic confirms distinct, non-trivial effects inside the closed formal system, and JAX/Julia parity checks the implementation, but the channel separation is still a property of the constructed channel bank rather than an emergent discovery.

## Fence

The passing result supports:

- one finite spinor-network substrate family can host distinguishable channel transformations;
- the identity control does not move the readouts;
- named binding, decay/topology-change, phase/coupling, and synchronization/flattening channels have different finite response profiles;
- the channel response rank is `4`, so the result is not a single-force scalar relabel;
- JAX/Julia parity holds to about `3.9e-16`.

It does not support:

- electromagnetic force admission;
- strong force admission;
- weak force admission;
- gravity admission;
- particle admission;
- Standard Model reconstruction;
- dark-sector admission;
- Axis0;
- `M(C)`;
- PEPS3D;
- bridge;
- final manifold closure.

## Next Hardening Step

Use this result only as a fenced scratch diagnostic for channel-taxonomy discussion or follow-up scouts. The next finite hardening target is a source-independent adversarial reimplementation that does not import the face taxonomy module, varies the carrier family, and adds label-blind channel scrambling controls.
