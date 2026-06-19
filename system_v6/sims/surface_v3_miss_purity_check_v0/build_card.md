# BUILD CARD - surface_v3_miss_purity_check_v0

## Scope

One micro-check for the surface v3 miss vs the alt-view purity-shrinkage explanation. This packet is file-disjoint under `system_v6/sims/surface_v3_miss_purity_check_v0/` and does not edit or regenerate `spinor_network_surface_v3`.

## Authority

- Surface v3 authority: commit `b02444162`, where the preserved miss is `entangled_nonproduct:A33_x00_y00_zm10`.
- Alt-view authority: receipt commit `731b61933`, where the proposed explanation is that the entangled pattern's single-site reduced states are mixed and therefore shrink radially inside the Bloch ball.
- Consumed source/result surfaces are hash-pinned in `results/surface_v3_miss_purity_check_v0_results.json`.

## Check

The committed v3 construction defines:

```text
entangled_nonproduct = cos(0.31)|0000> + sin(0.31)exp(i*0.37)|1111>
```

This packet computes each single-site reduced density matrix by finite partial trace, then records:

- the exact diagonal marginal `diag(cos(0.31)^2, sin(0.31)^2)`;
- Bloch vector `(0, 0, cos(2*0.31))`;
- Bloch radius `abs(cos(2*0.31))`;
- the v3 predicted `-z` pole-cell radius band, with the strict nearest-neighbor radial-band discriminator kept separate from the weaker mixed-marginal `< 1` check;
- the corrected A33 cell and whether v3 recovered it.

Cheap discriminator included: vary the relative GHZ phase over `0`, `0.37`, and `pi`; if single-site marginals and cells are invariant, the phase-gauge mismatch explanation is not supported by this cheap check.

Expected nuance: the mixed marginal confirms the alt-view's purity-shrinkage premise (`radius < 1`), but under the packet's nearest-neighbor A33 pole-band convention the radius is not below the pole-cell lower boundary. The decisive correction is therefore the actual reduced-state cell (`+z`) versus the pre-registered miss cell (`-z`), and v3 did recover the corrected `+z` cell.

## Boundary

Classification is `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`. This packet may confirm or reject the alt-view explanation for the v3 miss. It cannot promote the surface doctrine, the QIT engine, or any physics/admission claim.

## Commands

```bash
python3 system_v6/sims/surface_v3_miss_purity_check_v0/surface_v3_miss_purity_check_v0.py
python3 system_v6/sims/surface_v3_miss_purity_check_v0/validate_surface_v3_miss_purity_check_v0.py
```
