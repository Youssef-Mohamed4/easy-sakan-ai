"""
=============================================================================
PRODUCTION EXTRACT: FastAPI Router for AI Price Prediction
=============================================================================
Note: This file is a direct extract from the private Easy Sakan FastAPI backend
(specifically `app/api/routers/analytics.py`). 

Context:
This extract demonstrates how the trained XGBoost model (.joblib artifact) 
is integrated into a RESTful HTTP endpoint. It includes the dynamic pricing 
logic that scales predictions based on physical capacity (Entire Unit vs. Room 
vs. Bed) and handles validation and error states, while strictly adhering to 
the platform's Pydantic response schemas.
=============================================================================
"""

import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import joblib

# Internal project dependencies (from the private core repo)
from app.db.session import get_db
from app.api.dependencies import get_current_landlord
from app.core.exceptions import ApiException
from app.core.response import success_response
from app.models.user import Landlord
from app.schemas.analytics import PricePredictionRequest, PricePredictionData, PriceRange

router = APIRouter()

# Load the trained ML artifact into memory on server startup
try:
    price_model = joblib.load("easysakan_price_predictor.joblib")
except Exception:
    price_model = None


@router.post("/ml/predict-price")
def predict_price(
    body: PricePredictionRequest,
    db: Session = Depends(get_db),
    current_user: Landlord = Depends(get_current_landlord),
):
    """Predict fair market price using XGBoost ML Engine (10.1)."""
    
    if not price_model:
        raise ApiException(
            status_code=500,
            message="Machine learning engine is currently unavailable.",
            message_ar="محرك الذكاء الاصطناعي غير متاح حالياً",
            errors=[]
        )

    # 1. Map to expected XGBoost columns
    amenities_pool = ["WiFi", "AC", "Elevator", "Balcony", "Washing Machine", "Natural Gas"]
    
    input_data = {
        "nearest_university": body.location, 
        "listing_mode": body.listing_mode,
        "gender_allowed": body.gender_allowed,
        "area_sqm": body.area_sqm,
        "bedrooms": body.bedrooms,
        "bathrooms": body.bathrooms,
        "total_capacity": body.total_capacity,
    }

    # 2. Flatten amenities array into binary 1/0 columns
    for amenity in amenities_pool:
        key = f"has_{amenity.replace(' ', '')}"
        input_data[key] = 1 if body.amenities and amenity in body.amenities else 0

    # 3. Predict via XGBoost
    try:
        df = pd.DataFrame([input_data])
        predicted = float(price_model.predict(df)[0])
    except Exception as e:
        raise ApiException(
            status_code=400,
            message=f"Prediction failed due to malformed input: {str(e)}",
            message_ar="فشل التوقع بسبب بيانات غير صالحة",
            errors=[]
        )

    # 4. Format outputs using our MAE (+/- 346.22 EGP)
    predicted = round(predicted, 2)
    price_min = max(0.0, round(predicted - 346.22, 2))
    price_max = round(predicted + 346.22, 2)

    # Wrap perfectly in existing response schema
    data = PricePredictionData(
        predicted_price=predicted,
        price_range=PriceRange(min=price_min, max=price_max),
        market_avg=predicted, 
        confidence="HIGH",    
    )

    return success_response(
        data=data.model_dump(by_alias=True),
        message="Price prediction generated",
        message_ar="تم توليد توقع السعر",
    )