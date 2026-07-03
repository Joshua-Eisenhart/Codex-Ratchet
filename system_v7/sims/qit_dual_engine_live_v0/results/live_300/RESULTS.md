# QUARANTINE_EXPLORATORY: qit_dual_engine_live_v0 results

classification='scratch_diagnostic'; promotion_allowed=false.

owner doctrine reads this partition as L/R chirality engines; that mapping is interpretive, not computed here.

Engine D: eps-sheet direct, terrains 0-3 x {Ti,Fi}. Engine C: eps-sheet conjugated, terrains 4-7 x {Te,Fe}. Both consume the same world fixture and maintain separate 8x8 beliefs plus separate spinor-memory bits.

## Verdicts

- Parity passed: `True` with numeric bar `1e-09`.
- Action matches D: `300/300`.
- Action matches C: `300/300`.
- Sheet-engines diverge by trace gap: `True`.
- Surprise profiles diverge: `True`.
- Entropy coherent: `True`.
- Memory bits differ by sheet: `True`.

## Parity

- Max belief_pauli_63 abs dev: `4.030109579389318e-14`.
- Max surprise_bits abs dev: `3.1459279625778436e-12`.
- Max fe_gradient abs dev: `3.149480676256644e-12`.
- Max entropy_bits abs dev: `3.730349362740526e-14`.
- Max efe_scores_8 abs dev: `1.1457501614131615e-13`.
- Max sheet_gap_trace_distance abs dev: `7.216449660063518e-15`.
- Max sheet_gap_abs_surprise_delta abs dev: `3.142375248899043e-12`.
- Max memory_bit_fidelity abs dev: `2.3647750424515834e-14`.

## Sheet Gap

- Trace distance min/mean/max/final: `0.0` / `0.25904396557395215` / `0.6367990145139109` / `0.6367990145139109`.
- |surprise_D - surprise_C| min/mean/max/final: `0.0` / `2.7487216574755866` / `10.283387018266158` / `4.345428045862478`.

## Memory

- D fidelity at read ticks: `{'0': 1.0, '50': 1.0, '100': 1.0, '150': 1.0, '200': 1.0, '250': 1.0, '299': 1.0}`.
- C fidelity at read ticks: `{'0': 1.0, '50': 0.5000000000000001, '100': 0.0, '150': 0.4999999999999999, '200': 1.0, '250': 0.5000000000000001, '299': 0.14644660940672632}`.

## Runtimes

- numpy_oracle_loop: wall `1.4313682499341667`, substrate total `1.160367916803807`.
- julia_loop: wall `13.518810166977346`, substrate total `2.7965423749999996`.

## Boundaries

- This is scratch diagnostic parity evidence only.
- No promotion, admission, bridge, axis, or chirality computation claim is made.
- The eps-sheet direct/conjugated naming is the computed partition; L/R is only the owner-doctrine interpretation line above.
- Fixture sha256: `30f7227cf75f3c61f0568d2116024add8a6f668d7c1da5089e501a9cd0d67cf6`.
