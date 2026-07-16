# FINITE CHU/PROBE KERNEL v0 — Build Card 3

## Status and boundary

This is a finite, pre-categorical response-table diagnostic.  Its primary
object is an exact response matrix

```text
R : S x P -> O
```

and not a Chu category, an adjunction, a duality theorem, a physical model, or
an admission claim.  No Chu-category laws are installed here.

The public status target is at most `passes local rerun`; the internal
promotion status is `diagnostic_only`.  The result is blocked from
scientific/manifold/entropy/Axis0/ontology consumers.

## Required operations

The runner must implement and receipt all of the following on finite tables:

1. Row quotient: states with identical outcome vectors under a selected probe
   family.
2. Column quotient: both literal-equal response columns and the requested
   identical-distinguishing-power quotient (same state partition).
3. Refinement under added probes: exhaustive verification on the synthetic
   five-probe fixture that a larger probe subset only refines a prior row
   quotient.
4. Sequential-probe extension: a second probe selected as a deterministic
   function of the first outcome, returning an ordered transcript.
5. State/probe dualization: literal matrix transpose, with double-transpose
   identity checked.
6. Exact minimal separating family search over all probe subsets.

## Fixtures

### Synthetic six-state, five-probe table

The fixed binary table is deliberately structured: `a/e` have the same
distinguishing partition, `b/d` have the same distinguishing partition, and
`a,b,c` separate all six states.  The full subset lattice has `3^5 = 243`
ordered inclusion pairs, all of which must satisfy monotone refinement.

### Ratchet G1 source surface

Source is read-only:

- `system_v7/constraint_core/ratchet/ratchet_engine.py`
- `system_v7/constraint_core/ratchet/examples/root_history_packet_v0_4.json`

The runner imports `generate_observations` and selects `G1_two_step_order`.
It regenerates the 81 ordered source records (three history marks cubed,
times three current marks).  The source has exactly three direct probes
`p,q,r` and four outcome labels:

```text
distinguished, not_distinguished, unresolved, inadmissible
```

There is no native 81-by-3 matrix API.  This lane derives it, without changing
the source, as:

```text
R(source_row, x) = outcome of the regenerated record with
                   source_row.history and direct probe x
```

Thus `S` is the 81 source records and `P = {p,q,r}` is the direct probe family.
The four labels are `O`, not four native source columns.  A separate derived
one-hot outcome-family membership view is reported only to make this
adaptation auditable; it is not conflated with the primary table.

## Memory-2 check

The upstream ratchet G1 receipt says a one-step candidate has 54 fit errors
while the two-step candidate has zero.  That is a source-level requirement on
the history representation.  A fixed response table has no source transition
or update operation.  Therefore this lane must measure rather than assume
whether outcome-adaptive sequential queries are needed:

- enumerate every two-step policy on the real direct table;
- test whether any sequential transcript separates states that the full static
  `p,q,r` table leaves equivalent;
- test whether a static subset already induces the full table quotient.

If static probes suffice, the result must say so and must not relabel the
memory-2 tooth as a sequential-query theorem.  An online update semantics is
out of scope unless separately specified.

## Evidence and freeze contract

- `run.py` uses only Python stdlib plus a genuine, required `rustworkx`
  connected-components cross-check built from raw response-equality edges.
- `results_v1.json` is append-only JSON Lines: a header, exactly two
  deterministic run records, then a freeze record.  The runner never rewrites
  prior lines.
- Two fresh invocations must produce identical canonical payload bytes and
  SHA-256 digests before freeze.
- No file outside this directory is to be created, deleted, moved, or edited
  by the implementation or its runner.
