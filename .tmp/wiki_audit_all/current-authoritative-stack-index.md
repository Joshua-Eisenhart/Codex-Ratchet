---
title: Current Authoritative Stack Index
created: 2026-04-10
updated: 2026-04-10
type: summary
tags: [reference, system, architecture, workflow, status]
sources:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/CURRENT_AUTHORITATIVE_STACK_INDEX.md
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/DOCS_QUICK_NAVIGATION.md
framing: current
---

# Current Authoritative Stack Index

## Overview
Compact mirror of the repo-current `system_v4` owner stack. This page exists so the wiki has a public route for the live repo-current routing surfaces instead of forcing readers to infer them from raw repo docs.

## What it controls
- Controller authority stays with `THREAD_CONSOLIDATION_CONTROLLER.md` and its compact state companions.
- The current Axis 0 owner stack is summarized through [[axis0-current-doctrine-state-card]] and [[constraint-geometry-axis0-separation]].
- Thread B remains a staging/support lane, not a doctrine lane; see [[thread-b-stack-audit]].

## Current routing rule
Read this page before using broad `system_v4/docs` clusters as stronger routing surfaces for the live stack. The repo’s own rule is narrow:
- owner packets first
- support packets second
- superseded packets never silently promoted back into live routing

## Current owner families
- Controller-side integration cards: `THREAD_CONSOLIDATION_CONTROLLER.md`, `AXIS0_CURRENT_DOCTRINE_STATE_CARD.md`
- Axis 0 owner packets: `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`, `AXIS0_MANIFOLD_BRIDGE_OPTIONS.md`, `AXIS0_CUT_TAXONOMY.md`, `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md`
- Thread B staging owner/support packets: `THREAD_B_STACK_AUDIT.md` and the narrower export/admission packets beneath it

## What not to do
- Do not treat support packets as if they replace owner packets.
- Do not treat superseded runbooks as active doctrine.
- Do not let the wiki’s older mixed-framing pages outrank this repo-current routing surface when the question is specifically about the live `system_v4` stack.

## Related pages
- [[axis0-current-doctrine-state-card]]
- [[constraint-geometry-axis0-separation]]
- [[thread-b-stack-audit]]
- [[llm-controller-contract]]
- [[topic-map]]
