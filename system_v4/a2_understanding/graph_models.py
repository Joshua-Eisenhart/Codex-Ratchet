import enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, ConfigDict, Field

class SurfaceClass(str, enum.Enum):
    ACTIVE = "ACTIVE"
    HISTORICAL = "HISTORICAL"
    SUPPORT = "SUPPORT"
    FUEL = "FUEL"
    QUARANTINE = "QUARANTINE"
    UNKNOWN = "UNKNOWN"

class NodeType(str, enum.Enum):
    SOURCE_MASS = "SOURCE_MASS"
    SYSTEM_NODE = "SYSTEM_NODE"
    ACTIVE_SURFACE = "ACTIVE_SURFACE"
    # Other types can be defined here.

class EdgeType(str, enum.Enum):
    APPENDS_TO = "APPENDS_TO"
    SAVES_FROM = "SAVES_FROM"
    CARRIES_STATE = "CARRIES_STATE"
    RELATES_TO = "RELATES_TO"
    DEPENDS_ON = "DEPENDS_ON"
    # Additional semantic relations

class BaseGraphNode(BaseModel):
    id: str = Field(description="Unique identifier for the node, usually the filepath or abstract concept name.")
    node_type: NodeType
    surface_class: SurfaceClass = SurfaceClass.UNKNOWN
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class FileNode(BaseGraphNode):
    filepath: str
    filename: str
    content_hash: Optional[str] = None
    
class AbstractNode(BaseGraphNode):
    name: str

class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    edge_type: EdgeType
    metadata: Dict[str, Any] = Field(default_factory=dict)
