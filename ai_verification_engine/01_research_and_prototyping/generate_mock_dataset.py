import os
import cv2
import numpy as np
from PIL import Image, ImageDraw

# --- Configuration ---
# Now it accepts multiple templates!
INPUT_TEMPLATES = ["clean_national_id.jpg", "clean_contract.jpg"]
OUTPUT_DIR = "mock_dataset"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def apply_physical_degradations(img: Image.Image, quality: str) -> Image.Image:
    """Simulates a user taking a bad photo of their document with a phone."""
    bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    if quality == "low_quality_blur":
        bgr = cv2.GaussianBlur(bgr, (9, 9), 2.0)
    elif quality == "low_quality_contrast":
        bgr = cv2.convertScaleAbs(bgr, alpha=0.6, beta=20)
    elif quality == "deskew_test":
        h, w = bgr.shape[:2]
        angle = np.random.uniform(-6.0, 6.0) 
        M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1)
        bgr = cv2.warpAffine(bgr, M, (w, h), borderValue=(255, 255, 255))

    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))

def inject_digital_forgery(img: Image.Image) -> Image.Image:
    """Simulates a user Photoshopping text onto the document."""
    forged_img = img.copy()
    draw = ImageDraw.Draw(forged_img)
    
    width, height = forged_img.size
    box_x1, box_y1 = int(width * 0.3), int(height * 0.4)
    box_x2, box_y2 = int(width * 0.7), int(height * 0.5)
    
    draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=(245, 245, 240))
    draw.text((box_x1 + 10, box_y1 + 10), "FORGED NAME / YOUSSEF", fill=(0, 0, 0))
    
    return forged_img

def main():
    print(f"🚀 Starting Real-World Data Generation...")
    
    for template_name in INPUT_TEMPLATES:
        if not os.path.exists(template_name):
            print(f"⚠️ Skipping '{template_name}' (File not found).")
            continue
            
        doc_prefix = template_name.split('.')[0]
        base_img = Image.open(template_name).convert("RGB")
        print(f"\n📄 Processing Template: {template_name}")
        
        # 1. Authentic Clean
        base_img.save(os.path.join(OUTPUT_DIR, f"{doc_prefix}_00_authentic_clean.jpg"), "JPEG", quality=95)
        
        # 2. Physical Variations
        qualities = ["low_quality_blur", "low_quality_contrast", "deskew_test"]
        for idx, q in enumerate(qualities, 1):
            degraded_img = apply_physical_degradations(base_img.copy(), q)
            out_name = f"{doc_prefix}_{idx:02d}_authentic_{q}.jpg"
            degraded_img.save(os.path.join(OUTPUT_DIR, out_name), "JPEG", quality=85)
            print(f"  ✅ Created: {out_name}")

        # 3. Digital Forgery
        forged_img = inject_digital_forgery(base_img.copy())
        forged_name = f"{doc_prefix}_99_FORGED_tampered_text.jpg"
        forged_img.save("temp_forge.jpg", "JPEG", quality=90)
        Image.open("temp_forge.jpg").save(os.path.join(OUTPUT_DIR, forged_name), "JPEG", quality=85)
        os.remove("temp_forge.jpg")
        print(f"  🚨 Created FORGERY: {forged_name}")

    print(f"\n🎉 Dataset generation complete! Check the '{OUTPUT_DIR}' folder.")

if __name__ == "__main__":
    main()