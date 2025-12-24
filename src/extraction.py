import re

class SpecificationExtractor:
    def __init__(self):
        # Using broad patterns from original ocr.py to catch OCR errors
        self.patterns = {
            "cable_type": {
                # Copper, C0pper, COpp er, etc.
                "en": r"\b(C[o0]pp[\s]*[e3]r|Cu|Aluminium|Aluminum|Al)\b\s*(?:C[@a]ble|Conductor)?",
                "ar": r"(نحاس|الومنيوم)"
            },
            "voltage": {
                # 450/750V, 450 / 7S0 V, 0.6/1kV
                "en": r"(\d[\d\s\.]*[/]?[\d\sS]*\s*[kK]?[vV])", 
                "ar": r"(\d+\s*פولت|جهد\s*\d+)"
            },
            "current_rating": {
                 # 32 A, 3 2 A
                 "en": r"(\d[\d\s]*\s*(?:Amps?|A)\b)",
                 "ar": r"(\d+\s*امبير)"
            },
            "insulation": {
                "en": r"(XLPE|PVC)",
                "ar": r"(اكس ال بي اي|بي في سي)"
            },
            "conductor_count": {
                "en": r"(\d+)\s*(?:Core|Cores|x)",
                "ar": r"(\d+)\s*(?:كور|خط)"
            },
            "conductor_size": { 
                # 6 mm2, 6m m 2, 6  mm2
                "en": r"(\d+(?:[\s]*[xX][\s]*\d+)?[\s]*m[\s]*m[h]?[\s]*[2²\?]?)", 
                "ar": r"(\d+\s*x\s*\d+\s*مم2)"
            },
            "sheath": {
                "en": r"(PVC|HDPE|LDPE|Lead|LAZH|LSOH|MDPE|EPR|PUR|TPU|Neoprene|Rubber|LSZH)\s*(?:Sheath|Jacket)?",
                "ar": r"(غلاف\s*بي في سي)"
            },
            "operating_temperature": {
                # 40 C, 4O C
                "en": r"(\d+[O0]?[\s]*(?:°|\*|deg|degrees)?[\s]*C)",
                "ar": r"(\d+\s*درجة)"
            },
            "insulation_resistance": {
                # 20 MO.km, 20M O.km
                "en": r"(\d+[\s]*M?[O\u03a9][\s]*[\.]?k?m)",
                "ar": r"(\d+\s*ميج اوم)"
            },
            "armor": {
                # Steel Wire Armor, Steel Tape Armor, SWA, STA (word boundaries)
                "en": r"(Stee[l1][\s]*[WT][l1Iae3p]+[\s]*Armo[r0x]|\bSWA\b|\bSTA\b|SWA|AWA|ATA|GSWA|GSTA|CWA|BWA)",
                "ar": r"(تسليح|مسلح)"
            }
        }

    def extract_specs(self, text):
        """
        Extract specifications from full text.
        """
        specs = {}
        for key, lang_patterns in self.patterns.items():
            specs[key] = None
            
            # Search English (Prioritize original logic)
            match_en = re.search(lang_patterns["en"], text, re.IGNORECASE)
            if match_en:
                # If we have groups, use group 1, unless it's the whole match we want
                if len(match_en.groups()) > 0:
                     specs[key] = match_en.group(1)
                else:
                     specs[key] = match_en.group(0)
                continue
            
            # Search Arabic
            match_ar = re.search(lang_patterns["ar"], text, re.IGNORECASE)
            if match_ar:
                specs[key] = match_ar.group(0)
        
        return self.clean_specs(specs)

    def clean_specs(self, specs):
        """
        Clean and correct extracted data using original logic.
        """
        # voltage correction logic
        if specs.get("voltage"):
            val = specs["voltage"]
            # Remove spaces
            val = val.replace(" ", "")
            # Fix S -> 5
            val = val.replace("S", "5").replace("s", "5")
            
            if "6" in val and "v" in val.lower() and ("1000" in val or "1k" in val):
                 specs["voltage"] = "600/1000V"
            # Attempt to normalize 450/750
            if "450" in val and "750" in val:
                specs["voltage"] = "450/750V"
            else:
                specs["voltage"] = val
        
        # conductor/size correction
        if specs.get("conductor_size"):
            val = specs["conductor_size"]
            val = val.replace(" ", "")
            val = val.replace("mh", "mm").replace("?", "2")
            if "mm" in val and not val.endswith("2"): # Append 2 if missing (e.g. 6mm -> 6mm2)
                 val += "2"
            specs["conductor_size"] = val

        # current rating correction
        if specs.get("current_rating"):
            val = specs["current_rating"]
            val = val.replace(" ", "")
            specs["current_rating"] = val

        # armor correction
        if specs.get("armor"):
             val = specs["armor"]
             import re
             if re.search(r"Stee[l1]", val, re.IGNORECASE):
                 specs["armor"] = "Steel Wire Armor"
             else:
                 specs["armor"] = val.replace("Armox", "Armor").replace("armox", "armor")
        
        # cable type cleanup
        if specs.get("cable_type"):
            val = specs["cable_type"].lower()
            if "c" in val and ("p" in val or "o" in val) and "r" in val: # Loose check for copper
                specs["cable_type"] = "Copper"
            elif "al" in val: 
                specs["cable_type"] = "Aluminum"

        # sheath cleanup
        if specs.get("sheath"):
             val = specs["sheath"].upper()
             if "PVC" in val: specs["sheath"] = "PVC"
             elif "HDPE" in val: specs["sheath"] = "HDPE"

        # resistance cleanup (OCR often reads Omega as O or 0)
        if specs.get("insulation_resistance"):
             specs["insulation_resistance"] = specs["insulation_resistance"].replace("O", "Ω").replace(" ", "")

        return specs
