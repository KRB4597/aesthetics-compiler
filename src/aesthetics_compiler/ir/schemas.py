from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, field_validator
import math

from aesthetics_compiler import SCHEMA_VERSION

AESTHETIC_DIMENSIONS: tuple[str, ...] = (
    "complexity",
    "order",
    "balance",
    "density",
    "hue_coherence",
    "saturation",
    "contrast",
    "color_harmony",
    "tension",
    "closure",
    "rhythm",
)

DIMENSION_INDEX: dict[str, int] = {d: i for i, d in enumerate(AESTHETIC_DIMENSIONS)}


def _direction(v: float) -> str:
    a = abs(v)
    if a >= 0.65:
        return "dominant"
    if a >= 0.35:
        return "present"
    if a >= 0.10:
        return "trace"
    return "absent"


class DimensionScore(BaseModel):
    value: float
    confidence: float
    direction: Literal["dominant", "present", "trace", "absent"]
    explanation: str | None = None

    @field_validator("value")
    @classmethod
    def clamp_value(cls, v: float) -> float:
        return max(-1.0, min(1.0, v))

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class AestheticVector(BaseModel):
    complexity:    DimensionScore = DimensionScore(value=0.0, confidence=0.5, direction="absent")
    order:         DimensionScore = DimensionScore(value=0.0, confidence=0.5, direction="absent")
    balance:       DimensionScore = DimensionScore(value=0.0, confidence=0.5, direction="absent")
    density:       DimensionScore = DimensionScore(value=0.0, confidence=0.5, direction="absent")
    hue_coherence: DimensionScore = DimensionScore(value=0.0, confidence=0.5, direction="absent")
    saturation:    DimensionScore = DimensionScore(value=0.0, confidence=0.5, direction="absent")
    contrast:      DimensionScore = DimensionScore(value=0.0, confidence=0.5, direction="absent")
    color_harmony: DimensionScore = DimensionScore(value=0.0, confidence=0.5, direction="absent")
    tension:       DimensionScore = DimensionScore(value=0.0, confidence=0.5, direction="absent")
    closure:       DimensionScore = DimensionScore(value=0.0, confidence=0.5, direction="absent")
    rhythm:        DimensionScore = DimensionScore(value=0.0, confidence=0.5, direction="absent")

    def to_array(self) -> list[float]:
        return [getattr(self, d).value for d in AESTHETIC_DIMENSIONS]

    def dominant_dimensions(self) -> list[str]:
        return [d for d in AESTHETIC_DIMENSIONS if getattr(self, d).direction in ("dominant", "present")]

    @classmethod
    def from_dict(cls, scores: dict[str, float], confidence: float = 0.7) -> "AestheticVector":
        kwargs: dict[str, DimensionScore] = {}
        for d in AESTHETIC_DIMENSIONS:
            v = float(scores.get(d, 0.0))
            kwargs[d] = DimensionScore(value=v, confidence=confidence, direction=_direction(v))
        return cls(**kwargs)


class Document(BaseModel):
    title: str
    source: str
    sha256: str
    medium: str | None = None
    style_period: str | None = None
    artist: str | None = None
    input_mode: Literal["text", "image", "html", "multimedia"] = "text"
    width_px: int | None = None
    height_px: int | None = None
    duration_s: float | None = None


class AestheticElement(BaseModel):
    id: str
    name: str
    element_type: Literal[
        "shape", "color_block", "text", "figure", "line",
        "texture", "image_region", "dom_node", "frame_region", "unknown"
    ]
    position: dict[str, float] | None = None
    color: dict[str, float] | None = None
    size_ratio: float = 0.0
    aesthetic_vector: AestheticVector = AestheticVector()
    metadata: dict[str, Any] = {}


class CompositionZone(BaseModel):
    id: str
    zone_type: Literal[
        "foreground", "midground", "background",
        "golden_ratio", "rule_of_thirds", "center", "periphery",
        "header", "body", "footer", "sidebar"
    ]
    salience: float = 0.5
    element_ids: list[str] = []


class ColorScheme(BaseModel):
    id: str
    harmony_type: Literal[
        "monochromatic", "analogous", "complementary",
        "triadic", "split_complementary", "tetradic", "polychromatic", "achromatic"
    ]
    dominant_hue_deg: float | None = None
    saturation_avg: float = 0.0
    lightness_avg: float = 0.5
    element_ids: list[str] = []


class VisualMotif(BaseModel):
    id: str
    motif_type: Literal["repetition", "rhythm", "pattern", "texture", "grid"]
    frequency: int = 1
    element_ids: list[str] = []


class AestheticFactKind(str):
    IMBALANCE = "imbalance"
    COMPLEXITY_OVERLOAD = "complexity_overload"
    COLOR_CLASH = "color_clash"
    FIGURE_GROUND_AMBIGUITY = "figure_ground_ambiguity"
    DOMINANT_TENSION = "dominant_tension"
    CLOSURE_GAP = "closure_gap"
    RHYTHM_BREAK = "rhythm_break"
    COLOR_HARMONY = "color_harmony"
    BALANCE_ACHIEVED = "balance_achieved"
    BIRKHOFF_EXCESS_COMPLEXITY = "birkhoff_excess_complexity"
    BERLYNE_OVERAROUSAL = "berlyne_overarousal"


class AestheticFact(BaseModel):
    id: str
    fact_kind: str
    subject_ids: list[str] = []
    dimension: str | None = None
    severity: Literal["high", "moderate", "low"] = "low"
    confidence: float = 0.7
    explanation: str | None = None


class Segment(BaseModel):
    id: str
    text: str
    segment_type: Literal[
        "color_description", "composition_description",
        "style_reference", "subject_description",
        "technique_description", "temporal_description", "general"
    ]
    start_char: int
    end_char: int


class AestheticFinding(BaseModel):
    element_ids: list[str] = []
    finding_type: str
    score: float
    explanation: str


class ProjectionResult(BaseModel):
    projection_id: str
    verdict: str
    polarity: Literal["harmonious", "neutral", "discordant"]
    findings: list[AestheticFinding] = []
    score: float
    explanation: str | None = None


class AestheticVerdictLabel(str):
    HARMONIOUS = "harmonious"
    DYNAMIC = "dynamic"
    NEUTRAL = "neutral"
    DISCORDANT = "discordant"
    PROJECTION_CONFLICT = "projection_conflict"


class AestheticVerdict(BaseModel):
    verdict: str
    confidence: float
    explanation: str | None = None
    dominant_projection: str | None = None


class PassRecord(BaseModel):
    pass_number: float
    pass_name: str
    status: Literal["ok", "skip", "warn", "error"]
    note: str | None = None


class AuditRecord(BaseModel):
    passes: list[PassRecord] = []
    extractor_tier: str = "rule"
    input_mode: str = "text"
    active_projections: list[str] = []
    graph_hash: str | None = None
    input_sha256: str | None = None
    provenance: dict[str, Any] = {}


class AestheticIR(BaseModel):
    document: Document
    elements: list[AestheticElement] = []
    zones: list[CompositionZone] = []
    color_schemes: list[ColorScheme] = []
    motifs: list[VisualMotif] = []
    aesthetic_facts: list[AestheticFact] = []
    segments: list[Segment] = []
    aesthetic_graph: Any | None = None
    aggregate_aesthetic_vector: AestheticVector = AestheticVector()
    per_element_vectors: dict[str, AestheticVector] = {}
    projections: dict[str, ProjectionResult] = {}
    cross_projection_disagreement: dict[str, Any] | None = None
    aesthetic_verdict: AestheticVerdict = AestheticVerdict(
        verdict="neutral", confidence=0.5
    )
    audit: AuditRecord = AuditRecord()
    schema_version: str = SCHEMA_VERSION
