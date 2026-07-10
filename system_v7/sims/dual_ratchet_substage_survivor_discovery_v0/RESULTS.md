# Dual-Ratchet Substage Survivor Discovery v0 Results

Status: fresh local rerun passed at the packet's conditional ceiling.

The preregistered branch table is in `spec.json`. Julia and JAX independently
recomputed the candidate channels and terrain-relative measurements.

| Check | JAX | Julia |
|---|---:|---:|
| Main Pauli-registry classes | 4 | 4 |
| Main surviving candidates | 6 | 6 |
| Generic-axis classes | 8 | 8 |
| Generic surviving candidates | 10 | 10 |
| Conditional four-class quotient | true | true |
| Foundational four-substage emergence | false | false |
| History-dependent dual ratchet tested | false | false |
| Per-stage four substages earned | false | false |

The main and generic partitions, main checks, falsifier checks, and verdicts
agree across the two runtimes. The exact branch is
`conditional_pauli_registry_four_class_operator_quotient_only`.

The four classes are a conditional `2 x 2` product: contraction versus
isometry channel family, crossed with the terrain symmetry's transverse
`x/y` versus axial `z` orbit. Generic axes produce additional classes and are
the required kill control. Thus this packet does not earn a universal four,
the four operators' temporal order, native phase, Type-1/Type-2 behavior, or
the `16 x 4` engine.

Mechanical agreement receipt:
`results/dual_ratchet_substage_survivor_discovery_v0_agreement.json`.
