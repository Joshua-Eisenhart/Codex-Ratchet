# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent Batch
- `BATCH_archive_surface_deep_archive_test_a1_packet_empty__v1` is the first untouched deep-archive test parent in this ledger strip
- it is worth reducing because it captures the thinnest handoff-failure pattern in the archive family:
  - request emitted
  - no downstream A1 receipt
  - no execution progress
  - one concrete but provenance-weak A0 save packet

## Bounded Goal
- preserve the smallest reusable archive packet from this family:
  - archive-only boundary-run classification
  - clean one-hash alignment without semantic overread
  - request-only structure versus absent response
  - saved strategy skeleton without earned downstream work
  - seed vocabulary without live registries
  - packaging noise kept as noise
- remove redundant inventory detail from the parent batch
- keep the object below:
  - active runtime truth
  - active handoff doctrine
  - any claim of successful A1 packet ingress

## Why This Stays A2-2 Candidate Side
- the packet is reusable, but only as:
  - archive process lineage
  - handoff-failure pattern preservation
  - contradiction-side reference
- it does not authorize:
  - active runtime inference
  - promotion of placeholder hashes into trusted provenance
  - treating the saved packet as executed downstream work

## Deferred Alternatives
- `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1`
  - next strongest sibling because it moves from packet-absence to packet-presence contradictions
- `BATCH_archive_surface_deep_archive_test_det_b__v1`
  - later direct-run comparison once the packet pair is reduced

## Expected Value Of This Pass
- preserve the archive family’s cleanest zero-progress handoff stub without carrying the full source inventory
- keep the contradiction markers visible for later sibling comparison
