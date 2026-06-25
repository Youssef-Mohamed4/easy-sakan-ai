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
envelopes and Pydantic schemas.
=============================================================================
"""

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

# Internal project dependencies (from the private core repo)
from app.core.exceptions import ApiException
from app.core.response import ApiError, success_response
from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.verification import VerificationDocument
from app.schemas.auth import UploadVerificationResponseData

# Storage and AI Services
from app.services.storage import upload_file
from app.services.document_ai_service import document_ai
from app.services.verification_logic import is_name_match

router = APIRouter()

# ── Constants ────────────────────────────────────────────────────────────
ALLOWED_DOC_EXTENSIONS = {"jpg", "jpeg", "png", "pdf"}
MAX_DOC_SIZE = 5 * 1024 * 1024  # 5 MB
VALID_FILE_TYPES = {"UniversityID", "AdmissionProof", "NationalID", "PropertyDeed"}


@router.post("/upload-verification")
def upload_verification(
    file_type: str = Form(..., alias="fileType"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a verification document with integrated AI Fraud Detection."""
    
    # 1. Validation 
    if file_type not in VALID_FILE_TYPES:
        raise ApiException(
            status_code=400,
            message=f"Invalid file type. Allowed: {', '.join(sorted(VALID_FILE_TYPES))}",
            message_ar="نوع الملف غير صالح",
            errors=[ApiError(field="fileType", message="Invalid file type", code="VALIDATION_ERROR")],
        )

    if not file.filename:
        raise ApiException(
            status_code=400,
            message="No file provided",
            message_ar="لم يتم توفير ملف",
            errors=[ApiError(field="file", message="No file", code="VALIDATION_ERROR")],
        )

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_DOC_EXTENSIONS:
        raise ApiException(
            status_code=400,
            message="File type not supported. Allowed: jpg, jpeg, png, pdf",
            message_ar="نوع الملف غير مدعوم. المسموح به: jpg, jpeg, png, pdf",
            errors=[ApiError(field="file", message="Unsupported file type", code="INVALID_FILE_TYPE")],
        )

    content = file.file.read()
    if len(content) > MAX_DOC_SIZE:
        raise ApiException(
            status_code=400,
            message="File size exceeds 5MB limit",
            message_ar="حجم الملف يتجاوز الحد المسموح 5 ميجابايت",
            errors=[ApiError(field="file", message="File too large", code="VALIDATION_ERROR")],
        )

    # 2. Upload to S3 (Secure/Private)
    folder = f"docs/{current_user.id}"
    s3_key = upload_file(
        file_content=content,
        folder=folder,
        original_filename=f"{file_type}_{current_user.id}.{ext}",
        content_type=file.content_type or "application/octet-stream",
        public=False,
    )

    if not s3_key:
        raise ApiException(
            status_code=500,
            message="Failed to upload file. Please try again.",
            message_ar="فشل رفع الملف. يرجى المحاولة مرة أخرى.",
            errors=[ApiError(field="file", message="Upload failed", code="INTERNAL_ERROR")],
        )

    # 3. AI Processing Pipeline
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
                print(f"🤝 Cross-Check Done against {other_doc.fileType}! Name Match? {name_match}")
            else:
                print("⚠️ First document uploaded. Waiting for second document to cross-check names.")

            # --- FINAL ROUTING DECISION ---
            if fraud_score < 0.3:
                if file_type == "PropertyDeed" and not has_stamp:
                    verification_status = "PENDING_REVIEW"
                    print("❌ Routing: PENDING_REVIEW (Property Deed missing official stamp)")
                elif cross_check_done:
                    if name_match:
                        verification_status = "APPROVED"
                        print("✅ Routing: APPROVED (Cross-check passed, names match)")
                    else:
                        verification_status = "PENDING_REVIEW"
                        if file_type == "PropertyDeed":
                            print("✍️ Routing: PENDING_REVIEW (Contract name could not be auto-verified - likely handwritten)")
                        else:
                            print("⚠️ Routing: PENDING_REVIEW (Cross-check failed, names do not match)")
                else:
                    verification_status = "PENDING_REVIEW"
                    print("⏳ Routing: PENDING_REVIEW (Awaiting second document for cross-check)")
            
            elif fraud_score <= 0.7:
                verification_status = "PENDING_REVIEW"
                print("⚠️ Routing: PENDING_REVIEW (Fraud score is elevated)")
                
            else:
                verification_status = "PENDING_REVIEW"
                is_flagged = True
                print("🚨 Routing: FLAGGED FORGERY (Fraud score exceeded 0.7!)")

    except Exception as e:
        print(f"\n[❌ AI PIPELINE CRASHED]: {e}\n")
        verification_status = "PENDING_REVIEW"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # 4. Save to Database
    if verification_status == "APPROVED" and cross_check_done and name_match:
        current_user.isVerified = True
        db.commit()

    now = datetime.now(timezone.utc)
    doc = VerificationDocument(
        userId=current_user.id,
        fileType=file_type,
        documentUrl=s3_key,
        status=verification_status,
        fraudScore=fraud_score,       # Saved for Admin Panel
        isFlagged=is_flagged,         # Saved for Admin Panel
        aiAnalysis=ai_report,         # Saved for Admin Panel debugging
        uploadedAt=now,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 5. Dynamic API Response
    response_msg = "Document uploaded. Waiting for Admin approval."
    response_msg_ar = "تم رفع المستند. في انتظار موافقة المسؤول."
    
    if verification_status == "APPROVED":
        response_msg = "Document verified successfully. Account approved."
        response_msg_ar = "تم توثيق المستند بنجاح. تمت الموافقة على الحساب."

    data = UploadVerificationResponseData(
        user_id=current_user.id,
        document_id=doc.id,
        file_type=file_type,
        document_url=s3_key,
        verification_status=verification_status,
        uploaded_at=now.isoformat().replace("+00:00", "Z"),
    )

    return success_response(
        data=data.model_dump(by_alias=True),
        message=response_msg,
        message_ar=response_msg_ar,
    )