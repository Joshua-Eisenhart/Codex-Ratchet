import json
import hashlib
import os
import tempfile
import networkx as nx
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from system_v4.skills.graph_store import load_graph_json

# --- Pydantic Definitions for the System Graph Nodes --- #

class GraphNode(BaseModel):
    id: str
    node_type: str = Field(..., description="E.g. SOURCE_DOCUMENT, EXTRACTED_CONCEPT, REFINED_CONCEPT, KERNEL_CONCEPT")
    layer: str = Field(..., description="E.g. INDEX, A2_HIGH_INTAKE, A2_MID_REFINEMENT, A2_LOW_CONTROL, A1_JARGONED, ...")
    name: str
    description: str
    original_path: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    # Authority (entropy-gradient, not canon-claim)
    authority: str = Field(default="SOURCE_CLAIM", description="SOURCE_CLAIM → CROSS_VALIDATED → RATCHETED")
    tags: List[str] = Field(default_factory=list)
    
    # RegistryRecord Integration
    object_family: str = "RuntimeProcessRecord"
    source_class: str = "DERIVED"
    status: str = "LIVE"
    trust_zone: str = "A2_3_INTAKE"
    admissibility_state: str = "PROPOSAL_ONLY"
    lineage_refs: List[str] = Field(default_factory=list)
    witness_refs: List[str] = Field(default_factory=list)

class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation: str = Field(..., description="E.g. IMPLEMENTS, VALIDATES, DEPENDS_ON, PROPOSES_TO")
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # RegistryRelation Integration
    relation_id: Optional[str] = None
    status: str = "LIVE"
    source_class: str = "DERIVED"
    trust_zone: str = "A2_SANDBOX"

class V4SystemGraph(BaseModel):
    nodes: Dict[str, GraphNode] = Field(default_factory=dict)
    edges: List[GraphEdge] = Field(default_factory=list)


# --- Graph Management Skill --- #

class SystemGraphBuilder:
    """
    Manages the active runtime representation of the System V4 topological graph.
    Used by the A2 Brain to understand the system dependencies, tools, bounds,
    and engine loops without relying on classical flattenings.
    
    ALL graph mutations MUST go through add_node/add_edge/update_node.
    Direct manipulation of pydantic_model is a contract violation.
    """
    
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        self.a2_sandbox_dir = self.workspace_root / "system_v4" / "a2_state" / "graphs"
        self.a2_sandbox_dir.mkdir(parents=True, exist_ok=True)
        self.graph = nx.MultiDiGraph()
        self.pydantic_model = V4SystemGraph()
        self._edge_index: Set[Tuple[str, str, str]] = set()  # (src, tgt, rel) dedup
        self._overlay_audit_namespaces: Set[str] = {
            "overlay_audit",
            "overlay_provenance_audit",
            "nonowner_overlay",
        }
        self._overlay_audit_forbidden_fields: Set[str] = {
            "lineage_refs",
            "witness_refs",
            "source_intent_ids",
            "relation_refs",
            "source_concept_id",
            "target_ref",
            "candidate_id",
            "source_class",
            "trust_zone",
            "authority",
            "admissibility_state",
            "runtime_policy",
            "control",
            "guidance",
            "approved",
            "promotion_ready",
            "recommended_binding",
            "source_node_ids",
            "source_witness_refs",
            "source_lineage_refs",
        }

    def _rebuild_runtime_views(self) -> None:
        """Rebuild NetworkX graph + edge index from the pydantic model."""
        self.graph.clear()
        self._edge_index.clear()
        for n_id, node in self.pydantic_model.nodes.items():
            self.graph.add_node(
                n_id,
                type=node.node_type,
                layer=node.layer,
                name=node.name,
                authority=node.authority,
                tags=node.tags,
                trust_zone=node.trust_zone,
                **node.properties
            )
        for edge in self.pydantic_model.edges:
            self._edge_index.add((edge.source_id, edge.target_id, edge.relation))
            self.graph.add_edge(
                edge.source_id,
                edge.target_id,
                relation=edge.relation,
                **edge.attributes
            )

    def _export_graph_for_graphml(self) -> nx.MultiDiGraph:
        """Return a GraphML-safe export copy with nested attrs stringified."""
        import re
        # XML 1.0 valid characters (preventing ValueError in networkx write_graphml)
        _illegal_xml_chars_RE = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]')

        def sanitize(val: Any) -> str:
            if val is None:
                return ""
            if isinstance(val, (dict, list)):
                s = json.dumps(val)
            else:
                s = str(val)
            return _illegal_xml_chars_RE.sub('', s)

        export_graph = self.graph.copy()
        
        for node, data in export_graph.nodes(data=True):
            for k, v in data.items():
                export_graph.nodes[node][k] = sanitize(v)

        for u, v, k, data in export_graph.edges(data=True, keys=True):
            for attr_k, attr_v in data.items():
                export_graph.edges[u, v, k][attr_k] = sanitize(attr_v)
                
        return export_graph

    def load_graph_json_path(self, json_path: str | Path) -> bool:
        """Load graph data from an arbitrary JSON path."""
        path = Path(json_path)
        if not path.exists():
            return False
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            self.pydantic_model = V4SystemGraph(**data)
        self._rebuild_runtime_views()
        return True

    def load_multi_repo_provenance(self, json_path: str | Path) -> bool:
        """
        Merge the multi-repo provenance graph directly into the active system graph.
        These nodes are added to a special read-only PROVENANCE_INGEST layer, preserving
        their authority_class and repo fingerprints, ensuring they do not overwrite canon.
        """
        path = Path(json_path)
        try:
            prov_graph = load_graph_json(
                self.workspace_root,
                str(path.relative_to(self.workspace_root)),
                default={},
            )
        except ValueError:
            if not path.exists():
                return False
            with path.open("r", encoding="utf-8") as f:
                prov_graph = json.load(f)
        if not prov_graph:
            return False
            
        for n_id, n_data in prov_graph.get("nodes", {}).items():
            provenance = n_data.get("provenance", {})
            auth_class = provenance.get("authority_class", "UNKNOWN")
            
            node = GraphNode(
                id=n_id,
                node_type=n_data.get("node_type", "DOCUMENT"),
                layer="PROVENANCE_INGEST",
                name=n_data.get("label", n_id),
                description=f"Ingested node from {provenance.get('repo', '?')}",
                original_path=provenance.get("path"),
                authority=auth_class,
                properties={"provenance": provenance}
            )
            # Use add_node so it handles the pydantic Model and nx sync
            self.add_node(node)
            
        return True

    def save_graph_snapshot_paths(
        self,
        json_path: str | Path,
        graphml_path: str | Path | None = None,
    ) -> None:
        """Save the current graph to explicit JSON/GraphML snapshot paths."""
        json_path = Path(json_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)

        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(json_path.parent), suffix=".json.tmp"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(self.pydantic_model.model_dump_json(indent=2))
            os.replace(tmp_path, str(json_path))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

        if graphml_path is None:
            graphml_path = json_path.with_suffix(".graphml")
        graphml_path = Path(graphml_path)
        graphml_path.parent.mkdir(parents=True, exist_ok=True)
        export_graph = self._export_graph_for_graphml()

        tmp_fd2, tmp_path2 = tempfile.mkstemp(
            dir=str(graphml_path.parent), suffix=".graphml.tmp"
        )
        os.close(tmp_fd2)
        try:
            nx.write_graphml(export_graph, tmp_path2)
            os.replace(tmp_path2, str(graphml_path))
        except Exception:
            if os.path.exists(tmp_path2):
                os.unlink(tmp_path2)
            raise

    def add_node(self, node: GraphNode) -> None:
        """Add a node. If node.id already exists, this is a no-op (use update_node to modify)."""
        if node.id in self.pydantic_model.nodes:
            return
        self.pydantic_model.nodes[node.id] = node
        self.graph.add_node(
            node.id, 
            type=node.node_type, 
            layer=node.layer, 
            name=node.name,
            authority=node.authority,
            tags=node.tags,
            trust_zone=node.trust_zone,
            **node.properties
        )

    def update_node(self, node_id: str, **kwargs) -> bool:
        """Update specific fields on an existing node. Returns False if node doesn't exist."""
        if node_id not in self.pydantic_model.nodes:
            return False
        existing = self.pydantic_model.nodes[node_id]
        prior_properties = dict(existing.properties)
        for key, value in kwargs.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        # Sync to NetworkX
        if node_id in self.graph:
            nx_data = self.graph.nodes[node_id]
            if "node_type" in kwargs:
                nx_data["type"] = kwargs["node_type"]
            if "layer" in kwargs:
                nx_data["layer"] = kwargs["layer"]
            if "name" in kwargs:
                nx_data["name"] = kwargs["name"]
            if "authority" in kwargs:
                nx_data["authority"] = kwargs["authority"]
            if "tags" in kwargs:
                nx_data["tags"] = kwargs["tags"]
            if "trust_zone" in kwargs:
                nx_data["trust_zone"] = kwargs["trust_zone"]
            if "properties" in kwargs and isinstance(kwargs["properties"], dict):
                for prop_key in list(prior_properties.keys()):
                    nx_data.pop(prop_key, None)
                for prop_key, prop_value in kwargs["properties"].items():
                    nx_data[prop_key] = prop_value
        return True

    def merge_overlay_audit(
        self,
        node_id: str,
        namespace: str,
        payload: Dict[str, Any],
    ) -> bool:
        """
        Merge a fail-closed audit-only overlay payload into node.properties[namespace].

        This helper is intentionally narrow:
        - allowed namespaces are fixed audit-only namespaces
        - payload must remain audit_only_nonoperative
        - provenance-like keys are rejected even inside the namespace
        """
        if node_id not in self.pydantic_model.nodes:
            return False
        clean_namespace = namespace.strip()
        if clean_namespace not in self._overlay_audit_namespaces:
            return False
        if not isinstance(payload, dict):
            return False
        if payload.get("status") != "audit_only_nonoperative":
            return False
        if payload.get("runtime_effect") != "none":
            return False
        if payload.get("audit_only") is not True:
            return False
        if self._payload_contains_forbidden_overlay_keys(payload):
            return False
        existing = self.pydantic_model.nodes[node_id]
        props = dict(existing.properties)
        existing_namespace = props.get(clean_namespace, {})
        if existing_namespace and not isinstance(existing_namespace, dict):
            return False
        merged_namespace = dict(existing_namespace) if isinstance(existing_namespace, dict) else {}
        merged_namespace.update(payload)
        props[clean_namespace] = merged_namespace
        return self.update_node(node_id, properties=props)

    def _payload_contains_forbidden_overlay_keys(self, payload: Any) -> bool:
        if isinstance(payload, dict):
            for key, value in payload.items():
                if str(key) in self._overlay_audit_forbidden_fields:
                    return True
                if self._payload_contains_forbidden_overlay_keys(value):
                    return True
        elif isinstance(payload, list):
            for item in payload:
                if self._payload_contains_forbidden_overlay_keys(item):
                    return True
        return False

    def add_edge(self, edge: GraphEdge) -> bool:
        """Add an edge. Returns False if duplicate (same src+tgt+relation already exists)."""
        dedup_key = (edge.source_id, edge.target_id, edge.relation)
        if dedup_key in self._edge_index:
            return False
        # Auto-generate relation_id if missing
        if not edge.relation_id:
            edge.relation_id = hashlib.sha256(
                f"{edge.source_id}|{edge.target_id}|{edge.relation}".encode()
            ).hexdigest()[:16]
        self._edge_index.add(dedup_key)
        self.pydantic_model.edges.append(edge)
        self.graph.add_edge(
            edge.source_id, 
            edge.target_id, 
            relation=edge.relation,
            **edge.attributes
        )
        return True

    def node_exists(self, node_id: str) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self.pydantic_model.nodes

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID, or None."""
        return self.pydantic_model.nodes.get(node_id)

    def save_graph_artifacts(self, version_label: str = "latest") -> None:
        """
        Saves the active graph to both a readable JSON (Pydantic model)
        and a standard GraphML format for topological analysis.
        Uses atomic writes (write to tmp, rename) to prevent partial-file reads.
        """
        json_path = self.a2_sandbox_dir / f"system_graph_{version_label}.json"
        graphml_path = self.a2_sandbox_dir / f"system_graph_{version_label}.graphml"
        self.save_graph_snapshot_paths(json_path, graphml_path)

    def load_graph_artifacts(self, version_label: str = "latest") -> bool:
        """Loads an existing graph from the A2 sandbox JSON file."""
        json_path = self.a2_sandbox_dir / f"system_graph_{version_label}.json"
        return self.load_graph_json_path(json_path)
