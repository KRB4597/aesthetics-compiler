from __future__ import annotations
import json
from pathlib import Path
from aesthetic_compiler.ir.schemas import AestheticIR


def export_schema_org(ir: AestheticIR, path: str | Path | None = None) -> str:
    vec = ir.aggregate_aesthetic_vector
    dominant = vec.dominant_dimensions()

    obj = {
        "@context": "https://schema.org",
        "@type": "VisualArtwork",
        "name": ir.document.title,
        "description": ir.aesthetic_verdict.explanation or "",
        "encodingFormat": ir.document.medium or "unknown",
        "keywords": dominant,
        "artMedium": ir.document.medium or "unknown",
        "artworkSurface": ir.document.medium or "unknown",
        "creator": {"@type": "Person", "name": ir.document.artist or "Unknown"},
        "inLanguage": "en",
        "additionalProperty": [
            {
                "@type": "PropertyValue",
                "name": f"aesthetic:{dim}",
                "value": round(getattr(vec, dim).value, 3),
                "description": getattr(vec, dim).direction,
            }
            for dim in ["complexity", "order", "balance", "density",
                        "hue_coherence", "saturation", "contrast",
                        "color_harmony", "tension", "closure", "rhythm"]
        ],
        "aestheticVerdict": {
            "verdict": ir.aesthetic_verdict.verdict,
            "confidence": ir.aesthetic_verdict.confidence,
            "dominant_projection": ir.aesthetic_verdict.dominant_projection,
        },
        "projectionResults": {
            pid: {
                "verdict": pr.verdict,
                "polarity": pr.polarity,
                "score": pr.score,
            }
            for pid, pr in ir.projections.items()
        },
        "identifier": {
            "@type": "PropertyValue",
            "name": "graph_hash",
            "value": ir.audit.graph_hash or "",
        },
    }

    serialized = json.dumps(obj, indent=2)
    if path:
        Path(path).write_text(serialized, encoding="utf-8")
    return serialized
