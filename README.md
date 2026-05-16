# Easy-Sakan-AI

AI features for the Easy-Sakan student housing platform.

## Structure

```
easy-sakan-ai/
├── recommendation_system/   # Content-based apartment recommender
│   ├── generate_data.py
│   ├── mock_properties.csv
│   ├── recommender.py
│   └── README.md
├── requirements.txt
└── README.md
```

Each subdirectory is a self-contained AI module. New models will be added here as separate folders.

## Modules

| Module | Description | Status |
|---|---|---|
| [`recommendation_system`](./recommendation_system/README.md) | Content-based filtering — recommends similar apartments using cosine similarity on price, location, area, and amenities | ✅ Ready |

## Setup

Install all dependencies for every module from the root:

```bash
pip install -r requirements.txt
```

Then navigate into any module and follow its own README for usage instructions.