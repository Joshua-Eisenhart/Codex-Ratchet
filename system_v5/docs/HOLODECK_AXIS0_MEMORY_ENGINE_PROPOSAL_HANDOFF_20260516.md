# Holodeck / Axis0 / Memory / Engine Proposal Handoff

Date: 2026-05-16
Status: proposal_admitted
Promotion allowed: false

This note saves the current proposal-space understanding after local doc reads
plus Grok, Gemini, Sonnet, and Opus audit passes. It is a guide for QIT engine
engineering, not canonical doctrine.

## Route Truth

- Native Codex subagent fanout was attempted for three doc-audit lanes and
  blocked by the current agent thread limit.
- Grok and Gemini provider receipts completed:
  - `system_v5/ops/formal_scouts/provider_receipts/20260516T224852Z_grok_xai_holodeck_axis0_memory_provider_audit.json`
  - `system_v5/ops/formal_scouts/provider_receipts/20260516T224852Z_gemini_holodeck_axis0_memory_provider_audit.json`
- Sonnet-high external worker fanout completed 4 of 6 lanes; 2 timed out.
  Receipt:
  - `work/tmp/holodeck_axis0_memory_audit_sonnet/20260516T224722Z-holodeck-axis0-memory-audit-sonnet/fanout_receipt.json`
- The two timed-out Sonnet lanes were rerouted with narrower prompts and both
  completed.
  Receipt:
  - `work/tmp/holodeck_axis0_memory_reroute_sonnet/20260516T225306Z-holodeck-axis0-memory-reroute-sonnet/fanout_receipt.json`
- Opus arbitration completed:
  - `/tmp/codex_claude_bridge/20260516T225428Z-codex-ratchet-opus-arbitration-do-not-edit-files-9e13cf847084.receipt.json`

All provider and Claude outputs are proposal/audit evidence only. They do not
promote any sim, axis, engine, Holodeck, FEP, IGT, psychology, physics, or
consciousness claim.

## Primary Local Anchors

- Holodeck docs: `READ ONLY Legacy core_docs/ultra high entropy docs/txt/holodeck docs.md.txt`
  - Lines 38-48: owner memory model; predictive model plus hashes; context
    triggers and chain recall; sim/game world as recall space.
  - Lines 168-179: NetHack/ASCII recall-space framing, semantic hashes,
    confirmation vs recall, embedded loop.
  - Lines 287-329: semantic hashes as vectors, hash sea, chain recall,
    persistent triggers, ASCII/NetHack memory compression.
  - Line 3043: `predict -> project -> sense -> error-correct/hash -> update model -> repeat`.
- `system_v5/docs/CONSTRAINT_SURFACE_AND_PROCESS.md`
  - Prediction-first FEP alignment: candidate as prediction, constraint chain
    as sensory error-correction, survivor as updated prediction, re-entry as
    next cycle.
- `system_v5/docs/AXIS_AND_ENTROPY_REFERENCE.md`
  - Axis 0 is active/open.
  - `Omega_r` is admissible refinement set.
  - `rho_present = C({rho_omega}_{omega in Omega_r})` is compression of
    future possibilities.
  - Axis0 is still open at bridge-and-cut level.
- `system_v5/docs/OWNER_THESIS_AND_COSMOLOGY.md`
  - Many possible futures create the present as admissible-refinement
    constraint, not classical future-to-past signaling.
  - FEP is intended as a literal physics mirror: prediction first, senses
    error-correct.
- `system_v5/READ ONLY Reference Docs/Older Legacy/MODEL_CONTEXT copy.md`
  - FEP should be derived from the constraint surface, not applied as
    classical probability.
  - QIT constraint manifold -> engine stages -> evolutionary strategies ->
    perception modes -> base emotions.

## Corrected Architecture

Holodeck memory is not stored replay.

The current model is:

```text
predictive world model + semantic/vector hashes + contextual trigger chains
```

Recall is not lookup. Recall is a boot process:

```text
current sensory/context trigger
-> activates partial hash/context lattice
-> predictive model generates candidate reconstruction
-> hash confirms or rejects the reconstruction
-> confirmed hashes activate linked hashes
-> context chain floods back
-> stable world/self/time context returns
```

Confirmation is fast because it is a match operation against a generated
candidate. Recall is hard because the predictive model must first generate a
candidate worth confirming.

## ASCII / NetHack World

The ASCII world is not the memory and not the world model.

It is a durable trigger lattice:

```text
ASCII glyph -> addressable context handle -> semantic/vector hash key
```

Every glyph/tile/object/person may carry a vector hash or chain of hashes:

```text
glyph: "T"
role: table-like handle
hash: model-relative semantic/vector confirmation key
links: room, event, person, affordance, graveyard exclusions
model_id: predictive model that can expand/confirm this hash
```

Without the correct predictive model, the hash-lattice is opaque. A saved
ASCII/hash world without its model is not a readable memory; it is random-looking
information relative to the wrong decoder.

## Graveyard As Memory

The graveyard is not an archive outside memory. It is negative memory.

```text
survivor hash = projection confirmed under probe family M
graveyard hash = projection killed under probe family M
```

Both are model-relative and probe-relative. A graveyard hash is an anti-hash:
it suppresses, penalizes, or excludes reconstructions that previously failed a
named constraint/probe. It prevents repeated hallucination and preserves the
value of losing.

Do not let graveyard become a static archive. It must participate in active
recall:

```text
trigger -> candidate reconstruction -> positive hash match
        -> negative hash filter -> survivor context or killed reconstruction
```

## Engines Run The Science Method Internally

The science method is not only a controller method around the engines. Each of
the two QIT engines must be able to run a full science-method loop internally.

Generic engine loop:

```text
1. predict candidate futures / reconstructions
2. project through the engine/Holodeck surface
3. sense or probe the result
4. compute residual / error / constraint failure
5. emit survivor hash or graveyard hash
6. update/reweight the predictive context
7. re-enter the next stage with the new context
```

The two engines must keep separate probe families and emission provenance:

```text
engine_id
probe_family M_E
constraints active at emission
stage token / operator / terrain
hash polarity: survivor or graveyard
residual that earned the polarity
trigger-chain edges that fired
```

Do not fuse the two engines into one generic FEP loop. Fusion is allowed only
at a declared compositor/boundary, not inside the engine-stage functions.

## Axis0 Constraint

Axis0 must not collapse to the easiest scalar.

Required preserved structure:

```text
Omega_r: admissible future/refinement set
C: compositor/compression over many admissible futures
rho_present: compressed present state
signed polarity: allostatic/homeostatic, positive/negative feedback
```

Axis0 cannot be:

- unsigned entropy alone;
- scalar reward;
- single argmax future;
- generic "minimize F" objective;
- Axis1/Axis2 terrain-stage basis;
- classical prior in a Bayesian model.

Axis0 can be used here only as proposal-grade guidance until a receipt-bound
sim shows many-futures preservation plus signed feedback polarity.

## Stage-Power Preservation Rules

The main engineering risk is stage collapse: unique engine stages becoming
generic scalar/readout functions.

Guardrails:

1. Each stage must have a replacement test. If a generic Lindblad/operator with
   similar spectrum can replace the stage without breaking a named constraint,
   the stage is decorative.
2. Each stage must emit a different survivor/graveyard profile under the same
   probe family.
3. Axis0 sign flips must matter. If sign flips do not change admissibility,
   Axis0 is overlay, not constraint.
4. FEP/Holodeck language must produce exclusions. If it never kills a candidate
   stage or reconstruction, it is not load-bearing.
5. IGT/losing value must be encoded as durable graveyard hashes, not prose.
6. Engine identity must remain attached to hash emissions.

## Anti-Teleology / Nominalism Guardrails

Use:

```text
survived under probe family M
admitted by constraint C
excluded by graveyard hash H-
co-varies under observable O
```

Avoid:

```text
seeks
wants
drives toward
causes the future
optimizes as primitive
converges by destiny
```

Objects are not primitives. A table, person, wall, engine stage, or memory is
what survives reconstruction and confirmation under the active model, context,
constraints, and probes.

## Premortem Findings

Most likely failure:

The Holodeck/FEP/Axis0 language motivates the engine work, but no sim makes it
load-bearing. Stage labels then drift into narrative roles. Generic operators
replace specific stages without changing observables. The engines still run,
but their unique stage power is lost.

Early warning signs:

- Axis0 reported only as unsigned entropy or scalar reward.
- A stage can be replaced by a generic operator without an UNSAT/failure.
- Holodeck hashes are treated as stored content rather than confirmation keys.
- Graveyard entries are written but not used in next-cycle reconstruction.
- FEP language has no candidate-killing effect.

## First Receipt-Bound Probes

### 1. `sim_engine_fep_loop_closure_classical.py`

Purpose: prove a finite engine can close the internal science-method loop.

Loop:

```text
predict -> project -> sense/probe -> residual -> survivor/graveyard hash -> re-enter
```

Acceptance:

- non-empty survivor and graveyard hash sets;
- per-step probe id and residual recorded;
- no scalar reward used as hidden objective;
- `classification = tool_lego_fit_probe`;
- `promotion_allowed = false`.

Kill:

- loop needs external controller intervention;
- no graveyard hash is produced;
- survivor/graveyard polarity cannot be reproduced.

### 2. `sim_holodeck_hash_recall_under_probe_swap.py`

Purpose: test model-relative hash opacity.

Design:

- emit hashes under probe family `M1`;
- attempt recall under `M2`;
- success allowed only if `M2` refines or equals `M1` quotient.

Acceptance:

- recall succeeds under matching/refining model/probe;
- recall fails or is UNSAT under incompatible probe;
- hash alone does not decode stored content.

Kill:

- hashes are invertible without the predictive model;
- wrong model/probe recalls equally well.

### 3. `sim_axis0_compositor_many_futures_preservation.py`

Purpose: prevent Axis0 scalar collapse.

Design:

- feed compositor `C` a set `{rho_omega}` with `|Omega| > 1`;
- include mixed survivor/graveyard polarity;
- compare against scalar-entropy and argmax controls.

Acceptance:

- compositor preserves more than one admissible future when required;
- signed polarity survives the compression;
- scalar/argmax control fails.

Kill:

- all useful behavior comes from scalar entropy or argmax;
- polarity is lost without changing result.

## Secondary Probe Ideas

- `sim_nethack_hash_graveyard_gate_v0`
  - test whether ASCII frames admit a live/graveyard partition a selector can
    exploit.
- `sim_stage_replacement_unsat_probe.py`
  - test whether generic replacement of a stage breaks a structural constraint.
- `sim_engine_stage_hash_profile_non_equivalence.py`
  - test whether each stage emits a distinguishable survivor/graveyard profile.

## Boundary Text

This architecture is proposal_admitted under a provisional probe family. It is
`exists` as a written candidate. It is not `runs`, not `passes local rerun`, and
not `canonical by process`.

It may guide QIT engine engineering anti-teleologically by naming what must not
collapse:

- many futures;
- signed Axis0 polarity;
- per-engine probe closure;
- survivor/negative memory;
- trigger-chain recall;
- stage-specific exclusions.

No hash schema, ASCII lattice, compositor `C`, Axis0 interpretation, FEP loop,
or engine-stage function is canonical until receipt-bound sims pass local rerun
and survive audit.

## Adopted / Not Adopted From Workers

Adopted:

- Holodeck memory as predictive reconstruction plus confirmation hashes.
- ASCII/NetHack as trigger lattice, not memory.
- Graveyard as active negative memory.
- Axis0 scalar-collapse guard.
- Three micro-first probes above.

Not adopted:

- Treating the two current QIT engines as Carnot/Szilard engines. A rerouted
  Sonnet lane used this as an analogy, but it is not the current engine identity.
  The current two-engine reading must stay attached to the repo's QIT/chiral
  engine surfaces unless a separate proposal explicitly changes that.
