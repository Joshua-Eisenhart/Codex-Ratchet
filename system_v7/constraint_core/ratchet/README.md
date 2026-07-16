# Order-open Ratchet v0.6 evidence audit

This directory contains the current executable process. It explores candidate presentations, gate boundaries, gate
decompositions, and gate orders as proposal populations. It does not treat a list as a ladder.

## Run

```text
python3 ratchet/ratchet_engine.py --self-test
python3 ratchet/ratchet_engine.py --run \
  ratchet/examples/root_order_open_packet_v0_5.json \
  --output ratchet/runs/root_order_open_run_v0_5.json
python3 ratchet/ratchet_engine.py --validate ratchet/runs/root_order_open_run_v0_5.json
python3 ratchet/bundle_ratchet_lint.py
python3 ratchet/manifold_evidence/run_layer_receipts.py
python3 ratchet/manifold_evidence/entropic_geometry_audit.py
python3 ratchet/manifold_evidence/manifold_fixture_ratchet.py
python3 ratchet/manifold_evidence/build_layer_state.py
```

`ratchet_kernel.py` is the compatibility entry point to the same v0.5 engine.

## What was actually executed

- 32,400 finite parameter proposals in 64 batches;
- 3,147 distinct behavioural partitions after exposing 29,253 aliases;
- all 16 active-demand subsets;
- 50,352 behaviour-by-demand-subset evaluations (3,147 × 16), memoized without repeat-count inflation;
- all 75 ordered set-partitions of four proposed demand families;
- fused and split gates at every granularity from one to four blocks;
- coface-gradient, demand-erasure, relisting, rechunking, and anti-canon controls.

The run found 44 intermediate trajectories and one common final frontier on a generated process fixture. That is
packet-level endpoint convergence, not a canonical gate order and not a scientific manifold result.

## Executed manifold audit

The v0.6 evidence lane applies the process to actual bundled manifold observations and reports every proposed layer:

- all L1–L8 instruments pass a fresh local rerun;
- 16,384 manifold candidate presentations collapse to 224 actual partitions and 16,160 aliases;
- all 75 gate-order/decomposition schedules execute;
- the orientation demand produces a real coface gradient `9 -> 0` when one binary orientation distinction is added to
  the radial scalar;
- L5 scalar presentations are mutually invertible aliases on the installed branch;
- BKM, SLD/Bures, Wigner–Yanase, and RLD coincide on the installed commuting radial tangent;
- the marginal entropy geometry has `g_phi_phi=0` while the global phase geometry has
  `QFI_phi_phi=sin^2(2 eta)>0`;
- the nontrivial, reversed, and constant-section Chern integrations are all executed;
- scientific manifold layers admitted remain **0**.

Read `manifold_evidence/MANIFOLD_RATCHET_STATE_REPORT.md` for the layer-by-layer equations, controls, failures, and
next digs. A local script PASS is evidence at its declared fixture ceiling, never Ratchet admission by itself.

## Current files

- `ratchet_engine.py` — mass candidate streamer, behavioural alias census, finite-partition MSS, ordered gate-partition
  search, coface gradient, receipts, validator, and self-test.
- `examples/root_order_open_packet_v0_5.json` — the bounded process fixture.
- `runs/root_order_open_run_v0_5.json` — the full executed trace for 75 schedules.
- `schemas/ratchet_order_open_run.schema.json` — v0.5 interchange schema.
- `GRADIENT_DRIVE.md` — entropy–geometry coface semantics.
- `CURRENT_FRONTIER.md` — the exact process result and scientific non-result.
- `CA_MSS_RESEARCH_PROGRAM.md` — a proposal lane; no CA is admitted by v0.5.
- `archive/ratchet_engine_v0_4_frozen.py` — frozen predecessor for audit reproduction.
- `archive/manifold_l5_reaudit_v0_4_killed.py` — preserved killed instrument, never imported as evidence.
- `manifold_evidence/` — raw L1–L8 execution receipts, the adversarial entropic-geometry audit, the actual
  manifold-observation Ratchet, the external-L5-claim boundary, and the complete layer state report.

The v0.4 L5 demotion receipt remains killed as scientific evidence. The v0.5 engine does not execute it during
integrity checks.
