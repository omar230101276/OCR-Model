import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Cable Specification OCR System")
    parser.add_argument("--image", required=True, help="Path to input image")
    parser.add_argument("--mode", choices=["text", "table"], default="text", help="Operation mode: 'text' for specs/text extraction, 'table' for table extraction")
    parser.add_argument("--output", help="Output path (for CSV tables)")


    parser.add_argument("--langs", default="en", help="Comma-separated list of languages (e.g., 'en,ar')")
    parser.add_argument("--use-spacy", action="store_true", help="Use SpaCy for robust specification extraction")

    args = parser.parse_args()

    print(f"DEBUG: Received image path: '{args.image}'")
    print(f"DEBUG: Absolute path: '{os.path.abspath(args.image)}'")
    print(f"DEBUG: Exists? {os.path.exists(args.image)}")

    if not os.path.exists(args.image):
        print(f"Error: File {args.image} not found.")
        return

    # Initialize Engine
    languages = args.langs.split(',')
    
    # Lazy imports
    from src.core_ocr import OCREngine
    from src.extraction import SpecificationExtractor
    from src.table_engine import TableExtractor

    ocr = OCREngine(languages=languages)

    if args.mode == "text":
        print(f"Reading text from: {args.image} ...")
        results = ocr.read_image(args.image, detail=0)
        full_text = " ".join(results)
        print("\n--- Extracted Text ---")
        print(full_text)
        
        print("\n--- Extracted Specifications ---")
        
        if args.use_spacy:
            print("(Using SpaCy Extractor)")
            from src.spacy_extraction import SpacyExtractor
            extractor = SpacyExtractor()
        else:
            print("(Using Standard Regex Extractor)")
            extractor = SpecificationExtractor()
            
        specs = extractor.extract_specs(full_text)
        for k, v in specs.items():
            if v:
                print(f"{k}: {v}")
            else:
                print(f"{k}: Not Found")
        
        # Save to validation/latest_specs.json for synchronous validation
        import json
        
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'validation')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        json_path = os.path.join(output_dir, 'latest_specs.json')
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(specs, f, indent=4)
            print(f"\n[INFO] Specifications saved to: {json_path}")
        except Exception as e:
            print(f"\n[WARN] Failed to save latest_specs.json: {e}")

    elif args.mode == "table":
        print(f"Extracting table from: {args.image} ...")
        table_engine = TableExtractor(ocr)
        try:
            df = table_engine.extract_table(args.image)
            print("\n--- Extracted Table ---")
            print(df)
            
            if args.output:
                df.to_csv(args.output, index=False, encoding='utf-8-sig')
                print(f"Table saved to: {args.output}")
        except Exception as e:
            print(f"Error extracting table: {e}")

if __name__ == "__main__":
    main()
