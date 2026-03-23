# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_mutation_snapshot_overhang__v1`
Date: 2026-03-09

## Preserved Contradictions
- contradiction 1:
  - the run preserves one executed mutation event row only
  - summary/state bind final closure above that sole event endpoint
- contradiction 2:
  - summary and soak report keep zero parked packets and zero rejects
  - final state still keeps two `PARKED` promotion states and two unresolved blockers
- contradiction 3:
  - the Thread-S snapshot keeps both retained specs under `EVIDENCE_PENDING`
  - final state keeps `evidence_pending` empty
- contradiction 4:
  - export and snapshot both keep `KILL_IF ... NEG_NEG_BOUNDARY` lines
  - final state keeps `kill_log` empty and retained SIM evidence does not carry explicit kill-signal lines
- contradiction 5:
  - the root keeps exact duplicate ` 2` run-core files and empty residue directories
  - those artifacts do not become a second execution lane
- contradiction 6:
  - archived event rows still point to live-runtime packet paths
  - the retained packet bodies now live under the archive mirror

## Preservation Rule
- this batch keeps all contradictions above intact
- none of them are resolved into a clean one-step closure story, a clean promotion-complete story, or a clean packaging story
