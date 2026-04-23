# [Live runtime truth] 64-Step Runtime Engine Table

This is the live execution table generated from `engine_core.py`.
It is not the same object as the 64 structural state-space scaffold.

Shape:
- `2 engine types × 8 terrains × 4 operator slots = 64 runtime steps`
- Type 1 and Type 2 run the same operator order per terrain
- What changes is dominance/strength by loop and type
- This table materializes the current live `4-operator-slot` runtime, not a fully first-class `8 signed operator` basis

| Step | Type | Stage | Terrain | Loop | Exp | Open | Slot | Operator | Dominant | Default Ax0 Target | Default Strength |
|---:|---:|---:|---|---|---:|---:|---:|---|---:|---:|---:|
| 0 | 1 | 0 | Se_f | fiber | 1 | 1 | 0 | Ti | 0 | 0.350000 | 0.163500 |
| 1 | 1 | 0 | Se_f | fiber | 1 | 1 | 1 | Fe | 0 | 0.650000 | 0.163500 |
| 2 | 1 | 0 | Se_f | fiber | 1 | 1 | 2 | Te | 1 | 0.850000 | 0.605000 |
| 3 | 1 | 0 | Se_f | fiber | 1 | 1 | 3 | Fi | 1 | 0.550000 | 0.485000 |
| 4 | 1 | 1 | Si_f | fiber | 0 | 0 | 0 | Ti | 0 | 0.050000 | 0.190500 |
| 5 | 1 | 1 | Si_f | fiber | 0 | 0 | 1 | Fe | 0 | 0.250000 | 0.127500 |
| 6 | 1 | 1 | Si_f | fiber | 0 | 0 | 2 | Te | 1 | 0.450000 | 0.485000 |
| 7 | 1 | 1 | Si_f | fiber | 0 | 0 | 3 | Fi | 1 | 0.150000 | 0.605000 |
| 8 | 1 | 2 | Ne_f | fiber | 1 | 0 | 0 | Ti | 0 | 0.200000 | 0.177000 |
| 9 | 1 | 2 | Ne_f | fiber | 1 | 0 | 1 | Fe | 0 | 0.500000 | 0.150000 |
| 10 | 1 | 2 | Ne_f | fiber | 1 | 0 | 2 | Te | 1 | 0.700000 | 0.560000 |
| 11 | 1 | 2 | Ne_f | fiber | 1 | 0 | 3 | Fi | 1 | 0.400000 | 0.530000 |
| 12 | 1 | 3 | Ni_f | fiber | 0 | 1 | 0 | Ti | 0 | 0.100000 | 0.186000 |
| 13 | 1 | 3 | Ni_f | fiber | 0 | 1 | 1 | Fe | 0 | 0.400000 | 0.141000 |
| 14 | 1 | 3 | Ni_f | fiber | 0 | 1 | 2 | Te | 1 | 0.600000 | 0.530000 |
| 15 | 1 | 3 | Ni_f | fiber | 0 | 1 | 3 | Fi | 1 | 0.300000 | 0.560000 |
| 16 | 1 | 4 | Se_b | base | 1 | 1 | 0 | Ti | 1 | 0.500000 | 0.500000 |
| 17 | 1 | 4 | Se_b | base | 1 | 1 | 1 | Fe | 1 | 0.800000 | 0.590000 |
| 18 | 1 | 4 | Se_b | base | 1 | 1 | 2 | Te | 0 | 0.950000 | 0.190500 |
| 19 | 1 | 4 | Se_b | base | 1 | 1 | 3 | Fi | 0 | 0.700000 | 0.132000 |
| 20 | 1 | 5 | Si_b | base | 0 | 0 | 0 | Ti | 1 | 0.100000 | 0.620000 |
| 21 | 1 | 5 | Si_b | base | 0 | 0 | 1 | Fe | 1 | 0.400000 | 0.470000 |
| 22 | 1 | 5 | Si_b | base | 0 | 0 | 2 | Te | 0 | 0.600000 | 0.159000 |
| 23 | 1 | 5 | Si_b | base | 0 | 0 | 3 | Fi | 0 | 0.300000 | 0.168000 |
| 24 | 1 | 6 | Ne_b | base | 1 | 0 | 0 | Ti | 1 | 0.350000 | 0.545000 |
| 25 | 1 | 6 | Ne_b | base | 1 | 0 | 1 | Fe | 1 | 0.650000 | 0.545000 |
| 26 | 1 | 6 | Ne_b | base | 1 | 0 | 2 | Te | 0 | 0.850000 | 0.181500 |
| 27 | 1 | 6 | Ne_b | base | 1 | 0 | 3 | Fi | 0 | 0.550000 | 0.145500 |
| 28 | 1 | 7 | Ni_b | base | 0 | 1 | 0 | Ti | 1 | 0.250000 | 0.575000 |
| 29 | 1 | 7 | Ni_b | base | 0 | 1 | 1 | Fe | 1 | 0.550000 | 0.515000 |
| 30 | 1 | 7 | Ni_b | base | 0 | 1 | 2 | Te | 0 | 0.750000 | 0.172500 |
| 31 | 1 | 7 | Ni_b | base | 0 | 1 | 3 | Fi | 0 | 0.450000 | 0.154500 |
| 32 | 2 | 0 | Se_f | fiber | 1 | 1 | 0 | Ti | 1 | 0.300000 | 0.560000 |
| 33 | 2 | 0 | Se_f | fiber | 1 | 1 | 1 | Fe | 1 | 0.600000 | 0.530000 |
| 34 | 2 | 0 | Se_f | fiber | 1 | 1 | 2 | Te | 0 | 0.800000 | 0.177000 |
| 35 | 2 | 0 | Se_f | fiber | 1 | 1 | 3 | Fi | 0 | 0.500000 | 0.150000 |
| 36 | 2 | 1 | Si_f | fiber | 0 | 0 | 0 | Ti | 1 | 0.050000 | 0.635000 |
| 37 | 2 | 1 | Si_f | fiber | 0 | 0 | 1 | Fe | 1 | 0.200000 | 0.410000 |
| 38 | 2 | 1 | Si_f | fiber | 0 | 0 | 2 | Te | 0 | 0.400000 | 0.141000 |
| 39 | 2 | 1 | Si_f | fiber | 0 | 0 | 3 | Fi | 0 | 0.100000 | 0.186000 |
| 40 | 2 | 2 | Ne_f | fiber | 1 | 0 | 0 | Ti | 1 | 0.150000 | 0.605000 |
| 41 | 2 | 2 | Ne_f | fiber | 1 | 0 | 1 | Fe | 1 | 0.450000 | 0.485000 |
| 42 | 2 | 2 | Ne_f | fiber | 1 | 0 | 2 | Te | 0 | 0.650000 | 0.163500 |
| 43 | 2 | 2 | Ne_f | fiber | 1 | 0 | 3 | Fi | 0 | 0.350000 | 0.163500 |
| 44 | 2 | 3 | Ni_f | fiber | 0 | 1 | 0 | Ti | 1 | 0.050000 | 0.635000 |
| 45 | 2 | 3 | Ni_f | fiber | 0 | 1 | 1 | Fe | 1 | 0.350000 | 0.455000 |
| 46 | 2 | 3 | Ni_f | fiber | 0 | 1 | 2 | Te | 0 | 0.550000 | 0.154500 |
| 47 | 2 | 3 | Ni_f | fiber | 0 | 1 | 3 | Fi | 0 | 0.250000 | 0.172500 |
| 48 | 2 | 4 | Se_b | base | 1 | 1 | 0 | Ti | 0 | 0.550000 | 0.145500 |
| 49 | 2 | 4 | Se_b | base | 1 | 1 | 1 | Fe | 0 | 0.850000 | 0.181500 |
| 50 | 2 | 4 | Se_b | base | 1 | 1 | 2 | Te | 1 | 0.950000 | 0.635000 |
| 51 | 2 | 4 | Se_b | base | 1 | 1 | 3 | Fi | 1 | 0.750000 | 0.425000 |
| 52 | 2 | 5 | Si_b | base | 0 | 0 | 0 | Ti | 0 | 0.150000 | 0.181500 |
| 53 | 2 | 5 | Si_b | base | 0 | 0 | 1 | Fe | 0 | 0.450000 | 0.145500 |
| 54 | 2 | 5 | Si_b | base | 0 | 0 | 2 | Te | 1 | 0.650000 | 0.545000 |
| 55 | 2 | 5 | Si_b | base | 0 | 0 | 3 | Fi | 1 | 0.350000 | 0.545000 |
| 56 | 2 | 6 | Ne_b | base | 1 | 0 | 0 | Ti | 0 | 0.400000 | 0.159000 |
| 57 | 2 | 6 | Ne_b | base | 1 | 0 | 1 | Fe | 0 | 0.700000 | 0.168000 |
| 58 | 2 | 6 | Ne_b | base | 1 | 0 | 2 | Te | 1 | 0.900000 | 0.620000 |
| 59 | 2 | 6 | Ne_b | base | 1 | 0 | 3 | Fi | 1 | 0.600000 | 0.470000 |
| 60 | 2 | 7 | Ni_b | base | 0 | 1 | 0 | Ti | 0 | 0.300000 | 0.168000 |
| 61 | 2 | 7 | Ni_b | base | 0 | 1 | 1 | Fe | 0 | 0.600000 | 0.159000 |
| 62 | 2 | 7 | Ni_b | base | 0 | 1 | 2 | Te | 1 | 0.800000 | 0.590000 |
| 63 | 2 | 7 | Ni_b | base | 0 | 1 | 3 | Fi | 1 | 0.500000 | 0.500000 |

## Notes

- This table documents current runtime semantics only.
- It should be read alongside the structural 64-state table, not as a replacement for it.
- If engine semantics change in `engine_core.py`, regenerate this table.
- Structural bit assignments and signed-operator closure remain bridge-layer hypotheses unless decoded back from runtime state.
