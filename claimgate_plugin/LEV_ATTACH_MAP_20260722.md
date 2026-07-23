# Lev attach map (2026-07-22, verified read-only vs ~/lev-main pure main)

KEY FINDING: the CR eval work was NOT wholly lost — upstream main ships
`plugins/sim-witness` with `cr_*` evaluator packs (template:
`plugins/sim-witness/evals/cr_constraint_battery/`), a
`codex_ratchet.engine_leg_result.v1` adapter (src/cr-result-adapter.ts), and
6 cr-*.test.ts. Upstream's hard contract ("one brain"): provider evidence may
NOT carry verdict bits — `all_pass`/`promotion_allowed`/`verdict`/`gate_proof`
are REJECTED as facts; only core/eval emits verdicts.

ABSENT upstream: `lev orchestration` (steering-consume gone for good),
claimgate rows in dna/gates.yaml, ratchet-forward floor comparison;
ratchet-admission.flow.yaml exists but executor is a boot-stub (all stages
pass at boot — do not trust it as a gate). `lev ratchet-admission` CLI is the
AAVF graph writer, NOT a receipt gate.

MINIMAL ATTACH (zero lev-main changes):
1. Build evaluator pack IN CR: claimgate_plugin/evals/claimgate/
   (claimgate.eval.yaml schema lev.evaluator_pack.v1, companions/sensor.mjs
   wrapping claim_verify.py exits into lev.evaluator.result.v1,
   policies/gate-policy.yaml, pass.eval.js suite; fixture receipt adapted to
   codex_ratchet.engine_leg_result.v1 with ALL self-assessment bits stripped).
   Clone the cr_constraint_battery shape.
2. Run through Lev's brain by ABSOLUTE PATH (core/exec/src/handlers/eval.ts:125):
   cd ~/lev-main && ./core/poly/bin/lev eval run \
     /Users/joshuaeisenhart/Codex-Ratchet/claimgate_plugin/evals/claimgate/pass.eval.js --json
   Decision lands at ~/.local/share/lev/execution-ledger/artifacts/eval/<runId>/decision.json
3. Harness-fired leg unchanged: lev exec --verifier 'python3 claimgate_plugin/claim_verify.py ...'
   (core/exec/src/loop/until.ts, gate-proof.json, replay-graded claim_verdicts).
4. Symlinks into lev-main are DEAD (fractal-scan containment I-35/N-35);
   .lev/local.config.yaml eval.roots override possible but = untracked file in
   the read-only repo — owner's call only.
5. Upstream later: docs/_inbox/20260619-claimgate-leviathan-convergence.md
   already sanctions ClaimGate as a plugins/ surface; sim-witness is the
   template; dna/gates.yaml row = the PR-sized enforcement add.
