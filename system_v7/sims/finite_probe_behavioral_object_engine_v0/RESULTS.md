# Finite Behavioral-Object Engine Results

Classification: `scratch_diagnostic`

Packet-wide verdict: `RED_NONREDUNDANCY_UNEARNED_EXACT_CORE_SURVIVES`.

Independent validator label:
`EXACT_CORE_PLUS_TOPOLOGY_DEPENDENT_FIT_ONLY`. Artifact validation and all five
result-mutation tests pass; `all_scientific_gates_pass` remains `false`.

## Exact Object And Attractor Result

The exact Julia and JAX lanes independently compute one finite behavioral
fixture. Starting from Hamming weight and periodic domain-wall probes, partition
refinement moves from 11 to 14 classes after one action depth and then remains
stable through depth six. The stable partition exactly equals the 14 cyclic
rotation orbits of six-bit ring states.

This is an operational object construction: object identity is the stable
equivalence class under declared probes and both actions. It is not supplied as
a state label.

The 11-class depth-zero quotient is invalid dynamically. Both actions send
members of two raw classes to different successor classes. The stable
14-object quotient has exact induced action maps.

Rules 30 and 110 are order-sensitive on 56 of 64 states. Their two composite
orders each have five exact functional-graph attractors, but different basin
masses:

```text
A after B: [3, 7, 18, 18, 18]
B after A: [3, 13, 16, 16, 16]
```

No clustering or endpoint similarity defines these attractors.

## Runtime Truth

- Julia uses `Graphs.SimpleDiGraph`, `add_edge!`, and
  `strongly_connected_components` for the exact quotient graph/SCC receipt.
- JAX uses x64 `vmap`, `lax.fori_loop`, and `lax.scan` for exhaustive histories,
  quotient controls, rotations, and functional-graph traces.
- PyTorch/PyG uses directed `MessagePassing`, global pooling, deterministic
  optimization, and `torch.func.jacrev` on the learned fit.

All three result files are deterministic and byte-identical on repeated runs.

## Learned Lane

After a bounded architecture repair that left the preregistered fixture, split,
epochs, thresholds, and controls unchanged, PyTorch fits all 14 training orbit
representatives and all 50 held-out rotations. Erasing graph edges lowers
accuracy to `0.44`.

This does not establish general perception. Held-out states are isomorphic
presentations of training objects, and graph pooling is invariant to those
relabelings. The accepted statement is `topology-dependent orbit fitting`.

## Why The Packet Is Red

T9 required executable engine-removal nonredundancy. No such ablation was run.
Julia and JAX overlap on the exact finite core; PyTorch adds a learned fit but
its presentation test is not unseen-object generalization. Julia and JAX now
emit `all_pass:false` solely to preserve this unearned T9 boundary.

The cross-class transition mutation and shuffled-target control are also
sanity-only because they were selected to fail. They do not count as scientific
selection evidence.

## Ceiling

This is a capability anchor for finite probe-relative object construction,
exact quotient dynamics, exact finite attractors, and topology-dependent graph
fitting. It does not select or validate the QIT 16-by-4 schedule, unique engine
personalities, four substages, general AI perception, MMMs, ontologies,
cross-domain unification, Axis0, physics, or consciousness.
