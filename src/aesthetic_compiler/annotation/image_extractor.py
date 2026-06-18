from __future__ import annotations
import math
from typing import Any
from aesthetic_compiler.annotation.base import BaseExtractor, ExtractorResult
from aesthetic_compiler.ir.schemas import (
    AestheticElement, CompositionZone, ColorScheme, AestheticFact,
    AestheticVector, DimensionScore, _direction,
)


class ImageExtractor(BaseExtractor):
    def extract(self, meta: dict[str, Any]) -> ExtractorResult:
        import numpy as np

        arr = meta["arr"]
        lum = meta["lum"]
        hsv_h = meta["hsv_h"]
        hsv_s = meta["hsv_s"]
        hsv_v = meta["hsv_v"]
        h, w = arr.shape[:2]

        scores: dict[str, float] = {}

        # k0: complexity — edge magnitude (gradient of luminance)
        grad_y = np.diff(lum, axis=0)
        grad_x = np.diff(lum, axis=1)
        edge_mag = np.sqrt(
            grad_y[:, :w-1] ** 2 + grad_x[:h-1, :] ** 2
        )
        edge_density = float(edge_mag.mean()) / 127.5
        scores["complexity"] = min(1.0, edge_density * 2.5)

        # k1: order — horizontal + vertical symmetry via flip-and-compare
        sym_h = 1.0 - float(np.abs(lum - np.flip(lum, axis=1)).mean()) / 255.0
        sym_v = 1.0 - float(np.abs(lum - np.flip(lum, axis=0)).mean()) / 255.0
        scores["order"] = float(max(sym_h, sym_v))

        # k2: balance — luminance-weighted center of mass deviation
        ys, xs = np.mgrid[0:h, 0:w]
        weights = (255.0 - lum)  # darker = heavier
        total_w = float(weights.sum()) + 1e-9
        cx = float((weights * xs).sum()) / total_w
        cy = float((weights * ys).sum()) / total_w
        dev_x = abs(cx - w / 2) / (w / 2)
        dev_y = abs(cy - h / 2) / (h / 2)
        imbalance = math.sqrt(dev_x ** 2 + dev_y ** 2) / math.sqrt(2)
        scores["balance"] = max(0.0, 1.0 - imbalance)

        # k3: density — fill ratio (non-near-white pixels)
        near_white = (arr.mean(axis=2) > 230).sum()
        scores["density"] = 1.0 - float(near_white) / (h * w)

        # k4: hue_coherence — entropy of hue histogram
        valid_mask = hsv_s > 0.15
        if valid_mask.sum() > 100:
            hue_vals = hsv_h[valid_mask]
            hist, _ = np.histogram(hue_vals, bins=18, range=(0, 1))
            p = hist.astype(float) / (hist.sum() + 1e-9)
            entropy = float(-np.sum(p * np.log(p + 1e-12)))
            max_entropy = math.log(18)
            scores["hue_coherence"] = max(0.0, 1.0 - entropy / max_entropy)
        else:
            scores["hue_coherence"] = 0.9

        # k5: saturation — mean saturation
        scores["saturation"] = float(hsv_s.mean())

        # k6: contrast — log-scale luminance range (Weber-Fechner)
        lum_max = float(lum.max())
        lum_min = float(lum.min())
        log_contrast = math.log(lum_max / (lum_min + 1.0)) / math.log(255.0)
        scores["contrast"] = min(1.0, log_contrast)

        # k7: color_harmony — classify dominant hue cluster
        scores["color_harmony"] = self._color_harmony_score(hsv_h, hsv_s)

        # k8: tension — diagonal edge dominance (45°/135° lines create tension)
        if h > 4 and w > 4:
            diag1 = np.diff(lum[::2, ::2], axis=1)
            diag2 = np.diff(lum[::2, ::2], axis=0)
            diag_energy = float(np.abs(diag1).mean() + np.abs(diag2).mean())
            horiz_energy = float(np.abs(np.diff(lum, axis=1)).mean())
            vert_energy = float(np.abs(np.diff(lum, axis=0)).mean())
            total_energy = horiz_energy + vert_energy + 1e-9
            scores["tension"] = min(1.0, diag_energy / total_energy)
        else:
            scores["tension"] = 0.0

        # k9: closure — ratio of enclosed regions to total area
        try:
            from skimage.measure import label as sk_label
            threshold = 128
            binary = (lum < threshold).astype(np.uint8)
            labeled = sk_label(binary)
            n_regions = int(labeled.max())
            scores["closure"] = min(1.0, n_regions / max(1, (h * w / 1000)))
        except ImportError:
            scores["closure"] = max(0.0, 1.0 - scores.get("contrast", 0.5))

        # k10: rhythm — 0 for static images
        scores["rhythm"] = 0.0

        elem = AestheticElement(
            id="elem:image",
            name="image composition",
            element_type="image_region",
            size_ratio=1.0,
            aesthetic_vector=AestheticVector.from_dict(scores),
            metadata={"width": w, "height": h},
        )

        zone = CompositionZone(
            id="zone:primary",
            zone_type="center",
            salience=1.0,
            element_ids=["elem:image"],
        )

        harmony_type = self._classify_harmony(hsv_h, hsv_s)
        cs = ColorScheme(
            id="scheme:computed",
            harmony_type=harmony_type,
            dominant_hue_deg=float(np.median(hsv_h[hsv_s > 0.15]) * 360) if (hsv_s > 0.15).sum() > 0 else None,
            saturation_avg=scores["saturation"],
            lightness_avg=float(hsv_v.mean()),
            element_ids=["elem:image"],
        )

        facts = self._extract_facts(scores)

        return ExtractorResult(
            elements=[elem],
            zones=[zone],
            color_schemes=[cs],
            aesthetic_facts=facts,
            extractor_metadata={"computed_scores": scores},
        )

    def _color_harmony_score(self, hsv_h: "np.ndarray", hsv_s: "np.ndarray") -> float:
        import numpy as np
        valid = hsv_h[hsv_s > 0.15]
        if len(valid) < 50:
            return 0.8
        hist, _ = np.histogram(valid, bins=36, range=(0, 1))
        peaks = [i for i in range(36) if hist[i] > hist.mean() * 1.5]
        if len(peaks) <= 1:
            return 0.9
        hue_degs = [p * 10 for p in peaks]
        if len(peaks) == 2:
            diff = abs(hue_degs[0] - hue_degs[1])
            diff = min(diff, 360 - diff)
            if 150 <= diff <= 210:
                return 0.85
            if diff <= 60:
                return 0.8
            return 0.6
        if len(peaks) == 3:
            diffs = sorted([abs(hue_degs[i] - hue_degs[j]) for i in range(3) for j in range(i+1, 3)])
            if all(100 <= d <= 140 for d in diffs):
                return 0.82
        return max(0.3, 0.9 - (len(peaks) - 1) * 0.1)

    def _classify_harmony(self, hsv_h: "np.ndarray", hsv_s: "np.ndarray") -> str:
        import numpy as np
        valid = hsv_h[hsv_s > 0.15]
        if len(valid) < 50:
            return "achromatic"
        hist, _ = np.histogram(valid, bins=36, range=(0, 1))
        peaks = [i for i in range(36) if hist[i] > hist.mean() * 1.5]
        if len(peaks) <= 1:
            return "monochromatic"
        if len(peaks) == 2:
            diff = abs(peaks[0] - peaks[1]) * 10
            diff = min(diff, 360 - diff)
            if 150 <= diff <= 210:
                return "complementary"
            if diff <= 60:
                return "analogous"
        if len(peaks) == 3:
            return "triadic"
        if len(peaks) >= 4:
            return "polychromatic"
        return "analogous"

    def _extract_facts(self, scores: dict[str, float]) -> list[AestheticFact]:
        facts: list[AestheticFact] = []
        if scores.get("complexity", 0) > 0.75 and scores.get("order", 0) < 0.3:
            facts.append(AestheticFact(
                id="fact:complexity_overload",
                fact_kind="complexity_overload",
                dimension="complexity", severity="high", confidence=0.8,
                explanation="High edge density with low symmetry",
            ))
        if scores.get("balance", 0) < 0.3:
            facts.append(AestheticFact(
                id="fact:imbalance",
                fact_kind="imbalance",
                dimension="balance", severity="moderate", confidence=0.75,
                explanation="Center of mass significantly off-center",
            ))
        if scores.get("contrast", 0) > 0.8:
            facts.append(AestheticFact(
                id="fact:high_contrast",
                fact_kind="dominant_tension",
                dimension="contrast", severity="low", confidence=0.7,
                explanation="Very high luminance contrast may create visual tension",
            ))
        return facts
