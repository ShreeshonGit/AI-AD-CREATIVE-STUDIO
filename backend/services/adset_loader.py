import os
from pathlib import Path
from typing import List

# Resolve project root and reference_adsets folder
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
REFERENCE_ADSETS_DIR = PROJECT_ROOT / "reference_adsets"

def get_available_adset_categories() -> List[str]:
    """
    Returns a list of available adset reference names (lowercase, without .md extension).
    """
    if not REFERENCE_ADSETS_DIR.exists() or not REFERENCE_ADSETS_DIR.is_dir():
        return []
    
    categories = []
    for entry in sorted(REFERENCE_ADSETS_DIR.iterdir()):
        if entry.is_file() and entry.suffix == ".md":
            categories.append(entry.stem.lower())
    return categories

def load_all_adset_references() -> str:
    """
    Scans reference_adsets directory, loads all .md files, and returns combined context.
    """
    if not REFERENCE_ADSETS_DIR.exists() or not REFERENCE_ADSETS_DIR.is_dir():
        return ""
    
    markdown_files = [entry for entry in sorted(REFERENCE_ADSETS_DIR.iterdir()) if entry.is_file() and entry.suffix == ".md"]
    if not markdown_files:
        return ""
    
    combined_parts = []
    for file_path in markdown_files:
        try:
            filename = file_path.name
            category_header = file_path.stem.replace("_", " ").upper()
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                
            combined_parts.append(f"===== {category_header} =====\n\n{content}\n")
            print(f"[INFO] Loaded adset reference file: {filename}")
        except Exception as e:
            print(f"[ERROR] Error loading adset file {file_path.name}: {e}")
            
    print(f"[INFO] Total adset references loaded: {len(markdown_files)}")
    return "\n".join(combined_parts).strip()
