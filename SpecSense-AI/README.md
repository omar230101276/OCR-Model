# SpecSense AI 🔌

**Intelligent Cable Inspection & Document Analysis System**

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-green.svg)
![EasyOCR](https://img.shields.io/badge/EasyOCR-1.7+-orange.svg)

## 📋 Overview

SpecSense AI is a comprehensive cable analysis system that combines computer vision and OCR technologies to:

1. **Vision Inspection Module** - Analyze cable cross-section images using YOLOv8 for automated geometry detection
2. **OCR & Validation Module** - Extract technical specifications from datasheets and validate them against engineering standards
3. **Keyword Generation** - Automatically classify cables and extract key technical terms

## ✨ Features

- 🔍 **Automated Geometry Analysis** - Detect cable diameter and defects from cross-section images
- 📄 **Smart Document Extraction** - Extract voltage, current, insulation, and other specs from datasheets
- 🛡️ **Engineering Validation** - Validate extracted specs against industry standards
- 🔢 **Keyword Generation** - Classify cables by voltage category and extract technical keywords
- 📊 **Interactive Dashboard** - Modern Streamlit-based web interface

## 🚀 Installation

### Prerequisites
- Python 3.10+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/ahmed-kora3/SpecSense-AI.git
cd SpecSense-AI

# Install dependencies
pip install -r requirements.txt
```

## 💻 Usage

### Run the Application

```bash
python -m streamlit run app.py
```

Then open your browser at `http://localhost:8501`

### Modules

#### 1. Vision Inspection
- Upload cable cross-section images (JPG, PNG)
- Click "Start AI Analysis"
- View detected components and measurements

#### 2. Datasheet OCR & Validation
- Upload datasheets or catalogs (JPG, PNG, PDF, DOCX)
- Click "Extract & Validate All"
- View extracted specifications
- Click "Generate Keywords" for cable classification

## 📁 Project Structure

```
SpecSenseAI/
├── app.py                     # Main Streamlit application
├── requirements.txt           # Python dependencies
├── logo.png                   # Application logo
├── ocr_module/               
│   ├── interface.py           # OCR module interface
│   ├── src/
│   │   ├── core_ocr.py        # EasyOCR engine
│   │   ├── extraction.py      # Specification extractor
│   │   └── validation.py      # Engineering validator
│   └── keyword_gen_module/
│       └── keyword_tool.py    # Cable classifier & keyword extractor
├── vision_module/
│   ├── interface.py           # Vision module interface
│   └── src/
│       └── detector.py        # YOLOv8 detector
└── yolov8n.pt                 # Pre-trained YOLO model
```

## 🔧 Technologies

| Technology | Purpose |
|------------|---------|
| **Streamlit** | Web interface |
| **YOLOv8 (Ultralytics)** | Object detection for vision inspection |
| **EasyOCR** | Optical character recognition |
| **OpenCV** | Image processing |
| **spaCy** | Natural language processing |
| **PyPDF2** | PDF text extraction |
| **python-docx** | DOCX text extraction |

## 📝 Cable Categories

The system classifies cables into:
- **HTLS Conductors** - High Temperature Low Sag
- **Overhead Conductors** - AAC, AAAC, ACSR
- **High & Extra High Voltage Cables** - 66kV to 500kV
- **Medium Voltage Cables** - 6.6kV to 33kV
- **Low Voltage Cables** - Up to 1.8/3 kV

## 👥 Authors

**Graduation Project Team**

## 📄 License

This project is part of a graduation project system.

---

© 2025 SpecSense AI | Graduation Project System
