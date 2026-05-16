"""
=============================================================================
PRODUCTION EXTRACT: FastAPI Router for Recommendation Engine
=============================================================================
Note: This file is a direct extract from the private Easy Sakan FastAPI backend
(specifically `app/api/routers/analytics.py`). 

Context:
This extract demonstrates how the pure-Python recommendation service is exposed 
to the frontend via a RESTful HTTP endpoint. It replaces a legacy Collaborative 
Filtering stub with the optimized Content-Based ML service, while strictly 
adhering to the platform's Pydantic response schemas and standard JSON envelopes.
=============================================================================
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

# Internal project dependencies (from the private core repo)
from app.db.session import get_db
from app.api.dependencies import get_current_student
from app.core.response import success_response
from app.models.user import Student
from app.schemas.analytics import PaginatedRecommendationsResponse
from app.services.recommendation_service import get_content_based_recommendations

router = APIRouter()

@router.get("/properties/recommended")
def get_recommended_properties(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=20, alias="pageSize"),
    based_on: str = Query("views", alias="basedOn"),
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """Get personalized property recommendations using ML Content-Based Filtering."""

    # Call the integrated Machine Learning service
    result_dict = get_content_based_recommendations(
        db=db,
        student_id=current_student.id,
        based_on=based_on,
        page=page,
        page_size=page_size
    )

    # Convert the raw dictionary from the service into the strict Pydantic response schema
    data = PaginatedRecommendationsResponse(**result_dict)

    return success_response(
        data=data.model_dump(by_alias=True),
        message="Recommended properties fetched",
        message_ar="تم جلب التوصيات",
    )