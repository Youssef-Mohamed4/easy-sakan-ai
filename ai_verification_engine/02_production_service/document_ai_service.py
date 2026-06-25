import os
import cv2
import numpy as np
from PIL import Image, ImageChops
from ultralytics import YOLO
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor

class DocumentVerificationService:
    def __init__(self):
        print("🧠 Booting Easy Sakan AI Engine...")
        # 1. Load Surya OCR (Will use shared ~/.cache so it loads instantly)
        self.det_predictor = DetectionPredictor()
        self.rec_predictor = RecognitionPredictor()
        
        # 2. Load Custom YOLO Stamp Detector
        # Get absolute path dynamically based on this file's location
        base_dir = os.path.dirname(os.path.abspath(__file__))
        weights_path = os.path.join(base_dir, "ai_weights", "stamp_detector.pt")
        self.stamp_model = YOLO(weights_path)
        
        print("✅ AI Engine Ready!")

    def deskew_image(self, img_path: str) -> str:
        """Fixes tilted images. Returns the path to the cleaned image."""
        img = Image.open(img_path).convert("RGB")
        bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
        
        if lines is not None:
            angles = [np.degrees(np.arctan2(l[0][3] - l[0][1], l[0][2] - l[0][0])) for l in lines]
            skew = float(np.median(angles)) - (round(float(np.median(angles)) / 90) * 90)
            if abs(skew) >= 0.5:
                h, w = bgr.shape[:2]
                M = cv2.getRotationMatrix2D((w / 2, h / 2), skew, 1.0)
                rotated = cv2.warpAffine(bgr, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                clean_img = Image.fromarray(cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB))
                
                clean_path = f"deskewed_{os.path.basename(img_path)}"
                clean_img.save(clean_path)
                return clean_path
        return img_path

    def run_ela_forgery_check(self, image_path: str) -> float:
        """Calculates pixel variance to detect Photoshop manipulation."""
        try:
            original = Image.open(image_path).convert('RGB')
            temp_path = f"temp_ela_{os.path.basename(image_path)}"
            original.save(temp_path, 'JPEG', quality=90)
            compressed = Image.open(temp_path)
            
            ela_image = ImageChops.difference(original, compressed)
            ela_array = np.array(ela_image)
            suspicion_score = float(np.var(ela_array) / 255.0)
            
            os.remove(temp_path)
            return suspicion_score
        except Exception:
            return 0.0

    def check_official_stamp(self, image_path: str) -> bool:
        """Uses custom YOLOv8 model to detect government stamps."""
        results = self.stamp_model.predict(image_path, conf=0.25, verbose=False)
        stamp_count = len(results[0].boxes)
        return stamp_count > 0

    def extract_arabic_text(self, image_path: str) -> str:
        """Runs Surya OCR to extract names and data."""
        try:
            img = Image.open(image_path)
            det_results = self.det_predictor([img])
            bboxes = [box.bbox for box in det_results[0].bboxes]
            
            if not bboxes: return ""
                
            rec_results = self.rec_predictor([img], bboxes=[bboxes])
            text_lines = [line.text for line in rec_results[0].text_lines if getattr(line, "confidence", 1.0) > 0.4]
            return "\n".join(text_lines)
        except Exception:
            return ""

    def check_exif_metadata(self, image_path: str) -> bool:
        """Checks hidden metadata for known editing software signatures."""
        try:
            from PIL import ExifTags
            img = Image.open(image_path)
            exif = img._getexif()
            if exif:
                for k, v in exif.items():
                    if k in ExifTags.TAGS and ExifTags.TAGS[k] == 'Software':
                        software = str(v).lower()
                        # List of common editing apps
                        suspicious_apps = ['picsart', 'photoshop', 'canva', 'samsung', 'snapseed', 'lightroom']
                        if any(app in software for app in suspicious_apps):
                            print(f"⚠️ Metadata Alert: Edited by {v}")
                            return True
            return False
        except Exception:
            return False

    def detect_human_face(self, image_path: str) -> bool:
        """Uses OpenCV Haar Cascades to verify a real human face exists (catches emojis)."""
        try:
            # Load OpenCV's built-in lightweight face detector
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces (scaleFactor 1.1, minNeighbors 4 are standard for IDs)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            # If it finds at least one face, return True
            return len(faces) > 0
        except Exception:
            # If it fails to run, assume True so we don't break the pipeline
            return True

    def process_document(self, uploaded_file_path: str) -> dict:
        """The Main Pipeline Endpoint"""
        clean_path = self.deskew_image(uploaded_file_path)
        
        forgery_score = self.run_ela_forgery_check(clean_path)
        has_stamp = self.check_official_stamp(clean_path)
        extracted_text = self.extract_arabic_text(clean_path)
        
        # --- NEW HACKS START HERE ---
        is_software_edited = self.check_exif_metadata(clean_path)
        has_face = self.detect_human_face(clean_path)
        # --- NEW HACKS END HERE ---
        
        if clean_path != uploaded_file_path and os.path.exists(clean_path):
            os.remove(clean_path)
            
        # Business Logic Rules:
        if is_software_edited:
            status = "REJECTED_FORGERY_DETECTED" # Caught by Metadata
            print("🚨 REJECTED: Editing software found in metadata!")
        elif not has_face:
            status = "REJECTED_FORGERY_DETECTED" # Caught sticker
            print("🚨 REJECTED: No real human face detected!")
        elif forgery_score > 0.25:
            status = "REJECTED_FORGERY_DETECTED" # Caught by ELA math
        elif not has_stamp:
            status = "MANUAL_REVIEW_NO_STAMP"
        else:
            status = "PENDING_NAME_MATCH" 

        return {
            "status": status,
            "metrics": {
                "forgery_score": round(forgery_score, 4),
                "has_official_stamp": has_stamp,
                "text_length": len(extracted_text),
                "software_edited": is_software_edited,
                "face_detected": has_face
            },
            "extracted_data": {
                "raw_text": extracted_text
            }
        }

# Instantiate globally so the heavy AI weights load only ONCE when the server starts
document_ai = DocumentVerificationService()