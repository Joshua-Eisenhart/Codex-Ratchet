# Build Card — `gcm_constraint_carve_floor_v0`

Status: constraints-first finite floor packet.  
Claim ceiling: `scratch_diagnostic`; no manifold admission; no axis claims; no engine claims.

## Authority

- `system_v6/receipts/owner_stop_order_manifold_first_20260612.md`: axes stopped; manifold first.
- `system_v6/receipts/gcm_reanchor_requirement_20260612.md`: the manifold is constraint-carved, not drawn; every assembly packet must answer: where is the constraint set, and what did it carve?
- `system_v6/foundations/root_axioms_v0_1_DRAFT.md`: `M(C) = {x : x is admissible under active constraint set C}` and `M(C) = (S, C, P, ~_P, Adm_C, composition/bracketing, local readouts, controls, receipts)`.
- `~/wiki/concepts/constraint-manifold-architecture.md`: root constraints -> `M(C)` -> geometry on `M(C)` -> axes as downstream functions.

## Packet goal

Build the smallest executable finite floor that has the required pieces:

```text
S: finite candidate state set
C: active constraints that actually bite
P: finite probe family
~_P: probe-relative quotient classes over survivors
Adm_C: executable admissibility predicate
composition/order maps: R and D with noncommuting order test
controls: empty-C, constraint erasures, overconstraint, probe erasures
carved structure: adjacency/components read off survivors
terrain readout attempt: explicit negative if 8 regions do not appear
```

## Finite object

Candidate state:

```text
(shell, phase_parity, orientation, memory)
```

with:

- `shell ∈ {0,1,2}`
- `phase_parity ∈ {0,1}`
- `orientation ∈ {0,1}`
- `memory ∈ {0,1}`

So `|S| = 24`.

This is not the manifold. It is the first finite constraint-carve floor. The result must say exactly what survives and what dies.

## Constraints

1. `C_history_consistency`: finite history/memory bookkeeping must match the local finite coordinates.
2. `C_N01_order_visible`: the two maps `R∘D` and `D∘R` must be distinguishable under the finite probe family.
3. `C_closure_under_order_maps`: after applying `R`, `D`, `R∘D`, and `D∘R`, survivors must remain inside the survivor set. This is the stability tooth.

## Required tests

Tests must fail before production code exists, then pass after implementation:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/gcm_constraint_carve_floor_v0/tests/test_gcm_constraint_carve_floor_v0.py
```

## Expected honest result

This packet may show a very small survivor floor. It must not invent terrain regions. If the survivor graph has one component and no eight-region split, the terrain readout verdict is negative.
