# geometric-aesthetics-compiler Architecture (v0.1.0)

This document describes the runtime architecture as of `main` at v0.1.0. For the eleven-module AM-DAG see `docs/am_dag.md`. For the four projections see `docs/projections.md`. For extraction tiers and vocabulary tables see `docs/extraction.md`.

## One-paragraph summary

A source (text, image, HTML, or multimedia) compiles into a typed `AestheticGraph` with a canonical SHA-256 hash anchored in the audit chain. Four aesthetic `Projection` analysers read that graph and emit projection-relative verdicts grounded in their respective theoretical frameworks (Birkhoff, Arnheim, Berlyne, Gestalt). When projections disagree by normalised polarity, the compiler refuses to aggregate and surfaces all verdicts via `ir.cross_projection_disagreement`. The eleven-module AM-DAG evaluates aesthetic dimensions in topological dependency order and writes the aggregate `AestheticVector` into the IR. Projections are selected at compile time via `--projection`; any subset is valid. Input mode is auto-detected from file extension; `--input-mode` overrides.

---

## The two-layer IR

```
              ┌──────────────────────────────────────────────┐
              │              AestheticGraph (DAG)             │
              │                                              │
              │  Nodes: element · zone · color_scheme ·      │
              │         motif · tension_vector · fact        │
              │                                              │
              │  Edges: contains · contrasts · grouped_with ·│
              │         anchors · mirrors · belongs_to ·     │
              │         generates_tension · overlaps ·       │
              │         dominates · part_of_motif            │
              │                                              │
              │  Canonical SHA-256 → audit.graph_hash        │
              └──────────────────────────────────────────────┘
                                   │
                       (typed graph queries)
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
┌─────────────────┐   ┌──────────────────────┐   ┌──────────────────────────┐
│ BirkhoffProject-│   │ ArnheimProjection     │   │ BerlyneProjection        │
│ ion             │   │                       │   │                          │
│ M=log(1+O)/     │   │ Visual weight balance │   │ Arousal potential A =    │
│   (1+C)         │   │ Spatial equilibrium   │   │ Σ w_i · k_i              │
│                 │   │ Tension-balance ideal │   │ Hedonic H = 1-(|A-A*|    │
│ verdict:        │   │                       │   │            /A*)²         │
│  high_aesthetic_│   │ verdict:              │   │                          │
│  measure /      │   │  spatial_equilibrium /│   │ verdict:                 │
│  complexity_    │   │  dynamic_tension /    │   │  optimal_arousal /       │
│  dominated      │   │  structural_discord   │   │  overarousal_aversive /  │
│                 │   │                       │   │  underarousal_boring     │
│ polarity:       │   │ polarity:             │   │                          │
│  harmonious /   │   │  harmonious /         │   │ polarity:                │
│  neutral /      │   │  neutral /            │   │  harmonious /            │
│  discordant     │   │  discordant           │   │  neutral /               │
│                 │   │                       │   │  discordant              │
└─────────────────┘   └──────────────────────┘   └──────────────────────────┘

              ┌──────────────────────────────────────┐
              │         GestaltProjection             │
              │                                      │
              │  Grouping strength (GROUPED_WITH      │
              │  edges / element count)               │
              │  Figure-ground clarity (contrast)     │
              │  Closure satisfaction (1 - closure)   │
              │  Unity = order×0.4 + grouping×0.3     │
              │          + closure_sat×0.3            │
              │                                      │
              │  verdict:                            │
              │   gestalt_coherent /                 │
              │   partial_gestalt_unity /            │
              │   gestalt_dissolution                │
              │                                      │
              │  polarity:                           │
              │   harmonious / neutral / discordant  │
              └──────────────────────────────────────┘

                                   │
      ┌────────────────────────────┴────────────────────────────┐
      │  Cross-projection polarity comparison                    │
      │  If {harmonious, discordant} both present → populate    │
      │  ir.cross_projection_disagreement; refuse to aggregate  │
      └──────────────────────────────────────────────────────────┘
```

The substrate is **descriptive**: what visual elements are present, how they relate spatially and chromatically, what aesthetic facts have been detected. The projections are **framework-bound**: each reads the same graph through the lens of a specific aesthetic theory and emits the kind of analytical object that theory actually produces. The compiler never silently aggregates across frameworks because framework selection is itself an aesthetic judgment.

---

## AestheticGraph schema

`src/aesthetic_compiler/ir/graph/`

```python
class NodeKind(str, Enum):
    ELEMENT      = "element"         # a visual design element
    ZONE         = "zone"            # spatial region (foreground, golden_ratio, …)
    COLOR_SCHEME = "color_scheme"    # a coherent colour relationship
    MOTIF        = "motif"           # repeated visual pattern
    TENSION_VEC  = "tension_vector"  # implied directional force
    FACT         = "fact"            # detected aesthetic property

class EdgeKind(str, Enum):
    CONTAINS          = "contains"           # zone → element
    CONTRASTS         = "contrasts"          # element ↔ element (colour/value)
    GROUPED_WITH      = "grouped_with"       # element ↔ element (Gestalt)
    ANCHORS           = "anchors"            # element → zone
    MIRRORS           = "mirrors"            # element ↔ element (symmetry)
    BELONGS_TO        = "belongs_to"         # element → color_scheme
    GENERATES_TENSION = "generates_tension"  # element → tension_vector
    OVERLAPS          = "overlaps"           # element → element
    DOMINATES         = "dominates"          # element → element (visual weight)
    PART_OF_MOTIF     = "part_of_motif"      # element → motif
```

`AestheticNode.aesthetic_scores` holds raw float values from the element's `AestheticVector` (one float per dimension in `[-1, 1]`), enabling projection code to query dimension scores without re-traversing the flat IR.

### Canonical hashing

`ir/graph/canonical.py` produces a deterministic JSON encoding (nodes sorted by `id`, edges sorted by `(src, dst, kind)`) and an SHA-256 over it. Identical nodes-and-edges content produces the same hash regardless of insertion order. Anchored in `AuditRecord.graph_hash`.

### Graph synthesis (Pass 7.5)

`ir/graph/promote.py` — `graph_from_ir(ir) -> AestheticGraph`.

- Every `AestheticElement` becomes an `ELEMENT` node with `aesthetic_scores` populated from its `AestheticVector`.
- Every `CompositionZone` becomes a `ZONE` node with `CONTAINS` edges to its member elements.
- Every `ColorScheme` becomes a `COLOR_SCHEME` node with `BELONGS_TO` edges from its member elements.
- Every `VisualMotif` becomes a `MOTIF` node with `PART_OF_MOTIF` edges from its member elements.
- Every `AestheticFact` becomes a `FACT` node.

---

## The eleven aesthetic dimensions

```
k=0   complexity    — edge density, element count, visual clutter
k=1   order         — symmetry, alignment, grid regularity
k=2   balance       — spatial equilibrium, center-of-mass deviation
k=3   density       — fill ratio, visual weight
k=4   hue_coherence — monochromatic vs. polychromatic palette
k=5   saturation    — vibrant vs. muted
k=6   contrast      — luminance range, figure-ground separation
k=7   color_harmony — color-wheel relationship quality
k=8   tension       — directional forces, dynamic vs. static
k=9   closure       — Gestalt completion demand
k=10  rhythm        — temporal pacing (0 for static inputs)
```

Each dimension is encoded as a `DimensionScore` in `[-1, 1]`:

```python
class DimensionScore(BaseModel):
    value:       float   # ∈ [-1, 1]
    confidence:  float   # ∈ [0, 1]
    direction:   Literal["dominant", "present", "trace", "absent"]
    explanation: str | None
```

Direction thresholds: `dominant` ≥ 0.65, `present` ≥ 0.35, `trace` ≥ 0.10, `absent` < 0.10.

---

## The four input modes

| Mode | Trigger | Extractor | Key technique |
|---|---|---|---|
| `text` | `.txt`, `.md`, plain string | `RuleExtractor` | Vocabulary table matching; artist style profiles |
| `image` | `.jpg`, `.png`, `.webp`, `.gif` (static) | `ImageExtractor` | Luminance gradient, HSV histogram, symmetry flip-and-compare |
| `html` | `.html`, `.htm` | `HtmlExtractor` | `html.parser` DOM traversal; CSS colour regex |
| `multimedia` | `.mp4`, `.avi`, `.mov`, `.gif` (animated) | `MultimediaExtractor` | Frame sampling; inter-frame luminance diff for rhythm (k=10) |

All four modes produce the same `AestheticIR` schema. Projections, the AM-DAG, and the audit chain are identical regardless of input mode.

---

## The 13-pass pipeline

| Pass | Stage | Implementation |
|---|---|---|
| 0 | Ingestion | `ingestion/{text,image,html,multimedia}_loader.py` — load source; return `(content, sha256)` |
| 1 | Segmentation | `segmentation/segmenter.py` — text only; classify paragraphs by aesthetic vocabulary type |
| 2–6 | Extraction | `annotation/{rule,image,html,multimedia}_extractor.py` — elements, zones, colour schemes, motifs, aesthetic facts |
| 7 | Canonicalization | `canonicalizer/registry.py` — alias resolution (e.g. *colour field* → *color_field*, *rothko style* → *rothko*) |
| **7.5** | **Graph synthesis** | `ir/graph/promote.py` — promote flat extractor output to `AestheticGraph`; compute `graph_hash` |
| **8** | **AM-DAG** | `am_dag/dag.py` — run 11 aesthetic modules in topological order; write aggregate `AestheticVector` |
| 9 | Codegen | IR finalization (no-op pass record; IR fully assembled) |
| 10 | Projection evaluation | `projections/` — run each selected projection; write `ir.projections` |
| 11 | Harmony verdict | `pipeline/orchestrator.py:_aggregate_verdict` — aggregate polarity votes; populate `ir.aesthetic_verdict` |
| 12 | Audit | `audit/hash_chain.py` — finalize `AuditRecord` |

### Projection selection at compile time

```bash
# All four (default)
aesthetic-compile compile artwork.txt

# Subset
aesthetic-compile compile artwork.jpg --projection birkhoff,arnheim

# Force input mode
aesthetic-compile compile page.html --input-mode html --projection gestalt
```

---

## Projection layer

`src/aesthetic_compiler/projections/`

Each `BaseProjection` reads the fully-assembled `AestheticIR` and returns a `ProjectionResult`:

```python
class ProjectionResult(BaseModel):
    projection_id: str
    verdict:       str
    polarity:      Literal["harmonious", "neutral", "discordant"]
    findings:      list[AestheticFinding]
    score:         float   # ∈ [-1, 1]
    explanation:   str | None
```

| Projection | Reads | Key formula | Verdict polarities |
|---|---|---|---|
| **`BirkhoffProjection`** | `order`, `complexity` | M = log(1+O)/(1+C) | all three |
| **`ArnheimProjection`** | `balance`, `tension`, `order` | balance×0.6 + (1−\|tension−0.35\|)×0.4 | all three |
| **`BerlyneProjection`** | `complexity`, `contrast`, `tension`, `saturation`, `closure` | A = Σw_i·k_i; H = 1−(\|A−0.5\|/0.5)² | all three |
| **`GestaltProjection`** | `closure`, `order`, `contrast`, graph edges | unity = order×0.4 + grouping×0.3 + closure_sat×0.3 | all three |

### Cross-projection disagreement

`ir.cross_projection_disagreement` is populated iff ≥ 2 active projections emit distinct non-neutral polarities. Comparison is on **polarity** (`harmonious` vs. `discordant`), not on verdict strings.

```python
{
  "verdicts":   { projection_id: verdict_str, … },
  "polarities": { projection_id: "harmonious"|"neutral"|"discordant", … },
  "note": "Projections disagree on polarity. The compiler surfaces all verdicts; …"
}
```

The compiler does **not** populate a winner.

---

## AM-DAG (aesthetic evaluator)

`src/aesthetic_compiler/am_dag/`

Eleven modules run in topological dependency order. See `docs/am_dag.md` for full specifications.

```
Roots (no upstream dependencies):
    ComplexityModule    k=0  — edge density + element count
    HueCoherenceModule  k=4  — hue histogram entropy

Second tier (read complexity or hue_coherence):
    OrderModule         k=1  — reads complexity (high complexity → order penalty)
    SaturationModule    k=5  — reads hue_coherence (polychromatic high-sat → clash risk)

Third tier (read order):
    BalanceModule       k=2  — reads order (high order → balance boost)
    DensityModule       k=3  — reads complexity

Fourth tier (read order, balance, hue_coherence, saturation):
    ContrastModule      k=6  — reads balance, density (via facts)
    ColorHarmonyModule  k=7  — reads hue_coherence, saturation

Fifth tier (read order, balance, contrast, color_harmony):
    TensionModule       k=8  — reads order, balance (low balance → tension amplified)
    ClosureModule       k=9  — reads complexity, order

Sixth tier:
    RhythmModule        k=10 — reads motifs; base from multimedia extractor
```

Key inter-module dependencies:

- **Complexity → Order**: `OrderModule` applies `−0.1 × max(0, complexity − 0.6)` — high visual clutter erodes perceived order.
- **HueCoherence → Saturation**: `SaturationModule` detects garish risk when `saturation > 0.7` and `hue_coherence < 0.3`, emitting a `color_clash` fact.
- **Order → Balance**: `BalanceModule` applies `+0.05 × max(0, order − 0.5)` — symmetrical compositions tend to feel balanced.
- **Balance → Tension**: `TensionModule` applies `+0.15 × max(0, 0.5 − balance)` — off-balance compositions read as tense (Arnheim).
- **Complexity+Order → Closure**: `ClosureModule` adds `0.1 × max(0, complexity − order)` — complex compositions with little order leave more forms visually open.

---

## Audit chain

`AuditRecord` carries:

- `passes` — per-pass `PassRecord` list
- `extractor_tier` — the tier used (`rule`, `image`, `html`, `multimedia`, `mock`)
- `input_mode` — the detected or forced input mode
- `active_projections` — projection IDs that were run
- `graph_hash` — SHA-256 of the canonical `AestheticGraph`
- `input_sha256` — SHA-256 of the raw input bytes
- `provenance.schema` — `"aesthetic_ir_v0.1"`
- `provenance.passes_completed` — count of `ok` passes

Identical input + extractor tier + projection set produces identical `graph_hash`.

---

## AestheticIR field reference

```
ir.document                       Document metadata (title, source, sha256, medium,
                                  artist, style_period, input_mode, width_px, …)
ir.elements                       list[AestheticElement]
ir.zones                          list[CompositionZone]
ir.color_schemes                  list[ColorScheme]
ir.motifs                         list[VisualMotif]
ir.aesthetic_facts                list[AestheticFact]
ir.segments                       list[Segment]  — text input only
ir.aesthetic_graph                AestheticGraph — populated Pass 7.5
ir.aggregate_aesthetic_vector     AestheticVector — populated Pass 8
ir.per_element_vectors            dict[element_id, AestheticVector]
ir.projections                    dict[projection_id, ProjectionResult] — Pass 10
ir.cross_projection_disagreement  dict | None — populated Pass 10
ir.aesthetic_verdict              AestheticVerdict — populated Pass 11
ir.audit                          AuditRecord — populated Pass 12
ir.schema_version                 "aesthetic_ir_v0.1"
```

---

## Export formats

| Format | Command | File |
|---|---|---|
| AestheticIR JSON | `aesthetic-compile compile … --out file.ir.json` | orchestrator |
| Schema.org/VisualArtwork JSON-LD | `aesthetic-compile export-schema-org file.ir.json` | `export/schema_org.py` |

---

## What this architecture is not

- **Not a universal aesthetic authority.** Birkhoff's M is a Western, mathematically reductive measure that ignores context, culture, and viewer. Gestalt principles were developed primarily on European perceivers. The compiler makes these frameworks explicit and refuses to aggregate them silently.
- **Not a full computer-vision system.** The image extractor derives dimension scores from luminance gradients and colour histograms without semantic segmentation. It cannot identify objects, faces, or named pictorial elements.
- **Not a web renderer.** The HTML extractor parses raw HTML and CSS text; it does not simulate browser rendering, flexbox/grid layout, or JavaScript-driven positioning.
- **Not a temporal media analyser.** The multimedia extractor samples frames and measures inter-frame difference; it does not perform shot detection, scene segmentation, or audio analysis.
- **Not a replacement for art criticism.** The projection findings and aesthetic verdict are structured inputs to human aesthetic judgment, not substitutes for it.
