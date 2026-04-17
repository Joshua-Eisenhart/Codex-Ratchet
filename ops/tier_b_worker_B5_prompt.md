You are Tier B worker B5 in /Users/joshuaeisenhart/Desktop/Codex Ratchet.

Read in order:
1. ~/wiki/harness/00_READ_FIRST.md
2. ~/wiki/harness/06_coupling_program_order.md
3. ~/wiki/harness/07_z3_unsat_primacy.md
4. system_v4/probes/SIM_TEMPLATE.py
5. Scan ~/wiki/concepts/ for clifford and pauli matches
6. ops/HERMES_RULES.md
7. ops/SIM_RUNNER.md
8. ops/TIER_B.md
9. ~/wiki/projects/codex-ratchet/tier_b_spawn_plan.md
10. ~/wiki/projects/codex-ratchet/tier_b.md

Scope only:
- clifford_*
- pauli_*
- ~/wiki/projects/codex-ratchet/tier_b_clifford_pauli.md
- ops/queue_tier_b.txt append lines for your new probes

Tasks:
1. Inventory existing clifford/pauli probes and classify canonical/classical_baseline/broken.
2. Identify shell-local gaps only.
3. Write at least 4 new canonical shell-local probes in your scope.
4. Each new probe must be SIM_TEMPLATE conformant, shell-local only, positive+negative+boundary sections, and at least one load_bearing Tier A tool.
5. Commit each probe individually as: tier-b/B5: <probe-name>
6. After each commit, append basename to ops/queue_tier_b.txt and append a steward log line in canonical format.
7. Rewrite ~/wiki/projects/codex-ratchet/tier_b_clifford_pauli.md with last_updated and your inventory/gap/probe list.

Do not execute sims or drift into coupling/bridge work.
Stop after writing, committing, enqueueing, and updating the layer report.