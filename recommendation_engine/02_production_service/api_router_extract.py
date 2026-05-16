"""
=============================================================================
PRODUCTION EXTRACT: FastAPI Router for Recommendation Engine
=============================================================================
Note: This file is a direct extract from the private Easy Sakan FastAPI backend
(specifically `app/api/routers/analytics.py`). 

Context:
This extract demonstrates how the pure-Python recommendation service is exposed 
to the frontend via a RESTful HTTP endpoint. It handles pagination, extracts 
the student's identity from the JWT token via dependency injection, and wraps 
the mathematical similarity results in the platform's standard JSON success envelope.
=============================================================================
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

# Internal project dependencies (from the private core repo)
from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.services.recommendation_service import get_content_based_recommendations

router = APIRouter()

@router.get("/properties/recommended")
def get_recommended_properties(
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=20, description="Items per page"),
    basedOn: str = Query("views", description="views, saves, or bookings"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user) # Gatekeeper ensures user is authenticated
):
    # Call the lightweight ML service
    result_data = get_content_based_recommendations(
        db=db,
        student_id=current_user.id,
        based_on=basedOn,
        page=page,
        page_size=pageSize
    )

    # Wrap in the Standard Success Response Envelope
    return {
        "isSuccess": True,
        "message": "Recommended properties fetched",
        "messageAr": "تم جلب التوصيات بنجاح",
        "data": result_data,
        "errors": [],
        "statusCode": 200,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }