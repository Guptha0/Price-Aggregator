import re
from typing import Dict, Set, Tuple, List

# Graceful fallback if thefuzz is not yet installed in the environment
try:
    from thefuzz import fuzz
except ImportError:
    import difflib
    class fuzz:
        @staticmethod
        def token_set_ratio(s1: str, s2: str) -> int:
            return int(difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100)
        @staticmethod
        def token_sort_ratio(s1: str, s2: str) -> int:
            return int(difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100)

# Common units and qualifiers across tech hardware and general e-commerce
UNITS = {"gb", "tb", "mb", "ghz", "mhz", "inch", '"', "in", "cm", "mm", "v", "w", "mah", "rpm", "hz"}
QUALIFIERS = {"ram", "ssd", "hdd", "nvme", "ddr4", "ddr5", "display", "screen", "battery", "memory", "storage", "gen3", "gen4", "gen5"}

def extract_quantities(title: str) -> Dict[str, float]:
    """
    Extracts numerical quantities and pairs them with their technical qualifier.
    Example: 'Lenovo 8GB RAM 512GB SSD 15.6"' -> {'ram': 8.0, 'ssd': 512.0, 'inch': 15.6}
    """
    title_clean = title.lower()
    # Match numbers followed optionally by units (e.g., 512GB, 15.6", 8 GB)
    pattern = r'(\d+(?:\.\d+)?)\s*([a-z"\'/]+)?'
    matches = list(re.finditer(pattern, title_clean))
    
    quantities = {}
    
    for match in matches:
        val_str, unit_str = match.group(1), match.group(2)
        try:
            val = float(val_str)
        except ValueError:
            continue
            
        qualifier = None
        
        # 1. Check the immediate trailing word/unit first (common pattern: 512GB SSD, 8GB RAM)
        if unit_str and unit_str in UNITS:
            qualifier = unit_str
            # Look one word ahead for deeper context (e.g., "GB SSD")
            end_idx = match.end()
            trailing_slice = title_clean[end_idx:].strip().split()
            if trailing_slice and trailing_slice[0] in QUALIFIERS:
                qualifier = trailing_slice[0]
        elif unit_str and unit_str in QUALIFIERS:
            qualifier = unit_str
            
        # 2. If no trailing qualifier, check strict 1-word leading window to prevent bleed-over
        if not qualifier:
            start_idx = match.start()
            leading_slice = title_clean[:start_idx].strip().split()
            if leading_slice and leading_slice[-1] in QUALIFIERS:
                qualifier = leading_slice[-1]
            elif leading_slice and leading_slice[-1] in UNITS:
                qualifier = leading_slice[-1]
                
        # Normalize inch representations
        if qualifier in {'"', 'in', 'inch'}:
            qualifier = 'inch'
            
        if qualifier:
            quantities[qualifier] = val
            
    return quantities

def extract_identifiers(title: str) -> Set[str]:
    """
    Extracts distinctive alphanumeric model codes and series numbers.
    Example: 'Samsung 980 PRO NVMe' -> {'980', 'pro'}
    """
    # Remove common words, brand names, and standalone units
    ignore_words = {"samsung", "western", "digital", "wd", "lenovo", "thinkpad", "hp", "dell", 
                    "asus", "acer", "apple", "new", "factory", "unlocked", "gen", "with", "for", "black"} | UNITS | QUALIFIERS
    
    words = re.findall(r'\b[a-z0-9_-]+\b', title.lower())
    identifiers = set()
    
    for word in words:
        if word in ignore_words or word.isdigit() and len(word) < 3:
            continue
        # Keep words with mixed alpha-numeric (e.g., l340, sn850x) or distinctive numbers (980, 970)
        if any(c.isdigit() for c in word) or len(word) >= 3:
            identifiers.add(word)
            
    return identifiers

def match_products(title_a: str, title_b: str) -> Tuple[bool, float, str]:
    """
    Evaluates whether two platform titles represent the exact same product variant.
    Returns: (is_match: bool, confidence_score: float, reasoning: str)
    """
    quants_a = extract_quantities(title_a)
    quants_b = extract_quantities(title_b)
    
    # 1. QUANTITY VETO TRAP: Check for conflicting technical specs (e.g., 1TB vs 2TB)
    shared_qualifiers = set(quants_a.keys()) & set(quants_b.keys())
    for qual in shared_qualifiers:
        if quants_a[qual] != quants_b[qual]:
            return False, 35.0, f"VETO: Conflicting quantity for '{qual}' ({quants_a[qual]} vs {quants_b[qual]})"
            
    # 2. IDENTIFIER CONFLICT VETO: Check for conflicting model codes (e.g., 980 vs 970, PRO vs EVO)
    ids_a = extract_identifiers(title_a)
    ids_b = extract_identifiers(title_b)
    shared_ids = ids_a & ids_b
    disjoint_a = ids_a - ids_b
    disjoint_b = ids_b - ids_a
    
    # If both titles contain explicit model identifiers but share ZERO of them, veto
    if ids_a and ids_b and not shared_ids:
        return False, 40.0, f"VETO: Disjoint model identifiers ({ids_a} vs {ids_b})"
        
    # If one model has a specific sub-series tag (PRO vs EVO) that conflicts, veto
    conflict_pairs = [{"pro", "evo"}, {"plus", "normal"}, {"home", "pro"}, {"5g", "4g"}]
    for pair in conflict_pairs:
        if (pair & disjoint_a) and (pair & disjoint_b):
            return False, 45.0, f"VETO: Conflicting series tier ({pair & disjoint_a} vs {pair & disjoint_b})"

    # 3. TEXT SIMILARITY: Use token_set_ratio to handle brand padding and word reordering gracefully
    base_score = float(fuzz.token_set_ratio(title_a, title_b))
    
    # 4. TIERED SPEC-OVERRIDE CALCULATION
    # Default required threshold for raw text matches
    required_threshold = 85.0
    reason = "Standard text similarity match"
    
    has_quantity_agreement = len(shared_qualifiers) > 0
    has_id_agreement = len(shared_ids) > 0
    
    # Tier 1 Override: Strong technical corroboration (Both specs and model numbers agree)
    if has_quantity_agreement and has_id_agreement:
        required_threshold = 60.0
        reason = f"Tier 1 Override (60%): Corroborated by shared specs {shared_qualifiers} and models {shared_ids}"
    # Tier 2 Override: Partial technical corroboration (Either exact specs or exact model numbers agree)
    elif has_quantity_agreement or has_id_agreement:
        required_threshold = 72.0
        reason = f"Tier 2 Override (72%): Supported by shared attributes ({shared_qualifiers or shared_ids})"
        
    is_match = base_score >= required_threshold
    
    if not is_match:
        reason = f"Failed: Score {base_score:.1f}% below required threshold of {required_threshold:.1f}%"
        
    return is_match, base_score, reason

# --- BUILT-IN VERIFICATION SUITE ---
if __name__ == "__main__":
    test_cases = [
        # 1. The Brand Padding Trap (Should match via Tier 2/Tier 1 override despite 'Western Digital' words)
        ("WD_BLACK 1TB SN850X NVMe Internal Gaming SSD Solid State Drive",
         "Western Digital WD_BLACK 1TB SN850X NVMe Internal Gaming SSD Solid State Drive",
         True, "WD Brand Padding"),
         
        # 2. The Capacity Trap (Should VETO immediately at <40 score)
        ("Western Digital WD_BLACK 1TB SN850X NVMe SSD",
         "Western Digital WD_BLACK 2TB SN850X NVMe SSD",
         False, "1TB vs 2TB Trap"),
         
        # 3. The Model Trap (Should VETO due to PRO vs EVO / 980 vs 970)
        ("Samsung 980 PRO 1TB PCIe NVMe Gen4 SSD",
         "Samsung 970 EVO Plus 1TB PCIe NVMe Gen3 SSD",
         False, "980 PRO vs 970 EVO False Positive"),
         
        # 4. Synonym Drift / Category Generalization (Should match via Tier 1 override at ~60%+ score)
        ("Lenovo ThinkPad L340 15.6 inch 8GB RAM 512GB SSD Laptop",
         "Lenovo ThinkPad L340 15.6\" 8GB 512GB SSD Notebook",
         True, "Laptop vs Notebook Synonym Drift")
    ]
    
    print("=== RUNNING MATCHER VERIFICATION SUITE ===")
    all_passed = True
    for idx, (title1, title2, expected, label) in enumerate(test_cases, 1):
        match, score, note = match_products(title1, title2)
        status = "PASS" if match == expected else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"Test {idx} [{label}]: [{status}] | Match: {match} (Expected {expected}) | Score: {score:.1f}%")
        print(f"   |- Note: {note}\n")
        
    if all_passed:
        print("[OK] ALL TESTS PASSED. The matching engine is clean and ready for dashboard integration.")
    else:
        print("[FAIL] SOME TESTS FAILED. Review logic above.")
