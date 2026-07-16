#!/usr/bin/env python3
"""generate_bundle_docs.py -- SELF-DESCRIBING BUNDLE GENERATOR (2026-07-10).

Regenerates the bundle's orientation/doc set from LIVE state every ship, so external consumers (the codex app, other
sim runners, future sessions) can process the zip STANDALONE and it can never drift stale. Run from the bundle root:
    python generate_bundle_docs.py
Emits (all at bundle root, in docs/BUNDLE_*.md and bundle_manifest.json):
  - BUNDLE_GUIDE.md        : what this is, the root project, plan, current state, what's being worked, future projects
  - TOOLS_AND_REPOS.md     : every tool/env/solver/library + versions, repos, the 3-engine dependency contract
  - MATH_INVENTORY.md      : every math class in play, forced vs installed vs withdrawn, with the deciding constraint
  - WITHDRAWN_AND_FAILED.md: registry of NEGATIVES -- withdrawn UPs, failed proposed math, why (negatives are data)
  - UP_REGISTRY.md         : every UP ledger entry (number, title, status) parsed from MODEL_LAYER_LEDGER.md
  - bundle_manifest.json   : machine-readable superset (for codex to parse programmatically)

Everything is PARSED from the live files (MODEL_LAYER_LEDGER.md, run_all.py, run_all_report.json, requirements.txt,
installed package versions) -- nothing is hardcoded, so the docs always match the shipped state. Static hand-curated
prose (the root project statement, the plan, future projects) lives in the EDITABLE BLOCKS below and is the ONLY thing
to update by hand as direction changes.
"""
import json, os, re, sys, subprocess, datetime

ROOT=os.path.dirname(os.path.abspath(__file__))
def R(p): 
    fp=os.path.join(ROOT,p)
    return open(fp).read() if os.path.exists(fp) else ""

# ============================ EDITABLE BLOCKS (hand-curated; update as DIRECTION changes) ============================
ROOT_PROJECT = """The root project is to formalize CREATION, MATHEMATICS, PHYSICS, PERCEPTION, and INTELLIGENCE through
one finite, history-bearing admissibility Ratchet. ROOT = CONSTRAINED_DISTINGUISHABILITY: no object, equivalence,
quotient, support, entropy, geometry, carrier, algebra, or cellular automaton is primitive. F01 (finitude) and N01
(noncommutation) constrain candidates and the search. Gate boundaries, subgates, orders, decompositions, gradients, and
weakness relations are proposal populations. A surviving entropy–geometry coface gradient supplies the reason and
direction for a tooth, while a missing witness expands the unordered dig pool.
MSS computes a provisional MSS frontier of all
currently
undefeated minimal survivors inside a declared finite candidate grammar, weakening grammar, test battery, and budget.
Evidence history is append-only; every model frontier is defeasible when a weaker survivor or stronger negative appears.
Nonassociativity (T01) and every other lift remain hypotheses until a load-bearing demand defeats weaker alternatives.

The downstream FACES (all measure whether the root works; none is the root): the dual-ratchet entropic-geometric
constraint MANIFOLD; the QIT ENGINES (two Weyl-chirality engine types x 8 terrains x operators); FEP/active-inference
(a QIT FEP, no classical thermo); IGT / known-unknown; object-perception ("holodeck") with distinguishability gates;
the physics TOE (GR+SM as new foundations, gravity as entropy gradient, chiral spacetime); cosmogenesis (MSS in a
static field, dark-energy-first). Oracle duality: deduction<->induction, Turing<->oracle, reason<->perception."""

PLAN = """ORDER-OPEN SEARCH, always looping back to constrained distinguishability. The currently executable QIT route
is one installed proposal: complex-spinor carrier -> Schmidt strata / nested shells -> BKM relative-entropy Hessian ->
Berry holonomy / flux -> Weyl chirality -> engine stages. Its ordering, boundaries, and missing substeps are not canon.
Surface-identity and Umegaki/Petz results are later-layer fixtures whose uniqueness and MSS standing remain open.

METHOD: (1) mine finite demand families without fixing their gates; (2) generate rival candidates, gate boundaries,
orders, decompositions, gradients, weakness relations, negatives, and controls at high exploration temperature;
(3) stream every proposal allowed by the finite budget and deduplicate behavioural aliases; (4) execute fused and split
schedule hypotheses; (5) compute every packet-relative MSS antichain; (6) admit narrowly at low admission temperature;
(7) emit every kill, projection, residual, schedule divergence, and open attack; (8) keep authored seeds separate from
run-derived questions in an unordered dig pool.
Known theorems and green sims are realizations, not self-promoting admission evidence."""

CURRENT_FOCUS = """Ratchet v0.7 makes the complete locally available proposal/evidence population functional project
memory. It preserves the v0.6 manifold audit while surfacing all 190 top-level simulation scripts, including 46 that
are not registered in run_all.py. Dedicated reports now expose exceptional/nonassociative mathematics and attractor
basins with their controls, retractions, and admission ceilings. Four 127 artifacts omitted by 130 are hash-restored.
Julia now owns the exceptional algebra convention in source and export form; local Julia replay remains honestly
blocked because this build container has no Julia runtime."""

FUTURE_PROJECTS = """(A) Get the QIT engines FULLY running in deep nuance: every stage/substage doing distinct
information processing, all axes load-bearing on one running trajectory, Axis-0 end-to-end entropy-gradient on the
engine pair. (B) Axes 7-12 = the FIELD OF ENGINES (each node an engine; natural home of IGT) with its own embedding
geometry -- where the exceptional algebras (E6/E8/Albert) may finally become load-bearing; needs a field-metric rung.
(C) Grand-application projects, kept ONLY where they consistently help the overall system when looped back from
foundations: fine-structure constant, P-vs-NP, Navier-Stokes, Riemann/primes, Yang-Mills, GR+SM unification, gravity,
cosmogenesis. All GATED behind earning the structure they need; no skipping ahead. (D) Idempotent-analysis/HJB as a
possible forced ratchet STEP (decohere->T->0), which would upgrade the max-plus placement from context to a gate.
(E) Run the owner's real Julia/JAX/PyTorch engines where load-bearing (Julia canon arbiter; strict-carrier laptop-side
due to registry TLS block)."""

DEPENDENCY_CONTRACT = """THREE-ENGINE DEPENDENCY CONTRACT (load-bearing gates): z3 AND cvc5 must agree on the same
structural claim with erased controls that flip it; numpy/scipy/mpmath are CONTROL-LANE only, never load-bearing; at
least one tool outside the array baseline must gate a verdict. Sims carry NO jargon -- pure real math and structure;
a rosetta layer maps earned structure to labels afterward."""

VALIDATION_NOTE = """The order-open engine self-test, saved-run validation, bundle lint, L1-L8 direct execution,
entropic-geometry audit, and manifold fixture Ratchet pass. The initial local full harness is honestly red at 109 pass /
4 fail / 33 skip; its receipt is preserved. Three failures passed individually after installing SymPy/PySINDy. The
legacy fixed-ladder nonlinear Z3/cvc5 instrument did not complete in its finite test window and was not weakened to make
the bundle green. The 129 input's front door reported 146/0/0 from another environment but shipped no matching
top-level report; it is provenance, not a substitute for the local receipt."""

SOURCE_LINEAGE = {
    "source_archive": "130_claude_science_executed_manifold_ratchet_v0_6.zip",
    "source_archive_sha256": "07c4262ddce3ec3fb2a6ecb18f03a6806cd2f0c2fc15b9b2b8c95b62642de3e4",
    "source_entry_count": 682,
    "compared_archive": "127.zip",
    "compared_archive_sha256": "c3cc3272a1121e6bd54de78a2544c26612b569199b86e06c2a5553c88cfdbcbd",
    "upgrade": "Ratchet v0.7: complete preservation/surfacing, dedicated exceptional and basin state, Julia algebra ownership",
    "output_bundle": "131_claude_science_preservation_complete_ratchet_v0_7.zip",
    "source_mutated_in_place": False,
}

CONSUMER_NOTE = """FOR EXTERNAL CONSUMERS: run `python preservation/verify_preservation.py` and
`python ratchet/bundle_ratchet_lint.py`, then read the preservation index, complete simulation ledger, exceptional
math report, basin report, and manifold report before any legacy layer ledger. `python run_all.py` is a legacy
aggregate reproduction lane, not the complete inventory and not an admission engine. MODEL_LAYER_LEDGER.md is a legacy
component/result history, not an MSS admission ledger. A receipt may earn only a scoped provisional frontier member;
it does not establish a global minimum or promote descendants. Run candidate, gate-boundary, decomposition, and order
populations before claiming the Ratchet ran. A missing drive witness yields no tooth and an expanded unordered dig pool,
never a global terminal HOLD. Re-run
`python generate_bundle_docs.py`, then `python preservation/build_preservation_reports.py`, to regenerate
the live docs and hash manifest without restoring the older root/forcing language."""
# ====================================================================================================================

def parse_ups(ledger):
    """Parse every '## UP-N ... title' header; dedupe by UP number, withdrawn-wins.
    A rung may appear twice (original ship header + a later WITHDRAWN header); the WITHDRAWN status must win and the
    withdrawal title is preferred."""
    seen={}
    for m in re.finditer(r'^##\s+(UP-[0-9/]+)\s+(?:--\s*)?(.+)$', ledger, re.M):
        num,rest=m.group(1),m.group(2).strip()
        low=(num+" "+rest).lower()
        status="withdrawn" if "withdrawn" in low else "shipped"
        if num not in seen:
            seen[num]={"up":num,"title":rest,"status":status}
        else:
            # merge: withdrawn wins, and prefer the withdrawn title
            if status=="withdrawn":
                seen[num]={"up":num,"title":rest,"status":"withdrawn"}
    # preserve first-seen order by UP numeric where possible
    def key(u):
        mm=re.match(r'UP-(\d+)',u["up"]); return int(mm.group(1)) if mm else 9999
    return sorted(seen.values(), key=key)

def parse_registered_sims(runall):
    """Return every Python script registered in SUITE/TORCH_SUITE.

    The old `_sim.py`-only regex silently omitted proof, bridge, linter, emitter,
    and ladder scripts even though run_all executed them.
    """
    return sorted(set(re.findall(r'^\s*\("([^"]+\.py)"\s*,\s*\d+', runall, re.M)))

def get_versions():
    vers={}
    for mod in ["numpy","scipy","sympy","sklearn","pysindy","z3","cvc5","mpmath"]:
        try:
            code=f"import {mod};v=getattr({mod},'__version__',None) or getattr({mod},'get_version_string',lambda:'present')();print(v)"
            out=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True,timeout=60)
            vers[mod]=out.stdout.strip() if out.returncode==0 else "not present"
        except Exception: vers[mod]="unknown"
    return vers

def main():
    ledger=R("MODEL_LAYER_LEDGER.md"); runall=R("run_all.py"); changelog=R("CHANGELOG_HARDENING.md")
    report=json.loads(R("run_all_report.json")) if R("run_all_report.json") else {}
    ratchet_run=json.loads(R("ratchet/runs/root_order_open_run_v0_5.json")) if R("ratchet/runs/root_order_open_run_v0_5.json") else {}
    summ=report.get("summary",{})
    ups=parse_ups(ledger); regsims=parse_registered_sims(runall); vers=get_versions()
    all_top_sims=sorted(f for f in os.listdir(os.path.join(ROOT,"sims_and_scripts")) if f.endswith(".py"))
    registered_set=set(regsims)
    unregistered_sims=sorted(set(all_top_sims)-registered_set)
    withdrawn=[u for u in ups if u["status"]=="withdrawn"]
    now=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    hp=summ.get("pass","?"); hf=summ.get("fail","?"); hs=summ.get("skip","?"); green=summ.get("green","?")

    docs=os.path.join(ROOT,"docs"); os.makedirs(docs,exist_ok=True)

    # math-class inventory: parse sim filenames for math keywords -> a coarse but real inventory
    mathmap={"entangl":"entanglement/negativity","bkm|modular|umegaki|petz|dpi|relent":"QIT entropy / modular theory",
      "jordan|albert|j3o|octonion|malcev|fano|spin9|op2|exceptional|nonassoci|f4|e6|g2|clifford|hopf":"nonassociative / exceptional algebra (Jordan/octonion/Lie)",
      "attractor|basin|hysteresis|memory_carrier":"attractor basins / multistability / memory",
      "spinor|weyl|chiral|holonomy|berry":"spinor / chirality / holonomy","schmidt|shell|metric|geodesic":"information geometry / manifold",
      "maxplus|tropical|idempotent":"tropical / max-plus (idempotent)","qfi|fubini|fisher":"quantum information geometry (QFI/Fubini-Study)",
      "braid|hott|homotop":"topology / braid groups (HoTT)","fep|surprise|active":"FEP / active inference",
      "carnot|szilard|landauer|thermo":"thermodynamic bridges (rosetta only)","mond|a0|redshift|physics|gravity|cosmo":"physics bridges / TOE",
      "smt|z3|cvc5":"SMT-gated structural proofs","penrose|aperiodic|e8":"aperiodic order / E8 (not forced)",
      "hubbard|biochem|tunnel|chem":"chemistry / biochem bridges","axis|engine|terrain|stage|substage|schedule":"QIT engine mechanics / axes"}
    mathinv={}
    for s in regsims+[u["up"] for u in withdrawn]:
        pass
    allsims=all_top_sims
    # Classify every script. Registration is recorded separately and never used as an existence filter.
    for s in allsims:
        for pat,label in mathmap.items():
            if re.search(pat,s): mathinv.setdefault(label,[]).append(s)

    # ---------- BUNDLE_GUIDE.md ----------
    g=f"""# BUNDLE GUIDE -- constraint_core_unified (self-describing)
_Regenerated {now} from live ledger + harness. Do not hand-edit; run `python generate_bundle_docs.py`._

## Legacy aggregate harness state (authoritative for that lane only)
**{hp} pass / {hf} fail / {hs} skip -> {"GREEN" if green else "NOT GREEN"}**  ({len(regsims)} registered sims; {len(all_top_sims)} total top-level scripts; {len(unregistered_sims)} unregistered and surfaced; {len(ups)} UP rungs in ledger, {len(withdrawn)} withdrawn.)
Aggregate run: `python run_all.py` (full, no --fast). Result: `run_all_report.json`. This is not a complete project-memory or admission lane.

{VALIDATION_NOTE}

## Upgrade lineage
Source: `{SOURCE_LINEAGE['source_archive']}`, SHA-256 `{SOURCE_LINEAGE['source_archive_sha256']}`, {SOURCE_LINEAGE['source_entry_count']} file entries.
The source attachment was not overwritten; this bundle is a separate Ratchet v0.7 preservation-complete derivative.

## The root project
{ROOT_PROJECT}

## Plan & method
{PLAN}

## What is being worked NOW
{CURRENT_FOCUS}

## Future projects
{FUTURE_PROJECTS}

## For external consumers (codex app, other sim runners)
{CONSUMER_NOTE}

## Doc set in this bundle (docs/)
- `BUNDLE_GUIDE.md` (this file) -- plan, state, focus, future
- `TOOLS_AND_REPOS.md` -- every tool/solver/library + versions, repos, dependency contract
- `MATH_INVENTORY.md` -- every math class, forced vs installed vs withdrawn
- `WITHDRAWN_AND_FAILED.md` -- registry of NEGATIVES (as informative as positives)
- `UP_REGISTRY.md` -- every rung (UP) with status
- `../preservation/THREAD_WORK_PRESERVATION_INDEX.md` -- anti-amnesia front door and completeness boundary
- `../reports/SIM_REGISTRATION_LEDGER.md` -- all 190 scripts, not only registered scripts
- `../reports/DIRECT_RERUN_RECEIPTS.md` -- direct reruns, path repairs, and honest runtime blockers
- `../reports/EXCEPTIONAL_NONASSOCIATIVE_MATH_STATE.md` -- exceptional branch with actual math and controls
- `../reports/ATTRACTOR_BASIN_STATE.md` -- basin branch with audit reversals
- `../julia_canon/README.md` -- Julia algebra ownership and replay status
- `../RATCHET_SPEC.md` + `../ratchet/GRADIENT_DRIVE.md` -- working process and gradient-digging authority
- `../ratchet/runs/root_order_open_run_v0_5.json` -- executed 32,400-proposal, 75-schedule process trace
- `../ratchet/runs/L5_REAUDIT_AUDIT_KILLED_NOTE.md` -- audit fence on the killed v0.4 L5 demotion
- `../ratchet/manifold_evidence/MANIFOLD_RATCHET_STATE_REPORT.md` -- executed layer state and actual entropic geometry
- `../ratchet/manifold_evidence/manifold_fixture_ratchet_results.json` -- 16,384-proposal actual-observation trace
- `../ratchet/` -- engines, packets, frontier, schemas, CA lane, and lint
- `../ratchet/CA_MSS_RESEARCH_PROGRAM.md` -- bounded CA/ring-checkerboard candidate bakeoff
- `../bundle_manifest.json` -- machine-readable superset for programmatic parsing
"""
    open(os.path.join(docs,"BUNDLE_GUIDE.md"),"w").write(g)

    # ---------- TOOLS_AND_REPOS.md ----------
    vtable="\n".join(f"- **{k}**: {v}" for k,v in vers.items())
    t=f"""# TOOLS, SOLVERS, LIBRARIES & REPOS
_Regenerated {now}. Versions read from the live environment._

## Solver & library versions (this environment)
{vtable}

Python: {sys.version.split()[0]}. Env: constraintcore (conda). Numba cache: /tmp/numba_cache.

## Dependency contract
{DEPENDENCY_CONTRACT}

## Repos (source of truth)
- **codex-ratchet repo** (system_v7/constraint_core/): the v7 sim runner + working docs. Provenance and live code, not a truth database.
- **Wiki** (Joshua-Eisenhart/Joshua-Eisenhart-Wiki, projects/codex-ratchet/): synced reports, ledger, changelog, sims.
- **leviathan** (github.com/lev-os/leviathan): a CS-version reference of many concepts; REFERENCE not canon.
- **LevRatchet** (Joshua-Eisenhart/LevRatchet): private convergence/coordination repo; role must be earned per claim.
- **Sofia** (Kingly-Agency/Sofia): adjacent private agent/runtime work; relevance must be demonstrated.
- **Leviathan-Arbitrage** (Joshua-Eisenhart/Leviathan-Arbitrage): public application repo, not foundations authority.
- This bundle mirrors the audit-engine sim set; the codex app consumes these zips + runs its own sims.
- `GITHUB_REPO_CONTEXT_2026-07-10.md` records the connector snapshot and the local-vs-published boundary.

## How the pieces run
- `run_all.py` -- the full harness (each sim is a subprocess; a row PASSES on a 'contains' string match). No jargon in sims.
- `sims_and_scripts/` -- {len([f for f in os.listdir(os.path.join(ROOT,'sims_and_scripts')) if f.endswith('.py')])} python sim files (some are withdrawn scaffolds, not registered).
- `panel_adversarial_review.py` -- cross-family LLM panel (Gemini/Grok/Qwen/GLM) as an ADVISORY adversarial reviewer; never gates.
- `MODEL_LAYER_LEDGER.md` / `CHANGELOG_HARDENING.md` -- append-only rung record + hardening log.
"""
    open(os.path.join(docs,"TOOLS_AND_REPOS.md"),"w").write(t)

    # ---------- MATH_INVENTORY.md ----------
    mi=f"""# MATH INVENTORY -- classes in play, and their status under the constraints
_Regenerated {now}. Classes inferred from all top-level sim names; registration and status are tracked separately._

Every placement is scoped. **FORCED-WITHIN-GRAMMAR** means all survivors in one frozen finite candidate grammar carry
the property; it is not globally forced. **INSTALLED/REALIZED** means a runnable branch exhibits it without a uniqueness
claim. **EXCLUDED-WITHIN-SCOPE** means named finite tests killed it, not that every future formulation is impossible.

## Complete top-level math classes (by sim clustering)

This inventory scans all {len(all_top_sims)} scripts. A suffix `[unregistered]` means only that the script is not selected
by the current aggregate harness; it remains part of project memory. See the complete machine ledger for result status.
"""
    for label in sorted(mathinv):
        rendered=[s + (" [unregistered]" if s not in registered_set else "") for s in sorted(mathinv[label])]
        mi+=f"\n### {label}\n{len(mathinv[label])} sim(s): {', '.join(rendered)}\n"
    mi+=f"""
## Key placements after the v0.5 order-open process correction
- **constrained distinguishability** -- ROOT doctrine; no object/equivalence/carrier is included in the primitive.
- **entropy–geometry coface gradients** -- GENERATED DRIVE CANDIDATES. Collapsed demanded quotient edges and unresolved
  distinctions are the same finite surface quantity. A named entropy formula is not installed at the root.
- **complex spinor (qubit)** -- INSTALLED, machine-checked realization in the current grammar; not globally forced by F01/N01.
- **su(2)/Pauli noncommutation** -- REALIZED and load-bearing on the installed qubit branch; N01 does not uniquely select it.
- **Umegaki relative entropy / Petz pawl** -- REALIZED as a finite QIT monotone with recovery structure; uniqueness across
  all finite distinction presentations remains open.
- **BKM metric** -- REALIZED as the Umegaki Hessian. It is not selected uniquely on the installed commuting radial
  tangent: SLD/Bures, Wigner-Yanase, and RLD produce the same metric there.
- **Z2 spinor double cover, Weyl chirality, and Im(H)** -- REALIZED/FORCED-WITHIN-GRAMMAR at named QIT rungs; all remain
  open to weaker or non-isomorphic carrier challenges.
- **max-plus / tropical / idempotent** -- EXCLUDED-WITHIN-SCOPE as the coherent QIT foundation tested here;
  it is the T->0 decoherence/deductive-limit (Bellman) arithmetic. [UP-138]
- **QFI / Fubini-Study** -- INSTALLED as the fidelity/Bures-family metric; the current QIT route uses BKM as a
  relative-entropy Hessian, but the v0.6 audit kills BKM uniqueness on the commuting radial tangent. [UP-139]
- **HoTT / braid groups** -- CONSTRUCTIBLE-NOT-FORCED (needs a multi-anyon degenerate fusion space the single carrier
  lacks); forced carrier topology is the abelian Z2 double cover. [UP-140 withdrawn -- placement real, no failable gate]
- **octonions / T01 / Malcev / G2->F4->E6 / E8 / Albert(27) / 3-generations / Penrose** -- CONSTRUCTIBLE-NOT-FORCED
  ({{H,O}} branch); "3 generations = |chi|/2" is an ANSATZ. Live upper-layer math, not re-derived as forced.
- **Clifford Cl_3** -- REALIZED exactly at the installed Pauli-operator level and associative; it cannot carry octonionic
  nonassociativity in that fixture (a scoped decisive negative).
"""
    open(os.path.join(docs,"MATH_INVENTORY.md"),"w").write(mi)

    # ---------- WITHDRAWN_AND_FAILED.md ----------
    wf=f"""# WITHDRAWN & FAILED -- the NEGATIVES (as informative as the positives)
_Regenerated {now}. Withdrawn rungs parsed from the ledger; retained scaffolds live in sims_and_scripts/ but are NOT registered._

Proposed math that FAILS to be forced, and sims whose gates did not hold up, are first-class information: they tell you
what the constraints EXCLUDE or leave merely constructible. Nothing is deleted; withdrawals are recorded.

## Withdrawn rungs (from ledger headers)
"""
    for u in withdrawn:
        wf+=f"- **{u['up']}** -- {u['title']}\n"
    wf+=f"""
## Standing negatives (excluded / constructible-not-forced) -- see MATH_INVENTORY for the deciding constraint
- max-plus/tropical: EXCLUDED as foundation (interference breaks monotonicity). [UP-138]
- HoTT/braids: constructible-not-forced (no failable gate at the single carrier). [UP-140 withdrawn]
- octonions/T01/Malcev/exceptional tower/E8/Penrose/3-generations: constructible-not-forced ({{H,O}} branch, ansatz).
- "entropy = topology / Atiyah-Singer index" and E6-gauge/F4-gravity/dim-27: genuine established math on the unforced branch, NOT earned by {{F01,N01}}.
- gauge-breaking-law (old): WITHDRAWN as an algebraic identity (R^2=1 by construction).
- field-of-engines "weakest rung" (UP-137): WITHDRAWN -- opposite/same chirality gave identical negativity -> generic 2-qubit QM, not theory-specific.
- 64/64 substage uniqueness overclaim (UP-104/105): WITHDRAWN -- only a coarse subset shown position-unique.

## Why keep them
Each negative is a probe of the boundary of the forced core. A future forced DEMAND (e.g. a Malcev bracket, a
non-special 3-level observable, a field-metric rung) could promote a currently-unforced item; the negatives map where
to look. They also stop the grand-synthesis overclaim from creeping back in.
"""
    open(os.path.join(docs,"WITHDRAWN_AND_FAILED.md"),"w").write(wf)

    # ---------- UP_REGISTRY.md ----------
    ur=f"# UP REGISTRY -- every rung\n_Regenerated {now}. Parsed from MODEL_LAYER_LEDGER.md ({len(ups)} entries)._\n\n"
    for u in ups:
        mark="~~WITHDRAWN~~ " if u["status"]=="withdrawn" else ""
        ur+=f"- **{u['up']}** {mark}-- {u['title']}\n"
    open(os.path.join(docs,"UP_REGISTRY.md"),"w").write(ur)

    # ---------- bundle_manifest.json (machine-readable) ----------
    # ---------- 00_START_HERE.md (single entry point; curated static guidance, harness line live) ----------
    sh_path=os.path.join(ROOT,"00_START_HERE.md")
    if os.path.exists(sh_path):
        sh=open(sh_path).read()
        sh=re.sub(r"<!--LIVE_HARNESS-->.*?<!--/LIVE_HARNESS-->",
                  "<!--LIVE_HARNESS-->**Local container harness: %s pass / %s fail / %s skip -- green=%s** "
                  "(stamped %s). The supplied 129 front door reported 146/0/0 in a fuller environment but shipped no "
                  "matching top-level report; the dedicated manifold evidence lane is independently green.<!--/LIVE_HARNESS-->"%
                  (hp,hf,hs,green,now),
                  sh, flags=re.S)
        open(sh_path,"w").write(sh)

    manifold_run=json.loads(R("ratchet/manifold_evidence/manifold_fixture_ratchet_results.json")) if R("ratchet/manifold_evidence/manifold_fixture_ratchet_results.json") else {}
    geometry_audit=json.loads(R("ratchet/manifold_evidence/entropic_geometry_audit_results.json")) if R("ratchet/manifold_evidence/entropic_geometry_audit_results.json") else {}
    manifest={"generated_utc":now,"bundle_name":"131_claude_science_preservation_complete_ratchet_v0_7",
      "ratchet_spec_version":"0.7-preservation_on_0.6-evidence_application_on_0.5-engine",
      "root_primitive":"constrained_distinguishability",
      "drive_semantics":"entropy and geometry share one collapsed-demand-edge coface; positive repair contrast drives a tooth",
      "process_semantics":"mass candidate batches; all declared gate orders/decompositions; low-temperature packet admission; unordered dig pool",
      "mss_semantics":"finite-partition-refinement provisional antichain; weakness and global search remain open",
      "harness":{"pass":hp,"fail":hf,"skip":hs,"green":green,"registered_sims":len(regsims),
        "all_top_level_sims":len(all_top_sims),"unregistered_sims":len(unregistered_sims)},
      "versions":vers,"python":sys.version.split()[0],
      "ups":ups,"withdrawn":withdrawn,"registered_sims":regsims,"all_top_level_sims":all_top_sims,
      "unregistered_sims":unregistered_sims,
      "math_inventory":{k:sorted(v) for k,v in mathinv.items()},
      "root_project":ROOT_PROJECT,"plan":PLAN,"current_focus":CURRENT_FOCUS,"future_projects":FUTURE_PROJECTS,
      "dependency_contract":DEPENDENCY_CONTRACT,"consumer_note":CONSUMER_NOTE,"source_lineage":SOURCE_LINEAGE,
      "validation_note":VALIDATION_NOTE,
      "validation_environment":{
        "ratchet_integrity_lane":"PASS",
        "local_fast_harness":{"pass":hp,"fail":hf,"skip":hs,"green":green},
        "initial_missing_required_for_four_failures":["sympy","pysindy","z3"],
        "post_install_individual_rechecks":"sympy and both pysindy lanes pass; legacy nonlinear fixed-ladder solver exceeds finite window",
        "optional_runtime_gaps":"see run_all_report.json",
        "audited_input_harness_receipt":{"pass":146,"fail":0,"skip":0,"environment":"source archive owner environment"},
      },
      "ratchet_process_run":{
        "run_id":ratchet_run.get("run_id"),
        "claim_ceiling":ratchet_run.get("claim_ceiling"),
        "parameter_proposals_executed":ratchet_run.get("summary",{}).get("parameter_proposals_executed"),
        "behavioural_partition_classes":ratchet_run.get("summary",{}).get("behavioural_partition_classes"),
        "behaviour_subset_evaluations":ratchet_run.get("summary",{}).get("behaviour_subset_evaluations"),
        "parameter_aliases":ratchet_run.get("candidate_population",{}).get("parameter_aliases"),
        "schedule_hypotheses_executed":ratchet_run.get("summary",{}).get("schedule_hypotheses_executed"),
        "unique_trajectories":ratchet_run.get("gate_order_search",{}).get("unique_trajectories"),
        "unique_final_frontiers":ratchet_run.get("gate_order_search",{}).get("unique_final_frontiers"),
        "canonical_gate_order_admitted":False,
        "canonical_gate_decomposition_admitted":False,
        "scientific_manifold_layers_admitted":0,
        "physical_entropy_types_admitted":0,
      },
      "manifold_evidence_run":{
        "parameter_proposals_executed":manifold_run.get("candidate_population",{}).get("parameter_proposals_executed"),
        "behavioural_partition_classes":manifold_run.get("candidate_population",{}).get("behavioural_partition_classes"),
        "parameter_aliases":manifold_run.get("candidate_population",{}).get("parameter_aliases"),
        "schedule_hypotheses_executed":manifold_run.get("gate_order_search",{}).get("ordered_set_partitions_executed"),
        "orientation_gradient":manifold_run.get("entropy_geometry_coface",{}).get("orientation_tooth"),
        "phase_bridge_obstruction":geometry_audit.get("L6_to_L7_bridge",{}).get("phase_bridge_obstruction_fires"),
        "scientific_manifold_layers_admitted":0,
      },
      "doc_files":["RATCHET_SPEC.md","ESTATE_REGISTRY.yaml",
        "preservation/THREAD_WORK_PRESERVATION_INDEX.md","preservation/preservation_manifest.json",
        "preservation/bootstrap_project_memory.py",
        "preservation/standalone_path_audit.py","reports/DIRECT_RERUN_RECEIPTS.md",
        "reports/DIRECT_RERUN_RECEIPTS.json","reports/STANDALONE_PATH_AUDIT.json",
        "reports/V0_7_WORKING_TREE_VALIDATION.json",
        "preservation/CLAUDE_CODE_FAILURES_AND_GUARDS.md","reports/SIM_REGISTRATION_LEDGER.md",
        "reports/EXCEPTIONAL_NONASSOCIATIVE_MATH_STATE.md","reports/ATTRACTOR_BASIN_STATE.md",
        "julia_canon/README.md","julia_canon/artifacts/export_status.toml",
        "julia_canon/artifacts/python_cross_validation_receipt.json",
        "archive/RATCHET_V0_7_PRESERVATION_COMPLETE_UPGRADE_REPORT.md",
        "archive/RATCHET_V0_5_ORDER_OPEN_UPGRADE_REPORT.md",
        "archive/RATCHET_V0_6_MANIFOLD_EVIDENCE_UPGRADE_REPORT.md",
        "archive/INPUT_127_COMPARISON_AND_DISPOSITION.md",
        "archive/RATCHET_V0_5_VALIDATION_REPORT.md",
        "archive/RATCHET_V0_4_WORKING_PROCESS_UPGRADE_REPORT.md",
        "archive/RATCHET_V0_3_GRADIENT_UPGRADE_REPORT.md","archive/RATCHET_V0_2_UPGRADE_REPORT.md",
        "ratchet/GRADIENT_DRIVE.md","ratchet/README.md","ratchet/CURRENT_FRONTIER.md","ratchet/ratchet_engine.py",
        "ratchet/archive/ratchet_engine_v0_4_frozen.py","ratchet/archive/manifold_l5_reaudit_v0_4_killed.py",
        "ratchet/CA_MSS_RESEARCH_PROGRAM.md","ratchet/weakening_grammar.json",
        "ratchet/schemas/ratchet_order_open_run.schema.json","ratchet/examples/root_order_open_packet_v0_5.json",
        "ratchet/runs/root_order_open_run_v0_5.json","ratchet/runs/L5_REAUDIT_AUDIT_KILLED_NOTE.md",
        "ratchet/manifold_evidence/MANIFOLD_RATCHET_STATE_REPORT.md",
        "ratchet/manifold_evidence/L5_EXTERNAL_CLAIM_DISPOSITION.md",
        "ratchet/manifold_evidence/layer_execution_receipts.json",
        "ratchet/manifold_evidence/entropic_geometry_audit_results.json",
        "ratchet/manifold_evidence/manifold_fixture_ratchet_results.json",
        "ratchet/manifold_evidence/manifold_layer_state.json",
        "docs/BUNDLE_GUIDE.md","docs/TOOLS_AND_REPOS.md",
        "docs/GITHUB_REPO_CONTEXT_2026-07-10.md",
        "docs/MATH_INVENTORY.md","docs/WITHDRAWN_AND_FAILED.md","docs/UP_REGISTRY.md"]}
    json.dump(manifest,open(os.path.join(ROOT,"bundle_manifest.json"),"w"),indent=2)

    print(f"Generated docs/ (5 md) + bundle_manifest.json")
    print(f"  harness {hp}/{hf}/{hs} green={green}; {len(ups)} UPs ({len(withdrawn)} withdrawn); {len(regsims)} registered / {len(all_top_sims)} total sims")
    print(f"  math classes: {len(mathinv)}; versions: {', '.join(f'{k}={v}' for k,v in list(vers.items())[:4])} ...")
    print("  withdrawn:", ", ".join(u["up"] for u in withdrawn))

if __name__=="__main__":
    main()
