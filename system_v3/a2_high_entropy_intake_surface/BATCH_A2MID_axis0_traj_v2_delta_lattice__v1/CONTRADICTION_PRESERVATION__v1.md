# CONTRADICTION PRESERVATION

## Preserved Contradictions

1. Family relation vs missing runner anchor
- preserved:
  - the orphan clearly belongs near the trajectory-correlation family neighborhood
  - no direct `traj_corr_suite_v2` runner-name hit exists in current `simpy/`
- not collapsed into:
  - "there must be a current runner anchor somewhere" or "no runner anchor means no family relation"

2. Four-sequence family vs seq01-only absolutes
- preserved:
  - the file represents a four-sequence family
  - absolute values are stored only for `SEQ01`, with `SEQ02-04` encoded as deltas
- not collapsed into:
  - "missing absolute entries mean missing runs"

3. Visible metadata vs hidden lattice
- preserved:
  - top-level metadata shows only part of the lattice
  - key prefixes add a hidden `T1` / `T2` axis
- not collapsed into:
  - "the metadata exhausts the real axis count"

4. Trajectory resemblance vs contract nonidentity
- preserved:
  - the orphan resembles the earlier local trajectory-correlation family
  - the storage, lattice, gate, repetition, and scale contracts differ materially
- not collapsed into:
  - "this is simply a new serialization of the earlier local suite"

5. Catalog visibility vs descendant/evidence identity
- preserved:
  - the orphan is catalog-visible by filename alias
  - it is neither repo-top `V4` / `V5` nor evidence-pack admitted
- not collapsed into:
  - "catalog presence proves descendant continuity or maintained evidence status"

## Quarantine Rules

- quarantine reason: `no current runner anchor is not repaired by inference`
- quarantine reason: `delta encoding is not misread as absent sequence coverage`
- quarantine reason: `hidden T-axis is not dropped because metadata is thinner`
- quarantine reason: `the orphan is not merged into the earlier local suite`
- quarantine reason: `the orphan is not merged into repo-top descendants or treated as evidence-admitted`
