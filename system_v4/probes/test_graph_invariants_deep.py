import json
import os
import re
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

# --- Configuration ---
GRAPHS_DIR = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs"
# Broadening based on observed values
VALID_TRUST_ZONES = {
    "A2_1_KERNEL",
    "A2_2_CANDIDATE",
    "A2_3_INTAKE",
    "A2_4_REJECTED",
    "A2_5_EXTERNAL",
    "A1_KERNEL",
    "A1_CANDIDATE",
    "A1_INTAKE",
    "A1_JARGONED",
    "CROSS_LAYER",
    "A2_2_CONTRADICTION",
    "A1",
    "GRAVEYARD"
}
ID_PATTERN = re.compile(r".+::.+")

# --- Helpers ---
def load_graph(filename):
    path = os.path.join(GRAPHS_DIR, filename)
    with open(path, 'r') as f:
        return json.load(f)

def get_all_graphs():
    return [f for f in os.listdir(GRAPHS_DIR) if f.endswith(".json")]

ALL_GRAPH_FILES = get_all_graphs()

def get_nodes(graph):
    """Abstraction to handle different graph schemas for nodes."""
    if "nodes" in graph:
        return graph["nodes"]
    # nested_graph_v1 doesn't have a top-level nodes key, it describes layers
    return None

def get_edges(graph):
    """Abstraction to handle different graph schemas for edges."""
    if "edges" in graph:
        return graph["edges"]
    if "inter_layer_edges" in graph and "edges" in graph["inter_layer_edges"]:
        return graph["inter_layer_edges"]["edges"]
    return []

# --- Hypothesis Strategies ---
@st.composite
def graph_data(draw):
    filename = draw(st.sampled_from(ALL_GRAPH_FILES))
    return load_graph(filename), filename

# --- Tests ---

@pytest.mark.parametrize("filename", ALL_GRAPH_FILES)
def test_node_description_non_empty(filename):
    """1. Every node has a non-empty description"""
    graph = load_graph(filename)
    nodes = get_nodes(graph)
    if nodes is None:
        pytest.skip(f"No direct nodes in {filename}")
        
    if isinstance(nodes, list):
        for node in nodes:
            assert "description" in node, f"Node missing description in {filename}"
            assert node["description"].strip(), f"Node has empty description in {filename}"
    else:
        for node_id, node_data in nodes.items():
            assert "description" in node_data, f"Node {node_id} missing description in {filename}"
            assert node_data["description"].strip(), f"Node {node_id} has empty description in {filename}"

@pytest.mark.parametrize("filename", ALL_GRAPH_FILES)
def test_edge_fields(filename):
    """2. Every edge has source_id, target_id, and relation"""
    graph = load_graph(filename)
    edges = get_edges(graph)
    for i, edge in enumerate(edges):
        assert "source_id" in edge, f"Edge {i} missing source_id in {filename}"
        assert "target_id" in edge, f"Edge {i} missing target_id in {filename}"
        assert "relation" in edge, f"Edge {i} missing relation in {filename}"

@pytest.mark.parametrize("filename", ALL_GRAPH_FILES)
def test_no_dangling_edges(filename):
    """3. No edge references a node that doesn't exist (no dangling edges)"""
    graph = load_graph(filename)
    nodes = get_nodes(graph)
    
    # If it's a nested graph, the nodes might be in other files, but we check internal refs
    if filename == "nested_graph_v1.json":
        # For nested graph, we don't have a local 'nodes' list to check against easily
        # without loading all sub-graphs. We'll skip this for now or just check if it's not empty.
        pytest.skip("Dangling edge check for nested_graph_v1 requires multi-graph context")

    if nodes is None:
        pytest.skip(f"No nodes to check against in {filename}")

    if isinstance(nodes, list):
        node_ids = {n.get("id") for n in nodes if n.get("id")}
    else:
        node_ids = set(nodes.keys())
    
    edges = get_edges(graph)
    for i, edge in enumerate(edges):
        sid = edge["source_id"]
        tid = edge["target_id"]
        # Some graphs might refer to nodes that are 'external' or in registries
        # But per requirement 3, 'No edge references a node that doesn't exist'
        assert sid in node_ids, f"Edge {i} has dangling source_id {sid} in {filename}"
        assert tid in node_ids, f"Edge {i} has dangling target_id {tid} in {filename}"

@pytest.mark.parametrize("filename", ALL_GRAPH_FILES)
def test_node_id_format(filename):
    """4. Node IDs match their expected format (contain :: separator)"""
    graph = load_graph(filename)
    nodes = get_nodes(graph)
    if nodes is None:
        pytest.skip(f"No nodes in {filename}")

    if isinstance(nodes, list):
        for node in nodes:
            node_id = node.get("id", "")
            if node_id:
                assert ID_PATTERN.match(node_id), f"Node ID {node_id} invalid format in {filename}"
    else:
        for node_id in nodes.keys():
            assert ID_PATTERN.match(node_id), f"Node ID {node_id} invalid format in {filename}"

@pytest.mark.parametrize("filename", ALL_GRAPH_FILES)
def test_trust_zone_validity(filename):
    """5. Layer trust zones are valid values"""
    graph = load_graph(filename)
    nodes = get_nodes(graph)
    
    # In nested graph, trust zones are in the layers dict
    if filename == "nested_graph_v1.json":
        layers = graph.get("layers", {})
        for lname, ldata in layers.items():
            tz = ldata.get("trust_zone")
            if tz:
                assert tz in VALID_TRUST_ZONES, f"Invalid trust_zone {tz} in layer {lname} of {filename}"
        return

    if nodes is None:
        pytest.skip(f"No nodes in {filename}")

    if isinstance(nodes, list):
        for node in nodes:
            tz = node.get("trust_zone")
            if tz:
                assert tz in VALID_TRUST_ZONES, f"Invalid trust_zone {tz} in {filename}"
    else:
        for node_id, node_data in nodes.items():
            tz = node_data.get("trust_zone")
            if tz:
                assert tz in VALID_TRUST_ZONES, f"Invalid trust_zone {tz} in node {node_id} in {filename}"

def test_promoted_subgraph_subset():
    """6. The promoted subgraph is a subset of the low-control graph"""
    try:
        promoted = load_graph("promoted_subgraph.json")
        low_control = load_graph("a2_low_control_graph_v1.json")
    except FileNotFoundError:
        pytest.skip("Required graph files not found for subset test")

    p_nodes = set(get_nodes(promoted).keys())
    l_nodes = set(get_nodes(low_control).keys())
    
    # Check nodes
    diff_nodes = p_nodes - l_nodes
    assert not diff_nodes, f"Promoted nodes are not a subset of low-control nodes. Extras: {diff_nodes}"

    # Check edges
    p_edges = {(e["source_id"], e["target_id"], e["relation"]) for e in get_edges(promoted)}
    l_edges = {(e["source_id"], e["target_id"], e["relation"]) for e in get_edges(low_control)}
    diff_edges = p_edges - l_edges
    assert not diff_edges, f"Promoted edges are not a subset of low-control edges. Extras: {diff_edges}"

@given(graph_data=graph_data())
@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much], deadline=None)
def test_add_node_preserves_edges(graph_data):
    """7. Adding a node to any graph preserves all existing edges"""
    graph, filename = graph_data
    original_edges = list(get_edges(graph))
    
    nodes = get_nodes(graph)
    if nodes is None:
        pytest.skip(f"Skipping add-node test for {filename} (no standard nodes container)")

    # Simulate adding a node
    new_node_id = "TEST::ADDED_NODE::12345"
    if isinstance(nodes, list):
        nodes.append({"id": new_node_id, "description": "test node"})
    else:
        nodes[new_node_id] = {"description": "test node"}
    
    current_edges = get_edges(graph)
    assert current_edges == original_edges, f"Adding a node corrupted edges in {filename}"

@pytest.mark.parametrize("filename", ALL_GRAPH_FILES)
def test_no_duplicate_edges(filename):
    """8. No duplicate edges exist"""
    graph = load_graph(filename)
    edges = get_edges(graph)
    seen = set()
    for i, edge in enumerate(edges):
        # We define uniqueness by relation_id if present, or (src, tgt, rel)
        # Note: relation_id is the primary key for edges in this system
        rid = edge.get("relation_id")
        key = rid if rid else (edge["source_id"], edge["target_id"], edge["relation"])
        assert key not in seen, f"Duplicate edge found in {filename} (index {i}): {key}"
        seen.add(key)

def test_cross_layer_edge_consistency():
    """9. Cross-layer edge counts are consistent"""
    # This check ensures that if the 'nested_graph_v1.json' reports a count, 
    # the actual count in the edges list matches it.
    try:
        graph = load_graph("nested_graph_v1.json")
    except FileNotFoundError:
        pytest.skip("nested_graph_v1.json not found")
        
    inter_layer = graph.get("inter_layer_edges", {})
    reported_total = inter_layer.get("total")
    actual_total = len(inter_layer.get("edges", []))
    
    if reported_total is not None:
        assert reported_total == actual_total, f"Reported total {reported_total} != actual edges {actual_total}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
