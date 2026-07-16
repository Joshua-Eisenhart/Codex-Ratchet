# Attractor-basin mathematics — actual state

This report makes the basin work visible as a distinct mathematical program. It preserves positive results, failed symmetries, and later repairs that refuted earlier claims.

## Probe-relative basin object

For a finite state set or finite sample grid \(X_B\), an ordered update schedule \(\sigma\), and a finite observation map \(q\), the executable object is not an assumed metaphysical basin. It is a finite equivalence relation on tested initial conditions:

\[
x\sim_{B,\sigma,q,\varepsilon}y
\quad\Longleftrightarrow\quad
d\!\left(q(F_\sigma^T x),q(F_\sigma^T y)\right)\le\varepsilon
\]

for the declared budget \(T\). The observed basin is an equivalence class or viability class of this relation. Changing \(q\), \(T\), \(\varepsilon\), schedule order, or the update rule changes the tested object. That is exactly why the controls and dwell audits are load-bearing.

When a finite entropy/information functional \(S\) is defined on the same observed coface, a drive witness is a measured contrast such as

\[
\Delta_\sigma S(x)=S(F_\sigma x)-S(x)
\]

or a relative-entropy/surprise descent. No nonzero gradient means no directed Ratchet tooth. A basin label alone does not provide that drive.

## Terrain and nested-basin result

`data_json/nested_basin_results.json` records eight finite terrain regions:

- Left engine: Funnel/Se, Vortex/Ne, Pit/Ni, Hill/Si.
- Right engine: Cannon/Se, Spiral/Ne, Source/Ni, Citadel/Si.

The finite kill test separates Ne/Ni point-attractor behavior from Se/Si bounded-viability behavior. Pit subbasins have minimum separation 0.445; Hill subbasins only 0.005. The rich fingerprint minimum distance is 0.043. Ordered noncommuting updates produce an order gap of 0.268, while the commuting control collapses it to \(1.96\times10^{-17}\). These are useful finite fingerprints, not proof that the eight named terrains are uniquely forced objects.

## Engine-pair basin map

The dedicated engine-pair map sampled 123 grid points for six cycles:

- Type1-left: one observed basin centered at \((0.00191,-0.00570,-0.00184)\).
- Type2-right: one observed basin centered at \((-0.03075,-0.00628,0.12132)\).
- Both loop-to-engine nesting checks held on this finite map.
- The proposed pair mirror relation failed: Hausdorff distance 0.12345 exceeded the 0.09 tolerance.
- Shuffling schedule order moved basin centers (Hausdorff shifts 0.64008 and 0.12599).
- Commuting-generator controls collapsed both centers to zero.

So schedule order and noncommutation are load-bearing for the observed locations, while the stronger mirror-isomorphism story is not supported.

## Belief basin: baseline, confound, and repaired carrier

The original belief-space probe reported terrain-keyed attractors and path dependence under finite dwell. That result demonstrates history sensitivity of the installed relaxation process, but it does not by itself distinguish a genuine multistable memory carrier from slow exponential lag.

The later memory-carrier audit supplied that missing control. It stores four orthogonal patterns and remains multistable even after a final dwell of ten measured carrier time constants (100 steps): histories ending in the same nominal final regime retain different winners with projective distance 0.99999997. Under the identical protocol, the linear exponential smoother collapses to path distance \(3.88\times10^{-6}\). Thus the finite memory-carrier construction passes a stronger multistability test; the earlier generic smoother-style hysteresis must not be promoted as the same result.

## FEP known/unknown audit chain — an explicit retraction

The first FEP basin script reported an engine allocation split. That split was not clean: it used hardcoded learning-rate constants keyed to loop-profile labels. The v2 script removed that hidden asymmetry:

- one shared update rule;
- one shared learning rate, 0.62;
- identical tick counts and initial-state protocol;
- engine schedules as the only engine-specific parameter.

The repaired result keeps the occupied-versus-transition basin partition: mean occupied surprise 0.001733 bits versus transition surprise 0.541726 bits, a gap of 0.539993 bits. But the engine allocation verdict becomes **no-split**, the shuffled-schedule control is also no-split, and the entropy-gradient initialization produces **no measured shift** under the declared threshold. The v1 allocation split is therefore refuted as evidence. This negative is part of the live basin state, not an embarrassment to hide.

## Seven-axis unified basin probe

`unified_attractor_basin_seven_axes_sim_results.json` treats one engine substrate as one finite running object and probes seven measurements with erasure controls. All seven were load-bearing in that battery, and its nested levels were distinguishable:

- L0 stage minimum pairwise separation 0.7086;
- L1 loop order gap 0.4418;
- L2 two-loop gap 1.6461;
- L3 Type1/Type2 Axis0 polarities -0.02052 and 0.01387.

This is a useful finite construction and a good integrative probe. Its own receipt correctly says it is not a proof of axis uniqueness, closure, or a canonical layer order.

## Current state by claim

| Claim | Current evidence state | Ratchet status |
|---|---|---|
| Eight terrain fingerprints | Finite reproducible partition/viability observations | Installed probe-relative map |
| Order and noncommutation move basin structure | Positive with shuffled and commuting controls | Load-bearing in declared fixtures |
| Type1/Type2 mirror-isomorphic basins | Failed tolerance | Rejected in that fixture |
| Generic relaxation hysteresis is genuine multistability | Confounded by finite lag | Qualified; do not promote |
| Four-pattern memory carrier is multistable | Survives 10× dwell; linear control collapses | Strong finite construction, still scratch |
| FEP occupied/transition surprise partition | Survives repaired v2 | Finite positive observation |
| FEP Type1/Type2 allocation split | v1 hidden-rate artifact; v2 no-split | Refuted as current evidence |
| Entropy initialization shifts allocation | v2 no measured shift | Negative/open |
| Seven axes are load-bearing | Finite erasure battery passes | Scratch diagnostic; uniqueness open |
| Basin ontology/order is canonical | Not tested globally and incompatible with strong nominalism | Not earned |

## What the next basin Ratchet must do

1. Generate multiple finite carrier/update families, not only parameter variants of one smoother.
2. Search schedule, probe, tolerance, dwell, and partition definitions as hypotheses.
3. Measure time constants before calling finite lag “hysteresis.”
4. Require same-rule/same-rate controls and schedule erasure.
5. Demand a nonzero entropy–geometry coface gradient for a tooth.
6. Compute packet-relative MSS fronts over behavioral equivalence classes.
7. Preserve no-split, collapsed, and reversed outcomes as evidence.
8. Keep every basin object provisional on the finite grammar and on not finding a weaker carrier.

## Primary evidence

- `data_json/nested_basin_results.json`
- `sims_and_scripts/engine_pair_basin_map_sim_results.json`
- `sims_and_scripts/belief_space_basin_map_sim_results.json`
- `sims_and_scripts/memory_carrier_belief_basin_sim_results.json`
- `sims_and_scripts/fep_known_unknown_basin_sim_results.json`
- `sims_and_scripts/fep_known_unknown_basin_v2_sim_results.json`
- `sims_and_scripts/unified_attractor_basin_seven_axes_sim_results.json`

Most dedicated basin probes were among the 46 unregistered scripts and were therefore omitted by the old generated inventory. Their registration state is now explicit in `reports/SIM_REGISTRATION_LEDGER.json`.

