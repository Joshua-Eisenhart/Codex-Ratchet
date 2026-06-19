# Audit Verdict - surface_v3_miss_purity_check_v0

Bottom line: PASS_WITH_CAVEAT. The numerical check is sound: the committed v3 entangled pattern reduces to a mixed single-site state with Bloch vector `(0, 0, +0.8138784566625339)`, so the sign is `+z` and the corrected cell is `A33_x00_y00_zp10`. The caveat is binding: the v3 pre-registered structured score remains `3/4`; this packet explains the fourth miss as a prediction-label/sign error, not as a retroactive `4/4`.

## Verdict

- Verdict: `PASS_WITH_CAVEAT + post-hoc statistic guard`.
- Correct claim shape: `3/4 pre-registered stands; the 4th miss is adjudicated as prediction-label error, with recovery succeeding on the true reduced-state cell`.
- Do not upgrade: replacing the pre-registered `entangled_nonproduct:A33_x00_y00_zm10` target after inspection would violate the standards codex post-hoc statistic rule.

## Checks

1. Reduced-state recomputation from committed v3 construction: PASS.
   - Hash-pinned source: `system_v6/sims/spinor_network_surface_v3/spinor_network_surface_v3_jax.py`, sha256 `d446dc4df380c591f6df8d705dc5840e7734c98c2f4a264fd45e570dac1adfbe`.
   - Source construction is `theta = 0.31`, `state[0] = cos(theta)`, `state[15] = sin(theta) * exp(i*0.37)`.
   - Independent partial trace gives each site `rho = diag(0.906939228331267, 0.09306077166873304)`, Bloch vector `(0, 0, 0.8138784566625339)`, radius `0.8138784566625339`, purity `0.8311990711096939`.
   - Packet result records the same formula and values: `bloch_radius_value = 0.8138784566625339`, `bloch_z_value = 0.8138784566625339`, and all per-site corrected cells are `A33_x00_y00_zp10`.

2. Committed v3 result recovery: PASS.
   - Exact v3 row: `pre_registered_structured_prediction.recovered_predicted_family_cell_pairs` contains `entangled_nonproduct:A33_x00_y00_zp10`.
   - The same row leaves `entangled_nonproduct:A33_x00_y00_zm10` in `missed_predicted_family_cell_pairs`.
   - Therefore v3 recovered the corrected `+z` cell but did not recover the originally predicted `-z` cell.

3. Post-hoc statistic discipline: PASS_WITH_CAVEAT.
   - The standards codex says post-hoc statistics are target sets selected after observing positives, and significant statistics bind only when the target set, seeds or prediction family, null, and scoring rule were predeclared.
   - The v3 envelope states `expected_predicted_pair_count = 4`, `recovered_predicted_pair_count = 3`, `recovered_fraction = 0.75`, and verdict `PARTIAL_PREDICTED_CELL_RECOVERY`.
   - The v3 plain reading explicitly says the pre-registered structured statistic recovers `3/4` and misses `entangled_nonproduct:A33_x00_y00_zm10`.

4. Alt-view adjudication: partial, with sign-flip as the actual resolution.
   - Purity-shrinkage survives only in the weak sense: the marginal is mixed and the radius is below the pure pole radius `1.0`.
   - The strict nearest-neighbor pole-band shrinkage discriminator is false: the `-z` pole-band floor is `0.75`, and `0.8138784566625339` is not below it.
   - The sign-label explanation survives: the reduced-state cell is `+z`, not the pre-registered `-z` miss.

## Citations

- `system_v6/sims/spinor_network_surface_v3/spinor_network_surface_v3_jax.py:61-70`: pre-registered entangled targets include both `A33_x00_y00_zm10` and `A33_x00_y00_zp10`.
- `system_v6/sims/spinor_network_surface_v3/spinor_network_surface_v3_jax.py:229-234`: committed entangled pattern construction.
- `system_v6/sims/surface_v3_miss_purity_check_v0/results/surface_v3_miss_purity_check_v0_results.json:107-123`: formula values for single-site rho, `cos(2*0.31)`, and radius.
- `system_v6/sims/surface_v3_miss_purity_check_v0/results/surface_v3_miss_purity_check_v0_results.json:126-252`: per-site reduced density matrices all have positive z radius and corrected `A33_x00_y00_zp10` cell.
- `system_v6/sims/surface_v3_miss_purity_check_v0/results/surface_v3_miss_purity_check_v0_results.json:284-296`: pole-cell radial band floor is `0.75`.
- `system_v6/sims/surface_v3_miss_purity_check_v0/results/surface_v3_miss_purity_check_v0_results.json:302-328`: packet extraction of v3 recovery/miss rows.
- `system_v6/sims/spinor_network_surface_v3/results/spinor_network_surface_v3_envelope_results.json:18250-18338`: exact pre-registered v3 structured statistic row.
- `system_v6/sims/spinor_network_surface_v3/results/spinor_network_surface_v3_envelope_results.json:18344-18360`: v3 plain reading preserves `3/4` partial fixed-prediction recovery.
- `system_v6/receipts/audit_standards_codex_v1.md:40-40`: post-hoc statistic species definition and binding rule.
- `system_v6/receipts/audit_standards_codex_v1.md:59-59`: no new subvariant may enter the adjudicated set after results are inspected.

## Commands Run

```bash
shasum -a 256 system_v6/sims/spinor_network_surface_v3/spinor_network_surface_v3_jax.py system_v6/sims/spinor_network_surface_v3/results/spinor_network_surface_v3_envelope_results.json system_v6/receipts/altviews_capability_and_surface_miss_20260612.md
```

```bash
python3 system_v6/sims/surface_v3_miss_purity_check_v0/validate_surface_v3_miss_purity_check_v0.py
```

```bash
python3 - <<'PY'
import math, cmath, numpy as np
N=4; DIM=2**N; theta=0.31; phase=0.37
state=np.zeros(DIM, dtype=np.complex128)
state[0]=math.cos(theta)
state[15]=math.sin(theta)*cmath.exp(1j*phase)
state=state/np.linalg.norm(state)
rho=np.outer(state, state.conj())
for keep in range(N):
    out=np.zeros((2,2), dtype=np.complex128)
    for a in range(2):
        for b in range(2):
            s=0j
            for rest in range(2**(N-1)):
                bits=[]; r=rest
                for i in range(N):
                    if i==keep:
                        bits.append(None)
                    else:
                        bits.append(r & 1); r >>= 1
                ket_bits=list(bits); bra_bits=list(bits)
                ket_bits[keep]=a; bra_bits[keep]=b
                ki=0; bi=0
                for bit in ket_bits: ki=(ki<<1)|bit
                for bit in bra_bits: bi=(bi<<1)|bit
                s += rho[ki, bi]
            out[a,b]=s
    sx=np.array([[0,1],[1,0]], complex)
    sy=np.array([[0,-1j],[1j,0]], complex)
    sz=np.array([[1,0],[0,-1]], complex)
    bloch=[float(np.real(np.trace(out @ p))) for p in (sx,sy,sz)]
    print(keep, out, bloch, math.sqrt(sum(x*x for x in bloch)), float(np.real(np.trace(out@out))))
print(math.cos(2*theta), abs(math.cos(2*theta)))
PY
```
