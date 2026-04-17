---
title: Stack Authority and Capability Index
created: 2026-04-07
updated: 2026-04-16
type: concept
tags: [architecture, planning, validation, system]
sources:
  - raw/articles/new-docs/15_stack_authority_and_capability_index.md
  - raw/articles/new-docs/AGENT_WORKFLOW_AND_BOOT_ARCHITECTURE.md
  - raw/articles/new-docs/00_manifest.md
framing: mixed
---

# Stack Authority and Capability Index

## Overview
This page is the governance index for the stack: it records which docs the source bundle treated as the strongest routing/reference surfaces for each layer and which boots can do what.

It is a governance/source-index page, not a claim that the stack collapses into a hard binary canon/non-canon split.

It is aligned with [[new-docs-manifest]].

## Authority Rules
If a doc is marked `canonical` in the source new-docs bundle, read that as the strongest internal reference label within that bundle, not as closed truth across the whole wiki. Source-note may inform synthesis but does not override the stronger governance/routing surface named for that layer. `archive_old` is historical unless explicitly promoted. If a boot can audit but not run sims, docs must say so explicitly. If a sim claim is live, the file must state artifact and execution path. (from 15_stack_authority_and_capability_index.md)

## Boot Capability Matrix
A1/Recon: drives runner, no audit, does not set strongest truth labels on its own, produces recon artifacts. A0/Compiler: no sims, audits, does not set strongest truth labels on its own, produces campaign tape. B/Ratchet: no sims, audits, writes routing/governance decisions rather than final proof labels, produces ratchet decisions. SIM/Discipline: no sims, audits, does not set strongest truth labels on its own, produces sim audits. Hermes/A2: no sims, audits, does not set strongest truth labels on its own, produces plans/audits/routing. RUNNER: runs sims, no audit, does not set strongest truth labels on its own, produces sim result artifacts. (from 15_stack_authority_and_capability_index.md)

## Governance Gaps
Some historical docs still mention archived execution paths. Some active docs need provenance-based file names instead of duplicate generic labels. Some status claims still need alignment to the stronger tooling and tier-routing docs. (from 15_stack_authority_and_capability_index.md)

## Related pages
- [[leviathan-system]]
- [[mimetic-meme-manifold-source-map]]
- [[constraint-surface-and-process]]
- [[system-architecture-reference]]
- [[agent-workflow-and-boot-architecture]]
- [[tooling-status]]
- [[engine-64-schedule-atlas]]
- [[system-tools-and-plan]]
