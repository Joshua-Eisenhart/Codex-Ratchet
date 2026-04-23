---
skill_id: ratchet-overseer
name: ratchet-overseer
description: Monitor ratchet convergence — watch acceptance rates, SIM kill rates, park growth, attractor density, and alert when the ratchet is stuck, drifting, or converging.
skill_type: supervisor
source_type: repo_skill
applicable_layers: [B_ADJUDICATED, SIM_EVIDENCED, GRAVEYARD]
applicable_graphs: [runtime, graveyard, dependency]
inputs: [batch_summaries, invocation_log, survivor_ledger, graveyard, sim_evidence]
outputs: [convergence_report, drift_alerts, plateau_diagnosis]
related_skills: [ratchet-verify, graveyard-lawyer, run-real-ratchet]
capabilities:
  can_only_propose: true
  can_write_repo: false
  requires_human_gate: false
tool_dependencies: []
provenance: "run_real_ratchet.py batch summary output"
adapters:
  codex: system_v4/skill_specs/ratchet-overseer/SKILL.md
  gemini: system_v4/skill_specs/ratchet-overseer/SKILL.md
  shell: system_v4/skills/ratchet_overseer.py
---

# Ratchet Overseer — Convergence Monitor

Monitor the ratchet pipeline's health across batches. Detect:
- **Convergence**: acceptance rate stabilizing, attractor basins forming
- **Plateau**: same concepts cycling through without progress
- **Drift**: rejection reasons shifting away from structural toward noise
- **Stall**: no new concepts entering the pipeline

## When to Invoke

- After each batch completes (post-Phase 4)
- Periodically between batches as a health check
- When acceptance rate drops below threshold

## EXECUTE NOW Steps

1. **Read batch history** from invocation log and runtime state
2. **Compute convergence metrics:**
   - Acceptance rate (last 5 batches)
   - SIM kill rate (last 5 batches)
   - Park growth rate
   - Graveyard growth rate
   - Unique rejection tag distribution
   - Repeated concept re-entry count
3. **Classify ratchet state:**
   - `CONVERGING` — acceptance rate stable, kill rate declining, basins forming
   - `PLATEAU` — same metrics repeating, no new structure admitted
   - `DRIFTING` — rejection reasons shifting, noise entering pipeline
   - `STALLED` — no new concepts entering, pipeline empty
   - `HEALTHY` — normal operation with expected reject/accept ratio
4. **Check for attractor basin formation:**
   - Clusters of survivors with dense dependency edges
   - Graveyard records clustering by failure class
   - Repeated SIM evidence patterns
5. **Emit convergence report:**
   - `ratchet_state`: one of the 5 classes above
   - `acceptance_rate_trend`: improving | stable | declining
   - `attractor_basin_candidates`: list of survivor clusters
   - `recommended_action`: CONTINUE | PAUSE | ADJUST_PARAMETERS | HUMAN_REVIEW

## Quality Gates

- Do NOT raise false alarms on normal rejection rates (most concepts should fail)
- Do NOT recommend parameter changes without specific metric evidence
- Report raw numbers alongside classifications

## Adapter Notes

- **Codex/Gemini**: Read batch artifacts and emit structured report
- **Shell**: Call `system_v4/skills/ratchet_overseer.py` to append a bounded convergence report
