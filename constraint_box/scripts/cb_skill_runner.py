#!/usr/bin/env python3
"""cb_skill_runner — run ARBITRARY skills as skills, generalised from
cb_skill_premortem.py.

cb_skill_premortem.py runs exactly one skill (premortem), by hand: its
procedure and its output contract are both hard-coded into the script.
About 110 skills exist across four roots and one has ever been run.

This script generalises the pattern:

  1. LOCATE   find <name>/SKILL.md (or a path) across all four roots:
                ~/.codex/skills, ~/.agents/skills, ~/.claude/skills,
                ~/wiki/wizard/packet-v4-3-current/**/SKILL.md
  2. PARSE    read frontmatter, the declared PROCEDURE (a numbered
              workflow/steps/method section) and the declared OUTPUT
              SHAPE (a yaml/json return-fields block, a named list of
              report sections, or a set of declared output filenames)
              from the SKILL.md TEXT ITSELF — never from a linked
              reference file the SKILL.md merely points at. A skill
              that only points elsewhere for its shape is, from this
              runner's standpoint, a skill with no inline shape.
  3. EXECUTE  each declared procedure step becomes a NESTED COUNCIL:
              >=5 members, different salience slices, different free
              lanes, answering the SAME step under different framing
              so they can genuinely disagree. Steps run independently
              in parallel, exactly as cb_wave_decision's routes/children
              do; a single compiler then reads all step councils and
              produces ONE compiled artifact.
  4. GATE     the compiled artifact against the SKILL's OWN declared
              shape — never a shape this script invented. member-floor
              first (a starved council is refused, not silently
              accepted), then shape conformance.
  5. RECEIPT  one JSON receipt naming the skill, its source root, its
              declared shape, and the gate verdict. promotion_allowed
              is always false.

If a SKILL.md declares no checkable output shape inline, the runner
REFUSES with reason "skill declares no gateable output shape" — a
skill CB cannot gate is a skill CB cannot admit (owner ruling A1: CB
gates the domain answers fall in, not their truth).

This runner exercises a skill's PROCEDURE SHAPE and OUTPUT SHAPE
against a generic, self-referential task by default (--task overrides
it). It does not attempt to supply the bespoke domain input a given
skill would normally need (a plan for premortem, a repo for
codex-autoresearch, ...) — that is out of scope for a shape gate.

  cb_skill_runner.py --list                       # inventory, free
  cb_skill_runner.py --skill premortem --dry-run   # structure, free
  cb_skill_runner.py --skill premortem             # dispatches, costs tokens

promotion_allowed=false.
"""
from __future__ import annotations
import argparse, difflib, hashlib, json, re, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
sys.path.insert(0, str(REPO / "constraint_box" / "scripts"))
from cb_multi_provider import provider_diversity, family_of
from cb_strategy_memory import StrategyMemory
from cb_wave_decision import DEFAULT_LANES, COMPILE_LANE, SLICES, \
    MEMBER_FLOOR, run_jobs, collapse_check

try:
    import yaml
except ImportError:                             # pragma: no cover
    yaml = None

# ------------------------------------------------------------------ roots
ROOTS = {
    "codex":         Path.home() / ".codex" / "skills",
    "agents":        Path.home() / ".agents" / "skills",
    "claude":        Path.home() / ".claude" / "skills",
    "wizard-packet": Path.home() / "wiki" / "wizard" / "packet-v4-3-current",
}
ROOT_ORDER = ["codex", "agents", "claude", "wizard-packet"]

RECEIPTS = REPO / "constraint_box" / "receipts"

# ------------------------------------------------------------------ discovery
def find_skill_files(root_path: Path):
    if not root_path.is_dir():
        return []
    return sorted(p for p in root_path.rglob("*")
                  if p.is_file() and p.name.lower() == "skill.md")


def skill_id_for(root_key: str, path: Path, root_path: Path) -> str:
    """Stable id: basename for the three flat roots; a disambiguated
    relative path for the nested wizard packet (council-members/* etc)."""
    if root_key != "wizard-packet":
        return path.parent.name
    rel = str(path.parent.relative_to(root_path)).replace("\\", "/")
    return rel[len("skills/"):] if rel.startswith("skills/") else rel


def discover_all_skills() -> list:
    """Every SKILL.md across the four roots, parsed once. Cheap, no dispatch."""
    out = []
    for rk in ROOT_ORDER:
        rp = ROOTS[rk]
        for p in find_skill_files(rp):
            raw = p.read_bytes()
            text = raw.decode(errors="ignore")
            fm, body = parse_frontmatter(text)
            proc, proc_heading = extract_procedure(body)
            shape = detect_output_shape(body)
            out.append({
                "id": skill_id_for(rk, p, rp), "root": rk, "path": str(p),
                "sha256": hashlib.sha256(raw).hexdigest()[:16],
                "bytes": len(raw),
                "frontmatter": fm,
                "name": fm.get("name") or p.parent.name,
                "description": str(fm.get("description") or "")[:600],
                "procedure": proc, "procedure_heading": proc_heading,
                "shape": shape,
            })
    return out


def locate_skill(query: str, root_filter: str = ""):
    """Exact match only — id, basename, or frontmatter name. No fuzzy
    substitution: the harness does not guess which skill a human meant."""
    p = Path(query)
    if p.name.lower() == "skill.md" and p.is_file():
        return [_record_for_path(p)]
    if p.is_dir() and (p / "SKILL.md").is_file():
        return [_record_for_path(p / "SKILL.md")]

    q = query.lower()
    all_skills = discover_all_skills()
    if root_filter:
        all_skills = [s for s in all_skills if s["root"] == root_filter]
    hits = [s for s in all_skills
            if s["id"].lower() == q or s["id"].split("/")[-1].lower() == q
            or str(s["frontmatter"].get("name", "")).lower() == q]
    if hits:
        order = {r: i for i, r in enumerate(ROOT_ORDER)}
        hits.sort(key=lambda s: order.get(s["root"], 99))
        return hits
    return []


def _record_for_path(path: Path):
    """A record for a skill given directly as a path, outside the four
    roots or not resolvable through them by name."""
    raw = path.read_bytes()
    text = raw.decode(errors="ignore")
    fm, body = parse_frontmatter(text)
    proc, proc_heading = extract_procedure(body)
    shape = detect_output_shape(body)
    root = "path"
    for rk, rp in ROOTS.items():
        try:
            path.relative_to(rp)
            root = rk
        except ValueError:
            continue
    return {"id": path.parent.name, "root": root, "path": str(path),
            "sha256": hashlib.sha256(raw).hexdigest()[:16], "bytes": len(raw),
            "frontmatter": fm, "name": fm.get("name") or path.parent.name,
            "description": str(fm.get("description") or "")[:600],
            "procedure": proc, "procedure_heading": proc_heading,
            "shape": shape}


# ------------------------------------------------------------------ parsing
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.S)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.M)
FENCE_RE = re.compile(r"```(\w*)\n(.*?)```", re.S)
SUBHEAD_NUM_RE = re.compile(r"^#{2,6}\s*(\d+)\.\s*(.+)$", re.M)
LIST_NUM_RE = re.compile(r"^[ \t]*(\d+)[.)][ \t]+(.+)$", re.M)
FILENAME_TOKEN_RE = re.compile(
    r"[A-Za-z0-9][\w\-\[\]{}]*\.(?:html|md|json|py|csv|txt|ya?ml)\b")
PRODUCE_CUE_RE = re.compile(
    r"(?:produces?|creates?|writes?|saves?|generates?)\s*:?\s*$", re.I | re.M)
PRE_CUE_RE = re.compile(
    r"return\s+(?:only|fields|json)\b|output\s+(?:shape|format|fields)\b|"
    r"(?:output|return)\s*(?:shape|format|schema)\s*:", re.I)
SECTIONS_CUE_RE = re.compile(
    r"with\s+(?:exactly\s+)?these\s+sections|following\s+sections|"
    r"these\s+\d+\s+sections", re.I)
BOLD_ITEM_RE = re.compile(r"^[ \t]*[-\d.)]+[ \t]*\*\*(.+?)\*\*", re.M)
PLAIN_NUM_ITEM_RE = re.compile(r"^[ \t]*\d+[.)][ \t]+(.+)$", re.M)

PROCEDURE_HEADINGS = ("workflow", "steps", "method", "procedure", "process",
                      "core loop", "when activated", "boot order", "run path")
OUTPUT_HEADING_WORDS = ("output", "return field", "report file")


def parse_frontmatter(text: str):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    body = text[m.end():]
    if yaml is None:
        return {}, body
    try:
        fm = yaml.safe_load(m.group(1))
        return (fm if isinstance(fm, dict) else {}), body
    except Exception:
        return {}, body


def _mask_fences(body: str) -> str:
    """Blank fenced code-block INTERIORS (comments, example numbered
    lists, example JSON) to spaces, same length, same offsets. Without
    this, a bash `# comment` or a `1. like this` inside a ```bash example
    is indistinguishable from real markdown structure — a bash comment
    that happens to contain the word "output" would otherwise be read
    as a heading. Fence markers/language tags are left alone; only the
    content between them is blanked."""
    out = list(body)
    for m in FENCE_RE.finditer(body):
        s, e = m.span(2)
        for i in range(s, e):
            if out[i] != "\n":
                out[i] = " "
    return "".join(out)


def _heading_index(body: str):
    masked = _mask_fences(body)
    return [(m.start(), m.group(2).strip()) for m in HEADING_RE.finditer(masked)]


def _heading_at(heads, pos: int):
    title = None
    for hstart, htitle in heads:
        if hstart <= pos:
            title = htitle
        else:
            break
    return title


def _is_output_heading(title: str) -> bool:
    t = (title or "").lower()
    return any(w in t for w in OUTPUT_HEADING_WORDS)


def _ordered_items(text: str):
    subheads = SUBHEAD_NUM_RE.findall(text)
    if subheads:
        return [t.strip() for _, t in
                sorted(subheads, key=lambda x: int(x[0]))]
    items = LIST_NUM_RE.findall(text)
    if items:
        return [t.strip() for _, t in items]
    return []


def extract_procedure(body: str):
    """The first heading whose title names a procedure convention. Its
    numbered sub-headings or numbered list items are the declared steps."""
    heads = _heading_index(body)
    for i, (start, title) in enumerate(heads):
        if not any(a in title.lower() for a in PROCEDURE_HEADINGS):
            continue
        end = len(body)
        # section runs to the next heading at the SAME markdown level or
        # shallower (a deeper subheading stays inside this section).
        m = HEADING_RE.match(body, start)
        this_level = len(m.group(1)) if m else 2
        for start2, title2 in heads[i+1:]:
            m2 = HEADING_RE.match(body, start2)
            lvl2 = len(m2.group(1)) if m2 else 99
            if lvl2 <= this_level:
                end = start2
                break
        section_body = _mask_fences(body[start:end])
        steps = _ordered_items(section_body)
        if steps:
            return steps, title
    return [], None


def _extract_fields(block: str, lang: str):
    lang = lang.lower()
    try:
        if lang in ("yaml", "yml", ""):
            data = yaml.safe_load(block) if yaml else None
        elif lang == "json":
            data = json.loads(block)
        else:
            return []
    except Exception:
        return []
    return list(data.keys()) if isinstance(data, dict) and data else []


def _sections_near(body: str, pos: int, window: int = 1500):
    chunk = body[pos:pos + window]
    bolds = BOLD_ITEM_RE.findall(chunk)
    if bolds:
        return [b.strip() for b in bolds]
    plains = PLAIN_NUM_ITEM_RE.findall(chunk)
    out = []
    for p in plains:
        head = re.split(r"\s+-\s+|:", p, maxsplit=1)[0].strip(" *")
        if head:
            out.append(head[:70])
    return out


def detect_output_shape(body: str) -> dict:
    """Declared output shape, read ONLY from inline SKILL.md content:
      fields    - keys of a yaml/json block under an output-labelled
                  heading, or one cued by "return only/fields/json" text
      artifacts - filename-shaped tokens under an output-labelled
                  heading, or cued by "produces/creates/writes/saves:"
      sections  - named report sections cued by "with these sections"
    A block that is yaml/json but sits under an unrelated heading with
    no output cue (e.g. a runtime config schema) is NOT counted — that
    would fabricate a shape the skill did not declare as its output."""
    heads = _heading_index(body)
    masked = _mask_fences(body)
    fields, artifacts, sections, declared_in = [], [], [], []

    for m in FENCE_RE.finditer(body):
        lang = m.group(1)
        block = m.group(2)
        title = _heading_at(heads, m.start()) or ""
        # the cue window is read from the MASKED body: a preceding fenced
        # example (a bash comment, a sample line) must never be mistaken
        # for the prose cue that introduces this block.
        pre = masked[max(0, m.start() - 220):m.start()]
        out_heading = _is_output_heading(title)
        cue_pre = bool(PRE_CUE_RE.search(pre))
        produce_pre = bool(PRODUCE_CUE_RE.search(pre))

        if lang.lower() in ("yaml", "yml", "json") and (out_heading or cue_pre):
            f = _extract_fields(block, lang)
            if f:
                fields += [x for x in f if x not in fields]
                declared_in.append(f"fields@{title or 'body'}")

        if out_heading or produce_pre:
            toks = FILENAME_TOKEN_RE.findall(block)
            if toks:
                artifacts += [t for t in toks if t not in artifacts]
                declared_in.append(f"artifacts@{title or 'body'}")

    for m in SECTIONS_CUE_RE.finditer(masked):
        for s in _sections_near(masked, m.end()):
            if s and s not in sections:
                sections.append(s)
                declared_in.append("sections@cue")

    return {"fields": fields, "artifacts": artifacts, "sections": sections,
            "declared_in": sorted(set(declared_in)),
            "gateable": bool(fields or artifacts or sections)}


def shape_kind(shape: dict) -> str:
    if shape["fields"]:
        return "fields"
    if shape["sections"]:
        return "sections"
    if shape["artifacts"]:
        return "artifacts_only"
    return "none"


def shape_hint_text(shape: dict, kind: str) -> str:
    if kind == "fields":
        return f"DECLARED OUTPUT FIELDS (this skill's own SKILL.md): {shape['fields']}"
    if kind == "sections":
        return f"DECLARED OUTPUT SECTIONS (this skill's own SKILL.md): {shape['sections']}"
    if kind == "artifacts_only":
        return (f"DECLARED OUTPUT FILES (this skill's own SKILL.md): "
                f"{shape['artifacts']} — CB does not write files; this run "
                f"produces text evidence toward them only.")
    return "This skill declares no gateable output shape."


# ------------------------------------------------------------------ execution
def build_step_jobs(skill: dict, steps: list, shape: dict, kind: str,
                    task: str, members: list, lanes: list, sm: StrategyMemory):
    jobs = []
    hint = shape_hint_text(shape, kind)
    for si, step in enumerate(steps, start=1):
        for n, sl in enumerate(members):
            jobs.append({
                "id": f"step{si}|{sl}", "step_index": si, "step_text": step,
                "lane": lanes[(si * len(members) + n) % len(lanes)],
                "prompt": (
                    f"{sm.preamble()}\n\n"
                    f"=== SALIENCE SLICE: {sl} ===\n{SLICES[sl]}\n\n"
                    f"SKILL UNDER RUN: {skill['name']}\n"
                    f"SKILL DESCRIPTION: {skill['description'][:400]}\n\n"
                    "You are one member of a council carrying out ONE "
                    f"declared procedure step of this skill.\n"
                    f"STEP {si} OF {len(steps)}: {step}\n\n"
                    f"{hint}\n\n"
                    f"TASK CONTEXT:\n{task}\n\n"
                    "Carry out this step now for that task context. State "
                    "only what this step produces. Under 120 words.")})
    return jobs


def build_compile_job(skill: dict, steps: list, shape: dict, kind: str,
                      task: str, councils: dict, sm: StrategyMemory):
    body = "\n".join(
        f"[step {si} / {sl}] {' '.join(a.split())[:220]}"
        for si in councils for sl, a in councils[si]["answers"].items())
    if kind == "fields":
        want = json.dumps({f: "<derived from the step councils>"
                           for f in shape["fields"]})
        instr = ("Compile these into ONE JSON object with EXACTLY these "
                f"keys, no others:\n{want}")
    elif kind == "sections":
        instr = ("Compile these into ONE document with EXACTLY these "
                f"headings, each followed by real content drawn from the "
                f"step councils:\n{shape['sections']}")
    else:
        instr = ("This skill's declared output is a set of files this "
                 "runner will not write. Compile the step councils into a "
                 "short text summary of what those files would contain.")
    return {"id": "compile", "lane": COMPILE_LANE, "prompt": (
        f"{sm.preamble()}\n\nYou are the OUTPUT COMPILER for the skill "
        f"'{skill['name']}'.\nIts procedure step councils returned:\n{body}\n\n"
        f"TASK CONTEXT:\n{task}\n\n{instr}")}


# ------------------------------------------------------------------ THE GATE
def gate_artifact(kind: str, shape: dict, compiled_text: str,
                  councils: dict, floor: int = MEMBER_FLOOR) -> dict:
    """Deterministic. Admits or refuses the compiled artifact against the
    skill's OWN declared shape. Member floor is checked before shape,
    exactly as cb_wave_decision does — a starved council cannot be
    hidden behind a well-shaped compilation."""
    reasons = []
    for si, c in councils.items():
        if len(c["answers"]) < floor:
            reasons.append(f"step {si}: {len(c['answers'])} live members, "
                           f"below the conformance floor of {floor}")

    if kind == "artifacts_only":
        reasons.append(
            f"declared output is unwritten files ({', '.join(shape['artifacts'][:4])}"
            f"{'...' if len(shape['artifacts']) > 4 else ''}); CB does not "
            "write files and cannot verify artifacts it did not produce")
        return {"admitted": False, "reasons": reasons, "compiled": None}

    if kind == "fields":
        i, j = compiled_text.find("{"), compiled_text.rfind("}")
        try:
            pkt = json.loads(compiled_text[i:j + 1])
        except Exception:
            pkt = None
        if not isinstance(pkt, dict):
            reasons.append("compilation is not a JSON object")
            return {"admitted": False, "reasons": reasons, "compiled": pkt}
        for f in shape["fields"]:
            if f not in pkt:
                reasons.append(f"missing declared output field: {f}")
                continue
            v = pkt[f]
            if isinstance(v, str) and len(v.strip()) < 8:
                reasons.append(f"{f}: shorter than 8 chars")
            elif isinstance(v, list) and len(v) < 1:
                reasons.append(f"{f}: empty list")
        return {"admitted": not reasons, "reasons": reasons, "compiled": pkt}

    if kind == "sections":
        low = compiled_text.lower()
        for s in shape["sections"]:
            if s.lower() not in low:
                reasons.append(f"missing declared section: {s}")
        if len(compiled_text.split()) < 40:
            reasons.append("compiled text too short to plausibly cover the "
                           "declared sections")
        return {"admitted": not reasons, "reasons": reasons,
                "compiled": compiled_text}

    reasons.append("no declared output shape kind resolved")
    return {"admitted": False, "reasons": reasons, "compiled": None}


# ------------------------------------------------------------------ commands
def cmd_list() -> int:
    skills = discover_all_skills()
    print(f"SKILL INVENTORY — {len(skills)} SKILL.md found across "
          f"{len(ROOTS)} roots\n")
    by_root = {}
    for s in skills:
        by_root.setdefault(s["root"], []).append(s)
    for rk in ROOT_ORDER:
        rows = sorted(by_root.get(rk, []), key=lambda s: s["id"])
        print(f"{rk}  ({ROOTS[rk]})  {len(rows)} skills")
        for s in rows:
            kind = shape_kind(s["shape"])
            gate = "gateable:" + kind if s["shape"]["gateable"] else "NOT gateable"
            nsteps = len(s["procedure"])
            print(f"   {s['id']:<32} steps={nsteps:<3} {gate}")
        print()
    gateable = sum(1 for s in skills if s["shape"]["gateable"])
    print(f"TOTAL {len(skills)}  gateable {gateable}  "
          f"not gateable {len(skills) - gateable}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true",
                    help="enumerate every skill across the four roots")
    ap.add_argument("--skill", default="", help="skill name or path")
    ap.add_argument("--root", default="", choices=[""] + ROOT_ORDER)
    ap.add_argument("--task", default=(
        "Use this SKILL.md's own text as the input material and run the "
        "skill's declared procedure against itself as a bounded, generic, "
        "self-referential check."))
    ap.add_argument("--members", type=int, default=5,
                    help="council seats per procedure step; floor is 5")
    ap.add_argument("--dry-run", action="store_true",
                    help="locate, parse, and gate the SHAPE only; no dispatch")
    ap.add_argument("--lanes", default=",".join(DEFAULT_LANES))
    ap.add_argument("--conc", type=int, default=8)
    a = ap.parse_args()
    t0 = time.time()

    if a.list:
        return cmd_list()

    if not a.skill:
        print("REFUSED: --skill <name-or-path> or --list is required")
        return 2

    lanes = [x.strip() for x in a.lanes.split(",") if x.strip()]
    if a.members < 5:
        print(f"REFUSED: --members {a.members} is below the conformance "
              f"floor of 5.")
        return 2
    members = list(SLICES)[:a.members]

    matches = locate_skill(a.skill, a.root)
    ts = time.strftime("%Y%m%dT%H%M%SZ")
    if not matches:
        near = difflib.get_close_matches(
            a.skill, [s["id"] for s in discover_all_skills()], n=5)
        print(f"REFUSED: skill '{a.skill}' not found in any of the four "
              f"roots ({', '.join(ROOT_ORDER)}).")
        if near:
            print(f"   did you mean: {near}")
        rundir = RECEIPTS / f"skillrun_NOTFOUND_{ts}"
        rundir.mkdir(parents=True, exist_ok=True)
        (rundir / "SKILL_RUN_RECEIPT.json").write_text(json.dumps({
            "schema": "cb.skill-run.v1", "requested": a.skill,
            "found": False, "near_matches": near, "dispatched": False,
            "gate": {"admitted": False,
                     "reasons": [f"skill '{a.skill}' not found"]},
            "promotion_allowed": False,
            "claim_ceiling": "skill discovery only; nothing ran"},
            indent=1, sort_keys=True))
        print(f"RECEIPT {rundir.name}/SKILL_RUN_RECEIPT.json")
        return 2

    skill = matches[0]
    others = matches[1:]
    raw_sha = skill["sha256"]
    print(f"SKILL   {skill['name']}  (id={skill['id']}, root={skill['root']})")
    print(f"   path {skill['path']}")
    print(f"   sha256[:16] {raw_sha}   {skill['bytes']} bytes")
    if others:
        print(f"   also present in: "
              f"{[(m['root'], m['id']) for m in others]}")
    print()

    print("PROCEDURE")
    if skill["procedure"]:
        print(f"   found under heading '{skill['procedure_heading']}', "
              f"{len(skill['procedure'])} step(s):")
        for i, st in enumerate(skill["procedure"], 1):
            print(f"      {i}. {st[:100]}")
    else:
        print("   NONE FOUND — no workflow/steps/method/procedure heading "
              "with numbered items in this SKILL.md; falling back to a "
              "single self-referential step.")
    print()

    shape = skill["shape"]
    kind = shape_kind(shape)
    print("OUTPUT SHAPE (parsed from SKILL.md text only, not references)")
    print(f"   gateable: {shape['gateable']}   kind: {kind}")
    if shape["fields"]:
        print(f"   fields    {shape['fields']}")
    if shape["sections"]:
        print(f"   sections  {shape['sections']}")
    if shape["artifacts"]:
        print(f"   artifacts {shape['artifacts']}")
    if shape["declared_in"]:
        print(f"   declared in: {shape['declared_in']}")
    print()

    steps = skill["procedure"] or [
        "Execute the skill's declared workflow as a whole (no individually "
        "numbered procedure steps were found in its SKILL.md)."]
    n_children = len(steps)
    n_jobs = n_children * len(members)

    rundir = RECEIPTS / f"skillrun_{skill['id'].replace('/', '_')}_{ts}"

    if not shape["gateable"]:
        print("GATE  REFUSED: skill declares no gateable output shape")
        print("   reason: no yaml/json return-fields block under an "
              "output-labelled heading or return/shape cue, no declared "
              "report sections, and no declared output filenames were "
              "found in this SKILL.md's own text.")
        if a.dry_run:
            rundir.mkdir(parents=True, exist_ok=True)
            (rundir / "SKILL_RUN_RECEIPT.json").write_text(json.dumps({
                "schema": "cb.skill-run.v1", "skill": skill["name"],
                "skill_id": skill["id"], "skill_root": skill["root"],
                "skill_path": skill["path"], "skill_sha256_16": raw_sha,
                "also_found_in": [{"root": m["root"], "id": m["id"]}
                                  for m in others],
                "procedure": steps, "procedure_declared":
                    bool(skill["procedure"]),
                "shape": shape, "dry_run": True, "dispatched": False,
                "gate": {"admitted": False,
                         "reasons": ["skill declares no gateable output "
                                    "shape"]},
                "wall_seconds": round(time.time() - t0, 1),
                "promotion_allowed": False,
                "claim_ceiling": "shape analysis only; nothing dispatched"},
                indent=1, sort_keys=True))
            print(f"RECEIPT {rundir.name}/SKILL_RUN_RECEIPT.json")
            return 0
        rundir.mkdir(parents=True, exist_ok=True)
        (rundir / "SKILL_RUN_RECEIPT.json").write_text(json.dumps({
            "schema": "cb.skill-run.v1", "skill": skill["name"],
            "skill_id": skill["id"], "skill_root": skill["root"],
            "skill_path": skill["path"], "skill_sha256_16": raw_sha,
            "also_found_in": [{"root": m["root"], "id": m["id"]}
                              for m in others],
            "procedure": steps, "procedure_declared": bool(skill["procedure"]),
            "shape": shape, "dry_run": False, "dispatched": False,
            "gate": {"admitted": False,
                     "reasons": ["skill declares no gateable output shape"]},
            "wall_seconds": round(time.time() - t0, 1),
            "promotion_allowed": False,
            "claim_ceiling": "shape analysis only; nothing dispatched"},
            indent=1, sort_keys=True))
        print(f"RECEIPT {rundir.name}/SKILL_RUN_RECEIPT.json")
        return 1

    print(f"STRUCTURE  {n_children} procedure-step council(s) x "
          f"{len(members)} members = {n_jobs} L3 calls, plus 1 compile call "
          f"on {COMPILE_LANE}")
    print(f"   members answer under: {members}")
    print(f"   lanes ({len(lanes)}): {lanes}\n")

    if a.dry_run:
        print(f"DRY RUN — {n_jobs} step-council jobs would be built, "
              f"none dispatched.")
        rundir.mkdir(parents=True, exist_ok=True)
        (rundir / "SKILL_RUN_RECEIPT.json").write_text(json.dumps({
            "schema": "cb.skill-run.v1", "skill": skill["name"],
            "skill_id": skill["id"], "skill_root": skill["root"],
            "skill_path": skill["path"], "skill_sha256_16": raw_sha,
            "also_found_in": [{"root": m["root"], "id": m["id"]}
                              for m in others],
            "procedure": steps, "procedure_declared": bool(skill["procedure"]),
            "shape": shape, "shape_kind": kind,
            "structure": {"steps": n_children, "members_per_step": len(members),
                         "l3_calls_planned": n_jobs, "compile_lane": COMPILE_LANE},
            "dry_run": True, "dispatched": False,
            "gate": {"admitted": None,
                     "reasons": ["dry run — shape is gateable; not dispatched"]},
            "wall_seconds": round(time.time() - t0, 1),
            "promotion_allowed": False,
            "claim_ceiling": "structure and shape analysis only; nothing "
                            "dispatched"},
            indent=1, sort_keys=True))
        print(f"RECEIPT {rundir.name}/SKILL_RUN_RECEIPT.json")
        return 0

    # ---------------------------------------------------------- live dispatch
    sm = StrategyMemory(
        prompt_intent=f"Run the skill '{skill['name']}' to its own declared "
                      "procedure, then gate the compiled artifact against "
                      "its own declared output shape.",
        success_condition="every procedure-step council clears the member "
                          "floor and the compiled artifact conforms to the "
                          "skill's own declared shape",
        claim_ceiling="the skill's declared procedure ran on free-lane "
                      "councils and its declared shape was checked; CB "
                      "does not judge whether the skill's analysis is "
                      "correct, and does not claim any declared output "
                      "file was actually written to disk")
    sm.kill("reading a SKILL.md as prompt text is the same as running it")
    sm.kill("a shape this runner invents is the same as a shape the "
           "skill declared")

    jobs = build_step_jobs(skill, steps, shape, kind, a.task, members,
                           lanes, sm)
    raw = run_jobs(jobs, width=a.conc, lanes=lanes)
    live = [r for r in raw.values() if r["ok"]]
    print(f"L3  dispatched {len(jobs)}  live {len(live)}  "
          f"count law {'holds' if len(live) <= len(jobs) else 'VIOLATED'}")
    by_lane = {}
    for r in raw.values():
        s = by_lane.setdefault(r["lane"], [0, 0])
        s[0] += 1; s[1] += 1 if r["ok"] else 0
    for ln, (c, o) in by_lane.items():
        print(f"      {ln:<44}{o}/{c} live")
    print()

    councils = {}
    for si, step in enumerate(steps, 1):
        recs = {k.split("|")[1]: v for k, v in raw.items()
                if k.startswith(f"step{si}|")}
        ans = {sl: r["text"] for sl, r in recs.items() if r["ok"] and r["text"]}
        cc = collapse_check(ans)
        pd = provider_diversity(list(recs.values()))
        councils[si] = {"step": step, "answers": ans, "collapse": cc,
                        "provider_diversity": pd,
                        "seats": {sl: {"lane": r["lane"], "model": r.get("model"),
                                       "family": family_of(r), "ok": r["ok"],
                                       "sec": r.get("sec"),
                                       "error": r.get("error", "")}
                                 for sl, r in recs.items()}}
        print(f"step {si}  {cc['verdict']:<34}sim {cc.get('mean_similarity')}"
              f"  n={cc['members']}  families {pd['families']}")
    print()

    comp_job = build_compile_job(skill, steps, shape, kind, a.task,
                                 councils, sm)
    comp_raw = run_jobs([comp_job], width=1)
    comp_r = comp_raw.get("compile", {"ok": False, "text": ""})
    compiled_text = comp_r.get("text", "") if comp_r.get("ok") else ""
    print(f"COMPILE  dispatched 1 on {COMPILE_LANE}  "
          f"{'returned' if compiled_text else 'FAILED'}\n")

    gate = gate_artifact(kind, shape, compiled_text, councils)
    print(f"GATE  {'ADMITTED' if gate['admitted'] else 'REFUSED'}")
    for r in gate["reasons"]:
        print(f"   - {r}")

    rundir.mkdir(parents=True, exist_ok=True)
    (rundir / "SKILL_RUN_RECEIPT.json").write_text(json.dumps({
        "schema": "cb.skill-run.v1", "skill": skill["name"],
        "skill_id": skill["id"], "skill_root": skill["root"],
        "skill_path": skill["path"], "skill_sha256_16": raw_sha,
        "also_found_in": [{"root": m["root"], "id": m["id"]} for m in others],
        "task": a.task,
        "procedure": steps, "procedure_declared": bool(skill["procedure"]),
        "shape": shape, "shape_kind": kind,
        "structure": {"steps": n_children, "members_per_step": len(members),
                     "l3_calls_planned": n_jobs, "compile_lane": COMPILE_LANE},
        "L3": {"dispatched": len(jobs), "live": len(live),
              "by_lane": {k: {"called": c, "live": o}
                         for k, (c, o) in by_lane.items()}},
        "councils": councils,
        "compiled_raw": compiled_text, "compiled": gate.get("compiled"),
        "dry_run": False, "dispatched": True,
        "gate": {"admitted": gate["admitted"], "reasons": gate["reasons"]},
        "strategy_memory": sm.receipt(),
        "wall_seconds": round(time.time() - t0, 1), "promotion_allowed": False,
        "claim_ceiling": "the skill's declared procedure ran on free-lane "
                        "councils and its declared shape was checked; CB "
                        "does not judge whether the skill's analysis is "
                        "correct, and does not claim any declared output "
                        "file was actually written to disk"},
        indent=1, sort_keys=True))
    print(f"\nRECEIPT {rundir.name}/SKILL_RUN_RECEIPT.json "
          f"({time.time() - t0:.1f}s)")
    return 0 if gate["admitted"] else 1


if __name__ == "__main__":
    sys.exit(main())
