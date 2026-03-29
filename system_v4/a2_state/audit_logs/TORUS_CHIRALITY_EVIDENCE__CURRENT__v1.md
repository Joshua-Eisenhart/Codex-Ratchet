# Torus/Chirality Evidence Loop Results

- generated_utc: `2026-03-29T09:40:45Z`
- do_not_promote: `True`

## Verdicts
- **Torus placement matters**: `True`
- **Chirality split matters**: `True`

## Per-Run Summary

| Engine | Torus | ΔΦ_L | ΔΦ_R | Chirality | Entropy |
|--------|-------|------|------|-----------|---------|
| Type-1 | default  | -0.2286 | -0.2940 | 0.8272 | 0.9680 |
| Type-1 | inner    | -0.0668 | -0.2231 | 0.8961 | 0.9546 |
| Type-1 | clifford | -0.2286 | -0.2940 | 0.8272 | 0.9680 |
| Type-1 | outer    | -0.4741 | -0.4191 | 0.6572 | 0.9865 |
| Type-2 | default  | -0.2680 | -0.2892 | 0.8172 | 0.9724 |
| Type-2 | inner    | -0.0862 | -0.2153 | 0.9005 | 0.9635 |
| Type-2 | clifford | -0.2680 | -0.2892 | 0.8172 | 0.9724 |
| Type-2 | outer    | -0.5584 | -0.4357 | 0.5852 | 0.9850 |

## Axis Spread (Torus Effect)

### Type-1
- `GA0_entropy`: 0.031925
- `GA1_boundary`: 0.111807
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.238916
- `GA4_variance`: 0.137565
- `GA5_coupling`: 0.301667
- Max spread: `0.301667`

### Type-2
- `GA0_entropy`: 0.021575
- `GA1_boundary`: 0.104965
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.315338
- `GA4_variance`: 0.095234
- `GA5_coupling`: 0.346269
- Max spread: `0.346269`

## Engine Type Differences (at same torus)

### inner
- `GA0_entropy`: 0.008855
- `GA1_boundary`: 0.000028
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.004446
- `GA4_variance`: 0.053771
- `GA5_coupling`: 0.005829
- Chirality diff: `0.004446`

### clifford
- `GA0_entropy`: 0.004419
- `GA1_boundary`: 0.035191
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.010098
- `GA4_variance`: 0.025569
- `GA5_coupling`: 0.017304
- Chirality diff: `0.010098`

### outer
- `GA0_entropy`: 0.001495
- `GA1_boundary`: 0.028349
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.071976
- `GA4_variance`: 0.011440
- `GA5_coupling`: 0.050431
- Chirality diff: `0.071976`

### default
- `GA0_entropy`: 0.004419
- `GA1_boundary`: 0.035191
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.010098
- `GA4_variance`: 0.025569
- `GA5_coupling`: 0.017304
- Chirality diff: `0.010098`

