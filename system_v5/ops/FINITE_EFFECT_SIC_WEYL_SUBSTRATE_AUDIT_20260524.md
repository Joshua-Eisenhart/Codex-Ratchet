# Finite Effect / SIC / Weyl Substrate Audit

Date: 2026-05-24

Status: formal scout result and next-candidate map. This is not canon and not a
final manifold foundation claim.

## Why This Layer Exists

The current repair direction is:

```text
root constraints
-> finite admissible effects/probes
-> probe-response state assignments
-> quotient identity under active probes
-> admitted carrier adapters
-> spinor/Hopf/Weyl geometry
-> engine/flux/Axis0 candidates
```

This fixes the old failure mode where the working carrier or picture became the
substrate. The root object in the new scout is not a sphere, axis picture, or
carrier matrix. The root object is:

```text
finite effect family E = {E_i}
state response p_i = observed/derived response to E_i
identity a ~_E b iff all active effects in E give the same response
```

Carrier matrices, older sphere pictures, and named low-dimensional generators
can still be useful, but only as adapters after the finite effect gate is
declared and tested.

## New Scout

Script:

```text
system_v5/ops/formal_scouts/sim_finite_effect_sic_weyl_substrate_admission_probe.py
```

Result:

```text
system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json
```

Fresh run:

```text
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/sim_finite_effect_sic_weyl_substrate_admission_probe.py
```

Outcome:

```text
all_pass = true
nearby_variants = 15 / 15
primary_substrate = finite_effect_povm_state_space
primary_concrete_probe = qubit_sic_povm
primary_operator_algebra = finite_weyl_heisenberg_shift_phase
secondary_candidate_passed = mub_finite_probe_family
```

Validation:

```text
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/validate_formal_scout_results.py system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json
```

Outcome:

```text
all_pass = true
errors = []
```

Lint:

```text
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_finite_effect_sic_weyl_substrate_admission_probe.py
```

Outcome:

```text
violation_total = 0
```

## Prior Source-Backed Alignment

There was already a v5 formal scout pointing in this direction:

```text
system_v5/ops/formal_scouts/sim_geometric_constraint_manifold_representation_alignment_probe.py
```

Fresh rerun status:

```text
all_pass = true
nearby_variants = 11 / 11
```

That older scout ranks the layer roles this way:

```text
SIC/POVM finite effect layer      score 14
Weyl-Heisenberg shift/phase layer score 12
admitted carrier layer            score 10
old sphere/axis chart             score 7
projective spinor-ray-only layer  score 6
```

Important caveat: that scout is an alignment/profile scout, not the new root
substrate gate. It still uses older adapter machinery inside the test fixture.
So it is useful source backing, but the stronger root-layer evidence is the new
finite effect/SIC/Weyl scout above.

I also patched that older scout's receipt schema so it now validates under the
current formal-scout validator:

```text
why_not_v4_probes present
nearby_variants present
validate_formal_scout_results.py = pass
lint_sim_contract.py = pass
```

## What Passed

| Gate | Result | Meaning |
|---|---:|---|
| finite SIC effect family | pass | four finite effects sum to identity and form an informationally complete probe family |
| SIC response assignment | pass | probe responses are finite, nonnegative, normalized, and reconstruct the carrier adapter |
| quotient identity | pass | one probe can merge two states that the complete active SIC separates |
| global phase quotient | pass | finite effect responses ignore irrelevant global phase |
| WH relation in d=2 | pass | finite shift/phase operators obey XZ = omega ZX with nonzero order gap |
| WH relation in d=3 | pass | noncommuting finite algebra is not just a qubit trick |
| WH orbit -> qubit SIC | pass | the d=2 SIC can be generated as a finite Weyl-Heisenberg orbit |
| MUB smoke test | pass | mutually unbiased finite probes are a viable secondary candidate family |
| z3 nonpromotion gate | pass | finite/noncommuting/nonpromotion constraints are mutually consistent |

## Graveyards That Failed Correctly

| Graveyard | Result | Why It Matters |
|---|---:|---|
| single probe identity | rejected | one finite effect is not enough to define identity |
| commuting operator family | rejected | commuting algebra has no order witness for N01 |
| one two-outcome basis | rejected | finite does not mean informationally complete |

The strongest numerical separation in the scout:

```text
single active probe gap = 0.0
full SIC assignment gap = 0.38611470092334943
```

That is the key operational point: equality is active-probe-family-relative.

## Effect Algebra Law Scout

The explorer audit caught a naming gap: the repo backed finite effects and
POVM/SIC completeness, but not the phrase "effect algebra" as a named law
surface. I added a separate law scout:

```text
system_v5/ops/formal_scouts/sim_finite_effect_algebra_laws_probe.py
```

Result:

```text
system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json
```

Fresh outcome:

```text
all_pass = true
finite_effect_count = 4
laws_tested = zero_unit, complement, bounded_partial_sum, coarse_graining, effect_order
carrier_role = bounded_probe_response_adapter_only
```

It tests:

| Law | Meaning |
|---|---|
| zero/unit | `0` and `I` are valid effects |
| complement | if `E` is an effect, `I - E` is its bounded complement |
| bounded partial sum | addition is admitted only when the sum remains an effect |
| coarse-graining | grouped effects remain a finite instrument and responses add |
| order | `E <= F` means `F - E` is an effect |

Graveyards:

| Graveyard | Why It Fails |
|---|---|
| arbitrary addition | effect algebra is not closed under arbitrary addition |
| negative effect | negative operator is not a valid finite effect |
| unlabeled response | a probability-like number without its named effect is not an admissible root object |

## Current Ranking

| Candidate | Score | Status | Next Gate |
|---|---:|---|---|
| finite effect / POVM state space | 10.0 | passed local substrate gate | integrate as root adapter contract |
| SIC-POVM probability simplex | 9.5 | passed local concrete carrier gate | run higher-d and engine-consumption tests |
| Weyl-Heisenberg shift/phase algebra | 9.0 | passed d=2 and d=3 order gate | replace Pauli-lego assumptions in engine rows |
| finite effect algebra laws | 8.8 | passed zero/unit/complement/partial-sum/coarse-grain/order law gate | make this prerequisite for using "effect algebra" language |
| MUB finite probe family | 8.4 | smoke test passed | add reconstruction and comparison against SIC |
| contextuality sheaf / presheaf events | 8.2 | not run | finite context/no-global-section witness |
| finite projective geometry / quantum designs | 8.0 | not run | incidence/design IC-probe construction |
| finite spectral triple / Dirac pair | 7.6 | not run | finite algebra/module/bounded-commutator separation |
| quantum comb / process POVM | 7.5 | not run | finite instrument-history state without primitive clock ontology |
| finite convex operational theory | 7.3 | not run | finite-generated state/effect dual cones |

## Doctrine Update Candidate

Use this wording as a proposal, not as admitted canon:

```text
The root geometry is finite operational distinguishability. A state is a
finite response assignment over an admitted effect family, and identity is
quotient identity under the active probes. SIC-POVM probabilities are the best
current concrete finite replacement for the old sphere adapter. Finite
Weyl-Heisenberg shift/phase relations are the best current replacement for
the old axis-generator adapter. Spinor/Hopf/Weyl geometry remains important,
but it enters after finite effect/probe admission.
```

Use "effect algebra" only when the law gate is in scope:

```text
zero/unit + complement + bounded partial sum + coarse-graining + order
```

## Immediate Next Work

1. Add a contextuality finite-event scout:

```text
finite measurement contexts -> no global section -> nonclassical effect
family that cannot be reduced to one classical sample space
```

2. Add a MUB/SIC comparison scout:

```text
SIC minimal IC family vs MUB overcomplete finite family
```

3. Add a process-POVM / quantum-comb scout:

```text
finite instrument history -> effect over histories -> QIT-FEP/Holodeck
without primitive hidden Markov ontology
```

4. Add an adapter quarantine scout:

```text
Axis0/flux/engine rows must consume finite probe-response assignments first.
Carrier matrices and old sphere/axis machinery may appear only as bounded
adapters or graveyard controls.
```
