# Rosetta contract v1  
  
**ID: RZ1_01**  
**STATEMENT: It is forbidden for any interpretive overlay declaration to modify, weaken, override, or constrain any kernel rule or kernel admissibility condition.**  
**FORBIDS: kernel modification via overlays, overlay-gated admissibility, overlay-gated rejection, overlay-defined kernel exceptions**  
**PERMITS: overlays that are removable annotations only**  
**OPEN: minimal audit criteria for demonstrating non-binding status**  
  
**ID: RZ1_02**  
**STATEMENT: It is forbidden to treat any interpretive overlay as true, correct, or preferred by default; interpretive overlays carry no default correctness status.**  
**FORBIDS: truth-by-overlay, correctness-by-overlay, preferred interpretation by default, privileged overlay**  
**PERMITS: optional overlays with no default truth status**  
**OPEN: admissible forms of explicit overlay confidence declarations (if any)**  
  
**ID: RZ1_03**  
**STATEMENT: It is forbidden to treat interpretive names or labels as granting semantic force to kernel tokens beyond what is explicitly declared within the overlay itself.**  
**FORBIDS: implicit semantics from labels, meaning inflation by naming, semantic completion by overlay**  
**PERMITS: explicitly declared overlay meanings that remain non-binding to the kernel**  
**OPEN: admissible schemas for explicit overlay meaning declarations**  
  
**ID: RZ2_01**  
**STATEMENT: It is forbidden to conflate overlay namespaces with kernel namespaces; overlay tokens must not be treated as kernel tokens.**  
**FORBIDS: namespace conflation, overlay-as-kernel token substitution, implicit kernel re-tokenization**  
**PERMITS: explicit overlay namespaces, explicit mapping tables between overlay and kernel tokens**  
**OPEN: minimal namespace declaration schema**  
  
**ID: RZ2_02**  
**STATEMENT: It is forbidden to overload a single overlay token to mean multiple incompatible kernel targets without an explicit disambiguation mechanism.**  
**FORBIDS: ambiguous overlay tokens, uncontrolled polysemy, implicit disambiguation by context**  
**PERMITS: explicit disambiguation mechanisms, multiple distinct overlay tokens for distinct targets**  
**OPEN: admissible disambiguation mechanism schemas**  
  
**ID: RZ2_03**  
**STATEMENT: It is forbidden to introduce overlay symbols that are treated as primitive kernel operators; overlay operator-like glyphs remain overlay-only unless separately admitted by kernel layers.**  
**FORBIDS: overlay glyphs promoted to kernel operators, operator smuggling via notation**  
**PERMITS: overlay-only operator notation as non-binding labels**  
**OPEN: admissible criteria for distinguishing overlay glyphs from kernel operators**  
  
**ID: RZ3_01**  
**STATEMENT: It is forbidden to assert an overlay-to-kernel mapping without an explicit mapping declaration that specifies source token, target token(s), and scope.**  
**FORBIDS: implicit mappings, unstated target tokens, scope-free mapping assertions**  
**PERMITS: explicit mapping declarations with explicit scope**  
**OPEN: minimal mapping declaration schema**  
  
**ID: RZ3_02**  
**STATEMENT: It is forbidden to assume overlay mappings are injective, surjective, or invertible by default.**  
**FORBIDS: invertibility-by-fiat, one-to-one assumptions, onto assumptions**  
**PERMITS: partial mappings, many-to-one mappings, one-to-many mappings under explicit declaration**  
**OPEN: admissible conditions for invertibility or partial inverses (if any)**  
  
**ID: RZ3_03**  
**STATEMENT: It is forbidden to treat overlay mappings as preserving any kernel equivalence, refinement relation, compatibility relation, transport relation, or obstruction relation by default.**  
**FORBIDS: relation-preservation-by-overlay, invariance-by-overlay, equivalence smuggling via mapping**  
**PERMITS: overlay mappings that do not assert preservation unless explicitly declared**  
**OPEN: admissible forms of explicit preservation claims (if any)**  
  
**ID: RZ4_01**  
**STATEMENT: It is forbidden to assume a single canonical overlay exists; multiple incompatible overlays may coexist without requiring reconciliation.**  
**FORBIDS: canonical overlay by default, forced unification, reconciliation-by-fiat**  
**PERMITS: coexistence of multiple overlays, parallel interpretation layers**  
**OPEN: admissible coexistence constraints for managing multiple overlays (if any)**  
  
**ID: RZ4_02**  
**STATEMENT: It is forbidden to resolve conflicts between overlays by default rules that privilege one overlay; conflict resolution must be explicitly declared and remains non-binding to the kernel.**  
**FORBIDS: implicit overlay precedence, default tie-breakers, privileged overlay resolution**  
**PERMITS: explicitly declared conflict-handling rules within overlays**  
**OPEN: admissible conflict-handling schemas**  
  
**ID: RZ4_03**  
**STATEMENT: It is forbidden to merge two overlays into a single overlay without an explicit merge declaration that enumerates retained tokens, discarded tokens, and retained mappings.**  
**FORBIDS: implicit merging, silent token dropping, silent mapping alteration**  
**PERMITS: explicit merge declarations**  
**OPEN: minimal merge declaration schema**  
  
**ID: RZ5_01**  
**STATEMENT: It is forbidden to use overlay labels to assert identity, equality, or unrestricted substitutability of kernel objects or kernel paths.**  
**FORBIDS: identity-from-label, equality-from-label, substitution-by-label**  
**PERMITS: overlay-level grouping labels with no kernel sameness consequences**  
**OPEN: admissible overlay-only equivalence schemas (if any)**  
  
**ID: RZ5_02**  
**STATEMENT: It is forbidden to treat overlay-induced grouping as determining kernel cycle classes or kernel engine-like classes by default.**  
**FORBIDS: class-determination-by-overlay, kernel class collapse via overlay, canonical classification by overlay**  
**PERMITS: overlay annotations over kernel classes without determining them**  
**OPEN: admissible forms of overlay-to-kernel class correspondence claims (if any)**  
  
**ID: RZ5_03**  
**STATEMENT: It is forbidden to introduce overlay rules that add new admission gates for kernel cycles or kernel engine-like objects.**  
**FORBIDS: overlay-gated cycle admission, overlay-gated engine admission, overlay-defined kernel rejection criteria**  
**PERMITS: overlay annotations that do not affect kernel admission**  
**OPEN: admissible audit criteria for demonstrating no admission impact**  
  
**ID: RZ6_01**  
**STATEMENT: It is forbidden to modify an overlay mapping set without an explicit version identifier for the overlay and an explicit changelog declaration.**  
**FORBIDS: silent overlay edits, silent remapping, unversioned overlay mutation**  
**PERMITS: versioned overlays, explicit changelog declarations**  
**OPEN: minimal version identifier and changelog schema**  
  
**ID: RZ6_02**  
**STATEMENT: It is forbidden to treat overlay versions as retroactively changing the meaning of previously recorded kernel artifacts; overlay versions apply only as optional lenses.**  
**FORBIDS: retroactive reinterpretation as binding, rewriting historical kernel artifacts, forced reannotation**  
**PERMITS: multiple overlay versions applied as optional lenses**  
**OPEN: admissible schemas for non-binding historical annotation (if any)**  
  
**ID: RZ6_03**  
**STATEMENT: It is forbidden to infer overlay provenance or authorship by default; provenance must be explicitly declared if used.**  
**FORBIDS: implicit provenance, inferred authorship, default authority assignment**  
**PERMITS: explicit provenance declarations**  
**OPEN: admissible provenance declaration schema**  
  
**ID: RZ7_01**  
**STATEMENT: It is forbidden to require kernel changes as a prerequisite for adding or updating an overlay; overlays must remain addable without kernel modification.**  
**FORBIDS: kernel-change prerequisite for overlays, kernel-dependent overlay admission**  
**PERMITS: overlay updates independent of kernel changes**  
**OPEN: admissible coupling mechanisms placed as OPEN when kernel changes would be required**  
  
**ID: RZ7_02**  
**STATEMENT: It is forbidden to assume overlay migration is lossless by default; any migration claim must explicitly declare what is preserved and what may be discarded.**  
**FORBIDS: lossless migration-by-fiat, implicit preservation guarantees**  
**PERMITS: explicit migration declarations with explicit preservation/discard sets**  
**OPEN: minimal migration declaration schema**  
  
**ID: RZ7_03**  
**STATEMENT: It is forbidden to assume that an overlay update preserves compatibility across all prior overlay-dependent artifacts; preservation must be explicitly declared and scoped.**  
**FORBIDS: preservation-by-default across overlay updates, backward-compatibility-by-fiat**  
**PERMITS: explicitly declared backward-compatibility claims under scope**  
**OPEN: admissible backward-compatibility schemas**  
  
**ID: RZ8_01**  
**STATEMENT: It is forbidden for any kernel artifact to require any overlay for validity; removing all overlays must leave all kernel artifacts well-formed and admissible under kernel rules alone.**  
**FORBIDS: overlay-required kernel validity, overlay-required well-formedness, kernel dependence on rosetta annotations**  
**PERMITS: kernel artifacts that stand alone, overlays as removable annotations**  
**OPEN: minimal audit criteria for demonstrating removability**  
  
**ID: RZ8_02**  
**STATEMENT: It is forbidden to treat removal of overlays as deleting kernel content; overlay removal may delete only overlay tokens and overlay mappings.**  
**FORBIDS: kernel deletion via overlay removal, kernel mutation via stripping overlays**  
**PERMITS: overlay stripping that preserves kernel artifacts unchanged**  
**OPEN: admissible overlay stripping declaration schema**  
  
**ID: RZ8_03**  
**STATEMENT: It is forbidden to treat interpretive overlays as enforcing a single canonical narrative; overlays may be mutually incompatible and still remain admissible as non-binding annotations.**  
**FORBIDS: canonical narrative enforcement, narrative unification by fiat, forced story coherence**  
**PERMITS: multiple non-binding narratives as overlays**  
**OPEN: admissible schemas for declaring narrative overlays**  
