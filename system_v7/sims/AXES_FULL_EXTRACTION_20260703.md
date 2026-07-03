**Axis 5**

Name/readout: operator/generator family (`IGT:336-358`; `Deep:903-1114`).  
Math: `{Ti,Te}` dephasing/projection vs `{Fi,Fe}` rotation/unitary. Ti/Te are pinching/GKSL semigroups; Fi/Fe are Hamiltonian/unitary groups; witnesses are entropy/purity/contractivity vs orbit/spectrum preservation (`IGT:344-356`; `Apple:935-990`, `1072-1078`; `Signed:37-53`, `640-656`, `772-825`).  
Status/sims: strong operator split; S-curve/lobe overlay open (`IGT:358-366`; `Wiki:449-483`). `wb_axis5_spectral_gradient_julia` is a tool-lego fit probe, all-pass but candidate/non-promotion (`system_v5/julia_carrier/wb_axis5_spectral_gradient_julia_results.json:29-49`, `8940-8949`).  
Competing readings: dephasing/rotation, gradient/spectral, S-curve/lobe, `FeFi` vs `TiTe`/`TeTi`, unequal win/loss overlays (`Scaffold:116`, `145`; `Signed:683-690`; `Wiki:455-463`, `483`).  
Geometry-contamination check: clean if kept as operator-family selection. Contaminated if S-curve/lobe, visual weighting, or terrain attraction geometry replaces the channel/generator invariant (`Wiki:461-470`, `476-483`).

**Axis 6**

Name/readout: composition order / sidedness / precedence (`IGT:368-392`; `Deep:1115-1350`; `Signed:897-953`).  
Math: token precedence `up=operator written first`, `down=terrain written first`; channel order `Phi_T o O` vs `O o Phi_T`; primitive action-side `L_A(rho)=A rho` vs `R_A(rho)=rho A`; gap `||A rho - rho A||_F`; rows must record token precedence, action side, and closure type (`IGT:376-392`; `Deep:1119-1139`, `1161-1240`, `1242-1320`; `Signed:917-943`, `955-995`).  
Status/sims: strong math/symbol alignment, but action-side and token-order are related, not automatically identical (`IGT:388-392`; `Signed:932-943`). `ax6_julia_results` has bounded finite-map/order-sensitive receipt with promotion blocked (`system_v5/julia_carrier/ax6_julia_results.json:22-26`, `52`, `198-201`).  
Competing readings: up/down token, left/right action, judging-first/perceiving-first, outward/inward functional direction; outward/inward is open (`Signed:932-939`, `1017-1034`; `Deep:1282-1297`). `b6=-b0*b3`, but `b3` is chart-role inner/outer, not raw fiber/base (`Deep:1135-1159`; `Scaffold:117`).  
Geometry-contamination check: high risk. Because `b6` depends on `b0` and chart-role `b3`, using raw fiber/base, flux, or geometry path as the precedence bit contaminates the definition (`Deep:1148-1155`, `1282-1297`).

**Axes 7-12**

Status: informal/game-theory tier only. Owner receipt says axes 7-12 are “like a big game theory map” where each IGT agent has “a full engine” with all strategies, weighted but not deleted; structure registered as many-agent interaction readouts mirroring 1-6, gated behind shell-local -> pairwise -> coexistence (`system_v6/receipts/owner_doctrine_axes_7_12_and_engine_capability_20260612.md:3-13`). Not active axis math; no 7-12 packet may jump the coupling ladder (`...:25-32`).

**Type-1 vs Type-2**

The docs do **not** reduce Type-1/Type-2 to a single axis or flux alone.

What they explicitly say: Type 1 = “left, flux IN, H=+H0”; Type 2 = “right, flux OUT, H=-H0” (`IGT:482-500`, `515-525`). Atlas says Type1/Type2 is modeled by `H -> -H`, but “other flux-split mechanisms remain open” (`Atlas:103-129`). Atlas also says terrain family is shared, outer/inner is loop realization, and Type1/Type2 is orientation/chirality realization (`Atlas:74-79`).

What determines the type in the current chart: a combined chart vector: sheet/chirality/H sign + IN/OUT orientation + placement of Axis3 loop class with Axis4 order class. Type1 outer=deductive and inner=inductive; Type2 outer=inductive and inner=deductive (`IGT:517-525`; `Atlas:135-142`, `217-249`; `Scaffold:161`, `179`). But `A3 x A4` alone is underdetermined: the same `(A3,A4)` pairs occur in both types, so engine type needs chart loop role, path/order pairing, sheet sign, and token row; flux may later compress part of the distinction but is not admitted as replacement (`Deep:1401-1429`; `Layout:560-594`). Atlas hard non-claims also warn: `type != flow != chirality != precedence` and `Ax3 is not closed` (`Atlas:331-344`).

So the faithful answer is: Type1/Type2 = current engine-orientation/chart realization, not one axis. Flux IN/OUT is one named layer, H sign/chirality is another, and Axis3 x Axis4 placement participates but does not by itself determine type.


tokens used
301,717
**Source Key**

`IGT` = `system_v7/constraint_core/reference_docs/engine_math/igt-pattern-explicit-math-reference.md`  
`Scaffold` = `system_v7/constraint_core/reference_docs_from_josh/physics_program/working_math_scaffold_20260609.md`  
`A012` = `system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md`  
`Apple` = `system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md`  
`Atlas` = `system_v7/constraint_core/reference_docs/engine_math/ENGINE_64_SCHEDULE_ATLAS.md`  
`Deep` = `system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md`  
`Layout` = `system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md`  
`Signed` = `system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md`  
`Wiki` = `/Users/joshuaeisenhart/wiki/concepts/igt-axes-terrain-source-extraction-2026-06-04.md`

**Global Lock**

Axes are not primitive terrain/geometry objects. They are “readout maps `A_i : M(C) -> V_i`” and “never primitive coordinates” (`Scaffold:109`; `A012:44-47`; `Deep:24-32`). Terrains and flux are “geometry on the manifold, not axes”; flux is a candidate current family and “never as axis content” (`Scaffold:278-287`, `309-311`). So: axis definitions may read geometry, but must not absorb flux/holonomy/nesting as the axis itself.

**Axis 0**

Name/readout: “The drive”; splits `{Ne, Ni}` vs `{Se, Si}` and reads white/N/allostatic vs black/S/homeostatic terrain polarity (`IGT:188-206`; `Scaffold:264-274`; `A012:149-166`).  
Math: chart readout `b0 = sign(cos(2η)) = sign(r_z)`; bridge target `Phi_0(rho_AB) = -sum w_r S(A_r|B_r) = sum w_r I_c(A_r>B_r)` after `Xi : geometry/history -> rho_AB` (`IGT:196-217`; `A012:99-110`, `139-147`; `Deep:217-249`).  
Status/sims: source-backed candidate, not final; bridge/cut open (`A012:3-5`, `334-356`; `IGT:215-217`, `656-658`). Docs list `sim_L0_s3_valid`, `engine_core`, `axis0_gradient`, `axis0_path_integral`, `sim_GA0_entropic_gradient`, `axis0_xi_strict_bakeoff` as partial/candidate evidence (`A012:172-180`, `198-213`). Current/probe surfaces include `axis0_entropy_monotone`, `carnot_szilard_qit_engine`, and Type1 entropy-gradient probes, all candidate/scratch/non-promotion (`Wiki:378-389`; `system_v7/sims/type1_engine_v0/results/entropy_gradient_axis_probe_julia_results.json:5-6`, `120-133`).  
Competing readings: local `b0`; entropy of averaged local state; cut coherent-information functional; `Xi_ref`, `Xi_shell`, `Xi_hist` (`Scaffold:111`, `145`; `A012:133-137`, `217-223`).  
Geometry-contamination check: using `η`, nested Hopf tori, or ring/checkerboard as a readout seat is allowed; claiming the geometry-to-cut bridge is solved, or making flux/transport itself Axis 0, is contamination (`A012:196-206`; `Deep:251-263`; `Scaffold:278-287`, `309-311`).

**Axis 1**

Name/readout: “Branch split (derived)”; `{Se, Ni}` vs `{Ne, Si}` (`IGT:225-239`; `Deep:303-318`; `Layout:197-212`).  
Math: source-locked semantic split is unitary `Phi(rho)=U rho U†` vs proper CPTP `Phi(rho)=sum K rho K†`; Markovian GKLS is only a subclass (`A012:227-244`; `Apple:727-761`).  
Status/sims: Axis 1 semantic split and reduced Axis1 x Axis2 terrain join are source-locked; Axis 1 alone does not identify terrain (`A012:347-356`; `Deep:331-352`, `443-489`). Existing carrier probes can test product regimes but a source-lock exact product sim is still cleaner (`Wiki:390`). Type1 entropy-gradient probe touched `axis1_eps_terrain`, but its label-erased control did not win (`system_v7/sims/type1_engine_v0/results/entropy_gradient_axis_probe_numpy_results.json:43-59`).  
Competing readings: isothermal/adiabatic, bath-gating, black/white dot-teardrop layer are overlays, not kernel (`IGT:241-244`; `A012:264-273`; `Scaffold:112`).  
Geometry-contamination check: the CPTP/unitary branch is not geometry-contaminated. The drift risk is treating “expansion/compression,” hemisphere, or terrain labels as Axis 1 itself instead of a product/overlay (`A012:264-273`; `Deep:361-369`).

**Axis 2**

Name/readout: “Representation frame”; direct `{Se, Ne}` vs conjugated `{Ni, Si}` (`IGT:246-266`; `Layout:214-243`).  
Math: direct `rho_tilde=rho`, `dot(rho)=L(rho)` vs conjugated `rho_tilde=V_s† rho V_s` with `K=iV†Vdot` and transport correction (`IGT:254-264`; `A012:248-273`; `Deep:491-603`; `Apple:763-791`).  
Status/sims: source-locked / strong lower-stack anchor (`IGT:266`; `A012:351-353`). `ring_checkerboard_euler_conversion_axis2_frame_v0` supports Axis-2 `K_t` direct/static/dynamic discriminator at scratch ceiling, not admission (`.../ring_checkerboard_euler_conversion_axis2_frame_v0_exact_results.json:20-37`, `62-69`). `ring_checkerboard_axis2_kt_holonomy_v0` measures curvature-coupled holonomy, still scratch/no admission (`.../ring_checkerboard_axis2_kt_holonomy_v0_exact_results.json:20-48`, `140`).  
Competing readings: direct/conjugated is kernel; Eulerian/Lagrangian and dots/teardrops are overlays; expansion/compression is weak metaphor (`A012:264-273`; `Scaffold:113`, `145`).  
Geometry-contamination check: `K_t` is the frame readout; holonomy/curvature/flux/nesting are geometry on `M(C,t)`. If Axis 2 becomes “holonomy” or “flux,” contaminated (`Scaffold:278-287`, `309-311`; `...axis2_kt_holonomy...json:46-48`).

**Axis 3**

Name/readout: “Loop class”; strongest read is fiber/inner vs lifted-base/outer, but inner/outer is chart-relative (`IGT:273-291`; `Deep:605-713`; `Layout:245-275`).  
Math: fiber `gamma_f(u)=psi(phi0+u,chi0;eta0)`, density stationary; lifted-base `gamma_b(u)=psi(phi0-cos(2eta0)u,chi0+u;eta0)`, density traversing, horizontal `A(dot gamma_b)=0` (`IGT:279-289`; `A012:65-73`; `Deep:625-690`).  
Status/sims: strongest current reading, not closed against alternatives (`IGT:291`; `Atlas:293-303`; `Wiki:420-447`). `wb_axis3_terrains_julia` is a candidate finite-map probe with promotion blocked; it reports an observed gap but not admitted direction closure (`system_v5/julia_carrier/wb_axis3_terrains_julia_results.json:18-34`, `124-132`, `287-292`).  
Competing readings: L/R chirality, Type1/Type2 topology inversion, flux in/out remain live (`IGT:291`; `Scaffold:114`, `145`; `Wiki:406`, `420-428`). Proposed discriminator: build 16-row token table, attach density-motion observable, score inner/outer vs chirality vs Type partitions, with shuffle/chirality/path/degenerate-eta controls (`Wiki:430-443`).  
Geometry-contamination check: Axis 3 may read loop class, but it does not “own flux”; flux orientation is read from geometry, and flattening fiber/base is a flux control, not an Axis-3 identity (`Scaffold:278-287`; `Deep:611-617`, `1580-1605`).

**Axis 4**

Name/readout: loop order, “inductive vs deductive” (`IGT:300-334`; `Apple:886-934`; `Layout:277-303`).  
Math: `Phi_D = U o E o U o E` or generator form `e^(tau_R L_R)e^(tau_C L_C)` vs reversed `Phi_I`; first nontrivial difference approximates `tau_R tau_C [L_R,L_C]`; witness `||Phi_D(rho)-Phi_I(rho)||_1` (`IGT:306-318`; `Apple:888-919`; `Deep:790-902`).  
Status/sims: strong runtime/order anchor; taijitu spin direction open (`IGT:326-334`; `Atlas:300-302`; `Wiki:527-570`). `ax4_julia_results` says finite order split with commuting controls near zero and `promotion_allowed=false` (`system_v5/julia_carrier/ax4_julia_results.json:58-72`, `392-405`).  
Competing readings: runtime order `UEUE/EUEU` or `Phi_D/Phi_I`; FeTi/TeFi loop-family label; older `TiFe/FeTi`; clockwise/counterclockwise overlay (`Atlas:166-179`; `Signed:663-690`; `Wiki:533-550`). Discriminator: predeclared symbol-direction coding must predict runtime order and collapse under commuting/wrong-structure controls (`Wiki:552-566`).  
Geometry-contamination check: noncommuting composition order is clean. Contamination happens if visual spin direction or terrain graph path is promoted without the commutator/order witness (`IGT:318`, `334`; `Wiki:548-550`, `570`).

**Axis 5**

Name/readout: operator/generator family (`IGT:336-358`; `Deep:903-1114`).  
Math: `{Ti,Te}` dephasing/projection vs `{Fi,Fe}` rotation/unitary. Ti/Te are pinching/GKSL semigroups; Fi/Fe are Hamiltonian/unitary groups; witnesses are entropy/purity/contractivity vs orbit/spectrum preservation (`IGT:344-356`; `Apple:935-990`, `1072-1078`; `Signed:37-53`, `640-656`, `772-825`).  
Status/sims: strong operator split; S-curve/lobe overlay open (`IGT:358-366`; `Wiki:449-483`). `wb_axis5_spectral_gradient_julia` is a tool-lego fit probe, all-pass but candidate/non-promotion (`system_v5/julia_carrier/wb_axis5_spectral_gradient_julia_results.json:29-49`, `8940-8949`).  
Competing readings: dephasing/rotation, gradient/spectral, S-curve/lobe, `FeFi` vs `TiTe`/`TeTi`, unequal win/loss overlays (`Scaffold:116`, `145`; `Signed:683-690`; `Wiki:455-463`, `483`).  
Geometry-contamination check: clean if kept as operator-family selection. Contaminated if S-curve/lobe, visual weighting, or terrain attraction geometry replaces the channel/generator invariant (`Wiki:461-470`, `476-483`).

**Axis 6**

Name/readout: composition order / sidedness / precedence (`IGT:368-392`; `Deep:1115-1350`; `Signed:897-953`).  
Math: token precedence `up=operator written first`, `down=terrain written first`; channel order `Phi_T o O` vs `O o Phi_T`; primitive action-side `L_A(rho)=A rho` vs `R_A(rho)=rho A`; gap `||A rho - rho A||_F`; rows must record token precedence, action side, and closure type (`IGT:376-392`; `Deep:1119-1139`, `1161-1240`, `1242-1320`; `Signed:917-943`, `955-995`).  
Status/sims: strong math/symbol alignment, but action-side and token-order are related, not automatically identical (`IGT:388-392`; `Signed:932-943`). `ax6_julia_results` has bounded finite-map/order-sensitive receipt with promotion blocked (`system_v5/julia_carrier/ax6_julia_results.json:22-26`, `52`, `198-201`).  
Competing readings: up/down token, left/right action, judging-first/perceiving-first, outward/inward functional direction; outward/inward is open (`Signed:932-939`, `1017-1034`; `Deep:1282-1297`). `b6=-b0*b3`, but `b3` is chart-role inner/outer, not raw fiber/base (`Deep:1135-1159`; `Scaffold:117`).  
Geometry-contamination check: high risk. Because `b6` depends on `b0` and chart-role `b3`, using raw fiber/base, flux, or geometry path as the precedence bit contaminates the definition (`Deep:1148-1155`, `1282-1297`).

**Axes 7-12**

Status: informal/game-theory tier only. Owner receipt says axes 7-12 are “like a big game theory map” where each IGT agent has “a full engine” with all strategies, weighted but not deleted; structure registered as many-agent interaction readouts mirroring 1-6, gated behind shell-local -> pairwise -> coexistence (`system_v6/receipts/owner_doctrine_axes_7_12_and_engine_capability_20260612.md:3-13`). Not active axis math; no 7-12 packet may jump the coupling ladder (`...:25-32`).

**Type-1 vs Type-2**

The docs do **not** reduce Type-1/Type-2 to a single axis or flux alone.

What they explicitly say: Type 1 = “left, flux IN, H=+H0”; Type 2 = “right, flux OUT, H=-H0” (`IGT:482-500`, `515-525`). Atlas says Type1/Type2 is modeled by `H -> -H`, but “other flux-split mechanisms remain open” (`Atlas:103-129`). Atlas also says terrain family is shared, outer/inner is loop realization, and Type1/Type2 is orientation/chirality realization (`Atlas:74-79`).

What determines the type in the current chart: a combined chart vector: sheet/chirality/H sign + IN/OUT orientation + placement of Axis3 loop class with Axis4 order class. Type1 outer=deductive and inner=inductive; Type2 outer=inductive and inner=deductive (`IGT:517-525`; `Atlas:135-142`, `217-249`; `Scaffold:161`, `179`). But `A3 x A4` alone is underdetermined: the same `(A3,A4)` pairs occur in both types, so engine type needs chart loop role, path/order pairing, sheet sign, and token row; flux may later compress part of the distinction but is not admitted as replacement (`Deep:1401-1429`; `Layout:560-594`). Atlas hard non-claims also warn: `type != flow != chirality != precedence` and `Ax3 is not closed` (`Atlas:331-344`).

So the faithful answer is: Type1/Type2 = current engine-orientation/chart realization, not one axis. Flux IN/OUT is one named layer, H sign/chirality is another, and Axis3 x Axis4 placement participates but does not by itself determine type.


