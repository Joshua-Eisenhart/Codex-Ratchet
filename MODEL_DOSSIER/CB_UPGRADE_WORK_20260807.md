# CB upgrade work

Build these. In order. Nothing under `constraint_box/` is tracked, so
everything reverses.

Interpreter: `~/.local/share/codex-ratchet/envs/main/bin/python3`
Working dir: `~/Codex-Ratchet`

---

## 1. Build the Decision wave

Three councils, none of which exist:
`decision.context_strategy`, `decision.move_selection`,
`decision.evidence_boundary`.

Pattern to copy: `constraint_box/scripts/cb_wave_falsifier_v2.py`.
Each council is N members answering the SAME question under different
salience — not one question split into parts. Minimum 5 members per
council (the conformance floor is 5-10 child receipts per parent).

Required children per route, from the Wizard packet:
- context_strategy: voice.strategy, voice.systems, voice.hume, voice.feynman
- move_selection: voice.factory, voice.orwell, voice.hume, lane.direct, lane.alternative
- evidence_boundary: voice.hume, voice.popper, voice.feynman, guard.receipt_audit

Declared outputs the gate should check: selected move, why now,
rejected alternatives, operating boundary, evidence boundary, falsifier.

## 2. Build the Follow-Up wave

`follow_up.next_move_selector`, `follow_up.lane_builder`,
`follow_up.compile_gate`.

Lanes: direct, alternative, reframe, back, wildcard.
The open question is whether five lanes cover the option space — build a
test where an option maps to zero lanes.

## 3. Run the two Failure councils that have never run

`failure.premortem` (as the ROUTE, with its four required children —
not the standalone skill invocation, which is a different thing) and
`failure.loophole_auditor`.

`cb_skill_premortem.py` runs the skill to its contract; that is not the
same as running the route.

## 4. Wire the managers

Five specced, never run: `run_controller`, `child_health`,
`route_truth`, `output_compiler`, `strategy_memory`. Plus
`council-collapse-auditor`.

`cb_strategy_memory.py` exists as a Python class and works (6/6). The
other five don't exist. `child_health` matters most — its verbs are
kill, demote, reroute, shrink, override, block_full, accept_with_reason.

## 5. Run skills as skills

About 110 exist across `~/.codex/skills` (44), `~/.agents/skills`,
`~/.claude/skills` (7), and the Wizard packet. One has been run.

`cb_skill_premortem.py` is the pattern: read the SKILL.md, execute its
declared procedure, gate the artifacts against the skill's OWN declared
output shape. Next candidates: `ultraqa`, `wizard-loophole-auditor`,
`codex-autoresearch`.

## 6. Route real swarm output through the gates at scale

`cb_run2.py` composes agent spec + mini-MMM + MMM pack + skill and gates
the returns. It has run once with six voices.
`cb_multi_provider.py` gives cross-provider lanes (Haiku + 17 free
OpenRouter models incl. 7 NVIDIA Nemotron).

Scale it: many claims, many lanes, gated, indexed, with the refusal
profile measured.

---

## Known traps

- `cb_integrated_run.py` scans `REPO.rglob("*")`, which includes its own
  receipts and `constraint_box/handoff/`. Its `never_run` measure is
  latched at 0 and is meaningless until those are excluded. Real
  execution coverage is in `constraint_box/config/member_role_wave_v1.json`
  (21 of 43).
- `cb_loop.py --cycles 20` bills provider calls and its autoresearch leg
  raises `KeyError: 'ladder'` every time. Don't run it.
- `cb_wave_falsifier_v3.py` hardcodes `councils_run: 0`, so it kills
  every target. Don't trust its verdicts until that's parameterised.
- `cb_all_tools_council.py` twins differ on nine fields at once; ten of
  its 23 members pass on `promotion_allowed` alone.
- Three receipts in `constraint_box/receipts/` (and three copies in
  `handoff/`) contain negation-inverted text from a digger regex. Two
  read as the opposite of their source.

None of these block the six build items above. Fix them if they get in
the way.

## What CB is

A deterministic gate over LLM swarms. Many diverse models in nested
councils arranged in waves; code decides admission, never a model. It
doesn't judge truth — it judges whether a claim arrived in a shape that
can be checked.

Owner's own words: `~/Desktop/CB_COMPLETE_HANDOFF.zip` → `00_OWNER/`.
Read that before any model-written file, this one included.
