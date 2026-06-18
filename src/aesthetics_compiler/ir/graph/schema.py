from enum import Enum
from typing import Any
from pydantic import BaseModel


class NodeKind(str, Enum):
    ELEMENT      = "element"
    ZONE         = "zone"
    COLOR_SCHEME = "color_scheme"
    MOTIF        = "motif"
    TENSION_VEC  = "tension_vector"
    FACT         = "fact"


class EdgeKind(str, Enum):
    CONTAINS         = "contains"          # zone → element
    CONTRASTS        = "contrasts"         # element ↔ element (color/value contrast)
    GROUPED_WITH     = "grouped_with"      # element ↔ element (Gestalt proximity/similarity)
    ANCHORS          = "anchors"           # element → zone
    MIRRORS          = "mirrors"           # element ↔ element (symmetry)
    BELONGS_TO       = "belongs_to"        # element → color_scheme
    GENERATES_TENSION = "generates_tension" # element → tension_vector
    OVERLAPS         = "overlaps"          # element → element
    DOMINATES        = "dominates"         # element → element (visual weight)
    PART_OF_MOTIF    = "part_of_motif"     # element → motif


class AestheticNode(BaseModel):
    id: str
    kind: NodeKind
    label: str
    aesthetic_scores: dict[str, float] = {}
    metadata: dict[str, Any] = {}


class AestheticEdge(BaseModel):
    src: str
    dst: str
    kind: EdgeKind
    payload: dict[str, Any] = {}
