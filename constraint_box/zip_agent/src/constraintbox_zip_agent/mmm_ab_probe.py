from __future__ import annotations

from typing import Any

from .council_zip import MARKER, MEMBERS, VOICES, build_three_member_council_packet
from .protocol import sha256_bytes
from .runtime import execute_packet

CLAIM_CEILING = (
    "local_mmm_ab_delivery_difference_only;"
    "not_mmm_read;not_cognition;not_admission;not_release"
)


def _script(agent_id: str) -> str:
    return (
        "from pathlib import Path\n"
        "import json, hashlib\n"
        "Path('output').mkdir(exist_ok=True)\n"
        "Path('meta').mkdir(exist_ok=True)\n"
        "Path('meta/provider_evidence.json').write_text(\n"
        "    json.dumps({'schema':'constraintbox.fixture-provider-evidence.v1',"
        "'disposition':'OBSERVED','model_observed':'fixture-observed'}) + '\\n',\n"
        "    encoding='utf-8',\n"
        ")\n"
        "token = json.loads(Path('output/tool_evidence.json').read_text(encoding='utf-8'))['canonical_sha256']\n"
        "skill = hashlib.sha256(Path('SKILLS/council.md').read_bytes()).hexdigest()\n"
        "manifest = json.loads(Path('input/council_manifest.json').read_text(encoding='utf-8'))\n"
        "me = next(row for row in manifest['members'] if row['agent_id'] == "
        f"'{agent_id}')\n"
        "mmm_lines = ''.join('mmm-token: ' + digest + '\\n' for digest in me['mmm_sha256'].values())\n"
        f"Path('output/{agent_id}.md').write_text(\n"
        f"    'finding: {MARKER}\\n'"
        f"    'council: {agent_id}\\n'"
        "    'support: observed\\n'"
        "    'falsifier: missing required token\\n'"
        "    'keep_or_discard: keep\\n'"
        "    'live_patch: false\\n'"
        "    'disposition: REQUEST_CONTEXT\\n'"
        "    'tool-token: ' + token + '\\n'"
        "    'skill-token: ' + skill + '\\n'"
        "    + mmm_lines,\n"
        "    encoding='utf-8',\n"
        ")\n"
    )


def _agent(agent_id: str) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "agent_path": f"AGENTS/{agent_id}.md",
        "output_path": f"output/{agent_id}.md",
        "provider": "fixture-subprocess",
        "model_requested": "fixture-model",
        "fixture_script": _script(agent_id),
        "required_fragments": [
            f"finding: {MARKER}",
            f"council: {agent_id}",
            "support: observed",
        ],
        "max_output_bytes": 4096,
    }


def _mmm_files(tag: bytes) -> dict[str, bytes]:
    return {
        f"MMMS/{voice}.md": b"# " + voice.encode() + b" compact mini-MMM fixture\n" + tag + b"\n"
        for voice in VOICES
    }


def _outputs(return_zip: bytes) -> dict[str, str]:
    import io
    import zipfile

    out: dict[str, str] = {}
    with zipfile.ZipFile(io.BytesIO(return_zip)) as archive:
        for name in MEMBERS:
            path = f"output/{name}.md"
            out[path] = sha256_bytes(archive.read(path))
    return out


def _mmm_sha256(files: dict[str, bytes]) -> dict[str, str]:
    return {path: sha256_bytes(raw) for path, raw in sorted(files.items())}


def run_mmm_ab_probe(*, seed: int = 461, owner_prompt: bytes | None = None) -> dict[str, Any]:
    owner = owner_prompt or b"MMM A/B delivery probe. Do not promote.\n"
    agents = [_agent(name) for name in MEMBERS]
    extra = {f"AGENTS/{name}.md": f"role: {name}\n".encode() for name in MEMBERS}
    files_a = _mmm_files(b"variant-A")
    files_b = _mmm_files(b"variant-B")
    packet_a = build_three_member_council_packet(
        owner_prompt=owner,
        seed=seed,
        run_id="mmm-ab-a",
        agents=agents,
        mmm_files=files_a,
        extra_files=extra,
    )
    packet_b = build_three_member_council_packet(
        owner_prompt=owner,
        seed=seed,
        run_id="mmm-ab-b",
        agents=agents,
        mmm_files=files_b,
        extra_files=extra,
    )
    result_a = execute_packet(packet_a)
    result_b = execute_packet(packet_b)
    outputs_a = _outputs(result_a.return_zip_bytes)
    outputs_b = _outputs(result_b.return_zip_bytes)
    changed = sorted(path for path in outputs_a if outputs_a[path] != outputs_b[path])
    return {
        "schema": "constraintbox.mmm-ab-probe.v1",
        "seed": seed,
        "owner_prompt_sha256": sha256_bytes(owner),
        "packet_a_sha256": result_a.input_packet_sha256,
        "packet_b_sha256": result_b.input_packet_sha256,
        "mmm_sha256_a": _mmm_sha256(files_a),
        "mmm_sha256_b": _mmm_sha256(files_b),
        "output_sha256_a": outputs_a,
        "output_sha256_b": outputs_b,
        "changed_outputs": changed,
        "difference_observed": bool(changed),
        "mmm_read_proved": False,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
