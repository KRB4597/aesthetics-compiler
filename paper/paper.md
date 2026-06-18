---
title: 'geometric-aesthetics-compiler: a structure-preserving aesthetic intermediate representation with pluggable framework analysers'

tags:
  - Python
  - computational aesthetics
  - aesthetic analysis
  - intermediate representation
  - graph IR
  - visual composition
  - color theory
  - natural language processing
  - image analysis
  - multimedia

authors:
  - name: Kim R. Baley
    affiliation: 1
  - name: Andrew H. Bond
    orcid: 0009-0009-1769-5099
    affiliation: 2

affiliations:
  - name: Justice Innovations, USA
    index: 1
  - name: San José State University, San José, CA, USA
    index: 2

date: 18 June 2026

bibliography: paper.bib

---

## Summary

`geometric-aesthetics-compiler` is a Python compiler that accepts natural-language
descriptions, image files (JPEG/PNG), HTML documents, or multimedia (video/GIF)
as input and emits a typed directed acyclic graph — the **AestheticGraph** —
anchored by a canonical SHA-256 hash. Four aesthetic projection analysers
(Birkhoff, Arnheim, Berlyne, and Gestalt) read the same substrate and emit
projection-relative verdicts. When their normalised polarities disagree, the
compiler **refuses to aggregate** and surfaces all verdicts via
`ir.cross_projection_disagreement`, deferring framework selection to the caller.
An eleven-module **AM-DAG** (Aesthetic Module directed acyclic graph) evaluates
each of the eleven canonical aesthetic dimensions (complexity, order, balance,
density, hue\_coherence, saturation, contrast, color\_harmony, tension, closure,
rhythm) in topological dependency order, encoding known perceptual interactions
such as the Birkhoff order-complexity tradeoff [@Birkhoff1933], Arnheim's
visual-weight balance rules [@Arnheim1954], and Berlyne's inverted-U hedonic
curve [@Berlyne1971]. The rule extractor grounds style vocabulary in the
established computational aesthetics literature [@Datta2006] and in the companion
mathematical framework of *Geometric Aesthetics* [@Bond2026aesthetics]. All
results are auditable: every IR carries hashed provenance for the input, the
AestheticGraph, and the active projection set.

## Statement of need

Computational aesthetics has historically converged on scalar outputs — an
"aesthetic quality score," a "beauty rating," or a neural network confidence
that a photograph is "professional." This convergence is understandable: scalars
compose cleanly with ranking and recommendation pipelines. But it discards the
structure that aesthetic reasoning is actually about.

A designer deciding whether a layout is aesthetically successful is simultaneously
reasoning about Birkhoff's order-complexity ratio (is there enough structure to
make sense of the complexity?), Arnheim's visual balance (is the distribution of
visual weight in equilibrium?), Berlyne's arousal potential (is the composition
stimulating enough without crossing into aversion?), and Gestalt coherence (does
the composition read as a unified whole?). A scalar "0.87 aesthetic quality"
cannot represent that. Worse, scalar scoring pre-commits to a specific framework —
typically a deep learning model trained on human ratings — whose theoretical
choices are invisible: the system looks framework-neutral while quietly encoding
one aesthetic tradition at every aggregation step.

`geometric-aesthetics-compiler` addresses both problems architecturally.

**Structure preservation**: the IR is a typed graph (nodes are elements, zones,
color schemes, motifs, tension vectors, and aesthetic facts; edges are typed
compositional relations — `contrasts`, `grouped_with`, `mirrors`, `dominates`,
`generates_tension`, etc.), not a scalar. The AestheticGraph plays the same role
for aesthetic reasoning that an SSA-form IR plays for code generation: a
structured intermediate that later passes can analyse, transform, and emit from.
The canonical SHA-256 hash makes every compiled artwork reproducible and
auditable.

**Projection pluralism**: each aesthetic theory gets a first-class `Projection`
of its own primitives. The Birkhoff projection computes M = log(1+O)/(1+C),
the classical order-over-complexity formula, and emits findings for order
deficit and complexity excess. The Arnheim projection applies the visual-weight
balance model and identifies whether a composition has achieved Arnheim's ideal
of "expressive equilibrium" [@Arnheim1954]. The Berlyne projection computes
arousal potential as a weighted sum of complexity, contrast, tension, saturation,
and closure, and maps it onto the inverted-U hedonic curve to predict whether
the composition falls in the under-arousing, optimal, or overarousing range
[@Berlyne1971]. The Gestalt projection measures grouping coherence, figure-ground
clarity, closure satisfaction, and unity. When projections disagree on polarity,
the compiler does not pick a winner — that choice is itself an aesthetic and
theoretical judgment, and it is deferred to the caller explicitly.

The compiler also accepts **four input modalities** from a single unified pipeline:
natural-language text (for art criticism, design briefs, and curatorial
descriptions), image files (JPEG/PNG analysed via Pillow and NumPy), HTML
documents (CSS color extraction, DOM structural analysis), and multimedia
(video/GIF frame sampling with temporal pacing estimation). All four modes
produce the same `AestheticIR`, enabling cross-modal comparison.

To our knowledge no other open-source artifact combines (a) a typed aesthetic
graph IR spanning four input modalities, (b) multiple first-class aesthetic
theory analysers over a shared substrate with honest polarity disagreement,
and (c) an eleven-dimension aesthetic vector grounded in a century of
experimental aesthetics research from Birkhoff through Berlyne. Adjacent work
falls into three categories: deep learning aesthetic scoring models that reduce
to a single quality number [@Datta2006; @Karayev2013]; image feature extraction
libraries that compute metrics without theoretical framework; and expert systems
that encode only one tradition's norms. `geometric-aesthetics-compiler`
occupies the structural-compositional gap between these.

The compiler is designed as the computational counterpart to *Geometric
Aesthetics* [@Bond2026aesthetics], which develops the mathematical structure of
aesthetic space — compositions as vectors in perceptual receptor space, visual
transformations as geometric operators, aesthetic evaluation as manifold
geometry — but does not itself provide a runnable implementation.

## Software description

The compiler implements a **13-pass pipeline** across four input modalities.
Passes 0–6 ingest the source, segment text (for textual input), and extract
aesthetic elements through one of four tiered extractors: a rule-based text
extractor (Tier 1) that matches against vocabulary tables for complexity,
order, balance, saturation, colour harmony, tension, closure, and rhythm
terms, and canonicalises known artist styles (Rothko, Mondrian, Pollock,
Kandinsky, Monet, Picasso, Vermeer) against profile dictionaries; an image
extractor (Tier 2) that derives dimension scores computationally from luminance
gradients, HSV histograms, symmetry indices, and centre-of-mass calculations;
an HTML extractor (Tier 3) that parses DOM structure, extracts CSS colour
values, and scores harmony from hue distributions; and a multimedia extractor
(Tier 4) that samples up to thirty frames from video/animated GIF files,
averages spatial aesthetic dimensions across frames, and computes a temporal
rhythm score from inter-frame luminance differences. Pass 7 canonicalises
style vocabulary. Pass 7.5 promotes the flat extractor output into a typed
`AestheticGraph`. Pass 8 runs the AM-DAG over the populated IR. Passes 10–11
run the enabled projections and aggregate a verdict. Pass 12 finalises the
audit record.

Five capabilities are first-class:

- **Typed graph IR** (`ir/graph/`). Six node kinds (`element`, `zone`,
  `color_scheme`, `motif`, `tension_vector`, `fact`) and ten edge kinds;
  canonical SHA-256 hashing; bidirectional derivation from the flat extractor
  output via `graph_from_ir`.

- **Eleven-dimension AM-DAG** (`am_dag/`). Aesthetic modules run in topological
  order: `ComplexityModule` and `HueCoherenceModule` execute first because
  later modules (`OrderModule`, `SaturationModule`, `TensionModule`,
  `ClosureModule`) depend on their outputs as perceptual modifiers.
  Concretely: high complexity penalises perceived order; hue coherence modulates
  saturation harmony; low balance amplifies tension; high complexity with low
  order raises Gestalt closure demand. The aggregate `AestheticVector` encodes
  all eleven dimensions as signed `DimensionScore` objects in $[-1, 1]$,
  each carrying a confidence, a direction label (`dominant`, `present`,
  `trace`, `absent`), and a natural-language explanation.

- **Four compile-time selectable projections** (`projections/`).
  `BirkhoffProjection` computes M = log(1+O)/(1+C) and emits findings for
  order deficit and complexity excess. `ArnheimProjection` evaluates balance
  and tension against Arnheim's spatial equilibrium model, identifying
  compositions that achieve his ideal of balanced expressiveness.
  `BerlyneProjection` computes weighted arousal potential from complexity
  (weight 0.30), contrast (0.25), tension (0.20), saturation (0.15), and
  closure (0.10), and maps the result onto the inverted-U to predict hedonic
  value. `GestaltProjection` measures grouping strength from `GROUPED_WITH`
  edges, figure-ground clarity from contrast, closure satisfaction, and unity
  as a weighted combination of order, grouping, and closure satisfaction. Any
  subset may be selected at compile time via `--projection`.

- **Multimodal input** (`ingestion/`). A single `compile` command
  auto-detects the input mode from the file extension (`.txt`/`.md` →
  text; `.jpg`/`.png`/`.webp` → image; `.html`/`.htm` → HTML;
  `.mp4`/`.avi`/`.gif` → multimedia). The `--input-mode` flag overrides
  auto-detection. All four modes produce `AestheticIR` objects with the same
  schema, enabling direct comparison of a painting described in text against
  the same painting analysed as an image file.

- **Cross-projection disagreement surface**. When two or more active
  projections emit distinct non-neutral polarities (`harmonious` vs.
  `discordant`), the compiler populates `ir.cross_projection_disagreement`
  with all projection verdicts and a note that framework selection is the
  caller's responsibility. The aesthetic verdict in this case is
  `projection_conflict` rather than a silently aggregated scalar.

The compiler also ships a **Schema.org/VisualArtwork export**
(`export/schema_org.py`) that re-serialises the IR as JSON-LD, enabling
direct integration with digital humanities knowledge graphs and institutional
catalogue systems.

## Worked example

On the bundled `rothko_description.txt` scenario, the rule extractor detects
dominant saturation and monochromatic hue vocabulary, a balanced and
meditative composition, and the Rothko artist style profile. The AM-DAG
produces an aggregate `AestheticVector` with `balance` (dominant, 0.91),
`hue_coherence` (dominant, 1.00), `color_harmony` (dominant, 1.00), and
`density` (dominant, 0.79) as the leading dimensions. The deliberately low
complexity (0.44, present) and very low contrast (0.25, trace) match the
characteristic Rothko color-field vocabulary of large, soft, nearly
monochromatic fields with blurred edges.

The four projections return:

| Projection | Verdict | Polarity | Score |
|---|---|---|---|
| `birkhoff` | `moderate_aesthetic_measure` | neutral | 0.533 |
| `arnheim` | `spatial_equilibrium` | harmonious | 0.916 |
| `berlyne` | `optimal_arousal` | harmonious | 0.906 |
| `gestalt` | `partial_gestalt_unity` | neutral | 0.460 |

The Birkhoff projection identifies moderate M: the low complexity is offset by
the fact that order is also only moderate (0.70), since Rothko deliberately
avoids the maximally ordered grid of De Stijl. The Arnheim projection correctly
identifies spatial equilibrium (balance=0.91). The Berlyne projection identifies
optimal arousal: a composition that sits precisely on the hedonic optimum —
complex enough to be absorbing, simple enough not to overwhelm. The Gestalt
projection identifies only partial unity, reflecting that the Rothko format
(two rectangles, no grouping edges between elements) does not produce strong
Gestalt coherence in the graph. The compiler emits a `neutral` aggregate
verdict at confidence 0.50 with `arnheim` as the dominant projection, because
the Birkhoff and Gestalt neutral verdicts cancel the Arnheim and Berlyne
harmonious verdicts.  The full result is reproducible with:

```bash
aesthetic-compile compile examples/rothko_description.txt \
    --projection birkhoff,arnheim,berlyne,gestalt
```

## Limitations

The rule extractor's vocabulary tables cover approximately 60 aesthetic terms
and seven canonical artists. Artworks described using regional idioms, technical
jargon, or non-Western aesthetic vocabularies may be poorly extracted. The image
extractor computes dimension scores from luminance gradients and colour
histograms without semantic object segmentation; it cannot distinguish a red
figure from a red background, or detect alignment relationships between named
elements. The HTML extractor cannot simulate rendering; CSS `calc()` expressions,
flexbox/grid layouts, and JavaScript-driven positioning are not analysed.
The multimedia extractor does not perform shot-detection, scene segmentation,
or audio analysis; it treats cuts as inter-frame luminance differences.
The Birkhoff projection uses a simplified M formula and does not model the
full range of symmetry operators Birkhoff identified in his original monograph.
Cultural and historical context — the difference between a Mondrian grid and
an Islamic tessellation that shares similar order and complexity scores — is
not currently captured. Each limitation is noted in the relevant module.

## Acknowledgements

The mathematical framework of aesthetic space that grounds this compiler's
type system was developed in *Geometric Aesthetics: The Mathematical Structure
of Visual Composition, Color Harmony, and Aesthetic Judgment* [@Bond2026aesthetics]
at San José State University. The compiler's pipeline architecture mirrors that
of `erisml-compiler` [@Bond2025] and `gastronomy-compiler` [@Baley2026], which
established the pattern of typed graph IR, tiered extraction, and pluralist
projection analysers.

## References

(The bibliography is stored separately in paper.bib)
