---
status: corrected stage-word/loop-readout structure (Hermes formalization 2026-06-09 over the owner's charts; the read rule is grounded in the charts themselves — outer/inner result columns read single components)
claim_ceiling: structural formalization; readout grammar fence unchanged (WIN/LOSE = readout, not payoff)
---

# The Two-Engine Readout Automaton

READ RULE: each stage carries a TWO-COMPONENT word (outer component uppercase, inner lowercase); the ACTIVE LOOP reads ONE component. "WINlose" means outer=WIN, inner=lose — never "the loop reads WINlose."

Stage words: Se=LoseWin, Ne=WinLose, Ni=LoseLose, Si=WinWin (the complete 2-bit alphabet).
Carnot orders: C_D (deductive/closure) = Se->Ne->Ni->Si; C_I (inductive/expansion) = Se->Si->Ni->Ne.
Placements: Type1 = outer:C_D + inner:C_I; Type2 = outer:C_I + inner:C_D.

THE 16 LOOP-READOUT STRATEGIES (2 types x 2 loops x 4 stages), as readout sequences:
- Type1 outer (deductive):  LOSE -> WIN -> LOSE -> WIN   (alternating, period 2)
- Type1 inner (inductive):  win -> win -> lose -> lose    (paired, period 4)
- Type2 outer (inductive):  WIN -> WIN -> LOSE -> LOSE    (paired, period 4)
- Type2 inner (deductive):  lose -> win -> lose -> win    (alternating, period 2)
STRUCTURE NOTE: deductive order always yields the ALTERNATING readout; inductive order always yields the PAIRED readout — loop order determines readout periodicity regardless of engine type; engine type sets phase/casing. (Checkable against the committed rigidity result: signs+operator -> unique table.)

ABSTRACT OBJECT (the thing to encode in the 64-matrix sim): a two-layer directed automaton / constrained fibered system —
base S = {Se,Ne,Ni,Si}; fiber per stage = (outer,inner) components; sheets = Type1/Type2; allowed paths = C_D, C_I; readout R(engine,loop,stage) -> {WIN,LOSE,win,lose}; operator action = signed precedence on transitions.
Expansion discipline: 4 -> 16 -> 64 by CONSTRAINED PLACEMENT, not free combination (each DOF fibered over stage geometry and constrained by loop/order/operator rules + Axis-0 polarity).

STACKING: a full transition = (engine type, loop, stage_i->stage_j) + Carnot legality + Szilard measurement/memory legality + IGT active-loop readout.
