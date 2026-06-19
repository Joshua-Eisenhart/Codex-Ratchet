# Build Card: engines_run_with_axes_v0

## Boundary

- Packet: `system_v6/sims/engines_run_with_axes_v0/`
- Object: Carnot and Szilard cycles run as finite dynamics on the committed 33-cell carrier, then read through the committed Axis 0, Axis 6, Axis 4, and Axis 5-family readouts.
- Claim ceiling: `classical_engine_axis_signature_baseline_only`.
- Classification: `scratch_diagnostic`.
- Row classification: `classical_baseline`.
- Promotion allowed: `false`.
- Formal admission allowed: `false`.
- NO git add/commit.
- No builder `audit_verdict.md`; the boundary helper is used fully by the builder and validator.

## Authority

- Owner order: "make sure the carnot and szilard engines themselves run and have axes".
- Disciplined-path doctrine: `df17999f2`.
- Carnot/Szilard ledger v1: `d79d71a0d`.
- Basin-cycle conventions and 33-cell carrier continuity: `ffe6e1c38`.
- Axis 0 readout: `5d330b427`, signed outgoing generator-gradient flux.
- Axis 6 readout: `b6fafc67f`, precedence polarity.
- Axis 4 readout: `99c4f84b3`, W4 fixture.
- Axis 5-family partial readout: committed partial witness packet at current source lock.
- Standards codex: `c83842e55`.

## Object

The packet executes two classical engine fixtures over the full 33-cell carrier:

- Carnot strokes consume the reversible Carnot ledger row and apply committed generators in a four-stroke order: hot isothermal expansion, adiabatic expansion, cold isothermal compression, adiabatic compression.
- Szilard strokes consume the paid measure/feedback/erase ledger row and apply committed generators in a four-stroke order: measure record, feedback expansion, erase record, reset boundary.
- Every stroke maps all 33 starting cells through one committed generator/channel edge and records a 33-row state trajectory.
- Every stroke carries a typed ledger row from the committed ledger source or a packet-local split of the committed Szilard paid row.

The stroke-to-generator map is a packet fixture over committed generator names. It is not a new heat-bath model, a new thermodynamic proof, or a nonclassical engine result.

## Axis Signature

For each engine and each stroke, the packet computes the post-stroke axis signature by looking up the running trajectory's post-stroke cells in the unchanged parent readout tables:

- Axis 0: signed outgoing generator-gradient flux polarity.
- Axis 6: precedence sign.
- Axis 4: W4 sign.
- Axis 5-family: partial `{Ti,Te}` versus `{Fi,Fe}` operator-family witness rows only.

The per-stroke polarity table is the engine's axis signature. The Carnot-vs-Szilard comparison is computed from those per-stroke signatures and staged as the classical baseline row that a future QIT engine signature must exceed or differ from.

## Controls

- Do-nothing identity engine: identity strokes over all 33 cells must leave state trajectories unchanged and produce degenerate repeated signatures.
- Shuffled stroke order N01: the same generator multiset in a different order must change the signature for Carnot and Szilard.
- Ledger continuity: Carnot stroke names must match `d79d71a0d`; Szilard paid measure/feedback/erase must remain SAT with paid erasure cost meeting the Landauer row.

## Tool Contract

- Python runner: committed carrier edge execution and JSON output.
- Parent readout builders: Axis 0, Axis 6, Axis 4, Axis 5-family partial.
- Ledger helpers: Carnot ledger and Szilard paid erasure rows.
- Boundary helper: `scripts/builder_audit_boundary.py`.

Support tools such as `json`, `hashlib`, `pathlib`, and `subprocess` only serialize, hash, and source-lock the packet.

## Validator Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engines_run_with_axes_v0/engines_run_with_axes_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engines_run_with_axes_v0/validate_engines_run_with_axes_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/engines_run_with_axes_v0/tests
```

## Status

Implementation target:

- two engines run over all 33 cells;
- four stroke trajectories per engine;
- typed ledger per stroke;
- committed axis readouts applied unchanged to running trajectories;
- Carnot-vs-Szilard axis signature comparison emitted;
- identity and N01 shuffled controls pass;
- `classical_baseline` row staged for future QIT capability comparison;
- boundary helper gate present;
- no git add/commit.
