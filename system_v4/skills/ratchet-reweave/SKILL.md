---
name: ratchet-reweave
description: Update existing graph concepts with new knowledge. Backward pass from JP's 6R REWEAVE phase.
skill_type: graph-refinement
related_skills: [ratchet-reduce, ratchet-reflect, ratchet-verify]
---

# Ratchet REWEAVE — Update Old Concepts with New Knowledge

The backward pass: after new concepts are added and connected, revisit existing concepts to see if they should be updated.

## Invocation

```
/ratchet-reweave [concept_id]       # fully reconsider specific concept
/ratchet-reweave --sparse           # process concepts with <2 edges
/ratchet-reweave --since Nd         # reweave concepts not updated in N days
```

## Core Question

> "If I wrote this concept today, with everything I now know, what would be different?"

## EXECUTE NOW Steps

1. **Read target concept fully** — current description, connections, age
2. **Search for newer related concepts** — dual discovery
3. **Evaluate what needs changing:**
   - Add connections to newer concepts
   - Sharpen description if understanding evolved
   - Consider splitting if concept covers separate ideas
   - Challenge claim if new evidence contradicts
   - Rewrite if understanding is deeper now
4. **Apply changes**
5. **Report** structured summary of changes

## The Five Reweave Actions

| Action | When |
|--------|------|
| Add connections | Newer concepts exist that should link here |
| Sharpen description | Description too vague (fails the Disagreement Test) |
| Split concept | Multiple claims bundled into one node |
| Challenge claim | New evidence contradicts existing description |
| Promote trust zone | Concept has enough evidence to move from INTAKE→REFINED→KERNEL |

## The Sharpening Test

> Could someone disagree with this specific claim?

- Yes → Sharp enough
- No → Too vague, needs sharpening

| Vague | Sharp |
|-------|-------|
| "X is important" | "X matters because Y, which enables Z" |
| "consider doing X" | "X works when [condition] because [mechanism]" |
| "there are tradeoffs" | "[specific tradeoff]: gaining X costs Y" |

## The Split Test

Does this concept make multiple claims that could stand alone? If yes → split into focused concepts, each with its own edges.

## When NOT to Change

- Accurate + well-connected + recently verified = leave alone
- Cosmetic rewording without semantic improvement = churn

## Pipeline Chaining

After REWEAVE → `/ratchet-verify [reweaved concepts]` to run quality gates.
