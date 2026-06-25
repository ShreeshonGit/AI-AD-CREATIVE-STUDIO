import os
import glob
from typing import List

# Determine the project root dynamically relative to this file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

# Resolve absolute paths to the reference folders
REFERENCE_ADS_DIR = os.path.join(PROJECT_ROOT, "reference_ads")
REFERENCE_VIDEO_DIR = os.path.join(PROJECT_ROOT, "reference_video_scripts")

# Quota optimization thresholds to save context tokens and avoid API limitations
MAX_REFERENCE_FILES = 3
MAX_REFERENCE_CHARACTERS = 4000

def get_available_categories() -> List[str]:
    """
    Scans the reference_ads directory and returns a list of available subdirectories (categories).
    """
    if not os.path.exists(REFERENCE_ADS_DIR):
        return []
    
    try:
        categories = [
            d for d in os.listdir(REFERENCE_ADS_DIR)
            if os.path.isdir(os.path.join(REFERENCE_ADS_DIR, d)) and not d.startswith(".")
        ]
        return sorted(categories)
    except Exception as e:
        print(f"[ERROR] Error scanning categories: {e}")
        return []

def load_ad_references(category: str, limit: int = MAX_REFERENCE_FILES) -> str:
    """
    Loads up to `limit` markdown files within the specified category's folder,
    merging their content into a single formatted reference guide.
    If category directory is missing, returns empty string for true dynamic generation.
    """
    category_dir = os.path.join(REFERENCE_ADS_DIR, category)
    if not os.path.exists(category_dir) or not os.path.isdir(category_dir):
        # Silent fallback to let Gemini perform dynamic style synthesis
        print(f"[INFO] Ad category '{category}' has no local reference catalog.")
        return ""
    
    md_files = glob.glob(os.path.join(category_dir, "*.md"))
    if not md_files:
        return ""
    
    # Sort and slice to limit file reads
    md_files = sorted(md_files)[:limit]
    
    reference_contents = []
    current_char_count = 0
    
    for file_path in md_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                filename = os.path.basename(file_path)
                block = f"--- REFERENCE AD: {filename} ---\n{content}\n"
                
                # Check character quota limits
                if current_char_count + len(block) > MAX_REFERENCE_CHARACTERS:
                    remaining_budget = MAX_REFERENCE_CHARACTERS - current_char_count
                    if remaining_budget > 100:
                        reference_contents.append(block[:remaining_budget] + "\n[Truncated to fit context budget]\n")
                    break
                
                reference_contents.append(block)
                current_char_count += len(block)
        except Exception as e:
            print(f"[ERROR] Error reading ad file '{file_path}': {e}")
            
    return "\n".join(reference_contents)

def load_video_references(category: str, limit: int = MAX_REFERENCE_FILES) -> str:
    """
    Loads up to `limit` video script markdown files from category folder.
    If directory is missing, returns empty string to support dynamic script formatting.
    """
    category_dir = os.path.join(REFERENCE_VIDEO_DIR, category)
    if not os.path.exists(category_dir) or not os.path.isdir(category_dir):
        # Silent fallback to let Gemini perform dynamic screenplay synthesis
        print(f"[INFO] Video category '{category}' has no local script catalog.")
        return ""

    md_files = glob.glob(os.path.join(category_dir, "*.md"))
    if not md_files:
        return ""

    # Sort and slice
    md_files = sorted(md_files)[:limit]
    
    reference_contents = []
    current_char_count = 0
    
    for file_path in md_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                filename = os.path.basename(file_path)
                block = f"--- VIDEO SCRIPT REFERENCE: {filename} ---\n{content}\n"
                
                # Check character quota limits
                if current_char_count + len(block) > MAX_REFERENCE_CHARACTERS:
                    remaining_budget = MAX_REFERENCE_CHARACTERS - current_char_count
                    if remaining_budget > 100:
                        reference_contents.append(block[:remaining_budget] + "\n[Truncated to fit screenplay budget]\n")
                    break
                
                reference_contents.append(block)
                current_char_count += len(block)
        except Exception as e:
            print(f"[ERROR] Error reading video script file '{file_path}': {e}")
            
    return "\n".join(reference_contents)
