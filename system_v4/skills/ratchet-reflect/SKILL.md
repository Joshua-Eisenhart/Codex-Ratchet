---
name: ratchet-reflect
description: Find connections between concepts and weave the graph. Adapted from JP's 6R REFLECT phase.
skill_type: graph-enrichment
related_skills: [ratchet-reduce, ratchet-reweave, ratchet-verify]
---

# Ratchet REFLECT — Find Connections, Weave the Graph

Connect newly extracted concepts to existing graph nodes using dual discovery.

## Invocation

```
/ratchet-reflect [concept_id]        # connect a specific concept
/ratchet-reflect recent              # connect all concepts from last extraction
/ratchet-reflect --promoted          # run on promoted layer only (dense linking)
```

## Core Rule: The Articulation Test

> [[Concept A]] connects to [[Concept B]] because [specific reason]

If you cannot fill in [specific reason] with something substantive, **the connection FAILS**. Do not add the edge.

## EXECUTE NOW Steps

1. **Read target concept fully** — understand its claim and context
2. **Dual discovery** (run in parallel):
   - **Path 1: Structural** — Browse concepts in same trust zone, same source doc family
   - **Path 2: Semantic** — Search by description terms for conceptually related concepts
3. **Evaluate each candidate** — does a genuine connection exist?
4. **Apply Articulation Test** — can you articulate WHY?
5. **Add edges** where connections pass the test
6. **Report** what was connected and why

## Valid Relationship Types

| Relationship | Signal | Example |
|-------------|--------|---------|
| DEPENDS_ON | A requires B to function | "ratchet loop depends on constraint verification" |
| CONSTRAINS | A limits or gates B | "entropy ordering constrains intake valve" |
| IMPLEMENTS | A is concrete instance of B | "prompt stack implements deterministic execution" |
| CONTRADICTS | Mutually exclusive | "global state contradicts locality constraint" |
| EXTENDS | Adds dimension | "chirality extends symmetry into handedness" |
| GROUNDS | Provides foundation | "identity emergence grounds observer theory" |
| EXEMPLIFIES | Concrete instance | "DreamCoder exemplifies abstraction learning" |

## Reject If

- "Related" without specifics
- Found through keyword matching alone with no semantic depth
- Linking would confuse more than clarify
- Relationship too obvious to be useful ("readme related to documentation")

## Agent Traversal Check

| Agent Benefit | Keep Edge |
|---------------|-----------|
| Provides reasoning foundation | YES |
| Offers implementation pattern | YES |
| Surfaces tension to consider | YES |
| Gives concrete example | YES |
| Just "related topic" with no decision value | NO |

## Synthesis Detection

When 3+ concepts make complementary arguments that combine into something none says alone → flag for future synthesis note. Do NOT create during REFLECT.

## Pipeline Chaining

After REFLECT → `/ratchet-reweave [connected concepts]` to update older concepts.
