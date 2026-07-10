# finite_probe_behavioral_object_engine_v0

Preregistered three-engine capability anchor for exact behavioral objects,
finite attractors, and learned presentation-invariant reidentification.

## Object Definition

A state is not assigned an object label in advance. Two six-bit ring states are
the same object at refinement depth `d` only when their declared probe outputs
match and every action history through that depth leads to matching probe
outputs. Stable partition refinement computes the behavioral quotient.

The fixture uses elementary cellular-automaton rules 30 and 110 as two action
generators. They are finite, nonlinear, translation-equivariant, and
noncommuting. The probes are Hamming weight and periodic domain-wall count, so
they do not name a privileged site.

## Engine Roles

- Julia is the semantic owner: exact partition refinement, independent cyclic
  orbits, quotient transitions, SCCs, exact cycles, and basin cardinalities.
- JAX exhausts all states and bounded action histories, applies probe and
  transition mutations, and checks projection/evolution commutation in batch.
- PyTorch/PyG fits cyclic-orbit classes from ring graphs. Its held-out rows are
  isomorphic rotations and its pooling is relabel-invariant, so this measures
  topology-dependent fitting, not unseen-object generalization. It cannot
  certify exact objects, basins, or general perception.

No engine may read another engine's result. The final validator reconstructs
the finite fixture independently and checks each engine only within its role.

## Why This Has Teeth

The depth-zero two-probe quotient has 11 classes but is not a congruence: both
actions send members of some class to different successor classes. Refinement
must discover the stable 14-class quotient. A false projection, one mutated
transition, shuffled learning targets, and erased ring edges are registered
kills.

The cross-class transition mutation and shuffled-label control are sanity
checks because they are selected to fail. Edge erasure is the meaningful
PyTorch topology-dependence control. No executable engine-removal ablation has
yet earned role nonredundancy, so the packet-wide T9 verdict remains red.

Attractors are exact cycles of the two composite functional graphs. Clustering
and endpoint similarity have no authority.

## Ceiling

This packet can show exact finite behavioral-object and attractor computation,
plus topology-dependent orbit fitting on one fixture. It cannot show that the QIT engine
schedule is forced, that sixteen stages have unique personalities, that four
substages emerge, or that general perception, MMMs, ontologies, cross-domain
unification, physics, or consciousness has been achieved.

## Run

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v7/sims/finite_probe_behavioral_object_engine_v0/run_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/finite_probe_behavioral_object_engine_v0/run_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/finite_probe_behavioral_object_engine_v0/run_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/finite_probe_behavioral_object_engine_v0/validate_finite_probe_behavioral_object_engine_v0.py
```
