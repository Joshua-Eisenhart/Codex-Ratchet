# Skills Plan — Keep / Build / Patch / Retire

Status: working plan
Purpose: define how skills should be handled across the system so they become an operational layer instead of a pile of partially-related procedures

This document covers skills for:
- Hermes use
- bounded ingestion
- QIT/sim workflow
- proof/graph/tooling workflow
- cleanup/inventory workflow
- broader system-building support

---

## 1. Governing rule

A skill should exist only if it has a recurring operational job.

Do not keep or build skills that are:
- decorative
- stale
- narrative-only
- one-off and trivial
- disconnected from the real workflow

---

## 2. Skill status classes

Every skill should eventually be classified as one of:

- `keep`
  - useful now, aligned with real workflow, worth maintaining

- `build`
  - needed but not yet properly formalized as a skill

- `patch`
  - already useful, but incomplete, stale, misleading, or not aligned with current reality

- `retire`
  - no longer justified, stale, superseded, or misleading enough to remove from active use

- `reference_only`
  - useful pattern source, but not yet worth turning into a live skill

---

## 3. What skills are for in this system

Skills should serve recurring operational patterns such as:
- bounded Hermes ingestion
- repo/tooling audits
- QIT engine planning
- pre-Axis sim classification
- proof/graph tool wiring
- cleanup planning
- environment verification
- artifact verification
- later system-building procedures

Skills are procedural memory, not broad conceptual essays.

---

## 4. Immediate skill categories that matter now

## 4.1 Hermes workflow skills
Examples:
- bounded intake pack construction
- bounded audit execution
- Hermes stack classification
- Hermes repo/ecosystem review
- Hermes add-on planning

Status:
- high priority
- many likely need `build`

## 4.2 QIT / pre-Axis sim skills
Examples:
- classify a sim as admitted / keep open / diagnostic / broken
- map tool requirements by tier
- audit a pre-Axis tranche
- build or evaluate a lego sim contract

Status:
- high priority
- many likely need `build`

## 4.3 Proof/graph/tooling skills
Examples:
- audit current tool status
- verify graph/proof tool wiring
- classify installed vs missing vs not wired tools
- verify writeback honesty

Status:
- high priority
- some may already exist in partial form and need `patch`

## 4.4 Cleanup / inventory skills
Examples:
- machine-scope inventory pass
- environment/reference-repo classification
- cleanup deletion-gate verification

Status:
- medium-high priority
- many may need `build`

## 4.5 Broader v5/system-building skills
Examples:
- later architecture planning
- broader graph/system synthesis
- system-level doc queue generation

Status:
- important later
- should not outrun QIT proto and core tooling work

---

## 5. Immediate keep candidates

These are the kinds of skills that are likely worth keeping or strengthening now:

### 5.1 Bounded-ingestion skills
Why keep:
- Hermes must be fed slowly and explicitly
- this is already clearly a recurring workflow

### 5.2 Tool-audit skills
Why keep:
- current setup requires repeated verification of installed vs wired vs broken status

### 5.3 Repo audit / planning skills
Why keep:
- ongoing cleanup and planning needs repeated disciplined passes

### 5.4 Formal document generation skills
Why keep:
- there is now a real document stack and more planning docs will likely be needed

### 5.5 Pre-Axis sim audit skills
Why keep:
- the QIT engine proto needs repeated classification and tranche analysis

---

## 6. Immediate build candidates

These are the most obvious skill gaps to build next.

They should be tied to actual existing workflow surfaces where possible, especially:
- bounded planning docs already created in this repo
- current `system_v4/skills/` machinery
- current `system_v4/runners/` and `system_v4/probes/` workflows
- Hermes stack procedures

### 6.1 Bounded Hermes intake pack builder
Named job:
- produce bounded packs with purpose, role, frame, exclusions, and output requirements

Reason:
- this is central to using Hermes properly

### 6.2 Pre-Axis sim tranche auditor
Named job:
- audit a bounded tranche of pre-Axis sims under the correct frame

Reason:
- immediate QIT proto work needs this repeatedly

### 6.3 Lego sim classifier
Named job:
- classify a sim against the lego contract

Reason:
- needed to make “small sims as legos” operational

### 6.4 Tool-status auditor
Named job:
- classify tools as installed / not wired / broken / missing / later

Reason:
- this remains a recurring setup problem

### 6.5 Hermes stack auditor
Named job:
- classify Hermes repos, add-ons, and related surfaces

Reason:
- Hermes is a first-class stack in the architecture now

### 6.6 Cleanup deletion-gate checker
Named job:
- verify whether something is safe to remove yet

Reason:
- useful for slow cleanup without breaking the repo

### 6.7 Existing-skill audit and mapping pass
Named job:
- map actual existing skills in `system_v4/skills/` and Hermes skill surfaces into `keep / build / patch / retire / reference_only`

Reason:
- the current plan should not remain abstract; it needs to land on real existing skill files and current workflow surfaces

---

## 7. Immediate patch candidates

These are skill areas that likely already exist in some form but need tightening.

### 7.1 Old broad repo-inspection or planning skills
Patch reason:
- if they encourage reading too much at once, they are misaligned with the bounded-ingestion method

### 7.2 Graph/proof tooling skills
Patch reason:
- if they assume package presence is enough without wiring or artifact checks, they are too weak

### 7.3 Sim-related skills
Patch reason:
- if they do not enforce tier/tool/artifact/negative discipline, they are outdated

### 7.4 Hermes-related skills
Patch reason:
- if they treat Hermes as just another tool instead of a first-class architecture layer, they are incomplete

---

## 8. Immediate retire candidates

These are not specific named skills yet, but the retirement criteria are clear.

Retire a skill if it:
- depends on whole-repo ingestion as a normal workflow
- encourages narrative closure over bounded evidence
- assumes old repo/env layout that is no longer desired
- is superseded by a more precise bounded protocol
- is so stale that it is more misleading than helpful

---

## 9. Reference-only skill sources

Some surfaces should be mined for ideas without being treated as live skills yet.

Examples:
- `hermes-agent-self-evolution`
- `awesome-hermes-agent`
- large external agent ecosystems
- proof-search and geometry-search reference repos

Status:
- `reference_only` or `method_mine` until they have a real recurring job in this repo

---

## 10. Skill quality requirements

A real system skill should include:
- trigger/when-to-use
- exact role
- ordered steps
- exact commands or tool actions when relevant
- pitfalls / anti-patterns
- expected artifacts or outputs
- verification step

If a skill lacks these, it likely needs `patch` or should remain `reference_only`.

---

## 11. Relation to Hermes

Skills are a major part of making Hermes useful without making Hermes vague.

Skills help Hermes:
- stay bounded
- stay procedural
- avoid rereading too much
- avoid smoothing over critical distinctions
- operate more like a disciplined system component

So Hermes improvement and skills work are tightly linked.

---

## 12. Relation to the QIT proto work

The QIT engine proto needs repeatable procedures, not just one-off analysis.

Skills can help with:
- bounded pre-Axis sim audits
- lego-sim classification
- proof/graph requirement checks
- document generation for tranche reviews
- later candidate-law refinement procedures

That means QIT proto work is one of the strongest justifications for building new skills now.

---

## 13. Skills should not outrun the stack

Do not build a lot of skills for workflows that are still undefined.

Build skills in this order:
1. bounded Hermes intake and audit
2. current tool and install/use audit
3. QIT proto sim classification and planning
4. cleanup/inventory procedures
5. broader v5/system-building procedures later

---

## 14. Immediate next skill docs/procedures to build

Likely most useful next skill targets:
- bounded Hermes intake pack builder
- current tool-status audit skill
- pre-Axis sim tranche audit skill
- lego sim classification skill
- cleanup deletion-gate verification skill
- Hermes stack classification skill

---

## 15. Current best summary

Skills should become the procedural layer that makes:
- Hermes bounded and reliable
- tool audits repeatable
- QIT proto work operational
- cleanup slow and safe

The immediate skill program is not about quantity.
It is about building a small number of high-value recurring procedures and keeping them aligned with the current system reality.
