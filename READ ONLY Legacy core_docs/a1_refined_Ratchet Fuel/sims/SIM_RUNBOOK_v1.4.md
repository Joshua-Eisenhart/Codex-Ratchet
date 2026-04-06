# SIM Runbook v1.4 (simpy/simson integration)

This runbook is **engineering**, not truth‑claims.  
Goal: make SIM runs **repeatable**, **auditable**, and **ratchet‑compatible** without you doing manual edits.

---

## 0) One rule that prevents 90% of pain

### Thread‑B only accepts:
- **one** `EXPORT_BLOCK` *or*
- **one** `SAVE_SNAPSHOT` *or*
- a **SIM_EVIDENCE pack** (i.e., **one or more `SIM_EVIDENCE` blocks back‑to‑back**)  

…and **nothing else**. No commentary, no headers, no extra whitespace narrative.

So when you paste evidence: paste **only** the `BEGIN SIM_EVIDENCE… END SIM_EVIDENCE` blocks.  
(If you include even a single stray sentence above them, Thread‑B will HALT.)

---

## 1) Fast-start checklist (deterministic, low‑drama)

If you want “up and running quick” while staying maximally pure:

1) **Boot Thread‑B** (kernel pinned).  
2) **Replay a tape** (preferred for certainty) *or* load snapshot + then replay term bootstrap tape.  
3) **Run sims from the simpy/simson folder** (or your Cursor/Codex runner).  
4) **Paste SIM_EVIDENCE blocks** back into Thread‑B (no extra text).  
5) If Thread‑B halts: isolate the failing SIM_ID and rerun just that script.

---

## 2) The “no‑manual‑editing” pattern (the one you want)

Most of your sim scripts already follow a pattern like this:

- run script  
- write a `results_*.json`  
- also write a `sim_evidence_pack.txt` containing paste‑ready `SIM_EVIDENCE` blocks

**So your workflow is:**
1) run `python <script>.py`  
2) open `sim_evidence_pack.txt`  
3) copy/paste its entire contents into Thread‑B

No hand‑formatting.

---

## 3) Debugging failures (when sims are huge)

### 3.1 If a single bad item would kill a giant run
Don’t do “one mega run” while still evolving mappings. Do **sharded runs**:

- 4‑stage / 8‑stage micro sims (seconds)
- mid sims (1–3 minutes)
- then “mega sim” (30+ min) only after you’ve locked mapping + invariants

### 3.2 Binary search the failure
If a mega suite fails:
- split the suite in half
- rerun halves
- repeat until you isolate the failing SIM_ID

### 3.3 Use negative controls as “fault detectors”
Negative controls catch hidden drift:
- commutation‑forced control (order erased)
- no‑entanglement / no‑correlation control
- label swap control (mapping broken on purpose)

If negative control unexpectedly “passes,” you found a bug.

---

## 4) What we are actually testing (tight scope)

This matters because it tells you which sims to prioritize.

### Axis‑4 (variance‑order class) is **two kinds of math**, not “loop order”
- inductive = variance/spread before constraint  
- deductive = constraint before expansion  

Your axis‑4 seq sims (“both dirs”) are the right harness for this.

### Axis‑1 × Axis‑2 form **Topology4**
Axis‑1 and Axis‑2 are not “graph edges.” They define **four orthogonal regimes** (Topology4) that later connect via edges.

### Axis‑3 turns Topology4 into Terrain8
Same 4 base topologies; flux/chirality produces the inward/outward variants.

---

## 5) Minimal sim suite (what to run first)

1) **Axis‑4 seq both dirs** (SEQ01–SEQ04, plus type‑2 suite)  
2) **Axis‑3 Weyl/Hopf grid** (chirality realization)  
3) **Axis‑0 trajectory correlation / mutual info suite**  
4) **Axis‑12 channel realization / topology4 terrain8 suite**  
5) then “ultra stack” (only after the above are stable)

---

## 6) Paste hygiene (copy/paste exact)

### Correct
```
BEGIN SIM_EVIDENCE v1
...
END SIM_EVIDENCE v1
BEGIN SIM_EVIDENCE v1
...
END SIM_EVIDENCE v1
```

### Incorrect
- any prose above/between blocks
- Markdown code fences
- “here’s the evidence: …”

Thread‑B will treat that as contamination.

---

## 7) Where the docs live

- `SIM_CATALOG_*` = what each SIM_ID means + what it’s testing
- `SIM_EVIDENCE_PACK_*` = paste‑ready evidence blocks (generated)
- `run_*` scripts in simpy/simson = actual harnesses

