| A6 | token law `TiSe/SeTi/...`; `b6=-b0*b3`; left/right `L_A(rho)=A rho`, `R_A(rho)=rho A`; commutator `[A,rho]=i(a x r).sigma`; `gap=sqrt(2)||a x r||`; closure forms commutator/Kraus/unitary/dephasing | compare up/down composed stages; compute noncommutation gap; closure/CPTP checks | token precedence and action side not automatically identical; primitive side actions alone not physical channels [D:1115-1350; S:103-117; L:68-101] |

## E. Gaps / Unmeasured Relations

| gap | why |
|---|---|
| A0-A4 | no direct law or explicit pairwise independence statement in requested sources; only both appear in engine/entropy scaffold [S:163-165,179-183] |
| A0-A5 | no direct law; strong anti-conflation because entropy/cut polarity, dephasing entropy, unitality, and feedback polarity are separate columns [S:111,116,276,305-307] |
| symbolic A3/A4/A5 overlays | inner/outer, runtime order, and operator-family anchors are strong, but chirality/type/flux, clockwise/counterclockwise, and S-curve/lobe overlays need bounded discriminators [W:399-412,414-483,527-570] |
| Axis0 bridge/cut | final `Xi -> rho_AB -> Phi0` bridge not closed; single-spinor scalar cannot substitute [Q:99-147,198-224; W:403] |
| 64 runtime schedule closure | address/enumeration exists, but dynamic distinctness and full visitation are not established; prior `eng_64` snapshot reported only 16 distinct fingerprints [W:359-366,388,493-517] |


tokens used
143,183
Using skill: `using-superpowers` for mandatory session workflow.

**Source Legend**
`D` = `system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md`  
`Q` = `system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md`  
`S` = `system_v7/constraint_core/reference_docs_from_josh/physics_program/working_math_scaffold_20260609.md`  
`W` = `/Users/joshuaeisenhart/wiki/concepts/igt-axes-terrain-source-extraction-2026-06-04.md`  
`L` = `system_v7/constraint_core/sims_and_scripts/axis_laws_dual_proof.py`  
`O` = `system_v7/constraint_core/sims_and_scripts/coratchet_axis_orthogonality_sim.py`  
`M` = `system_v7/constraint_core/sims_and_scripts/manifold_laws_smt_proof.py`  
`X` = `system_v7/constraint_core/sims_and_scripts/axis0_xor_sim.py`

## A. B-Bit Algebra

| bit | exact definition / formula | operational measurement | caveat |
|---|---|---|---|
| `b0` | chart: `b_0 = sign(cos(2 eta)) = sign(r_z)`; threshold `eta=pi/4`; bridge target `sign(Phi_0(Xi(history, geometry)))` | sample eta on both sides, compute `S_eta`, `dS/deta`, `sign(cos(2eta))`; bridge requires `rho_AB`, `I_c`, `S(A|B)`, `I(A:B)` | chart and bridge must not be silently identified; Ax0 bridge open [D:190-205,238-249,267-301; Q:99-147,334-358] |
| `b1` | Axis1 branch: `{Se,Ni}` vs `{Ne,Si}`; local sign `chi1(Se)=chi1(Ni)=+1`, `chi1(Ne)=chi1(Si)=-1`; boolean sim uses `Se/Ni=0`, `Ne/Si=1` | verify branch plus A2 maps to topology; QIT kernel: proper CPTP vs unitary branch | labels differ: Deep says open/isothermal vs closed/adiabatic; Q says proper CPTP vs unitary; preserve as aligned branch split, not identical wording [D:313-329,431-489; Q:227-245,298-299; L:24] |
| `b2` | Axis2 frame: direct `{Se,Ne}` vs conjugated `{Ni,Si}`; local sign `chi2(Se)=chi2(Ne)=-1`, `chi2(Ni)=chi2(Si)=+1`; boolean sim uses direct `0`, conjugated `1` | direct: `tilde(rho)=rho`; conjugated: `tilde(rho)=V_s^dagger rho V_s` plus transport/gauge term | not chirality and not dot/teardrop kernel by itself [D:495-603; Q:248-273,299; L:25] |
| `b3` | two readouts: geometry path `fiber|lifted_base`; XOR readout `outer -> +1`, `inner -> -1` | fiber: density stationary; lifted-base: density changes and horizontal condition holds | do not use raw fiber/base in the XOR; Type2 swaps chart role, so raw path would invert rows [D:605-743,745-788; Q:57-73; S:55-64,114] |
| `b4` | Axis4 loop-order family: deductive `U o E o U o E`; inductive `E o U o E o U`; scaffold also `Phi_D=e^{tau_R L_R}e^{tau_C L_C}`, `Phi_I` reversed | compute `Delta_4 = Phi_deductive(rho)-Phi_inductive(rho)` on finite probes | no canonical `+/-` sign for `b4` found in requested docs; symbolic clockwise/counterclockwise open [D:790-901; S:115,165,179-181; W:533-570] |
| `b5` | Axis5 operator family: dephasing/pinching `{Ti,Te}` vs rotation/unitary `{Fi,Fe}` | dephasing contracts fixed-algebra distance / transverse components; rotation preserves `spec(rho)`, `S(rho)`, `Tr(rho^2)`, `||r||`; sim: T `dS>0`, F `dS=0` | no canonical `+/-` sign found; S-curve/lobe and `FeFi/TiTe/TeTi` overlays unresolved [D:903-1114; S:75,116,145; O:20-21,71-79; W:455-483] |
| `b6` | Axis6 token precedence/action audit: `up = operator written first`, `down = terrain written first`; law `b_6 = - b_0 b_3` | compare token-up vs token-down with terrain/operator fixed; compute `gap_A(rho)=||A rho-rho A||_F`; record action side and closure | `b3` in law is chart role, not raw path; primitive side action is not a CPTP channel unless closure is specified [D:1115-1350; S:103-117; O:77-80] |

**Laws**

| law | exact form | computed / controls |
|---|---|---|
| Axis0 parity | boolean: `a0 = a1 XOR a2`; sign convention: `chi0 = chi1 chi2` | `axis_laws_dual_proof.py` proves the unique map is XOR in Z3+cvc5; erasing the `Ni` constraint flips uniqueness. `axis0_xor_sim.py` shows XOR is not linearly separable [Q:292-316; L:6-13,57-64,98-101; X:6-24,34-52] |
| Axis6 bilinear law | `b6 = -b0*b3` | Z3+cvc5 force coefficient `-1`, unique, with no linear law; coratchet proves `b0` and `b6` negations UNSAT, and erasing each law frees it SAT [D:715-743,1135-1159; L:68-101; O:22-25,87-140] |
| topology join | `A1 x A2 -> {Se,Ne,Ni,Si}` | source-locked reduced join: proper CPTP/direct `Se`, proper CPTP/conjugated `Ni`, unitary/direct `Ne`, unitary/conjugated `Si` [D:331-352,400-429; Q:277-288,351-353] |
| token identity | `A1 x A2 x A5 x A6 = 16 ordered tokens` | 4 topologies x 2 operator families x 2 precedence values; corrected projection [D:1351-1379,1621-1629; W:350-366,387-394] |
| loop-placement projection | `A3 x A4 x A5 x A6 = 8 paired signatures`, not 16 tokens | same signature can pair two topology rows; engine chart required [D:1381-1429,1572-1578] |
| terrain placements | `terrain x sheet x path = 16 terrain placements` | generator/path objects, not token identities; must be joined by engine chart [D:1431-1462; S:100-107] |
| Axis4 order gap | `Phi_deductive != Phi_inductive` when noncommutation makes order observable | complete dephasing can erase the effect; controls must collapse under commuting/wrong structure [D:840-901; W:392,533-570] |
| manifold extras | access 8/16 forced; pole-mirror forced only by zero-sum plus cross-sheet; entropy eigenvalue identity makes entropy blind to Axis2 rotations | SMT/sympy script states and asserts these; zero-sum alone is explicitly degenerate [M:1-19,29-70] |

## B. Pairwise Relation Table, Axes 0-6

| pair | status | extraction |
|---|---|---|
| A0-A1 | LAW-COMPONENT | `a0=a1 XOR a2`; A1 alone does not determine A0. Source also says A0 is cross-cutting polarity, not same kind as A1/A2 [D:396-398; Q:302-316; L:6-13] |
| A0-A2 | LAW-COMPONENT | same XOR/chi closure; A2 alone does not determine A0 [Q:292-316; X:6-24] |
| A0-A3 | LAW-COMPONENT | `b6=-b0*b3`; A3 enters through chart role only [D:715-743,1135-1159] |
| A0-A4 | UNKNOWN/GAP | no direct law or explicit pairwise independence statement found; both appear in engine/entropy scaffolds but not tied pairwise [S:163-165,179-183] |
| A0-A5 | UNKNOWN/GAP with anti-conflation | no direct pair law; must not collapse entropy/cut Ax0 into dephasing entropy Ax5 or unitality [S:111,116,276,305-307] |
| A0-A6 | LAW | `b6=-b0*b3`; A0 color/hemisphere aliases are not Axis6 up/down [D:368-369,1135-1159; L:68-101] |
| A1-A2 | LAW-JOIN | `A1 x A2 -> terrain`; reduced join source-locked [D:331-352; Q:277-288,351-353] |
| A1-A3 | ORTHOGONAL-COMPUTED | `b1,b3` are primitive free DOF in the 5-free lattice [O:22-25,81-85,136-140] |
| A1-A4 | ORTHOGONAL-COMPUTED | `b1,b4` primitive free [O:22-25,81-85] |
| A1-A5 | ORTHOGONAL-COMPUTED + OVERLAY-RISK | primitive free; risk: both carry unitary/CPTP-flavored language, but A1 is topology/legality branch, A5 is operator family [Q:227-245; D:903-1114; O:22-25,81-85] |
| A1-A6 | DERIVED-LAW COMPONENT | `b6=-(b1*b2)*b3` through `b0=b1*b2`; no A1-only relation [O:77-91; L:24-27,68-101] |
| A2-A3 | ORTHOGONAL-COMPUTED + OVERLAY-RISK | primitive free; A2 is frame, A3 is path/chart role [D:491-603,605-743; O:22-25,81-85] |
| A2-A4 | ORTHOGONAL-COMPUTED | `b2,b4` primitive free [O:22-25,81-85] |
| A2-A5 | LAW-JOIN / AFFINITY | A2 x A5 selects operator identity/native frame: direct uses Ti/Fi, conjugated uses Te/Fe [O:8-12; W:341-348] |
| A2-A6 | DERIVED-LAW COMPONENT | A2 contributes to `b0=b1*b2`, then to `b6`; no A2-only relation [O:12,22-25,77-91] |
| A3-A4 | ORTHOGONAL-COMPUTED + OVERLAY-RISK | primitive free; same `(A3,A4)` pairs occur in both engine types, so engine type not recovered from A3xA4 [D:1401-1429; O:22-25,81-85] |
| A3-A5 | ORTHOGONAL-COMPUTED | `b3,b5` primitive free; their larger projection with A4/A6 gives paired signatures, not tokens [D:1381-1399; O:22-25,81-85] |
| A3-A6 | LAW | `b6=-b0*b3`; `b3` is inner/outer chart role, not raw fiber/base [D:715-743,1135-1159] |
| A4-A5 | ORTHOGONAL-COMPUTED + OVERLAY-RISK | primitive free; runtime loop labels FeTi/TeFi correlate with order, but A4 cannot identify operator family alone [D:828-838,864-878; O:22-25,81-85] |
| A4-A6 | ORTHOGONAL-COMPUTED + OVERLAY-RISK | A4 is loop order; A6 is token precedence/action side; not the same order DOF [D:790-797,876-878,1282-1297; S:179-181; O:22-25,81-85] |
| A5-A6 | LAW-JOIN | together choose signed operator family/order within token identity, but topology still needs A1xA2 [D:1351-1373,1463-1515; O:20-25] |

## C. Anti-Conflation Rules

| trap | discriminating observable |
|---|---|
| Axis vs terrain/operator/token/engine layers | axis is projection/readout over `M(C)`; do not collapse terrain generators, operator channels, ordered grammar, or engine composition into axes [D:24-44; S:23,278-287] |
| A0 chart vs A0 bridge | chart: `sign(cos(2eta))`; bridge: `Phi0(Xi(...))` on cut state. Observable: actual `rho_AB`/cut coherent-information discriminator [D:142-152,244-249,286-301; Q:99-147,198-224] |
| A0 entropy drive vs Ax5 entropy/dephasing | A0 reads feedback/cut polarity; A5 distinguishes dephasing vs rotation. Observable: cut/coherent-info or participation response for A0 versus fixed-algebra contraction/purity preservation for A5 [S:111,116,274-276,305-307; D:1080-1097] |
| A1 branch vs A5 operator family | A1: terrain/topology legality branch and needs A2 for terrain. A5: judging operator family. Observable: A1xA2 topology join vs operator PTM/invariant split [D:331-352,903-1114; Q:227-245] |
| A2 frame vs A3 chart/path role | A2: direct/conjugated transport equation. A3: fiber/lifted-base path and inner/outer chart role. Observable: gauge/transport term vs density-stationary/path-horizontal witness [D:515-543,574-603,625-680,745-788] |
| A3 loop class vs A4 loop order vs A6 precedence | A3: path density motion; A4: `Phi_D` vs `Phi_I` loop-order gap; A6: token-up/down plus `A rho` vs `rho A` gap. One measurement each: `||rho_path(u)-rho(0)||`, `||Phi_D-Phi_I||`, `||A rho-rho A||` [D:745-788,850-889,1299-1320; S:179-181] |
| A3 raw fiber/base vs A3 XOR chart role | XOR uses inner/outer chart role, not raw path; Type2 swaps path roles. Observable: receipt must record both `geometry_path` and `chart_role` [D:715-743,1141-1155,1463-1494] |
| A4 clockwise/counterclockwise overlay vs runtime order | symbolic direction is open; runtime anchor is `UEUE/EUEU` or `Phi_D/Phi_I`. Observable: predeclared symbol-direction coding must predict finite order split under controls [W:527-570] |
| A5 S-curve/lobe overlay vs operator-family split | visual lobe coding is open; operator family is dephasing/rotation. Observable: entropy/purity/contractivity/orbit-preservation split beats label shuffle [W:449-483] |
| A6 token precedence vs physical action side | token order and QIT action side are related but not identical; primitive `A rho`/`rho A` is not a channel without closure. Observable: record `token_precedence`, `action_side`, `closure_type`, CPTP checks [D:1161-1267] |
| 16 ordered tokens vs 16 terrain placements | tokens = topology/operator family/precedence; placements = terrain/sheet/path. Observable: token enumeration vs `(X_tau,s, Gamma_l^s)` placement receipt; engine chart joins them [D:1351-1462] |
| `A3 x A4 x A5 x A6` vs token identity | that projection gives 8 paired signatures, not 16 tokens. Observable: enumerate both projections and catch paired topology collapse [D:1375-1399,1572-1578] |
| Flux as axis content | flux may be manifold/cross-axis observable but cannot replace A3/A4/engine chart until admitted. Observable: remove chirality, flatten fiber/base, collapse seats, remove operator action, scramble scalars [D:1580-1605; S:123-128,282-287] |
| IGT/Jung/I-Ching labels vs math ontology | labels are correlation layers/symbolic witnesses unless invariant-tested. Observable: label shuffle must fail while operation-grounded claims survive [W:52-60; S:181] |

## D. Full Explicit Math Assembly

| axis | merged formula set | witness / controls | disagreements/open |
|---|---|---|---|
| A0 | `rho_bar=diag(cos^2 eta,sin^2 eta)`; `S_eta=-cos^2 eta log cos^2 eta - sin^2 eta log sin^2 eta`; `dS/deta=-sin(2eta)log(tan^2 eta)`; `b0=sign(cos2eta)`; bridge candidates `I_c`, `S(A|B)`, `I(A:B)`, shell sum | eta sampling; cut-state bakeoff; bridge fails if `Xi` absent or candidate cannot separate controls | exact bridge/cut still open; chart/bridge not identical [D:154-231,267-301; Q:99-224; S:111,264-276] |
| A1 | `{Se,Ni}` vs `{Ne,Si}`; QIT split proper CPTP vs unitary; with A2 maps to terrain | verify `(A1,A2)->topology`; source-lock product table | label variants: open/isothermal, closed/adiabatic, CPTP/unitary, bath gate; preserve alternatives [D:303-489; Q:227-245; S:112] |
| A2 | direct `tilde(rho)=rho`, `dot(rho)=L(rho)`; conjugated `tilde(rho)=V_s^dagger rho V_s`, `dot(tilde rho)=V_s^dagger L(V_s tilde rho V_s^dagger)V_s - i[-K,tilde rho]`, `K=iV_s^dagger dot(V_s)` | direct rows use same frame; conjugated rows must include transport/gauge correction | not chirality; dots/teardrops overlay only [D:491-603; Q:248-273; S:113] |
| A3 | fiber `gamma_f=psi(phi0+u,chi0;eta0)`, density stationary; base `gamma_b=psi(phi0-cos2eta0*u,chi0+u;eta0)`, horizontal `A_Hopf(dot gamma)=0`; chart role inner/outer | density motion, horizontal condition, spinor closure/Berry phase; Axis3 collapsed if only final density compared | older chirality/type/flux readings live but weaker; raw path not XOR bit [D:605-788; Q:57-73; S:114,145; W:420-447] |
| A4 | deductive `U o E o U o E`; inductive `E o U o E o U`; scaffold generator order `Phi_D=e^{tau_R L_R}e^{tau_C L_C}`, `Phi_I` reversed, first difference approx commutator | `Delta4` finite-probe norm; commuting/dephasing controls collapse | symbolic clockwise/counterclockwise open; FeTi/TeFi labels cannot override order formula [D:790-901; S:115,165,179-181; W:527-570] |
| A5 | Ti/Te dephasing formulas, fixed algebras, distances `D_z,D_x`; Fi/Fe unitary rotations, preserved spectrum/entropy/purity/Bloch norm | dephasing contracts transverse components; rotation preserves orbit; coratchet T entropy-producing, F neutral | S-curve/lobe and label drift open [D:903-1114; S:116; O:70-80; W:449-483] |
| A6 | token law `TiSe/SeTi/...`; `b6=-b0*b3`; left/right `L_A(rho)=A rho`, `R_A(rho)=rho A`; commutator `[A,rho]=i(a x r).sigma`; `gap=sqrt(2)||a x r||`; closure forms commutator/Kraus/unitary/dephasing | compare up/down composed stages; compute noncommutation gap; closure/CPTP checks | token precedence and action side not automatically identical; primitive side actions alone not physical channels [D:1115-1350; S:103-117; L:68-101] |

## E. Gaps / Unmeasured Relations

| gap | why |
|---|---|
| A0-A4 | no direct law or explicit pairwise independence statement in requested sources; only both appear in engine/entropy scaffold [S:163-165,179-183] |
| A0-A5 | no direct law; strong anti-conflation because entropy/cut polarity, dephasing entropy, unitality, and feedback polarity are separate columns [S:111,116,276,305-307] |
| symbolic A3/A4/A5 overlays | inner/outer, runtime order, and operator-family anchors are strong, but chirality/type/flux, clockwise/counterclockwise, and S-curve/lobe overlays need bounded discriminators [W:399-412,414-483,527-570] |
| Axis0 bridge/cut | final `Xi -> rho_AB -> Phi0` bridge not closed; single-spinor scalar cannot substitute [Q:99-147,198-224; W:403] |
| 64 runtime schedule closure | address/enumeration exists, but dynamic distinctness and full visitation are not established; prior `eng_64` snapshot reported only 16 distinct fingerprints [W:359-366,388,493-517] |


