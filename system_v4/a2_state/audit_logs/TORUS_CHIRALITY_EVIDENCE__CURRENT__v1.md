# Torus/Chirality Evidence Loop Results

- generated_utc: `2026-04-06T06:00:38Z`
- do_not_promote: `True`

## Verdicts
- **Torus placement matters**: `True`
- **Chirality split matters**: `True`

## Per-Run Summary

| Engine | Torus | ΔΦ_L | ΔΦ_R | Chirality | Entropy |
|--------|-------|------|------|-----------|---------|
| Type-1 | default  | -0.5863 | -0.5863 | 0.8298 | 0.9986 |
| Type-1 | inner    | -0.5470 | -0.5470 | 0.8341 | 1.0000 |
| Type-1 | clifford | -0.5863 | -0.5863 | 0.8298 | 0.9986 |
| Type-1 | outer    | -0.5470 | -0.5470 | 0.8341 | 1.0000 |
| Type-2 | default  | -0.6152 | -0.6152 | 0.7529 | 0.9999 |
| Type-2 | inner    | -0.5578 | -0.5578 | 0.7701 | 1.0000 |
| Type-2 | clifford | -0.6152 | -0.6152 | 0.7529 | 0.9999 |
| Type-2 | outer    | -0.5577 | -0.5577 | 0.7701 | 1.0000 |

## Axis Spread (Torus Effect)

### Type-1
- `Ax0_hemisphere`: 0.000000
- `Ax0_torus_entropy`: 0.000000
- `GA0_entropy`: 0.001336
- `GA1_boundary`: 0.001052
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.004392
- `GA4_variance`: 0.086170
- `GA5_coupling`: 0.005576
- Max spread: `0.086170`

### Type-2
- `Ax0_hemisphere`: 0.000000
- `Ax0_torus_entropy`: 0.000000
- `GA0_entropy`: 0.000085
- `GA1_boundary`: 0.003207
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.017213
- `GA4_variance`: 0.019208
- `GA5_coupling`: 0.024721
- Max spread: `0.024721`

## Engine Type Differences (at same torus)

### inner
- `Ax0_hemisphere`: 0.000000
- `Ax0_torus_entropy`: 0.000000
- `GA0_entropy`: 0.000022
- `GA1_boundary`: 0.034664
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.063965
- `GA4_variance`: 0.005142
- `GA5_coupling`: 0.102161
- Chirality diff: `0.063965`

### clifford
- `Ax0_hemisphere`: 0.000000
- `Ax0_torus_entropy`: 0.000000
- `GA0_entropy`: 0.001273
- `GA1_boundary`: 0.038923
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.076830
- `GA4_variance`: 0.072104
- `GA5_coupling`: 0.121384
- Chirality diff: `0.076830`

### outer
- `Ax0_hemisphere`: 0.000000
- `Ax0_torus_entropy`: 0.000000
- `GA0_entropy`: 0.000017
- `GA1_boundary`: 0.034740
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.064064
- `GA4_variance`: 0.003337
- `GA5_coupling`: 0.102311
- Chirality diff: `0.064064`

### default
- `Ax0_hemisphere`: 0.000000
- `Ax0_torus_entropy`: 0.000000
- `GA0_entropy`: 0.001273
- `GA1_boundary`: 0.038923
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.076830
- `GA4_variance`: 0.072104
- `GA5_coupling`: 0.121384
- Chirality diff: `0.076830`

