# Torus/Chirality Evidence Loop Results

- generated_utc: `2026-04-14T11:53:41Z`
- do_not_promote: `True`

## Verdicts
- **Torus placement matters**: `True`
- **Chirality split matters**: `True`

## Per-Run Summary

| Engine | Torus | ΔΦ_L | ΔΦ_R | Chirality | Entropy |
|--------|-------|------|------|-----------|---------|
| Type-1 | default  | -0.9931 | -0.9931 | 0.7298 | 0.9989 |
| Type-1 | inner    | -0.7329 | -0.7329 | 0.7800 | 0.9515 |
| Type-1 | clifford | -0.9931 | -0.9931 | 0.7298 | 0.9989 |
| Type-1 | outer    | -0.7320 | -0.7320 | 0.7789 | 0.9524 |
| Type-2 | default  | -1.0768 | -1.0768 | 0.6876 | 0.9996 |
| Type-2 | inner    | -0.7485 | -0.7485 | 0.7566 | 0.9788 |
| Type-2 | clifford | -1.0768 | -1.0768 | 0.6876 | 0.9996 |
| Type-2 | outer    | -0.7459 | -0.7459 | 0.7562 | 0.9800 |

## Axis Spread (Torus Effect)

### Type-1
- `Ax0_hemisphere`: 0.000000
- `Ax0_torus_entropy`: 0.000000
- `GA0_entropy`: 0.047387
- `GA1_boundary`: 0.043696
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.050151
- `GA4_variance`: 0.530589
- `GA5_coupling`: 0.135837
- Max spread: `0.530589`

### Type-2
- `Ax0_hemisphere`: 0.000000
- `Ax0_torus_entropy`: 0.000000
- `GA0_entropy`: 0.020861
- `GA1_boundary`: 0.040397
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.068974
- `GA4_variance`: 0.394029
- `GA5_coupling`: 0.118366
- Max spread: `0.394029`

## Engine Type Differences (at same torus)

### inner
- `Ax0_hemisphere`: 0.000000
- `Ax0_torus_entropy`: 0.000000
- `GA0_entropy`: 0.027287
- `GA1_boundary`: 0.024414
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.023408
- `GA4_variance`: 0.195113
- `GA5_coupling`: 0.072275
- Chirality diff: `0.023408`

### clifford
- `Ax0_hemisphere`: 0.000000
- `Ax0_torus_entropy`: 0.000000
- `GA0_entropy`: 0.000761
- `GA1_boundary`: 0.021115
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.042231
- `GA4_variance`: 0.058553
- `GA5_coupling`: 0.054804
- Chirality diff: `0.042231`

### outer
- `Ax0_hemisphere`: 0.000000
- `Ax0_torus_entropy`: 0.000000
- `GA0_entropy`: 0.027615
- `GA1_boundary`: 0.025444
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.022786
- `GA4_variance`: 0.201811
- `GA5_coupling`: 0.071734
- Chirality diff: `0.022786`

### default
- `Ax0_hemisphere`: 0.000000
- `Ax0_torus_entropy`: 0.000000
- `GA0_entropy`: 0.000761
- `GA1_boundary`: 0.021115
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.042231
- `GA4_variance`: 0.058553
- `GA5_coupling`: 0.054804
- Chirality diff: `0.042231`

