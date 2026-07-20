# Fuel adequacy gate

This is Principle Zero. It runs before any ratchet (pairwise MSS) comparison.
It decides whether a candidate pool has enough real fuel to make a comparison
mean anything. It does not decide which candidate is better. It is fuel
infrastructure, not the ratchet.

`fuel_adequacy_gate.py` is a deterministic script, like `claimgate/claimgate.py`.
It never asks a model to judge a candidate. Exit codes are the only interface:

- `0` = `ADEQUATE`, nothing printed to stdout.
- `1` = `HOLD_INSUFFICIENT_FUEL`, a JSON reasons object printed to stdout.

Pool membership is discovered by a naming convention (`candidate_*.md` by
default), never by a hardcoded file list. A thin provenance manifest cannot
buy a candidate a pass by simply omitting it — the gate scans the pool
directory directly and reports any file with no matching manifest entry as a
provenance gap.

## What it checks

Four checks run every time. All four must pass for exit 0.

1. **Required variation slots.** The pool must fill six roles: `incumbent`,
   `minimal_rival`, `structural_rival`, `order_nesting_rival`, `countermodel`,
   `ablation_control`. Empty slots are named in the output.
2. **Real diversity.** At least `--min-diversity-floor` (default 4) distinct
   model families, that many distinct generation paths, and that many
   effective candidates. Two candidates that share model family, carrier,
   and nesting order collapse into one effective candidate. The report
   always states effective count against raw count.
3. **Provenance present.** Every candidate needs, per its manifest entry:
   `model`, `version`, `prompt_lineage`, `source_corpus`, `tools`,
   `saw_preferred_answer` (a real boolean), `inherited_assumptions`, and
   `code_lineage`. A field that is present but says, in effect, "unknown" is
   flagged as thin — it does not pass as adequate provenance just because a
   placeholder string fills the key.
4. **Executable enough.** Each candidate file is scanned for a probe/test
   section and a defeat-condition/witness section. Bare prose with neither
   is flagged. This checks that probes and a can-fail witness are named, not
   that they have actually been run — see "What this gate does not do"
   below.

The required field list for check 3 is read from `candidate_package_schema.json`
at run time, not duplicated by hand in the script, so the schema stays the
single source of truth.

## The six fuel slots

| Slot | What it means |
|---|---|
| `incumbent` | the candidate this round is defending or extending |
| `minimal_rival` | removes a presumed layer or assumption from the incumbent |
| `structural_rival` | a genuinely different carrier family, not a relabel |
| `order_nesting_rival` | same ingredients, different order, bracket, or containment |
| `countermodel` | preserves the observed result without the claimed mechanism |
| `ablation_control` | a deletion, reversal, scramble, or flatten control |

## Why prompt variation is not diversity

A hundred near-identical proposals are one effective candidate. Asking one
model to write the same carrier ten different ways produces ten prompts and
one idea. The gate buckets each candidate by `(model family, carrier,
nesting order)`. Two candidates that share all three collapse to one
effective candidate. The model-family count and the generation-path count
are checked separately from the effective-candidate count, because a pool
can fail in either direction: too few distinct sources, or enough sources
that still converge on the same structure and order.

Fields that only say "unknown" do not count toward diversity either. Four
candidates each claiming an untracked prompt lineage are not four data
points about generation diversity — they are one data point about how
little is known, and the gate reports it that way rather than treating four
copies of "unknown" as four distinct paths.

## How to run

Against the current pool, with defaults (`system_v8/candidates/`, the
manifest under `manifests/`):

```
python3 fuel_gate/fuel_adequacy_gate.py
```

Writing the full diagnostic (not just the stdout-on-fail shape) to a file:

```
python3 fuel_gate/fuel_adequacy_gate.py --write-result fuel_gate/results/first_pool_verdict.json
```

Against a different pool or manifest:

```
python3 fuel_gate/fuel_adequacy_gate.py --pool-dir path/to/pool --manifest path/to/manifest.json
```

## Current pool result

Run 2026-07-20 against `system_v8/candidates/` (4 candidates: spinor/QIT,
top-down 12-to-0, classical bottom-up, foreign nonassociative). Verdict:
`HOLD_INSUFFICIENT_FUEL`. Full receipt at
[`results/first_pool_verdict.json`](results/first_pool_verdict.json).

- Missing slots: `countermodel`, `ablation_control`. Nothing in the pool
  preserves the result without the claimed mechanism, and nothing is a
  deletion/reversal/scramble/flatten control.
- Effective vs raw candidates: 4 vs 4. No collapsing — the four carriers are
  genuinely distinct (finite relation, density-matrix/spinor, nonassociative
  octonion, multi-agent registry), confirmed by three different
  `(model, carrier, order)` triples never repeating.
- Distinct model families: 3 (`openai_gpt_codex`, `xai_grok`,
  `anthropic_claude` — the last used twice, for two different candidates),
  below the floor of 4.
- Distinct generation paths: 0. All four candidates predate this manifest;
  `prompt_lineage` is honestly recorded as unknown for all of them rather
  than guessed, and unknown values do not count as diversity evidence.
- Provenance gaps: 11, across all four candidates — `prompt_lineage` thin on
  all four, `saw_preferred_answer` not a real boolean on all four (nobody
  tracked whether the generating process saw a preferred answer), and
  `code_lineage` thin on three of four (the classical candidate is the
  exception: it genuinely reuses executed functions from
  `base_ratchet_campaign.py`, so its code lineage is not flagged).
- Executable-enough: passes. All four candidates carry a named probe/test
  section and a defeat-condition/witness section in their own text.

This matches the honest expected outcome: the pool clears the strawman bar
(see `system_v8/candidates/STRAWMAN_AUDIT.md`) but is not yet adequate fuel
for a pairwise comparison, for reasons the strawman audit itself named in
prose and this gate now confirms by running code against the pool directory
and the manifest.

The gate was checked against a synthetic six-candidate pool with all slots
filled, six distinct model families, tracked generation paths, and real
booleans: it returns `ADEQUATE` (exit 0). Removing one slot assignment from
that synthetic pool flips it back to `HOLD_INSUFFICIENT_FUEL` naming exactly
the removed slot. The gate can pass — it is not a decorative always-fail
trap — and it is not a rubber stamp either.

## What this gate does not do

It does not rank candidates. It does not compute presumption, relative MSS,
or any tooth. That is the ratchet's job: code (JAX, Julia, SMT) run on
executable finite structures, never an LLM narrative and never this gate.

This boundary is not theoretical. On 2026-07-20, an LLM audit ranked these
same four candidates by presumption, a second LLM pass "corrected" that
ranking, and the owner voided both — see
`system_v8/candidates/RANKING_VOID_llm_did_ratchets_job.md`. The void notice
states the correct state is "the same HOLD the fuel-adequacy gate returns."
This gate's checks (slot coverage, family and path counting, key presence
and type, section grep) are all mechanical. None of them compare candidates
against each other on quality, correctness, or minimality — only on whether
the pool, as a set, has the shape a pairwise comparison would need before it
is run.

Check 4 also does not confirm that probes have actually executed. It
confirms that a probe/test section and a witness/defeat-condition section
exist in the candidate's own text. All four current candidates are
`exists`-tier prose (per `STRAWMAN_AUDIT.md`): they describe probes, they
have not run them. That gap is real and this gate does not close it — the
executable-enough check is deliberately scoped to "names its probes and its
own way to lose," not "has been executed," because the owner's spec for
this check is a grep, not an execution trace.

## Architecture

```
candidate-fuel ecology -> fuel-adequacy gate (this) -> pairwise ratchet -> receipt / frontier / purgatory
```

Candidates are produced and vetted for genuineness upstream (fuel-audit work
like `STRAWMAN_AUDIT.md` — legitimate LLM work). This gate checks whether
that fuel is adequate in shape and provenance. Only past this gate does a
pairwise ratchet run. Its outcome is a receipt that lands the candidate on
the frontier or in purgatory. This gate touches none of that pipeline; it
only decides whether the pipeline is allowed to start.

## Files

- `fuel_adequacy_gate.py` — the gate.
- `candidate_package_schema.json` — the candidate package schema: `claim`,
  `assumptions`, `carrier`, `nesting_order`, `implementation`, `predictions`,
  `rivals`, `known_failure_modes`, plus a nested `provenance` object. The
  required-fields list in check 3 is read from this file, not duplicated.
- `manifests/current_pool_provenance_manifest.json` — the best-effort
  provenance manifest for the current four candidates, with an explicit
  `status_note` on what is genuinely known versus honestly marked unknown.
- `results/first_pool_verdict.json` — the full diagnostic from the run
  documented above.
