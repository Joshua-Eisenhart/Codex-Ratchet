# A2_HIGH_MASS_PROCESSING_TRIAGE__2026_03_11__v1

Status: DRAFT / NONCANON / A2 TRIAGE OUTPUT
Date: 2026-03-11
Role: bounded family-level triage for the `a2_high_entropy_intake_surface`

## 1) Why this pass exists

The intake surface is not large by bytes (`16M`), but it is large by batch count:
- current visible batch directories: `444`

So the correct problem is:
- not generic size cleanup
- but mass-processing / queueing / routing

## 2) Family counts

- `201` `BATCH_A2MID*`
- `72` `BATCH_refinedfuel*`
- `51` `BATCH_archive_surface*`
- `41` `BATCH_sims*`
- `34` `BATCH_systemv3*`
- `15` `BATCH_a2feed*`
- `13` `BATCH_work_surface*`
- `11` other `BATCH_*`
- `6` `BATCH_upgrade_docs*`

Operational read:
- the surface is already dominated by reduced children (`A2MID`)
- the remaining mass-processing problem is not “reduce everything blindly”
- it is “route the remaining non-A2MID families in the right order”

## 3) Current routing signal

Existing controller surfaces already say:
- no live unreduced non-`A2MID` `A2_2_CANDIDATE` broad-parent packet remains as the immediate default queue
- revisit-side routing is now the active mode

Relevant surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/CONTROLLER_QUEUE_INTEGRITY_AUDIT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/CONTROLLER_REENTRY_SHORTLIST__v1.md`

## 4) Triage classes

### Class A: already reduction-dominant
- `BATCH_A2MID*`

Action:
- do not mass-process as if unreduced
- use only for targeted controller-fence follow-ons or selective promotion

### Class B: strongest remaining revisit/routing fuel
- `BATCH_refinedfuel*`
- especially constraint / entropy / admissibility / contract families

Action:
- treat as the highest-value internal mass-processing lane
- process by paired revisit routing, not by flat alphabetical sweep

### Class C: archive-side revisit and lineage packets
- `BATCH_archive_surface*`

Action:
- keep bounded
- use for archive-policy, lineage, heat-dump/root-family routing
- do not let archive-side work consume the whole controller loop

### Class D: method / support / archaeology packets
- `BATCH_work_surface*`
- `BATCH_upgrade_docs*`
- some `BATCH_a2feed*`

Action:
- use for controller/process repair and source archaeology
- do not treat as first-choice doctrine lanes

### Class E: active live system packets
- `BATCH_systemv3*`

Action:
- use only for active system integration / drift refresh / state packet follow-ons

## 5) Exact next internal A2-high go-ons

The next valid internal A2-high thread-actions are:

1. `REFINEDFUEL_REVISIT_ROUTING_PASS`
- focus on the `BATCH_refinedfuel*` family only
- produce a family queue:
  - `run now`
  - `hold`
  - `archive-side only`

2. `ARCHIVE_SURFACE_HEAT_DUMP_ROUTING_PASS`
- focus on the `BATCH_archive_surface*` family only
- continue the heat-dumps/root-family split line

3. `A2MID_CONTROLLER_FENCE_FOLLOWON_PASS`
- target only explicitly high-signal A2MID/controller-boundary children
- do not reopen broad parents

## 6) Decision

Decision: `MASS_PROCESS_BY_FAMILY_NOT_BY_GLOBAL_SWEEP`

Meaning:
- there is a real thread-action left here
- but it should be:
  - family-bounded
  - queue-driven
  - revisit-first
- not “process the whole intake surface”

## 7) Best next internal A2-high go-on

Best next internal thread-action:

`REFINEDFUEL_REVISIT_ROUTING_PASS`

Reason:
- `refinedfuel` is the largest remaining non-A2MID unresolved family (`72`)
- it is closer to current active conceptual/refinery work than archive-only families
- current queue/reentry surfaces already point toward revisit routing rather than fresh broad-parent reduction
