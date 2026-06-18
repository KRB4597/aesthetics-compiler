# Extraction Tiers and Vocabulary

`src/aesthetics_compiler/annotation/` and `src/aesthetics_compiler/ingestion/`

The extraction subsystem transforms a raw source into the flat IR objects — `AestheticElement`, `CompositionZone`, `ColorScheme`, `VisualMotif`, `AestheticFact` — that Pass 7.5 promotes into the `AestheticGraph`. There are four extraction tiers, one per input mode, plus a Mock tier for testing. All tiers produce the same schema.

---

## Tier selection

| Tier | Input mode | Class | File |
|---|---|---|---|
| Rule (Tier 1) | `text` | `RuleExtractor` | `annotation/rule_extractor.py` |
| Image (Tier 2) | `image` | `ImageExtractor` | `annotation/image_extractor.py` |
| HTML (Tier 3) | `html` | `HtmlExtractor` | `annotation/html_extractor.py` |
| Multimedia (Tier 4) | `multimedia` | `MultimediaExtractor` | `annotation/multimedia_extractor.py` |
| Mock (Tier 5) | testing | `MockExtractor` | `annotation/mock_extractor.py` |

`CompilerTier` and `InputMode` are both declared in `tiers.py`. `detect_input_mode(path)` maps file extensions to `InputMode` values; `--input-mode` overrides the detection.

---

## Tier 1: Rule extractor (text input)

`annotation/rule_extractor.py`

The rule extractor processes natural-language text by matching tokens against vocabulary tables, detecting artist style names, and classifying the medium. The extraction is deliberately lightweight: it does not use a parser or tagger, so it remains dependency-free and deterministic.

### Vocabulary tables

Each vocabulary table maps token patterns to a score in `[-1, 1]` for one of the eleven dimensions. Tokens are lowercased and whitespace-normalised before matching. Matches are additive; the final score is clamped to `[-1, 1]`.

**`_COMPLEXITY_VOCAB`** — examples:

| Token | Score |
|---|---|
| `chaotic`, `cluttered`, `intricate` | +0.8 to +1.0 |
| `complex`, `dense pattern` | +0.5 to +0.7 |
| `simple`, `minimal`, `uncluttered` | −0.5 to −0.8 |
| `clean`, `sparse` | −0.3 to −0.5 |

**`_ORDER_VOCAB`** — examples:

| Token | Score |
|---|---|
| `grid`, `perfectly aligned`, `rigid structure` | +0.8 to +1.0 |
| `structured`, `regular`, `geometric` | +0.4 to +0.7 |
| `random`, `chaotic arrangement`, `disorder` | −0.6 to −0.9 |
| `asymmetric`, `irregular` | −0.2 to −0.5 |

**`_BALANCE_VOCAB`** — examples:

| Token | Score |
|---|---|
| `balanced`, `symmetric`, `harmonious arrangement` | +0.7 to +1.0 |
| `centered`, `stable` | +0.3 to +0.6 |
| `off-balance`, `unbalanced`, `lopsided` | −0.5 to −0.8 |

**`_DENSITY_VOCAB`** — examples:

| Token | Score |
|---|---|
| `filled`, `dense`, `packed`, `heavy` | +0.6 to +0.9 |
| `empty`, `sparse`, `negative space`, `void` | −0.4 to −0.7 |

**`_HUE_COHERENCE_VOCAB`** — examples:

| Token | Score |
|---|---|
| `monochromatic`, `single hue`, `limited palette` | +0.8 to +1.0 |
| `analogous`, `harmonious palette` | +0.4 to +0.7 |
| `polychromatic`, `many colors`, `rainbow`, `chaotic palette` | −0.4 to −0.7 |

**`_SATURATION_VOCAB`** — examples:

| Token | Score |
|---|---|
| `vibrant`, `saturated`, `vivid`, `intense color` | +0.7 to +1.0 |
| `muted`, `subdued`, `desaturated`, `dull` | −0.4 to −0.7 |
| `pastel`, `soft` | −0.1 to −0.3 |

**`_CONTRAST_VOCAB`** — examples:

| Token | Score |
|---|---|
| `high contrast`, `stark`, `black and white` | +0.8 to +1.0 |
| `contrasty`, `sharp edges` | +0.4 to +0.6 |
| `low contrast`, `subtle`, `soft` | −0.3 to −0.6 |
| `blurry edges`, `sfumato` | −0.4 to −0.5 |

**`_COLOR_HARMONY_VOCAB`** — examples:

| Token | Score |
|---|---|
| `harmonious color`, `color chord`, `complementary` | +0.6 to +0.9 |
| `analogous colors` | +0.7 to +0.8 |
| `clashing`, `discordant colors`, `jarring` | −0.5 to −0.8 |

**`_TENSION_VOCAB`** — examples:

| Token | Score |
|---|---|
| `tension`, `dynamic`, `energetic`, `forceful` | +0.6 to +0.9 |
| `explosive`, `agitated`, `turbulent` | +0.7 to +1.0 |
| `calm`, `serene`, `meditative`, `still` | −0.5 to −0.8 |
| `peaceful`, `tranquil` | −0.3 to −0.5 |

**`_CLOSURE_VOCAB`** — examples:

| Token | Score |
|---|---|
| `incomplete`, `open form`, `ambiguous boundary` | +0.6 to +0.8 |
| `fragmented`, `broken` | +0.4 to +0.6 |
| `closed form`, `complete`, `well-defined boundary` | −0.4 to −0.6 |

**`_RHYTHM_VOCAB`** — examples:

| Token | Score |
|---|---|
| `rhythmic`, `pulsating`, `repetitive pattern`, `beat` | +0.6 to +0.9 |
| `visual rhythm`, `cadence`, `oscillating` | +0.4 to +0.7 |
| `static`, `frozen`, `no movement` | −0.3 to −0.5 |

### Artist style map

`ARTIST_STYLE_MAP` maps a normalised artist name to a pre-computed `AestheticVector` approximating the artist's characteristic style. The presence of an artist name overrides the vocabulary score for all dimensions simultaneously (using a weighted blend).

| Artist key | Notes |
|---|---|
| `rothko` | High balance, hue_coherence, color_harmony, density; low complexity, contrast; zero order |
| `mondrian` | High order, balance, color_harmony; moderate density; low complexity, tension |
| `pollock` | High complexity, rhythm; moderate tension; low order, balance |
| `kandinsky` | High tension, saturation, rhythm; moderate complexity; low order, balance |
| `monet` | Moderate hue_coherence, saturation; low contrast (sfumato), low order |
| `picasso` | High tension, complexity; moderate order (cubist structure); low balance |
| `vermeer` | High contrast, balance, closure; moderate order; low complexity |

### `_extract_elements(text)`

Scans text for colour mentions (regex matching `#[0-9a-fA-F]{3,6}`, named CSS colours, and natural-language colour adjectives). Each detected colour is wrapped in an `AestheticElement` with an estimated per-element `AestheticVector`. Colour adjectives (e.g. "bright red", "deep blue") contribute to saturation, hue_coherence, and contrast scores.

### `_detect_style(text)`

Matches lowercase text against `ARTIST_STYLE_MAP` keys. Returns the artist key if found, else `None`. Used to set `ir.document.artist`.

### `_detect_medium(text)`

Pattern-matches against a short `_MEDIUM_KEYWORDS` table: "oil", "watercolor", "acrylic", "digital", "photograph", "print". Returns the matched medium or `"unknown"`.

---

## Tier 2: Image extractor (image input)

`annotation/image_extractor.py` and `ingestion/image_loader.py`

### Image loading

`load_image(source) -> (pil_image, metadata, sha256)`

Loads with Pillow. If the source is a URL string, uses `urllib.request.urlopen`. `metadata` dict contains:

| Key | Contents |
|---|---|
| `arr` | uint8 NumPy array, shape (H, W, 3) |
| `lum` | luminance array, shape (H, W), float32, range [0, 1] |
| `hsv_h` | hue channel, shape (H, W), float32, range [0, 1] |
| `hsv_s` | saturation channel |
| `hsv_v` | value channel |
| `is_animated` | bool — True for multi-frame GIFs |
| `n_frames` | int |
| `duration_s` | float — total duration if animated, else 0 |

`_rgb_to_hsv_channels(arr)` is a pure NumPy implementation to avoid requiring `colorsys` to operate on full arrays.

### ImageExtractor dimension computations

| Dimension | Formula |
|---|---|
| k=0 complexity | `edge_density = sum(|grad_x| + |grad_y|) / (H×W×255)` where `grad_x/grad_y` are first-difference arrays; `value = min(1.0, edge_density × 2.5)` |
| k=1 order | Horizontal symmetry: flip image left-right, compute mean absolute difference of luminance arrays; vertical: flip top-bottom. `value = 1 − max(h_diff, v_diff)` |
| k=2 balance | Luminance-weighted center of mass `(cx, cy)`; deviation from `(W/2, H/2)` normalized to [0,1]; `value = 1 − deviation` |
| k=3 density | Count pixels with luminance < 0.9 (near-white = empty); `value = 1 − (near_white_count / total)` |
| k=4 hue_coherence | For pixels with `hsv_s > 0.15`: bin `hsv_h` into 18 buckets; Shannon entropy H_s; `value = 1 − (H_s / log(18))` |
| k=5 saturation | `value = mean(hsv_s)` over all pixels |
| k=6 contrast | Weber-Fechner: `lum_max = percentile(lum, 99)`, `lum_min = percentile(lum, 1)`; `value = log(lum_max / (lum_min + 1)) / log(255.0)` |
| k=7 color_harmony | `_color_harmony_score(hsv_h[hsv_s > 0.15])` — peak detection in the hue histogram; score mapped from `_HARMONY_SCORE_MAP` based on angular separations between peaks |
| k=8 tension | Compute `grad_x`, `grad_y`; diagonal energy = `sum(|grad_x| × |grad_y|)`; total energy = `sum(grad_x² + grad_y²)`; `value = diagonal_energy / (total_energy + ε)` |
| k=9 closure | If `scikit-image` available: `skimage.measure.label` on binary edge map; `value = min(1.0, n_open_regions / 20)`. Fallback: high contrast at image border → low closure demand |
| k=10 rhythm | `0.0` for static images |

### `_color_harmony_score(hue_samples)`

1. Bin into 36 buckets (10° each).
2. Find peaks above mean count.
3. Compute pairwise angular distances between peak centres.
4. Map to relationship type: single peak → monochromatic; spread ≤ 30° → analogous; spread ≈ 180° → complementary; three peaks ≈ 120° apart → triadic; four peaks ≈ 90° → tetradic; else polychromatic.
5. Return `_HARMONY_SCORE_MAP[relationship]`.

---

## Tier 3: HTML extractor (HTML input)

`annotation/html_extractor.py` and `ingestion/html_loader.py`

### HTML loading

`load_html(source) -> (raw_html, metadata, sha256)`. Uses stdlib `urllib.request` for URLs. `_StyleExtractor(HTMLParser)` accumulates inline styles and `<style>` blocks. Regex extraction:

- CSS hex colours: `#[0-9a-fA-F]{3,6}`
- CSS `rgb()` / `rgba()` values
- Background-color declarations
- Font-family declarations

### HtmlExtractor dimension computations

| Dimension | Source |
|---|---|
| k=0 complexity | `log(1 + element_count) / log(100)` — log-compressed DOM element count |
| k=1 order | Grid-related CSS keywords (`grid`, `flex`, `table`); returns moderate-high score if grid-based |
| k=2 balance | Paragraph and heading element ratio; symmetry of color count in left vs. right halves of the palette |
| k=3 density | Font sizes (large → denser); block vs. inline element ratio |
| k=4 hue_coherence | Count unique hue buckets across extracted CSS colors; entropy as in image extractor |
| k=5 saturation | Mean HSL saturation across extracted CSS colors |
| k=6 contrast | Luminance range across detected background-color and foreground-color values |
| k=7 color_harmony | Same peak detection on hue samples from CSS colors as image extractor |
| k=8 tension | CSS animation keywords, transform declarations |
| k=9 closure | Completeness of HTML structure (presence of `<html>`, `<head>`, `<body>`) as a proxy |
| k=10 rhythm | `0.0` — HTML documents are static |

**Helpers**:
- `_hex_to_rgb(hex_str) -> (r, g, b)` — converts 3- or 6-digit hex.
- `_rgb_to_hsl(r, g, b) -> (h, s, l)` — pure Python, no dependencies.

---

## Tier 4: Multimedia extractor (video/GIF input)

`annotation/multimedia_extractor.py` and `ingestion/multimedia_loader.py`

### Multimedia loading

`load_multimedia(source) -> (frames, metadata, sha256)`.

- Animated GIF: loaded with Pillow; each frame extracted as an RGB array.
- Video (`.mp4`, `.avi`, `.mov`): loaded with optional `imageio`; raises `ImportError` with installation instructions if absent.
- `_sample_indices(n_frames, max_frames=30)`: selects up to 30 evenly spaced frame indices.

`metadata` contains:

| Key | Contents |
|---|---|
| `n_frames` | total frame count |
| `sampled_frames` | list of sampled frame arrays |
| `fps` | frames per second (from imageio or GIF timing) |
| `duration_s` | total duration |
| `width`, `height` | pixel dimensions |

### MultimediaExtractor computations

For spatial dimensions (k=0–k=9): runs `ImageExtractor` on each sampled frame; returns the mean `DimensionScore.value` and `DimensionScore.confidence` across frames. This means a video that alternates between ordered and chaotic compositions will score in the moderate range — the correct behaviour given the extractor's spatial-static design.

**`_compute_rhythm(frames, fps) -> float`** (k=10):

1. Compute per-frame mean luminance as a 1-D signal.
2. Compute `mean_diff = mean(|lum[i+1] − lum[i]|)` over consecutive sampled frames.
3. `pacing_score = min(1.0, mean_diff × 2.5)` — high inter-frame luminance changes → high pacing.
4. `fps_score = min(1.0, fps / 60.0)` — higher frame rate = more potential temporal information.
5. `rhythm = pacing_score × 0.7 + fps_score × 0.3`.

This formula assigns primary weight to actual scene activity and secondary weight to the frame rate, on the basis that a 60fps static lockdown has lower expressive rhythm than a 24fps montage.

---

## Canonicalizer

`canonicalizer/registry.py` — Pass 7 (text input only)

The canonicalizer maps informal or variant phrases to canonical form before the graph is assembled. It does not alter the dimension scores; it normalises the element and motif names that appear in the graph nodes.

**`_ALIASES`** — selected examples:

| Raw form | Canonical |
|---|---|
| `colour field`, `colour-field` | `color_field` |
| `rothko style`, `rothko-like` | `rothko` |
| `mondrian style` | `mondrian` |
| `colour` | `color` |
| `centre` | `center` |
| `grey` | `gray` |
| `primary colour palette` | `primary_color_palette` |
| `sfumato`, `soft edges` | `low_contrast_edges` |
| `impasto`, `thick paint` | `high_texture` |

Canonicalization is case-insensitive and applied before graph promotion.

---

## Segmenter

`segmentation/segmenter.py` — Pass 1 (text input only)

The segmenter classifies paragraphs in the text into `Segment` objects with a `segment_type` label. The segmenter uses simple heuristics rather than a parser.

| Segment type | Heuristic |
|---|---|
| `color_description` | Paragraph contains ≥ 2 color mentions |
| `composition_description` | Contains spatial vocabulary (balance, arrangement, position, center, corner, …) |
| `style_reference` | Paragraph mentions an artist name or a named style period |
| `technical_description` | Contains medium or technique vocabulary (oil, fresco, brushstroke, glaze, …) |
| `general_description` | Default when none of the above match |

Segments are stored in `ir.segments` and are used by the rule extractor to weight per-segment scores before averaging.

---

## Adding vocabulary for a new dimension

1. Add the dimension to `AESTHETIC_DIMENSIONS` in `ir/schemas.py` and a field to `AestheticVector`.
2. Add the dimension to `_MODULE_ORDER` in `am_dag/dag.py`.
3. Add a `_MYDIM_VOCAB` dictionary to `annotation/rule_extractor.py` and call `_score_dimensions()` for it.
4. Add pixel-level or structural computation to `ImageExtractor._compute_scores()`, `HtmlExtractor._compute_scores()`, and `MultimediaExtractor._compute_scores()`.
5. Update the context dict contract in `docs/am_dag.md`.
