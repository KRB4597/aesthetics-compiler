from __future__ import annotations
from typing import Any
from aesthetics_compiler.annotation.base import BaseExtractor, ExtractorResult
from aesthetics_compiler.annotation.image_extractor import ImageExtractor
from aesthetics_compiler.ingestion.image_loader import _rgb_to_hsv_channels
from aesthetics_compiler.ir.schemas import (
    AestheticElement, CompositionZone, ColorScheme, AestheticFact,
    AestheticVector, DimensionScore, _direction, VisualMotif,
)


class MultimediaExtractor(BaseExtractor):
    def __init__(self) -> None:
        self._img_extractor = ImageExtractor()

    def extract(self, frames: list[Any], meta: dict[str, Any]) -> ExtractorResult:
        import numpy as np

        if not frames:
            return ExtractorResult()

        # Run image extractor on each sampled frame
        frame_results: list[dict[str, float]] = []
        for frame in frames:
            arr = np.array(frame, dtype=np.float32)
            lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
            hsv_h, hsv_s, hsv_v = _rgb_to_hsv_channels(arr)
            frame_meta = {"arr": arr, "lum": lum, "hsv_h": hsv_h, "hsv_s": hsv_s, "hsv_v": hsv_v}
            result = self._img_extractor.extract(frame_meta)
            if result.elements:
                raw = result.extractor_metadata.get("computed_scores", {})
                frame_results.append(raw)

        if not frame_results:
            return ExtractorResult()

        # Average spatial dimensions across frames
        avg_scores: dict[str, float] = {}
        for dim in ["complexity", "order", "balance", "density", "hue_coherence",
                    "saturation", "contrast", "color_harmony", "tension", "closure"]:
            vals = [f.get(dim, 0.0) for f in frame_results]
            avg_scores[dim] = sum(vals) / len(vals)

        # k10: rhythm — temporal pacing from frame differences
        avg_scores["rhythm"] = self._compute_rhythm(frames, meta)

        # Detect temporal facts
        facts = self._extract_temporal_facts(avg_scores, frame_results, meta)

        elem = AestheticElement(
            id="elem:video_composite",
            name="video composite",
            element_type="frame_region",
            size_ratio=1.0,
            aesthetic_vector=AestheticVector.from_dict(avg_scores),
            metadata={
                "n_frames": meta.get("n_frames_sampled", len(frames)),
                "duration_s": meta.get("duration_s", 0),
                "fps": meta.get("fps", 0),
            },
        )

        zone = CompositionZone(
            id="zone:temporal",
            zone_type="center",
            salience=1.0,
            element_ids=["elem:video_composite"],
        )

        motif = None
        if avg_scores.get("rhythm", 0) > 0.5:
            motif = VisualMotif(
                id="motif:temporal_rhythm",
                motif_type="rhythm",
                frequency=int(meta.get("n_frames_sampled", 1)),
                element_ids=["elem:video_composite"],
            )

        return ExtractorResult(
            elements=[elem],
            zones=[zone],
            color_schemes=[],
            motifs=[motif] if motif else [],
            aesthetic_facts=facts,
            medium_hint="video",
            extractor_metadata={"avg_scores": avg_scores, "n_frames": len(frames)},
        )

    def _compute_rhythm(self, frames: list[Any], meta: dict[str, Any]) -> float:
        import numpy as np
        if len(frames) < 2:
            return 0.0

        diffs: list[float] = []
        for i in range(1, len(frames)):
            a = np.array(frames[i - 1], dtype=np.float32)
            b = np.array(frames[i], dtype=np.float32)
            diff = float(np.abs(a - b).mean()) / 255.0
            diffs.append(diff)

        mean_diff = sum(diffs) / len(diffs)
        fps = meta.get("fps", 1.0)

        pacing_score = min(1.0, mean_diff * 2.5)
        fps_score = min(1.0, fps / 60.0)
        return (pacing_score * 0.7 + fps_score * 0.3)

    def _extract_temporal_facts(
        self,
        avg_scores: dict[str, float],
        frame_results: list[dict[str, float]],
        meta: dict[str, Any],
    ) -> list[AestheticFact]:
        facts: list[AestheticFact] = []

        if avg_scores.get("rhythm", 0) > 0.75:
            facts.append(AestheticFact(
                id="fact:high_pacing",
                fact_kind="rhythm_break",
                dimension="rhythm", severity="moderate", confidence=0.7,
                explanation="High inter-frame change rate; rapid visual pacing",
            ))

        if frame_results:
            complexity_vals = [f.get("complexity", 0) for f in frame_results]
            std = (sum((v - avg_scores["complexity"])**2 for v in complexity_vals) / len(complexity_vals)) ** 0.5
            if std > 0.3:
                facts.append(AestheticFact(
                    id="fact:temporal_complexity_variance",
                    fact_kind="rhythm_break",
                    dimension="complexity", severity="low", confidence=0.65,
                    explanation="Complexity varies significantly across frames",
                ))

        return facts
