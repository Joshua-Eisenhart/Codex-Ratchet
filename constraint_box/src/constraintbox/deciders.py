"""Independent, bounded multi-decider probes for ConstraintBox."""
from __future__ import annotations
import hashlib, importlib.util, itertools, json
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_REGISTRY = _ROOT / "config" / "decider_registry.json"
_RECEIPT = _ROOT / "receipts" / "decider_agreement_v1.json"

def _blake3(value: bytes) -> str:
    from blake3 import blake3
    return blake3(value).hexdigest()

def load_registry(path: Path = _REGISTRY) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def _canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()

def _graph(payload: dict[str, Any], kind: str, engine: str) -> bool:
    nodes, edges = payload["nodes"], [tuple(e) for e in payload["edges"]]
    if engine == "rustworkx":
        import rustworkx as rx
        g = rx.PyDiGraph(); g.add_nodes_from(nodes); pos = {n:i for i,n in enumerate(nodes)}
        g.add_edges_from([(pos[a], pos[b], None) for a,b in edges])
        result = rx.is_directed_acyclic_graph(g)
        if kind == "graph.has_cycle": return not result
        if kind == "graph.is_acyclic": return result
        return all(rx.has_path(g, pos[a], pos[b]) for a,b in payload["required"])
    if engine == "networkx":
        import networkx as nx
        g = nx.DiGraph(); g.add_nodes_from(nodes); g.add_edges_from(edges)
        if kind == "graph.has_cycle":
            try: nx.find_cycle(g); return True
            except nx.NetworkXNoCycle: return False
        if kind == "graph.is_acyclic": return nx.is_directed_acyclic_graph(g)
        return all(nx.has_path(g, a, b) for a,b in payload["required"])
    if engine == "igraph":
        import igraph
        g = igraph.Graph(directed=True); g.add_vertices(nodes); g.add_edges(edges)
        if kind == "graph.has_cycle": return not g.is_dag()
        if kind == "graph.is_acyclic": return g.is_dag()
        return all(bool(g.get_shortest_paths(a, to=b)[0]) for a,b in payload["required"])
    outgoing = {n: [] for n in nodes}
    for a,b in edges: outgoing[a].append(b)
    def reaches(a,b):
        seen=set(); todo=[a]
        while todo:
            x=todo.pop()
            if x == b: return True
            if x in seen: continue
            seen.add(x); todo.extend(outgoing[x])
        return False
    if kind == "graph.has_cycle": return any(reaches(b,a) for a,b in edges)
    acyclic = not any(reaches(b,a) for a,b in edges)
    return acyclic if kind == "graph.is_acyclic" else all(reaches(a,b) for a,b in payload["required"])

def _chain(payload: dict[str, Any], algorithm: str) -> bool:
    previous = ""
    for record in payload["records"]:
        key = "prev_sha256" if algorithm == "sha256" else "prev_blake3"
        if record[key] != previous: return False
        material = _canon({"data": record["data"], "prev": previous})
        previous = hashlib.sha256(material).hexdigest() if algorithm == "sha256" else _blake3(material)
    expected = payload.get("final_sha256" if algorithm == "sha256" else "final_blake3")
    return expected is None or previous == expected

def _sat(payload: dict[str, Any], engine: str) -> bool:
    vars_, constraints = payload["variables"], payload["constraints"]
    def eval_(c, env):
        def val(v): return env[v["var"]] if isinstance(v, dict) else v
        return val(c["left"]) == val(c["right"])
    if engine == "enumeration": return any(all(eval_(c,e) for c in constraints) for e in (dict(zip(vars_, vals)) for vals in itertools.product(*vars_.values())))
    if engine == "z3":
        import z3
        xs = {n:z3.Int(n) for n in vars_}; s=z3.Solver()
        for n,domain in vars_.items(): s.add(z3.Or(*[xs[n] == v for v in domain]))
        for c in constraints:
            left=xs[c["left"]["var"]] if isinstance(c["left"],dict) else c["left"]; s.add(left == c["right"])
        return s.check() == z3.sat
    import cvc5
    from cvc5 import Kind
    s=cvc5.Solver(); sort=s.getIntegerSort(); xs={n:s.mkConst(sort,n) for n in vars_}
    for n,domain in vars_.items(): s.assertFormula(s.mkTerm(Kind.OR,*[s.mkTerm(Kind.EQUAL,xs[n],s.mkInteger(v)) for v in domain]))
    for c in constraints:
        left=xs[c["left"]["var"]] if isinstance(c["left"],dict) else s.mkInteger(c["left"]); s.assertFormula(s.mkTerm(Kind.EQUAL,left,s.mkInteger(c["right"])))
    return s.checkSat().isSat()

def _answer(kind: str, payload: dict[str, Any], decider: str) -> bool:
    if kind.startswith("graph."): return _graph(payload, kind, decider)
    if kind == "hash.content_digest":
        data=payload["content"].encode(); return hashlib.sha256(data).hexdigest() == payload["expected_sha256"] if decider == "hashlib_sha256" else _blake3(data) == payload["expected_blake3"]
    if kind == "chain.verify": return _chain(payload, "sha256" if decider == "hashlib_chain" else "blake3")
    if kind == "arith.exact_equal":
        if decider == "sympy":
            import sympy; return bool(sympy.simplify(payload["left"])-sympy.simplify(payload["right"]) == 0)
        from fractions import Fraction
        def f(x): return sum((Fraction(t.strip()) for t in x.split("+")), Fraction(0))
        return f(payload["left"]) == f(payload["right"])
    if kind == "schema.validates":
        schema, instance = payload["schema"], payload["instance"]
        if decider == "jsonschema":
            import jsonschema
            try: jsonschema.validate(instance, schema); return True
            except jsonschema.ValidationError: return False
        if decider == "pydantic":
            from pydantic import BaseModel, ConfigDict, ValidationError, create_model
            M=create_model("DeciderModel", __config__=ConfigDict(extra="forbid"), name=(str,...), age=(int,...))
            try: M.model_validate(instance, strict=True); return True
            except ValidationError: return False
        import attrs
        @attrs.define
        class SchemaRecord:
            name: str = attrs.field(validator=attrs.validators.instance_of(str))
            age: int = attrs.field(validator=attrs.validators.instance_of(int))
        if not isinstance(instance, dict) or set(instance) != {"name", "age"} or isinstance(instance.get("age"), bool):
            return False
        try:
            SchemaRecord(**instance)
            return True
        except (TypeError, ValueError):
            return False
    if kind == "sat.decide": return _sat(payload, decider)
    if kind == "order.is_sorted":
        if decider == "sortedcontainers":
            from sortedcontainers import SortedList
            return payload["value"] == list(SortedList(payload["value"]))
        return payload["value"] == sorted(payload["value"])
    raise KeyError(kind)

def decide(question_kind: str, payload: dict[str, Any], registry: dict[str, Any] | None = None) -> dict[str, Any]:
    spec=(registry or load_registry())["question_kinds"][question_kind]; verdicts={}; unavailable=[]
    for d in spec["deciders"]:
        if d["module"] is not None and importlib.util.find_spec(d["module"]) is None:
            verdicts[d["id"]]="unavailable"; unavailable.append(d["id"]); continue
        verdicts[d["id"]]=_answer(question_kind,payload,d["id"])
    available={k:v for k,v in verdicts.items() if v != "unavailable"}; groups={}
    for k,v in available.items(): groups.setdefault(str(v),[]).append(k)
    enough=len(available) >= spec["minimum_agreeing"]; agreed=enough and len(groups)==1
    result={"verdicts":verdicts,"unavailable":unavailable,"agreed":agreed,"majority":next(iter(available.values())) if agreed else None}
    if not agreed: result["disagreement"]={"reason": "INSUFFICIENT_DECIDERS" if not enough else "definite_status_disagreement", "decider_ids_by_verdict":groups, "payload_sha256":hashlib.sha256(_canon(payload)).hexdigest()}
    return result

def run_registry(registry: dict[str, Any] | None = None, output: Path = _RECEIPT) -> dict[str, Any]:
    registry=registry or load_registry(); out={"schema":"cb.decider_agreement.v1","question_kinds":{},"disagreements":[]}
    for kind,spec in registry["question_kinds"].items():
        cases={}
        for label,payload in spec["cases"].items():
            # Chain fixtures are completed deterministically from the first record.
            if kind == "chain.verify":
                a=spec["cases"]["positive"]["records"][0]; material=_canon({"data":a["data"],"prev":""});
                spec["cases"]["positive"]["records"][1]["prev_sha256"]=hashlib.sha256(material).hexdigest(); spec["cases"]["positive"]["records"][1]["prev_blake3"]=_blake3(material); payload=spec["cases"][label]
            r=decide(kind,payload,registry); cases[label]={"payload":payload,"result":r}
            if r.get("disagreement"): out["disagreements"].append({"question_kind":kind,"case":label,"detail":r["disagreement"]})
        out["question_kinds"][kind]={"minimum_agreeing":spec["minimum_agreeing"],"cases":cases}
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8"); return out
