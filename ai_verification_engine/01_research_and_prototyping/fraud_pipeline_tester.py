print("🚀 [1/5] Booting up Python engine...")
import os
import cv2
import numpy as np
from PIL import Image, ImageChops

print("📦 [2/5] Basic image libraries loaded. Initializing PyTorch & Surya OCR...")
try:
    from surya.recognition import RecognitionPredictor
    from surya.detection import DetectionPredictor
    print("✅ [3/5] Surya OCR imported successfully.")
except ImportError as e:
    print(f"❌ [CRASH] Failed to import Surya: {e}")
    exit(1)

class IDPipelinePreprocessors:
    @staticmethod
    def _pil_to_bgr(img: Image.Image) -> np.ndarray:
        return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)

    @staticmethod
    def _np_to_pil(bgr: np.ndarray) -> Image.Image:
        return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))

    @classmethod
    def deskew(cls, img: Image.Image) -> Image.Image:
        bgr = cls._pil_to_bgr(img)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
        
        if lines is None: return img
            
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 != x1:
                angles.append(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
                
        if not angles: return img

        median_angle = float(np.median(angles))
        snapped = round(median_angle / 90) * 90
        skew = median_angle - snapped

        if abs(skew) < 0.5: return img 

        h, w = bgr.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), skew, 1.0)
        rotated = cv2.warpAffine(bgr, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        print(f"  [Preprocessor] ↻ Deskew applied: {skew:+.1f}°")
        return cls._np_to_pil(rotated)

class FraudDetectorPipeline:
    def __init__(self):
        print("🧠 [4/5] Loading AI Weights into Memory...")
        # Load Detection and Recognition separately
        self.det_predictor = DetectionPredictor()
        self.rec_predictor = RecognitionPredictor()
        print("✅ [5/5] AI Models loaded and ready!")

    def run_ela(self, image_path: str, resaved_quality: int = 90) -> float:
        try:
            original = Image.open(image_path).convert('RGB')
            temp_path = "temp_ela.jpg"
            original.save(temp_path, 'JPEG', quality=resaved_quality)
            compressed = Image.open(temp_path)
            
            ela_image = ImageChops.difference(original, compressed)
            ela_array = np.array(ela_image)
            
            # Using Pixel Variance to catch Photoshop injections
            suspicion_score = np.var(ela_array) / 255.0
            os.remove(temp_path)
            
            return float(suspicion_score)
        except Exception as e:
            print(f"  [ELA Error] {e}")
            return 0.0

    def extract_text(self, img: Image.Image) -> str:
        try:
            # Step 1: Detect where the text is (Bounding Boxes)
            det_results = self.det_predictor([img])
            
            bboxes = []
            for box in det_results[0].bboxes:
                bboxes.append(box.bbox)
                
            if not bboxes:
                return ""
                
            # Step 2: Read the text inside those boxes
            # We omit 'langs' completely so it auto-detects and avoids the hashing crash
            rec_results = self.rec_predictor([img], bboxes=[bboxes])
            
            text_lines = []
            for line in rec_results[0].text_lines:
                if getattr(line, "confidence", 1.0) > 0.4:
                    text_lines.append(line.text)
                    
            return "\n".join(text_lines)
            
        except Exception as e:
            print(f"  [OCR Error] {e}")
            return ""

    def evaluate_document(self, document_path: str):
        print(f"\n{'='*50}\n🔍 EVALUATING: {os.path.basename(document_path)}\n{'='*50}")
        
        raw_img = Image.open(document_path)
        clean_img = IDPipelinePreprocessors.deskew(raw_img)
        temp_clean_path = "temp_clean_id.jpg"
        clean_img.save(temp_clean_path)

        print("-> Running Error Level Analysis (Forgery Check)...")
        ela_score = self.run_ela(temp_clean_path)
        ela_flag = "🚨 HIGH RISK" if ela_score > 0.25 else "✅ Safe"
        print(f"-> Forgery Score: {ela_score:.4f} ({ela_flag})")

        print("-> Extracting Text (Surya OCR)...")
        extracted_text = self.extract_text(clean_img)
        print(f"-> Extracted {len(extracted_text)} characters.")
        if len(extracted_text) > 0:
            print("-> Snippet: ", repr(extracted_text[:75] + "..."))
        
        if os.path.exists(temp_clean_path):
            os.remove(temp_clean_path)

if __name__ == "__main__":
    TEST_DIR = "mock_dataset"

    if not os.path.exists(TEST_DIR) or len(os.listdir(TEST_DIR)) == 0:
        print(f"❌ '{TEST_DIR}' is empty. Run 'generate_mock_dataset.py' first!")
        exit(1)

    pipeline = FraudDetectorPipeline()

    for filename in sorted(os.listdir(TEST_DIR)):
        if filename.endswith(".jpg"):
            doc_path = os.path.join(TEST_DIR, filename)
            pipeline.evaluate_document(doc_path)