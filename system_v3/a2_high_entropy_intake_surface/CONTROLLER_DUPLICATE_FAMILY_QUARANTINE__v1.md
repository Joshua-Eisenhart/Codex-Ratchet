# CONTROLLER_DUPLICATE_FAMILY_QUARANTINE__v1
Status: PROPOSED / NONCANONICAL / CONTROLLER DUPLICATE-FAMILY QUARANTINE
Date: 2026-03-09
Role: small controller routing packet for duplicate-family handling inside the intake surface

## 1) Quarantine Target
- duplicate-family batch:
  - `BATCH_a2feed_grok_unified_phuysics_source_map__v1`
- corrected sibling already present:
  - `BATCH_a2feed_grok_unified_physics_source_map__v1`
- corrected sibling direct child already present:
  - `BATCH_A2MID_grok_unified_admission_conflicts__v1`

## 2) Source-Bound Match Facts
- both source-map parents point to the same underlying source file:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a2_feed_high entropy doc/grok unified phuysics nov 29th.txt`
- both parents record the same source hash:
  - `0389cf9353e87f38d48241a1421e68bbffce41789715d71d205be5ae5608aabe`
- both parents record the same source size and line count:
  - `407166` bytes
  - `6599` lines
- both parents are `SOURCE_MAP_PASS` surfaces and both remain `REVISIT_REQUIRED`

## 3) Why This Stays Quarantine-Side
- the typo variant does not expose a distinct source-bearing delta at the manifest layer
- the corrected sibling already has the narrower child packet that captures the reusable admission-conflict seams
- creating a fresh controller reduction from the typo variant would duplicate family work rather than expose a new bounded gap

## 4) Controller Rule
- preferred live family handle for routing:
  - `BATCH_a2feed_grok_unified_physics_source_map__v1`
- quarantine-side duplicate pointer:
  - `BATCH_a2feed_grok_unified_phuysics_source_map__v1`
- allowed controller use:
  - keep the typo variant visible as duplicate-family residue
  - preserve the existence of the typo spelling and later duplicate intake event
  - route any further narrowed reasoning through the corrected sibling and its existing child packet
- blocked controller move:
  - do not reduce the typo variant as if it were a fresh unresolved doctrine parent

## 5) Non-Destructive Boundary
- this packet does not delete, archive, or demote either batch
- this packet only assigns routing posture:
  - corrected sibling is the active queue handle
  - typo variant remains explicit duplicate-family quarantine until a later explicit dedup or archive instruction

## 6) Duplicate-Child Coverage
- shared parent:
  - `BATCH_archive_surface_deep_archive_v2_zipv2_packet_req_001__v1`
- preferred live child handle:
  - `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
- overlapping later child:
  - `BATCH_A2MID_archive_v2_packet_req_request_only_handoff__v1`
- why this stays quarantine-side:
  - both children point at the same parent and preserve the same request-only save-handoff contradiction surface
  - both children use the same comparison-anchor pair and no distinct new source-bearing delta separates them
  - the later child is therefore duplicate-child residue rather than a fresh unresolved controller gap
- controller rule:
  - route further controller-facing use through `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
  - keep `BATCH_A2MID_archive_v2_packet_req_request_only_handoff__v1` visible as overlapping duplicate-child residue
  - do not launch a third reduction from the same parent as if the request-only ZIPv2 packet were still unresolved
