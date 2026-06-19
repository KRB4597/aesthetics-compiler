from __future__ import annotations
import re
from typing import Any
from aesthetics_compiler.annotation.base import BaseExtractor, ExtractorResult
from aesthetics_compiler.ir.schemas import (
    AestheticElement, CompositionZone, ColorScheme, AestheticFact,
    AestheticVector, _direction, DimensionScore,
)

_HEX_RE = re.compile(r'#([0-9a-fA-F]{3,8})')
_RGB_RE = re.compile(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)')


def _hex_to_rgb(h: str) -> tuple[int, int, int] | None:
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    if len(h) != 6:
        return None
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return None


def _rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    cmax = max(r_, g_, b_)
    cmin = min(r_, g_, b_)
    delta = cmax - cmin
    l = (cmax + cmin) / 2.0
    s = delta / (1 - abs(2 * l - 1) + 1e-9) if delta > 0 else 0.0
    if delta == 0:
        h = 0.0
    elif cmax == r_:
        h = 60 * (((g_ - b_) / delta) % 6)
    elif cmax == g_:
        h = 60 * ((b_ - r_) / delta + 2)
    else:
        h = 60 * ((r_ - g_) / delta + 4)
    return h % 360, min(1.0, s), l


class HtmlExtractor(BaseExtractor):
    def extract(self, meta: dict[str, Any]) -> ExtractorResult:
        elements_data = meta.get("elements", [])
        css_colors = meta.get("css_colors", [])
        bg_colors = meta.get("background_colors", [])
        font_families = meta.get("font_families", [])
        element_count = meta.get("element_count", 0)
        max_depth = meta.get("max_depth", 0)

        all_colors_raw = css_colors + bg_colors
        rgb_colors: list[tuple[int, int, int]] = []
        for c in all_colors_raw:
            if c.startswith('#'):
                parsed = _hex_to_rgb(c)
                if parsed:
                    rgb_colors.append(parsed)
            else:
                m = _RGB_RE.match(c)
                if m:
                    rgb_colors.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))

        hsl_colors = [_rgb_to_hsl(*rgb) for rgb in rgb_colors] if rgb_colors else []

        scores = self._compute_scores(elements_data, hsl_colors, element_count, max_depth, font_families)

        elements: list[AestheticElement] = []

        STRUCTURAL_TAGS = {"header", "nav", "main", "section", "article", "aside", "footer"}
        seen_tags: set[str] = set()
        for i, ed in enumerate(elements_data[:30]):
            tag = ed.get("tag", "div")
            if tag in STRUCTURAL_TAGS and tag not in seen_tags:
                seen_tags.add(tag)
                zone_type = "header" if tag == "header" else "footer" if tag == "footer" else "body"
                elem = AestheticElement(
                    id=f"elem:dom_{tag}_{i}",
                    name=f"<{tag}> element",
                    element_type="dom_node",
                    metadata={"tag": tag, "depth": ed.get("depth", 0)},
                    aesthetic_vector=AestheticVector.from_dict(scores),
                )
                elements.append(elem)

        if not elements:
            elements.append(AestheticElement(
                id="elem:html_document",
                name="HTML document",
                element_type="dom_node",
                size_ratio=1.0,
                aesthetic_vector=AestheticVector.from_dict(scores),
                metadata={"element_count": element_count, "max_depth": max_depth},
            ))

        elem_ids = [e.id for e in elements]

        zone_types = ["header", "body", "footer"] if any(
            e.metadata.get("tag") in {"header", "main", "footer"} for e in elements
        ) else ["center"]
        zones = [CompositionZone(
            id=f"zone:{zt}", zone_type=zt, salience=0.8, element_ids=elem_ids,
        ) for zt in zone_types[:1]]

        harmony_type = self._classify_color_harmony(hsl_colors)
        dominant_hue = hsl_colors[0][0] if hsl_colors else None
        cs = ColorScheme(
            id="scheme:css_colors",
            harmony_type=harmony_type,
            dominant_hue_deg=dominant_hue,
            saturation_avg=sum(c[1] for c in hsl_colors) / max(1, len(hsl_colors)),
            lightness_avg=sum(c[2] for c in hsl_colors) / max(1, len(hsl_colors)),
            element_ids=elem_ids,
        )

        facts = self._extract_facts(scores, elem_ids)

        return ExtractorResult(
            elements=elements,
            zones=zones,
            color_schemes=[cs],
            aesthetic_facts=facts,
            medium_hint="digital_web",
            extractor_metadata={
                "element_count": element_count,
                "color_count": len(rgb_colors),
                "font_families": font_families,
            },
        )

    def _compute_scores(
        self,
        elements_data: list[dict],
        hsl_colors: list[tuple[float, float, float]],
        element_count: int,
        max_depth: int,
        font_families: list[str],
    ) -> dict[str, float]:
        import math
        scores: dict[str, float] = {}

        # complexity: DOM element count (log-compressed)
        scores["complexity"] = min(1.0, math.log(1 + element_count) / math.log(1 + 200))

        # order: depth and nesting regularity
        if elements_data:
            depths = [e.get("depth", 0) for e in elements_data]
            depth_std = (sum((d - max_depth/2)**2 for d in depths) / len(depths)) ** 0.5
            scores["order"] = max(0.0, 1.0 - depth_std / max(max_depth, 1))
        else:
            scores["order"] = 0.5

        # balance: rough left-right balance (can't compute without rendering; proxy via element count)
        scores["balance"] = 0.6  # reasonable default for structured HTML

        # density: element count relative to page
        scores["density"] = min(1.0, element_count / 100.0)

        if hsl_colors:
            hues = [c[0] for c in hsl_colors]
            sats = [c[1] for c in hsl_colors]
            ligs = [c[2] for c in hsl_colors]

            # hue_coherence: hue spread
            hue_range = max(hues) - min(hues) if len(hues) > 1 else 0
            scores["hue_coherence"] = max(0.0, 1.0 - hue_range / 360.0)

            # saturation: mean saturation
            scores["saturation"] = sum(sats) / len(sats)

            # contrast: luminance range
            scores["contrast"] = max(ligs) - min(ligs) if len(ligs) > 1 else 0.0

            # color_harmony
            scores["color_harmony"] = self._harmony_score(hues)
        else:
            scores.update({"hue_coherence": 0.5, "saturation": 0.3, "contrast": 0.5, "color_harmony": 0.5})

        scores["tension"] = 0.2
        scores["closure"] = 0.1
        scores["rhythm"] = 0.0

        return scores

    def _harmony_score(self, hues: list[float]) -> float:
        if len(hues) <= 1:
            return 0.9
        n = len(hues)
        diffs = []
        for i in range(n):
            for j in range(i + 1, n):
                d = abs(hues[i] - hues[j])
                diffs.append(min(d, 360 - d))
        avg_diff = sum(diffs) / len(diffs)
        # complementary: ~180°, analogous: <60°, random: penalize
        if avg_diff > 150:
            return 0.85
        if avg_diff < 60:
            return 0.80
        return max(0.3, 0.85 - (avg_diff - 60) / 300)

    def _classify_color_harmony(self, hsl_colors: list[tuple[float, float, float]]) -> str:
        if not hsl_colors:
            return "achromatic"
        hues = [c[0] for c in hsl_colors if c[1] > 0.1]
        if not hues:
            return "achromatic"
        if len(hues) == 1:
            return "monochromatic"
        hue_range = max(hues) - min(hues)
        if hue_range < 30:
            return "monochromatic"
        if hue_range < 60:
            return "analogous"
        diffs = [min(abs(hues[i] - hues[j]), 360 - abs(hues[i] - hues[j]))
                 for i in range(len(hues)) for j in range(i + 1, len(hues))]
        avg = sum(diffs) / len(diffs)
        if 150 <= avg <= 210:
            return "complementary"
        if len(hues) >= 3 and 100 <= avg <= 140:
            return "triadic"
        return "polychromatic"

    def _extract_facts(self, scores: dict[str, float], elem_ids: list[str]) -> list[AestheticFact]:
        facts: list[AestheticFact] = []
        if scores.get("complexity", 0) > 0.8:
            facts.append(AestheticFact(
                id="fact:dom_complexity",
                fact_kind="complexity_overload",
                subject_ids=elem_ids,
                dimension="complexity", severity="moderate", confidence=0.7,
                explanation="High DOM element count may reduce visual clarity",
            ))
        if scores.get("color_harmony", 0) < 0.4:
            facts.append(AestheticFact(
                id="fact:color_clash",
                fact_kind="color_clash",
                subject_ids=elem_ids,
                dimension="color_harmony", severity="moderate", confidence=0.65,
                explanation="CSS color palette shows poor color-wheel harmony",
            ))
        return facts
