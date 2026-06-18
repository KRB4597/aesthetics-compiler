# aesthetics-compiler

A structure-preserving aesthetic intermediate representation (AestheticIR) with pluggable culinary framework analysers.

Accepts **natural-language text descriptions** or **image files** (JPEG/PNG) and emits a typed `AestheticGraph` with a canonical SHA-256 hash. Four aesthetic projection analysers — Birkhoff, Arnheim, Berlyne, and Gestalt — read the same substrate and emit projection-relative harmony verdicts. When their normalised polarities disagree, the compiler surfaces all verdicts via `ir.cross_projection_disagreement` without aggregating.

## Install

```bash
pip install -e .
# With image CV extras:
pip install -e ".[cv]"
```

## Quick start

```bash
# Text description input
aesthetics-compile compile examples/rothko_description.txt

# Image file input
aesthetics-compile compile examples/composition.jpg

# Select projections
aesthetics-compile compile examples/mondrian_description.txt \
    --projection birkhoff,arnheim

# Save IR
aesthetics-compile compile examples/rothko_description.txt --out rothko.ir.json

# Generate report
aesthetics-compile report rothko.ir.json
```

## Ten aesthetic dimensions

| k | Dimension | Description |
|---|-----------|-------------|
| 0 | complexity | Visual clutter, element count, edge density |
| 1 | order | Symmetry, alignment, regularity |
| 2 | balance | Spatial equilibrium, center-of-mass deviation |
| 3 | density | Fill ratio, visual weight |
| 4 | hue_coherence | Monochromatic vs. polychromatic palette |
| 5 | saturation | Vibrant vs. muted |
| 6 | contrast | Luminance range, figure-ground separation |
| 7 | color_harmony | Color-wheel relationship quality |
| 8 | tension | Directional forces, dynamic vs. static |
| 9 | closure | Gestalt completion demand |

## Four projections

| Projection | Theoretical basis |
|---|---|
| `birkhoff` | Birkhoff (1933) M = O/C aesthetic measure |
| `arnheim` | Arnheim (1954) visual dynamics and spatial equilibrium |
| `berlyne` | Berlyne (1971) arousal potential and hedonic curves |
| `gestalt` | Wertheimer / Gestalt grouping, figure-ground, closure |

## Architecture

See `docs/architecture.md`.
