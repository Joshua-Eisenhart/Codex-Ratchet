# qit_live_loop_v0 Results

QUARANTINE_EXPLORATORY.

- classification: `scratch_diagnostic`
- promotion_allowed: `false`
- ceiling: `runs / scratch_diagnostic`
- process status: explicitly NOT a sim per the gated process

## What Ran

- Live driver: `qit_live_loop_v0.py`
- Mechanics: imported `LevBridge.tick()` from `lev_bridge_sim.py`; minimally reimplemented reactive-risk + entropy cost surrogate action score (labeled EFE-analogue, not full active-inference EFE) from `agent_loop_sim.py` to avoid import-time demo execution.
- Ticks: `300`
- True regime shifts: `[100, 200]`
- local stream integrity check ok: `True` over `300` ticks

## Exact Numbers

- A stationary tail ticks 80-99 surprise max/mean/last: `0.0025` / `0.00223` / `0.0024`
- B stationary tail ticks 180-199 surprise max/mean/last: `0.0084` / `0.007685` / `0.0077`
- C drifting tail ticks 280-299 surprise max/mean/last: `0.0034` / `0.00178` / `0.0034`
- Shift spike tick 100: `0.0342`
- Shift spike tick 200: `1.53`
- Detector first dual tick: `100`
- Detector second dual tick global: `200`

## Honest Verdict

Detector fires near both true shift points. Stationary tails are near-zero by a <0.01 max-surprise diagnostic. Surprise spikes at abrupt shift tick 100; tick 200 starts a drift segment, so the detector report is interpreted as drift-onset detection, not a second abrupt-step proof.
