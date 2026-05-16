"""
=============================================================================
PRODUCTION EXTRACT: Lightweight Content-Based Recommendation Engine
=============================================================================
Note: This file is a direct extract from the private Easy Sakan FastAPI backend. 

Context:
After successfully prototyping the recommendation logic using Scikit-Learn and 
Pandas in the research phase, the algorithm was translated into this pure-Python 
service. This architectural pivot eliminated heavy ML dependencies from the 
deployment container, keeping the FastAPI Docker image lightweight and ensuring 
sub-5ms response times.

Dependencies like `app.models` refer to the SQLAlchemy ORM models in the 
private core repository.
=============================================================================
"""

import math
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.property import Property
from app.models.user_interaction import UserInteraction

def calculate_similarity(target: Property, candidate: Property, max_price: float) -> float:
    """Calculates a mathematical similarity score between 0.0 and 1.0."""
    score = 0.0
    
    # Tunable weights for the recommendation engine
    weights = {
        "price": 0.4,
        "university": 0.3,
        "amenities": 0.3
    }

    # 1. Price Similarity (Normalized)
    if max_price > 0 and target.price and candidate.price:
        price_diff = abs(float(target.price) - float(candidate.price)) / max_price
        score += weights["price"] * (1.0 - price_diff)

    # 2. Location / University Match
    if target.nearestUniversity and candidate.nearestUniversity:
        if target.nearestUniversity.lower() == candidate.nearestUniversity.lower():
            score += weights["university"]

    # 3. Amenities Overlap (Jaccard Similarity)
    # Safely handle JSON array parsing if they are stored as lists
    target_amenities = set(target.amenities) if target.amenities else set()
    candidate_amenities = set(candidate.amenities) if candidate.amenities else set()
    
    if target_amenities or candidate_amenities:
        intersection = len(target_amenities.intersection(candidate_amenities))
        union = len(target_amenities.union(candidate_amenities))
        score += weights["amenities"] * (intersection / union)

    return score

def get_content_based_recommendations(
    db: Session, student_id: int, based_on: str, page: int, page_size: int
) -> Dict[str, Any]:
    
    # 1. Find the user's most recent interaction (VIEW, SAVE, BOOKING)
    latest_interaction = db.query(UserInteraction).filter(
        UserInteraction.student_id == student_id,
        UserInteraction.interaction_type == based_on.upper()
    ).order_by(desc(UserInteraction.created_at)).first()

    target_property = None
    if latest_interaction:
        target_property = db.query(Property).filter(Property.id == latest_interaction.property_id).first()

    # 2. Fetch available candidates
    # Only recommend properties that are APPROVED and isAvailable = True
    query = db.query(Property).filter(
        Property.status == "APPROVED",
        Property.isAvailable == True
    )
    
    if target_property:
        query = query.filter(Property.id != target_property.id)
        
    candidates = query.all()

    if not candidates:
        return {"recommendations": [], "page": page, "pageSize": page_size, "totalPages": 0, "totalCount": 0}

    # 3. If no target property (cold start / brand new user), fallback to highest rated/newest
    if not target_property:
        candidates.sort(key=lambda x: x.createdAt, reverse=True)
        return _paginate_and_format(candidates, page, page_size, is_fallback=True)

    # 4. Score all candidates using pure-Python vector math
    max_price = max([float(p.price) for p in candidates if p.price] + [float(target_property.price or 0)])
    
    scored_candidates = []
    for candidate in candidates:
        score = calculate_similarity(target_property, candidate, max_price)
        scored_candidates.append({
            "property": candidate,
            "score": round(score, 3),
            "reason": f"Similar price range and location to your recent {based_on.lower()}s"
        })

    # 5. Sort by highest mathematical match
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)

    # 6. Paginate and map to exactly match Page 103 of the API Design
    total_count = len(scored_candidates)
    total_pages = math.ceil(total_count / page_size)
    start_idx = (page - 1) * page_size
    paginated_results = scored_candidates[start_idx : start_idx + page_size]

    recommendations = []
    for item in paginated_results:
        prop = item["property"]
        # Extract primary image URL safely
        images = prop.images if hasattr(prop, 'images') and prop.images else []
        primary_img = next((img.url for img in images if getattr(img, 'isPrimary', False)), "/img/placeholder.jpg")
        
        recommendations.append({
            "id": prop.id,
            "title": prop.title,
            "price": float(prop.price) if prop.price else 0.0,
            "location": {"address": prop.address},
            "images": [{"url": primary_img, "isPrimary": True}],
            "matchReason": item["reason"],
            "matchScore": item["score"]
        })

    return {
        "recommendations": recommendations,
        "page": page,
        "pageSize": page_size,
        "totalPages": total_pages,
        "totalCount": total_count
    }

def _paginate_and_format(properties: List[Property], page: int, page_size: int, is_fallback: bool) -> Dict[str, Any]:
    """Helper for formatting cold-start fallback properties."""
    total_count = len(properties)
    total_pages = math.ceil(total_count / page_size)
    start_idx = (page - 1) * page_size
    paginated_results = properties[start_idx : start_idx + page_size]

    recommendations = []
    for prop in paginated_results:
        images = prop.images if hasattr(prop, 'images') and prop.images else []
        primary_img = next((img.url for img in images if getattr(img, 'isPrimary', False)), "/img/placeholder.jpg")
        recommendations.append({
            "id": prop.id,
            "title": prop.title,
            "price": float(prop.price) if prop.price else 0.0,
            "location": {"address": prop.address},
            "images": [{"url": primary_img, "isPrimary": True}],
            "matchReason": "Popular on Easy Sakan right now" if is_fallback else "",
            "matchScore": 0.75
        })

    return {
        "recommendations": recommendations,
        "page": page,
        "pageSize": page_size,
        "totalPages": total_pages,
        "totalCount": total_count
    }