# Easy-Sakan-AI

AI features for the Easy-Sakan student housing platform.

## Structure

```
easy-sakan-ai/
├── recommendation_engine/
│   ├── 01_research_and_prototyping/
│   │   ├── generate_data.py
│   │   ├── mock_properties.csv
│   │   └── recommender.py
│   ├── 02_production_service/
│   │   ├── recommendation_service.py
│   │   └── api_router_extract.py
│   └── README.md
├── requirements.txt
└── README.md
```

Each subdirectory is a self-contained AI module. New models will be added here as separate folders.

## Modules

| Module | Description | Status |
|---|---|---|
| [`recommendation_engine`](./recommendation_engine/README.md) | Content-based filtering — recommends similar apartments using cosine similarity on price, location, area, and amenities. Includes research prototype and production FastAPI service. | ✅ Ready |

## Setup

Install all dependencies for every module from the root:

```bash
pip install -r requirements.txt
```

Then navigate into any module and follow its own README for usage instructions.