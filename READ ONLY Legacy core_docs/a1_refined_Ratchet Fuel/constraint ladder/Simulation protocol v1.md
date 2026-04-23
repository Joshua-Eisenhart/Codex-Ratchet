# Simulation protocol v1  
  
**ID: S1_01**  
**STATEMENT: It is forbidden for protocol execution status to modify, weaken, override, or constrain kernel admissibility or kernel-derived artifacts.**  
**FORBIDS: protocol-gated admissibility, protocol-defined kernel exceptions, protocol-defined kernel rejection**  
**PERMITS: protocol outputs that are removable, kernel artifacts that remain admissible independent of protocol outcomes**  
**OPEN: minimal audit criteria for demonstrating non-gating behavior**  
  
**ID: S1_02**  
**STATEMENT: It is forbidden to mix kernel artifacts, optional overlay artifacts, and protocol artifacts into an indistinguishable output stream; artifact classes must remain explicitly separable.**  
**FORBIDS: mixed artifact channels, implicit artifact typing, kernel/overlay/protocol conflation**  
**PERMITS: explicit artifact class tags, separable bundles for kernel, overlays, and protocol logs**  
**OPEN: minimal artifact typing schema**  
  
**ID: S1_03**  
**STATEMENT: It is forbidden to execute a run without an explicit run manifest that declares the exact frozen kernel set and the optional overlay set (if any) as inputs.**  
**FORBIDS: implicit versioning, undeclared kernel set, assumed overlay presence**  
**PERMITS: explicit run manifests, overlay-free runs, explicitly declared overlay lenses**  
**OPEN: minimal run manifest schema**  
  
**ID: S2_01**  
**STATEMENT: It is forbidden for a run to depend on undeclared external sources for inputs; all inputs must be explicit finite encodings included in the run manifest.**  
**FORBIDS: implicit external retrieval, undeclared input dependencies, implicit context injection**  
**PERMITS: explicit input payloads, explicit input identifiers, explicit input manifests**  
**OPEN: admissible input identifier schemas**  
  
**ID: S2_02**  
**STATEMENT: It is forbidden to require any overlay for running or replaying kernel artifacts; overlays are optional and must be removable without affecting kernel replay.**  
**FORBIDS: overlay-required replay, overlay-required well-formedness, overlay-required validity claims**  
**PERMITS: overlay-free execution, optional overlay attachment as non-binding annotation**  
**OPEN: minimal overlay attachment schema**  
  
**ID: S2_03**  
**STATEMENT: It is forbidden to mutate input payloads in place; any transformation of inputs must produce explicitly new derived payloads with explicit lineage declarations.**  
**FORBIDS: in-place input mutation, silent input rewriting, implicit lineage**  
**PERMITS: derived payload creation, explicit lineage tags, explicit parent-child payload relations**  
**OPEN: minimal lineage declaration schema**  
  
**ID: S3_01**  
**STATEMENT: It is forbidden to execute an unbounded or implicit step schedule; every run must declare an explicit finite step list.**  
**FORBIDS: unbounded loops, implicit iteration, implicit step generation**  
**PERMITS: explicit finite step lists, explicit step indexing, explicit step typing**  
**OPEN: minimal step list schema**  
  
**ID: S3_02**  
**STATEMENT: It is forbidden for execution outcomes to depend on undeclared nondeterministic degrees of freedom; any nondeterminism must be explicitly declared as an optional protocol feature.**  
**FORBIDS: unlogged nondeterminism, implicit variability, hidden run-to-run variation sources**  
**PERMITS: deterministic replay from manifest + payloads + step list, explicitly declared nondeterminism flags**  
**OPEN: admissible nondeterminism declaration schema**  
  
**ID: S3_03**  
**STATEMENT: It is forbidden for execution to depend on undeclared environment state; all environment dependencies must be explicitly declared in the run manifest.**  
**FORBIDS: hidden environment dependencies, implicit state carryover, implicit configuration**  
**PERMITS: explicit environment manifests, explicit configuration payloads, environment-independent replay where possible**  
**OPEN: minimal environment manifest schema**  
  
**ID: S4_01**  
**STATEMENT: It is forbidden to omit a complete execution tape; each executed step must produce a tape entry binding step index, input identifiers, output identifiers, and status.**  
**FORBIDS: missing tape entries, partial tapes without explicit truncation markers, unbound outputs**  
**PERMITS: complete execution tapes, explicit truncation markers, explicit step-status tags**  
**OPEN: minimal tape entry schema**  
  
**ID: S4_02**  
**STATEMENT: It is forbidden to require temporal metadata for replay; replay must depend only on the ordered tape index and declared payloads.**  
**FORBIDS: replay requiring temporal metadata, ordering derived from external clocks, clock-dependent reconstruction**  
**PERMITS: replay by tape order, tape-local ordering tokens**  
**OPEN: optional temporal fields as ignorable annotations**  
  
**ID: S4_03**  
**STATEMENT: It is forbidden for replay to require hidden intermediate state; all intermediate artifacts required for replay must be explicitly present or explicitly declared as absent.**  
**FORBIDS: hidden intermediates, implicit recomputation assumptions, silent omission of required artifacts**  
**PERMITS: replay-complete artifact sets, explicit “missing artifact” declarations**  
**OPEN: minimal “missing artifact” declaration schema**  
  
**ID: S5_01**  
**STATEMENT: It is forbidden to perform silent auto-repair on failures; any repair attempt must be explicitly logged as a separate step with explicit inputs and outputs.**  
**FORBIDS: silent recovery, implicit patching, unlogged auto-repair**  
**PERMITS: explicit repair steps, explicit repair logs, explicit repair provenance**  
**OPEN: admissible repair step schemas**  
  
**ID: S5_02**  
**STATEMENT: It is forbidden to present partial runs as complete; truncation or failure must be explicitly recorded and propagated to all derived protocol summaries.**  
**FORBIDS: silent truncation, completeness-by-fiat, missing failure propagation**  
**PERMITS: explicit failure states, explicit partial-run markers, explicit derivation of summaries from tape**  
**OPEN: minimal failure state taxonomy**  
  
**ID: S5_03**  
**STATEMENT: It is forbidden to assume a default halt-or-continue policy; the run policy must be explicitly declared and recorded in the run manifest.**  
**FORBIDS: implicit halting policy, implicit continuation policy, policy inferred from context**  
**PERMITS: explicit run policies, per-step policy overrides explicitly logged**  
**OPEN: minimal run policy schema**  
  
**ID: S6_01**  
**STATEMENT: It is forbidden for diagnostics to gate acceptance, rejection, or admissibility of kernel artifacts; diagnostics are non-binding and removable.**  
**FORBIDS: diagnostic-gated admissibility, diagnostic-based rejection, diagnostic-defined kernel exceptions**  
**PERMITS: diagnostics as annotations, diagnostics stored outside kernel artifacts**  
**OPEN: minimal audit criteria for diagnostic non-binding status**  
  
**ID: S6_02**  
**STATEMENT: It is forbidden for diagnostics to assert correctness status; diagnostics may report only declared structural properties of artifacts and tape completeness properties.**  
**FORBIDS: correctness assertions, truth assertions, evaluative verdicts**  
**PERMITS: structural diagnostics, completeness diagnostics, declared-property reports**  
**OPEN: admissible diagnostic property schemas**  
  
**ID: S6_03**  
**STATEMENT: It is forbidden to attach diagnostic outputs as if they were kernel-derived structure; diagnostic artifacts must remain explicitly typed as protocol artifacts.**  
**FORBIDS: diagnostic-to-kernel promotion, diagnostic artifact conflation, implicit semantic elevation**  
**PERMITS: protocol-typed diagnostic artifacts, separable diagnostic bundles**  
**OPEN: minimal diagnostic artifact typing schema**  
  
**ID: S7_01**  
**STATEMENT: It is forbidden to use hidden caches; any reuse of prior artifacts must be explicit via identifiers recorded in the run manifest and tape.**  
**FORBIDS: hidden caching, implicit reuse, unlogged memoization**  
**PERMITS: explicit reuse by identifier, explicit cache manifests as protocol artifacts**  
**OPEN: minimal cache manifest schema**  
  
**ID: S7_02**  
**STATEMENT: It is forbidden to carry protocol state across runs without explicit import declarations; cross-run reuse must be declared as explicit inputs.**  
**FORBIDS: implicit state carryover, hidden session state, undeclared cross-run dependencies**  
**PERMITS: explicit import of prior artifacts, explicit dependency manifests**  
**OPEN: minimal cross-run import schema**  
  
**ID: S7_03**  
**STATEMENT: It is forbidden to compress, summarize, or elide tape information without an explicit loss declaration; any lossy transformation must be explicitly marked as lossy and non-replayable.**  
**FORBIDS: silent elision, silent summarization loss, replay claims over lossy artifacts**  
**PERMITS: explicit loss markers, separable lossy summaries as protocol artifacts**  
**OPEN: minimal loss declaration schema**  
  
**ID: S8_01**  
**STATEMENT: It is forbidden to export a run without a portable bundle sufficient for replay under the declared dependencies; the bundle must include manifest, inputs, tape, and required intermediates or explicit absence declarations.**  
**FORBIDS: incomplete exports, non-replayable exports presented as replayable, missing manifest/tape/payloads**  
**PERMITS: replayable bundles, explicit absence declarations, separable artifact classes**  
**OPEN: minimal portable bundle schema**  
  
**ID: S8_02**  
**STATEMENT: It is forbidden for overlay removal to change kernel artifact content; stripping overlays must delete only overlay artifacts and overlay mappings.**  
**FORBIDS: kernel mutation on overlay stripping, kernel dependence on overlay presence, overlay-driven kernel rewriting**  
**PERMITS: overlay stripping as a reversible protocol operation, kernel artifacts unchanged under stripping**  
**OPEN: minimal overlay stripping declaration schema**  
  
**ID: S8_03**  
**STATEMENT: It is forbidden for protocol summaries to become authoritative sources over the tape; any summary must be explicitly derived from tape entries and marked as non-binding.**  
**FORBIDS: summary-as-authority, summary overriding tape, ungrounded summaries**  
**PERMITS: tape-derived summaries, explicit derivation tags, non-binding protocol summaries**  
**OPEN: minimal summary derivation schema**  
