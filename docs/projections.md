# Aesthetic Projections

`src/aesthetic_compiler/projections/`

A projection is an aesthetic theory analyser. It reads the fully-assembled `AestheticIR` and emits a `ProjectionResult` expressing what that specific theory says about the work's harmony. The compiler ships four projections grounded in foundational aesthetic scholarship. Any subset may be selected at compile time via `--projection`.

---

## Architecture

```python
class BaseProjection(ABC):
    projection_id: str

    @abstractmethod
    def run(self, ir: AestheticIR) -> ProjectionResult: ...

class ProjectionResult(BaseModel):
    projection_id: str
    verdict:       str
    polarity:      Literal["harmonious", "neutral", "discordant"]
    findings:      list[AestheticFinding]
    score:         float   # ∈ [-1, 1]
    explanation:   str | None
```

---

## Selecting projections at compile time

```bash
# All four (default)
aesthetic-compile compile artwork.txt

# Two projections
aesthetic-compile compile artwork.jpg --projection birkhoff,arnheim

# One projection
aesthetic-compile compile design.html --projection gestalt
```

---

## `BirkhoffProjection`

**ID**: `birkhoff`
**File**: `projections/birkhoff.py`

**Theoretical basis**: George David Birkhoff (1933), *Aesthetic Measure*. Birkhoff proposed that aesthetic value M is determined by the ratio of order O to complexity C: M = O/C. Compositions with higher order relative to complexity are perceived as more aesthetically pleasing. The compiler uses the log-normalised form M = log(1+O)/(1+C) to prevent unbounded values and to model the diminishing returns on order noted by later researchers.

**Algorithm**:

1. Retrieve `order = ir.aggregate_aesthetic_vector.order.value` and `complexity = ir.aggregate_aesthetic_vector.complexity.value`.
2. Compute `M = log(1.0 + order) / (1.0 + complexity)`.
3. Normalise: `M_norm = min(1.0, M / log(2))` — maps the maximal theoretical value (order=1, complexity=0) to 1.0.
4. Emit findings for order deficit (`order < 0.7`), complexity excess (`complexity > 0.6`), and the raw M value.

**Verdict mapping**:

| M_norm | Verdict | Polarity |
|---|---|---|
| ≥ 0.65 | `high_aesthetic_measure` | `harmonious` |
| ≥ 0.40 | `moderate_aesthetic_measure` | `neutral` |
| ≥ 0.20 | `low_aesthetic_measure` | `neutral` |
| < 0.20 | `complexity_dominated` | `discordant` |

**Limitations acknowledged**: Birkhoff's formula reduces aesthetic value to a single ratio and does not account for semantic content, cultural context, or the viewer's prior exposure. A pure-white canvas scores maximally (complexity=0, any order) but would not be considered aesthetically meritorious. The projection is most informative as one input among four, not as a standalone quality metric.

---

## `ArnheimProjection`

**ID**: `arnheim`
**File**: `projections/arnheim.py`

**Theoretical basis**: Rudolf Arnheim (1954), *Art and Visual Perception*. Arnheim argued that visual compositions exert spatial forces — every element has visual weight determined by its size, darkness, saturation, and position — and that compositional balance is achieved when these forces are in equilibrium. He distinguished static equilibrium (a centred, symmetrical composition at rest) from dynamic equilibrium (an asymmetric composition that achieves balance through the counterplay of opposed forces). Both are aesthetically valid; the difference is expressive character.

**Algorithm**:

1. Retrieve `balance = ir.aggregate_aesthetic_vector.balance.value` and `tension = ir.aggregate_aesthetic_vector.tension.value`.
2. Balance analysis:
   - `balance ≥ 0.7`: spatial equilibrium achieved.
   - `0.4 ≤ balance < 0.7`: dynamic balance (Arnheim's "active equilibrium").
   - `balance < 0.4`: visual imbalance without resolution.
3. Tension analysis:
   - `tension ≥ 0.65`: dominant directional forces (centrifugal composition).
   - `0.35 ≤ tension < 0.65`: moderate dynamism.
   - `tension < 0.35`: static, restful composition.
4. Arnheim ideal detection: if `balance ≥ 0.6` and `tension ≥ 0.4`, emit `arnheim_ideal` finding — balanced composition with expressive tension.
5. Aggregate score: `balance × 0.6 + (1.0 − |tension − 0.35|) × 0.4`. This formula rewards balance heavily and rewards moderate tension over both extreme tension and complete stasis.

**Verdict mapping**:

| Score | Verdict | Polarity |
|---|---|---|
| ≥ 0.65 | `spatial_equilibrium` | `harmonious` |
| ≥ 0.45 | `dynamic_tension` | `harmonious` |
| ≥ 0.25 | `moderate_imbalance` | `neutral` |
| < 0.25 | `structural_discord` | `discordant` |

---

## `BerlyneProjection`

**ID**: `berlyne`
**File**: `projections/berlyne.py`

**Theoretical basis**: Daniel Berlyne (1971), *Aesthetics and Psychobiology*. Berlyne proposed that aesthetic preference follows an inverted-U function of arousal potential A: compositions with too little stimulation are perceived as boring; compositions with too much are perceived as aversive or overwhelming. The hedonic optimum lies at an intermediate arousal level that depends on the viewer's adaptation level. Berlyne identified complexity, novelty, incongruity, and uncertainty as the primary collative variables that drive arousal potential.

**Arousal potential weights**:

| Dimension | Weight |
|---|---|
| `complexity` | 0.30 |
| `contrast` | 0.25 |
| `tension` | 0.20 |
| `saturation` | 0.15 |
| `closure` | 0.10 |

**Algorithm**:

1. Compute `A = Σ weight_i × dimension_i.value` over the five dimensions above.
2. Compute hedonic value on the inverted-U: `H = 1.0 − (|A − 0.5| / 0.5)²`. This places the optimum at A=0.5 and maps the extremes (A=0 or A=1) to H=0.
3. Emit overarousal finding if `A > 0.75`; underarousal finding if `A < 0.20`.
4. Emit per-dimension arousal contribution findings for any dimension contributing > 0.1.

**Verdict mapping**:

| H | Condition | Verdict | Polarity |
|---|---|---|---|
| ≥ 0.65 | — | `optimal_arousal` | `harmonious` |
| ≥ 0.30 | — | `moderate_arousal` | `neutral` |
| < 0.30 | A > 0.5 | `overarousal_aversive` | `discordant` |
| < 0.30 | A ≤ 0.5 | `underarousal_boring` | `discordant` |

**Note on viewer-dependence**: Berlyne explicitly noted that the optimal arousal level shifts with adaptation. A viewer who regularly engages with complex contemporary art will have a higher optimal A than a viewer whose baseline is commercial photography. This projection uses a universal optimum of A=0.5; callers working with specific audience contexts may wish to adjust the `_OPTIMAL_AROUSAL` constant.

---

## `GestaltProjection`

**ID**: `gestalt`
**File**: `projections/gestalt.py`

**Theoretical basis**: Gestalt psychology (Wertheimer 1923, Köhler 1947). The Gestalt principles — proximity, similarity, continuity, closure, figure-ground — describe how the visual system organises elements into coherent wholes. A composition that supports strong Gestalt grouping, clear figure-ground separation, and satisfying closure reads as unified and complete. A composition that violates these principles reads as fragmented or unresolved.

**Algorithm**:

1. **Grouping strength**: count `GROUPED_WITH` edges in the `AestheticGraph`; divide by element count. Add a 0.30 baseline to prevent zero scores for compositions with no explicit grouping edges detected.
2. **Figure-ground clarity**: use `contrast` as a proxy — high contrast between foreground elements and background registers as clear figure-ground separation.
3. **Closure satisfaction**: `1.0 − closure × 0.7`. High closure demand (open, ambiguous contours) reduces satisfaction; some closure demand is acceptable (value 0.3 weight).
4. **Unity index**: `order × 0.4 + grouping × 0.3 + closure_satisfaction × 0.3`.
5. Detect `figure_ground_ambiguity` facts and apply a −0.2 penalty finding for each.
6. Aggregate score: `unity × 0.5 + fg_clarity × 0.3 + grouping × 0.2`.

**Verdict mapping**:

| Score | Verdict | Polarity |
|---|---|---|
| ≥ 0.65 | `gestalt_coherent` | `harmonious` |
| ≥ 0.45 | `partial_gestalt_unity` | `neutral` |
| ≥ 0.25 | `fragmented_composition` | `neutral` |
| < 0.25 | `gestalt_dissolution` | `discordant` |

---

## Cross-projection disagreement

When two or more active projections emit distinct non-neutral polarities, `ir.cross_projection_disagreement` is populated. The comparison is on **polarity** (`harmonious` vs. `discordant`); a `neutral` polarity is not a party to disagreement.

```python
{
  "verdicts":   {"birkhoff": "complexity_dominated", "arnheim": "spatial_equilibrium"},
  "polarities": {"birkhoff": "discordant",           "arnheim": "harmonious"},
  "note":       "Projections disagree on polarity. ..."
}
```

This structure makes it possible for a work to be simultaneously:
- **Birkhoff-discordant**: too complex relative to its order (the mathematical ratio is poor)
- **Arnheim-harmonious**: in spatial equilibrium with expressive tension
- **Berlyne-harmonious**: at the hedonic optimum arousal level
- **Gestalt-neutral**: partially unified but not fully coherent

...without the compiler forcing a resolution. Framework selection is the caller's responsibility.

---

## Adding a new projection

1. Create `projections/my_projection.py` with a class inheriting from `BaseProjection` and implementing `run(ir) -> ProjectionResult`.
2. Set `projection_id` to a snake_case string.
3. Add the ID to `ALL_PROJECTIONS` in `tiers.py`.
4. Register the instance in `_PROJECTION_REGISTRY` in `pipeline/orchestrator.py`.
5. Add tests in `tests/test_projections.py`.

The CLI's `--projection` flag accepts the new ID automatically once it is in `ALL_PROJECTIONS`.
