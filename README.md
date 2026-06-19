# aesthetics-compiler

A structure-preserving aesthetic intermediate representation (AestheticIR) with pluggable aesthetic framework analysers.

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

## Acknowledgements

This compiler adapts the architecture of the **[ErisML Compiler](https://github.com/ahb-sjsu/erisml-compiler)** (Bond, 2025) — a structure-preserving moral IR with pluggable framework analysers — to the aesthetic domain. The IR-graph substrate, canonical hashing, pluggable-projection pattern, and non-aggregating cross-projection disagreement model all originate there.

## References

The four projections operationalise established theories of aesthetic perception:

- Birkhoff, G. D. (1933). *Aesthetic Measure.* Harvard University Press.
- Arnheim, R. (1954). *Art and Visual Perception: A Psychology of the Creative Eye.* University of California Press.
- Berlyne, D. E. (1971). *Aesthetics and Psychobiology.* Appleton-Century-Crofts.
- Wertheimer, M. (1923). Untersuchungen zur Lehre von der Gestalt. *Psychologische Forschung,* 4, 301–350.
- Köhler, W. (1947). *Gestalt Psychology.* Liveright.

Computational-aesthetics context and datasets for empirical validation:

- Datta, R., Joshi, D., Li, J., & Wang, J. Z. (2006). Studying aesthetics in photographic images using a computational approach. *ECCV.*
- Murray, N., Marchesotti, L., & Perronnin, F. (2012). AVA: A large-scale database for aesthetic visual analysis. *CVPR.*
- Kong, S., Shen, X., Lin, Z., Mech, R., & Fowlkes, C. (2016). Photo aesthetics ranking network with attributes and content adaptation (AADB). *ECCV.* — its 11 human-annotated attributes (balance, color harmony, symmetry, repetition, vivid color, …) map closely onto this compiler's dimensions and make it a natural validation target.

A full BibTeX bibliography is in [`paper/paper.bib`](paper/paper.bib).

## Citation

If you use this software, please cite:

```bibtex
@misc{Baley2026aesthetics,
  author = {Baley, Kim R. and Bond, Andrew H.},
  title  = {aesthetics-compiler: a structure-preserving aesthetic intermediate
            representation with pluggable framework analysers},
  year   = {2026},
  url    = {https://github.com/KRB4597/aesthetics-compiler},
  note   = {Adapts the ErisML Compiler architecture (Bond, 2025) to the aesthetic domain}
}
```
