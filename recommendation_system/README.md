# Recommendation System

A content-based filtering engine that recommends student apartments based on price, location (nearest university), area, and amenities.

## How It Works

The model represents each apartment as a numeric vector and uses **cosine similarity** to find the most similar listings to a given target property.

### Pipeline

```
Raw CSV Data
    │
    ▼
Feature Engineering
    ├── Price & Area       → MinMax scaled to [0, 1]
    ├── Nearest University → One-hot encoded
    └── Amenities          → Multi-label binarized
    │
    ▼
Weighted Feature Matrix
    ├── price_scaled  × 2.0   (highest priority)
    ├── univ_*        × 1.5   (strong location signal)
    ├── amenities_*   × 1.0   (standard)
    └── area_scaled   × 0.5   (minor influence)
    │
    ▼
Cosine Similarity Matrix  (100 × 100)
    │
    ▼
get_recommendations(target_id, top_n)
```

### Why Cosine Similarity?

It measures the **angle** between two feature vectors rather than their magnitude, so a large apartment and a small one can still match perfectly if their relative feature profiles are aligned. This works well for mixed numeric/binary feature spaces.

## Files

| File | Description |
|---|---|
| `generate_data.py` | Generates `mock_properties.csv` with 100 synthetic listings |
| `mock_properties.csv` | Mock dataset (100 apartments, 7 columns) |
| `recommender.py` | Core model — feature engineering, similarity matrix, recommendation function, and metrics |

## Usage

**Step 1 — Generate (or replace) the dataset:**
```bash
python generate_data.py
```

**Step 2 — Run the recommender:**
```bash
python recommender.py
```

This will print:
- The target property's details
- Top 5 most similar listings with match scores
- System metrics (latency, catalog coverage, diversity)

**To query a different property**, change `target_property_id` at the bottom of `recommender.py`:
```python
target_property_id = 42  # any id from 1–100
```

## Tuning the Weights

The weights in `recommender.py` control how much each feature group influences the final score. Edit these lines to reprioritize:

```python
feature_matrix = pd.concat([
    df[['price_scaled']] * 2.0,   # ← increase to make price dominate
    df[['area_scaled']]  * 0.5,   # ← increase to surface larger units
    univ_dummies         * 1.5,   # ← high value keeps results near same university
    amenities_encoded    * 1.0,
], axis=1)
```

## Metrics

The script measures three things automatically at runtime:

| Metric | Recorded value | What it means |
|---|---|---|
| **Execution Time** | 0.0020s | Well under the 0.01s target for 100 listings — will scale comfortably to larger catalogs |
| **Catalog Coverage** | 100% (100/100) | Every listing in the dataset appears in at least one recommendation list — no popularity bias |
| **Intra-List Diversity** | ±1238.92 EGP | Healthy spread; the model is not surfacing near-identical price clones |

## Dataset Schema

| Column | Type | Description |
|---|---|---|
| `id` | int | Unique listing identifier |
| `title` | string | Display name |
| `price` | int | Monthly rent in EGP |
| `nearest_university` | string | One of 5 Cairo universities |
| `bedrooms` | int | 1–3 |
| `area_sqm` | int | 50–150 m² |
| `amenities` | JSON array | Subset of 8 possible amenities |