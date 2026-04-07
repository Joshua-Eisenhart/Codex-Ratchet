# Stack Authority and Capability Index

Date: 2026-04-06
Status: Canonical governance index for the `new docs/` stack

## Authority Precedence

1. This governance index > process doc for routing and capabilities
2. Process doc (CONSTRAINT_SURFACE_AND_PROCESS.md) > thesis/session notes for work execution
3. Narrower docs outrank broader docs within the same tier

## Purpose

This doc answers two questions that the stack currently leaves too implicit:
1. Which docs are authoritative for which layer?
2. Which boots are allowed to do what?

It is a governance index, not a math doc.

## 1) Canonical stack index

| doc | class | status | owner | supersedes | depends_on | source_of_truth |
|---|---|---|---|---|---|---|
| `00_manifest.md` | index | canonical | Hermes/A2 | older ad hoc lists | all promoted docs | folder index only |
| `CONSTRAINT_SURFACE_AND_PROCESS.md` | process | canonical | owner + Hermes | older process notes | root constraints docs | process framing |
| `TOOLING_STATUS.md` | status | canonical | Hermes/A2 | older tooling statuses | live interpreter / import checks | current tooling state |
| `TIER_STATUS.md` | status | canonical | Hermes/A2 | older tier status docs | sim results + current tooling | tier/resolution status |
| `BOOT_PROMPT_TEMPLATES.md` | prompt templates | canonical | Hermes/A2 | older boot prompt drafts | boot architecture docs | launchable boot prompts |
| `AGENT_WORKFLOW_AND_BOOT_ARCHITECTURE.md` | architecture | canonical | Hermes/A2 | older workflow docs | boot prompts + repo artifacts | boot/agent architecture |
| `00_manifest.md` (new content) | index | canonical | Hermes/A2 | old content folder lists | promoted digests | new-doc stack index |
| `06_entropy_sweep_protocol.md` | protocol | canonical | Hermes/A2 | earlier entropy sweep notes | sim family docs | entropy sweep rules |
| `07_model_math_geometry_sim_plan.md` | plan | canonical | Hermes/A2 | earlier geometry plan notes | entropy protocol | model-to-sim stack |
| `13_mimetic_meme_manifold_source_map.md` | source-note | canonical | Hermes/A2 | ad hoc mimetic notes | legacy source docs | source-backed corpus |
| `14_mimetic_meme_manifold_canonical_synthesis.md` | synthesis | canonical | Hermes/A2 | partial mimetic notes | source map + current work | merged synthesis |
| `15_stack_authority_and_capability_index.md` | governance | canonical | Hermes/A2 | none | stack docs | this doc |

## 2) Boot capability matrix

| boot | can run sims | can audit | can write canon | artifact class | notes |
|---|---|---|---|---|---|
| A1 / Recon | drives runner | no | no | recon artifacts | advocates candidate geometry; "sim it richly" means driving the runner to produce sims |
| A0 / Compiler | no | yes | no | campaign tape / structural records | deterministic compilation, linting, archival record |
| B / Ratchet | no | yes | yes | canon / ratchet decisions | blind constraint enforcement; accepts or rejects evidence |
| SIM / Discipline Enforcer | no | yes | no | sim audits | audits runner output: declarations, negatives, artifacts, promotion status |
| Hermes / A2 | no | yes | no | plans / audits / routing | launches, routes, monitors contamination; not a sim runner |
| RUNNER (e.g. `run_real_ratchet`) | yes | no | no | sim result artifacts (.json) | executes sim code; produces evidence consumed by A1/B/SIM boots |


## 3) Authority rules

- If a doc is marked `canonical`, it is the current best internal reference for that layer.
- If a doc is marked `source-note`, it may inform synthesis but does not override canonical governance.
- If a doc is marked `archive_old`, it is historical unless explicitly promoted.
- If a boot can audit but not run sims, the docs must say so explicitly.
- If a sim claim is live, the file must state the artifact and the execution path that produced it.

## 4) Current governance gaps

- Some historical docs still mention archived execution paths or prior interpreter states.
- Some active docs still need provenance-based file names instead of duplicate generic labels.
- Some status claims still need to be aligned to the canonical tooling and tier docs.

## 5) Immediate use
Use this doc when deciding whether a file is:
- a source note
- a canonical summary
- an operational status card
- a boot prompt
- a historical archive
