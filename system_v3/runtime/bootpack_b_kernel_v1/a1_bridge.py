import hashlib
import json
import os
import re
import zipfile
from copy import deepcopy
from pathlib import Path

from a1_strategy import canonical_strategy_bytes, load_strategy, validate_strategy
from zip_protocol_v2_validator import validate_zip_protocol_v2

_FENCED_JSON_RE = re.compile(r"```json\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
_STEP_SUFFIX_RE = re.compile(r"_S[0-9]{4}$")
_TARGET_CLASS_SUFFIX_RE = re.compile(r"_STEP_[0-9]{4}_C[0-9]{2}$")
_FORBIDDEN_FIELD_KEYS = {"confidence", "probability", "embedding", "hidden_prompt", "raw_text"}
_REPLAY_TERM_SEQUENCE = (
    "density_matrix",
    "cptp_channel",
    "partial_trace",
    "unitary_operator",
    "lindblad_generator",
    "hamiltonian_operator",
    "finite_dimensional_hilbert_space",
    "finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator",
)


def _parse_strategy_output_text(raw_text: str) -> dict:
    text = raw_text.strip()
    if not text:
        raise ValueError("empty output")

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    fenced = _FENCED_JSON_RE.search(text)
    if fenced:
        parsed = json.loads(fenced.group(1))
        if isinstance(parsed, dict):
            return parsed

    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[index:])
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        parsed = json.loads(text[start : end + 1])
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("no parseable json object")


def _clone_candidate(base_candidate: dict, lane: str, step: int, index: int) -> dict:
    out = deepcopy(base_candidate)
    suffix = f"_S{step:04d}"
    candidate_id = str(out.get("id", "S_AUTO")).strip() or "S_AUTO"
    candidate_id = _STEP_SUFFIX_RE.sub("", candidate_id) + suffix
    out["id"] = candidate_id
    out["item_class"] = "SPEC_HYP"
    out["kind"] = str(out.get("kind", "SIM_SPEC")).strip() or "SIM_SPEC"
    out["requires"] = [str(x).strip() for x in out.get("requires", []) if str(x).strip()]
    out["def_fields"] = [dict(x) for x in out.get("def_fields", []) if isinstance(x, dict)]
    out["asserts"] = [dict(x) for x in out.get("asserts", []) if isinstance(x, dict)]
    out["operator_id"] = str(out.get("operator_id", "OP_A1_GENERATED")).strip() or "OP_A1_GENERATED"
    step_term = _REPLAY_TERM_SEQUENCE[(max(1, int(step)) - 1) % len(_REPLAY_TERM_SEQUENCE)]

    # Keep replay chains progressing by rotating term-level anchors per step.
    for row in out["def_fields"]:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name", "")).upper().strip()
        if name == "TERM":
            row["value"] = step_term
        elif out["kind"] == "MATH_DEF" and name == "CODOMAIN":
            row["value"] = step_term
        elif out["kind"] == "MATH_DEF" and name == "OBJECTS":
            row["value"] = f"finite_dimensional_hilbert_space {step_term}"
        elif out["kind"] == "MATH_DEF" and name == "OPERATIONS":
            row["value"] = f"{step_term} partial_trace cptp_channel unitary_operator"
        elif out["kind"] == "MATH_DEF" and name == "VARIANCE_MARKERS":
            row["value"] = " ".join(f"V{step:04d}_{suffix}" for suffix in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])

    if out["kind"] == "MATH_DEF" and not any(
        str(row.get("name", "")).upper().strip() == "VARIANCE_MARKERS" for row in out["def_fields"]
    ):
        out["def_fields"].append(
            {
                "field_id": f"F_VARIANCE_{index:02d}",
                "name": "VARIANCE_MARKERS",
                "value_kind": "TOKEN",
                "value": " ".join(
                    f"V{step:04d}_{suffix}" for suffix in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
                ),
            }
        )
    if out["kind"] == "CANON_PERMIT":
        canon_evidence = f"E_CANON_{candidate_id}"
        for row in out["def_fields"]:
            if str(row.get("name", "")).upper().strip() == "REQUIRES_EVIDENCE":
                row["value"] = canon_evidence
                break
        else:
            out["def_fields"].append(
                {
                    "field_id": f"F_CANON_EVID_{index:02d}",
                    "name": "REQUIRES_EVIDENCE",
                    "value_kind": "TOKEN",
                    "value": canon_evidence,
                }
            )

    # Ensure replay has deterministic structural motion across steps/lane/index.
    branch_track = f"{lane.upper()}_STEP_{step:04d}_C{index:02d}"
    for row in out["def_fields"]:
        if str(row.get("name", "")).upper() == "BRANCH_TRACK":
            row["value_kind"] = "TOKEN"
            row["value"] = branch_track
            break
    else:
        out["def_fields"].append(
            {
                "field_id": f"F_BRANCH_{index:02d}",
                "name": "BRANCH_TRACK",
                "value_kind": "TOKEN",
                "value": branch_track,
            }
        )

    if out["kind"] == "SIM_SPEC":
        probe_id = ""
        for dep in out["requires"]:
            if dep.startswith("P_"):
                probe_id = dep
                break
        if not probe_id:
            probe_id = f"P_{candidate_id}"
            out["requires"] = [probe_id] + out["requires"]

        probe_token = ""
        for row in out["asserts"]:
            if str(row.get("token_class", "")).upper() == "PROBE_TOKEN":
                probe_token = str(row.get("token", "")).strip()
                break
        if not probe_token:
            probe_token = f"PT_{probe_id}"
            out["asserts"].append(
                {"assert_id": f"A_PROBE_{index:02d}", "token_class": "PROBE_TOKEN", "token": probe_token}
            )

        evidence_token = ""
        for row in out["def_fields"]:
            if str(row.get("name", "")).upper() == "REQUIRES_EVIDENCE":
                evidence_token = str(row.get("value", "")).strip()
                break
        if lane == "alternatives":
            evidence_token = f"E_{candidate_id}"
        if not evidence_token:
            evidence_token = f"E_{candidate_id}"
            out["def_fields"].append(
                {
                    "field_id": f"F_EVID_{index:02d}",
                    "name": "REQUIRES_EVIDENCE",
                    "value_kind": "TOKEN",
                    "value": evidence_token,
                }
            )
        else:
            for row in out["def_fields"]:
                if str(row.get("name", "")).upper() == "REQUIRES_EVIDENCE":
                    row["value"] = evidence_token
                    break
        for row in out["asserts"]:
            if str(row.get("token_class", "")).upper() == "EVIDENCE_TOKEN":
                row["token"] = evidence_token
                break
        else:
            out["asserts"].append(
                {"assert_id": f"A_EVID_{index:02d}", "token_class": "EVIDENCE_TOKEN", "token": evidence_token}
            )

        out["def_fields"] = [
            row
            for row in out["def_fields"]
            if not (
                str(row.get("name", "")).upper() == "NEGATIVE_CLASS"
                and not str(row.get("value", "")).strip()
            )
        ]
        fields_by_name = {str(row.get("name", "")).upper(): row for row in out["def_fields"]}
        phase = (step + index) % 3
        default_tier = "T0_ATOM" if phase == 0 else "T1_COMPOUND"
        default_family = "BASELINE" if phase == 0 else ("BOUNDARY_SWEEP" if phase == 1 else "PERTURBATION")
        tier = str(fields_by_name.get("TIER", {}).get("value", "")).strip() or default_tier
        family = str(fields_by_name.get("FAMILY", {}).get("value", "")).strip() or default_family
        target_class = str(fields_by_name.get("TARGET_CLASS", {}).get("value", "")).strip() or candidate_id
        target_class = _TARGET_CLASS_SUFFIX_RE.sub("", target_class)
        default_negative_class = "NEG_BOUNDARY" if lane == "alternatives" else ""
        negative_class = str(fields_by_name.get("NEGATIVE_CLASS", {}).get("value", "")).strip() or default_negative_class
        probe_kind = str(fields_by_name.get("PROBE_KIND", {}).get("value", "")).strip() or "A1_GENERATED"
        for name, value in [
            ("SIM_ID", candidate_id),
            ("TIER", tier),
            ("FAMILY", family),
            ("TARGET_CLASS", target_class),
            ("NEGATIVE_CLASS", negative_class),
            ("PROBE_KIND", probe_kind),
        ]:
            if name == "NEGATIVE_CLASS" and not str(value).strip():
                continue
            if name in fields_by_name:
                fields_by_name[name]["value"] = value
            else:
                out["def_fields"].append(
                    {
                        "field_id": f"F_{name}_{index:02d}",
                        "name": name,
                        "value_kind": "TOKEN",
                        "value": value,
                    }
                )
    return out


def _strip_forbidden_keys(candidate: dict) -> dict:
    if isinstance(candidate, dict):
        out = {}
        for key, value in candidate.items():
            if str(key) in _FORBIDDEN_FIELD_KEYS:
                continue
            out[key] = _strip_forbidden_keys(value)
        return out
    if isinstance(candidate, list):
        return [_strip_forbidden_keys(x) for x in candidate]
    return candidate


def _coerce_strategy(candidate: dict, base_strategy: dict, step: int) -> dict:
    out = deepcopy(base_strategy)
    candidate = _strip_forbidden_keys(candidate if isinstance(candidate, dict) else {})

    if isinstance(candidate.get("strategy_id"), str) and candidate["strategy_id"].strip():
        out["strategy_id"] = candidate["strategy_id"].strip()

    for section in ["inputs", "budget", "policy", "sims"]:
        if isinstance(candidate.get(section), dict):
            merged = deepcopy(out.get(section, {}))
            for key, value in candidate[section].items():
                merged[key] = deepcopy(value)
            out[section] = merged

    policy = out.setdefault("policy", {})
    forbid_fields = {str(x) for x in policy.get("forbid_fields", []) if str(x)}
    forbid_fields.update(_FORBIDDEN_FIELD_KEYS)
    policy["forbid_fields"] = sorted(forbid_fields)
    if not isinstance(policy.get("overlay_ban_terms"), list):
        policy["overlay_ban_terms"] = []
    if not isinstance(policy.get("require_try_to_fail"), bool):
        policy["require_try_to_fail"] = True

    base_target = deepcopy(out.get("targets", [{}])[0]) if out.get("targets") else {}
    base_alt = deepcopy(out.get("alternatives", [{}])[0]) if out.get("alternatives") else deepcopy(base_target)

    # Preserve whole-lane replay templates (not just first target/alt) so A1 replay can
    # emit multi-item chains (e.g. MATH_DEF -> TERM_DEF -> CANON_PERMIT -> SIM_SPEC).
    base_targets = [deepcopy(x) for x in out.get("targets", []) if isinstance(x, dict)]
    base_alternatives = [deepcopy(x) for x in out.get("alternatives", []) if isinstance(x, dict)]

    id_map: dict[str, str] = {}

    coerced_targets = []
    if isinstance(candidate.get("targets"), list) and candidate["targets"]:
        for i, row in enumerate(candidate["targets"], start=1):
            if not isinstance(row, dict):
                continue
            seed = deepcopy(base_targets[min(i - 1, len(base_targets) - 1)] if base_targets else base_target)
            seed.update(row)
            old_id = str(seed.get("id", "")).strip()
            cloned = _clone_candidate(seed, lane="targets", step=step, index=i)
            new_id = str(cloned.get("id", "")).strip()
            if old_id and new_id:
                id_map[old_id] = new_id
            coerced_targets.append(cloned)
    else:
        source_targets = base_targets if base_targets else [deepcopy(base_target)]
        for i, row in enumerate(source_targets, start=1):
            old_id = str(row.get("id", "")).strip()
            cloned = _clone_candidate(row, lane="targets", step=step, index=i)
            new_id = str(cloned.get("id", "")).strip()
            if old_id and new_id:
                id_map[old_id] = new_id
            coerced_targets.append(cloned)
    out["targets"] = coerced_targets

    coerced_alts = []
    if isinstance(candidate.get("alternatives"), list) and candidate["alternatives"]:
        for i, row in enumerate(candidate["alternatives"], start=1):
            if not isinstance(row, dict):
                continue
            seed = deepcopy(base_alternatives[min(i - 1, len(base_alternatives) - 1)] if base_alternatives else base_alt)
            seed.update(row)
            old_id = str(seed.get("id", "")).strip()
            cloned = _clone_candidate(seed, lane="alternatives", step=step, index=i)
            new_id = str(cloned.get("id", "")).strip()
            if old_id and new_id:
                id_map[old_id] = new_id
            coerced_alts.append(cloned)
    elif base_alternatives:
        for i, row in enumerate(base_alternatives, start=1):
            old_id = str(row.get("id", "")).strip()
            cloned = _clone_candidate(row, lane="alternatives", step=step, index=i)
            new_id = str(cloned.get("id", "")).strip()
            if old_id and new_id:
                id_map[old_id] = new_id
            coerced_alts.append(cloned)
    if not coerced_alts and out.get("policy", {}).get("require_try_to_fail", False) and out.get("targets"):
        alt_seed = deepcopy(base_alt if base_alt else base_target)
        alt_seed["id"] = str(alt_seed.get("id", "S_ALT")) + "_ALT"
        alt_seed["operator_id"] = "OP_NEG_SIM_EXPAND"
        old_id = str(alt_seed.get("id", "")).strip()
        cloned = _clone_candidate(alt_seed, lane="alternatives", step=step, index=1)
        new_id = str(cloned.get("id", "")).strip()
        if old_id and new_id:
            id_map[old_id] = new_id
        coerced_alts.append(cloned)
    out["alternatives"] = coerced_alts

    def _rewrite_candidate_refs(item: dict) -> None:
        requires = [str(x).strip() for x in item.get("requires", []) if str(x).strip()]
        item["requires"] = [id_map.get(dep, dep) for dep in requires]
        for row in item.get("def_fields", []):
            if not isinstance(row, dict):
                continue
            name = str(row.get("name", "")).upper().strip()
            value = str(row.get("value", "")).strip()
            if not value:
                continue
            if name in {"BINDS", "KILL_TARGET", "SIM_ID"} and value in id_map:
                row["value"] = id_map[value]
                continue
            if name == "DEPENDS_ON":
                row["value"] = " ".join(id_map.get(token, token) for token in value.split())

    for row in out["targets"]:
        _rewrite_candidate_refs(row)
    for row in out["alternatives"]:
        _rewrite_candidate_refs(row)

    # Keep baseline target SIM evidence coupled to the batch's CANON_PERMIT token.
    canon_tokens: list[str] = []
    for row in out["targets"]:
        if str(row.get("kind", "")).upper() != "CANON_PERMIT":
            continue
        for field in row.get("def_fields", []):
            if str(field.get("name", "")).upper().strip() == "REQUIRES_EVIDENCE":
                token = str(field.get("value", "")).strip()
                if token:
                    canon_tokens.append(token)
                    break
    if canon_tokens:
        canon_token = canon_tokens[0]
        for row in out["targets"]:
            if str(row.get("kind", "")).upper() != "SIM_SPEC":
                continue
            has_negative = False
            for field in row.get("def_fields", []):
                if str(field.get("name", "")).upper().strip() == "NEGATIVE_CLASS" and str(field.get("value", "")).strip():
                    has_negative = True
                    break
            if has_negative:
                continue
            for field in row.get("def_fields", []):
                if str(field.get("name", "")).upper().strip() == "REQUIRES_EVIDENCE":
                    field["value"] = canon_token
                    break
            else:
                row.setdefault("def_fields", []).append(
                    {
                        "field_id": "F_CANON_LINK_01",
                        "name": "REQUIRES_EVIDENCE",
                        "value_kind": "TOKEN",
                        "value": canon_token,
                    }
                )
            for assertion in row.get("asserts", []):
                if str(assertion.get("token_class", "")).upper().strip() == "EVIDENCE_TOKEN":
                    assertion["token"] = canon_token
                    break
            else:
                row.setdefault("asserts", []).append(
                    {
                        "assert_id": "A_CANON_LINK_01",
                        "token_class": "EVIDENCE_TOKEN",
                        "token": canon_token,
                    }
                )

    positive = []
    for i, target in enumerate(out["targets"], start=1):
        positive.append({"sim_id": f"SIM_POS_{target['id']}_{i:02d}", "binds_to": target["id"]})
    negative = []
    for i, alt in enumerate(out["alternatives"], start=1):
        negative.append({"sim_id": f"SIM_NEG_{alt['id']}_{i:02d}", "binds_to": alt["id"]})
    sims = out.get("sims", {})
    if not isinstance(sims, dict):
        sims = {}
    sims["positive"] = positive
    sims["negative"] = negative
    out["sims"] = sims

    operator_ids = sorted(
        {
            str(row.get("operator_id", "")).strip()
            for row in out["targets"] + out["alternatives"]
            if isinstance(row, dict) and str(row.get("operator_id", "")).strip()
        }
    )
    lane_digest_payload = {
        "targets": [{"id": row["id"], "kind": row["kind"]} for row in out["targets"]],
        "alternatives": [{"id": row["id"], "kind": row["kind"]} for row in out["alternatives"]],
        "operators": operator_ids,
    }
    compile_lane_digest = hashlib.sha256(
        json.dumps(lane_digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    self_audit = deepcopy(out.get("self_audit", {}))
    self_audit["candidate_count"] = len(out["targets"])
    self_audit["alternative_count"] = len(out["alternatives"])
    self_audit["operator_ids_used"] = operator_ids
    self_audit["compile_lane_digest"] = compile_lane_digest
    self_audit["strategy_hash"] = ""
    out["self_audit"] = self_audit
    out["schema"] = "A1_STRATEGY_v1"
    out["self_audit"]["strategy_hash"] = hashlib.sha256(canonical_strategy_bytes(out)).hexdigest()
    return out


class A1Bridge:
    def __init__(
        self,
        source: str = "replay",
        model: str = "phi4-mini",
        timeout_sec: int = 60,
        inbox_dir: Path | None = None,
    ):
        if source == "ollama":
            raise ValueError("a1_source_ollama_disabled:use_packet_or_replay")
        self.source = source
        self.model = model
        self.timeout_sec = timeout_sec
        self.inbox_dir = inbox_dir

    def next_strategy(self, strategy_path: Path, step: int, state_hash: str, last_tags: list[str]) -> dict:
        if self.source == "replay":
            loaded = load_strategy(strategy_path)
            strategy = _coerce_strategy({}, loaded["strategy"], step)
            strategy.setdefault("inputs", {})["state_hash"] = state_hash
            strategy.setdefault("self_audit", {})["strategy_hash"] = hashlib.sha256(canonical_strategy_bytes(strategy)).hexdigest()
            errors = validate_strategy(strategy)
            if errors:
                raise ValueError("replay_strategy_invalid:" + ";".join(errors))
            strategy_sha = hashlib.sha256(canonical_strategy_bytes(strategy)).hexdigest()
            return {
                "strategy": strategy,
                "strategy_sha256": strategy_sha,
                "raw_output": json.dumps(strategy, sort_keys=True, separators=(",", ":")),
                "source": "replay",
            }
        if self.source == "packet":
            return self._from_packet_inbox(strategy_path, step, state_hash)
        raise ValueError(f"unsupported A1 source: {self.source}")

    def _from_packet_inbox(self, strategy_path: Path, step: int, state_hash: str) -> dict:
        inbox = self.inbox_dir
        if inbox is None:
            raise ValueError("a1_packet_missing_inbox_dir")
        inbox.mkdir(parents=True, exist_ok=True)

        # Packet mode consumes ZIP_PROTOCOL_v2 capsules only.
        candidates = sorted([p for p in inbox.glob("*.zip") if p.is_file()], key=lambda p: p.name)
        if not candidates:
            raise ValueError("a1_inbox_empty")

        # Persist sequence tracking across runner invocations.
        # The ZIP validator enforces monotone sequence per (run_id, source_layer). Without
        # persistence, any packet with sequence > 1 would be deterministically PARKed when
        # the runner is invoked step-by-step (new process each time).
        seq_state_path = inbox / "sequence_state.json"
        seq_state: dict[tuple[str, str], int] = {}
        if seq_state_path.exists():
            try:
                raw = json.loads(seq_state_path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    for k, v in raw.items():
                        if not isinstance(k, str):
                            continue
                        if not isinstance(v, int):
                            continue
                        if "|" not in k:
                            continue
                        run_id, source_layer = k.split("|", 1)
                        run_id = run_id.strip()
                        source_layer = source_layer.strip()
                        if not run_id or not source_layer:
                            continue
                        seq_state[(run_id, source_layer)] = int(v)
            except Exception:
                seq_state = {}

        packet_path = candidates[0]
        result = validate_zip_protocol_v2(str(packet_path), seq_state)
        if result.get("outcome") != "OK":
            raise ValueError(f"a1_packet_zip_invalid:{result.get('tag','')}:{result.get('reason','')}")

        with zipfile.ZipFile(packet_path, "r") as zf:
            header = json.loads(zf.read("ZIP_HEADER.json").decode("utf-8"))
            if str(header.get("zip_type", "")) != "A1_TO_A0_STRATEGY_ZIP":
                raise ValueError("a1_packet_wrong_zip_type")
            strategy_candidate = json.loads(zf.read("A1_STRATEGY_v1.json").decode("utf-8"))
            run_id = str(header.get("run_id", "")).strip()
            source_layer = str(header.get("source_layer", "")).strip()
            sequence = int(header.get("sequence", 0))
        if not isinstance(strategy_candidate, dict):
            raise ValueError("a1_packet_missing_strategy")

        strategy = strategy_candidate
        errors = validate_strategy(strategy)
        if errors:
            raise ValueError("a1_packet_schema_fail:" + ";".join(errors))

        # Update persisted seq_state after successful validation.
        if run_id and source_layer and sequence > 0:
            seq_state[(run_id, source_layer)] = int(sequence)
            to_dump = {f"{k[0]}|{k[1]}": int(v) for k, v in sorted(seq_state.items())}
            seq_state_path.write_text(json.dumps(to_dump, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

        # Default is cache-lean operation: consume and delete packet after successful
        # validation/parse. Set A1_PACKET_KEEP_CONSUMED=1 to keep an audit copy.
        if os.getenv("A1_PACKET_KEEP_CONSUMED", "").strip() == "1":
            consumed = inbox / "consumed"
            consumed.mkdir(parents=True, exist_ok=True)
            packet_path.replace(consumed / packet_path.name)
        else:
            packet_path.unlink(missing_ok=True)

        return {
            "strategy": strategy,
            "strategy_sha256": hashlib.sha256(canonical_strategy_bytes(strategy)).hexdigest(),
            "raw_output": json.dumps(strategy_candidate, sort_keys=True, separators=(",", ":")),
            "source": "packet",
        }
