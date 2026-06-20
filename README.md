# Easy-Sakan-AI

AI features for the Easy-Sakan student housing platform.

## Structure

```
easy-sakan-ai/
├── price_predictor/
│   ├── 01_research_and_prototyping/
│   │   ├── generate_data.py                  # Generates 5000-property physically chained mock dataset
│   │   ├── predictor.py                      # Trains XGBoost model, prints metrics & exports .joblib artifact
│   │   └── student_housing_train.csv         # Generated training dataset (auto-overwritten on re-run)
│   ├── 02_production_service/
│   │   ├── easysakan_price_predictor.joblib  # Serialized trained model binary (copied to backend root)
│   │   └── api_router_extract.py             # FastAPI POST /ml/predict-price router reference
│   └── README.md
├── recommendation_engine/
│   ├── 01_research_and_prototyping/
│   │   ├── generate_data.py                  # Generates student-property interaction dataset
│   │   ├── recommender.py                    # Implements cosine similarity pipeline & evaluates output
│   │   └── student_housing_data.csv          # Generated interaction dataset (auto-overwritten on re-run)
│   ├── 02_production_service/
│   │   ├── recommendation_service.py         # Pure-Python engine deployed into backend/app/services/
│   │   └── api_router_extract.py             # FastAPI GET /properties/recommended router reference
│   └── README.md
├── requirements.txt
└── README.md
```

Each subdirectory is a self-contained AI module. New models will be added here as separate folders.

## Modules

| Module | Description | Status |
|---|---|---|
| [`recommendation_engine`](./recommendation_engine/README.md) | Content-based filtering — recommends similar apartments using cosine similarity on price, location, area, and amenities. | ✅ Ready |
| [`price_predictor`](./price_predictor/README.md) | XGBoost regression engine — predicts fair market rent dynamically based on capacity, location, and physical properties. | ✅ Ready |

## Setup

Install all dependencies for every module from the root:

```bash
pip install -r requirements.txt
```

Then navigate into any module and follow its own README for usage instructions.