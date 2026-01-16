import streamlit as st
import os
import cv2
import numpy as np
from PIL import Image
import tempfile

# Module Imports
# Ensure these match your folder structure
from vision_module.interface import analyze_cable_image
from ocr_module.src.core_ocr import OCREngine
from ocr_module.src.extraction import SpecificationExtractor, SpecCorrector
from ocr_module.src.validation import CableValidator
from ocr_module.keyword_gen_module.keyword_tool import KeywordExtractor, CableClassifier

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SpecSense AI",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown("""
<style>
    .main-title {
        font-size: 4rem;
        font-weight: 800;
        color: #FFFFFF;
        text-align: center;
        letter-spacing: 2px;
        margin-top: -20px;
        margin-bottom: 0px;
        text-shadow: 0 0 10px rgba(77, 168, 218, 0.5);
    }
    .sub-title {
        font-size: 1.4rem;
        color: #B0B0B0;
        text-align: center;
        font-weight: 300;
        margin-bottom: 40px;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4DA8DA; /* Lighter blue for dark mode */
        margin-bottom: 10px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #C0C0C0;
        margin-bottom: 20px;
    }
    .card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .stApp {
        background-color: #0E1117;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("logo.png", width=120) 
    st.title("SpecSense AI")
    st.markdown("---")
    
    mode = st.radio(
        "Select Module:",
        ["Vision Inspection", "Datasheet/OCR Analysis"]
    )
    
    st.markdown("---")
    st.info("""
    **System Status:**
    ✅ Vision Module: Active
    ✅ OCR Module: Active
    ✅ Keyword Engine: Active
    """)
    st.caption("v1.0.0 | Graduation Project")

# --- HEADER PRESENTATION (Global) ---
# --- HEADER PRESENTATION (Global) ---
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    # Use columns to center the image effectively
    sub_c1, sub_c2, sub_c3 = st.columns([1, 2, 1])
    with sub_c2:
        st.image("logo.png", use_container_width=True)
    
    st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
    st.markdown('<p class="main-title">SpecSense AI</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Intelligent Cable Inspection & Document Analysis System</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN FUNCTIONS ---

def save_uploaded_file(uploaded_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

# --- MODULE: VISION INSPECTION ---
if mode == "Vision Inspection":
    st.markdown('<p class="main-header">👁️ Vision Inspection Module</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Automated cable cross-section analysis and defect detection.</p>', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader("Upload Cable Cross-Section (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("Start AI Analysis", type="primary"):
            
            # Create tabs for each image if multiple are uploaded
            tabs = st.tabs([f"Image {i+1}" for i in range(len(uploaded_files))])
            
            for i, uploaded_file in enumerate(uploaded_files):
                with tabs[i]:
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.subheader("Original Image")
                        image = Image.open(uploaded_file)
                        st.image(image, use_container_width=True)
                        
                    with st.spinner(f"Running YOLOv8 Inspection Model on {uploaded_file.name}..."):
                        # Save temp file for CV2 to read path
                        temp_path = save_uploaded_file(uploaded_file)
                        
                        if temp_path:
                            processed_img, data = analyze_cable_image(temp_path)
                            
                            # Clean up
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                            
                            if processed_img is not None:
                                # Convert BGR (CV2) to RGB (Streamlit)
                                processed_img_rgb = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
                                
                                with col2:
                                    st.subheader("Analysis Results")
                                    st.image(processed_img_rgb, use_container_width=True)
                                
                                # --- METRICS DASHBOARD ---
                                st.markdown("---")
                                st.subheader("📋 Inspection Report")
                                
                                if data and isinstance(data, list):
                                    # Usually only one cable per image is the main target, but handle list
                                    for j, cable_data in enumerate(data):
                                        if "Error" in cable_data:
                                            st.error(cable_data["Error"])
                                            continue
                                        
                                        # Display Metrics
                                        m1, m2, m3, m4 = st.columns(4)
                                        m1.metric("Diameter", f"{cable_data.get('Diameter (mm)', 0)} mm")
                                        status = cable_data.get('Status', 'Unknown')
                                        m2.metric("QC Status", status, delta="PASS" if "PASS" in status else "-FAIL")
                                        m3.metric("Est. Voltage", cable_data.get('Voltage Class', 'N/A').split('(')[0].strip())
                                        m4.metric("Cable Type", cable_data.get('Cable Type', 'N/A'))
                                        
                                        # Detailed Table
                                        with st.expander(f"Full Technical Details (Cable #{j+1})", expanded=True):
                                            # FIX: Convert to string to avoid Arrow type errors
                                            st.table({k: str(v) for k, v in cable_data.items()})
                                else:
                                    st.warning("No cables detected in the image.")
                                    
                            else:
                                # Error returned in data list
                                st.error(data[0].get("Error", "Unknown Analysis Error"))

# --- MODULE: DATASHEET OCR ---
elif mode == "Datasheet/OCR Analysis":
    st.markdown('<p class="main-header">📄 Datasheet OCR & Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Extract specifications, validate engineering rules, and generate keywords.</p>', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader("Upload Datasheet (PDF/Image)", type=["pdf", "png", "jpg", "jpeg", "docx"], accept_multiple_files=True)
    
    if uploaded_files and st.button("Extract & Validate All", type="primary"):
        
        tabs = st.tabs([f"Doc {i+1}: {f.name}" for i, f in enumerate(uploaded_files)])
        
        for i, uploaded_file in enumerate(uploaded_files):
            with tabs[i]:
                temp_path = save_uploaded_file(uploaded_file)
                status_container = st.container()
                
                try:
                    # 1. OCR READING
                    with status_container.status(f"Processing {uploaded_file.name}...", expanded=True) as s:
                        s.write("Initializing OCR Engine...")
                        ocr_engine = OCREngine(languages=['en']) # GPU auto-detected
                        
                        s.write("Reading Text...")
                        results = ocr_engine.read_image(temp_path, detail=0) # detail=0 for text list
                        
                        # Combine all text lines
                        full_text = " ".join(results)
                        s.write("Text Extraction Complete!")
                        
                        # 2. EXTRACTION
                        s.write("Extracting Specifications...")
                        extractor = SpecificationExtractor()
                        raw_specs = extractor.extract_specs(full_text)
                        
                        # 3. CORRECTION
                        s.write("Applying Engineering Corrections...")
                        corrector = SpecCorrector()
                        clean_specs, correction_log = corrector.correct_all(raw_specs)
                        
                        # 4. VALIDATION
                        s.write("Validating against IEC Standards...")
                        validator = CableValidator()
                        validation_result = validator.validate_cable(clean_specs)
                        
                        # 5. KEYWORDS
                        s.write("Generating Keywords & Classification...")
                        key_extractor = KeywordExtractor()
                        classifier = CableClassifier()
                        
                        keywords = key_extractor.extract_keywords(full_text)
                        category = classifier.classify(full_text)
                        
                        s.update(label="Analysis Complete!", state="complete", expanded=False)
                    
                    # --- DISPLAY RESULTS ---
                    
                    # Row 1: Extracted Data & Validation
                    c1, c2 = st.columns([3, 2])
                    
                    with c1:
                        st.subheader("📝 Extracted Specifications")
                        st.json(clean_specs)
                        
                        if correction_log:
                            with st.expander("🛠️ Correction Log (Auto-Fixes applied)"):
                                for log in correction_log:
                                    st.caption(f"- {log}")

                    with c2:
                        st.subheader("🛡️ Engineering Validation")
                        status_color = "green" if validation_result['valid'] else "red" if validation_result['status'] == 'NOT READY' else "orange"
                        st.markdown(f":{status_color}[**Status: {validation_result['status']}**]")
                        
                        if validation_result['errors']:
                            st.error("Violations Found:")
                            for err in validation_result['errors']:
                                st.markdown(f"- ❌ {err}")
                        
                        if validation_result['missing']:
                            st.warning("Missing / Unverifiable Data:")
                            for miss in validation_result['missing']:
                                st.markdown(f"- ⚠️ {miss}")
                                
                        if validation_result['valid']:
                            st.balloons()
                            st.success("✅ This cable specification meets all defined engineering standards.")

                    if validation_result['status'] != 'NOT READY':
                        st.markdown("---")
                        
                        # Row 2: Keywords & Classification
                        st.subheader("🏷️ Keyword Generation")
                        
                        k1, k2 = st.columns([1, 2])
                        with k1:
                            st.info(f"**Category Identified:**\n\n### {category}")
                        
                        with k2:
                            st.write("**Identified Keywords:**")
                            # Flatten the keyword dict for display tags
                            all_tags = []
                            for k, v in keywords.items():
                                if isinstance(v, list): all_tags.extend(v)
                                else: all_tags.append(str(v))
                            
                            st.write(", ".join([f"`{tag}`" for tag in all_tags[:20]])) # Limit display
                            
                            with st.expander("View Full Keyword JSON"):
                                st.json(keywords)

                except Exception as e:
                    st.error(f"System Error in {uploaded_file.name}: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
                    
                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)

# --- FOOTER ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #aaa; font-size: 0.8rem;'>© 2025 SpecSense AI | Graduation Project Team</div>", unsafe_allow_html=True)
