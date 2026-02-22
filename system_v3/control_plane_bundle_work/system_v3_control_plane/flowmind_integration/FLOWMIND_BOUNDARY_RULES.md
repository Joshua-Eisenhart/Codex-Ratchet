
# FLOWMIND_BOUNDARY_RULES

This document defines what may be borrowed from FlowMind-style documents and what must not leak across boundaries.

## Allowed borrows (pattern-level)
- Ownership mapping (explicit owner / no bypass) → strengthens `zip_type → (direction, source_layer, target_layer)` invariants.
- Fail-closed discipline → strengthens allowlist/forbidlist validation and deterministic reject semantics.
- Provenance / replay philosophy → strengthens BACKWARD save discipline and auditability.

## Forbidden leakage into transport law (ZIP_PROTOCOL_v2)
Transport is structure-only. ZIP protocol MUST NOT encode:
- classifier stages or parser triage logic
- ABAC semantics
- confidence scoring
- embeddings
- TTL/latency/runtime tuning
- harness UX semantics
- any probabilistic reasoning

## Transport-Only Clause (must appear in ZIP_PROTOCOL_v2)
“This protocol defines transport structure only. It does not encode policy logic, confidence metrics, classification stages, TTL management, ABAC semantics, or probabilistic reasoning.”

## No-Reroute Clause (must appear in ZIP_PROTOCOL_v2)
“ZIP validation failure MUST NOT trigger alternate routing, auto-correction, or downgrade; invalid ZIPs are PARK/REJECT per contract.”

## Correct placement
- FlowMind-like governance and meta-learning concepts belong in A2 reasoning interfaces (e.g., perception frames), not in transport law or kernel admission.

## Decentralized-MMM placement rule
- Decentralization goals (multiple MMMs/Leviathans, anti-monoculture, exploration diversity) are A2 governance concerns only.
- They may influence A2 proposal generation and A1 search diversity targets.
- They MUST NOT alter ZIP allowlists, reject tags, container grammars, or B admission semantics.

## Hard prohibition (normative)
FlowMind semantics must never influence ZIP validation outcomes or container admissibility rules.
