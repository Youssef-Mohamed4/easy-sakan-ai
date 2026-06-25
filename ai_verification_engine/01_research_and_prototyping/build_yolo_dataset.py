import os
import random
from PIL import Image, ImageEnhance

# --- Configuration ---
STAMP_IMG = "reference_stamp.jpg"
BG_IMG = "clean_contract.jpg"
NUM_IMAGES = 100

# --- Setup YOLO Directories ---
dirs = ["yolo_dataset/images/train", "yolo_dataset/labels/train"]
for d in dirs:
    os.makedirs(d, exist_ok=True)

def create_synthetic_data():
    print("🚀 Generating Synthetic YOLO Dataset...")
    
    stamp = Image.open(STAMP_IMG).convert("RGBA")
    background = Image.open(BG_IMG).convert("RGB")
    bg_w, bg_h = background.size

    for i in range(NUM_IMAGES):
        bg_copy = background.copy()
        
        # 1. FIXED SCALING: Make the stamp 10% to 25% of the contract's width
        target_width_ratio = random.uniform(0.10, 0.25)
        new_w = int(bg_w * target_width_ratio)
        
        # Maintain aspect ratio so the stamp doesn't get squished!
        aspect_ratio = stamp.height / stamp.width
        new_h = int(new_w * aspect_ratio)
        
        resized_stamp = stamp.resize((new_w, new_h))
        
        # 2. Randomly fade the ink (Simulate bad stamps)
        alpha = resized_stamp.getchannel('A')
        alpha = ImageEnhance.Brightness(alpha).enhance(random.uniform(0.3, 1.0))
        resized_stamp.putalpha(alpha)
        
        # 3. Pick a random location on the contract
        paste_x = random.randint(0, bg_w - new_w)
        paste_y = random.randint(0, bg_h - new_h)
        
        # 4. Paste the stamp
        bg_copy.paste(resized_stamp, (paste_x, paste_y), resized_stamp)
        
        # 5. Calculate YOLO bounding box format (Normalized x_center, y_center, width, height)
        x_center = (paste_x + (new_w / 2)) / bg_w
        y_center = (paste_y + (new_h / 2)) / bg_h
        norm_w = new_w / bg_w
        norm_h = new_h / bg_h
        
        # 6. Save Image
        img_filename = f"synthetic_stamp_{i:03d}.jpg"
        bg_copy.save(os.path.join("yolo_dataset/images/train", img_filename), quality=85)
        
        # 7. Save YOLO Label (Class 0)
        label_filename = f"synthetic_stamp_{i:03d}.txt"
        with open(os.path.join("yolo_dataset/labels/train", label_filename), "w") as f:
            f.write(f"0 {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}\n")

    # Create the YAML file that tells YOLO where the data is
    yaml_content = f"""
path: {os.path.abspath('yolo_dataset')}
train: images/train
val: images/train # Using train for val just for this rapid prototype

names:
  0: official_stamp
"""
    with open("stamp_data.yaml", "w") as f:
        f.write(yaml_content)

    print(f"✅ Successfully generated {NUM_IMAGES} synthetic training images and labels!")
    print("✅ Created stamp_data.yaml")

if __name__ == "__main__":
    create_synthetic_data()