# Face Readout Taxonomy

Claim ceiling: completed finite taxonomy scratch diagnostic. The completed receipt is:

`/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/spinor_network_face_readout_taxonomy_results.json`

The result supports one bounded spinor-network substrate with six distinct readout maps. It does not admit dark matter, dark energy, gravity, forces, Axis0, physics, M(C), bridge, PEPS3D, final manifold closure, or consciousness.

## Source Boundary

Primary sources:

- `/Users/joshuaeisenhart/.claude/projects/-Users-joshuaeisenhart-Codex-Ratchet/memory/project_entropic_monism_face_readout_taxonomy.md`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/sim_spinor_network_face_readout_taxonomy.py`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/spinor_network_face_readout_taxonomy_results.json`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/spinor_network_face_readout_taxonomy_julia_results.json`
- `/tmp/face_taxonomy/driver.py`
- `/tmp/face_taxonomy/driver.log`

## State

`COMPLETED`.

Receipt fields:

| Field | Value |
|---|---:|
| `classification` | `scratch_diagnostic` |
| `all_pass` | `true` |
| `formal_admission_allowed` | `false` |
| `promotion_allowed` | `false` |
| `readout_response_rank` | `3` |
| `parity.within_1e_10` | `true` |
| `parity.parity_max_diff` | `3.3306690738754696e-16` |

Audit verdicts supplied for the completed run:

- Grok: `GENUINE`
- Gemini: `GENUINE`

The scratch-diagnostic fence remains load-bearing: this is a finite readout taxonomy, not a physics-admission result.

## Object

The finite object is one spinor-network substrate with multiple readouts:

- primitive carrier: finite spinor-network state `psi` over `(C^2)^5`;
- graph edges: `(0,1)`, `(1,2)`, `(2,3)`, `(3,4)`, `(0,4)`;
- Hilbert dimension: `32`;
- density `rho=|psi><psi|` and reduced densities `rho_A` are derived readout layers, not primitive state declarations.

This is the nominalist object: one substrate, many faces.

## Six Readouts

| Readout key | Face |
|---|---|
| `expansion_dark_energy_time` | expansion -> dark energy / time |
| `preserved_info_dark_matter` | preserved information -> dark matter |
| `bounded_knot_matter_mass` | bounded knot -> matter / mass |
| `composite_knot_baryons_hadrons` | composite knot -> baryons / hadrons |
| `transition_forces` | transition channels -> forces |
| `synchronization_gradient_gravity` | sync gradient -> gravity |

The six readouts are distinct probes, not relabeling of one scalar. The response-rank control reports `readout_response_rank=3` with minimum required rank `2`.

The decisive distinction control is `phase_twisted_flat`: it leaves `expansion_dark_energy_time` invariant at `0.9999999999999994`, while moving `preserved_info_dark_matter` to `0.21040208776627686` and `transition_forces` from `0.6436311970270981` to `0.642989410620971`.

## Readout Rows

| State | expansion / dark energy | preserved info / dark matter | knot / matter mass | composite knot / baryons | transition / forces | sync gradient / gravity |
|---|---:|---:|---:|---:|---:|---:|
| `flat_fuzz` | `0.9999999999999994` | `0.0` | `0.0` | `0.0` | `0.6436311970270981` | `0.0` |
| `phase_twisted_flat` | `0.9999999999999994` | `0.21040208776627686` | `0.0` | `0.0` | `0.642989410620971` | `0.0` |
| `single_knot` | `0.7999999999999999` | `0.19999999999999998` | `1.0` | `0.0` | `0.5000000000000002` | `1.0` |
| `composite_knot` | `0.7999999999999999` | `0.4` | `0.5` | `1.0` | `0.6603780215540438` | `0.5` |

## Controls

| Control | Completed result |
|---|---|
| distinct-probe rank | Pass: `readout_response_rank=3`, so the six readouts are not one scalar relabeled six times. |
| flat-fuzz vanish | Pass: `flat_fuzz` makes matter/mass, baryon/hadron, preserved-info/dark-matter, and sync-gradient/gravity readouts vanish while dark-energy/expansion stays maximal. |
| knot couples mass+gravity | Pass: `single_knot` turns on `bounded_knot_matter_mass=1.0` and `synchronization_gradient_gravity=1.0` together. |
| finite CPTP transition channels | Pass: transition readout uses a finite channel bank with `max_cptp_residual=0.0` in all tested states. |
| density-derived layer boundary | Pass: `rho` and `rho_A` are readout layers, not primitive carriers. |
| dual-backend parity | Pass: Julia mirror available; max backend difference is `3.3306690738754696e-16`, worst key `composite_knot.transition_forces`. |
| promotion fence | Pass: `classification=scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`. |

## Fence

The passing result supports:

- one finite carrier has six named readout maps;
- the readouts are distinguishable under finite perturbations;
- the `phase_twisted_flat` perturbation separates preserved-info/dark-matter and transition/forces from expansion/dark-energy;
- flat-fuzz and knot controls behave as specified;
- JAX/Julia parity holds to about `3.3e-16`.

It does not support:

- dark matter admission;
- dark energy admission;
- gravity admission;
- force unification admission;
- Axis0;
- M(C);
- PEPS3D;
- bridge;
- consciousness;
- final manifold closure.

## Next Hardening Step

Use this result only as a fenced scratch diagnostic for follow-up readout-taxonomy scouts, parity checks, or audit discussion. Any consumer that wants physics admission, bridge promotion, PEPS3D promotion, Axis0, or final manifold closure remains blocked and needs a separate admissible result.
