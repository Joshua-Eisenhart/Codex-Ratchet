# Manifold Wizard Operation

Status: working operation note for candidate/root repair loops; not final
manifold admission authority.
Scope: current geometric-constraint-manifold candidate repair loops

## Object

The working root object is the geometric constraint manifold candidate: nested simultaneous
constraint shells with order-sensitive geometry, not axis labels and not only
the Weyl/chirality layer. PEPS/PEPS3D, Axis0, attractor-basin receipts,
graph/proof tools, auto_LiRPA, and le-wm are evidence surfaces over that root.
They are not final manifold, real-basin, Axis0, bridge, engine, or physics
promotion.

## MMM Loading Rule

Current wiki upgrades are out of scope for this operation. Use the current
Wizard v4.2 packet as the runtime compression layer until Hermes produces a
newer packet.

- Main Codex controller loads the v4.2 packet plus either the full MMM or the
  compact MMM plus all relevant mini-MMM slices for the turn.
- External Grok/Gemini/Claude lanes load `COMPACT_MMM_v4_2.md` by default.
- Specialized external lanes also load the relevant mini-MMM slices, such as
  premortem, falsifier, evidence-boundary, compile-gate, expert, or lane cards.
- A provider receipt only counts as MMM-loaded when it records
  `wizard_mmm.mmm_loaded=true`, source paths, digests, route card, council role,
  mini-MMM ids, and prompt hash.

MMM-informed summaries are useful, but they do not count as MMM-loaded council
lanes.

## Practical External Council Standard

This section defines advisory external provider/council evidence only. It does
not satisfy Codex-native Wizard v4.2 Max Assembly topology for sim, proof,
runner, tool-stage, queue, or result work. Under the current repo contract,
those work types still require sim-mode Max Assembly unless the current user
request explicitly narrows the task or a fresh preflight proves the full route
inadmissible.

For external manifold advisory lanes, the useful standard is:

- real model call;
- compact MMM present in the prompt;
- relevant mini-MMM slice present when the lane is specialized;
- distinct role and route card;
- durable provider receipt;
- concrete finding that changes, kills, blocks, or sharpens the next move.

Full v4.2 parent/child topology remains stricter than this and must be labeled
separately. Do not count a provider receipt meeting this advisory standard as
operational Wizard satisfaction.

## Loop Shape

Each manifold loop should keep these checks separate:

1. Decision lane: choose the smallest manifold-rooted repair, not the broadest
   receipt count.
2. Failure lane: run a premortem or falsifier at least every third loop and
   whenever a scout can be mistaken for promotion.
3. Tool lane: isolate one tool/function/manifold role per packet before
   claiming coupling.
4. Graph/proof lane: test z3/cvc5, rustworkx, PyG, XGI, TopoNetX, GUDHI, and
   related proof tools against a non-tautological predicate.
5. Tensor lane: ensure PyTorch/autograd, PEPS/PEPS3D/MPS, auto_LiRPA, and le-wm
   carry branch-dependent signal rather than ornamental execution.
6. Compile lane: name killed claims, open claims, next receipt, exact validator,
   stop condition, and claim ceiling.

## Current Manifold Stop Conditions

Stop or shrink the loop when:

- the next move treats row counts as manifold depth;
- a named layer is index-driven rather than semantically implemented;
- a proof predicate would pass under label scramble or arbitrary replacement;
- le-wm or auto_LiRPA executes but does not discriminate branch-dependent data;
- Axis0 scalar projection is treated as repaired without a receipt that keeps
  multidimensional actuation load-bearing;
- provider output is cited as evidence instead of a proposal/falsifier source.

## MMM-Loaded Primary Provider Entry Points

- `system_v5/ops/formal_scouts/run_manifold_integration_provider_audit.py`
- `system_v5/ops/formal_scouts/run_tool_foundation_provider_audit.py`

Both entry points now build prompts with compact MMM plus route mini-MMM slices
and record MMM provenance in provider receipts.

Other `run_*provider*audit*.py` launchers in this folder are provider-audit
surfaces only. Treat them as legacy, specialized, or non-MMM routes unless their
source explicitly records the same MMM provenance fields and current grounding.

Use `--write-prompt <path>` to export the exact same MMM-loaded prompt for a
Claude Bridge Sonnet/Opus lane. Normalize the bridge output into a provider
receipt before counting it in the indexed receipt estate.
