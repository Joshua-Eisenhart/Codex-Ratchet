# Claude Science 94/95 Engine-State Audit

**Date:** 2026-07-09  
**Status:** bounded external-packet intake plus fresh local probes  
**Classification:** audit receipt; not engine admission  
**Promotion allowed:** false

## Packet Identity And Ceiling

| Packet | SHA-256 | Members | Intake result |
|---|---|---:|---|
| `/Users/joshuaeisenhart/Desktop/94.zip` | `476cb9181e3a32c71e4d2d1538832c80c6a065033fe68778a519b32e53a05783` | 453 | integrity-valid external evidence |
| `/Users/joshuaeisenhart/Desktop/95.zip` | `1bf786835b659e132930e0673178a9d8756308ff4bfbe7d8e6f9940f9507ad98` | 453 | integrity-valid; supersedes 94; passes isolated local rerun |

Both archives pass CRC and path-safety inspection. Neither archive contains a
packaged `run_all_report.json`, so the prose claim `133 GREEN` is not an
admissible run receipt. Packet 94 is packet 92 plus three changed control files
and six added files. Packet 95 carries the same three new source/result pairs
and later control-text corrections. The engine sources inspected below are
byte-identical to the active repo copies.

The new packet material is useful but bounded:

- the Penrose/E8 scout constructs a finite aperiodic diagnostic but does not
  force that structure into the engine;
- the L7 scout has finite Berry curvature and holonomy, but no derivation of
  the older `+2*pi*Delta r` claim;
- the L8 scout constructs a near-unit Chern number for an installed spinor
  family, while its trivial control is assigned and no engine data binds Chern
  sign to Type-1/Type-2 chirality.

## The Three Different Stage Namespaces

Current artifacts use the phrase `16 stages` for different finite objects.
They must not be pooled.

1. **Source slots:** two engines, two loops per engine, four ordered rows per
   loop. These are 16 chart positions carrying terrain, source-canonical
   operator, and Axis-6 precedence metadata.
2. **Proxy fingerprints:** eight terrains crossed with one of two selected or
   native operators. The fresh `16/16` affine re-identification result belongs
   here. It is not re-identification of the 16 signed source slots.
3. **Candidate 16 x 4 expansion:** eight terrains crossed with two precedence
   signs gives 16 macro channels; a candidate pool can contain four exact
   operators at the same sign, giving 64 possible transitions. Only 16 of
   those 64 rows are source-canonical under the older chart. The other 48 are
   an architecture hypothesis, not a result.

This distinction controls every uniqueness, necessity, personality, and
objecthood claim.

## Fresh Isolated 95 Rerun

After archive inspection, packet 95 was extracted to an isolated `/tmp`
directory and run with the sim-stack Python 3.13.6 interpreter. No packet code
was run inside a live repo checkout.

```text
133 pass / 0 fail / 0 skip -> GREEN
1q: NumPy oracle vs JAX + PyTorch + Julia GREEN
3q: NumPy oracle vs JAX + PyTorch + Julia GREEN
```

Harness SHA-256:
`bfbb4a407a6ee854f046b3bfdc5cf7b98b41b6cd470bdf3652f869f6b7d622a2`.

Fresh `run_all_report.json` SHA-256:
`40f5f2068be42cfd5fb0d519589dabbf69c652975c11283535e4283869df98a6`.

Durable local receipt:
`/Users/joshuaeisenhart/Desktop/95-local-rerun-20260709/`.

This upgrades the packet from `exists` to `passes local rerun`. It does not
override per-sim negative results, contract lint, fabrication audit, or
`scratch_diagnostic` / `promotion_allowed=false` ceilings.

The broad green is not fully dependency-closed. Packet `run_all.py` executes
`v7_codex_ratchet_crosscheck_sim.py` before it regenerates the
`engine_reidentification_objective_sim_results.json` file that the crosscheck
reads. The packet-held result masks this ordering defect. A flattened wiki
mirror with no pre-existing result fails the crosscheck as `result file
absent`; running the re-identification producer first and then the crosscheck
passes with fresh `16/16`, separation `0.9271875`, and zero degenerate pairs.
This is a harness-order defect, not an engine-math regression. It must be fixed
before calling the full runner clean-checkout self-contained.

## What Actually Runs

### Source and expansion structure

`schedule_source_fidelity_linter.py` passes its bounded contract:

- 16 source slots parse;
- the owner-requested expansion has exactly 64 rows;
- every macro channel has all four operators at one shared sign;
- the 16 source-canonical rows reconstruct the older chart;
- a corruption control is rejected.

This proves table shape and consumer agreement, not dynamics.

### Independent 64-channel fingerprints

`engine_64_schedule_definition_sim.py` applies all four exact operator maps at
each of the 16 terrain/sign channels. Under its selected flow parameters and
six-probe battery it reports:

- `64/64` distinct finite channel signatures;
- minimum pairwise distance `0.1086`;
- up/down separation for `32/32` terrain/operator pairs;
- `0/32` separation under the no-drive control;
- collapse to 16 under a single-operator control.

This is real finite order sensitivity in a hard-coded candidate pool. Each row
is nevertheless run independently from the probes. It does not implement a
four-beat sequential interior for each macro stage, and it remains
`scratch_diagnostic` with `promotion_allowed=false`. It cannot establish that
four substages emerged from the dual ratchet.

### UP-130 disposition after packet 97

Packet 97 supplied the source and passed a fresh isolated `135/0/0` runner,
but a source-locked local falsifier rejects its derivation. Its maps are
commuting entropy-preserving Bloch half-turns; its count predicate already
fixes length four; its controls are confounded; and `ABAB/BABA` are one cyclic
orbit. See `CLAUDE_SCIENCE_97_UP129_UP130_AUDIT_20260709.md` and
`four_substages_up130_fabrication_audit_sim.py`.

A separate Julia/JAX scout now supports only a conditional replacement: the
source's `x/z` Pauli/Bloch operator axes crossed with its pinching/unitary
family split form four cells and one MSS square cycle modulo reversal. That
does not yet bind the four cells into each macro stage or prove sequential
engine dynamics.

### Sequential four-beat interior

`sixteen_intelligences_substages_terrain_ratchet_sim.py` does run four ordered,
state-changing beats and distinguishes 16 hand-selected terrain/operator
fingerprints. Its substage function does not carry the source slot's Axis-6
sign and does not compose terrain-first versus operator-first maps. Instead it
applies an installed unitary casing around each substage operator after one
terrain flow. Its claimed fixed Axis-6 interior is therefore not implemented.

The result supports a sequential four-beat candidate. It does not establish
the requested same-sign four-operator stage, 16 intelligence families, or
personality.

### Type-1, Type-2, and four loops

Fresh active-repo copies of the full Type-1 and Type-2 scripts both pass their
own finite gates:

- each engine has two ordered four-row loops;
- Type-1 loop-order gap is about `0.5819`, with commuting control `0`;
- Type-2 loop-order gap is about `0.5012`, with commuting control `0`;
- both loop schedules are finite, noncollapsed, and order-sensitive.

The schedule labels install opposite sheet couplings by construction. The
measured dynamical correlations are only partially separated, and the
stranger-seed Type-2 content-equivalence criterion previously failed. Four
loop schedules therefore run, but two unique bidirectional scientific methods
with stable complementary intelligence are not yet earned.

## What Is Not Valid Yet

- `stage_necessity_ablation_sim.py` has only 10 nondegenerate stages and six
  expected-null or degenerate stages. It cannot support `all 16 stages are
  necessary`.
- `substage_architecture_discriminator_sim.py` leaves both the four-operator
  and four-loop-terrain candidates alive. Its candidates are not cardinality
  matched, and 64-position uniqueness remains open.
- `engine_64_schedule_sim.py` supports 16/16 matched-content order carrying
  after an order-blind collapse to 11 buckets. Its earlier 64-position
  uniqueness interpretation was withdrawn. This does not invalidate the
  separate six-probe channel distinction in
  `engine_64_schedule_definition_sim.py`.
- The current contract linter reports 18 process violations over the six
  inspected engine sims: each lacks required classification, manifest, and
  depth fields. None is canonical by process.
- Current task-family controls find no load-bearing engine task family, and
  slot-level operator sensitivity is asymmetric across signs. Distinct maps
  are not yet distinct kinds of useful thinking.
- Axis0 alignment, personality, perception, object formation, MMM authority,
  ontology authority, and mesh mutation do not follow from these finite
  signatures.
- One packet/live result family is environment-sensitive:
  `engine_dynamics_id_arbiter_sim_results.json` changes from a packaged
  `R^2=0.856551` to a current local `R^2=-42.546185`, propagating into object
  formation loss. PySINDy and the numerical environment must be pinned before
  this family is cited.

## The Math That Can Support The Requested Stage

Let `T_tau` be the CPTP terrain flow for terrain `tau`, and let `O_k` be one of
the four exact operator channels `Ti`, `Te`, `Fi`, or `Fe`. Define one Axis-6
precedence sign consistently across a macro stage:

```text
Phi_up(tau,k)   = T_tau compose O_k
Phi_down(tau,k) = O_k compose T_tau
```

Both maps are CPTP because a composition of CPTP maps is CPTP. For an explicit
four-operator order `pi`, a coherent four-beat macro stage is

```text
M(tau,s,pi)
  = Phi_s(tau,pi_4) compose Phi_s(tau,pi_3)
    compose Phi_s(tau,pi_2) compose Phi_s(tau,pi_1).
```

This establishes mathematical legality for a candidate, not architectural
necessity or emergence. Proper dual ratcheting must determine the survivor
maps. The evidence must determine whether four equivalence classes survive
independently on the geometry and entropy ratchets, whether one order is
canonical, and whether the 48 extension rows add useful computation rather
than decorative distinctions.

Axis-6 token precedence, left/right action side, and closure orientation are
related source concepts but are not automatically the same mathematical
operation. A passing sim must name which one it implements and test any claimed
equivalence.

## Required Dual-Ratchet Experiment

The conditional product-square prerequisite now passes independently in Julia
and JAX. The remaining experiment begins at the unearned bridge from that
four-cell graph into each source macro stage.

Build `engine_dual_ratchet_substage_emergence_v0` as one source-derived
experiment:

1. Parse the 16 source slots without a second hand-coded schedule, but do not
   inject a four-substage count into the admission rule.
2. Generate a declared superset of admissible terrain/operator/order/side
   candidates for each slot, including eliminable controls.
3. Run an independent geometry ratchet: source-faithful quotient
   distinguishability, noncommutation/order sensitivity, CPTP validity,
   nuisance-invariant fingerprints, and closure controls.
4. Run an independent entropy ratchet: Umegaki/BKM monotonicity, fixed-point
   behavior, entropy-kind separation, gradient direction, and wrong-pawl
   controls.
5. Intersect the two survivor ledgers only after each has run. Require the same
   four minimal equivalence classes to survive under `E_then_G` and `G_then_E`,
   across seeds and candidate enumeration order. Four must be an output, not an
   input.
6. Only then compose survivors sequentially with one inherited Axis-6 sign per
   macro stage, and record exact superoperator or Choi fingerprints.
7. Run forward/reverse, one-survivor removal, duplicate-survivor, sign-flip,
   terrain-identity, native-only, non-native, and order-erasure controls.
8. Compare both engines and all four loops under matched information and
   compute budgets, then add held-out task and object outcomes.
9. Emit the required classification, authority manifest, depth record,
   source/result hashes, environment lock, and negative results.

### Pass ceiling

If those gates pass, the project may claim that proper dual ratcheting emits
four load-bearing, same-sign sequential substage classes for each of 16
source-bound macro channels and arranges them into two finite loop charts. It
still may not claim 64 intelligences, personality, perception, Axis0, or
ontology authority without their separate discriminators.

### Kill or demotion rules

- If beat removal, permutation, or sign controls do not degrade held-out work,
  demote the four-beat interior to installed schedule decoration.
- If a simpler entity-resolution or bag-of-fields baseline matches the engine
  on object tasks, retain the channels as finite transforms and withdraw the
  perception claim.
- If Type-1/Type-2 differences vanish under matched budgets, retain one engine
  implementation and demote the two-type interpretation.
- If results drift across a pinned clean environment, stop promotion and repair
  reproducibility before adding new theory.
