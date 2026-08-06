"""Source-bound user profile and MMM compiler.

The compiled profile shapes prompts and the controller's output format.  It is
not an admission policy and its inferred preferences never gate settlement.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .intake import canonical_json, parse_json_object


SCHEMA = "constraintbox.user-profile.v1"
BOX_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACK_ROOT = BOX_ROOT / "mmm" / "packs"
DEFAULT_PROFILE_PATH = (
    BOX_ROOT / "config" / "users" / "joshua_eisenhart_v1.json"
)
_SAFE_PACK_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_PACK_POLICY = MappingProxyType(
    {
        "nominalist": (
            "380554750988c1af5959cc2e11e94a3c0de4b9bf66088f2edf5e8ac72c528edd",
            "keep claims tied to finite operations and avoid ontology inflation",
        ),
        "constraint-programming": (
            "1ecd4162a42d86ed90d7512d99c2ea515eae0486060003cb9e2abe8b0f63dc6b",
            "make constraints and failed clauses operational",
        ),
        "smt": (
            "11a5074a5d4ae999ba41642eaee9748786aab00cc37b06464766fa9a11608886",
            "keep finite encodings, polarity, and uncertainty explicit",
        ),
        "claimgate": (
            "07537fe62f4056d7fc8fd3a7708217fa925d9fa2f2e4ff1da97244d5b119b862",
            "preserve deterministic release checks and exact claim ceilings",
        ),
        "cr-ratchet": (
            "cff83646e32bae5c658935fb9fcb322ef1fc25e9c245a5e4c3b07d06ea0eca06",
            "provide source and fixture context without importing CR conclusions",
        ),
        "lev-os": (
            "66978f264fabe9da42d420681e2abd7caef22baf7aa7b89ca1bd527f612eb671",
            (
                "reuse bounded agent and context mechanisms without making "
                "LevOS authoritative"
            ),
        ),
    }
)
PROFILE_FIELDS = {
    "schema",
    "profile_id",
    "profile_version",
    "display_name",
    "source_anchors",
    "mmm_packs",
    "owner_requirements",
    "work_preferences",
    "inferred_preferences",
    "excluded_context",
    "claim_ceiling",
}
OUTPUT_RULES = {
    "lead_with_outcome",
    "name_real_operations",
    "plain_language",
    "push_back_on_unsupported_premises",
    "separate_advice_from_decision",
    "state_evidence_ceiling",
    "surface_assumptions",
}
SOURCE_TYPES = {"current_owner_statement", "owner_memory", "repo_doc"}
SOURCE_AUTHORITIES = {"owner_asserted", "context_only"}


class ProfileError(ValueError):
    pass


@dataclass(frozen=True)
class CompiledUserContext:
    schema: str
    profile_id: str
    profile_version: int
    profile_sha256: str
    context_sha256: str
    context_text: str
    pack_receipts: tuple[dict[str, str], ...]
    output_contract: tuple[str, ...]
    inferred_preferences_advisory_only: bool
    claim_ceiling: str

    def to_dict(self, *, include_text: bool = False) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema": self.schema,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "profile_sha256": self.profile_sha256,
            "context_sha256": self.context_sha256,
            "pack_receipts": [dict(row) for row in self.pack_receipts],
            "output_contract": list(self.output_contract),
            "inferred_preferences_advisory_only": (
                self.inferred_preferences_advisory_only
            ),
            "claim_ceiling": self.claim_ceiling,
        }
        if include_text:
            value["context_text"] = self.context_text
        return value


def _text(value: Any, label: str, maximum: int = 5_000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ProfileError(f"{label} must be a nonempty bounded string")
    return value.strip()


def _source_authorities(rows: Any) -> dict[str, str]:
    if not isinstance(rows, list) or not rows:
        raise ProfileError("source_anchors must be a nonempty list")
    found: dict[str, str] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {
            "source_id",
            "source_type",
            "reference",
            "statement",
            "authority",
        }:
            raise ProfileError(f"source_anchors[{index}] has the wrong fields")
        source_id = _text(row["source_id"], f"source_anchors[{index}].source_id", 128)
        if source_id in found:
            raise ProfileError(f"duplicate source_id: {source_id}")
        if row["source_type"] not in SOURCE_TYPES:
            raise ProfileError(f"source_anchors[{index}].source_type is invalid")
        if row["authority"] not in SOURCE_AUTHORITIES:
            raise ProfileError(f"source_anchors[{index}].authority is invalid")
        _text(row["reference"], f"source_anchors[{index}].reference", 1_000)
        _text(row["statement"], f"source_anchors[{index}].statement", 2_000)
        found[source_id] = row["authority"]
    return found


def _require_sources(
    values: Any,
    *,
    label: str,
    source_authorities: dict[str, str],
    with_output_rule: bool,
) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        raise ProfileError(f"{label} must be a list")
    output: list[dict[str, Any]] = []
    expected = {"id", "text", "source_ids"}
    if with_output_rule:
        expected.add("output_rule")
    for index, row in enumerate(values):
        if not isinstance(row, dict) or set(row) != expected:
            raise ProfileError(f"{label}[{index}] has the wrong fields")
        _text(row["id"], f"{label}[{index}].id", 128)
        _text(row["text"], f"{label}[{index}].text", 1_000)
        sources = row["source_ids"]
        if (
            not isinstance(sources, list)
            or not sources
            or any(
                not isinstance(source, str)
                or source not in source_authorities
                for source in sources
            )
        ):
            raise ProfileError(f"{label}[{index}].source_ids are not bound")
        if any(
            source_authorities[source] != "owner_asserted"
            for source in sources
        ):
            raise ProfileError(
                f"{label}[{index}].source_ids must all be owner_asserted"
            )
        if with_output_rule and row["output_rule"] not in OUTPUT_RULES:
            raise ProfileError(f"{label}[{index}].output_rule is invalid")
        output.append(row)
    return output


def _inferred_preferences(
    values: Any, source_authorities: dict[str, str]
) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        raise ProfileError("inferred_preferences must be a list")
    output: list[dict[str, Any]] = []
    for index, row in enumerate(values):
        if not isinstance(row, dict) or set(row) != {
            "id",
            "text",
            "source_ids",
            "confidence",
        }:
            raise ProfileError(f"inferred_preferences[{index}] has the wrong fields")
        _text(row["id"], f"inferred_preferences[{index}].id", 128)
        _text(row["text"], f"inferred_preferences[{index}].text", 1_000)
        sources = row["source_ids"]
        if (
            not isinstance(sources, list)
            or not sources
            or any(
                not isinstance(source, str)
                or source not in source_authorities
                for source in sources
            )
        ):
            raise ProfileError(
                f"inferred_preferences[{index}].source_ids are not bound"
            )
        confidence = row["confidence"]
        if (
            not isinstance(confidence, (int, float))
            or isinstance(confidence, bool)
            or not 0.0 <= float(confidence) <= 1.0
        ):
            raise ProfileError(
                f"inferred_preferences[{index}].confidence must be 0..1"
            )
        output.append(row)
    return output


def _pack_rows(
    rows: Any, pack_root: Path
) -> tuple[list[dict[str, str]], list[tuple[str, str]]]:
    if not isinstance(rows, list) or not rows:
        raise ProfileError("mmm_packs must be a nonempty list")
    try:
        approved_root = pack_root.resolve(strict=True)
    except OSError as exc:
        raise ProfileError(f"MMM pack root is unavailable: {pack_root}") from exc
    if not approved_root.is_dir():
        raise ProfileError(f"MMM pack root is not a directory: {pack_root}")
    receipts: list[dict[str, str]] = []
    texts: list[tuple[str, str]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {"name", "sha256", "role"}:
            raise ProfileError(f"mmm_packs[{index}] has the wrong fields")
        name = _text(row["name"], f"mmm_packs[{index}].name", 128)
        if _SAFE_PACK_SLUG.fullmatch(name) is None:
            raise ProfileError(f"mmm_packs[{index}].name is not a safe slug")
        if name in seen:
            raise ProfileError(f"duplicate MMM pack: {name}")
        seen.add(name)
        if name not in _PACK_POLICY:
            raise ProfileError(f"MMM pack is not controller-approved: {name}")
        policy_sha256, policy_role = _PACK_POLICY[name]
        profile_sha256 = _text(
            row["sha256"], f"mmm_packs[{index}].sha256", 64
        )
        profile_role = _text(row["role"], f"mmm_packs[{index}].role", 500)
        if profile_sha256 != policy_sha256:
            raise ProfileError(
                f"MMM pack profile sha256 differs from controller policy: {name}"
            )
        if profile_role != policy_role:
            raise ProfileError(
                f"MMM pack profile role differs from controller policy: {name}"
            )
        candidate = approved_root / f"{name}.md"
        try:
            path = candidate.resolve(strict=True)
        except OSError as exc:
            raise ProfileError(f"MMM pack is missing: {name}") from exc
        try:
            path.relative_to(approved_root)
        except ValueError as exc:
            raise ProfileError(
                f"MMM pack escapes approved root: {name}"
            ) from exc
        if not path.is_file():
            raise ProfileError(f"MMM pack is missing: {name}")
        raw = path.read_bytes()
        observed = hashlib.sha256(raw).hexdigest()
        if observed != policy_sha256:
            raise ProfileError(
                f"MMM pack drift: {name}; expected {policy_sha256}, "
                f"observed {observed}"
            )
        receipts.append(
            {
                "name": name,
                "path": str(path),
                "sha256": observed,
                "role": policy_role,
            }
        )
        texts.append((name, raw.decode("utf-8")))
    missing = sorted(set(_PACK_POLICY) - seen)
    if missing:
        raise ProfileError(f"controller-required MMM packs are missing: {missing}")
    return receipts, texts


def compile_user_profile(
    raw: bytes, *, pack_root: Path = DEFAULT_PACK_ROOT
) -> CompiledUserContext:
    body = parse_json_object(raw)
    if set(body) != PROFILE_FIELDS:
        missing = sorted(PROFILE_FIELDS - set(body))
        extra = sorted(set(body) - PROFILE_FIELDS)
        raise ProfileError(
            "profile fields differ"
            + (f"; missing={missing}" if missing else "")
            + (f"; extra={extra}" if extra else "")
        )
    if body["schema"] != SCHEMA:
        raise ProfileError(f"profile schema must be {SCHEMA}")
    profile_id = _text(body["profile_id"], "profile_id", 128)
    version = body["profile_version"]
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ProfileError("profile_version must be a positive integer")
    display_name = _text(body["display_name"], "display_name", 256)
    claim_ceiling = _text(body["claim_ceiling"], "claim_ceiling", 2_000)
    source_authorities = _source_authorities(body["source_anchors"])
    requirements = _require_sources(
        body["owner_requirements"],
        label="owner_requirements",
        source_authorities=source_authorities,
        with_output_rule=True,
    )
    work_preferences = _require_sources(
        body["work_preferences"],
        label="work_preferences",
        source_authorities=source_authorities,
        with_output_rule=False,
    )
    inferred = _inferred_preferences(
        body["inferred_preferences"], source_authorities
    )
    excluded = body["excluded_context"]
    if not isinstance(excluded, list) or any(
        not isinstance(item, str) or not item.strip() for item in excluded
    ):
        raise ProfileError("excluded_context must be a list of nonempty strings")
    pack_receipts, pack_texts = _pack_rows(body["mmm_packs"], pack_root)

    sections = [
        f"[USER PROFILE {profile_id} v{version}: {display_name}]",
        "[OWNER-ASSERTED COMMUNICATION REQUIREMENTS]",
        *[f"- {row['text']}" for row in requirements],
        "[OWNER-ASSERTED WORK PREFERENCES]",
        *[f"- {row['text']}" for row in work_preferences],
        "[INFERRED PREFERENCES: ADVISORY ONLY; NEVER A GATE]",
        *[
            f"- {row['text']} (confidence={float(row['confidence']):.2f})"
            for row in inferred
        ],
        "[EXCLUDED FROM NORMAL CONTEXT]",
        *[f"- {item}" for item in excluded],
    ]
    for (name, text), receipt in zip(pack_texts, pack_receipts, strict=True):
        sections.extend(
            [
                f"[MMM PACK {name} sha256={receipt['sha256']} role={receipt['role']}]",
                text,
            ]
        )
    context = "\n".join(sections)
    profile_sha = hashlib.sha256(canonical_json(body)).hexdigest()
    return CompiledUserContext(
        schema="constraintbox.compiled-user-context.v1",
        profile_id=profile_id,
        profile_version=version,
        profile_sha256=profile_sha,
        context_sha256=hashlib.sha256(context.encode("utf-8")).hexdigest(),
        context_text=context,
        pack_receipts=tuple(pack_receipts),
        output_contract=tuple(
            sorted({row["output_rule"] for row in requirements})
        ),
        inferred_preferences_advisory_only=True,
        claim_ceiling=claim_ceiling,
    )
