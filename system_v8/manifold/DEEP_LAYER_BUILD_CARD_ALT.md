# Build card: v8 deep-layer manifold — REDUNDANT LANE (codex2 / gpt-5.5)

Execute system_v8/manifold/DEEP_LAYER_BUILD_CARD.md EXACTLY, with ONLY this
namespace change so you never collide with the primary lane:

- every new engine module gets suffix `_alt` (connection_layer_alt.py,
  history_layer_alt.py, persistence_layer_alt.py, chirality_layer_alt.py,
  whole_manifold_v2_alt.py, verify_deep_alt.py,
  deterministic_replay_deep_alt.py)
- runner is RUN_DEEP_ALT.sh writing into results/deep_alt/
- report is DEEP_RESULTS_ALT.md

You are an INDEPENDENT implementation for semantic redundancy: do NOT read
any file created by the primary lane (no connection_layer.py, no
results/deep/, no DEEP_RESULTS.md, none of the non-_alt deliverables even if
they exist). Derive everything from the card, the 9-packet source JSON, the
vendored inputs, and the existing welded results. The two implementations
will be diffed on their COMPUTED values (frontiers, noncommutation status,
chirality status); agreement is the redundancy signal, so contact with the
primary lane's code would destroy the point.

All other constraints in the primary card bind unchanged (no deletions, new
files only, stdlib python, deterministic, promotion_allowed false).
