# QUARANTINE_EXPLORATORY: qit_dual_engine_live_v0

classification='scratch_diagnostic'; promotion_allowed=false.

Builds the eps-sheet direct/conjugated dual sheet-loop over one shared 3q world fixture. sheet-D loop is the eps-sheet direct loop: terrains 0-3 x {Ti,Fi}. sheet-C loop is the eps-sheet conjugated loop: terrains 4-7 x {Te,Fe}. Each sheet loop has its own 8x8 belief, action loop, and spinor-memory bit, while both consume the same fixture outcomes.

owner doctrine reads this partition as L/R chirality loops; that mapping is interpretive, not computed here.

These are two sheet-restricted belief/action loops. They are NOT Type-1/Type-2 engines at full operator+geometry depth doing distinct per-stage work; that build does not exist yet.

Boundary: chosen actions feed only the next belief predict; world outcomes remain fixture-driven.

`efe_scores_8` is a schema-stable legacy field name; the quantity is the cost surrogate, not active-inference EFE.

Directory name and emitted `engine_id` field values stay as-is for schema stability.

The existing `qit_live_loop_3q_v1` stage order comes from `engines/oracle_targets_3q.py` native conventions: `(0,Ti),(0,Fi),(1,Ti),(1,Fi),(2,Te),(2,Fe),(3,Te),(3,Fe),(4,Ti),(4,Fi),(5,Ti),(5,Fi),(6,Te),(6,Fe),(7,Te),(7,Fe)`. That order is not the pinned eps-sheet direct/conjugated partition from `sixteen_stage_engine_schedule_sim.py` lines 57-83. This sim therefore constructs the pinned eps-sheet direct/conjugated stages by `(terrain,op)` labels with the same 3q generator/operator functions, and records which rows do or do not have a v1.1 native-stage index.

Run:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/qit_dual_engine_live_v0/qit_dual_engine_live_v0.py --fresh
```

Outputs land in `results/live_300/`:

- `world_fixture.json`
- `numpy_oracle_loop_engine_D.jsonl`
- `numpy_oracle_loop_engine_C.jsonl`
- `julia_loop_engine_D.jsonl`
- `julia_loop_engine_C.jsonl`
- `parity_report.json`
- `sheet_gap_summary.json`
- `RESULTS.md`
