# Game theory rosetta v1  
  
**ID: GZ1_01**  
**STATEMENT: It is forbidden for any game-theory interpretation to modify, weaken, override, or constrain any kernel rule or kernel admissibility condition.**  
**FORBIDS: kernel modification via game overlay, game-overlay-gated admissibility, game-overlay-gated rejection, game-defined kernel exceptions**  
**PERMITS: removable game-theory annotations, optional game labels with no kernel force**  
**OPEN: minimal audit criteria for non-binding game overlays**  
  
**ID: GZ1_02**  
**STATEMENT: It is forbidden to treat any game-theory interpretation as true, correct, optimal, or preferred by default.**  
**FORBIDS: truth-by-game-overlay, correctness-by-game-overlay, optimality-by-overlay, preferred-interpretation-by-default**  
**PERMITS: multiple optional game lenses with no default correctness status**  
**OPEN: admissible non-binding confidence annotations for interpretations (if any)**  
  
**ID: GZ1_03**  
**STATEMENT: It is forbidden to treat game-theory terminology as granting semantic force to kernel tokens beyond what is explicitly declared within game overlay declarations.**  
**FORBIDS: implicit semantics from game labels, meaning inflation by naming, semantic completion by overlay**  
**PERMITS: explicit non-binding game-meaning declarations scoped to overlay tokens**  
**OPEN: minimal schema for explicit non-binding interpretation declarations**  
  
**ID: GZ2_01**  
**STATEMENT: It is forbidden to conflate game-overlay namespaces with kernel namespaces; game-overlay tokens must not be treated as kernel tokens.**  
**FORBIDS: namespace conflation, game-token substitution for kernel tokens, implicit kernel re-tokenization via game terms**  
**PERMITS: explicit game overlay namespaces, explicit mapping tables from kernel tokens to game tokens**  
**OPEN: minimal namespace declaration schema**  
  
**ID: GZ2_02**  
**STATEMENT: It is forbidden to assert any game-overlay mapping without an explicit mapping declaration specifying source token(s), target game token(s), and scope.**  
**FORBIDS: implicit mappings, scope-free mapping assertions, unstated targets, context-inferred mappings**  
**PERMITS: explicit mapping declarations with explicit scope**  
**OPEN: minimal mapping declaration schema**  
  
**ID: GZ2_03**  
**STATEMENT: It is forbidden to assume game-overlay mappings are injective, surjective, invertible, or canonical by default.**  
**FORBIDS: one-to-one assumptions, onto assumptions, invertibility-by-fiat, canonical mapping by default**  
**PERMITS: partial mappings, one-to-many mappings, many-to-one mappings, multiple coexisting mappings**  
**OPEN: admissible premises for partial inverses (if any)**  
  
**ID: GZ3_01**  
**STATEMENT: It is forbidden to interpret kernel objects as players, agents, or coalitions by default; any such interpretation must be explicitly declared and remains non-binding.**  
**FORBIDS: player-by-default, agent-by-default, coalition-by-default, implicit agency assumptions**  
**PERMITS: explicit optional player/agent/coalition overlays scoped to kernel artifacts**  
**OPEN: admissible schemas for optional agency overlays without importing rationality axioms**  
  
**ID: GZ3_02**  
**STATEMENT: It is forbidden to interpret kernel paths as strategies, moves, or policies by default; any such strategy interpretation must be explicitly declared and scoped.**  
**FORBIDS: strategy-by-default, move-by-default, policy-by-default, implicit action semantics**  
**PERMITS: explicit optional strategy/move overlays over kernel path encodings**  
**OPEN: admissible schemas for strategy overlays without time or optimization semantics**  
  
**ID: GZ3_03**  
**STATEMENT: It is forbidden to interpret kernel compatibility, adjacency, or neighborhoods as information availability, observation structure, or communication structure by default.**  
**FORBIDS: information-availability-by-default, observation structure by default, communication semantics by default**  
**PERMITS: explicit optional information-structure overlays as non-binding annotations**  
**OPEN: admissible schemas for information-structure overlays without probability or time semantics**  
  
**ID: GZ4_01**  
**STATEMENT: It is forbidden to interpret any kernel scalar functional as payoff, utility, value, or reward by default.**  
**FORBIDS: payoff-by-default, utility-by-default, reward-by-default, value-by-default**  
**PERMITS: explicit optional payoff/utility labeling overlays that remain non-binding**  
**OPEN: admissible schemas for payoff-label overlays that do not introduce maximization**  
  
**ID: GZ4_02**  
**STATEMENT: It is forbidden to use payoff/utility overlays to select, rank, or privilege kernel artifacts by default.**  
**FORBIDS: selection-by-payoff-label, ranking-by-utility-label, canonicalization by overlay values**  
**PERMITS: descriptive payoff labels without preference force**  
**OPEN: later admission conditions for selection mechanisms (if any)**  
  
**ID: GZ4_03**  
**STATEMENT: It is forbidden to assume additivity, comparability, or normalization of payoff overlays by default.**  
**FORBIDS: additive payoffs by default, comparable payoffs by default, normalized payoffs by default**  
**PERMITS: explicit scoped payoff law overlays treated as non-binding**  
**OPEN: admissible schemas for payoff law overlays without binding force**  
  
**ID: GZ5_01**  
**STATEMENT: It is forbidden to interpret kernel transport as belief update, strategy update, learning, or adaptation by default.**  
**FORBIDS: belief-update semantics, learning semantics, adaptation semantics, update-as-dynamics**  
**PERMITS: explicit optional update-lens overlays as non-binding annotations**  
**OPEN: admissible schemas for update-lens overlays without time or probability semantics**  
  
**ID: GZ5_02**  
**STATEMENT: It is forbidden to interpret kernel transport invariants as rationality constraints, common knowledge, or equilibrium conditions by default.**  
**FORBIDS: rationality-by-default, common knowledge by default, equilibrium condition by default**  
**PERMITS: explicit optional rationality/equilibrium-lens overlays treated as non-binding hypotheses**  
**OPEN: admissible schemas for rationality/equilibrium lenses without optimization**  
  
**ID: GZ5_03**  
**STATEMENT: It is forbidden to interpret transport composition laws as strategic composition laws by default.**  
**FORBIDS: strategic composition by default, law smuggling via transport composition, forced game algebra**  
**PERMITS: explicit optional strategic-composition overlays treated as non-binding**  
**OPEN: admissible schemas for strategic composition overlays**  
  
**ID: GZ6_01**  
**STATEMENT: It is forbidden to interpret curvature/obstruction as externalities, strategic friction, institutional constraint, or incentive misalignment by default.**  
**FORBIDS: externality semantics by default, friction semantics by default, institutional constraint semantics by default, incentive misalignment by default**  
**PERMITS: explicit optional obstruction-as-friction overlays treated as non-binding hypotheses**  
**OPEN: admissible schemas for obstruction-as-friction overlays without evaluation or optimization**  
  
**ID: GZ6_02**  
**STATEMENT: It is forbidden to interpret closed-path transport effects as repeated games, iterated play, or temporal cycles by default.**  
**FORBIDS: repeated-game semantics, iterated-play semantics, temporal cycle semantics**  
**PERMITS: optional loop-effect-as-consistency overlays without time meaning**  
**OPEN: admissible schemas for repeated-game lenses treated as non-binding hypotheses**  
  
**ID: GZ6_03**  
**STATEMENT: It is forbidden to scalarize obstruction/curvature into cost, regret, or penalty by default.**  
**FORBIDS: cost-by-default, regret-by-default, penalty-by-default, canonical scalarization**  
**PERMITS: explicit optional scalarization overlays with declared scope and non-binding status**  
**OPEN: admissible scalarization schemas without optimization or selection force**  
  
**ID: GZ7_01**  
**STATEMENT: It is forbidden to interpret engine-like objects as equilibrium concepts, solution concepts, or optimal mechanisms by default.**  
**FORBIDS: equilibrium-by-default, Nash-like semantics by default, solution-concept identification by default, optimal mechanism claims**  
**PERMITS: optional engine-as-stable-pattern overlays treated as non-binding annotations**  
**OPEN: admissible schemas for solution-concept overlays treated as hypotheses only**  
  
**ID: GZ7_02**  
**STATEMENT: It is forbidden to infer equilibrium existence, uniqueness, or optimality from any kernel structure or any overlay mapping.**  
**FORBIDS: equilibrium existence inference, uniqueness inference, optimality inference, rationality axiom injection**  
**PERMITS: explicit equilibrium-hypothesis tagging without kernel impact**  
**OPEN: admissible schemas for equilibrium hypothesis declarations**  
  
**ID: GZ7_03**  
**STATEMENT: It is forbidden to require rationality axioms, preference completeness, or transitivity as prerequisites for game overlays.**  
**FORBIDS: rationality prerequisites, completeness assumptions, transitivity assumptions, utility axioms by default**  
**PERMITS: overlays that omit rationality axioms, multiple incompatible rationality lenses**  
**OPEN: admissible schemas for optional rationality-lens overlays**  
  
**ID: GZ8_01**  
**STATEMENT: It is forbidden to modify a game overlay mapping set without an explicit game-overlay version identifier and an explicit changelog declaration.**  
**FORBIDS: silent overlay edits, silent remapping, unversioned game overlay mutation**  
**PERMITS: versioned game overlays, explicit changelog declarations**  
**OPEN: minimal version identifier and changelog schema**  
  
**ID: GZ8_02**  
**STATEMENT: It is forbidden to treat any game overlay as predictive, prescriptive, or validated by default.**  
**FORBIDS: prediction claims, prescription claims, validation-by-assertion, correctness claims**  
**PERMITS: game overlays as hypotheses-only annotations, explicit non-binding “hypothesis” tagging**  
**OPEN: admissible schemas for linking overlays to external evidence without kernel impact**  
  
**ID: GZ8_03**  
**STATEMENT: It is forbidden to treat removal of the game overlay as deleting or mutating any kernel artifact; game overlay removal may delete only game overlay tokens and mappings.**  
**FORBIDS: kernel deletion via overlay removal, kernel mutation via overlay stripping, kernel dependence on game overlay**  
**PERMITS: reversible overlay stripping, kernel artifacts unchanged under stripping**  
**OPEN: minimal overlay stripping declaration schema**  
