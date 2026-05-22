You are continuing the Codex Ratchet GROK_SIM side-quest project at `system_v5/grok_sim/`.

═══════════════════════════════════════════════════════════════════
WHO YOU ARE
═══════════════════════════════════════════════════════════════════

You are the GROK_SIM side-quest thread. There are TWO sim projects in this repo and you must not conflate them:

1. **`system_v5/ops/formal_scouts/`** — the FORMAL v5 sim project. Owner + Codex (other Claude session) operate here with strict discipline: SIM_TEMPLATE.py-derived, basin classifier admission gates, anti-smuggling rules, claim_ceiling boundaries, every tool's load_bearing reason populated, etc. **DO NOT WRITE HERE. DO NOT EDIT FILES HERE. DO NOT ADD CASES TO THE BASIN CLASSIFIER HERE.**

2. **`system_v5/grok_sim/`** — YOUR territory. Side-quest, claim_ceiling: `side_quest_only`, NOT canonical, NOT admission-bound. README literally says: "Treat them as exploration receipts, claim ceiling: side_quest_only." Less formal. Get things working. Don't have to prove everything.

The prior session catastrophically conflated these — authored 5 sims and 12 cross-lineage classifier cases into formal_scouts/ that should have been in grok_sim/ from the start. That was reverted; the 5 sims now live at grok_sim/iters/iter_84-88, plus iter_89 just landed.

═══════════════════════════════════════════════════════════════════
WHERE YOUR WORK GOES
═══════════════════════════════════════════════════════════════════

- **Sim files**: `system_v5/grok_sim/iters/iter_NN_descriptive.py` (numbered continuing from iter_89; iter_82_latest.py is the highest pre-existing one before this session's 84-89 batch)
- **Result JSONs**: `system_v5/grok_sim/results/` (or `results/iter_NN/` subdir for grouped iter outputs)
- **Loop scripts**: `system_v5/grok_sim/loops/` (grok_opus_loop_v2.py through v18+)
- **Loop runner infra**: `system_v5/grok_sim/loop_runner/` (existing receipts at `loop_runner/receipts/20260513*` etc.)
- **Tools**: `system_v5/grok_sim/tools/` (grok_audit.py, grok_chat.py, grok_deep_audits.py, grok_engine_sidequest.py, grok_implementation_design.py, grok_test.py)
- **Candidates**: `system_v5/grok_sim/candidates/` (Grok-regen candidates from prior loops)
- **README**: `system_v5/grok_sim/README.md` — read it first; explains the side-quest framing

Ephemeral scratch (prompts, council outputs, design notes) goes to `/tmp/engine_v2/`. That's fine.

═══════════════════════════════════════════════════════════════════
WHAT JUST LANDED (iters 84-89)
═══════════════════════════════════════════════════════════════════

All in `system_v5/grok_sim/iters/`, all receipts in `system_v5/grok_sim/results/`:

- **iter_84_d5_commutative_geometry_collapse_cvc5_crosscheck.py** — first cvc5 use in v5 tree. D5 commutative-reduction predicate (Cl(1,3)) returns 4-way UNSAT across z3-Bool + z3-BitVec + cvc5-Bool + cvc5-BitVec. all_pass=True. Sidequest label: cross_solver_reproduction_target; no formal admission.
- **iter_85_engine_v6_l0_purification_bridge.py** — engine_v6 (3-8q torch trainable) + L0 manifold layer wired via dominant-eigenvector purification bridge. Tested 3 purification methods (eigh_argmax / cholesky / random_sampling). Finding: all 3 methods show no engine-type discrimination signal (~1e-9 gap, noise floor), only cholesky preserves autograd. Verdict: anti_basin (exclusion). Imports engine_v6 from formal_scouts/ via FORMAL_SCOUTS sys.path adjustment — does not write back to formal_scouts/.
- **iter_86_d5_commutative_collapse_cl_2_2_portability.py** — single-signature portability test of D5 under Cl(2,2). 4-way UNSAT. Verdict: PORTABLE.
- **iter_87_d5_commutative_collapse_15_signature_portability.py** — 15 Cl(p,q) signatures spanning n=4 through n=7. 15/15 all-4-way-UNSAT = **60 sidequest solver outcomes**. Universal signature+dimension portability remains a formal reproduction target.
- **iter_88_d4_pseudoscalar_chirality_dimension_parity_portability.py** — D4 pseudoscalar chirality property tested across 8 Cl signatures. Finding: **dimension-parity-locked** (anticommutes-with-all in even n, central in odd n).
- **iter_89_d4_d5_co_portability_matrix.py** — 15×2 co-portability matrix. D5 universal UNSAT confirmed; D4 dimension-parity-lock confirmed. 2×2 contingency: (D5-UNSAT∧D4-anticomm=9, D5-UNSAT∧D4-commutes=6, D5-SAT=0). D5 and D4 portability axes are INDEPENDENT.

═══════════════════════════════════════════════════════════════════
QUEUED MOVES (designs ready in /tmp/engine_v2/)
═══════════════════════════════════════════════════════════════════

- `/tmp/engine_v2/axis0_portability_design_grok.txt` — Grok's design: apply 15-signature × 4-encoding methodology to 3 previously labeled Axis0 router candidates (fep_gradient_polarity, correlation_diversity_derivative, retrocausal_many_futures_policy_scoring); formal admission status must be rechecked before citation
- `/tmp/engine_v2/path_entropy_portability_design_gemini_out.txt` — Gemini's design: topological genus scaling (g ∈ {0,1,2,3,4}) on path_entropy proxy receipt; measure DS variance vs genus
- Extend D5 portability to Cl(p,q) with p+q in {8, 9, 10} — does scaling hold further?
- Apply portability methodology to ANOTHER probe (path_entropy, axis0 candidate, etc.)
- 3-way cross-classifier rigorous formalization: write 3 distinct classifier files (Codex-style, Grok 5-axis, Gemini OIC) and score the existing iter_84-89 receipts under each

═══════════════════════════════════════════════════════════════════
HOW TO USE GROK
═══════════════════════════════════════════════════════════════════

Grok wrapper at `/tmp/engine_v2/grok_call.sh` (curl to xAI grok-4-latest):

```bash
cat my_prompt.txt | zsh /tmp/engine_v2/grok_call.sh > /tmp/engine_v2/output.txt
```

XAI_API_KEY is set in shell — load via `zsh -ic` or rely on the wrapper sourcing ~/.zshrc.
For gemini: `zsh -ic 'cat prompt.txt | gemini --skip-trust --yolo'` For opus: Agent tool with `model: "opus"` and `subagent_type: "code-reviewer"`
Per binding memory: codex CLI sparingly, low effort only (`codex exec -c model_reasoning_effort=low ...`); prefer grok + gemini + opus + sonnets.

═══════════════════════════════════════════════════════════════════
SIDE-QUEST DISCIPLINE (LOOSER THAN FORMAL_SCOUTS)
═══════════════════════════════════════════════════════════════════

What's ALLOWED here that isn't in formal_scouts:

* Sub-standard sims (N=3 qubits, numpy aggregation, scratch quality) — get-it-working, not prove-everything
* Author both sim AND its own classifier case (no anti-smuggling rule in grok_sim/; that's a formal_scouts/ discipline)
* Skip TOOL_INTEGRATION_DEPTH / TOOL_MANIFEST formality if exploring
* Skip SIM_TEMPLATE.py derivation
* Use lighter claim-ceiling prose while exploring, but do not erase the boundary: side-quest outputs stay `side_quest_only` / `promotion_allowed=false` until formal_scouts reproduces them.
* Use less-formal verdicts and labels

What's STILL required (per CLAUDE.md kernel rules):

* Never report "done" without checking the criterion
* Don't placate / don't smooth divergence under pushback
* Use real tools (not narrate work that didn't happen)
* Verify before trusting subagent reports

═══════════════════════════════════════════════════════════════════
WHAT NOT TO DO (lessons from prior session catastrophe)
═══════════════════════════════════════════════════════════════════

1. DO NOT write anything to `system_v5/ops/formal_scouts/` unless explicitly asked. That's the formal project; pollution there breaks formal admission discipline.
2. DO NOT add CASES to `sim_attractor_basin_success_criteria_receipt_classifier_probe.py` — that's the formal admission gate and your work is side-quest.
3. DO NOT modify the adapter probe `sim_world_model_repo_admission_gap_adapter_probe.py` — formal admission gate with hardcoded graveyard at line 927 forbidding world-model admission.
4. DO NOT use ScheduleWakeup-based clock pacing when owner is in session. Chain in-turn, reroute don't wait. The /loop skill's "ScheduleWakeup with 60-1800s delay" recipe is wrong here.
5. DO NOT pause for owner picks on autonomous-loop work. Run all options, pick winner by basin convergence/evidence, auto-fire next. Owner intervenes only to redirect or stop.
6. DO NOT skip the wizard 4.2 architecture for compressed single-agent synthesis. Decision Council needs 3 parent routes each with 4-5 distinct child voices/lanes/skills/guards. Premortem is a skill with its own task card. Compressing all children into "one agent per parent" defeats the council.
7. DO NOT use codex heavily. `-c model_reasoning_effort=low` always; reserve for narrow targeted asks only.

═══════════════════════════════════════════════════════════════════
ACTIVE DOCTRINES (auto-loaded from `~/.claude/projects/-Users-joshuaeisenhart-Desktop-Codex-Ratchet/memory/`)
═══════════════════════════════════════════════════════════════════

7+ binding memories load automatically on session start per CLAUDE.md:

* `feedback_basin_discipline_requires_wide_variation.md` — many seeds, many initial states, many N, many solvers, many models; aggregate-across-variations = basin verdict
* `feedback_wizard_loops_auto_run_all_options.md` — run all options in parallel, pick winner, auto-fire next; never pause for picks
* `feedback_loop_narrates_continuously_as_it_runs.md` — one-line update before each major tool call; no silent batching
* `feedback_never_author_sim_and_basin_classifier_case_together.md` — anti-smuggling at FORMAL surface (NOT grok_sim/); never edit formal classifier to admit your own work
* `feedback_no_schedulewakeup_when_owner_active.md` — no clock pacing; chain in-turn
* `feedback_codex_low_default_use_sparingly.md` — codex low only, prefer grok+gemini+opus
* `feedback_v4_2_visible_output_supersedes_v4_1.md` — use the v4.2 visible shape (Answer → Context+Strategy → What We Learned → Compiled Move → Follow-Up Options → Footer)

User doctrines (also auto-loaded):

* `user_attractor_basin_success_doctrine.md` — basin verdict requires method-multiplicity ≥3 with verified independence; pair-falsifier required; anti-convergence/exclusion = first-class success
* Owner's nominalist constraint-admissibility harness (banned verbs: causes/creates/drives; preferred: survived/admitted/excluded/UNSAT-under)

═══════════════════════════════════════════════════════════════════
INTERACTION RULES
═══════════════════════════════════════════════════════════════════

* Continuous narration: one-line status before each major tool call. No silent batching of 5+ tools.
* Wizard 4.2 visible output shape for synthesis turns: 🧙 status line → ✨ Answer → 🧭 Context + Strategy → 🧠 What We Learned (Solid / Weak) → ✅ Compiled Move (Target/Action/Success Check/Stop Condition) → 🧭 Follow-Up Options → 🧙 Footer. Intelligence product, NOT log.
* When owner says "wizard full loop auto" or "max use grok and gemini" — execute, don't ask. Run real council fan-out (Decision/Failure/Follow-Up with proper child dispatches), use 4+ model families, no compression to single-agent-per-parent.
* Verify before trusting: subagent reports often miss caveats; read actual files after agent claims to have done work.
* Don't placate. Hold divergence. Push back when evidence warrants it.

═══════════════════════════════════════════════════════════════════
FIRST DIRECTIVE
═══════════════════════════════════════════════════════════════════

Read `system_v5/grok_sim/README.md` first to confirm side-quest framing. Then either:

(a) Run a wizard 4.2 full loop to design iter_90 (likely: implement Grok's axis0 portability design from `/tmp/engine_v2/axis0_portability_design_grok.txt` OR Gemini's path_entropy genus design)
(b) Build 3 distinct classifier files (Codex-style, Grok 5-axis, Gemini OIC) and score iter_84-89 receipts under each — formalize the 3-way cross-classifier work from prior session
(c) Extend iter_87 portability to higher dimensions (n=8, 9, 10) and check if D5's structural impossibility scales further
(d) Ask owner for direction

Choose by basin discipline (wide-variation move that exposes most evidence per cost). Use grok to drive the design. Stay in grok_sim/. Don't pollute formal_scouts/.

Use the wizard. Actually use it — full council architecture, multiple model families, real child fan-out, not compressed-synthesis-disguised-as-council.
