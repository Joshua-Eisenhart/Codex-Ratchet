# A2 FUEL: GRAVEYARD ARCHITECTURE
**STATUS:** A2 HIGH-ENTROPY FUEL — SOURCE-BEARING EXTRACT

## Graveyard Schema (Two Levels)

### Thread B Rejection Contract (RQ-028, RQ-060..064)
MANDATORY: candidate_id, reason_tag, raw_lines, failure_class (B_KILL or SIM_KILL), target_ref

### Full SIM/Cluster Schema (GRAVEYARD_CLUSTER_PROTOCOL_v1)
MANDATORY: STRUCTURE_ID, SIM_ID, SIM_TIER, BRANCH_TRACK, MUTATION_OPERATOR, FAIL_CLASS, RULE_HIT, SIM_METRICS, PARENT_STRUCTURE, ENGINE_ORDER, TIMESTAMP, RESURRECTION_TRIGGER

## Thread B Interaction
- Thread B does NOT query the Graveyard
- Thread A1 reads rejection tags and failure classes
- A1 computes mutation weights and rescue candidates from Graveyard
- ≥50% graveyard-rescue share in submitted batches (when Graveyard non-empty)

## Known Failed Hypotheses (Pre-Populate)
- CLASSICAL_TIME, COMMUTATIVE_ASSUMPTION, CONTINUOUS_BATH, INFINITE_SET
- INFINITE_RESOLUTION, PRIMITIVE_EQUALS, EUCLIDEAN_METRIC, CLASSICAL_TEMPERATURE
- Primitive causality ("past-push" determinism)
- Primitive identity ("a=a" without probe equivalence)
- FLAT_TORUS (single engine → winding saturation → rescued by Nested Hopf)
- HUB_DIAMOND_BOTTLENECK (collapsed into 110K diamonds, 305K star hubs)

## Resurrection Protocol
- "Courtroom, not a cemetery" — entries are never final
- RESURRECTION_TRIGGER field defines re-test condition
- Trigger fires → GRAVEYARD_SIM_RETEST automatically
- Success path: GRAVEYARD_SIM → SIM_TEST → SIM_CANON_PERMIT → TERM_DEF → canonical

## Holodeck Connection
- Holodeck does NOT test against Graveyard
- Holodeck = outer empirical memory / world-model lab
- Feeds A2 ONLY — forbidden from feeding B rules or SIM evidence directly
- Regression testing = SIM tier + A1 adversarial lanes (not Holodeck)
- Holodeck DEFERRED until core ratchet stabilizes

## Capacity Bounds
- Graveyard MUST be larger than active ratcheted canon
- "Big enough to be useful, not maximal"
- Bounded by F01_FINITUDE: no infinite records
- Managed via Entropy Compaction: coarse-grain high-S failures into low-S boundary atlases
