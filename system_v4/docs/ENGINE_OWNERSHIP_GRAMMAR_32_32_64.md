# [Controller-safe] Engine Ownership Grammar: 32 / 32 / 64

**Status:** Runtime-vs-structure separation surface.  
**Purpose:** Preserve the distinction between per-engine ownership, current runtime execution counts, and the broader structural 8x8 scaffold.

---

## The Three Counts

### 1. `32 per engine`

Current runtime truth:

- one engine type runs:
  - `8 macro-stages`
  - `4 ordered operator slots per macro-stage`
- that gives:
  - `8 x 4 = 32` runtime microsteps per engine type

### 2. `32 per other engine`

The other engine type contributes its own separate `32` runtime microsteps.

### 3. `64 total runtime microsteps`

The current live runtime reaches `64` by combining:

- `32` from engine type 1
- `32` from engine type 2

This is a runtime total, not proof that both engines share one flat pool of 64 identical structural units.

---

## What This Does Not Settle

This document does **not** settle:

- the final structural 8x8 decomposition
- the final signed-operator basis
- whether each engine's owned 32 should later be rebuilt from a stricter dual-loop representation
- the final bridge from runtime 32/32/64 into structural state-space ownership

---

## Stage-Local Ownership

Within each engine's `32`:

- each macro-stage owns `4` ordered substeps
- the order matters
- stage-local ordering is part of the grammar, not a display convenience

Current runtime order:

- `Ti -> Fe -> Te -> Fi`

This stage-local ordering must remain distinct from:

- larger loop ordering
- engine family split
- flow direction
- Axis 6 precedence claims

---

## Structural 8x8 Note

There may still be a deeper structural 8x8 picture where:

- one 8-set comes from terrain/topology ownership
- one 8-set comes from signed operator realizations

But that structural picture is a scaffold until the bridge is closed.

So the safe rule is:

- `32 / 32 / 64` = current runtime ownership surface
- `8x8` = structural scaffold / proposal surface unless explicitly earned

---

## Use Rule

If a future doc or sim says `64`, it must say which of these it means:

1. runtime total across both engine families
2. per-engine owned execution units
3. structural 8x8 scaffold

If it does not say which one, it is ambiguous and should be treated as drift.
