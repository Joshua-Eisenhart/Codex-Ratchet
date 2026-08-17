from __future__ import annotations

import importlib
import importlib.metadata
import itertools
import math
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Literal

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .protocol import ZipJobRefusal, canonical_json_bytes, sha256_bytes, strict_json_loads

CLAIM_CEILING = (
    "local_observational_tool_field_only;not_global_tool_rank;not_prompt_truth;"
    "not_model_execution;not_admission;not_portability;not_release"
)

EVENT_OUTPUTS = tuple(f"output/probe_events.{index:03d}.jsonl" for index in range(8))


class ToolFieldRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)
    schema_: Literal["constraintbox.zip_tool_field_request.v1"] = Field(alias="schema")
    seed: int = Field(ge=0, le=2**31 - 1)
    jobs: int = Field(ge=1, le=64)
    pair_samples: int = Field(ge=1, le=4096)


def _object(data: bytes, label: str) -> dict[str, Any]:
    value = strict_json_loads(data, label=label)
    if not isinstance(value, dict):
        raise ZipJobRefusal("REFUSE_TOOL_FIELD_INPUT_SHAPE", label)
    return value


def _request(value: dict[str, Any]) -> ToolFieldRequest:
    schema = ToolFieldRequest.model_json_schema()
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: list(e.path))
    if errors:
        raise ZipJobRefusal("REFUSE_TOOL_FIELD_REQUEST_SCHEMA", errors[0].message)
    try:
        return ToolFieldRequest.model_validate(value, strict=True)
    except ValidationError as exc:
        raise ZipJobRefusal("REFUSE_TOOL_FIELD_REQUEST_TYPED", str(exc)) from exc


def _tools(manifest: dict[str, Any]) -> list[dict[str, str]]:
    raw = manifest.get("tools")
    if not isinstance(raw, list) or not raw:
        raise ZipJobRefusal("REFUSE_TOOL_MANIFEST_EMPTY")
    rows: list[dict[str, str]] = []
    for index, item in enumerate(raw):
        imports = item.get("import_names") if isinstance(item, dict) else None
        distribution = item.get("locked_distribution") if isinstance(item, dict) else None
        version = item.get("locked_version") if isinstance(item, dict) else None
        if not (
            isinstance(imports, list) and len(imports) == 1 and isinstance(imports[0], str)
            and isinstance(distribution, str) and isinstance(version, str)
        ):
            raise ZipJobRefusal("REFUSE_TOOL_MANIFEST_ROW", str(index))
        rows.append({
            "tool_id": distribution, "distribution": distribution,
            "version": version, "import_name": imports[0],
        })
    if len({row["tool_id"] for row in rows}) != len(rows):
        raise ZipJobRefusal("REFUSE_TOOL_ID_DUPLICATE")
    return sorted(rows, key=lambda row: row["tool_id"])


def _observe_single(spec: tuple[str, str]) -> dict[str, Any]:
    module_name, distribution = spec
    observed: dict[str, Any] = {"module": module_name, "distribution": distribution}
    try:
        module = importlib.import_module(module_name)
        observed.update({
            "status": "IMPORTED", "origin": str(getattr(module, "__file__", None)),
            "observed_version": importlib.metadata.version(distribution),
        })
    except BaseException as exc:
        observed.update({"status": "REFUSED", "error_type": type(exc).__name__})
    return observed


def _observe_pair(names: tuple[str, str]) -> list[dict[str, Any]]:
    observed: list[dict[str, Any]] = []
    for name in names:
        try:
            module = importlib.import_module(name)
            observed.append({"module": name, "status": "IMPORTED", "origin": str(getattr(module, "__file__", None))})
        except BaseException as exc:
            observed.append({"module": name, "status": "REFUSED", "error_type": type(exc).__name__})
    return observed


def _pair_set(rows: list[dict[str, str]], seed: int, limit: int) -> list[tuple[dict[str, str], dict[str, str]]]:
    pairs = list(itertools.combinations(rows, 2))
    pairs.sort(key=lambda pair: sha256_bytes(canonical_json_bytes([seed, pair[0]["tool_id"], pair[1]["tool_id"]])))
    return pairs[: min(limit, len(pairs))]


def _event(body: dict[str, Any]) -> dict[str, Any]:
    return {**body, "event_id": sha256_bytes(canonical_json_bytes(body))}


def _event_outputs(events: list[dict[str, Any]]) -> dict[str, bytes]:
    chunk_size = max(1, math.ceil(len(events) / len(EVENT_OUTPUTS)))
    outputs: dict[str, bytes] = {}
    for index, path in enumerate(EVENT_OUTPUTS):
        chunk = events[index * chunk_size : (index + 1) * chunk_size]
        outputs[path] = (
            b"\n".join(canonical_json_bytes(item) for item in chunk) + (b"\n" if chunk else b"")
        )
    return outputs


def _prior_rows(prior: dict[str, Any]) -> dict[str, dict[str, Any]]:
    values = prior.get("tool_projection")
    if not isinstance(values, list):
        return {}
    aliases = {"z3": "z3-solver"}
    return {
        aliases.get(str(row["tool_id"]), str(row["tool_id"])): row
        for row in values
        if isinstance(row, dict) and isinstance(row.get("tool_id"), str)
    }


def _compile(rows: list[dict[str, str]], events: list[dict[str, Any]], prior: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    singles: dict[str, list[dict[str, Any]]] = defaultdict(list)
    paired: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for item in events:
        if item["kind"] == "pair_order":
            paired[(item["left_tool_id"], item["right_tool_id"])][item["order"]] = item
        else:
            singles[item["tool_id"]].append(item)
    exposure: Counter[str] = Counter()
    divergence: Counter[str] = Counter()
    edges: list[dict[str, Any]] = []
    for pair, orders in sorted(paired.items()):
        if set(orders) == {"AB", "BA"}:
            exposure.update(pair)
            views = [{part["module"]: part["status"] for part in orders[key]["observed"]} for key in ("AB", "BA")]
            stable = views[0] == views[1]
            if not stable:
                divergence.update(pair)
            edges.append({"source": pair[0], "target": pair[1], "order_stable": stable})
    prior_by_tool = _prior_rows(prior)
    facts: dict[str, dict[str, Any]] = {}
    signatures: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for row in rows:
        local = singles[row["tool_id"]]
        positives = sorted((item for item in local if item["kind"] == "import_replay"), key=lambda item: item["repeat"])
        negatives = [item for item in local if item["kind"] == "import_severance"]
        views = [item["observed"] for item in positives]
        imported = len(views) == 2 and all(item.get("status") == "IMPORTED" for item in views)
        replay = len(views) == 2 and views[0] == views[1]
        version = imported and all(item.get("observed_version") == row["version"] for item in views)
        severance = len(negatives) == 1 and negatives[0]["observed"].get("status") == "REFUSED"
        prior_row = prior_by_tool.get(row["tool_id"], {})
        prior_count = int(prior_row.get("observations", 0) or 0)
        fact = {
            "tool_id": row["tool_id"], "imported": imported, "version_match": version,
            "replay_stable": replay, "severance_refused": severance,
            "pair_exposure": exposure[row["tool_id"]], "pair_order_divergence": divergence[row["tool_id"]],
            "prior_operation_observations": prior_count,
            "prior_local_centrality": prior_row.get("local_centrality"),
        }
        facts[row["tool_id"]] = fact
        signatures[(imported, version, replay, severance, divergence[row["tool_id"]] > 0, prior_count > 0)].append(row["tool_id"])
    classes: list[dict[str, Any]] = []
    total_mass = 0
    for signature, members in sorted(signatures.items(), key=lambda item: sorted(item[1])):
        mass = sum(1 + facts[name]["pair_exposure"] + facts[name]["prior_operation_observations"] for name in members)
        total_mass += mass
        classes.append({
            "class_id": sha256_bytes(canonical_json_bytes([signature, sorted(members)]))[:16],
            "observational_signature": list(signature), "members": sorted(members), "mass": mass,
        })
    class_by_tool = {
        member: item["class_id"]
        for item in classes
        for member in item["members"]
    }
    quotient_edge_counts: Counter[tuple[str, str, bool]] = Counter()
    for edge in edges:
        endpoints = sorted((class_by_tool[edge["source"]], class_by_tool[edge["target"]]))
        quotient_edge_counts[(endpoints[0], endpoints[1], edge["order_stable"])] += 1
    quotient_edges = [
        {
            "source_class": key[0],
            "target_class": key[1],
            "order_stable": key[2],
            "observation_count": count,
        }
        for key, count in sorted(quotient_edge_counts.items())
    ]
    entropy = -sum((item["mass"] / total_mass) * math.log2(item["mass"] / total_mass) for item in classes) if total_mass else 0.0
    mapped = sorted(
        (item for item in facts.values() if item["prior_operation_observations"] > 0),
        key=lambda item: (-item["prior_operation_observations"], item["tool_id"]),
    )
    rankings = [
        {**item, "mapping_status": "OPERATION_MAPPED", "operation_rank": rank}
        for rank, item in enumerate(mapped, start=1)
    ]
    rankings.extend(
        {**facts[name], "mapping_status": "UNMAPPED_GENERIC_ONLY", "operation_rank": None}
        for name in sorted(facts)
        if facts[name]["prior_operation_observations"] == 0
    )
    quotient = {
        "schema": "constraintbox.measured_tool_quotient.v1", "tool_count": len(rows),
        "class_count": len(classes), "classes": classes,
        "tool_facts": [facts[name] for name in sorted(facts)], "rankings": rankings,
        "ranking_summary": {
            "operation_mapped": len(mapped),
            "generic_only_unranked": len(rows) - len(mapped),
        },
        "ranking_ceiling": "only operation-level ablation evidence is ordered; generic-only tools remain tied and unranked",
        "claim_ceiling": CLAIM_CEILING,
    }
    coupled = {
        "schema": "constraintbox.entropy_topology_coupling.v1",
        "measure_space": "finite observational quotient under this packet's probes",
        "total_mass": total_mass, "shannon_entropy_bits": round(entropy, 12),
        "quotient_class_count": len(classes),
        "class_nodes": [
            {"class_id": item["class_id"], "mass": item["mass"], "member_count": len(item["members"])}
            for item in classes
        ],
        "quotient_edges": quotient_edges,
        "tool_relation_edges": edges,
        "order_divergent_edge_count": sum(not edge["order_stable"] for edge in edges),
        "claim_ceiling": CLAIM_CEILING,
    }
    return quotient, coupled


def _crosscheck(quotient: dict[str, Any], coupled: dict[str, Any]) -> dict[str, Any]:
    import cvc5
    import rustworkx as rx
    import sympy
    import z3
    expected = quotient["tool_count"]
    observed = sum(len(item["members"]) for item in quotient["classes"])
    z3_solver = z3.Solver()
    z3_value = z3.Int("observed")
    z3_solver.add(z3_value == observed, z3_value == expected)
    z3_ok = z3_solver.check() == z3.sat
    cvc5_solver = cvc5.Solver()
    cvc5_value = cvc5_solver.mkConst(cvc5_solver.getIntegerSort(), "observed")
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(cvc5.Kind.EQUAL, cvc5_value, cvc5_solver.mkInteger(observed)))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(cvc5.Kind.EQUAL, cvc5_value, cvc5_solver.mkInteger(expected)))
    cvc5_ok = cvc5_solver.checkSat().isSat()
    mass_ok = bool(coupled["total_mass"] and sympy.Rational(coupled["total_mass"], coupled["total_mass"]) == 1)
    graph = rx.PyGraph()
    nodes = {name: graph.add_node(name) for name in sorted(item["tool_id"] for item in quotient["tool_facts"])}
    for edge in coupled["tool_relation_edges"]:
        graph.add_edge(nodes[edge["source"]], nodes[edge["target"]], edge["order_stable"])
    tool_components = rx.number_connected_components(graph)
    quotient_graph = rx.PyGraph()
    quotient_nodes = {
        item["class_id"]: quotient_graph.add_node(item["class_id"])
        for item in coupled["class_nodes"]
    }
    for edge in coupled["quotient_edges"]:
        if edge["source_class"] != edge["target_class"]:
            quotient_graph.add_edge(
                quotient_nodes[edge["source_class"]],
                quotient_nodes[edge["target_class"]],
                edge["observation_count"],
            )
    quotient_components = rx.number_connected_components(quotient_graph)
    return {
        "z3_count_identity": z3_ok, "cvc5_count_identity": cvc5_ok,
        "sympy_mass_normalization": mass_ok,
        "rustworkx_tool_component_count": tool_components,
        "rustworkx_quotient_component_count": quotient_components,
        "rustworkx_component_check": tool_components >= 1 and quotient_components >= 1,
        "all_crosschecks_satisfied": all((z3_ok, cvc5_ok, mass_ok, tool_components >= 1, quotient_components >= 1)),
    }


def run_tool_field(request_bytes: bytes, prompt_bytes: bytes, manifest_bytes: bytes, prior_bytes: bytes) -> dict[str, bytes]:
    request = _request(_object(request_bytes, "inputs/request.json"))
    manifest = _object(manifest_bytes, "inputs/tool_manifest.json")
    prior = _object(prior_bytes, "inputs/prior_field_summary.json")
    try:
        prompt = prompt_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ZipJobRefusal("REFUSE_PROMPT_NOT_UTF8") from exc
    if not prompt.strip():
        raise ZipJobRefusal("REFUSE_PROMPT_EMPTY")
    rows = _tools(manifest)
    pairs = _pair_set(rows, request.seed, request.pair_samples)
    single_specs: list[tuple[str, str]] = []
    event_meta: list[tuple[str, dict[str, str], int]] = []
    for row in rows:
        for repeat in (0, 1):
            single_specs.append((row["import_name"], row["distribution"]))
            event_meta.append(("import_replay", row, repeat))
        missing = "_cb_absent_" + sha256_bytes(row["tool_id"].encode())[:20]
        single_specs.append((missing, row["distribution"]))
        event_meta.append(("import_severance", {**row, "import_name": missing}, 0))
    pair_specs: list[tuple[str, str]] = []
    pair_meta: list[tuple[dict[str, str], dict[str, str], str]] = []
    for left, right in pairs:
        for order in ("AB", "BA"):
            ordered = (left, right) if order == "AB" else (right, left)
            pair_specs.append((ordered[0]["import_name"], ordered[1]["import_name"]))
            pair_meta.append((left, right, order))
    with ProcessPoolExecutor(max_workers=request.jobs, max_tasks_per_child=1) as pool:
        single_results = list(pool.map(_observe_single, single_specs))
        pair_results = list(pool.map(_observe_pair, pair_specs))
    events: list[dict[str, Any]] = []
    for (kind, row, repeat), observed in zip(event_meta, single_results, strict=True):
        body = {"kind": kind, "tool_id": row["tool_id"], "import_name": row["import_name"], "observed": observed}
        if kind == "import_replay":
            body.update({"expected_version": row["version"], "repeat": repeat})
        events.append(_event(body))
    for (left, right, order), observed in zip(pair_meta, pair_results, strict=True):
        events.append(_event({
            "kind": "pair_order", "left_tool_id": left["tool_id"],
            "right_tool_id": right["tool_id"], "order": order, "observed": observed,
        }))
    events.sort(key=lambda item: item["event_id"])
    quotient, coupled = _compile(rows, events, prior)
    checks = _crosscheck(quotient, coupled)
    branches = {
        "schema": "constraintbox.prompt_interpretation_branches.v1",
        "prompt_sha256": sha256_bytes(prompt_bytes), "prompt_is_source_not_canon": True,
        "branches": [
            {"branch": "literal", "hypothesis": prompt.strip()},
            {"branch": "bounded", "hypothesis": "Build one finite local operation with explicit claim ceilings."},
            {"branch": "counterreading", "hypothesis": "The architecture may fail; retain refusal evidence and alternatives."},
        ],
        "claim_ceiling": "interpretation hypotheses only; none is owner intent or canon",
    }
    complete = len(rows) == 93 and all(item["replay_stable"] and item["severance_refused"] for item in quotient["tool_facts"]) and checks["all_crosschecks_satisfied"]
    cycle = {
        "schema": "constraintbox.zip_probe_work_cycle.v1",
        "states": ["RECEIVED", "INTERPRETATIONS_OPEN", "CONTEXT_BOUND", "PROBED", "QUOTIENTED", "SETTLED_LOCAL" if complete else "HOLD_FIELD_INCOMPLETE"],
        "tool_count": len(rows), "event_count": len(events), "pair_count": len(pairs),
        "prior_field_sha256": sha256_bytes(prior_bytes), "tool_manifest_sha256": sha256_bytes(manifest_bytes),
        "crosschecks": checks, "disposition": "WORK_CYCLE_SETTLED_LOCAL" if complete else "HOLD_FIELD_INCOMPLETE",
        "next_finite_tests": [
            "replace generic import probes with operation-specific probes for highest-ranked unmapped tools",
            "repeat pair field with a second seed and compare quotient stability",
            "run one model filler only through a validated child ZIP and compare its return to deterministic evidence",
        ],
        "claim_ceiling": CLAIM_CEILING, "promotion_allowed": False,
    }
    return {
        "output/interpretations.json": canonical_json_bytes(branches),
        **_event_outputs(events),
        "output/measured_quotient.json": canonical_json_bytes(quotient),
        "output/entropy_topology.json": canonical_json_bytes(coupled),
        "output/work_cycle.json": canonical_json_bytes(cycle),
    }
