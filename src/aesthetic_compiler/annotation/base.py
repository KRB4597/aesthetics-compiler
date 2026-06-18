from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from aesthetic_compiler.ir.schemas import (
    AestheticElement, CompositionZone, ColorScheme, VisualMotif, AestheticFact
)


@dataclass
class ExtractorResult:
    elements: list[AestheticElement] = field(default_factory=list)
    zones: list[CompositionZone] = field(default_factory=list)
    color_schemes: list[ColorScheme] = field(default_factory=list)
    motifs: list[VisualMotif] = field(default_factory=list)
    aesthetic_facts: list[AestheticFact] = field(default_factory=list)
    medium_hint: str | None = None
    style_period_hint: str | None = None
    artist_hint: str | None = None
    extractor_metadata: dict = field(default_factory=dict)


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, *args, **kwargs) -> ExtractorResult: ...
