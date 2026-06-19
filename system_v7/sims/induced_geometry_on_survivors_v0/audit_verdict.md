# audit_verdict - induced_geometry_on_survivors_v0

```yaml
classification: scratch_diagnostic
promotion_allowed: false
formal_admission_allowed: false
does_not_self_upgrade: true
ladder_reached: passes local rerun
builder: Codex local build; this is not a fresh fleet audit
```

## What this sim is

Manifold-tower L6 scratch diagnostic: relational geometry restricted to the
current survivor set. The finite support is `S={0,1}^5`. The probe map is
`pi(s)=(p0,p1,p2,p3)`, and the named equivalence relation is:

```text
s ~_P s_prime iff pi(s) == pi(s_prime)
```

The live vertices are quotient classes `[s]_P`, represented by 4-bit probe
signatures. The hidden bit is not identity-bearing in this sim.

## Load-bearing discriminator

At each constraint step the sim recomputes:

```text
G_t = InducedGeometry_HammingNN(X_t)
```

where edges join pairs at the minimum positive Hamming distance inside the
current survivor set `X_t`. The first constraint keeps even-parity probe
classes. That removes every original distance-1 neighbor, so the recomputed
nearest-neighbor distance changes from `1` to `2`.

The stale control holds `G_0` fixed and only restricts old edges. On the same
`C1` survivor set, stale geometry has zero old edges and eight components,
while recomputed geometry has distance-2 edges, one component, and degree
sequence `[6,6,6,6,6,6,6,6]`.

## State/data perturbation

The primary final constraint is `pi(s)[0] == 0`. The perturbation replaces it
with `pi(s)[0] == 1`. This is a real admissibility-predicate change, not a
label edit. It changes the final survivor set and degree sequence (`K4` versus
`K3` under the recomputed Hamming nearest-neighbor geometry).

## What it earns

Two local legs, exact tuple/set and JAX mask/matrix, agree that recomputation on
the current survivor set is necessary. A relabelled or edge-restricted stale
geometry is detectably wrong.

It does not earn smooth manifold status, formal admission, physics, bridge or
axis claims, or any promotion above `scratch_diagnostic`.
