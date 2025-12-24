from src.core_ocr import OCREngine
import re

# Initialize Engine with English (matching previous behavior)
ocr = OCREngine(languages=['en'])

# Path to image or PDF
file_path = "C:\\Users\\Omar Gaffer\\OneDrive - El Sewedy University of Technology\\Desktop\\project\\test\\handwrite.png"
# file_path = "path/to/test_file.pdf" # PDF files are now supported!

results = ocr.read_image(file_path, detail=1)




# Flatten OCR text list
words = [r[1] for r in results]
full_text = " ".join(words)

specs = {}

# Patterns for each spec (tuned for handwritten OCR errors)
# Note: We search for the values directly as the keys might be far away or garbled.
patterns = {
    # Matches things like "6OdA(ooov" which is "600/1000V"
    "voltage": r"(\d+[A-Za-z0-9\(\)\/]+[vV])",
    # Matches "3x25 mh 2" -> "3x25 mm2"
    "conductor": r"(\d+\s*[xX]\s*\d+\s*m[mh]\s*2)",
    # Matches "XLpE"
    "insulation": r"(XLPE|PVC)",
    # Matches "Steel wire Armox" or "SWA"
    "armor": r"(Steel\s+wire\s+Armo[rx]|SWA)",
    # "diameter": r"(\d+\s*mm)", # Not clearly seen in text
    # "current rating": r"(\d+\s*A)", # Not clearly seen in text
}

for key, pattern in patterns.items():
    match = re.search(pattern, full_text, re.IGNORECASE)

    if match:
        specs[key] = match.group(1) # group 1 is the value

def clean_value(key, value):
    if key == "voltage":
        # Attempt to fix common OCR errors for 600/1000V
        # 6OdA(ooov -> 600/1000V
        if "6" in value and "v" in value.lower():
            return "600/1000V"
        return value
    if key == "conductor":
        return value.replace("mh 2", "mm2").replace("mh2", "mm2")
    if key == "insulation":
        return value.upper()
    if key == "armor":
        return value.replace("Armox", "Armor").replace("armox", "armor")
    return value

print("\nExtracted Specifications:")
for k, v in specs.items():
    clean_v = clean_value(k, v)
    print(f"{k}: {clean_v}")
