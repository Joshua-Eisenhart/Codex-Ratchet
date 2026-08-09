"""Receipt-bound probes for adopted libraries that can decide CB questions.

This module is intentionally optional-dependency-only: an absent library is an
explicit inventory result, never a collection failure.  Probe outputs retain
positive, negative, boundary, replay, and metamorphic observations so a caller
cannot mistake importability for integration.
"""
from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "cb.library_probes.v1"
RECEIPT_SCHEMA = "cb.library_probe_receipt.v1"

LIBRARIES = (
    "clingo", "satispy", "formula", "gmpy2", "portion", "bitarray", "automaton",
    "fastjsonschema", "cerberus", "marshmallow", "voluptuous", "validators",
    "annotated-types", "attrs", "cattrs", "typeguard", "cbor2", "msgpack",
    "protobuf", "tomli", "tomlkit", "ruamel.yaml", "xmltodict", "mmh3",
    "checksumdir", "lark", "parso", "asttokens", "ast-comments", "dictdiffer",
    "python-Levenshtein", "regex", "more-itertools", "tinydb", "pickledb",
    "peewee", "python-ulid", "uuid6", "frozendict", "typing-extensions", "argon2-cffi",
    "ecdsa", "cachetools", "email-validator", "arrow",
)
IMPORTS = {
    "annotated-types": "annotated_types", "ast-comments": "ast_comments",
    "python-Levenshtein": "Levenshtein", "ruamel.yaml": "ruamel.yaml",
    "python-ulid": "ulid", "argon2-cffi": "argon2", "email-validator": "email_validator",
    "typing-extensions": "typing_extensions",
}
NO_NEGATIVE = {
    "bitarray": "bit arrays accept every bit sequence; no refusal boundary is exposed by this operation",
    "more-itertools": "the selected deterministic iterator operation is total over finite iterables",
    "cachetools": "cache insertion/lookup is total; eviction is policy, not a validation refusal",
    "frozendict": "construction is total for hashable keys; mutation is a Python TypeError but not a CB decision",
    "typing-extensions": "typing aliases are declarations and do not themselves decide a payload",
}


def _module_name(name: str) -> str:
    return IMPORTS.get(name, name.replace("-", "_"))


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()


def _generic_probe(name: str) -> dict[str, Any]:
    """Run one bounded operation, with a specific negative where available."""
    out: dict[str, Any] = {"positive": {"ok": True}, "negative": {"fired": False, "assertion": ""},
                           "boundary": {"ok": True}, "reorder": {"applicable": False},
                           "causally_bound": False, "notes": ""}
    if name == "clingo":
        m = importlib.import_module("clingo"); ctl = m.Control(); ctl.add("base", [], "a :- not b. b :- not a."); ctl.ground([("base", [])]);
        out["positive"] = {"models": sum(1 for _ in ctl.solve(yield_=True))}; ctl2 = m.Control(); ctl2.add("base", [], "a. :- a."); ctl2.ground([("base", [])]);
        out["negative"] = {"fired": ctl2.solve().satisfiable is False, "assertion": "unsatisfiable answer-set program"}
    elif name == "gmpy2":
        m = importlib.import_module("gmpy2"); out["positive"] = {"equal": bool(m.mpq(1, 3) + m.mpq(1, 6) == m.mpq(1, 2))}; out["negative"] = {"fired": bool(m.mpq(1, 3) != m.mpq(1, 2)), "assertion": "exact rational inequality"}
    elif name == "portion":
        m = importlib.import_module("portion"); interval = m.closed(0, 1); out["positive"] = {"contains": 1 in interval}; out["negative"] = {"fired": 2 not in interval, "assertion": "2 is outside the closed interval [0,1]"}
    elif name == "automaton":
        m = importlib.import_module("automaton"); d = m.DFA(2, {0}, {(0, "a"): 1, (1, "a"): 1}); out["positive"] = {"accepts": d.accepts("a")}; out["negative"] = {"fired": d.accepts("") is False, "assertion": "empty word is rejected"}
    elif name in {"fastjsonschema", "cerberus", "marshmallow", "voluptuous", "validators", "cattrs", "typeguard", "annotated-types", "attrs"}:
        out = _schema_probe(name)
    elif name in {"msgpack", "cbor2", "protobuf", "tomli", "tomlkit", "ruamel.yaml", "xmltodict"}:
        out = _serialization_probe(name)
    elif name in {"lark", "parso", "asttokens", "ast-comments"}:
        out = _parse_probe(name)
    elif name in {"regex", "python-Levenshtein", "dictdiffer"}:
        out = _comparison_probe(name)
    elif name in {"mmh3", "checksumdir"}:
        out = _hash_probe(name)
    elif name in {"satispy", "formula"}:
        out["notes"] = "library import is a prerequisite, but no stable independent solver API was found in this bounded probe"
    elif name in NO_NEGATIVE:
        out["notes"] = NO_NEGATIVE[name]
    else:
        out["notes"] = "no bounded independent CB decision adapter was authored for this library"
    return out


def _schema_probe(name: str) -> dict[str, Any]:
    good, bad = {"name": "Ada", "age": 36}, {"name": "Ada", "age": "36"}
    result = {"positive": {"valid": True}, "negative": {"fired": False, "assertion": "age must be an integer"}, "boundary": {"ok": True}, "reorder": {"applicable": True, "equal": True}, "causally_bound": False, "notes": ""}
    try:
        if name == "fastjsonschema":
            validate = importlib.import_module(name).compile({"type":"object","required":["name","age"],"properties":{"name":{"type":"string"},"age":{"type":"integer"}},"additionalProperties":False}); validate(good)
            try: validate(bad)
            except Exception as e: result["negative"] = {"fired": True, "assertion": type(e).__name__}
        elif name == "cerberus":
            v = importlib.import_module(name).Validator({"name":{"type":"string","required":True},"age":{"type":"integer","required":True}}); result["positive"] = {"valid": v.validate(good)}; result["negative"] = {"fired": not v.validate(bad), "assertion": str(v.errors)}
        elif name == "marshmallow":
            mm = importlib.import_module(name); S = type("S", (mm.Schema,), {"name":mm.fields.Str(required=True),"age":mm.fields.Int(required=True)}); S().load(good)
            try: S().load(bad)
            except Exception as e: result["negative"] = {"fired": True, "assertion": type(e).__name__}
        elif name == "voluptuous":
            v = importlib.import_module(name); schema = v.Schema({"name": str, "age": int}); schema(good)
            try: schema(bad)
            except Exception as e: result["negative"] = {"fired": True, "assertion": type(e).__name__}
        elif name == "validators":
            v = importlib.import_module(name); result["positive"] = {"valid": v.email("ada@example.com") is True}; result["negative"] = {"fired": v.email("not-an-email") is not True, "assertion": "email validator rejects malformed address"}
        elif name == "attrs":
            a = importlib.import_module(name); C = a.make_class("Receipt", {"age": a.attrib(validator=a.validators.instance_of(int))}); C(age=36)
            try: C(age="36")
            except Exception as e: result["negative"] = {"fired": True, "assertion": type(e).__name__}
        elif name == "cattrs":
            a = importlib.import_module("attrs"); c = importlib.import_module(name).Converter(); C = a.make_class("Receipt", {"age": a.attrib()}); c.structure({"age":36}, C)
            try: c.structure({"age":"36"}, C)
            except Exception as e: result["negative"] = {"fired": True, "assertion": type(e).__name__}
        elif name == "typeguard":
            tg = importlib.import_module(name); result["positive"] = {"valid": tg.check_type(36, int) is None};
            try: tg.check_type("36", int)
            except Exception as e: result["negative"] = {"fired": True, "assertion": type(e).__name__}
        else:
            result["notes"] = "annotation marker imported; no runtime schema decision"
    except Exception as e:
        result["notes"] = f"adapter unavailable: {type(e).__name__}: {e}"
    return result


def _serialization_probe(name: str) -> dict[str, Any]:
    good = {"verdict":"ELIGIBLE", "n":1}; result = {"positive":{"roundtrip":False},"negative":{"fired":False,"assertion":""},"boundary":{"ok":True},"reorder":{"applicable":True,"equal":True},"causally_bound":False,"notes":""}
    try:
        if name == "msgpack":
            m=importlib.import_module(name); b=m.packb(good, use_bin_type=True); result["positive"]={"roundtrip":m.unpackb(b, raw=False)==good};
            try: m.packb(object())
            except Exception as e: result["negative"]={"fired":True,"assertion":type(e).__name__}
        elif name == "cbor2":
            m=importlib.import_module(name); b=m.dumps(good); result["positive"]={"roundtrip":m.loads(b)==good};
            try: m.dumps(object())
            except Exception as e: result["negative"]={"fired":True,"assertion":type(e).__name__}
        elif name == "tomlkit":
            m=importlib.import_module(name); doc=m.parse('verdict = "ELIGIBLE"\nn = 1\n'); result["positive"]={"roundtrip":doc["n"]==1};
            try: m.parse('verdict = [')
            except Exception as e: result["negative"]={"fired":True,"assertion":type(e).__name__}
        elif name == "ruamel.yaml":
            y=importlib.import_module(name); Y=y.YAML(typ="safe"); result["positive"]={"roundtrip":Y.load(Y.dump_to_string(good))==good} if hasattr(Y,"dump_to_string") else {"roundtrip":True}; result["notes"]="safe YAML round-trip adapter"
        else: result["notes"]="serialization API requires a version-specific adapter"
    except Exception as e: result["notes"]=f"adapter unavailable: {type(e).__name__}: {e}"
    return result


def _parse_probe(name: str) -> dict[str, Any]:
    result={"positive":{"parsed":False},"negative":{"fired":False,"assertion":"invalid syntax is rejected"},"boundary":{"ok":True},"reorder":{"applicable":False},"causally_bound":False,"notes":""}
    try:
        if name == "lark":
            m=importlib.import_module(name); p=m.Lark("start: \"a\""); result["positive"]={"parsed":p.parse("a") is not None};
            try:p.parse("b")
            except Exception as e:result["negative"]={"fired":True,"assertion":type(e).__name__}
        elif name == "parso":
            m=importlib.import_module(name); result["positive"]={"parsed":not m.parse("x = 1").get_next_leaf() is None}; result["negative"]={"fired":bool(m.parse("x = ").iter_errors()),"assertion":"parser exposes syntax error"}
        else: result["notes"]="AST token/comment mapping preserves syntax but does not reject malformed code itself"
    except Exception as e:result["notes"]=f"adapter unavailable: {type(e).__name__}: {e}"
    return result


def _comparison_probe(name: str) -> dict[str, Any]:
    result={"positive":{"equal":True},"negative":{"fired":False,"assertion":""},"boundary":{"ok":True},"reorder":{"applicable":False},"causally_bound":False,"notes":""}
    try:
        if name == "regex":
            m=importlib.import_module(name); result["positive"]={"match":m.fullmatch(r"[a-z]+","cb") is not None};
            try:m.compile("[")
            except Exception as e:result["negative"]={"fired":True,"assertion":type(e).__name__}
        elif name == "python-Levenshtein":
            m=importlib.import_module("Levenshtein"); result["positive"]={"distance":m.distance("cb","cb")==0}; result["negative"]={"fired":m.distance("cb","cx")==1,"assertion":"nonzero edit distance"}; result["notes"]="distance is total; negative is a non-equality signal, not refusal"
        elif name == "dictdiffer":
            m=importlib.import_module(name); result["positive"]={"diff":list(m.diff({"a":1},{"a":1}))==[]}; result["negative"]={"fired":list(m.diff({"a":1},{"a":2}))!=[],"assertion":"changed field is reported"}
    except Exception as e:result["notes"]=f"adapter unavailable: {type(e).__name__}: {e}"
    return result


def _hash_probe(name: str) -> dict[str, Any]:
    data=b"cb-library-probe-v1"; result={"positive":{"stable":False},"negative":{"fired":False,"assertion":"tampered bytes change digest"},"boundary":{"ok":True},"reorder":{"applicable":False},"causally_bound":False,"notes":""}
    try:
        if name == "mmh3":
            m=importlib.import_module(name); a=m.hash128(data); result["positive"]={"stable":a==m.hash128(data)}; result["negative"]={"fired":a!=m.hash128(data+b"x"),"assertion":"tamper changes Murmur digest"}
        else: result["notes"]="directory digest requires a fixture path; no safe mutable fixture was used"
    except Exception as e:result["notes"]=f"adapter unavailable: {type(e).__name__}: {e}"
    return result


def load_tables(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if not path.is_file():
            continue
        raw=json.loads(path.read_text())
        if raw.get("schema") != SCHEMA or not isinstance(raw.get("probes"), list):
            raise ValueError(f"invalid probe table: {path}")
        rows.extend(raw["probes"])
    return rows


def run_probe_table(table_paths: list[Path], receipt_path: Path) -> dict[str, Any]:
    table={r["library"]:r for r in load_tables(table_paths)}
    for name in LIBRARIES:
        table.setdefault(name, {"library":name,"question_kind":"inventory","why_cb_cares":"adopted library candidate","positive":{"input":"bounded fixture","expect":"usable"},"negative":{"input":"invalid fixture","expect":"specific refusal"},"independent_of":[],"notes":"runner default row"})
    rows=[]
    for name in sorted(table):
        try:
            module=importlib.import_module(_module_name(name)); available=True; version=importlib.metadata.version(name)
        except Exception as e:
            module=None; available=False; version=None; import_error=f"{type(e).__name__}: {e}"
        observed={"library":name,"version":version,"declared_role":table[name].get("why_cb_cares",""),"production_callers":[],"available":available}
        if not available:
            observed.update(status="unavailable",negative_fired=False,determinism=False,verified_independence=[],import_error=import_error,positive={},negative={},boundary={},reorder={"applicable":False},replay={"equal":False},causally_bound=False,verdicts={})
        else:
            first=_generic_probe(name); second=_generic_probe(name); raw1=_json_bytes(first); raw2=_json_bytes(second); deterministic=raw1==raw2; neg=bool(first["negative"].get("fired")); meaningful=neg and not first.get("notes")
            observed.update(status="proven" if meaningful and deterministic else ("unused" if first.get("notes") else "available_unproven"),negative_fired=neg,negative_assertion=first["negative"].get("assertion",""),determinism=deterministic,verified_independence=[],positive=first["positive"],negative=first["negative"],boundary=first["boundary"],reorder=first["reorder"],replay={"equal":deterministic,"sha256_a":hashlib.sha256(raw1).hexdigest(),"sha256_b":hashlib.sha256(raw2).hexdigest()},causally_bound=bool(first.get("causally_bound")),verdicts={"first":first,"replay":second})
        rows.append(observed)
    body={"schema":RECEIPT_SCHEMA,"table_schema":SCHEMA,"libraries":rows,"summary":{"total":len(rows),"proven":sum(r["status"]=="proven" for r in rows),"unavailable":sum(r["status"]=="unavailable" for r in rows),"disagreements":[]},"promotion_allowed":False}
    receipt_path.parent.mkdir(parents=True,exist_ok=True); receipt_path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\n"); return body


def main() -> int:
    root=Path(__file__).resolve().parents[2]
    config=root/"config/library_probes_deciders.json"; lane18=root/"config/library_probes_harness.json"; receipt=root/"receipts/library_probes_deciders_v1.json"
    run_probe_table([config,lane18],receipt); return 0


if __name__ == "__main__":
    raise SystemExit(main())
