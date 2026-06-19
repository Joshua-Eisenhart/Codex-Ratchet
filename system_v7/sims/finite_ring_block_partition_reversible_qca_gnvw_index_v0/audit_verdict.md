# Audit verdict - finite_ring_block_partition_reversible_qca_gnvw_index_v0

Classification: `scratch_diagnostic`
promotion_allowed: `false`
formal_admission_allowed: `false`

This directory builds one small finite-ring reversible QCA diagnostic for the GNVW support-algebra index. The ring has `N=8` qubit cells, the true periodic odd bond `(7,0)`, and an oriented local cut `3|4`.

The chirality-bearing rules now use explicit adjacent-SWAP block circuits on the same periodic ring operator used by the reversibility checks:

| Rule | SWAP schedule |
|---|---|
| `right_shift` | `(7,0) -> (6,7) -> (5,6) -> (4,5) -> (3,4) -> (2,3) -> (1,2)` |
| `left_shift` | `(1,2) -> (2,3) -> (3,4) -> (4,5) -> (5,6) -> (6,7) -> (7,0)` |

Each leg conjugates Pauli support vectors through these schedules using the same `circuit_image` path used by the CZ/CNOT brickwork. The shift rules do not return a translated generator directly. The support-overlap GF(2) rank flow across the cut produces the sign and magnitude.

Expected one-step GNVW controls:

| Rule | index units of log(d) | log value |
|---|---:|---:|
| `left_shift` | `-1` | `-log(2)` |
| `right_shift` | `1` | `log(2)` |
| `identity` | `0` | `0` |
| `finite_depth_local_circuit` | `0` | `0` |
| `non_shift_partitioned` | `0` | `0` |

The shift-by-k emergence test composes the same block circuit k times and uses a k-cell collar around the cut. This is an oriented local-cut flow diagnostic: `right_shift` counts left-collar generators transported across `3|4` to the right, `left_shift` counts right-collar generators transported across `3|4` to the left, and the opposite ring cut is not subtracted into this local-cut measurement. Required values are:

| k | `left_shift` | `right_shift` |
|---:|---:|---:|
| 1 | `-1` | `1` |
| 2 | `-2` | `2` |
| 3 | `-3` | `3` |

The index operator and reversibility operator are now the same finite object: `N=8`, `EVEN_BONDS=[(0,1),(2,3),(4,5),(6,7)]`, `ODD_BONDS=[(1,2),(3,4),(5,6),(7,0)]`, and the same shift schedules. The lifted `POSITIONS=0..8` / `(7,8)` open-line construction is gone.

The JAX leg keeps `jax` load-bearing for batched index computation. z3 and cvc5 are honestly demoted to `supportive`: they still run a sign sanity check, but they are not labeled structural proof and are not in `aligned_packages_load_bearing`.

The three computation styles remain distinct:

| Engine | style |
|---|---|
| Julia | `exact_permutation_support_algebra` |
| JAX | `vmap_batched_index_plus_smt_chirality_flip` |
| PyTorch | `dense_tensor_reversibility_and_index` |

This remains a finite periodic-ring scratch diagnostic, not a formal GNVW proof or promotion artifact.
