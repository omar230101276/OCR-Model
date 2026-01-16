import cv2
import numpy as np  # Required for robust image loading
import os
from ultralytics import YOLO

# ==========================================
# ⚙️ CONFIGURATION & SETTINGS
# ==========================================
# Calibration Factor: Number of pixels representing 1 millimeter.
# Calibrated based on reference object (Adjust if camera height changes).
PIXELS_PER_MM = 18.5 

# AI Confidence Threshold: Minimum score (0-1) to accept a detection.
# Set EXTREMELY low (0.01) because the current model is very weak/undertrained.
CONF_THRESHOLD = 0.01

# ==========================================
# 🧠 MODEL LOADER
# ==========================================
# Locate the YOLO model file relative to this script
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "best.pt")

def analyze_cable_image(image_path):
    """
    Analyzes a cable cross-section image using YOLOv8 AI model.
    Measures diameter and classifies quality.

    Args:
        image_path (str): Full path to the input image.

    Returns:
        tuple: (processed_image_array, results_list_of_dicts)
    """
    
    # 1. Load the AI Model
    try:
        model = YOLO(model_path)
    except Exception as e:
        return None, [{"Error": f"Model failed to load. Check '{model_path}'. Error: {e}"}]

    # 2. Read Image (ROBUST METHOD)
    # Standard cv2.imread fails with non-English paths/spaces on Windows.
    # We use numpy to read raw bytes, then decode them.
    try:
        # Read file as byte stream
        img_stream = np.fromfile(image_path, dtype=np.uint8)
        # Decode image
        img = cv2.imdecode(img_stream, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Image decoding failed (Result is None).")
            
    except Exception as e:
        return None, [{"Error": f"Failed to read image. File might be corrupt or path invalid. Details: {e}"}]

    # 3. Run AI Inference
    # verbose=False suppresses terminal noise
    results = model(img, conf=CONF_THRESHOLD, verbose=False)
    
    output_data = []
    
    # 4. Process Detections
    all_detections = []
    
    if results[0].boxes:
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            width_px = x2 - x1
            height_px = y2 - y1
            area = width_px * height_px
            conf = float(box.conf)
            
            diameter_mm = width_px / PIXELS_PER_MM
            
            all_detections.append({
                "box": (x1, y1, x2, y2),
                "width_px": width_px,
                "diameter_mm": diameter_mm,
                "area": area,
                "conf": conf
            })
            
    # --- SMART FILTERING ---
    # Logic matched to get_specs.py: Find the ONE best box (Largest Area)
    final_detections = []
    if all_detections:
        # Sort by Area (Largest first)
        all_detections.sort(key=lambda x: x['area'], reverse=True)
        # Take ONLY the largest one (Main Cable)
        final_detections = [all_detections[0]]
            
    output_data = []
    
    for det in final_detections:
        x1, y1, x2, y2 = det['box']
        diameter_mm = det['diameter_mm']
        width_px = det['width_px']
        
        # --- AI Estimation Logic (Rule-Based) ---
        # Estimate specs based on physical diameter
        # Logic copied exactly from get_specs.py to match user expectations
        if diameter_mm >= 40:
            specs = {
                "Voltage Class": "Medium Voltage (11 kV - 33 kV)",
                "Conductor": "Class 2 (Compacted Copper/Al)",
                "Insulation": "XLPE + Semi-conductive Layer",
                "Sheath Mat.": "HDPE / PVC (Red/Black)",
                "Cable Type": "Heavy Duty Power Feeder"
            }
        elif 15 <= diameter_mm < 40:
            specs = {
                "Voltage Class": "Low Voltage (0.6/1 kV)",
                "Conductor": "Class 2 (Stranded Copper)",
                "Insulation": "XLPE (Cross-linked PE)",
                "Sheath Mat.": "PVC (Black/UV Resistant)",
                "Cable Type": "Power Cable (Armoured)"
            }
        else:
            specs = {
                "Voltage Class": "Low Voltage (300/500 V)",
                "Conductor": "Class 1 (Solid Copper)",
                "Insulation": "PVC (Polyvinyl Chloride)",
                "Sheath Mat.": "PVC (Grey/White)",
                "Cable Type": "Control/Light Duty"
            }

        # --- Quality Control Logic ---
        if diameter_mm > 5.0:
            status = "PASS"
            color = (0, 255, 0)
        else:
            status = "FAIL (Too Small)"
            color = (0, 0, 255)

        # --- Visualization ---
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
        
        # Info Panel on Image - mirroring get_specs.py style
        # Create a larger background area to fit details if needed
        label_text = f"Dia: {diameter_mm:.1f} mm"
        (text_w, text_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        
        # Top label
        cv2.rectangle(img, (x1, y1 - 30), (x1 + text_w + 20, y1), color, -1)
        cv2.putText(img, label_text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        output_data.append({
            "Diameter (mm)": round(diameter_mm, 2),
            "Width (px)": width_px,
            "Voltage Class": specs["Voltage Class"],
            "Conductor": specs["Conductor"],
            "Insulation": specs["Insulation"],
            "Sheath Mat.": specs["Sheath Mat."],
            "Cable Type": specs["Cable Type"],
            "Status": status
        })
            
    return img, output_data