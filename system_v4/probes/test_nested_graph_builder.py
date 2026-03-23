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
    _build_layer_summary, build_nested_graph, LAYER_GRAPHS, REPO_ROOT,
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
        """Report has status field."""
        assert nested_result["report"]["status"] == "built"


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
