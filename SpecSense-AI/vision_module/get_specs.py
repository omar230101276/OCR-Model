from ultralytics import YOLO
import cv2
import os
import glob

# --- System Configuration ---
# 1. Auto-find models
current_dir = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.join(current_dir, "runs", "detect")
possible_models = glob.glob(os.path.join(base_path, "train*", "weights", "best.pt"))
possible_models.sort(reverse=True)

# Create output folder for results
output_folder = os.path.join(current_dir, "Inspection_Results")
os.makedirs(output_folder, exist_ok=True)

# 2. Images Path
images_folder = os.path.join(current_dir, "Cable_Dataset", "images", "train")
image_files = glob.glob(os.path.join(images_folder, "*"))
image_files = [f for f in image_files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.jpg.jpg'))]

# 3. Calibration (Pixels per MM)
pixels_per_mm = 18.5 

if not image_files:
    print(f"[ERROR] No images found.")
    exit()

# 4. Select Working Model
active_model = None
print(f"[INFO] Initializing System...")
for model_path in possible_models:
    try:
        temp_model = YOLO(model_path)
        if temp_model(image_files[0], conf=0.01, verbose=False)[0].boxes:
            active_model = temp_model
            break
    except: continue

if not active_model:
    print("[ERROR] System Failure: No working AI model found.")
    exit()

# --- ENGINEERING LOGIC DATABASE ---
def get_cable_datasheet(diameter):
    """
    Returns technical specs based on cable diameter (Standard Estimation).
    """
    specs = {}
    
    if diameter < 15:
        specs["Voltage"] = "Low Voltage (300/500 V)"
        specs["Conductor"] = "Class 1 (Solid Copper)"
        specs["Insulation"] = "PVC (Polyvinyl Chloride)"
        specs["Sheath"] = "PVC (Grey/White)"
        specs["Type"] = "Control/Light Duty"
        
    elif 15 <= diameter < 40:
        specs["Voltage"] = "Low Voltage (0.6/1 kV)"
        specs["Conductor"] = "Class 2 (Stranded Copper)"
        specs["Insulation"] = "XLPE (Cross-linked PE)"
        specs["Sheath"] = "PVC (Black/UV Resistant)"
        specs["Type"] = "Power Cable (Armoured)"
        
    elif diameter >= 40:
        specs["Voltage"] = "Medium Voltage (11 kV - 33 kV)"
        specs["Conductor"] = "Class 2 (Compacted Copper/Al)"
        specs["Insulation"] = "XLPE + Semi-conductive Layer"
        specs["Sheath"] = "HDPE / PVC (Red/Black)"
        specs["Type"] = "Heavy Duty Power Feeder"
        
    return specs

print("\n" + "="*70)
print("🚀 FINAL TECHNICAL INSPECTION REPORT")
print("="*70 + "\n")

cables_found = 0

for image_path in image_files:
    results = active_model(image_path, conf=0.01, verbose=False)

    if results[0].boxes:
        cables_found += 1
        
        # Select best box
        best_box = None
        max_area = 0
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            area = (x2 - x1) * (y2 - y1)
            if area > max_area:
                max_area = area
                best_box = box
        
        if best_box:
            x1, y1, x2, y2 = best_box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            width_pixels = x2 - x1
            diameter_mm = width_pixels / pixels_per_mm
            
            # GET TECHNICAL SPECS
            tech_data = get_cable_datasheet(diameter_mm)
            
            # Status Check
            status = "✅ PASSED"
            # Logic: If diameter is weirdly small (<5mm) it's likely a cut or error
            if diameter_mm < 5: status = "⚠️ FAILED (Cut/Damage Detected)"

            # --- PRINT DETAILED REPORT ---
            print(f"📄 IMAGE FILE: {os.path.basename(image_path)}")
            print("-" * 50)
            print(f" > MEASUREMENTS:")
            print(f"   - Pixel Width:    {width_pixels} px")
            print(f"   - Real Diameter:  {diameter_mm:.2f} mm")
            print(f"   - System Status:  {status}")
            print("-" * 50)
            print(f" > TECHNICAL SPECIFICATIONS (AI ESTIMATED):")
            print(f"   - Voltage Class:  {tech_data['Voltage']}")
            print(f"   - Conductor:      {tech_data['Conductor']}")
            print(f"   - Insulation:     {tech_data['Insulation']}")
            print(f"   - Sheath Mat.:    {tech_data['Sheath']}")
            print(f"   - Cable Type:     {tech_data['Type']}")
            print("=" * 70 + "\n")

            # --- DRAW ON IMAGE ---
            img = cv2.imread(image_path)
            # Box
            color = (0, 255, 0) if "PASSED" in status else (0, 0, 255)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 4)
            
            # Info Panel (Background)
            # Create a larger black area to fit the text
            cv2.rectangle(img, (x1, y1-130), (x1+500, y1), (0, 0, 0), -1)
            
            # Text Lines
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(img, f"Dia: {diameter_mm:.1f} mm ({status})", (x1+10, y1 - 90), font, 0.8, (255, 255, 255), 2)
            cv2.putText(img, f"Volt: {tech_data['Voltage']}", (x1+10, y1 - 60), font, 0.6, (200, 200, 200), 1)
            cv2.putText(img, f"Insul: {tech_data['Insulation']}", (x1+10, y1 - 30), font, 0.6, (200, 200, 200), 1)
            
            output_name = f"Datasheet_{os.path.basename(image_path)}".replace(".jpg.jpg", ".jpg")
            output_path = os.path.join(output_folder, output_name)
            cv2.imwrite(output_path, img)

print(f"✅ Full Technical Generation Complete.")
print(f"📁 Results saved to: {output_folder}")
print("Check 'Inspection_Results' folder for visual verification.")