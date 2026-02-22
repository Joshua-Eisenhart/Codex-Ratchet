# Model Switch Protocol (System Spec Pack v2)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: avoid doing the right work in the wrong model/mode.

## When To Use Which Model (trigger-based)

- Use `GPT-5.3-Codex` when the task requires:
  - reading/writing files in the repo
  - running python/scripts/tests
  - producing deterministic artifacts on disk
  - organizing folders
  - building/running the A0/B/SIM pipeline

- Use `GPT-5.2` when the task is:
  - conceptual/spec discussion
  - system comprehension / interpretation
  - drafting human-readable specs or intent maps
  - debating terminology/labels (noncanon overlays)

## Hard Boundaries (operational)
- Never run long loops or heavy execution unless the request explicitly asks for it.
- Never assume an 8-hour run is desired without an explicit command.
- Any run must be sandbox-contained (writes only under an explicit run dir).

## A1 "Wiggle Room" Requirement
- A1 exploration is inherently nondeterministic and should be LLM-driven.
- A0/B/SIM must remain deterministic given fixed inputs.

