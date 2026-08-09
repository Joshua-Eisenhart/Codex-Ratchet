# Session work index — 2026-08-07/08

Everything below was verified against disk when this file was written, not recalled.
The verification column names the check that was actually run.

Status ladder: `exists` < `runs` < `passes local rerun`.

---

## FIX — defects found and closed

| ID | What was wrong | Where | Verified |
|---|---|---|---|
| FIX-01 | Coverage measure read its own prior receipt, latching `never_run` at 0. Excluding receipts restores the true 21 | `scripts/cb_integrated_run.py` | `SELF_OUTPUT` present; measure now reports 21 |
| FIX-02 | Digger regex kept its trigger outside the capture group, so survivors asserted what their source forbade | `scripts/cb_integrated_run.py:83` | trigger now inside capture; W4 fails if any polarity word is lost |
| FIX-03 | Member ids matched by bare substring: `premortem` matched `failure.premortem`, `z3` matched `AGENTS.md` | `scripts/cb_integrated_run.py` | `ID_BOUND` whole-token regex present |
| FIX-04 | `deep_survivors` counted byte-identical file copies as independent versions | `scripts/cb_integrated_run.py` | depth now counts distinct content hashes |
| FIX-05 | `--resume` was `load_state() if a.resume else load_state()` — both arms identical | `scripts/cb_loop.py:75` | fresh run starts at 0, `--resume` continues |
| FIX-06 | Loop billed OpenRouter and claude every cycle with no gate | `scripts/cb_loop.py` | `--allow-paid` required; default run is free |
| FIX-07 | Autoresearch leg had never once executed — `KeyError: 'ladder'` swallowed as a quiet negative | `scripts/cb_autoresearch_loop.py` | `params.update(disk)` merge; leg runs and reports LAW 8 honestly |
| FIX-08 | Falsifier had no SURVIVED branch and hardcoded `councils_run: 0`, so every target was killed by construction | `scripts/cb_wave_falsifier_v3.py` | `councils_run_measured()` reads disk; three reachable verdicts |
| FIX-09 | LAW 8 tested only the measure, never the receipt conjunct its own text requires | `scripts/cb_loop.py` | both conjuncts tested; crashed census no longer reads as static |
| FIX-10 | `estate_controller` pin predated the package's git import, PARKing every `constraintbox run` | `src/constraintbox/agentrun.py:93` | all 5 pins match; verified by sha256 comparison |
| FIX-11 | `operation_poisoner_sha256` was never pinned, so severance capabilities reported a digest mismatch for a missing pin | `config/sim_estate_v2.json` | pinned; numpy/scipy digest drift cleared |
| FIX-12 | Gate parsed model output with `json.loads`, which keeps the last duplicate key — a duplicate `verdict` could upgrade PARKED to ADMIT | `scripts/cb_run.py:130` | now `parse_json_object`; duplicate key returns `IntakeError` |
| FIX-13 | `make gates` ran 1 of 4 ClaimGate surfaces; 22 tests had no runner | `Makefile:367` | +3 lines: SMT tests, ledger verify, aggregate report |
| FIX-14 | `make cb-check` ran only S1 while reporting green | `Makefile` | `TIER ?= S1`; `make cb-estate TIER=S3` works |
| FIX-15 | Fake-swarm detector read the routing path, so 5 lanes reaching 4 vendors scored 1 family | `scripts/cb_multi_provider.py` | `family_of()` reads model vendor |
| FIX-16 | `child_health` wrote second-resolution receipt paths; two runs in one second overwrote each other | `scripts/cb_child_health.py` | keyed by source-receipt hash + collision counter |
| FIX-17 | `cb_heavy_gate` counted itself as a call site, so all 10 lanes reported integrated | `scripts/cb_heavy_gate.py` | self-excluded; honest 6 of 10 |
| FIX-18 | `cb_project_state` detectors tested the wrong things and stopped registering fixes | `scripts/cb_project_state.py` | detectors rewritten; defect list now empty |

**Recurring shapes.** Four of these are the same defect wearing different clothes: a measure that reads its own output (FIX-01, FIX-17), a capture that drops the polarity word (FIX-02), a branch whose arms are identical (FIX-05), and a return code discarded so a crash reads as a quiet negative (FIX-07).

---

## BUILD — new tooling

| ID | What it is | Where | Rung |
|---|---|---|---|
| BUILD-01 | Decision wave: 3 routes, 13 councils, 65 seats, deterministic output gate | `scripts/cb_wave_decision.py` | passes local rerun |
| BUILD-02 | Follow-Up wave: 3 routes, 14 councils, 70 seats, lane-coverage classifier | `scripts/cb_wave_followup.py` | passes local rerun |
| BUILD-03 | The two never-run Failure routes as ROUTES, not skill invocations | `scripts/cb_wave_failure_routes.py` | passes local rerun |
| BUILD-04 | `child_health` manager, seven verbs over a wave receipt | `scripts/cb_child_health.py` | passes local rerun |
| BUILD-05 | Skill runner: reads SKILL.md, gates artifacts against the skill's own shape | `scripts/cb_skill_runner.py` | runs (`--list` only) |
| BUILD-06 | Agent monitor: idle time, tool-call count, last action, stall bound | `scripts/cb_agents.py` | passes local rerun |
| BUILD-07 | CB-light gate over the CB-heavy estate, four separable questions | `scripts/cb_heavy_gate.py` | passes local rerun — **duplicates `constraintbox estate`, see OPEN-05** |

---

## LAND — estate moved onto disk

| ID | What | Count | Rung |
|---|---|---|---|
| LAND-01 | `sim_engines/incoming_20260807` — five Desktop packs | 1,763 files | exists, unread |
| LAND-02 | `system_v9/incoming_20260807` — manifold archive | 734 files | exists, unread |
| LAND-03 | `holodeck/sources_20260807` — probes gathered from across v4-v8 | 79 probes, 32 results, 16 docs | exists |
| LAND-04 | `holodeck/julia_fep` — ActiveInference.jl, isolated | 1 env | runs |
| LAND-05 | `holodeck/python_fep` — pyhgf 0.3.0 on py3.12, isolated | 1 venv | runs |
| LAND-06 | Quarantine for the negation-inverted receipts | 4 receipts | exists |
| LAND-07 | py313-macos locks generated from the installed set | 3 locks, 66 packages | exists |
| LAND-08 | `verify_cb_sim_admission.py` rescued from a gitignored directory | 1 file | exists |

---

## RUN — executed, with receipts on disk

| ID | Run | Receipts | Result |
|---|---|---|---|
| RUN-01 | Decision wave | 3 | 65/65 seats live, 3/3 routes admitted, 0/13 councils collapsed |
| RUN-02 | Follow-Up wave | 1 | 70 seats, 2/3 admitted, lane test fired: 19 of 25 options mapped to zero lanes |
| RUN-03 | Failure routes | 1 | 40/40 seats, 8/8 diverged, both routes admitted |
| RUN-04 | `child_health` | 5 | kill 21, reroute 16, demote 11 on degraded receipts |
| RUN-05 | Heavy gate | 4 | 10 declared / 10 installed / 10 capable / 6 integrated |
| RUN-06 | Census (integrated run) | 4 | corpus 18,417 docs; `unmentioned` 21, honest |
| RUN-07 | Holodeck atoms 1-7 | 7 | all `all_pass=True`, first receipts in repo history |
| RUN-08 | Packaged test suite | — | 929 passed, 336 subtests, twice (before and after edits) |
| RUN-09 | Estate tier ladder | S1-S4 | **11/11 required capabilities READY**, up from 6/11 |
| RUN-10 | Julia estate load | — | 26 of 27 packages load; only Catlab absent from the main depot |
| RUN-11 | JAX suite probe | — | 21 of 24 compute correctly |

---

## INST — installed and verified computing

| ID | What | Where | Evidence |
|---|---|---|---|
| INST-01 | `constraintbox` editable install | main env | was NOT INSTALLED; 108 modules were unreachable |
| INST-02 | pyhgf 0.3.0 | `holodeck/python_fep` | 5 observations → belief trajectory 0.0 → 0.209 |
| INST-03 | ActiveInference.jl 0.1.2 | `holodeck/julia_fep` | posterior [0.75, 0.25], normalised |
| INST-04 | pymdp 1.0.3 | main env | generative model columns sum to 1 |
| INST-05 | NVIDIA + OpenRouter free lanes | `cb_multi_provider.py` | 8 lanes; 135 seats ran free this session |

---

## DOC — documents produced

| ID | Document | Size |
|---|---|---|
| DOC-01 | `docs/CB_COMPONENT_INDEX_20260807.md` | 986 components, 8 domains, stable IDs |
| DOC-02 | `docs/CB_SYSTEM_LAYOUT_20260807.md` | subsystem map from 9 readers |
| DOC-03 | `PROJECT_STATE.md` | regenerated; defect list now empty |
| DOC-04 | This index | |

---

## OPEN — known and not done

| ID | What | Why it matters |
|---|---|---|
| OPEN-01 | Follow-Up lane test measures its keyword classifier, not the five-lane partition | The result fires but does not answer the question asked |
| OPEN-02 | Failure routes measure divergence and never fire a debate round (`rounds: 0`) | 8/8 diverged and nothing acted on it |
| OPEN-03 | 76 unwired items in the scouts' backlog | Nine of the top ten are single-line fixes |
| OPEN-04 | Component index is a snapshot, not generated from disk | It drifts the moment code changes |
| OPEN-05 | `cb_heavy_gate.py` duplicates `constraintbox estate`, which is better | I built it without checking what existed |
| OPEN-06 | Two diverged `claimgate_plugin` copies, 534 vs 427 files, both bound | `gate` and `crosscheck` resolve different trees |
| OPEN-07 | Environment reads DRIFT: 399 packages installed that the lock does not list | The lock models a minimal tier env; everything runs in one shared 3.8 GB env |
| OPEN-08 | `julia_density` not registered by the controller | Julia works, 521 `.jl` files use it, the tier cannot test it |
| OPEN-09 | `pykoopman_rate`, `dimod_anneal` acceptance profiles not implemented | Both non-required |
| OPEN-10 | 1,763 + 734 landed files unread | On disk is not integrated |
| OPEN-11 | Nothing committed | All work is untracked |

---

## Mistakes I made this session

| What | Consequence | Caught by |
|---|---|---|
| Used bare `python3` instead of the project interpreter for version pins | Wrote 3 wrong pins (numpy 2.2.6 vs 2.3.4) | Reran and compared; the exact failure the owner's handoff documents |
| Built `cb_heavy_gate.py` without checking the CLI I had already mapped | Duplicated `constraintbox estate`, which pins digests and locks; mine does not | The scout fan-out |
| Printed the OpenRouter API key into the transcript | Key exposed; rotation advised | Immediately, self-reported |
| Framed a non-decision as an owner decision | Handed back resolvable work | The owner |
| Shipped a monitor that reported all 14 finished agents as STALLED | Read the agent transcript instead of the run journal | First run of the tool |
