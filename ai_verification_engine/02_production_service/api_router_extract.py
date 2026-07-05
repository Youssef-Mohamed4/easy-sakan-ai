"""
=============================================================================
PRODUCTION EXTRACT: FastAPI Router for AI Verification Engine
=============================================================================
Note: This file is a direct extract from the private Easy Sakan FastAPI backend
(specifically `app/api/routers/auth.py`). 

Context:
This extract demonstrates how the multi-layered AI Document Verification 
pipeline (YOLOv8, Surya OCR, ELA, and Metadata analysis) is securely exposed 
to the frontend. It processes multipart form uploads, evaluates fraud vectors, 
executes logical cross-referencing on names, and routes suspicious documents 
to the Admin Dashboard (PENDING_REVIEW) while maintaining strict RESTful 
envelopes and a Fail-Closed security policy.
=============================================================================
"""

import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

# Internal project dependencies (from the private core repo)
from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.verification import VerificationDocument
from app.services.storage import upload_file
from app.services.document_ai_service import document_ai
from app.services.verification_logic import is_name_match
from app.core.response import success_response

router = APIRouter()

@router.post("/upload-verification")
def upload_verification(
    file_type: str = Form(..., alias="fileType"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a verification document with integrated AI Fraud Detection."""
    
    # 1. Validation & S3 Upload Logic Omitted for brevity in AI Repo Extract...
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    content = file.file.read()
    s3_key = f"mock_s3_url/docs/{current_user.id}/{file_type}.{ext}"
    
    # 2. AI Processing Pipeline
    temp_path = f"temp_doc_{current_user.id}.{ext}"
    with open(temp_path, "wb") as f:
        f.write(content)

    verification_status = "PENDING_REVIEW"
    fraud_score = None
    is_flagged = False
    ai_report = None

    try:
        if ext == "pdf":
            verification_status = "PENDING_REVIEW"
        else:
            ai_report = document_ai.process_document(temp_path)
            fraud_score = ai_report["metrics"]["forgery_score"]
            has_stamp = ai_report["metrics"]["has_official_stamp"]
            extracted_text = ai_report["extracted_data"]["raw_text"]
            has_face = ai_report["metrics"]["face_detected"]
            is_software_edited = ai_report["metrics"]["software_edited"]

            # --- CROSS-REFERENCE LOGIC ---
            name_match = False
            cross_check_done = False
            
            other_doc = db.query(VerificationDocument).filter(
                VerificationDocument.userId == current_user.id,
                VerificationDocument.fileType != file_type
            ).first()

            if other_doc and other_doc.aiAnalysis:
                cross_check_done = True
                other_ocr = other_doc.aiAnalysis["extracted_data"]["raw_text"]
                name_match = is_name_match(extracted_text, other_ocr)

            # --- FINAL ROUTING DECISION ---
            if is_software_edited:
                verification_status = "PENDING_REVIEW"
                is_flagged = True
            elif file_type in ["NationalID", "UniversityID"] and not has_face:
                verification_status = "PENDING_REVIEW"
                is_flagged = True
            elif fraud_score < 0.3:
                if file_type == "PropertyDeed" and not has_stamp:
                    verification_status = "PENDING_REVIEW"
                elif cross_check_done:
                    if name_match:
                        verification_status = "APPROVED"
                    else:
                        verification_status = "PENDING_REVIEW"
                else:
                    verification_status = "PENDING_REVIEW"
            elif fraud_score <= 0.7:
                verification_status = "PENDING_REVIEW"
            else:
                verification_status = "PENDING_REVIEW"
                is_flagged = True

    except Exception as e:
        print(f"\n[❌ AI PIPELINE CRASHED]: {e}\n")
        # CRITICAL SECURITY FIX: Fail-Closed Policy
        verification_status = "PENDING_REVIEW"
        is_flagged = True  
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # 3. Save to Database Logic Omitted...
    
    return success_response(data={"status": verification_status, "isFlagged": is_flagged}, message="Document processed")