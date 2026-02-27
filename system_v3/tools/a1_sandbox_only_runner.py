#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORE_DOCS = REPO / "core_docs"
SYSTEM_V3 = REPO / "system_v3"
A2_STATE = SYSTEM_V3 / "a2_state"

WORK = REPO / "work"
SANDBOX_ROOT = WORK / "a1_sandbox_only"

CONSTRAINTS = ["F01_FINITUDE", "N01_NONCOMMUTATION"]

ROLE_SET = [
    "STEELMAN_CORE",
    "DEVIL_CLASSICAL_TIME",
    "DEVIL_COMMUTATIVE",
    "DEVIL_CONTINUUM",
    "DEVIL_EQUALS_SMUGGLE",
    "BOUNDARY_REPAIR",
    "RESCUER_MINIMAL_EDIT",
    "ENTROPY_LENS_MUTUAL",
    "ENGINE_LENS_SZILARD_CARNOT",
]

# Compact, deterministic prompts are encoded as role claims here.
ROLE_CLAIMS = {
    "STEELMAN_CORE": [
        "Build the lowest-presumption QIT substrate: density_matrix + probe_operator; avoid primitive equality and global time.",
        "Draft explicit, professional math definitions with compositional requires_terms.",
    ],
    "DEVIL_CLASSICAL_TIME": [
        "Construct a plausible classical-time variant; make the smuggled assumption explicit so it can be killed later.",
    ],
    "DEVIL_COMMUTATIVE": [
        "Construct a plausible commutative-collapse variant; make the commutativity assumption explicit.",
    ],
    "DEVIL_CONTINUUM": [
        "Construct a continuum/infinite-resolution variant; make infinity/continuum assumptions explicit.",
    ],
    "DEVIL_EQUALS_SMUGGLE": [
        "Construct a primitive-equals/identity-smuggle variant; make '=' as primitive explicit.",
    ],
    "BOUNDARY_REPAIR": [
        "Propose boundary repairs near known classical leaks without reintroducing primitives.",
    ],
    "RESCUER_MINIMAL_EDIT": [
        "Propose minimal-edit rescue paths from graveyard items into admissible QIT-like candidates.",
    ],
    "ENTROPY_LENS_MUTUAL": [
        "Treat entropy as correlation structure (mutual information / partial trace cuts) not classical bath temperature.",
    ],
    "ENGINE_LENS_SZILARD_CARNOT": [
        "Treat Carnot/Szilard as overlays; extract only nonclassical information-work witnesses to be ratcheted later.",
    ],
}

ROLE_NEG_CLASSES = {
    "STEELMAN_CORE": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME", "PRIMITIVE_EQUALS"],
    "DEVIL_CLASSICAL_TIME": ["CLASSICAL_TIME"],
    "DEVIL_COMMUTATIVE": ["COMMUTATIVE_ASSUMPTION"],
    "DEVIL_CONTINUUM": ["INFINITE_SET", "INFINITE_RESOLUTION", "EUCLIDEAN_METRIC"],
    "DEVIL_EQUALS_SMUGGLE": ["PRIMITIVE_EQUALS"],
    "BOUNDARY_REPAIR": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
    "RESCUER_MINIMAL_EDIT": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
    "ENTROPY_LENS_MUTUAL": ["CLASSICAL_TEMPERATURE", "CONTINUOUS_BATH"],
    "ENGINE_LENS_SZILARD_CARNOT": ["CLASSICAL_TEMPERATURE", "CLASSICAL_TIME", "CONTINUOUS_BATH"],
}


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canon_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _read_text_if_exists(path: Path, *, max_chars: int) -> str:
    if not path.exists() or not path.is_file():
        return ""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = " ".join(raw.split())
    return text[:max_chars]


def _fuel_digest() -> tuple[str, dict]:
    sources = {
        "MODEL_CONTEXT.md": A2_STATE / "MODEL_CONTEXT.md",
        "INTENT_SUMMARY.md": A2_STATE / "INTENT_SUMMARY.md",
        "PHYSICS_FUEL_DIGEST_v1.0.md": CORE_DOCS / "a1_refined_Ratchet Fuel" / "PHYSICS_FUEL_DIGEST_v1.0.md",
        "AXES_MASTER_SPEC_v0.2.md": CORE_DOCS / "a1_refined_Ratchet Fuel" / "AXES_MASTER_SPEC_v0.2.md",
        "AXIS_FOUNDATION_COMPANION_v1.4.md": CORE_DOCS / "a1_refined_Ratchet Fuel" / "AXIS_FOUNDATION_COMPANION_v1.4.md",
    }
    excerpt = {name: _read_text_if_exists(path, max_chars=4000) for name, path in sources.items()}
    digest = _sha256_text(_canon_json(excerpt))
    return digest, excerpt


@dataclass
class Brain:
    schema: str
    run_id: str
    created_ts_utc: str
    last_sequence: int
    focus_terms: list[str]
    open_questions: list[str]
    graveyard_seed_queue: list[str]


def _brain_path(run_dir: Path) -> Path:
    return run_dir / "brain" / "a1_brain.json"


def _load_brain(run_dir: Path, run_id: str) -> Brain:
    path = _brain_path(run_dir)
    if path.exists():
        obj = json.loads(path.read_text(encoding="utf-8"))
        return Brain(
            schema=str(obj.get("schema", "A1_SANDBOX_BRAIN_v1")),
            run_id=str(obj.get("run_id", run_id)),
            created_ts_utc=str(obj.get("created_ts_utc", "")),
            last_sequence=int(obj.get("last_sequence", 0) or 0),
            focus_terms=[str(x) for x in (obj.get("focus_terms") or [])],
            open_questions=[str(x) for x in (obj.get("open_questions") or [])],
            graveyard_seed_queue=[str(x) for x in (obj.get("graveyard_seed_queue") or [])],
        )
    now = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return Brain(
        schema="A1_SANDBOX_BRAIN_v1",
        run_id=run_id,
        created_ts_utc=now,
        last_sequence=0,
        focus_terms=["density_matrix", "probe_operator"],
        open_questions=[
            "What is the minimal nonclassical probe semantics consistent with N01_NONCOMMUTATION?",
            "Which classical smuggles must be explicitly demarcated before any rescue attempts?",
        ],
        graveyard_seed_queue=[
            "carnot_engine_overlay",
            "szilard_engine_overlay",
            "primitive_equals",
            "classical_time_parameter",
        ],
    )


def _save_brain(run_dir: Path, brain: Brain) -> str:
    path = _brain_path(run_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    obj = {
        "schema": brain.schema,
        "run_id": brain.run_id,
        "created_ts_utc": brain.created_ts_utc,
        "last_sequence": int(brain.last_sequence),
        "focus_terms": list(dict.fromkeys(brain.focus_terms)),
        "open_questions": list(dict.fromkeys(brain.open_questions)),
        "graveyard_seed_queue": list(dict.fromkeys(brain.graveyard_seed_queue)),
    }
    text = _canon_json(obj) + "\n"
    path.write_text(text, encoding="utf-8")
    return _sha256_text(text)


def _write_packet_zip(run_dir: Path, *, sequence: int, request: dict, response: dict | None) -> Path:
    packets = run_dir / "packets"
    packets.mkdir(parents=True, exist_ok=True)

    seq = int(sequence)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stem = f"{seq:06d}__A1_SANDBOX_TASK_ZIP_v1__{ts}"

    tmp = run_dir / "_tmp_packet_build" / stem
    if tmp.exists():
        for p in sorted(tmp.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink(missing_ok=True)
            elif p.is_dir():
                try:
                    p.rmdir()
                except OSError:
                    pass
    tmp.mkdir(parents=True, exist_ok=True)

    header = {
        "schema": "ZIP_HEADER_v2",
        "zip_type": "A1_SANDBOX_TASK_ZIP_v1",
        "direction": "SANDBOX_ONLY",
        "source_layer": "A1",
        "target_layer": "A1_SANDBOX",
        "sequence": seq,
        "ts_utc": ts,
    }
    (tmp / "ZIP_HEADER.json").write_text(_canon_json(header) + "\n", encoding="utf-8")

    (tmp / "A1_SANDBOX_TASK_REQUEST.json").write_text(_canon_json(request) + "\n", encoding="utf-8")
    if response is not None:
        (tmp / "A1_SANDBOX_TASK_RESPONSE.json").write_text(_canon_json(response) + "\n", encoding="utf-8")

    manifest = {
        "schema": "MANIFEST_v1",
        "files": sorted([p.name for p in tmp.iterdir() if p.is_file()]),
    }
    (tmp / "MANIFEST.json").write_text(_canon_json(manifest) + "\n", encoding="utf-8")

    out = packets / f"{stem}.zip"
    import zipfile

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(tmp.iterdir()):
            if p.is_file():
                z.write(p, arcname=p.name)

    return out


def _pick_topic_terms(brain: Brain) -> list[str]:
    # Deterministic: focus terms + next from seed queue.
    terms = list(dict.fromkeys(brain.focus_terms))
    if brain.graveyard_seed_queue:
        terms.append(brain.graveyard_seed_queue[0])
    return terms[:6]


def _draft_term_defs(topic_terms: list[str]) -> list[dict]:
    # Minimal, explicit, professional definitions. No '=' primitive.
    # These are *drafts* for later ratchet admission.
    drafts: list[dict] = []
    if "density_matrix" in topic_terms:
        drafts.append(
            {
                "term": "density_matrix",
                "math_def": "A density_matrix is a finite-dimensional positive semidefinite operator rho with trace(rho)=1 used to represent a state as an equivalence class of preparation statistics under admissible probes.",
                "requires_terms": ["finite_dimensional_hilbert_space", "positive_semidefinite", "trace_one"],
            }
        )
    if "probe_operator" in topic_terms:
        drafts.append(
            {
                "term": "probe_operator",
                "math_def": "A probe_operator is a finite operator-valued map that acts on a density_matrix to produce an observable witness (e.g., expectation or outcome distribution) without assuming global commutativity or classical time parameterization.",
                "requires_terms": ["density_matrix", "measurement_operator", "noncommutative_composition_order"],
            }
        )
    return drafts


def _draft_sims(topic_terms: list[str], neg_classes: list[str]) -> list[dict]:
    sims: list[dict] = []
    # Sandbox-only sim drafts: planning for later SIM layer.
    if "density_matrix" in topic_terms and "probe_operator" in topic_terms:
        sims.append(
            {
                "sim_name": "sim_probe_distinguishability_under_noncommutative_composition_order",
                "sim_intent": "POSITIVE",
                "probe_terms": ["density_matrix", "probe_operator"],
                "expected_kill_tokens": [],
            }
        )
    if "primitive_equals" in topic_terms or "primitive_equals" in neg_classes:
        sims.append(
            {
                "sim_name": "sim_kill_primitive_equals_smuggle",
                "sim_intent": "NEGATIVE",
                "probe_terms": ["primitive_equals"],
                "expected_kill_tokens": ["NEG_PRIMITIVE_EQUALS"],
            }
        )
    return sims


def _generate_role_outputs(*, sequence: int, brain: Brain, topic_terms: list[str]) -> list[dict]:
    outputs: list[dict] = []
    for role in ROLE_SET:
        claims = ROLE_CLAIMS.get(role, ["Provide explicit claims."])
        negs = ROLE_NEG_CLASSES.get(role, ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"])

        term_defs = []
        sim_drafts = []

        if role == "STEELMAN_CORE":
            term_defs = _draft_term_defs(topic_terms)
            sim_drafts = _draft_sims(topic_terms, negs)
        elif role.startswith("DEVIL_"):
            # Devils propose explicit smuggles as graveyard seeds, not as truth.
            term_defs = []
            sim_drafts = _draft_sims(topic_terms + ["primitive_equals"], negs)
        elif role in {"ENTROPY_LENS_MUTUAL", "ENGINE_LENS_SZILARD_CARNOT"}:
            # Planning-only: push these concepts into graveyard seed queue.
            term_defs = []
            sim_drafts = []

        outputs.append(
            {
                "role": role,
                "claims": list(claims),
                "negative_classes": list(negs),
                "proposed_terms": list(dict.fromkeys(topic_terms))[:12],
                "term_definition_drafts": term_defs,
                "sim_drafts": sim_drafts,
            }
        )
    return outputs


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Run A1 LLM-side work inside sandbox only (no A0/B/SIM).")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--steps", type=int, default=12)
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--max-packets", type=int, default=200)
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    run_dir = SANDBOX_ROOT / run_id
    if bool(args.clean) and run_dir.exists():
        # Non-destructive: move to legacy bucket rather than delete.
        legacy = SANDBOX_ROOT / "LEGACY__MIGRATED__" / f"{run_id}__{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        run_dir.rename(legacy)

    run_dir.mkdir(parents=True, exist_ok=True)

    brain = _load_brain(run_dir, run_id)
    fuel_hash, fuel_excerpt = _fuel_digest()

    executed = 0
    while executed < int(args.steps):
        seq = int(brain.last_sequence) + 1
        if seq > int(args.max_packets):
            break

        brain_digest = _save_brain(run_dir, brain)
        topic_terms = _pick_topic_terms(brain)

        request = {
            "schema": "A1_SANDBOX_TASK_REQUEST_v1",
            "run_id": run_id,
            "sequence": seq,
            "task_kind": "STEELMAN_AND_LAWYERS_BATCH",
            "topic_terms": list(topic_terms),
            "required_roles": list(ROLE_SET),
            "inputs": {
                "a1_brain_digest": brain_digest,
                "fuel_digest": fuel_hash,
                "constraints": list(CONSTRAINTS),
            },
            "fuel_excerpt": fuel_excerpt,  # bounded by _fuel_digest; stays compact
        }

        role_outputs = _generate_role_outputs(sequence=seq, brain=brain, topic_terms=topic_terms)

        # Update brain deterministically from this step.
        new_focus = ["density_matrix", "probe_operator", "partial_trace", "cptp_channel"]
        for t in new_focus:
            if t not in brain.focus_terms:
                brain.focus_terms.append(t)
        # Pop one seed concept per step to ensure breadth without explosion.
        if brain.graveyard_seed_queue:
            brain.graveyard_seed_queue.pop(0)
        brain.last_sequence = seq

        response = {
            "schema": "A1_SANDBOX_TASK_RESPONSE_v1",
            "run_id": run_id,
            "sequence": seq,
            "role_outputs": role_outputs,
            "graveyard_seed_list": list(dict.fromkeys(brain.graveyard_seed_queue))[:64],
            "brain_delta": {
                "new_focus_terms": list(dict.fromkeys(new_focus)),
                "new_open_questions": [],
            },
        }

        _write_packet_zip(run_dir, sequence=seq, request=request, response=response)
        executed += 1

    out = {
        "schema": "A1_SANDBOX_ONLY_RUN_REPORT_v1",
        "run_id": run_id,
        "executed_steps": executed,
        "brain_path": str(_brain_path(run_dir)),
        "packets_dir": str((run_dir / "packets")),
    }
    (run_dir / "report.json").write_text(_canon_json(out) + "\n", encoding="utf-8")
    print(_canon_json(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
