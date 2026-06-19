# Substage Transition Convention Mining Receipt - 2026-06-11

Scope: source-mining only.  
Ceiling: mining receipt only; promotion_allowed: false.  
Write boundary: this receipt is the only write for this lane.

## Bottom Line

The searched sources do **not** pin one owner-source four-substage transition law of the form needed by `basin_two_engine_joint_v2` (`substage cycles 0..3; wrap advances stage; stage wrap advances loop`). They do pin several adjacent structures:

- a four-stage directed loop convention: deductive `Se -> Ne -> Ni -> Si`, inductive `Se -> Si -> Ni -> Ne`;
- a stage-word/readout convention: each stage word has outer and inner components, and the active loop reads one component;
- a composition convention: four validated substages compose into one stage, then stages compose into loops, then loops into engines/schedules;
- a Matrix64/Carnot-style product convention: `4 strokes (axis1 x axis2) x 4 substages (axis5 x axis6) x 2 directions (axis4) = 32` per engine-family lane.

Those structures constrain any v3 realization, but they do not uniquely choose a substage update law. The prediction remains OPEN and must be re-registered convention-relative unless a stronger owner-source pin is found.

## Source Status Classes

- `owner-source`: direct owner quote, pre-AI provenance, owner working notes, or owner-corrected source/report preserving exact owner wording.
- `LLM-elaboration`: assistant/Hermes/bootpack/scaffold formalization over owner material. Useful reference, never canon by itself.
- `sim-realization`: executable packet convention. It can be cited as realization-relative evidence only, not as source admission.

## Read-First / Router Evidence

`/Users/joshuaeisenhart/wiki/projects/codex-ratchet/read-first.md` is the current project front door and routes engine/axis work through the QIT/terrain/IGT source pages. It explicitly lists the current two-engine pattern router:

> `[[projects/codex-ratchet/two-engine-winlose-carnot-szilard-pattern-2026-06-09]] - current routing page for the paired Type1/Type2 WIN/LOSE pattern, Carnot loop orders `Se->Ne->Ni->Si` and `Se->Si->Ni->Ne`, loop-selected component readouts, and the finite discriminator result`  
> Source: `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/read-first.md:95`

`/Users/joshuaeisenhart/wiki/concepts/igt-axes-terrain-source-extraction-2026-06-04.md` is the requested axes/terrains/operators router. It is extraction/reference, not admission:

> `Status: read-only extraction and source-lock aid. This is not a doctrine rewrite, sim admission, layer completion claim, manifold admission, or QIT-engine convergence claim.`  
> Source: `/Users/joshuaeisenhart/wiki/concepts/igt-axes-terrain-source-extraction-2026-06-04.md:5`

It classifies engine patterns:

> `Type 1: outer loop deductive on lifted base, inner loop inductive on fiber; rows are `LOSEwin`, `WINlose`, `loseLOSE`, `winWIN` (lines 304-317). Type 2: outer loop inductive on fiber, inner loop deductive on lifted base; rows are `loseWIN`, `WINwin`, `LOSElose`, `winLOSE` (lines 318-330).`  
> Source: `/Users/joshuaeisenhart/wiki/concepts/igt-axes-terrain-source-extraction-2026-06-04.md:47`

It pins loop order families:

> `| Deductive | In the engine charts, deductive is the `FeTi` loop family and the loop order `Se -> Ne -> Ni -> Si`. In Axis 4 math it is a noncommuting order class, not merely a label. |`  
> `| Inductive | In the engine charts, inductive is the `TeFi` loop family and the loop order `Se -> Si -> Ni -> Ne`. In Axis 4 math it is the complementary order class. |`  
> Source: `/Users/joshuaeisenhart/wiki/concepts/igt-axes-terrain-source-extraction-2026-06-04.md:220-221`

Classification: LLM-elaboration/source-lock extraction over named owner/reference docs.

## Candidate Convention A - Directed Stage-Word / Loop-Readout

This is the strongest current v6 formalization for stage order and loop readout. It distinguishes **stage word** from **active-loop readout**.

> `READ RULE: each stage carries a TWO-COMPONENT word (outer component uppercase, inner lowercase); the ACTIVE LOOP reads ONE component. "WINlose" means outer=WIN, inner=lose - never "the loop reads WINlose."`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/two_engine_readout_automaton_20260609.md:8`

> `Stage words: Se=LoseWin, Ne=WinLose, Ni=LoseLose, Si=WinWin (the complete 2-bit alphabet).`  
> `Carnot orders: C_D (deductive/closure) = Se->Ne->Ni->Si; C_I (inductive/expansion) = Se->Si->Ni->Ne.`  
> `Placements: Type1 = outer:C_D + inner:C_I; Type2 = outer:C_I + inner:C_D.`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/two_engine_readout_automaton_20260609.md:10-12`

> `THE 16 LOOP-READOUT STRATEGIES (2 types x 2 loops x 4 stages), as readout sequences:`  
> `- Type1 outer (deductive):  LOSE -> WIN -> LOSE -> WIN   (alternating, period 2)`  
> `- Type1 inner (inductive):  win -> win -> lose -> lose    (paired, period 4)`  
> `- Type2 outer (inductive):  WIN -> WIN -> LOSE -> LOSE    (paired, period 4)`  
> `- Type2 inner (deductive):  lose -> win -> lose -> win    (alternating, period 2)`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/two_engine_readout_automaton_20260609.md:14-18`

> `STRUCTURE NOTE: deductive order always yields the ALTERNATING readout; inductive order always yields the PAIRED readout - loop order determines readout periodicity regardless of engine type; engine type sets phase/casing.`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/two_engine_readout_automaton_20260609.md:19`

Commit/source note:

> `dd9ec4999 foundations: two-engine readout automaton - stage-word read rule, 16 strategies, deductive=alternating/inductive=paired periodicity, fibered-system form`  
> Source: `git log --all --oneline --grep='directed\|loop order\|loop orders\|stage word\|readout automaton\|deductive\|inductive' -- system_v6/foundations system_v6/receipts`

Classification: LLM-elaboration over owner's charts, but current repo foundation. It pins stage/readout structure, not a four-substage transition law.

Effect on substage transition question:

- Substage update law: not specified.
- Stage advance law: directed loop order is specified (`C_D` or `C_I`).
- Loop advance law: placement says which loop uses which order; no wrap/advance rule is specified.
- Joint terminal prediction: constrains terminal rows by directed stage order and active-loop readout periodicity; does not determine a `2 x 2 x 4 x 4` terminal lattice by itself.

## Candidate Convention B - Two Directed Loop Orders

The symbolic-layer foundation explicitly records the owner correction that the two engine patterns are directed loop orders, not an unordered square:

> `Owner correction: the terrain/function families are read in **two directed loop orders**:`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:89`

> `Se -> Ne -> Ni -> Si`  
> `Se -> Si -> Ni -> Ne`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:91-94`

> `These are loop orders / directed cycles, not just four vertices of a static `Z2 x Z2` square. Any later finite-automaton, QIT-schedule, 64-index, or I Ching comparison must preserve the order separately from the content labels.`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:96`

The same file records the active-loop component rule:

> `Owner correction: on an actual engine loop, the active readout is the **loop-selected component** of the paired word, not necessarily the whole paired word.`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:98`

> `Ni stage word = loseLOSE`  
> `active loop may read = lose`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:100-103`

> `Type 1 outer loop at WINlose stage reads WIN`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:107-109`

Commit/source note:

> `11f6fa2ca foundations: preserve two directed loop orders in engine pattern`  
> Source: `git log --all --oneline --grep='directed\|loop order\|loop orders\|stage word\|readout automaton\|deductive\|inductive' -- system_v6/foundations system_v6/receipts`

Note: the user prompt named `11fea36ca`; the resolvable commit in this checkout is `11f6fa2ca`.

Classification: owner-source lines embedded in LLM-elaboration foundation; strong for directed stage order and readout, not substage law.

Effect on substage transition question:

- Substage update law: not specified.
- Stage advance law: pinned to one of two directed cycles.
- Loop advance law: not specified as an automaton wrap.
- Joint terminal prediction: any convention-relative v3 must preserve order separately from content labels. A realization that treats stages as unordered labels is source-invalid.

## Candidate Convention C - Composition-First Substage Maps

The raw system-v5 reference material explicitly says each main stage is expanded into four substages and gives a composition order.

> `- 16 main stage placements`  
> `- each main stage expanded into 4 substages`  
> `- full 64 schedule made explicit as actual flow, not just a static grid`  
> Source: `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/apple axes terrain operator math.md:422-424`

> `\Phi_{\text{stage}}`  
> `=`  
> `\Phi_{\text{substage},4}\circ`  
> `\Phi_{\text{substage},3}\circ`  
> `\Phi_{\text{substage},2}\circ`  
> `\Phi_{\text{substage},1}`  
> Source: `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/apple axes terrain operator math.md:443-449`

> `\Phi_{\text{loop}}`  
> `=`  
> `\Phi_{\text{stage},4}\circ`  
> `\Phi_{\text{stage},3}\circ`  
> `\Phi_{\text{stage},2}\circ`  
> `\Phi_{\text{stage},1}`  
> Source: `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/apple axes terrain operator math.md:452-458`

> `\Phi_{\text{engine}}`  
> `=`  
> `\Phi_{\text{outer loop}}\circ \Phi_{\text{inner loop}}`  
> `\quad\text{or the reverse, if the schedule specifies that}`  
> Source: `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/apple axes terrain operator math.md:461-465`

> `- define substage maps`  
> `- validate each substage`  
> `- compose substages into stages`  
> `- compose stages into loops`  
> `- compose loops into engines`  
> `- compose engines into schedules`  
> Source: `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/apple axes terrain operator math.md:501-507`

The wiki screenshot transcription reproduces this:

> `Phi_stage = Phi_substage,4 o Phi_substage,3 o Phi_substage,2 o Phi_substage,1`  
> `Phi_loop = Phi_stage,4 o Phi_stage,3 o Phi_stage,2 o Phi_stage,1`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/screenshots_math_report_20260609.md:567-569`

The new-docs gap analysis records it as anti-flattening:

> `Sim composition must go substage -> stage -> loop -> engine -> schedule.`  
> `Cannot flatten/skip levels.`  
> Source: `/Users/joshuaeisenhart/wiki/raw/articles/new-docs/V5_CONTENT_GAP_ANALYSIS.md:220-221`

Classification: likely LLM-elaboration/reference consolidation over owner materials. It is the clearest four-substage composition convention, but not a state transition law.

Effect on substage transition question:

- Substage update law: sequential composition `substage_1`, then `substage_2`, then `substage_3`, then `substage_4` inside a stage.
- Stage advance law: after composition, a stage map is complete; stage order is separately supplied by the loop order sources.
- Loop advance law: stages compose into loops; outer/inner loop composition order is schedule-dependent.
- Joint terminal prediction: a basin realization should carry intermediate trace rows across substages/stages/loops rather than only final state labels. Terminal class count is not predicted by this source alone.

## Candidate Convention D - Matrix64 / Carnot-Szilard Product Substages

Matrix64 records a different four-substage product: substages are `axis5 x axis6`; strokes are `axis1 x axis2`; direction is `axis4`.

> `4 strokes (axis1 x axis2) x 4 substages (axis5 x axis6) x 2 directions (axis4) = 32 per engine family ... Total = 64 = 2^6`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/matrix64_mine_20260610.md:66-67`

Matrix64 also records why final-density-only fingerprints hid stroke/substage structure:

> `n_distinct=16 (not 64) is structurally expected: axis1 and axis2 are applied AFTER the substage (axis5/axis6) composition, so varying (ax1,ax2) with fixed (ax3,ax4,ax5,ax6) does not change the fingerprint ... 16 = 2^4 distinct (ax3,ax4,ax5,ax6) combinations survive.`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/matrix64_mine_20260610.md:126`

It names the discriminator needed:

> `| F7_trajectory | full ordered intermediate trace across strokes/substages | tests ax1/ax2 post-substage aliasing |`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/matrix64_mine_20260610.md:224`

The symbolic layer has the same Carnot finite-map count:

> `Carnot = thermodynamic-legality grammar (4 strokes x 4 substages x 2 directions = 32; Clausius bookkeeping as Axis0 readout).`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:59`

Classification: LLM/sim-derived formalization over current axis map and older Julia carrier. It is a live candidate convention for a 64 schedule surface, but it does **not** match the owner prediction's exact `2 engines x 2 loops x 4 stages x 4 substages` factor order without an additional mapping.

Effect on substage transition question:

- Substage update law: four axis5/axis6 ordered operator substages inside each stroke/stage.
- Stage advance law: four strokes from axis1/axis2, not necessarily the same as the `Se/Ne/Ni/Si` directed loop stage order.
- Loop advance law: direction is axis4 in this convention; loop is not the explicit second factor of the owner prediction.
- Joint terminal prediction: predicts a 64 schedule/grid/fingerprint surface, not automatically 64 basin terminal classes. Re-registration would need to declare whether `loop` maps to axis4/direction or to fiber/base loop.

## Candidate Convention E - v2 Cyclic Substage Realization

This is the convention already audited as underdetermined. It is included for contrast only.

> `UNDER THE v2 CYCLIC-SUBSTAGE REALIZATION and REMAINS OPEN - the four-substage transition law is`  
> `` `underdetermined_by_committed_sources`; v2 pinned a cyclic convention (substage wrap advances``  
> `stage, stage wrap advances loop) that is not source-admitted.`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md:55-58`

The v2 audit repeats the same caveat:

> `The main design caveat is not by-construction exclusion of 64. It is realization scope: the cyclic substage convention determines the 32-state per-engine cycle. A different source-pinned substage transition law could change the terminal lattice.`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/sims/basin_two_engine_joint_v2/audit_verdict.md:83`

Classification: sim-realization, not owner-source. It is not admissible as the source-pinned convention.

Effect on substage transition question:

- Substage update law: `substage i -> (i + 1) mod 4`.
- Stage advance law: stage advances on substage wrap.
- Loop advance law: loop advances on stage wrap.
- Joint terminal prediction: v2 found no primary 64 terminal/SCC level under this convention; that is realization-relative negative evidence only.

## Do bc910f24b and 11f6fa2ca Constrain Substage Transitions?

`bc910f24b` constrains readout semantics, not substage transitions:

> `bc910f24b foundations: distinguish stage word from loop readout`  
> Source: `git log --all --oneline -- system_v6/foundations/working_math_scaffold_20260609.md system_v6/foundations/two_engine_readout_automaton_20260609.md system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md`

Its file content says the paired word preserves two-loop stage structure while the active loop reads a component:

> `So the paired word preserves the two-loop stage structure, while each engine loop reads its own selected casing/component. This applies across the 16 strategies. Encoding the full word as the active loop value would overstate the per-loop readout.`  
> Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:111`

`11f6fa2ca` constrains directed stage order, not substage transitions:

> `11f6fa2ca foundations: preserve two directed loop orders in engine pattern`  
> Source: `git log --all --oneline --grep='directed\|loop order\|loop orders\|stage word\|readout automaton\|deductive\|inductive' -- system_v6/foundations system_v6/receipts`

It forces a v3 realization to preserve the two directed cycles and to test order separately from labels. It does not say whether substages cycle, reset, compose, branch, or remain internal to a stage map.

## Absence Evidence / Failed Searches

Literal `~/wiki/core_docs` was not present:

```bash
rg -n -i "substage|sub-stage|sub stage|4 substages|stage transition|stage order|stage progression|loop advance|MAX loop|min loop|deductive|inductive|alternating|paired|stage word|readout|precedence|Ti/Te/Fi/Fe ordering" /Users/joshuaeisenhart/wiki/raw /Users/joshuaeisenhart/wiki/core_docs /Users/joshuaeisenhart/wiki/concepts
```

Observed output included:

```text
rg: /Users/joshuaeisenhart/wiki/core_docs: No such file or directory (os error 2)
```

Path discovery also found no `core_docs` directory under `~/wiki`:

```bash
find /Users/joshuaeisenhart/wiki -maxdepth 3 -type d \( -iname 'core_docs' -o -iname 'core-docs' -o -iname '*core*docs*' \) -print
```

Observed output: no lines.

The direct wrap/advance search did not find an owner-source cyclic wrap rule. It found only the v2 caveat/sim realization and unrelated uses of "wrap":

```bash
rg -n -i "substage|sub-stage|sub stage|4 substages|stage transition|stage progression|loop advance|wrap|advance[s]? stage|advance[s]? loop|cycle[s]? 0|substage.*stage|stage.*substage" /Users/joshuaeisenhart/wiki/raw /Users/joshuaeisenhart/wiki/concepts /Users/joshuaeisenhart/wiki/codex-ratchet-research system_v6/foundations system_v6/receipts system_v5/docs/references
```

Relevant observed hits:

```text
system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md:56:UNDER THE v2 CYCLIC-SUBSTAGE REALIZATION and REMAINS OPEN — the four-substage transition law is
system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md:57:`underdetermined_by_committed_sources`; v2 pinned a cyclic convention (substage wrap advances
system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md:58:stage, stage wrap advances loop) that is not source-admitted.
system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:59:- eng_carnot_axiswired: all_pass=true, tool_lego_fit_probe, promotion blocked. Carnot = thermodynamic-legality grammar (4 strokes x 4 substages x 2 directions = 32; Clausius bookkeeping as Axis0 readout).
/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/apple axes terrain operator math.md:423:- each main stage expanded into 4 substages
/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/apple axes terrain operator math.md:446:\Phi_{\text{substage},4}\circ
system_v6/receipts/matrix64_mine_20260610.md:67:     > 4 strokes (axis1 x axis2) x 4 substages (axis5 x axis6) x 2 directions (axis4) = 32 per engine family ... Total = 64 = 2^6
system_v6/receipts/matrix64_mine_20260610.md:126:  > n_distinct=16 (not 64) is structurally expected: axis1 and axis2 are applied AFTER the substage (axis5/axis6) composition...
```

The broader requested repo/wiki sweeps were run:

```bash
rg -n -i "substage|sub-stage|sub stage|4 substages|stage transition|stage order|stage progression|loop advance|MAX loop|min loop|deductive|inductive|alternating|paired|stage word|readout|precedence|Ti/Te/Fi/Fe ordering" /Users/joshuaeisenhart/wiki/codex-ratchet-research
```

No hit in that surface pinned a four-substage transition law. Relevant hits were only general readout/precedence separation, e.g.:

```text
/Users/joshuaeisenhart/wiki/codex-ratchet-research/old-sims-mined/old-registries-axes-operators.md:60:| Noncommutative/order controls | Axis 4 loop order, Axis 6 precedence, token order, operator order, and noncommuting channel order are separate degrees of freedom. | Order-correctness must be tested separately from content-correctness. |
```

Repo sweep:

```bash
rg -n -i "substage|sub-stage|sub stage|4 substages|stage transition|stage order|stage progression|loop advance|MAX loop|min loop|deductive|inductive|alternating|paired|stage word|readout|precedence|Ti/Te/Fi/Fe ordering" system_v6/foundations system_v6/receipts system_v5/docs/references
```

Relevant hits are cited above. They pin stage/readout/composition/product surfaces, not a unique substage transition automaton.

## Convention-Relative Re-Registration Rows

| Convention | Source class | Substage update law | Stage advance law | Loop advance law | Joint terminal structure prediction |
|---|---|---|---|---|---|
| Directed stage-word/readout | LLM-elaboration over owner charts; owner correction embedded | none pinned | `C_D = Se->Ne->Ni->Si` or `C_I = Se->Si->Ni->Ne` | placement selects outer/inner orders; no wrap law | terminal structure must preserve directed stage order and active-loop component readout; no guaranteed 64 |
| Composition-first substage maps | LLM/reference consolidation | `Phi_stage = sub4 o sub3 o sub2 o sub1` | stage maps compose in loop order | `Phi_engine = outer loop o inner loop` or reverse if schedule specifies | terminal structure depends on composed maps and intermediate traces; no source-pinned cyclic 64 |
| Matrix64/Carnot product | sim/formalization, reference only | 4 substages = `axis5 x axis6` ordered operator variants | 4 strokes = `axis1 x axis2` | direction = `axis4`; loop mapping open | predicts schedule/fingerprint 64 candidate, not basin terminal 64 unless earned |
| v2 cyclic-substage | sim-realization only | substage cycles 0..3, wrap advances stage | stage wrap advances loop | cyclic loop advance | v2 found no primary 64; realization-relative negative evidence only; not source-admitted |

## Final Classification

The sources **ADMIT SEVERAL adjacent conventions** but **PIN NONE** as the owner-source four-substage transition convention required for canonical v3 adjudication.

What is pinned:

- two directed stage cycles;
- active-loop component readout from paired stage words;
- substage-to-stage composition discipline;
- Matrix64/Carnot product substages as a separate reference/sim convention.

What is not pinned:

- a source-admitted cyclic substage state machine;
- a rule that substage wrap advances stage;
- a rule that stage wrap advances loop;
- a unique mapping from the owner prediction's `2 engines x 2 loops x 4 stages x 4 substages` into the Matrix64 `4 strokes x 4 substages x 2 directions` convention.

Therefore: do not promote any v3 result as canonical unless it declares which convention it realizes and cites a source-pinned law. If no stronger owner-source pin is later found, re-registration should be convention-relative, with one registration per row above or a narrower owner-approved convention set.
