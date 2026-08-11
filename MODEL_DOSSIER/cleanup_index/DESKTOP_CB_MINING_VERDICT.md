# Desktop/Constraint Box — index and mining verdict

## What this is

A content-addressed index of everything in `~/Desktop/Constraint Box/`, and the verdict on what
should be pulled into the repo. Indexing came first, before any move or delete, as instructed.

Built by `scratchpad/index_desktop_cb.py`. It SHA256s every file inside every zip, recurses three
levels into nested zips, and compares each hash against every tracked blob under
`constraint_box/`, `claimgate_plugin/`, `MODEL_DOSSIER/` and `ROOT/`.

Machine-readable index: [desktop_cb_content_index.json](desktop_cb_content_index.json)
Readable summary: [desktop_cb_content_index.md](desktop_cb_content_index.md)

## Bottom line

The repo is ahead of every ConstraintBox code snapshot on the Desktop. There is nothing to
import into `constraint_box/src/`. The novel mass is documents and sim-lane code, not CB.

Two gate modules exist there and nowhere in the repo. Both are sim-lane external-workload
consumers, and both look superseded by modules the repo already has. That needs one check.

## The numbers

| measure | value |
|---|---|
| containers | 33 zips + 25 loose files |
| file occurrences (recursing nested zips) | 8,955 |
| distinct contents by SHA256 | 2,304 |
| nominal bytes across occurrences | 258,120,868 |
| unique bytes | 82,021,906 |
| redundancy | 68.2% of bytes are duplicate copies |
| distinct contents already in the repo | 947 |
| distinct contents not in the repo | 1,357 (71,733,230 bytes) |
| zip read errors | 0 |

Recursing into the 18 nested zips added 2,514 file occurrences and exactly 2 new distinct
contents. The nested zips are re-packaging, not content.

## Where the novelty actually sits

| container | distinct | novel | novel % |
|---|---|---|---|
| `3CLAUDE_CONTAINER_PACK_20260727_cc_FULL.zip` | 459 | 395 | 86% |
| `CLAUDE_CONTAINER_PACK_20260727_cc_FULL.zip` | 449 | 385 | 86% |
| `CONSTRAINT_GEOMETRY_RESEARCH_CONTINUITY_PACK_20260727_v2.zip` | 408 | 351 | 86% |
| `COMPLETE_CONSTRAINTBOX_SIMENGINE_CODEX_RATCHET_HANDOFF_20260730_v1.zip` | 1,747 | 1,139 | 65% |
| `OVERALL_RATCHET_CONSTRAINTBOX_MANIFOLD_ARCHIVE_20260730_v1.zip` | 461 | 426 | 92% |
| `FABLE_RATCHET_MANIFOLD_16_HANDOFF_20260729_v1.zip` | 207 | 206 | 100% |
| `FOUR_SYSTEM_MINI_LEVOS_PACK_20260804_v5.zip` | 35 | 35 | 100% |
| `CB_SIM_FOUNDATION_HANDOFF_20260806_v1.zip` | 50 | 50 | 100% |
| `ConstraintBox_Contained_Local_Sim_Product_0.3.5_r28.zip` | 644 | 34 | 5% |
| `ConstraintBox_Contained_Core_20260731_r6.zip` | 587 | 70 | 12% |
| `CB_SIM_ENGINE_STRESS_HANDOFF_20260803_v2.zip` | 727 | 99 | 14% |
| `constraintbox-core-0.3.4-r24-claude.zip` | 644 | 103 | 16% |
| `CONSTRAINTBOX_COMPLETE_20260806.zip` | 774 | 178 | 23% |

The split is clean. CB code packs are 5% to 23% novel — the repo holds them. Research and handoff
packs are 86% to 100% novel — those carry documents the repo does not have.

`3CLAUDE_CONTAINER_PACK_20260727_cc_FULL.zip` and `CLAUDE_CONTAINER_PACK_20260727_cc_FULL.zip`
are near-identical, ~48 MB each. One is a copy of the other with 10 extra files.

## CB code: the repo is ahead, file by file

Every CB module on the Desktop is smaller than its counterpart in the repo.

| module | repo bytes | Desktop bytes | verdict |
|---|---|---|---|
| `mini_levos.py` | 105,892 | 17,189 (as `mini_levos_v2.py`) | repo ahead |
| `proposal_minilev_flow.py` | 43,618 | 42,428 | repo ahead |
| `workflow_graph.py` | 39,320 | 34,548 | repo ahead |
| `claimgate_plugin/ratchet_floor_smt.py` | 26,038 | 25,852 | repo ahead |
| `levos_flowmind.py` | 23,560 | 23,560 | identical |
| `capability_receipt_replay.py` | 10,654 | 9,539 | repo ahead |

`mini_levos_v1.py`, `v2.py` and `v3.py` in `FOUR_SYSTEM_MINI_LEVOS_PACK` are 13.7 KB, 17.2 KB and
12.2 KB. The repo kernel is 105.9 KB. They are earlier prototypes, not a newer branch.

## The one open item

Two gate modules have no counterpart by name anywhere in the repo, both dated 6 August, both from
`CB_SIM_FOUNDATION_HANDOFF_20260806_v1.zip`:

- `handoff/source/cb_foundation_external_gate.py` (26,405 bytes) — a strict consumer of external
  simulation workloads. Its docstring states the discipline plainly: producer `all_pass` and
  `BUILT` values are preserved as evidence, never accepted as this consumer's verdict.
- `handoff/source/cb_cross_runtime_contract_gate.py` (12,028 bytes) — a cross-runtime contract
  gate over the three-runtime probe results.

The repo has `cb_foundation_custody_gate_v2.py` (which already references cross_runtime),
`strict_receipt_consumer.py` and `strict_receipt_consumer_v2.py`. Those probably supersede both.
Status: `exists` on the Desktop, superseded `UNCHECKED`. One diff settles it.

## Novel content by kind

| ext | files | bytes |
|---|---|---|
| `.zip` (nested) | 18 | 41,733,196 |
| `.json` | 250 | 8,091,360 |
| `.md` | 389 | 6,182,222 |
| `.pdf` | 4 | 6,101,755 |
| `.py` | 399 | 5,139,922 |
| `.txt` | 81 | 1,554,431 |
| `.png` | 9 | 1,327,839 |
| `.jl` | 14 | 98,991 |
| `.tla` | 1 | 2,536 |
| `.lean` | 1 | 1,631 |

Of the 389 novel markdown files, 265 have basenames that appear nowhere in the repo and 124 are
different versions of documents the repo already holds. None of the 265 is named for a gate,
ClaimGate, ConstraintBox, mini-LevOS, FlowMind, ratchet, receipt or harness — checked by pattern.
The CB doctrine layer is already in the repo. What is absent is the physics and philosophy layer:
`ENTROPIC_GEOMETRY_PHILOSOPHY_FOURTH_EDITION.md` (318 KB),
`RATCHET_SYSTEM_MODEL_ORIENTATION_FOR_GEMINI_20260723.md` (182 KB), and the Gemini governance set.

Of the 399 novel Python files, 147 have basenames absent from the repo. They are sim-lane:
three-qubit GKSL tournaments, Conley-Morse probes, Hopf tori, basin engines, cross-runtime
oracles. That is layer work above CB, and the layer order says CB comes first.

## How to check this yourself

Rebuild the index from scratch and diff it against the committed one:

```bash
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 /private/tmp/claude-501/-Users-joshuaeisenhart-Codex-Ratchet/b1e33759-f392-47e0-8f05-c6ce7250426c/scratchpad/index_desktop_cb.py
```

Confirm the repo is ahead on a named module:

```bash
wc -c constraint_box/src/constraintbox/mini_levos.py
```

## What this verdict does not cover

- Whether the 265 absent documents contain owner rulings not yet captured. Not read, only named.
- Whether `cb_foundation_external_gate.py` is genuinely superseded. Not diffed.
- The 4 PDFs and 9 screenshots. Not read.
- Nothing has been moved or deleted. This is an index and a verdict, not a cleanup.
