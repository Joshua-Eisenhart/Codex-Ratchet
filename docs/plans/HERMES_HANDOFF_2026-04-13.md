# Hermes Handoff — 2026-04-13

## What was built this session

**Lane A — tool-capability probes (12 total, all `all_pass=True`):**
z3, cvc5, sympy, pytorch, rustworkx, pyg, xgi, gudhi, toponetx, clifford, e3nn, geomstats
- Files: `system_v4/probes/sim_<tool>_capability.py`
- Results: `system_v4/probes/a2_state/sim_results/<tool>_capability_results.json`
- All emit both top-level `all_pass` and `summary.all_pass`
- All have non-empty `TOOL_MANIFEST.reason` fields

**Lane B — classical baselines (44 new sims, classification="classical_baseline"):**
Admission (6), compression/spectral (9), state-representation (7), geometry (5), g-tower/manifold (1), entropy/information (4), dynamics/evolution (3), probe/measurement (7), coupling/weight (2).
Files: `system_v4/probes/sim_*_classical*.py`

**Infrastructure:**
- `system_v4/probes/classical_sweep_runner.py` — Lane B runner. Default selects explicit `classical_baseline` only (44 sims). `--include-heuristic` flag restores numpy/sympy import fallback (152 sims).
- `scripts/verify_load_bearing_has_capability_probe.py` — Lane A gate auditor. Currently **5 violations** (all pre-existing e3nn probe_failing sims, listed below).
- `scripts/classical_baseline_report.py` — boundary-failure matrix aggregator.
- `system_v4/probes/_classical_baseline_common.py` — shared manifest helper.

## Canary status
`classical_sweep_runner.py --minutes 5 --max-parallel 4` → 118 sims attempted, 117 pass, 1 exit=1 (`sim_partial_trace_audit.py` — static auditor, known misclassification, do not fix).

## Ready for auto-run NOW
**Lane B only**:
```
python3 system_v4/probes/classical_sweep_runner.py --minutes 240 --max-parallel 4
```
Safe: `classical_baseline` classification prevents any canonical promotion; failures are boundary data.

## NOT ready (gaps Hermes needs to decide on)
1. **Per-worker gate shim** — `verify_load_bearing_has_capability_probe.py` only runs in batch mode. No `--sim <path>` single-sim gate call yet. Needed before Lane A or nonclassical sims run in parallel.
2. **Queue dirs** — `a2_state/queue/lane_A/` + `lane_B/` with atomic-rename claim protocol not wired. Single-runner fine; multi-runner collisions possible.
3. **5 pre-existing e3nn probe_failing sims** (outside this session's work):
   - `sim_e3nn_hopf_spinor_equivariance.py`
   - `sim_e3nn_ic_invariance.py`
   - `sim_e3nn_relay_equivariance.py`
   - `sim_e3nn_tensor_product.py`
   - `sim_tools_load_bearing.py`
4. **Morning reports** — `queue_manifest.json` / `gate_denials.json` / `tool_capability_state.json` / SHA-256 checksums not emitted by runner yet.
5. **`overnight_8h_run.sh`** — still assumes old single-controller shape; two-runner topology from the brief not yet wired.

## Recommended first auto-run
- **Tonight**: Lane B only, 4h, max-parallel 4, on the 44 strict-selected classical baselines. Hermes monitors + reads result JSON.
- **Tomorrow**: build gate shim + queue dirs + morning reports, then enable Lane A.
- **Nonclassical lane stays OFF** until Lane A batch audit returns 0 violations.

## Three-lane rule (durable, do not violate)
- Lane A (tool-capability-sim): priority z3/cvc5/sympy → rustworkx/PyG/XGI → TopoNetX/GUDHI → clifford/e3nn/geomstats
- Lane B (classical_baseline): free to run broadly, never canonical, failures are useful data
- Lane C (nonclassical/tool-native): **BLOCKED** until Lane A gates satisfied per sim

## Key file paths
- Runner: `system_v4/probes/classical_sweep_runner.py`
- Auditor: `scripts/verify_load_bearing_has_capability_probe.py`
- Report: `scripts/classical_baseline_report.py`
- Results dir: `system_v4/probes/a2_state/sim_results/`
- Audit JSON: `system_v4/probes/a2_state/sim_results/load_bearing_capability_audit.json`
