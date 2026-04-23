# Bounded Hermes Ingestion Protocol

Status: working protocol
Purpose: define how Hermes should be fed bounded high-entropy material so it helps the system without drowning in mixed layers, stale branches, or narrative smoothing

This protocol exists because Hermes is useful at processing high entropy, but only if the intake is constrained.

---

## 1. Core rule

Never ask Hermes to ingest the whole system at once.

Hermes should always receive:
- a bounded pack
- a defined role
- a defined frame
- a defined output
- explicit exclusions

If these are missing, the intake is malformed.

---

## 2. Why bounded ingestion is required

Unbounded ingestion causes:
- mixed layers
- stale branch contamination
- old-doc overload
- graph overload
- over-compression
- smoothing over unresolved structure
- fake closure
- loss of tier discipline

Bounded ingestion is therefore mandatory.

---

## 3. Hermes role during ingestion

Hermes is not being used here as a universal knower.
Hermes is being used as:
- A2 high-entropy ingestion plane
- bounded synthesis/audit surface
- planning and classification support
- architecture support layer

Hermes should therefore be told what role it is playing for each intake.

Allowed role examples:
- `audit reader`
- `bounded synthesizer`
- `tool-role mapper`
- `sim tranche classifier`
- `Hermes-stack planner`
- `skills planner`
- `cleanup planner`
- `reference-repo classifier`

---

## 4. Every bounded pack must contain these fields

Each bounded Hermes intake pack should explicitly specify:

1. `purpose`
   - what this pack is for

2. `role`
   - what Hermes is supposed to be in this pass

3. `frame`
   - what perspective to use
   - examples:
     - pre-Axis admission
     - Hermes-stack planning
     - proof/graph audit
     - skills curation

4. `read_order`
   - exact files/paths in order

5. `do_not_read`
   - explicit exclusions
   - this is important

6. `questions`
   - exact questions to answer

7. `required_output`
   - exact output form

8. `promotion_rule`
   - what should and should not be concluded from the pack

---

## 5. What a good bounded pack looks like

A good pack is:
- narrow enough to keep one frame coherent
- broad enough to answer one meaningful question
- ordered
- explicit about exclusions
- explicit about output expectations

Examples of good bounded packs:
- one sim tranche
- one pre-Axis tier family
- one graph/proof tool surface
- one Hermes planning problem
- one skills curation pass
- one set of old boot docs for a specific purpose

Examples of bad bounded packs:
- “read the whole repo”
- “understand my entire system”
- “read system_v4 and system_v5 and tell me what to do”

---

## 6. Pack size guidance

Hard numbers are not fixed, but practical discipline matters.

A pack should usually be one of:

### Small pack
Use for:
- one narrow subsystem
- one immediate install or audit question

Typical contents:
- 3–8 files
- one frame
- one output

### Medium pack
Use for:
- one tranche or one architecture problem

Typical contents:
- 8–20 files
- one frame
- several tightly related questions

### Large bounded pack
Use for:
- one major but coherent workstream

Typical contents:
- 20+ files only if all are in the same frame and ordered carefully

Rule:
- if the frame changes, make a new pack

---

## 7. Frame discipline

Every pack must say what frame to use.

Examples:

### `pre-axis-admission`
Hermes should interpret materials as:
- lower-tier scientific substrate
- not Axis construction
- not broad speculative doctrine

### `tool-stack-planning`
Hermes should interpret materials as:
- install/use planning
- named jobs for tools
- not broad scientific theory synthesis

### `Hermes-stack-planning`
Hermes should interpret materials as:
- Hermes itself and its improvement surfaces
- not the whole QIT engine or the whole repo

### `skills-curation`
Hermes should interpret materials as:
- keep/build/patch/retire logic
- not general architecture or science doctrine

If the wrong frame is used, the pack is invalid even if the files are good.

---

## 8. Exclusion discipline

Every pack should explicitly say what not to read.

This is necessary because Hermes can otherwise blur:
- old and new docs
- current and legacy branches
- theory and tooling
- geometry and symbolic overlays
- actual sims and narrative packet summaries

Examples:
- do not read old system_v4 general docs
- do not read whole repo
- do not read unrelated Hermes ecosystem repos
- do not use high-entropy model-context docs as authority
- do not use legacy bootpacks unless explicitly asked

---

## 9. Output discipline

Every pack should require an explicit output form.

Good output forms include:
- keep / audit further / demote / broken map
- install/use matrix
- current status table
- named jobs for tools
- pack-specific summary
- explicit unanswered questions
- no-promotion blockers
- next bounded pack recommendation

Bad output forms:
- broad freeform philosophical synthesis
- “here is my understanding of your whole system”
- premature confidence

---

## 10. Promotion discipline for ingestion

Reading a pack does not automatically promote the contents.

A bounded Hermes pass may do things like:
- classify
- summarize
- identify blockers
- map tools to jobs
- identify missing evidence
- propose next work

It may not by itself:
- admit laws
- promote geometry claims
- close open branches
- reclassify diagnostic sims as real evidence

unless the pack explicitly includes the evidence and the task explicitly calls for that judgment.

---

## 11. Standard bounded-pack template

Use a structure like this:

```text
Purpose:
- <what this pack is for>

Role for Hermes:
- <what Hermes should be in this pass>

Frame:
- <pre-Axis admission / Hermes planning / tool audit / skills curation / etc.>

Read in this order:
1. <path>
2. <path>
3. <path>
...

Do not read:
- <excluded areas>
- <excluded doc families>
- <excluded legacy surfaces>

Questions to answer:
1. <question>
2. <question>
3. <question>
...

Required output:
- <format>

Promotion rule:
- <what Hermes is not allowed to overclaim>
```

---

## 12. Standard output checklist for Hermes

Hermes output should usually include:
- what worked
- what is still open
- what is only diagnostic
- what is blocked
- what should happen next
- what should NOT be concluded yet

Optional:
- exact next bounded pack
- exact install/use follow-up
- exact skill gap

---

## 13. Common pack types to use next

### 13.1 Tool-role pack
Purpose:
- map one set of tools to named jobs

### 13.2 Sim-tranche pack
Purpose:
- classify one tranche of recent sims

### 13.3 Hermes-stack pack
Purpose:
- assess Hermes core/add-ons/ecosystem/skills

### 13.4 Skills pack
Purpose:
- curate or patch skills in one coherent area

### 13.5 QIT proto pack
Purpose:
- one bounded slice of the QIT engine prototype and its immediate scientific requirements

---

## 14. Anti-patterns

Do not do:
- giant mixed packs with multiple frames
- theory + tools + skills + cleanup all in one prompt without order
- packs with no exclusions
- packs with no required output
- packs where Hermes is expected to decide the frame itself
- packs that reward narrative compression over explicit classification

---

## 15. Relation to the broader system

This protocol exists because:
- Hermes is useful at high-entropy ingestion
- the system is too large and layered for unbounded reading
- the QIT engine and pre-Axis substrate must be handled carefully
- planning and architecture work must stay bounded and auditable

Hermes should therefore be used as a disciplined ingestion and synthesis tool, not as a freeform totalizing interpreter.

---

## 16. Current best summary

The right way to use Hermes is:
- one bounded pack at a time
- one frame at a time
- one role at a time
- one required output at a time

If a pack is unbounded, mixed-frame, or under-specified, Hermes should not be trusted to produce clean system guidance from it.
