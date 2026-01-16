from ultralytics import YOLO
import torch
from pathlib import Path

# --- Configuration ---
DATA_YAML_PATH = 'data.yaml' 
MODEL_SIZE = 'yolov8m-seg.pt' # 'm' for medium. Use 'n' for smaller/faster training.
EPOCHS = 150
BATCH_SIZE = 8 
IMG_SIZE = 640

# --- Training Script ---
def train_yolov8():
    """Initializes and trains the YOLOv8 segmentation model."""
    
    # Check for GPU availability
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"--- Starting Training on Device: {device.upper()} ---")

    try:
        # Load a pretrained YOLOv8 Segmentation model
        model = YOLO(MODEL_SIZE)
        print(f"Loaded base model: {MODEL_SIZE}")

        # Start Training
        results = model.train(
            data=DATA_YAML_PATH,     # Your dataset configuration file
            epochs=EPOCHS,           # Number of training cycles
            imgsz=IMG_SIZE,          # Input image size
            batch=BATCH_SIZE,        # Adjust based on your GPU VRAM
            device=device,           # Specify the device (cuda or cpu)
            name='cable_analysis_v1' # Run name
        )

        # Get the path of the best saved model
        save_dir = Path(results.save_dir)
        best_model_path = save_dir / 'weights' / 'best.pt'
        print(f"\nTraining Complete. Best model saved to: {best_model_path}")
        return best_model_path

    except Exception as e:
        print(f"An error occurred during training: {e}")
        return None

if __name__ == "__main__":
    trained_model_path = train_yolov8()