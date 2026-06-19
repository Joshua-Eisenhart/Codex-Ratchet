# audit_verdict - region_discovery_from_observables_v0

```yaml
classification: scratch_diagnostic
promotion_allowed: false
formal_admission_allowed: false
does_not_self_upgrade: true
ladder_reached: passes local rerun
builder: Codex controller-local builder; this is not a fresh fleet audit
```

## What this sim is

Finite Manifold-tower L12 region discovery from observables only. The probe set is a `10 x 12`
finite grid. Each cell has integer observable readouts `O(p) = (o0, o1, o2)`. No terrain labels,
hidden target labels, or prewritten region classes enter the computation.

The named relation is explicit:

`observable_threshold_component_equivalence_v0`: `p equiv_{O,tau,A4} q` iff
`sigma_tau(O(p)) = sigma_tau(O(q))` and there is a 4-neighbor path from `p` to `q` whose every cell
has that same threshold signature.

The threshold signature is:

`sigma_tau(O(p)) = (o0(p) <= 0, o1(p) >= 0, o2(p) >= 0)`.

## Why it is not label-smuggling

The base quotient has eight non-universal threshold signatures and eight connected components. The
cell memberships are discovered from observable threshold values plus adjacency.

The structure hash is a PROJECTION of the full, label-carrying discovery dict onto structural keys
(`signature_code`, `min_cell_id`, `size`, `cells`, `bbox_xyxy`, boundary edges, cell membership). It
is no longer hand-built from a separately curated label-free payload. Because the projection is taken
from the same dict that carries `display_label`, a label leak into any structural field would change
the hash under a shuffle. A leak-injection check confirms both legs flip
`label_shuffle_structure_invariant` to False when a display label is forced into a structural field,
so the control is genuinely could-fail, not by-construction.

`no_terrain_labels_consumed_in_region_computation` replaces a former hardcoded `no_terrain_labels_used
= True` self-certification. It is computed at runtime by discovering the same observables under two
different label maps (`DEFAULT_LABELS`, `SHUFFLED_LABELS`) and comparing the structural projection
byte-for-byte; it flips to False if labels contaminate the region computation.

The label-shuffle control permutes only display names attached to signatures. It changes the names
but leaves the region structure hash invariant. This control is not allowed to satisfy the value
gate.

## Genuine discriminator

The value-change control changes actual observable data: it adds `+10` to `o0` on a finite mask of
probe cells while leaving thresholds, adjacency, and display labels unchanged. That recomputation
changes six threshold memberships, changes the component count from `8` to `10`, and changes the
boundary-edge set by `17` edges. If the regions were not forced by readout values, this control
would not move the quotient.

## What this earns

Two local legs agree: exact numpy/stdlib BFS and JAX fixed-point min-label propagation. They agree on
the inequality regions, connected components, cell memberships, quotient structure hashes, label
shuffle invariance, and value-perturbation boundary movement.

It does not earn formal admission, smooth manifold claims, terrain segmentation, or promotion beyond
`scratch_diagnostic`.
