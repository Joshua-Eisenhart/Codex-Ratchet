# Initial verdict — quantum Hopfield QCA entropy-information (2026-06-15)

```yaml
sim_id: quantum_hopfield_qca_entropy_information_v0
classification: scratch_diagnostic
promotion_allowed: false
formal_admission_allowed: false
status: exact diagonal/open-channel fixture started; not fleet-audited yet
```

## What this exact leg tests

This is a fenced first pass for the Levos target:

- finite ring support: `S = {0,1}^4`
- memory states: `0000`, `1111`
- QCA/Hopfield update: local majority rule on ring neighborhoods
- open diagonal channel: `p * HopfieldUpdate + (1-p) * uniform noise`
- entropy/readouts:
  - basin assignment entropy
  - diagonal von-Neumann/Shannon entropy
  - fidelity to named memory states
  - mutual information across cut `{0,1}|{2,3}`
  - false-memory rate

## What passed

- finite support exists: `16` states
- named memory basins exist
- open diagonal channel is row-stochastic
- steady state is computed and normalized
- typed entropy/information readouts are available
- coherent information is blocked, not faked
- random-memory / identity / density-only controls are fenced

## Honest ceiling

This earns only a **diagonal open-channel memory fixture**:

```text
finite QCA/Hopfield-like basins + typed entropy-information readouts at scratch ceiling
```

It does **not** earn:

- full quantum Hopfield,
- Lindblad/CPTP non-diagonal dynamics,
- coherent information,
- admitted QIT engine,
- physical/social claims.

## Next hardening

Add independent JAX/PyTorch legs and run non-Claude fleet audit before treating this as more than a scratch fixture.
