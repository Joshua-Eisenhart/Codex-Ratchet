"""
Phase 3 pytest tests for nested_graph_builder.py

These tests allow mutmut to evaluate test quality and are
also Hypothesis-powered domain invariants for the nested graph.
"""
import json
import pytest
from pathlib import Path
from hypothesis import given, strategies as st, settings, HealthCheck

# Import the module under test
from system_v4.skills.nested_graph_builder import (
    _load_json, _write_json, _node_id, _utc_iso,
    _build_layer_summary, _find_cross_layer_edges,
    build_nested_graph, LAYER_GRAPHS, REPO_ROOT,
)


# ── Unit tests for pure functions ──

class TestNodeId:
    def test_deterministic(self):
        """Same input always gives same hash."""
        assert _node_id("A", "foo") == _node_id("A", "foo")

    def test_different_inputs_different_hashes(self):
        """Different inputs should produce different hashes."""
        assert _node_id("A", "foo") != _node_id("B", "foo")
        assert _node_id("A", "foo") != _node_id("A", "bar")

    def test_length(self):
        """Hash should be 16 chars."""
        assert len(_node_id("prefix", "name")) == 16

    @settings(max_examples=50, suppress_health_check=[HealthCheck.differing_executors])
    @given(st.text(min_size=1, max_size=50), st.text(min_size=1, max_size=50))
    def test_always_16_chars(self, prefix, name):
        """Property: _node_id always returns 16-char string."""
        result = _node_id(prefix, name)
        assert isinstance(result, str)
        assert len(result) == 16


class TestUtcIso:
    def test_format(self):
        """UTC timestamp should match ISO format."""
        ts = _utc_iso()
        assert ts.endswith("Z")
        assert "T" in ts
        assert len(ts) == 20  # "2026-03-22T01:23:45Z"


class TestLoadJson:
    def test_missing_file(self, tmp_path):
        """Missing file returns empty dict."""
        result = _load_json(tmp_path / "nonexistent.json")
        assert result == {}

    def test_valid_json(self, tmp_path):
        """Valid JSON file loads correctly."""
        f = tmp_path / "test.json"
        f.write_text('{"key": "value"}')
        result = _load_json(f)
        assert result == {"key": "value"}

    def test_invalid_json(self, tmp_path):
        """Invalid JSON returns empty dict."""
        f = tmp_path / "bad.json"
        f.write_text('not json {')
        result = _load_json(f)
        assert result == {}


class TestWriteJson:
    def test_creates_file(self, tmp_path):
        """Write creates file with correct content."""
        f = tmp_path / "out.json"
        _write_json(f, {"test": True})
        assert f.exists()
        data = json.loads(f.read_text())
        assert data["test"] is True

    def test_creates_parent_dirs(self, tmp_path):
        """Write creates parent directories."""
        f = tmp_path / "a" / "b" / "out.json"
        _write_json(f, {"nested": True})
        assert f.exists()


# ── Integration tests with real repo data ──

class TestBuildLayerSummary:
    def test_low_control_loads(self):
        """Low-control graph loads and has expected structure."""
        summary = _build_layer_summary(REPO_ROOT, "A2_LOW_CONTROL", LAYER_GRAPHS["A2_LOW_CONTROL"])
        assert summary["layer_id"] == "A2_LOW_CONTROL"
        assert summary["node_count"] > 0
        assert summary["edge_count"] >= 0
        assert summary["rank"] == 2
        assert summary["trust_zone"] == "A2_1_KERNEL"

    def test_all_layers_have_nodes_or_are_empty(self):
        """Every configured layer loads without error."""
        for layer_id, cfg in LAYER_GRAPHS.items():
            summary = _build_layer_summary(REPO_ROOT, layer_id, cfg)
            assert summary["layer_id"] == layer_id
            assert isinstance(summary["node_count"], int)
            assert isinstance(summary["edge_count"], int)


class TestBuildNestedGraph:
    @pytest.fixture(scope="class")
    def nested_result(self):
        return build_nested_graph(REPO_ROOT)

    def test_has_layers(self, nested_result):
        """Nested graph output has layers."""
        ng = nested_result["nested_graph"]
        assert "layers" in ng
        assert len(ng["layers"]) > 0

    def test_layers_have_required_keys(self, nested_result):
        """Every layer has node_count, edge_count, rank, trust_zone."""
        for lid, layer in nested_result["nested_graph"]["layers"].items():
            assert "node_count" in layer
            assert "edge_count" in layer
            assert "rank" in layer
            assert "trust_zone" in layer

    def test_has_hierarchy(self, nested_result):
        """Nested graph has hierarchy definition."""
        ng = nested_result["nested_graph"]
        assert "hierarchy" in ng
        assert len(ng["hierarchy"]) > 0

    def test_cross_edges_are_list(self, nested_result):
        """Cross edges should be a list."""
        assert isinstance(nested_result["cross_edges"], list)

    def test_report_has_status(self, nested_result):
        """Report has status continuous_operator."""
        assert nested_result["report"]["status"] == "built"


class TestStrongBridgeResolution:
    def test_resolves_qit_public_id_on_edge_endpoint(self, tmp_path):
        """Cross-layer discovery should resolve QIT endpoints by public_id."""
        qit_path = tmp_path / LAYER_GRAPHS["QIT_ENGINE"]["path"]
        _write_json(qit_path, {
            "nodes": {
                "qit_hash_1": {
                    "public_id": "qit::ENGINE::type1_left_weyl",
                    "node_type": "ENGINE",
                }
            },
            "edges": [],
            "public_id_index": {
                "qit::ENGINE::type1_left_weyl": "qit_hash_1",
            },
        })

        accum_path = tmp_path / "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
        _write_json(accum_path, {
            "nodes": {
                "SIM::demo": {"node_type": "SIM_EVIDENCED", "properties": {}},
            },
            "edges": [
                {
                    "source_id": "SIM::demo",
                    "target_id": "missing_qit_hash",
                    "target_public_id": "qit::ENGINE::type1_left_weyl",
                    "relation": "SIM_EVIDENCE_FOR",
                    "attributes": {},
                }
            ],
        })

        cross_edges = _find_cross_layer_edges(tmp_path)
        assert len(cross_edges) == 1
        edge = cross_edges[0]
        assert edge["source_layer"] == "SIM_LAYER"
        assert edge["target_layer"] == "QIT_ENGINE"
        assert edge["resolved_target_id"] == "qit_hash_1"
        assert edge["target_resolved_via"] == "public_id"
        assert edge["discovery_mode"] == "explicit_edge"

    def test_derives_source_concept_id_bridge_without_fake_label_match(self, tmp_path):
        """Strong bridge fields should materialize a cross-layer bridge even without an explicit edge."""
        a2_high_path = tmp_path / LAYER_GRAPHS["A2_HIGH_INTAKE"]["path"]
        concept_id = "A2_3::QIT_BRIDGE_PASS::Entropy as Spacetime (Axiom)::2ab647479e76a51a"
        _write_json(a2_high_path, {
            "nodes": {
                concept_id: {
                    "node_type": "EXTRACTED_CONCEPT",
                    "description": "QIT bridge concept",
                }
            },
            "edges": [],
        })

        accum_path = tmp_path / "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
        _write_json(accum_path, {
            "nodes": {
                "GRAVEYARD_RECORD::demo": {
                    "node_type": "GRAVEYARD_RECORD",
                    "properties": {
                        "source_concept_id": concept_id,
                    },
                }
            },
            "edges": [],
        })

        cross_edges = _find_cross_layer_edges(tmp_path)
        assert len(cross_edges) == 1
        edge = cross_edges[0]
        assert edge["relation"] == "SOURCE_CONCEPT_ID_BRIDGE"
        assert edge["source_layer"] == "GRAVEYARD"
        assert edge["target_layer"] == "A2_HIGH_INTAKE"
        assert edge["target_id"] == concept_id
        assert edge["attributes"]["bridge_field"] == "source_concept_id"
        assert edge["discovery_mode"] == "strong_bridge_field"

    def test_registry_source_layer_overrides_promoted_subgraph_when_explicit(self, tmp_path):
        """Explicit QIT registry rows should honor a pinned source layer when a node exists in multiple graphs."""
        source_id = "A2_1::KERNEL::KERNEL: Chiral Game Theory Operators::189a01b4b3cd537c"

        _write_json(tmp_path / LAYER_GRAPHS["A2_LOW_CONTROL"]["path"], {
            "nodes": {
                source_id: {
                    "node_type": "KERNEL_CONCEPT",
                    "description": "kernel anchor",
                }
            },
            "edges": [],
        })
        _write_json(tmp_path / LAYER_GRAPHS["PROMOTED_SUBGRAPH"]["path"], {
            "nodes": {
                source_id: {
                    "node_type": "KERNEL_CONCEPT",
                    "description": "promoted copy",
                }
            },
            "edges": [],
        })
        _write_json(tmp_path / LAYER_GRAPHS["QIT_ENGINE"]["path"], {
            "nodes": {
                "qit_op_ti": {
                    "public_id": "qit::OPERATOR::Ti",
                    "node_type": "OPERATOR",
                }
            },
            "edges": [],
            "public_id_index": {
                "qit::OPERATOR::Ti": "qit_op_ti",
            },
        })
        _write_json(tmp_path / "system_v4/a2_state/graphs/system_graph_a2_refinery.json", {
            "nodes": {},
            "edges": [],
        })
        _write_json(tmp_path / "system_v4/a2_state/graphs/qit_cross_layer_registry_v1.json", {
            "bridges": [
                {
                    "bridge_id": "qit_operator_family_ti",
                    "status": "ADMITTED",
                    "source_id": source_id,
                    "source_layer": "A2_LOW_CONTROL",
                    "target_public_id": "qit::OPERATOR::Ti",
                    "relation": "QIT_OPERATOR_FAMILY_BRIDGE",
                    "bridge_via": "manual_registry",
                    "scope": "family_member_bridge",
                    "rationale": "Pinned to kernel owner layer.",
                }
            ]
        })

        cross_edges = _find_cross_layer_edges(tmp_path)
        registry_edges = [e for e in cross_edges if e["discovery_mode"] == "explicit_bridge_registry"]
        assert len(registry_edges) == 1
        edge = registry_edges[0]
        assert edge["source_layer"] == "A2_LOW_CONTROL"
        assert edge["target_layer"] == "QIT_ENGINE"
        assert edge["attributes"]["registry_source_layer"] == "A2_LOW_CONTROL"
        assert edge["attributes"]["target_public_id"] == "qit::OPERATOR::Ti"

    def test_uses_explicit_qit_bridge_registry(self, tmp_path):
        """Explicit admitted registry bridges should materialize cross-layer QIT links."""
        a2_low_path = tmp_path / LAYER_GRAPHS["A2_LOW_CONTROL"]["path"]
        _write_json(a2_low_path, {
            "nodes": {
                "A2_2::REFINED::a2_axis_0_first_principle::demo": {
                    "node_type": "REFINED_CONCEPT",
                    "description": "Axis 0 bridge candidate",
                }
            },
            "edges": [],
        })

        qit_path = tmp_path / LAYER_GRAPHS["QIT_ENGINE"]["path"]
        _write_json(qit_path, {
            "nodes": {
                "qit_hash_axis0": {
                    "public_id": "qit::AXIS::axis_0",
                    "node_type": "AXIS",
                }
            },
            "edges": [],
            "public_id_index": {
                "qit::AXIS::axis_0": "qit_hash_axis0",
            },
        })

        _write_json(tmp_path / "system_v4/a2_state/graphs/system_graph_a2_refinery.json", {
            "nodes": {
                "A2_2::REFINED::a2_axis_0_first_principle::demo": {
                    "node_type": "REFINED_CONCEPT",
                }
            },
            "edges": [],
        })

        _write_json(tmp_path / "system_v4/a2_state/graphs/qit_cross_layer_registry_v1.json", {
            "bridges": [
                {
                    "bridge_id": "demo_axis0_bridge",
                    "status": "ADMITTED",
                    "source_id": "A2_2::REFINED::a2_axis_0_first_principle::demo",
                    "target_public_id": "qit::AXIS::axis_0",
                    "relation": "QIT_AXIS_BRIDGE",
                    "bridge_via": "manual_registry",
                    "scope": "exact_admitted_mapping",
                    "rationale": "Axis-0 first-principle concept is explicitly admitted as the bridge anchor.",
                }
            ]
        })

        cross_edges = _find_cross_layer_edges(tmp_path)
        assert len(cross_edges) == 1
        edge = cross_edges[0]
        assert edge["relation"] == "QIT_AXIS_BRIDGE"
        assert edge["source_layer"] == "A2_LOW_CONTROL"
        assert edge["target_layer"] == "QIT_ENGINE"
        assert edge["resolved_target_id"] == "qit_hash_axis0"
        assert edge["discovery_mode"] == "explicit_bridge_registry"


# ── Hypothesis domain invariants ──

class TestGraphInvariants:
    @pytest.fixture(scope="class")
    def low_control_data(self):
        path = REPO_ROOT / LAYER_GRAPHS["A2_LOW_CONTROL"]["path"]
        return _load_json(path)

    def test_all_nodes_have_description(self, low_control_data):
        """Every node in low-control graph has a non-empty description."""
        nodes = low_control_data.get("nodes", {})
        for nid, attrs in nodes.items():
            if isinstance(attrs, dict):
                assert "description" in attrs, f"Node {nid[:50]} missing description"
                assert len(str(attrs["description"])) > 0

    def test_all_edges_have_relation(self, low_control_data):
        """Every edge has a relation type."""
        edges = low_control_data.get("edges", [])
        for e in edges:
            assert "relation" in e, f"Edge missing relation: {str(e)[:100]}"
            assert len(e["relation"]) > 0

    def test_all_edges_have_endpoints(self, low_control_data):
        """Every edge has source_id and target_id."""
        edges = low_control_data.get("edges", [])
        for e in edges:
            assert "source_id" in e, f"Edge missing source_id"
            assert "target_id" in e, f"Edge missing target_id"
