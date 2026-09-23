"""Spatial analysis primitives."""

from src.spatial.components import (
    BoundingBox,
    LitComponent,
    components_to_payload,
    find_lit_components,
)
from src.spatial.candidates import (
    DEFAULT_CANDIDATE_THRESHOLDS,
    CandidateCompositeBox,
    candidate_boxes_to_payload,
    generate_candidate_boxes,
)
from src.spatial.relationships import (
    ComponentRelationship,
    component_relationship,
    find_component_relationships,
    relationships_to_payload,
)
from src.spatial.regions import (
    RegionSplitBand,
    RegionSplitEvidence,
    RefinedSpatialRegion,
    SpatialRegion,
    discover_spatial_regions,
    find_region_split_evidence,
    refined_regions_to_payload,
    region_split_evidence_to_payload,
    regions_to_payload,
    refine_spatial_regions,
)

__all__ = [
    "BoundingBox",
    "CandidateCompositeBox",
    "ComponentRelationship",
    "DEFAULT_CANDIDATE_THRESHOLDS",
    "candidate_boxes_to_payload",
    "LitComponent",
    "RegionSplitBand",
    "RegionSplitEvidence",
    "RefinedSpatialRegion",
    "SpatialRegion",
    "component_relationship",
    "components_to_payload",
    "discover_spatial_regions",
    "find_region_split_evidence",
    "generate_candidate_boxes",
    "find_lit_components",
    "find_component_relationships",
    "refine_spatial_regions",
    "refined_regions_to_payload",
    "region_split_evidence_to_payload",
    "regions_to_payload",
    "relationships_to_payload",
]
