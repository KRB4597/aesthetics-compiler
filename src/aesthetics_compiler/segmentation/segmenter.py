from __future__ import annotations
import re
from aesthetics_compiler.ir.schemas import Segment

_COLOR_WORDS = re.compile(
    r'\b(red|blue|yellow|green|orange|purple|black|white|grey|gray|'
    r'ochre|amber|crimson|cobalt|viridian|ultramarine|vermillion|sienna|'
    r'monochromatic|palette|hue|chroma|saturation|warm|cool|tonal)\b',
    re.IGNORECASE,
)
_COMPOSITION_WORDS = re.compile(
    r'\b(composition|layout|arrangement|balance|symmetry|asymmetry|'
    r'foreground|background|midground|center|rule of thirds|golden ratio|'
    r'diagonal|horizontal|vertical|depth|perspective|plane)\b',
    re.IGNORECASE,
)
_STYLE_WORDS = re.compile(
    r'\b(rothko|mondrian|pollock|kandinsky|picasso|monet|vermeer|'
    r'abstract|expressionism|impressionism|cubism|minimalism|baroque|'
    r'bauhaus|modernism|de stijl|art nouveau)\b',
    re.IGNORECASE,
)
_SUBJECT_WORDS = re.compile(
    r'\b(figure|portrait|landscape|still life|abstract|person|face|'
    r'body|nature|sky|water|earth|building|interior)\b',
    re.IGNORECASE,
)
_TECHNIQUE_WORDS = re.compile(
    r'\b(oil|acrylic|watercolor|charcoal|pencil|digital|brushstroke|'
    r'impasto|glaze|wash|stipple|hatching|blending|layering)\b',
    re.IGNORECASE,
)
_TEMPORAL_WORDS = re.compile(
    r'\b(animation|animated|video|film|motion|transition|cut|frame|'
    r'sequence|duration|timing|loop|fade|pan|zoom)\b',
    re.IGNORECASE,
)


def segment_text(text: str) -> list[Segment]:
    paragraphs = re.split(r'\n\s*\n', text.strip())
    segments: list[Segment] = []
    pos = 0
    for i, para in enumerate(paragraphs):
        if not para.strip():
            pos += len(para) + 2
            continue
        seg_type = _classify(para)
        segments.append(Segment(
            id=f"seg:{i}",
            text=para.strip(),
            segment_type=seg_type,
            start_char=pos,
            end_char=pos + len(para),
        ))
        pos += len(para) + 2
    return segments


def _classify(text: str) -> str:
    color_score = len(_COLOR_WORDS.findall(text))
    composition_score = len(_COMPOSITION_WORDS.findall(text))
    style_score = len(_STYLE_WORDS.findall(text))
    subject_score = len(_SUBJECT_WORDS.findall(text))
    technique_score = len(_TECHNIQUE_WORDS.findall(text))
    temporal_score = len(_TEMPORAL_WORDS.findall(text))

    scores = {
        "color_description": color_score,
        "composition_description": composition_score,
        "style_reference": style_score,
        "subject_description": subject_score,
        "technique_description": technique_score,
        "temporal_description": temporal_score,
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"
