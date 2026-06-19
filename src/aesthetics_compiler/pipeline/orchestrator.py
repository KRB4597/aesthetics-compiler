from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any

from aesthetics_compiler.ir.schemas import (
    AestheticIR, Document, AestheticVerdict, PassRecord, AESTHETIC_DIMENSIONS,
)
from aesthetics_compiler.ir.graph.promote import graph_from_ir
from aesthetics_compiler.ir.graph.canonical import canonical_hash
from aesthetics_compiler.am_dag.dag import AMDAG
from aesthetics_compiler.audit.hash_chain import build_audit
from aesthetics_compiler.tiers import CompilerTier, InputMode, ALL_PROJECTIONS, detect_input_mode
from aesthetics_compiler.projections.birkhoff import BirkhoffProjection
from aesthetics_compiler.projections.arnheim import ArnheimProjection
from aesthetics_compiler.projections.berlyne import BerlyneProjection
from aesthetics_compiler.projections.gestalt import GestaltProjection

_PROJECTION_REGISTRY = {
    "birkhoff": BirkhoffProjection(),
    "arnheim":  ArnheimProjection(),
    "berlyne":  BerlyneProjection(),
    "gestalt":  GestaltProjection(),
}


def compile_document(
    source: str | Path,
    *,
    input_mode: InputMode | str | None = None,
    projections: list[str] | None = None,
    title: str | None = None,
    quiet: bool = False,
    extractor: str = "rule",
) -> AestheticIR:
    source = str(source)
    passes: list[PassRecord] = []

    if projections is None:
        projections = list(ALL_PROJECTIONS)
    else:
        bad = [p for p in projections if p not in ALL_PROJECTIONS]
        if bad:
            raise ValueError(f"Unknown projection(s): {bad}. Valid: {ALL_PROJECTIONS}")

    if input_mode is None:
        detected = detect_input_mode(source)
    else:
        detected = InputMode(str(input_mode))

    # ------------------------------------------------------------------
    # Pass 0: Ingestion
    # ------------------------------------------------------------------
    sha256_input: str
    raw_meta: dict[str, Any] = {}
    frames: list[Any] = []

    if detected == InputMode.TEXT:
        from aesthetics_compiler.ingestion.text_loader import load_text
        text, sha256_input = load_text(source)
        passes.append(PassRecord(pass_number=0, pass_name="ingestion_text", status="ok"))

    elif detected == InputMode.IMAGE:
        from aesthetics_compiler.ingestion.image_loader import load_image
        _, raw_meta, sha256_input = load_image(source)
        passes.append(PassRecord(pass_number=0, pass_name="ingestion_image", status="ok"))

    elif detected == InputMode.HTML:
        from aesthetics_compiler.ingestion.html_loader import load_html
        _, raw_meta, sha256_input = load_html(source)
        passes.append(PassRecord(pass_number=0, pass_name="ingestion_html", status="ok"))

    elif detected == InputMode.MULTIMEDIA:
        from aesthetics_compiler.ingestion.multimedia_loader import load_multimedia
        frames, raw_meta, sha256_input = load_multimedia(source)
        passes.append(PassRecord(pass_number=0, pass_name="ingestion_multimedia", status="ok"))
    else:
        from aesthetics_compiler.ingestion.text_loader import load_text
        text, sha256_input = load_text(source)
        passes.append(PassRecord(pass_number=0, pass_name="ingestion_text", status="ok"))

    # ------------------------------------------------------------------
    # Pass 1: Segmentation (text only)
    # ------------------------------------------------------------------
    segments = []
    if detected == InputMode.TEXT:
        from aesthetics_compiler.segmentation.segmenter import segment_text
        segments = segment_text(text)  # type: ignore[name-defined]
        passes.append(PassRecord(pass_number=1, pass_name="segmentation", status="ok",
                                 note=f"{len(segments)} segments"))
    else:
        passes.append(PassRecord(pass_number=1, pass_name="segmentation", status="skip",
                                 note=f"not applicable for {detected.value} input"))

    # ------------------------------------------------------------------
    # Pass 2–6: Extraction
    # ------------------------------------------------------------------
    extractor_tier: str
    if detected == InputMode.TEXT:
        if extractor == "nlp":
            from aesthetics_compiler.annotation.nlp_extractor import NlpExtractor
            result = NlpExtractor().extract(text)  # type: ignore[name-defined]
            extractor_tier = CompilerTier.NLP
        else:
            from aesthetics_compiler.annotation.rule_extractor import RuleExtractor
            result = RuleExtractor().extract(text)  # type: ignore[name-defined]
            extractor_tier = CompilerTier.RULE
    elif detected == InputMode.IMAGE:
        from aesthetics_compiler.annotation.image_extractor import ImageExtractor
        result = ImageExtractor().extract(raw_meta)
        extractor_tier = CompilerTier.IMAGE
    elif detected == InputMode.HTML:
        from aesthetics_compiler.annotation.html_extractor import HtmlExtractor
        result = HtmlExtractor().extract(raw_meta)
        extractor_tier = CompilerTier.HTML
    elif detected == InputMode.MULTIMEDIA:
        from aesthetics_compiler.annotation.multimedia_extractor import MultimediaExtractor
        result = MultimediaExtractor().extract(frames, raw_meta)
        extractor_tier = CompilerTier.MULTIMEDIA
    else:
        from aesthetics_compiler.annotation.mock_extractor import MockExtractor
        result = MockExtractor().extract()
        extractor_tier = CompilerTier.MOCK

    passes.append(PassRecord(pass_number=2, pass_name="extraction", status="ok",
                             note=f"tier={extractor_tier}; {len(result.elements)} elements"))

    # ------------------------------------------------------------------
    # Pass 7: Canonicalization
    # ------------------------------------------------------------------
    from aesthetics_compiler.canonicalizer.registry import StyleRegistry
    registry = StyleRegistry()
    if result.artist_hint:
        result.artist_hint = registry.canonicalize(result.artist_hint)
    passes.append(PassRecord(pass_number=7, pass_name="canonicalization", status="ok"))

    # ------------------------------------------------------------------
    # Assemble draft IR
    # ------------------------------------------------------------------
    inferred_title = title or _infer_title(source)
    doc = Document(
        title=inferred_title,
        source=source,
        sha256=sha256_input,
        medium=result.medium_hint,
        style_period=result.style_period_hint,
        artist=result.artist_hint,
        input_mode=detected.value,
        width_px=raw_meta.get("width"),
        height_px=raw_meta.get("height"),
        duration_s=raw_meta.get("duration_s"),
    )

    ir = AestheticIR(
        document=doc,
        elements=result.elements,
        zones=result.zones,
        color_schemes=result.color_schemes,
        motifs=result.motifs,
        aesthetic_facts=result.aesthetic_facts,
        segments=segments,
    )

    # ------------------------------------------------------------------
    # Pass 7.5: Graph synthesis
    # ------------------------------------------------------------------
    graph = graph_from_ir(ir)
    graph_hash = canonical_hash(graph)
    graph.graph_hash = graph_hash
    ir.aesthetic_graph = graph
    passes.append(PassRecord(pass_number=7.5, pass_name="graph_synthesis", status="ok",
                             note=f"hash={graph_hash[:16]}…"))

    # ------------------------------------------------------------------
    # Pass 8: AM-DAG
    # ------------------------------------------------------------------
    ir.aggregate_aesthetic_vector = AMDAG().evaluate(ir)
    ir.per_element_vectors = {
        e.id: e.aesthetic_vector for e in ir.elements
    }
    passes.append(PassRecord(pass_number=8, pass_name="am_dag", status="ok"))

    # ------------------------------------------------------------------
    # Pass 10: Projections
    # ------------------------------------------------------------------
    for proj_id in projections:
        proj = _PROJECTION_REGISTRY[proj_id]
        ir.projections[proj_id] = proj.run(ir)
    passes.append(PassRecord(pass_number=10, pass_name="projection_evaluation", status="ok",
                             note=f"projections={projections}"))

    # ------------------------------------------------------------------
    # Pass 11: Cross-projection disagreement + harmony verdict
    # ------------------------------------------------------------------
    polarities = {pid: pr.polarity for pid, pr in ir.projections.items()}
    unique_nonneural = {p for p in polarities.values() if p != "neutral"}
    if "harmonious" in unique_nonneural and "discordant" in unique_nonneural:
        ir.cross_projection_disagreement = {
            "verdicts": {pid: pr.verdict for pid, pr in ir.projections.items()},
            "polarities": polarities,
            "note": (
                "Projections disagree on polarity. "
                "The compiler surfaces all verdicts; choosing is the caller's responsibility."
            ),
        }
        ir.aesthetic_verdict = AestheticVerdict(
            verdict="projection_conflict",
            confidence=0.5,
            explanation="Aesthetic frameworks disagree; no single verdict is appropriate",
        )
    else:
        ir.aesthetic_verdict = _aggregate_verdict(ir.projections)

    passes.append(PassRecord(pass_number=11, pass_name="harmony_verdict", status="ok"))

    # ------------------------------------------------------------------
    # Pass 12: Audit
    # ------------------------------------------------------------------
    ir.audit = build_audit(
        passes, str(extractor_tier), detected.value,
        projections, graph_hash, sha256_input,
    )

    return ir


def _aggregate_verdict(projections: dict) -> AestheticVerdict:
    from collections import Counter
    if not projections:
        return AestheticVerdict(verdict="neutral", confidence=0.5)

    polarity_counts: Counter = Counter(pr.polarity for pr in projections.values())
    dominant_polarity = polarity_counts.most_common(1)[0][0]

    scores = [pr.score for pr in projections.values()]
    avg_score = sum(scores) / len(scores)

    best_pid = max(projections, key=lambda pid: projections[pid].score)
    best = projections[best_pid]

    if dominant_polarity == "harmonious":
        verdict = "aesthetically_harmonious"
    elif dominant_polarity == "discordant":
        verdict = "aesthetically_discordant"
    else:
        verdict = "aesthetically_neutral"

    return AestheticVerdict(
        verdict=verdict,
        confidence=round(polarity_counts[dominant_polarity] / len(projections), 2),
        explanation=f"Dominant polarity: {dominant_polarity}; avg projection score: {avg_score:.2f}",
        dominant_projection=best_pid,
    )


def _infer_title(source: str) -> str:
    p = Path(source)
    if p.exists():
        return p.stem.replace("_", " ").replace("-", " ").title()
    first_line = source.split("\n")[0].strip()
    return (first_line[:80] if first_line else "Untitled") or "Untitled"
