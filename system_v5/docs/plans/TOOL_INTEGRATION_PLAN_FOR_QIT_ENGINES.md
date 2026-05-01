# Tool-Integration Sim Plan (Foundation Stage)

Date: 2026-04-19 (rewritten after owner correction; see Meta at end)
Status: **draft** — every claim is `[VERIFIED: source]` or `[UNVERIFIED: to-read]`. Do not act on `[UNVERIFIED]` items until the cited source has been read.

## Scope

Foundation-stage tool work only:

- tool-capability sims (Kind 3 per `~/wiki/harness/05_four_sim_kinds.md`)
- tool-lego-integration sims (Kind 4)

That is the full scope. Everything named on `~/wiki/harness/06_coupling_program_order.md` Steps 2–6 (pairwise coupling, multi-shell coexistence, topology-variant reruns, emergence tests, bridge / axis / engine claims) is **out of scope** under this plan's bound.

## Out of scope (named explicitly, per `~/wiki/harness/28_bounded_work.md`)

The forward-chain completion the training manifold reaches for after "finish tool integration" is "...and then run the engines." That completion is refused here. Listing out-of-scope items by name:

- running any engine / system-level sim (Type-1-named, Type-2-named, or otherwise)
- running axis-level sims (Axis 0…6)
- coupling / pairwise / coexistence / topology-variant / emergence sims
- bridge claims (rho_AB, Xi, Phi0, Axis 0 gradient)
- **any narrative-theory labels (Type 1, Type 2, Weyl, chirality, FeTi, TeFi, IGT, Jungian, WIN-LOSE) inside sim code or sim JSON** — per `feedback_sim_pure_math_rosetta_earned_later.md`; measured invariants only; rosetta is a post-hoc pass

Skip-ahead to any of the above requires a separate work unit with its own admission gate citing `06_coupling_program_order.md`.

## Bound exit condition

The tool-integration stage is complete, and this plan's work is closed, when:

1. Each of the 22 installed tools has a capability probe that passes local rerun (status `passes local rerun`, not a higher label).
2. For each `(tool, lego-family)` pair where the tool is intended to be load-bearing for an admissibility claim, a `sim_integration_<tool>_*` file exists, is run cleanly, and has positive + negative + boundary tests with the tool in a load-bearing position confirmed by reading the file body.
3. Each integration sim's manifest has `classification`, `TOOL_MANIFEST` (with non-empty `reason`), and `TOOL_INTEGRATION_DEPTH` fields populated honestly.
4. The ledger at `system_v5/docs/plans/plans/TOOL_CAPABILITY_AND_INTEGRATION_LEDGER.md` reflects the real state of each row, cited to the file + line that justifies the label.

When those four are true, this plan closes and the next work unit (per `28_bounded_work.md`) begins — the next work unit is not this plan's continuation.

## Pre-plan priming (done this session after owner reminder)

[VERIFIED: read this session 2026-04-19]

- `~/wiki/harness/SALIENCE_LOADER.md`
- `~/wiki/harness/00_READ_FIRST.md`
- `~/wiki/harness/READ_POLICY.md`
- `~/wiki/harness/05_four_sim_kinds.md` — four-kinds classification, hard-block rule
- `~/wiki/harness/06_coupling_program_order.md` — step gates, admission by cited result-file
- `~/wiki/harness/08_anti_patterns.md` — failure modes
- `~/wiki/harness/11_pytorch_as_ratchet.md` — numpy contamination test
- `~/wiki/harness/28_bounded_work.md` — work-unit block shape, queues as admission pools

Not yet read (needed before authoring any new integration code):
- `~/wiki/harness/03_language_discipline.md`
- `~/wiki/harness/07_z3_unsat_primacy.md`
- `~/wiki/harness/12_f01_n01_nominalist_axioms.md`
- `~/wiki/harness/16_dictionary.md`
- `~/wiki/harness/17_pre_emit_audit.md`
- `~/wiki/harness/19_grammar.md`

## Owner-named failure modes to actively fight

1. **Hallucinated APIs** — LLM invents function signatures and claims they are real. Counter: every API call traceable to either (a) a repo file that already uses it, or (b) an upstream doc page actually fetched and read at the pinned version.
2. **Toy sims** — primitives that claim "nonclassical." Counter: a sim is a tool-integration anchor only if removing the named tool breaks the admissibility claim. If the tool can be swapped for numpy without the claim failing, the tool is decorative and the sim is not an integration anchor.
3. **numpy contamination** — per `11_pytorch_as_ratchet.md`, a geometry sim using `np.dot` / `np.einsum` / `np.linalg.eig*` as load-bearing IS classical_baseline by construction. Not a drift to fix; a category to mark. Any such sim gets labeled `classical_baseline`; separate nonclassical counterpart is authored if needed.
4. **Stage-skipping** — jumping to coupling / axis / engine work before integration is honest. Counter: `Out of scope` list above; any skip-ahead is refused by name.
5. **Celebrating sed-stamps** — ledger label bumps without reading the files. Counter: every label change cites a probe file and the specific load-bearing pattern read end to end in it.
6. **Jargon in sims** — Type-1/Type-2/Weyl/FeTi/TeFi/IGT labels inside sim code or JSON. Counter: measured invariants only; rosetta is a separate post-hoc analysis pass on top of pure-math sims.

## Installed tool versions — 2026-04-19, `codex-ratchet/envs/main`

[VERIFIED: ran `importlib` check against live env]

| Tool | Version | Tool | Version |
|---|---|---|---|
| torch | 2.11.0 | networkx | 3.6.1 |
| torch_geometric | 2.7.0 | xgi | 0.10.1 |
| z3 | (import ok; no `__version__`) | toponetx | (import ok; no `__version__`) |
| cvc5 | 1.3.3 | gudhi | 3.12.0 |
| sympy | 1.14.0 | hdbscan | (import ok; no `__version__`) |
| clifford | 1.5.1 | umap | 0.5.12 |
| geomstats | 2.8.0 | hypothesis | 6.151.12 |
| e3nn | 0.6.0 | optuna | 4.8.0 |
| rustworkx | 0.17.1 | ribs | 0.10.0 |
| deap | 1.4 | evotorch | 0.6.1 |
| pymoo | 0.6.1.6 | datasketch | 1.9.0 |
| numpy | 2.3.4 | | |

## Candidate upstream doc URLs — pin-to-installed-version

[UNVERIFIED: URLs not fetched. Fetch only under auto-mode when a specific integration sim requires a specific API reference; cite section per call.]

- torch 2.11 · torch_geometric 2.7 · z3py · cvc5 1.3 python · sympy 1.14 · clifford 1.5 · geomstats 2.8 · e3nn 0.6 · rustworkx 0.17 · toponetx (unpinned) · gudhi 3.12 · xgi 0.10

Rule: for any API in new integration code, cite a repo file already using it OR an upstream doc page fetched this session. No other source.

## Tool-category map (for integration-matrix planning only — NOT engine-use)

| Category | Tools | Integration-anchor question |
|---|---|---|
| Numerical substrate | torch (canonical), numpy (baseline) | which admissibility claims require autograd / torch computational graph and fail when replaced with numpy? |
| Graph machinery | pyg, rustworkx, networkx, toponetx, xgi | which legos' admissibility claims fail without message-passing / DAG-admissibility / cell-complex / hypergraph representation? |
| Proof | z3, cvc5 | which exclusion claims require UNSAT witness, not numerical non-finding? |
| Symbolic | sympy | which invariants require closed-form / symbolic trace-preservation proof, not numerical check? |
| Geometry | clifford, geomstats, e3nn | which claims require rotor / geodesic / equivariant representation, not coordinate matrices? |
| Topology/homology | gudhi, toponetx | which claims require persistent homology / Betti numbers / chain complex, not descriptive topology? |
| Search / optimization | optuna, evotorch, ribs, pymoo, deap | which admissibility searches are real only under bounded / Pareto / archive / evolutionary search, not grid scan? |
| Density clustering | hdbscan, umap | which probe-result reductions require density clustering, not k-means / PCA? |
| Property-based | hypothesis | which invariants require random-input property coverage, not fixed-case tests? |

## Bounded step-by-step plan

**Non-negotiable:** do not proceed to step N+1 until step N is honestly complete. "Honestly complete" = written finding, anchored to file+line, naming what passes and what still fails, with the ledger updated to match.

### Step 1 — Tier-3 harness priming (finish)

Read the six `~/wiki/harness/` files still pending (listed above). Tier 3 is required per `READ_POLICY.md` for plan / canonical sim work.

Bound exit: all six read; notes taken on anything that changes the plan below.

### Step 2 — Ledger honesty pass, anchored to file bodies

For each of the 20 capability probes marked `passes local rerun (2026-04-19)` in the ledger, read the file body (not just the header). For each: is the "passes local rerun" label for the primitive-level test only, or does the probe also exercise a load-bearing pattern? Tag each row accordingly:

- `passes local rerun — primitives only` (most probes will be this)
- `passes local rerun — load-bearing pattern confirmed` (requires a demonstration in the file body)

This is not a promotion; it is a truth-in-labeling pass that prevents "primitives pass" from being read as "nonclassical capability confirmed."

Bound exit: ledger capability column annotated truthfully; anchor file+line for every `load-bearing pattern confirmed` tag.

### Step 3 — Audit existing integration sims for real vs decorative use

For each existing `sim_integration_*` file in `system_v4/probes/`, read the file end to end. For the declared load-bearing tool(s), check: if I remove the tool and replace with the baseline, does the admissibility claim still hold? If yes, the tool is decorative and the sim is a toy / reference-grade, not a canonical integration anchor. Tag each file:

- `load-bearing confirmed` (tool is required for the admissibility claim)
- `decorative` (tool is imported but the claim still holds without it)
- `reference-grade` (the sim is a valid baseline but not a canonical integration anchor)

Bound exit: a per-file tag table with file+line anchors for each tag.

### Step 4 — Identify the integration matrix and its empty cells

Per `05_four_sim_kinds.md`: "The real backlog is the integration matrix: for each (tool, lego-family) pair, is there an integration sim? Empty cells are the actual work."

Construct the matrix. Rows = 22 installed tools. Columns = lego-families from `system_v5/docs/17_actual_lego_registry.md`. A cell is filled iff a `sim_integration_<tool>_*` exists with `load-bearing confirmed` tag from Step 3 for that tool on a lego in that family.

Bound exit: the matrix, plus the list of empty cells sorted by which are next-admissible.

### Step 5 — Admission pool for new integration sims

Per `28_bounded_work.md`: queues are admission pools, not pipelines. From the empty-cell list, form an admission pool. For each candidate cell, the admission gate is:

- the tool's capability probe passes local rerun with `load-bearing pattern confirmed` (from Step 2), AND
- the lego is in a family with at least one existing canonical sim in `17_actual_lego_registry.md`

Any candidate that does not clear both gates stays in the pool but cannot be drawn.

Bound exit: admission pool populated; gate status noted per candidate.

### Step 6 — Bounded authoring, one integration sim at a time

For one drawn candidate from the Step 5 pool:

1. Read the upstream doc page for the tool at the installed version. Cite section per API used.
2. Read an existing canonical sim on the target lego. Cite the file+line that shows how the lego is currently represented.
3. Author the sim from `system_v4/probes/SIM_TEMPLATE.py`. No jargon in code or JSON. Measured invariants only. Tool must be load-bearing such that removing it breaks the admissibility claim.
4. Run. Record `all_pass`. If not `all_pass`, stop and diagnose; do not draw a new candidate.
5. Update the ledger row with file+line anchor.
6. Stop. Do not draw the next candidate as part of this work unit. Next draw is a separate work unit.

Bound exit (per sim): sim passes local rerun; ledger updated; session ends or hands to next work unit.

### Step 7 — Repeat Step 6 for the next candidate

Separate work unit. Separate admission. Separate closeout.

### Plan-complete condition (restating the Bound exit from top)

All 22 capability probes have `passes local rerun — load-bearing pattern confirmed` OR a documented reason for `primitives only` being acceptable for that tool's role. Every `(tool, lego-family)` cell intended to be load-bearing is either filled with a `load-bearing confirmed` integration sim, or explicitly marked `not-needed` with reason.

Then this plan closes. The next stage (coupling, per `06_coupling_program_order.md` Step 2) requires a **new** plan and new admission gate. This plan's completion does not admit coupling work.

## Self-test before every resumption of this plan

1. Is my next action inside this plan's Scope? If it touches any Out-of-scope item, stop.
2. Am I about to run a sim with engine / axis / coupling naming in its filename or body? Stop.
3. Am I about to claim a tool is load-bearing based on a file header / declaration / manifest? Read the file body first.
4. Am I about to batch Step 6 (author > 1 integration sim in one unit)? Stop; that is pipeline behavior refused by `28_bounded_work.md`.
5. Have I saved a memory update if I discovered a new durable pattern? If no, save it.

## Open questions for owner

1. **Plan filename**: this file is still named `TOOL_INTEGRATION_PLAN_FOR_QIT_ENGINES.md`. The name carries the old (wrong) framing. Should I rename it (e.g. to `TOOL_INTEGRATION_SIM_PLAN_FOUNDATION_STAGE.md`), leave it as a record of the correction, or delete-and-replace?
2. **Scope of "load-bearing"**: for Step 3, is the test "replace with numpy baseline → does the claim survive?" the right load-bearing test across all tool categories, or are there categories (e.g. property-based / search) where the test should be different?
3. **Integration-matrix granularity**: rows are 22 tools; columns are lego-families. Is family-level the right granularity, or should the matrix be per-lego?
4. **Doc-fetch policy under auto-mode**: should I fetch upstream docs with WebFetch at Step 6 when a specific API is needed, or do you want doc-fetches gated on explicit approval?

## Meta — why this plan was rewritten

[VERIFIED: this session 2026-04-19]

The prior draft of this file was titled "Tool Integration Plan for Type 1 and Type 2 QIT Engines." It named running Type 1 and Type 2 engine sims as Step 8 / the endpoint. That framing violates two standing rules already in memory and in the wiki harness:

- **Engine / axis / coupling work is Stage 6** per `~/wiki/harness/06_coupling_program_order.md`. Foundation work (tool sims + tool integrations) is Stages 1–2. A plan whose endpoint is Stage 6 while claiming to be bounded foundation work is narrative substitution of skip-ahead as progress.
- **No narrative-theory jargon in sims** per `feedback_sim_pure_math_rosetta_earned_later.md`. "Type 1 / Type 2 / Weyl / chirality / FeTi / TeFi / IGT" inside sim code or JSON is disallowed.

Owner called both errors out (2026-04-19, verbatim): *"you aren't supposed to be running the type 1 and type 2 sims. if you look at this context. that is exactly the wrong thing to do. nor should any jargon be in the sims."*

The rewritten plan's endpoint is the integration matrix (empty cells filled with load-bearing-confirmed integration sims), not engine runs. Engines are a separate later work unit requiring separate admission.

Preserved from the prior draft: the installed-tool versions table, the tool-category map (reframed as integration-matrix question per row, not engine-use column), the upstream-doc candidate URL list, the verified-sources structure.

Dropped from the prior draft: every engine target, every axis target, every jargon token (Type 1, Type 2, Weyl, chirality, FeTi, TeFi, IGT, Jungian, WIN-LOSE) in the plan body, the "asymmetry to fix" framing that treated engine canonicalization as a plan deliverable.
