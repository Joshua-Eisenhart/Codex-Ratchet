# Sedenion Witness Convention Row 2026-06-10

Status: convention guard only. No packet is edited or promoted by this receipt.

## Doubling Conventions

| Label | Parent table / basis order | Doubling rule |
| --- | --- | --- |
| S9 committed packet convention | Cayley-Dickson `R -> C -> H -> O -> S` built from the packet basis order in `geo_s9_octonionic_hopf_stack_v0` | `(a,b)(c,d) = (a*c - conj(d)*b, d*a + b*conj(c))` |
| Bloch packet convention | Canon algebra artifact octonion parent table imported by `bloch_root_admissibility_discriminator_v0`, then Cayley-Dickson doubled | `(a,b)(c,d) = (a*c - conj(d)*b, d*a + b*conj(c))` |

## Recomputed Products

| Convention | `(e1+e10)(e4+e13)` | `(e1+e10)(e5+e14)` |
| --- | --- | --- |
| S9 committed packet convention | `e5 - e7 + e12 - e14`, `norm^2=4`, nonzero | `0`, `norm^2=0`, zero divisor |
| Bloch packet convention | `0`, `norm^2=0`, zero divisor | `e4 - e6 - e13 + e15`, `norm^2=4`, nonzero |

Recompute basis: exact integer Cayley-Dickson multiplication with the displayed rule. For the S9 row, the sedenion table was rebuilt from `R`; for the Bloch row, the sedenion table was rebuilt by doubling `system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json`'s octonion table.

## Binding Guidance

Future sedenion witnesses must pin both the doubling rule and the basis order / parent octonion table. Never cite a zero-divisor spelling without its convention. The invariant cross-packet claim is sedenion norm/fiber-law failure, not a universal index spelling for the zero-divisor pair.

Cross-references:

- S9 octonionic packet commit `17d4698ab`, especially `system_v6/sims/geo_s9_octonionic_hopf_stack_v0/geo_s9_octonionic_hopf_stack_v0_jax.py` and its audit row.
- `system_v6/sims/bloch_root_admissibility_discriminator_v0/audit_verdict.md`, especially the convention notes at lines 341 and 373.
