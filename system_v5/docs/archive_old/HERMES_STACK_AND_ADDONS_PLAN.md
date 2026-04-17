# Hermes Stack and Add-ons Plan

Status: working plan
Purpose: define Hermes itself, Hermes-related repos, Hermes add-ons, Hermes skills, and Hermes improvement surfaces as a first-class stack in the system

This document is not about the whole machine.
It is specifically about Hermes:
- what role Hermes plays
- what should be installed and used around Hermes
- what Hermes-adjacent repos matter
- how Hermes should be fed and improved
- what should happen before broad integration or cleanup

---

## 1. Core role of Hermes

Hermes is not just a convenience agent.
In this system Hermes is effectively:
- the A2 high-entropy ingestion plane
- a bounded planning and audit surface
- an architecture support layer
- a system that can later help ratchet the broader stack

Hermes should therefore be treated as:
- part of the architecture
- part of the install/use plan
- part of the skills plan
- part of the cleanup plan

---

## 2. Governing rules for Hermes use

1. Do not ask Hermes to understand the whole system at once.
2. Feed Hermes bounded packs slowly.
3. Every Hermes ingestion pass should have:
   - a scope
   - a role
   - a task
   - a required output
4. Hermes should not be rewarded for smoothing ambiguity.
5. Hermes should not be asked for narrative closure where proof/graph/sim pressure is required.
6. Hermes should support the QIT engine work, not replace it with prose.
7. Hermes stack planning should happen before mass installs or mass cleanup.

---

## 3. What counts as “Hermes extensions”

Hermes extensions means:
- Hermes itself
- Hermes-related repos
- things built to make Hermes better
- self-improvement / self-evolution surfaces
- Hermes-specific skills
- Hermes-specific operational patterns
- bounded ingestion/audit workflows around Hermes

It does NOT just mean random plugins.

---

## 4. Hermes stack categories

The Hermes stack should be split into these categories:

1. Hermes core
2. Hermes improvement repos
3. Hermes ecosystem/reference repos
4. Hermes skills
5. Hermes bounded-ingestion procedures
6. Hermes verification and safety procedures
7. Hermes future self-improvement layer

---

## 5. Hermes core

### 5.1 Role
Hermes core is the main operational agent surface.
It should be stable enough to:
- read bounded packs
- help plan
- help audit
- help organize the system
- later support scientific workflow around the QIT engine stack

### 5.2 Current planning priority
Hermes core should be made solid before trying to use Hermes as a universal ingestion engine.

### 5.3 What “solid” means
At minimum:
- correct tool access
- clear install/use path
- bounded context discipline
- stable skill loading behavior
- no broad-prompt “digest everything” workflow
- good support for formal docs and audits

---

## 6. Hermes improvement repos

These are Hermes-adjacent repos that may improve Hermes directly.
They must be classified explicitly.

### 6.1 Hermes self-evolution
Repo surface:
- `~/GitHub/hermes-agent-self-evolution`

Current role:
- Hermes improvement / self-improvement research surface
- likely method mine for evolving Hermes behavior, workflows, prompts, or skills

Current status:
- important reference repo
- not yet assumed to be directly integrated

Rule:
- treat as a real Hermes-stack repo, not just random research clutter

### 6.2 Awesome Hermes Agent
Repo surface:
- `awesome-hermes-agent`

Current role:
- curated ecosystem/reference surface
- useful for skills planning, ecosystem scanning, and Hermes-specific ideas

Current status:
- reference/method surface
- not core runtime

Rule:
- use for inventory and idea mining, not as canonical runtime truth

### 6.3 Other Hermes-adjacent repos
Any repo that directly improves Hermes should eventually be marked as one of:
- active dependency
- active integration target
- reference only
- later experiment surface
- ignore/stale

---

## 7. Hermes ecosystem / reference surfaces

Hermes should not be planned in isolation.
Its improvement stack can draw from:
- Hermes core repos
- Hermes self-evolution work
- Hermes curated ecosystem lists
- Leviathan-adjacent agent repos where relevant
- agent workflow / context engineering / memory / self-improvement methods

But all such sources must be bounded and classified.

No repo should remain an undefined “maybe useful” blob.

---

## 8. Hermes skills

### 8.1 Why Hermes skills matter
Skills are one of the main ways Hermes becomes reliably useful rather than just improvisational.

Hermes skills matter for:
- bounded ingestion
- audit procedures
- cleanup procedures
- graph/proof/sim setup procedures
- recurring system workflows

### 8.2 Current skill categories relevant to Hermes
Important Hermes skill categories likely include:
- bounded intake / bounded briefing skills
- repo audit skills
- Python/tooling audit skills
- graph/proof setup skills
- QIT/sim contract support skills
- cleanup/migration planning skills
- Hermes self-improvement / stack-maintenance skills

### 8.3 Skill rule
A Hermes skill should only exist if it has a recurring operational job.
No decorative or vague skills.

### 8.4 Immediate Hermes skill priorities
The most useful near-term Hermes skill areas are:
- bounded high-entropy intake
- repo/tooling audit
- formal document generation
- graph/proof tool planning
- QIT engine support planning

---

## 9. Hermes bounded-ingestion method

This is one of the most important parts of the Hermes stack.

### 9.1 Core rule
Hermes should be fed slowly.
Not whole-system ingestion.

### 9.2 Every bounded ingestion pack should specify
- purpose
- role for Hermes
- files/paths to read
- what NOT to read
- exact audit or planning question
- expected output format

### 9.3 Good use cases
Good bounded packs include:
- one recent sim tranche
- one proof/graph audit surface
- one Hermes-related repo surface
- one skills surface
- one subsystem planning problem

### 9.4 Bad use case
Bad prompt:
- “read my whole repo/system and understand it”

---

## 10. Hermes verification / safety procedures

Hermes should be checked for:
- bounded-scope compliance
- no false certainty
- no smoothing over open branches
- no replacing proofs/sims with narrative
- respecting tool and artifact requirements
- respecting the current stack priority

This matters because Hermes is operating in a high-entropy role.
Without discipline, it will over-compress and over-smooth.

---

## 11. Hermes relation to the QIT engine work

### 11.1 Hermes is not the scientific proof engine
Hermes helps organize and refine the work.
It does not replace:
- sims
- negatives
- proofs
- graph artifacts
- scientific pressure

### 11.2 Hermes does support the scientific workflow
Hermes can help with:
- planning
- bounded ingestion
- audit
- documentation
- synthesis of subsystem state
- identifying missing tool wiring
- skill-building around repeated workflows

### 11.3 Proper relation
The QIT engine prototype and pre-Axis sim ladder are the immediate scientific substrate.
Hermes should support that substrate and later grow out of it.

---

## 12. Hermes install/use priority

Hermes-related install/use priority should be:

1. Hermes core working cleanly
2. Hermes add-ons/improvement surfaces documented
3. Hermes ecosystem/reference surfaces classified
4. Hermes bounded-ingestion workflow formalized
5. Hermes skill plan formalized
6. Hermes self-evolution/improvement layer explored carefully

This should happen alongside, not instead of:
- graph/proof/geometry tool stabilization

---

## 13. Hermes stack classification model

Every Hermes-related surface should eventually be marked as one of:
- `core`
- `active dependency`
- `active integration target`
- `reference only`
- `method mine`
- `later experiment`
- `legacy/stale`

This should apply to:
- repos
- skills
- add-ons
- ecosystem lists
- self-evolution surfaces

---

## 14. Immediate next Hermes documents that should exist

After this plan, likely companion docs are:
- `HERMES_CURRENT_STATUS__INSTALLED_VS_PRESENT_VS_NOT_WIRED.md`
- `HERMES_REPOS_AND_ECOSYSTEM_CLASSIFICATION.md`
- `HERMES_SKILLS_PLAN__KEEP_BUILD_PATCH_RETIRE.md`
- `BOUNDED_HERMES_INGESTION_PROTOCOL.md`

---

## 15. What not to do yet

Do not:
- try to turn Hermes into the whole system at once
- ask Hermes to ingest everything
- treat Hermes self-evolution as a substitute for proof/graph/sim legitimacy
- mass install Hermes-adjacent things without classification
- build Hermes skills before clarifying their recurring job

---

## 16. Current best summary

Hermes should be treated as a first-class architecture layer.
Its immediate role is as the A2 high-entropy ingestion plane.

So the Hermes stack must be planned explicitly across:
- core setup
- improvement repos
- ecosystem references
- skills
- bounded-ingestion method
- verification/safety discipline

Hermes should help the QIT engine and broader system become clearer and more disciplined.
It should not be used as a substitute for real scientific or simulation legitimacy.
