from ultralytics import YOLO

print("🧠 Initializing YOLOv8 Nano Model...")
# Load a blank, lightweight nano model
model = YOLO('yolov8n.pt') 

print("🚀 Starting Training Phase...")
# Train the model on our synthetic dataset
# 20 epochs is usually enough for it to learn a simple stamp!
model.train(
    data='stamp_data.yaml',
    epochs=20,
    imgsz=640,
    device='cpu', # using CPU since your CachyOS CUDA paths were noisy earlier, it trains fast anyway!
    plots=True
)

print("✅ Training Complete! Your custom model is saved in 'runs/detect/train/weights/best.pt'")