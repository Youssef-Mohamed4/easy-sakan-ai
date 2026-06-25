from ultralytics import YOLO

def check_stamp_with_ai(document_path):
    print(f"🔍 AI Scanning {document_path} for official stamps...")
    
    # Load your custom trained model
    model = YOLO('runs/detect/train/weights/best.pt')
    
    # Run prediction (conf=0.25 means we are okay with faded/blurry stamps)
    results = model.predict(document_path, conf=0.25)
    
    # Count how many stamps it found
    stamp_count = len(results[0].boxes)
    
    if stamp_count > 0:
        print(f"✅ STAMP DETECTED! Found {stamp_count} stamp(s).")
        # Optional: Save a picture showing exactly where it drew the box
        results[0].save(filename=f"ai_result_{document_path}")
        return True
    else:
        print("🚨 NO STAMP FOUND. Document rejected.")
        return False

if __name__ == "__main__":
    check_stamp_with_ai("real_contract_sample.jpg")