import copy
import hashlib
import json
import re

from a1_strategy import canonical_strategy_bytes, validate_strategy
from containers import build_export_block
from state import KernelState


COMPILER_VERSION = "A0_COMPILER_v2"
_KIND_PRIORITY = {"MATH_DEF": 0, "TERM_DEF": 1, "LABEL_DEF": 2, "CANON_PERMIT": 3, "SIM_SPEC": 4}
_PROBE_ID_RE = re.compile(r"^P_[A-Za-z0-9_]+$")
_REJECT_REPAIR_OPERATOR_MAP = {
    "FORWARD_DEPEND": ("OP_REORDER_DEPENDENCIES",),
    "DERIVED_ONLY": ("OP_MUTATE_LEXEME",),
    "DERIVED_ONLY_PRIMITIVE_USE": ("OP_MUTATE_LEXEME",),
    "UNDEFINED_TERM_USE": ("OP_MUTATE_LEXEME",),
    "SIM_FAIL_KILL": ("OP_NEG_SIM_EXPAND",),
    "SCHEMA_FAIL": ("OP_REPAIR_DEF_FIELD",),
    "PROBE_PRESSURE": ("OP_INJECT_PROBE",),
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _set_def_field(candidate: dict, name: str, value_kind: str, value: str) -> None:
    for row in candidate.get("def_fields", []):
        if str(row.get("name", "")).upper() == name:
            row["value_kind"] = value_kind
            row["value"] = value
            return
    candidate.setdefault("def_fields", []).append(
        {
            "field_id": f"F_{name}_{len(candidate.get('def_fields', [])) + 1:02d}",
            "name": name,
            "value_kind": value_kind,
            "value": value,
        }
    )


def _get_def_field(candidate: dict, name: str) -> str:
    for row in candidate.get("def_fields", []):
        if str(row.get("name", "")).upper() == name:
            return str(row.get("value", "")).strip()
    return ""


def _set_assert_token(candidate: dict, token_class: str, token: str) -> None:
    token_class = token_class.upper()
    for row in candidate.get("asserts", []):
        if str(row.get("token_class", "")).upper() == token_class:
            row["token"] = token
            return
    candidate.setdefault("asserts", []).append(
        {
            "assert_id": f"A_{token_class}_{len(candidate.get('asserts', [])) + 1:02d}",
            "token_class": token_class,
            "token": token,
        }
    )


def _apply_operator_inject_probe(strategy: dict) -> int:
    changed = 0
    for lane in ["targets", "alternatives"]:
        for candidate in strategy.get(lane, []):
            if str(candidate.get("kind", "")).upper() != "SIM_SPEC":
                continue
            requires = [str(x).strip() for x in candidate.get("requires", []) if str(x).strip()]
            if any(_PROBE_ID_RE.match(dep) for dep in requires):
                continue
            probe_id = f"P_{str(candidate.get('id', 'S_AUTO')).strip()}"
            candidate["requires"] = [probe_id] + requires
            _set_assert_token(candidate, "PROBE_TOKEN", f"PT_{probe_id}")
            _set_def_field(candidate, "PROBE_KIND", "TOKEN", "A1_GENERATED")
            changed += 1
    return changed


def _apply_operator_reorder_dependencies(strategy: dict) -> int:
    changed = 0
    for lane in ["targets", "alternatives"]:
        for candidate in strategy.get(lane, []):
            before = [str(x).strip() for x in candidate.get("requires", []) if str(x).strip()]
            after = sorted(set(before))
            if before != after:
                candidate["requires"] = after
                changed += 1
    return changed


def _apply_operator_mutate_lexeme(strategy: dict) -> int:
    changed = 0
    for lane in ["targets", "alternatives"]:
        for candidate in strategy.get(lane, []):
            for row in candidate.get("def_fields", []):
                name = str(row.get("name", "")).upper()
                if name not in {"TERM", "LABEL", "OBJECTS", "OPERATIONS", "INVARIANTS"}:
                    continue
                value = str(row.get("value", ""))
                normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
                if normalized and normalized != value:
                    row["value"] = normalized
                    changed += 1
    return changed


def _apply_operator_repair_def_field(strategy: dict) -> int:
    changed = 0
    for lane in ["targets", "alternatives"]:
        for candidate in strategy.get(lane, []):
            candidate.setdefault("requires", [])
            candidate.setdefault("def_fields", [])
            candidate.setdefault("asserts", [])
            if str(candidate.get("kind", "")).upper() != "SIM_SPEC":
                continue
            evidence = _get_def_field(candidate, "REQUIRES_EVIDENCE")
            if not evidence:
                evidence = f"E_{str(candidate.get('id', 'S_AUTO')).strip()}"
                _set_def_field(candidate, "REQUIRES_EVIDENCE", "TOKEN", evidence)
                changed += 1
            if not _get_def_field(candidate, "SIM_ID"):
                _set_def_field(candidate, "SIM_ID", "TOKEN", str(candidate.get("id", "S_AUTO")))
                changed += 1
            if not _get_def_field(candidate, "TIER"):
                _set_def_field(candidate, "TIER", "TOKEN", "T0_ATOM")
                changed += 1
            if not _get_def_field(candidate, "FAMILY"):
                _set_def_field(candidate, "FAMILY", "TOKEN", "BASELINE")
                changed += 1
            if not _get_def_field(candidate, "TARGET_CLASS"):
                _set_def_field(candidate, "TARGET_CLASS", "TOKEN", str(candidate.get("id", "S_AUTO")))
                changed += 1
            _set_assert_token(candidate, "EVIDENCE_TOKEN", evidence)
    return changed


def _apply_operator_neg_sim_expand(strategy: dict) -> int:
    changed = 0
    if not strategy.get("targets"):
        return changed
    if not strategy.get("alternatives"):
        alt = copy.deepcopy(strategy["targets"][0])
        alt["id"] = f"{str(alt.get('id', 'S_AUTO')).strip()}_ALT"
        alt["operator_id"] = "OP_NEG_SIM_EXPAND"
        strategy["alternatives"] = [alt]
        changed += 1
    for candidate in strategy.get("alternatives", []):
        if str(candidate.get("kind", "")).upper() == "SIM_SPEC":
            if not _get_def_field(candidate, "NEGATIVE_CLASS"):
                _set_def_field(candidate, "NEGATIVE_CLASS", "TOKEN", "NEG_BOUNDARY")
                changed += 1
    sims = strategy.setdefault("sims", {"positive": [], "negative": []})
    positive = sims.setdefault("positive", [])
    negative = sims.setdefault("negative", [])
    for candidate in strategy.get("targets", []):
        bind_id = str(candidate.get("id", "")).strip()
        if bind_id and not any(row.get("binds_to") == bind_id for row in positive):
            positive.append({"sim_id": f"SIM_POS_{bind_id}", "binds_to": bind_id})
            changed += 1
    for candidate in strategy.get("alternatives", []):
        bind_id = str(candidate.get("id", "")).strip()
        if bind_id and not any(row.get("binds_to") == bind_id for row in negative):
            negative.append({"sim_id": f"SIM_NEG_{bind_id}", "binds_to": bind_id})
            changed += 1
    return changed


_OPERATOR_IMPL = {
    "OP_INJECT_PROBE": _apply_operator_inject_probe,
    "OP_REORDER_DEPENDENCIES": _apply_operator_reorder_dependencies,
    "OP_MUTATE_LEXEME": _apply_operator_mutate_lexeme,
    "OP_REPAIR_DEF_FIELD": _apply_operator_repair_def_field,
    "OP_NEG_SIM_EXPAND": _apply_operator_neg_sim_expand,
}


def _apply_repairs(strategy: dict, prior_tags: list[str]) -> tuple[dict, list[dict]]:
    repaired = copy.deepcopy(strategy)
    actions: list[dict] = []
    for tag in sorted(set(prior_tags)):
        operators = _REJECT_REPAIR_OPERATOR_MAP.get(tag, ())
        if not operators:
            continue
        for operator in operators:
            impl = _OPERATOR_IMPL.get(operator)
            changed = impl(repaired) if impl else 0
            actions.append({"tag": tag, "operator_id": operator, "changed": changed})
            # Deterministic single-operator per tag.
            break
    return repaired, actions


def _candidate_rows(strategy: dict) -> list[tuple[int, dict]]:
    rows: list[tuple[int, dict]] = []
    for candidate in strategy.get("targets", []):
        rows.append((0, candidate))
    for candidate in strategy.get("alternatives", []):
        rows.append((1, candidate))
    rows.sort(
        key=lambda row: (
            row[0],
            _KIND_PRIORITY.get(str(row[1].get("kind", "")).upper(), 99),
            str(row[1].get("id", "")),
        )
    )
    return rows


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def compile_export_block(
    state: KernelState,
    strategy: dict,
    canonical_state_hash: str,
    step: int,
    prior_tags: list[str] | None = None,
) -> dict:
    prior_tags = prior_tags or []
    normalized = copy.deepcopy(strategy)
    normalized.setdefault("self_audit", {})
    normalized["self_audit"]["candidate_count"] = len(normalized.get("targets", []))
    normalized["self_audit"]["alternative_count"] = len(normalized.get("alternatives", []))
    normalized["self_audit"]["operator_ids_used"] = sorted(
        {
            str(candidate.get("operator_id", "")).strip()
            for _, candidate in _candidate_rows(normalized)
            if str(candidate.get("operator_id", "")).strip()
        }
    )
    validation_errors = validate_strategy(normalized)
    if validation_errors:
        raise ValueError("invalid_a1_strategy:" + ";".join(validation_errors))
    repaired, repair_actions = _apply_repairs(normalized, prior_tags)
    exhausted_tags: list[str] = []
    for tag in sorted(set(prior_tags)):
        allowed_ops = _REJECT_REPAIR_OPERATOR_MAP.get(tag, ())
        if not allowed_ops:
            exhausted_tags.append(tag)
            continue
        tag_actions = [row for row in repair_actions if row.get("tag") == tag]
        if not tag_actions:
            exhausted_tags.append(tag)
            continue
        if all(int(row.get("changed", 0)) <= 0 for row in tag_actions):
            exhausted_tags.append(tag)

    # Keep self_audit counts aligned with the repaired lane.
    repaired.setdefault("self_audit", {})
    repaired["self_audit"]["candidate_count"] = len(repaired.get("targets", []))
    repaired["self_audit"]["alternative_count"] = len(repaired.get("alternatives", []))
    repaired["self_audit"]["operator_ids_used"] = sorted(
        {
            str(candidate.get("operator_id", "")).strip()
            for _, candidate in _candidate_rows(repaired)
            if str(candidate.get("operator_id", "")).strip()
        }
    )
    repaired["self_audit"]["strategy_hash"] = ""
    repaired["self_audit"]["strategy_hash"] = _sha256_bytes(canonical_strategy_bytes(repaired))

    lines: list[str] = []
    seen_probes: set[str] = set()
    spec_kind_counts: dict[str, int] = {}
    operator_trace: list[dict] = []

    max_items = int(repaired.get("budget", {}).get("max_items", 1))
    candidate_rows = _candidate_rows(repaired)[:max_items]

    for lane, candidate in candidate_rows:
        item_id = str(candidate.get("id", "")).strip()
        kind = str(candidate.get("kind", "")).upper().strip()
        if not item_id or not kind:
            continue

        requires = [str(x).strip() for x in candidate.get("requires", []) if str(x).strip()]
        def_fields = [dict(x) for x in candidate.get("def_fields", []) if isinstance(x, dict)]
        asserts = [dict(x) for x in candidate.get("asserts", []) if isinstance(x, dict)]

        for dep in requires:
            if not _PROBE_ID_RE.match(dep):
                continue
            if dep in seen_probes:
                continue
            probe_kind = "A1_GENERATED"
            for row in def_fields:
                if str(row.get("name", "")).upper() == "PROBE_KIND":
                    probe_kind = str(row.get("value", "A1_GENERATED")).strip() or "A1_GENERATED"
                    break
            probe_token = f"PT_{dep}"
            for row in asserts:
                if str(row.get("token_class", "")).upper() == "PROBE_TOKEN":
                    probe_token = str(row.get("token", probe_token)).strip() or probe_token
                    break
            lines.extend(
                [
                    f"PROBE_HYP {dep}",
                    f"PROBE_KIND {dep} CORR {probe_kind}",
                    f"ASSERT {dep} CORR EXISTS PROBE_TOKEN {probe_token}",
                ]
            )
            seen_probes.add(dep)

        lines.append(f"SPEC_HYP {item_id}")
        lines.append(f"SPEC_KIND {item_id} CORR {kind}")
        for dep in sorted(set(requires)):
            lines.append(f"REQUIRES {item_id} CORR {dep}")

        for row in def_fields:
            name = str(row.get("name", "")).upper().strip()
            if not name or name == "PROBE_KIND":
                continue
            value = str(row.get("value", "")).strip()
            value_kind = str(row.get("value_kind", "TOKEN")).upper().strip()
            if value_kind in {"TERM_QUOTED", "LABEL_QUOTED", "FORMULA_QUOTED", "QUOTED"}:
                lines.append(f"DEF_FIELD {item_id} CORR {name} {_quote(value)}")
            else:
                lines.append(f"DEF_FIELD {item_id} CORR {name} {value}")

        for row in asserts:
            token_class = str(row.get("token_class", "")).upper().strip()
            token = str(row.get("token", "")).strip()
            if not token_class or not token:
                continue
            lines.append(f"ASSERT {item_id} CORR EXISTS {token_class} {token}")

        spec_kind_counts[kind] = spec_kind_counts.get(kind, 0) + 1
        operator_trace.append(
            {
                "lane": "targets" if lane == 0 else "alternatives",
                "id": item_id,
                "kind": kind,
                "operator_id": str(candidate.get("operator_id", "")).strip(),
            }
        )

    strategy_hash = _sha256_bytes(canonical_strategy_bytes(repaired))
    export_seed = f"{canonical_state_hash}|{strategy_hash}|{COMPILER_VERSION}|{step}"
    export_id = "A0_" + _sha256_bytes(export_seed.encode("utf-8"))[:16].upper()
    export_text = build_export_block(
        export_id=export_id,
        proposal_type="A1_COMPILED_BATCH",
        content_lines=lines,
        version="v1",
        ruleset_sha256=state.active_ruleset_sha256,
        megaboot_sha256=state.active_megaboot_sha256,
    )
    export_bytes = export_text.encode("utf-8")
    report = {
        "compiler_version": COMPILER_VERSION,
        "canonical_state_hash": canonical_state_hash,
        "strategy_hash": strategy_hash,
        "step": step,
        "prior_tags": sorted(set(prior_tags)),
        "repair_actions": repair_actions,
        "operator_exhausted_tags": exhausted_tags,
        "reject_repair_operator_map": {k: list(v) for k, v in sorted(_REJECT_REPAIR_OPERATOR_MAP.items())},
        "operator_trace": operator_trace,
        "spec_count": sum(spec_kind_counts.values()),
        "spec_kind_counts": {k: spec_kind_counts[k] for k in sorted(spec_kind_counts.keys())},
        "probe_count": len(seen_probes),
        "export_id": export_id,
        "export_block_sha256": _sha256_bytes(export_bytes),
    }
    return {"export_text": export_text, "export_bytes": export_bytes, "report": report, "repaired_strategy": repaired}
