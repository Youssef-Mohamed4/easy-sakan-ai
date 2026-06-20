# AI Pricing Engine

An XGBoost-based regression engine that predicts fair market rent for student housing in Egypt. The model dynamically scales prices based on the physical capacity of the unit, the rental mode (Entire Unit, Room, or Bed), location multipliers, and specific amenities.

The engine went through two phases: an offline research and training pipeline, and a production-ready `.joblib` artifact integrated into the Easy Sakan FastAPI backend.

## How It Works

The system uses **XGBoost (Extreme Gradient Boosting)** to process non-linear relationships in the Egyptian real estate market, simulating the mental models and premium pricing floors used by actual landlords.

### Pipeline

```
Raw Physical Constraints
├── Bedrooms (1-4)
├── Total Capacity (scales with bedrooms)
└── Area (scales with bedrooms)
│
▼
Feature Engineering & Logic
├── Location           → Multiplier applied (e.g., AUC = 2.6x, Assiut = 0.9x)
├── Amenities          → Binary flags (AC, WiFi, Elevator, etc.)
└── Listing Mode       → Mathematical division based on capacity
│
▼
XGBoost Decision Trees
├── Handles premium floor thresholds (prevents "cheap" areas from hitting zero)
└── Absorbs ±12% realistic market noise
│
▼
predict_price()  → Outputs Fair Price + Confidence Range (Min/Max)
```

### Why XGBoost?

Unlike simple linear regression, XGBoost uses decision trees. If a landlord lists a high-density "Bed" in a premium area (like AUC) with AC and WiFi, XGBoost understands that the price will not drop linearly—landlords maintain a "premium floor." It captures human pricing behavior, not just raw calculator math.

---

## Structure

```
price_predictor/
├── 01_research_and_prototyping/   # Offline ML pipeline
│   ├── generate_data.py
│   ├── predictor.py
│   └── student_housing_train.csv
└── 02_production_service/         # Exported artifact and FastAPI integration reference
    ├── easysakan_price_predictor.joblib
    └── api_router_extract.py
```

### Phase 01 — Training Pipeline

| File | Description |
|---|---|
| `generate_data.py` | Generates a perfectly chained, physically logical mock dataset of 5000 properties. |
| `student_housing_train.csv` | The generated dataset used for training. |
| `predictor.py` | Core ML script — loads data, trains the XGBoost model, prints evaluation metrics, and exports the `.joblib` artifact. |

### Phase 02 — Production Service

After training, the model is serialized into a `.joblib` artifact. This allows the FastAPI backend to load the "brain" into memory on startup without needing to retrain or store the dataset.

| File | Description |
|---|---|
| `easysakan_price_predictor.joblib` | The trained model binary. This file is copied to the root of the backend repository. |
| `api_router_extract.py` | FastAPI router reference showing the `POST /ml/predict-price` endpoint, input mapping, error handling, and MAE formatting. |

**Key differences from the prototype:**

| | Prototype (Training) | Production (FastAPI) |
|---|---|---|
| **Data Source** | 5000-row CSV file | Single JSON request payload |
| **Output** | `.joblib` file & Terminal metrics | JSON API response with `priceRange` |
| **Error Handling** | None | Graceful 500 degradation if model fails to load |
| **Auth** | None | JWT via `get_current_landlord` dependency |

---

## Usage

### Prototype & Retraining

**Step 1 — Generate new market data:**
```bash
python 01_research_and_prototyping/generate_data.py
```

**Step 2 — Train the model and generate a new artifact:**
```bash
python 01_research_and_prototyping/predictor.py
```

This will overwrite `easysakan_price_predictor.joblib`.

### Production API

The endpoint is mounted on the Easy Sakan FastAPI backend. Once the server is running and the `.joblib` file is in the root directory:

```bash
POST /api/ml/predict-price
```

Requires a valid Landlord JWT in the `Authorization` header. The router maps the JSON payload to Pandas columns, runs the XGBoost prediction, and formats the output using the model's known Mean Absolute Error (MAE) to provide a confidence interval.

## Metrics

Evaluated during the final training pipeline iteration:

| Metric | Recorded value | What it means |
|---|---|---|
| R-Squared ($R^2$) | 0.9803 | 98% of the rent price variance is perfectly explained by the model's features. Highly production-ready. |
| Mean Absolute Error | ± 346.22 EGP | The average margin of error. Captures the natural "human inconsistency" of landlords pricing identical units slightly differently. |

## Dataset Schema (Training)

| Column | Type | Description |
|---|---|---|
| `nearest_university` | string | University anchor point (determines base multiplier) |
| `listing_mode` | string | EntireUnit, Room, Bed |
| `area_sqm` | float | Physically chained to the number of bedrooms |
| `bedrooms` | int | 1–4 |
| `total_capacity` | int | Scales logically with bedrooms (e.g., 2 per room) |
| `has_[Amenity]` | int (0/1) | Flattened binary columns for specific amenities |
| `price` | float | Target variable. Contains ±12% simulated market noise |