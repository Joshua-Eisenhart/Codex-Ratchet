# ConstraintBox implementation-seed status

This directory is the previously built standalone ConstraintBox seed. It is
included because it captures the clean separation that the existing ClaimGate
work needs to move toward:

- a small standalone controller;
- a separate simulation-estate registry;
- optional Lev and Codex-Ratchet adapters;
- typed finite/manifold fixtures without a physical ontology baked into the
  controller.

The seed is not a replacement for the copied ClaimGate work. It is a proposed
refactoring target. The receiving system should compare its modules and tests
against `02_CURRENT_CLAIMGATE/` rather than choosing either by prose.

Its own included `BUILD_VERIFICATION.json` records a local 50-test run from
the prior build context. That is a bounded package receipt, not a fresh
verification of the full copied ClaimGate estate.
