import os
import sys
import argparse
import json
import pandas as pd

# Add the project root to sys.path to allow importing from src
# Assuming valid.py is in o:\OCR Model\validation\valid.py
# and project root is o:\OCR Model
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import the shared validator
try:
    from src.validation import CableValidator
except ImportError:
    print("❌ Error: Could not import CableValidator from src.validation.")
    print(f"PYTHONPATH: {sys.path}")
    sys.exit(1)

# Lazy import wrapper for OCR components
def get_ocr_engine_class():
    try:
        # We need to import OCREngine from the original script or move it to a shared place?
        # The user's original valid.py had OCREngine inline.
        # But main.py imports it from src.core_ocr.
        # So we should use src.core_ocr here too to be consistent!
        from src.core_ocr import OCREngine
        return OCREngine
    except ImportError as e:
        print(f"❌ Error importing OCR Engine: {e}")
        return None

def get_table_extractor_class():
    from src.table_engine import TableExtractor
    return TableExtractor

def get_spec_extractor_class():
    from src.extraction import SpecificationExtractor
    return SpecificationExtractor


# -----------------------------------------------------------------------------
# REPORT GENERATOR
# -----------------------------------------------------------------------------
class ReportGenerator:
    @staticmethod
    def print_console_report(filename, specs, validation):
        """Print formatted console report"""
        print("\n" + "="*80)
        print(f"📄 SOURCE: {filename}")
        print("="*80)
        
        print("\n📋 SPECIFICATIONS:")
        print("-" * 80)
        for key, value in specs.items():
            display_value = value if value else "Not Found"
            print(f"  {key.replace('_', ' ').title()}: {display_value}")
        
        print("\n🔍 VALIDATION RESULTS:")
        print("-" * 80)
        print(f"  Status: {validation['status']}")
        
        if validation['warnings']:
            print("\n  ⚠️  WARNINGS:")
            for warning in validation['warnings']:
                print(f"    • {warning}")
        
        if validation['errors']:
            print("\n  ❌ ERRORS:")
            for error in validation['errors']:
                print(f"    • {error}")
        
        if validation['valid'] and not validation['warnings']:
            print("\n  ✅ All specifications are valid and meet standards!")
        
        print("="*80 + "\n")


# -----------------------------------------------------------------------------
# MAIN EXECUTION
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Cable Specification Validation Tool")
    parser.add_argument("--image", help="Path to input image/PDF/DOCX. If omitted, checks validation/latest_specs.json")
    parser.add_argument("--mode", choices=["text", "table", "full", "test", "validate_json"], default="full", 
                       help="Operation mode. 'full' does OCR+Validation (if image provided). 'validate_json' is default if no image.")
    parser.add_argument("--langs", default="en", help="Comma-separated list of languages (e.g., 'en,ar')")

    args = parser.parse_args()
    
    # Import Keyword Tool (lazy load)
    # Since we added project_root to sys.path, we can import from keyword_gen_module
    def get_keyword_tool():
        try:
            from keyword_gen_module.keyword_tool import run_analysis
            return run_analysis
        except ImportError as e:
            print(f"❌ Error importing Keyword Tool: {e}")
            return None

    # Mode: Test (Unit tests for validator)
    if args.mode == "test":
        test_validation()
        return

    # Scenario 1: No image provided -> Check latest_specs.json
    if not args.image:
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'latest_specs.json')
        if os.path.exists(json_path):
            print(f"📢 No image provided. Checking latest output: {json_path}")
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    specs = json.load(f)
                
                # --- 1. POST-OCR CORRECTION ---
                from src.extraction import SpecCorrector
                corrector = SpecCorrector()
                specs, logs = corrector.correct_all(specs)

                # Save CORRECTED specs back to file (so keyword tool sees clean data)
                try:
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(specs, f, indent=4)
                except Exception as e:
                    print(f"⚠️ Failed to save corrected specs: {e}")

                # --- 2. VALIDATION ---
                validator = CableValidator()
                validation = validator.validate_cable(specs)
                
                # --- 3. REPORTING (MANDATORY FORMAT) ---
                print("\n" + "="*80)
                print("Normalized Specifications:")
                print("="*80)
                fields = [
                    "Cable Type", "Voltage Rating", "Current Rating", "Insulation Type",
                    "Number of Conductors", "Conductor Size", "Sheath / Jacket", 
                    "Armor", "Operating Temperature", "Insulation Resistance"
                ]
                # Map extracted keys to display keys
                key_map = {
                    "Cable Type": "cable_type", "Voltage Rating": "voltage", "Current Rating": "current_rating",
                    "Insulation Type": "insulation", "Number of Conductors": "conductor_count", 
                    "Conductor Size": "conductor_size", "Sheath / Jacket": "sheath", "Armor": "armor",
                    "Operating Temperature": "operating_temperature", "Insulation Resistance": "insulation_resistance"
                }
                
                for field in fields:
                    val = specs.get(key_map[field])
                    print(f"- {field}: {val if val else 'N/A'}")

                print("\nValidation Result:")
                print("-" * 80)
                print(f"- Status: {validation.get('status', 'UNKNOWN')}")
                
                print("\nIssues Fixed:")
                print("-" * 80)
                if logs:
                    for log in logs:
                        print(f"- {log}")
                else:
                    print("- None")

                print("\nEngineering Violations:")
                print("-" * 80)
                if validation.get('errors'):
                    for err in validation['errors']:
                        print(f"- {err}")
                else:
                    print("- None")
                
                if validation.get('missing') and validation['status'] == "UNVERIFIABLE":
                     print("\nUnverifiable Factors:")
                     for miss in validation['missing']:
                         print(f"- {miss}")
                
                print("="*80)

                if validation['valid']:
                    print("\n\n✅ VALIDATION SUCCESSFUL. Proceeding to Keyword Analysis...")
                    print("="*80)
                    try:
                        import keyword_gen_module.keyword_tool as kt
                        kt.run_analysis(json_path)
                    except ImportError:
                        print("⚠️ Could not import keyword_tool. Is it in the path?")
                    except Exception as e:
                        print(f"⚠️ Keyword Analysis Failed: {e}")
                else:
                    print(f"\n\n❌ VALIDATION RESULT: {validation['status']}. Process Terminated.")
                    sys.exit(1)
                return
            except Exception as e:
                print(f"❌ Error reading/processing JSON: {e}")
                import traceback
                traceback.print_exc()
                return
        else:
            print("❌ No image provided and 'latest_specs.json' not found.")
            print("   Run 'python main.py ...' first to generate specs or provide --image.")
            return

    # Scenario 2: Image provided -> Run OCR + Validation (The old 'full' mode)
    if not os.path.exists(args.image):
        print(f"❌ Error: File {args.image} not found.")
        return

    # Initialize Engine (Lazy Load)
    OCREngine = get_ocr_engine_class()
    if not OCREngine:
        return

    languages = args.langs.split(',')
    ocr = OCREngine(languages=languages)

    if args.mode == "text" or args.mode == "full":
        # Text extraction
        print(f"📖 Reading text from: {args.image} ...")
        results = ocr.read_image(args.image, detail=0)
        full_text = " ".join(results)
        
        # Extract specs
        SpecificationExtractor = get_spec_extractor_class()
        extractor = SpecificationExtractor()
        specs = extractor.extract_specs(full_text)
        
        if args.mode == "text":
             # Just print specs
             print(specs)
        else:
            # Validate
            validator = CableValidator()
            validation = validator.validate_cable(specs)
            ReportGenerator.print_console_report(args.image, specs, validation)
            
            # INTEGRATION for --image mode too?
            # The prompt implies "when I run valid.py automaticly read it" which matches Scenario 1.
            # But let's support it here too if desired, though usually valid.py is run without args for the pipeline.
            if validation['valid']:
                 print("\n✅ VALIDATION SUCCESSFUL.")
            else:
                 print("\n❌ VALIDATION FAILED.")

    elif args.mode == "table":
        # Table extraction
        print(f"📊 Extracting table from: {args.image} ...")
        TableExtractor = get_table_extractor_class()
        table_engine = TableExtractor(ocr)
        try:
            df = table_engine.extract_table(args.image)
            print("\n--- Extracted Table ---")
            print(df)
        except Exception as e:
            print(f"❌ Error extracting table: {e}")


# Test mode for validation testing
def test_validation():
    """Test validation with different scenarios"""
    validator = CableValidator()
    
    print("\n" + "="*80)
    print("🧪 TESTING VALIDATION SYSTEM")
    print("="*80)
    
    # Test Case 1: Invalid - PVC with high voltage
    print("\n📋 TEST CASE 1: PVC + High Voltage")
    specs1 = {
        'insulation': 'PVC',
        'voltage': '1500V',
        'cable_type': 'Copper',
        'operating_temperature': '60C'
    }
    result1 = validator.validate_cable(specs1)
    print(f"Status: {result1['status']}")
    
    # Test Case: Decimal Voltage (The Fix)
    print("\n📋 TEST CASE: Decimal Voltage (0.6/1kV)")
    specs_dec = {
        'insulation': 'XLPE',
        'voltage': '0.6/1kV',
        'cable_type': 'Copper',
        'operating_temperature': '90C'
    }
    result_dec = validator.validate_cable(specs_dec)
    print(f"Status: {result_dec['status']}")
    if result_dec['valid']:
         print("  ✅ Decimal voltage handled correctly!")
    else:
         print(f"  ❌ Failed: {result_dec['errors']}")


if __name__ == "__main__":
    main()