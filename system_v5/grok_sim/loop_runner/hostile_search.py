#!/usr/bin/env python3
"""hostile_search.py — many independent attacks per lego.

Implements §1B–§1D of .tmp/qit_engine_overall_math_exploration_20260513.md.

Architecture: strict gates + many independent hostile search armies.
For one math-named primitive (a "lego"), fan out N attacks across distinct
model pools. Each attack carries a distinct (attack_shape × MMM_language)
pair so two attacks on the same lego differ in formulation, not just author.

Pools available here:
  - grok     (gen_grok)
  - gemini   (gen_gemini)
  - codex    (gen_codex via codex CLI)

Sonnet/Opus subagents are run by the parent Claude session, not this script,
so they are not invoked from here.

Attack shapes (§1C):
  - direct                  (direct construction)
  - alternate_formulation   (same target, different math route)
  - graveyard_first         (build the negative controls first)
  - tool_heavy_proof        (lean on a specific tool: z3/cvc5/clifford/etc.)
  - minimal_toy             (smallest version that exercises the constraint)
  - naming_audit            (claim-ceiling and naming discipline review)
  - sub_lego_decomposition  (split the lego into independent sub-legos)

MMM attack languages (§1D):
  - Feynman    : mechanism, observable, minimal experiment
  - Hume       : what evidence would actually distinguish this?
  - Popper     : what would kill this fast?
  - Zhuangzi   : what alternate reading survives if this one dies?
  - Factory    : what bottleneck/queue move unlocks more attempts?
  - Strategy   : which attack order gives highest expected progress?
  - Systems    : what feedback loop is making us over-gate or under-search?
  - Orwell     : what is the plain math name that avoids jargon drift?

Each attack's prompt is shape × language × the §1A six-element ask
(X, C, M, ~_M, survivors, graveyard, claim ceiling).

Receipts: one directory per run under
  receipts/hostile_search/<primitive_key>_<ts>/
    manifest.json          — the plan, who fired what
    attack_<idx>_<pool>_<shape>_<mmm>.{py|md}  — raw response
    survivors.md           — passed the gate
    graveyard.md           — failed the gate, with cause
"""
import argparse
import ast
import concurrent.futures
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import multi_model_loop as mml
import propose_axis_lego as plego  # for PRIMITIVE_SPECS

RECEIPTS = HERE / "receipts" / "hostile_search"


# ---------- MMM attack-language fragments ----------

MMM_FRAMING = {
    "Feynman": (
        "Frame the attack in Feynman language: name the mechanism, the single "
        "observable that distinguishes the positive case from the negative, and "
        "the minimal experiment that would force a decision. No abstract nouns "
        "doing work they have not earned."
    ),
    "Hume": (
        "Frame the attack in Hume language: speak from what would actually be "
        "observed. Keep claims conditional where evidence does not warrant more. "
        "Name the evidence that would distinguish this lego's positive case from "
        "every neighbor — no leaps past what the probe would actually report."
    ),
    "Popper": (
        "Frame the attack falsifier-first: name the strongest live observation "
        "that would kill the lego, before naming any construction that would "
        "build it. The lego earns admission only by surviving the strongest "
        "kill attempt; classify the result as killed / open / survived."
    ),
    "Zhuangzi": (
        "Frame the attack as anti-collapse: name at least two readings of the "
        "lego that bounded work has not yet excluded, and refuse to pick one. "
        "Keep the live alternatives visible in the code's structure (e.g. two "
        "parallel constructions with side-by-side outputs)."
    ),
    "Factory": (
        "Frame the attack as bottleneck removal: name the single blocking step "
        "that prevents more attempts on this lego, and design the attack so it "
        "removes that bottleneck (e.g. a smaller toy, a faster tool, a cached "
        "intermediate). Throughput over elegance."
    ),
    "Strategy": (
        "Frame the attack at campaign scope: name the sequence in which "
        "sub-claims of this lego must be earned, and what would force a "
        "retreat. The attack's order of operations is itself the artifact."
    ),
    "Systems": (
        "Frame the attack as feedback-loop diagnosis: name the loop that is "
        "currently making this lego over-gated or under-searched, and design "
        "the attack so it changes which loop dominates."
    ),
    "Orwell": (
        "Frame the attack as naming discipline: every identifier in the code "
        "must be a literal math name. Cut every word that does not name a "
        "concrete operation, operator, or observable. If a name is jargon, "
        "replace it; do not explain why the jargon was bad."
    ),
}


# ---------- attack-shape fragments ----------

ATTACK_SHAPES = {
    "direct": (
        "Attack shape: DIRECT CONSTRUCTION. Build the lego as straightforwardly "
        "as possible — the most obvious admissible construction. Pass the "
        "positive test on the first try or RAISE."
    ),
    "alternate_formulation": (
        "Attack shape: ALTERNATE FORMULATION. The direct construction is "
        "already being attempted by another army. Take a deliberately different "
        "math route to the same target (e.g. spectral instead of operator, "
        "Lindblad instead of Kraus, sympy symbolic instead of numerical). The "
        "value of this attack is that it converges or fails to converge "
        "DIFFERENTLY from the direct attack."
    ),
    "graveyard_first": (
        "Attack shape: GRAVEYARD-FIRST. Build the negative controls FIRST, "
        "before the positive construction. The positive case only earns "
        "admission if it survives all named negative controls. The graveyard "
        "is the primary scientific output of this attack."
    ),
    "tool_heavy_proof": (
        "Attack shape: TOOL-HEAVY PROOF. Make a specific tool load-bearing "
        "(pick one: z3, cvc5, clifford, sympy, gudhi, toponetx). The attack "
        "should fail outright if that tool's contribution is removed."
    ),
    "minimal_toy": (
        "Attack shape: MINIMAL TOY. The smallest possible version that still "
        "exercises the constraint — single-qubit if the carrier allows, "
        "n_steps = 2 if a loop is involved, two-state probe family if M can "
        "be shrunk. The goal is fast iteration, not coverage."
    ),
    "naming_audit": (
        "Attack shape: NAMING / CLAIM-CEILING AUDIT. Do NOT build the lego. "
        "Instead, scan the spec for jargon, smuggled essences, and overclaim. "
        "Return a markdown document naming every identifier that should be "
        "renamed, every implicit ontology that should be made explicit, and "
        "the strictest claim ceiling the lego could honestly carry. Receipt "
        "is a .md file, not a .py file."
    ),
    "sub_lego_decomposition": (
        "Attack shape: SUB-LEGO DECOMPOSITION. Decompose the target lego into "
        "two or more independent sub-legos that could each be attacked "
        "separately. Return python code that contains stubs for each sub-lego "
        "(with positive + negative + boundary tests per stub) plus a top-level "
        "function that calls them in dependency order. Each sub-lego must be "
        "independently testable."
    ),
}


# ---------- the 7-attack lineup ----------

# Each entry: (attack_shape, mmm_language, model_pool)
# Cost-weighted: grok/gemini are cheaper than codex; sonnet subagent attacks
# would be cheapest but can't be spawned from inside this python subprocess
# (they need the parent Claude session via Agent tool). Codex is the most
# expensive pool here, so we use it sparingly or not at all in the default
# lineup. Audit subagents (which DO get spawned from the parent session)
# should be passed model="sonnet" to avoid defaulting to Opus.
DEFAULT_LINEUP = [
    ("direct",                  "Feynman",  "grok"),
    ("alternate_formulation",   "Zhuangzi", "gemini"),
    ("graveyard_first",         "Popper",   "grok"),
    ("tool_heavy_proof",        "Factory",  "gemini"),
    ("minimal_toy",             "Hume",     "grok"),
    ("naming_audit",            "Orwell",   "gemini"),
    ("sub_lego_decomposition",  "Strategy", "grok"),
]


EXTRA_CONSTRAINTS_BLOCK = ""  # populated by --inject-constraints

def build_attack_prompt(primitive_key: str, attack_shape: str, mmm_language: str) -> str:
    spec = plego.PRIMITIVE_SPECS[primitive_key]
    extras = ("\n\n## Round-N binding constraints (audit findings from prior round)\n\n"
              + EXTRA_CONSTRAINTS_BLOCK + "\n") if EXTRA_CONSTRAINTS_BLOCK else ""
    is_md = attack_shape == "naming_audit"
    output_block = (
        "Return ONE markdown document with sections: "
        "(1) jargon hits, (2) implicit ontology, (3) strictest honest claim "
        "ceiling, (4) recommended literal-math identifiers."
    ) if is_md else (
        "Return ONE python code block. Module must include: TOOL_MANIFEST + "
        "TOOL_INTEGRATION_DEPTH dicts; run_positive(); run_negative(); "
        "run_boundary(); main(). Qobjs use dims=[[2,2,2,2],[2,2,2,2]]."
    )
    return f"""You are one of seven independent attack armies on a 4-qubit-carrier
math primitive. The other six armies use different attack shapes and different
attack languages. You do not coordinate with them. Your receipt — survivor or
corpse — is independently useful.

## Lego

{spec["name"]}

## Math the lego must verify

{spec["math"]}

## Six-element ask (§1A nominalist object doctrine)

Your code (or document, for the naming-audit attack) must expose:
  - candidate set X
  - constraint set C
  - probe family M
  - distinguishability relation ~_M (or readout used)
  - survivor classes (positive-test pass)
  - killed neighbors / graveyard (negative-test corpses)
  - claim ceiling (one plain string)

## Tests required

- Positive: {spec["positive_test"]}
- Negative: {spec["negative_test"]}
- Boundary: {spec["boundary_test"]}

## Attack shape ({attack_shape})

{ATTACK_SHAPES[attack_shape]}

## Attack language ({mmm_language})

{MMM_FRAMING[mmm_language]}

## Constraints

- Status vocabulary: SURVIVED / KILLED / OPEN / NOT_YET_TESTED. Not PASS / FAIL.
- No hash distinctness, no classical-primality sieves, no synthetic returns,
  no closed-form values where integration is implied. If a test cannot be
  honestly satisfied, RAISE — do not fake.
- Banned identifiers: axis, Ax0..Ax6, engine, engine_stage, Engine A/B,
  Type 1/2, gstack, terrain, Ti/Te/Fi/Fe as function names, prime_resonance,
  hexagram, Carnot, Szilard, IGT, Jung.

## Standing wall constraints (24-audit aggregate)

Cumulative reviewer audits found the SAME failures across legos:
  trivial × 34, hardcoded × 22, decorative × 21, synthetic × 14, hash × 13,
  tautological × 4, vacuous × 4, shallow-negative × 3, identity-disguised × 3.
Survivor rate at reviewer gate: 1 of 24 (~4%). The walls below are the
reasons the other 23 failed. Your attack is rejected at the reviewer gate
if it commits any of these patterns:

1. TESTS DESIGNED TO PASS, NOT TO STRESS. Pick states where the constraint
   under test is NON-OBVIOUS. If the positive test passes by inspection
   (e.g. a Z-eigenstate input to a Z-dephasing channel), you are testing
   a trivially-separable subspace. Use a GHZ-type superposition, a
   non-eigenstate, or a generic-mixed input.

2. HARDCODED INDICES OR HARDCODED STRING RESULTS. Never `return "SURVIVED"`
   without computing a number and comparing it to a threshold. Never
   reference `gammas[1]` — name the value you want explicitly.

3. DECORATIVE TOOLS. If your `TOOL_MANIFEST` lists qutip and the only
   qutip call is `qt.Qobj(mat).full()` (round-trip wrap-and-discard), qutip
   is not load-bearing. Either invoke a real qutip path (qt.expect, qt.ptrace,
   qt.kraus_to_choi) or remove qutip from the manifest. A reviewer will
   read the imports against the manifest and flag any mismatch.

4. SYNTHETIC RETURNS. Negative controls that operate on hand-crafted
   subsets where the answer is guaranteed by construction (e.g. "drop one
   Kraus operator and verify the gap is now huge") test the construction,
   not the witness. Use the SAME state set for positive and negative;
   the negative must apply a real, narrow perturbation.

5. HASH-STYLE DISTINGUISHERS. Never use `% N`, `hash()`, or
   classical-primality multipliers to manufacture state distinctness.
   Distinctness must come from the algebraic structure of the operators.

6. SHALLOW NEGATIVES. Drop-one-Kraus, drop-25%-mass, flip-sign-of-add-term:
   these all produce O(1) gaps that any witness catches. The real test
   is near-threshold: perturb by (1 + 10·threshold) and confirm the
   witness catches it; perturb by (1 + 0.1·threshold) and confirm it
   honestly falls below.

7. PARALLEL READINGS SHARING ONE PROBE. If you keep two readings live
   (Zhuangzi anti-collapse), the readings must use INDEPENDENT probe
   functionals. Two generators feeding one witness is generator-divergence
   only — not real anti-collapse.

8. IDENTITY-CHANNEL DISGUISED AS NON-TRIVIAL. A negative control where
   R = U† inverts U at machine precision tests adjoint inversion, not
   the named property. A near-zero parameter that collapses the channel
   to identity is not a boundary — it's a trivial degenerate.

9. UNVERIFIED SELF-ADJOINTNESS / SYMMETRY ASSUMPTIONS. If you assume a
   channel ε is self-adjoint or that two parallel constructions are
   equivalent, ADD a numerical check. Don't assert by construction.

10. TOOL_MANIFEST WITH NON-STANDARD KEYS. Each entry must be a dict
    with keys `tried: bool, used: bool, reason: str` — not free-form
    strings, not custom keys like `"army"` or `"math_primitive"`.
    TOOL_INTEGRATION_DEPTH uses ONLY the tokens "load_bearing" /
    "supportive" / None — lowercase, no decorative descriptions.

## Negative-control discipline (audit-mapped failure mode)

A prior round of five audits across two legos found that 5/5 survivor attacks
were killed at the reviewer gate by SHALLOW OR TAUTOLOGICAL negative controls.
The light gate and the runs gate cannot catch this — only reviewer audit can.
Your `run_negative()` is wrong if it does ANY of the following:

- Computes `td(X, X)` where the two arguments are the SAME expression. The
  trace distance from a state to itself is zero by Python, not by physics.
- Subtracts an expression from itself and reports the difference as the
  negative test result.
- Runs the negative case on an input that lies in the fixed subspace of the
  channel under test (e.g. `|0...0⟩⟨0...0|` for a phase-flip channel — the
  channel acts as identity there, so order has no effect).
- Uses a degenerate parameter value that collapses the construction to
  identity (e.g. dissipator strength = 0, loop angle = 0, identity unitary).
- Re-runs the positive construction with one trivially-different label.

What a HONEST negative control looks like:

- For an order/non-commutation test: use a pair of channels that genuinely
  COMMUTE (e.g. two dephasing channels in the same basis, or two Z-rotations)
  and confirm the order observable is zero. Distinct expression, different
  physics, observed-by-construction-to-be-the-control case.
- For a completeness/CPTP test: a deliberately-perturbed Kraus set
  (e.g. scale one `K_i` by `1 + 1e-6`) that should still be CLOSE but caught
  by a tight tolerance.
- For a probe-equivalence test: a pair of density matrices that DIFFER in a
  probe-detectable way (separate physics, not the same input twice).

Boundary tests must exercise a LIMIT, not collapse the construction to
identity. If your boundary case sets the only nontrivial parameter to zero,
it is not a boundary — it is a trivial degenerate.

## Known math hallucinations (graveyard-mapped)

A prior round found two independent attacks using `tr(ρ)²` and claiming it
was purity. `tr(ρ) ≡ 1` for any density matrix, so `tr(ρ)² ≡ 1` is constant
and useless. Purity is `tr(ρ²) = sum_i p_i²`. The two are NOT the same.

If you write a purity check, it MUST be one of:
  - `(rho * rho).tr()`            (qutip)
  - `np.trace(rho_np @ rho_np)`   (numpy, real part)
NEVER `tr(rho)**2`.

If your `main()` prints "KILLED" because your own positive/negative test
failed, that file is a corpse — do not return it. Fix the math, or RAISE
honestly, instead of reporting completion.

## qutip API discipline (graveyard-mapped failure mode)

A prior hostile-search round had three of seven attacks killed by qutip API
hallucinations: `qt.norm` (does not exist), `choi_to_kraus` (does not exist
at the module level in this qutip version), and a wrong norm flag.

Stay inside this safe set of qutip APIs unless you have verified the symbol
on the installed version:
  - State construction: `qt.basis`, `qt.ket2dm`, `qt.tensor`, `qt.Qobj`
  - Operators: `qt.qeye`, `qt.sigmax`, `qt.sigmay`, `qt.sigmaz`, `qt.sigmap`, `qt.sigmam`
  - Algebra: `op.dag()`, `op * op2`, `op + op2`, `op.tr()`, `op.eigenstates()`
  - Norms: `(op).norm()` returns trace norm by default;
            for Frobenius use `np.linalg.norm(op.full(), 'fro')`
  - Partial trace: `rho.ptrace([keep_indices])`
  - Channel: roll your own ρ ↦ Σ K_i ρ K_i† with numpy + qutip; do NOT rely
    on `kraus_to_choi` / `choi_to_kraus` existing.

If unsure, compute with numpy on `op.full()` and wrap the result back in
`qt.Qobj(..., dims=[[2,2,2,2],[2,2,2,2]])`. A working numpy fallback beats
a hallucinated qutip call.

## Output

{output_block}
{extras}"""


# ---------- pool dispatchers ----------

def fire_grok(prompt: str) -> str:
    return mml.gen_grok(prompt)

def fire_gemini(prompt: str) -> str:
    return mml.gen_gemini(prompt)

def fire_codex(prompt: str) -> str:
    return mml.gen_codex(prompt)

POOL_DISPATCH = {"grok": fire_grok, "gemini": fire_gemini, "codex": fire_codex}


# ---------- gate ----------

def gate_check(text: str, is_md_attack: bool, spec: dict) -> tuple[bool, str]:
    """Return (passed, reason). The gate screens:
      (a) empty / malformed receipts
      (b) banned-identifier contamination
      (c) missing required functions
      (d) nominalist-schema absence — the lego MUST expose X, C, M, ~_M,
          survivors, graveyard, claim ceiling (string-level check, not
          semantic). Doctrine binding is on the schema being present.
    The semantic check (do these fields actually mean something) is the
    reviewer gate, fired later."""
    if not text or len(text) < 200:
        return False, "empty or trivially short response"
    if is_md_attack:
        if "claim ceiling" not in text.lower():
            return False, "naming-audit attack returned no claim-ceiling section"
        return True, "naming-audit md present"
    # python attack: must extract code that parses
    code = mml.extract_code(text)
    if not code:
        return False, "no python code block found"
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"syntax error: {e}"
    # banned-token scan on the code body
    banned = ("Ax0", "Ax1", "Ax2", "Ax3", "Ax4", "Ax5", "Ax6",
              "engine_stage", "Engine A", "Engine B", "Type 1", "Type 2",
              "gstack", "prime_resonance", "hexagram", "Carnot", "Szilard",
              "IGT", "Jung", "MBTI")
    hits = [t for t in banned if t in code]
    if hits:
        return False, f"banned identifiers in code: {hits[:5]}"
    # required functions
    required = ("run_positive", "run_negative", "run_boundary", "main")
    missing = [f for f in required if f"def {f}" not in code]
    if missing:
        return False, f"missing required functions: {missing}"
    # nominalist-schema string-level check: each of the six elements must
    # appear by name somewhere in the file (in a docstring, comment, or
    # variable name). Absent fields fail the gate. This is a SHAPE check,
    # not a semantic one — semantic fitness comes later from the reviewer.
    schema_terms = [
        ("candidate set",       ("candidate_set", "candidate set", "candidate configuration")),
        ("constraint set",      ("constraint_set", "constraint set")),
        ("probe family",        ("probe_family", "probe family", "M_ops")),
        ("distinguishability",  ("distinguishability", "~_M", "indistinguish")),
        ("survivor",            ("survivor", "survived")),
        ("graveyard",           ("graveyard", "killed neighbor", "killed_neighbor", "corpse")),
        ("claim ceiling",       ("claim_ceiling", "claim ceiling")),
    ]
    missing_schema = [name for name, tokens in schema_terms
                      if not any(t.lower() in code.lower() for t in tokens)]
    if missing_schema:
        return False, f"nominalist schema fields missing from file: {missing_schema}"
    return True, "passed light gate (parse + functions + nominalist schema present)"


# ---------- runner ----------

def run_one(primitive_key: str, idx: int, attack_shape: str, mmm_language: str,
            pool: str, out_dir: Path, spec: dict) -> dict:
    is_md = attack_shape == "naming_audit"
    ext = "md" if is_md else "py"
    raw_path = out_dir / f"attack_{idx:02d}_{pool}_{attack_shape}_{mmm_language}.{ext}"
    prompt = build_attack_prompt(primitive_key, attack_shape, mmm_language)
    t0 = time.time()
    err = None
    text = ""
    try:
        text = POOL_DISPATCH[pool](prompt)
    except Exception as e:
        err = f"{type(e).__name__}: {str(e)[:200]}"
    dt = time.time() - t0
    if text:
        if is_md:
            raw_path.write_text(text)
        else:
            code = mml.extract_code(text) or text
            raw_path.write_text(code)
    passed, reason = (False, err) if err else gate_check(text, is_md, spec)
    return {
        "idx": idx, "pool": pool, "attack_shape": attack_shape,
        "mmm_language": mmm_language, "attack_path": str(raw_path.name),
        "wall_seconds": round(dt, 1), "passed_gate": passed,
        "gate_reason": reason, "response_chars": len(text),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("primitive_key", help="key into propose_axis_lego.PRIMITIVE_SPECS")
    ap.add_argument("--max-parallel", type=int, default=3,
                    help="max simultaneous attacks (model pools are rate-limited)")
    ap.add_argument("--inject-constraints", type=Path, default=None,
                    help="path to a markdown file whose contents are injected into every attack prompt as binding round-N constraints (e.g. audit findings from a prior round)")
    args = ap.parse_args()
    if args.inject_constraints and args.inject_constraints.exists():
        global EXTRA_CONSTRAINTS_BLOCK
        EXTRA_CONSTRAINTS_BLOCK = args.inject_constraints.read_text()
        print(f"injected {len(EXTRA_CONSTRAINTS_BLOCK)} chars of round-N constraints from {args.inject_constraints.name}")

    if args.primitive_key not in plego.PRIMITIVE_SPECS:
        print(f"unknown primitive '{args.primitive_key}'")
        print(f"available: {sorted(plego.PRIMITIVE_SPECS)}")
        sys.exit(1)
    spec = plego.PRIMITIVE_SPECS[args.primitive_key]

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = RECEIPTS / f"{args.primitive_key}_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nHostile-search on lego: {spec['name']}")
    print(f"Receipts dir: {out_dir}")
    print(f"Plan: {len(DEFAULT_LINEUP)} independent attacks across pools "
          f"{sorted(set(p for _,_,p in DEFAULT_LINEUP))}\n")

    receipts = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_parallel) as ex:
        futures = {
            ex.submit(run_one, args.primitive_key, i, shape, mmm, pool, out_dir, spec): (i, shape, mmm, pool)
            for i, (shape, mmm, pool) in enumerate(DEFAULT_LINEUP)
        }
        for fut in concurrent.futures.as_completed(futures):
            r = fut.result()
            receipts.append(r)
            tag = "✓" if r["passed_gate"] else "✗"
            print(f"  {tag} attack_{r['idx']:02d} {r['pool']:7s} "
                  f"{r['attack_shape']:24s} {r['mmm_language']:9s} "
                  f"{r['wall_seconds']:5.1f}s · {r['gate_reason']}")

    receipts.sort(key=lambda r: r["idx"])
    manifest = {
        "primitive_key": args.primitive_key,
        "primitive_name": spec["name"],
        "timestamp_utc": ts,
        "lineup": DEFAULT_LINEUP,
        "receipts": receipts,
        "doctrine_ref": ".tmp/qit_engine_overall_math_exploration_20260513.md §1A-§1D",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    survivors = [r for r in receipts if r["passed_gate"]]
    corpses = [r for r in receipts if not r["passed_gate"]]

    surv_md = [f"# Survivors — {spec['name']}", "",
               f"Run: {ts}  ·  {len(survivors)}/{len(receipts)} attacks survived light gate.",
               ""]
    for r in survivors:
        surv_md.append(f"- **attack_{r['idx']:02d}** · {r['pool']} · "
                       f"{r['attack_shape']} · {r['mmm_language']} → "
                       f"`{r['attack_path']}` ({r['response_chars']} chars, {r['wall_seconds']}s)")
    (out_dir / "survivors.md").write_text("\n".join(surv_md) + "\n")

    grave_md = [f"# Graveyard — {spec['name']}", "",
                f"Run: {ts}  ·  {len(corpses)}/{len(receipts)} attacks killed at the gate.",
                "",
                "A failed attack is useful: it maps the wall. Each corpse names its cause of death."]
    grave_md.append("")
    for r in corpses:
        grave_md.append(f"- **attack_{r['idx']:02d}** · {r['pool']} · "
                        f"{r['attack_shape']} · {r['mmm_language']} → "
                        f"`{r['attack_path']}`  \n  cause: *{r['gate_reason']}*")
    (out_dir / "graveyard.md").write_text("\n".join(grave_md) + "\n")

    print(f"\nDone. survivors={len(survivors)} corpses={len(corpses)}")
    print(f"  {out_dir}/manifest.json")
    print(f"  {out_dir}/survivors.md")
    print(f"  {out_dir}/graveyard.md")


if __name__ == "__main__":
    main()
