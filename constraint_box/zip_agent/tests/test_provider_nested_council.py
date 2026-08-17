from __future__ import annotations

import io
import json
import zipfile
import pytest

from constraintbox_zip_agent.council_zip import MARKER
from constraintbox_zip_agent.protocol import (
    MANIFEST_PATH,
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    sha256_bytes,
    validate_return_zip,
)
from constraintbox_zip_agent.provider_nested_council import (
    LEAF_MANIFEST_PATH,
    LINEAGE_PATH,
    PARENT_INVENTORY_PATH,
    build_provider_nested_council_packet,
    compile_provider_nested_inventory,
    execute_provider_nested_council,
    validate_provider_nested_packet,
)
from constraintbox_zip_agent.runtime import execute_packet


VOICES = (
    "factory",
    "feynman",
    "hume",
    "orwell",
    "popper",
    "pushback",
    "strategy",
    "systems",
    "zhuangzi",
)


def _entries(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
        return {
            info.filename: archive.read(info)
            for info in archive.infolist()
            if not info.is_dir()
        }


def _rebuild(data: bytes, mutate) -> bytes:
    entries = _entries(data)
    manifest = json.loads(entries.pop(MANIFEST_PATH))
    manifest.pop("file_sha256_registry")
    mutate(manifest, entries)
    return build_packet(manifest, entries)


def _mmm() -> dict[str, bytes]:
    return {f"MMMS/{voice}.md": f"fixture mini {voice}\n".encode() for voice in VOICES}


def _script(agent_id: str, *, fail: bool = False) -> str:
    if fail:
        return "raise SystemExit(17)\n"
    return (
        "from pathlib import Path\n"
        "import hashlib, json\n"
        "Path('output').mkdir(exist_ok=True)\n"
        "Path('meta').mkdir(exist_ok=True)\n"
        "Path('meta/provider_evidence.json').write_text("
        "json.dumps({'schema':'constraintbox.fixture-provider-evidence.v1',"
        "'disposition':'OBSERVED','model_observed':'fixture-observed'}) + '\\n')\n"
        "manifest = json.loads(Path('input/council_manifest.json').read_text())\n"
        f"member = next(row for row in manifest['members'] if row['agent_id'] == '{agent_id}')\n"
        "tool = json.loads(Path('output/tool_evidence.json').read_text())['canonical_sha256']\n"
        "skill = hashlib.sha256(Path('SKILLS/council.md').read_bytes()).hexdigest()\n"
        "mmm = ''.join('mmm-token: ' + value + '\\n' for value in member['mmm_sha256'].values())\n"
        f"Path('output/{agent_id}.md').write_text("
        f"'finding: {MARKER}\\n' + "
        f"'council: {agent_id}\\n' + "
        "'support: observed\\n' + 'falsifier: absent token\\n' + "
        "'keep_or_discard: keep\\n' + 'live_patch: false\\n' + "
        "'disposition: REQUEST_CONTEXT\\n' + 'tool-token: ' + tool + '\\n' + "
        "'skill-token: ' + skill + '\\n' + mmm)\n"
    )


def _child(council_id: str, job_id: str, names: tuple[str, ...], *, fail: str | None = None) -> dict:
    agents = []
    files = {}
    for name in names:
        agents.append(
            {
                "agent_id": name,
                "agent_path": f"AGENTS/{name}.md",
                "output_path": f"output/{name}.md",
                "provider": "fixture-subprocess",
                "model_requested": f"fixture-{council_id}-{name}",
                "fixture_script": _script(name, fail=fail == name),
                "max_output_bytes": 8192,
            }
        )
        files[f"AGENTS/{name}.md"] = f"role: {name}\n".encode()
    return {
        "council_id": council_id,
        "job_id": job_id,
        "agents": agents,
        "agent_files": files,
    }


def _packet(*, fail: str | None = None) -> bytes:
    return build_provider_nested_council_packet(
        owner_prompt=b"target: bounded provider council\n",
        seed=713,
        run_id="nested-fixture",
        mmm_files=_mmm(),
        children=[
            _child("failure", "child-failure", ("likely", "dangerous", "assumption"), fail=fail),
            _child("repair", "child-repair", ("smallest", "test", "ceiling"), fail=fail),
        ],
    )


def test_fixture_parent_preserves_child_returns_and_explicit_depth_two_leaves() -> None:
    packet = _packet()
    council = validate_provider_nested_packet(packet)
    direct = execute_packet(packet)
    execution = execute_provider_nested_council(packet)
    direct_entries = _entries(direct.return_zip_bytes)
    returned = _entries(execution.result.return_zip_bytes)
    assert council.parent_depth == 0
    assert len(council.child_job_ids) == 2
    assert len(council.leaf_ids) == 6
    assert returned[PARENT_INVENTORY_PATH] == execution.inventory_bytes
    assert direct_entries[PARENT_INVENTORY_PATH] == execution.inventory_bytes
    assert direct.return_zip_bytes == execution.result.return_zip_bytes
    inventory = json.loads(execution.inventory_bytes)
    assert inventory["schema"] == "constraintbox.provider-nested-inventory.v1"
    assert inventory["parent"]["depth"] == 0
    assert [child["depth"] for child in inventory["children"]] == [1, 1]
    assert {leaf["depth"] for child in inventory["children"] for leaf in child["leaves"]} == {2}
    assert all(
        leaf["parent_id"] == child["job_id"]
        for child in inventory["children"]
        for leaf in child["leaves"]
    )
    assert inventory["synthesis_request"]["semantic_consensus"] is False
    for child_id in council.child_job_ids:
        path = f"output/{child_id}.return.zip"
        assert returned[path]
        assert sha256_bytes(returned[path]) == execution.retained_child_return_sha256[child_id]
        child_packet = _entries(packet)[f"children/{child_id}.zip"]
        validate_return_zip(returned[path], input_packet_bytes=child_packet)


def test_fixture_parent_replays_byte_identically() -> None:
    first = execute_provider_nested_council(_packet())
    second = execute_provider_nested_council(_packet())
    assert first.result.return_zip_bytes == second.result.return_zip_bytes
    assert first.inventory_bytes == second.inventory_bytes


def test_depth_three_child_is_refused() -> None:
    packet = _packet()

    def add_depth_three(_manifest, entries):
        child = entries["children/child-failure.zip"]
        child_entries = _entries(child)
        child_manifest = json.loads(child_entries.pop(MANIFEST_PATH))
        child_manifest.pop("file_sha256_registry")
        child_manifest["max_child_depth"] = 1
        entries["children/child-failure.zip"] = build_packet(child_manifest, child_entries)

    forged = _rebuild(packet, add_depth_three)
    with pytest.raises(ZipJobRefusal) as caught:
        validate_provider_nested_packet(forged)
    assert caught.value.reason_code in {
        "REFUSE_PROVIDER_NESTED_DEPTH",
        "REFUSE_PROVIDER_NESTED_CHILD_REBOUND",
    }


def test_missing_or_tampered_child_return_is_refused_before_parent_compile() -> None:
    packet = _packet()
    result = execute_packet(packet)
    returned = _entries(result.return_zip_bytes)
    missing = {"child-failure": returned["output/child-failure.return.zip"]}
    with pytest.raises(ZipJobRefusal) as caught:
        compile_provider_nested_inventory(packet, missing)
    assert caught.value.reason_code == "REFUSE_PROVIDER_NESTED_CHILD_RETURN_MISSING"

    tampered = dict(
        missing,
        **{
            "child-repair": returned["output/child-repair.return.zip"][:-1] + b"x"
        },
    )
    with pytest.raises(ZipJobRefusal) as caught:
        compile_provider_nested_inventory(packet, tampered)
    assert caught.value.reason_code == "REFUSE_PROVIDER_NESTED_CHILD_RETURN"


def test_duplicate_or_rebound_leaf_identity_is_refused() -> None:
    packet = _packet()

    def rebound(_manifest, entries):
        child = entries["children/child-failure.zip"]
        child_entries = _entries(child)
        child_manifest = json.loads(child_entries.pop(MANIFEST_PATH))
        child_manifest.pop("file_sha256_registry")
        leaves = json.loads(child_entries[LEAF_MANIFEST_PATH])
        leaves["leaves"][0]["leaf_id"] = "child-repair:smallest"
        child_entries[LEAF_MANIFEST_PATH] = canonical_json_bytes(leaves)
        entries["children/child-failure.zip"] = build_packet(child_manifest, child_entries)

    forged = _rebuild(packet, rebound)
    with pytest.raises(ZipJobRefusal) as caught:
        validate_provider_nested_packet(forged)
    assert caught.value.reason_code in {
        "REFUSE_PROVIDER_NESTED_LEAF_REBOUND",
        "REFUSE_PROVIDER_NESTED_LEAF_IDENTITY",
    }


def test_malformed_output_and_model_binding_failure_are_refused() -> None:
    packet = _packet()
    result = execute_packet(packet)
    returned = _entries(result.return_zip_bytes)
    child = _entries(packet)["children/child-failure.zip"]

    malformed = {"child-failure": b"not a return zip"}
    with pytest.raises(ZipJobRefusal) as caught:
        compile_provider_nested_inventory(packet, malformed)
    assert caught.value.reason_code == "REFUSE_PROVIDER_NESTED_CHILD_RETURN"

    def require_binding(_manifest, entries):
        child_entries = _entries(entries["children/child-failure.zip"])
        child_manifest = json.loads(child_entries.pop(MANIFEST_PATH))
        child_manifest.pop("file_sha256_registry")
        leaves = json.loads(child_entries[LEAF_MANIFEST_PATH])
        leaves["leaves"][0]["model_binding_required"] = True
        child_entries[LEAF_MANIFEST_PATH] = canonical_json_bytes(leaves)
        entries["children/child-failure.zip"] = build_packet(child_manifest, child_entries)

    rebound_packet = _rebuild(packet, require_binding)
    # The stale parent synthesis record binds the original child bytes, so
    # this is rejected before any semantic interpretation of the fixture.
    with pytest.raises(ZipJobRefusal):
        compile_provider_nested_inventory(
            rebound_packet,
            {
                "child-failure": returned["output/child-failure.return.zip"],
                "child-repair": returned["output/child-repair.return.zip"],
            },
        )


def test_one_exhausted_leaf_emits_no_parent_return() -> None:
    packet = _packet(fail="likely")
    with pytest.raises(ZipJobRefusal) as caught:
        execute_provider_nested_council(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"


def test_retry_bound_is_two() -> None:
    child = _child("failure", "child-failure", ("likely", "dangerous", "assumption"))
    child["agents"][0]["max_attempts"] = 3
    with pytest.raises(ZipJobRefusal) as caught:
        build_provider_nested_council_packet(
            owner_prompt=b"x",
            seed=1,
            run_id="r",
            mmm_files=_mmm(),
            children=[child, _child("repair", "child-repair", ("smallest", "test", "ceiling"))],
        )
    assert caught.value.reason_code == "REFUSE_PROVIDER_NESTED_RETRY_LIMIT"
