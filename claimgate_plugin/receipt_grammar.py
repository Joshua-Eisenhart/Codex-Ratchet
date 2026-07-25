#!/usr/bin/env python3
"""TYPED RECEIPT GRAMMAR — dispositions come from a schema ROLE, not from a number hunt.

WHAT THIS REPLACES. claimgate_plugin/claim_policy_gate.py went through three
designs and each was defeated by attacking it:

  1. key-name denylist + container allowlist   -> b7 (`count` is on the ignored
     list at ANY depth), b8 (bare integer outside a claim-bearing container),
     b9 (the float written as a JSON string)
  2. inverted "every number is a claim" + 22 exempt full paths -> b11 (the whole
     payload one level down under `digest`, because the exemption pruned the
     SUBTREE), b12 (a top-level array returned 0 without evaluating)
  3. leaf-not-subtree patch -> 12/12 fixtures non-admitting, but the rule is
     still SHAPE INFERENCE from raw JSON and a 22-path raw-number exemption list
     is itself the loophole

The through-line in all three is that the gate tried to recover MEANING from
JSON shape. `count` is bookkeeping in one receipt and a measured cardinality in
the next; no walker can tell them apart, so every fix was a new heuristic and
every heuristic had a next fixture.

THE RULE HERE. A receipt node has no meaning until an evaluator-owned schema
assigns it a ROLE. Six roles, and the ROLE's POLARITY — not the schema author,
not the receipt — fixes how far it reaches:

    role         polarity      reach                      obligation
    ----------   -----------   ------------------------   -------------------
    metadata     relieving     ONE SCALAR, exact position exempt
    input        relieving     ONE SCALAR, exact position exempt
    measurement  obligation    the whole SUBTREE          witnessed provenance
    claim        obligation    the whole SUBTREE          witnessed provenance
    result       obligation    the whole SUBTREE          witnessed provenance
    evidence     recheckable   a container it declares    admitted procedure
    envelope     grouping      nothing; children speak    none

The asymmetry is the design. Obligations inherit DOWNWARD because inheriting an
obligation can only ADD requirements — so a subtree typed `measurement` needs no
rule for anything inside it, and an unknown key under it becomes an obligation
rather than an escape. Exemptions do NOT inherit, and cannot: meta-rule M1
refuses any schema in which a relieving role owns children, so a `metadata` node
has no subtree and "does the exemption cover the children" is a question that
cannot be asked. That is b11 closed structurally instead of patched.

Everything unnamed PARKs. There is no permissive fallback family and no
default-allow node, so b8's bare integer and b9's numeric string need no rule of
their own — they are simply not typed, and untyped is refused. The
`_NUMERIC_STRING` regex from design 2 is gone: at a `measurement` position the
schema declares `number`, so a string there is a declared-type violation, not a
pattern to sniff for.

The grammar is POSITIONAL, which is why relocation stops working. `digest` typed
as a scalar hex string is exempt at the root; the same bytes moved to
`digest.metrics.spectral_gap` resolve to no schema node at all, so they are
untyped and PARK. Moving a payload does not carry its type with it.

EXIT 0 MEANS "AN OBLIGATION WAS DISCHARGED", NOT "NOTHING WAS FOUND". Meta-rule
M9. claim_policy_gate's `if not nums: return 0, "pass"` meant the second thing,
and the first cut of THIS module inherited it: an empty JSON object reached exit
0, and so did `{"count": 42}`, whose only content sat in a bounded metadata
integer slot. Both were found by attacking this file after it was written, and
both now PARK. Only the evaluator can waive this, per family, with a boolean
`x-asserts-nothing`.

NO UNBOUNDED NUMERIC EXEMPTION EXISTS. Meta-rule M6 rejects any schema whose
relieving scalar type is numeric without finite `min` and `max`. The 22-path
list allowed an arbitrary float at each of 22 positions; here every permitted
raw number sits in a declared closed range, and `detail.residual_relieving_
numeric_paths` reports that surface as a number so it can be audited rather
than assumed small.

PRODUCER SELF-DESCRIPTION IS RECORDED AND NEVER HONOURED. `claim_kind`,
`numeric_engine_required`, `exemption_reason`, `TOOL_INTEGRATION_DEPTH` and any
other node flagged `x-producer-assertion` are copied verbatim into
`detail.producer_assertions` and have ZERO effect on the exit code. Meta-rule M5
additionally refuses any schema that tries to read a role out of the instance,
so "the receipt names its own role" is not expressible.

HONEST CEILING, three parts:

  1. receipt_schema.json lives in the repo it governs, so a producer who can
     commit can edit it. CODEOWNERS on this path plus branch protection is what
     would make it a trust root. NOT in force. Same ceiling claim_policy.json
     carries; moving to a grammar does not change it.
  2. THERE IS NO PASS PATH FOR A NUMERIC RECEIPT TODAY, by construction. The
     only registered witness procedure is claimgate_plugin/engine_witness.py,
     whose own header reads "FAILED CANDIDATE — PURGATORY. Do NOT import this
     from any gate." Its status in receipt_schema.json is `purgatory`, and a
     non-admitted procedure cannot satisfy an obligation, so every measurement
     PARKs. claim_policy_gate.py:146 imports that module anyway and lets its
     verdict decide BLOCK; this grammar makes the file's own status operative
     instead of leaving it as prose the gate does not read.
  3. this module checks that the OBLIGATION is discharged — procedure admitted,
     artifact present, sha256 of the artifact matching the declared digest. It
     does not re-execute an engine. Actually running a leg is the witness layer,
     a separate seam, and it currently has no admitted implementation.

KNOWN LIMIT, stated rather than hidden: free text at a `metadata` position is
exempt, so a number written inside prose ("spectral gap is 1.78") is not
refused. It is also not admitted by anything — no gate can consume it, and a
`claim` role requires an object, so prose at a claim position PARKs. The grammar
governs what a gate may consume, not what a human may infer from prose.

Exit: 0 grammar satisfied | 1 BLOCK | 3 PARK/PENDING_EVIDENCE | 2 usage.
Nonzero is a policy/infra disposition, never a scientific verdict.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO / "claimgate_plugin" / "receipt_schema.json"

# POLARITY IS FIXED HERE, in the evaluator's code, not in the schema file. A
# schema may say WHICH role a position has; it may not invent a role, and it may
# not change what a role reaches. Both would let the loophole move from data
# into configuration.
POLARITY = {
    "metadata": "relieving",
    "input": "relieving",
    "measurement": "obligation",
    "claim": "obligation",
    "result": "obligation",
    "evidence": "recheckable",
    "envelope": "grouping",
}
RELIEVING = {r for r, p in POLARITY.items() if p == "relieving"}
OBLIGATION = {r for r, p in POLARITY.items() if p == "obligation"}
CONTAINER_KEYS = ("properties", "items", "values")

# What JSON kinds a role may carry when it lands on a scalar.
OBLIGATION_VALUE_KINDS = {
    "measurement": {"integer", "number"},
    "result": {"integer", "number", "bool"},
    "claim": set(),          # a claim must be an OBJECT; prose alone is not a claim
}

BLOCK_CODES = {
    "SCHEMA_REJECTED", "BINDING_AMBIGUOUS", "ROOT_TYPE_MISMATCH", "TYPE_MISMATCH",
    "RANGE_VIOLATION", "NON_FINITE_MEASUREMENT", "CONTAINER_KIND_MISMATCH",
}


def load_schema(path: Path | None = None) -> dict:
    return json.loads((path or SCHEMA_PATH).read_bytes())


# ---------------------------------------------------------------------------
# JSON kinds
# ---------------------------------------------------------------------------
def _kind(v):
    if v is None:
        return "null"
    if isinstance(v, bool):          # before int: bool is a subclass of int
        return "bool"
    if isinstance(v, int):
        return "integer"
    if isinstance(v, float):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, dict):
        return "object"
    if isinstance(v, list):
        return "array"
    return "unknown"


def _is_container(v):
    return isinstance(v, (dict, list))


# ---------------------------------------------------------------------------
# META-RULES. Checked at load. A schema that violates any of them fails the
# WHOLE evaluation CLOSED — an evaluator that cannot state its own grammar must
# not grade a receipt.
# ---------------------------------------------------------------------------
def validate_schema(schema: dict) -> list[str]:
    bad: list[str] = []
    types = schema.get("scalar_types") or {}
    procs = schema.get("witness_procedures") or {}

    for name, spec in types.items():
        if name.startswith("_"):      # `_rule` / `_why` prose, not a type
            continue
        j = spec.get("json") if isinstance(spec, dict) else None
        if j not in {"null", "bool", "integer", "number", "string"}:
            bad.append(f"M0 scalar_types.{name}: json={j!r} is not a scalar kind")
            continue
        # M6: no unbounded raw-number exemption anywhere in the grammar.
        if j in {"integer", "number"}:
            lo, hi = spec.get("min"), spec.get("max")
            if not isinstance(lo, (int, float)) or not isinstance(hi, (int, float)):
                bad.append(f"M6 scalar_types.{name}: numeric relieving type without finite "
                           f"min AND max — an unbounded raw-number exemption is the 22-path "
                           f"list rebuilt as a type")
            elif not (math.isfinite(lo) and math.isfinite(hi) and lo <= hi):
                bad.append(f"M6 scalar_types.{name}: min/max not a finite ordered range")

    for pname, p in procs.items():
        if pname.startswith("_"):
            continue
        if not isinstance(p, dict) or p.get("status") not in {"admitted", "purgatory", "absent"}:
            bad.append(f"M8 witness_procedures.{pname}: status must be admitted|purgatory|absent")

    def node(n, where):
        if not isinstance(n, dict):
            bad.append(f"M0 {where}: schema node is not an object")
            return
        if "x-role-from-instance" in n:
            # M5: a role read out of the instance is producer-declared typing.
            bad.append(f"M5 {where}: x-role-from-instance — a receipt may DESCRIBE itself, "
                       f"it may not assign its own role")
        role = n.get("role")
        if role not in POLARITY:
            bad.append(f"M0 {where}: role={role!r} not in the fixed role table")
            return
        owns = [k for k in CONTAINER_KEYS if k in n]

        if role in RELIEVING:
            # M1: no role both owns children and confers exemption.
            if owns:
                bad.append(f"M1 {where}: relieving role {role!r} declares {owns} — an exemption "
                           f"that owns a subtree is exactly the b11 hole")
            t = n.get("type")
            if t not in types:
                bad.append(f"M1 {where}: relieving role {role!r} needs a declared scalar type "
                           f"(got {t!r})")
            # M3: exemption is a reviewed act and must say why, in the schema.
            if len(str(n.get("x-why") or "")) < 12:
                bad.append(f"M3 {where}: relieving role needs a reviewed x-why of >= 12 chars")
            if role == "input" and not n.get("x-input-source"):
                bad.append(f"M3 {where}: input role needs x-input-source")

        elif role == "envelope":
            # M2: grouping only, and it must actually group something.
            if not owns:
                bad.append(f"M2 {where}: envelope declares no children — it confers nothing and "
                           f"covers nothing, so it can only be a silent hole")
            if "values" in n and not n.get("x-key-type"):
                bad.append(f"M2 {where}: envelope with `values` needs x-key-type to constrain "
                           f"the key set")
            if n.get("x-key-type") and n["x-key-type"] not in types:
                bad.append(f"M2 {where}: x-key-type={n['x-key-type']!r} is not a declared type")

        elif role in OBLIGATION:
            # M7: a measurement the evaluator cannot say how to witness is a defect
            # in the GATE. Fail closed rather than let it quietly park forever.
            if not n.get("x-provenance"):
                bad.append(f"M7 {where}: obligation role {role!r} without x-provenance — a gate "
                           f"that cannot name how a number is witnessed must not grade it")

        elif role == "evidence":
            if not n.get("x-recheck"):
                bad.append(f"M8 {where}: evidence role without x-recheck")
            elif n["x-recheck"] not in procs:
                bad.append(f"M8 {where}: x-recheck={n['x-recheck']!r} is not a registered "
                           f"witness procedure")
            props = n.get("properties") or {}
            for req in ("artifact", "digest"):
                if req not in props:
                    bad.append(f"M8 {where}: evidence must declare properties.{req}")

        for k in ("properties", "values", "items"):
            sub = n.get(k)
            if k == "properties" and isinstance(sub, dict):
                for kk, vv in sub.items():
                    if kk.startswith("_"):
                        continue
                    node(vv, f"{where}.properties.{kk}")
            elif k in ("values", "items") and sub is not None:
                node(sub, f"{where}.{k}")

    fams = {k: v for k, v in (schema.get("families") or {}).items() if not k.startswith("_")}
    if not fams:
        bad.append("M0 families: no family declared, so every receipt is unbound")
    for fname, fam in fams.items():
        root = (fam or {}).get("root")
        # M4: the root is an object envelope. A receipt that is not a mapping
        # cannot resolve any position, and design 2 returned 0 for exactly that.
        if not isinstance(root, dict) or root.get("role") != "envelope" \
                or "properties" not in root:
            bad.append(f"M4 families.{fname}.root: must be an envelope declaring properties")
            continue
        # M9: only the EVALUATOR may declare a family assertion-free, and it must be
        # a bool, so "this receipt asserts nothing" cannot be smuggled as prose.
        an = fam.get("x-asserts-nothing")
        if an is not None and not isinstance(an, bool):
            bad.append(f"M9 families.{fname}.x-asserts-nothing: must be a bool")
        node(root, f"families.{fname}.root")
    return bad


# ---------------------------------------------------------------------------
# Family binding. Evaluator-owned PATH globs, never a field the producer chose:
# selecting your own family by writing `classification` would be self-typing.
# ---------------------------------------------------------------------------
def _glob_re(g: str) -> re.Pattern:
    out, i = [], 0
    while i < len(g):
        if g.startswith("**", i):
            out.append(".*")
            i += 2
        elif g[i] == "*":
            out.append("[^/]*")
            i += 1
        elif g[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(g[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def bind_family(path, schema):
    """-> (family_name | None, [candidate keys], normalised paths tried)"""
    p = Path(path)
    tried = [p.as_posix()]
    try:
        tried.append(p.resolve().relative_to(REPO).as_posix())
    except (ValueError, OSError):
        pass
    hits = []
    for b in schema.get("bindings") or []:
        rx = _glob_re(b.get("path_glob", ""))
        if any(rx.match(t) for t in tried):
            hits.append(b["family"])
    hits = sorted(set(hits))
    if len(hits) == 1 and hits[0] in (schema.get("families") or {}):
        return hits[0], hits, tried
    return None, hits, tried


# ---------------------------------------------------------------------------
# Scalar type check
# ---------------------------------------------------------------------------
def _check_scalar(value, tname, types):
    """-> (ok, code, why)"""
    spec = types[tname]
    k = _kind(value)
    want = spec["json"]
    if k == "null":
        if spec.get("nullable"):
            return True, None, None
        return False, "TYPE_MISMATCH", f"null where {tname} ({want}) is declared"
    if want == "integer":
        if k == "number" and spec.get("reject_float"):
            return False, "TYPE_MISMATCH", (f"{value!r} is a float where {tname} declares an "
                                            f"integer — a measured quantity wearing a "
                                            f"bookkeeping type")
        if k not in {"integer"}:
            return False, "TYPE_MISMATCH", f"{k} where {tname} declares integer"
    elif want == "number":
        if k not in {"integer", "number"}:
            return False, "TYPE_MISMATCH", f"{k} where {tname} declares number"
    elif want == "bool":
        if k != "bool":
            return False, "TYPE_MISMATCH", f"{k} where {tname} declares bool"
    elif want == "string":
        if k != "string":
            return False, "TYPE_MISMATCH", f"{k} where {tname} declares string"
    if want in {"integer", "number"}:
        if not math.isfinite(float(value)):
            return False, "RANGE_VIOLATION", f"non-finite value at {tname}"
        if not (spec["min"] <= value <= spec["max"]):
            return False, "RANGE_VIOLATION", (f"{value!r} outside the declared closed range "
                                              f"[{spec['min']}, {spec['max']}] for {tname} — a "
                                              f"bookkeeping position is not a place to park a "
                                              f"measurement")
    if want == "string":
        if spec.get("maxLength") and len(value) > spec["maxLength"]:
            return False, "TYPE_MISMATCH", f"string longer than {tname} maxLength"
        if spec.get("enum") is not None and value not in spec["enum"]:
            return False, "TYPE_MISMATCH", f"{value!r} not in the {tname} enum"
        if spec.get("regex") and not re.match(spec["regex"], value):
            return False, "TYPE_MISMATCH", f"{value!r} does not match the {tname} pattern"
    return True, None, None


# ---------------------------------------------------------------------------
# Walk
# ---------------------------------------------------------------------------
class _Ctx:
    def __init__(self, schema, famroot, instance, receipt_path):
        self.schema = schema
        self.types = schema.get("scalar_types") or {}
        self.procs = schema.get("witness_procedures") or {}
        self.famroot = famroot
        self.instance = instance
        self.receipt_path = Path(receipt_path)
        self.findings: list[dict] = []
        self.exempt: list[str] = []
        self.obligations: list[str] = []
        self.discharged: list[str] = []
        self.producer_assertions: dict = {}
        self._prov_cache: dict = {}
        # provenance pointer of the nearest obligation ancestor, per role, so an
        # unknown key inside a measurement subtree inherits the SAME obligation
        self._inherited_prov: dict = {}

    def add(self, path, code, why):
        self.findings.append({"path": path or ".", "code": code,
                              "severity": "BLOCK" if code in BLOCK_CODES else "PARK",
                              "why": why})


def _schema_at(famroot, dotted):
    n = famroot
    for part in dotted.split("."):
        if not isinstance(n, dict):
            return None
        n = (n.get("properties") or {}).get(part)
        if n is None:
            return None
    return n


def _inst_at(instance, dotted):
    v = instance
    for part in dotted.split("."):
        if not isinstance(v, dict) or part not in v:
            return None
        v = v[part]
    return v


def _provenance(dotted, ctx):
    """Is the obligation at `dotted` discharged? -> (ok, code, why)"""
    if dotted in ctx._prov_cache:
        return ctx._prov_cache[dotted]
    res = _provenance_uncached(dotted, ctx)
    ctx._prov_cache[dotted] = res
    return res


def _provenance_uncached(dotted, ctx):
    snode = _schema_at(ctx.famroot, dotted)
    if snode is None or snode.get("role") != "evidence":
        return False, "PROVENANCE_TARGET_NOT_EVIDENCE", (
            f"x-provenance points at {dotted!r}, which the schema does not type as evidence")
    inst = _inst_at(ctx.instance, dotted)
    if inst is None:
        return False, "PROVENANCE_TARGET_ABSENT", (
            f"the receipt carries no {dotted!r}, so nothing witnesses this value. Omission is "
            f"pending evidence, never exemption")
    if not isinstance(inst, dict):
        return False, "PROVENANCE_TARGET_ABSENT", f"{dotted!r} is not an evidence object"
    pname = snode.get("x-recheck")
    proc = ctx.procs.get(pname) or {}
    if proc.get("status") != "admitted":
        return False, "WITNESS_PROCEDURE_NOT_ADMITTED", (
            f"witness procedure {pname!r} has status {proc.get('status')!r} — "
            f"{str(proc.get('_why') or '')[:150]}")
    art, dig = inst.get("artifact"), inst.get("digest")
    if not isinstance(art, str) or not isinstance(dig, str):
        return False, "EVIDENCE_ARTIFACT_ABSENT", f"{dotted} lacks a scalar artifact + digest"
    for base in (ctx.receipt_path.parent, REPO):
        cand = base / art
        if cand.is_file():
            got = hashlib.sha256(cand.read_bytes()).hexdigest()
            if got.lower() != dig.lower():
                return False, "EVIDENCE_ARTIFACT_ABSENT", (
                    f"{art} sha256 {got[:16]}... does not match the declared digest "
                    f"{dig[:16]}...")
            return True, None, None
    return False, "EVIDENCE_ARTIFACT_ABSENT", f"artifact {art!r} not found on disk"


def _walk(inst, snode, path, ctx, inherited):
    """inherited is an OBLIGATION role carried down from an ancestor, or None.

    Nothing ever carries an EXEMPTION down. That is not a policy choice made
    here; meta-rule M1 has already refused any schema in which a relieving role
    has children, so there is no exemption with a subtree to carry.
    """
    # ---- no schema node at this position -----------------------------------
    if snode is None:
        if inherited:
            # An unknown key under an obligation subtree is an OBLIGATION, not an
            # escape. Inheriting downward can only add requirements.
            snode = {"role": inherited,
                     "x-provenance": ctx._inherited_prov.get(inherited)}
        else:
            if _is_container(inst):
                ctx.add(path, "UNTYPED_SUBTREE",
                        "no schema position types this subtree; an unknown subtree is MORE "
                        "untyped, never less, so it is inspected and still refused")
                _descend_untyped(inst, path, ctx)
            else:
                ctx.add(path, "UNTYPED_SCALAR",
                        f"no schema position types this {_kind(inst)}; the grammar has no "
                        f"permissive default, so unnamed content PARKs")
            return

    role = snode["role"]
    if snode.get("x-producer-assertion") and not _is_container(inst):
        ctx.producer_assertions[path.lstrip(".") or "."] = inst

    # ---- envelope: grouping only ------------------------------------------
    if role == "envelope":
        if not _is_container(inst):
            ctx.add(path, "UNDER_SPECIFIED",
                    f"schema declares a container here; instance holds a {_kind(inst)}. Less "
                    f"payload than declared is incompleteness, so it PARKs")
            return
        _descend(inst, snode, path, ctx, inherited=None)
        return

    # ---- relieving: exemption is a SCALAR at an EXACT position -------------
    if role in RELIEVING:
        if _is_container(inst):
            ctx.add(path, "RELIEVING_ROLE_ON_CONTAINER",
                    f"schema declares role {role!r} on a SCALAR here; the instance holds a "
                    f"{_kind(inst)}. An exemption never covers a subtree, so this PARKs and "
                    f"the children are inspected with NO inherited exemption")
            _descend_untyped(inst, path, ctx)
            return
        ok, code, why = _check_scalar(inst, snode["type"], ctx.types)
        if ok:
            ctx.exempt.append(path.lstrip("."))
        else:
            ctx.add(path, code, f"{why}. Declared {role} by the schema, so the TYPE is the "
                                f"second, independent refusal")
        return

    # ---- evidence: satisfies pointers, exempts nothing by itself ----------
    if role == "evidence":
        if not isinstance(inst, dict):
            ctx.add(path, "UNDER_SPECIFIED", "evidence must be an object with artifact + digest")
            return
        _descend(inst, snode, path, ctx, inherited=None)
        return

    # ---- obligation: measurement | claim | result -------------------------
    ctx.obligations.append(path.lstrip(".") or ".")
    dotted = snode.get("x-provenance")
    if _is_container(inst):
        if role == "claim" and isinstance(inst, list):
            ctx.add(path, "CLAIM_WITHOUT_POINTERS",
                    "a claim must be an object binding an assertion to measurement pointers")
        prov_ok, pcode, pwhy = _provenance(dotted, ctx) if dotted else (
            False, "PROVENANCE_UNDECLARED", "schema names no provenance for this subtree")
        if not prov_ok:
            ctx.add(path, pcode, f"{role} subtree: {pwhy}")
        else:
            ctx.discharged.append(path.lstrip(".") or ".")
        ctx._inherited_prov[role] = dotted
        _descend(inst, snode, path, ctx, inherited=role)
        return

    if role == "claim":
        ctx.add(path, "CLAIM_WITHOUT_POINTERS",
                f"a {_kind(inst)} at a claim position. Prose is not a claim: an assertion the "
                f"grammar can check must be an object binding text to measurement pointers, so "
                f"a number written inside a sentence is admitted by nothing")
        return

    k = _kind(inst)
    allowed = OBLIGATION_VALUE_KINDS[role]
    if k not in allowed:
        ctx.add(path, "TYPE_MISMATCH",
                f"{k} at a {role} position, which declares {sorted(allowed)}. Encoding a "
                f"number as text does not make it a different number, and the schema type "
                f"refuses it without any string-sniffing")
        return
    if k in {"integer", "number"} and not math.isfinite(float(inst)):
        ctx.add(path, "NON_FINITE_MEASUREMENT",
                f"{inst!r} at a {role} position: NaN == NaN is false in IEEE 754, so a NaN pair "
                f"reads as perfect agreement under a difference test")
        return
    prov_ok, pcode, pwhy = _provenance(dotted, ctx) if dotted else (
        False, "PROVENANCE_UNDECLARED", "schema names no provenance for this value")
    if not prov_ok:
        ctx.add(path, pcode, f"{role} value {inst!r}: {pwhy}")
    else:
        ctx.discharged.append(path.lstrip(".") or ".")


def _descend(inst, snode, path, ctx, inherited):
    if isinstance(inst, dict):
        props = snode.get("properties") or {}
        vals = snode.get("values")
        keyt = snode.get("x-key-type")
        for k, v in inst.items():
            p = f"{path}.{k}"
            child = props.get(k)
            if child is None and vals is not None:
                if keyt and not _check_scalar(k, keyt, ctx.types)[0]:
                    ctx.add(p, "UNTYPED_SCALAR",
                            f"key {k!r} is outside the declared key type {keyt!r} for this map")
                    continue
                child = vals
            _walk(v, child, p, ctx, inherited)
    elif isinstance(inst, list):
        items = snode.get("items")
        for i, v in enumerate(inst):
            _walk(v, items, f"{path}[{i}]", ctx, inherited)


def _descend_untyped(inst, path, ctx):
    """Recurse with NO schema and NO inheritance. Used under an unknown subtree and
    under a relieving role that landed on a container — the b11 shape. Every leaf
    inside lands on UNTYPED, so relocating a payload strips its type."""
    if isinstance(inst, dict):
        for k, v in inst.items():
            _walk(v, None, f"{path}.{k}", ctx, None)
    elif isinstance(inst, list):
        for i, v in enumerate(inst):
            _walk(v, None, f"{path}[{i}]", ctx, None)


# ---------------------------------------------------------------------------
# evaluate — same contract as claim_policy_gate.evaluate
# ---------------------------------------------------------------------------
def _residual_numeric_surface(schema):
    """Every position where the grammar permits a RAW NUMBER with no obligation.
    Reported as a count so the exemption surface is audited, not assumed small."""
    types = schema.get("scalar_types") or {}
    out = []

    def node(n, where):
        if not isinstance(n, dict):
            return
        if n.get("role") in RELIEVING:
            spec = types.get(n.get("type")) or {}
            if spec.get("json") in {"integer", "number"}:
                out.append(f"{where} [{spec.get('min')}, {spec.get('max')}]")
        for kk, vv in (n.get("properties") or {}).items():
            if not kk.startswith("_"):
                node(vv, f"{where}.{kk}")
        for k in ("values", "items"):
            if n.get(k) is not None:
                node(n[k], f"{where}.{k}")

    for fname, fam in (schema.get("families") or {}).items():
        if not fname.startswith("_") and isinstance(fam, dict):
            node(fam.get("root"), fname)
    return out


def evaluate(receipt, path, schema):
    """-> (exit, label, message, detail). 0 satisfied | 1 BLOCK | 3 PARK."""
    det = {
        "grammar_id": schema.get("grammar_id"),
        "producer_assertions_honoured": False,
        "_producer_assertions_note": "recorded verbatim below and given ZERO weight in the exit "
                                     "code; meta-rule M5 also refuses any schema that reads a "
                                     "role out of the instance",
        "schema_ownership": str(schema.get("_ownership") or "")[:200],
    }

    problems = validate_schema(schema)
    if problems:
        det["schema_meta_rule_violations"] = problems[:12]
        det["schema_meta_rule_violation_count"] = len(problems)
        return 1, "BLOCK", (f"SCHEMA REJECTED on {len(problems)} meta-rule violation(s), e.g. "
                            f"{problems[0]}. This is an EVALUATOR-side defect, not a verdict on "
                            f"the receipt: a gate that cannot state its own grammar must not "
                            f"grade anything, so it fails CLOSED"), det

    fam, hits, tried = bind_family(path, schema)
    det["binding_candidates"] = hits
    det["binding_paths_tried"] = tried
    if fam is None and len(hits) > 1:
        return 1, "BLOCK", (f"ambiguous binding {hits} for {path} — two families claiming one "
                            f"receipt is a schema defect, and the choice is not the producer's "
                            f"to make, so it fails CLOSED"), det
    if fam is None:
        return 3, "PARK", (f"no evaluator-owned binding covers {path}. There is no permissive "
                           f"fallback family on purpose: a fallback is where everything quietly "
                           f"routes. Migration of this path is PENDING, and pending is PARK"), det

    det["family"] = fam
    famroot = schema["families"][fam]["root"]
    ctx = _Ctx(schema, famroot, receipt, path)

    if not isinstance(receipt, dict):
        # design 2 returned 0 here, so wrapping any receipt in a JSON array skipped
        # the whole policy. The root role is `envelope` with `properties`, which
        # declares an object; an array is a declared-type violation. The contents
        # are walked anyway, so even a softened root rule leaves them refused.
        ctx.add("", "ROOT_TYPE_MISMATCH",
                f"family {fam} declares an object envelope at the root; the document is a "
                f"{_kind(receipt)}. A non-mapping receipt can resolve no schema position")
        _descend_untyped(receipt, "", ctx)
    else:
        _walk(receipt, famroot, "", ctx, None)

    codes: dict[str, int] = {}
    for f in ctx.findings:
        codes[f["code"]] = codes.get(f["code"], 0) + 1
    blocks = [f for f in ctx.findings if f["severity"] == "BLOCK"]
    parks = [f for f in ctx.findings if f["severity"] == "PARK"]

    det.update({
        "reason_codes": dict(sorted(codes.items(), key=lambda kv: (-kv[1], kv[0]))),
        "block_count": len(blocks),
        "park_count": len(parks),
        "findings": (blocks + parks)[:10],
        "typed_obligations": ctx.obligations[:10],
        "typed_obligation_count": len(ctx.obligations),
        "discharged_obligation_count": len(ctx.discharged),
        "schema_owned_exempt_scalars": ctx.exempt[:10],
        "schema_owned_exempt_count": len(ctx.exempt),
        "producer_assertions": ctx.producer_assertions,
        "residual_relieving_numeric_paths": _residual_numeric_surface(schema),
        "witness_procedure_status": {k: v.get("status")
                                     for k, v in (schema.get("witness_procedures") or {}).items()
                                     if isinstance(v, dict)},
    })

    if blocks:
        top = "; ".join(f"{f['path']} {f['code']}" for f in blocks[:3])
        return 1, "BLOCK", (f"{len(blocks)} declared-type violation(s) — {top}. A schema-owned "
                            f"position states what may sit there; a value that contradicts it is "
                            f"DECIDED, not pending"), det
    if parks:
        top = "; ".join(f"{f['path']} {f['code']}" for f in parks[:3])
        return 3, "PARK", (f"{len(parks)} unresolved position(s) — {top}. Untyped content and "
                           f"undischarged obligations are PENDING EVIDENCE, never exemption"), det

    # M9. Exit 0 means "an obligation was discharged and nothing is unresolved", NOT
    # "nothing was found". claim_policy_gate's `if not nums: return 0, "pass"` had the
    # second meaning, and measured against this module an EMPTY JSON OBJECT reached
    # exit 0 the same way — as did a receipt whose only content sat in a bounded
    # metadata integer slot. A downstream consumer reads exit 0 as gate_admits, so
    # "found nothing" must not wear the same code as "witnessed something".
    fam_decl = (schema["families"][fam] or {})
    if not ctx.discharged and not fam_decl.get("x-asserts-nothing"):
        det["reason_codes"] = {"NO_DISCHARGED_OBLIGATION": 1}
        return 3, "PARK", (f"nothing is unresolved, but NOTHING WAS WITNESSED either: 0 "
                           f"obligation(s) discharged, {len(ctx.exempt)} schema-owned scalar(s) "
                           f"exempt. Family {fam} does not declare x-asserts-nothing, so "
                           f"'no finding' is PENDING EVIDENCE rather than a pass. An empty "
                           f"document must not exit 0"), det
    return 0, "pass", (f"every position resolves to a schema role: {len(ctx.exempt)} "
                       f"schema-owned scalar(s) exempt, {len(ctx.discharged)} obligation(s) "
                       f"discharged by an admitted witness procedure"), det


def main(argv):
    if len(argv) not in (2, 3):
        print("usage: receipt_grammar.py <receipt.json> [schema.json]", file=sys.stderr)
        return 2
    p = Path(argv[1])
    if not p.exists():
        print(f"receipt_grammar: BLOCK — artifact absent: {p}", file=sys.stderr)
        return 1
    try:
        # STRICT PARSE, reused — not plain json.loads. duplicate_json_key was the
        # FIRST hostile class this estate closed (claimgate_plugin/intake_supervisor.py
        # strict_parse), and it reappeared here because a brand-new component reached
        # for the stdlib default instead of the closed thing. Plain json.loads is
        # last-wins, so {"count": 1.78, "count": 5} silently discards the claim before
        # any rule sees it. A closed defect that returns in a new file was never
        # closed at the estate level — only in one file.
        from claimgate_plugin.intake_supervisor import strict_parse
        receipt = strict_parse(p.read_bytes())
        schema = load_schema(Path(argv[2]) if len(argv) == 3 else None)
    except Exception as exc:  # noqa: BLE001
        print(f"receipt_grammar: BLOCK — cannot evaluate ({exc}); failing CLOSED", file=sys.stderr)
        return 1
    code, label, msg, det = evaluate(receipt, p, schema)
    print(json.dumps({"tool": "claimgate.receipt_grammar", "receipt": str(p),
                      "disposition": label, "message": msg, "detail": det,
                      "ceiling": "receipt_schema.json lives in the repo it governs, so it is a "
                                 "strong default, not a trust root, until CODEOWNERS + branch "
                                 "protection cover it; and no witness procedure is ADMITTED "
                                 "today, so no numeric receipt has a pass path"}, indent=1))
    print(f"receipt_grammar: {label} — {msg}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
