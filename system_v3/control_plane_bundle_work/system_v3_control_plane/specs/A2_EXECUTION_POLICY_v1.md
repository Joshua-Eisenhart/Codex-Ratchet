# A2_EXECUTION_POLICY v1

Purpose: define execution discipline for A2 without changing transport or kernel contracts.

This document is doctrine-only.
It does NOT modify `ZIP_PROTOCOL_v2`.
It does NOT modify kernel behavior.

## Policy

- A2 is manual-triggered only.
- Automatic tightening requires `MODEL_CAPABILITY_LEVEL = HIGH`.
- Escalation is advisory only.
- No auto-escalation is allowed.
- No wall-clock triggers are allowed.

## Scope Constraints

- No new ZIP types are allowed.
- No new container primitives are allowed.
- A2 must use existing ZIP transport contracts only.
