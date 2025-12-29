import re

class CableValidator:
    def __init__(self):
        self.rules = {
            "valid_insulation": ["PVC", "XLPE", "EPR", "RUBBER", "LSZH"],
            "valid_sheath": ["PVC", "PE", "LSZH", "RUBBER", "HDPE", "MDPE", "LDPE"],
            "valid_armor": ["STEEL", "ALUMINUM", "COPPER", "SWA", "STA", "AWA", "ATA", "NONE"],
            "invalid_materials": ["PLASTIC", "FOAM", "GLASS", "WOOD", "PAPER", "PAINT", "WATER", "STONE"],
            "temp_range": (-40, 105)
        }
    
    def parse_float(self, val_str):
        if not val_str: return None
        nums = re.findall(r'\d+(?:\.\d+)?', str(val_str))
        if nums: return float(nums[0])
        return None

    def validate_cable(self, specs):
        violations = []
        missing_data = []
        
        # Extract Raw Values (Already Corrected by SpecCorrector)
        type_str = (specs.get('cable_type') or "").upper()
        voltage_str = (specs.get('voltage') or "").upper()
        current_str = (specs.get('current_rating') or "").upper()
        insulation_str = (specs.get('insulation') or "").upper()
        conductor_count_str = str(specs.get('conductor_count') or "")
        conductor_size_str = (specs.get('conductor_size') or "").upper()
        sheath_str = (specs.get('sheath') or "").upper()
        armor_str = (specs.get('armor') or "NONE").upper()
        temp_str = str(specs.get('operating_temperature') or "")
        resistance_str = (specs.get('insulation_resistance') or "").upper()

        # Check for explicitly UNVERIFIABLE from Corrector
        if "UNVERIFIABLE" in [type_str, voltage_str, current_str, insulation_str, conductor_size_str, temp_str]:
             missing_data.append("Contains UNVERIFIABLE fields (marked by Corrector).")

        # --- ENGINEERING VALIDATION RULES ---

        # Rule 1: Cable Type
        if "FIBER" in type_str or "OPTIC" in type_str:
            violations.append("1. Cable Type: Rejected hybrid Fiber-Optic/Power cable.")
        if not type_str or any(x in type_str for x in ["UNKNOWN", "?", "AMBIGUOUS"]):
            missing_data.append("1. Cable Type: Unknown or ambiguous.")

        # Rule 2: Voltage Rating
        if "AC" in voltage_str and "DC" in voltage_str:
            violations.append("2. Voltage: Rejected mixed AC/DC ratings.")
        if "/" in voltage_str and "V" in voltage_str:
             matches = re.findall(r'(\d+(?:\.\d+)?)\s*(k?V)', voltage_str, re.IGNORECASE)
             parsed_vs = []
             for val_str, unit in matches:
                 try:
                    v = float(val_str)
                    if 'k' in unit.lower(): v *= 1000
                    parsed_vs.append(v)
                 except: pass
             if len(parsed_vs) >= 2 and max(parsed_vs) > 0:
                 ratio = max(parsed_vs) / (min(parsed_vs) if min(parsed_vs) > 0 else 1)
                 if ratio > 50: 
                     violations.append(f"2. Voltage: Rejected mixed voltage levels '{voltage_str}'.")

        # Rule 3 & 10: Current vs Conductor Size
        current_val = self.parse_float(current_str)
        size_val = self.parse_float(conductor_size_str)
        
        if size_val is not None:
             if size_val < 0.1: 
                 violations.append(f"10. Conductor Size: Rejected unrealistic size {size_val} mm2.")
        
        if current_val and size_val:
            density = current_val / size_val
            if density > 30: 
                 violations.append(f"3. Current: {current_val}A is physically incompatible with {size_val}mm2 (Density {density:.1f} A/mm2 too high).")
        
        # Rule 4: Insulation Type
        if any(bad in insulation_str for bad in self.rules["invalid_materials"]):
            violations.append(f"4. Insulation: Rejected non-electrical material '{insulation_str}'.")

        # Rule 5: Number of Conductors
        if conductor_count_str and '.' in conductor_count_str:
            violations.append(f"5. Conductors: Rejected fractional conductor count '{conductor_count_str}'.")

        # Rule 7: Armor
        if armor_str != "NONE" and armor_str not in self.rules["valid_armor"]:
             if any(bad in armor_str for bad in self.rules["invalid_materials"]):
                 violations.append(f"7. Armor: Rejected non-metallic armor '{armor_str}'.")

        # Rule 8: Operating Temperature
        temp_val = self.parse_float(temp_str)
        if temp_val is not None:
            min_t, max_t = self.rules["temp_range"]
            if not (min_t <= temp_val <= max_t):
                violations.append(f"8. Temperature: {temp_val}°C is outside realistic limit.")

        # Final Decision Logic
        if violations:
            status = "NOT READY"
        elif missing_data or not voltage_str: # Voltage is critical
            status = "UNVERIFIABLE"
        else:
            status = "READY"
        
        return {
            'valid': status == "READY",
            'status': status,
            'errors': violations, # Only Engineering Violations
            'missing': missing_data
        }
