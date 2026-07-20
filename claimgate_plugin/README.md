# ClaimGate v0.1

Done-ness is computed, never asserted. Two gates, exit codes are the interface.

Dependency-free Node (>=18). Independent plugin: attaches to Lev at the boundary,
never patches Lev core, expects rework per Lev release.

## 1. Claim-receipt linter — for "the agent says it's done"

```
node claimgate.mjs lint-receipt <receipt.json> [--rules rules.json]
```

Exit 0 admissible, 1 rejected, 2 malformed. Rules (all mechanical):

- R1 verdict-inflation: any `verdict`/`status` field must agree with the `pass`
  field beside it (INTEGRATED requires pass=true; BLOCKED/PRUNED must not pass).
  Divergence is allowed only with an explanation field (`gate_miss_note`, ...)
  — the honest-gate-miss pattern stays representable, silent inflation does not.
- R2 claim-without-evidence: numeric claim fields (accuracy, corr, MI, ...)
  must sit beside provenance (raw arrays, CIs, source_path, sha256, ...).
- R3 baseline honesty: any comparison-to-chance must carry a majority/null/twin
  baseline field. "Beats chance 0.5" hid a 0.867 majority class once; never again.
- R4 preregistration: every evaluated check must appear in a `preregistered`
  block. Post-hoc gates are rejected.
- R5 recompute contract (with tolerance ceiling: declared tol must be within
  5% of the claim magnitude, else R5-tolerance-gaming): the receipt may declare
  `recompute: [{claim, op, from, tol}]` (mean/min/max/sum/count/fraction_true);
  the linter re-derives each claim from the receipt's own raw arrays.
  Receipts with no recompute contract pass R5 but are flagged: asserted, not re-derivable.

### Wiring into the Lev SDK done-callback

The agent's "I'm finished" call must submit a receipt path; the harness runs the
linter; exit != 0 means the claim never lands and the task is not done:

```bash
node claimgate.mjs lint-receipt "$RECEIPT" || { echo "claim rejected"; exit 1; }
```

## 2. Module admission gate — for "the agent wants to create a file"

```
node claimgate.mjs admit-module <declaration.json> --estate <repo-dir> \
    [--registry admissions.jsonl] [--threshold 0.6]
```

Exit 0 admit, 3 park for human review (near-duplicate found), 1 reject, 2 error.
Declaration shape:

```json
{
  "name": "telemetry-flush-scheduler",
  "purpose": "Batches telemetry events and flushes them on an adaptive interval",
  "paths_to_create": ["core/telemetry/flush-scheduler.ts"],
  "interface": ["scheduleFlush", "TelemetryBatcher"],
  "searched": [{"query": "telemetry flush", "tool": "grep", "hits": 0}]
}
```

Gates:

- G1 schema: name, purpose, paths required.
- G2 inventory-before-generation: a non-empty `searched` receipt is mandatory —
  the agent must prove it looked for an existing implementation first.
- G3 immutability: refuses creation over an existing path; a new version is a
  new admission at a new path.
- G4 near-duplicate: token-similarity (with stemming/prefix matching) over
  estate file names + headers, plus declared-interface collision against
  exported identifiers. A colliding config-loader parks at score >= threshold;
  a human decides extend-vs-split. This is Lev's ratchet-admission near-dup
  gate (BR-007) applied to code instead of declarations.
- G5 term fence (optional): terms_used must resolve against a term registry.

Every decision appends to `admissions.jsonl` — an append-only log.

### Wiring

Wrap the agent's file-creation tool (or a pre-commit hook listing new files):
creation is only executed when admit-module exits 0; exit 3 routes to the human
queue with the near-duplicate evidence attached.

### Gaming defenses (added after adversarial stress round)

- Empty evidence is not evidence: `{}`, `[]`, and `""` do not satisfy R2.
- Explanation fields must exceed 30 characters to legitimize a verdict/pass
  divergence — junk notes do not.
- `--strict`: verdicts outside the agreed vocabulary are rejected, not noted
  (vocabulary-evasion defense). Recommended for CI.
- Tolerance gaming: `tol` larger than 5% of the claim magnitude voids the
  recompute contract instead of passing it.
- `checks` as an array of names is handled the same as an object.

## Tests

`fixtures/` contains the five cases (all derived from real incidents):
inflated receipt (rejected, 8 violations), honest receipt with explained
gate-miss + recompute contract (admissible), duplicate config loader
(parked, name_sim 1.0 + 2 interface collisions), novel module without a search
receipt (rejected), novel module with search receipt (admitted).

## Boundary

This plugin validates claims and admissions. It does not judge science,
does not call any model, and holds no LLM-controlled step — every verdict
is reproducible from the inputs. The adversarial fresh-context audit
(a model prompted to refute, armed with the accumulated fake-pass catalog)
remains a separate, complementary layer above this one.
