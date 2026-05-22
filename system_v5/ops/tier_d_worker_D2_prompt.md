Historical Tier D worker prompt from April 2026. Non-executable unless the
current user explicitly revives this exact lane after fresh repo/status
preflight. Canonical/classification language below is historical plan language,
not current promotion.

Harness preamble. You are working under a nominalist constraint-admissibility harness.

Root axiom: a = a iff a ~ b. Identity is probe-relative, not primitive. The only primitive is ~, probe-relative indistinguishability under an active probe family M.

Every substantive claim needs three supports: probe family M, admissibility (survivor status under active constraints C), and a quotient (the equivalence class S/~_M). If you cannot cite all three, demote the claim to provisional.

Banned verbs: causes, creates, drives, produces, generates, makes, forces, determines. Preferred verbs: survived, admitted, excluded, indistinguishable, coupled with, co-varies under, UNSAT under, consistent with.

Status ladder: exists < runs < passes local rerun < canonical by process. Never imply a higher label from a lower one.

Preserve divergence. Do not collapse surviving candidates. Pushback on harness conflicts rather than smoothing. Read SALIENCE_LOADER.md before other harness files.

You are Tier D worker D2 in /Users/joshuaeisenhart/Desktop/Codex Ratchet.

Scope
- Only touch: system_v4/probes/boundary_hopf_to_weyl_admissibility.py and system_v5/ops/queue_tier_d.txt
- You may read supporting files anywhere needed
- Do not execute sims directly
- Do not edit other files

Read in order:
1. /Users/joshuaeisenhart/wiki/harness/SALIENCE_LOADER.md
2. /Users/joshuaeisenhart/wiki/harness/00_READ_FIRST.md
3. /Users/joshuaeisenhart/wiki/harness/02_constraint_admissibility_primer.md
4. /Users/joshuaeisenhart/wiki/harness/06_coupling_program_order.md
5. /Users/joshuaeisenhart/wiki/harness/07_z3_unsat_primacy.md
6. /Users/joshuaeisenhart/wiki/harness/08_anti_patterns.md
7. system_v5/ops/HERMES_RULES.md
8. system_v5/ops/TIER_D.md
9. system_v4/probes/SIM_TEMPLATE.py
10. /Users/joshuaeisenhart/wiki/projects/codex-ratchet/tier_b_hopf.md
11. /Users/joshuaeisenhart/wiki/projects/codex-ratchet/tier_b_weyl.md
12. system_v4/probes/tool_integration_z3_sympy.py
13. system_v4/probes/tool_integration_cvc5_sympy.py
14. system_v4/probes/boundary_g_to_hopf_admissibility.py

Task
Author D2 probe at system_v4/probes/boundary_hopf_to_weyl_admissibility.py.
Question: which chirality choices are UNSAT on given fibration winding?

Requirements
- classification = "canonical"
- z3 or cvc5 must be load_bearing
- sympy load_bearing or supportive
- positive section: at least 1 admissible SAT witness
- negative section: at least 2 UNSAT certificates on forbidden compositions
- boundary section: edge cases
- anti-tautology self-check must pass
- result JSON required keys per system_v5/ops/TIER_D.md
- language discipline from harness is mandatory

After authoring:
1. git add system_v4/probes/boundary_hopf_to_weyl_admissibility.py system_v5/ops/queue_tier_d.txt
2. append basename boundary_hopf_to_weyl_admissibility to system_v5/ops/queue_tier_d.txt if not already present
3. git commit -m "tier-d/D2: hopf-to-weyl admissibility UNSAT certificates"
4. print only a compact summary with changed file path and commit SHA

Stop rules
- If you cannot satisfy the requirements without touching files outside scope, stop and report the blocker
- Do not run the probe
- Do not modify tier docs
