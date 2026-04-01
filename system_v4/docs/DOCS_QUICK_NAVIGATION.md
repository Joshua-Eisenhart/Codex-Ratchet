# System V4 Docs — Quick Navigation

## Why this exists

This repo has grown quickly. This file is your one-page entrypoint so you do not need to hunt for active and legacy docs manually.

## Start here (first)

- [AXIS0_ACTIVE_PACKET_INDEX.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_ACTIVE_PACKET_INDEX.md) — compact Axis 0 entrypoint for the active packet stack.
- [CURRENT_AUTHORITATIVE_STACK_INDEX.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/CURRENT_AUTHORITATIVE_STACK_INDEX.md) — authority surfaces + support + superseded surfaces.
- [AXIS0_CURRENT_DOCTRINE_STATE_CARD.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_CURRENT_DOCTRINE_STATE_CARD.md) — current earned/open/closed state.
- [AXIS0_BRIDGE_CLOSEOUT_CARD.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_BRIDGE_CLOSEOUT_CARD.md) — compact safe read + anti-smoothing locks.

## Fast checks

- Run this once when you need a clean view of doc health:

```bash
./system_v4/tools/doc_inventory.sh
```

- If you only want active docs:

```bash
./system_v4/tools/doc_inventory.sh --active
```

- If you only want superseded/legacy docs:

```bash
./system_v4/tools/doc_inventory.sh --superseded
```

## What is junk vs live

- `ACTIVE`: current-use docs where `Status` is not marked as superseded/deprecated.
- `SUPERSEDED`: docs with `Status: SUPERSEDED` or explicit replacement/deprecation.

## Anti-junk rule

- If a doc is unneeded for current routing, it belongs only in support/scratch/history and should be listed in the superseded/legacy section of `CURRENT_AUTHORITATIVE_STACK_INDEX.md`.
