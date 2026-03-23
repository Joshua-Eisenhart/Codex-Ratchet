import os
import hashlib
import networkx as nx
from pathlib import Path
from typing import Dict, List, Any
import json

from graph_models import (
    SurfaceClass, NodeType, EdgeType, BaseGraphNode, FileNode, AbstractNode, GraphEdge
)

def compute_hash(filepath: str) -> str:
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

class A2GraphBuilder:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.graph = nx.MultiDiGraph()
        self.nodes: Dict[str, BaseGraphNode] = {}
        self.edges: List[GraphEdge] = []
        
    def _add_node(self, node: BaseGraphNode):
        self.nodes[node.id] = node
        self.graph.add_node(node.id, **node.model_dump())
        
    def _add_edge(self, edge: GraphEdge):
        self.edges.append(edge)
        self.graph.add_edge(edge.source_id, edge.target_id, key=edge.edge_type.value, **edge.model_dump())

    def index_directory(self, target_dir_relative: str, surface_class: SurfaceClass = SurfaceClass.UNKNOWN, node_type: NodeType = NodeType.SOURCE_MASS):
        target_path = self.root_dir / target_dir_relative
        if not target_path.exists() or not target_path.is_dir():
            print(f"Warning: Directory {target_path} does not exist. Skipping.")
            return

        for root, _, files in os.walk(target_path):
            for file in files:
                # Skip invisible files and git objects
                if file.startswith('.') or '.git' in root:
                    continue
                
                filepath = Path(root) / file
                rel_path = filepath.relative_to(self.root_dir)
                str_rel_path = str(rel_path)
                
                try:
                    file_hash = compute_hash(str(filepath))
                except Exception as e:
                    print(f"Failed to hash {filepath}: {e}")
                    file_hash = None
                
                node = FileNode(
                    id=str_rel_path,
                    node_type=node_type,
                    surface_class=surface_class,
                    filepath=str(filepath),
                    filename=file,
                    content_hash=file_hash,
                    metadata={"scanned": True, "ext": filepath.suffix}
                )
                self._add_node(node)

    def extract_relations(self):
        # A placeholder for future extraction logic across nodes.
        # This will later read file contents to find links, explicit save patterns, etc.
        pass

    def build(self):
        # 1. Whole-system understanding via system_v3 indexing
        self.index_directory("system_v3/runs", SurfaceClass.ACTIVE, NodeType.SYSTEM_NODE)
        self.index_directory("system_v3/a2_state", SurfaceClass.ACTIVE, NodeType.SYSTEM_NODE)
        self.index_directory("system_v3/specs", SurfaceClass.SUPPORT, NodeType.SYSTEM_NODE)
        
        # 2. Add high entropy docs
        self.index_directory("core_docs/a1_refined_Ratchet Fuel", SurfaceClass.FUEL, NodeType.SOURCE_MASS)
        self.index_directory("core_docs/a2_feed_high entropy doc", SurfaceClass.FUEL, NodeType.SOURCE_MASS)
        self.index_directory("core_docs/v4 upgrades", SurfaceClass.SUPPORT, NodeType.SOURCE_MASS)
        self.index_directory("core_docs/upgrade docs", SurfaceClass.SUPPORT, NodeType.SOURCE_MASS)
        
        self.extract_relations()
        
    def export_graphml(self, output_path: str):
        # Export for potential Gephi/Cytoscape visualization, ignoring complex nested dicts for graphml compat.
        export_graph = self.graph.copy()
        for _, data in export_graph.nodes(data=True):
            if "metadata" in data:
                data["metadata"] = str(data["metadata"])
                
        for u, v, k, data in export_graph.edges(data=True, keys=True):
            if "metadata" in data:
                data["metadata"] = str(data["metadata"])
                
        nx.write_graphml(export_graph, output_path)
        print(f"Exported to {output_path}")

    def summary(self):
        print(f"Graph constructed with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges.")
        classes = {}
        for _, data in self.graph.nodes(data=True):
            cls = data.get("surface_class", "UNKNOWN")
            classes[cls] = classes.get(cls, 0) + 1
        
        print("Nodes by surface class:")
        for k, v in classes.items():
            print(f" - {k}: {v}")

if __name__ == "__main__":
    builder = A2GraphBuilder("../../")
    builder.build()
    builder.summary()
