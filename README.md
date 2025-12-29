# Cable Specification OCR & Validation System

An intelligent pipeline for extracting, correcting, validating, and classifying electrical cable specifications from images and documents. This system combines Deep Learning OCR with expert engineering rules to ensure data integrity and compliance with international standards (IEC, IEEE).

## 🚀 Key Features

### 1. Robust OCR Extraction
- **Engine**: Powered by `EasyOCR` with GPU acceleration.
- **Multilingual**: Supports English and Arabic.
- **Extraction Logic**: Uses hybrid Regex patterns (`src/extraction.py`) to identify key electrical parameters (Voltage, Current, Size, Insulation, Armor, etc.).

### 2. Expert Post-OCR Correction (`SpecCorrector`)
Before validation, raw OCR data is cleaned and normalized:
- **"NxS" Notation Parsing**: Automatically splits complicated size strings (e.g., `"4x16mm2"` → `Cores: 4`, `Size: 16 mm²`).
- **Heuristic Repairs**: Intelli-fix for common OCR truncations (e.g., converts `"4 c"` to `"40°C"` based on context).
- **Unit Normalization**: Standardizes units (e.g., `MΩkm` → `MΩ·km`, `600/1000V` → `600/1000 V`).
- **Ambiguity Handling**: Safely marks unclear values as `UNVERIFIABLE` instead of guessing.

### 3. Strict 10-Point Engineering Validation (`CableValidator`)
Enforces a rigorous set of industrial rules to reject invalid or dangerous specs:
1.  **Cable Type**: Rejects hybrid Fiber-Optic/Power cables or unknown types.
2.  **Voltage**: Checks for mixed voltage levels (e.g., 500kV mixed with 12V) and AC/DC conflicts.
3.  **Current/Size**: Verifies physical ampacity limits (Current Density checks).
4.  **Insulation**: Validates material types (XLPE, PVC, EPR).
5.  **Conductor Count**: Ensures integer values.
6.  **Sheath**: Validates jacket materials (PVC, LSZH, PE).
7.  **Armor**: Rejects non-metallic armor types.
8.  **Temperature**: Enforces realistic operating ranges (-40°C to 105°C).
9.  **Resistance**: Checks for minimum insulation resistance (≥ 1 MΩ).
10. **Conductor Size**: Rejects physically impossible sizes.

### 4. Smart Keyword Analysis
- Automatically categorizes cables (e.g., "Low Voltage", "Medium Voltage") based on validated specs.
- Generates "Top Terms" for indexing and search.

---

## 🛠️ Usage

### Step 1: Run OCR Extraction
Extract raw data from an image.
```bash
python main.py --image "data/raw/your_image.png"
```
*Output*: Saves raw extracted specifications to `validation/latest_specs.json`.

### Step 2: Validate, Correct & Analyze
Run the strict validation/correction pipeline on the extracted data.
```bash
python validation/valid.py
```
*Output*: 
- Applies **Post-OCR Corrections**.
- Runs **10-Point Validation**.
- If `READY`: Executes **Keyword Analysis**.
- Displays a mandatory report:
    - **Normalized Specifications**
    - **Issues Fixed** (Log of corrections)
    - **Engineering Violations** (If any)

---

## 📂 Project Structure

```
OCR Model/
├── data/                   # Input images and raw data
├── keyword_gen_module/     # Keyword analysis & Classification
│   └── keyword_tool.py     # Main keyword logic
├── src/                    # Core Source Code
│   ├── core_ocr.py         # EasyOCR Engine setup
│   ├── extraction.py       # SpecExtractor & SpecCorrector class
│   └── validation.py       # CableValidator (Strict 10-Point Rules)
├── validation/             # Validation Workspace
│   ├── valid.py            # Main Validation execution script
│   └── latest_specs.json   # Interim data storage
├── main.py                 # Entry point for OCR Extraction
└── requirements.txt        # Python dependencies
```

## 📦 Requirements

- Python 3.8+
- NVIDIA GPU (Recommended for EasyOCR)
- Dependencies: `easyocr`, `torch`, `opencv-python`, `pandas`

Install via:
```bash
pip install -r requirements.txt
```
