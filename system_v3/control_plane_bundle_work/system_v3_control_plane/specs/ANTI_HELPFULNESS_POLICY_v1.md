# ANTI_HELPFULNESS_POLICY v1

Purpose: define hostile-input handling doctrine for all LLM-produced artifacts across entropy layers.

This document is doctrine-only.
It does NOT modify `ZIP_PROTOCOL_v2`.
It does NOT modify kernel behavior.

## Doctrine

- All LLM artifacts are hostile input by default.
- No auto-correction is allowed.
- No schema forgiveness is allowed.
- No implicit defaults are allowed.
- No free-text interpretation is allowed in enforcement paths.

## Scope

- Applies to A2 and A1 outputs at ingestion boundaries.
- Reinforces fail-closed posture in A0/B/SIM handling.
- Does not introduce new container primitives, ZIP types, or mutation paths.
