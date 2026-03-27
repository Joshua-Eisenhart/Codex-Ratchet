# Torus/Chirality Evidence Loop Results

- generated_utc: `2026-03-27T00:20:57Z`
- do_not_promote: `True`

## Verdicts
- **Torus placement matters**: `True`
- **Chirality split matters**: `True`

## Per-Run Summary

| Engine | Torus | ΔΦ_L | ΔΦ_R | Chirality | Entropy |
|--------|-------|------|------|-----------|---------|
| Type-1 | default  | -0.5113 | -0.4999 | 0.5814 | 0.9906 |
| Type-1 | inner    | -0.2326 | -0.5285 | 0.7139 | 0.9788 |
| Type-1 | clifford | -0.5113 | -0.4999 | 0.5814 | 0.9906 |
| Type-1 | outer    | -0.6708 | -0.5863 | 0.3303 | 0.9884 |
| Type-2 | default  | -0.2718 | -0.3132 | 0.7997 | 0.9661 |
| Type-2 | inner    | -0.0857 | -0.2280 | 0.8896 | 0.9549 |
| Type-2 | clifford | -0.2718 | -0.3132 | 0.7997 | 0.9661 |
| Type-2 | outer    | -0.5634 | -0.4691 | 0.5548 | 0.9833 |

## Axis Spread (Torus Effect)

### Type-1
- `GA0_entropy`: 0.011820
- `GA1_boundary`: 0.099410
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.383660
- `GA4_variance`: 0.207149
- `GA5_coupling`: 0.247989
- Max spread: `0.383660`

### Type-2
- `GA0_entropy`: 0.028475
- `GA1_boundary`: 0.100762
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.334811
- `GA4_variance`: 0.062617
- `GA5_coupling`: 0.359364
- Max spread: `0.359364`

## Engine Type Differences (at same torus)

### inner
- `GA0_entropy`: 0.023959
- `GA1_boundary`: 0.001295
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.175639
- `GA4_variance`: 0.359615
- `GA5_coupling`: 0.223698
- Chirality diff: `0.175639`

### clifford
- `GA0_entropy`: 0.024567
- `GA1_boundary`: 0.002070
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.218284
- `GA4_variance`: 0.140490
- `GA5_coupling`: 0.213082
- Chirality diff: `0.218284`

### outer
- `GA0_entropy`: 0.005048
- `GA1_boundary`: 0.003422
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.224488
- `GA4_variance`: 0.241291
- `GA5_coupling`: 0.112323
- Chirality diff: `0.224488`

### default
- `GA0_entropy`: 0.024567
- `GA1_boundary`: 0.002070
- `GA2_scale`: 0.000000
- `GA3_chirality`: 0.218284
- `GA4_variance`: 0.140490
- `GA5_coupling`: 0.213082
- Chirality diff: `0.218284`

