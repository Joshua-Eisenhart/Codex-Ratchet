# Public-Facing FlowMind as “A3 Host” (Interface Contract, v1)
Status: PUBLIC / NONCANON (explanatory only)
Date: 2026-02-20

This project can be hosted by a higher-level workflow/orchestration system (e.g., “FlowMind”) as long as the entropy boundary is enforced.

## Terminology
- **A3 Host (FlowMind)**: orchestration/runtime that coordinates high-entropy work (A2/A1), handles manifests, provenance, storage ergonomics, and scheduling.
- **Kernel Substrate (A0/B/SIM)**: deterministic compiler + admission kernel + deterministic sims, with strict artifact boundaries.

## Non-Negotiable Boundary
FlowMind (A3) MUST treat the kernel substrate as sealed:
- FlowMind can *request* work and *store* context.
- FlowMind MUST NOT introduce new kernel primitives (confidence, probability, time windows, optimization objectives) into kernel-facing artifacts.
- FlowMind MUST NOT bypass A0 compilation/canonicalization when communicating with B.

## Safe-to-Salvage Patterns From a Workflow/OS Spec
These patterns align well when confined above the boundary:
- manifest-driven execution (explicit inputs/outputs)
- provenance chains (hashes, replay pointers)
- deterministic logging discipline
- strict container boundaries (no “ambient memory” touching canon)
- policy gating as explicit configuration (above the boundary; kernel still enforces hard fences)

## Quarantine (Keep Above Boundary Only)
If FlowMind uses these, they must remain A3/A2/A1-only and must not leak into canon:
- confidence scores / probabilities as “truth markers”
- time/TTL/frame-rate/sliding-window primitives as kernel concepts
- “world-model” state treated as canonical
- optimization/teleology as a kernel goal

## YAML Use (Recommended Scope)
YAML is a good fit for A3/A2/A1 operational surfaces:
- manifests for work units (“ZIP_JOB”-like bundles)
- Rosetta overlay dictionaries (multi-vocabulary mapping to cold core)
- A2 persistent memory schemas (append-only logs + compact indices)

Kernel-facing artifacts should remain in a strict, unambiguous grammar; YAML may describe them, but should not replace the kernel container formats.

## A3 ↔ Substrate Interface (Minimal Contract)
FlowMind can integrate by treating the substrate as a black-box pipeline:
1. Provide inputs to A2/A1 (documents, prompts, fuel manifests).
2. Receive compiled artifacts from A0 (kernel-eligible containers only).
3. Submit artifacts to B; receive deterministic outcomes (admit/park/reject + reasons).
4. Launch SIM runs (deterministic) and collect SIM_EVIDENCE artifacts.
5. Submit SIM_EVIDENCE artifacts to B; receive updated canonical snapshots.

FlowMind should never “reinterpret” kernel outputs; it may only route/log them.

