# Bundle 14 direct/wildcard layout compare receipt

Scope: compare two render layouts for the collapsed Optional Sub-follow-up issue, recommend one, and draft a compact rerender that keeps Results and Optional Sub-follow-up in contract.

## Checked
- `~/.hermes/HERMES.md`
  - Results is the place for message-time lane/voice worker receipts.
  - Optional Sub-follow-up is only for extra actions beyond the message-time worker set.
  - `All` stays controller-side and should read like an ordered composition, not a flattening pass.
- `~/.hermes/skills/note-taking/hermes-follow-up-menu-style/SKILL.md`
  - keep the fixed shape: main answer -> Results -> optional Sub-follow-up -> footer
  - during format tuning, do not use Sub-follow-up as a leftovers queue
- `~/.hermes/task-cards/FOLLOWUP_RUNTIME_ADAPTER.md`
  - each visible lane/voice needs an action class and compact receipt
- `~/.hermes/pastes/paste_3_220256.txt`
  - bundle 14 full = rerender + compare layouts + audit starvation + full voice reruns

## Layouts compared

### Layout A: dense Results / light Optional Sub-follow-up
Use Results to carry the actual message-time worker field. Keep Optional Sub-follow-up short and only for the next extra moves.

Pros
- matches the current contract directly
- shows what already ran before offering more branches
- reduces duplication between Results and follow-up menu
- makes collapse easier to diagnose because the worker field stays visible

Risk
- can get list-heavy if every lane is rendered with equal weight

### Layout B: light Results / richer Optional Sub-follow-up
Keep Results minimal and move more of the visible option field into Optional Sub-follow-up.

Pros
- feels generous and menu-rich
- gives the user more visible steering room at a glance

Risk
- blurs message-time worker receipts with extra actions
- recreates the exact failure mode: too much semantic load pushed into Optional Sub-follow-up
- makes it harder to tell what actually ran vs what is merely offered next
- invites `All` bundles to swallow distinctions that should stay in Results

## Recommendation
Recommend Layout A for this exact issue.

Why
- the problem was collapse in Optional Sub-follow-up
- the contract already says the active worker field belongs in Results
- putting more weight back into Optional Sub-follow-up would reintroduce the same ambiguity the repair is trying to remove

## Short candidate rerender
Bottom line
- Use dense Results and keep Optional Sub-follow-up short here.
- The worker field belongs in Results; Optional Sub-follow-up should only carry the remaining extras.

Checked
- `HERMES.md`: Results = message-time worker receipts; Optional Sub-follow-up = extras only.
- `SKILL.md`: tuning should replenish options without turning Sub-follow-up into the main payload.

Results
- 🎯 Direct (spawn_worker) — compared two layouts for this collapse; dense Results / light Optional Sub-follow-up fits the contract better.
- 🃏 Wildcard (spawn_worker) — side-by-side stress test says the richer-menu version looks fuller but hides what already ran and invites duplicate surface area.

Optional Sub-follow-up
- 🏭 Factory (spawn_worker) — audit starvation: where admission caps or suppression rules are thinning the extra-action field
- 🔬 Feynman (spawn_worker) — rerun the remaining voice pass with an explicit pass/fail rule
- 🔗 All-of-the-above lean — run the starvation audit, then rerender the remaining voice pass on this layout

bundle14/layout-compare | recommended = dense Results / light Optional Sub-follow-up | next = run starvation audit against this layout | 🛡️contract kept | 🧹no Results/Sub-follow-up duplication
