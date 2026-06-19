# Fleet verdict — finite ring-checkerboard support / three-presentation consistency (2026-06-15)

```yaml
sim_id: finite_ring_checkerboard_support_three_presentation_consistency_v0
classification: scratch_diagnostic
promotion_allowed: false
formal_admission_allowed: false
controller: Hermes
fleet_role: advisory audit only; not autonomous control
status: useful exact-table fixture; not admitted
```

## What ran

- Exact Python finite-table leg:
  - `finite_ring_checkerboard_support_three_presentation_consistency_v0_exact.py`
- Source targets:
  - Levos packet `sim_targets/finite_ring_checkerboard_support_three_presentation_consistency_v0.md`
  - wiki ring-checkerboard three-presentations runbook.

## What is genuinely earned at scratch ceiling

- A finite support table with `96 = 2 sheets × 3 eta-shells × 4 phi × 4 chi` rows.
- Agreement of the three presentation coordinates at the table level:
  - flat nested checkerboard chart,
  - spherical/shell chart,
  - nested ring/fiber chart.
- Density-row availability from the runbook spinor table, fenced as a finite readout only.
- Phi-blindness under density probes.
- Phase-sensitive probes split the density quotient.
- Flat/ring adjacency readouts agree for the constructed table.
- Shell/fiber erasure controls merge classes as expected.

## Fleet audit caveats

Codex2 high/xhigh rated the sim **major caveat**, not clean:

1. Agreement is partly by construction because all presentations are generated from one shared index table.
2. Only one exact Python leg existed at first; cross-engine agreement was missing.
3. Folding/reindexing invariants are thin.
4. The support-table hash, generated metadata, peer-read flags, and stronger engine-result fields were missing.
5. It does not admit final `M(C)`, QIT engine, Axis0, smooth manifold, or physics claims.

Grok/grok-build rated it cleaner, but Codex2 is the stronger arbiter. The honest ceiling is therefore:

```text
runs / scratch_diagnostic / exact-table fixture
not canonical
not admitted
needs independent engine legs and stronger folding/reindexing controls
```

## Next hardening step

Add independent JAX and PyTorch legs that compute the same finite support/readout invariants from separate data representations, then require exact agreement before using this support as a base for `spinor_quotient_freedom_discriminator_v0`.
