---
id: "A1_STRIPPED::DETERMINISTIC_DUAL_REPLAY"
type: "REFINED_CONCEPT"
layer: "A1_STRIPPED"
authority: "CROSS_VALIDATED"
---

# DETERMINISTIC_DUAL_REPLAY
**Node ID:** `A1_STRIPPED::DETERMINISTIC_DUAL_REPLAY`

## Description
RQ-124: promotion candidate must produce identical final state hash AND identical event-log hash across two full deterministic replays from same baseline. Mismatch → mark NONDETERMINISTIC, write grave

## Properties
- **dropped_jargon**: []
- **required_anchors**: ["UNVERIFIED"]

## Outward Relations
- **STRIPPED_FROM** → [[deterministic_dual_replay]]
- **STRUCTURALLY_RELATED** → [[deterministic_dual_replay]]
- **STRUCTURALLY_RELATED** → [[DUAL_REPLAY_DETERMINISM_REQUIREMENT]]
- **STRUCTURALLY_RELATED** → [[DUAL_REPLAY_DETERMINISM_REQUIREMENT]]
- **STRUCTURALLY_RELATED** → [[dual_replay_release_gate]]
- **STRUCTURALLY_RELATED** → [[DUAL_REPLAY_DETERMINISM_REQUIREMENT]]
- **STRUCTURALLY_RELATED** → [[control_plane_deterministic_replay_runner_outline_v1]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v2_deterministic_replay_runner_ou]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v3_deterministic_replay_runner_ou]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v4_deterministic_replay_runner_ou]]
- **STRUCTURALLY_RELATED** → [[sim_deterministic_replay]]
- **STRUCTURALLY_RELATED** → [[deterministic_replay_runner]]
- **STRUCTURALLY_RELATED** → [[deterministic_replay_runner_outline_v1]]
- **STRUCTURALLY_RELATED** → [[DETERMINISTIC_REPLAY_HASH_EQUALITY]]

## Inward Relations
- [[deterministic_dual_replay]] → **ROSETTA_MAP**
- [[DETERMINISTIC_DUAL_REPLAY_CARTRIDGE]] → **PACKAGED_FROM**
