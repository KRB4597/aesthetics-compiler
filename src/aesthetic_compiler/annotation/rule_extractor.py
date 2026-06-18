from __future__ import annotations
import re
from aesthetic_compiler.annotation.base import BaseExtractor, ExtractorResult
from aesthetic_compiler.ir.schemas import (
    AestheticElement, CompositionZone, ColorScheme, VisualMotif,
    AestheticFact, AestheticVector, DimensionScore, _direction,
)

# ---------------------------------------------------------------------------
# Vocabulary tables
# ---------------------------------------------------------------------------

COMPLEXITY_KEYWORDS: dict[str, float] = {
    "complex": 0.8, "intricate": 0.85, "busy": 0.75, "detailed": 0.7,
    "elaborate": 0.75, "crowded": 0.8, "layered": 0.65, "dense": 0.7,
    "simple": 0.15, "minimal": 0.1, "clean": 0.12, "sparse": 0.08,
    "empty": 0.05, "pure": 0.1, "bare": 0.08, "uncluttered": 0.1,
}

ORDER_KEYWORDS: dict[str, float] = {
    "symmetrical": 0.9, "symmetric": 0.9, "ordered": 0.8, "regular": 0.75,
    "structured": 0.75, "geometric": 0.8, "grid": 0.85, "aligned": 0.8,
    "repeating": 0.7, "patterned": 0.75, "systematic": 0.8,
    "asymmetric": 0.2, "irregular": 0.2, "chaotic": 0.1, "random": 0.15,
    "spontaneous": 0.15, "gestural": 0.2, "dripped": 0.1, "splattered": 0.1,
}

BALANCE_KEYWORDS: dict[str, float] = {
    "balanced": 0.85, "centered": 0.8, "stable": 0.8, "equilibrium": 0.9,
    "grounded": 0.75, "symmetrical": 0.85,
    "unbalanced": 0.2, "off-center": 0.3, "tipped": 0.25, "dynamic": 0.4,
    "asymmetric": 0.35, "precarious": 0.2,
}

DENSITY_KEYWORDS: dict[str, float] = {
    "dense": 0.8, "full": 0.75, "saturated": 0.7, "packed": 0.85,
    "sparse": 0.2, "airy": 0.15, "open": 0.2, "breathing": 0.15,
    "negative space": 0.1, "whitespace": 0.1,
}

HUE_COHERENCE_KEYWORDS: dict[str, float] = {
    "monochromatic": 0.95, "single color": 0.9, "one hue": 0.9,
    "colorful": 0.2, "polychromatic": 0.15, "rainbow": 0.05,
    "many colors": 0.1, "varied palette": 0.2, "rich palette": 0.3,
    "limited palette": 0.75, "restricted palette": 0.8,
}

SATURATION_KEYWORDS: dict[str, float] = {
    "vibrant": 0.9, "vivid": 0.85, "bright": 0.8, "saturated": 0.85,
    "bold": 0.75, "intense": 0.8, "rich": 0.7, "brilliant": 0.85,
    "muted": 0.2, "subdued": 0.2, "desaturated": 0.1, "pale": 0.15,
    "washed": 0.15, "faded": 0.2, "pastel": 0.3, "soft": 0.3, "subtle": 0.25,
}

CONTRAST_KEYWORDS: dict[str, float] = {
    "high contrast": 0.9, "stark": 0.85, "bold contrast": 0.8,
    "dramatic": 0.75, "sharp": 0.7, "crisp": 0.65,
    "low contrast": 0.2, "tonal": 0.3, "subtle": 0.25, "gentle": 0.2,
    "soft": 0.25, "atmospheric": 0.3, "hazy": 0.2,
}

COLOR_HARMONY_KEYWORDS: dict[str, float] = {
    "harmonious": 0.9, "harmonized": 0.85, "coherent palette": 0.85,
    "complementary": 0.8, "coordinated": 0.8, "unified color": 0.85,
    "discordant": 0.1, "clashing": 0.05, "jarring": 0.1, "conflicting": 0.15,
}

TENSION_KEYWORDS: dict[str, float] = {
    "tense": 0.8, "dynamic": 0.75, "energetic": 0.7, "active": 0.65,
    "restless": 0.75, "charged": 0.7, "explosive": 0.85, "strident": 0.8,
    "calm": 0.1, "serene": 0.05, "peaceful": 0.08, "static": 0.1,
    "meditative": 0.05, "contemplative": 0.08, "still": 0.05,
}

CLOSURE_KEYWORDS: dict[str, float] = {
    "ambiguous": 0.8, "open-ended": 0.7, "unresolved": 0.75, "fragmented": 0.7,
    "incomplete": 0.65, "gestalt": 0.6, "implied": 0.55,
    "resolved": 0.1, "complete": 0.08, "finished": 0.1, "defined": 0.12,
    "clear": 0.1, "crisp edges": 0.08,
}

RHYTHM_KEYWORDS: dict[str, float] = {
    "animated": 0.8, "motion": 0.75, "kinetic": 0.85, "movement": 0.7,
    "transitions": 0.65, "cuts": 0.7, "dynamic video": 0.8, "fast-paced": 0.85,
    "slow": 0.2, "still": 0.05, "static": 0.08,
}

ARTIST_STYLE_MAP: dict[str, dict[str, float]] = {
    "rothko": {"complexity": 0.1, "order": 0.7, "balance": 0.8, "density": 0.4,
               "hue_coherence": 0.8, "saturation": 0.65, "contrast": 0.5,
               "color_harmony": 0.85, "tension": 0.15, "closure": 0.1},
    "mondrian": {"complexity": 0.4, "order": 0.95, "balance": 0.85, "density": 0.3,
                 "hue_coherence": 0.6, "saturation": 0.8, "contrast": 0.85,
                 "color_harmony": 0.8, "tension": 0.25, "closure": 0.05},
    "pollock": {"complexity": 0.95, "order": 0.1, "balance": 0.5, "density": 0.85,
                "hue_coherence": 0.2, "saturation": 0.6, "contrast": 0.55,
                "color_harmony": 0.4, "tension": 0.9, "closure": 0.7},
    "kandinsky": {"complexity": 0.8, "order": 0.5, "balance": 0.55, "density": 0.7,
                  "hue_coherence": 0.3, "saturation": 0.85, "contrast": 0.75,
                  "color_harmony": 0.65, "tension": 0.8, "closure": 0.55},
    "monet": {"complexity": 0.6, "order": 0.4, "balance": 0.65, "density": 0.55,
              "hue_coherence": 0.45, "saturation": 0.5, "contrast": 0.35,
              "color_harmony": 0.8, "tension": 0.2, "closure": 0.6},
    "picasso": {"complexity": 0.8, "order": 0.4, "balance": 0.4, "density": 0.65,
                "hue_coherence": 0.3, "saturation": 0.6, "contrast": 0.7,
                "color_harmony": 0.5, "tension": 0.7, "closure": 0.65},
    "vermeer": {"complexity": 0.55, "order": 0.75, "balance": 0.8, "density": 0.5,
                "hue_coherence": 0.55, "saturation": 0.55, "contrast": 0.6,
                "color_harmony": 0.85, "tension": 0.2, "closure": 0.15},
}

COLOR_SCHEME_VOCABULARY: dict[str, str] = {
    "monochromatic": "monochromatic", "analogous": "analogous",
    "complementary": "complementary", "triadic": "triadic",
    "split complementary": "split_complementary", "tetradic": "tetradic",
    "achromatic": "achromatic", "black and white": "achromatic",
    "grayscale": "achromatic", "grey scale": "achromatic",
    "warm": "analogous", "cool": "analogous", "earth tones": "analogous",
}

STYLE_PERIOD_KEYWORDS: dict[str, str] = {
    "abstract expressionism": "abstract_expressionism",
    "abstract expressionist": "abstract_expressionism",
    "de stijl": "de_stijl", "neoplasticism": "de_stijl",
    "impressionism": "impressionism", "impressionist": "impressionism",
    "cubism": "cubism", "cubist": "cubism",
    "minimalism": "minimalism", "minimalist": "minimalism",
    "baroque": "baroque", "renaissance": "renaissance",
    "modernism": "modernism", "postmodern": "postmodernism",
    "art nouveau": "art_nouveau", "art deco": "art_deco",
    "bauhaus": "bauhaus",
}

ZONE_KEYWORDS: dict[str, str] = {
    "foreground": "foreground", "background": "background",
    "midground": "midground", "center": "center",
    "left": "periphery", "right": "periphery",
    "golden ratio": "golden_ratio", "rule of thirds": "rule_of_thirds",
    "header": "header", "footer": "footer", "sidebar": "sidebar",
}

MOTIF_KEYWORDS: dict[str, str] = {
    "repeated": "repetition", "repeating": "repetition", "repetition": "repetition",
    "rhythm": "rhythm", "rhythmic": "rhythm",
    "pattern": "pattern", "patterned": "pattern",
    "texture": "texture", "textured": "texture",
    "grid": "grid", "gridded": "grid",
}


class RuleExtractor(BaseExtractor):
    def extract(self, text: str) -> ExtractorResult:
        lower = text.lower()

        scores = self._score_dimensions(lower)
        artist, style_period = self._detect_style(lower)
        if artist and artist in ARTIST_STYLE_MAP:
            artist_scores = ARTIST_STYLE_MAP[artist]
            for k, v in artist_scores.items():
                if k not in scores or scores[k] == 0.0:
                    scores[k] = v

        elements = self._extract_elements(lower, scores)
        zones = self._extract_zones(lower, elements)
        color_schemes = self._extract_color_schemes(lower, elements)
        motifs = self._extract_motifs(lower, elements)
        facts = self._extract_facts(scores, elements)

        return ExtractorResult(
            elements=elements,
            zones=zones,
            color_schemes=color_schemes,
            motifs=motifs,
            aesthetic_facts=facts,
            medium_hint=self._detect_medium(lower),
            style_period_hint=style_period,
            artist_hint=artist,
        )

    def _score_dimensions(self, lower: str) -> dict[str, float]:
        vocab_maps = {
            "complexity": COMPLEXITY_KEYWORDS,
            "order": ORDER_KEYWORDS,
            "balance": BALANCE_KEYWORDS,
            "density": DENSITY_KEYWORDS,
            "hue_coherence": HUE_COHERENCE_KEYWORDS,
            "saturation": SATURATION_KEYWORDS,
            "contrast": CONTRAST_KEYWORDS,
            "color_harmony": COLOR_HARMONY_KEYWORDS,
            "tension": TENSION_KEYWORDS,
            "closure": CLOSURE_KEYWORDS,
            "rhythm": RHYTHM_KEYWORDS,
        }
        scores: dict[str, float] = {}
        for dim, vocab in vocab_maps.items():
            hits = [(score, kw) for kw, score in vocab.items() if kw in lower]
            if hits:
                scores[dim] = sum(s for s, _ in hits) / len(hits)
        return scores

    def _extract_elements(self, lower: str, scores: dict[str, float]) -> list[AestheticElement]:
        elements: list[AestheticElement] = []

        color_patterns = [
            (r'\b(red|crimson|scarlet|vermillion)\b', "red", {"r": 210, "g": 40, "b": 30}, 0.25),
            (r'\b(blue|cobalt|ultramarine|cerulean|azure)\b', "blue", {"r": 30, "g": 80, "b": 190}, 0.25),
            (r'\b(yellow|ochre|cadmium|lemon|amber)\b', "yellow", {"r": 230, "g": 200, "b": 40}, 0.2),
            (r'\b(green|viridian|emerald|sage)\b', "green", {"r": 60, "g": 160, "b": 80}, 0.2),
            (r'\b(orange|burnt\s+sienna)\b', "orange", {"r": 220, "g": 110, "b": 30}, 0.2),
            (r'\b(purple|violet|mauve|magenta)\b', "purple", {"r": 140, "g": 60, "b": 180}, 0.15),
            (r'\b(black|ebony|jet)\b', "black", {"r": 20, "g": 20, "b": 20}, 0.15),
            (r'\b(white|ivory|cream)\b', "white", {"r": 245, "g": 245, "b": 240}, 0.15),
            (r'\b(grey|gray|silver|charcoal)\b', "grey", {"r": 130, "g": 130, "b": 130}, 0.1),
        ]

        for i, (pattern, name, color, size) in enumerate(color_patterns):
            if re.search(pattern, lower):
                vec_scores = dict(scores)
                vec_scores.setdefault("hue_coherence", 0.5)
                vec_scores.setdefault("saturation", 0.5)
                elements.append(AestheticElement(
                    id=f"elem:{name}_region_{i}",
                    name=f"{name} region",
                    element_type="color_block",
                    color=color,
                    size_ratio=size,
                    aesthetic_vector=AestheticVector.from_dict(vec_scores),
                ))

        shape_patterns = [
            (r'\b(rectangle|square|block|band|stripe|field)\b', "geometric_form", "shape"),
            (r'\b(circle|oval|sphere|disc)\b', "circular_form", "shape"),
            (r'\b(line|lines|stroke|strokes)\b', "linear_element", "line"),
            (r'\b(figure|portrait|person|face|body)\b', "figure", "figure"),
            (r'\b(text|typography|lettering|font)\b', "text_element", "text"),
        ]
        for i, (pattern, name, etype) in enumerate(shape_patterns):
            if re.search(pattern, lower):
                elements.append(AestheticElement(
                    id=f"elem:{name}_{i}",
                    name=name.replace("_", " "),
                    element_type=etype,
                    size_ratio=0.15,
                    aesthetic_vector=AestheticVector.from_dict(scores),
                ))

        if not elements:
            elements.append(AestheticElement(
                id="elem:composition",
                name="overall composition",
                element_type="image_region",
                size_ratio=1.0,
                aesthetic_vector=AestheticVector.from_dict(scores),
            ))

        return elements

    def _extract_zones(self, lower: str, elements: list[AestheticElement]) -> list[CompositionZone]:
        zones: list[CompositionZone] = []
        elem_ids = [e.id for e in elements]
        for kw, zone_type in ZONE_KEYWORDS.items():
            if kw in lower:
                zones.append(CompositionZone(
                    id=f"zone:{zone_type}",
                    zone_type=zone_type,
                    salience=0.7,
                    element_ids=elem_ids[:2],
                ))
        if not zones:
            zones.append(CompositionZone(
                id="zone:center",
                zone_type="center",
                salience=0.8,
                element_ids=elem_ids,
            ))
        return zones

    def _extract_color_schemes(self, lower: str, elements: list[AestheticElement]) -> list[ColorScheme]:
        elem_ids = [e.id for e in elements]
        harmony = "polychromatic"
        for kw, ht in COLOR_SCHEME_VOCABULARY.items():
            if kw in lower:
                harmony = ht
                break
        return [ColorScheme(
            id="scheme:primary",
            harmony_type=harmony,
            saturation_avg=0.55,
            lightness_avg=0.5,
            element_ids=elem_ids,
        )]

    def _extract_motifs(self, lower: str, elements: list[AestheticElement]) -> list[VisualMotif]:
        motifs: list[VisualMotif] = []
        elem_ids = [e.id for e in elements]
        for kw, mtype in MOTIF_KEYWORDS.items():
            if kw in lower:
                freq_match = re.search(r'(\d+)\s+(?:times?|repetitions?)', lower)
                freq = int(freq_match.group(1)) if freq_match else 2
                motifs.append(VisualMotif(
                    id=f"motif:{mtype}",
                    motif_type=mtype,
                    frequency=freq,
                    element_ids=elem_ids[:3],
                ))
                break
        return motifs

    def _extract_facts(self, scores: dict[str, float], elements: list[AestheticElement]) -> list[AestheticFact]:
        facts: list[AestheticFact] = []
        ids = [e.id for e in elements]

        if scores.get("complexity", 0) > 0.7 and scores.get("order", 0) < 0.3:
            facts.append(AestheticFact(
                id="fact:complexity_overload",
                fact_kind="complexity_overload",
                subject_ids=ids,
                dimension="complexity",
                severity="high",
                confidence=0.75,
                explanation="High complexity without compensating order risks visual overwhelm",
            ))
        if scores.get("balance", 0) < 0.25:
            facts.append(AestheticFact(
                id="fact:imbalance",
                fact_kind="imbalance",
                subject_ids=ids,
                dimension="balance",
                severity="moderate",
                confidence=0.7,
                explanation="Composition appears spatially imbalanced",
            ))
        if scores.get("tension", 0) > 0.7:
            facts.append(AestheticFact(
                id="fact:dominant_tension",
                fact_kind="dominant_tension",
                subject_ids=ids,
                dimension="tension",
                severity="moderate",
                confidence=0.75,
                explanation="High directional tension without resolution",
            ))
        if scores.get("color_harmony", 0) > 0.75 and scores.get("order", 0) > 0.7:
            facts.append(AestheticFact(
                id="fact:balance_achieved",
                fact_kind="balance_achieved",
                subject_ids=ids,
                dimension="color_harmony",
                severity="low",
                confidence=0.8,
                explanation="Strong color harmony with ordered composition",
            ))
        return facts

    def _detect_style(self, lower: str) -> tuple[str | None, str | None]:
        artist = None
        for name in ARTIST_STYLE_MAP:
            if name in lower:
                artist = name
                break
        period = None
        for kw, per in STYLE_PERIOD_KEYWORDS.items():
            if kw in lower:
                period = per
                break
        return artist, period

    def _detect_medium(self, lower: str) -> str | None:
        mediums = {
            "oil": "oil_on_canvas", "acrylic": "acrylic", "watercolor": "watercolor",
            "watercolour": "watercolor", "gouache": "gouache", "pastel": "pastel",
            "charcoal": "charcoal", "pencil": "pencil", "ink": "ink",
            "digital": "digital", "photograph": "photograph", "photo": "photograph",
            "sculpture": "sculpture", "ceramic": "ceramic",
            "fresco": "fresco", "tempera": "tempera",
        }
        for kw, med in mediums.items():
            if kw in lower:
                return med
        return None
