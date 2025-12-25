import spacy
from spacy.matcher import Matcher
import re

class SpacyExtractor:
    def __init__(self, model="en_core_web_sm"):
        """
        Initialize the SpaCy extractor with a specific model.
        """
        try:
            print(f"Loading SpaCy model: {model}...")
            self.nlp = spacy.load(model)
        except OSError:
            print(f"Model '{model}' not found. Downloading...")
            from spacy.cli import download
            download(model)
            self.nlp = spacy.load(model)
            
        self.matcher = Matcher(self.nlp.vocab)
        self._add_patterns()

    def _add_patterns(self):
        """
        Define and add all extraction patterns to the Matcher.
        """
        # 1. Voltage Pattern (e.g., 450/750 V, 0.6/1 kV)
        # Matches: Number + (Optional / + Number) + (Optional Space) + V/kV
        voltage_patterns = [
            [{"LIKE_NUM": True}, {"TEXT": "/"}, {"LIKE_NUM": True}, {"LOWER": {"IN": ["v", "kv", "volts"]}}], # 450/750 V
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["v", "kv", "volts"]}}], # 1000V
            [{"TEXT": {"REGEX": r"^\d+/\d+$"}}, {"LOWER": {"IN": ["v", "kv", "volts"]}}], # 450/750 V (split)
            [{"TEXT": {"REGEX": r"^\d+/\d+[kK]?[vV]$"}}] # 450/750V (merged)
        ]
        self.matcher.add("VOLTAGE", voltage_patterns)

        # 2. Conductor Size (e.g., 6mm2, 6 mm2, 3x50+25 mm2)
        # Regex is still useful inside SpaCy for complex units like mm2
        size_patterns = [
            [{"LIKE_NUM": True}, {"LOWER": "mm2"}],
            [{"LIKE_NUM": True}, {"LOWER": "mm"}, {"TEXT": "2"}],
            [{"TEXT": {"REGEX": r"^\d+mm2$"}}], # 6mm2 attached
            [{"TEXT": {"REGEX": r"^\d+mm[²2]$"}}], # 6mm² or 6mm2
            [{"TEXT": {"REGEX": r"^\d+m\s*m\s*[²2]$"}}], # 6 m m 2 (merged token with spaces inside? Unlikely for SpaCy, but good for regex)
            [{"TEXT": {"REGEX": r"^\d+mm$"}}, {"TEXT": "2"}], # 6mm 2
            # Complex: 3 x 240 mm2
            [{"LIKE_NUM": True}, {"LOWER": "x"}, {"LIKE_NUM": True}, {"LOWER": {"IN": ["mm2", "mm"]}}] 
        ]
        self.matcher.add("CONDUCTOR_SIZE", size_patterns)

        # 3. Core Count (e.g., 4 Core, 4C)
        core_patterns = [
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["core", "cores"]}}],
            [{"TEXT": {"REGEX": r"^\d+C$"}}], # 4C
            [{"TEXT": {"REGEX": r"^\d+c$"}}]  # 4c
        ]
        self.matcher.add("CORES", core_patterns)

        # 4. Temperature (e.g., 90 C, 90 deg C)
        temp_patterns = [
             [{"LIKE_NUM": True}, {"LOWER": "c"}],
             [{"LIKE_NUM": True}, {"LOWER": {"IN": ["deg", "degree", "degrees"]}}, {"LOWER": "c"}],
             [{"TEXT": {"REGEX": r"^\d+[cC]$"}}], # 40C
             [{"TEXT": {"REGEX": r"^\d+°[cC]$"}}] # 40°C
        ]
        self.matcher.add("TEMPERATURE", temp_patterns)
        
        # 5. Cable Type (Copper, Al) - Using NER-like matching
        type_patterns = [
            [{"LOWER": {"IN": ["copper", "cu", "aluminum", "aluminium", "al"]}}]
        ]
        self.matcher.add("CABLE_TYPE", type_patterns)

        # 6. Insulation/Sheath (XLPE, PVC)
        material_patterns = [
            [{"LOWER": {"IN": ["xlpe", "pvc", "lsoh", "lszh", "hdpe", "pe"]}}],
            [{"TEXT": {"REGEX": r"(?i).*XLPE.*"}}], # Catch XLPE16mm2
            [{"TEXT": {"REGEX": r"(?i).*PVC.*"}}]   # Catch PVC/PVC
        ]
        self.matcher.add("MATERIAL", material_patterns)

        # 7. Current Rating (e.g., 32 A, 32A)
        current_patterns = [
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["a", "amp", "amps"]}}],
            [{"TEXT": {"REGEX": r"^\d+[aA]$"}}] # 32A
        ]
        self.matcher.add("CURRENT_RATING", current_patterns)

        # 8. Insulation Resistance (e.g., 20 MΩ.km)
        resistance_patterns = [
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["mω.km", "mohm.km", "mΩkm"]}}],
            [{"TEXT": {"REGEX": r"(?i)^\d+M[ΩO]km$"}}], # 20MΩkm case-insensitive
            [{"TEXT": {"REGEX": r"(?i)^\d+M[ΩO]\.km$"}}] # 20MΩ.km
        ]
        self.matcher.add("RESISTANCE", resistance_patterns)

        # 9. Armor (SWA, Steel Wire Armor)
        armor_patterns = [
            [{"LOWER": "swa"}],
            [{"LOWER": "sta"}],
            [{"LOWER": "steel"}, {"LOWER": "wire"}, {"LOWER": "armor"}],
            [{"LOWER": "steel"}, {"LOWER": "tape"}, {"LOWER": "armor"}],
            [{"LOWER": "aluminum"}, {"LOWER": "armored"}],
            [{"LOWER": "armored"}] # Generic fallback
        ]
        self.matcher.add("ARMOR", armor_patterns)

    def extract_specs(self, text):
        """
        Process text and return extracted specifications.
        """
        doc = self.nlp(text)
        matches = self.matcher(doc)
        
        specs = {
            "voltage": None,
            "conductor_size": None,
            "conductor_count": None,
            "cable_type": None,
            "insulation": None,
            "sheath": None,
            "operating_temperature": None,
            "current_rating": None,
            "insulation_resistance": None,
            "armor": None
        }

        # Retrieve matched spans
        for match_id, start, end in matches:
            string_id = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            val = span.text

            # Assign to spec dict with simple logic (can be improved with proximity checks)
            if string_id == "VOLTAGE":
                specs["voltage"] = val
            elif string_id == "CONDUCTOR_SIZE":
                # Clean if merged (e.g. XLPE16mm2 -> 16mm2)
                size_match = re.search(r"(\d+(?:\.\d+)?\s*(?:x\s*\d+\s*)?mm[²2]?)", val, re.IGNORECASE)
                if size_match:
                    specs["conductor_size"] = size_match.group(1)
                else:
                    specs["conductor_size"] = val
            elif string_id == "CORES":
                specs["conductor_count"] = val
            elif string_id == "TEMPERATURE":
                # Differentiate Temp from simple Core count or unrelated numbers
                # e.g. 90C
                temp_match = re.search(r"(\d+\s*°?[cC])", val)
                if temp_match:
                    specs["operating_temperature"] = temp_match.group(1)
                else:
                    specs["operating_temperature"] = val
            elif string_id == "CABLE_TYPE":
                # Prefer existing if we find a better match? For now, overwrite.
                specs["cable_type"] = self._normalize_type(val)
            elif string_id == "MATERIAL":
                # Context check: Insulation vs Sheath (hard without more context, but let's try)
                # If we see PVC twice, first might be insulation, second sheath?
                # For now, just simplistic assignment
                if not specs["insulation"]:
                     specs["insulation"] = val.upper()
                else:
                     specs["sheath"] = val.upper()
                
                # Check if this token ALSO contains size (e.g. XLPE16mm2)
                size_match = re.search(r"(\d+mm[²2]?)", val, re.IGNORECASE)
                if size_match and not specs["conductor_size"]:
                    specs["conductor_size"] = size_match.group(1)
                    
            elif string_id == "CURRENT_RATING":
                specs["current_rating"] = val
            elif string_id == "RESISTANCE":
                specs["insulation_resistance"] = val
            elif string_id == "ARMOR":
                specs["armor"] = "Steel Wire Armor" if "swa" in val.lower() or "wire" in val.lower() else val

        return specs

    def _normalize_type(self, text):
        t = text.lower()
        if t in ["cu", "copper"]: return "Copper"
        if t in ["al", "aluminum", "aluminium"]: return "Aluminum"
        return text.title()
