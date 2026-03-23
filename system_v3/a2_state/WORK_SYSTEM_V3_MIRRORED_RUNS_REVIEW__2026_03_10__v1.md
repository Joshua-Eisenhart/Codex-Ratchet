# WORK_SYSTEM_V3_MIRRORED_RUNS_REVIEW__2026_03_10__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: narrower review of the mirrored run concentration inside `work/system_v3/runs`

## 1) Concentration read

Largest mirrored run entries:
- `93M` `WIGGLE_AUTO_001`
- `12M` `TEST_REFINED_050`
- `6.2M` `TEST_REFINED_001`
- `4.4M` `_CURRENT_STATE`

These account for essentially all meaningful size inside the shadow run tree.

## 2) Structural read

### `WIGGLE_AUTO_001`
- old heavy run surface
- contains:
  - `a1_strategies`
  - `events.jsonl`
  - `outbox`
  - many compile / B reports
  - `sim`
- matches the older thick-save/helper style, not the current lean run model

### `TEST_REFINED_050` and `TEST_REFINED_001`
- mirrored refined test runs
- contain:
  - `zip_packets`
  - `state.json`
  - `summary.json`
  - `reports`
  - `sim`
- these look closer to valid run evidence, but still inside the shadow `work/system_v3` tree rather than the live `system_v3/runs` owner path

## 3) Reference read

Live references found:
- `WIGGLE_AUTO_001` is explicitly cited in existing `a2_high_entropy_intake_surface` work-surface archaeology packets
- the mirrored run names also appear in the local cleanup notes already created during this maintenance sequence

No comparable active owner-path dependency was found that would make these shadow runs authoritative runtime state.

## 4) Decision

Decision: `CORRECT_LANE_LATER`

Meaning:
- these mirrored runs are correctly classified as shadow residue, not active owner surfaces
- but moving them now would break path continuity for existing archaeology/source-map references

## 5) Keep vs future target

### Keep in place for now
- `work/system_v3/runs/WIGGLE_AUTO_001`
- `work/system_v3/runs/TEST_REFINED_050`
- `work/system_v3/runs/TEST_REFINED_001`
- `work/system_v3/runs/_CURRENT_STATE`

### Future target, but only with a path-preserving strategy
- mirrored-run archive or relocation plan that preserves readable source anchors for existing archaeology packets

## 6) Maintenance conclusion

This review closes the local `work/system_v3` line for now.

The subtree is:
- semantically quarantined
- still readable as archaeology/reference
- not yet a safe direct filesystem-mutation target

That means the next higher-value action is no longer local mirror cleanup.
The next higher-value action is the prepared external entropy/Carnot/Szilard lane.
