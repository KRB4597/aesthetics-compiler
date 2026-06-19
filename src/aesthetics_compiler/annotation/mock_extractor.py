from aesthetics_compiler.annotation.base import BaseExtractor, ExtractorResult
from aesthetics_compiler.ir.schemas import (
    AestheticElement, CompositionZone, ColorScheme, AestheticVector, DimensionScore
)


class MockExtractor(BaseExtractor):
    def extract(self, *args, **kwargs) -> ExtractorResult:
        def _ds(v: float) -> DimensionScore:
            from aesthetics_compiler.ir.schemas import _direction
            return DimensionScore(value=v, confidence=0.8, direction=_direction(v))

        red_block = AestheticElement(
            id="elem:red_block",
            name="red block",
            element_type="color_block",
            position={"x": 0.5, "y": 0.3, "w": 0.8, "h": 0.4},
            color={"r": 210, "g": 50, "b": 30},
            size_ratio=0.35,
            aesthetic_vector=AestheticVector(
                complexity=_ds(0.15), order=_ds(0.8), balance=_ds(0.7),
                density=_ds(0.4), hue_coherence=_ds(0.85), saturation=_ds(0.75),
                contrast=_ds(0.6), color_harmony=_ds(0.7), tension=_ds(0.2),
                closure=_ds(0.1), rhythm=_ds(0.0),
            ),
        )
        ochre_band = AestheticElement(
            id="elem:ochre_band",
            name="ochre band",
            element_type="color_block",
            position={"x": 0.5, "y": 0.75, "w": 0.8, "h": 0.2},
            color={"r": 195, "g": 150, "b": 60},
            size_ratio=0.18,
            aesthetic_vector=AestheticVector(
                complexity=_ds(0.1), order=_ds(0.85), balance=_ds(0.65),
                density=_ds(0.3), hue_coherence=_ds(0.7), saturation=_ds(0.55),
                contrast=_ds(0.4), color_harmony=_ds(0.75), tension=_ds(0.15),
                closure=_ds(0.05), rhythm=_ds(0.0),
            ),
        )
        zone = CompositionZone(
            id="zone:center",
            zone_type="center",
            salience=0.9,
            element_ids=["elem:red_block"],
        )
        cs = ColorScheme(
            id="scheme:warm_analogous",
            harmony_type="analogous",
            dominant_hue_deg=10.0,
            saturation_avg=0.65,
            lightness_avg=0.45,
            element_ids=["elem:red_block", "elem:ochre_band"],
        )
        return ExtractorResult(
            elements=[red_block, ochre_band],
            zones=[zone],
            color_schemes=[cs],
            medium_hint="oil_on_canvas",
            style_period_hint="abstract_expressionism",
            artist_hint="rothko_style",
        )
