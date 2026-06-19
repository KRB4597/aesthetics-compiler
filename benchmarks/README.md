# Benchmarks — does the compiler agree with human taste?

This directory is a standalone evaluation layer. It does **not** change the
compiler; it measures it. The question it answers:

> When the compiler says one image is more *balanced* / *color-harmonious* /
> *ordered* than another, do **humans** agree?

It answers that by running the compiler over a labeled image set and computing
the **Spearman rank correlation** between each predicted dimension and the
matching human attribute. (See `metrics.py` for what Spearman means — short
version: +1 = perfect agreement, 0 = no relationship, −1 = backwards.)

## Quick start (no download needed)

```bash
pip install -e .          # installs the compiler + Pillow
python -m benchmarks.run_aadb
```

This generates six tiny synthetic images and runs the whole pipeline on them.
It exists to prove the harness works — **the numbers are not meaningful** with
only six made-up labels. For a real evaluation, use AADB below.

## Real evaluation with AADB

[AADB](https://github.com/aimerykong/deepImageAestheticsAnalysis) (Kong et al.,
*Photo Aesthetics Ranking Network with Attributes and Content Adaptation*,
ECCV 2016) has 10,000 photos, each with an overall aesthetic score and 11
human attribute scores. Several attributes map directly onto this compiler's
dimensions:

| compiler dimension | AADB attribute      |
|--------------------|---------------------|
| `balance`          | `balancing_element` |
| `color_harmony`    | `color_harmony`     |
| `order`            | `symmetry`          |
| `rhythm`           | `repetition`        |
| `saturation`       | `vivid_color`       |

(The mapping lives in `datasets.py::ATTRIBUTE_MAP` — edit it to add or change
pairings.)

### Steps

1. Download AADB (images + attribute labels) from the link above.
2. Build a CSV with a header row and these columns (include whichever
   attributes you have; `overall` is the mean aesthetic score):

   ```csv
   image,overall,balancing_element,color_harmony,symmetry,repetition,vivid_color
   /data/aadb/farm1_1.jpg,0.71,0.6,0.8,0.4,0.2,0.7
   /data/aadb/farm1_2.jpg,0.33,0.2,0.3,0.1,0.1,0.5
   ```

   Image paths may be absolute or relative to the CSV's location.
3. Run it:

   ```bash
   python -m benchmarks.run_aadb --data /data/aadb/labels.csv
   # optionally cap the run while iterating:
   python -m benchmarks.run_aadb --data /data/aadb/labels.csv --limit 1000
   ```

## Reading the output

```
compiler dimension  vs AADB attribute        n   Spearman  strength
----------------------------------------------------------------
balance             balancing_element     1000     +0.41   moderate
color_harmony       color_harmony         1000     +0.55   strong
...
```

- **n** — how many images had that attribute labeled.
- **Spearman** — the agreement score. Positive and large is good.
- A **negative** value is a warning sign: the compiler may have that dimension
  inverted relative to how humans use it.
- **n/a** means the compiler produced a constant value for that dimension
  across all images (no variation to correlate) — itself a useful finding.

## Files

| file            | purpose                                                        |
|-----------------|----------------------------------------------------------------|
| `metrics.py`    | Spearman / Pearson / MAE in pure Python (no extra deps).       |
| `datasets.py`   | CSV loader + bundled synthetic-sample generator.               |
| `run_aadb.py`   | The runner described above.                                    |
| `sample_data/`  | Auto-generated on first run; safe to delete.                   |

## Other datasets

The same `run_aadb.py` works with **AVA** (Murray et al., CVPR 2012, ~250k
images) if you export an `image,overall` CSV — you just won't have the
attribute columns, so only the overall-score row will be populated.
