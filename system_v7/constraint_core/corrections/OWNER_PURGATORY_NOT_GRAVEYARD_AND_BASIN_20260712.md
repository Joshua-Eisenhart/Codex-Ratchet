---
source: owner, 2026-07-12 (repeat of a prior correction that drifted back; binding)
status: BINDING — supersedes all "graveyard / dead stay dead / no re-entry" language in process surfaces
---

# 1. PURGATORY, not graveyard

A candidate that fails at rung k is NOT permanently dead. It goes to PURGATORY and the ENTIRE purgatory pool is
retried at the next rung, by rule. Failure is rung-scoped. Only the RECORD is immutable: the receipt "failed rung k
for reason r" is append-only and never overwritten. Re-entry is not silent because purgatory retry is explicit and
universal — everything gets its shot again at every new rung. (Owner: "the whole model and every single thing could
be tried at the first rung and fail but one. all those could be tested again at the next rung. there is no permanent
graveyard. i already made this correction before.")
All spec/engine language reading "graveyard", "no re-entry", "the dead stay dead" is to be corrected on next touch:
graveyard -> purgatory; no-re-entry -> no UNRECEIPTED re-entry within a rung; automatic pool-wide retry at each new rung.

# 2. Constraints -> attractor basin; basin implies MSS

Fallback success criterion (owner doctrine, already recorded): wide variation (starts, orders, mass candidates)
under the root constraints alone; convergence of everything to one structure = the attractor basin; the basin IS
MSS realized dynamically, without formal minimality machinery. Measured basin signature to date: all 75 gate
orderings converge to the identical survivor set (root_order_open_run_v0_5). Nonassociativity may arise mid-process
and further constrain the basin — consistent with the N=3 census (99.8% of minimal survivors nonassociative).

# 3. Level structure of the root constraint

The constraint on distinguishability is THE root. Finitude (F01) = scope condition on realized runs. The root
constraint expressed at the ELEMENT level = probe-relative identity; at the ORDER level = noncommutation (N01,
activated from the start by owner choice); at the GROUPING level = nonassociativity (T01, activates when grouping
distinctions become live). N01 and T01 are not separate axioms beside the root — they are the root constraint at
two levels. (Matches root_axioms: "One root relation appears at three levels.")
