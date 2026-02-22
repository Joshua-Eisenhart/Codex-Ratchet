# Conformance Fixture Pack v1
Status: DRAFT / NONCANON

This pack contains deterministic fixture payloads and expected outcomes for bootpack conformance validation.

Hashing rule:
- fixture pack hash is computed over `expected_outcomes.json` and `fixtures/*` files (sorted path order).
- `manifest.json` stores the declared fixture pack hash for audit.

