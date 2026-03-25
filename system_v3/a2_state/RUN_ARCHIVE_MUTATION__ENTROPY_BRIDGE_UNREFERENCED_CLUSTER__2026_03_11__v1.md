# RUN_ARCHIVE_MUTATION__ENTROPY_BRIDGE_UNREFERENCED_CLUSTER__2026_03_11__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-11
Role: record of the bounded archive/quarantine mutation over the exact unreferenced entropy-bridge run cluster

## Mutation basis

Source prep set:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/RUN_ARCHIVE_PREP__ENTROPY_BRIDGE_UNREFERENCED_CLUSTER__2026_03_11__v1.md`

Archive destination:
- `/home/ratchet/Desktop/Codex Ratchet/archive/distillery/RUN_ENTROPY_BRIDGE_UNREFERENCED_CLUSTER__2026_03_11__v1`

## What moved

Moved exactly `42` run directories from:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs`

into:
- `/home/ratchet/Desktop/Codex Ratchet/archive/distillery/RUN_ENTROPY_BRIDGE_UNREFERENCED_CLUSTER__2026_03_11__v1`

Mutation class:
- bounded archive/quarantine move
- no run-anchor file rewrite
- no touch to anchor-dependent members

## Measured result

Before:
- `system_v3/runs`: `557M`
- live entropy-bridge cluster members: `62`

After:
- `system_v3/runs`: `279M`
- archived batch size: `277M`
- live entropy-bridge cluster members remaining in `system_v3/runs`: `20`

## Remaining live cluster

The remaining `20` live members are exactly the anchor-dependent set:

1. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_0001`
2. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_0002`
3. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_0003`
4. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0006`
5. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0007`
6. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0008`
7. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0026`
8. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0028`
9. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0030`
10. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0040`
11. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_ROTATE_0001`
12. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_SUPPORT_0001`
13. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_TARGETROT_0001`
14. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_COLDER_WITNESS_BROAD_0001`
15. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_HELPER_LIFT_BROAD_0001`
16. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_HELPER_STRIP_BROAD_0001`
17. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_HELPER_STRIP_BROAD_0002`
18. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_RATE_ALIAS_BROAD_0001`
19. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_REFORMULATION_BROAD_0001`
20. `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_THERMAL_TIME_BROAD_0001`

## Stop rule reached

This mutation stops here.

It does not:
- rewrite anchor/witness files
- move the remaining `20`
- continue into a second run-family cleanup sweep

The next run-side cleanup move, if wanted, must be a different bounded pass over the remaining anchor-dependent set or another run family entirely.
