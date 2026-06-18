# AM-DAG: Eleven-Module Aesthetic Evaluator

`src/aesthetic_compiler/am_dag/`

The AM-DAG (Aesthetic Module directed acyclic graph) evaluates the eleven canonical aesthetic dimensions in topological dependency order and writes the aggregate `AestheticVector` into `ir.aggregate_aesthetic_vector` during Pass 8. Each module is a function `evaluate(ir, ctx) -> DimensionScore` in `am_dag/modules/`.

---

## Why a topological order?

Aesthetic perception is not independent across dimensions. High visual complexity erodes perceived order: a chaotic composition is harder to read as structured even if its individual symmetry score is moderate. Low spatial balance amplifies tension: Arnheim's visual-weight theory says off-balance compositions exert directional forces that read as tense. Polychromatic high-saturation colour creates a risk of clash that does not exist for a monochromatic palette at the same saturation level. These are documented perceptual interactions, not heuristics invented for this compiler.

A flat average, computed without order, cannot model these dependencies. The topological AM-DAG executes `ComplexityModule` before `OrderModule`, writes the complexity context, and lets `OrderModule` read from it to apply the appropriate penalty. Each inter-module dependency is modelled at the right place in the computation graph.

---

## Execution order

```
┌──────────────┐   ┌─────────────────┐
│ComplexityMod │   │HueCoherenceMod  │   ← roots (no upstream deps)
│    k=0       │   │    k=4          │
└──────┬───────┘   └────────┬────────┘
       │                    │
       ▼                    ▼
┌──────────────┐   ┌─────────────────┐
│  OrderMod    │   │ SaturationMod   │   ← reads complexity / hue_coherence
│    k=1       │   │    k=5          │
└──────┬───────┘   └────────┬────────┘
       │                    │
       ▼                    │
┌──────────────┐   ┌────────▼────────┐
│  BalanceMod  │   │  DensityMod     │
│    k=2       │   │    k=3          │
└──────┬───────┘   └────────┬────────┘
       │                    │
       └──────────┬──────────┘
                  ▼
       ┌──────────────────────────────────────┐
       │                                      │
┌──────▼───────┐                    ┌─────────▼──────────┐
│  ContrastMod │                    │  ColorHarmonyMod   │
│    k=6       │                    │    k=7             │
└──────┬───────┘                    └─────────┬──────────┘
       │                                      │
       └──────────────┬───────────────────────┘
                      │
            ┌─────────▼──────────┐   ┌───────────────────┐
            │    TensionMod      │   │    ClosureMod      │
            │       k=8          │   │       k=9          │
            └─────────┬──────────┘   └─────────┬─────────┘
                      │                        │
                      └────────────┬───────────┘
                                   ▼
                          ┌────────────────┐
                          │   RhythmMod    │
                          │     k=10       │
                          └────────────────┘
```

`_MODULE_ORDER` in `am_dag/dag.py`:

```python
_MODULE_ORDER = [
    ("complexity",    complexity.evaluate),
    ("order",         order.evaluate),
    ("hue_coherence", hue_coherence.evaluate),
    ("balance",       balance.evaluate),
    ("density",       density.evaluate),
    ("saturation",    saturation.evaluate),
    ("contrast",      contrast.evaluate),
    ("color_harmony", color_harmony.evaluate),
    ("tension",       tension.evaluate),
    ("closure",       closure.evaluate),
    ("rhythm",        rhythm.evaluate),
]
```

`AMDAG.evaluate(ir)` runs each module in sequence. Each module receives the `GastronomyIR` and a mutable `context: dict[str, float]` that accumulates intermediate values for downstream modules.

---

## Module specifications

### ComplexityModule (k=0)

**Dimension**: complexity — visual clutter, element count, edge density.

**Logic**:
1. Mean per-element complexity scores.
2. Element-count penalty: if `element_count > 15`, add `0.05 × (element_count − 15) / 10`, capped at 1.0.
3. Write `context["complexity"]`.

**Writes to context**: `complexity`

**Why first**: complexity is a perceptual modifier for order, density, and closure. All three downstream modules read from `context["complexity"]`.

---

### HueCoherenceModule (k=4)

**Dimension**: hue_coherence — how clustered vs. scattered the colour palette is.

**Logic**:
1. Mean per-element hue_coherence scores.
2. Color-scheme adjustment: `monochromatic` scheme adds +0.10; `polychromatic` subtracts 0.05.
3. Write `context["hue_coherence"]`.

**Writes to context**: `hue_coherence`

**Why root**: hue coherence is a perceptual modifier for saturation (polychromatic high-saturation → garish risk). It has no upstream spatial dependencies.

---

### OrderModule (k=1)

**Dimension**: order — symmetry, alignment, grid regularity.

**Logic**:
1. Mean per-element order scores.
2. Symmetry edge bonus: each `MIRRORS` edge in the `AestheticGraph` adds up to +0.15 total.
3. Complexity penalty: `−0.1 × max(0, context["complexity"] − 0.6)`. High clutter erodes perceived structure.

**Reads from context**: `complexity`
**Writes to context**: `order`

**Inter-module motivation**: Birkhoff's O and C are formally independent but perceptually linked — the same composition is harder to read as "ordered" when it is also highly complex.

---

### BalanceModule (k=2)

**Dimension**: balance — spatial equilibrium, center-of-mass deviation.

**Logic**:
1. Mean per-element balance scores.
2. High-salience periphery zone penalty: each `zone.zone_type == "periphery"` with `salience > 0.7` subtracts 0.10.
3. Order boost: `+0.05 × max(0, order − 0.5)`. Symmetrical/grid compositions tend to feel balanced.

**Reads from context**: `order`
**Writes to context**: `balance`

---

### DensityModule (k=3)

**Dimension**: density — fill ratio, visual weight.

**Logic**:
1. Mean per-element density scores.
2. Negative-space penalty: low-salience periphery zones subtract 0.05 each.
3. Complexity contribution: `+0.1 × context["complexity"]`.

**Reads from context**: `complexity`
**Writes to context**: `density`

---

### SaturationModule (k=5)

**Dimension**: saturation — vibrant vs. muted palette.

**Logic**:
1. Mean per-element saturation scores.
2. Clash detection: if `saturation > 0.7` and `hue_coherence < 0.3`, emit a `color_clash` `AestheticFact` into `ir.aesthetic_facts`. The fact is read downstream by `ColorHarmonyModule` and `GestaltProjection`.

**Reads from context**: `hue_coherence`
**Writes to context**: `saturation`

**Inter-module motivation**: high saturation is not intrinsically bad. It is bad in combination with many scattered hues. Separating the two modules allows the polarity of the interaction to be evaluated explicitly rather than baked into a single composite score.

---

### ContrastModule (k=6)

**Dimension**: contrast — luminance range, Weber-Fechner log-scale.

**Logic**:
1. Mean per-element contrast scores.
2. If any `ir.aesthetic_facts` entries have `dimension == "contrast"` with `severity in ("high", "moderate")`, add +0.05.

**Reads from context**: (reads facts, not ctx keys)
**Writes to context**: `contrast`

---

### ColorHarmonyModule (k=7)

**Dimension**: color_harmony — color-wheel relationship quality.

**Logic**:
1. Mean per-element color_harmony scores.
2. Scheme bonus: the `harmony_type` of each `ColorScheme` in the IR maps to a score (monochromatic=0.9, analogous=0.85, complementary=0.85, triadic/split_complementary=0.80, tetradic=0.70, polychromatic=0.45). The best scheme's surplus over 0.5 adds up to +0.3 × 0.15 = +0.045 maximum.
3. Coherence boost: `+0.05 × (hue_coherence − 0.5)`.

**Reads from context**: `hue_coherence`, `saturation`
**Writes to context**: `color_harmony`

---

### TensionModule (k=8)

**Dimension**: tension — directional forces, dynamic vs. static.

**Logic**:
1. Mean per-element tension scores.
2. `GENERATES_TENSION` edge bonus: each such edge in the graph adds up to +0.20 total.
3. Balance contribution: `+0.15 × max(0, 0.5 − balance)`. Low balance → higher perceived tension (Arnheim: off-balance compositions exert visual forces).
4. Order contribution: `+0.05` if `0.2 < order < 0.6`. Moderate order provides enough structure for tension to read as intentional rather than chaotic.

**Reads from context**: `order`, `balance`
**Writes to context**: `tension`

**Inter-module motivation**: Arnheim's key insight is that tension and balance are not opposites but can coexist. A composition that is slightly off-balance with strong directional lines achieves "dynamic equilibrium" — balanced expressiveness. The TensionModule encodes this by reading balance context and applying a graduated penalty.

---

### ClosureModule (k=9)

**Dimension**: closure — Gestalt completion demand.

**Logic**:
1. Mean per-element closure scores.
2. `closure_gap` facts add up to +0.20 total.
3. `figure_ground_ambiguity` facts add up to +0.15 total.
4. Implicit closure: `+0.1 × max(0, complexity − order)`. Compositions that are complex but not ordered leave more forms visually open, increasing the viewer's Gestalt completion work.

**Reads from context**: `complexity`, `order`
**Writes to context**: `closure`

**Inter-module motivation**: closure demand is not simply a function of the image's edges; it depends on how much structure the viewer has available to complete the forms. High order provides scaffolding that reduces the ambiguity; high complexity without order creates many unresolved contours.

---

### RhythmModule (k=10)

**Dimension**: rhythm — temporal pacing (0 for static inputs).

**Logic**:
1. Mean per-element rhythm scores (set by the multimedia extractor from inter-frame luminance differences; 0 for text/image/HTML extractors).
2. Repetition motif bonus: each `repetition`, `rhythm`, or `pattern` motif adds up to +0.20 total. This allows static compositions with strong visual repetition to register modest non-zero rhythm.

**Reads from context**: none
**Writes to context**: `rhythm`

---

## Context dict contract

| Key | Written by | Read by |
|---|---|---|
| `"complexity"` | `ComplexityModule` | `OrderModule`, `DensityModule`, `ClosureModule` |
| `"hue_coherence"` | `HueCoherenceModule` | `SaturationModule`, `ColorHarmonyModule` |
| `"order"` | `OrderModule` | `BalanceModule`, `TensionModule`, `ClosureModule` |
| `"balance"` | `BalanceModule` | `TensionModule` |
| `"density"` | `DensityModule` | (available; not currently read downstream) |
| `"saturation"` | `SaturationModule` | `ColorHarmonyModule` |
| `"contrast"` | `ContrastModule` | (available; not currently read downstream) |
| `"color_harmony"` | `ColorHarmonyModule` | (available; not currently read downstream) |
| `"tension"` | `TensionModule` | (available; not currently read downstream) |
| `"closure"` | `ClosureModule` | (available; not currently read downstream) |
| `"rhythm"` | `RhythmModule` | (available; not currently read downstream) |

---

## AestheticVector output format

```python
class DimensionScore(BaseModel):
    value:       float   # ∈ [-1, 1], final adjusted score
    confidence:  float   # ∈ [0, 1], mean of per-element confidences
    direction:   Literal["dominant", "present", "trace", "absent"]
    explanation: str | None
```

Direction thresholds applied by `_direction(v)`: `dominant` ≥ 0.65, `present` ≥ 0.35, `trace` ≥ 0.10, `absent` < 0.10.

---

## Adding a new aesthetic module

1. Create `am_dag/modules/my_module.py` with `evaluate(ir, ctx) -> DimensionScore`.
2. Add `("my_dimension", my_module.evaluate)` to `_MODULE_ORDER` in `am_dag/dag.py` at the correct topological position.
3. Add the dimension name to `AESTHETIC_DIMENSIONS` in `ir/schemas.py` and add the corresponding field to `AestheticVector`.
4. Add the key to the context dict contract above.
5. Add a test in `tests/test_am_dag.py`.
